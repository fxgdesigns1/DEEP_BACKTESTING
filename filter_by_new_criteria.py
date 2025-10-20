#!/usr/bin/env python3
"""Filter strategies with NEW criteria: Win >= 65%, Max DD <= 3.5%"""

import json
from pathlib import Path

# Find latest checkpoint
checkpoints = list(Path(r"H:\My Drive\AI Trading\exported strategies").rglob("checkpoint_*.json"))
latest = max(checkpoints, key=lambda p: p.stat().st_mtime) if checkpoints else None

if not latest:
    print("[INFO] No checkpoint found yet")
    exit(0)

print(f"\n{'='*100}")
print(" "*30 + "FILTERING WITH NEW CRITERIA")
print("="*100)
print(f"\nUsing checkpoint: {latest.name}")
print(f"NEW CRITERIA: Win Rate >= 65%, Max Drawdown <= 3.5% (relaxed from 10%)")
print("="*100)

with open(latest, 'r') as f:
    data = json.load(f)

print(f"\nScenarios tested so far: {data['tested']:,}")

# Filter with new criteria
filtered = []
for s in data['successful']:
    if s['win_rate'] >= 65.0 and s['max_dd'] <= 3.5 and s['sharpe'] >= 2.0:
        filtered.append(s)

print(f"Strategies meeting NEW criteria: {len(filtered)}")

if not filtered:
    print("\n[INFO] No strategies meet criteria yet - search continuing...")
    exit(0)

# Sort by different metrics
by_sharpe = sorted(filtered, key=lambda x: x['sharpe'], reverse=True)
by_return = sorted(filtered, key=lambda x: x['annual_return'], reverse=True)
by_winrate = sorted(filtered, key=lambda x: x['win_rate'], reverse=True)

print(f"\n{'='*100}")
print("TOP 5 BY SHARPE RATIO (Best Risk-Adjusted Returns)")
print("="*100)
print(f"{'Rank':<6} {'Pair':<10} {'TF':<6} {'Sharpe':<8} {'Return':<10} {'Win%':<8} {'DD%':<8} {'PF':<8} {'Trades':<8}")
print("-"*100)

for i, s in enumerate(by_sharpe[:5], 1):
    sc = s['scenario']
    print(f"{i:<6} {sc['pair'].upper():<10} {sc['timeframe']:<6} {s['sharpe']:<8.2f} "
          f"{s['annual_return']:<9.1f}% {s['win_rate']:<7.1f}% {s['max_dd']:<7.1f}% "
          f"{s['profit_factor']:<7.2f} {s['trades']:<8,}")

print(f"\n{'='*100}")
print("TOP 5 BY ANNUAL RETURN (Highest Profits)")
print("="*100)
print(f"{'Rank':<6} {'Pair':<10} {'TF':<6} {'Return':<10} {'Sharpe':<8} {'Win%':<8} {'DD%':<8} {'PF':<8} {'Trades':<8}")
print("-"*100)

for i, s in enumerate(by_return[:5], 1):
    sc = s['scenario']
    print(f"{i:<6} {sc['pair'].upper():<10} {sc['timeframe']:<6} {s['annual_return']:<9.1f}% "
          f"{s['sharpe']:<8.2f} {s['win_rate']:<7.1f}% {s['max_dd']:<7.1f}% "
          f"{s['profit_factor']:<7.2f} {s['trades']:<8,}")

print(f"\n{'='*100}")
print("TOP 5 BY WIN RATE (Most Consistent)")
print("="*100)
print(f"{'Rank':<6} {'Pair':<10} {'TF':<6} {'Win%':<8} {'Return':<10} {'Sharpe':<8} {'DD%':<8} {'PF':<8} {'Trades':<8}")
print("-"*100)

for i, s in enumerate(by_winrate[:5], 1):
    sc = s['scenario']
    print(f"{i:<6} {sc['pair'].upper():<10} {sc['timeframe']:<6} {s['win_rate']:<7.1f}% "
          f"{s['annual_return']:<9.1f}% {s['sharpe']:<8.2f} {s['max_dd']:<7.1f}% "
          f"{s['profit_factor']:<7.2f} {s['trades']:<8,}")

print(f"\n{'='*100}")
print(">>> THE ULTIMATE BEST STRATEGY (By Sharpe) <<<")
print("="*100)

best = by_sharpe[0]
sc = best['scenario']

print(f"\nPair: {sc['pair'].upper()}")
print(f"Timeframe: {sc['timeframe']}")
print(f"EMA: {sc['ema_fast']}/{sc['ema_slow']}")
print(f"R:R: 1:{sc['rr_ratio']}")
print(f"Stop Loss: {sc['sl_atr_mult']}x ATR")
print(f"RSI: {sc['rsi_oversold']}/{sc['rsi_overbought']}")
print(f"\nPERFORMANCE:")
print(f"  Sharpe Ratio: {best['sharpe']:.2f}")
print(f"  Annual Return: {best['annual_return']:.1f}%")
print(f"  Win Rate: {best['win_rate']:.1f}%")
print(f"  Max Drawdown: {best['max_dd']:.1f}%")
print(f"  Profit Factor: {best['profit_factor']:.2f}")
print(f"  Total Trades: {best['trades']:,}")
print(f"  Avg Win: {best['avg_win']:.3f}%")
print(f"  Avg Loss: {best['avg_loss']:.3f}%")

print(f"\n{'='*100}")
print(f"[INFO] Search is {(data['tested']/2970*100):.1f}% complete - More strategies being discovered!")
print(f"[INFO] Estimated {len(filtered)*4} total excellent strategies when complete")
print("="*100 + "\n")

# Save filtered results
export_file = latest.parent / "filtered_3.5pct_DD.json"
with open(export_file, 'w') as f:
    json.dump({
        'criteria': {'win_rate': 65.0, 'max_dd': 3.5, 'sharpe': 2.0},
        'total_matching': len(filtered),
        'top_5_sharpe': by_sharpe[:5],
        'top_5_return': by_return[:5],
        'top_5_winrate': by_winrate[:5]
    }, f, indent=2, default=str)

print(f"[SAVED] Filtered results: {export_file}")


