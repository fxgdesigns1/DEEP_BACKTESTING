#!/usr/bin/env python3
"""Real-time simulation progress monitor"""

import os
import json
import time
from pathlib import Path
from datetime import datetime

def check_progress():
    """Check progress of all simulations"""
    results_dir = Path("results")
    
    print("\n" + "=" * 80)
    print(f"SIMULATION PROGRESS MONITOR - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 80)
    
    # Check for new result files in last 5 minutes
    cutoff_time = time.time() - 300
    recent_files = []
    
    if results_dir.exists():
        for json_file in results_dir.rglob("*.json"):
            try:
                if json_file.stat().st_mtime > cutoff_time:
                    recent_files.append(json_file)
            except:
                continue
    
    print(f"\n[STATUS] Recent result files: {len(recent_files)}")
    
    # Analyze recent results
    best_sharpe = -999
    best_strategy = None
    
    for result_file in recent_files:
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                if 'best_strategy' in data:
                    strategy = data['best_strategy']
                    sharpe = strategy.get('sharpe_ratio', 0)
                    
                    print(f"\n[FILE] {result_file.name}")
                    print(f"  Strategy: {strategy.get('name', 'Unknown')}")
                    print(f"  Sharpe: {sharpe:.2f}")
                    print(f"  Win Rate: {strategy.get('win_rate', 0):.1f}%")
                    print(f"  Return: {strategy.get('total_return', 0):.2f}%")
                    
                    if sharpe > best_sharpe:
                        best_sharpe = sharpe
                        best_strategy = {
                            'file': result_file.name,
                            'strategy': strategy
                        }
        except:
            continue
    
    # Report best so far
    if best_strategy:
        print("\n" + "-" * 80)
        print(">>> BEST STRATEGY SO FAR <<<")
        print("-" * 80)
        strat = best_strategy['strategy']
        print(f"Source: {best_strategy['file']}")
        print(f"Strategy: {strat.get('name', 'Unknown')}")
        print(f"Sharpe Ratio: {strat.get('sharpe_ratio', 0):.2f}")
        print(f"Win Rate: {strat.get('win_rate', 0):.1f}%")
        print(f"Total Return: {strat.get('total_return', 0):.2f}%")
        print(f"Max Drawdown: {strat.get('max_drawdown', 0):.2f}%")
    
    print("\n" + "=" * 80)
    print("[INFO] Simulations still running... Check back in a few minutes")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    check_progress()


