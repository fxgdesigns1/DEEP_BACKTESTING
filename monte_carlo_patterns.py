#!/usr/bin/env python3
"""
MONTE CARLO PATTERN ANALYSIS MODULE
Advanced statistical analysis and pattern detection for trading backtests
Includes: MC simulations, pattern discovery, leverageability testing
"""

import os
import json
import math
import uuid
import time
import random
import logging
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)


def _to_df(trades_or_equity: Dict[str, Any]) -> pd.DataFrame:
    """Convert trades or equity array to standardized DataFrame"""
    if "equity" in trades_or_equity:
        eq = pd.Series(trades_or_equity["equity"], dtype=float)
        ret = eq.diff().fillna(0.0)
        df = pd.DataFrame({
            "ts": np.arange(len(eq)), 
            "equity": eq.values, 
            "ret": ret.values
        })
        df["hour"] = (df["ts"] % 24).astype(int)
        df["side"] = 0
        df["duration"] = 0.0
        return df
        
    trades = trades_or_equity.get("trades", [])
    if not trades:
        raise ValueError("Provide 'equity' array or 'trades' list.")
        
    df = pd.DataFrame(trades)
    df["ts"] = pd.to_datetime(df.get("timestamp", pd.Series(range(len(df)))))
    
    if "pnl" not in df.columns:
        raise ValueError("Each trade must have 'pnl'.")
        
    df["ret"] = df["pnl"].astype(float)
    
    if "hour" not in df.columns:
        df["hour"] = pd.to_datetime(df["ts"]).dt.hour.fillna(0).astype(int)
    if "side" not in df.columns:
        df["side"] = 0
    if "duration" not in df.columns:
        df["duration"] = 0.0
        
    df["equity"] = df["ret"].cumsum()
    
    return df[["ts", "ret", "equity", "hour", "side", "duration"]]


def mc_trade_shuffle(df: pd.DataFrame, runs: int = 1000, seed: int = 42) -> List[np.ndarray]:
    """Monte Carlo simulation using trade shuffling (permutation test)"""
    rng = np.random.default_rng(seed)
    rets = df["ret"].values.copy()
    paths = []
    n = len(rets)
    
    logger.info(f"Running {runs} MC trade shuffle simulations on {n} trades")
    
    for _ in range(runs):
        idx = rng.permutation(n)
        r = rets[idx]
        paths.append(np.cumsum(r))
        
    return paths


def mc_block_bootstrap(df: pd.DataFrame, runs: int = 1000, block: int = 10, seed: int = 123) -> List[np.ndarray]:
    """Monte Carlo simulation using block bootstrap (preserves serial correlation)"""
    rng = np.random.default_rng(seed)
    rets = df["ret"].values
    n = len(rets)
    nb = int(np.ceil(n / block))
    paths = []
    
    logger.info(f"Running {runs} MC block bootstrap simulations (block size={block})")
    
    for _ in range(runs):
        out = []
        for _ in range(nb):
            start = int(rng.integers(0, max(1, n - block)))
            out.extend(rets[start:start+block])
        out = out[:n]
        paths.append(np.cumsum(np.array(out)))
        
    return paths


def sharpe_ratio(returns: np.ndarray, eps: float = 1e-9) -> float:
    """Calculate annualized Sharpe ratio"""
    if len(returns) < 2:
        return 0.0
    mu = returns.mean()
    sd = returns.std(ddof=1) + eps
    return (mu / sd) * np.sqrt(252)


def max_drawdown(equity: np.ndarray) -> float:
    """Calculate maximum drawdown"""
    cummax = np.maximum.accumulate(equity)
    dd = (equity - cummax)
    return -dd.min() if len(dd) else 0.0


def ulcer_index(equity: np.ndarray) -> float:
    """Calculate Ulcer Index (RMS of drawdown)"""
    cummax = np.maximum.accumulate(equity)
    dd = (equity - cummax)
    return float(np.sqrt(np.mean(dd**2))) if len(dd) else 0.0


def compute_metrics(equity: np.ndarray) -> Dict[str, float]:
    """Compute key performance metrics from equity curve"""
    rets = np.diff(np.concatenate([[0.0], equity]))
    return {
        "sharpe": float(sharpe_ratio(rets)), 
        "max_dd": float(max_drawdown(equity)), 
        "ulcer": float(ulcer_index(equity)), 
        "trades": int(len(rets))
    }


