#!/usr/bin/env python3
"""Quick progress checker for optimization"""

import os
import json
from pathlib import Path
from datetime import datetime

print("\n" + "=" * 80)
print("OPTIMIZATION PROGRESS CHECK")
print("=" * 80)

# Check for results files
results_files = list(Path(".").glob("optimization_results_*.json"))

if results_files:
    latest = max(results_files, key=lambda p: p.stat().st_mtime)
    
    with open(latest, 'r') as f:
        data = json.load(f)
    
    print(f"\nLatest Results File: {latest.name}")
    print(f"Scenarios Tested: {data.get('total_tested', 0):,}")
    print(f"Time Elapsed: {data.get('elapsed_time', 'Unknown')}")
    print()
    print(f"SUCCESS COUNT:")
    print(f"  EXCELLENT: {len(data.get('excellent', []))}")
    print(f"  GOOD: {len(data.get('good', []))}")
    print(f"  ACCEPTABLE: {len(data.get('acceptable', []))}")
    
    # Show best strategy
    if data.get('excellent'):
        best = data['excellent'][0]
        print(f"\n[BEST STRATEGY]")
        print(f"  Pair: {best['scenario']['pair'].upper()}")
        print(f"  Timeframe: {best['scenario']['timeframe']}")
        print(f"  Sharpe: {best['sharpe']:.2f}")
        print(f"  Annual Return: {best['annual_return']:.1f}%")
        print(f"  Trades: {best['total_trades']}")
    
else:
    print("\n[INFO] Optimization still initializing...")
    print("[INFO] Results will appear as successful strategies are found")
    
    # Check if process is running
    import subprocess
    result = subprocess.run(['powershell', '-Command', 
                           'Get-Process python -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count'],
                          capture_output=True, text=True)
    
    process_count = int(result.stdout.strip()) if result.stdout.strip() else 0
    print(f"\n[STATUS] {process_count} Python processes active")
    
    if process_count > 1:
        print("[OK] Optimization is running!")
    else:
        print("[WARNING] Optimization may not be running")

print("\n" + "=" * 80)
print("Run this script again anytime to check progress")
print("=" * 80 + "\n")


