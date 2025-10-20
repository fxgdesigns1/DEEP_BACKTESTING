"""
COMPREHENSIVE FUTURES OPTIMIZER
Tests multiple proven strategies across all instruments and timeframes
Runs autonomously overnight - complete world-class optimization
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import multiprocessing as mp
from itertools import product
import warnings
warnings.filterwarnings('ignore')

class FuturesStrategy:
    """Base class for all strategies"""
    
    def __init__(self, params):
        self.params = params
        self.name = "BaseStrategy"
    
    def generate_signals(self, df):
        """Generate buy/sell signals - override in subclasses"""
        raise NotImplementedError

class EMAStrategy(FuturesStrategy):
    """EMA Crossover Strategy (Your proven winner!)"""
    
    def __init__(self, params):
        super().__init__(params)
        self.name = f"EMA_{params['fast']}_{params['slow']}"
    
    def generate_signals(self, df):
        fast = self.params['fast']
        slow = self.params['slow']
        
        df['EMA_fast'] = df['Close'].ewm(span=fast).mean()
        df['EMA_slow'] = df['Close'].ewm(span=slow).mean()
        
        df['signal'] = 0
        df.loc[df['EMA_fast'] > df['EMA_slow'], 'signal'] = 1  # Long
        df.loc[df['EMA_fast'] < df['EMA_slow'], 'signal'] = -1  # Short
        
        return df

class RSIStrategy(FuturesStrategy):
    """RSI Mean Reversion Strategy"""
    
    def __init__(self, params):
        super().__init__(params)
        self.name = f"RSI_{params['period']}"
    
    def generate_signals(self, df):
        period = self.params['period']
        oversold = self.params['oversold']
        overbought = self.params['overbought']
        
        # Calculate RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        df['signal'] = 0
        df.loc[df['RSI'] < oversold, 'signal'] = 1  # Oversold = Buy
        df.loc[df['RSI'] > overbought, 'signal'] = -1  # Overbought = Sell
        
        return df

class MACDStrategy(FuturesStrategy):
    """MACD Trend Following Strategy"""
    
    def __init__(self, params):
        super().__init__(params)
        self.name = f"MACD_{params['fast']}_{params['slow']}_{params['signal']}"
    
    def generate_signals(self, df):
        fast = self.params['fast']
        slow = self.params['slow']
        signal_period = self.params['signal']
        
        # Calculate MACD
        ema_fast = df['Close'].ewm(span=fast).mean()
        ema_slow = df['Close'].ewm(span=slow).mean()
        df['MACD'] = ema_fast - ema_slow
        df['MACD_signal'] = df['MACD'].ewm(span=signal_period).mean()
        
        df['signal'] = 0
        df.loc[df['MACD'] > df['MACD_signal'], 'signal'] = 1  # Bullish
        df.loc[df['MACD'] < df['MACD_signal'], 'signal'] = -1  # Bearish
        
        return df

class BollingerStrategy(FuturesStrategy):
    """Bollinger Bands Mean Reversion"""
    
    def __init__(self, params):
        super().__init__(params)
        self.name = f"BB_{params['period']}_{params['std']}"
    
    def generate_signals(self, df):
        period = self.params['period']
        num_std = self.params['std']
        
        # Calculate Bollinger Bands
        df['BB_mid'] = df['Close'].rolling(window=period).mean()
        df['BB_std'] = df['Close'].rolling(window=period).std()
        df['BB_upper'] = df['BB_mid'] + (df['BB_std'] * num_std)
        df['BB_lower'] = df['BB_mid'] - (df['BB_std'] * num_std)
        
        df['signal'] = 0
        df.loc[df['Close'] < df['BB_lower'], 'signal'] = 1  # Oversold
        df.loc[df['Close'] > df['BB_upper'], 'signal'] = -1  # Overbought
        
        return df

class ATRBreakoutStrategy(FuturesStrategy):
    """ATR-based Breakout Strategy"""
    
    def __init__(self, params):
        super().__init__(params)
        self.name = f"ATR_BO_{params['period']}_{params['multiplier']}"
    
    def generate_signals(self, df):
        period = self.params['period']
        multiplier = self.params['multiplier']
        
        # Calculate ATR
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(window=period).mean()
        
        # Breakout levels
        df['breakout_high'] = df['Close'].shift() + (df['ATR'] * multiplier)
        df['breakout_low'] = df['Close'].shift() - (df['ATR'] * multiplier)
        
        df['signal'] = 0
        df.loc[df['Close'] > df['breakout_high'], 'signal'] = 1  # Breakout up
        df.loc[df['Close'] < df['breakout_low'], 'signal'] = -1  # Breakout down
        
        return df

class FuturesBacktester:
    """Comprehensive futures backtesting engine"""
    
    def __init__(self):
        self.data_dir = Path("data/FUTURES_MASTER")
        self.results_dir = Path("H:/My Drive/AI Trading/exported strategies/futures_optimization_" + 
                               datetime.now().strftime("%Y%m%d_%H%M%S"))
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def backtest_strategy(self, df, strategy, rr_ratio=2.0, sl_atr_mult=1.5, commission=2.50):
        """Run backtest for a strategy"""
        
        # Generate signals
        df = strategy.generate_signals(df.copy())
        
        # Calculate ATR for stop loss if not already there
        if 'ATR' not in df.columns:
            high_low = df['High'] - df['Low']
            high_close = abs(df['High'] - df['Close'].shift())
            low_close = abs(df['Low'] - df['Close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df['ATR'] = tr.rolling(window=14).mean()
        
        # Backtest logic
        trades = []
        position = None
        
        for i in range(1, len(df)):
            if pd.isna(df['ATR'].iloc[i]) or df['ATR'].iloc[i] == 0:
                continue
            
            # Entry logic
            if position is None:
                signal = df['signal'].iloc[i]
                prev_signal = df['signal'].iloc[i-1]
                
                # New signal
                if signal != 0 and signal != prev_signal:
                    entry_price = df['Close'].iloc[i]
                    atr = df['ATR'].iloc[i]
                    
                    if signal == 1:  # Long
                        stop_loss = entry_price - (atr * sl_atr_mult)
                        take_profit = entry_price + (atr * sl_atr_mult * rr_ratio)
                    else:  # Short
                        stop_loss = entry_price + (atr * sl_atr_mult)
                        take_profit = entry_price - (atr * sl_atr_mult * rr_ratio)
                    
                    position = {
                        'entry_idx': i,
                        'entry_price': entry_price,
                        'entry_time': df.index[i],
                        'direction': signal,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'atr': atr
                    }
            
            # Exit logic
            elif position is not None:
                current_price = df['Close'].iloc[i]
                direction = position['direction']
                
                exit_reason = None
                exit_price = None
                
                if direction == 1:  # Long position
                    if current_price <= position['stop_loss']:
                        exit_reason = 'SL'
                        exit_price = position['stop_loss']
                    elif current_price >= position['take_profit']:
                        exit_reason = 'TP'
                        exit_price = position['take_profit']
                    elif df['signal'].iloc[i] == -1:
                        exit_reason = 'Signal'
                        exit_price = current_price
                
                else:  # Short position
                    if current_price >= position['stop_loss']:
                        exit_reason = 'SL'
                        exit_price = position['stop_loss']
                    elif current_price <= position['take_profit']:
                        exit_reason = 'TP'
                        exit_price = position['take_profit']
                    elif df['signal'].iloc[i] == 1:
                        exit_reason = 'Signal'
                        exit_price = current_price
                
                if exit_reason:
                    # Calculate P&L
                    if direction == 1:
                        pnl_points = exit_price - position['entry_price']
                    else:
                        pnl_points = position['entry_price'] - exit_price
                    
                    # Convert to dollars (using tick_value from df metadata)
                    tick_value = df['tick_value'].iloc[0] if 'tick_value' in df.columns else 12.50
                    tick_size = df['tick_size'].iloc[0] if 'tick_size' in df.columns else 0.25
                    ticks = pnl_points / tick_size
                    pnl_gross = ticks * tick_value
                    pnl_net = pnl_gross - (commission * 2)  # Round trip
                    
                    trades.append({
                        'entry_time': position['entry_time'],
                        'exit_time': df.index[i],
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'direction': direction,
                        'pnl_net': pnl_net,
                        'exit_reason': exit_reason,
                        'bars_held': i - position['entry_idx']
                    })
                    
                    position = None
        
        # Calculate performance metrics
        if len(trades) == 0:
            return None
        
        trades_df = pd.DataFrame(trades)
        
        total_pnl = trades_df['pnl_net'].sum()
        wins = trades_df[trades_df['pnl_net'] > 0]
        losses = trades_df[trades_df['pnl_net'] <= 0]
        
        win_rate = len(wins) / len(trades) * 100 if len(trades) > 0 else 0
        avg_win = wins['pnl_net'].mean() if len(wins) > 0 else 0
        avg_loss = losses['pnl_net'].mean() if len(losses) > 0 else 0
        profit_factor = abs(wins['pnl_net'].sum() / losses['pnl_net'].sum()) if len(losses) > 0 and losses['pnl_net'].sum() != 0 else 0
        
        # Calculate max drawdown
        trades_df['cumulative_pnl'] = trades_df['pnl_net'].cumsum()
        trades_df['cumulative_max'] = trades_df['cumulative_pnl'].cummax()
        trades_df['drawdown'] = trades_df['cumulative_pnl'] - trades_df['cumulative_max']
        max_dd = abs(trades_df['drawdown'].min()) if len(trades_df) > 0 else 0
        
        # Sharpe ratio (simplified)
        returns = trades_df['pnl_net'] / 10000  # Normalize
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
        
        # Annual return estimate
        days = (trades_df['exit_time'].iloc[-1] - trades_df['entry_time'].iloc[0]).days
        annual_return = (total_pnl / 100000) * (365 / days) * 100 if days > 0 else 0
        
        results = {
            'strategy': strategy.name,
            'total_trades': len(trades),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_dd,
            'sharpe_ratio': sharpe,
            'annual_return': annual_return,
            'avg_bars_held': trades_df['bars_held'].mean()
        }
        
        return results
    
    def test_instrument_strategy(self, args):
        """Test a single instrument/timeframe/strategy combination"""
        symbol, timeframe, strategy, params = args
        
        try:
            # Load data
            filename = self.data_dir / f"{symbol}_{timeframe}.csv"
            if not filename.exists():
                return None
            
            df = pd.read_csv(filename, index_col=0, parse_dates=True)
            
            # Create strategy instance
            if strategy == 'EMA':
                strat = EMAStrategy(params)
            elif strategy == 'RSI':
                strat = RSIStrategy(params)
            elif strategy == 'MACD':
                strat = MACDStrategy(params)
            elif strategy == 'Bollinger':
                strat = BollingerStrategy(params)
            elif strategy == 'ATR_Breakout':
                strat = ATRBreakoutStrategy(params)
            else:
                return None
            
            # Run backtest
            results = self.backtest_strategy(df, strat)
            
            if results:
                results['symbol'] = symbol
                results['timeframe'] = timeframe
                results['strategy_type'] = strategy
                results['parameters'] = params
            
            return results
            
        except Exception as e:
            print(f"Error testing {symbol} {timeframe} {strategy}: {e}")
            return None
    
    def generate_test_scenarios(self):
        """Generate all test scenarios"""
        symbols = ['ES', 'NQ', 'GC']
        timeframes = ['5m', '15m', '30m', '1h', '4h']
        
        scenarios = []
        
        # EMA strategies (your proven winner!)
        ema_params = [
            {'fast': 3, 'slow': 8},
            {'fast': 3, 'slow': 12},
            {'fast': 3, 'slow': 21},
            {'fast': 5, 'slow': 13},
            {'fast': 5, 'slow': 21},
            {'fast': 8, 'slow': 21},
            {'fast': 12, 'slow': 26},
            {'fast': 12, 'slow': 50}
        ]
        
        for symbol, tf in product(symbols, timeframes):
            for params in ema_params:
                scenarios.append((symbol, tf, 'EMA', params))
        
        # RSI strategies
        rsi_params = [
            {'period': 14, 'oversold': 30, 'overbought': 70},
            {'period': 14, 'oversold': 20, 'overbought': 80},
            {'period': 9, 'oversold': 25, 'overbought': 75},
            {'period': 21, 'oversold': 30, 'overbought': 70}
        ]
        
        for symbol, tf in product(symbols, timeframes):
            for params in rsi_params:
                scenarios.append((symbol, tf, 'RSI', params))
        
        # MACD strategies
        macd_params = [
            {'fast': 12, 'slow': 26, 'signal': 9},
            {'fast': 8, 'slow': 17, 'signal': 9},
            {'fast': 5, 'slow': 13, 'signal': 5}
        ]
        
        for symbol, tf in product(symbols, timeframes):
            for params in macd_params:
                scenarios.append((symbol, tf, 'MACD', params))
        
        # Bollinger Bands
        bb_params = [
            {'period': 20, 'std': 2.0},
            {'period': 20, 'std': 2.5},
            {'period': 10, 'std': 2.0}
        ]
        
        for symbol, tf in product(symbols, timeframes):
            for params in bb_params:
                scenarios.append((symbol, tf, 'Bollinger', params))
        
        # ATR Breakout
        atr_params = [
            {'period': 14, 'multiplier': 2.0},
            {'period': 14, 'multiplier': 2.5},
            {'period': 10, 'multiplier': 2.0}
        ]
        
        for symbol, tf in product(symbols, timeframes):
            for params in atr_params:
                scenarios.append((symbol, tf, 'ATR_Breakout', params))
        
        return scenarios
    
    def run_comprehensive_optimization(self):
        """Run the complete optimization"""
        print("\n" + "="*80)
        print(" "*15 + "COMPREHENSIVE FUTURES OPTIMIZATION")
        print(" "*20 + "(Running Overnight)")
        print("="*80)
        
        # Generate all scenarios
        scenarios = self.generate_test_scenarios()
        
        print(f"\n[DATA] Total Scenarios: {len(scenarios):,}")
        print(f"[STRATEGIES] EMA, RSI, MACD, Bollinger, ATR Breakout")
        print(f"[INSTRUMENTS] ES, NQ, GC")
        print(f"[TIMEFRAMES] 5m, 15m, 30m, 1h, 4h")
        print(f"\n[CORES] Using {mp.cpu_count()} CPU cores")
        print(f"[RESULTS] {self.results_dir}")
        
        start_time = datetime.now()
        print(f"\n[START] {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Run in parallel
        with mp.Pool(processes=mp.cpu_count()) as pool:
            results = []
            for i, result in enumerate(pool.imap_unordered(self.test_instrument_strategy, scenarios)):
                if result:
                    results.append(result)
                
                if (i + 1) % 100 == 0:
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    progress = (i + 1) / len(scenarios) * 100
                    print(f"Progress: {i+1}/{len(scenarios)} ({progress:.1f}%) | "
                          f"Elapsed: {elapsed:.1f}min | "
                          f"Found: {len(results)} profitable")
        
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds() / 60
        
        print("\n" + "="*80)
        print(" "*25 + "OPTIMIZATION COMPLETE")
        print("="*80)
        print(f"\n  Total Time: {elapsed:.1f} minutes")
        print(f" Scenarios Tested: {len(scenarios):,}")
        print(f" Profitable Strategies: {len(results)}")
        
        # Save all results
        if results:
            self.analyze_and_save_results(results)
        
        return results
    
    def analyze_and_save_results(self, results):
        """Analyze and save comprehensive results"""
        print("\n" + "="*80)
        print(" "*20 + "ANALYZING & SAVING RESULTS")
        print("="*80)
        
        df_results = pd.DataFrame(results)
        
        # Sort by Sharpe ratio
        df_results = df_results.sort_values('sharpe_ratio', ascending=False)
        
        # Save full results
        full_file = self.results_dir / "all_results.csv"
        df_results.to_csv(full_file, index=False)
        print(f"\n Full results: {full_file.name}")
        
        # Filter high quality
        quality_filter = (
            (df_results['win_rate'] >= 60) &
            (df_results['total_trades'] >= 30) &
            (df_results['sharpe_ratio'] >= 1.5) &
            (df_results['profit_factor'] >= 1.5) &
            (df_results['max_drawdown'] <= 5000)  # $5K max DD
        )
        
        high_quality = df_results[quality_filter].copy()
        
        if len(high_quality) > 0:
            hq_file = self.results_dir / "high_quality_strategies.csv"
            high_quality.to_csv(hq_file, index=False)
            print(f" High Quality: {len(high_quality)} strategies -> {hq_file.name}")
        
        # Generate comprehensive report
        self.generate_report(df_results, high_quality if len(high_quality) > 0 else None)
    
    def generate_report(self, all_results, high_quality):
        """Generate detailed analysis report"""
        report_file = self.results_dir / "OPTIMIZATION_REPORT.md"
        
        with open(report_file, 'w') as f:
            f.write("# COMPREHENSIVE FUTURES OPTIMIZATION REPORT\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("="*80 + "\n\n")
            
            # Summary statistics
            f.write("## SUMMARY\n\n")
            f.write(f"- **Total Strategies Tested:** {len(all_results):,}\n")
            if high_quality is not None:
                f.write(f"- **High Quality Strategies:** {len(high_quality)}\n")
            f.write(f"- **Best Sharpe Ratio:** {all_results['sharpe_ratio'].max():.2f}\n")
            f.write(f"- **Best Win Rate:** {all_results['win_rate'].max():.1f}%\n")
            f.write(f"- **Best Annual Return:** ${all_results['annual_return'].max():,.0f}\n\n")
            
            # Top 20 strategies
            f.write("## TOP 20 STRATEGIES (by Sharpe Ratio)\n\n")
            top_20 = all_results.head(20)
            
            for i, row in enumerate(top_20.itertuples(), 1):
                f.write(f"### #{i}: {row.symbol} {row.timeframe} - {row.strategy}\n\n")
                f.write(f"- **Sharpe Ratio:** {row.sharpe_ratio:.2f}\n")
                f.write(f"- **Win Rate:** {row.win_rate:.1f}%\n")
                f.write(f"- **Total P&L:** ${row.total_pnl:,.2f}\n")
                f.write(f"- **Annual Return:** ${row.annual_return:,.0f}\n")
                f.write(f"- **Max Drawdown:** ${row.max_drawdown:,.2f}\n")
                f.write(f"- **Profit Factor:** {row.profit_factor:.2f}\n")
                f.write(f"- **Trades:** {row.total_trades}\n")
                f.write(f"- **Avg Win:** ${row.avg_win:.2f}\n")
                f.write(f"- **Avg Loss:** ${row.avg_loss:.2f}\n\n")
            
            # By instrument
            f.write("\n## BEST STRATEGY PER INSTRUMENT\n\n")
            for symbol in all_results['symbol'].unique():
                symbol_best = all_results[all_results['symbol'] == symbol].iloc[0]
                f.write(f"### {symbol}\n\n")
                f.write(f"- **Strategy:** {symbol_best['strategy']}\n")
                f.write(f"- **Timeframe:** {symbol_best['timeframe']}\n")
                f.write(f"- **Sharpe:** {symbol_best['sharpe_ratio']:.2f}\n")
                f.write(f"- **Win Rate:** {symbol_best['win_rate']:.1f}%\n")
                f.write(f"- **Annual Return:** ${symbol_best['annual_return']:,.0f}\n\n")
            
            # By strategy type
            f.write("\n## BEST TIMEFRAME PER STRATEGY TYPE\n\n")
            for strat_type in all_results['strategy_type'].unique():
                strat_best = all_results[all_results['strategy_type'] == strat_type].iloc[0]
                f.write(f"### {strat_type}\n\n")
                f.write(f"- **Best on:** {strat_best['symbol']} {strat_best['timeframe']}\n")
                f.write(f"- **Sharpe:** {strat_best['sharpe_ratio']:.2f}\n")
                f.write(f"- **Win Rate:** {strat_best['win_rate']:.1f}%\n\n")
        
        print(f" Detailed report: {report_file.name}")

if __name__ == "__main__":
    optimizer = FuturesBacktester()
    results = optimizer.run_comprehensive_optimization()
    
    print("\n" + "="*80)
    print(" COMPREHENSIVE OPTIMIZATION COMPLETE!")
    print(f" Results saved to: {optimizer.results_dir}")
    print(" Review OPTIMIZATION_REPORT.md for full analysis")
    print("="*80 + "\n")


