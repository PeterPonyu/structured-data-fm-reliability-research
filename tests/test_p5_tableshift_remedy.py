"""Offline synthetic tests for p5_tableshift_remedy.py (PREREG-REMEDY-EVAL-
2026-07-13, confirmatory TableShift arm). No TableShift install, no network,
no box -- exercises the p5-specific logic on synthetic bundles shaped like
`tableshift_registry.load_task`'s return contract:

  - endpoint dispatch: primary / fallback / excluded-by-rule routing through
    `_run_one_k` (group-conditional remedy ladder vs descriptive-only path)
  - remedy application: the ladder runs and produces a sane restores_coverage
    decision on synthetic data
  - MAX_ROWS row-cap subsampling
  - marginal id-vs-ood coverage-gap arithmetic
  - H1/H2 tally arithmetic: summarize_at_k, build_aggregate (majority, min-
    across-k, verdict + venue mapping), multiplicity attachment
  - roster determination (kaggle-gated exclusion)

`tests/test_tableshift_endpoint.py` already covers `classify_endpoint` itself
in isolation; this file reuses it (frozen, untouched) to drive p5's dispatch.
"""
import os
import numpy as np
import pandas as pd

import p5_tableshift_remedy as P5
import tableshift_registry as T

RNG = np.random.RandomState(0)


# ---------------------------------------------------------------------------
# synthetic bundle builder (mirrors tableshift_registry.load_task's schema)
# ---------------------------------------------------------------------------
def _make_bundle(name, task_type="clf", n_id=300, n_ood_groups=None, key="dom_key",
                 secondary_col=None, secondary_levels=3, rng=None):
    rng = rng or np.random.RandomState(0)

    def _make_X(n, dom_labels):
        d = {"num1": rng.normal(size=n), "num2": rng.normal(size=n),
             "cat1": rng.choice(["a", "b", "c"], size=n)}
        d[key] = dom_labels
        if secondary_col:
            d[secondary_col] = rng.choice(np.arange(secondary_levels), size=n)
        return pd.DataFrame(d)

    def _make_y(n):
        return pd.Series(rng.choice([0, 1], size=n) if task_type == "clf"
                         else rng.normal(size=n))

    X_id = _make_X(n_id, np.array(["train_dom"] * n_id))
    y_id = _make_y(n_id)

    n_ood_groups = n_ood_groups or [30, 30, 30]
    dom_ood = np.concatenate([[f"g{i}"] * s for i, s in enumerate(n_ood_groups)])
    X_ood = _make_X(len(dom_ood), dom_ood)
    y_ood = _make_y(len(dom_ood))

    return {"name": name, "X_id": X_id, "y_id": y_id, "X_ood": X_ood, "y_ood": y_ood,
            "group_ood": dom_ood, "task_type": task_type, "key": key,
            "axis": "domain", "n_features": X_id.shape[1], "n_id": n_id,
            "n_ood": len(dom_ood), "n_ood_groups": len(set(dom_ood))}


# ---------------------------------------------------------------------------
# endpoint dispatch through _run_one_k
# ---------------------------------------------------------------------------
def test_primary_endpoint_runs_group_conditional_ladder():
    """3 ood domain groups >= MIN_GROUP -> primary endpoint -> remedies ladder
    runs, best_remedy selected, selective comparison present."""
    bundle = _make_bundle("synthetic_primary", n_ood_groups=[25, 25, 25])
    decision = T.classify_endpoint(bundle)
    assert decision["endpoint"] == "primary_worst_group_domain"
    r = P5._run_one_k(bundle, decision, (None, None), k=0)
    assert r["status"] == "ok"
    assert r["remedies"] is not None
    assert set(r["remedies"]) == {"split_conformal", "weighted_cp", "mondrian_inferred", "mondrian_unc_decile"}
    assert r["best_remedy"] in ("weighted_cp", "mondrian_inferred", "mondrian_unc_decile")
    for nm, rec in r["remedies"].items():
        assert 0.0 <= rec["worst_cov"] <= 1.0
        assert isinstance(rec["restores_coverage"], bool)
        if nm != "split_conformal":
            assert "gap_reduction_p_one_sided" in rec
            assert 0.0 <= rec["gap_reduction_p_one_sided"] <= 1.0
    assert r["selective"] is not None
    assert r["selective"]["head_to_head"] in (
        "uncertainty_wins", "tie", "tuned_wins", "selector_degenerate")


