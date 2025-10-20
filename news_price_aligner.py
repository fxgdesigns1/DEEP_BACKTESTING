#!/usr/bin/env python3
"""
NEWS-PRICE ALIGNER
Organizes and aligns economic/news data with price candles for backtesting
"""

import pandas as pd
import numpy as np
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import yaml

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NewsPriceAligner:
    """
    Aligns economic/news data with price candles for backtesting
    """
    
    def __init__(self, base_path: str = "/Users/mac/SharedNetwork/quant_strategy_ai"):
        """Initialize News-Price Aligner"""
        self.base_path = base_path
        self.news_path = os.path.join(base_path, "data/historical/news")
        self.enhanced_news_path = os.path.join(base_path, "data/historical/enhanced_news")
        self.price_path = os.path.join(base_path, "deep_backtesting/data/historical/prices")
        
        # Create organized structure
        self.organized_path = os.path.join(base_path, "deep_backtesting/data/news")
        self.raw_path = os.path.join(self.organized_path, "raw")
        self.processed_path = os.path.join(self.organized_path, "processed")
        self.linked_path = os.path.join(self.organized_path, "linked")
        
        # Create directories
        for path in [self.organized_path, self.raw_path, self.processed_path, self.linked_path]:
            os.makedirs(path, exist_ok=True)
        
        # Symbol mapping
        self.symbol_mapping = {
            'EUR_USD': 'eur_usd',
            'GBP_USD': 'gbp_usd', 
            'USD_JPY': 'usd_jpy',
            'AUD_USD': 'aud_usd',
            'USD_CAD': 'usd_cad',
            'USD_CHF': 'usd_chf',
            'NZD_USD': 'nzd_usd',
            'XAU_USD': 'xau_usd',
            'EUR_JPY': 'eur_jpy',
            'GBP_JPY': 'gbp_jpy'
        }
        
        logger.info("🎯 News-Price Aligner initialized")
    
    def organize_news_data(self):
        """Organize existing news data into proper structure"""
        try:
            logger.info("📁 Organizing news data...")
            
            # Copy raw news files
            self._copy_raw_news_files()
            
            # Process and normalize news data
            self._process_news_data()
            
            # Align with price data
            self._align_news_with_prices()
            
            logger.info("✅ News data organization complete!")
            
        except Exception as e:
            logger.error(f"Error organizing news data: {e}")
    
    def _copy_raw_news_files(self):
        """Copy raw news files to organized structure"""
        try:
            # Copy basic news files
            for symbol in self.symbol_mapping.keys():
                news_file = os.path.join(self.news_path, f"{symbol.lower()}_news.json")
                if os.path.exists(news_file):
                    dest_file = os.path.join(self.raw_path, f"{symbol.lower()}_news.json")
                    with open(news_file, 'r') as src, open(dest_file, 'w') as dst:
                        dst.write(src.read())
                    logger.info(f"Copied {symbol} news file")
            
            # Copy enhanced news files
            for symbol in self.symbol_mapping.keys():
                enhanced_file = os.path.join(self.enhanced_news_path, f"{symbol.lower()}_enhanced_news.json")
                if os.path.exists(enhanced_file):
                    dest_file = os.path.join(self.raw_path, f"{symbol.lower()}_enhanced_news.json")
                    with open(enhanced_file, 'r') as src, open(dest_file, 'w') as dst:
                        dst.write(src.read())
                    logger.info(f"Copied {symbol} enhanced news file")
            
        except Exception as e:
            logger.error(f"Error copying raw news files: {e}")
    
    def _process_news_data(self):
        """Process and normalize news data"""
        try:
            logger.info("🔄 Processing news data...")
            
            for symbol in self.symbol_mapping.keys():
                # Process basic news
                basic_file = os.path.join(self.raw_path, f"{symbol.lower()}_news.json")
                if os.path.exists(basic_file):
                    self._process_basic_news(symbol, basic_file)
                
                # Process enhanced news
                enhanced_file = os.path.join(self.raw_path, f"{symbol.lower()}_enhanced_news.json")
                if os.path.exists(enhanced_file):
                    self._process_enhanced_news(symbol, enhanced_file)
            
        except Exception as e:
            logger.error(f"Error processing news data: {e}")
    
    def _process_basic_news(self, symbol: str, file_path: str):
        """Process basic news data"""
        try:
            with open(file_path, 'r') as f:
                news_data = json.load(f)
            
            processed_news = []
            for item in news_data:
                processed_item = {
                    'timestamp_utc': item.get('published_at', ''),
                    'title': item.get('title', ''),
                    'description': item.get('description', ''),
                    'source': item.get('source', ''),
                    'url': item.get('url', ''),
                    'sentiment': item.get('sentiment', 'neutral'),
                    'sentiment_score': item.get('sentiment_score', 0),
                    'symbol': symbol,
                    'data_source': item.get('data_source', 'marketaux'),
                    'impact': self._classify_impact(item.get('title', '') + ' ' + item.get('description', '')),
                    'category': self._classify_category(item.get('title', '') + ' ' + item.get('description', ''))
                }
                processed_news.append(processed_item)
            
            # Save processed data
            output_file = os.path.join(self.processed_path, f"{symbol.lower()}_processed_news.csv")
            df = pd.DataFrame(processed_news)
            df.to_csv(output_file, index=False)
            logger.info(f"Processed {len(processed_news)} news items for {symbol}")
            
        except Exception as e:
            logger.error(f"Error processing basic news for {symbol}: {e}")
    
    def _process_enhanced_news(self, symbol: str, file_path: str):
        """Process enhanced news data"""
        try:
            with open(file_path, 'r') as f:
                enhanced_data = json.load(f)
            
            processed_news = []
            market_news = enhanced_data.get('market_news', [])
            
            for item in market_news:
                processed_item = {
                    'timestamp_utc': item.get('published_at', ''),
                    'title': item.get('title', ''),
                    'description': item.get('description', ''),
                    'source': item.get('source', ''),
                    'url': item.get('url', ''),
                    'sentiment': 'neutral',  # Enhanced data doesn't have sentiment
                    'sentiment_score': item.get('sentiment_score', 0),
                    'symbol': symbol,
                    'data_source': item.get('data_source', 'marketaux'),
                    'impact': self._classify_impact(item.get('title', '') + ' ' + item.get('description', '')),
                    'category': self._classify_category(item.get('title', '') + ' ' + item.get('description', '')),
                    'entities': str(item.get('entities', [])),
                    'downloaded_at': item.get('downloaded_at', '')
                }
                processed_news.append(processed_item)
            
            # Save processed data
            output_file = os.path.join(self.processed_path, f"{symbol.lower()}_enhanced_processed_news.csv")
            df = pd.DataFrame(processed_news)
            df.to_csv(output_file, index=False)
            logger.info(f"Processed {len(processed_news)} enhanced news items for {symbol}")
            
        except Exception as e:
            logger.error(f"Error processing enhanced news for {symbol}: {e}")
    
    def _classify_impact(self, text: str) -> str:
        """Classify news impact based on content"""
        text_lower = text.lower()
        
        # High impact keywords
        high_impact = ['cpi', 'inflation', 'fed', 'interest rate', 'nfp', 'unemployment', 'gdp', 'fomc', 'rate cut', 'rate hike']
        medium_impact = ['retail sales', 'manufacturing', 'trade', 'deficit', 'surplus', 'pmi', 'consumer confidence']
        low_impact = ['speech', 'comment', 'forecast', 'outlook', 'analysis']
        
        if any(keyword in text_lower for keyword in high_impact):
            return 'high'
        elif any(keyword in text_lower for keyword in medium_impact):
            return 'medium'
        elif any(keyword in text_lower for keyword in low_impact):
            return 'low'
        else:
            return 'unknown'
    
    def _classify_category(self, text: str) -> str:
        """Classify news category"""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['cpi', 'inflation', 'price']):
            return 'inflation'
        elif any(keyword in text_lower for keyword in ['fed', 'interest rate', 'fomc']):
            return 'monetary_policy'
        elif any(keyword in text_lower for keyword in ['employment', 'unemployment', 'jobs', 'nfp']):
            return 'employment'
        elif any(keyword in text_lower for keyword in ['gdp', 'growth', 'recession']):
            return 'economic_growth'
        elif any(keyword in text_lower for keyword in ['trade', 'deficit', 'surplus']):
            return 'trade'
        else:
            return 'general'
    
    def _align_news_with_prices(self):
        """Align news events with price candles"""
        try:
            logger.info("🔗 Aligning news with price data...")
            
            for symbol in self.symbol_mapping.keys():
                # Load price data
                price_file = os.path.join(self.price_path, f"{symbol.lower()}_1h.csv")
                if not os.path.exists(price_file):
                    logger.warning(f"Price file not found for {symbol}")
                    continue
                
                price_data = pd.read_csv(price_file)
                price_data['timestamp'] = pd.to_datetime(price_data['timestamp'])
                
                # Load processed news data
                news_file = os.path.join(self.processed_path, f"{symbol.lower()}_processed_news.csv")
                enhanced_news_file = os.path.join(self.processed_path, f"{symbol.lower()}_enhanced_processed_news.csv")
                
                all_news = []
                if os.path.exists(news_file):
                    basic_news = pd.read_csv(news_file)
                    all_news.append(basic_news)
                
                if os.path.exists(enhanced_news_file):
                    enhanced_news = pd.read_csv(enhanced_news_file)
                    all_news.append(enhanced_news)
                
                if not all_news:
                    logger.warning(f"No news data found for {symbol}")
                    continue
                
                # Combine news data
                combined_news = pd.concat(all_news, ignore_index=True)
                combined_news['timestamp_utc'] = pd.to_datetime(combined_news['timestamp_utc'])
                
                # Align news with price candles
                aligned_data = self._align_events_with_candles(price_data, combined_news)
                
                # Save aligned data
                output_file = os.path.join(self.linked_path, f"{symbol}_1H_events.csv")
                aligned_data.to_csv(output_file, index=False)
                logger.info(f"Aligned {len(aligned_data)} news events with price data for {symbol}")
            
        except Exception as e:
            logger.error(f"Error aligning news with prices: {e}")
    
    def _align_events_with_candles(self, price_data: pd.DataFrame, news_data: pd.DataFrame) -> pd.DataFrame:
        """Align news events with price candles"""
        try:
            aligned_events = []
            
            for _, news_item in news_data.iterrows():
                event_time = news_item['timestamp_utc']
                
                # Find the closest candle (before or after the event)
                price_data['time_diff'] = abs(price_data['timestamp'] - event_time)
                closest_candle = price_data.loc[price_data['time_diff'].idxmin()]
                
                # Determine relationship
                candle_time = closest_candle['timestamp']
                time_diff_minutes = (event_time - candle_time).total_seconds() / 60
                
                if time_diff_minutes < 0:
                    relation = 'pre_event'
                elif time_diff_minutes <= 60:  # Within the same hour
                    relation = 'within_candle'
                else:
                    relation = 'post_event'
                
                aligned_event = {
                    'candle_timestamp_utc': candle_time,
                    'event_timestamp_utc': event_time,
                    'event_title': news_item['title'],
                    'event_description': news_item['description'],
                    'source': news_item['source'],
                    'impact': news_item['impact'],
                    'category': news_item['category'],
                    'sentiment': news_item['sentiment'],
                    'sentiment_score': news_item['sentiment_score'],
                    'relation': relation,
                    'minutes_from_event': time_diff_minutes,
                    'candle_open': closest_candle['open'],
                    'candle_high': closest_candle['high'],
                    'candle_low': closest_candle['low'],
                    'candle_close': closest_candle['close'],
                    'candle_volume': closest_candle['volume']
                }
                aligned_events.append(aligned_event)
            
            return pd.DataFrame(aligned_events)
            
        except Exception as e:
            logger.error(f"Error aligning events with candles: {e}")
            return pd.DataFrame()
    
    def get_news_summary(self) -> Dict[str, Any]:
        """Get summary of organized news data"""
        try:
            summary = {
                'total_symbols': len(self.symbol_mapping),
                'organized_path': self.organized_path,
                'symbols_processed': [],
                'total_events': 0
            }
            
            for symbol in self.symbol_mapping.keys():
                linked_file = os.path.join(self.linked_path, f"{symbol}_1H_events.csv")
                if os.path.exists(linked_file):
                    df = pd.read_csv(linked_file)
                    summary['symbols_processed'].append({
                        'symbol': symbol,
                        'events_count': len(df),
                        'high_impact_events': len(df[df['impact'] == 'high']),
                        'medium_impact_events': len(df[df['impact'] == 'medium']),
                        'low_impact_events': len(df[df['impact'] == 'low'])
                    })
                    summary['total_events'] += len(df)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting news summary: {e}")
            return {}

