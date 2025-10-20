#!/usr/bin/env python3
"""
IMPROVED STRATEGIES WITH QUALIFYING FILTERS
Add filters to reduce bad trades and increase win rate

Filters applied:
1. ATR filter (avoid low volatility/consolidation)
2. Trend strength filter (ADX)
3. Volume confirmation
4. Time-of-day filter (London/NY sessions only)
5. Momentum confirmation
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime, time
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class ImprovedStrategyTester:
    """Test strategies with qualifying filters to improve win rate"""
    
    def __init__(self, data_file, transaction_cost_pct=0.0002):
        """Initialize with REAL data"""
        self.data = pd.read_csv(data_file)
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
        self.transaction_cost = transaction_cost_pct
        
        # Split data (60% train, 20% val, 20% test)
        n = len(self.data)
        train_end = int(n * 0.60)
        val_end = int(n * 0.80)
        
        self.train_data = self.data.iloc[:train_end].copy()
        self.val_data = self.data.iloc[train_end:val_end].copy()
        self.test_data = self.data.iloc[val_end:].copy()
        
        logger.info(f"Loaded {n:,} candles")
        logger.info(f"  Test: {len(self.test_data):,} candles (out-of-sample)")
    
    def calculate_indicators_with_filters(self, df):
        """Calculate indicators INCLUDING qualifying filters"""
        df = df.copy()
        
        # Standard indicators
        df['ema_3'] = df['close'].ewm(span=3, adjust=False).mean()
        df['ema_8'] = df['close'].ewm(span=8, adjust=False).mean()
        df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
        df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # ATR (Average True Range) - FILTER #1
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14).mean()
        df['atr_pct'] = df['atr'] / df['close']  # ATR as % of price
        
        # ADX (Average Directional Index) - FILTER #2
        # Simplified ADX calculation
        plus_dm = df['high'].diff()
        minus_dm = -df['low'].diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr_smooth = tr.rolling(window=14).mean()
        plus_di = 100 * (plus_dm.rolling(window=14).mean() / tr_smooth)
        minus_di = 100 * (minus_dm.rolling(window=14).mean() / tr_smooth)
        
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        df['adx'] = dx.rolling(window=14).mean()
        
        # Volume - FILTER #3
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # Momentum - FILTER #4
        df['roc'] = ((df['close'] - df['close'].shift(10)) / df['close'].shift(10)) * 100
        
        # Donchian Channel
        df['dc_upper'] = df['high'].rolling(window=20).max()
        df['dc_lower'] = df['low'].rolling(window=20).min()
        
        # Extract hour for session filter - FILTER #5
        df['hour'] = df['timestamp'].dt.hour
        
        return df
    
    def apply_qualifying_filters(self, df, base_signals):
        """Apply qualifying filters to reduce bad trades"""
        
        # Convert to series if needed
        if isinstance(base_signals, pd.DataFrame):
            signals = base_signals['signal'] if 'signal' in base_signals.columns else base_signals.iloc[:, 0]
        else:
            signals = base_signals.copy()
        
        # FILTER #1: ATR Filter - Only trade when volatility is sufficient
        # Avoid low volatility periods (consolidation)
        atr_threshold = df['atr_pct'].quantile(0.30)  # Bottom 30% volatility
        atr_filter = df['atr_pct'] > atr_threshold
        
        # FILTER #2: ADX Filter - Only trade when trend is strong
        # ADX > 20 indicates trending market (vs choppy)
        adx_filter = df['adx'] > 20
        
        # FILTER #3: Volume Filter - Confirm with above-average volume
        volume_filter = df['volume_ratio'] > 1.0  # Above 20-period average
        
        # FILTER #4: Momentum Filter - Trade in direction of momentum
        # For longs, want positive momentum; for shorts, want negative
        long_momentum_filter = (signals == 1) & (df['roc'] > 0)
        short_momentum_filter = (signals == -1) & (df['roc'] < 0)
        momentum_filter = long_momentum_filter | short_momentum_filter | (signals == 0)
        
        # FILTER #5: Session Filter - Only trade during London/NY sessions (best liquidity)
        # London: 7-16 GMT, NY: 13-21 GMT (overlap: 13-16)
        # Convert to hours (assuming UTC timestamps)
        london_session = (df['hour'] >= 7) & (df['hour'] < 16)
        ny_session = (df['hour'] >= 13) & (df['hour'] < 21)
        session_filter = london_session | ny_session
        
        # Combine all filters
        all_filters = atr_filter & adx_filter & volume_filter & momentum_filter & session_filter
        
        # Apply filters to signals
        filtered_signals = signals.copy()
        filtered_signals[~all_filters] = 0
        
        # Count how many signals were filtered out
        original_signals = (signals != 0).sum()
        filtered_signals_count = (filtered_signals != 0).sum()
        removed = original_signals - filtered_signals_count
        
        logger.info(f"  Original signals: {original_signals}")
        logger.info(f"  After filters: {filtered_signals_count}")
        logger.info(f"  Removed: {removed} ({removed/original_signals*100 if original_signals > 0 else 0:.1f}%)")
        
        return filtered_signals
    
    def strategy_ma_ribbon_filtered(self, df):
        """MA Ribbon with qualifying filters"""
        # Base signals
        signals = pd.Series(0, index=df.index)
        
        long_condition = (df['ema_8'] > df['ema_21']) & (df['ema_21'] > df['ema_50']) & (df['close'] > df['ema_8'])
        short_condition = (df['ema_8'] < df['ema_21']) & (df['ema_21'] < df['ema_50']) & (df['close'] < df['ema_8'])
        
        long_signal = long_condition & (long_condition.shift().fillna(False) == False)
        short_signal = short_condition & (short_condition.shift().fillna(False) == False)
        
        signals[long_signal] = 1
        signals[short_signal] = -1
        
        # Apply qualifying filters
        return self.apply_qualifying_filters(df, signals)
    
    def strategy_bollinger_filtered(self, df):
        """Bollinger Bands with qualifying filters"""
        signals = pd.Series(0, index=df.index)
        
        long_condition = (df['close'] > df['bb_upper']) & (df['close'].shift() <= df['bb_upper'].shift())
        short_condition = (df['close'] < df['bb_lower']) & (df['close'].shift() >= df['bb_lower'].shift())
        
        signals[long_condition] = 1
        signals[short_condition] = -1
        
        return self.apply_qualifying_filters(df, signals)
    
    def strategy_donchian_filtered(self, df):
        """Donchian Breakout with qualifying filters"""
        signals = pd.Series(0, index=df.index)
        
        long_condition = (df['close'] > df['dc_upper'].shift()) & (df['close'].shift() <= df['dc_upper'].shift(2))
        short_condition = (df['close'] < df['dc_lower'].shift()) & (df['close'].shift() >= df['dc_lower'].shift(2))
        
        signals[long_condition] = 1
        signals[short_condition] = -1
        
        return self.apply_qualifying_filters(df, signals)
    
    def strategy_ema_filtered(self, df):
        """EMA Crossover with qualifying filters"""
        signals = pd.Series(0, index=df.index)
        
        long_condition = (df['ema_3'] > df['ema_8']) & (df['ema_3'].shift() <= df['ema_8'].shift()) & (df['close'] > df['ema_21'])
        short_condition = (df['ema_3'] < df['ema_8']) & (df['ema_3'].shift() >= df['ema_8'].shift()) & (df['close'] < df['ema_21'])
        
        signals[long_condition] = 1
        signals[short_condition] = -1
        
        return self.apply_qualifying_filters(df, signals)
    
    def backtest_strategy(self, df, signals, stop_loss_pct=0.01, take_profit_pct=0.02):
        """Backtest with realistic execution"""
        trades = []
        position = None
        
        for i in range(len(df)):
            if i < 200:
                continue
            
            current_price = df.iloc[i]['close']
            current_time = df.iloc[i]['timestamp']
            
            # Check open position
            if position is not None:
                if position['direction'] == 'long':
                    if current_price <= position['stop_loss']:
                        pnl_pct = (position['stop_loss'] - position['entry_price']) / position['entry_price'] - self.transaction_cost
                        trades.append({'pnl_pct': pnl_pct, 'exit_reason': 'stop_loss'})
                        position = None
                    elif current_price >= position['take_profit']:
                        pnl_pct = (position['take_profit'] - position['entry_price']) / position['entry_price'] - self.transaction_cost
                        trades.append({'pnl_pct': pnl_pct, 'exit_reason': 'take_profit'})
                        position = None
                else:
                    if current_price >= position['stop_loss']:
                        pnl_pct = (position['entry_price'] - position['stop_loss']) / position['entry_price'] - self.transaction_cost
                        trades.append({'pnl_pct': pnl_pct, 'exit_reason': 'stop_loss'})
                        position = None
                    elif current_price <= position['take_profit']:
                        pnl_pct = (position['entry_price'] - position['take_profit']) / position['entry_price'] - self.transaction_cost
                        trades.append({'pnl_pct': pnl_pct, 'exit_reason': 'take_profit'})
                        position = None
            
            # New signal
            if position is None and signals.iloc[i] != 0:
                direction = 'long' if signals.iloc[i] == 1 else 'short'
                entry_price = current_price * (1 + self.transaction_cost) if direction == 'long' else current_price * (1 - self.transaction_cost)
                
                if direction == 'long':
                    stop_loss = entry_price * (1 - stop_loss_pct)
                    take_profit = entry_price * (1 + take_profit_pct)
                else:
                    stop_loss = entry_price * (1 + stop_loss_pct)
                    take_profit = entry_price * (1 - take_profit_pct)
                
                position = {
                    'entry_price': entry_price,
                    'direction': direction,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit
                }
        
        return pd.DataFrame(trades)
    
    def calculate_metrics(self, trades_df):
        """Calculate metrics"""
        if len(trades_df) == 0:
            return {'total_trades': 0, 'win_rate': 0, 'total_return': 0, 'sharpe_ratio': 0}
        
        returns = trades_df['pnl_pct'].values
        wins = returns > 0
        
        return {
            'total_trades': len(returns),
            'win_rate': np.mean(wins),
            'total_return': np.sum(returns),
            'sharpe_ratio': (np.mean(returns) / np.std(returns) * np.sqrt(252)) if np.std(returns) > 0 else 0,
            'max_drawdown': self._calc_max_dd(returns),
            'profit_factor': self._calc_pf(returns),
            'expectancy': np.mean(returns)
        }
    
    def _calc_max_dd(self, returns):
        """Calculate max drawdown"""
        cum = np.cumsum(returns)
        peak = np.maximum.accumulate(cum)
        dd = peak - cum
        return np.max(dd) if len(dd) > 0 else 0
    
    def _calc_pf(self, returns):
        """Calculate profit factor"""
        wins = returns[returns > 0]
        losses = returns[returns <= 0]
        gross_profit = np.sum(wins) if len(wins) > 0 else 0
        gross_loss = abs(np.sum(losses)) if len(losses) > 0 else 0
        return gross_profit / gross_loss if gross_loss > 0 else 0
    
    def run_monte_carlo(self, trades_df, n_runs=1000):
        """Quick Monte Carlo"""
        if len(trades_df) == 0:
            return {'survival_rate': 0}
        
        returns = trades_df['pnl_pct'].values
        final_returns = []
        
        for _ in range(n_runs):
            shuffled = np.random.permutation(returns)
            final_returns.append(np.sum(shuffled))
        
        return {
            'survival_rate': np.mean(np.array(final_returns) > 0),
            'mean_return': np.mean(final_returns)
        }

def main():
    """Test improved strategies with filters"""
    
    data_file = "data/MASTER_DATASET/15m/xau_usd_15m.csv"
    
    logger.info("="*80)
    logger.info("IMPROVED STRATEGIES WITH QUALIFYING FILTERS")
    logger.info("Goal: Reduce bad trades, increase win rate to 60%+")
    logger.info("="*80)
    
    tester = ImprovedStrategyTester(data_file)
    
    # Calculate indicators with filters
    tester.test_data = tester.calculate_indicators_with_filters(tester.test_data)
    
    # Test period info
    test_days = (tester.test_data['timestamp'].max() - tester.test_data['timestamp'].min()).days
    test_weeks = test_days / 7
    
    strategies = [
        ('MA Ribbon FILTERED', tester.strategy_ma_ribbon_filtered),
        ('Bollinger FILTERED', tester.strategy_bollinger_filtered),
        ('Donchian FILTERED', tester.strategy_donchian_filtered),
        ('EMA Crossover FILTERED', tester.strategy_ema_filtered)
    ]
    
    results = []
    
    for name, func in strategies:
        logger.info(f"\n{'='*80}")
        logger.info(f"TESTING: {name}")
        logger.info(f"{'='*80}")
        
        # Generate filtered signals
        signals = func(tester.test_data)
        
        # Backtest
        trades = tester.backtest_strategy(tester.test_data, signals)
        
        # Metrics
        metrics = tester.calculate_metrics(trades)
        
        # Monte Carlo
        mc = tester.run_monte_carlo(trades, n_runs=1000)
        
        # Calculate frequency
        trades_per_week = metrics['total_trades'] / test_weeks if test_weeks > 0 else 0
        
        # Display
        logger.info(f"\nRESULTS:")
        logger.info(f"  Total Trades: {metrics['total_trades']}")
        logger.info(f"  Trades/Week: {trades_per_week:.1f}")
        logger.info(f"  Win Rate: {metrics['win_rate']*100:.2f}%")
        logger.info(f"  Total Return: {metrics['total_return']*100:.2f}%")
        logger.info(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        logger.info(f"  Max Drawdown: {metrics['max_drawdown']*100:.2f}%")
        logger.info(f"  Profit Factor: {metrics['profit_factor']:.2f}")
        logger.info(f"  Expectancy/Trade: {metrics['expectancy']*100:.4f}%")
        logger.info(f"\nMonte Carlo (1000 runs):")
        logger.info(f"  Survival Rate: {mc['survival_rate']*100:.2f}%")
        
        # Verdict
        if metrics['win_rate'] >= 0.60 and mc['survival_rate'] >= 0.95:
            verdict = "EXCELLENT - 60%+ win rate achieved"
        elif metrics['win_rate'] >= 0.55 and mc['survival_rate'] >= 0.90:
            verdict = "VERY GOOD - Strong improvement"
        elif metrics['win_rate'] >= 0.50:
            verdict = "GOOD - Filters helped"
        else:
            verdict = "NEEDS MORE WORK"
        
        logger.info(f"\nVERDICT: {verdict}")
        
        results.append({
            'strategy': name,
            'metrics': metrics,
            'monte_carlo': mc,
            'trades_per_week': trades_per_week,
            'verdict': verdict
        })
    
    # Save results
    output_file = f"improved_strategies_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Results saved to {output_file}")
    logger.info(f"\n{'='*80}")
    logger.info("FINAL COMPARISON - ORIGINAL vs FILTERED:")
    logger.info(f"{'='*80}\n")
    
    # Compare original vs filtered
    original_results = [
        {'name': 'MA Ribbon ORIGINAL', 'trades': 67, 'wr': 53.73, 'ret': 39.66, 'sharpe': 6.28},
        {'name': 'Bollinger ORIGINAL', 'trades': 68, 'wr': 50.00, 'ret': 32.64, 'sharpe': 5.08},
        {'name': 'Donchian ORIGINAL', 'trades': 71, 'wr': 49.30, 'ret': 32.58, 'sharpe': 4.86},
        {'name': 'EMA Cross ORIGINAL', 'trades': 65, 'wr': 49.23, 'ret': 29.70, 'sharpe': 4.84}
    ]
    
    for i, (orig, filtered) in enumerate(zip(original_results, results)):
        logger.info(f"{orig['name']}:")
        logger.info(f"  Trades: {orig['trades']} → {filtered['metrics']['total_trades']} (trades/week: {filtered['trades_per_week']:.1f})")
        logger.info(f"  Win Rate: {orig['wr']:.2f}% → {filtered['metrics']['win_rate']*100:.2f}%")
        logger.info(f"  Return: {orig['ret']:.2f}% → {filtered['metrics']['total_return']*100:.2f}%")
        logger.info(f"  Sharpe: {orig['sharpe']:.2f} → {filtered['metrics']['sharpe_ratio']:.2f}")
        
        wr_improvement = filtered['metrics']['win_rate']*100 - orig['wr']
        logger.info(f"  Win Rate Change: {'+' if wr_improvement > 0 else ''}{wr_improvement:.2f}%")
        logger.info()

if __name__ == "__main__":
    main()


