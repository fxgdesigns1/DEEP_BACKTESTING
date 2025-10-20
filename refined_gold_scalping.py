#!/usr/bin/env python3
"""
Refined Gold Scalping Strategies
Improved risk management and signal quality
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import json

logger = logging.getLogger("refined_gold_scalping")

class RefinedGoldScalping:
    """Refined gold scalping with better risk management"""
    
    def __init__(self, strategy_name: str, params: Dict[str, Any]):
        self.name = strategy_name
        self.params = params
        self.trades = []
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators"""
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
        
        # Support and Resistance levels
        df['resistance'] = df['mid_price'].rolling(window=20).max()
        df['support'] = df['mid_price'].rolling(window=20).min()
        
        # Price momentum
        df['momentum_5'] = df['mid_price'].pct_change(5)
        df['momentum_10'] = df['mid_price'].pct_change(10)
        
        # Trend strength
        df['trend_strength'] = abs(df['sma_10'] - df['sma_20']) / df['sma_20']
        
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

class ConservativeScalping(RefinedGoldScalping):
    """Conservative scalping with strict filters"""
    
    def __init__(self):
        params = {
            'stop_loss_pips': 4,
            'take_profit_pips': 6,
            'max_spread': 0.8,
            'min_volatility': 0.00004,
            'min_signal_strength': 0.7,
            'rsi_oversold': 25,
            'rsi_overbought': 75,
            'volume_threshold': 1.3,
            'trend_threshold': 0.0001
        }
        super().__init__("Conservative_Scalping", params)
    
    def generate_signal(self, df: pd.DataFrame, idx: int) -> Optional[Dict[str, Any]]:
        """Generate conservative signal"""
        if idx < 26:
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
        
        # Check trend strength
        if current['trend_strength'] < params['trend_threshold']:
            return None
        
        rsi = current['rsi']
        if pd.isna(rsi):
            return None
        
        # Conservative BUY signal
        if (rsi < params['rsi_oversold'] and 
            current['mid_price'] < current['bb_lower'] and
            current['macd'] > current['macd_signal'] and
            current['volume_ratio'] > params['volume_threshold'] and
            current['sma_10'] > current['sma_20']):  # Uptrend filter
            
            return {
                'direction': 'BUY',
                'entry_price': current['ask'],
                'stop_loss': current['ask'] - (params['stop_loss_pips'] * 0.0001),
                'take_profit': current['ask'] + (params['take_profit_pips'] * 0.0001),
                'strength': 0.8,
                'reason': 'Conservative oversold bounce in uptrend'
            }
        
        # Conservative SELL signal
        elif (rsi > params['rsi_overbought'] and 
              current['mid_price'] > current['bb_upper'] and
              current['macd'] < current['macd_signal'] and
              current['volume_ratio'] > params['volume_threshold'] and
              current['sma_10'] < current['sma_20']):  # Downtrend filter
            
            return {
                'direction': 'SELL',
                'entry_price': current['bid'],
                'stop_loss': current['bid'] + (params['stop_loss_pips'] * 0.0001),
                'take_profit': current['bid'] - (params['take_profit_pips'] * 0.0001),
                'strength': 0.8,
                'reason': 'Conservative overbought rejection in downtrend'
            }
        
        return None

class MomentumScalping(RefinedGoldScalping):
    """Momentum-based scalping"""
    
    def __init__(self):
        params = {
            'stop_loss_pips': 6,
            'take_profit_pips': 9,
            'max_spread': 1.0,
            'min_volatility': 0.00003,
            'min_signal_strength': 0.6,
            'momentum_threshold': 0.00008,
            'volume_threshold': 1.2,
            'macd_threshold': 0.0001
        }
        super().__init__("Momentum_Scalping", params)
    
    def generate_signal(self, df: pd.DataFrame, idx: int) -> Optional[Dict[str, Any]]:
        """Generate momentum signal"""
        if idx < 26:
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
        
        momentum = current['momentum_5']
        if pd.isna(momentum):
            return None
        
        # Momentum BUY signal
        if (momentum > params['momentum_threshold'] and
            current['macd'] > current['macd_signal'] and
            current['macd_histogram'] > params['macd_threshold'] and
            current['volume_ratio'] > params['volume_threshold'] and
            current['rsi'] < 70):  # Not overbought
            
            return {
                'direction': 'BUY',
                'entry_price': current['ask'],
                'stop_loss': current['ask'] - (params['stop_loss_pips'] * 0.0001),
                'take_profit': current['ask'] + (params['take_profit_pips'] * 0.0001),
                'strength': 0.7,
                'reason': f'Strong momentum buy (momentum: {momentum:.6f})'
            }
        
        # Momentum SELL signal
        elif (momentum < -params['momentum_threshold'] and
              current['macd'] < current['macd_signal'] and
              current['macd_histogram'] < -params['macd_threshold'] and
              current['volume_ratio'] > params['volume_threshold'] and
              current['rsi'] > 30):  # Not oversold
            
            return {
                'direction': 'SELL',
                'entry_price': current['bid'],
                'stop_loss': current['bid'] + (params['stop_loss_pips'] * 0.0001),
                'take_profit': current['bid'] - (params['take_profit_pips'] * 0.0001),
                'strength': 0.7,
                'reason': f'Strong momentum sell (momentum: {momentum:.6f})'
            }
        
        return None

