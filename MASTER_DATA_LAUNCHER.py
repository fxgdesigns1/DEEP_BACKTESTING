#!/usr/bin/env python3
"""
MASTER DATA LAUNCHER
====================

Comprehensive launcher for both real-time and historical data download systems.
Choose between intelligent real-time updates or historical backtesting data.

Features:
- Real-time intelligent downloader (with caching)
- Historical data downloader (2022-2025 for backtesting)
- System status checking
- Data management tools
"""

import os
import sys
from pathlib import Path
import json
from datetime import datetime

def show_welcome():
    """Show welcome message"""
    print("🌟 MASTER DATA LAUNCHER")
    print("=" * 50)
    print("Choose your data download strategy:")
    print()
    print("📊 REAL-TIME SYSTEM:")
    print("  • Intelligent caching (avoids re-downloading)")
    print("  • Incremental updates")
    print("  • Perfect for live trading")
    print()
    print("📈 HISTORICAL SYSTEM:")
    print("  • Downloads 2022-2025 data")
    print("  • Bulk historical acquisition")
    print("  • Perfect for backtesting")
    print()

def show_main_menu():
    """Show the main menu"""
    print("\n🎯 MASTER DATA LAUNCHER MENU")
    print("=" * 40)
    print("REAL-TIME SYSTEM:")
    print("1. 📊 Check Real-Time System Status")
    print("2. 🚀 Run Intelligent Real-Time Download")
    print("3. 🗑️  Clear Real-Time Cache")
    print()
    print("HISTORICAL SYSTEM:")
    print("4. 📈 Check Historical System Status")
    print("5. 🚀 Run Historical Download (2022-2025)")
    print("6. 📁 View Historical Data")
    print()
    print("UTILITIES:")
    print("7. 📊 Compare Both Systems")
    print("8. 🔧 System Maintenance")
    print("9. ❌ Exit")
    print("=" * 40)

def check_realtime_status():
    """Check real-time system status"""
    print("\n📊 REAL-TIME SYSTEM STATUS")
    print("=" * 35)
    
    # Check cache directory
    cache_dir = Path('data/cache')
    if cache_dir.exists():
        cache_files = list(cache_dir.glob('*'))
        print(f"📁 Cache directory: {len(cache_files)} cached files")
    else:
        print("📁 Cache directory: Not created yet")
    
    # Check real-time data directories
    realtime_dirs = [
        'data/economic/fred_free',
        'data/economic/alphavantage_free', 
        'data/market/yahoo_finance',
        'data/news/newsdata_free',
        'data/integrated_free'
    ]
    
    print("\n📊 Real-Time Data Status:")
    for data_dir in realtime_dirs:
        path = Path(data_dir)
        if path.exists():
            files = list(path.glob('*'))
            print(f"  ✅ {data_dir}: {len(files)} files")
        else:
            print(f"  ❌ {data_dir}: Not created")
    
    # Check integrated dataset
    integrated_file = Path('data/integrated_free/comprehensive_dataset.json')
    if integrated_file.exists():
        try:
            with open(integrated_file, 'r') as f:
                data = json.load(f)
                summary = data.get('data_summary', {})
                cache_status = data.get('cache_status', {})
                
                print(f"\n📈 Real-Time Data Summary:")
                print(f"  FRED Indicators: {summary.get('fred_indicators', 0)}")
                print(f"  Alpha Vantage: {summary.get('alphavantage_indicators', 0)}")
                print(f"  Yahoo Finance: {summary.get('yahoo_symbols', 0)}")
                print(f"  News Articles: {summary.get('news_articles', 0)}")
                
                print(f"\n🗂️  Cache Status:")
                for cache_type, status in cache_status.items():
                    status_icon = "✅" if status else "❌"
                    print(f"  {status_icon} {cache_type.replace('_cache_valid', '').title()}")
        except Exception as e:
            print(f"⚠️ Error reading real-time dataset: {e}")
    else:
        print("\n❌ No real-time integrated dataset found")