def hour_of_day_effect(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze hour-of-day effects using Kruskal-Wallis test"""
    g = df.groupby("hour")["ret"].agg(["mean", "std", "count"]).reset_index()
    groups = [group["ret"].values for _, group in df.groupby("hour")]
    
    if len(groups) > 1 and all(len(x) > 1 for x in groups):
        H, p = stats.kruskal(*groups)
    else:
        H, p = float('nan'), 1.0
        
    best_hours = g.sort_values("mean", ascending=False).head(3)["hour"].tolist()
    worst_hours = g.sort_values("mean", ascending=True).head(3)["hour"].tolist()
    
    return {
        "table": g.to_dict(orient="records"), 
        "kruskal_H": float(H), 
        "p_value": float(p), 
        "best_hours": best_hours, 
        "worst_hours": worst_hours
    }


def autocorr_tests(df: pd.DataFrame, lags: int = 20) -> Dict[str, Any]:
    """Test for autocorrelation using Ljung-Box test"""
    x = df["ret"].values
    try:
        lb_stat, lb_p = acorr_ljungbox(x, lags=lags, return_df=False)
        lb_stat = lb_stat.tolist()
        lb_p = lb_p.tolist()
    except Exception as e:
        logger.warning(f"Ljung-Box test failed: {e}")
        lb_stat = [float('nan')] * lags
        lb_p = [1.0] * lags
        
    return {"lb_stat": lb_stat, "lb_p": lb_p}


def runs_test(x: np.ndarray) -> Dict[str, Any]:
    """Runs test for randomness"""
    signs = np.sign(x)
    signs = signs[signs != 0]
    
    if len(signs) < 2:
        return {
            "z": 0.0, 
            "p": 1.0, 
            "runs": 0, 
            "n_pos": 0, 
            "n_neg": 0
        }
        
    n_pos = int((signs > 0).sum())
    n_neg = int((signs < 0).sum())
    runs = int(1 + (signs[1:] != signs[:-1]).sum())
    
    mu = (2 * n_pos * n_neg) / (n_pos + n_neg) + 1
    var = (2 * n_pos * n_neg * (2 * n_pos * n_neg - n_pos - n_neg)) / (
        ((n_pos + n_neg)**2) * (n_pos + n_neg - 1) + 1e-9
    )
    
    z = (runs - mu) / np.sqrt(var + 1e-9) if var > 0 else 0.0
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    
    return {
        "z": float(z), 
        "p": float(p), 
        "runs": runs, 
        "n_pos": n_pos, 
        "n_neg": n_neg
    }


def motif_discovery_simple(series: np.ndarray, w: int = 20, top_k: int = 3) -> Dict[str, Any]:
    """Discover recurring patterns (motifs) and anomalies (discords) in equity curve"""
    n = len(series)
    if n < 3 * w:
        return {"motifs": [], "discord": None}
        
    # Extract and normalize windows
    windows = []
    for i in range(0, n - w + 1):
        seg = series[i:i+w]
        z = (seg - seg.mean()) / (seg.std(ddof=1) + 1e-9)
        windows.append((i, z))
        
    idxs = list(range(len(windows)))
    rng = np.random.default_rng(123)
    sample = set(rng.choice(idxs, size=min(200, len(idxs)), replace=False))
    
    counts = np.zeros(len(windows))
    dists = np.full(len(windows), np.inf)
    
    # Find motifs (similar patterns) and discords (anomalous patterns)
    for i, (si, sz) in enumerate(windows):
        if i not in sample:
            continue
        for j, (sj, tz) in enumerate(windows):
            if abs(si - sj) < w:
                continue
            d = np.linalg.norm(sz - tz)
            if d < 5.0:
                counts[i] += 1
            dists[i] = min(dists[i], d)
            
    motif_idx = np.argsort(-counts)[:top_k]
    motifs = [
        {"start": int(windows[i][0]), "len": int(w), "score": float(counts[i])} 
        for i in motif_idx if counts[i] > 0
    ]
    
    discord = int(np.argmax(dists)) if np.isfinite(dists).any() else None
    discord_info = {"start": int(windows[discord][0]), "len": int(w)} if discord is not None else None
    
    return {"motifs": motifs, "discord": discord_info}


def drawdown_shape_clustering(equity: np.ndarray, k: int = 3) -> Dict[str, Any]:
    """Cluster drawdown episodes by shape using K-Means"""
    eq = np.array(equity)
    peaks = np.maximum.accumulate(eq)
    dd = peaks - eq
    episodes = []
    start = None
    
    # Extract drawdown episodes
    for i in range(len(dd)):
        if dd[i] > 1e-12 and start is None:
            start = i
        if dd[i] < 1e-12 and start is not None:
            end = i
            seg = dd[start:end]
            if len(seg) >= 5:
                # Normalize to fixed length for clustering
                x = np.interp(np.linspace(0, len(seg)-1, 50), np.arange(len(seg)), seg)
                episodes.append(x)
            start = None
            
    if not episodes:
        return {"clusters": []}
        
    X = np.vstack(episodes)
    km = KMeans(n_clusters=min(k, len(episodes)), n_init=10, random_state=42)
    labels = km.fit_predict(X)
    centers = km.cluster_centers_.tolist()
    counts = pd.Series(labels).value_counts().to_dict()
    
    return {
        "k": int(km.n_clusters), 
        "counts": {int(k): int(v) for k, v in counts.items()}, 
        "centers": centers
    }


def leverage_test_hour_filter(
    df: pd.DataFrame, 
    mc_paths: List[np.ndarray], 
    top_hours: List[int], 
    worst_hours: List[int]
) -> Dict[str, Any]:
    """Test if filtering hours and leveraging best hours improves Sharpe ratio"""
    hours = df["hour"].values
    uplifts = []
    
    for eq in mc_paths:
        rets = np.diff(np.concatenate([[0.0], eq]))
        h = np.resize(hours, rets.shape[0])
        adj = rets.copy()
        
        # Filter worst hours (set returns to 0)
        adj[np.isin(h, worst_hours)] = 0.0
        # Leverage best hours (multiply by 1.25)
        adj[np.isin(h, top_hours)] *= 1.25
        
        base_sharpe = float((rets.mean() / (rets.std(ddof=1) + 1e-9)) * np.sqrt(252)) if len(rets) > 1 else 0.0
        adj_sharpe = float((adj.mean() / (adj.std(ddof=1) + 1e-9)) * np.sqrt(252)) if len(adj) > 1 else 0.0
        
        uplifts.append(adj_sharpe - base_sharpe)
        
    arr = np.array(uplifts)
    
    return {
        "uplift_mean": float(arr.mean() if len(arr) else 0.0),
        "uplift_p95": float(np.percentile(arr, 95) if len(arr) else 0.0),
        "uplift_frac_positive": float((arr > 0).mean() if len(arr) else 0.0),
        "n_paths": int(len(arr))
    }


def analyze(
    trades_or_equity: Dict[str, Any], 
    runs: int = 1000, 
    block: int = 10, 
    window: int = 20, 
    seed: int = 42
) -> Dict[str, Any]:
    """
    Comprehensive Monte Carlo pattern analysis
    
    Args:
        trades_or_equity: Dict with either 'equity' array or 'trades' list
        runs: Number of Monte Carlo simulations
        block: Block size for block bootstrap
        window: Window size for motif discovery
        seed: Random seed for reproducibility
        
    Returns:
        Comprehensive analysis report with MC simulations and pattern analysis
    """
    logger.info("Starting Monte Carlo pattern analysis")
    logger.info(f"Settings: runs={runs}, block={block}, window={window}, seed={seed}")
    
    # Convert to DataFrame
    df = _to_df(trades_or_equity)
    logger.info(f"Loaded {len(df)} trades/data points")
    
    # Run Monte Carlo simulations (50/50 split between shuffle and block bootstrap)
    paths_shuffle = mc_trade_shuffle(df, runs=runs//2, seed=seed)
    paths_block = mc_block_bootstrap(df, runs=runs - len(paths_shuffle), block=block, seed=seed+1)
    paths = paths_shuffle + paths_block
    logger.info(f"Generated {len(paths)} MC paths")
    
    # Calculate base metrics
    base_metrics = compute_metrics(df["equity"].values)
    logger.info(f"Base metrics: Sharpe={base_metrics['sharpe']:.2f}, MaxDD={base_metrics['max_dd']:.2f}")
    
    # Pattern analysis
    hod = hour_of_day_effect(df)
    ac = autocorr_tests(df)
    rt = runs_test(df["ret"].values)
    motifs = motif_discovery_simple(df["equity"].values, w=window, top_k=3)
    ddc = drawdown_shape_clustering(df["equity"].values, k=3)
    lev = leverage_test_hour_filter(df, paths, hod["best_hours"], hod["worst_hours"])
    
    # MC metrics distribution
    metrics = [compute_metrics(p) for p in paths]
    sharpe_dist = [m["sharpe"] for m in metrics]
    dd_dist = [m["max_dd"] for m in metrics]
    
    logger.info(f"MC Sharpe: mean={np.mean(sharpe_dist):.2f}, p5={np.percentile(sharpe_dist, 5):.2f}, p95={np.percentile(sharpe_dist, 95):.2f}")
    logger.info(f"Leverageability uplift: {lev['uplift_mean']:.3f} (p95={lev['uplift_p95']:.3f})")
    
    # Compile report
    report = {
        "run_id": str(uuid.uuid4())[:8],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "base_metrics": base_metrics,
        "mc": {
            "runs": len(paths),
            "sharpe_mean": float(np.mean(sharpe_dist)) if sharpe_dist else 0.0,
            "sharpe_p05": float(np.percentile(sharpe_dist, 5)) if sharpe_dist else 0.0,
            "sharpe_p95": float(np.percentile(sharpe_dist, 95)) if sharpe_dist else 0.0,
            "maxdd_mean": float(np.mean(dd_dist)) if dd_dist else 0.0,
            "maxdd_p95": float(np.percentile(dd_dist, 95)) if dd_dist else 0.0
        },
        "patterns": {
            "hour_of_day": hod,
            "autocorr": ac,
            "runs_test": rt,
            "motifs": motifs,
            "drawdown_clusters": ddc
        },
        "leverageability": lev
    }
    
    logger.info("Monte Carlo pattern analysis complete")
    
    return report




