#!/usr/bin/env python3
"""
ULTRA-SELECTIVE HIGH WIN RATE STRATEGY
Goal: 60%+ win rate by being VERY selective

Approach:
- Only trade the ABSOLUTE BEST setups
- Multiple confirmations required
- Trade count will drop significantly
- Win rate should increase dramatically
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class UltraSelectiveStrategy:
    """Ultra-selective strategy for high win rate"""
    
    def __init__(self, data_file):
        self.data = pd.read_csv(data_file)
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
        self.transaction_cost = 0.0002
        
        n = len(self.data)
        val_end = int(n * 0.80)
        self.test_data = self.data.iloc[val_end:].copy()
        
        logger.info(f"Test set: {len(self.test_data):,} candles")
    
    def calculate_indicators(self, df):
        """Calculate all indicators"""
        df = df.copy()
        
        # EMAs
        for period in [3, 8, 21, 50, 200]:
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
        
        # BB
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14).mean()
        
        # Volume
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        
        # Donchian
        df['dc_upper'] = df['high'].rolling(window=20).max()
        df['dc_lower'] = df['low'].rolling(window=20).min()
        
        return df
    
    def ultra_selective_ma_ribbon(self, df):
        """Ultra-selective MA Ribbon - Only the BEST setups"""
        signals = pd.Series(0, index=df.index)
        
        # Requirement 1: Perfect EMA alignment
        ema_aligned_bull = (df['ema_3'] > df['ema_8']) & (df['ema_8'] > df['ema_21']) & (df['ema_21'] > df['ema_50']) & (df['ema_50'] > df['ema_200'])
        ema_aligned_bear = (df['ema_3'] < df['ema_8']) & (df['ema_8'] < df['ema_21']) & (df['ema_21'] < df['ema_50']) & (df['ema_50'] < df['ema_200'])
        
        # Requirement 2: Fresh crossover (happened in last 1-3 candles)
        ema8_above_21 = (df['ema_8'] > df['ema_21']).astype(bool)
        ema8_above_21_3ago = ema8_above_21.shift(3).fillna(False)
        fresh_bull_cross = ema8_above_21 & (ema8_above_21_3ago == False)
        fresh_bear_cross = (ema8_above_21 == False) & (ema8_above_21_3ago == True)
        
        # Requirement 3: RSI confirmation (not overbought/oversold)
        rsi_ok_bull = (df['rsi'] > 40) & (df['rsi'] < 70)
        rsi_ok_bear = (df['rsi'] > 30) & (df['rsi'] < 60)
        
        # Requirement 4: Price pullback to EMA8 (better entry)
        pullback_to_ema8_bull = (df['close'] <= df['ema_8'] * 1.001) & (df['close'] >= df['ema_8'] * 0.999)
        pullback_to_ema8_bear = (df['close'] >= df['ema_8'] * 0.999) & (df['close'] <= df['ema_8'] * 1.001)
        
        # Combine ALL requirements for ultra-selective entry
        ultra_long = ema_aligned_bull & fresh_bull_cross & rsi_ok_bull & pullback_to_ema8_bull
        ultra_short = ema_aligned_bear & fresh_bear_cross & rsi_ok_bear & pullback_to_ema8_bear
        
        signals[ultra_long] = 1
        signals[ultra_short] = -1
        
        return signals
    
    def ultra_selective_bollinger(self, df):
        """Ultra-selective Bollinger - Only STRONG breakouts"""
        signals = pd.Series(0, index=df.index)
        
        # Requirement 1: Strong breakout (price well beyond band)
        strong_upper_break = df['close'] > df['bb_upper'] * 1.005  # 0.5% beyond upper band
        strong_lower_break = df['close'] < df['bb_lower'] * 0.995  # 0.5% below lower band
        
        # Requirement 2: Was NOT overbought/oversold in previous candle
        not_overbought_before = df['close'].shift() < df['bb_upper'].shift() * 1.002
        not_oversold_before = df['close'].shift() > df['bb_lower'].shift() * 0.998
        
        # Requirement 3: Volume surge (breakouts should have volume)
        volume_surge = df['volume'] > df['volume_ma'] * 1.2
        
        # Requirement 4: HTF trend alignment
        htf_bull = df['ema_50'] > df['ema_200']
        htf_bear = df['ema_50'] < df['ema_200']
        
        # Combine
        ultra_long = strong_upper_break & not_overbought_before & volume_surge & htf_bull
        ultra_short = strong_lower_break & not_oversold_before & volume_surge & htf_bear
        
        signals[ultra_long] = 1
        signals[ultra_short] = -1
        
        return signals
    
    def ultra_selective_donchian(self, df):
        """Ultra-selective Donchian - Only cleanest breakouts"""
        signals = pd.Series(0, index=df.index)
        
        # Requirement 1: Clean breakout (new high/low)
        clean_upper_break = (df['close'] > df['dc_upper'].shift()) & (df['high'] == df['dc_upper'])
        clean_lower_break = (df['close'] < df['dc_lower'].shift()) & (df['low'] == df['dc_lower'])
        
        # Requirement 2: Price momentum (strong move, not slow drift)
        strong_momentum_up = (df['close'] - df['open']) / df['open'] > 0.002  # 0.2% candle
        strong_momentum_down = (df['open'] - df['close']) / df['open'] > 0.002
        
        # Requirement 3: Not extended (RSI filter)
        not_extended_bull = df['rsi'] < 70
        not_extended_bear = df['rsi'] > 30
        
        # Combine
        ultra_long = clean_upper_break & strong_momentum_up & not_extended_bull
        ultra_short = clean_lower_break & strong_momentum_down & not_extended_bear
        
        signals[ultra_long] = 1
        signals[ultra_short] = -1
        
        return signals
    
    def backtest_optimized(self, df, signals, sl_pct=0.008, tp_pct=0.024):
        """Backtest with optimized stops (wider stops for higher win rate)"""
        trades = []
        position = None
        
        for i in range(len(df)):
            if i < 200:
                continue
            
            current_price = df.iloc[i]['close']
            
            if position is not None:
                if position['direction'] == 'long':
                    if current_price <= position['stop_loss']:
                        pnl_pct = (position['stop_loss'] - position['entry_price']) / position['entry_price'] - self.transaction_cost
                        trades.append({'pnl_pct': pnl_pct})
                        position = None
                    elif current_price >= position['take_profit']:
                        pnl_pct = (position['take_profit'] - position['entry_price']) / position['entry_price'] - self.transaction_cost
                        trades.append({'pnl_pct': pnl_pct})
                        position = None
                else:
                    if current_price >= position['stop_loss']:
                        pnl_pct = (position['entry_price'] - position['stop_loss']) / position['entry_price'] - self.transaction_cost
                        trades.append({'pnl_pct': pnl_pct})
                        position = None
                    elif current_price <= position['take_profit']:
                        pnl_pct = (position['entry_price'] - position['take_profit']) / position['entry_price'] - self.transaction_cost
                        trades.append({'pnl_pct': pnl_pct})
                        position = None
            
            if position is None and signals.iloc[i] != 0:
                direction = 'long' if signals.iloc[i] == 1 else 'short'
                entry_price = current_price * (1 + self.transaction_cost) if direction == 'long' else current_price * (1 - self.transaction_cost)
                
                if direction == 'long':
                    stop_loss = entry_price * (1 - sl_pct)
                    take_profit = entry_price * (1 + tp_pct)
                else:
                    stop_loss = entry_price * (1 + sl_pct)
                    take_profit = entry_price * (1 - tp_pct)
                
                position = {
                    'entry_price': entry_price,
                    'direction': direction,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit
                }
        
        return pd.DataFrame(trades)
    
    def calculate_metrics(self, trades_df):
        if len(trades_df) == 0:
            return {'total_trades': 0}
        returns = trades_df['pnl_pct'].values
        wins = returns > 0
        return {
            'total_trades': len(returns),
            'win_rate': np.mean(wins),
            'total_return': np.sum(returns),
            'sharpe_ratio': (np.mean(returns) / np.std(returns) * np.sqrt(252)) if np.std(returns) > 0 else 0,
            'max_drawdown': np.max(np.maximum.accumulate(np.cumsum(returns)) - np.cumsum(returns)),
            'profit_factor': np.sum(returns[wins]) / abs(np.sum(returns[~wins])) if np.sum(~wins) > 0 else 0
        }
    
    def run_monte_carlo(self, trades_df, n_runs=1000):
        if len(trades_df) == 0:
            return {'survival_rate': 0}
        returns = trades_df['pnl_pct'].values
        final_returns = [np.sum(np.random.permutation(returns)) for _ in range(n_runs)]
        return {'survival_rate': np.mean(np.array(final_returns) > 0)}

def main():
    logger.info("="*80)
    logger.info("ULTRA-SELECTIVE HIGH WIN RATE STRATEGY")
    logger.info("Multiple confirmations required for each trade")
    logger.info("="*80)
    
    tester = UltraSelectiveStrategy("data/MASTER_DATASET/15m/xau_usd_15m.csv")
    tester.test_data = tester.calculate_indicators(tester.test_data)
    
    test_weeks = (tester.test_data['timestamp'].max() - tester.test_data['timestamp'].min()).days / 7
    
    strategies = [
        ('ULTRA-SELECTIVE MA Ribbon', tester.ultra_selective_ma_ribbon),
        ('ULTRA-SELECTIVE Bollinger', tester.ultra_selective_bollinger),
        ('ULTRA-SELECTIVE Donchian', tester.ultra_selective_donchian)
    ]
    
    all_results = []
    
    for name, func in strategies:
        logger.info(f"\n{'='*80}")
        logger.info(f"{name}")
        logger.info(f"{'='*80}")
        
        signals = func(tester.test_data)
        trades = tester.backtest_optimized(tester.test_data, signals, sl_pct=0.008, tp_pct=0.024)
        metrics = tester.calculate_metrics(trades)
        mc = tester.run_monte_carlo(trades)
        
        tw = metrics['total_trades'] / test_weeks
        
        logger.info(f"  Total Trades: {metrics['total_trades']}")
        logger.info(f"  Trades/Week: {tw:.1f}")
        logger.info(f"  Win Rate: {metrics['win_rate']*100:.2f}% {'✓✓✓' if metrics['win_rate'] >= 0.60 else '✓✓' if metrics['win_rate'] >= 0.55 else '✓' if metrics['win_rate'] >= 0.50 else 'X'}")
        logger.info(f"  Return: {metrics['total_return']*100:.2f}%")
        logger.info(f"  Sharpe: {metrics['sharpe_ratio']:.2f}")
        logger.info(f"  Profit Factor: {metrics['profit_factor']:.2f}")
        logger.info(f"  MC Survival: {mc['survival_rate']*100:.1f}%")
        
        all_results.append({
            'strategy': name,
            'metrics': metrics,
            'trades_per_week': tw
        })
    
    # Find best win rate
    logger.info(f"\n{'='*80}")
    logger.info("BEST WIN RATE:")
    logger.info(f"{'='*80}")
    
    best = max(all_results, key=lambda x: x['metrics']['win_rate'])
    logger.info(f"\n{best['strategy']}")
    logger.info(f"  Win Rate: {best['metrics']['win_rate']*100:.2f}%")
    logger.info(f"  Return: {best['metrics']['total_return']*100:.2f}%")
    logger.info(f"  Sharpe: {best['metrics']['sharpe_ratio']:.2f}")
    logger.info(f"  Trades/Week: {best['trades_per_week']:.1f}")
    
    # Save
    with open(f"ultra_selective_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
        json.dump(all_results, f, indent=2, default=str)

if __name__ == "__main__":
    main()

