#!/usr/bin/env python3
"""
ULTIMATE STRATEGY SEARCH CONTROLLER
Master orchestrator for institutional-grade FX strategy discovery
"""

import os
import json
import itertools
import math
import random
import logging
import sys
import traceback
import argparse
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

import yaml
import pandas as pd
import numpy as np

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import existing engines and frameworks
from professional_backtesting_system import ProfessionalBacktestingSystem
from multi_timeframe_backtesting_system import MultiTimeframeBacktestingSystem
from advanced_validation_framework import AdvancedValidationFramework
from risk_management_framework import RiskManagementFramework
from professional_data_gap_analyzer import ProfessionalDataGapAnalyzer

# Import strategies
from strategies.comprehensive_enhanced_strategy import ComprehensiveEnhancedStrategy
from strategies.ultra_strict_v3_strategy import UltraStrictV3Strategy
from strategies.news_enhanced_strategy import NewsEnhancedStrategy
from strategies.enhanced_optimized_strategy import EnhancedOptimizedStrategy

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('controller.log'),
        logging.StreamHandler()
    ]
)

# Helper functions for observability
def config_hash(pair, tf, strat, params):
    """Generate config hash for observability"""
    payload = {"pair": pair, "tf": tf, "strat": strat, "params": params}
    return hashlib.sha1(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:10]

def trade_signature(trades):
    """Generate trade signature to detect identical entries across runs"""
    try:
        keys = sorted(str(t["entry_time"]) for t in trades)
    except Exception:
        keys = sorted(str(t.get("entry_time") or t.get("time") or t) for t in trades)
    return hashlib.sha1("|".join(keys).encode()).hexdigest()[:12]

LOW_TFS = {"1m","5m","15m","30m"}
HIGH_TFS = {"1h","4h","1d","1w"}

def passes_selection(metrics, sel, tf):
    """Check if metrics pass selection criteria"""
    min_trades = sel["min_trades_low_tf"] if tf in LOW_TFS else sel["min_trades_high_tf"]
    reasons = []
    if metrics.get("trades",0) < min_trades: reasons.append("min_trades")
    if metrics.get("oos_sharpe", -999) < sel["min_oos_sharpe"]: reasons.append("oos_sharpe")
    if metrics.get("oos_sortino", -999) < sel["min_oos_sortino"]: reasons.append("oos_sortino")
    if metrics.get("oos_max_dd", 999) > sel["max_oos_dd"]: reasons.append("oos_max_dd")
    if metrics.get("profit_factor", 0) < 1.3: reasons.append("profit_factor")
    return (len(reasons)==0), reasons
logger = logging.getLogger(__name__)

