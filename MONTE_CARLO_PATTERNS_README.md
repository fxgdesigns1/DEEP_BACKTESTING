# Monte Carlo Pattern Analysis System

## 🎲 Overview

This is a professional-grade Monte Carlo pattern analysis system designed for deep backtesting of trading strategies. It goes beyond traditional backtesting by using advanced statistical methods to validate strategy robustness, detect patterns, and assess leverageability.

## 🌟 Key Features

### 1. **Monte Carlo Simulations**
- **Trade Shuffling**: Permutation-based Monte Carlo to test if results are due to luck
- **Block Bootstrap**: Preserves serial correlation in returns for more realistic simulations
- Configurable number of runs (default: 1000)

### 2. **Pattern Discovery**
- **Hour-of-Day Effect**: Identifies optimal and worst trading hours using Kruskal-Wallis test
- **Autocorrelation Analysis**: Ljung-Box test to detect serial correlation in returns
- **Runs Test**: Tests for randomness in win/loss sequences
- **Motif Discovery**: Finds recurring patterns in equity curves
- **Discord Detection**: Identifies anomalous patterns (regime changes, rare events)
- **Drawdown Clustering**: Groups similar drawdown episodes using K-Means

### 3. **Leverageability Testing**
- Tests if filtering worst hours and leveraging best hours improves Sharpe ratio
- Monte Carlo-based uplift estimation with confidence intervals
- Practical strategy recommendations

### 4. **Professional Reporting**
- Beautiful HTML reports with interactive visualizations
- JSON output for programmatic analysis
- Summary statistics and interpretations
- Export-ready for presentations

## 📦 Installation

### Required Packages

The system requires the following Python packages:

```bash
pip install numpy pandas scipy statsmodels scikit-learn
```

Or install from requirements:

```bash
pip install -r requirements.txt
```

### Package Versions (Tested)
- `numpy >= 1.20.0`
- `pandas >= 1.3.0`
- `scipy >= 1.7.0`
- `statsmodels >= 0.13.0`
- `scikit-learn >= 1.0.0`

## 🚀 Quick Start

### 1. Analyze a Single Backtest File

```bash
python mc_pattern_runner.py --file my_backtest_results.json
```

### 2. Analyze All Files in a Directory

```bash
python mc_pattern_runner.py --dir backtesting_output
```

### 3. Custom Monte Carlo Settings

```bash
python mc_pattern_runner.py --file results.json --runs 2000 --block 15 --window 30
```

### 4. Analyze with Limits

```bash
# Only process first 10 files
python mc_pattern_runner.py --dir backtesting_output --max-files 10

# Skip HTML generation for faster processing
python mc_pattern_runner.py --dir backtesting_output --no-html
```

## 📊 Input Data Format

The system accepts backtest results in multiple formats:

### Format 1: Trades List

```json
{
  "trades": [
    {
      "timestamp": "2024-01-01 10:00:00",
      "pnl": 150.50,
      "hour": 10
    },
    {
      "timestamp": "2024-01-01 14:30:00",
      "pnl": -75.25,
      "hour": 14
    }
  ]
}
```

### Format 2: Equity Curve

```json
{
  "equity": [10000, 10150, 10200, 10050, 10300, ...]
}
```

### Format 3: Results Object

```json
{
  "results": {
    "trades": [...],
    "equity_curve": [...]
  }
}
```

## 📈 Output Reports

### JSON Report Structure

```json
{
  "run_id": "abc123",
  "timestamp": "2024-10-14T12:30:00Z",
  "base_metrics": {
    "sharpe": 1.45,
    "max_dd": 0.08,
    "ulcer": 0.05,
    "trades": 220
  },
  "mc": {
    "runs": 1000,
    "sharpe_mean": 1.38,
    "sharpe_p05": 0.95,
    "sharpe_p95": 1.82,
    "maxdd_mean": 0.09,
    "maxdd_p95": 0.15
  },
  "patterns": {
    "hour_of_day": {...},
    "autocorr": {...},
    "runs_test": {...},
    "motifs": {...},
    "drawdown_clusters": {...}
  },
  "leverageability": {
    "uplift_mean": 0.25,
    "uplift_p95": 0.42,
    "uplift_frac_positive": 0.78,
    "n_paths": 1000
  }
}
```

### HTML Report

Beautiful, professional HTML reports are automatically generated with:
- Key performance metrics with color coding
- Monte Carlo distribution analysis
- Hour-of-day effect tables
- Leverageability recommendations
- Pattern discovery results
- Statistical interpretations

Open in any web browser for interactive viewing.

## 🔧 Programmatic Usage

### Basic Analysis

```python
from monte_carlo_patterns import analyze

# Prepare data
data = {
    "equity": [10000, 10150, 10200, 10050, 10300, ...]
}

# Run analysis
report = analyze(
    data,
    runs=1000,
    block=10,
    window=20,
    seed=42
)

print(f"Base Sharpe: {report['base_metrics']['sharpe']:.3f}")
print(f"MC Sharpe Mean: {report['mc']['sharpe_mean']:.3f}")
print(f"Leverageability Uplift: {report['leverageability']['uplift_mean']:.3f}")
```

### Batch Analysis

```python
from monte_carlo_analyzer import MonteCarloAnalyzer

analyzer = MonteCarloAnalyzer(output_dir="my_reports")

# Analyze directory
reports = analyzer.analyze_directory(
    "backtesting_output",
    pattern="*.json",
    runs=1000,
    max_files=50
)

print(f"Analyzed {len(reports)} files")
```

### Generate HTML Report

```python
from mc_patterns_report_generator import MCPatternsReportGenerator

generator = MCPatternsReportGenerator(output_dir="my_reports")

# Load JSON report
import json
with open("mc_report.json") as f:
    report = json.load(f)

# Generate HTML
html_path = generator.generate_html_report(report)
print(f"HTML report: {html_path}")
```

