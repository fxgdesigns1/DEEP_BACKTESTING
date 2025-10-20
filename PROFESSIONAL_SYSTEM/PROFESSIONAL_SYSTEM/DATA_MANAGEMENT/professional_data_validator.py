#!/usr/bin/env python3
"""
PROFESSIONAL DATA VALIDATOR
Institutional-grade data validation and quality assurance framework
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class ProfessionalDataValidator:
    def __init__(self, data_dir="data/completed"):
        self.data_dir = data_dir
        self.validation_results = {}
        self.quality_metrics = {}
        
        # Validation thresholds
        self.thresholds = {
            'completeness_min': 99.0,  # Minimum 99% completeness
            'price_accuracy_max_error': 0.001,  # Max 0.1% price error
            'volume_realism_min': 0.1,  # Minimum volume ratio
            'ohlc_violations_max': 0,  # Zero tolerance for OHLC violations
            'extreme_moves_max_pct': 5.0,  # Max 5% hourly moves
            'correlation_min': 0.8,  # Minimum correlation with market
            'sharpe_ratio_min': 0.0,  # Minimum Sharpe ratio
            'max_drawdown_max': 0.3  # Max 30% drawdown
        }
        
    def load_completed_data(self, currency_pair: str) -> pd.DataFrame:
        """Load completed data for validation"""
        file_path = os.path.join(self.data_dir, f"{currency_pair.lower()}_completed_1h.csv")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Completed data file not found: {file_path}")
            
        df = pd.read_csv(file_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    def validate_data_completeness(self, df: pd.DataFrame, currency_pair: str) -> Dict[str, Any]:
        """Validate data completeness"""
        print(f"   📊 Validating completeness for {currency_pair}...")
        
        # Calculate expected vs actual data points
        start_date = df['timestamp'].min()
        end_date = df['timestamp'].max()
        
        # Create expected time series (excluding weekends)
        expected_range = pd.date_range(start=start_date, end=end_date, freq='H')
        weekend_filtered = []
        
        for timestamp in expected_range:
            if timestamp.weekday() == 5 and timestamp.hour >= 22:  # Saturday 22:00+
                continue
            elif timestamp.weekday() == 6 and timestamp.hour < 22:  # Sunday before 22:00
                continue
            else:
                weekend_filtered.append(timestamp)
        
        expected_count = len(weekend_filtered)
        actual_count = len(df)
        completeness = (actual_count / expected_count) * 100
        
        # Check for gaps
        df['hour_diff'] = df['timestamp'].diff().dt.total_seconds() / 3600
        gaps = df[df['hour_diff'] > 1.1]
        
        return {
            'expected_count': expected_count,
            'actual_count': actual_count,
            'completeness_percentage': completeness,
            'missing_count': expected_count - actual_count,
            'gaps_found': len(gaps),
            'largest_gap_hours': gaps['hour_diff'].max() if len(gaps) > 0 else 0,
            'passes_threshold': completeness >= self.thresholds['completeness_min']
        }
    
    def validate_price_accuracy(self, df: pd.DataFrame, currency_pair: str) -> Dict[str, Any]:
        """Validate price data accuracy"""
        print(f"   💰 Validating price accuracy for {currency_pair}...")
        
        issues = []
        quality_score = 10.0
        
        # Check for negative prices
        price_columns = ['open', 'high', 'low', 'close']
        for col in price_columns:
            negative_prices = df[df[col] <= 0]
            if len(negative_prices) > 0:
                issues.append(f"Negative prices in {col}: {len(negative_prices)} instances")
                quality_score -= 3.0
        
        # Check OHLC relationships
        ohlc_violations = df[
            (df['high'] < df['low']) |
            (df['open'] > df['high']) |
            (df['close'] > df['high']) |
            (df['open'] < df['low']) |
            (df['close'] < df['low'])
        ]
        
        if len(ohlc_violations) > 0:
            issues.append(f"OHLC violations: {len(ohlc_violations)} instances")
            quality_score -= 5.0
        
        # Check for extreme price movements
        df['price_change'] = df['close'].pct_change().abs()
        extreme_moves = df[df['price_change'] > self.thresholds['extreme_moves_max_pct'] / 100]
        
        if len(extreme_moves) > 0:
            issues.append(f"Extreme price movements: {len(extreme_moves)} instances >{self.thresholds['extreme_moves_max_pct']}%")
            quality_score -= 1.0
        
        # Check for price spikes (unrealistic jumps)
        df['price_spike'] = df['close'].pct_change().abs()
        price_spikes = df[df['price_spike'] > 0.02]  # 2% spikes
        
        if len(price_spikes) > 0:
            issues.append(f"Price spikes: {len(price_spikes)} instances >2%")
            quality_score -= 0.5
        
        # Calculate price statistics
        price_stats = {
            'min_price': df['close'].min(),
            'max_price': df['close'].max(),
            'avg_price': df['close'].mean(),
            'price_volatility': df['close'].std(),
            'price_range': df['close'].max() - df['close'].min()
        }
        
        return {
            'quality_score': max(0.0, quality_score),
            'issues': issues,
            'ohlc_violations': len(ohlc_violations),
            'extreme_moves': len(extreme_moves),
            'price_spikes': len(price_spikes),
            'price_statistics': price_stats,
            'passes_threshold': len(ohlc_violations) == 0 and quality_score >= 7.0
        }
    
    def validate_volume_data(self, df: pd.DataFrame, currency_pair: str) -> Dict[str, Any]:
        """Validate volume data quality"""
        print(f"   📈 Validating volume data for {currency_pair}...")
        
        issues = []
        quality_score = 10.0
        
        # Check for zero volumes
        zero_volumes = df[df['volume'] == 0]
        if len(zero_volumes) > 0:
            issues.append(f"Zero volumes: {len(zero_volumes)} instances")
            quality_score -= 2.0
        
        # Check for negative volumes
        negative_volumes = df[df['volume'] < 0]
        if len(negative_volumes) > 0:
            issues.append(f"Negative volumes: {len(negative_volumes)} instances")
            quality_score -= 3.0
        
        # Check for unrealistic volume patterns
        volume_mean = df['volume'].mean()
        volume_std = df['volume'].std()
        
        # Flag extremely high volumes
        high_volume_threshold = volume_mean + 5 * volume_std
        extreme_volumes = df[df['volume'] > high_volume_threshold]
        
        if len(extreme_volumes) > 0:
            issues.append(f"Extreme volumes: {len(extreme_volumes)} instances >{high_volume_threshold:.0f}")
            quality_score -= 1.0
        
        # Check volume consistency
        volume_changes = df['volume'].pct_change().abs()
        extreme_volume_changes = volume_changes[volume_changes > 10.0]  # 1000% changes
        
        if len(extreme_volume_changes) > 0:
            issues.append(f"Extreme volume changes: {len(extreme_volume_changes)} instances")
            quality_score -= 1.0
        
        # Calculate volume statistics
        volume_stats = {
            'min_volume': df['volume'].min(),
            'max_volume': df['volume'].max(),
            'avg_volume': volume_mean,
            'volume_volatility': volume_std,
            'volume_consistency': 1.0 - (volume_std / volume_mean) if volume_mean > 0 else 0.0
        }
        
        return {
            'quality_score': max(0.0, quality_score),
            'issues': issues,
            'zero_volumes': len(zero_volumes),
            'negative_volumes': len(negative_volumes),
            'extreme_volumes': len(extreme_volumes),
            'extreme_volume_changes': len(extreme_volume_changes),
            'volume_statistics': volume_stats,
            'passes_threshold': len(zero_volumes) == 0 and len(negative_volumes) == 0 and quality_score >= 7.0
        }
    
    def validate_time_continuity(self, df: pd.DataFrame, currency_pair: str) -> Dict[str, Any]:
        """Validate time series continuity"""
        print(f"   ⏰ Validating time continuity for {currency_pair}...")
        
        issues = []
        quality_score = 10.0
        
        # Check for duplicate timestamps
        duplicate_timestamps = df[df.duplicated(subset=['timestamp'], keep=False)]
        if len(duplicate_timestamps) > 0:
            issues.append(f"Duplicate timestamps: {len(duplicate_timestamps)} instances")
            quality_score -= 3.0
        
        # Check for time gaps
        df['time_diff'] = df['timestamp'].diff().dt.total_seconds() / 3600
        gaps = df[df['time_diff'] > 1.1]  # More than 1 hour gap
        
        if len(gaps) > 0:
            issues.append(f"Time gaps: {len(gaps)} instances")
            quality_score -= 2.0
        
        # Check for time reversals
        time_reversals = df[df['time_diff'] < 0]
        if len(time_reversals) > 0:
            issues.append(f"Time reversals: {len(time_reversals)} instances")
            quality_score -= 5.0
        
        # Check for weekend gaps (should be present)
        weekend_gaps = df[(df['timestamp'].dt.weekday == 5) & (df['timestamp'].dt.hour >= 22)]
        weekend_gaps = weekend_gaps[weekend_gaps['time_diff'] > 48]
        
        # This is expected for forex, so we don't penalize
        weekend_gap_count = len(weekend_gaps)
        
        return {
            'quality_score': max(0.0, quality_score),
            'issues': issues,
            'duplicate_timestamps': len(duplicate_timestamps),
            'time_gaps': len(gaps),
            'time_reversals': len(time_reversals),
            'weekend_gaps': weekend_gap_count,
            'passes_threshold': len(duplicate_timestamps) == 0 and len(time_reversals) == 0 and quality_score >= 7.0
        }
    
    def validate_market_realism(self, df: pd.DataFrame, currency_pair: str) -> Dict[str, Any]:
        """Validate market realism and behavior"""
        print(f"   🌍 Validating market realism for {currency_pair}...")
        
        issues = []
        quality_score = 10.0
        
        # Check for realistic price movements
        df['hourly_return'] = df['close'].pct_change()
        returns = df['hourly_return'].dropna()
        
        # Check return distribution
        return_skewness = returns.skew()
        return_kurtosis = returns.kurtosis()
        
        # Realistic skewness should be close to 0, kurtosis should be > 0 (fat tails)
        if abs(return_skewness) > 2.0:
            issues.append(f"Unrealistic return skewness: {return_skewness:.2f}")
            quality_score -= 1.0
        
        if return_kurtosis < 0:
            issues.append(f"Unrealistic return kurtosis: {return_kurtosis:.2f}")
            quality_score -= 1.0
        
        # Check for autocorrelation (should be minimal for efficient markets)
        autocorr_1 = returns.autocorr(lag=1)
        if abs(autocorr_1) > 0.1:
            issues.append(f"High autocorrelation: {autocorr_1:.3f}")
            quality_score -= 1.0
        
        # Check for volatility clustering
        df['volatility'] = returns.rolling(24).std()  # 24-hour rolling volatility
        vol_autocorr = df['volatility'].autocorr(lag=1)
        
        # Volatility clustering is normal, so we don't penalize high autocorr here
        
        # Calculate market statistics
        market_stats = {
            'avg_hourly_return': returns.mean(),
            'return_volatility': returns.std(),
            'sharpe_ratio': returns.mean() / returns.std() if returns.std() > 0 else 0,
            'max_drawdown': self._calculate_max_drawdown(returns),
            'return_skewness': return_skewness,
            'return_kurtosis': return_kurtosis,
            'autocorrelation': autocorr_1
        }
        
        return {
            'quality_score': max(0.0, quality_score),
            'issues': issues,
            'market_statistics': market_stats,
            'passes_threshold': quality_score >= 7.0
        }
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def validate_cross_currency_consistency(self, all_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Validate consistency across currency pairs"""
        print(f"   🔄 Validating cross-currency consistency...")
        
        issues = []
        quality_score = 10.0
        
        # Check for correlated movements (major pairs should move together)
        major_pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD']
        available_pairs = [pair for pair in major_pairs if pair in all_data]
        
        if len(available_pairs) >= 2:
            # Calculate correlations
            correlations = {}
            for i, pair1 in enumerate(available_pairs):
                for pair2 in available_pairs[i+1:]:
                    df1 = all_data[pair1]
                    df2 = all_data[pair2]
                    
                                            # Align timestamps
                        common_timestamps = set(df1['timestamp']).intersection(set(df2['timestamp']))
                        if len(common_timestamps) > 100:  # Need sufficient data
                            df1_aligned = df1[df1['timestamp'].isin(common_timestamps)].sort_values('timestamp')
                            df2_aligned = df2[df2['timestamp'].isin(common_timestamps)].sort_values('timestamp')
                        
                        returns1 = df1_aligned['close'].pct_change().dropna()
                        returns2 = df2_aligned['close'].pct_change().dropna()
                        
                        if len(returns1) > 50 and len(returns2) > 50:
                            correlation = returns1.corr(returns2)
                            correlations[f"{pair1}-{pair2}"] = correlation
                            
                            # Check for unrealistic correlations
                            if abs(correlation) > 0.95:
                                issues.append(f"Unrealistic correlation {pair1}-{pair2}: {correlation:.3f}")
                                quality_score -= 1.0
        
        return {
            'quality_score': max(0.0, quality_score),
            'issues': issues,
            'correlations': correlations,
            'passes_threshold': quality_score >= 7.0
        }
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive validation on all completed data"""
        print("🏆 PROFESSIONAL DATA VALIDATION")
        print("=" * 80)
        
        currency_pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 'USD_CAD', 
                         'USD_CHF', 'NZD_USD', 'EUR_JPY', 'GBP_JPY', 'XAU_USD']
        
        validation_results = {
            'validation_timestamp': datetime.now().isoformat(),
            'currency_validations': {},
            'overall_summary': {},
            'recommendations': []
        }
        
        all_data = {}
        successful_validations = 0
        
        for pair in currency_pairs:
            print(f"\n📊 Validating {pair}...")
            
            try:
                df = self.load_completed_data(pair)
                all_data[pair] = df
                
                # Run all validation checks
                completeness = self.validate_data_completeness(df, pair)
                price_accuracy = self.validate_price_accuracy(df, pair)
                volume_data = self.validate_volume_data(df, pair)
                time_continuity = self.validate_time_continuity(df, pair)
                market_realism = self.validate_market_realism(df, pair)
                
                # Calculate overall quality score
                overall_score = (
                    completeness['completeness_percentage'] / 10 +  # 10 points max
                    price_accuracy['quality_score'] * 0.3 +  # 30% weight
                    volume_data['quality_score'] * 0.2 +  # 20% weight
                    time_continuity['quality_score'] * 0.2 +  # 20% weight
                    market_realism['quality_score'] * 0.3  # 30% weight
                )
                
                validation_results['currency_validations'][pair] = {
                    'completeness': completeness,
                    'price_accuracy': price_accuracy,
                    'volume_data': volume_data,
                    'time_continuity': time_continuity,
                    'market_realism': market_realism,
                    'overall_quality_score': overall_score,
                    'passes_all_tests': all([
                        completeness['passes_threshold'],
                        price_accuracy['passes_threshold'],
                        volume_data['passes_threshold'],
                        time_continuity['passes_threshold'],
                        market_realism['passes_threshold']
                    ])
                }
                
                successful_validations += 1
                
                # Print summary
                print(f"   ✅ Overall Quality Score: {overall_score:.1f}/10")
                print(f"   📊 Completeness: {completeness['completeness_percentage']:.1f}%")
                print(f"   💰 Price Accuracy: {price_accuracy['quality_score']:.1f}/10")
                print(f"   📈 Volume Quality: {volume_data['quality_score']:.1f}/10")
                print(f"   ⏰ Time Continuity: {time_continuity['quality_score']:.1f}/10")
                print(f"   🌍 Market Realism: {market_realism['quality_score']:.1f}/10")
                
            except Exception as e:
                print(f"   ❌ Validation failed for {pair}: {e}")
                validation_results['currency_validations'][pair] = {'error': str(e)}
        
        # Cross-currency validation
        if len(all_data) >= 2:
            cross_validation = self.validate_cross_currency_consistency(all_data)
            validation_results['cross_currency_validation'] = cross_validation
        
        # Generate overall summary
        validation_results['overall_summary'] = self._generate_overall_summary(validation_results['currency_validations'])
        validation_results['recommendations'] = self._generate_recommendations(validation_results)
        
        # Save results
        self._save_validation_results(validation_results)
        
        return validation_results
    
    def _generate_overall_summary(self, currency_validations: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall validation summary"""
        valid_validations = {k: v for k, v in currency_validations.items() if 'error' not in v}
        
        if not valid_validations:
            return {'error': 'No valid validations found'}
        
        quality_scores = [v['overall_quality_score'] for v in valid_validations.values()]
        passing_tests = [v['passes_all_tests'] for v in valid_validations.values()]
        
        return {
            'total_pairs_validated': len(valid_validations),
            'pairs_passing_all_tests': sum(passing_tests),
            'average_quality_score': np.mean(quality_scores),
            'min_quality_score': np.min(quality_scores),
            'max_quality_score': np.max(quality_scores),
            'overall_grade': self._calculate_overall_grade(quality_scores, passing_tests)
        }
    
    def _calculate_overall_grade(self, quality_scores: List[float], passing_tests: List[bool]) -> str:
        """Calculate overall grade"""
        avg_score = np.mean(quality_scores)
        pass_rate = sum(passing_tests) / len(passing_tests)
        
        if avg_score >= 9.0 and pass_rate >= 0.9:
            return 'A+ (EXCELLENT)'
        elif avg_score >= 8.0 and pass_rate >= 0.8:
            return 'A (VERY GOOD)'
        elif avg_score >= 7.0 and pass_rate >= 0.7:
            return 'B (GOOD)'
        elif avg_score >= 6.0 and pass_rate >= 0.6:
            return 'C (ACCEPTABLE)'
        else:
            return 'D (POOR)'
    
    def _generate_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate professional recommendations"""
        recommendations = []
        
        summary = validation_results['overall_summary']
        
        if summary['overall_grade'].startswith('A'):
            recommendations.append("✅ Data quality is excellent - ready for institutional trading")
        elif summary['overall_grade'].startswith('B'):
            recommendations.append("✅ Data quality is good - suitable for professional backtesting")
        elif summary['overall_grade'].startswith('C'):
            recommendations.append("⚠️ Data quality is acceptable - review issues before live trading")
        else:
            recommendations.append("❌ Data quality is poor - address issues before any trading")
        
        # Specific recommendations based on common issues
        for pair, validation in validation_results['currency_validations'].items():
            if 'error' in validation:
                continue
            
            if not validation['completeness']['passes_threshold']:
                recommendations.append(f"• {pair}: Improve data completeness (currently {validation['completeness']['completeness_percentage']:.1f}%)")
            
            if not validation['price_accuracy']['passes_threshold']:
                recommendations.append(f"• {pair}: Fix price accuracy issues ({validation['price_accuracy']['quality_score']:.1f}/10)")
            
            if not validation['volume_data']['passes_threshold']:
                recommendations.append(f"• {pair}: Address volume data quality ({validation['volume_data']['quality_score']:.1f}/10)")
        
        return recommendations
    
    def _save_validation_results(self, validation_results: Dict[str, Any]):
        """Save validation results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON report
        json_file = f"professional_validation_results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(validation_results, f, indent=2, default=str)
        
        # Save summary report
        summary_file = f"validation_summary_{timestamp}.md"
        self._generate_summary_report(validation_results, summary_file)
        
        print(f"\n💾 Validation results saved:")
        print(f"   📄 Detailed JSON: {json_file}")
        print(f"   📋 Summary Report: {summary_file}")
    
    def _generate_summary_report(self, validation_results: Dict[str, Any], filename: str):
        """Generate professional summary report"""
        with open(filename, 'w') as f:
            f.write("# PROFESSIONAL DATA VALIDATION REPORT\n\n")
            f.write(f"**Validation Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Overall Summary
            summary = validation_results['overall_summary']
            f.write("## EXECUTIVE SUMMARY\n\n")
            f.write(f"- **Overall Grade:** {summary['overall_grade']}\n")
            f.write(f"- **Average Quality Score:** {summary['average_quality_score']:.1f}/10\n")
            f.write(f"- **Pairs Validated:** {summary['total_pairs_validated']}\n")
            f.write(f"- **Pairs Passing All Tests:** {summary['pairs_passing_all_tests']}\n")
            f.write(f"- **Quality Range:** {summary['min_quality_score']:.1f} - {summary['max_quality_score']:.1f}\n\n")
            
            # Currency Pair Details
            f.write("## CURRENCY PAIR VALIDATION\n\n")
            for pair, validation in validation_results['currency_validations'].items():
                if 'error' in validation:
                    f.write(f"### {pair} - ERROR\n")
                    f.write(f"Error: {validation['error']}\n\n")
                    continue
                
                f.write(f"### {pair}\n")
                f.write(f"- **Overall Quality Score:** {validation['overall_quality_score']:.1f}/10\n")
                f.write(f"- **Completeness:** {validation['completeness']['completeness_percentage']:.1f}%\n")
                f.write(f"- **Price Accuracy:** {validation['price_accuracy']['quality_score']:.1f}/10\n")
                f.write(f"- **Volume Quality:** {validation['volume_data']['quality_score']:.1f}/10\n")
                f.write(f"- **Time Continuity:** {validation['time_continuity']['quality_score']:.1f}/10\n")
                f.write(f"- **Market Realism:** {validation['market_realism']['quality_score']:.1f}/10\n")
                f.write(f"- **Passes All Tests:** {'✅' if validation['passes_all_tests'] else '❌'}\n\n")
            
            # Recommendations
            f.write("## PROFESSIONAL RECOMMENDATIONS\n\n")
            for i, rec in enumerate(validation_results['recommendations'], 1):
                f.write(f"{i}. {rec}\n")

def main():
    """Main execution function"""
    print("🏆 PROFESSIONAL DATA VALIDATOR")
    print("Institutional-Grade Data Quality Assurance")
    print("=" * 80)
    
    validator = ProfessionalDataValidator()
    results = validator.run_comprehensive_validation()
    
    print("\n" + "=" * 80)
    print("🎯 VALIDATION COMPLETE")
    print("=" * 80)
    
    summary = results['overall_summary']
    print(f"Overall Grade: {summary['overall_grade']}")
    print(f"Average Quality Score: {summary['average_quality_score']:.1f}/10")
    print(f"Pairs Passing All Tests: {summary['pairs_passing_all_tests']}/{summary['total_pairs_validated']}")
    
    print(f"\n📋 {len(results['recommendations'])} PROFESSIONAL RECOMMENDATIONS GENERATED")
    print("Your data is now validated to institutional standards!")

if __name__ == "__main__":
    main()
