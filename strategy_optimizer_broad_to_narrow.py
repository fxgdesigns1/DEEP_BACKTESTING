#!/usr/bin/env python3
"""
Strategy Optimizer – Broad to Narrow Search
Uses your existing ImprovedBacktestingSystem + Config
No engine changes required – only feeds strategies/configs

Phase 1: Broad exploration across strategies, instruments, timeframes
Phase 2: Refined parameter optimization for survivors

Author: AI Trading System
Date: October 1, 2025
Version: 1.0
"""

import os
import pandas as pd
import numpy as np
import json
import yaml
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from improved_backtesting_system_oct2025 import ImprovedBacktestingSystem

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('strategy_optimizer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# === CONFIG ===
CONFIG_FILE = "backtesting_config_oct2025.yaml"
DATA_PATH = "data/MASTER_DATASET/"
RESULTS_PATH = "results/"

# Ensure results directory exists
os.makedirs(RESULTS_PATH, exist_ok=True)

# Strategy name mappings (config name -> display name)
STRATEGY_MAPPING = {
    "ultra_strict_forex": "Ultra Strict Forex",
    "gold_scalping": "Gold Scalping",
    "momentum_trading": "Momentum Trading"
}

# Strategies to test broadly
BROAD_STRATEGIES = [
    "ultra_strict_forex",     # Trend EMA crossover with HTF alignment
    "gold_scalping",          # Gold pullback scalper
    "momentum_trading"        # ADX/ATR momentum
]

# Instruments (lowercase with underscores for file paths)
INSTRUMENTS = [
    "eur_usd", "gbp_usd", "usd_jpy", "aud_usd",
    "usd_cad", "nzd_usd", "usd_chf", "eur_jpy",
    "gbp_jpy", "xau_usd"
]

# Timeframes (matching actual file structure)
TIMEFRAMES = ["15m", "1h", "4h", "1d"]

# === PHASE 1 FILTER CRITERIA (broad filter) ===
# RELAXED: Allow more strategies through to Phase 2
PHASE1_FILTERS = {
    "sharpe_ratio": 0.5,     # Very relaxed (was 1.5)
    "max_drawdown_pct": 50.0, # Very generous (was 20.0)
    "win_rate": 30.0,         # Low bar (was 45.0)
    "min_trades": 5,          # Very low (was 10)
    "profit_factor": 1.0      # Break-even (was 1.2)
}

# === PHASE 2 FILTER CRITERIA (refined survivors) ===
PHASE2_FILTERS = {
    "sharpe_ratio": 2.0,
    "max_drawdown_pct": 10.0,
    "win_rate": 55.0,
    "profit_factor": 2.0,
    "min_trades": 20
}


class StrategyOptimizer:
    """Broad-to-narrow strategy optimizer"""
    
    def __init__(self, config_file: str):
        """Initialize optimizer"""
        self.config_file = config_file
        self.base_config = self._load_config()
        self.results_phase1 = []
        self.results_phase2 = []
        
    def _load_config(self) -> Dict:
        """Load base configuration"""
        with open(self.config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_data(self, pair: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Load market data for a pair and timeframe"""
        file_path = f"{DATA_PATH}{timeframe}/{pair}_{timeframe}.csv"
        
        if not os.path.exists(file_path):
            logger.warning(f"Data file not found: {file_path}")
            return None
        
        try:
            df = pd.read_csv(file_path)
            
            # Ensure timestamp column exists and is datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            elif df.index.name == 'timestamp':
                df.index = pd.to_datetime(df.index)
            else:
                logger.error(f"No timestamp column found in {file_path}")
                return None
            
            # Ensure required columns exist
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"Missing required columns in {file_path}")
                return None
            
            logger.debug(f"Loaded {len(df)} bars from {file_path}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None
    
    def _meets_phase1_criteria(self, metrics: Dict) -> bool:
        """Check if results meet Phase 1 criteria"""
        try:
            return (
                metrics.get('sharpe_ratio', 0) >= PHASE1_FILTERS['sharpe_ratio'] and
                metrics.get('max_drawdown_pct', 100) <= PHASE1_FILTERS['max_drawdown_pct'] and
                metrics.get('win_rate', 0) >= PHASE1_FILTERS['win_rate'] and
                metrics.get('total_trades', 0) >= PHASE1_FILTERS['min_trades'] and
                metrics.get('profit_factor', 0) >= PHASE1_FILTERS['profit_factor']
            )
        except:
            return False
    
    def _meets_phase2_criteria(self, metrics: Dict) -> bool:
        """Check if results meet Phase 2 criteria"""
        try:
            return (
                metrics.get('sharpe_ratio', 0) >= PHASE2_FILTERS['sharpe_ratio'] and
                metrics.get('max_drawdown_pct', 100) <= PHASE2_FILTERS['max_drawdown_pct'] and
                metrics.get('win_rate', 0) >= PHASE2_FILTERS['win_rate'] and
                metrics.get('total_trades', 0) >= PHASE2_FILTERS['min_trades'] and
                metrics.get('profit_factor', 0) >= PHASE2_FILTERS['profit_factor']
            )
        except:
            return False
    
    def run_phase1(self) -> List[Dict]:
        """
        Phase 1: Broad Exploration
        Test all strategies across all instruments and timeframes
        """
        logger.info("\n" + "="*80)
        logger.info("PHASE 1: BROAD EXPLORATION")
        logger.info("="*80 + "\n")
        
        survivors = []
        total_tests = len(BROAD_STRATEGIES) * len(INSTRUMENTS) * len(TIMEFRAMES)
        current_test = 0
        
        for strategy in BROAD_STRATEGIES:
            for pair in INSTRUMENTS:
                for timeframe in TIMEFRAMES:
                    current_test += 1
                    logger.info(f"[{current_test}/{total_tests}] Testing {strategy} | {pair.upper()} | {timeframe}")
                    
                    # Load data
                    df = self._load_data(pair, timeframe)
                    if df is None or len(df) < 1000:
                        logger.warning(f"Insufficient data, skipping...")
                        continue
                    
                    try:
                        # Run backtest
                        backtest = ImprovedBacktestingSystem(self.config_file)
                        results = backtest.run_backtest(
                            strategy_name=strategy,
                            df=df
                        )
                        
                        # Extract metrics
                        metrics = results.get('metrics', {})
                        
                        # Check if meets Phase 1 criteria
                        if self._meets_phase1_criteria(metrics):
                            survivor = {
                                'strategy': strategy,
                                'pair': pair,
                                'timeframe': timeframe,
                                'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                                'max_drawdown_pct': metrics.get('max_drawdown_pct', 0),
                                'win_rate': metrics.get('win_rate', 0),
                                'profit_factor': metrics.get('profit_factor', 0),
                                'total_return_pct': metrics.get('total_return_pct', 0),
                                'total_trades': metrics.get('total_trades', 0),
                                'avg_quality_score': results.get('quality_stats', {}).get('avg_quality_score', 0)
                            }
                            survivors.append(survivor)
                            
                            logger.info(f"✔ SURVIVOR: Sharpe {survivor['sharpe_ratio']:.2f} | "
                                      f"Win Rate {survivor['win_rate']:.1f}% | "
                                      f"Drawdown {survivor['max_drawdown_pct']:.1f}%")
                        else:
                            logger.debug(f"✗ Failed filters")
                    
                    except Exception as e:
                        logger.error(f"Error running backtest: {e}")
                        continue
        
        self.results_phase1 = survivors
        logger.info(f"\n✅ Phase 1 Complete: {len(survivors)} survivors out of {total_tests} tests")
        
        return survivors
    
    def run_phase2(self, survivors: List[Dict]) -> List[Dict]:
        """
        Phase 2: Refinement
        Test parameter variations on survivors
        """
        logger.info("\n" + "="*80)
        logger.info("PHASE 2: REFINEMENT")
        logger.info("="*80 + "\n")
        
        if not survivors:
            logger.warning("No survivors from Phase 1 to refine!")
            return []
        
        refined = []
        
        # Parameter variations to test
        variations = {
            'risk_per_trade': [0.01, 0.015, 0.02, 0.025],
            'min_signal_quality': [50, 60, 70, 75],
            'min_time_between_trades': [15, 30, 45, 60]
        }
        
        total_variations = (len(variations['risk_per_trade']) * 
                           len(variations['min_signal_quality']) * 
                           len(variations['min_time_between_trades']))
        
        total_tests = len(survivors) * total_variations
        current_test = 0
        
        for survivor in survivors:
            strategy = survivor['strategy']
            pair = survivor['pair']
            timeframe = survivor['timeframe']
            
            logger.info(f"\nRefining survivor: {strategy} | {pair.upper()} | {timeframe}")
            
            # Load data once
            df = self._load_data(pair, timeframe)
            if df is None:
                continue
            
            for risk in variations['risk_per_trade']:
                for quality in variations['min_signal_quality']:
                    for time_spacing in variations['min_time_between_trades']:
                        current_test += 1
                        
                        logger.debug(f"[{current_test}/{total_tests}] "
                                   f"Risk: {risk*100:.1f}% | "
                                   f"Quality: {quality} | "
                                   f"Spacing: {time_spacing}m")
                        
                        try:
                            # Create modified config
                            modified_config = self.base_config.copy()
                            
                            # Update parameters in the config
                            strategy_config = modified_config['strategies'].get(strategy, {})
                            if 'risk' in strategy_config:
                                strategy_config['risk']['risk_per_trade_pct'] = risk
                            
                            if 'entry' in strategy_config:
                                strategy_config['entry']['min_signal_strength'] = quality / 100
                                strategy_config['entry']['min_time_between_trades_minutes'] = time_spacing
                            
                            # Save temporary config
                            temp_config_file = f"temp_config_{current_test}.yaml"
                            with open(temp_config_file, 'w') as f:
                                yaml.dump(modified_config, f)
                            
                            # Run backtest with modified config
                            backtest = ImprovedBacktestingSystem(temp_config_file)
                            results = backtest.run_backtest(
                                strategy_name=strategy,
                                df=df
                            )
                            
                            # Clean up temp config
                            if os.path.exists(temp_config_file):
                                os.remove(temp_config_file)
                            
                            # Extract metrics
                            metrics = results.get('metrics', {})
                            
                            # Check if meets Phase 2 criteria
                            if self._meets_phase2_criteria(metrics):
                                refined_result = {
                                    'strategy': strategy,
                                    'pair': pair,
                                    'timeframe': timeframe,
                                    'parameters': {
                                        'risk_per_trade': risk,
                                        'min_signal_quality': quality,
                                        'min_time_between_trades': time_spacing
                                    },
                                    'metrics': {
                                        'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                                        'max_drawdown_pct': metrics.get('max_drawdown_pct', 0),
                                        'win_rate': metrics.get('win_rate', 0),
                                        'profit_factor': metrics.get('profit_factor', 0),
                                        'total_return_pct': metrics.get('total_return_pct', 0),
                                        'total_trades': metrics.get('total_trades', 0)
                                    },
                                    'quality_stats': results.get('quality_stats', {})
                                }
                                refined.append(refined_result)
                                
                                logger.info(f"🔥 REFINED: Sharpe {refined_result['metrics']['sharpe_ratio']:.2f} | "
                                          f"Win Rate {refined_result['metrics']['win_rate']:.1f}%")
                        
                        except Exception as e:
                            logger.error(f"Error in refinement: {e}")
                            # Clean up temp config on error
                            temp_config_file = f"temp_config_{current_test}.yaml"
                            if os.path.exists(temp_config_file):
                                os.remove(temp_config_file)
                            continue
        
        self.results_phase2 = refined
        logger.info(f"\n✅ Phase 2 Complete: {len(refined)} optimized strategies found")
        
        return refined
    
    def save_results(self):
        """Save all results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save Phase 1 results
        phase1_file = f"{RESULTS_PATH}phase1_survivors_{timestamp}.json"
        with open(phase1_file, 'w') as f:
            json.dump(self.results_phase1, f, indent=4)
        logger.info(f"📁 Phase 1 results saved to {phase1_file}")
        
        # Save Phase 2 results
        phase2_file = f"{RESULTS_PATH}phase2_optimized_{timestamp}.json"
        with open(phase2_file, 'w') as f:
            json.dump(self.results_phase2, f, indent=4)
        logger.info(f"📁 Phase 2 results saved to {phase2_file}")
        
        # Save top performers
        if self.results_phase2:
            top_performers = sorted(
                self.results_phase2,
                key=lambda x: x['metrics']['sharpe_ratio'],
                reverse=True
            )[:10]
            
            top_file = f"{RESULTS_PATH}top_10_strategies_{timestamp}.json"
            with open(top_file, 'w') as f:
                json.dump(top_performers, f, indent=4)
            logger.info(f"📁 Top 10 strategies saved to {top_file}")
            
            # Print summary
            logger.info("\n" + "="*80)
            logger.info("TOP 10 STRATEGIES")
            logger.info("="*80)
            for i, strat in enumerate(top_performers, 1):
                logger.info(f"\n{i}. {STRATEGY_MAPPING.get(strat['strategy'], strat['strategy'])} | "
                          f"{strat['pair'].upper()} | {strat['timeframe']}")
                logger.info(f"   Sharpe: {strat['metrics']['sharpe_ratio']:.2f} | "
                          f"Win Rate: {strat['metrics']['win_rate']:.1f}% | "
                          f"Return: {strat['metrics']['total_return_pct']:.2f}%")
                logger.info(f"   Max DD: {strat['metrics']['max_drawdown_pct']:.1f}% | "
                          f"Profit Factor: {strat['metrics']['profit_factor']:.2f}")
                logger.info(f"   Parameters: Risk {strat['parameters']['risk_per_trade']*100:.1f}% | "
                          f"Quality {strat['parameters']['min_signal_quality']} | "
                          f"Spacing {strat['parameters']['min_time_between_trades']}m")
    
    def run_full_optimization(self):
        """Run complete optimization pipeline"""
        start_time = datetime.now()
        
        logger.info("\n" + "="*80)
        logger.info("STRATEGY OPTIMIZER: BROAD TO NARROW SEARCH")
        logger.info("="*80)
        logger.info(f"Start Time: {start_time}")
        logger.info(f"Config: {self.config_file}")
        logger.info(f"Strategies: {len(BROAD_STRATEGIES)}")
        logger.info(f"Instruments: {len(INSTRUMENTS)}")
        logger.info(f"Timeframes: {len(TIMEFRAMES)}")
        
        # Phase 1: Broad exploration
        survivors = self.run_phase1()
        
        # Phase 2: Refinement
        if survivors:
            refined = self.run_phase2(survivors)
        else:
            logger.warning("No survivors from Phase 1, skipping Phase 2")
            refined = []
        
        # Save results
        self.save_results()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("\n" + "="*80)
        logger.info("OPTIMIZATION COMPLETE")
        logger.info("="*80)
        logger.info(f"End Time: {end_time}")
        logger.info(f"Duration: {duration}")
        logger.info(f"Phase 1 Survivors: {len(survivors)}")
        logger.info(f"Phase 2 Optimized: {len(refined)}")
        logger.info("="*80 + "\n")


# === MAIN EXECUTION ===
if __name__ == "__main__":
    try:
        optimizer = StrategyOptimizer(CONFIG_FILE)
        optimizer.run_full_optimization()
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Optimization interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)

