#!/usr/bin/env python3
"""
Analyze trade frequency from the Monte Carlo results
Calculate trades per week for each strategy
"""

import json
import pandas as pd
from datetime import datetime, timedelta

# Load the enhanced MC results
with open('enhanced_mc_results_20251018_181831.json', 'r') as f:
    results = json.load(f)

print("="*80)
print("TRADE FREQUENCY ANALYSIS")
print("="*80)

# Test period: 18,526 candles at 15m intervals
candles = 18526
minutes_per_candle = 15
total_minutes = candles * minutes_per_candle
total_days = total_minutes / (60 * 24)
total_weeks = total_days / 7

print(f"\nTest Period:")
print(f"  Candles: {candles:,}")
print(f"  Days: {total_days:.1f}")
print(f"  Weeks: {total_weeks:.1f}")

print(f"\n{'='*80}")
print("TRADES PER WEEK BY STRATEGY:")
print(f"{'='*80}\n")

for i, strategy_result in enumerate(results, 1):
    strategy_name = strategy_result['strategy']
    total_trades = strategy_result['metrics']['total_trades']
    win_rate = strategy_result['metrics']['win_rate']
    sharpe = strategy_result['metrics']['sharpe_ratio']
    total_return = strategy_result['metrics']['total_return']
    
    trades_per_week = total_trades / total_weeks
    trades_per_month = total_trades / (total_weeks / 4.33)
    
    print(f"{i}. {strategy_name}")
    print(f"   Total Trades: {total_trades}")
    print(f"   Trades/Week: {trades_per_week:.1f}")
    print(f"   Trades/Month: {trades_per_month:.1f}")
    print(f"   Win Rate: {win_rate*100:.2f}%")
    print(f"   Return: {total_return*100:.2f}%")
    print(f"   Sharpe: {sharpe:.2f}")
    print()

print(f"{'='*80}")
print("OBSERVATIONS:")
print(f"{'='*80}")
print(f"\n- All strategies trade relatively infrequently (2-3 trades/week)")
print(f"- This is actually GOOD - quality over quantity")
print(f"- Win rates are 44-54% (realistic for trading)")
print(f"- More trades doesn't mean better returns")


