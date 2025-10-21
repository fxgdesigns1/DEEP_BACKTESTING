#!/usr/bin/env python3
"""
DEEP BACKTEST LAUNCHER
Quick launcher for deep backtest optimization
"""

import os
import sys
import subprocess
from datetime import datetime

def main():
    print("🎯 DEEP BACKTEST OPTIMIZATION LAUNCHER")
    print("=" * 50)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Check if we're in the right directory
    if not os.path.exists("deep_backtest_optimizer.py"):
        print("❌ Error: deep_backtest_optimizer.py not found!")
        print("Please run this script from the project root directory.")
        return 1
    
    # Check for data
    if not os.path.exists("data/MASTER_DATASET"):
        print("❌ Error: MASTER_DATASET not found!")
        print("Please ensure real historical data is available in data/MASTER_DATASET/")
        return 1
    
    print("✅ Prerequisites check passed")
    print("")
    
    # Ask for confirmation
    print("This will run comprehensive backtesting optimization which may take 30-60 minutes.")
    print("The process will:")
    print("• Test multiple strategies across various parameters")
    print("• Analyze performance across different pairs and timeframes")
    print("• Generate optimal deployment configuration")
    print("• Create detailed performance reports")
    print("")
    
    response = input("Do you want to proceed? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Operation cancelled by user")
        return 0
    
    print("")
    print("🚀 Starting deep backtest optimization...")
    print("This may take 30-60 minutes. Please be patient.")
    print("")
    
    try:
        # Run the optimization
        result = subprocess.run([
            sys.executable, "run_deep_backtest_optimization.py"
        ], check=True)
        
        print("")
        print("✅ Deep backtest optimization completed successfully!")
        print("Check the results directory for detailed reports and deployment configurations.")
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"")
        print(f"❌ Optimization failed with exit code {e.returncode}")
        print("Check the logs for error details.")
        return 1
        
    except KeyboardInterrupt:
        print("")
        print("❌ Optimization interrupted by user")
        return 1
        
    except Exception as e:
        print(f"")
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())