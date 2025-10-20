#!/usr/bin/env python3
"""
🔄 SESSION CONTINUITY CHECKER
Ensures seamless continuation of work between desktop and laptop
"""

import os
import sys
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

class SessionContinuityChecker:
    """Comprehensive session continuity verification"""
    
    def __init__(self, project_path: str = None):
        self.project_path = Path(project_path or os.getcwd())
        self.continuity_status = {
            'timestamp': datetime.now().isoformat(),
            'session_files': {},
            'data_consistency': {},
            'resume_capability': {},
            'sync_status': {},
            'recommendations': []
        }
        
    def check_session_continuity(self) -> Dict[str, Any]:
        """Check complete session continuity"""
        print("🔄 SESSION CONTINUITY CHECKER")
        print("=" * 50)
        print(f"Project Path: {self.project_path}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        try:
            # Check session files
            self._check_session_files()
            
            # Check data consistency
            self._check_data_consistency()
            
            # Check resume capability
            self._check_resume_capability()
            
            # Check sync status
            self._check_sync_status()
            
            # Generate recommendations
            self._generate_continuity_recommendations()
            
            # Generate report
            self._generate_continuity_report()
            
            return self.continuity_status
            
        except Exception as e:
            self.continuity_status['recommendations'].append(f"Continuity check failed: {str(e)}")
            print(f"❌ Continuity check failed: {e}")
            return self.continuity_status
    
    def _check_session_files(self):
        """Check critical session files"""
        print("📁 Checking Session Files...")
        
        session_files = {
            'RESUME_HERE.md': {
                'path': 'RESUME_HERE.md',
                'critical': True,
                'description': 'Main resume file with current status'
            },
            'NEXT_AGENT_SESSION_GUIDE.md': {
                'path': 'NEXT_AGENT_SESSION_GUIDE.md',
                'critical': True,
                'description': 'Guide for next agent session'
            },
            'SYSTEM_VERIFICATION.py': {
                'path': 'SYSTEM_VERIFICATION.py',
                'critical': True,
                'description': 'System verification script'
            },
            'check_status.py': {
                'path': 'check_status.py',
                'critical': True,
                'description': 'Status checking script'
            },
            'controller.py': {
                'path': 'controller.py',
                'critical': True,
                'description': 'Main controller script'
            }
        }
        
        self.continuity_status['session_files'] = {}
        
        for file_name, file_info in session_files.items():
            file_path = self.project_path / file_info['path']
            file_status = {
                'exists': file_path.exists(),
                'size': 0,
                'modified': None,
                'hash': None,
                'critical': file_info['critical'],
                'description': file_info['description']
            }
            
            if file_path.exists():
                try:
                    stat = file_path.stat()
                    file_status['size'] = stat.st_size
                    file_status['modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                    
                    # Calculate file hash
                    with open(file_path, 'rb') as f:
                        file_status['hash'] = hashlib.md5(f.read()).hexdigest()
                    
                    print(f"✅ {file_name}: {file_status['size']} bytes")
                except Exception as e:
                    file_status['error'] = str(e)
                    print(f"⚠️  {file_name}: Error reading - {e}")
            else:
                print(f"❌ {file_name}: Missing")
            
            self.continuity_status['session_files'][file_name] = file_status
    
    def _check_data_consistency(self):
        """Check data consistency across devices"""
        print("🔍 Checking Data Consistency...")
        
        data_consistency = {
            'master_dataset': {},
            'backtesting_results': {},
            'strategy_files': {},
            'configuration_files': {}
        }
        
        # Check master dataset
        master_dataset_path = self.project_path / 'data' / 'MASTER_ALIGNED_DATASET'
        if master_dataset_path.exists():
            dataset_files = list(master_dataset_path.glob('*.csv'))
            data_consistency['master_dataset'] = {
                'exists': True,
                'file_count': len(dataset_files),
                'total_size': sum(f.stat().st_size for f in dataset_files),
                'files': [f.name for f in dataset_files],
                'latest_modified': max(f.stat().st_mtime for f in dataset_files) if dataset_files else None
            }
            print(f"✅ Master Dataset: {len(dataset_files)} files")
        else:
            data_consistency['master_dataset'] = {'exists': False}
            print("❌ Master Dataset: Missing")
        
        # Check backtesting results
        results_path = self.project_path / 'results'
        if results_path.exists():
            result_files = list(results_path.rglob('*.json'))
            data_consistency['backtesting_results'] = {
                'exists': True,
                'file_count': len(result_files),
                'total_size': sum(f.stat().st_size for f in result_files),
                'latest_file': max(result_files, key=lambda x: x.stat().st_mtime).name if result_files else None
            }
            print(f"✅ Backtesting Results: {len(result_files)} files")
        else:
            data_consistency['backtesting_results'] = {'exists': False}
            print("❌ Backtesting Results: Missing")
        
        # Check strategy files
        strategies_path = self.project_path / 'strategies'
        if strategies_path.exists():
            strategy_files = list(strategies_path.glob('*.py'))
            data_consistency['strategy_files'] = {
                'exists': True,
                'file_count': len(strategy_files),
                'files': [f.name for f in strategy_files]
            }
            print(f"✅ Strategy Files: {len(strategy_files)} files")
        else:
            data_consistency['strategy_files'] = {'exists': False}
            print("❌ Strategy Files: Missing")
        
        # Check configuration files
        config_files = ['config/settings.yaml', 'requirements.txt', 'experiments.yaml']
        config_status = {}
        for config_file in config_files:
            config_path = self.project_path / config_file
            config_status[config_file] = {
                'exists': config_path.exists(),
                'size': config_path.stat().st_size if config_path.exists() else 0,
                'modified': datetime.fromtimestamp(config_path.stat().st_mtime).isoformat() if config_path.exists() else None
            }
        
        data_consistency['configuration_files'] = config_status
        
        self.continuity_status['data_consistency'] = data_consistency
    
    def _check_resume_capability(self):
        """Check if system can resume work"""
        print("🔄 Checking Resume Capability...")
        
        resume_capability = {
            'can_resume': False,
            'resume_file_status': 'UNKNOWN',
            'next_session_guide_status': 'UNKNOWN',
            'system_verification_status': 'UNKNOWN',
            'missing_components': [],
            'resume_confidence': 0
        }
        
        # Check resume file
        resume_file = self.project_path / 'RESUME_HERE.md'
        if resume_file.exists():
            resume_capability['resume_file_status'] = 'EXISTS'
            print("✅ Resume file exists")
        else:
            resume_capability['resume_file_status'] = 'MISSING'
            resume_capability['missing_components'].append('RESUME_HERE.md')
            print("❌ Resume file missing")
        
        # Check next session guide
        next_session_file = self.project_path / 'NEXT_AGENT_SESSION_GUIDE.md'
        if next_session_file.exists():
            resume_capability['next_session_guide_status'] = 'EXISTS'
            print("✅ Next session guide exists")
        else:
            resume_capability['next_session_guide_status'] = 'MISSING'
            resume_capability['missing_components'].append('NEXT_AGENT_SESSION_GUIDE.md')
            print("❌ Next session guide missing")
        
        # Check system verification
        system_verification = self.project_path / 'SYSTEM_VERIFICATION.py'
        if system_verification.exists():
            resume_capability['system_verification_status'] = 'EXISTS'
            print("✅ System verification exists")
        else:
            resume_capability['system_verification_status'] = 'MISSING'
            resume_capability['missing_components'].append('SYSTEM_VERIFICATION.py')
            print("❌ System verification missing")
        
        # Calculate resume confidence
        total_components = 3
        existing_components = sum([
            1 for status in [
                resume_capability['resume_file_status'],
                resume_capability['next_session_guide_status'],
                resume_capability['system_verification_status']
            ] if status == 'EXISTS'
        ])
        
        resume_capability['resume_confidence'] = (existing_components / total_components) * 100
        
        # Determine if can resume
        if resume_capability['resume_confidence'] >= 80:
            resume_capability['can_resume'] = True
            print("✅ System ready to resume")
        else:
            resume_capability['can_resume'] = False
            print("❌ System not ready to resume")
        
        self.continuity_status['resume_capability'] = resume_capability
    
    def _check_sync_status(self):
        """Check sync status between devices"""
        print("🔄 Checking Sync Status...")
        
        sync_status = {
            'last_activity': None,
            'recent_changes': [],
            'sync_indicators': {},
            'sync_confidence': 0
        }
        
        # Check for recent activity
        recent_files = []
        for root, dirs, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(('.log', '.json', '.md', '.py')):
                    file_path = Path(root) / file
                    try:
                        modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if (datetime.now() - modified_time).days < 1:
                            recent_files.append({
                                'file': str(file_path.relative_to(self.project_path)),
                                'modified': modified_time.isoformat(),
                                'size': file_path.stat().st_size
                            })
                    except Exception:
                        continue
        
        if recent_files:
            sync_status['recent_changes'] = sorted(recent_files, key=lambda x: x['modified'], reverse=True)[:10]
            sync_status['last_activity'] = sync_status['recent_changes'][0]['modified']
            print(f"✅ Recent activity: {len(recent_files)} files modified")
        else:
            print("⚠️  No recent activity detected")
        
        # Check sync indicators
        sync_indicators = {
            'log_files': len(list(self.project_path.glob('*.log'))),
            'result_files': len(list(self.project_path.rglob('results/**/*.json'))),
            'backup_files': len(list(self.project_path.rglob('**/*.backup'))),
            'config_files': len(list(self.project_path.rglob('config/**/*')))
        }
        
        sync_status['sync_indicators'] = sync_indicators
        
        # Calculate sync confidence
        total_indicators = sum(sync_indicators.values())
        if total_indicators > 0:
            sync_status['sync_confidence'] = min(100, (total_indicators / 10) * 100)
        else:
            sync_status['sync_confidence'] = 0
        
        print(f"✅ Sync confidence: {sync_status['sync_confidence']:.1f}%")
        
        self.continuity_status['sync_status'] = sync_status
    
    def _generate_continuity_recommendations(self):
        """Generate continuity recommendations"""
        print("💡 Generating Continuity Recommendations...")
        
        recommendations = []
        
        # Check for missing critical files
        missing_files = [f for f in self.continuity_status['session_files'].values() if not f['exists']]
        if missing_files:
            recommendations.append(f"Sync missing critical files: {', '.join([f['path'] for f in missing_files])}")
        
        # Check data consistency
        if not self.continuity_status['data_consistency'].get('master_dataset', {}).get('exists', False):
            recommendations.append("Sync master dataset from working device")
        
        if not self.continuity_status['data_consistency'].get('backtesting_results', {}).get('exists', False):
            recommendations.append("Sync backtesting results from working device")
        
        # Check resume capability
        if not self.continuity_status['resume_capability'].get('can_resume', False):
            recommendations.append("Ensure all resume files are synced before continuing")
        
        # Check sync status
        if self.continuity_status['sync_status'].get('sync_confidence', 0) < 50:
            recommendations.append("Verify sync status with working device")
        
        self.continuity_status['recommendations'] = recommendations
        
        if recommendations:
            print("📋 Continuity Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        else:
            print("✅ No continuity issues detected")
    
    def _generate_continuity_report(self):
        """Generate continuity report"""
        print("\n" + "=" * 50)
        print("📊 SESSION CONTINUITY REPORT")
        print("=" * 50)
        
        # Save detailed report
        report_path = self.project_path / "session_continuity_report.json"
        with open(report_path, 'w') as f:
            json.dump(self.continuity_status, f, indent=2, default=str)
        
        # Print summary
        print(f"Resume Capability: {'Yes' if self.continuity_status['resume_capability'].get('can_resume', False) else 'No'}")
        print(f"Resume Confidence: {self.continuity_status['resume_capability'].get('resume_confidence', 0):.1f}%")
        print(f"Sync Confidence: {self.continuity_status['sync_status'].get('sync_confidence', 0):.1f}%")
        print(f"Recent Activity: {len(self.continuity_status['sync_status'].get('recent_changes', []))} files")
        
        if self.continuity_status['recommendations']:
            print(f"\nRecommendations ({len(self.continuity_status['recommendations'])}):")
            for i, rec in enumerate(self.continuity_status['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        print(f"\nDetailed report saved to: {report_path}")
        
        return report_path

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Session Continuity Checker')
    parser.add_argument('--path', '-p', default=None, help='Project path')
    parser.add_argument('--output', '-o', default=None, help='Output report path')
    
    args = parser.parse_args()
    
    checker = SessionContinuityChecker(args.path)
    results = checker.check_session_continuity()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Report saved to: {args.output}")
    
    # Exit with appropriate code
    if results['resume_capability'].get('can_resume', False):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
