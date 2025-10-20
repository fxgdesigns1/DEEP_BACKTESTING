#!/usr/bin/env python3
"""
Progress Monitor for Multi-Timeframe Strategy Search
Periodically checks progress and shows best findings
"""

import os
import json
import time
import subprocess
import psutil
from pathlib import Path
from datetime import datetime
import re

class ProgressMonitor:
    def __init__(self):
        self.log_file = "logs/multi_tf_sanity.out"
        self.results_dir = Path("results")
        self.best_findings = []
        self.last_progress = 0
        
    def get_process_info(self):
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
    
    def parse_progress(self, log_content):
        """Parse progress from log content"""
        progress_matches = re.findall(r'Progress: ([\d.]+)% \((\d+)/(\d+)\)', log_content)
        if progress_matches:
            latest = progress_matches[-1]
            return {
                'percentage': float(latest[0]),
                'completed': int(latest[1]),
                'total': int(latest[2])
            }
        return None
    
    def parse_experiment_results(self, log_content):
        """Parse experiment results from log content"""
        results = []
        
        # Find all experiment results
        experiment_pattern = r'🧪 Running experiment: (\w+) (\w+) (\w+) \[(\w+)\]'
        experiments = re.findall(experiment_pattern, log_content)
        
        # Find corresponding results
        for pair, tf, strategy, config_hash in experiments:
            # Look for results after this experiment
            pattern = f'🧪 Running experiment: {pair} {tf} {strategy} \\[{config_hash}\\]'
            start_idx = log_content.find(pattern)
            if start_idx != -1:
                # Look for results in the next 50 lines
                end_idx = start_idx + 2000  # Look ahead
                section = log_content[start_idx:end_idx]
                
                # Check if it passed or failed
                if '✅ Experiment completed' in section:
                    # Extract metrics
                    sharpe_match = re.search(r'Sharpe: ([\d.-]+)', section)
                    trades_match = re.search(r'Trades: (\d+)', section)
                    sig_match = re.search(r'Sig: (\w+)', section)
                    
                    if sharpe_match:
                        results.append({
                            'pair': pair,
                            'timeframe': tf,
                            'strategy': strategy,
                            'config_hash': config_hash,
                            'sharpe': float(sharpe_match.group(1)),
                            'trades': int(trades_match.group(1)) if trades_match else 0,
                            'signature': sig_match.group(1) if sig_match else 'unknown',
                            'status': 'success'
                        })
                elif '❌ Failed selection criteria' in section:
                    results.append({
                        'pair': pair,
                        'timeframe': tf,
                        'strategy': strategy,
                        'config_hash': config_hash,
                        'status': 'failed'
                    })
        
        return results
    
    def get_best_findings(self):
        """Get best findings from results directory"""
        best = []
        
        if not self.results_dir.exists():
            return best
            
        # Look for today's results
        today = datetime.now().strftime("%Y-%m-%d")
        today_dir = self.results_dir / today
        
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
                            'config_hash': data.get('config_hash', 'unknown'),
                            'trade_signature': data.get('trade_signature', 'unknown')
                        })
            except Exception as e:
                continue
                
        # Sort by Sharpe ratio
        best.sort(key=lambda x: x['sharpe'], reverse=True)
        return best[:5]  # Top 5
    
    def get_recent_activity(self, log_content):
        """Get recent activity from log"""
        lines = log_content.split('\n')
        recent_lines = [line for line in lines[-20:] if line.strip()]
        
        activity = []
        for line in recent_lines:
            if '🧪 Running experiment' in line:
                # Extract experiment info
                match = re.search(r'🧪 Running experiment: (\w+) (\w+) (\w+) \[(\w+)\]', line)
                if match:
                    activity.append(f"Testing: {match.group(1)} {match.group(2)} {match.group(3)}")
            elif '✅ Experiment completed' in line:
                activity.append(f"✅ SUCCESS: {line.split('✅ Experiment completed: ')[1]}")
            elif '❌ Failed selection criteria' in line:
                activity.append(f"❌ Failed: {line.split('❌ Failed selection criteria: ')[1]}")
                
        return activity[-10:]  # Last 10 activities
    
    def monitor(self, interval=30, findings_interval=3600):
        """Monitor progress with periodic updates"""
        print("🔍 Multi-Timeframe Strategy Search Monitor")
        print("=" * 60)
        print(f"Monitoring: {self.log_file}")
        print(f"Progress updates: every {interval} seconds")
        print(f"Best findings updates: every {findings_interval/60} minutes")
        print("=" * 60)
        
        last_findings_update = 0
        
        while True:
            try:
                # Check if process is running
                process_info = self.get_process_info()
                
                if not process_info['running']:
                    print(f"\n⏹️  Process not running. Checking for completion...")
                    break
                
                # Read log file
                if not os.path.exists(self.log_file):
                    print(f"\n⏳ Waiting for log file: {self.log_file}")
                    time.sleep(interval)
                    continue
                
                with open(self.log_file, 'r') as f:
                    log_content = f.read()
                
                # Parse progress
                progress = self.parse_progress(log_content)
                
                if progress:
                    # Check if progress has changed
                    if progress['completed'] != self.last_progress:
                        print(f"\n📊 PROGRESS UPDATE - {datetime.now().strftime('%H:%M:%S')}")
                        print(f"   Progress: {progress['percentage']:.1f}% ({progress['completed']}/{progress['total']})")
                        print(f"   Process: PID {process_info['pid']}, CPU: {process_info['cpu_percent']:.1f}%, RAM: {process_info['memory_mb']:.1f}MB")
                        
                        # Get recent activity
                        recent_activity = self.get_recent_activity(log_content)
                        if recent_activity:
                            print(f"   Recent Activity:")
                            for activity in recent_activity[-3:]:  # Last 3 activities
                                print(f"     {activity}")
                        
                        self.last_progress = progress['completed']
                
                # Get best findings (only every hour)
                current_time = time.time()
                if current_time - last_findings_update >= findings_interval:
                    best_findings = self.get_best_findings()
                    if best_findings:
                        print(f"\n🏆 BEST FINDINGS SO FAR (Updated every hour):")
                        for i, finding in enumerate(best_findings, 1):
                            print(f"   {i}. {finding['pair']} {finding['timeframe']} {finding['strategy']}")
                            print(f"      Sharpe: {finding['sharpe']:.3f}, Sortino: {finding['sortino']:.3f}")
                            print(f"      Max DD: {finding['max_dd']:.1%}, Profit Factor: {finding['profit_factor']:.2f}")
                            print(f"      Trades: {finding['trades']}, Sig: {finding['trade_signature']}")
                            print()
                    else:
                        print(f"\n🔍 No successful strategies found yet...")
                    last_findings_update = current_time
                
                # Estimate time remaining
                if progress and progress['completed'] > 0:
                    elapsed = time.time() - os.path.getmtime(self.log_file)
                    rate = progress['completed'] / elapsed
                    remaining = (progress['total'] - progress['completed']) / rate
                    eta = datetime.now().timestamp() + remaining
                    print(f"⏱️  ETA: {datetime.fromtimestamp(eta).strftime('%H:%M:%S')} ({remaining/60:.1f} minutes)")
                
                print("=" * 60)
                
            except KeyboardInterrupt:
                print(f"\n👋 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                
            time.sleep(interval)
        
        # Final summary
        print(f"\n📋 FINAL SUMMARY")
        best_findings = self.get_best_findings()
        if best_findings:
            print(f"🏆 Top {len(best_findings)} successful strategies:")
            for i, finding in enumerate(best_findings, 1):
                print(f"   {i}. {finding['pair']} {finding['timeframe']} {finding['strategy']} - Sharpe: {finding['sharpe']:.3f}")
        else:
            print(f"❌ No successful strategies found")
        
        print(f"📁 Results saved in: {self.results_dir}")

def main():
    monitor = ProgressMonitor()
    monitor.monitor(interval=30)  # Update every 30 seconds

if __name__ == "__main__":
    main()
