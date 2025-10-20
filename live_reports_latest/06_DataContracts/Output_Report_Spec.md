# Output Report Specification

Artifacts per run in `07_Results/YYYY-MM-DD_<run_id>/`:
- performance.json — metrics listed in config.performance_metrics
- trades.csv — per-trade details incl. costs (spread, slippage, commission)
- equity_curve.csv — timestamp, equity
- validation.json — live vs backtest drift metrics and pass/fail
- charts/ — PNGs for equity, drawdown, distribution