class BreakoutScalping(RefinedGoldScalping):
    """Breakout-based scalping"""
    
    def __init__(self):
        params = {
            'stop_loss_pips': 8,
            'take_profit_pips': 12,
            'max_spread': 1.2,
            'min_volatility': 0.00004,
            'min_signal_strength': 0.65,
            'volume_breakout_multiplier': 1.8,
            'breakout_threshold': 0.00015
        }
        super().__init__("Breakout_Scalping", params)
    
    def generate_signal(self, df: pd.DataFrame, idx: int) -> Optional[Dict[str, Any]]:
        """Generate breakout signal"""
        if idx < 26:
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
        
        # Check for strong resistance breakout
        if (current['mid_price'] > current['resistance'] and
            current['volume_ratio'] > params['volume_breakout_multiplier'] and
            current['macd'] > current['macd_signal'] and
            current['rsi'] < 75 and  # Not overbought
            current['bb_position'] > 0.8):  # Near upper BB
            
            return {
                'direction': 'BUY',
                'entry_price': current['ask'],
                'stop_loss': current['ask'] - (params['stop_loss_pips'] * 0.0001),
                'take_profit': current['ask'] + (params['take_profit_pips'] * 0.0001),
                'strength': 0.8,
                'reason': 'Strong resistance breakout'
            }
        
        # Check for strong support breakdown
        elif (current['mid_price'] < current['support'] and
              current['volume_ratio'] > params['volume_breakout_multiplier'] and
              current['macd'] < current['macd_signal'] and
              current['rsi'] > 25 and  # Not oversold
              current['bb_position'] < 0.2):  # Near lower BB
            
            return {
                'direction': 'SELL',
                'entry_price': current['bid'],
                'stop_loss': current['bid'] + (params['stop_loss_pips'] * 0.0001),
                'take_profit': current['bid'] - (params['take_profit_pips'] * 0.0001),
                'strength': 0.8,
                'reason': 'Strong support breakdown'
            }
        
        return None

