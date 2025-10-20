#!/usr/bin/env python3
"""
ADVANCED XAU_USD VOLATILITY STRATEGY OPTIMIZER
World-class optimization framework for 100 different scenarios
Created by: World's #1 Trader & Coder
"""

import pandas as pd
import numpy as np
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
import os
import warnings
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingRegressor

warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedXAUUSDVolatilityOptimizer:
    """World-class XAU_USD Volatility Strategy Optimizer"""
    
    def __init__(self):
        self.logger = logger
        self.data_path = "/Users/mac/SharedNetwork/quant_strategy_ai/deep_backtesting/data/enhanced/xau_usd_1h_enhanced.csv"
        
        # Advanced parameter ranges for optimization
        self.parameter_ranges = {
            'volatility_lookback': [50, 100, 150, 200],
            'volatility_multiplier': [1.2, 1.5, 1.8, 2.0, 2.5],
            'bb_width_lookback': [10, 20, 30, 40],
            'bb_width_multiplier': [1.1, 1.2, 1.3, 1.5],
            'stop_loss_atr_multiplier': [1.0, 1.5, 2.0, 2.5, 3.0],
            'take_profit_atr_multiplier': [2.0, 3.0, 4.0, 5.0, 6.0],
            'trailing_stop_atr_multiplier': [0, 1.0, 1.5, 2.0],
            'rsi_oversold': [20, 25, 30],
            'rsi_overbought': [70, 75, 80],
            'volume_threshold': [1.0, 1.2, 1.5, 2.0],
            'atr_min_threshold': [0.5, 1.0, 1.5, 2.0],
            'session_filter': ['all', 'london_ny', 'ny_only', 'london_only'],
            'avoid_news_hours': [True, False],
            'use_ml_filter': [True, False],
            'use_momentum_confirmation': [True, False],
            'use_volume_profile': [True, False],
            'use_market_regime_filter': [True, False]
        }
    
    def load_data(self) -> pd.DataFrame:
        """Load and prepare XAU_USD data"""
        self.logger.info("Loading XAU_USD enhanced data...")
        df = pd.read_csv(self.data_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Rename columns to standard format
        df = df.rename(columns={
            'open': 'Open',
            'high': 'High', 
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })
        
        self.logger.info(f"Loaded {len(df)} candles from {df.index[0]} to {df.index[-1]}")
        return df
    
    def calculate_advanced_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators"""
        
        # Basic indicators
        df['SMA_20'] = df['Close'].rolling(20).mean()
        df['SMA_50'] = df['Close'].rolling(50).mean()
        df['EMA_12'] = df['Close'].ewm(span=12).mean()
        df['EMA_26'] = df['Close'].ewm(span=26).mean()
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(20).mean()
        bb_std = df['Close'].rolling(20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
        
        # MACD
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # Volatility measures
        df['Price_Change'] = df['Close'].pct_change()
        df['Volatility'] = df['Price_Change'].rolling(20).std()
        df['Volatility_50'] = df['Price_Change'].rolling(50).std()
        df['Volatility_100'] = df['Price_Change'].rolling(100).std()
        
        # Volume indicators
        df['Volume_SMA'] = df['Volume'].rolling(20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
        
        # Advanced momentum indicators
        df['Stoch_K'] = ((df['Close'] - df['Low'].rolling(14).min()) / 
                        (df['High'].rolling(14).max() - df['Low'].rolling(14).min())) * 100
        df['Stoch_D'] = df['Stoch_K'].rolling(3).mean()
        
        # Williams %R
        high_max = df['High'].rolling(14).max()
        low_min = df['Low'].rolling(14).min()
        df['Williams_R'] = -100 * ((high_max - df['Close']) / (high_max - low_min))
        
        # Market regime indicators
        df['Trend_Strength'] = abs(df['Close'] - df['SMA_50']) / df['ATR']
        df['Market_Regime'] = np.where(df['Close'] > df['SMA_50'], 1, -1)
        
        # Session identification
        df['Hour'] = df.index.hour
        df['London_Session'] = ((df['Hour'] >= 8) & (df['Hour'] <= 16)).astype(int)
        df['NY_Session'] = ((df['Hour'] >= 13) & (df['Hour'] <= 21)).astype(int)
        df['London_NY_Overlap'] = ((df['Hour'] >= 13) & (df['Hour'] <= 16)).astype(int)
        
        return df
    
    def generate_parameter_combinations(self) -> List[Dict]:
        """Generate 100 different parameter combinations"""
        
        np.random.seed(42)  # For reproducibility
        combinations = []
        
        # Strategy 1-25: Basic volatility variations
        for i in range(25):
            combo = {
                'volatility_lookback': np.random.choice(self.parameter_ranges['volatility_lookback']),
                'volatility_multiplier': np.random.choice(self.parameter_ranges['volatility_multiplier']),
                'bb_width_lookback': np.random.choice(self.parameter_ranges['bb_width_lookback']),
                'bb_width_multiplier': np.random.choice(self.parameter_ranges['bb_width_multiplier']),
                'stop_loss_atr_multiplier': np.random.choice(self.parameter_ranges['stop_loss_atr_multiplier']),
                'take_profit_atr_multiplier': np.random.choice(self.parameter_ranges['take_profit_atr_multiplier']),
                'trailing_stop_atr_multiplier': 0,
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'volume_threshold': 1.0,
                'atr_min_threshold': 1.0,
                'session_filter': 'all',
                'avoid_news_hours': False,
                'use_ml_filter': False,
                'use_momentum_confirmation': False,
                'use_volume_profile': False,
                'use_market_regime_filter': False,
                'scenario_name': f'Basic_Volatility_{i+1}'
            }
            combinations.append(combo)
        
        # Strategy 26-50: Risk management variations
        for i in range(25):
            combo = {
                'volatility_lookback': 100,
                'volatility_multiplier': 1.5,
                'bb_width_lookback': 20,
                'bb_width_multiplier': 1.2,
                'stop_loss_atr_multiplier': np.random.choice(self.parameter_ranges['stop_loss_atr_multiplier']),
                'take_profit_atr_multiplier': np.random.choice(self.parameter_ranges['take_profit_atr_multiplier']),
                'trailing_stop_atr_multiplier': np.random.choice(self.parameter_ranges['trailing_stop_atr_multiplier']),
                'rsi_oversold': np.random.choice(self.parameter_ranges['rsi_oversold']),
                'rsi_overbought': np.random.choice(self.parameter_ranges['rsi_overbought']),
                'volume_threshold': np.random.choice(self.parameter_ranges['volume_threshold']),
                'atr_min_threshold': np.random.choice(self.parameter_ranges['atr_min_threshold']),
                'session_filter': 'all',
                'avoid_news_hours': False,
                'use_ml_filter': False,
                'use_momentum_confirmation': True,
                'use_volume_profile': False,
                'use_market_regime_filter': False,
                'scenario_name': f'Risk_Management_{i+1}'
            }
            combinations.append(combo)
        
        # Strategy 51-75: Session and time-based filters
        for i in range(25):
            combo = {
                'volatility_lookback': 100,
                'volatility_multiplier': 1.5,
                'bb_width_lookback': 20,
                'bb_width_multiplier': 1.2,
                'stop_loss_atr_multiplier': 2.0,
                'take_profit_atr_multiplier': 4.0,
                'trailing_stop_atr_multiplier': 1.5,
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'volume_threshold': 1.5,
                'atr_min_threshold': 1.0,
                'session_filter': np.random.choice(self.parameter_ranges['session_filter']),
                'avoid_news_hours': np.random.choice(self.parameter_ranges['avoid_news_hours']),
                'use_ml_filter': False,
                'use_momentum_confirmation': True,
                'use_volume_profile': np.random.choice(self.parameter_ranges['use_volume_profile']),
                'use_market_regime_filter': np.random.choice(self.parameter_ranges['use_market_regime_filter']),
                'scenario_name': f'Session_Filter_{i+1}'
            }
            combinations.append(combo)
        
        # Strategy 76-100: Advanced ML and hybrid approaches
        for i in range(25):
            combo = {
                'volatility_lookback': np.random.choice(self.parameter_ranges['volatility_lookback']),
                'volatility_multiplier': np.random.choice(self.parameter_ranges['volatility_multiplier']),
                'bb_width_lookback': np.random.choice(self.parameter_ranges['bb_width_lookback']),
                'bb_width_multiplier': np.random.choice(self.parameter_ranges['bb_width_multiplier']),
                'stop_loss_atr_multiplier': np.random.choice(self.parameter_ranges['stop_loss_atr_multiplier']),
                'take_profit_atr_multiplier': np.random.choice(self.parameter_ranges['take_profit_atr_multiplier']),
                'trailing_stop_atr_multiplier': np.random.choice(self.parameter_ranges['trailing_stop_atr_multiplier']),
                'rsi_oversold': np.random.choice(self.parameter_ranges['rsi_oversold']),
                'rsi_overbought': np.random.choice(self.parameter_ranges['rsi_overbought']),
                'volume_threshold': np.random.choice(self.parameter_ranges['volume_threshold']),
                'atr_min_threshold': np.random.choice(self.parameter_ranges['atr_min_threshold']),
                'session_filter': np.random.choice(self.parameter_ranges['session_filter']),
                'avoid_news_hours': np.random.choice(self.parameter_ranges['avoid_news_hours']),
                'use_ml_filter': True,
                'use_momentum_confirmation': True,
                'use_volume_profile': True,
                'use_market_regime_filter': True,
                'scenario_name': f'Advanced_ML_{i+1}'
            }
            combinations.append(combo)
        
        return combinations

    def advanced_volatility_strategy(self, df: pd.DataFrame, params: Dict) -> List[Dict]:
        """Advanced volatility breakout strategy with all optimizations"""
        signals = []
        
        # ML model for signal filtering (if enabled)
        ml_model = None
        scaler = None
        if params['use_ml_filter']:
            try:
                features = ['RSI', 'MACD', 'Stoch_K', 'Williams_R', 'Volume_Ratio', 'BB_Width', 'ATR', 'Trend_Strength']
                feature_data = df[features].dropna()
                target_data = df['Price_Change'].shift(-1).dropna()
                
                common_index = feature_data.index.intersection(target_data.index)
                X = feature_data.loc[common_index]
                y = target_data.loc[common_index]
                
                if len(X) > 100:
                    ml_model = GradientBoostingRegressor(n_estimators=50, random_state=42)
                    scaler = StandardScaler()
                    X_scaled = scaler.fit_transform(X)
                    
                    split_idx = int(len(X) * 0.7)
                    ml_model.fit(X_scaled[:split_idx], y[:split_idx])
            except Exception as e:
                self.logger.warning(f"ML model failed: {e}")
        
        for i in range(max(params['volatility_lookback'], 50), len(df)):
            try:
                current_time = df.index[i]
                
                # Session filtering
                if params['session_filter'] == 'london_ny' and df['London_NY_Overlap'].iloc[i] == 0:
                    continue
                elif params['session_filter'] == 'ny_only' and df['NY_Session'].iloc[i] == 0:
                    continue
                elif params['session_filter'] == 'london_only' and df['London_Session'].iloc[i] == 0:
                    continue
                
                # Avoid news hours
                if params['avoid_news_hours']:
                    hour = current_time.hour
                    minute = current_time.minute
                    if hour in [8, 10, 14, 16] and minute <= 30:
                        continue
                
                # Calculate dynamic volatility threshold
                vol_lookback = params['volatility_lookback']
                volatility_threshold = df['Volatility'].rolling(vol_lookback).mean().iloc[i] * params['volatility_multiplier']
                
                # Bollinger Band width filter
                bb_width_threshold = df['BB_Width'].rolling(params['bb_width_lookback']).mean().iloc[i] * params['bb_width_multiplier']
                
                # ATR minimum threshold
                atr_min = df['ATR'].rolling(20).mean().iloc[i] * params['atr_min_threshold']
                
                # Volume filter
                volume_condition = df['Volume_Ratio'].iloc[i] > params['volume_threshold']
                
                # Market regime filter
                regime_condition = True
                if params['use_market_regime_filter']:
                    regime_condition = df['Trend_Strength'].iloc[i] > 1.0
                
                # Main volatility breakout condition
                volatility_breakout = (df['Volatility'].iloc[i] > volatility_threshold and
                                     df['BB_Width'].iloc[i] > bb_width_threshold and
                                     df['ATR'].iloc[i] > atr_min and
                                     volume_condition and
                                     regime_condition)
                
                if not volatility_breakout:
                    continue
                
                # Determine direction
                direction = None
                entry_price = df['Close'].iloc[i]
                
                # Enhanced direction logic
                if df['Close'].iloc[i] > df['SMA_20'].iloc[i]:
                    # Bullish conditions
                    rsi_condition = df['RSI'].iloc[i] < params['rsi_overbought']
                    macd_condition = df['MACD'].iloc[i] > df['MACD_Signal'].iloc[i] if params['use_momentum_confirmation'] else True
                    
                    if rsi_condition and macd_condition:
                        direction = 'BUY'
                        stop_loss = entry_price - (df['ATR'].iloc[i] * params['stop_loss_atr_multiplier'])
                        take_profit = entry_price + (df['ATR'].iloc[i] * params['take_profit_atr_multiplier'])
                
                elif df['Close'].iloc[i] < df['SMA_20'].iloc[i]:
                    # Bearish conditions
                    rsi_condition = df['RSI'].iloc[i] > params['rsi_oversold']
                    macd_condition = df['MACD'].iloc[i] < df['MACD_Signal'].iloc[i] if params['use_momentum_confirmation'] else True
                    
                    if rsi_condition and macd_condition:
                        direction = 'SELL'
                        stop_loss = entry_price + (df['ATR'].iloc[i] * params['stop_loss_atr_multiplier'])
                        take_profit = entry_price - (df['ATR'].iloc[i] * params['take_profit_atr_multiplier'])
                
                if direction is None:
                    continue
                
                # ML filter
                ml_confidence = 50
                if params['use_ml_filter'] and ml_model is not None and scaler is not None:
                    try:
                        features = ['RSI', 'MACD', 'Stoch_K', 'Williams_R', 'Volume_Ratio', 'BB_Width', 'ATR', 'Trend_Strength']
                        feature_values = df[features].iloc[i].values.reshape(1, -1)
                        
                        # Check for NaN values
                        if np.isnan(feature_values).any():
                            continue
                            
                        feature_values_scaled = scaler.transform(feature_values)
                        prediction = ml_model.predict(feature_values_scaled)[0]
                        
                        # Filter based on ML prediction
                        if direction == 'BUY' and prediction < -0.001:
                            continue
                        elif direction == 'SELL' and prediction > 0.001:
                            continue
                        
                        ml_confidence = min(abs(prediction) * 1000, 100)
                    except Exception as e:
                        ml_confidence = 50
                
                # Calculate confidence score
                confidence = min(
                    (df['Volatility'].iloc[i] / volatility_threshold) * 30 +
                    (df['Volume_Ratio'].iloc[i] / params['volume_threshold']) * 20 +
                    ml_confidence * 0.5,
                    100
                )
                
                signal = {
                    'timestamp': current_time,
                    'direction': direction,
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'confidence': confidence,
                    'strategy': f"Advanced_Volatility_{params['scenario_name']}",
                    'atr': df['ATR'].iloc[i],
                    'volatility': df['Volatility'].iloc[i],
                    'volume_ratio': df['Volume_Ratio'].iloc[i],
                    'trailing_stop_atr': params['trailing_stop_atr_multiplier']
                }
                
                signals.append(signal)
                
            except Exception as e:
                continue
        
        return signals
    
    def simulate_trades(self, signals: List[Dict], df: pd.DataFrame, params: Dict) -> List[Dict]:
        """Simulate trade execution with advanced features"""
        trades = []
        
        for signal in signals:
            try:
                entry_time = signal['timestamp']
                entry_price = signal['entry_price']
                direction = signal['direction']
                stop_loss = signal['stop_loss']
                take_profit = signal['take_profit']
                
                # Find exit point
                entry_idx = df.index.get_loc(entry_time)
                exit_time = None
                exit_price = None
                exit_reason = 'timeout'
                
                # Look for exit within next 48 hours
                for j in range(entry_idx + 1, min(entry_idx + 49, len(df))):
                    current_price = df['Close'].iloc[j]
                    current_high = df['High'].iloc[j]
                    current_low = df['Low'].iloc[j]
                    current_time = df.index[j]
                    
                    # Check for stop loss or take profit
                    if direction == 'BUY':
                        # Trailing stop logic
                        if params['trailing_stop_atr_multiplier'] > 0:
                            new_stop = current_price - (df['ATR'].iloc[j] * params['trailing_stop_atr_multiplier'])
                            if new_stop > stop_loss:
                                stop_loss = new_stop
                        
                        if current_low <= stop_loss:
                            exit_price = stop_loss
                            exit_time = current_time
                            exit_reason = 'stop_loss'
                            break
                        elif current_high >= take_profit:
                            exit_price = take_profit
                            exit_time = current_time
                            exit_reason = 'take_profit'
                            break
                    
                    else:  # SELL
                        # Trailing stop logic
                        if params['trailing_stop_atr_multiplier'] > 0:
                            new_stop = current_price + (df['ATR'].iloc[j] * params['trailing_stop_atr_multiplier'])
                            if new_stop < stop_loss:
                                stop_loss = new_stop
                        
                        if current_high >= stop_loss:
                            exit_price = stop_loss
                            exit_time = current_time
                            exit_reason = 'stop_loss'
                            break
                        elif current_low <= take_profit:
                            exit_price = take_profit
                            exit_time = current_time
                            exit_reason = 'take_profit'
                            break
                
                # If no exit found, close at timeout
                if exit_time is None:
                    exit_idx = min(entry_idx + 48, len(df) - 1)
                    exit_time = df.index[exit_idx]
                    exit_price = df['Close'].iloc[exit_idx]
                    exit_reason = 'timeout'
                
                # Calculate P&L in pips (for gold, 1 pip = 0.1)
                if direction == 'BUY':
                    pnl = (exit_price - entry_price) * 10  # Convert to pips
                else:
                    pnl = (entry_price - exit_price) * 10  # Convert to pips
                
                # Apply transaction costs (2 pips)
                pnl -= 2
                
                trade = {
                    'entry_time': entry_time,
                    'exit_time': exit_time,
                    'direction': direction,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'exit_reason': exit_reason,
                    'confidence': signal['confidence'],
                    'duration_hours': (exit_time - entry_time).total_seconds() / 3600,
                    'atr_at_entry': signal.get('atr', 0),
                    'volatility_at_entry': signal.get('volatility', 0),
                    'volume_ratio_at_entry': signal.get('volume_ratio', 0)
                }
                
                trades.append(trade)
                
            except Exception as e:
                continue
        
        return trades
    
    def calculate_performance_metrics(self, trades: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        if not trades:
            return {
                'total_trades': 0, 'win_rate': 0, 'profit_factor': 0, 'total_pips': 0,
                'avg_win': 0, 'avg_loss': 0, 'max_drawdown': 0, 'sharpe_ratio': 0,
                'sortino_ratio': 0, 'calmar_ratio': 0, 'avg_confidence': 0,
                'wins': 0, 'losses': 0, 'max_consecutive_wins': 0,
                'max_consecutive_losses': 0, 'profit_per_week': 0,
                'risk_reward_ratio': 0, 'trades_per_week': 0
            }
        
        # Basic metrics
        total_trades = len(trades)
        wins = [t for t in trades if t['pnl'] > 0]
        losses = [t for t in trades if t['pnl'] <= 0]
        
        win_count = len(wins)
        loss_count = len(losses)
        win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0
        
        total_pips = sum([t['pnl'] for t in trades])
        gross_profit = sum([t['pnl'] for t in wins])
        gross_loss = abs(sum([t['pnl'] for t in losses]))
        
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        avg_win = gross_profit / win_count if win_count > 0 else 0
        avg_loss = gross_loss / loss_count if loss_count > 0 else 0
        
        # Risk metrics
        returns = [t['pnl'] for t in trades]
        cumulative_returns = np.cumsum(returns)
        
        max_drawdown = 0
        peak = 0
        for ret in cumulative_returns:
            if ret > peak:
                peak = ret
            drawdown = peak - ret
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Sharpe ratio
        if len(returns) > 1:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
            downside_returns = [r for r in returns if r < 0]
            downside_std = np.std(downside_returns) if downside_returns else 0
            sortino_ratio = np.mean(returns) / downside_std * np.sqrt(252) if downside_std > 0 else 0
        else:
            sharpe_ratio = 0
            sortino_ratio = 0
        
        # Calmar ratio
        calmar_ratio = (total_pips / max_drawdown) if max_drawdown > 0 else 0
        
        # Consecutive wins/losses
        consecutive_wins = 0
        consecutive_losses = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        
        for trade in trades:
            if trade['pnl'] > 0:
                consecutive_wins += 1
                consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
            else:
                consecutive_losses += 1
                consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
        
        # Additional metrics
        avg_confidence = np.mean([t.get('confidence', 50) for t in trades])
        risk_reward_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        profit_per_week = total_pips / 12  # 2000 hours ≈ 12 weeks
        
        return {
            'total_trades': total_trades,
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 3),
            'total_pips': round(total_pips, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe_ratio': round(sharpe_ratio, 3),
            'sortino_ratio': round(sortino_ratio, 3),
            'calmar_ratio': round(calmar_ratio, 3),
            'avg_confidence': round(avg_confidence, 1),
            'wins': win_count,
            'losses': loss_count,
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses,
            'profit_per_week': round(profit_per_week, 2),
            'risk_reward_ratio': round(risk_reward_ratio, 2),
            'trades_per_week': round(total_trades / 12, 1)
        }
    
    def run_optimization(self) -> Dict[str, Any]:
        """Run comprehensive optimization across 100 scenarios"""
        
        self.logger.info("🚀 Starting Advanced XAU_USD Volatility Strategy Optimization")
        self.logger.info("Testing 100 different scenarios with world-class parameter combinations")
        
        # Load data
        df = self.load_data()
        df = self.calculate_advanced_indicators(df)
        
        # Use last 2000 candles for consistency
        test_data = df.tail(2000).copy()
        
        # Generate parameter combinations
        parameter_combinations = self.generate_parameter_combinations()
        
        self.logger.info(f"Generated {len(parameter_combinations)} parameter combinations")
        
        # Test each scenario
        results = []
        for i, params in enumerate(parameter_combinations):
            try:
                self.logger.info(f"Testing Scenario {i+1}/100: {params['scenario_name']}")
                
                # Generate signals
                signals = self.advanced_volatility_strategy(test_data, params)
                
                if not signals:
                    continue
                
                # Simulate trades
                trades = self.simulate_trades(signals, test_data, params)
                
                if not trades:
                    continue
                
                # Calculate metrics
                metrics = self.calculate_performance_metrics(trades)
                
                # Combine results
                result = {
                    'scenario_id': i + 1,
                    'scenario_name': params['scenario_name'],
                    'parameters': params,
                    'performance': metrics,
                    'signals_generated': len(signals),
                    'trades_executed': len(trades)
                }
                
                results.append(result)
                
                # Log key metrics
                self.logger.info(f"  Trades: {metrics['total_trades']}, Win Rate: {metrics['win_rate']}%, "
                               f"Profit Factor: {metrics['profit_factor']}, Total Pips: {metrics['total_pips']}")
                
            except Exception as e:
                self.logger.error(f"Error in scenario {i+1}: {e}")
                continue
        
        # Sort results by composite score
        if results:
            for result in results:
                perf = result['performance']
                composite_score = (
                    perf['profit_factor'] * 0.3 +
                    perf['win_rate'] * 0.002 +
                    (perf['total_pips'] / 10000) * 0.3 +
                    perf['sharpe_ratio'] * 0.2 +
                    (100 / max(perf['max_drawdown'], 1)) * 0.2
                )
                result['composite_score'] = composite_score
            
            results.sort(key=lambda x: x['composite_score'], reverse=True)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"/Users/mac/SharedNetwork/quant_strategy_ai/deep_backtesting/results/xau_usd_optimization_{timestamp}.json"
        
        optimization_summary = {
            'optimization_timestamp': timestamp,
            'total_scenarios_tested': len(parameter_combinations),
            'successful_scenarios': len(results),
            'data_period': {
                'start': str(test_data.index[0]),
                'end': str(test_data.index[-1]),
                'total_candles': len(test_data)
            },
            'results': results
        }
        
        with open(results_file, 'w') as f:
            json.dump(optimization_summary, f, indent=2, default=str)
        
        self.logger.info(f"Optimization complete! Results saved to: {results_file}")
        
        return optimization_summary
    
    def print_top_results(self, optimization_results: Dict, top_n: int = 10):
        """Print top performing scenarios"""
        
        results = optimization_results['results'][:top_n]
        
        print("\n" + "="*120)
        print("🏆 TOP 10 XAU_USD VOLATILITY STRATEGY OPTIMIZATIONS")
        print("="*120)
        
        for i, result in enumerate(results):
            perf = result['performance']
            params = result['parameters']
            
            print(f"\n🥇 RANK #{i+1}: {result['scenario_name']}")
            print(f"   Composite Score: {result['composite_score']:.3f}")
            print(f"   📊 Performance:")
            print(f"      • Total Trades: {perf['total_trades']} ({perf['trades_per_week']} per week)")
            print(f"      • Win Rate: {perf['win_rate']}%")
            print(f"      • Profit Factor: {perf['profit_factor']}")
            print(f"      • Total Pips: {perf['total_pips']:,.0f}")
            print(f"      • Sharpe Ratio: {perf['sharpe_ratio']}")
            print(f"      • Max Drawdown: {perf['max_drawdown']:,.0f}")
            print(f"      • Risk/Reward: {perf['risk_reward_ratio']}")
            print(f"   🔧 Key Parameters:")
            print(f"      • Volatility: {params['volatility_lookback']} bars, {params['volatility_multiplier']}x multiplier")
            print(f"      • Risk Management: SL={params['stop_loss_atr_multiplier']}x ATR, TP={params['take_profit_atr_multiplier']}x ATR")
            print(f"      • Session Filter: {params['session_filter']}")
            print(f"      • Advanced Features: ML={params['use_ml_filter']}, Momentum={params['use_momentum_confirmation']}")
        
        print("\n" + "="*120)

if __name__ == "__main__":
    optimizer = AdvancedXAUUSDVolatilityOptimizer()
    results = optimizer.run_optimization()
    optimizer.print_top_results(results)