def test_excluded_endpoint_is_descriptive_only_not_group_conditional():
    """Single ood domain, no evaluable secondary column for this task name ->
    EXCLUDED-BY-RULE -> no remedy ladder, no selective eval, marginal cov only."""
    bundle = _make_bundle("synthetic_excluded_task", n_ood_groups=[90])
    decision = T.classify_endpoint(bundle)
    assert decision["endpoint"] == "marginal_gap_only"
    assert decision["excluded_by_rule"] is True
    r = P5._run_one_k(bundle, decision, (None, None), k=0)
    assert r["status"] == "ok"
    assert r["remedies"] is None
    assert r["best_remedy"] is None
    assert r["selective"] is None
    assert 0.0 <= r["descriptive_marginal_cov_split_conformal"] <= 1.0


def test_fallback_endpoint_uses_secondary_grouping_column():
    """Single ood domain but a frozen secondary column (RAC1P, via a real
    task's candidate list) is present and evaluable -> fallback endpoint ->
    remedy ladder runs, grouped by the secondary column."""
    bundle = _make_bundle("acsincome", n_ood_groups=[90],
                          secondary_col="RAC1P", secondary_levels=3)
    decision = T.classify_endpoint(bundle)
    assert decision["endpoint"] == "fallback_marginal_gap_plus_secondary_group"
    assert decision["grouping"] == "RAC1P"
    r = P5._run_one_k(bundle, decision, (None, None), k=0)
    assert r["status"] == "ok"
    assert r["remedies"] is not None
    assert r["selective"] is not None


def test_regression_task_type_dispatches_through_excluded_path():
    """Regression variant of the excluded path -- covers the non-clf branch of
    the marginal-only descriptive computation."""
    bundle = _make_bundle("synthetic_reg_excluded", task_type="reg", n_ood_groups=[90])
    decision = T.classify_endpoint(bundle)
    assert decision["excluded_by_rule"] is True
    r = P5._run_one_k(bundle, decision, (None, None), k=0)
    assert r["status"] == "ok"
    assert r["remedies"] is None
    assert 0.0 <= r["descriptive_marginal_cov_split_conformal"] <= 1.0


# ---------------------------------------------------------------------------
# MAX_ROWS subsampling
# ---------------------------------------------------------------------------
def test_max_rows_cap_subsamples_id_and_ood(monkeypatch):
    monkeypatch.setattr(P5, "MAX_ROWS", 100)
    bundle = _make_bundle("synthetic_cap", n_id=400, n_ood_groups=[80, 80, 80])
    decision = T.classify_endpoint(bundle)
    r = P5._run_one_k(bundle, decision, (None, None), k=0)
    assert r["status"] == "ok"
    assert r["n_id_used"] <= 100
    assert r["n_ood_used"] <= 100
    assert r["n_ood_full"] == 240


# ---------------------------------------------------------------------------
# marginal id-vs-ood coverage gap arithmetic
# ---------------------------------------------------------------------------
def test_marginal_gap_arithmetic_when_id_test_available():
    bundle = _make_bundle("synthetic_idtest", n_ood_groups=[25, 25, 25])
    decision = T.classify_endpoint(bundle)
    rng = np.random.RandomState(1)
    n_idt = 120
    X_idt = pd.DataFrame({
        "num1": rng.normal(size=n_idt), "num2": rng.normal(size=n_idt),
        "cat1": rng.choice(["a", "b", "c"], size=n_idt),
        "dom_key": ["train_dom"] * n_idt,
    })
    y_idt = pd.Series(rng.choice([0, 1], size=n_idt))
    r = P5._run_one_k(bundle, decision, (X_idt, y_idt), k=0)
    assert r["status"] == "ok"
    mg = r["marginal_gap"]
    assert mg is not None
    assert set(mg) == {"cov_id_test", "cov_ood_test", "gap", "n_id_test"}
    assert abs((mg["cov_id_test"] - mg["cov_ood_test"]) - mg["gap"]) < 2e-4  # rounded to 4dp
    assert 0.0 <= mg["cov_id_test"] <= 1.0 and 0.0 <= mg["cov_ood_test"] <= 1.0


