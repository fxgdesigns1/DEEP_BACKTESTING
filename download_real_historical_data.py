#!/usr/bin/env python3
"""
Download REAL Historical Data - NO SIMULATION
Uses yfinance for forex and gold data
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_real_data():
    """Download real historical data from Yahoo Finance"""
    
    # Create output directory
    output_dir = Path("real_historical_data")
    output_dir.mkdir(exist_ok=True)
    
    # Define instruments (Yahoo Finance tickers)
    instruments = {
        'GC=F': 'GOLD',  # Gold Futures
        'EURUSD=X': 'EUR_USD',
        'GBPUSD=X': 'GBP_USD',
        'USDJPY=X': 'USD_JPY',
        'AUDUSD=X': 'AUD_USD'
    }
    
    # Download 2 years of data for robust testing
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # 2 years
    
    logger.info(f"Downloading REAL historical data from {start_date.date()} to {end_date.date()}")
    
    downloaded_data = {}
    
    for ticker, name in instruments.items():
        try:
            logger.info(f"Downloading {name} ({ticker})...")
            
            # Download data with 15-minute intervals
            df = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                interval='15m',
                progress=False
            )
            
            if df.empty:
                logger.warning(f"No data received for {name}")
                continue
            
            # Clean up the data
            df = df.reset_index()
            df.columns = [col.lower() for col in df.columns]
            
            # Rename datetime column if needed
            if 'datetime' not in df.columns and 'date' in df.columns:
                df.rename(columns={'date': 'datetime'}, inplace=True)
            
            # Calculate spread (estimate 2-3 pips for forex, $1-2 for gold)
            if 'GOLD' in name:
                df['spread'] = 1.5  # $1.50 spread for gold
            else:
                df['spread'] = 0.0002  # 2 pips for forex
            
            # Save to CSV
            output_file = output_dir / f"{name}_15m_real.csv"
            df.to_csv(output_file, index=False)
            
            logger.info(f"✓ Downloaded {len(df)} candles for {name}")
            logger.info(f"  Date range: {df['datetime'].min()} to {df['datetime'].max()}")
            logger.info(f"  Saved to: {output_file}")
            
            downloaded_data[name] = df
            
        except Exception as e:
            logger.error(f"Error downloading {name}: {e}")
    
    logger.info(f"\nSuccessfully downloaded {len(downloaded_data)} instruments")
    return downloaded_data

if __name__ == "__main__":
    download_real_data()


