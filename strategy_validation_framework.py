#!/usr/bin/env python3
"""
STRATEGY VALIDATION FRAMEWORK
Comprehensive validation of trading strategies for real market deployment
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('strategy_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StrategyValidationFramework:
    """
    Comprehensive strategy validation framework
    Validates strategies for real market deployment
    """
    
    def __init__(self):
        self.logger = logger
        self.start_time = datetime.now()
        
        # Validation criteria
        self.validation_criteria = {
            'min_trades': 50,
            'min_win_rate': 0.45,
            'min_sharpe_ratio': 1.0,
            'max_drawdown': 0.15,
            'min_profit_factor': 1.3,
            'max_consecutive_losses': 8,
            'min_avg_trade_duration_hours': 2,
            'max_avg_trade_duration_hours': 48,
            'min_consistency_score': 0.60
        }
        
        # Results tracking
        self.validation_results = []
        self.passed_strategies = []
        self.failed_strategies = []
        
        self.logger.info("🔍 Strategy Validation Framework initialized")
    
    def validate_strategy(self, strategy_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single strategy result"""
        self.logger.info(f"🔍 Validating strategy: {strategy_result.get('strategy', 'unknown')}")
        
        validation_result = {
            'strategy': strategy_result.get('strategy', 'unknown'),
            'pair': strategy_result.get('pair', 'unknown'),
            'timeframe': strategy_result.get('timeframe', 'unknown'),
            'parameters': strategy_result.get('parameters', {}),
            'validation_passed': False,
            'validation_score': 0.0,
            'criteria_checks': {},
            'warnings': [],
            'recommendations': []
        }
        
        # Check each validation criterion
        criteria_checks = {}
        warnings = []
        recommendations = []
        
        # 1. Minimum trades
        total_trades = strategy_result.get('total_trades', 0)
        criteria_checks['min_trades'] = {
            'required': self.validation_criteria['min_trades'],
            'actual': total_trades,
            'passed': total_trades >= self.validation_criteria['min_trades']
        }
        
        if not criteria_checks['min_trades']['passed']:
            warnings.append(f"Insufficient trades: {total_trades} < {self.validation_criteria['min_trades']}")
        
        # 2. Win rate
        win_rate = strategy_result.get('win_rate', 0)
        criteria_checks['win_rate'] = {
            'required': self.validation_criteria['min_win_rate'],
            'actual': win_rate,
            'passed': win_rate >= self.validation_criteria['min_win_rate']
        }
        
        if not criteria_checks['win_rate']['passed']:
            warnings.append(f"Low win rate: {win_rate:.1%} < {self.validation_criteria['min_win_rate']:.1%}")
        elif win_rate > 0.70:
            recommendations.append("High win rate - consider increasing position size")
        
        # 3. Sharpe ratio
        sharpe_ratio = strategy_result.get('sharpe_ratio', 0)
        criteria_checks['sharpe_ratio'] = {
            'required': self.validation_criteria['min_sharpe_ratio'],
            'actual': sharpe_ratio,
            'passed': sharpe_ratio >= self.validation_criteria['min_sharpe_ratio']
        }
        
        if not criteria_checks['sharpe_ratio']['passed']:
            warnings.append(f"Low Sharpe ratio: {sharpe_ratio:.2f} < {self.validation_criteria['min_sharpe_ratio']}")
        elif sharpe_ratio > 2.0:
            recommendations.append("Excellent Sharpe ratio - consider as primary strategy")
        
        # 4. Maximum drawdown
        max_drawdown = strategy_result.get('max_drawdown', 0)
        criteria_checks['max_drawdown'] = {
            'required': self.validation_criteria['max_drawdown'],
            'actual': max_drawdown,
            'passed': max_drawdown <= self.validation_criteria['max_drawdown']
        }
        
        if not criteria_checks['max_drawdown']['passed']:
            warnings.append(f"High drawdown: {max_drawdown:.1%} > {self.validation_criteria['max_drawdown']:.1%}")
        elif max_drawdown < 0.05:
            recommendations.append("Very low drawdown - consider increasing risk")
        
        # 5. Profit factor
        profit_factor = strategy_result.get('profit_factor', 0)
        criteria_checks['profit_factor'] = {
            'required': self.validation_criteria['min_profit_factor'],
            'actual': profit_factor,
            'passed': profit_factor >= self.validation_criteria['min_profit_factor']
        }
        
        if not criteria_checks['profit_factor']['passed']:
            warnings.append(f"Low profit factor: {profit_factor:.2f} < {self.validation_criteria['min_profit_factor']}")
        elif profit_factor > 2.5:
            recommendations.append("Excellent profit factor - consider as primary strategy")
        
        # 6. Consecutive losses (if trades data available)
        trades = strategy_result.get('trades', [])
        if trades:
            consecutive_losses = self._calculate_consecutive_losses(trades)
            criteria_checks['consecutive_losses'] = {
                'required': self.validation_criteria['max_consecutive_losses'],
                'actual': consecutive_losses,
                'passed': consecutive_losses <= self.validation_criteria['max_consecutive_losses']
            }
            
            if not criteria_checks['consecutive_losses']['passed']:
                warnings.append(f"Too many consecutive losses: {consecutive_losses} > {self.validation_criteria['max_consecutive_losses']}")
        
        # 7. Trade duration (if trades data available)
        if trades:
            avg_duration = self._calculate_avg_trade_duration(trades)
            criteria_checks['avg_trade_duration'] = {
                'required_min': self.validation_criteria['min_avg_trade_duration_hours'],
                'required_max': self.validation_criteria['max_avg_trade_duration_hours'],
                'actual': avg_duration,
                'passed': (self.validation_criteria['min_avg_trade_duration_hours'] <= 
                          avg_duration <= self.validation_criteria['max_avg_trade_duration_hours'])
            }
            
            if not criteria_checks['avg_trade_duration']['passed']:
                if avg_duration < self.validation_criteria['min_avg_trade_duration_hours']:
                    warnings.append(f"Trades too short: {avg_duration:.1f}h < {self.validation_criteria['min_avg_trade_duration_hours']}h")
                else:
                    warnings.append(f"Trades too long: {avg_duration:.1f}h > {self.validation_criteria['max_avg_trade_duration_hours']}h")
        
        # 8. Consistency score
        consistency_score = self._calculate_consistency_score(strategy_result)
        criteria_checks['consistency_score'] = {
            'required': self.validation_criteria['min_consistency_score'],
            'actual': consistency_score,
            'passed': consistency_score >= self.validation_criteria['min_consistency_score']
        }
        
        if not criteria_checks['consistency_score']['passed']:
            warnings.append(f"Low consistency: {consistency_score:.2f} < {self.validation_criteria['min_consistency_score']}")
        elif consistency_score > 0.80:
            recommendations.append("High consistency - consider for portfolio approach")
        
        # Calculate overall validation score
        passed_checks = sum(1 for check in criteria_checks.values() if check['passed'])
        total_checks = len(criteria_checks)
        validation_score = passed_checks / total_checks if total_checks > 0 else 0
        
        # Determine if validation passed
        validation_passed = validation_score >= 0.70  # 70% of criteria must pass
        
        # Update validation result
        validation_result.update({
            'validation_passed': validation_passed,
            'validation_score': validation_score,
            'criteria_checks': criteria_checks,
            'warnings': warnings,
            'recommendations': recommendations
        })
        
        # Log result
        if validation_passed:
            self.logger.info(f"✅ Validation passed: {validation_score:.1%} ({passed_checks}/{total_checks} criteria)")
            self.passed_strategies.append(validation_result)
        else:
            self.logger.info(f"❌ Validation failed: {validation_score:.1%} ({passed_checks}/{total_checks} criteria)")
            self.failed_strategies.append(validation_result)
        
        return validation_result
    
    def _calculate_consecutive_losses(self, trades: List[Dict]) -> int:
        """Calculate maximum consecutive losses"""
        if not trades:
            return 0
        
        max_consecutive = 0
        current_consecutive = 0
        
        for trade in trades:
            if trade.get('result') == 'LOSS':
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def _calculate_avg_trade_duration(self, trades: List[Dict]) -> float:
        """Calculate average trade duration in hours"""
        if not trades:
            return 0
        
        durations = []
        for trade in trades:
            if 'entry_time' in trade and 'exit_time' in trade:
                try:
                    entry_time = pd.to_datetime(trade['entry_time'])
                    exit_time = pd.to_datetime(trade['exit_time'])
                    duration = (exit_time - entry_time).total_seconds() / 3600  # Convert to hours
                    durations.append(duration)
                except:
                    continue
        
        return np.mean(durations) if durations else 0
    
    def _calculate_consistency_score(self, strategy_result: Dict[str, Any]) -> float:
        """Calculate consistency score based on performance stability"""
        try:
            # Get key metrics
            win_rate = strategy_result.get('win_rate', 0)
            sharpe_ratio = strategy_result.get('sharpe_ratio', 0)
            profit_factor = strategy_result.get('profit_factor', 0)
            max_drawdown = strategy_result.get('max_drawdown', 0)
            
            # Normalize metrics (0-1 scale)
            win_rate_norm = min(win_rate, 1.0)
            sharpe_norm = min(sharpe_ratio / 3.0, 1.0)  # 3.0 is excellent Sharpe
            profit_factor_norm = min(profit_factor / 3.0, 1.0)  # 3.0 is excellent PF
            drawdown_norm = max(0, 1.0 - max_drawdown / 0.20)  # 20% is bad drawdown
            
            # Calculate consistency score
            consistency_score = (
                win_rate_norm * 0.3 +
                sharpe_norm * 0.3 +
                profit_factor_norm * 0.2 +
                drawdown_norm * 0.2
            )
            
            return min(consistency_score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating consistency score: {e}")
            return 0.0
    
    def validate_strategies(self, strategies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate multiple strategies"""
        self.logger.info(f"🔍 Validating {len(strategies)} strategies...")
        
        validation_results = []
        
        for i, strategy in enumerate(strategies, 1):
            self.logger.info(f"[{i}/{len(strategies)}] Validating {strategy.get('strategy', 'unknown')} - {strategy.get('pair', 'unknown')} {strategy.get('timeframe', 'unknown')}")
            
            validation_result = self.validate_strategy(strategy)
            validation_results.append(validation_result)
        
        # Generate summary
        summary = self._generate_validation_summary(validation_results)
        
        return {
            'validation_results': validation_results,
            'summary': summary,
            'passed_strategies': self.passed_strategies,
            'failed_strategies': self.failed_strategies
        }
    
    def _generate_validation_summary(self, validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate validation summary"""
        total_strategies = len(validation_results)
        passed_strategies = len(self.passed_strategies)
        failed_strategies = len(self.failed_strategies)
        
        # Calculate average scores
        avg_validation_score = np.mean([r['validation_score'] for r in validation_results])
        avg_win_rate = np.mean([r['criteria_checks']['win_rate']['actual'] for r in validation_results if 'win_rate' in r['criteria_checks']])
        avg_sharpe = np.mean([r['criteria_checks']['sharpe_ratio']['actual'] for r in validation_results if 'sharpe_ratio' in r['criteria_checks']])
        avg_drawdown = np.mean([r['criteria_checks']['max_drawdown']['actual'] for r in validation_results if 'max_drawdown' in r['criteria_checks']])
        
        # Strategy breakdown
        strategy_breakdown = {}
        for result in validation_results:
            strategy = result['strategy']
            if strategy not in strategy_breakdown:
                strategy_breakdown[strategy] = {'total': 0, 'passed': 0, 'failed': 0}
            
            strategy_breakdown[strategy]['total'] += 1
            if result['validation_passed']:
                strategy_breakdown[strategy]['passed'] += 1
            else:
                strategy_breakdown[strategy]['failed'] += 1
        
        # Pair breakdown
        pair_breakdown = {}
        for result in validation_results:
            pair = result['pair']
            if pair not in pair_breakdown:
                pair_breakdown[pair] = {'total': 0, 'passed': 0, 'failed': 0}
            
            pair_breakdown[pair]['total'] += 1
            if result['validation_passed']:
                pair_breakdown[pair]['passed'] += 1
            else:
                pair_breakdown[pair]['failed'] += 1
        
        # Timeframe breakdown
        timeframe_breakdown = {}
        for result in validation_results:
            tf = result['timeframe']
            if tf not in timeframe_breakdown:
                timeframe_breakdown[tf] = {'total': 0, 'passed': 0, 'failed': 0}
            
            timeframe_breakdown[tf]['total'] += 1
            if result['validation_passed']:
                timeframe_breakdown[tf]['passed'] += 1
            else:
                timeframe_breakdown[tf]['failed'] += 1
        
        return {
            'total_strategies': total_strategies,
            'passed_strategies': passed_strategies,
            'failed_strategies': failed_strategies,
            'pass_rate': passed_strategies / total_strategies if total_strategies > 0 else 0,
            'avg_validation_score': avg_validation_score,
            'avg_win_rate': avg_win_rate,
            'avg_sharpe_ratio': avg_sharpe,
            'avg_max_drawdown': avg_drawdown,
            'strategy_breakdown': strategy_breakdown,
            'pair_breakdown': pair_breakdown,
            'timeframe_breakdown': timeframe_breakdown
        }
    
    def generate_validation_report(self, validation_data: Dict[str, Any]) -> str:
        """Generate comprehensive validation report"""
        self.logger.info("📋 Generating validation report...")
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("STRATEGY VALIDATION REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Duration: {datetime.now() - self.start_time}")
        report_lines.append("")
        
        # Summary
        summary = validation_data['summary']
        report_lines.append("VALIDATION SUMMARY")
        report_lines.append("-" * 40)
        report_lines.append(f"Total Strategies: {summary['total_strategies']}")
        report_lines.append(f"Passed: {summary['passed_strategies']}")
        report_lines.append(f"Failed: {summary['failed_strategies']}")
        report_lines.append(f"Pass Rate: {summary['pass_rate']:.1%}")
        report_lines.append(f"Average Validation Score: {summary['avg_validation_score']:.1%}")
        report_lines.append("")
        
        # Performance metrics
        report_lines.append("AVERAGE PERFORMANCE METRICS")
        report_lines.append("-" * 40)
        report_lines.append(f"Average Win Rate: {summary['avg_win_rate']:.1%}")
        report_lines.append(f"Average Sharpe Ratio: {summary['avg_sharpe_ratio']:.2f}")
        report_lines.append(f"Average Max Drawdown: {summary['avg_max_drawdown']:.1%}")
        report_lines.append("")
        
        # Passed strategies
        if self.passed_strategies:
            report_lines.append("PASSED STRATEGIES")
            report_lines.append("-" * 40)
            for i, strategy in enumerate(self.passed_strategies[:10], 1):
                report_lines.append(f"{i}. {strategy['strategy']} - {strategy['pair']} {strategy['timeframe']}")
                report_lines.append(f"   Validation Score: {strategy['validation_score']:.1%}")
                report_lines.append(f"   Win Rate: {strategy['criteria_checks']['win_rate']['actual']:.1%}")
                report_lines.append(f"   Sharpe Ratio: {strategy['criteria_checks']['sharpe_ratio']['actual']:.2f}")
                report_lines.append(f"   Max Drawdown: {strategy['criteria_checks']['max_drawdown']['actual']:.1%}")
                if strategy['recommendations']:
                    report_lines.append(f"   Recommendations: {', '.join(strategy['recommendations'])}")
                report_lines.append("")
        
        # Strategy breakdown
        if summary['strategy_breakdown']:
            report_lines.append("STRATEGY BREAKDOWN")
            report_lines.append("-" * 40)
            for strategy, stats in summary['strategy_breakdown'].items():
                pass_rate = stats['passed'] / stats['total'] if stats['total'] > 0 else 0
                report_lines.append(f"{strategy}: {stats['passed']}/{stats['total']} ({pass_rate:.1%})")
            report_lines.append("")
        
        # Pair breakdown
        if summary['pair_breakdown']:
            report_lines.append("PAIR BREAKDOWN")
            report_lines.append("-" * 40)
            for pair, stats in summary['pair_breakdown'].items():
                pass_rate = stats['passed'] / stats['total'] if stats['total'] > 0 else 0
                report_lines.append(f"{pair}: {stats['passed']}/{stats['total']} ({pass_rate:.1%})")
            report_lines.append("")
        
        # Recommendations
        report_lines.append("DEPLOYMENT RECOMMENDATIONS")
        report_lines.append("-" * 40)
        if self.passed_strategies:
            report_lines.append("1. Deploy top 3-5 passed strategies on demo accounts")
            report_lines.append("2. Monitor performance for 2-4 weeks")
            report_lines.append("3. Gradually increase position sizes for best performers")
            report_lines.append("4. Consider portfolio approach with diverse strategies")
        else:
            report_lines.append("1. No strategies passed validation - review criteria")
            report_lines.append("2. Consider relaxing validation requirements")
            report_lines.append("3. Test additional parameter combinations")
            report_lines.append("4. Review data quality and strategy logic")
        report_lines.append("")
        
        report_lines.append("=" * 80)
        
        # Save report
        report_file = f"strategy_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_file, 'w') as f:
            f.write('\n'.join(report_lines))
        
        self.logger.info(f"📄 Validation report saved to: {report_file}")
        return report_file

def main():
    """Main execution function"""
    try:
        # Create validation framework
        validator = StrategyValidationFramework()
        
        # Load strategies from results (this would be loaded from actual results)
        # For demonstration, we'll create some sample strategies
        sample_strategies = [
            {
                'strategy': 'ultra_strict_v3',
                'pair': 'EUR_USD',
                'timeframe': '1h',
                'parameters': {'min_rr_ratio': 3.0, 'min_confidence': 85},
                'total_trades': 75,
                'win_rate': 0.68,
                'sharpe_ratio': 2.1,
                'max_drawdown': 0.08,
                'profit_factor': 2.8,
                'trades': []  # Would contain actual trade data
            },
            {
                'strategy': 'prop_firm_challenge',
                'pair': 'GBP_USD',
                'timeframe': '15m',
                'parameters': {'signal_strength_min': 0.75, 'confluence_required': 3},
                'total_trades': 120,
                'win_rate': 0.62,
                'sharpe_ratio': 1.8,
                'max_drawdown': 0.06,
                'profit_factor': 2.2,
                'trades': []
            }
        ]
        
        # Validate strategies
        validation_data = validator.validate_strategies(sample_strategies)
        
        # Generate report
        report_file = validator.generate_validation_report(validation_data)
        
        print(f"✅ Strategy validation complete!")
        print(f"Report saved to: {report_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())