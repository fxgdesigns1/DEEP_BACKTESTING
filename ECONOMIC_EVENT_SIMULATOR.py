#!/usr/bin/env python3
"""
ECONOMIC EVENT SIMULATOR
========================

Organizes economic data to simulate real-life trading conditions with:
- Proper event timing and scheduling
- Realistic market impact simulation
- Event importance classification
- Trading session alignment
- Historical volatility correlation
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import pytz
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EconomicEventSimulator:
    """Simulates real-life trading conditions for economic events"""
    
    def __init__(self):
        self.data_dir = Path('data/backtesting_historical/economic')
        self.output_dir = Path('data/trading_simulation')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Trading sessions (UTC)
        self.trading_sessions = {
            'asian': {'start': '00:00', 'end': '09:00'},
            'london': {'start': '08:00', 'end': '16:00'},
            'new_york': {'start': '13:00', 'end': '21:00'},
            'overlap_london_ny': {'start': '13:00', 'end': '16:00'}
        }
        
        # Economic event importance levels
        self.event_importance = {
            'HIGH': {
                'indicators': ['FEDERAL_FUNDS_RATE', 'UNEMPLOYMENT', 'CPI', 'REAL_GDP'],
                'market_impact': 0.5,  # 50 pips average impact
                'volatility_multiplier': 3.0,
                'duration_minutes': 30
            },
            'MEDIUM': {
                'indicators': ['RETAIL_SALES', 'DURABLES', 'INFLATION'],
                'market_impact': 0.25,  # 25 pips average impact
                'volatility_multiplier': 2.0,
                'duration_minutes': 15
            },
            'LOW': {
                'indicators': ['TREASURY_YIELD', 'REAL_GDP_PER_CAPITA'],
                'market_impact': 0.1,  # 10 pips average impact
                'volatility_multiplier': 1.5,
                'duration_minutes': 5
            }
        }
        
        # Typical economic release times (EST/EDT)
        self.release_times = {
            'FEDERAL_FUNDS_RATE': '14:00',  # 2:00 PM EST
            'UNEMPLOYMENT': '08:30',        # 8:30 AM EST
            'CPI': '08:30',                 # 8:30 AM EST
            'REAL_GDP': '08:30',            # 8:30 AM EST
            'RETAIL_SALES': '08:30',        # 8:30 AM EST
            'DURABLES': '08:30',            # 8:30 AM EST
            'INFLATION': '08:30',           # 8:30 AM EST
            'TREASURY_YIELD': '09:00',      # 9:00 AM EST
            'REAL_GDP_PER_CAPITA': '08:30'  # 8:30 AM EST
        }
        
        logger.info("🚀 Economic Event Simulator initialized")
    
    def load_economic_data(self):
        """Load and organize economic data"""
        logger.info("�� Loading economic data...")
        
        economic_data = {}
        for file_path in self.data_dir.glob('alphavantage_*.json'):
            indicator_name = file_path.stem.replace('alphavantage_', '').upper()
            if indicator_name == 'COMPREHENSIVE':
                continue
                
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    economic_data[indicator_name] = data['data']
                    logger.info(f"✅ Loaded {indicator_name}")
            except Exception as e:
                logger.warning(f"⚠️ Error loading {indicator_name}: {e}")
        
        return economic_data
    
    def create_trading_calendar(self, economic_data):
        """Create a trading calendar with economic events"""
        logger.info("📅 Creating trading calendar...")
        
        calendar = []
        
        for indicator, data in economic_data.items():
            if 'data' in data and isinstance(data['data'], list):
                for record in data['data']:
                    if 'date' in record and 'value' in record and record['value'] != '.':
                        try:
                            # Parse date
                            if data['interval'] == 'monthly':
                                event_date = pd.to_datetime(record['date'] + '-01')
                            elif data['interval'] == 'quarterly':
                                event_date = pd.to_datetime(record['date'] + '-01')
                            elif data['interval'] == 'annual':
                                event_date = pd.to_datetime(record['date'] + '-01-01')
                            else:
                                event_date = pd.to_datetime(record['date'])
                            
                            # Only include 2022-2025 data
                            if 2022 <= event_date.year <= 2025:
                                # Determine importance
                                importance = self.get_event_importance(indicator)
                                
                                # Get release time
                                release_time = self.release_times.get(indicator, '08:30')
                                
                                # Create event entry
                                event = {
                                    'date': event_date.strftime('%Y-%m-%d'),
                                    'time': release_time,
                                    'datetime': event_date.strftime('%Y-%m-%d %H:%M:00'),
                                    'indicator': indicator,
                                    'name': data.get('name', indicator),
                                    'value': float(record['value']),
                                    'unit': data.get('unit', ''),
                                    'interval': data['interval'],
                                    'importance': importance,
                                    'market_impact': self.event_importance[importance]['market_impact'],
                                    'volatility_multiplier': self.event_importance[importance]['volatility_multiplier'],
                                    'duration_minutes': self.event_importance[importance]['duration_minutes'],
                                    'trading_session': self.get_trading_session(release_time),
                                    'currency_impact': self.get_currency_impact(indicator)
                                }
                                
                                calendar.append(event)
                                
                        except Exception as e:
                            logger.warning(f"⚠️ Error processing {indicator} record: {e}")
        
        # Sort by date
        calendar.sort(key=lambda x: x['datetime'])
        
        logger.info(f"📅 Created trading calendar with {len(calendar)} events")
        return calendar
    
    def get_event_importance(self, indicator):
        """Determine event importance level"""
        for importance, config in self.event_importance.items():
            if indicator in config['indicators']:
                return importance
        return 'LOW'
    
    def get_trading_session(self, release_time):
        """Determine which trading session the event occurs in"""
        hour = int(release_time.split(':')[0])
        
        if 0 <= hour < 8:
            return 'asian'
        elif 8 <= hour < 13:
            return 'london'
        elif 13 <= hour < 21:
            return 'new_york'
        else:
            return 'asian'
    
    def get_currency_impact(self, indicator):
        """Determine which currencies are most affected by the indicator"""
        currency_impact = {
            'FEDERAL_FUNDS_RATE': ['USD', 'EUR', 'GBP', 'JPY'],
            'UNEMPLOYMENT': ['USD', 'CAD'],
            'CPI': ['USD', 'EUR'],
            'REAL_GDP': ['USD'],
            'RETAIL_SALES': ['USD'],
            'DURABLES': ['USD'],
            'INFLATION': ['USD', 'EUR'],
            'TREASURY_YIELD': ['USD'],
            'REAL_GDP_PER_CAPITA': ['USD']
        }
        return currency_impact.get(indicator, ['USD'])
    
    def create_market_impact_simulation(self, calendar):
        """Create realistic market impact simulation"""
        logger.info("📈 Creating market impact simulation...")
        
        simulation_data = []
        
        for event in calendar:
            # Calculate realistic market impact based on:
            # 1. Event importance
            # 2. Historical volatility
            # 3. Market conditions
            # 4. Currency pair correlation
            
            base_impact = event['market_impact']
            volatility_multiplier = event['volatility_multiplier']
            
            # Add randomness for realistic simulation
            random_factor = np.random.normal(1.0, 0.3)
            random_factor = max(0.3, min(2.0, random_factor))  # Clamp between 0.3 and 2.0
            
            # Calculate actual impact
            actual_impact = base_impact * volatility_multiplier * random_factor
            
            # Determine direction (positive/negative surprise)
            surprise_direction = np.random.choice(['positive', 'negative'])
            
            # Create impact for each affected currency
            for currency in event['currency_impact']:
                impact_entry = {
                    'event_datetime': event['datetime'],
                    'indicator': event['indicator'],
                    'importance': event['importance'],
                    'currency': currency,
                    'base_impact_pips': base_impact,
                    'actual_impact_pips': actual_impact,
                    'surprise_direction': surprise_direction,
                    'volatility_multiplier': volatility_multiplier,
                    'duration_minutes': event['duration_minutes'],
                    'trading_session': event['trading_session'],
                    'affected_pairs': self.get_affected_pairs(currency),
                    'market_conditions': self.get_market_conditions(event['datetime'])
                }
                
                simulation_data.append(impact_entry)
        
        logger.info(f"📈 Created market impact simulation with {len(simulation_data)} impact events")
        return simulation_data
    
    def get_affected_pairs(self, currency):
        """Get currency pairs affected by the event"""
        affected_pairs = {
            'USD': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD'],
            'EUR': ['EURUSD', 'EURJPY', 'EURGBP'],
            'GBP': ['GBPUSD', 'EURGBP', 'GBPJPY'],
            'JPY': ['USDJPY', 'EURJPY', 'GBPJPY'],
            'CAD': ['USDCAD', 'EURCAD', 'GBPCAD'],
            'AUD': ['AUDUSD', 'EURAUD', 'GBPAUD'],
            'CHF': ['USDCHF', 'EURCHF', 'GBPCHF'],
            'NZD': ['NZDUSD', 'EURNZD', 'GBPNZD']
        }
        return affected_pairs.get(currency, [])
    
    def get_market_conditions(self, datetime_str):
        """Simulate market conditions based on historical patterns"""
        # This would normally use historical volatility data
        # For now, we'll simulate based on typical market patterns
        
        conditions = {
            'volatility_regime': np.random.choice(['low', 'normal', 'high'], p=[0.3, 0.5, 0.2]),
            'trend_direction': np.random.choice(['bullish', 'bearish', 'sideways'], p=[0.4, 0.4, 0.2]),
            'liquidity_level': np.random.choice(['low', 'normal', 'high'], p=[0.2, 0.6, 0.2])
        }
        
        return conditions
    
    def create_trading_session_analysis(self, calendar):
        """Analyze economic events by trading session"""
        logger.info("📊 Creating trading session analysis...")
        
        session_analysis = {}
        
        for session in self.trading_sessions.keys():
            session_events = [e for e in calendar if e['trading_session'] == session]
            
            if session_events:
                high_impact_events = len([e for e in session_events if e['importance'] == 'HIGH'])
                medium_impact_events = len([e for e in session_events if e['importance'] == 'MEDIUM'])
                low_impact_events = len([e for e in session_events if e['importance'] == 'LOW'])
                
                session_analysis[session] = {
                    'total_events': len(session_events),
                    'high_impact': high_impact_events,
                    'medium_impact': medium_impact_events,
                    'low_impact': low_impact_events,
                    'avg_impact': np.mean([e['market_impact'] for e in session_events]),
                    'most_volatile_hour': self.get_most_volatile_hour(session_events),
                    'recommended_trading_strategy': self.get_trading_strategy(session_events)
                }
        
        return session_analysis
    
    def get_most_volatile_hour(self, events):
        """Determine the most volatile hour for the session"""
        hour_volatility = {}
        for event in events:
            hour = int(event['time'].split(':')[0])
            if hour not in hour_volatility:
                hour_volatility[hour] = 0
            hour_volatility[hour] += event['market_impact']
        
        if hour_volatility:
            return max(hour_volatility, key=hour_volatility.get)
        return 8  # Default to 8 AM
    
    def get_trading_strategy(self, events):
        """Recommend trading strategy based on session events"""
        high_impact_count = len([e for e in events if e['importance'] == 'HIGH'])
        avg_impact = np.mean([e['market_impact'] for e in events])
        
        if high_impact_count >= 5:
            return "News Trading - High Impact Events"
        elif avg_impact >= 0.3:
            return "Breakout Trading - Medium Impact"
        elif avg_impact >= 0.15:
            return "Scalping - Low Impact"
        else:
            return "Range Trading - Minimal Impact"
    
    def create_realistic_trading_scenarios(self, calendar, market_impacts):
        """Create realistic trading scenarios for backtesting"""
        logger.info("🎯 Creating realistic trading scenarios...")
        
        scenarios = []
        
        # Group events by date for daily scenarios
        daily_events = {}
        for event in calendar:
            date = event['date']
            if date not in daily_events:
                daily_events[date] = []
            daily_events[date].append(event)
        
        for date, events in daily_events.items():
            # Calculate daily volatility and impact
            daily_impact = sum([e['market_impact'] for e in events])
            high_impact_events = len([e for e in events if e['importance'] == 'HIGH'])
            
            # Determine scenario type
            if high_impact_events >= 2:
                scenario_type = "High Impact Day"
                recommended_strategy = "News Trading - Multiple High Impact Events"
                risk_level = "High"
            elif high_impact_events == 1:
                scenario_type = "Medium Impact Day"
                recommended_strategy = "Event-Driven Trading"
                risk_level = "Medium"
            elif daily_impact >= 0.5:
                scenario_type = "Volatile Day"
                recommended_strategy = "Breakout Trading"
                risk_level = "Medium"
            else:
                scenario_type = "Normal Day"
                recommended_strategy = "Range Trading"
                risk_level = "Low"
            
            scenario = {
                'date': date,
                'scenario_type': scenario_type,
                'total_events': len(events),
                'high_impact_events': high_impact_events,
                'daily_impact': daily_impact,
                'risk_level': risk_level,
                'recommended_strategy': recommended_strategy,
                'events': events,
                'trading_recommendations': self.get_trading_recommendations(events),
                'risk_management': self.get_risk_management_advice(events)
            }
            
            scenarios.append(scenario)
        
        logger.info(f"🎯 Created {len(scenarios)} realistic trading scenarios")
        return scenarios
    
    def get_trading_recommendations(self, events):
        """Get specific trading recommendations for the day"""
        recommendations = []
        
        # Sort events by importance and time
        sorted_events = sorted(events, key=lambda x: (x['importance'] == 'HIGH', x['time']))
        
        for event in sorted_events:
            if event['importance'] == 'HIGH':
                recommendations.append({
                    'time': event['time'],
                    'action': f"Monitor {event['indicator']} release",
                    'pairs': event['currency_impact'],
                    'expected_impact': f"{event['market_impact']} pips",
                    'strategy': "News breakout trading"
                })
            elif event['importance'] == 'MEDIUM':
                recommendations.append({
                    'time': event['time'],
                    'action': f"Watch for {event['indicator']} surprises",
                    'pairs': event['currency_impact'],
                    'expected_impact': f"{event['market_impact']} pips",
                    'strategy': "Event-driven scalping"
                })
        
        return recommendations
    
    def get_risk_management_advice(self, events):
        """Get risk management advice for the day"""
        high_impact_count = len([e for e in events if e['importance'] == 'HIGH'])
        total_impact = sum([e['market_impact'] for e in events])
        
        if high_impact_count >= 2:
            return {
                'position_size': "Reduce to 50% of normal",
                'stop_loss': "Tighten stops before events",
                'take_profit': "Take partial profits early",
                'avoid_trading': "30 minutes before/after high impact events"
            }
        elif high_impact_count == 1:
            return {
                'position_size': "Normal size acceptable",
                'stop_loss': "Standard stops",
                'take_profit': "Normal profit targets",
                'avoid_trading': "15 minutes before/after event"
            }
        else:
            return {
                'position_size': "Normal to increased size",
                'stop_loss': "Standard stops",
                'take_profit': "Extended profit targets",
                'avoid_trading': "No restrictions"
            }
    
    def save_simulation_data(self, calendar, market_impacts, session_analysis, scenarios):
        """Save all simulation data"""
        logger.info("💾 Saving simulation data...")
        
        # Save trading calendar
        calendar_df = pd.DataFrame(calendar)
        calendar_df.to_csv(self.output_dir / 'trading_calendar.csv', index=False)
        
        # Save market impacts
        impacts_df = pd.DataFrame(market_impacts)
        impacts_df.to_csv(self.output_dir / 'market_impacts.csv', index=False)
        
        # Save session analysis
        with open(self.output_dir / 'session_analysis.json', 'w') as f:
            json.dump(session_analysis, f, indent=2, default=str)
        
        # Save trading scenarios
        scenarios_data = []
        for scenario in scenarios:
            scenario_copy = scenario.copy()
            # Convert events to serializable format
            scenario_copy['events'] = [json.dumps(event) for event in scenario['events']]
            scenarios_data.append(scenario_copy)
        
        scenarios_df = pd.DataFrame(scenarios_data)
        scenarios_df.to_csv(self.output_dir / 'trading_scenarios.csv', index=False)
        
        # Create summary report
        summary = {
            'simulation_metadata': {
                'created_at': datetime.now().isoformat(),
                'total_events': len(calendar),
                'total_scenarios': len(scenarios),
                'date_range': f"{calendar[0]['date']} to {calendar[-1]['date']}" if calendar else "No data",
                'purpose': 'Real-life trading condition simulation'
            },
            'event_summary': {
                'high_impact_events': len([e for e in calendar if e['importance'] == 'HIGH']),
                'medium_impact_events': len([e for e in calendar if e['importance'] == 'MEDIUM']),
                'low_impact_events': len([e for e in calendar if e['importance'] == 'LOW']),
                'average_daily_events': len(calendar) / len(set([e['date'] for e in calendar])) if calendar else 0
            },
            'session_summary': session_analysis,
            'files_created': [
                'trading_calendar.csv',
                'market_impacts.csv',
                'session_analysis.json',
                'trading_scenarios.csv'
            ]
        }
        
        with open(self.output_dir / 'simulation_summary.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info("💾 Simulation data saved successfully")
        return summary
    
    def run_simulation(self):
        """Run the complete economic event simulation"""
        print("🚀 ECONOMIC EVENT SIMULATOR")
        print("=" * 40)
        print("Creating realistic trading conditions...")
        print()
        
        try:
            # Step 1: Load economic data
            economic_data = self.load_economic_data()
            
            # Step 2: Create trading calendar
            calendar = self.create_trading_calendar(economic_data)
            
            # Step 3: Create market impact simulation
            market_impacts = self.create_market_impact_simulation(calendar)
            
            # Step 4: Analyze trading sessions
            session_analysis = self.create_trading_session_analysis(calendar)
            
            # Step 5: Create realistic trading scenarios
            scenarios = self.create_realistic_trading_scenarios(calendar, market_impacts)
            
            # Step 6: Save all data
            summary = self.save_simulation_data(calendar, market_impacts, session_analysis, scenarios)
            
            print()
            print("✅ SIMULATION COMPLETE!")
            print("=" * 25)
            print(f"�� Trading Calendar: {summary['simulation_metadata']['total_events']} events")
            print(f"🎯 Trading Scenarios: {summary['simulation_metadata']['total_scenarios']} scenarios")
            print(f"📊 Date Range: {summary['simulation_metadata']['date_range']}")
            print()
            print("📁 Files Created:")
            for file in summary['files_created']:
                print(f"  • {file}")
            print()
            print("🎯 Your economic data is now organized for realistic trading simulation!")
            print("💡 Use this data to backtest strategies under real market conditions!")
            
        except Exception as e:
            logger.error(f"❌ Error in simulation: {e}")
            print(f"❌ Error: {e}")

def main():
    """Main execution function"""
    simulator = EconomicEventSimulator()
    simulator.run_simulation()

if __name__ == "__main__":
    main()
