#!/usr/bin/env python3
"""
MULTI-TIMEFRAME DATA ORGANIZER
Organizes and syncs existing data across all timeframes
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import shutil
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiTimeframeDataOrganizer:
    def __init__(self, base_dir: str = "/Users/mac/SharedNetwork/quant_strategy_ai/deep_backtesting"):
        self.base_dir = base_dir
        self.data_dir = os.path.join(base_dir, "data")
        
        # Timeframe mapping
        self.timeframes = {
            "1m": {"minutes": 1, "directory": "1m"},
            "5m": {"minutes": 5, "directory": "5m"},
            "15m": {"minutes": 15, "directory": "15m"},
            "30m": {"minutes": 30, "directory": "30m"},
            "1h": {"minutes": 60, "directory": "1h"},
            "4h": {"minutes": 240, "directory": "4h"},
            "1d": {"minutes": 1440, "directory": "1d"},
            "1w": {"minutes": 10080, "directory": "1w"}
        }
        
        # Currency pairs
        self.currency_pairs = [
            "EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD", "USD_CAD",
            "USD_CHF", "NZD_USD", "EUR_JPY", "GBP_JPY", "XAU_USD"
        ]
    
    def find_existing_data(self) -> Dict[str, List[str]]:
        """Find all existing data files across the system"""
        logger.info("🔍 Scanning for existing data files...")
        
        existing_data = {
            "1h": [],
            "other_timeframes": [],
            "unorganized": []
        }
        
        # Search in main data directory
        if os.path.exists(self.data_dir):
            for root, dirs, files in os.walk(self.data_dir):
                for file in files:
                    if file.endswith('.csv'):
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)
                        
                        # Skip very small files (likely empty or corrupted)
                        if file_size < 100:
                            continue
                        
                        # Check if it's 1H data
                        if '1h' in file.lower() or '1H' in file:
                            existing_data["1h"].append(file_path)
                        else:
                            existing_data["other_timeframes"].append(file_path)
        
        # Search in parent directory for additional data
        parent_data_dir = os.path.join(os.path.dirname(self.base_dir), "data")
        if os.path.exists(parent_data_dir):
            for root, dirs, files in os.walk(parent_data_dir):
                for file in files:
                    if file.endswith('.csv'):
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)
                        
                        if file_size < 100:
                            continue
                        
                        # Check if it's already in our organized structure
                        if "timeframes" not in file_path:
                            existing_data["unorganized"].append(file_path)
        
        logger.info(f"Found {len(existing_data['1h'])} 1H files")
        logger.info(f"Found {len(existing_data['other_timeframes'])} other timeframe files")
        logger.info(f"Found {len(existing_data['unorganized'])} unorganized files")
        
        return existing_data
    
    def create_timeframe_structure(self):
        """Create organized directory structure for all timeframes"""
        logger.info("📁 Creating multi-timeframe directory structure...")
        
        # Create main timeframes directory
        timeframes_dir = os.path.join(self.data_dir, "timeframes")
        os.makedirs(timeframes_dir, exist_ok=True)
        
        # Create subdirectories for each timeframe
        for timeframe, config in self.timeframes.items():
            timeframe_dir = os.path.join(timeframes_dir, config["directory"])
            
            # Create subdirectories
            for subdir in ["raw", "processed", "completed", "enhanced", "validated"]:
                os.makedirs(os.path.join(timeframe_dir, subdir), exist_ok=True)
        
        # Create summary and reports directories
        os.makedirs(os.path.join(timeframes_dir, "summaries"), exist_ok=True)
        os.makedirs(os.path.join(timeframes_dir, "reports"), exist_ok=True)
        
        logger.info("✅ Directory structure created successfully")
    
    def organize_existing_1h_data(self, existing_files: List[str]):
        """Organize existing 1H data into proper structure"""
        logger.info("📊 Organizing existing 1H data...")
        
        organized_count = 0
        
        for file_path in existing_files:
            try:
                # Read the file to get basic info
                df = pd.read_csv(file_path, nrows=5)
                
                # Determine currency pair from filename or content
                currency_pair = self._extract_currency_pair(file_path, df)
                
                if currency_pair:
                    # Create organized filename
                    organized_filename = f"{currency_pair.lower()}_1h.csv"
                    
                    # Copy to organized structure
                    dest_path = os.path.join(
                        self.data_dir, "timeframes", "1h", "processed", organized_filename
                    )
                    
                    # Copy file
                    shutil.copy2(file_path, dest_path)
                    organized_count += 1
                    
                    logger.info(f"✅ Organized {currency_pair} 1H data")
                
            except Exception as e:
                logger.error(f"Error organizing file {file_path}: {e}")
        
        logger.info(f"📊 Organized {organized_count} 1H data files")
    
    def _extract_currency_pair(self, file_path: str, df: pd.DataFrame) -> Optional[str]:
        """Extract currency pair from filename or data"""
        filename = os.path.basename(file_path).lower()
        
        # Try to extract from filename
        for pair in self.currency_pairs:
            pair_lower = pair.lower()
            if pair_lower in filename:
                return pair
        
        # If not found in filename, try to infer from data
        # This is a fallback - in practice, filenames should contain the pair
        return None
    
    def generate_timeframe_from_1h(self, source_file: str, target_timeframe: str) -> Optional[pd.DataFrame]:
        """Generate higher timeframe data from 1H data"""
        try:
            # Read 1H data
            df = pd.read_csv(source_file)
            
            # Ensure timestamp column exists and is properly formatted
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            elif 'Date' in df.columns:
                df['timestamp'] = pd.to_datetime(df['Date'])
                df = df.drop('Date', axis=1)
            else:
                logger.error(f"No timestamp column found in {source_file}")
                return None
            
            # Set timestamp as index
            df = df.set_index('timestamp')
            
            # Resample to target timeframe
            target_minutes = self.timeframes[target_timeframe]["minutes"]
            
            # Resample OHLCV data
            resampled = df.resample(f'{target_minutes}T').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            # Reset index
            resampled = resampled.reset_index()
            
            return resampled
            
        except Exception as e:
            logger.error(f"Error generating {target_timeframe} from {source_file}: {e}")
            return None
    
    def generate_all_timeframes_from_1h(self):
        """Generate all higher timeframes from existing 1H data"""
        logger.info("🔄 Generating higher timeframes from 1H data...")
        
        # Get all 1H files
        h1_dir = os.path.join(self.data_dir, "timeframes", "1h", "processed")
        
        if not os.path.exists(h1_dir):
            logger.error("No 1H data directory found")
            return
        
        h1_files = [f for f in os.listdir(h1_dir) if f.endswith('.csv')]
        
        generated_count = 0
        
        for h1_file in h1_files:
            h1_path = os.path.join(h1_dir, h1_file)
            currency_pair = h1_file.replace('_1h.csv', '').upper()
            
            logger.info(f"Processing {currency_pair}...")
            
            # Generate higher timeframes
            for timeframe, config in self.timeframes.items():
                if timeframe == "1h":
                    continue  # Skip 1H itself
                
                try:
                    # Generate timeframe data
                    generated_df = self.generate_timeframe_from_1h(h1_path, timeframe)
                    
                    if generated_df is not None and not generated_df.empty:
                        # Save generated data
                        output_filename = f"{currency_pair.lower()}_{timeframe}.csv"
                        output_path = os.path.join(
                            self.data_dir, "timeframes", config["directory"], "processed", output_filename
                        )
                        
                        generated_df.to_csv(output_path, index=False)
                        generated_count += 1
                        
                        logger.info(f"✅ Generated {currency_pair} {timeframe} ({len(generated_df)} candles)")
                    
                except Exception as e:
                    logger.error(f"Error generating {timeframe} for {currency_pair}: {e}")
        
        logger.info(f"🔄 Generated {generated_count} timeframe files from 1H data")
    
    def validate_timeframe_data(self, file_path: str) -> Dict[str, Any]:
        """Validate timeframe data quality"""
        try:
            df = pd.read_csv(file_path)
            
            validation = {
                "file": file_path,
                "total_candles": len(df),
                "date_range": {
                    "start": df['timestamp'].min() if 'timestamp' in df.columns else "Unknown",
                    "end": df['timestamp'].max() if 'timestamp' in df.columns else "Unknown"
                },
                "data_quality": {
                    "missing_values": df.isnull().sum().to_dict(),
                    "duplicate_timestamps": df['timestamp'].duplicated().sum() if 'timestamp' in df.columns else 0,
                    "price_consistency": self._check_price_consistency(df),
                    "volume_consistency": self._check_volume_consistency(df)
                },
                "valid": True,
                "issues": []
            }
            
            # Check for issues
            if validation["data_quality"]["duplicate_timestamps"] > 0:
                validation["issues"].append("Duplicate timestamps")
                validation["valid"] = False
            
            if validation["data_quality"]["missing_values"]["close"] > 0:
                validation["issues"].append("Missing close prices")
                validation["valid"] = False
            
            if not validation["data_quality"]["price_consistency"]:
                validation["issues"].append("Price consistency issues")
                validation["valid"] = False
            
            return validation
            
        except Exception as e:
            return {
                "file": file_path,
                "valid": False,
                "error": str(e)
            }
    
    def _check_price_consistency(self, df: pd.DataFrame) -> bool:
        """Check OHLC price consistency"""
        try:
            return (
                (df['high'] >= df['low']).all() and
                (df['high'] >= df['open']).all() and
                (df['high'] >= df['close']).all() and
                (df['low'] <= df['open']).all() and
                (df['low'] <= df['close']).all()
            )
        except:
            return False
    
    def _check_volume_consistency(self, df: pd.DataFrame) -> bool:
        """Check volume data consistency"""
        try:
            return (df['volume'] >= 0).all()
        except:
            return False
    
    def validate_all_timeframes(self):
        """Validate all timeframe data"""
        logger.info("🔍 Validating all timeframe data...")
        
        validation_results = {}
        
        for timeframe, config in self.timeframes.items():
            timeframe_dir = os.path.join(self.data_dir, "timeframes", config["directory"], "processed")
            
            if os.path.exists(timeframe_dir):
                files = [f for f in os.listdir(timeframe_dir) if f.endswith('.csv')]
                
                for file in files:
                    file_path = os.path.join(timeframe_dir, file)
                    validation = self.validate_timeframe_data(file_path)
                    validation_results[f"{timeframe}_{file}"] = validation
        
        # Save validation results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        validation_file = os.path.join(
            self.data_dir, "timeframes", "summaries", f"validation_results_{timestamp}.json"
        )
        
        with open(validation_file, 'w') as f:
            json.dump(validation_results, f, indent=2, default=str)
        
        # Print validation summary
        valid_count = sum(1 for v in validation_results.values() if v.get("valid", False))
        total_count = len(validation_results)
        
        logger.info(f"🔍 Validation complete: {valid_count}/{total_count} files valid")
        logger.info(f"💾 Validation results saved to {validation_file}")
        
        return validation_results
    
    def create_timeframe_summary(self):
        """Create comprehensive timeframe summary"""
        logger.info("📋 Creating timeframe summary...")
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "timeframes": {},
            "currency_pairs": {},
            "total_files": 0,
            "total_candles": 0
        }
        
        # Analyze each timeframe
        for timeframe, config in self.timeframes.items():
            timeframe_dir = os.path.join(self.data_dir, "timeframes", config["directory"], "processed")
            
            if os.path.exists(timeframe_dir):
                files = [f for f in os.listdir(timeframe_dir) if f.endswith('.csv')]
                
                timeframe_summary = {
                    "files_count": len(files),
                    "currency_pairs": [],
                    "total_candles": 0,
                    "date_ranges": {}
                }
                
                for file in files:
                    try:
                        df = pd.read_csv(os.path.join(timeframe_dir, file))
                        currency_pair = file.replace(f'_{timeframe}.csv', '').upper()
                        
                        timeframe_summary["currency_pairs"].append(currency_pair)
                        timeframe_summary["total_candles"] += len(df)
                        
                        if 'timestamp' in df.columns:
                            timeframe_summary["date_ranges"][currency_pair] = {
                                "start": df['timestamp'].min(),
                                "end": df['timestamp'].max(),
                                "candles": len(df)
                            }
                        
                        summary["total_files"] += 1
                        summary["total_candles"] += len(df)
                        
                    except Exception as e:
                        logger.error(f"Error analyzing {file}: {e}")
                
                summary["timeframes"][timeframe] = timeframe_summary
        
        # Save summary
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = os.path.join(
            self.data_dir, "timeframes", "summaries", f"timeframe_summary_{timestamp}.json"
        )
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Print summary
        self._print_timeframe_summary(summary)
        
        logger.info(f"📋 Summary saved to {summary_file}")
        
        return summary
    
    def _print_timeframe_summary(self, summary: Dict[str, Any]):
        """Print timeframe summary"""
        print("\n" + "="*80)
        print("📊 MULTI-TIMEFRAME DATA SUMMARY")
        print("="*80)
        
        print(f"📁 Total Files: {summary['total_files']}")
        print(f"📈 Total Candles: {summary['total_candles']:,}")
        
        print(f"\n📊 Timeframe Breakdown:")
        for timeframe, data in summary["timeframes"].items():
            print(f"   {timeframe:>4}: {data['files_count']:>2} files, {data['total_candles']:>8,} candles")
        
        print(f"\n💱 Currency Pairs Available:")
        all_pairs = set()
        for timeframe_data in summary["timeframes"].values():
            all_pairs.update(timeframe_data["currency_pairs"])
        
        for pair in sorted(all_pairs):
            print(f"   • {pair}")
        
        print("\n" + "="*80)
    
    def organize_all_data(self):
        """Main function to organize all data"""
        logger.info("🚀 Starting multi-timeframe data organization...")
        
        # Find existing data
        existing_data = self.find_existing_data()
        
        # Create directory structure
        self.create_timeframe_structure()
        
        # Organize existing 1H data
        if existing_data["1h"]:
            self.organize_existing_1h_data(existing_data["1h"])
        
        # Generate higher timeframes from 1H data
        self.generate_all_timeframes_from_1h()
        
        # Validate all data
        self.validate_all_timeframes()
        
        # Create summary
        self.create_timeframe_summary()
        
        logger.info("🎉 Multi-timeframe data organization completed!")
        
        return True

def main():
    """Main execution function"""
    organizer = MultiTimeframeDataOrganizer()
    organizer.organize_all_data()

if __name__ == "__main__":
    main()

