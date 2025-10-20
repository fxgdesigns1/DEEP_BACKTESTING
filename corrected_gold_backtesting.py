#!/usr/bin/env python3
"""
Corrected Gold Backtesting System
Fixing fundamental flaws in the gold scalping backtesting system:
1. Corrected gold pip value definition (1 pip = $0.10)
2. Fixed position sizing calculation
3. Realistic stop loss/take profit values
4. Proper trade simulation using price data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import json
import os

logger = logging.getLogger("corrected_gold_backtesting")

class CorrectedGoldBacktesting:
    """Base class for gold scalping with corrected mechanics"""
    
    def __init__(self, strategy_name: str, params: Dict[str, Any]):
        self.name = strategy_name
        self.params = params
        self.trades = []
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        df = df.copy()
        
        # Price-based indicators
        df['sma_5'] = df['mid_price'].rolling(window=5).mean()
        df['sma_10'] = df['mid_price'].rolling(window=10).mean()
        df['sma_20'] = df['mid_price'].rolling(window=20).mean()
        df['ema_12'] = df['mid_price'].ewm(span=12).mean()
        df['ema_26'] = df['mid_price'].ewm(span=26).mean()
        
        # RSI
        df['rsi'] = self._calculate_rsi(df['mid_price'], 14)
        
        # MACD
        macd_data = self._calculate_macd(df['mid_price'])
        df['macd'] = macd_data['macd']
        df['macd_signal'] = macd_data['signal']
        df['macd_histogram'] = macd_data['histogram']
        
        # Bollinger Bands
        bb_data = self._calculate_bollinger_bands(df['mid_price'], 20, 2)
        df['bb_upper'] = bb_data['upper']
        df['bb_middle'] = bb_data['middle']
        df['bb_lower'] = bb_data['lower']
        df['bb_width'] = df['bb_upper'] - df['bb_lower']
        df['bb_position'] = (df['mid_price'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # ATR for volatility
        df['atr'] = self._calculate_atr(df, 14)
        
        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(window=10).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Price momentum
        df['momentum_5'] = df['mid_price'].pct_change(5)
        df['momentum_10'] = df['mid_price'].pct_change(10)
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD indicator"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        return {
            'upper': sma + (std * std_dev),
            'middle': sma,
            'lower': sma - (std * std_dev)
        }
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high = df['ask']
        low = df['bid']
        close = df['mid_price']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr

class CorrectedRSIStrategy(CorrectedGoldBacktesting):
    """Corrected RSI-based gold scalping"""
    
    def __init__(self):
        params = {
            'stop_loss_pips': 50,     # 50 pips = $5.00 in gold
            'take_profit_pips': 80,   # 80 pips = $8.00 in gold
            'max_spread': 5,          # 5 pips = $0.50 in gold
            'min_volatility': 0.5,    # 0.5 pips minimum ATR
            'rsi_oversold': 35,
            'rsi_overbought': 65,
            'volume_threshold': 1.0
        }
        super().__init__("Corrected_RSI_Strategy", params)
    
    def generate_signal(self, df: pd.DataFrame, idx: int) -> Optional[Dict[str, Any]]:
        """Generate RSI signal with corrected pip values"""
        if idx < 20:
            return None
        
        current = df.iloc[idx]
        params = self.params
        
        # Check spread (in gold pips)
        spread = (current['ask'] - current['bid']) * 10
        if spread > params['max_spread']:
            return None
        
        # Check volatility
        if current['atr'] * 10 < params['min_volatility']:  # Convert ATR to gold pips
            return None
        
        rsi = current['rsi']
        if pd.isna(rsi):
            return None
        
        # RSI BUY signal
        if (rsi < params['rsi_oversold'] and
            current['volume_ratio'] > params['volume_threshold']):
            
            # Calculate stop loss and take profit in dollars ($)
            stop_loss_amount = params['stop_loss_pips'] * 0.1  # Convert to dollars
            take_profit_amount = params['take_profit_pips'] * 0.1  # Convert to dollars
            
            return {
                'direction': 'BUY',
                'entry_price': current['ask'],
                'stop_loss': current['ask'] - stop_loss_amount,
                'take_profit': current['ask'] + take_profit_amount,
                'strength': 0.6,
                'timestamp': current['timestamp'],
                'reason': 'RSI oversold'
            }
        
        # RSI SELL signal
        elif (rsi > params['rsi_overbought'] and
              current['volume_ratio'] > params['volume_threshold']):
            
            # Calculate stop loss and take profit in dollars ($)
            stop_loss_amount = params['stop_loss_pips'] * 0.1  # Convert to dollars
            take_profit_amount = params['take_profit_pips'] * 0.1  # Convert to dollars
            
            return {
                'direction': 'SELL',
                'entry_price': current['bid'],
                'stop_loss': current['bid'] + stop_loss_amount,
                'take_profit': current['bid'] - take_profit_amount,
                'strength': 0.6,
                'timestamp': current['timestamp'],
                'reason': 'RSI overbought'
            }
        
        return None

class CorrectedMACDStrategy(CorrectedGoldBacktesting):
    """Corrected MACD-based gold scalping"""
    
    def __init__(self):
        params = {
            'stop_loss_pips': 60,     # 60 pips = $6.00 in gold
            'take_profit_pips': 90,   # 90 pips = $9.00 in gold
            'max_spread': 5,          # 5 pips = $0.50 in gold
            'min_volatility': 0.5,    # 0.5 pips minimum ATR
            'volume_threshold': 1.0,
            'macd_threshold': 0.1     # Minimum MACD value
        }
        super().__init__("Corrected_MACD_Strategy", params)
    
    def generate_signal(self, df: pd.DataFrame, idx: int) -> Optional[Dict[str, Any]]:
        """Generate MACD signal with corrected pip values"""
        if idx < 20:
            return None
        
        current = df.iloc[idx]
        params = self.params
        
        # Check spread
        spread = (current['ask'] - current['bid']) * 10
        if spread > params['max_spread']:
            return None
        
        # Check volatility
        if current['atr'] * 10 < params['min_volatility']:
            return None
        
        # MACD BUY signal
        if (current['macd'] > current['macd_signal'] and
            abs(current['macd_histogram']) > params['macd_threshold'] and
            current['volume_ratio'] > params['volume_threshold']):
            
            # Calculate stop loss and take profit in dollars ($)
            stop_loss_amount = params['stop_loss_pips'] * 0.1  # Convert to dollars
            take_profit_amount = params['take_profit_pips'] * 0.1  # Convert to dollars
            
            return {
                'direction': 'BUY',
                'entry_price': current['ask'],
                'stop_loss': current['ask'] - stop_loss_amount,
                'take_profit': current['ask'] + take_profit_amount,
                'strength': 0.6,
                'timestamp': current['timestamp'],
                'reason': 'MACD bullish crossover'
            }
        
        # MACD SELL signal
        elif (current['macd'] < current['macd_signal'] and
              abs(current['macd_histogram']) > params['macd_threshold'] and
              current['volume_ratio'] > params['volume_threshold']):
            
            # Calculate stop loss and take profit in dollars ($)
            stop_loss_amount = params['stop_loss_pips'] * 0.1  # Convert to dollars
            take_profit_amount = params['take_profit_pips'] * 0.1  # Convert to dollars
            
            return {
                'direction': 'SELL',
                'entry_price': current['bid'],
                'stop_loss': current['bid'] + stop_loss_amount,
                'take_profit': current['bid'] - take_profit_amount,
                'strength': 0.6,
                'timestamp': current['timestamp'],
                'reason': 'MACD bearish crossover'
            }
        
        return None

class CorrectedBBStrategy(CorrectedGoldBacktesting):
    """Corrected Bollinger Bands gold scalping"""
    
    def __init__(self):
        params = {
            'stop_loss_pips': 50,     # 50 pips = $5.00 in gold
            'take_profit_pips': 75,   # 75 pips = $7.50 in gold
            'max_spread': 5,          # 5 pips = $0.50 in gold
            'min_volatility': 0.5,    # 0.5 pips minimum ATR
            'volume_threshold': 1.0,
            'bb_threshold': 0.1       # BB position threshold
        }
        super().__init__("Corrected_BB_Strategy", params)
    
    def generate_signal(self, df: pd.DataFrame, idx: int) -> Optional[Dict[str, Any]]:
        """Generate Bollinger Bands signal with corrected pip values"""
        if idx < 20:
            return None
        
        current = df.iloc[idx]
        params = self.params
        
        # Check spread
        spread = (current['ask'] - current['bid']) * 10
        if spread > params['max_spread']:
            return None
        
        # Check volatility
        if current['atr'] * 10 < params['min_volatility']:
            return None
        
        # BB BUY signal
        if (current['mid_price'] < current['bb_lower'] and
            current['bb_position'] < params['bb_threshold'] and
            current['volume_ratio'] > params['volume_threshold']):
            
            # Calculate stop loss and take profit in dollars ($)
            stop_loss_amount = params['stop_loss_pips'] * 0.1  # Convert to dollars
            take_profit_amount = params['take_profit_pips'] * 0.1  # Convert to dollars
            
            return {
                'direction': 'BUY',
                'entry_price': current['ask'],
                'stop_loss': current['ask'] - stop_loss_amount,
                'take_profit': current['ask'] + take_profit_amount,
                'strength': 0.6,
                'timestamp': current['timestamp'],
                'reason': 'BB lower band bounce'
            }
        
        # BB SELL signal
        elif (current['mid_price'] > current['bb_upper'] and
              current['bb_position'] > (1 - params['bb_threshold']) and
              current['volume_ratio'] > params['volume_threshold']):
            
            # Calculate stop loss and take profit in dollars ($)
            stop_loss_amount = params['stop_loss_pips'] * 0.1  # Convert to dollars
            take_profit_amount = params['take_profit_pips'] * 0.1  # Convert to dollars
            
            return {
                'direction': 'SELL',
                'entry_price': current['bid'],
                'stop_loss': current['bid'] + stop_loss_amount,
                'take_profit': current['bid'] - take_profit_amount,
                'strength': 0.6,
                'timestamp': current['timestamp'],
                'reason': 'BB upper band rejection'
            }
        
        return None

class CorrectedBacktester:
    """Corrected backtesting system for gold"""
    
    def __init__(self, initial_balance=10000.0):
        self.strategies = {
            'rsi': CorrectedRSIStrategy(),
            'macd': CorrectedMACDStrategy(),
            'bollinger': CorrectedBBStrategy()
        }
        self.results = {}
        self.initial_balance = initial_balance
    
    def test_strategy(self, strategy_name: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Test a strategy with properly simulated trades"""
        strategy = self.strategies[strategy_name]
        
        # Calculate indicators
        df_with_indicators = strategy.calculate_indicators(df)
        
        # Generate signals
        signals = []
        for idx in range(20, len(df_with_indicators)):
            signal = strategy.generate_signal(df_with_indicators, idx)
            if signal:
                signals.append(signal)
        
        # Simulate trades with proper mechanics
        trades = self._simulate_trades_correctly(signals, df_with_indicators, strategy.params)
        
        # Calculate performance
        performance = self._calculate_performance_metrics(trades)
        
        return {
            'strategy_name': strategy_name,
            'total_signals': len(signals),
            'total_trades': len(trades),
            'performance': performance,
            'sample_trades': trades[:5] if trades else []
        }
    
    def _simulate_trades_correctly(self, signals: List[Dict], df: pd.DataFrame, params: Dict) -> List[Dict]:
        """Simulate trades using actual price data and correct position sizing"""
        trades = []
        balance = self.initial_balance
        max_risk_per_trade = 0.01  # 1% risk per trade
        active_trade = None
        
        # Create a timestamp to index mapping for quick lookups
        timestamp_to_index = {row['timestamp']: i for i, row in df.iterrows()}
        
        # Process each bar chronologically
        for idx in range(20, len(df)):
            current = df.iloc[idx]
            
            # Check if we have an active trade
            if active_trade:
                # Check if stop loss or take profit hit
                if active_trade['direction'] == 'BUY':
                    # Stop loss hit
                    if current['bid'] <= active_trade['stop_loss']:
                        # Calculate profit/loss
                        pnl = (current['bid'] - active_trade['entry_price']) * active_trade['position_size']
                        commission = active_trade['position_size'] * active_trade['entry_price'] * 0.0001  # 0.01% commission
                        pnl -= commission
                        
                        # Update balance
                        balance += pnl
                        
                        # Record trade
                        trade = {
                            'entry_time': active_trade['entry_time'],
                            'exit_time': current['timestamp'],
                            'direction': active_trade['direction'],
                            'entry_price': active_trade['entry_price'],
                            'exit_price': current['bid'],
                            'position_size': active_trade['position_size'],
                            'pnl': pnl,
                            'balance': balance,
                            'duration_hours': (current['timestamp'] - active_trade['entry_time']).total_seconds() / 3600,
                            'exit_type': 'stop_loss',
                            'reason': active_trade['reason']
                        }
                        trades.append(trade)
                        active_trade = None
                    
                    # Take profit hit
                    elif current['ask'] >= active_trade['take_profit']:
                        # Calculate profit/loss
                        pnl = (current['ask'] - active_trade['entry_price']) * active_trade['position_size']
                        commission = active_trade['position_size'] * active_trade['entry_price'] * 0.0001
                        pnl -= commission
                        
                        # Update balance
                        balance += pnl
                        
                        # Record trade
                        trade = {
                            'entry_time': active_trade['entry_time'],
                            'exit_time': current['timestamp'],
                            'direction': active_trade['direction'],
                            'entry_price': active_trade['entry_price'],
                            'exit_price': current['ask'],
                            'position_size': active_trade['position_size'],
                            'pnl': pnl,
                            'balance': balance,
                            'duration_hours': (current['timestamp'] - active_trade['entry_time']).total_seconds() / 3600,
                            'exit_type': 'take_profit',
                            'reason': active_trade['reason']
                        }
                        trades.append(trade)
                        active_trade = None
                
                elif active_trade['direction'] == 'SELL':
                    # Stop loss hit
                    if current['ask'] >= active_trade['stop_loss']:
                        # Calculate profit/loss
                        pnl = (active_trade['entry_price'] - current['ask']) * active_trade['position_size']
                        commission = active_trade['position_size'] * active_trade['entry_price'] * 0.0001
                        pnl -= commission
                        
                        # Update balance
                        balance += pnl
                        
                        # Record trade
                        trade = {
                            'entry_time': active_trade['entry_time'],
                            'exit_time': current['timestamp'],
                            'direction': active_trade['direction'],
                            'entry_price': active_trade['entry_price'],
                            'exit_price': current['ask'],
                            'position_size': active_trade['position_size'],
                            'pnl': pnl,
                            'balance': balance,
                            'duration_hours': (current['timestamp'] - active_trade['entry_time']).total_seconds() / 3600,
                            'exit_type': 'stop_loss',
                            'reason': active_trade['reason']
                        }
                        trades.append(trade)
                        active_trade = None
                    
                    # Take profit hit
                    elif current['bid'] <= active_trade['take_profit']:
                        # Calculate profit/loss
                        pnl = (active_trade['entry_price'] - current['bid']) * active_trade['position_size']
                        commission = active_trade['position_size'] * active_trade['entry_price'] * 0.0001
                        pnl -= commission
                        
                        # Update balance
                        balance += pnl
                        
                        # Record trade
                        trade = {
                            'entry_time': active_trade['entry_time'],
                            'exit_time': current['timestamp'],
                            'direction': active_trade['direction'],
                            'entry_price': active_trade['entry_price'],
                            'exit_price': current['bid'],
                            'position_size': active_trade['position_size'],
                            'pnl': pnl,
                            'balance': balance,
                            'duration_hours': (current['timestamp'] - active_trade['entry_time']).total_seconds() / 3600,
                            'exit_type': 'take_profit',
                            'reason': active_trade['reason']
                        }
                        trades.append(trade)
                        active_trade = None
            
            # If we don't have an active trade, check for signals
            if not active_trade:
                # Find signals for this timestamp
                for signal in signals:
                    if signal['timestamp'] == current['timestamp']:
                        # Calculate proper position size with risk management
                        risk_amount = balance * max_risk_per_trade
                        price_distance = abs(signal['entry_price'] - signal['stop_loss'])
                        
                        # FIXED: Correct position sizing for gold
                        # For gold, we divide by price_distance directly since it's already in dollars
                        position_size = risk_amount / price_distance
                        
                        # Apply reasonable position size caps
                        max_position_size = balance * 0.05  # Max 5% of account as position size
                        position_size = min(position_size, max_position_size)
                        
                        # Create active trade
                        active_trade = {
                            'entry_time': current['timestamp'],
                            'direction': signal['direction'],
                            'entry_price': signal['entry_price'],
                            'stop_loss': signal['stop_loss'],
                            'take_profit': signal['take_profit'],
                            'position_size': position_size,
                            'reason': signal['reason']
                        }
                        break
        
        # Close any active trade at the end of the data
        if active_trade:
            last_bar = df.iloc[-1]
            exit_price = last_bar['bid'] if active_trade['direction'] == 'BUY' else last_bar['ask']
            
            # Calculate profit/loss
            if active_trade['direction'] == 'BUY':
                pnl = (exit_price - active_trade['entry_price']) * active_trade['position_size']
            else:
                pnl = (active_trade['entry_price'] - exit_price) * active_trade['position_size']
            
            commission = active_trade['position_size'] * active_trade['entry_price'] * 0.0001
            pnl -= commission
            
            # Update balance
            balance += pnl
            
            # Record trade
            trade = {
                'entry_time': active_trade['entry_time'],
                'exit_time': last_bar['timestamp'],
                'direction': active_trade['direction'],
                'entry_price': active_trade['entry_price'],
                'exit_price': exit_price,
                'position_size': active_trade['position_size'],
                'pnl': pnl,
                'balance': balance,
                'duration_hours': (last_bar['timestamp'] - active_trade['entry_time']).total_seconds() / 3600,
                'exit_type': 'end_of_data',
                'reason': active_trade['reason']
            }
            trades.append(trade)
        
        return trades
    
    def _calculate_performance_metrics(self, trades: List[Dict]) -> Dict[str, float]:
        """Calculate comprehensive performance metrics"""
        if not trades:
            return {
                'total_return': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'avg_trade': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'max_win': 0.0,
                'max_loss': 0.0,
                'total_pnl': 0.0
            }
        
        # Get initial and final balance
        initial_balance = self.initial_balance
        final_balance = trades[-1]['balance']
        
        # Calculate return
        total_return = ((final_balance - initial_balance) / initial_balance) * 100
        
        # Calculate win rate
        winning_trades = [t for t in trades if t['pnl'] > 0]
        win_rate = (len(winning_trades) / len(trades)) * 100
        
        # Calculate profit factor
        total_profit = sum(t['pnl'] for t in trades if t['pnl'] > 0)
        total_loss = abs(sum(t['pnl'] for t in trades if t['pnl'] < 0))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # Calculate drawdown
        balances = [initial_balance] + [t['balance'] for t in trades]
        peak = initial_balance
        drawdowns = []
        
        for balance in balances:
            if balance > peak:
                peak = balance
            drawdown = (peak - balance) / peak * 100
            drawdowns.append(drawdown)
        
        max_drawdown = max(drawdowns) if drawdowns else 0.0
        
        # Calculate Sharpe ratio
        returns = [(t['balance'] / prev_balance) - 1 for t, prev_balance in zip(trades, [initial_balance] + [t['balance'] for t in trades[:-1]])]
        sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if returns and np.std(returns) > 0 else 0.0
        
        # Calculate average trade, win, loss
        avg_trade = sum(t['pnl'] for t in trades) / len(trades) if trades else 0.0
        avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0.0
        losing_trades = [t for t in trades if t['pnl'] <= 0]
        avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0.0
        
        # Calculate max win and loss
        max_win = max([t['pnl'] for t in trades], default=0.0)
        max_loss = min([t['pnl'] for t in trades], default=0.0)
        
        # Calculate total PnL
        total_pnl = sum(t['pnl'] for t in trades)
        
        return {
            'total_return': total_return,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'avg_trade': avg_trade,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_win': max_win,
            'max_loss': max_loss,
            'total_pnl': total_pnl
        }
    
    def test_all_strategies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Test all strategies with the corrected system"""
        results = {}
        
        for strategy_name in self.strategies.keys():
            print(f"Testing {strategy_name} strategy with corrected system...")
            result = self.test_strategy(strategy_name, df)
            results[strategy_name] = result
        
        return results
    
    def create_detailed_report(self, results: Dict[str, Any]) -> str:
        """Generate a detailed performance report"""
        report = "# Gold Scalping Backtesting Report (Corrected System)\n"
        report += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        report += "## Summary of Performance\n\n"
        report += "| Strategy | Signals | Trades | Return (%) | Win Rate (%) | Profit Factor | Max DD (%) | Sharpe |\n"
        report += "|----------|---------|--------|------------|--------------|--------------|------------|--------|\n"
        
        for strategy_name, result in results.items():
            perf = result['performance']
            report += f"| {strategy_name} | {result['total_signals']} | {result['total_trades']} | "
            report += f"{perf['total_return']:.2f}% | {perf['win_rate']:.2f}% | "
            report += f"{perf['profit_factor']:.2f} | {perf['max_drawdown']:.2f}% | {perf['sharpe_ratio']:.2f} |\n"
        
        report += "\n## Detailed Performance Metrics\n\n"
        
        for strategy_name, result in results.items():
            perf = result['performance']
            report += f"### {strategy_name} Strategy\n\n"
            report += f"- Total Signals Generated: {result['total_signals']}\n"
            report += f"- Total Trades Executed: {result['total_trades']}\n"
            report += f"- Total Return: {perf['total_return']:.2f}%\n"
            report += f"- Win Rate: {perf['win_rate']:.2f}%\n"
            report += f"- Profit Factor: {perf['profit_factor']:.2f}\n"
            report += f"- Maximum Drawdown: {perf['max_drawdown']:.2f}%\n"
            report += f"- Sharpe Ratio: {perf['sharpe_ratio']:.2f}\n"
            report += f"- Average Trade: ${perf['avg_trade']:.2f}\n"
            report += f"- Average Win: ${perf['avg_win']:.2f}\n"
            report += f"- Average Loss: ${perf['avg_loss']:.2f}\n"
            report += f"- Maximum Win: ${perf['max_win']:.2f}\n"
            report += f"- Maximum Loss: ${perf['max_loss']:.2f}\n"
            report += f"- Total P&L: ${perf['total_pnl']:.2f}\n\n"
            
            if result['sample_trades']:
                report += "#### Sample Trades\n\n"
                report += "| Entry Time | Exit Time | Direction | Entry | Exit | P&L | Reason | Exit Type |\n"
                report += "|------------|-----------|-----------|-------|------|-----|--------|----------|\n"
                
                for trade in result['sample_trades']:
                    entry_time = trade['entry_time'].strftime("%Y-%m-%d %H:%M")
                    exit_time = trade['exit_time'].strftime("%Y-%m-%d %H:%M")
                    report += f"| {entry_time} | {exit_time} | {trade['direction']} | "
                    report += f"{trade['entry_price']:.2f} | {trade['exit_price']:.2f} | "
                    report += f"${trade['pnl']:.2f} | {trade['reason']} | {trade['exit_type']} |\n"
            
            report += "\n"
        
        report += "## System Corrections\n\n"
        report += "The following fundamental errors were corrected in this backtesting system:\n\n"
        report += "1. **Gold Pip Value**: Corrected gold pip definition from 0.0001 to $0.10\n"
        report += "2. **Position Sizing**: Fixed position size calculation for gold's unique characteristics\n"
        report += "3. **Stop Loss/Take Profit**: Implemented realistic values (50-100 pips)\n"
        report += "4. **Trade Simulation**: Used actual price data instead of random probabilities\n"
        report += "5. **Risk Management**: Capped position sizes to 5% of account balance\n\n"
        
        report += "## Conclusion\n\n"
        report += "This corrected backtesting system addresses the fundamental flaws in the previous implementation, "
        report += "resulting in more realistic and reliable performance metrics. The results now reflect "
        report += "proper risk management and trade simulation methods specific to gold trading.\n"
        
        return report

def main():
    """Run the corrected gold backtesting system"""
    try:
        # Load XAU_USD data
        df = pd.read_csv('backtesting_data/XAU_USD.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        print(f"Loaded {len(df)} data points for XAU_USD")
        
        # Initialize the corrected backtester
        backtester = CorrectedBacktester()
        
        # Test all strategies
        results = backtester.test_all_strategies(df)
        
        # Print results
        print("\n" + "="*80)
        print("CORRECTED GOLD BACKTESTING SYSTEM RESULTS")
        print("="*80)
        
        for strategy_name, result in results.items():
            perf = result['performance']
            print(f"\n{strategy_name.upper()} STRATEGY:")
            print(f"  Total Signals: {result['total_signals']}")
            print(f"  Total Trades: {result['total_trades']}")
            print(f"  Total Return: {perf['total_return']:.2f}%")
            print(f"  Win Rate: {perf['win_rate']:.2f}%")
            print(f"  Profit Factor: {perf['profit_factor']:.2f}")
            print(f"  Max Drawdown: {perf['max_drawdown']:.2f}%")
            print(f"  Sharpe Ratio: {perf['sharpe_ratio']:.2f}")
            print(f"  Total P&L: ${perf['total_pnl']:.2f}")
        
        # Save results
        with open('corrected_gold_backtesting_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nDetailed results saved to corrected_gold_backtesting_results.json")
        
        # Generate detailed report
        report = backtester.create_detailed_report(results)
        
        # Save report
        with open('CORRECTED_GOLD_BACKTESTING_REPORT.md', 'w') as f:
            f.write(report)
        
        print(f"Detailed report saved to CORRECTED_GOLD_BACKTESTING_REPORT.md")
        
        return results
        
    except Exception as e:
        print(f"Error running corrected backtesting system: {e}")
        return None

if __name__ == "__main__":
    main()
