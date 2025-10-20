#!/usr/bin/env python3
"""
OPTIMIZED PARALLEL STRATEGY SEARCH CONTROLLER
Utilizes all 16 cores of your AMD Ryzen 9 5950X for maximum performance
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

class OptimizedParallelController:
    """Optimized parallel strategy search controller for maximum CPU utilization"""
    
    def __init__(self, config_path: str = "experiments.yaml"):
        """Initialize the optimized parallel controller"""
        self.config_path = config_path
        self.config = self.load_config(config_path)
        self.results_dir = Path(self.config['meta']['results_dir'])
        self.run_name = self.config['meta']['run_name']
        
        # Create results directory
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Use all available cores (16 cores, 32 threads)
        self.max_workers = min(16, mp.cpu_count())  # Use 16 cores for optimal performance
        logger.info(f"🚀 Optimized Parallel Controller initialized with {self.max_workers} workers")
        
        # Performance tracking
        self.start_time = datetime.now()
        self.completed_experiments = 0
        self.successful_strategies = []
        self.total_experiments = 0
        
    def load_config(self, path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def generate_experiment_combinations(self) -> List[Dict[str, Any]]:
        """Generate all experiment combinations for parallel processing"""
        experiments = []
        
        # Get universe parameters
        pairs = self.config['universe']['pairs']
        timeframes = self.config['universe']['timeframes']
        strategies = self.config['universe']['strategies']
        
        # Generate parameter combinations for each strategy
        for strategy in strategies:
            # Get strategy-specific parameters
            strategy_key = strategy.replace('_strategy', '')
            if strategy_key in self.config['search_space']:
                strategy_params = self.config['search_space'][strategy_key]
                
                # Generate all parameter combinations
                param_combinations = self._generate_parameter_combinations(strategy_params)
                
                # Create experiments for each pair, timeframe, and parameter combination
                for pair in pairs:
                    for timeframe in timeframes:
                        for params in param_combinations:
                            experiments.append({
                                'pair': pair,
                                'timeframe': timeframe,
                                'strategy': strategy,
                                'params': params,
                                'experiment_id': f"{pair}_{timeframe}_{strategy}_{hash(str(params))}"
                            })
        
        self.total_experiments = len(experiments)
        logger.info(f"📊 Generated {self.total_experiments} experiments for parallel processing")
        return experiments
    
    def _generate_parameter_combinations(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate all parameter combinations for a strategy"""
        from itertools import product
        
        # Convert parameter ranges to lists
        param_lists = {}
        for key, value in params.items():
            if isinstance(value, list):
                param_lists[key] = value
            else:
                param_lists[key] = [value]
        
        # Generate all combinations
        keys = list(param_lists.keys())
        values = list(param_lists.values())
        
        combinations = []
        for combo in product(*values):
            combinations.append(dict(zip(keys, combo)))
        
        return combinations
    
    def run_single_experiment(self, experiment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run a single experiment (optimized for parallel execution)"""
        try:
            pair = experiment['pair']
            timeframe = experiment['timeframe']
            strategy = experiment['strategy']
            params = experiment['params']
            
            # Import strategy dynamically
            strategy_module = __import__(f'strategies.{strategy}', fromlist=[strategy])
            strategy_class = getattr(strategy_module, strategy.replace('_strategy', '').title().replace('_', '') + 'Strategy')
            
            # Load data
            data = self._load_data(pair, timeframe)
            if data is None or len(data) < 1000:
                return None
            
            # Initialize strategy
            strategy_instance = strategy_class()
            
            # Run backtest
            results = self._run_optimized_backtest(data, strategy_instance, params, pair, timeframe)
            
            # Check if results pass selection criteria
            if self._passes_selection_criteria(results, timeframe):
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
    
    def _run_optimized_backtest(self, data: pd.DataFrame, strategy, params: Dict, pair: str, timeframe: str) -> Dict[str, Any]:
        """Run optimized backtest with realistic costs"""
        try:
            # Apply parameters to strategy
            for key, value in params.items():
                if hasattr(strategy, key):
                    setattr(strategy, key, value)
            
            # Generate signals - try different method names
            signals = None
            if hasattr(strategy, 'generate_enhanced_signals'):
                signals = strategy.generate_enhanced_signals(pair)
            elif hasattr(strategy, 'generate_signals'):
                signals = strategy.generate_signals(data)
            elif hasattr(strategy, 'check_optimized_conditions'):
                # For strategies that use check_optimized_conditions
                result = strategy.check_optimized_conditions(data, pair)
                if result and result.get('signal'):
                    signals = [result['signal']]
            else:
                # Try to find any signal generation method
                for method_name in ['generate_signals', 'generate_enhanced_signals', 'check_conditions', 'analyze']:
                    if hasattr(strategy, method_name):
                        method = getattr(strategy, method_name)
                        try:
                            if method_name == 'generate_enhanced_signals':
                                signals = method(pair)
                            else:
                                signals = method(data)
                            break
                        except:
                            continue
            
            if not signals:
                return self._empty_results()
            
            # Simulate trades with costs
            trades = self._simulate_trades_optimized(signals, data, pair)
            
            # Calculate performance metrics
            return self._calculate_performance_metrics(trades)
            
        except Exception as e:
            logger.error(f"❌ Backtest error for {pair} {timeframe}: {e}")
            return self._empty_results()
    
    def _simulate_trades_optimized(self, signals: List[Dict], data: pd.DataFrame, pair: str) -> List[Dict]:
        """Optimized trade simulation with realistic costs"""
        trades = []
        
        for signal in signals:
            try:
                entry_idx = data.index.get_loc(signal['timestamp'])
                entry_price = signal['entry_price']
                direction = signal['direction']
                stop_loss = signal['stop_loss']
                take_profit = signal['take_profit']
                
                # Add realistic slippage
                slippage = 0.00005 if 'JPY' not in pair else 0.0001
                if direction == 'BUY':
                    entry_price += slippage
                else:
                    entry_price -= slippage
                
                # Simulate trade progression
                for i in range(entry_idx + 1, min(entry_idx + 100, len(data))):  # Limit lookahead
                    current_price = data.iloc[i]['Close']
                    
                    if direction == 'BUY':
                        if current_price <= stop_loss:
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
    
    def _calculate_performance_metrics(self, trades: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        if not trades:
            return self._empty_results()
        
        wins = [t for t in trades if t['status'] == 'WIN']
        losses = [t for t in trades if t['status'] == 'LOSS']
        
        total_trades = len(trades)
        win_rate = len(wins) / total_trades * 100 if total_trades > 0 else 0
        
        total_pips = sum(t['pips'] for t in trades)
        avg_win = np.mean([t['pips'] for t in wins]) if wins else 0
        avg_loss = np.mean([abs(t['pips']) for t in losses]) if losses else 0
        
        total_wins = sum(t['pips'] for t in wins) if wins else 0
        total_losses = sum(abs(t['pips']) for t in losses) if losses else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Calculate Sharpe ratio
        returns = [t['pips'] for t in trades]
        if returns and np.std(returns) > 0:
            sharpe_ratio = np.mean(returns) / np.std(returns)
        else:
            sharpe_ratio = 0
        
        # Calculate Sortino ratio
        negative_returns = [r for r in returns if r < 0]
        if negative_returns and np.std(negative_returns) > 0:
            sortino_ratio = np.mean(returns) / np.std(negative_returns)
        else:
            sortino_ratio = 0
        
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
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_pips': total_pips,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'wins': len(wins),
            'losses': len(losses)
        }
    
    def _empty_results(self) -> Dict[str, Any]:
        """Return empty results"""
        return {
            'total_trades': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'total_pips': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
            'wins': 0,
            'losses': 0
        }
    
    def _passes_selection_criteria(self, results: Dict[str, Any], timeframe: str) -> bool:
        """Check if results pass selection criteria"""
        selection = self.config['selection']
        
        # Check minimum trades
        min_trades = selection['min_trades_low_tf'] if timeframe in ['1m', '5m', '15m'] else selection['min_trades_high_tf']
        if results['total_trades'] < min_trades:
            return False
        
        # Check performance metrics
        if results['sharpe_ratio'] < selection['min_oos_sharpe']:
            return False
        
        if results['sortino_ratio'] < selection['min_oos_sortino']:
            return False
        
        if abs(results['max_drawdown']) > selection['max_oos_dd']:
            return False
        
        if results['profit_factor'] < selection['min_profit_factor']:
            return False
        
        if results['win_rate'] < selection['min_win_rate'] * 100:
            return False
        
        return True
    
    def run_parallel_search(self):
        """Run the optimized parallel strategy search"""
        logger.info("🚀 Starting Optimized Parallel Strategy Search")
        logger.info(f"💻 Using {self.max_workers} CPU cores for maximum performance")
        logger.info("="*80)
        
        # Generate all experiments
        experiments = self.generate_experiment_combinations()
        
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
                        logger.info(f"✅ SUCCESS: {experiment['pair']} {experiment['timeframe']} {experiment['strategy']}")
                        logger.info(f"   Sharpe: {result['results']['sharpe_ratio']:.3f}, Sortino: {result['results']['sortino_ratio']:.3f}")
                        logger.info(f"   Win Rate: {result['results']['win_rate']:.1f}%, Profit Factor: {result['results']['profit_factor']:.2f}")
                        logger.info(f"   Trades: {result['results']['total_trades']}, Max DD: {result['results']['max_drawdown']:.1f}")
                    else:
                        logger.info(f"❌ Failed: {experiment['pair']} {experiment['timeframe']} {experiment['strategy']}")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing {experiment['experiment_id']}: {e}")
                
                # Progress update every 50 experiments
                if self.completed_experiments % 50 == 0:
                    progress = (self.completed_experiments / max(self.total_experiments, 1)) * 100
                    elapsed = datetime.now() - self.start_time
                    eta = elapsed * (self.total_experiments - self.completed_experiments) / max(self.completed_experiments, 1)
                    
                    logger.info(f"📊 Progress: {progress:.1f}% ({self.completed_experiments}/{self.total_experiments})")
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
                            logger.info(f"   {i}. {exp['pair']} {exp['timeframe']} {exp['strategy']}")
                            logger.info(f"      Sharpe: {results['sharpe_ratio']:.3f}, Sortino: {results['sortino_ratio']:.3f}")
                            logger.info(f"      Win Rate: {results['win_rate']:.1f}%, Profit Factor: {results['profit_factor']:.2f}")
        
        # Final results
        self._save_final_results()
        self._print_final_summary()
    
    def _save_final_results(self):
        """Save final results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"optimized_parallel_results_{timestamp}.json"
        
        final_results = {
            'timestamp': timestamp,
            'total_experiments': self.total_experiments,
            'successful_strategies': len(self.successful_strategies),
            'success_rate': len(self.successful_strategies) / max(self.total_experiments, 1) * 100,
            'execution_time': str(datetime.now() - self.start_time),
            'strategies': self.successful_strategies
        }
        
        with open(results_file, 'w') as f:
            json.dump(final_results, f, indent=2, default=str)
        
        logger.info(f"💾 Results saved to: {results_file}")
    
    def _print_final_summary(self):
        """Print final summary"""
        logger.info("\n" + "="*80)
        logger.info("🏆 OPTIMIZED PARALLEL STRATEGY SEARCH - FINAL RESULTS")
        logger.info("="*80)
        
        total_time = datetime.now() - self.start_time
        logger.info(f"⏱️  Total execution time: {total_time}")
        logger.info(f"📊 Total experiments: {self.total_experiments}")
        logger.info(f"✅ Successful strategies: {len(self.successful_strategies)}")
        logger.info(f"📈 Success rate: {len(self.successful_strategies) / max(self.total_experiments, 1) * 100:.2f}%")
        logger.info(f"💻 CPU utilization: {self.max_workers} cores")
        
        if self.successful_strategies:
            logger.info("\n🥇 TOP 10 STRATEGIES:")
            sorted_strategies = sorted(self.successful_strategies, 
                                     key=lambda x: x['results']['sharpe_ratio'], 
                                     reverse=True)
            
            for i, strategy in enumerate(sorted_strategies[:10], 1):
                exp = strategy['experiment']
                results = strategy['results']
                logger.info(f"\n{i}. {exp['pair']} {exp['timeframe']} {exp['strategy']}")
                logger.info(f"   Sharpe Ratio: {results['sharpe_ratio']:.3f}")
                logger.info(f"   Sortino Ratio: {results['sortino_ratio']:.3f}")
                logger.info(f"   Win Rate: {results['win_rate']:.1f}%")
                logger.info(f"   Profit Factor: {results['profit_factor']:.2f}")
                logger.info(f"   Total Trades: {results['total_trades']}")
                logger.info(f"   Max Drawdown: {results['max_drawdown']:.1f}")
                logger.info(f"   Total Pips: {results['total_pips']:.1f}")
        else:
            logger.info("\n❌ No successful strategies found")
            logger.info("💡 Consider relaxing selection criteria or checking data quality")

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Optimized Parallel Strategy Search Controller')
    parser.add_argument('--config', '-c', default='experiments.yaml', 
                       help='Path to configuration file (default: experiments.yaml)')
    args = parser.parse_args()
    
    try:
        controller = OptimizedParallelController(config_path=args.config)
        controller.run_parallel_search()
    except KeyboardInterrupt:
        logger.info("🛑 Search interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
