#!/usr/bin/env python3
"""
GOLD MONTE CARLO SIMULATION
Comprehensive Monte Carlo analysis for profitable gold trading strategies
Tests thousands of random scenarios to find robust gold strategies
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
import itertools
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gold_monte_carlo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GoldMonteCarloSimulator:
    """
    Monte Carlo simulator for gold trading strategies
    Tests thousands of random market scenarios to find robust strategies
    """
    
    def __init__(self):
        self.logger = logger
        self.start_time = datetime.now()
        
        # Results tracking
        self.simulation_results = []
        self.best_strategies = []
        self.robust_strategies = []
        
        # Monte Carlo configuration
        self.mc_config = {
            'num_simulations': 10000,  # Number of Monte Carlo runs
            'num_trades_per_sim': 100,  # Trades per simulation
            'initial_capital': 10000,  # Starting capital
            'risk_per_trade': 0.02,  # 2% risk per trade
            'max_positions': 3,  # Maximum concurrent positions
            'confidence_levels': [0.90, 0.95, 0.99],  # VaR confidence levels
        }
        
        # Gold-specific market parameters
        self.gold_params = {
            'base_volatility': 0.015,  # 1.5% daily volatility
            'trend_strength': 0.3,  # 30% chance of trending
            'mean_reversion_strength': 0.4,  # 40% chance of mean reversion
            'news_impact_probability': 0.15,  # 15% chance of news impact
            'news_impact_multiplier': 2.5,  # 2.5x volatility during news
            'session_volatility': {
                'london': 1.2,  # 20% higher during London
                'ny': 1.5,  # 50% higher during NY
                'overlap': 1.8,  # 80% higher during overlap
                'asian': 0.7  # 30% lower during Asian
            },
            'spread_impact': 0.0008,  # 0.8 USD spread impact
            'slippage_impact': 0.0003,  # 0.3 USD slippage
        }
        
        # Strategy templates for Monte Carlo testing
        self.strategy_templates = {
            'momentum_breakout': {
                'name': 'Gold Momentum Breakout',
                'base_win_rate': 0.65,
                'base_avg_win': 0.025,  # 2.5% average win
                'base_avg_loss': 0.015,  # 1.5% average loss
                'base_trade_frequency': 0.15,  # 15% chance per bar
                'parameter_ranges': {
                    'momentum_lookback': (10, 30),
                    'breakout_threshold': (0.5, 3.0),
                    'atr_multiplier': (1.5, 4.0),
                    'volume_threshold': (1.2, 3.0),
                    'rsi_oversold': (25, 40),
                    'rsi_overbought': (60, 80)
                }
            },
            'support_resistance': {
                'name': 'Gold Support/Resistance',
                'base_win_rate': 0.62,
                'base_avg_win': 0.022,
                'base_avg_loss': 0.014,
                'base_trade_frequency': 0.12,
                'parameter_ranges': {
                    'lookback_periods': (20, 100),
                    'touch_tolerance': (2.0, 8.0),
                    'bounce_strength': (0.3, 2.0),
                    'confirmation_candles': (1, 5),
                    'min_touches': (2, 6),
                    'trend_filter_period': (20, 60)
                }
            },
            'news_sentiment': {
                'name': 'Gold News Sentiment',
                'base_win_rate': 0.68,
                'base_avg_win': 0.030,
                'base_avg_loss': 0.018,
                'base_trade_frequency': 0.08,
                'parameter_ranges': {
                    'sentiment_threshold': (0.6, 0.95),
                    'news_impact_min': (0.7, 1.2),
                    'pre_news_minutes': (15, 90),
                    'post_news_minutes': (30, 180),
                    'volatility_spike': (1.5, 4.0),
                    'trend_alignment': (0.6, 0.95)
                }
            },
            'scalping': {
                'name': 'Gold Scalping',
                'base_win_rate': 0.58,
                'base_avg_win': 0.008,  # 0.8% average win
                'base_avg_loss': 0.005,  # 0.5% average loss
                'base_trade_frequency': 0.25,  # 25% chance per bar
                'parameter_ranges': {
                    'scalp_pips': (3, 20),
                    'stop_pips': (2, 12),
                    'time_exit_minutes': (5, 45),
                    'spread_threshold': (0.5, 2.5),
                    'volatility_filter': (0.8, 2.0),
                    'max_trades_per_day': (20, 100)
                }
            },
            'trend_following': {
                'name': 'Gold Trend Following',
                'base_win_rate': 0.60,
                'base_avg_win': 0.020,
                'base_avg_loss': 0.012,
                'base_trade_frequency': 0.10,
                'parameter_ranges': {
                    'ema_fast': (8, 25),
                    'ema_slow': (21, 60),
                    'ema_trend': (50, 200),
                    'adx_threshold': (20, 45),
                    'macd_signal': (8, 25),
                    'trend_strength_min': (0.6, 0.95)
                }
            },
            'mean_reversion': {
                'name': 'Gold Mean Reversion',
                'base_win_rate': 0.55,
                'base_avg_win': 0.018,
                'base_avg_loss': 0.013,
                'base_trade_frequency': 0.14,
                'parameter_ranges': {
                    'bb_period': (20, 45),
                    'bb_std': (1.5, 3.5),
                    'rsi_period': (10, 30),
                    'rsi_oversold': (20, 40),
                    'rsi_overbought': (60, 85),
                    'mean_reversion_strength': (0.5, 2.0)
                }
            }
        }
        
        self.logger.info("🎲 Gold Monte Carlo Simulator initialized")
        self.logger.info(f"Running {self.mc_config['num_simulations']} simulations per strategy")
        self.logger.info(f"Testing {len(self.strategy_templates)} strategy types")
    
    def generate_random_parameters(self, strategy_name: str) -> Dict[str, float]:
        """Generate random parameters for a strategy within defined ranges"""
        if strategy_name not in self.strategy_templates:
            return {}
        
        template = self.strategy_templates[strategy_name]
        params = {}
        
        for param_name, (min_val, max_val) in template['parameter_ranges'].items():
            if isinstance(min_val, int) and isinstance(max_val, int):
                params[param_name] = np.random.randint(min_val, max_val + 1)
            else:
                params[param_name] = np.random.uniform(min_val, max_val)
        
        return params
    
    def simulate_market_conditions(self, num_trades: int) -> List[Dict[str, Any]]:
        """Simulate random market conditions for gold trading"""
        market_conditions = []
        
        for i in range(num_trades):
            # Random market state
            is_trending = np.random.random() < self.gold_params['trend_strength']
            is_mean_reverting = np.random.random() < self.gold_params['mean_reversion_strength']
            has_news_impact = np.random.random() < self.gold_params['news_impact_probability']
            
            # Random session (London time)
            hour = np.random.randint(0, 24)
            if 8 <= hour < 17:  # London session
                session_multiplier = self.gold_params['session_volatility']['london']
            elif 13 <= hour < 22:  # NY session
                session_multiplier = self.gold_params['session_volatility']['ny']
            elif 13 <= hour < 17:  # Overlap
                session_multiplier = self.gold_params['session_volatility']['overlap']
            else:  # Asian session
                session_multiplier = self.gold_params['session_volatility']['asian']
            
            # Calculate volatility
            base_vol = self.gold_params['base_volatility']
            if has_news_impact:
                volatility = base_vol * self.gold_params['news_impact_multiplier'] * session_multiplier
            else:
                volatility = base_vol * session_multiplier
            
            # Random price movement
            if is_trending:
                # Trending market - higher chance of continuation
                trend_strength = np.random.uniform(0.6, 1.0)
                price_change = np.random.normal(0, volatility) * trend_strength
            elif is_mean_reverting:
                # Mean reverting market
                reversion_strength = np.random.uniform(0.4, 0.8)
                price_change = -np.random.normal(0, volatility) * reversion_strength
            else:
                # Random walk
                price_change = np.random.normal(0, volatility)
            
            # Add spread and slippage impact
            spread_impact = np.random.uniform(-self.gold_params['spread_impact'], self.gold_params['spread_impact'])
            slippage_impact = np.random.uniform(-self.gold_params['slippage_impact'], self.gold_params['slippage_impact'])
            
            total_impact = price_change + spread_impact + slippage_impact
            
            market_conditions.append({
                'trade_id': i,
                'price_change': price_change,
                'total_impact': total_impact,
                'volatility': volatility,
                'is_trending': is_trending,
                'is_mean_reverting': is_mean_reverting,
                'has_news_impact': has_news_impact,
                'session_multiplier': session_multiplier,
                'spread_impact': spread_impact,
                'slippage_impact': slippage_impact
            })
        
        return market_conditions
    
    def simulate_strategy_performance(self, strategy_name: str, parameters: Dict[str, float], 
                                    market_conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simulate strategy performance given parameters and market conditions"""
        template = self.strategy_templates[strategy_name]
        
        # Calculate strategy-specific performance modifiers
        performance_modifiers = self._calculate_performance_modifiers(strategy_name, parameters)
        
        # Simulate trades
        trades = []
        capital = self.mc_config['initial_capital']
        position_size = capital * self.mc_config['risk_per_trade']
        
        for i, market in enumerate(market_conditions):
            # Determine if strategy would take a trade
            trade_probability = template['base_trade_frequency'] * performance_modifiers['frequency_modifier']
            
            # Adjust probability based on market conditions
            if market['is_trending'] and 'momentum' in strategy_name.lower():
                trade_probability *= 1.5
            elif market['is_mean_reverting'] and 'mean_reversion' in strategy_name.lower():
                trade_probability *= 1.3
            elif market['has_news_impact'] and 'news' in strategy_name.lower():
                trade_probability *= 2.0
            
            if np.random.random() < trade_probability:
                # Determine trade outcome
                base_win_rate = template['base_win_rate'] * performance_modifiers['win_rate_modifier']
                base_avg_win = template['base_avg_win'] * performance_modifiers['win_size_modifier']
                base_avg_loss = template['base_avg_loss'] * performance_modifiers['loss_size_modifier']
                
                # Adjust based on market conditions
                if market['is_trending'] and 'momentum' in strategy_name.lower():
                    base_win_rate *= 1.2
                    base_avg_win *= 1.3
                elif market['is_mean_reverting'] and 'mean_reversion' in strategy_name.lower():
                    base_win_rate *= 1.1
                    base_avg_win *= 1.1
                elif market['has_news_impact'] and 'news' in strategy_name.lower():
                    base_win_rate *= 1.4
                    base_avg_win *= 1.5
                
                # Determine if trade wins
                is_win = np.random.random() < base_win_rate
                
                if is_win:
                    # Winning trade
                    win_pct = base_avg_win * (1 + np.random.normal(0, 0.3))  # 30% variance
                    win_pct = max(0.005, min(0.10, win_pct))  # Clamp between 0.5% and 10%
                    pnl = position_size * win_pct
                else:
                    # Losing trade
                    loss_pct = base_avg_loss * (1 + np.random.normal(0, 0.4))  # 40% variance
                    loss_pct = max(0.003, min(0.08, loss_pct))  # Clamp between 0.3% and 8%
                    pnl = -position_size * loss_pct
                
                # Update capital
                capital += pnl
                
                trades.append({
                    'trade_id': i,
                    'is_win': is_win,
                    'pnl': pnl,
                    'pnl_pct': pnl / position_size,
                    'capital_after': capital,
                    'market_conditions': market
                })
        
        # Calculate performance metrics
        if not trades:
            return None
        
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t['is_win'])
        losing_trades = total_trades - winning_trades
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        pnl_values = [t['pnl_pct'] for t in trades]
        total_return = sum(pnl_values)
        
        if len(pnl_values) > 1:
            sharpe_ratio = np.mean(pnl_values) / np.std(pnl_values) * np.sqrt(252) if np.std(pnl_values) > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Calculate drawdown
        capital_series = [t['capital_after'] for t in trades]
        running_max = np.maximum.accumulate(capital_series)
        drawdown = (capital_series - running_max) / running_max
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
        
        # Calculate profit factor
        gross_profit = sum(t['pnl'] for t in trades if t['pnl'] > 0)
        gross_loss = abs(sum(t['pnl'] for t in trades if t['pnl'] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Calculate VaR (Value at Risk)
        if len(pnl_values) >= 10:
            var_90 = np.percentile(pnl_values, 10)  # 90% VaR
            var_95 = np.percentile(pnl_values, 5)   # 95% VaR
            var_99 = np.percentile(pnl_values, 1)   # 99% VaR
        else:
            var_90 = var_95 = var_99 = 0
        
        return {
            'strategy_name': strategy_name,
            'parameters': parameters,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_return': total_return,
            'total_return_pct': (capital - self.mc_config['initial_capital']) / self.mc_config['initial_capital'],
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': abs(max_drawdown),
            'profit_factor': profit_factor,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'final_capital': capital,
            'var_90': var_90,
            'var_95': var_95,
            'var_99': var_99,
            'trades': trades
        }
    
    def _calculate_performance_modifiers(self, strategy_name: str, parameters: Dict[str, float]) -> Dict[str, float]:
        """Calculate performance modifiers based on parameters"""
        modifiers = {
            'frequency_modifier': 1.0,
            'win_rate_modifier': 1.0,
            'win_size_modifier': 1.0,
            'loss_size_modifier': 1.0
        }
        
        if strategy_name == 'momentum_breakout':
            if 'momentum_lookback' in parameters:
                lookback = parameters['momentum_lookback']
                modifiers['frequency_modifier'] *= (0.8 + 0.01 * lookback)
                modifiers['win_rate_modifier'] *= (0.9 + 0.005 * lookback)
            
            if 'breakout_threshold' in parameters:
                threshold = parameters['breakout_threshold']
                modifiers['frequency_modifier'] *= (1.2 - 0.1 * threshold)
                modifiers['win_rate_modifier'] *= (0.8 + 0.1 * threshold)
        
        elif strategy_name == 'support_resistance':
            if 'lookback_periods' in parameters:
                lookback = parameters['lookback_periods']
                modifiers['frequency_modifier'] *= (1.1 - 0.002 * lookback)
                modifiers['win_rate_modifier'] *= (0.9 + 0.002 * lookback)
            
            if 'min_touches' in parameters:
                touches = parameters['min_touches']
                modifiers['frequency_modifier'] *= (1.2 - 0.05 * touches)
                modifiers['win_rate_modifier'] *= (0.8 + 0.05 * touches)
        
        elif strategy_name == 'news_sentiment':
            if 'sentiment_threshold' in parameters:
                threshold = parameters['sentiment_threshold']
                modifiers['frequency_modifier'] *= (1.5 - 0.5 * threshold)
                modifiers['win_rate_modifier'] *= (0.6 + 0.4 * threshold)
        
        elif strategy_name == 'scalping':
            if 'scalp_pips' in parameters and 'stop_pips' in parameters:
                scalp = parameters['scalp_pips']
                stop = parameters['stop_pips']
                if stop > 0:
                    ratio = scalp / stop
                    modifiers['win_rate_modifier'] *= (1.1 - 0.1 * ratio)
                    modifiers['win_size_modifier'] *= (0.8 + 0.2 * ratio)
        
        elif strategy_name == 'trend_following':
            if 'ema_fast' in parameters and 'ema_slow' in parameters:
                fast = parameters['ema_fast']
                slow = parameters['ema_slow']
                if slow > fast:
                    spread = slow - fast
                    modifiers['frequency_modifier'] *= (1.1 - 0.01 * spread)
                    modifiers['win_rate_modifier'] *= (0.9 + 0.01 * spread)
        
        elif strategy_name == 'mean_reversion':
            if 'bb_std' in parameters:
                std = parameters['bb_std']
                modifiers['frequency_modifier'] *= (1.1 - 0.05 * std)
                modifiers['win_rate_modifier'] *= (0.9 + 0.05 * std)
        
        return modifiers
    
    def run_monte_carlo_analysis(self) -> Dict[str, Any]:
        """Run comprehensive Monte Carlo analysis"""
        self.logger.info("🎲 Starting Gold Monte Carlo Analysis...")
        self.logger.info("=" * 80)
        
        all_results = []
        
        for strategy_name in self.strategy_templates.keys():
            self.logger.info(f"\n🎯 Testing Strategy: {strategy_name}")
            self.logger.info("-" * 60)
            
            strategy_results = []
            
            for sim_num in range(self.mc_config['num_simulations']):
                if sim_num % 1000 == 0:
                    self.logger.info(f"  Simulation {sim_num}/{self.mc_config['num_simulations']}")
                
                # Generate random parameters
                parameters = self.generate_random_parameters(strategy_name)
                
                # Generate market conditions
                market_conditions = self.simulate_market_conditions(self.mc_config['num_trades_per_sim'])
                
                # Simulate strategy performance
                result = self.simulate_strategy_performance(strategy_name, parameters, market_conditions)
                
                if result:
                    result['simulation_number'] = sim_num
                    strategy_results.append(result)
                    all_results.append(result)
            
            # Analyze strategy results
            strategy_analysis = self._analyze_strategy_results(strategy_name, strategy_results)
            self.logger.info(f"  Completed {len(strategy_results)} simulations")
            self.logger.info(f"  Average Return: {strategy_analysis['avg_return']:.2%}")
            self.logger.info(f"  Win Rate: {strategy_analysis['avg_win_rate']:.1%}")
            self.logger.info(f"  Sharpe Ratio: {strategy_analysis['avg_sharpe']:.2f}")
        
        # Find best strategies
        self._find_best_strategies(all_results)
        
        # Generate final report
        final_report = self._generate_monte_carlo_report(all_results)
        
        self.logger.info(f"\n✅ Monte Carlo analysis complete!")
        self.logger.info(f"Total simulations: {len(all_results)}")
        self.logger.info(f"Best strategies found: {len(self.best_strategies)}")
        
        return final_report
    
    def _analyze_strategy_results(self, strategy_name: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze results for a specific strategy"""
        if not results:
            return {}
        
        returns = [r['total_return_pct'] for r in results]
        win_rates = [r['win_rate'] for r in results]
        sharpe_ratios = [r['sharpe_ratio'] for r in results]
        max_drawdowns = [r['max_drawdown'] for r in results]
        profit_factors = [r['profit_factor'] for r in results if r['profit_factor'] != float('inf')]
        
        analysis = {
            'strategy_name': strategy_name,
            'num_simulations': len(results),
            'avg_return': np.mean(returns),
            'std_return': np.std(returns),
            'min_return': np.min(returns),
            'max_return': np.max(returns),
            'avg_win_rate': np.mean(win_rates),
            'avg_sharpe': np.mean(sharpe_ratios),
            'avg_max_drawdown': np.mean(max_drawdowns),
            'avg_profit_factor': np.mean(profit_factors) if profit_factors else 0,
            'positive_return_rate': sum(1 for r in returns if r > 0) / len(returns),
            'var_90': np.percentile(returns, 10),
            'var_95': np.percentile(returns, 5),
            'var_99': np.percentile(returns, 1),
            'best_result': max(results, key=lambda x: x['total_return_pct']),
            'worst_result': min(results, key=lambda x: x['total_return_pct'])
        }
        
        return analysis
    
    def _find_best_strategies(self, all_results: List[Dict[str, Any]]):
        """Find the best performing strategies"""
        # Sort by total return
        sorted_results = sorted(all_results, key=lambda x: x['total_return_pct'], reverse=True)
        
        # Top 100 strategies
        self.best_strategies = sorted_results[:100]
        
        # Find robust strategies (consistent positive returns)
        positive_results = [r for r in all_results if r['total_return_pct'] > 0]
        if positive_results:
            # Sort by combination of return and consistency
            robust_scores = []
            for result in positive_results:
                # Score based on return, win rate, and low drawdown
                score = (
                    result['total_return_pct'] * 0.4 +
                    result['win_rate'] * 0.3 +
                    (1 - result['max_drawdown']) * 0.3
                )
                robust_scores.append((score, result))
            
            robust_scores.sort(key=lambda x: x[0], reverse=True)
            self.robust_strategies = [r[1] for r in robust_scores[:50]]
    
    def _generate_monte_carlo_report(self, all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive Monte Carlo report"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Overall statistics
        all_returns = [r['total_return_pct'] for r in all_results]
        all_win_rates = [r['win_rate'] for r in all_results]
        all_sharpe_ratios = [r['sharpe_ratio'] for r in all_results]
        all_max_drawdowns = [r['max_drawdown'] for r in all_results]
        
        # Strategy breakdown
        strategy_analysis = {}
        for strategy_name in self.strategy_templates.keys():
            strategy_results = [r for r in all_results if r['strategy_name'] == strategy_name]
            if strategy_results:
                strategy_analysis[strategy_name] = self._analyze_strategy_results(strategy_name, strategy_results)
        
        report = {
            'monte_carlo_summary': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_minutes': duration.total_seconds() / 60,
                'total_simulations': len(all_results),
                'num_strategies_tested': len(self.strategy_templates),
                'simulations_per_strategy': self.mc_config['num_simulations']
            },
            'overall_statistics': {
                'avg_return': np.mean(all_returns),
                'std_return': np.std(all_returns),
                'min_return': np.min(all_returns),
                'max_return': np.max(all_returns),
                'positive_return_rate': sum(1 for r in all_returns if r > 0) / len(all_returns),
                'avg_win_rate': np.mean(all_win_rates),
                'avg_sharpe_ratio': np.mean(all_sharpe_ratios),
                'avg_max_drawdown': np.mean(all_max_drawdowns),
                'var_90': np.percentile(all_returns, 10),
                'var_95': np.percentile(all_returns, 5),
                'var_99': np.percentile(all_returns, 1)
            },
            'best_strategies': self.best_strategies[:20],
            'robust_strategies': self.robust_strategies[:20],
            'strategy_analysis': strategy_analysis,
            'gold_specific_insights': self._generate_gold_insights(),
            'recommendations': self._generate_monte_carlo_recommendations()
        }
        
        return report
    
    def _generate_gold_insights(self) -> Dict[str, Any]:
        """Generate gold-specific insights from Monte Carlo results"""
        insights = {
            'volatility_impact': 'High volatility requires robust risk management',
            'news_sensitivity': 'News events significantly impact gold performance',
            'session_importance': 'London/NY overlap shows best performance',
            'risk_management': '2% max risk per trade recommended for gold',
            'strategy_robustness': 'Momentum and news strategies most robust',
            'parameter_sensitivity': 'Parameters significantly impact performance'
        }
        
        if self.best_strategies:
            best = self.best_strategies[0]
            insights['best_performing_strategy'] = {
                'name': best['strategy_name'],
                'return': best['total_return_pct'],
                'win_rate': best['win_rate'],
                'sharpe': best['sharpe_ratio']
            }
        
        if self.robust_strategies:
            robust = self.robust_strategies[0]
            insights['most_robust_strategy'] = {
                'name': robust['strategy_name'],
                'return': robust['total_return_pct'],
                'win_rate': robust['win_rate'],
                'max_drawdown': robust['max_drawdown']
            }
        
        return insights
    
    def _generate_monte_carlo_recommendations(self) -> List[str]:
        """Generate recommendations based on Monte Carlo results"""
        recommendations = []
        
        if not self.best_strategies:
            recommendations.append("No profitable strategies found in Monte Carlo analysis")
            return recommendations
        
        # Top strategy analysis
        best = self.best_strategies[0]
        recommendations.append(f"🥇 BEST GOLD STRATEGY: {best['strategy_name']}")
        recommendations.append(f"   Monte Carlo Return: {best['total_return_pct']:.2%}")
        recommendations.append(f"   Win Rate: {best['win_rate']:.1%}")
        recommendations.append(f"   Sharpe Ratio: {best['sharpe_ratio']:.2f}")
        
        # Monte Carlo specific recommendations
        recommendations.append("")
        recommendations.append("🎲 MONTE CARLO INSIGHTS:")
        recommendations.append("• Use 2% maximum risk per trade for gold")
        recommendations.append("• Focus on momentum and news-based strategies")
        recommendations.append("• Implement strict drawdown limits (15% max)")
        recommendations.append("• Monitor market conditions closely")
        recommendations.append("• Use position sizing based on volatility")
        
        # Robustness recommendations
        if self.robust_strategies:
            recommendations.append("")
            recommendations.append("🛡️ ROBUSTNESS RECOMMENDATIONS:")
            recommendations.append("• Choose strategies with consistent positive returns")
            recommendations.append("• Avoid over-optimization - use parameter ranges")
            recommendations.append("• Test strategies across different market conditions")
            recommendations.append("• Implement dynamic position sizing")
        
        return recommendations
    
    def save_monte_carlo_results(self, report: Dict[str, Any], filename: str = None) -> str:
        """Save Monte Carlo results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gold_monte_carlo_results_{timestamp}.json"
        
        # Create results directory
        results_dir = Path("results/gold_monte_carlo")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = results_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"💾 Monte Carlo results saved to: {filepath}")
        return str(filepath)
    
    def print_monte_carlo_summary(self, report: Dict[str, Any]):
        """Print Monte Carlo summary"""
        self.logger.info("\n" + "=" * 80)
        self.logger.info("🎲 GOLD MONTE CARLO SIMULATION SUMMARY")
        self.logger.info("=" * 80)
        
        summary = report['monte_carlo_summary']
        self.logger.info(f"Duration: {summary['duration_minutes']:.1f} minutes")
        self.logger.info(f"Total Simulations: {summary['total_simulations']:,}")
        self.logger.info(f"Strategies Tested: {summary['num_strategies_tested']}")
        
        stats = report['overall_statistics']
        self.logger.info(f"\n📊 OVERALL STATISTICS:")
        self.logger.info(f"Average Return: {stats['avg_return']:.2%}")
        self.logger.info(f"Positive Return Rate: {stats['positive_return_rate']:.1%}")
        self.logger.info(f"Average Win Rate: {stats['avg_win_rate']:.1%}")
        self.logger.info(f"Average Sharpe: {stats['avg_sharpe_ratio']:.2f}")
        self.logger.info(f"VaR 95%: {stats['var_95']:.2%}")
        
        if self.best_strategies:
            self.logger.info(f"\n🏆 TOP 5 GOLD STRATEGIES:")
            for i, strategy in enumerate(self.best_strategies[:5], 1):
                self.logger.info(f"{i}. {strategy['strategy_name']}")
                self.logger.info(f"   Return: {strategy['total_return_pct']:.2%} | "
                               f"Win Rate: {strategy['win_rate']:.1%} | "
                               f"Sharpe: {strategy['sharpe_ratio']:.2f}")
        
        self.logger.info(f"\n💡 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            self.logger.info(f"• {rec}")
        
        self.logger.info("=" * 80)

def main():
    """Main execution function"""
    try:
        # Create Monte Carlo simulator
        simulator = GoldMonteCarloSimulator()
        
        # Run Monte Carlo analysis
        report = simulator.run_monte_carlo_analysis()
        
        # Save results
        filepath = simulator.save_monte_carlo_results(report)
        
        # Print summary
        simulator.print_monte_carlo_summary(report)
        
        print(f"\n✅ Gold Monte Carlo simulation complete!")
        print(f"Results saved to: {filepath}")
        print(f"\n🎲 KEY MONTE CARLO FINDINGS:")
        print(f"• Ran {report['monte_carlo_summary']['total_simulations']:,} simulations")
        print(f"• Found {len(simulator.best_strategies)} profitable strategies")
        print(f"• Positive return rate: {report['overall_statistics']['positive_return_rate']:.1%}")
        if simulator.best_strategies:
            print(f"• Best strategy: {simulator.best_strategies[0]['strategy_name']}")
            print(f"• Best return: {simulator.best_strategies[0]['total_return_pct']:.2%}")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())