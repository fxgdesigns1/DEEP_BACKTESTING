# 🎯 Deep Backtesting Environment

## Overview
This folder contains a complete backtesting environment for testing trading strategies on historical data. It includes all necessary components to run comprehensive strategy analysis on a more powerful machine.

## 📁 Directory Structure

```
deep_backtesting/
├── strategies/           # Strategy implementations
│   ├── ultra_strict_v3_strategy.py
│   ├── enhanced_optimized_strategy.py
│   └── live_optimized_strategies.py
├── data/                # Historical price data
│   └── historical/
│       ├── eur_usd_1h.csv
│       ├── gbp_usd_1h.csv
│       ├── usd_jpy_1h.csv
│       └── ... (10 pairs total)
├── scripts/             # Analysis and testing scripts
│   ├── ultimate_strategy_analysis.py
│   └── strategy_summary_table.py
├── results/             # Test results and reports
├── config/              # Configuration files
│   ├── config.yaml
│   └── settings.yaml
├── logs/                # Test logs
├── temp/                # Temporary files
├── exports/             # Exported results
├── reports/             # Generated reports
├── setup_environment.py # Environment setup script
├── run_deep_backtest.py # Main test runner
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Navigate to deep_backtesting folder
cd deep_backtesting

# Install dependencies
pip install -r requirements.txt

# Run setup script
python setup_environment.py
```

### 2. Run Deep Backtesting
```bash
# Run comprehensive analysis
python run_deep_backtest.py

# Or run individual scripts
python scripts/ultimate_strategy_analysis.py
python scripts/strategy_summary_table.py
```

## 📊 Available Strategies

### 1. Ultra-Strict V3 Strategy
- **File**: `strategies/ultra_strict_v3_strategy.py`
- **Features**:
  - Minimum 1:3 Risk-Reward ratio
  - 85%+ confidence requirement
  - Maximum 2 trades per day per pair
  - Major session only trading
  - AI insights and entry suggestions

### 2. Enhanced Optimized Strategy
- **File**: `strategies/enhanced_optimized_strategy.py`
- **Features**:
  - Market regime detection
  - Dynamic risk management
  - Session filtering
  - Advanced entry conditions

### 3. Live Optimized Strategy Manager
- **File**: `strategies/live_optimized_strategies.py`
- **Features**:
  - Real-time signal generation
  - Performance tracking
  - Multi-strategy management

## 📈 Available Data

### Historical Price Data (1H timeframe)
- **EUR_USD**: 15,001 candles
- **GBP_USD**: 15,001 candles
- **USD_JPY**: 15,001 candles
- **AUD_USD**: 15,001 candles
- **USD_CAD**: 15,001 candles
- **USD_CHF**: 15,001 candles
- **NZD_USD**: 15,001 candles
- **XAU_USD**: 15,001 candles
- **EUR_JPY**: 15,001 candles
- **GBP_JPY**: 15,001 candles

### Data Format
```csv
timestamp,open,high,low,close,volume
2024-01-01 00:00:00,1.12345,1.12367,1.12323,1.12345,1234
```

## 🔧 Adding New Pairs

### Step 1: Prepare Data
1. Download historical data for the new pair
2. Format as CSV with columns: `timestamp,open,high,low,close,volume`
3. Save as `data/historical/{pair_lowercase}_1h.csv`

### Step 2: Update Configuration
1. Add pair to `config/settings.yaml`:
```yaml
default_symbols:
  - EUR_USD
  - GBP_USD
  - YOUR_NEW_PAIR
```

### Step 3: Update Scripts
1. Add pair to analysis scripts in `scripts/`
2. Update pair lists in strategy files if needed

### Step 4: Test
```bash
python scripts/ultimate_strategy_analysis.py
```

## 📊 Running Different Types of Tests

### 1. Comprehensive Strategy Analysis
```bash
python scripts/ultimate_strategy_analysis.py
```
- Tests all strategies on all pairs
- Generates performance metrics
- Creates comparison tables

### 2. Strategy Summary Table
```bash
python scripts/strategy_summary_table.py
```
- Creates formatted summary tables
- Exports results to CSV/JSON

### 3. Individual Strategy Testing
```python
from strategies.ultra_strict_v3_strategy import UltraStrictV3Strategy
import pandas as pd

# Load data
data = pd.read_csv('data/historical/eur_usd_1h.csv')

# Initialize strategy
strategy = UltraStrictV3Strategy()

# Generate signals
signals = strategy.generate_signal(data, 'EUR_USD')
```

## 📈 Understanding Results

### Performance Metrics
- **Win Rate**: Percentage of winning trades
- **Profit Factor**: Total profit / Total loss
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Largest peak-to-trough decline
- **Total Trades**: Number of trades executed
- **Average RR**: Average risk-reward ratio

### Output Files
- **JSON Reports**: Detailed results in JSON format
- **CSV Exports**: Tabular data for analysis
- **Log Files**: Detailed execution logs
- **Charts**: Performance visualization (if matplotlib available)

## 🔍 Advanced Usage

### Custom Strategy Testing
```python
# Create custom strategy class
class CustomStrategy:
    def __init__(self):
        self.name = "Custom Strategy"
    
    def generate_signal(self, data, symbol):
        # Your strategy logic here
        pass

# Test custom strategy
from scripts.ultimate_strategy_analysis import test_strategy
results = test_strategy(CustomStrategy(), 'EUR_USD')
```

### Parameter Optimization
```python
# Test different parameters
parameters = [
    {'min_rr_ratio': 2.0, 'min_confidence': 80},
    {'min_rr_ratio': 3.0, 'min_confidence': 85},
    {'min_rr_ratio': 4.0, 'min_confidence': 90}
]

for params in parameters:
    strategy = UltraStrictV3Strategy()
    strategy.min_rr_ratio = params['min_rr_ratio']
    strategy.min_confidence = params['min_confidence']
    # Test strategy...
```

## 🛠️ Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Make sure you're in the deep_backtesting directory
   cd deep_backtesting
   python setup_environment.py
   ```

2. **Missing Data**
   ```bash
   # Check data files exist
   ls data/historical/
   ```

3. **Memory Issues**
   ```python
   # For large datasets, process in chunks
   chunk_size = 1000
   for chunk in pd.read_csv('data.csv', chunksize=chunk_size):
       # Process chunk
   ```

### Performance Optimization

1. **Use Vectorized Operations**
   ```python
   # Good: Vectorized
   data['sma'] = data['close'].rolling(20).mean()
   
   # Avoid: Loops
   for i in range(len(data)):
       data.loc[i, 'sma'] = data['close'][:i+1].mean()
   ```

2. **Parallel Processing**
   ```python
   from multiprocessing import Pool
   
   def test_pair(pair):
       # Test strategy on single pair
       pass
   
   with Pool() as pool:
       results = pool.map(test_pair, pairs)
   ```

## 📞 Support

For issues or questions:
1. Check the logs in `logs/` directory
2. Review `environment_info.json` for system details
3. Ensure all dependencies are installed: `pip install -r requirements.txt`

## 🎯 Next Steps

1. **Run Initial Tests**: Execute `python run_deep_backtest.py`
2. **Review Results**: Check `results/` directory for outputs
3. **Customize Strategies**: Modify strategy parameters in `strategies/`
4. **Add New Data**: Follow the "Adding New Pairs" guide
5. **Scale Up**: Use more powerful machine for larger datasets

---

**Happy Backtesting! 🚀**
