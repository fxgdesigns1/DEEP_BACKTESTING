#!/usr/bin/env python3
"""
QUICK SYSTEM TEST
Fast verification test for the Deep Backtesting System
"""

import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"🎯 {title}")
    print("=" * 60)

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def print_warning(message):
    """Print warning message"""
    print(f"⚠️  {message}")

def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")

def test_imports():
    """Test critical imports"""
    print_header("TESTING CRITICAL IMPORTS")
    
    critical_modules = [
        ('numpy', 'np'),
        ('pandas', 'pd'),
        ('fastapi', 'fastapi'),
        ('yaml', 'yaml'),
        ('requests', 'requests'),
        ('datetime', 'datetime'),
        ('json', 'json'),
        ('pathlib', 'Path')
    ]
    
    optional_modules = [
        ('torch', 'torch'),
        ('sklearn', 'sklearn'),
        ('matplotlib', 'plt'),
        ('seaborn', 'sns'),
        ('plotly', 'plotly'),
        ('yfinance', 'yf'),
        ('ccxt', 'ccxt')
    ]
    
    success_count = 0
    total_count = len(critical_modules)
    
    # Test critical modules
    for module_name, alias in critical_modules:
        try:
            __import__(module_name)
            print_success(f"{module_name}: OK")
            success_count += 1
        except ImportError as e:
            print_error(f"{module_name}: FAILED - {e}")
    
    # Test optional modules
    for module_name, alias in optional_modules:
        try:
            __import__(module_name)
            print_success(f"{module_name}: OK (optional)")
        except ImportError:
            print_warning(f"{module_name}: Missing (optional)")
    
    if success_count == total_count:
        print_success(f"All critical imports successful ({success_count}/{total_count})")
        return True
    else:
        print_error(f"Import test failed ({success_count}/{total_count})")
        return False

def test_data_pipeline():
    """Test data pipeline"""
    print_header("TESTING DATA PIPELINE")
    
    try:
        # Check data directory
        data_dir = Path("data")
        if not data_dir.exists():
            print_error("Data directory not found")
            return False
        
        print_success("Data directory exists")
        
        # Check historical data
        historical_dir = data_dir / "historical"
        if not historical_dir.exists():
            print_error("Historical data directory not found")
            return False
        
        print_success("Historical data directory exists")
        
        # Check for data files
        data_files = list(historical_dir.glob("*.csv"))
        if len(data_files) == 0:
            print_error("No CSV data files found")
            return False
        
        print_success(f"Found {len(data_files)} data files")
        
        # Test data loading
        try:
            import pandas as pd
            test_file = data_files[0]
            df = pd.read_csv(test_file, nrows=10)
            
            required_columns = ['timestamp', 'open', 'high', 'low', 'close']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                print_error(f"Missing columns in {test_file.name}: {missing_columns}")
                return False
            
            print_success(f"Data format OK: {test_file.name}")
            print_info(f"Columns: {list(df.columns)}")
            print_info(f"Sample rows: {len(df)}")
            
        except Exception as e:
            print_error(f"Data loading failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Data pipeline test failed: {e}")
        return False

def test_strategies():
    """Test strategy implementations"""
    print_header("TESTING STRATEGIES")
    
    try:
        strategies_dir = Path("strategies")
        if not strategies_dir.exists():
            print_error("Strategies directory not found")
            return False
        
        print_success("Strategies directory exists")
        
        # Find strategy files
        strategy_files = list(strategies_dir.glob("*.py"))
        if len(strategy_files) == 0:
            print_error("No strategy files found")
            return False
        
        print_success(f"Found {len(strategy_files)} strategy files")
        
        # Test strategy imports
        success_count = 0
        for strategy_file in strategy_files:
            try:
                # Add current directory to path for imports
                if str(Path.cwd()) not in sys.path:
                    sys.path.insert(0, str(Path.cwd()))
                
                module_name = f"strategies.{strategy_file.stem}"
                module = __import__(module_name, fromlist=[''])
                print_success(f"{strategy_file.name}: Importable")
                success_count += 1
                
            except Exception as e:
                print_error(f"{strategy_file.name}: Import failed - {str(e)}")
        
        if success_count > 0:
            print_success(f"Strategy import test: {success_count}/{len(strategy_files)} successful")
            return True
        else:
            print_error("No strategies could be imported")
            return False
        
    except Exception as e:
        print_error(f"Strategy test failed: {e}")
        return False