def test_marginal_gap_is_none_when_id_test_unavailable():
    bundle = _make_bundle("synthetic_noidtest", n_ood_groups=[25, 25, 25])
    decision = T.classify_endpoint(bundle)
    r = P5._run_one_k(bundle, decision, (None, "SomeError: not found"), k=0)
    assert r["marginal_gap"] is None


# ---------------------------------------------------------------------------
# H1/H2 tally arithmetic
# ---------------------------------------------------------------------------
def _fake_task_result(worst_cov_restores, head_to_head, selector_ok=True):
    remedy_names = ["weighted_cp", "mondrian_inferred", "mondrian_unc_decile"]
    remedies = {"split_conformal": {"worst_cov": 0.70, "gap": 0.20}}
    for nm in remedy_names:
        remedies[nm] = {"worst_cov": 0.88, "gap": 0.02,
                        "restores_coverage": bool(worst_cov_restores.get(nm, False))}
    selective = {"selector_ok": selector_ok, "head_to_head": head_to_head,
                "uncertainty_ties_or_beats_tuned": head_to_head != "tuned_wins" and selector_ok}
    return {"status": "ok", "remedies": remedies, "best_remedy": "mondrian_inferred",
           "selective": selective}


def test_summarize_at_k_majority_arithmetic():
    evaluable = ["t1", "t2", "t3"]
    task_results_k = {
        "t1": _fake_task_result({"weighted_cp": True}, "uncertainty_wins"),
        "t2": _fake_task_result({}, "tie"),
        "t3": _fake_task_result({}, "tuned_wins"),
    }
    s = P5.summarize_at_k(task_results_k, evaluable)
    assert s["n_ok"] == 3
    assert s["majority_threshold"] == 2
    assert s["n_tasks_remedy_restores_coverage"]["weighted_cp"] == 1
    assert s["n_tasks_any_remedy_restores"] == 1
    # t1 (uncertainty_wins) and t2 (tie) tie-or-beat; t3 (tuned_wins) does not
    assert s["n_uncertainty_ties_or_beats_tuned"] == 2
    assert s["h2h"]["tuned_wins"] == 1


def test_build_aggregate_h1_confirm_majority_at_min_across_k():
    """H1 CONFIRMs only if the any-remedy-restores count clears majority at
    the MIN across k (prereg: 'holds at the min across all K=20 repeats')."""
    evaluable = ["t1", "t2", "t3"]
    # k=0: 2/3 restore (majority); k=1: only 1/3 restores -> min fails majority
    per_k_summaries = [
        {"n_ok": 3, "n_tasks_any_remedy_restores": 2, "n_uncertainty_ties_or_beats_tuned": 3,
         "median_split_conformal_worst_group_cov": 0.7, "median_split_conformal_group_gap": 0.2,
         "n_tasks_remedy_restores_coverage": {"weighted_cp": 2, "mondrian_inferred": 0, "mondrian_unc_decile": 0}},
        {"n_ok": 3, "n_tasks_any_remedy_restores": 1, "n_uncertainty_ties_or_beats_tuned": 3,
         "median_split_conformal_worst_group_cov": 0.68, "median_split_conformal_group_gap": 0.22,
         "n_tasks_remedy_restores_coverage": {"weighted_cp": 1, "mondrian_inferred": 0, "mondrian_unc_decile": 0}},
    ]
    agg = P5.build_aggregate(per_k_summaries, evaluable, [], [], kmax_completed=2)
    assert agg["majority_threshold"] == 2
    assert agg["n_any_remedy_restores_coverage"]["min"] == 1
    assert agg["H1_verdict"] == "REJECT"          # min (1) < majority (2)
    assert agg["H2_verdict"] == "CONFIRM"         # min (3) >= majority (2)
    assert "DMKD" in agg["venue_read"]


