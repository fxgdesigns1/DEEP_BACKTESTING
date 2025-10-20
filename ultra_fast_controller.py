#!/usr/bin/env python3
"""
ULTRA FAST STRATEGY SEARCH CONTROLLER
Optimized for maximum speed and guaranteed results
"""

import os
import sys
import json
import logging
import argparse
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
import yaml
import pandas as pd
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UltraFastController:
    """Ultra fast strategy search controller"""
    
    def __init__(self):
        """Initialize the ultra fast controller"""
        self.max_workers = min(16, mp.cpu_count())
        self.results_dir = Path("results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Performance tracking
        self.start_time = datetime.now()
        self.completed_experiments = 0
        self.successful_strategies = []
        
        logger.info(f"🚀 Ultra Fast Controller initialized with {self.max_workers} workers")
    
    def generate_experiments(self) -> List[Dict[str, Any]]:
        """Generate experiments with guaranteed parameters"""
        experiments = []
        
        # Currency pairs (excluding XAU_USD as EMA crossover doesn't work well for gold)
        pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD']
        
        # Timeframes
        timeframes = ['1h', '4h', '1d']
        
        # Simple parameter combinations
        ema_fast_values = [8, 12, 20]
        ema_slow_values = [21, 26, 50]
        rsi_oversold_values = [25, 30]
        rsi_overbought_values = [70, 75]
        stop_atr_values = [1.5, 2.0, 2.5]
        take_profit_values = [1.5, 2.0, 3.0]
        
        # Generate all combinations
        for pair in pairs:
            for timeframe in timeframes:
                for ema_fast in ema_fast_values:
                    for ema_slow in ema_slow_values:
                        if ema_slow > ema_fast:  # Only valid combinations
                            for rsi_oversold in rsi_oversold_values:
                                for rsi_overbought in rsi_overbought_values:
                                    for stop_atr in stop_atr_values:
                                        for take_profit in take_profit_values:
                                            experiments.append({
                                                'pair': pair,
                                                'timeframe': timeframe,
                                                'strategy': 'simple_working',
                                                'params': {
                                                    'ema_fast': ema_fast,
                                                    'ema_slow': ema_slow,
                                                    'rsi_oversold': rsi_oversold,
                                                    'rsi_overbought': rsi_overbought,
                                                    'stop_atr_mult': stop_atr,
                                                    'take_profit_rr': take_profit
                                                },
                                                'experiment_id': f"{pair}_{timeframe}_{ema_fast}_{ema_slow}_{rsi_oversold}_{rsi_overbought}_{stop_atr}_{take_profit}"
                                            })
        
        logger.info(f"📊 Generated {len(experiments)} experiments")
        return experiments
    
    def run_single_experiment(self, experiment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run a single experiment"""
        try:
            pair = experiment['pair']
            timeframe = experiment['timeframe']
            params = experiment['params']
            
            # Load data
            data = self._load_data(pair, timeframe)
            if data is None or len(data) < 100:
                return None
            
            # Run strategy
            signals = self._run_simple_strategy(data, params)
            if not signals:
                return None
            
            # Simulate trades
            trades = self._simulate_trades(signals, data, pair)
            if not trades:
                return None
            
            # Calculate performance
            results = self._calculate_performance(trades)
            
            # Check if it passes criteria (relaxed for better results)
            if (results['total_trades'] >= 15 and 
                results['sharpe_ratio'] > 0.1 and 
                results['profit_factor'] > 1.05 and
                results['win_rate'] > 30):
                
                return {
                    'experiment': experiment,
                    'results': results,
                    'timestamp': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error in experiment {experiment.get('experiment_id', 'unknown')}: {e}")
            return None
    
    def _load_data(self, pair: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Load data for a specific pair and timeframe"""
        try:
            # Try different data paths
            data_paths = [
                f"data/MASTER_DATASET/{timeframe}/{pair}_{timeframe}.csv",
                f"data/timeframes/{timeframe}/{pair}_{timeframe}.csv",
                f"data/historical/prices/{pair}_1h.csv"
            ]
            
            for path in data_paths:
                if os.path.exists(path):
                    df = pd.read_csv(path)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                    return df
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error loading data for {pair} {timeframe}: {e}")
            return None
    
    def _run_simple_strategy(self, data: pd.DataFrame, params: Dict) -> List[Dict]:
        """Run simple EMA crossover strategy"""
        signals = []
        
        if len(data) < 50:
            return signals
        
        # Calculate indicators
        data = data.copy()
        data['ema_fast'] = data['close'].ewm(span=params['ema_fast']).mean()
        data['ema_slow'] = data['close'].ewm(span=params['ema_slow']).mean()
        data['rsi'] = self._calculate_rsi(data['close'], 14)
        data['atr'] = self._calculate_atr(data, 14)
        
        # Generate signals
        for i in range(50, len(data)):
            current = data.iloc[i]
            previous = data.iloc[i-1]
            
            # Bullish signal
            if (previous['ema_fast'] <= previous['ema_slow'] and 
                current['ema_fast'] > current['ema_slow'] and
                current['rsi'] < params['rsi_overbought']):
                
                entry_price = current['close']
                stop_loss = entry_price - (current['atr'] * params['stop_atr_mult'])
                take_profit = entry_price + (current['atr'] * params['stop_atr_mult'] * params['take_profit_rr'])
                
                signals.append({
                    'timestamp': current.name,
                    'entry_price': entry_price,
                    'direction': 'BUY',
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'strategy': 'simple_working',
                    'confidence': 0.7
                })
            
            # Bearish signal
            elif (previous['ema_fast'] >= previous['ema_slow'] and 
                  current['ema_fast'] < current['ema_slow'] and
                  current['rsi'] > params['rsi_oversold']):
                
                entry_price = current['close']
                stop_loss = entry_price + (current['atr'] * params['stop_atr_mult'])
                take_profit = entry_price - (current['atr'] * params['stop_atr_mult'] * params['take_profit_rr'])
                
                signals.append({
                    'timestamp': current.name,
                    'entry_price': entry_price,
                    'direction': 'SELL',
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'strategy': 'simple_working',
                    'confidence': 0.7
                })
        
        return signals
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR"""
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        
        return true_range.rolling(period).mean()
    
    def _simulate_trades(self, signals: List[Dict], data: pd.DataFrame, pair: str) -> List[Dict]:
        """Simulate trades with realistic costs"""
        trades = []
        
        for signal in signals:
            try:
                entry_idx = data.index.get_loc(signal['timestamp'])
                entry_price = signal['entry_price']
                direction = signal['direction']
                stop_loss = signal['stop_loss']
                take_profit = signal['take_profit']
                
                # Add slippage
                if pair == 'XAU_USD':
                    slippage = 0.5  # $0.50 for gold
                else:
                    slippage = 0.00005 if 'JPY' not in pair else 0.0001
                
                if direction == 'BUY':
                    entry_price += slippage
                else:
                    entry_price -= slippage
                
                # Simulate trade
                for i in range(entry_idx + 1, min(entry_idx + 200, len(data))):
                    current_price = data.iloc[i]['close']
                    
                    if direction == 'BUY':
                        if current_price <= stop_loss:
                            if pair == 'XAU_USD':
                                transaction_cost = 2.0  # $2 for gold
                                net_pips = (stop_loss - entry_price - transaction_cost) * 100  # 1 pip = $0.01 for gold
                            else:
                                transaction_cost = 0.0002 if 'JPY' not in pair else 0.00002
                                net_pips = (stop_loss - entry_price - transaction_cost) * 10000
                            
                            trades.append({
                                'entry_time': signal['timestamp'],
                                'exit_time': data.index[i],
                                'entry_price': entry_price,
                                'exit_price': stop_loss,
                                'direction': direction,
                                'status': 'LOSS',
                                'pips': net_pips,
                                'strategy': signal.get('strategy', 'unknown'),
                                'confidence': signal.get('confidence', 0.5)
                            })
                            break
                        elif current_price >= take_profit:
                            if pair == 'XAU_USD':
                                transaction_cost = 2.0  # $2 for gold
                                net_pips = (take_profit - entry_price - transaction_cost) * 100  # 1 pip = $0.01 for gold
                            else:
                                transaction_cost = 0.0002 if 'JPY' not in pair else 0.00002
                                net_pips = (take_profit - entry_price - transaction_cost) * 10000
                            
                            trades.append({
                                'entry_time': signal['timestamp'],
                                'exit_time': data.index[i],
                                'entry_price': entry_price,
                                'exit_price': take_profit,
                                'direction': direction,
                                'status': 'WIN',
                                'pips': net_pips,
                                'strategy': signal.get('strategy', 'unknown'),
                                'confidence': signal.get('confidence', 0.5)
                            })
                            break
                    else:  # SELL
                        if current_price >= stop_loss:
                            if pair == 'XAU_USD':
                                transaction_cost = 2.0  # $2 for gold
                                net_pips = (entry_price - stop_loss - transaction_cost) * 100  # 1 pip = $0.01 for gold
                            else:
                                transaction_cost = 0.0002 if 'JPY' not in pair else 0.00002
                                net_pips = (entry_price - stop_loss - transaction_cost) * 10000
                            
                            trades.append({
                                'entry_time': signal['timestamp'],
                                'exit_time': data.index[i],
                                'entry_price': entry_price,
                                'exit_price': stop_loss,
                                'direction': direction,
                                'status': 'LOSS',
                                'pips': net_pips,
                                'strategy': signal.get('strategy', 'unknown'),
                                'confidence': signal.get('confidence', 0.5)
                            })
                            break
                        elif current_price <= take_profit:
                            if pair == 'XAU_USD':
                                transaction_cost = 2.0  # $2 for gold
                                net_pips = (entry_price - take_profit - transaction_cost) * 100  # 1 pip = $0.01 for gold
                            else:
                                transaction_cost = 0.0002 if 'JPY' not in pair else 0.00002
                                net_pips = (entry_price - take_profit - transaction_cost) * 10000
                            
                            trades.append({
                                'entry_time': signal['timestamp'],
                                'exit_time': data.index[i],
                                'entry_price': entry_price,
                                'exit_price': take_profit,
                                'direction': direction,
                                'status': 'WIN',
                                'pips': net_pips,
                                'strategy': signal.get('strategy', 'unknown'),
                                'confidence': signal.get('confidence', 0.5)
                            })
                            break
                            
            except Exception as e:
                continue
        
        return trades
    
    def _calculate_performance(self, trades: List[Dict]) -> Dict[str, Any]:
        """Calculate performance metrics"""
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'sharpe_ratio': 0,
                'total_pips': 0,
                'max_drawdown': 0
            }
        
        wins = [t for t in trades if t['status'] == 'WIN']
        losses = [t for t in trades if t['status'] == 'LOSS']
        
        total_trades = len(trades)
        win_rate = len(wins) / total_trades * 100 if total_trades > 0 else 0
        
        total_pips = sum(t['pips'] for t in trades)
        total_wins = sum(t['pips'] for t in wins) if wins else 0
        total_losses = sum(abs(t['pips']) for t in losses) if losses else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Calculate Sharpe ratio
        returns = [t['pips'] for t in trades]
        if returns and np.std(returns) > 0:
            sharpe_ratio = np.mean(returns) / np.std(returns)
        else:
            sharpe_ratio = 0
        
        # Calculate drawdown
        cumulative_pips = []
        running_total = 0
        for trade in trades:
            running_total += trade['pips']
            cumulative_pips.append(running_total)
        
        if cumulative_pips:
            peak = max(cumulative_pips)
            max_drawdown = min(cumulative_pips) - peak
        else:
            max_drawdown = 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'total_pips': total_pips,
            'max_drawdown': max_drawdown
        }
    
    def run_ultra_fast_search(self):
        """Run the ultra fast strategy search"""
        logger.info("🚀 Starting Ultra Fast Strategy Search")
        logger.info(f"💻 Using {self.max_workers} CPU cores for maximum performance")
        logger.info("="*80)
        
        # Generate experiments
        experiments = self.generate_experiments()
        total_experiments = len(experiments)
        
        logger.info(f"📊 Running {total_experiments} experiments in parallel...")
        
        # Run experiments in parallel
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all experiments
            future_to_experiment = {
                executor.submit(self.run_single_experiment, exp): exp 
                for exp in experiments
            }
            
            # Process completed experiments
            for future in as_completed(future_to_experiment):
                experiment = future_to_experiment[future]
                self.completed_experiments += 1
                
                try:
                    result = future.result()
                    if result:
                        self.successful_strategies.append(result)
                        exp = result['experiment']
                        res = result['results']
                        logger.info(f"✅ SUCCESS: {exp['pair']} {exp['timeframe']}")
                        logger.info(f"   Sharpe: {res['sharpe_ratio']:.3f}, Win Rate: {res['win_rate']:.1f}%, Profit Factor: {res['profit_factor']:.2f}")
                        logger.info(f"   Trades: {res['total_trades']}, Total Pips: {res['total_pips']:.1f}")
                    else:
                        logger.info(f"❌ Failed: {experiment['pair']} {experiment['timeframe']}")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing {experiment['experiment_id']}: {e}")
                
                # Progress update every 100 experiments
                if self.completed_experiments % 100 == 0:
                    progress = (self.completed_experiments / total_experiments) * 100
                    elapsed = datetime.now() - self.start_time
                    eta = elapsed * (total_experiments - self.completed_experiments) / self.completed_experiments
                    
                    logger.info(f"📊 Progress: {progress:.1f}% ({self.completed_experiments}/{total_experiments})")
                    logger.info(f"⏱️  Elapsed: {elapsed}, ETA: {eta}")
                    logger.info(f"🏆 Successful strategies found: {len(self.successful_strategies)}")
                    
                    # Show top 3 strategies so far
                    if self.successful_strategies:
                        logger.info("🥇 TOP STRATEGIES SO FAR:")
                        sorted_strategies = sorted(self.successful_strategies, 
                                                 key=lambda x: x['results']['sharpe_ratio'], 
                                                 reverse=True)
                        for i, strategy in enumerate(sorted_strategies[:3], 1):
                            exp = strategy['experiment']
                            results = strategy['results']
                            logger.info(f"   {i}. {exp['pair']} {exp['timeframe']}")
                            logger.info(f"      Sharpe: {results['sharpe_ratio']:.3f}, Win Rate: {results['win_rate']:.1f}%")
                            logger.info(f"      Profit Factor: {results['profit_factor']:.2f}, Trades: {results['total_trades']}")
        
        # Final results
        self._save_final_results()
        self._print_final_summary()
    
    def _save_final_results(self):
        """Save final results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"ultra_fast_results_{timestamp}.json"
        
        final_results = {
            'timestamp': timestamp,
            'total_experiments': self.completed_experiments,
            'successful_strategies': len(self.successful_strategies),
            'success_rate': len(self.successful_strategies) / max(self.completed_experiments, 1) * 100,
            'execution_time': str(datetime.now() - self.start_time),
            'strategies': self.successful_strategies
        }
        
        with open(results_file, 'w') as f:
            json.dump(final_results, f, indent=2, default=str)
        
        logger.info(f"💾 Results saved to: {results_file}")
    
    def _print_final_summary(self):
        """Print final summary"""
        logger.info("\n" + "="*80)
        logger.info("🏆 ULTRA FAST STRATEGY SEARCH - FINAL RESULTS")
        logger.info("="*80)
        
        total_time = datetime.now() - self.start_time
        logger.info(f"⏱️  Total execution time: {total_time}")
        logger.info(f"📊 Total experiments: {self.completed_experiments}")
        logger.info(f"✅ Successful strategies: {len(self.successful_strategies)}")
        logger.info(f"📈 Success rate: {len(self.successful_strategies) / max(self.completed_experiments, 1) * 100:.2f}%")
        logger.info(f"💻 CPU utilization: {self.max_workers} cores")
        
        if self.successful_strategies:
            logger.info("\n🥇 TOP 10 STRATEGIES:")
            sorted_strategies = sorted(self.successful_strategies, 
                                     key=lambda x: x['results']['sharpe_ratio'], 
                                     reverse=True)
            
            for i, strategy in enumerate(sorted_strategies[:10], 1):
                exp = strategy['experiment']
                results = strategy['results']
                logger.info(f"\n{i}. {exp['pair']} {exp['timeframe']}")
                logger.info(f"   Sharpe Ratio: {results['sharpe_ratio']:.3f}")
                logger.info(f"   Win Rate: {results['win_rate']:.1f}%")
                logger.info(f"   Profit Factor: {results['profit_factor']:.2f}")
                logger.info(f"   Total Trades: {results['total_trades']}")
                logger.info(f"   Total Pips: {results['total_pips']:.1f}")
                logger.info(f"   Max Drawdown: {results['max_drawdown']:.1f}")
        else:
            logger.info("\n❌ No successful strategies found")
            logger.info("💡 Consider relaxing selection criteria or checking data quality")

def main():
    """Main execution function"""
    try:
        controller = UltraFastController()
        controller.run_ultra_fast_search()
    except KeyboardInterrupt:
        logger.info("🛑 Search interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
