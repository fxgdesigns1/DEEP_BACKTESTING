#!/usr/bin/env python3
"""
STRATEGY STRESS TEST RUNNER
High-performance implementation of stress tests for trading strategies
"""

import os
import sys
import subprocess
import json
import time
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'stress_test_runner_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_data_download():
    """Run the high performance data downloader"""
    logger.info("STEP 1: RUNNING HIGH-PERFORMANCE DATA DOWNLOADER")
    logger.info("=" * 80)
    
    try:
        # Check if downloader script exists
        downloader_path = Path("high_performance_data_downloader.py")
        if not downloader_path.exists():
            logger.error(f"Data downloader script not found at {downloader_path}")
            return False
        
        # Execute downloader script
        logger.info(f"Executing {downloader_path}")
        result = subprocess.run(
            [sys.executable, str(downloader_path)],
            capture_output=True,
            text=True
        )
        
        # Check result
        if result.returncode != 0:
            logger.error(f"Data downloader failed with code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False
        
        logger.info("Data downloader completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error running data downloader: {e}")
        return False

def run_stress_test_orchestrator():
    """Run the high performance stress test orchestrator"""
    logger.info("STEP 2: RUNNING HIGH-PERFORMANCE STRESS TEST ORCHESTRATOR")
    logger.info("=" * 80)
    
    try:
        # Check if orchestrator script exists
        orchestrator_path = Path("strategy_stress_test_orchestrator.py")
        if not orchestrator_path.exists():
            logger.error(f"Orchestrator script not found at {orchestrator_path}")
            return False
        
        # Execute orchestrator script
        logger.info(f"Executing {orchestrator_path}")
        result = subprocess.run(
            [sys.executable, str(orchestrator_path)],
            capture_output=True,
            text=True
        )
        
        # Check result
        if result.returncode != 0:
            logger.error(f"Stress test orchestrator failed with code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False
        
        logger.info("Stress test orchestrator completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error running stress test orchestrator: {e}")
        return False

def check_results():
    """Check for stress test results and display summary"""
    logger.info("STEP 3: CHECKING RESULTS")
    logger.info("=" * 80)
    
    try:
        # Check for results directory
        results_dir = Path("strategy_stress_test_results")
        if not results_dir.exists():
            logger.error(f"Results directory not found at {results_dir}")
            return False
        
        # Find the most recent final report
        report_files = list(results_dir.glob("final_report_*.json"))
        if not report_files:
            logger.error("No final report files found")
            return False
        
        latest_report = max(report_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"Found latest report: {latest_report}")
        
        # Load and display summary
        with open(latest_report, 'r') as f:
            report = json.load(f)
        
        logger.info("\n" + "=" * 80)
        logger.info(f"STRESS TEST RESULTS SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Strategy: {report.get('strategy_name', 'Unknown')}")
        logger.info(f"Robustness Score: {report.get('robustness_score', 'N/A')}/100")
        logger.info(f"Total Tests Run: {report.get('summary', {}).get('total_tests_run', 'N/A')}")
        logger.info(f"Monte Carlo Simulations: {report.get('summary', {}).get('monte_carlo_simulations', 'N/A')}")
        logger.info(f"Test Duration: {report.get('summary', {}).get('test_duration', 'N/A')}")
        
        # Find the human-readable report
        md_reports = list(results_dir.glob("STRATEGY_STRESS_TEST_REPORT_*.md"))
        if md_reports:
            latest_md = max(md_reports, key=lambda p: p.stat().st_mtime)
            logger.info(f"\nHuman-readable report available at: {latest_md}")
        
        logger.info("=" * 80)
        return True
        
    except Exception as e:
        logger.error(f"Error checking results: {e}")
        return False

def main():
    """Main execution function"""
    start_time = datetime.now()
    logger.info(f"STARTING STRATEGY STRESS TEST PIPELINE AT {start_time}")
    logger.info("=" * 80)
    
    success = True
    
    # Step 1: Run data downloader
    if not run_data_download():
        logger.error("Data download stage failed")
        success = False
    
    # Only proceed if data download was successful
    if success:
        # Step 2: Run stress test orchestrator
        if not run_stress_test_orchestrator():
            logger.error("Stress test orchestration stage failed")
            success = False
    
    # Check results regardless of orchestrator success (might have partial results)
    check_results()
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info("\n" + "=" * 80)
    if success:
        logger.info(f"✅ STRESS TEST PIPELINE COMPLETED SUCCESSFULLY IN {duration}")
    else:
        logger.info(f"❌ STRESS TEST PIPELINE COMPLETED WITH ERRORS IN {duration}")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()

