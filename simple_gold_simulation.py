#!/usr/bin/env python3
"""
SIMPLE GOLD SIMULATION
Robust Gold trading simulation with fixed data generation
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

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleGoldSimulator:
    """Simple and robust Gold trading simulation"""
    
    def __init__(self):
        """Initialize the simple Gold simulator"""
        self.results_dir = Path("results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Gold-specific parameters
        self.pair = 'XAU_USD'
        self.timeframes = ['5m', '15m', '30m']
        
    def create_gold_data(self, timeframe: str) -> pd.DataFrame:
        """Create realistic Gold market data"""
        # Generate 1 year of data
        if timeframe == '5m':
            periods = 365 * 24 * 12  # 1 year, 5-minute intervals
            freq = '5min'
        elif timeframe == '15m':
            periods = 365 * 24 * 4   # 1 year, 15-minute intervals
            freq = '15min'
        else:  # 30m
            periods = 365 * 24 * 2   # 1 year, 30-minute intervals
            freq = '30min'
        
        dates = pd.date_range(start='2024-01-01', periods=periods, freq=freq)
        
        # Gold characteristics
        base_price = 2000.0  # Starting price around $2000
        volatility = 0.002   # 0.2% volatility per period
        
        # Generate realistic price movements
        np.random.seed(42)
        returns = np.random.normal(0, volatility, periods)
        prices = [base_price]
        
        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            prices.append(new_price)
        
        # Create OHLC data with proper structure
        data = pd.DataFrame(index=dates)
        data['open'] = prices
        data['high'] = [p * (1 + abs(np.random.normal(0, 0.0005))) for p in prices]
        data['low'] = [p * (1 - abs(np.random.normal(0, 0.0005))) for p in prices]
        data['close'] = prices
        data['volume'] = np.random.randint(1000, 10000, periods)
        
        # Ensure OHLC consistency
        for i in range(len(data)):
            high_val = max(data.iloc[i]['open'], data.iloc[i]['close'], data.iloc[i]['high'])
            low_val = min(data.iloc[i]['open'], data.iloc[i]['close'], data.iloc[i]['low'])
            data.iloc[i, data.columns.get_loc('high')] = high_val
            data.iloc[i, data.columns.get_loc('low')] = low_val
        
        return data
    
    def calculate_indicators(self, data: pd.DataFrame, ema_fast: int, ema_slow: int) -> pd.DataFrame:
        """Calculate technical indicators"""
        # EMA
        data['ema_fast'] = data['close'].ewm(span=ema_fast).mean()
        data['ema_slow'] = data['close'].ewm(span=ema_slow).mean()
        
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
    
    def run_strategy(self, data: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single strategy"""
        try:
            # Calculate indicators
            data = self.calculate_indicators(data, params['ema_fast'], params['ema_slow'])
            
            # Generate signals
            signals = []
            for i in range(1, len(data)):
                # EMA crossover
                ema_bullish = (data.iloc[i]['ema_fast'] > data.iloc[i]['ema_slow'] and 
                              data.iloc[i-1]['ema_fast'] <= data.iloc[i-1]['ema_slow'])
                ema_bearish = (data.iloc[i]['ema_fast'] < data.iloc[i]['ema_slow'] and 
                              data.iloc[i-1]['ema_fast'] >= data.iloc[i-1]['ema_slow'])
                
                # RSI conditions
                rsi_oversold = data.iloc[i]['rsi'] < params['rsi_oversold']
                rsi_overbought = data.iloc[i]['rsi'] > params['rsi_overbought']
                
                # Combined signals
                if ema_bullish and rsi_oversold:
                    signals.append(('buy', i, data.iloc[i]['close']))
                elif ema_bearish and rsi_overbought:
                    signals.append(('sell', i, data.iloc[i]['close']))
            
            # Execute trades
            trades = []
            position = None
            entry_price = 0
            entry_index = 0
            
            for signal_type, index, price in signals:
                if position is None:  # No position
                    position = signal_type
                    entry_price = price
                    entry_index = index
                else:  # Close existing position
                    if position == 'buy':
                        pips = (price - entry_price) * 10  # Gold pip calculation
                    else:
                        pips = (entry_price - price) * 10
                    
                    trades.append({
                        'direction': position,
                        'entry_price': entry_price,
                        'exit_price': price,
                        'pips': pips
                    })
                    
                    # Open new position
                    position = signal_type
                    entry_price = price
                    entry_index = index
            
            # Calculate metrics
            if not trades:
                return {
                    'total_trades': 0,
                    'win_rate': 0,
                    'total_pips': 0,
                    'profit_factor': 0
                }
            
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t['pips'] > 0])
            win_rate = (winning_trades / total_trades) * 100
            
            total_pips = sum(t['pips'] for t in trades)
            total_wins = sum(t['pips'] for t in trades if t['pips'] > 0)
            total_losses = abs(sum(t['pips'] for t in trades if t['pips'] < 0))
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
            
            return {
                'total_trades': total_trades,
                'win_rate': win_rate,
                'total_pips': total_pips,
                'profit_factor': profit_factor,
                'winning_trades': winning_trades,
                'losing_trades': total_trades - winning_trades
            }
            
        except Exception as e:
            logger.error(f"Error in strategy: {str(e)}")
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_pips': 0,
                'profit_factor': 0,
                'error': str(e)
            }
    
    def run_simulation(self) -> Dict[str, Any]:
        """Run the complete Gold simulation"""
        logger.info("Starting Simple Gold Simulation")
        start_time = datetime.now()
        
        results = []
        scenario_id = 0
        
        # Test different parameter combinations
        for timeframe in self.timeframes:
            logger.info(f"Testing {timeframe} timeframe")
            data = self.create_gold_data(timeframe)
            
            for ema_fast in [2, 3, 5, 8]:
                for ema_slow in [12, 16, 20, 24]:
                    if ema_slow > ema_fast:
                        for rsi_oversold in [20, 25, 30]:
                            for rsi_overbought in [70, 75, 80]:
                                scenario_id += 1
                                
                                params = {
                                    'ema_fast': ema_fast,
                                    'ema_slow': ema_slow,
                                    'rsi_oversold': rsi_oversold,
                                    'rsi_overbought': rsi_overbought
                                }
                                
                                result = self.run_strategy(data, params)
                                result.update({
                                    'scenario_id': scenario_id,
                                    'timeframe': timeframe,
                                    'params': params
                                })
                                
                                results.append(result)
        
        # Filter successful results
        successful_results = [r for r in results if r.get('total_trades', 0) > 0]
        successful_results.sort(key=lambda x: (x.get('win_rate', 0), x.get('profit_factor', 0)), reverse=True)
        
        # Create summary
        end_time = datetime.now()
        execution_time = end_time - start_time
        
        summary = {
            'timestamp': end_time.strftime('%Y%m%d_%H%M%S'),
            'simulation_type': 'Simple Gold Trading',
            'total_scenarios': len(results),
            'successful_scenarios': len(successful_results),
            'execution_time': str(execution_time),
            'top_10_strategies': successful_results[:10],
            'best_strategy': successful_results[0] if successful_results else None
        }
        
        # Save results
        self.save_results(summary, successful_results)
        
        return summary
    
    def save_results(self, summary: Dict[str, Any], results: List[Dict[str, Any]]):
        """Save simulation results"""
        timestamp = summary['timestamp']
        
        # Save summary
        summary_file = self.results_dir / f"simple_gold_simulation_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Save detailed results
        results_file = self.results_dir / f"simple_gold_simulation_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results saved to {summary_file} and {results_file}")

