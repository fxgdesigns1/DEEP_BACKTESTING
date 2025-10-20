#!/usr/bin/env python3
"""
📊 SYNC STATUS DASHBOARD
Real-time dashboard for monitoring sync status between desktop and laptop
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import psutil

class SyncStatusDashboard:
    """Real-time sync status dashboard"""
    
    def __init__(self, project_path: str = None):
        self.project_path = Path(project_path or os.getcwd())
        self.dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'device_info': {},
            'sync_status': {},
            'file_status': {},
            'data_status': {},
            'session_status': {},
            'recommendations': [],
            'overall_status': 'UNKNOWN'
        }
        
    def run_dashboard(self, refresh_interval: int = 30):
        """Run real-time dashboard"""
        print("📊 SYNC STATUS DASHBOARD")
        print("=" * 60)
        print(f"Project Path: {self.project_path}")
        print(f"Refresh Interval: {refresh_interval} seconds")
        print("Press Ctrl+C to stop")
        print()
        
        try:
            while True:
                self._update_dashboard()
                self._display_dashboard()
                time.sleep(refresh_interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Dashboard stopped by user")
            return self.dashboard_data
            
        except Exception as e:
            print(f"❌ Dashboard error: {e}")
            return self.dashboard_data
    
    def _update_dashboard(self):
        """Update dashboard data"""
        try:
            # Update timestamp
            self.dashboard_data['timestamp'] = datetime.now().isoformat()
            
            # Update device info
            self._update_device_info()
            
            # Update sync status
            self._update_sync_status()
            
            # Update file status
            self._update_file_status()
            
            # Update data status
            self._update_data_status()
            
            # Update session status
            self._update_session_status()
            
            # Generate recommendations
            self._generate_recommendations()
            
            # Assess overall status
            self._assess_overall_status()
            
        except Exception as e:
            self.dashboard_data['recommendations'].append(f"Dashboard update failed: {str(e)}")
    
    def _update_device_info(self):
        """Update device information"""
        try:
            self.dashboard_data['device_info'] = {
                'hostname': os.uname().nodename if hasattr(os, 'uname') else os.environ.get('COMPUTERNAME', 'Unknown'),
                'platform': sys.platform,
                'python_version': sys.version.split()[0],
                'working_directory': str(self.project_path),
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_usage': psutil.disk_usage(str(self.project_path))._asdict()
            }
        except Exception as e:
            self.dashboard_data['device_info']['error'] = str(e)
    
    def _update_sync_status(self):
        """Update sync status"""
        try:
            sync_status = {
                'last_activity': None,
                'recent_files': [],
                'sync_indicators': {},
                'sync_confidence': 0
            }
            
            # Check for recent activity
            recent_files = []
            for root, dirs, files in os.walk(self.project_path):
                for file in files:
                    if file.endswith(('.log', '.json', '.md', '.py', '.yaml', '.csv')):
                        file_path = Path(root) / file
                        try:
                            modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if (datetime.now() - modified_time).hours < 24:
                                recent_files.append({
                                    'file': str(file_path.relative_to(self.project_path)),
                                    'modified': modified_time.isoformat(),
                                    'size': file_path.stat().st_size
                                })
                        except Exception:
                            continue
            
            if recent_files:
                sync_status['recent_files'] = sorted(recent_files, key=lambda x: x['modified'], reverse=True)[:10]
                sync_status['last_activity'] = sync_status['recent_files'][0]['modified']
            
            # Check sync indicators
            sync_indicators = {
                'log_files': len(list(self.project_path.glob('*.log'))),
                'result_files': len(list(self.project_path.rglob('results/**/*.json'))),
                'backup_files': len(list(self.project_path.rglob('**/*.backup'))),
                'config_files': len(list(self.project_path.rglob('config/**/*'))),
                'strategy_files': len(list(self.project_path.rglob('strategies/**/*.py')))
            }
            
            sync_status['sync_indicators'] = sync_indicators
            
            # Calculate sync confidence
            total_indicators = sum(sync_indicators.values())
            if total_indicators > 0:
                sync_status['sync_confidence'] = min(100, (total_indicators / 20) * 100)
            else:
                sync_status['sync_confidence'] = 0
            
            self.dashboard_data['sync_status'] = sync_status
            
        except Exception as e:
            self.dashboard_data['sync_status']['error'] = str(e)
    
    def _update_file_status(self):
        """Update file status"""
        try:
            critical_files = [
                'RESUME_HERE.md',
                'NEXT_AGENT_SESSION_GUIDE.md',
                'SYSTEM_VERIFICATION.py',
                'check_status.py',
                'controller.py',
                'requirements.txt'
            ]
            
            file_status = {}
            for file_name in critical_files:
                file_path = self.project_path / file_name
                file_status[file_name] = {
                    'exists': file_path.exists(),
                    'size': file_path.stat().st_size if file_path.exists() else 0,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat() if file_path.exists() else None,
                    'hash': None
                }
                
                if file_path.exists():
                    try:
                        with open(file_path, 'rb') as f:
                            file_status[file_name]['hash'] = hashlib.md5(f.read()).hexdigest()
                    except Exception:
                        pass
            
            self.dashboard_data['file_status'] = file_status
            
        except Exception as e:
            self.dashboard_data['file_status']['error'] = str(e)
    
    def _update_data_status(self):
        """Update data status"""
        try:
            data_status = {
                'master_dataset': {},
                'backtesting_results': {},
                'strategy_files': {},
                'configuration_files': {}
            }
            
            # Check master dataset
            master_dataset_path = self.project_path / 'data' / 'MASTER_ALIGNED_DATASET'
            if master_dataset_path.exists():
                dataset_files = list(master_dataset_path.glob('*.csv'))
                data_status['master_dataset'] = {
                    'exists': True,
                    'file_count': len(dataset_files),
                    'total_size': sum(f.stat().st_size for f in dataset_files),
                    'latest_modified': max(f.stat().st_mtime for f in dataset_files) if dataset_files else None
                }
            else:
                data_status['master_dataset'] = {'exists': False}
            
            # Check backtesting results
            results_path = self.project_path / 'results'
            if results_path.exists():
                result_files = list(results_path.rglob('*.json'))
                data_status['backtesting_results'] = {
                    'exists': True,
                    'file_count': len(result_files),
                    'total_size': sum(f.stat().st_size for f in result_files),
                    'latest_file': max(result_files, key=lambda x: x.stat().st_mtime).name if result_files else None
                }
            else:
                data_status['backtesting_results'] = {'exists': False}
            
            # Check strategy files
            strategies_path = self.project_path / 'strategies'
            if strategies_path.exists():
                strategy_files = list(strategies_path.glob('*.py'))
                data_status['strategy_files'] = {
                    'exists': True,
                    'file_count': len(strategy_files),
                    'files': [f.name for f in strategy_files]
                }
            else:
                data_status['strategy_files'] = {'exists': False}
            
            self.dashboard_data['data_status'] = data_status
            
        except Exception as e:
            self.dashboard_data['data_status']['error'] = str(e)
    
    def _update_session_status(self):
        """Update session status"""
        try:
            session_status = {
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
                session_status['resume_file_status'] = 'EXISTS'
            else:
                session_status['resume_file_status'] = 'MISSING'
                session_status['missing_components'].append('RESUME_HERE.md')
            
            # Check next session guide
            next_session_file = self.project_path / 'NEXT_AGENT_SESSION_GUIDE.md'
            if next_session_file.exists():
                session_status['next_session_guide_status'] = 'EXISTS'
            else:
                session_status['next_session_guide_status'] = 'MISSING'
                session_status['missing_components'].append('NEXT_AGENT_SESSION_GUIDE.md')
            
            # Check system verification
            system_verification = self.project_path / 'SYSTEM_VERIFICATION.py'
            if system_verification.exists():
                session_status['system_verification_status'] = 'EXISTS'
            else:
                session_status['system_verification_status'] = 'MISSING'
                session_status['missing_components'].append('SYSTEM_VERIFICATION.py')
            
            # Calculate resume confidence
            total_components = 3
            existing_components = sum([
                1 for status in [
                    session_status['resume_file_status'],
                    session_status['next_session_guide_status'],
                    session_status['system_verification_status']
                ] if status == 'EXISTS'
            ])
            
            session_status['resume_confidence'] = (existing_components / total_components) * 100
            
            # Determine if can resume
            if session_status['resume_confidence'] >= 80:
                session_status['can_resume'] = True
            
            self.dashboard_data['session_status'] = session_status
            
        except Exception as e:
            self.dashboard_data['session_status']['error'] = str(e)
    
    def _generate_recommendations(self):
        """Generate recommendations"""
        recommendations = []
        
        # Check for missing critical files
        missing_files = [f for f in self.dashboard_data['file_status'].values() if not f.get('exists', False)]
        if missing_files:
            recommendations.append(f"Sync missing critical files: {len(missing_files)} files")
        
        # Check data consistency
        if not self.dashboard_data['data_status'].get('master_dataset', {}).get('exists', False):
            recommendations.append("Sync master dataset from working device")
        
        if not self.dashboard_data['data_status'].get('backtesting_results', {}).get('exists', False):
            recommendations.append("Sync backtesting results from working device")
        
        # Check session status
        if not self.dashboard_data['session_status'].get('can_resume', False):
            recommendations.append("Ensure all resume files are synced before continuing")
        
        # Check sync status
        if self.dashboard_data['sync_status'].get('sync_confidence', 0) < 50:
            recommendations.append("Verify sync status with working device")
        
        self.dashboard_data['recommendations'] = recommendations
    
    def _assess_overall_status(self):
        """Assess overall status"""
        try:
            critical_issues = 0
            warning_issues = 0
            
            # Count issues
            for rec in self.dashboard_data['recommendations']:
                if any(keyword in rec.lower() for keyword in ['missing', 'not ready', 'failed']):
                    critical_issues += 1
                else:
                    warning_issues += 1
            
            # Assess status
            if critical_issues == 0 and warning_issues == 0:
                self.dashboard_data['overall_status'] = 'EXCELLENT'
            elif critical_issues == 0:
                self.dashboard_data['overall_status'] = 'GOOD'
            elif critical_issues <= 2:
                self.dashboard_data['overall_status'] = 'FAIR'
            else:
                self.dashboard_data['overall_status'] = 'POOR'
                
        except Exception as e:
            self.dashboard_data['overall_status'] = 'ERROR'
    
    def _display_dashboard(self):
        """Display dashboard"""
        # Clear screen (works on most terminals)
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("📊 SYNC STATUS DASHBOARD")
        print("=" * 60)
        print(f"Timestamp: {self.dashboard_data['timestamp']}")
        print(f"Device: {self.dashboard_data['device_info'].get('hostname', 'Unknown')}")
        print(f"Platform: {self.dashboard_data['device_info'].get('platform', 'Unknown')}")
        print()
        
        # Overall status
        status_emoji = {
            'EXCELLENT': '🟢',
            'GOOD': '🟡',
            'FAIR': '🟠',
            'POOR': '🔴',
            'ERROR': '❌'
        }
        
        print(f"Overall Status: {status_emoji.get(self.dashboard_data['overall_status'], '❓')} {self.dashboard_data['overall_status']}")
        print()
        
        # Sync status
        sync_status = self.dashboard_data['sync_status']
        print(f"Sync Confidence: {sync_status.get('sync_confidence', 0):.1f}%")
        print(f"Recent Files: {len(sync_status.get('recent_files', []))}")
        print(f"Last Activity: {sync_status.get('last_activity', 'None')}")
        print()
        
        # File status
        file_status = self.dashboard_data['file_status']
        existing_files = sum(1 for f in file_status.values() if f.get('exists', False))
        total_files = len(file_status)
        print(f"Critical Files: {existing_files}/{total_files}")
        print()
        
        # Data status
        data_status = self.dashboard_data['data_status']
        print(f"Master Dataset: {'✅' if data_status.get('master_dataset', {}).get('exists', False) else '❌'}")
        print(f"Backtesting Results: {'✅' if data_status.get('backtesting_results', {}).get('exists', False) else '❌'}")
        print(f"Strategy Files: {'✅' if data_status.get('strategy_files', {}).get('exists', False) else '❌'}")
        print()
        
        # Session status
        session_status = self.dashboard_data['session_status']
        print(f"Can Resume: {'✅' if session_status.get('can_resume', False) else '❌'}")
        print(f"Resume Confidence: {session_status.get('resume_confidence', 0):.1f}%")
        print()
        
        # Recommendations
        if self.dashboard_data['recommendations']:
            print("📋 Recommendations:")
            for i, rec in enumerate(self.dashboard_data['recommendations'], 1):
                print(f"  {i}. {rec}")
        else:
            print("✅ No issues detected")
        
        print()
        print("=" * 60)
        print("Press Ctrl+C to stop dashboard")
        print(f"Next refresh in 30 seconds...")
    
    def get_snapshot(self) -> Dict[str, Any]:
        """Get current dashboard snapshot"""
        self._update_dashboard()
        return self.dashboard_data.copy()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync Status Dashboard')
    parser.add_argument('--path', '-p', default=None, help='Project path')
    parser.add_argument('--interval', '-i', type=int, default=30, help='Refresh interval in seconds')
    parser.add_argument('--snapshot', '-s', action='store_true', help='Get single snapshot instead of continuous dashboard')
    
    args = parser.parse_args()
    
    dashboard = SyncStatusDashboard(args.path)
    
    if args.snapshot:
        snapshot = dashboard.get_snapshot()
        print(json.dumps(snapshot, indent=2, default=str))
    else:
        dashboard.run_dashboard(args.interval)

if __name__ == "__main__":
    main()
