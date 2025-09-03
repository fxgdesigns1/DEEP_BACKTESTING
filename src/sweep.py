import itertools
import json
import os
import random
from pathlib import Path

import numpy as np
import pandas as pd

from src.engine import run_backtest

CFG_PATH = Path("artifacts/expanded_config.json")
if not CFG_PATH.exists():
    raise FileNotFoundError(
        "Expanded config not found. Generate it via src/synth_config before running sweep."
    )

CFG = json.loads(CFG_PATH.read_text())
ART = Path("artifacts")
ART.mkdir(parents=True, exist_ok=True)

rows = []
random.seed(7)
np.random.seed(7)

for asset in CFG["assets"]:
    for tf in CFG["timeframes"]:
        for family, grid in CFG["families"].items():
            keys, vals = zip(*grid.items())
            combos = list(itertools.product(*vals))
            if len(combos) > 200:
                combos = random.sample(combos, 200)
            for combo in combos:
                params = dict(zip(keys, combo))
                metrics = run_backtest(
                    asset,
                    tf,
                    family,
                    params,
                    CFG["risk"],
                    CFG["costs"],
                    CFG["backtest"],
                )
                row = {"asset": asset, "tf": tf, "family": family, **params, **metrics}
                rows.append(row)

rows_df = pd.DataFrame(rows)
rows_df.to_csv(ART / "runs_raw.csv", index=False)

robust = rows_df.query(
    "Sharpe >= 1.2 and Calmar >= 0.8 and MaxDD <= 0.15 and ProfitFactor >= 1.3"
).copy()
robust.to_csv(ART / "runs_robust.csv", index=False)

w = {
    "Sharpe": 0.35,
    "Sortino": 0.15,
    "Calmar": 0.15,
    "ProfitFactor": 0.15,
    "MaxDD": -0.10,
    "Ulcer": -0.10,
}
for k, v in w.items():
    if k in robust:
        robust[f"z_{k}"] = (robust[k] - robust[k].mean()) / robust[k].std(ddof=0)
robust["score"] = sum(
    robust[f"z_{k}"] * v for k, v in w.items() if f"z_{k}" in robust
)
leader = robust.sort_values("score", ascending=False)
leader.head(20).to_csv(ART / "leaderboard.csv", index=False)

TOP3 = leader.head(3)
TOP3.to_csv(ART / "top3.csv", index=False)
print(
    "TOP-3 CANDIDATES:\n",
    TOP3[["family", "asset", "tf", "Sharpe", "Calmar", "MaxDD", "ProfitFactor", "score"]],
)

# Placeholder for refinement pass – to be implemented later.
# from src.refine import refine_top3
# refine_top3(TOP3, CFG).to_csv(ART/"top3_refined.csv", index=False)