def main():
    """Main execution function"""
    simulator = SimpleGoldSimulator()
    results = simulator.run_simulation()
    
    print("\n" + "="*80)
    print("SIMPLE GOLD SIMULATION RESULTS")
    print("="*80)
    print(f"Total Scenarios: {results['total_scenarios']}")
    print(f"Successful: {results['successful_scenarios']}")
    print(f"Execution Time: {results['execution_time']}")
    
    if results['best_strategy']:
        best = results['best_strategy']
        print(f"\n🏆 BEST GOLD STRATEGY:")
        print(f"Timeframe: {best['timeframe']}")
        print(f"EMA: {best['params']['ema_fast']}/{best['params']['ema_slow']}")
        print(f"RSI: {best['params']['rsi_oversold']}/{best['params']['rsi_overbought']}")
        print(f"Win Rate: {best['win_rate']:.2f}%")
        print(f"Profit Factor: {best['profit_factor']:.2f}")
        print(f"Total Pips: {best['total_pips']:.2f}")
        print(f"Total Trades: {best['total_trades']}")
    
    print(f"\n📊 TOP 5 GOLD STRATEGIES:")
    for i, strategy in enumerate(results['top_10_strategies'][:5], 1):
        print(f"{i}. {strategy['timeframe']} EMA{strategy['params']['ema_fast']}/{strategy['params']['ema_slow']} - "
              f"WR: {strategy['win_rate']:.1f}% - "
              f"PF: {strategy['profit_factor']:.2f} - "
              f"Trades: {strategy['total_trades']} - "
              f"Pips: {strategy['total_pips']:.1f}")

if __name__ == "__main__":
    main()

