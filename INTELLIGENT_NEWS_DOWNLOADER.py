#!/usr/bin/env python3
"""
INTELLIGENT NEWS DOWNLOADER
===========================

Advanced news and economic data downloader with intelligent caching,
incremental updates, and smart re-download prevention.

Features:
- Timestamp-based caching
- Incremental updates
- API response caching
- Smart skip logic
- Comprehensive logging
- Rate limit handling
"""

import requests
import json
import yaml
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import logging
import hashlib
import time
from pathlib import Path
import pickle

# Setup enhanced logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('intelligent_downloader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IntelligentDownloader:
    """Intelligent data downloader with caching and incremental updates"""
    
    def __init__(self):
        self.cache_dir = Path('data/cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.config = self.load_config()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'IntelligentDownloader/1.0'})
        
        # Cache settings
        self.cache_duration = {
            'economic_data': timedelta(hours=6),    # Economic data every 6 hours
            'market_data': timedelta(hours=1),      # Market data every hour
            'news_data': timedelta(minutes=30),     # News every 30 minutes
            'api_responses': timedelta(hours=24)    # API responses for 24 hours
        }
        
        logger.info("🚀 Intelligent Downloader initialized")
    
    def load_config(self):
        """Load configuration with error handling"""
        try:
            with open('config/settings.yaml', 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"⚠️ Config load failed, using defaults: {e}")
            return {
                'data_sources': {
                    'api_keys': {
                        'alphavantage': {'api_key': 'demo'},
                        'newsdata': {'api_key': 'demo'}
                    }
                }
            }
    
    def get_cache_key(self, source, endpoint, params=None):
        """Generate cache key for API calls"""
        key_string = f"{source}_{endpoint}_{str(params) if params else ''}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def is_cache_valid(self, cache_file, cache_type):
        """Check if cached data is still valid"""
        if not cache_file.exists():
            return False
        
        cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        max_age = self.cache_duration.get(cache_type, timedelta(hours=1))
        
        return cache_age < max_age
    
    def load_from_cache(self, cache_file):
        """Load data from cache"""
        try:
            if cache_file.suffix == '.json':
                with open(cache_file, 'r') as f:
                    return json.load(f)
            elif cache_file.suffix == '.pkl':
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            logger.warning(f"⚠️ Cache load failed: {e}")
        return None
    
    def save_to_cache(self, data, cache_file):
        """Save data to cache"""
        try:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            if cache_file.suffix == '.json':
                with open(cache_file, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            elif cache_file.suffix == '.pkl':
                with open(cache_file, 'wb') as f:
                    pickle.dump(data, f)
        except Exception as e:
            logger.warning(f"⚠️ Cache save failed: {e}")
    
    def make_api_request(self, url, params, cache_type='api_responses', timeout=10):
        """Make API request with intelligent caching"""
        cache_key = self.get_cache_key(url, params)
        cache_file = self.cache_dir / f"{cache_type}_{cache_key}.json"
        
        # Check cache first
        if self.is_cache_valid(cache_file, cache_type):
            logger.info(f"📋 Using cached data for {url}")
            return self.load_from_cache(cache_file)
        
        try:
            logger.info(f"🌐 Making API request to {url}")
            response = self.session.get(url, params=params, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                self.save_to_cache(data, cache_file)
                return data
            else:
                logger.warning(f"⚠️ API error {response.status_code} for {url}")
                return None
                
        except Exception as e:
            logger.error(f"❌ API request failed: {e}")
            return None
    
    def download_fred_data(self):
        """Download FRED economic data with intelligent caching"""
        logger.info("📊 Downloading FRED economic data...")
        
        fred_key = "demo"  # Replace with your FRED API key
        indicators = {
            'CPIAUCSL': 'Consumer Price Index',
            'UNRATE': 'Unemployment Rate', 
            'FEDFUNDS': 'Federal Funds Rate',
            'GDP': 'Gross Domestic Product',
            'PAYEMS': 'Nonfarm Payrolls',
            'DGS10': '10-Year Treasury Rate',
            'VIXCLS': 'VIX Volatility Index'
        }
        
        output_dir = Path('data/economic/fred_free')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if we have recent data
        output_file = output_dir / 'economic_indicators.json'
        if self.is_cache_valid(output_file, 'economic_data'):
            logger.info("📋 FRED data is recent, skipping download")
            try:
                with open(output_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        fred_data = {}
        successful_downloads = 0
        
        for indicator, name in indicators.items():
            try:
                url = "https://api.stlouisfed.org/fred/series/observations"
                params = {
                    'series_id': indicator,
                    'api_key': fred_key,
                    'file_type': 'json',
                    'limit': 100
                }
                
                data = self.make_api_request(url, params, 'api_responses')
                if data and 'observations' in data:
                    fred_data[indicator] = {
                        'name': name,
                        'data': data['observations'],
                        'downloaded_at': datetime.now().isoformat()
                    }
                    successful_downloads += 1
                    logger.info(f"✅ Downloaded {name}: {len(data['observations'])} data points")
                else:
                    logger.warning(f"⚠️ Failed to download {name}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Error downloading {name}: {e}")
        
        # Save FRED data with timestamp
        fred_data['_metadata'] = {
            'download_timestamp': datetime.now().isoformat(),
            'successful_indicators': successful_downloads,
            'total_attempted': len(indicators)
        }
        
        with open(output_file, 'w') as f:
            json.dump(fred_data, f, indent=2, default=str)
        
        logger.info(f"📊 FRED download complete: {successful_downloads}/{len(indicators)} indicators")
        return fred_data
    
    def download_alphavantage_data(self):
        """Download Alpha Vantage data with intelligent caching"""
        logger.info("📈 Downloading Alpha Vantage data...")
        
        api_key = self.config['data_sources']['api_keys']['alphavantage']['api_key']
        indicators = ['REAL_GDP', 'INFLATION', 'FEDERAL_FUNDS_RATE', 'CPI', 'UNEMPLOYMENT']
        
        output_dir = Path('data/economic/alphavantage_free')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if we have recent data
        output_file = output_dir / 'economic_indicators.json'
        if self.is_cache_valid(output_file, 'economic_data'):
            logger.info("📋 Alpha Vantage data is recent, skipping download")
            try:
                with open(output_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        av_data = {}
        successful_downloads = 0
        
        for indicator in indicators:
            try:
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': indicator,
                    'apikey': api_key
                }
                
                data = self.make_api_request(url, params, 'api_responses')
                if data:
                    av_data[indicator] = {
                        'data': data,
                        'downloaded_at': datetime.now().isoformat()
                    }
                    successful_downloads += 1
                    logger.info(f"✅ Downloaded {indicator}")
                else:
                    logger.warning(f"⚠️ Failed to download {indicator}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Error downloading {indicator}: {e}")
        
        # Add metadata
        av_data['_metadata'] = {
            'download_timestamp': datetime.now().isoformat(),
            'successful_indicators': successful_downloads,
            'total_attempted': len(indicators)
        }
        
        with open(output_file, 'w') as f:
            json.dump(av_data, f, indent=2, default=str)
        
        logger.info(f"📈 Alpha Vantage download complete: {successful_downloads}/{len(indicators)} indicators")
        return av_data
    
    def download_yahoo_finance_data(self):
        """Download Yahoo Finance data with intelligent caching"""
        logger.info("📊 Downloading Yahoo Finance data...")
        
        symbols = ['^VIX', '^GSPC', '^DJI', '^IXIC']
        output_dir = Path('data/market/yahoo_finance')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if we have recent data
        output_file = output_dir / 'market_data.json'
        if self.is_cache_valid(output_file, 'market_data'):
            logger.info("📋 Yahoo Finance data is recent, skipping download")
            try:
                with open(output_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        yf_data = {}
        successful_downloads = 0
        
        for symbol in symbols:
            try:
                # Check individual symbol cache
                symbol_cache_file = output_dir / f"{symbol.replace('^', '').lower()}_cache.json"
                if self.is_cache_valid(symbol_cache_file, 'market_data'):
                    logger.info(f"📋 Using cached data for {symbol}")
                    with open(symbol_cache_file, 'r') as f:
                        cached_data = json.load(f)
                        yf_data[symbol] = cached_data
                        successful_downloads += 1
                        continue
                
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="1y")
                
                if not data.empty:
                    symbol_data = {
                        'data': data.to_dict('records'),
                        'latest_price': float(data['Close'].iloc[-1]),
                        'latest_date': data.index[-1].strftime('%Y-%m-%d'),
                        'downloaded_at': datetime.now().isoformat()
                    }
                    yf_data[symbol] = symbol_data
                    
                    # Save individual symbol cache
                    with open(symbol_cache_file, 'w') as f:
                        json.dump(symbol_data, f, indent=2, default=str)
                    
                    successful_downloads += 1
                    logger.info(f"✅ Downloaded {symbol}: Latest price {symbol_data['latest_price']}")
                else:
                    logger.warning(f"⚠️ No data for {symbol}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Error downloading {symbol}: {e}")
        
        # Add metadata
        yf_data['_metadata'] = {
            'download_timestamp': datetime.now().isoformat(),
            'successful_symbols': successful_downloads,
            'total_attempted': len(symbols)
        }
        
        with open(output_file, 'w') as f:
            json.dump(yf_data, f, indent=2, default=str)
        
        logger.info(f"📊 Yahoo Finance download complete: {successful_downloads}/{len(symbols)} symbols")
        return yf_data
    
    def download_newsdata_news(self):
        """Download NewsData.io news with incremental updates"""
        logger.info("📰 Downloading NewsData.io news...")
        
        api_key = self.config['data_sources']['api_keys']['newsdata']['api_key']
        output_dir = Path('data/news/newsdata_free')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check for existing news data
        output_file = output_dir / 'forex_news.json'
        existing_articles = []
        
        if output_file.exists():
            try:
                with open(output_file, 'r') as f:
                    existing_data = json.load(f)
                    if isinstance(existing_data, list):
                        existing_articles = existing_data
                    elif isinstance(existing_data, dict) and 'articles' in existing_data:
                        existing_articles = existing_data['articles']
            except:
                pass
        
        # Get existing article IDs to avoid duplicates
        existing_ids = set()
        for article in existing_articles:
            if isinstance(article, dict) and 'article_id' in article:
                existing_ids.add(article['article_id'])
        
        try:
            url = "https://newsdata.io/api/1/news"
            params = {
                'apikey': api_key,
                'category': 'business',
                'language': 'en',
                'q': 'forex OR currency OR exchange rate',
                'size': 50
            }
            
            data = self.make_api_request(url, params, 'news_data')
            if data and 'results' in data:
                new_articles = data['results']
                
                # Filter out duplicates
                unique_new_articles = []
                for article in new_articles:
                    article_id = article.get('article_id', article.get('link', ''))
                    if article_id not in existing_ids:
                        unique_new_articles.append(article)
                        existing_ids.add(article_id)
                
                # Combine existing and new articles
                all_articles = existing_articles + unique_new_articles
                
                # Keep only the most recent 200 articles to prevent file bloat
                all_articles = sorted(all_articles, key=lambda x: x.get('pubDate', ''), reverse=True)[:200]
                
                news_data = {
                    'articles': all_articles,
                    'metadata': {
                        'download_timestamp': datetime.now().isoformat(),
                        'total_articles': len(all_articles),
                        'new_articles_added': len(unique_new_articles),
                        'duplicates_filtered': len(new_articles) - len(unique_new_articles)
                    }
                }
                
                with open(output_file, 'w') as f:
                    json.dump(news_data, f, indent=2, default=str)
                
                logger.info(f"✅ Downloaded {len(unique_new_articles)} new articles (total: {len(all_articles)})")
                return news_data
            else:
                logger.warning("⚠️ NewsData.io API error or no data")
                return {'articles': existing_articles, 'metadata': {'download_timestamp': datetime.now().isoformat()}}
                
        except Exception as e:
            logger.warning(f"⚠️ NewsData.io error: {e}")
            return {'articles': existing_articles, 'metadata': {'download_timestamp': datetime.now().isoformat()}}
    
    def create_integrated_dataset(self):
        """Create integrated dataset from all sources"""
        logger.info("🔗 Creating integrated dataset...")
        
        integrated_data = {
            'timestamp': datetime.now().isoformat(),
            'sources': {
                'fred': 'Economic indicators from Federal Reserve',
                'alphavantage': 'Economic indicators from Alpha Vantage',
                'yahoo_finance': 'Market sentiment and VIX data',
                'newsdata': 'Forex and economic news'
            },
            'data_summary': {
                'fred_indicators': 0,
                'alphavantage_indicators': 0,
                'yahoo_symbols': 0,
                'news_articles': 0
            },
            'cache_status': {
                'fred_cache_valid': False,
                'alphavantage_cache_valid': False,
                'yahoo_cache_valid': False,
                'news_cache_valid': False
            }
        }
        
        # Count data points and check cache status
        try:
            fred_file = Path('data/economic/fred_free/economic_indicators.json')
            if fred_file.exists():
                with open(fred_file, 'r') as f:
                    fred_data = json.load(f)
                    integrated_data['data_summary']['fred_indicators'] = len([k for k in fred_data.keys() if not k.startswith('_')])
                    integrated_data['cache_status']['fred_cache_valid'] = self.is_cache_valid(fred_file, 'economic_data')
        except:
            pass
        
        try:
            av_file = Path('data/economic/alphavantage_free/economic_indicators.json')
            if av_file.exists():
                with open(av_file, 'r') as f:
                    av_data = json.load(f)
                    integrated_data['data_summary']['alphavantage_indicators'] = len([k for k in av_data.keys() if not k.startswith('_')])
                    integrated_data['cache_status']['alphavantage_cache_valid'] = self.is_cache_valid(av_file, 'economic_data')
        except:
            pass
        
        try:
            yf_file = Path('data/market/yahoo_finance/market_data.json')
            if yf_file.exists():
                with open(yf_file, 'r') as f:
                    yf_data = json.load(f)
                    integrated_data['data_summary']['yahoo_symbols'] = len([k for k in yf_data.keys() if not k.startswith('_')])
                    integrated_data['cache_status']['yahoo_cache_valid'] = self.is_cache_valid(yf_file, 'market_data')
        except:
            pass
        
        try:
            news_file = Path('data/news/newsdata_free/forex_news.json')
            if news_file.exists():
                with open(news_file, 'r') as f:
                    news_data = json.load(f)
                    if isinstance(news_data, dict) and 'articles' in news_data:
                        integrated_data['data_summary']['news_articles'] = len(news_data['articles'])
                    elif isinstance(news_data, list):
                        integrated_data['data_summary']['news_articles'] = len(news_data)
                    integrated_data['cache_status']['news_cache_valid'] = self.is_cache_valid(news_file, 'news_data')
        except:
            pass
        
        # Save integrated dataset
        output_dir = Path('data/integrated_free')
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / 'comprehensive_dataset.json', 'w') as f:
            json.dump(integrated_data, f, indent=2, default=str)
        
        logger.info("🔗 Integrated dataset created successfully")
        return integrated_data
    
    def run_intelligent_download(self):
        """Run the intelligent download process"""
        print("🚀 INTELLIGENT NEWS DOWNLOADER")
        print("=" * 50)
        print("Starting intelligent data download with caching...")
        print()
        
        start_time = time.time()
        
        try:
            # Step 1: Download FRED data (with caching)
            fred_data = self.download_fred_data()
            
            # Step 2: Download Alpha Vantage data (with caching)
            av_data = self.download_alphavantage_data()
            
            # Step 3: Download Yahoo Finance data (with caching)
            yf_data = self.download_yahoo_finance_data()
            
            # Step 4: Download NewsData.io news (with incremental updates)
            news_data = self.download_newsdata_news()
            
            # Step 5: Create integrated dataset
            integrated_data = self.create_integrated_dataset()
            
            end_time = time.time()
            duration = end_time - start_time
            
            print()
            print("✅ INTELLIGENT DOWNLOAD COMPLETE!")
            print("=" * 40)
            print(f"⏱️  Total execution time: {duration:.2f} seconds")
            print()
            print("📊 Data Summary:")
            print(f"  FRED Indicators: {integrated_data['data_summary']['fred_indicators']}")
            print(f"  Alpha Vantage Indicators: {integrated_data['data_summary']['alphavantage_indicators']}")
            print(f"  Yahoo Finance Symbols: {integrated_data['data_summary']['yahoo_symbols']}")
            print(f"  News Articles: {integrated_data['data_summary']['news_articles']}")
            print()
            print("🗂️  Cache Status:")
            cache_status = integrated_data['cache_status']
            print(f"  FRED Cache Valid: {'✅' if cache_status['fred_cache_valid'] else '❌'}")
            print(f"  Alpha Vantage Cache Valid: {'✅' if cache_status['alphavantage_cache_valid'] else '❌'}")
            print(f"  Yahoo Finance Cache Valid: {'✅' if cache_status['yahoo_cache_valid'] else '❌'}")
            print(f"  News Cache Valid: {'✅' if cache_status['news_cache_valid'] else '❌'}")
            print()
            print("📁 Data saved to:")
            print("  - data/economic/fred_free/")
            print("  - data/economic/alphavantage_free/")
            print("  - data/market/yahoo_finance/")
            print("  - data/news/newsdata_free/")
            print("  - data/integrated_free/")
            print("  - data/cache/ (API response cache)")
            print()
            print("🎯 Your intelligent news dataset is ready!")
            print("💡 Next run will be much faster thanks to intelligent caching!")
            
        except Exception as e:
            logger.error(f"❌ Error in intelligent download: {e}")
            print(f"❌ Error: {e}")

def main():
    """Main execution function"""
    downloader = IntelligentDownloader()
    downloader.run_intelligent_download()

if __name__ == "__main__":
    main()
