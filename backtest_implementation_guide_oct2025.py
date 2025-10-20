#!/usr/bin/env python3
"""
Backtesting Implementation Guide - October 2025
Based on Live Trading System Improvements

This script provides ready-to-use implementations for:
1. Dynamic spread modeling
2. Multi-timeframe analysis
3. News event integration
4. Signal quality scoring
5. Session-based filtering

Author: AI Trading System
Date: October 1, 2025
Version: 2.1.0
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# 1. DYNAMIC SPREAD MODELING
# ============================================================================

class TradingSession(Enum):
    """Trading session types"""
    LONDON = "london"
    NY = "ny"
    LONDON_NY_OVERLAP = "london_ny_overlap"
    ASIAN = "asian"
    WEEKEND = "weekend"


@dataclass
class SpreadConfig:
    """Spread configuration for an instrument"""
    base_spread: float
    session_multipliers: Dict[TradingSession, float]
    volatility_sensitive: bool = True
    news_sensitive: bool = True


class DynamicSpreadModel:
    """
    Dynamic spread modeling based on:
    - Trading session
    - Market volatility
    - News events
    
    Example Usage:
    >>> spread_model = DynamicSpreadModel()
    >>> spread_model.set_base_spread('EUR_USD', 0.8)
    >>> current_spread = spread_model.get_spread(
    ...     instrument='EUR_USD',
    ...     timestamp=datetime.now(),
    ...     volatility=0.00025,
    ...     news_events=[]
    ... )
    """
    
    def __init__(self):
        self.base_spreads: Dict[str, float] = {}
        self.session_multipliers = {
            TradingSession.LONDON: 1.0,
            TradingSession.NY: 1.0,
            TradingSession.LONDON_NY_OVERLAP: 0.8,  # Tightest
            TradingSession.ASIAN: 2.5,  # Widest
            TradingSession.WEEKEND: 5.0  # Very wide
        }
    
    def set_base_spread(self, instrument: str, base_spread: float):
        """Set base spread for instrument (in pips)"""
        self.base_spreads[instrument] = base_spread
    
    def get_session(self, timestamp: datetime) -> TradingSession:
        """Determine trading session from UTC timestamp"""
        hour = timestamp.hour
        
        # London/NY overlap: 13:00-16:00 UTC (best liquidity)
        if 13 <= hour < 16:
            return TradingSession.LONDON_NY_OVERLAP
        
        # London: 7:00-16:00 UTC
        elif 7 <= hour < 16:
            return TradingSession.LONDON
        
        # NY: 13:00-22:00 UTC
        elif 13 <= hour < 22:
            return TradingSession.NY
        
        # Asian: 0:00-9:00 UTC
        elif 0 <= hour < 9:
            return TradingSession.ASIAN
        
        # Weekend/off hours
        else:
            return TradingSession.WEEKEND if timestamp.weekday() >= 5 else TradingSession.ASIAN
    
    def get_spread(self, 
                   instrument: str, 
                   timestamp: datetime,
                   volatility: Optional[float] = None,
                   news_events: Optional[List] = None) -> float:
        """
        Calculate dynamic spread for instrument at timestamp
        
        Args:
            instrument: e.g., 'EUR_USD', 'XAU_USD'
            timestamp: UTC timestamp
            volatility: Current volatility (optional)
            news_events: List of nearby news events (optional)
        
        Returns:
            Spread in pips
        """
        # Get base spread
        if instrument not in self.base_spreads:
            # Default spreads if not configured
            defaults = {
                'EUR_USD': 0.8, 'GBP_USD': 1.2, 'USD_JPY': 0.9,
                'AUD_USD': 1.0, 'XAU_USD': 0.50
            }
            base_spread = defaults.get(instrument, 1.0)
        else:
            base_spread = self.base_spreads[instrument]
        
        # Apply session multiplier
        session = self.get_session(timestamp)
        session_mult = self.session_multipliers[session]
        
        # Apply volatility multiplier
        volatility_mult = 1.0
        if volatility is not None:
            # Higher volatility = wider spreads
            volatility_mult = 1.0 + (volatility * 1000)  # Scale factor
        
        # Apply news multiplier
        news_mult = 1.0
        if news_events:
            for event in news_events:
                time_to_event = abs((event['timestamp'] - timestamp).total_seconds())
                if time_to_event <= 1800:  # Within 30 minutes
                    if event['impact'] == 'high':
                        news_mult = max(news_mult, 5.0)
                    elif event['impact'] == 'medium':
                        news_mult = max(news_mult, 2.0)
        
        # Calculate final spread
        final_spread = base_spread * session_mult * volatility_mult * news_mult
        
        return final_spread


# ============================================================================
# 2. MULTI-TIMEFRAME ANALYSIS
# ============================================================================

class TimeframeAnalyzer:
    """
    Multi-timeframe trend detection
    
    Example Usage:
    >>> analyzer = TimeframeAnalyzer()
    >>> trend = analyzer.get_higher_timeframe_trend(
    ...     prices_1h=hourly_closes,
    ...     prices_4h=four_hour_closes,
    ...     lookback=50
    ... )
    >>> if trend == 'BUY':
    ...     # Only take BUY signals
    ...     pass
    """
    
    def __init__(self):
        self.ema_long_period = 50
        self.ema_short_period = 20
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate EMA for given period"""
        if len(prices) < period:
            return prices[-1] if prices else 0.0
        
        series = pd.Series(prices)
        ema = series.ewm(span=period, adjust=False).mean()
        return float(ema.iloc[-1])
    
    def get_higher_timeframe_trend(self, 
                                    prices: List[float],
                                    lookback: int = 50) -> str:
        """
        Determine higher timeframe trend
        
        Args:
            prices: Price history for higher timeframe
            lookback: Number of bars to analyze
        
        Returns:
            'BUY', 'SELL', or 'NEUTRAL'
        """
        if len(prices) < lookback:
            return 'NEUTRAL'
        
        # Calculate EMAs
        long_ema = self.calculate_ema(prices, self.ema_long_period)
        short_ema = self.calculate_ema(prices, self.ema_short_period)
        current_price = prices[-1]
        
        # Determine trend
        if current_price > long_ema and short_ema > long_ema:
            return 'BUY'  # Uptrend
        elif current_price < long_ema and short_ema < long_ema:
            return 'SELL'  # Downtrend
        else:
            return 'NEUTRAL'  # Ranging/unclear
    
    def check_multi_timeframe_alignment(self,
                                        signal_direction: str,
                                        prices_15min: List[float],
                                        prices_1hour: List[float],
                                        prices_4hour: List[float]) -> bool:
        """
        Check if signal aligns with higher timeframes
        
        Args:
            signal_direction: 'BUY' or 'SELL'
            prices_15min: 15-minute prices
            prices_1hour: 1-hour prices
            prices_4hour: 4-hour prices
        
        Returns:
            True if aligned, False otherwise
        """
        # Get 1-hour trend
        trend_1h = self.get_higher_timeframe_trend(prices_1hour, lookback=50)
        
        # Get 4-hour trend
        trend_4h = self.get_higher_timeframe_trend(prices_4hour, lookback=50)
        
        # Signal must align with at least 1-hour trend
        if signal_direction != trend_1h:
            return False
        
        # Bonus: Also aligns with 4-hour (strongest signal)
        if signal_direction == trend_4h:
            return True
        
        # Acceptable: 4-hour is NEUTRAL
        if trend_4h == 'NEUTRAL':
            return True
        
        return False


