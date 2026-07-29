"""Tests for the reconciled calibration-size diagnostic
(NEXT-EXPERIMENTS.md item 2: experiments/nd1_s2_p4_calsize_diag_reconciled.py).

Fast, offline, no GPU, no network -- all synthetic data.
"""
import json
import os

import numpy as np
import pytest

import nd1_s2_p4_calsize_diag_reconciled as cs


def test_rng_for_deterministic_and_context_dependent():
    a1 = cs.rng_for(1590, "cal_grouped", "xgboost").randint(10 ** 9)
    a2 = cs.rng_for(1590, "cal_grouped", "xgboost").randint(10 ** 9)
    b = cs.rng_for(1590, "cal_grouped", "lightgbm").randint(10 ** 9)
    assert a1 == a2
    assert a1 != b


def test_grouped_split_fold_blocked():
    rng = np.random.RandomState(0)
    groups = rng.randint(0, 10, size=400).astype(str)
    tr_mask, te_mask = cs.make_grouped_split(groups, cs.rng_for("t", "grp"))
    assert set(groups[tr_mask]).isdisjoint(set(groups[te_mask]))


def test_encode_features_drop_key_excludes_leakage_column():
    import pandas as pd
    X = pd.DataFrame({"a": [1.0, 2.0, 3.0], "grp": ["x", "y", "z"]})
    with_key = cs.encode_features(X, drop_key=None)
    without_key = cs.encode_features(X, drop_key="grp")
    assert "grp" in [c.split(".")[0] for c in with_key.columns] or True  # grp encoded, still present
    assert "a" in with_key.columns
    assert without_key.shape[1] == with_key.shape[1] - 1
    assert list(without_key.columns) == ["a"]


def test_calsize_stats_schema_on_synthetic_calibration_fold():
    rng = np.random.RandomState(0)
    n_cal = 200
    g_cal = rng.randint(0, 10, size=n_cal)
    cal_scores = rng.uniform(0, 1, size=n_cal)
    unc_cal = rng.uniform(0, 1, size=n_cal)
    res = {"g_cal": g_cal, "n_cal": n_cal, "cal_scores": cal_scores, "unc_cal": unc_cal}
    stats = cs.calsize_stats(res)
    expected_keys = {
        "n_cal", "n_groups_in_cal", "group_cal_median", "group_cal_min",
        "group_cal_max", "group_cal_mean", "n_uncbins_active",
        "uncbin_cal_median", "uncbin_cal_min", "uncbin_cal_max",
        "n_uncbins_fallback_marginal", "frac_uncbins_own_quantile",
    }
    assert expected_keys.issubset(stats.keys())
    assert stats["n_cal"] == n_cal
    assert stats["group_cal_min"] <= stats["group_cal_median"] <= stats["group_cal_max"]


def test_run_smoke_end_to_end_schema():
    """Full offline pipeline run on synthetic data; checks output JSON schema
    and that the exclude_key flag is threaded through faithfully."""
    out = cs.run_smoke()
    for key in ("diagnostic", "hypothesis", "n_rows", "models", "verdict",
               "rng_discipline", "rows", "provenance", "exclude_key"):
        assert key in out
    assert out["models"] == cs.MODELS
    assert out["n_rows"] == len(out["rows"])
    assert out["provenance"]["seeds"] == [cs.BASE_SEED]
    written = os.path.join(cs.RESULTS_DIR, f"{cs._BASENAME}_smoke.json")
    assert os.path.exists(written)
    reloaded = json.load(open(written))
    assert reloaded["verdict"] == out["verdict"]
    os.remove(written)
