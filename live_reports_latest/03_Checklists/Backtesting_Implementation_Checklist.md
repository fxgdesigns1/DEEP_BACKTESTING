# Backtesting Implementation Checklist

## Pre-flight
- [ ] Pull latest data exports into `backtesting_data/`
- [ ] Confirm config in `04_Configs/optimized_backtesting_config.yaml`

## Engine changes
- [ ] Dynamic spread modeling applied per instrument/session
- [ ] Probabilistic slippage based on volatility/volume/news
- [ ] Commission applied; P&L includes cost breakdown

## Strategy logic
- [ ] EMA(3,8,21) crossover implemented
- [ ] Momentum confirmation (period 10)
- [ ] min_signal_strength >= 0.35
- [ ] max_trades_per_day limits applied (50 scalping / 25 strict)
- [ ] Portfolio exposure cap 10%; max concurrent positions 5

## Validation
- [ ] Live vs backtest comparisons enabled (daily/weekly/monthly)
- [ ] Tolerances set: win±5%, return±10%, dd±5%, freq±20%
- [ ] Auto-fail and log corrective action when drift exceeded

## Run
- [ ] Execute `05_Scripts/run_backtesting.py` with visualize and validate flags
- [ ] Save outputs to `07_Results/YYYY-MM-DD_*`