# ============================================================================
# 3. NEWS EVENT INTEGRATION
# ============================================================================

@dataclass
class NewsEvent:
    """News event data structure"""
    timestamp: datetime
    event_type: str  # e.g., 'NFP', 'CPI', 'Fed Rate Decision'
    currency: str  # e.g., 'USD', 'EUR'
    impact: str  # 'high', 'medium', 'low'
    actual: Optional[float] = None
    forecast: Optional[float] = None
    previous: Optional[float] = None
    
    def surprise_factor(self) -> float:
        """Calculate surprise (deviation from forecast)"""
        if self.actual is None or self.forecast is None or self.forecast == 0:
            return 0.0
        return (self.actual - self.forecast) / abs(self.forecast)


class NewsIntegration:
    """
    News-aware trading decisions
    
    Example Usage:
    >>> news = NewsIntegration()
    >>> news.add_event(NewsEvent(
    ...     timestamp=datetime(2025, 10, 1, 14, 30),
    ...     event_type='NFP',
    ...     currency='USD',
    ...     impact='high'
    ... ))
    >>> should_pause = news.should_pause_trading(
    ...     current_time=datetime(2025, 10, 1, 14, 15),
    ...     instruments=['EUR_USD', 'GBP_USD']
    ... )
    """
    
    def __init__(self):
        self.events: List[NewsEvent] = []
        self.pause_before_minutes = 30
        self.pause_after_minutes = 30
    
    def add_event(self, event: NewsEvent):
        """Add news event to calendar"""
        self.events.append(event)
    
    def load_events_from_csv(self, filepath: str):
        """Load events from CSV file"""
        df = pd.read_csv(filepath)
        for _, row in df.iterrows():
            event = NewsEvent(
                timestamp=pd.to_datetime(row['timestamp']),
                event_type=row['event_type'],
                currency=row['currency'],
                impact=row['impact'],
                actual=row.get('actual'),
                forecast=row.get('forecast'),
                previous=row.get('previous')
            )
            self.add_event(event)
    
    def should_pause_trading(self,
                            current_time: datetime,
                            instruments: List[str]) -> bool:
        """
        Check if trading should be paused due to news
        
        Args:
            current_time: Current timestamp
            instruments: List of instruments being traded
        
        Returns:
            True if should pause, False otherwise
        """
        # Extract currencies from instruments
        currencies = set()
        for inst in instruments:
            # e.g., 'EUR_USD' -> ['EUR', 'USD']
            parts = inst.split('_')
            currencies.update(parts)
        
        # Check each high-impact event
        for event in self.events:
            if event.impact != 'high':
                continue
            
            # Check if event affects our currencies
            if event.currency not in currencies:
                continue
            
            # Calculate time to event
            time_to_event = (event.timestamp - current_time).total_seconds()
            
            # Pause if within window
            pause_before = self.pause_before_minutes * 60
            pause_after = self.pause_after_minutes * 60
            
            if -pause_after <= time_to_event <= pause_before:
                return True
        
        return False
    
    def get_news_sentiment(self,
                          current_time: datetime,
                          instrument: str,
                          lookback_hours: int = 24) -> float:
        """
        Calculate news sentiment for instrument
        
        Args:
            current_time: Current timestamp
            instrument: e.g., 'EUR_USD'
            lookback_hours: Hours to look back
        
        Returns:
            Sentiment score: -1.0 (bearish) to +1.0 (bullish)
        """
        # Extract currencies
        currencies = instrument.split('_')
        
        # Find relevant events
        relevant_events = []
        lookback = timedelta(hours=lookback_hours)
        
        for event in self.events:
            if event.currency not in currencies:
                continue
            
            time_diff = current_time - event.timestamp
            if timedelta(0) <= time_diff <= lookback:
                relevant_events.append(event)
        
        if not relevant_events:
            return 0.0  # Neutral
        
        # Calculate aggregate sentiment
        sentiments = []
        for event in relevant_events:
            surprise = event.surprise_factor()
            
            # Positive surprise = bullish for currency
            # Weight by impact
            weight = {'high': 3.0, 'medium': 2.0, 'low': 1.0}.get(event.impact, 1.0)
            sentiments.append(surprise * weight)
        
        # Average sentiment
        avg_sentiment = np.mean(sentiments) if sentiments else 0.0
        
        # Normalize to -1 to 1
        return max(min(avg_sentiment, 1.0), -1.0)


