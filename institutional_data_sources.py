#!/usr/bin/env python3
"""
INSTITUTIONAL DATA SOURCES
Professional-grade data fetching from multiple institutional sources
"""

import pandas as pd
import numpy as np
import requests
import yfinance as yf
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class InstitutionalDataSources:
    def __init__(self):
        self.data_sources = {
            'yahoo_finance': {
                'name': 'Yahoo Finance',
                'rate_limit': 2000,  # requests per hour
                'reliability': 0.95,
                'coverage': 'excellent',
                'cost': 'free'
            },
            'alpha_vantage': {
                'name': 'Alpha Vantage',
                'rate_limit': 5,  # requests per minute (free tier)
                'reliability': 0.90,
                'coverage': 'good',
                'cost': 'free_tier_available'
            },
            'finnhub': {
                'name': 'Finnhub',
                'rate_limit': 60,  # requests per minute (free tier)
                'reliability': 0.92,
                'coverage': 'good',
                'cost': 'free_tier_available'
            },
            'polygon': {
                'name': 'Polygon.io',
                'rate_limit': 5,  # requests per minute (free tier)
                'reliability': 0.88,
                'coverage': 'excellent',
                'cost': 'free_tier_available'
            }
        }
        
        # API Keys (replace with your actual keys)
        self.api_keys = {
            'alpha_vantage': 'demo',  # Replace with real key
            'finnhub': 'demo',  # Replace with real key
            'polygon': 'demo'  # Replace with real key
        }
        
        # Currency pair mappings for different sources
        self.currency_mappings = {
            'yahoo_finance': {
                'EUR_USD': 'EURUSD=X',
                'GBP_USD': 'GBPUSD=X',
                'USD_JPY': 'USDJPY=X',
                'AUD_USD': 'AUDUSD=X',
                'USD_CAD': 'USDCAD=X',
                'USD_CHF': 'USDCHF=X',
                'NZD_USD': 'NZDUSD=X',
                'EUR_JPY': 'EURJPY=X',
                'GBP_JPY': 'GBPJPY=X',
                'XAU_USD': 'GC=F'  # Gold futures
            },
            'alpha_vantage': {
                'EUR_USD': 'EURUSD',
                'GBP_USD': 'GBPUSD',
                'USD_JPY': 'USDJPY',
                'AUD_USD': 'AUDUSD',
                'USD_CAD': 'USDCAD',
                'USD_CHF': 'USDCHF',
                'NZD_USD': 'NZDUSD',
                'EUR_JPY': 'EURJPY',
                'GBP_JPY': 'GBPJPY',
                'XAU_USD': 'XAUUSD'
            }
        }
    
    def fetch_yahoo_finance_data(self, currency_pair: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Fetch data from Yahoo Finance"""
        try:
            symbol = self.currency_mappings['yahoo_finance'].get(currency_pair)
            if not symbol:
                print(f"   ❌ No Yahoo Finance mapping for {currency_pair}")
                return None
            
            print(f"   📡 Fetching {currency_pair} from Yahoo Finance...")
            
            # Download data
            ticker = yf.Ticker(symbol)
            data = ticker.history(
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval='1h'
            )
            
            if data.empty:
                print(f"   ⚠️  No data returned from Yahoo Finance for {currency_pair}")
                return None
            
            # Convert to our format
            df = pd.DataFrame({
                'timestamp': data.index,
                'open': data['Open'],
                'high': data['High'],
                'low': data['Low'],
                'close': data['Close'],
                'volume': data['Volume']
            })
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.reset_index(drop=True)
            
            print(f"   ✅ Yahoo Finance: {len(df)} records for {currency_pair}")
            return df
            
        except Exception as e:
            print(f"   ❌ Yahoo Finance error for {currency_pair}: {e}")
            return None
    
    def fetch_alpha_vantage_data(self, currency_pair: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Fetch data from Alpha Vantage"""
        try:
            symbol = self.currency_mappings['alpha_vantage'].get(currency_pair)
            if not symbol:
                print(f"   ❌ No Alpha Vantage mapping for {currency_pair}")
                return None
            
            print(f"   📡 Fetching {currency_pair} from Alpha Vantage...")
            
            # Rate limiting
            time.sleep(12)  # 5 requests per minute = 12 seconds between requests
            
            api_key = self.api_keys['alpha_vantage']
            if api_key == 'demo':
                print(f"   ⚠️  Using demo API key - limited functionality")
                return None
            
            # Alpha Vantage API call
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'FX_INTRADAY',
                'from_symbol': symbol[:3],
                'to_symbol': symbol[3:],
                'interval': '60min',
                'apikey': api_key,
                'outputsize': 'full'
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'Error Message' in data:
                print(f"   ❌ Alpha Vantage error: {data['Error Message']}")
                return None
            
            if 'Note' in data:
                print(f"   ⚠️  Alpha Vantage rate limit: {data['Note']}")
                return None
            
            # Parse response
            time_series_key = f"Time Series (60min)"
            if time_series_key not in data:
                print(f"   ❌ No time series data in Alpha Vantage response")
                return None
            
            time_series = data[time_series_key]
            
            # Convert to DataFrame
            records = []
            for timestamp_str, values in time_series.items():
                timestamp = pd.to_datetime(timestamp_str)
                if start_date <= timestamp <= end_date:
                    records.append({
                        'timestamp': timestamp,
                        'open': float(values['1. open']),
                        'high': float(values['2. high']),
                        'low': float(values['3. low']),
                        'close': float(values['4. close']),
                        'volume': 0  # Alpha Vantage doesn't provide volume for FX
                    })
            
            if not records:
                print(f"   ⚠️  No data in specified date range from Alpha Vantage")
                return None
            
            df = pd.DataFrame(records)
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            print(f"   ✅ Alpha Vantage: {len(df)} records for {currency_pair}")
            return df
            
        except Exception as e:
            print(f"   ❌ Alpha Vantage error for {currency_pair}: {e}")
            return None
    
    def fetch_finnhub_data(self, currency_pair: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Fetch data from Finnhub"""
        try:
            print(f"   📡 Fetching {currency_pair} from Finnhub...")
            
            api_key = self.api_keys['finnhub']
            if api_key == 'demo':
                print(f"   ⚠️  Using demo API key - limited functionality")
                return None
            
            # Rate limiting
            time.sleep(1)  # 60 requests per minute
            
            # Finnhub API call for forex
            url = f"https://finnhub.io/api/v1/forex/candle"
            params = {
                'symbol': currency_pair.replace('_', ''),
                'resolution': '60',  # 1 hour
                'from': int(start_date.timestamp()),
                'to': int(end_date.timestamp()),
                'token': api_key
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('s') != 'ok':
                print(f"   ❌ Finnhub error: {data.get('s', 'Unknown error')}")
                return None
            
            # Parse response
            timestamps = data.get('t', [])
            opens = data.get('o', [])
            highs = data.get('h', [])
            lows = data.get('l', [])
            closes = data.get('c', [])
            volumes = data.get('v', [])
            
            if not timestamps:
                print(f"   ⚠️  No data returned from Finnhub for {currency_pair}")
                return None
            
            # Convert to DataFrame
            records = []
            for i, timestamp in enumerate(timestamps):
                records.append({
                    'timestamp': pd.to_datetime(timestamp, unit='s'),
                    'open': opens[i] if i < len(opens) else 0,
                    'high': highs[i] if i < len(highs) else 0,
                    'low': lows[i] if i < len(lows) else 0,
                    'close': closes[i] if i < len(closes) else 0,
                    'volume': volumes[i] if i < len(volumes) else 0
                })
            
            df = pd.DataFrame(records)
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            print(f"   ✅ Finnhub: {len(df)} records for {currency_pair}")
            return df
            
        except Exception as e:
            print(f"   ❌ Finnhub error for {currency_pair}: {e}")
            return None
    
    def fetch_polygon_data(self, currency_pair: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Fetch data from Polygon.io"""
        try:
            print(f"   📡 Fetching {currency_pair} from Polygon.io...")
            
            api_key = self.api_keys['polygon']
            if api_key == 'demo':
                print(f"   ⚠️  Using demo API key - limited functionality")
                return None
            
            # Rate limiting
            time.sleep(12)  # 5 requests per minute
            
            # Polygon.io API call
            symbol = f"C:{currency_pair.replace('_', '')}"
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/hour/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            params = {
                'adjusted': 'true',
                'sort': 'asc',
                'apikey': api_key
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('status') != 'OK':
                print(f"   ❌ Polygon.io error: {data.get('status', 'Unknown error')}")
                return None
            
            results = data.get('results', [])
            if not results:
                print(f"   ⚠️  No data returned from Polygon.io for {currency_pair}")
                return None
            
            # Convert to DataFrame
            records = []
            for result in results:
                records.append({
                    'timestamp': pd.to_datetime(result['t'], unit='ms'),
                    'open': result['o'],
                    'high': result['h'],
                    'low': result['l'],
                    'close': result['c'],
                    'volume': result['v']
                })
            
            df = pd.DataFrame(records)
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            print(f"   ✅ Polygon.io: {len(df)} records for {currency_pair}")
            return df
            
        except Exception as e:
            print(f"   ❌ Polygon.io error for {currency_pair}: {e}")
            return None
    
    def fetch_data_from_all_sources(self, currency_pair: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Try to fetch data from all available sources"""
        print(f"🌐 Fetching {currency_pair} data from multiple sources...")
        
        sources = [
            ('yahoo_finance', self.fetch_yahoo_finance_data),
            ('alpha_vantage', self.fetch_alpha_vantage_data),
            ('finnhub', self.fetch_finnhub_data),
            ('polygon', self.fetch_polygon_data)
        ]
        
        for source_name, fetch_function in sources:
            try:
                data = fetch_function(currency_pair, start_date, end_date)
                if data is not None and len(data) > 0:
                    print(f"   ✅ Successfully fetched data from {source_name}")
                    return data
            except Exception as e:
                print(f"   ❌ {source_name} failed: {e}")
                continue
        
        print(f"   ❌ All sources failed for {currency_pair}")
        return None
    
    def validate_fetched_data(self, df: pd.DataFrame, currency_pair: str) -> Dict[str, Any]:
        """Validate fetched data quality"""
        validation_results = {
            'valid': True,
            'issues': [],
            'quality_score': 10.0
        }
        
        if df.empty:
            validation_results['valid'] = False
            validation_results['issues'].append('Empty dataset')
            validation_results['quality_score'] = 0.0
            return validation_results
        
        # Check for required columns
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            validation_results['issues'].append(f'Missing columns: {missing_columns}')
            validation_results['quality_score'] -= 2.0
        
        # Check for null values
        null_counts = df.isnull().sum()
        if null_counts.any():
            validation_results['issues'].append(f'Null values found: {null_counts.to_dict()}')
            validation_results['quality_score'] -= 1.0
        
        # Check for negative prices
        price_columns = ['open', 'high', 'low', 'close']
        for col in price_columns:
            if col in df.columns and (df[col] <= 0).any():
                validation_results['issues'].append(f'Negative prices in {col}')
                validation_results['quality_score'] -= 2.0
        
        # Check OHLC relationships
        if all(col in df.columns for col in price_columns):
            ohlc_violations = df[
                (df['high'] < df['low']) |
                (df['open'] > df['high']) |
                (df['close'] > df['high']) |
                (df['open'] < df['low']) |
                (df['close'] < df['low'])
            ]
            if len(ohlc_violations) > 0:
                validation_results['issues'].append(f'OHLC violations: {len(ohlc_violations)}')
                validation_results['quality_score'] -= 3.0
        
        # Check for extreme price movements
        if 'close' in df.columns and len(df) > 1:
            price_changes = df['close'].pct_change().abs()
            extreme_moves = price_changes[price_changes > 0.1]  # 10% moves
            if len(extreme_moves) > 0:
                validation_results['issues'].append(f'Extreme price movements: {len(extreme_moves)}')
                validation_results['quality_score'] -= 1.0
        
        validation_results['quality_score'] = max(0.0, validation_results['quality_score'])
        
        if validation_results['quality_score'] < 7.0:
            validation_results['valid'] = False
        
        return validation_results
    
    def get_data_source_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for data sources based on requirements"""
        recommendations = {
            'for_retail_trading': {
                'primary': 'yahoo_finance',
                'backup': 'alpha_vantage',
                'reasoning': 'Free, reliable, good coverage for major pairs'
            },
            'for_institutional_trading': {
                'primary': 'polygon',
                'backup': 'finnhub',
                'reasoning': 'High frequency, low latency, institutional grade'
            },
            'for_backtesting': {
                'primary': 'yahoo_finance',
                'backup': 'alpha_vantage',
                'reasoning': 'Historical data availability, cost-effective'
            },
            'for_live_trading': {
                'primary': 'polygon',
                'backup': 'finnhub',
                'reasoning': 'Real-time data, low latency, high reliability'
            }
        }
        
        return recommendations

def main():
    """Test the data sources"""
    print("🏆 INSTITUTIONAL DATA SOURCES TEST")
    print("=" * 60)
    
    sources = InstitutionalDataSources()
    
    # Test with a recent date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    test_pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY']
    
    for pair in test_pairs:
        print(f"\n📊 Testing {pair}...")
        data = sources.fetch_data_from_all_sources(pair, start_date, end_date)
        
        if data is not None:
            validation = sources.validate_fetched_data(data, pair)
            print(f"   Data quality: {validation['quality_score']:.1f}/10")
            if validation['issues']:
                print(f"   Issues: {validation['issues']}")
        else:
            print(f"   ❌ No data available for {pair}")
    
    # Show recommendations
    print(f"\n📋 DATA SOURCE RECOMMENDATIONS:")
    recommendations = sources.get_data_source_recommendations()
    for use_case, rec in recommendations.items():
        print(f"   {use_case.replace('_', ' ').title()}: {rec['primary']} (backup: {rec['backup']})")

if __name__ == "__main__":
    main()

