#!/usr/bin/env python3
"""
Desktop Backtesting Export Tool
Version: 1.2.0
Date: September 23, 2025

This tool exports market data and configurations for desktop backtesting.
It includes Bloomberg data correlation and spread analysis for realistic trading costs.
"""

import os
import sys
import yaml
import json
import logging
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("export_backtesting.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("export_desktop_backtesting")

class DesktopBacktestingExporter:
    """Export tool for desktop backtesting"""
    
    def __init__(self, config_path: str = "optimized_backtesting_config.yaml"):
        """Initialize the export tool"""
        self.config_path = config_path
        self.config = self._load_config()
        
        # Create output directories
        self.output_dir = None  # Will be set in export_data()
        
        logger.info("🚀 Desktop Backtesting Export Tool initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"✅ Configuration loaded from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"❌ Failed to load configuration: {e}")
            return {}
    
    def export_data(self, instruments: List[str], days: int, output_dir: str) -> bool:
        """Export data for desktop backtesting"""
        try:
            self.output_dir = output_dir
            os.makedirs(output_dir, exist_ok=True)
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"📊 Exporting data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            
            # Export each instrument's data
            for instrument in instruments:
                self._export_instrument_data(instrument, start_date, end_date)
            
            # Export Bloomberg mapping
            self._export_bloomberg_mapping(instruments)
            
            # Export configuration
            self._export_config()
            
            # Create README
            self._create_readme(instruments, days)
            
            logger.info(f"✅ Export completed to {output_dir}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Export failed: {e}")
            return False
    
    def _export_instrument_data(self, instrument: str, start_date: datetime, end_date: datetime) -> bool:
        """Export data for a specific instrument"""
        try:
            logger.info(f"📝 Exporting data for {instrument}")
            
            # Check if we have real data or need to generate sample data
            data_file = os.path.join("backtesting_data", f"{instrument}.csv")
            
            if os.path.exists(data_file):
                # Use existing data
                df = pd.read_csv(data_file)
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Filter by date range
                mask = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)
                df_filtered = df.loc[mask].copy()
                
                if df_filtered.empty:
                    logger.warning(f"⚠️ No data for {instrument} in specified date range")
                    return self._generate_export_data(instrument, start_date, end_date)
                
                logger.info(f"✅ Using existing data for {instrument}: {len(df_filtered)} data points")
            else:
                # Generate sample data
                return self._generate_export_data(instrument, start_date, end_date)
            
            # Add spread modeling
            self._enhance_with_spread_modeling(df_filtered, instrument)
            
            # Add slippage estimates
            self._add_slippage_estimates(df_filtered, instrument)
            
            # Export to CSV
            output_file = os.path.join(self.output_dir, f"{instrument}.csv")
            df_filtered.to_csv(output_file, index=False)
            
            logger.info(f"✅ Exported {len(df_filtered)} data points for {instrument}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to export data for {instrument}: {e}")
            return False
    
    def _generate_export_data(self, instrument: str, start_date: datetime, end_date: datetime) -> bool:
        """Generate sample data for export when real data is not available"""
        try:
            logger.info(f"📝 Generating sample data for {instrument}")
            
            # Calculate number of hours
            hours = int((end_date - start_date).total_seconds() / 3600) + 1
            
            # Generate timestamps
            timestamps = [start_date + timedelta(hours=i) for i in range(hours)]
            
            # Generate price data
            base_price = 1.0
            if instrument == "EUR_USD":
                base_price = 1.1
            elif instrument == "GBP_USD":
                base_price = 1.3
            elif instrument == "USD_JPY":
                base_price = 110.0
            elif instrument == "XAU_USD":
                base_price = 1800.0
            
            # Generate random price movements
            np.random.seed(42)  # For reproducibility
            price_changes = np.random.normal(0, 0.0001, hours)
            prices = np.cumsum(price_changes) + base_price
            
            # Calculate bid/ask prices with realistic spread
            spread_factor = self.config['spread_modeling']['instrument_factors'].get(instrument, 1.0)
            base_spread = 0.0001  # 1 pip
            spread = base_spread * spread_factor
            
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
            
            # Add spread modeling
            self._enhance_with_spread_modeling(df, instrument)
            
            # Add slippage estimates
            self._add_slippage_estimates(df, instrument)
            
            # Export to CSV
            output_file = os.path.join(self.output_dir, f"{instrument}.csv")
            df.to_csv(output_file, index=False)
            
            logger.info(f"✅ Generated and exported {len(df)} data points for {instrument}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to generate sample data for {instrument}: {e}")
            return False
    
    def _enhance_with_spread_modeling(self, df: pd.DataFrame, instrument: str) -> None:
        """Enhance data with realistic spread modeling"""
        try:
            # Get spread modeling configuration
            spread_config = self.config.get('spread_modeling', {})
            instrument_factor = spread_config.get('instrument_factors', {}).get(instrument, 1.0)
            
            # Add hour of day and day of week
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            
            # Determine market session for each row
            def get_session(row):
                hour = row['hour']
                if 0 <= hour < 8:
                    return 'asian'
                elif 8 <= hour < 16:
                    return 'european'
                else:
                    return 'us'
            
            df['session'] = df.apply(get_session, axis=1)
            
            # Calculate session factor
            session_factors = spread_config.get('session_factors', {})
            df['session_factor'] = df['session'].map(session_factors).fillna(1.0)
            
            # Weekend factor
            df['is_weekend'] = df['day_of_week'].isin([5, 6])  # Saturday or Sunday
            df.loc[df['is_weekend'], 'session_factor'] = spread_config.get('session_factors', {}).get('weekend', 1.5)
            
            # Calculate realistic spread
            base_spread = df['ask'] - df['bid']
            df['realistic_spread'] = base_spread * df['session_factor'] * instrument_factor
            
            # Adjust bid and ask prices
            df['realistic_bid'] = df['mid_price'] - df['realistic_spread'] / 2
            df['realistic_ask'] = df['mid_price'] + df['realistic_spread'] / 2
            
            # Replace original bid/ask with realistic ones
            df['original_bid'] = df['bid']
            df['original_ask'] = df['ask']
            df['bid'] = df['realistic_bid']
            df['ask'] = df['realistic_ask']
            
            # Clean up temporary columns
            df.drop(['hour', 'day_of_week', 'session', 'session_factor', 'is_weekend', 
                    'realistic_spread', 'realistic_bid', 'realistic_ask'], axis=1, inplace=True)
            
        except Exception as e:
            logger.error(f"❌ Failed to enhance spread modeling: {e}")
    
    def _add_slippage_estimates(self, df: pd.DataFrame, instrument: str) -> None:
        """Add slippage estimates to the data"""
        try:
            # Get slippage configuration
            slippage_config = self.config.get('slippage_simulation', {})
            base_slippage = slippage_config.get('base_slippage_pips', {}).get(instrument, 0.1) / 10000
            
            # Calculate volatility (simple implementation - standard deviation of returns)
            df['returns'] = df['mid_price'].pct_change().fillna(0)
            df['volatility'] = df['returns'].rolling(window=24).std().fillna(0)
            
            # Calculate volume factor (normalized)
            df['norm_volume'] = (df['volume'] - df['volume'].min()) / (df['volume'].max() - df['volume'].min() + 1e-10)
            
            # Calculate slippage
            volatility_factor = slippage_config.get('volatility_factor', 0.5)
            volume_factor = slippage_config.get('volume_factor', -0.3)
            
            df['slippage'] = (base_slippage + 
                            base_slippage * volatility_factor * df['volatility'] +
                            base_slippage * volume_factor * df['norm_volume'])
            
            # Ensure minimum slippage
            df['slippage'] = np.maximum(df['slippage'], base_slippage * 0.5)
            
            # Clean up temporary columns
            df.drop(['returns', 'volatility', 'norm_volume'], axis=1, inplace=True)
            
        except Exception as e:
            logger.error(f"❌ Failed to add slippage estimates: {e}")
    
    def _export_bloomberg_mapping(self, instruments: List[str]) -> None:
        """Export Bloomberg ticker mapping"""
        try:
            # Get Bloomberg configuration
            bloomberg_config = self.config.get('bloomberg_integration', {})
            if not bloomberg_config.get('enabled', False):
                logger.info("ℹ️ Bloomberg integration disabled, skipping mapping export")
                return
            
            # Get ticker mapping
            ticker_mapping = bloomberg_config.get('ticker_mapping', {})
            
            # Create mapping for selected instruments
            mapping = {instrument: ticker_mapping.get(instrument, f"{instrument} Curncy") 
                     for instrument in instruments}
            
            # Export to JSON
            mapping_file = os.path.join(self.output_dir, "bloomberg_mapping.json")
            with open(mapping_file, 'w') as f:
                json.dump({
                    'ticker_mapping': mapping,
                    'data_fields': bloomberg_config.get('data_fields', [])
                }, f, indent=2)
            
            logger.info(f"✅ Exported Bloomberg mapping for {len(mapping)} instruments")
            
        except Exception as e:
            logger.error(f"❌ Failed to export Bloomberg mapping: {e}")
    
    def _export_config(self) -> None:
        """Export configuration for desktop backtesting"""
        try:
            # Create a simplified configuration for desktop systems
            desktop_config = {
                'backtesting': self.config.get('backtesting', {}),
                'strategies': self.config.get('strategies', {}),
                'spread_modeling': self.config.get('spread_modeling', {}),
                'slippage_simulation': self.config.get('slippage_simulation', {}),
                'performance_metrics': self.config.get('performance_metrics', {})
            }
            
            # Export to YAML
            config_file = os.path.join(self.output_dir, "desktop_config.yaml")
            with open(config_file, 'w') as f:
                yaml.dump(desktop_config, f)
            
            logger.info(f"✅ Exported desktop configuration")
            
        except Exception as e:
            logger.error(f"❌ Failed to export configuration: {e}")
    
    def _create_readme(self, instruments: List[str], days: int) -> None:
        """Create README with validation instructions"""
        try:
            readme_content = f"""# Desktop Backtesting Data Export
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Data Period: {(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}
Instruments: {', '.join(instruments)}

## Data Files
{chr(10).join([f"- {instrument}.csv - Price data with realistic spreads and slippage estimates" for instrument in instruments])}
- desktop_config.yaml - Configuration for backtesting parameters
- bloomberg_mapping.json - Bloomberg ticker mapping for validation

## Validation Instructions

### Basic Backtesting
1. Import the CSV files into your desktop backtesting software
2. Configure spread and slippage parameters from desktop_config.yaml
3. Run backtests with your strategy

### Bloomberg Data Validation
1. Use the provided mapping in bloomberg_mapping.json
2. Compare price data with Bloomberg terminal data
3. Validate spread patterns against market session times

### Performance Metrics
Calculate the following metrics to compare with the cloud-based system:
- Total return
- Max drawdown
- Sharpe ratio
- Win rate
- Profit factor

## Notes
- All data includes realistic spreads based on market sessions
- Slippage estimates are included based on volatility and volume
- For support, contact: fxgdesigns1@gmail.com
"""
            
            # Write README
            readme_file = os.path.join(self.output_dir, "README.md")
            with open(readme_file, 'w') as f:
                f.write(readme_content)
            
            logger.info(f"✅ Created README with validation instructions")
            
        except Exception as e:
            logger.error(f"❌ Failed to create README: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Desktop Backtesting Export Tool")
    parser.add_argument("--config", default="optimized_backtesting_config.yaml", help="Configuration file")
    parser.add_argument("--days", type=int, default=30, help="Number of days to export")
    parser.add_argument("--output", default="desktop_export", help="Output directory")
    parser.add_argument("--instruments", nargs='+', default=["EUR_USD", "GBP_USD", "USD_JPY", "XAU_USD"], 
                      help="Instruments to export")
    
    args = parser.parse_args()
    
    logger.info("🚀 Starting Desktop Backtesting Export Tool")
    
    # Initialize export tool
    exporter = DesktopBacktestingExporter(args.config)
    
    # Export data
    success = exporter.export_data(args.instruments, args.days, args.output)
    
    if success:
        logger.info(f"✅ Export completed successfully to {args.output}")
        return 0
    else:
        logger.error("❌ Export failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
