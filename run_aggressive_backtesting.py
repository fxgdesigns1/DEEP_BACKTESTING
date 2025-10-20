#!/usr/bin/env python3
"""
AGGRESSIVE BACKTESTING EXECUTION
Run backtesting with relaxed parameters to generate more signals for analysis
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class AggressiveBacktestingSystem:
    """Aggressive backtesting system with relaxed parameters for signal generation"""
    
    def __init__(self, live_data_path: str):
        self.live_data_path = live_data_path
        self.results_dir = "results/aggressive"
        os.makedirs(self.results_dir, exist_ok=True)
        
        print("🚀 Aggressive Backtesting System Initialized")
        print("   📊 Relaxed parameters for maximum signal generation")
    
    def run_aggressive_backtest(self, strategy_name: str, start_date: str, end_date: str) -> dict:
        """Run aggressive backtest with relaxed parameters"""
        
        print(f"\n🎯 Running Aggressive Backtest: {strategy_name}")
        print(f"📅 Period: {start_date} to {end_date}")
        
        # Load and process data
        instruments = self._get_strategy_instruments(strategy_name)
        all_trades = []
        
        for instrument in instruments:
            print(f"📊 Processing {instrument}...")
            
            # Load data
            file_path = os.path.join(self.live_data_path, f'{instrument}_market_data_20250921_175106.csv')
            if not os.path.exists(file_path):
                print(f"   ⚠️ Data file not found: {instrument}")
                continue
            
            data = pd.read_csv(file_path)
            data['datetime'] = pd.to_datetime(data['datetime'])
            
            # Filter date range
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            mask = (data['datetime'] >= start_dt) & (data['datetime'] <= end_dt)
            filtered_data = data[mask].copy()
            
            if len(filtered_data) == 0:
                print(f"   ⚠️ No data in range for {instrument}")
                continue
            
            print(f"   📈 {len(filtered_data)} data points in range")
            
            # Generate aggressive signals
            signals = self._generate_aggressive_signals(strategy_name, filtered_data, instrument)
            print(f"   🎯 Generated {len(signals)} signals")
            
            # Execute trades
            for signal in signals:
                trade = self._execute_aggressive_trade(signal, instrument, filtered_data)
                if trade:
                    all_trades.append(trade)
        
        # Calculate performance
        performance = self._calculate_performance(all_trades)
        
        result = {
            'strategy': strategy_name,
            'period': f"{start_date} to {end_date}",
            'total_trades': len(all_trades),
            'performance': performance,
            'trades': all_trades,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(self.results_dir, f'{strategy_name}_aggressive_{timestamp}.json')
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"✅ Aggressive backtest completed: {len(all_trades)} trades")
        print(f"💾 Results saved to: {results_file}")
        
        return result
    
    def _get_strategy_instruments(self, strategy_name: str) -> list:
        """Get instruments for each strategy"""
        instrument_map = {
            'alpha_strategy': ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 'USD_CAD', 'NZD_USD'],
            'gold_scalping': ['XAU_USD'],
            'ultra_strict_forex': ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD']
        }
        return instrument_map.get(strategy_name, [])
    
    def _generate_aggressive_signals(self, strategy_name: str, data: pd.DataFrame, instrument: str) -> list:
        """Generate aggressive signals with relaxed parameters"""
        
        signals = []
        
        if len(data) < 10:  # Need minimum data
            return signals
        
        if strategy_name == 'alpha_strategy':
            signals = self._alpha_aggressive_signals(data, instrument)
        elif strategy_name == 'gold_scalping':
            signals = self._gold_aggressive_signals(data, instrument)
        elif strategy_name == 'ultra_strict_forex':
            signals = self._forex_aggressive_signals(data, instrument)
        
        return signals
    
    def _alpha_aggressive_signals(self, data: pd.DataFrame, instrument: str) -> list:
        """Generate aggressive alpha strategy signals"""
        signals = []
        
        # Relaxed parameters
        ema_fast_period = 3
        ema_slow_period = 8
        min_signal_strength = 0.3  # Much more relaxed
        max_trades = 200  # Much higher limit
        
        if len(data) < ema_slow_period + 5:
            return signals
        
        # Calculate EMAs
        ema_fast = data['mid_price'].ewm(span=ema_fast_period).mean()
        ema_slow = data['mid_price'].ewm(span=ema_slow_period).mean()
        
        # Calculate momentum
        momentum = (data['mid_price'] / data['mid_price'].shift(5) - 1) * 100
        
        # More aggressive signal conditions
        bullish_conditions = (ema_fast > ema_slow) & (momentum > 0.1)  # Very small momentum threshold
        bearish_conditions = (ema_fast < ema_slow) & (momentum < -0.1)
        
        # Calculate signal strength
        signal_strength = abs(momentum) / 5  # Normalize
        
        # Apply relaxed filtering
        valid_bullish = bullish_conditions & (signal_strength >= min_signal_strength)
        valid_bearish = bearish_conditions & (signal_strength >= min_signal_strength)
        
        # Generate signals (much more aggressive)
        for i in range(len(data)):
            if len(signals) >= max_trades:
                break
                
            if valid_bullish.iloc[i]:
                signals.append({
                    'type': 'BUY',
                    'strength': float(signal_strength.iloc[i]),
                    'timestamp': data['datetime'].iloc[i],
                    'size': 10000
                })
            elif valid_bearish.iloc[i]:
                signals.append({
                    'type': 'SELL',
                    'strength': float(signal_strength.iloc[i]),
                    'timestamp': data['datetime'].iloc[i],
                    'size': 10000
                })
        
        return signals
    
    def _gold_aggressive_signals(self, data: pd.DataFrame, instrument: str) -> list:
        """Generate aggressive gold scalping signals"""
        signals = []
        
        # Very relaxed parameters
        max_spread = 20.0  # Much higher spread tolerance
        min_volatility = 1e-06  # Much lower volatility requirement
        max_trades = 500  # Much higher limit
        
        if len(data) < 5:
            return signals
        
        # Check spread conditions (very relaxed)
        current_spread_pips = data['spread_pips'].iloc[-1]
        if current_spread_pips > max_spread:
            return signals
        
        # Calculate volatility (very relaxed)
        volatility = data['mid_price'].rolling(5).std().iloc[-1]
        if volatility < min_volatility:
            return signals
        
        # Very aggressive momentum signals
        for i in range(1, len(data)):
            if len(signals) >= max_trades:
                break
                
            price_change = (data['mid_price'].iloc[i] - data['mid_price'].iloc[i-1]) / data['mid_price'].iloc[i-1]
            
            if price_change > 0.0001:  # Very small price change threshold
                signals.append({
                    'type': 'BUY',
                    'strength': float(abs(price_change) * 1000),
                    'timestamp': data['datetime'].iloc[i],
                    'size': 10000
                })
            elif price_change < -0.0001:
                signals.append({
                    'type': 'SELL',
                    'strength': float(abs(price_change) * 1000),
                    'timestamp': data['datetime'].iloc[i],
                    'size': 10000
                })
        
        return signals
    
    def _forex_aggressive_signals(self, data: pd.DataFrame, instrument: str) -> list:
        """Generate aggressive forex signals"""
        signals = []
        
        # Relaxed parameters
        ema_fast_period = 3
        ema_slow_period = 8
        min_signal_strength = 0.2  # Very relaxed
        max_trades = 300  # Higher limit
        
        if len(data) < ema_slow_period + 10:
            return signals
        
        # Calculate EMAs
        ema_fast = data['mid_price'].ewm(span=ema_fast_period).mean()
        ema_slow = data['mid_price'].ewm(span=ema_slow_period).mean()
        
        # Calculate RSI (simplified)
        delta = data['mid_price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=5).mean()  # Shorter window
        loss = (-delta.where(delta < 0, 0)).rolling(window=5).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Very relaxed conditions
        bullish_conditions = (ema_fast > ema_slow) & (rsi > 30)  # Very relaxed RSI
        bearish_conditions = (ema_fast < ema_slow) & (rsi < 70)
        
        # Calculate signal strength
        signal_strength = abs(rsi - 50) / 50
        
        # Apply very relaxed filtering
        valid_bullish = bullish_conditions & (signal_strength >= min_signal_strength)
        valid_bearish = bearish_conditions & (signal_strength >= min_signal_strength)
        
        # Generate signals (very aggressive)
        for i in range(len(data)):
            if len(signals) >= max_trades:
                break
                
            if valid_bullish.iloc[i]:
                signals.append({
                    'type': 'BUY',
                    'strength': float(signal_strength.iloc[i]),
                    'timestamp': data['datetime'].iloc[i],
                    'size': 10000
                })
            elif valid_bearish.iloc[i]:
                signals.append({
                    'type': 'SELL',
                    'strength': float(signal_strength.iloc[i]),
                    'timestamp': data['datetime'].iloc[i],
                    'size': 10000
                })
        
        return signals
    
    def _execute_aggressive_trade(self, signal: dict, instrument: str, data: pd.DataFrame) -> dict:
        """Execute aggressive trade with simplified costs"""
        
        try:
            # Simple execution (no delay for aggressive testing)
            signal_time = signal['timestamp']
            
            # Find execution price
            execution_data = data[data['datetime'] >= signal_time].head(1)
            if len(execution_data) == 0:
                return None
            
            execution_row = execution_data.iloc[0]
            
            # Calculate entry price
            if signal['type'] == 'BUY':
                entry_price = execution_row['ask']
                stop_loss_price = entry_price * 0.998  # 0.2% stop loss
                take_profit_price = entry_price * 1.004  # 0.4% take profit
            else:
                entry_price = execution_row['bid']
                stop_loss_price = entry_price * 1.002  # 0.2% stop loss
                take_profit_price = entry_price * 0.996  # 0.4% take profit
            
            # Simple cost calculation
            spread_cost = execution_row['spread']
            slippage = spread_cost * 0.5
            total_cost = spread_cost + slippage
            
            return {
                'timestamp': signal_time.isoformat(),
                'instrument': instrument,
                'type': signal['type'],
                'entry_price': float(entry_price),
                'stop_loss_price': float(stop_loss_price),
                'take_profit_price': float(take_profit_price),
                'size': signal['size'],
                'spread_cost': float(spread_cost),
                'slippage': float(slippage),
                'total_cost': float(total_cost),
                'signal_strength': float(signal.get('strength', 0))
            }
            
        except Exception as e:
            print(f"   ❌ Error executing trade: {e}")
            return None
    
    def _calculate_performance(self, trades: list) -> dict:
        """Calculate performance metrics"""
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
            # Simplified P&L calculation
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

def main():
    """Main aggressive backtesting execution"""
    
    print("🚀 AGGRESSIVE BACKTESTING EXECUTION")
    print("=" * 60)
    print("⚠️  WARNING: Using relaxed parameters for maximum signal generation")
    print("=" * 60)
    
    try:
        # Initialize aggressive system
        live_data_path = r"H:\My Drive\desktop_backtesting_export"
        system = AggressiveBacktestingSystem(live_data_path)
        
        # Test periods
        test_periods = [
            {
                'name': 'Full Period',
                'start': '2025-09-18 00:00:00',
                'end': '2025-09-18 23:59:59'
            }
        ]
        
        strategies = ['alpha_strategy', 'gold_scalping', 'ultra_strict_forex']
        all_results = {}
        
        for period in test_periods:
            print(f"\n📊 Testing Period: {period['name']}")
            print(f"📅 {period['start']} to {period['end']}")
            
            period_results = {}
            
            for strategy in strategies:
                result = system.run_aggressive_backtest(
                    strategy,
                    period['start'],
                    period['end']
                )
                
                period_results[strategy] = result
                
                print(f"\n✅ {strategy} Results:")
                print(f"   📊 Total trades: {result['total_trades']}")
                if result['performance']:
                    print(f"   📈 Total return: {result['performance']['total_return']:.2%}")
                    print(f"   🎯 Win rate: {result['performance']['win_rate']:.1%}")
                    print(f"   📊 Sharpe ratio: {result['performance']['sharpe_ratio']:.2f}")
                    print(f"   💰 Avg cost per trade: ${result['performance']['avg_cost_per_trade']:.4f}")
            
            all_results[period['name']] = period_results
        
        # Save comprehensive results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"aggressive_backtesting_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        print(f"\n💾 Aggressive backtesting report saved to: {report_file}")
        
        # Print summary
        total_trades = sum(
            sum(pr[strategy]['total_trades'] for strategy in strategies)
            for pr in all_results.values()
        )
        
        print(f"\n🎉 AGGRESSIVE BACKTESTING COMPLETED")
        print(f"📊 Total Trades Generated: {total_trades}")
        print(f"🎯 Strategies Tested: {len(strategies)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)













