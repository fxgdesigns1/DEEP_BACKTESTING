"""
Analyze all 114 strategies to understand pair distribution and DD vs profit relationship
"""

import json
from pathlib import Path
from collections import defaultdict

# Load the filtered results
results_file = Path("H:/My Drive/AI Trading/exported strategies/ultimate_search_20251004_091405/filtered_3.5pct_DD.json")

with open(results_file) as f:
    data = json.load(f)

all_strategies = data['top_5_sharpe']  # This actually contains ALL matching strategies

print("\n" + "="*100)
print(" "*30 + "FULL ANALYSIS - ALL 114 STRATEGIES")
print("="*100)

# Analyze by pair
by_pair = defaultdict(list)
for s in all_strategies:
    pair = s['scenario']['pair'].upper()
    by_pair[pair].append(s)

print(f"\nSTRATEGIES BY PAIR:")
print("="*100)
for pair, strategies in sorted(by_pair.items(), key=lambda x: len(x[1]), reverse=True):
    best_sharpe = max(s['sharpe'] for s in strategies)
    best_return = max(s['annual_return'] for s in strategies)
    avg_dd = sum(s['max_dd'] for s in strategies) / len(strategies)
    
    print(f"\n{pair}: {len(strategies)} strategies")
    print(f"   Best Sharpe: {best_sharpe:.2f}")
    print(f"   Best Return: {best_return:.1f}%")
    print(f"   Avg DD: {avg_dd:.2f}%")

# Analyze DD vs Return relationship
print("\n" + "="*100)
print("DRAWDOWN vs RETURN ANALYSIS")
print("="*100)

dd_buckets = {
    '0-0.5%': [],
    '0.5-1.0%': [],
    '1.0-1.5%': [],
    '1.5-2.0%': [],
    '2.0-2.5%': [],
    '2.5-3.0%': [],
    '3.0-3.5%': []
}

for s in all_strategies:
    dd = s['max_dd']
    if dd <= 0.5:
        dd_buckets['0-0.5%'].append(s)
    elif dd <= 1.0:
        dd_buckets['0.5-1.0%'].append(s)
    elif dd <= 1.5:
        dd_buckets['1.0-1.5%'].append(s)
    elif dd <= 2.0:
        dd_buckets['1.5-2.0%'].append(s)
    elif dd <= 2.5:
        dd_buckets['2.0-2.5%'].append(s)
    elif dd <= 3.0:
        dd_buckets['2.5-3.0%'].append(s)
    else:
        dd_buckets['3.0-3.5%'].append(s)

print(f"\nDD Range       | Count | Avg Return | Avg Sharpe | Best Return")
print("-" * 100)
for dd_range, strategies in dd_buckets.items():
    if len(strategies) > 0:
        avg_return = sum(s['annual_return'] for s in strategies) / len(strategies)
        avg_sharpe = sum(s['sharpe'] for s in strategies) / len(strategies)
        best_return = max(s['annual_return'] for s in strategies)
        print(f"{dd_range:15} | {len(strategies):5} | {avg_return:10.1f}% | {avg_sharpe:10.2f} | {best_return:11.1f}%")

# Find highest return strategies
print("\n" + "="*100)
print("TOP 10 BY ANNUAL RETURN (not Sharpe)")
print("="*100)

sorted_by_return = sorted(all_strategies, key=lambda x: x['annual_return'], reverse=True)[:10]

for i, s in enumerate(sorted_by_return, 1):
    scenario = s['scenario']
    print(f"\n#{i}: {scenario['pair'].upper()} on {scenario['timeframe']}")
    print(f"   Return: {s['annual_return']:.1f}% | Sharpe: {s['sharpe']:.2f} | Win Rate: {s['win_rate']:.1f}%")
    print(f"   Max DD: {s['max_dd']:.2f}% | Trades: {s['trades']} | PF: {s['profit_factor']:.2f}")

# Check if higher DD could give more profit
print("\n" + "="*100)
print("WHAT IF WE ALLOWED 5% OR 6% DRAWDOWN?")
print("="*100)

# Load all results (not just filtered)
all_results_file = Path("H:/My Drive/AI Trading/exported strategies/ultimate_search_20251004_091405/ultimate_search_results.json")
if all_results_file.exists():
    with open(all_results_file) as f:
        all_data = json.load(f)
    
    # Find strategies with 3.5-6% DD
    higher_dd = []
    for s in all_data:
        if 'max_dd' in s and 'win_rate' in s and 'sharpe' in s:
            dd = s['max_dd']
            win_rate = s['win_rate']
            sharpe = s['sharpe']
            
            # Same quality criteria but higher DD
            if 3.5 < dd <= 6.0 and win_rate >= 65 and sharpe >= 2.0:
                higher_dd.append(s)
    
    if len(higher_dd) > 0:
        print(f"\nFound {len(higher_dd)} additional strategies with 3.5-6% DD")
        
        # Show top 5 by return
        sorted_higher = sorted(higher_dd, key=lambda x: x['annual_return'], reverse=True)[:5]
        print("\nTOP 5 WITH HIGHER DD:")
        for i, s in enumerate(sorted_higher, 1):
            scenario = s['scenario']
            print(f"\n#{i}: {scenario['pair'].upper()} on {scenario['timeframe']}")
            print(f"   Return: {s['annual_return']:.1f}% | Sharpe: {s['sharpe']:.2f}")
            print(f"   Max DD: {s['max_dd']:.2f}% | Win Rate: {s['win_rate']:.1f}%")
    else:
        print("\nNo additional strategies found with 3.5-6% DD meeting quality criteria")
        print("This suggests the 3.5% limit is already optimal!")
else:
    print("\nNeed to check full results file...")

print("\n" + "="*100)





