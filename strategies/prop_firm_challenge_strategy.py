#!/usr/bin/env python3
"""
PROP FIRM CHALLENGE STRATEGY
Optimized for prop firm challenges (FTMO, MyForexFunds, The5%ers, etc.)
Focus on consistency, controlled risk, and meeting challenge requirements
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class PropFirmChallengeStrategy:
    """
    Conservative strategy optimized for prop firm challenges
    Focuses on: High win rate, controlled drawdown, consistency
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Prop firm challenge parameters
        self.profit_target = self.config.get('profit_target', 0.10)  # 10%
        self.max_daily_loss = self.config.get('max_daily_loss', 0.05)  # 5%
        self.max_total_loss = self.config.get('max_total_loss', 0.10)  # 10%
        self.min_trading_days = self.config.get('min_trading_days', 5)
        
        # Entry requirements (STRICT)
        self.signal_strength_min = self.config.get('signal_strength_min', 0.70)
        self.confluence_required = self.config.get('confluence_required', 3)
        
        # Risk management (CONSERVATIVE)
        self.risk_per_trade = self.config.get('risk_per_trade', 0.01)  # 1%
        self.max_trades_per_day = self.config.get('max_trades_per_day', 5)
        self.daily_profit_target = self.config.get('daily_profit_target', 0.02)  # 2%
        self.stop_trading_after_loss = self.config.get('stop_trading_after_loss', 0.03)  # 3%
        
        # Exit parameters
        self.tp_rr_ratio = self.config.get('tp_rr_ratio', 2.5)
        self.partial_tp_enabled = self.config.get('partial_tp_enabled', True)
        self.trailing_stop_trigger = self.config.get('trailing_stop_trigger', 1.5)
        self.breakeven_trigger = self.config.get('breakeven_trigger', 0.8)
        
        # Tracking
        self.daily_stats = {}
        self.total_profit = 0.0
        self.trading_days = 0
        self.current_daily_pnl = 0.0
        self.daily_trades_count = 0
        self.daily_stopped = False
        
    def check_daily_limits(self, current_date: date) -> bool:
        """Check if we can still trade today"""
        # Reset daily tracking if new day
        if current_date not in self.daily_stats:
            self.current_daily_pnl = 0.0
            self.daily_trades_count = 0
            self.daily_stopped = False
            self.daily_stats[current_date] = {
                'pnl': 0.0,
                'trades': 0,
                'stopped': False
            }
        
        # Check if already stopped for the day
        if self.daily_stopped:
            return False
        
        # Check max trades per day
        if self.daily_trades_count >= self.max_trades_per_day:
            return False
        
        # Check if hit daily profit target
        if self.current_daily_pnl >= self.daily_profit_target:
            self.daily_stopped = True
            return False
        
        # Check if hit daily loss limit
        if self.current_daily_pnl <= -self.stop_trading_after_loss:
            self.daily_stopped = True
            return False
        
        return True
    
    def calculate_trend_strength(self, data: pd.DataFrame) -> float:
        """Calculate trend strength (0-1)"""
        if len(data) < 50:
            return 0.0
        
        score = 0.0
        
        # EMA alignment
        if 'ema_20' in data.columns and 'ema_50' in data.columns:
            ema_20 = data['ema_20'].iloc[-1]
            ema_50 = data['ema_50'].iloc[-1]
            price = data['close'].iloc[-1]
            
            # Uptrend: price > EMA20 > EMA50
            if price > ema_20 > ema_50:
                score += 0.3
            # Downtrend: price < EMA20 < EMA50
            elif price < ema_20 < ema_50:
                score += 0.3
        
        # ADX strength
        if 'adx' in data.columns:
            adx = data['adx'].iloc[-1]
            if adx > 25:
                score += 0.3
        
        # MACD alignment
        if 'macd' in data.columns and 'macd_signal' in data.columns:
            macd = data['macd'].iloc[-1]
            macd_signal = data['macd_signal'].iloc[-1]
            
            if abs(macd - macd_signal) > 0:
                score += 0.2
        
        return min(score, 1.0)
    
    def calculate_momentum_strength(self, data: pd.DataFrame) -> float:
        """Calculate momentum strength (0-1)"""
        if len(data) < 30:
            return 0.0
        
        score = 0.0
        
        # RSI in trend zone
        if 'rsi' in data.columns:
            rsi = data['rsi'].iloc[-1]
            # For uptrend: RSI 40-60 (not overbought)
            if 40 <= rsi <= 60:
                score += 0.4
            # For downtrend: RSI 40-60
            elif 40 <= rsi <= 60:
                score += 0.4
        
        # Stochastic
        if 'stoch_k' in data.columns and 'stoch_d' in data.columns:
            k = data['stoch_k'].iloc[-1]
            d = data['stoch_d'].iloc[-1]
            
            # Bullish: K > D and not overbought
            if k > d and k < 80:
                score += 0.3
            # Bearish: K < D and not oversold
            elif k < d and k > 20:
                score += 0.3
        
        # Price momentum
        if len(data) >= 20:
            price_change = (data['close'].iloc[-1] - data['close'].iloc[-20]) / data['close'].iloc[-20]
            if abs(price_change) > 0.001:  # At least 0.1% move
                score += 0.3
        
        return min(score, 1.0)
    
    def check_support_resistance(self, data: pd.DataFrame) -> float:
        """Check proximity to support/resistance levels (0-1)"""
        if len(data) < 50:
            return 0.0
        
        current_price = data['close'].iloc[-1]
        recent_data = data.tail(50)
        
        # Find recent highs and lows
        resistance_levels = recent_data.nlargest(3, 'high')['high'].values
        support_levels = recent_data.nsmallest(3, 'low')['low'].values
        
        # Check distance to nearest level
        all_levels = np.concatenate([resistance_levels, support_levels])
        distances = [abs(current_price - level) / current_price for level in all_levels]
        min_distance = min(distances)
        
        # Closer to S/R = higher score (good for bounces/breaks)
        if min_distance < 0.002:  # Within 0.2%
            return 0.8
        elif min_distance < 0.005:  # Within 0.5%
            return 0.5
        else:
            return 0.2
    
    def calculate_signal_confidence(self, data: pd.DataFrame) -> Tuple[float, int, List[str]]:
        """Calculate overall signal confidence and confluence count"""
        trend_strength = self.calculate_trend_strength(data)
        momentum_strength = self.calculate_momentum_strength(data)
        sr_proximity = self.check_support_resistance(data)
        
        # List of confirmations
        confirmations = []
        
        if trend_strength >= 0.6:
            confirmations.append('Strong Trend')
        if momentum_strength >= 0.6:
            confirmations.append('Good Momentum')
        if sr_proximity >= 0.5:
            confirmations.append('Near S/R Level')
        
        # Weighted confidence score
        confidence = (
            trend_strength * 0.4 +
            momentum_strength * 0.4 +
            sr_proximity * 0.2
        )
        
        confluence_count = len(confirmations)
        
        return confidence, confluence_count, confirmations
    
    def generate_signals(self, data: pd.DataFrame, pair: str) -> List[Dict]:
        """Generate conservative prop firm challenge signals"""
        if len(data) < 50:
            return []
        
        current_date = data.index[-1].date()
        
        # Check daily limits
        if not self.check_daily_limits(current_date):
            return []
        
        signals = []
        current_price = data['close'].iloc[-1]
        
        # Calculate signal confidence
        confidence, confluence, confirmations = self.calculate_signal_confidence(data)
        
        # Strict entry requirements
        if confidence < self.signal_strength_min:
            return []
        
        if confluence < self.confluence_required:
            return []
        
        # Determine direction
        signal_direction = None
        
        if 'ema_20' in data.columns and 'ema_50' in data.columns:
            ema_20 = data['ema_20'].iloc[-1]
            ema_50 = data['ema_50'].iloc[-1]
            
            # Buy signal: Uptrend confirmed
            if current_price > ema_20 > ema_50:
                if 'rsi' in data.columns and data['rsi'].iloc[-1] < 70:
                    signal_direction = 'BUY'
            
            # Sell signal: Downtrend confirmed
            elif current_price < ema_20 < ema_50:
                if 'rsi' in data.columns and data['rsi'].iloc[-1] > 30:
                    signal_direction = 'SELL'
        
        if not signal_direction:
            return []
        
        # Calculate entry, TP, SL with conservative R:R
        atr = data['atr'].iloc[-1] if 'atr' in data.columns else current_price * 0.002
        
        if signal_direction == 'BUY':
            sl_price = current_price - (atr * 1.5)
            risk = current_price - sl_price
            tp_price = current_price + (risk * self.tp_rr_ratio)
        else:  # SELL
            sl_price = current_price + (atr * 1.5)
            risk = sl_price - current_price
            tp_price = current_price - (risk * self.tp_rr_ratio)
        
        rr_ratio = abs(tp_price - current_price) / abs(current_price - sl_price)
        
        # Create signal
        signals.append({
            'pair': pair,
            'signal': signal_direction,
            'entry_price': current_price,
            'tp_price': tp_price,
            'sl_price': sl_price,
            'confidence': confidence,
            'reason': f'Prop Firm Setup: {", ".join(confirmations)}',
            'rr_ratio': rr_ratio,
            'confluence_count': confluence,
            'confirmations': confirmations,
            'strategy_type': 'prop_firm_challenge',
            'risk_pct': self.risk_per_trade,
            'partial_tp_enabled': self.partial_tp_enabled,
            'trailing_stop_trigger': self.trailing_stop_trigger,
            'breakeven_trigger': self.breakeven_trigger
        })
        
        self.daily_trades_count += 1
        
        return signals
    
    def update_daily_pnl(self, pnl: float, current_date: date):
        """Update daily P&L tracking"""
        self.current_daily_pnl += pnl
        
        if current_date in self.daily_stats:
            self.daily_stats[current_date]['pnl'] = self.current_daily_pnl
        
        # Check if need to stop trading for the day
        if self.current_daily_pnl >= self.daily_profit_target:
            self.daily_stopped = True
            logger.info(f"Daily profit target reached: {self.current_daily_pnl:.2%}")
        
        if self.current_daily_pnl <= -self.stop_trading_after_loss:
            self.daily_stopped = True
            logger.warning(f"Daily loss limit hit: {self.current_daily_pnl:.2%}")
    
    def get_challenge_stats(self) -> Dict:
        """Get prop firm challenge statistics"""
        total_days = len(self.daily_stats)
        winning_days = sum(1 for stats in self.daily_stats.values() if stats['pnl'] > 0)
        
        return {
            'total_profit': self.total_profit,
            'trading_days': total_days,
            'winning_days': winning_days,
            'winning_days_pct': winning_days / total_days if total_days > 0 else 0,
            'avg_daily_pnl': sum(s['pnl'] for s in self.daily_stats.values()) / total_days if total_days > 0 else 0,
            'challenge_progress': self.total_profit / self.profit_target if self.profit_target > 0 else 0,
            'max_drawdown_hit': self.total_profit < -self.max_total_loss,
            'profit_target_hit': self.total_profit >= self.profit_target
        }




