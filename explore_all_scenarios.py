"""
Check ALL scenarios to find higher profit strategies with more drawdown tolerance
"""

import json
from pathlib import Path
from collections import defaultdict

# Load the checkpoint files (they have all data)
results_dir = Path("H:/My Drive/AI Trading/exported strategies/ultimate_search_20251004_091405")

# Try to load the largest checkpoint
checkpoint_files = list(results_dir.glob("checkpoint_*.json"))
if checkpoint_files:
    latest_checkpoint = max(checkpoint_files, key=lambda x: int(x.stem.split('_')[1]))
    print(f"\nLoading: {latest_checkpoint.name}")
    
    with open(latest_checkpoint) as f:
        all_scenarios = json.load(f)
    
    print(f"Total scenarios in checkpoint: {len(all_scenarios)}")
    
    # Filter for good quality but higher DD tolerance
    print("\n" + "="*100)
    print("EXPLORING DIFFERENT DRAWDOWN LEVELS")
    print("="*100)
    
    dd_levels = [
        (0, 2.0, "0-2% (Ultra Conservative)"),
        (0, 3.5, "0-3.5% (Your Previous Filter)"),
        (0, 4.0, "0-4% (Your Request)"),
        (0, 5.0, "0-5% (Moderate Risk)"),
        (0, 6.0, "0-6% (Higher Risk)"),
        (0, 8.0, "0-8% (Aggressive)"),
    ]
    
    for min_dd, max_dd, label in dd_levels:
        filtered = [
            s for s in all_scenarios
            if 'max_dd' in s and 'win_rate' in s and 'sharpe' in s and 'annual_return' in s
            and min_dd <= s['max_dd'] <= max_dd
            and s['win_rate'] >= 65  # Minimum 65% win rate
            and s['sharpe'] >= 2.0   # Minimum Sharpe of 2
        ]
        
        if len(filtered) > 0:
            # Get top by return
            top_by_return = sorted(filtered, key=lambda x: x['annual_return'], reverse=True)[:3]
            avg_return = sum(s['annual_return'] for s in filtered) / len(filtered)
            max_return = max(s['annual_return'] for s in filtered)
            
            print(f"\n{label}:")
            print(f"   Count: {len(filtered)} strategies")
            print(f"   Avg Return: {avg_return:.1f}%")
            print(f"   Max Return: {max_return:.1f}%")
            
            print(f"\n   Top 3 by Return:")
            for i, s in enumerate(top_by_return, 1):
                scenario = s['scenario']
                print(f"   #{i}: {scenario['pair'].upper()} {scenario['timeframe']} | "
                      f"Return: {s['annual_return']:.1f}% | DD: {s['max_dd']:.2f}% | "
                      f"Sharpe: {s['sharpe']:.2f} | Win: {s['win_rate']:.1f}%")
    
    # Now find THE BEST strategy by pure return (regardless of DD up to 10%)
    print("\n" + "="*100)
    print("TOP 20 HIGHEST RETURN STRATEGIES (Win Rate >= 65%, Sharpe >= 2.0)")
    print("="*100)
    
    quality_strategies = [
        s for s in all_scenarios
        if 'max_dd' in s and 'win_rate' in s and 'sharpe' in s and 'annual_return' in s
        and s['win_rate'] >= 65
        and s['sharpe'] >= 2.0
        and s['max_dd'] <= 10.0  # Cap at 10% DD
    ]
    
    top_20_return = sorted(quality_strategies, key=lambda x: x['annual_return'], reverse=True)[:20]
    
    for i, s in enumerate(top_20_return, 1):
        scenario = s['scenario']
        print(f"\n#{i}: {scenario['pair'].upper()} on {scenario['timeframe']}")
        print(f"   Annual Return: {s['annual_return']:.1f}%")
        print(f"   Max Drawdown: {s['max_dd']:.2f}%")
        print(f"   Sharpe Ratio: {s['sharpe']:.2f}")
        print(f"   Win Rate: {s['win_rate']:.1f}%")
        print(f"   Profit Factor: {s['profit_factor']:.2f}")
        print(f"   Total Trades: {s['trades']}")
        print(f"   EMA: {scenario['ema_fast']}/{scenario['ema_slow']} | "
              f"R:R: 1:{scenario['rr_ratio']} | SL: {scenario['sl_atr_mult']}x ATR")
    
    # Analyze by pair
    print("\n" + "="*100)
    print("BEST STRATEGY PER PAIR (Max 6% DD)")
    print("="*100)
    
    by_pair = defaultdict(list)
    for s in quality_strategies:
        if s['max_dd'] <= 6.0:
            pair = s['scenario']['pair'].upper()
            by_pair[pair].append(s)
    
    for pair in sorted(by_pair.keys()):
        best = max(by_pair[pair], key=lambda x: x['annual_return'])
        scenario = best['scenario']
        print(f"\n{pair}:")
        print(f"   Return: {best['annual_return']:.1f}% | DD: {best['max_dd']:.2f}% | "
              f"Sharpe: {best['sharpe']:.2f} | Win: {best['win_rate']:.1f}%")
        print(f"   EMA: {scenario['ema_fast']}/{scenario['ema_slow']} | "
              f"Timeframe: {scenario['timeframe']} | Trades: {best['trades']}")

else:
    print("No checkpoint files found!")

print("\n" + "="*100)





