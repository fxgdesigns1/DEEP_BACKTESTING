# Ultra High-Performance Strategy Stress Testing Suite

**Optimized for AMD 5950X, RTX 3080, 64GB RAM, NVMe Storage**

## Overview

This stress testing suite is specially designed to leverage your high-performance hardware to thoroughly test the XAU_USD 15m EMA Strategy. The system uses parallel processing, GPU acceleration, and memory optimization to achieve maximum performance.

## Features

- **GPU Acceleration**: CUDA-powered calculations using your RTX 3080
- **Multi-Core Utilization**: Optimized for all 16 cores (32 threads) of your 5950X
- **Memory Optimization**: Leverages your 64GB RAM for data caching
- **NVMe Performance**: Uses memory-mapped files for ultra-fast storage I/O
- **Comprehensive Testing**: Transaction costs, parameter robustness, market conditions
- **Advanced Monte Carlo**: GPU-accelerated simulations with 1000+ runs
- **Professional Reporting**: Detailed metrics and recommendations

## How to Run

Simply run the main launcher script which orchestrates the entire process:

```bash
python run_high_performance_stress_test.py
```

This will:
1. Download and prepare the latest market data
2. Run comprehensive backtests with various stress conditions
3. Perform GPU-accelerated Monte Carlo simulations
4. Generate detailed reports and recommendations

## Components

- `run_high_performance_stress_test.py`: Main launcher script
- `high_performance_data_downloader.py`: Parallel data acquisition module
- `strategy_backtester.py`: Multi-threaded backtesting engine
- `high_performance_monte_carlo.py`: GPU-accelerated Monte Carlo simulator
- `strategy_stress_test_orchestrator.py`: Test orchestration and reporting engine
- `stress_test_config.json`: Configuration optimized for your hardware

## System Requirements

- **CPU**: AMD Ryzen 5950X (16-core, 32-thread)
- **GPU**: NVIDIA RTX 3080 (10GB VRAM)
- **RAM**: 64GB DDR4-3600
- **Storage**: NVMe SSD
- **OS**: Windows 10/11 or Linux
- **Python**: 3.8+ with CUDA toolkit

## Dependencies

Key Python packages:
- `numpy`, `pandas` - Data processing
- `cupy`, `numba` - GPU acceleration
- `psutil` - System monitoring and optimization

CUDA GPU acceleration is automatically enabled if available, otherwise, the system falls back to multi-threaded CPU processing.

## Optimization Details

The suite employs several optimization techniques:

- **Process Priority Management**: Sets highest priority for critical processes
- **Memory-Mapped Files**: Uses memory mapping for efficient NVMe access
- **Thread Affinity**: Optimal core assignment for parallel tasks
- **Dynamic Batch Sizing**: Adjusts processing batches based on GPU VRAM
- **Zero-Copy Data Transfers**: Minimizes data movement between CPU and GPU
- **RAM Caching**: Preloads frequently accessed data into RAM

## Output

The system generates several output files:

- `stress_test_results/stress_test_results_*.json`: Raw test results
- `monte_carlo_results/mc_results_*.json`: Monte Carlo simulation data
- `strategy_stress_test_results/STRATEGY_STRESS_TEST_REPORT_*.md`: Comprehensive report
- `*.log`: Detailed execution logs

## Performance Expectations

On your hardware (5950X + RTX 3080 + 64GB RAM + NVMe):

- **Data Download**: ~5-10 seconds
- **Backtesting**: ~15-30 seconds for all stress tests
- **Monte Carlo**: ~20-40 seconds for 1000 simulations
- **Report Generation**: ~5-10 seconds
- **Total Runtime**: ~45-90 seconds for complete analysis

The system is designed to utilize your hardware to its maximum potential:
- All 32 threads for parallel processing
- 10GB GPU VRAM for acceleration
- ~48GB RAM for caching
- NVMe's high bandwidth for data access