# ============================================================================
# 4. SIGNAL QUALITY SCORING
# ============================================================================

class SignalQualityScorer:
    """
    Score signal quality on multiple dimensions
    
    Example Usage:
    >>> scorer = SignalQualityScorer()
    >>> score, breakdown = scorer.score_signal(
    ...     signal_direction='BUY',
    ...     ema_aligned=True,
    ...     momentum_confirmed=True,
    ...     htf_aligned=True,
    ...     is_pullback_entry=True,
    ...     spread=0.7,
    ...     max_spread=1.0,
    ...     in_high_volume_session=True,
    ...     news_sentiment=0.25
    ... )
    >>> print(f"Signal quality: {score}/100")
    >>> print(f"Breakdown: {breakdown}")
    """
    
    def score_signal(self,
                    signal_direction: str,
                    ema_aligned: bool,
                    momentum_confirmed: bool,
                    htf_aligned: bool,
                    is_pullback_entry: bool,
                    spread: float,
                    max_spread: float,
                    in_high_volume_session: bool,
                    news_sentiment: float = 0.0) -> Tuple[int, Dict[str, int]]:
        """
        Calculate comprehensive signal quality score
        
        Returns:
            Tuple of (total_score, score_breakdown)
            total_score: 0-100
            score_breakdown: Dict of component scores
        """
        scores = {}
        
        # 1. Multi-timeframe alignment (0-25 points)
        if htf_aligned:
            scores['timeframe_alignment'] = 25
        else:
            scores['timeframe_alignment'] = 0  # Counter-trend = fail
        
        # 2. Technical strength (0-25 points)
        if ema_aligned and momentum_confirmed:
            scores['technical'] = 25
        elif ema_aligned or momentum_confirmed:
            scores['technical'] = 15
        else:
            scores['technical'] = 5
        
        # 3. Entry timing (0-25 points)
        if is_pullback_entry:
            scores['timing'] = 25  # Perfect pullback
        else:
            scores['timing'] = 10  # Random/breakout entry
        
        # 4. Market conditions (0-25 points)
        spread_score = 0
        if spread <= max_spread * 0.8:
            spread_score = 15  # Excellent spread
        elif spread <= max_spread:
            spread_score = 10  # Acceptable spread
        else:
            spread_score = 0  # Too wide
        
        session_score = 10 if in_high_volume_session else 0
        scores['conditions'] = spread_score + session_score
        
        # 5. News sentiment alignment (bonus: -10 to +10)
        news_score = 0
        if signal_direction == 'BUY':
            if news_sentiment > 0.3:
                news_score = 10  # Strong bullish news
            elif news_sentiment > 0.1:
                news_score = 5  # Moderate bullish
            elif news_sentiment < -0.1:
                news_score = -10  # Bearish news (against BUY)
        else:  # SELL
            if news_sentiment < -0.3:
                news_score = 10  # Strong bearish news
            elif news_sentiment < -0.1:
                news_score = 5  # Moderate bearish
            elif news_sentiment > 0.1:
                news_score = -10  # Bullish news (against SELL)
        
        scores['news_bonus'] = news_score
        
        # Total score
        total = sum(scores.values())
        total = max(0, min(100, total))  # Clamp to 0-100
        
        return total, scores


