# ⚡ Update Monitor - Quick Reference Card

## 🚀 Common Commands

### Check for Updates Now
```bash
python update_monitor.py
```

### Check Key Files Status
```bash
python update_monitor.py --status
```

### Setup Automated Daily Checks
```powershell
# Run as Administrator
.\setup_periodic_update_check.ps1
```

### Run Continuous Monitoring
```bash
# Check every 24 hours
python update_monitor.py --continuous --interval 24

# Check every 6 hours
python update_monitor.py --continuous --interval 6
```

---

## 📁 Important File Locations

### Monitoring System
- **Monitor Script:** `update_monitor.py`
- **Setup Script:** `setup_periodic_update_check.ps1`
- **User Guide:** `UPDATE_MONITORING_SYSTEM_GUIDE.md`
- **Summary:** `UPDATES_AVAILABLE_SUMMARY.md`

### Live System Updates
- **Source Folder:** `H:\My Drive\AI Trading\Backtesting updates`
- **Start Here:** `H:\My Drive\AI Trading\Backtesting updates\01_README\START_HERE.md`
- **Implementation Code:** `H:\My Drive\AI Trading\Backtesting updates\05_Scripts\backtest_implementation_guide.py`
- **Configuration:** `H:\My Drive\AI Trading\Backtesting updates\04_Configs\optimized_backtesting_config.yaml`

### Generated Files
- **State File:** `update_monitor_state.json` (don't delete!)
- **Reports:** `update_report_YYYYMMDD_HHMMSS.txt`
- **Logs:** `update_monitor_logs\last_run.log`

---

## 🛠️ Task Scheduler Management

### View Task
```powershell
Get-ScheduledTask -TaskName "TradingSystemUpdateMonitor"
```

### Run Task Manually
```powershell
Start-ScheduledTask -TaskName "TradingSystemUpdateMonitor"
```

### Disable Task
```powershell
Disable-ScheduledTask -TaskName "TradingSystemUpdateMonitor"
```

### Enable Task
```powershell
Enable-ScheduledTask -TaskName "TradingSystemUpdateMonitor"
```

### Remove Task
```powershell
Unregister-ScheduledTask -TaskName "TradingSystemUpdateMonitor" -Confirm:$false
```

---

## 📊 Priority Updates (October 2025)

### 🔴 Critical (Implement First)
1. **Dynamic Spread Modeling** - 20-30% accuracy improvement
2. **Multi-Timeframe Alignment** - Filters 40-50% bad signals
3. **News Event Integration** - Avoids 5-10 pip slippage

### 🟡 High Priority
4. **Pullback-Based Entries** - $6+ better prices
5. **Session Filtering** - 50% spread reduction
6. **Time-Spaced Entries** - Quality over quantity

### 🟢 Standard Priority
7. **Improved R:R Ratios** - 1:3 to 1:4
8. **ATR-Based Stops** - Volatility-adaptive
9. **Signal Quality Scoring** - 100-point system

---

## 🔍 Troubleshooting

### Reset State (Force Rescan)
```bash
del update_monitor_state.json
python update_monitor.py
```

### View Last Run Log
```bash
type update_monitor_logs\last_run.log
```

### View Saved Reports
```bash
dir update_report_*.txt | sort -Property LastWriteTime -Descending
type update_report_LATEST.txt
```

### Test Python
```bash
python --version
python -c "import json, hashlib, pathlib; print('OK')"
```

---

## 📖 Reading Order

### Quick Start (30 minutes)
1. `UPDATES_AVAILABLE_SUMMARY.md` ← You are here
2. `QUICK_REFERENCE.md` ← This file
3. `H:\My Drive\...\01_README\WEEK_OF_OCT_1_2025_SUMMARY.md`

### Deep Dive (2-3 hours)
1. `UPDATE_MONITORING_SYSTEM_GUIDE.md` (monitoring system)
2. `H:\My Drive\...\01_README\START_HERE.md` (implementation guide)
3. `H:\My Drive\...\02_Reports\Trading_System_Improvements_Report_2025-10-01.md` (full analysis)
4. `H:\My Drive\...\05_Scripts\backtest_implementation_guide.py` (code review)

---

## 💡 Pro Tips

- **Don't delete** `update_monitor_state.json` unless you want to rescan everything
- **Check status** before implementing: `python update_monitor.py --status`
- **Read logs** if task seems not to run: `type update_monitor_logs\last_run.log`
- **Test manually** before automating: `python update_monitor.py`
- **Schedule off-hours** to avoid interrupting work (default: 6 AM)

---

## 🎯 Your Implementation Checklist

- [ ] Review `UPDATES_AVAILABLE_SUMMARY.md`
- [ ] Read `WEEK_OF_OCT_1_2025_SUMMARY.md`
- [ ] Run `python update_monitor.py --status`
- [ ] Decide: Implement now, review first, or defer
- [ ] If implementing: Start with Priority 1 items
- [ ] Setup automation: `.\setup_periodic_update_check.ps1`
- [ ] Test: Run manual check after setup
- [ ] Monitor: Check logs daily for first week

---

**Questions?** See `UPDATE_MONITORING_SYSTEM_GUIDE.md` for detailed help.

**Ready to implement?** Start with `UPDATES_AVAILABLE_SUMMARY.md` → Option A.

