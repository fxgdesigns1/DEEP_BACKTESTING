#!/usr/bin/env python3
"""
Data Cleaning Script for Trading Simulations
This script cleans and prepares historical market data for backtesting.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class DataCleaner:
    def __init__(self, data_dir="data/historical/prices", output_dir="data/cleaned"):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.cleaned_data = {}
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
    
    def load_currency_pair(self, currency_pair):
        """Load a specific currency pair data"""
        filename = f"{currency_pair.lower()}_1h.csv"
        file_path = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None
            
        df = pd.read_csv(file_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    def identify_gaps(self, df):
        """Identify and categorize data gaps"""
        df['hour_diff'] = df['timestamp'].diff().dt.total_seconds() / 3600
        
        # Weekend gaps (48+ hours)
        weekend_gaps = df[df['hour_diff'] >= 48]
        
        # Other gaps (1-48 hours)
        other_gaps = df[(df['hour_diff'] > 1.1) & (df['hour_diff'] < 48)]
        
        # Missing data periods
        start_time = df['timestamp'].min()
        end_time = df['timestamp'].max()
        expected_hours = (end_time - start_time).total_seconds() / 3600
        missing_hours = expected_hours - len(df)
        
        return {
            'weekend_gaps': weekend_gaps,
            'other_gaps': other_gaps,
            'missing_hours': missing_hours,
            'expected_hours': expected_hours
        }
    
    def fill_weekend_gaps(self, df):
        """Fill weekend gaps with Friday close prices"""
        print("  Filling weekend gaps...")
        
        df_cleaned = df.copy()
        df_cleaned['hour_diff'] = df_cleaned['timestamp'].diff().dt.total_seconds() / 3600
        
        # Find weekend gaps
        weekend_gaps = df_cleaned[df_cleaned['hour_diff'] >= 48]
        
        if len(weekend_gaps) > 0:
            print(f"    Found {len(weekend_gaps)} weekend gaps")
            
            # For each weekend gap, we'll use the Friday close price
            # This is a simplified approach - in practice you might want more sophisticated gap handling
            for idx in weekend_gaps.index:
                if idx > 0:  # Not the first row
                    friday_close = df_cleaned.loc[idx-1, 'close']
                    
                    # Create a new row for the weekend gap
                    new_row = df_cleaned.loc[idx-1].copy()
                    new_row['timestamp'] = df_cleaned.loc[idx-1, 'timestamp'] + timedelta(hours=1)
                    new_row['open'] = friday_close
                    new_row['high'] = friday_close
                    new_row['low'] = friday_close
                    new_row['close'] = friday_close
                    new_row['volume'] = 0  # No trading on weekends
                    
                    # Insert the new row
                    df_cleaned = pd.concat([
                        df_cleaned.iloc[:idx],
                        pd.DataFrame([new_row]),
                        df_cleaned.iloc[idx:]
                    ]).reset_index(drop=True)
        
        return df_cleaned
    
    def handle_extreme_volumes(self, df, currency_pair):
        """Handle extreme volume values that might be data errors"""
        print("  Handling extreme volumes...")
        
        df_cleaned = df.copy()
        
        # Calculate volume statistics
        volume_mean = df_cleaned['volume'].mean()
        volume_std = df_cleaned['volume'].std()
        
        # Identify extreme volumes (3+ standard deviations from mean)
        extreme_threshold = volume_mean + 3 * volume_std
        extreme_volumes = df_cleaned[df_cleaned['volume'] > extreme_threshold]
        
        if len(extreme_volumes) > 0:
            print(f"    Found {len(extreme_volumes)} extreme volume bars")
            
            # Replace extreme volumes with median volume
            median_volume = df_cleaned['volume'].median()
            df_cleaned.loc[df_cleaned['volume'] > extreme_threshold, 'volume'] = median_volume
            
            print(f"    Replaced extreme volumes with median: {median_volume:.0f}")
        
        return df_cleaned
    
    def validate_ohlc_relationships(self, df):
        """Ensure OHLC relationships are valid"""
        print("  Validating OHLC relationships...")
        
        df_cleaned = df.copy()
        
        # Fix any OHLC violations
        violations = 0
        
        # High should be >= Low
        high_low_violations = df_cleaned[df_cleaned['high'] < df_cleaned['low']]
        if len(high_low_violations) > 0:
            violations += len(high_low_violations)
            # Fix by setting high = low + small increment
            df_cleaned.loc[df_cleaned['high'] < df_cleaned['low'], 'high'] = \
                df_cleaned.loc[df_cleaned['high'] < df_cleaned['low'], 'low'] * 1.0001
        
        # Open and Close should be between High and Low
        open_high_violations = df_cleaned[df_cleaned['open'] > df_cleaned['high']]
        if len(open_high_violations) > 0:
            violations += len(open_high_violations)
            df_cleaned.loc[df_cleaned['open'] > df_cleaned['high'], 'open'] = \
                df_cleaned.loc[df_cleaned['open'] > df_cleaned['high'], 'high']
        
        close_high_violations = df_cleaned[df_cleaned['close'] > df_cleaned['high']]
        if len(close_high_violations) > 0:
            violations += len(close_high_violations)
            df_cleaned.loc[df_cleaned['close'] > df_cleaned['high'], 'close'] = \
                df_cleaned.loc[df_cleaned['close'] > df_cleaned['high'], 'high']
        
        open_low_violations = df_cleaned[df_cleaned['open'] < df_cleaned['low']]
        if len(open_low_violations) > 0:
            violations += len(open_low_violations)
            df_cleaned.loc[df_cleaned['open'] < df_cleaned['low'], 'open'] = \
                df_cleaned.loc[df_cleaned['open'] < df_cleaned['low'], 'low']
        
        close_low_violations = df_cleaned[df_cleaned['close'] < df_cleaned['low']]
        if len(close_low_violations) > 0:
            violations += len(close_low_violations)
            df_cleaned.loc[df_cleaned['close'] < df_cleaned['low'], 'close'] = \
                df_cleaned.loc[df_cleaned['close'] < df_cleaned['low'], 'low']
        
        if violations > 0:
            print(f"    Fixed {violations} OHLC violations")
        
        return df_cleaned
    
    def add_technical_indicators(self, df):
        """Add basic technical indicators for analysis"""
        print("  Adding technical indicators...")
        
        df_enhanced = df.copy()
        
        # Simple Moving Averages
        df_enhanced['sma_20'] = df_enhanced['close'].rolling(window=20).mean()
        df_enhanced['sma_50'] = df_enhanced['close'].rolling(window=50).mean()
        
        # Exponential Moving Averages
        df_enhanced['ema_12'] = df_enhanced['close'].ewm(span=12).mean()
        df_enhanced['ema_26'] = df_enhanced['close'].ewm(span=26).mean()
        
        # RSI
        delta = df_enhanced['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df_enhanced['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df_enhanced['bb_middle'] = df_enhanced['close'].rolling(window=20).mean()
        bb_std = df_enhanced['close'].rolling(window=20).std()
        df_enhanced['bb_upper'] = df_enhanced['bb_middle'] + (bb_std * 2)
        df_enhanced['bb_lower'] = df_enhanced['bb_middle'] - (bb_std * 2)
        
        # MACD
        df_enhanced['macd'] = df_enhanced['ema_12'] - df_enhanced['ema_26']
        df_enhanced['macd_signal'] = df_enhanced['macd'].ewm(span=9).mean()
        df_enhanced['macd_histogram'] = df_enhanced['macd'] - df_enhanced['macd_signal']
        
        # ATR (Average True Range)
        high_low = df_enhanced['high'] - df_enhanced['low']
        high_close = np.abs(df_enhanced['high'] - df_enhanced['close'].shift())
        low_close = np.abs(df_enhanced['low'] - df_enhanced['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df_enhanced['atr'] = true_range.rolling(14).mean()
        
        return df_enhanced
    
    def clean_currency_pair(self, currency_pair):
        """Clean a single currency pair dataset"""
        print(f"\nCleaning {currency_pair}...")
        
        # Load data
        df = self.load_currency_pair(currency_pair)
        if df is None:
            return None
        
        # Initial data info
        initial_rows = len(df)
        print(f"  Initial rows: {initial_rows}")
        
        # Identify gaps
        gap_info = self.identify_gaps(df)
        print(f"  Missing hours: {gap_info['missing_hours']:.0f} ({gap_info['missing_hours']/gap_info['expected_hours']*100:.1f}%)")
        print(f"  Weekend gaps: {len(gap_info['weekend_gaps'])}")
        print(f"  Other gaps: {len(gap_info['other_gaps'])}")
        
        # Clean the data
        df_cleaned = df.copy()
        
        # Fill weekend gaps
        df_cleaned = self.fill_weekend_gaps(df_cleaned)
        
        # Handle extreme volumes
        df_cleaned = self.handle_extreme_volumes(df_cleaned, currency_pair)
        
        # Validate OHLC relationships
        df_cleaned = self.validate_ohlc_relationships(df_cleaned)
        
        # Add technical indicators
        df_cleaned = self.add_technical_indicators(df_cleaned)
        
        # Final validation
        final_rows = len(df_cleaned)
        print(f"  Final rows: {final_rows}")
        print(f"  Rows added: {final_rows - initial_rows}")
        
        # Store cleaned data
        self.cleaned_data[currency_pair] = df_cleaned
        
        return df_cleaned
    
    def save_cleaned_data(self):
        """Save all cleaned data to files"""
        print(f"\nSaving cleaned data to {self.output_dir}...")
        
        for currency_pair, df in self.cleaned_data.items():
            filename = f"{currency_pair.lower()}_cleaned_1h.csv"
            file_path = os.path.join(self.output_dir, filename)
            
            # Save without technical indicators for compatibility
            columns_to_save = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            df_to_save = df[columns_to_save].copy()
            
            df_to_save.to_csv(file_path, index=False)
            print(f"  Saved {currency_pair}: {filename}")
            
            # Also save enhanced version with indicators
            enhanced_filename = f"{currency_pair.lower()}_enhanced_1h.csv"
            enhanced_file_path = os.path.join(self.output_dir, enhanced_filename)
            df.to_csv(enhanced_file_path, index=False)
            print(f"  Saved enhanced {currency_pair}: {enhanced_filename}")
    
    def generate_cleaning_report(self):
        """Generate a report of the cleaning process"""
        print("\n" + "=" * 60)
        print("DATA CLEANING REPORT")
        print("=" * 60)
        
        total_initial_rows = 0
        total_final_rows = 0
        
        for currency_pair, df in self.cleaned_data.items():
            initial_df = self.load_currency_pair(currency_pair)
            if initial_df is not None:
                initial_rows = len(initial_df)
                final_rows = len(df)
                total_initial_rows += initial_rows
                total_final_rows += final_rows
                
                print(f"{currency_pair}: {initial_rows} → {final_rows} rows (+{final_rows - initial_rows})")
        
        print(f"\nTotal: {total_initial_rows} → {total_final_rows} rows (+{total_final_rows - total_initial_rows})")
        
        if total_final_rows > total_initial_rows:
            print("✓ Data gaps have been filled for better simulation continuity")
        
        print(f"\nCleaned data saved to: {self.output_dir}")
        print("Files available:")
        print("  • *_cleaned_1h.csv - Basic OHLCV data")
        print("  • *_enhanced_1h.csv - Data with technical indicators")
    
    def run_cleaning_pipeline(self, currency_pairs=None):
        """Run the complete cleaning pipeline"""
        print("Data Cleaning Pipeline for Trading Simulations")
        print("=" * 60)
        
        if currency_pairs is None:
            # Get all available currency pairs
            files = [f for f in os.listdir(self.data_dir) if f.endswith('_1h.csv')]
            currency_pairs = [f.replace('_1h.csv', '').upper() for f in files]
        
        print(f"Processing {len(currency_pairs)} currency pairs...")
        
        # Clean each currency pair
        for currency_pair in currency_pairs:
            self.clean_currency_pair(currency_pair)
        
        # Save cleaned data
        self.save_cleaned_data()
        
        # Generate report
        self.generate_cleaning_report()
        
        print("\nData cleaning complete! Your data is now ready for simulations.")

def main():
    """Main execution function"""
    # Initialize cleaner
    cleaner = DataCleaner()
    
    # Define currency pairs to clean (or None for all)
    currency_pairs = [
        'EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CAD', 'AUD_USD',
        'USD_CHF', 'NZD_USD', 'EUR_JPY', 'GBP_JPY', 'XAU_USD'
    ]
    
    # Run cleaning pipeline
    cleaner.run_cleaning_pipeline(currency_pairs)

if __name__ == "__main__":
    main()