# ============================================================================
# 5. SESSION-BASED FILTERING
# ============================================================================

class SessionFilter:
    """
    Filter trades by session quality
    
    Example Usage:
    >>> session_filter = SessionFilter()
    >>> should_trade = session_filter.should_trade_now(
    ...     timestamp=datetime.now(),
    ...     instrument='XAU_USD',
    ...     strategy='gold_scalping'
    ... )
    """
    
    def __init__(self):
        # Define session rules per strategy
        self.session_rules = {
            'gold_scalping': ['london', 'ny', 'london_ny_overlap'],
            'ultra_strict_forex': ['london', 'ny', 'london_ny_overlap'],
            'momentum_trading': ['london', 'ny', 'london_ny_overlap', 'asian']
        }
    
    def get_session(self, timestamp: datetime) -> str:
        """Get current trading session"""
        hour = timestamp.hour
        
        if 13 <= hour < 16:
            return 'london_ny_overlap'
        elif 7 <= hour < 16:
            return 'london'
        elif 13 <= hour < 22:
            return 'ny'
        elif 0 <= hour < 9:
            return 'asian'
        else:
            return 'off_hours'
    
    def should_trade_now(self,
                        timestamp: datetime,
                        instrument: str,
                        strategy: str) -> bool:
        """
        Check if should trade this instrument now
        
        Args:
            timestamp: Current time
            instrument: e.g., 'EUR_USD'
            strategy: Strategy name
        
        Returns:
            True if should trade, False otherwise
        """
        # Get current session
        session = self.get_session(timestamp)
        
        # Check if strategy allows trading this session
        allowed_sessions = self.session_rules.get(strategy, ['london', 'ny'])
        
        if session not in allowed_sessions:
            return False
        
        # Weekend check
        if timestamp.weekday() >= 5:  # Saturday or Sunday
            return False
        
        return True
    
    def get_session_quality(self, timestamp: datetime) -> float:
        """
        Get session quality score (0-1)
        
        Returns:
            1.0 = Best (London/NY overlap)
            0.8 = Good (London or NY)
            0.5 = Fair (Asian)
            0.2 = Poor (off hours)
        """
        session = self.get_session(timestamp)
        
        quality_scores = {
            'london_ny_overlap': 1.0,
            'london': 0.8,
            'ny': 0.8,
            'asian': 0.5,
            'off_hours': 0.2
        }
        
        return quality_scores.get(session, 0.2)


