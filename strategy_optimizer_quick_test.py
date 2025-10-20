#!/usr/bin/env python3
"""
Strategy Optimizer – Quick Test
Tests a small subset to verify the system works

Author: AI Trading System
Date: October 1, 2025
"""

import os
import pandas as pd
import json
import yaml
import logging
from datetime import datetime
from improved_backtesting_system_oct2025 import ImprovedBacktestingSystem

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# === QUICK TEST CONFIG ===
CONFIG_FILE = "backtesting_config_oct2025.yaml"
DATA_PATH = "data/MASTER_DATASET/"
RESULTS_PATH = "results/"

# Quick test: Just test 2 strategies on 2 pairs on 1 timeframe
TEST_STRATEGIES = ["ultra_strict_forex", "gold_scalping"]
TEST_INSTRUMENTS = ["eur_usd", "xau_usd"]
TEST_TIMEFRAMES = ["15m"]

def quick_test():
    """Run quick test"""
    logger.info("\n" + "="*80)
    logger.info("STRATEGY OPTIMIZER - QUICK TEST")
    logger.info("="*80 + "\n")
    
    results = []
    
    for strategy in TEST_STRATEGIES:
        for pair in TEST_INSTRUMENTS:
            for timeframe in TEST_TIMEFRAMES:
                logger.info(f"\nTesting: {strategy} | {pair.upper()} | {timeframe}")
                
                # Load data
                file_path = f"{DATA_PATH}{timeframe}/{pair}_{timeframe}.csv"
                
                if not os.path.exists(file_path):
                    logger.warning(f"File not found: {file_path}")
                    continue
                
                try:
                    df = pd.read_csv(file_path)
                    
                    # Set timestamp as index
                    if 'timestamp' in df.columns:
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
                        df.set_index('timestamp', inplace=True)
                    
                    logger.info(f"Loaded {len(df)} bars")
                    
                    # Run backtest
                    backtest = ImprovedBacktestingSystem(CONFIG_FILE)
                    backtest_results = backtest.run_backtest(
                        strategy_name=strategy,
                        df=df
                    )
                    
                    # Extract metrics
                    metrics = backtest_results.get('metrics', {})
                    quality = backtest_results.get('quality_stats', {})
                    
                    result = {
                        'strategy': strategy,
                        'pair': pair,
                        'timeframe': timeframe,
                        'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                        'total_return_pct': metrics.get('total_return_pct', 0),
                        'max_drawdown_pct': metrics.get('max_drawdown_pct', 0),
                        'win_rate': metrics.get('win_rate', 0),
                        'profit_factor': metrics.get('profit_factor', 0),
                        'total_trades': metrics.get('total_trades', 0),
                        'avg_quality_score': quality.get('avg_quality_score', 0)
                    }
                    results.append(result)
                    
                    logger.info(f"✅ Results:")
                    logger.info(f"   Sharpe: {result['sharpe_ratio']:.2f}")
                    logger.info(f"   Return: {result['total_return_pct']:.2f}%")
                    logger.info(f"   Win Rate: {result['win_rate']:.1f}%")
                    logger.info(f"   Trades: {result['total_trades']}")
                    
                except Exception as e:
                    logger.error(f"Error: {e}", exc_info=True)
    
    # Save results
    os.makedirs(RESULTS_PATH, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{RESULTS_PATH}quick_test_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=4)
    
    logger.info(f"\n📁 Results saved to {output_file}")
    logger.info("\n" + "="*80)
    logger.info("QUICK TEST COMPLETE")
    logger.info("="*80)
    
    return results

if __name__ == "__main__":
    quick_test()




