#!/usr/bin/env python3
"""
Filter strategies with LARGE wins criteria:
- Average wins: 1-2%
- Average losses: < 1%
- Still maintain good win rate and drawdown
"""

import json
from pathlib import Path

print("\n" + "="*100)
print(" "*20 + "FILTERING FOR LARGE WIN STRATEGIES")
print("="*100)
print("\nNEW CRITERIA:")
print("  Average Win: 1.0% - 2.0%")
print("  Average Loss: < 1.0%")
print("  Win Rate: >= 65%")
print("  Max Drawdown: <= 3.5%")
print("="*100)

# Load completed results
results_file = Path(r"H:\My Drive\AI Trading\exported strategies\ultimate_search_20251004_091405\ultimate_search_results.json")

if not results_file.exists():
    print("\n[ERROR] Results file not found")
    exit(1)

with open(results_file, 'r') as f:
    data = json.load(f)

# Filter for large wins
large_win_strategies = []

for strategy in data['top_20']:
    avg_win = abs(strategy.get('avg_win', 0))
    avg_loss = abs(strategy.get('avg_loss', 0))
    
    # Check if meets large win criteria
    if (1.0 <= avg_win <= 2.0 and 
        avg_loss < 1.0 and 
        strategy['win_rate'] >= 65.0 and 
        strategy['max_dd'] <= 3.5):
        
        large_win_strategies.append(strategy)

print(f"\n[FOUND] {len(large_win_strategies)} strategies meeting large win criteria")

if large_win_strategies:
    # Sort by avg win size
    large_win_strategies.sort(key=lambda x: x.get('avg_win', 0), reverse=True)
    
    print(f"\n{'='*100}")
    print("STRATEGIES WITH 1-2% AVERAGE WINS")
    print("="*100)
    print(f"\n{'Rank':<6} {'Pair':<10} {'TF':<6} {'AvgWin':<10} {'AvgLoss':<10} {'WinRate':<9} {'Sharpe':<8} {'Return':<10}")
    print("-"*100)
    
    for i, s in enumerate(large_win_strategies, 1):
        sc = s['scenario']
        print(f"{i:<6} {sc['pair'].upper():<10} {sc['timeframe']:<6} "
              f"{abs(s['avg_win']):<9.3f}% {abs(s['avg_loss']):<9.3f}% "
              f"{s['win_rate']:<8.1f}% {s['sharpe']:<8.2f} {s['annual_return']:<9.1f}%")
    
    # Analyze what changed
    print(f"\n{'='*100}")
    print("IMPACT OF LARGE WIN REQUIREMENT")
    print("="*100)
    
    # Compare to best overall strategy
    best_overall = data['top_20'][0]
    if large_win_strategies:
        best_large_win = large_win_strategies[0]
        
        print(f"\nBest Overall Strategy (GBP_USD):")
        print(f"  Avg Win: {abs(best_overall.get('avg_win', 0)):.3f}%")
        print(f"  Avg Loss: {abs(best_overall.get('avg_loss', 0)):.3f}%")
        print(f"  Sharpe: {best_overall['sharpe']:.2f}")
        print(f"  Return: {best_overall['annual_return']:.1f}%")
        print(f"  Win Rate: {best_overall['win_rate']:.1f}%")
        
        print(f"\nBest Large Win Strategy:")
        sc = best_large_win['scenario']
        print(f"  Pair: {sc['pair'].upper()}")
        print(f"  Avg Win: {abs(best_large_win.get('avg_win', 0)):.3f}%")
        print(f"  Avg Loss: {abs(best_large_win.get('avg_loss', 0)):.3f}%")
        print(f"  Sharpe: {best_large_win['sharpe']:.2f}")
        print(f"  Return: {best_large_win['annual_return']:.1f}%")
        print(f"  Win Rate: {best_large_win['win_rate']:.1f}%")
        
        print(f"\nDIFFERENCE:")
        print(f"  Sharpe: {best_large_win['sharpe'] - best_overall['sharpe']:+.2f}")
        print(f"  Return: {best_large_win['annual_return'] - best_overall['annual_return']:+.1f}%")
        print(f"  Win Rate: {best_large_win['win_rate'] - best_overall['win_rate']:+.1f}%")
        
        # What parameters enable large wins?
        print(f"\nWHAT ENABLES LARGE WINS:")
        print(f"  R:R Ratio: 1:{sc.get('rr_ratio', 'N/A')}")
        print(f"  Stop Loss: {sc.get('sl_atr_mult', 'N/A')}x ATR")
        print(f"  EMA: {sc.get('ema_fast', 'N/A')}/{sc.get('ema_slow', 'N/A')}")

else:
    print(f"\n[RESULT] No strategies in TOP 20 meet the 1-2% avg win criteria")
    print(f"\n[ANALYSIS] Why This Is Difficult:")
    print(f"  - 5-minute timeframe averages 0.1-0.3% per trade")
    print(f"  - To get 1-2% avg wins need:")
    print(f"    * Larger timeframes (15m, 1h, 4h)")
    print(f"    * Much higher R:R ratios (5:1 to 10:1)")
    print(f"    * Wider stops (2-3x ATR)")
    print(f"    * Accepting lower win rates (50-60%)")
    
    # Check which pairs came closest
    closest = sorted(data['top_20'], key=lambda x: abs(x.get('avg_win', 0)), reverse=True)[:5]
    
    print(f"\n[CLOSEST TO TARGET]")
    print(f"Top 5 by largest average wins:")
    print(f"\n{'Pair':<10} {'TF':<6} {'AvgWin':<10} {'AvgLoss':<10} {'R:R':<8} {'Sharpe':<8} {'Return':<10}")
    print("-"*80)
    
    for s in closest:
        sc = s['scenario']
        print(f"{sc['pair'].upper():<10} {sc['timeframe']:<6} "
              f"{abs(s.get('avg_win', 0)):<9.3f}% {abs(s.get('avg_loss', 0)):<9.3f}% "
              f"1:{sc.get('rr_ratio', 0):<7.1f} {s['sharpe']:<8.2f} {s['annual_return']:<9.1f}%")
    
    print(f"\n[RECOMMENDATION] To achieve 1-2% avg wins:")
    print(f"  1. Test 15-minute or 1-hour timeframes (larger moves)")
    print(f"  2. Use R:R ratios of 5:1 to 10:1")
    print(f"  3. Accept lower win rates (50-65%)")
    print(f"  4. Focus on XAU_USD (Gold) - naturally larger moves")
    print(f"  5. Use wider stops (2.5x to 3.0x ATR)")

print(f"\n{'='*100}")
print("[INFO] The advanced optimizer is testing higher R:R ratios (up to 5:1)")
print("[INFO] Check back in 4-6 hours for results with larger wins!")
print("="*100 + "\n")


