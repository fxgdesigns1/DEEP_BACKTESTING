"""
Quick analysis script for ultimate quality optimizer results
Run this if the overnight monitor didn't create WAKE_UP_SUMMARY.txt
"""

import json
import glob
from pathlib import Path
from datetime import datetime

def analyze_results():
    """Analyze ultimate quality optimizer results"""
    
    # Find latest results directory
    export_dir = Path("H:/My Drive/AI Trading/exported strategies")
    pattern = str(export_dir / "ultimate_quality_*")
    dirs = glob.glob(pattern)
    
    if not dirs:
        print("❌ No results directory found!")
        print("\nChecking if optimizer is still running...")
        import subprocess
        result = subprocess.run(["powershell", "Get-Process python -ErrorAction SilentlyContinue | Measure-Object"], 
                              capture_output=True, text=True)
        print(result.stdout)
        return
    
    latest_dir = max(dirs, key=os.path.getmtime)
    results_path = Path(latest_dir)
    
    print("="*100)
    print(" "*30 + "ULTIMATE QUALITY RESULTS ANALYSIS")
    print("="*100)
    print(f"\nResults Directory: {results_path}")
    print(f"Last Modified: {datetime.fromtimestamp(results_path.stat().st_mtime)}")
    
    # Load high quality strategies
    hq_file = results_path / "high_quality_strategies.json"
    all_file = results_path / "all_results.json"
    
    if not hq_file.exists():
        print("\n❌ No high_quality_strategies.json file found!")
        if all_file.exists():
            print("⚠️  But all_results.json exists - checking that...")
            with open(all_file) as f:
                all_data = json.load(f)
            print(f"\nTotal scenarios tested: {len(all_data)}")
            print("\nNo strategies met the 4% max drawdown criteria.")
            print("\n💡 RECOMMENDATIONS:")
            print("   1. Relax max drawdown to 5%")
            print("   2. Lower win rate requirement to 55%")
            print("   3. Test on longer timeframes (4h)")
            print("   4. Use strategies from FINAL_MULTI_TIMEFRAME_STRATEGIES.yaml")
        return
    
    with open(hq_file) as f:
        strategies = json.load(f)
    
    print(f"\n✅ HIGH QUALITY STRATEGIES FOUND: {len(strategies)}")
    
    if len(strategies) == 0:
        print("\n⚠️  No strategies met the 4% DD criteria")
        print("\n💡 Use the proven strategies from FINAL_MULTI_TIMEFRAME_STRATEGIES.yaml instead!")
        return
    
    # Analyze by timeframe
    by_timeframe = {}
    for strat in strategies:
        tf = strat['timeframe']
        if tf not in by_timeframe:
            by_timeframe[tf] = []
        by_timeframe[tf].append(strat)
    
    print("\n" + "="*100)
    print("STRATEGIES BY TIMEFRAME")
    print("="*100)
    for tf, strats in sorted(by_timeframe.items()):
        avg_sharpe = sum(s.get('sharpe_ratio', 0) for s in strats) / len(strats)
        avg_return = sum(s.get('annual_return_%', 0) for s in strats) / len(strats)
        avg_dd = sum(s.get('max_drawdown_%', 0) for s in strats) / len(strats)
        
        print(f"\n{tf.upper()}: {len(strats)} strategies")
        print(f"   Avg Sharpe: {avg_sharpe:.2f}")
        print(f"   Avg Return: {avg_return:.1f}%")
        print(f"   Avg DD: {avg_dd:.2f}%")
    
    # Top 10 overall
    print("\n" + "="*100)
    print("TOP 10 STRATEGIES (BY SHARPE RATIO)")
    print("="*100)
    top_10 = sorted(strategies, key=lambda x: x.get('sharpe_ratio', 0), reverse=True)[:10]
    
    for i, s in enumerate(top_10, 1):
        print(f"\n#{i}: {s['pair']} on {s['timeframe']}")
        print(f"   Sharpe Ratio: {s.get('sharpe_ratio', 0):.2f}")
        print(f"   Annual Return: {s.get('annual_return_%', 0):.1f}%")
        print(f"   Win Rate: {s.get('win_rate_%', 0):.1f}%")
        print(f"   Max Drawdown: {s.get('max_drawdown_%', 0):.2f}%")
        print(f"   Profit Factor: {s.get('profit_factor', 0):.2f}")
        print(f"   Total Trades: {s.get('total_trades', 0)}")
        print(f"   Avg Win: {s.get('avg_win_%', 0):.2f}% | Avg Loss: {s.get('avg_loss_%', 0):.2f}%")
        
        # Show parameters
        params = s.get('parameters', {})
        print(f"   EMA: {params.get('fast_ema')}/{params.get('slow_ema')} | "
              f"SL: {params.get('stop_loss_atr_mult', 0):.1f}x | "
              f"TP: {params.get('take_profit_atr_mult', 0):.1f}x")
    
    print("\n" + "="*100)
    print("NEXT STEPS")
    print("="*100)
    print("1. Review strategies above")
    print("2. Check deployment_ready.yaml in results directory")
    print("3. Deploy top 3-5 to demo accounts")
    print("4. Monitor for 1-2 weeks before going live")
    
    print("\n" + "="*100)
    print(f"Full results available at: {results_path}")
    print("="*100)

if __name__ == "__main__":
    import os
    analyze_results()





