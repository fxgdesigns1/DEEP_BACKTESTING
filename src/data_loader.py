from pathlib import Path
import pandas as pd
import numpy as np

class DataBundle:
    """Loads price data, DXY features, news calendar, and merges them with anti-leakage controls."""
    def __init__(self, cfg):
        self.cfg = cfg
        self.base = Path("data/prices")
        self.news_path = Path(cfg["news"]["calendar_source"]).resolve()
        self.tz = cfg["backtest"].get("timezone", "UTC")

    # ------------------------- price helpers ------------------------- #
    def _read_csv(self, symbol):
        """Read raw CSV for *symbol* and enforce monotonic timestamp index."""
        f = self.base / f"{symbol}.csv"
        df = pd.read_csv(f)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.set_index("timestamp").sort_index()
        # Drop duplicate timestamps, keep last occurrence (assume corrections later in file)
        df = df[~df.index.duplicated(keep="last")]
        return df

    def _resample(self, df: pd.DataFrame, tf: str) -> pd.DataFrame:
        """Resample OHLCV frame to target timeframe."""
        rule = {"15m": "15T", "1h": "1H", "4h": "4H", "1d": "1D"}.get(tf, tf)
        o = df["open"].resample(rule, label="right", closed="right").first()
        h = df["high"].resample(rule, label="right", closed="right").max()
        l = df["low"].resample(rule, label="right", closed="right").min()
        c = df["close"].resample(rule, label="right", closed="right").last()
        v = (
            df.get("volume", pd.Series(index=c.index))
            .resample(rule, label="right", closed="right")
            .sum(min_count=1)
        )
        out = pd.concat({"open": o, "high": h, "low": l, "close": c, "volume": v}, axis=1)
        return out.dropna()

    def load_price(self, symbol: str, tf: str) -> pd.DataFrame:
        df = self._read_csv(symbol)
        if self.cfg.get("resample_from_native", False):
            df = self._resample(df, tf)
        return df

    # --------------------------- DXY --------------------------- #
    def load_dxy_feature(self, tf: str) -> pd.DataFrame:
        aliases = self.cfg["dxy"]["symbol_aliases"]
        base = Path("data/factors")
        for alias in aliases:
            file = base / f"{alias}.csv"
            if file.exists():
                dxy = pd.read_csv(file)
                dxy["timestamp"] = pd.to_datetime(dxy["timestamp"], utc=True)
                dxy = dxy.set_index("timestamp").sort_index()[["close"]].rename(columns={"close": "dxy"})
                return self._resample(dxy, tf)
        raise FileNotFoundError(
            "No DXY file found under aliases: " + ", ".join(aliases)
        )

    # --------------------------- NEWS --------------------------- #
    def load_news(self) -> pd.DataFrame:
        cal = pd.read_csv(self.news_path)
        cal["timestamp"] = pd.to_datetime(cal["timestamp"], utc=True)
        need = [
            "timestamp",
            "title",
            "currency",
            "impact",
            "forecast",
            "previous",
            "actual",
        ]
        for col in need:
            if col not in cal.columns:
                cal[col] = np.nan
        cal = cal[need].sort_values("timestamp").reset_index(drop=True)
        return cal

    def merge_news(self, price_df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        cfg_news = self.cfg["news"]
        if not (cfg_news.get("use_as_features") or cfg_news.get("as_trading_filter")):
            return price_df

        cal = self.load_news()
        # Reverse mapping currency -> symbols
        rev_map = {}
        for cur, symbols in cfg_news.get("mapping", {}).items():
            for s in symbols:
                rev_map.setdefault(s, set()).add(cur)
        currencies = rev_map.get(symbol, set())
        if not currencies:
            return price_df

        sub = cal[cal["currency"].isin(list(currencies))].copy()
        latency = pd.to_timedelta(cfg_news.get("release_latency_seconds", 0), unit="s")
        sub["effective_time"] = sub["timestamp"] + latency
        sub = sub.set_index("effective_time").sort_index()

        impact_map = {"low": 1, "medium": 2, "high": 3}
        sub["impact_code"] = sub["impact"].str.lower().map(impact_map).fillna(0)
        feats = sub[["impact_code", "actual", "forecast", "previous"]].copy()

        merged = price_df.join(feats.reindex(price_df.index, method="ffill"))
        merged["news_surprise"] = (
            (merged["actual"] - merged["forecast"]).where(merged["forecast"].notna())
        )

        if cfg_news.get("as_trading_filter"):
            merged["news_blackout"] = 0
            for imp, win in cfg_news["blackout_windows"].items():
                pre = pd.to_timedelta(win["pre_minutes"], unit="m")
                post = pd.to_timedelta(win["post_minutes"], unit="m")
                rows = sub[sub["impact"].str.lower() == imp]
                for t in rows.index:
                    mask = (merged.index >= t - pre) & (merged.index <= t + post)
                    merged.loc[mask, "news_blackout"] = 1

        return merged.fillna(0)