def test_build_aggregate_h1_confirm_when_min_clears_majority():
    evaluable = ["t1", "t2", "t3"]
    per_k_summaries = [
        {"n_ok": 3, "n_tasks_any_remedy_restores": 2, "n_uncertainty_ties_or_beats_tuned": 2,
         "median_split_conformal_worst_group_cov": 0.7, "median_split_conformal_group_gap": 0.2,
         "n_tasks_remedy_restores_coverage": {"weighted_cp": 2, "mondrian_inferred": 0, "mondrian_unc_decile": 0}},
        {"n_ok": 3, "n_tasks_any_remedy_restores": 3, "n_uncertainty_ties_or_beats_tuned": 3,
         "median_split_conformal_worst_group_cov": 0.71, "median_split_conformal_group_gap": 0.19,
         "n_tasks_remedy_restores_coverage": {"weighted_cp": 3, "mondrian_inferred": 0, "mondrian_unc_decile": 0}},
    ]
    agg = P5.build_aggregate(per_k_summaries, evaluable, [], [], kmax_completed=2)
    assert agg["H1_verdict"] == "CONFIRM"
    assert "Machine Learning" in agg["venue_read"]


def test_build_aggregate_no_evaluable_tasks_is_safe():
    agg = P5.build_aggregate([], [], ["excl1"], ["missing1"], kmax_completed=0)
    assert agg["n_evaluable_tasks"] == 0
    assert agg["H1_verdict"] == "REJECT"
    assert agg["H2_verdict"] == "REJECT"


# ---------------------------------------------------------------------------
# multiplicity correction attachment (§3, supplementary layer)
# ---------------------------------------------------------------------------
def test_attach_multiplicity_flags_strong_signal_and_spares_weak():
    agg = {}
    p_gap = {"t1": 0.001, "t2": 0.02, "t3": 0.9}
    p_repair = {"t1": 0.5}
    P5._attach_multiplicity(agg, p_gap, p_repair)
    fam = agg["multiplicity_k0"]["gap_reduction"]
    assert set(fam) == {"t1", "t2", "t3"}
    assert fam["t1"]["reject_holm"] is True     # strong raw p survives correction
    assert fam["t3"]["reject_holm"] is False    # p=0.9 never rejects
    assert fam["t1"]["p_holm"] >= fam["t1"]["p_raw"]   # Holm adjustment only inflates
    assert "repair_ratio" in agg["multiplicity_k0"]
    assert set(agg["multiplicity_k0"]["repair_ratio"]) == {"t1"}


def test_attach_multiplicity_empty_families_omitted():
    agg = {}
    P5._attach_multiplicity(agg, {}, {})
    assert agg["multiplicity_k0"] == {}


# ---------------------------------------------------------------------------
# roster determination (kaggle-gated exclusion, prereg 2026-07-15 amendment)
# ---------------------------------------------------------------------------
def test_determine_roster_excludes_kaggle_gated_tasks():
    roster = P5.determine_roster(reachability_path=None)
    assert len(roster) == 9
    assert "assistments" not in roster
    assert "college_scorecard" not in roster
    assert set(roster) == set(T.OPEN_TASKS) - P5.KNOWN_KAGGLE_GATED


def test_determine_roster_falls_back_when_reachability_path_missing():
    roster = P5.determine_roster(reachability_path="/nonexistent/path/reachability.json")
    assert len(roster) == 9
    assert "assistments" not in roster and "college_scorecard" not in roster


def test_determine_roster_reads_reachability_record(tmp_path):
    import json
    rec = {t: {"status": "reached"} for t in T.OPEN_TASKS}
    rec["nhanes_lead"] = {"status": "gated_kaggle_token"}
    rec["assistments"] = {"status": "gated_kaggle_token"}
    p = tmp_path / "reachability.json"
    p.write_text(json.dumps(rec))
    roster = P5.determine_roster(reachability_path=str(p))
    assert "nhanes_lead" not in roster
    assert "assistments" not in roster
    # college_scorecard is NOT marked gated in this synthetic record -> the
    # box-record content wins over the hardcoded default (freshest signal)
    assert "college_scorecard" in roster
