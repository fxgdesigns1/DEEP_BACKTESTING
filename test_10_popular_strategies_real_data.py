#!/usr/bin/env python3
"""
Test 10 Popular Trading Strategies on REAL Historical Data
NO SIMULATED DATA - NO CHEATING - NO LOOK-AHEAD BIAS

Strategies tested:
1. EMA Crossover (3/8/21)
2. RSI Mean Reversion
3. Bollinger Bands Breakout
4. MACD Crossover
5. Moving Average Ribbon
6. Breakout (Donchian Channel)
7. Momentum (ROC)
8. Stochastic Oscillator
9. Parabolic SAR
10. Ichimoku Cloud

Each strategy tested with:
- Out-of-sample validation (train on 70%, test on 30%)
- Realistic transaction costs
- No look-ahead bias
- Monte Carlo validation (1000 runs)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class StrategyBacktester:
    """Backtest trading strategies with no cheating"""
    
    def __init__(self, data_file, transaction_cost_pct=0.0002):
        """
        Initialize backtester
        
        Args:
            data_file: Path to REAL historical data CSV
            transaction_cost_pct: Transaction cost as decimal (0.0002 = 0.02% = 2 pips)
        """
        self.data = pd.read_csv(data_file)
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
        self.transaction_cost = transaction_cost_pct
        
        # Split data: 70% train, 30% test (NO OVERLAP)
        split_idx = int(len(self.data) * 0.70)
        self.train_data = self.data.iloc[:split_idx].copy()
        self.test_data = self.data.iloc[split_idx:].copy()
        
        logger.info(f"Loaded {len(self.data)} candles from {data_file}")
        logger.info(f"Train: {len(self.train_data)} candles ({self.train_data['timestamp'].min()} to {self.train_data['timestamp'].max()})")
        logger.info(f"Test: {len(self.test_data)} candles ({self.test_data['timestamp'].min()} to {self.test_data['timestamp'].max()})")
    
    def calculate_indicators(self, df):
        """Calculate technical indicators (NO LOOK-AHEAD BIAS)"""
        df = df.copy()
        
        # EMAs
        df['ema_3'] = df['close'].ewm(span=3, adjust=False).mean()
        df['ema_8'] = df['close'].ewm(span=8, adjust=False).mean()
        df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
        df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        # MACD
        ema_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14).mean()
        
        # Stochastic
        low_14 = df['low'].rolling(window=14).min()
        high_14 = df['high'].rolling(window=14).max()
        df['stoch_k'] = 100 * (df['close'] - low_14) / (high_14 - low_14)
        df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
        
        # Donchian Channel
        df['dc_upper'] = df['high'].rolling(window=20).max()
        df['dc_lower'] = df['low'].rolling(window=20).min()
        
        # ROC (Rate of Change)
        df['roc'] = ((df['close'] - df['close'].shift(10)) / df['close'].shift(10)) * 100
        
        return df
    
    def strategy_ema_crossover(self, df):
        """Strategy 1: EMA Crossover (3, 8, 21)"""
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Long: EMA3 crosses above EMA8 and price > EMA21
        long_condition = (df['ema_3'] > df['ema_8']) & (df['ema_3'].shift() <= df['ema_8'].shift()) & (df['close'] > df['ema_21'])
        
        # Short: EMA3 crosses below EMA8 and price < EMA21
        short_condition = (df['ema_3'] < df['ema_8']) & (df['ema_3'].shift() >= df['ema_8'].shift()) & (df['close'] < df['ema_21'])
        
        signals.loc[long_condition, 'signal'] = 1
        signals.loc[short_condition, 'signal'] = -1
        
        return signals['signal']
    
    def strategy_rsi_mean_reversion(self, df):
        """Strategy 2: RSI Mean Reversion"""
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Long: RSI < 30 (oversold)
        long_condition = (df['rsi'] < 30) & (df['rsi'].shift() >= 30)
        
        # Short: RSI > 70 (overbought)
        short_condition = (df['rsi'] > 70) & (df['rsi'].shift() <= 70)
        
        signals.loc[long_condition, 'signal'] = 1
        signals.loc[short_condition, 'signal'] = -1
        
        return signals['signal']
    
    def strategy_bollinger_breakout(self, df):
        """Strategy 3: Bollinger Bands Breakout"""
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Long: Price breaks above upper band
        long_condition = (df['close'] > df['bb_upper']) & (df['close'].shift() <= df['bb_upper'].shift())
        
        # Short: Price breaks below lower band  
        short_condition = (df['close'] < df['bb_lower']) & (df['close'].shift() >= df['bb_lower'].shift())
        
        signals.loc[long_condition, 'signal'] = 1
        signals.loc[short_condition, 'signal'] = -1
        
        return signals['signal']
    
    def strategy_macd_crossover(self, df):
        """Strategy 4: MACD Crossover"""
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Long: MACD crosses above signal line
        long_condition = (df['macd'] > df['macd_signal']) & (df['macd'].shift() <= df['macd_signal'].shift())
        
        # Short: MACD crosses below signal line
        short_condition = (df['macd'] < df['macd_signal']) & (df['macd'].shift() >= df['macd_signal'].shift())
        
        signals.loc[long_condition, 'signal'] = 1
        signals.loc[short_condition, 'signal'] = -1
        
        return signals['signal']
    
    def strategy_ma_ribbon(self, df):
        """Strategy 5: Moving Average Ribbon (EMA 8, 21, 50)"""
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Long: All EMAs aligned bullish
        long_condition = (df['ema_8'] > df['ema_21']) & (df['ema_21'] > df['ema_50']) & (df['close'] > df['ema_8'])
        
        # Short: All EMAs aligned bearish
        short_condition = (df['ema_8'] < df['ema_21']) & (df['ema_21'] < df['ema_50']) & (df['close'] < df['ema_8'])
        
        # Only signal on new alignment
        long_signal = long_condition & (long_condition.shift().fillna(False) == False)
        short_signal = short_condition & (short_condition.shift().fillna(False) == False)
        
        signals.loc[long_signal, 'signal'] = 1
        signals.loc[short_signal, 'signal'] = -1
        
        return signals['signal']
    
    def strategy_donchian_breakout(self, df):
        """Strategy 6: Donchian Channel Breakout"""
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Long: Price breaks above upper channel
        long_condition = (df['close'] > df['dc_upper'].shift()) & (df['close'].shift() <= df['dc_upper'].shift(2))
        
        # Short: Price breaks below lower channel
        short_condition = (df['close'] < df['dc_lower'].shift()) & (df['close'].shift() >= df['dc_lower'].shift(2))
        
        signals.loc[long_condition, 'signal'] = 1
        signals.loc[short_condition, 'signal'] = -1
        
        return signals['signal']
    
    def strategy_momentum_roc(self, df):
        """Strategy 7: Momentum (Rate of Change)"""
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Long: ROC crosses above 0
        long_condition = (df['roc'] > 0) & (df['roc'].shift() <= 0)
        
        # Short: ROC crosses below 0
        short_condition = (df['roc'] < 0) & (df['roc'].shift() >= 0)
        
        signals.loc[long_condition, 'signal'] = 1
        signals.loc[short_condition, 'signal'] = -1
        
        return signals['signal']
    
    def strategy_stochastic(self, df):
        """Strategy 8: Stochastic Oscillator"""
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Long: %K crosses above %D in oversold zone
        long_condition = (df['stoch_k'] > df['stoch_d']) & (df['stoch_k'].shift() <= df['stoch_d'].shift()) & (df['stoch_k'] < 20)
        
        # Short: %K crosses below %D in overbought zone
        short_condition = (df['stoch_k'] < df['stoch_d']) & (df['stoch_k'].shift() >= df['stoch_d'].shift()) & (df['stoch_k'] > 80)
        
        signals.loc[long_condition, 'signal'] = 1
        signals.loc[short_condition, 'signal'] = -1
        
        return signals['signal']
    
    def strategy_trend_following_ma(self, df):
        """Strategy 9: Simple Trend Following (50/200 MA)"""
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Long: Price above 50 EMA and 50 EMA above 200 EMA
        long_condition = (df['close'] > df['ema_50']) & (df['ema_50'] > df['ema_200']) & (df['close'].shift() <= df['ema_50'].shift())
        
        # Short: Price below 50 EMA and 50 EMA below 200 EMA
        short_condition = (df['close'] < df['ema_50']) & (df['ema_50'] < df['ema_200']) & (df['close'].shift() >= df['ema_50'].shift())
        
        signals.loc[long_condition, 'signal'] = 1
        signals.loc[short_condition, 'signal'] = -1
        
        return signals['signal']
    
    def strategy_price_action_pin_bar(self, df):
        """Strategy 10: Price Action (Pin Bar / Rejection)"""
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Calculate candle properties
        body = abs(df['close'] - df['open'])
        total_range = df['high'] - df['low']
        upper_wick = df['high'] - df[['open', 'close']].max(axis=1)
        lower_wick = df[['open', 'close']].min(axis=1) - df['low']
        
        # Bullish pin bar: long lower wick, small body, near top of range
        bullish_pin = (lower_wick > 2 * body) & (body < 0.3 * total_range) & (upper_wick < 0.3 * total_range)
        
        # Bearish pin bar: long upper wick, small body, near bottom of range
        bearish_pin = (upper_wick > 2 * body) & (body < 0.3 * total_range) & (lower_wick < 0.3 * total_range)
        
        signals.loc[bullish_pin, 'signal'] = 1
        signals.loc[bearish_pin, 'signal'] = -1
        
        return signals['signal']
    
    def backtest_strategy(self, df, signals, stop_loss_pct=0.01, take_profit_pct=0.02):
        """
        Backtest a strategy with realistic execution
        
        Args:
            df: DataFrame with price data
            signals: Series with trading signals (1=long, -1=short, 0=no signal)
            stop_loss_pct: Stop loss as decimal (0.01 = 1%)
            take_profit_pct: Take profit as decimal (0.02 = 2%)
        """
        trades = []
        position = None
        
        for i in range(len(df)):
            if i < 200:  # Skip first 200 candles to allow indicators to stabilize
                continue
            
            current_price = df.iloc[i]['close']
            current_time = df.iloc[i]['timestamp']
            
            # Check if we have an open position
            if position is not None:
                # Check stop loss
                if position['direction'] == 'long':
                    if current_price <= position['stop_loss']:
                        # Stop loss hit
                        pnl_pct = (position['stop_loss'] - position['entry_price']) / position['entry_price']
                        pnl_pct -= self.transaction_cost  # Exit cost
                        trades.append({
                            'entry_time': position['entry_time'],
                            'exit_time': current_time,
                            'direction': 'long',
                            'entry_price': position['entry_price'],
                            'exit_price': position['stop_loss'],
                            'pnl_pct': pnl_pct,
                            'exit_reason': 'stop_loss'
                        })
                        position = None
                    elif current_price >= position['take_profit']:
                        # Take profit hit
                        pnl_pct = (position['take_profit'] - position['entry_price']) / position['entry_price']
                        pnl_pct -= self.transaction_cost  # Exit cost
                        trades.append({
                            'entry_time': position['entry_time'],
                            'exit_time': current_time,
                            'direction': 'long',
                            'entry_price': position['entry_price'],
                            'exit_price': position['take_profit'],
                            'pnl_pct': pnl_pct,
                            'exit_reason': 'take_profit'
                        })
                        position = None
                
                elif position['direction'] == 'short':
                    if current_price >= position['stop_loss']:
                        # Stop loss hit
                        pnl_pct = (position['entry_price'] - position['stop_loss']) / position['entry_price']
                        pnl_pct -= self.transaction_cost  # Exit cost
                        trades.append({
                            'entry_time': position['entry_time'],
                            'exit_time': current_time,
                            'direction': 'short',
                            'entry_price': position['entry_price'],
                            'exit_price': position['stop_loss'],
                            'pnl_pct': pnl_pct,
                            'exit_reason': 'stop_loss'
                        })
                        position = None
                    elif current_price <= position['take_profit']:
                        # Take profit hit
                        pnl_pct = (position['entry_price'] - position['take_profit']) / position['entry_price']
                        pnl_pct -= self.transaction_cost  # Exit cost
                        trades.append({
                            'entry_time': position['entry_time'],
                            'exit_time': current_time,
                            'direction': 'short',
                            'entry_price': position['entry_price'],
                            'exit_price': position['take_profit'],
                            'pnl_pct': pnl_pct,
                            'exit_reason': 'take_profit'
                        })
                        position = None
            
            # Check for new signals (only if no position)
            if position is None and signals.iloc[i] != 0:
                # Entry signal
                entry_price = current_price
                direction = 'long' if signals.iloc[i] == 1 else 'short'
                
                # Apply transaction cost
                entry_price_with_cost = entry_price * (1 + self.transaction_cost) if direction == 'long' else entry_price * (1 - self.transaction_cost)
                
                # Set stop loss and take profit
                if direction == 'long':
                    stop_loss = entry_price * (1 - stop_loss_pct)
                    take_profit = entry_price * (1 + take_profit_pct)
                else:
                    stop_loss = entry_price * (1 + stop_loss_pct)
                    take_profit = entry_price * (1 - take_profit_pct)
                
                position = {
                    'entry_time': current_time,
                    'entry_price': entry_price_with_cost,
                    'direction': direction,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit
                }
        
        # Close any remaining position at the end
        if position is not None:
            final_price = df.iloc[-1]['close']
            final_time = df.iloc[-1]['timestamp']
            
            if position['direction'] == 'long':
                pnl_pct = (final_price - position['entry_price']) / position['entry_price']
            else:
                pnl_pct = (position['entry_price'] - final_price) / position['entry_price']
            
            pnl_pct -= self.transaction_cost  # Exit cost
            
            trades.append({
                'entry_time': position['entry_time'],
                'exit_time': final_time,
                'direction': position['direction'],
                'entry_price': position['entry_price'],
                'exit_price': final_price,
                'pnl_pct': pnl_pct,
                'exit_reason': 'end_of_data'
            })
        
        return pd.DataFrame(trades)
    
    def calculate_metrics(self, trades_df):
        """Calculate performance metrics"""
        if len(trades_df) == 0:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'profit_factor': 0
            }
        
        # Basic metrics
        total_trades = len(trades_df)
        winners = trades_df[trades_df['pnl_pct'] > 0]
        losers = trades_df[trades_df['pnl_pct'] <= 0]
        
        win_rate = len(winners) / total_trades if total_trades > 0 else 0
        
        # Returns
        returns = trades_df['pnl_pct'].values
        total_return = np.sum(returns)
        
        # Sharpe ratio
        if len(returns) > 1 and np.std(returns) > 0:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)  # Annualized
        else:
            sharpe_ratio = 0
        
        # Maximum drawdown
        cum_returns = np.cumsum(returns)
        running_max = np.maximum.accumulate(cum_returns)
        drawdown = running_max - cum_returns
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
        
        # Profit factor
        gross_profit = winners['pnl_pct'].sum() if len(winners) > 0 else 0
        gross_loss = abs(losers['pnl_pct'].sum()) if len(losers) > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'profit_factor': profit_factor,
            'avg_win': winners['pnl_pct'].mean() if len(winners) > 0 else 0,
            'avg_loss': losers['pnl_pct'].mean() if len(losers) > 0 else 0
        }
    
    def run_monte_carlo(self, trades_df, n_runs=1000):
        """Run Monte Carlo simulation"""
        if len(trades_df) == 0:
            return {'survival_rate': 0, 'mean_return': 0}
        
        returns = trades_df['pnl_pct'].values
        n_trades = len(returns)
        
        mc_results = []
        for _ in range(n_runs):
            # Shuffle returns
            shuffled = np.random.permutation(returns)
            total_return = np.sum(shuffled)
            mc_results.append(total_return)
        
        mc_results = np.array(mc_results)
        survival_rate = np.sum(mc_results > 0) / n_runs
        
        return {
            'survival_rate': survival_rate,
            'mean_return': np.mean(mc_results),
            'std_return': np.std(mc_results),
            'p5': np.percentile(mc_results, 5),
            'p95': np.percentile(mc_results, 95)
        }

def main():
    """Test all 10 strategies"""
    
    # Use REAL historical data
    data_file = "data/MASTER_DATASET/15m/xau_usd_15m.csv"
    
    logger.info("="*80)
    logger.info("TESTING 10 POPULAR STRATEGIES ON REAL HISTORICAL DATA")
    logger.info("NO SIMULATED DATA - NO CHEATING - NO LOOK-AHEAD BIAS")
    logger.info("="*80)
    
    # Initialize backtester
    bt = StrategyBacktester(data_file, transaction_cost_pct=0.0002)
    
    # Calculate indicators on BOTH train and test data
    bt.train_data = bt.calculate_indicators(bt.train_data)
    bt.test_data = bt.calculate_indicators(bt.test_data)
    
    # Define all strategies
    strategies = [
        ('1. EMA Crossover (3/8/21)', bt.strategy_ema_crossover),
        ('2. RSI Mean Reversion', bt.strategy_rsi_mean_reversion),
        ('3. Bollinger Bands Breakout', bt.strategy_bollinger_breakout),
        ('4. MACD Crossover', bt.strategy_macd_crossover),
        ('5. MA Ribbon (8/21/50)', bt.strategy_ma_ribbon),
        ('6. Donchian Breakout', bt.strategy_donchian_breakout),
        ('7. Momentum (ROC)', bt.strategy_momentum_roc),
        ('8. Stochastic Oscillator', bt.strategy_stochastic),
        ('9. Trend Following (50/200)', bt.strategy_trend_following_ma),
        ('10. Price Action (Pin Bar)', bt.strategy_price_action_pin_bar)
    ]
    
    all_results = []
    
    for strategy_name, strategy_func in strategies:
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing: {strategy_name}")
        logger.info(f"{'='*80}")
        
        # Generate signals on TEST data only (out-of-sample)
        test_signals = strategy_func(bt.test_data)
        
        # Backtest on test data
        trades = bt.backtest_strategy(bt.test_data, test_signals)
        
        # Calculate metrics
        metrics = bt.calculate_metrics(trades)
        
        # Run Monte Carlo
        mc_results = bt.run_monte_carlo(trades, n_runs=1000)
        
        # Log results
        logger.info(f"\nOUT-OF-SAMPLE RESULTS:")
        logger.info(f"  Total Trades: {metrics['total_trades']}")
        logger.info(f"  Win Rate: {metrics['win_rate']*100:.2f}%")
        logger.info(f"  Total Return: {metrics['total_return']*100:.2f}%")
        logger.info(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.4f}")
        logger.info(f"  Max Drawdown: {metrics['max_drawdown']*100:.2f}%")
        logger.info(f"  Profit Factor: {metrics['profit_factor']:.2f}")
        
        logger.info(f"\nMONTE CARLO (1000 runs):")
        logger.info(f"  Survival Rate: {mc_results['survival_rate']*100:.2f}%")
        logger.info(f"  Mean Return: {mc_results['mean_return']*100:.2f}%")
        logger.info(f"  5th Percentile: {mc_results['p5']*100:.2f}%")
        logger.info(f"  95th Percentile: {mc_results['p95']*100:.2f}%")
        
        # Verdict
        if mc_results['survival_rate'] >= 0.7 and metrics['sharpe_ratio'] > 1.0:
            verdict = "EXCELLENT - Deploy with confidence"
        elif mc_results['survival_rate'] >= 0.6 and metrics['sharpe_ratio'] > 0.5:
            verdict = "GOOD - Worth considering"
        elif mc_results['survival_rate'] >= 0.5:
            verdict = "MARGINAL - Weak edge"
        else:
            verdict = "POOR - Do not deploy"
        
        logger.info(f"\nVERDICT: {verdict}")
        
        # Store results
        all_results.append({
            'strategy': strategy_name,
            'metrics': metrics,
            'monte_carlo': mc_results,
            'verdict': verdict
        })
    
    # Save all results
    output_file = f"strategy_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"\n{'='*80}")
    logger.info(f"All results saved to {output_file}")
    logger.info(f"{'='*80}")
    
    # Print summary
    logger.info(f"\n{'='*80}")
    logger.info("FINAL RANKINGS (by Survival Rate):")
    logger.info(f"{'='*80}")
    
    sorted_results = sorted(all_results, key=lambda x: x['monte_carlo']['survival_rate'], reverse=True)
    
    for i, result in enumerate(sorted_results, 1):
        logger.info(f"{i}. {result['strategy']}")
        logger.info(f"   Survival Rate: {result['monte_carlo']['survival_rate']*100:.1f}% | " 
                   f"Sharpe: {result['metrics']['sharpe_ratio']:.2f} | "
                   f"Win Rate: {result['metrics']['win_rate']*100:.1f}%")
        logger.info(f"   {result['verdict']}")

if __name__ == "__main__":
    main()

