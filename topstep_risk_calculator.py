"""
TopStep 100K Challenge - Risk Calculator & Progress Tracker
Ensures compliance with TopStep rules
"""

import json
from datetime import datetime
from pathlib import Path

class TopStepRiskManager:
    def __init__(self):
        # Account parameters
        self.account_size = 100000
        self.profit_target = 6000
        self.daily_loss_limit = 2000
        self.trailing_max_dd = 3000
        self.consistency_limit = 3000  # 50% of profit target
        
        # Current state
        self.starting_balance = 100000
        self.current_balance = 100000
        self.highest_balance = 100000
        self.daily_pnl = 0
        self.total_pnl = 0
        self.today_trades = 0
        
        # Tracking
        self.daily_history = []
        self.trade_log = []
    
    def calculate_trailing_drawdown(self):
        """Calculate current trailing drawdown"""
        return self.highest_balance - self.current_balance
    
    def calculate_max_allowed_loss(self):
        """Calculate max allowed loss for current position"""
        # Daily limit remaining
        daily_remaining = self.daily_loss_limit - abs(min(0, self.daily_pnl))
        
        # Trailing DD remaining
        trailing_remaining = self.trailing_max_dd - self.calculate_trailing_drawdown()
        
        # Return the stricter limit
        return min(daily_remaining, trailing_remaining)
    
    def calculate_position_size(self, stop_loss_ticks, tick_value, risk_dollars=200):
        """
        Calculate number of contracts based on stop loss
        
        Args:
            stop_loss_ticks: Number of ticks for stop loss (e.g., 20 ticks)
            tick_value: Value per tick (e.g., $12.50 for ES)
            risk_dollars: Amount willing to risk (default $200)
        
        Returns:
            Number of contracts to trade
        """
        # Risk per contract = stop_loss_ticks * tick_value
        risk_per_contract = stop_loss_ticks * tick_value
        
        # Calculate contracts
        contracts = int(risk_dollars / risk_per_contract)
        
        # Safety limits
        max_allowed = self.get_max_contracts_allowed()
        contracts = min(contracts, max_allowed)
        contracts = max(contracts, 1)  # At least 1 contract
        
        return contracts
    
    def get_max_contracts_allowed(self):
        """Get maximum contracts based on current state"""
        # Base limit
        base_max = 2  # Conservative start
        
        # Check if we're in good state
        if self.total_pnl > 2000:  # If up $2,000
            base_max = 3
        elif self.total_pnl > 4000:  # If up $4,000
            base_max = 4
        
        # Reduce if having a bad day
        if self.daily_pnl < -500:
            base_max = 1
        elif self.daily_pnl < -1000:
            return 0  # Stop trading!
        
        return base_max
    
    def can_take_trade(self):
        """Check if allowed to take a new trade"""
        reasons = []
        
        # Check daily loss limit (with buffer)
        if self.daily_pnl <= -1500:
            reasons.append(f"Daily loss limit approached: ${self.daily_pnl:.2f}")
        
        # Check trailing drawdown (with buffer)
        current_dd = self.calculate_trailing_drawdown()
        if current_dd >= 2500:
            reasons.append(f"Trailing drawdown limit approached: ${current_dd:.2f}")
        
        # Check consistency rule
        if self.daily_pnl >= 2500:
            reasons.append(f"Consistency limit approached: ${self.daily_pnl:.2f}")
        
        # Check time (assume 4:00 PM ET cutoff)
        current_hour = datetime.now().hour
        if current_hour >= 16:
            reasons.append("Past trading cutoff time (4:00 PM ET)")
        
        # Check trade count
        if self.today_trades >= 15:
            reasons.append(f"Daily trade limit reached: {self.today_trades}")
        
        if reasons:
            return False, reasons
        return True, []
    
    def record_trade(self, pnl, instrument, entry_price, exit_price, contracts):
        """Record a completed trade"""
        trade = {
            'timestamp': datetime.now().isoformat(),
            'instrument': instrument,
            'contracts': contracts,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'daily_pnl_after': self.daily_pnl + pnl,
            'total_pnl_after': self.total_pnl + pnl
        }
        
        # Update balances
        self.current_balance += pnl
        self.daily_pnl += pnl
        self.total_pnl += pnl
        self.today_trades += 1
        
        # Update highest balance
        if self.current_balance > self.highest_balance:
            self.highest_balance = self.current_balance
        
        # Save trade
        self.trade_log.append(trade)
        
        # Check for violations
        self.check_violations()
        
        return trade
    
    def check_violations(self):
        """Check for rule violations"""
        violations = []
        
        # Daily loss limit
        if self.daily_pnl <= -self.daily_loss_limit:
            violations.append(f"VIOLATION: Daily loss limit exceeded: ${self.daily_pnl:.2f}")
        
        # Trailing drawdown
        current_dd = self.calculate_trailing_drawdown()
        if current_dd >= self.trailing_max_dd:
            violations.append(f"VIOLATION: Trailing max drawdown exceeded: ${current_dd:.2f}")
        
        # Consistency rule
        if self.daily_pnl >= self.consistency_limit:
            violations.append(f"VIOLATION: Consistency rule - single day profit too high: ${self.daily_pnl:.2f}")
        
        if violations:
            print("\n" + "="*80)
            print("RULE VIOLATIONS DETECTED!")
            print("="*80)
            for v in violations:
                print(f"[X] {v}")
            print("="*80)
            print("CHALLENGE FAILED - ACCOUNT RESET REQUIRED")
            print("="*80)
        
        return violations
    
    def end_of_day_summary(self):
        """Print end of day summary and reset daily counters"""
        print("\n" + "="*80)
        print(f"END OF DAY SUMMARY - {datetime.now().strftime('%Y-%m-%d')}")
        print("="*80)
        
        print(f"\nDaily Performance:")
        print(f"  P&L: ${self.daily_pnl:,.2f}")
        print(f"  Trades: {self.today_trades}")
        if self.today_trades > 0:
            print(f"  Avg per Trade: ${self.daily_pnl/self.today_trades:.2f}")
        
        print(f"\nAccount Status:")
        print(f"  Starting Balance: ${self.starting_balance:,.2f}")
        print(f"  Current Balance: ${self.current_balance:,.2f}")
        print(f"  Total P&L: ${self.total_pnl:,.2f}")
        print(f"  Highest Balance: ${self.highest_balance:,.2f}")
        
        print(f"\nChallenge Progress:")
        progress_pct = (self.total_pnl / self.profit_target) * 100
        print(f"  Profit Target: ${self.profit_target:,.2f}")
        print(f"  Progress: ${self.total_pnl:,.2f} ({progress_pct:.1f}%)")
        print(f"  Remaining: ${self.profit_target - self.total_pnl:,.2f}")
        
        days_elapsed = len(self.daily_history) + 1
        if self.total_pnl > 0:
            avg_daily = self.total_pnl / days_elapsed
            days_to_goal = (self.profit_target - self.total_pnl) / avg_daily
            print(f"  Avg Daily P&L: ${avg_daily:.2f}")
            print(f"  Est. Days to Goal: {days_to_goal:.1f}")
        
        print(f"\nRisk Metrics:")
        current_dd = self.calculate_trailing_drawdown()
        print(f"  Trailing Drawdown: ${current_dd:,.2f} / ${self.trailing_max_dd:,.2f}")
        print(f"  DD Buffer Remaining: ${self.trailing_max_dd - current_dd:,.2f}")
        
        # Check if passed
        if self.total_pnl >= self.profit_target:
            print("\n" + "="*80)
            print("*** CHALLENGE PASSED! ***")
            print("="*80)
            print(f"Profit Target Achieved: ${self.total_pnl:,.2f}")
            print(f"Days Taken: {days_elapsed}")
            print("Ready for funded account!")
        
        print("="*80)
        
        # Save daily record
        daily_record = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'daily_pnl': self.daily_pnl,
            'total_pnl': self.total_pnl,
            'current_balance': self.current_balance,
            'trades': self.today_trades,
            'trailing_dd': current_dd
        }
        self.daily_history.append(daily_record)
        
        # Reset daily counters
        self.daily_pnl = 0
        self.today_trades = 0
    
    def print_current_status(self):
        """Print current intraday status"""
        print("\n" + "="*80)
        print("CURRENT STATUS")
        print("="*80)
        
        print(f"\nToday's Performance:")
        print(f"  P&L: ${self.daily_pnl:,.2f}")
        print(f"  Trades: {self.today_trades}")
        
        print(f"\nDaily Limits:")
        daily_loss_remaining = self.daily_loss_limit - abs(min(0, self.daily_pnl))
        daily_profit_to_consistency = self.consistency_limit - max(0, self.daily_pnl)
        print(f"  Loss Limit Remaining: ${daily_loss_remaining:,.2f}")
        print(f"  Profit to Consistency Limit: ${daily_profit_to_consistency:,.2f}")
        
        print(f"\nTrailing Drawdown:")
        current_dd = self.calculate_trailing_drawdown()
        dd_remaining = self.trailing_max_dd - current_dd
        print(f"  Current DD: ${current_dd:,.2f}")
        print(f"  DD Limit Remaining: ${dd_remaining:,.2f}")
        
        # Can trade?
        can_trade, reasons = self.can_take_trade()
        if can_trade:
            print(f"\n[OK] CLEAR TO TRADE")
            print(f"  Max Contracts Allowed: {self.get_max_contracts_allowed()}")
        else:
            print(f"\n[X] TRADING RESTRICTED:")
            for reason in reasons:
                print(f"  - {reason}")
        
        print("="*80)

