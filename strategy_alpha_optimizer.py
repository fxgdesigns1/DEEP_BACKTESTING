#!/usr/bin/env python3
"""
STRATEGY ALPHA OPTIMIZER
Fine-tune the winning AUD_USD 15m strategy with multiple variations and tweaks
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

class StrategyAlphaOptimizer:
    """Strategy Alpha fine-tuning optimizer"""
    
    def __init__(self):
        """Initialize the Strategy Alpha optimizer"""
        self.max_workers = min(16, mp.cpu_count())
        self.results_dir = Path("results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Base Strategy Alpha parameters (our winning strategy)
        self.base_params = {
            'pair': 'AUD_USD',
            'timeframe': '15m',
            'ema_fast': 5,
            'ema_slow': 13,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'stop_atr_mult': 1.0,
            'take_profit_rr': 1.5
        }
        
    def generate_alpha_variations(self) -> List[Dict[str, Any]]:
        """Generate multiple Strategy Alpha variations for fine-tuning"""
        experiments = []
        
        # FINE-TUNING VARIATIONS AROUND WINNING STRATEGY
        
        # 1. EMA Fine-tuning (around 5, 13)
        ema_fast_variations = [3, 4, 5, 6, 7, 8]  # Around winning 5
        ema_slow_variations = [11, 12, 13, 14, 15, 16, 17]  # Around winning 13
        
        # 2. RSI Fine-tuning (around 30, 70)
        rsi_oversold_variations = [25, 28, 30, 32, 35]  # Around winning 30
        rsi_overbought_variations = [65, 68, 70, 72, 75]  # Around winning 70
        
        # 3. Risk Management Fine-tuning
        stop_atr_variations = [0.8, 0.9, 1.0, 1.1, 1.2]  # Around winning 1.0
        take_profit_variations = [1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8]  # Around winning 1.5
        
        # 4. Advanced Variations
        advanced_variations = [
            # Trend confirmation
            {'trend_confirmation': True, 'trend_ema': 21},
            {'trend_confirmation': True, 'trend_ema': 34},
            
            # Momentum filters
            {'momentum_filter': True, 'momentum_period': 10},
            {'momentum_filter': True, 'momentum_period': 14},
            
            # Volatility filters
            {'volatility_filter': True, 'vol_threshold': 0.5},
            {'volatility_filter': True, 'vol_threshold': 1.0},
            
            # Time-based filters
            {'time_filter': True, 'avoid_news_hours': True},
            {'session_filter': True, 'prefer_london_session': True},
        ]
        
        experiment_id = 0
        
        # Generate base variations
        for ema_fast in ema_fast_variations:
            for ema_slow in ema_slow_variations:
                if ema_fast >= ema_slow:  # Skip invalid combinations
                    continue
                    
                for rsi_oversold in rsi_oversold_variations:
                    for rsi_overbought in rsi_overbought_variations:
                        if rsi_oversold >= rsi_overbought:  # Skip invalid combinations
                            continue
                            
                        for stop_atr in stop_atr_variations:
                            for take_profit in take_profit_variations:
                                experiment_id += 1
                                
                                experiments.append({
                                    'experiment_id': experiment_id,
                                    'variation_type': 'base_fine_tune',
                                    'params': {
                                        'pair': 'AUD_USD',
                                        'timeframe': '15m',
                                        'ema_fast': ema_fast,
                                        'ema_slow': ema_slow,
                                        'rsi_oversold': rsi_oversold,
                                        'rsi_overbought': rsi_overbought,
                                        'stop_atr_mult': stop_atr,
                                        'take_profit_rr': take_profit
                                    }
                                })
        
        # Generate advanced variations
        for adv_var in advanced_variations:
            experiment_id += 1
            
            # Start with base winning parameters
            params = self.base_params.copy()
            params.update(adv_var)
            
            experiments.append({
                'experiment_id': experiment_id,
                'variation_type': 'advanced',
                'params': params
            })
        
        # Generate hybrid variations (combining multiple enhancements)
        hybrid_variations = [
            # Trend + Momentum
            {'trend_confirmation': True, 'trend_ema': 21, 'momentum_filter': True, 'momentum_period': 14},
            # Trend + Volatility
            {'trend_confirmation': True, 'trend_ema': 34, 'volatility_filter': True, 'vol_threshold': 0.8},
            # Momentum + Time
            {'momentum_filter': True, 'momentum_period': 10, 'time_filter': True, 'avoid_news_hours': True},
            # All filters
            {'trend_confirmation': True, 'trend_ema': 21, 'momentum_filter': True, 'momentum_period': 14, 
             'volatility_filter': True, 'vol_threshold': 0.8, 'time_filter': True, 'avoid_news_hours': True}
        ]
        
        for hybrid_var in hybrid_variations:
            experiment_id += 1
            
            params = self.base_params.copy()
            params.update(hybrid_var)
            
            experiments.append({
                'experiment_id': experiment_id,
                'variation_type': 'hybrid',
                'params': params
            })
        
        logger.info(f"🎯 Generated {len(experiments)} Strategy Alpha variations for optimization")
        return experiments
    
    def run_alpha_optimization(self):
        """Run comprehensive Strategy Alpha optimization"""
        logger.info("🚀 Starting Strategy Alpha optimization...")
        
        experiments = self.generate_alpha_variations()
        successful_strategies = []
        
        start_time = datetime.now()
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all experiments
            future_to_experiment = {
                executor.submit(self._run_alpha_experiment, exp): exp 
                for exp in experiments
            }
            
            completed = 0
            for future in as_completed(future_to_experiment):
                experiment = future_to_experiment[future]
                completed += 1
                
                try:
                    result = future.result()
                    if result:
                        successful_strategies.append(result)
                        logger.info(f"✅ Alpha Success: {result['variation_type']} - Trades: {result['total_trades']}, Win Rate: {result['win_rate']:.1f}%, PF: {result['profit_factor']:.2f}, Sharpe: {result['sharpe_ratio']:.2f}")
                    
                    if completed % 100 == 0:
                        logger.info(f"📈 Progress: {completed}/{len(experiments)} experiments completed")
                        
                except Exception as e:
                    logger.error(f"❌ Error in experiment {experiment['experiment_id']}: {e}")
        
        end_time = datetime.now()
        execution_time = end_time - start_time
        
        # Sort by Sharpe ratio (best risk-adjusted returns)
        successful_strategies.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
        
        # Save results
        results = {
            'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'strategy_name': 'Strategy Alpha Optimization',
            'base_strategy': self.base_params,
            'total_experiments': len(experiments),
            'successful_strategies': len(successful_strategies),
            'success_rate': len(successful_strategies) / len(experiments) * 100,
            'execution_time': str(execution_time),
            'strategies': successful_strategies[:50]  # Top 50
        }
        
        results_file = self.results_dir / f"strategy_alpha_optimization_{results['timestamp']}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"🎉 Strategy Alpha optimization completed!")
        logger.info(f"📊 Results: {len(successful_strategies)}/{len(experiments)} strategies successful")
        logger.info(f"💾 Results saved to: {results_file}")
        
        if successful_strategies:
            best = successful_strategies[0]
            logger.info(f"🏆 Best Strategy Alpha variation:")
            logger.info(f"   Variation Type: {best['variation_type']}")
            logger.info(f"   Trades: {best['total_trades']}")
            logger.info(f"   Win Rate: {best['win_rate']:.1f}%")
            logger.info(f"   Profit Factor: {best['profit_factor']:.2f}")
            logger.info(f"   Sharpe Ratio: {best['sharpe_ratio']:.2f}")
            logger.info(f"   Total Pips: {best['total_pips']:.1f}")
            logger.info(f"   Max Drawdown: {best['max_drawdown']:.2f}")
        
        return results
    
    def _run_alpha_experiment(self, experiment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run a single Strategy Alpha experiment"""
        try:
            # Load data
            data = self._load_data(experiment['params']['pair'], experiment['params']['timeframe'])
            if data is None or len(data) < 100:
                return None
            
            # Run strategy
            results = self._run_alpha_strategy(data, experiment['params'])
            if results is None:
                return None
            
            # Check if strategy meets criteria (relaxed for optimization)
            if (results['total_trades'] >= 20 and
                results['sharpe_ratio'] > 0.2 and
                results['profit_factor'] > 1.1 and
                results['win_rate'] > 35 and
                results['max_drawdown'] > -0.30):
                
                results.update({
                    'pair': experiment['params']['pair'],
                    'timeframe': experiment['params']['timeframe'],
                    'experiment_id': experiment['experiment_id'],
                    'variation_type': experiment['variation_type'],
                    'params': experiment['params']
                })
                
                return results
            
            return None
            
        except Exception as e:
            logger.error(f"Error in experiment {experiment['experiment_id']}: {e}")
            return None
    
    def _load_data(self, pair: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Load data for the specified pair and timeframe"""
        try:
            data_path = f"data/MASTER_DATASET/{timeframe}/{pair}_{timeframe}.csv"
            if not os.path.exists(data_path):
                return None
            
            data = pd.read_csv(data_path)
            if len(data) < 100:
                return None
            
            # Ensure required columns exist
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in data.columns for col in required_columns):
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"Error loading data for {pair} {timeframe}: {e}")
            return None
    
    def _run_alpha_strategy(self, data: pd.DataFrame, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run Strategy Alpha with given parameters"""
        try:
            # Calculate indicators
            ema_fast = data['close'].ewm(span=params['ema_fast']).mean()
            ema_slow = data['close'].ewm(span=params['ema_slow']).mean()
            rsi = self._calculate_rsi(data['close'], 14)
            atr = self._calculate_atr(data, 14)
            
            # Generate signals with enhancements
            bullish_conditions, bearish_conditions = self._generate_enhanced_signals(
                data, ema_fast, ema_slow, rsi, params
            )
            
            # Simulate trades
            trades = self._simulate_alpha_trades(data, bullish_conditions, bearish_conditions, atr, params)
            
            if len(trades) < 5:
                return None
            
            # Calculate performance metrics
            results = self._calculate_performance_metrics(trades, data)
            return results
            
        except Exception as e:
            logger.error(f"Error running strategy: {e}")
            return None
    
    def _generate_enhanced_signals(self, data: pd.DataFrame, ema_fast: pd.Series, 
                                 ema_slow: pd.Series, rsi: pd.Series, 
                                 params: Dict[str, Any]) -> tuple:
        """Generate enhanced signals with optional filters"""
        
        # Base signals
        bullish_base = (
            (ema_fast > ema_slow) & 
            (ema_fast.shift(1) <= ema_slow.shift(1)) &  # EMA crossover
            (rsi < params['rsi_oversold']) &  # RSI oversold
            (data['close'] > ema_slow)  # Price above slow EMA
        )
        
        bearish_base = (
            (ema_fast < ema_slow) & 
            (ema_fast.shift(1) >= ema_slow.shift(1)) &  # EMA crossover
            (rsi > params['rsi_overbought']) &  # RSI overbought
            (data['close'] < ema_slow)  # Price below slow EMA
        )
        
        # Apply enhancements
        bullish_conditions = bullish_base.copy()
        bearish_conditions = bearish_base.copy()
        
        # Trend confirmation
        if params.get('trend_confirmation', False):
            trend_ema = data['close'].ewm(span=params.get('trend_ema', 21)).mean()
            bullish_conditions &= (data['close'] > trend_ema)
            bearish_conditions &= (data['close'] < trend_ema)
        
        # Momentum filter
        if params.get('momentum_filter', False):
            momentum_period = params.get('momentum_period', 14)
            momentum = data['close'].pct_change(momentum_period)
            bullish_conditions &= (momentum > 0)
            bearish_conditions &= (momentum < 0)
        
        # Volatility filter
        if params.get('volatility_filter', False):
            vol_threshold = params.get('vol_threshold', 0.8)
            volatility = atr / data['close']
            bullish_conditions &= (volatility > vol_threshold)
            bearish_conditions &= (volatility > vol_threshold)
        
        # Time filter (avoid news hours)
        if params.get('time_filter', False):
            # Simple time filter - avoid first and last hour of trading day
            hour = pd.to_datetime(data.index).hour if hasattr(data.index, 'hour') else 0
            time_mask = (hour >= 1) & (hour <= 22)  # Avoid 0-1 and 22-24
            bullish_conditions &= time_mask
            bearish_conditions &= time_mask
        
        return bullish_conditions, bearish_conditions
    
    def _simulate_alpha_trades(self, data: pd.DataFrame, bullish_conditions: pd.Series, 
                             bearish_conditions: pd.Series, atr: pd.Series, 
                             params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate Strategy Alpha trades"""
        trades = []
        position = None
        
        for i in range(1, len(data)):
            current_price = data['close'].iloc[i]
            current_atr = atr.iloc[i]
            
            if current_atr <= 0:
                continue
            
            # Close existing position
            if position is not None:
                if position['type'] == 'long':
                    if current_price <= position['stop_loss']:
                        trades.append({
                            'type': 'long',
                            'entry_price': position['entry_price'],
                            'exit_price': position['stop_loss'],
                            'pips': (position['stop_loss'] - position['entry_price']) * 10000,
                            'result': 'loss'
                        })
                        position = None
                    elif current_price >= position['take_profit']:
                        trades.append({
                            'type': 'long',
                            'entry_price': position['entry_price'],
                            'exit_price': position['take_profit'],
                            'pips': (position['take_profit'] - position['entry_price']) * 10000,
                            'result': 'win'
                        })
                        position = None
                
                elif position['type'] == 'short':
                    if current_price >= position['stop_loss']:
                        trades.append({
                            'type': 'short',
                            'entry_price': position['entry_price'],
                            'exit_price': position['stop_loss'],
                            'pips': (position['entry_price'] - position['stop_loss']) * 10000,
                            'result': 'loss'
                        })
                        position = None
                    elif current_price <= position['take_profit']:
                        trades.append({
                            'type': 'short',
                            'entry_price': position['entry_price'],
                            'exit_price': position['take_profit'],
                            'pips': (position['entry_price'] - position['take_profit']) * 10000,
                            'result': 'win'
                        })
                        position = None
            
            # Open new position
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
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR indicator"""
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(period).mean()
        return atr
    
    def _calculate_performance_metrics(self, trades: List[Dict[str, Any]], data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate performance metrics"""
        if not trades:
            return None
        
        total_trades = len(trades)
        winning_trades = [t for t in trades if t['result'] == 'win']
        losing_trades = [t for t in trades if t['result'] == 'loss']
        
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
        
        total_pips = sum(t['pips'] for t in trades)
        winning_pips = sum(t['pips'] for t in winning_trades)
        losing_pips = sum(t['pips'] for t in losing_trades)
        
        profit_factor = abs(winning_pips / losing_pips) if losing_pips != 0 else float('inf')
        
        # Calculate Sharpe ratio (simplified)
        returns = [t['pips'] for t in trades]
        if len(returns) > 1:
            sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) != 0 else 0
        else:
            sharpe_ratio = 0
        
        # Calculate max drawdown
        cumulative_pips = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative_pips)
        drawdown = (cumulative_pips - running_max) / 10000  # Convert to percentage
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_pips': total_pips,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown
        }

def main():
    """Main function to run Strategy Alpha optimization"""
    optimizer = StrategyAlphaOptimizer()
    results = optimizer.run_alpha_optimization()
    
    print(f"\n🎉 Strategy Alpha optimization completed!")
    print(f"📊 Found {results['successful_strategies']} successful variations")
    print(f"🏆 Best variation saved to results file")

if __name__ == "__main__":
    main()
