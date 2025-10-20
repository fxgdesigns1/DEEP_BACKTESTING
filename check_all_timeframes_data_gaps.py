#!/usr/bin/env python3
"""
CHECK ALL TIMEFRAMES FOR DATA GAPS
BRUTAL HONESTY - Report every single gap found
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_timeframe_gaps(file_path, expected_interval_minutes):
    """Check a single timeframe file for gaps"""
    logger.info(f"\nChecking: {file_path.name}")
    logger.info("="*60)
    
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    total_candles = len(df)
    first_date = df['timestamp'].min()
    last_date = df['timestamp'].max()
    
    logger.info(f"  Total candles: {total_candles:,}")
    logger.info(f"  First: {first_date}")
    logger.info(f"  Last: {last_date}")
    logger.info(f"  Span: {(last_date - first_date).days} days")
    
    # Check for gaps
    time_diffs = df['timestamp'].diff()
    expected_diff = pd.Timedelta(minutes=expected_interval_minutes)
    
    # Find significant gaps (more than expected interval)
    # Allow for weekends (2-3 days) and market closures
    max_acceptable_gap = pd.Timedelta(days=4)  # Weekend + 1 day buffer
    
    gaps = time_diffs[time_diffs > max_acceptable_gap]
    
    if len(gaps) > 0:
        logger.info(f"\n  ⚠️  FOUND {len(gaps)} SIGNIFICANT GAPS:")
        for idx, gap_duration in gaps.items():
            gap_start = df.iloc[idx-1]['timestamp']
            gap_end = df.iloc[idx]['timestamp']
            logger.info(f"    Gap #{idx}: {gap_duration} from {gap_start} to {gap_end}")
    else:
        logger.info(f"  ✓ NO SIGNIFICANT GAPS (weekends/holidays are normal)")
    
    # Check for duplicates
    duplicates = df[df['timestamp'].duplicated()]
    if len(duplicates) > 0:
        logger.info(f"\n  ⚠️  FOUND {len(duplicates)} DUPLICATE TIMESTAMPS")
    else:
        logger.info(f"  ✓ NO DUPLICATES")
    
    # Check data recency (gap from last candle to now)
    now = datetime.now()
    if last_date.tz is not None:
        import pytz
        now = now.replace(tzinfo=pytz.UTC)
    
    days_behind = (now - last_date).days
    logger.info(f"\n  Data is {days_behind} days behind current date")
    
    if days_behind > 7:
        logger.info(f"  ⚠️  DATA IS MORE THAN 1 WEEK OLD")
    elif days_behind > 2:
        logger.info(f"  ⚠️  DATA IS {days_behind} DAYS OLD")
    else:
        logger.info(f"  ✓ DATA IS CURRENT (within 2 days)")
    
    return {
        'file': file_path.name,
        'total_candles': total_candles,
        'first_date': str(first_date),
        'last_date': str(last_date),
        'significant_gaps': len(gaps),
        'duplicates': len(duplicates),
        'days_behind': days_behind,
        'status': 'OK' if len(gaps) == 0 and days_behind <= 2 else 'NEEDS_UPDATE'
    }

def main():
    """Check all timeframes"""
    logger.info("="*80)
    logger.info("CHECKING ALL TIMEFRAMES FOR DATA GAPS")
    logger.info("BRUTAL HONESTY - REPORTING EVERY GAP")
    logger.info("="*80)
    
    data_dir = Path("data/MASTER_DATASET")
    
    timeframes = {
        '1m': 1,
        '5m': 5,
        '15m': 15,
        '30m': 30,
        '1h': 60,
        '4h': 240,
        '1d': 1440
    }
    
    all_results = []
    
    for tf, interval_mins in timeframes.items():
        tf_dir = data_dir / tf
        if not tf_dir.exists():
            logger.info(f"\n⚠️  MISSING DIRECTORY: {tf_dir}")
            continue
        
        # Check XAU_USD file
        xau_file = tf_dir / "xau_usd_{}.csv".format(tf)
        
        if not xau_file.exists():
            logger.info(f"\n❌ MISSING FILE: {xau_file}")
            all_results.append({
                'file': xau_file.name,
                'status': 'MISSING'
            })
            continue
        
        result = check_timeframe_gaps(xau_file, interval_mins)
        all_results.append(result)
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("SUMMARY - ALL TIMEFRAMES")
    logger.info(f"{'='*80}\n")
    
    for result in all_results:
        if result.get('status') == 'MISSING':
            logger.info(f"❌ {result['file']}: FILE MISSING")
        elif result.get('status') == 'OK':
            logger.info(f"✓ {result['file']}: OK ({result['total_candles']:,} candles, {result['days_behind']} days old)")
        else:
            logger.info(f"⚠️  {result['file']}: NEEDS UPDATE ({result['significant_gaps']} gaps, {result['days_behind']} days old)")
    
    logger.info(f"\n{'='*80}")

if __name__ == "__main__":
    main()


