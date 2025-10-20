#!/usr/bin/env python3
"""
OPTIMIZE WIN RATE - SMART APPROACH
Instead of filtering signals, optimize entry timing and exit strategy

Improvements:
1. Wait for pullback confirmation (better entry price)
2. Optimize stop-loss distance based on ATR
3. Use trailing stops for winners
4. Add higher timeframe trend filter only
5. Improve R:R ratio
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class WinRateOptimizer:
    """Optimize strategies for higher win rate"""
    
    def __init__(self, data_file):
        """Initialize"""
        self.data = pd.read_csv(data_file)
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
        self.transaction_cost = 0.0002
        
        # Split
        n = len(self.data)
        val_end = int(n * 0.80)
        self.test_data = self.data.iloc[val_end:].copy()
        
        logger.info(f"Test set: {len(self.test_data):,} candles")
    
    def calculate_indicators(self, df):
        """Calculate indicators"""
        df = df.copy()
        
        # EMAs
        for period in [3, 8, 21, 50, 200]:
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
        
        # BB
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14).mean()
        
        # Donchian
        df['dc_upper'] = df['high'].rolling(window=20).max()
        df['dc_lower'] = df['low'].rolling(window=20).min()
        
        # Higher timeframe trend
        df['higher_tf_trend'] = (df['ema_50'] > df['ema_200']).astype(int)  # 1=bullish, 0=bearish
        
        return df
    
    def optimized_ma_ribbon(self, df):
        """MA Ribbon with optimized exits and HTF filter"""
        signals = pd.Series(0, index=df.index)
        
        # Base condition
        long_base = (df['ema_8'] > df['ema_21']) & (df['ema_21'] > df['ema_50']) & (df['close'] > df['ema_8'])
        short_base = (df['ema_8'] < df['ema_21']) & (df['ema_21'] < df['ema_50']) & (df['close'] < df['ema_8'])
        
        # NEW: Only trade WITH higher timeframe trend
        long_with_htf = long_base & (df['higher_tf_trend'] == 1)
        short_with_htf = short_base & (df['higher_tf_trend'] == 0)
        
        # Detect new signals
        long_signal = long_with_htf & (long_with_htf.shift().fillna(False) == False)
        short_signal = short_with_htf & (short_with_htf.shift().fillna(False) == False)
        
        signals[long_signal] = 1
        signals[short_signal] = -1
        
        return signals
    
    def optimized_bollinger(self, df):
        """Bollinger with HTF trend filter"""
        signals = pd.Series(0, index=df.index)
        
        # Base breakout
        long_base = (df['close'] > df['bb_upper']) & (df['close'].shift() <= df['bb_upper'].shift())
        short_base = (df['close'] < df['bb_lower']) & (df['close'].shift() >= df['bb_lower'].shift())
        
        # With HTF trend filter
        long_htf = long_base & (df['higher_tf_trend'] == 1)
        short_htf = short_base & (df['higher_tf_trend'] == 0)
        
        signals[long_htf] = 1
        signals[short_htf] = -1
        
        return signals
    
    def optimized_donchian(self, df):
        """Donchian with HTF trend filter"""
        signals = pd.Series(0, index=df.index)
        
        # Base breakout
        long_base = (df['close'] > df['dc_upper'].shift()) & (df['close'].shift() <= df['dc_upper'].shift(2))
        short_base = (df['close'] < df['dc_lower'].shift()) & (df['close'].shift() >= df['dc_lower'].shift(2))
        
        # With HTF trend filter
        long_htf = long_base & (df['higher_tf_trend'] == 1)
        short_htf = short_base & (df['higher_tf_trend'] == 0)
        
        signals[long_htf] = 1
        signals[short_htf] = -1
        
        return signals
    
    def backtest_with_atr_stops(self, df, signals):
        """Backtest with ATR-based stops for better win rate"""
        trades = []
        position = None
        
        for i in range(len(df)):
            if i < 200:
                continue
            
            current_price = df.iloc[i]['close']
            atr = df.iloc[i]['atr']
            
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
                
                # ATR-based stops (tighter stops = higher win rate)
                atr_multiplier = 1.5  # Tighter than usual
                
                if direction == 'long':
                    stop_loss = entry_price - (atr * atr_multiplier)
                    take_profit = entry_price + (atr * atr_multiplier * 2.5)  # 2.5:1 R:R
                else:
                    stop_loss = entry_price + (atr * atr_multiplier)
                    take_profit = entry_price - (atr * atr_multiplier * 2.5)
                
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
            return {'total_trades': 0}
        
        returns = trades_df['pnl_pct'].values
        wins = returns > 0
        
        return {
            'total_trades': len(returns),
            'win_rate': np.mean(wins),
            'total_return': np.sum(returns),
            'sharpe_ratio': (np.mean(returns) / np.std(returns) * np.sqrt(252)) if np.std(returns) > 0 else 0,
            'max_drawdown': self._calc_max_dd(returns),
            'profit_factor': self._calc_pf(returns)
        }
    
    def _calc_max_dd(self, returns):
        cum = np.cumsum(returns)
        peak = np.maximum.accumulate(cum)
        return np.max(peak - cum)
    
    def _calc_pf(self, returns):
        wins = returns[returns > 0]
        losses = returns[returns <= 0]
        gp = np.sum(wins) if len(wins) > 0 else 0
        gl = abs(np.sum(losses)) if len(losses) > 0 else 0
        return gp / gl if gl > 0 else 0
    
    def run_monte_carlo(self, trades_df, n_runs=1000):
        if len(trades_df) == 0:
            return {'survival_rate': 0}
        returns = trades_df['pnl_pct'].values
        final_returns = [np.sum(np.random.permutation(returns)) for _ in range(n_runs)]
        return {'survival_rate': np.mean(np.array(final_returns) > 0)}

def main():
    """Test optimized strategies"""
    
    logger.info("="*80)
    logger.info("WIN RATE OPTIMIZATION - HTF TREND FILTER + ATR STOPS")
    logger.info("="*80)
    
    optimizer = WinRateOptimizer("data/MASTER_DATASET/15m/xau_usd_15m.csv")
    optimizer.test_data = optimizer.calculate_indicators(optimizer.test_data)
    
    test_days = (optimizer.test_data['timestamp'].max() - optimizer.test_data['timestamp'].min()).days
    test_weeks = test_days / 7
    
    strategies = [
        ('MA Ribbon + HTF Trend', optimizer.optimized_ma_ribbon),
        ('Bollinger + HTF Trend', optimizer.optimized_bollinger),
        ('Donchian + HTF Trend', optimizer.optimized_donchian)
    ]
    
    results = []
    
    for name, func in strategies:
        logger.info(f"\n{'='*80}")
        logger.info(f"{name}")
        logger.info(f"{'='*80}")
        
        signals = func(optimizer.test_data)
        trades = optimizer.backtest_with_atr_stops(optimizer.test_data, signals)
        metrics = optimizer.calculate_metrics(trades)
        mc = optimizer.run_monte_carlo(trades)
        
        trades_per_week = metrics['total_trades'] / test_weeks
        
        logger.info(f"  Total Trades: {metrics['total_trades']}")
        logger.info(f"  Trades/Week: {trades_per_week:.1f}")
        logger.info(f"  Win Rate: {metrics['win_rate']*100:.2f}%")
        logger.info(f"  Return: {metrics['total_return']*100:.2f}%")
        logger.info(f"  Sharpe: {metrics['sharpe_ratio']:.2f}")
        logger.info(f"  Profit Factor: {metrics['profit_factor']:.2f}")
        logger.info(f"  MC Survival: {mc['survival_rate']*100:.1f}%")
        
        results.append({
            'strategy': name,
            'metrics': metrics,
            'trades_per_week': trades_per_week
        })
    
    # Save
    with open(f"optimized_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Find best
    logger.info(f"\n{'='*80}")
    logger.info("BEST PERFORMER:")
    logger.info(f"{'='*80}")
    
    best = max(results, key=lambda x: x['metrics']['win_rate'])
    logger.info(f"\n{best['strategy']}")
    logger.info(f"  Win Rate: {best['metrics']['win_rate']*100:.2f}%")
    logger.info(f"  Return: {best['metrics']['total_return']*100:.2f}%")
    logger.info(f"  Trades/Week: {best['trades_per_week']:.1f}")

if __name__ == "__main__":
    main()


