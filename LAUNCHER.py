#!/usr/bin/env python3
"""
PROFESSIONAL BACKTESTING SYSTEM LAUNCHER
Easy access to all system components
"""

import os
import sys
import subprocess
from datetime import datetime

class ProfessionalSystemLauncher:
    def __init__(self):
        self.base_dir = "/Users/mac/SharedNetwork/quant_strategy_ai/deep_backtesting"
        self.system_dir = os.path.join(self.base_dir, "PROFESSIONAL_SYSTEM")
        
    def show_menu(self):
        """Display main menu"""
        print("\n" + "="*80)
        print("🏆 PROFESSIONAL BACKTESTING SYSTEM LAUNCHER")
        print("="*80)
        print("Your institutional-grade forex backtesting system")
        print("="*80)
        
        print("\n📊 MAIN FUNCTIONS:")
        print("1. 🚀 Run Professional Backtest")
        print("2. 🔍 Validate Data Quality")
        print("3. 🔧 Fill Data Gaps")
        print("4. 📈 View Results")
        print("5. 📚 Open Documentation")
        print("6. 💾 Create Backup")
        print("7. 🔄 Restore from Backup")
        print("8. 📋 System Status")
        print("9. ❌ Exit")
        
        print("\n🎯 QUICK ACCESS:")
        print("A. Run All Validations")
        print("B. Run Complete Backtest")
        print("C. System Health Check")
        
        print("\n⏰ MULTI-TIMEFRAME FUNCTIONS:")
        print("D. 🕐 Run Multi-Timeframe Backtest")
        print("E. 📊 Organize Timeframe Data")
        print("F. 🔄 Download Missing Timeframes")
        
    def run_professional_backtest(self):
        """Run professional backtest"""
        print("\n🚀 RUNNING PROFESSIONAL BACKTEST...")
        print("="*60)
        
        script_path = os.path.join(self.system_dir, "CORE_ENGINES", "professional_backtesting_system.py")
        
        if os.path.exists(script_path):
            try:
                subprocess.run([sys.executable, script_path], check=True)
                print("\n✅ Professional backtest completed successfully!")
            except subprocess.CalledProcessError as e:
                print(f"\n❌ Error running backtest: {e}")
        else:
            print(f"\n❌ Backtest script not found: {script_path}")
    
    def validate_data_quality(self):
        """Validate data quality"""
        print("\n🔍 VALIDATING DATA QUALITY...")
        print("="*60)
        
        script_path = os.path.join(self.system_dir, "DATA_MANAGEMENT", "professional_data_validator.py")
        
        if os.path.exists(script_path):
            try:
                subprocess.run([sys.executable, script_path], check=True)
                print("\n✅ Data validation completed successfully!")
            except subprocess.CalledProcessError as e:
                print(f"\n❌ Error validating data: {e}")
        else:
            print(f"\n❌ Validator script not found: {script_path}")
    
    def fill_data_gaps(self):
        """Fill data gaps"""
        print("\n🔧 FILLING DATA GAPS...")
        print("="*60)
        
        script_path = os.path.join(self.system_dir, "DATA_MANAGEMENT", "professional_data_gap_filler.py")
        
        if os.path.exists(script_path):
            try:
                subprocess.run([sys.executable, script_path], check=True)
                print("\n✅ Data gap filling completed successfully!")
            except subprocess.CalledProcessError as e:
                print(f"\n❌ Error filling gaps: {e}")
        else:
            print(f"\n❌ Gap filler script not found: {script_path}")
    
    def view_results(self):
        """View results"""
        print("\n📈 VIEWING RESULTS...")
        print("="*60)
        
        results_dir = os.path.join(self.system_dir, "RESULTS")
        
        if os.path.exists(results_dir):
            print(f"📁 Results directory: {results_dir}")
            
            # List recent results
            files = os.listdir(results_dir)
            recent_files = [f for f in files if f.endswith(('.json', '.csv', '.md'))]
            
            if recent_files:
                print("\n📊 Recent Results:")
                for file in sorted(recent_files)[-5:]:  # Show last 5 files
                    file_path = os.path.join(results_dir, file)
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    print(f"   • {file} (Modified: {mod_time.strftime('%Y-%m-%d %H:%M')})")
            else:
                print("   No results files found")
        else:
            print(f"❌ Results directory not found: {results_dir}")
    
    def open_documentation(self):
        """Open documentation"""
        print("\n📚 OPENING DOCUMENTATION...")
        print("="*60)
        
        doc_dir = os.path.join(self.base_dir, "DOCUMENTATION")
        
        if os.path.exists(doc_dir):
            print(f"📁 Documentation directory: {doc_dir}")
            
            # List documentation files
            for root, dirs, files in os.walk(doc_dir):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, doc_dir)
                        print(f"   📄 {rel_path}")
        else:
            print(f"❌ Documentation directory not found: {doc_dir}")
    
    def create_backup(self):
        """Create system backup"""
        print("\n💾 CREATING SYSTEM BACKUP...")
        print("="*60)
        
        backup_script = os.path.join(self.base_dir, "backup_system.sh")
        
        if os.path.exists(backup_script):
            try:
                subprocess.run(["bash", backup_script], check=True)
                print("\n✅ System backup created successfully!")
            except subprocess.CalledProcessError as e:
                print(f"\n❌ Error creating backup: {e}")
        else:
            print(f"❌ Backup script not found: {backup_script}")
    
    def restore_from_backup(self):
        """Restore from backup"""
        print("\n🔄 RESTORING FROM BACKUP...")
        print("="*60)
        
        restore_script = os.path.join(self.base_dir, "restore_system.sh")
        
        if os.path.exists(restore_script):
            # List available backups
            backup_dir = os.path.join(self.base_dir, "SYSTEM_BACKUPS", "DAILY_BACKUPS")
            if os.path.exists(backup_dir):
                backups = [f for f in os.listdir(backup_dir) if f.endswith('.zip')]
                if backups:
                    print("📦 Available Backups:")
                    for i, backup in enumerate(sorted(backups)[-5:], 1):
                        print(f"   {i}. {backup}")
                    
                    try:
                        choice = input("\nEnter backup number to restore (or 'q' to quit): ")
                        if choice.lower() != 'q':
                            backup_index = int(choice) - 1
                            if 0 <= backup_index < len(backups):
                                backup_file = os.path.join(backup_dir, sorted(backups)[-5:][backup_index])
                                subprocess.run(["bash", restore_script, backup_file], check=True)
                                print("\n✅ System restored successfully!")
                            else:
                                print("❌ Invalid backup number")
                    except (ValueError, IndexError):
                        print("❌ Invalid input")
                else:
                    print("❌ No backups found")
            else:
                print("❌ Backup directory not found")
        else:
            print(f"❌ Restore script not found: {restore_script}")
    
    def system_status(self):
        """Show system status"""
        print("\n📋 SYSTEM STATUS...")
        print("="*60)
        
        # Check system components
        components = {
            "Core Engines": os.path.join(self.system_dir, "CORE_ENGINES"),
            "Data Management": os.path.join(self.system_dir, "DATA_MANAGEMENT"),
            "Strategies": os.path.join(self.system_dir, "STRATEGIES"),
            "Results": os.path.join(self.system_dir, "RESULTS"),
            "Data": os.path.join(self.system_dir, "DATA"),
            "Documentation": os.path.join(self.base_dir, "DOCUMENTATION")
        }
        
        print("🔍 Component Status:")
        for name, path in components.items():
            if os.path.exists(path):
                file_count = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
                print(f"   ✅ {name}: {file_count} files")
            else:
                print(f"   ❌ {name}: Not found")
        
        # Check data completeness
        data_dir = os.path.join(self.system_dir, "DATA", "completed")
        if os.path.exists(data_dir):
            completed_files = [f for f in os.listdir(data_dir) if f.endswith('_completed_1h.csv')]
            print(f"\n📊 Data Status: {len(completed_files)} completed currency pairs")
        
        # Check recent activity
        results_dir = os.path.join(self.system_dir, "RESULTS")
        if os.path.exists(results_dir):
            recent_files = []
            for root, dirs, files in os.walk(results_dir):
                for file in files:
                    if file.endswith(('.json', '.csv')):
                        file_path = os.path.join(root, file)
                        mod_time = os.path.getmtime(file_path)
                        recent_files.append((file, mod_time))
            
            if recent_files:
                recent_files.sort(key=lambda x: x[1], reverse=True)
                print(f"\n📈 Recent Activity:")
                for file, mod_time in recent_files[:3]:
                    mod_date = datetime.fromtimestamp(mod_time)
                    print(f"   • {file} ({mod_date.strftime('%Y-%m-%d %H:%M')})")
    
    def run_all_validations(self):
        """Run all validation checks"""
        print("\n🔍 RUNNING ALL VALIDATIONS...")
        print("="*60)
        
        self.validate_data_quality()
        print("\n" + "-"*60)
        self.system_status()
    
    def run_complete_backtest(self):
        """Run complete backtest suite"""
        print("\n🚀 RUNNING COMPLETE BACKTEST...")
        print("="*60)
        
        self.validate_data_quality()
        print("\n" + "-"*60)
        self.run_professional_backtest()
        print("\n" + "-"*60)
        self.view_results()
    
    def system_health_check(self):
        """Run system health check"""
        print("\n🏥 SYSTEM HEALTH CHECK...")
        print("="*60)
        
        # Check Python environment
        print("🐍 Python Environment:")
        print(f"   Version: {sys.version}")
        print(f"   Executable: {sys.executable}")
        
        # Check required packages
        required_packages = ['pandas', 'numpy', 'requests']
        print("\n📦 Required Packages:")
        for package in required_packages:
            try:
                __import__(package)
                print(f"   ✅ {package}: Available")
            except ImportError:
                print(f"   ❌ {package}: Missing")
        
        # Check system components
        self.system_status()
        
        # Check file permissions
        print("\n🔒 File Permissions:")
        critical_files = [
            "professional_backtesting_system.py",
            "professional_data_validator.py",
            "professional_data_gap_filler.py"
        ]
        
        for file in critical_files:
            file_path = os.path.join(self.system_dir, "CORE_ENGINES", file)
            if os.path.exists(file_path):
                stat_info = os.stat(file_path)
                if stat_info.st_mode & 0o200:  # Check write permission
                    print(f"   ⚠️  {file}: Writable (consider write-protecting)")
                else:
                    print(f"   🔒 {file}: Write-protected")
            else:
                print(f"   ❌ {file}: Not found")
    
    def run_multi_timeframe_backtest(self):
        """Run multi-timeframe backtest"""
        print("\n🕐 RUNNING MULTI-TIMEFRAME BACKTEST...")
        print("="*60)
        
        script_path = os.path.join(self.base_dir, "multi_timeframe_backtesting_system.py")
        
        if os.path.exists(script_path):
            try:
                subprocess.run([sys.executable, script_path], check=True)
                print("\n✅ Multi-timeframe backtest completed successfully!")
            except subprocess.CalledProcessError as e:
                print(f"\n❌ Error running multi-timeframe backtest: {e}")
        else:
            print(f"\n❌ Multi-timeframe backtest script not found: {script_path}")
    
    def organize_timeframe_data(self):
        """Organize timeframe data"""
        print("\n📊 ORGANIZING TIMEFRAME DATA...")
        print("="*60)
        
        script_path = os.path.join(self.base_dir, "multi_timeframe_data_organizer.py")
        
        if os.path.exists(script_path):
            try:
                subprocess.run([sys.executable, script_path], check=True)
                print("\n✅ Timeframe data organization completed successfully!")
            except subprocess.CalledProcessError as e:
                print(f"\n❌ Error organizing timeframe data: {e}")
        else:
            print(f"\n❌ Timeframe organizer script not found: {script_path}")
    
    def download_missing_timeframes(self):
        """Download missing timeframe data"""
        print("\n🔄 DOWNLOADING MISSING TIMEFRAMES...")
        print("="*60)
        
        script_path = os.path.join(self.base_dir, "multi_timeframe_data_acquisition.py")
        
        if os.path.exists(script_path):
            try:
                subprocess.run([sys.executable, script_path], check=True)
                print("\n✅ Missing timeframe download completed successfully!")
            except subprocess.CalledProcessError as e:
                print(f"\n❌ Error downloading missing timeframes: {e}")
        else:
            print(f"\n❌ Timeframe acquisition script not found: {script_path}")
    
    def run(self):
        """Main launcher loop"""
        while True:
            self.show_menu()
            
            try:
                choice = input("\nEnter your choice (1-9, A-F): ").strip().upper()
                
                if choice == '1':
                    self.run_professional_backtest()
                elif choice == '2':
                    self.validate_data_quality()
                elif choice == '3':
                    self.fill_data_gaps()
                elif choice == '4':
                    self.view_results()
                elif choice == '5':
                    self.open_documentation()
                elif choice == '6':
                    self.create_backup()
                elif choice == '7':
                    self.restore_from_backup()
                elif choice == '8':
                    self.system_status()
                elif choice == '9':
                    print("\n👋 Goodbye! Your professional backtesting system is ready when you need it.")
                    break
                elif choice == 'A':
                    self.run_all_validations()
                elif choice == 'B':
                    self.run_complete_backtest()
                elif choice == 'C':
                    self.system_health_check()
                elif choice == 'D':
                    self.run_multi_timeframe_backtest()
                elif choice == 'E':
                    self.organize_timeframe_data()
                elif choice == 'F':
                    self.download_missing_timeframes()
                else:
                    print("\n❌ Invalid choice. Please try again.")
                
                if choice in ['1', '2', '3', '4', '5', '6', '7', '8', 'A', 'B', 'C', 'D', 'E', 'F']:
                    input("\nPress Enter to continue...")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Your professional backtesting system is ready when you need it.")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                input("Press Enter to continue...")

def main():
    """Main execution function"""
    launcher = ProfessionalSystemLauncher()
    launcher.run()

if __name__ == "__main__":
    main()
