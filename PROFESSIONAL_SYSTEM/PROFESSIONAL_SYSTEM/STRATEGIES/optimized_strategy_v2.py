#!/usr/bin/env python3
"""
OPTIMIZED STRATEGY V2
Improved strategy with realistic parameters, better risk management, and enhanced features
"""

import pandas as pd
import numpy as np
import logging
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import yaml

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OptimizedStrategyV2:
    """
    Optimized Strategy V2 - Realistic parameters with enhanced risk management
    """
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize Optimized Strategy V2"""
        self.config = self._load_config(config_path)
        self.logger = logger
        
        # Realistic parameters (reduced from ultra-strict)
        self.min_rr_ratio = 2.0  # Minimum 1:2 risk-reward (was 3.0)
        self.min_confidence = 70  # Minimum 70% confidence (was 85%)
        self.min_volume_multiplier = 1.5  # Volume must be 1.5x average (was 2.0)
        self.min_atr_multiplier = 1.2  # ATR must be 1.2x average (was 1.5)
        self.max_daily_trades = 3  # Maximum 3 trades per day per pair (was 2)
        self.min_pips_threshold = 10  # Minimum 10 pips potential (was 15)
        
        # Market regime requirements (relaxed)
        self.min_adx_trend = 20  # Minimum ADX for trend confirmation (was 25)
        self.max_correlation_threshold = 0.8  # Maximum correlation with other pairs (was 0.7)
        
        # Session requirements (more flexible)
        self.required_sessions = ['London', 'New York', 'Tokyo']  # All major sessions
        
        # Enhanced features
        self.use_market_regime_detection = True
        self.use_adaptive_parameters = True
        self.use_news_filtering = False  # Disabled for now
        self.use_sentiment_analysis = False  # Disabled for now
        
        # Performance tracking
        self.daily_trades = {}
        self.trade_history = []
        self.market_regimes = {}
        self.performance_metrics = {}
        
        self.logger.info("🎯 Optimized Strategy V2 initialized with realistic parameters")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return {}
    
    def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators"""
        try:
            # Basic indicators
            data['SMA_20'] = data['close'].rolling(window=20).mean()
            data['SMA_50'] = data['close'].rolling(window=50).mean()
            data['EMA_12'] = data['close'].ewm(span=12).mean()
            data['EMA_26'] = data['close'].ewm(span=26).mean()
            data['EMA_50'] = data['close'].ewm(span=50).mean()
            
            # RSI
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
            # MACD
            data['MACD'] = data['EMA_12'] - data['EMA_26']
            data['MACD_Signal'] = data['MACD'].ewm(span=9).mean()
            data['MACD_Histogram'] = data['MACD'] - data['MACD_Signal']
            
            # Bollinger Bands
            data['BB_Middle'] = data['close'].rolling(window=20).mean()
            bb_std = data['close'].rolling(window=20).std()
            data['BB_Upper'] = data['BB_Middle'] + (bb_std * 2)
            data['BB_Lower'] = data['BB_Middle'] - (bb_std * 2)
            data['BB_Width'] = (data['BB_Upper'] - data['BB_Lower']) / data['BB_Middle']
            
            # ATR
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            data['ATR'] = true_range.rolling(window=14).mean()
            
            # ADX for trend strength
            data['ADX'] = self._calculate_adx(data)
            
            # Volume analysis
            data['Volume_SMA'] = data['volume'].rolling(window=20).mean()
            data['Volume_Ratio'] = data['volume'] / data['Volume_SMA']
            
            # Price action patterns
            data['Doji'] = self._detect_doji(data)
            data['Hammer'] = self._detect_hammer(data)
            data['Engulfing'] = self._detect_engulfing(data)
            
            # Market regime detection
            if self.use_market_regime_detection:
                data['Market_Regime'] = self._detect_market_regime(data)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return data
    
    def _calculate_adx(self, data: pd.DataFrame) -> pd.Series:
        """Calculate ADX for trend strength"""
        try:
            # Calculate +DM and -DM
            high_diff = data['high'].diff()
            low_diff = data['low'].diff()
            
            plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
            minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
            
            # Calculate TR, +DI, -DI
            tr = self._calculate_true_range(data)
            plus_di = 100 * pd.Series(plus_dm).rolling(14).mean() / tr.rolling(14).mean()
            minus_di = 100 * pd.Series(minus_dm).rolling(14).mean() / tr.rolling(14).mean()
            
            # Calculate ADX
            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = pd.Series(dx).rolling(14).mean()
            
            return adx
            
        except Exception as e:
            self.logger.error(f"Error calculating ADX: {e}")
            return pd.Series([0] * len(data))
    
    def _calculate_true_range(self, data: pd.DataFrame) -> pd.Series:
        """Calculate True Range"""
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        return np.max(ranges, axis=1)
    
    def _detect_doji(self, data: pd.DataFrame) -> pd.Series:
        """Detect Doji candlestick patterns"""
        body_size = np.abs(data['close'] - data['open'])
        total_range = data['high'] - data['low']
        doji_threshold = 0.1  # Body is less than 10% of total range
        return (body_size / total_range) < doji_threshold
    
    def _detect_hammer(self, data: pd.DataFrame) -> pd.Series:
        """Detect Hammer candlestick patterns"""
        body_size = np.abs(data['close'] - data['open'])
        lower_shadow = np.minimum(data['open'], data['close']) - data['low']
        upper_shadow = data['high'] - np.maximum(data['open'], data['close'])
        
        # Hammer: small body, long lower shadow, small upper shadow
        return (body_size < lower_shadow * 0.3) & (upper_shadow < body_size * 0.3)
    
    def _detect_engulfing(self, data: pd.DataFrame) -> pd.Series:
        """Detect Engulfing candlestick patterns"""
        bullish_engulfing = (
            (data['close'] > data['open']) &  # Current candle is bullish
            (data['close'].shift(1) < data['open'].shift(1)) &  # Previous candle is bearish
            (data['open'] < data['close'].shift(1)) &  # Current open below previous close
            (data['close'] > data['open'].shift(1))  # Current close above previous open
        )
        
        bearish_engulfing = (
            (data['close'] < data['open']) &  # Current candle is bearish
            (data['close'].shift(1) > data['open'].shift(1)) &  # Previous candle is bullish
            (data['open'] > data['close'].shift(1)) &  # Current open above previous close
            (data['close'] < data['open'].shift(1))  # Current close below previous open
        )
        
        return bullish_engulfing | bearish_engulfing
    
    def _detect_market_regime(self, data: pd.DataFrame) -> pd.Series:
        """Detect market regime: trending, ranging, or volatile"""
        try:
            # Calculate regime based on ADX and volatility
            adx = data['ADX']
            volatility = data['ATR'] / data['close']
            
            regime = pd.Series(['ranging'] * len(data), index=data.index)
            
            # Trending regime
            regime[(adx > 25) & (volatility > volatility.rolling(20).mean())] = 'trending'
            
            # Volatile regime
            regime[volatility > volatility.rolling(20).mean() * 1.5] = 'volatile'
            
            return regime
            
        except Exception as e:
            self.logger.error(f"Error detecting market regime: {e}")
            return pd.Series(['ranging'] * len(data), index=data.index)
    
    def check_optimized_conditions(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Check optimized conditions for trade qualification"""
        try:
            if len(data) < 50:
                return {'qualified': False, 'reason': 'Insufficient data'}
            
            current = data.iloc[-1]
            previous = data.iloc[-2]
            
            # 1. Market Regime Check (relaxed)
            if current['ADX'] < self.min_adx_trend:
                return {'qualified': False, 'reason': f'Weak trend (ADX: {current["ADX"]:.1f})'}
            
            # 2. Volume Check (relaxed)
            if current['Volume_Ratio'] < self.min_volume_multiplier:
                return {'qualified': False, 'reason': f'Low volume (Ratio: {current["Volume_Ratio"]:.1f})'}
            
            # 3. ATR Check (relaxed)
            avg_atr = data['ATR'].rolling(20).mean().iloc[-1]
            if current['ATR'] < avg_atr * self.min_atr_multiplier:
                return {'qualified': False, 'reason': f'Low volatility (ATR: {current["ATR"]:.5f})'}
            
            # 4. Daily Trade Limit Check (increased)
            today = datetime.now().strftime('%Y-%m-%d')
            if symbol not in self.daily_trades:
                self.daily_trades[symbol] = {}
            if today not in self.daily_trades[symbol]:
                self.daily_trades[symbol][today] = 0
            
            if self.daily_trades[symbol][today] >= self.max_daily_trades:
                return {'qualified': False, 'reason': 'Daily trade limit reached'}
            
            # 5. Session Check (more flexible)
            current_hour = datetime.now().hour
            if not self._is_major_session(current_hour):
                return {'qualified': False, 'reason': 'Not during major session'}
            
            # 6. Price Action Check (relaxed)
            if not self._check_price_action_quality(data):
                return {'qualified': False, 'reason': 'Poor price action quality'}
            
            # 7. Technical Alignment Check (relaxed)
            alignment_score = self._calculate_technical_alignment(data)
            if alignment_score < self.min_confidence:
                return {'qualified': False, 'reason': f'Low technical alignment ({alignment_score:.1f}%)'}
            
            # 8. Risk-Reward Check (relaxed)
            rr_ratio = self._calculate_potential_rr(data)
            if rr_ratio < self.min_rr_ratio:
                return {'qualified': False, 'reason': f'Insufficient RR ratio ({rr_ratio:.1f})'}
            
            # 9. Minimum Pips Check (relaxed)
            potential_pips = self._calculate_potential_pips(data)
            if potential_pips < self.min_pips_threshold:
                return {'qualified': False, 'reason': f'Insufficient potential pips ({potential_pips:.1f})'}
            
            return {
                'qualified': True,
                'confidence': alignment_score,
                'rr_ratio': rr_ratio,
                'potential_pips': potential_pips,
                'volume_ratio': current['Volume_Ratio'],
                'atr_ratio': current['ATR'] / avg_atr,
                'adx': current['ADX'],
                'market_regime': current.get('Market_Regime', 'unknown')
            }
            
        except Exception as e:
            self.logger.error(f"Error checking optimized conditions: {e}")
            return {'qualified': False, 'reason': f'Error: {str(e)}'}
    
    def _is_major_session(self, hour: int) -> bool:
        """Check if current hour is during major trading session (more flexible)"""
        # London: 7-16 UTC, New York: 13-22 UTC, Tokyo: 0-9 UTC
        london_session = 7 <= hour <= 16
        ny_session = 13 <= hour <= 22
        tokyo_session = 0 <= hour <= 9
        return london_session or ny_session or tokyo_session
    
    def _check_price_action_quality(self, data: pd.DataFrame) -> bool:
        """Check price action quality (relaxed)"""
        try:
            current = data.iloc[-1]
            
            # Check for reasonable momentum (relaxed from 60% to 40%)
            price_change = abs(current['close'] - current['open'])
            total_range = current['high'] - current['low']
            
            if price_change / total_range < 0.4:  # Body should be at least 40% of range
                return False
            
            # Check for reasonable wicks (relaxed)
            upper_wick = current['high'] - max(current['open'], current['close'])
            lower_wick = min(current['open'], current['close']) - current['low']
            
            if upper_wick > price_change * 0.8 or lower_wick > price_change * 0.8:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking price action quality: {e}")
            return False
    
    def _calculate_technical_alignment(self, data: pd.DataFrame) -> float:
        """Calculate technical alignment score (0-100) - relaxed scoring"""
        try:
            current = data.iloc[-1]
            score = 0
            total_checks = 0
            
            # Trend alignment (relaxed)
            if current['close'] > current['SMA_20'] > current['SMA_50']:
                score += 20
            elif current['close'] < current['SMA_20'] < current['SMA_50']:
                score += 20
            elif current['close'] > current['SMA_20'] or current['close'] < current['SMA_20']:
                score += 10  # Partial credit for any trend
            total_checks += 1
            
            # MACD alignment (relaxed)
            if current['MACD'] > current['MACD_Signal'] and current['MACD_Histogram'] > 0:
                score += 15
            elif current['MACD'] < current['MACD_Signal'] and current['MACD_Histogram'] < 0:
                score += 15
            elif current['MACD'] > current['MACD_Signal'] or current['MACD'] < current['MACD_Signal']:
                score += 8  # Partial credit
            total_checks += 1
            
            # RSI alignment (relaxed)
            if 25 <= current['RSI'] <= 75:  # Wider range
                score += 15
            elif 20 <= current['RSI'] <= 80:  # Even wider range
                score += 10
            total_checks += 1
            
            # Bollinger Bands alignment (relaxed)
            if current['close'] > current['BB_Upper'] or current['close'] < current['BB_Lower']:
                score += 10
            elif current['close'] > current['BB_Middle'] or current['close'] < current['BB_Middle']:
                score += 5  # Partial credit
            total_checks += 1
            
            # Volume confirmation (relaxed)
            if current['Volume_Ratio'] > 1.2:
                score += 10
            elif current['Volume_Ratio'] > 1.0:
                score += 5  # Partial credit
            total_checks += 1
            
            # Price action patterns (relaxed)
            if current['Hammer'] or current['Engulfing']:
                score += 10
            elif current['Doji']:
                score += 5  # Partial credit for doji
            total_checks += 1
            
            # ADX strength (relaxed)
            if current['ADX'] > 20:  # Lower threshold
                score += 10
            elif current['ADX'] > 15:
                score += 5  # Partial credit
            total_checks += 1
            
            # ATR volatility (relaxed)
            avg_atr = data['ATR'].rolling(20).mean().iloc[-1]
            if current['ATR'] > avg_atr * 1.1:  # Lower threshold
                score += 10
            elif current['ATR'] > avg_atr:
                score += 5  # Partial credit
            total_checks += 1
            
            return (score / total_checks) * 100
            
        except Exception as e:
            self.logger.error(f"Error calculating technical alignment: {e}")
            return 0
    
    def _calculate_potential_rr(self, data: pd.DataFrame) -> float:
        """Calculate potential risk-reward ratio (relaxed)"""
        try:
            current = data.iloc[-1]
            atr = current['ATR']
            
            # Conservative stop loss: 1.2 * ATR (was 1.5)
            stop_loss = atr * 1.2
            
            # Conservative take profit: 2.4 * ATR (for 1:2 RR, was 4.5 for 1:3)
            take_profit = atr * 2.4
            
            return take_profit / stop_loss
            
        except Exception as e:
            self.logger.error(f"Error calculating potential RR: {e}")
            return 0
    
    def _calculate_potential_pips(self, data: pd.DataFrame) -> float:
        """Calculate potential pips for the trade (relaxed)"""
        try:
            current = data.iloc[-1]
            atr = current['ATR']
            
            # Convert ATR to pips (assuming 5-digit pricing)
            potential_pips = atr * 2.4 * 10000  # 2.4 * ATR for take profit (was 4.5)
            
            return potential_pips
            
        except Exception as e:
            self.logger.error(f"Error calculating potential pips: {e}")
            return 0
    
    def generate_signal(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Generate trading signal with optimized criteria"""
        try:
            # Calculate indicators
            data = self.calculate_technical_indicators(data)
            
            # Check optimized conditions
            conditions = self.check_optimized_conditions(data, symbol)
            
            if not conditions['qualified']:
                return {
                    'signal': 'NO_SIGNAL',
                    'reason': conditions['reason'],
                    'confidence': 0,
                    'timestamp': datetime.now().isoformat(),
                    'strategy': 'Optimized Strategy V2'
                }
            
            # Determine signal direction
            signal_direction = self._determine_signal_direction(data)
            
            if signal_direction == 'NEUTRAL':
                return {
                    'signal': 'NO_SIGNAL',
                    'reason': 'No clear direction',
                    'confidence': 0,
                    'timestamp': datetime.now().isoformat(),
                    'strategy': 'Optimized Strategy V2'
                }
            
            # Update daily trade count
            today = datetime.now().strftime('%Y-%m-%d')
            self.daily_trades[symbol][today] += 1
            
            # Create comprehensive signal
            signal = {
                'signal': signal_direction,
                'symbol': symbol,
                'strategy': 'Optimized Strategy V2',
                'confidence': conditions['confidence'],
                'rr_ratio': conditions['rr_ratio'],
                'potential_pips': conditions['potential_pips'],
                'volume_ratio': conditions['volume_ratio'],
                'atr_ratio': conditions['atr_ratio'],
                'adx': conditions['adx'],
                'market_regime': conditions['market_regime'],
                'timestamp': datetime.now().isoformat(),
                'entry_price': data['close'].iloc[-1],
                'stop_loss': self._calculate_stop_loss(data, signal_direction),
                'take_profit': self._calculate_take_profit(data, signal_direction)
            }
            
            # Log trade
            self.trade_history.append(signal)
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error generating signal: {e}")
            return {
                'signal': 'ERROR',
                'reason': str(e),
                'timestamp': datetime.now().isoformat(),
                'strategy': 'Optimized Strategy V2'
            }
    
    def _determine_signal_direction(self, data: pd.DataFrame) -> str:
        """Determine signal direction based on technical analysis (relaxed)"""
        try:
            current = data.iloc[-1]
            
            # Count bullish and bearish indicators (relaxed scoring)
            bullish_count = 0
            bearish_count = 0
            
            # Trend indicators (relaxed)
            if current['close'] > current['SMA_20'] > current['SMA_50']:
                bullish_count += 2
            elif current['close'] < current['SMA_20'] < current['SMA_50']:
                bearish_count += 2
            elif current['close'] > current['SMA_20']:
                bullish_count += 1
            elif current['close'] < current['SMA_20']:
                bearish_count += 1
            
            # MACD (relaxed)
            if current['MACD'] > current['MACD_Signal'] and current['MACD_Histogram'] > 0:
                bullish_count += 1
            elif current['MACD'] < current['MACD_Signal'] and current['MACD_Histogram'] < 0:
                bearish_count += 1
            elif current['MACD'] > current['MACD_Signal']:
                bullish_count += 0.5
            elif current['MACD'] < current['MACD_Signal']:
                bearish_count += 0.5
            
            # RSI (relaxed)
            if current['RSI'] < 35:  # More lenient oversold
                bullish_count += 1
            elif current['RSI'] > 65:  # More lenient overbought
                bearish_count += 1
            elif current['RSI'] < 45:
                bullish_count += 0.5
            elif current['RSI'] > 55:
                bearish_count += 0.5
            
            # Bollinger Bands (relaxed)
            if current['close'] < current['BB_Lower']:
                bullish_count += 1
            elif current['close'] > current['BB_Upper']:
                bearish_count += 1
            elif current['close'] < current['BB_Middle']:
                bullish_count += 0.5
            elif current['close'] > current['BB_Middle']:
                bearish_count += 0.5
            
            # Price action (relaxed)
            if current['Hammer']:
                bullish_count += 1
            elif current['Engulfing'] and current['close'] > current['open']:
                bullish_count += 1
            elif current['Engulfing'] and current['close'] < current['open']:
                bearish_count += 1
            
            # Determine direction (relaxed threshold)
            if bullish_count > bearish_count + 0.5:  # Lower threshold
                return 'LONG'
            elif bearish_count > bullish_count + 0.5:  # Lower threshold
                return 'SHORT'
            else:
                return 'NEUTRAL'
                
        except Exception as e:
            self.logger.error(f"Error determining signal direction: {e}")
            return 'NEUTRAL'
    
    def _calculate_stop_loss(self, data: pd.DataFrame, direction: str) -> float:
        """Calculate stop loss based on ATR"""
        try:
            current = data.iloc[-1]
            atr = current['ATR']
            entry_price = current['close']
            
            if direction == 'LONG':
                return entry_price - (atr * 1.2)  # 1.2 ATR stop loss
            else:
                return entry_price + (atr * 1.2)  # 1.2 ATR stop loss
                
        except Exception as e:
            self.logger.error(f"Error calculating stop loss: {e}")
            return 0
    
    def _calculate_take_profit(self, data: pd.DataFrame, direction: str) -> float:
        """Calculate take profit based on ATR"""
        try:
            current = data.iloc[-1]
            atr = current['ATR']
            entry_price = current['close']
            
            if direction == 'LONG':
                return entry_price + (atr * 2.4)  # 2.4 ATR take profit (1:2 RR)
            else:
                return entry_price - (atr * 2.4)  # 2.4 ATR take profit (1:2 RR)
                
        except Exception as e:
            self.logger.error(f"Error calculating take profit: {e}")
            return 0
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the strategy"""
        try:
            if not self.trade_history:
                return {'message': 'No trades executed yet'}
            
            total_trades = len(self.trade_history)
            winning_trades = len([t for t in self.trade_history if t.get('result') == 'WIN'])
            losing_trades = len([t for t in self.trade_history if t.get('result') == 'LOSS'])
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            avg_confidence = np.mean([t.get('confidence', 0) for t in self.trade_history])
            avg_rr = np.mean([t.get('rr_ratio', 0) for t in self.trade_history])
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'avg_confidence': avg_confidence,
                'avg_rr_ratio': avg_rr,
                'strategy': 'Optimized Strategy V2'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return {'error': str(e)}

def main():
    """Main function to test Optimized Strategy V2"""
    strategy = OptimizedStrategyV2()
    
    print("🎯 Optimized Strategy V2 Created Successfully!")
    print("\n📊 Key Features:")
    print("• Minimum 1:2 Risk-Reward Ratio (realistic)")
    print("• Minimum 70% Confidence Score (achievable)")
    print("• Maximum 3 Trades Per Day Per Pair (practical)")
    print("• Minimum 10 Pips Potential (realistic)")
    print("• All Major Sessions (flexible)")
    print("• Market Regime Detection")
    print("• Adaptive Parameters")
    print("• Enhanced Risk Management")

if __name__ == "__main__":
    main()
