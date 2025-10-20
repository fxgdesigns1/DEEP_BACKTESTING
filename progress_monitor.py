#!/usr/bin/env python3
"""
Progress Monitor for Parallel Strategy Search
Shows best strategies found so far
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path

def find_latest_results():
    """Find the latest results file"""
    results_dir = Path("results")
    if not results_dir.exists():
        return None
    
    # Look for optimized_parallel_results files
    result_files = list(results_dir.glob("**/optimized_parallel_results_*.json"))
    if not result_files:
        return None
    
    # Get the most recent file
    latest_file = max(result_files, key=os.path.getmtime)
    return latest_file

def monitor_progress():
    """Monitor progress and show best strategies"""
    print("🔍 PARALLEL STRATEGY SEARCH - PROGRESS MONITOR")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check for results
    results_file = find_latest_results()
    if results_file:
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)
            
            print(f"📊 Results File: {results_file}")
            print(f"⏱️  Execution Time: {results.get('execution_time', 'Unknown')}")
            print(f"📈 Total Experiments: {results.get('total_experiments', 0)}")
            print(f"✅ Successful Strategies: {results.get('successful_strategies', 0)}")
            print(f"📊 Success Rate: {results.get('success_rate', 0):.2f}%")
            print()
            
            # Show top strategies
            strategies = results.get('strategies', [])
            if strategies:
                print("🏆 TOP STRATEGIES FOUND:")
                print("-" * 70)
                
                # Sort by Sharpe ratio
                sorted_strategies = sorted(strategies, 
                                         key=lambda x: x['results']['sharpe_ratio'], 
                                         reverse=True)
                
                for i, strategy in enumerate(sorted_strategies[:10], 1):
                    exp = strategy['experiment']
                    res = strategy['results']
                    
                    print(f"{i:2d}. {exp['pair']} {exp['timeframe']} {exp['strategy']}")
                    print(f"    Sharpe: {res['sharpe_ratio']:.3f} | Sortino: {res['sortino_ratio']:.3f}")
                    print(f"    Win Rate: {res['win_rate']:.1f}% | Profit Factor: {res['profit_factor']:.2f}")
                    print(f"    Trades: {res['total_trades']} | Max DD: {res['max_drawdown']:.1f}")
                    print()
            else:
                print("🔍 No successful strategies found yet...")
                print("💡 The search is still running - strategies will appear as they are found")
        except Exception as e:
            print(f"❌ Error reading results: {e}")
    else:
        print("🔍 No results file found yet...")
        print("💡 The parallel search is starting up - results will appear shortly")
    
    print()
    print("💡 This monitor updates in real-time as strategies are found")
    print("💡 Press Ctrl+C to stop monitoring")

def main():
    """Main monitoring loop"""
    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
            monitor_progress()
            time.sleep(10)  # Update every 10 seconds
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")

if __name__ == "__main__":
    main()