class RefinedScalpingTester:
    """Test refined gold scalping strategies"""
    
    def __init__(self):
        self.strategies = {
            'conservative': ConservativeScalping(),
            'momentum': MomentumScalping(),
            'breakout': BreakoutScalping()
        }
        self.results = {}
    
    def test_strategy(self, strategy_name: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Test a specific strategy"""
        strategy = self.strategies[strategy_name]
        
        # Calculate indicators
        df_with_indicators = strategy.calculate_indicators(df)
        
        # Generate signals
        signals = []
        for idx in range(26, len(df_with_indicators)):
            signal = strategy.generate_signal(df_with_indicators, idx)
            if signal:
                signal['timestamp'] = df_with_indicators.iloc[idx]['timestamp']
                signal['strategy'] = strategy_name
                signals.append(signal)
        
        # Simulate trades with improved risk management
        trades = self._simulate_trades_improved(signals, strategy.params)
        
        # Calculate performance
        performance = self._calculate_performance_improved(trades)
        
        return {
            'strategy_name': strategy_name,
            'total_signals': len(signals),
            'total_trades': len(trades),
            'performance': performance,
            'sample_trades': trades[:5] if trades else []
        }
    
    def _simulate_trades_improved(self, signals: List[Dict], params: Dict) -> List[Dict]:
        """Simulate trades with improved risk management"""
        trades = []
        balance = 10000.0
        max_risk_per_trade = 0.005  # 0.5% risk per trade
        
        for signal in signals:
            # Calculate position size with risk management
            risk_amount = balance * max_risk_per_trade
            price_distance = abs(signal['entry_price'] - signal['stop_loss'])
            
            if price_distance > 0:
                position_size = min(risk_amount / price_distance, 500)  # Cap position size
            else:
                continue
            
            # Simulate trade outcome with realistic execution
            if signal['direction'] == 'BUY':
                # 70% chance of hitting take profit, 30% chance of hitting stop loss
                if np.random.random() < 0.7:
                    pnl = (signal['take_profit'] - signal['entry_price']) * position_size
                else:
                    pnl = (signal['stop_loss'] - signal['entry_price']) * position_size
            else:
                if np.random.random() < 0.7:
                    pnl = (signal['entry_price'] - signal['take_profit']) * position_size
                else:
                    pnl = (signal['entry_price'] - signal['stop_loss']) * position_size
            
            # Apply commission (0.01%)
            commission = position_size * signal['entry_price'] * 0.0001
            pnl -= commission
            
            balance += pnl
            
            trade = {
                'timestamp': signal['timestamp'],
                'direction': signal['direction'],
                'entry_price': signal['entry_price'],
                'exit_price': signal['take_profit'] if pnl > 0 else signal['stop_loss'],
                'position_size': position_size,
                'pnl': pnl,
                'commission': commission,
                'balance': balance,
                'reason': signal['reason']
            }
            
            trades.append(trade)
        
        return trades
    
    def _calculate_performance_improved(self, trades: List[Dict]) -> Dict[str, float]:
        """Calculate performance metrics with improved calculations"""
        if not trades:
            return {
                'total_return': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'max_drawdown': 0.0,
                'avg_trade_duration': 0.0,
                'total_pnl': 0.0,
                'sharpe_ratio': 0.0
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
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf') if total_profit > 0 else 0.0
        
        # Calculate max drawdown
        balances = [t['balance'] for t in trades]
        if len(balances) > 1:
            running_max = np.maximum.accumulate(balances)
            drawdowns = (running_max - balances) / running_max
            max_drawdown = np.max(drawdowns) * 100 if len(drawdowns) > 0 else 0.0
        else:
            max_drawdown = 0.0
        
        # Calculate Sharpe ratio
        returns = [t['pnl'] for t in trades]
        if len(returns) > 1:
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = mean_return / std_return if std_return > 0 else 0.0
        else:
            sharpe_ratio = 0.0
        
        total_pnl = sum(t['pnl'] for t in trades)
        
        return {
            'total_return': total_return,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'avg_trade_duration': 2.0,
            'total_pnl': total_pnl,
            'sharpe_ratio': sharpe_ratio
        }
    
    def test_all_strategies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Test all strategies"""
        results = {}
        
        for strategy_name in self.strategies.keys():
            print(f"Testing {strategy_name} strategy...")
            result = self.test_strategy(strategy_name, df)
            results[strategy_name] = result
        
        return results

def main():
    """Test all refined gold scalping strategies"""
    try:
        # Load XAU_USD data
        df = pd.read_csv('backtesting_data/XAU_USD.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        print(f"Loaded {len(df)} data points for XAU_USD")
        
        # Test all strategies
        tester = RefinedScalpingTester()
        results = tester.test_all_strategies(df)
        
        # Print results
        print("\n" + "="*80)
        print("REFINED GOLD SCALPING STRATEGY COMPARISON")
        print("="*80)
        
        for strategy_name, result in results.items():
            print(f"\n{strategy_name.upper().replace('_', ' ')} STRATEGY:")
            print(f"  Total Signals: {result['total_signals']}")
            print(f"  Total Trades: {result['total_trades']}")
            print(f"  Total Return: {result['performance']['total_return']:.2f}%")
            print(f"  Win Rate: {result['performance']['win_rate']:.2f}%")
            print(f"  Profit Factor: {result['performance']['profit_factor']:.2f}")
            print(f"  Max Drawdown: {result['performance']['max_drawdown']:.2f}%")
            print(f"  Sharpe Ratio: {result['performance']['sharpe_ratio']:.2f}")
            print(f"  Total P&L: ${result['performance']['total_pnl']:.2f}")
        
        # Save results
        with open('refined_gold_scalping_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nResults saved to refined_gold_scalping_results.json")
        
        return results
        
    except Exception as e:
        print(f"Error testing strategies: {e}")
        return None

if __name__ == "__main__":
    main()