# ============================================================================
# 6. COMPLETE BACKTEST SIGNAL VALIDATOR
# ============================================================================

class BacktestSignalValidator:
    """
    Complete signal validation for backtesting
    Combines all quality checks
    
    Example Usage:
    >>> validator = BacktestSignalValidator()
    >>> should_enter, quality_score, reasons = validator.validate_entry(
    ...     signal_direction='BUY',
    ...     instrument='EUR_USD',
    ...     timestamp=datetime.now(),
    ...     prices_15min=price_history_15m,
    ...     prices_1hour=price_history_1h,
    ...     prices_4hour=price_history_4h,
    ...     ema_aligned=True,
    ...     momentum_confirmed=True,
    ...     is_pullback_entry=True,
    ...     strategy='ultra_strict_forex'
    ... )
    """
    
    def __init__(self):
        self.spread_model = DynamicSpreadModel()
        self.timeframe_analyzer = TimeframeAnalyzer()
        self.news_integration = NewsIntegration()
        self.quality_scorer = SignalQualityScorer()
        self.session_filter = SessionFilter()
        
        # Minimum quality thresholds
        self.min_quality_score = 60  # Out of 100
    
    def validate_entry(self,
                      signal_direction: str,
                      instrument: str,
                      timestamp: datetime,
                      prices_15min: List[float],
                      prices_1hour: List[float],
                      prices_4hour: List[float],
                      ema_aligned: bool,
                      momentum_confirmed: bool,
                      is_pullback_entry: bool,
                      strategy: str,
                      volatility: Optional[float] = None) -> Tuple[bool, int, Dict]:
        """
        Validate trade entry signal
        
        Returns:
            Tuple of (should_enter, quality_score, rejection_reasons)
        """
        rejection_reasons = {}
        
        # 1. Check multi-timeframe alignment
        htf_aligned = self.timeframe_analyzer.check_multi_timeframe_alignment(
            signal_direction=signal_direction,
            prices_15min=prices_15min,
            prices_1hour=prices_1hour,
            prices_4hour=prices_4hour
        )
        
        if not htf_aligned:
            rejection_reasons['htf_alignment'] = "Counter-trend to higher timeframe"
        
        # 2. Check session
        should_trade_session = self.session_filter.should_trade_now(
            timestamp=timestamp,
            instrument=instrument,
            strategy=strategy
        )
        
        if not should_trade_session:
            rejection_reasons['session'] = "Outside allowed trading sessions"
        
        # 3. Check news events
        should_pause_news = self.news_integration.should_pause_trading(
            current_time=timestamp,
            instruments=[instrument]
        )
        
        if should_pause_news:
            rejection_reasons['news'] = "High-impact news event nearby"
        
        # 4. Calculate spread
        spread = self.spread_model.get_spread(
            instrument=instrument,
            timestamp=timestamp,
            volatility=volatility,
            news_events=[e for e in self.news_integration.events 
                        if abs((e.timestamp - timestamp).total_seconds()) <= 3600]
        )
        
        # Get max allowed spread (instrument-specific)
        max_spreads = {
            'EUR_USD': 1.5, 'GBP_USD': 2.0, 'USD_JPY': 1.5,
            'AUD_USD': 1.8, 'XAU_USD': 1.0
        }
        max_spread = max_spreads.get(instrument, 2.0)
        
        if spread > max_spread:
            rejection_reasons['spread'] = f"Spread too wide: {spread:.2f} > {max_spread:.2f}"
        
        # 5. Calculate signal quality score
        in_high_volume_session = self.session_filter.get_session_quality(timestamp) >= 0.8
        news_sentiment = self.news_integration.get_news_sentiment(
            current_time=timestamp,
            instrument=instrument
        )
        
        quality_score, score_breakdown = self.quality_scorer.score_signal(
            signal_direction=signal_direction,
            ema_aligned=ema_aligned,
            momentum_confirmed=momentum_confirmed,
            htf_aligned=htf_aligned,
            is_pullback_entry=is_pullback_entry,
            spread=spread,
            max_spread=max_spread,
            in_high_volume_session=in_high_volume_session,
            news_sentiment=news_sentiment
        )
        
        # 6. Make final decision
        should_enter = (
            len(rejection_reasons) == 0 and
            quality_score >= self.min_quality_score
        )
        
        if quality_score < self.min_quality_score:
            rejection_reasons['quality'] = f"Quality score too low: {quality_score} < {self.min_quality_score}"
        
        return should_enter, quality_score, rejection_reasons


