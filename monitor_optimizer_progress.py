#!/usr/bin/env python3
"""
Real-time optimizer progress monitor
Watches log file and displays progress
"""

import os
import time
from datetime import datetime

LOG_FILE = "strategy_optimizer.log"

def monitor_progress():
    """Monitor optimizer progress in real-time"""
    print("\n" + "="*80)
    print("STRATEGY OPTIMIZER - LIVE PROGRESS MONITOR")
    print("="*80 + "\n")
    print("Press Ctrl+C to stop monitoring\n")
    
    if not os.path.exists(LOG_FILE):
        print(f"Waiting for {LOG_FILE} to be created...")
        while not os.path.exists(LOG_FILE):
            time.sleep(1)
    
    # Open log file and seek to end
    with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        # Seek to end
        f.seek(0, 2)
        
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            
            # Filter for important lines
            if any(keyword in line for keyword in [
                'Testing', 'SURVIVOR', 'REFINED', 'Phase', 
                'Complete', 'Failed', 'survivors', 'optimized'
            ]):
                # Clean up the line
                clean_line = line.strip()
                if clean_line:
                    # Add timestamp
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] {clean_line}")

if __name__ == "__main__":
    try:
        monitor_progress()
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
    except Exception as e:
        print(f"\nError: {e}")




