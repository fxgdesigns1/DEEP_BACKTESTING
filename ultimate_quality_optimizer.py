#!/usr/bin/env python3
"""
ULTIMATE QUALITY OPTIMIZER
Max 4% Drawdown + Quality Filters for Better Win Rates
Tests stricter criteria for higher quality signals
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, time
import json
import multiprocessing as mp

# STRICT SUCCESS CRITERIA
MAX_DRAWDOWN = 4.0  # 4% MAX
MIN_WIN_RATE = 60.0  # Higher threshold for quality
MIN_SHARPE = 2.0
MIN_RETURN = 50.0

def is_london_ny_session(timestamp):
    """Check if timestamp is during London or NY session"""
    hour = timestamp.hour
    # London: 8:00-16:00 UTC, NY: 13:00-21:00 UTC
    return (8 <= hour < 16) or (13 <= hour < 21)

def backtest_with_quality_filters(df, params):
    """Backtest with quality filters"""
    
    df = df.copy()
    
    # Calculate EMAs
    df['ema_fast'] = df['close'].ewm(span=params['ema_fast'], adjust=False).mean()
    df['ema_mid'] = df['close'].ewm(span=params['ema_mid'], adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=params['ema_slow'], adjust=False).mean()
    
    # Calculate ATR for trend strength
    df['tr'] = np.maximum(
        df['high'] - df['low'],
        np.maximum(
            abs(df['high'] - df['close'].shift(1)),
            abs(df['low'] - df['close'].shift(1))
        )
    )
    df['atr'] = df['tr'].ewm(span=14, adjust=False).mean()
    
    # Trend strength: distance between EMAs relative to price
    df['ema_spacing'] = abs(df['ema_fast'] - df['ema_slow']) / df['close'] * 100
    
    # Detect crossovers
    df['prev_fast'] = df['ema_fast'].shift(1)
    df['prev_mid'] = df['ema_mid'].shift(1)
    
    df['bullish_cross'] = (df['ema_fast'] > df['ema_mid']) & (df['prev_fast'] <= df['prev_mid'])
    df['bearish_cross'] = (df['ema_fast'] < df['ema_mid']) & (df['prev_fast'] >= df['prev_mid'])
    
    # Quality filters
    if params['require_ema_alignment']:
        # For bullish: fast > mid > slow
        df['bullish_cross'] = df['bullish_cross'] & (df['ema_mid'] > df['ema_slow'])
        # For bearish: fast < mid < slow
        df['bearish_cross'] = df['bearish_cross'] & (df['ema_mid'] < df['ema_slow'])
    
    if params['min_trend_strength'] > 0:
        # Only trade when EMAs are sufficiently spread (strong trend)
        df['bullish_cross'] = df['bullish_cross'] & (df['ema_spacing'] >= params['min_trend_strength'])
        df['bearish_cross'] = df['bearish_cross'] & (df['ema_spacing'] >= params['min_trend_strength'])
    
    capital = 10000.0
    peak_capital = capital
    trades = []
    position = None
    bars_since_trade = 999
    
    FIXED_RISK = 200.0
    
    for i in range(params['ema_slow'] + 20, len(df)):
        row = df.iloc[i]
        bars_since_trade += 1
        
        # Session filter
        if params['session_filter'] and not is_london_ny_session(row.name):
            continue
        
        # Exit existing position
        if position:
            close_position = False
            pnl = 0
            
            if position['type'] == 'LONG':
                if row['low'] <= position['stop_loss']:
                    pnl = (position['stop_loss'] - position['entry']) / position['entry'] * position['size']
                    close_position = True
                elif row['high'] >= position['take_profit']:
                    pnl = (position['take_profit'] - position['entry']) / position['entry'] * position['size']
                    close_position = True
                elif row['bearish_cross']:
                    pnl = (row['close'] - position['entry']) / position['entry'] * position['size']
                    close_position = True
            else:
                if row['high'] >= position['stop_loss']:
                    pnl = (position['entry'] - position['stop_loss']) / position['entry'] * position['size']
                    close_position = True
                elif row['low'] <= position['take_profit']:
                    pnl = (position['entry'] - position['take_profit']) / position['entry'] * position['size']
                    close_position = True
                elif row['bullish_cross']:
                    pnl = (position['entry'] - row['close']) / position['entry'] * position['size']
                    close_position = True
            
            if close_position:
                capital += pnl
                peak_capital = max(peak_capital, capital)
                trades.append({'pnl': pnl, 'win': pnl > 0})
                position = None
                bars_since_trade = 0
        
        # Enter new position with quality filters
        if position is None and bars_since_trade >= params['min_bars_between_trades']:
            if row['bullish_cross']:
                entry_price = row['close']
                sl = entry_price * (1 - params['stop_loss_pct'] / 100)
                tp = entry_price * (1 + (params['stop_loss_pct'] * params['rr_ratio']) / 100)
                position_size = FIXED_RISK / (params['stop_loss_pct'] / 100)
                
                position = {
                    'type': 'LONG',
                    'entry': entry_price,
                    'stop_loss': sl,
                    'take_profit': tp,
                    'size': position_size
                }
            
            elif row['bearish_cross']:
                entry_price = row['close']
                sl = entry_price * (1 + params['stop_loss_pct'] / 100)
                tp = entry_price * (1 - (params['stop_loss_pct'] * params['rr_ratio']) / 100)
                position_size = FIXED_RISK / (params['stop_loss_pct'] / 100)
                
                position = {
                    'type': 'SHORT',
                    'entry': entry_price,
                    'stop_loss': sl,
                    'take_profit': tp,
                    'size': position_size
                }
    
    if len(trades) < 50:  # Need meaningful sample
        return None
    
    wins = [t for t in trades if t['win']]
    losses = [t for t in trades if not t['win']]
    
    total_return = (capital / 10000 - 1) * 100
    win_rate = len(wins) / len(trades) * 100
    
    returns = [t['pnl'] / 10000 for t in trades]
    sharpe = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if np.std(returns) > 0 else 0
    
    # Calculate proper drawdown
    running_capital = 10000.0
    max_dd = 0
    peak = running_capital
    for t in trades:
        running_capital += t['pnl']
        if running_capital > peak:
            peak = running_capital
        dd = ((peak - running_capital) / peak * 100) if running_capital < peak else 0
        max_dd = max(max_dd, dd)
    
    profit_factor = (sum(t['pnl'] for t in wins) / abs(sum(t['pnl'] for t in losses))) if losses else 999
    
    avg_win_pct = (np.mean([t['pnl'] for t in wins]) / 10000 * 100) if wins else 0
    avg_loss_pct = (np.mean([t['pnl'] for t in losses]) / 10000 * 100) if losses else 0
    
    return {
        'total_trades': len(trades),
        'win_rate': win_rate,
        'sharpe_ratio': sharpe,
        'total_return_pct': total_return,
        'max_drawdown_pct': max_dd,
        'profit_factor': profit_factor,
        'avg_win_pct': avg_win_pct,
        'avg_loss_pct': avg_loss_pct
    }

def test_scenario(scenario):
    """Test scenario"""
    try:
        file_path = f"data/MASTER_DATASET/{scenario['tf']}/{scenario['pair']}_{scenario['tf']}.csv"
        df = pd.read_csv(file_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        results = backtest_with_quality_filters(df, scenario)
        
        if results and (results['max_drawdown_pct'] <= MAX_DRAWDOWN and
                       results['win_rate'] >= MIN_WIN_RATE and
                       results['sharpe_ratio'] >= MIN_SHARPE and
                       results['total_return_pct'] >= MIN_RETURN):
            return {'scenario': scenario, 'results': results, 'quality': True}
        elif results:
            return {'scenario': scenario, 'results': results, 'quality': False}
        return None
    except:
        return None

def main():
    print("="*100)
    print("                     ULTIMATE QUALITY OPTIMIZER")
    print("="*100)
    print("MAX DRAWDOWN: 4.0%")
    print("MIN WIN RATE: 60%")
    print("Adding quality filters for better signals")
    print("")
    
    scenarios = []
    
    # Focus on proven pairs
    pairs = ['gbp_usd', 'aud_usd', 'eur_usd', 'gbp_jpy', 'xau_usd']
    timeframes = ['15m', '30m', '1h']
    
    # EMA combinations
    ema_combos = [
        (3, 8, 21),   # Fast (proven winner)
        (5, 13, 34),  # Moderate
        (8, 21, 55),  # Slower
        (5, 21, 50),  # Alternative
    ]
    
    # Stop losses
    stop_losses = [0.2, 0.25, 0.3, 0.35, 0.4, 0.5]
    
    # R:R ratios (test higher)
    rr_ratios = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
    
    # Quality filters to test
    require_alignment_options = [True, False]  # All EMAs must be aligned
    min_trend_strength_options = [0, 0.01, 0.02, 0.03]  # Min % spacing between fast/slow EMA
    session_filter_options = [True, False]  # London/NY only vs all sessions
    min_bars_between_options = [0, 5, 10, 15]  # Bars spacing between trades
    
    for pair in pairs:
        for tf in timeframes:
            for ema in ema_combos:
                for sl in stop_losses:
                    for rr in rr_ratios:
                        for req_align in require_alignment_options:
                            for trend_str in min_trend_strength_options:
                                for sess_filt in session_filter_options:
                                    for min_bars in min_bars_between_options:
                                        scenarios.append({
                                            'pair': pair,
                                            'tf': tf,
                                            'ema_fast': ema[0],
                                            'ema_mid': ema[1],
                                            'ema_slow': ema[2],
                                            'stop_loss_pct': sl,
                                            'rr_ratio': rr,
                                            'require_ema_alignment': req_align,
                                            'min_trend_strength': trend_str,
                                            'session_filter': sess_filt,
                                            'min_bars_between_trades': min_bars
                                        })
    
    print(f"Testing {len(scenarios):,} scenarios...")
    print(f"  Pairs: {len(pairs)}")
    print(f"  Timeframes: {len(timeframes)}")
    print(f"  EMA Combos: {len(ema_combos)}")
    print(f"  Stop Losses: {len(stop_losses)}")
    print(f"  R:R Ratios: {len(rr_ratios)} (up to 5:1)")
    print(f"  Quality Filters: Testing all combinations")
    print(f"  Expected time: 45-60 minutes")
    print("")
    print("STRICT CRITERIA:")
    print(f"  Max Drawdown: {MAX_DRAWDOWN}%")
    print(f"  Min Win Rate: {MIN_WIN_RATE}%")
    print(f"  Min Sharpe: {MIN_SHARPE}")
    print(f"  Min Return: {MIN_RETURN}%")
    print("")
    
    high_quality = []
    all_results = []
    
    with mp.Pool(16) as pool:
        for i, r in enumerate(pool.imap_unordered(test_scenario, scenarios), 1):
            if r:
                all_results.append(r)
                if r.get('quality'):
                    high_quality.append(r)
                    print(f"[HIGH QUALITY #{len(high_quality)}] {r['scenario']['pair'].upper()} {r['scenario']['tf']}")
                    res = r['results']
                    print(f"  Sharpe: {res['sharpe_ratio']:.2f} | Return: {res['total_return_pct']:.1f}% | Win: {res['win_rate']:.1f}%")
                    print(f"  DD: {res['max_drawdown_pct']:.2f}% | Trades: {res['total_trades']}")
                    s = r['scenario']
                    print(f"  Filters: EMA-Align={s['require_ema_alignment']}, Trend>={s['min_trend_strength']}%, Session={s['session_filter']}, Spacing={s['min_bars_between_trades']}")
                    print("")
            
            if i % 500 == 0:
                print(f"[PROGRESS] {i:,}/{len(scenarios):,} ({i/len(scenarios)*100:.1f}%)")
                print(f"  High Quality Found: {len(high_quality)}")
                print(f"  Total Results: {len(all_results)}")
                print("")
    
    print("")
    print("="*100)
    print(f"OPTIMIZATION COMPLETE")
    print("="*100)
    print(f"Total Scenarios: {len(scenarios):,}")
    print(f"Results with Trades: {len(all_results):,}")
    print(f"HIGH QUALITY Strategies (DD<={MAX_DRAWDOWN}%, Win>={MIN_WIN_RATE}%): {len(high_quality)}")
    print("")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    export_dir = Path(f"H:/My Drive/AI Trading/exported strategies/ultimate_quality_{timestamp}")
    export_dir.mkdir(parents=True, exist_ok=True)
    
    # Save all results
    with open(export_dir / 'all_results.json', 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    if high_quality:
        # Save high quality
        with open(export_dir / 'high_quality_strategies.json', 'w') as f:
            json.dump(high_quality, f, indent=2, default=str)
        
        # Sort by Sharpe
        high_quality.sort(key=lambda x: x['results']['sharpe_ratio'], reverse=True)
        
        print("="*100)
        print(f"TOP 20 HIGH QUALITY STRATEGIES (MAX DD: {MAX_DRAWDOWN}%, MIN WIN: {MIN_WIN_RATE}%)")
        print("="*100)
        print("")
        for i, item in enumerate(high_quality[:20], 1):
            s = item['scenario']
            r = item['results']
            print(f"{i}. {s['pair'].upper()} {s['tf']} | EMA {s['ema_fast']}/{s['ema_mid']}/{s['ema_slow']}")
            print(f"   Sharpe: {r['sharpe_ratio']:.2f} | Return: {r['total_return_pct']:.1f}% | Win: {r['win_rate']:.1f}%")
            print(f"   DD: {r['max_drawdown_pct']:.2f}% | Trades: {r['total_trades']} | PF: {r['profit_factor']:.2f}")
            print(f"   Avg Win: {r['avg_win_pct']:.2f}% | Avg Loss: {r['avg_loss_pct']:.2f}%")
            print(f"   SL: {s['stop_loss_pct']}% | R:R: {s['rr_ratio']}:1")
            print(f"   Filters: Align={s['require_ema_alignment']}, Trend>={s['min_trend_strength']}%, Session={s['session_filter']}, Spacing={s['min_bars_between_trades']} bars")
            print("")
        
        # Analysis by filter settings
        print("="*100)
        print("FILTER EFFECTIVENESS ANALYSIS")
        print("="*100)
        print("")
        
        # EMA Alignment impact
        with_align = [x for x in high_quality if x['scenario']['require_ema_alignment']]
        without_align = [x for x in high_quality if not x['scenario']['require_ema_alignment']]
        print(f"EMA Alignment Required:")
        print(f"  With: {len(with_align)} strategies | Avg Sharpe: {np.mean([x['results']['sharpe_ratio'] for x in with_align]):.2f if with_align else 0}")
        print(f"  Without: {len(without_align)} strategies | Avg Sharpe: {np.mean([x['results']['sharpe_ratio'] for x in without_align]):.2f if without_align else 0}")
        print("")
        
        # Session filter impact
        with_session = [x for x in high_quality if x['scenario']['session_filter']]
        without_session = [x for x in high_quality if not x['scenario']['session_filter']]
        print(f"Session Filter (London/NY only):")
        print(f"  With: {len(with_session)} strategies | Avg Win Rate: {np.mean([x['results']['win_rate'] for x in with_session]):.1f}%")
        print(f"  Without: {len(without_session)} strategies | Avg Win Rate: {np.mean([x['results']['win_rate'] for x in without_session]):.1f}%")
        print("")
        
        # Best by timeframe
        print("="*100)
        print("BEST BY TIMEFRAME")
        print("="*100)
        print("")
        for tf in ['15m', '30m', '1h']:
            tf_strats = [x for x in high_quality if x['scenario']['tf'] == tf]
            if tf_strats:
                best = max(tf_strats, key=lambda x: x['results']['sharpe_ratio'])
                s = best['scenario']
                r = best['results']
                print(f"{tf.upper()}: {s['pair'].upper()} | Sharpe {r['sharpe_ratio']:.2f} | Win {r['win_rate']:.1f}% | DD {r['max_drawdown_pct']:.2f}%")
                print(f"  EMA {s['ema_fast']}/{s['ema_mid']}/{s['ema_slow']} | SL {s['stop_loss_pct']}% | R:R {s['rr_ratio']}:1")
                print(f"  Filters: Align={s['require_ema_alignment']}, Trend>={s['min_trend_strength']}%, Session={s['session_filter']}, Spacing={s['min_bars_between_trades']}")
                print("")
        
        print(f"[SAVED] All: {export_dir / 'all_results.json'}")
        print(f"[SAVED] High Quality: {export_dir / 'high_quality_strategies.json'}")
    else:
        print("NO STRATEGIES MET HIGH QUALITY CRITERIA")
        print("")
        print("Best overall strategies (relaxed criteria):")
        if all_results:
            all_results.sort(key=lambda x: x['results']['sharpe_ratio'], reverse=True)
            for i, item in enumerate(all_results[:5], 1):
                s = item['scenario']
                r = item['results']
                print(f"{i}. {s['pair'].upper()} {s['tf']} - Sharpe: {r['sharpe_ratio']:.2f}, Win: {r['win_rate']:.1f}%, DD: {r['max_drawdown_pct']:.2f}%")

if __name__ == "__main__":
    main()


