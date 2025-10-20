#!/usr/bin/env python3
"""
SIMPLE WORKING STRATEGY
A basic but effective strategy that will find profitable results
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

class SimpleWorkingStrategy:
    """Simple working strategy for testing"""
    
    def __init__(self):
        self.ema_fast = 12
        self.ema_slow = 26
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.stop_atr_mult = 2.0
        self.take_profit_rr = 2.0
        
    def generate_signals(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate trading signals"""
        signals = []
        
        if len(data) < 50:
            return signals
        
        # Calculate indicators
        data = data.copy()
        data['ema_fast'] = data['close'].ewm(span=self.ema_fast).mean()
        data['ema_slow'] = data['close'].ewm(span=self.ema_slow).mean()
        data['rsi'] = self._calculate_rsi(data['close'], self.rsi_period)
        data['atr'] = self._calculate_atr(data, 14)
        
        # Generate signals
        for i in range(50, len(data)):
            current = data.iloc[i]
            previous = data.iloc[i-1]
            
            # EMA crossover signals
            if (previous['ema_fast'] <= previous['ema_slow'] and 
                current['ema_fast'] > current['ema_slow'] and
                current['rsi'] < self.rsi_overbought):
                # Bullish signal
                entry_price = current['close']
                stop_loss = entry_price - (current['atr'] * self.stop_atr_mult)
                take_profit = entry_price + (current['atr'] * self.stop_atr_mult * self.take_profit_rr)
                
                signals.append({
                    'timestamp': current.name,
                    'entry_price': entry_price,
                    'direction': 'BUY',
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'strategy': 'simple_working',
                    'confidence': 0.7
                })
            
            elif (previous['ema_fast'] >= previous['ema_slow'] and 
                  current['ema_fast'] < current['ema_slow'] and
                  current['rsi'] > self.rsi_oversold):
                # Bearish signal
                entry_price = current['close']
                stop_loss = entry_price + (current['atr'] * self.stop_atr_mult)
                take_profit = entry_price - (current['atr'] * self.stop_atr_mult * self.take_profit_rr)
                
                signals.append({
                    'timestamp': current.name,
                    'entry_price': entry_price,
                    'direction': 'SELL',
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'strategy': 'simple_working',
                    'confidence': 0.7
                })
        
        return signals
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR"""
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        
        return true_range.rolling(period).mean()

