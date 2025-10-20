# Input Data Specification (CSV)

Required columns per instrument CSV placed in `backtesting_data/`:
- timestamp (ISO 8601, UTC)
- open, high, low, close (float)
- volume (int or float)
- bid, ask (optional; if absent, spread modeled)

Constraints:
- No missing timestamps within chosen timeframe; if gaps, system must handle
- No forward-looking fields; data ordered by timestamp ascending
