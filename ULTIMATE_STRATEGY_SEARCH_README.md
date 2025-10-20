# Ultimate Strategy Search System

## 🎯 Overview

This is an institutional-grade FX strategy discovery system designed to find robust, production-ready trading strategies through comprehensive backtesting, walk-forward optimization, and rigorous validation.

## 🏗️ Architecture

### Core Components

1. **Backtesting Engines**
   - `ProfessionalBacktestingSystem`: 1H single-timeframe backtesting
   - `MultiTimeframeBacktestingSystem`: Multi-timeframe backtesting (1m to 1w)

2. **Strategy Library**
   - `ComprehensiveEnhancedStrategy`: News + indicators + technical analysis
   - `UltraStrictV3Strategy`: Ultra-strict criteria with AI insights
   - `NewsEnhancedStrategy`: News-driven strategy with sentiment analysis
   - `EnhancedOptimizedStrategy`: Market regime detection + dynamic risk management

3. **Validation Framework**
   - `AdvancedValidationFramework`: Walk-forward analysis, Monte Carlo validation
   - `RiskManagementFramework`: Position sizing, risk limits, portfolio tracking
   - `ProfessionalDataGapAnalyzer`: Data quality assessment and gap detection

4. **Orchestration**
   - `UltimateStrategySearchController`: Master orchestrator
   - `DataPipelineValidator`: Data readiness validation

## 🚀 Quick Start

### 1. Test Integration
```bash
python test_integration.py
```

### 2. Validate Data Pipeline
```bash
python data_pipeline_validator.py
```

### 3. Run Strategy Search
```bash
python controller.py
```

## 📊 Configuration

The system is configured via `experiments.yaml`:

### Key Parameters

```yaml
meta:
  run_name: ultimate_strategy_search
  results_dir: results
  seed: 1337
  holdout_months: 9
  wfo_test_months: 3

risk:
  capital: 100000
  risk_per_trade: [0.01, 0.015, 0.02]
  max_drawdown: 0.15

costs:
  spread_pips: [2, 3, 5]
  slippage_pips: [0.5, 1.0]

universe:
  pairs: [EUR_USD, GBP_USD, USD_JPY, AUD_USD, USD_CAD, USD_CHF, NZD_USD, EUR_JPY, GBP_JPY, XAU_USD]
  timeframes: [1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w]
  strategies: [comprehensive_enhanced_strategy, ultra_strict_v3_strategy, news_enhanced_strategy, enhanced_optimized_strategy]
```

## 🔍 Search Process

### 1. Data Validation
- Gap analysis and filling
- 5-layer data validation
- Completeness and quality checks

### 2. Baseline Testing
- No-tuning baselines for each pair/TF/strategy
- Performance metrics and trade logs

### 3. Walk-Forward Optimization
- Anchored expanding windows
- Purged K-Fold CV with embargo
- Bayesian optimization (Optuna) or grid search

### 4. Robustness Testing
- Cost/slippage stress tests
- Parameter perturbation
- Monte Carlo simulations
- Feature ablation studies

### 5. Cross-Pair Generalization
- Apply best parameters to similar pairs
- Require no catastrophic degradation

### 6. Final Holdout
- Untouched recent period
- No tuning allowed
- Executive reporting

## 📈 Selection Criteria

All criteria must be met on out-of-sample and holdout data:

- **Risk-Adjusted Returns**: OOS Sharpe ≥ 1.2, Sortino ≥ 1.6
- **Drawdown Control**: Max DD ≤ 12%, 95th percentile Monte Carlo DD ≤ 15%
- **Profitability**: Profit factor ≥ 1.3, win rate ≥ 45%
- **Trade Volume**: ≥ 400 trades (low TF) / ≥ 150 trades (high TF)
- **Robustness**: Performance persists under stress conditions
- **Stability**: Equity curve improves with filters

## 📁 Results Structure

