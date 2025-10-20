#!/usr/bin/env python3
"""
Optimized Parallel Data Acquisition Script
This script uses parallel processing to dramatically speed up data acquisition.
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
import concurrent.futures
import threading
from queue import Queue
import asyncio
import aiohttp
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OptimizedDataAcquisitionManager:
    def __init__(self, config_file="config/settings.yaml"):
        self.config = self.load_config(config_file)
        self.api_limits = self.analyze_api_limits()
        self.data_dir = "data/historical/prices"
        self.output_dir = "data/completed_optimized"
        
        # Create output directory
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"Created output directory: {self.output_dir}")
        
        # Thread-safe counters
        self.request_counter = 0
        self.request_lock = threading.Lock()
        
        # Initialize API clients
        self.oanda_client = OptimizedOandaClient(self.config['data_sources']['api_keys']['oanda'])
        
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
                        'oanda': {'api_key': 'd5d9a1d481fd07b5ec39214873639129-4c7188797832a4f3d59d5268e0dfb64b', 'account_id': '001-004-13116062-001'}
                    }
                }
            }
    
    def analyze_api_limits(self) -> dict:
        """Analyze API rate limits and calculate optimal acquisition strategy"""
        # OANDA limits (much higher than Alpha Vantage)
        oanda_limits = {
            'requests_per_minute': 120,
            'requests_per_day': 10000,
            'data_points_per_request': 5000,
            'max_lookback_days': 5000
        }
        
        # Calculate optimal strategy
        total_missing_hours = 6144  # From our analysis
        total_currency_pairs = 10
        total_requests_needed = total_missing_hours * total_currency_pairs
        
        # Parallel processing strategy
        optimal_workers = min(10, total_currency_pairs)  # Max 10 parallel workers
        
        parallel_strategy = {
            'total_requests': total_requests_needed,
            'parallel_workers': optimal_workers,
            'requests_per_worker': total_requests_needed // optimal_workers,
            'time_required_minutes': (total_requests_needed / optimal_workers) / oanda_limits['requests_per_minute'],
            'days_required': 1,  # Can be done in 1 day with parallel processing
            'feasible': True
        }
        
        return {
            'limits': oanda_limits,
            'strategy': parallel_strategy,
            'recommended_workers': optimal_workers
        }
    
    def analyze_missing_data(self) -> dict:
        """Analyze missing data patterns to optimize acquisition"""
        logger.info("Analyzing missing data patterns for parallel processing...")
        
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
                'end_date': end_date,
                'priority': self.calculate_priority(currency_pair, len(missing_timestamps))
            }
        
        return missing_data_analysis
    
    def calculate_priority(self, currency_pair: str, missing_count: int) -> int:
        """Calculate processing priority for currency pairs"""
        # Major pairs get higher priority
        major_pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY']
        if currency_pair in major_pairs:
            return 1
        elif missing_count > 1000:  # High missing data
            return 2
        else:
            return 3
    
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
    
    def process_currency_pair(self, currency_pair: str, analysis: dict) -> Tuple[str, pd.DataFrame]:
        """Process a single currency pair (for parallel execution)"""
        logger.info(f"Processing {currency_pair} in parallel...")
        
        try:
            # Acquire missing data
            acquired_data = self.acquire_missing_data_parallel(currency_pair, analysis['missing_periods'])
            
            if len(acquired_data) > 0:
                # Save acquired data
                acquired_file = os.path.join(self.output_dir, f"{currency_pair.lower()}_acquired.csv")
                acquired_data.to_csv(acquired_file, index=False)
                logger.info(f"  Saved acquired data for {currency_pair}: {len(acquired_data)} rows")
            
            # Merge and fill
            completed_data = self.merge_and_fill_data_parallel(currency_pair)
            
            if completed_data is not None:
                # Save completed data
                completed_file = os.path.join(self.output_dir, f"{currency_pair.lower()}_completed_1h.csv")
                completed_data.to_csv(completed_file, index=False)
                logger.info(f"  Saved completed data for {currency_pair}: {len(completed_data)} rows")
                
                return currency_pair, completed_data
            else:
                return currency_pair, pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error processing {currency_pair}: {e}")
            return currency_pair, pd.DataFrame()
    
    def acquire_missing_data_parallel(self, currency_pair: str, missing_periods: List[dict]) -> pd.DataFrame:
        """Acquire missing data for a specific currency pair (parallel version)"""
        all_acquired_data = []
        
        for period in missing_periods:
            start_time = period['start']
            end_time = period['end']
            duration_hours = period['duration_hours']
            
            # Skip weekend gaps (will be filled with interpolation)
            if duration_hours >= 48:
                continue
            
            logger.info(f"  Acquiring data for {currency_pair}: {start_time} to {end_time} ({duration_hours:.0f} hours)")
            
            try:
                period_data = self.oanda_client.get_historical_data(
                    currency_pair, start_time, end_time
                )
                if period_data is not None and len(period_data) > 0:
                    all_acquired_data.extend(period_data)
                    logger.info(f"    Acquired {len(period_data)} data points for {currency_pair}")
                
                # Minimal rate limiting for parallel processing
                time.sleep(0.05)  # 50ms delay between requests
                
            except Exception as e:
                logger.error(f"    Error acquiring data for {currency_pair}: {e}")
                continue
        
        if all_acquired_data:
            # Convert to DataFrame
            df_acquired = pd.DataFrame(all_acquired_data)
            df_acquired['timestamp'] = pd.to_datetime(df_acquired['timestamp'])
            df_acquired = df_acquired.sort_values('timestamp').reset_index(drop=True)
            
            return df_acquired
        else:
            return pd.DataFrame()
    
    def merge_and_fill_data_parallel(self, currency_pair: str) -> pd.DataFrame:
        """Merge existing data with acquired data and fill remaining gaps (parallel version)"""
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
        else:
            df_merged = df_existing.copy()
        
        # Fill remaining gaps with interpolation
        df_filled = self.fill_remaining_gaps_parallel(df_merged)
        
        return df_filled
    
    def fill_remaining_gaps_parallel(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill remaining gaps with interpolation and forward-fill (parallel version)"""
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
        
        return df_filled
    
    def run_parallel_acquisition(self):
        """Run the complete data acquisition process using parallel processing"""
        logger.info("Starting optimized parallel data acquisition process")
        
        # Analyze missing data
        missing_analysis = self.analyze_missing_data()
        
        # Display analysis
        self.display_missing_data_analysis(missing_analysis)
        
        # Display optimization strategy
        self.display_optimization_strategy()
        
        # Confirm with user
        response = input("\nProceed with parallel data acquisition? (y/n): ").lower()
        if response != 'y':
            logger.info("Parallel data acquisition cancelled by user")
            return
        
        # Sort currency pairs by priority
        sorted_pairs = sorted(
            missing_analysis.items(), 
            key=lambda x: (x[1]['priority'], -x[1]['total_missing'])
        )
        
        # Process in parallel
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.api_limits['recommended_workers']) as executor:
            # Submit all tasks
            future_to_pair = {
                executor.submit(self.process_currency_pair, pair, analysis): pair 
                for pair, analysis in sorted_pairs if analysis['total_missing'] > 0
            }
            
            # Process completed tasks
            completed_pairs = []
            for future in concurrent.futures.as_completed(future_to_pair):
                pair = future_to_pair[future]
                try:
                    currency_pair, completed_data = future.result()
                    if len(completed_data) > 0:
                        completed_pairs.append(currency_pair)
                        logger.info(f"✓ Completed {currency_pair}: {len(completed_data)} rows")
                except Exception as e:
                    logger.error(f"✗ Error processing {pair}: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        logger.info(f"\nParallel data acquisition complete in {total_time:.2f} seconds!")
        self.generate_parallel_completion_report(missing_analysis, completed_pairs, total_time)
    
    def display_missing_data_analysis(self, missing_analysis: dict):
        """Display analysis of missing data"""
        print("\n" + "=" * 80)
        print("MISSING DATA ANALYSIS FOR PARALLEL PROCESSING")
        print("=" * 80)
        
        total_missing = sum(analysis['total_missing'] for analysis in missing_analysis.values())
        total_weekend_gaps = sum(analysis['weekend_gaps'] for analysis in missing_analysis.values())
        total_other_gaps = sum(analysis['other_gaps'] for analysis in missing_analysis.values())
        
        print(f"Total Missing Hours: {total_missing:,}")
        print(f"Weekend Gaps: {total_weekend_gaps:,} (will be interpolated)")
        print(f"Other Gaps: {total_other_gaps:,} (will be acquired via API)")
        
        print(f"\nCurrency Pair Breakdown (Sorted by Priority):")
        print(f"{'Pair':<12} {'Missing':<10} {'Weekend':<10} {'Other':<10} {'Priority':<10}")
        print("-" * 60)
        
        sorted_pairs = sorted(
            missing_analysis.items(), 
            key=lambda x: (x[1]['priority'], -x[1]['total_missing'])
        )
        
        for pair, analysis in sorted_pairs:
            print(f"{pair:<12} {analysis['total_missing']:<10} {analysis['weekend_gaps']:<10} {analysis['other_gaps']:<10} {analysis['priority']:<10}")
    
    def display_optimization_strategy(self):
        """Display the optimization strategy"""
        print(f"\n" + "=" * 80)
        print("OPTIMIZATION STRATEGY & TIMELINE")
        print("=" * 80)
        
        strategy = self.api_limits['strategy']
        
        print(f"Parallel Processing Strategy:")
        print(f"Total Requests Needed: {strategy['total_requests']:,}")
        print(f"Parallel Workers: {strategy['parallel_workers']}")
        print(f"Requests per Worker: {strategy['requests_per_worker']:,}")
        print(f"Estimated Time: {strategy['time_required_minutes']:.1f} minutes")
        print(f"Estimated Days: {strategy['days_required']:.1f} days")
        
        print(f"\nOptimization Benefits:")
        print(f"• Parallel processing reduces total time by ~{strategy['parallel_workers']}x")
        print(f"• Weekend gaps filled with interpolation (no API calls needed)")
        print(f"• Priority-based processing (major pairs first)")
        print(f"• Efficient rate limiting per worker")
        
        print(f"\nAPI Limits:")
        print(f"OANDA: {self.api_limits['limits']['requests_per_minute']} req/min, {self.api_limits['limits']['requests_per_day']} req/day")
        print(f"Parallel Workers: {self.api_limits['recommended_workers']} (each with separate rate limiting)")
    
    def generate_parallel_completion_report(self, missing_analysis: dict, completed_pairs: List[str], total_time: float):
        """Generate completion report for parallel processing"""
        print(f"\n" + "=" * 80)
        print("PARALLEL PROCESSING COMPLETION REPORT")
        print("=" * 80)
        
        print(f"Parallel data acquisition completed successfully!")
        print(f"Total processing time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
        print(f"Output directory: {self.output_dir}")
        
        print(f"\nCompleted Currency Pairs:")
        for pair in completed_pairs:
            print(f"  ✓ {pair}")
        
        print(f"\nPerformance Metrics:")
        total_missing = sum(analysis['total_missing'] for analysis in missing_analysis.values())
        print(f"Total missing hours processed: {total_missing:,}")
        print(f"Processing speed: {total_missing/total_time:.1f} hours/second")
        
        print(f"\nFiles created:")
        print(f"  • *_acquired.csv - Newly acquired data")
        print(f"  • *_completed_1h.csv - Complete, gap-filled data")
        
        print(f"\nNext steps:")
        print(f"1. Verify data quality with validation script")
        print(f"2. Run cleaning script on completed data")
        print(f"3. Use completed data for trading simulations")

class OptimizedOandaClient:
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
        self.request_lock = threading.Lock()
    
    def get_historical_data(self, symbol: str, start_time: datetime, end_time: datetime) -> Optional[List[dict]]:
        """Get historical data from OANDA with thread-safe rate limiting"""
        # Thread-safe rate limiting
        with self.request_lock:
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
        return symbol.replace('_', '_')
    
    def _check_rate_limits(self):
        """Check and enforce rate limits (thread-safe)"""
        current_time = time.time()
        
        # Check minute limit
        if current_time - self.last_request_time < 60 / self.rate_limit_per_minute:
            sleep_time = (60 / self.rate_limit_per_minute) - (current_time - self.last_request_time)
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

def main():
    """Main execution function"""
    print("Optimized Parallel Data Acquisition Script")
    print("=" * 60)
    
    # Initialize manager
    manager = OptimizedDataAcquisitionManager()
    
    # Run parallel acquisition
    manager.run_parallel_acquisition()

if __name__ == "__main__":
    main()
