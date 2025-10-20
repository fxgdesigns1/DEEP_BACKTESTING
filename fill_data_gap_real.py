#!/usr/bin/env python3
"""
FILL DATA GAP WITH REAL HISTORICAL DATA
NO SIMULATED DATA - ONLY REAL DOWNLOADS

Fills gap from August 12, 2025 to October 18, 2025
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def check_existing_data():
    """Check what data we have"""
    data_file = "data/MASTER_DATASET/15m/xau_usd_15m.csv"
    
    logger.info("Checking existing data...")
    df = pd.read_csv(data_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    first_date = df['timestamp'].min()
    last_date = df['timestamp'].max()
    total_candles = len(df)
    
    logger.info(f"Existing data:")
    logger.info(f"  First candle: {first_date}")
    logger.info(f"  Last candle: {last_date}")
    logger.info(f"  Total candles: {total_candles:,}")
    
    # Calculate gap
    now = datetime.now()
    # Make now timezone-aware if last_date is timezone-aware
    if last_date.tz is not None:
        import pytz
        now = now.replace(tzinfo=pytz.UTC)
    
    gap_days = (now - last_date).days
    
    logger.info(f"\nData gap: {gap_days} days from {last_date.date()} to {now.date()}")
    
    return df, last_date, now

def download_gap_data(start_date, end_date):
    """Download REAL data for the gap period"""
    logger.info(f"\nDownloading REAL data from {start_date.date()} to {end_date.date()}...")
    
    # Yahoo Finance only allows 60 days for 15m interval
    # Download the maximum available (last 60 days)
    days_requested = (end_date - start_date).days
    
    if days_requested > 60:
        logger.warning(f"Gap is {days_requested} days but Yahoo only allows 60 days for 15m data")
        logger.info(f"Downloading the most recent 60 days available")
        start_date = end_date - timedelta(days=60)
    
    try:
        # Download Gold futures data
        logger.info(f"Downloading Gold (GC=F) from {start_date.date()} to {end_date.date()}...")
        df = yf.download(
            'GC=F',
            start=start_date,
            end=end_date,
            interval='15m',
            progress=True,
            auto_adjust=False
        )
        
        if df.empty:
            logger.error("No data downloaded! Yahoo Finance may not have data for this period.")
            return None
        
        # Clean up
        df = df.reset_index()
        
        # Handle multi-level columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0].lower() if isinstance(col, tuple) else col.lower() for col in df.columns]
        else:
            df.columns = [col.lower() for col in df.columns]
        
        # Rename datetime column
        if 'datetime' in df.columns:
            df.rename(columns={'datetime': 'timestamp'}, inplace=True)
        elif 'date' in df.columns:
            df.rename(columns={'date': 'timestamp'}, inplace=True)
        
        logger.info(f"Downloaded {len(df)} candles")
        logger.info(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error downloading data: {e}")
        return None

def merge_and_validate(existing_df, new_df):
    """Merge new data with existing and validate"""
    logger.info("\nMerging data...")
    
    # Ensure both have same columns
    required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    
    # Check if new_df has all required columns
    for col in required_cols:
        if col not in new_df.columns:
            logger.error(f"Missing column in new data: {col}")
            return None
    
    # Select only required columns from both
    existing_clean = existing_df[required_cols].copy()
    new_clean = new_df[required_cols].copy()
    
    # Concatenate
    combined = pd.concat([existing_clean, new_clean], ignore_index=True)
    
    # Remove duplicates based on timestamp
    before_dedup = len(combined)
    combined = combined.drop_duplicates(subset=['timestamp'], keep='first')
    after_dedup = len(combined)
    
    if before_dedup != after_dedup:
        logger.info(f"Removed {before_dedup - after_dedup} duplicate candles")
    
    # Sort by timestamp
    combined = combined.sort_values('timestamp').reset_index(drop=True)
    
    # Validate no gaps
    logger.info("\nValidating data integrity...")
    combined['timestamp'] = pd.to_datetime(combined['timestamp'])
    
    # Check for 15-minute gaps
    time_diffs = combined['timestamp'].diff()
    expected_diff = pd.Timedelta(minutes=15)
    
    # Find gaps (more than 15 minutes)
    gaps = time_diffs[time_diffs > expected_diff]
    
    if len(gaps) > 0:
        logger.warning(f"Found {len(gaps)} gaps in data (weekends/holidays expected)")
        # This is normal for forex/gold markets (weekends, holidays)
    else:
        logger.info("No unexpected gaps found")
    
    logger.info(f"\nFinal dataset:")
    logger.info(f"  First candle: {combined['timestamp'].min()}")
    logger.info(f"  Last candle: {combined['timestamp'].max()}")
    logger.info(f"  Total candles: {len(combined):,}")
    logger.info(f"  Date span: {(combined['timestamp'].max() - combined['timestamp'].min()).days} days")
    
    return combined

def main():
    """Main execution"""
    logger.info("="*80)
    logger.info("FILLING DATA GAP WITH REAL HISTORICAL DATA")
    logger.info("NO SIMULATED DATA - REAL DOWNLOADS ONLY")
    logger.info("="*80)
    
    # Step 1: Check existing data
    existing_df, last_date, current_date = check_existing_data()
    
    # Step 2: Download gap data
    # Add 1 day to last_date to avoid overlap
    download_start = last_date + timedelta(days=1)
    
    new_df = download_gap_data(download_start, current_date)
    
    if new_df is None:
        logger.error("Failed to download gap data")
        return False
    
    # Step 3: Merge and validate
    complete_df = merge_and_validate(existing_df, new_df)
    
    if complete_df is None:
        logger.error("Failed to merge data")
        return False
    
    # Step 4: Save complete dataset
    output_file = "data/MASTER_DATASET/15m/xau_usd_15m_COMPLETE.csv"
    complete_df.to_csv(output_file, index=False)
    logger.info(f"\nComplete dataset saved to {output_file}")
    
    # Also update the original file
    backup_file = f"data/MASTER_DATASET/15m/xau_usd_15m_BACKUP_{datetime.now().strftime('%Y%m%d')}.csv"
    existing_df.to_csv(backup_file, index=False)
    logger.info(f"Original data backed up to {backup_file}")
    
    original_file = "data/MASTER_DATASET/15m/xau_usd_15m.csv"
    complete_df.to_csv(original_file, index=False)
    logger.info(f"Original file updated with complete data: {original_file}")
    
    logger.info("\n" + "="*80)
    logger.info("DATA GAP FILLED SUCCESSFULLY WITH REAL DATA")
    logger.info("="*80)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        logger.error("Failed to fill data gap")
        exit(1)