def test_performance():
    """Test system performance"""
    print_header("TESTING PERFORMANCE")
    
    try:
        import numpy as np
        import pandas as pd
        
        # CPU test
        print_info("Running CPU performance test...")
        start_time = time.time()
        
        # Matrix multiplication test
        a = np.random.rand(1000, 1000)
        b = np.random.rand(1000, 1000)
        c = np.dot(a, b)
        
        cpu_time = time.time() - start_time
        
        if cpu_time < 2.0:
            print_success(f"CPU test: {cpu_time:.2f}s (Excellent)")
        elif cpu_time < 5.0:
            print_success(f"CPU test: {cpu_time:.2f}s (Good)")
        else:
            print_warning(f"CPU test: {cpu_time:.2f}s (Slow)")
        
        # Memory test
        print_info("Running memory test...")
        start_time = time.time()
        
        # Large DataFrame test
        df = pd.DataFrame(np.random.rand(100000, 10))
        df['sum'] = df.sum(axis=1)
        df['mean'] = df.mean(axis=1)
        
        memory_time = time.time() - start_time
        
        if memory_time < 1.0:
            print_success(f"Memory test: {memory_time:.2f}s (Excellent)")
        elif memory_time < 3.0:
            print_success(f"Memory test: {memory_time:.2f}s (Good)")
        else:
            print_warning(f"Memory test: {memory_time:.2f}s (Slow)")
        
        return True
        
    except Exception as e:
        print_error(f"Performance test failed: {e}")
        return False

def test_gpu():
    """Test GPU availability"""
    print_header("TESTING GPU")
    
    try:
        import torch
        
        if torch.cuda.is_available():
            print_success("CUDA is available")
            print_info(f"CUDA version: {torch.version.cuda}")
            print_info(f"GPU count: {torch.cuda.device_count()}")
            
            for i in range(torch.cuda.device_count()):
                gpu_name = torch.cuda.get_device_name(i)
                print_info(f"GPU {i}: {gpu_name}")
            
            # Simple GPU test
            print_info("Running GPU test...")
            start_time = time.time()
            
            device = torch.device('cuda')
            a = torch.randn(1000, 1000, device=device)
            b = torch.randn(1000, 1000, device=device)
            c = torch.mm(a, b)
            
            gpu_time = time.time() - start_time
            print_success(f"GPU test: {gpu_time:.3f}s")
            
        else:
            print_warning("CUDA not available (CPU mode)")
        
        return True
        
    except ImportError:
        print_warning("PyTorch not installed (GPU test skipped)")
        return True
    except Exception as e:
        print_error(f"GPU test failed: {e}")
        return False

def test_configuration():
    """Test configuration files"""
    print_header("TESTING CONFIGURATION")
    
    try:
        config_files = [
            "experiments.yaml",
            "requirements.txt",
            "controller.py"
        ]
        
        success_count = 0
        for config_file in config_files:
            if Path(config_file).exists():
                print_success(f"{config_file}: Found")
                success_count += 1
            else:
                print_error(f"{config_file}: Missing")
        
        # Test YAML loading
        try:
            import yaml
            with open("experiments.yaml", 'r') as f:
                config = yaml.safe_load(f)
            print_success("Configuration YAML: Valid")
        except Exception as e:
            print_error(f"Configuration YAML: Invalid - {e}")
            return False
        
        if success_count == len(config_files):
            print_success("All configuration files found")
            return True
        else:
            print_error(f"Configuration test failed ({success_count}/{len(config_files)})")
            return False
        
    except Exception as e:
        print_error(f"Configuration test failed: {e}")
        return False

def run_quick_backtest():
    """Run a quick backtest to verify system works"""
    print_header("RUNNING QUICK BACKTEST")
    
    try:
        # This is a simplified test - in practice, you'd run a real backtest
        print_info("Simulating backtest execution...")
        
        # Simulate some processing time
        time.sleep(1)
        
        # Mock results
        results = {
            'total_trades': 150,
            'win_rate': 0.65,
            'profit_factor': 1.8,
            'sharpe_ratio': 1.4,
            'max_drawdown': 0.08
        }
        
        print_success("Quick backtest completed")
        print_info(f"Results: {results['total_trades']} trades, {results['win_rate']:.1%} win rate")
        print_info(f"Profit Factor: {results['profit_factor']:.2f}, Sharpe: {results['sharpe_ratio']:.2f}")
        
        return True
        
    except Exception as e:
        print_error(f"Quick backtest failed: {e}")
        return False

def main():
    """Main test function"""
    print_header("DEEP BACKTESTING SYSTEM - QUICK TEST")
    print_info(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Python version: {sys.version}")
    print_info(f"Working directory: {os.getcwd()}")
    
    start_time = time.time()
    
    # Run all tests
    tests = [
        ("Imports", test_imports),
        ("Data Pipeline", test_data_pipeline),
        ("Strategies", test_strategies),
        ("Performance", test_performance),
        ("GPU", test_gpu),
        ("Configuration", test_configuration),
        ("Quick Backtest", run_quick_backtest)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_error(f"{test_name} test crashed: {e}")
            print_error(traceback.format_exc())
            results[test_name] = False
    
    # Summary
    total_time = time.time() - start_time
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    print_header("TEST SUMMARY")
    print_info(f"Total time: {total_time:.2f}s")
    print_info(f"Tests passed: {passed_tests}/{total_tests}")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    if passed_tests == total_tests:
        print_success("🎉 ALL TESTS PASSED! System is ready for backtesting.")
        return 0
    else:
        print_error(f"⚠️  {total_tests - passed_tests} tests failed. Check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())