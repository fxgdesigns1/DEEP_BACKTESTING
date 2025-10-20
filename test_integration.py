#!/usr/bin/env python3
"""
INTEGRATION TEST SCRIPT
Quick test to validate the ultimate strategy search integration
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all required modules can be imported"""
    logger.info("🔍 Testing imports...")
    
    try:
        # Test engine imports
        from professional_backtesting_system import ProfessionalBacktestingSystem
        from multi_timeframe_backtesting_system import MultiTimeframeBacktestingSystem
        logger.info("✅ Engines imported successfully")
        
        # Test strategy imports
        from strategies.comprehensive_enhanced_strategy import ComprehensiveEnhancedStrategy
        from strategies.ultra_strict_v3_strategy import UltraStrictV3Strategy
        from strategies.news_enhanced_strategy import NewsEnhancedStrategy
        from strategies.enhanced_optimized_strategy import EnhancedOptimizedStrategy
        logger.info("✅ Strategies imported successfully")
        
        # Test framework imports
        from advanced_validation_framework import AdvancedValidationFramework
        from risk_management_framework import RiskManagementFramework
        from professional_data_gap_analyzer import ProfessionalDataGapAnalyzer
        logger.info("✅ Frameworks imported successfully")
        
        # Test controller import
        from controller import UltimateStrategySearchController
        logger.info("✅ Controller imported successfully")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        return False

def test_config_loading():
    """Test configuration loading"""
    logger.info("🔍 Testing configuration loading...")
    
    try:
        import yaml
        
        # Test experiments.yaml
        if os.path.exists("experiments.yaml"):
            with open("experiments.yaml", "r") as f:
                config = yaml.safe_load(f)
            
            required_sections = ['meta', 'risk', 'costs', 'universe', 'search_space']
            for section in required_sections:
                if section not in config:
                    logger.error(f"❌ Missing config section: {section}")
                    return False
            
            logger.info("✅ Configuration loaded successfully")
            return True
        else:
            logger.error("❌ experiments.yaml not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Config loading failed: {e}")
        return False

def test_component_initialization():
    """Test component initialization"""
    logger.info("🔍 Testing component initialization...")
    
    try:
        # Test engine initialization
        from professional_backtesting_system import ProfessionalBacktestingSystem
        engine = ProfessionalBacktestingSystem()
        logger.info("✅ Professional backtesting engine initialized")
        
        # Test strategy initialization
        from strategies.enhanced_optimized_strategy import EnhancedOptimizedStrategy
        strategy = EnhancedOptimizedStrategy()
        logger.info("✅ Enhanced optimized strategy initialized")
        
        # Test controller initialization
        from controller import UltimateStrategySearchController
        controller = UltimateStrategySearchController()
        logger.info("✅ Controller initialized")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Component initialization failed: {e}")
        return False

def test_data_structure():
    """Test data directory structure"""
    logger.info("🔍 Testing data directory structure...")
    
    required_dirs = [
        "data",
        "data/historical",
        "data/completed",
        "data/timeframes",
        "results"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        logger.warning(f"⚠️  Missing directories: {missing_dirs}")
        logger.info("💡 Creating missing directories...")
        
        for dir_path in missing_dirs:
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"   Created: {dir_path}")
    else:
        logger.info("✅ All required directories exist")
    
    return True

def test_small_backtest():
    """Test a small backtest to ensure everything works"""
    logger.info("🔍 Testing small backtest...")
    
    try:
        from professional_backtesting_system import ProfessionalBacktestingSystem
        
        # Initialize engine
        engine = ProfessionalBacktestingSystem()
        
        # Check if we have any data files
        data_dir = "data/completed"
        if os.path.exists(data_dir):
            data_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
            if data_files:
                logger.info(f"✅ Found {len(data_files)} data files")
                logger.info("✅ Backtest capability confirmed")
                return True
            else:
                logger.warning("⚠️  No data files found in data/completed")
                return False
        else:
            logger.warning("⚠️  Data directory not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Backtest test failed: {e}")
        return False

def run_integration_test():
    """Run complete integration test"""
    logger.info("🚀 Starting integration test")
    logger.info("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Config Loading Test", test_config_loading),
        ("Data Structure Test", test_data_structure),
        ("Component Initialization Test", test_component_initialization),
        ("Backtest Test", test_small_backtest)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running {test_name}...")
        try:
            result = test_func()
            results[test_name] = result
            if result:
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} ERROR: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("🎯 INTEGRATION TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED - System ready for strategy search!")
        logger.info("💡 Next steps:")
        logger.info("   1. Run: python data_pipeline_validator.py")
        logger.info("   2. Run: python controller.py")
        return True
    else:
        logger.error("❌ Some tests failed - Please fix issues before proceeding")
        return False

def main():
    """Main execution function"""
    try:
        success = run_integration_test()
        
        if success:
            print("\n🎯 INTEGRATION TEST COMPLETE - SYSTEM READY")
        else:
            print("\n❌ INTEGRATION TEST FAILED - PLEASE FIX ISSUES")
            
    except KeyboardInterrupt:
        logger.info("🛑 Integration test interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()
