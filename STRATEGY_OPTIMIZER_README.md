# Strategy Optimizer: Broad to Narrow Search

## Overview

The Strategy Optimizer uses a two-phase approach to systematically discover optimal trading strategies without modifying the core backtesting engine.

**Approach**: Start broad → Filter survivors → Refine parameters

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              ImprovedBacktestingSystem                   │
│                 (Unchanged Core)                         │
└─────────────────────────────────────────────────────────┘
                         ▲
                         │
┌────────────────────────┴─────────────────────────────────┐
│            Strategy Optimizer (New Layer)                │
│  ┌─────────────┐              ┌──────────────┐          │
│  │  Phase 1    │ ─Survivors→  │   Phase 2    │          │
│  │  Broad      │              │  Refinement  │          │
│  │  Exploration│              │              │          │
│  └─────────────┘              └──────────────┘          │
└──────────────────────────────────────────────────────────┘
```

## Files

### 1. `strategy_optimizer_broad_to_narrow.py`
**Full optimization pipeline**

- **Phase 1**: Tests all strategies × all instruments × all timeframes
- **Phase 2**: Refines parameter variations on survivors
- **Output**: Top 10 optimized strategies with parameters

### 2. `strategy_optimizer_quick_test.py`
**Quick verification**

- Tests 2 strategies on 2 pairs on 1 timeframe
- Verifies system works before full run
- ~2-5 minutes runtime

## Usage

### Quick Test First
```bash
python strategy_optimizer_quick_test.py
```

Expected output:
```
Testing: ultra_strict_forex | EUR_USD | 15m
✅ Results:
   Sharpe: 2.34
   Return: 45.67%
   Win Rate: 58.5%
   Trades: 152

Testing: gold_scalping | XAU_USD | 15m
✅ Results:
   Sharpe: 1.89
   Return: 32.10%
   Win Rate: 52.3%
   Trades: 287
```

### Full Optimization
```bash
python strategy_optimizer_broad_to_narrow.py
```

**Runtime**: ~2-4 hours (depending on data size)

## Phase 1: Broad Exploration

### What It Does
- Tests **3 strategies** × **10 instruments** × **4 timeframes** = **120 combinations**
- Filters using minimum criteria
- Identifies promising combinations

### Filter Criteria
```yaml
sharpe_ratio: ≥ 1.5
max_drawdown: ≤ 20%
win_rate: ≥ 45%
profit_factor: ≥ 1.2
min_trades: ≥ 10
```

### Survivors
Only combinations meeting ALL criteria advance to Phase 2.

**Example Output**:
```
✔ SURVIVOR: ultra_strict_forex | EUR_USD | 1h
   Sharpe 2.1 | Win Rate 56.2% | Drawdown 8.5%

✔ SURVIVOR: gold_scalping | XAU_USD | 15m
   Sharpe 1.8 | Win Rate 52.0% | Drawdown 12.3%
```

## Phase 2: Refinement

### What It Does
- Takes each survivor from Phase 1
- Tests parameter variations:
  - **Risk per trade**: [1%, 1.5%, 2%, 2.5%]
  - **Signal quality**: [50, 60, 70, 75]
  - **Time spacing**: [15, 30, 45, 60 minutes]
- Total: **64 variations per survivor**

### Filter Criteria (Stricter)
```yaml
sharpe_ratio: ≥ 2.0
max_drawdown: ≤ 10%
win_rate: ≥ 55%
profit_factor: ≥ 2.0
min_trades: ≥ 20
```

### Optimized Strategies
Only best parameter combinations are kept.

**Example Output**:
```
🔥 REFINED: ultra_strict_forex | EUR_USD | 1h
   Sharpe 2.45 | Win Rate 58.3%
   Parameters: Risk 1.5% | Quality 70 | Spacing 30m
