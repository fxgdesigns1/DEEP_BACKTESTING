#!/usr/bin/env python3
"""
DATA QUALITY ENHANCER
Fixes data quality issues and creates reliable datasets for backtesting
"""

import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class DataQualityEnhancer:
    def __init__(self, data_dir="data/historical/prices"):
        self.data_dir = data_dir
        self.enhanced_dir = "data/enhanced"
        self.logger = logging.getLogger(__name__)
        
        # Create enhanced directory
        os.makedirs(self.enhanced_dir, exist_ok=True)
        
    def load_and_validate_data(self):
        """Load data from prices directory and validate quality"""
        print("🔍 Loading and validating data from prices directory...")
        
        data_files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
        validated_data = {}
        
        for file in data_files:
            currency_pair = file.replace('_1h.csv', '').upper()
            file_path = os.path.join(self.data_dir, file)
            
            try:
                df = pd.read_csv(file_path)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp').reset_index(drop=True)
                
                # Validate data quality
                if self._validate_data_quality(df, currency_pair):
                    validated_data[currency_pair] = df
                    print(f"✅ {currency_pair}: {len(df)} rows - VALID")
                else:
                    print(f"❌ {currency_pair}: Data quality issues detected")
                    
            except Exception as e:
                print(f"❌ Error loading {currency_pair}: {e}")
                
        return validated_data
    
    def _validate_data_quality(self, df, currency_pair):
        """Validate data quality and return True if acceptable"""
        issues = []
        
        # Check for negative prices
        if (df[['open', 'high', 'low', 'close']] <= 0).any().any():
            issues.append("Negative prices")
            
        # Check OHLC relationships
        if len(df[df['high'] < df['low']]) > 0:
            issues.append("High < Low violations")
            
        if len(df[df['open'] > df['high']]) > 0:
            issues.append("Open > High violations")
            
        if len(df[df['close'] > df['high']]) > 0:
            issues.append("Close > High violations")
            
        # Check volume data
        if df['volume'].sum() == 0:
            issues.append("Zero volume data")
            
        # Check for extreme price movements
        max_change = df['close'].pct_change().abs().max()
        if max_change > 0.1:  # 10% hourly change
            issues.append(f"Extreme price movement: {max_change*100:.2f}%")
            
        if issues:
            print(f"   Issues: {', '.join(issues)}")
            return False
            
        return True
    
    def fill_data_gaps(self, df, currency_pair):
        """Fill data gaps with appropriate methods"""
        print(f"🔧 Filling gaps for {currency_pair}...")
        
        # Create complete time series
        start_time = df['timestamp'].min()
        end_time = df['timestamp'].max()
        complete_timeline = pd.date_range(start=start_time, end=end_time, freq='H')
        
        # Set timestamp as index
        df_indexed = df.set_index('timestamp')
        
        # Reindex to complete timeline
        df_complete = df_indexed.reindex(complete_timeline)
        
        # Identify gaps
        gaps = df_complete[df_complete['open'].isna()]
        weekend_gaps = gaps[gaps.index.weekday >= 5]  # Saturday = 5, Sunday = 6
        other_gaps = gaps[gaps.index.weekday < 5]
        
        print(f"   Weekend gaps: {len(weekend_gaps)} (normal for forex)")
        print(f"   Other gaps: {len(other_gaps)} (will be filled)")
        
        # Fill gaps using forward fill for weekends, interpolation for others
        df_complete['open'] = df_complete['open'].fillna(method='ffill')
        df_complete['high'] = df_complete['high'].fillna(method='ffill')
        df_complete['low'] = df_complete['low'].fillna(method='ffill')
        df_complete['close'] = df_complete['close'].fillna(method='ffill')
        df_complete['volume'] = df_complete['volume'].fillna(0)  # Zero volume for filled gaps
        
        # Reset index
        df_filled = df_complete.reset_index()
        df_filled.rename(columns={'index': 'timestamp'}, inplace=True)
        
        return df_filled
    
    def enhance_data_quality(self, df, currency_pair):
        """Enhance data quality with additional features"""
        print(f"✨ Enhancing data quality for {currency_pair}...")
        
        # Add technical indicators for validation
        df['sma_20'] = df['close'].rolling(20).mean()
        df['atr'] = self._calculate_atr(df)
        df['price_change'] = df['close'].pct_change()
        df['volatility'] = df['price_change'].rolling(20).std()
        
        # Add data quality flags
        df['is_weekend'] = df['timestamp'].dt.weekday >= 5
        df['is_major_session'] = self._is_major_session(df['timestamp'])
        
        # Add market session information
        df['session'] = self._get_trading_session(df['timestamp'])
        
        # Add data quality score
        df['quality_score'] = self._calculate_quality_score(df)
        
        return df
    
    def _calculate_atr(self, df, period=14):
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.rolling(period).mean()
    
    def _is_major_session(self, timestamps):
        """Check if timestamp is during major trading session"""
        hours = timestamps.dt.hour
        # London: 7-16 UTC, New York: 13-22 UTC
        return ((hours >= 7) & (hours <= 16)) | ((hours >= 13) & (hours <= 22))
    
    def _get_trading_session(self, timestamps):
        """Get trading session for each timestamp"""
        hours = timestamps.dt.hour
        sessions = []
        
        for hour in hours:
            if 0 <= hour < 7:
                sessions.append('Tokyo')
            elif 7 <= hour < 13:
                sessions.append('London')
            elif 13 <= hour < 17:
                sessions.append('London_NY_Overlap')
            elif 17 <= hour < 22:
                sessions.append('New_York')
            else:
                sessions.append('After_Hours')
                
        return sessions
    
    def _calculate_quality_score(self, df):
        """Calculate data quality score for each row"""
        scores = []
        
        for i in range(len(df)):
            score = 100  # Start with perfect score
            
            # Deduct for extreme price movements
            if abs(df.iloc[i]['price_change']) > 0.05:  # 5% change
                score -= 20
                
            # Deduct for zero volume
            if df.iloc[i]['volume'] == 0:
                score -= 10
                
            # Deduct for weekend trading (less reliable)
            if df.iloc[i]['is_weekend']:
                score -= 5
                
            # Deduct for after-hours trading
            if df.iloc[i]['session'] == 'After_Hours':
                score -= 5
                
            scores.append(max(0, score))
            
        return scores
    
    def save_enhanced_data(self, enhanced_data):
        """Save enhanced data to new directory"""
        print("💾 Saving enhanced data...")
        
        for currency_pair, df in enhanced_data.items():
            filename = f"{currency_pair.lower()}_1h_enhanced.csv"
            filepath = os.path.join(self.enhanced_dir, filename)
            
            df.to_csv(filepath, index=False)
            print(f"✅ Saved {currency_pair}: {len(df)} rows to {filename}")
    
    def generate_enhancement_report(self, enhanced_data):
        """Generate report on data enhancement"""
        print("\n" + "="*60)
        print("📊 DATA ENHANCEMENT REPORT")
        print("="*60)
        
        for currency_pair, df in enhanced_data.items():
            print(f"\n{currency_pair}:")
            print(f"  Total rows: {len(df):,}")
            print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            print(f"  Weekend data: {df['is_weekend'].sum():,} rows")
            print(f"  Major session: {df['is_major_session'].sum():,} rows")
            print(f"  Avg quality score: {df['quality_score'].mean():.1f}")
            print(f"  Avg volatility: {df['volatility'].mean()*100:.3f}%")
            
        print(f"\n✅ Enhanced data saved to: {self.enhanced_dir}/")
        print("🎯 Data is now ready for reliable backtesting!")
    
    def run_enhancement(self):
        """Run complete data enhancement process"""
        print("🚀 Starting Data Quality Enhancement...")
        print("="*60)
        
        # Load and validate data
        validated_data = self.load_and_validate_data()
        
        if not validated_data:
            print("❌ No valid data found. Exiting.")
            return
        
        # Enhance each dataset
        enhanced_data = {}
        for currency_pair, df in validated_data.items():
            print(f"\n--- Processing {currency_pair} ---")
            
            # Fill gaps
            df_filled = self.fill_data_gaps(df, currency_pair)
            
            # Enhance quality
            df_enhanced = self.enhance_data_quality(df_filled, currency_pair)
            
            enhanced_data[currency_pair] = df_enhanced
        
        # Save enhanced data
        self.save_enhanced_data(enhanced_data)
        
        # Generate report
        self.generate_enhancement_report(enhanced_data)

def main():
    """Main execution function"""
    enhancer = DataQualityEnhancer()
    enhancer.run_enhancement()

if __name__ == "__main__":
    main()
