#!/usr/bin/env python3
"""
MONTE CARLO STRATEGY COMPARATOR
Analyzes aggregate strategy results and creates synthetic equity curves for MC analysis
Works with strategy summary data (win_rate, avg_win, avg_loss, etc.)
"""

import os
import json
import logging
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from monte_carlo_patterns import analyze
from mc_patterns_report_generator import MCPatternsReportGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCStrategyComparator:
    """Compare and analyze strategy results using Monte Carlo"""
    
    def __init__(self, output_dir: str = "monte_carlo_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.report_gen = MCPatternsReportGenerator(output_dir=str(self.output_dir))
        
    def create_synthetic_equity_from_stats(self, stats: Dict[str, Any], n_trades: int = None) -> List[float]:
        """
        Create a synthetic equity curve from aggregate statistics
        Uses win_rate, avg_win, avg_loss to generate realistic trade sequence
        """
        n_trades = n_trades or stats.get('total_trades', 100)
        win_rate = stats.get('win_rate', 50.0) / 100.0
        avg_win_pct = stats.get('avg_win_pct', 2.0)
        avg_loss_pct = stats.get('avg_loss_pct', -1.0)
        
        # Ensure avg_loss is negative
        if avg_loss_pct > 0:
            avg_loss_pct = -avg_loss_pct
            
        # Generate trade sequence
        np.random.seed(42)
        trades = []
        
        for _ in range(n_trades):
            if np.random.random() < win_rate:
                # Winning trade
                pnl = np.random.normal(avg_win_pct, avg_win_pct * 0.3)
            else:
                # Losing trade
                pnl = np.random.normal(avg_loss_pct, abs(avg_loss_pct) * 0.3)
            trades.append(pnl)
            
        # Create equity curve
        equity = [100.0]  # Starting with $100
        for pnl_pct in trades:
            equity.append(equity[-1] * (1 + pnl_pct / 100.0))
            
        return equity
        
    def analyze_strategy_file(self, file_path: str, top_n: int = 10, runs: int = 1000) -> List[Dict]:
        """Analyze strategies from aggregate results file"""
        logger.info(f"Loading strategy results from: {file_path}")
        
        with open(file_path, 'r') as f:
            strategies = json.load(f)
            
        logger.info(f"Found {len(strategies)} strategies")
        
        # Filter and sort by Sharpe ratio
        valid_strategies = [s for s in strategies if s.get('results', {}).get('sharpe_ratio', 0) > 0]
        sorted_strategies = sorted(
            valid_strategies,
            key=lambda x: x['results'].get('sharpe_ratio', 0),
            reverse=True
        )[:top_n]
        
        logger.info(f"Analyzing top {len(sorted_strategies)} strategies by Sharpe ratio")
        
        reports = []
        for i, strategy in enumerate(sorted_strategies, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"Strategy {i}/{len(sorted_strategies)}")
            logger.info(f"{'='*80}")
            
            scenario = strategy.get('scenario', {})
            results = strategy.get('results', {})
            
            logger.info(f"Pair: {scenario.get('pair', 'N/A')}")
            logger.info(f"Timeframe: {scenario.get('tf', 'N/A')}")
            logger.info(f"Parameters: EMA({scenario.get('ema_fast')}, {scenario.get('ema_mid')}, {scenario.get('ema_slow')})")
            logger.info(f"Base Sharpe: {results.get('sharpe_ratio', 0):.3f}")
            logger.info(f"Win Rate: {results.get('win_rate', 0):.1f}%")
            logger.info(f"Total Trades: {results.get('total_trades', 0)}")
            
            # Create synthetic equity curve
            equity = self.create_synthetic_equity_from_stats(
                results,
                n_trades=min(results.get('total_trades', 100), 1000)  # Limit to 1000 for performance
            )
            
            logger.info(f"Generated synthetic equity curve with {len(equity)} points")
            
            # Run MC analysis
            try:
                mc_report = analyze(
                    {"equity": equity},
                    runs=runs,
                    block=10,
                    window=20,
                    seed=42 + i
                )
                
                # Add strategy info to report
                mc_report['strategy_info'] = {
                    'scenario': scenario,
                    'base_results': results,
                    'rank': i
                }
                
                # Save JSON report
                report_filename = f"mc_strategy_{i}_{scenario.get('pair', 'unknown')}_{scenario.get('tf', 'unknown')}.json"
                report_path = self.output_dir / report_filename
                with open(report_path, 'w') as f:
                    json.dump(mc_report, f, indent=2)
                    
                logger.info(f"MC Report saved: {report_path}")
                
                # Generate HTML report
                html_filename = f"mc_strategy_{i}_{scenario.get('pair', 'unknown')}_{scenario.get('tf', 'unknown')}.html"
                self.report_gen.generate_html_report(mc_report, output_filename=html_filename)
                
                # Print summary
                self._print_strategy_summary(mc_report, i)
                
                reports.append(mc_report)
                
            except Exception as e:
                logger.error(f"Failed to analyze strategy {i}: {e}")
                continue
                
        # Create comparison summary
        if reports:
            self._create_comparison_summary(reports, sorted_strategies)
            
        return reports
        
    def _print_strategy_summary(self, mc_report: Dict, rank: int):
        """Print summary for a single strategy"""
        base = mc_report.get('base_metrics', {})
        mc = mc_report.get('mc', {})
        lev = mc_report.get('leverageability', {})
        
        logger.info("")
        logger.info(f"MONTE CARLO RESULTS (Rank #{rank}):")
        logger.info(f"  MC Sharpe Mean:     {mc.get('sharpe_mean', 0):>8.3f}")
        logger.info(f"  MC Sharpe P5-P95:   {mc.get('sharpe_p05', 0):>8.3f} - {mc.get('sharpe_p95', 0):.3f}")
        logger.info(f"  MC MaxDD Mean:      {mc.get('maxdd_mean', 0):>8.2%}")
        logger.info(f"  Leverageability:    {lev.get('uplift_mean', 0):>8.3f}")
        
        # Robustness check
        if base.get('sharpe', 0) > mc.get('sharpe_mean', 0):
            logger.info(f"  Status: ROBUST (base > MC mean)")
        else:
            logger.info(f"  Status: Check needed (base <= MC mean)")
            
    def _create_comparison_summary(self, reports: List[Dict], strategies: List[Dict]):
        """Create a comparison summary across all analyzed strategies"""
        logger.info("\n" + "="*80)
        logger.info("STRATEGY COMPARISON SUMMARY")
        logger.info("="*80)
        
        summary = {
            "generated_at": datetime.now().isoformat(),
            "total_strategies_analyzed": len(reports),
            "comparison": []
        }
        
        for i, (report, strategy) in enumerate(zip(reports, strategies), 1):
            scenario = strategy.get('scenario', {})
            results = strategy.get('results', {})
            base = report.get('base_metrics', {})
            mc = report.get('mc', {})
            lev = report.get('leverageability', {})
            
            comparison_entry = {
                "rank": i,
                "pair": scenario.get('pair'),
                "timeframe": scenario.get('tf'),
                "parameters": f"EMA({scenario.get('ema_fast')},{scenario.get('ema_mid')},{scenario.get('ema_slow')})",
                "base_sharpe": results.get('sharpe_ratio'),
                "base_win_rate": results.get('win_rate'),
                "base_max_dd": results.get('max_drawdown_pct'),
                "mc_sharpe_mean": mc.get('sharpe_mean'),
                "mc_sharpe_p05": mc.get('sharpe_p05'),
                "mc_sharpe_p95": mc.get('sharpe_p95'),
                "leverageability": lev.get('uplift_mean'),
                "robust": base.get('sharpe', 0) > mc.get('sharpe_mean', 0)
            }
            
            summary["comparison"].append(comparison_entry)
            
        # Save summary
        summary_path = self.output_dir / f"strategy_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
            
        logger.info(f"\nComparison summary saved: {summary_path}")
        
        # Print comparison table
        logger.info("\n" + "="*80)
        logger.info("TOP STRATEGIES COMPARISON")
        logger.info("="*80)
        logger.info(f"{'Rank':<6} {'Pair':<10} {'TF':<6} {'Base Sharpe':<12} {'MC Sharpe':<12} {'Leverage':<10} {'Robust':<8}")
        logger.info("-"*80)
        
        for entry in summary["comparison"]:
            logger.info(
                f"{entry['rank']:<6} "
                f"{entry['pair']:<10} "
                f"{entry['timeframe']:<6} "
                f"{entry['base_sharpe']:<12.3f} "
                f"{entry['mc_sharpe_mean']:<12.3f} "
                f"{entry['leverageability']:<10.3f} "
                f"{'YES' if entry['robust'] else 'CHECK':<8}"
            )
            
        logger.info("="*80)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Monte Carlo Strategy Comparator")
    parser.add_argument("file", type=str, help="Strategy results JSON file")
    parser.add_argument("--top-n", type=int, default=10, help="Number of top strategies to analyze")
    parser.add_argument("--runs", type=int, default=1000, help="Number of MC simulations")
    parser.add_argument("--output", type=str, default="monte_carlo_reports", help="Output directory")
    
    args = parser.parse_args()
    
    comparator = MCStrategyComparator(output_dir=args.output)
    reports = comparator.analyze_strategy_file(
        args.file,
        top_n=args.top_n,
        runs=args.runs
    )
    
    logger.info(f"\nAnalysis complete! Generated {len(reports)} reports")
    logger.info(f"Check {args.output}/ for HTML and JSON reports")


if __name__ == "__main__":
    main()




