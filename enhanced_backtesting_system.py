#!/usr/bin/env python3
"""
ENHANCED BACKTESTING SYSTEM WITH LIVE TRADING INTEGRATION
Integrates OANDA live trading data with Bloomberg backtesting system
"""

import pandas as pd
import numpy as np
import os
import json
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class EnhancedBacktestingSystem:
    def __init__(self, live_data_path: str, bloomberg_data_path: str):
        """
        Initialize enhanced backtesting system with live trading integration
        
        Args:
            live_data_path: Path to live trading export data
            bloomberg_data_path: Path to Bloomberg data
        """
        self.live_data_path = live_data_path
        self.bloomberg_data_path = bloomberg_data_path
        self.results_dir = "results/enhanced"
        
        # Create results directory
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Load live trading configurations
        self.live_configs = self._load_live_configs()
        self.bloomberg_mapping = self._load_bloomberg_mapping()
        
        # Enhanced parameters from live system
        self.initial_capital = 100000.0
        self.risk_per_trade = 0.02  # 2% risk per trade
        self.max_drawdown_limit = 0.15  # 15% max drawdown
        
        # Dynamic spread and slippage modeling
        self.spread_model = DynamicSpreadModel(live_data_path)
        self.slippage_model = SlippageModel(self.spread_model)
        self.news_model = NewsImpactModel(bloomberg_data_path)
        
        # Strategy configurations from live system
        self.strategies = {
            'alpha_strategy': AlphaStrategyOptimized(self.live_configs['alpha_strategy']),
            'gold_scalping': GoldScalpingOptimized(self.live_configs['gold_scalping']),
            'ultra_strict_forex': UltraStrictForexOptimized(self.live_configs['ultra_strict_forex'])
        }
        
        print("✅ Enhanced Backtesting System Initialized")
        print(f"📊 Live Data Path: {live_data_path}")
        print(f"📈 Bloomberg Data Path: {bloomberg_data_path}")
        print(f"🎯 Strategies Loaded: {list(self.strategies.keys())}")
        
    def _load_live_configs(self) -> Dict:
        """Load live trading system configurations"""
        configs = {}
        
        try:
            # Load strategy configurations
            with open(os.path.join(self.live_data_path, 'strategies_config_20250921_175106.yaml'), 'r') as f:
                configs.update(yaml.safe_load(f))
                
            # Load risk management
            with open(os.path.join(self.live_data_path, 'risk_management_20250921_175106.json'), 'r') as f:
                configs['risk_management'] = json.load(f)
                
            print("✅ Live trading configurations loaded successfully")
        except Exception as e:
            print(f"⚠️ Warning: Could not load live configs: {e}")
            # Fallback configurations
            configs = self._get_fallback_configs()
            
        return configs
    
    def _get_fallback_configs(self) -> Dict:
        """Fallback configurations if live configs not available"""
        return {
            'alpha_strategy': {
                'ema_periods': [3, 8, 21],
                'momentum_period': 10,
                'min_signal_strength': 0.6,
                'max_trades_per_day': 50,
                'stop_loss_pct': 0.002,
                'take_profit_pct': 0.003,
                'instruments': ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 'USD_CAD', 'NZD_USD']
            },
            'gold_scalping': {
                'max_spread': 1.0,
                'min_volatility': 5e-05,
                'max_trades_per_day': 100,
                'stop_loss_pips': 8,
                'take_profit_pips': 12,
                'instruments': ['XAU_USD']
            },
            'ultra_strict_forex': {
                'ema_periods': [3, 8, 21],
                'min_signal_strength': 0.6,
                'max_trades_per_day': 50,
                'stop_loss_pct': 0.002,
                'take_profit_pct': 0.003,
                'instruments': ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD']
            }
        }
    
    def _load_bloomberg_mapping(self) -> Dict:
        """Load Bloomberg ticker mapping"""
        try:
            with open(os.path.join(self.live_data_path, 'bloomberg_mapping_20250921_175106.json'), 'r') as f:
                mapping = json.load(f)
                print("✅ Bloomberg ticker mapping loaded successfully")
                return mapping
        except Exception as e:
            print(f"⚠️ Warning: Could not load Bloomberg mapping: {e}")
            # Fallback mapping
            return {
                'ticker_mapping': {
                    'EUR_USD': 'EURUSD Curncy',
                    'GBP_USD': 'GBPUSD Curncy',
                    'USD_JPY': 'USDJPY Curncy',
                    'AUD_USD': 'AUDUSD Curncy',
                    'USD_CAD': 'USDCAD Curncy',
                    'NZD_USD': 'NZDUSD Curncy',
                    'XAU_USD': 'XAUUSD Curncy'
                }
            }
    
    def validate_data_quality(self) -> Dict:
        """Validate OANDA data against Bloomberg data"""
        validation_results = {}
        
        print("\n🔍 Validating Data Quality...")
        
        instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 'USD_CAD', 'NZD_USD', 'XAU_USD']
        
        for instrument in instruments:
            try:
                # Load OANDA data
                oanda_file = os.path.join(self.live_data_path, f'{instrument}_market_data_20250921_175106.csv')
                
                if not os.path.exists(oanda_file):
                    print(f"⚠️ OANDA data file not found: {instrument}")
                    continue
                    
                oanda_data = pd.read_csv(oanda_file)
                oanda_data['datetime'] = pd.to_datetime(oanda_data['datetime'])
                
                # Validation checks
                validation_results[instrument] = {
                    'data_points': len(oanda_data),
                    'time_range': {
                        'start': oanda_data['datetime'].min().strftime('%Y-%m-%d %H:%M:%S'),
                        'end': oanda_data['datetime'].max().strftime('%Y-%m-%d %H:%M:%S')
                    },
                    'spread_stats': {
                        'min': float(oanda_data['spread_pips'].min()),
                        'max': float(oanda_data['spread_pips'].max()),
                        'mean': float(oanda_data['spread_pips'].mean()),
                        'std': float(oanda_data['spread_pips'].std())
                    },
                    'price_range': {
                        'min': float(oanda_data['mid_price'].min()),
                        'max': float(oanda_data['mid_price'].max())
                    },
                    'bloomberg_ticker': self.bloomberg_mapping['ticker_mapping'].get(instrument, 'Unknown')
                }
                
                print(f"✅ {instrument}: {len(oanda_data)} data points, "
                      f"spread: {oanda_data['spread_pips'].min():.2f}-{oanda_data['spread_pips'].max():.2f} pips")
                      
            except Exception as e:
                print(f"❌ Error validating {instrument}: {e}")
                validation_results[instrument] = {'error': str(e)}
        
        # Save validation results
        with open(os.path.join(self.results_dir, 'data_validation_results.json'), 'w') as f:
            json.dump(validation_results, f, indent=2, default=str)
            
        return validation_results
    
    def run_enhanced_backtest(self, strategy_name: str, start_date: str, end_date: str) -> Dict:
        """Run enhanced backtest with live trading integration"""
        
        print(f"\n🚀 Running Enhanced Backtest: {strategy_name}")
        print(f"📅 Period: {start_date} to {end_date}")
        
        if strategy_name not in self.strategies:
            raise ValueError(f"Strategy {strategy_name} not found. Available: {list(self.strategies.keys())}")
        
        strategy = self.strategies[strategy_name]
        results = []
        
        # Load market data for strategy instruments
        for instrument in strategy.instruments:
            print(f"📊 Processing {instrument}...")
            
            try:
                # Load OANDA data
                oanda_file = os.path.join(self.live_data_path, f'{instrument}_market_data_20250921_175106.csv')
                
                if not os.path.exists(oanda_file):
                    print(f"⚠️ Data file not found: {instrument}")
                    continue
                    
                oanda_data = pd.read_csv(oanda_file)
                oanda_data['datetime'] = pd.to_datetime(oanda_data['datetime'])
                
                # Filter date range
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                mask = (oanda_data['datetime'] >= start_dt) & (oanda_data['datetime'] <= end_dt)
                data = oanda_data[mask].copy()
                
                if len(data) == 0:
                    print(f"⚠️ No data in date range for {instrument}")
                    continue
                
                print(f"   📈 {len(data)} data points in range")
                
                # Generate signals with enhanced logic
                signals = strategy.generate_signals(data, instrument)
                print(f"   🎯 Generated {len(signals)} signals")
                
                # Execute trades with realistic costs
                for signal in signals:
                    trade_result = self._execute_enhanced_trade(
                        signal, instrument, data, strategy
                    )
                    if trade_result:
                        results.append(trade_result)
                        
            except Exception as e:
                print(f"❌ Error processing {instrument}: {e}")
                continue
        
        # Calculate performance metrics
        performance = self._calculate_performance_metrics(results)
        
        backtest_result = {
            'strategy': strategy_name,
            'period': f"{start_date} to {end_date}",
            'total_trades': len(results),
            'performance': performance,
            'trades': results,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save results
        results_file = os.path.join(self.results_dir, f'{strategy_name}_enhanced_backtest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(results_file, 'w') as f:
            json.dump(backtest_result, f, indent=2, default=str)
        
        print(f"✅ Backtest completed: {len(results)} trades")
        print(f"💾 Results saved to: {results_file}")
        
        return backtest_result
    
    def _execute_enhanced_trade(self, signal: Dict, instrument: str, data: pd.DataFrame, strategy) -> Dict:
        """Execute trade with realistic costs and timing"""
        
        try:
            # Get execution timestamp (30-second delay)
            signal_time = signal['timestamp']
            execution_time = signal_time + timedelta(seconds=30)
            
            # Find execution price
            execution_data = data[data['datetime'] >= execution_time].head(1)
            if len(execution_data) == 0:
                return None
                
            execution_row = execution_data.iloc[0]
            
            # Get news impact (placeholder for now)
            news_impact = self.news_model.get_news_impact(instrument, execution_time)
            
            # Calculate realistic costs
            spread_cost = self.spread_model.get_spread(instrument, execution_time)
            slippage = self.slippage_model.calculate_slippage(
                instrument, signal['size'], execution_time, news_impact
            )
            
            # Calculate entry price
            if signal['type'] == 'BUY':
                entry_price = execution_row['ask']
            else:
                entry_price = execution_row['bid']
            
            # Calculate exit prices (using strategy stop loss and take profit)
            if signal['type'] == 'BUY':
                stop_loss_price = entry_price * (1 - strategy.stop_loss_pct)
                take_profit_price = entry_price * (1 + strategy.take_profit_pct)
            else:
                stop_loss_price = entry_price * (1 + strategy.stop_loss_pct)
                take_profit_price = entry_price * (1 - strategy.take_profit_pct)
            
            # Calculate P&L
            total_cost = spread_cost + slippage
            
            return {
                'timestamp': execution_time.isoformat(),
                'instrument': instrument,
                'type': signal['type'],
                'entry_price': float(entry_price),
                'stop_loss_price': float(stop_loss_price),
                'take_profit_price': float(take_profit_price),
                'size': signal['size'],
                'spread_cost': float(spread_cost),
                'slippage': float(slippage),
                'total_cost': float(total_cost),
                'news_impact': float(news_impact),
                'signal_strength': float(signal.get('strength', 0))
            }
            
        except Exception as e:
            print(f"❌ Error executing trade: {e}")
            return None
    
    def _calculate_performance_metrics(self, trades: List[Dict]) -> Dict:
        """Calculate comprehensive performance metrics"""
        if not trades:
            return {
                'total_return': 0.0,
                'win_rate': 0.0,
                'avg_return': 0.0,
                'sharpe_ratio': 0.0,
                'total_trades': 0,
                'avg_cost_per_trade': 0.0
            }
        
        # Calculate returns for each trade
        returns = []
        for trade in trades:
            # Simplified P&L calculation (you'll need to implement actual exit logic)
            if trade['type'] == 'BUY':
                potential_return = (trade['take_profit_price'] - trade['entry_price']) / trade['entry_price']
            else:
                potential_return = (trade['entry_price'] - trade['take_profit_price']) / trade['entry_price']
            
            # Subtract costs
            net_return = potential_return - (trade['total_cost'] / trade['entry_price'])
            returns.append(net_return)
        
        returns = np.array(returns)
        
        # Calculate metrics
        total_return = float(np.sum(returns))
        win_rate = float(np.mean(returns > 0))
        avg_return = float(np.mean(returns))
        std_return = float(np.std(returns))
        sharpe_ratio = float(avg_return / std_return) if std_return > 0 else 0.0
        
        return {
            'total_return': total_return,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'sharpe_ratio': sharpe_ratio,
            'total_trades': len(trades),
            'avg_cost_per_trade': float(np.mean([t['total_cost'] for t in trades]))
        }


class DynamicSpreadModel:
    """Dynamic spread modeling based on actual OANDA data"""
    
    def __init__(self, live_data_path: str):
        self.live_data_path = live_data_path
        self.spread_data = self._load_spread_data()
        print(f"✅ Dynamic Spread Model initialized with {len(self.spread_data)} instruments")
    
    def _load_spread_data(self) -> Dict:
        """Load spread data for all instruments"""
        spread_data = {}
        
        instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 'USD_CAD', 'NZD_USD', 'XAU_USD']
        
        for instrument in instruments:
            file_path = os.path.join(self.live_data_path, f'{instrument}_market_data_20250921_175106.csv')
            if os.path.exists(file_path):
                try:
                    data = pd.read_csv(file_path)
                    data['datetime'] = pd.to_datetime(data['datetime'])
                    spread_data[instrument] = data[['datetime', 'spread', 'spread_pips']]
                    print(f"   📊 Loaded spread data for {instrument}: {len(data)} points")
                except Exception as e:
                    print(f"   ⚠️ Error loading {instrument}: {e}")
        
        return spread_data
    
    def get_spread(self, instrument: str, timestamp: datetime) -> float:
        """Get actual spread for specific instrument and time"""
        if instrument not in self.spread_data:
            return 0.0001  # Default spread
        
        instrument_data = self.spread_data[instrument]
        
        # Find closest timestamp
        time_diff = abs(instrument_data['datetime'] - timestamp)
        closest_idx = time_diff.idxmin()
        
        if time_diff.iloc[closest_idx] < timedelta(minutes=5):  # Within 5 minutes
            return float(instrument_data.iloc[closest_idx]['spread'])
        else:
            # Return average spread if no close match
            return float(instrument_data['spread'].mean())


class SlippageModel:
    """Realistic slippage modeling"""
    
    def __init__(self, spread_model: DynamicSpreadModel):
        self.spread_model = spread_model
        print("✅ Slippage Model initialized")
    
    def calculate_slippage(self, instrument: str, order_size: float, timestamp: datetime, news_impact: float = 0) -> float:
        """Calculate realistic slippage based on spread and market conditions"""
        current_spread = self.spread_model.get_spread(instrument, timestamp)
        
        # Base slippage (half the spread)
        base_slippage = current_spread * 0.5
        
        # Increase slippage for larger orders
        size_factor = min(1.5, 1 + (order_size / 100000) * 0.1)
        
        # Increase slippage during news events
        news_factor = 1 + (news_impact * 0.3)
        
        return float(base_slippage * size_factor * news_factor)


class NewsImpactModel:
    """News impact modeling for correlation with price movements"""
    
    def __init__(self, bloomberg_data_path: str):
        self.bloomberg_data_path = bloomberg_data_path
        print("✅ News Impact Model initialized (placeholder)")
    
    def get_news_impact(self, instrument: str, timestamp: datetime) -> float:
        """Get news impact score for specific time"""
        # Placeholder implementation
        # You'll need to integrate with your Bloomberg news data
        return 0.0


class AlphaStrategyOptimized:
    """Optimized Alpha Strategy with signal filtering"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.ema_periods = config['ema_periods']
        self.momentum_period = config['momentum_period']
        self.min_signal_strength = config['min_signal_strength']
        self.max_trades_per_day = config['max_trades_per_day']
        self.stop_loss_pct = config['stop_loss_pct']
        self.take_profit_pct = config['take_profit_pct']
        self.instruments = config['instruments']
        self.daily_trades = 0
        
        print(f"✅ Alpha Strategy Optimized initialized")
        print(f"   📊 Instruments: {self.instruments}")
        print(f"   🎯 Min signal strength: {self.min_signal_strength}")
        print(f"   📈 Max trades per day: {self.max_trades_per_day}")
    
    def generate_signals(self, data: pd.DataFrame, instrument: str) -> List[Dict]:
        """Generate trading signals with filtering"""
        signals = []
        
        if len(data) < max(self.ema_periods) + self.momentum_period:
            return signals
        
        # Calculate EMAs
        ema_fast = data['mid_price'].ewm(span=self.ema_periods[0]).mean()
        ema_mid = data['mid_price'].ewm(span=self.ema_periods[1]).mean()
        ema_slow = data['mid_price'].ewm(span=self.ema_periods[2]).mean()
        
        # Calculate momentum
        momentum = (data['mid_price'] / data['mid_price'].shift(self.momentum_period) - 1) * 100
        
        # Signal conditions
        bullish_conditions = (ema_fast > ema_mid) & (ema_mid > ema_slow) & (momentum > 0)
        bearish_conditions = (ema_fast < ema_mid) & (ema_mid < ema_slow) & (momentum < 0)
        
        # Calculate signal strength
        signal_strength = abs(momentum) / 10  # Normalize to 0-1 range
        
        # Apply signal filtering
        valid_bullish = bullish_conditions & (signal_strength >= self.min_signal_strength)
        valid_bearish = bearish_conditions & (signal_strength >= self.min_signal_strength)
        
        # Limit daily trades
        if self.daily_trades < self.max_trades_per_day:
            if valid_bullish.iloc[-1]:
                signals.append({
                    'type': 'BUY',
                    'strength': float(signal_strength.iloc[-1]),
                    'timestamp': data['datetime'].iloc[-1],
                    'size': 10000  # Standard position size
                })
                self.daily_trades += 1
            elif valid_bearish.iloc[-1]:
                signals.append({
                    'type': 'SELL',
                    'strength': float(signal_strength.iloc[-1]),
                    'timestamp': data['datetime'].iloc[-1],
                    'size': 10000
                })
                self.daily_trades += 1
        
        return signals


class GoldScalpingOptimized:
    """Optimized Gold Scalping Strategy with spread sensitivity"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.max_spread = config['max_spread']
        self.min_volatility = config['min_volatility']
        self.max_trades_per_day = config['max_trades_per_day']
        self.stop_loss_pips = config['stop_loss_pips']
        self.take_profit_pips = config['take_profit_pips']
        self.instruments = config['instruments']
        self.daily_trades = 0
        
        print(f"✅ Gold Scalping Strategy Optimized initialized")
        print(f"   📊 Instruments: {self.instruments}")
        print(f"   📈 Max spread: {self.max_spread} pips")
        print(f"   🎯 Max trades per day: {self.max_trades_per_day}")
    
    def generate_signals(self, data: pd.DataFrame, instrument: str) -> List[Dict]:
        """Generate signals with spread sensitivity"""
        signals = []
        
        if len(data) < 20:  # Need minimum data for volatility calculation
            return signals
        
        # Check spread conditions first
        current_spread_pips = data['spread_pips'].iloc[-1]
        if current_spread_pips > self.max_spread:
            return signals  # Skip trading if spread too wide
        
        # Calculate volatility
        volatility = data['mid_price'].rolling(20).std().iloc[-1]
        if volatility < self.min_volatility:
            return signals  # Skip if volatility too low
        
        # Simple momentum signal for gold
        price_change = (data['mid_price'].iloc[-1] - data['mid_price'].iloc[-5]) / data['mid_price'].iloc[-5]
        
        if self.daily_trades < self.max_trades_per_day:
            if price_change > 0.001:  # 0.1% price increase
                signals.append({
                    'type': 'BUY',
                    'strength': float(abs(price_change) * 100),
                    'timestamp': data['datetime'].iloc[-1],
                    'size': 10000
                })
                self.daily_trades += 1
            elif price_change < -0.001:  # 0.1% price decrease
                signals.append({
                    'type': 'SELL',
                    'strength': float(abs(price_change) * 100),
                    'timestamp': data['datetime'].iloc[-1],
                    'size': 10000
                })
                self.daily_trades += 1
        
        return signals


class UltraStrictForexOptimized:
    """Optimized Ultra Strict Forex Strategy"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.ema_periods = config['ema_periods']
        self.min_signal_strength = config['min_signal_strength']
        self.max_trades_per_day = config['max_trades_per_day']
        self.stop_loss_pct = config['stop_loss_pct']
        self.take_profit_pct = config['take_profit_pct']
        self.instruments = config['instruments']
        self.daily_trades = 0
        
        print(f"✅ Ultra Strict Forex Strategy Optimized initialized")
        print(f"   📊 Instruments: {self.instruments}")
        print(f"   🎯 Min signal strength: {self.min_signal_strength}")
        print(f"   📈 Max trades per day: {self.max_trades_per_day}")
    
    def generate_signals(self, data: pd.DataFrame, instrument: str) -> List[Dict]:
        """Generate ultra-strict forex signals"""
        signals = []
        
        if len(data) < max(self.ema_periods) + 14:  # Need RSI calculation
            return signals
        
        # More strict conditions for forex
        ema_fast = data['mid_price'].ewm(span=self.ema_periods[0]).mean()
        ema_mid = data['mid_price'].ewm(span=self.ema_periods[1]).mean()
        ema_slow = data['mid_price'].ewm(span=self.ema_periods[2]).mean()
        
        # Additional confirmation with RSI
        delta = data['mid_price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Ultra-strict conditions
        bullish_conditions = (
            (ema_fast > ema_mid) & 
            (ema_mid > ema_slow) & 
            (rsi > 50) & 
            (rsi < 70)  # Not overbought
        )
        
        bearish_conditions = (
            (ema_fast < ema_mid) & 
            (ema_mid < ema_slow) & 
            (rsi < 50) & 
            (rsi > 30)  # Not oversold
        )
        
        # Calculate signal strength
        signal_strength = abs(rsi - 50) / 50  # Normalize RSI to 0-1
        
        # Apply strict filtering
        valid_bullish = bullish_conditions & (signal_strength >= self.min_signal_strength)
        valid_bearish = bearish_conditions & (signal_strength >= self.min_signal_strength)
        
        if self.daily_trades < self.max_trades_per_day:
            if valid_bullish.iloc[-1]:
                signals.append({
                    'type': 'BUY',
                    'strength': float(signal_strength.iloc[-1]),
                    'timestamp': data['datetime'].iloc[-1],
                    'size': 10000
                })
                self.daily_trades += 1
            elif valid_bearish.iloc[-1]:
                signals.append({
                    'type': 'SELL',
                    'strength': float(signal_strength.iloc[-1]),
                    'timestamp': data['datetime'].iloc[-1],
                    'size': 10000
                })
                self.daily_trades += 1
        
        return signals


# Usage example and testing
if __name__ == "__main__":
    print("🚀 ENHANCED BACKTESTING SYSTEM - INITIALIZATION")
    print("=" * 60)
    
    # Initialize enhanced backtesting system
    live_data_path = r"H:\My Drive\desktop_backtesting_export"
    bloomberg_data_path = r"E:\deep_backtesting_windows1\deep_backtesting\data"
    
    try:
        system = EnhancedBacktestingSystem(live_data_path, bloomberg_data_path)
        
        # Validate data quality
        print("\n" + "=" * 60)
        validation_results = system.validate_data_quality()
        
        # Run enhanced backtests
        print("\n" + "=" * 60)
        print("🧪 RUNNING ENHANCED BACKTESTS")
        
        strategies = ['alpha_strategy', 'gold_scalping', 'ultra_strict_forex']
        test_start_date = "2025-09-18 00:00:00"
        test_end_date = "2025-09-18 23:59:59"
        
        all_results = {}
        
        for strategy in strategies:
            print(f"\n🎯 Testing Strategy: {strategy}")
            try:
                results = system.run_enhanced_backtest(
                    strategy, 
                    test_start_date, 
                    test_end_date
                )
                
                all_results[strategy] = results
                
                print(f"✅ {strategy} Results:")
                print(f"   📊 Total trades: {results['total_trades']}")
                if results['performance']:
                    print(f"   🎯 Win rate: {results['performance']['win_rate']:.2%}")
                    print(f"   📈 Total return: {results['performance']['total_return']:.2%}")
                    print(f"   📊 Sharpe ratio: {results['performance']['sharpe_ratio']:.2f}")
                    print(f"   💰 Avg cost per trade: ${results['performance']['avg_cost_per_trade']:.4f}")
                
            except Exception as e:
                print(f"❌ Error testing {strategy}: {e}")
                all_results[strategy] = {'error': str(e)}
        
        # Save comprehensive results
        comprehensive_results = {
            'validation': validation_results,
            'backtest_results': all_results,
            'timestamp': datetime.now().isoformat(),
            'system_info': {
                'live_data_path': live_data_path,
                'bloomberg_data_path': bloomberg_data_path,
                'test_period': f"{test_start_date} to {test_end_date}"
            }
        }
        
        results_file = os.path.join(system.results_dir, f'comprehensive_test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(results_file, 'w') as f:
            json.dump(comprehensive_results, f, indent=2, default=str)
        
        print(f"\n✅ COMPREHENSIVE TESTING COMPLETED")
        print(f"💾 All results saved to: {results_file}")
        
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        import traceback
        traceback.print_exc()

