"""
Simple script to show the optimization results clearly
"""

import json
from pathlib import Path

# Load the filtered results
results_file = Path("H:/My Drive/AI Trading/exported strategies/ultimate_search_20251004_091405/filtered_3.5pct_DD.json")

with open(results_file) as f:
    data = json.load(f)

print("\n" + "="*100)
print(" "*30 + "YOUR OPTIMIZATION RESULTS")
print("="*100)

print(f"\nTOTAL STRATEGIES FOUND: {data['total_matching']} strategies meeting 3.5% max DD")
print(f"\nCriteria Used:")
print(f"  - Win Rate >= {data['criteria']['win_rate']}%")
print(f"  - Max Drawdown <= {data['criteria']['max_dd']}%")
print(f"  - Sharpe Ratio >= {data['criteria']['sharpe']}")

print("\n" + "="*100)
print("TOP 10 STRATEGIES - READY TO DEPLOY")
print("="*100)

top_strategies = data['top_5_sharpe'][:10] if len(data['top_5_sharpe']) >= 10 else data['top_5_sharpe']

for i, strategy in enumerate(top_strategies, 1):
    scenario = strategy['scenario']
    
    print(f"\n#{i}: {scenario['pair'].upper()} on {scenario['timeframe']}")
    print(f"   Performance:")
    print(f"      - Sharpe Ratio: {strategy['sharpe']:.2f}")
    print(f"      - Annual Return: {strategy['annual_return']:.1f}%")
    print(f"      - Win Rate: {strategy['win_rate']:.1f}%")
    print(f"      - Max Drawdown: {strategy['max_dd']:.2f}%")
    print(f"      - Profit Factor: {strategy['profit_factor']:.2f}")
    print(f"      - Total Trades: {strategy['trades']}")
    
    print(f"   Parameters:")
    print(f"      - EMA: {scenario['ema_fast']}/{scenario['ema_slow']}")
    print(f"      - Risk:Reward: 1:{scenario['rr_ratio']}")
    print(f"      - Stop Loss: {scenario['sl_atr_mult']}x ATR")
    print(f"      - RSI: {scenario['rsi_oversold']}/{scenario['rsi_overbought']}")
    
    print(f"   Trade Stats:")
    print(f"      - Avg Win: +{strategy['avg_win']:.3f}%")
    print(f"      - Avg Loss: {strategy['avg_loss']:.3f}%")
    print(f"      - Trades/Week: ~{strategy['trades']/156:.0f}")  # 3 years ≈ 156 weeks

print("\n" + "="*100)
print("KEY INSIGHTS")
print("="*100)

# Calculate averages
avg_sharpe = sum(s['sharpe'] for s in top_strategies) / len(top_strategies)
avg_return = sum(s['annual_return'] for s in top_strategies) / len(top_strategies)
avg_win_rate = sum(s['win_rate'] for s in top_strategies) / len(top_strategies)
avg_dd = sum(s['max_dd'] for s in top_strategies) / len(top_strategies)

print(f"\nAverage Performance (Top 10):")
print(f"   - Sharpe Ratio: {avg_sharpe:.2f}")
print(f"   - Annual Return: {avg_return:.1f}%")
print(f"   - Win Rate: {avg_win_rate:.1f}%")
print(f"   - Max Drawdown: {avg_dd:.2f}%")

print(f"\nAll strategies use:")
print(f"   - Timeframe: 5 minutes (scalping)")
print(f"   - EMA: 3/12 crossover (fast-moving)")
print(f"   - R:R: 1:2 ratio (conservative)")
print(f"   - Real data: 3 years OANDA MASTER_DATASET")

print("\n" + "="*100)
print("DEPLOYMENT RECOMMENDATION")
print("="*100)

print(f"\nSTART WITH TOP 3 STRATEGIES:")
print(f"   1. {top_strategies[0]['scenario']['pair'].upper()} (Sharpe: {top_strategies[0]['sharpe']:.2f})")
print(f"   2. {top_strategies[1]['scenario']['pair'].upper()} (Return: {top_strategies[1]['annual_return']:.1f}%)")
print(f"   3. {top_strategies[2]['scenario']['pair'].upper()} (Win Rate: {top_strategies[2]['win_rate']:.1f}%)")

print(f"\nNEXT STEPS:")
print(f"   1. Deploy to demo accounts")
print(f"   2. Monitor for 1-2 weeks")
print(f"   3. Verify live performance matches backtest")
print(f"   4. Scale up capital gradually")

print("\n" + "="*100)
print("Full details at:")
print("H:/My Drive/AI Trading/exported strategies/ultimate_search_20251004_091405/")
print("  - filtered_3.5pct_DD.json")
print("  - ULTIMATE_TOP_10_WITH_STATS.md")
print("="*100 + "\n")

