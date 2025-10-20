#!/usr/bin/env python3
"""Filter strategies by user criteria: Win Rate ≥ 65%, Drawdown ≤ 10%"""

import json
from pathlib import Path

print("\n" + "=" * 80)
print("FILTERING STRATEGIES: Win Rate >= 65%, Max Drawdown <= 10%")
print("=" * 80)

# Find latest optimization results
results_files = list(Path(".").glob("optimization_results_*.json"))

if not results_files:
    print("\n[INFO] No results file found yet. Optimization still running...")
    print("[INFO] Results will be generated when optimization updates")
    exit(0)

latest = max(results_files, key=lambda p: p.stat().st_mtime)

with open(latest, 'r') as f:
    data = json.load(f)

print(f"\nAnalyzing results from: {latest.name}")
print(f"Total Scenarios Tested: {data.get('total_tested', 0):,}")
print()

# Filter strategies
filtered_excellent = []
filtered_good = []

for strategy in data.get('excellent', []):
    if strategy['win_rate'] >= 65.0 and strategy['max_dd'] <= 10.0:
        filtered_excellent.append(strategy)

for strategy in data.get('good', []):
    if strategy['win_rate'] >= 65.0 and strategy['max_dd'] <= 10.0:
        filtered_good.append(strategy)

print(f"STRATEGIES MEETING YOUR CRITERIA:")
print(f"  EXCELLENT tier (Win >=65%, DD <=10%): {len(filtered_excellent)}")
print(f"  GOOD tier (Win >=65%, DD <=10%): {len(filtered_good)}")
print()

# Sort by Sharpe ratio
all_filtered = filtered_excellent + filtered_good
all_filtered.sort(key=lambda x: x['sharpe'], reverse=True)

if all_filtered:
    print("=" * 80)
    print("TOP 10 STRATEGIES MEETING YOUR CRITERIA")
    print("=" * 80)
    
    for i, strategy in enumerate(all_filtered[:10], 1):
        scenario = strategy['scenario']
        
        print(f"\n#{i} - Scenario #{scenario['id']}")
        print(f"Pair: {scenario['pair'].upper()} | Timeframe: {scenario['timeframe']}")
        print(f"EMA: {scenario['ema_fast']}/{scenario['ema_slow']} | R:R: {scenario['rr_ratio']}")
        print(f"SL: {scenario['sl_atr_mult']}x ATR | RSI: {scenario['rsi_oversold']}/{scenario['rsi_overbought']}")
        print()
        print(f"  Win Rate: {strategy['win_rate']:.1f}%")
        print(f"  Max Drawdown: {strategy['max_dd']:.1f}%")
        print(f"  Sharpe Ratio: {strategy['sharpe']:.2f}")
        print(f"  Annual Return: {strategy['annual_return']:.1f}%")
        print(f"  Profit Factor: {strategy['profit_factor']:.2f}")
        print(f"  Total Trades: {strategy['total_trades']}")
        print("-" * 80)
    
    # Export filtered results
    export_file = f"filtered_strategies_{latest.stem.split('_')[-1]}.json"
    with open(export_file, 'w') as f:
        json.dump({
            'criteria': {
                'min_win_rate': 65.0,
                'max_drawdown': 10.0
            },
            'total_matching': len(all_filtered),
            'strategies': all_filtered[:10]
        }, f, indent=2, default=str)
    
    print(f"\n[SAVED] Filtered results: {export_file}")
    
    # Show THE BEST
    best = all_filtered[0]
    print("\n" + "=" * 80)
    print(">>> YOUR BEST STRATEGY <<<")
    print("=" * 80)
    s = best['scenario']
    print(f"Pair: {s['pair'].upper()}")
    print(f"Timeframe: {s['timeframe']}")
    print(f"EMA Fast: {s['ema_fast']}")
    print(f"EMA Slow: {s['ema_slow']}")
    print(f"Risk:Reward: 1:{s['rr_ratio']}")
    print(f"Stop Loss: {s['sl_atr_mult']}x ATR")
    print(f"RSI Oversold: {s['rsi_oversold']}")
    print(f"RSI Overbought: {s['rsi_overbought']}")
    print()
    print(f"PERFORMANCE:")
    print(f"  Win Rate: {best['win_rate']:.1f}% [Target: >=65%]")
    print(f"  Max Drawdown: {best['max_dd']:.1f}% [Target: <=10%]")
    print(f"  Sharpe Ratio: {best['sharpe']:.2f}")
    print(f"  Annual Return: {best['annual_return']:.1f}%")
    print(f"  Profit Factor: {best['profit_factor']:.2f}")
    print(f"  Total Trades: {best['total_trades']:,}")
    print(f"  Avg Win: {best.get('avg_win', 0):.2f}%")
    print(f"  Avg Loss: {best.get('avg_loss', 0):.2f}%")
    print("=" * 80)

else:
    print("[INFO] No strategies meet your specific criteria yet")
    print("[INFO] Optimization is still running - more strategies coming!")

print()

