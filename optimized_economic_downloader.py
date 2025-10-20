#!/usr/bin/env python3
"""
Optimized Economic Data Downloader
Fixes issues found in the current download and uses working APIs
"""

import requests
import pandas as pd
import json
import time
import os
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OptimizedEconomicDownloader:
    def __init__(self):
        self.api_keys = {
            # Alpha Vantage (3 keys) - WORKING
            'alphavantage': [
                'LSBZJ73J9W1G8FWB',
                'LB36ODU7500OUAHP', 
                'YXDNYDZ55K1248AR'
            ],
            # MarketAux (3 keys) - RATE LIMITED, but some working
            'marketaux': [
                'qL23wrqpBdU908DrznhIpfINVOgDg4bPmpKzQfW2',
                '39Ss2ny2bfHy2XNZLGRCof1011G3LT7gyRFC4Vct',
                'MwHMtJge9xsol0Q2NKC731fZz2XIoM23220ukx6C'
            ],
            # FRED (2 keys) - WORKING
            'fred': [
                'a9ef244d7466e388cde64cca30d225db',
                '3910b5fb49b1519a75782b57cd749341'
            ]
        }
        
        self.current_key_index = {service: 0 for service in self.api_keys}
        self.start_date = datetime(2022, 10, 24)
        self.end_date = datetime(2025, 8, 8)
        
        # Create output directories
        os.makedirs('data/economic/fred', exist_ok=True)
        os.makedirs('data/economic/alphavantage', exist_ok=True)
        os.makedirs('data/economic/marketaux', exist_ok=True)
        
    def get_next_api_key(self, service: str) -> str:
        """Get next API key for rotation"""
        current_index = self.current_key_index[service]
        key = self.api_keys[service][current_index]
        self.current_key_index[service] = (current_index + 1) % len(self.api_keys[service])
        return key
    
    def download_fred_additional_indicators(self):
        """Download additional FRED indicators that work"""
        logger.info("Downloading additional FRED indicators...")
        
        # Additional working FRED series
        fred_series = {
            'GDPC1': 'Real GDP',
            'GDPPOT': 'Real Potential GDP',
            'UNEMPLOY': 'Unemployment Level',
            'PAYEMS': 'All Employees, Total Nonfarm',
            'CES0500000003': 'Average Hourly Earnings',
            'CPILFESL': 'Core CPI',
            'CPIAUCSL': 'CPI All Items',
            'FEDFUNDS': 'Federal Funds Rate',
            'DGS10': '10-Year Treasury Rate',
            'DGS2': '2-Year Treasury Rate',
            'DGS3MO': '3-Month Treasury Rate',
            'DGS5': '5-Year Treasury Rate',
            'DGS30': '30-Year Treasury Rate',
            'INDPRO': 'Industrial Production Index',
            'RETAILSALES': 'Retail Sales',
            'HOUST': 'Housing Starts',
            'PERMIT': 'Building Permits',
            'UMCSENT': 'Consumer Sentiment',
            'VIXCLS': 'VIX Volatility Index'
        }
        
        for series_id, description in fred_series.items():
            try:
                api_key = self.get_next_api_key('fred')
                url = f"https://api.stlouisfed.org/fred/series/observations"
                
                params = {
                    'series_id': series_id,
                    'api_key': api_key,
                    'file_type': 'json',
                    'observation_start': self.start_date.strftime('%Y-%m-%d'),
                    'observation_end': self.end_date.strftime('%Y-%m-%d'),
                    'frequency': 'm'  # Monthly data
                }
                
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'observations' in data and data['observations']:
                        df = pd.DataFrame(data['observations'])
                        df['series_id'] = series_id
                        df['description'] = description
                        df['date'] = pd.to_datetime(df['date'])
                        
                        # Clean filename
                        clean_description = description.replace(' ', '_').replace(',', '').replace('/', '_')
                        filename = f"data/economic/fred/{series_id}_{clean_description}.csv"
                        df.to_csv(filename, index=False)
                        logger.info(f"Downloaded {len(df)} records for {description}")
                    else:
                        logger.warning(f"No observations found for {series_id}")
                else:
                    logger.error(f"FRED API error for {series_id}: {response.status_code}")
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error downloading FRED data for {series_id}: {e}")
                continue
    
    def download_alphavantage_economic_data(self):
        """Download Alpha Vantage economic data"""
        logger.info("Downloading Alpha Vantage economic data...")
        
        # Alpha Vantage economic indicators
        indicators = [
            'REAL_GDP',
            'REAL_GDP_PER_CAPITA', 
            'TREASURY_YIELD',
            'FEDERAL_FUNDS_RATE',
            'CPI',
            'INFLATION',
            'RETAIL_SALES',
            'DURABLES',
            'UNEMPLOYMENT'
        ]
        
        for indicator in indicators:
            try:
                api_key = self.get_next_api_key('alphavantage')
                url = "https://www.alphavantage.co/query"
                
                params = {
                    'function': indicator,
                    'apikey': api_key,
                    'datatype': 'json'
                }
                
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Save raw data
                    filename = f"data/economic/alphavantage/{indicator}.json"
                    with open(filename, 'w') as f:
                        json.dump(data, f, indent=2)
                    
                    logger.info(f"Downloaded {indicator} from Alpha Vantage")
                else:
                    logger.error(f"Alpha Vantage API error for {indicator}: {response.status_code}")
                
                time.sleep(12)  # Alpha Vantage rate limit: 5 calls per minute
                
            except Exception as e:
                logger.error(f"Error downloading Alpha Vantage {indicator}: {e}")
                continue
    
    def download_marketaux_working_news(self):
        """Download MarketAux news using working keys"""
        logger.info("Downloading MarketAux news with working keys...")
        
        all_news = []
        current_date = self.start_date
        
        while current_date <= self.end_date:
            try:
                # Try each API key
                for key in self.api_keys['marketaux']:
                    try:
                        url = "https://api.marketaux.com/v1/news/all"
                        
                        # Get next month
                        next_month = current_date + timedelta(days=30)
                        if next_month > self.end_date:
                            next_month = self.end_date
                        
                        params = {
                            'api_token': key,
                            'countries': 'us,eu,gb,jp,au,ca,ch,nz',
                            'published_after': current_date.strftime('%Y-%m-%d'),
                            'published_before': next_month.strftime('%Y-%m-%d'),
                            'limit': 100,
                            'page': 1
                        }
                        
                        response = requests.get(url, params=params, timeout=30)
                        
                        if response.status_code == 200:
                            data = response.json()
                            if 'data' in data and data['data']:
                                all_news.extend(data['data'])
                                logger.info(f"Downloaded {len(data['data'])} news articles for {current_date.strftime('%Y-%m')} with key {key[:10]}...")
                                break  # Success, move to next month
                            else:
                                logger.warning(f"No news found for {current_date.strftime('%Y-%m')}")
                        elif response.status_code == 402:
                            logger.warning(f"Rate limit for key {key[:10]}..., trying next key")
                            continue
                        else:
                            logger.error(f"MarketAux API error: {response.status_code}")
                            
                    except Exception as e:
                        logger.error(f"Error with key {key[:10]}...: {e}")
                        continue
                
                current_date = next_month + timedelta(days=1)
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error downloading MarketAux news for {current_date}: {e}")
                current_date += timedelta(days=30)
                continue
        
        # Save all news
        if all_news:
            df = pd.DataFrame(all_news)
            df['published_at'] = pd.to_datetime(df['published_at'])
            filename = "data/economic/marketaux/economic_news_optimized.csv"
            df.to_csv(filename, index=False)
            logger.info(f"Saved {len(all_news)} total news articles")
    
    def run_optimized_download(self):
        """Run optimized downloads focusing on working APIs"""
        logger.info("Starting optimized economic data download...")
        logger.info(f"Date range: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        
        # Download from working APIs
        self.download_fred_additional_indicators()
        self.download_alphavantage_economic_data()
        self.download_marketaux_working_news()
        
        logger.info("Optimized economic data download completed!")

if __name__ == "__main__":
    downloader = OptimizedEconomicDownloader()
    downloader.run_optimized_download()

