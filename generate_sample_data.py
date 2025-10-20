#!/usr/bin/env python3
"""
Sample Data Generator for Backtesting
Generates realistic market data for testing the backtesting system
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("sample_data_generator")

def generate_sample_data(instrument: str, start_date: datetime, end_date: datetime, output_dir: str) -> bool:
    """Generate sample market data for a specific instrument"""
    try:
        logger.info(f"Generating sample data for {instrument}")
        
        # Calculate number of hours
        hours = int((end_date - start_date).total_seconds() / 3600) + 1
        
        # Generate timestamps
        timestamps = [start_date + timedelta(hours=i) for i in range(hours)]
        
        # Generate price data based on instrument
        if instrument == "EUR_USD":
            base_price = 1.1
            volatility = 0.0001
        elif instrument == "GBP_USD":
            base_price = 1.3
            volatility = 0.0001
        elif instrument == "USD_JPY":
            base_price = 110.0
            volatility = 0.01
        elif instrument == "XAU_USD":
            base_price = 1800.0
            volatility = 0.5
        else:
            base_price = 1.0
            volatility = 0.0001
        
        # Generate random price movements
        np.random.seed(42)  # For reproducibility
        price_changes = np.random.normal(0, volatility, hours)
        prices = np.cumsum(price_changes) + base_price
        
        # Calculate bid/ask prices with realistic spread
        spread = 0.0002  # 2 pips spread
        bid_prices = prices - spread / 2
        ask_prices = prices + spread / 2
        
        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': timestamps,
            'mid_price': prices,
            'bid': bid_prices,
            'ask': ask_prices,
            'volume': np.random.randint(10, 100, hours)
        })
        
        # Save to CSV
        output_file = os.path.join(output_dir, f"{instrument}.csv")
        df.to_csv(output_file, index=False)
        
        logger.info(f"Generated {len(df)} data points for {instrument}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate sample data for {instrument}: {e}")
        return False

def main():
    """Generate sample data for all instruments"""
    # Create output directory
    output_dir = "backtesting_data"
    os.makedirs(output_dir, exist_ok=True)
    
    # Define instruments
    instruments = ["EUR_USD", "GBP_USD", "USD_JPY", "XAU_USD"]
    
    # Define date range
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 9, 1)
    
    # Generate data for each instrument
    for instrument in instruments:
        success = generate_sample_data(instrument, start_date, end_date, output_dir)
        if not success:
            logger.error(f"Failed to generate data for {instrument}")
            return 1
    
    logger.info("Sample data generation completed successfully")
    return 0

if __name__ == "__main__":
    exit(main())
