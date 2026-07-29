"""Offline tests for the TabPFN-v2 arm's audit pipeline (COMPUTE-PLAN §5 retarget).
No GPU, no network, NO TABPFN_TOKEN: the real `tabpfn` model calls are
monkeypatched, same pattern as test_tabpfn25_arm.py / test_tabdpt_fm_arm.py. The
real forward pass against actual TabPFN-v2 weights is verified only once a token
is available (see test_tabpfn25_stub.py for the guard tests, mirrored here)."""
import json
import os

import numpy as np
import pandas as pd
import pytest

import nd1_tabpfnv2_arm as fm
import fm_arm_common as common


def _stub_fit_predict(Xtr, ytr, Xte, task, nclass=None):
    rng = np.random.RandomState(0)
    n = len(Xte)
    if task == "clf":
        classes = np.unique(ytr)
        pred = np.full(n, classes[0])
        proba = np.tile(np.eye(len(classes))[0], (n, 1))
        proba = np.clip(proba + rng.uniform(0, 0.1, size=proba.shape), 0.01, 0.99)
        proba = proba / proba.sum(axis=1, keepdims=True)
        return pred, proba, 1.0 - proba.max(1)
    pt = np.full(n, float(np.mean(ytr)))
    return pt, (pt - 1.0, pt + 1.0), np.full(n, 2.0)


def _stub_get_cal_proba(Xfit, yfit, Xcal, task, nclass=None):
    rng = np.random.RandomState(1)
    n = len(Xcal)
    if task == "clf":
        classes = np.unique(yfit)
        proba = np.tile(np.eye(len(classes))[0], (n, 1))
        proba = np.clip(proba + rng.uniform(0, 0.1, size=proba.shape), 0.01, 0.99)
        return proba / proba.sum(axis=1, keepdims=True), classes
    pt = np.full(n, float(np.mean(yfit)))
    return pt, (pt - 1.0, pt + 1.0)


@pytest.fixture(autouse=True)
def stub_tabpfn(monkeypatch):
    monkeypatch.setattr(fm, "fit_predict_tabpfn", _stub_fit_predict)
    monkeypatch.setattr(fm, "get_cal_proba_tabpfn", _stub_get_cal_proba)


def _fake_load(did):
    rng = np.random.RandomState(0)
    n = 300
    a = rng.normal(size=n)
    X = pd.DataFrame({"a": a, "grp": rng.randint(0, 8, size=n).astype(str)})
    return None, X, pd.Series((a > 0).astype(int)), "y"


def test_audit_dataset_tags_v2(monkeypatch):
    monkeypatch.setattr(common, "load_dataset", _fake_load)
    r = fm._audit_dataset({"did": -9999, "name": "fx", "key": "grp", "kind": "group"},
                          exclude_key=False)
    assert r["status"] == "ok"
    assert r["model"] == "TabPFN-v2"
    assert r["tabpfn_model_version"] == "V2"


def test_main_run_schema_and_license(tmp_path, monkeypatch):
    specs, frames = common.make_synthetic_datasets(n=300, seed=0)
    monkeypatch.setattr(common, "load_dataset", lambda did: (None, *frames[did], "y"))
    out = fm.main_run(specs, exclude_key=False,
                      gbm_ref_path=str(tmp_path / "missing.json"),
                      out_path=str(tmp_path / "v2.json"), write=True)
    assert "TabPFN-v2" in out["model"]
    assert out["tabpfn_model_version"] == "V2"
    assert "Apache" in out["tabpfn_license"]
    assert os.path.exists(str(tmp_path / "v2.json"))


def test_token_guard_blocks_without_token(monkeypatch):
    monkeypatch.delenv("TABPFN_TOKEN", raising=False)
    assert fm.check_token_guard() is False


def test_token_guard_passes_with_token(monkeypatch):
    monkeypatch.setenv("TABPFN_TOKEN", "dummy")
    assert fm.check_token_guard() is True
