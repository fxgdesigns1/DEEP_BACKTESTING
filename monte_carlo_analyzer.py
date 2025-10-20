#!/usr/bin/env python3
"""
MONTE CARLO ANALYZER FOR BACKTESTING RESULTS
Integrates MC pattern analysis with existing backtesting results
Analyzes JSON result files and generates comprehensive reports
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

# Import the Monte Carlo patterns module
from monte_carlo_patterns import analyze

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monte_carlo_analyzer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MonteCarloAnalyzer:
    """Analyze backtest results using Monte Carlo pattern analysis"""
    
    def __init__(self, output_dir: str = "monte_carlo_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"Monte Carlo Analyzer initialized. Output: {self.output_dir}")
        
    def extract_trades_from_backtest(self, backtest_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract trade data from backtest results in various formats"""
        try:
            # Format 1: Direct trades list
            if "trades" in backtest_result:
                trades = backtest_result["trades"]
                if isinstance(trades, list) and len(trades) > 0:
                    return {"trades": trades}
                    
            # Format 2: Equity curve
            if "equity_curve" in backtest_result:
                equity = backtest_result["equity_curve"]
                if isinstance(equity, list) and len(equity) > 0:
                    return {"equity": equity}
                    
            # Format 3: Results with metrics (extract from trades if available)
            if "results" in backtest_result:
                results = backtest_result["results"]
                if isinstance(results, dict):
                    if "trades" in results:
                        return {"trades": results["trades"]}
                    if "equity" in results:
                        return {"equity": results["equity"]}
                        
            # Format 4: Check for PnL list
            if "pnl" in backtest_result:
                pnl_list = backtest_result["pnl"]
                if isinstance(pnl_list, list) and len(pnl_list) > 0:
                    # Convert PnL list to trades format
                    trades = []
                    for i, pnl in enumerate(pnl_list):
                        trades.append({
                            "timestamp": i,
                            "pnl": pnl,
                            "hour": i % 24
                        })
                    return {"trades": trades}
                    
            logger.warning("Could not find trades or equity data in backtest result")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting trades from backtest: {e}")
            return None
            
    def analyze_backtest_file(
        self, 
        file_path: str, 
        runs: int = 1000, 
        block: int = 10, 
        window: int = 20,
        seed: int = 42
    ) -> Optional[Dict[str, Any]]:
        """Analyze a single backtest result file"""
        try:
            logger.info(f"Analyzing backtest file: {file_path}")
            
            # Load backtest results
            with open(file_path, 'r') as f:
                backtest_data = json.load(f)
                
            # Extract trade data
            trade_data = self.extract_trades_from_backtest(backtest_data)
            
            if trade_data is None:
                logger.warning(f"No valid trade data found in {file_path}")
                return None
                
            # Run Monte Carlo analysis
            mc_report = analyze(
                trade_data,
                runs=runs,
                block=block,
                window=window,
                seed=seed
            )
            
            # Add source information
            mc_report["source_file"] = str(file_path)
            mc_report["original_backtest"] = {
                "file": os.path.basename(file_path),
                "analyzed_at": datetime.now().isoformat()
            }
            
            # Save report
            report_filename = f"mc_pattern_{mc_report['run_id']}_{Path(file_path).stem}.json"
            report_path = self.output_dir / report_filename
            
            with open(report_path, 'w') as f:
                json.dump(mc_report, f, indent=2)
                
            logger.info(f"MC analysis complete. Report saved to: {report_path}")
            
            return mc_report
            
        except Exception as e:
            logger.error(f"Error analyzing backtest file {file_path}: {e}", exc_info=True)
            return None
            
    def analyze_directory(
        self, 
        directory: str, 
        pattern: str = "*.json",
        runs: int = 1000,
        block: int = 10,
        window: int = 20,
        max_files: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Analyze all backtest result files in a directory"""
        logger.info(f"Scanning directory: {directory}")
        logger.info(f"Looking for files matching: {pattern}")
        
        directory_path = Path(directory)
        if not directory_path.exists():
            logger.error(f"Directory does not exist: {directory}")
            return []
            
        # Find all matching files
        files = list(directory_path.glob(pattern))
        logger.info(f"Found {len(files)} matching files")
        
        if max_files is not None:
            files = files[:max_files]
            logger.info(f"Limiting to first {max_files} files")
            
        reports = []
        for i, file_path in enumerate(files, 1):
            logger.info(f"Processing file {i}/{len(files)}: {file_path.name}")
            
            report = self.analyze_backtest_file(
                str(file_path),
                runs=runs,
                block=block,
                window=window,
                seed=42 + i  # Different seed for each file
            )
            
            if report is not None:
                reports.append(report)
                
        logger.info(f"Successfully analyzed {len(reports)}/{len(files)} files")
        
        # Create summary report
        if reports:
            summary = self.create_summary_report(reports)
            summary_path = self.output_dir / f"mc_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
                
            logger.info(f"Summary report saved to: {summary_path}")
            
        return reports
        
    def create_summary_report(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary report from multiple MC analyses"""
        if not reports:
            return {"error": "No reports to summarize"}
            
        summary = {
            "generated_at": datetime.now().isoformat(),
            "total_analyses": len(reports),
            "statistics": {
                "sharpe": {
                    "base_mean": np.mean([r["base_metrics"]["sharpe"] for r in reports]),
                    "base_std": np.std([r["base_metrics"]["sharpe"] for r in reports]),
                    "mc_mean": np.mean([r["mc"]["sharpe_mean"] for r in reports]),
                    "mc_std": np.std([r["mc"]["sharpe_mean"] for r in reports])
                },
                "max_drawdown": {
                    "base_mean": np.mean([r["base_metrics"]["max_dd"] for r in reports]),
                    "base_std": np.std([r["base_metrics"]["max_dd"] for r in reports]),
                    "mc_mean": np.mean([r["mc"]["maxdd_mean"] for r in reports]),
                    "mc_std": np.std([r["mc"]["maxdd_mean"] for r in reports])
                },
                "leverageability": {
                    "uplift_mean": np.mean([r["leverageability"]["uplift_mean"] for r in reports]),
                    "uplift_std": np.std([r["leverageability"]["uplift_mean"] for r in reports]),
                    "positive_rate": np.mean([r["leverageability"]["uplift_frac_positive"] for r in reports])
                }
            },
            "best_strategies": [],
            "reports": reports
        }
        
        # Find best strategies by various metrics
        sorted_by_sharpe = sorted(reports, key=lambda x: x["base_metrics"]["sharpe"], reverse=True)[:5]
        sorted_by_leverage = sorted(reports, key=lambda x: x["leverageability"]["uplift_mean"], reverse=True)[:5]
        
        summary["best_strategies"] = {
            "by_sharpe": [
                {
                    "run_id": r["run_id"],
                    "source": r.get("source_file", "unknown"),
                    "sharpe": r["base_metrics"]["sharpe"],
                    "max_dd": r["base_metrics"]["max_dd"]
                }
                for r in sorted_by_sharpe
            ],
            "by_leverageability": [
                {
                    "run_id": r["run_id"],
                    "source": r.get("source_file", "unknown"),
                    "uplift_mean": r["leverageability"]["uplift_mean"],
                    "uplift_p95": r["leverageability"]["uplift_p95"]
                }
                for r in sorted_by_leverage
            ]
        }
        
        return summary
        
    def analyze_from_equity_curve(
        self, 
        equity_curve: List[float], 
        name: str = "custom",
        runs: int = 1000,
        block: int = 10,
        window: int = 20
    ) -> Dict[str, Any]:
        """Analyze directly from an equity curve"""
        logger.info(f"Analyzing equity curve: {name} ({len(equity_curve)} points)")
        
        mc_report = analyze(
            {"equity": equity_curve},
            runs=runs,
            block=block,
            window=window,
            seed=42
        )
        
        mc_report["name"] = name
        
        # Save report
        report_filename = f"mc_pattern_{mc_report['run_id']}_{name}.json"
        report_path = self.output_dir / report_filename
        
        with open(report_path, 'w') as f:
            json.dump(mc_report, f, indent=2)
            
        logger.info(f"MC analysis complete. Report saved to: {report_path}")
        
        return mc_report


def main():
    """Command-line interface for Monte Carlo analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monte Carlo Pattern Analysis for Backtesting Results")
    parser.add_argument("--file", type=str, help="Single backtest result file to analyze")
    parser.add_argument("--dir", type=str, help="Directory containing backtest results")
    parser.add_argument("--pattern", type=str, default="*.json", help="File pattern to match (default: *.json)")
    parser.add_argument("--runs", type=int, default=1000, help="Number of MC simulations (default: 1000)")
    parser.add_argument("--block", type=int, default=10, help="Block size for bootstrap (default: 10)")
    parser.add_argument("--window", type=int, default=20, help="Window size for motif discovery (default: 20)")
    parser.add_argument("--max-files", type=int, help="Maximum number of files to process")
    parser.add_argument("--output", type=str, default="monte_carlo_reports", help="Output directory")
    
    args = parser.parse_args()
    
    analyzer = MonteCarloAnalyzer(output_dir=args.output)
    
    if args.file:
        # Analyze single file
        report = analyzer.analyze_backtest_file(
            args.file,
            runs=args.runs,
            block=args.block,
            window=args.window
        )
        if report:
            print(f"\nAnalysis complete!")
            print(f"Run ID: {report['run_id']}")
            print(f"Base Sharpe: {report['base_metrics']['sharpe']:.3f}")
            print(f"MC Sharpe Mean: {report['mc']['sharpe_mean']:.3f}")
            print(f"Leverageability Uplift: {report['leverageability']['uplift_mean']:.3f}")
        else:
            print("Analysis failed.")
            
    elif args.dir:
        # Analyze directory
        reports = analyzer.analyze_directory(
            args.dir,
            pattern=args.pattern,
            runs=args.runs,
            block=args.block,
            window=args.window,
            max_files=args.max_files
        )
        print(f"\nAnalyzed {len(reports)} files successfully")
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()




