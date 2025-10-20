#!/usr/bin/env python3
"""
Quick script to analyze why optimization found 0 survivors
"""

import json
import glob

print("\n" + "="*80)
print("CHECKING OPTIMIZER RESULTS")
print("="*80 + "\n")

# Find all result files
phase1_files = glob.glob("results/phase1_survivors_*.json")
if phase1_files:
    latest = sorted(phase1_files)[-1]
    print(f"Latest Phase 1 file: {latest}")
    
    with open(latest, 'r') as f:
        survivors = json.load(f)
    
    print(f"Survivors found: {len(survivors)}\n")
    
    if survivors:
        for s in survivors:
            print(f"  - {s['strategy']} | {s['pair']} | {s['timeframe']}")
            print(f"    Sharpe: {s['sharpe_ratio']:.2f} | Win Rate: {s['win_rate']:.1f}%")
    else:
        print("  No survivors found!")
        print("\n  Possible reasons:")
        print("  1. Strategies generating 0 trades")
        print("  2. Filters too strict")
        print("  3. Configuration issues")
else:
    print("No phase 1 files found!")

print("\n" + "="*80)
print("Recommended: Lower Phase 1 filters and re-run")
print("="*80)




