#!/usr/bin/env python3
"""
INTEGRATED TESTING FRAMEWORK
Comprehensive testing system that integrates all improvements
"""

import pandas as pd
import numpy as np
import logging
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Import our custom modules
from optimized_strategy_v2 import OptimizedStrategyV2
from risk_management_framework import RiskManagementFramework
from advanced_validation_framework import AdvancedValidationFramework

class IntegratedTestingFramework:
    def __init__(self, enhanced_data_dir="data/enhanced"):
        self.enhanced_data_dir = enhanced_data_dir
        self.results_dir = "results/integrated"
        self.logger = logging.getLogger(__name__)
        
        # Create results directory
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Initialize components
        self.strategy = OptimizedStrategyV2()
        self.risk_manager = RiskManagementFramework(initial_capital=10000.0)
        self.validator = AdvancedValidationFramework(enhanced_data_dir)
        
        # Testing parameters
        self.test_symbols = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 'USD_CAD', 'XAU_USD']
        self.test_periods = {
            'in_sample': 0.6,  # 60% for in-sample
            'out_of_sample': 0.4  # 40% for out-of-sample
        }
        
        self.logger.info("🚀 Integrated Testing Framework initialized")
    
    def load_enhanced_data(self):
        """Load enhanced data for testing"""
        print("📊 Loading enhanced data for integrated testing...")
        
        data_files = [f for f in os.listdir(self.enhanced_data_dir) if f.endswith('_enhanced.csv')]
        enhanced_data = {}
        
        for file in data_files:
            currency_pair = file.replace('_1h_enhanced.csv', '').upper()
            file_path = os.path.join(self.enhanced_data_dir, file)
            
            try:
                df = pd.read_csv(file_path)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                
                # Filter to test symbols only
                if currency_pair in self.test_symbols:
                    enhanced_data[currency_pair] = df
                    print(f"✅ Loaded {currency_pair}: {len(df):,} rows")
                
            except Exception as e:
                print(f"❌ Error loading {currency_pair}: {e}")
                
        return enhanced_data
    
    def run_comprehensive_backtest(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Run comprehensive backtest with all improvements"""
        print(f"🔄 Running comprehensive backtest for {symbol}...")
        
        # Split data into in-sample and out-of-sample
        total_length = len(data)
        split_point = int(total_length * self.test_periods['in_sample'])
        
        in_sample_data = data.iloc[:split_point].copy()
        out_of_sample_data = data.iloc[split_point:].copy()
        
        print(f"   In-sample: {len(in_sample_data):,} rows ({in_sample_data.index[0]} to {in_sample_data.index[-1]})")
        print(f"   Out-of-sample: {len(out_of_sample_data):,} rows ({out_of_sample_data.index[0]} to {out_of_sample_data.index[-1]})")
        
        # Run backtest on both periods
        in_sample_results = self._run_backtest_period(in_sample_data, symbol, 'in_sample')
        out_of_sample_results = self._run_backtest_period(out_of_sample_data, symbol, 'out_of_sample')
        
        # Calculate performance metrics
        performance_metrics = self._calculate_comprehensive_metrics(
            in_sample_results, out_of_sample_results, symbol
        )
        
        return {
            'symbol': symbol,
            'in_sample': in_sample_results,
            'out_of_sample': out_of_sample_results,
            'performance_metrics': performance_metrics,
            'data_info': {
                'total_rows': total_length,
                'in_sample_rows': len(in_sample_data),
                'out_of_sample_rows': len(out_of_sample_data),
                'date_range': f"{data.index[0]} to {data.index[-1]}"
            }
        }
    
    def _run_backtest_period(self, data: pd.DataFrame, symbol: str, period_type: str) -> Dict[str, Any]:
        """Run backtest on a specific period"""
        try:
            trades = []
            signals = []
            portfolio_values = []
            current_capital = self.risk_manager.initial_capital
            
            # Process each candle
            for i in range(50, len(data)):  # Start after 50 candles for indicators
                current_data = data.iloc[:i+1].copy()
                
                # Generate signal
                signal = self.strategy.generate_signal(current_data, symbol)
                
                if signal['signal'] != 'NO_SIGNAL' and signal['signal'] != 'ERROR':
                    signals.append(signal)
                    
                    # Calculate position size
                    position_size = self.risk_manager.calculate_position_size(signal, current_capital)
                    
                    if 'error' not in position_size:
                        # Check risk limits
                        risk_check = self.risk_manager.check_risk_limits(signal, position_size)
                        
                        if risk_check['approved']:
                            # Add position
                            position_added = self.risk_manager.add_position(signal, position_size)
                            
                            if position_added:
                                # Simulate trade
                                trade_result = self._simulate_trade(signal, current_data, i)
                                if trade_result:
                                    trades.append(trade_result)
                                    
                                    # Update position
                                    self.risk_manager.update_position(
                                        trade_result['position_id'],
                                        trade_result['exit_price'],
                                        trade_result['exit_reason']
                                    )
                                    
                                    # Update capital
                                    current_capital += trade_result['pnl']
                
                # Record portfolio value
                portfolio_values.append({
                    'timestamp': data.index[i],
                    'capital': current_capital,
                    'positions': len(self.risk_manager.positions)
                })
            
            # Calculate period performance
            period_performance = self._calculate_period_performance(trades, portfolio_values)
            
            return {
                'period_type': period_type,
                'trades': trades,
                'signals': signals,
                'portfolio_values': portfolio_values,
                'performance': period_performance,
                'final_capital': current_capital
            }
            
        except Exception as e:
            self.logger.error(f"Error running backtest for {symbol} {period_type}: {e}")
            return {'error': str(e)}
    
    def _simulate_trade(self, signal: Dict[str, Any], data: pd.DataFrame, entry_idx: int) -> Optional[Dict[str, Any]]:
        """Simulate a trade from entry to exit"""
        try:
            entry_price = signal['entry_price']
            stop_loss = signal['stop_loss']
            take_profit = signal['take_profit']
            direction = signal['direction']
            
            # Find position ID (simplified)
            position_id = f"{signal['symbol']}_{data.index[entry_idx].strftime('%Y%m%d_%H%M%S')}"
            
            # Simulate trade progression
            for i in range(entry_idx + 1, len(data)):
                current_price = data.iloc[i]['Close']
                
                if direction == 'LONG':
                    if current_price <= stop_loss:
                        return {
                            'position_id': position_id,
                            'entry_time': data.index[entry_idx],
                            'exit_time': data.index[i],
                            'entry_price': entry_price,
                            'exit_price': stop_loss,
                            'direction': direction,
                            'status': 'LOSS',
                            'exit_reason': 'STOP_LOSS',
                            'pnl': self._calculate_pnl(entry_price, stop_loss, direction, 1.0)  # Simplified position size
                        }
                    elif current_price >= take_profit:
                        return {
                            'position_id': position_id,
                            'entry_time': data.index[entry_idx],
                            'exit_time': data.index[i],
                            'entry_price': entry_price,
                            'exit_price': take_profit,
                            'direction': direction,
                            'status': 'WIN',
                            'exit_reason': 'TAKE_PROFIT',
                            'pnl': self._calculate_pnl(entry_price, take_profit, direction, 1.0)
                        }
                else:  # SELL
                    if current_price >= stop_loss:
                        return {
                            'position_id': position_id,
                            'entry_time': data.index[entry_idx],
                            'exit_time': data.index[i],
                            'entry_price': entry_price,
                            'exit_price': stop_loss,
                            'direction': direction,
                            'status': 'LOSS',
                            'exit_reason': 'STOP_LOSS',
                            'pnl': self._calculate_pnl(entry_price, stop_loss, direction, 1.0)
                        }
                    elif current_price <= take_profit:
                        return {
                            'position_id': position_id,
                            'entry_time': data.index[entry_idx],
                            'exit_time': data.index[i],
                            'entry_price': entry_price,
                            'exit_price': take_profit,
                            'direction': direction,
                            'status': 'WIN',
                            'exit_reason': 'TAKE_PROFIT',
                            'pnl': self._calculate_pnl(entry_price, take_profit, direction, 1.0)
                        }
            
            # If no exit found, close at end of data
            final_price = data.iloc[-1]['Close']
            return {
                'position_id': position_id,
                'entry_time': data.index[entry_idx],
                'exit_time': data.index[-1],
                'entry_price': entry_price,
                'exit_price': final_price,
                'direction': direction,
                'status': 'UNKNOWN',
                'exit_reason': 'END_OF_DATA',
                'pnl': self._calculate_pnl(entry_price, final_price, direction, 1.0)
            }
            
        except Exception as e:
            self.logger.error(f"Error simulating trade: {e}")
            return None
    
    def _calculate_pnl(self, entry_price: float, exit_price: float, direction: str, position_size: float) -> float:
        """Calculate P&L for a trade"""
        try:
            if direction == 'LONG':
                return (exit_price - entry_price) * position_size
            else:
                return (entry_price - exit_price) * position_size
        except Exception as e:
            self.logger.error(f"Error calculating P&L: {e}")
            return 0.0
    
    def _calculate_period_performance(self, trades: List[Dict], portfolio_values: List[Dict]) -> Dict[str, Any]:
        """Calculate performance metrics for a period"""
        try:
            if not trades:
                return self._empty_performance()
            
            wins = [t for t in trades if t['status'] == 'WIN']
            losses = [t for t in trades if t['status'] == 'LOSS']
            
            total_trades = len(trades)
            win_rate = len(wins) / total_trades * 100 if total_trades > 0 else 0
            
            total_pnl = sum(t['pnl'] for t in trades)
            avg_win = np.mean([t['pnl'] for t in wins]) if wins else 0
            avg_loss = np.mean([t['pnl'] for t in losses]) if losses else 0
            
            total_wins = sum(t['pnl'] for t in wins) if wins else 0
            total_losses = sum(abs(t['pnl']) for t in losses) if losses else 0
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
            
            # Calculate drawdown
            capital_values = [pv['capital'] for pv in portfolio_values]
            if capital_values:
                peak = max(capital_values)
                max_drawdown = (peak - min(capital_values)) / peak
            else:
                max_drawdown = 0
            
            # Calculate Sharpe ratio
            returns = [t['pnl'] for t in trades]
            if returns and np.std(returns) > 0:
                sharpe_ratio = np.mean(returns) / np.std(returns)
            else:
                sharpe_ratio = 0
            
            return {
                'total_trades': total_trades,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'total_pnl': total_pnl,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'wins': len(wins),
                'losses': len(losses)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating period performance: {e}")
            return self._empty_performance()
    
    def _empty_performance(self) -> Dict[str, Any]:
        """Return empty performance metrics"""
        return {
            'total_trades': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'total_pnl': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0,
            'wins': 0,
            'losses': 0
        }
    
    def _calculate_comprehensive_metrics(self, in_sample: Dict, out_of_sample: Dict, symbol: str) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        try:
            # Basic metrics
            in_sample_perf = in_sample.get('performance', self._empty_performance())
            out_of_sample_perf = out_of_sample.get('performance', self._empty_performance())
            
            # Calculate overfitting ratio
            in_sample_pf = in_sample_perf['profit_factor']
            out_of_sample_pf = out_of_sample_perf['profit_factor']
            overfitting_ratio = in_sample_pf / out_of_sample_pf if out_of_sample_pf > 0 else float('inf')
            
            # Calculate consistency score
            consistency_score = self._calculate_consistency_score(in_sample_perf, out_of_sample_perf)
            
            # Calculate risk-adjusted metrics
            risk_metrics = self._calculate_risk_metrics(in_sample, out_of_sample)
            
            return {
                'overfitting_ratio': overfitting_ratio,
                'consistency_score': consistency_score,
                'in_sample_performance': in_sample_perf,
                'out_of_sample_performance': out_of_sample_perf,
                'risk_metrics': risk_metrics,
                'overall_rating': self._calculate_overall_rating(in_sample_perf, out_of_sample_perf, overfitting_ratio)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating comprehensive metrics: {e}")
            return {'error': str(e)}
    
    def _calculate_consistency_score(self, in_sample: Dict, out_of_sample: Dict) -> float:
        """Calculate consistency score between in-sample and out-of-sample performance"""
        try:
            # Compare key metrics
            win_rate_diff = abs(in_sample['win_rate'] - out_of_sample['win_rate'])
            profit_factor_diff = abs(in_sample['profit_factor'] - out_of_sample['profit_factor'])
            sharpe_diff = abs(in_sample['sharpe_ratio'] - out_of_sample['sharpe_ratio'])
            
            # Calculate consistency score (0-100)
            consistency = 100 - (win_rate_diff * 0.4 + profit_factor_diff * 0.4 + sharpe_diff * 0.2)
            
            return max(0, min(100, consistency))
            
        except Exception as e:
            self.logger.error(f"Error calculating consistency score: {e}")
            return 0.0
    
    def _calculate_risk_metrics(self, in_sample: Dict, out_of_sample: Dict) -> Dict[str, Any]:
        """Calculate risk-related metrics"""
        try:
            in_sample_perf = in_sample.get('performance', self._empty_performance())
            out_of_sample_perf = out_of_sample.get('performance', self._empty_performance())
            
            return {
                'max_drawdown_in_sample': in_sample_perf['max_drawdown'],
                'max_drawdown_out_of_sample': out_of_sample_perf['max_drawdown'],
                'sharpe_ratio_in_sample': in_sample_perf['sharpe_ratio'],
                'sharpe_ratio_out_of_sample': out_of_sample_perf['sharpe_ratio'],
                'risk_score': self._calculate_risk_score(in_sample_perf, out_of_sample_perf)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {e}")
            return {}
    
    def _calculate_risk_score(self, in_sample: Dict, out_of_sample: Dict) -> float:
        """Calculate overall risk score (0-100, lower is better)"""
        try:
            # Factors that increase risk score
            risk_factors = []
            
            # High drawdown
            if in_sample['max_drawdown'] > 0.1:  # 10%
                risk_factors.append(20)
            if out_of_sample['max_drawdown'] > 0.1:
                risk_factors.append(30)
            
            # Low Sharpe ratio
            if in_sample['sharpe_ratio'] < 0.5:
                risk_factors.append(15)
            if out_of_sample['sharpe_ratio'] < 0.5:
                risk_factors.append(20)
            
            # Low win rate
            if in_sample['win_rate'] < 40:
                risk_factors.append(10)
            if out_of_sample['win_rate'] < 40:
                risk_factors.append(15)
            
            # High overfitting
            overfitting_ratio = in_sample['profit_factor'] / out_of_sample['profit_factor'] if out_of_sample['profit_factor'] > 0 else float('inf')
            if overfitting_ratio > 2.0:
                risk_factors.append(25)
            
            return min(100, sum(risk_factors))
            
        except Exception as e:
            self.logger.error(f"Error calculating risk score: {e}")
            return 100.0
    
    def _calculate_overall_rating(self, in_sample: Dict, out_of_sample: Dict, overfitting_ratio: float) -> str:
        """Calculate overall rating for the strategy"""
        try:
            # Criteria for rating
            out_of_sample_pf = out_of_sample['profit_factor']
            out_of_sample_wr = out_of_sample['win_rate']
            out_of_sample_sharpe = out_of_sample['sharpe_ratio']
            out_of_sample_dd = out_of_sample['max_drawdown']
            
            # Excellent criteria
            if (out_of_sample_pf > 1.5 and out_of_sample_wr > 55 and 
                out_of_sample_sharpe > 1.0 and out_of_sample_dd < 0.1 and overfitting_ratio < 1.5):
                return 'EXCELLENT'
            
            # Good criteria
            elif (out_of_sample_pf > 1.2 and out_of_sample_wr > 50 and 
                  out_of_sample_sharpe > 0.5 and out_of_sample_dd < 0.15 and overfitting_ratio < 2.0):
                return 'GOOD'
            
            # Fair criteria
            elif (out_of_sample_pf > 1.0 and out_of_sample_wr > 45 and 
                  out_of_sample_sharpe > 0.0 and out_of_sample_dd < 0.2 and overfitting_ratio < 3.0):
                return 'FAIR'
            
            # Poor criteria
            else:
                return 'POOR'
                
        except Exception as e:
            self.logger.error(f"Error calculating overall rating: {e}")
            return 'UNKNOWN'
    
    def run_integrated_testing(self):
        """Run integrated testing on all symbols"""
        print("🚀 Starting Integrated Testing...")
        print("="*80)
        
        # Load enhanced data
        enhanced_data = self.load_enhanced_data()
        
        if not enhanced_data:
            print("❌ No enhanced data found. Run data_quality_enhancer.py first.")
            return
        
        results = {}
        
        for symbol, data in enhanced_data.items():
            print(f"\n--- Testing {symbol} ---")
            
            try:
                # Run comprehensive backtest
                backtest_results = self.run_comprehensive_backtest(data, symbol)
                results[symbol] = backtest_results
                
                # Print summary
                perf = backtest_results['performance_metrics']
                print(f"   Overall Rating: {perf['overall_rating']}")
                print(f"   Out-of-Sample Win Rate: {perf['out_of_sample_performance']['win_rate']:.1f}%")
                print(f"   Out-of-Sample Profit Factor: {perf['out_of_sample_performance']['profit_factor']:.2f}")
                print(f"   Overfitting Ratio: {perf['overfitting_ratio']:.2f}")
                print(f"   Consistency Score: {perf['consistency_score']:.1f}")
                
            except Exception as e:
                self.logger.error(f"Error testing {symbol}: {e}")
                results[symbol] = {'error': str(e)}
        
        # Generate comprehensive report
        self.generate_integrated_report(results)
        
        return results
    
    def generate_integrated_report(self, results: Dict[str, Any]):
        """Generate comprehensive integrated report"""
        print("\n" + "="*80)
        print("📊 INTEGRATED TESTING REPORT")
        print("="*80)
        
        # Summary table
        print(f"\n{'Symbol':<10} {'Rating':<10} {'OOS WR%':<10} {'OOS PF':<10} {'Overfitting':<12} {'Consistency':<12}")
        print("-" * 80)
        
        for symbol, result in results.items():
            if 'error' in result:
                print(f"{symbol:<10} {'ERROR':<10} {'N/A':<10} {'N/A':<10} {'N/A':<12} {'N/A':<12}")
                continue
            
            perf = result['performance_metrics']
            print(f"{symbol:<10} {perf['overall_rating']:<10} {perf['out_of_sample_performance']['win_rate']:<10.1f} {perf['out_of_sample_performance']['profit_factor']:<10.2f} {perf['overfitting_ratio']:<12.2f} {perf['consistency_score']:<12.1f}")
        
        # Best performers
        print(f"\n🏆 BEST PERFORMERS:")
        valid_results = {k: v for k, v in results.items() if 'error' not in v}
        
        if valid_results:
            # Best by rating
            best_rating = max(valid_results.items(), key=lambda x: x[1]['performance_metrics']['overall_rating'])
            print(f"   Best Overall: {best_rating[0]} ({best_rating[1]['performance_metrics']['overall_rating']})")
            
            # Best by out-of-sample performance
            best_oos = max(valid_results.items(), key=lambda x: x[1]['performance_metrics']['out_of_sample_performance']['profit_factor'])
            print(f"   Best OOS Performance: {best_oos[0]} (PF: {best_oos[1]['performance_metrics']['out_of_sample_performance']['profit_factor']:.2f})")
            
            # Most consistent
            most_consistent = max(valid_results.items(), key=lambda x: x[1]['performance_metrics']['consistency_score'])
            print(f"   Most Consistent: {most_consistent[0]} (Score: {most_consistent[1]['performance_metrics']['consistency_score']:.1f})")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(self.results_dir, f"integrated_testing_results_{timestamp}.json")
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {results_file}")
        print("🎯 Integrated testing complete!")

def main():
    """Main execution function"""
    framework = IntegratedTestingFramework()
    framework.run_integrated_testing()

if __name__ == "__main__":
    main()