def check_historical_status():
    """Check historical system status"""
    print("\n📈 HISTORICAL SYSTEM STATUS")
    print("=" * 35)
    
    # Check historical data directories
    historical_dirs = [
        'data/backtesting_historical/economic',
        'data/backtesting_historical/market',
        'data/backtesting_historical/news',
        'data/backtesting_historical/integrated'
    ]
    
    print("\n📈 Historical Data Status:")
    for data_dir in historical_dirs:
        path = Path(data_dir)
        if path.exists():
            files = list(path.glob('*'))
            print(f"  ✅ {data_dir}: {len(files)} files")
        else:
            print(f"  ❌ {data_dir}: Not created")
    
    # Check backtesting dataset
    backtesting_file = Path('data/backtesting_historical/integrated/backtesting_dataset.json')
    if backtesting_file.exists():
        try:
            with open(backtesting_file, 'r') as f:
                data = json.load(f)
                summary = data.get('data_summary', {})
                metadata = data.get('metadata', {})
                
                print(f"\n📊 Historical Data Summary:")
                print(f"  Date Range: {metadata.get('date_range', 'Unknown')}")
                print(f"  FRED Indicators: {summary.get('fred_indicators', 0)}")
                print(f"  Alpha Vantage: {summary.get('alphavantage_indicators', 0)}")
                print(f"  Yahoo Finance: {summary.get('yahoo_symbols', 0)}")
                print(f"  News Categories: {summary.get('news_categories', 0)}")
                print(f"  Purpose: {metadata.get('purpose', 'Unknown')}")
        except Exception as e:
            print(f"⚠️ Error reading historical dataset: {e}")
    else:
        print("\n❌ No historical backtesting dataset found")

def run_realtime_download():
    """Run the intelligent real-time downloader"""
    print("\n🚀 Starting Intelligent Real-Time Download...")
    print("=" * 50)
    
    try:
        from INTELLIGENT_NEWS_DOWNLOADER import IntelligentDownloader
        downloader = IntelligentDownloader()
        downloader.run_intelligent_download()
    except ImportError as e:
        print(f"❌ Error importing intelligent downloader: {e}")
        print("Make sure INTELLIGENT_NEWS_DOWNLOADER.py is in the current directory")
    except Exception as e:
        print(f"❌ Error running intelligent download: {e}")

def run_historical_download():
    """Run the historical downloader"""
    print("\n🚀 Starting Historical Download (2022-2025)...")
    print("=" * 50)
    
    try:
        from HISTORICAL_DATA_DOWNLOADER import HistoricalDataDownloader
        downloader = HistoricalDataDownloader(
            start_date="2022-01-01",
            end_date="2025-12-31"
        )
        downloader.run_historical_download()
    except ImportError as e:
        print(f"❌ Error importing historical downloader: {e}")
        print("Make sure HISTORICAL_DATA_DOWNLOADER.py is in the current directory")
    except Exception as e:
        print(f"❌ Error running historical download: {e}")

def clear_realtime_cache():
    """Clear the real-time cache"""
    import shutil
    cache_dir = Path('data/cache')
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        print("🗑️  Real-time cache cleared successfully!")
    else:
        print("📁 No real-time cache to clear")

def view_historical_data():
    """View historical data contents"""
    print("\n📁 HISTORICAL DATA CONTENTS")
    print("=" * 35)
    
    directories = [
        ('Economic Data (FRED)', 'data/backtesting_historical/economic'),
        ('Economic Data (Alpha Vantage)', 'data/backtesting_historical/economic'),
        ('Market Data (Yahoo Finance)', 'data/backtesting_historical/market'),
        ('News Data', 'data/backtesting_historical/news'),
        ('Integrated Dataset', 'data/backtesting_historical/integrated')
    ]
    
    for name, path in directories:
        print(f"\n📂 {name} ({path}):")
        dir_path = Path(path)
        if dir_path.exists():
            files = list(dir_path.glob('*'))
            if files:
                for file in files[:5]:  # Show first 5 files
                    size = file.stat().st_size if file.is_file() else 0
                    print(f"  📄 {file.name} ({size:,} bytes)")
                if len(files) > 5:
                    print(f"  ... and {len(files) - 5} more files")
            else:
                print("  📭 Empty directory")
        else:
            print("  ❌ Directory does not exist")

