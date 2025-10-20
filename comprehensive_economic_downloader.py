#!/usr/bin/env python3
"""
Comprehensive Economic Data Downloader
Downloads historical economic data matching candle data timeframes (2022-10-24 to 2025-08-08)
Uses all available APIs with rotation and rate limiting
"""

import requests
import pandas as pd
import json
import time
import asyncio
import aiohttp
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveEconomicDownloader:
    def __init__(self):
        self.api_keys = {
            # Alpha Vantage (3 keys)
            'alphavantage': [
                'LSBZJ73J9W1G8FWB',
                'LB36ODU7500OUAHP', 
                'YXDNYDZ55K1248AR'
            ],
            # MarketAux (3 keys)
            'marketaux': [
                'qL23wrqpBdU908DrznhIpfINVOgDg4bPmpKzQfW2',
                '39Ss2ny2bfHy2XNZLGRCof1011G3LT7gyRFC4Vct',
                'MwHMtJge9xsol0Q2NKC731fZz2XIoM23220ukx6C'
            ],
            # Polygon.io (3 keys)
            'polygon': [
                'eiRSVY6NjFnh5dG9iHkXzKBdLLp8C39q',
                'aU2fVci7svp3GXJA4PCyqtykSsa8V2iN',
                'RGEL1p4sDdghdpORGzglkmLWDK1cj2Eh'
            ],
            # FinancialModelingPrep (2 keys)
            'fmp': [
                'XaZrx5fB6UEM5xoSHPjPEO6crJ1zDe6J',
                '6sksRLjThlEZIILXuya2mxTtcqzQHrDv'
            ],
            # FRED (2 keys)
            'fred': [
                'a9ef244d7466e388cde64cca30d225db',
                '3910b5fb49b1519a75782b57cd749341'
            ],
            # NewsData.io (1 key)
            'newsdata': ['pub_f8e040b68d614a31b36877ea5fbd6732']
        }
        
        self.current_key_index = {service: 0 for service in self.api_keys}
        self.rate_limits = {
            'alphavantage': {'per_minute': 5, 'per_day': 500},
            'marketaux': {'per_minute': 10, 'per_day': 1000},
            'polygon': {'per_minute': 5, 'per_day': 1000},
            'fmp': {'per_minute': 10, 'per_day': 1000},
            'fred': {'per_minute': 120, 'per_day': 10000},
            'newsdata': {'per_minute': 10, 'per_day': 1000}
        }
        
        self.last_request_time = {service: {} for service in self.api_keys}
        self.daily_usage = {service: {} for service in self.api_keys}
        
        # Date range from candle data
        self.start_date = datetime(2022, 10, 24)
        self.end_date = datetime(2025, 8, 8)
        
        # Create output directories
        os.makedirs('data/economic/fred', exist_ok=True)
        os.makedirs('data/economic/fmp', exist_ok=True)
        os.makedirs('data/economic/polygon', exist_ok=True)
        os.makedirs('data/economic/marketaux', exist_ok=True)
        os.makedirs('data/economic/newsdata', exist_ok=True)
        
    def get_next_api_key(self, service: str) -> str:
        """Get next API key for rotation"""
        current_index = self.current_key_index[service]
        key = self.api_keys[service][current_index]
        self.current_key_index[service] = (current_index + 1) % len(self.api_keys[service])
        return key
    
    def check_rate_limit(self, service: str) -> bool:
        """Check if we can make a request without hitting rate limits"""
        now = datetime.now()
        today = now.date()
        
        # Check daily limit
        if today not in self.daily_usage[service]:
            self.daily_usage[service][today] = 0
        
        if self.daily_usage[service][today] >= self.rate_limits[service]['per_day']:
            logger.warning(f"Daily limit reached for {service}")
            return False
        
        # Check per-minute limit
        minute_key = now.replace(second=0, microsecond=0)
        if minute_key not in self.last_request_time[service]:
            self.last_request_time[service][minute_key] = 0
        
        if self.last_request_time[service][minute_key] >= self.rate_limits[service]['per_minute']:
            logger.warning(f"Per-minute limit reached for {service}")
            return False
        
        return True
    
    def record_request(self, service: str):
        """Record a successful request"""
        now = datetime.now()
        today = now.date()
        minute_key = now.replace(second=0, microsecond=0)
        
        self.daily_usage[service][today] = self.daily_usage[service].get(today, 0) + 1
        self.last_request_time[service][minute_key] = self.last_request_time[service].get(minute_key, 0) + 1
    
    def download_fred_data(self):
        """Download FRED economic indicators"""
        logger.info("Starting FRED data download...")
        
        # Key economic indicators
        fred_series = {
            'CPIAUCSL': 'Consumer Price Index',
            'UNRATE': 'Unemployment Rate',
            'GDP': 'Gross Domestic Product',
            'FEDFUNDS': 'Federal Funds Rate',
            'PAYEMS': 'Nonfarm Payrolls',
            'RETAILSALES': 'Retail Sales',
            'INDPRO': 'Industrial Production',
            'DGS10': '10-Year Treasury Rate',
            'DGS2': '2-Year Treasury Rate',
            'DEXUSEU': 'USD/EUR Exchange Rate',
            'DEXJPUS': 'USD/JPY Exchange Rate',
            'DEXUSUK': 'USD/GBP Exchange Rate'
        }
        
        for series_id, description in fred_series.items():
            try:
                if not self.check_rate_limit('fred'):
                    time.sleep(60)  # Wait 1 minute
                    continue
                
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
                self.record_request('fred')
                
                if response.status_code == 200:
                    data = response.json()
                    if 'observations' in data:
                        df = pd.DataFrame(data['observations'])
                        df['series_id'] = series_id
                        df['description'] = description
                        df['date'] = pd.to_datetime(df['date'])
                        
                        # Save to CSV
                        filename = f"data/economic/fred/{series_id}_{description.replace(' ', '_')}.csv"
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
    
    def download_fmp_economic_calendar(self):
        """Download FMP economic calendar"""
        logger.info("Starting FMP economic calendar download...")
        
        try:
            if not self.check_rate_limit('fmp'):
                time.sleep(60)
                return
            
            api_key = self.get_next_api_key('fmp')
            url = "https://financialmodelingprep.com/api/v3/economic_calendar"
            
            params = {
                'apikey': api_key,
                'from': self.start_date.strftime('%Y-%m-%d'),
                'to': self.end_date.strftime('%Y-%m-%d')
            }
            
            response = requests.get(url, params=params, timeout=30)
            self.record_request('fmp')
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    df = pd.DataFrame(data)
                    df['date'] = pd.to_datetime(df['date'])
                    
                    # Save to CSV
                    filename = "data/economic/fmp/economic_calendar.csv"
                    df.to_csv(filename, index=False)
                    logger.info(f"Downloaded {len(df)} economic events from FMP")
                else:
                    logger.warning("No economic calendar data found")
            else:
                logger.error(f"FMP API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error downloading FMP economic calendar: {e}")
    
    def download_polygon_data(self):
        """Download Polygon.io economic data"""
        logger.info("Starting Polygon.io data download...")
        
        try:
            if not self.check_rate_limit('polygon'):
                time.sleep(60)
                return
            
            api_key = self.get_next_api_key('polygon')
            
            # Get market status and economic indicators
            endpoints = [
                'marketstatus',
                'indicators/economic',
                'indicators/technical'
            ]
            
            for endpoint in endpoints:
                try:
                    url = f"https://api.polygon.io/v1/{endpoint}"
                    params = {'apikey': api_key}
                    
                    response = requests.get(url, params=params, timeout=30)
                    self.record_request('polygon')
                    
                    if response.status_code == 200:
                        data = response.json()
                        filename = f"data/economic/polygon/{endpoint.replace('/', '_')}.json"
                        
                        with open(filename, 'w') as f:
                            json.dump(data, f, indent=2)
                        
                        logger.info(f"Downloaded {endpoint} from Polygon.io")
                    else:
                        logger.error(f"Polygon API error for {endpoint}: {response.status_code}")
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error downloading {endpoint} from Polygon: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error downloading Polygon data: {e}")
    
    def download_marketaux_news(self):
        """Download MarketAux economic news"""
        logger.info("Starting MarketAux news download...")
        
        # Download news in monthly batches
        current_date = self.start_date
        all_news = []
        
        while current_date <= self.end_date:
            try:
                if not self.check_rate_limit('marketaux'):
                    time.sleep(60)
                    continue
                
                api_key = self.get_next_api_key('marketaux')
                url = "https://api.marketaux.com/v1/news/all"
                
                # Get next month
                next_month = current_date + timedelta(days=30)
                if next_month > self.end_date:
                    next_month = self.end_date
                
                params = {
                    'api_token': api_key,
                    'countries': 'us,eu,gb,jp,au,ca,ch,nz',
                    'published_after': current_date.strftime('%Y-%m-%d'),
                    'published_before': next_month.strftime('%Y-%m-%d'),
                    'limit': 100,
                    'page': 1
                }
                
                response = requests.get(url, params=params, timeout=30)
                self.record_request('marketaux')
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and data['data']:
                        all_news.extend(data['data'])
                        logger.info(f"Downloaded {len(data['data'])} news articles for {current_date.strftime('%Y-%m')}")
                    else:
                        logger.warning(f"No news found for {current_date.strftime('%Y-%m')}")
                else:
                    logger.error(f"MarketAux API error: {response.status_code}")
                
                current_date = next_month + timedelta(days=1)
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error downloading MarketAux news for {current_date}: {e}")
                current_date += timedelta(days=30)
                continue
        
        # Save all news
        if all_news:
            df = pd.DataFrame(all_news)
            df['published_at'] = pd.to_datetime(df['published_at'])
            filename = "data/economic/marketaux/economic_news.csv"
            df.to_csv(filename, index=False)
            logger.info(f"Saved {len(all_news)} total news articles")
    
    def download_newsdata_news(self):
        """Download NewsData.io economic news"""
        logger.info("Starting NewsData.io news download...")
        
        try:
            if not self.check_rate_limit('newsdata'):
                time.sleep(60)
                return
            
            api_key = self.get_next_api_key('newsdata')
            url = "https://newsdata.io/api/1/archive"
            
            # Download in monthly batches
            current_date = self.start_date
            all_news = []
            
            while current_date <= self.end_date:
                try:
                    next_month = current_date + timedelta(days=30)
                    if next_month > self.end_date:
                        next_month = self.end_date
                    
                    params = {
                        'apikey': api_key,
                        'q': 'economy OR inflation OR GDP OR unemployment OR interest rate OR central bank OR Federal Reserve OR ECB OR BOJ OR BOE',
                        'from_date': current_date.strftime('%Y-%m-%d'),
                        'to_date': next_month.strftime('%Y-%m-%d'),
                        'language': 'en',
                        'country': 'us,gb,eu,jp,au,ca,ch,nz'
                    }
                    
                    response = requests.get(url, params=params, timeout=30)
                    self.record_request('newsdata')
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'results' in data and data['results']:
                            all_news.extend(data['results'])
                            logger.info(f"Downloaded {len(data['results'])} news articles for {current_date.strftime('%Y-%m')}")
                        else:
                            logger.warning(f"No news found for {current_date.strftime('%Y-%m')}")
                    else:
                        logger.error(f"NewsData API error: {response.status_code}")
                    
                    current_date = next_month + timedelta(days=1)
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error downloading NewsData for {current_date}: {e}")
                    current_date += timedelta(days=30)
                    continue
            
            # Save all news
            if all_news:
                df = pd.DataFrame(all_news)
                df['pubDate'] = pd.to_datetime(df['pubDate'])
                filename = "data/economic/newsdata/economic_news.csv"
                df.to_csv(filename, index=False)
                logger.info(f"Saved {len(all_news)} total news articles")
                
        except Exception as e:
            logger.error(f"Error downloading NewsData: {e}")
    
    def run_comprehensive_download(self):
        """Run all downloads"""
        logger.info("Starting comprehensive economic data download...")
        logger.info(f"Date range: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        
        # Download in order of importance
        self.download_fred_data()
        self.download_fmp_economic_calendar()
        self.download_polygon_data()
        self.download_marketaux_news()
        self.download_newsdata_news()
        
        logger.info("Comprehensive economic data download completed!")

if __name__ == "__main__":
    downloader = ComprehensiveEconomicDownloader()
    downloader.run_comprehensive_download()

