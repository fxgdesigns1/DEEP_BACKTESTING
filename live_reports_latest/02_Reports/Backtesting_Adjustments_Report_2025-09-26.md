# Backtesting Adjustments Report — 2025-09-26

## What we learned
- Overtrading was the core failure mode; fixed via EMA(3/8/21) + momentum gate and min signal strength.
- Realistic costs matter: dynamic spreads by session/instrument + probabilistic slippage improved P&L fidelity to within ~5–10% of live.
- Validation must compare live vs backtest across win rate, returns, drawdown, and frequency; alerts when drift exceeds tolerances.
- Strategy caps and portfolio limits reduce variance without suppressing edge.

## Required adjustments to the desktop backtesting system
- Enable cost modeling:
  - include_slippage: true; include_spread: true; include_commission: true
  - Use `spread_modeling.session_factors` and `instrument_factors` from config
- Enforce trade discipline:
  - EMA(3/8/21) crossover with momentum confirmation
  - min_signal_strength >= 0.35; max_trades_per_day: 50 (scalping), 25 (ultra_strict)
- Use parameter optimization but constrain ranges to realistic bands
- Add validation workflow:
  - Compare live vs backtest: win_rate, return, drawdown, frequency (daily/weekly/monthly)
  - Fail-fast if drift > tolerances in config
- Data hygiene:
  - Use exported OANDA spreads and timestamps; align timezone; no forward-looking fields

## Concrete changes to make
- Backtester engine
  - Apply dynamic spread at order construction time; add slippage sampled by volatility and session
  - Commission-aware P&L; store per-trade cost breakdown
- Signal engine
  - Implement EMA(3,8,21) with momentum period=10 filter
  - Gate entries by min_signal_strength and max open positions = 5; portfolio exposure cap = 10%
- Optimization
  - Default to grid_search resolution=medium; consider bayesian for fine-tune
- Reporting
  - Export CSV + JSON; include validation.json with drift metrics and flags

## Expected impact
- Fewer but higher-quality signals, improved live alignment, and more stable equity curve.

