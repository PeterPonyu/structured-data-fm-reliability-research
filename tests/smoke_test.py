"""Smoke test: fast (<2 min), offline, no network, no result-JSON mutation.

Checks three things:
  1. The core analysis modules import (incl. the local relmetrics package).
  2. The Stage-1 audit pipeline (run_split: XGBoost fit -> AURC ->
     split-conformal coverage) runs end-to-end on a tiny synthetic fixture.
  3. The tracked result JSONs parse and contain their expected top-level keys.

It deliberately does NOT import the GPU/FM modules (nd1_tabicl_fm_arm*,
nd2_mini_spike): those pull torch/tabicl/tabpfn_time_series and are covered by
their own frozen result JSONs (checked in part 3).

Run via ./smoke_test.sh (uses the conda env that produced the results).
"""
import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "experiments"))

FAILURES = []


def check(name, fn):
    try:
        fn()
        print(f"  ok    {name}")
    except Exception as e:
        print(f"  FAIL  {name}: {type(e).__name__}: {e}")
        FAILURES.append(name)


# ---------------------------------------------------------------- 1. imports
print("[1/3] importing core analysis modules")
CORE_MODULES = [
    "census_openml_groupkeys",
    "census_verify_groupkeys",
    "nd1_split_conditioned_audit",
    "nd1_s2_lightgbm_mondrian",
    "nd1_s2_p4_calsize_diag",
    "p4_tableshift",
]
for m in CORE_MODULES:
    check(f"import {m}", lambda m=m: importlib.import_module(m))

check("import relmetrics (multiplicity + provenance)", lambda: (
    importlib.import_module("relmetrics.multiplicity"),
    importlib.import_module("relmetrics.provenance")))


# ------------------------------------------------- 2. tiny functional fixture
print("[2/3] running Stage-1 run_split on a synthetic fixture")


def fixture_run():
    import numpy as np
    import pandas as pd
    import nd1_split_conditioned_audit as s1

    rng = np.random.RandomState(0)
    n = 400
    X = pd.DataFrame({
        "a": rng.normal(size=n),
        "b": rng.normal(size=n),
        "c": rng.randint(0, 5, size=n).astype(float),
    })
    # learnable binary target with noise
    y = ((X["a"] + 0.5 * X["b"] + 0.3 * rng.normal(size=n)) > 0).astype(int).values

    tr = np.zeros(n, dtype=bool); tr[:300] = True
    te = ~tr
    res = s1.run_split(X, y, "clf", 2, tr, te, s1.rng_for("smoke", "cal"))
    assert res is not None, "run_split returned None on a valid fixture"
    a = s1.aurc(res["loss"], res["unc"])
    a_rand = s1.aurc_random_defer(res["loss"])
    assert np.isfinite(a) and 0.0 <= a <= 1.0, f"AURC out of range: {a}"
    assert np.isfinite(a_rand), f"random-defer AURC not finite: {a_rand}"
    assert 0.0 <= res["cov"] <= 1.0, f"conformal coverage out of [0,1]: {res['cov']}"
    # determinism of the per-context RNG discipline (2026-07-02 fix)
    r1 = s1.rng_for(151, "split").randint(10**9)
    r2 = s1.rng_for(151, "split").randint(10**9)
    assert r1 == r2, "rng_for is not deterministic per context"
    # multiplicity helpers behave sanely
    from relmetrics.multiplicity import holm_bonferroni
    hb = holm_bonferroni([0.001, 0.5, 0.04], alpha=0.05)
    assert not hb["reject"][1], "Holm rejected an obviously null p=0.5"
    assert hb["reject"][0], "Holm failed to reject p=0.001 in a family of 3"


check("run_split + aurc + conformal coverage on fixture", fixture_run)


# ------------------------------------------------------- 3. result JSON shape
print("[3/3] validating tracked result JSONs parse with expected keys")
RESULTS = os.path.join(REPO, "experiments", "results")
EXPECTED = {
    "nd1_split_conditioned_audit.json": ["gate", "model", "n_datasets_ok",
                                         "n_grouped_reliability_gap_ci_excl0"],
    "nd1_split_conditioned_audit_keyexcluded.json": ["gate", "model",
                                                     "n_datasets_ok"],
    "nd1_s2_lightgbm_mondrian.json": ["gate", "models", "per_model_summary",
                                      "pooled_mondrian", "verdict"],
    "nd1_s2_lightgbm_mondrian_keyexcluded.json": ["gate", "models", "verdict"],
    "nd1_s2_p4_calsize_diag.json": ["diagnostic", "hypothesis", "models"],
    "nd1_tabicl_fm_arm_full14.json": ["gate", "model", "n_ok",
                                      "n_aurc_degrade_ci_excl0"],
    "nd1_tabicl_fm_arm.json": ["gate", "model", "n_ok"],
    "p4_tableshift_result.json": ["experiment", "benchmark", "tasks",
                                  "ood_axis"],
    "census_final_triage.json": ["gate", "verdict"],
    "openml_groupkey_census.json": ["n_qualifying", "verdict"],
    "openml_groupkey_census_verified.json": ["n_qualifying", "verdict"],
}


def json_check(fname, keys):
    path = os.path.join(RESULTS, fname)
    with open(path) as fh:
        d = json.load(fh)
    missing = [k for k in keys if k not in d]
    assert not missing, f"missing top-level keys {missing}"


for fname, keys in EXPECTED.items():
    check(fname, lambda f=fname, k=keys: json_check(f, k))

# -----------------------------------------------------------------------------
if FAILURES:
    print(f"\nSMOKE TEST FAILED ({len(FAILURES)}): {FAILURES}")
    sys.exit(1)
print("\nSMOKE TEST PASSED")
