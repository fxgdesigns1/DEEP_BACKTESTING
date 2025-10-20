#!/usr/bin/env python3
"""
PROFESSIONAL DATA GAP ANALYZER
World-class data analysis for forex trading - identifies and categorizes all data gaps
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import warnings
warnings.filterwarnings('ignore')

class ProfessionalDataGapAnalyzer:
    def __init__(self, data_dir="data/historical/prices"):
        self.data_dir = data_dir
        self.gap_analysis = {}
        self.missing_periods = {}
        self.data_quality_metrics = {}
        
    def load_currency_data(self, currency_pair: str) -> pd.DataFrame:
        """Load data for a specific currency pair"""
        file_path = os.path.join(self.data_dir, f"{currency_pair.lower()}_1h.csv")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file not found: {file_path}")
            
        df = pd.read_csv(file_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    def create_complete_time_series(self, start_date: datetime, end_date: datetime) -> pd.DatetimeIndex:
        """Create complete hourly time series for the period"""
        # Create hourly range excluding weekends (Saturday 22:00 to Sunday 22:00 UTC)
        complete_range = pd.date_range(start=start_date, end=end_date, freq='H')
        
        # Filter out weekend gaps (Saturday 22:00 to Sunday 22:00)
        filtered_range = []
        for timestamp in complete_range:
            # Skip Saturday 22:00 to Sunday 22:00 (weekend gap)
            if timestamp.weekday() == 5 and timestamp.hour >= 22:  # Saturday 22:00+
                continue
            elif timestamp.weekday() == 6 and timestamp.hour < 22:  # Sunday before 22:00
                continue
            else:
                filtered_range.append(timestamp)
        
        return pd.DatetimeIndex(filtered_range)
    
    def analyze_gaps_detailed(self, df: pd.DataFrame, currency_pair: str) -> Dict[str, Any]:
        """Perform detailed gap analysis for a currency pair"""
        print(f"🔍 Analyzing gaps for {currency_pair}...")
        
        # Get data range
        start_date = df['timestamp'].min()
        end_date = df['timestamp'].max()
        
        # Create complete expected time series
        expected_timestamps = self.create_complete_time_series(start_date, end_date)
        actual_timestamps = pd.DatetimeIndex(df['timestamp'])
        
        # Find missing timestamps
        missing_timestamps = expected_timestamps.difference(actual_timestamps)
        
        # Categorize gaps
        gap_analysis = {
            'currency_pair': currency_pair,
            'data_period': {
                'start': start_date,
                'end': end_date,
                'total_expected_hours': len(expected_timestamps),
                'actual_hours': len(actual_timestamps),
                'missing_hours': len(missing_timestamps),
                'completeness_percentage': (len(actual_timestamps) / len(expected_timestamps)) * 100
            },
            'gap_categories': self._categorize_gaps(missing_timestamps),
            'critical_gaps': self._identify_critical_gaps(missing_timestamps),
            'data_quality_issues': self._identify_data_quality_issues(df)
        }
        
        return gap_analysis
    
    def _categorize_gaps(self, missing_timestamps: pd.DatetimeIndex) -> Dict[str, Any]:
        """Categorize gaps by type and duration"""
        if len(missing_timestamps) == 0:
            return {'no_gaps': True}
        
        gaps = []
        current_gap_start = None
        current_gap_end = None
        
        for timestamp in missing_timestamps:
            if current_gap_start is None:
                current_gap_start = timestamp
                current_gap_end = timestamp
            elif (timestamp - current_gap_end).total_seconds() <= 3600:  # Within 1 hour
                current_gap_end = timestamp
            else:
                # Gap ended, record it
                gap_duration = (current_gap_end - current_gap_start).total_seconds() / 3600
                gaps.append({
                    'start': current_gap_start,
                    'end': current_gap_end,
                    'duration_hours': gap_duration,
                    'type': self._classify_gap_type(current_gap_start, current_gap_end)
                })
                current_gap_start = timestamp
                current_gap_end = timestamp
        
        # Don't forget the last gap
        if current_gap_start is not None:
            gap_duration = (current_gap_end - current_gap_start).total_seconds() / 3600
            gaps.append({
                'start': current_gap_start,
                'end': current_gap_end,
                'duration_hours': gap_duration,
                'type': self._classify_gap_type(current_gap_start, current_gap_end)
            })
        
        # Categorize by type
        weekend_gaps = [g for g in gaps if g['type'] == 'weekend']
        holiday_gaps = [g for g in gaps if g['type'] == 'holiday']
        data_errors = [g for g in gaps if g['type'] == 'data_error']
        unknown_gaps = [g for g in gaps if g['type'] == 'unknown']
        
        return {
            'total_gaps': len(gaps),
            'weekend_gaps': {
                'count': len(weekend_gaps),
                'total_hours': sum(g['duration_hours'] for g in weekend_gaps),
                'gaps': weekend_gaps
            },
            'holiday_gaps': {
                'count': len(holiday_gaps),
                'total_hours': sum(g['duration_hours'] for g in holiday_gaps),
                'gaps': holiday_gaps
            },
            'data_error_gaps': {
                'count': len(data_errors),
                'total_hours': sum(g['duration_hours'] for g in data_errors),
                'gaps': data_errors
            },
            'unknown_gaps': {
                'count': len(unknown_gaps),
                'total_hours': sum(g['duration_hours'] for g in unknown_gaps),
                'gaps': unknown_gaps
            }
        }
    
    def _classify_gap_type(self, start: datetime, end: datetime) -> str:
        """Classify gap type based on timing and duration"""
        duration_hours = (end - start).total_seconds() / 3600
        
        # Weekend gaps (typically 49 hours: Friday 22:00 to Sunday 22:00)
        if 48 <= duration_hours <= 50:
            return 'weekend'
        
        # Holiday gaps (longer than weekend, typically 72+ hours)
        elif duration_hours > 72:
            return 'holiday'
        
        # Short gaps (likely data errors)
        elif duration_hours <= 24:
            return 'data_error'
        
        # Unknown gaps
        else:
            return 'unknown'
    
    def _identify_critical_gaps(self, missing_timestamps: pd.DatetimeIndex) -> List[Dict[str, Any]]:
        """Identify critical gaps that could impact trading strategies"""
        critical_gaps = []
        
        # Group consecutive missing timestamps
        gaps = []
        current_gap = []
        
        for timestamp in missing_timestamps:
            if not current_gap:
                current_gap = [timestamp]
            elif (timestamp - current_gap[-1]).total_seconds() <= 3600:
                current_gap.append(timestamp)
            else:
                if len(current_gap) > 1:  # Only consider gaps with multiple missing hours
                    gaps.append(current_gap)
                current_gap = [timestamp]
        
        if len(current_gap) > 1:
            gaps.append(current_gap)
        
        # Identify critical gaps
        for gap in gaps:
            gap_start = gap[0]
            gap_end = gap[-1]
            duration_hours = len(gap)
            
            # Critical if:
            # 1. More than 24 hours (excluding weekends)
            # 2. During major trading sessions
            # 3. Around major economic events
            
            is_critical = False
            reasons = []
            
            if duration_hours > 24 and gap_start.weekday() not in [5, 6]:  # Not weekend
                is_critical = True
                reasons.append(f"Long gap during trading days ({duration_hours}h)")
            
            # Check if gap is during major sessions (London/NY overlap)
            if self._is_during_major_session(gap_start, gap_end):
                is_critical = True
                reasons.append("Gap during major trading session")
            
            if is_critical:
                critical_gaps.append({
                    'start': gap_start,
                    'end': gap_end,
                    'duration_hours': duration_hours,
                    'reasons': reasons,
                    'impact_level': 'HIGH' if duration_hours > 48 else 'MEDIUM'
                })
        
        return critical_gaps
    
    def _is_during_major_session(self, start: datetime, end: datetime) -> bool:
        """Check if gap occurs during major trading sessions"""
        # London session: 8:00-17:00 UTC
        # NY session: 13:00-22:00 UTC
        # Overlap: 13:00-17:00 UTC
        
        for timestamp in [start, end]:
            if 13 <= timestamp.hour <= 17:  # Major session overlap
                return True
        return False
    
    def _identify_data_quality_issues(self, df: pd.DataFrame) -> List[str]:
        """Identify data quality issues"""
        issues = []
        
        # Check for price anomalies
        price_changes = df['close'].pct_change().abs()
        extreme_moves = price_changes[price_changes > 0.05]  # 5% moves
        if len(extreme_moves) > 0:
            issues.append(f"Extreme price movements: {len(extreme_moves)} instances >5%")
        
        # Check for volume anomalies
        volume_mean = df['volume'].mean()
        volume_std = df['volume'].std()
        extreme_volumes = df[df['volume'] > volume_mean + 3 * volume_std]
        if len(extreme_volumes) > 0:
            issues.append(f"Extreme volume spikes: {len(extreme_volumes)} instances")
        
        # Check for OHLC violations
        ohlc_violations = df[(df['high'] < df['low']) | 
                           (df['open'] > df['high']) | 
                           (df['close'] > df['high']) |
                           (df['open'] < df['low']) | 
                           (df['close'] < df['low'])]
        if len(ohlc_violations) > 0:
            issues.append(f"OHLC violations: {len(ohlc_violations)} instances")
        
        return issues
    
    def run_comprehensive_gap_analysis(self) -> Dict[str, Any]:
        """Run comprehensive gap analysis for all currency pairs"""
        print("🚀 PROFESSIONAL DATA GAP ANALYSIS")
        print("=" * 80)
        
        currency_pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 'USD_CAD', 
                         'USD_CHF', 'NZD_USD', 'EUR_JPY', 'GBP_JPY', 'XAU_USD']
        
        overall_analysis = {
            'analysis_timestamp': datetime.now().isoformat(),
            'total_pairs_analyzed': len(currency_pairs),
            'currency_analyses': {},
            'overall_summary': {},
            'critical_issues': [],
            'recommendations': []
        }
        
        for pair in currency_pairs:
            try:
                print(f"\n📊 Analyzing {pair}...")
                df = self.load_currency_data(pair)
                gap_analysis = self.analyze_gaps_detailed(df, pair)
                overall_analysis['currency_analyses'][pair] = gap_analysis
                
                # Print summary
                completeness = gap_analysis['data_period']['completeness_percentage']
                missing_hours = gap_analysis['data_period']['missing_hours']
                critical_gaps = len(gap_analysis['critical_gaps'])
                
                print(f"   Completeness: {completeness:.1f}%")
                print(f"   Missing Hours: {missing_hours:,}")
                print(f"   Critical Gaps: {critical_gaps}")
                
            except Exception as e:
                print(f"   ❌ Error analyzing {pair}: {e}")
                overall_analysis['currency_analyses'][pair] = {'error': str(e)}
        
        # Generate overall summary
        overall_analysis['overall_summary'] = self._generate_overall_summary(overall_analysis['currency_analyses'])
        overall_analysis['critical_issues'] = self._identify_critical_issues(overall_analysis['currency_analyses'])
        overall_analysis['recommendations'] = self._generate_recommendations(overall_analysis)
        
        # Save detailed analysis
        self._save_analysis_results(overall_analysis)
        
        return overall_analysis
    
    def _generate_overall_summary(self, currency_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall summary statistics"""
        valid_analyses = {k: v for k, v in currency_analyses.items() if 'error' not in v}
        
        if not valid_analyses:
            return {'error': 'No valid analyses found'}
        
        completeness_scores = [v['data_period']['completeness_percentage'] for v in valid_analyses.values()]
        missing_hours = [v['data_period']['missing_hours'] for v in valid_analyses.values()]
        critical_gaps = [len(v['critical_gaps']) for v in valid_analyses.values()]
        
        return {
            'average_completeness': np.mean(completeness_scores),
            'min_completeness': np.min(completeness_scores),
            'max_completeness': np.max(completeness_scores),
            'total_missing_hours': sum(missing_hours),
            'average_missing_hours': np.mean(missing_hours),
            'total_critical_gaps': sum(critical_gaps),
            'pairs_with_critical_gaps': len([c for c in critical_gaps if c > 0]),
            'data_quality_rating': self._calculate_overall_quality_rating(completeness_scores, critical_gaps)
        }
    
    def _calculate_overall_quality_rating(self, completeness_scores: List[float], critical_gaps: List[int]) -> str:
        """Calculate overall data quality rating"""
        avg_completeness = np.mean(completeness_scores)
        total_critical_gaps = sum(critical_gaps)
        
        if avg_completeness >= 95 and total_critical_gaps == 0:
            return 'EXCELLENT'
        elif avg_completeness >= 90 and total_critical_gaps <= 2:
            return 'GOOD'
        elif avg_completeness >= 80 and total_critical_gaps <= 5:
            return 'FAIR'
        else:
            return 'POOR'
    
    def _identify_critical_issues(self, currency_analyses: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify critical issues across all currency pairs"""
        critical_issues = []
        
        for pair, analysis in currency_analyses.items():
            if 'error' in analysis:
                continue
            
            # Check for low completeness
            if analysis['data_period']['completeness_percentage'] < 80:
                critical_issues.append({
                    'type': 'LOW_COMPLETENESS',
                    'pair': pair,
                    'severity': 'HIGH',
                    'description': f"Only {analysis['data_period']['completeness_percentage']:.1f}% data completeness",
                    'impact': 'Significant impact on backtesting reliability'
                })
            
            # Check for critical gaps
            for gap in analysis['critical_gaps']:
                critical_issues.append({
                    'type': 'CRITICAL_GAP',
                    'pair': pair,
                    'severity': gap['impact_level'],
                    'description': f"Critical gap: {gap['duration_hours']:.0f}h from {gap['start']} to {gap['end']}",
                    'reasons': gap['reasons'],
                    'impact': 'Potential strategy failure during gap periods'
                })
        
        return critical_issues
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate professional recommendations"""
        recommendations = []
        
        summary = analysis['overall_summary']
        critical_issues = analysis['critical_issues']
        
        # Data completeness recommendations
        if summary['average_completeness'] < 90:
            recommendations.append("URGENT: Implement comprehensive data gap filling strategy")
            recommendations.append("Consider multiple data sources for missing periods")
        
        # Critical gap recommendations
        if summary['total_critical_gaps'] > 0:
            recommendations.append("CRITICAL: Address all critical gaps before live trading")
            recommendations.append("Implement gap detection and handling in trading strategies")
        
        # Data quality recommendations
        if summary['data_quality_rating'] in ['FAIR', 'POOR']:
            recommendations.append("Implement real-time data quality monitoring")
            recommendations.append("Establish data validation protocols")
        
        # Professional trading recommendations
        recommendations.extend([
            "Use only verified, institutional-grade data sources",
            "Implement redundant data feeds for critical pairs",
            "Establish data backup and recovery procedures",
            "Create data quality dashboards for monitoring",
            "Regular data audits and validation checks"
        ])
        
        return recommendations
    
    def _save_analysis_results(self, analysis: Dict[str, Any]):
        """Save detailed analysis results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON report
        json_file = f"professional_gap_analysis_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        # Save summary report
        summary_file = f"gap_analysis_summary_{timestamp}.md"
        self._generate_summary_report(analysis, summary_file)
        
        print(f"\n💾 Analysis results saved:")
        print(f"   📄 Detailed JSON: {json_file}")
        print(f"   📋 Summary Report: {summary_file}")
    
    def _generate_summary_report(self, analysis: Dict[str, Any], filename: str):
        """Generate professional summary report"""
        with open(filename, 'w') as f:
            f.write("# PROFESSIONAL DATA GAP ANALYSIS REPORT\n\n")
            f.write(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Overall Summary
            summary = analysis['overall_summary']
            f.write("## EXECUTIVE SUMMARY\n\n")
            f.write(f"- **Data Quality Rating:** {summary['data_quality_rating']}\n")
            f.write(f"- **Average Completeness:** {summary['average_completeness']:.1f}%\n")
            f.write(f"- **Total Missing Hours:** {summary['total_missing_hours']:,}\n")
            f.write(f"- **Critical Gaps:** {summary['total_critical_gaps']}\n")
            f.write(f"- **Pairs with Issues:** {summary['pairs_with_critical_gaps']}/{analysis['total_pairs_analyzed']}\n\n")
            
            # Critical Issues
            if analysis['critical_issues']:
                f.write("## CRITICAL ISSUES\n\n")
                for issue in analysis['critical_issues']:
                    f.write(f"### {issue['type']} - {issue['pair']}\n")
                    f.write(f"- **Severity:** {issue['severity']}\n")
                    f.write(f"- **Description:** {issue['description']}\n")
                    f.write(f"- **Impact:** {issue['impact']}\n\n")
            
            # Recommendations
            f.write("## PROFESSIONAL RECOMMENDATIONS\n\n")
            for i, rec in enumerate(analysis['recommendations'], 1):
                f.write(f"{i}. {rec}\n")
            
            f.write("\n## CURRENCY PAIR DETAILS\n\n")
            for pair, pair_analysis in analysis['currency_analyses'].items():
                if 'error' in pair_analysis:
                    f.write(f"### {pair} - ERROR\n")
                    f.write(f"Error: {pair_analysis['error']}\n\n")
                    continue
                
                f.write(f"### {pair}\n")
                data_period = pair_analysis['data_period']
                f.write(f"- **Completeness:** {data_period['completeness_percentage']:.1f}%\n")
                f.write(f"- **Missing Hours:** {data_period['missing_hours']:,}\n")
                f.write(f"- **Critical Gaps:** {len(pair_analysis['critical_gaps'])}\n")
                
                if pair_analysis['data_quality_issues']:
                    f.write("- **Quality Issues:**\n")
                    for issue in pair_analysis['data_quality_issues']:
                        f.write(f"  - {issue}\n")
                f.write("\n")

def main():
    """Main execution function"""
    print("🏆 PROFESSIONAL DATA GAP ANALYZER")
    print("World-Class Forex Data Analysis")
    print("=" * 80)
    
    analyzer = ProfessionalDataGapAnalyzer()
    results = analyzer.run_comprehensive_gap_analysis()
    
    print("\n" + "=" * 80)
    print("🎯 ANALYSIS COMPLETE")
    print("=" * 80)
    
    summary = results['overall_summary']
    print(f"Data Quality Rating: {summary['data_quality_rating']}")
    print(f"Average Completeness: {summary['average_completeness']:.1f}%")
    print(f"Total Missing Hours: {summary['total_missing_hours']:,}")
    print(f"Critical Gaps: {summary['total_critical_gaps']}")
    
    if results['critical_issues']:
        print(f"\n⚠️  {len(results['critical_issues'])} CRITICAL ISSUES FOUND")
        for issue in results['critical_issues'][:3]:  # Show top 3
            print(f"   • {issue['pair']}: {issue['description']}")
    
    print(f"\n📋 {len(results['recommendations'])} PROFESSIONAL RECOMMENDATIONS GENERATED")
    print("Check the generated reports for detailed analysis and action plan.")

if __name__ == "__main__":
    main()