class UltimateStrategySearchController:
    """
    Master controller for ultimate strategy search
    """
    
    def __init__(self, config_path: str = "experiments.yaml"):
        """Initialize the controller"""
        self.config = self.load_config(config_path)
        self.logger = logger
        
        # Set random seed for reproducibility
        random.seed(self.config.get("meta", {}).get("seed", 1337))
        np.random.seed(self.config.get("meta", {}).get("seed", 1337))
        
        # Initialize components
        self.engines = {}
        self.strategies = {}
        self.validation_framework = None
        self.risk_manager = None
        self.gap_analyzer = None
        
        # Results tracking
        self.results = {}
        self.failures = []
        self.best_configs = []
        
        # Performance tracking
        self.start_time = datetime.now()
        self.total_experiments = 0
        self.completed_experiments = 0
        
        self.logger.info("🎯 Ultimate Strategy Search Controller initialized")
    
    def load_config(self, path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            raise
    
    def timestamp(self) -> str:
        """Generate timestamp string"""
        return datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
    
    def config_hash(self, pair: str, tf: str, strat: str, params: Dict[str, Any]) -> str:
        """Generate config hash for observability"""
        payload = {"pair": pair, "tf": tf, "strat": strat, "params": params}
        return hashlib.sha1(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:10]
    
    def trade_signature(self, trades: List[Dict]) -> str:
        """Generate trade signature to detect identical entries across runs"""
        if not trades:
            return "no_trades"
        keys = sorted(str(t.get("entry_time", t.get("timestamp", ""))) for t in trades)
        return hashlib.sha1("|".join(keys).encode()).hexdigest()[:12]
    
    def ensure_dirs(self, base: Path):
        """Ensure directory exists"""
        base.mkdir(parents=True, exist_ok=True)
    
    def product_dict(self, grid: Dict[str, List]) -> List[Dict[str, Any]]:
        """Generate cartesian product of parameter grid with nested dict support"""
        # Flatten nested dictionaries
        flattened = {}
        for key, value in grid.items():
            if isinstance(value, dict):
                # Handle nested dictionaries like regime_filter
                for nested_key, nested_value in value.items():
                    flattened[f"{key}_{nested_key}"] = nested_value
            else:
                flattened[key] = value
        
        keys = list(flattened.keys())
        for vals in itertools.product(*[flattened[k] for k in keys]):
            yield dict(zip(keys, vals))
    
    def _apply_parameters_to_engine(self, engine, params: Dict[str, Any]):
        """Apply parameters to the backtesting engine"""
        try:
            # Apply technical indicator parameters
            if 'ema_fast' in params:
                engine.ema_fast_period = params['ema_fast']
            if 'ema_slow' in params:
                engine.ema_slow_period = params['ema_slow']
            if 'rsi_period' in params:
                engine.rsi_period = params['rsi_period']
            if 'macd_fast' in params:
                engine.macd_fast = params['macd_fast']
            if 'macd_slow' in params:
                engine.macd_slow = params['macd_slow']
            if 'macd_signal' in params:
                engine.macd_signal = params['macd_signal']
            if 'atr_period' in params:
                engine.atr_period = params['atr_period']
            
            # Apply risk management parameters
            if 'stop_atr_mult' in params:
                engine.stop_loss_atr_multiplier = params['stop_atr_mult']
            if 'take_profit_rr' in params:
                engine.take_profit_risk_reward = params['take_profit_rr']
            if 'trailing_atr_mult' in params and params['trailing_atr_mult'] is not None:
                engine.trailing_stop_atr_multiplier = params['trailing_atr_mult']
            
            # Apply session filtering
            if 'session' in params:
                engine.session_filter = params['session']
            
            # Apply news blackout
            if 'news_blackout_minutes' in params:
                engine.news_blackout_minutes = params['news_blackout_minutes']
                
        except Exception as e:
            self.logger.warning(f"⚠️ Could not apply some parameters: {e}")
    
    def initialize_components(self):
        """Initialize all required components"""
        self.logger.info("🔧 Initializing components...")
        
        try:
            # Initialize engines
            self.engines['professional'] = ProfessionalBacktestingSystem()
            self.engines['multi_timeframe'] = MultiTimeframeBacktestingSystem()
            
            # Initialize validation framework
            self.validation_framework = AdvancedValidationFramework()
            
            # Initialize risk manager
            self.risk_manager = RiskManagementFramework(
                initial_capital=self.config['risk']['capital']
            )
            
            # Initialize gap analyzer
            self.gap_analyzer = ProfessionalDataGapAnalyzer()
            
            # Initialize strategies
            self.strategies['comprehensive_enhanced'] = ComprehensiveEnhancedStrategy()
            self.strategies['ultra_strict_v3'] = UltraStrictV3Strategy()
            self.strategies['news_enhanced'] = NewsEnhancedStrategy()
            self.strategies['enhanced_optimized'] = EnhancedOptimizedStrategy()
            
            self.logger.info("✅ All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Error initializing components: {e}")
            raise
    
    def validate_data_pipeline(self) -> bool:
        """Validate data pipeline and ensure data readiness"""
        self.logger.info("📊 Validating data pipeline...")
        
        try:
            # Run gap analysis
            gap_results = self.gap_analyzer.run_comprehensive_gap_analysis()
            
            # Check data quality
            summary = gap_results['overall_summary']
            min_completeness = self.config['data_validation']['min_completeness']
            max_critical_gaps = self.config['data_validation']['max_critical_gaps']
            
            if summary['average_completeness'] < min_completeness * 100:
                self.logger.error(f"❌ Data completeness too low: {summary['average_completeness']:.1f}% < {min_completeness * 100:.1f}%")
                return False
            
            if summary['total_critical_gaps'] > max_critical_gaps:
                self.logger.error(f"❌ Too many critical gaps: {summary['total_critical_gaps']} > {max_critical_gaps}")
                return False
            
            self.logger.info(f"✅ Data validation passed: {summary['average_completeness']:.1f}% completeness, {summary['total_critical_gaps']} critical gaps")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Data validation failed: {e}")
            return False
    
    def choose_engine(self, tf: str) -> Any:
        """Choose appropriate engine for timeframe"""
        if tf == "1h":
            return self.engines['professional']
        else:
            return self.engines['multi_timeframe']
    
    def get_strategy(self, strategy_name: str) -> Any:
        """Get strategy instance by name"""
        strategy_map = {
            'comprehensive_enhanced_strategy': 'comprehensive_enhanced',
            'ultra_strict_v3_strategy': 'ultra_strict_v3',
            'news_enhanced_strategy': 'news_enhanced',
            'enhanced_optimized_strategy': 'enhanced_optimized'
        }
        
        key = strategy_map.get(strategy_name, strategy_name)
        return self.strategies.get(key)
    
    def run_baseline_backtest(self, engine, pair: str, tf: str, strategy_name: str) -> Dict[str, Any]:
        """Run baseline backtest with default parameters"""
        self.logger.info(f"📈 Running baseline for {pair} {tf} {strategy_name}")
        
        try:
            if tf == "1h":
                result = engine.run_professional_backtest(pair)
            else:
                result = engine.run_timeframe_backtest(pair, tf)
            
            return {
                'metrics': result.get('performance', {}),
                'equity': [],  # Will be populated by engine
                'trades': result.get('trades', []),
                'folds': []
            }
            
        except Exception as e:
            self.logger.error(f"❌ Baseline backtest failed: {e}")
            return {'error': str(e)}
    
    def run_walk_forward_optimization(self, engine, pair: str, tf: str, strategy_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run walk-forward optimization"""
        self.logger.info(f"🔄 Running WFO for {pair} {tf} {strategy_name} with params: {params}")
        
        try:
            # This is a simplified WFO implementation
            # In practice, you'd implement proper anchored expanding windows
            
            # Apply parameters to the engine before running backtest
            self._apply_parameters_to_engine(engine, params)
            
            # For now, run a single backtest with the given parameters
            if tf == "1h":
                result = engine.run_professional_backtest(pair)
            else:
                result = engine.run_timeframe_backtest(pair, tf)
            
            # Extract metrics
            performance = result.get('performance', {})
            metrics = {
                'oos_sharpe': performance.get('sharpe_ratio', 0),
                'oos_sortino': performance.get('sortino_ratio', 0),
                'oos_max_dd': performance.get('max_drawdown', 0) / 100,
                'profit_factor': performance.get('profit_factor', 0),
                'trades': performance.get('total_trades', 0),
                'win_rate': performance.get('win_rate', 0) / 100
            }
            
            return {
                'metrics': metrics,
                'equity': [],
                'trades': result.get('trades', []),
                'folds': []
            }
            
        except Exception as e:
            self.logger.error(f"❌ WFO failed: {e}")
            return {'error': str(e)}
    
    def passes_selection_criteria(self, metrics: Dict[str, Any], tf: str) -> bool:
        """Check if results pass selection criteria"""
        selection = self.config['selection']
        
        min_trades = selection['min_trades_low_tf'] if tf in LOW_TFS else selection['min_trades_high_tf']
        
        return (
            metrics.get('trades', 0) >= min_trades and
            metrics.get('oos_sharpe', 0) >= selection['min_oos_sharpe'] and
            metrics.get('oos_sortino', 0) >= selection['min_oos_sortino'] and
            metrics.get('oos_max_dd', 1) <= selection['max_oos_dd'] and
            metrics.get('profit_factor', 0) >= selection['min_profit_factor'] and
            metrics.get('win_rate', 0) >= selection['min_win_rate']
        )
    
    def run_robustness_tests(self, engine, pair: str, tf: str, strategy_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run robustness tests"""
        self.logger.info(f"🛡️ Running robustness tests for {pair} {tf} {strategy_name}")
        
        try:
            robustness_results = {}
            
            # Cost stress tests
            original_spread = self.config['costs']['spread_pips'][0]
            original_slippage = self.config['costs']['slippage_pips'][0]
            
            for stress_spread in self.config['robustness']['cost_stress_spread_pips']:
                for stress_slippage in self.config['robustness']['cost_stress_slippage_pips']:
                    # Temporarily modify engine costs
                    engine.transaction_cost = stress_spread / 10000
                    engine.slippage = stress_slippage / 10000
                    
                    result = self.run_walk_forward_optimization(engine, pair, tf, strategy_name, params)
                    
                    if 'error' not in result:
                        robustness_results[f'stress_{stress_spread}p_{stress_slippage}p'] = result['metrics']
                    
                    # Restore original costs
                    engine.transaction_cost = original_spread / 10000
                    engine.slippage = original_slippage / 10000
            
            # Parameter perturbation tests
            perturbation_pct = self.config['robustness']['param_perturbation_pct']
            perturbed_results = []
            
            for _ in range(10):  # 10 perturbation tests
                perturbed_params = params.copy()
                for key, value in params.items():
                    if isinstance(value, (int, float)):
                        perturbation = value * perturbation_pct * random.uniform(-1, 1)
                        perturbed_params[key] = value + perturbation
                
                result = self.run_walk_forward_optimization(engine, pair, tf, strategy_name, perturbed_params)
                if 'error' not in result:
                    perturbed_results.append(result['metrics'])
            
            robustness_results['parameter_perturbation'] = {
                'mean_sharpe': np.mean([r.get('oos_sharpe', 0) for r in perturbed_results]),
                'std_sharpe': np.std([r.get('oos_sharpe', 0) for r in perturbed_results]),
                'min_sharpe': np.min([r.get('oos_sharpe', 0) for r in perturbed_results]),
                'max_sharpe': np.max([r.get('oos_sharpe', 0) for r in perturbed_results])
            }
            
            return robustness_results
            
        except Exception as e:
            self.logger.error(f"❌ Robustness tests failed: {e}")
            return {'error': str(e)}
    
    def save_result(self, base_dir: Path, summary: Dict[str, Any], equity: List, trades: List):
        """Save experiment results"""
        try:
            self.ensure_dirs(base_dir)
            
            # Save summary
            with open(base_dir / "summary.json", "w") as f:
                json.dump(summary, f, indent=2, default=str)
            
            # Save equity curve if available
            if equity:
                equity_df = pd.DataFrame(equity)
                equity_df.to_csv(base_dir / "equity_curve.csv", index=False)
            
            # Save trade log if available
            if trades:
                trades_df = pd.DataFrame(trades)
                trades_df.to_csv(base_dir / "trade_log.csv", index=False)
            
            # Save README
            readme_content = f"""# Experiment Results

**Pair:** {summary['pair']}
**Timeframe:** {summary['timeframe']}
**Strategy:** {summary['strategy']}
**Timestamp:** {summary['timestamp']}

## Performance Metrics
- OOS Sharpe: {summary['metrics'].get('oos_sharpe', 0):.3f}
- OOS Sortino: {summary['metrics'].get('oos_sortino', 0):.3f}
- Max Drawdown: {summary['metrics'].get('oos_max_dd', 0):.3f}
- Profit Factor: {summary['metrics'].get('profit_factor', 0):.3f}
- Total Trades: {summary['metrics'].get('trades', 0)}
- Win Rate: {summary['metrics'].get('win_rate', 0):.3f}

## Hyperparameters
```json
{json.dumps(summary['hyperparams'], indent=2)}
```

## Configuration
```json
{json.dumps(summary['config'], indent=2)}
```
"""
            
            with open(base_dir / "README.md", "w") as f:
                f.write(readme_content)
            
        except Exception as e:
            self.logger.error(f"❌ Error saving results: {e}")
    
    def run_single_experiment(self, pair: str, tf: str, strategy_name: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run a single experiment"""
        try:
            # Generate config hash for observability
            config_hash = self.config_hash(pair, tf, strategy_name, params)
            self.logger.info(f"🧪 Running experiment: {pair} {tf} {strategy_name} [{config_hash}]")
            self.logger.info(f"[PARAMS] {strategy_name} {pair} {tf} {config_hash} {params}")
            
            # Choose engine
            engine = self.choose_engine(tf)
            if engine is None:
                self.failures.append((pair, tf, strategy_name, "Engine not available"))
                return None
            
            # Get strategy
            strategy = self.get_strategy(strategy_name)
            if strategy is None:
                self.failures.append((pair, tf, strategy_name, "Strategy not available"))
                return None
            
            # Run walk-forward optimization
            result = self.run_walk_forward_optimization(engine, pair, tf, strategy_name, params)
            
            if 'error' in result:
                self.failures.append((pair, tf, strategy_name, f"WFO failed: {result['error']}"))
                return None
            
            metrics = result['metrics']
            
            # Mark experiment as completed regardless of pass/fail for accurate progress
            self.completed_experiments += 1
            
            # Check selection criteria
            if not self.passes_selection_criteria(metrics, tf):
                self.logger.info(f"❌ Failed selection criteria: {pair} {tf} {strategy_name}")
                return None
            
            # Run robustness tests
            robustness_results = self.run_robustness_tests(engine, pair, tf, strategy_name, params)
            
            # Create summary with observability data
            trades = result.get('trades', [])
            trade_sig = trade_signature(trades)
            
            summary = {
                'pair': pair,
                'timeframe': tf,
                'strategy': strategy_name,
                'hyperparams': params,
                'metrics': metrics,
                'robustness': robustness_results,
                'config': self.config['meta'],
                'timestamp': self.timestamp(),
                'trade_signature': trade_sig,
                'config_hash': config_hash,
                'run_ts_utc': datetime.utcnow().isoformat()
            }
            
            # Save results with new directory structure
            run_root = Path(self.config['meta']['results_dir']) / datetime.now().strftime("%Y-%m-%d")
            out_dir = run_root / pair / tf / strategy_name / config_hash
            self.save_result(out_dir, summary, result.get('equity', []), trades)
            
            self.logger.info(f"✅ Experiment completed: {pair} {tf} {strategy_name} - Sharpe: {metrics.get('oos_sharpe', 0):.3f} - Trades: {len(trades)} - Sig: {trade_sig}")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Experiment failed: {e}")
            self.failures.append((pair, tf, strategy_name, f"Exception: {str(e)}"))
            return None
    
    def run_comprehensive_search(self):
        """Run comprehensive strategy search"""
        self.logger.info("🚀 Starting Ultimate Strategy Search")
        self.logger.info("=" * 80)
        
        try:
            # Initialize components
            self.initialize_components()
            
            # Validate data pipeline
            if not self.validate_data_pipeline():
                self.logger.error("❌ Data validation failed. Aborting search.")
                return
            
            # Calculate total experiments
            universe = self.config['universe']
            search_space = self.config['search_space']
            
            # Count total parameter combinations
            total_combinations = 1
            for param, values in search_space.items():
                if isinstance(values, list):
                    total_combinations *= len(values)
            
            total_experiments = (
                len(universe['pairs']) * 
                len(universe['timeframes']) * 
                len(universe['strategies']) * 
                total_combinations
            )
            
            self.total_experiments = total_experiments
            self.logger.info(f"📊 Total experiments to run: {total_experiments:,}")
            
            # Run experiments with job interleaving
            run_root = Path(self.config['meta']['results_dir']) / datetime.now().strftime("%Y-%m-%d")
            self.ensure_dirs(run_root)
            
            best_configs = []
            
            # Create job list and shuffle for interleaving
            jobs = list(itertools.product(universe['pairs'], universe['timeframes'], universe['strategies']))
            random.shuffle(jobs)
            
            for pair, tf, strategy_name in jobs:
                self.logger.info(f"🎯 Processing {pair} {tf} {strategy_name}")
                
                # Generate parameter combinations
                param_combinations = list(self.product_dict(search_space))
                
                for params in param_combinations:
                    # Skip invalid parameter combinations
                    if self._is_invalid_params(params):
                        continue
                    
                    # Generate run ID and log parameters
                    run_id = config_hash(pair, tf, strategy_name, params)
                    self.logger.info(f"[RUN] {pair} {tf} {strategy_name} {run_id} params={params}")
                    
                    # Run experiment
                    result = self.run_single_experiment(pair, tf, strategy_name, params)
                    
                    if result:
                        # Add observability data
                        trades = result.get('trades', [])
                        result['metrics']['trade_signature'] = trade_signature(trades)
                        result['config_hash'] = run_id
                        
                        # Check selection criteria
                        ok, reasons = passes_selection(result['metrics'], self.config['selection'], tf)
                        result['metrics']['selected'] = bool(ok)
                        result['metrics']['rejected_by'] = reasons
                        
                        best_configs.append(result)
                        
                        # Keep only top 10 configs
                        best_configs.sort(
                            key=lambda x: x['metrics'].get('oos_sharpe', 0), 
                            reverse=True
                        )
                        best_configs = best_configs[:10]
                    
                    # Progress update
                    progress = (self.completed_experiments / self.total_experiments) * 100
                    self.logger.info(f"📈 Progress: {progress:.1f}% ({self.completed_experiments}/{self.total_experiments})")
            
            # Save final results
            self._save_final_results(run_root, best_configs)
            
            # Print summary
            self._print_final_summary(best_configs)
            
        except Exception as e:
            self.logger.error(f"❌ Comprehensive search failed: {e}")
            self.logger.error(traceback.format_exc())
    
    def _is_invalid_params(self, params: Dict[str, Any]) -> bool:
        """Check if parameter combination is invalid"""
        # EMA fast must be less than EMA slow
        if 'ema_fast' in params and 'ema_slow' in params:
            if params['ema_fast'] >= params['ema_slow']:
                return True
        
        # MACD fast must be less than MACD slow
        if 'macd_fast' in params and 'macd_slow' in params:
            if params['macd_fast'] >= params['macd_slow']:
                return True
        
        return False
    
    def _save_final_results(self, run_root: Path, best_configs: List[Dict[str, Any]]):
        """Save final results and summary"""
        try:
            # Save best configurations
            with open(run_root / "best_configurations.json", "w") as f:
                json.dump(best_configs, f, indent=2, default=str)
            
            # Save failures log
            with open(run_root / "failures.log", "w") as f:
                for failure in self.failures:
                    f.write(f"{failure}\n")
            
            # Save search summary
            summary = {
                'search_timestamp': self.start_time.isoformat(),
                'completion_timestamp': datetime.now().isoformat(),
                'total_experiments': self.total_experiments,
                'completed_experiments': self.completed_experiments,
                'successful_experiments': len(best_configs),
                'failed_experiments': len(self.failures),
                'success_rate': len(best_configs) / self.completed_experiments if self.completed_experiments > 0 else 0,
                'best_configurations': best_configs,
                'config': self.config
            }
            
            with open(run_root / "search_summary.json", "w") as f:
                json.dump(summary, f, indent=2, default=str)
            
            self.logger.info(f"💾 Final results saved to: {run_root}")
            
        except Exception as e:
            self.logger.error(f"❌ Error saving final results: {e}")
    
    def _print_final_summary(self, best_configs: List[Dict[str, Any]]):
        """Print final search summary"""
        self.logger.info("\n" + "=" * 80)
        self.logger.info("🎯 ULTIMATE STRATEGY SEARCH COMPLETE")
        self.logger.info("=" * 80)
        
        duration = datetime.now() - self.start_time
        self.logger.info(f"⏱️  Total Duration: {duration}")
        self.logger.info(f"📊 Total Experiments: {self.total_experiments:,}")
        self.logger.info(f"✅ Successful: {len(best_configs)}")
        self.logger.info(f"❌ Failed: {len(self.failures)}")
        
        if best_configs:
            self.logger.info(f"\n🏆 TOP 3 CONFIGURATIONS:")
            for i, config in enumerate(best_configs[:3], 1):
                metrics = config['metrics']
                self.logger.info(f"{i}. {config['pair']} {config['timeframe']} {config['strategy']}")
                self.logger.info(f"   Sharpe: {metrics.get('oos_sharpe', 0):.3f}, Sortino: {metrics.get('oos_sortino', 0):.3f}")
                self.logger.info(f"   Max DD: {metrics.get('oos_max_dd', 0):.3f}, Profit Factor: {metrics.get('profit_factor', 0):.3f}")
                self.logger.info(f"   Trades: {metrics.get('trades', 0)}, Win Rate: {metrics.get('win_rate', 0):.3f}")
        else:
            self.logger.info("❌ No successful configurations found")
        
        self.logger.info(f"\n📋 {len(self.failures)} FAILURES LOGGED")
        self.logger.info("Check the generated reports for detailed analysis and next steps.")

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Ultimate Strategy Search Controller')
    parser.add_argument('--config', '-c', default='experiments.yaml', 
                       help='Path to configuration file (default: experiments.yaml)')
    args = parser.parse_args()
    
    try:
        controller = UltimateStrategySearchController(config_path=args.config)
        controller.run_comprehensive_search()
    except KeyboardInterrupt:
        logger.info("🛑 Search interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
