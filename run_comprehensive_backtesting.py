#!/usr/bin/env python3
"""
COMPREHENSIVE BACKTESTING EXECUTION
Run comprehensive backtesting with live trading data integration
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def main():
    """Main backtesting execution function"""
    
    print("🚀 COMPREHENSIVE BACKTESTING EXECUTION")
    print("=" * 60)
    print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # Import enhanced system
        from enhanced_backtesting_system import EnhancedBacktestingSystem
        
        # Initialize system
        live_data_path = r"H:\My Drive\desktop_backtesting_export"
        bloomberg_data_path = r"E:\deep_backtesting_windows1\deep_backtesting\data"
        
        print("📊 Initializing Enhanced Backtesting System...")
        system = EnhancedBacktestingSystem(live_data_path, bloomberg_data_path)
        
        # Analyze available data first
        print("\n🔍 ANALYZING AVAILABLE DATA")
        print("-" * 50)
        
        instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 'USD_CAD', 'NZD_USD', 'XAU_USD']
        data_summary = {}
        
        for instrument in instruments:
            file_path = os.path.join(live_data_path, f'{instrument}_market_data_20250921_175106.csv')
            if os.path.exists(file_path):
                data = pd.read_csv(file_path)
                data['datetime'] = pd.to_datetime(data['datetime'])
                
                data_summary[instrument] = {
                    'total_points': len(data),
                    'start_time': data['datetime'].min().strftime('%Y-%m-%d %H:%M:%S'),
                    'end_time': data['datetime'].max().strftime('%Y-%m-%d %H:%M:%S'),
                    'duration_hours': (data['datetime'].max() - data['datetime'].min()).total_seconds() / 3600,
                    'avg_spread_pips': float(data['spread_pips'].mean()),
                    'price_range': {
                        'min': float(data['mid_price'].min()),
                        'max': float(data['mid_price'].max()),
                        'volatility': float(data['mid_price'].std())
                    }
                }
                
                print(f"📈 {instrument}: {len(data)} points, "
                      f"{data_summary[instrument]['duration_hours']:.1f}h, "
                      f"spread: {data_summary[instrument]['avg_spread_pips']:.2f} pips")
        
        # Determine optimal test periods
        print("\n🎯 DETERMINING TEST PERIODS")
        print("-" * 50)
        
        # Find common time range across all instruments
        all_start_times = [data_summary[inst]['start_time'] for inst in data_summary.keys()]
        all_end_times = [data_summary[inst]['end_time'] for inst in data_summary.keys()]
        
        common_start = max(all_start_times)
        common_end = min(all_end_times)
        
        print(f"📅 Common data range: {common_start} to {common_end}")
        
        # Create multiple test periods for comprehensive testing
        test_periods = [
            {
                'name': 'Full Period',
                'start': common_start,
                'end': common_end,
                'description': 'Complete available data range'
            },
            {
                'name': 'First Half',
                'start': common_start,
                'end': common_end,  # Will be adjusted to first half
                'description': 'First half of available data'
            },
            {
                'name': 'Second Half',
                'start': common_start,  # Will be adjusted to second half
                'end': common_end,
                'description': 'Second half of available data'
            }
        ]
        
        # Adjust periods for first and second half
        start_dt = pd.to_datetime(common_start)
        end_dt = pd.to_datetime(common_end)
        mid_dt = start_dt + (end_dt - start_dt) / 2
        
        test_periods[1]['end'] = mid_dt.strftime('%Y-%m-%d %H:%M:%S')
        test_periods[2]['start'] = mid_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Run comprehensive backtesting
        print("\n🚀 RUNNING COMPREHENSIVE BACKTESTING")
        print("-" * 50)
        
        strategies = ['alpha_strategy', 'gold_scalping', 'ultra_strict_forex']
        all_results = {}
        
        for period in test_periods:
            print(f"\n📊 Testing Period: {period['name']}")
            print(f"   📅 {period['start']} to {period['end']}")
            print(f"   📝 {period['description']}")
            
            period_results = {}
            
            for strategy in strategies:
                print(f"\n   🎯 Strategy: {strategy}")
                try:
                    result = system.run_enhanced_backtest(
                        strategy,
                        period['start'],
                        period['end']
                    )
                    
                    period_results[strategy] = result
                    
                    print(f"      ✅ Trades: {result['total_trades']}")
                    if result['performance']:
                        print(f"      📈 Return: {result['performance']['total_return']:.2%}")
                        print(f"      🎯 Win Rate: {result['performance']['win_rate']:.1%}")
                        print(f"      📊 Sharpe: {result['performance']['sharpe_ratio']:.2f}")
                    
                except Exception as e:
                    print(f"      ❌ Error: {e}")
                    period_results[strategy] = {'error': str(e)}
            
            all_results[period['name']] = period_results
        
        # Run strategy comparison analysis
        print("\n📊 STRATEGY COMPARISON ANALYSIS")
        print("-" * 50)
        
        comparison_results = {}
        
        for strategy in strategies:
            strategy_summary = {
                'total_trades_all_periods': 0,
                'total_return_all_periods': 0.0,
                'avg_win_rate': 0.0,
                'avg_sharpe_ratio': 0.0,
                'periods_tested': 0,
                'successful_periods': 0
            }
            
            for period_name, period_results in all_results.items():
                if strategy in period_results and 'error' not in period_results[strategy]:
                    result = period_results[strategy]
                    strategy_summary['periods_tested'] += 1
                    strategy_summary['successful_periods'] += 1
                    strategy_summary['total_trades_all_periods'] += result['total_trades']
                    
                    if result['performance']:
                        strategy_summary['total_return_all_periods'] += result['performance']['total_return']
                        strategy_summary['avg_win_rate'] += result['performance']['win_rate']
                        strategy_summary['avg_sharpe_ratio'] += result['performance']['sharpe_ratio']
                else:
                    strategy_summary['periods_tested'] += 1
            
            # Calculate averages
            if strategy_summary['successful_periods'] > 0:
                strategy_summary['avg_win_rate'] /= strategy_summary['successful_periods']
                strategy_summary['avg_sharpe_ratio'] /= strategy_summary['successful_periods']
            
            comparison_results[strategy] = strategy_summary
            
            print(f"📈 {strategy}:")
            print(f"   🎯 Total Trades: {strategy_summary['total_trades_all_periods']}")
            print(f"   📊 Successful Periods: {strategy_summary['successful_periods']}/{strategy_summary['periods_tested']}")
            print(f"   📈 Avg Win Rate: {strategy_summary['avg_win_rate']:.1%}")
            print(f"   📊 Avg Sharpe: {strategy_summary['avg_sharpe_ratio']:.2f}")
        
        # Generate comprehensive report
        print("\n📋 GENERATING COMPREHENSIVE REPORT")
        print("-" * 50)
        
        comprehensive_report = {
            'execution_timestamp': datetime.now().isoformat(),
            'data_summary': data_summary,
            'test_periods': test_periods,
            'backtest_results': all_results,
            'strategy_comparison': comparison_results,
            'system_info': {
                'live_data_path': live_data_path,
                'bloomberg_data_path': bloomberg_data_path,
                'total_instruments': len(data_summary),
                'total_data_points': sum(ds['total_points'] for ds in data_summary.values())
            }
        }
        
        # Save comprehensive report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"comprehensive_backtesting_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(comprehensive_report, f, indent=2, default=str)
        
        print(f"💾 Comprehensive report saved to: {report_file}")
        
        # Print final summary
        print("\n🎉 COMPREHENSIVE BACKTESTING COMPLETED")
        print("=" * 60)
        
        total_trades = sum(cr['total_trades_all_periods'] for cr in comparison_results.values())
        total_periods = len(test_periods)
        total_strategies = len(strategies)
        
        print(f"📊 Total Strategies Tested: {total_strategies}")
        print(f"📅 Total Test Periods: {total_periods}")
        print(f"🎯 Total Trades Generated: {total_trades}")
        print(f"📈 Total Instruments: {len(data_summary)}")
        print(f"📊 Total Data Points: {sum(ds['total_points'] for ds in data_summary.values())}")
        
        # Best performing strategy
        if comparison_results:
            best_strategy = max(comparison_results.items(), 
                              key=lambda x: x[1]['total_trades_all_periods'])
            print(f"🏆 Most Active Strategy: {best_strategy[0]} ({best_strategy[1]['total_trades_all_periods']} trades)")
        
        print(f"\n⏰ End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        # Save error report
        error_report = {
            'error_timestamp': datetime.now().isoformat(),
            'error_message': str(e),
            'traceback': traceback.format_exc()
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        error_file = f"backtesting_error_report_{timestamp}.json"
        
        with open(error_file, 'w') as f:
            json.dump(error_report, f, indent=2)
        
        print(f"💾 Error report saved to: {error_file}")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)













