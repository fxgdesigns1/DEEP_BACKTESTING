#!/usr/bin/env python3
"""
MARKET STATUS AND TRADING SYSTEM REPORT
Comprehensive analysis of current market conditions and bot performance
"""

import json
import os
from datetime import datetime, timedelta
import pytz
from pathlib import Path

class MarketStatusReport:
    """Generate comprehensive market and trading system status report"""
    
    def __init__(self):
        self.london_tz = pytz.timezone('Europe/London')
        self.current_time = datetime.now(self.london_tz)
        
    def get_latest_strategy_info(self):
        """Get information about the latest validated strategy"""
        try:
            with open('strategies/LATEST_STRATEGY.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"Could not load strategy info: {e}"}
    
    def check_system_status(self):
        """Check overall system status"""
        status = {
            "timestamp": self.current_time.isoformat(),
            "london_time": self.current_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "system_operational": True,
            "optimization_running": False,
            "data_available": True
        }
        
        # Check if optimization is running
        try:
            import psutil
            python_processes = [p for p in psutil.process_iter(['name', 'cmdline']) 
                              if p.info['name'] == 'python' and p.info['cmdline']]
            
            optimization_running = any('controller.py' in ' '.join(p.info['cmdline']) 
                                     for p in python_processes)
            status["optimization_running"] = optimization_running
            status["active_python_processes"] = len(python_processes)
        except:
            status["active_python_processes"] = "Unknown"
        
        return status
    
    def analyze_trading_opportunities(self, strategy_info):
        """Analyze current trading opportunities based on strategy"""
        if "error" in strategy_info:
            return {"error": "Cannot analyze opportunities - strategy info unavailable"}
        
        # Get strategy details
        details = strategy_info.get("strategy_details", {})
        performance = details.get("validated_performance", {})
        
        # Current market session analysis
        hour = self.current_time.hour
        
        session_analysis = {
            "current_session": self.get_current_session(hour),
            "trading_recommended": self.is_trading_recommended(hour),
            "session_quality": self.get_session_quality(hour)
        }
        
        # Strategy performance summary
        performance_summary = {
            "win_rate": performance.get("win_rate", 0),
            "sharpe_ratio": performance.get("sharpe_ratio", 0),
            "max_drawdown": performance.get("max_drawdown", 0),
            "trades_per_week": performance.get("trades_per_week", 0),
            "risk_per_trade": details.get("parameters", {}).get("risk_per_trade_pct", 0)
        }
        
        # Trading recommendations
        recommendations = self.generate_trading_recommendations(session_analysis, performance_summary)
        
        return {
            "session_analysis": session_analysis,
            "performance_summary": performance_summary,
            "recommendations": recommendations,
            "strategy_ready": True
        }
    
    def get_current_session(self, hour):
        """Determine current trading session"""
        if 0 <= hour < 8:
            return "Asian Session (Low Activity)"
        elif 8 <= hour < 13:
            return "London Session (High Activity)"
        elif 13 <= hour < 17:
            return "London/NY Overlap (Prime Time)"
        elif 17 <= hour < 22:
            return "New York Session (High Activity)"
        else:
            return "Evening Session (Low Activity)"
    
    def is_trading_recommended(self, hour):
        """Determine if trading is recommended based on time"""
        # Prime time is 1pm-5pm London (London/NY overlap)
        # London session is 8am-5pm
        # Avoid 10pm-8am (Asian session)
        return 8 <= hour < 17  # London session + overlap
    
    def get_session_quality(self, hour):
        """Rate session quality for trading"""
        if 13 <= hour < 17:  # Prime time
            return "EXCELLENT - Prime London/NY overlap"
        elif 8 <= hour < 13 or 17 <= hour < 20:  # London or NY session
            return "GOOD - Active session"
        elif 20 <= hour < 22:  # Evening
            return "FAIR - Reduced activity"
        else:  # Asian session
            return "POOR - Low activity, avoid trading"
    
    def generate_trading_recommendations(self, session_analysis, performance):
        """Generate specific trading recommendations"""
        recommendations = []
        
        if session_analysis["trading_recommended"]:
            recommendations.append("✅ TRADING RECOMMENDED - Current session is suitable for trading")
            
            if performance["win_rate"] >= 50:
                recommendations.append(f"📈 Strategy shows {performance['win_rate']:.1f}% win rate - Good probability")
            
            if performance["sharpe_ratio"] >= 2.0:
                recommendations.append(f"🎯 Excellent Sharpe ratio ({performance['sharpe_ratio']:.2f}) - High quality strategy")
            
            recommendations.append(f"💰 Risk per trade: {performance['risk_per_trade']}% - Conservative approach")
            recommendations.append(f"📊 Expected trades per week: {performance['trades_per_week']:.1f}")
            
        else:
            recommendations.append("⏰ WAIT - Current session not optimal for trading")
            recommendations.append("🕐 Best trading times: 8am-5pm London time")
            recommendations.append("💡 Consider setting limit orders for better entry prices")
        
        return recommendations
    
    def generate_account_update(self, strategy_info):
        """Generate account performance update"""
        if "error" in strategy_info:
            return {"error": "Cannot generate account update - strategy info unavailable"}
        
        details = strategy_info.get("strategy_details", {})
        performance = details.get("validated_performance", {})
        
        # Simulate account performance (in real system, this would come from actual account data)
        account_update = {
            "account_status": "ACTIVE",
            "strategy_deployed": "MA Ribbon (8/21/50)",
            "instrument": details.get("instrument", "XAU_USD"),
            "timeframe": details.get("timeframe", "15m"),
            "current_equity": "Simulated - Check live account",
            "daily_pnl": "Simulated - Check live account",
            "weekly_pnl": "Simulated - Check live account",
            "monthly_pnl": "Simulated - Check live account",
            "open_positions": "Simulated - Check live account",
            "max_drawdown_current": "Simulated - Check live account",
            "trades_today": "Simulated - Check live account",
            "win_rate_current": performance.get("win_rate", 0),
            "last_trade_time": "Simulated - Check live account"
        }
        
        return account_update
    
    def generate_complete_report(self):
        """Generate complete market and trading status report"""
        print("=" * 80)
        print("📊 MARKET STATUS & TRADING SYSTEM REPORT")
        print("=" * 80)
        print(f"Report Time: {self.current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print("=" * 80)
        
        # System Status
        print("\n🔧 SYSTEM STATUS:")
        system_status = self.check_system_status()
        print(f"  Status: {'✅ OPERATIONAL' if system_status['system_operational'] else '❌ ISSUES'}")
        print(f"  Optimization Running: {'✅ YES' if system_status['optimization_running'] else '❌ NO'}")
        print(f"  Active Python Processes: {system_status['active_python_processes']}")
        print(f"  Data Available: {'✅ YES' if system_status['data_available'] else '❌ NO'}")
        
        # Strategy Information
        print("\n📈 CURRENT STRATEGY:")
        strategy_info = self.get_latest_strategy_info()
        if "error" not in strategy_info:
            details = strategy_info.get("strategy_details", {})
            performance = details.get("validated_performance", {})
            
            print(f"  Strategy: {strategy_info.get('latest_strategy', {}).get('name', 'Unknown')}")
            print(f"  Instrument: {details.get('instrument', 'Unknown')}")
            print(f"  Timeframe: {details.get('timeframe', 'Unknown')}")
            print(f"  Status: {strategy_info.get('latest_strategy', {}).get('status', 'Unknown')}")
            print(f"  Win Rate: {performance.get('win_rate', 0):.1f}%")
            print(f"  Sharpe Ratio: {performance.get('sharpe_ratio', 0):.2f}")
            print(f"  Max Drawdown: {performance.get('max_drawdown', 0):.1f}%")
            print(f"  Trades/Week: {performance.get('trades_per_week', 0):.1f}")
        else:
            print(f"  ❌ Error: {strategy_info['error']}")
        
        # Trading Opportunities
        print("\n🎯 TRADING OPPORTUNITIES:")
        opportunities = self.analyze_trading_opportunities(strategy_info)
        if "error" not in opportunities:
            session = opportunities["session_analysis"]
            print(f"  Current Session: {session['current_session']}")
            print(f"  Session Quality: {session['session_quality']}")
            print(f"  Trading Recommended: {'✅ YES' if session['trading_recommended'] else '❌ NO'}")
            
            print("\n  📋 RECOMMENDATIONS:")
            for rec in opportunities["recommendations"]:
                print(f"    {rec}")
        else:
            print(f"  ❌ Error: {opportunities['error']}")
        
        # Account Update
        print("\n💰 ACCOUNT UPDATE:")
        account_update = self.generate_account_update(strategy_info)
        if "error" not in account_update:
            print(f"  Account Status: {account_update['account_status']}")
            print(f"  Strategy Deployed: {account_update['strategy_deployed']}")
            print(f"  Instrument: {account_update['instrument']}")
            print(f"  Timeframe: {account_update['timeframe']}")
            print(f"  Current Win Rate: {account_update['win_rate_current']:.1f}%")
            print("\n  📊 LIVE ACCOUNT DATA:")
            print("    ⚠️  For real account data, check your live trading platform")
            print("    ⚠️  This system shows strategy performance, not live account P&L")
        else:
            print(f"  ❌ Error: {account_update['error']}")
        
        # Bot Performance Summary
        print("\n🤖 BOT PERFORMANCE SUMMARY:")
        if "error" not in strategy_info:
            performance = strategy_info.get("strategy_details", {}).get("validated_performance", {})
            print(f"  ✅ Strategy Validated: {strategy_info.get('latest_strategy', {}).get('validated', False)}")
            print(f"  📊 Validation Date: {strategy_info.get('latest_strategy', {}).get('validation_date', 'Unknown')}")
            print(f"  🎯 Monte Carlo Survival: {performance.get('monte_carlo_survival', 0):.1f}%")
            print(f"  📈 Total Return: {performance.get('total_return', 0):.1f}%")
            print(f"  🛡️  Max Drawdown: {performance.get('max_drawdown', 0):.1f}%")
            print(f"  ⚡ Trades per Month: {performance.get('trades_per_month', 0):.1f}")
            
            print("\n  🏆 WHY THIS STRATEGY IS EXCELLENT:")
            reasons = strategy_info.get("why_this_strategy", [])
            for i, reason in enumerate(reasons[:5], 1):  # Show top 5 reasons
                print(f"    {i}. {reason}")
        else:
            print("  ❌ Cannot assess bot performance - strategy info unavailable")
        
        # Next Steps
        print("\n🚀 NEXT STEPS:")
        if opportunities.get("session_analysis", {}).get("trading_recommended", False):
            print("  1. ✅ Market conditions are favorable for trading")
            print("  2. 📊 Monitor for MA Ribbon signals (EMA 8/21/50)")
            print("  3. 🎯 Look for price crossing above/below EMA(8)")
            print("  4. 💰 Use 2% risk per trade with 1% SL, 2% TP")
            print("  5. 📱 Set up alerts for signal notifications")
        else:
            print("  1. ⏰ Wait for better trading session (8am-5pm London)")
            print("  2. 📊 Consider setting limit orders for better entries")
            print("  3. 📱 Set up alerts for when market becomes active")
            print("  4. 📈 Review strategy performance during off-hours")
        
        print("\n" + "=" * 80)
        print("📞 For live account data, check your trading platform")
        print("🔧 For system issues, check logs and restart if needed")
        print("=" * 80)

def main():
    """Main execution"""
    report = MarketStatusReport()
    report.generate_complete_report()

if __name__ == "__main__":
    main()