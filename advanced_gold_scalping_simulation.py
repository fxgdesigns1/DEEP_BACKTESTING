#!/usr/bin/env python3
"""
ADVANCED GOLD SCALPING SIMULATION
Focused optimization for XAU_USD with advanced parameters and real market conditions
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

class AdvancedGoldScalpingSimulator:
    """Advanced Gold scalping simulation with sophisticated parameters"""
    
    def __init__(self):
        """Initialize the advanced Gold scalping simulator"""
        self.max_workers = min(8, mp.cpu_count())
        self.results_dir = Path("results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Gold-specific parameters
        self.pair = 'XAU_USD'
        self.timeframes = ['5m', '15m', '30m']
        
        # Advanced parameter ranges for Gold
        self.ema_fast_range = [2, 3, 4, 5, 6, 8]
        self.ema_slow_range = [8, 10, 12, 15, 18, 20, 24]
        self.rsi_oversold_range = [20, 25, 30, 35]
        self.rsi_overbought_range = [65, 70, 75, 80]
        self.stop_atr_range = [0.5, 0.6, 0.8, 1.0, 1.2, 1.5]
        self.rr_ratio_range = [1.0, 1.2, 1.5, 2.0, 2.5, 3.0]
        
    def generate_gold_scenarios(self) -> List[Dict[str, Any]]:
        """Generate comprehensive Gold scalping scenarios"""
        scenarios = []
        scenario_id = 0
        
        for timeframe in self.timeframes:
            # 1. Ultra-tight scalping scenarios
            for ema_fast in [2, 3, 4]:
                for ema_slow in [8, 10, 12]:
                    if ema_slow > ema_fast:
                        for rsi_oversold in [20, 25]:
                            for rsi_overbought in [75, 80]:
                                for stop_atr in [0.5, 0.6, 0.8]:
                                    for rr_ratio in [1.0, 1.2, 1.5]:
                                        scenario_id += 1
                                        scenarios.append({
                                            'scenario_id': scenario_id,
                                            'name': f"Gold_UltraTight_{timeframe}_EMA{ema_fast}_{ema_slow}_RSI{rsi_oversold}_{rsi_overbought}_SL{stop_atr}_RR{rr_ratio}",
                                            'pair': self.pair,
                                            'timeframe': timeframe,
                                            'params': {
                                                'ema_fast': ema_fast,
                                                'ema_slow': ema_slow,
                                                'rsi_oversold': rsi_oversold,
                                                'rsi_overbought': rsi_overbought,
                                                'stop_atr_mult': stop_atr,
                                                'take_profit_rr': rr_ratio
                                            },
                                            'variation_type': 'ultra_tight_scalping'
                                        })
            
            # 2. Balanced scalping scenarios
            for ema_fast in [3, 4, 5, 6]:
                for ema_slow in [12, 15, 18, 20]:
                    if ema_slow > ema_fast:
                        for rsi_oversold in [25, 30]:
                            for rsi_overbought in [70, 75]:
                                for stop_atr in [0.8, 1.0, 1.2]:
                                    for rr_ratio in [1.2, 1.5, 2.0]:
                                        scenario_id += 1
                                        scenarios.append({
                                            'scenario_id': scenario_id,
                                            'name': f"Gold_Balanced_{timeframe}_EMA{ema_fast}_{ema_slow}_RSI{rsi_oversold}_{rsi_overbought}_SL{stop_atr}_RR{rr_ratio}",
                                            'pair': self.pair,
                                            'timeframe': timeframe,
                                            'params': {
                                                'ema_fast': ema_fast,
                                                'ema_slow': ema_slow,
                                                'rsi_oversold': rsi_oversold,
                                                'rsi_overbought': rsi_overbought,
                                                'stop_atr_mult': stop_atr,
                                                'take_profit_rr': rr_ratio
                                            },
                                            'variation_type': 'balanced_scalping'
                                        })
            
            # 3. Conservative scalping scenarios
            for ema_fast in [5, 6, 8]:
                for ema_slow in [18, 20, 24]:
                    if ema_slow > ema_fast:
                        for rsi_oversold in [30, 35]:
                            for rsi_overbought in [65, 70]:
                                for stop_atr in [1.0, 1.2, 1.5]:
                                    for rr_ratio in [1.5, 2.0, 2.5, 3.0]:
                                        scenario_id += 1
                                        scenarios.append({
                                            'scenario_id': scenario_id,
                                            'name': f"Gold_Conservative_{timeframe}_EMA{ema_fast}_{ema_slow}_RSI{rsi_oversold}_{rsi_overbought}_SL{stop_atr}_RR{rr_ratio}",
                                            'pair': self.pair,
                                            'timeframe': timeframe,
                                            'params': {
                                                'ema_fast': ema_fast,
                                                'ema_slow': ema_slow,
                                                'rsi_oversold': rsi_oversold,
                                                'rsi_overbought': rsi_overbought,
                                                'stop_atr_mult': stop_atr,
                                                'take_profit_rr': rr_ratio
                                            },
                                            'variation_type': 'conservative_scalping'
                                        })
        
        logger.info(f"Generated {len(scenarios)} Gold scalping scenarios")
        return scenarios
    
    def create_realistic_gold_data(self, timeframe: str) -> pd.DataFrame:
        """Create realistic Gold market data with proper volatility and trends"""
        # Generate 2 years of data
        if timeframe == '5m':
            periods = 2 * 365 * 24 * 12  # 2 years, 5-minute intervals
            freq = '5min'
        elif timeframe == '15m':
            periods = 2 * 365 * 24 * 4   # 2 years, 15-minute intervals
            freq = '15min'
        elif timeframe == '30m':
            periods = 2 * 365 * 24 * 2   # 2 years, 30-minute intervals
            freq = '30min'
        else:
            periods = 2 * 365 * 24       # 2 years, 1-hour intervals
            freq = '1H'
        
        dates = pd.date_range(start='2023-01-01', periods=periods, freq=freq)
        
        # Gold-specific characteristics
        base_price = 1800.0  # Starting price around $1800
        volatility = 0.0015  # 0.15% volatility per period (realistic for Gold)
        trend_strength = 0.0001  # Slight upward trend
        
        # Generate realistic price movements with Gold characteristics
        np.random.seed(42)  # For reproducible results
        
        # Add some market sessions and volatility clustering
        session_multipliers = []
        for i in range(periods):
            hour = dates[i].hour
            # Higher volatility during London/NY overlap (13-17 UTC)
            if 13 <= hour <= 17:
                session_multipliers.append(1.5)
            # Medium volatility during London session (8-17 UTC)
            elif 8 <= hour <= 17:
                session_multipliers.append(1.2)
            # Lower volatility during Asian session
            else:
                session_multipliers.append(0.8)
        
        # Generate returns with volatility clustering
        returns = []
        for i in range(periods):
            # Base return with trend
            base_return = np.random.normal(trend_strength, volatility * session_multipliers[i])
            
            # Add some volatility clustering (GARCH-like effect)
            if i > 0 and abs(returns[-1]) > volatility * 2:
                base_return *= 1.2  # Higher volatility after large moves
            
            returns.append(base_return)
        
        # Generate prices
        prices = [base_price]
        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            prices.append(new_price)
        
        # Create OHLC data with realistic spreads
        data = pd.DataFrame({
            'open': prices,
            'high': prices,  # Initialize with prices, will be adjusted below
            'low': prices,   # Initialize with prices, will be adjusted below
            'close': prices,
            'volume': np.random.randint(500, 5000, periods)
        }, index=dates)
        
        # Generate realistic high/low with spreads
        for i in range(periods):
            price = prices[i]
            spread = price * 0.0002  # 0.02% spread (realistic for Gold)
            
            # Random high/low within realistic range
            high_offset = np.random.uniform(0, spread * 2)
            low_offset = np.random.uniform(0, spread * 2)
            
            data.iloc[i, data.columns.get_loc('high')] = price + high_offset
            data.iloc[i, data.columns.get_loc('low')] = price - low_offset
            
            # Ensure OHLC consistency
            data.iloc[i, data.columns.get_loc('high')] = max(
                data.iloc[i, data.columns.get_loc('high')],
                data.iloc[i, data.columns.get_loc('open')],
                data.iloc[i, data.columns.get_loc('close')]
            )
            data.iloc[i, data.columns.get_loc('low')] = min(
                data.iloc[i, data.columns.get_loc('low')],
                data.iloc[i, data.columns.get_loc('open')],
                data.iloc[i, data.columns.get_loc('close')]
            )
        
        return data
    
    def simulate_gold_strategy(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate a single Gold scalping strategy"""
        try:
            # Create realistic Gold data
            data = self.create_realistic_gold_data(scenario['timeframe'])
            
            # Run strategy simulation
            results = self.run_gold_strategy_simulation(data, scenario['params'])
            
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
            logger.error(f"Error simulating Gold scenario {scenario['scenario_id']}: {str(e)}")
            return {
                'scenario_id': scenario['scenario_id'],
                'status': 'failed',
                'error': str(e)
            }
    
    def run_gold_strategy_simulation(self, data: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Gold strategy simulation with enhanced logic"""
        try:
            # Calculate technical indicators
            data = self.calculate_gold_indicators(data, params)
            
            # Generate enhanced signals for Gold
            signals = self.generate_gold_signals(data, params)
            
            # Execute trades with Gold-specific logic
            trades = self.execute_gold_trades(data, signals, params)
            
            # Calculate performance metrics
            metrics = self.calculate_gold_metrics(trades, data)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error in Gold strategy simulation: {str(e)}")
            raise
    
    def calculate_gold_indicators(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """Calculate technical indicators optimized for Gold"""
        # EMA
        data['ema_fast'] = data['close'].ewm(span=params['ema_fast']).mean()
        data['ema_slow'] = data['close'].ewm(span=params['ema_slow']).mean()
        
        # RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # ATR (Average True Range)
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        data['atr'] = true_range.rolling(window=14).mean()
        
        # Gold-specific indicators
        # Price momentum
        data['momentum'] = data['close'].pct_change(5)
        
        # Volatility (for Gold, this is important)
        data['volatility'] = data['close'].rolling(window=20).std()
        
        # Volume-weighted average price (simplified)
        data['vwap'] = (data['close'] * data['volume']).rolling(window=20).sum() / data['volume'].rolling(window=20).sum()
        
        return data
    
    def generate_gold_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """Generate enhanced trading signals for Gold"""
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        signals['position'] = 0
        
        # Enhanced EMA crossover signals
        ema_bullish = (data['ema_fast'] > data['ema_slow']) & (data['ema_fast'].shift(1) <= data['ema_slow'].shift(1))
        ema_bearish = (data['ema_fast'] < data['ema_slow']) & (data['ema_fast'].shift(1) >= data['ema_slow'].shift(1))
        
        # RSI conditions
        rsi_oversold = data['rsi'] < params['rsi_oversold']
        rsi_overbought = data['rsi'] > params['rsi_overbought']
        
        # Gold-specific conditions
        # Price above/below VWAP
        price_above_vwap = data['close'] > data['vwap']
        price_below_vwap = data['close'] < data['vwap']
        
        # Momentum confirmation
        positive_momentum = data['momentum'] > 0
        negative_momentum = data['momentum'] < 0
        
        # Enhanced buy signals (more conservative for Gold)
        buy_signal = (ema_bullish & rsi_oversold & price_above_vwap & positive_momentum)
        
        # Enhanced sell signals
        sell_signal = (ema_bearish & rsi_overbought & price_below_vwap & negative_momentum)
        
        signals.loc[buy_signal, 'signal'] = 1
        signals.loc[sell_signal, 'signal'] = -1
        
        return signals
    
    def execute_gold_trades(self, data: pd.DataFrame, signals: pd.DataFrame, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute trades with Gold-specific logic"""
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
                
                # Calculate stop loss and take profit (Gold-specific)
                if position == 1:  # Long position
                    stop_loss = entry_price - (atr * params['stop_atr_mult'])
                    take_profit = entry_price + (atr * params['stop_atr_mult'] * params['take_profit_rr'])
                    
                    # Additional exit conditions for Gold
                    # Exit if RSI becomes overbought
                    if data.loc[timestamp, 'rsi'] > 80:
                        current_price = data.loc[timestamp, 'close']
                    
                    if current_price <= stop_loss or current_price >= take_profit:
                        # Close position
                        pips = (current_price - entry_price) * 10  # Gold pip calculation
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
                    
                    # Additional exit conditions for Gold
                    # Exit if RSI becomes oversold
                    if data.loc[timestamp, 'rsi'] < 20:
                        current_price = data.loc[timestamp, 'close']
                    
                    if current_price >= stop_loss or current_price <= take_profit:
                        # Close position
                        pips = (entry_price - current_price) * 10  # Gold pip calculation
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
    
    def calculate_gold_metrics(self, trades: List[Dict[str, Any]], data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate performance metrics optimized for Gold trading"""
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_pips': 0,
                'profit_factor': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'avg_trade_duration': 0,
                'trades_per_week': 0
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
        
        # Sharpe ratio
        if total_trades > 1:
            returns = [t['pips'] for t in trades]
            sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Max drawdown
        cumulative_pips = np.cumsum([t['pips'] for t in trades])
        running_max = np.maximum.accumulate(cumulative_pips)
        drawdown = running_max - cumulative_pips
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
        
        # Gold-specific metrics
        avg_trade_duration = np.mean([t['duration'] for t in trades]) if trades else 0
        
        # Calculate trades per week (assuming 2 years of data)
        data_span_weeks = (data.index[-1] - data.index[0]).days / 7
        trades_per_week = total_trades / data_span_weeks if data_span_weeks > 0 else 0
        
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
            'average_loss': total_losses / losing_trades if losing_trades > 0 else 0,
            'avg_trade_duration': avg_trade_duration,
            'trades_per_week': trades_per_week
        }
    
    def run_simulation(self) -> Dict[str, Any]:
        """Run the complete Gold scalping simulation"""
        logger.info("Starting Advanced Gold Scalping Simulation")
        start_time = datetime.now()
        
        # Generate scenarios
        scenarios = self.generate_gold_scenarios()
        logger.info(f"Generated {len(scenarios)} Gold scenarios")
        
        # Run simulations in parallel
        results = []
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_scenario = {executor.submit(self.simulate_gold_strategy, scenario): scenario for scenario in scenarios}
            
            for i, future in enumerate(as_completed(future_to_scenario)):
                try:
                    result = future.result()
                    results.append(result)
                    
                    if (i + 1) % 50 == 0:
                        logger.info(f"Completed {i + 1}/{len(scenarios)} Gold scenarios")
                        
                except Exception as e:
                    logger.error(f"Error in Gold scenario execution: {str(e)}")
        
        # Filter successful results
        successful_results = [r for r in results if r.get('status') == 'success']
        failed_results = [r for r in results if r.get('status') == 'failed']
        
        logger.info(f"Gold simulation completed: {len(successful_results)} successful, {len(failed_results)} failed")
        
        # Sort by win rate and profit factor
        successful_results.sort(key=lambda x: (x.get('win_rate', 0), x.get('profit_factor', 0)), reverse=True)
        
        # Create summary
        end_time = datetime.now()
        execution_time = end_time - start_time
        
        summary = {
            'timestamp': end_time.strftime('%Y%m%d_%H%M%S'),
            'simulation_type': 'Advanced Gold Scalping',
            'total_scenarios': len(scenarios),
            'successful_scenarios': len(successful_results),
            'failed_scenarios': len(failed_results),
            'execution_time': str(execution_time),
            'top_10_strategies': successful_results[:10],
            'best_strategy': successful_results[0] if successful_results else None,
            'timeframe_performance': self.analyze_gold_timeframe_performance(successful_results),
            'parameter_analysis': self.analyze_gold_parameters(successful_results)
        }
        
        # Save results
        self.save_gold_results(summary, successful_results)
        
        return summary
    
    def analyze_gold_timeframe_performance(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze Gold performance by timeframe"""
        timeframe_stats = {}
        
        for result in results:
            timeframe = result.get('timeframe', 'Unknown')
            if timeframe not in timeframe_stats:
                timeframe_stats[timeframe] = {
                    'count': 0,
                    'total_win_rate': 0,
                    'total_profit_factor': 0,
                    'total_trades': 0,
                    'best_win_rate': 0,
                    'best_profit_factor': 0
                }
            
            stats = timeframe_stats[timeframe]
            stats['count'] += 1
            stats['total_win_rate'] += result.get('win_rate', 0)
            stats['total_profit_factor'] += result.get('profit_factor', 0)
            stats['total_trades'] += result.get('total_trades', 0)
            stats['best_win_rate'] = max(stats['best_win_rate'], result.get('win_rate', 0))
            stats['best_profit_factor'] = max(stats['best_profit_factor'], result.get('profit_factor', 0))
        
        # Calculate averages
        for timeframe, stats in timeframe_stats.items():
            if stats['count'] > 0:
                stats['avg_win_rate'] = stats['total_win_rate'] / stats['count']
                stats['avg_profit_factor'] = stats['total_profit_factor'] / stats['count']
                stats['avg_trades'] = stats['total_trades'] / stats['count']
        
        return timeframe_stats
    
    def analyze_gold_parameters(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze which parameters work best for Gold"""
        param_analysis = {
            'ema_fast': {},
            'ema_slow': {},
            'rsi_oversold': {},
            'rsi_overbought': {},
            'stop_atr_mult': {},
            'take_profit_rr': {}
        }
        
        for result in results:
            # Extract parameters from scenario name or add them to results
            # This is a simplified analysis - in practice, you'd store params in results
            
            # For now, just analyze the top performers
            if result.get('win_rate', 0) > 60:  # High win rate strategies
                # This would need to be enhanced to extract actual parameters
                pass
        
        return param_analysis
    
    def save_gold_results(self, summary: Dict[str, Any], results: List[Dict[str, Any]]):
        """Save Gold simulation results"""
        timestamp = summary['timestamp']
        
        # Save summary
        summary_file = self.results_dir / f"gold_scalping_advanced_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Save detailed results
        results_file = self.results_dir / f"gold_scalping_advanced_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Gold results saved to {summary_file} and {results_file}")

def main():
    """Main execution function"""
    simulator = AdvancedGoldScalpingSimulator()
    results = simulator.run_simulation()
    
    print("\n" + "="*80)
    print("ADVANCED GOLD SCALPING SIMULATION RESULTS")
    print("="*80)
    print(f"Total Scenarios: {results['total_scenarios']}")
    print(f"Successful: {results['successful_scenarios']}")
    print(f"Failed: {results['failed_scenarios']}")
    print(f"Execution Time: {results['execution_time']}")
    
    if results['best_strategy']:
        best = results['best_strategy']
        print(f"\n🏆 BEST GOLD STRATEGY:")
        print(f"Timeframe: {best['timeframe']}")
        print(f"Win Rate: {best['win_rate']:.2f}%")
        print(f"Profit Factor: {best['profit_factor']:.2f}")
        print(f"Total Pips: {best['total_pips']:.2f}")
        print(f"Total Trades: {best['total_trades']}")
        print(f"Trades/Week: {best.get('trades_per_week', 0):.1f}")
        print(f"Avg Duration: {best.get('avg_trade_duration', 0):.1f} hours")
    
    print(f"\n📊 TOP 5 GOLD STRATEGIES:")
    for i, strategy in enumerate(results['top_10_strategies'][:5], 1):
        print(f"{i}. {strategy['timeframe']} - "
              f"WR: {strategy['win_rate']:.1f}% - "
              f"PF: {strategy['profit_factor']:.2f} - "
              f"Trades: {strategy['total_trades']} - "
              f"Pips: {strategy['total_pips']:.1f}")

if __name__ == "__main__":
    main()

