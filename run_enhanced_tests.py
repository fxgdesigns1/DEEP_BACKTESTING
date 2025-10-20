#!/usr/bin/env python3
"""
RUN ENHANCED TESTS
Execute enhanced backtesting system with comprehensive validation
"""

import os
import sys
import json
from datetime import datetime
import traceback

def main():
    """Main execution function"""
    
    print("🚀 ENHANCED BACKTESTING SYSTEM - TEST EXECUTION")
    print("=" * 60)
    print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # Step 1: Run Enhanced Backtesting System
        print("\n📊 STEP 1: RUNNING ENHANCED BACKTESTING SYSTEM")
        print("-" * 50)
        
        from enhanced_backtesting_system import EnhancedBacktestingSystem
        
        # Initialize system
        live_data_path = r"H:\My Drive\desktop_backtesting_export"
        bloomberg_data_path = r"E:\deep_backtesting_windows1\deep_backtesting\data"
        
        system = EnhancedBacktestingSystem(live_data_path, bloomberg_data_path)
        
        # Run backtests
        strategies = ['alpha_strategy', 'gold_scalping', 'ultra_strict_forex']
        test_start_date = "2025-09-18 00:00:00"
        test_end_date = "2025-09-18 23:59:59"
        
        backtest_results = {}
        
        for strategy in strategies:
            print(f"\n🎯 Testing Strategy: {strategy}")
            try:
                result = system.run_enhanced_backtest(
                    strategy, 
                    test_start_date, 
                    test_end_date
                )
                
                backtest_results[strategy] = result
                
                print(f"✅ {strategy} Results:")
                print(f"   📊 Total trades: {result['total_trades']}")
                if result['performance']:
                    print(f"   🎯 Win rate: {result['performance']['win_rate']:.2%}")
                    print(f"   📈 Total return: {result['performance']['total_return']:.2%}")
                    print(f"   📊 Sharpe ratio: {result['performance']['sharpe_ratio']:.2f}")
                    print(f"   💰 Avg cost per trade: ${result['performance']['avg_cost_per_trade']:.4f}")
                
            except Exception as e:
                print(f"❌ Error testing {strategy}: {e}")
                backtest_results[strategy] = {'error': str(e)}
        
        # Step 2: Run Comprehensive Validation
        print("\n🔍 STEP 2: RUNNING COMPREHENSIVE VALIDATION")
        print("-" * 50)
        
        from comprehensive_validation_system import ComprehensiveValidationSystem
        
        validator = ComprehensiveValidationSystem(
            r"E:\deep_backtesting_windows1\deep_backtesting",
            live_data_path
        )
        
        validation_results = validator.run_triple_check_validation()
        
        # Step 3: Generate Final Report
        print("\n📋 STEP 3: GENERATING FINAL REPORT")
        print("-" * 50)
        
        final_report = {
            'execution_timestamp': datetime.now().isoformat(),
            'system_info': {
                'enhanced_system_path': r"E:\deep_backtesting_windows1\deep_backtesting",
                'live_data_path': live_data_path,
                'bloomberg_data_path': bloomberg_data_path,
                'test_period': f"{test_start_date} to {test_end_date}"
            },
            'backtest_results': backtest_results,
            'validation_results': validation_results,
            'summary': {
                'total_strategies_tested': len(strategies),
                'successful_backtests': sum(1 for r in backtest_results.values() if 'error' not in r),
                'failed_backtests': sum(1 for r in backtest_results.values() if 'error' in r),
                'overall_validation_status': validation_results['overall_status']['status'],
                'validation_success_rate': validation_results['overall_status']['success_rate']
            }
        }
        
        # Save final report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"enhanced_system_final_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2, default=str)
        
        print(f"💾 Final report saved to: {report_file}")
        
        # Print final summary
        print("\n🎉 FINAL SUMMARY")
        print("=" * 60)
        print(f"📊 Strategies Tested: {final_report['summary']['total_strategies_tested']}")
        print(f"✅ Successful Backtests: {final_report['summary']['successful_backtests']}")
        print(f"❌ Failed Backtests: {final_report['summary']['failed_backtests']}")
        print(f"🔍 Validation Status: {final_report['summary']['overall_validation_status']}")
        print(f"📈 Validation Success Rate: {final_report['summary']['validation_success_rate']:.1%}")
        
        # Print individual strategy results
        print("\n📊 STRATEGY RESULTS:")
        for strategy, result in backtest_results.items():
            if 'error' not in result:
                print(f"   ✅ {strategy}: {result['total_trades']} trades")
                if result['performance']:
                    print(f"      Win Rate: {result['performance']['win_rate']:.1%}")
                    print(f"      Total Return: {result['performance']['total_return']:.2%}")
            else:
                print(f"   ❌ {strategy}: {result['error']}")
        
        print(f"\n⏰ End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        print("\n🔍 Full Traceback:")
        traceback.print_exc()
        
        # Save error report
        error_report = {
            'error_timestamp': datetime.now().isoformat(),
            'error_message': str(e),
            'traceback': traceback.format_exc()
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        error_file = f"enhanced_system_error_report_{timestamp}.json"
        
        with open(error_file, 'w') as f:
            json.dump(error_report, f, indent=2)
        
        print(f"💾 Error report saved to: {error_file}")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

