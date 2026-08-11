#!/usr/bin/env python3
"""make_fig_coverage_alpha.py — structured-kbs coverage vs nominal α curve.

Reads split-conformal results across alpha values for the three split strategies
(random, leave-group-out, rolling-origin). The data structure is produced by
the box/local runner `alpha_sweep_structured.py` and is expected at:
  structured-data-fm-reliability-research/alpha_sweep_2026-07-20/results.json

Each entry contains:
  {
    "strategy": "random" | "group" | "time",
    "dataset": "<openml_id>",
    "alpha": 0.1,
    "coverage_mean": 0.89,
    "coverage_low": 0.85,
    "coverage_high": 0.93,
    "model": "xgb" | "lightgbm" | "tabicl" | "tabdpt"
  }

Produces a figure with:
  (a) mean coverage vs nominal 1-α across strategies, with parity band.
  (b) coverage deficit (nominal - empirical) vs alpha, per strategy.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _portal_commons_root():
    import os
    from pathlib import Path
    for key in ("COMMONS_ROOT", "RELIABILITY_COMMONS"):
        v = os.environ.get(key)
        if v:
            p = Path(v).expanduser().resolve()
            if p.is_dir():
                return p
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        for cand in (parent / "reliability-commons", parent.parent / "reliability-commons"):
            if cand.is_dir():
                return cand
    raise RuntimeError(
        "Set COMMONS_ROOT to the reliability-commons checkout (or place it as a sibling of this repo)."
    )

def _portal_repo_root():
    from pathlib import Path
    here = Path(__file__).resolve().parent
    for p in [here, *here.parents]:
        if (p / ".git").exists() or (p / "pyproject.toml").exists() or (p / "README.md").exists():
            return p
    return here

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_portal_commons_root() / "tools" / "inspect-gate" / "figures_2026-07-19"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

DATA = _portal_repo_root() / "alpha_sweep_2026-07-20" / "results.json"
OUT = _portal_repo_root() / "manuscripts" / "figures" / "F8_coverage_alpha.pdf"


def main():
    if not DATA.exists():
        raise FileNotFoundError(
            f"Alpha-sweep results not found: {DATA}\n"
            "Run the box/local alpha_sweep_structured.py first."
        )
    records = json.load(open(DATA))
    strategies = ["random", "group", "time"]
    colors = {"random": "#0072B2", "group": "#D55E00", "time": "#E69F00"}
    labels = {"random": "random split", "group": "leave-group-out", "time": "rolling-origin"}

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8))
    alphas = sorted({r["alpha"] for r in records})
    nominal = [1 - a for a in alphas]

    for strategy in strategies:
        means = []
        lows = []
        highs = []
        for alpha in alphas:
            vals = [r["coverage_mean"] for r in records
                    if r["strategy"] == strategy and r["alpha"] == alpha]
            if vals:
                means.append(np.mean(vals))
                lows.append(np.percentile(vals, 10))
                highs.append(np.percentile(vals, 90))
            else:
                means.append(float("nan"))
                lows.append(float("nan"))
                highs.append(float("nan"))
        axes[0].plot(nominal, means, "o-", color=colors[strategy], label=labels[strategy], lw=1.2, ms=3)
        axes[0].fill_between(nominal, lows, highs, color=colors[strategy], alpha=0.12)

    axes[0].plot([0, 1], [0, 1], "k--", lw=0.8, label="nominal parity")
    axes[0].set_xlabel("nominal coverage $1-\\alpha$")
    axes[0].set_ylabel("empirical coverage")
    axes[0].set_xlim(0.75, 1.0)
    axes[0].set_ylim(0.70, 1.0)
    axes[0].legend(fontsize=7, frameon=False)
    axes[0].text(0.05, 0.95, "(a)", transform=axes[0].transAxes, fontweight="bold", va="top")

    for strategy in strategies:
        deficits = []
        for alpha in alphas:
            vals = [r["coverage_mean"] for r in records
                    if r["strategy"] == strategy and r["alpha"] == alpha]
            if vals:
                deficits.append((1 - alpha) - np.mean(vals))
            else:
                deficits.append(float("nan"))
        axes[1].plot(alphas, deficits, "o-", color=colors[strategy], label=labels[strategy], lw=1.2, ms=3)
    axes[1].axhline(0, color="black", lw=0.8, ls="--")
    axes[1].set_xlabel("nominal miscoverage level $\\alpha$")
    axes[1].set_ylabel("coverage deficit")
    axes[1].set_xlim(0, 0.21)
    axes[1].legend(fontsize=7, frameon=False)
    axes[1].text(0.05, 0.95, "(b)", transform=axes[1].transAxes, fontweight="bold", va="top")

    fig.tight_layout()
    fig.savefig(OUT, dpi=600)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
