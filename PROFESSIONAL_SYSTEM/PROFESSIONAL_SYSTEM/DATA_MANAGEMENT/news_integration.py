#!/usr/bin/env python3
"""
NEWS INTEGRATION MODULE
Integrates news/economic data with trading strategies for enhanced decision making
"""

import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import yaml

logger = logging.getLogger(__name__)

class NewsIntegration:
    """
    Integrates news/economic data with trading strategies
    """
    
    def __init__(self, news_path: str = "data/news"):
        """Initialize News Integration"""
        self.news_path = news_path
        self.linked_path = os.path.join(news_path, "linked")
        self.processed_path = os.path.join(news_path, "processed")
        
        # News impact weights
        self.impact_weights = {
            'high': 1.0,
            'medium': 0.6,
            'low': 0.3,
            'unknown': 0.1
        }
        
        # Category weights
        self.category_weights = {
            'inflation': 1.0,
            'monetary_policy': 1.0,
            'employment': 0.8,
            'economic_growth': 0.7,
            'trade': 0.6,
            'general': 0.3
        }
        
        # Time windows for news impact (in hours)
        self.impact_windows = {
            'high': 4,    # High impact news affects 4 hours
            'medium': 2,  # Medium impact news affects 2 hours
            'low': 1,     # Low impact news affects 1 hour
            'unknown': 0.5
        }
        
        logger.info("📰 News Integration initialized")
    
    def get_news_context(self, symbol: str, timestamp: datetime, lookback_hours: int = 24) -> Dict[str, Any]:
        """Get news context for a specific symbol and timestamp"""
        try:
            # Load linked news data
            linked_file = os.path.join(self.linked_path, f"{symbol}_1H_events.csv")
            if not os.path.exists(linked_file):
                return self._get_empty_news_context()
            
            news_data = pd.read_csv(linked_file)
            news_data['candle_timestamp_utc'] = pd.to_datetime(news_data['candle_timestamp_utc'])
            news_data['event_timestamp_utc'] = pd.to_datetime(news_data['event_timestamp_utc'])
            
            # Filter news within lookback period
            start_time = timestamp - timedelta(hours=lookback_hours)
            end_time = timestamp + timedelta(hours=1)  # Include current hour
            
            # Convert timestamps to timezone-naive for comparison
            news_data['event_timestamp_naive'] = news_data['event_timestamp_utc'].dt.tz_localize(None)
            start_time_naive = start_time.replace(tzinfo=None) if start_time.tzinfo else start_time
            end_time_naive = end_time.replace(tzinfo=None) if end_time.tzinfo else end_time
            
            recent_news = news_data[
                (news_data['event_timestamp_naive'] >= start_time_naive) & 
                (news_data['event_timestamp_naive'] <= end_time_naive)
            ].copy()
            
            if recent_news.empty:
                return self._get_empty_news_context()
            
            # Calculate news impact score
            impact_score = self._calculate_news_impact_score(recent_news)
            
            # Get upcoming events
            upcoming_events = self._get_upcoming_events(news_data, timestamp)
            
            # Analyze news sentiment
            sentiment_analysis = self._analyze_news_sentiment(recent_news)
            
            # Get news-based trading recommendations
            trading_recommendations = self._get_news_trading_recommendations(recent_news, upcoming_events)
            
            return {
                'has_recent_news': True,
                'news_count': len(recent_news),
                'impact_score': impact_score,
                'recent_events': recent_news.to_dict('records'),
                'upcoming_events': upcoming_events,
                'sentiment_analysis': sentiment_analysis,
                'trading_recommendations': trading_recommendations,
                'news_filter_active': impact_score > 0.5,  # High impact news
                'recommended_action': self._get_recommended_action(impact_score, sentiment_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error getting news context for {symbol}: {e}")
            return self._get_empty_news_context()
    
    def _get_empty_news_context(self) -> Dict[str, Any]:
        """Return empty news context when no news data available"""
        return {
            'has_recent_news': False,
            'news_count': 0,
            'impact_score': 0.0,
            'recent_events': [],
            'upcoming_events': [],
            'sentiment_analysis': {'overall_sentiment': 'neutral', 'sentiment_score': 0.0},
            'trading_recommendations': {'action': 'normal_trading', 'reason': 'No significant news'},
            'news_filter_active': False,
            'recommended_action': 'proceed'
        }
    
    def _calculate_news_impact_score(self, news_data: pd.DataFrame) -> float:
        """Calculate overall news impact score (0-1)"""
        try:
            if news_data.empty:
                return 0.0
            
            total_score = 0.0
            total_weight = 0.0
            
            for _, event in news_data.iterrows():
                impact_weight = self.impact_weights.get(event['impact'], 0.1)
                category_weight = self.category_weights.get(event['category'], 0.3)
                
                # Time decay factor (more recent news has higher impact)
                time_diff = datetime.now() - pd.to_datetime(event['event_timestamp_utc'])
                time_decay = max(0.1, 1.0 - (time_diff.total_seconds() / 3600) / 24)  # Decay over 24 hours
                
                event_score = impact_weight * category_weight * time_decay
                total_score += event_score
                total_weight += 1.0
            
            return min(1.0, total_score / max(1.0, total_weight))
            
        except Exception as e:
            logger.error(f"Error calculating news impact score: {e}")
            return 0.0
    
    def _get_upcoming_events(self, news_data: pd.DataFrame, current_time: datetime) -> List[Dict[str, Any]]:
        """Get upcoming high-impact events within next 24 hours"""
        try:
            future_time = current_time + timedelta(hours=24)
            
            # Convert timestamps for comparison
            news_data['event_timestamp_naive'] = news_data['event_timestamp_utc'].dt.tz_localize(None)
            current_time_naive = current_time.replace(tzinfo=None) if current_time.tzinfo else current_time
            future_time_naive = future_time.replace(tzinfo=None) if future_time.tzinfo else future_time
            
            upcoming = news_data[
                (news_data['event_timestamp_naive'] > current_time_naive) & 
                (news_data['event_timestamp_naive'] <= future_time_naive) &
                (news_data['impact'].isin(['high', 'medium']))
            ].copy()
            
            upcoming_events = []
            for _, event in upcoming.iterrows():
                upcoming_events.append({
                    'event_title': event['event_title'],
                    'event_timestamp': event['event_timestamp_utc'],
                    'impact': event['impact'],
                    'category': event['category'],
                    'hours_until': (pd.to_datetime(event['event_timestamp_utc']) - current_time).total_seconds() / 3600
                })
            
            return sorted(upcoming_events, key=lambda x: x['hours_until'])
            
        except Exception as e:
            logger.error(f"Error getting upcoming events: {e}")
            return []
    
    def _analyze_news_sentiment(self, news_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze overall sentiment from recent news"""
        try:
            if news_data.empty:
                return {'overall_sentiment': 'neutral', 'sentiment_score': 0.0}
            
            # Simple sentiment analysis based on keywords
            positive_keywords = ['positive', 'growth', 'increase', 'rise', 'strong', 'bullish', 'optimistic']
            negative_keywords = ['negative', 'decline', 'decrease', 'fall', 'weak', 'bearish', 'pessimistic']
            
            sentiment_scores = []
            for _, event in news_data.iterrows():
                text = (event['event_title'] + ' ' + event['event_description']).lower()
                
                positive_count = sum(1 for keyword in positive_keywords if keyword in text)
                negative_count = sum(1 for keyword in negative_keywords if keyword in text)
                
                if positive_count > negative_count:
                    sentiment_scores.append(1.0)
                elif negative_count > positive_count:
                    sentiment_scores.append(-1.0)
                else:
                    sentiment_scores.append(0.0)
            
            avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0.0
            
            if avg_sentiment > 0.2:
                overall_sentiment = 'positive'
            elif avg_sentiment < -0.2:
                overall_sentiment = 'negative'
            else:
                overall_sentiment = 'neutral'
            
            return {
                'overall_sentiment': overall_sentiment,
                'sentiment_score': avg_sentiment,
                'confidence': abs(avg_sentiment)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing news sentiment: {e}")
            return {'overall_sentiment': 'neutral', 'sentiment_score': 0.0}
    
    def _get_news_trading_recommendations(self, recent_news: pd.DataFrame, upcoming_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get trading recommendations based on news analysis"""
        try:
            if recent_news.empty and not upcoming_events:
                return {'action': 'normal_trading', 'reason': 'No significant news'}
            
            # Check for high-impact recent events
            high_impact_recent = recent_news[recent_news['impact'] == 'high']
            if not high_impact_recent.empty:
                return {
                    'action': 'reduce_risk',
                    'reason': f'High-impact news detected: {len(high_impact_recent)} events',
                    'details': high_impact_recent[['event_title', 'impact', 'category']].to_dict('records')
                }
            
            # Check for upcoming high-impact events
            upcoming_high_impact = [e for e in upcoming_events if e['impact'] == 'high']
            if upcoming_high_impact:
                next_event = upcoming_high_impact[0]
                if next_event['hours_until'] <= 2:  # Within 2 hours
                    return {
                        'action': 'prepare_for_volatility',
                        'reason': f'High-impact event in {next_event["hours_until"]:.1f} hours: {next_event["event_title"]}',
                        'details': upcoming_high_impact
                    }
            
            # Check for medium-impact events
            medium_impact_recent = recent_news[recent_news['impact'] == 'medium']
            if not medium_impact_recent.empty:
                return {
                    'action': 'monitor_closely',
                    'reason': f'Medium-impact news: {len(medium_impact_recent)} events',
                    'details': medium_impact_recent[['event_title', 'impact', 'category']].to_dict('records')
                }
            
            return {'action': 'normal_trading', 'reason': 'Low-impact news only'}
            
        except Exception as e:
            logger.error(f"Error getting news trading recommendations: {e}")
            return {'action': 'normal_trading', 'reason': 'Error analyzing news'}
    
    def _get_recommended_action(self, impact_score: float, sentiment_analysis: Dict[str, Any]) -> str:
        """Get recommended trading action based on news analysis"""
        try:
            if impact_score > 0.7:
                return 'avoid_trading'
            elif impact_score > 0.5:
                return 'reduce_position_size'
            elif impact_score > 0.3:
                return 'monitor_closely'
            else:
                return 'proceed'
                
        except Exception as e:
            logger.error(f"Error getting recommended action: {e}")
            return 'proceed'
    
    def should_filter_trade(self, symbol: str, timestamp: datetime, trade_direction: str) -> Tuple[bool, str]:
        """Determine if a trade should be filtered out based on news"""
        try:
            news_context = self.get_news_context(symbol, timestamp)
            
            if not news_context['has_recent_news']:
                return False, "No recent news"
            
            # High impact news - avoid trading
            if news_context['impact_score'] > 0.7:
                return True, f"High impact news detected (score: {news_context['impact_score']:.2f})"
            
            # Check for conflicting sentiment
            sentiment = news_context['sentiment_analysis']['overall_sentiment']
            if trade_direction == 'LONG' and sentiment == 'negative':
                return True, f"Negative news sentiment conflicts with long position"
            elif trade_direction == 'SHORT' and sentiment == 'positive':
                return True, f"Positive news sentiment conflicts with short position"
            
            # Check upcoming events
            upcoming_high_impact = [e for e in news_context['upcoming_events'] if e['impact'] == 'high']
            if upcoming_high_impact and upcoming_high_impact[0]['hours_until'] <= 1:
                return True, f"High-impact event within 1 hour: {upcoming_high_impact[0]['event_title']}"
            
            return False, "News analysis passed"
            
        except Exception as e:
            logger.error(f"Error filtering trade based on news: {e}")
            return False, "Error in news analysis"
    
    def get_news_enhanced_confidence(self, base_confidence: float, symbol: str, timestamp: datetime) -> float:
        """Enhance confidence score based on news alignment"""
        try:
            news_context = self.get_news_context(symbol, timestamp)
            
            if not news_context['has_recent_news']:
                return base_confidence
            
            # Adjust confidence based on news sentiment alignment
            sentiment_score = news_context['sentiment_analysis']['sentiment_score']
            impact_score = news_context['impact_score']
            
            # If news sentiment is strong and positive, boost confidence for long trades
            if sentiment_score > 0.3 and impact_score > 0.3:
                confidence_boost = min(0.2, sentiment_score * impact_score)
                return min(1.0, base_confidence + confidence_boost)
            
            # If news sentiment is strong and negative, reduce confidence for long trades
            elif sentiment_score < -0.3 and impact_score > 0.3:
                confidence_penalty = min(0.3, abs(sentiment_score) * impact_score)
                return max(0.0, base_confidence - confidence_penalty)
            
            return base_confidence
            
        except Exception as e:
            logger.error(f"Error enhancing confidence with news: {e}")
            return base_confidence
    
    def get_news_summary(self) -> Dict[str, Any]:
        """Get summary of available news data"""
        try:
            summary = {
                'available_symbols': [],
                'total_events': 0,
                'high_impact_events': 0,
                'medium_impact_events': 0,
                'low_impact_events': 0
            }
            
            if not os.path.exists(self.linked_path):
                return summary
            
            for file in os.listdir(self.linked_path):
                if file.endswith('_1H_events.csv'):
                    symbol = file.replace('_1H_events.csv', '')
                    file_path = os.path.join(self.linked_path, file)
                    
                    df = pd.read_csv(file_path)
                    summary['available_symbols'].append(symbol)
                    summary['total_events'] += len(df)
                    summary['high_impact_events'] += len(df[df['impact'] == 'high'])
                    summary['medium_impact_events'] += len(df[df['impact'] == 'medium'])
                    summary['low_impact_events'] += len(df[df['impact'] == 'low'])
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting news summary: {e}")
            return {}

def main():
    """Test the News Integration module"""
    news_integration = NewsIntegration()
    
    print("📰 News Integration Test")
    print("=" * 50)
    
    # Get news summary
    summary = news_integration.get_news_summary()
    print(f"Available symbols: {len(summary.get('available_symbols', []))}")
    print(f"Total events: {summary.get('total_events', 0)}")
    print(f"High impact: {summary.get('high_impact_events', 0)}")
    print(f"Medium impact: {summary.get('medium_impact_events', 0)}")
    print(f"Low impact: {summary.get('low_impact_events', 0)}")
    
    # Test news context for EUR_USD
    if 'EUR_USD' in summary.get('available_symbols', []):
        print("\n🔍 Testing news context for EUR_USD...")
        test_time = datetime(2025, 8, 12, 14, 0, 0)  # Sample time
        context = news_integration.get_news_context('EUR_USD', test_time)
        
        print(f"Has recent news: {context['has_recent_news']}")
        print(f"News count: {context['news_count']}")
        print(f"Impact score: {context['impact_score']:.2f}")
        print(f"Recommended action: {context['recommended_action']}")
        print(f"Trading recommendation: {context['trading_recommendations']['action']}")

if __name__ == "__main__":
    main()