# Example usage
if __name__ == "__main__":
    print("="*80)
    print(" "*20 + "TOPSTEP 100K RISK CALCULATOR")
    print("="*80)
    
    # Initialize risk manager
    rm = TopStepRiskManager()
    
    # Example: Calculate position size for ES trade
    print("\n" + "="*80)
    print("POSITION SIZE CALCULATOR")
    print("="*80)
    
    print("\nExample 1: ES (S&P 500) Trade")
    print("  Stop Loss: 20 ticks")
    print("  Tick Value: $12.50")
    print("  Risk Amount: $200")
    
    contracts = rm.calculate_position_size(
        stop_loss_ticks=20,
        tick_value=12.50,
        risk_dollars=200
    )
    
    print(f"\n  >> Trade {contracts} contracts")
    print(f"  >> Risk per contract: ${20 * 12.50:.2f}")
    print(f"  >> Total risk: ${contracts * 20 * 12.50:.2f}")
    
    # Example: Calculate for different instruments
    instruments = [
        {'name': 'ES (S&P)', 'tick_value': 12.50, 'stop_ticks': 20},
        {'name': 'NQ (Nasdaq)', 'tick_value': 5.00, 'stop_ticks': 40},
        {'name': 'GC (Gold)', 'tick_value': 10.00, 'stop_ticks': 20},
    ]
    
    print("\n" + "="*80)
    print("POSITION SIZING FOR DIFFERENT INSTRUMENTS")
    print("="*80)
    
    for inst in instruments:
        contracts = rm.calculate_position_size(
            stop_loss_ticks=inst['stop_ticks'],
            tick_value=inst['tick_value'],
            risk_dollars=200
        )
        risk = contracts * inst['stop_ticks'] * inst['tick_value']
        print(f"\n{inst['name']}:")
        print(f"  Contracts: {contracts}")
        print(f"  Total Risk: ${risk:.2f}")
    
    # Show current status
    rm.print_current_status()
    
    print("\n" + "="*80)
    print("To use this calculator:")
    print("1. Import: from topstep_risk_calculator import TopStepRiskManager")
    print("2. Create instance: rm = TopStepRiskManager()")
    print("3. Check if can trade: can_trade, reasons = rm.can_take_trade()")
    print("4. Calculate size: contracts = rm.calculate_position_size(stop_ticks, tick_value)")
    print("5. Record trade: rm.record_trade(pnl, 'ES', entry, exit, contracts)")
    print("6. End of day: rm.end_of_day_summary()")
    print("="*80)

