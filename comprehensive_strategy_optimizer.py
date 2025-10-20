#!/usr/bin/env python3
"""
COMPREHENSIVE STRATEGY OPTIMIZER
Live monitoring with success metrics - Using ONLY REAL DATA
"""

import os
import sys
import json
import time
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

# Import golden rule enforcer
from GOLDEN_RULE_NO_SYNTHETIC_DATA import RealDataEnforcer

class StrategyOptimizer:
    """Comprehensive optimizer with live success tracking"""
    
    def __init__(self):
        self.enforcer = RealDataEnforcer()
        self.start_time = datetime.now()
        
        # Success criteria
        self.SUCCESS_TIERS = {
            'EXCELLENT': {
                'sharpe': 2.0,
                'annual_return': 30.0,
                'max_dd': 15.0,
                'profit_factor': 2.0,
                'min_trades': 100
            },
            'GOOD': {
                'sharpe': 1.5,
                'annual_return': 20.0,
                'max_dd': 25.0,
                'profit_factor': 1.5,
                'min_trades': 50
            },
            'ACCEPTABLE': {
                'sharpe': 1.0,
                'annual_return': 15.0,
                'max_dd': 35.0,
                'profit_factor': 1.2,
                'min_trades': 30
            }
        }
        
        self.excellent_strategies = []
        self.good_strategies = []
        self.acceptable_strategies = []
        self.total_tested = 0
        self.total_scenarios = 0
        
        # Ensure ONLY real data is used
        self.enforcer.prevent_synthetic_data_creation()
        
    def generate_scenarios(self):
        """Generate comprehensive test scenarios"""
        
        scenarios = []
        scenario_id = 0
        
        # Pairs to test (prioritize based on previous results)
        pairs = ['gbp_usd', 'eur_usd', 'xau_usd', 'aud_usd']
        
        # Timeframes
        timeframes = ['5m', '15m', '30m', '1h']
        
        # EMA combinations
        ema_fast_values = [3, 5, 8, 12]
        ema_slow_values = [12, 21, 34, 50]
        
        # Risk/Reward ratios
        rr_ratios = [1.5, 2.0, 2.5, 3.0, 4.0]
        
        # Stop loss ATR multipliers
        sl_atr_mults = [0.5, 1.0, 1.5, 2.0]
        
        # RSI levels
        rsi_oversold = [20, 25, 30, 35]
        rsi_overbought = [65, 70, 75, 80]
        
        print("\n[SCENARIO GENERATION] Building comprehensive test matrix...")
        
        for pair in pairs:
            for timeframe in timeframes:
                for ema_fast in ema_fast_values:
                    for ema_slow in ema_slow_values:
                        if ema_slow <= ema_fast:
                            continue
                        
                        for rr in rr_ratios:
                            for sl_mult in sl_atr_mults:
                                for rsi_os in rsi_oversold:
                                    for rsi_ob in rsi_overbought:
                                        if rsi_ob <= rsi_os:
                                            continue
                                        
                                        scenario_id += 1
                                        scenarios.append({
                                            'id': scenario_id,
                                            'pair': pair,
                                            'timeframe': timeframe,
                                            'ema_fast': ema_fast,
                                            'ema_slow': ema_slow,
                                            'rr_ratio': rr,
                                            'sl_atr_mult': sl_mult,
                                            'rsi_oversold': rsi_os,
                                            'rsi_overbought': rsi_ob
                                        })
        
        self.total_scenarios = len(scenarios)
        print(f"[SUCCESS] Generated {self.total_scenarios:,} test scenarios")
        print(f"  Pairs: {len(pairs)}")
        print(f"  Timeframes: {len(timeframes)}")
        print(f"  Parameter combinations: {self.total_scenarios // (len(pairs) * len(timeframes)):,} per pair/timeframe")
        
        return scenarios
    
    def test_scenario(self, scenario):
        """Test a single scenario with real data"""
        
        try:
            # Load REAL data using enforcer
            df = self.enforcer.load_real_data(
                scenario['pair'],
                scenario['timeframe']
            )
            
            # Run strategy simulation
            results = self.simulate_strategy(df, scenario)
            
            # Evaluate success
            tier = self.evaluate_strategy(results)
            
            if tier:
                results['success_tier'] = tier
                results['scenario'] = scenario
                
            return results
            
        except Exception as e:
            return {
                'scenario_id': scenario['id'],
                'status': 'failed',
                'error': str(e)
            }
    
    def simulate_strategy(self, df, params):
        """Simulate strategy on real data"""
        
        # Calculate indicators
        df['ema_fast'] = df['close'].ewm(span=params['ema_fast']).mean()
        df['ema_slow'] = df['close'].ewm(span=params['ema_slow']).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['atr'] = true_range.rolling(window=14).mean()
        
        # Generate signals
        df['signal'] = 0
        
        # Buy signals
        buy_condition = (
            (df['ema_fast'] > df['ema_slow']) &
            (df['ema_fast'].shift(1) <= df['ema_slow'].shift(1)) &
            (df['rsi'] < params['rsi_overbought'])
        )
        df.loc[buy_condition, 'signal'] = 1
        
        # Sell signals
        sell_condition = (
            (df['ema_fast'] < df['ema_slow']) &
            (df['ema_fast'].shift(1) >= df['ema_slow'].shift(1)) &
            (df['rsi'] > params['rsi_oversold'])
        )
        df.loc[sell_condition, 'signal'] = -1
        
        # Execute trades
        trades = []
        position = 0
        entry_price = 0
        entry_time = None
        
        for i, (timestamp, row) in enumerate(df.iterrows()):
            if pd.isna(row['atr']) or row['atr'] == 0:
                continue
            
            # Entry
            if row['signal'] == 1 and position == 0:  # Buy
                position = 1
                entry_price = row['close']
                entry_time = timestamp
                sl = entry_price - (row['atr'] * params['sl_atr_mult'])
                tp = entry_price + (row['atr'] * params['sl_atr_mult'] * params['rr_ratio'])
                
            elif row['signal'] == -1 and position == 0:  # Sell
                position = -1
                entry_price = row['close']
                entry_time = timestamp
                sl = entry_price + (row['atr'] * params['sl_atr_mult'])
                tp = entry_price - (row['atr'] * params['sl_atr_mult'] * params['rr_ratio'])
            
            # Exit
            elif position != 0:
                exit_reason = None
                exit_price = None
                
                if position == 1:  # Long position
                    if row['low'] <= sl:
                        exit_reason = 'SL'
                        exit_price = sl
                    elif row['high'] >= tp:
                        exit_reason = 'TP'
                        exit_price = tp
                    elif row['signal'] == -1:
                        exit_reason = 'Signal'
                        exit_price = row['close']
                        
                elif position == -1:  # Short position
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
                        'direction': 'LONG' if position == 1 else 'SHORT',
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'exit_reason': exit_reason
                    })
                    
                    position = 0
        
        # Calculate metrics
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'sharpe': 0,
                'max_dd': 0,
                'profit_factor': 0
            }
        
        trades_df = pd.DataFrame(trades)
        
        wins = trades_df[trades_df['pnl'] > 0]
        losses = trades_df[trades_df['pnl'] < 0]
        
        win_rate = (len(wins) / len(trades_df)) * 100 if len(trades_df) > 0 else 0
        
        total_return = trades_df['pnl_pct'].sum()
        
        # Calculate drawdown
        cumulative = trades_df['pnl_pct'].cumsum()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max)
        max_dd = abs(drawdown.min()) if len(drawdown) > 0 else 0
        
        # Sharpe ratio (simplified)
        if len(trades_df) > 1 and trades_df['pnl_pct'].std() > 0:
            sharpe = (trades_df['pnl_pct'].mean() / trades_df['pnl_pct'].std()) * np.sqrt(len(trades_df))
        else:
            sharpe = 0
        
        # Profit factor
        total_profit = wins['pnl'].sum() if len(wins) > 0 else 0
        total_loss = abs(losses['pnl'].sum()) if len(losses) > 0 else 0
        profit_factor = (total_profit / total_loss) if total_loss > 0 else 0
        
        # Annualize return
        days = (df.index[-1] - df.index[0]).days
        years = days / 365.25
        annual_return = (total_return / years) if years > 0 else 0
        
        return {
            'total_trades': len(trades_df),
            'win_rate': win_rate,
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe': sharpe,
            'max_dd': max_dd,
            'profit_factor': profit_factor,
            'avg_win': wins['pnl_pct'].mean() if len(wins) > 0 else 0,
            'avg_loss': losses['pnl_pct'].mean() if len(losses) > 0 else 0
        }
    
    def evaluate_strategy(self, results):
        """Evaluate if strategy meets success criteria"""
        
        if results['total_trades'] == 0:
            return None
        
        # Check EXCELLENT tier
        tier = self.SUCCESS_TIERS['EXCELLENT']
        if (results['sharpe'] >= tier['sharpe'] and
            results['annual_return'] >= tier['annual_return'] and
            results['max_dd'] <= tier['max_dd'] and
            results['profit_factor'] >= tier['profit_factor'] and
            results['total_trades'] >= tier['min_trades']):
            return 'EXCELLENT'
        
        # Check GOOD tier
        tier = self.SUCCESS_TIERS['GOOD']
        if (results['sharpe'] >= tier['sharpe'] and
            results['annual_return'] >= tier['annual_return'] and
            results['max_dd'] <= tier['max_dd'] and
            results['profit_factor'] >= tier['profit_factor'] and
            results['total_trades'] >= tier['min_trades']):
            return 'GOOD'
        
        # Check ACCEPTABLE tier
        tier = self.SUCCESS_TIERS['ACCEPTABLE']
        if (results['sharpe'] >= tier['sharpe'] and
            results['annual_return'] >= tier['annual_return'] and
            results['max_dd'] <= tier['max_dd'] and
            results['profit_factor'] >= tier['profit_factor'] and
            results['total_trades'] >= tier['min_trades']):
            return 'ACCEPTABLE'
        
        return None
    
    def print_success(self, results):
        """Print successful strategy discovery"""
        
        tier = results['success_tier']
        scenario = results['scenario']
        
        print("\n" + "=" * 80)
        if tier == 'EXCELLENT':
            print(f">>> EXCELLENT STRATEGY FOUND! <<<")
        elif tier == 'GOOD':
            print(f">>> GOOD STRATEGY FOUND <<<")
        else:
            print(f">>> ACCEPTABLE STRATEGY <<<")
        print("=" * 80)
        
        print(f"Scenario #{scenario['id']}")
        print(f"Pair: {scenario['pair'].upper()} | Timeframe: {scenario['timeframe']}")
        print(f"EMA: {scenario['ema_fast']}/{scenario['ema_slow']} | R:R: {scenario['rr_ratio']}")
        print(f"SL: {scenario['sl_atr_mult']}x ATR | RSI: {scenario['rsi_oversold']}/{scenario['rsi_overbought']}")
        print()
        print(f"[METRICS]")
        print(f"  Sharpe Ratio: {results['sharpe']:.2f}")
        print(f"  Annual Return: {results['annual_return']:.1f}%")
        print(f"  Max Drawdown: {results['max_dd']:.1f}%")
        print(f"  Profit Factor: {results['profit_factor']:.2f}")
        print(f"  Win Rate: {results['win_rate']:.1f}%")
        print(f"  Total Trades: {results['total_trades']}")
        print("=" * 80 + "\n")
    
    def run_optimization(self):
        """Run comprehensive optimization"""
        
        print("\n" + "=" * 80)
        print("COMPREHENSIVE STRATEGY OPTIMIZER - USING REAL DATA ONLY")
        print("=" * 80)
        
        # Generate scenarios
        scenarios = self.generate_scenarios()
        
        print(f"\n[START] Testing {len(scenarios):,} scenarios...")
        print(f"[INFO] Using {mp.cpu_count()} CPU cores")
        print()
        
        # Progress tracking
        last_update = time.time()
        update_interval = 30  # Update every 30 seconds
        
        # Run in parallel
        max_workers = min(16, mp.cpu_count())
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.test_scenario, s): s for s in scenarios}
            
            for future in as_completed(futures):
                try:
                    results = future.result()
                    self.total_tested += 1
                    
                    # Check for success
                    if 'success_tier' in results:
                        tier = results['success_tier']
                        
                        if tier == 'EXCELLENT':
                            self.excellent_strategies.append(results)
                            self.print_success(results)
                        elif tier == 'GOOD':
                            self.good_strategies.append(results)
                            self.print_success(results)
                        elif tier == 'ACCEPTABLE':
                            self.acceptable_strategies.append(results)
                    
                    # Periodic progress update
                    if time.time() - last_update > update_interval:
                        self.print_progress()
                        last_update = time.time()
                        
                except Exception as e:
                    print(f"[ERROR] Scenario failed: {e}")
                    self.total_tested += 1
        
        # Final report
        self.print_final_report()
    
    def print_progress(self):
        """Print progress update"""
        
        pct = (self.total_tested / self.total_scenarios) * 100
        elapsed = datetime.now() - self.start_time
        
        print(f"\n[PROGRESS] {self.total_tested:,}/{self.total_scenarios:,} ({pct:.1f}%)")
        print(f"  Elapsed: {elapsed}")
        print(f"  EXCELLENT: {len(self.excellent_strategies)}")
        print(f"  GOOD: {len(self.good_strategies)}")
        print(f"  ACCEPTABLE: {len(self.acceptable_strategies)}")
    
    def print_final_report(self):
        """Print final optimization report"""
        
        print("\n" + "=" * 80)
        print("OPTIMIZATION COMPLETE - FINAL RESULTS")
        print("=" * 80)
        
        elapsed = datetime.now() - self.start_time
        
        print(f"\nTotal Scenarios Tested: {self.total_tested:,}")
        print(f"Total Time: {elapsed}")
        print()
        print(f"SUCCESS BREAKDOWN:")
        print(f"  EXCELLENT Strategies: {len(self.excellent_strategies)}")
        print(f"  GOOD Strategies: {len(self.good_strategies)}")
        print(f"  ACCEPTABLE Strategies: {len(self.acceptable_strategies)}")
        print()
        
        # Save results
        report_file = f"optimization_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump({
                'total_tested': self.total_tested,
                'elapsed_time': str(elapsed),
                'excellent': self.excellent_strategies,
                'good': self.good_strategies,
                'acceptable': self.acceptable_strategies
            }, f, indent=2, default=str)
        
        print(f"[SAVED] Results saved to: {report_file}")
        print("=" * 80)


if __name__ == "__main__":
    optimizer = StrategyOptimizer()
    optimizer.run_optimization()


