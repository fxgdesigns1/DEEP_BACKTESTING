#!/usr/bin/env python3
"""
MONTE CARLO PATTERN RUNNER
Standalone script to analyze existing backtest results with MC pattern analysis
Easy-to-use command-line interface for traders and analysts
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Import our modules
from monte_carlo_analyzer import MonteCarloAnalyzer
from mc_patterns_report_generator import MCPatternsReportGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'mc_pattern_runner_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MCPatternRunner:
    """
    Complete Monte Carlo Pattern Analysis Runner
    Combines analysis, report generation, and easy CLI
    """
    
    def __init__(self, output_dir: str = "monte_carlo_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        self.analyzer = MonteCarloAnalyzer(output_dir=str(self.output_dir))
        self.report_generator = MCPatternsReportGenerator(output_dir=str(self.output_dir))
        
        logger.info("=" * 80)
        logger.info("MONTE CARLO PATTERN ANALYSIS RUNNER")
        logger.info("=" * 80)
        logger.info(f"Output directory: {self.output_dir.absolute()}")
        
    def run_single_file(
        self, 
        file_path: str,
        runs: int = 1000,
        block: int = 10,
        window: int = 20,
        generate_html: bool = True
    ) -> Optional[str]:
        """Analyze a single backtest file and generate reports"""
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"ANALYZING: {file_path}")
        logger.info("=" * 80)
        
        # Run MC analysis
        mc_report = self.analyzer.analyze_backtest_file(
            file_path,
            runs=runs,
            block=block,
            window=window
        )
        
        if mc_report is None:
            logger.error("Analysis failed!")
            return None
            
        # Print summary
        self._print_summary(mc_report)
        
        # Generate HTML report
        html_path = None
        if generate_html:
            logger.info("Generating HTML report...")
            html_path = self.report_generator.generate_html_report(mc_report)
            logger.info(f"HTML report saved: {html_path}")
            
        return html_path
        
    def run_directory(
        self,
        directory: str,
        pattern: str = "*.json",
        runs: int = 1000,
        block: int = 10,
        window: int = 20,
        max_files: Optional[int] = None,
        generate_html: bool = True
    ) -> List[str]:
        """Analyze all backtest files in a directory"""
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"ANALYZING DIRECTORY: {directory}")
        logger.info(f"Pattern: {pattern}")
        logger.info("=" * 80)
        
        # Run MC analysis on all files
        reports = self.analyzer.analyze_directory(
            directory,
            pattern=pattern,
            runs=runs,
            block=block,
            window=window,
            max_files=max_files
        )
        
        logger.info(f"\nSuccessfully analyzed {len(reports)} files")
        
        # Generate HTML reports
        html_paths = []
        if generate_html and reports:
            logger.info("\nGenerating HTML reports...")
            for report in reports:
                try:
                    html_path = self.report_generator.generate_html_report(report)
                    html_paths.append(html_path)
                except Exception as e:
                    logger.error(f"Failed to generate HTML for {report.get('run_id')}: {e}")
                    
            logger.info(f"Generated {len(html_paths)} HTML reports")
            
        # Print overall summary
        if reports:
            self._print_directory_summary(reports)
            
        return html_paths
        
    def _print_summary(self, mc_report: Dict[str, Any]):
        """Print a nice summary of the MC analysis"""
        base = mc_report.get("base_metrics", {})
        mc = mc_report.get("mc", {})
        lev = mc_report.get("leverageability", {})
        patterns = mc_report.get("patterns", {})
        hod = patterns.get("hour_of_day", {})
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("ANALYSIS SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Run ID: {mc_report.get('run_id')}")
        logger.info("")
        logger.info("BASE METRICS:")
        logger.info(f"  Sharpe Ratio:    {base.get('sharpe', 0):>8.3f}")
        logger.info(f"  Max Drawdown:    {base.get('max_dd', 0):>8.2%}")
        logger.info(f"  Ulcer Index:     {base.get('ulcer', 0):>8.3f}")
        logger.info(f"  Trades:          {base.get('trades', 0):>8}")
        logger.info("")
        logger.info(f"MONTE CARLO ({mc.get('runs', 0)} simulations):")
        logger.info(f"  Sharpe Mean:     {mc.get('sharpe_mean', 0):>8.3f}")
        logger.info(f"  Sharpe P5-P95:   {mc.get('sharpe_p05', 0):>8.3f} - {mc.get('sharpe_p95', 0):.3f}")
        logger.info(f"  MaxDD Mean:      {mc.get('maxdd_mean', 0):>8.2%}")
        logger.info(f"  MaxDD P95:       {mc.get('maxdd_p95', 0):>8.2%}")
        logger.info("")
        logger.info("LEVERAGEABILITY:")
        logger.info(f"  Mean Uplift:     {lev.get('uplift_mean', 0):>8.3f}")
        logger.info(f"  P95 Uplift:      {lev.get('uplift_p95', 0):>8.3f}")
        logger.info(f"  Positive Rate:   {lev.get('uplift_frac_positive', 0):>8.1%}")
        logger.info("")
        logger.info("HOUR-OF-DAY EFFECT:")
        logger.info(f"  Kruskal-Wallis H: {hod.get('kruskal_H', 0):.3f}")
        logger.info(f"  P-value:          {hod.get('p_value', 1):.4f}")
        logger.info(f"  Best Hours:       {', '.join(map(str, hod.get('best_hours', [])))}")
        logger.info(f"  Worst Hours:      {', '.join(map(str, hod.get('worst_hours', [])))}")
        logger.info("=" * 80)
        
    def _print_directory_summary(self, reports: List[Dict[str, Any]]):
        """Print summary of multiple analyses"""
        logger.info("")
        logger.info("=" * 80)
        logger.info("DIRECTORY ANALYSIS SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Files Analyzed: {len(reports)}")
        logger.info("")
        
        # Calculate statistics
        sharpes = [r["base_metrics"]["sharpe"] for r in reports]
        max_dds = [r["base_metrics"]["max_dd"] for r in reports]
        uplifts = [r["leverageability"]["uplift_mean"] for r in reports]
        
        import numpy as np
        
        logger.info("SHARPE RATIO DISTRIBUTION:")
        logger.info(f"  Mean:     {np.mean(sharpes):>8.3f}")
        logger.info(f"  Median:   {np.median(sharpes):>8.3f}")
        logger.info(f"  Std Dev:  {np.std(sharpes):>8.3f}")
        logger.info(f"  Min:      {np.min(sharpes):>8.3f}")
        logger.info(f"  Max:      {np.max(sharpes):>8.3f}")
        logger.info("")
        
        logger.info("MAX DRAWDOWN DISTRIBUTION:")
        logger.info(f"  Mean:     {np.mean(max_dds):>8.2%}")
        logger.info(f"  Median:   {np.median(max_dds):>8.2%}")
        logger.info(f"  Min:      {np.min(max_dds):>8.2%}")
        logger.info(f"  Max:      {np.max(max_dds):>8.2%}")
        logger.info("")
        
        logger.info("LEVERAGEABILITY UPLIFT:")
        logger.info(f"  Mean:     {np.mean(uplifts):>8.3f}")
        logger.info(f"  Median:   {np.median(uplifts):>8.3f}")
        logger.info(f"  Positive: {sum(1 for u in uplifts if u > 0)}/{len(uplifts)} ({sum(1 for u in uplifts if u > 0)/len(uplifts)*100:.1f}%)")
        logger.info("")
        
        # Top strategies
        sorted_by_sharpe = sorted(reports, key=lambda x: x["base_metrics"]["sharpe"], reverse=True)[:3]
        logger.info("TOP 3 STRATEGIES BY SHARPE:")
        for i, r in enumerate(sorted_by_sharpe, 1):
            logger.info(f"  {i}. {r.get('run_id')} - Sharpe: {r['base_metrics']['sharpe']:.3f}, MaxDD: {r['base_metrics']['max_dd']:.2%}")
            
        logger.info("")
        sorted_by_leverage = sorted(reports, key=lambda x: x["leverageability"]["uplift_mean"], reverse=True)[:3]
        logger.info("TOP 3 STRATEGIES BY LEVERAGEABILITY:")
        for i, r in enumerate(sorted_by_leverage, 1):
            logger.info(f"  {i}. {r.get('run_id')} - Uplift: {r['leverageability']['uplift_mean']:.3f}")
            
        logger.info("=" * 80)


def main():
    """Command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Monte Carlo Pattern Analysis Runner for Trading Backtests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a single backtest file
  python mc_pattern_runner.py --file my_backtest_results.json

  # Analyze all JSON files in a directory
  python mc_pattern_runner.py --dir backtesting_output

  # Analyze with custom settings (2000 MC runs, block size 15)
  python mc_pattern_runner.py --file results.json --runs 2000 --block 15

  # Analyze directory but only first 10 files
  python mc_pattern_runner.py --dir backtesting_output --max-files 10

  # Skip HTML generation (faster)
  python mc_pattern_runner.py --dir backtesting_output --no-html
        """
    )
    
    # Input options
    parser.add_argument("--file", type=str, help="Single backtest result file to analyze")
    parser.add_argument("--dir", type=str, help="Directory containing backtest results")
    parser.add_argument("--pattern", type=str, default="*.json", help="File pattern to match (default: *.json)")
    
    # MC parameters
    parser.add_argument("--runs", type=int, default=1000, help="Number of MC simulations (default: 1000)")
    parser.add_argument("--block", type=int, default=10, help="Block size for bootstrap (default: 10)")
    parser.add_argument("--window", type=int, default=20, help="Window size for motif discovery (default: 20)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    
    # Output options
    parser.add_argument("--output", type=str, default="monte_carlo_reports", help="Output directory (default: monte_carlo_reports)")
    parser.add_argument("--max-files", type=int, help="Maximum number of files to process")
    parser.add_argument("--no-html", action="store_true", help="Skip HTML report generation (faster)")
    
    args = parser.parse_args()
    
    # Validate input
    if not args.file and not args.dir:
        parser.print_help()
        print("\nError: Must specify either --file or --dir")
        sys.exit(1)
        
    # Create runner
    runner = MCPatternRunner(output_dir=args.output)
    
    try:
        if args.file:
            # Analyze single file
            html_path = runner.run_single_file(
                args.file,
                runs=args.runs,
                block=args.block,
                window=args.window,
                generate_html=not args.no_html
            )
            
            if html_path:
                logger.info("")
                logger.info("✅ Analysis complete!")
                logger.info(f"📊 View HTML report: {html_path}")
                logger.info(f"📁 All reports in: {runner.output_dir.absolute()}")
            else:
                logger.error("❌ Analysis failed")
                sys.exit(1)
                
        elif args.dir:
            # Analyze directory
            html_paths = runner.run_directory(
                args.dir,
                pattern=args.pattern,
                runs=args.runs,
                block=args.block,
                window=args.window,
                max_files=args.max_files,
                generate_html=not args.no_html
            )
            
            logger.info("")
            logger.info("✅ Analysis complete!")
            logger.info(f"📊 Generated {len(html_paths)} HTML reports")
            logger.info(f"📁 All reports in: {runner.output_dir.absolute()}")
            
    except KeyboardInterrupt:
        logger.info("\n\nInterrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n\n❌ Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()