```
results/
└── YYYY-MM-DD/
    ├── EUR_USD/
    │   ├── 1h/
    │   │   ├── comprehensive_enhanced_strategy/
    │   │   │   └── 2024-01-15T10-30-00Z/
    │   │   │       ├── summary.json
    │   │   │       ├── equity_curve.csv
    │   │   │       ├── trade_log.csv
    │   │   │       └── README.md
    │   │   └── ultra_strict_v3_strategy/
    │   └── 4h/
    ├── GBP_USD/
    ├── best_configurations.json
    ├── failures.log
    └── search_summary.json
```

## 🛡️ Risk Management

### Position Sizing
- Fixed fractional: 1-2% risk per trade
- Kelly criterion: 25% of optimal
- Volatility-adjusted sizing

### Risk Limits
- Daily risk: 6% max
- Portfolio risk: 20% max
- Max drawdown: 15% hard stop
- Max consecutive losses: 5

### Session Filtering
- London: 7-16 UTC
- New York: 12-21 UTC
- Tokyo: 0-9 UTC
- Overlaps preferred

## 📰 News Integration

### Economic Events
- High-impact events: ±30-120min blackout
- Sentiment analysis integration
- Impact scoring and filtering

### News Sources
- Economic calendar integration
- Real-time news feeds
- Sentiment scoring

## 🔧 Advanced Features

### Market Regime Detection
- Trending: ADX > 25, price range > 2%
- Volatile: ATR > 1.5% of price
- Ranging: Low volatility, sideways movement

### Dynamic Risk Management
- ATR-based stop losses
- Volatility-adjusted position sizing
- Regime-specific parameters

### AI Insights
- Entry suggestions
- Risk assessments
- Market analysis
- Technical insights

## 📊 Performance Metrics

### Primary Metrics
- Sharpe Ratio
- Sortino Ratio
- Maximum Drawdown
- Profit Factor
- Win Rate
- Total Trades

### Advanced Metrics
- Calmar Ratio
- Sterling Ratio
- Ulcer Index
- Tail Ratio
- Common Sense Ratio

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure all dependencies are installed
   pip install -r requirements.txt
   ```

2. **Data Issues**
   ```bash
   # Run data validation
   python data_pipeline_validator.py
   ```

3. **Memory Issues**
   - Reduce search space
   - Use fewer timeframes
   - Limit currency pairs

4. **Performance Issues**
   - Use fewer Monte Carlo trials
   - Reduce walk-forward periods
   - Limit parameter combinations

### Log Files
- `controller.log`: Main execution log
- `failures.log`: Failed experiments
- `data_validation_report_*.md`: Data quality reports

## 📚 Strategy Details

### Comprehensive Enhanced Strategy
- **Features**: News + indicators + technical analysis
- **Weights**: News 30%, Indicators 40%, Technical 30%
- **Min RR**: 2:1
- **Min Confidence**: 70%

### Ultra-Strict V3 Strategy
- **Features**: AI insights, ultra-strict criteria
- **Min RR**: 3:1
- **Min Confidence**: 85%
- **Max Daily Trades**: 2 per pair

### News Enhanced Strategy
- **Features**: News integration, sentiment analysis
- **Min RR**: 2:1
- **Min Confidence**: 70%
- **News Impact**: Required

### Enhanced Optimized Strategy
- **Features**: Market regime detection, dynamic risk
- **Min RR**: 2:1
- **Min Confidence**: 60%
- **Session Filtering**: Yes

## 🎯 Best Practices

### Before Running
1. Ensure data quality > 90%
2. Validate all components
3. Set appropriate risk limits
4. Configure search space

### During Execution
1. Monitor log files
2. Check disk space
3. Monitor memory usage
4. Track progress

### After Completion
1. Review best configurations
2. Analyze failures
3. Validate holdout results
4. Document findings

## 📞 Support

For issues or questions:
1. Check log files
2. Review troubleshooting section
3. Validate data pipeline
4. Test individual components

## 🔄 Updates

The system is designed to be modular and extensible:
- Add new strategies in `strategies/`
- Extend search spaces in `experiments.yaml`
- Add new validation methods
- Integrate additional data sources

---

**Remember**: This system is designed for institutional-grade strategy discovery. Always validate results thoroughly before live trading.
