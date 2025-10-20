#!/usr/bin/env python3
"""Quick test of all pairs using GBP_USD's winning parameters"""

import pandas as pd
import numpy as np
from pathlib import Path
from GOLDEN_RULE_NO_SYNTHETIC_DATA import RealDataEnforcer

enforcer = RealDataEnforcer()

# GBP_USD's winning parameters
WINNING_PARAMS = {
    'ema_fast': 3,
    'ema_slow': 12,
    'rsi_oversold': 20,
    'rsi_overbought': 80,
    'sl_atr_mult': 1.5,
    'rr_ratio': 3.0
}

def test_pair(pair):
    """Test one pair with winning parameters"""
    
    print(f"\n{'='*80}")
    print(f"Testing {pair.upper()} with GBP_USD's winning parameters")
    print(f"{'='*80}")
    
    try:
        # Load real data
        df = enforcer.load_real_data(pair, '5m')
        
        # Calculate indicators
        df['ema_fast'] = df['close'].ewm(span=WINNING_PARAMS['ema_fast']).mean()
        df['ema_slow'] = df['close'].ewm(span=WINNING_PARAMS['ema_slow']).mean()
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['atr'] = true_range.rolling(window=14).mean()
        
        # Generate signals
        df['signal'] = 0
        buy = (df['ema_fast'] > df['ema_slow']) & (df['ema_fast'].shift(1) <= df['ema_slow'].shift(1)) & (df['rsi'] < WINNING_PARAMS['rsi_overbought'])
        sell = (df['ema_fast'] < df['ema_slow']) & (df['ema_fast'].shift(1) >= df['ema_slow'].shift(1)) & (df['rsi'] > WINNING_PARAMS['rsi_oversold'])
        df.loc[buy, 'signal'] = 1
        df.loc[sell, 'signal'] = -1
        
        # Execute trades
        trades = []
        position = 0
        
        for timestamp, row in df.iterrows():
            if pd.isna(row['atr']) or row['atr'] == 0:
                continue
            
            if row['signal'] == 1 and position == 0:
                position = 1
                entry_price = row['close']
                entry_time = timestamp
                sl = entry_price - (row['atr'] * WINNING_PARAMS['sl_atr_mult'])
                tp = entry_price + (row['atr'] * WINNING_PARAMS['sl_atr_mult'] * WINNING_PARAMS['rr_ratio'])
                
            elif row['signal'] == -1 and position == 0:
                position = -1
                entry_price = row['close']
                entry_time = timestamp
                sl = entry_price + (row['atr'] * WINNING_PARAMS['sl_atr_mult'])
                tp = entry_price - (row['atr'] * WINNING_PARAMS['sl_atr_mult'] * WINNING_PARAMS['rr_ratio'])
            
            elif position != 0:
                exit_price = None
                
                if position == 1:
                    if row['low'] <= sl:
                        exit_price = sl
                    elif row['high'] >= tp:
                        exit_price = tp
                    elif row['signal'] == -1:
                        exit_price = row['close']
                        
                elif position == -1:
                    if row['high'] >= sl:
                        exit_price = sl
                    elif row['low'] <= tp:
                        exit_price = tp
                    elif row['signal'] == 1:
                        exit_price = row['close']
                
                if exit_price:
                    pnl_pct = ((exit_price - entry_price) / entry_price * 100) * position
                    trades.append({'pnl_pct': pnl_pct})
                    position = 0
        
        # Calculate metrics
        if not trades:
            print(f"[RESULT] {pair.upper()}: NO TRADES GENERATED")
            return None
        
        trades_df = pd.DataFrame(trades)
        wins = trades_df[trades_df['pnl_pct'] > 0]
        losses = trades_df[trades_df['pnl_pct'] < 0]
        
        win_rate = (len(wins) / len(trades_df)) * 100
        
        cumulative = trades_df['pnl_pct'].cumsum()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max)
        max_dd = abs(drawdown.min())
        
        sharpe = (trades_df['pnl_pct'].mean() / trades_df['pnl_pct'].std()) * np.sqrt(len(trades_df)) if len(trades_df) > 1 else 0
        
        total_profit = wins['pnl_pct'].sum() if len(wins) > 0 else 0
        total_loss = abs(losses['pnl_pct'].sum()) if len(losses) > 0 else 0
        profit_factor = (total_profit / total_loss) if total_loss > 0 else 0
        
        days = (df.index[-1] - df.index[0]).days
        annual_return = (trades_df['pnl_pct'].sum() / (days/365.25))
        
        # Print results
        print(f"\n[RESULTS] {pair.upper()}")
        print(f"  Total Trades: {len(trades_df):,}")
        print(f"  Win Rate: {win_rate:.1f}%")
        print(f"  Sharpe Ratio: {sharpe:.2f}")
        print(f"  Annual Return: {annual_return:.1f}%")
        print(f"  Max Drawdown: {max_dd:.1f}%")
        print(f"  Profit Factor: {profit_factor:.2f}")
        
        # Check criteria
        meets_criteria = win_rate >= 65.0 and max_dd <= 10.0 and sharpe >= 2.0
        print(f"  Meets Criteria (Win>=65%, DD<=10%, Sharpe>=2.0): {'YES' if meets_criteria else 'NO'}")
        
        if meets_criteria:
            print(f"  >>> EXCELLENT STRATEGY! <<<")
        
        return {
            'pair': pair,
            'trades': len(trades_df),
            'win_rate': win_rate,
            'sharpe': sharpe,
            'annual_return': annual_return,
            'max_dd': max_dd,
            'profit_factor': profit_factor,
            'meets_criteria': meets_criteria
        }
        
    except Exception as e:
        print(f"[ERROR] {pair.upper()}: {e}")
        return None

# Test all pairs
print("\n" + "="*80)
print("TESTING ALL PAIRS WITH GBP_USD'S WINNING PARAMETERS")
print("="*80)
print(f"\nParameters: EMA {WINNING_PARAMS['ema_fast']}/{WINNING_PARAMS['ema_slow']}, "
      f"RSI {WINNING_PARAMS['rsi_oversold']}/{WINNING_PARAMS['rsi_overbought']}, "
      f"SL {WINNING_PARAMS['sl_atr_mult']}x ATR, R:R 1:{WINNING_PARAMS['rr_ratio']}")

results = []
for pair in ['gbp_usd', 'eur_usd', 'xau_usd', 'aud_usd']:
    result = test_pair(pair)
    if result:
        results.append(result)

# Summary
print(f"\n\n{'='*80}")
print("SUMMARY - ALL PAIRS TESTED")
print(f"{'='*80}\n")
print(f"{'Pair':<10} {'Trades':<8} {'Win%':<8} {'Sharpe':<8} {'Return%':<10} {'MaxDD%':<8} {'PF':<8} {'Criteria'}")
print("-"*80)

for r in results:
    criteria = "YES" if r['meets_criteria'] else "NO"
    print(f"{r['pair'].upper():<10} {r['trades']:<8,} {r['win_rate']:<8.1f} {r['sharpe']:<8.2f} {r['annual_return']:<10.1f} {r['max_dd']:<8.1f} {r['profit_factor']:<8.2f} {criteria}")

print(f"\n{'='*80}\n")


