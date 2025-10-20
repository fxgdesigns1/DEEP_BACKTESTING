#!/usr/bin/env python3
"""
SWING TRADING OPTIMIZER
Test 4-hour, Daily, and Weekly timeframes
For traders who want fewer trades with larger moves
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

from GOLDEN_RULE_NO_SYNTHETIC_DATA import RealDataEnforcer

enforcer = RealDataEnforcer()

class SwingTradingOptimizer:
    """Optimizer for swing trading strategies"""
    
    def __init__(self):
        self.export_path = Path(r"H:\My Drive\AI Trading\exported strategies")
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results_dir = self.export_path / f"swing_trading_{self.timestamp}"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "="*100)
        print(" "*30 + "SWING TRADING OPTIMIZER")
        print("="*100)
        print(f"\nTimeframes: 1-hour, 4-hour ONLY (user preference)")
        print(f"Target: Swing trading with reasonable holding times")
        print(f"Export: {self.results_dir}")
        
    def generate_swing_scenarios(self):
        """Generate swing trading scenarios"""
        
        scenarios = []
        scenario_id = 0
        
        # All pairs
        pairs = ['gbp_usd', 'eur_usd', 'xau_usd', 'aud_usd', 'nzd_usd', 
                 'usd_jpy', 'eur_jpy', 'gbp_jpy', 'usd_cad', 'usd_chf']
        
        # SWING TIMEFRAMES (1H and 4H only per user request)
        timeframes = ['1h', '4h']
        
        # EMA combinations for swing trading
        ema_combos = [
            (8, 21),   # Short-term swing
            (12, 50),  # Medium swing
            (20, 50),  # Balanced swing
            (21, 89),  # Long-term swing
            (50, 200), # Very long-term
        ]
        
        # Swing trading R:R (larger targets)
        rr_ratios = [2.0, 3.0, 4.0, 5.0]
        
        # Wider stops for swing
        sl_mults = [1.5, 2.0, 2.5, 3.0]
        
        # RSI
        rsi_configs = [(30, 70), (25, 75), (20, 80)]
        
        print("\n[GENERATING] Swing trading scenarios...")
        
        for pair in pairs:
            for tf in timeframes:
                for ema_fast, ema_slow in ema_combos:
                    for rr in rr_ratios:
                        for sl in sl_mults:
                            for rsi_os, rsi_ob in rsi_configs:
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
        
        print(f"\n[SUCCESS] Generated {len(scenarios):,} swing scenarios")
        print(f"  Pairs: {len(pairs)}")
        print(f"  Timeframes: {timeframes}")
        print(f"  EMA Combos: {ema_combos}")
        print(f"  Expected trades: 20-200 per year per strategy")
        print(f"  Expected holding time: Hours to weeks")
        print(f"  Estimated time: 2-3 hours\n")
        
        return scenarios
    
    def test_scenario(self, scenario):
        """Test swing trading scenario with detailed stats"""
        
        try:
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
                        duration_hours = (timestamp - entry_time).total_seconds() / 3600
                        
                        trades.append({
                            'pnl_pct': pnl_pct,
                            'duration_hours': duration_hours
                        })
                        position = 0
            
            if not trades or len(trades) < 20:  # Need at least 20 trades for swing
                return None
            
            trades_df = pd.DataFrame(trades)
            wins = trades_df[trades_df['pnl_pct'] > 0]
            losses = trades_df[trades_df['pnl_pct'] < 0]
            
            win_rate = (len(wins) / len(trades_df)) * 100
            avg_win = wins['pnl_pct'].mean() if len(wins) > 0 else 0
            avg_loss = losses['pnl_pct'].mean() if len(losses) > 0 else 0
            
            cumulative = trades_df['pnl_pct'].cumsum()
            running_max = cumulative.cummax()
            drawdown = (cumulative - running_max)
            max_dd = abs(drawdown.min())
            
            sharpe = (trades_df['pnl_pct'].mean() / trades_df['pnl_pct'].std()) * np.sqrt(len(trades_df)) if len(trades_df) > 1 and trades_df['pnl_pct'].std() > 0 else 0
            
            total_profit = wins['pnl_pct'].sum() if len(wins) > 0 else 0
            total_loss = abs(losses['pnl_pct'].sum()) if len(losses) > 0 else 0
            profit_factor = (total_profit / total_loss) if total_loss > 0 else 0
            
            days = (df.index[-1] - df.index[0]).days
            annual_return = (trades_df['pnl_pct'].sum() / (days/365.25))
            
            avg_duration = trades_df['duration_hours'].mean()
            
            # Swing trading criteria (more relaxed)
            if (win_rate >= 50.0 and  # Lower win rate OK for swing
                max_dd <= 15.0 and      # Higher DD acceptable
                sharpe >= 1.0 and       # Lower Sharpe OK
                len(trades_df) >= 20):  # Min trades for significance
                
                return {
                    'scenario': scenario,
                    'trades': len(trades_df),
                    'win_rate': win_rate,
                    'sharpe': sharpe,
                    'annual_return': annual_return,
                    'max_dd': max_dd,
                    'profit_factor': profit_factor,
                    'avg_win': avg_win,
                    'avg_loss': avg_loss,
                    'avg_duration_hours': avg_duration,
                    'trades_per_year': len(trades_df) / (days/365.25)
                }
            
            return None
            
        except Exception as e:
            return None
    
    def run_optimization(self):
        """Run swing optimization"""
        
        scenarios = self.generate_swing_scenarios()
        
        print(f"[STARTING] Testing {len(scenarios):,} swing scenarios...")
        print(f"[CORES] Using {mp.cpu_count()} cores\n")
        
        successful = []
        tested = 0
        
        with ProcessPoolExecutor(max_workers=min(20, mp.cpu_count())) as executor:
            futures = {executor.submit(self.test_scenario, s): s for s in scenarios}
            
            for future in as_completed(futures):
                tested += 1
                
                try:
                    result = future.result()
                    
                    if result:
                        successful.append(result)
                        
                        print(f"\n>>> SWING STRATEGY #{len(successful)} <<<")
                        print(f"  {result['scenario']['pair'].upper()} {result['scenario']['timeframe']} - "
                              f"EMA {result['scenario']['ema_fast']}/{result['scenario']['ema_slow']}")
                        print(f"  Win: {result['win_rate']:.1f}% | Return: {result['annual_return']:.1f}% | "
                              f"Sharpe: {result['sharpe']:.2f}")
                        print(f"  Avg Win: {result['avg_win']:.2f}% | Avg Loss: {result['avg_loss']:.2f}%")
                        print(f"  Trades/Year: {result['trades_per_year']:.0f} | Avg Hold: {result['avg_duration_hours']:.0f} hours")
                    
                    if tested % 500 == 0:
                        pct = (tested / len(scenarios)) * 100
                        print(f"\n[PROGRESS] {tested:,}/{len(scenarios):,} ({pct:.1f}%) - Found {len(successful)} swing strategies")
                
                except:
                    pass
        
        # Save results
        self.save_results(successful, len(scenarios))
    
    def save_results(self, strategies, total_tested):
        """Save swing trading results"""
        
        print(f"\n\n{'='*100}")
        print(" "*30 + "SWING TRADING OPTIMIZATION COMPLETE")
        print("="*100)
        print(f"\nTotal Scenarios: {total_tested:,}")
        print(f"Swing Strategies Found: {len(strategies)}")
        
        if not strategies:
            print("\n[INFO] No swing strategies met criteria")
            return
        
        strategies.sort(key=lambda x: x['sharpe'], reverse=True)
        
        print(f"\n[TOP 10 SWING STRATEGIES]")
        print(f"{'Rank':<6} {'Pair':<10} {'TF':<6} {'Sharpe':<8} {'Return':<10} {'Win%':<8} {'Trades/Yr':<12} {'Hold (hrs)':<12}")
        print("-"*100)
        
        for i, s in enumerate(strategies[:10], 1):
            sc = s['scenario']
            print(f"{i:<6} {sc['pair'].upper():<10} {sc['timeframe']:<6} {s['sharpe']:<8.2f} "
                  f"{s['annual_return']:<9.1f}% {s['win_rate']:<7.1f}% {s['trades_per_year']:<11.0f} "
                  f"{s['avg_duration_hours']:<12.0f}")
        
        # Save
        results_file = self.results_dir / "swing_trading_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': self.timestamp,
                'total_tested': total_tested,
                'successful': len(strategies),
                'top_20': strategies[:20]
            }, f, indent=2, default=str)
        
        print(f"\n[SAVED] {results_file}")
        print("="*100 + "\n")

if __name__ == "__main__":
    optimizer = SwingTradingOptimizer()
    optimizer.run_optimization()

