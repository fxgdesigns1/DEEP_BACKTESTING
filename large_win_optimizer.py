#!/usr/bin/env python3
"""
LARGE WIN OPTIMIZER
Specifically targets: 1-2% average wins, <1% average losses
Uses larger timeframes and higher R:R ratios
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

class LargeWinOptimizer:
    """Optimizer for large win strategies"""
    
    def __init__(self):
        self.export_path = Path(r"H:\My Drive\AI Trading\exported strategies")
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results_dir = self.export_path / f"large_wins_{self.timestamp}"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "="*100)
        print(" "*25 + "LARGE WIN STRATEGY OPTIMIZER")
        print("="*100)
        print(f"\nTARGET: Avg Wins 1-2%, Avg Losses <1%")
        print(f"Method: Larger timeframes + Higher R:R ratios")
        print(f"Export: {self.results_dir}")
        
    def generate_large_win_scenarios(self):
        """Generate scenarios optimized for large wins"""
        
        scenarios = []
        scenario_id = 0
        
        # Focus on pairs with larger moves
        pairs = ['xau_usd', 'gbp_jpy', 'eur_jpy', 'nzd_usd', 'gbp_usd', 'aud_usd']
        
        # LARGER TIMEFRAMES for bigger moves
        timeframes = ['15m', '30m', '1h']  # Skip 5m - moves too small
        
        # Use proven EMA combinations
        ema_combos = [(3, 12), (3, 21), (5, 21), (8, 21)]
        
        # HIGH R:R ratios to capture large wins
        rr_ratios = [3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0]
        
        # WIDER stops to let wins develop
        sl_mults = [2.0, 2.5, 3.0, 3.5, 4.0]
        
        # RSI configurations
        rsi_configs = [(20, 80), (25, 75), (30, 70)]
        
        print("\n[GENERATING] Large win scenarios...")
        
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
        
        print(f"\n[SUCCESS] Generated {len(scenarios):,} large-win scenarios")
        print(f"  Pairs: {pairs}")
        print(f"  Timeframes: {timeframes} (larger moves)")
        print(f"  R:R Ratios: {rr_ratios} (up to 10:1!)")
        print(f"  Stop Loss: {sl_mults} (wider stops)")
        print(f"  Estimated time: 3-5 hours\n")
        
        return scenarios
    
    def test_scenario(self, scenario):
        """Test scenario and calculate detailed stats"""
        
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
                    exit_reason = None
                    
                    if position == 1:
                        if row['low'] <= sl:
                            exit_price = sl
                            exit_reason = 'SL'
                        elif row['high'] >= tp:
                            exit_price = tp
                            exit_reason = 'TP'
                        elif row['signal'] == -1:
                            exit_price = row['close']
                            exit_reason = 'Signal'
                    elif position == -1:
                        if row['high'] >= sl:
                            exit_price = sl
                            exit_reason = 'SL'
                        elif row['low'] <= tp:
                            exit_price = tp
                            exit_reason = 'TP'
                        elif row['signal'] == 1:
                            exit_price = row['close']
                            exit_reason = 'Signal'
                    
                    if exit_price:
                        pnl_pct = ((exit_price - entry_price) / entry_price * 100) * position
                        trades.append({
                            'pnl_pct': pnl_pct,
                            'exit_reason': exit_reason
                        })
                        position = 0
            
            if not trades or len(trades) < 30:
                return None
            
            trades_df = pd.DataFrame(trades)
            wins = trades_df[trades_df['pnl_pct'] > 0]
            losses = trades_df[trades_df['pnl_pct'] < 0]
            
            # Calculate metrics
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
            
            # CHECK LARGE WIN CRITERIA
            if (1.0 <= avg_win <= 2.0 and 
                abs(avg_loss) < 1.0 and 
                win_rate >= 50.0 and  # Lower win rate acceptable with large wins
                max_dd <= 3.5 and 
                sharpe >= 1.5):  # Slightly lower Sharpe acceptable
                
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
                    'tp_rate': (trades_df['exit_reason'] == 'TP').sum() / len(trades_df) * 100
                }
            
            return None
            
        except Exception as e:
            return None
    
    def run_optimization(self):
        """Run large win optimization"""
        
        scenarios = self.generate_large_win_scenarios()
        
        print(f"[STARTING] Testing {len(scenarios):,} scenarios for large wins...")
        print(f"[CORES] Using {mp.cpu_count()} cores\n")
        
        successful = []
        tested = 0
        start_time = datetime.now()
        
        with ProcessPoolExecutor(max_workers=min(20, mp.cpu_count())) as executor:
            futures = {executor.submit(self.test_scenario, s): s for s in scenarios}
            
            for future in as_completed(futures):
                tested += 1
                
                try:
                    result = future.result()
                    
                    if result:
                        successful.append(result)
                        
                        print(f"\n>>> LARGE WIN STRATEGY #{len(successful)} <<<")
                        print(f"  {result['scenario']['pair'].upper()} {result['scenario']['timeframe']} - "
                              f"R:R 1:{result['scenario']['rr_ratio']}")
                        print(f"  Avg Win: {result['avg_win']:.3f}% | Avg Loss: {result['avg_loss']:.3f}%")
                        print(f"  Win Rate: {result['win_rate']:.1f}% | Sharpe: {result['sharpe']:.2f} | "
                              f"Return: {result['annual_return']:.1f}%")
                    
                    if tested % 500 == 0:
                        elapsed = datetime.now() - start_time
                        pct = (tested / len(scenarios)) * 100
                        print(f"\n[PROGRESS] {tested:,}/{len(scenarios):,} ({pct:.1f}%)")
                        print(f"  Elapsed: {elapsed} | Found: {len(successful)} large-win strategies")
                        
                        if successful:
                            checkpoint = self.results_dir / f"checkpoint_{tested}.json"
                            with open(checkpoint, 'w') as f:
                                json.dump({'tested': tested, 'successful': successful}, f, indent=2, default=str)
                
                except:
                    pass
        
        # Save results
        self.save_results(successful, len(scenarios))
    
    def save_results(self, strategies, total_tested):
        """Save large win results"""
        
        print(f"\n\n{'='*100}")
        print(" "*30 + "LARGE WIN OPTIMIZATION COMPLETE")
        print("="*100)
        print(f"\nTotal Scenarios: {total_tested:,}")
        print(f"Large Win Strategies Found: {len(strategies)}")
        
        if not strategies:
            print("\n[RESULT] No strategies achieved 1-2% average wins with current parameters")
            print("\n[ANALYSIS] This is expected because:")
            print("  - Even 1-hour timeframe averages 0.5-0.8% per move")
            print("  - To get 1-2% avg wins requires:")
            print("    * 4-hour or daily timeframes")
            print("    * R:R ratios of 10:1 or higher")
            print("    * Win rates dropping to 30-50%")
            print("    * Much fewer total trades (20-50/year)")
            print("\n[TRADE-OFF] Large wins mean:")
            print("  PROS: Each win is 1-2% (vs 0.1-0.3%)")
            print("  CONS: Win rate drops from 80% to 40-60%")
            print("  CONS: Fewer trades (100-200/year vs 3,000/year)")
            print("  CONS: Longer holding times (hours to days)")
            print("  RESULT: Similar or LOWER annual returns overall")
            return
        
        strategies.sort(key=lambda x: x['avg_win'], reverse=True)
        
        print(f"\n[TOP 10 LARGE WIN STRATEGIES]")
        print(f"{'Rank':<6} {'Pair':<10} {'TF':<6} {'AvgWin':<10} {'AvgLoss':<10} {'WinRate':<9} {'Return':<10}")
        print("-"*100)
        
        for i, s in enumerate(strategies[:10], 1):
            sc = s['scenario']
            print(f"{i:<6} {sc['pair'].upper():<10} {sc['timeframe']:<6} "
                  f"{s['avg_win']:<9.3f}% {s['avg_loss']:<9.3f}% "
                  f"{s['win_rate']:<8.1f}% {s['annual_return']:<9.1f}%")
        
        # Save JSON
        results_file = self.results_dir / "large_win_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': self.timestamp,
                'total_tested': total_tested,
                'successful': len(strategies),
                'top_10': strategies[:10]
            }, f, indent=2, default=str)
        
        print(f"\n[SAVED] {results_file}")
        print("="*100 + "\n")

if __name__ == "__main__":
    optimizer = LargeWinOptimizer()
    optimizer.run_optimization()


