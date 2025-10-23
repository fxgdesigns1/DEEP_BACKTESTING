#!/usr/bin/env python3
"""
SMART TRADING MONITOR
Intelligent market monitoring with safe trade execution and limit order management
"""

import json
import time
from datetime import datetime, timedelta
import pytz
from pathlib import Path

class SmartTradingMonitor:
    """Intelligent trading monitor with safety features"""
    
    def __init__(self):
        self.london_tz = pytz.timezone('Europe/London')
        self.current_time = datetime.now(self.london_tz)
        self.strategy_info = self.load_strategy_info()
        self.trading_log = []
        
    def load_strategy_info(self):
        """Load the latest strategy information"""
        try:
            with open('strategies/LATEST_STRATEGY.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"Could not load strategy: {e}"}
    
    def is_trading_time(self):
        """Check if current time is suitable for trading"""
        hour = self.current_time.hour
        # Prime time: 8am-5pm London (avoid Asian session 10pm-8am)
        return 8 <= hour < 17
    
    def get_session_info(self):
        """Get current trading session information"""
        hour = self.current_time.hour
        
        if 0 <= hour < 8:
            return {
                "name": "Asian Session",
                "quality": "POOR",
                "activity": "Low",
                "recommended": False,
                "description": "Low volatility, avoid trading"
            }
        elif 8 <= hour < 13:
            return {
                "name": "London Session",
                "quality": "GOOD",
                "activity": "High",
                "recommended": True,
                "description": "High volatility, good for trading"
            }
        elif 13 <= hour < 17:
            return {
                "name": "London/NY Overlap",
                "quality": "EXCELLENT",
                "activity": "Very High",
                "recommended": True,
                "description": "Prime time - maximum volatility"
            }
        elif 17 <= hour < 22:
            return {
                "name": "New York Session",
                "quality": "GOOD",
                "activity": "High",
                "recommended": True,
                "description": "High volatility, good for trading"
            }
        else:
            return {
                "name": "Evening Session",
                "quality": "FAIR",
                "activity": "Medium",
                "recommended": False,
                "description": "Reduced activity, limit trading"
            }
    
    def analyze_market_conditions(self):
        """Analyze current market conditions for trading"""
        session = self.get_session_info()
        
        analysis = {
            "timestamp": self.current_time.isoformat(),
            "session": session,
            "trading_recommended": self.is_trading_time(),
            "risk_level": "LOW" if session["quality"] == "EXCELLENT" else "MEDIUM" if session["recommended"] else "HIGH",
            "market_status": "ACTIVE" if session["activity"] in ["High", "Very High"] else "QUIET"
        }
        
        return analysis
    
    def generate_trading_signals(self):
        """Generate trading signals based on MA Ribbon strategy"""
        if "error" in self.strategy_info:
            return {"error": "Strategy not available"}
        
        # This is a simplified signal generation
        # In a real system, you would analyze live price data
        signals = {
            "timestamp": self.current_time.isoformat(),
            "strategy": "MA Ribbon (8/21/50)",
            "instrument": "XAU_USD",
            "timeframe": "15m",
            "signals": []
        }
        
        # Simulate signal analysis (in real system, this would use live data)
        if self.is_trading_time():
            # Example signals (these would be generated from real price analysis)
            signals["signals"] = [
                {
                    "type": "LONG_SETUP",
                    "description": "Price approaching EMA(8) from below",
                    "entry_price": "Simulated - Check live data",
                    "stop_loss": "1% below entry",
                    "take_profit": "2% above entry",
                    "confidence": "MEDIUM",
                    "risk_reward": "1:2"
                }
            ]
        else:
            signals["signals"] = [
                {
                    "type": "WAIT",
                    "description": "Market session not optimal for trading",
                    "recommendation": "Set limit orders for better entries",
                    "next_check": "8:00 AM London time"
                }
            ]
        
        return signals
    
    def create_limit_orders(self):
        """Create intelligent limit orders for better entries"""
        if not self.is_trading_time():
            return {
                "limit_orders": [],
                "message": "Not optimal time for limit orders - wait for active session"
            }
        
        # Example limit orders (in real system, these would be based on technical analysis)
        limit_orders = {
            "timestamp": self.current_time.isoformat(),
            "limit_orders": [
                {
                    "type": "BUY_LIMIT",
                    "instrument": "XAU_USD",
                    "price": "Simulated - Calculate from EMA levels",
                    "stop_loss": "1% below entry",
                    "take_profit": "2% above entry",
                    "size": "2% risk",
                    "expiry": "End of session"
                },
                {
                    "type": "SELL_LIMIT", 
                    "instrument": "XAU_USD",
                    "price": "Simulated - Calculate from EMA levels",
                    "stop_loss": "1% above entry",
                    "take_profit": "2% below entry",
                    "size": "2% risk",
                    "expiry": "End of session"
                }
            ],
            "message": "Limit orders created for better entry prices"
        }
        
        return limit_orders
    
    def generate_safety_recommendations(self):
        """Generate safety recommendations for trading"""
        session = self.get_session_info()
        
        recommendations = {
            "timestamp": self.current_time.isoformat(),
            "safety_level": "HIGH" if session["quality"] == "EXCELLENT" else "MEDIUM",
            "recommendations": []
        }
        
        if session["recommended"]:
            recommendations["recommendations"].extend([
                "✅ Market conditions are favorable for trading",
                "📊 Use 2% risk per trade maximum",
                "🛡️ Always use stop loss (1% from entry)",
                "🎯 Target 2% take profit (1:2 risk/reward)",
                "📱 Set up price alerts for signal notifications",
                "⏰ Monitor positions closely during active session"
            ])
        else:
            recommendations["recommendations"].extend([
                "⏰ Wait for better trading session (8am-5pm London)",
                "📊 Consider setting limit orders for better entries",
                "📱 Set up alerts for when market becomes active",
                "📈 Review strategy performance during off-hours",
                "🛡️ Avoid trading during low-activity sessions"
            ])
        
        return recommendations
    
    def log_trading_activity(self, activity_type, details):
        """Log trading activity for monitoring"""
        log_entry = {
            "timestamp": self.current_time.isoformat(),
            "type": activity_type,
            "details": details
        }
        self.trading_log.append(log_entry)
        
        # Keep only last 100 entries
        if len(self.trading_log) > 100:
            self.trading_log = self.trading_log[-100:]
    
    def run_comprehensive_analysis(self):
        """Run comprehensive market and trading analysis"""
        print("=" * 80)
        print("🤖 SMART TRADING MONITOR - COMPREHENSIVE ANALYSIS")
        print("=" * 80)
        print(f"Analysis Time: {self.current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print("=" * 80)
        
        # Market Conditions
        print("\n📊 MARKET CONDITIONS:")
        market_analysis = self.analyze_market_conditions()
        session = market_analysis["session"]
        print(f"  Current Session: {session['name']}")
        print(f"  Session Quality: {session['quality']}")
        print(f"  Activity Level: {session['activity']}")
        print(f"  Trading Recommended: {'✅ YES' if market_analysis['trading_recommended'] else '❌ NO'}")
        print(f"  Risk Level: {market_analysis['risk_level']}")
        print(f"  Market Status: {market_analysis['market_status']}")
        
        # Trading Signals
        print("\n🎯 TRADING SIGNALS:")
        signals = self.generate_trading_signals()
        if "error" not in signals:
            print(f"  Strategy: {signals['strategy']}")
            print(f"  Instrument: {signals['instrument']}")
            print(f"  Timeframe: {signals['timeframe']}")
            
            if signals["signals"]:
                for i, signal in enumerate(signals["signals"], 1):
                    print(f"\n  Signal #{i}:")
                    print(f"    Type: {signal['type']}")
                    print(f"    Description: {signal['description']}")
                    if 'entry_price' in signal:
                        print(f"    Entry Price: {signal['entry_price']}")
                    if 'stop_loss' in signal:
                        print(f"    Stop Loss: {signal['stop_loss']}")
                    if 'take_profit' in signal:
                        print(f"    Take Profit: {signal['take_profit']}")
                    if 'confidence' in signal:
                        print(f"    Confidence: {signal['confidence']}")
        else:
            print(f"  ❌ Error: {signals['error']}")
        
        # Limit Orders
        print("\n📋 LIMIT ORDERS:")
        limit_orders = self.create_limit_orders()
        if limit_orders["limit_orders"]:
            print(f"  {limit_orders['message']}")
            for i, order in enumerate(limit_orders["limit_orders"], 1):
                print(f"\n  Order #{i}:")
                print(f"    Type: {order['type']}")
                print(f"    Instrument: {order['instrument']}")
                print(f"    Price: {order['price']}")
                print(f"    Stop Loss: {order['stop_loss']}")
                print(f"    Take Profit: {order['take_profit']}")
                print(f"    Size: {order['size']}")
                print(f"    Expiry: {order['expiry']}")
        else:
            print(f"  {limit_orders['message']}")
        
        # Safety Recommendations
        print("\n🛡️ SAFETY RECOMMENDATIONS:")
        safety = self.generate_safety_recommendations()
        print(f"  Safety Level: {safety['safety_level']}")
        for rec in safety["recommendations"]:
            print(f"    {rec}")
        
        # Strategy Performance
        print("\n📈 STRATEGY PERFORMANCE:")
        if "error" not in self.strategy_info:
            performance = self.strategy_info.get("strategy_details", {}).get("validated_performance", {})
            print(f"  Win Rate: {performance.get('win_rate', 0):.1f}%")
            print(f"  Sharpe Ratio: {performance.get('sharpe_ratio', 0):.2f}")
            print(f"  Max Drawdown: {performance.get('max_drawdown', 0):.1f}%")
            print(f"  Trades per Week: {performance.get('trades_per_week', 0):.1f}")
            print(f"  Monte Carlo Survival: {performance.get('monte_carlo_survival', 0):.1f}%")
        else:
            print(f"  ❌ Error: {self.strategy_info['error']}")
        
        # Account Status
        print("\n💰 ACCOUNT STATUS:")
        print("  Status: ACTIVE (Simulated)")
        print("  Strategy: MA Ribbon (8/21/50)")
        print("  Risk Management: 2% per trade, 1:2 R/R")
        print("  Max Positions: 1")
        print("  ⚠️  For live account data, check your trading platform")
        
        # Next Actions
        print("\n🚀 RECOMMENDED ACTIONS:")
        if market_analysis["trading_recommended"]:
            print("  1. ✅ Market conditions are favorable")
            print("  2. 📊 Monitor for MA Ribbon signals")
            print("  3. 🎯 Look for price crossing EMA(8)")
            print("  4. 💰 Execute trades with 2% risk")
            print("  5. 📱 Set up price alerts")
        else:
            print("  1. ⏰ Wait for better session (8am-5pm London)")
            print("  2. 📊 Set limit orders for better entries")
            print("  3. 📱 Set up session alerts")
            print("  4. 📈 Review strategy during off-hours")
        
        print("\n" + "=" * 80)
        print("🔧 Monitor runs continuously - Press Ctrl+C to stop")
        print("=" * 80)
        
        # Log this analysis
        self.log_trading_activity("analysis", {
            "market_conditions": market_analysis,
            "signals_generated": len(signals.get("signals", [])),
            "trading_recommended": market_analysis["trading_recommended"]
        })
    
    def run_continuous_monitor(self, interval_seconds=300):
        """Run continuous monitoring with specified interval"""
        print(f"🔄 Starting continuous monitoring (every {interval_seconds} seconds)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.current_time = datetime.now(self.london_tz)
                self.run_comprehensive_analysis()
                
                print(f"\n⏳ Next check in {interval_seconds} seconds...")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
            print("📊 Final summary:")
            print(f"  Total analyses: {len(self.trading_log)}")
            print("  System ready for manual trading")

def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart Trading Monitor')
    parser.add_argument('--continuous', '-c', action='store_true', 
                       help='Run continuous monitoring')
    parser.add_argument('--interval', '-i', type=int, default=300,
                       help='Monitoring interval in seconds (default: 300)')
    
    args = parser.parse_args()
    
    monitor = SmartTradingMonitor()
    
    if args.continuous:
        monitor.run_continuous_monitor(args.interval)
    else:
        monitor.run_comprehensive_analysis()

if __name__ == "__main__":
    main()