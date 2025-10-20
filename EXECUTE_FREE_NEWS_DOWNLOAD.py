#!/usr/bin/env python3
"""
EXECUTE FREE NEWS DOWNLOAD
==========================

Execute the free approach plan immediately to download comprehensive news data
"""

import requests
import json
import yaml
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration"""
    with open('config/settings.yaml', 'r') as f:
        return yaml.safe_load(f)

def download_fred_data():
    """Download FRED economic data"""
    logger.info("📊 Downloading FRED economic data...")
    
    # FRED API key (free)
    fred_key = "demo"  # Replace with your FRED API key if you have one
    
    # Economic indicators to download
    indicators = {
        'CPIAUCSL': 'Consumer Price Index',
        'UNRATE': 'Unemployment Rate', 
        'FEDFUNDS': 'Federal Funds Rate',
        'GDP': 'Gross Domestic Product',
        'PAYEMS': 'Nonfarm Payrolls',
        'DGS10': '10-Year Treasury Rate',
        'VIXCLS': 'VIX Volatility Index'
    }
    
    fred_data = {}
    
    for indicator, name in indicators.items():
        try:
            url = f"https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': indicator,
                'api_key': fred_key,
                'file_type': 'json',
                'limit': 100
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                fred_data[indicator] = {
                    'name': name,
                    'data': data.get('observations', [])
                }
                logger.info(f"✅ Downloaded {name}: {len(data.get('observations', []))} data points")
            else:
                logger.warning(f"⚠️ Failed to download {name}: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"⚠️ Error downloading {name}: {e}")
    
    # Save FRED data
    os.makedirs('data/economic/fred_free', exist_ok=True)
    with open('data/economic/fred_free/economic_indicators.json', 'w') as f:
        json.dump(fred_data, f, indent=2, default=str)
    
    logger.info(f"📊 FRED download complete: {len(fred_data)} indicators")
    return fred_data

def download_alphavantage_data():
    """Download Alpha Vantage data"""
    logger.info("📈 Downloading Alpha Vantage data...")
    
    config = load_config()
    api_key = config['data_sources']['api_keys']['alphavantage']['api_key']
    
    # Download economic indicators
    indicators = ['REAL_GDP', 'INFLATION', 'FEDERAL_FUNDS_RATE', 'CPI', 'UNEMPLOYMENT']
    
    av_data = {}
    
    for indicator in indicators:
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': indicator,
                'apikey': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                av_data[indicator] = data
                logger.info(f"✅ Downloaded {indicator}")
            else:
                logger.warning(f"⚠️ Failed to download {indicator}: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"⚠️ Error downloading {indicator}: {e}")
    
    # Save Alpha Vantage data
    os.makedirs('data/economic/alphavantage_free', exist_ok=True)
    with open('data/economic/alphavantage_free/economic_indicators.json', 'w') as f:
        json.dump(av_data, f, indent=2, default=str)
    
    logger.info(f"📈 Alpha Vantage download complete: {len(av_data)} indicators")
    return av_data

def download_yahoo_finance_data():
    """Download Yahoo Finance data"""
    logger.info("📊 Downloading Yahoo Finance data...")
    
    # Download VIX and market sentiment data
    symbols = ['^VIX', '^GSPC', '^DJI', '^IXIC']  # VIX, S&P 500, Dow, NASDAQ
    
    yf_data = {}
    
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1y")
            
            if not data.empty:
                yf_data[symbol] = {
                    'data': data.to_dict('records'),
                    'latest_price': float(data['Close'].iloc[-1]),
                    'latest_date': data.index[-1].strftime('%Y-%m-%d')
                }
                logger.info(f"✅ Downloaded {symbol}: Latest price {yf_data[symbol]['latest_price']}")
            else:
                logger.warning(f"⚠️ No data for {symbol}")
                
        except Exception as e:
            logger.warning(f"⚠️ Error downloading {symbol}: {e}")
    
    # Save Yahoo Finance data
    os.makedirs('data/market/yahoo_finance', exist_ok=True)
    with open('data/market/yahoo_finance/market_data.json', 'w') as f:
        json.dump(yf_data, f, indent=2, default=str)
    
    logger.info(f"📊 Yahoo Finance download complete: {len(yf_data)} symbols")
    return yf_data

def download_newsdata_news():
    """Download NewsData.io news"""
    logger.info("📰 Downloading NewsData.io news...")
    
    config = load_config()
    api_key = config['data_sources']['api_keys']['newsdata']['api_key']
    
    try:
        url = "https://newsdata.io/api/1/news"
        params = {
            'apikey': api_key,
            'category': 'business',
            'language': 'en',
            'q': 'forex OR currency OR exchange rate',
            'size': 50
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            news_data = data.get('results', [])
            logger.info(f"✅ Downloaded {len(news_data)} news articles")
        else:
            logger.warning(f"⚠️ NewsData.io API error: {response.status_code}")
            news_data = []
            
    except Exception as e:
        logger.warning(f"⚠️ NewsData.io error: {e}")
        news_data = []
    
    # Save news data
    os.makedirs('data/news/newsdata_free', exist_ok=True)
    with open('data/news/newsdata_free/forex_news.json', 'w') as f:
        json.dump(news_data, f, indent=2, default=str)
    
    logger.info(f"📰 NewsData.io download complete: {len(news_data)} articles")
    return news_data

def create_integrated_dataset():
    """Create integrated dataset from all sources"""
    logger.info("🔗 Creating integrated dataset...")
    
    # Load all downloaded data
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
        }
    }
    
    # Count data points
    try:
        with open('data/economic/fred_free/economic_indicators.json', 'r') as f:
            fred_data = json.load(f)
            integrated_data['data_summary']['fred_indicators'] = len(fred_data)
    except:
        pass
    
    try:
        with open('data/economic/alphavantage_free/economic_indicators.json', 'r') as f:
            av_data = json.load(f)
            integrated_data['data_summary']['alphavantage_indicators'] = len(av_data)
    except:
        pass
    
    try:
        with open('data/market/yahoo_finance/market_data.json', 'r') as f:
            yf_data = json.load(f)
            integrated_data['data_summary']['yahoo_symbols'] = len(yf_data)
    except:
        pass
    
    try:
        with open('data/news/newsdata_free/forex_news.json', 'r') as f:
            news_data = json.load(f)
            integrated_data['data_summary']['news_articles'] = len(news_data)
    except:
        pass
    
    # Save integrated dataset
    os.makedirs('data/integrated_free', exist_ok=True)
    with open('data/integrated_free/comprehensive_dataset.json', 'w') as f:
        json.dump(integrated_data, f, indent=2, default=str)
    
    logger.info("🔗 Integrated dataset created successfully")
    return integrated_data

def main():
    """Main execution function"""
    print("🚀 EXECUTING FREE NEWS DOWNLOAD")
    print("=" * 50)
    print("Starting comprehensive news download using free APIs...")
    print()
    
    try:
        # Step 1: Download FRED data
        fred_data = download_fred_data()
        
        # Step 2: Download Alpha Vantage data
        av_data = download_alphavantage_data()
        
        # Step 3: Download Yahoo Finance data
        yf_data = download_yahoo_finance_data()
        
        # Step 4: Download NewsData.io news
        news_data = download_newsdata_news()
        
        # Step 5: Create integrated dataset
        integrated_data = create_integrated_dataset()
        
        print()
        print("✅ FREE NEWS DOWNLOAD COMPLETE!")
        print("=" * 40)
        print(f"FRED Indicators: {integrated_data['data_summary']['fred_indicators']}")
        print(f"Alpha Vantage Indicators: {integrated_data['data_summary']['alphavantage_indicators']}")
        print(f"Yahoo Finance Symbols: {integrated_data['data_summary']['yahoo_symbols']}")
        print(f"News Articles: {integrated_data['data_summary']['news_articles']}")
        print()
        print("📁 Data saved to:")
        print("  - data/economic/fred_free/")
        print("  - data/economic/alphavantage_free/")
        print("  - data/market/yahoo_finance/")
        print("  - data/news/newsdata_free/")
        print("  - data/integrated_free/")
        print()
        print("🎯 Your comprehensive news dataset is ready!")
        
    except Exception as e:
        logger.error(f"❌ Error in free news download: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
