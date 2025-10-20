#!/usr/bin/env python3
"""
MULTI-TIMEFRAME BACKTESTING SYSTEM
Professional backtesting with support for all timeframes: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class MultiTimeframeBacktestingSystem:
    def __init__(self, data_dir="data/timeframes"):
        self.data_dir = data_dir
        self.results_dir = "results/multi_timeframe"
        
        # Create results directory
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Available timeframes
        self.timeframes = {
            "1m": {"minutes": 1, "strategy_type": "scalp"},
            "5m": {"minutes": 5, "strategy_type": "scalp"},
            "15m": {"minutes": 15, "strategy_type": "scalp"},
            "30m": {"minutes": 30, "strategy_type": "swing"},
            "1h": {"minutes": 60, "strategy_type": "swing"},
            "4h": {"minutes": 240, "strategy_type": "swing"},
            "1d": {"minutes": 1440, "strategy_type": "position"},
            "1w": {"minutes": 10080, "strategy_type": "position"}
        }
        
        # Currency pairs
        self.currency_pairs = [
            "EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD", "USD_CAD",
            "USD_CHF", "NZD_USD", "EUR_JPY", "GBP_JPY", "XAU_USD"
        ]
        
        # Professional backtesting parameters
        self.initial_capital = 100000.0  # $100k starting capital
        self.risk_per_trade = 0.02  # 2% risk per trade
        self.max_drawdown_limit = 0.15  # 15% max drawdown
        self.transaction_cost = 0.0002  # 2 pips transaction cost
        self.slippage = 0.00005  # 0.5 pips slippage
        
        # Timeframe-specific parameters
        self.timeframe_params = {
            "1m": {"risk_per_trade": 0.01, "max_trades_per_day": 20, "min_confidence": 80},
            "5m": {"risk_per_trade": 0.015, "max_trades_per_day": 15, "min_confidence": 75},
            "15m": {"risk_per_trade": 0.02, "max_trades_per_day": 10, "min_confidence": 70},
            "30m": {"risk_per_trade": 0.02, "max_trades_per_day": 8, "min_confidence": 70},
            "1h": {"risk_per_trade": 0.02, "max_trades_per_day": 5, "min_confidence": 70},
            "4h": {"risk_per_trade": 0.025, "max_trades_per_day": 3, "min_confidence": 65},
            "1d": {"risk_per_trade": 0.03, "max_trades_per_day": 2, "min_confidence": 60},
            "1w": {"risk_per_trade": 0.03, "max_trades_per_day": 1, "min_confidence": 60}
        }
        
    def load_timeframe_data(self, currency_pair: str, timeframe: str) -> pd.DataFrame:
        """Load data for specific currency pair and timeframe"""
        file_path = os.path.join(
            self.data_dir, timeframe, "processed", f"{currency_pair.lower()}_{timeframe}.csv"
        )
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file not found: {file_path}")
            
        df = pd.read_csv(file_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    def calculate_multi_timeframe_indicators(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """Calculate timeframe-appropriate technical indicators"""
        # Base indicators for all timeframes
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        df['atr'] = true_range.rolling(window=14).mean()
        
        # Timeframe-specific indicators
        if timeframe in ["1m", "5m", "15m"]:  # Scalping timeframes
            # Fast indicators for scalping
            df['sma_5'] = df['close'].rolling(window=5).mean()
            df['sma_10'] = df['close'].rolling(window=10).mean()
            df['ema_5'] = df['close'].ewm(span=5).mean()
            df['ema_10'] = df['close'].ewm(span=10).mean()
            
            # Fast RSI
            fast_delta = df['close'].diff()
            fast_gain = (fast_delta.where(fast_delta > 0, 0)).rolling(window=7).mean()
            fast_loss = (-fast_delta.where(fast_delta < 0, 0)).rolling(window=7).mean()
            fast_rs = fast_gain / fast_loss
            df['rsi_fast'] = 100 - (100 / (1 + fast_rs))
            
        elif timeframe in ["4h", "1d", "1w"]:  # Position timeframes
            # Slower indicators for position trading
            df['sma_100'] = df['close'].rolling(window=100).mean()
            df['sma_200'] = df['close'].rolling(window=200).mean()
            df['ema_50'] = df['close'].ewm(span=50).mean()
            
            # ADX for trend strength
            plus_dm = df['high'].diff()
            minus_dm = df['low'].diff()
            plus_dm[plus_dm < 0] = 0
            minus_dm[minus_dm > 0] = 0
            minus_dm = minus_dm.abs()
            
            tr = true_range
            plus_di = 100 * (plus_dm.rolling(window=14).mean() / tr.rolling(window=14).mean())
            minus_di = 100 * (minus_dm.rolling(window=14).mean() / tr.rolling(window=14).mean())
            
            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
            df['adx'] = dx.rolling(window=14).mean()
        
        return df
    
    def generate_timeframe_signals(self, df: pd.DataFrame, currency_pair: str, timeframe: str) -> List[Dict[str, Any]]:
        """Generate signals appropriate for the timeframe"""
        signals = []
        
        # Ensure we have enough data for indicators
        min_periods = 200 if timeframe in ["1d", "1w"] else 100
        if len(df) < min_periods:
            return signals
        
        start_idx = min_periods
        
        for i in range(start_idx, len(df)):
            current = df.iloc[i]
            previous = df.iloc[i-1]
            
            # Skip if any required indicators are NaN
            if pd.isna(current['sma_20']) or pd.isna(current['rsi']) or pd.isna(current['macd']):
                continue
            
            # Generate timeframe-specific signal
            signal = self._analyze_timeframe_setup(df, i, currency_pair, timeframe)
            
            if signal and signal['signal'] != 'NO_SIGNAL':
                signals.append(signal)
        
        return signals
    
    def _analyze_timeframe_setup(self, df: pd.DataFrame, index: int, currency_pair: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Analyze trading setup for specific timeframe"""
        current = df.iloc[index]
        previous = df.iloc[index-1]
        
        # Get timeframe-specific parameters
        params = self.timeframe_params.get(timeframe, self.timeframe_params["1h"])
        min_confidence = params["min_confidence"]
        
        # Base trend analysis
        trend_bullish = (current['sma_20'] > current['sma_50'] and 
                        current['close'] > current['sma_20'] and
                        current['macd'] > current['macd_signal'])
        
        trend_bearish = (current['sma_20'] < current['sma_50'] and 
                        current['close'] < current['sma_20'] and
                        current['macd'] < current['macd_signal'])
        
        # Timeframe-specific analysis
        if timeframe in ["1m", "5m", "15m"]:  # Scalping
            signal = self._analyze_scalping_setup(df, index, currency_pair, current, previous, trend_bullish, trend_bearish)
        elif timeframe in ["30m", "1h"]:  # Swing trading
            signal = self._analyze_swing_setup(df, index, currency_pair, current, previous, trend_bullish, trend_bearish)
        else:  # Position trading
            signal = self._analyze_position_setup(df, index, currency_pair, current, previous, trend_bullish, trend_bearish)
        
        if signal and signal.get('confidence', 0) >= min_confidence:
            return signal
        
        return {'signal': 'NO_SIGNAL'}
    
    def _analyze_scalping_setup(self, df: pd.DataFrame, index: int, currency_pair: str, current: pd.Series, 
                               previous: pd.Series, trend_bullish: bool, trend_bearish: bool) -> Optional[Dict[str, Any]]:
        """Analyze scalping setup (1m, 5m, 15m)"""
        # Fast momentum analysis
        momentum_bullish = (current['rsi_fast'] > 30 and current['rsi_fast'] < 70 and
                           current['ema_5'] > current['ema_10'] and
                           current['macd_histogram'] > previous['macd_histogram'])
        
        momentum_bearish = (current['rsi_fast'] < 70 and current['rsi_fast'] > 30 and
                           current['ema_5'] < current['ema_10'] and
                           current['macd_histogram'] < previous['macd_histogram'])
        
        # Volatility check
        volatility_adequate = current['atr'] > df['atr'].rolling(10).mean().iloc[index] * 0.5
        
        if trend_bullish and momentum_bullish and volatility_adequate:
            return self._create_signal(df, index, currency_pair, 'LONG', current, "scalp")
        elif trend_bearish and momentum_bearish and volatility_adequate:
            return self._create_signal(df, index, currency_pair, 'SHORT', current, "scalp")
        
        return None
    
    def _analyze_swing_setup(self, df: pd.DataFrame, index: int, currency_pair: str, current: pd.Series, 
                            previous: pd.Series, trend_bullish: bool, trend_bearish: bool) -> Optional[Dict[str, Any]]:
        """Analyze swing trading setup (30m, 1h)"""
        # Standard momentum analysis
        momentum_bullish = (current['rsi'] > 30 and current['rsi'] < 70 and
                           current['macd_histogram'] > previous['macd_histogram'])
        
        momentum_bearish = (current['rsi'] < 70 and current['rsi'] > 30 and
                           current['macd_histogram'] < previous['macd_histogram'])
        
        # Volatility check
        volatility_adequate = current['atr'] > df['atr'].rolling(20).mean().iloc[index] * 0.8
        
        if trend_bullish and momentum_bullish and volatility_adequate:
            return self._create_signal(df, index, currency_pair, 'LONG', current, "swing")
        elif trend_bearish and momentum_bearish and volatility_adequate:
            return self._create_signal(df, index, currency_pair, 'SHORT', current, "swing")
        
        return None
    
    def _analyze_position_setup(self, df: pd.DataFrame, index: int, currency_pair: str, current: pd.Series, 
                               previous: pd.Series, trend_bullish: bool, trend_bearish: bool) -> Optional[Dict[str, Any]]:
        """Analyze position trading setup (4h, 1d, 1w)"""
        # Strong trend analysis
        strong_trend_bullish = (current['sma_50'] > current['sma_200'] and
                               current['close'] > current['sma_50'] and
                               current['adx'] > 25)
        
        strong_trend_bearish = (current['sma_50'] < current['sma_200'] and
                               current['close'] < current['sma_50'] and
                               current['adx'] > 25)
        
        # Momentum analysis
        momentum_bullish = (current['rsi'] > 40 and current['rsi'] < 60 and
                           current['macd'] > current['macd_signal'])
        
        momentum_bearish = (current['rsi'] < 60 and current['rsi'] > 40 and
                           current['macd'] < current['macd_signal'])
        
        if strong_trend_bullish and momentum_bullish:
            return self._create_signal(df, index, currency_pair, 'LONG', current, "position")
        elif strong_trend_bearish and momentum_bearish:
            return self._create_signal(df, index, currency_pair, 'SHORT', current, "position")
        
        return None
    
    def _create_signal(self, df: pd.DataFrame, index: int, currency_pair: str, direction: str, current: pd.Series, strategy_type: str) -> Dict[str, Any]:
        """Create trading signal with appropriate risk management"""
        entry_price = current['close']
        atr = current['atr']
        
        # Strategy-specific risk management
        if strategy_type == "scalp":
            stop_multiplier = 1.5
            target_multiplier = 2.0  # 1.33:1 RR
        elif strategy_type == "swing":
            stop_multiplier = 2.0
            target_multiplier = 3.0  # 1.5:1 RR
        else:  # position
            stop_multiplier = 2.5
            target_multiplier = 4.0  # 1.6:1 RR
        
        # Calculate stop loss and take profit
        if direction == 'LONG':
            stop_loss = entry_price - (atr * stop_multiplier)
            take_profit = entry_price + (atr * target_multiplier)
        else:  # SHORT
            stop_loss = entry_price + (atr * stop_multiplier)
            take_profit = entry_price - (atr * target_multiplier)
        
        # Calculate confidence
        confidence = self._calculate_signal_confidence(df, index, direction, strategy_type)
        
        return {
            'signal': direction,
            'timestamp': current['timestamp'],
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'confidence': confidence,
            'strategy_type': strategy_type,
            'atr': atr,
            'risk_reward_ratio': target_multiplier / stop_multiplier,
            'currency_pair': currency_pair
        }
    
    def _calculate_signal_confidence(self, df: pd.DataFrame, index: int, direction: str, strategy_type: str) -> float:
        """Calculate signal confidence based on strategy type"""
        current = df.iloc[index]
        confidence = 50.0  # Base confidence
        
        # Trend alignment bonus
        if direction == 'LONG':
            if current['close'] > current['sma_20'] > current['sma_50']:
                confidence += 15
            if current['macd'] > current['macd_signal']:
                confidence += 10
        else:  # SHORT
            if current['close'] < current['sma_20'] < current['sma_50']:
                confidence += 15
            if current['macd'] < current['macd_signal']:
                confidence += 10
        
        # RSI momentum bonus
        if 30 < current['rsi'] < 70:
            confidence += 10
        
        # Strategy-specific bonuses
        if strategy_type == "scalp":
            if hasattr(current, 'rsi_fast') and 30 < current['rsi_fast'] < 70:
                confidence += 5
        elif strategy_type == "position":
            if hasattr(current, 'adx') and current['adx'] > 30:
                confidence += 10
        
        # Volatility bonus
        if current['atr'] > df['atr'].rolling(20).mean().iloc[index]:
            confidence += 5
        
        return min(100.0, confidence)
    
    def simulate_timeframe_trading(self, df: pd.DataFrame, signals: List[Dict[str, Any]], 
                                  currency_pair: str, timeframe: str) -> Dict[str, Any]:
        """Simulate trading for specific timeframe"""
        print(f"   📈 Simulating {timeframe} trading for {currency_pair}...")
        
        trades = []
        portfolio_value = self.initial_capital
        max_portfolio_value = self.initial_capital
        current_drawdown = 0.0
        max_drawdown = 0.0
        
        # Get timeframe-specific parameters
        params = self.timeframe_params.get(timeframe, self.timeframe_params["1h"])
        risk_per_trade = params["risk_per_trade"]
        max_trades_per_day = params["max_trades_per_day"]
        
        # Track daily trade count
        daily_trades = {}
        
        for signal in signals:
            # Check max drawdown
            if current_drawdown > self.max_drawdown_limit:
                continue
            
            # Check daily trade limit
            signal_date = signal['timestamp'].date()
            if signal_date not in daily_trades:
                daily_trades[signal_date] = 0
            
            if daily_trades[signal_date] >= max_trades_per_day:
                continue
            
            # Calculate position size
            risk_amount = portfolio_value * risk_per_trade
            stop_distance = abs(signal['entry_price'] - signal['stop_loss'])
            position_size = risk_amount / stop_distance
            
            # Simulate trade execution
            trade_result = self._simulate_trade_execution(df, signal, position_size)
            
            if trade_result:
                trades.append(trade_result)
                daily_trades[signal_date] += 1
                
                # Update portfolio
                portfolio_value += trade_result['pnl']
                max_portfolio_value = max(max_portfolio_value, portfolio_value)
                current_drawdown = (max_portfolio_value - portfolio_value) / max_portfolio_value
                max_drawdown = max(max_drawdown, current_drawdown)
        
        # Calculate performance metrics
        performance = self._calculate_performance_metrics(trades, portfolio_value)
        
        return {
            'currency_pair': currency_pair,
            'timeframe': timeframe,
            'strategy_type': self.timeframes[timeframe]['strategy_type'],
            'total_trades': len(trades),
            'trades': trades,
            'final_portfolio_value': portfolio_value,
            'performance': performance,
            'max_drawdown': max_drawdown
        }
    
    def _simulate_trade_execution(self, df: pd.DataFrame, signal: Dict[str, Any], position_size: float) -> Optional[Dict[str, Any]]:
        """Simulate realistic trade execution"""
        entry_time = signal['timestamp']
        entry_price = signal['entry_price']
        stop_loss = signal['stop_loss']
        take_profit = signal['take_profit']
        direction = signal['signal']
        
        # Find entry point in data
        entry_idx = df[df['timestamp'] == entry_time].index
        if len(entry_idx) == 0:
            return None
        
        entry_idx = entry_idx[0]
        
        # Add slippage and transaction costs
        if direction == 'LONG':
            actual_entry = entry_price + self.slippage
        else:
            actual_entry = entry_price - self.slippage
        
        # Simulate trade progression
        for i in range(entry_idx + 1, len(df)):
            current_price = df.iloc[i]['close']
            
            if direction == 'LONG':
                if current_price <= stop_loss:
                    exit_price = stop_loss
                    exit_reason = 'STOP_LOSS'
                    pnl = (exit_price - actual_entry) * position_size - (position_size * actual_entry * self.transaction_cost)
                    break
                elif current_price >= take_profit:
                    exit_price = take_profit
                    exit_reason = 'TAKE_PROFIT'
                    pnl = (exit_price - actual_entry) * position_size - (position_size * actual_entry * self.transaction_cost)
                    break
            else:  # SHORT
                if current_price >= stop_loss:
                    exit_price = stop_loss
                    exit_reason = 'STOP_LOSS'
                    pnl = (actual_entry - exit_price) * position_size - (position_size * actual_entry * self.transaction_cost)
                    break
                elif current_price <= take_profit:
                    exit_price = take_profit
                    exit_reason = 'TAKE_PROFIT'
                    pnl = (actual_entry - exit_price) * position_size - (position_size * actual_entry * self.transaction_cost)
                    break
        else:
            # Trade still open at end of data
            exit_price = df.iloc[-1]['close']
            exit_reason = 'END_OF_DATA'
            if direction == 'LONG':
                pnl = (exit_price - actual_entry) * position_size - (position_size * actual_entry * self.transaction_cost)
            else:
                pnl = (actual_entry - exit_price) * position_size - (position_size * actual_entry * self.transaction_cost)
        
        return {
            'entry_time': entry_time,
            'exit_time': df.iloc[i]['timestamp'] if 'i' in locals() else df.iloc[-1]['timestamp'],
            'entry_price': actual_entry,
            'exit_price': exit_price,
            'direction': direction,
            'position_size': position_size,
            'pnl': pnl,
            'exit_reason': exit_reason,
            'confidence': signal['confidence'],
            'strategy_type': signal['strategy_type'],
            'currency_pair': signal['currency_pair']
        }
    
    def _calculate_performance_metrics(self, trades: List[Dict[str, Any]], final_value: float) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        if not trades:
            return self._empty_performance()
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] < 0]
        
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
        
        total_pnl = sum(t['pnl'] for t in trades)
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100
        
        # Profit factor
        gross_profit = sum(t['pnl'] for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t['pnl'] for t in losing_trades)) if losing_trades else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Risk metrics
        returns = [t['pnl'] for t in trades]
        if returns:
            avg_return = np.mean(returns)
            return_std = np.std(returns)
            sharpe_ratio = avg_return / return_std if return_std > 0 else 0
            
            # Sortino ratio
            downside_returns = [r for r in returns if r < 0]
            downside_std = np.std(downside_returns) if downside_returns else 0
            sortino_ratio = avg_return / downside_std if downside_std > 0 else 0
        else:
            sharpe_ratio = 0
            sortino_ratio = 0
        
        # Drawdown calculation
        portfolio_values = [self.initial_capital]
        for trade in trades:
            portfolio_values.append(portfolio_values[-1] + trade['pnl'])
        
        peak = max(portfolio_values)
        max_drawdown = (peak - min(portfolio_values)) / peak if peak > 0 else 0
        
        # Calmar ratio
        calmar_ratio = total_return / (max_drawdown * 100) if max_drawdown > 0 else 0
        
        # Trade duration
        durations = []
        for trade in trades:
            duration = (trade['exit_time'] - trade['entry_time']).total_seconds() / 3600
            durations.append(duration)
        
        avg_duration = np.mean(durations) if durations else 0
        
        return {
            'total_return': total_return,
            'annualized_return': total_return * (365 / len(trades)) if total_trades > 0 else 0,
            'max_drawdown': max_drawdown * 100,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'avg_trade_duration': avg_duration,
            'total_pnl': total_pnl,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss
        }
    
    def _empty_performance(self) -> Dict[str, Any]:
        """Return empty performance metrics"""
        return {
            'total_return': 0.0,
            'annualized_return': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'calmar_ratio': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'avg_trade_duration': 0.0,
            'total_pnl': 0.0,
            'gross_profit': 0.0,
            'gross_loss': 0.0
        }
    
    def run_timeframe_backtest(self, currency_pair: str, timeframe: str) -> Dict[str, Any]:
        """Run backtest for specific currency pair and timeframe"""
        print(f"\n📊 BACKTEST: {currency_pair} {timeframe}")
        print("=" * 60)
        
        try:
            # Load data
            df = self.load_timeframe_data(currency_pair, timeframe)
            print(f"   📈 Loaded {len(df):,} data points")
            
            # Calculate indicators
            df = self.calculate_multi_timeframe_indicators(df, timeframe)
            print(f"   🔧 Calculated {timeframe} indicators")
            
            # Generate signals
            signals = self.generate_timeframe_signals(df, currency_pair, timeframe)
            print(f"   🎯 Generated {len(signals)} {timeframe} signals")
            
            # Simulate trading
            backtest_result = self.simulate_timeframe_trading(df, signals, currency_pair, timeframe)
            
            # Print results
            perf = backtest_result['performance']
            print(f"   📊 RESULTS:")
            print(f"      Total Return: {perf['total_return']:.2f}%")
            print(f"      Max Drawdown: {perf['max_drawdown']:.2f}%")
            print(f"      Sharpe Ratio: {perf['sharpe_ratio']:.2f}")
            print(f"      Win Rate: {perf['win_rate']:.1f}%")
            print(f"      Profit Factor: {perf['profit_factor']:.2f}")
            print(f"      Total Trades: {perf['total_trades']}")
            
            return backtest_result
            
        except Exception as e:
            print(f"   ❌ Error in {timeframe} backtest: {e}")
            return {'error': str(e)}
    
    def run_comprehensive_multi_timeframe_backtest(self) -> Dict[str, Any]:
        """Run comprehensive backtest across all timeframes and currency pairs"""
        print("🏆 MULTI-TIMEFRAME BACKTESTING SYSTEM")
        print("Professional Multi-Timeframe Trading Simulation")
        print("=" * 80)
        
        comprehensive_results = {
            'backtest_timestamp': datetime.now().isoformat(),
            'initial_capital': self.initial_capital,
            'timeframe_results': {},
            'overall_summary': {},
            'recommendations': []
        }
        
        successful_backtests = 0
        total_return = 0.0
        total_trades = 0
        
        # Run backtests for each timeframe and currency pair
        for timeframe in self.timeframes.keys():
            print(f"\n🕐 PROCESSING TIMEFRAME: {timeframe}")
            print("-" * 60)
            
            comprehensive_results['timeframe_results'][timeframe] = {}
            
            for currency_pair in self.currency_pairs:
                result = self.run_timeframe_backtest(currency_pair, timeframe)
                comprehensive_results['timeframe_results'][timeframe][currency_pair] = result
                
                if 'error' not in result:
                    successful_backtests += 1
                    total_return += result['performance']['total_return']
                    total_trades += result['performance']['total_trades']
        
        # Generate overall summary
        comprehensive_results['overall_summary'] = {
            'successful_backtests': successful_backtests,
            'total_requests': len(self.timeframes) * len(self.currency_pairs),
            'average_return': total_return / successful_backtests if successful_backtests > 0 else 0,
            'total_trades': total_trades,
            'success_rate': successful_backtests / (len(self.timeframes) * len(self.currency_pairs)) * 100
        }
        
        # Generate recommendations
        comprehensive_results['recommendations'] = self._generate_multi_timeframe_recommendations(comprehensive_results)
        
        # Save results
        self._save_multi_timeframe_results(comprehensive_results)
        
        return comprehensive_results
    
    def _generate_multi_timeframe_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on multi-timeframe results"""
        recommendations = []
        
        summary = results['overall_summary']
        
        if summary['average_return'] > 20:
            recommendations.append("🎯 Excellent multi-timeframe performance - consider live trading with small position sizes")
        elif summary['average_return'] > 10:
            recommendations.append("✅ Good multi-timeframe performance - suitable for paper trading and gradual live implementation")
        elif summary['average_return'] > 0:
            recommendations.append("⚠️ Positive but modest returns - optimize strategies before live trading")
        else:
            recommendations.append("❌ Negative returns - strategy needs significant improvement")
        
        # Timeframe-specific recommendations
        for timeframe, timeframe_results in results['timeframe_results'].items():
            timeframe_returns = []
            for pair, result in timeframe_results.items():
                if 'error' not in result:
                    timeframe_returns.append(result['performance']['total_return'])
            
            if timeframe_returns:
                avg_timeframe_return = np.mean(timeframe_returns)
                strategy_type = self.timeframes[timeframe]['strategy_type']
                
                if avg_timeframe_return > 15:
                    recommendations.append(f"• {timeframe} ({strategy_type}): Excellent performance ({avg_timeframe_return:.1f}%) - prioritize for live trading")
                elif avg_timeframe_return > 5:
                    recommendations.append(f"• {timeframe} ({strategy_type}): Good performance ({avg_timeframe_return:.1f}%) - suitable for paper trading")
                elif avg_timeframe_return > 0:
                    recommendations.append(f"• {timeframe} ({strategy_type}): Modest performance ({avg_timeframe_return:.1f}%) - needs optimization")
                else:
                    recommendations.append(f"• {timeframe} ({strategy_type}): Poor performance ({avg_timeframe_return:.1f}%) - avoid or redesign")
        
        return recommendations
    
    def _save_multi_timeframe_results(self, results: Dict[str, Any]):
        """Save comprehensive multi-timeframe results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON results
        json_file = os.path.join(self.results_dir, f"multi_timeframe_backtest_{timestamp}.json")
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save summary report
        summary_file = os.path.join(self.results_dir, f"multi_timeframe_summary_{timestamp}.md")
        self._generate_multi_timeframe_summary(results, summary_file)
        
        print(f"\n💾 Multi-timeframe results saved:")
        print(f"   📄 Detailed JSON: {json_file}")
        print(f"   📋 Summary Report: {summary_file}")
    
    def _generate_multi_timeframe_summary(self, results: Dict[str, Any], filename: str):
        """Generate multi-timeframe summary report"""
        with open(filename, 'w') as f:
            f.write("# MULTI-TIMEFRAME BACKTESTING REPORT\n\n")
            f.write(f"**Backtest Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Overall Summary
            summary = results['overall_summary']
            f.write("## EXECUTIVE SUMMARY\n\n")
            f.write(f"- **Initial Capital:** ${results['initial_capital']:,.0f}\n")
            f.write(f"- **Successful Backtests:** {summary['successful_backtests']}/{summary['total_requests']}\n")
            f.write(f"- **Average Return:** {summary['average_return']:.2f}%\n")
            f.write(f"- **Total Trades:** {summary['total_trades']:,}\n")
            f.write(f"- **Success Rate:** {summary['success_rate']:.1f}%\n\n")
            
            # Timeframe Results
            f.write("## TIMEFRAME RESULTS\n\n")
            for timeframe, timeframe_results in results['timeframe_results'].items():
                strategy_type = self.timeframes[timeframe]['strategy_type']
                f.write(f"### {timeframe} ({strategy_type.upper()})\n\n")
                
                timeframe_returns = []
                for pair, result in timeframe_results.items():
                    if 'error' not in result:
                        perf = result['performance']
                        f.write(f"**{pair}:**\n")
                        f.write(f"- Return: {perf['total_return']:.2f}%\n")
                        f.write(f"- Win Rate: {perf['win_rate']:.1f}%\n")
                        f.write(f"- Trades: {perf['total_trades']}\n")
                        f.write(f"- Sharpe: {perf['sharpe_ratio']:.2f}\n\n")
                        timeframe_returns.append(perf['total_return'])
                
                if timeframe_returns:
                    avg_return = np.mean(timeframe_returns)
                    f.write(f"**Average Return:** {avg_return:.2f}%\n\n")
            
            # Recommendations
            f.write("## RECOMMENDATIONS\n\n")
            for i, rec in enumerate(results['recommendations'], 1):
                f.write(f"{i}. {rec}\n")

def main():
    """Main execution function"""
    print("🏆 MULTI-TIMEFRAME BACKTESTING SYSTEM")
    print("Professional Multi-Timeframe Trading Simulation")
    print("=" * 80)
    
    backtester = MultiTimeframeBacktestingSystem()
    results = backtester.run_comprehensive_multi_timeframe_backtest()
    
    print("\n" + "=" * 80)
    print("🎯 MULTI-TIMEFRAME BACKTESTING COMPLETE")
    print("=" * 80)
    
    summary = results['overall_summary']
    print(f"Successful Backtests: {summary['successful_backtests']}/{summary['total_requests']}")
    print(f"Average Return: {summary['average_return']:.2f}%")
    print(f"Total Trades: {summary['total_trades']:,}")
    
    print(f"\n📋 {len(results['recommendations'])} RECOMMENDATIONS GENERATED")
    print("Your multi-timeframe backtesting system is ready for professional trading!")

if __name__ == "__main__":
    main()

