#!/usr/bin/env python3
"""
HIGH-PERFORMANCE MONTE CARLO ANALYZER
Optimized for AMD 5950X, RTX 3080, 64GB RAM, NVMe Storage

Features:
- Multi-threaded simulations
- GPU acceleration where available
- Memory-optimized data structures
- Parallel processing of results
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, List, Any, Tuple, Optional
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import threading
import time

# Setup logging
log_filename = f"monte_carlo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try to use GPU acceleration if available
try:
    import cupy as cp
    import cudf
    HAS_GPU = True
    logger.info("GPU acceleration enabled with CUDA")
except ImportError:
    HAS_GPU = False
    logger.info("GPU acceleration not available, using CPU only")

class HighPerformanceMonteCarlo:
    """High-performance Monte Carlo analysis for trading strategies"""
    
    def __init__(self):
        """Initialize the Monte Carlo analyzer with system-specific optimizations"""
        self.start_time = datetime.now()
        self.system_specs = self._get_system_specs()
        self.optimal_workers = self._calculate_optimal_workers()
        
        # Output directory
        self.output_dir = Path("monte_carlo_results")
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Monte Carlo settings
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results_file = self.output_dir / f"mc_results_{self.timestamp}.json"
        self.report_file = self.output_dir / f"mc_report_{self.timestamp}.md"
        
        logger.info(f"HIGH-PERFORMANCE MONTE CARLO INITIALIZED")
        logger.info(f"System: {self.system_specs['cpu_cores']} cores | {self.system_specs['ram_gb']}GB RAM | GPU: {self.system_specs['gpu_available']}")
        logger.info(f"Optimal Workers: {self.optimal_workers['cpu_workers']} CPU threads | Batch size: {self.optimal_workers['mc_batch_size']}")
    
    def _get_system_specs(self) -> Dict[str, Any]:
        """Get system specifications for optimal performance"""
        try:
            # CPU info
            cpu_count = mp.cpu_count()
            
            # Memory info
            import psutil
            memory = psutil.virtual_memory()
            ram_gb = round(memory.total / (1024**3))
            
            # GPU detection
            gpu_available = False
            gpu_memory_gb = 0
            try:
                if HAS_GPU:
                    gpu_available = True
                    # Try to get GPU memory (this is approximate)
                    try:
                        import pynvml
                        pynvml.nvmlInit()
                        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                        memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                        gpu_memory_gb = round(memory_info.total / (1024**3))
                    except:
                        gpu_memory_gb = 8  # Assume at least 8GB if can't detect
            except:
                pass
            
            return {
                'cpu_cores': cpu_count,
                'ram_gb': ram_gb,
                'gpu_available': gpu_available,
                'gpu_memory_gb': gpu_memory_gb,
                'platform': sys.platform
            }
        except Exception as e:
            logger.warning(f"Could not detect system specs: {e}")
            # Fallback to high-performance system specs
            return {
                'cpu_cores': 16,  # Assuming 5950X
                'ram_gb': 64,
                'gpu_available': True,
                'gpu_memory_gb': 10,  # Assuming RTX 3080
                'platform': 'win32'
            }
    
    def _calculate_optimal_workers(self) -> Dict[str, Any]:
        """Calculate optimal worker configuration based on hardware"""
        cpu_cores = self.system_specs['cpu_cores']
        ram_gb = self.system_specs['ram_gb']
        gpu_available = self.system_specs['gpu_available']
        gpu_memory_gb = self.system_specs['gpu_memory_gb']
        
        # Use ~85% of available cores for workers
        cpu_workers = max(8, int(cpu_cores * 0.85))
        
        # Determine optimal batch size for Monte Carlo simulations
        if gpu_available and gpu_memory_gb > 6:
            # If we have a good GPU, we can process large batches
            mc_batch_size = 250 if gpu_memory_gb > 10 else 100
        else:
            # Otherwise scale based on CPU and RAM
            mc_batch_size = min(100, max(25, int(ram_gb / 2)))
        
        # Memory optimizations
        memory_optimized = True if ram_gb >= 32 else False
        large_dataset_mode = True if ram_gb >= 48 else False
        
        return {
            'cpu_workers': cpu_workers,
            'memory_optimized': memory_optimized,
            'large_dataset_mode': large_dataset_mode,
            'gpu_available': gpu_available,
            'mc_batch_size': mc_batch_size,
            'use_gpu_for_mc': gpu_available and HAS_GPU
        }
    
    def load_trade_data(self, file_path: str) -> pd.DataFrame:
        """Load trade data from a file"""
        logger.info(f"Loading trade data from {file_path}")
        
        try:
            # Determine file type based on extension
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                # Try to extract trades from common structures
                if 'trades' in data:
                    df = pd.DataFrame(data['trades'])
                elif 'results' in data and 'trades' in data['results']:
                    df = pd.DataFrame(data['results']['trades'])
                else:
                    # Create from raw data
                    df = pd.DataFrame(data)
            else:
                logger.error(f"Unsupported file format: {file_path}")
                raise ValueError(f"Unsupported file format: {file_path}")
            
            logger.info(f"Loaded {len(df)} trade records")
            return df
            
        except Exception as e:
            logger.error(f"Error loading trade data: {e}")
            raise
    
    def prepare_returns_data(self, df: pd.DataFrame) -> np.ndarray:
        """Extract and prepare returns data from trade DataFrame"""
        logger.info("Preparing returns data for Monte Carlo analysis")
        
        try:
            # Try to identify the returns/PnL column
            if 'pnl' in df.columns:
                returns_col = 'pnl'
            elif 'profit' in df.columns:
                returns_col = 'profit'
            elif 'returns' in df.columns:
                returns_col = 'returns'
            elif 'return' in df.columns:
                returns_col = 'return'
            else:
                # Try to find a numeric column that could be returns
                numeric_cols = df.select_dtypes(include=np.number).columns
                if len(numeric_cols) > 0:
                    returns_col = numeric_cols[0]
                    logger.warning(f"No obvious returns column found, using {returns_col}")
                else:
                    logger.error("No suitable returns column found in the data")
                    raise ValueError("No suitable returns column found in the data")
            
            # Extract returns as numpy array
            returns = df[returns_col].values
            logger.info(f"Extracted {len(returns)} returns values from column '{returns_col}'")
            return returns
            
        except Exception as e:
            logger.error(f"Error preparing returns data: {e}")
            raise
    
    def _mc_trade_shuffle_parallel_cpu(self, returns: np.ndarray, runs: int, seed: int) -> List[np.ndarray]:
        """Run Monte Carlo trade shuffling simulations in parallel on CPU"""
        logger.info(f"Running {runs} Monte Carlo trade shuffling simulations on CPU")
        n_trades = len(returns)
        
        # Generate all random permutations at once
        batch_size = self.optimal_workers['mc_batch_size']
        n_batches = (runs + batch_size - 1) // batch_size
        
        results = []
        rng = np.random.RandomState(seed)
        
        with ThreadPoolExecutor(max_workers=self.optimal_workers['cpu_workers']) as executor:
            future_to_batch = {}
            
            for batch_idx in range(n_batches):
                batch_runs = min(batch_size, runs - batch_idx * batch_size)
                if batch_runs <= 0:
                    break
                
                batch_seed = seed + batch_idx
                future = executor.submit(
                    self._run_mc_batch, returns, batch_runs, batch_seed
                )
                future_to_batch[future] = batch_idx
            
            completed = 0
            for future in future_to_batch:
                batch_results = future.result()
                results.extend(batch_results)
                
                completed += len(batch_results)
                if completed % (runs // 10) < batch_size:
                    logger.info(f"Monte Carlo progress: {completed}/{runs} simulations ({completed/runs*100:.1f}%)")
        
        return results
    
    def _run_mc_batch(self, returns: np.ndarray, n_runs: int, seed: int) -> List[np.ndarray]:
        """Run a batch of Monte Carlo simulations"""
        n_trades = len(returns)
        rng = np.random.RandomState(seed)
        results = []
        
        for _ in range(n_runs):
            idx = rng.permutation(n_trades)
            shuffled_returns = returns[idx]
            results.append(np.cumsum(shuffled_returns))
        
        return results
    
    def _mc_trade_shuffle_gpu(self, returns: np.ndarray, runs: int, seed: int) -> List[np.ndarray]:
        """Run Monte Carlo trade shuffling simulations on GPU (if available)"""
        if not HAS_GPU:
            logger.warning("GPU acceleration requested but not available, falling back to CPU")
            return self._mc_trade_shuffle_parallel_cpu(returns, runs, seed)
        
        logger.info(f"Running {runs} Monte Carlo trade shuffling simulations on GPU")
        try:
            # Move data to GPU
            returns_gpu = cp.array(returns)
            n_trades = len(returns)
            
            # Generate all simulations in batches
            batch_size = self.optimal_workers['mc_batch_size']
            n_batches = (runs + batch_size - 1) // batch_size
            
            all_paths = []
            
            for batch_idx in range(n_batches):
                batch_runs = min(batch_size, runs - batch_idx * batch_size)
                if batch_runs <= 0:
                    break
                
                # Create random permutations on GPU
                cp.random.seed(seed + batch_idx)
                
                # Process one simulation at a time to avoid memory issues
                batch_paths = []
                for i in range(batch_runs):
                    idx = cp.random.permutation(n_trades)
                    shuffled_returns = returns_gpu[idx]
                    cum_returns = cp.cumsum(shuffled_returns)
                    # Move result back to CPU
                    batch_paths.append(cp.asnumpy(cum_returns))
                
                all_paths.extend(batch_paths)
                
                if batch_idx % max(1, n_batches // 10) == 0:
                    logger.info(f"GPU Monte Carlo progress: {len(all_paths)}/{runs} simulations ({len(all_paths)/runs*100:.1f}%)")
            
            return all_paths
            
        except Exception as e:
            logger.error(f"Error running GPU Monte Carlo: {e}")
            logger.warning("Falling back to CPU implementation")
            return self._mc_trade_shuffle_parallel_cpu(returns, runs, seed)
    
    def _mc_block_bootstrap_parallel(self, returns: np.ndarray, runs: int, block_size: int, seed: int) -> List[np.ndarray]:
        """Run block bootstrap Monte Carlo simulations in parallel"""
        logger.info(f"Running {runs} block bootstrap Monte Carlo simulations (block size: {block_size})")
        n_trades = len(returns)
        n_blocks = int(np.ceil(n_trades / block_size))
        
        # Generate all simulations in batches
        batch_size = self.optimal_workers['mc_batch_size']
        n_batches = (runs + batch_size - 1) // batch_size
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.optimal_workers['cpu_workers']) as executor:
            future_to_batch = {}
            
            for batch_idx in range(n_batches):
                batch_runs = min(batch_size, runs - batch_idx * batch_size)
                if batch_runs <= 0:
                    break
                
                batch_seed = seed + batch_idx
                future = executor.submit(
                    self._run_block_bootstrap_batch, 
                    returns, batch_runs, block_size, n_trades, batch_seed
                )
                future_to_batch[future] = batch_idx
            
            completed = 0
            for future in future_to_batch:
                batch_results = future.result()
                results.extend(batch_results)
                
                completed += len(batch_results)
                if completed % (runs // 10) < batch_size:
                    logger.info(f"Block bootstrap progress: {completed}/{runs} simulations ({completed/runs*100:.1f}%)")
        
        return results
    
    def _run_block_bootstrap_batch(self, returns: np.ndarray, n_runs: int, block_size: int, n_trades: int, seed: int) -> List[np.ndarray]:
        """Run a batch of block bootstrap simulations"""
        rng = np.random.RandomState(seed)
        results = []
        n_blocks = int(np.ceil(n_trades / block_size))
        
        for _ in range(n_runs):
            bootstrapped_returns = []
            for _ in range(n_blocks):
                # Select a random starting point for the block
                start = rng.randint(0, max(1, n_trades - block_size))
                # Add the block to bootstrapped returns
                block = returns[start:start+block_size]
                bootstrapped_returns.extend(block)
            
            # Trim to original length
            bootstrapped_returns = bootstrapped_returns[:n_trades]
            results.append(np.cumsum(np.array(bootstrapped_returns)))
        
        return results
    
    def run_monte_carlo_simulations(
        self, 
        returns: np.ndarray, 
        runs: int = 1000, 
        block_size: int = 10, 
        seed: int = 42
    ) -> Dict[str, Any]:
        """Run multiple types of Monte Carlo simulations"""
        logger.info(f"Running {runs} Monte Carlo simulations with seed {seed}")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'n_trades': len(returns),
            'runs': runs,
            'block_size': block_size,
            'seed': seed,
            'original_returns': {
                'mean': float(np.mean(returns)),
                'std': float(np.std(returns)),
                'sharpe': float(np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0),
                'total': float(np.sum(returns)),
                'min': float(np.min(returns)),
                'max': float(np.max(returns))
            },
            'trade_shuffle_mc': {},
            'block_bootstrap_mc': {},
            'performance': {}
        }
        
        start_time = time.time()
        
        # Run trade shuffle Monte Carlo (standard)
        shuffle_start = time.time()
        logger.info("Running standard trade shuffle Monte Carlo...")
        
        if self.optimal_workers['use_gpu_for_mc']:
            shuffle_paths = self._mc_trade_shuffle_gpu(returns, runs, seed)
        else:
            shuffle_paths = self._mc_trade_shuffle_parallel_cpu(returns, runs, seed)
        
        shuffle_end = time.time()
        logger.info(f"Trade shuffle Monte Carlo completed in {shuffle_end - shuffle_start:.2f} seconds")
        
        # Calculate statistics from shuffle paths
        shuffle_metrics = self._calculate_mc_metrics(shuffle_paths, returns)
        results['trade_shuffle_mc'] = shuffle_metrics
        
        # Run block bootstrap Monte Carlo
        bootstrap_start = time.time()
        logger.info("Running block bootstrap Monte Carlo...")
        
        bootstrap_paths = self._mc_block_bootstrap_parallel(returns, runs, block_size, seed)
        
        bootstrap_end = time.time()
        logger.info(f"Block bootstrap Monte Carlo completed in {bootstrap_end - bootstrap_start:.2f} seconds")
        
        # Calculate statistics from bootstrap paths
        bootstrap_metrics = self._calculate_mc_metrics(bootstrap_paths, returns)
        results['block_bootstrap_mc'] = bootstrap_metrics
        
        # Calculate performance metrics
        end_time = time.time()
        total_duration = end_time - start_time
        
        results['performance'] = {
            'total_duration_seconds': total_duration,
            'trade_shuffle_duration_seconds': shuffle_end - shuffle_start,
            'block_bootstrap_duration_seconds': bootstrap_end - bootstrap_start,
            'simulations_per_second': runs * 2 / total_duration
        }
        
        logger.info(f"Monte Carlo simulations completed in {total_duration:.2f} seconds")
        logger.info(f"Performance: {results['performance']['simulations_per_second']:.1f} simulations per second")
        
        # Save results
        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Monte Carlo results saved to {self.results_file}")
        
        # Generate human-readable report
        self._generate_report(results)
        
        return results
    
    def _calculate_mc_metrics(self, paths: List[np.ndarray], original_returns: np.ndarray) -> Dict[str, Any]:
        """Calculate metrics from Monte Carlo paths"""
        # Extract final returns
        final_returns = np.array([path[-1] for path in paths])
        
        # Calculate Sharpe ratios
        sharpe_ratios = np.array([
            np.mean(path[1:] - path[:-1]) / np.std(path[1:] - path[:-1])
            if len(path) > 1 and np.std(path[1:] - path[:-1]) > 0 else 0
            for path in paths
        ])
        
        # Calculate maximum drawdowns
        max_drawdowns = np.array([self._calculate_max_drawdown(path) for path in paths])
        
        # Calculate percentiles
        return_percentiles = np.percentile(final_returns, [1, 5, 10, 25, 50, 75, 90, 95, 99])
        sharpe_percentiles = np.percentile(sharpe_ratios, [1, 5, 10, 25, 50, 75, 90, 95, 99])
        drawdown_percentiles = np.percentile(max_drawdowns, [1, 5, 10, 25, 50, 75, 90, 95, 99])
        
        # Calculate survival rate (% of simulations with positive returns)
        survival_rate = np.mean(final_returns > 0) * 100
        
        # Calculate average path and confidence bands
        def get_path_length(p):
            return len(p)
        
        min_length = min(map(get_path_length, paths))
        path_matrix = np.zeros((len(paths), min_length))
        
        for i, path in enumerate(paths):
            path_matrix[i, :] = path[:min_length]
        
        mean_path = np.mean(path_matrix, axis=0)
        lower_5pct = np.percentile(path_matrix, 5, axis=0)
        upper_95pct = np.percentile(path_matrix, 95, axis=0)
        
        return {
            'returns_mean': float(np.mean(final_returns)),
            'returns_std': float(np.std(final_returns)),
            'returns_min': float(np.min(final_returns)),
            'returns_max': float(np.max(final_returns)),
            'sharpe_mean': float(np.mean(sharpe_ratios)),
            'sharpe_std': float(np.std(sharpe_ratios)),
            'max_drawdown_mean': float(np.mean(max_drawdowns)),
            'max_drawdown_std': float(np.std(max_drawdowns)),
            'survival_rate': float(survival_rate),
            'return_percentiles': {
                'p1': float(return_percentiles[0]),
                'p5': float(return_percentiles[1]),
                'p10': float(return_percentiles[2]),
                'p25': float(return_percentiles[3]),
                'p50': float(return_percentiles[4]),
                'p75': float(return_percentiles[5]),
                'p90': float(return_percentiles[6]),
                'p95': float(return_percentiles[7]),
                'p99': float(return_percentiles[8])
            },
            'sharpe_percentiles': {
                'p1': float(sharpe_percentiles[0]),
                'p5': float(sharpe_percentiles[1]),
                'p10': float(sharpe_percentiles[2]),
                'p25': float(sharpe_percentiles[3]),
                'p50': float(sharpe_percentiles[4]),
                'p75': float(sharpe_percentiles[5]),
                'p90': float(sharpe_percentiles[6]),
                'p95': float(sharpe_percentiles[7]),
                'p99': float(sharpe_percentiles[8])
            },
            'drawdown_percentiles': {
                'p1': float(drawdown_percentiles[0]),
                'p5': float(drawdown_percentiles[1]),
                'p10': float(drawdown_percentiles[2]),
                'p25': float(drawdown_percentiles[3]),
                'p50': float(drawdown_percentiles[4]),
                'p75': float(drawdown_percentiles[5]),
                'p90': float(drawdown_percentiles[6]),
                'p95': float(drawdown_percentiles[7]),
                'p99': float(drawdown_percentiles[8])
            },
            'mean_path': mean_path.tolist(),
            'lower_5pct_path': lower_5pct.tolist(),
            'upper_95pct_path': upper_95pct.tolist()
        }
    
    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate maximum drawdown from cumulative returns"""
        peak = returns[0]
        max_dd = 0
        
        for value in returns:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
        
        return max_dd
    
    def _generate_report(self, results: Dict[str, Any]) -> None:
        """Generate human-readable report from Monte Carlo results"""
        logger.info("Generating Monte Carlo report...")
        
        with open(self.report_file, 'w') as f:
            f.write("# Monte Carlo Simulation Report\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Simulations:** {results['runs']}\n")
            f.write(f"**Original Trades:** {results['n_trades']}\n\n")
            
            # Original returns statistics
            f.write("## Original Returns Statistics\n\n")
            f.write("| Metric | Value |\n")
            f.write("|--------|-------|\n")
            f.write(f"| Mean Return | {results['original_returns']['mean']:.6f} |\n")
            f.write(f"| Std Dev | {results['original_returns']['std']:.6f} |\n")
            f.write(f"| Sharpe Ratio | {results['original_returns']['sharpe']:.4f} |\n")
            f.write(f"| Total Return | {results['original_returns']['total']:.6f} |\n")
            f.write(f"| Min Return | {results['original_returns']['min']:.6f} |\n")
            f.write(f"| Max Return | {results['original_returns']['max']:.6f} |\n\n")
            
            # Trade Shuffle Monte Carlo
            f.write("## Trade Shuffle Monte Carlo\n\n")
            f.write("| Metric | Mean | Std Dev | 5th Percentile | Median | 95th Percentile |\n")
            f.write("|--------|------|---------|----------------|--------|----------------|\n")
            f.write(f"| Final Return | {results['trade_shuffle_mc']['returns_mean']:.6f} | ")
            f.write(f"{results['trade_shuffle_mc']['returns_std']:.6f} | ")
            f.write(f"{results['trade_shuffle_mc']['return_percentiles']['p5']:.6f} | ")
            f.write(f"{results['trade_shuffle_mc']['return_percentiles']['p50']:.6f} | ")
            f.write(f"{results['trade_shuffle_mc']['return_percentiles']['p95']:.6f} |\n")
            
            f.write(f"| Sharpe Ratio | {results['trade_shuffle_mc']['sharpe_mean']:.4f} | ")
            f.write(f"{results['trade_shuffle_mc']['sharpe_std']:.4f} | ")
            f.write(f"{results['trade_shuffle_mc']['sharpe_percentiles']['p5']:.4f} | ")
            f.write(f"{results['trade_shuffle_mc']['sharpe_percentiles']['p50']:.4f} | ")
            f.write(f"{results['trade_shuffle_mc']['sharpe_percentiles']['p95']:.4f} |\n")
            
            f.write(f"| Max Drawdown | {results['trade_shuffle_mc']['max_drawdown_mean']:.4f} | ")
            f.write(f"{results['trade_shuffle_mc']['max_drawdown_std']:.4f} | ")
            f.write(f"{results['trade_shuffle_mc']['drawdown_percentiles']['p5']:.4f} | ")
            f.write(f"{results['trade_shuffle_mc']['drawdown_percentiles']['p50']:.4f} | ")
            f.write(f"{results['trade_shuffle_mc']['drawdown_percentiles']['p95']:.4f} |\n\n")
            
            f.write(f"**Survival Rate:** {results['trade_shuffle_mc']['survival_rate']:.2f}%\n\n")
            
            # Block Bootstrap Monte Carlo
            f.write("## Block Bootstrap Monte Carlo\n\n")
            f.write("| Metric | Mean | Std Dev | 5th Percentile | Median | 95th Percentile |\n")
            f.write("|--------|------|---------|----------------|--------|----------------|\n")
            f.write(f"| Final Return | {results['block_bootstrap_mc']['returns_mean']:.6f} | ")
            f.write(f"{results['block_bootstrap_mc']['returns_std']:.6f} | ")
            f.write(f"{results['block_bootstrap_mc']['return_percentiles']['p5']:.6f} | ")
            f.write(f"{results['block_bootstrap_mc']['return_percentiles']['p50']:.6f} | ")
            f.write(f"{results['block_bootstrap_mc']['return_percentiles']['p95']:.6f} |\n")
            
            f.write(f"| Sharpe Ratio | {results['block_bootstrap_mc']['sharpe_mean']:.4f} | ")
            f.write(f"{results['block_bootstrap_mc']['sharpe_std']:.4f} | ")
            f.write(f"{results['block_bootstrap_mc']['sharpe_percentiles']['p5']:.4f} | ")
            f.write(f"{results['block_bootstrap_mc']['sharpe_percentiles']['p50']:.4f} | ")
            f.write(f"{results['block_bootstrap_mc']['sharpe_percentiles']['p95']:.4f} |\n")
            
            f.write(f"| Max Drawdown | {results['block_bootstrap_mc']['max_drawdown_mean']:.4f} | ")
            f.write(f"{results['block_bootstrap_mc']['max_drawdown_std']:.4f} | ")
            f.write(f"{results['block_bootstrap_mc']['drawdown_percentiles']['p5']:.4f} | ")
            f.write(f"{results['block_bootstrap_mc']['drawdown_percentiles']['p50']:.4f} | ")
            f.write(f"{results['block_bootstrap_mc']['drawdown_percentiles']['p95']:.4f} |\n\n")
            
            f.write(f"**Survival Rate:** {results['block_bootstrap_mc']['survival_rate']:.2f}%\n\n")
            
            # Performance statistics
            f.write("## Performance Statistics\n\n")
            f.write(f"Total Duration: {results['performance']['total_duration_seconds']:.2f} seconds\n")
            f.write(f"Trade Shuffle Duration: {results['performance']['trade_shuffle_duration_seconds']:.2f} seconds\n")
            f.write(f"Block Bootstrap Duration: {results['performance']['block_bootstrap_duration_seconds']:.2f} seconds\n")
            f.write(f"Performance: {results['performance']['simulations_per_second']:.1f} simulations per second\n")
        
        logger.info(f"Monte Carlo report saved to {self.report_file}")

def run_monte_carlo_analysis(trades_file: str, runs: int = 1000, block_size: int = 10):
    """Run Monte Carlo analysis on a trades file"""
    logger.info(f"Running Monte Carlo analysis on {trades_file} with {runs} runs")
    
    try:
        mc = HighPerformanceMonteCarlo()
        
        # Load trade data
        trades_df = mc.load_trade_data(trades_file)
        
        # Extract returns
        returns = mc.prepare_returns_data(trades_df)
        
        # Run Monte Carlo simulations
        results = mc.run_monte_carlo_simulations(returns, runs, block_size)
        
        logger.info(f"Monte Carlo analysis completed successfully")
        return results
    
    except Exception as e:
        logger.error(f"Error running Monte Carlo analysis: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="High-Performance Monte Carlo Analyzer")
    parser.add_argument("trades_file", help="Path to trades data file (CSV or JSON)")
    parser.add_argument("--runs", type=int, default=1000, help="Number of Monte Carlo simulations to run")
    parser.add_argument("--block-size", type=int, default=10, help="Block size for block bootstrap")
    args = parser.parse_args()
    
    # Run Monte Carlo analysis
    run_monte_carlo_analysis(args.trades_file, args.runs, args.block_size)
