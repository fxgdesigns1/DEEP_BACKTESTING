import pandas as pd

__all__ = ["attach_dxy_features", "dxy_risk_scale"]

def attach_dxy_features(price_df: pd.DataFrame, dxy_df: pd.DataFrame, cfg_features: dict) -> pd.DataFrame:
    """Join DXY price series into *price_df* and create rolling z-score features."""
    df = price_df.join(dxy_df, how="left").ffill()
    for w in cfg_features.get("rolling_z_windows", [20, 60]):
        df[f"dxy_z_{w}"] = (
            (df["dxy"] - df["dxy"].rolling(w).mean()) / df["dxy"].rolling(w).std(ddof=0)
        )
    return df

def dxy_risk_scale(signal_bias: int, dxy_slope: float, *, scale_min: float = 0.5, scale_max: float = 1.0) -> float:
    """Return risk scale between *scale_min* and *scale_max* depending on DXY disagreement.

    Parameters
    ----------
    signal_bias : int
        1 for long, -1 for short signals.
    dxy_slope : float
        Recent slope of DXY (positive = USD strength, negative = USD weakness).
    scale_min, scale_max : float
        Bounds of scaling factor.
    """
    disagree = (signal_bias * dxy_slope) < 0
    return scale_min if disagree else scale_max