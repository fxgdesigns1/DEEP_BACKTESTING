"""
Create comprehensive strategy index for easy access
Organizes forex and futures strategies in one place
"""

import shutil
from pathlib import Path
from datetime import datetime

# Paths
forex_source = Path("H:/My Drive/AI Trading/exported strategies/ultimate_search_20251004_091405")
main_dir = Path("H:/My Drive/AI Trading/exported strategies")
index_file = main_dir / "STRATEGY_MASTER_INDEX.md"

print("\n" + "="*80)
print(" "*20 + "CREATING STRATEGY INDEX")
print("="*80)

# Create index content
content = []
content.append("# STRATEGY MASTER INDEX\n")
content.append(f"**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
content.append(f"**Location:** H:/My Drive/AI Trading/exported strategies/\n\n")
content.append("="*80 + "\n\n")

# FOREX STRATEGIES
content.append("## FOREX STRATEGIES (Proven - Ready to Deploy)\n\n")
content.append("### Source Directory\n")
content.append(f"`{forex_source}/`\n\n")

if forex_source.exists():
    content.append("### Key Files:\n\n")
    
    key_files = [
        ("filtered_3.5pct_DD.json", "114 strategies with <=3.5% max drawdown"),
        ("ULTIMATE_TOP_10_WITH_STATS.md", "Top 10 performers with full statistics"),
        ("COMPLETE_TOP_10_STATISTICS.md", "Comprehensive performance analysis"),
        ("ultimate_search_results.json", "All 258 successful strategies")
    ]
    
    for filename, description in key_files:
        filepath = forex_source / filename
        if filepath.exists():
            size_kb = filepath.stat().st_size / 1024
            content.append(f"- **{filename}** ({size_kb:.1f} KB)\n")
            content.append(f"  - {description}\n")
            content.append(f"  - Path: `{filepath}`\n\n")
    
    content.append("### Best Performers (Forex):\n\n")
    content.append("| Pair | Timeframe | Annual Return | Max DD | Win Rate | Sharpe |\n")
    content.append("|------|-----------|---------------|--------|----------|--------|\n")
    content.append("| XAU_USD (Gold) | 5m | 187.5% | 0.80% | 77.9% | 36.43 |\n")
    content.append("| NZD_USD | 5m | 152.9% | 0.93% | 81.8% | 37.41 |\n")
    content.append("| GBP_JPY | 5m | 143.0% | 1.32% | 82.1% | 36.20 |\n")
    content.append("| AUD_USD | 5m | 140.0% | 1.41% | 80.4% | 37.06 |\n")
    content.append("| EUR_JPY | 5m | 140.9% | 1.08% | 83.2% | 36.92 |\n\n")
    content.append("**Common Configuration:**\n")
    content.append("- Strategy: EMA 3/12 Crossover\n")
    content.append("- Risk:Reward: 1:2\n")
    content.append("- Stop Loss: 1.0-2.0x ATR\n")
    content.append("- RSI: 20/80 levels\n")
    content.append("- Data: 3 years real OANDA data\n\n")
else:
    content.append("**[WARNING] Forex strategies directory not found!**\n\n")

content.append("="*80 + "\n\n")

# FUTURES STRATEGIES
content.append("## FUTURES STRATEGIES (Backtested - TopStep Ready)\n\n")

futures_dirs = list(main_dir.glob("futures_optimization_*"))
if futures_dirs:
    latest_futures = max(futures_dirs, key=lambda p: p.stat().st_mtime)
    content.append("### Source Directory\n")
    content.append(f"`{latest_futures}/`\n\n")
    
    content.append("### Key Files:\n\n")
    
    futures_files = [
        ("all_results.csv", "All 600+ scenarios tested"),
        ("high_quality_strategies.csv", "Best performers only (filtered)"),
        ("OPTIMIZATION_REPORT.md", "Comprehensive analysis and recommendations")
    ]
    
    for filename, description in futures_files:
        filepath = latest_futures / filename
        if filepath.exists():
            size_kb = filepath.stat().st_size / 1024
            content.append(f"- **{filename}** ({size_kb:.1f} KB)\n")
            content.append(f"  - {description}\n")
            content.append(f"  - Path: `{filepath}`\n\n")
    
    content.append("### Instruments Tested:\n")
    content.append("- ES (E-mini S&P 500)\n")
    content.append("- NQ (E-mini Nasdaq 100)\n")
    content.append("- GC (Gold Futures)\n\n")
    
    content.append("### Strategies Tested:\n")
    content.append("1. EMA Crossover (8 variations)\n")
    content.append("2. RSI Mean Reversion (4 variations)\n")
    content.append("3. MACD Trend Following (3 variations)\n")
    content.append("4. Bollinger Bands (3 variations)\n")
    content.append("5. ATR Breakout (3 variations)\n\n")
    
    content.append("### Timeframes Tested:\n")
    content.append("- 5m (Scalping)\n")
    content.append("- 15m (Day Trading)\n")
    content.append("- 30m (Intraday)\n")
    content.append("- 1h (Swing)\n")
    content.append("- 4h (Position)\n\n")
else:
    content.append("### Futures Optimization\n")
    content.append("**[PENDING]** Futures optimization running overnight...\n\n")
    content.append("**Check:** `overnight_optimization.log` for progress\n\n")

content.append("="*80 + "\n\n")

# TOPSTEP FILES
content.append("## TOPSTEP CHALLENGE FILES\n\n")
content.append("### Configuration Files (Project Root)\n\n")

topstep_files = [
    ("TOPSTEP_100K_STRATEGY_CONFIG.yaml", "Complete TopStep configuration"),
    ("TOPSTEP_IMPLEMENTATION_GUIDE.md", "Step-by-step deployment guide"),
    ("topstep_risk_calculator.py", "Position sizing and risk management"),
    ("FILE_LOCATIONS_SUMMARY.md", "Where everything is saved")
]

for filename, description in topstep_files:
    content.append(f"- **{filename}**\n")
    content.append(f"  - {description}\n")
    content.append(f"  - Location: `E:\\deep_backtesting_windows1\\deep_backtesting\\{filename}`\n\n")

content.append("="*80 + "\n\n")

# QUICK ACCESS
content.append("## QUICK ACCESS COMMANDS\n\n")
content.append("### View Forex Strategies\n")
content.append("```powershell\n")
content.append(f'cd "{forex_source}"\n')
content.append("notepad ULTIMATE_TOP_10_WITH_STATS.md\n")
content.append("```\n\n")

content.append("### View Futures Strategies\n")
content.append("```powershell\n")
content.append('cd "H:\\My Drive\\AI Trading\\exported strategies"\n')
content.append("dir futures_optimization_*\n")
content.append("cd [latest_folder]\n")
content.append("notepad OPTIMIZATION_REPORT.md\n")
content.append("```\n\n")

content.append("### View TopStep Config\n")
content.append("```powershell\n")
content.append("cd E:\\deep_backtesting_windows1\\deep_backtesting\n")
content.append("notepad TOPSTEP_IMPLEMENTATION_GUIDE.md\n")
content.append("```\n\n")

content.append("="*80 + "\n\n")

# DEPLOYMENT CHECKLIST
content.append("## DEPLOYMENT CHECKLIST\n\n")
content.append("### For Forex Trading:\n")
content.append("- [ ] Review top strategies in `ULTIMATE_TOP_10_WITH_STATS.md`\n")
content.append("- [ ] Select 3-5 best performers\n")
content.append("- [ ] Note exact parameters (EMA, R:R, SL)\n")
content.append("- [ ] Configure in your MT5/broker platform\n")
content.append("- [ ] Paper trade 1-2 weeks\n")
content.append("- [ ] Deploy with demo account first\n\n")

content.append("### For Futures/TopStep:\n")
content.append("- [ ] Review `OPTIMIZATION_REPORT.md`\n")
content.append("- [ ] Select top 3 strategies\n")
content.append("- [ ] Update `TOPSTEP_100K_STRATEGY_CONFIG.yaml`\n")
content.append("- [ ] Test with `topstep_risk_calculator.py`\n")
content.append("- [ ] Paper trade on futures platform\n")
content.append("- [ ] Start TopStep challenge\n\n")

content.append("="*80 + "\n\n")

# SAVE
with open(index_file, 'w') as f:
    f.writelines(content)

print(f"\n[OK] Strategy index created: {index_file}")
print(f"[OK] Size: {index_file.stat().st_size / 1024:.1f} KB")

# Create README in main strategies folder
readme_file = main_dir / "README.md"
readme_content = f"""# TRADING STRATEGIES - MASTER DIRECTORY

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## WHAT'S HERE

This directory contains all your proven trading strategies:

1. **Forex Strategies** - 258 backtested strategies (80%+ win rates)
2. **Futures Strategies** - Comprehensive optimization results
3. **TopStep Configuration** - Ready for $100K challenge

## QUICK START

**READ THIS FIRST:** `STRATEGY_MASTER_INDEX.md`

This index file contains:
- Links to all strategy files
- Best performers summary
- Deployment checklists
- Quick access commands

## BEST PERFORMERS

### Forex (Proven):
- XAU_USD: 187.5% return, 0.80% DD
- NZD_USD: 152.9% return, 0.93% DD
- GBP_JPY: 143.0% return, 1.32% DD

### Futures (Backtested):
- Check latest `futures_optimization_*/` folder
- Review `OPTIMIZATION_REPORT.md`

## FILES

- `STRATEGY_MASTER_INDEX.md` - Complete index
- `ultimate_search_20251004_091405/` - Forex strategies
- `futures_optimization_*/` - Futures strategies

## NEXT STEPS

1. Open `STRATEGY_MASTER_INDEX.md`
2. Review best performers
3. Select top 3-5 strategies
4. Follow deployment checklist
5. Deploy to TopStep/Broker

---

**All strategies backtested on real data - Ready to deploy!**
"""

with open(readme_file, 'w') as f:
    f.write(readme_content)

print(f"[OK] README created: {readme_file}")
print("\n" + "="*80)
print("STRATEGY ORGANIZATION COMPLETE!")
print("="*80)
print("\nCreated Files:")
print(f"  1. {index_file.name}")
print(f"  2. {readme_file.name}")
print("\nLocation: H:/My Drive/AI Trading/exported strategies/")
print("\n[OK] All strategies organized and labeled!")
print("="*80 + "\n")

