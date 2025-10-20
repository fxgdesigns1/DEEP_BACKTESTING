#!/usr/bin/env python3
"""
SYSTEM VERIFICATION AND HEALTH CHECK
Comprehensive verification system for the Deep Backtesting environment
"""

import os
import sys
import json
import subprocess
import importlib
import platform
import psutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class SystemVerification:
    """Comprehensive system verification and health check"""
    
    def __init__(self, install_path: str = None):
        self.install_path = install_path or os.getcwd()
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {},
            'python_environment': {},
            'dependencies': {},
            'data_pipeline': {},
            'strategies': {},
            'performance': {},
            'gpu': {},
            'overall_status': 'UNKNOWN',
            'issues': [],
            'recommendations': []
        }
        
    def run_comprehensive_verification(self) -> Dict[str, Any]:
        """Run complete system verification"""
        print("🔍 Starting Comprehensive System Verification...")
        print("=" * 60)
        
        try:
            # System information
            self._check_system_info()
            
            # Python environment
            self._check_python_environment()
            
            # Dependencies
            self._check_dependencies()
            
            # Data pipeline
            self._check_data_pipeline()
            
            # Strategies
            self._check_strategies()
            
            # Performance
            self._check_performance()
            
            # GPU
            self._check_gpu()
            
            # Overall assessment
            self._assess_overall_status()
            
            # Generate report
            self._generate_report()
            
            return self.results
            
        except Exception as e:
            self.results['overall_status'] = 'ERROR'
            self.results['issues'].append(f"Verification failed: {str(e)}")
            print(f"❌ Verification failed: {e}")
            return self.results
    
    def _check_system_info(self):
        """Check system information"""
        print("📊 Checking System Information...")
        
        try:
            self.results['system_info'] = {
                'platform': platform.platform(),
                'architecture': platform.architecture(),
                'processor': platform.processor(),
                'python_version': sys.version,
                'python_executable': sys.executable,
                'cpu_count': psutil.cpu_count(),
                'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_usage': psutil.disk_usage('/')._asdict() if os.name != 'nt' else psutil.disk_usage('C:')._asdict(),
                'install_path': self.install_path,
                'working_directory': os.getcwd()
            }
            
            # Check system requirements
            memory_gb = self.results['system_info']['memory_total'] / (1024**3)
            if memory_gb < 16:
                self.results['issues'].append(f"Insufficient RAM: {memory_gb:.1f}GB (minimum 16GB recommended)")
            
            cpu_count = self.results['system_info']['cpu_count']
            if cpu_count < 8:
                self.results['issues'].append(f"Low CPU core count: {cpu_count} (8+ cores recommended)")
            
            print(f"✅ System: {platform.platform()}")
            print(f"✅ CPU: {cpu_count} cores")
            print(f"✅ RAM: {memory_gb:.1f}GB")
            
        except Exception as e:
            self.results['issues'].append(f"System info check failed: {str(e)}")
            print(f"❌ System info check failed: {e}")
    
    def _check_python_environment(self):
        """Check Python environment"""
        print("🐍 Checking Python Environment...")
        
        try:
            # Python version
            python_version = sys.version_info
            self.results['python_environment']['version'] = f"{python_version.major}.{python_version.minor}.{python_version.micro}"
            self.results['python_environment']['version_info'] = python_version._asdict()
            
            if python_version < (3, 8):
                self.results['issues'].append(f"Python version too old: {python_version.major}.{python_version.minor} (3.8+ required)")
            
            # Virtual environment
            in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
            self.results['python_environment']['virtual_environment'] = in_venv
            self.results['python_environment']['prefix'] = sys.prefix
            
            if not in_venv:
                self.results['issues'].append("Not running in virtual environment (recommended)")
            
            # PATH
            self.results['python_environment']['path'] = sys.path[:5]  # First 5 entries
            
            print(f"✅ Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
            print(f"✅ Virtual Environment: {'Yes' if in_venv else 'No'}")
            
        except Exception as e:
            self.results['issues'].append(f"Python environment check failed: {str(e)}")
            print(f"❌ Python environment check failed: {e}")
    
    def _check_dependencies(self):
        """Check Python dependencies"""
        print("📦 Checking Dependencies...")
        
        # Core dependencies
        core_packages = [
            'numpy', 'pandas', 'fastapi', 'uvicorn', 'aiohttp',
            'python-dotenv', 'pyyaml', 'requests', 'python-dateutil',
            'pytz', 'scikit-learn', 'scipy', 'matplotlib', 'seaborn',
            'plotly', 'yfinance', 'ccxt', 'sqlalchemy', 'redis',
            'numba', 'joblib', 'tqdm', 'pytest', 'jupyter'
        ]
        
        # Optional dependencies
        optional_packages = [
            'torch', 'ta-lib', 'alpha-vantage', 'fredapi',
            'psutil', 'schedule', 'python-telegram-bot', 'discord'
        ]
        
        self.results['dependencies'] = {
            'core': {},
            'optional': {},
            'missing_core': [],
            'missing_optional': []
        }
        
        # Check core packages
        for package in core_packages:
            try:
                module = importlib.import_module(package)
                version = getattr(module, '__version__', 'Unknown')
                self.results['dependencies']['core'][package] = version
                print(f"✅ {package}: {version}")
            except ImportError:
                self.results['dependencies']['missing_core'].append(package)
                self.results['issues'].append(f"Missing core package: {package}")
                print(f"❌ {package}: Missing")
        
        # Check optional packages
        for package in optional_packages:
            try:
                module = importlib.import_module(package)
                version = getattr(module, '__version__', 'Unknown')
                self.results['dependencies']['optional'][package] = version
                print(f"✅ {package}: {version}")
            except ImportError:
                self.results['dependencies']['missing_optional'].append(package)
                print(f"⚠️  {package}: Missing (optional)")
        
        # Check pip packages
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.results['dependencies']['pip_list'] = result.stdout
            else:
                self.results['issues'].append("Failed to get pip package list")
        except Exception as e:
            self.results['issues'].append(f"Pip list check failed: {str(e)}")
    
    def _check_data_pipeline(self):
        """Check data pipeline"""
        print("📊 Checking Data Pipeline...")
        
        try:
            data_dir = Path(self.install_path) / "data"
            historical_dir = data_dir / "historical"
            
            self.results['data_pipeline'] = {
                'data_directory_exists': data_dir.exists(),
                'historical_directory_exists': historical_dir.exists(),
                'data_files': [],
                'total_files': 0,
                'total_size_mb': 0,
                'data_quality': {}
            }
            
            if not data_dir.exists():
                self.results['issues'].append("Data directory not found")
                return
            
            if not historical_dir.exists():
                self.results['issues'].append("Historical data directory not found")
                return
            
            # Check data files
            data_files = list(historical_dir.glob("*.csv"))
            self.results['data_pipeline']['total_files'] = len(data_files)
            
            total_size = 0
            for file_path in data_files:
                file_size = file_path.stat().st_size
                total_size += file_size
                
                file_info = {
                    'name': file_path.name,
                    'size_mb': file_size / (1024 * 1024),
                    'exists': True
                }
                
                # Quick data quality check
                try:
                    import pandas as pd
                    df = pd.read_csv(file_path, nrows=5)
                    file_info['columns'] = list(df.columns)
                    file_info['sample_rows'] = len(df)
                    file_info['data_quality'] = 'OK'
                except Exception as e:
                    file_info['data_quality'] = f'Error: {str(e)}'
                    self.results['issues'].append(f"Data quality issue in {file_path.name}: {str(e)}")
                
                self.results['data_pipeline']['data_files'].append(file_info)
            
            self.results['data_pipeline']['total_size_mb'] = total_size / (1024 * 1024)
            
            print(f"✅ Data files: {len(data_files)}")
            print(f"✅ Total size: {self.results['data_pipeline']['total_size_mb']:.1f}MB")
            
            if len(data_files) < 5:
                self.results['issues'].append(f"Low data file count: {len(data_files)} (5+ recommended)")
            
        except Exception as e:
            self.results['issues'].append(f"Data pipeline check failed: {str(e)}")
            print(f"❌ Data pipeline check failed: {e}")
    
    def _check_strategies(self):
        """Check strategy implementations"""
        print("🎯 Checking Strategies...")
        
        try:
            strategies_dir = Path(self.install_path) / "strategies"
            self.results['strategies'] = {
                'strategies_directory_exists': strategies_dir.exists(),
                'strategy_files': [],
                'importable_strategies': [],
                'import_errors': []
            }
            
            if not strategies_dir.exists():
                self.results['issues'].append("Strategies directory not found")
                return
            
            # Find strategy files
            strategy_files = list(strategies_dir.glob("*.py"))
            self.results['strategies']['strategy_files'] = [f.name for f in strategy_files]
            
            # Test strategy imports
            for strategy_file in strategy_files:
                module_name = f"strategies.{strategy_file.stem}"
                try:
                    # Add strategies directory to path
                    if str(strategies_dir.parent) not in sys.path:
                        sys.path.insert(0, str(strategies_dir.parent))
                    
                    module = importlib.import_module(module_name)
                    self.results['strategies']['importable_strategies'].append(strategy_file.name)
                    print(f"✅ {strategy_file.name}: Importable")
                except Exception as e:
                    self.results['strategies']['import_errors'].append({
                        'file': strategy_file.name,
                        'error': str(e)
                    })
                    print(f"❌ {strategy_file.name}: Import failed - {str(e)}")
            
            if len(self.results['strategies']['importable_strategies']) == 0:
                self.results['issues'].append("No strategies could be imported")
            
        except Exception as e:
            self.results['issues'].append(f"Strategies check failed: {str(e)}")
            print(f"❌ Strategies check failed: {e}")
    
    def _check_performance(self):
        """Check system performance"""
        print("⚡ Checking Performance...")
        
        try:
            # CPU performance test
            start_time = time.time()
            import numpy as np
            # Simple matrix multiplication test
            a = np.random.rand(1000, 1000)
            b = np.random.rand(1000, 1000)
            c = np.dot(a, b)
            cpu_time = time.time() - start_time
            
            self.results['performance'] = {
                'cpu_test_time': cpu_time,
                'cpu_test_status': 'OK' if cpu_time < 5.0 else 'SLOW',
                'memory_usage_mb': psutil.Process().memory_info().rss / (1024 * 1024),
                'cpu_percent': psutil.cpu_percent(interval=1)
            }
            
            if cpu_time > 5.0:
                self.results['issues'].append(f"CPU performance slow: {cpu_time:.2f}s (should be <5s)")
            
            print(f"✅ CPU test: {cpu_time:.2f}s")
            print(f"✅ Memory usage: {self.results['performance']['memory_usage_mb']:.1f}MB")
            
        except Exception as e:
            self.results['issues'].append(f"Performance check failed: {str(e)}")
            print(f"❌ Performance check failed: {e}")
    
    def _check_gpu(self):
        """Check GPU availability"""
        print("🎮 Checking GPU...")
        
        try:
            self.results['gpu'] = {
                'torch_available': False,
                'cuda_available': False,
                'cuda_version': None,
                'gpu_count': 0,
                'gpu_names': []
            }
            
            # Check PyTorch
            try:
                import torch
                self.results['gpu']['torch_available'] = True
                self.results['gpu']['cuda_available'] = torch.cuda.is_available()
                
                if torch.cuda.is_available():
                    self.results['gpu']['cuda_version'] = torch.version.cuda
                    self.results['gpu']['gpu_count'] = torch.cuda.device_count()
                    
                    for i in range(torch.cuda.device_count()):
                        gpu_name = torch.cuda.get_device_name(i)
                        self.results['gpu']['gpu_names'].append(gpu_name)
                    
                    print(f"✅ CUDA: Available (v{self.results['gpu']['cuda_version']})")
                    print(f"✅ GPUs: {self.results['gpu']['gpu_count']}")
                    for i, name in enumerate(self.results['gpu']['gpu_names']):
                        print(f"   GPU {i}: {name}")
                else:
                    print("⚠️  CUDA: Not available (CPU mode)")
                    
            except ImportError:
                self.results['issues'].append("PyTorch not available")
                print("❌ PyTorch: Not installed")
            
        except Exception as e:
            self.results['issues'].append(f"GPU check failed: {str(e)}")
            print(f"❌ GPU check failed: {e}")
    
    def _assess_overall_status(self):
        """Assess overall system status"""
        print("📋 Assessing Overall Status...")
        
        critical_issues = 0
        warning_issues = 0
        
        for issue in self.results['issues']:
            if any(keyword in issue.lower() for keyword in ['missing core', 'failed', 'not found', 'too old']):
                critical_issues += 1
            else:
                warning_issues += 1
        
        if critical_issues == 0 and warning_issues == 0:
            self.results['overall_status'] = 'EXCELLENT'
        elif critical_issues == 0:
            self.results['overall_status'] = 'GOOD'
        elif critical_issues <= 2:
            self.results['overall_status'] = 'FAIR'
        else:
            self.results['overall_status'] = 'POOR'
        
        # Generate recommendations
        if self.results['overall_status'] in ['FAIR', 'POOR']:
            self.results['recommendations'].append("Run 'pip install -r requirements.txt' to install missing packages")
        
        if not self.results['python_environment'].get('virtual_environment', False):
            self.results['recommendations'].append("Consider using a virtual environment for better isolation")
        
        if self.results['gpu'].get('cuda_available', False) == False:
            self.results['recommendations'].append("Install PyTorch with CUDA support for GPU acceleration")
        
        print(f"✅ Overall Status: {self.results['overall_status']}")
        print(f"✅ Critical Issues: {critical_issues}")
        print(f"✅ Warnings: {warning_issues}")
    
    def _generate_report(self):
        """Generate verification report"""
        print("\n" + "=" * 60)
        print("📊 VERIFICATION REPORT")
        print("=" * 60)
        
        # Save detailed report
        report_path = Path(self.install_path) / "verification_report.json"
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Print summary
        print(f"Overall Status: {self.results['overall_status']}")
        print(f"System: {self.results['system_info'].get('platform', 'Unknown')}")
        print(f"Python: {self.results['python_environment'].get('version', 'Unknown')}")
        print(f"Core Packages: {len(self.results['dependencies'].get('core', {}))}")
        print(f"Data Files: {self.results['data_pipeline'].get('total_files', 0)}")
        print(f"Strategies: {len(self.results['strategies'].get('importable_strategies', []))}")
        print(f"GPU: {'Available' if self.results['gpu'].get('cuda_available', False) else 'Not Available'}")
        
        if self.results['issues']:
            print(f"\nIssues Found ({len(self.results['issues'])}):")
            for i, issue in enumerate(self.results['issues'], 1):
                print(f"  {i}. {issue}")
        
        if self.results['recommendations']:
            print(f"\nRecommendations ({len(self.results['recommendations'])}):")
            for i, rec in enumerate(self.results['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        print(f"\nDetailed report saved to: {report_path}")
        
        return report_path

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='System Verification for Deep Backtesting')
    parser.add_argument('--path', '-p', default=None, help='Installation path')
    parser.add_argument('--output', '-o', default=None, help='Output report path')
    
    args = parser.parse_args()
    
    verifier = SystemVerification(args.path)
    results = verifier.run_comprehensive_verification()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Report saved to: {args.output}")
    
    # Exit with appropriate code
    if results['overall_status'] in ['EXCELLENT', 'GOOD']:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
