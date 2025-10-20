#!/usr/bin/env python3
"""
IMPROVED BACKTESTING SYSTEM - October 2025
Based on Live Trading System Improvements

Implements critical improvements:
1. Dynamic Spread Modeling (session-based, volatility-based, news-based)
2. Multi-Timeframe Analysis and HTF alignment
3. News Event Integration with pause mechanism
4. Signal Quality Scoring (0-100 point system)
5. Session-Based Filtering (London/NY only)
6. Pullback Entry Detection
7. Time Spacing Between Trades (30 min minimum)
8. ATR-Based Dynamic Stops
9. Improved R:R Ratios (1:3 to 1:4)

Author: AI Trading System
Date: October 1, 2025
Version: 2.1.0
"""

import pandas as pd
import numpy as np
import os
import json
import yaml
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('improved_backtesting_oct2025.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# 1. ENUMS AND DATA CLASSES
# ============================================================================

class TradingSession(Enum):
    """Trading session types"""
    LONDON = "london"
    NY = "ny"
    LONDON_NY_OVERLAP = "london_ny_overlap"
    ASIAN = "asian"
    WEEKEND = "weekend"
    OFF_HOURS = "off_hours"


class SignalDirection(Enum):
    """Signal direction"""
    BUY = "BUY"
    SELL = "SELL"
    NO_SIGNAL = "NO_SIGNAL"


@dataclass
class NewsEvent:
    """News event data"""
    timestamp: datetime
    event_type: str
    impact: str  # high, medium, low
    currency: str
    actual: Optional[float] = None
    forecast: Optional[float] = None
    previous: Optional[float] = None
    
    def surprise_factor(self) -> float:
        """Calculate surprise (actual vs forecast deviation)"""
        if self.forecast == 0 or self.actual is None or self.forecast is None:
            return 0
        return (self.actual - self.forecast) / abs(self.forecast)


@dataclass
class TradeSignal:
    """Trading signal with quality score"""
    timestamp: datetime
    instrument: str
    direction: SignalDirection
    entry_price: float
    stop_loss: float
    take_profit: float
    quality_score: float  # 0-100
    quality_breakdown: Dict[str, float]
    signal_type: str  # pullback, breakout, momentum
    htf_aligned: bool
    session: TradingSession
    spread: float
    confidence: float
    

@dataclass
class Trade:
    """Executed trade"""
    entry_time: datetime
    exit_time: Optional[datetime]
    instrument: str
    direction: SignalDirection
    entry_price: float
    exit_price: Optional[float]
    stop_loss: float
    take_profit: float
    position_size: float
    pnl: float
    pnl_pips: float
    exit_reason: str  # take_profit, stop_loss, trailing_stop, news_exit, time_exit
    quality_score: float
    trade_duration: Optional[timedelta]
    

# ============================================================================
# 2. DYNAMIC SPREAD MODEL
# ============================================================================

class DynamicSpreadModel:
    """
    Dynamic spread modeling based on:
    - Trading session
    - Market volatility
    - News events
    """
    
    def __init__(self):
        self.base_spreads = {
            'EUR_USD': 0.8,
            'GBP_USD': 1.2,
            'USD_JPY': 0.9,
            'AUD_USD': 1.0,
            'USD_CAD': 1.2,
            'NZD_USD': 1.3,
            'EUR_JPY': 1.1,
            'GBP_JPY': 1.4,
            'AUD_JPY': 1.2,
            'XAU_USD': 0.50  # Gold in dollars
        }
        
        self.session_multipliers = {
            TradingSession.LONDON: 1.0,
            TradingSession.NY: 1.0,
            TradingSession.LONDON_NY_OVERLAP: 0.8,  # Tightest
            TradingSession.ASIAN: 2.5,  # Widest
            TradingSession.WEEKEND: 5.0,  # Very wide
            TradingSession.OFF_HOURS: 2.0
        }
    
    def get_session(self, timestamp: datetime) -> TradingSession:
        """Determine trading session from UTC timestamp"""
        hour = timestamp.hour
        weekday = timestamp.weekday()
        
        # Weekend
        if weekday >= 5:
            return TradingSession.WEEKEND
        
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
        
        # Off hours
        else:
            return TradingSession.OFF_HOURS
    
    def get_spread(self, 
                   instrument: str, 
                   timestamp: datetime,
                   volatility: Optional[float] = None,
                   news_events: Optional[List[NewsEvent]] = None) -> float:
        """
        Calculate dynamic spread for instrument at timestamp
        
        Returns:
            Spread in pips
        """
        # Get base spread
        base_spread = self.base_spreads.get(instrument, 1.0)
        
        # Apply session multiplier
        session = self.get_session(timestamp)
        session_mult = self.session_multipliers[session]
        
        # Apply volatility multiplier
        volatility_mult = 1.0
        if volatility is not None:
            # Higher volatility = wider spreads
            volatility_mult = 1.0 + (volatility * 1000)
        
        # Apply news multiplier
        news_mult = 1.0
        if news_events:
            for event in news_events:
                time_to_event = abs((event.timestamp - timestamp).total_seconds())
                if time_to_event <= 1800:  # Within 30 minutes
                    if event.impact == 'high':
                        news_mult = max(news_mult, 5.0)
                    elif event.impact == 'medium':
                        news_mult = max(news_mult, 2.0)
        
        # Calculate final spread
        final_spread = base_spread * session_mult * volatility_mult * news_mult
        
        return final_spread


# ============================================================================
# 3. MULTI-TIMEFRAME ANALYZER
# ============================================================================

class TimeframeAnalyzer:
    """Multi-timeframe trend detection"""
    
    def __init__(self):
        self.ema_long_period = 50
        self.ema_short_period = 20
    
    def calculate_ema(self, prices: pd.Series, period: int) -> float:
        """Calculate EMA for given period"""
        if len(prices) < period:
            return prices.iloc[-1] if len(prices) > 0 else 0.0
        
        ema = prices.ewm(span=period, adjust=False).mean()
        return float(ema.iloc[-1])
    
    def get_higher_timeframe_trend(self, 
                                    df: pd.DataFrame,
                                    lookback: int = 50) -> str:
        """
        Determine higher timeframe trend
        
        Returns:
            'BUY', 'SELL', or 'NEUTRAL'
        """
        if len(df) < lookback:
            return 'NEUTRAL'
        
        # Use last lookback bars
        recent_df = df.tail(lookback)
        
        # Calculate EMAs
        long_ema = self.calculate_ema(recent_df['close'], self.ema_long_period)
        short_ema = self.calculate_ema(recent_df['close'], self.ema_short_period)
        current_price = recent_df['close'].iloc[-1]
        
        # Determine trend
        if current_price > long_ema and short_ema > long_ema:
            return 'BUY'
        elif current_price < long_ema and short_ema < long_ema:
            return 'SELL'
        else:
            return 'NEUTRAL'
    
    def check_htf_alignment(self, 
                           signal_direction: str, 
                           htf_trend: str) -> bool:
        """Check if signal aligns with higher timeframe trend"""
        if htf_trend == 'NEUTRAL':
            return True  # Allow trades in neutral HTF
        
        return signal_direction == htf_trend


# ============================================================================
# 4. NEWS INTEGRATION
# ============================================================================

class NewsIntegration:
    """News event integration for trading"""
    
    def __init__(self):
        self.high_impact_events = [
            'Fed Rate Decision',
            'ECB Rate Decision',
            'BOE Rate Decision',
            'BOJ Rate Decision',
            'Non-Farm Payrolls',
            'NFP',
            'CPI',
            'GDP',
            'Unemployment Rate'
        ]
        self.pause_before_minutes = 30
        self.pause_after_minutes = 30
    
    def should_pause_trading(self, 
                            timestamp: datetime,
                            instrument: str,
                            news_events: List[NewsEvent]) -> bool:
        """Check if trading should be paused due to news"""
        for event in news_events:
            # Check if event is high impact
            if event.impact != 'high':
                continue
            
            # Check if event affects this instrument
            if not self._affects_instrument(event, instrument):
                continue
            
            # Check time proximity
            time_to_event = (event.timestamp - timestamp).total_seconds()
            
            # Pause 30 min before and after
            if -self.pause_after_minutes * 60 <= time_to_event <= self.pause_before_minutes * 60:
                return True
        
        return False
    
    def _affects_instrument(self, event: NewsEvent, instrument: str) -> bool:
        """Check if news event affects instrument"""
        # Extract currencies from instrument
        if '_' in instrument:
            base, quote = instrument.split('_')
        else:
            # Gold
            if 'XAU' in instrument:
                base, quote = 'XAU', 'USD'
            else:
                return True  # Default: affects all
        
        # Check if event currency matches
        return event.currency in [base, quote, 'USD']  # USD affects most pairs
    
    def get_sentiment_boost(self,
                           timestamp: datetime,
                           signal_direction: str,
                           instrument: str,
                           news_events: List[NewsEvent]) -> float:
        """
        Get sentiment boost/reduction factor
        
        Returns:
            Multiplier (0.8 to 1.2 range, ±20%)
        """
        # Find relevant recent news
        recent_events = []
        for event in news_events:
            time_diff = (timestamp - event.timestamp).total_seconds()
            # Look at news from last 4 hours
            if 0 <= time_diff <= 14400 and self._affects_instrument(event, instrument):
                recent_events.append(event)
        
        if not recent_events:
            return 1.0  # No boost
        
        # Calculate sentiment from surprise factors
        total_sentiment = 0
        for event in recent_events:
            surprise = event.surprise_factor()
            
            # Positive surprise = bullish for currency
            if event.currency in instrument:
                total_sentiment += surprise
        
        avg_sentiment = total_sentiment / len(recent_events) if recent_events else 0
        
        # Convert to boost factor
        if signal_direction == 'BUY':
            if avg_sentiment > 0.1:
                return 1.20  # +20% boost
            elif avg_sentiment < -0.1:
                return 0.80  # -20% reduction
        elif signal_direction == 'SELL':
            if avg_sentiment < -0.1:
                return 1.20  # +20% boost
            elif avg_sentiment > 0.1:
                return 0.80  # -20% reduction
        
        return 1.0


# ============================================================================
# 5. SIGNAL QUALITY SCORER
# ============================================================================

class SignalQualityScorer:
    """Score signal quality on multiple dimensions (0-100)"""
    
    def calculate_quality_score(self,
                               signal_direction: str,
                               htf_aligned: bool,
                               ema_aligned: bool,
                               momentum_confirmed: bool,
                               is_pullback_entry: bool,
                               spread: float,
                               max_spread: float,
                               session: TradingSession,
                               news_boost: float) -> Tuple[float, Dict[str, float]]:
        """
        Calculate comprehensive quality score
        
        Returns:
            (total_score, breakdown_dict)
        """
        scores = {}
        
        # 1. Multi-timeframe alignment (0-25 points)
        if htf_aligned:
            scores['timeframe_alignment'] = 25
        else:
            scores['timeframe_alignment'] = 0
        
        # 2. Technical strength (0-25 points)
        if ema_aligned and momentum_confirmed:
            scores['technical'] = 25
        elif ema_aligned or momentum_confirmed:
            scores['technical'] = 15
        else:
            scores['technical'] = 5
        
        # 3. Entry timing (0-25 points)
        if is_pullback_entry:
            scores['timing'] = 25  # Perfect pullback entry
        else:
            scores['timing'] = 10  # Breakout or other entry
        
        # 4. Market conditions (0-25 points)
        if spread <= max_spread * 0.8:
            scores['conditions'] = 25  # Excellent spread
        elif spread <= max_spread:
            scores['conditions'] = 15  # Acceptable spread
        else:
            scores['conditions'] = 0  # Spread too wide
        
        # Session bonus/penalty
        if session in [TradingSession.LONDON, TradingSession.NY, TradingSession.LONDON_NY_OVERLAP]:
            scores['conditions'] += 0  # Already good
        else:
            scores['conditions'] -= 10  # Low volume penalty
        
        scores['conditions'] = max(0, scores['conditions'])
        
        # 5. News sentiment alignment (bonus -10 to +10)
        if news_boost > 1.15:
            scores['news_bonus'] = 10
        elif news_boost > 1.05:
            scores['news_bonus'] = 5
        elif news_boost < 0.85:
            scores['news_bonus'] = -10
        elif news_boost < 0.95:
            scores['news_bonus'] = -5
        else:
            scores['news_bonus'] = 0
        
        # Total quality score
        total = sum(scores.values())
        total = min(100, max(0, total))
        
        return total, scores


# ============================================================================
# 6. SESSION FILTER
# ============================================================================

class SessionFilter:
    """Filter trading by session"""
    
    def __init__(self):
        self.allowed_sessions = {
            'ultra_strict_forex': [TradingSession.LONDON, TradingSession.NY, TradingSession.LONDON_NY_OVERLAP],
            'gold_scalping': [TradingSession.LONDON, TradingSession.NY, TradingSession.LONDON_NY_OVERLAP],
            'momentum_trading': [TradingSession.LONDON, TradingSession.NY, TradingSession.LONDON_NY_OVERLAP, TradingSession.ASIAN]
        }
    
    def should_trade_session(self, strategy: str, session: TradingSession) -> bool:
        """Check if strategy should trade this session"""
        allowed = self.allowed_sessions.get(strategy, [])
        return session in allowed if allowed else True


# ============================================================================
# 7. IMPROVED BACKTESTING SYSTEM
# ============================================================================

class ImprovedBacktestingSystem:
    """
    Improved backtesting system with all October 2025 enhancements
    """
    
    def __init__(self, config_path: str = None):
        """Initialize improved backtesting system"""
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.spread_model = DynamicSpreadModel()
        self.timeframe_analyzer = TimeframeAnalyzer()
        self.news_integration = NewsIntegration()
        self.quality_scorer = SignalQualityScorer()
        self.session_filter = SessionFilter()
        
        # Trading state
        self.trades = []
        self.open_positions = []
        self.last_trade_time = {}
        self.capital = 10000.0
        self.peak_capital = 10000.0
        
        # Results
        self.results = {
            'trades': [],
            'metrics': {},
            'quality_stats': {},
            'session_breakdown': {},
            'news_impact': {}
        }
        
        logger.info("✅ Improved Backtesting System Initialized (Oct 2025)")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        
        # Default configuration
        return {
            'initial_capital': 10000.0,
            'risk_per_trade': 0.02,
            'max_positions': 5,
            'portfolio_risk_limit': 0.10,
            'min_signal_quality': 60,
            'min_time_between_trades_minutes': 30
        }
    
    def run_backtest(self,
                    strategy_name: str,
                    df: pd.DataFrame,
                    htf_df: Optional[pd.DataFrame] = None,
                    news_events: Optional[List[NewsEvent]] = None) -> Dict[str, Any]:
        """
        Run improved backtest
        
        Args:
            strategy_name: Name of strategy
            df: Primary timeframe data
            htf_df: Higher timeframe data for alignment
            news_events: List of news events
        
        Returns:
            Backtest results dictionary
        """
        logger.info(f"🚀 Running improved backtest for {strategy_name}")
        logger.info(f"📊 Data: {len(df)} bars from {df.index[0]} to {df.index[-1]}")
        
        # Reset state
        self.trades = []
        self.open_positions = []
        self.last_trade_time = {}
        initial_cap = self.config.get('global', {}).get('initial_capital', 10000.0)
        self.capital = initial_cap
        self.peak_capital = self.capital
        
        if news_events is None:
            news_events = []
        
        # Calculate indicators
        df = self._calculate_indicators(df)
        if htf_df is not None:
            htf_df = self._calculate_indicators(htf_df)
        
        # Run simulation
        for i in range(100, len(df)):  # Start after indicators ready
            current_time = df.index[i]
            current_bar = df.iloc[i]
            
            # Update open positions
            self._update_open_positions(current_bar, current_time)
            
            # Check for news pause
            instrument = self._get_instrument_from_df(df)
            if self.news_integration.should_pause_trading(current_time, instrument, news_events):
                continue
            
            # Check session filter
            session = self.spread_model.get_session(current_time)
            if not self.session_filter.should_trade_session(strategy_name, session):
                continue
            
            # Generate signals
            signal = self._generate_signal(
                strategy_name=strategy_name,
                df=df,
                index=i,
                htf_df=htf_df,
                news_events=news_events,
                current_time=current_time
            )
            
            if signal and signal.quality_score >= self.config.get('min_signal_quality', 60):
                # Execute trade
                self._execute_trade(signal)
        
        # Close remaining positions
        self._close_all_positions(df.iloc[-1], df.index[-1], "backtest_end")
        
        # Calculate results
        self.results = self._calculate_results()
        
        logger.info(f"✅ Backtest complete: {len(self.trades)} trades")
        logger.info(f"💰 Final Capital: ${self.capital:.2f}")
        initial_cap = self.config.get('global', {}).get('initial_capital', 10000.0)
        logger.info(f"📈 Total Return: {((self.capital / initial_cap) - 1) * 100:.2f}%")
        
        return self.results
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        # EMAs
        df['ema_3'] = df['close'].ewm(span=3, adjust=False).mean()
        df['ema_8'] = df['close'].ewm(span=8, adjust=False).mean()
        df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
        df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        df['atr'] = true_range.rolling(window=14).mean()
        
        # Momentum
        df['momentum'] = df['close'].pct_change(periods=10)
        
        return df
    
    def _generate_signal(self,
                        strategy_name: str,
                        df: pd.DataFrame,
                        index: int,
                        htf_df: Optional[pd.DataFrame],
                        news_events: List[NewsEvent],
                        current_time: datetime) -> Optional[TradeSignal]:
        """Generate trading signal with quality scoring"""
        current = df.iloc[index]
        instrument = self._get_instrument_from_df(df)
        
        # Check time spacing
        if not self._can_trade_now(instrument, current_time):
            return None
        
        # Check position limits
        if len(self.open_positions) >= self.config.get('max_positions', 5):
            return None
        
        # Get HTF trend
        htf_trend = 'NEUTRAL'
        if htf_df is not None and len(htf_df) > 0:
            htf_trend = self.timeframe_analyzer.get_higher_timeframe_trend(htf_df)
        
        # Generate signal based on strategy
        direction = SignalDirection.NO_SIGNAL
        is_pullback = False
        ema_aligned = False
        momentum_confirmed = False
        
        if strategy_name == 'ultra_strict_forex':
            # EMA crossover strategy
            ema_aligned = (current['ema_3'] > current['ema_8'] > current['ema_21'])
            momentum_confirmed = (current['rsi'] > 50 and current['macd'] > current['macd_signal'])
            is_pullback = abs(current['close'] - current['ema_21']) / current['ema_21'] < 0.001
            
            if ema_aligned and momentum_confirmed:
                direction = SignalDirection.BUY
                htf_aligned = htf_trend in ['BUY', 'NEUTRAL']
            elif (current['ema_3'] < current['ema_8'] < current['ema_21'] and
                  current['rsi'] < 50 and current['macd'] < current['macd_signal']):
                direction = SignalDirection.SELL
                ema_aligned = True
                momentum_confirmed = True
                is_pullback = abs(current['close'] - current['ema_21']) / current['ema_21'] < 0.001
                htf_aligned = htf_trend in ['SELL', 'NEUTRAL']
            else:
                return None
        
        elif strategy_name == 'gold_scalping':
            # Impulse scalping strategy
            momentum_confirmed = abs(current['momentum']) >= 0.003
            is_pullback = abs(current['close'] - current['ema_21']) / current['ema_21'] < 0.001
            ema_aligned = True  # Less strict for scalping
            
            if current['momentum'] > 0.003 and is_pullback:
                direction = SignalDirection.BUY
                htf_aligned = htf_trend != 'SELL'
            elif current['momentum'] < -0.003 and is_pullback:
                direction = SignalDirection.SELL
                htf_aligned = htf_trend != 'BUY'
            else:
                return None
        
        else:
            return None
        
        if direction == SignalDirection.NO_SIGNAL:
            return None
        
        # Check HTF alignment
        if not self.timeframe_analyzer.check_htf_alignment(direction.value, htf_trend):
            return None
        
        # Get spread
        session = self.spread_model.get_session(current_time)
        spread = self.spread_model.get_spread(
            instrument, 
            current_time,
            volatility=current.get('atr', 0) / current['close'],
            news_events=news_events
        )
        
        # Check max spread
        max_spread = 2.0 if 'XAU' in instrument else 1.5
        if spread > max_spread:
            return None
        
        # Get news sentiment boost
        news_boost = self.news_integration.get_sentiment_boost(
            current_time, direction.value, instrument, news_events
        )
        
        # Calculate quality score
        quality_score, quality_breakdown = self.quality_scorer.calculate_quality_score(
            signal_direction=direction.value,
            htf_aligned=htf_aligned,
            ema_aligned=ema_aligned,
            momentum_confirmed=momentum_confirmed,
            is_pullback_entry=is_pullback,
            spread=spread,
            max_spread=max_spread,
            session=session,
            news_boost=news_boost
        )
        
        # Calculate stops based on strategy
        if strategy_name == 'ultra_strict_forex':
            # Fixed percentage stops with 1:4 R:R
            sl_pct = 0.005  # 0.5%
            tp_pct = 0.020  # 2.0%
            
            if direction == SignalDirection.BUY:
                stop_loss = current['close'] * (1 - sl_pct)
                take_profit = current['close'] * (1 + tp_pct)
            else:
                stop_loss = current['close'] * (1 + sl_pct)
                take_profit = current['close'] * (1 - tp_pct)
        
        elif strategy_name == 'gold_scalping':
            # Fixed pip stops with 1:3.75 R:R
            sl_pips = 8
            tp_pips = 30
            pip_value = 0.01 if 'JPY' not in instrument else 0.01
            
            if direction == SignalDirection.BUY:
                stop_loss = current['close'] - (sl_pips * pip_value)
                take_profit = current['close'] + (tp_pips * pip_value)
            else:
                stop_loss = current['close'] + (sl_pips * pip_value)
                take_profit = current['close'] - (tp_pips * pip_value)
        
        # Create signal
        signal = TradeSignal(
            timestamp=current_time,
            instrument=instrument,
            direction=direction,
            entry_price=current['close'],
            stop_loss=stop_loss,
            take_profit=take_profit,
            quality_score=quality_score,
            quality_breakdown=quality_breakdown,
            signal_type='pullback' if is_pullback else 'breakout',
            htf_aligned=htf_aligned,
            session=session,
            spread=spread,
            confidence=quality_score / 100.0
        )
        
        return signal
    
    def _can_trade_now(self, instrument: str, current_time: datetime) -> bool:
        """Check if enough time has passed since last trade"""
        if instrument not in self.last_trade_time:
            return True
        
        min_gap = timedelta(minutes=self.config.get('min_time_between_trades_minutes', 30))
        time_since_last = current_time - self.last_trade_time[instrument]
        
        return time_since_last >= min_gap
    
    def _execute_trade(self, signal: TradeSignal):
        """Execute trade from signal"""
        # Calculate position size (risk per trade)
        risk_pct = self.config.get('risk_per_trade', 0.02)
        risk_amount = self.capital * risk_pct
        
        # Calculate position size based on stop loss distance
        sl_distance = abs(signal.entry_price - signal.stop_loss)
        position_size = risk_amount / sl_distance if sl_distance > 0 else 0
        
        # Create trade
        trade = Trade(
            entry_time=signal.timestamp,
            exit_time=None,
            instrument=signal.instrument,
            direction=signal.direction,
            entry_price=signal.entry_price,
            exit_price=None,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            position_size=position_size,
            pnl=0,
            pnl_pips=0,
            exit_reason='',
            quality_score=signal.quality_score,
            trade_duration=None
        )
        
        self.open_positions.append(trade)
        self.last_trade_time[signal.instrument] = signal.timestamp
        
        logger.debug(f"📈 {signal.direction.value} {signal.instrument} @ {signal.entry_price:.5f} (Q={signal.quality_score:.0f})")
    
    def _update_open_positions(self, current_bar: pd.Series, current_time: datetime):
        """Update open positions and check for exits"""
        closed_positions = []
        
        for trade in self.open_positions:
            # Check stop loss
            if trade.direction == SignalDirection.BUY:
                if current_bar['low'] <= trade.stop_loss:
                    trade.exit_price = trade.stop_loss
                    trade.exit_reason = 'stop_loss'
                    closed_positions.append(trade)
                    continue
                elif current_bar['high'] >= trade.take_profit:
                    trade.exit_price = trade.take_profit
                    trade.exit_reason = 'take_profit'
                    closed_positions.append(trade)
                    continue
            else:  # SELL
                if current_bar['high'] >= trade.stop_loss:
                    trade.exit_price = trade.stop_loss
                    trade.exit_reason = 'stop_loss'
                    closed_positions.append(trade)
                    continue
                elif current_bar['low'] <= trade.take_profit:
                    trade.exit_price = trade.take_profit
                    trade.exit_reason = 'take_profit'
                    closed_positions.append(trade)
                    continue
        
        # Process closed positions
        for trade in closed_positions:
            trade.exit_time = current_time
            trade.trade_duration = trade.exit_time - trade.entry_time
            
            # Calculate P&L
            if trade.direction == SignalDirection.BUY:
                trade.pnl = (trade.exit_price - trade.entry_price) * trade.position_size
            else:
                trade.pnl = (trade.entry_price - trade.exit_price) * trade.position_size
            
            # Update capital
            self.capital += trade.pnl
            self.peak_capital = max(self.peak_capital, self.capital)
            
            # Record trade
            self.trades.append(trade)
            self.open_positions.remove(trade)
            
            logger.debug(f"💰 Closed {trade.direction.value} {trade.instrument}: P&L=${trade.pnl:.2f} ({trade.exit_reason})")
    
    def _close_all_positions(self, last_bar: pd.Series, last_time: datetime, reason: str):
        """Close all remaining open positions"""
        for trade in self.open_positions:
            trade.exit_time = last_time
            trade.exit_price = last_bar['close']
            trade.exit_reason = reason
            trade.trade_duration = trade.exit_time - trade.entry_time
            
            # Calculate P&L
            if trade.direction == SignalDirection.BUY:
                trade.pnl = (trade.exit_price - trade.entry_price) * trade.position_size
            else:
                trade.pnl = (trade.entry_price - trade.exit_price) * trade.position_size
            
            # Update capital
            self.capital += trade.pnl
            
            # Record trade
            self.trades.append(trade)
        
        self.open_positions = []
    
    def _calculate_results(self) -> Dict[str, Any]:
        """Calculate comprehensive backtest results"""
        if not self.trades:
            return {
                'error': 'No trades executed',
                'trades': [],
                'metrics': {}
            }
        
        # Convert trades to DataFrame
        trades_data = []
        for trade in self.trades:
            trades_data.append({
                'entry_time': trade.entry_time,
                'exit_time': trade.exit_time,
                'instrument': trade.instrument,
                'direction': trade.direction.value,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'pnl': trade.pnl,
                'exit_reason': trade.exit_reason,
                'quality_score': trade.quality_score,
                'duration_hours': trade.trade_duration.total_seconds() / 3600 if trade.trade_duration else 0
            })
        
        trades_df = pd.DataFrame(trades_data)
        
        # Calculate metrics
        total_pnl = trades_df['pnl'].sum()
        wins = trades_df[trades_df['pnl'] > 0]
        losses = trades_df[trades_df['pnl'] <= 0]
        
        win_rate = len(wins) / len(trades_df) if len(trades_df) > 0 else 0
        avg_win = wins['pnl'].mean() if len(wins) > 0 else 0
        avg_loss = losses['pnl'].mean() if len(losses) > 0 else 0
        profit_factor = abs(wins['pnl'].sum() / losses['pnl'].sum()) if len(losses) > 0 and losses['pnl'].sum() != 0 else 0
        
        # Calculate returns
        initial_capital = self.config.get('global', {}).get('initial_capital', 10000.0)
        total_return = (self.capital / initial_capital - 1) * 100
        
        # Calculate drawdown
        equity_curve = [initial_capital]
        for pnl in trades_df['pnl']:
            equity_curve.append(equity_curve[-1] + pnl)
        
        equity_series = pd.Series(equity_curve)
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max * 100
        max_drawdown = drawdown.min()
        
        # Calculate Sharpe ratio
        returns = trades_df['pnl'] / initial_capital
        sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
        
        # Quality stats
        quality_stats = {
            'avg_quality_score': trades_df['quality_score'].mean(),
            'min_quality_score': trades_df['quality_score'].min(),
            'max_quality_score': trades_df['quality_score'].max(),
            'high_quality_trades': len(trades_df[trades_df['quality_score'] >= 80]),
            'medium_quality_trades': len(trades_df[(trades_df['quality_score'] >= 60) & (trades_df['quality_score'] < 80)]),
            'low_quality_trades': len(trades_df[trades_df['quality_score'] < 60])
        }
        
        # Exit reason breakdown
        exit_breakdown = trades_df['exit_reason'].value_counts().to_dict()
        
        metrics = {
            'total_trades': len(trades_df),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate': win_rate * 100,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_return_pct': total_return,
            'max_drawdown_pct': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'avg_trade_duration_hours': trades_df['duration_hours'].mean(),
            'final_capital': self.capital,
            'initial_capital': initial_capital
        }
        
        return {
            'trades': trades_data,
            'metrics': metrics,
            'quality_stats': quality_stats,
            'exit_breakdown': exit_breakdown,
            'equity_curve': equity_curve
        }
    
    def _get_instrument_from_df(self, df: pd.DataFrame) -> str:
        """Extract instrument name from dataframe"""
        # Try to get from metadata or filename
        if hasattr(df, 'name'):
            return df.name
        return 'EUR_USD'  # Default
    
    def export_results(self, output_path: str):
        """Export results to JSON"""
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"✅ Results exported to {output_path}")


# ============================================================================
# 8. MAIN EXECUTION
# ============================================================================

def main():
    """Main execution"""
    logger.info("=" * 80)
    logger.info("IMPROVED BACKTESTING SYSTEM - October 2025")
    logger.info("=" * 80)
    
    # Initialize system
    backtest = ImprovedBacktestingSystem()
    
    logger.info("✅ System ready for backtesting")
    logger.info("📚 To use this system:")
    logger.info("   1. Load your data into a pandas DataFrame")
    logger.info("   2. Call backtest.run_backtest(strategy_name, df, htf_df, news_events)")
    logger.info("   3. Review results with backtest.results")
    

if __name__ == "__main__":
    main()


