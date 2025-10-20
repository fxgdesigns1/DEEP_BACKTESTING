#!/usr/bin/env python3
"""
Monitor Economic Data Download Progress
"""

import os
import time
import pandas as pd
from datetime import datetime

def monitor_download_progress():
    """Monitor the progress of economic data downloads"""
    
    print("🔍 ECONOMIC DATA DOWNLOAD MONITOR")
    print("=" * 50)
    
    # Check directories
    directories = [
        'data/economic/fred',
        'data/economic/fmp', 
        'data/economic/polygon',
        'data/economic/marketaux',
        'data/economic/newsdata'
    ]
    
    total_files = 0
    total_size = 0
    
    for directory in directories:
        if os.path.exists(directory):
            files = os.listdir(directory)
            dir_size = sum(os.path.getsize(os.path.join(directory, f)) 
                          for f in files if os.path.isfile(os.path.join(directory, f)))
            
            print(f"📁 {directory}:")
            print(f"   Files: {len(files)}")
            print(f"   Size: {dir_size / 1024 / 1024:.2f} MB")
            
            # Show file details
            for file in files:
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    print(f"   📄 {file}: {size / 1024:.1f} KB ({mod_time.strftime('%H:%M:%S')})")
            
            total_files += len(files)
            total_size += dir_size
            print()
        else:
            print(f"📁 {directory}: Not found")
            print()
    
    print("📊 SUMMARY:")
    print(f"   Total Files: {total_files}")
    print(f"   Total Size: {total_size / 1024 / 1024:.2f} MB")
    print(f"   Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    monitor_download_progress()

