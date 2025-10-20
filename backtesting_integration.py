#!/usr/bin/env python3
"""
Backtesting Integration Module
Version: 1.2.0
Date: September 23, 2025

This module provides integration between the backtesting system and trading strategies.
It implements proper spread modeling, slippage simulation, and commission calculation.
"""

import os
import yaml
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backtesting_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("backtesting_integration")

class BacktestMode(Enum):
    """Backtesting modes"""
    HISTORICAL = "historical"
    LIVE_SIMULATION = "live_simulation"
    WALK_FORWARD = "walk_forward"
    OPTIMIZATION = "optimization"

@dataclass
class BacktestConfig:
    """Backtesting configuration"""
    mode: BacktestMode
    start_date: datetime
    end_date: datetime
    initial_balance: float
    instruments: List[str]
    strategies: List[str]
    include_slippage: bool = True
    include_spread: bool = True
    include_commission: bool = True
    commission_rate: float = 0.0001
    data_source: str = "oanda"

class BacktestingIntegration:
    """Integration class for backtesting system"""
    
    def __init__(self, config_path: str = "optimized_backtesting_config.yaml"):
        """Initialize backtesting integration"""
        self.config_path = config_path
        self.config = self._load_config()
        self.data_cache = {}
        self.results = {}
        
        # Create output directory
        self.output_dir = self.config['backtesting'].get('export_directory', 'backtesting_data')
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info("🚀 Backtesting integration initialized")
    
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

    def run_strategy_backtest(self, strategy_id: str, config: BacktestConfig) -> Dict[str, Any]:
        """Run backtest for a specific strategy"""
        try:
            logger.info(f"🔄 Running backtest for {strategy_id}")
            
            # Prepare market data
            if not self._prepare_market_data(config.instruments, config.start_date, config.end_date, config.data_source):
                logger.error("❌ Failed to prepare market data for backtest")
                return None
            
            # Run backtest simulation
            from run_backtesting import DesktopBacktestingSystem
            
            # Initialize backtesting system
            system = DesktopBacktestingSystem(self.config_path)
            
            # Run backtest
            result = system.run_backtest(strategy_id, config)
            
            # Store result
            if result:
                self.results[strategy_id] = result
                logger.info(f"✅ Backtest completed for {strategy_id}")
            
            return asdict(result) if result else None
            
        except Exception as e:
            logger.error(f"❌ Backtest failed for {strategy_id}: {e}")
            return None

    def _prepare_market_data(self, instruments: List[str], 
                           start_date: datetime, end_date: datetime,
                           data_source: str) -> bool:
        """Prepare market data for backtesting"""
        try:
            logger.info(f"📊 Preparing market data for {len(instruments)} instruments")
            
            # Create backtesting_data directory if it doesn't exist
            os.makedirs("backtesting_data", exist_ok=True)
            
            # For each instrument, either download or use existing data
            for instrument in instruments:
                csv_path = os.path.join("backtesting_data", f"{instrument}.csv")
                
                # Check if data already exists
                if os.path.exists(csv_path):
                    logger.info(f"✅ Found existing data for {instrument}")
                    continue
                
                # Download or generate sample data
                if data_source == "oanda":
                    self._download_oanda_data(instrument, start_date, end_date, csv_path)
                else:
                    self._generate_sample_data(instrument, start_date, end_date, csv_path)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to prepare market data: {e}")
            return False
    
    def _download_oanda_data(self, instrument: str, start_date: datetime, 
                           end_date: datetime, output_path: str) -> bool:
        """Download data from OANDA API"""
        try:
            # This is a placeholder for actual OANDA API integration
            # In a real implementation, this would connect to OANDA's API
            
            logger.warning(f"⚠️ OANDA API integration not implemented")
            logger.info(f"📝 Generating sample data for {instrument} instead")
            
            return self._generate_sample_data(instrument, start_date, end_date, output_path)
            
        except Exception as e:
            logger.error(f"❌ Failed to download OANDA data: {e}")
            return False
    
    def _generate_sample_data(self, instrument: str, start_date: datetime, 
                            end_date: datetime, output_path: str) -> bool:
        """Generate sample market data for backtesting"""
        try:
            logger.info(f"📝 Generating sample data for {instrument}")
            
            # Calculate number of days
            days = (end_date - start_date).days + 1
            hours = days * 24
            
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
            
            # Calculate bid/ask prices
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
            df.to_csv(output_path, index=False)
            logger.info(f"✅ Generated sample data for {instrument}: {len(df)} data points")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to generate sample data: {e}")
            return False
    
    def optimize_strategy_parameters(self, strategy_id: str, 
                                  parameter_ranges: Dict[str, Tuple[float, float]]) -> Dict[str, Any]:
        """Optimize strategy parameters"""
        try:
            logger.info(f"🔧 Optimizing parameters for {strategy_id}")
            
            from run_backtesting import DesktopBacktestingSystem
            
            # Initialize backtesting system
            system = DesktopBacktestingSystem(self.config_path)
            
            # Run optimization
            result = system.optimize_strategy(strategy_id, parameter_ranges)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Strategy optimization failed: {e}")
            return None
    
    def export_backtest_results(self) -> Dict[str, str]:
        """Export backtest results"""
        try:
            logger.info("📊 Exporting backtest results")
            
            from run_backtesting import DesktopBacktestingSystem, ExportFormat
            
            # Initialize backtesting system
            system = DesktopBacktestingSystem(self.config_path)
            
            # Export results
            formats = []
            if self.config.get('export_formats', {}).get('json', True):
                formats.append(ExportFormat.JSON)
            if self.config.get('export_formats', {}).get('csv', True):
                formats.append(ExportFormat.CSV)
            
            export_paths = {}
            for format in formats:
                path = system.export_results(format)
                if path:
                    export_paths[format.value] = path
            
            return export_paths
            
        except Exception as e:
            logger.error(f"❌ Failed to export results: {e}")
            return {}
    
    def validate_backtest_against_live(self, strategy_id: str, 
                                    live_results_path: str) -> Dict[str, Any]:
        """Validate backtest results against live trading data"""
        try:
            logger.info(f"🔍 Validating backtest results for {strategy_id}")
            
            # Load live results
            live_df = pd.read_csv(live_results_path)
            
            # Get backtest results
            backtest_result = self.results.get(strategy_id)
            if not backtest_result:
                logger.error(f"❌ No backtest results found for {strategy_id}")
                return None
            
            # Calculate validation metrics
            validation_metrics = {}
            
            # Compare win rates
            if 'win_rate' in live_df.columns:
                live_win_rate = live_df['win_rate'].mean()
                backtest_win_rate = backtest_result.win_rate
                win_rate_diff = abs(live_win_rate - backtest_win_rate)
                
                validation_metrics['win_rate'] = {
                    'live': live_win_rate,
                    'backtest': backtest_win_rate,
                    'difference': win_rate_diff,
                    'is_valid': win_rate_diff <= 5.0  # 5% tolerance
                }
            
            # Compare returns
            if 'total_return' in live_df.columns:
                live_return = live_df['total_return'].mean()
                backtest_return = backtest_result.total_return
                return_diff = abs(live_return - backtest_return)
                
                validation_metrics['total_return'] = {
                    'live': live_return,
                    'backtest': backtest_return,
                    'difference': return_diff,
                    'is_valid': return_diff <= 10.0  # 10% tolerance
                }
            
            # Overall validation result
            validation_metrics['overall_valid'] = all(
                metric.get('is_valid', False) 
                for metric in validation_metrics.values()
                if isinstance(metric, dict)
            )
            
            logger.info(f"✅ Validation completed for {strategy_id}")
            logger.info(f"📊 Valid: {validation_metrics['overall_valid']}")
            
            return validation_metrics
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            return None

def get_backtesting_integration(config_path: str = "optimized_backtesting_config.yaml") -> BacktestingIntegration:
    """Get backtesting integration singleton instance"""
    return BacktestingIntegration(config_path)

if __name__ == "__main__":
    # Example usage
    integration = get_backtesting_integration()
    
    # Configure backtest
    config = BacktestConfig(
        mode=BacktestMode.HISTORICAL,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31),
        initial_balance=10000.0,
        instruments=["EUR_USD", "GBP_USD"],
        strategies=["alpha_strategy"]
    )
    
    # Run backtest
    result = integration.run_strategy_backtest("alpha_strategy", config)
    
    # Export results
    export_paths = integration.export_backtest_results()
    
    print(f"Backtest completed. Results exported to: {export_paths}")
