#!/usr/bin/env python3
"""
VALIDATE BALANCED HIGH WR STRATEGIES
Test 70-75% WR strategies that should be more robust
"""

import json
from pathlib import Path
import logging
import sys

sys.path.insert(0, '.')
from run_professional_validation import ProfessionalValidator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Load balanced strategies
    balanced_file = Path("results/balanced_high_wr_strategies.json")
    with open(balanced_file, 'r') as f:
        data = json.load(f)
    
    top_balanced = data['top_10'][:5]
    
    logger.info("=" * 80)
    logger.info("VALIDATING BALANCED 70-75% WR STRATEGIES")
    logger.info("=" * 80)
    logger.info(f"Testing top 5 balanced strategies (70-75% WR)")
    logger.info("")
    
    validator = ProfessionalValidator()
    results = []
    
    for i, strategy in enumerate(top_balanced, 1):
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"BALANCED STRATEGY #{i} - {strategy['win_rate']*100:.1f}% WR")
        logger.info("=" * 80)
        logger.info(f"Monthly Trades: {strategy['monthly_trades']:.1f}")
        logger.info(f"Expected Return: {strategy['total_return']*100:.1f}%")
        logger.info("")
        
        strategy_data = {
            'sharpe_ratio': strategy['sharpe'],
            'win_rate': strategy['win_rate'] * 100,
            'total_trades': int(strategy['total_trades']),
            'max_drawdown': strategy['max_dd_estimated']
        }
        
        result = validator.validate_strategy(
            f"Balanced #{i} ({strategy['win_rate']*100:.0f}% WR)",
            strategy_data
        )
        
        result['params'] = strategy['params']
        result['monthly_trades'] = strategy['monthly_trades']
        results.append(result)
    
    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("BALANCED STRATEGIES VALIDATION SUMMARY")
    logger.info("=" * 80)
    
    passed_count = sum(1 for r in results if r['passed'])
    
    for i, result in enumerate(results, 1):
        status = "VALIDATED" if result['passed'] else "FAILED"
        logger.info(f"\nBalanced #{i}: {status} ({result['passed_count']}/7)")
        logger.info(f"  Win Rate: {result['current_metrics']['win_rate']:.1f}%")
        logger.info(f"  Monthly Trades: {result['monthly_trades']:.1f}")
        logger.info(f"  Deflated Sharpe: {result['professional_metrics']['deflated_sharpe']:.2f}")
        logger.info(f"  ESI: {result['professional_metrics']['esi']:.2f}")
        logger.info(f"  MC Survival: {result['professional_metrics']['mc_survival_rate']*100:.0f}%")
        
        if not result['passed']:
            failed_checks = [k for k, v in result['validation_checks'].items() if not v]
            logger.info(f"  Failed: {', '.join(failed_checks)}")
    
    logger.info(f"\n\nPassed professional validation: {passed_count}/5")
    
    # Save
    output_file = Path("results/balanced_validation_results.json")
    
    def convert(obj):
        import numpy as np
        if isinstance(obj, (np.integer, np.floating, np.bool_)):
            return float(obj) if isinstance(obj, np.floating) else (int(obj) if isinstance(obj, np.integer) else bool(obj))
        elif isinstance(obj, (dict, list)):
            return {k: convert(v) for k, v in obj.items()} if isinstance(obj, dict) else [convert(i) for i in obj]
        return obj
    
    with open(output_file, 'w') as f:
        json.dump({'results': convert(results)}, f, indent=2)
    
    logger.info(f"Results saved to: {output_file}")

if __name__ == "__main__":
    main()




