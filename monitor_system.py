#!/usr/bin/env python3
"""
System Monitor for Parallel Strategy Search
"""

import psutil
import time
import os
from datetime import datetime

def monitor_system():
    """Monitor system utilization"""
    print("🚀 PARALLEL STRATEGY SEARCH - SYSTEM MONITOR")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # CPU Usage
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    print(f"💻 CPU: {cpu_percent}% (of {cpu_count} cores)")
    
    # Memory Usage
    memory = psutil.virtual_memory()
    print(f"🧠 Memory: {memory.percent}% ({memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB)")
    
    # Python Processes
    python_processes = [p for p in psutil.process_iter() if "python" in p.name().lower()]
    print(f"🐍 Python Processes: {len(python_processes)}")
    
    # Check for results
    if os.path.exists("results"):
        result_dirs = [d for d in os.listdir("results") if os.path.isdir(os.path.join("results", d))]
        print(f"📊 Results Directories: {len(result_dirs)}")
        
        # Check for today's results
        today = datetime.now().strftime("%Y-%m-%d")
        if today in result_dirs:
            today_results = os.listdir(f"results/{today}")
            print(f"📈 Today's Results: {len(today_results)} files")
    
    print()
    print("💡 System is optimized for parallel processing!")
    print("💡 Using 16 CPU cores for maximum performance")

if __name__ == "__main__":
    monitor_system()

