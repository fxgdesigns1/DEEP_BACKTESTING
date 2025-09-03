#!/usr/bin/env python3
"""
Deep Backtesting Environment Setup Script
This script sets up the complete backtesting environment for strategy testing
"""

import os
import sys
import shutil
import subprocess
import json
from datetime import datetime
from pathlib import Path

def setup_environment():
    """Setup the complete backtesting environment"""
    print("🚀 Setting up Deep Backtesting Environment...")
    
    # Create necessary directories
    directories = [
        'logs',
        'temp',
        'backup',
        'exports',
        'reports'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Copy configuration files
    config_files = {
        'config/config.yaml': 'config.yaml',
        'config/settings.yaml': 'settings.yaml'
    }
    
    for src, dst in config_files.items():
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"✅ Copied config: {src} -> {dst}")
    
    # Create environment info
    env_info = {
        'setup_date': datetime.now().isoformat(),
        'python_version': sys.version,
        'platform': sys.platform,
        'directories_created': directories,
        'data_pairs': [
            'EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 'USD_CAD',
            'USD_CHF', 'NZD_USD', 'XAU_USD', 'EUR_JPY', 'GBP_JPY'
        ],
        'strategies_available': [
            'UltraStrictV3Strategy',
            'EnhancedOptimizedStrategy',
            'LiveOptimizedStrategyManager'
        ]
    }
    
    with open('environment_info.json', 'w') as f:
        json.dump(env_info, f, indent=2)
    
    print("✅ Environment info saved to environment_info.json")
    
    # Create test runner script
    create_test_runner()
    
    print("\n🎯 Deep Backtesting Environment Setup Complete!")
    print("\n📁 Directory Structure:")
    print("├── strategies/     - Strategy implementations")
    print("├── data/          - Historical price data")
    print("├── scripts/       - Analysis and testing scripts")
    print("├── results/       - Test results and reports")
    print("├── config/        - Configuration files")
    print("├── logs/          - Test logs")
    print("├── temp/          - Temporary files")
    print("├── exports/       - Exported results")
    print("└── reports/       - Generated reports")

def create_test_runner():
    """Create the main test runner script"""
    runner_script = '''#!/usr/bin/env python3
"""
Deep Backtesting Test Runner
Main script to run comprehensive strategy testing
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from strategies.ultra_strict_v3_strategy import UltraStrictV3Strategy
from strategies.enhanced_optimized_strategy import EnhancedOptimizedStrategy
from scripts.ultimate_strategy_analysis import run_comprehensive_analysis

def main():
    """Main test runner function"""
    print("🎯 Deep Backtesting Test Runner")
    print("=" * 50)
    
    # Initialize strategies
    print("\\n📊 Initializing Strategies...")
    ultra_strict = UltraStrictV3Strategy()
    enhanced = EnhancedOptimizedStrategy()
    
    print("✅ Strategies initialized")
    
    # Run comprehensive analysis
    print("\\n🔍 Running Comprehensive Analysis...")
    results = run_comprehensive_analysis()
    
    print("✅ Analysis complete")
    print(f"📈 Results saved to: results/comprehensive_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    return results

if __name__ == "__main__":
    main()
'''
    
    with open('run_deep_backtest.py', 'w') as f:
        f.write(runner_script)
    
    # Make executable
    os.chmod('run_deep_backtest.py', 0o755)
    print("✅ Created test runner: run_deep_backtest.py")

if __name__ == "__main__":
    setup_environment()
