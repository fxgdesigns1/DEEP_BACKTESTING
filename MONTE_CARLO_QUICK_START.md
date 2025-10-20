# 🎲 Monte Carlo Patterns - Quick Start Guide

## 30-Second Start

```bash
# Analyze a single backtest file
python mc_pattern_runner.py --file my_results.json

# Analyze all files in a directory
python mc_pattern_runner.py --dir backtesting_output
```

That's it! Open the generated HTML report in your browser.

## 5-Minute Tutorial

### Step 1: Check Your Data

Your backtest results should have one of these formats:

**Option A: Equity curve**
```json
{"equity": [10000, 10150, 10200, ...]}
```

**Option B: Trade list**
```json
{"trades": [{"pnl": 150, "timestamp": "..."}, ...]}
```

### Step 2: Run Analysis

```bash
cd E:\deep_backtesting_windows1\deep_backtesting
python mc_pattern_runner.py --file "H:\My Drive\AI Trading\exported strategies\final_correct_20251004_144957\all_results.json"
```

### Step 3: View Results

Look in the `monte_carlo_reports` folder:
- **HTML file**: Beautiful visual report (open in browser)
- **JSON file**: Raw data for further analysis

## Common Commands

### Fast Analysis (500 runs)
```bash
python mc_pattern_runner.py --file results.json --runs 500
```

### Thorough Analysis (2000 runs)
```bash
python mc_pattern_runner.py --file results.json --runs 2000
```

### Batch Process (limit to 10 files)
```bash
python mc_pattern_runner.py --dir backtesting_output --max-files 10
```

### Speed Mode (no HTML)
```bash
python mc_pattern_runner.py --dir backtesting_output --no-html
```

## What to Look For in Reports

### 🎯 Key Metrics

1. **Base Sharpe vs MC Sharpe**
   - Base > MC Mean = Good! (skill, not luck)
   - Base < MC P5 = Warning! (possible overfitting)

2. **Leverageability Uplift**
   - \> 0.2 = Strong! (use hour filtering)
   - 0.0 - 0.2 = Moderate
   - < 0.0 = Weak (skip hour filtering)

3. **Hour-of-Day p-value**
   - < 0.01 = Strong hour effect (filter!)
   - < 0.05 = Moderate hour effect
   - \> 0.05 = No significant effect

### 🚦 Traffic Light System

- 🟢 **Green**: Base Sharpe > 2.0, MaxDD < 10%, Uplift > 0.2
- 🟡 **Yellow**: Base Sharpe 1.0-2.0, MaxDD 10-20%, Uplift 0.0-0.2
- 🔴 **Red**: Base Sharpe < 1.0, MaxDD > 20%, Uplift < 0.0

## Real-World Example

```bash
# You have backtest results
python mc_pattern_runner.py --file my_strategy.json --runs 1000

# Output shows:
# ✅ Base Sharpe: 1.85
# ✅ MC Sharpe Mean: 1.72
# ✅ Leverageability: +0.28
# ✅ Hour effect p-value: 0.003
# 
# Best hours: [8, 9, 13]
# Worst hours: [0, 22, 23]
```

**Interpretation**: 
- Strategy is robust (base > MC mean)
- Strong hour effect detected
- Hour filtering could improve Sharpe by +0.28
- **Action**: Implement hour filter (trade only 8-9 and 13)

## View Results

### Option 1: HTML Report (Best)
```bash
# Open the HTML file
start monte_carlo_reports/mc_report_*.html
```

### Option 2: JSON Viewer
```bash
# Open the viewer HTML in browser
start mc_patterns_viewer.html
# Then drag-drop the JSON file
```

### Option 3: Command Line
```bash
# JSON is also printed to console
cat monte_carlo_reports/mc_pattern_*.json
```

## Troubleshooting

### "No valid trade data found"
```bash
# Check your JSON structure
python -c "import json; print(json.load(open('your_file.json')).keys())"
```

### "Module not found"
```bash
pip install numpy pandas scipy statsmodels scikit-learn
```

### Performance is slow
```bash
# Use fewer runs
python mc_pattern_runner.py --file results.json --runs 500

# Skip HTML
python mc_pattern_runner.py --file results.json --no-html
```

## Next Steps

1. ✅ Run MC analysis on your best strategies
2. ✅ Review HTML reports
3. ✅ Implement hour filtering if beneficial
4. ✅ Re-run backtests with optimizations
5. ✅ Compare before/after results

## Pro Tips

💡 **Run MC analysis BEFORE deploying live**
💡 **Use 1000+ runs for final validation**
💡 **Check multiple strategies to find patterns**
💡 **Save HTML reports for documentation**
💡 **Re-run MC analysis quarterly**

## Help

Full documentation: `MONTE_CARLO_PATTERNS_README.md`

Questions? Check:
1. README file (detailed docs)
2. Log files (*.log)
3. Example commands above

---

**You're ready to go! Start analyzing your strategies now.** 🚀




