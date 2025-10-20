#!/usr/bin/env python3
"""
HIGH-PERFORMANCE SIMULATION EXECUTOR
Optimized for AMD 5950X, RTX 3080, 64GB RAM, NVMe Storage
Intelligent resource management to maximize performance without overload
"""

import os
import sys
import json
import logging
import subprocess
import time
import psutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('high_performance_simulation_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HighPerformanceSimulationExecutor:
    """High-performance simulation executor optimized for powerful hardware"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.system_specs = self._get_system_specs()
        self.optimal_workers = self._calculate_optimal_workers()
        self.results = {
            'execution_start': self.start_time.isoformat(),
            'system_specs': self.system_specs,
            'optimization_settings': {},
            'phases': {},
            'simulations': {},
            'validation': {},
            'final_report': {}
        }
        
        logger.info("HIGH-PERFORMANCE SIMULATION EXECUTOR INITIALIZED")
        logger.info(f"System: {self.system_specs['cpu_cores']} cores | {self.system_specs['ram_gb']}GB RAM | GPU: {self.system_specs['gpu_available']}")
        logger.info(f"Optimal Workers: {self.optimal_workers['cpu_workers']} CPU | GPU: {self.optimal_workers['gpu_enabled']}")
        
    def _get_system_specs(self):
        """Get system specifications"""
        try:
            # CPU info
            cpu_count = mp.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory info
            memory = psutil.virtual_memory()
            ram_gb = round(memory.total / (1024**3))
            
            # GPU detection (simplified)
            gpu_available = False
            try:
                import torch
                gpu_available = torch.cuda.is_available()
            except:
                pass
            
            return {
                'cpu_cores': cpu_count,
                'cpu_frequency': cpu_freq.max if cpu_freq else 'Unknown',
                'ram_gb': ram_gb,
                'gpu_available': gpu_available,
                'platform': sys.platform,
                'python_version': sys.version.split()[0]
            }
        except Exception as e:
            logger.warning(f"Could not detect system specs: {e}")
            return {
                'cpu_cores': 16,  # Default for 5950X
                'ram_gb': 64,
                'gpu_available': True,
                'platform': 'win32'
            }
    
    def _calculate_optimal_workers(self):
        """Calculate optimal worker configuration for your hardware"""
        cpu_cores = self.system_specs['cpu_cores']
        ram_gb = self.system_specs['ram_gb']
        
        # DOUBLED USAGE approach for 5950X (16 cores, 32 threads)
        # Use 95% of logical cores for maximum performance
        cpu_workers = max(16, int(cpu_cores * 0.95))
        
        # For 64GB RAM, we can handle large datasets with maximum usage
        memory_optimized = True if ram_gb >= 32 else False
        
        # GPU utilization (if available)
        gpu_enabled = self.system_specs['gpu_available']
        
        return {
            'cpu_workers': cpu_workers,
            'memory_optimized': memory_optimized,
            'gpu_enabled': gpu_enabled,
            'parallel_simulations': 4  # Fixed 4 parallel simulations as requested
        }
    
    def _monitor_system_resources(self):
        """Monitor system resources during execution"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        if cpu_percent > 90:
            logger.warning(f"⚠️ High CPU usage: {cpu_percent}%")
        if memory_percent > 85:
            logger.warning(f"⚠️ High memory usage: {memory_percent}%")
            
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'memory_available_gb': round(memory.available / (1024**3), 2)
        }
    
    def execute_high_performance_plan(self):
        """Execute optimized simulation plan"""
        logger.info("STARTING HIGH-PERFORMANCE SIMULATION EXECUTION")
        logger.info("=" * 80)
        
        try:
            # Phase 1: System Optimization
            self._phase_1_system_optimization()
            
            # Phase 2: Parallel Simulation Execution
            self._phase_2_parallel_execution()
            
            # Phase 3: Results Analysis
            self._phase_3_results_analysis()
            
            # Phase 4: Final Report
            self._phase_4_final_report()
            
            logger.info("HIGH-PERFORMANCE SIMULATION PLAN COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            logger.error(f"❌ Execution failed: {str(e)}")
            raise
    
    def _phase_1_system_optimization(self):
        """Phase 1: System Optimization & Preparation"""
        logger.info("PHASE 1: SYSTEM OPTIMIZATION & PREPARATION")
        logger.info("-" * 50)
        
        phase_start = datetime.now()
        
        # Monitor initial system state
        initial_resources = self._monitor_system_resources()
        logger.info(f"Initial CPU: {initial_resources['cpu_percent']}% | Memory: {initial_resources['memory_percent']}%")
        
        # Optimize simulation scripts for high performance
        optimization_settings = {
            'max_workers': self.optimal_workers['cpu_workers'],
            'parallel_simulations': self.optimal_workers['parallel_simulations'],
            'memory_optimized': self.optimal_workers['memory_optimized'],
            'gpu_enabled': self.optimal_workers['gpu_enabled'],
            'timeout_multiplier': 2.0  # Longer timeouts for complex simulations
        }
        
        # Check critical files and prepare environment
        critical_files = [
            'advanced_gold_scalping_simulation.py',
            'real_data_simulation.py', 
            'multi_pair_simulation.py',
            'risk_management_simulation.py'
        ]
        
        missing_files = [f for f in critical_files if not os.path.exists(f)]
        if missing_files:
            logger.error(f"❌ Missing files: {missing_files}")
            verification_status = "FAILED"
        else:
            logger.info("✅ All simulation files present")
            verification_status = "PASSED"
        
        # Prepare results directory with high-performance settings
        results_dir = Path("results")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Set environment variables for optimal performance
        os.environ['OMP_NUM_THREADS'] = str(self.optimal_workers['cpu_workers'])
        os.environ['NUMEXPR_MAX_THREADS'] = str(self.optimal_workers['cpu_workers'])
        
        phase_end = datetime.now()
        self.results['phases']['phase_1'] = {
            'name': 'System Optimization & Preparation',
            'start': phase_start.isoformat(),
            'end': phase_end.isoformat(),
            'duration': str(phase_end - phase_start),
            'verification_status': verification_status,
            'optimization_settings': optimization_settings,
            'initial_resources': initial_resources
        }
        
        self.results['optimization_settings'] = optimization_settings
        
        logger.info(f"✅ Phase 1 completed in {phase_end - phase_start}")
    
    def _phase_2_parallel_execution(self):
        """Phase 2: Parallel Simulation Execution"""
        logger.info("🚀 PHASE 2: PARALLEL SIMULATION EXECUTION")
        logger.info("-" * 50)
        
        phase_start = datetime.now()
        
        # Define simulations with optimized timeouts for your hardware
        simulations = [
            {
                'name': 'Advanced Gold Scalping',
                'script': 'advanced_gold_scalping_simulation.py',
                'priority': 1,
                'description': 'Specialized XAU_USD simulation with advanced parameters',
                'timeout': 900,  # 15 minutes (increased for complex scenarios)
                'expected_scenarios': 1200
            },
            {
                'name': 'Multi-Pair Simulation', 
                'script': 'multi_pair_simulation.py',
                'priority': 2,
                'description': 'Comprehensive testing across 8 currency pairs',
                'timeout': 1200,  # 20 minutes
                'expected_scenarios': 800
            },
            {
                'name': 'Real Data Simulation',
                'script': 'real_data_simulation.py',
                'priority': 3,
                'description': 'Uses proven 36,762-experiment dataset',
                'timeout': 1800,  # 30 minutes (longest for comprehensive testing)
                'expected_scenarios': 2000
            },
            {
                'name': 'Risk Management Simulation',
                'script': 'risk_management_simulation.py',
                'priority': 4,
                'description': 'Professional risk modeling and testing',
                'timeout': 900,  # 15 minutes
                'expected_scenarios': 400
            }
        ]
        
        # Execute simulations with intelligent parallelization
        max_parallel = self.optimal_workers['parallel_simulations']
        
        if max_parallel > 1:
            logger.info(f"🔄 Executing up to {max_parallel} simulations in parallel")
            self._execute_parallel_simulations(simulations, max_parallel)
        else:
            logger.info("🔄 Executing simulations sequentially for optimal resource usage")
            self._execute_sequential_simulations(simulations)
        
        phase_end = datetime.now()
        successful_sims = len([s for s in self.results['simulations'].values() if s['status'] == 'SUCCESS'])
        
        self.results['phases']['phase_2'] = {
            'name': 'Parallel Simulation Execution',
            'start': phase_start.isoformat(),
            'end': phase_end.isoformat(),
            'duration': str(phase_end - phase_start),
            'simulations_executed': len(simulations),
            'successful_simulations': successful_sims,
            'parallel_execution': max_parallel > 1
        }
        
        logger.info(f"✅ Phase 2 completed in {phase_end - phase_start}")
    
    def _execute_parallel_simulations(self, simulations, max_parallel):
        """Execute simulations in parallel with live progress monitoring"""
        logger.info(f"EXECUTING {max_parallel} SIMULATIONS IN PARALLEL")
        
        # Progress tracking
        self.progress = {'completed': 0, 'total': len(simulations), 'running': 0}
        
        # Start live monitor thread
        monitor_thread = threading.Thread(target=self._live_monitor, daemon=True)
        monitor_thread.start()
        
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            # Submit all simulations at once for true parallel execution
            futures = {executor.submit(self._execute_single_simulation_with_progress, sim, i): sim 
                      for i, sim in enumerate(simulations)}
            
            # Wait for all to complete with progress updates
            for future in futures:
                try:
                    future.result()
                    self.progress['completed'] += 1
                    logger.info(f"LIVE PROGRESS: {self.progress['completed']}/{self.progress['total']} completed")
                except Exception as e:
                    logger.error(f"Simulation failed: {e}")
    
    def _live_monitor(self):
        """Live progress monitor showing real-time stats"""
        start_time = datetime.now()
        while self.progress['completed'] < self.progress['total']:
            elapsed = datetime.now() - start_time
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            logger.info(f"LIVE STATS: {self.progress['completed']}/{self.progress['total']} done | CPU: {cpu_percent}% | RAM: {memory.percent}% | Time: {elapsed}")
            time.sleep(15)  # Update every 15 seconds
    
    def _execute_single_simulation_with_progress(self, sim, index):
        """Execute simulation with progress tracking"""
        self.progress['running'] += 1
        logger.info(f"[{index+1}] EXECUTING {sim['name']}...")
        sim_start = datetime.now()
        
        # Monitor resources before starting
        pre_resources = self._monitor_system_resources()
        logger.info(f"[{index+1}] Pre-execution: CPU {pre_resources['cpu_percent']}% | RAM {pre_resources['memory_percent']}%")
        
        try:
            # Run simulation with optimized environment
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            env['OMP_NUM_THREADS'] = str(self.optimal_workers['cpu_workers'])
            env['NUMEXPR_MAX_THREADS'] = str(self.optimal_workers['cpu_workers'])
            
            result = subprocess.run(
                [sys.executable, sim['script']],
                capture_output=True,
                text=True,
                timeout=sim.get('timeout', 1800),
                env=env
            )
            
            # Monitor resources after completion
            post_resources = self._monitor_system_resources()
            
            if result.returncode == 0:
                logger.info(f"[{index+1}] SUCCESS: {sim['name']} completed successfully")
                status = "SUCCESS"
            else:
                logger.warning(f"[{index+1}] WARNING: {sim['name']} completed with issues")
                status = "ISSUES"
                
        except subprocess.TimeoutExpired:
            logger.error(f"[{index+1}] TIMEOUT: {sim['name']} timed out")
            status = "TIMEOUT"
            sim_end = datetime.now()
            result = type('obj', (object,), {'returncode': -1, 'stdout': '', 'stderr': 'Timeout'})
            post_resources = self._monitor_system_resources()
        except Exception as e:
            logger.error(f"[{index+1}] ERROR: {sim['name']} failed: {e}")
            status = "ERROR"
            sim_end = datetime.now()
            result = type('obj', (object,), {'returncode': -1, 'stdout': '', 'stderr': str(e)})
            post_resources = self._monitor_system_resources()
        
        sim_end = datetime.now()
        self.progress['running'] -= 1
        
        # Store results
        self.results['simulations'][sim['name']] = {
            'status': status,
            'start_time': sim_start.isoformat(),
            'end_time': sim_end.isoformat(),
            'duration': str(sim_end - sim_start),
            'pre_resources': pre_resources,
            'post_resources': post_resources,
            'stdout': result.stdout[-2000:] if result.stdout else '',
            'stderr': result.stderr[-1000:] if result.stderr else ''
        }
        
        logger.info(f"[{index+1}] COMPLETED: {sim['name']} in {sim_end - sim_start}")
        logger.info(f"[{index+1}] Post-execution: CPU {post_resources['cpu_percent']}% | RAM {post_resources['memory_percent']}%")
    
    def _execute_sequential_simulations(self, simulations):
        """Execute simulations sequentially with resource monitoring"""
        for sim in simulations:
            self._execute_single_simulation(sim)
    
    def _execute_single_simulation(self, sim):
        """Execute a single simulation with monitoring"""
        logger.info(f"EXECUTING {sim['name']}...")
        sim_start = datetime.now()
        
        # Monitor resources before starting
        pre_resources = self._monitor_system_resources()
        logger.info(f"Pre-execution: CPU {pre_resources['cpu_percent']}% | RAM {pre_resources['memory_percent']}%")
        
        try:
            # Run simulation with optimized environment
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'  # Ensure real-time output
            
            result = subprocess.run(
                [sys.executable, sim['script']], 
                capture_output=True, 
                text=True, 
                timeout=sim['timeout'],
                env=env
            )
            
            sim_end = datetime.now()
            
            # Monitor resources after completion
            post_resources = self._monitor_system_resources()
            
            if result.returncode == 0:
                logger.info(f"SUCCESS: {sim['name']} completed successfully")
                status = "SUCCESS"
            else:
                logger.warning(f"WARNING: {sim['name']} completed with issues")
                status = "ISSUES"
                
        except subprocess.TimeoutExpired:
            logger.error(f"TIMEOUT: {sim['name']} timed out after {sim['timeout']} seconds")
            status = "TIMEOUT"
            sim_end = datetime.now()
            result = type('obj', (object,), {'returncode': -1, 'stdout': '', 'stderr': 'Timeout'})
            post_resources = self._monitor_system_resources()
        except Exception as e:
            logger.error(f"❌ {sim['name']} failed: {e}")
            status = "FAILED"
            sim_end = datetime.now()
            result = type('obj', (object,), {'returncode': -1, 'stdout': '', 'stderr': str(e)})
            post_resources = self._monitor_system_resources()
        
        # Store results
        self.results['simulations'][sim['name']] = {
            'script': sim['script'],
            'description': sim['description'],
            'priority': sim['priority'],
            'start': sim_start.isoformat(),
            'end': sim_end.isoformat(),
            'duration': str(sim_end - sim_start),
            'status': status,
            'return_code': result.returncode,
            'expected_scenarios': sim['expected_scenarios'],
            'pre_resources': pre_resources,
            'post_resources': post_resources,
            'stdout': result.stdout[-2000:] if result.stdout else '',  # Last 2000 chars
            'stderr': result.stderr[-1000:] if result.stderr else ''   # Last 1000 chars
        }
        
        logger.info(f"COMPLETED: {sim['name']} completed in {sim_end - sim_start}")
        logger.info(f"Post-execution: CPU {post_resources['cpu_percent']}% | RAM {post_resources['memory_percent']}%")
    
    def _phase_3_results_analysis(self):
        """Phase 3: High-Performance Results Analysis"""
        logger.info("📊 PHASE 3: HIGH-PERFORMANCE RESULTS ANALYSIS")
        logger.info("-" * 50)
        
        phase_start = datetime.now()
        
        # Analyze results with parallel processing
        results_dir = Path("results")
        if results_dir.exists():
            result_files = list(results_dir.rglob("*.json"))
            logger.info(f"Found {len(result_files)} result files")
            
            # Analyze recent results (last 2 hours for high-performance execution)
            recent_files = []
            for f in result_files:
                try:
                    if (datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)).total_seconds() < 7200:
                        recent_files.append(f)
                except:
                    continue
            
            logger.info(f"Found {len(recent_files)} recent result files")
            
            # Parallel analysis of results
            with ThreadPoolExecutor(max_workers=min(4, self.optimal_workers['cpu_workers'] // 2)) as executor:
                futures = [executor.submit(self._analyze_result_file, f) for f in recent_files]
                recent_results = [f.result() for f in futures if f.result()]
            
            self.results['validation'] = {
                'total_result_files': len(result_files),
                'recent_result_files': len(recent_files),
                'recent_results_analysis': recent_results,
                'results_analysis': 'COMPLETED',
                'analysis_method': 'PARALLEL'
            }
        else:
            logger.warning("No results directory found")
            self.results['validation'] = {
                'results_analysis': 'NO_RESULTS_DIR'
            }
        
        phase_end = datetime.now()
        self.results['phases']['phase_3'] = {
            'name': 'High-Performance Results Analysis',
            'start': phase_start.isoformat(),
            'end': phase_end.isoformat(),
            'duration': str(phase_end - phase_start)
        }
        
        logger.info(f"✅ Phase 3 completed in {phase_end - phase_start}")
    
    def _analyze_result_file(self, file_path):
        """Analyze a single result file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return {
                    'file': str(file_path),
                    'type': data.get('simulation_type', 'Unknown'),
                    'scenarios': data.get('total_scenarios', 0),
                    'successful': data.get('successful_scenarios', 0),
                    'execution_time': data.get('execution_time', 'Unknown'),
                    'best_strategy': data.get('best_strategy', {})
                }
        except Exception as e:
            logger.warning(f"Could not analyze {file_path}: {e}")
            return None
    
    def _phase_4_final_report(self):
        """Phase 4: High-Performance Final Report"""
        logger.info("📋 PHASE 4: HIGH-PERFORMANCE FINAL REPORT")
        logger.info("-" * 50)
        
        phase_start = datetime.now()
        
        # Generate comprehensive final report
        end_time = datetime.now()
        total_duration = end_time - self.start_time
        
        successful_sims = len([s for s in self.results['simulations'].values() if s['status'] == 'SUCCESS'])
        total_sims = len(self.results['simulations'])
        
        # Calculate performance metrics
        total_scenarios = sum(s.get('expected_scenarios', 0) for s in self.results['simulations'].values() if s['status'] == 'SUCCESS')
        actual_scenarios = self._get_total_scenarios_tested()
        
        # System performance summary
        final_resources = self._monitor_system_resources()
        
        self.results['final_report'] = {
            'execution_summary': {
                'total_duration': str(total_duration),
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'phases_completed': len(self.results['phases']),
                'simulations_executed': total_sims,
                'hardware_optimized': True
            },
            'success_metrics': {
                'successful_simulations': successful_sims,
                'total_simulations': total_sims,
                'success_rate': (successful_sims / total_sims * 100) if total_sims > 0 else 0
            },
            'performance_summary': {
                'expected_scenarios': total_scenarios,
                'actual_scenarios': actual_scenarios,
                'scenario_efficiency': (actual_scenarios / total_scenarios * 100) if total_scenarios > 0 else 0,
                'best_performing_simulation': self._get_best_performing_simulation(),
                'system_health': self._assess_system_health(),
                'resource_utilization': final_resources
            },
            'hardware_utilization': {
                'cpu_workers_used': self.optimal_workers['cpu_workers'],
                'parallel_execution': self.results['phases']['phase_2'].get('parallel_execution', False),
                'memory_optimized': self.optimal_workers['memory_optimized'],
                'gpu_utilized': self.optimal_workers['gpu_enabled']
            }
        }
        
        # Save comprehensive report
        report_path = Path(f"high_performance_simulation_report_{end_time.strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        phase_end = datetime.now()
        self.results['phases']['phase_4'] = {
            'name': 'High-Performance Final Report',
            'start': phase_start.isoformat(),
            'end': phase_end.isoformat(),
            'duration': str(phase_end - phase_start),
            'report_path': str(report_path)
        }
        
        logger.info(f"✅ Phase 4 completed in {phase_end - phase_start}")
        logger.info(f"📋 High-performance report saved to: {report_path}")
    
    def _get_best_performing_simulation(self):
        """Get the best performing simulation"""
        best_sim = None
        for name, sim in self.results['simulations'].items():
            if sim['status'] == 'SUCCESS' and (not best_sim or sim['priority'] < best_sim['priority']):
                best_sim = name
        return best_sim
    
    def _get_total_scenarios_tested(self):
        """Get total scenarios tested across all simulations"""
        total = 0
        for analysis in self.results['validation'].get('recent_results_analysis', []):
            total += analysis.get('scenarios', 0)
        return total
    
    def _assess_system_health(self):
        """Assess overall system health"""
        successful_sims = len([s for s in self.results['simulations'].values() if s['status'] == 'SUCCESS'])
        total_sims = len(self.results['simulations'])
        
        if successful_sims >= total_sims * 0.9:
            return 'EXCELLENT'
        elif successful_sims >= total_sims * 0.75:
            return 'GOOD'
        elif successful_sims >= total_sims * 0.5:
            return 'FAIR'
        else:
            return 'NEEDS_ATTENTION'
    
    def print_final_summary(self):
        """Print final execution summary"""
        logger.info("\n" + "=" * 80)
        logger.info("🎉 HIGH-PERFORMANCE SIMULATION EXECUTION COMPLETE")
        logger.info("=" * 80)
        
        final_report = self.results['final_report']
        
        logger.info(f"⏱️  Total Execution Time: {final_report['execution_summary']['total_duration']}")
        logger.info(f"📊 Simulations Executed: {final_report['execution_summary']['simulations_executed']}")
        logger.info(f"✅ Success Rate: {final_report['success_metrics']['success_rate']:.1f}%")
        logger.info(f"🎯 System Health: {final_report['performance_summary']['system_health']}")
        logger.info(f"⚡ Hardware Optimized: {final_report['execution_summary']['hardware_optimized']}")
        
        # Performance metrics
        logger.info(f"\n🚀 PERFORMANCE METRICS:")
        logger.info(f"  📈 Expected Scenarios: {final_report['performance_summary']['expected_scenarios']:,}")
        logger.info(f"  📊 Actual Scenarios: {final_report['performance_summary']['actual_scenarios']:,}")
        logger.info(f"  🎯 Scenario Efficiency: {final_report['performance_summary']['scenario_efficiency']:.1f}%")
        
        # Hardware utilization
        hw_util = final_report['hardware_utilization']
        logger.info(f"\n💻 HARDWARE UTILIZATION:")
        logger.info(f"  🔧 CPU Workers: {hw_util['cpu_workers_used']}")
        logger.info(f"  🔄 Parallel Execution: {hw_util['parallel_execution']}")
        logger.info(f"  🧠 Memory Optimized: {hw_util['memory_optimized']}")
        logger.info(f"  🎮 GPU Utilized: {hw_util['gpu_utilized']}")
        
        logger.info(f"\n📋 Detailed Report: {self.results['phases']['phase_4']['report_path']}")
        
        # Print simulation results
        logger.info(f"\n🎯 SIMULATION RESULTS:")
        for name, sim in self.results['simulations'].items():
            status_icon = "✅" if sim['status'] == 'SUCCESS' else "⚠️" if sim['status'] == 'ISSUES' else "❌"
            logger.info(f"  {status_icon} {name}: {sim['status']} ({sim['duration']})")
            if 'expected_scenarios' in sim:
                logger.info(f"      📊 Expected Scenarios: {sim['expected_scenarios']:,}")
        
        # Print validation summary
        if 'recent_results_analysis' in self.results['validation']:
            logger.info(f"\n📊 RECENT SIMULATION RESULTS:")
            for result in self.results['validation']['recent_results_analysis']:
                logger.info(f"  📁 {Path(result['file']).name}: {result['successful']}/{result['scenarios']} scenarios successful")

    def run_monte_carlo_analysis(self, results_dir: str = "backtesting_output", max_files: int = None):
        """
        Run Monte Carlo pattern analysis on backtest results
        This is an optional post-processing step for deep strategy validation
        """
        logger.info("\n" + "=" * 80)
        logger.info("🎲 MONTE CARLO PATTERN ANALYSIS")
        logger.info("=" * 80)
        
        try:
            # Import MC modules
            from monte_carlo_analyzer import MonteCarloAnalyzer
            from mc_patterns_report_generator import MCPatternsReportGenerator
            
            # Initialize analyzers
            analyzer = MonteCarloAnalyzer(output_dir="monte_carlo_reports")
            report_gen = MCPatternsReportGenerator(output_dir="monte_carlo_reports")
            
            logger.info(f"Analyzing backtest results in: {results_dir}")
            
            # Run analysis on directory
            reports = analyzer.analyze_directory(
                results_dir,
                pattern="*.json",
                runs=1000,
                block=10,
                window=20,
                max_files=max_files
            )
            
            logger.info(f"Generated {len(reports)} MC analysis reports")
            
            # Generate HTML reports
            html_count = 0
            for report in reports:
                try:
                    report_gen.generate_html_report(report)
                    html_count += 1
                except Exception as e:
                    logger.warning(f"Failed to generate HTML for {report.get('run_id')}: {e}")
            
            logger.info(f"Generated {html_count} HTML reports")
            
            # Store in results
            self.results['monte_carlo'] = {
                'status': 'SUCCESS',
                'reports_generated': len(reports),
                'html_reports': html_count,
                'output_dir': 'monte_carlo_reports'
            }
            
            logger.info("✅ Monte Carlo analysis complete")
            logger.info("=" * 80)
            
            return reports
            
        except ImportError:
            logger.warning("Monte Carlo modules not found. Skipping MC analysis.")
            logger.warning("To enable: Ensure monte_carlo_patterns.py and related files exist.")
            return None
        except Exception as e:
            logger.error(f"Monte Carlo analysis failed: {e}", exc_info=True)
            return None

def main():
    """Main execution function"""
    executor = HighPerformanceSimulationExecutor()
    executor.execute_high_performance_plan()
    executor.print_final_summary()
    
    # Optional: Run Monte Carlo analysis on results
    # Uncomment to enable automatic MC analysis after simulations
    # executor.run_monte_carlo_analysis(results_dir="backtesting_output", max_files=10)

if __name__ == "__main__":
    main()
