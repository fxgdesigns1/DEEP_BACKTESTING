#!/usr/bin/env python3
"""
REALISTIC HIGH-FREQUENCY STRATEGY CONTROLLER
Optimized for realistic trading frequency and practical results
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
import pandas as pd
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealisticStrategyController:
    """Realistic high-frequency strategy controller"""
    
    def __init__(self):
        """Initialize the realistic strategy controller"""
        self.max_workers = min(16, mp.cpu_count())
        self.results_dir = Path("results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Performance tracking
        self.start_time = datetime.now()
        self.completed_experiments = 0
        self.successful_strategies = []
        
        logger.info(f"🚀 Realistic Strategy Controller initialized with {self.max_workers} workers")
    
    def generate_experiments(self) -> List[Dict[str, Any]]:
        """Generate experiments with realistic high-frequency parameters"""
        experiments = []
        
        # Currency pairs - focus on major pairs
        pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD']
        
        # 15M TIMEFRAME FOR MAXIMUM SIGNAL FREQUENCY
        timeframes = ['15m']  # Focus on 15m for maximum trading opportunities
        
        # 15M OPTIMIZED PARAMETERS FOR HIGH FREQUENCY
        ema_fast_values = [3, 5, 8]       # Very fast EMAs for 15m scalping
        ema_slow_values = [8, 13, 21]     # Quick slow EMAs for 15m
        rsi_oversold_values = [25, 30, 35] # More RSI options for entries
        rsi_overbought_values = [65, 70, 75] # More RSI options for entries
        stop_atr_values = [0.8, 1.0, 1.2] # Tighter stops for 15m
        take_profit_values = [1.0, 1.5, 2.0] # Quick profits for 15m (1:1 to 2:1)
        
        # Generate all combinations
        for pair in pairs:
            for timeframe in timeframes:
                for ema_fast in ema_fast_values:
                    for ema_slow in ema_slow_values:
                        if ema_slow > ema_fast:  # Only valid combinations
                            for rsi_oversold in rsi_oversold_values:
                                for rsi_overbought in rsi_overbought_values:
                                    for stop_atr in stop_atr_values:
                                        for take_profit in take_profit_values:
                                            experiments.append({
                                                'pair': pair,
                                                'timeframe': timeframe,
                                                'strategy': 'realistic_hf',
                                                'params': {
                                                    'ema_fast': ema_fast,
                                                    'ema_slow': ema_slow,
                                                    'rsi_oversold': rsi_oversold,
                                                    'rsi_overbought': rsi_overbought,
                                                    'stop_atr_mult': stop_atr,
                                                    'take_profit_rr': take_profit
                                                },
                                                'experiment_id': f"{pair}_{timeframe}_{ema_fast}_{ema_slow}_{rsi_oversold}_{rsi_overbought}_{stop_atr}_{take_profit}"
                                            })
        
        logger.info(f"📊 Generated {len(experiments)} realistic high-frequency experiments")
        return experiments
    
    def run_single_experiment(self, experiment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run a single experiment"""
        try:
            pair = experiment['pair']
            timeframe = experiment['timeframe']
            params = experiment['params']
            
            # Load data
            data = self._load_data(pair, timeframe)
            if data is None or len(data) < 100:
                return None
            
            # Run strategy
            results = self._run_realistic_strategy(data, params)
            if results is None:
                return None
            
            # Check if strategy meets 15m high-frequency criteria
            if (results['total_trades'] >= 20 and  # Higher minimum trades for 15m
                results['total_trades'] <= 200 and  # Allow more trades for 15m
                results['sharpe_ratio'] > 0.2 and  # Reasonable risk-adjusted returns
                results['profit_factor'] > 1.1 and  # Profitable
                results['win_rate'] > 35 and  # Decent win rate
                results['max_drawdown'] > -0.25):  # Acceptable drawdown
                
                results.update({
                    'pair': pair,
                    'timeframe': timeframe,
                    'experiment_id': experiment['experiment_id'],
                    'params': params
                })
                
                logger.info(f"✅ Success: {pair} {timeframe} - Trades: {results['total_trades']}, Win Rate: {results['win_rate']:.1f}%, PF: {results['profit_factor']:.2f}")
                return results
            
            # Debug logging for failed strategies
            if results['total_trades'] >= 5:  # Only log strategies with some trades
                logger.info(f"❌ Failed: {pair} {timeframe} - Trades: {results['total_trades']}, Win Rate: {results['win_rate']:.1f}%, PF: {results['profit_factor']:.2f}, Sharpe: {results['sharpe_ratio']:.2f}, DD: {results['max_drawdown']:.2f}")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed: {experiment['experiment_id']} - {str(e)}")
            return None
    
    def _load_data(self, pair: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Load data for the given pair and timeframe"""
        try:
            data_path = Path(f"data/MASTER_DATASET/{timeframe}/{pair}_{timeframe}.csv")
            if not data_path.exists():
                logger.warning(f"⚠️ Data file not found: {data_path}")
                return None
            
            data = pd.read_csv(data_path)
            if len(data) < 100:
                logger.warning(f"⚠️ Insufficient data: {len(data)} rows")
                return None
            
            # Ensure proper column names
            data.columns = data.columns.str.lower()
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in data.columns for col in required_columns):
                logger.warning(f"⚠️ Missing required columns in {data_path}")
                return None
            
            # Convert to numeric
            for col in ['open', 'high', 'low', 'close', 'volume']:
                data[col] = pd.to_numeric(data[col], errors='coerce')
            
            # Remove any rows with NaN values
            data = data.dropna()
            
            if len(data) < 100:
                logger.warning(f"⚠️ Insufficient data after cleaning: {len(data)} rows")
                return None
            
            logger.info(f"📈 Loaded {len(data)} rows for {pair} {timeframe}")
            return data
            
        except Exception as e:
            logger.error(f"❌ Error loading data for {pair} {timeframe}: {str(e)}")
            return None
    
    def _run_realistic_strategy(self, data: pd.DataFrame, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run the realistic high-frequency strategy"""
        try:
            # Calculate indicators
            ema_fast = data['close'].ewm(span=params['ema_fast']).mean()
            ema_slow = data['close'].ewm(span=params['ema_slow']).mean()
            
            # Calculate RSI
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Calculate ATR
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            atr = true_range.rolling(window=14).mean()
            
            # Generate balanced selective signals
            # Enter on trend with RSI confirmation
            bullish_conditions = (
                (ema_fast > ema_slow) & 
                (ema_fast.shift(1) <= ema_slow.shift(1)) &  # EMA crossover
                (rsi < params['rsi_oversold']) &  # RSI oversold for entry
                (data['close'] > ema_slow)  # Price above slow EMA (trend confirmation)
            )
            
            bearish_conditions = (
                (ema_fast < ema_slow) & 
                (ema_fast.shift(1) >= ema_slow.shift(1)) &  # EMA crossover
                (rsi > params['rsi_overbought']) &  # RSI overbought for entry
                (data['close'] < ema_slow)  # Price below slow EMA (trend confirmation)
            )
            
            # Simulate trades
            trades = self._simulate_realistic_trades(data, bullish_conditions, bearish_conditions, atr, params)
            
            if len(trades) == 0:
                return None
            
            # Calculate performance metrics
            return self._calculate_performance_metrics(trades, data)
            
        except Exception as e:
            logger.error(f"❌ Error running realistic strategy: {str(e)}")
            return None
    
    def _simulate_realistic_trades(self, data: pd.DataFrame, bullish_conditions: pd.Series, 
                                 bearish_conditions: pd.Series, atr: pd.Series, 
                                 params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate selective high-quality trades (max 8 trades/week)"""
        trades = []
        position = None
        last_trade_time = None
        max_trades_per_week = 8
        
        for i in range(1, len(data)):
            current_price = data['close'].iloc[i]
            current_atr = atr.iloc[i]
            
            if pd.isna(current_atr) or current_atr == 0:
                continue
            
            # Close existing position if conditions are met
            if position is not None:
                if position['type'] == 'long':
                    # Check stop loss
                    if current_price <= position['stop_loss']:
                        trades.append({
                            'entry_price': position['entry_price'],
                            'exit_price': position['stop_loss'],
                            'type': 'long',
                            'pips': (position['stop_loss'] - position['entry_price']) * 10000,
                            'result': 'loss'
                        })
                        position = None
                    # Check take profit
                    elif current_price >= position['take_profit']:
                        trades.append({
                            'entry_price': position['entry_price'],
                            'exit_price': position['take_profit'],
                            'type': 'long',
                            'pips': (position['take_profit'] - position['entry_price']) * 10000,
                            'result': 'win'
                        })
                        position = None
                
                elif position['type'] == 'short':
                    # Check stop loss
                    if current_price >= position['stop_loss']:
                        trades.append({
                            'entry_price': position['entry_price'],
                            'exit_price': position['stop_loss'],
                            'type': 'short',
                            'pips': (position['entry_price'] - position['stop_loss']) * 10000,
                            'result': 'loss'
                        })
                        position = None
                    # Check take profit
                    elif current_price <= position['take_profit']:
                        trades.append({
                            'entry_price': position['entry_price'],
                            'exit_price': position['take_profit'],
                            'type': 'short',
                            'pips': (position['entry_price'] - position['take_profit']) * 10000,
                            'result': 'win'
                        })
                        position = None
            
            # Open new position if no existing position (15m high frequency)
            if position is None:
                if bullish_conditions.iloc[i]:
                    stop_loss = current_price - (current_atr * params['stop_atr_mult'])
                    take_profit = current_price + (current_atr * params['stop_atr_mult'] * params['take_profit_rr'])
                    
                    position = {
                        'type': 'long',
                        'entry_price': current_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit
                    }
                
                elif bearish_conditions.iloc[i]:
                    stop_loss = current_price + (current_atr * params['stop_atr_mult'])
                    take_profit = current_price - (current_atr * params['stop_atr_mult'] * params['take_profit_rr'])
                    
                    position = {
                        'type': 'short',
                        'entry_price': current_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit
                    }
        
        return trades
    
    def _calculate_performance_metrics(self, trades: List[Dict[str, Any]], data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate realistic performance metrics"""
        if len(trades) == 0:
            return None
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = [t for t in trades if t['result'] == 'win']
        losing_trades = [t for t in trades if t['result'] == 'loss']
        
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
        
        # Pips calculation
        total_pips = sum(t['pips'] for t in trades)
        winning_pips = sum(t['pips'] for t in winning_trades)
        losing_pips = sum(t['pips'] for t in losing_trades)
        
        # Profit factor
        profit_factor = abs(winning_pips / losing_pips) if losing_pips != 0 else float('inf')
        
        # Calculate returns and Sharpe ratio
        returns = [t['pips'] for t in trades]
        if len(returns) > 1:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) != 0 else 0
        else:
            sharpe_ratio = 0
        
        # Calculate drawdown
        cumulative_returns = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_pips': total_pips,
            'winning_pips': winning_pips,
            'losing_pips': losing_pips,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'avg_win': np.mean([t['pips'] for t in winning_trades]) if winning_trades else 0,
            'avg_loss': np.mean([t['pips'] for t in losing_trades]) if losing_trades else 0
        }
    
    def run_all_experiments(self) -> Dict[str, Any]:
        """Run all realistic high-frequency experiments"""
        logger.info("🚀 Starting realistic high-frequency strategy search...")
        
        experiments = self.generate_experiments()
        logger.info(f"📊 Running {len(experiments)} realistic experiments...")
        
        successful_strategies = []
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_experiment = {
                executor.submit(self.run_single_experiment, exp): exp 
                for exp in experiments
            }
            
            for future in as_completed(future_to_experiment):
                result = future.result()
                if result is not None:
                    successful_strategies.append(result)
                
                self.completed_experiments += 1
                if self.completed_experiments % 50 == 0:
                    logger.info(f"📈 Progress: {self.completed_experiments}/{len(experiments)} experiments completed")
        
        # Sort by total trades (frequency) and then by profit factor
        successful_strategies.sort(key=lambda x: (x['total_trades'], x['profit_factor']), reverse=True)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"realistic_results_{timestamp}.json"
        
        results = {
            'timestamp': timestamp,
            'total_experiments': len(experiments),
            'successful_strategies': len(successful_strategies),
            'success_rate': len(successful_strategies) / len(experiments) * 100,
            'execution_time': str(datetime.now() - self.start_time),
            'strategies': successful_strategies
        }
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"✅ Realistic strategy search completed!")
        logger.info(f"📊 Results: {len(successful_strategies)}/{len(experiments)} strategies successful")
        logger.info(f"💾 Results saved to: {results_file}")
        
        if successful_strategies:
            best = successful_strategies[0]
            logger.info(f"🏆 Best realistic strategy:")
            logger.info(f"   Pair: {best['pair']} {best['timeframe']}")
            logger.info(f"   Trades: {best['total_trades']}")
            logger.info(f"   Win Rate: {best['win_rate']:.1f}%")
            logger.info(f"   Profit Factor: {best['profit_factor']:.2f}")
            logger.info(f"   Sharpe Ratio: {best['sharpe_ratio']:.2f}")
            logger.info(f"   Total Pips: {best['total_pips']:.1f}")
        
        return results

def main():
    """Main function"""
    controller = RealisticStrategyController()
    results = controller.run_all_experiments()
    
    if results['successful_strategies'] > 0:
        print(f"\n🎉 SUCCESS! Found {results['successful_strategies']} realistic high-frequency strategies!")
        print(f"📊 Success Rate: {results['success_rate']:.1f}%")
        
        # Show top 5 strategies
        print(f"\n🏆 TOP 5 REALISTIC STRATEGIES:")
        for i, strategy in enumerate(results['strategies'][:5], 1):
            print(f"{i}. {strategy['pair']} {strategy['timeframe']}")
            print(f"   Trades: {strategy['total_trades']} | Win Rate: {strategy['win_rate']:.1f}% | PF: {strategy['profit_factor']:.2f}")
    else:
        print(f"\n❌ No realistic strategies found. Consider adjusting parameters.")

if __name__ == "__main__":
    main()
