#!/usr/bin/env python3
"""
COMPREHENSIVE ENHANCED STRATEGY
Strategy that integrates news, indicators, and technical analysis for enhanced decision making
"""

import pandas as pd
import numpy as np
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Add current directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news_integration import NewsIntegration
from indicators_integration import IndicatorsIntegration

logger = logging.getLogger(__name__)

class ComprehensiveEnhancedStrategy:
    """
    Strategy that integrates news, indicators, and technical analysis for enhanced decision making
    """
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize Comprehensive Enhanced Strategy"""
        self.logger = logger
        
        # Initialize integration modules
        self.news_integration = NewsIntegration()
        self.indicators_integration = IndicatorsIntegration()
        
        # Strategy parameters
        self.min_rr_ratio = 2.0
        self.min_confidence = 70
        self.min_volume_multiplier = 1.5
        self.min_atr_multiplier = 1.2
        self.max_daily_trades = 3
        self.min_pips_threshold = 10
        
        # Enhanced parameters
        self.news_weight = 0.3          # 30% weight for news analysis
        self.indicators_weight = 0.4    # 40% weight for indicators analysis
        self.technical_weight = 0.3     # 30% weight for technical analysis
        
        # Performance tracking
        self.daily_trades = {}
        self.trade_history = []
        
        self.logger.info("🎯 Comprehensive Enhanced Strategy initialized")
    
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
            
            # Volume analysis
            data['Volume_SMA'] = data['volume'].rolling(window=20).mean()
            data['Volume_Ratio'] = data['volume'] / data['Volume_SMA']
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return data
    
    def get_comprehensive_analysis(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Get comprehensive analysis combining news, indicators, and technical analysis"""
        try:
            current_time = datetime.now()
            
            # 1. News Analysis
            news_context = self.news_integration.get_news_context(symbol, current_time)
            
            # 2. Indicators Analysis
            indicators_analysis = self.indicators_integration.get_comprehensive_analysis(symbol)
            
            # 3. Technical Analysis
            technical_analysis = self._perform_technical_analysis(data)
            
            # 4. Combine analyses
            combined_analysis = self._combine_analyses(news_context, indicators_analysis, technical_analysis)
            
            return {
                'symbol': symbol,
                'timestamp': current_time.isoformat(),
                'news_analysis': news_context,
                'indicators_analysis': indicators_analysis,
                'technical_analysis': technical_analysis,
                'combined_analysis': combined_analysis
            }
            
        except Exception as e:
            self.logger.error(f"Error getting comprehensive analysis: {e}")
            return {'error': str(e)}
    
    def _perform_technical_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform technical analysis on price data"""
        try:
            if len(data) < 50:
                return {'error': 'Insufficient data'}
            
            current = data.iloc[-1]
            
            # Trend analysis
            trend_score = 0
            if current['close'] > current['SMA_20'] > current['SMA_50']:
                trend_score = 1.0  # Strong bullish
            elif current['close'] < current['SMA_20'] < current['SMA_50']:
                trend_score = -1.0  # Strong bearish
            elif current['close'] > current['SMA_20']:
                trend_score = 0.5  # Weak bullish
            elif current['close'] < current['SMA_20']:
                trend_score = -0.5  # Weak bearish
            
            # Momentum analysis
            momentum_score = 0
            if current['RSI'] < 30:
                momentum_score = 1.0  # Oversold - bullish
            elif current['RSI'] > 70:
                momentum_score = -1.0  # Overbought - bearish
            elif 40 <= current['RSI'] <= 60:
                momentum_score = 0  # Neutral
            
            # MACD analysis
            macd_score = 0
            if current['MACD'] > current['MACD_Signal'] and current['MACD_Histogram'] > 0:
                macd_score = 1.0  # Strong bullish
            elif current['MACD'] < current['MACD_Signal'] and current['MACD_Histogram'] < 0:
                macd_score = -1.0  # Strong bearish
            elif current['MACD'] > current['MACD_Signal']:
                macd_score = 0.5  # Weak bullish
            elif current['MACD'] < current['MACD_Signal']:
                macd_score = -0.5  # Weak bearish
            
            # Volume analysis
            volume_score = 0
            if current['Volume_Ratio'] > 1.5:
                volume_score = 1.0  # High volume
            elif current['Volume_Ratio'] > 1.2:
                volume_score = 0.5  # Above average volume
            elif current['Volume_Ratio'] < 0.8:
                volume_score = -0.5  # Low volume
            
            # Calculate overall technical score
            technical_score = (trend_score * 0.4 + momentum_score * 0.3 + macd_score * 0.2 + volume_score * 0.1)
            
            return {
                'trend_score': trend_score,
                'momentum_score': momentum_score,
                'macd_score': macd_score,
                'volume_score': volume_score,
                'overall_score': technical_score,
                'rsi': current['RSI'],
                'volume_ratio': current['Volume_Ratio'],
                'atr': current['ATR']
            }
            
        except Exception as e:
            self.logger.error(f"Error performing technical analysis: {e}")
            return {'error': str(e)}
    
    def _combine_analyses(self, news_context: Dict[str, Any], indicators_analysis: Dict[str, Any], technical_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Combine news, indicators, and technical analyses"""
        try:
            combined_score = 0.0
            confidence = 0.0
            signals = []
            
            # News contribution
            if news_context['has_recent_news']:
                news_impact = news_context['impact_score']
                news_sentiment = news_context['sentiment_analysis']['sentiment_score']
                news_contribution = news_impact * news_sentiment * self.news_weight
                combined_score += news_contribution
                confidence += news_impact * self.news_weight
                
                if news_impact > 0.5:
                    signals.append(f"High impact news: {news_context['impact_score']:.2f}")
            
            # Indicators contribution
            if 'overall_score' in indicators_analysis:
                indicators_score = (indicators_analysis['overall_score'] - 50) / 50  # Normalize to -1 to 1
                indicators_contribution = indicators_score * self.indicators_weight
                combined_score += indicators_contribution
                confidence += (indicators_analysis['overall_score'] / 100) * self.indicators_weight
                
                if indicators_analysis['overall_score'] > 70:
                    signals.append(f"Strong indicators: {indicators_analysis['overall_score']:.1f}")
                elif indicators_analysis['overall_score'] < 30:
                    signals.append(f"Weak indicators: {indicators_analysis['overall_score']:.1f}")
            
            # Technical contribution
            if 'overall_score' in technical_analysis:
                technical_contribution = technical_analysis['overall_score'] * self.technical_weight
                combined_score += technical_contribution
                confidence += abs(technical_analysis['overall_score']) * self.technical_weight
                
                if technical_analysis['overall_score'] > 0.5:
                    signals.append("Strong technical signals")
                elif technical_analysis['overall_score'] < -0.5:
                    signals.append("Weak technical signals")
            
            # Determine overall direction
            if combined_score > 0.3:
                direction = 'bullish'
                strength = 'strong' if combined_score > 0.6 else 'moderate'
            elif combined_score < -0.3:
                direction = 'bearish'
                strength = 'strong' if combined_score < -0.6 else 'moderate'
            else:
                direction = 'neutral'
                strength = 'weak'
            
            # Determine recommendation
            if combined_score > 0.5 and confidence > 0.7:
                recommendation = 'strong_buy'
            elif combined_score > 0.2 and confidence > 0.6:
                recommendation = 'buy'
            elif combined_score < -0.5 and confidence > 0.7:
                recommendation = 'strong_sell'
            elif combined_score < -0.2 and confidence > 0.6:
                recommendation = 'sell'
            else:
                recommendation = 'hold'
            
            return {
                'combined_score': combined_score,
                'confidence': min(1.0, confidence),
                'direction': direction,
                'strength': strength,
                'recommendation': recommendation,
                'signals': signals,
                'news_contribution': news_context.get('impact_score', 0) * self.news_weight,
                'indicators_contribution': indicators_analysis.get('overall_score', 50) / 100 * self.indicators_weight,
                'technical_contribution': technical_analysis.get('overall_score', 0) * self.technical_weight
            }
            
        except Exception as e:
            self.logger.error(f"Error combining analyses: {e}")
            return {'error': str(e)}
    
    def check_comprehensive_conditions(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Check conditions with comprehensive analysis"""
        try:
            if len(data) < 50:
                return {'qualified': False, 'reason': 'Insufficient data'}
            
            current = data.iloc[-1]
            current_time = datetime.now()
            
            # Get comprehensive analysis
            analysis = self.get_comprehensive_analysis(data, symbol)
            if 'error' in analysis:
                return {'qualified': False, 'reason': f'Analysis error: {analysis["error"]}'}
            
            combined_analysis = analysis['combined_analysis']
            
            # 1. Basic technical checks
            if current['Volume_Ratio'] < self.min_volume_multiplier:
                return {'qualified': False, 'reason': f'Low volume (Ratio: {current["Volume_Ratio"]:.1f})'}
            
            avg_atr = data['ATR'].rolling(20).mean().iloc[-1]
            if current['ATR'] < avg_atr * self.min_atr_multiplier:
                return {'qualified': False, 'reason': f'Low volatility (ATR: {current["ATR"]:.5f})'}
            
            # 2. Daily trade limit check
            today = datetime.now().strftime('%Y-%m-%d')
            if symbol not in self.daily_trades:
                self.daily_trades[symbol] = {}
            if today not in self.daily_trades[symbol]:
                self.daily_trades[symbol][today] = 0
            
            if self.daily_trades[symbol][today] >= self.max_daily_trades:
                return {'qualified': False, 'reason': 'Daily trade limit reached'}
            
            # 3. Comprehensive analysis check
            if combined_analysis['confidence'] < self.min_confidence / 100:
                return {'qualified': False, 'reason': f'Low confidence ({combined_analysis["confidence"]*100:.1f}%)'}
            
            # 4. News filtering
            news_context = analysis['news_analysis']
            if news_context['has_recent_news']:
                should_filter, filter_reason = self.news_integration.should_filter_trade(
                    symbol, current_time, 'LONG'  # We'll determine direction later
                )
                
                if should_filter:
                    return {'qualified': False, 'reason': f'News filter: {filter_reason}'}
            
            # 5. Risk-Reward check
            rr_ratio = self._calculate_potential_rr(data)
            if rr_ratio < self.min_rr_ratio:
                return {'qualified': False, 'reason': f'Insufficient RR ratio ({rr_ratio:.1f})'}
            
            # 6. Minimum pips check
            potential_pips = self._calculate_potential_pips(data)
            if potential_pips < self.min_pips_threshold:
                return {'qualified': False, 'reason': f'Insufficient potential pips ({potential_pips:.1f})'}
            
            return {
                'qualified': True,
                'confidence': combined_analysis['confidence'] * 100,
                'combined_score': combined_analysis['combined_score'],
                'direction': combined_analysis['direction'],
                'strength': combined_analysis['strength'],
                'recommendation': combined_analysis['recommendation'],
                'rr_ratio': rr_ratio,
                'potential_pips': potential_pips,
                'volume_ratio': current['Volume_Ratio'],
                'atr_ratio': current['ATR'] / avg_atr,
                'analysis': analysis
            }
            
        except Exception as e:
            self.logger.error(f"Error checking comprehensive conditions: {e}")
            return {'qualified': False, 'reason': f'Error: {str(e)}'}
    
    def _calculate_potential_rr(self, data: pd.DataFrame) -> float:
        """Calculate potential risk-reward ratio"""
        try:
            current = data.iloc[-1]
            atr = current['ATR']
            
            # Conservative stop loss: 1.2 * ATR
            stop_loss = atr * 1.2
            
            # Conservative take profit: 2.4 * ATR (for 1:2 RR)
            take_profit = atr * 2.4
            
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
            potential_pips = atr * 2.4 * 10000  # 2.4 * ATR for take profit
            
            return potential_pips
            
        except Exception as e:
            self.logger.error(f"Error calculating potential pips: {e}")
            return 0
    
    def generate_signal(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Generate trading signal with comprehensive analysis"""
        try:
            # Calculate indicators
            data = self.calculate_technical_indicators(data)
            
            # Check comprehensive conditions
            conditions = self.check_comprehensive_conditions(data, symbol)
            
            if not conditions['qualified']:
                return {
                    'signal': 'NO_SIGNAL',
                    'reason': conditions['reason'],
                    'confidence': 0,
                    'timestamp': datetime.now().isoformat(),
                    'strategy': 'Comprehensive Enhanced Strategy'
                }
            
            # Determine signal direction based on comprehensive analysis
            combined_analysis = conditions['analysis']['combined_analysis']
            
            if combined_analysis['recommendation'] in ['strong_buy', 'buy']:
                signal_direction = 'LONG'
            elif combined_analysis['recommendation'] in ['strong_sell', 'sell']:
                signal_direction = 'SHORT'
            else:
                return {
                    'signal': 'NO_SIGNAL',
                    'reason': 'No clear direction from comprehensive analysis',
                    'confidence': 0,
                    'timestamp': datetime.now().isoformat(),
                    'strategy': 'Comprehensive Enhanced Strategy'
                }
            
            # Update daily trade count
            today = datetime.now().strftime('%Y-%m-%d')
            self.daily_trades[symbol][today] += 1
            
            # Create comprehensive signal
            signal = {
                'signal': signal_direction,
                'symbol': symbol,
                'strategy': 'Comprehensive Enhanced Strategy',
                'confidence': conditions['confidence'],
                'combined_score': conditions['combined_score'],
                'direction': conditions['direction'],
                'strength': conditions['strength'],
                'recommendation': conditions['recommendation'],
                'rr_ratio': conditions['rr_ratio'],
                'potential_pips': conditions['potential_pips'],
                'volume_ratio': conditions['volume_ratio'],
                'atr_ratio': conditions['atr_ratio'],
                'timestamp': datetime.now().isoformat(),
                'entry_price': data['close'].iloc[-1],
                'stop_loss': self._calculate_stop_loss(data, signal_direction),
                'take_profit': self._calculate_take_profit(data, signal_direction),
                'analysis': conditions['analysis']
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
                'strategy': 'Comprehensive Enhanced Strategy'
            }
    
    def _calculate_stop_loss(self, data: pd.DataFrame, direction: str) -> float:
        """Calculate stop loss based on ATR"""
        try:
            current = data.iloc[-1]
            atr = current['ATR']
            entry_price = current['close']
            
            if direction == 'LONG':
                return entry_price - (atr * 1.2)
            else:
                return entry_price + (atr * 1.2)
                
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
                return entry_price + (atr * 2.4)
            else:
                return entry_price - (atr * 2.4)
                
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
            avg_combined_score = np.mean([t.get('combined_score', 0) for t in self.trade_history])
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'avg_confidence': avg_confidence,
                'avg_rr_ratio': avg_rr,
                'avg_combined_score': avg_combined_score,
                'strategy': 'Comprehensive Enhanced Strategy'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return {'error': str(e)}

def main():
    """Main function to test Comprehensive Enhanced Strategy"""
    strategy = ComprehensiveEnhancedStrategy()
    
    print("🎯 Comprehensive Enhanced Strategy Created Successfully!")
    print("\n📊 Key Features:")
    print("• News Analysis Integration (30% weight)")
    print("• Indicators Analysis Integration (40% weight)")
    print("• Technical Analysis Integration (30% weight)")
    print("• Comprehensive Signal Generation")
    print("• Multi-factor Confidence Scoring")
    print("• Advanced Risk Management")
    print("• Real-time Market Analysis")

if __name__ == "__main__":
    main()
