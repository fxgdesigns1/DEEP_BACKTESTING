"""
OVERNIGHT FUTURES OPTIMIZATION - CLEAN VERSION
Runs complete optimization while you sleep - NO EMOJIS
"""

import subprocess
import time
from datetime import datetime
from pathlib import Path
import json

class OvernightOptimizer:
    def __init__(self):
        self.start_time = datetime.now()
        self.log_file = Path("overnight_optimization.log")
        self.status_file = Path("overnight_status.json")
    
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_msg + "\n")
    
    def update_status(self, phase, status, details=""):
        """Update status file"""
        status_data = {
            'phase': phase,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'elapsed_minutes': (datetime.now() - self.start_time).total_seconds() / 60
        }
        with open(self.status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
    
    def run_command(self, command, phase_name):
        """Run a command and log output"""
        self.log(f"\n{'='*80}")
        self.log(f"PHASE: {phase_name}")
        self.log(f"Command: {command}")
        self.log(f"{'='*80}")
        
        self.update_status(phase_name, 'running')
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=7200  # 2 hour timeout per phase
            )
            
            self.log(f"\nOutput:\n{result.stdout}")
            if result.stderr:
                self.log(f"\nErrors:\n{result.stderr}")
            
            if result.returncode == 0:
                self.log(f"\n[OK] {phase_name} completed successfully!")
                self.update_status(phase_name, 'completed')
                return True
            else:
                self.log(f"\n[ERROR] {phase_name} failed with code {result.returncode}")
                self.update_status(phase_name, 'failed', result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            self.log(f"\n[TIMEOUT] {phase_name} timed out after 2 hours")
            self.update_status(phase_name, 'timeout')
            return False
        except Exception as e:
            self.log(f"\n[ERROR] {phase_name} error: {e}")
            self.update_status(phase_name, 'error', str(e))
            return False
    
    def run_overnight(self):
        """Run the complete overnight optimization"""
        self.log("\n" + "="*80)
        self.log(" "*15 + "OVERNIGHT FUTURES OPTIMIZATION")
        self.log(" "*10 + "World-Class Autonomous Trading System")
        self.log("="*80)
        self.log(f"\nStart Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"Log File: {self.log_file}")
        self.log(f"Status File: {self.status_file}")
        self.log("\n" + "="*80)
        
        # Phase 1: Download Data
        phase1_success = self.run_command(
            "python efficient_futures_downloader.py",
            "PHASE 1: Data Download"
        )
        
        if not phase1_success:
            self.log("\n[ERROR] Data download failed - cannot continue")
            return
        
        time.sleep(5)  # Brief pause
        
        # Phase 2: Comprehensive Optimization
        phase2_success = self.run_command(
            "python comprehensive_futures_optimizer.py",
            "PHASE 2: Comprehensive Optimization"
        )
        
        if not phase2_success:
            self.log("\n[WARNING] Optimization had issues but may have partial results")
        
        # Final summary
        end_time = datetime.now()
        elapsed = (end_time - self.start_time).total_seconds() / 60
        
        self.log("\n" + "="*80)
        self.log(" "*20 + "OVERNIGHT OPTIMIZATION COMPLETE")
        self.log("="*80)
        self.log(f"\nStart Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"Total Time: {elapsed:.1f} minutes ({elapsed/60:.1f} hours)")
        
        # Check for results
        results_dirs = list(Path("H:/My Drive/AI Trading/exported strategies").glob("futures_optimization_*"))
        if results_dirs:
            latest = max(results_dirs, key=lambda p: p.stat().st_mtime)
            self.log(f"\n[RESULTS] Results Directory: {latest}")
            
            # Check for key files
            report_file = latest / "OPTIMIZATION_REPORT.md"
            if report_file.exists():
                self.log(f"[REPORT] Report: {report_file}")
                self.log("\n[OK] All results generated successfully!")
            else:
                self.log("\n[WARNING] Report file not found - check results manually")
        else:
            self.log("\n[ERROR] No results directory found")
        
        self.log("\n" + "="*80)
        self.log("Good morning! Check the results!")
        self.log("="*80)
        
        self.update_status("COMPLETE", "finished", f"Total time: {elapsed:.1f} minutes")

if __name__ == "__main__":
    print("\n" + "="*80)
    print(" "*10 + "STARTING OVERNIGHT FUTURES OPTIMIZATION")
    print(" "*15 + "(This will run for several hours)")
    print("="*80)
    print("\nWhat will happen:")
    print("1. Download 3 years of ES, NQ, GC futures data")
    print("2. Test 5 different strategies (EMA, RSI, MACD, BB, ATR)")
    print("3. Test all timeframes (5m, 15m, 30m, 1h, 4h)")
    print("4. Test each instrument individually")
    print("5. Generate comprehensive reports")
    print("\nEstimated time: 2-4 hours")
    print("\nYou can check progress in:")
    print("  - overnight_optimization.log")
    print("  - overnight_status.json")
    print("\n" + "="*80)
    print("\n>>> Starting automatically in 3 seconds...")
    time.sleep(3)
    
    optimizer = OvernightOptimizer()
    optimizer.run_overnight()
    
    print("\n[OK] OPTIMIZATION COMPLETE! Check overnight_optimization.log for details.")






