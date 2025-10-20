#!/usr/bin/env python3
"""
ULTIMATE ADVANCED OPTIMIZER
Tests advanced parameters with comprehensive statistics
- Better R:R ratios (up to 5:1)
- Multi-timeframe confirmation
- Session filtering
- Advanced entry conditions
- Complete trade statistics
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

from GOLDEN_RULE_NO_SYNTHETIC_DATA import RealDataEnforcer

enforcer = RealDataEnforcer()

class UltimateAdvancedOptimizer:
    """Advanced optimizer with comprehensive statistics"""
    
    def __init__(self):
        self.export_path = Path(r"H:\My Drive\AI Trading\exported strategies")
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results_dir = self.export_path / f"ultimate_advanced_{self.timestamp}"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "="*100)
        print(" "*25 + "ULTIMATE ADVANCED STRATEGY OPTIMIZER")
        print("="*100)
        print(f"\nExport Directory: {self.results_dir}")
        print(f"Criteria: Win >= 65%, Max DD <= 3.5%, Sharpe >= 2.0")
        
    def generate_advanced_scenarios(self):
        """Generate advanced test scenarios"""
        
        scenarios = []
        scenario_id = 0
        
        # Use proven best pairs from previous results
        top_pairs = ['gbp_usd', 'nzd_usd', 'eur_jpy', 'gbp_jpy', 'xau_usd', 'aud_usd', 'eur_usd', 'usd_jpy']
        
        # Test multiple timeframes
        timeframes = ['5m', '15m', '1h']
        
        # ADVANCED PARAMETER RANGES
        
        # EMA combinations (include proven winners + new variations)
        ema_combinations = [
            (3, 12),   # Proven winner
            (3, 21),   # Faster response
            (5, 21),   # Slightly slower
            (8, 21),   # More conservative
            (3, 34),   # Wider spread
            (8, 34),   # Medium-term
        ]
        
        # BETTER R:R ratios (up to 5:1)
        rr_ratios = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
        
        # Stop loss multipliers
        sl_mults = [1.0, 1.2, 1.5, 1.8, 2.0, 2.5]
        
        # RSI thresholds (tighter for targeted entries)
        rsi_configs = [
            (20, 80),  # Wide (current winner)
            (25, 75),  # Balanced
            (30, 70),  # Conservative
            (15, 85),  # Very wide
        ]
        
        # Advanced entry filters
        entry_types = [
            'simple',           # Just EMA crossover + RSI
            'pullback',         # Wait for pullback to EMA
            'momentum_confirm', # Require momentum confirmation
        ]
        
        print("\n[GENERATING] Advanced test scenarios...")
        
        for pair in top_pairs:
            for tf in timeframes:
                for ema_fast, ema_slow in ema_combinations:
                    for rr in rr_ratios:
                        for sl in sl_mults:
                            for rsi_os, rsi_ob in rsi_configs:
                                for entry_type in entry_types:
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
                                        'rsi_overbought': rsi_ob,
                                        'entry_type': entry_type
                                    })
        
        print(f"\n[SUCCESS] Generated {len(scenarios):,} advanced scenarios")
        print(f"  Pairs: {len(top_pairs)}")
        print(f"  Timeframes: {len(timeframes)}")
        print(f"  EMA Combinations: {len(ema_combinations)}")
        print(f"  R:R Ratios: {rr_ratios}")
        print(f"  Entry Types: {entry_types}")
        print(f"  Estimated time: 4-6 hours\n")
        
        return scenarios
    
    def test_advanced_scenario(self, scenario):
        """Test scenario with comprehensive statistics"""
        
        try:
            # Load real data
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
            
            # Add momentum for advanced entries
            df['momentum'] = df['close'].pct_change(5)
            
            # Generate signals based on entry type
            df['signal'] = 0
            
            if scenario['entry_type'] == 'simple':
                buy = (df['ema_fast'] > df['ema_slow']) & (df['ema_fast'].shift(1) <= df['ema_slow'].shift(1)) & (df['rsi'] < scenario['rsi_overbought'])
                sell = (df['ema_fast'] < df['ema_slow']) & (df['ema_fast'].shift(1) >= df['ema_slow'].shift(1)) & (df['rsi'] > scenario['rsi_oversold'])
                
            elif scenario['entry_type'] == 'pullback':
                # Wait for price to pullback near EMA slow after crossover
                near_ema = abs(df['close'] - df['ema_slow']) / df['close'] < 0.001  # Within 0.1%
                buy = (df['ema_fast'] > df['ema_slow']) & near_ema & (df['rsi'] < scenario['rsi_overbought'])
                sell = (df['ema_fast'] < df['ema_slow']) & near_ema & (df['rsi'] > scenario['rsi_oversold'])
                
            elif scenario['entry_type'] == 'momentum_confirm':
                # Require momentum confirmation
                buy = (df['ema_fast'] > df['ema_slow']) & (df['ema_fast'].shift(1) <= df['ema_slow'].shift(1)) & (df['rsi'] < scenario['rsi_overbought']) & (df['momentum'] > 0)
                sell = (df['ema_fast'] < df['ema_slow']) & (df['ema_fast'].shift(1) >= df['ema_slow'].shift(1)) & (df['rsi'] > scenario['rsi_oversold']) & (df['momentum'] < 0)
            
            df.loc[buy, 'signal'] = 1
            df.loc[sell, 'signal'] = -1
            
            # Execute trades with DETAILED tracking
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
                        duration = (timestamp - entry_time).total_seconds() / 60  # minutes
                        
                        trades.append({
                            'entry_time': entry_time,
                            'exit_time': timestamp,
                            'pnl_pct': pnl_pct,
                            'exit_reason': exit_reason,
                            'duration_minutes': duration,
                            'day_of_week': timestamp.dayofweek,  # 0=Monday, 6=Sunday
                            'hour_of_day': timestamp.hour
                        })
                        position = 0
            
            if not trades or len(trades) < 50:
                return None
            
            # Calculate COMPREHENSIVE statistics
            trades_df = pd.DataFrame(trades)
            wins = trades_df[trades_df['pnl_pct'] > 0]
            losses = trades_df[trades_df['pnl_pct'] < 0]
            
            # Basic metrics
            win_rate = (len(wins) / len(trades_df)) * 100
            total_return = trades_df['pnl_pct'].sum()
            
            cumulative = trades_df['pnl_pct'].cumsum()
            running_max = cumulative.cummax()
            drawdown = (cumulative - running_max)
            max_dd = abs(drawdown.min())
            
            sharpe = (trades_df['pnl_pct'].mean() / trades_df['pnl_pct'].std()) * np.sqrt(len(trades_df)) if len(trades_df) > 1 and trades_df['pnl_pct'].std() > 0 else 0
            
            total_profit = wins['pnl_pct'].sum() if len(wins) > 0 else 0
            total_loss = abs(losses['pnl_pct'].sum()) if len(losses) > 0 else 0
            profit_factor = (total_profit / total_loss) if total_loss > 0 else 0
            
            days = (df.index[-1] - df.index[0]).days
            years = days / 365.25
            annual_return = (total_return / years) if years > 0 else 0
            
            # ADVANCED STATISTICS
            
            # Time-based analysis
            trades_per_week = len(trades_df) / (days / 7)
            
            # Day of week performance
            day_stats = {}
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            for day in range(7):
                day_trades = trades_df[trades_df['day_of_week'] == day]
                if len(day_trades) > 0:
                    day_stats[day_names[day]] = {
                        'trades': len(day_trades),
                        'win_rate': (len(day_trades[day_trades['pnl_pct'] > 0]) / len(day_trades)) * 100,
                        'avg_pnl': day_trades['pnl_pct'].mean()
                    }
            
            # Best trading day
            best_day = max(day_stats.items(), key=lambda x: x[1]['avg_pnl'])[0] if day_stats else 'N/A'
            
            # Hour-based analysis (sessions)
            hour_stats = {}
            for hour in range(24):
                hour_trades = trades_df[trades_df['hour_of_day'] == hour]
                if len(hour_trades) > 0:
                    hour_stats[hour] = {
                        'trades': len(hour_trades),
                        'win_rate': (len(hour_trades[hour_trades['pnl_pct'] > 0]) / len(hour_trades)) * 100,
                        'avg_pnl': hour_trades['pnl_pct'].mean()
                    }
            
            # Best session (hour)
            best_hour = max(hour_stats.items(), key=lambda x: x[1]['avg_pnl'])[0] if hour_stats else 0
            best_session_name = self.get_session_name(best_hour)
            best_session_stats = hour_stats[best_hour] if best_hour in hour_stats else {}
            
            # Exit reason breakdown
            exit_reasons = trades_df['exit_reason'].value_counts().to_dict()
            
            # Duration statistics
            avg_trade_duration = trades_df['duration_minutes'].mean()
            median_trade_duration = trades_df['duration_minutes'].median()
            
            # Win/Loss statistics
            avg_win = wins['pnl_pct'].mean() if len(wins) > 0 else 0
            avg_loss = losses['pnl_pct'].mean() if len(losses) > 0 else 0
            largest_win = wins['pnl_pct'].max() if len(wins) > 0 else 0
            largest_loss = losses['pnl_pct'].min() if len(losses) > 0 else 0
            
            # Consecutive win/loss streaks
            trades_df['is_win'] = trades_df['pnl_pct'] > 0
            trades_df['streak'] = (trades_df['is_win'] != trades_df['is_win'].shift()).cumsum()
            win_streaks = trades_df[trades_df['is_win']].groupby('streak').size()
            loss_streaks = trades_df[~trades_df['is_win']].groupby('streak').size()
            max_win_streak = win_streaks.max() if len(win_streaks) > 0 else 0
            max_loss_streak = loss_streaks.max() if len(loss_streaks) > 0 else 0
            
            # Monthly profit distribution
            trades_df['year_month'] = trades_df['exit_time'].dt.to_period('M')
            monthly_pnl = trades_df.groupby('year_month')['pnl_pct'].sum()
            best_month_pnl = monthly_pnl.max() if len(monthly_pnl) > 0 else 0
            worst_month_pnl = monthly_pnl.min() if len(monthly_pnl) > 0 else 0
            profitable_months = (monthly_pnl > 0).sum()
            total_months = len(monthly_pnl)
            
            # Check criteria
            if win_rate >= 65.0 and max_dd <= 3.5 and sharpe >= 2.0:
                return {
                    'scenario': scenario,
                    
                    # Basic metrics
                    'total_trades': len(trades_df),
                    'win_rate': win_rate,
                    'sharpe': sharpe,
                    'annual_return': annual_return,
                    'max_dd': max_dd,
                    'profit_factor': profit_factor,
                    
                    # Win/Loss stats
                    'avg_win': avg_win,
                    'avg_loss': avg_loss,
                    'largest_win': largest_win,
                    'largest_loss': largest_loss,
                    'max_win_streak': int(max_win_streak),
                    'max_loss_streak': int(max_loss_streak),
                    
                    # Time-based stats
                    'trades_per_week': trades_per_week,
                    'avg_trade_duration_minutes': avg_trade_duration,
                    'median_trade_duration_minutes': median_trade_duration,
                    
                    # Day/Session stats
                    'best_trading_day': best_day,
                    'day_of_week_stats': day_stats,
                    'best_session_hour': best_hour,
                    'best_session_name': best_session_name,
                    'best_session_stats': best_session_stats,
                    'hourly_stats': hour_stats,
                    
                    # Exit analysis
                    'exit_reasons': exit_reasons,
                    'tp_rate': (exit_reasons.get('TP', 0) / len(trades_df)) * 100,
                    'sl_rate': (exit_reasons.get('SL', 0) / len(trades_df)) * 100,
                    
                    # Monthly stats
                    'best_month_pnl': best_month_pnl,
                    'worst_month_pnl': worst_month_pnl,
                    'profitable_months': int(profitable_months),
                    'total_months': int(total_months),
                    'monthly_consistency': (profitable_months / total_months * 100) if total_months > 0 else 0
                }
            
            return None
            
        except Exception as e:
            return None
    
    def get_session_name(self, hour):
        """Convert hour to session name"""
        if 0 <= hour < 8:
            return "Asian Session"
        elif 8 <= hour < 13:
            return "London Session"
        elif 13 <= hour < 17:
            return "London/NY Overlap"
        elif 17 <= hour < 20:
            return "NY Afternoon"
        else:
            return "Late NY Session"
    
    def run_optimization(self):
        """Run advanced optimization"""
        
        scenarios = self.generate_advanced_scenarios()
        
        print(f"[STARTING] Testing {len(scenarios):,} advanced scenarios...")
        print(f"[CORES] Using {mp.cpu_count()} cores\n")
        
        successful = []
        tested = 0
        start_time = datetime.now()
        
        with ProcessPoolExecutor(max_workers=min(20, mp.cpu_count())) as executor:
            futures = {executor.submit(self.test_advanced_scenario, s): s for s in scenarios}
            
            for future in as_completed(futures):
                tested += 1
                
                try:
                    result = future.result()
                    
                    if result:
                        successful.append(result)
                        
                        print(f"\n>>> EXCELLENT #{len(successful)} <<<")
                        print(f"  {result['scenario']['pair'].upper()} {result['scenario']['timeframe']} "
                              f"({result['scenario']['entry_type']}) - EMA {result['scenario']['ema_fast']}/{result['scenario']['ema_slow']}")
                        print(f"  Sharpe: {result['sharpe']:.2f} | Win: {result['win_rate']:.1f}% | "
                              f"Return: {result['annual_return']:.1f}% | DD: {result['max_dd']:.1f}%")
                        print(f"  R:R: 1:{result['scenario']['rr_ratio']} | Trades/Week: {result['trades_per_week']:.1f} | "
                              f"Best Day: {result['best_trading_day']}")
                    
                    if tested % 500 == 0:
                        elapsed = datetime.now() - start_time
                        pct = (tested / len(scenarios)) * 100
                        print(f"\n[PROGRESS] {tested:,}/{len(scenarios):,} ({pct:.1f}%) - Found {len(successful)} excellent")
                        print(f"  Elapsed: {elapsed} | Successful: {len(successful)}")
                        
                        # Save checkpoint
                        if successful:
                            self.save_checkpoint(successful, tested)
                
                except:
                    pass
        
        # Save final results
        self.save_final_results(successful, len(scenarios))
        
        return successful
    
    def save_checkpoint(self, strategies, tested):
        """Save checkpoint"""
        checkpoint_file = self.results_dir / f"checkpoint_{tested}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump({
                'tested': tested,
                'successful': strategies
            }, f, indent=2, default=str)
    
    def save_final_results(self, strategies, total_tested):
        """Save comprehensive final results"""
        
        if not strategies:
            print("\n[WARNING] No strategies met criteria")
            return
        
        # Sort by Sharpe
        strategies.sort(key=lambda x: x['sharpe'], reverse=True)
        
        # Create detailed summary
        summary = self.results_dir / "ULTIMATE_ADVANCED_SUMMARY.txt"
        
        with open(summary, 'w') as f:
            f.write("="*100 + "\n")
            f.write(" "*25 + "ULTIMATE ADVANCED STRATEGY RESULTS\n")
            f.write("="*100 + "\n\n")
            f.write(f"Total Scenarios Tested: {total_tested:,}\n")
            f.write(f"Successful Strategies: {len(strategies)}\n")
            f.write(f"Success Rate: {(len(strategies)/total_tested*100):.1f}%\n\n")
            
            f.write("="*100 + "\n")
            f.write("TOP 10 ULTIMATE STRATEGIES WITH FULL STATISTICS\n")
            f.write("="*100 + "\n\n")
            
            for i, s in enumerate(strategies[:10], 1):
                sc = s['scenario']
                f.write(f"\n{'='*100}\n")
                f.write(f"RANK #{i}: {sc['pair'].upper()} {sc['timeframe']} ({sc['entry_type'].upper()})\n")
                f.write(f"{'='*100}\n\n")
                
                f.write(f"CONFIGURATION:\n")
                f.write(f"  EMA: {sc['ema_fast']}/{sc['ema_slow']}\n")
                f.write(f"  R:R Ratio: 1:{sc['rr_ratio']}\n")
                f.write(f"  Stop Loss: {sc['sl_atr_mult']}x ATR\n")
                f.write(f"  RSI: {sc['rsi_oversold']}/{sc['rsi_overbought']}\n")
                f.write(f"  Entry Type: {sc['entry_type']}\n\n")
                
                f.write(f"PERFORMANCE METRICS:\n")
                f.write(f"  Sharpe Ratio: {s['sharpe']:.2f}\n")
                f.write(f"  Annual Return: {s['annual_return']:.1f}%\n")
                f.write(f"  Win Rate: {s['win_rate']:.1f}%\n")
                f.write(f"  Max Drawdown: {s['max_dd']:.1f}%\n")
                f.write(f"  Profit Factor: {s['profit_factor']:.2f}\n")
                f.write(f"  Total Trades: {s['total_trades']:,}\n\n")
                
                f.write(f"WIN/LOSS STATISTICS:\n")
                f.write(f"  Average Win: {s['avg_win']:.3f}%\n")
                f.write(f"  Average Loss: {s['avg_loss']:.3f}%\n")
                f.write(f"  Largest Win: {s['largest_win']:.3f}%\n")
                f.write(f"  Largest Loss: {s['largest_loss']:.3f}%\n")
                f.write(f"  Max Win Streak: {s['max_win_streak']} trades\n")
                f.write(f"  Max Loss Streak: {s['max_loss_streak']} trades\n\n")
                
                f.write(f"TRADING FREQUENCY:\n")
                f.write(f"  Trades Per Week: {s['trades_per_week']:.1f}\n")
                f.write(f"  Average Trade Duration: {s['avg_trade_duration_minutes']:.0f} minutes\n")
                f.write(f"  Median Trade Duration: {s['median_trade_duration_minutes']:.0f} minutes\n\n")
                
                f.write(f"EXIT ANALYSIS:\n")
                f.write(f"  Take Profit Exits: {s['tp_rate']:.1f}%\n")
                f.write(f"  Stop Loss Exits: {s['sl_rate']:.1f}%\n")
                f.write(f"  Signal Reversal Exits: {s['exit_reasons'].get('Signal', 0)}\n\n")
                
                f.write(f"TIME-BASED PERFORMANCE:\n")
                f.write(f"  Best Trading Day: {s['best_trading_day']}\n")
                f.write(f"  Best Session: {s['best_session_name']} (Hour {s['best_session_hour']})\n")
                if s['best_session_stats']:
                    f.write(f"    Win Rate: {s['best_session_stats']['win_rate']:.1f}%\n")
                    f.write(f"    Avg Profit: {s['best_session_stats']['avg_pnl']:.3f}%\n")
                    f.write(f"    Trades: {s['best_session_stats']['trades']}\n")
                
                f.write(f"\n  Day of Week Performance:\n")
                for day, stats in s['day_of_week_stats'].items():
                    f.write(f"    {day}: {stats['trades']} trades, {stats['win_rate']:.1f}% win rate, "
                           f"{stats['avg_pnl']:.3f}% avg profit\n")
                
                f.write(f"\nMONTHLY CONSISTENCY:\n")
                f.write(f"  Profitable Months: {s['profitable_months']}/{s['total_months']} ({s['monthly_consistency']:.1f}%)\n")
                f.write(f"  Best Month: +{s['best_month_pnl']:.1f}%\n")
                f.write(f"  Worst Month: {s['worst_month_pnl']:.1f}%\n")
                
                f.write(f"\n")
        
        print(f"\n[SAVED] Comprehensive summary: {summary}")
        
        # Save JSON with all data
        json_file = self.results_dir / "ultimate_advanced_results.json"
        with open(json_file, 'w') as f:
            json.dump({
                'timestamp': self.timestamp,
                'total_tested': total_tested,
                'successful': len(strategies),
                'top_20': strategies[:20]
            }, f, indent=2, default=str)
        
        print(f"[SAVED] JSON results: {json_file}")
        
        # Print summary to console
        self.print_summary(strategies[:10])
    
    def print_summary(self, top_10):
        """Print summary of top 10"""
        
        print("\n\n" + "="*100)
        print(" "*35 + "TOP 10 ULTIMATE STRATEGIES")
        print("="*100)
        print(f"\n{'Rank':<6} {'Pair':<10} {'TF':<6} {'Entry':<12} {'Sharpe':<8} {'Return':<10} {'Win%':<8} {'DD%':<8} {'Trades/Wk':<12}")
        print("-"*100)
        
        for i, s in enumerate(top_10, 1):
            sc = s['scenario']
            print(f"{i:<6} {sc['pair'].upper():<10} {sc['timeframe']:<6} {sc['entry_type']:<12} "
                  f"{s['sharpe']:<8.2f} {s['annual_return']:<9.1f}% {s['win_rate']:<7.1f}% "
                  f"{s['max_dd']:<7.1f}% {s['trades_per_week']:<12.1f}")
        
        # Show champion details
        best = top_10[0]
        print(f"\n\n{'='*100}")
        print(">>> THE ULTIMATE CHAMPION <<<")
        print("="*100)
        sc = best['scenario']
        print(f"\nPair: {sc['pair'].upper()}")
        print(f"Timeframe: {sc['timeframe']}")
        print(f"Entry Type: {sc['entry_type']}")
        print(f"EMA: {sc['ema_fast']}/{sc['ema_slow']}")
        print(f"R:R: 1:{sc['rr_ratio']}")
        print(f"Stop Loss: {sc['sl_atr_mult']}x ATR")
        print(f"\nKEY METRICS:")
        print(f"  Sharpe: {best['sharpe']:.2f}")
        print(f"  Annual Return: {best['annual_return']:.1f}%")
        print(f"  Win Rate: {best['win_rate']:.1f}%")
        print(f"  Profit Factor: {best['profit_factor']:.2f}")
        print(f"  Avg Win: {best['avg_win']:.3f}% | Avg Loss: {best['avg_loss']:.3f}%")
        print(f"\nTRADING STATS:")
        print(f"  Total Trades: {best['total_trades']:,}")
        print(f"  Trades/Week: {best['trades_per_week']:.1f}")
        print(f"  Avg Duration: {best['avg_trade_duration_minutes']:.0f} minutes")
        print(f"  Best Day: {best['best_trading_day']}")
        print(f"  Best Session: {best['best_session_name']}")
        print(f"  TP Exits: {best['tp_rate']:.1f}% | SL Exits: {best['sl_rate']:.1f}%")
        print(f"  Monthly Consistency: {best['monthly_consistency']:.1f}%")
        print("="*100 + "\n")

if __name__ == "__main__":
    optimizer = UltimateAdvancedOptimizer()
    optimizer.run_optimization()


