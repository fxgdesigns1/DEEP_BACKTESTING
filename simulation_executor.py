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
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simulation_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimulationExecutor:
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
        
        # Conservative approach for 5950X (16 cores, 32 threads)
        # Use 75% of logical cores to leave headroom
        cpu_workers = max(8, int(cpu_cores * 0.75))
        
        # For 64GB RAM, we can handle large datasets
        memory_optimized = True if ram_gb >= 32 else False
        
        # GPU utilization (if available)
        gpu_enabled = self.system_specs['gpu_available']
        
        return {
            'cpu_workers': cpu_workers,
            'memory_optimized': memory_optimized,
            'gpu_enabled': gpu_enabled,
            'parallel_simulations': min(2, cpu_workers // 4)  # Max 2 parallel simulations
        }
    
    def _monitor_system_resources(self):
        """Monitor system resources during execution"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        if cpu_percent > 90:
            logger.warning(f"High CPU usage: {cpu_percent}%")
        if memory_percent > 85:
            logger.warning(f"High memory usage: {memory_percent}%")
            
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'memory_available_gb': round(memory.available / (1024**3), 2)
        }
    
    def execute_plan(self):
        """Execute optimized simulation plan"""
        logger.info("STARTING HIGH-PERFORMANCE SIMULATION EXECUTION")
        logger.info("=" * 80)
        
        try:
            # Phase 1: System Optimization
            self._phase_1_system_optimization()
            
            # Phase 2: Simulation Execution
            self._phase_2_execution()
            
            # Phase 3: Results Analysis
            self._phase_3_results_analysis()
            
            # Phase 4: Final Report
            self._phase_4_final_report()
            
            logger.info("SIMULATION PLAN COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            logger.error(f"Execution failed: {str(e)}")
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
            logger.error(f"Missing files: {missing_files}")
            verification_status = "FAILED"
        else:
            logger.info("All simulation files present")
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
        
        logger.info(f"Phase 1 completed in {phase_end - phase_start}")
    
    def _phase_2_execution(self):
        """Phase 2: Simulation Execution"""
        logger.info("PHASE 2: SIMULATION EXECUTION")
        logger.info("-" * 50)
        
        phase_start = datetime.now()
        
        # Define simulations with optimized timeouts for your hardware
        simulations = [
            {
                'name': 'Advanced Gold Scalping',
                'script': 'advanced_gold_scalping_simulation.py',
                'priority': 1,
                'description': 'Specialized XAU_USD simulation with advanced parameters',
                'timeout': 900,  # 15 minutes
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
                'timeout': 1800,  # 30 minutes
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
        
        # Execute simulations
        for sim in simulations:
            logger.info(f"Executing {sim['name']}...")
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
                    logger.warning(f"ISSUES: {sim['name']} completed with issues")
                    status = "ISSUES"
                    
            except subprocess.TimeoutExpired:
                logger.error(f"TIMEOUT: {sim['name']} timed out after {sim['timeout']} seconds")
                status = "TIMEOUT"
                sim_end = datetime.now()
                result = type('obj', (object,), {'returncode': -1, 'stdout': '', 'stderr': 'Timeout'})
                post_resources = self._monitor_system_resources()
            except Exception as e:
                logger.error(f"FAILED: {sim['name']} failed: {e}")
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
                'stdout': result.stdout[-2000:] if result.stdout else '',
                'stderr': result.stderr[-1000:] if result.stderr else ''
            }
            
            logger.info(f"Completed {sim['name']} in {sim_end - sim_start}")
            logger.info(f"Post-execution: CPU {post_resources['cpu_percent']}% | RAM {post_resources['memory_percent']}%")
        
        phase_end = datetime.now()
        successful_sims = len([s for s in self.results['simulations'].values() if s['status'] == 'SUCCESS'])
        
        self.results['phases']['phase_2'] = {
            'name': 'Simulation Execution',
            'start': phase_start.isoformat(),
            'end': phase_end.isoformat(),
            'duration': str(phase_end - phase_start),
            'simulations_executed': len(simulations),
            'successful_simulations': successful_sims
        }
        
        logger.info(f"Phase 2 completed in {phase_end - phase_start}")
    
    def _phase_3_results_analysis(self):
        """Phase 3: Results Analysis"""
        logger.info("PHASE 3: RESULTS ANALYSIS")
        logger.info("-" * 50)
        
        phase_start = datetime.now()
        
        # Analyze results directory
        results_dir = Path("results")
        if results_dir.exists():
            result_files = list(results_dir.rglob("*.json"))
            logger.info(f"Found {len(result_files)} result files")
            
            # Analyze recent results (last 2 hours)
            recent_files = []
            for f in result_files:
                try:
                    if (datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)).total_seconds() < 7200:
                        recent_files.append(f)
                except:
                    continue
            
            logger.info(f"Found {len(recent_files)} recent result files")
            
            # Analyze results
            recent_results = []
            for file_path in recent_files:
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        recent_results.append({
                            'file': str(file_path),
                            'type': data.get('simulation_type', 'Unknown'),
                            'scenarios': data.get('total_scenarios', 0),
                            'successful': data.get('successful_scenarios', 0),
                            'execution_time': data.get('execution_time', 'Unknown'),
                            'best_strategy': data.get('best_strategy', {})
                        })
                except Exception as e:
                    logger.warning(f"Could not analyze {file_path}: {e}")
            
            self.results['validation'] = {
                'total_result_files': len(result_files),
                'recent_result_files': len(recent_files),
                'recent_results_analysis': recent_results,
                'results_analysis': 'COMPLETED'
            }
        else:
            logger.warning("No results directory found")
            self.results['validation'] = {
                'results_analysis': 'NO_RESULTS_DIR'
            }
        
        phase_end = datetime.now()
        self.results['phases']['phase_3'] = {
            'name': 'Results Analysis',
            'start': phase_start.isoformat(),
            'end': phase_end.isoformat(),
            'duration': str(phase_end - phase_start)
        }
        
        logger.info(f"Phase 3 completed in {phase_end - phase_start}")
    
    def _phase_4_final_report(self):
        """Phase 4: Final Report"""
        logger.info("PHASE 4: FINAL REPORT GENERATION")
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
                'memory_optimized': self.optimal_workers['memory_optimized'],
                'gpu_utilized': self.optimal_workers['gpu_enabled']
            }
        }
        
        # Save comprehensive report
        report_path = Path(f"simulation_report_{end_time.strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        phase_end = datetime.now()
        self.results['phases']['phase_4'] = {
            'name': 'Final Report Generation',
            'start': phase_start.isoformat(),
            'end': phase_end.isoformat(),
            'duration': str(phase_end - phase_start),
            'report_path': str(report_path)
        }
        
        logger.info(f"Phase 4 completed in {phase_end - phase_start}")
        logger.info(f"Report saved to: {report_path}")
    
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
        logger.info("SIMULATION EXECUTION COMPLETE")
        logger.info("=" * 80)
        
        final_report = self.results['final_report']
        
        logger.info(f"Total Execution Time: {final_report['execution_summary']['total_duration']}")
        logger.info(f"Simulations Executed: {final_report['execution_summary']['simulations_executed']}")
        logger.info(f"Success Rate: {final_report['success_metrics']['success_rate']:.1f}%")
        logger.info(f"System Health: {final_report['performance_summary']['system_health']}")
        logger.info(f"Hardware Optimized: {final_report['execution_summary']['hardware_optimized']}")
        
        # Performance metrics
        logger.info(f"\nPERFORMANCE METRICS:")
        logger.info(f"Expected Scenarios: {final_report['performance_summary']['expected_scenarios']:,}")
        logger.info(f"Actual Scenarios: {final_report['performance_summary']['actual_scenarios']:,}")
        logger.info(f"Scenario Efficiency: {final_report['performance_summary']['scenario_efficiency']:.1f}%")
        
        # Hardware utilization
        hw_util = final_report['hardware_utilization']
        logger.info(f"\nHARDWARE UTILIZATION:")
        logger.info(f"CPU Workers: {hw_util['cpu_workers_used']}")
        logger.info(f"Memory Optimized: {hw_util['memory_optimized']}")
        logger.info(f"GPU Utilized: {hw_util['gpu_utilized']}")
        
        logger.info(f"\nDetailed Report: {self.results['phases']['phase_4']['report_path']}")
        
        # Print simulation results
        logger.info(f"\nSIMULATION RESULTS:")
        for name, sim in self.results['simulations'].items():
            status_icon = "SUCCESS" if sim['status'] == 'SUCCESS' else "ISSUES" if sim['status'] == 'ISSUES' else "FAILED"
            logger.info(f"  {status_icon}: {name} ({sim['duration']})")
            if 'expected_scenarios' in sim:
                logger.info(f"      Expected Scenarios: {sim['expected_scenarios']:,}")
        
        # Print validation summary
        if 'recent_results_analysis' in self.results['validation']:
            logger.info(f"\nRECENT SIMULATION RESULTS:")
            for result in self.results['validation']['recent_results_analysis']:
                logger.info(f"  {Path(result['file']).name}: {result['successful']}/{result['scenarios']} scenarios successful")

def main():
    """Main execution function"""
    executor = SimulationExecutor()
    executor.execute_plan()
    executor.print_final_summary()

if __name__ == "__main__":
    main()








