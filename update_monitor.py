#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Update Monitor for Live Trading System Improvements
Checks H:\\My Drive\\AI Trading\\Backtesting updates for new files and changes
Version: 1.0.0
Date: October 11, 2025
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import time

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'ignore')

class UpdateMonitor:
    """Monitor the updates folder for changes from live trading system"""
    
    def __init__(self):
        self.updates_folder = Path(r"H:\My Drive\AI Trading\Backtesting updates")
        self.state_file = Path("update_monitor_state.json")
        self.last_state = self.load_state()
        
    def load_state(self) -> Dict:
        """Load the last known state of files"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            'last_check': None,
            'files': {},
            'last_notification': None
        }
    
    def save_state(self):
        """Save current state to disk"""
        with open(self.state_file, 'w') as f:
            json.dump(self.last_state, f, indent=2)
    
    def get_file_hash(self, filepath: Path) -> str:
        """Calculate MD5 hash of file contents"""
        if not filepath.exists():
            return ""
        
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    def scan_updates_folder(self) -> Dict[str, Dict]:
        """Scan the updates folder and return file information"""
        files_info = {}
        
        if not self.updates_folder.exists():
            print(f"❌ Updates folder not found: {self.updates_folder}")
            return files_info
        
        # Scan all relevant files
        for root, dirs, files in os.walk(self.updates_folder):
            # Skip certain directories
            if '__pycache__' in root or '.git' in root:
                continue
                
            for file in files:
                # Only track relevant files
                if file.endswith(('.md', '.py', '.yaml', '.yml', '.json')):
                    filepath = Path(root) / file
                    relative_path = filepath.relative_to(self.updates_folder)
                    
                    try:
                        stat = filepath.stat()
                        files_info[str(relative_path)] = {
                            'path': str(filepath),
                            'size': stat.st_size,
                            'modified': stat.st_mtime,
                            'modified_str': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'hash': self.get_file_hash(filepath)
                        }
                    except Exception as e:
                        print(f"⚠️  Error scanning {filepath}: {e}")
        
        return files_info
    
    def check_for_updates(self) -> Tuple[List[str], List[str], List[str]]:
        """
        Check for new, modified, or deleted files
        Returns: (new_files, modified_files, deleted_files)
        """
        current_files = self.scan_updates_folder()
        old_files = self.last_state.get('files', {})
        
        new_files = []
        modified_files = []
        deleted_files = []
        
        # Check for new and modified files
        for filepath, info in current_files.items():
            if filepath not in old_files:
                new_files.append(filepath)
            elif info['hash'] != old_files[filepath].get('hash', ''):
                modified_files.append(filepath)
        
        # Check for deleted files
        for filepath in old_files:
            if filepath not in current_files:
                deleted_files.append(filepath)
        
        return new_files, modified_files, deleted_files
    
    def generate_update_report(self, new_files: List[str], modified_files: List[str], 
                               deleted_files: List[str]) -> str:
        """Generate a readable update report"""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("📊 LIVE TRADING SYSTEM UPDATE REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Updates Folder: {self.updates_folder}")
        report_lines.append("")
        
        if not new_files and not modified_files and not deleted_files:
            report_lines.append("✅ No changes detected - system is up to date")
            report_lines.append("")
            return "\n".join(report_lines)
        
        # New files
        if new_files:
            report_lines.append(f"🆕 NEW FILES ({len(new_files)}):")
            report_lines.append("-" * 80)
            for filepath in sorted(new_files):
                report_lines.append(f"  + {filepath}")
            report_lines.append("")
        
        # Modified files
        if modified_files:
            report_lines.append(f"📝 MODIFIED FILES ({len(modified_files)}):")
            report_lines.append("-" * 80)
            for filepath in sorted(modified_files):
                current_files = self.scan_updates_folder()
                if filepath in current_files:
                    mod_time = current_files[filepath]['modified_str']
                    report_lines.append(f"  ✏️  {filepath}")
                    report_lines.append(f"      Last modified: {mod_time}")
            report_lines.append("")
        
        # Deleted files
        if deleted_files:
            report_lines.append(f"🗑️  DELETED FILES ({len(deleted_files)}):")
            report_lines.append("-" * 80)
            for filepath in sorted(deleted_files):
                report_lines.append(f"  - {filepath}")
            report_lines.append("")
        
        report_lines.append("=" * 80)
        report_lines.append("📋 RECOMMENDED ACTIONS:")
        report_lines.append("-" * 80)
        
        # Priority recommendations based on file types
        priority_files = [f for f in new_files + modified_files 
                         if any(x in f.lower() for x in ['readme', 'summary', 'start_here'])]
        
        if priority_files:
            report_lines.append("🔴 HIGH PRIORITY - Read these first:")
            for f in priority_files:
                report_lines.append(f"   • {f}")
            report_lines.append("")
        
        code_files = [f for f in new_files + modified_files if f.endswith('.py')]
        if code_files:
            report_lines.append("💻 CODE UPDATES - Review and integrate:")
            for f in code_files:
                report_lines.append(f"   • {f}")
            report_lines.append("")
        
        config_files = [f for f in new_files + modified_files 
                       if f.endswith(('.yaml', '.yml', '.json'))]
        if config_files:
            report_lines.append("⚙️  CONFIG UPDATES - Merge settings:")
            for f in config_files:
                report_lines.append(f"   • {f}")
            report_lines.append("")
        
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append("❓ Would you like to implement these updates?")
        report_lines.append("   Run: python update_monitor.py --implement")
        report_lines.append("")
        
        return "\n".join(report_lines)
    
    def run_check(self, save_state: bool = True) -> str:
        """Run a single check and return the report"""
        print("🔍 Scanning for updates from live trading system...")
        
        new_files, modified_files, deleted_files = self.check_for_updates()
        report = self.generate_update_report(new_files, modified_files, deleted_files)
        
        if save_state:
            # Update state
            self.last_state['last_check'] = datetime.now().isoformat()
            self.last_state['files'] = self.scan_updates_folder()
            if new_files or modified_files or deleted_files:
                self.last_state['last_notification'] = datetime.now().isoformat()
            self.save_state()
        
        return report
    
    def get_key_files_status(self) -> Dict:
        """Get status of key files that should be implemented"""
        key_files = {
            'Implementation Guide': '05_Scripts/backtest_implementation_guide.py',
            'Main Report': '02_Reports/Trading_System_Improvements_Report_2025-10-01.md',
            'Week Summary': '01_README/WEEK_OF_OCT_1_2025_SUMMARY.md',
            'Optimized Config': '04_Configs/optimized_backtesting_config.yaml',
            'Implementation Checklist': '03_Checklists/Backtesting_Implementation_Checklist.md'
        }
        
        current_files = self.scan_updates_folder()
        status = {}
        
        for name, rel_path in key_files.items():
            if rel_path in current_files:
                info = current_files[rel_path]
                status[name] = {
                    'exists': True,
                    'size_kb': round(info['size'] / 1024, 1),
                    'last_modified': info['modified_str'],
                    'path': info['path']
                }
            else:
                status[name] = {'exists': False}
        
        return status
    
    def continuous_monitor(self, check_interval_hours: int = 24):
        """Continuously monitor for updates"""
        print(f"🔄 Starting continuous monitoring...")
        print(f"   Check interval: Every {check_interval_hours} hours")
        print(f"   Updates folder: {self.updates_folder}")
        print(f"   Press Ctrl+C to stop")
        print("")
        
        try:
            while True:
                report = self.run_check()
                print(report)
                
                # Save report to file
                report_file = Path(f"update_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                report_file.write_text(report, encoding='utf-8')
                print(f"📄 Report saved to: {report_file}")
                print("")
                
                # Wait for next check
                print(f"⏳ Next check in {check_interval_hours} hours...")
                time.sleep(check_interval_hours * 3600)
                
        except KeyboardInterrupt:
            print("\n⛔ Monitoring stopped by user")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Monitor live trading system updates folder for changes'
    )
    parser.add_argument(
        '--continuous', '-c',
        action='store_true',
        help='Run continuous monitoring (check every 24 hours)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=24,
        help='Check interval in hours for continuous mode (default: 24)'
    )
    parser.add_argument(
        '--status', '-s',
        action='store_true',
        help='Show status of key files'
    )
    
    args = parser.parse_args()
    
    monitor = UpdateMonitor()
    
    if args.status:
        print("📊 KEY FILES STATUS:")
        print("=" * 80)
        status = monitor.get_key_files_status()
        for name, info in status.items():
            if info['exists']:
                print(f"✅ {name}")
                print(f"   Size: {info['size_kb']} KB")
                print(f"   Modified: {info['last_modified']}")
                print(f"   Path: {info['path']}")
            else:
                print(f"❌ {name} - NOT FOUND")
            print("")
        return
    
    if args.continuous:
        monitor.continuous_monitor(args.interval)
    else:
        # Single check
        report = monitor.run_check()
        print(report)
        
        # Save report
        report_file = Path(f"update_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        report_file.write_text(report, encoding='utf-8')
        print(f"📄 Report saved to: {report_file}")


if __name__ == "__main__":
    main()

