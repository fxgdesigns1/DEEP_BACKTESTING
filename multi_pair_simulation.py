#!/usr/bin/env python3
"""
MULTI-PAIR SIMULATION SYSTEM
Comprehensive simulation across multiple currency pairs to find optimal strategies
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiPairSimulator:
    """Multi-pair strategy simulation system"""
    
    def __init__(self):
        """Initialize the multi-pair simulator"""
        self.max_workers = min(8, mp.cpu_count())
        self.results_dir = Path("results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Currency pairs to test
        self.currency_pairs = [
            'EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 
            'USD_CAD', 'NZD_USD', 'EUR_GBP', 'XAU_USD'
        ]
        
        # Timeframes to test
        self.timeframes = ['5m', '15m', '30m', '1h']
        
        # Base strategy parameters (based on our winning strategy)
        self.base_params = {
            'ema_fast': 6,
            'ema_slow': 16,
            'rsi_oversold': 25,
            'rsi_overbought': 72,
            'stop_atr_mult': 1.2,
            'take_profit_rr': 1.2
        }
        
    def generate_simulation_scenarios(self) -> List[Dict[str, Any]]:
        """Generate comprehensive simulation scenarios"""
        scenarios = []
        scenario_id = 0
        
        # 1. Multi-pair optimization with base parameters
        for pair in self.currency_pairs:
            for timeframe in self.timeframes:
                scenario_id += 1
                scenarios.append({
                    'scenario_id': scenario_id,
                    'name': f"{pair}_{timeframe}_Base",
                    'pair': pair,
                    'timeframe': timeframe,
                    'params': self.base_params.copy(),
                    'variation_type': 'base_multi_pair'
                })
        
        # 2. Parameter variations for top pairs
        top_pairs = ['AUD_USD', 'EUR_USD', 'GBP_USD', 'XAU_USD']
        for pair in top_pairs:
            for timeframe in ['15m', '30m']:
                # EMA variations
                for ema_fast in [3, 5, 6, 8]:
                    for ema_slow in [12, 16, 20, 24]:
                        if ema_slow > ema_fast:
                            scenario_id += 1
                            params = self.base_params.copy()
                            params.update({
                                'ema_fast': ema_fast,
                                'ema_slow': ema_slow
                            })
                            scenarios.append({
                                'scenario_id': scenario_id,
                                'name': f"{pair}_{timeframe}_EMA_{ema_fast}_{ema_slow}",
                                'pair': pair,
                                'timeframe': timeframe,
                                'params': params,
                                'variation_type': 'ema_optimization'
                            })
                
                # RSI variations
                for rsi_oversold in [20, 25, 30]:
                    for rsi_overbought in [70, 75, 80]:
                        scenario_id += 1
                        params = self.base_params.copy()
                        params.update({
                            'rsi_oversold': rsi_oversold,
                            'rsi_overbought': rsi_overbought
                        })
                        scenarios.append({
                            'scenario_id': scenario_id,
                            'name': f"{pair}_{timeframe}_RSI_{rsi_oversold}_{rsi_overbought}",
                            'pair': pair,
                            'timeframe': timeframe,
                            'params': params,
                            'variation_type': 'rsi_optimization'
                        })
                
                # Risk management variations
                for stop_atr in [0.8, 1.0, 1.2, 1.5]:
                    for rr_ratio in [1.0, 1.2, 1.5, 2.0]:
                        scenario_id += 1
                        params = self.base_params.copy()
                        params.update({
                            'stop_atr_mult': stop_atr,
                            'take_profit_rr': rr_ratio
                        })
                        scenarios.append({
                            'scenario_id': scenario_id,
                            'name': f"{pair}_{timeframe}_Risk_{stop_atr}_{rr_ratio}",
                            'pair': pair,
                            'timeframe': timeframe,
                            'params': params,
                            'variation_type': 'risk_optimization'
                        })
        
        logger.info(f"Generated {len(scenarios)} simulation scenarios")
        return scenarios
    
    def simulate_strategy(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate a single strategy scenario"""
        try:
            # Load data for the pair and timeframe
            data = self.load_market_data(scenario['pair'], scenario['timeframe'])
            if data is None or len(data) < 100:
                return {
                    'scenario_id': scenario['scenario_id'],
                    'status': 'failed',
                    'error': 'Insufficient data'
                }
            
            # Run strategy simulation
            results = self.run_strategy_simulation(data, scenario['params'])
            
            # Add scenario metadata
            results.update({
                'scenario_id': scenario['scenario_id'],
                'scenario_name': scenario['name'],
                'pair': scenario['pair'],
                'timeframe': scenario['timeframe'],
                'variation_type': scenario['variation_type'],
                'status': 'success'
            })
            
            return results
            
        except Exception as e:
            logger.error(f"Error simulating scenario {scenario['scenario_id']}: {str(e)}")
            return {
                'scenario_id': scenario['scenario_id'],
                'status': 'failed',
                'error': str(e)
            }
    
    def load_market_data(self, pair: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Load market data for simulation"""
        try:
            # Try to load from data directory
            data_path = Path(f"data/{pair}_{timeframe}.csv")
            if data_path.exists():
                data = pd.read_csv(data_path)
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                data.set_index('timestamp', inplace=True)
                return data
            
            # If no data file, create synthetic data for testing
            logger.warning(f"No data file found for {pair}_{timeframe}, creating synthetic data")
            return self.create_synthetic_data(pair, timeframe)
            
        except Exception as e:
            logger.error(f"Error loading data for {pair}_{timeframe}: {str(e)}")
            return None
    
    def create_synthetic_data(self, pair: str, timeframe: str) -> pd.DataFrame:
        """Create synthetic market data for testing"""
        # Generate 2 years of data
        periods = 2 * 365 * 24 * 4  # 2 years, 15-minute intervals
        dates = pd.date_range(start='2023-01-01', periods=periods, freq='15T')
        
        # Base price (different for each pair)
        base_prices = {
            'EUR_USD': 1.1000, 'GBP_USD': 1.2500, 'USD_JPY': 110.0,
            'AUD_USD': 0.7500, 'USD_CAD': 1.3000, 'NZD_USD': 0.7000,
            'EUR_GBP': 0.8800, 'XAU_USD': 1800.0
        }
        
        base_price = base_prices.get(pair, 1.0000)
        
        # Generate realistic price movements
        np.random.seed(42)  # For reproducible results
        returns = np.random.normal(0, 0.0005, periods)  # 0.05% volatility
        prices = [base_price]
        
        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            prices.append(new_price)
        
        # Create OHLC data
        data = pd.DataFrame({
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.0002))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.0002))) for p in prices],
            'close': prices,
            'volume': np.random.randint(1000, 10000, periods)
        }, index=dates)
        
        # Ensure high >= max(open, close) and low <= min(open, close)
        data['high'] = np.maximum(data['high'], np.maximum(data['open'], data['close']))
        data['low'] = np.minimum(data['low'], np.minimum(data['open'], data['close']))
        
        return data
    
    def run_strategy_simulation(self, data: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run the actual strategy simulation"""
        try:
            # Calculate technical indicators
            data = self.calculate_indicators(data, params)
            
            # Generate trading signals
            signals = self.generate_signals(data, params)
            
            # Execute trades
            trades = self.execute_trades(data, signals, params)
            
            # Calculate performance metrics
            metrics = self.calculate_metrics(trades, data)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error in strategy simulation: {str(e)}")
            raise
    
    def calculate_indicators(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """Calculate technical indicators"""
        # EMA
        data['ema_fast'] = data['close'].ewm(span=params['ema_fast']).mean()
        data['ema_slow'] = data['close'].ewm(span=params['ema_slow']).mean()
        
        # RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # ATR
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        data['atr'] = true_range.rolling(window=14).mean()
        
        return data
    
    def generate_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """Generate trading signals"""
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        signals['position'] = 0
        
        # EMA crossover signals
        ema_bullish = (data['ema_fast'] > data['ema_slow']) & (data['ema_fast'].shift(1) <= data['ema_slow'].shift(1))
        ema_bearish = (data['ema_fast'] < data['ema_slow']) & (data['ema_fast'].shift(1) >= data['ema_slow'].shift(1))
        
        # RSI conditions
        rsi_oversold = data['rsi'] < params['rsi_oversold']
        rsi_overbought = data['rsi'] > params['rsi_overbought']
        
        # Combined signals
        buy_signal = ema_bullish & rsi_oversold
        sell_signal = ema_bearish & rsi_overbought
        
        signals.loc[buy_signal, 'signal'] = 1
        signals.loc[sell_signal, 'signal'] = -1
        
        return signals
    
    def execute_trades(self, data: pd.DataFrame, signals: pd.DataFrame, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute trades based on signals"""
        trades = []
        position = 0
        entry_price = 0
        entry_time = None
        
        for i, (timestamp, row) in enumerate(signals.iterrows()):
            signal = row['signal']
            
            if signal == 1 and position == 0:  # Buy signal
                position = 1
                entry_price = data.loc[timestamp, 'close']
                entry_time = timestamp
                
            elif signal == -1 and position == 0:  # Sell signal
                position = -1
                entry_price = data.loc[timestamp, 'close']
                entry_time = timestamp
                
            elif position != 0:  # Check for exit conditions
                current_price = data.loc[timestamp, 'close']
                atr = data.loc[timestamp, 'atr']
                
                # Calculate stop loss and take profit
                if position == 1:  # Long position
                    stop_loss = entry_price - (atr * params['stop_atr_mult'])
                    take_profit = entry_price + (atr * params['stop_atr_mult'] * params['take_profit_rr'])
                    
                    if current_price <= stop_loss or current_price >= take_profit:
                        # Close position
                        pips = (current_price - entry_price) * 10000 if 'JPY' not in params.get('pair', '') else (current_price - entry_price) * 100
                        trades.append({
                            'entry_time': entry_time,
                            'exit_time': timestamp,
                            'direction': 'long',
                            'entry_price': entry_price,
                            'exit_price': current_price,
                            'pips': pips,
                            'duration': (timestamp - entry_time).total_seconds() / 3600  # hours
                        })
                        position = 0
                        
                elif position == -1:  # Short position
                    stop_loss = entry_price + (atr * params['stop_atr_mult'])
                    take_profit = entry_price - (atr * params['stop_atr_mult'] * params['take_profit_rr'])
                    
                    if current_price >= stop_loss or current_price <= take_profit:
                        # Close position
                        pips = (entry_price - current_price) * 10000 if 'JPY' not in params.get('pair', '') else (entry_price - current_price) * 100
                        trades.append({
                            'entry_time': entry_time,
                            'exit_time': timestamp,
                            'direction': 'short',
                            'entry_price': entry_price,
                            'exit_price': current_price,
                            'pips': pips,
                            'duration': (timestamp - entry_time).total_seconds() / 3600  # hours
                        })
                        position = 0
        
        return trades
    
    def calculate_metrics(self, trades: List[Dict[str, Any]], data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate performance metrics"""
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_pips': 0,
                'profit_factor': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0
            }
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pips'] > 0])
        losing_trades = len([t for t in trades if t['pips'] < 0])
        
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        total_pips = sum(t['pips'] for t in trades)
        
        # Profit factor
        total_wins = sum(t['pips'] for t in trades if t['pips'] > 0)
        total_losses = abs(sum(t['pips'] for t in trades if t['pips'] < 0))
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Sharpe ratio (simplified)
        if total_trades > 1:
            returns = [t['pips'] for t in trades]
            sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Max drawdown (simplified)
        cumulative_pips = np.cumsum([t['pips'] for t in trades])
        running_max = np.maximum.accumulate(cumulative_pips)
        drawdown = running_max - cumulative_pips
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_pips': total_pips,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'average_win': total_wins / winning_trades if winning_trades > 0 else 0,
            'average_loss': total_losses / losing_trades if losing_trades > 0 else 0
        }
    
    def run_simulation(self) -> Dict[str, Any]:
        """Run the complete multi-pair simulation"""
        logger.info("Starting Multi-Pair Simulation")
        start_time = datetime.now()
        
        # Generate scenarios
        scenarios = self.generate_simulation_scenarios()
        logger.info(f"Generated {len(scenarios)} scenarios")
        
        # Run simulations in parallel
        results = []
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_scenario = {executor.submit(self.simulate_strategy, scenario): scenario for scenario in scenarios}
            
            for i, future in enumerate(as_completed(future_to_scenario)):
                try:
                    result = future.result()
                    results.append(result)
                    
                    if (i + 1) % 100 == 0:
                        logger.info(f"Completed {i + 1}/{len(scenarios)} scenarios")
                        
                except Exception as e:
                    logger.error(f"Error in scenario execution: {str(e)}")
        
        # Filter successful results
        successful_results = [r for r in results if r.get('status') == 'success']
        failed_results = [r for r in results if r.get('status') == 'failed']
        
        logger.info(f"Simulation completed: {len(successful_results)} successful, {len(failed_results)} failed")
        
        # Sort by win rate and profit factor
        successful_results.sort(key=lambda x: (x.get('win_rate', 0), x.get('profit_factor', 0)), reverse=True)
        
        # Create summary
        end_time = datetime.now()
        execution_time = end_time - start_time
        
        summary = {
            'timestamp': end_time.strftime('%Y%m%d_%H%M%S'),
            'simulation_type': 'Multi-Pair Optimization',
            'total_scenarios': len(scenarios),
            'successful_scenarios': len(successful_results),
            'failed_scenarios': len(failed_results),
            'execution_time': str(execution_time),
            'top_10_strategies': successful_results[:10],
            'best_strategy': successful_results[0] if successful_results else None,
            'pair_performance': self.analyze_pair_performance(successful_results),
            'timeframe_performance': self.analyze_timeframe_performance(successful_results)
        }
        
        # Save results
        self.save_results(summary, successful_results)
        
        return summary
    
    def analyze_pair_performance(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance by currency pair"""
        pair_stats = {}
        
        for result in results:
            pair = result.get('pair', 'Unknown')
            if pair not in pair_stats:
                pair_stats[pair] = {
                    'count': 0,
                    'total_win_rate': 0,
                    'total_profit_factor': 0,
                    'best_win_rate': 0,
                    'best_profit_factor': 0
                }
            
            stats = pair_stats[pair]
            stats['count'] += 1
            stats['total_win_rate'] += result.get('win_rate', 0)
            stats['total_profit_factor'] += result.get('profit_factor', 0)
            stats['best_win_rate'] = max(stats['best_win_rate'], result.get('win_rate', 0))
            stats['best_profit_factor'] = max(stats['best_profit_factor'], result.get('profit_factor', 0))
        
        # Calculate averages
        for pair, stats in pair_stats.items():
            if stats['count'] > 0:
                stats['avg_win_rate'] = stats['total_win_rate'] / stats['count']
                stats['avg_profit_factor'] = stats['total_profit_factor'] / stats['count']
        
        return pair_stats
    
    def analyze_timeframe_performance(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance by timeframe"""
        timeframe_stats = {}
        
        for result in results:
            timeframe = result.get('timeframe', 'Unknown')
            if timeframe not in timeframe_stats:
                timeframe_stats[timeframe] = {
                    'count': 0,
                    'total_win_rate': 0,
                    'total_profit_factor': 0,
                    'best_win_rate': 0,
                    'best_profit_factor': 0
                }
            
            stats = timeframe_stats[timeframe]
            stats['count'] += 1
            stats['total_win_rate'] += result.get('win_rate', 0)
            stats['total_profit_factor'] += result.get('profit_factor', 0)
            stats['best_win_rate'] = max(stats['best_win_rate'], result.get('win_rate', 0))
            stats['best_profit_factor'] = max(stats['best_profit_factor'], result.get('profit_factor', 0))
        
        # Calculate averages
        for timeframe, stats in timeframe_stats.items():
            if stats['count'] > 0:
                stats['avg_win_rate'] = stats['total_win_rate'] / stats['count']
                stats['avg_profit_factor'] = stats['total_profit_factor'] / stats['count']
        
        return timeframe_stats
    
    def save_results(self, summary: Dict[str, Any], results: List[Dict[str, Any]]):
        """Save simulation results"""
        timestamp = summary['timestamp']
        
        # Save summary
        summary_file = self.results_dir / f"multi_pair_simulation_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Save detailed results
        results_file = self.results_dir / f"multi_pair_simulation_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results saved to {summary_file} and {results_file}")

def main():
    """Main execution function"""
    simulator = MultiPairSimulator()
    results = simulator.run_simulation()
    
    print("\n" + "="*80)
    print("MULTI-PAIR SIMULATION RESULTS")
    print("="*80)
    print(f"Total Scenarios: {results['total_scenarios']}")
    print(f"Successful: {results['successful_scenarios']}")
    print(f"Failed: {results['failed_scenarios']}")
    print(f"Execution Time: {results['execution_time']}")
    
    if results['best_strategy']:
        best = results['best_strategy']
        print(f"\n🏆 BEST STRATEGY:")
        print(f"Pair: {best['pair']}")
        print(f"Timeframe: {best['timeframe']}")
        print(f"Win Rate: {best['win_rate']:.2f}%")
        print(f"Profit Factor: {best['profit_factor']:.2f}")
        print(f"Total Pips: {best['total_pips']:.2f}")
        print(f"Total Trades: {best['total_trades']}")
    
    print(f"\n📊 TOP 5 STRATEGIES:")
    for i, strategy in enumerate(results['top_10_strategies'][:5], 1):
        print(f"{i}. {strategy['pair']} {strategy['timeframe']} - "
              f"WR: {strategy['win_rate']:.1f}% - "
              f"PF: {strategy['profit_factor']:.2f} - "
              f"Trades: {strategy['total_trades']}")

if __name__ == "__main__":
    main()

