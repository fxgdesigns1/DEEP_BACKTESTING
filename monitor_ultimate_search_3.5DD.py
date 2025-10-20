#!/usr/bin/env python3
"""
LIVE MONITOR - Ultimate Search with 3.5% DD Limit
Shows best strategies as they're discovered
"""

import json
import time
from pathlib import Path
from datetime import datetime

def monitor_search():
    """Monitor and display results with 3.5% DD criteria"""
    
    export_path = Path(r"H:\My Drive\AI Trading\exported strategies")
    
    last_count = 0
    iteration = 0
    
    print("\n" + "="*100)
    print(" "*25 + "ULTIMATE STRATEGY SEARCH - LIVE MONITOR")
    print(" "*30 + "Max Drawdown: 3.5% (Updated)")
    print("="*100)
    print("\nRefreshing every 30 seconds... Press Ctrl+C to stop\n")
    
    try:
        while True:
            iteration += 1
            
            # Find latest checkpoint
            checkpoints = list(export_path.rglob("checkpoint_*.json"))
            
            if not checkpoints:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for results...")
                time.sleep(30)
                continue
            
            latest = max(checkpoints, key=lambda p: p.stat().st_mtime)
            
            with open(latest, 'r') as f:
                data = json.load(f)
            
            # Filter with NEW 3.5% DD criteria
            filtered = []
            for s in data['successful']:
                if s['win_rate'] >= 65.0 and s['max_dd'] <= 3.5 and s['sharpe'] >= 2.0:
                    filtered.append(s)
            
            # Only update if new strategies found
            if len(filtered) > last_count:
                os.system('cls' if os.name == 'nt' else 'clear')
                
                print("\n" + "="*100)
                print(" "*25 + "ULTIMATE STRATEGY SEARCH - LIVE UPDATE")
                print("="*100)
                print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
                print(f"Progress: {data['tested']:,}/2,970 ({data['tested']/2970*100:.1f}%)")
                print(f"Strategies Found (DD <= 3.5%): {len(filtered)}")
                print(f"NEW since last update: {len(filtered) - last_count}")
                print("="*100)
                
                # Sort and show top 5
                by_sharpe = sorted(filtered, key=lambda x: x['sharpe'], reverse=True)[:5]
                by_return = sorted(filtered, key=lambda x: x['annual_return'], reverse=True)[:5]
                
                print("\n[TOP 5 BY SHARPE - Best Risk-Adjusted]")
                print(f"{'Rank':<6} {'Pair':<10} {'TF':<6} {'Sharpe':<8} {'Return':<10} {'Win%':<8} {'DD%':<8}")
                print("-"*80)
                for i, s in enumerate(by_sharpe, 1):
                    sc = s['scenario']
                    print(f"{i:<6} {sc['pair'].upper():<10} {sc['timeframe']:<6} {s['sharpe']:<8.2f} "
                          f"{s['annual_return']:<9.1f}% {s['win_rate']:<7.1f}% {s['max_dd']:<7.1f}%")
                
                print("\n[TOP 5 BY ANNUAL RETURN - Highest Profits]")
                print(f"{'Rank':<6} {'Pair':<10} {'TF':<6} {'Return':<10} {'Sharpe':<8} {'Win%':<8} {'DD%':<8}")
                print("-"*80)
                for i, s in enumerate(by_return, 1):
                    sc = s['scenario']
                    print(f"{i:<6} {sc['pair'].upper():<10} {sc['timeframe']:<6} {s['annual_return']:<9.1f}% "
                          f"{s['sharpe']:<8.2f} {s['win_rate']:<7.1f}% {s['max_dd']:<7.1f}%")
                
                # Show THE BEST
                best = by_sharpe[0]
                print("\n" + "="*100)
                print(">>> CURRENT ULTIMATE CHAMPION <<<")
                print("="*100)
                sc = best['scenario']
                print(f"Pair: {sc['pair'].upper()} | Timeframe: {sc['timeframe']}")
                print(f"EMA: {sc['ema_fast']}/{sc['ema_slow']} | R:R: 1:{sc['rr_ratio']} | SL: {sc['sl_atr_mult']}x ATR")
                print(f"\nSharpe: {best['sharpe']:.2f} | Return: {best['annual_return']:.1f}% | "
                      f"Win: {best['win_rate']:.1f}% | DD: {best['max_dd']:.1f}%")
                print(f"Trades: {best['trades']:,} | PF: {best['profit_factor']:.2f}")
                print("="*100)
                
                last_count = len(filtered)
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\n[STOPPED] Monitor stopped - Search continues in background")
        print(f"Final count: {last_count} excellent strategies found")

if __name__ == "__main__":
    import os
    monitor_search()


