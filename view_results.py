#!/usr/bin/env python3
"""
Results Viewer for Multi-Timeframe Strategy Search
View best findings and detailed results anytime
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
import pandas as pd

def get_all_results():
    """Get all results from results directory"""
    all_results = []
    results_dir = Path("results")
    
    if not results_dir.exists():
        return all_results
        
    # Look for today's results
    today = datetime.now().strftime("%Y-%m-%d")
    today_dir = results_dir / today
    
    if not today_dir.exists():
        return all_results
        
    # Find all summary.json files
    for summary_file in today_dir.rglob("summary.json"):
        try:
            with open(summary_file, 'r') as f:
                data = json.load(f)
                
            if 'metrics' in data:
                metrics = data['metrics']
                sharpe = metrics.get('oos_sharpe', 0)
                
                # Include all results, even negative Sharpe for analysis
                all_results.append({
                    'pair': data.get('pair', 'unknown'),
                    'timeframe': data.get('timeframe', 'unknown'),
                    'strategy': data.get('strategy', 'unknown'),
                    'sharpe': sharpe,
                    'sortino': metrics.get('oos_sortino', 0),
                    'max_dd': metrics.get('oos_max_dd', 0),
                    'profit_factor': metrics.get('profit_factor', 0),
                    'trades': metrics.get('total_trades', 0),
                    'win_rate': metrics.get('win_rate', 0),
                    'config_hash': data.get('config_hash', 'unknown'),
                    'trade_signature': data.get('trade_signature', 'unknown'),
                    'file_path': str(summary_file)
                })
        except Exception as e:
            print(f"Error reading {summary_file}: {e}")
            continue
            
    return all_results

def get_best_findings(limit=10):
    """Get best findings sorted by Sharpe ratio"""
    all_results = get_all_results()
    
    # Sort by Sharpe ratio
    all_results.sort(key=lambda x: x['sharpe'], reverse=True)
    
    return all_results[:limit]

def get_results_by_timeframe():
    """Get results grouped by timeframe"""
    all_results = get_all_results()
    
    by_timeframe = {}
    for result in all_results:
        tf = result['timeframe']
        if tf not in by_timeframe:
            by_timeframe[tf] = []
        by_timeframe[tf].append(result)
    
    # Sort each timeframe by Sharpe
    for tf in by_timeframe:
        by_timeframe[tf].sort(key=lambda x: x['sharpe'], reverse=True)
    
    return by_timeframe

def get_results_by_pair():
    """Get results grouped by pair"""
    all_results = get_all_results()
    
    by_pair = {}
    for result in all_results:
        pair = result['pair']
        if pair not in by_pair:
            by_pair[pair] = []
        by_pair[pair].append(result)
    
    # Sort each pair by Sharpe
    for pair in by_pair:
        by_pair[pair].sort(key=lambda x: x['sharpe'], reverse=True)
    
    return by_pair

def print_summary_table(results):
    """Print results in a nice table format"""
    if not results:
        print("No results found")
        return
    
    print(f"{'Rank':<4} {'Pair':<8} {'TF':<4} {'Strategy':<20} {'Sharpe':<8} {'Sortino':<8} {'Max DD':<8} {'PF':<6} {'Trades':<7} {'Sig':<12}")
    print("-" * 100)
    
    for i, result in enumerate(results, 1):
        print(f"{i:<4} {result['pair']:<8} {result['timeframe']:<4} {result['strategy'][:20]:<20} "
              f"{result['sharpe']:<8.3f} {result['sortino']:<8.3f} {result['max_dd']:<8.1%} "
              f"{result['profit_factor']:<6.2f} {result['trades']:<7} {result['trade_signature']:<12}")

def view_detailed_result(file_path):
    """View detailed result from a specific file"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        print(f"\n📊 DETAILED RESULT: {file_path}")
        print("=" * 60)
        
        print(f"Pair: {data.get('pair', 'unknown')}")
        print(f"Timeframe: {data.get('timeframe', 'unknown')}")
        print(f"Strategy: {data.get('strategy', 'unknown')}")
        print(f"Config Hash: {data.get('config_hash', 'unknown')}")
        print(f"Trade Signature: {data.get('trade_signature', 'unknown')}")
        
        if 'hyperparams' in data:
            print(f"\nParameters:")
            for key, value in data['hyperparams'].items():
                print(f"  {key}: {value}")
        
        if 'metrics' in data:
            metrics = data['metrics']
            print(f"\nMetrics:")
            print(f"  Sharpe Ratio: {metrics.get('oos_sharpe', 0):.3f}")
            print(f"  Sortino Ratio: {metrics.get('oos_sortino', 0):.3f}")
            print(f"  Max Drawdown: {metrics.get('oos_max_dd', 0):.1%}")
            print(f"  Profit Factor: {metrics.get('profit_factor', 0):.2f}")
            print(f"  Win Rate: {metrics.get('win_rate', 0):.1%}")
            print(f"  Total Trades: {metrics.get('total_trades', 0)}")
            
    except Exception as e:
        print(f"Error reading detailed result: {e}")

