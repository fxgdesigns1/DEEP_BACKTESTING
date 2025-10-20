#!/usr/bin/env python3
"""
SESSION HIGHS/LOWS STRATEGY
Targets session extremes with smart reversal entries
Hunts for session high/low points and trades reversals
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

class SessionHighsLowsStrategy:
    """
    Session-based strategy targeting highs and lows
    Trades reversals from session extremes
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Session definitions (UTC times)
        self.sessions = {
            'tokyo': {'start': 0, 'end': 9},
            'london': {'start': 8, 'end': 17},
            'new_york': {'start': 13, 'end': 22},
            'overlap': {'start': 13, 'end': 17}  # London-NY overlap
        }
        
        # Strategy parameters
        self.lookback_periods = self.config.get('lookback_periods', 30)
        self.distance_from_extreme = self.config.get('distance_from_extreme', 0.001)  # 0.1%
        self.tp_pct = self.config.get('tp_pct', 0.003)  # 30 pips
        self.sl_pct = self.config.get('sl_pct', 0.0015)  # 15 pips
        self.min_rr_ratio = self.config.get('min_rr_ratio', 2.0)
        self.max_trades_per_session = self.config.get('max_trades_per_session', 3)
        
        # Tracking
        self.session_trades = {}
        self.session_highs = {}
        self.session_lows = {}
        
    def get_current_session(self, dt: datetime) -> Optional[str]:
        """Determine which trading session we're in"""
        hour = dt.hour
        
        # Check each session
        if self.sessions['overlap']['start'] <= hour < self.sessions['overlap']['end']:
            return 'overlap'
        elif self.sessions['london']['start'] <= hour < self.sessions['london']['end']:
            return 'london'
        elif self.sessions['new_york']['start'] <= hour < self.sessions['new_york']['end']:
            return 'new_york'
        elif self.sessions['tokyo']['start'] <= hour < self.sessions['tokyo']['end']:
            return 'tokyo'
        
        return None
    
    def identify_session_extremes(self, data: pd.DataFrame, session: str) -> Tuple[float, float]:
        """Identify session high and low"""
        # Get data for current session
        session_data = data.tail(self.lookback_periods)
        
        if len(session_data) < 5:
            return None, None
            
        session_high = session_data['high'].max()
        session_low = session_data['low'].min()
        
        return session_high, session_low
    
    def check_reversal_signals(self, data: pd.DataFrame, signal_type: str) -> float:
        """Check for reversal confirmation signals"""
        if len(data) < 20:
            return 0.0
            
        latest = data.iloc[-1]
        
        # RSI reversal
        rsi_signal = 0.0
        if 'rsi' in data.columns:
            rsi = latest['rsi']
            if signal_type == 'SELL' and rsi > 70:
                rsi_signal = 0.3
            elif signal_type == 'BUY' and rsi < 30:
                rsi_signal = 0.3
                
        # MACD reversal
        macd_signal = 0.0
        if 'macd' in data.columns and 'macd_signal' in data.columns:
            macd = latest['macd']
            macd_sig = latest['macd_signal']
            
            if signal_type == 'SELL' and macd < macd_sig:
                macd_signal = 0.3
            elif signal_type == 'BUY' and macd > macd_sig:
                macd_signal = 0.3
                
        # Price action (rejection wicks)
        pa_signal = 0.0
        candle_range = latest['high'] - latest['low']
        
        if signal_type == 'SELL':
            upper_wick = latest['high'] - max(latest['open'], latest['close'])
            if candle_range > 0 and upper_wick / candle_range > 0.5:
                pa_signal = 0.4
                
        elif signal_type == 'BUY':
            lower_wick = min(latest['open'], latest['close']) - latest['low']
            if candle_range > 0 and lower_wick / candle_range > 0.5:
                pa_signal = 0.4
        
        total_signal = rsi_signal + macd_signal + pa_signal
        return min(total_signal, 1.0)
    
    def generate_signals(self, data: pd.DataFrame, pair: str) -> List[Dict]:
        """Generate trading signals based on session highs/lows"""
        if len(data) < self.lookback_periods:
            return []
            
        signals = []
        current_time = data.index[-1]
        current_price = data.iloc[-1]['close']
        
        # Determine current session
        session = self.get_current_session(current_time)
        if not session:
            return []
            
        # Check if we've hit max trades for this session
        session_key = f"{session}_{current_time.date()}"
        if self.session_trades.get(session_key, 0) >= self.max_trades_per_session:
            return []
            
        # Identify session extremes
        session_high, session_low = self.identify_session_extremes(data, session)
        
        if session_high is None or session_low is None:
            return []
            
        # Store extremes
        self.session_highs[session_key] = session_high
        self.session_lows[session_key] = session_low
        
        # Check for reversal from session high (SELL signal)
        distance_from_high = abs(current_price - session_high) / session_high
        if distance_from_high <= self.distance_from_extreme:
            reversal_strength = self.check_reversal_signals(data, 'SELL')
            
            if reversal_strength > 0.5:
                tp_price = current_price - (current_price * self.tp_pct)
                sl_price = current_price + (current_price * self.sl_pct)
                
                rr_ratio = abs(current_price - tp_price) / abs(sl_price - current_price)
                
                if rr_ratio >= self.min_rr_ratio:
                    signals.append({
                        'pair': pair,
                        'signal': 'SELL',
                        'entry_price': current_price,
                        'tp_price': tp_price,
                        'sl_price': sl_price,
                        'confidence': 0.6 + (reversal_strength * 0.3),
                        'reason': f'Session high reversal ({session})',
                        'rr_ratio': rr_ratio,
                        'session': session,
                        'session_high': session_high,
                        'session_low': session_low
                    })
                    
                    # Increment session trade count
                    self.session_trades[session_key] = self.session_trades.get(session_key, 0) + 1
        
        # Check for reversal from session low (BUY signal)
        distance_from_low = abs(current_price - session_low) / session_low
        if distance_from_low <= self.distance_from_extreme:
            reversal_strength = self.check_reversal_signals(data, 'BUY')
            
            if reversal_strength > 0.5:
                tp_price = current_price + (current_price * self.tp_pct)
                sl_price = current_price - (current_price * self.sl_pct)
                
                rr_ratio = abs(tp_price - current_price) / abs(current_price - sl_price)
                
                if rr_ratio >= self.min_rr_ratio:
                    signals.append({
                        'pair': pair,
                        'signal': 'BUY',
                        'entry_price': current_price,
                        'tp_price': tp_price,
                        'sl_price': sl_price,
                        'confidence': 0.6 + (reversal_strength * 0.3),
                        'reason': f'Session low reversal ({session})',
                        'rr_ratio': rr_ratio,
                        'session': session,
                        'session_high': session_high,
                        'session_low': session_low
                    })
                    
                    # Increment session trade count
                    self.session_trades[session_key] = self.session_trades.get(session_key, 0) + 1
        
        return signals
    
    def calculate_position_size(self, account_balance: float, risk_pct: float, 
                               entry_price: float, sl_price: float) -> float:
        """Calculate position size based on risk"""
        risk_amount = account_balance * risk_pct
        price_risk = abs(entry_price - sl_price)
        
        if price_risk == 0:
            return 0
            
        position_size = risk_amount / price_risk
        return position_size
    
    def reset_session_tracking(self):
        """Reset session tracking (call at end of day)"""
        self.session_trades = {}
        self.session_highs = {}
        self.session_lows = {}



