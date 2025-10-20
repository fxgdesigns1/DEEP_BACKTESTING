"""
Download 3 years of historical futures data for TopStep optimization
Uses yfinance (free) for initial data
"""

import yfinance as yf
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import time

class FuturesDataDownloader:
    def __init__(self):
        self.data_dir = Path("data/FUTURES_DATA")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Futures contracts with their Yahoo symbols
        self.futures = {
            'ES': {
                'symbol': 'ES=F',
                'name': 'E-mini S&P 500',
                'tick_value': 12.50,
                'tick_size': 0.25,
                'commission': 2.50
            },
            'NQ': {
                'symbol': 'NQ=F',
                'name': 'E-mini Nasdaq 100',
                'tick_value': 5.00,
                'tick_size': 0.25,
                'commission': 2.50
            },
            'YM': {
                'symbol': 'YM=F',
                'name': 'E-mini Dow Jones',
                'tick_value': 5.00,
                'tick_size': 1.0,
                'commission': 2.50
            },
            'RTY': {
                'symbol': 'RTY=F',
                'name': 'E-mini Russell 2000',
                'tick_value': 5.00,
                'tick_size': 0.10,
                'commission': 2.50
            },
            'GC': {
                'symbol': 'GC=F',
                'name': 'Gold Futures',
                'tick_value': 10.00,
                'tick_size': 0.10,
                'commission': 2.50
            },
            'CL': {
                'symbol': 'CL=F',
                'name': 'Crude Oil Futures',
                'tick_value': 10.00,
                'tick_size': 0.01,
                'commission': 2.50
            },
            '6E': {
                'symbol': '6E=F',
                'name': 'Euro FX Futures',
                'tick_value': 12.50,
                'tick_size': 0.00005,
                'commission': 2.50
            }
        }
    
    def download_instrument(self, symbol_key, years=3, interval='5m'):
        """
        Download data for a specific futures contract
        
        Args:
            symbol_key: Key from self.futures (e.g., 'ES')
            years: Number of years of historical data
            interval: '1m', '5m', '15m', '30m', '1h', '1d'
        """
        instrument = self.futures[symbol_key]
        symbol = instrument['symbol']
        name = instrument['name']
        
        print(f"\n{'='*80}")
        print(f"Downloading: {name} ({symbol})")
        print(f"{'='*80}")
        
        # Calculate date range
        end_date = datetime.now()
        
        # yfinance has limitations on how much intraday data you can get
        # For 1m/5m data, max is ~7-30 days per request
        if interval in ['1m', '5m']:
            # Download in chunks
            all_data = []
            days_per_chunk = 7 if interval == '1m' else 60  # yfinance limits
            
            total_days = years * 365
            num_chunks = (total_days // days_per_chunk) + 1
            
            print(f"Downloading {interval} data in {num_chunks} chunks...")
            
            for i in range(num_chunks):
                chunk_end = end_date - timedelta(days=i * days_per_chunk)
                chunk_start = chunk_end - timedelta(days=days_per_chunk)
                
                try:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(
                        start=chunk_start,
                        end=chunk_end,
                        interval=interval,
                        actions=False
                    )
                    
                    if len(data) > 0:
                        all_data.append(data)
                        print(f"  Chunk {i+1}/{num_chunks}: {len(data)} bars from {chunk_start.date()}")
                    
                    time.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    print(f"  Error on chunk {i+1}: {e}")
                    continue
            
            if all_data:
                # Combine all chunks
                df = pd.concat(all_data)
                df = df.sort_index()
                df = df[~df.index.duplicated(keep='first')]  # Remove duplicates
            else:
                print(f"❌ Failed to download any data for {name}")
                return None
                
        else:
            # For longer intervals (15m, 30m, 1h, 1d), we can get more data at once
            start_date = end_date - timedelta(days=years*365)
            
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(
                    start=start_date,
                    end=end_date,
                    interval=interval,
                    actions=False
                )
            except Exception as e:
                print(f"❌ Error downloading {name}: {e}")
                return None
        
        if df is None or len(df) == 0:
            print(f"❌ No data retrieved for {name}")
            return None
        
        # Add metadata
        df['symbol'] = symbol_key
        df['tick_value'] = instrument['tick_value']
        df['tick_size'] = instrument['tick_size']
        df['commission'] = instrument['commission']
        
        # Save to CSV
        filename = self.data_dir / f"{symbol_key}_{interval}.csv"
        df.to_csv(filename)
        
        print(f"✅ Downloaded {len(df):,} bars")
        print(f"   Date range: {df.index[0]} to {df.index[-1]}")
        print(f"   Saved to: {filename}")
        
        # Quality check
        self.check_data_quality(df, symbol_key, interval)
        
        return df
    
    def check_data_quality(self, df, symbol, interval):
        """Check for data quality issues"""
        print(f"\n📊 Data Quality Check:")
        
        # Check for missing values
        missing = df.isnull().sum().sum()
        if missing > 0:
            print(f"   ⚠️  Missing values: {missing}")
        else:
            print(f"   ✅ No missing values")
        
        # Check for duplicate timestamps
        duplicates = df.index.duplicated().sum()
        if duplicates > 0:
            print(f"   ⚠️  Duplicate timestamps: {duplicates}")
        else:
            print(f"   ✅ No duplicate timestamps")
        
        # Check for zero volume
        if 'Volume' in df.columns:
            zero_vol = (df['Volume'] == 0).sum()
            if zero_vol > len(df) * 0.1:  # More than 10%
                print(f"   ⚠️  Many zero-volume bars: {zero_vol} ({zero_vol/len(df)*100:.1f}%)")
            else:
                print(f"   ✅ Volume data looks good")
        
        # Check for price gaps
        if len(df) > 1:
            df['price_change_pct'] = df['Close'].pct_change().abs() * 100
            large_gaps = (df['price_change_pct'] > 5).sum()
            if large_gaps > 0:
                print(f"   ⚠️  Large price gaps (>5%): {large_gaps}")
            else:
                print(f"   ✅ No unusual price gaps")
    
    def download_all(self, instruments=['ES', 'NQ', 'GC'], intervals=['5m', '15m'], years=3):
        """Download data for multiple instruments and timeframes"""
        print("\n" + "="*80)
        print(" "*20 + "FUTURES DATA DOWNLOAD")
        print("="*80)
        print(f"\nInstruments: {', '.join(instruments)}")
        print(f"Intervals: {', '.join(intervals)}")
        print(f"Years: {years}")
        print(f"Target: {self.data_dir}")
        
        results = {}
        
        for instrument in instruments:
            for interval in intervals:
                key = f"{instrument}_{interval}"
                print(f"\n{'='*80}")
                df = self.download_instrument(instrument, years=years, interval=interval)
                results[key] = df
                time.sleep(2)  # Rate limiting between requests
        
        # Summary
        print("\n" + "="*80)
        print(" "*25 + "DOWNLOAD SUMMARY")
        print("="*80)
        
        success_count = sum(1 for df in results.values() if df is not None)
        total_count = len(results)
        
        print(f"\nSuccessful: {success_count}/{total_count}")
        print(f"\nDownloaded files:")
        for key, df in results.items():
            if df is not None:
                print(f"  ✅ {key}: {len(df):,} bars")
            else:
                print(f"  ❌ {key}: Failed")
        
        print(f"\n💾 Data saved to: {self.data_dir}")
        print("="*80)
        
        return results

if __name__ == "__main__":
    downloader = FuturesDataDownloader()
    
    # Start with primary instruments and 5-minute data
    # This is enough to run comprehensive tests
    results = downloader.download_all(
        instruments=['ES', 'NQ', 'GC'],  # Start with top 3
        intervals=['5m', '15m'],  # 5m for trading, 15m for trend filter
        years=3
    )
    
    print("\n" + "="*80)
    print("✅ DOWNLOAD COMPLETE!")
    print("="*80)
    print("\nNext steps:")
    print("1. Review data quality")
    print("2. Run: python test_ema_on_futures.py")
    print("3. Then: python optimize_futures_strategy.py")
    print("="*80)






