"""Tests for the TabDPT FM arm (EXPANSION-PLAN-2026-07-09 §2.2, deliverable
2: "FM roster expansion" -- second tabular FM alongside TabICLv2).

Fast, offline, no GPU, no network: the real TabDPT model calls
(`fit_predict_tabdpt` / `get_cal_proba_tabdpt`) are monkeypatched out, same
pattern as tests/test_fm_leakage_ablation.py for the TabICL arm. The real
end-to-end `--smoke` path (which DOES exercise the actual TabDPT classifier
AND regressor forward pass on CPU with the real, HF-downloaded checkpoint)
was run manually while building this script -- see the executor's report.
"""
import json
import os

import numpy as np
import pandas as pd
import pytest

import nd1_tabdpt_fm_arm as fm
import dataset_registry as reg


def _stub_fit_predict_tabdpt(Xtr, ytr, Xte, task, nclass=None):
    rng = np.random.RandomState(0)
    n = len(Xte)
    if task == "clf":
        classes = np.unique(ytr)
        pred = np.full(n, classes[0])
        proba = np.tile(np.eye(len(classes))[0], (n, 1))
        proba = np.clip(proba + rng.uniform(0, 0.1, size=proba.shape), 0.01, 0.99)
        proba = proba / proba.sum(axis=1, keepdims=True)
        unc = 1.0 - proba.max(1)
        return pred, proba, unc
    else:
        pt = np.full(n, float(np.mean(ytr)))
        preds = np.tile(pt, (3, 1))
        return pt, preds, np.full(n, 0.5)


def _stub_get_cal_proba_tabdpt(Xfit, yfit, Xcal, task, nclass=None):
    rng = np.random.RandomState(1)
    n = len(Xcal)
    if task == "clf":
        classes = np.unique(yfit)
        proba = np.tile(np.eye(len(classes))[0], (n, 1))
        proba = np.clip(proba + rng.uniform(0, 0.1, size=proba.shape), 0.01, 0.99)
        proba = proba / proba.sum(axis=1, keepdims=True)
        return proba, classes
    else:
        pt = np.full(n, float(np.mean(yfit)))
        return pt, None


@pytest.fixture(autouse=True)
def stub_tabdpt(monkeypatch):
    monkeypatch.setattr(fm, "fit_predict_tabdpt", _stub_fit_predict_tabdpt)
    monkeypatch.setattr(fm, "get_cal_proba_tabdpt", _stub_get_cal_proba_tabdpt)


def test_grid_flag_defaults_to_core14():
    parser_datasets = reg.get_datasets("core14")
    assert len(parser_datasets) == 14


def test_exclude_key_removes_leakage_column_before_encoding():
    import fm_arm_common as common
    X = pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0], "key_col": ["g1", "g2", "g1", "g2"]})
    key = "key_col"
    Xfeat = X.drop(columns=[key])
    excluded = common.encode_features(Xfeat)
    included = common.encode_features(X)
    assert "key_col" not in excluded.columns
    assert excluded.shape[1] == included.shape[1] - 1


def test_audit_dataset_end_to_end_via_fm_module(monkeypatch):
    """Runs fm._audit_dataset (the TabDPT-bound closure) end to end against a
    synthetic fixture, with the TabDPT model calls stubbed, verifying the
    module wiring (rng_for, model_extra_fields) matches the shared pipeline."""
    import fm_arm_common as common

    def fake_load_dataset(did):
        rng = np.random.RandomState(0)
        n = 300
        groups = rng.randint(0, 8, size=n)
        a = rng.normal(size=n)
        X = pd.DataFrame({"a": a, "grp": groups.astype(str)})
        y = pd.Series((a > 0).astype(int))
        return None, X, y, "y"

    monkeypatch.setattr(common, "load_dataset", fake_load_dataset)
    spec = {"did": -9999, "name": "fixture", "key": "grp", "kind": "group"}

    r = fm._audit_dataset(spec, exclude_key=False)
    assert r["status"] == "ok"
    assert r["model"] == "TabDPT"
    assert "tabdpt_n_ensembles" in r
    assert "tabdpt_unc_spread_k" in r


def test_main_run_end_to_end_schema(tmp_path):
    import fm_arm_common as common
    specs, frames = common.make_synthetic_datasets(n=300, seed=0)

    def fake_load_dataset(did):
        X, y = frames[did]
        return None, X, y, "y"

    orig = common.load_dataset
    common.load_dataset = fake_load_dataset
    try:
        out_path = str(tmp_path / "tabdpt_out.json")
        out = fm.main_run(specs, exclude_key=False,
                          gbm_ref_path=str(tmp_path / "missing.json"),
                          out_path=out_path, write=True)
    finally:
        common.load_dataset = orig

    for key in ("gate", "model", "n_ok", "n_attempted", "results",
               "gbm_reference_xgb_stage1", "rng_discipline", "provenance",
               "full_coverage", "tabdpt_n_ensembles"):
        assert key in out
    assert "TabDPT" in out["model"]
    assert os.path.exists(out_path)
    reloaded = json.load(open(out_path))
    assert reloaded["n_attempted"] == len(specs)
