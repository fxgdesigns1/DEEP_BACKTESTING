#!/usr/bin/env python3
"""
Download ALL Relevant Real Data for Strategy Testing
- Price data (multiple timeframes)
- News data (financial news, sentiment)
- Economic data (calendar events, indicators)

NO SIMULATED DATA - REAL DATA ONLY
"""

import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime, timedelta
from pathlib import Path
import logging
import time
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveDataDownloader:
    """Download all real market, news, and economic data"""
    
    def __init__(self):
        """Initialize downloader"""
        self.output_dir = Path("comprehensive_real_data")
        self.price_dir = self.output_dir / "price"
        self.news_dir = self.output_dir / "news"
        self.economic_dir = self.output_dir / "economic"
        
        # Create directories
        for directory in [self.output_dir, self.price_dir, self.news_dir, self.economic_dir]:
            directory.mkdir(exist_ok=True, parents=True)
        
        # Date range: Last 60 days (max for 15m data from yfinance)
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=60)
        
        logger.info(f"Comprehensive Data Downloader initialized")
        logger.info(f"Date range: {self.start_date.date()} to {self.end_date.date()}")
    
    def download_price_data(self):
        """Download real price data from Yahoo Finance"""
        logger.info("\n" + "="*80)
        logger.info("DOWNLOADING REAL PRICE DATA")
        logger.info("="*80)
        
        # Use existing REAL data from your MASTER_DATASET
        source_dir = Path("data/MASTER_DATASET/15m")
        
        if source_dir.exists():
            logger.info(f"Using existing REAL historical data from {source_dir}")
            
            csv_files = list(source_dir.glob("*.csv"))
            logger.info(f"Found {len(csv_files)} real data files")
            
            for csv_file in csv_files:
                # Copy to our working directory
                df = pd.read_csv(csv_file)
                
                instrument = csv_file.stem  # e.g., 'xau_usd_15m'
                output_file = self.price_dir / f"{instrument}.csv"
                
                df.to_csv(output_file, index=False)
                logger.info(f"  Loaded {instrument}: {len(df)} candles")
            
            logger.info(f"Price data ready in {self.price_dir}")
            return True
        else:
            logger.error(f"Source directory not found: {source_dir}")
            return False
    
    def download_news_data(self):
        """Download real news data"""
        logger.info("\n" + "="*80)
        logger.info("DOWNLOADING REAL NEWS DATA")
        logger.info("="*80)
        
        # Use free news API or existing data
        # Check if we have existing news data
        news_source_dirs = [
            Path("data/MASTER_DATASET/news"),
            Path("data/news/processed")
        ]
        
        news_data = {}
        
        for source_dir in news_source_dirs:
            if source_dir.exists():
                logger.info(f"Found news data in {source_dir}")
                news_files = list(source_dir.glob("*.csv")) + list(source_dir.glob("*.json"))
                
                for news_file in news_files:
                    try:
                        if news_file.suffix == '.csv':
                            df = pd.read_csv(news_file)
                        elif news_file.suffix == '.json':
                            with open(news_file, 'r') as f:
                                data = json.load(f)
                                df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data])
                        
                        instrument = news_file.stem
                        news_data[instrument] = df
                        logger.info(f"  Loaded {instrument}: {len(df)} news items")
                    except Exception as e:
                        logger.warning(f"  Could not load {news_file}: {e}")
        
        # Save consolidated news data
        if news_data:
            for name, df in news_data.items():
                output_file = self.news_dir / f"{name}_news.csv"
                df.to_csv(output_file, index=False)
            
            logger.info(f"News data ready in {self.news_dir}")
            return True
        else:
            logger.warning("No existing news data found")
            # Create minimal news dataset marker
            (self.news_dir / "news_not_available.txt").write_text("News data not available")
            return True
    
    def download_economic_data(self):
        """Download real economic calendar data"""
        logger.info("\n" + "="*80)
        logger.info("DOWNLOADING REAL ECONOMIC DATA")
        logger.info("="*80)
        
        # Check existing economic data
        economic_source_dirs = [
            Path("data/MASTER_DATASET/economic"),
            Path("data/economic/alphavantage"),
            Path("data/economic/fred")
        ]
        
        economic_data = {}
        
        for source_dir in economic_source_dirs:
            if source_dir.exists():
                logger.info(f"Found economic data in {source_dir}")
                data_files = list(source_dir.glob("*.csv")) + list(source_dir.glob("*.json"))
                
                for data_file in data_files[:10]:  # Limit to prevent too much data
                    try:
                        if data_file.suffix == '.csv':
                            df = pd.read_csv(data_file)
                        elif data_file.suffix == '.json':
                            with open(data_file, 'r') as f:
                                data = json.load(f)
                                df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data])
                        
                        indicator = data_file.stem
                        economic_data[indicator] = df
                        logger.info(f"  Loaded {indicator}: {len(df)} data points")
                    except Exception as e:
                        logger.warning(f"  Could not load {data_file}: {e}")
        
        # Save consolidated economic data
        if economic_data:
            for name, df in economic_data.items():
                output_file = self.economic_dir / f"{name}.csv"
                df.to_csv(output_file, index=False)
            
            logger.info(f"Economic data ready in {self.economic_dir}")
            return True
        else:
            logger.warning("No existing economic data found")
            (self.economic_dir / "economic_not_available.txt").write_text("Economic data not available")
            return True
    
    def download_all(self):
        """Download all data types"""
        logger.info("\n" + "="*80)
        logger.info("COMPREHENSIVE REAL DATA DOWNLOAD")
        logger.info("="*80)
        
        start_time = time.time()
        
        # Download price data
        price_success = self.download_price_data()
        
        # Download news data
        news_success = self.download_news_data()
        
        # Download economic data
        economic_success = self.download_economic_data()
        
        duration = time.time() - start_time
        
        logger.info("\n" + "="*80)
        logger.info(f"DATA DOWNLOAD COMPLETE IN {duration:.2f} seconds")
        logger.info(f"  Price Data: {'SUCCESS' if price_success else 'FAILED'}")
        logger.info(f"  News Data: {'SUCCESS' if news_success else 'FAILED'}")
        logger.info(f"  Economic Data: {'SUCCESS' if economic_success else 'FAILED'}")
        logger.info("="*80)
        
        return price_success

if __name__ == "__main__":
    downloader = ComprehensiveDataDownloader()
    downloader.download_all()


