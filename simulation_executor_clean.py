#!/usr/bin/env python3
"""
CLEAN HIGH-PERFORMANCE SIMULATION EXECUTOR
4 Parallel Simulations with Live Progress Monitoring
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

class CleanSimulationExecutor:
    """Clean high-performance simulation executor with 4 parallel simulations"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.system_specs = self._get_system_specs()
        self.progress = {'completed': 0, 'total': 0, 'running': 0}
        self.results = {}
        
        logger.info("CLEAN SIMULATION EXECUTOR INITIALIZED")
        logger.info(f"System: {self.system_specs['cpu_cores']} cores | {self.system_specs['ram_gb']}GB RAM")
        logger.info("Configuration: 4 PARALLEL SIMULATIONS with LIVE PROGRESS MONITORING")
        
    def _get_system_specs(self):
        """Get system specifications"""
        try:
            cpu_count = mp.cpu_count()
            memory = psutil.virtual_memory()
            ram_gb = round(memory.total / (1024**3))
            
            # GPU detection
            gpu_available = False
            try:
                import torch
                gpu_available = torch.cuda.is_available()
            except:
                pass
            
            return {
                'cpu_cores': cpu_count,
                'ram_gb': ram_gb,
                'gpu_available': gpu_available
            }
        except Exception as e:
            logger.error(f"Error getting system specs: {e}")
            return {'cpu_cores': 16, 'ram_gb': 64, 'gpu_available': False}
    
    def execute_simulations(self):
        """Execute all simulations with 4 parallel and live monitoring"""
        logger.info("STARTING SIMULATION EXECUTION WITH 4 PARALLEL SIMULATIONS")
        
        # Define simulations to run
        simulations = [
            {'name': 'Advanced Gold Scalping', 'script': 'advanced_gold_scalping_simulation.py', 'timeout': 1200},
            {'name': 'Multi-Pair Simulation', 'script': 'multi_pair_simulation.py', 'timeout': 900},
            {'name': 'Real Data Simulation', 'script': 'real_data_simulation.py', 'timeout': 1800},
            {'name': 'Risk Management Simulation', 'script': 'risk_management_simulation.py', 'timeout': 1800}
        ]
        
        self.progress['total'] = len(simulations)
        logger.info(f"Total simulations: {self.progress['total']}")
        
        # Start live monitor
        monitor_thread = threading.Thread(target=self._live_monitor, daemon=True)
        monitor_thread.start()
        
        # Execute 4 simulations in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(self._execute_simulation, sim, i): sim 
                      for i, sim in enumerate(simulations)}
            
            # Wait for all to complete
            for future in futures:
                try:
                    future.result()
                    self.progress['completed'] += 1
                    logger.info(f"LIVE PROGRESS: {self.progress['completed']}/{self.progress['total']} completed")
                except Exception as e:
                    logger.error(f"Simulation failed: {e}")
        
        # Final report
        self._generate_final_report()
    
    def _live_monitor(self):
        """Live progress monitor showing real-time stats"""
        start_time = datetime.now()
        while self.progress['completed'] < self.progress['total']:
            elapsed = datetime.now() - start_time
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            logger.info(f"LIVE STATS: {self.progress['completed']}/{self.progress['total']} done | CPU: {cpu_percent}% | RAM: {memory.percent}% | Time: {elapsed}")
            time.sleep(15)  # Update every 15 seconds
    
    def _execute_simulation(self, sim, index):
        """Execute a single simulation with progress tracking"""
        self.progress['running'] += 1
        logger.info(f"[{index+1}] EXECUTING {sim['name']}...")
        sim_start = datetime.now()
        
        # Monitor resources before starting
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        logger.info(f"[{index+1}] Pre-execution: CPU {cpu_percent}% | RAM {memory.percent}%")
        
        try:
            # Run simulation
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            env['OMP_NUM_THREADS'] = '30'  # Use 30 threads
            env['NUMEXPR_MAX_THREADS'] = '30'
            
            result = subprocess.run(
                [sys.executable, sim['script']],
                capture_output=True,
                text=True,
                timeout=sim.get('timeout', 1800),
                env=env
            )
            
            # Monitor resources after completion
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            if result.returncode == 0:
                logger.info(f"[{index+1}] SUCCESS: {sim['name']} completed successfully")
                status = "SUCCESS"
            else:
                logger.warning(f"[{index+1}] WARNING: {sim['name']} completed with issues")
                status = "ISSUES"
                
        except subprocess.TimeoutExpired:
            logger.error(f"[{index+1}] TIMEOUT: {sim['name']} timed out")
            status = "TIMEOUT"
            result = type('obj', (object,), {'returncode': -1, 'stdout': '', 'stderr': 'Timeout'})
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
        except Exception as e:
            logger.error(f"[{index+1}] ERROR: {sim['name']} failed: {e}")
            status = "ERROR"
            result = type('obj', (object,), {'returncode': -1, 'stdout': '', 'stderr': str(e)})
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
        
        sim_end = datetime.now()
        self.progress['running'] -= 1
        
        # Store results
        self.results[sim['name']] = {
            'status': status,
            'duration': str(sim_end - sim_start),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent
        }
        
        logger.info(f"[{index+1}] COMPLETED: {sim['name']} in {sim_end - sim_start}")
        logger.info(f"[{index+1}] Post-execution: CPU {cpu_percent}% | RAM {memory.percent}%")
    
    def _generate_final_report(self):
        """Generate final execution report"""
        end_time = datetime.now()
        total_time = end_time - self.start_time
        
        logger.info("=" * 60)
        logger.info("SIMULATION EXECUTION COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Total execution time: {total_time}")
        logger.info(f"Simulations completed: {self.progress['completed']}/{self.progress['total']}")
        
        # Results summary
        for name, result in self.results.items():
            logger.info(f"{name}: {result['status']} ({result['duration']})")
        
        # Save results
        report_data = {
            'execution_time': str(total_time),
            'completed_simulations': self.progress['completed'],
            'total_simulations': self.progress['total'],
            'results': self.results,
            'system_specs': self.system_specs
        }
        
        report_path = f"simulation_report_{end_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Report saved to: {report_path}")

if __name__ == "__main__":
    executor = CleanSimulationExecutor()
    executor.execute_simulations()








