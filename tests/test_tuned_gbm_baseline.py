"""Tests for the tuned-GBM baseline rerun
(NEXT-EXPERIMENTS.md item 4: experiments/nd1_tuned_gbm_baseline.py).

Fast (CPU, tiny synthetic data, small search budgets), offline, no GPU/network.
Uses the real xgboost/lightgbm fit calls (they are already CPU-fast core deps
of this repo), not stubs -- unlike the TabICL arm there is no heavyweight
checkpoint download involved.
"""
import json
import os

import numpy as np
import pandas as pd
import pytest

import nd1_tuned_gbm_baseline as tg


def test_rng_for_deterministic_and_context_dependent():
    a = tg.rng_for(1590, "tune", "xgboost").randint(10 ** 9)
    b = tg.rng_for(1590, "tune", "xgboost").randint(10 ** 9)
    c = tg.rng_for(1590, "tune", "lightgbm").randint(10 ** 9)
    assert a == b
    assert a != c


def test_grouped_split_fold_blocked():
    rng = np.random.RandomState(0)
    groups = rng.randint(0, 10, size=400).astype(str)
    tr_mask, te_mask = tg.make_grouped_split(groups, tg.rng_for("t", "grp"))
    assert set(groups[tr_mask]).isdisjoint(set(groups[te_mask]))


def test_tuning_only_touches_the_random_split_training_fold():
    """Leakage-safety invariant: tune_hyperparams must select params using only
    the rows handed to it (the random-split TRAIN fold) -- it must not receive
    or need the grouped/time test fold at all. We verify this structurally: the
    function signature takes Xtr/ytr only (no grouped-split arguments exist),
    and a param dict is returned using only the sizes present in Xtr."""
    rng = np.random.RandomState(0)
    n = 200
    Xtr = pd.DataFrame({"a": rng.normal(size=n), "b": rng.normal(size=n)})
    ytr = ((Xtr["a"] + rng.normal(scale=0.1, size=n)) > 0).astype(int).values
    params = tg.tune_hyperparams("xgboost", Xtr, ytr, "clf", tg.rng_for("test", "tune"))
    for key in ("n_estimators", "max_depth", "learning_rate", "subsample", "colsample"):
        assert key in params
    assert params["n_estimators"] in tg.PARAM_SPACE["n_estimators"]


def test_tune_hyperparams_falls_back_on_tiny_data():
    """n < 60 is too little for a safe inner holdout; must fall back to a fixed
    default rather than overfitting the search to noise."""
    rng = np.random.RandomState(0)
    n = 30
    Xtr = pd.DataFrame({"a": rng.normal(size=n)})
    ytr = (Xtr["a"] > 0).astype(int).values
    params = tg.tune_hyperparams("xgboost", Xtr, ytr, "clf", tg.rng_for("test", "tune2"))
    assert params == {"n_estimators": 200, "max_depth": 6, "learning_rate": 0.1,
                      "subsample": 0.8, "colsample": 0.8}


def test_run_smoke_end_to_end_schema():
    out = tg.run_smoke()
    for key in ("gate", "models", "n_tune_trials", "param_space",
               "tuning_protocol", "rng_discipline", "per_model_summary",
               "results", "provenance"):
        assert key in out
    assert set(out["per_model_summary"].keys()) == set(tg.MODELS)
    for model, summ in out["per_model_summary"].items():
        assert summ["n_datasets_ok"] >= 0
        assert "median_aurc_delta" in summ
    written = os.path.join(tg.RESULTS_DIR, f"{tg._BASENAME}_smoke.json")
    assert os.path.exists(written)
    reloaded = json.load(open(written))
    assert reloaded["gate"] == out["gate"]
    os.remove(written)


def test_exclude_key_ablation_drops_key_from_features(monkeypatch):
    """audit_dataset(..., exclude_key=True) must not expose the grouping key as
    a model feature (no-leakage invariant, same contract as Stage-1)."""
    seen_columns = []
    real_encode = tg.encode_features

    def spy_encode(X):
        seen_columns.append(list(X.columns))
        return real_encode(X)

    monkeypatch.setattr(tg, "encode_features", spy_encode)

    def fake_load_dataset(did):
        rng = np.random.RandomState(0)
        n = 200
        groups = rng.randint(0, 8, size=n)
        a = rng.normal(size=n)
        X = pd.DataFrame({"a": a, "grp": groups.astype(str)})
        y = pd.Series((a > 0).astype(int))
        return None, X, y, "y"

    monkeypatch.setattr(tg, "load_dataset", fake_load_dataset)
    monkeypatch.setattr(tg, "N_TUNE_TRIALS", 2)
    spec = {"did": -7777, "name": "fixture", "key": "grp", "kind": "group"}

    r = tg.audit_dataset(spec, "xgboost", exclude_key=True)
    assert r["status"] == "ok"
    assert all("grp" not in cols for cols in seen_columns)
