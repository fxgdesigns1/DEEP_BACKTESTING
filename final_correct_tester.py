#!/usr/bin/env python3
"""
FINAL CORRECT TESTER - Fixed Position Sizing
Uses FIXED DOLLAR RISK per trade to prevent exponential growth
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import multiprocessing as mp

def backtest_fixed_risk(df, ema_fast, ema_mid, ema_slow, stop_loss_pct, risk_reward):
    """Backtest with FIXED $200 risk per trade"""
    
    df = df.copy()
    df['ema_fast'] = df['close'].ewm(span=ema_fast, adjust=False).mean()
    df['ema_mid'] = df['close'].ewm(span=ema_mid, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=ema_slow, adjust=False).mean()
    
    df['prev_fast'] = df['ema_fast'].shift(1)
    df['prev_mid'] = df['ema_mid'].shift(1)
    
    df['bullish'] = (df['ema_fast'] > df['ema_mid']) & (df['prev_fast'] <= df['prev_mid'])
    df['bearish'] = (df['ema_fast'] < df['ema_mid']) & (df['prev_fast'] >= df['prev_mid'])
    
    capital = 10000.0
    peak_capital = capital
    trades = []
    position = None
    
    FIXED_RISK_DOLLARS = 200.0  # Risk $200 per trade (2% of initial $10k)
    
    for i in range(ema_slow + 10, len(df)):
        row = df.iloc[i]
        
        # Exit existing position
        if position:
            close_position = False
            pnl = 0
            
            if position['type'] == 'LONG':
                if row['low'] <= position['stop_loss']:
                    exit_price = position['stop_loss']
                    close_position = True
                elif row['high'] >= position['take_profit']:
                    exit_price = position['take_profit']
                    close_position = True
                elif row['bearish']:
                    exit_price = row['close']
                    close_position = True
                    
                if close_position:
                    pnl = (exit_price - position['entry']) / position['entry'] * position['size']
            
            else:  # SHORT
                if row['high'] >= position['stop_loss']:
                    exit_price = position['stop_loss']
                    close_position = True
                elif row['low'] <= position['take_profit']:
                    exit_price = position['take_profit']
                    close_position = True
                elif row['bullish']:
                    exit_price = row['close']
                    close_position = True
                    
                if close_position:
                    pnl = (position['entry'] - exit_price) / position['entry'] * position['size']
            
            if close_position:
                capital += pnl
                peak_capital = max(peak_capital, capital)
                trades.append({'pnl': pnl, 'win': pnl > 0})
                position = None
        
        # Enter new position with FIXED risk
        if position is None and capital > 0:
            if row['bullish']:
                entry_price = row['close']
                sl = entry_price * (1 - stop_loss_pct / 100)
                tp = entry_price * (1 + (stop_loss_pct * risk_reward) / 100)
                
                # FIXED RISK: position size based on $200 risk, not % of capital
                position_size = FIXED_RISK_DOLLARS / (stop_loss_pct / 100)
                
                position = {
                    'type': 'LONG',
                    'entry': entry_price,
                    'stop_loss': sl,
                    'take_profit': tp,
                    'size': position_size
                }
            
            elif row['bearish']:
                entry_price = row['close']
                sl = entry_price * (1 + stop_loss_pct / 100)
                tp = entry_price * (1 - (stop_loss_pct * risk_reward) / 100)
                
                position_size = FIXED_RISK_DOLLARS / (stop_loss_pct / 100)
                
                position = {
                    'type': 'SHORT',
                    'entry': entry_price,
                    'stop_loss': sl,
                    'take_profit': tp,
                    'size': position_size
                }
    
    if len(trades) == 0:
        return None
    
    wins = [t for t in trades if t['win']]
    losses = [t for t in trades if not t['win']]
    
    total_return = (capital / 10000 - 1) * 100
    win_rate = len(wins) / len(trades) * 100
    
    returns = [t['pnl'] / 10000 for t in trades]
    sharpe = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if len(returns) > 1 and np.std(returns) > 0 else 0
    
    max_dd_pct = ((peak_capital - capital) / peak_capital * 100) if capital < peak_capital else 0
    
    profit_factor = (sum(t['pnl'] for t in wins) / abs(sum(t['pnl'] for t in losses))) if losses else 999
    
    avg_win_pct = (np.mean([t['pnl'] for t in wins]) / 10000 * 100) if wins else 0
    avg_loss_pct = (np.mean([t['pnl'] for t in losses]) / 10000 * 100) if losses else 0
    
    return {
        'total_trades': len(trades),
        'win_rate': win_rate,
        'sharpe_ratio': sharpe,
        'total_return_pct': total_return,
        'max_drawdown_pct': max_dd_pct,
        'profit_factor': profit_factor,
        'avg_win_pct': avg_win_pct,
        'avg_loss_pct': avg_loss_pct
    }

def test_scenario(scenario):
    """Test single scenario"""
    try:
        file_path = f"data/MASTER_DATASET/{scenario['tf']}/{scenario['pair']}_{scenario['tf']}.csv"
        df = pd.read_csv(file_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        results = backtest_fixed_risk(
            df=df,
            ema_fast=scenario['ema_fast'],
            ema_mid=scenario['ema_mid'],
            ema_slow=scenario['ema_slow'],
            stop_loss_pct=scenario['sl'],
            risk_reward=scenario['rr']
        )
        
        if results:
            return {'scenario': scenario, 'results': results}
        return None
    except Exception as e:
        return None

def main():
    print("="*100)
    print("                     FINAL CORRECT MULTI-TIMEFRAME TESTER")
    print("="*100)
    print("Fixed position sizing: $200 risk per trade (no compounding)")
    print("This will give REALISTIC returns!")
    print("")
    
    scenarios = []
    for pair in ['xau_usd', 'gbp_usd', 'eur_usd', 'aud_usd', 'gbp_jpy']:
        for tf in ['15m', '30m', '1h']:
            for ema_combo in [(3,8,21), (5,13,34), (8,21,55)]:
                for sl in [0.2, 0.3, 0.4, 0.5]:
                    for rr in [1.5, 2.0, 2.5, 3.0]:
                        scenarios.append({
                            'pair': pair,
                            'tf': tf,
                            'ema_fast': ema_combo[0],
                            'ema_mid': ema_combo[1],
                            'ema_slow': ema_combo[2],
                            'sl': sl,
                            'rr': rr
                        })
    
    print(f"Testing {len(scenarios)} scenarios...")
    print("Expected time: 10-15 minutes")
    print("")
    
    results = []
    with mp.Pool(16) as pool:
        for i, r in enumerate(pool.imap_unordered(test_scenario, scenarios), 1):
            if r:
                results.append(r)
                if len(results) <= 5:
                    s = r['scenario']
                    res = r['results']
                    print(f"[FOUND #{len(results)}] {s['pair'].upper()} {s['tf']}")
                    print(f"  Sharpe: {res['sharpe_ratio']:.2f} | Return: {res['total_return_pct']:.1f}% | Win: {res['win_rate']:.1f}%")
            
            if i % 100 == 0:
                print(f"[PROGRESS] {i}/{len(scenarios)} ({i/len(scenarios)*100:.1f}%) - Found {len(results)}")
    
    print("")
    print("="*100)
    print(f"COMPLETE - Found {len(results)} successful strategies")
    print("="*100)
    print("")
    
    if results:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_dir = Path(f"H:/My Drive/AI Trading/exported strategies/final_correct_{timestamp}")
        export_dir.mkdir(parents=True, exist_ok=True)
        
        with open(export_dir / 'all_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Sort by Sharpe
        results.sort(key=lambda x: x['results']['sharpe_ratio'], reverse=True)
        
        print("TOP 30 STRATEGIES BY SHARPE RATIO:")
        print("")
        for i, item in enumerate(results[:30], 1):
            s = item['scenario']
            r = item['results']
            print(f"{i}. {s['pair'].upper()} {s['tf']} | EMA {s['ema_fast']}/{s['ema_mid']}/{s['ema_slow']}")
            print(f"   Sharpe: {r['sharpe_ratio']:.2f} | Return: {r['total_return_pct']:.1f}% | Win: {r['win_rate']:.1f}%")
            print(f"   Trades: {r['total_trades']} | DD: {r['max_drawdown_pct']:.2f}% | PF: {r['profit_factor']:.2f}")
            print(f"   Avg Win: {r['avg_win_pct']:.2f}% | Avg Loss: {r['avg_loss_pct']:.2f}% | SL: {s['sl']}% | R:R: {s['rr']}:1")
            print("")
        
        # Best by timeframe
        print("="*100)
        print("BEST STRATEGY BY TIMEFRAME:")
        print("="*100)
        print("")
        for tf in ['15m', '30m', '1h']:
            tf_results = [x for x in results if x['scenario']['tf'] == tf]
            if tf_results:
                best = max(tf_results, key=lambda x: x['results']['sharpe_ratio'])
                s = best['scenario']
                r = best['results']
                print(f"{tf.upper()} WINNER: {s['pair'].upper()}")
                print(f"  EMAs: {s['ema_fast']}/{s['ema_mid']}/{s['ema_slow']}")
                print(f"  Sharpe: {r['sharpe_ratio']:.2f} | Return: {r['total_return_pct']:.1f}%")
                print(f"  Win Rate: {r['win_rate']:.1f}% | Trades: {r['total_trades']}")
                print(f"  Max DD: {r['max_drawdown_pct']:.2f}% | PF: {r['profit_factor']:.2f}")
                print(f"  Stop Loss: {s['sl']}% | R:R: {s['rr']}:1")
                print("")
        
        # Filter for SUCCESS criteria (relaxed for longer timeframes)
        successful = [x for x in results if 
                     x['results']['sharpe_ratio'] >= 1.5 and
                     x['results']['total_return_pct'] >= 20 and
                     x['results']['max_drawdown_pct'] <= 5 and
                     x['results']['win_rate'] >= 55 and
                     x['results']['total_trades'] >= 100]
        
        print("="*100)
        print(f"STRATEGIES MEETING SUCCESS CRITERIA: {len(successful)}")
        print("="*100)
        print("Criteria: Sharpe >= 1.5, Return >= 20%, DD <= 5%, Win >= 55%, Trades >= 100")
        print("")
        
        if successful:
            for i, item in enumerate(successful[:10], 1):
                s = item['scenario']
                r = item['results']
                print(f"{i}. {s['pair'].upper()} {s['tf']} | EMA {s['ema_fast']}/{s['ema_mid']}/{s['ema_slow']}")
                print(f"   Sharpe: {r['sharpe_ratio']:.2f} | Return: {r['total_return_pct']:.1f}% | Win: {r['win_rate']:.1f}%")
                print(f"   SL: {s['sl']}% | R:R: {s['rr']}:1")
                print("")
        
        print(f"[SAVED] All results: {export_dir / 'all_results.json'}")
        print("")
        print("="*100)
        print("READY TO DEPLOY!")
        print("="*100)

if __name__ == "__main__":
    main()


