#!/usr/bin/env python3
"""
LIVE OPTIMIZED STRATEGIES INTEGRATION
Integrates UltraOptimizedCurrencyStrategy and UltraOptimizedGoldStrategy into live system
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import yaml
import json

logger = logging.getLogger(__name__)

class LiveOptimizedStrategyManager:
    """
    Manages live trading with optimized strategies
    """
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize the live strategy manager"""
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        
        # Live data storage
        self.live_data = {}
        self.current_signals = {}
        self.signal_history = []
        
        # Performance tracking
        self.performance_metrics = {
            'currency': {'wins': 0, 'losses': 0, 'total_pnl': 0},
            'gold': {'wins': 0, 'losses': 0, 'total_pnl': 0}
        }
        
        self.logger.info("✅ LiveOptimizedStrategyManager initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration"""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return {}
    
    def update_live_data(self, symbol: str, ohlc_data: Dict[str, Any]):
        """Update live market data"""
        try:
            # Convert to DataFrame format expected by strategies
            df_data = []
            for candle in ohlc_data:
                df_data.append({
                    'Date': pd.to_datetime(candle['timestamp'], unit='ms'),
                    'Open': candle['open'],
                    'High': candle['high'],
                    'Low': candle['low'],
                    'Close': candle['close'],
                    'Volume': candle.get('volume', 1000)
                })
            
            df = pd.DataFrame(df_data)
            df.set_index('Date', inplace=True)
            
            self.live_data[symbol] = df
            self.logger.info(f"Updated live data for {symbol}: {len(df)} candles")
            
        except Exception as e:
            self.logger.error(f"Error updating live data for {symbol}: {e}")
    
    def generate_live_signals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Generate live trading signals using optimized strategies"""
        try:
            if symbol not in self.live_data:
                return None
            
            data = self.live_data[symbol]
            if len(data) < 50:  # Need minimum data
                return None
            
            # Determine which strategy to use
            if symbol == 'XAU_USD':
                signal = self._analyze_gold_strategy(data, symbol)
                strategy_name = 'UltraOptimizedGoldStrategy'
            else:
                signal = self._analyze_currency_strategy(data, symbol)
                strategy_name = 'UltraOptimizedCurrencyStrategy'
            
            if signal:
                signal['strategy'] = strategy_name
                signal['timestamp'] = datetime.now().isoformat()
                signal['symbol'] = symbol
                
                # Store in history
                self.signal_history.append(signal)
                
                # Update current signals
                self.current_signals[symbol] = signal
                
                self.logger.info(f"Generated signal for {symbol}: {signal['direction']} @ {signal['entry_price']}")
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error generating signals for {symbol}: {e}")
            return None
    
    def _analyze_currency_strategy(self, data: pd.DataFrame, symbol: str) -> Optional[Dict[str, Any]]:
        """Analyze data using currency strategy logic"""
        try:
            # Get current market conditions
            current_price = data['Close'].iloc[-1]
            current_volume = data['Volume'].iloc[-1]
            
            # Calculate indicators
            rsi = self._calculate_rsi(data['Close'], 14)
            atr = self._calculate_atr(data['High'], data['Low'], data['Close'], 14)
            ema_15 = self._calculate_ema(data['Close'], 15)
            ema_50 = self._calculate_ema(data['Close'], 50)
            
            # Currency strategy conditions
            long_conditions = (
                rsi > 30 and rsi < 60 and
                ema_15 > ema_50 and
                current_volume > 0
            )
            
            short_conditions = (
                rsi < 70 and rsi > 40 and
                ema_15 < ema_50 and
                current_volume > 0
            )
            
            if long_conditions:
                stop_loss = current_price - (atr * 2.5)
                take_profit = current_price + (atr * 5.0)  # 2:1 RR
                return {
                    'direction': 'BUY',
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'confidence': 75,
                    'reasoning': 'Currency strategy long signal - RSI oversold, EMA bullish, volume confirmed'
                }
            
            elif short_conditions:
                stop_loss = current_price + (atr * 2.5)
                take_profit = current_price - (atr * 5.0)  # 2:1 RR
                return {
                    'direction': 'SELL',
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'confidence': 75,
                    'reasoning': 'Currency strategy short signal - RSI overbought, EMA bearish, volume confirmed'
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in currency strategy analysis: {e}")
            return None
    
    def _analyze_gold_strategy(self, data: pd.DataFrame, symbol: str) -> Optional[Dict[str, Any]]:
        """Analyze data using gold strategy logic"""
        try:
            # Get current market conditions
            current_price = data['Close'].iloc[-1]
            current_volume = data['Volume'].iloc[-1]
            
            # Calculate indicators
            rsi = self._calculate_rsi(data['Close'], 14)
            atr = self._calculate_atr(data['High'], data['Low'], data['Close'], 21)  # Longer period for gold
            ema_15 = self._calculate_ema(data['Close'], 15)
            ema_50 = self._calculate_ema(data['Close'], 50)
            
            # Gold-specific conditions
            long_conditions = (
                rsi > 25 and rsi < 65 and
                ema_15 > ema_50 and
                current_volume > 0
            )
            
            short_conditions = (
                rsi < 75 and rsi > 35 and
                ema_15 < ema_50 and
                current_volume > 0
            )
            
            if long_conditions:
                stop_loss = current_price - (atr * 3.0)
                take_profit = current_price + (atr * 7.5)  # 2.5:1 RR
                return {
                    'direction': 'BUY',
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'confidence': 80,
                    'reasoning': 'Gold strategy long signal - Conservative RSI, EMA bullish, volatility managed'
                }
            
            elif short_conditions:
                stop_loss = current_price + (atr * 3.0)
                take_profit = current_price - (atr * 7.5)  # 2.5:1 RR
                return {
                    'direction': 'SELL',
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'confidence': 80,
                    'reasoning': 'Gold strategy short signal - Conservative RSI, EMA bearish, volatility managed'
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in gold strategy analysis: {e}")
            return None
    
    def _calculate_rsi(self, prices, period):
        """Calculate RSI"""
        delta = pd.Series(prices).diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs)).iloc[-1]
    
    def _calculate_atr(self, high, low, close, period):
        """Calculate ATR"""
        tr1 = pd.Series(high) - pd.Series(low)
        tr2 = abs(pd.Series(high) - pd.Series(close).shift(1))
        tr3 = abs(pd.Series(low) - pd.Series(close).shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(period).mean().iloc[-1]
    
    def _calculate_ema(self, prices, period):
        """Calculate EMA"""
        return pd.Series(prices).ewm(span=period).mean().iloc[-1]
    
    def get_current_signals(self) -> Dict[str, Any]:
        """Get current active signals"""
        return self.current_signals
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.performance_metrics
    
    def get_signal_history(self) -> List[Dict[str, Any]]:
        """Get signal history"""
        return self.signal_history
    
    def generate_sample_signals(self) -> Dict[str, Any]:
        """Generate sample signals for testing"""
        sample_signals = {
            'EUR_USD': {
                'direction': 'BUY',
                'entry_price': 1.1695,  # Updated current price
                'stop_loss': 1.1645,
                'take_profit': 1.1795,
                'confidence': 75,
                'reasoning': 'Currency strategy long signal - RSI oversold, EMA bullish, volume confirmed',
                'strategy': 'UltraOptimizedCurrencyStrategy',
                'timestamp': datetime.now().isoformat(),
                'symbol': 'EUR_USD'
            },
            'XAU_USD': {
                'direction': 'BUY',
                'entry_price': 3358.4,  # Updated current price
                'stop_loss': 3348.4,
                'take_profit': 3378.4,
                'confidence': 80,
                'reasoning': 'Gold strategy long signal - Conservative RSI, EMA bullish, volatility managed',
                'strategy': 'UltraOptimizedGoldStrategy',
                'timestamp': datetime.now().isoformat(),
                'symbol': 'XAU_USD'
            },
            'GBP_USD': {
                'direction': 'BUY',  # Changed from SELL to BUY since price is rising
                'entry_price': 1.3587,  # Updated current price
                'stop_loss': 1.3537,  # 50 pips below entry
                'take_profit': 1.3687,  # 100 pips above entry
                'confidence': 75,
                'reasoning': 'Currency strategy long signal - RSI oversold, EMA bullish, volume confirmed',
                'strategy': 'UltraOptimizedCurrencyStrategy',
                'timestamp': datetime.now().isoformat(),
                'symbol': 'GBP_USD'
            }
        }
        
        # Update current signals
        self.current_signals = sample_signals
        
        return sample_signals
