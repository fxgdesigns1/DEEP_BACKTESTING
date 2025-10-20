#!/usr/bin/env python3
"""
Quick progress checker - run anytime
"""

import os
import json
import glob
from datetime import datetime

def show_progress():
    print("\n" + "="*80)
    print(f"OPTIMIZER PROGRESS CHECK - {datetime.now().strftime('%H:%M:%S')}")
    print("="*80 + "\n")
    
    # Check if optimizer is running
    log_file = "strategy_optimizer.log"
    if not os.path.exists(log_file):
        print("[ERROR] Optimizer not started yet or log file missing\n")
        return
    
    # Read log file
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    # Find key information
    phase1_complete = False
    phase2_complete = False
    survivors_count = 0
    optimized_count = 0
    current_test = "Unknown"
    
    for line in lines:
        if "Testing" in line and "[" in line:
            current_test = line.strip()
        if "Phase 1 Complete" in line:
            phase1_complete = True
            if "survivors" in line:
                try:
                    survivors_count = int(line.split("survivors")[0].split()[-1])
                except:
                    pass
        if "Phase 2 Complete" in line or "OPTIMIZATION COMPLETE" in line:
            phase2_complete = True
        if "Phase 2 Optimized:" in line:
            try:
                optimized_count = int(line.split(":")[-1].strip())
            except:
                pass
    
    # Display status
    if phase2_complete:
        print("[COMPLETE] OPTIMIZATION COMPLETE!\n")
        print(f"   Phase 1 Survivors: {survivors_count}")
        print(f"   Phase 2 Optimized: {optimized_count}")
        print("\n   Check results in:")
        print(f"   - results/phase1_survivors_*.json")
        print(f"   - results/phase2_optimized_*.json")
        print(f"   - results/top_10_strategies_*.json")
    elif phase1_complete:
        print(f"[RUNNING] PHASE 2 - Refining {survivors_count} survivors\n")
        if current_test and current_test != "Unknown":
            print(f"   Last activity: {current_test}")
    else:
        print("[RUNNING] PHASE 1 - Broad Exploration\n")
        if current_test and current_test != "Unknown":
            print(f"   Current: {current_test}")
    
    # Show last few log lines
    print("\n   Recent activity (last 5 lines):")
    important_lines = [l for l in lines if any(k in l for k in ['Testing', 'SURVIVOR', 'Complete', 'Phase'])]
    for line in important_lines[-5:]:
        clean = line.strip().split(" - ")[-1] if " - " in line else line.strip()
        print(f"   {clean}")
    
    print("\n" + "="*80)
    print("Run this script again anytime to check progress")
    print("="*80 + "\n")

if __name__ == "__main__":
    show_progress()

