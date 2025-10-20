#!/usr/bin/env python3
"""
Enhanced Gold Scalping Strategies
Multiple variations with different technical indicators and approaches
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger("gold_scalping")

class GoldScalpingStrategy:
    """Base class for gold scalping strategies"""
    
    def __init__(self, name: str, params: Dict[str, Any]):
        self.name = name
        self.params = params
        self.trades = []
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        df = df.copy()
        
        # Price-based indicators
        df['sma_5'] = df['mid_price'].rolling(window=5).mean()
        df['sma_10'] = df['mid_price'].rolling(window=10).mean()
        df['sma_20'] = df['mid_price'].rolling(window=20).mean()
        
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
        
        # Support and Resistance levels
        df['resistance'] = df['mid_price'].rolling(window=20).max()
        df['support'] = df['mid_price'].rolling(window=20).min()
        
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
        high = df['ask']  # Using ask as high proxy
        low = df['bid']   # Using bid as low proxy
        close = df['mid_price']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr

class ConservativeGoldScalping(GoldScalpingStrategy):
    """Conservative gold scalping with strict filters"""
    
    def __init__(self):
        params = {
            'stop_loss_pips': 5,
            'take_profit_pips': 8,
            'max_spread': 1.0,
            'min_volatility': 0.00003,
            'min_signal_strength': 0.6,
            'max_trades_per_day': 20,
            'risk_per_trade': 0.01,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'bb_squeeze_threshold': 0.001
        }
        super().__init__("Conservative Gold Scalping", params)
    
    def generate_signal(self, df: pd.DataFrame, idx: int) -> Optional[Dict[str, Any]]:
        """Generate conservative scalping signal"""
        if idx < 20:  # Need history
            return None
        
        current = df.iloc[idx]
        params = self.params
        
        # Check spread
        spread = current['ask'] - current['bid']
        if spread > params['max_spread']:
            return None
        
        # Check volatility (ATR)
        if current['atr'] < params['min_volatility']:
            return None
        
        # Check RSI conditions
        rsi = current['rsi']
        if pd.isna(rsi):
            return None
        
        # Check Bollinger Band squeeze
        bb_width = current['bb_width']
        if bb_width < params['bb_squeeze_threshold']:
            return None
        
        # Conservative BUY signal
        if (rsi < params['rsi_oversold'] and 
            current['mid_price'] < current['bb_lower'] and
            current['macd'] > current['macd_signal'] and
            current['volume_ratio'] > 1.2):
            
            return {
                'direction': 'BUY',
                'entry_price': current['ask'],
                'stop_loss': current['ask'] - (params['stop_loss_pips'] * 0.0001),
                'take_profit': current['ask'] + (params['take_profit_pips'] * 0.0001),
                'strength': 0.8,
                'reason': 'Conservative oversold bounce'
            }
        
        # Conservative SELL signal
        elif (rsi > params['rsi_overbought'] and 
              current['mid_price'] > current['bb_upper'] and
              current['macd'] < current['macd_signal'] and
              current['volume_ratio'] > 1.2):
            
            return {
                'direction': 'SELL',
                'entry_price': current['bid'],
                'stop_loss': current['bid'] + (params['stop_loss_pips'] * 0.0001),
                'take_profit': current['bid'] - (params['take_profit_pips'] * 0.0001),
                'strength': 0.8,
                'reason': 'Conservative overbought rejection'
            }
        
        return None

class AggressiveGoldScalping(GoldScalpingStrategy):
    """Aggressive gold scalping with more signals"""
    
    def __init__(self):
        params = {
            'stop_loss_pips': 8,
            'take_profit_pips': 12,
            'max_spread': 1.5,
            'min_volatility': 0.00002,
            'min_signal_strength': 0.4,
            'max_trades_per_day': 50,
            'risk_per_trade': 0.02,
            'rsi_oversold': 40,
            'rsi_overbought': 60,
            'momentum_threshold': 0.0001
        }
        super().__init__("Aggressive Gold Scalping", params)
    
    def generate_signal(self, df: pd.DataFrame, idx: int) -> Optional[Dict[str, Any]]:
        """Generate aggressive scalping signal"""
        if idx < 20:
            return None
        
        current = df.iloc[idx]
        params = self.params
        
        # Check spread
        spread = current['ask'] - current['bid']
        if spread > params['max_spread']:
            return None
        
        # Check volatility
        if current['atr'] < params['min_volatility']:
            return None
        
        # Check RSI
        rsi = current['rsi']
        if pd.isna(rsi):
            return None
        
        # Aggressive BUY signals
        buy_signals = 0
        if rsi < params['rsi_oversold']:
            buy_signals += 1
        if current['mid_price'] < current['bb_lower']:
            buy_signals += 1
        if current['macd'] > current['macd_signal']:
            buy_signals += 1
        if current['volume_ratio'] > 1.1:
            buy_signals += 1
        
        if buy_signals >= 2:  # At least 2 signals
            return {
                'direction': 'BUY',
                'entry_price': current['ask'],
                'stop_loss': current['ask'] - (params['stop_loss_pips'] * 0.0001),
                'take_profit': current['ask'] + (params['take_profit_pips'] * 0.0001),
                'strength': 0.6,
                'reason': f'Aggressive buy ({buy_signals} signals)'
            }
        
        # Aggressive SELL signals
        sell_signals = 0
        if rsi > params['rsi_overbought']:
            sell_signals += 1
        if current['mid_price'] > current['bb_upper']:
            sell_signals += 1
        if current['macd'] < current['macd_signal']:
            sell_signals += 1
        if current['volume_ratio'] > 1.1:
            sell_signals += 1
        
        if sell_signals >= 2:  # At least 2 signals
            return {
                'direction': 'SELL',
                'entry_price': current['bid'],
                'stop_loss': current['bid'] + (params['stop_loss_pips'] * 0.0001),
                'take_profit': current['bid'] - (params['take_profit_pips'] * 0.0001),
                'strength': 0.6,
                'reason': f'Aggressive sell ({sell_signals} signals)'
            }
        
        return None

class MomentumGoldScalping(GoldScalpingStrategy):
    """Momentum-based gold scalping"""
    
    def __init__(self):
        params = {
            'stop_loss_pips': 6,
            'take_profit_pips': 10,
            'max_spread': 1.2,
            'min_volatility': 0.000025,
            'min_signal_strength': 0.5,
            'max_trades_per_day': 30,
            'risk_per_trade': 0.015,
            'momentum_period': 5,
            'momentum_threshold': 0.00005
        }
        super().__init__("Momentum Gold Scalping", params)
    
    def generate_signal(self, df: pd.DataFrame, idx: int) -> Optional[Dict[str, Any]]:
        """Generate momentum-based scalping signal"""
        if idx < 20:
            return None
        
        current = df.iloc[idx]
        params = self.params
        
        # Check spread
        spread = current['ask'] - current['bid']
        if spread > params['max_spread']:
            return None
        
        # Check volatility
        if current['atr'] < params['min_volatility']:
            return None
        
        # Calculate momentum
        if idx >= params['momentum_period']:
            momentum = (current['mid_price'] - df.iloc[idx - params['momentum_period']]['mid_price']) / df.iloc[idx - params['momentum_period']]['mid_price']
        else:
            return None
        
        # Momentum BUY signal
        if (momentum > params['momentum_threshold'] and
            current['macd'] > current['macd_signal'] and
            current['volume_ratio'] > 1.15):
            
            return {
                'direction': 'BUY',
                'entry_price': current['ask'],
                'stop_loss': current['ask'] - (params['stop_loss_pips'] * 0.0001),
                'take_profit': current['ask'] + (params['take_profit_pips'] * 0.0001),
                'strength': 0.7,
                'reason': f'Momentum buy (momentum: {momentum:.6f})'
            }
        
        # Momentum SELL signal
        elif (momentum < -params['momentum_threshold'] and
              current['macd'] < current['macd_signal'] and
              current['volume_ratio'] > 1.15):
            
            return {
                'direction': 'SELL',
                'entry_price': current['bid'],
                'stop_loss': current['bid'] + (params['stop_loss_pips'] * 0.0001),
                'take_profit': current['bid'] - (params['take_profit_pips'] * 0.0001),
                'strength': 0.7,
                'reason': f'Momentum sell (momentum: {momentum:.6f})'
            }
        
        return None

class BreakoutGoldScalping(GoldScalpingStrategy):
    """Breakout-based gold scalping"""
    
    def __init__(self):
        params = {
            'stop_loss_pips': 7,
            'take_profit_pips': 14,
            'max_spread': 1.3,
            'min_volatility': 0.00003,
            'min_signal_strength': 0.55,
            'max_trades_per_day': 25,
            'risk_per_trade': 0.018,
            'breakout_threshold': 0.0001,
            'volume_breakout_multiplier': 1.5
        }
        super().__init__("Breakout Gold Scalping", params)
    
    def generate_signal(self, df: pd.DataFrame, idx: int) -> Optional[Dict[str, Any]]:
        """Generate breakout-based scalping signal"""
        if idx < 20:
            return None
        
        current = df.iloc[idx]
        params = self.params
        
        # Check spread
        spread = current['ask'] - current['bid']
        if spread > params['max_spread']:
            return None
        
        # Check volatility
        if current['atr'] < params['min_volatility']:
            return None
        
        # Check for resistance breakout
        if (current['mid_price'] > current['resistance'] and
            current['volume_ratio'] > params['volume_breakout_multiplier'] and
            current['macd'] > current['macd_signal']):
            
            return {
                'direction': 'BUY',
                'entry_price': current['ask'],
                'stop_loss': current['ask'] - (params['stop_loss_pips'] * 0.0001),
                'take_profit': current['ask'] + (params['take_profit_pips'] * 0.0001),
                'strength': 0.75,
                'reason': 'Resistance breakout'
            }
        
        # Check for support breakdown
        elif (current['mid_price'] < current['support'] and
              current['volume_ratio'] > params['volume_breakout_multiplier'] and
              current['macd'] < current['macd_signal']):
            
            return {
                'direction': 'SELL',
                'entry_price': current['bid'],
                'stop_loss': current['bid'] + (params['stop_loss_pips'] * 0.0001),
                'take_profit': current['bid'] - (params['take_profit_pips'] * 0.0001),
                'strength': 0.75,
                'reason': 'Support breakdown'
            }
        
        return None

class ScalpingStrategyTester:
    """Test multiple gold scalping strategies"""
    
    def __init__(self):
        self.strategies = {
            'conservative': ConservativeGoldScalping(),
            'aggressive': AggressiveGoldScalping(),
            'momentum': MomentumGoldScalping(),
            'breakout': BreakoutGoldScalping()
        }
        self.results = {}
    
    def test_strategy(self, strategy_name: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Test a specific strategy"""
        strategy = self.strategies[strategy_name]
        
        # Calculate indicators
        df_with_indicators = strategy.calculate_indicators(df)
        
        # Generate signals
        signals = []
        for idx in range(20, len(df_with_indicators)):
            signal = strategy.generate_signal(df_with_indicators, idx)
            if signal:
                signal['timestamp'] = df_with_indicators.iloc[idx]['timestamp']
                signal['strategy'] = strategy_name
                signals.append(signal)
        
        # Simulate trades
        trades = self._simulate_trades(signals, strategy.params)
        
        # Calculate performance
        performance = self._calculate_performance(trades, strategy.params)
        
        return {
            'strategy_name': strategy_name,
            'total_signals': len(signals),
            'total_trades': len(trades),
            'performance': performance,
            'trades': trades[:10]  # First 10 trades for analysis
        }
    
    def _simulate_trades(self, signals: List[Dict], params: Dict) -> List[Dict]:
        """Simulate trade execution"""
        trades = []
        balance = 10000.0
        
        for signal in signals:
            # Calculate position size
            risk_amount = balance * params['risk_per_trade']
            price_distance = abs(signal['entry_price'] - signal['stop_loss'])
            position_size = risk_amount / price_distance
            
            # Simulate trade outcome (simplified)
            if signal['direction'] == 'BUY':
                pnl = (signal['take_profit'] - signal['entry_price']) * position_size
            else:
                pnl = (signal['entry_price'] - signal['take_profit']) * position_size
            
            # Apply commission
            commission = position_size * signal['entry_price'] * 0.0001
            pnl -= commission
            
            balance += pnl
            
            trade = {
                'timestamp': signal['timestamp'],
                'direction': signal['direction'],
                'entry_price': signal['entry_price'],
                'exit_price': signal['take_profit'],
                'position_size': position_size,
                'pnl': pnl,
                'commission': commission,
                'balance': balance,
                'reason': signal['reason']
            }
            
            trades.append(trade)
        
        return trades
    
    def _calculate_performance(self, trades: List[Dict], params: Dict) -> Dict[str, float]:
        """Calculate performance metrics"""
        if not trades:
            return {
                'total_return': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'max_drawdown': 0.0,
                'avg_trade_duration': 0.0
            }
        
        # Calculate returns
        initial_balance = 10000.0
        final_balance = trades[-1]['balance']
        total_return = ((final_balance - initial_balance) / initial_balance) * 100
        
        # Calculate win rate
        winning_trades = [t for t in trades if t['pnl'] > 0]
        win_rate = (len(winning_trades) / len(trades)) * 100 if trades else 0.0
        
        # Calculate profit factor
        total_profit = sum(t['pnl'] for t in trades if t['pnl'] > 0)
        total_loss = abs(sum(t['pnl'] for t in trades if t['pnl'] < 0))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # Calculate max drawdown
        balances = [t['balance'] for t in trades]
        running_max = np.maximum.accumulate(balances)
        drawdowns = (running_max - balances) / running_max
        max_drawdown = np.max(drawdowns) * 100 if len(drawdowns) > 0 else 0.0
        
        return {
            'total_return': total_return,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'avg_trade_duration': 2.0  # Simplified
        }
    
    def test_all_strategies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Test all strategies"""
        results = {}
        
        for strategy_name in self.strategies.keys():
            logger.info(f"Testing {strategy_name} strategy...")
            result = self.test_strategy(strategy_name, df)
            results[strategy_name] = result
        
        return results

def main():
    """Test all gold scalping strategies"""
    # Load XAU_USD data
    try:
        df = pd.read_csv('backtesting_data/XAU_USD.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Test all strategies
        tester = ScalpingStrategyTester()
        results = tester.test_all_strategies(df)
        
        # Print results
        print("\n" + "="*80)
        print("GOLD SCALPING STRATEGY COMPARISON")
        print("="*80)
        
        for strategy_name, result in results.items():
            print(f"\n{strategy_name.upper()} STRATEGY:")
            print(f"  Total Signals: {result['total_signals']}")
            print(f"  Total Trades: {result['total_trades']}")
            print(f"  Total Return: {result['performance']['total_return']:.2f}%")
            print(f"  Win Rate: {result['performance']['win_rate']:.2f}%")
            print(f"  Profit Factor: {result['performance']['profit_factor']:.2f}")
            print(f"  Max Drawdown: {result['performance']['max_drawdown']:.2f}%")
        
        return results
        
    except Exception as e:
        logger.error(f"Error testing strategies: {e}")
        return None

if __name__ == "__main__":
    main()
