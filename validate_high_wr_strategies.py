#!/usr/bin/env python3
"""
VALIDATE HIGH WIN RATE STRATEGIES
Run professional validation on the ultra-selective 70%+ WR strategies
"""

import os
import sys
import json
from pathlib import Path
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_professional_validation import ProfessionalValidator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Validate top 3 high win rate strategies"""
    
    # Load optimization results
    results_file = list(Path("results").glob("high_wr_optimization_*.json"))[-1]
    
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    top_strategies = data['top_strategies'][:3]
    
    logger.info("=" * 80)
    logger.info("VALIDATING TOP 3 HIGH WIN RATE STRATEGIES")
    logger.info("=" * 80)
    logger.info(f"Loaded {len(top_strategies)} strategies for validation")
    logger.info("")
    
    validator = ProfessionalValidator()
    validated_results = []
    
    for i, strategy in enumerate(top_strategies, 1):
        logger.info("")
        logger.info(f"{'='*80}")
        logger.info(f"VALIDATING RANK #{i} - {strategy['win_rate']*100:.1f}% WR Strategy")
        logger.info(f"{'='*80}")
        
        # Convert to format expected by validator
        strategy_data = {
            'sharpe_ratio': strategy['sharpe'],
            'win_rate': strategy['win_rate'] * 100,
            'total_trades': int(strategy['total_trades']),
            'max_drawdown': strategy['max_dd_estimated']
        }
        
        result = validator.validate_strategy(
            f"Ultra-Selective Rank #{i} ({strategy['win_rate']*100:.0f}% WR)",
            strategy_data
        )
        
        result['original_params'] = strategy['params']
        result['monthly_trades'] = strategy['monthly_trades']
        validated_results.append(result)
    
    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("HIGH WIN RATE VALIDATION SUMMARY")
    logger.info("=" * 80)
    
    for i, result in enumerate(validated_results, 1):
        status = "VALIDATED" if result['passed'] else "FAILED"
        logger.info(f"\nRank #{i}: {status} ({result['passed_count']}/7 checks)")
        logger.info(f"  Win Rate: {result['current_metrics']['win_rate']:.1f}%")
        logger.info(f"  Monthly Trades: {result['monthly_trades']:.1f}")
        logger.info(f"  Deflated Sharpe: {result['professional_metrics']['deflated_sharpe']:.2f}")
        logger.info(f"  ESI: {result['professional_metrics']['esi']:.2f}")
        logger.info(f"  MC Survival: {result['professional_metrics']['mc_survival_rate']*100:.0f}%")
    
    # Save
    output_file = Path(f"results/high_wr_validation_{Path(results_file).stem.split('_')[-1]}.json")
    
    # Convert to serializable
    def convert(obj):
        import numpy as np
        if isinstance(obj, (np.integer, np.floating, np.bool_)):
            return float(obj) if isinstance(obj, np.floating) else (int(obj) if isinstance(obj, np.integer) else bool(obj))
        elif isinstance(obj, (dict, list)):
            return {k: convert(v) for k, v in obj.items()} if isinstance(obj, dict) else [convert(i) for i in obj]
        return obj
    
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': str(Path(results_file).stem.split('_')[-1]),
            'strategies_validated': len(validated_results),
            'results': convert(validated_results)
        }, f, indent=2)
    
    logger.info(f"\nResults saved to: {output_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())




