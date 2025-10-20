# Desktop Backtesting Data Export
Generated: 2025-09-23 23:23:35
Data Period: 2025-08-24 to 2025-09-23
Instruments: EUR_USD, GBP_USD, USD_JPY, XAU_USD

## Data Files
- EUR_USD.csv - Price data with realistic spreads and slippage estimates
- GBP_USD.csv - Price data with realistic spreads and slippage estimates
- USD_JPY.csv - Price data with realistic spreads and slippage estimates
- XAU_USD.csv - Price data with realistic spreads and slippage estimates
- desktop_config.yaml - Configuration for backtesting parameters
- bloomberg_mapping.json - Bloomberg ticker mapping for validation

## Validation Instructions

### Basic Backtesting
1. Import the CSV files into your desktop backtesting software
2. Configure spread and slippage parameters from desktop_config.yaml
3. Run backtests with your strategy

### Bloomberg Data Validation
1. Use the provided mapping in bloomberg_mapping.json
2. Compare price data with Bloomberg terminal data
3. Validate spread patterns against market session times

### Performance Metrics
Calculate the following metrics to compare with the cloud-based system:
- Total return
- Max drawdown
- Sharpe ratio
- Win rate
- Profit factor

## Notes
- All data includes realistic spreads based on market sessions
- Slippage estimates are included based on volatility and volume
- For support, contact: fxgdesigns1@gmail.com
