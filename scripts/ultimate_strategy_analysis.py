#!/usr/bin/env python3
"""
ULTIMATE STRATEGY ANALYSIS
Comprehensive testing of multiple strategies and experimental theories
"""

import pandas as pd
import numpy as np
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
import sys
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_optimized_strategy import EnhancedOptimizedStrategy
from live_optimized_strategies import LiveOptimizedStrategyManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UltimateStrategyAnalyzer:
    """Comprehensive strategy analysis and testing"""
    
    def __init__(self):
        self.results = {}
        self.logger = logging.getLogger(__name__)
        
    def load_all_data(self) -> Dict[str, pd.DataFrame]:
        """Load all available historical data"""
        data_files = {
            'EUR_USD': 'data/historical/prices/eur_usd_1h.csv',
            'GBP_USD': 'data/historical/prices/gbp_usd_1h.csv',
            'USD_JPY': 'data/historical/prices/usd_jpy_1h.csv',
            'AUD_USD': 'data/historical/prices/aud_usd_1h.csv',
            'USD_CAD': 'data/historical/prices/usd_cad_1h.csv',
            'XAU_USD': 'data/historical/prices/xau_usd_1h.csv'
        }
        
        data = {}
        for symbol, file_path in data_files.items():
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                data[symbol] = df
                self.logger.info(f"Loaded {len(df)} candles for {symbol}")
        
        return data
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators"""
        # Basic indicators
        df['SMA_20'] = df['Close'].rolling(20).mean()
        df['SMA_50'] = df['Close'].rolling(50).mean()
        df['EMA_20'] = df['Close'].ewm(span=20).mean()
        df['EMA_50'] = df['Close'].ewm(span=50).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12).mean()
        exp2 = df['Close'].ewm(span=26).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(20).mean()
        bb_std = df['Close'].rolling(20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        # Stochastic
        low_min = df['Low'].rolling(14).min()
        high_max = df['High'].rolling(14).max()
        df['Stoch_K'] = 100 * ((df['Close'] - low_min) / (high_max - low_min))
        df['Stoch_D'] = df['Stoch_K'].rolling(3).mean()
        
        # Williams %R
        df['Williams_R'] = -100 * ((high_max - df['Close']) / (high_max - low_min))
        
        # Volume indicators
        df['Volume_SMA'] = df['Volume'].rolling(20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
        
        # Price action
        df['Price_Change'] = df['Close'].pct_change()
        df['Price_Change_5'] = df['Close'].pct_change(5)
        df['Price_Change_20'] = df['Close'].pct_change(20)
        
        # Volatility
        df['Volatility'] = df['Price_Change'].rolling(20).std()
        
        return df
    
    def strategy_1_momentum_breakout(self, df: pd.DataFrame) -> List[Dict]:
        """Momentum breakout strategy"""
        signals = []
        for i in range(50, len(df)):
            if (df['Close'].iloc[i] > df['BB_Upper'].iloc[i] and 
                df['Volume_Ratio'].iloc[i] > 1.5 and
                df['RSI'].iloc[i] < 80):
                signals.append({
                    'timestamp': df.index[i],
                    'direction': 'BUY',
                    'entry_price': df['Close'].iloc[i],
                    'stop_loss': df['SMA_20'].iloc[i],
                    'take_profit': df['Close'].iloc[i] + (df['ATR'].iloc[i] * 3),
                    'confidence': min(df['Volume_Ratio'].iloc[i] * 20, 100),
                    'strategy': 'Momentum_Breakout'
                })
            elif (df['Close'].iloc[i] < df['BB_Lower'].iloc[i] and 
                  df['Volume_Ratio'].iloc[i] > 1.5 and
                  df['RSI'].iloc[i] > 20):
                signals.append({
                    'timestamp': df.index[i],
                    'direction': 'SELL',
                    'entry_price': df['Close'].iloc[i],
                    'stop_loss': df['SMA_20'].iloc[i],
                    'take_profit': df['Close'].iloc[i] - (df['ATR'].iloc[i] * 3),
                    'confidence': min(df['Volume_Ratio'].iloc[i] * 20, 100),
                    'strategy': 'Momentum_Breakout'
                })
        return signals
    
    def strategy_2_mean_reversion(self, df: pd.DataFrame) -> List[Dict]:
        """Mean reversion strategy"""
        signals = []
        for i in range(50, len(df)):
            if (df['RSI'].iloc[i] < 30 and 
                df['Close'].iloc[i] < df['BB_Lower'].iloc[i] and
                df['Stoch_K'].iloc[i] < 20):
                signals.append({
                    'timestamp': df.index[i],
                    'direction': 'BUY',
                    'entry_price': df['Close'].iloc[i],
                    'stop_loss': df['Close'].iloc[i] - (df['ATR'].iloc[i] * 2),
                    'take_profit': df['SMA_50'].iloc[i],
                    'confidence': 100 - df['RSI'].iloc[i],
                    'strategy': 'Mean_Reversion'
                })
            elif (df['RSI'].iloc[i] > 70 and 
                  df['Close'].iloc[i] > df['BB_Upper'].iloc[i] and
                  df['Stoch_K'].iloc[i] > 80):
                signals.append({
                    'timestamp': df.index[i],
                    'direction': 'SELL',
                    'entry_price': df['Close'].iloc[i],
                    'stop_loss': df['Close'].iloc[i] + (df['ATR'].iloc[i] * 2),
                    'take_profit': df['SMA_50'].iloc[i],
                    'confidence': df['RSI'].iloc[i] - 30,
                    'strategy': 'Mean_Reversion'
                })
        return signals
    
    def strategy_3_trend_following(self, df: pd.DataFrame) -> List[Dict]:
        """Trend following strategy"""
        signals = []
        for i in range(50, len(df)):
            if (df['EMA_20'].iloc[i] > df['EMA_50'].iloc[i] and
                df['MACD'].iloc[i] > df['MACD_Signal'].iloc[i] and
                df['Close'].iloc[i] > df['EMA_20'].iloc[i] and
                df['RSI'].iloc[i] > 40 and df['RSI'].iloc[i] < 70):
                signals.append({
                    'timestamp': df.index[i],
                    'direction': 'BUY',
                    'entry_price': df['Close'].iloc[i],
                    'stop_loss': df['EMA_20'].iloc[i],
                    'take_profit': df['Close'].iloc[i] + (df['ATR'].iloc[i] * 4),
                    'confidence': 70,
                    'strategy': 'Trend_Following'
                })
            elif (df['EMA_20'].iloc[i] < df['EMA_50'].iloc[i] and
                  df['MACD'].iloc[i] < df['MACD_Signal'].iloc[i] and
                  df['Close'].iloc[i] < df['EMA_20'].iloc[i] and
                  df['RSI'].iloc[i] > 30 and df['RSI'].iloc[i] < 60):
                signals.append({
                    'timestamp': df.index[i],
                    'direction': 'SELL',
                    'entry_price': df['Close'].iloc[i],
                    'stop_loss': df['EMA_20'].iloc[i],
                    'take_profit': df['Close'].iloc[i] - (df['ATR'].iloc[i] * 4),
                    'confidence': 70,
                    'strategy': 'Trend_Following'
                })
        return signals
    
    def strategy_4_volatility_breakout(self, df: pd.DataFrame) -> List[Dict]:
        """Volatility breakout strategy"""
        signals = []
        for i in range(50, len(df)):
            volatility_threshold = df['Volatility'].rolling(100).mean().iloc[i] * 1.5
            if (df['Volatility'].iloc[i] > volatility_threshold and
                df['BB_Width'].iloc[i] > df['BB_Width'].rolling(20).mean().iloc[i] * 1.2):
                if df['Close'].iloc[i] > df['SMA_20'].iloc[i]:
                    signals.append({
                        'timestamp': df.index[i],
                        'direction': 'BUY',
                        'entry_price': df['Close'].iloc[i],
                        'stop_loss': df['Close'].iloc[i] - (df['ATR'].iloc[i] * 2),
                        'take_profit': df['Close'].iloc[i] + (df['ATR'].iloc[i] * 4),
                        'confidence': min(df['Volatility'].iloc[i] * 100, 100),
                        'strategy': 'Volatility_Breakout'
                    })
                else:
                    signals.append({
                        'timestamp': df.index[i],
                        'direction': 'SELL',
                        'entry_price': df['Close'].iloc[i],
                        'stop_loss': df['Close'].iloc[i] + (df['ATR'].iloc[i] * 2),
                        'take_profit': df['Close'].iloc[i] - (df['ATR'].iloc[i] * 4),
                        'confidence': min(df['Volatility'].iloc[i] * 100, 100),
                        'strategy': 'Volatility_Breakout'
                    })
        return signals
    
    def strategy_5_machine_learning(self, df: pd.DataFrame) -> List[Dict]:
        """Machine learning based strategy"""
        signals = []
        
        # Prepare features
        features = ['RSI', 'MACD', 'Stoch_K', 'Williams_R', 'Volume_Ratio', 'BB_Width', 'ATR']
        X = df[features].dropna()
        y = df['Price_Change'].shift(-1).dropna()
        
        # Align data
        common_index = X.index.intersection(y.index)
        X = X.loc[common_index]
        y = y.loc[common_index]
        
        if len(X) < 100:
            return signals
        
        # Train model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Use last 80% for training
        split_idx = int(len(X) * 0.8)
        model.fit(X_scaled[:split_idx], y[:split_idx])
        
        # Generate predictions for remaining data
        for i in range(split_idx, len(X)):
            prediction = model.predict([X_scaled[i]])[0]
            if abs(prediction) > 0.001:  # Significant prediction
                signals.append({
                    'timestamp': X.index[i],
                    'direction': 'BUY' if prediction > 0 else 'SELL',
                    'entry_price': df.loc[X.index[i], 'Close'],
                    'stop_loss': df.loc[X.index[i], 'Close'] * (0.995 if prediction > 0 else 1.005),
                    'take_profit': df.loc[X.index[i], 'Close'] * (1.01 if prediction > 0 else 0.99),
                    'confidence': min(abs(prediction) * 1000, 100),
                    'strategy': 'Machine_Learning'
                })
        
        return signals
    
    def strategy_6_time_based(self, df: pd.DataFrame) -> List[Dict]:
        """Time-based strategy (London/NY overlap)"""
        signals = []
        for i in range(50, len(df)):
            hour = df.index[i].hour
            # London/NY overlap (13:00-17:00 UTC)
            if 13 <= hour <= 17:
                if (df['RSI'].iloc[i] > 50 and df['EMA_20'].iloc[i] > df['EMA_50'].iloc[i]):
                    signals.append({
                        'timestamp': df.index[i],
                        'direction': 'BUY',
                        'entry_price': df['Close'].iloc[i],
                        'stop_loss': df['EMA_20'].iloc[i],
                        'take_profit': df['Close'].iloc[i] + (df['ATR'].iloc[i] * 3),
                        'confidence': 80,
                        'strategy': 'Time_Based'
                    })
                elif (df['RSI'].iloc[i] < 50 and df['EMA_20'].iloc[i] < df['EMA_50'].iloc[i]):
                    signals.append({
                        'timestamp': df.index[i],
                        'direction': 'SELL',
                        'entry_price': df['Close'].iloc[i],
                        'stop_loss': df['EMA_20'].iloc[i],
                        'take_profit': df['Close'].iloc[i] - (df['ATR'].iloc[i] * 3),
                        'confidence': 80,
                        'strategy': 'Time_Based'
                    })
        return signals
    
    def strategy_7_enhanced_hybrid(self, df: pd.DataFrame) -> List[Dict]:
        """Enhanced hybrid strategy combining multiple approaches"""
        signals = []
        for i in range(50, len(df)):
            score = 0
            direction = None
            
            # Trend score
            if df['EMA_20'].iloc[i] > df['EMA_50'].iloc[i]:
                score += 20
                direction = 'BUY'
            elif df['EMA_20'].iloc[i] < df['EMA_50'].iloc[i]:
                score += 20
                direction = 'SELL'
            
            # Momentum score
            if df['MACD'].iloc[i] > df['MACD_Signal'].iloc[i]:
                score += 15
            elif df['MACD'].iloc[i] < df['MACD_Signal'].iloc[i]:
                score -= 15
            
            # RSI score
            if 30 < df['RSI'].iloc[i] < 70:
                score += 15
            elif df['RSI'].iloc[i] < 30 or df['RSI'].iloc[i] > 70:
                score -= 10
            
            # Volume score
            if df['Volume_Ratio'].iloc[i] > 1.2:
                score += 10
            
            # Volatility score
            if df['BB_Width'].iloc[i] > df['BB_Width'].rolling(20).mean().iloc[i]:
                score += 10
            
            # Time score
            hour = df.index[i].hour
            if 13 <= hour <= 17:  # London/NY overlap
                score += 10
            
            # Generate signal if score is high enough
            if score >= 40 and direction:
                signals.append({
                    'timestamp': df.index[i],
                    'direction': direction,
                    'entry_price': df['Close'].iloc[i],
                    'stop_loss': df['Close'].iloc[i] - (df['ATR'].iloc[i] * 2) if direction == 'BUY' else df['Close'].iloc[i] + (df['ATR'].iloc[i] * 2),
                    'take_profit': df['Close'].iloc[i] + (df['ATR'].iloc[i] * 4) if direction == 'BUY' else df['Close'].iloc[i] - (df['ATR'].iloc[i] * 4),
                    'confidence': min(score, 100),
                    'strategy': 'Enhanced_Hybrid'
                })
        
        return signals
    
    def simulate_trades(self, signals: List[Dict], df: pd.DataFrame) -> List[Dict]:
        """Simulate trades from signals"""
        trades = []
        for signal in signals:
            entry_idx = df.index.get_loc(signal['timestamp'])
            entry_price = signal['entry_price']
            direction = signal['direction']
            stop_loss = signal['stop_loss']
            take_profit = signal['take_profit']
            
            # Simulate trade progression
            for i in range(entry_idx + 1, len(df)):
                current_price = df.iloc[i]['Close']
                
                if direction == 'BUY':
                    if current_price <= stop_loss:
                        trades.append({
                            'entry_time': signal['timestamp'],
                            'exit_time': df.index[i],
                            'entry_price': entry_price,
                            'exit_price': stop_loss,
                            'direction': direction,
                            'status': 'LOSS',
                            'pips': (stop_loss - entry_price) * 10000 if 'JPY' not in str(signal.get('pair', '')) else (stop_loss - entry_price) * 100,
                            'strategy': signal['strategy'],
                            'confidence': signal['confidence']
                        })
                        break
                    elif current_price >= take_profit:
                        trades.append({
                            'entry_time': signal['timestamp'],
                            'exit_time': df.index[i],
                            'entry_price': entry_price,
                            'exit_price': take_profit,
                            'direction': direction,
                            'status': 'WIN',
                            'pips': (take_profit - entry_price) * 10000 if 'JPY' not in str(signal.get('pair', '')) else (take_profit - entry_price) * 100,
                            'strategy': signal['strategy'],
                            'confidence': signal['confidence']
                        })
                        break
                else:  # SELL
                    if current_price >= stop_loss:
                        trades.append({
                            'entry_time': signal['timestamp'],
                            'exit_time': df.index[i],
                            'entry_price': entry_price,
                            'exit_price': stop_loss,
                            'direction': direction,
                            'status': 'LOSS',
                            'pips': (entry_price - stop_loss) * 10000 if 'JPY' not in str(signal.get('pair', '')) else (entry_price - stop_loss) * 100,
                            'strategy': signal['strategy'],
                            'confidence': signal['confidence']
                        })
                        break
                    elif current_price <= take_profit:
                        trades.append({
                            'entry_time': signal['timestamp'],
                            'exit_time': df.index[i],
                            'entry_price': entry_price,
                            'exit_price': take_profit,
                            'direction': direction,
                            'status': 'WIN',
                            'pips': (entry_price - take_profit) * 10000 if 'JPY' not in str(signal.get('pair', '')) else (entry_price - take_profit) * 100,
                            'strategy': signal['strategy'],
                            'confidence': signal['confidence']
                        })
                        break
        
        return trades
    
    def calculate_performance_metrics(self, trades: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'total_pips': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'avg_confidence': 0
            }
        
        wins = [t for t in trades if t['status'] == 'WIN']
        losses = [t for t in trades if t['status'] == 'LOSS']
        
        total_trades = len(trades)
        win_rate = len(wins) / total_trades * 100 if total_trades > 0 else 0
        
        total_pips = sum(t['pips'] for t in trades)
        avg_win = np.mean([t['pips'] for t in wins]) if wins else 0
        avg_loss = np.mean([abs(t['pips']) for t in losses]) if losses else 0
        
        total_wins = sum(t['pips'] for t in wins) if wins else 0
        total_losses = sum(abs(t['pips']) for t in losses) if losses else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Drawdown calculation
        cumulative_pips = []
        running_total = 0
        for trade in trades:
            running_total += trade['pips']
            cumulative_pips.append(running_total)
        
        if cumulative_pips:
            peak = max(cumulative_pips)
            max_drawdown = min(cumulative_pips) - peak
        else:
            max_drawdown = 0
        
        # Sharpe ratio
        returns = [t['pips'] for t in trades]
        if returns:
            sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        avg_confidence = np.mean([t['confidence'] for t in trades]) if trades else 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_pips': total_pips,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'avg_confidence': avg_confidence,
            'wins': len(wins),
            'losses': len(losses)
        }
    
    def run_comprehensive_analysis(self):
        """Run comprehensive analysis on all strategies"""
        self.logger.info("🚀 Starting Ultimate Strategy Analysis...")
        
        # Load data
        data = self.load_all_data()
        if not data:
            self.logger.error("No data available")
            return
        
        # Test on last 2000 candles for each symbol
        results_table = []
        
        for symbol, df in data.items():
            self.logger.info(f"Analyzing {symbol}...")
            
            # Use last 2000 candles
            test_data = df.tail(2000).copy()
            test_data = self.calculate_technical_indicators(test_data)
            
            # Define strategies
            strategies = [
                ('Momentum_Breakout', self.strategy_1_momentum_breakout),
                ('Mean_Reversion', self.strategy_2_mean_reversion),
                ('Trend_Following', self.strategy_3_trend_following),
                ('Volatility_Breakout', self.strategy_4_volatility_breakout),
                ('Machine_Learning', self.strategy_5_machine_learning),
                ('Time_Based', self.strategy_6_time_based),
                ('Enhanced_Hybrid', self.strategy_7_enhanced_hybrid)
            ]
            
            for strategy_name, strategy_func in strategies:
                try:
                    # Generate signals
                    signals = strategy_func(test_data)
                    
                    # Simulate trades
                    trades = self.simulate_trades(signals, test_data)
                    
                    # Calculate performance
                    performance = self.calculate_performance_metrics(trades)
                    
                    # Add to results
                    results_table.append({
                        'Symbol': symbol,
                        'Strategy': strategy_name,
                        'Total_Trades': performance['total_trades'],
                        'Win_Rate_%': round(performance['win_rate'], 1),
                        'Profit_Factor': round(performance['profit_factor'], 2),
                        'Total_Pips': round(performance['total_pips'], 1),
                        'Avg_Win': round(performance['avg_win'], 1),
                        'Avg_Loss': round(performance['avg_loss'], 1),
                        'Max_Drawdown': round(performance['max_drawdown'], 1),
                        'Sharpe_Ratio': round(performance['sharpe_ratio'], 2),
                        'Avg_Confidence': round(performance['avg_confidence'], 1),
                        'Wins': performance['wins'],
                        'Losses': performance['losses']
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error testing {strategy_name} on {symbol}: {e}")
                    continue
        
        # Create results DataFrame
        results_df = pd.DataFrame(results_table)
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"results/ultimate_strategy_analysis_{timestamp}.csv"
        results_df.to_csv(results_file, index=False)
        
        # Print comprehensive results table
        print("\n" + "="*120)
        print("🎯 ULTIMATE STRATEGY ANALYSIS RESULTS")
        print("="*120)
        print(results_df.to_string(index=False))
        print("\n" + "="*120)
        
        # Find best strategies
        print("\n🏆 TOP PERFORMING STRATEGIES BY METRIC:")
        print("-" * 60)
        
        # Best by Win Rate
        best_win_rate = results_df.nlargest(5, 'Win_Rate_%')[['Symbol', 'Strategy', 'Win_Rate_%', 'Total_Trades']]
        print(f"\n🥇 Best Win Rate:")
        print(best_win_rate.to_string(index=False))
        
        # Best by Profit Factor
        best_profit_factor = results_df.nlargest(5, 'Profit_Factor')[['Symbol', 'Strategy', 'Profit_Factor', 'Total_Trades']]
        print(f"\n💰 Best Profit Factor:")
        print(best_profit_factor.to_string(index=False))
        
        # Best by Total Pips
        best_pips = results_df.nlargest(5, 'Total_Pips')[['Symbol', 'Strategy', 'Total_Pips', 'Win_Rate_%']]
        print(f"\n📈 Best Total Pips:")
        print(best_pips.to_string(index=False))
        
        # Best by Sharpe Ratio
        best_sharpe = results_df.nlargest(5, 'Sharpe_Ratio')[['Symbol', 'Strategy', 'Sharpe_Ratio', 'Win_Rate_%']]
        print(f"\n📊 Best Sharpe Ratio:")
        print(best_sharpe.to_string(index=False))
        
        print(f"\n📊 Detailed results saved to: {results_file}")
        print("="*120)

if __name__ == "__main__":
    # Create results directory if it doesn't exist
    os.makedirs("results", exist_ok=True)
    
    # Run comprehensive analysis
    analyzer = UltimateStrategyAnalyzer()
    analyzer.run_comprehensive_analysis()
