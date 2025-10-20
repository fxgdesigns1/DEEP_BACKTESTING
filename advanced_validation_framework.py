#!/usr/bin/env python3
"""
ADVANCED VALIDATION FRAMEWORK
Implements walk-forward analysis, out-of-sample testing, and Monte Carlo validation
"""

import pandas as pd
import numpy as np
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class AdvancedValidationFramework:
    def __init__(self, enhanced_data_dir="data/enhanced"):
        self.enhanced_data_dir = enhanced_data_dir
        self.results_dir = "results/validation"
        self.logger = logging.getLogger(__name__)
        
        # Create results directory
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Validation parameters
        self.walk_forward_periods = 12  # Number of walk-forward periods
        self.training_ratio = 0.7  # 70% for training, 30% for testing
        self.monte_carlo_runs = 1000  # Number of Monte Carlo simulations
        
    def load_enhanced_data(self):
        """Load enhanced data from the enhanced directory"""
        print("📊 Loading enhanced data...")
        
        data_files = [f for f in os.listdir(self.enhanced_data_dir) if f.endswith('_enhanced.csv')]
        enhanced_data = {}
        
        for file in data_files:
            currency_pair = file.replace('_1h_enhanced.csv', '').upper()
            file_path = os.path.join(self.enhanced_data_dir, file)
            
            try:
                df = pd.read_csv(file_path)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                enhanced_data[currency_pair] = df
                print(f"✅ Loaded {currency_pair}: {len(df):,} rows")
                
            except Exception as e:
                print(f"❌ Error loading {currency_pair}: {e}")
                
        return enhanced_data
    
    def walk_forward_analysis(self, data: pd.DataFrame, strategy_func, symbol: str) -> Dict[str, Any]:
        """Perform walk-forward analysis on a strategy"""
        print(f"🔄 Running walk-forward analysis for {symbol}...")
        
        # Calculate period size
        total_length = len(data)
        period_size = total_length // self.walk_forward_periods
        
        results = {
            'symbol': symbol,
            'total_periods': self.walk_forward_periods,
            'period_size': period_size,
            'period_results': [],
            'summary': {}
        }
        
        for period in range(self.walk_forward_periods):
            # Define training and testing periods
            train_start = period * period_size
            train_end = train_start + int(period_size * self.training_ratio)
            test_start = train_end
            test_end = min(test_start + int(period_size * (1 - self.training_ratio)), total_length)
            
            if test_end <= test_start:
                continue
                
            # Split data
            train_data = data.iloc[train_start:train_end].copy()
            test_data = data.iloc[test_start:test_end].copy()
            
            if len(train_data) < 100 or len(test_data) < 50:
                continue
            
            # Run strategy on training data (for parameter optimization)
            train_results = self._run_strategy_period(train_data, strategy_func, f"{symbol}_train_{period}")
            
            # Run strategy on testing data (out-of-sample)
            test_results = self._run_strategy_period(test_data, strategy_func, f"{symbol}_test_{period}")
            
            # Store period results
            period_result = {
                'period': period,
                'train_start': train_data.index[0],
                'train_end': train_data.index[-1],
                'test_start': test_data.index[0],
                'test_end': test_data.index[-1],
                'train_performance': train_results,
                'test_performance': test_results,
                'overfitting_ratio': self._calculate_overfitting_ratio(train_results, test_results)
            }
            
            results['period_results'].append(period_result)
            
            print(f"   Period {period+1}: Train {len(train_data)} rows, Test {len(test_data)} rows")
        
        # Calculate summary statistics
        results['summary'] = self._calculate_walk_forward_summary(results['period_results'])
        
        return results
    
    def _run_strategy_period(self, data: pd.DataFrame, strategy_func, period_name: str) -> Dict[str, Any]:
        """Run strategy on a specific period and return performance metrics"""
        try:
            # Generate signals
            signals = strategy_func(data)
            
            if not signals:
                return self._empty_performance()
            
            # Simulate trades
            trades = self._simulate_trades_with_costs(signals, data)
            
            # Calculate performance metrics
            performance = self._calculate_performance_metrics(trades)
            
            return performance
            
        except Exception as e:
            self.logger.error(f"Error running strategy for {period_name}: {e}")
            return self._empty_performance()
    
    def _simulate_trades_with_costs(self, signals: List[Dict], data: pd.DataFrame) -> List[Dict]:
        """Simulate trades with realistic transaction costs and slippage"""
        trades = []
        
        for signal in signals:
            entry_idx = data.index.get_loc(signal['timestamp'])
            entry_price = signal['entry_price']
            direction = signal['direction']
            stop_loss = signal['stop_loss']
            take_profit = signal['take_profit']
            
            # Add slippage (0.5 pips for major pairs, 1 pip for others)
            slippage = 0.00005 if 'JPY' not in str(signal.get('pair', '')) else 0.0001
            if direction == 'BUY':
                entry_price += slippage
            else:
                entry_price -= slippage
            
            # Simulate trade progression
            for i in range(entry_idx + 1, len(data)):
                current_price = data.iloc[i]['Close']
                
                if direction == 'BUY':
                    if current_price <= stop_loss:
                        # Calculate transaction costs (2 pips round trip)
                        transaction_cost = 0.0002 if 'JPY' not in str(signal.get('pair', '')) else 0.00002
                        net_pips = (stop_loss - entry_price - transaction_cost) * 10000
                        
                        trades.append({
                            'entry_time': signal['timestamp'],
                            'exit_time': data.index[i],
                            'entry_price': entry_price,
                            'exit_price': stop_loss,
                            'direction': direction,
                            'status': 'LOSS',
                            'pips': net_pips,
                            'strategy': signal['strategy'],
                            'confidence': signal['confidence'],
                            'transaction_cost': transaction_cost
                        })
                        break
                    elif current_price >= take_profit:
                        transaction_cost = 0.0002 if 'JPY' not in str(signal.get('pair', '')) else 0.00002
                        net_pips = (take_profit - entry_price - transaction_cost) * 10000
                        
                        trades.append({
                            'entry_time': signal['timestamp'],
                            'exit_time': data.index[i],
                            'entry_price': entry_price,
                            'exit_price': take_profit,
                            'direction': direction,
                            'status': 'WIN',
                            'pips': net_pips,
                            'strategy': signal['strategy'],
                            'confidence': signal['confidence'],
                            'transaction_cost': transaction_cost
                        })
                        break
                else:  # SELL
                    if current_price >= stop_loss:
                        transaction_cost = 0.0002 if 'JPY' not in str(signal.get('pair', '')) else 0.00002
                        net_pips = (entry_price - stop_loss - transaction_cost) * 10000
                        
                        trades.append({
                            'entry_time': signal['timestamp'],
                            'exit_time': data.index[i],
                            'entry_price': entry_price,
                            'exit_price': stop_loss,
                            'direction': direction,
                            'status': 'LOSS',
                            'pips': net_pips,
                            'strategy': signal['strategy'],
                            'confidence': signal['confidence'],
                            'transaction_cost': transaction_cost
                        })
                        break
                    elif current_price <= take_profit:
                        transaction_cost = 0.0002 if 'JPY' not in str(signal.get('pair', '')) else 0.00002
                        net_pips = (entry_price - take_profit - transaction_cost) * 10000
                        
                        trades.append({
                            'entry_time': signal['timestamp'],
                            'exit_time': data.index[i],
                            'entry_price': entry_price,
                            'exit_price': take_profit,
                            'direction': direction,
                            'status': 'WIN',
                            'pips': net_pips,
                            'strategy': signal['strategy'],
                            'confidence': signal['confidence'],
                            'transaction_cost': transaction_cost
                        })
                        break
        
        return trades
    
    def _calculate_performance_metrics(self, trades: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        if not trades:
            return self._empty_performance()
        
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
        
        # Drawdown calculation
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
        
        # Sharpe ratio
        returns = [t['pips'] for t in trades]
        if returns and np.std(returns) > 0:
            sharpe_ratio = np.mean(returns) / np.std(returns)
        else:
            sharpe_ratio = 0
        
        avg_confidence = np.mean([t['confidence'] for t in trades]) if trades else 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_pips': total_pips,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'avg_confidence': avg_confidence,
            'wins': len(wins),
            'losses': len(losses)
        }
    
    def _empty_performance(self) -> Dict[str, Any]:
        """Return empty performance metrics"""
        return {
            'total_trades': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'total_pips': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0,
            'avg_confidence': 0,
            'wins': 0,
            'losses': 0
        }
    
    def _calculate_overfitting_ratio(self, train_performance: Dict, test_performance: Dict) -> float:
        """Calculate overfitting ratio between training and testing performance"""
        if train_performance['total_trades'] == 0 or test_performance['total_trades'] == 0:
            return 0
        
        # Use profit factor as the main metric
        train_pf = train_performance['profit_factor']
        test_pf = test_performance['profit_factor']
        
        if test_pf == 0:
            return float('inf')
        
        return train_pf / test_pf
    
    def _calculate_walk_forward_summary(self, period_results: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics for walk-forward analysis"""
        if not period_results:
            return {}
        
        # Extract test performance metrics
        test_win_rates = [p['test_performance']['win_rate'] for p in period_results]
        test_profit_factors = [p['test_performance']['profit_factor'] for p in period_results]
        test_sharpe_ratios = [p['test_performance']['sharpe_ratio'] for p in period_results]
        overfitting_ratios = [p['overfitting_ratio'] for p in period_results if p['overfitting_ratio'] != float('inf')]
        
        return {
            'avg_test_win_rate': np.mean(test_win_rates),
            'std_test_win_rate': np.std(test_win_rates),
            'avg_test_profit_factor': np.mean(test_profit_factors),
            'std_test_profit_factor': np.std(test_profit_factors),
            'avg_test_sharpe_ratio': np.mean(test_sharpe_ratios),
            'std_test_sharpe_ratio': np.std(test_sharpe_ratios),
            'avg_overfitting_ratio': np.mean(overfitting_ratios) if overfitting_ratios else 0,
            'consistent_periods': len([p for p in period_results if p['test_performance']['profit_factor'] > 1.0]),
            'total_periods': len(period_results)
        }
    
    def monte_carlo_analysis(self, trades: List[Dict], symbol: str) -> Dict[str, Any]:
        """Perform Monte Carlo analysis on trade results"""
        print(f"🎲 Running Monte Carlo analysis for {symbol}...")
        
        if not trades:
            return {'error': 'No trades available for Monte Carlo analysis'}
        
        # Extract trade returns
        trade_returns = [t['pips'] for t in trades]
        
        # Run Monte Carlo simulations
        simulation_results = []
        
        for run in range(self.monte_carlo_runs):
            # Randomly sample trades with replacement
            sample_size = len(trades)
            sampled_returns = np.random.choice(trade_returns, size=sample_size, replace=True)
            
            # Calculate performance metrics for this simulation
            total_return = np.sum(sampled_returns)
            win_rate = len([r for r in sampled_returns if r > 0]) / len(sampled_returns) * 100
            
            # Calculate drawdown
            cumulative_returns = np.cumsum(sampled_returns)
            peak = np.maximum.accumulate(cumulative_returns)
            drawdown = np.min(cumulative_returns - peak)
            
            simulation_results.append({
                'total_return': total_return,
                'win_rate': win_rate,
                'max_drawdown': drawdown
            })
        
        # Calculate statistics
        total_returns = [r['total_return'] for r in simulation_results]
        win_rates = [r['win_rate'] for r in simulation_results]
        drawdowns = [r['max_drawdown'] for r in simulation_results]
        
        return {
            'symbol': symbol,
            'simulations': self.monte_carlo_runs,
            'avg_total_return': np.mean(total_returns),
            'std_total_return': np.std(total_returns),
            'percentile_5': np.percentile(total_returns, 5),
            'percentile_95': np.percentile(total_returns, 95),
            'avg_win_rate': np.mean(win_rates),
            'std_win_rate': np.std(win_rates),
            'avg_max_drawdown': np.mean(drawdowns),
            'std_max_drawdown': np.std(drawdowns),
            'probability_profitable': len([r for r in total_returns if r > 0]) / len(total_returns) * 100
        }
    
    def generate_validation_report(self, validation_results: Dict[str, Any]):
        """Generate comprehensive validation report"""
        print("\n" + "="*80)
        print("📊 ADVANCED VALIDATION REPORT")
        print("="*80)
        
        for symbol, results in validation_results.items():
            if 'error' in results:
                print(f"\n❌ {symbol}: {results['error']}")
                continue
                
            print(f"\n{symbol}:")
            print(f"  Walk-Forward Analysis:")
            print(f"    Avg Test Win Rate: {results['walk_forward']['summary']['avg_test_win_rate']:.1f}% ± {results['walk_forward']['summary']['std_test_win_rate']:.1f}%")
            print(f"    Avg Test Profit Factor: {results['walk_forward']['summary']['avg_test_profit_factor']:.2f} ± {results['walk_forward']['summary']['std_test_profit_factor']:.2f}")
            print(f"    Consistent Periods: {results['walk_forward']['summary']['consistent_periods']}/{results['walk_forward']['summary']['total_periods']}")
            print(f"    Avg Overfitting Ratio: {results['walk_forward']['summary']['avg_overfitting_ratio']:.2f}")
            
            print(f"  Monte Carlo Analysis:")
            print(f"    Avg Total Return: {results['monte_carlo']['avg_total_return']:.1f} ± {results['monte_carlo']['std_total_return']:.1f}")
            print(f"    5th Percentile: {results['monte_carlo']['percentile_5']:.1f}")
            print(f"    95th Percentile: {results['monte_carlo']['percentile_95']:.1f}")
            print(f"    Probability Profitable: {results['monte_carlo']['probability_profitable']:.1f}%")
            print(f"    Avg Max Drawdown: {results['monte_carlo']['avg_max_drawdown']:.1f}")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(self.results_dir, f"validation_results_{timestamp}.json")
        
        with open(results_file, 'w') as f:
            json.dump(validation_results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {results_file}")
    
    def run_comprehensive_validation(self, strategy_func, symbols: List[str] = None):
        """Run comprehensive validation on all symbols"""
        print("🚀 Starting Comprehensive Validation...")
        print("="*80)
        
        # Load enhanced data
        enhanced_data = self.load_enhanced_data()
        
        if not enhanced_data:
            print("❌ No enhanced data found. Run data_quality_enhancer.py first.")
            return
        
        # Filter symbols if specified
        if symbols:
            enhanced_data = {k: v for k, v in enhanced_data.items() if k in symbols}
        
        validation_results = {}
        
        for symbol, data in enhanced_data.items():
            print(f"\n--- Validating {symbol} ---")
            
            try:
                # Walk-forward analysis
                walk_forward_results = self.walk_forward_analysis(data, strategy_func, symbol)
                
                # Get all trades for Monte Carlo analysis
                all_trades = []
                for period_result in walk_forward_results['period_results']:
                    # Simulate trades for the entire dataset
                    signals = strategy_func(data)
                    trades = self._simulate_trades_with_costs(signals, data)
                    all_trades.extend(trades)
                
                # Monte Carlo analysis
                monte_carlo_results = self.monte_carlo_analysis(all_trades, symbol)
                
                validation_results[symbol] = {
                    'walk_forward': walk_forward_results,
                    'monte_carlo': monte_carlo_results
                }
                
            except Exception as e:
                self.logger.error(f"Error validating {symbol}: {e}")
                validation_results[symbol] = {'error': str(e)}
        
        # Generate report
        self.generate_validation_report(validation_results)
        
        return validation_results

def main():
    """Main execution function"""
    # This would be called with actual strategy functions
    print("Advanced Validation Framework initialized.")
    print("Use run_comprehensive_validation() with your strategy function.")

if __name__ == "__main__":
    main()
