#!/usr/bin/env python3
"""
RISK MANAGEMENT SIMULATION
Test different risk management parameters and SL/TP ratios
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RiskManagementSimulator:
    """Risk management focused simulation"""
    
    def __init__(self):
        """Initialize the risk management simulator"""
        self.results_dir = Path("results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Focus on top performing pairs from previous results
        self.currency_pairs = ['AUD_USD', 'EUR_USD', 'GBP_USD', 'XAU_USD']
        self.timeframes = ['15m', '30m', '1h']
        
    def load_data(self, pair: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Load real market data"""
        try:
            data_path = f"data/MASTER_DATASET/{timeframe}/{pair}_{timeframe}.csv"
            if not os.path.exists(data_path):
                return None
            
            data = pd.read_csv(data_path)
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            data.set_index('timestamp', inplace=True)
            
            return data
            
        except Exception as e:
            logger.error(f"Error loading data for {pair} {timeframe}: {str(e)}")
            return None
    
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
    
    def run_risk_strategy(self, data: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run strategy with specific risk management parameters"""
        try:
            # Calculate indicators
            data = self.calculate_indicators(data, params)
            
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
                    signals.append(('buy', i, data.iloc[i]['close'], data.iloc[i]['atr']))
                elif ema_bearish and rsi_overbought:
                    signals.append(('sell', i, data.iloc[i]['close'], data.iloc[i]['atr']))
            
            # Execute trades with risk management
            trades = []
            position = None
            entry_price = 0
            entry_atr = 0
            
            for signal_type, index, price, atr in signals:
                if position is None:  # No position
                    position = signal_type
                    entry_price = price
                    entry_atr = atr
                else:  # Close existing position
                    # Calculate stop loss and take profit based on risk parameters
                    if position == 'buy':
                        stop_loss = entry_price - (entry_atr * params['stop_atr_mult'])
                        take_profit = entry_price + (entry_atr * params['stop_atr_mult'] * params['take_profit_rr'])
                        
                        # Check if price hit stop loss or take profit
                        if price <= stop_loss:
                            pips = (stop_loss - entry_price) * 10000 if 'JPY' not in params.get('pair', '') else (stop_loss - entry_price) * 100
                            exit_price = stop_loss
                        elif price >= take_profit:
                            pips = (take_profit - entry_price) * 10000 if 'JPY' not in params.get('pair', '') else (take_profit - entry_price) * 100
                            exit_price = take_profit
                        else:
                            pips = (price - entry_price) * 10000 if 'JPY' not in params.get('pair', '') else (price - entry_price) * 100
                            exit_price = price
                    else:  # sell
                        stop_loss = entry_price + (entry_atr * params['stop_atr_mult'])
                        take_profit = entry_price - (entry_atr * params['stop_atr_mult'] * params['take_profit_rr'])
                        
                        # Check if price hit stop loss or take profit
                        if price >= stop_loss:
                            pips = (entry_price - stop_loss) * 10000 if 'JPY' not in params.get('pair', '') else (entry_price - stop_loss) * 100
                            exit_price = stop_loss
                        elif price <= take_profit:
                            pips = (entry_price - take_profit) * 10000 if 'JPY' not in params.get('pair', '') else (entry_price - take_profit) * 100
                            exit_price = take_profit
                        else:
                            pips = (entry_price - price) * 10000 if 'JPY' not in params.get('pair', '') else (entry_price - price) * 100
                            exit_price = price
                    
                    trades.append({
                        'direction': position,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'pips': pips,
                        'stop_atr_mult': params['stop_atr_mult'],
                        'take_profit_rr': params['take_profit_rr']
                    })
                    
                    # Open new position
                    position = signal_type
                    entry_price = price
                    entry_atr = atr
            
            # Calculate metrics
            if not trades:
                return {
                    'total_trades': 0,
                    'win_rate': 0,
                    'total_pips': 0,
                    'profit_factor': 0,
                    'max_drawdown': 0,
                    'sharpe_ratio': 0
                }
            
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t['pips'] > 0])
            win_rate = (winning_trades / total_trades) * 100
            
            total_pips = sum(t['pips'] for t in trades)
            total_wins = sum(t['pips'] for t in trades if t['pips'] > 0)
            total_losses = abs(sum(t['pips'] for t in trades if t['pips'] < 0))
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
            
            # Calculate max drawdown
            cumulative_pips = np.cumsum([t['pips'] for t in trades])
            running_max = np.maximum.accumulate(cumulative_pips)
            drawdown = running_max - cumulative_pips
            max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
            
            # Calculate Sharpe ratio
            if total_trades > 1:
                returns = [t['pips'] for t in trades]
                sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
            else:
                sharpe_ratio = 0
            
            return {
                'total_trades': total_trades,
                'win_rate': win_rate,
                'total_pips': total_pips,
                'profit_factor': profit_factor,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'winning_trades': winning_trades,
                'losing_trades': total_trades - winning_trades,
                'average_win': total_wins / winning_trades if winning_trades > 0 else 0,
                'average_loss': total_losses / (total_trades - winning_trades) if (total_trades - winning_trades) > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error in risk strategy: {str(e)}")
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_pips': 0,
                'profit_factor': 0,
                'error': str(e)
            }
    
    def run_simulation(self) -> Dict[str, Any]:
        """Run risk management simulation"""
        logger.info("Starting Risk Management Simulation")
        start_time = datetime.now()
        
        results = []
        scenario_id = 0
        
        # Test different risk management parameters
        for pair in self.currency_pairs:
            for timeframe in self.timeframes:
                logger.info(f"Testing {pair} {timeframe}")
                data = self.load_data(pair, timeframe)
                if data is None:
                    continue
                
                # Base parameters (from successful strategies)
                base_ema_fast = 6 if pair == 'AUD_USD' else 5
                base_ema_slow = 16 if pair == 'AUD_USD' else 13
                base_rsi_oversold = 25 if pair == 'AUD_USD' else 30
                base_rsi_overbought = 72 if pair == 'AUD_USD' else 70
                
                # Test different risk management parameters
                for stop_atr in [0.5, 0.8, 1.0, 1.2, 1.5, 2.0]:
                    for rr_ratio in [1.0, 1.2, 1.5, 2.0, 2.5, 3.0]:
                        scenario_id += 1
                        
                        params = {
                            'pair': pair,
                            'timeframe': timeframe,
                            'ema_fast': base_ema_fast,
                            'ema_slow': base_ema_slow,
                            'rsi_oversold': base_rsi_oversold,
                            'rsi_overbought': base_rsi_overbought,
                            'stop_atr_mult': stop_atr,
                            'take_profit_rr': rr_ratio
                        }
                        
                        result = self.run_risk_strategy(data, params)
                        result.update({
                            'scenario_id': scenario_id,
                            'pair': pair,
                            'timeframe': timeframe,
                            'params': params
                        })
                        
                        results.append(result)
        
        # Filter successful results
        successful_results = [r for r in results if r.get('total_trades', 0) > 0]
        successful_results.sort(key=lambda x: (x.get('win_rate', 0), x.get('profit_factor', 0), -x.get('max_drawdown', 0)), reverse=True)
        
        # Create summary
        end_time = datetime.now()
        execution_time = end_time - start_time
        
        summary = {
            'timestamp': end_time.strftime('%Y%m%d_%H%M%S'),
            'simulation_type': 'Risk Management Optimization',
            'total_scenarios': len(results),
            'successful_scenarios': len(successful_results),
            'execution_time': str(execution_time),
            'top_10_strategies': successful_results[:10],
            'best_strategy': successful_results[0] if successful_results else None,
            'risk_analysis': self.analyze_risk_parameters(successful_results)
        }
        
        # Save results
        self.save_results(summary, successful_results)
        
        return summary
    
    def analyze_risk_parameters(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze which risk parameters work best"""
        risk_analysis = {
            'stop_atr_mult': {},
            'take_profit_rr': {},
            'risk_reward_combinations': {}
        }
        
        for result in results:
            stop_atr = result['params']['stop_atr_mult']
            rr_ratio = result['params']['take_profit_rr']
            
            # Analyze stop ATR multiplier
            if stop_atr not in risk_analysis['stop_atr_mult']:
                risk_analysis['stop_atr_mult'][stop_atr] = {
                    'count': 0,
                    'total_win_rate': 0,
                    'total_profit_factor': 0,
                    'total_max_drawdown': 0
                }
            
            stats = risk_analysis['stop_atr_mult'][stop_atr]
            stats['count'] += 1
            stats['total_win_rate'] += result.get('win_rate', 0)
            stats['total_profit_factor'] += result.get('profit_factor', 0)
            stats['total_max_drawdown'] += result.get('max_drawdown', 0)
            
            # Analyze risk-reward ratio
            if rr_ratio not in risk_analysis['take_profit_rr']:
                risk_analysis['take_profit_rr'][rr_ratio] = {
                    'count': 0,
                    'total_win_rate': 0,
                    'total_profit_factor': 0,
                    'total_max_drawdown': 0
                }
            
            stats = risk_analysis['take_profit_rr'][rr_ratio]
            stats['count'] += 1
            stats['total_win_rate'] += result.get('win_rate', 0)
            stats['total_profit_factor'] += result.get('profit_factor', 0)
            stats['total_max_drawdown'] += result.get('max_drawdown', 0)
            
            # Analyze combinations
            combo_key = f"SL{stop_atr}_RR{rr_ratio}"
            if combo_key not in risk_analysis['risk_reward_combinations']:
                risk_analysis['risk_reward_combinations'][combo_key] = {
                    'count': 0,
                    'total_win_rate': 0,
                    'total_profit_factor': 0,
                    'total_max_drawdown': 0
                }
            
            stats = risk_analysis['risk_reward_combinations'][combo_key]
            stats['count'] += 1
            stats['total_win_rate'] += result.get('win_rate', 0)
            stats['total_profit_factor'] += result.get('profit_factor', 0)
            stats['total_max_drawdown'] += result.get('max_drawdown', 0)
        
        # Calculate averages
        for category in risk_analysis:
            for key, stats in risk_analysis[category].items():
                if stats['count'] > 0:
                    stats['avg_win_rate'] = stats['total_win_rate'] / stats['count']
                    stats['avg_profit_factor'] = stats['total_profit_factor'] / stats['count']
                    stats['avg_max_drawdown'] = stats['total_max_drawdown'] / stats['count']
        
        return risk_analysis
    
    def save_results(self, summary: Dict[str, Any], results: List[Dict[str, Any]]):
        """Save risk management results"""
        timestamp = summary['timestamp']
        
        # Save summary
        summary_file = self.results_dir / f"risk_management_simulation_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Save detailed results
        results_file = self.results_dir / f"risk_management_simulation_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Risk management results saved to {summary_file} and {results_file}")

