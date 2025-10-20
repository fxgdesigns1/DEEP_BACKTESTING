#!/usr/bin/env python3
"""
Launch Multi-Timeframe Strategy Search
Stops current 1h-only search and launches proper multi-timeframe discovery
"""

import os
import subprocess
import time
import signal
import psutil
from pathlib import Path

def find_controller_process():
    """Find the running controller process"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'Python' and proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if 'controller.py' in cmdline and 'experiments_1h_broad.yaml' in cmdline:
                    return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def stop_current_search():
    """Stop the current 1h-only search"""
    pid = find_controller_process()
    if pid:
        print(f"🛑 Stopping current 1h-only search (PID: {pid})")
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            # Check if still running
            if psutil.pid_exists(pid):
                print(f"⚠️ Process still running, force killing...")
                os.kill(pid, signal.SIGKILL)
            print("✅ Current search stopped")
        except ProcessLookupError:
            print("✅ Process already stopped")
        except Exception as e:
            print(f"❌ Error stopping process: {e}")
    else:
        print("ℹ️ No running controller process found")

def launch_sanity_run():
    """Launch multi-timeframe sanity run"""
    print("🚀 Launching multi-timeframe sanity run...")
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Launch in background
    cmd = [
        "python", "controller.py", 
        "--config", "experiments_multi_tf_sanity.yaml"
    ]
    
    with open("logs/multi_tf_sanity.out", "w") as f:
        process = subprocess.Popen(
            cmd,
            stdout=f,
            stderr=subprocess.STDOUT,
            cwd=os.getcwd()
        )
    
    print(f"✅ Sanity run launched (PID: {process.pid})")
    print("📊 Monitoring logs/multi_tf_sanity.out")
    return process.pid

def launch_4h_daily_run():
    """Launch 4h/daily focus run"""
    print("🚀 Launching 4h/daily focus run...")
    
    cmd = [
        "python", "controller.py", 
        "--config", "experiments_4h_daily_focus.yaml"
    ]
    
    with open("logs/4h_daily_focus.out", "w") as f:
        process = subprocess.Popen(
            cmd,
            stdout=f,
            stderr=subprocess.STDOUT,
            cwd=os.getcwd()
        )
    
    print(f"✅ 4h/daily run launched (PID: {process.pid})")
    print("📊 Monitoring logs/4h_daily_focus.out")
    return process.pid

def main():
    print("🎯 Multi-Timeframe Strategy Search Launcher")
    print("=" * 50)
    
    # Step 1: Stop current search
    stop_current_search()
    time.sleep(3)
    
    # Step 2: Launch sanity run
    sanity_pid = launch_sanity_run()
    
    print("\n" + "=" * 50)
    print("📋 NEXT STEPS:")
    print("1. Monitor sanity run: tail -f logs/multi_tf_sanity.out")
    print("2. Check for parameter variability in trade signatures")
    print("3. If variability looks good, launch 4h/daily run")
    print("4. Compare results across timeframes")
    print("\n🔍 KEY OBSERVATIONS TO LOOK FOR:")
    print("- Different trade signatures across parameter combinations")
    print("- Varying trade counts across timeframes")
    print("- Performance differences between 15m, 4h, 1d")
    print("- Parameter sensitivity in results")
    
    print(f"\n✅ Sanity run PID: {sanity_pid}")
    print("📊 Check logs/multi_tf_sanity.out for progress")

if __name__ == "__main__":
    main()