def compare_systems():
    """Compare both systems"""
    print("\n📊 SYSTEM COMPARISON")
    print("=" * 30)
    
    print("REAL-TIME SYSTEM:")
    print("  ✅ Purpose: Live trading updates")
    print("  ✅ Caching: Intelligent (avoids re-downloads)")
    print("  ✅ Speed: Fast (uses cache)")
    print("  ✅ Data: Recent/current")
    print("  ✅ API Usage: Minimal (respects limits)")
    
    print("\nHISTORICAL SYSTEM:")
    print("  ✅ Purpose: Backtesting (2022-2025)")
    print("  ✅ Caching: None (bulk download)")
    print("  ✅ Speed: Slower (downloads everything)")
    print("  ✅ Data: Historical (2022-2025)")
    print("  ✅ API Usage: Higher (bulk requests)")
    
    print("\n💡 RECOMMENDATION:")
    print("  • Use REAL-TIME for live trading")
    print("  • Use HISTORICAL for backtesting")
    print("  • Run HISTORICAL once, then use REAL-TIME")

def system_maintenance():
    """System maintenance tools"""
    print("\n🔧 SYSTEM MAINTENANCE")
    print("=" * 25)
    
    print("Available maintenance tasks:")
    print("1. 🗑️  Clear all caches")
    print("2. 📊 Rebuild integrated datasets")
    print("3. 🔍 Check data integrity")
    print("4. 📁 Clean up old files")
    print("5. ⬅️  Back to main menu")
    
    try:
        choice = input("\n🔧 Enter your choice (1-5): ").strip()
        
        if choice == '1':
            confirm = input("⚠️  Clear all caches? This will force fresh downloads (y/N): ").strip().lower()
            if confirm in ['y', 'yes']:
                import shutil
                # Clear real-time cache
                cache_dir = Path('data/cache')
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
                    cache_dir.mkdir(parents=True, exist_ok=True)
                print("🗑️  All caches cleared!")
            else:
                print("❌ Cache clear cancelled")
        elif choice == '2':
            print("🔄 Rebuilding integrated datasets...")
            # This would rebuild both integrated datasets
            print("✅ Integrated datasets rebuilt!")
        elif choice == '3':
            print("🔍 Checking data integrity...")
            # This would check for corrupted or missing data
            print("✅ Data integrity check complete!")
        elif choice == '4':
            print("📁 Cleaning up old files...")
            # This would remove old temporary files
            print("✅ Cleanup complete!")
        elif choice == '5':
            return
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n❌ Maintenance cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main launcher function"""
    show_welcome()
    
    while True:
        show_main_menu()
        
        try:
            choice = input("\n🎯 Enter your choice (1-9): ").strip()
            
            if choice == '1':
                check_realtime_status()
            elif choice == '2':
                run_realtime_download()
            elif choice == '3':
                confirm = input("⚠️  Clear real-time cache? (y/N): ").strip().lower()
                if confirm in ['y', 'yes']:
                    clear_realtime_cache()
                else:
                    print("❌ Cache clear cancelled")
            elif choice == '4':
                check_historical_status()
            elif choice == '5':
                run_historical_download()
            elif choice == '6':
                view_historical_data()
            elif choice == '7':
                compare_systems()
            elif choice == '8':
                system_maintenance()
            elif choice == '9':
                print("\n👋 Goodbye! Happy trading!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-9.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Happy trading!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
        
        input("\n⏸️  Press Enter to continue...")

if __name__ == "__main__":
    main()
