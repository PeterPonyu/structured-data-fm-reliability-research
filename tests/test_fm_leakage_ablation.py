"""Tests for the TabICLv2 FM-arm leakage ablation + larger-ensembles script
(NEXT-EXPERIMENTS.md item 3: experiments/nd1_tabicl_fm_arm_leakage_ablation.py).

Fast, offline, no GPU, no network: the real TabICL model calls
(`fit_predict_tabicl` / `get_cal_proba_tabicl`) are monkeypatched out with a
trivial deterministic stand-in so the surrounding pipeline logic (splits,
fold-blocking, EXCLUDE_KEY leakage exclusion, bootstrap CIs, JSON schema, live
GBM-reference loading) can be verified without downloading/running the real
model. The real end-to-end `--smoke` path (which DOES exercise the actual
TabICL forward pass on CPU with the cached checkpoint) was verified manually;
see the executor's report.
"""
import json
import os

import numpy as np
import pandas as pd
import pytest

import nd1_tabicl_fm_arm_leakage_ablation as fm


def _stub_fit_predict_tabicl(Xtr, ytr, Xte, task, nclass=None):
    """Deterministic stand-in: predict the majority class of ytr for every
    test row (clf) with uncertainty = distance from a fixed pseudo-probability,
    or the training mean (reg)."""
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
        width = hi - lo
        return pt, (lo, hi), width


def _stub_get_cal_proba_tabicl(Xfit, yfit, Xcal, task, nclass=None):
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
def stub_tabicl(monkeypatch):
    """Every test in this module runs with TabICL calls stubbed out."""
    monkeypatch.setattr(fm, "fit_predict_tabicl", _stub_fit_predict_tabicl)
    monkeypatch.setattr(fm, "get_cal_proba_tabicl", _stub_get_cal_proba_tabicl)


def test_rng_for_deterministic_and_context_dependent():
    a = fm.rng_for(151, "split_random").randint(10 ** 9)
    b = fm.rng_for(151, "split_random").randint(10 ** 9)
    c = fm.rng_for(151, "split_grouped").randint(10 ** 9)
    assert a == b
    assert a != c


def test_grouped_split_fold_blocked():
    rng = np.random.RandomState(0)
    groups = rng.randint(0, 10, size=400).astype(str)
    tr_mask, te_mask = fm.make_grouped_split(groups, fm.rng_for("t", "grp"))
    assert set(groups[tr_mask]).isdisjoint(set(groups[te_mask]))


def test_exclude_key_removes_leakage_column_before_encoding():
    """Mirrors the exact conditional used in audit_dataset: EXCLUDE_KEY=1 must
    drop the split key from the feature matrix (no-leakage invariant)."""
    X = pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0], "key_col": ["g1", "g2", "g1", "g2"]})
    key = "key_col"
    exclude_key = True

    Xfeat = X.drop(columns=[key]) if exclude_key else X
    excluded = fm.encode_features(Xfeat)
    included = fm.encode_features(X)
    assert "key_col" not in excluded.columns
    assert excluded.shape[1] == included.shape[1] - 1


def test_audit_dataset_excludes_key_column_end_to_end(monkeypatch):
    """Full audit_dataset() call with EXCLUDE_KEY semantics: the model must
    never see the grouping key as a feature when exclude_key=True. We verify
    this indirectly by checking the run succeeds identically in shape whether
    or not the key is present (the stub ignores X content), and directly by
    intercepting encode_features to record the columns it was given."""
    seen_columns = []
    real_encode = fm.encode_features

    def spy_encode(X):
        seen_columns.append(list(X.columns))
        return real_encode(X)

    monkeypatch.setattr(fm, "encode_features", spy_encode)

    def fake_load_dataset(did):
        rng = np.random.RandomState(0)
        n = 300
        groups = rng.randint(0, 8, size=n)
        a = rng.normal(size=n)
        X = pd.DataFrame({"a": a, "grp": groups.astype(str)})
        y = pd.Series(((a) > 0).astype(int))
        return None, X, y, "y"

    monkeypatch.setattr(fm, "load_dataset", fake_load_dataset)
    spec = {"did": -9999, "name": "fixture", "key": "grp", "kind": "group"}

    r_incl = fm.audit_dataset(spec, exclude_key=False)
    assert r_incl["status"] == "ok"
    assert any("grp" in cols for cols in seen_columns)

    seen_columns.clear()
    r_excl = fm.audit_dataset(spec, exclude_key=True)
    assert r_excl["status"] == "ok"
    assert all("grp" not in cols for cols in seen_columns)
    assert r_excl["exclude_key"] is True


def test_load_gbm_reference_parses_expected_shape(tmp_path):
    fixture = {
        "results": [
            {"status": "ok", "name": "adult",
             "conformal_cov_grouped": 0.81, "repair_ratio_grouped": 0.63},
            {"status": "skip", "name": "broken"},
        ]
    }
    path = tmp_path / "stage1.json"
    path.write_text(json.dumps(fixture))
    ref = fm.load_gbm_reference(str(path))
    assert ref == {"adult": {"cov_grouped": 0.81, "repair_grouped": 0.63}}


def test_load_gbm_reference_missing_file_returns_empty(tmp_path):
    assert fm.load_gbm_reference(str(tmp_path / "nope.json")) == {}


def test_main_run_end_to_end_schema_and_gbm_reference(tmp_path):
    specs, frames = fm.make_synthetic_datasets(n=300, seed=0)

    def fake_load_dataset(did):
        X, y = frames[did]
        return None, X, y, "y"

    orig = fm.load_dataset
    fm.load_dataset = fake_load_dataset
    try:
        out_path = str(tmp_path / "fm_out.json")
        out = fm.main_run(specs, exclude_key=False,
                          gbm_ref_path=str(tmp_path / "missing.json"),
                          out_path=out_path, write=True)
    finally:
        fm.load_dataset = orig

    for key in ("gate", "model", "n_ok", "n_attempted", "results",
               "gbm_reference_xgb_stage1", "rng_discipline", "provenance",
               "tabicl_n_estimators", "full_coverage"):
        assert key in out
    assert out["gbm_reference_xgb_stage1"] == {}  # missing path -> empty, not stale-hardcoded
    assert out["full_coverage"] is True  # all synthetic specs ran ok
    assert os.path.exists(out_path)
    reloaded = json.load(open(out_path))
    assert reloaded["n_attempted"] == len(specs)


def test_grid_flag_core14_matches_module_level_datasets():
    """--grid core14 (the default) must reproduce the exact same dataset list
    as the module's own frozen DATASETS constant (dataset_registry.CORE14 is
    a byte-identical copy) -- existing tracked result JSONs depend on this."""
    from dataset_registry import get_datasets
    assert [s["did"] for s in get_datasets("core14")] == [s["did"] for s in fm.DATASETS]


def test_grid_flag_extended30_adds_16_more_datasets():
    from dataset_registry import get_datasets
    extended = get_datasets("extended30")
    assert len(extended) == len(fm.DATASETS) + 16
    core_ids = {s["did"] for s in fm.DATASETS}
    assert core_ids.issubset({s["did"] for s in extended})
