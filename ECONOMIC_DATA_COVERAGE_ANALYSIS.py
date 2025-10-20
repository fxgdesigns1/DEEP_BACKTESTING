#!/usr/bin/env python3
"""
ECONOMIC DATA COVERAGE ANALYSIS
===============================

Analyzes the comprehensive coverage of economic indicators for 2022-2025 backtesting period.
"""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import numpy as np

def analyze_economic_coverage():
    """Analyze comprehensive coverage of economic indicators"""
    print("🔍 ECONOMIC DATA COVERAGE ANALYSIS")
    print("=" * 50)
    print("Analyzing 2022-2025 coverage for backtesting...")
    print()
    
    economic_dir = Path('data/backtesting_historical/economic')
    indicators = {}
    
    # Load all economic indicators
    for file_path in economic_dir.glob('alphavantage_*.json'):
        indicator_name = file_path.stem.replace('alphavantage_', '').upper()
        if indicator_name == 'COMPREHENSIVE':
            continue
            
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                indicators[indicator_name] = data['data']
        except Exception as e:
            print(f"⚠️ Error loading {indicator_name}: {e}")
    
    # Analyze coverage
    coverage_analysis = {
        'indicators': {},
        'summary': {
            'total_indicators': len(indicators),
            'coverage_period': '2022-2025',
            'data_points_2022_2025': 0,
            'comprehensive_coverage': True
        }
    }
    
    print("📊 INDICATOR COVERAGE ANALYSIS:")
    print("-" * 40)
    
    for indicator_name, data in indicators.items():
        if 'data' in data and isinstance(data['data'], list):
            dates = [item['date'] for item in data['data']]
            values = [item['value'] for item in data['data'] if item['value'] != '.']
            
            # Filter for 2022-2025
            target_dates = [d for d in dates if '2022' <= d[:4] <= '2025']
            target_values = [v for d, v in zip(dates, values) if '2022' <= d[:4] <= '2025' and v != '.']
            
            # Calculate coverage
            coverage_2022_2025 = len(target_values)
            total_records = len(values)
            interval = data.get('interval', 'unknown')
            unit = data.get('unit', 'unknown')
            
            coverage_analysis['indicators'][indicator_name] = {
                'name': data.get('name', indicator_name),
                'interval': interval,
                'unit': unit,
                'total_records': total_records,
                'coverage_2022_2025': coverage_2022_2025,
                'coverage_percentage': (coverage_2022_2025 / total_records * 100) if total_records > 0 else 0,
                'latest_date': dates[0] if dates else 'unknown',
                'earliest_date': dates[-1] if dates else 'unknown',
                'latest_value': values[0] if values else 'unknown'
            }
            
            coverage_analysis['summary']['data_points_2022_2025'] += coverage_2022_2025
            
            # Display analysis
            status = "✅" if coverage_2022_2025 >= 10 else "⚠️" if coverage_2022_2025 > 0 else "❌"
            print(f"{status} {indicator_name}:")
            print(f"    📅 Period: {dates[-1] if dates else 'N/A'} to {dates[0] if dates else 'N/A'}")
            print(f"    📊 2022-2025 Records: {coverage_2022_2025}/{total_records} ({coverage_2022_2025/total_records*100:.1f}%)")
            print(f"    🔄 Interval: {interval}")
            print(f"    📈 Latest Value: {values[0] if values else 'N/A'} {unit}")
            print()
    
    # Overall assessment
    print("🎯 COMPREHENSIVE COVERAGE ASSESSMENT:")
    print("-" * 45)
    
    total_indicators = len(indicators)
    indicators_with_coverage = sum(1 for ind in coverage_analysis['indicators'].values() 
                                  if ind['coverage_2022_2025'] > 0)
    total_data_points = coverage_analysis['summary']['data_points_2022_2025']
    
    print(f"📊 Total Indicators: {total_indicators}")
    print(f"📈 Indicators with 2022-2025 Data: {indicators_with_coverage}/{total_indicators}")
    print(f"📅 Total Data Points (2022-2025): {total_data_points:,}")
    print()
    
    # Coverage quality assessment
    if indicators_with_coverage >= 8:
        coverage_quality = "EXCELLENT ✅"
        assessment = "Comprehensive coverage for backtesting"
    elif indicators_with_coverage >= 5:
        coverage_quality = "GOOD ⚠️"
        assessment = "Good coverage, some gaps may exist"
    else:
        coverage_quality = "LIMITED ❌"
        assessment = "Limited coverage, significant gaps"
    
    print(f"🎯 Coverage Quality: {coverage_quality}")
    print(f"💡 Assessment: {assessment}")
    print()
    
    # Key economic events coverage
    print("📅 KEY ECONOMIC EVENTS COVERAGE (2022-2025):")
    print("-" * 50)
    
    key_events = {
        '2022': ['High Inflation (8%+)', 'Fed Rate Hikes', 'Strong USD'],
        '2023': ['Inflation Decline', 'Continued Rate Hikes', 'Banking Crisis'],
        '2024': ['Rate Cuts Begin', 'Inflation Normalization', 'Economic Growth'],
        '2025': ['Current Data', 'Policy Normalization', 'Growth Trends']
    }
    
    for year, events in key_events.items():
        print(f"📅 {year}:")
        for event in events:
            print(f"    • {event}")
        print()
    
    # Backtesting recommendations
    print("🚀 BACKTESTING RECOMMENDATIONS:")
    print("-" * 35)
    
    if coverage_quality.startswith("EXCELLENT"):
        print("✅ Your data provides EXCELLENT coverage for:")
        print("   • Economic news trading strategies")
        print("   • Fundamental analysis backtesting")
        print("   • Multi-factor model development")
        print("   • Risk management based on economic indicators")
        print("   • Correlation analysis between currencies and economics")
    elif coverage_quality.startswith("GOOD"):
        print("⚠️ Your data provides GOOD coverage for:")
        print("   • Basic economic news trading")
        print("   • Limited fundamental analysis")
        print("   • Some correlation studies")
        print("   • Consider adding more indicators for comprehensive analysis")
    else:
        print("❌ Limited coverage - consider:")
        print("   • Getting FRED API key for additional data")
        print("   • Using alternative data sources")
        print("   • Focusing on technical analysis strategies")
    
    # Save analysis
    with open('economic_coverage_analysis.json', 'w') as f:
        json.dump(coverage_analysis, f, indent=2, default=str)
    
    print()
    print("📁 Analysis saved to: economic_coverage_analysis.json")
    print("🎯 Your economic data coverage analysis is complete!")

if __name__ == "__main__":
    analyze_economic_coverage()