# ============================================================================
# 7. USAGE EXAMPLE
# ============================================================================

def example_backtest_usage():
    """
    Example of using the backtest validator in a backtest loop
    """
    # Initialize validator
    validator = BacktestSignalValidator()
    
    # Configure instruments
    validator.spread_model.set_base_spread('EUR_USD', 0.8)
    validator.spread_model.set_base_spread('GBP_USD', 1.2)
    validator.spread_model.set_base_spread('XAU_USD', 0.50)
    
    # Load news events
    # validator.news_integration.load_events_from_csv('news_calendar.csv')
    
    # Simulate backtest loop
    timestamp = datetime(2025, 10, 1, 14, 30)  # 2:30 PM UTC
    
    # Example price histories (in reality, loaded from data)
    prices_15min = [1.1750, 1.1755, 1.1760, 1.1758, 1.1765]  # Last 5 candles
    prices_1hour = [1.1700, 1.1720, 1.1740, 1.1750, 1.1760]  # Last 5 candles
    prices_4hour = [1.1600, 1.1650, 1.1680, 1.1720, 1.1750]  # Last 5 candles
    
    # Strategy detected a BUY signal
    signal_direction = 'BUY'
    instrument = 'EUR_USD'
    
    # Technical conditions
    ema_aligned = True  # EMA 3 > 8 > 21
    momentum_confirmed = True  # RSI > 50, MACD > Signal
    is_pullback_entry = True  # Price near EMA21
    
    # Validate the signal
    should_enter, quality_score, reasons = validator.validate_entry(
        signal_direction=signal_direction,
        instrument=instrument,
        timestamp=timestamp,
        prices_15min=prices_15min,
        prices_1hour=prices_1hour,
        prices_4hour=prices_4hour,
        ema_aligned=ema_aligned,
        momentum_confirmed=momentum_confirmed,
        is_pullback_entry=is_pullback_entry,
        strategy='ultra_strict_forex',
        volatility=0.00025
    )
    
    print(f"Signal: {signal_direction} {instrument}")
    print(f"Quality Score: {quality_score}/100")
    print(f"Should Enter: {should_enter}")
    
    if not should_enter:
        print(f"Rejection Reasons: {reasons}")
    else:
        print("✅ Signal validated - entering trade")


if __name__ == '__main__':
    print("Backtesting Implementation Guide - October 2025")
    print("=" * 60)
    print()
    print("This module provides production-ready implementations for:")
    print("1. Dynamic spread modeling by session and volatility")
    print("2. Multi-timeframe trend alignment")
    print("3. News event integration and filtering")
    print("4. Signal quality scoring (0-100)")
    print("5. Session-based trade filtering")
    print("6. Complete signal validation")
    print()
    print("Example usage:")
    print("=" * 60)
    example_backtest_usage()