## 📚 Understanding the Metrics

### Sharpe Ratio
- **Good**: > 2.0
- **Acceptable**: 1.0 - 2.0
- **Poor**: < 1.0

### Maximum Drawdown
- **Excellent**: < 10%
- **Good**: 10% - 20%
- **Concerning**: > 20%

### Monte Carlo Interpretation
- If **base Sharpe > MC mean**: Strategy shows skill beyond luck
- If **base Sharpe > MC P5**: Strategy is within normal range
- If **base Sharpe < MC P5**: ⚠️ Possible overfitting

### Leverageability Uplift
- **Strong**: > 0.2 (consider hour filtering)
- **Moderate**: 0.0 - 0.2 (may benefit from filtering)
- **Weak**: < 0.0 (hour filtering not recommended)

### Hour-of-Day Effect
- **Significant**: p-value < 0.01 (strong evidence)
- **Moderate**: p-value 0.01 - 0.05
- **Not significant**: p-value > 0.05

## 🔬 Advanced Features

### Custom Block Size

The block size in block bootstrap affects how much serial correlation is preserved:
- **Small blocks (5-10)**: More randomization
- **Medium blocks (10-20)**: Balanced (recommended)
- **Large blocks (20-50)**: Preserves more structure

```bash
python mc_pattern_runner.py --file results.json --block 15
```

### Custom Window Size

Window size for motif discovery:
- **Small windows (10-15)**: Detect short-term patterns
- **Medium windows (20-30)**: Balanced (recommended)
- **Large windows (40-60)**: Detect long-term patterns

```bash
python mc_pattern_runner.py --file results.json --window 30
```

### Random Seed Control

For reproducibility:

```bash
python mc_pattern_runner.py --file results.json --seed 12345
```

## 🎯 Use Cases

### 1. Strategy Validation
Validate that your strategy's performance is not due to luck:
```bash
python mc_pattern_runner.py --file my_strategy.json --runs 2000
```

### 2. Hour Filtering Optimization
Identify optimal trading hours:
```bash
python mc_pattern_runner.py --file my_strategy.json
# Check "Hour-of-Day Effect" section in HTML report
```

### 3. Regime Change Detection
Detect when market conditions changed:
```bash
python mc_pattern_runner.py --file my_strategy.json --window 40
# Check "Motifs & Discords" section
```

### 4. Batch Strategy Comparison
Compare multiple strategies:
```bash
python mc_pattern_runner.py --dir all_strategies --runs 1000
# Review summary statistics
```

## 📁 File Structure

```
deep_backtesting/
├── monte_carlo_patterns.py          # Core MC analysis functions
├── monte_carlo_analyzer.py          # Integration with backtest results
├── mc_patterns_report_generator.py  # HTML report generation
├── mc_pattern_runner.py             # CLI runner (main entry point)
├── mc_patterns_viewer.html          # Interactive JSON viewer
├── MONTE_CARLO_PATTERNS_README.md   # This file
└── monte_carlo_reports/             # Output directory
    ├── mc_pattern_*.json            # JSON reports
    ├── mc_report_*.html             # HTML reports
    └── mc_summary_*.json            # Summary reports
```

## 🐛 Troubleshooting

### "No valid trade data found"
- Check that your JSON has either `trades` list or `equity` array
- Ensure trades have `pnl` field

### "Insufficient data for analysis"
- Need at least 30+ trades for meaningful results
- MC simulations work best with 100+ trades

### "Module not found" errors
- Install required packages: `pip install numpy pandas scipy statsmodels scikit-learn`
- Ensure you're in the correct Python environment

### Performance Issues
- Reduce `--runs` for faster analysis (500 runs is often sufficient)
- Use `--no-html` to skip HTML generation
- Use `--max-files` to limit batch processing

## 🎓 Best Practices

1. **Use at least 1000 MC runs** for stable results
2. **Analyze multiple strategies** to find common patterns
3. **Review HTML reports visually** before making decisions
4. **Check p-values** to ensure statistical significance
5. **Validate with out-of-sample data** after MC analysis
6. **Document your findings** using the JSON reports

## 📞 Support

For issues or questions:
1. Check this README first
2. Review example commands
3. Check log files (*.log)
4. Verify input data format

## 🔄 Integration with Existing System

The MC pattern analysis system is designed to work seamlessly with your existing deep backtesting framework. It automatically detects backtest result formats and extracts the necessary data.

### Automatic Integration

Simply point to your existing backtesting output:

```bash
python mc_pattern_runner.py --dir backtesting_output
```

### Manual Integration

For custom integration into your backtesting pipeline:

```python
from monte_carlo_patterns import analyze

# After your backtest completes
backtest_results = run_backtest(...)

# Extract equity curve
equity = backtest_results['equity_curve']

# Run MC analysis
mc_report = analyze({"equity": equity}, runs=1000)

# Save or use the report
print(f"Strategy robustness score: {mc_report['mc']['sharpe_mean']:.3f}")
```

## 🚀 Future Enhancements

Planned features:
- [ ] Walk-forward Monte Carlo analysis
- [ ] Multi-strategy correlation analysis
- [ ] Real-time MC monitoring for live trading
- [ ] Machine learning pattern detection
- [ ] Regime classification with HMM

## 📜 License

Part of the Deep Backtesting Trading System.
For professional trading use.

---

**Remember**: Monte Carlo analysis is a tool for validation and insight, not a guarantee of future performance. Always use proper risk management and validate strategies on out-of-sample data.

**Trade Responsibly. Analyze Thoroughly. Succeed Consistently.** 🎯




