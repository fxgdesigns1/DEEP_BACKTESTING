#!/usr/bin/env python3
"""
Quick Status Check for Multi-Timeframe Strategy Search
Run this anytime to see current progress and best findings
"""

import os
import json
import re
import psutil
from pathlib import Path
from datetime import datetime

def get_process_info():
    """Get information about running controller process"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info']):
        try:
            if proc.info['name'] == 'Python' and proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if 'controller.py' in cmdline and 'experiments_multi_tf_sanity.yaml' in cmdline:
                    return {
                        'pid': proc.info['pid'],
                        'cpu_percent': proc.cpu_percent(),
                        'memory_mb': proc.info['memory_info'].rss / 1024 / 1024,
                        'running': True
                    }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return {'running': False}

def get_current_progress():
    """Get current progress from log file"""
    log_file = "logs/multi_tf_sanity.out"
    
    if not os.path.exists(log_file):
        return None
    
    with open(log_file, 'r') as f:
        content = f.read()
    
    # Find latest progress
    progress_matches = re.findall(r'Progress: ([\d.]+)% \((\d+)/(\d+)\)', content)
    if progress_matches:
        latest = progress_matches[-1]
        return {
            'percentage': float(latest[0]),
            'completed': int(latest[1]),
            'total': int(latest[2])
        }
    return None

def get_best_findings():
    """Get best findings from results directory"""
    best = []
    results_dir = Path("results")
    
    if not results_dir.exists():
        return best
        
    # Look for today's results
    today = datetime.now().strftime("%Y-%m-%d")
    today_dir = results_dir / today
    
    if not today_dir.exists():
        return best
        
    # Find all summary.json files
    for summary_file in today_dir.rglob("summary.json"):
        try:
            with open(summary_file, 'r') as f:
                data = json.load(f)
                
            if 'metrics' in data:
                metrics = data['metrics']
                sharpe = metrics.get('oos_sharpe', 0)
                
                if sharpe > 0:  # Only include positive Sharpe
                    best.append({
                        'pair': data.get('pair', 'unknown'),
                        'timeframe': data.get('timeframe', 'unknown'),
                        'strategy': data.get('strategy', 'unknown'),
                        'sharpe': sharpe,
                        'sortino': metrics.get('oos_sortino', 0),
                        'max_dd': metrics.get('oos_max_dd', 0),
                        'profit_factor': metrics.get('profit_factor', 0),
                        'trades': metrics.get('total_trades', 0),
                        'trade_signature': data.get('trade_signature', 'unknown')
                    })
        except Exception:
            continue
            
    # Sort by Sharpe ratio
    best.sort(key=lambda x: x['sharpe'], reverse=True)
    return best[:3]  # Top 3

def get_recent_activity():
    """Get recent activity from log"""
    log_file = "logs/multi_tf_sanity.out"
    
    if not os.path.exists(log_file):
        return []
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    # Get last 10 lines with activity
    recent_activity = []
    for line in lines[-50:]:  # Check last 50 lines
        if '🧪 Running experiment' in line or '✅ Experiment completed' in line or '❌ Failed selection criteria' in line:
            recent_activity.append(line.strip())
    
    return recent_activity[-5:]  # Last 5 activities

def main():
    print("🔍 MULTI-TIMEFRAME STRATEGY SEARCH - STATUS CHECK")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if process is running
    process_info = get_process_info()
    if process_info['running']:
        print(f"✅ PROCESS RUNNING")
        print(f"   PID: {process_info['pid']}")
        print(f"   CPU: {process_info['cpu_percent']:.1f}%")
        print(f"   RAM: {process_info['memory_mb']:.1f}MB")
    else:
        print(f"❌ PROCESS NOT RUNNING")
        print("   The search may have completed or stopped")
    
    print()
    
    # Get progress
    progress = get_current_progress()
    if progress:
        print(f"📊 PROGRESS")
        print(f"   {progress['percentage']:.1f}% complete ({progress['completed']}/{progress['total']} experiments)")
        
        # Estimate time remaining
        if progress['completed'] > 0:
            log_file = "logs/multi_tf_sanity.out"
            if os.path.exists(log_file):
                elapsed = time.time() - os.path.getmtime(log_file)
                rate = progress['completed'] / elapsed
                remaining = (progress['total'] - progress['completed']) / rate
                eta = datetime.now().timestamp() + remaining
                print(f"   ETA: {datetime.fromtimestamp(eta).strftime('%H:%M:%S')} ({remaining/60:.1f} minutes)")
    else:
        print(f"📊 PROGRESS: Unable to determine")
    
    print()
    
    # Get best findings
    best_findings = get_best_findings()
    if best_findings:
        print(f"🏆 BEST FINDINGS SO FAR")
        for i, finding in enumerate(best_findings, 1):
            print(f"   {i}. {finding['pair']} {finding['timeframe']} {finding['strategy']}")
            print(f"      Sharpe: {finding['sharpe']:.3f}, Sortino: {finding['sortino']:.3f}")
            print(f"      Max DD: {finding['max_dd']:.1%}, Profit Factor: {finding['profit_factor']:.2f}")
            print(f"      Trades: {finding['trades']}, Sig: {finding['trade_signature']}")
            print()
    else:
        print(f"🔍 No successful strategies found yet...")
    
    print()
    
    # Get recent activity
    recent_activity = get_recent_activity()
    if recent_activity:
        print(f"📈 RECENT ACTIVITY")
        for activity in recent_activity:
            if '🧪 Running experiment' in activity:
                # Extract experiment info
                match = re.search(r'🧪 Running experiment: (\w+) (\w+) (\w+)', activity)
                if match:
                    print(f"   Testing: {match.group(1)} {match.group(2)} {match.group(3)}")
            elif '✅ Experiment completed' in activity:
                print(f"   ✅ SUCCESS: {activity.split('✅ Experiment completed: ')[1]}")
            elif '❌ Failed selection criteria' in activity:
                print(f"   ❌ Failed: {activity.split('❌ Failed selection criteria: ')[1]}")
    
    print()
    print("=" * 60)
    print("💡 Run 'python3 check_status.py' anytime for updates")
    print("💡 Run 'python3 monitor_progress.py' for continuous monitoring")

if __name__ == "__main__":
    import time
    main()