def main():
    print("📊 MULTI-TIMEFRAME STRATEGY SEARCH - RESULTS VIEWER")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get all results
    all_results = get_all_results()
    print(f"Total experiments completed: {len(all_results)}")
    
    if not all_results:
        print("No results found. The search may still be running or no successful strategies found yet.")
        return
    
    # Show best findings
    best_findings = get_best_findings(10)
    print(f"\n🏆 TOP 10 RESULTS (by Sharpe Ratio):")
    print_summary_table(best_findings)
    
    # Show results by timeframe
    by_timeframe = get_results_by_timeframe()
    print(f"\n📈 BEST RESULTS BY TIMEFRAME:")
    for tf in sorted(by_timeframe.keys()):
        tf_results = by_timeframe[tf][:3]  # Top 3 per timeframe
        print(f"\n{tf} timeframe:")
        print_summary_table(tf_results)
    
    # Show results by pair
    by_pair = get_results_by_pair()
    print(f"\n💱 BEST RESULTS BY PAIR:")
    for pair in sorted(by_pair.keys()):
        pair_results = by_pair[pair][:3]  # Top 3 per pair
        print(f"\n{pair}:")
        print_summary_table(pair_results)
    
    # Show successful strategies only
    successful = [r for r in all_results if r['sharpe'] > 0]
    if successful:
        print(f"\n✅ SUCCESSFUL STRATEGIES (Sharpe > 0): {len(successful)}")
        print_summary_table(successful)
    else:
        print(f"\n❌ No successful strategies found yet (Sharpe > 0)")
    
    # Show strategies meeting institutional criteria
    institutional = [r for r in all_results if r['sharpe'] >= 1.2 and r['max_dd'] <= 0.12]
    if institutional:
        print(f"\n🏛️ INSTITUTIONAL-GRADE STRATEGIES (Sharpe ≥ 1.2, DD ≤ 12%): {len(institutional)}")
        print_summary_table(institutional)
    else:
        print(f"\n🏛️ No institutional-grade strategies found yet")
    
    print(f"\n💡 To view detailed results, run:")
    print(f"   python3 view_results.py --detail <file_path>")
    print(f"💡 To view specific timeframe, run:")
    print(f"   python3 view_results.py --timeframe <15m|4h|1d>")
    print(f"💡 To view specific pair, run:")
    print(f"   python3 view_results.py --pair <EUR_USD|GBP_USD|etc>")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--detail" and len(sys.argv) > 2:
            view_detailed_result(sys.argv[2])
        elif sys.argv[1] == "--timeframe" and len(sys.argv) > 2:
            tf = sys.argv[2]
            by_timeframe = get_results_by_timeframe()
            if tf in by_timeframe:
                print(f"📈 RESULTS FOR {tf} TIMEFRAME:")
                print_summary_table(by_timeframe[tf])
            else:
                print(f"No results found for {tf} timeframe")
        elif sys.argv[1] == "--pair" and len(sys.argv) > 2:
            pair = sys.argv[2]
            by_pair = get_results_by_pair()
            if pair in by_pair:
                print(f"💱 RESULTS FOR {pair}:")
                print_summary_table(by_pair[pair])
            else:
                print(f"No results found for {pair}")
        else:
            print("Usage:")
            print("  python3 view_results.py                    # View all results")
            print("  python3 view_results.py --detail <file>    # View detailed result")
            print("  python3 view_results.py --timeframe <tf>   # View by timeframe")
            print("  python3 view_results.py --pair <pair>      # View by pair")
    else:
        main()
