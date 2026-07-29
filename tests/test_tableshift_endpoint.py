"""Offline unit test for the frozen evaluability + endpoint rule in
tableshift_registry.py (PREREG-REMEDY-EVAL-2026-07-13 §1, AMENDED 2026-07-15).

Resolves G0_RECORD.md Caveat-1: TableShift `ood_test` is often single-domain, so
the keyed-OpenML worst-group endpoint does not transfer 1:1. `classify_endpoint`
assigns each task exactly one frozen endpoint decidable from the loaded bundle.
These tests exercise all three branches (primary / fallback / EXCLUDED-BY-RULE)
plus the deterministic first-present secondary-column selection, on synthetic
bundles -- no TableShift install, no network, no download.
"""
import numpy as np
import pandas as pd

import tableshift_registry as T


def _bundle(name, group_ood, X_ood=None):
    return {"name": name, "group_ood": np.asarray(group_ood), "X_ood": X_ood}


def test_primary_when_ood_has_three_plus_domain_groups():
    """>= MIN_GROUPS domain groups each >= MIN_GROUP rows -> primary worst-group."""
    grp = np.repeat(["a", "b", "c"], T.MIN_GROUP)   # 3 groups x MIN_GROUP rows
    ep = T.classify_endpoint(_bundle("acsincome", grp))
    assert ep["endpoint"] == "primary_worst_group_domain"
    assert ep["grouping"] == "ood_domain"
    assert ep["n_groups"] == 3
    assert ep["evaluable"] is True
    assert ep["excluded_by_rule"] is False


def test_domain_group_below_min_rows_does_not_count():
    """A domain group with < MIN_GROUP rows is not evaluable; with only 2 full
    groups + 1 undersized, the primary branch must not fire."""
    grp = np.array(["a"] * T.MIN_GROUP + ["b"] * T.MIN_GROUP + ["c"] * (T.MIN_GROUP - 1))
    # no secondary column supplied -> falls through to EXCLUDED-BY-RULE
    ep = T.classify_endpoint(_bundle("acsincome", grp, X_ood=pd.DataFrame({"foo": range(len(grp))})))
    assert ep["endpoint"] != "primary_worst_group_domain"
    assert ep["n_domain_groups"] == 2


def test_fallback_secondary_group_on_single_domain():
    """Single-domain ood_test but a frozen secondary column (RAC1P) is present and
    evaluable -> fallback endpoint keyed on that column."""
    n = T.MIN_GROUP * 3
    grp = np.array(["only_domain"] * n)             # single domain -> primary unavailable
    X_ood = pd.DataFrame({
        "RAC1P": np.repeat([1, 2, 3], T.MIN_GROUP),  # 3 evaluable secondary groups
        "DIVISION": np.arange(n),                    # domain key, never a candidate
    })
    ep = T.classify_endpoint(_bundle("acsincome", grp, X_ood))
    assert ep["endpoint"] == "fallback_marginal_gap_plus_secondary_group"
    assert ep["grouping"] == "RAC1P"
    assert ep["n_groups"] == 3
    assert ep["excluded_by_rule"] is False


def test_secondary_selection_is_first_present_evaluable():
    """RAC1P absent -> deterministically fall to the next frozen candidate (SEX)."""
    n = T.MIN_GROUP * 3
    grp = np.array(["only_domain"] * n)
    X_ood = pd.DataFrame({
        "SEX": np.repeat([1, 2, 3], T.MIN_GROUP),    # SEX is 2nd in the frozen list
    })
    col, n_ok = T.select_secondary_group(X_ood, T.SECONDARY_GROUP_CANDIDATES["acsincome"])
    assert col == "SEX" and n_ok == 3
    ep = T.classify_endpoint(_bundle("acsincome", grp, X_ood))
    assert ep["grouping"] == "SEX"


def test_excluded_by_rule_when_single_domain_and_no_secondary():
    """Single-domain ood_test AND no evaluable secondary column -> EXCLUDED-BY-RULE
    (only a marginal gap is available; no group-conditional worst-group content)."""
    n = T.MIN_GROUP * 3
    grp = np.array(["only_domain"] * n)
    X_ood = pd.DataFrame({"RAC1P": np.zeros(n, dtype=int)})  # 1 secondary level only
    ep = T.classify_endpoint(_bundle("acsincome", grp, X_ood))
    assert ep["endpoint"] == "marginal_gap_only"
    assert ep["grouping"] is None
    assert ep["evaluable"] is False
    assert ep["excluded_by_rule"] is True


def test_domain_split_key_never_a_secondary_candidate():
    """No task lists its own domain-split key among its secondary candidates."""
    for task, meta in T.OPEN_TASKS.items():
        assert meta["key"] not in T.SECONDARY_GROUP_CANDIDATES.get(task, [])


def test_every_open_task_has_a_frozen_candidate_list():
    assert set(T.SECONDARY_GROUP_CANDIDATES) == set(T.OPEN_TASKS)
