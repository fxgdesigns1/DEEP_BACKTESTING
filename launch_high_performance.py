#!/usr/bin/env python3
"""
High-Performance Strategy Search Launcher
Optimized for 3080 GPU / 5950X CPU / 64GB RAM / NVMe Storage
"""

import os
import sys
import multiprocessing
import psutil
import logging
from datetime import datetime

# Set high-performance environment variables
os.environ['OMP_NUM_THREADS'] = '16'
os.environ['MKL_NUM_THREADS'] = '16'
os.environ['NUMEXPR_NUM_THREADS'] = '16'
os.environ['OPENBLAS_NUM_THREADS'] = '16'
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ['TF_GPU_MEMORY_GROWTH'] = 'true'

# Configure multiprocessing
multiprocessing.set_start_method('spawn', force=True)

# Setup high-performance logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'high_performance_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def optimize_system_performance():
    """Optimize system for high-performance backtesting"""
    logger.info("🚀 Optimizing system for high-performance backtesting...")
    
    # Set process priority to high
    try:
        p = psutil.Process()
        p.nice(psutil.HIGH_PRIORITY_CLASS)
        logger.info("✅ Process priority set to HIGH")
    except Exception as e:
        logger.warning(f"⚠️ Could not set process priority: {e}")
    
    # Display system specs
    cpu_count = multiprocessing.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    logger.info(f"💻 System Specs:")
    logger.info(f"   CPU Cores: {cpu_count}")
    logger.info(f"   RAM: {memory_gb:.1f} GB")
    logger.info(f"   Available RAM: {psutil.virtual_memory().available / (1024**3):.1f} GB")
    
    # Check GPU availability
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            logger.info(f"🎮 GPU: {gpu_name}")
            logger.info(f"   GPU Memory: {gpu_memory:.1f} GB")
            logger.info("✅ GPU acceleration enabled")
        else:
            logger.warning("⚠️ GPU not available for acceleration")
    except ImportError:
        logger.info("ℹ️ PyTorch not available - using CPU only")
    
    return True

def launch_high_performance_search():
    """Launch the high-performance strategy search"""
    logger.info("🎯 Launching Ultimate Strategy Search with High Performance")
    logger.info("=" * 80)
    
    # Optimize system
    optimize_system_performance()
    
    # Import and run controller with high-performance config
    try:
        from controller import UltimateStrategySearchController
        
        # Initialize controller with high-performance config
        controller = UltimateStrategySearchController(
            config_file='experiments_high_performance.yaml',
            max_workers=16,
            use_gpu=True,
            memory_limit_gb=56
        )
        
        logger.info("🚀 Starting high-performance strategy search...")
        logger.info("📊 This will test thousands of strategy combinations")
        logger.info("⏱️ Estimated time: 2-6 hours depending on results")
        logger.info("💾 Results will be saved to results/ directory")
        
        # Run the search
        results = controller.run_ultimate_search()
        
        logger.info("✅ High-performance strategy search completed!")
        logger.info(f"📈 Found {len(results.get('successful_strategies', []))} successful strategies")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ High-performance search failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function"""
    logger.info("🎯 High-Performance Strategy Search Launcher")
    logger.info("Optimized for: RTX 3080 + Ryzen 5950X + 64GB RAM + NVMe")
    logger.info("=" * 80)
    
    # Check if we're on the right system
    cpu_count = multiprocessing.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    if cpu_count < 12:
        logger.warning(f"⚠️ Detected only {cpu_count} CPU cores. This system is optimized for 16+ cores.")
    
    if memory_gb < 32:
        logger.warning(f"⚠️ Detected only {memory_gb:.1f} GB RAM. This system is optimized for 64GB+ RAM.")
    
    # Launch the search
    results = launch_high_performance_search()
    
    if results:
        logger.info("🎉 High-performance search completed successfully!")
        logger.info("📊 Check the results/ directory for detailed outputs")
    else:
        logger.error("❌ High-performance search failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
