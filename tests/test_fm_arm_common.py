"""Tests for fm_arm_common.py, the pipeline shared by the TabDPT and
TabPFN-2.5 FM arms (EXPANSION-PLAN-2026-07-09 §2.2, deliverable 2). This is a
straight port of nd1_tabicl_fm_arm_leakage_ablation.py's own already-tested
logic (see tests/test_fm_leakage_ablation.py), parametrized over
fit_predict_fn/get_cal_proba_fn; these tests re-check the same invariants
against the shared, model-agnostic module.
"""
import json
import os

import numpy as np
import pandas as pd
import pytest

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
        unc = 1.0 - proba.max(1)
        return pred, proba, unc
    else:
        pt = np.full(n, float(np.mean(ytr)))
        lo = pt - 1.0
        hi = pt + 1.0
        return pt, (lo, hi), hi - lo


def _stub_get_cal_proba(Xfit, yfit, Xcal, task, nclass=None):
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


def test_make_rng_for_deterministic_and_context_dependent():
    rng_for = common.make_rng_for(0)
    a = rng_for(151, "split_random").randint(10 ** 9)
    b = rng_for(151, "split_random").randint(10 ** 9)
    c = rng_for(151, "split_grouped").randint(10 ** 9)
    assert a == b
    assert a != c


def test_make_rng_for_repeat_k_changes_stream():
    rng0 = common.make_rng_for(0, 0)
    rngk = common.make_rng_for(0, 5)
    assert rng0(1, "x").randint(10 ** 9) != rngk(1, "x").randint(10 ** 9)


def test_grouped_split_fold_blocked():
    rng = np.random.RandomState(0)
    groups = rng.randint(0, 10, size=400).astype(str)
    rng_for = common.make_rng_for(0)
    tr_mask, te_mask = common.make_grouped_split(groups, rng_for("t", "grp"))
    assert set(groups[tr_mask]).isdisjoint(set(groups[te_mask]))


def test_audit_dataset_excludes_key_column_end_to_end(monkeypatch):
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
        y = pd.Series(((a) > 0).astype(int))
        return None, X, y, "y"

    rng_for = common.make_rng_for(0)
    spec = {"did": -9999, "name": "fixture", "key": "grp", "kind": "group"}

    r_incl = common.audit_dataset(spec, False, rng_for, _stub_fit_predict,
                                  _stub_get_cal_proba, "stub",
                                  load_dataset_fn=fake_load_dataset)
    assert r_incl["status"] == "ok"
    assert any("grp" in cols for cols in seen_columns)

    seen_columns.clear()
    r_excl = common.audit_dataset(spec, True, rng_for, _stub_fit_predict,
                                  _stub_get_cal_proba, "stub",
                                  load_dataset_fn=fake_load_dataset)
    assert r_excl["status"] == "ok"
    assert all("grp" not in cols for cols in seen_columns)
    assert r_excl["exclude_key"] is True


def test_load_gbm_reference_parses_expected_shape(tmp_path):
    fixture = {"results": [
        {"status": "ok", "name": "adult",
         "conformal_cov_grouped": 0.81, "repair_ratio_grouped": 0.63},
        {"status": "skip", "name": "broken"},
    ]}
    path = tmp_path / "stage1.json"
    path.write_text(json.dumps(fixture))
    ref = common.load_gbm_reference(str(path))
    assert ref == {"adult": {"cov_grouped": 0.81, "repair_grouped": 0.63}}


def test_load_gbm_reference_missing_file_returns_empty(tmp_path):
    assert common.load_gbm_reference(str(tmp_path / "nope.json")) == {}


def test_main_run_end_to_end_schema_and_full_coverage_flag(tmp_path):
    specs, frames = common.make_synthetic_datasets(n=300, seed=0)

    def fake_load_dataset(did):
        X, y = frames[did]
        return None, X, y, "y"

    rng_for = common.make_rng_for(0)

    def audit_fn(spec, exclude_key):
        return common.audit_dataset(spec, exclude_key, rng_for, _stub_fit_predict,
                                    _stub_get_cal_proba, "stub-model",
                                    load_dataset_fn=fake_load_dataset)

    out_path = str(tmp_path / "fm_out.json")
    out = common.main_run(
        specs, exclude_key=False, gbm_ref_path=str(tmp_path / "missing.json"),
        out_path=out_path, gate="test gate", model_label="stub-model",
        rng_discipline="test", script_path=__file__, write=True,
        audit_dataset_fn=audit_fn)

    for key in ("gate", "model", "n_ok", "n_attempted", "results",
               "gbm_reference_xgb_stage1", "rng_discipline", "provenance",
               "full_coverage"):
        assert key in out
    assert out["full_coverage"] is True
    assert out["gbm_reference_xgb_stage1"] == {}
    assert os.path.exists(out_path)
    reloaded = json.load(open(out_path))
    assert reloaded["n_attempted"] == len(specs)


def test_main_run_full_coverage_false_on_skip(tmp_path):
    specs, frames = common.make_synthetic_datasets(n=300, seed=0)
    specs = specs + [{"did": -3000, "name": "will_skip", "key": "nope", "kind": "group"}]

    def fake_load_dataset(did):
        if did == -3000:
            return None, pd.DataFrame({"a": [1, 2, 3]}), pd.Series([0, 1, 0]), "y"
        X, y = frames[did]
        return None, X, y, "y"

    rng_for = common.make_rng_for(0)

    def audit_fn(spec, exclude_key):
        return common.audit_dataset(spec, exclude_key, rng_for, _stub_fit_predict,
                                    _stub_get_cal_proba, "stub-model",
                                    load_dataset_fn=fake_load_dataset)

    out_path = str(tmp_path / "fm_out2.json")
    out = common.main_run(
        specs, exclude_key=False, gbm_ref_path=str(tmp_path / "missing.json"),
        out_path=out_path, gate="test gate", model_label="stub-model",
        rng_discipline="test", script_path=__file__, write=True,
        audit_dataset_fn=audit_fn)

    assert out["full_coverage"] is False
    assert out["n_ok"] == 1
    assert out["n_skipped"] == 1
    assert "will_skip" in out["skipped_names"]
