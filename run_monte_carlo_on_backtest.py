#!/usr/bin/env python3
"""
Run Monte Carlo Analysis on Actual Backtest Results
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_backtest_results(file_path):
    """Load backtest results"""
    with open(file_path, 'r') as f:
        return json.load(f)

def extract_returns_from_metrics(backtest_data):
    """Extract returns from backtest metrics"""
    baseline = backtest_data.get('baseline', {})
    metrics = baseline.get('metrics', {})
    
    # Get the key stats
    total_trades = metrics.get('total_trades', 0)
    win_count = metrics.get('win_count', 0)
    loss_count = metrics.get('loss_count', 0)
    average_win = metrics.get('average_win', 0)
    average_loss = metrics.get('average_loss', 0)
    
    logger.info(f"Total trades: {total_trades}")
    logger.info(f"Wins: {win_count}, Losses: {loss_count}")
    logger.info(f"Avg Win: {average_win:.4f}, Avg Loss: {average_loss:.4f}")
    
    # Simulate the returns based on win/loss distribution
    returns = []
    
    # Add wins
    for _ in range(win_count):
        returns.append(average_win)
    
    # Add losses
    for _ in range(loss_count):
        returns.append(average_loss)
    
    return np.array(returns)

def run_monte_carlo_shuffle(returns, n_runs=1000, seed=42):
    """Run Monte Carlo by shuffling trades"""
    logger.info(f"Running {n_runs} Monte Carlo simulations...")
    
    np.random.seed(seed)
    n_trades = len(returns)
    
    final_returns = []
    sharpe_ratios = []
    max_drawdowns = []
    
    for i in range(n_runs):
        # Shuffle the returns
        shuffled = np.random.permutation(returns)
        
        # Calculate cumulative returns
        cum_returns = np.cumsum(shuffled)
        
        # Final return
        final_return = cum_returns[-1]
        final_returns.append(final_return)
        
        # Sharpe ratio
        if len(shuffled) > 1 and np.std(shuffled) > 0:
            sharpe = np.mean(shuffled) / np.std(shuffled)
        else:
            sharpe = 0
        sharpe_ratios.append(sharpe)
        
        # Maximum drawdown
        peak = np.maximum.accumulate(cum_returns)
        drawdown = peak - cum_returns
        max_dd = np.max(drawdown) if len(drawdown) > 0 else 0
        max_drawdowns.append(max_dd)
        
        if (i + 1) % 100 == 0:
            logger.info(f"Progress: {i+1}/{n_runs} simulations complete")
    
    return {
        'final_returns': np.array(final_returns),
        'sharpe_ratios': np.array(sharpe_ratios),
        'max_drawdowns': np.array(max_drawdowns)
    }

def analyze_monte_carlo_results(original_metrics, mc_results):
    """Analyze Monte Carlo results"""
    logger.info("\n" + "="*80)
    logger.info("MONTE CARLO ANALYSIS RESULTS")
    logger.info("="*80)
    
    # Original strategy performance
    logger.info("\nORIGINAL STRATEGY:")
    logger.info(f"  Win Rate: {original_metrics['win_rate']*100:.2f}%")
    logger.info(f"  Sharpe Ratio: {original_metrics['sharpe_ratio']:.4f}")
    logger.info(f"  Max Drawdown: {original_metrics['max_drawdown']*100:.2f}%")
    logger.info(f"  Total Return: {original_metrics['total_return']*100:.2f}%")
    logger.info(f"  Profit Factor: {original_metrics['profit_factor']:.4f}")
    
    # Monte Carlo statistics
    final_returns = mc_results['final_returns']
    sharpe_ratios = mc_results['sharpe_ratios']
    max_drawdowns = mc_results['max_drawdowns']
    
    logger.info("\nMONTE CARLO SIMULATION RESULTS (1000 runs):")
    logger.info("\nFinal Returns Distribution:")
    logger.info(f"  Mean: {np.mean(final_returns)*100:.2f}%")
    logger.info(f"  Median: {np.median(final_returns)*100:.2f}%")
    logger.info(f"  Std Dev: {np.std(final_returns)*100:.2f}%")
    logger.info(f"  Min: {np.min(final_returns)*100:.2f}%")
    logger.info(f"  Max: {np.max(final_returns)*100:.2f}%")
    logger.info(f"  5th Percentile: {np.percentile(final_returns, 5)*100:.2f}%")
    logger.info(f"  95th Percentile: {np.percentile(final_returns, 95)*100:.2f}%")
    
    logger.info("\nSharpe Ratio Distribution:")
    logger.info(f"  Mean: {np.mean(sharpe_ratios):.4f}")
    logger.info(f"  Median: {np.median(sharpe_ratios):.4f}")
    logger.info(f"  Std Dev: {np.std(sharpe_ratios):.4f}")
    logger.info(f"  5th Percentile: {np.percentile(sharpe_ratios, 5):.4f}")
    logger.info(f"  95th Percentile: {np.percentile(sharpe_ratios, 95):.4f}")
    
    logger.info("\nMaximum Drawdown Distribution:")
    logger.info(f"  Mean: {np.mean(max_drawdowns)*100:.2f}%")
    logger.info(f"  Median: {np.median(max_drawdowns)*100:.2f}%")
    logger.info(f"  Worst (95th percentile): {np.percentile(max_drawdowns, 95)*100:.2f}%")
    
    # Survival rate
    positive_returns = np.sum(final_returns > 0)
    survival_rate = positive_returns / len(final_returns) * 100
    logger.info(f"\nSURVIVAL RATE: {survival_rate:.2f}% of simulations had positive returns")
    
    # Risk of ruin (returns below -20%)
    ruin_threshold = -0.20
    ruined = np.sum(final_returns < ruin_threshold)
    ruin_rate = ruined / len(final_returns) * 100
    logger.info(f"RISK OF RUIN: {ruin_rate:.2f}% of simulations had returns below -20%")
    
    logger.info("\n" + "="*80)
    logger.info("CONCLUSION:")
    if survival_rate < 50:
        logger.info("⚠️  CRITICAL: Less than 50% of simulations are profitable!")
        logger.info("    This strategy has a NEGATIVE EDGE.")
    elif survival_rate < 60:
        logger.info("⚠️  WARNING: Only ~50% of simulations are profitable.")
        logger.info("    Strategy has a WEAK EDGE at best.")
    elif survival_rate < 70:
        logger.info("✓  Strategy shows a MODEST POSITIVE EDGE.")
    else:
        logger.info("✓✓ Strategy shows a STRONG POSITIVE EDGE.")
    
    logger.info("="*80)
    
    return {
        'survival_rate': survival_rate,
        'mean_return': np.mean(final_returns),
        'median_return': np.median(final_returns),
        'mean_sharpe': np.mean(sharpe_ratios),
        'mean_drawdown': np.mean(max_drawdowns),
        'risk_of_ruin': ruin_rate
    }

def main():
    # Load backtest results
    backtest_file = "backtest_results/stress_test_results_20251018_130859.json"
    logger.info(f"Loading backtest results from {backtest_file}")
    
    backtest_data = load_backtest_results(backtest_file)
    
    # Extract returns
    returns = extract_returns_from_metrics(backtest_data)
    logger.info(f"Extracted {len(returns)} trade returns")
    
    # Run Monte Carlo
    mc_results = run_monte_carlo_shuffle(returns, n_runs=1000, seed=42)
    
    # Analyze results
    original_metrics = backtest_data['baseline']['metrics']
    summary = analyze_monte_carlo_results(original_metrics, mc_results)
    
    # Save results
    output = {
        'original_metrics': original_metrics,
        'monte_carlo_summary': summary,
        'monte_carlo_distributions': {
            'final_returns': {
                'mean': float(np.mean(mc_results['final_returns'])),
                'std': float(np.std(mc_results['final_returns'])),
                'percentiles': {
                    'p5': float(np.percentile(mc_results['final_returns'], 5)),
                    'p25': float(np.percentile(mc_results['final_returns'], 25)),
                    'p50': float(np.percentile(mc_results['final_returns'], 50)),
                    'p75': float(np.percentile(mc_results['final_returns'], 75)),
                    'p95': float(np.percentile(mc_results['final_returns'], 95))
                }
            },
            'sharpe_ratios': {
                'mean': float(np.mean(mc_results['sharpe_ratios'])),
                'std': float(np.std(mc_results['sharpe_ratios'])),
                'percentiles': {
                    'p5': float(np.percentile(mc_results['sharpe_ratios'], 5)),
                    'p50': float(np.percentile(mc_results['sharpe_ratios'], 50)),
                    'p95': float(np.percentile(mc_results['sharpe_ratios'], 95))
                }
            }
        }
    }
    
    output_file = "monte_carlo_results/mc_analysis_actual_results.json"
    Path("monte_carlo_results").mkdir(exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"\nResults saved to {output_file}")

if __name__ == "__main__":
    main()


