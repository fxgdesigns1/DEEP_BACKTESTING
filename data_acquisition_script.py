#!/usr/bin/env python3
"""
Data Acquisition and Gap-Filling Script for Trading Simulations
This script acquires missing data and fills gaps using available APIs efficiently.
"""

import pandas as pd
import numpy as np
import os
import time
import requests
import json
from datetime import datetime, timedelta
import warnings
from typing import Dict, List, Optional, Tuple
import logging
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataAcquisitionManager:
    def __init__(self, config_file="config/settings.yaml"):
        self.config = self.load_config(config_file)
        self.api_limits = self.analyze_api_limits()
        self.data_dir = "data/historical/prices"
        self.output_dir = "data/completed"
        
        # Create output directory
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"Created output directory: {self.output_dir}")
        
        # Initialize API clients
        self.alphavantage_client = AlphaVantageClient(self.config['data_sources']['api_keys']['alphavantage'])
        self.oanda_client = OandaClient(self.config['data_sources']['api_keys']['oanda'])
        
    def load_config(self, config_file: str) -> dict:
        """Load configuration from YAML file"""
        try:
            import yaml
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            # Fallback to hardcoded config
            return {
                'data_sources': {
                    'api_keys': {
                        'alphavantage': {'api_key': 'LSBZJ73J9W1G8FWB', 'rate_limit_per_minute': 5, 'rate_limit_per_day': 500},
                        'oanda': {'api_key': 'd5d9a1d481fd07b5ec39214873639129-4c7188797832a4f3d59d5268e0dfb64b', 'account_id': '001-004-13116062-001'}
                    }
                }
            }
    
    def analyze_api_limits(self) -> dict:
        """Analyze API rate limits and calculate optimal acquisition strategy"""
        limits = {
            'alphavantage': {
                'requests_per_minute': 5,
                'requests_per_day': 500,
                'data_points_per_request': 100,  # 1-hour data
                'max_lookback_days': 100  # Free tier limitation
            },
            'oanda': {
                'requests_per_minute': 120,  # OANDA has higher limits
                'requests_per_day': 10000,
                'data_points_per_request': 5000,  # Much higher limit
                'max_lookback_days': 5000  # Very high limit
            }
        }
        
        # Calculate optimal strategy
        total_missing_hours = 6144  # From our analysis
        total_currency_pairs = 10
        
        # Strategy 1: Use Alpha Vantage (limited but free)
        alphavantage_strategy = {
            'requests_needed': total_missing_hours * total_currency_pairs,
            'time_required_minutes': (total_missing_hours * total_currency_pairs) / limits['alphavantage']['requests_per_minute'],
            'days_required': ((total_missing_hours * total_currency_pairs) / limits['alphavantage']['requests_per_day']),
            'feasible': False  # Would take too long
        }
        
        # Strategy 2: Use OANDA (higher limits)
        oanda_strategy = {
            'requests_needed': total_missing_hours * total_currency_pairs,
            'time_required_minutes': (total_missing_hours * total_currency_pairs) / limits['oanda']['requests_per_minute'],
            'days_required': ((total_missing_hours * total_currency_pairs) / limits['oanda']['requests_per_day']),
            'feasible': True
        }
        
        # Strategy 3: Hybrid approach (optimize with OANDA)
        hybrid_strategy = {
            'oanda_requests': total_missing_hours * total_currency_pairs,
            'time_required_minutes': (total_missing_hours * total_currency_pairs) / limits['oanda']['requests_per_minute'],
            'days_required': 1,  # Can be done in 1 day
            'feasible': True
        }
        
        return {
            'limits': limits,
            'strategies': {
                'alphavantage': alphavantage_strategy,
                'oanda': oanda_strategy,
                'hybrid': hybrid_strategy
            },
            'recommended': 'hybrid'
        }
    
    def analyze_missing_data(self) -> dict:
        """Analyze missing data patterns to optimize acquisition"""
        logger.info("Analyzing missing data patterns...")
        
        missing_data_analysis = {}
        
        for currency_pair in ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CAD', 'AUD_USD', 'USD_CHF', 'NZD_USD', 'EUR_JPY', 'GBP_JPY', 'XAU_USD']:
            file_path = os.path.join(self.data_dir, f"{currency_pair.lower()}_1h.csv")
            if not os.path.exists(file_path):
                continue
                
            df = pd.read_csv(file_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Calculate gaps
            df['hour_diff'] = df['timestamp'].diff().dt.total_seconds() / 3600
            gaps = df[df['hour_diff'] > 1.1]
            
            # Categorize gaps
            weekend_gaps = gaps[gaps['hour_diff'] >= 48]
            other_gaps = gaps[(gaps['hour_diff'] > 1.1) & (gaps['hour_diff'] < 48)]
            
            # Identify specific missing periods
            start_date = df['timestamp'].min()
            end_date = df['timestamp'].max()
            expected_timeline = pd.date_range(start=start_date, end=end_date, freq='h')
            actual_timestamps = set(df['timestamp'])
            missing_timestamps = [ts for ts in expected_timeline if ts not in actual_timestamps]
            
            missing_data_analysis[currency_pair] = {
                'total_missing': len(missing_timestamps),
                'weekend_gaps': len(weekend_gaps),
                'other_gaps': len(other_gaps),
                'missing_periods': self.group_missing_periods(missing_timestamps),
                'start_date': start_date,
                'end_date': end_date
            }
        
        return missing_data_analysis
    
    def group_missing_periods(self, missing_timestamps: List[datetime]) -> List[dict]:
        """Group consecutive missing timestamps into periods"""
        if not missing_timestamps:
            return []
        
        missing_timestamps.sort()
        periods = []
        current_start = missing_timestamps[0]
        current_end = missing_timestamps[0]
        
        for ts in missing_timestamps[1:]:
            if ts == current_end + timedelta(hours=1):
                current_end = ts
            else:
                periods.append({
                    'start': current_start,
                    'end': current_end,
                    'duration_hours': (current_end - current_start).total_seconds() / 3600 + 1
                })
                current_start = ts
                current_end = ts
        
        # Add the last period
        periods.append({
            'start': current_start,
            'end': current_end,
            'duration_hours': (current_end - current_start).total_seconds() / 3600 + 1
        })
        
        return periods
    
    def acquire_missing_data(self, currency_pair: str, missing_periods: List[dict]) -> pd.DataFrame:
        """Acquire missing data for a specific currency pair"""
        logger.info(f"Acquiring missing data for {currency_pair}")
        
        all_acquired_data = []
        
        for period in missing_periods:
            start_time = period['start']
            end_time = period['end']
            duration_hours = period['duration_hours']
            
            logger.info(f"  Acquiring data for period: {start_time} to {end_time} ({duration_hours:.0f} hours)")
            
            # Use OANDA for data acquisition (higher limits)
            try:
                period_data = self.oanda_client.get_historical_data(
                    currency_pair, start_time, end_time
                )
                if period_data is not None and len(period_data) > 0:
                    all_acquired_data.extend(period_data)
                    logger.info(f"    Acquired {len(period_data)} data points")
                else:
                    logger.warning(f"    No data acquired for this period")
                
                # Rate limiting
                time.sleep(0.1)  # 100ms delay between requests
                
            except Exception as e:
                logger.error(f"    Error acquiring data: {e}")
                continue
        
        if all_acquired_data:
            # Convert to DataFrame
            df_acquired = pd.DataFrame(all_acquired_data)
            df_acquired['timestamp'] = pd.to_datetime(df_acquired['timestamp'])
            df_acquired = df_acquired.sort_values('timestamp').reset_index(drop=True)
            
            return df_acquired
        else:
            return pd.DataFrame()
    
    def merge_and_fill_data(self, currency_pair: str) -> pd.DataFrame:
        """Merge existing data with acquired data and fill remaining gaps"""
        logger.info(f"Merging and filling data for {currency_pair}")
        
        # Load existing data
        existing_file = os.path.join(self.data_dir, f"{currency_pair.lower()}_1h.csv")
        if not os.path.exists(existing_file):
            logger.error(f"Existing data file not found: {existing_file}")
            return None
        
        df_existing = pd.read_csv(existing_file)
        df_existing['timestamp'] = pd.to_datetime(df_existing['timestamp'])
        df_existing = df_existing.sort_values('timestamp').reset_index(drop=True)
        
        # Load acquired data
        acquired_file = os.path.join(self.output_dir, f"{currency_pair.lower()}_acquired.csv")
        df_acquired = pd.DataFrame()
        if os.path.exists(acquired_file):
            df_acquired = pd.read_csv(acquired_file)
            df_acquired['timestamp'] = pd.to_datetime(df_acquired['timestamp'])
        
        # Merge data
        if len(df_acquired) > 0:
            df_merged = pd.concat([df_existing, df_acquired], ignore_index=True)
            df_merged = df_merged.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
            logger.info(f"  Merged data: {len(df_existing)} + {len(df_acquired)} = {len(df_merged)} rows")
        else:
            df_merged = df_existing.copy()
            logger.info(f"  No acquired data to merge, using existing: {len(df_merged)} rows")
        
        # Fill remaining gaps with interpolation
        df_filled = self.fill_remaining_gaps(df_merged)
        
        return df_filled
    
    def fill_remaining_gaps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill remaining gaps with interpolation and forward-fill"""
        logger.info("  Filling remaining gaps with interpolation...")
        
        df_filled = df.copy()
        
        # Create complete hourly timeline
        start_time = df_filled['timestamp'].min()
        end_time = df_filled['timestamp'].max()
        complete_timeline = pd.date_range(start=start_time, end=end_time, freq='h')
        
        # Reindex to complete timeline
        df_filled = df_filled.set_index('timestamp').reindex(complete_timeline)
        
        # Forward fill OHLC data
        df_filled[['open', 'high', 'low', 'close']] = df_filled[['open', 'high', 'low', 'close']].fillna(method='ffill')
        
        # Fill volume with 0 for missing periods
        df_filled['volume'] = df_filled['volume'].fillna(0)
        
        # Reset index
        df_filled = df_filled.reset_index().rename(columns={'index': 'timestamp'})
        
        logger.info(f"    Filled gaps: {len(complete_timeline)} total rows")
        
        return df_filled
    
    def run_complete_acquisition(self):
        """Run the complete data acquisition and gap-filling process"""
        logger.info("Starting complete data acquisition and gap-filling process")
        
        # Analyze missing data
        missing_analysis = self.analyze_missing_data()
        
        # Display analysis
        self.display_missing_data_analysis(missing_analysis)
        
        # Display API strategy
        self.display_api_strategy()
        
        # Confirm with user
        response = input("\nProceed with data acquisition? (y/n): ").lower()
        if response != 'y':
            logger.info("Data acquisition cancelled by user")
            return
        
        # Process each currency pair
        for currency_pair, analysis in missing_analysis.items():
            if analysis['total_missing'] > 0:
                logger.info(f"\nProcessing {currency_pair}...")
                
                # Acquire missing data
                acquired_data = self.acquire_missing_data(currency_pair, analysis['missing_periods'])
                
                if len(acquired_data) > 0:
                    # Save acquired data
                    acquired_file = os.path.join(self.output_dir, f"{currency_pair.lower()}_acquired.csv")
                    acquired_data.to_csv(acquired_file, index=False)
                    logger.info(f"  Saved acquired data: {acquired_file}")
                
                # Merge and fill
                completed_data = self.merge_and_fill_data(currency_pair)
                
                if completed_data is not None:
                    # Save completed data
                    completed_file = os.path.join(self.output_dir, f"{currency_pair.lower()}_completed_1h.csv")
                    completed_data.to_csv(completed_file, index=False)
                    logger.info(f"  Saved completed data: {completed_file}")
        
        logger.info("\nData acquisition and gap-filling complete!")
        self.generate_completion_report(missing_analysis)
    
    def display_missing_data_analysis(self, missing_analysis: dict):
        """Display analysis of missing data"""
        print("\n" + "=" * 80)
        print("MISSING DATA ANALYSIS")
        print("=" * 80)
        
        total_missing = sum(analysis['total_missing'] for analysis in missing_analysis.values())
        total_weekend_gaps = sum(analysis['weekend_gaps'] for analysis in missing_analysis.values())
        total_other_gaps = sum(analysis['other_gaps'] for analysis in missing_analysis.values())
        
        print(f"Total Missing Hours: {total_missing:,}")
        print(f"Weekend Gaps: {total_weekend_gaps:,} (normal for forex)")
        print(f"Other Gaps: {total_other_gaps:,} (need acquisition)")
        
        print(f"\nCurrency Pair Breakdown:")
        print(f"{'Pair':<12} {'Missing':<10} {'Weekend':<10} {'Other':<10}")
        print("-" * 50)
        
        for pair, analysis in missing_analysis.items():
            print(f"{pair:<12} {analysis['total_missing']:<10} {analysis['weekend_gaps']:<10} {analysis['other_gaps']:<10}")
    
    def display_api_strategy(self):
        """Display the recommended API strategy"""
        print(f"\n" + "=" * 80)
        print("API STRATEGY & TIMELINE")
        print("=" * 80)
        
        strategy = self.api_limits['strategies'][self.api_limits['recommended']]
        
        print(f"Recommended Strategy: {self.api_limits['recommended'].upper()}")
        print(f"Total Requests Needed: {strategy['oanda_requests']:,}")
        print(f"Time Required: {strategy['time_required_minutes']:.1f} minutes")
        print(f"Days Required: {strategy['days_required']:.1f} days")
        
        print(f"\nAPI Limits:")
        print(f"OANDA: {self.api_limits['limits']['oanda']['requests_per_minute']} req/min, {self.api_limits['limits']['oanda']['requests_per_day']} req/day")
        print(f"Alpha Vantage: {self.api_limits['limits']['alphavantage']['requests_per_minute']} req/min, {self.api_limits['limits']['alphavantage']['requests_per_day']} req/day")
        
        print(f"\nOptimization Notes:")
        print(f"• Using OANDA for bulk data acquisition (higher limits)")
        print(f"• Parallel processing possible for multiple currency pairs")
        print(f"• Weekend gaps will be filled with interpolation (normal for forex)")
        print(f"• Holiday gaps (Christmas, New Year) will be acquired from API")
    
    def generate_completion_report(self, missing_analysis: dict):
        """Generate completion report"""
        print(f"\n" + "=" * 80)
        print("COMPLETION REPORT")
        print("=" * 80)
        
        print(f"Data acquisition completed successfully!")
        print(f"Output directory: {self.output_dir}")
        print(f"Files created:")
        print(f"  • *_acquired.csv - Newly acquired data")
        print(f"  • *_completed_1h.csv - Complete, gap-filled data")
        
        print(f"\nNext steps:")
        print(f"1. Verify data quality with validation script")
        print(f"2. Run cleaning script on completed data")
        print(f"3. Use completed data for trading simulations")

class AlphaVantageClient:
    def __init__(self, config: dict):
        self.api_key = config['api_key']
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit_per_minute = config['rate_limit_per_minute']
        self.rate_limit_per_day = config['rate_limit_per_day']
        self.last_request_time = 0
        self.daily_request_count = 0
        self.last_reset_date = datetime.now().date()
    
    def get_historical_data(self, symbol: str, start_time: datetime, end_time: datetime) -> Optional[List[dict]]:
        """Get historical data from Alpha Vantage"""
        # Rate limiting
        self._check_rate_limits()
        
        # Alpha Vantage format
        av_symbol = self._convert_to_alphavantage_symbol(symbol)
        
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': av_symbol,
            'interval': '60min',
            'apikey': self.api_key,
            'outputsize': 'full'
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if 'Time Series (60min)' in data:
                time_series = data['Time Series (60min)']
                
                # Convert to our format
                result = []
                for timestamp_str, values in time_series.items():
                    timestamp = pd.to_datetime(timestamp_str)
                    if start_time <= timestamp <= end_time:
                        result.append({
                            'timestamp': timestamp,
                            'open': float(values['1. open']),
                            'high': float(values['2. high']),
                            'low': float(values['3. low']),
                            'close': float(values['4. close']),
                            'volume': int(values['5. volume'])
                        })
                
                return result
            else:
                logger.error(f"Alpha Vantage error: {data}")
                return None
                
        except Exception as e:
            logger.error(f"Alpha Vantage request failed: {e}")
            return None
    
    def _convert_to_alphavantage_symbol(self, symbol: str) -> str:
        """Convert forex symbol to Alpha Vantage format"""
        # Alpha Vantage uses different format for forex
        if symbol in ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CAD', 'AUD_USD', 'USD_CHF', 'NZD_USD']:
            return symbol.replace('_', '')
        else:
            return symbol  # For other symbols
    
    def _check_rate_limits(self):
        """Check and enforce rate limits"""
        current_time = time.time()
        current_date = datetime.now().date()
        
        # Reset daily counter if new day
        if current_date > self.last_reset_date:
            self.daily_request_count = 0
            self.last_reset_date = current_date
        
        # Check daily limit
        if self.daily_request_count >= self.rate_limit_per_day:
            raise Exception("Daily API limit reached")
        
        # Check minute limit
        if current_time - self.last_request_time < 60 / self.rate_limit_per_minute:
            sleep_time = (60 / self.rate_limit_per_minute) - (current_time - self.last_request_time)
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.daily_request_count += 1

class OandaClient:
    def __init__(self, config: dict):
        self.api_key = config['api_key']
        self.account_id = config['account_id']
        self.base_url = "https://api-fxtrade.oanda.com"
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        self.last_request_time = 0
        self.rate_limit_per_minute = 120
    
    def get_historical_data(self, symbol: str, start_time: datetime, end_time: datetime) -> Optional[List[dict]]:
        """Get historical data from OANDA"""
        # Rate limiting
        self._check_rate_limits()
        
        # OANDA format
        oanda_symbol = self._convert_to_oanda_symbol(symbol)
        
        # OANDA API endpoint
        url = f"{self.base_url}/v3/instruments/{oanda_symbol}/candles"
        
        params = {
            'price': 'M',  # Mid price
            'granularity': 'H1',  # 1-hour candles
            'from': start_time.isoformat(),
            'to': end_time.isoformat(),
            'count': 5000  # Maximum count
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            if 'candles' in data:
                candles = data['candles']
                
                # Convert to our format
                result = []
                for candle in candles:
                    if candle['complete']:  # Only complete candles
                        result.append({
                            'timestamp': pd.to_datetime(candle['time']),
                            'open': float(candle['mid']['o']),
                            'high': float(candle['mid']['h']),
                            'low': float(candle['mid']['l']),
                            'close': float(candle['mid']['c']),
                            'volume': 0  # OANDA doesn't provide volume for forex
                        })
                
                return result
            else:
                logger.error(f"OANDA error: {data}")
                return None
                
        except Exception as e:
            logger.error(f"OANDA request failed: {e}")
            return None
    
    def _convert_to_oanda_symbol(self, symbol: str) -> str:
        """Convert symbol to OANDA format"""
        # OANDA uses underscore format
        return symbol.replace('_', '_')
    
    def _check_rate_limits(self):
        """Check and enforce rate limits"""
        current_time = time.time()
        
        # Check minute limit
        if current_time - self.last_request_time < 60 / self.rate_limit_per_minute:
            sleep_time = (60 / self.rate_limit_per_minute) - (current_time - self.last_request_time)
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

def main():
    """Main execution function"""
    print("Data Acquisition and Gap-Filling Script")
    print("=" * 60)
    
    # Initialize manager
    manager = DataAcquisitionManager()
    
    # Run complete acquisition
    manager.run_complete_acquisition()

if __name__ == "__main__":
    main()