def main():
    """Main execution function"""
    simulator = RiskManagementSimulator()
    results = simulator.run_simulation()
    
    print("\n" + "="*80)
    print("RISK MANAGEMENT SIMULATION RESULTS")
    print("="*80)
    print(f"Total Scenarios: {results['total_scenarios']}")
    print(f"Successful: {results['successful_scenarios']}")
    print(f"Execution Time: {results['execution_time']}")
    
    if results['best_strategy']:
        best = results['best_strategy']
        print(f"\n🏆 BEST RISK MANAGEMENT STRATEGY:")
        print(f"Pair: {best['pair']}")
        print(f"Timeframe: {best['timeframe']}")
        print(f"Stop Loss ATR: {best['params']['stop_atr_mult']}")
        print(f"Risk/Reward Ratio: {best['params']['take_profit_rr']}")
        print(f"Win Rate: {best['win_rate']:.2f}%")
        print(f"Profit Factor: {best['profit_factor']:.2f}")
        print(f"Max Drawdown: {best['max_drawdown']:.2f}")
        print(f"Sharpe Ratio: {best['sharpe_ratio']:.2f}")
        print(f"Total Trades: {best['total_trades']}")
    
    print(f"\n📊 TOP 5 RISK MANAGEMENT STRATEGIES:")
    for i, strategy in enumerate(results['top_10_strategies'][:5], 1):
        print(f"{i}. {strategy['pair']} {strategy['timeframe']} - "
              f"SL:{strategy['params']['stop_atr_mult']} RR:{strategy['params']['take_profit_rr']} - "
              f"WR: {strategy['win_rate']:.1f}% - "
              f"PF: {strategy['profit_factor']:.2f} - "
              f"DD: {strategy['max_drawdown']:.1f}")

if __name__ == "__main__":
    main()

