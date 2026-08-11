#!/usr/bin/env python3
"""alpha_sweep_structured.py — local or box-side conformal alpha sweep for the
structured-kbs paper. Assumes model predictions and conformal score functions
are available in the research package.

This is a stub/spec; the exact data loader and model harness must be imported
from the existing research package (replace `PLACEHOLDER` imports below).

Output: alpha_sweep_2026-07-20/results.json with records:
  {"strategy": "random|group|time", "dataset": "...", "model": "...", "alpha": 0.1,
   "coverage_mean": 0.89, "coverage_low": ..., "coverage_high": ...}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np


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

ROOT = _portal_repo_root()
OUT = ROOT / "alpha_sweep_2026-07-20" / "results.json"
OUT.parent.mkdir(exist_ok=True)

ALPHAS = [0.01, 0.02, 0.03, 0.04, 0.05, 0.075, 0.10, 0.125, 0.15, 0.175, 0.20]

# TODO: import the actual data loaders and conformal helpers from the research package
# sys.path.insert(0, str(ROOT / "research"))


def split_conformal_coverage(scores, labels, alpha, n_cal=0.8, n_repeats=10):
    """Placeholder coverage estimator. Replace with package implementation."""
    records = []
    for _ in range(n_repeats):
        n = len(scores)
        idx = np.random.permutation(n)
        n_cal = max(1, int(n * n_cal))
        cal_scores = scores[idx[:n_cal]]
        eval_labels = labels[idx[n_cal:]]
        eval_scores = scores[idx[n_cal:]]
        q = np.quantile(cal_scores, np.ceil((n_cal + 1) * (1 - alpha)) / n_cal, method="higher")
        covered = eval_labels[eval_scores <= q]
        records.append(float(covered.mean()) if len(covered) > 0 else float("nan"))
    return records


def main():
    # TODO: load actual datasets, strategies, and predictions
    results = []
    # Example skeleton loop:
    # for dataset in DATASETS:
    #     for model in MODELS:
    #         for strategy in ("random", "group", "time"):
    #             scores, labels = load_predictions(dataset, model, strategy)
    #             for alpha in ALPHAS:
    #                 coverages = split_conformal_coverage(scores, labels, alpha)
    #                 results.append({
    #                     "strategy": strategy, "dataset": dataset, "model": model,
    #                     "alpha": alpha, "coverage_mean": np.mean(coverages),
    #                     "coverage_low": np.percentile(coverages, 10),
    #                     "coverage_high": np.percentile(coverages, 90),
    #                 })
    OUT.write_text(json.dumps(results, indent=2))
    print(f"wrote {OUT} with {len(results)} records")


if __name__ == "__main__":
    main()
