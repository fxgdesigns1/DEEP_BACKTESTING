#!/usr/bin/env python3
"""
QUICK SCALPER STRATEGY
Fast in, fast out scalping for quick profits
High frequency, tight stops, quick targets
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class QuickScalperStrategy:
    """
    High-frequency scalping strategy
    Targets quick 5-15 pip moves with tight risk management
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Scalping parameters
        self.quick_tp_pips = self.config.get('quick_tp_pips', 10)
        self.quick_sl_pips = self.config.get('quick_sl_pips', 5)
        self.time_exit_minutes = self.config.get('time_exit_minutes', 15)
        self.breakeven_trigger_pips = self.config.get('breakeven_trigger_pips', 5)
        
        # Entry parameters
        self.momentum_threshold = self.config.get('momentum_threshold', 0.0005)
        self.volume_multiplier = self.config.get('volume_multiplier', 1.5)
        self.bb_period = self.config.get('bb_period', 20)
        self.bb_std = self.config.get('bb_std', 2.0)
        
        # Risk management
        self.max_trades_per_day = self.config.get('max_trades_per_day', 50)
        self.max_consecutive_losses = self.config.get('max_consecutive_losses', 3)
        self.position_size_pct = self.config.get('position_size_pct', 0.01)
        
        # Tracking
        self.daily_trades = 0
        self.consecutive_losses = 0
        self.entry_times = {}
        
    def calculate_momentum(self, data: pd.DataFrame, period: int = 10) -> float:
        """Calculate price momentum"""
        if len(data) < period:
            return 0.0
            
        price_change = data['close'].iloc[-1] - data['close'].iloc[-period]
        momentum = price_change / data['close'].iloc[-period]
        
        return momentum
    
    def check_volume_spike(self, data: pd.DataFrame, period: int = 20) -> bool:
        """Check for volume spike"""
        if 'volume' not in data.columns or len(data) < period:
            return True  # Assume OK if no volume data
            
        avg_volume = data['volume'].tail(period).mean()
        current_volume = data['volume'].iloc[-1]
        
        if avg_volume == 0:
            return True
            
        return current_volume >= (avg_volume * self.volume_multiplier)
    
    def calculate_bollinger_bands(self, data: pd.DataFrame) -> Tuple[float, float, float]:
        """Calculate Bollinger Bands"""
        if len(data) < self.bb_period:
            return None, None, None
            
        sma = data['close'].tail(self.bb_period).mean()
        std = data['close'].tail(self.bb_period).std()
        
        upper = sma + (self.bb_std * std)
        lower = sma - (self.bb_std * std)
        
        return upper, sma, lower
    
    def check_momentum_burst(self, data: pd.DataFrame) -> Optional[Dict]:
        """Check for momentum burst signal"""
        if len(data) < 20:
            return None
            
        momentum = self.calculate_momentum(data, period=10)
        volume_ok = self.check_volume_spike(data)
        
        current_price = data['close'].iloc[-1]
        
        # Bullish momentum burst
        if momentum > self.momentum_threshold and volume_ok:
            return {
                'signal': 'BUY',
                'entry_price': current_price,
                'confidence': min(0.7 + abs(momentum) * 100, 0.95),
                'reason': 'Momentum burst (bullish)'
            }
            
        # Bearish momentum burst
        elif momentum < -self.momentum_threshold and volume_ok:
            return {
                'signal': 'SELL',
                'entry_price': current_price,
                'confidence': min(0.7 + abs(momentum) * 100, 0.95),
                'reason': 'Momentum burst (bearish)'
            }
            
        return None
    
    def check_mean_reversion(self, data: pd.DataFrame) -> Optional[Dict]:
        """Check for mean reversion opportunity"""
        if len(data) < self.bb_period:
            return None
            
        upper, middle, lower = self.calculate_bollinger_bands(data)
        
        if upper is None:
            return None
            
        current_price = data['close'].iloc[-1]
        
        # RSI confirmation
        rsi_oversold = False
        rsi_overbought = False
        
        if 'rsi' in data.columns:
            rsi = data['rsi'].iloc[-1]
            rsi_oversold = rsi < 30
            rsi_overbought = rsi > 70
        
        # Price at lower band - potential BUY
        if current_price <= lower and rsi_oversold:
            return {
                'signal': 'BUY',
                'entry_price': current_price,
                'confidence': 0.75,
                'reason': 'Mean reversion (oversold)'
            }
            
        # Price at upper band - potential SELL
        elif current_price >= upper and rsi_overbought:
            return {
                'signal': 'SELL',
                'entry_price': current_price,
                'confidence': 0.75,
                'reason': 'Mean reversion (overbought)'
            }
            
        return None
    
    def check_micro_breakout(self, data: pd.DataFrame, consolidation_bars: int = 15) -> Optional[Dict]:
        """Check for micro breakout from consolidation"""
        if len(data) < consolidation_bars + 5:
            return None
            
        # Check for consolidation (low volatility)
        recent_data = data.tail(consolidation_bars)
        price_range = recent_data['high'].max() - recent_data['low'].min()
        avg_price = recent_data['close'].mean()
        
        if avg_price == 0:
            return None
            
        consolidation_pct = price_range / avg_price
        
        # If consolidation is tight (< 0.5%)
        if consolidation_pct < 0.005:
            current_price = data['close'].iloc[-1]
            recent_high = recent_data['high'].max()
            recent_low = recent_data['low'].min()
            
            # Breakout above
            if current_price > recent_high:
                return {
                    'signal': 'BUY',
                    'entry_price': current_price,
                    'confidence': 0.70,
                    'reason': 'Micro breakout (up)'
                }
                
            # Breakout below
            elif current_price < recent_low:
                return {
                    'signal': 'SELL',
                    'entry_price': current_price,
                    'confidence': 0.70,
                    'reason': 'Micro breakout (down)'
                }
                
        return None
    
    def generate_signals(self, data: pd.DataFrame, pair: str) -> List[Dict]:
        """Generate scalping signals"""
        if len(data) < 30:
            return []
            
        # Check risk management limits
        if self.daily_trades >= self.max_trades_per_day:
            return []
            
        if self.consecutive_losses >= self.max_consecutive_losses:
            return []
            
        signals = []
        current_time = data.index[-1]
        
        # Try different signal types
        signal_checks = [
            self.check_momentum_burst(data),
            self.check_mean_reversion(data),
            self.check_micro_breakout(data)
        ]
        
        for signal_data in signal_checks:
            if signal_data:
                entry_price = signal_data['entry_price']
                
                # Calculate quick TP/SL in price
                pip_value = 0.0001 if 'JPY' not in pair else 0.01
                
                if signal_data['signal'] == 'BUY':
                    tp_price = entry_price + (self.quick_tp_pips * pip_value)
                    sl_price = entry_price - (self.quick_sl_pips * pip_value)
                else:
                    tp_price = entry_price - (self.quick_tp_pips * pip_value)
                    sl_price = entry_price + (self.quick_sl_pips * pip_value)
                
                rr_ratio = self.quick_tp_pips / self.quick_sl_pips
                
                signals.append({
                    'pair': pair,
                    'signal': signal_data['signal'],
                    'entry_price': entry_price,
                    'tp_price': tp_price,
                    'sl_price': sl_price,
                    'confidence': signal_data['confidence'],
                    'reason': signal_data['reason'],
                    'rr_ratio': rr_ratio,
                    'entry_time': current_time,
                    'time_exit_minutes': self.time_exit_minutes,
                    'strategy_type': 'quick_scalper'
                })
                
                self.entry_times[pair] = current_time
                self.daily_trades += 1
                
                break  # Only one signal at a time
        
        return signals
    
    def check_time_exit(self, pair: str, current_time: datetime) -> bool:
        """Check if time-based exit should trigger"""
        if pair not in self.entry_times:
            return False
            
        entry_time = self.entry_times[pair]
        time_elapsed = (current_time - entry_time).total_seconds() / 60
        
        return time_elapsed >= self.time_exit_minutes
    
    def reset_daily_tracking(self):
        """Reset daily counters"""
        self.daily_trades = 0
        self.consecutive_losses = 0
        self.entry_times = {}
    
    def update_consecutive_losses(self, trade_result: str):
        """Update consecutive loss counter"""
        if trade_result == 'LOSS':
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0




