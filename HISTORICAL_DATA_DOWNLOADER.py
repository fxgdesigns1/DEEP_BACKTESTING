#!/usr/bin/env python3
"""
HISTORICAL DATA DOWNLOADER FOR BACKTESTING
==========================================

Specialized downloader for historical data (2022-2025) needed for backtesting.
Downloads comprehensive historical economic, market, and news data.

Features:
- Historical date range downloads (2022-2025)
- Bulk data acquisition for backtesting
- Economic indicators with full historical coverage
- Historical news data
- Backtesting-optimized data organization
"""

import requests
import json
import yaml
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import logging
import time
from pathlib import Path
import numpy as np

# Setup enhanced logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('historical_downloader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HistoricalDataDownloader:
    """Historical data downloader for backtesting (2022-2025)"""
    
    def __init__(self, start_date="2022-01-01", end_date="2025-12-31"):
        self.start_date = start_date
        self.end_date = end_date
        self.config = self.load_config()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'HistoricalDownloader/1.0'})
        
        # Create backtesting-specific directories
        self.backtesting_dir = Path('data/backtesting_historical')
        self.backtesting_dir.mkdir(parents=True, exist_ok=True)
        
        # Subdirectories for different data types
        self.economic_dir = self.backtesting_dir / 'economic'
        self.market_dir = self.backtesting_dir / 'market'
        self.news_dir = self.backtesting_dir / 'news'
        self.integrated_dir = self.backtesting_dir / 'integrated'
        
        for dir_path in [self.economic_dir, self.market_dir, self.news_dir, self.integrated_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🚀 Historical Downloader initialized for {start_date} to {end_date}")
    
    def load_config(self):
        """Load configuration"""
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
    
    def download_historical_fred_data(self):
        """Download historical FRED economic data for backtesting"""
        logger.info("📊 Downloading historical FRED economic data...")
        
        fred_key = "demo"  # Replace with your FRED API key
        
        # Comprehensive economic indicators for backtesting
        indicators = {
            'CPIAUCSL': 'Consumer Price Index',
            'UNRATE': 'Unemployment Rate', 
            'FEDFUNDS': 'Federal Funds Rate',
            'GDP': 'Gross Domestic Product',
            'PAYEMS': 'Nonfarm Payrolls',
            'DGS10': '10-Year Treasury Rate',
            'VIXCLS': 'VIX Volatility Index',
            'DGS2': '2-Year Treasury Rate',
            'DGS5': '5-Year Treasury Rate',
            'DGS30': '30-Year Treasury Rate',
            'INDPRO': 'Industrial Production Index',
            'HOUST': 'Housing Starts',
            'UMCSENT': 'Consumer Sentiment Index',
            'CPILFESL': 'Core Consumer Price Index',
            'PERMIT': 'Building Permits'
        }
        
        fred_data = {}
        successful_downloads = 0
        
        for indicator, name in indicators.items():
            try:
                logger.info(f"📈 Downloading {name} ({indicator})...")
                
                url = "https://api.stlouisfed.org/fred/series/observations"
                params = {
                    'series_id': indicator,
                    'api_key': fred_key,
                    'file_type': 'json',
                    'observation_start': self.start_date,
                    'observation_end': self.end_date,
                    'limit': 10000  # Maximum limit for historical data
                }
                
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    observations = data.get('observations', [])
                    
                    if observations:
                        # Convert to DataFrame for easier processing
                        df_data = []
                        for obs in observations:
                            if obs.get('value') != '.' and obs.get('value') is not None:
                                df_data.append({
                                    'date': obs['date'],
                                    'value': float(obs['value']),
                                    'indicator': indicator,
                                    'name': name
                                })
                        
                        fred_data[indicator] = {
                            'name': name,
                            'data': df_data,
                            'count': len(df_data),
                            'start_date': self.start_date,
                            'end_date': self.end_date,
                            'downloaded_at': datetime.now().isoformat()
                        }
                        
                        successful_downloads += 1
                        logger.info(f"✅ Downloaded {name}: {len(df_data)} historical data points")
                        
                        # Save individual indicator file
                        indicator_file = self.economic_dir / f"fred_{indicator.lower()}.json"
                        with open(indicator_file, 'w') as f:
                            json.dump(fred_data[indicator], f, indent=2, default=str)
                    else:
                        logger.warning(f"⚠️ No data found for {name}")
                else:
                    logger.warning(f"⚠️ Failed to download {name}: HTTP {response.status_code}")
                    
                # Rate limiting - be respectful to FRED API
                time.sleep(1)
                    
            except Exception as e:
                logger.warning(f"⚠️ Error downloading {name}: {e}")
        
        # Save comprehensive FRED data
        fred_data['_metadata'] = {
            'download_timestamp': datetime.now().isoformat(),
            'successful_indicators': successful_downloads,
            'total_attempted': len(indicators),
            'date_range': f"{self.start_date} to {self.end_date}",
            'purpose': 'backtesting'
        }
        
        with open(self.economic_dir / 'fred_comprehensive.json', 'w') as f:
            json.dump(fred_data, f, indent=2, default=str)
        
        logger.info(f"📊 FRED historical download complete: {successful_downloads}/{len(indicators)} indicators")
        return fred_data
    
    def download_historical_alphavantage_data(self):
        """Download historical Alpha Vantage data for backtesting"""
        logger.info("📈 Downloading historical Alpha Vantage data...")
        
        api_key = self.config['data_sources']['api_keys']['alphavantage']['api_key']
        
        # Economic indicators for backtesting
        indicators = [
            'REAL_GDP', 'INFLATION', 'FEDERAL_FUNDS_RATE', 'CPI', 'UNEMPLOYMENT',
            'RETAIL_SALES', 'DURABLES', 'TREASURY_YIELD', 'REAL_GDP_PER_CAPITA'
        ]
        
        av_data = {}
        successful_downloads = 0
        
        for indicator in indicators:
            try:
                logger.info(f"📈 Downloading Alpha Vantage {indicator}...")
                
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': indicator,
                    'apikey': api_key
                }
                
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if we got valid data (not error message)
                    if 'data' in data or 'data' in str(data):
                        av_data[indicator] = {
                            'data': data,
                            'downloaded_at': datetime.now().isoformat(),
                            'date_range': f"{self.start_date} to {self.end_date}",
                            'purpose': 'backtesting'
                        }
                        
                        successful_downloads += 1
                        logger.info(f"✅ Downloaded Alpha Vantage {indicator}")
                        
                        # Save individual indicator file
                        indicator_file = self.economic_dir / f"alphavantage_{indicator.lower()}.json"
                        with open(indicator_file, 'w') as f:
                            json.dump(av_data[indicator], f, indent=2, default=str)
                    else:
                        logger.warning(f"⚠️ No valid data for Alpha Vantage {indicator}")
                else:
                    logger.warning(f"⚠️ Failed to download Alpha Vantage {indicator}: HTTP {response.status_code}")
                
                # Rate limiting for Alpha Vantage
                time.sleep(2)
                    
            except Exception as e:
                logger.warning(f"⚠️ Error downloading Alpha Vantage {indicator}: {e}")
        
        # Save comprehensive Alpha Vantage data
        av_data['_metadata'] = {
            'download_timestamp': datetime.now().isoformat(),
            'successful_indicators': successful_downloads,
            'total_attempted': len(indicators),
            'date_range': f"{self.start_date} to {self.end_date}",
            'purpose': 'backtesting'
        }
        
        with open(self.economic_dir / 'alphavantage_comprehensive.json', 'w') as f:
            json.dump(av_data, f, indent=2, default=str)
        
        logger.info(f"📈 Alpha Vantage historical download complete: {successful_downloads}/{len(indicators)} indicators")
        return av_data
    
    def download_historical_yahoo_finance_data(self):
        """Download historical Yahoo Finance data for backtesting"""
        logger.info("📊 Downloading historical Yahoo Finance data...")
        
        # Comprehensive list of symbols for backtesting
        symbols = {
            '^VIX': 'VIX Volatility Index',
            '^GSPC': 'S&P 500',
            '^DJI': 'Dow Jones Industrial Average',
            '^IXIC': 'NASDAQ Composite',
            '^RUT': 'Russell 2000',
            '^TNX': '10-Year Treasury Note',
            '^FVX': '5-Year Treasury Note',
            '^TYX': '30-Year Treasury Bond',
            'DX-Y.NYB': 'US Dollar Index',
            'GC=F': 'Gold Futures',
            'CL=F': 'Crude Oil Futures',
            'EURUSD=X': 'EUR/USD',
            'GBPUSD=X': 'GBP/USD',
            'USDJPY=X': 'USD/JPY'
        }
        
        yf_data = {}
        successful_downloads = 0
        
        for symbol, name in symbols.items():
            try:
                logger.info(f"📊 Downloading {name} ({symbol})...")
                
                ticker = yf.Ticker(symbol)
                
                # Download historical data for the specified period
                data = ticker.history(
                    start=self.start_date,
                    end=self.end_date,
                    interval='1d'  # Daily data for backtesting
                )
                
                if not data.empty:
                    # Convert to records format
                    records = []
                    for date, row in data.iterrows():
                        records.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'open': float(row['Open']),
                            'high': float(row['High']),
                            'low': float(row['Low']),
                            'close': float(row['Close']),
                            'volume': int(row['Volume']) if pd.notna(row['Volume']) else 0,
                            'symbol': symbol,
                            'name': name
                        })
                    
                    yf_data[symbol] = {
                        'name': name,
                        'data': records,
                        'count': len(records),
                        'start_date': self.start_date,
                        'end_date': self.end_date,
                        'downloaded_at': datetime.now().isoformat(),
                        'purpose': 'backtesting'
                    }
                    
                    successful_downloads += 1
                    logger.info(f"✅ Downloaded {name}: {len(records)} historical data points")
                    
                    # Save individual symbol file
                    symbol_file = self.market_dir / f"yahoo_{symbol.replace('^', '').replace('=', '_').replace('-', '_').lower()}.json"
                    with open(symbol_file, 'w') as f:
                        json.dump(yf_data[symbol], f, indent=2, default=str)
                else:
                    logger.warning(f"⚠️ No data found for {symbol}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Error downloading {symbol}: {e}")
        
        # Save comprehensive Yahoo Finance data
        yf_data['_metadata'] = {
            'download_timestamp': datetime.now().isoformat(),
            'successful_symbols': successful_downloads,
            'total_attempted': len(symbols),
            'date_range': f"{self.start_date} to {self.end_date}",
            'purpose': 'backtesting'
        }
        
        with open(self.market_dir / 'yahoo_comprehensive.json', 'w') as f:
            json.dump(yf_data, f, indent=2, default=str)
        
        logger.info(f"📊 Yahoo Finance historical download complete: {successful_downloads}/{len(symbols)} symbols")
        return yf_data
    
    def download_historical_news_data(self):
        """Download historical news data for backtesting (simulated)"""
        logger.info("📰 Preparing historical news data structure...")
        
        # Since most news APIs don't provide historical data going back to 2022,
        # we'll create a structure for news data integration
        # You can manually add historical news or use other sources
        
        news_structure = {
            'metadata': {
                'download_timestamp': datetime.now().isoformat(),
                'date_range': f"{self.start_date} to {self.end_date}",
                'purpose': 'backtesting',
                'note': 'Historical news data structure created. Add your historical news sources here.'
            },
            'categories': [
                'central_bank_announcements',
                'economic_indicators',
                'political_events',
                'market_volatility',
                'currency_interventions'
            ],
            'sources': [
                'federal_reserve_meetings',
                'ecb_announcements',
                'boe_meetings',
                'economic_calendar',
                'financial_news'
            ]
        }
        
        # Save news structure
        with open(self.news_dir / 'news_structure.json', 'w') as f:
            json.dump(news_structure, f, indent=2, default=str)
        
        logger.info("📰 Historical news structure created")
        return news_structure
    
    def create_backtesting_dataset(self):
        """Create integrated backtesting dataset"""
        logger.info("🔗 Creating integrated backtesting dataset...")
        
        backtesting_data = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'date_range': f"{self.start_date} to {self.end_date}",
                'purpose': 'backtesting',
                'version': '1.0'
            },
            'data_summary': {
                'fred_indicators': 0,
                'alphavantage_indicators': 0,
                'yahoo_symbols': 0,
                'news_categories': 0
            },
            'directories': {
                'economic_data': str(self.economic_dir),
                'market_data': str(self.market_dir),
                'news_data': str(self.news_dir),
                'integrated_data': str(self.integrated_dir)
            }
        }
        
        # Count downloaded data
        try:
            # Count FRED indicators
            fred_file = self.economic_dir / 'fred_comprehensive.json'
            if fred_file.exists():
                with open(fred_file, 'r') as f:
                    fred_data = json.load(f)
                    backtesting_data['data_summary']['fred_indicators'] = len([k for k in fred_data.keys() if not k.startswith('_')])
        except:
            pass
        
        try:
            # Count Alpha Vantage indicators
            av_file = self.economic_dir / 'alphavantage_comprehensive.json'
            if av_file.exists():
                with open(av_file, 'r') as f:
                    av_data = json.load(f)
                    backtesting_data['data_summary']['alphavantage_indicators'] = len([k for k in av_data.keys() if not k.startswith('_')])
        except:
            pass
        
        try:
            # Count Yahoo Finance symbols
            yf_file = self.market_dir / 'yahoo_comprehensive.json'
            if yf_file.exists():
                with open(yf_file, 'r') as f:
                    yf_data = json.load(f)
                    backtesting_data['data_summary']['yahoo_symbols'] = len([k for k in yf_data.keys() if not k.startswith('_')])
        except:
            pass
        
        try:
            # Count news categories
            news_file = self.news_dir / 'news_structure.json'
            if news_file.exists():
                with open(news_file, 'r') as f:
                    news_data = json.load(f)
                    backtesting_data['data_summary']['news_categories'] = len(news_data.get('categories', []))
        except:
            pass
        
        # Save integrated backtesting dataset
        with open(self.integrated_dir / 'backtesting_dataset.json', 'w') as f:
            json.dump(backtesting_data, f, indent=2, default=str)
        
        logger.info("🔗 Backtesting dataset created successfully")
        return backtesting_data
    
    def run_historical_download(self):
        """Run the complete historical download process"""
        print("🚀 HISTORICAL DATA DOWNLOADER FOR BACKTESTING")
        print("=" * 60)
        print(f"📅 Date Range: {self.start_date} to {self.end_date}")
        print("🎯 Purpose: Backtesting System")
        print()
        
        start_time = time.time()
        
        try:
            # Step 1: Download historical FRED data
            fred_data = self.download_historical_fred_data()
            
            # Step 2: Download historical Alpha Vantage data
            av_data = self.download_historical_alphavantage_data()
            
            # Step 3: Download historical Yahoo Finance data
            yf_data = self.download_historical_yahoo_finance_data()
            
            # Step 4: Create news data structure
            news_data = self.download_historical_news_data()
            
            # Step 5: Create integrated backtesting dataset
            backtesting_data = self.create_backtesting_dataset()
            
            end_time = time.time()
            duration = end_time - start_time
            
            print()
            print("✅ HISTORICAL DOWNLOAD COMPLETE!")
            print("=" * 45)
            print(f"⏱️  Total execution time: {duration:.2f} seconds")
            print()
            print("📊 Historical Data Summary:")
            summary = backtesting_data['data_summary']
            print(f"  FRED Indicators: {summary['fred_indicators']}")
            print(f"  Alpha Vantage Indicators: {summary['alphavantage_indicators']}")
            print(f"  Yahoo Finance Symbols: {summary['yahoo_symbols']}")
            print(f"  News Categories: {summary['news_categories']}")
            print()
            print("📁 Backtesting data saved to:")
            print("  - data/backtesting_historical/economic/")
            print("  - data/backtesting_historical/market/")
            print("  - data/backtesting_historical/news/")
            print("  - data/backtesting_historical/integrated/")
            print()
            print("🎯 Your historical backtesting dataset is ready!")
            print("💡 Use this data for comprehensive backtesting analysis!")
            
        except Exception as e:
            logger.error(f"❌ Error in historical download: {e}")
            print(f"❌ Error: {e}")

def main():
    """Main execution function"""
    # You can customize the date range here
    downloader = HistoricalDataDownloader(
        start_date="2022-01-01",
        end_date="2025-12-31"
    )
    downloader.run_historical_download()

if __name__ == "__main__":
    main()