```

## Results Files

All results saved to `results/` directory:

### Phase 1 Survivors
```
results/phase1_survivors_20251001_143022.json
```

```json
[
  {
    "strategy": "ultra_strict_forex",
    "pair": "eur_usd",
    "timeframe": "1h",
    "sharpe_ratio": 2.1,
    "max_drawdown_pct": 8.5,
    "win_rate": 56.2,
    "profit_factor": 2.3,
    "total_return_pct": 48.5,
    "total_trades": 156
  }
]
```

### Phase 2 Optimized
```
results/phase2_optimized_20251001_183045.json
```

```json
[
  {
    "strategy": "ultra_strict_forex",
    "pair": "eur_usd",
    "timeframe": "1h",
    "parameters": {
      "risk_per_trade": 0.015,
      "min_signal_quality": 70,
      "min_time_between_trades": 30
    },
    "metrics": {
      "sharpe_ratio": 2.45,
      "max_drawdown_pct": 7.2,
      "win_rate": 58.3,
      "profit_factor": 2.8,
      "total_return_pct": 52.7,
      "total_trades": 143
    }
  }
]
```

### Top 10 Strategies
```
results/top_10_strategies_20251001_183045.json
```

Sorted by Sharpe ratio, includes:
- Strategy details
- Instrument & timeframe
- Optimized parameters
- All metrics

## Strategy Details

### Ultra Strict Forex
- **Type**: Trend following with EMA crossover
- **Best For**: Major forex pairs (EUR/USD, GBP/USD)
- **Timeframes**: 1h, 4h
- **Key**: Requires HTF alignment + momentum confirmation

### Gold Scalping
- **Type**: Pullback scalper
- **Best For**: XAU/USD only
- **Timeframes**: 15m
- **Key**: Impulse detection + pullback entry

### Momentum Trading
- **Type**: ADX/ATR momentum
- **Best For**: JPY pairs (EUR/JPY, GBP/JPY)
- **Timeframes**: 1h, 4h
- **Key**: Strong trending markets

## Interpreting Results

### Excellent Strategy
```
Sharpe Ratio: > 2.5
Win Rate: > 60%
Max Drawdown: < 8%
Profit Factor: > 3.0
```

### Good Strategy
```
Sharpe Ratio: 2.0 - 2.5
Win Rate: 55-60%
Max Drawdown: 8-10%
Profit Factor: 2.0 - 3.0
```

### Acceptable Strategy
```
Sharpe Ratio: 1.5 - 2.0
Win Rate: 50-55%
Max Drawdown: 10-15%
Profit Factor: 1.5 - 2.0
```

## Customization

### Adjust Phase 1 Filters
Edit in `strategy_optimizer_broad_to_narrow.py`:

```python
PHASE1_FILTERS = {
    "sharpe_ratio": 1.5,      # Lower = more survivors
    "max_drawdown_pct": 20.0, # Higher = more survivors
    "win_rate": 45.0,         # Lower = more survivors
    "min_trades": 10,
    "profit_factor": 1.2
}
```

### Adjust Phase 2 Filters
```python
PHASE2_FILTERS = {
    "sharpe_ratio": 2.0,      # Higher = fewer results
    "max_drawdown_pct": 10.0, # Lower = fewer results
    "win_rate": 55.0,         # Higher = fewer results
    "profit_factor": 2.0,
    "min_trades": 20
}
```

### Add Parameter Variations
In `run_phase2()` method:

```python
variations = {
    'risk_per_trade': [0.01, 0.015, 0.02, 0.025],
    'min_signal_quality': [50, 60, 70, 75],
    'min_time_between_trades': [15, 30, 45, 60]
    # Add more parameters here
}
```

## Advantages

1. **No Engine Changes**: Works with existing backtesting system
2. **Systematic**: Tests all combinations objectively
3. **Two-Phase**: Efficient broad search → focused refinement
4. **Reproducible**: All results logged and saved
5. **Flexible**: Easy to adjust filters and parameters

## Limitations

1. **Overfitting Risk**: More parameters = higher overfitting risk
2. **Data Dependency**: Results depend on historical data quality
3. **Runtime**: Full optimization takes 2-4 hours
4. **Look-Ahead Bias**: Ensure data doesn't contain future information

## Best Practices

1. **Always run quick test first** to verify system works
2. **Use walk-forward validation** on optimized strategies
3. **Test on out-of-sample data** before live deployment
4. **Monitor drift** between backtest and live performance
5. **Re-optimize quarterly** as market conditions change

## Next Steps

After optimization:

1. **Review Top 10**: Examine the top strategies
2. **Walk-Forward Test**: Validate on unseen data
3. **Paper Trade**: Test in demo account
4. **Live Deploy**: Deploy with small position sizes
5. **Monitor**: Track performance vs backtest

## Troubleshooting

### No Phase 1 Survivors
- **Problem**: Filters too strict
- **Solution**: Lower Phase 1 filter thresholds

### Too Many Phase 2 Results
- **Problem**: Phase 2 filters too loose
- **Solution**: Raise Phase 2 filter thresholds

### File Not Found Errors
- **Problem**: Data files missing
- **Solution**: Check `data/MASTER_DATASET/` structure matches:
  ```
  data/MASTER_DATASET/
    15m/eur_usd_15m.csv
    1h/eur_usd_1h.csv
    4h/eur_usd_4h.csv
    1d/eur_usd_1d.csv
  ```

### Slow Runtime
- **Problem**: Too many combinations
- **Solution**: Reduce instruments or timeframes in Phase 1

## Support

For issues or questions:
1. Check logs in `strategy_optimizer.log`
2. Review `TROUBLESHOOTING_GUIDE.md`
3. Verify data quality with `data_validation_script.py`

---

**Version**: 1.0  
**Date**: October 1, 2025  
**Compatible With**: ImprovedBacktestingSystem v2.1.0




