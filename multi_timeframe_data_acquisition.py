#!/usr/bin/env python3
"""
MULTI-TIMEFRAME DATA ACQUISITION SYSTEM
Downloads and organizes data for all timeframes: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w
"""

import asyncio
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import aiohttp
import yaml
import logging
from typing import List, Dict, Any, Optional, Tuple
import yfinance as yf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# All currency pairs
CURRENCY_PAIRS = [
    "EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD", "USD_CAD", 
    "USD_CHF", "NZD_USD", "EUR_JPY", "GBP_JPY", "XAU_USD"
]

# All timeframes to download
TIMEFRAMES = {
    "1m": {"oanda": "M1", "yfinance": "1m", "days_back": 7},      # 1 week of 1m data
    "5m": {"oanda": "M5", "yfinance": "5m", "days_back": 30},     # 1 month of 5m data
    "15m": {"oanda": "M15", "yfinance": "15m", "days_back": 60},  # 2 months of 15m data
    "30m": {"oanda": "M30", "yfinance": "30m", "days_back": 90},  # 3 months of 30m data
    "1h": {"oanda": "H1", "yfinance": "1h", "days_back": 730},    # 2 years of 1h data
    "4h": {"oanda": "H4", "yfinance": "4h", "days_back": 1095},   # 3 years of 4h data
    "1d": {"oanda": "D", "yfinance": "1d", "days_back": 1825},    # 5 years of daily data
    "1w": {"oanda": "W", "yfinance": "1wk", "days_back": 3650}    # 10 years of weekly data
}

