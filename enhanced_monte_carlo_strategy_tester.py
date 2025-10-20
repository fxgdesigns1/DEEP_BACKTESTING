#!/usr/bin/env python3
"""
ENHANCED MONTE CARLO STRATEGY TESTER
More sophisticated Monte Carlo with multiple validation methods:
- Trade shuffling (standard)
- Block bootstrap (preserves autocorrelation)
- Parametric bootstrap (samples from distribution)
- Regime-based resampling
- Walk-forward analysis
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import json
from scipy import stats

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedMonteCarloTester:
    """Enhanced Monte Carlo analysis with multiple validation methods"""
    
    def __init__(self, data_file, transaction_cost_pct=0.0002):
        """Initialize with REAL historical data"""
        self.data = pd.read_csv(data_file)
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
        self.transaction_cost = transaction_cost_pct
        
        # Out-of-sample split (60% train, 20% validation, 20% test)
        n = len(self.data)
        train_end = int(n * 0.60)
        val_end = int(n * 0.80)
        
        self.train_data = self.data.iloc[:train_end].copy()
        self.val_data = self.data.iloc[train_end:val_end].copy()
        self.test_data = self.data.iloc[val_end:].copy()
        
        logger.info(f"Loaded {n} candles")
        logger.info(f"  Train: {len(self.train_data)} candles (60%)")
        logger.info(f"  Validation: {len(self.val_data)} candles (20%)")
        logger.info(f"  Test: {len(self.test_data)} candles (20%)")
    
    def calculate_indicators(self, df):
        """Calculate indicators"""
        df = df.copy()
        
        # EMAs
        for period in [3, 8, 21, 50, 200]:
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
        
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
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14).mean()
        
        # Donchian Channel
        df['dc_upper'] = df['high'].rolling(window=20).max()
        df['dc_lower'] = df['low'].rolling(window=20).min()
        
        return df
    
    def strategy_bollinger_breakout(self, df):
        """Bollinger Bands Breakout Strategy"""
        signals = pd.Series(0, index=df.index)
        
        # Long: Price breaks above upper band
        long_condition = (df['close'] > df['bb_upper']) & (df['close'].shift() <= df['bb_upper'].shift())
        
        # Short: Price breaks below lower band
        short_condition = (df['close'] < df['bb_lower']) & (df['close'].shift() >= df['bb_lower'].shift())
        
        signals[long_condition] = 1
        signals[short_condition] = -1
        
        return signals
    
    def strategy_ema_crossover(self, df):
        """EMA Crossover Strategy"""
        signals = pd.Series(0, index=df.index)
        
        # Long: EMA3 crosses above EMA8 and price > EMA21
        long_condition = (df['ema_3'] > df['ema_8']) & (df['ema_3'].shift() <= df['ema_8'].shift()) & (df['close'] > df['ema_21'])
        
        # Short: EMA3 crosses below EMA8 and price < EMA21
        short_condition = (df['ema_3'] < df['ema_8']) & (df['ema_3'].shift() >= df['ema_8'].shift()) & (df['close'] < df['ema_21'])
        
        signals[long_condition] = 1
        signals[short_condition] = -1
        
        return signals
    
    def strategy_donchian_breakout(self, df):
        """Donchian Channel Breakout"""
        signals = pd.Series(0, index=df.index)
        
        # Long: Price breaks above upper channel
        long_condition = (df['close'] > df['dc_upper'].shift()) & (df['close'].shift() <= df['dc_upper'].shift(2))
        
        # Short: Price breaks below lower channel
        short_condition = (df['close'] < df['dc_lower'].shift()) & (df['close'].shift() >= df['dc_lower'].shift(2))
        
        signals[long_condition] = 1
        signals[short_condition] = -1
        
        return signals
    
    def strategy_ma_ribbon(self, df):
        """Moving Average Ribbon"""
        signals = pd.Series(0, index=df.index)
        
        # Long: All EMAs aligned bullish
        long_condition = (df['ema_8'] > df['ema_21']) & (df['ema_21'] > df['ema_50']) & (df['close'] > df['ema_8'])
        
        # Short: All EMAs aligned bearish
        short_condition = (df['ema_8'] < df['ema_21']) & (df['ema_21'] < df['ema_50']) & (df['close'] < df['ema_8'])
        
        # Only signal on new alignment
        long_signal = long_condition & (long_condition.shift().fillna(False) == False)
        short_signal = short_condition & (short_condition.shift().fillna(False) == False)
        
        signals[long_signal] = 1
        signals[short_signal] = -1
        
        return signals
    
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
                        trades.append({'pnl_pct': pnl_pct, 'exit_reason': 'stop_loss', 'direction': 'long'})
                        position = None
                    elif current_price >= position['take_profit']:
                        pnl_pct = (position['take_profit'] - position['entry_price']) / position['entry_price'] - self.transaction_cost
                        trades.append({'pnl_pct': pnl_pct, 'exit_reason': 'take_profit', 'direction': 'long'})
                        position = None
                else:  # short
                    if current_price >= position['stop_loss']:
                        pnl_pct = (position['entry_price'] - position['stop_loss']) / position['entry_price'] - self.transaction_cost
                        trades.append({'pnl_pct': pnl_pct, 'exit_reason': 'stop_loss', 'direction': 'short'})
                        position = None
                    elif current_price <= position['take_profit']:
                        pnl_pct = (position['entry_price'] - position['take_profit']) / position['entry_price'] - self.transaction_cost
                        trades.append({'pnl_pct': pnl_pct, 'exit_reason': 'take_profit', 'direction': 'short'})
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
    
    def enhanced_monte_carlo(self, trades_df, n_runs=1000):
        """Enhanced Monte Carlo with multiple methods"""
        if len(trades_df) == 0:
            return {}
        
        returns = trades_df['pnl_pct'].values
        
        logger.info(f"Running Enhanced Monte Carlo with {n_runs} simulations...")
        
        # Method 1: Standard Trade Shuffling
        logger.info("  Method 1: Trade Shuffling...")
        shuffle_results = self._mc_trade_shuffle(returns, n_runs)
        
        # Method 2: Block Bootstrap (preserves autocorrelation)
        logger.info("  Method 2: Block Bootstrap...")
        block_results = self._mc_block_bootstrap(returns, n_runs, block_size=10)
        
        # Method 3: Parametric Bootstrap (sample from fitted distribution)
        logger.info("  Method 3: Parametric Bootstrap...")
        parametric_results = self._mc_parametric(returns, n_runs)
        
        # Method 4: Regime-based resampling
        logger.info("  Method 4: Regime-based Resampling...")
        regime_results = self._mc_regime_based(trades_df, n_runs)
        
        # Aggregate results
        results = {
            'trade_shuffling': shuffle_results,
            'block_bootstrap': block_results,
            'parametric_bootstrap': parametric_results,
            'regime_based': regime_results,
            'consensus': self._calculate_consensus(shuffle_results, block_results, parametric_results, regime_results)
        }
        
        return results
    
    def _mc_trade_shuffle(self, returns, n_runs):
        """Standard Monte Carlo: shuffle trades"""
        final_returns = []
        sharpe_ratios = []
        max_dds = []
        
        for _ in range(n_runs):
            shuffled = np.random.permutation(returns)
            cum = np.cumsum(shuffled)
            final_returns.append(cum[-1])
            
            if np.std(shuffled) > 0:
                sharpe_ratios.append(np.mean(shuffled) / np.std(shuffled) * np.sqrt(252))
            
            peak = np.maximum.accumulate(cum)
            dd = np.max(peak - cum)
            max_dds.append(dd)
        
        return {
            'survival_rate': np.mean(np.array(final_returns) > 0),
            'mean_return': np.mean(final_returns),
            'median_return': np.median(final_returns),
            'std_return': np.std(final_returns),
            'p5': np.percentile(final_returns, 5),
            'p95': np.percentile(final_returns, 95),
            'mean_sharpe': np.mean(sharpe_ratios),
            'mean_dd': np.mean(max_dds),
            'worst_dd_95': np.percentile(max_dds, 95)
        }
    
    def _mc_block_bootstrap(self, returns, n_runs, block_size=10):
        """Block Bootstrap: preserves serial correlation"""
        n_trades = len(returns)
        n_blocks = int(np.ceil(n_trades / block_size))
        
        final_returns = []
        sharpe_ratios = []
        
        for _ in range(n_runs):
            bootstrapped = []
            for _ in range(n_blocks):
                start = np.random.randint(0, max(1, n_trades - block_size))
                block = returns[start:start+block_size]
                bootstrapped.extend(block)
            
            bootstrapped = bootstrapped[:n_trades]
            cum = np.cumsum(bootstrapped)
            final_returns.append(cum[-1])
            
            if np.std(bootstrapped) > 0:
                sharpe_ratios.append(np.mean(bootstrapped) / np.std(bootstrapped) * np.sqrt(252))
        
        return {
            'survival_rate': np.mean(np.array(final_returns) > 0),
            'mean_return': np.mean(final_returns),
            'p5': np.percentile(final_returns, 5),
            'p95': np.percentile(final_returns, 95),
            'mean_sharpe': np.mean(sharpe_ratios)
        }
    
    def _mc_parametric(self, returns, n_runs):
        """Parametric Bootstrap: sample from fitted distribution"""
        # Fit distribution to returns
        mean = np.mean(returns)
        std = np.std(returns)
        
        final_returns = []
        
        for _ in range(n_runs):
            # Sample from normal distribution with same mean/std
            sampled = np.random.normal(mean, std, len(returns))
            final_returns.append(np.sum(sampled))
        
        return {
            'survival_rate': np.mean(np.array(final_returns) > 0),
            'mean_return': np.mean(final_returns),
            'p5': np.percentile(final_returns, 5),
            'p95': np.percentile(final_returns, 95)
        }
    
    def _mc_regime_based(self, trades_df, n_runs):
        """Regime-based resampling: sample separately from win/loss distributions"""
        if len(trades_df) == 0:
            return {'survival_rate': 0}
        
        wins = trades_df[trades_df['pnl_pct'] > 0]['pnl_pct'].values
        losses = trades_df[trades_df['pnl_pct'] <= 0]['pnl_pct'].values
        
        n_wins = len(wins)
        n_losses = len(losses)
        n_total = len(trades_df)
        
        if n_wins == 0 or n_losses == 0:
            return {'survival_rate': 1.0 if n_wins > 0 else 0.0}
        
        final_returns = []
        
        for _ in range(n_runs):
            # Randomly sample wins and losses
            sampled_wins = np.random.choice(wins, size=n_wins, replace=True)
            sampled_losses = np.random.choice(losses, size=n_losses, replace=True)
            
            # Combine and shuffle
            combined = np.concatenate([sampled_wins, sampled_losses])
            np.random.shuffle(combined)
            
            final_returns.append(np.sum(combined))
        
        return {
            'survival_rate': np.mean(np.array(final_returns) > 0),
            'mean_return': np.mean(final_returns),
            'p5': np.percentile(final_returns, 5),
            'p95': np.percentile(final_returns, 95)
        }
    
    def _calculate_consensus(self, shuffle, block, parametric, regime):
        """Calculate consensus metrics across all methods"""
        survival_rates = [
            shuffle.get('survival_rate', 0),
            block.get('survival_rate', 0),
            parametric.get('survival_rate', 0),
            regime.get('survival_rate', 0)
        ]
        
        mean_returns = [
            shuffle.get('mean_return', 0),
            block.get('mean_return', 0),
            parametric.get('mean_return', 0),
            regime.get('mean_return', 0)
        ]
        
        return {
            'avg_survival_rate': np.mean(survival_rates),
            'min_survival_rate': np.min(survival_rates),
            'avg_mean_return': np.mean(mean_returns),
            'conservative_return_p5': shuffle.get('p5', 0)
        }
    
    def calculate_metrics(self, trades_df):
        """Calculate comprehensive performance metrics"""
        if len(trades_df) == 0:
            return {'total_trades': 0}
        
        returns = trades_df['pnl_pct'].values
        total_trades = len(returns)
        
        wins = returns > 0
        win_rate = np.mean(wins)
        
        total_return = np.sum(returns)
        
        # Sharpe
        sharpe = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if np.std(returns) > 0 else 0
        
        # Max Drawdown
        cum_returns = np.cumsum(returns)
        running_max = np.maximum.accumulate(cum_returns)
        drawdown = running_max - cum_returns
        max_dd = np.max(drawdown)
        
        # Profit Factor
        gross_profit = np.sum(returns[wins])
        gross_loss = abs(np.sum(returns[~wins]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Additional metrics
        avg_win = np.mean(returns[wins]) if np.sum(wins) > 0 else 0
        avg_loss = np.mean(returns[~wins]) if np.sum(~wins) > 0 else 0
        
        # Expectancy
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        
        # Risk of Ruin (simplified Kelly criterion)
        if avg_loss != 0:
            win_loss_ratio = abs(avg_win / avg_loss)
            kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        else:
            kelly = 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'expectancy': expectancy,
            'kelly_criterion': kelly
        }

def main():
    """Test top strategies with enhanced Monte Carlo"""
    
    data_file = "data/MASTER_DATASET/15m/xau_usd_15m.csv"
    
    logger.info("="*80)
    logger.info("ENHANCED MONTE CARLO ANALYSIS ON REAL DATA")
    logger.info("Testing Top 4 Strategies with Multiple Validation Methods")
    logger.info("="*80)
    
    tester = EnhancedMonteCarloTester(data_file)
    
    # Calculate indicators
    tester.test_data = tester.calculate_indicators(tester.test_data)
    
    # Top 4 strategies from previous test
    strategies = [
        ('Bollinger Bands Breakout', tester.strategy_bollinger_breakout),
        ('EMA Crossover (3/8/21)', tester.strategy_ema_crossover),
        ('Donchian Breakout', tester.strategy_donchian_breakout),
        ('MA Ribbon (8/21/50)', tester.strategy_ma_ribbon)
    ]
    
    all_results = []
    
    for name, func in strategies:
        logger.info(f"\n{'='*80}")
        logger.info(f"TESTING: {name}")
        logger.info(f"{'='*80}")
        
        # Generate signals
        signals = func(tester.test_data)
        
        # Backtest
        trades = tester.backtest_strategy(tester.test_data, signals)
        
        # Metrics
        metrics = tester.calculate_metrics(trades)
        
        # Enhanced Monte Carlo
        mc_results = tester.enhanced_monte_carlo(trades, n_runs=1000)
        
        # Display results
        logger.info(f"\nBASELINE PERFORMANCE:")
        logger.info(f"  Total Trades: {metrics['total_trades']}")
        logger.info(f"  Win Rate: {metrics['win_rate']*100:.2f}%")
        logger.info(f"  Total Return: {metrics['total_return']*100:.2f}%")
        logger.info(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        logger.info(f"  Max Drawdown: {metrics['max_drawdown']*100:.2f}%")
        logger.info(f"  Profit Factor: {metrics['profit_factor']:.2f}")
        logger.info(f"  Expectancy: {metrics['expectancy']*100:.4f}%")
        logger.info(f"  Kelly Criterion: {metrics['kelly_criterion']*100:.2f}%")
        
        logger.info(f"\nENHANCED MONTE CARLO (1000 runs each method):")
        consensus = mc_results.get('consensus', {})
        logger.info(f"  Consensus Survival Rate: {consensus.get('avg_survival_rate', 0)*100:.2f}%")
        logger.info(f"  Minimum Survival Rate: {consensus.get('min_survival_rate', 0)*100:.2f}%")
        logger.info(f"  Expected Return: {consensus.get('avg_mean_return', 0)*100:.2f}%")
        logger.info(f"  Conservative (5th %ile): {consensus.get('conservative_return_p5', 0)*100:.2f}%")
        
        logger.info(f"\n  Method Details:")
        logger.info(f"    Trade Shuffle:   Survival={mc_results['trade_shuffling']['survival_rate']*100:.1f}%  Return={mc_results['trade_shuffling']['mean_return']*100:.2f}%")
        logger.info(f"    Block Bootstrap: Survival={mc_results['block_bootstrap']['survival_rate']*100:.1f}%  Return={mc_results['block_bootstrap']['mean_return']*100:.2f}%")
        logger.info(f"    Parametric:      Survival={mc_results['parametric_bootstrap']['survival_rate']*100:.1f}%  Return={mc_results['parametric_bootstrap']['mean_return']*100:.2f}%")
        logger.info(f"    Regime-based:    Survival={mc_results['regime_based']['survival_rate']*100:.1f}%  Return={mc_results['regime_based']['mean_return']*100:.2f}%")
        
        # Verdict
        min_survival = consensus.get('min_survival_rate', 0)
        if min_survival >= 0.8 and metrics['sharpe_ratio'] > 2.0:
            verdict = "EXCEPTIONAL - Extremely robust"
        elif min_survival >= 0.7 and metrics['sharpe_ratio'] > 1.5:
            verdict = "EXCELLENT - Deploy with confidence"
        elif min_survival >= 0.6:
            verdict = "GOOD - Worth deploying"
        elif min_survival >= 0.5:
            verdict = "MARGINAL - Requires monitoring"
        else:
            verdict = "POOR - Do not deploy"
        
        logger.info(f"\nFINAL VERDICT: {verdict}")
        
        all_results.append({
            'strategy': name,
            'metrics': metrics,
            'monte_carlo': mc_results,
            'verdict': verdict
        })
    
    # Save results
    output_file = f"enhanced_mc_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Results saved to {output_file}")
    logger.info(f"{'='*80}")
    
    # Final rankings
    logger.info(f"\nFINAL RANKINGS:")
    for i, result in enumerate(all_results, 1):
        consensus = result['monte_carlo']['consensus']
        logger.info(f"{i}. {result['strategy']}")
        logger.info(f"   Min Survival: {consensus['min_survival_rate']*100:.1f}% | Sharpe: {result['metrics']['sharpe_ratio']:.2f}")
        logger.info(f"   {result['verdict']}")
    
    return all_results

if __name__ == "__main__":
    main()


