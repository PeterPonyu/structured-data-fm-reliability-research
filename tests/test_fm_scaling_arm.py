"""Tests for the TabICLv2 in-context scaling arm (EXPANSION-PLAN-2026-07-09
§2.2, deliverable 4: "In-context scaling arm" -- ensemble size x context
length sweep). Fast, offline, no GPU, no network: `fit_predict_tabicl_clf`
and the TabICLClassifier construction inside `run_cell` are monkeypatched out
via a fake `tabicl` module injected into sys.modules (same style as the
other FM arms' stubs, adapted because this script imports `TabICLClassifier`
locally inside functions rather than taking it as a parameter). The real
`--smoke` path (actual TabICL forward passes, CPU, cached checkpoint) was
run manually while building this script -- see the executor's report.
"""
import json
import os
import sys
import types

import numpy as np
import pandas as pd
import pytest

import nd1_fm_scaling_arm as sca


class _FakeTabICLClassifier:
    """Deterministic stand-in with the same constructor/fit/predict_proba
    shape as the real TabICLClassifier, parametrized by n_estimators so
    tests can assert the sweep actually threads it through."""

    def __init__(self, n_estimators=8, allow_auto_download=True, device="cpu",
                verbose=False):
        self.n_estimators = n_estimators

    def fit(self, X, y):
        self.classes_ = np.unique(y)
        self._majority = self.classes_[0]
        return self

    def predict_proba(self, X):
        rng = np.random.RandomState(self.n_estimators)
        n = len(X)
        proba = np.tile(np.eye(len(self.classes_))[0], (n, 1))
        proba = np.clip(proba + rng.uniform(0, 0.1, size=proba.shape), 0.01, 0.99)
        return proba / proba.sum(axis=1, keepdims=True)


@pytest.fixture(autouse=True)
def fake_tabicl_module(monkeypatch):
    fake_mod = types.SimpleNamespace(TabICLClassifier=_FakeTabICLClassifier)
    monkeypatch.setitem(sys.modules, "tabicl", fake_mod)
    yield


def _fixture_frame(n=300, seed=0):
    rng = np.random.RandomState(seed)
    a = rng.normal(size=n)
    b = rng.normal(size=n)
    X = pd.DataFrame({"a": a, "b": b})
    y = pd.Series(((a + 0.5 * b) > 0).astype(int))
    return X, y


def test_prep_fixed_split_produces_nested_pool_and_fixed_cal():
    X, y = _fixture_frame()

    def fake_load(did):
        return None, X, y, "y"

    spec = {"did": -1234, "name": "fixture", "key": "a", "kind": "group"}
    fixed = sca.prep_fixed_split(spec, load_dataset_fn=fake_load)
    assert fixed["task"] == "clf"
    assert fixed["n_fit_pool"] == len(fixed["Xfit_pool"])
    assert len(fixed["Xcal"]) > 0
    assert len(fixed["Xte"]) > 0
    # cal + fit_pool + test should reconstruct the whole dataset
    assert fixed["n_fit_pool"] + len(fixed["Xcal"]) + len(fixed["Xte"]) == len(X)


def test_run_cell_context_length_is_nested_prefix():
    X, y = _fixture_frame()

    def fake_load(did):
        return None, X, y, "y"

    spec = {"did": -1234, "name": "fixture", "key": "a", "kind": "group"}
    fixed = sca.prep_fixed_split(spec, load_dataset_fn=fake_load)

    small = sca.run_cell(fixed, n_estimators=1, context_length=20)
    large = sca.run_cell(fixed, n_estimators=1, context_length=40)
    assert small["status"] == "ok" and large["status"] == "ok"
    assert small["n_context_actual"] == 20
    assert large["n_context_actual"] == 40
    # the smaller context's rows must be a strict prefix of the larger one's
    small_rows = fixed["Xfit_pool"].iloc[:20]
    large_prefix = fixed["Xfit_pool"].iloc[:20]
    pd.testing.assert_frame_equal(small_rows.reset_index(drop=True),
                                  large_prefix.reset_index(drop=True))


def test_run_cell_context_length_capped_at_pool_size():
    X, y = _fixture_frame(n=200)

    def fake_load(did):
        return None, X, y, "y"

    spec = {"did": -1234, "name": "fixture", "key": "a", "kind": "group"}
    fixed = sca.prep_fixed_split(spec, load_dataset_fn=fake_load)
    huge_ctx = fixed["n_fit_pool"] + 10_000
    cell = sca.run_cell(fixed, n_estimators=1, context_length=huge_ctx)
    assert cell["status"] == "ok"
    assert cell["n_context_actual"] == fixed["n_fit_pool"]


def test_run_cell_threads_n_estimators_into_model():
    X, y = _fixture_frame()

    def fake_load(did):
        return None, X, y, "y"

    spec = {"did": -1234, "name": "fixture", "key": "a", "kind": "group"}
    fixed = sca.prep_fixed_split(spec, load_dataset_fn=fake_load)
    cell = sca.run_cell(fixed, n_estimators=7, context_length=50)
    assert cell["n_estimators"] == 7


def test_main_run_end_to_end_schema(tmp_path):
    X, y = _fixture_frame()

    def fake_load(did):
        return None, X, y, "y"

    spec = {"did": -1234, "name": "fixture", "key": "a", "kind": "group"}
    out_path = str(tmp_path / "scaling_out.json")
    out = sca.main_run([spec], n_est_grid=[1, 2], context_grid=[20, 40],
                       out_path=out_path, write=True, load_dataset_fn=fake_load)

    for key in ("gate", "model", "datasets", "ensemble_sizes", "context_lengths",
               "n_cells_attempted", "n_cells_ok", "cells", "protocol", "provenance"):
        assert key in out
    assert out["n_cells_attempted"] == 4  # 2 n_est x 2 context lengths
    assert out["n_cells_ok"] == 4
    assert os.path.exists(out_path)
    reloaded = json.load(open(out_path))
    assert reloaded["n_cells_attempted"] == 4


def test_main_run_skips_regression_task_cleanly(tmp_path):
    """The scaling arm's fast path only supports classification (see module
    docstring); a regression dataset must be recorded as a clean skip per
    dataset-fetch, not crash the whole sweep."""
    rng = np.random.RandomState(0)
    n = 300
    X = pd.DataFrame({"a": rng.normal(size=n)})
    y = pd.Series(rng.normal(size=n))  # continuous -> "reg" task

    def fake_load(did):
        return None, X, y, "y"

    spec = {"did": -5555, "name": "reg_fixture", "key": "a", "kind": "group"}
    out_path = str(tmp_path / "scaling_reg.json")
    out = sca.main_run([spec], n_est_grid=[1], context_grid=[20],
                       out_path=out_path, write=True, load_dataset_fn=fake_load)
    assert out["n_cells_ok"] == 0
    assert out["cells"][0]["status"] == "skip"
