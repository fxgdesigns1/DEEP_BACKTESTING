"""
OVERNIGHT MONITORING SYSTEM
Checks optimizer progress every 10 minutes and analyzes results when complete
"""

import os
import json
import time
import glob
from datetime import datetime
from pathlib import Path

class OvernightMonitor:
    def __init__(self):
        self.export_dir = Path("H:/My Drive/AI Trading/exported strategies")
        self.log_file = Path("overnight_monitor.log")
        self.status_file = Path("overnight_status.json")
        
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        with open(self.log_file, 'a') as f:
            f.write(log_msg + "\n")
    
    def check_optimizer_progress(self):
        """Check if ultimate_quality_optimizer has completed"""
        # Look for the results directory
        pattern = str(self.export_dir / "ultimate_quality_*")
        dirs = glob.glob(pattern)
        
        if not dirs:
            return {
                'status': 'RUNNING',
                'message': 'No results directory yet - optimizer still processing...',
                'progress': 0
            }
        
        latest_dir = max(dirs, key=os.path.getmtime)
        latest_path = Path(latest_dir)
        
        # Check for results files
        high_quality = latest_path / "high_quality_strategies.json"
        all_results = latest_path / "all_results.json"
        
        if not high_quality.exists() and not all_results.exists():
            return {
                'status': 'RUNNING',
                'message': f'Results directory exists: {latest_path.name}',
                'progress': 25
            }
        
        # Load results
        hq_count = 0
        all_count = 0
        
        if high_quality.exists():
            try:
                with open(high_quality) as f:
                    hq_data = json.load(f)
                    hq_count = len(hq_data)
            except:
                pass
        
        if all_results.exists():
            try:
                with open(all_results) as f:
                    all_data = json.load(f)
                    all_count = len(all_data)
            except:
                pass
        
        # If we have results, it's complete
        if hq_count > 0 or all_count > 0:
            return {
                'status': 'COMPLETE',
                'message': f'Optimization complete! {hq_count} high-quality strategies found',
                'high_quality_count': hq_count,
                'total_count': all_count,
                'results_dir': str(latest_path),
                'progress': 100
            }
        
        return {
            'status': 'RUNNING',
            'message': f'Processing... directory: {latest_path.name}',
            'progress': 50
        }
    
    def analyze_results(self, results_dir):
        """Analyze completed results"""
        self.log("="*80)
        self.log("ANALYZING COMPLETED RESULTS")
        self.log("="*80)
        
        results_path = Path(results_dir)
        
        # Load high quality strategies
        hq_file = results_path / "high_quality_strategies.json"
        if not hq_file.exists():
            self.log("No high quality strategies file found!")
            return
        
        with open(hq_file) as f:
            strategies = json.load(f)
        
        self.log(f"\nTotal High Quality Strategies: {len(strategies)}")
        
        if len(strategies) == 0:
            self.log("\n⚠️  NO STRATEGIES MET THE 4% DRAWDOWN CRITERIA!")
            self.log("Will need to relax criteria or adjust parameters")
            return
        
        # Analyze by timeframe
        by_timeframe = {}
        for strat in strategies:
            tf = strat['timeframe']
            if tf not in by_timeframe:
                by_timeframe[tf] = []
            by_timeframe[tf].append(strat)
        
        self.log("\n" + "="*80)
        self.log("STRATEGIES BY TIMEFRAME")
        self.log("="*80)
        for tf, strats in sorted(by_timeframe.items()):
            self.log(f"\n{tf.upper()}: {len(strats)} strategies")
            # Show top 3
            top_3 = sorted(strats, key=lambda x: x.get('sharpe_ratio', 0), reverse=True)[:3]
            for i, s in enumerate(top_3, 1):
                self.log(f"  #{i}: {s['pair']} | Sharpe: {s.get('sharpe_ratio', 0):.2f} | "
                        f"Return: {s.get('annual_return_%', 0):.1f}% | "
                        f"Win Rate: {s.get('win_rate_%', 0):.1f}% | "
                        f"Max DD: {s.get('max_drawdown_%', 0):.2f}%")
        
        # Find overall best
        self.log("\n" + "="*80)
        self.log("TOP 10 OVERALL STRATEGIES")
        self.log("="*80)
        top_10 = sorted(strategies, key=lambda x: x.get('sharpe_ratio', 0), reverse=True)[:10]
        for i, s in enumerate(top_10, 1):
            self.log(f"\n#{i}: {s['pair']} on {s['timeframe']}")
            self.log(f"   Sharpe: {s.get('sharpe_ratio', 0):.2f}")
            self.log(f"   Annual Return: {s.get('annual_return_%', 0):.1f}%")
            self.log(f"   Win Rate: {s.get('win_rate_%', 0):.1f}%")
            self.log(f"   Max Drawdown: {s.get('max_drawdown_%', 0):.2f}%")
            self.log(f"   Profit Factor: {s.get('profit_factor', 0):.2f}")
            self.log(f"   Total Trades: {s.get('total_trades', 0)}")
        
        # Save wake-up summary
        self.create_wake_up_summary(strategies, results_path)
    
    def create_wake_up_summary(self, strategies, results_path):
        """Create a summary report for when user wakes up"""
        summary = []
        summary.append("="*100)
        summary.append(" "*30 + "OVERNIGHT OPTIMIZATION COMPLETE!")
        summary.append("="*100)
        summary.append(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append(f"Results Directory: {results_path}")
        summary.append(f"\nTotal High Quality Strategies Found: {len(strategies)}")
        
        if len(strategies) == 0:
            summary.append("\n⚠️  NO STRATEGIES MET THE 4% MAX DRAWDOWN CRITERIA")
            summary.append("\nRECOMMENDATIONS:")
            summary.append("1. Relax max drawdown to 5% or 6%")
            summary.append("2. Lower minimum win rate to 55%")
            summary.append("3. Test with longer holding periods")
            summary.append("4. Consider different quality filters")
        else:
            # Stats
            timeframes = {}
            for s in strategies:
                tf = s['timeframe']
                timeframes[tf] = timeframes.get(tf, 0) + 1
            
            summary.append("\nSTRATEGIES BY TIMEFRAME:")
            for tf, count in sorted(timeframes.items()):
                summary.append(f"  {tf}: {count} strategies")
            
            # Top 5
            summary.append("\n" + "="*100)
            summary.append("TOP 5 STRATEGIES TO DEPLOY")
            summary.append("="*100)
            top_5 = sorted(strategies, key=lambda x: x.get('sharpe_ratio', 0), reverse=True)[:5]
            for i, s in enumerate(top_5, 1):
                summary.append(f"\n#{i}: {s['pair']} on {s['timeframe']}")
                summary.append(f"   Sharpe Ratio: {s.get('sharpe_ratio', 0):.2f}")
                summary.append(f"   Annual Return: {s.get('annual_return_%', 0):.1f}%")
                summary.append(f"   Win Rate: {s.get('win_rate_%', 0):.1f}%")
                summary.append(f"   Max Drawdown: {s.get('max_drawdown_%', 0):.2f}%")
                summary.append(f"   Profit Factor: {s.get('profit_factor', 0):.2f}")
                summary.append(f"   Total Trades: {s.get('total_trades', 0)}")
                summary.append(f"   Avg Win: {s.get('avg_win_%', 0):.2f}%")
                summary.append(f"   Avg Loss: {s.get('avg_loss_%', 0):.2f}%")
            
            summary.append("\n" + "="*100)
            summary.append("NEXT STEPS")
            summary.append("="*100)
            summary.append("1. Review the top strategies above")
            summary.append("2. Deploy to demo accounts for live testing")
            summary.append("3. Monitor performance for 1-2 weeks")
            summary.append("4. Scale up capital on proven performers")
        
        summary.append("\n" + "="*100)
        
        # Save to file
        summary_text = "\n".join(summary)
        summary_file = Path("WAKE_UP_SUMMARY.txt")
        with open(summary_file, 'w') as f:
            f.write(summary_text)
        
        self.log("\n" + summary_text)
        self.log(f"\nSummary saved to: {summary_file}")
    
    def run_overnight(self, check_interval_minutes=10, max_hours=12):
        """Run overnight monitoring"""
        self.log("="*80)
        self.log("OVERNIGHT MONITORING STARTED")
        self.log("="*80)
        self.log(f"Check interval: {check_interval_minutes} minutes")
        self.log(f"Max runtime: {max_hours} hours")
        self.log(f"Will monitor ultimate_quality_optimizer.py")
        self.log("")
        
        start_time = time.time()
        max_runtime = max_hours * 3600
        check_interval = check_interval_minutes * 60
        
        check_count = 0
        
        while True:
            check_count += 1
            elapsed = time.time() - start_time
            
            if elapsed > max_runtime:
                self.log("Max runtime reached - stopping monitor")
                break
            
            # Check progress
            status = self.check_optimizer_progress()
            
            self.log(f"\nCheck #{check_count} (Elapsed: {elapsed/3600:.1f}h)")
            self.log(f"Status: {status['status']}")
            self.log(f"Progress: ~{status['progress']}%")
            self.log(f"Message: {status['message']}")
            
            # Save status
            status['check_count'] = check_count
            status['elapsed_hours'] = elapsed / 3600
            status['timestamp'] = datetime.now().isoformat()
            
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
            
            # If complete, analyze and exit
            if status['status'] == 'COMPLETE':
                self.log("\n🎉 OPTIMIZATION COMPLETE!")
                self.analyze_results(status['results_dir'])
                self.log("\n✅ ANALYSIS COMPLETE - CHECK WAKE_UP_SUMMARY.txt")
                break
            
            # Wait for next check
            self.log(f"Next check in {check_interval_minutes} minutes...")
            time.sleep(check_interval)

if __name__ == "__main__":
    monitor = OvernightMonitor()
    monitor.run_overnight(check_interval_minutes=10, max_hours=12)



