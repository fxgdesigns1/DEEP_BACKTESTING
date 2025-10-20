#!/usr/bin/env python3
"""
INDICATORS INTEGRATION MODULE
Integrates comprehensive financial indicators with trading strategies
"""

import pandas as pd
import numpy as np
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import ast

logger = logging.getLogger(__name__)

class IndicatorsIntegration:
    """
    Integrates comprehensive financial indicators with trading strategies
    """
    
    def __init__(self, indicators_path: str = "/Users/mac/SharedNetwork/quant_strategy_ai/data/analysis/technical"):
        """Initialize Indicators Integration"""
        self.indicators_path = indicators_path
        
        # Indicator categories and their weights
        self.indicator_weights = {
            'trend': {
                'sma_20': 0.15,
                'sma_50': 0.15,
                'ema_20': 0.15,
                'ema_50': 0.15,
                'macd': 0.20,
                'macd_signal': 0.20
            },
            'momentum': {
                'rsi': 0.30,
                'stoch_k': 0.25,
                'stoch_d': 0.25,
                'cci': 0.20
            },
            'volatility': {
                'bb_upper': 0.25,
                'bb_middle': 0.25,
                'bb_lower': 0.25,
                'atr': 0.25
            }
        }
        
        # Indicator thresholds
        self.thresholds = {
            'rsi': {'oversold': 30, 'overbought': 70},
            'stoch_k': {'oversold': 20, 'overbought': 80},
            'stoch_d': {'oversold': 20, 'overbought': 80},
            'cci': {'oversold': -100, 'overbought': 100},
            'macd': {'bullish': 0, 'bearish': 0}
        }
        
        logger.info("📊 Indicators Integration initialized")
    
    def load_indicators(self, symbol: str) -> Dict[str, Any]:
        """Load indicators data for a specific symbol"""
        try:
            indicators_file = os.path.join(self.indicators_path, f"{symbol.lower()}_indicators.json")
            
            if not os.path.exists(indicators_file):
                logger.warning(f"Indicators file not found for {symbol}")
                return {}
            
            with open(indicators_file, 'r') as f:
                indicators_data = json.load(f)
            
            # Parse the string representations back to arrays
            parsed_indicators = {}
            for category, indicators in indicators_data.items():
                parsed_indicators[category] = {}
                for indicator_name, indicator_values in indicators.items():
                    if isinstance(indicator_values, str) and indicator_values.startswith('['):
                        try:
                            # Parse numpy array string representation
                            parsed_indicators[category][indicator_name] = np.array(ast.literal_eval(indicator_values))
                        except:
                            # If parsing fails, keep as string
                            parsed_indicators[category][indicator_name] = indicator_values
                    else:
                        parsed_indicators[category][indicator_name] = indicator_values
            
            return parsed_indicators
            
        except Exception as e:
            logger.error(f"Error loading indicators for {symbol}: {e}")
            return {}
    
    def get_current_indicators(self, symbol: str) -> Dict[str, Any]:
        """Get current indicator values for a symbol"""
        try:
            indicators = self.load_indicators(symbol)
            if not indicators:
                return {}
            
            current_indicators = {}
            
            # Extract current values (last non-NaN values)
            for category, category_indicators in indicators.items():
                current_indicators[category] = {}
                for indicator_name, indicator_values in category_indicators.items():
                    if isinstance(indicator_values, np.ndarray):
                        # Get last non-NaN value
                        valid_values = indicator_values[~np.isnan(indicator_values)]
                        if len(valid_values) > 0:
                            current_indicators[category][indicator_name] = float(valid_values[-1])
                        else:
                            current_indicators[category][indicator_name] = None
                    else:
                        current_indicators[category][indicator_name] = indicator_values
            
            return current_indicators
            
        except Exception as e:
            logger.error(f"Error getting current indicators for {symbol}: {e}")
            return {}
    
    def analyze_trend_strength(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trend strength based on multiple indicators"""
        try:
            trend_analysis = {
                'strength': 'unknown',
                'direction': 'neutral',
                'confidence': 0.0,
                'signals': []
            }
            
            if 'trend' not in indicators:
                return trend_analysis
            
            trend_indicators = indicators['trend']
            bullish_signals = 0
            bearish_signals = 0
            total_signals = 0
            
            # SMA Analysis
            if 'sma_20' in trend_indicators and 'sma_50' in trend_indicators:
                sma_20 = trend_indicators['sma_20']
                sma_50 = trend_indicators['sma_50']
                if sma_20 is not None and sma_50 is not None:
                    if sma_20 > sma_50:
                        bullish_signals += 1
                        trend_analysis['signals'].append('SMA 20 > SMA 50 (Bullish)')
                    else:
                        bearish_signals += 1
                        trend_analysis['signals'].append('SMA 20 < SMA 50 (Bearish)')
                    total_signals += 1
            
            # EMA Analysis
            if 'ema_20' in trend_indicators and 'ema_50' in trend_indicators:
                ema_20 = trend_indicators['ema_20']
                ema_50 = trend_indicators['ema_50']
                if ema_20 is not None and ema_50 is not None:
                    if ema_20 > ema_50:
                        bullish_signals += 1
                        trend_analysis['signals'].append('EMA 20 > EMA 50 (Bullish)')
                    else:
                        bearish_signals += 1
                        trend_analysis['signals'].append('EMA 20 < EMA 50 (Bearish)')
                    total_signals += 1
            
            # MACD Analysis
            if 'macd' in trend_indicators and 'macd_signal' in trend_indicators:
                macd = trend_indicators['macd']
                macd_signal = trend_indicators['macd_signal']
                if macd is not None and macd_signal is not None:
                    if macd > macd_signal:
                        bullish_signals += 1
                        trend_analysis['signals'].append('MACD > Signal (Bullish)')
                    else:
                        bearish_signals += 1
                        trend_analysis['signals'].append('MACD < Signal (Bearish)')
                    total_signals += 1
            
            # Determine trend direction and strength
            if total_signals > 0:
                bullish_ratio = bullish_signals / total_signals
                bearish_ratio = bearish_signals / total_signals
                
                if bullish_ratio > 0.6:
                    trend_analysis['direction'] = 'bullish'
                    trend_analysis['strength'] = 'strong' if bullish_ratio > 0.8 else 'moderate'
                elif bearish_ratio > 0.6:
                    trend_analysis['direction'] = 'bearish'
                    trend_analysis['strength'] = 'strong' if bearish_ratio > 0.8 else 'moderate'
                else:
                    trend_analysis['direction'] = 'neutral'
                    trend_analysis['strength'] = 'weak'
                
                trend_analysis['confidence'] = max(bullish_ratio, bearish_ratio)
            
            return trend_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing trend strength: {e}")
            return {'strength': 'unknown', 'direction': 'neutral', 'confidence': 0.0, 'signals': []}
    
    def analyze_momentum(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze momentum based on momentum indicators"""
        try:
            momentum_analysis = {
                'strength': 'unknown',
                'direction': 'neutral',
                'confidence': 0.0,
                'signals': [],
                'overbought_oversold': 'neutral'
            }
            
            if 'momentum' not in indicators:
                return momentum_analysis
            
            momentum_indicators = indicators['momentum']
            bullish_signals = 0
            bearish_signals = 0
            total_signals = 0
            overbought_count = 0
            oversold_count = 0
            
            # RSI Analysis
            if 'rsi' in momentum_indicators:
                rsi = momentum_indicators['rsi']
                if rsi is not None:
                    if rsi < self.thresholds['rsi']['oversold']:
                        bullish_signals += 1
                        oversold_count += 1
                        momentum_analysis['signals'].append(f'RSI Oversold ({rsi:.1f})')
                    elif rsi > self.thresholds['rsi']['overbought']:
                        bearish_signals += 1
                        overbought_count += 1
                        momentum_analysis['signals'].append(f'RSI Overbought ({rsi:.1f})')
                    elif 40 <= rsi <= 60:
                        momentum_analysis['signals'].append(f'RSI Neutral ({rsi:.1f})')
                    total_signals += 1
            
            # Stochastic Analysis
            if 'stoch_k' in momentum_indicators and 'stoch_d' in momentum_indicators:
                stoch_k = momentum_indicators['stoch_k']
                stoch_d = momentum_indicators['stoch_d']
                if stoch_k is not None and stoch_d is not None:
                    if stoch_k < self.thresholds['stoch_k']['oversold'] and stoch_d < self.thresholds['stoch_d']['oversold']:
                        bullish_signals += 1
                        oversold_count += 1
                        momentum_analysis['signals'].append(f'Stochastic Oversold (K:{stoch_k:.1f}, D:{stoch_d:.1f})')
                    elif stoch_k > self.thresholds['stoch_k']['overbought'] and stoch_d > self.thresholds['stoch_d']['overbought']:
                        bearish_signals += 1
                        overbought_count += 1
                        momentum_analysis['signals'].append(f'Stochastic Overbought (K:{stoch_k:.1f}, D:{stoch_d:.1f})')
                    elif stoch_k > stoch_d:
                        bullish_signals += 0.5
                        momentum_analysis['signals'].append('Stochastic K > D (Bullish)')
                    else:
                        bearish_signals += 0.5
                        momentum_analysis['signals'].append('Stochastic K < D (Bearish)')
                    total_signals += 1
            
            # CCI Analysis
            if 'cci' in momentum_indicators:
                cci = momentum_indicators['cci']
                if cci is not None:
                    if cci < self.thresholds['cci']['oversold']:
                        bullish_signals += 1
                        oversold_count += 1
                        momentum_analysis['signals'].append(f'CCI Oversold ({cci:.1f})')
                    elif cci > self.thresholds['cci']['overbought']:
                        bearish_signals += 1
                        overbought_count += 1
                        momentum_analysis['signals'].append(f'CCI Overbought ({cci:.1f})')
                    total_signals += 1
            
            # Determine momentum direction and strength
            if total_signals > 0:
                bullish_ratio = bullish_signals / total_signals
                bearish_ratio = bearish_signals / total_signals
                
                if bullish_ratio > 0.6:
                    momentum_analysis['direction'] = 'bullish'
                    momentum_analysis['strength'] = 'strong' if bullish_ratio > 0.8 else 'moderate'
                elif bearish_ratio > 0.6:
                    momentum_analysis['direction'] = 'bearish'
                    momentum_analysis['strength'] = 'strong' if bearish_ratio > 0.8 else 'moderate'
                else:
                    momentum_analysis['direction'] = 'neutral'
                    momentum_analysis['strength'] = 'weak'
                
                momentum_analysis['confidence'] = max(bullish_ratio, bearish_ratio)
            
            # Determine overbought/oversold condition
            if overbought_count > oversold_count:
                momentum_analysis['overbought_oversold'] = 'overbought'
            elif oversold_count > overbought_count:
                momentum_analysis['overbought_oversold'] = 'oversold'
            
            return momentum_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing momentum: {e}")
            return {'strength': 'unknown', 'direction': 'neutral', 'confidence': 0.0, 'signals': [], 'overbought_oversold': 'neutral'}
    
    def analyze_volatility(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze volatility based on volatility indicators"""
        try:
            volatility_analysis = {
                'level': 'unknown',
                'trend': 'stable',
                'confidence': 0.0,
                'signals': []
            }
            
            if 'volatility' not in indicators:
                return volatility_analysis
            
            volatility_indicators = indicators['volatility']
            
            # Bollinger Bands Analysis
            if all(key in volatility_indicators for key in ['bb_upper', 'bb_middle', 'bb_lower']):
                bb_upper = volatility_indicators['bb_upper']
                bb_middle = volatility_indicators['bb_middle']
                bb_lower = volatility_indicators['bb_lower']
                
                if all(val is not None for val in [bb_upper, bb_middle, bb_lower]):
                    bb_width = bb_upper - bb_lower
                    bb_percentage = (bb_width / bb_middle) * 100
                    
                    if bb_percentage > 2.0:
                        volatility_analysis['level'] = 'high'
                        volatility_analysis['signals'].append(f'High Volatility (BB Width: {bb_percentage:.2f}%)')
                    elif bb_percentage < 1.0:
                        volatility_analysis['level'] = 'low'
                        volatility_analysis['signals'].append(f'Low Volatility (BB Width: {bb_percentage:.2f}%)')
                    else:
                        volatility_analysis['level'] = 'normal'
                        volatility_analysis['signals'].append(f'Normal Volatility (BB Width: {bb_percentage:.2f}%)')
            
            # ATR Analysis
            if 'atr' in volatility_indicators:
                atr = volatility_indicators['atr']
                if atr is not None:
                    # ATR analysis would need historical comparison
                    volatility_analysis['signals'].append(f'ATR: {atr:.5f}')
            
            return volatility_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing volatility: {e}")
            return {'level': 'unknown', 'trend': 'stable', 'confidence': 0.0, 'signals': []}
    
    def get_comprehensive_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive technical analysis for a symbol"""
        try:
            indicators = self.get_current_indicators(symbol)
            if not indicators:
                return {'error': 'No indicators available'}
            
            # Perform individual analyses
            trend_analysis = self.analyze_trend_strength(indicators)
            momentum_analysis = self.analyze_momentum(indicators)
            volatility_analysis = self.analyze_volatility(indicators)
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(trend_analysis, momentum_analysis, volatility_analysis)
            
            # Determine trading recommendation
            recommendation = self._get_trading_recommendation(trend_analysis, momentum_analysis, volatility_analysis, overall_score)
            
            return {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'trend_analysis': trend_analysis,
                'momentum_analysis': momentum_analysis,
                'volatility_analysis': volatility_analysis,
                'overall_score': overall_score,
                'recommendation': recommendation,
                'raw_indicators': indicators
            }
            
        except Exception as e:
            logger.error(f"Error getting comprehensive analysis for {symbol}: {e}")
            return {'error': str(e)}
    
    def _calculate_overall_score(self, trend_analysis: Dict[str, Any], momentum_analysis: Dict[str, Any], volatility_analysis: Dict[str, Any]) -> float:
        """Calculate overall technical analysis score (0-100)"""
        try:
            score = 0.0
            
            # Trend contribution (40%)
            if trend_analysis['direction'] == 'bullish':
                score += 40 * trend_analysis['confidence']
            elif trend_analysis['direction'] == 'bearish':
                score += 40 * (1 - trend_analysis['confidence'])
            else:
                score += 20  # Neutral trend
            
            # Momentum contribution (35%)
            if momentum_analysis['direction'] == 'bullish':
                score += 35 * momentum_analysis['confidence']
            elif momentum_analysis['direction'] == 'bearish':
                score += 35 * (1 - momentum_analysis['confidence'])
            else:
                score += 17.5  # Neutral momentum
            
            # Volatility contribution (25%)
            if volatility_analysis['level'] == 'normal':
                score += 25
            elif volatility_analysis['level'] == 'high':
                score += 15  # High volatility reduces score
            elif volatility_analysis['level'] == 'low':
                score += 20  # Low volatility slightly reduces score
            
            return min(100.0, max(0.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 50.0
    
    def _get_trading_recommendation(self, trend_analysis: Dict[str, Any], momentum_analysis: Dict[str, Any], volatility_analysis: Dict[str, Any], overall_score: float) -> Dict[str, Any]:
        """Get trading recommendation based on analysis"""
        try:
            recommendation = {
                'action': 'hold',
                'confidence': 0.0,
                'reasoning': [],
                'risk_level': 'medium'
            }
            
            # Determine action based on overall score
            if overall_score > 75:
                recommendation['action'] = 'strong_buy'
                recommendation['confidence'] = overall_score / 100
                recommendation['reasoning'].append('Strong bullish signals across all indicators')
            elif overall_score > 60:
                recommendation['action'] = 'buy'
                recommendation['confidence'] = overall_score / 100
                recommendation['reasoning'].append('Bullish signals with good confidence')
            elif overall_score < 25:
                recommendation['action'] = 'strong_sell'
                recommendation['confidence'] = (100 - overall_score) / 100
                recommendation['reasoning'].append('Strong bearish signals across all indicators')
            elif overall_score < 40:
                recommendation['action'] = 'sell'
                recommendation['confidence'] = (100 - overall_score) / 100
                recommendation['reasoning'].append('Bearish signals with good confidence')
            else:
                recommendation['action'] = 'hold'
                recommendation['confidence'] = 0.5
                recommendation['reasoning'].append('Mixed signals, wait for clearer direction')
            
            # Adjust for volatility
            if volatility_analysis['level'] == 'high':
                recommendation['risk_level'] = 'high'
                recommendation['reasoning'].append('High volatility increases risk')
            elif volatility_analysis['level'] == 'low':
                recommendation['risk_level'] = 'low'
                recommendation['reasoning'].append('Low volatility reduces risk')
            
            # Adjust for overbought/oversold conditions
            if momentum_analysis['overbought_oversold'] == 'overbought':
                if recommendation['action'] in ['buy', 'strong_buy']:
                    recommendation['action'] = 'hold'
                    recommendation['reasoning'].append('Overbought conditions suggest caution for long positions')
            elif momentum_analysis['overbought_oversold'] == 'oversold':
                if recommendation['action'] in ['sell', 'strong_sell']:
                    recommendation['action'] = 'hold'
                    recommendation['reasoning'].append('Oversold conditions suggest caution for short positions')
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error getting trading recommendation: {e}")
            return {'action': 'hold', 'confidence': 0.0, 'reasoning': ['Error in analysis'], 'risk_level': 'high'}
    
    def get_indicators_summary(self) -> Dict[str, Any]:
        """Get summary of available indicators data"""
        try:
            summary = {
                'available_symbols': [],
                'total_indicators': 0,
                'indicator_categories': ['trend', 'momentum', 'volatility']
            }
            
            if not os.path.exists(self.indicators_path):
                return summary
            
            for file in os.listdir(self.indicators_path):
                if file.endswith('_indicators.json'):
                    symbol = file.replace('_indicators.json', '').upper()
                    summary['available_symbols'].append(symbol)
            
            summary['total_indicators'] = len(summary['available_symbols'])
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting indicators summary: {e}")
            return {}

def main():
    """Test the Indicators Integration module"""
    indicators_integration = IndicatorsIntegration()
    
    print("📊 Indicators Integration Test")
    print("=" * 50)
    
    # Get indicators summary
    summary = indicators_integration.get_indicators_summary()
    print(f"Available symbols: {len(summary.get('available_symbols', []))}")
    print(f"Symbols: {', '.join(summary.get('available_symbols', []))}")
    
    # Test comprehensive analysis for EUR_USD
    if 'EUR_USD' in summary.get('available_symbols', []):
        print("\n🔍 Testing comprehensive analysis for EUR_USD...")
        analysis = indicators_integration.get_comprehensive_analysis('EUR_USD')
        
        if 'error' not in analysis:
            print(f"Overall Score: {analysis['overall_score']:.1f}")
            print(f"Recommendation: {analysis['recommendation']['action']}")
            print(f"Confidence: {analysis['recommendation']['confidence']:.2f}")
            print(f"Risk Level: {analysis['recommendation']['risk_level']}")
            print(f"Trend: {analysis['trend_analysis']['direction']} ({analysis['trend_analysis']['strength']})")
            print(f"Momentum: {analysis['momentum_analysis']['direction']} ({analysis['momentum_analysis']['strength']})")
            print(f"Volatility: {analysis['volatility_analysis']['level']}")
        else:
            print(f"Error: {analysis['error']}")

if __name__ == "__main__":
    main()