class MultiTimeframeDataAcquisition:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = self._load_config(config_path)
        self.oanda_config = self.config['data_sources']['api_keys']['oanda']
        self.base_dir = "/Users/mac/SharedNetwork/quant_strategy_ai/deep_backtesting"
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return {
                'data_sources': {
                    'api_keys': {
                        'oanda': {
                            'api_key': 'd5d9a1d481fd07b5ec39214873639129-4c7188797832a4f3d59d5268e0dfb64b',
                            'base_url': 'https://api-fxtrade.oanda.com'
                        }
                    }
                }
            }
    
    def create_directory_structure(self):
        """Create organized directory structure for all timeframes"""
        logger.info("Creating multi-timeframe directory structure...")
        
        # Create main data directory structure
        for timeframe in TIMEFRAMES.keys():
            timeframe_dir = os.path.join(self.base_dir, "data", "timeframes", timeframe)
            os.makedirs(timeframe_dir, exist_ok=True)
            
            # Create subdirectories for each timeframe
            for subdir in ["raw", "processed", "completed", "enhanced"]:
                os.makedirs(os.path.join(timeframe_dir, subdir), exist_ok=True)
        
        # Create summary directory
        os.makedirs(os.path.join(self.base_dir, "data", "timeframes", "summaries"), exist_ok=True)
        
        logger.info("✅ Directory structure created successfully")
    
    async def download_oanda_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Download data from OANDA API"""
        try:
            base_url = self.oanda_config.get('base_url', 'https://api-fxtrade.oanda.com')
            api_key = self.oanda_config['api_key']
            granularity = TIMEFRAMES[timeframe]['oanda']
            days_back = TIMEFRAMES[timeframe]['days_back']
            
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days_back)
            
            all_candles = []
            current_date = end_date
            
            async with aiohttp.ClientSession() as session:
                while current_date > start_date:
                    url = f"{base_url}/v3/instruments/{symbol}/candles"
                    params = {
                        "price": "M",
                        "granularity": granularity,
                        "count": 5000,
                        "to": current_date.isoformat()
                    }
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    async with session.get(url, params=params, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            candles = data.get('candles', [])
                            if not candles:
                                break
                                
                            # Filter complete candles
                            complete_candles = [c for c in candles if c.get('complete', False)]
                            all_candles.extend(complete_candles)
                            
                            # Update current_date for next batch
                            if complete_candles:
                                current_date = datetime.fromisoformat(
                                    complete_candles[0]['time'].replace('Z', '+00:00')
                                ) - timedelta(minutes=1)
                            
                            # Check if we've reached start_date
                            if current_date <= start_date:
                                break
                        else:
                            logger.error(f"OANDA API error for {symbol} {timeframe}: {resp.status}")
                            break
                            
                        # Rate limiting
                        await asyncio.sleep(0.5)
            
            # Convert to DataFrame
            if not all_candles:
                return pd.DataFrame()
                
            df = pd.DataFrame([
                {
                    'timestamp': c['time'],
                    'open': float(c['mid']['o']),
                    'high': float(c['mid']['h']),
                    'low': float(c['mid']['l']),
                    'close': float(c['mid']['c']),
                    'volume': int(c['volume'])
                }
                for c in all_candles
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error downloading OANDA data for {symbol} {timeframe}: {e}")
            return pd.DataFrame()
    
    def download_yfinance_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Download data from Yahoo Finance as backup"""
        try:
            # Convert symbol to Yahoo Finance format
            yf_symbol = self._convert_to_yfinance_symbol(symbol)
            yf_interval = TIMEFRAMES[timeframe]['yfinance']
            days_back = TIMEFRAMES[timeframe]['days_back']
            
            # Download data
            df = yf.download(
                yf_symbol, 
                period=f"{days_back}d", 
                interval=yf_interval, 
                auto_adjust=False, 
                progress=False
            )
            
            if df.empty:
                return pd.DataFrame()
            
            # Standardize format
            df = df.reset_index()
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error downloading Yahoo Finance data for {symbol} {timeframe}: {e}")
            return pd.DataFrame()
    
    def _convert_to_yfinance_symbol(self, symbol: str) -> str:
        """Convert our symbol format to Yahoo Finance format"""
        symbol_map = {
            "EUR_USD": "EURUSD=X",
            "GBP_USD": "GBPUSD=X", 
            "USD_JPY": "USDJPY=X",
            "AUD_USD": "AUDUSD=X",
            "USD_CAD": "USDCAD=X",
            "USD_CHF": "USDCHF=X",
            "NZD_USD": "NZDUSD=X",
            "EUR_JPY": "EURJPY=X",
            "GBP_JPY": "GBPJPY=X",
            "XAU_USD": "XAUUSD=X"
        }
        return symbol_map.get(symbol, f"{symbol.replace('_', '')}=X")
    
    async def download_timeframe_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Download data for specific symbol and timeframe using best available source"""
        logger.info(f"Downloading {symbol} {timeframe} data...")
        
        # Try OANDA first (more reliable for forex)
        df = await self.download_oanda_data(symbol, timeframe)
        
        # If OANDA fails or returns insufficient data, try Yahoo Finance
        if df.empty or len(df) < 100:
            logger.info(f"OANDA data insufficient for {symbol} {timeframe}, trying Yahoo Finance...")
            df = self.download_yfinance_data(symbol, timeframe)
        
        if not df.empty:
            logger.info(f"✅ Downloaded {len(df)} candles for {symbol} {timeframe}")
        else:
            logger.error(f"❌ Failed to download data for {symbol} {timeframe}")
        
        return df
    
    def save_timeframe_data(self, df: pd.DataFrame, symbol: str, timeframe: str):
        """Save data to organized directory structure"""
        if df.empty:
            return
        
        # Create filename
        filename = f"{symbol.lower()}_{timeframe}.csv"
        
        # Save to raw data directory
        raw_path = os.path.join(self.base_dir, "data", "timeframes", timeframe, "raw", filename)
        df.to_csv(raw_path, index=False)
        
        # Also save to processed directory (for immediate use)
        processed_path = os.path.join(self.base_dir, "data", "timeframes", timeframe, "processed", filename)
        df.to_csv(processed_path, index=False)
        
        logger.info(f"💾 Saved {symbol} {timeframe} data to {raw_path}")
    
    def validate_timeframe_data(self, df: pd.DataFrame, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Validate downloaded timeframe data"""
        if df.empty:
            return {"valid": False, "reason": "Empty dataset"}
        
        validation_results = {
            "valid": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "total_candles": len(df),
            "date_range": {
                "start": df['timestamp'].min().isoformat(),
                "end": df['timestamp'].max().isoformat()
            },
            "data_quality": {
                "missing_values": df.isnull().sum().to_dict(),
                "duplicate_timestamps": df['timestamp'].duplicated().sum(),
                "price_consistency": self._check_price_consistency(df),
                "volume_consistency": self._check_volume_consistency(df)
            },
            "issues": []
        }
        
        # Check for common issues
        if validation_results["data_quality"]["duplicate_timestamps"] > 0:
            validation_results["issues"].append("Duplicate timestamps found")
            validation_results["valid"] = False
        
        if validation_results["data_quality"]["missing_values"]["close"] > 0:
            validation_results["issues"].append("Missing close prices")
            validation_results["valid"] = False
        
        if not validation_results["data_quality"]["price_consistency"]:
            validation_results["issues"].append("Price consistency issues (OHLC violations)")
            validation_results["valid"] = False
        
        return validation_results
    
    def _check_price_consistency(self, df: pd.DataFrame) -> bool:
        """Check if OHLC prices are consistent"""
        try:
            # Check if high >= low
            high_low_ok = (df['high'] >= df['low']).all()
            
            # Check if high >= open and high >= close
            high_open_close_ok = (df['high'] >= df['open']).all() and (df['high'] >= df['close']).all()
            
            # Check if low <= open and low <= close
            low_open_close_ok = (df['low'] <= df['open']).all() and (df['low'] <= df['close']).all()
            
            return high_low_ok and high_open_close_ok and low_open_close_ok
        except:
            return False
    
    def _check_volume_consistency(self, df: pd.DataFrame) -> bool:
        """Check if volume data is consistent"""
        try:
            # Volume should be non-negative
            return (df['volume'] >= 0).all()
        except:
            return False
    
    async def download_all_timeframes(self):
        """Download data for all symbols and timeframes"""
        logger.info("🚀 Starting multi-timeframe data acquisition...")
        
        # Create directory structure
        self.create_directory_structure()
        
        # Track results
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_requests": len(CURRENCY_PAIRS) * len(TIMEFRAMES),
            "successful_downloads": 0,
            "failed_downloads": 0,
            "timeframe_results": {},
            "validation_results": {}
        }
        
        # Download data for each symbol and timeframe
        for symbol in CURRENCY_PAIRS:
            logger.info(f"\n📊 Processing {symbol}...")
            results["timeframe_results"][symbol] = {}
            
            for timeframe in TIMEFRAMES.keys():
                try:
                    # Download data
                    df = await self.download_timeframe_data(symbol, timeframe)
                    
                    if not df.empty:
                        # Validate data
                        validation = self.validate_timeframe_data(df, symbol, timeframe)
                        results["validation_results"][f"{symbol}_{timeframe}"] = validation
                        
                        # Save data
                        self.save_timeframe_data(df, symbol, timeframe)
                        
                        # Record success
                        results["timeframe_results"][symbol][timeframe] = {
                            "status": "success",
                            "candles": len(df),
                            "date_range": validation["date_range"],
                            "valid": validation["valid"]
                        }
                        results["successful_downloads"] += 1
                        
                    else:
                        # Record failure
                        results["timeframe_results"][symbol][timeframe] = {
                            "status": "failed",
                            "reason": "No data downloaded"
                        }
                        results["failed_downloads"] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing {symbol} {timeframe}: {e}")
                    results["timeframe_results"][symbol][timeframe] = {
                        "status": "error",
                        "error": str(e)
                    }
                    results["failed_downloads"] += 1
                
                # Rate limiting between requests
                await asyncio.sleep(1)
        
        # Save comprehensive results
        self._save_acquisition_summary(results)
        
        # Print summary
        self._print_acquisition_summary(results)
        
        return results
    
    def _save_acquisition_summary(self, results: Dict[str, Any]):
        """Save acquisition summary to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results
        results_file = os.path.join(self.base_dir, "data", "timeframes", "summaries", f"acquisition_results_{timestamp}.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save validation summary
        validation_file = os.path.join(self.base_dir, "data", "timeframes", "summaries", f"validation_summary_{timestamp}.json")
        validation_summary = {
            "timestamp": results["timestamp"],
            "total_datasets": len(results["validation_results"]),
            "valid_datasets": sum(1 for v in results["validation_results"].values() if v.get("valid", False)),
            "invalid_datasets": sum(1 for v in results["validation_results"].values() if not v.get("valid", False)),
            "validation_details": results["validation_results"]
        }
        
        with open(validation_file, 'w') as f:
            json.dump(validation_summary, f, indent=2, default=str)
        
        logger.info(f"💾 Results saved to {results_file}")
        logger.info(f"💾 Validation summary saved to {validation_file}")
    
    def _print_acquisition_summary(self, results: Dict[str, Any]):
        """Print acquisition summary"""
        print("\n" + "="*80)
        print("🏆 MULTI-TIMEFRAME DATA ACQUISITION SUMMARY")
        print("="*80)
        
        print(f"📊 Total Requests: {results['total_requests']}")
        print(f"✅ Successful Downloads: {results['successful_downloads']}")
        print(f"❌ Failed Downloads: {results['failed_downloads']}")
        print(f"📈 Success Rate: {(results['successful_downloads']/results['total_requests']*100):.1f}%")
        
        print(f"\n📁 Data organized in: {os.path.join(self.base_dir, 'data', 'timeframes')}")
        print("📂 Directory structure:")
        for timeframe in TIMEFRAMES.keys():
            print(f"   • {timeframe}/ (raw, processed, completed, enhanced)")
        
        print(f"\n🎯 Available timeframes: {', '.join(TIMEFRAMES.keys())}")
        print(f"💱 Currency pairs: {len(CURRENCY_PAIRS)} pairs")
        
        # Show validation summary
        valid_count = sum(1 for v in results["validation_results"].values() if v.get("valid", False))
        total_count = len(results["validation_results"])
        print(f"\n🔍 Data Quality: {valid_count}/{total_count} datasets validated successfully")
        
        print("\n" + "="*80)
        print("🎉 Multi-timeframe data acquisition completed!")
        print("="*80)

async def main():
    """Main execution function"""
    acquirer = MultiTimeframeDataAcquisition()
    await acquirer.download_all_timeframes()

if __name__ == "__main__":
    asyncio.run(main())

