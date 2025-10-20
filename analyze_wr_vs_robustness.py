#!/usr/bin/env python3
"""
ANALYZE WIN RATE VS ROBUSTNESS TRADE-OFF
Find the sweet spot: High win rate + Professional validation
"""

import json
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_wr_ranges():
    """Analyze different win rate ranges for robustness"""
    
    # Load optimization results
    results_file = list(Path("results").glob("high_wr_optimization_*.json"))[-1]
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    all_strategies = data['all_strategies']
    
    logger.info("=" * 80)
    logger.info("WIN RATE VS ROBUSTNESS ANALYSIS")
    logger.info("=" * 80)
    logger.info(f"Total strategies found: {len(all_strategies)}")
    logger.info("")
    
    # Analyze by win rate buckets
    wr_buckets = {
        '70-72%': (0.70, 0.72),
        '72-74%': (0.72, 0.74),
        '74-76%': (0.74, 0.76),
        '76-78%': (0.76, 0.78),
        '78-80%': (0.78, 0.80),
        '80%+': (0.80, 1.00)
    }
    
    for bucket_name, (min_wr, max_wr) in wr_buckets.items():
        bucket_strategies = [s for s in all_strategies 
                            if min_wr <= s['win_rate'] < max_wr]
        
        if bucket_strategies:
            avg_sharpe = np.mean([s['sharpe'] for s in bucket_strategies])
            avg_monthly_trades = np.mean([s['monthly_trades'] for s in bucket_strategies])
            avg_return = np.mean([s['total_return'] for s in bucket_strategies])
            
            logger.info(f"\n{bucket_name} Win Rate:")
            logger.info(f"  Count: {len(bucket_strategies)}")
            logger.info(f"  Avg Sharpe: {avg_sharpe:.2f}")
            logger.info(f"  Avg Monthly Trades: {avg_monthly_trades:.1f}")
            logger.info(f"  Avg Return: {avg_return*100:.1f}%")
    
    # Find strategies with best balance
    logger.info("")
    logger.info("=" * 80)
    logger.info("BALANCED STRATEGIES (70-75% WR, >8 trades/month, Good Sharpe)")
    logger.info("=" * 80)
    
    balanced = [s for s in all_strategies 
                if 0.70 <= s['win_rate'] <= 0.75 
                and s['monthly_trades'] >= 8
                and s['sharpe'] > 2.0]
    
    if balanced:
        # Sort by composite score
        balanced_sorted = sorted(balanced, key=lambda x: x['composite_score'], reverse=True)
        
        logger.info(f"\nFound {len(balanced)} balanced strategies")
        logger.info("\nTop 5 Balanced Strategies:")
        
        for i, strategy in enumerate(balanced_sorted[:5], 1):
            logger.info(f"\n--- Balanced #{i} ---")
            logger.info(f"Win Rate: {strategy['win_rate']*100:.1f}%")
            logger.info(f"Monthly Trades: {strategy['monthly_trades']:.1f}")
            logger.info(f"Sharpe: {strategy['sharpe']:.2f}")
            logger.info(f"Expected Return: {strategy['total_return']*100:.1f}%")
            logger.info(f"Expectancy: ${strategy['expectancy']:.2f}")
            logger.info(f"\nKey Parameters:")
            logger.info(f"  Signal Strength: {strategy['params']['signal_strength_min']}")
            logger.info(f"  Confluence: {strategy['params']['confluence_required']}")
            logger.info(f"  R:R Ratio: {strategy['params']['rr_ratio']}")
            logger.info(f"  ADX Min: {strategy['params']['min_adx']}")
            logger.info(f"  Confirmation Bars: {strategy['params']['confirmation_bars']}")
        
        # Save balanced strategies
        output_file = Path("results/balanced_high_wr_strategies.json")
        with open(output_file, 'w') as f:
            json.dump({
                'description': '70-75% WR strategies with >8 trades/month and robustness',
                'total_found': len(balanced),
                'top_10': balanced_sorted[:10]
            }, f, indent=2)
        
        logger.info(f"\n\nBalanced strategies saved to: {output_file}")
        
        return balanced_sorted[:5]
    else:
        logger.warning("\nNo balanced strategies found in 70-75% range")
        return []

if __name__ == "__main__":
    analyze_wr_ranges()




