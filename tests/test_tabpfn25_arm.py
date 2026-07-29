"""Tests for the TabPFN-2.5 arm's audit pipeline (EXPANSION-PLAN-2026-07-09
§2.2 deliverable 2: "wire the existing TabPFN-2.5 stub so that when
TABPFN_TOKEN is set it actually runs"). Fast, offline, no GPU, no network,
NO TABPFN_TOKEN required for these tests: the real `tabpfn` model calls
(`fit_predict_tabpfn` / `get_cal_proba_tabpfn`) are monkeypatched out, same
pattern as tests/test_fm_leakage_ablation.py and tests/test_tabdpt_fm_arm.py.
This deliberately never imports the real `tabpfn` package's network/license
path -- per portfolio policy, the real forward pass against actual TabPFN-2.5
weights is verified only once TABPFN_TOKEN is available (see
tests/test_tabpfn25_stub.py for the guard tests, which DO require staying
green with no token set).
"""
import json
import os

import numpy as np
import pandas as pd
import pytest

import nd1_tabpfn25_arm as fm
import fm_arm_common as common


def _stub_fit_predict_tabpfn(Xtr, ytr, Xte, task, nclass=None):
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
        lo = pt - 1.0
        hi = pt + 1.0
        return pt, (lo, hi), hi - lo


def _stub_get_cal_proba_tabpfn(Xfit, yfit, Xcal, task, nclass=None):
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
        lo = pt - 1.0
        hi = pt + 1.0
        return pt, (lo, hi)


@pytest.fixture(autouse=True)
def stub_tabpfn(monkeypatch):
    monkeypatch.setattr(fm, "fit_predict_tabpfn", _stub_fit_predict_tabpfn)
    monkeypatch.setattr(fm, "get_cal_proba_tabpfn", _stub_get_cal_proba_tabpfn)


def test_audit_dataset_end_to_end_via_fm_module(monkeypatch):
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
    assert r["model"] == "TabPFN-2.5"
    assert "tabpfn_n_estimators" in r


def test_exclude_key_removes_leakage_column_end_to_end(monkeypatch):
    seen_columns = []
    real_encode = common.encode_features

    def spy_encode(X):
        seen_columns.append(list(X.columns))
        return real_encode(X)

    monkeypatch.setattr(common, "encode_features", spy_encode)

    def fake_load_dataset(did):
        rng = np.random.RandomState(0)
        n = 300
        groups = rng.randint(0, 8, size=n)
        a = rng.normal(size=n)
        X = pd.DataFrame({"a": a, "grp": groups.astype(str)})
        y = pd.Series((a > 0).astype(int))
        return None, X, y, "y"

    monkeypatch.setattr(common, "load_dataset", fake_load_dataset)
    spec = {"did": -8888, "name": "fixture2", "key": "grp", "kind": "group"}

    r = fm._audit_dataset(spec, exclude_key=True)
    assert r["status"] == "ok"
    assert all("grp" not in cols for cols in seen_columns)
    assert r["exclude_key"] is True


def test_main_run_end_to_end_schema(tmp_path):
    specs, frames = common.make_synthetic_datasets(n=300, seed=0)

    def fake_load_dataset(did):
        X, y = frames[did]
        return None, X, y, "y"

    orig = common.load_dataset
    common.load_dataset = fake_load_dataset
    try:
        out_path = str(tmp_path / "tabpfn_out.json")
        out = fm.main_run(specs, exclude_key=False,
                          gbm_ref_path=str(tmp_path / "missing.json"),
                          out_path=out_path, write=True)
    finally:
        common.load_dataset = orig

    for key in ("gate", "model", "n_ok", "n_attempted", "results",
               "gbm_reference_xgb_stage1", "rng_discipline", "provenance",
               "full_coverage", "tabpfn_n_estimators"):
        assert key in out
    assert "TabPFN-2.5" in out["model"]
    assert os.path.exists(out_path)
    reloaded = json.load(open(out_path))
    assert reloaded["n_attempted"] == len(specs)


def test_run_smoke_requires_no_network_and_produces_schema(monkeypatch):
    """--smoke uses the synthetic fixture path; still must not touch the
    guard (this test forces TABPFN_N_ESTIMATORS/DEVICE via run_smoke's own
    overrides, same pattern as the TabICL/TabDPT smoke paths)."""
    out = fm.run_smoke()
    assert out["n_attempted"] == 1
    assert out["full_coverage"] is True
    written = os.path.join(fm.RESULTS_DIR, f"{fm._BASENAME}_smoke.json")
    assert os.path.exists(written)
    os.remove(written)
