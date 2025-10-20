#!/usr/bin/env python3
"""
PROP FIRM STRATEGY OPTIMIZER
Filters and optimizes strategies for prop firm criteria
Supports: FTMO, Topstep, My Forex Funds, The5ers, etc.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
from mc_strategy_comparator import MCStrategyComparator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PropFirmCriteria:
    """Define prop firm evaluation criteria"""
    
    FTMO = {
        "name": "FTMO",
        "max_drawdown": 10.0,  # 10% max daily loss
        "profit_target": 10.0,  # 10% profit target
        "min_win_rate": 45.0,
        "max_daily_loss": 5.0,  # 5% max daily loss
        "min_sharpe": 1.5,
        "min_trades": 100,
        "max_leverage": 100
    }
    
    TOPSTEP = {
        "name": "Topstep",
        "max_drawdown": 3.0,  # $3,000 on $150k (2%)
        "profit_target": 6.0,  # $9,000 on $150k
        "min_win_rate": 50.0,
        "max_daily_loss": 2.0,  # $3,000 daily
        "min_sharpe": 2.0,
        "min_trades": 50,
        "consistency_score": 0.7
    }
    
    MY_FOREX_FUNDS = {
        "name": "My Forex Funds",
        "max_drawdown": 12.0,  # 12% max
        "profit_target": 8.0,  # 8% profit
        "min_win_rate": 45.0,
        "max_daily_loss": 5.0,
        "min_sharpe": 1.5,
        "min_trades": 100,
        "max_leverage": 100
    }
    
    THE5ERS = {
        "name": "The5ers",
        "max_drawdown": 6.0,  # 6% max
        "profit_target": 6.0,  # 6% profit
        "min_win_rate": 48.0,
        "max_daily_loss": 4.0,
        "min_sharpe": 1.8,
        "min_trades": 75,
        "max_leverage": 30
    }
    
    @classmethod
    def get_all_firms(cls):
        return [cls.FTMO, cls.TOPSTEP, cls.MY_FOREX_FUNDS, cls.THE5ERS]


class PropFirmStrategyOptimizer:
    """Optimize strategies for prop firm requirements"""
    
    def __init__(self, output_dir: str = "prop_firm_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.mc_comparator = MCStrategyComparator(output_dir=str(self.output_dir))
        
    def evaluate_strategy(self, strategy: Dict, criteria: Dict) -> Tuple[bool, Dict]:
        """Evaluate if strategy meets prop firm criteria"""
        results = strategy.get('results', {})
        scenario = strategy.get('scenario', {})
        
        evaluation = {
            "passes": True,
            "score": 0.0,
            "failures": [],
            "warnings": [],
            "strengths": []
        }
        
        total_checks = 0
        passed_checks = 0
        
        # Check Max Drawdown
        max_dd = results.get('max_drawdown_pct', 100)
        total_checks += 1
        if max_dd <= criteria['max_drawdown']:
            passed_checks += 1
            evaluation["strengths"].append(f"✅ Max DD {max_dd:.2f}% (limit: {criteria['max_drawdown']}%)")
        else:
            evaluation["passes"] = False
            evaluation["failures"].append(f"❌ Max DD {max_dd:.2f}% exceeds {criteria['max_drawdown']}%")
            
        # Check Win Rate
        win_rate = results.get('win_rate', 0)
        total_checks += 1
        if win_rate >= criteria['min_win_rate']:
            passed_checks += 1
            evaluation["strengths"].append(f"✅ Win Rate {win_rate:.1f}% (min: {criteria['min_win_rate']}%)")
        else:
            evaluation["passes"] = False
            evaluation["failures"].append(f"❌ Win Rate {win_rate:.1f}% below {criteria['min_win_rate']}%")
            
        # Check Sharpe Ratio
        sharpe = results.get('sharpe_ratio', 0)
        total_checks += 1
        if sharpe >= criteria['min_sharpe']:
            passed_checks += 1
            evaluation["strengths"].append(f"✅ Sharpe {sharpe:.2f} (min: {criteria['min_sharpe']})")
        else:
            evaluation["passes"] = False
            evaluation["failures"].append(f"❌ Sharpe {sharpe:.2f} below {criteria['min_sharpe']}")
            
        # Check Profit Target (assume over total trades)
        total_return = results.get('total_return_pct', 0)
        total_checks += 1
        if total_return >= criteria['profit_target']:
            passed_checks += 1
            evaluation["strengths"].append(f"✅ Return {total_return:.1f}% (target: {criteria['profit_target']}%)")
        else:
            evaluation["warnings"].append(f"⚠️ Return {total_return:.1f}% vs target {criteria['profit_target']}%")
            
        # Check Number of Trades
        total_trades = results.get('total_trades', 0)
        total_checks += 1
        if total_trades >= criteria['min_trades']:
            passed_checks += 1
            evaluation["strengths"].append(f"✅ {total_trades} trades (min: {criteria['min_trades']})")
        else:
            evaluation["warnings"].append(f"⚠️ Only {total_trades} trades (min: {criteria['min_trades']})")
            
        # Check Profit Factor
        profit_factor = results.get('profit_factor', 0)
        total_checks += 1
        if profit_factor >= 1.5:
            passed_checks += 1
            evaluation["strengths"].append(f"✅ Profit Factor {profit_factor:.2f}")
        elif profit_factor >= 1.2:
            evaluation["warnings"].append(f"⚠️ Profit Factor {profit_factor:.2f} (good, but could be higher)")
        else:
            evaluation["failures"].append(f"❌ Profit Factor {profit_factor:.2f} too low")
            evaluation["passes"] = False
            
        # Calculate score
        evaluation["score"] = (passed_checks / total_checks) * 100
        
        # Add overall assessment
        if evaluation["score"] >= 85:
            evaluation["grade"] = "EXCELLENT - Ready for prop firm"
        elif evaluation["score"] >= 70:
            evaluation["grade"] = "GOOD - Minor improvements needed"
        elif evaluation["score"] >= 50:
            evaluation["grade"] = "FAIR - Needs optimization"
        else:
            evaluation["grade"] = "POOR - Major improvements required"
            
        return evaluation["passes"], evaluation
        
    def find_prop_firm_strategies(
        self, 
        file_path: str, 
        firms: List[Dict] = None,
        top_n: int = 20
    ) -> Dict:
        """Find strategies that meet prop firm criteria"""
        
        if firms is None:
            firms = PropFirmCriteria.get_all_firms()
            
        logger.info(f"Loading strategies from: {file_path}")
        
        with open(file_path, 'r') as f:
            strategies = json.load(f)
            
        logger.info(f"Evaluating {len(strategies)} strategies against {len(firms)} prop firms")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_strategies": len(strategies),
            "firms": {},
            "universal_winners": [],  # Strategies that pass ALL firms
            "recommendations": []
        }
        
        # Evaluate each strategy against each firm
        for firm in firms:
            firm_name = firm['name']
            logger.info(f"\n{'='*80}")
            logger.info(f"EVALUATING FOR: {firm_name}")
            logger.info(f"{'='*80}")
            
            passing_strategies = []
            
            for strategy in strategies:
                passes, evaluation = self.evaluate_strategy(strategy, firm)
                
                if passes or evaluation['score'] >= 70:  # Include "good" strategies
                    passing_strategies.append({
                        'strategy': strategy,
                        'evaluation': evaluation,
                        'passes_strict': passes
                    })
                    
            # Sort by score
            passing_strategies.sort(key=lambda x: x['evaluation']['score'], reverse=True)
            
            logger.info(f"Found {len(passing_strategies)} strategies meeting {firm_name} criteria")
            
            results['firms'][firm_name] = {
                'criteria': firm,
                'passing_count': len([s for s in passing_strategies if s['passes_strict']]),
                'good_count': len(passing_strategies),
                'top_strategies': passing_strategies[:top_n]
            }
            
        # Find universal winners (pass ALL firms)
        logger.info(f"\n{'='*80}")
        logger.info("FINDING UNIVERSAL WINNERS (Pass ALL Firms)")
        logger.info(f"{'='*80}")
        
        for strategy in strategies:
            passes_all = True
            evaluations = {}
            min_score = 100.0
            
            for firm in firms:
                passes, evaluation = self.evaluate_strategy(strategy, firm)
                evaluations[firm['name']] = evaluation
                
                if not passes:
                    passes_all = False
                    
                min_score = min(min_score, evaluation['score'])
                
            if passes_all:
                results['universal_winners'].append({
                    'strategy': strategy,
                    'evaluations': evaluations,
                    'min_score': min_score
                })
                
        results['universal_winners'].sort(key=lambda x: x['min_score'], reverse=True)
        
        logger.info(f"Found {len(results['universal_winners'])} UNIVERSAL WINNERS!")
        
        # Generate recommendations
        self._generate_recommendations(results)
        
        # Save report
        report_path = self.output_dir / f"prop_firm_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"\nReport saved: {report_path}")
        
        # Print summary
        self._print_summary(results)
        
        return results
        
    def _generate_recommendations(self, results: Dict):
        """Generate actionable recommendations"""
        recommendations = []
        
        if results['universal_winners']:
            top_winner = results['universal_winners'][0]
            scenario = top_winner['strategy']['scenario']
            rec_results = top_winner['strategy']['results']
            
            recommendations.append({
                "priority": "HIGH",
                "action": "START HERE",
                "strategy": f"{scenario['pair']} {scenario['tf']} EMA({scenario.get('ema_fast')},{scenario.get('ema_mid')},{scenario.get('ema_slow')})",
                "reason": f"Passes ALL prop firms with {top_winner['min_score']:.1f}% score",
                "sharpe": rec_results['sharpe_ratio'],
                "win_rate": rec_results['win_rate'],
                "max_dd": rec_results['max_drawdown_pct']
            })
            
        # Find best for each firm
        for firm_name, firm_data in results['firms'].items():
            if firm_data['top_strategies']:
                top = firm_data['top_strategies'][0]
                scenario = top['strategy']['scenario']
                rec_results = top['strategy']['results']
                
                recommendations.append({
                    "priority": "MEDIUM",
                    "action": f"BEST FOR {firm_name}",
                    "strategy": f"{scenario['pair']} {scenario['tf']} EMA({scenario.get('ema_fast')},{scenario.get('ema_mid')},{scenario.get('ema_slow')})",
                    "reason": f"Score: {top['evaluation']['score']:.1f}%",
                    "sharpe": rec_results['sharpe_ratio'],
                    "win_rate": rec_results['win_rate'],
                    "max_dd": rec_results['max_drawdown_pct']
                })
                
        results['recommendations'] = recommendations
        
    def _print_summary(self, results: Dict):
        """Print analysis summary"""
        logger.info(f"\n{'='*80}")
        logger.info("PROP FIRM ANALYSIS SUMMARY")
        logger.info(f"{'='*80}")
        
        logger.info(f"Total Strategies Analyzed: {results['total_strategies']}")
        logger.info(f"Universal Winners (Pass ALL Firms): {len(results['universal_winners'])}")
        logger.info("")
        
        # Per-firm summary
        for firm_name, firm_data in results['firms'].items():
            logger.info(f"{firm_name}:")
            logger.info(f"  ✅ Passing (strict): {firm_data['passing_count']}")
            logger.info(f"  🟡 Good (70%+ score): {firm_data['good_count']}")
            
        logger.info("")
        logger.info(f"{'='*80}")
        logger.info("TOP RECOMMENDATIONS")
        logger.info(f"{'='*80}")
        
        for i, rec in enumerate(results['recommendations'][:5], 1):
            logger.info(f"\n{i}. [{rec['priority']}] {rec['action']}")
            logger.info(f"   Strategy: {rec['strategy']}")
            logger.info(f"   Sharpe: {rec['sharpe']:.2f} | Win Rate: {rec['win_rate']:.1f}% | Max DD: {rec['max_dd']:.2f}%")
            logger.info(f"   Reason: {rec['reason']}")
            
        logger.info(f"\n{'='*80}")
        
        # Print universal winners details
        if results['universal_winners']:
            logger.info("\n🏆 UNIVERSAL WINNERS (Pass ALL Prop Firms)")
            logger.info(f"{'='*80}")
            
            for i, winner in enumerate(results['universal_winners'][:10], 1):
                strategy = winner['strategy']
                scenario = strategy['scenario']
                res = strategy['results']
                
                logger.info(f"\n#{i} - {scenario['pair']} {scenario['tf']} | "
                          f"Sharpe: {res['sharpe_ratio']:.2f} | "
                          f"WR: {res['win_rate']:.1f}% | "
                          f"DD: {res['max_drawdown_pct']:.2f}%")
                logger.info(f"     Min Score: {winner['min_score']:.1f}%")
                
                # Show which firms it passes
                for firm_name, evaluation in winner['evaluations'].items():
                    logger.info(f"     {firm_name}: {evaluation['score']:.1f}% - {evaluation['grade']}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Prop Firm Strategy Optimizer")
    parser.add_argument("file", type=str, help="Strategy results JSON file")
    parser.add_argument("--firms", nargs="+", choices=["ftmo", "topstep", "mff", "the5ers", "all"],
                       default=["all"], help="Prop firms to evaluate for")
    parser.add_argument("--top-n", type=int, default=20, help="Number of top strategies per firm")
    parser.add_argument("--output", type=str, default="prop_firm_reports", help="Output directory")
    
    args = parser.parse_args()
    
    # Map firm names
    firm_map = {
        "ftmo": PropFirmCriteria.FTMO,
        "topstep": PropFirmCriteria.TOPSTEP,
        "mff": PropFirmCriteria.MY_FOREX_FUNDS,
        "the5ers": PropFirmCriteria.THE5ERS
    }
    
    if "all" in args.firms:
        firms = PropFirmCriteria.get_all_firms()
    else:
        firms = [firm_map[f] for f in args.firms]
        
    optimizer = PropFirmStrategyOptimizer(output_dir=args.output)
    results = optimizer.find_prop_firm_strategies(
        args.file,
        firms=firms,
        top_n=args.top_n
    )
    
    logger.info(f"\n✅ Analysis complete! Check {args.output}/ for detailed reports")


if __name__ == "__main__":
    main()




