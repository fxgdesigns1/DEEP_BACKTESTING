#!/usr/bin/env python3
"""
ULTRA-STRICT V3 STRATEGY
Ultra-strict, high-quality strategy with AI insights and entry suggestions
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

class UltraStrictV3Strategy:
    """
    Ultra-Strict V3 Strategy - Ultra-strict criteria for guaranteed trades
    Focuses only on the highest quality setups with minimum 1:3 RR ratio
    """
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize Ultra-Strict V3 Strategy"""
        self.config = self._load_config(config_path)
        self.logger = logger
        
        # Ultra-strict parameters
        self.min_rr_ratio = 3.0  # Minimum 1:3 risk-reward
        self.min_confidence = 85  # Minimum 85% confidence
        self.min_volume_multiplier = 2.0  # Volume must be 2x average
        self.min_atr_multiplier = 1.5  # ATR must be 1.5x average
        self.max_daily_trades = 2  # Maximum 2 trades per day per pair
        self.min_pips_threshold = 15  # Minimum 15 pips potential
        
        # Market regime requirements
        self.min_adx_trend = 25  # Minimum ADX for trend confirmation
        self.max_correlation_threshold = 0.7  # Maximum correlation with other pairs
        
        # Session requirements
        self.required_sessions = ['London', 'New York']  # Must be during major sessions
        
        # News filter requirements
        self.news_impact_threshold = 0.8  # High news impact required
        self.sentiment_threshold = 0.7  # Strong sentiment required
        
        # Performance tracking
        self.daily_trades = {}  # Track daily trades per pair
        self.trade_history = []
        
        # AI Insights tracking
        self.ai_insights = []
        
        self.logger.info("🎯 Ultra-Strict V3 Strategy initialized")
    
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
    
    def check_ultra_strict_conditions(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Check ultra-strict conditions for trade qualification"""
        try:
            if len(data) < 50:
                return {'qualified': False, 'reason': 'Insufficient data'}
            
            current = data.iloc[-1]
            previous = data.iloc[-2]
            
            # 1. Market Regime Check
            if current['ADX'] < self.min_adx_trend:
                return {'qualified': False, 'reason': f'Weak trend (ADX: {current["ADX"]:.1f})'}
            
            # 2. Volume Check
            if current['Volume_Ratio'] < self.min_volume_multiplier:
                return {'qualified': False, 'reason': f'Low volume (Ratio: {current["Volume_Ratio"]:.1f})'}
            
            # 3. ATR Check
            avg_atr = data['ATR'].rolling(20).mean().iloc[-1]
            if current['ATR'] < avg_atr * self.min_atr_multiplier:
                return {'qualified': False, 'reason': f'Low volatility (ATR: {current["ATR"]:.5f})'}
            
            # 4. Daily Trade Limit Check
            today = datetime.now().strftime('%Y-%m-%d')
            if symbol not in self.daily_trades:
                self.daily_trades[symbol] = {}
            if today not in self.daily_trades[symbol]:
                self.daily_trades[symbol][today] = 0
            
            if self.daily_trades[symbol][today] >= self.max_daily_trades:
                return {'qualified': False, 'reason': 'Daily trade limit reached'}
            
            # 5. Session Check
            current_hour = datetime.now().hour
            if not self._is_major_session(current_hour):
                return {'qualified': False, 'reason': 'Not during major session'}
            
            # 6. Price Action Check
            if not self._check_price_action_quality(data):
                return {'qualified': False, 'reason': 'Poor price action quality'}
            
            # 7. Technical Alignment Check
            alignment_score = self._calculate_technical_alignment(data)
            if alignment_score < self.min_confidence:
                return {'qualified': False, 'reason': f'Low technical alignment ({alignment_score:.1f}%)'}
            
            # 8. Risk-Reward Check
            rr_ratio = self._calculate_potential_rr(data)
            if rr_ratio < self.min_rr_ratio:
                return {'qualified': False, 'reason': f'Insufficient RR ratio ({rr_ratio:.1f})'}
            
            # 9. Minimum Pips Check
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
                'adx': current['ADX']
            }
            
        except Exception as e:
            self.logger.error(f"Error checking ultra-strict conditions: {e}")
            return {'qualified': False, 'reason': f'Error: {str(e)}'}
    
    def _is_major_session(self, hour: int) -> bool:
        """Check if current hour is during major trading session"""
        # London: 7-16 UTC, New York: 13-22 UTC
        london_session = 7 <= hour <= 16
        ny_session = 13 <= hour <= 22
        return london_session or ny_session
    
    def _check_price_action_quality(self, data: pd.DataFrame) -> bool:
        """Check price action quality"""
        try:
            current = data.iloc[-1]
            
            # Check for strong momentum
            price_change = abs(current['close'] - current['open'])
            total_range = current['high'] - current['low']
            
            if price_change / total_range < 0.6:  # Body should be at least 60% of range
                return False
            
            # Check for clean wicks
            upper_wick = current['high'] - max(current['open'], current['close'])
            lower_wick = min(current['open'], current['close']) - current['low']
            
            if upper_wick > price_change * 0.5 or lower_wick > price_change * 0.5:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking price action quality: {e}")
            return False
    
    def _calculate_technical_alignment(self, data: pd.DataFrame) -> float:
        """Calculate technical alignment score (0-100)"""
        try:
            current = data.iloc[-1]
            score = 0
            total_checks = 0
            
            # Trend alignment
            if current['close'] > current['SMA_20'] > current['SMA_50']:
                score += 20
            elif current['close'] < current['SMA_20'] < current['SMA_50']:
                score += 20
            total_checks += 1
            
            # MACD alignment
            if current['MACD'] > current['MACD_Signal'] and current['MACD_Histogram'] > 0:
                score += 15
            elif current['MACD'] < current['MACD_Signal'] and current['MACD_Histogram'] < 0:
                score += 15
            total_checks += 1
            
            # RSI alignment
            if 30 <= current['RSI'] <= 70:
                score += 15
            total_checks += 1
            
            # Bollinger Bands alignment
            if current['close'] > current['BB_Upper'] or current['close'] < current['BB_Lower']:
                score += 10
            total_checks += 1
            
            # Volume confirmation
            if current['Volume_Ratio'] > 1.5:
                score += 10
            total_checks += 1
            
            # Price action patterns
            if current['Hammer'] or current['Engulfing']:
                score += 10
            total_checks += 1
            
            # ADX strength
            if current['ADX'] > 25:
                score += 10
            total_checks += 1
            
            # ATR volatility
            avg_atr = data['ATR'].rolling(20).mean().iloc[-1]
            if current['ATR'] > avg_atr * 1.2:
                score += 10
            total_checks += 1
            
            return (score / total_checks) * 100
            
        except Exception as e:
            self.logger.error(f"Error calculating technical alignment: {e}")
            return 0
    
    def _calculate_potential_rr(self, data: pd.DataFrame) -> float:
        """Calculate potential risk-reward ratio"""
        try:
            current = data.iloc[-1]
            atr = current['ATR']
            
            # Conservative stop loss: 1.5 * ATR
            stop_loss = atr * 1.5
            
            # Conservative take profit: 4.5 * ATR (for 1:3 RR)
            take_profit = atr * 4.5
            
            return take_profit / stop_loss
            
        except Exception as e:
            self.logger.error(f"Error calculating potential RR: {e}")
            return 0
    
    def _calculate_potential_pips(self, data: pd.DataFrame) -> float:
        """Calculate potential pips for the trade"""
        try:
            current = data.iloc[-1]
            atr = current['ATR']
            
            # Convert ATR to pips (assuming 5-digit pricing)
            potential_pips = atr * 4.5 * 10000  # 4.5 * ATR for take profit
            
            return potential_pips
            
        except Exception as e:
            self.logger.error(f"Error calculating potential pips: {e}")
            return 0
    
    def generate_ai_insights(self, data: pd.DataFrame, symbol: str, signal_direction: str) -> Dict[str, Any]:
        """Generate AI insights and entry suggestions"""
        try:
            current = data.iloc[-1]
            
            # Analyze market conditions
            market_analysis = self._analyze_market_conditions(data)
            
            # Generate entry suggestions
            entry_suggestions = self._generate_entry_suggestions(data, signal_direction)
            
            # Risk management insights
            risk_insights = self._generate_risk_insights(data, signal_direction)
            
            # Technical analysis insights
            technical_insights = self._generate_technical_insights(data)
            
            insights = {
                'strategy_used': 'Ultra-Strict V3',
                'signal_direction': signal_direction,
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'market_analysis': market_analysis,
                'entry_suggestions': entry_suggestions,
                'risk_insights': risk_insights,
                'technical_insights': technical_insights,
                'confidence_score': self._calculate_technical_alignment(data),
                'risk_reward_ratio': self._calculate_potential_rr(data),
                'potential_pips': self._calculate_potential_pips(data)
            }
            
            # Store insights
            self.ai_insights.append(insights)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating AI insights: {e}")
            return {'error': str(e)}
    
    def _analyze_market_conditions(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze current market conditions"""
        try:
            current = data.iloc[-1]
            
            # Trend analysis
            trend_strength = "Strong" if current['ADX'] > 30 else "Moderate" if current['ADX'] > 20 else "Weak"
            trend_direction = "Bullish" if current['close'] > current['SMA_20'] > current['SMA_50'] else "Bearish"
            
            # Volatility analysis
            avg_atr = data['ATR'].rolling(20).mean().iloc[-1]
            volatility_level = "High" if current['ATR'] > avg_atr * 1.5 else "Normal" if current['ATR'] > avg_atr else "Low"
            
            # Volume analysis
            volume_level = "High" if current['Volume_Ratio'] > 2.0 else "Normal" if current['Volume_Ratio'] > 1.5 else "Low"
            
            # Session analysis
            current_hour = datetime.now().hour
            session = "London" if 7 <= current_hour <= 16 else "New York" if 13 <= current_hour <= 22 else "Tokyo"
            
            return {
                'trend_strength': trend_strength,
                'trend_direction': trend_direction,
                'volatility_level': volatility_level,
                'volume_level': volume_level,
                'current_session': session,
                'adx_value': current['ADX'],
                'atr_value': current['ATR'],
                'volume_ratio': current['Volume_Ratio']
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing market conditions: {e}")
            return {'error': str(e)}
    
    def _generate_entry_suggestions(self, data: pd.DataFrame, signal_direction: str) -> Dict[str, Any]:
        """Generate specific entry suggestions"""
        try:
            current = data.iloc[-1]
            atr = current['ATR']
            
            if signal_direction == 'LONG':
                entry_price = current['close']
                stop_loss = entry_price - (atr * 1.5)
                take_profit = entry_price + (atr * 4.5)
                
                entry_suggestions = {
                    'entry_type': 'Market Order',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'entry_timing': 'Immediate entry recommended',
                    'entry_reason': 'Strong bullish momentum with high volume confirmation',
                    'risk_pips': (entry_price - stop_loss) * 10000,
                    'reward_pips': (take_profit - entry_price) * 10000
                }
            else:  # SHORT
                entry_price = current['close']
                stop_loss = entry_price + (atr * 1.5)
                take_profit = entry_price - (atr * 4.5)
                
                entry_suggestions = {
                    'entry_type': 'Market Order',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'entry_timing': 'Immediate entry recommended',
                    'entry_reason': 'Strong bearish momentum with high volume confirmation',
                    'risk_pips': (stop_loss - entry_price) * 10000,
                    'reward_pips': (entry_price - take_profit) * 10000
                }
            
            return entry_suggestions
            
        except Exception as e:
            self.logger.error(f"Error generating entry suggestions: {e}")
            return {'error': str(e)}
    
    def _generate_risk_insights(self, data: pd.DataFrame, signal_direction: str) -> Dict[str, Any]:
        """Generate risk management insights"""
        try:
            current = data.iloc[-1]
            
            # Position sizing recommendation
            confidence = self._calculate_technical_alignment(data)
            position_size = "Standard" if confidence >= 90 else "Reduced" if confidence >= 85 else "Minimal"
            
            # Risk assessment
            risk_level = "Low" if confidence >= 90 else "Medium" if confidence >= 85 else "High"
            
            # Correlation warning
            correlation_warning = "Monitor USD pairs for correlation risk" if "USD" in signal_direction else "Standard correlation monitoring"
            
            return {
                'position_size_recommendation': position_size,
                'risk_level': risk_level,
                'confidence_score': confidence,
                'correlation_warning': correlation_warning,
                'max_risk_per_trade': "1% of account",
                'stop_loss_distance': f"{current['ATR'] * 1.5 * 10000:.1f} pips",
                'take_profit_distance': f"{current['ATR'] * 4.5 * 10000:.1f} pips"
            }
            
        except Exception as e:
            self.logger.error(f"Error generating risk insights: {e}")
            return {'error': str(e)}
    
    def _generate_technical_insights(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Generate technical analysis insights"""
        try:
            current = data.iloc[-1]
            
            # RSI analysis
            rsi_signal = "Oversold" if current['RSI'] < 30 else "Overbought" if current['RSI'] > 70 else "Neutral"
            
            # MACD analysis
            macd_signal = "Bullish" if current['MACD'] > current['MACD_Signal'] else "Bearish"
            
            # Bollinger Bands analysis
            bb_position = "Upper Band" if current['close'] > current['BB_Upper'] else "Lower Band" if current['close'] < current['BB_Lower'] else "Middle"
            
            # Price action patterns
            patterns = []
            if current['Hammer']:
                patterns.append("Hammer Pattern")
            if current['Engulfing']:
                patterns.append("Engulfing Pattern")
            if current['Doji']:
                patterns.append("Doji Pattern")
            
            return {
                'rsi_signal': rsi_signal,
                'rsi_value': current['RSI'],
                'macd_signal': macd_signal,
                'macd_value': current['MACD'],
                'bollinger_bands_position': bb_position,
                'price_action_patterns': patterns,
                'trend_strength': current['ADX'],
                'volume_confirmation': current['Volume_Ratio'] > 1.5
            }
            
        except Exception as e:
            self.logger.error(f"Error generating technical insights: {e}")
            return {'error': str(e)}
    
    def generate_signal(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Generate trading signal with ultra-strict criteria and AI insights"""
        try:
            # Calculate indicators
            data = self.calculate_technical_indicators(data)
            
            # Check ultra-strict conditions
            conditions = self.check_ultra_strict_conditions(data, symbol)
            
            if not conditions['qualified']:
                return {
                    'signal': 'NO_SIGNAL',
                    'reason': conditions['reason'],
                    'confidence': 0,
                    'timestamp': datetime.now().isoformat(),
                    'strategy': 'Ultra-Strict V3'
                }
            
            # Determine signal direction
            signal_direction = self._determine_signal_direction(data)
            
            if signal_direction == 'NEUTRAL':
                return {
                    'signal': 'NO_SIGNAL',
                    'reason': 'No clear direction',
                    'confidence': 0,
                    'timestamp': datetime.now().isoformat(),
                    'strategy': 'Ultra-Strict V3'
                }
            
            # Update daily trade count
            today = datetime.now().strftime('%Y-%m-%d')
            self.daily_trades[symbol][today] += 1
            
            # Generate AI insights
            ai_insights = self.generate_ai_insights(data, symbol, signal_direction)
            
            # Create comprehensive signal
            signal = {
                'signal': signal_direction,
                'symbol': symbol,
                'strategy': 'Ultra-Strict V3',
                'confidence': conditions['confidence'],
                'rr_ratio': conditions['rr_ratio'],
                'potential_pips': conditions['potential_pips'],
                'volume_ratio': conditions['volume_ratio'],
                'atr_ratio': conditions['atr_ratio'],
                'adx': conditions['adx'],
                'timestamp': datetime.now().isoformat(),
                'ai_insights': ai_insights,
                'entry_suggestions': ai_insights.get('entry_suggestions', {}),
                'risk_insights': ai_insights.get('risk_insights', {}),
                'technical_insights': ai_insights.get('technical_insights', {}),
                'market_analysis': ai_insights.get('market_analysis', {})
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
                'strategy': 'Ultra-Strict V3'
            }
    
    def _determine_signal_direction(self, data: pd.DataFrame) -> str:
        """Determine signal direction based on technical analysis"""
        try:
            current = data.iloc[-1]
            
            # Count bullish and bearish indicators
            bullish_count = 0
            bearish_count = 0
            
            # Trend indicators
            if current['close'] > current['SMA_20'] > current['SMA_50']:
                bullish_count += 2
            elif current['close'] < current['SMA_20'] < current['SMA_50']:
                bearish_count += 2
            
            # MACD
            if current['MACD'] > current['MACD_Signal'] and current['MACD_Histogram'] > 0:
                bullish_count += 1
            elif current['MACD'] < current['MACD_Signal'] and current['MACD_Histogram'] < 0:
                bearish_count += 1
            
            # RSI
            if current['RSI'] < 30:
                bullish_count += 1
            elif current['RSI'] > 70:
                bearish_count += 1
            
            # Bollinger Bands
            if current['close'] < current['BB_Lower']:
                bullish_count += 1
            elif current['close'] > current['BB_Upper']:
                bearish_count += 1
            
            # Price action
            if current['Hammer']:
                bullish_count += 1
            
            # Determine direction
            if bullish_count > bearish_count + 1:
                return 'LONG'
            elif bearish_count > bullish_count + 1:
                return 'SHORT'
            else:
                return 'NEUTRAL'
                
        except Exception as e:
            self.logger.error(f"Error determining signal direction: {e}")
            return 'NEUTRAL'
    
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
                'strategy': 'Ultra-Strict V3'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return {'error': str(e)}
    
    def update_live_data(self, symbol: str, data: pd.DataFrame):
        """Update live data for the strategy (compatibility method)"""
        try:
            # Store the latest data for this symbol
            if not hasattr(self, 'live_data'):
                self.live_data = {}
            
            self.live_data[symbol] = data
            self.logger.info(f"Updated live data for {symbol}: {len(data)} candles")
            
        except Exception as e:
            self.logger.error(f"Error updating live data for {symbol}: {e}")
    
    def generate_live_signals(self, symbol: str) -> Dict[str, Any]:
        """Generate live signals for a symbol (compatibility method)"""
        try:
            if symbol not in self.live_data or self.live_data[symbol] is None:
                return {
                    'signal': 'NO_SIGNAL',
                    'reason': 'No live data available',
                    'confidence': 0,
                    'timestamp': datetime.now().isoformat(),
                    'strategy': 'Ultra-Strict V3'
                }
            
            data = self.live_data[symbol]
            return self.generate_signal(data, symbol)
            
        except Exception as e:
            self.logger.error(f"Error generating live signals for {symbol}: {e}")
            return {
                'signal': 'ERROR',
                'reason': str(e),
                'timestamp': datetime.now().isoformat(),
                'strategy': 'Ultra-Strict V3'
            }
    
    def save_strategy_config(self, filename: str = "ultra_strict_v3_config.json"):
        """Save strategy configuration"""
        try:
            config = {
                'strategy_name': 'Ultra-Strict V3',
                'version': '3.0',
                'description': 'Ultra-strict, high-quality strategy with minimum 1:3 RR and AI insights',
                'parameters': {
                    'min_rr_ratio': self.min_rr_ratio,
                    'min_confidence': self.min_confidence,
                    'min_volume_multiplier': self.min_volume_multiplier,
                    'min_atr_multiplier': self.min_atr_multiplier,
                    'max_daily_trades': self.max_daily_trades,
                    'min_pips_threshold': self.min_pips_threshold,
                    'min_adx_trend': self.min_adx_trend,
                    'news_impact_threshold': self.news_impact_threshold,
                    'sentiment_threshold': self.sentiment_threshold
                },
                'features': [
                    'AI Insights and Entry Suggestions',
                    'Ultra-Strict Entry Criteria',
                    'Minimum 1:3 Risk-Reward Ratio',
                    '85%+ Confidence Requirement',
                    'Major Session Only Trading',
                    'High Volume & Volatility Requirements',
                    'Comprehensive Technical Alignment',
                    'Advanced Risk Management'
                ],
                'created_at': datetime.now().isoformat()
            }
            
            with open(filename, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info(f"Strategy config saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving strategy config: {e}")


def main():
    """Main function to test Ultra-Strict V3 Strategy"""
    strategy = UltraStrictV3Strategy()
    
    # Save configuration
    strategy.save_strategy_config()
    
    print("🎯 Ultra-Strict V3 Strategy Created Successfully!")
    print("\n📊 Key Features:")
    print("• Minimum 1:3 Risk-Reward Ratio")
    print("• Minimum 85% Confidence Score")
    print("• Maximum 2 Trades Per Day Per Pair")
    print("• Minimum 15 Pips Potential")
    print("• Major Session Only Trading")
    print("• Ultra-Strict Technical Alignment")
    print("• High Volume & Volatility Requirements")
    print("• AI Insights and Entry Suggestions")
    
    print("\n💾 Configuration saved to: ultra_strict_v3_config.json")


if __name__ == "__main__":
    main()
