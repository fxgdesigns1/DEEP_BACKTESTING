#!/usr/bin/env python3
"""
OPTIMIZED STRATEGY LAUNCHER
Maximum performance for 32-core system with 64GB RAM and GPU
Real-time progress tracking and results reporting
"""

import os
import sys
import json
import time
import psutil
import subprocess
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class OptimizedStrategyLauncher:
    """Optimized launcher with real-time progress tracking"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.results = {}
        self.progress_lock = threading.Lock()
        
        # Detect system capabilities
        self.cpu_cores = psutil.cpu_count()
        self.ram_gb = round(psutil.virtual_memory().total / (1024**3))
        
        print("=" * 80)
        print("OPTIMIZED STRATEGY LAUNCHER - MAXIMUM PERFORMANCE MODE")
        print("=" * 80)
        print(f"System: {self.cpu_cores} cores | {self.ram_gb}GB RAM")
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()
        
    def optimize_system(self):
        """Optimize system for maximum performance"""
        print("[PHASE 1] SYSTEM OPTIMIZATION")
        print("-" * 80)
        
        # Set high-performance environment variables
        os.environ['OMP_NUM_THREADS'] = str(self.cpu_cores)
        os.environ['NUMEXPR_MAX_THREADS'] = str(self.cpu_cores)
        os.environ['MKL_NUM_THREADS'] = str(self.cpu_cores)
        os.environ['PYTHONUNBUFFERED'] = '1'
        
        # Create results directory
        Path("results").mkdir(exist_ok=True)
        
        print(f"[OK] Optimized for {self.cpu_cores} cores")
        print(f"[OK] Results directory ready")
        print(f"[OK] High-performance mode enabled")
        print()
        
    def run_simulations(self):
        """Run all simulations with real-time progress"""
        print("[PHASE 2] RUNNING STRATEGY SIMULATIONS")
        print("-" * 80)
        
        simulations = [
            {
                'name': 'Advanced Gold Scalping',
                'script': 'advanced_gold_scalping_simulation.py',
                'timeout': 900,
                'icon': '[GOLD]'
            },
            {
                'name': 'Multi-Pair Simulation',
                'script': 'multi_pair_simulation.py',
                'timeout': 1200,
                'icon': '[MULTI]'
            },
            {
                'name': 'Real Data Simulation',
                'script': 'real_data_simulation.py',
                'timeout': 1800,
                'icon': '[DATA]'
            },
            {
                'name': 'Risk Management Simulation',
                'script': 'risk_management_simulation.py',
                'timeout': 900,
                'icon': '[RISK]'
            }
        ]
        
        # Check which files exist
        available_sims = []
        for sim in simulations:
            if os.path.exists(sim['script']):
                available_sims.append(sim)
                print(f"[OK] Found: {sim['name']}")
            else:
                print(f"[MISS] Missing: {sim['name']}")
        
        print(f"\n{len(available_sims)}/{len(simulations)} simulations available")
        print(f"Running {min(4, len(available_sims))} simulations in parallel...\n")
        
        if not available_sims:
            print("ERROR: No simulation scripts found!")
            return
        
        # Run simulations in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self.run_single_simulation, sim): sim 
                for sim in available_sims
            }
            
            # Track progress
            completed = 0
            for future in as_completed(futures):
                sim = futures[future]
                try:
                    result = future.result()
                    completed += 1
                    self.results[sim['name']] = result
                    
                    status_icon = "[SUCCESS]" if result['success'] else "[FAILED]"
                    print(f"\n{status_icon} {sim['icon']} {sim['name']}: {result['status']}")
                    print(f"   Duration: {result['duration']}")
                    print(f"   Progress: {completed}/{len(available_sims)} completed")
                    
                except Exception as e:
                    print(f"\n[ERROR] {sim['icon']} {sim['name']}: FAILED - {e}")
                    completed += 1
        
        print()
        
    def run_single_simulation(self, sim):
        """Run a single simulation and return results"""
        start_time = datetime.now()
        
        try:
            print(f"\n{sim['icon']} Starting {sim['name']}...")
            
            # Run with optimized settings
            result = subprocess.run(
                [sys.executable, sim['script']],
                capture_output=True,
                text=True,
                timeout=sim['timeout'],
                encoding='utf-8',
                errors='replace'
            )
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            success = result.returncode == 0
            
            return {
                'success': success,
                'status': 'SUCCESS' if success else 'FAILED',
                'duration': str(duration),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'return_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            end_time = datetime.now()
            return {
                'success': False,
                'status': 'TIMEOUT',
                'duration': str(end_time - start_time),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'return_code': -1
            }
        except Exception as e:
            end_time = datetime.now()
            return {
                'success': False,
                'status': f'ERROR: {str(e)}',
                'duration': str(end_time - start_time),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'return_code': -1
            }
    
    def analyze_results(self):
        """Analyze all results and find best strategy"""
        print("[PHASE 3] ANALYZING RESULTS")
        print("-" * 80)
        
        # Look for recent result files
        results_dir = Path("results")
        if not results_dir.exists():
            print("No results directory found")
            return
        
        # Get all JSON result files from the last hour
        recent_results = []
        cutoff_time = time.time() - 3600
        
        for json_file in results_dir.rglob("*.json"):
            try:
                if json_file.stat().st_mtime > cutoff_time:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        recent_results.append({
                            'file': json_file.name,
                            'path': str(json_file),
                            'data': data
                        })
            except:
                continue
        
        print(f"Found {len(recent_results)} recent result files\n")
        
        if not recent_results:
            print("No recent results found. Simulations may still be running...")
            return
        
        # Analyze each result
        best_strategy = None
        best_sharpe = -999
        
        for result in recent_results:
            data = result['data']
            
            # Extract key metrics
            if 'best_strategy' in data:
                strategy = data['best_strategy']
                sharpe = strategy.get('sharpe_ratio', 0)
                
                print(f"[RESULT] {result['file']}")
                print(f"   Strategy: {strategy.get('name', 'Unknown')}")
                print(f"   Sharpe Ratio: {sharpe:.2f}")
                print(f"   Win Rate: {strategy.get('win_rate', 0):.1f}%")
                print(f"   Total Return: {strategy.get('total_return', 0):.2f}%")
                print()
                
                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_strategy = {
                        'file': result['file'],
                        'strategy': strategy
                    }
        
        # Report best strategy
        if best_strategy:
            print("=" * 80)
            print(">>> BEST STRATEGY FOUND <<<")
            print("=" * 80)
            strat = best_strategy['strategy']
            print(f"Source: {best_strategy['file']}")
            print(f"Strategy: {strat.get('name', 'Unknown')}")
            print(f"Sharpe Ratio: {strat.get('sharpe_ratio', 0):.2f}")
            print(f"Win Rate: {strat.get('win_rate', 0):.1f}%")
            print(f"Total Return: {strat.get('total_return', 0):.2f}%")
            print(f"Max Drawdown: {strat.get('max_drawdown', 0):.2f}%")
            print(f"Profit Factor: {strat.get('profit_factor', 0):.2f}")
            print()
    
    def generate_report(self):
        """Generate final execution report"""
        print("[PHASE 4] FINAL REPORT")
        print("-" * 80)
        
        end_time = datetime.now()
        total_duration = end_time - self.start_time
        
        successful = sum(1 for r in self.results.values() if r['success'])
        total = len(self.results)
        
        print(f"Total Duration: {total_duration}")
        print(f"Simulations Run: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {total - successful}")
        print(f"Success Rate: {(successful/total*100):.1f}%" if total > 0 else "N/A")
        print()
        
        # System stats
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        
        print(f"Final System State:")
        print(f"  CPU Usage: {cpu:.1f}%")
        print(f"  Memory: {mem.percent:.1f}% ({mem.used/(1024**3):.1f}GB / {mem.total/(1024**3):.1f}GB)")
        print()
        
        # Save report
        report = {
            'execution_time': {
                'start': self.start_time.isoformat(),
                'end': end_time.isoformat(),
                'duration': str(total_duration)
            },
            'system': {
                'cpu_cores': self.cpu_cores,
                'ram_gb': self.ram_gb
            },
            'results': self.results
        }
        
        report_file = f"optimization_report_{end_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"[SAVED] Report saved: {report_file}")
        print()
        
        print("=" * 80)
        print("[COMPLETE] OPTIMIZATION COMPLETE")
        print("=" * 80)
    
    def run(self):
        """Main execution flow"""
        try:
            self.optimize_system()
            self.run_simulations()
            self.analyze_results()
            self.generate_report()
        except KeyboardInterrupt:
            print("\n\n[WARNING] Interrupted by user")
            self.generate_report()
        except Exception as e:
            print(f"\n\n[ERROR] Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    launcher = OptimizedStrategyLauncher()
    launcher.run()