def main():
    """Main function to organize news data"""
    aligner = NewsPriceAligner()
    
    print("🎯 News-Price Aligner Starting...")
    print(f"📁 Base path: {aligner.base_path}")
    print(f"📁 Organized path: {aligner.organized_path}")
    
    # Organize news data
    aligner.organize_news_data()
    
    # Get summary
    summary = aligner.get_news_summary()
    
    print("\n📊 News Organization Summary:")
    print(f"• Total symbols: {summary.get('total_symbols', 0)}")
    print(f"• Total events: {summary.get('total_events', 0)}")
    print(f"• Symbols processed: {len(summary.get('symbols_processed', []))}")
    
    print("\n📈 Per-Symbol Breakdown:")
    for symbol_info in summary.get('symbols_processed', []):
        print(f"• {symbol_info['symbol']}: {symbol_info['events_count']} events "
              f"(High: {symbol_info['high_impact_events']}, "
              f"Medium: {symbol_info['medium_impact_events']}, "
              f"Low: {symbol_info['low_impact_events']})")
    
    print(f"\n✅ News data organized in: {aligner.organized_path}")
    print("📁 Structure:")
    print("  • raw/ - Original news files")
    print("  • processed/ - Normalized news data")
    print("  • linked/ - News aligned with price candles")

if __name__ == "__main__":
    main()
