# Gold Scalping Backtesting Report (Corrected System)
Date: 2025-09-23 23:55:02

## Summary of Performance

| Strategy | Signals | Trades | Return (%) | Win Rate (%) | Profit Factor | Max DD (%) | Sharpe |
|----------|---------|--------|------------|--------------|--------------|------------|--------|
| rsi | 1033 | 37 | -7.39% | 32.43% | 0.71 | 8.82% | -2.50 |
| macd | 1543 | 28 | -8.07% | 28.57% | 0.60 | 8.33% | -3.97 |
| bollinger | 285 | 33 | -8.62% | 33.33% | 0.63 | 11.47% | -3.56 |

## Detailed Performance Metrics

### rsi Strategy

- Total Signals Generated: 1033
- Total Trades Executed: 37
- Total Return: -7.39%
- Win Rate: 32.43%
- Profit Factor: 0.71
- Maximum Drawdown: 8.82%
- Sharpe Ratio: -2.50
- Average Trade: $-19.96
- Average Win: $153.22
- Average Loss: $-103.09
- Maximum Win: $157.79
- Maximum Loss: $-113.40
- Total P&L: $-738.56

#### Sample Trades

| Entry Time | Exit Time | Direction | Entry | Exit | P&L | Reason | Exit Type |
|------------|-----------|-----------|-------|------|-----|--------|----------|
| 2025-01-01 22:00 | 2025-01-03 15:00 | BUY | 1798.94 | 1793.88 | $-104.88 | RSI oversold | stop_loss |
| 2025-01-04 01:00 | 2025-01-14 09:00 | SELL | 1797.00 | 1802.27 | $-107.83 | RSI overbought | stop_loss |
| 2025-01-14 09:00 | 2025-01-18 17:00 | SELL | 1802.27 | 1807.43 | $-104.54 | RSI overbought | stop_loss |
| 2025-01-18 18:00 | 2025-01-22 21:00 | SELL | 1806.95 | 1798.94 | $151.51 | RSI overbought | take_profit |
| 2025-01-22 23:00 | 2025-02-01 06:00 | BUY | 1798.15 | 1792.83 | $-108.19 | RSI oversold | stop_loss |

### macd Strategy

- Total Signals Generated: 1543
- Total Trades Executed: 28
- Total Return: -8.07%
- Win Rate: 28.57%
- Profit Factor: 0.60
- Maximum Drawdown: 8.33%
- Sharpe Ratio: -3.97
- Average Trade: $-28.84
- Average Win: $148.79
- Average Loss: $-99.89
- Maximum Win: $156.90
- Maximum Loss: $-118.61
- Total P&L: $-807.42

#### Sample Trades

| Entry Time | Exit Time | Direction | Entry | Exit | P&L | Reason | Exit Type |
|------------|-----------|-----------|-------|------|-----|--------|----------|
| 2025-01-01 22:00 | 2025-01-16 18:00 | SELL | 1798.94 | 1805.18 | $-106.95 | MACD bearish crossover | stop_loss |
| 2025-01-16 18:00 | 2025-01-22 21:00 | BUY | 1805.18 | 1798.94 | $-105.80 | MACD bullish crossover | stop_loss |
| 2025-01-22 23:00 | 2025-02-06 21:00 | SELL | 1798.15 | 1804.33 | $-103.71 | MACD bearish crossover | stop_loss |
| 2025-02-06 21:00 | 2025-02-10 07:00 | BUY | 1804.33 | 1813.79 | $149.83 | MACD bullish crossover | take_profit |
| 2025-02-10 08:00 | 2025-02-17 04:00 | BUY | 1813.77 | 1823.13 | $150.44 | MACD bullish crossover | take_profit |

### bollinger Strategy

- Total Signals Generated: 285
- Total Trades Executed: 33
- Total Return: -8.62%
- Win Rate: 33.33%
- Profit Factor: 0.63
- Maximum Drawdown: 11.47%
- Sharpe Ratio: -3.56
- Average Trade: $-26.13
- Average Win: $131.75
- Average Loss: $-105.07
- Maximum Win: $151.32
- Maximum Loss: $-116.24
- Total P&L: $-862.26

#### Sample Trades

| Entry Time | Exit Time | Direction | Entry | Exit | P&L | Reason | Exit Type |
|------------|-----------|-----------|-------|------|-----|--------|----------|
| 2025-01-02 13:00 | 2025-01-16 14:00 | BUY | 1796.19 | 1803.94 | $151.32 | BB lower band bounce | take_profit |
| 2025-01-16 15:00 | 2025-01-23 08:00 | SELL | 1803.55 | 1795.95 | $150.80 | BB upper band rejection | take_profit |
| 2025-01-24 09:00 | 2025-02-06 05:00 | SELL | 1796.59 | 1802.01 | $-115.38 | BB upper band rejection | stop_loss |
| 2025-02-06 16:00 | 2025-02-07 07:00 | SELL | 1803.05 | 1808.09 | $-106.27 | BB upper band rejection | stop_loss |
| 2025-02-08 19:00 | 2025-02-13 17:00 | SELL | 1812.26 | 1817.84 | $-116.24 | BB upper band rejection | stop_loss |

## System Corrections

The following fundamental errors were corrected in this backtesting system:

1. **Gold Pip Value**: Corrected gold pip definition from 0.0001 to $0.10
2. **Position Sizing**: Fixed position size calculation for gold's unique characteristics
3. **Stop Loss/Take Profit**: Implemented realistic values (50-100 pips)
4. **Trade Simulation**: Used actual price data instead of random probabilities
5. **Risk Management**: Capped position sizes to 5% of account balance

## Conclusion

This corrected backtesting system addresses the fundamental flaws in the previous implementation, resulting in more realistic and reliable performance metrics. The results now reflect proper risk management and trade simulation methods specific to gold trading.
