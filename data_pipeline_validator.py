#!/usr/bin/env python3
"""
DATA PIPELINE VALIDATOR
Ensures data readiness for ultimate strategy search
"""

import os
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from professional_data_gap_analyzer import ProfessionalDataGapAnalyzer
from professional_data_gap_filler import ProfessionalDataGapFiller

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataPipelineValidator:
    """
    Validates and prepares data pipeline for strategy search
    """
    
    def __init__(self, config_path: str = "experiments.yaml"):
        """Initialize the validator"""
        self.logger = logger
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.gap_analyzer = ProfessionalDataGapAnalyzer()
        self.gap_filler = ProfessionalDataGapFiller()
        
        # Data directories
        self.data_dirs = {
            'historical': 'data/historical/prices',
            'completed': 'data/completed',
            'timeframes': 'data/timeframes',
            'enhanced': 'data/enhanced'
        }
        
        # Currency pairs
        self.currency_pairs = [
            'EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 'USD_CAD',
            'USD_CHF', 'NZD_USD', 'EUR_JPY', 'GBP_JPY', 'XAU_USD'
        ]
        
        # Timeframes
        self.timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']
        
        self.logger.info("📊 Data Pipeline Validator initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration"""
        try:
            import yaml
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return {}
    
    def validate_data_structure(self) -> bool:
        """Validate data directory structure"""
        self.logger.info("🔍 Validating data directory structure...")
        
        missing_dirs = []
        for name, path in self.data_dirs.items():
            if not os.path.exists(path):
                missing_dirs.append((name, path))
                self.logger.warning(f"⚠️  Missing directory: {name} -> {path}")
        
        if missing_dirs:
            self.logger.error("❌ Missing required data directories")
            for name, path in missing_dirs:
                self.logger.error(f"   {name}: {path}")
            return False
        
        self.logger.info("✅ Data directory structure validated")
        return True
    
    def validate_currency_pair_data(self) -> Dict[str, Any]:
        """Validate data for all currency pairs"""
        self.logger.info("📈 Validating currency pair data...")
        
        validation_results = {}
        
        for pair in self.currency_pairs:
            self.logger.info(f"   Checking {pair}...")
            
            pair_results = {
                'pair': pair,
                'files_found': [],
                'files_missing': [],
                'data_quality': {},
                'issues': []
            }
            
            # Check for 1h data (required for professional backtesting)
            file_path = os.path.join(self.data_dirs['completed'], f"{pair.lower()}_completed_1h.csv")
            if os.path.exists(file_path):
                pair_results['files_found'].append('1h_completed')
                
                # Validate data quality
                try:
                    df = pd.read_csv(file_path)
                    if len(df) < 1000:
                        pair_results['issues'].append(f"Insufficient 1h data: {len(df)} rows")
                    else:
                        pair_results['data_quality']['1h_rows'] = len(df)
                        pair_results['data_quality']['1h_date_range'] = {
                            'start': df['timestamp'].min(),
                            'end': df['timestamp'].max()
                        }
                except Exception as e:
                    pair_results['issues'].append(f"Error reading 1h data: {e}")
            else:
                pair_results['files_missing'].append('1h_completed')
            
            # Check for historical data
            hist_file = os.path.join(self.data_dirs['historical'], f"{pair.lower()}_1h.csv")
            if os.path.exists(hist_file):
                pair_results['files_found'].append('1h_historical')
            else:
                pair_results['files_missing'].append('1h_historical')
            
            # Check for multi-timeframe data
            for tf in self.timeframes:
                tf_file = os.path.join(self.data_dirs['timeframes'], tf, "processed", f"{pair.lower()}_{tf}.csv")
                if os.path.exists(tf_file):
                    pair_results['files_found'].append(f'{tf}_processed')
                else:
                    pair_results['files_missing'].append(f'{tf}_processed')
            
            validation_results[pair] = pair_results
            
            # Log summary
            if pair_results['issues']:
                self.logger.warning(f"   ⚠️  {pair}: {len(pair_results['issues'])} issues")
            else:
                self.logger.info(f"   ✅ {pair}: OK")
        
        return validation_results
    
    def run_gap_analysis(self) -> Dict[str, Any]:
        """Run comprehensive gap analysis"""
        self.logger.info("🔍 Running gap analysis...")
        
        try:
            gap_results = self.gap_analyzer.run_comprehensive_gap_analysis()
            
            # Check if results meet requirements
            summary = gap_results['overall_summary']
            min_completeness = self.config.get('data_validation', {}).get('min_completeness', 0.90)
            max_critical_gaps = self.config.get('data_validation', {}).get('max_critical_gaps', 2)
            
            if summary['average_completeness'] < min_completeness * 100:
                self.logger.error(f"❌ Data completeness too low: {summary['average_completeness']:.1f}% < {min_completeness * 100:.1f}%")
                return {'status': 'failed', 'reason': 'insufficient_completeness', 'results': gap_results}
            
            if summary['total_critical_gaps'] > max_critical_gaps:
                self.logger.error(f"❌ Too many critical gaps: {summary['total_critical_gaps']} > {max_critical_gaps}")
                return {'status': 'failed', 'reason': 'too_many_gaps', 'results': gap_results}
            
            self.logger.info(f"✅ Gap analysis passed: {summary['average_completeness']:.1f}% completeness, {summary['total_critical_gaps']} critical gaps")
            return {'status': 'passed', 'results': gap_results}
            
        except Exception as e:
            self.logger.error(f"❌ Gap analysis failed: {e}")
            return {'status': 'failed', 'reason': 'analysis_error', 'error': str(e)}
    
    def fill_data_gaps(self) -> bool:
        """Fill data gaps if needed"""
        self.logger.info("🔧 Checking if gap filling is needed...")
        
        try:
            # Run gap analysis first
            gap_analysis = self.run_gap_analysis()
            
            if gap_analysis['status'] == 'passed':
                self.logger.info("✅ No gap filling needed")
                return True
            
            if gap_analysis['status'] == 'failed':
                self.logger.info("🔧 Attempting to fill data gaps...")
                
                # Run gap filler
                fill_results = self.gap_filler.run_comprehensive_gap_filling()
                
                if fill_results.get('success', False):
                    self.logger.info("✅ Gap filling completed successfully")
                    
                    # Re-run gap analysis to verify
                    verification = self.run_gap_analysis()
                    if verification['status'] == 'passed':
                        self.logger.info("✅ Data quality verified after gap filling")
                        return True
                    else:
                        self.logger.error("❌ Data quality still insufficient after gap filling")
                        return False
                else:
                    self.logger.error("❌ Gap filling failed")
                    return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error in gap filling: {e}")
            return False
    
    def validate_data_quality(self) -> Dict[str, Any]:
        """Validate overall data quality"""
        self.logger.info("📊 Validating data quality...")
        
        quality_results = {
            'overall_status': 'unknown',
            'currency_pairs': {},
            'issues': [],
            'recommendations': []
        }
        
        try:
            # Validate each currency pair
            pair_validation = self.validate_currency_pair_data()
            
            # Analyze results
            total_pairs = len(self.currency_pairs)
            pairs_with_issues = 0
            pairs_missing_critical = 0
            
            for pair, results in pair_validation.items():
                quality_results['currency_pairs'][pair] = results
                
                if results['issues']:
                    pairs_with_issues += 1
                
                if '1h_completed' in results['files_missing']:
                    pairs_missing_critical += 1
                    quality_results['issues'].append(f"{pair}: Missing critical 1h completed data")
            
            # Determine overall status
            if pairs_missing_critical > 0:
                quality_results['overall_status'] = 'critical_failure'
                quality_results['recommendations'].append("CRITICAL: Missing essential 1h completed data files")
            elif pairs_with_issues > total_pairs * 0.3:  # More than 30% have issues
                quality_results['overall_status'] = 'poor'
                quality_results['recommendations'].append("POOR: More than 30% of pairs have data quality issues")
            elif pairs_with_issues > 0:
                quality_results['overall_status'] = 'fair'
                quality_results['recommendations'].append("FAIR: Some pairs have minor data quality issues")
            else:
                quality_results['overall_status'] = 'excellent'
                quality_results['recommendations'].append("EXCELLENT: All pairs have good data quality")
            
            # Add specific recommendations
            if pairs_missing_critical == 0:
                quality_results['recommendations'].append("✅ Essential data files present")
            
            if pairs_with_issues < total_pairs * 0.1:  # Less than 10% have issues
                quality_results['recommendations'].append("✅ Data quality is acceptable for strategy search")
            
            self.logger.info(f"📊 Data quality status: {quality_results['overall_status'].upper()}")
            self.logger.info(f"   Pairs with issues: {pairs_with_issues}/{total_pairs}")
            self.logger.info(f"   Pairs missing critical data: {pairs_missing_critical}/{total_pairs}")
            
            return quality_results
            
        except Exception as e:
            self.logger.error(f"❌ Data quality validation failed: {e}")
            quality_results['overall_status'] = 'error'
            quality_results['issues'].append(f"Validation error: {str(e)}")
            return quality_results
    
    def generate_data_report(self, validation_results: Dict[str, Any]) -> str:
        """Generate comprehensive data validation report"""
        report = f"""# DATA PIPELINE VALIDATION REPORT

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## EXECUTIVE SUMMARY

**Overall Status:** {validation_results['overall_status'].upper()}
**Currency Pairs:** {len(self.currency_pairs)}
**Timeframes:** {', '.join(self.timeframes)}

## CURRENCY PAIR STATUS

"""
        
        for pair, results in validation_results['currency_pairs'].items():
            status = "✅" if not results['issues'] else "⚠️" if len(results['issues']) < 3 else "❌"
            report += f"### {pair} {status}\n"
            report += f"- **Files Found:** {', '.join(results['files_found'])}\n"
            if results['files_missing']:
                report += f"- **Files Missing:** {', '.join(results['files_missing'])}\n"
            if results['issues']:
                report += f"- **Issues:** {len(results['issues'])}\n"
                for issue in results['issues']:
                    report += f"  - {issue}\n"
            report += "\n"
        
        if validation_results['issues']:
            report += "## CRITICAL ISSUES\n\n"
            for issue in validation_results['issues']:
                report += f"- {issue}\n"
            report += "\n"
        
        if validation_results['recommendations']:
            report += "## RECOMMENDATIONS\n\n"
            for i, rec in enumerate(validation_results['recommendations'], 1):
                report += f"{i}. {rec}\n"
        
        return report
    
    def run_comprehensive_validation(self) -> bool:
        """Run comprehensive data pipeline validation"""
        self.logger.info("🚀 Starting comprehensive data pipeline validation")
        self.logger.info("=" * 80)
        
        try:
            # Step 1: Validate directory structure
            if not self.validate_data_structure():
                self.logger.error("❌ Directory structure validation failed")
                return False
            
            # Step 2: Validate currency pair data
            pair_validation = self.validate_currency_pair_data()
            
            # Step 3: Run gap analysis
            gap_analysis = self.run_gap_analysis()
            
            # Step 4: Fill gaps if needed
            if gap_analysis['status'] == 'failed':
                if not self.fill_data_gaps():
                    self.logger.error("❌ Gap filling failed")
                    return False
            
            # Step 5: Validate overall data quality
            quality_results = self.validate_data_quality()
            
            # Step 6: Generate report
            report = self.generate_data_report(quality_results)
            
            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"data_validation_report_{timestamp}.md"
            with open(report_file, 'w') as f:
                f.write(report)
            
            self.logger.info(f"📋 Data validation report saved: {report_file}")
            
            # Final status
            if quality_results['overall_status'] in ['excellent', 'fair']:
                self.logger.info("✅ Data pipeline validation PASSED")
                self.logger.info("🎯 Ready for strategy search")
                return True
            else:
                self.logger.error("❌ Data pipeline validation FAILED")
                self.logger.error("🔧 Please address the issues before running strategy search")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Comprehensive validation failed: {e}")
            return False

def main():
    """Main execution function"""
    try:
        validator = DataPipelineValidator()
        success = validator.run_comprehensive_validation()
        
        if success:
            print("\n🎯 DATA PIPELINE READY FOR STRATEGY SEARCH")
            print("You can now run: python controller.py")
        else:
            print("\n❌ DATA PIPELINE NOT READY")
            print("Please address the issues before running strategy search")
            
    except KeyboardInterrupt:
        logger.info("🛑 Validation interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()
