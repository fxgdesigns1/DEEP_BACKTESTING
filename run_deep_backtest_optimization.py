#!/usr/bin/env python3
"""
DEEP BACKTEST OPTIMIZATION RUNNER
Executes comprehensive strategy optimization for real market deployment
"""

import os
import sys
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'deep_backtest_runner_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DeepBacktestRunner:
    """Orchestrates the deep backtest optimization process"""
    
    def __init__(self):
        self.logger = logger
        self.start_time = datetime.now()
        self.results_dir = Path("results/deep_backtest_optimization")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("🚀 Deep Backtest Optimization Runner initialized")
        self.logger.info(f"Results directory: {self.results_dir}")
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        self.logger.info("🔍 Checking prerequisites...")
        
        # Check for required files
        required_files = [
            "deep_backtest_optimizer.py",
            "optimal_strategy_deployment.yaml",
            "strategies/ultra_strict_v3_strategy.py",
            "strategies/prop_firm_challenge_strategy.py",
            "strategies/session_highs_lows_strategy.py",
            "strategies/quick_scalper_strategy.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.logger.error(f"❌ Missing required files: {missing_files}")
            return False
        
        # Check for data directory
        data_dir = Path("data/MASTER_DATASET")
        if not data_dir.exists():
            self.logger.error("❌ MASTER_DATASET not found!")
            self.logger.error("Please ensure real historical data is available")
            return False
        
        # Check for required timeframes
        required_timeframes = ['5m', '15m', '30m', '1h', '4h']
        available_timeframes = [d.name for d in data_dir.iterdir() if d.is_dir()]
        
        missing_timeframes = [tf for tf in required_timeframes if tf not in available_timeframes]
        if missing_timeframes:
            self.logger.warning(f"⚠️ Missing timeframes: {missing_timeframes}")
        
        # Check for required pairs
        required_pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 'USD_CAD', 'NZD_USD', 'XAU_USD']
        available_pairs = set()
        
        for tf in available_timeframes:
            tf_path = data_dir / tf
            files = list(tf_path.glob('*.csv'))
            for file in files:
                pair = file.stem.replace(f'_{tf}', '')
                available_pairs.add(pair)
        
        missing_pairs = [pair for pair in required_pairs if pair not in available_pairs]
        if missing_pairs:
            self.logger.warning(f"⚠️ Missing pairs: {missing_pairs}")
        
        self.logger.info("✅ Prerequisites check complete")
        return True
    
    def run_optimization(self) -> bool:
        """Run the deep backtest optimization"""
        self.logger.info("🎯 Starting deep backtest optimization...")
        
        try:
            # Run the optimizer
            result = subprocess.run([
                sys.executable, "deep_backtest_optimizer.py"
            ], capture_output=True, text=True, timeout=3600)  # 1 hour timeout
            
            if result.returncode == 0:
                self.logger.info("✅ Optimization completed successfully")
                self.logger.info("Optimization output:")
                self.logger.info(result.stdout)
                return True
            else:
                self.logger.error("❌ Optimization failed")
                self.logger.error("Error output:")
                self.logger.error(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("❌ Optimization timed out after 1 hour")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error running optimization: {e}")
            return False
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analyze optimization results"""
        self.logger.info("📊 Analyzing optimization results...")
        
        # Look for results files
        results_files = list(self.results_dir.glob("deep_backtest_results_*.json"))
        
        if not results_files:
            self.logger.error("❌ No results files found")
            return {}
        
        # Get the latest results file
        latest_file = max(results_files, key=lambda x: x.stat().st_mtime)
        self.logger.info(f"📁 Analyzing results from: {latest_file}")
        
        try:
            with open(latest_file, 'r') as f:
                results = json.load(f)
            
            # Extract key insights
            analysis = {
                'file': str(latest_file),
                'total_tests': results.get('optimization_summary', {}).get('total_tests', 0),
                'successful_tests': results.get('optimization_summary', {}).get('successful_tests', 0),
                'success_rate': results.get('optimization_summary', {}).get('success_rate', 0),
                'best_strategies': results.get('best_strategies', [])[:5],
                'strategy_breakdown': results.get('strategy_breakdown', {}),
                'pair_breakdown': results.get('pair_breakdown', {}),
                'timeframe_breakdown': results.get('timeframe_breakdown', {}),
                'recommendations': results.get('recommendations', [])
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing results: {e}")
            return {}
    
    def generate_deployment_config(self, analysis: Dict[str, Any]) -> str:
        """Generate deployment configuration based on results"""
        self.logger.info("⚙️ Generating deployment configuration...")
        
        if not analysis.get('best_strategies'):
            self.logger.error("❌ No best strategies found for deployment config")
            return ""
        
        # Get top strategy
        top_strategy = analysis['best_strategies'][0]
        
        # Create deployment config
        deployment_config = {
            'generated_at': datetime.now().isoformat(),
            'based_on_file': analysis.get('file', ''),
            'optimization_summary': {
                'total_tests': analysis.get('total_tests', 0),
                'success_rate': analysis.get('success_rate', 0),
                'best_strategy': top_strategy.get('strategy', 'unknown')
            },
            'recommended_strategy': {
                'name': top_strategy.get('strategy', 'unknown'),
                'pair': top_strategy.get('pair', 'unknown'),
                'timeframe': top_strategy.get('timeframe', 'unknown'),
                'parameters': top_strategy.get('parameters', {}),
                'performance': {
                    'sharpe_ratio': top_strategy.get('sharpe_ratio', 0),
                    'win_rate': top_strategy.get('win_rate', 0),
                    'max_drawdown': top_strategy.get('max_drawdown', 0),
                    'total_trades': top_strategy.get('total_trades', 0),
                    'profit_factor': top_strategy.get('profit_factor', 0)
                }
            },
            'deployment_phases': {
                'phase_1_demo': {
                    'duration_weeks': 2,
                    'risk_multiplier': 0.5,
                    'monitoring_frequency': 'hourly'
                },
                'phase_2_limited': {
                    'duration_weeks': 2,
                    'risk_multiplier': 0.75,
                    'monitoring_frequency': '30min'
                },
                'phase_3_full': {
                    'duration_weeks': 'ongoing',
                    'risk_multiplier': 1.0,
                    'monitoring_frequency': '15min'
                }
            },
            'risk_management': {
                'max_daily_loss': 0.05,
                'max_drawdown': 0.12,
                'max_positions': 3,
                'portfolio_risk_limit': 0.15
            },
            'monitoring': {
                'telegram_alerts': True,
                'performance_alerts': True,
                'risk_alerts': True
            }
        }
        
        # Save deployment config
        config_file = self.results_dir / f"deployment_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(config_file, 'w') as f:
            json.dump(deployment_config, f, indent=2)
        
        self.logger.info(f"💾 Deployment config saved to: {config_file}")
        return str(config_file)
    
    def generate_summary_report(self, analysis: Dict[str, Any]) -> str:
        """Generate comprehensive summary report"""
        self.logger.info("📋 Generating summary report...")
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("DEEP BACKTEST OPTIMIZATION SUMMARY REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Duration: {datetime.now() - self.start_time}")
        report_lines.append("")
        
        # Optimization summary
        report_lines.append("OPTIMIZATION SUMMARY")
        report_lines.append("-" * 40)
        report_lines.append(f"Total Tests: {analysis.get('total_tests', 0):,}")
        report_lines.append(f"Successful: {analysis.get('successful_tests', 0):,}")
        report_lines.append(f"Success Rate: {analysis.get('success_rate', 0):.1%}")
        report_lines.append("")
        
        # Best strategies
        if analysis.get('best_strategies'):
            report_lines.append("TOP 5 STRATEGIES")
            report_lines.append("-" * 40)
            for i, strategy in enumerate(analysis['best_strategies'][:5], 1):
                report_lines.append(f"{i}. {strategy.get('strategy', 'unknown')} - {strategy.get('pair', 'unknown')} {strategy.get('timeframe', 'unknown')}")
                report_lines.append(f"   Sharpe: {strategy.get('sharpe_ratio', 0):.2f} | "
                                  f"Win Rate: {strategy.get('win_rate', 0):.1%} | "
                                  f"Trades: {strategy.get('total_trades', 0)} | "
                                  f"Max DD: {strategy.get('max_drawdown', 0):.1%}")
                report_lines.append("")
        
        # Strategy breakdown
        if analysis.get('strategy_breakdown'):
            report_lines.append("STRATEGY BREAKDOWN")
            report_lines.append("-" * 40)
            for strategy, stats in analysis['strategy_breakdown'].items():
                report_lines.append(f"{strategy}:")
                report_lines.append(f"  Count: {stats.get('count', 0)}")
                report_lines.append(f"  Avg Sharpe: {stats.get('avg_sharpe', 0):.2f}")
                report_lines.append(f"  Avg Win Rate: {stats.get('avg_win_rate', 0):.1%}")
                report_lines.append(f"  Best Sharpe: {stats.get('best_sharpe', 0):.2f}")
                report_lines.append("")
        
        # Pair breakdown
        if analysis.get('pair_breakdown'):
            report_lines.append("PAIR BREAKDOWN")
            report_lines.append("-" * 40)
            for pair, stats in analysis['pair_breakdown'].items():
                report_lines.append(f"{pair}: {stats.get('count', 0)} tests, "
                                  f"Avg Sharpe: {stats.get('avg_sharpe', 0):.2f}, "
                                  f"Best Sharpe: {stats.get('best_sharpe', 0):.2f}")
            report_lines.append("")
        
        # Recommendations
        if analysis.get('recommendations'):
            report_lines.append("RECOMMENDATIONS")
            report_lines.append("-" * 40)
            for rec in analysis['recommendations']:
                report_lines.append(f"• {rec}")
            report_lines.append("")
        
        # Next steps
        report_lines.append("NEXT STEPS")
        report_lines.append("-" * 40)
        report_lines.append("1. Review the top performing strategies above")
        report_lines.append("2. Deploy the best strategy on demo account")
        report_lines.append("3. Monitor performance for 2-4 weeks")
        report_lines.append("4. Gradually increase position sizes if performance is good")
        report_lines.append("5. Consider portfolio approach with top 3 strategies")
        report_lines.append("")
        
        report_lines.append("=" * 80)
        
        # Save report
        report_file = self.results_dir / f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_file, 'w') as f:
            f.write('\n'.join(report_lines))
        
        self.logger.info(f"📄 Summary report saved to: {report_file}")
        return str(report_file)
    
    def run_complete_optimization(self) -> bool:
        """Run the complete optimization process"""
        self.logger.info("🚀 Starting complete deep backtest optimization process...")
        self.logger.info("=" * 80)
        
        try:
            # Step 1: Check prerequisites
            if not self.check_prerequisites():
                self.logger.error("❌ Prerequisites check failed")
                return False
            
            # Step 2: Run optimization
            if not self.run_optimization():
                self.logger.error("❌ Optimization failed")
                return False
            
            # Step 3: Analyze results
            analysis = self.analyze_results()
            if not analysis:
                self.logger.error("❌ Results analysis failed")
                return False
            
            # Step 4: Generate deployment config
            config_file = self.generate_deployment_config(analysis)
            if not config_file:
                self.logger.error("❌ Deployment config generation failed")
                return False
            
            # Step 5: Generate summary report
            report_file = self.generate_summary_report(analysis)
            if not report_file:
                self.logger.error("❌ Summary report generation failed")
                return False
            
            # Final summary
            self.logger.info("")
            self.logger.info("=" * 80)
            self.logger.info("✅ DEEP BACKTEST OPTIMIZATION COMPLETE!")
            self.logger.info("=" * 80)
            self.logger.info(f"Results directory: {self.results_dir}")
            self.logger.info(f"Deployment config: {config_file}")
            self.logger.info(f"Summary report: {report_file}")
            self.logger.info("")
            self.logger.info("Next steps:")
            self.logger.info("1. Review the summary report")
            self.logger.info("2. Deploy the best strategy on demo account")
            self.logger.info("3. Monitor performance for 2-4 weeks")
            self.logger.info("4. Gradually increase position sizes if performance is good")
            self.logger.info("=" * 80)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Fatal error in optimization process: {e}")
            return False

def main():
    """Main execution function"""
    try:
        # Create runner
        runner = DeepBacktestRunner()
        
        # Run complete optimization
        success = runner.run_complete_optimization()
        
        if success:
            print("\n✅ Deep backtest optimization completed successfully!")
            print("Check the results directory for detailed reports and deployment configurations.")
            return 0
        else:
            print("\n❌ Deep backtest optimization failed!")
            print("Check the logs for error details.")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())