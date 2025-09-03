import pandas as pd
from datetime import datetime, timedelta, timezone

from src.data_loader import DataBundle


def test_no_lookahead(tmp_path):
    """Ensure news events cannot leak before effective_time (timestamp + latency)."""
    cfg = {
        "news": {
            "calendar_source": tmp_path / "calendar.csv",
            "use_as_features": True,
            "as_trading_filter": True,
            "release_latency_seconds": 300,
            "blackout_windows": {"high": {"pre_minutes": 15, "post_minutes": 5}},
            "mapping": {"USD": ["EURUSD"]},
        },
        "backtest": {"timezone": "UTC"},
    }

    # Craft synthetic calendar
    ts_event = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
    df_cal = pd.DataFrame(
        {
            "timestamp": [ts_event],
            "title": ["NFP"],
            "currency": ["USD"],
            "impact": ["high"],
            "forecast": [100],
            "previous": [90],
            "actual": [110],
        }
    )
    df_cal.to_csv(cfg["news"]["calendar_source"], index=False)

    # Create dummy price series around the event
    idx = pd.date_range(ts_event - timedelta(hours=1), periods=10, freq="6T", tz="UTC")
    price_df = pd.DataFrame(
        {
            "open": 1.0,
            "high": 1.0,
            "low": 1.0,
            "close": 1.0,
            "volume": 0,
        },
        index=idx,
    )

    bundle = DataBundle(cfg)
    merged = bundle.merge_news(price_df, "EURUSD")

    # Feature should be NaN/0 until latency has passed
    eff_time = ts_event + timedelta(seconds=cfg["news"]["release_latency_seconds"])
    assert merged.loc[idx < eff_time, "impact_code"].fillna(0).eq(0).all()