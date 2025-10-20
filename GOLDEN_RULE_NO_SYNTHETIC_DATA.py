#!/usr/bin/env python3
"""
=============================================================================
GOLDEN RULE: NEVER USE SYNTHETIC DATA
=============================================================================

This module ENFORCES the golden rule: Real data MUST be used for all backtesting.
Synthetic data is FORBIDDEN and will cause the system to FAIL LOUDLY.

USER HAS 3 YEARS OF REAL HISTORICAL DATA - USE IT!
"""

import os
import sys
from pathlib import Path
import pandas as pd

class RealDataEnforcer:
    """Enforces the golden rule: NO SYNTHETIC DATA EVER"""
    
    # Master dataset paths - THE ONLY SOURCE OF TRUTH
    MASTER_DATASET_ROOT = "data/MASTER_DATASET"
    
    AVAILABLE_TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']
    AVAILABLE_PAIRS = [
        'aud_usd', 'eur_jpy', 'eur_usd', 'gbp_jpy', 'gbp_usd',
        'nzd_usd', 'usd_cad', 'usd_chf', 'usd_jpy', 'xau_usd'
    ]
    
    @staticmethod
    def load_real_data(pair: str, timeframe: str) -> pd.DataFrame:
        """
        Load REAL historical data - NEVER SYNTHETIC
        
        Args:
            pair: Currency pair (e.g., 'eur_usd', 'xau_usd')
            timeframe: Timeframe (e.g., '15m', '1h')
            
        Returns:
            DataFrame with real historical data
            
        Raises:
            SystemExit: If real data is not available (FAIL LOUDLY)
        """
        pair = pair.lower()
        
        # Validate inputs
        if timeframe not in RealDataEnforcer.AVAILABLE_TIMEFRAMES:
            print("\n" + "=" * 80)
            print("CRITICAL ERROR: GOLDEN RULE VIOLATION")
            print("=" * 80)
            print(f"Invalid timeframe: {timeframe}")
            print(f"Available: {RealDataEnforcer.AVAILABLE_TIMEFRAMES}")
            print("=" * 80)
            sys.exit(1)
        
        if pair not in RealDataEnforcer.AVAILABLE_PAIRS:
            print("\n" + "=" * 80)
            print("CRITICAL ERROR: GOLDEN RULE VIOLATION")
            print("=" * 80)
            print(f"Invalid pair: {pair}")
            print(f"Available: {RealDataEnforcer.AVAILABLE_PAIRS}")
            print("=" * 80)
            sys.exit(1)
        
        # Construct data file path
        data_file = f"{RealDataEnforcer.MASTER_DATASET_ROOT}/{timeframe}/{pair}_{timeframe}.csv"
        
        # CHECK IF FILE EXISTS
        if not os.path.exists(data_file):
            print("\n" + "=" * 80)
            print("CRITICAL ERROR: GOLDEN RULE VIOLATION")
            print("=" * 80)
            print("GOLDEN RULE: NEVER USE SYNTHETIC DATA!")
            print()
            print(f"Real data file not found: {data_file}")
            print()
            print("USER HAS 3 YEARS OF REAL DATA - IT MUST BE USED!")
            print()
            print("SYSTEM CANNOT CONTINUE WITHOUT REAL DATA")
            print("=" * 80)
            sys.exit(1)
        
        # Load the REAL data
        try:
            df = pd.read_csv(data_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            df.columns = df.columns.str.lower()
            
            # Verify data quality
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing = [col for col in required_columns if col not in df.columns]
            
            if missing:
                print("\n" + "=" * 80)
                print("CRITICAL ERROR: DATA QUALITY VIOLATION")
                print("=" * 80)
                print(f"Missing required columns: {missing}")
                print(f"File: {data_file}")
                print("=" * 80)
                sys.exit(1)
            
            print(f"[REAL DATA] Loaded {len(df):,} candles for {pair.upper()} {timeframe}")
            print(f"  Period: {df.index.min()} to {df.index.max()}")
            
            return df
            
        except Exception as e:
            print("\n" + "=" * 80)
            print("CRITICAL ERROR: DATA LOADING FAILED")
            print("=" * 80)
            print(f"Error loading real data: {e}")
            print(f"File: {data_file}")
            print("=" * 80)
            sys.exit(1)
    
    @staticmethod
    def validate_data_availability():
        """Validate that all expected data files exist"""
        print("\n" + "=" * 80)
        print("VALIDATING REAL DATA AVAILABILITY")
        print("=" * 80)
        
        missing_files = []
        
        for timeframe in RealDataEnforcer.AVAILABLE_TIMEFRAMES:
            for pair in RealDataEnforcer.AVAILABLE_PAIRS:
                data_file = f"{RealDataEnforcer.MASTER_DATASET_ROOT}/{timeframe}/{pair}_{timeframe}.csv"
                
                if not os.path.exists(data_file):
                    missing_files.append(f"{pair} {timeframe}")
        
        if missing_files:
            print(f"\n[WARNING] {len(missing_files)} data files missing:")
            for missing in missing_files[:10]:  # Show first 10
                print(f"  - {missing}")
            if len(missing_files) > 10:
                print(f"  ... and {len(missing_files) - 10} more")
        else:
            print("\n[SUCCESS] All expected data files found!")
        
        print("=" * 80 + "\n")
        
        return len(missing_files) == 0
    
    @staticmethod
    def prevent_synthetic_data_creation():
        """
        This function should be called at the start of any script
        to ensure synthetic data creation is DISABLED
        """
        # Set environment variable to prevent synthetic data
        os.environ['FORBID_SYNTHETIC_DATA'] = '1'
        os.environ['USE_REAL_DATA_ONLY'] = '1'
        
        print("\n" + "=" * 80)
        print("GOLDEN RULE ENFORCED: NO SYNTHETIC DATA")
        print("=" * 80)
        print("All simulations MUST use real historical data")
        print("Synthetic data generation is FORBIDDEN")
        print("=" * 80 + "\n")


def check_synthetic_data_attempt(func):
    """Decorator to prevent any function from creating synthetic data"""
    def wrapper(*args, **kwargs):
        # Check if function name suggests synthetic data creation
        if 'synthetic' in func.__name__.lower() or 'generate' in func.__name__.lower():
            if 'data' in func.__name__.lower():
                print("\n" + "=" * 80)
                print("BLOCKED: SYNTHETIC DATA CREATION ATTEMPT")
                print("=" * 80)
                print(f"Function: {func.__name__}")
                print("GOLDEN RULE: Only real data from MASTER_DATASET allowed!")
                print("=" * 80)
                raise RuntimeError("GOLDEN RULE VIOLATION: Synthetic data creation is FORBIDDEN")
        
        return func(*args, **kwargs)
    return wrapper


# Export the enforcer
enforcer = RealDataEnforcer()

if __name__ == "__main__":
    # Validate data availability
    enforcer.validate_data_availability()
    
    # Test loading real data
    print("\nTesting real data loading...")
    try:
        df = enforcer.load_real_data('eur_usd', '15m')
        print(f"\n[SUCCESS] Successfully loaded {len(df)} candles")
    except SystemExit:
        print("\n[FAILED] Could not load real data")


