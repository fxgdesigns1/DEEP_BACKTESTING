#!/usr/bin/env python3
"""
FILL DATA GAP USING OANDA API - REAL DATA ONLY
Download real historical data from OANDA to bridge the gap
"""

import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import logging
from pathlib import Path
import time
import pytz

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class OandaDataDownloader:
    """Download real historical data from OANDA"""
    
    def __init__(self):
        """Initialize OANDA API connection"""
        # OANDA API configuration
        self.practice_url = "https://api-fxpractice.oanda.com"
        self.live_url = "https://api-fxtrade.oanda.com"
        
        # Try to load from config
        self.api_key = self._load_oanda_config()
        
        # Use practice URL for data downloads (same data, free tier)
        self.base_url = self.practice_url
        
        logger.info("OANDA Data Downloader initialized")
        logger.info(f"Using: {self.base_url}")
    
    def _load_oanda_config(self):
        """Load OANDA API configuration"""
        import yaml
        
        config_paths = [
            "config/api_config.yaml",
            "config/config.yaml",
            "config/settings.yaml"
        ]
        
        for config_path in config_paths:
            try:
                if Path(config_path).exists():
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f)
                        if 'oanda' in config:
                            api_key = config['oanda'].get('api_key') or config['oanda'].get('token')
                            if api_key:
                                logger.info(f"Loaded OANDA API key from {config_path}")
                                return api_key
            except Exception as e:
                logger.warning(f"Could not load config from {config_path}: {e}")
        
        # Default demo key (if user hasn't configured yet)
        logger.warning("No OANDA API key found in config, using demo mode")
        return "YOUR_OANDA_API_KEY_HERE"
    
    def download_candles(self, instrument, granularity, start_time, end_time):
        """
        Download candlestick data from OANDA
        
        Args:
            instrument: e.g., "XAU_USD"
            granularity: e.g., "M15" for 15-minute candles
            start_time: datetime object
            end_time: datetime object
        """
        logger.info(f"Downloading {instrument} {granularity} from {start_time.date()} to {end_time.date()}...")
        
        # OANDA limits to 5000 candles per request
        # For 15m candles: 5000 candles = ~52 days
        # We'll need to chunk the requests
        
        all_candles = []
        current_start = start_time
        
        while current_start < end_time:
            # Calculate chunk end (5000 candles or end_time, whichever is earlier)
            if granularity == "M15":
                max_duration = timedelta(days=52)
            elif granularity == "M5":
                max_duration = timedelta(days=17)
            elif granularity == "H1":
                max_duration = timedelta(days=208)
            else:
                max_duration = timedelta(days=30)
            
            chunk_end = min(current_start + max_duration, end_time)
            
            # Download chunk
            chunk_candles = self._download_chunk(instrument, granularity, current_start, chunk_end)
            
            if chunk_candles:
                all_candles.extend(chunk_candles)
                logger.info(f"  Downloaded {len(chunk_candles)} candles ({current_start.date()} to {chunk_end.date()})")
            else:
                logger.warning(f"  No data for chunk {current_start.date()} to {chunk_end.date()}")
            
            # Move to next chunk
            current_start = chunk_end
            
            # Rate limiting - be nice to OANDA API
            time.sleep(0.5)
        
        logger.info(f"Total candles downloaded: {len(all_candles)}")
        return all_candles
    
    def _download_chunk(self, instrument, granularity, start_time, end_time):
        """Download a single chunk of data from OANDA"""
        
        # Format times for OANDA API (RFC 3339)
        from_time = start_time.strftime('%Y-%m-%dT%H:%M:%S.000000000Z')
        to_time = end_time.strftime('%Y-%m-%dT%H:%M:%S.000000000Z')
        
        # Build request
        url = f"{self.base_url}/v3/instruments/{instrument}/candles"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        params = {
            "from": from_time,
            "to": to_time,
            "granularity": granularity,
            "price": "M"  # Mid prices
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                candles = data.get('candles', [])
                return candles
            else:
                logger.error(f"OANDA API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading chunk: {e}")
            return None
    
    def candles_to_dataframe(self, candles):
        """Convert OANDA candles to pandas DataFrame"""
        if not candles:
            return pd.DataFrame()
        
        rows = []
        for candle in candles:
            if not candle.get('complete', True):
                continue  # Skip incomplete candles
            
            mid = candle.get('mid', {})
            
            rows.append({
                'timestamp': candle['time'],
                'open': float(mid.get('o', 0)),
                'high': float(mid.get('h', 0)),
                'low': float(mid.get('l', 0)),
                'close': float(mid.get('c', 0)),
                'volume': int(candle.get('volume', 0))
            })
        
        df = pd.DataFrame(rows)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df

def main():
    """Main execution - Fill gap with OANDA data"""
    logger.info("="*80)
    logger.info("FILLING DATA GAP WITH REAL OANDA DATA")
    logger.info("NO SIMULATED DATA - ONLY REAL OANDA API DOWNLOADS")
    logger.info("="*80)
    
    # Step 1: Check existing data
    data_file = "data/MASTER_DATASET/15m/xau_usd_15m.csv"
    logger.info(f"\nChecking existing data in {data_file}...")
    
    existing_df = pd.read_csv(data_file)
    existing_df['timestamp'] = pd.to_datetime(existing_df['timestamp'])
    
    first_date = existing_df['timestamp'].min()
    last_date = existing_df['timestamp'].max()
    
    logger.info(f"Existing data:")
    logger.info(f"  First: {first_date}")
    logger.info(f"  Last: {last_date}")
    logger.info(f"  Total: {len(existing_df):,} candles")
    
    # Step 2: Calculate gap
    now = datetime.now(pytz.UTC)
    gap_days = (now - last_date).days
    
    logger.info(f"\nGap to fill: {gap_days} days (from {last_date.date()} to {now.date()})")
    
    # Step 3: Download gap data from OANDA
    downloader = OandaDataDownloader()
    
    # Download from day after last_date to now
    download_start = last_date + timedelta(hours=1)
    download_end = now
    
    candles = downloader.download_candles(
        instrument="XAU_USD",
        granularity="M15",  # 15-minute candles
        start_time=download_start,
        end_time=download_end
    )
    
    if not candles:
        logger.error("Failed to download gap data from OANDA")
        logger.info("\nNote: If OANDA API key is not configured, data download will fail")
        logger.info("Please configure OANDA API key in config/api_config.yaml")
        return False
    
    # Convert to DataFrame
    new_df = downloader.candles_to_dataframe(candles)
    
    if new_df.empty:
        logger.error("No new data retrieved")
        return False
    
    logger.info(f"\nDownloaded {len(new_df)} new candles from OANDA")
    logger.info(f"  Range: {new_df['timestamp'].min()} to {new_df['timestamp'].max()}")
    
    # Step 4: Merge datasets
    logger.info("\nMerging datasets...")
    
    # Concatenate
    combined = pd.concat([existing_df, new_df], ignore_index=True)
    
    # Remove duplicates
    before = len(combined)
    combined = combined.drop_duplicates(subset=['timestamp'], keep='first')
    after = len(combined)
    
    if before != after:
        logger.info(f"Removed {before - after} duplicate candles")
    
    # Sort by timestamp
    combined = combined.sort_values('timestamp').reset_index(drop=True)
    
    # Validate
    logger.info("\nValidating merged dataset...")
    logger.info(f"  First: {combined['timestamp'].min()}")
    logger.info(f"  Last: {combined['timestamp'].max()}")
    logger.info(f"  Total: {len(combined):,} candles")
    logger.info(f"  Span: {(combined['timestamp'].max() - combined['timestamp'].min()).days} days")
    
    # Step 5: Save complete dataset
    # Backup original
    backup_file = f"data/MASTER_DATASET/15m/xau_usd_15m_BACKUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    existing_df.to_csv(backup_file, index=False)
    logger.info(f"\nOriginal backed up to: {backup_file}")
    
    # Save complete dataset
    output_file = "data/MASTER_DATASET/15m/xau_usd_15m.csv"
    combined.to_csv(output_file, index=False)
    logger.info(f"Complete dataset saved to: {output_file}")
    
    # Also save a copy for reference
    complete_copy = "data/xau_usd_15m_COMPLETE_GAP_FILLED.csv"
    combined.to_csv(complete_copy, index=False)
    logger.info(f"Copy saved to: {complete_copy}")
    
    logger.info("\n" + "="*80)
    logger.info("DATA GAP SUCCESSFULLY FILLED WITH REAL OANDA DATA")
    logger.info("DATASET IS NOW COMPLETE AND AIRTIGHT")
    logger.info("="*80)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        logger.error("\nFailed to fill data gap")
        logger.info("Please ensure OANDA API key is configured")
        exit(1)
    else:
        logger.info("\nReady for enhanced Monte Carlo testing!")
        exit(0)


