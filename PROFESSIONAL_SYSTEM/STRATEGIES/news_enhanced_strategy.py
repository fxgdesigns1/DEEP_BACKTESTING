#!/usr/bin/env python3
"""
NEWS-ENHANCED STRATEGY
Strategy that integrates news/economic data for enhanced decision making
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

logger = logging.getLogger(__name__)

class NewsEnhancedStrategy:
    """
    Strategy that integrates news/economic data for enhanced decision making
    """
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize News-Enhanced Strategy"""
        self.logger = logger
        
        # Initialize news integration
        self.news_integration = NewsIntegration()
        
        # Strategy parameters
        self.min_rr_ratio = 2.0
        self.min_confidence = 70
        self.min_volume_multiplier = 1.5
        self.min_atr_multiplier = 1.2
        self.max_daily_trades = 3
        self.min_pips_threshold = 10
        
        # News-specific parameters
        self.news_impact_threshold = 0.5  # Minimum news impact to consider
        self.news_confidence_boost = 0.1   # Confidence boost from positive news
        self.news_confidence_penalty = 0.2 # Confidence penalty from negative news
        
        # Performance tracking
        self.daily_trades = {}
        self.trade_history = []
        
        self.logger.info("📰 News-Enhanced Strategy initialized")
    
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
    
    def check_news_enhanced_conditions(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Check conditions with news integration"""
        try:
            if len(data) < 50:
                return {'qualified': False, 'reason': 'Insufficient data'}
            
            current = data.iloc[-1]
            current_time = datetime.now()
            
            # Get news context
            news_context = self.news_integration.get_news_context(symbol, current_time)
            
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
            
            # 3. News-based filtering
            if news_context['has_recent_news']:
                # Check if news should filter out the trade
                should_filter, filter_reason = self.news_integration.should_filter_trade(
                    symbol, current_time, 'LONG'  # We'll determine direction later
                )
                
                if should_filter:
                    return {'qualified': False, 'reason': f'News filter: {filter_reason}'}
            
            # 4. Technical alignment check
            alignment_score = self._calculate_technical_alignment(data)
            
            # 5. News-enhanced confidence
            news_enhanced_confidence = self.news_integration.get_news_enhanced_confidence(
                alignment_score, symbol, current_time
            )
            
            if news_enhanced_confidence < self.min_confidence:
                return {'qualified': False, 'reason': f'Low confidence ({news_enhanced_confidence:.1f}%)'}
            
            # 6. Risk-Reward check
            rr_ratio = self._calculate_potential_rr(data)
            if rr_ratio < self.min_rr_ratio:
                return {'qualified': False, 'reason': f'Insufficient RR ratio ({rr_ratio:.1f})'}
            
            # 7. Minimum pips check
            potential_pips = self._calculate_potential_pips(data)
            if potential_pips < self.min_pips_threshold:
                return {'qualified': False, 'reason': f'Insufficient potential pips ({potential_pips:.1f})'}
            
            return {
                'qualified': True,
                'confidence': news_enhanced_confidence,
                'base_confidence': alignment_score,
                'news_boost': news_enhanced_confidence - alignment_score,
                'rr_ratio': rr_ratio,
                'potential_pips': potential_pips,
                'volume_ratio': current['Volume_Ratio'],
                'atr_ratio': current['ATR'] / avg_atr,
                'news_context': news_context
            }
            
        except Exception as e:
            self.logger.error(f"Error checking news-enhanced conditions: {e}")
            return {'qualified': False, 'reason': f'Error: {str(e)}'}
    
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
            elif current['close'] > current['SMA_20'] or current['close'] < current['SMA_20']:
                score += 10
            total_checks += 1
            
            # MACD alignment
            if current['MACD'] > current['MACD_Signal'] and current['MACD_Histogram'] > 0:
                score += 15
            elif current['MACD'] < current['MACD_Signal'] and current['MACD_Histogram'] < 0:
                score += 15
            elif current['MACD'] > current['MACD_Signal'] or current['MACD'] < current['MACD_Signal']:
                score += 8
            total_checks += 1
            
            # RSI alignment
            if 25 <= current['RSI'] <= 75:
                score += 15
            elif 20 <= current['RSI'] <= 80:
                score += 10
            total_checks += 1
            
            # Bollinger Bands alignment
            if current['close'] > current['BB_Upper'] or current['close'] < current['BB_Lower']:
                score += 10
            elif current['close'] > current['BB_Middle'] or current['close'] < current['BB_Middle']:
                score += 5
            total_checks += 1
            
            # Volume confirmation
            if current['Volume_Ratio'] > 1.2:
                score += 10
            elif current['Volume_Ratio'] > 1.0:
                score += 5
            total_checks += 1
            
            # ATR volatility
            avg_atr = data['ATR'].rolling(20).mean().iloc[-1]
            if current['ATR'] > avg_atr * 1.1:
                score += 10
            elif current['ATR'] > avg_atr:
                score += 5
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
        """Generate trading signal with news integration"""
        try:
            # Calculate indicators
            data = self.calculate_technical_indicators(data)
            
            # Check news-enhanced conditions
            conditions = self.check_news_enhanced_conditions(data, symbol)
            
            if not conditions['qualified']:
                return {
                    'signal': 'NO_SIGNAL',
                    'reason': conditions['reason'],
                    'confidence': 0,
                    'timestamp': datetime.now().isoformat(),
                    'strategy': 'News-Enhanced Strategy'
                }
            
            # Determine signal direction
            signal_direction = self._determine_signal_direction(data, conditions['news_context'])
            
            if signal_direction == 'NEUTRAL':
                return {
                    'signal': 'NO_SIGNAL',
                    'reason': 'No clear direction',
                    'confidence': 0,
                    'timestamp': datetime.now().isoformat(),
                    'strategy': 'News-Enhanced Strategy'
                }
            
            # Update daily trade count
            today = datetime.now().strftime('%Y-%m-%d')
            self.daily_trades[symbol][today] += 1
            
            # Create comprehensive signal
            signal = {
                'signal': signal_direction,
                'symbol': symbol,
                'strategy': 'News-Enhanced Strategy',
                'confidence': conditions['confidence'],
                'base_confidence': conditions['base_confidence'],
                'news_boost': conditions['news_boost'],
                'rr_ratio': conditions['rr_ratio'],
                'potential_pips': conditions['potential_pips'],
                'volume_ratio': conditions['volume_ratio'],
                'atr_ratio': conditions['atr_ratio'],
                'timestamp': datetime.now().isoformat(),
                'entry_price': data['close'].iloc[-1],
                'stop_loss': self._calculate_stop_loss(data, signal_direction),
                'take_profit': self._calculate_take_profit(data, signal_direction),
                'news_context': conditions['news_context']
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
                'strategy': 'News-Enhanced Strategy'
            }
    
    def _determine_signal_direction(self, data: pd.DataFrame, news_context: Dict[str, Any]) -> str:
        """Determine signal direction with news consideration"""
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
            elif current['close'] > current['SMA_20']:
                bullish_count += 1
            elif current['close'] < current['SMA_20']:
                bearish_count += 1
            
            # MACD
            if current['MACD'] > current['MACD_Signal'] and current['MACD_Histogram'] > 0:
                bullish_count += 1
            elif current['MACD'] < current['MACD_Signal'] and current['MACD_Histogram'] < 0:
                bearish_count += 1
            elif current['MACD'] > current['MACD_Signal']:
                bullish_count += 0.5
            elif current['MACD'] < current['MACD_Signal']:
                bearish_count += 0.5
            
            # RSI
            if current['RSI'] < 35:
                bullish_count += 1
            elif current['RSI'] > 65:
                bearish_count += 1
            elif current['RSI'] < 45:
                bullish_count += 0.5
            elif current['RSI'] > 55:
                bearish_count += 0.5
            
            # Bollinger Bands
            if current['close'] < current['BB_Lower']:
                bullish_count += 1
            elif current['close'] > current['BB_Upper']:
                bearish_count += 1
            elif current['close'] < current['BB_Middle']:
                bullish_count += 0.5
            elif current['close'] > current['BB_Middle']:
                bearish_count += 0.5
            
            # News sentiment adjustment
            if news_context['has_recent_news']:
                sentiment = news_context['sentiment_analysis']['overall_sentiment']
                sentiment_score = news_context['sentiment_analysis']['sentiment_score']
                
                if sentiment == 'positive' and sentiment_score > 0.3:
                    bullish_count += 1
                elif sentiment == 'negative' and sentiment_score < -0.3:
                    bearish_count += 1
            
            # Determine direction
            if bullish_count > bearish_count + 0.5:
                return 'LONG'
            elif bearish_count > bullish_count + 0.5:
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
            avg_news_boost = np.mean([t.get('news_boost', 0) for t in self.trade_history])
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'avg_confidence': avg_confidence,
                'avg_rr_ratio': avg_rr,
                'avg_news_boost': avg_news_boost,
                'strategy': 'News-Enhanced Strategy'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return {'error': str(e)}

def main():
    """Main function to test News-Enhanced Strategy"""
    strategy = NewsEnhancedStrategy()
    
    print("📰 News-Enhanced Strategy Created Successfully!")
    print("\n📊 Key Features:")
    print("• News Impact Analysis")
    print("• Sentiment-Based Confidence Adjustment")
    print("• Economic Event Filtering")
    print("• Upcoming Event Awareness")
    print("• Minimum 1:2 Risk-Reward Ratio")
    print("• Minimum 70% Confidence Score")
    print("• Maximum 3 Trades Per Day Per Pair")
    print("• News-Enhanced Signal Generation")

if __name__ == "__main__":
    main()
