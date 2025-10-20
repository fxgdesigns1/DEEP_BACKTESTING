#!/usr/bin/env python3
"""
SCENARIO RUNNER WITH LIVE PROGRESS
Shows results as they're discovered - saves checkpoints every 100 scenarios
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

# Import golden rule enforcer
from GOLDEN_RULE_NO_SYNTHETIC_DATA import RealDataEnforcer

enforcer = RealDataEnforcer()

# Export path
EXPORT_PATH = Path(r"H:\My Drive\AI Trading\exported strategies\optimization_20251002_195254")

def test_single_scenario(scenario):
    """Test one scenario with real data"""
    try:
        # Load REAL data
        df = enforcer.load_real_data(scenario['pair'], scenario['timeframe'])
        
        # Calculate indicators
        df['ema_fast'] = df['close'].ewm(span=scenario['ema_fast']).mean()
        df['ema_slow'] = df['close'].ewm(span=scenario['ema_slow']).mean()
        
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
        buy = (df['ema_fast'] > df['ema_slow']) & (df['ema_fast'].shift(1) <= df['ema_slow'].shift(1)) & (df['rsi'] < scenario['rsi_overbought'])
        sell = (df['ema_fast'] < df['ema_slow']) & (df['ema_fast'].shift(1) >= df['ema_slow'].shift(1)) & (df['rsi'] > scenario['rsi_oversold'])
        df.loc[buy, 'signal'] = 1
        df.loc[sell, 'signal'] = -1
        
        # Execute trades
        trades = []
        position = 0
        entry_price = 0
        entry_time = None
        sl = 0
        tp = 0
        
        for timestamp, row in df.iterrows():
            if pd.isna(row['atr']) or row['atr'] == 0:
                continue
            
            if row['signal'] == 1 and position == 0:
                position = 1
                entry_price = row['close']
                entry_time = timestamp
                sl = entry_price - (row['atr'] * scenario['sl_atr_mult'])
                tp = entry_price + (row['atr'] * scenario['sl_atr_mult'] * scenario['rr_ratio'])
                
            elif row['signal'] == -1 and position == 0:
                position = -1
                entry_price = row['close']
                entry_time = timestamp
                sl = entry_price + (row['atr'] * scenario['sl_atr_mult'])
                tp = entry_price - (row['atr'] * scenario['sl_atr_mult'] * scenario['rr_ratio'])
            
            elif position != 0:
                exit_reason = None
                exit_price = None
                
                if position == 1:
                    if row['low'] <= sl:
                        exit_reason = 'SL'
                        exit_price = sl
                    elif row['high'] >= tp:
                        exit_reason = 'TP'
                        exit_price = tp
                    elif row['signal'] == -1:
                        exit_reason = 'Signal'
                        exit_price = row['close']
                        
                elif position == -1:
                    if row['high'] >= sl:
                        exit_reason = 'SL'
                        exit_price = sl
                    elif row['low'] <= tp:
                        exit_reason = 'TP'
                        exit_price = tp
                    elif row['signal'] == 1:
                        exit_reason = 'Signal'
                        exit_price = row['close']
                
                if exit_reason:
                    pnl = (exit_price - entry_price) * position
                    pnl_pct = (pnl / entry_price) * 100
                    
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': timestamp,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'exit_reason': exit_reason
                    })
                    position = 0
        
        if not trades:
            return None
        
        trades_df = pd.DataFrame(trades)
        wins = trades_df[trades_df['pnl'] > 0]
        losses = trades_df[trades_df['pnl'] < 0]
        
        win_rate = (len(wins) / len(trades_df)) * 100
        total_return = trades_df['pnl_pct'].sum()
        
        cumulative = trades_df['pnl_pct'].cumsum()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max)
        max_dd = abs(drawdown.min()) if len(drawdown) > 0 else 0
        
        if len(trades_df) > 1 and trades_df['pnl_pct'].std() > 0:
            sharpe = (trades_df['pnl_pct'].mean() / trades_df['pnl_pct'].std()) * np.sqrt(len(trades_df))
        else:
            sharpe = 0
        
        total_profit = wins['pnl'].sum() if len(wins) > 0 else 0
        total_loss = abs(losses['pnl'].sum()) if len(losses) > 0 else 0
        profit_factor = (total_profit / total_loss) if total_loss > 0 else 0
        
        days = (df.index[-1] - df.index[0]).days
        years = days / 365.25
        annual_return = (total_return / years) if years > 0 else 0
        
        # Check if meets criteria (Win >= 65%, DD <= 10%)
        if win_rate >= 65.0 and max_dd <= 10.0 and sharpe >= 2.0:
            return {
                'scenario': scenario,
                'total_trades': len(trades_df),
                'win_rate': win_rate,
                'sharpe': sharpe,
                'annual_return': annual_return,
                'max_dd': max_dd,
                'profit_factor': profit_factor,
                'avg_win': wins['pnl_pct'].mean() if len(wins) > 0 else 0,
                'avg_loss': losses['pnl_pct'].mean() if len(losses) > 0 else 0
            }
        
        return None
        
    except Exception as e:
        return None

def main():
    """Main scenario runner"""
    
    print("\n" + "=" * 100)
    print(" " * 30 + "COMPREHENSIVE SCENARIO TESTING - REAL DATA ONLY")
    print("=" * 100)
    
    # Generate scenarios
    print("\n[GENERATING] Test scenarios...")
    
    scenarios = []
    scenario_id = 0
    
    pairs = ['gbp_usd', 'eur_usd', 'xau_usd', 'aud_usd']
    timeframes = ['5m', '15m', '30m', '1h']
    
    for pair in pairs:
        for tf in timeframes:
            for ema_fast in [3, 5, 8, 12]:
                for ema_slow in [12, 21, 34, 50]:
                    if ema_slow <= ema_fast:
                        continue
                    for rr in [1.5, 2.0, 2.5, 3.0, 4.0]:
                        for sl in [0.5, 1.0, 1.5, 2.0]:
                            for rsi_os in [20, 25, 30, 35]:
                                for rsi_ob in [65, 70, 75, 80]:
                                    if rsi_ob <= rsi_os:
                                        continue
                                    scenario_id += 1
                                    scenarios.append({
                                        'id': scenario_id,
                                        'pair': pair,
                                        'timeframe': tf,
                                        'ema_fast': ema_fast,
                                        'ema_slow': ema_slow,
                                        'rr_ratio': rr,
                                        'sl_atr_mult': sl,
                                        'rsi_oversold': rsi_os,
                                        'rsi_overbought': rsi_ob
                                    })
    
    print(f"[SUCCESS] Generated {len(scenarios):,} scenarios")
    print(f"  Pairs: {pairs}")
    print(f"  Timeframes: {timeframes}")
    print(f"  CPU Cores: {mp.cpu_count()}")
    print(f"\n[CRITERIA] Win Rate >= 65%, Max DD <= 10%, Sharpe >= 2.0")
    print(f"[START] Running optimization with live progress...\n")
    
    successful = []
    tested = 0
    start_time = datetime.now()
    
    # Run in parallel
    max_workers = min(16, mp.cpu_count())
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(test_single_scenario, s): s for s in scenarios}
        
        for future in as_completed(futures):
            tested += 1
            
            try:
                result = future.result()
                
                if result:
                    successful.append(result)
                    
                    # Print discovery
                    print(f"\n>>> SUCCESS #{len(successful)} <<<")
                    print(f"Scenario #{result['scenario']['id']}: {result['scenario']['pair'].upper()} {result['scenario']['timeframe']}")
                    print(f"  Sharpe: {result['sharpe']:.2f} | Win: {result['win_rate']:.1f}% | DD: {result['max_dd']:.1f}%")
                    print(f"  Return: {result['annual_return']:.1f}% | PF: {result['profit_factor']:.2f} | Trades: {result['total_trades']}")
                
                # Progress update every 100 scenarios
                if tested % 100 == 0:
                    elapsed = datetime.now() - start_time
                    pct = (tested / len(scenarios)) * 100
                    rate = tested / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
                    eta_seconds = (len(scenarios) - tested) / rate if rate > 0 else 0
                    eta = timedelta(seconds=int(eta_seconds))
                    
                    print(f"\n[PROGRESS] {tested:,}/{len(scenarios):,} ({pct:.1f}%)")
                    print(f"  Elapsed: {elapsed}")
                    print(f"  Rate: {rate:.1f} scenarios/sec")
                    print(f"  ETA: {eta}")
                    print(f"  Successful: {len(successful)}")
                    
                    # Save checkpoint
                    if successful:
                        checkpoint_file = EXPORT_PATH / f"checkpoint_{tested}.json"
                        with open(checkpoint_file, 'w') as f:
                            json.dump({
                                'tested': tested,
                                'total': len(scenarios),
                                'successful': successful
                            }, f, indent=2, default=str)
                
            except Exception as e:
                pass
    
    # Final report
    print(f"\n\n" + "=" * 100)
    print(" " * 35 + "OPTIMIZATION COMPLETE")
    print("=" * 100)
    print(f"\nTotal Scenarios: {len(scenarios):,}")
    print(f"Successful Strategies: {len(successful)}")
    print(f"Success Rate: {(len(successful)/len(scenarios)*100):.1f}%")
    
    if successful:
        successful.sort(key=lambda x: x['sharpe'], reverse=True)
        
        print(f"\n[TOP 10 BEST STRATEGIES]")
        print(f"{'Rank':<6} {'Pair':<10} {'TF':<6} {'Sharpe':<8} {'Return':<10} {'WinRate':<9} {'DD':<8} {'Trades':<8}")
        print("-" * 100)
        
        for i, s in enumerate(successful[:10], 1):
            sc = s['scenario']
            print(f"{i:<6} {sc['pair'].upper():<10} {sc['timeframe']:<6} {s['sharpe']:<8.2f} {s['annual_return']:<9.1f}% {s['win_rate']:<8.1f}% {s['max_dd']:<7.1f}% {s['total_trades']:<8,}")
        
        # Save final results
        final_file = EXPORT_PATH / "final_optimization_results.json"
        with open(final_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_tested': len(scenarios),
                'successful': len(successful),
                'strategies': successful
            }, f, indent=2, default=str)
        
        print(f"\n[SAVED] Final results: {final_file}")
    
    print("=" * 100 + "\n")

if __name__ == "__main__":
    # Enforce golden rule
    enforcer.prevent_synthetic_data_creation()
    main()


