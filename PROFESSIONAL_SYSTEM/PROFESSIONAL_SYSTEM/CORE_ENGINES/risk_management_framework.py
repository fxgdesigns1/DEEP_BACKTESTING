#!/usr/bin/env python3
"""
RISK MANAGEMENT FRAMEWORK
Comprehensive risk management system for trading strategies
"""

import pandas as pd
import numpy as np
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class RiskManagementFramework:
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.logger = logging.getLogger(__name__)
        
        # Risk parameters
        self.max_risk_per_trade = 0.02  # 2% risk per trade
        self.max_daily_risk = 0.06  # 6% max daily risk
        self.max_portfolio_risk = 0.20  # 20% max portfolio risk
        self.max_correlation = 0.7  # Maximum correlation between positions
        
        # Position sizing
        self.position_sizing_method = 'fixed_fractional'  # or 'kelly', 'volatility_adjusted'
        self.kelly_fraction = 0.25  # Kelly fraction (25% of optimal)
        
        # Portfolio tracking
        self.positions = {}
        self.daily_pnl = {}
        self.portfolio_metrics = {}
        self.correlation_matrix = {}
        
        # Risk monitoring
        self.risk_alerts = []
        self.risk_limits = {
            'max_drawdown': 0.15,  # 15% max drawdown
            'max_consecutive_losses': 5,
            'max_daily_trades': 10,
            'max_positions': 5
        }
        
        self.logger.info("🛡️ Risk Management Framework initialized")
    
    def calculate_position_size(self, signal: Dict[str, Any], account_balance: float = None) -> Dict[str, Any]:
        """Calculate optimal position size based on risk parameters"""
        try:
            if account_balance is None:
                account_balance = self.current_capital
            
            entry_price = signal['entry_price']
            stop_loss = signal['stop_loss']
            direction = signal['direction']
            confidence = signal.get('confidence', 50)
            
            # Calculate risk per unit
            if direction == 'LONG':
                risk_per_unit = entry_price - stop_loss
            else:
                risk_per_unit = stop_loss - entry_price
            
            if risk_per_unit <= 0:
                return {'error': 'Invalid stop loss'}
            
            # Calculate risk amount based on confidence
            base_risk = account_balance * self.max_risk_per_trade
            confidence_multiplier = confidence / 100.0
            adjusted_risk = base_risk * confidence_multiplier
            
            # Apply position sizing method
            if self.position_sizing_method == 'fixed_fractional':
                position_size = adjusted_risk / risk_per_unit
            elif self.position_sizing_method == 'kelly':
                # Simplified Kelly criterion
                win_rate = 0.6  # Assume 60% win rate
                avg_win = 2.0 * risk_per_unit  # Assume 2:1 RR
                avg_loss = risk_per_unit
                kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
                kelly_fraction = max(0, min(kelly_fraction, self.kelly_fraction))
                position_size = (account_balance * kelly_fraction) / risk_per_unit
            elif self.position_sizing_method == 'volatility_adjusted':
                # Adjust for volatility
                volatility_factor = 1.0  # Could be based on ATR
                position_size = (adjusted_risk * volatility_factor) / risk_per_unit
            else:
                position_size = adjusted_risk / risk_per_unit
            
            # Apply maximum position size limits
            max_position_value = account_balance * 0.1  # Max 10% of account per position
            max_position_size = max_position_value / entry_price
            position_size = min(position_size, max_position_size)
            
            # Calculate position value and risk
            position_value = position_size * entry_price
            position_risk = position_size * risk_per_unit
            
            return {
                'position_size': position_size,
                'position_value': position_value,
                'position_risk': position_risk,
                'risk_percentage': (position_risk / account_balance) * 100,
                'risk_per_unit': risk_per_unit,
                'confidence_multiplier': confidence_multiplier
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return {'error': str(e)}
    
    def check_risk_limits(self, signal: Dict[str, Any], position_size: Dict[str, Any]) -> Dict[str, Any]:
        """Check if trade violates risk limits"""
        try:
            violations = []
            warnings = []
            
            # Check daily risk limit
            today = datetime.now().strftime('%Y-%m-%d')
            daily_risk = self.daily_pnl.get(today, {}).get('total_risk', 0)
            new_daily_risk = daily_risk + position_size['position_risk']
            
            if new_daily_risk > self.current_capital * self.max_daily_risk:
                violations.append(f"Daily risk limit exceeded: {new_daily_risk:.2f} > {self.current_capital * self.max_daily_risk:.2f}")
            
            # Check portfolio risk limit
            total_portfolio_risk = sum(pos.get('risk', 0) for pos in self.positions.values())
            new_portfolio_risk = total_portfolio_risk + position_size['position_risk']
            
            if new_portfolio_risk > self.current_capital * self.max_portfolio_risk:
                violations.append(f"Portfolio risk limit exceeded: {new_portfolio_risk:.2f} > {self.current_capital * self.max_portfolio_risk:.2f}")
            
            # Check maximum positions
            if len(self.positions) >= self.risk_limits['max_positions']:
                violations.append(f"Maximum positions limit exceeded: {len(self.positions)} >= {self.risk_limits['max_positions']}")
            
            # Check daily trade limit
            daily_trades = self.daily_pnl.get(today, {}).get('trade_count', 0)
            if daily_trades >= self.risk_limits['max_daily_trades']:
                violations.append(f"Daily trade limit exceeded: {daily_trades} >= {self.risk_limits['max_daily_trades']}")
            
            # Check correlation limits
            correlation_warning = self._check_correlation_limits(signal['symbol'])
            if correlation_warning:
                warnings.append(correlation_warning)
            
            # Check drawdown limits
            current_drawdown = self._calculate_current_drawdown()
            if current_drawdown > self.risk_limits['max_drawdown']:
                violations.append(f"Maximum drawdown exceeded: {current_drawdown:.2%} > {self.risk_limits['max_drawdown']:.2%}")
            
            # Check consecutive losses
            consecutive_losses = self._count_consecutive_losses()
            if consecutive_losses >= self.risk_limits['max_consecutive_losses']:
                violations.append(f"Maximum consecutive losses exceeded: {consecutive_losses} >= {self.risk_limits['max_consecutive_losses']}")
            
            return {
                'approved': len(violations) == 0,
                'violations': violations,
                'warnings': warnings,
                'risk_metrics': {
                    'daily_risk': new_daily_risk,
                    'portfolio_risk': new_portfolio_risk,
                    'current_drawdown': current_drawdown,
                    'consecutive_losses': consecutive_losses
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error checking risk limits: {e}")
            return {'approved': False, 'violations': [f'Error: {str(e)}'], 'warnings': []}
    
    def _check_correlation_limits(self, new_symbol: str) -> Optional[str]:
        """Check correlation limits with existing positions"""
        try:
            if not self.positions:
                return None
            
            # Simple correlation check based on currency pairs
            new_base = new_symbol[:3]
            new_quote = new_symbol[4:]
            
            for symbol, position in self.positions.items():
                existing_base = symbol[:3]
                existing_quote = symbol[4:]
                
                # Check for direct correlation
                if new_base == existing_base or new_quote == existing_quote:
                    return f"High correlation with existing position {symbol}"
                
                # Check for inverse correlation
                if new_base == existing_quote and new_quote == existing_base:
                    return f"Inverse correlation with existing position {symbol}"
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking correlation limits: {e}")
            return None
    
    def _calculate_current_drawdown(self) -> float:
        """Calculate current drawdown from peak"""
        try:
            if not self.portfolio_metrics:
                return 0.0
            
            peak_capital = max(self.portfolio_metrics.get('peak_capital', self.initial_capital), self.initial_capital)
            current_drawdown = (peak_capital - self.current_capital) / peak_capital
            
            return max(0.0, current_drawdown)
            
        except Exception as e:
            self.logger.error(f"Error calculating drawdown: {e}")
            return 0.0
    
    def _count_consecutive_losses(self) -> int:
        """Count consecutive losing trades"""
        try:
            if not self.portfolio_metrics.get('trade_history', []):
                return 0
            
            consecutive_losses = 0
            trade_history = self.portfolio_metrics['trade_history']
            
            # Count from the end
            for trade in reversed(trade_history):
                if trade.get('result') == 'LOSS':
                    consecutive_losses += 1
                else:
                    break
            
            return consecutive_losses
            
        except Exception as e:
            self.logger.error(f"Error counting consecutive losses: {e}")
            return 0
    
    def add_position(self, signal: Dict[str, Any], position_size: Dict[str, Any]) -> bool:
        """Add a new position to the portfolio"""
        try:
            symbol = signal['symbol']
            position_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            position = {
                'id': position_id,
                'symbol': symbol,
                'direction': signal['direction'],
                'entry_price': signal['entry_price'],
                'stop_loss': signal['stop_loss'],
                'take_profit': signal['take_profit'],
                'position_size': position_size['position_size'],
                'position_value': position_size['position_value'],
                'risk': position_size['position_risk'],
                'entry_time': datetime.now(),
                'status': 'OPEN',
                'confidence': signal.get('confidence', 50)
            }
            
            self.positions[position_id] = position
            
            # Update daily P&L tracking
            today = datetime.now().strftime('%Y-%m-%d')
            if today not in self.daily_pnl:
                self.daily_pnl[today] = {'total_risk': 0, 'trade_count': 0, 'positions': []}
            
            self.daily_pnl[today]['total_risk'] += position_size['position_risk']
            self.daily_pnl[today]['trade_count'] += 1
            self.daily_pnl[today]['positions'].append(position_id)
            
            self.logger.info(f"Added position {position_id}: {symbol} {signal['direction']} @ {signal['entry_price']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding position: {e}")
            return False
    
    def update_position(self, position_id: str, exit_price: float, exit_reason: str) -> Dict[str, Any]:
        """Update position with exit information"""
        try:
            if position_id not in self.positions:
                return {'error': 'Position not found'}
            
            position = self.positions[position_id]
            entry_price = position['entry_price']
            direction = position['direction']
            position_size = position['position_size']
            
            # Calculate P&L
            if direction == 'LONG':
                pnl = (exit_price - entry_price) * position_size
            else:
                pnl = (entry_price - exit_price) * position_size
            
            # Update position
            position['exit_price'] = exit_price
            position['exit_time'] = datetime.now()
            position['status'] = 'CLOSED'
            position['pnl'] = pnl
            position['exit_reason'] = exit_reason
            position['result'] = 'WIN' if pnl > 0 else 'LOSS'
            
            # Update capital
            self.current_capital += pnl
            
            # Update portfolio metrics
            self._update_portfolio_metrics(position)
            
            # Remove from active positions
            del self.positions[position_id]
            
            self.logger.info(f"Closed position {position_id}: {position['result']} P&L: {pnl:.2f}")
            
            return {
                'position_id': position_id,
                'pnl': pnl,
                'result': position['result'],
                'new_capital': self.current_capital
            }
            
        except Exception as e:
            self.logger.error(f"Error updating position: {e}")
            return {'error': str(e)}
    
    def _update_portfolio_metrics(self, position: Dict[str, Any]):
        """Update portfolio performance metrics"""
        try:
            if 'trade_history' not in self.portfolio_metrics:
                self.portfolio_metrics['trade_history'] = []
            
            # Add to trade history
            self.portfolio_metrics['trade_history'].append(position)
            
            # Update peak capital
            if 'peak_capital' not in self.portfolio_metrics:
                self.portfolio_metrics['peak_capital'] = self.initial_capital
            
            self.portfolio_metrics['peak_capital'] = max(self.portfolio_metrics['peak_capital'], self.current_capital)
            
            # Calculate performance metrics
            trades = self.portfolio_metrics['trade_history']
            if trades:
                wins = [t for t in trades if t.get('result') == 'WIN']
                losses = [t for t in trades if t.get('result') == 'LOSS']
                
                self.portfolio_metrics['total_trades'] = len(trades)
                self.portfolio_metrics['winning_trades'] = len(wins)
                self.portfolio_metrics['losing_trades'] = len(losses)
                self.portfolio_metrics['win_rate'] = len(wins) / len(trades) * 100 if trades else 0
                self.portfolio_metrics['total_pnl'] = sum(t.get('pnl', 0) for t in trades)
                self.portfolio_metrics['avg_win'] = np.mean([t.get('pnl', 0) for t in wins]) if wins else 0
                self.portfolio_metrics['avg_loss'] = np.mean([t.get('pnl', 0) for t in losses]) if losses else 0
                
                # Calculate profit factor
                total_wins = sum(t.get('pnl', 0) for t in wins) if wins else 0
                total_losses = abs(sum(t.get('pnl', 0) for t in losses)) if losses else 0
                self.portfolio_metrics['profit_factor'] = total_wins / total_losses if total_losses > 0 else float('inf')
                
                # Calculate Sharpe ratio
                returns = [t.get('pnl', 0) for t in trades]
                if returns and np.std(returns) > 0:
                    self.portfolio_metrics['sharpe_ratio'] = np.mean(returns) / np.std(returns)
                else:
                    self.portfolio_metrics['sharpe_ratio'] = 0
            
        except Exception as e:
            self.logger.error(f"Error updating portfolio metrics: {e}")
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary"""
        try:
            summary = {
                'capital': {
                    'initial': self.initial_capital,
                    'current': self.current_capital,
                    'total_return': self.current_capital - self.initial_capital,
                    'return_percentage': ((self.current_capital - self.initial_capital) / self.initial_capital) * 100
                },
                'risk_metrics': {
                    'current_drawdown': self._calculate_current_drawdown(),
                    'max_drawdown': self.portfolio_metrics.get('max_drawdown', 0),
                    'consecutive_losses': self._count_consecutive_losses(),
                    'active_positions': len(self.positions),
                    'daily_risk': self.daily_pnl.get(datetime.now().strftime('%Y-%m-%d'), {}).get('total_risk', 0)
                },
                'performance': self.portfolio_metrics.copy(),
                'positions': {
                    'active': len(self.positions),
                    'details': list(self.positions.values())
                }
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio summary: {e}")
            return {'error': str(e)}
    
    def generate_risk_report(self) -> str:
        """Generate comprehensive risk report"""
        try:
            summary = self.get_portfolio_summary()
            
            report = f"""
🛡️ RISK MANAGEMENT REPORT
{'='*50}

CAPITAL STATUS:
  Initial Capital: ${summary['capital']['initial']:,.2f}
  Current Capital: ${summary['capital']['current']:,.2f}
  Total Return: ${summary['capital']['total_return']:,.2f} ({summary['capital']['return_percentage']:.2f}%)
  Current Drawdown: {summary['risk_metrics']['current_drawdown']:.2%}

RISK METRICS:
  Active Positions: {summary['risk_metrics']['active_positions']}
  Daily Risk: ${summary['risk_metrics']['daily_risk']:,.2f}
  Consecutive Losses: {summary['risk_metrics']['consecutive_losses']}
  Max Drawdown: {summary['risk_metrics']['max_drawdown']:.2%}

PERFORMANCE:
  Total Trades: {summary['performance'].get('total_trades', 0)}
  Win Rate: {summary['performance'].get('win_rate', 0):.1f}%
  Profit Factor: {summary['performance'].get('profit_factor', 0):.2f}
  Sharpe Ratio: {summary['performance'].get('sharpe_ratio', 0):.2f}

ACTIVE POSITIONS:
"""
            
            for position in summary['positions']['details']:
                report += f"  {position['symbol']} {position['direction']} @ {position['entry_price']:.5f}\n"
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating risk report: {e}")
            return f"Error generating report: {str(e)}"

def main():
    """Main function to test Risk Management Framework"""
    risk_manager = RiskManagementFramework(initial_capital=10000.0)
    
    print("🛡️ Risk Management Framework initialized!")
    print("\n📊 Key Features:")
    print("• Position sizing based on risk percentage")
    print("• Daily and portfolio risk limits")
    print("• Correlation monitoring")
    print("• Drawdown protection")
    print("• Consecutive loss limits")
    print("• Comprehensive portfolio tracking")
    print("• Real-time risk monitoring")

if __name__ == "__main__":
    main()
