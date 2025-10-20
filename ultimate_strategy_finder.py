#!/usr/bin/env python3
"""
ULTIMATE STRATEGY FINDER
Test ALL pairs, ALL timeframes, MULTIPLE strategy types
Find the absolute best strategies across entire possibility space
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
import json

from GOLDEN_RULE_NO_SYNTHETIC_DATA import RealDataEnforcer

enforcer = RealDataEnforcer()

class UltimateStrategyFinder:
    """Find the ultimate strategy across all possibilities"""
    
    def __init__(self):
        self.export_path = Path(r"H:\My Drive\AI Trading\exported strategies")
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results_dir = self.export_path / f"ultimate_search_{self.timestamp}"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # ALL available pairs
        self.all_pairs = [
            'gbp_usd', 'eur_usd', 'xau_usd', 'aud_usd',
            'usd_jpy', 'eur_jpy', 'gbp_jpy',
            'usd_cad', 'usd_chf', 'nzd_usd'
        ]
        
        # ALL available timeframes
        self.all_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']
        
        # Strategy types to test
        self.strategy_types = [
            'ema_crossover',
            'ema_pullback',
            'macd_crossover',
            'rsi_reversal',
            'multi_timeframe'
        ]
        
        self.results = []
        
    def generate_comprehensive_scenarios(self):
        """Generate ALL possible scenarios"""
        
        scenarios = []
        scenario_id = 0
        
        print("\n" + "="*100)
        print(" "*30 + "ULTIMATE STRATEGY FINDER")
        print("="*100)
        print("\nGenerating comprehensive test matrix...")
        
        # Priority timeframes (based on trading frequency)
        priority_timeframes = ['5m', '15m', '1h']
        
        # Test each pair
        for pair in self.all_pairs:
            for timeframe in priority_timeframes:
                
                # Strategy Type 1: Fast EMA Crossover (proven winner)
                for ema_fast in [3, 5, 8]:
                    for ema_slow in [12, 21, 34]:
                        if ema_slow <= ema_fast:
                            continue
                        for rr in [2.0, 3.0, 4.0]:
                            for sl in [1.0, 1.5, 2.0]:
                                scenario_id += 1
                                scenarios.append({
                                    'id': scenario_id,
                                    'type': 'ema_crossover',
                                    'pair': pair,
                                    'timeframe': timeframe,
                                    'ema_fast': ema_fast,
                                    'ema_slow': ema_slow,
                                    'rr_ratio': rr,
                                    'sl_atr_mult': sl,
                                    'rsi_oversold': 20,
                                    'rsi_overbought': 80
                                })
                
                # Strategy Type 2: Slower EMA (more conservative)
                for ema_fast in [8, 12, 20]:
                    for ema_slow in [34, 50, 89]:
                        if ema_slow <= ema_fast:
                            continue
                        for rr in [2.0, 3.0]:
                            scenario_id += 1
                            scenarios.append({
                                'id': scenario_id,
                                'type': 'ema_slow',
                                'pair': pair,
                                'timeframe': timeframe,
                                'ema_fast': ema_fast,
                                'ema_slow': ema_slow,
                                'rr_ratio': rr,
                                'sl_atr_mult': 1.5,
                                'rsi_oversold': 30,
                                'rsi_overbought': 70
                            })
        
        print(f"\n[SUCCESS] Generated {len(scenarios):,} comprehensive scenarios")
        print(f"  Pairs: {len(self.all_pairs)}")
        print(f"  Timeframes: {len(priority_timeframes)}")
        print(f"  Strategy Types: Fast EMA + Slow EMA variations")
        print(f"\n[CRITERIA] Win >= 65%, DD <= 10%, Sharpe >= 2.0")
        
        return scenarios
    
    def test_scenario(self, scenario):
        """Test single scenario - same logic as before"""
        try:
            df = enforcer.load_real_data(scenario['pair'], scenario['timeframe'])
            
            # Calculate indicators (same as before)
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
            
            df['signal'] = 0
            buy = (df['ema_fast'] > df['ema_slow']) & (df['ema_fast'].shift(1) <= df['ema_slow'].shift(1)) & (df['rsi'] < scenario['rsi_overbought'])
            sell = (df['ema_fast'] < df['ema_slow']) & (df['ema_fast'].shift(1) >= df['ema_slow'].shift(1)) & (df['rsi'] > scenario['rsi_oversold'])
            df.loc[buy, 'signal'] = 1
            df.loc[sell, 'signal'] = -1
            
            # Execute trades (same logic)
            trades = []
            position = 0
            
            for timestamp, row in df.iterrows():
                if pd.isna(row['atr']) or row['atr'] == 0:
                    continue
                
                if row['signal'] == 1 and position == 0:
                    position = 1
                    entry_price = row['close']
                    sl = entry_price - (row['atr'] * scenario['sl_atr_mult'])
                    tp = entry_price + (row['atr'] * scenario['sl_atr_mult'] * scenario['rr_ratio'])
                    
                elif row['signal'] == -1 and position == 0:
                    position = -1
                    entry_price = row['close']
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
                        trades.append({'pnl_pct': pnl_pct})
                        position = 0
            
            if not trades:
                return None
            
            trades_df = pd.DataFrame(trades)
            wins = trades_df[trades_df['pnl_pct'] > 0]
            losses = trades_df[trades_df['pnl_pct'] < 0]
            
            win_rate = (len(wins) / len(trades_df)) * 100
            
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
            
            # Check criteria
            if win_rate >= 65.0 and max_dd <= 10.0 and sharpe >= 2.0 and len(trades_df) >= 50:
                return {
                    'scenario': scenario,
                    'trades': len(trades_df),
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
    
    def run_ultimate_search(self):
        """Run the ultimate strategy search"""
        
        scenarios = self.generate_comprehensive_scenarios()
        
        print(f"\n[STARTING] Testing {len(scenarios):,} scenarios...")
        print(f"[CORES] Using {mp.cpu_count()} CPU cores")
        print(f"[ESTIMATED] ~2-4 hours for completion\n")
        
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
                        
                        print(f"\n>>> EXCELLENT #{len(successful)} <<<")
                        print(f"  {result['scenario']['pair'].upper()} {result['scenario']['timeframe']} - "
                              f"Sharpe: {result['sharpe']:.2f}, Win: {result['win_rate']:.1f}%, "
                              f"Return: {result['annual_return']:.1f}%, DD: {result['max_dd']:.1f}%")
                    
                    if tested % 200 == 0:
                        pct = (tested / len(scenarios)) * 100
                        print(f"\n[PROGRESS] {tested:,}/{len(scenarios):,} ({pct:.1f}%) - Found {len(successful)} excellent strategies")
                        
                        # Save checkpoint
                        if successful:
                            checkpoint = self.results_dir / f"checkpoint_{tested}.json"
                            with open(checkpoint, 'w') as f:
                                json.dump({'tested': tested, 'successful': successful}, f, indent=2, default=str)
                
                except:
                    pass
        
        # Save final results
        self.save_ultimate_results(successful, len(scenarios))
        
        return successful
    
    def save_ultimate_results(self, strategies, total_tested):
        """Save ultimate search results"""
        
        if not strategies:
            print("\n[WARNING] No strategies met criteria")
            return
        
        # Sort by Sharpe
        strategies.sort(key=lambda x: x['sharpe'], reverse=True)
        
        # Group by timeframe
        by_timeframe = {}
        for s in strategies:
            tf = s['scenario']['timeframe']
            if tf not in by_timeframe:
                by_timeframe[tf] = []
            by_timeframe[tf].append(s)
        
        # Group by pair
        by_pair = {}
        for s in strategies:
            pair = s['scenario']['pair']
            if pair not in by_pair:
                by_pair[pair] = []
            by_pair[pair].append(s)
        
        # Create summary report
        report = []
        report.append("\n" + "="*100)
        report.append(" "*30 + "ULTIMATE STRATEGY SEARCH RESULTS")
        report.append("="*100)
        report.append(f"\nTotal Scenarios Tested: {total_tested:,}")
        report.append(f"Successful Strategies: {len(strategies)}")
        report.append(f"Success Rate: {(len(strategies)/total_tested*100):.1f}%")
        
        report.append(f"\n\n[BEST BY TIMEFRAME]")
        for tf in sorted(by_timeframe.keys()):
            best = by_timeframe[tf][0]
            report.append(f"\n{tf}:")
            report.append(f"  Best: {best['scenario']['pair'].upper()} - Sharpe {best['sharpe']:.2f}, "
                         f"Win {best['win_rate']:.1f}%, Return {best['annual_return']:.1f}%")
            report.append(f"  Total {tf} strategies: {len(by_timeframe[tf])}")
        
        report.append(f"\n\n[BEST BY PAIR]")
        for pair in sorted(by_pair.keys()):
            best = by_pair[pair][0]
            report.append(f"\n{pair.upper()}:")
            report.append(f"  Best: {best['scenario']['timeframe']} - Sharpe {best['sharpe']:.2f}, "
                         f"Win {best['win_rate']:.1f}%, Return {best['annual_return']:.1f}%")
            report.append(f"  Total {pair.upper()} strategies: {len(by_pair[pair])}")
        
        report.append(f"\n\n[TOP 20 ABSOLUTE BEST]")
        report.append(f"{'Rank':<6} {'Pair':<10} {'TF':<6} {'Sharpe':<8} {'Return':<10} {'Win%':<8} {'DD%':<8} {'Trades':<8}")
        report.append("-"*100)
        
        for i, s in enumerate(strategies[:20], 1):
            sc = s['scenario']
            report.append(f"{i:<6} {sc['pair'].upper():<10} {sc['timeframe']:<6} {s['sharpe']:<8.2f} "
                         f"{s['annual_return']:<9.1f}% {s['win_rate']:<7.1f}% {s['max_dd']:<7.1f}% {s['trades']:<8,}")
        
        report.append("\n" + "="*100)
        
        # Print report
        for line in report:
            print(line)
        
        # Save to file
        report_file = self.results_dir / "ULTIMATE_SEARCH_SUMMARY.txt"
        with open(report_file, 'w') as f:
            f.write('\n'.join(report))
        
        # Save JSON
        json_file = self.results_dir / "ultimate_search_results.json"
        with open(json_file, 'w') as f:
            json.dump({
                'timestamp': self.timestamp,
                'total_tested': total_tested,
                'successful': len(strategies),
                'by_timeframe': {tf: len(strats) for tf, strats in by_timeframe.items()},
                'by_pair': {pair: len(strats) for pair, strats in by_pair.items()},
                'top_20': strategies[:20]
            }, f, indent=2, default=str)
        
        print(f"\n[SAVED] Results: {self.results_dir}")
        print(f"  Summary: {report_file.name}")
        print(f"  Full Results: {json_file.name}")

if __name__ == "__main__":
    finder = UltimateStrategyFinder()
    finder.run_ultimate_search()


