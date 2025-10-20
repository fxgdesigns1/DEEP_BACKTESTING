#!/usr/bin/env python3
"""
OANDA ECONOMIC CALENDAR ACCESS TEST
===================================

Test OANDA API access and check for economic calendar capabilities
"""

import requests
import json
import yaml
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_oanda_access():
    """Test OANDA API access and capabilities"""
    
    # Load configuration
    try:
        with open('config/settings.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        oanda_config = config['data_sources']['api_keys']['oanda']
        api_key = oanda_config['api_key']
        account_id = oanda_config['account_id']
        base_url = oanda_config['base_url']
        
        logger.info("✅ Configuration loaded successfully")
        
    except Exception as e:
        logger.error(f"❌ Error loading configuration: {e}")
        return False
    
    # Test basic OANDA API access
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Test 1: Account information
    logger.info("🔍 Testing OANDA account access...")
    try:
        url = f"{base_url}/v3/accounts/{account_id}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            account_data = response.json()
            logger.info("✅ OANDA account access successful")
            logger.info(f"   Account ID: {account_data['account']['id']}")
            logger.info(f"   Currency: {account_data['account']['currency']}")
            logger.info(f"   Balance: {account_data['account']['balance']}")
        else:
            logger.warning(f"⚠️ Account access failed: {response.status_code}")
            logger.warning(f"   Response: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Account access error: {e}")
    
    # Test 2: Available instruments
    logger.info("🔍 Testing OANDA instruments access...")
    try:
        url = f"{base_url}/v3/accounts/{account_id}/instruments"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            instruments_data = response.json()
            instruments = instruments_data['instruments']
            logger.info(f"✅ Instruments access successful - {len(instruments)} instruments available")
            
            # Show some forex pairs
            forex_pairs = [inst for inst in instruments if 'USD' in inst['name'] or 'EUR' in inst['name']][:5]
            for pair in forex_pairs:
                logger.info(f"   {pair['name']}: {pair['displayName']}")
        else:
            logger.warning(f"⚠️ Instruments access failed: {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ Instruments access error: {e}")
    
    # Test 3: Historical data access
    logger.info("🔍 Testing OANDA historical data access...")
    try:
        url = f"{base_url}/v3/instruments/EUR_USD/candles"
        params = {
            'price': 'M',
            'granularity': 'H1',
            'count': 5
        }
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            candles_data = response.json()
            candles = candles_data['candles']
            logger.info(f"✅ Historical data access successful - {len(candles)} candles retrieved")
            
            if candles:
                latest_candle = candles[-1]
                logger.info(f"   Latest EUR/USD: {latest_candle['mid']['c']} at {latest_candle['time']}")
        else:
            logger.warning(f"⚠️ Historical data access failed: {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ Historical data access error: {e}")
    
    # Test 4: Check for economic calendar endpoints
    logger.info("🔍 Testing OANDA economic calendar access...")
    
    # OANDA doesn't have a direct economic calendar API, but let's check what's available
    economic_endpoints = [
        f"{base_url}/v3/accounts/{account_id}/pricing",
        f"{base_url}/v3/accounts/{account_id}/transactions",
        f"{base_url}/v3/accounts/{account_id}/orders"
    ]
    
    available_endpoints = []
    for endpoint in economic_endpoints:
        try:
            response = requests.get(endpoint, headers=headers, timeout=5)
            if response.status_code in [200, 400]:  # 400 is OK for some endpoints
                available_endpoints.append(endpoint.split('/')[-1])
        except:
            pass
    
    logger.info(f"✅ Available OANDA endpoints: {', '.join(available_endpoints)}")
    
    # Test 5: Check for news or calendar endpoints
    logger.info("🔍 Checking for news/calendar endpoints...")
    
    # OANDA doesn't provide economic calendar data directly
    # But we can check if there are any news-related endpoints
    news_endpoints = [
        f"{base_url}/v3/accounts/{account_id}/news",
        f"{base_url}/v3/news",
        f"{base_url}/v3/calendar"
    ]
    
    for endpoint in news_endpoints:
        try:
            response = requests.get(endpoint, headers=headers, timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ Found news endpoint: {endpoint}")
            else:
                logger.info(f"❌ No news endpoint: {endpoint} (Status: {response.status_code})")
        except Exception as e:
            logger.info(f"❌ No news endpoint: {endpoint} (Error: {e})")
    
    return True

def check_oanda_limitations():
    """Check OANDA limitations for economic calendar data"""
    
    logger.info("📊 OANDA ECONOMIC CALENDAR ANALYSIS")
    logger.info("=" * 50)
    
    limitations = {
        'economic_calendar': {
            'available': False,
            'reason': 'OANDA does not provide economic calendar data through their API',
            'alternative': 'Use FRED, Alpha Vantage, or other economic data sources'
        },
        'news_data': {
            'available': False,
            'reason': 'OANDA does not provide news data through their API',
            'alternative': 'Use NewsData.io, MarketAux, or Alpha Vantage news'
        },
        'market_data': {
            'available': True,
            'reason': 'OANDA provides excellent forex market data',
            'capabilities': 'Historical prices, real-time quotes, order book data'
        },
        'account_data': {
            'available': True,
            'reason': 'OANDA provides account and trading data',
            'capabilities': 'Account info, positions, orders, transactions'
        }
    }
    
    for category, info in limitations.items():
        status = "✅" if info['available'] else "❌"
        logger.info(f"{status} {category.upper()}: {info['reason']}")
        if 'capabilities' in info:
            logger.info(f"   Capabilities: {info['capabilities']}")
        if 'alternative' in info:
            logger.info(f"   Alternative: {info['alternative']}")
        logger.info("")
    
    return limitations

def main():
    """Main execution function"""
    print("🏦 OANDA ECONOMIC CALENDAR ACCESS TEST")
    print("=" * 50)
    print("Testing your OANDA API access and economic calendar capabilities...")
    print()
    
    # Test OANDA access
    success = test_oanda_access()
    
    print()
    print("📊 OANDA CAPABILITIES ANALYSIS")
    print("=" * 40)
    
    # Check limitations
    limitations = check_oanda_limitations()
    
    print()
    print("🎯 RECOMMENDATIONS FOR FREE APPROACH")
    print("=" * 45)
    
    recommendations = [
        "✅ Use OANDA for high-quality forex market data (10,000 requests/day)",
        "❌ OANDA cannot provide economic calendar data",
        "✅ Use Alpha Vantage for economic indicators (500 requests/day)",
        "✅ Use FRED for official economic data (unlimited)",
        "⏰ Wait for NewsData.io limits to reset (100 requests/day)",
        "💰 Consider free alternatives: Yahoo Finance, Investing.com"
    ]
    
    for rec in recommendations:
        print(rec)
    
    print()
    print("📅 FREE APPROACH TIMELINE (UPDATED)")
    print("=" * 40)
    
    timeline = {
        "Day 1-2": "Alpha Vantage (500 requests/day) - Economic indicators",
        "Day 3-5": "FRED API (unlimited) - Official economic data", 
        "Day 6-8": "NewsData.io (100 requests/day) - News data",
        "Day 9-15": "Yahoo Finance (unlimited) - Market sentiment",
        "Day 16-25": "Comprehensive integration and validation"
    }
    
    for day, activity in timeline.items():
        print(f"{day}: {activity}")
    
    print()
    print("✅ OANDA TEST COMPLETE!")
    print("OANDA is excellent for market data but cannot provide economic calendar data.")
    print("Use the free approach with Alpha Vantage + FRED + NewsData.io for comprehensive coverage.")

if __name__ == "__main__":
    main()
