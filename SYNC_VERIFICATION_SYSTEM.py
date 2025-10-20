#!/usr/bin/env python3
"""
🔄 COMPREHENSIVE SYNC VERIFICATION SYSTEM
Ensures your backtesting system is properly synced between desktop and laptop
"""

import os
import sys
import json
import hashlib
import subprocess
import platform
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import psutil

class SyncVerificationSystem:
    """Comprehensive sync verification for multi-device backtesting system"""
    
    def __init__(self, project_path: str = None):
        self.project_path = Path(project_path or os.getcwd())
        self.sync_status = {
            'timestamp': datetime.now().isoformat(),
            'device_info': {},
            'file_sync_status': {},
            'data_integrity': {},
            'session_continuity': {},
            'sync_recommendations': [],
            'critical_files': [],
            'overall_sync_status': 'UNKNOWN'
        }
        
    def run_comprehensive_sync_check(self) -> Dict[str, Any]:
        """Run complete sync verification"""
        print("🔄 COMPREHENSIVE SYNC VERIFICATION SYSTEM")
        print("=" * 60)
        print(f"Project Path: {self.project_path}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        try:
            # Device information
            self._check_device_info()
            
            # Critical files sync status
            self._check_critical_files()
            
            # Data integrity verification
            self._check_data_integrity()
            
            # Session continuity
            self._check_session_continuity()
            
            # Generate sync recommendations
            self._generate_sync_recommendations()
            
            # Overall assessment
            self._assess_overall_sync_status()
            
            # Generate report
            self._generate_sync_report()
            
            return self.sync_status
            
        except Exception as e:
            self.sync_status['overall_sync_status'] = 'ERROR'
            self.sync_status['sync_recommendations'].append(f"Sync check failed: {str(e)}")
            print(f"❌ Sync verification failed: {e}")
            return self.sync_status
    
    def _check_device_info(self):
        """Check device information for sync tracking"""
        print("🖥️  Checking Device Information...")
        
        try:
            self.sync_status['device_info'] = {
                'platform': platform.platform(),
                'system': platform.system(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'hostname': platform.node(),
                'python_version': sys.version,
                'working_directory': str(self.project_path),
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ Platform: {platform.platform()}")
            print(f"✅ Hostname: {platform.node()}")
            print(f"✅ Python: {sys.version.split()[0]}")
            
        except Exception as e:
            self.sync_status['sync_recommendations'].append(f"Device info check failed: {str(e)}")
            print(f"❌ Device info check failed: {e}")
    
    def _check_critical_files(self):
        """Check critical files for sync status"""
        print("📁 Checking Critical Files...")
        
        critical_files = [
            'RESUME_HERE.md',
            'NEXT_AGENT_SESSION_GUIDE.md',
            'SYSTEM_VERIFICATION.py',
            'check_status.py',
            'controller.py',
            'requirements.txt',
            'config/settings.yaml',
            'data/MASTER_ALIGNED_DATASET/',
            'strategies/',
            'backtesting_output/',
            'results/'
        ]
        
        self.sync_status['critical_files'] = []
        missing_files = []
        
        for file_path in critical_files:
            full_path = self.project_path / file_path
            file_status = {
                'path': str(file_path),
                'exists': full_path.exists(),
                'size': 0,
                'modified': None,
                'hash': None
            }
            
            if full_path.exists():
                try:
                    if full_path.is_file():
                        stat = full_path.stat()
                        file_status['size'] = stat.st_size
                        file_status['modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                        
                        # Calculate file hash for integrity
                        with open(full_path, 'rb') as f:
                            file_status['hash'] = hashlib.md5(f.read()).hexdigest()
                    elif full_path.is_dir():
                        file_status['size'] = sum(f.stat().st_size for f in full_path.rglob('*') if f.is_file())
                        file_status['modified'] = datetime.fromtimestamp(full_path.stat().st_mtime).isoformat()
                        
                        # Calculate directory hash
                        dir_hash = hashlib.md5()
                        for file in sorted(full_path.rglob('*')):
                            if file.is_file():
                                with open(file, 'rb') as f:
                                    dir_hash.update(f.read())
                        file_status['hash'] = dir_hash.hexdigest()
                    
                    print(f"✅ {file_path}: {file_status['size']} bytes")
                except Exception as e:
                    file_status['error'] = str(e)
                    print(f"⚠️  {file_path}: Error reading - {e}")
            else:
                missing_files.append(file_path)
                print(f"❌ {file_path}: Missing")
            
            self.sync_status['critical_files'].append(file_status)
        
        if missing_files:
            self.sync_status['sync_recommendations'].append(f"Missing critical files: {', '.join(missing_files)}")
    
    def _check_data_integrity(self):
        """Check data integrity and consistency"""
        print("🔍 Checking Data Integrity...")
        
        try:
            data_integrity = {
                'master_dataset': {},
                'backtesting_results': {},
                'strategy_files': {},
                'configuration_files': {}
            }
            
            # Check master dataset
            master_dataset_path = self.project_path / 'data' / 'MASTER_ALIGNED_DATASET'
            if master_dataset_path.exists():
                dataset_files = list(master_dataset_path.glob('*.csv'))
                data_integrity['master_dataset'] = {
                    'exists': True,
                    'file_count': len(dataset_files),
                    'total_size': sum(f.stat().st_size for f in dataset_files),
                    'files': [f.name for f in dataset_files]
                }
                print(f"✅ Master Dataset: {len(dataset_files)} files")
            else:
                data_integrity['master_dataset'] = {'exists': False}
                print("❌ Master Dataset: Missing")
            
            # Check backtesting results
            results_path = self.project_path / 'results'
            if results_path.exists():
                result_files = list(results_path.rglob('*.json'))
                data_integrity['backtesting_results'] = {
                    'exists': True,
                    'file_count': len(result_files),
                    'total_size': sum(f.stat().st_size for f in result_files),
                    'latest_file': max(result_files, key=lambda x: x.stat().st_mtime).name if result_files else None
                }
                print(f"✅ Backtesting Results: {len(result_files)} files")
            else:
                data_integrity['backtesting_results'] = {'exists': False}
                print("❌ Backtesting Results: Missing")
            
            # Check strategy files
            strategies_path = self.project_path / 'strategies'
            if strategies_path.exists():
                strategy_files = list(strategies_path.glob('*.py'))
                data_integrity['strategy_files'] = {
                    'exists': True,
                    'file_count': len(strategy_files),
                    'files': [f.name for f in strategy_files]
                }
                print(f"✅ Strategy Files: {len(strategy_files)} files")
            else:
                data_integrity['strategy_files'] = {'exists': False}
                print("❌ Strategy Files: Missing")
            
            # Check configuration files
            config_files = ['config/settings.yaml', 'requirements.txt', 'experiments.yaml']
            config_status = {}
            for config_file in config_files:
                config_path = self.project_path / config_file
                config_status[config_file] = {
                    'exists': config_path.exists(),
                    'size': config_path.stat().st_size if config_path.exists() else 0
                }
            
            data_integrity['configuration_files'] = config_status
            
            self.sync_status['data_integrity'] = data_integrity
            
        except Exception as e:
            self.sync_status['sync_recommendations'].append(f"Data integrity check failed: {str(e)}")
            print(f"❌ Data integrity check failed: {e}")
    
    def _check_session_continuity(self):
        """Check session continuity and resume capability"""
        print("🔄 Checking Session Continuity...")
        
        try:
            session_continuity = {
                'resume_file_exists': False,
                'next_session_guide_exists': False,
                'last_activity': None,
                'system_status': 'UNKNOWN',
                'can_resume': False
            }
            
            # Check RESUME_HERE.md
            resume_file = self.project_path / 'RESUME_HERE.md'
            if resume_file.exists():
                session_continuity['resume_file_exists'] = True
                session_continuity['last_activity'] = datetime.fromtimestamp(resume_file.stat().st_mtime).isoformat()
                print("✅ Resume file exists")
            else:
                print("❌ Resume file missing")
            
            # Check NEXT_AGENT_SESSION_GUIDE.md
            next_session_file = self.project_path / 'NEXT_AGENT_SESSION_GUIDE.md'
            if next_session_file.exists():
                session_continuity['next_session_guide_exists'] = True
                print("✅ Next session guide exists")
            else:
                print("❌ Next session guide missing")
            
            # Check if system can resume
            if session_continuity['resume_file_exists'] and session_continuity['next_session_guide_exists']:
                session_continuity['can_resume'] = True
                session_continuity['system_status'] = 'READY_TO_RESUME'
                print("✅ System ready to resume")
            else:
                session_continuity['system_status'] = 'NOT_READY'
                print("❌ System not ready to resume")
            
            self.sync_status['session_continuity'] = session_continuity
            
        except Exception as e:
            self.sync_status['sync_recommendations'].append(f"Session continuity check failed: {str(e)}")
            print(f"❌ Session continuity check failed: {e}")
    
    def _generate_sync_recommendations(self):
        """Generate sync recommendations"""
        print("💡 Generating Sync Recommendations...")
        
        recommendations = []
        
        # Check for missing critical files
        missing_files = [f for f in self.sync_status['critical_files'] if not f['exists']]
        if missing_files:
            recommendations.append(f"Sync missing files: {', '.join([f['path'] for f in missing_files])}")
        
        # Check data integrity
        if not self.sync_status['data_integrity'].get('master_dataset', {}).get('exists', False):
            recommendations.append("Sync master dataset from working device")
        
        if not self.sync_status['data_integrity'].get('backtesting_results', {}).get('exists', False):
            recommendations.append("Sync backtesting results from working device")
        
        # Check session continuity
        if not self.sync_status['session_continuity'].get('can_resume', False):
            recommendations.append("Ensure RESUME_HERE.md and NEXT_AGENT_SESSION_GUIDE.md are synced")
        
        # Check for recent activity
        recent_activity = self._check_recent_activity()
        if recent_activity:
            recommendations.append(f"Recent activity detected: {recent_activity}")
        
        self.sync_status['sync_recommendations'] = recommendations
        
        if recommendations:
            print("📋 Sync Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        else:
            print("✅ No sync issues detected")
    
    def _check_recent_activity(self) -> str:
        """Check for recent activity in the system"""
        try:
            # Check for recent log files
            log_files = list(self.project_path.glob('*.log'))
            if log_files:
                latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
                if (datetime.now() - datetime.fromtimestamp(latest_log.stat().st_mtime)).days < 1:
                    return f"Recent log activity: {latest_log.name}"
            
            # Check for recent results
            results_path = self.project_path / 'results'
            if results_path.exists():
                result_files = list(results_path.rglob('*.json'))
                if result_files:
                    latest_result = max(result_files, key=lambda x: x.stat().st_mtime)
                    if (datetime.now() - datetime.fromtimestamp(latest_result.stat().st_mtime)).days < 1:
                        return f"Recent results: {latest_result.name}"
            
            return None
            
        except Exception:
            return None
    
    def _assess_overall_sync_status(self):
        """Assess overall sync status"""
        print("📊 Assessing Overall Sync Status...")
        
        critical_issues = 0
        warning_issues = 0
        
        # Count issues
        for rec in self.sync_status['sync_recommendations']:
            if any(keyword in rec.lower() for keyword in ['missing', 'not ready', 'failed']):
                critical_issues += 1
            else:
                warning_issues += 1
        
        # Assess status
        if critical_issues == 0 and warning_issues == 0:
            self.sync_status['overall_sync_status'] = 'EXCELLENT'
        elif critical_issues == 0:
            self.sync_status['overall_sync_status'] = 'GOOD'
        elif critical_issues <= 2:
            self.sync_status['overall_sync_status'] = 'FAIR'
        else:
            self.sync_status['overall_sync_status'] = 'POOR'
        
        print(f"✅ Overall Sync Status: {self.sync_status['overall_sync_status']}")
        print(f"✅ Critical Issues: {critical_issues}")
        print(f"✅ Warnings: {warning_issues}")
    
    def _generate_sync_report(self):
        """Generate comprehensive sync report"""
        print("\n" + "=" * 60)
        print("📊 SYNC VERIFICATION REPORT")
        print("=" * 60)
        
        # Save detailed report
        report_path = self.project_path / "sync_verification_report.json"
        with open(report_path, 'w') as f:
            json.dump(self.sync_status, f, indent=2, default=str)
        
        # Print summary
        print(f"Overall Sync Status: {self.sync_status['overall_sync_status']}")
        print(f"Device: {self.sync_status['device_info'].get('hostname', 'Unknown')}")
        print(f"Platform: {self.sync_status['device_info'].get('platform', 'Unknown')}")
        print(f"Critical Files: {len([f for f in self.sync_status['critical_files'] if f['exists']])}/{len(self.sync_status['critical_files'])}")
        print(f"Can Resume: {'Yes' if self.sync_status['session_continuity'].get('can_resume', False) else 'No'}")
        
        if self.sync_status['sync_recommendations']:
            print(f"\nSync Recommendations ({len(self.sync_status['sync_recommendations'])}):")
            for i, rec in enumerate(self.sync_status['sync_recommendations'], 1):
                print(f"  {i}. {rec}")
        
        print(f"\nDetailed report saved to: {report_path}")
        
        return report_path

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync Verification for Deep Backtesting')
    parser.add_argument('--path', '-p', default=None, help='Project path')
    parser.add_argument('--output', '-o', default=None, help='Output report path')
    
    args = parser.parse_args()
    
    verifier = SyncVerificationSystem(args.path)
    results = verifier.run_comprehensive_sync_check()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Report saved to: {args.output}")
    
    # Exit with appropriate code
    if results['overall_sync_status'] in ['EXCELLENT', 'GOOD']:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()



