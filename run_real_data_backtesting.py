#!/usr/bin/env python3
"""
REAL DATA BACKTESTING - Using Your 3 Years of Historical Data
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from improved_backtesting_system_oct2025 import ImprovedBacktestingSystem, NewsEvent

def load_real_price_data(pair, timeframe='15m'):
    """Load your real MASTER_DATASET price data"""
    data_file = f"data/MASTER_DATASET/{timeframe}/{pair.lower()}_{timeframe}.csv"
    
    print(f"Loading {pair} {timeframe} from {data_file}...")
    
    df = pd.read_csv(data_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    # Ensure proper column names
    df.columns = df.columns.str.lower()
    
    print(f"  Loaded {len(df)} candles ({df.index.min()} to {df.index.max()})")
    
    return df

def load_news_events(pair):
    """Load your real news data"""
    news_file = f"data/MASTER_DATASET/news/{pair.lower()}_news.csv"
    
    if not Path(news_file).exists():
        print(f"  No news data found for {pair}")
        return []
    
    news_df = pd.read_csv(news_file)
    news_df['timestamp'] = pd.to_datetime(news_df['timestamp'])
    
    events = []
    for _, row in news_df.iterrows():
        events.append(NewsEvent(
            timestamp=row['timestamp'],
            event_type=row.get('title', 'Economic Event'),
            impact=row.get('impact', 'medium'),
            currency=pair.split('_')[0]
        ))
    
    print(f"  Loaded {len(events)} news events")
    return events

def run_strategy_on_real_data():
    """Run all strategies on your real data"""
    
    print("=" * 80)
    print("REAL DATA BACKTESTING - Using Your 3 Years of Historical Data")
    print("=" * 80)
    print()
    
    # Initialize the October 2025 system
    backtest = ImprovedBacktestingSystem('backtesting_config_oct2025.yaml')
    
    # Test configurations
    test_configs = [
        {'pair': 'xau_usd', 'strategy': 'gold_scalping', 'timeframe': '15m'},
        {'pair': 'eur_usd', 'strategy': 'ultra_strict_forex', 'timeframe': '15m'},
        {'pair': 'gbp_usd', 'strategy': 'ultra_strict_forex', 'timeframe': '15m'},
        {'pair': 'aud_usd', 'strategy': 'momentum_trading', 'timeframe': '15m'},
    ]
    
    all_results = []
    
    for config in test_configs:
        print("\n" + "=" * 80)
        print(f"Testing {config['pair'].upper()} - {config['strategy']}")
        print("=" * 80)
        
        try:
            # Load your real price data
            df = load_real_price_data(config['pair'], config['timeframe'])
            
            # Load higher timeframe for HTF alignment
            htf_df = load_real_price_data(config['pair'], '1h')
            
            # Load news events
            news_events = load_news_events(config['pair'])
            
            # Run backtest
            print(f"\nRunning {config['strategy']} strategy...")
            results = backtest.run_backtest(
                strategy_name=config['strategy'],
                df=df,
                htf_df=htf_df,
                news_events=news_events
            )
            
            # Print results
            metrics = results['metrics']
            print(f"\n[RESULTS] {config['pair'].upper()} - {config['strategy']}")
            print(f"  Total Return: {metrics['total_return_pct']:.2f}%")
            print(f"  Win Rate: {metrics['win_rate']:.1f}%")
            print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
            print(f"  Max Drawdown: {metrics['max_drawdown_pct']:.2f}%")
            print(f"  Total Trades: {metrics['total_trades']}")
            print(f"  Profit Factor: {metrics.get('profit_factor', 0):.2f}")
            
            if 'quality_stats' in results:
                print(f"  Avg Quality Score: {results['quality_stats']['avg_quality_score']:.1f}/100")
            
            # Store results
            all_results.append({
                'pair': config['pair'],
                'strategy': config['strategy'],
                'timeframe': config['timeframe'],
                'metrics': metrics
            })
            
        except Exception as e:
            print(f"\n[ERROR] Failed to test {config['pair']}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Find best strategy
    print("\n" + "=" * 80)
    print(">>> BEST STRATEGY FROM REAL DATA <<<")
    print("=" * 80)
    
    if all_results:
        best = max(all_results, key=lambda x: x['metrics'].get('sharpe_ratio', 0))
        
        print(f"Pair: {best['pair'].upper()}")
        print(f"Strategy: {best['strategy']}")
        print(f"Timeframe: {best['timeframe']}")
        print(f"Total Return: {best['metrics']['total_return_pct']:.2f}%")
        print(f"Sharpe Ratio: {best['metrics']['sharpe_ratio']:.2f}")
        print(f"Win Rate: {best['metrics']['win_rate']:.1f}%")
        print(f"Total Trades: {best['metrics']['total_trades']}")
        
        # Save results
        report_file = f"real_data_backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'all_results': all_results,
                'best_strategy': best
            }, f, indent=2, default=str)
        
        print(f"\n[SAVED] Results saved to: {report_file}")
    else:
        print("[ERROR] No successful backtests completed")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    run_strategy_on_real_data()

