#!/usr/bin/env python3
"""
Data Validation Script for Trading Simulations
This script validates and cleans historical market data before running backtests.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class DataValidator:
    def __init__(self, data_dir="data/historical/prices"):
        self.data_dir = data_dir
        self.validation_results = {}
        self.data_summary = {}
        
    def load_all_data(self):
        """Load all currency pair data from the prices directory"""
        print("Loading data from:", self.data_dir)
        
        data_files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
        all_data = {}
        
        for file in data_files:
            currency_pair = file.replace('_1h.csv', '').upper()
            file_path = os.path.join(self.data_dir, file)
            
            try:
                df = pd.read_csv(file_path)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp').reset_index(drop=True)
                all_data[currency_pair] = df
                print(f"✓ Loaded {currency_pair}: {len(df)} rows")
            except Exception as e:
                print(f"✗ Error loading {currency_pair}: {e}")
                
        return all_data
    
    def validate_ohlc_integrity(self, df, currency_pair):
        """Validate OHLC price relationships"""
        issues = []
        
        # Check for negative prices
        if (df[['open', 'high', 'low', 'close']] <= 0).any().any():
            issues.append("Negative prices detected")
            
        # Check OHLC relationships
        high_low_violations = df[df['high'] < df['low']]
        if len(high_low_violations) > 0:
            issues.append(f"High < Low violations: {len(high_low_violations)}")
            
        open_high_violations = df[df['open'] > df['high']]
        if len(open_high_violations) > 0:
            issues.append(f"Open > High violations: {len(open_high_violations)}")
            
        close_high_violations = df[df['close'] > df['high']]
        if len(close_high_violations) > 0:
            issues.append(f"Close > High violations: {len(close_high_violations)}")
            
        open_low_violations = df[df['open'] < df['low']]
        if len(open_low_violations) > 0:
            issues.append(f"Open < Low violations: {len(open_low_violations)}")
            
        close_low_violations = df[df['close'] < df['low']]
        if len(close_low_violations) > 0:
            issues.append(f"Close < Low violations: {len(close_low_violations)}")
            
        return issues
    
    def validate_time_continuity(self, df, currency_pair):
        """Check for data gaps and time continuity"""
        issues = []
        
        # Calculate expected time range
        start_time = df['timestamp'].min()
        end_time = df['timestamp'].max()
        expected_hours = (end_time - start_time).total_seconds() / 3600
        actual_hours = len(df)
        missing_hours = expected_hours - actual_hours
        
        if missing_hours > 0:
            issues.append(f"Missing {missing_hours:.0f} hours ({missing_hours/expected_hours*100:.1f}%)")
        
        # Check for gaps larger than 1 hour
        df['hour_diff'] = df['timestamp'].diff().dt.total_seconds() / 3600
        gaps = df[df['hour_diff'] > 1.1]
        
        if len(gaps) > 0:
            # Categorize gaps
            weekend_gaps = gaps[gaps['hour_diff'] >= 48]  # Weekend gaps
            other_gaps = gaps[gaps['hour_diff'] < 48]
            
            if len(weekend_gaps) > 0:
                issues.append(f"Weekend gaps: {len(weekend_gaps)} (normal for forex)")
            if len(other_gaps) > 0:
                issues.append(f"Other gaps: {len(other_gaps)} (investigate)")
                
        return issues
    
    def validate_volume_data(self, df, currency_pair):
        """Validate volume data quality"""
        issues = []
        
        zero_volume = len(df[df['volume'] == 0])
        if zero_volume > 0:
            issues.append(f"Zero volume bars: {zero_volume}")
            
        # Check for unrealistic volume patterns
        volume_mean = df['volume'].mean()
        volume_std = df['volume'].std()
        
        # Flag extremely high volumes (potential data errors)
        high_volume_threshold = volume_mean + 3 * volume_std
        extreme_volumes = df[df['volume'] > high_volume_threshold]
        if len(extreme_volumes) > 0:
            issues.append(f"Extreme volumes: {len(extreme_volumes)} bars > {high_volume_threshold:.0f}")
            
        return issues
    
    def validate_price_movements(self, df, currency_pair):
        """Validate price movement patterns"""
        issues = []
        
        # Calculate price changes
        df['price_change'] = df['close'].pct_change()
        df['high_low_range'] = (df['high'] - df['low']) / df['low']
        
        # Check for extreme price movements
        max_change = df['price_change'].abs().max()
        if max_change > 0.05:  # 5% hourly change
            issues.append(f"Extreme hourly change: {max_change*100:.2f}%")
            
        # Check for price spikes (high-low range)
        max_range = df['high_low_range'].max()
        if max_range > 0.1:  # 10% high-low range
            issues.append(f"Extreme high-low range: {max_range*100:.2f}%")
            
        return issues
    
    def generate_data_summary(self, all_data):
        """Generate comprehensive data summary"""
        summary = {}
        
        for currency_pair, df in all_data.items():
            summary[currency_pair] = {
                'total_rows': len(df),
                'date_range': f"{df['timestamp'].min()} to {df['timestamp'].max()}",
                'start_date': df['timestamp'].min(),
                'end_date': df['timestamp'].max(),
                'expected_hours': (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600,
                'missing_hours': ((df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600) - len(df),
                'volume_range': f"{df['volume'].min()} to {df['volume'].max()}",
                'avg_hourly_change': df['close'].pct_change().abs().mean() * 100,
                'max_hourly_change': df['close'].pct_change().abs().max() * 100
            }
            
        return summary
    
    def run_comprehensive_validation(self):
        """Run all validation checks"""
        print("=" * 60)
        print("COMPREHENSIVE DATA VALIDATION")
        print("=" * 60)
        
        # Load data
        all_data = self.load_all_data()
        if not all_data:
            print("No data loaded. Exiting.")
            return
            
        # Generate summary
        self.data_summary = self.generate_data_summary(all_data)
        
        # Run validations for each currency pair
        for currency_pair, df in all_data.items():
            print(f"\n--- Validating {currency_pair} ---")
            
            issues = []
            
            # OHLC integrity
            ohlc_issues = self.validate_ohlc_integrity(df, currency_pair)
            issues.extend(ohlc_issues)
            
            # Time continuity
            time_issues = self.validate_time_continuity(df, currency_pair)
            issues.extend(time_issues)
            
            # Volume validation
            volume_issues = self.validate_volume_data(df, currency_pair)
            issues.extend(volume_issues)
            
            # Price movements
            price_issues = self.validate_price_movements(df, currency_pair)
            issues.extend(price_issues)
            
            # Store results
            self.validation_results[currency_pair] = {
                'issues': issues,
                'issue_count': len(issues),
                'data_quality_score': self.calculate_quality_score(issues, df)
            }
            
            # Display results
            if issues:
                print(f"⚠️  {len(issues)} issues found:")
                for issue in issues:
                    print(f"   • {issue}")
            else:
                print("✅ No issues found")
                
            print(f"Data Quality Score: {self.validation_results[currency_pair]['data_quality_score']:.1f}/10")
        
        # Generate overall report
        self.generate_validation_report()
    
    def calculate_quality_score(self, issues, df):
        """Calculate a data quality score from 0-10"""
        base_score = 10
        
        # Deduct points for different types of issues
        for issue in issues:
            if "violations" in issue.lower():
                base_score -= 2
            elif "gaps" in issue.lower() and "weekend" not in issue.lower():
                base_score -= 1.5
            elif "missing" in issue.lower():
                base_score -= 1
            elif "extreme" in issue.lower():
                base_score -= 0.5
            else:
                base_score -= 0.5
                
        return max(0, base_score)
    
    def generate_validation_report(self):
        """Generate a comprehensive validation report"""
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY REPORT")
        print("=" * 60)
        
        # Overall statistics
        total_issues = sum(result['issue_count'] for result in self.validation_results.values())
        avg_quality_score = np.mean([result['data_quality_score'] for result in self.validation_results.values()])
        
        print(f"Total Currency Pairs: {len(self.validation_results)}")
        print(f"Total Issues Found: {total_issues}")
        print(f"Average Quality Score: {avg_quality_score:.1f}/10")
        
        # Currency pair summary
        print(f"\nCurrency Pair Summary:")
        print(f"{'Pair':<12} {'Rows':<8} {'Issues':<8} {'Score':<8} {'Status':<10}")
        print("-" * 50)
        
        for pair, result in self.validation_results.items():
            rows = self.data_summary[pair]['total_rows']
            issues = result['issue_count']
            score = result['data_quality_score']
            status = "✅ GOOD" if score >= 7 else "⚠️  WARNING" if score >= 5 else "❌ POOR"
            
            print(f"{pair:<12} {rows:<8} {issues:<8} {score:<8.1f} {status:<10}")
        
        # Recommendations
        print(f"\nRECOMMENDATIONS:")
        
        if avg_quality_score >= 8:
            print("✅ Data quality is excellent. Safe to proceed with simulations.")
        elif avg_quality_score >= 6:
            print("⚠️  Data quality is acceptable but has some issues. Review before proceeding.")
        else:
            print("❌ Data quality is poor. Do not proceed without addressing issues.")
        
        # Specific recommendations based on common issues
        common_issues = []
        for result in self.validation_results.values():
            common_issues.extend(result['issues'])
        
        if any("gaps" in issue.lower() for issue in common_issues):
            print("• Implement proper gap handling for weekend and other data gaps")
            
        if any("missing" in issue.lower() for issue in common_issues):
            print("• Investigate missing data periods and consider data supplementation")
            
        if any("violations" in issue.lower() for issue in common_issues):
            print("• Data has OHLC violations - critical issue that must be resolved")
    
    def export_validation_results(self, filename="validation_results.csv"):
        """Export validation results to CSV"""
        results_data = []
        
        for pair, result in self.validation_results.items():
            row = {
                'currency_pair': pair,
                'total_rows': self.data_summary[pair]['total_rows'],
                'start_date': self.data_summary[pair]['start_date'],
                'end_date': self.data_summary[pair]['end_date'],
                'missing_hours': self.data_summary[pair]['missing_hours'],
                'issue_count': result['issue_count'],
                'data_quality_score': result['data_quality_score'],
                'issues': '; '.join(result['issues']) if result['issues'] else 'None'
            }
            results_data.append(row)
            
        df_results = pd.DataFrame(results_data)
        df_results.to_csv(filename, index=False)
        print(f"\nValidation results exported to: {filename}")

def main():
    """Main execution function"""
    print("Data Validation Script for Trading Simulations")
    print("=" * 60)
    
    # Initialize validator
    validator = DataValidator()
    
    # Run validation
    validator.run_comprehensive_validation()
    
    # Export results
    validator.export_validation_results()
    
    print("\nValidation complete! Check the results above and exported CSV file.")

if __name__ == "__main__":
    main()
