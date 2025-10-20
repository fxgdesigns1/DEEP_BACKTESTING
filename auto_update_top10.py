#!/usr/bin/env python3
"""
AUTO-UPDATE TOP 10 STRATEGIES
Continuously updates exported strategies as better ones are discovered
NEVER erases existing files - creates versioned updates
"""

import json
import yaml
import time
from pathlib import Path
from datetime import datetime

class AutoTop10Updater:
    """Auto-update TOP 10 without erasing existing files"""
    
    def __init__(self):
        self.base_export_path = Path(r"H:\My Drive\AI Trading\exported strategies\optimization_20251002_195254")
        self.top10_dir = self.base_export_path / "TOP_10_STRATEGIES"
        self.updates_dir = self.base_export_path / "STRATEGY_UPDATES"
        
        # Create updates directory
        self.updates_dir.mkdir(parents=True, exist_ok=True)
        
        self.last_update_count = 0
        
    def find_latest_results(self):
        """Find latest optimization results"""
        results_files = list(Path(".").glob("optimization_results_*.json"))
        
        if not results_files:
            return None
        
        return max(results_files, key=lambda p: p.stat().st_mtime)
    
    def check_for_updates(self):
        """Check if new strategies have been discovered"""
        
        results_file = self.find_latest_results()
        
        if not results_file:
            return False
        
        with open(results_file, 'r') as f:
            data = json.load(f)
        
        # Filter by criteria
        filtered = []
        for s in data.get('excellent', []):
            if s['win_rate'] >= 65.0 and s['max_dd'] <= 10.0:
                filtered.append(s)
        
        # Check if we have new strategies
        if len(filtered) > self.last_update_count:
            self.last_update_count = len(filtered)
            return filtered
        
        return False
    
    def export_updated_top10(self, strategies):
        """Export updated TOP 10 to new versioned folder"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        update_dir = self.updates_dir / f"TOP_10_UPDATE_{timestamp}"
        update_dir.mkdir(parents=True, exist_ok=True)
        
        # Sort by Sharpe
        strategies.sort(key=lambda x: x['sharpe'], reverse=True)
        top10 = strategies[:10]
        
        print(f"\n[UPDATE] New TOP 10 discovered at {datetime.now().strftime('%H:%M:%S')}")
        print(f"  Total strategies meeting criteria: {len(strategies)}")
        print(f"  Exporting to: {update_dir}")
        
        # Export each strategy
        for rank, strategy in enumerate(top10, 1):
            scenario = strategy['scenario']
            
            filename = f"RANK_{rank:02d}_{scenario['pair'].upper()}_{scenario['timeframe']}_Sharpe_{strategy['sharpe']:.1f}.yaml"
            filepath = update_dir / filename
            
            yaml_config = self.strategy_to_yaml(strategy, rank)
            
            with open(filepath, 'w') as f:
                yaml.dump(yaml_config, f, default_flow_style=False, sort_keys=False, indent=2)
            
            print(f"    [{rank:2d}] Sharpe: {strategy['sharpe']:.2f} | Win: {strategy['win_rate']:.1f}% | DD: {strategy['max_dd']:.1f}%")
        
        # Create update summary
        summary_file = update_dir / "UPDATE_SUMMARY.txt"
        with open(summary_file, 'w') as f:
            f.write(f"TOP 10 STRATEGY UPDATE\n")
            f.write(f"=" * 80 + "\n\n")
            f.write(f"Update Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Strategies Meeting Criteria: {len(strategies)}\n")
            f.write(f"Improvement: {len(strategies) - 10 if len(strategies) > 10 else 0} additional strategies discovered\n\n")
            f.write(f"TOP 10 RANKING:\n")
            f.write(f"{'-'*80}\n")
            f.write(f"Rank  Sharpe  Return   WinRate  MaxDD   Trades   Pair       Timeframe\n")
            f.write(f"{'-'*80}\n")
            
            for rank, s in enumerate(top10, 1):
                sc = s['scenario']
                f.write(f"{rank:4d}  {s['sharpe']:6.2f}  {s['annual_return']:6.1f}%  {s['win_rate']:6.1f}%  {s['max_dd']:5.1f}%  {s['total_trades']:6,}   {sc['pair'].upper():<10} {sc['timeframe']}\n")
        
        print(f"\n[SAVED] Update summary: {summary_file.name}")
        print(f"[PRESERVED] Original TOP 10 remains in: TOP_10_STRATEGIES/")
        
        return True
    
    def strategy_to_yaml(self, strategy, rank):
        """Convert strategy to YAML (same as before)"""
        scenario = strategy['scenario']
        
        return {
            'strategy_info': {
                'name': f"{scenario['pair'].upper()}_{scenario['timeframe']}_Strategy_Rank_{rank}",
                'rank': rank,
                'scenario_id': scenario['id'],
                'description': f"Optimized {scenario['pair'].upper()} strategy with {strategy['sharpe']:.2f} Sharpe ratio"
            },
            'instrument': {
                'pair': scenario['pair'].upper(),
                'timeframe': scenario['timeframe'],
            },
            'indicators': {
                'ema': {
                    'enabled': True,
                    'fast_period': scenario['ema_fast'],
                    'slow_period': scenario['ema_slow'],
                },
                'rsi': {
                    'enabled': True,
                    'period': 14,
                    'oversold': scenario['rsi_oversold'],
                    'overbought': scenario['rsi_overbought']
                },
                'atr': {
                    'enabled': True,
                    'period': 14,
                    'use_for_stops': True
                }
            },
            'exit_rules': {
                'stop_loss': {
                    'type': 'ATR_BASED',
                    'atr_multiplier': scenario['sl_atr_mult']
                },
                'take_profit': {
                    'type': 'RISK_REWARD',
                    'risk_reward_ratio': scenario['rr_ratio']
                }
            },
            'risk_management': {
                'risk_per_trade_pct': 1.5,
                'max_positions': 5,
                'max_daily_trades': 100,
                'portfolio_risk_limit': 10.0
            },
            'backtested_performance': {
                'test_period': '2023-03 to 2025-08',
                'total_trades': strategy['total_trades'],
                'win_rate_pct': round(strategy['win_rate'], 2),
                'sharpe_ratio': round(strategy['sharpe'], 2),
                'annual_return_pct': round(strategy['annual_return'], 2),
                'max_drawdown_pct': round(strategy['max_dd'], 2),
                'profit_factor': round(strategy['profit_factor'], 2)
            }
        }
    
    def monitor_and_update(self, check_interval=60):
        """Monitor optimization and auto-update TOP 10"""
        
        print("\n" + "=" * 100)
        print(" " * 30 + "AUTO-UPDATE MONITOR STARTED")
        print("=" * 100)
        print(f"Checking for updates every {check_interval} seconds")
        print(f"Original TOP 10 preserved in: {self.top10_dir}")
        print(f"Updates saved to: {self.updates_dir}")
        print("=" * 100 + "\n")
        
        try:
            iteration = 0
            while True:
                iteration += 1
                
                # Check for new strategies
                strategies = self.check_for_updates()
                
                if strategies:
                    # Export updated TOP 10
                    self.export_updated_top10(strategies)
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Check #{iteration}: No new strategies yet (Total: {self.last_update_count})")
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n\n[MONITOR STOPPED]")
            print("Optimization continues in background")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--dashboard':
        # Run dashboard mode
        dashboard = LiveDashboard()
        dashboard.run_live(refresh_seconds=30)
    else:
        # Run auto-update mode
        updater = AutoTop10Updater()
        updater.monitor_and_update(check_interval=60)


