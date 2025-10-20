"""
EFFICIENT FUTURES DATA DOWNLOADER
Uses yfinance (FREE - no API limits!) for comprehensive futures data
Optimized for minimal calls while maximizing data coverage
"""

import yfinance as yf
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import time
import json

class EfficientFuturesDownloader:
    def __init__(self):
        self.data_dir = Path("data/FUTURES_MASTER")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Futures instruments with specifications
        self.instruments = {
            'ES': {
                'symbol': 'ES=F',
                'name': 'E-mini S&P 500',
                'tick_value': 12.50,
                'tick_size': 0.25,
                'commission': 2.50,
                'margin': 500
            },
            'NQ': {
                'symbol': 'NQ=F',
                'name': 'E-mini Nasdaq',
                'tick_value': 5.00,
                'tick_size': 0.25,
                'commission': 2.50,
                'margin': 500
            },
            'GC': {
                'symbol': 'GC=F',
                'name': 'Gold Futures',
                'tick_value': 10.00,
                'tick_size': 0.10,
                'commission': 2.50,
                'margin': 1000
            }
        }
        
        self.download_log = []
    
    def download_efficient(self, symbol_key, max_days=1095):
        """
        Efficiently download multiple timeframes from single data source
        Download daily data once, resample to all needed timeframes
        """
        print(f"\n{'='*80}")
        print(f"DOWNLOADING: {self.instruments[symbol_key]['name']}")
        print(f"{'='*80}")
        
        # Download 1-minute data (maximum resolution)
        # We'll resample this to all other timeframes
        symbol = self.instruments[symbol_key]['symbol']
        
        # yfinance allows max 7 days of 1m data at a time
        # So we'll download 5m data for 60 days chunks, then resample
        all_data = []
        
        end_date = datetime.now()
        days_per_chunk = 59  # yfinance limit for 5m data
        num_chunks = (max_days // days_per_chunk) + 1
        
        print(f"Downloading in {num_chunks} chunks (5-minute resolution)...")
        
        for i in range(num_chunks):
            chunk_end = end_date - timedelta(days=i * days_per_chunk)
            chunk_start = chunk_end - timedelta(days=days_per_chunk)
            
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(
                    start=chunk_start,
                    end=chunk_end,
                    interval='5m',
                    actions=False
                )
                
                if len(data) > 0:
                    all_data.append(data)
                    print(f"  Chunk {i+1}/{num_chunks}: {len(data):,} bars ({chunk_start.date()} to {chunk_end.date()})")
                
                time.sleep(0.5)  # Small delay
                
            except Exception as e:
                print(f"  Warning: Chunk {i+1} failed: {e}")
                continue
        
        if not all_data:
            print(f" Failed to download data for {symbol_key}")
            return None
        
        # Combine all chunks
        df_5m = pd.concat(all_data)
        df_5m = df_5m.sort_index()
        df_5m = df_5m[~df_5m.index.duplicated(keep='first')]
        
        print(f"\n[OK] Downloaded {len(df_5m):,} 5-minute bars")
        print(f"   Range: {df_5m.index[0]} to {df_5m.index[-1]}")
        
        # Now resample to all timeframes efficiently
        timeframes = {
            '5m': df_5m,  # Already have this
            '15m': self._resample(df_5m, '15min'),
            '30m': self._resample(df_5m, '30min'),
            '1h': self._resample(df_5m, '1H'),
            '4h': self._resample(df_5m, '4H'),
            '1d': self._resample(df_5m, '1D')
        }
        
        # Add metadata and save all timeframes
        metadata = self.instruments[symbol_key]
        
        for tf_name, df in timeframes.items():
            if df is not None and len(df) > 0:
                # Add metadata
                df['symbol'] = symbol_key
                df['tick_value'] = metadata['tick_value']
                df['tick_size'] = metadata['tick_size']
                df['commission'] = metadata['commission']
                df['margin'] = metadata['margin']
                
                # Calculate additional indicators for efficiency
                df['ATR'] = self._calculate_atr(df, 14)
                df['EMA_3'] = df['Close'].ewm(span=3).mean()
                df['EMA_8'] = df['Close'].ewm(span=8).mean()
                df['EMA_12'] = df['Close'].ewm(span=12).mean()
                df['EMA_21'] = df['Close'].ewm(span=21).mean()
                df['RSI'] = self._calculate_rsi(df['Close'], 14)
                
                # Save
                filename = self.data_dir / f"{symbol_key}_{tf_name}.csv"
                df.to_csv(filename)
                
                print(f"  [OK] {tf_name}: {len(df):,} bars -> {filename.name}")
                
                self.download_log.append({
                    'symbol': symbol_key,
                    'timeframe': tf_name,
                    'bars': len(df),
                    'start': str(df.index[0]),
                    'end': str(df.index[-1]),
                    'file': str(filename)
                })
        
        return timeframes
    
    def _resample(self, df, rule):
        """Resample OHLCV data to different timeframe"""
        try:
            resampled = df.resample(rule).agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            })
            return resampled.dropna()
        except Exception as e:
            print(f"    Error resampling to {rule}: {e}")
            return None
    
    def _calculate_atr(self, df, period=14):
        """Calculate Average True Range"""
        high = df['High']
        low = df['Low']
        close = df['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def download_all_instruments(self):
        """Download all instruments efficiently"""
        print("\n" + "="*80)
        print(" "*20 + "EFFICIENT FUTURES DATA DOWNLOAD")
        print("="*80)
        print(f"\n[DATA] Instruments: {len(self.instruments)}")
        print(f"[DATA] Target: ~3 years historical data")
        print(f"[DATA] Timeframes: 5m, 15m, 30m, 1h, 4h, 1d")
        print(f"[SAVE] Save to: {self.data_dir}")
        print(f"\n[METHOD] Download 5m data, resample to all timeframes")
        print(f"   This minimizes API calls while maximizing data!\n")
        
        start_time = time.time()
        results = {}
        
        for symbol_key in self.instruments.keys():
            result = self.download_efficient(symbol_key, max_days=1095)
            results[symbol_key] = result
            time.sleep(1)  # Polite delay
        
        elapsed = time.time() - start_time
        
        # Save download log
        log_file = self.data_dir / "download_log.json"
        with open(log_file, 'w') as f:
            json.dump(self.download_log, f, indent=2)
        
        # Print summary
        print("\n" + "="*80)
        print(" "*25 + "DOWNLOAD COMPLETE")
        print("="*80)
        print(f"\n[TIME] Total time: {elapsed/60:.1f} minutes")
        print(f"[DATA] Files created: {len(self.download_log)}")
        print(f"[SAVE] Location: {self.data_dir}")
        print(f"\n[SUMMARY]:")
        
        for symbol_key in self.instruments.keys():
            symbol_files = [log for log in self.download_log if log['symbol'] == symbol_key]
            total_bars = sum(log['bars'] for log in symbol_files)
            print(f"\n  {symbol_key} ({self.instruments[symbol_key]['name']}):")
            print(f"    Files: {len(symbol_files)}")
            print(f"    Total bars: {total_bars:,}")
            for log in symbol_files:
                print(f"      - {log['timeframe']}: {log['bars']:,} bars")
        
        print(f"\n[OK] All data ready for backtesting!")
        print(f"[LOG] Download log: {log_file}")
        print("="*80)
        
        return results

if __name__ == "__main__":
    print("\n" + "="*80)
    print(" "*15 + "EFFICIENT FUTURES DATA DOWNLOADER")
    print(" "*18 + "(Uses FREE yfinance - No API limits!)")
    print("="*80)
    
    downloader = EfficientFuturesDownloader()
    results = downloader.download_all_instruments()
    
    print("\n" + "="*80)
    print(" NEXT STEP: Run comprehensive backtesting")
    print("   Command: python comprehensive_futures_optimizer.py")
    print("="*80 + "\n")

