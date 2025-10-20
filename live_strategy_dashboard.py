#!/usr/bin/env python3
"""
LIVE STRATEGY MONITORING DASHBOARD
Real-time tracking of optimization progress and successful strategies
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

class LiveDashboard:
    """Real-time monitoring dashboard"""
    
    def __init__(self):
        self.export_path = Path(r"H:\My Drive\AI Trading\exported strategies\optimization_20251002_195254")
        self.top10_dir = self.export_path / "TOP_10_STRATEGIES"
        
    def get_python_process_count(self):
        """Get number of active Python processes"""
        try:
            result = subprocess.run(
                ['powershell', '-Command', 
                 'Get-Process python -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return int(result.stdout.strip()) if result.stdout.strip() else 0
        except:
            return 0
    
    def find_latest_results(self):
        """Find latest optimization results"""
        results_files = list(Path(".").glob("optimization_results_*.json"))
        
        if not results_files:
            return None
        
        return max(results_files, key=lambda p: p.stat().st_mtime)
    
    def display_dashboard(self):
        """Display real-time dashboard"""
        
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("\n" + "=" * 100)
        print(" " * 30 + "LIVE STRATEGY OPTIMIZATION DASHBOARD")
        print("=" * 100)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)
        
        # System status
        process_count = self.get_python_process_count()
        status = "[RUNNING]" if process_count > 5 else "[IDLE]"
        
        print(f"\n[SYSTEM STATUS] {status}")
        print(f"  Active Python Processes: {process_count}")
        print(f"  CPU Cores Available: 32")
        print(f"  Optimization Status: {'Active' if process_count > 5 else 'Stopped'}")
        
        # Check for results
        results_file = self.find_latest_results()
        
        if results_file:
            with open(results_file, 'r') as f:
                data = json.load(f)
            
            # Progress
            total_tested = data.get('total_tested', 0)
            
            print(f"\n[OPTIMIZATION PROGRESS]")
            print(f"  Scenarios Tested: {total_tested:,}")
            print(f"  Estimated Total: 76,800")
            print(f"  Progress: {(total_tested/76800*100):.1f}%")
            
            # Success counts
            excellent = len(data.get('excellent', []))
            good = len(data.get('good', []))
            acceptable = len(data.get('acceptable', []))
            
            print(f"\n[STRATEGIES DISCOVERED]")
            print(f"  EXCELLENT (Sharpe>2.0, Return>30%, DD<15%):  {excellent}")
            print(f"  GOOD      (Sharpe>1.5, Return>20%, DD<25%):  {good}")
            print(f"  ACCEPTABLE (Sharpe>1.0, Return>15%, DD<35%): {acceptable}")
            print(f"  TOTAL SUCCESSFUL: {excellent + good + acceptable}")
            
            # Filter by user criteria
            filtered = []
            for s in data.get('excellent', []):
                if s['win_rate'] >= 65.0 and s['max_dd'] <= 10.0:
                    filtered.append(s)
            
            print(f"\n[MEETING YOUR CRITERIA] (Win>=65%, DD<=10%)")
            print(f"  Total Strategies: {len(filtered)}")
            
            if filtered:
                # Sort by Sharpe
                filtered.sort(key=lambda x: x['sharpe'], reverse=True)
                
                # Show top 5
                print(f"\n[CURRENT TOP 5]")
                print(f"  {'Rank':<6} {'Sharpe':<8} {'Return':<10} {'WinRate':<9} {'DD':<8} {'Trades':<8}")
                print(f"  {'-'*6} {'-'*8} {'-'*10} {'-'*9} {'-'*8} {'-'*8}")
                
                for i, s in enumerate(filtered[:5], 1):
                    print(f"  #{i:<5} {s['sharpe']:<8.2f} {s['annual_return']:<9.1f}% {s['win_rate']:<8.1f}% {s['max_dd']:<7.1f}% {s['total_trades']:<8,}")
                
                # Best strategy details
                best = filtered[0]
                print(f"\n[BEST STRATEGY RIGHT NOW]")
                print(f"  Pair: {best['scenario']['pair'].upper()}")
                print(f"  Timeframe: {best['scenario']['timeframe']}")
                print(f"  EMA: {best['scenario']['ema_fast']}/{best['scenario']['ema_slow']}")
                print(f"  R:R: 1:{best['scenario']['rr_ratio']}")
                print(f"  SL: {best['scenario']['sl_atr_mult']}x ATR")
                print(f"  RSI: {best['scenario']['rsi_oversold']}/{best['scenario']['rsi_overbought']}")
                print(f"  Sharpe: {best['sharpe']:.2f}")
                print(f"  Return: {best['annual_return']:.1f}%")
                print(f"  Win Rate: {best['win_rate']:.1f}%")
                print(f"  Trades: {best['total_trades']:,}")
        
        else:
            print(f"\n[NO RESULTS YET]")
            print(f"  Optimization is initializing...")
            print(f"  Results will appear as strategies are tested")
        
        # Export status
        print(f"\n[EXPORT STATUS]")
        
        if self.top10_dir.exists():
            yaml_files = list(self.top10_dir.glob("RANK_*.yaml"))
            doc_file = self.top10_dir / "TOP_10_STRATEGIES_DOCUMENTATION.md"
            
            print(f"  Export Directory: {self.top10_dir}")
            print(f"  YAML Strategy Files: {len(yaml_files)}")
            print(f"  Documentation: {'YES' if doc_file.exists() else 'NO'}")
        else:
            print(f"  Export Directory: Not created yet")
        
        print("\n" + "=" * 100)
        print("[INFO] Press Ctrl+C to exit dashboard | Dashboard refreshes every 30 seconds")
        print("=" * 100 + "\n")
    
    def run_live(self, refresh_seconds=30):
        """Run live dashboard with auto-refresh"""
        
        try:
            while True:
                self.display_dashboard()
                time.sleep(refresh_seconds)
                
        except KeyboardInterrupt:
            print("\n\n[DASHBOARD STOPPED]")
            print("Optimization continues running in background")

if __name__ == "__main__":
    dashboard = LiveDashboard()
    dashboard.run_live(refresh_seconds=30)


