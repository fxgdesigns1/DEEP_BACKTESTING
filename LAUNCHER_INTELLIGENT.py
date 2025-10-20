#!/usr/bin/env python3
"""
INTELLIGENT LAUNCHER
====================

Easy launcher for the intelligent news downloader system.
Provides menu options and status checking.
"""

import os
import sys
from pathlib import Path
import json
from datetime import datetime

def check_system_status():
    """Check the current status of the intelligent download system"""
    print("🔍 CHECKING SYSTEM STATUS")
    print("=" * 30)
    
    # Check cache directory
    cache_dir = Path('data/cache')
    if cache_dir.exists():
        cache_files = list(cache_dir.glob('*'))
        print(f"📁 Cache directory: {len(cache_files)} cached files")
    else:
        print("📁 Cache directory: Not created yet")
    
    # Check data directories
    data_dirs = [
        'data/economic/fred_free',
        'data/economic/alphavantage_free', 
        'data/market/yahoo_finance',
        'data/news/newsdata_free',
        'data/integrated_free'
    ]
    
    print("\n📊 Data Status:")
    for data_dir in data_dirs:
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
                
                print(f"\n📈 Data Summary:")
                print(f"  FRED Indicators: {summary.get('fred_indicators', 0)}")
                print(f"  Alpha Vantage: {summary.get('alphavantage_indicators', 0)}")
                print(f"  Yahoo Finance: {summary.get('yahoo_symbols', 0)}")
                print(f"  News Articles: {summary.get('news_articles', 0)}")
                
                print(f"\n🗂️  Cache Status:")
                for cache_type, status in cache_status.items():
                    status_icon = "✅" if status else "❌"
                    print(f"  {status_icon} {cache_type.replace('_cache_valid', '').title()}")
        except Exception as e:
            print(f"⚠️ Error reading integrated dataset: {e}")
    else:
        print("\n❌ No integrated dataset found")

def clear_cache():
    """Clear the cache directory"""
    import shutil
    cache_dir = Path('data/cache')
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        print("🗑️  Cache cleared successfully!")
    else:
        print("📁 No cache to clear")

def run_intelligent_download():
    """Run the intelligent downloader"""
    print("🚀 Starting Intelligent Download...")
    print("=" * 40)
    
    try:
        from INTELLIGENT_NEWS_DOWNLOADER import IntelligentDownloader
        downloader = IntelligentDownloader()
        downloader.run_intelligent_download()
    except ImportError as e:
        print(f"❌ Error importing intelligent downloader: {e}")
        print("Make sure INTELLIGENT_NEWS_DOWNLOADER.py is in the current directory")
    except Exception as e:
        print(f"❌ Error running intelligent download: {e}")

def show_menu():
    """Show the main menu"""
    print("\n🎯 INTELLIGENT NEWS DOWNLOADER MENU")
    print("=" * 40)
    print("1. 📊 Check System Status")
    print("2. 🚀 Run Intelligent Download")
    print("3. 🗑️  Clear Cache (Force Fresh Download)")
    print("4. 📁 View Data Directories")
    print("5. ❌ Exit")
    print("=" * 40)

def view_data_directories():
    """View contents of data directories"""
    print("\n📁 DATA DIRECTORY CONTENTS")
    print("=" * 35)
    
    directories = [
        ('Economic Data (FRED)', 'data/economic/fred_free'),
        ('Economic Data (Alpha Vantage)', 'data/economic/alphavantage_free'),
        ('Market Data (Yahoo Finance)', 'data/market/yahoo_finance'),
        ('News Data', 'data/news/newsdata_free'),
        ('Integrated Dataset', 'data/integrated_free'),
        ('Cache', 'data/cache')
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

def main():
    """Main launcher function"""
    print("🌟 WELCOME TO INTELLIGENT NEWS DOWNLOADER")
    print("=" * 50)
    print("Advanced news and economic data downloader")
    print("with intelligent caching and incremental updates")
    print()
    
    while True:
        show_menu()
        
        try:
            choice = input("\n🎯 Enter your choice (1-5): ").strip()
            
            if choice == '1':
                check_system_status()
            elif choice == '2':
                run_intelligent_download()
            elif choice == '3':
                confirm = input("⚠️  Are you sure you want to clear the cache? (y/N): ").strip().lower()
                if confirm in ['y', 'yes']:
                    clear_cache()
                else:
                    print("❌ Cache clear cancelled")
            elif choice == '4':
                view_data_directories()
            elif choice == '5':
                print("\n👋 Goodbye! Happy trading!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-5.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Happy trading!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
        
        input("\n⏸️  Press Enter to continue...")

if __name__ == "__main__":
    main()
