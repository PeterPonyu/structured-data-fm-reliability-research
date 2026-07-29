"""Tests for the K-repeated-folds arm (NEXT-EXPERIMENTS.md item 1).

NOTE on scope: this arm was already implemented and executed (K=30 Stage-1 /
K=20 Stage-2, both feature conditions -- see
experiments/results/split_repeats/ and
experiments/results/findings-split-repeats-2026-07-02.md) BEFORE this test
suite was written; NEXT-EXPERIMENTS.md itself is stale on this point (it still
lists item 1 as "Still deferred" / "TOP item", but the per-k JSONs, the
aggregate JSON, and the findings memo are all on disk and git-committed --
`git log` shows commits 6563301 / 5cc79bf implementing and reporting it). These
tests exercise the arm's core logic (the `rng_for` per-context RNG derivation
and the aggregate script's fold-blocking-aware statistics) on synthetic data;
they do not re-run the real 100-JSON sweep.

Fast, offline, no GPU, no network.
"""
import importlib
import os

import numpy as np
import pytest

import nd1_split_conditioned_audit as s1
import nd1_split_repeats_aggregate as agg


def test_rng_for_deterministic_same_context():
    r1 = s1.rng_for(151, "split_random")
    r2 = s1.rng_for(151, "split_random")
    assert r1.randint(10 ** 9) == r2.randint(10 ** 9)


def test_rng_for_differs_across_context():
    a = s1.rng_for(151, "split_random").randint(10 ** 9)
    b = s1.rng_for(151, "split_grouped").randint(10 ** 9)  # different purpose
    c = s1.rng_for(1590, "split_random").randint(10 ** 9)  # different did
    assert len({a, b, c}) == 3


def test_repeat_k_gives_independent_draws_but_k0_matches_baseline(monkeypatch):
    """k=0 must reproduce the tracked headline bit-for-bit (REPEAT_K unset ==
    REPEAT_K=0 by construction); k=1 must diverge. This is the exact invariant
    the split-repeats aggregate depends on (see PREDECL-split-repeats-2026-07-02.md
    "k = 0 leaves the key byte-identical to the reconciled single-draw code")."""
    monkeypatch.delenv("REPEAT_K", raising=False)
    baseline = importlib.reload(s1)
    base_draw = baseline.rng_for(151, "split_random").randint(10 ** 9)

    monkeypatch.setenv("REPEAT_K", "0")
    k0 = importlib.reload(s1)
    assert k0.SPLIT_REPEATS is True and k0.REPEAT_K == 0
    k0_draw = k0.rng_for(151, "split_random").randint(10 ** 9)
    assert k0_draw == base_draw, "k=0 must reproduce the baseline stream bit-for-bit"

    monkeypatch.setenv("REPEAT_K", "1")
    k1 = importlib.reload(s1)
    k1_draw = k1.rng_for(151, "split_random").randint(10 ** 9)
    assert k1_draw != base_draw, "k=1 must be an independent draw from k=0"

    # restore module state for any other test importing s1 in this session
    monkeypatch.delenv("REPEAT_K", raising=False)
    importlib.reload(s1)


def test_grouped_split_is_fold_blocked():
    """No group value may appear in both the train and test masks -- this is
    the invariant the whole leave-group-out protocol rests on."""
    rng = np.random.RandomState(0)
    groups = rng.randint(0, 12, size=500).astype(str)
    tr_mask, te_mask = s1.make_grouped_split(groups, s1.rng_for("test", "grp"))
    train_groups = set(groups[tr_mask])
    test_groups = set(groups[te_mask])
    assert train_groups.isdisjoint(test_groups)
    assert tr_mask.sum() + te_mask.sum() == len(groups)


def test_time_split_is_fold_blocked_and_future_only():
    """Rolling-origin: every test-fold timestamp must be >= every train-fold
    timestamp (no leakage of future information into training)."""
    timekey = np.arange(1000)
    tr_mask, te_mask = s1.make_time_split(timekey)
    assert timekey[tr_mask].max() < timekey[te_mask].min()


def _fake_per_k_dist_input():
    """Synthetic {k: count} fixture mimicking the aggregate script's inputs
    (n_grouped_reliability_gap_ci_excl0 style counts, out of 14)."""
    rng = np.random.RandomState(0)
    return {k: int(rng.randint(5, 13)) for k in range(10)}


def test_aggregate_dist_summary_schema_and_majority_logic():
    counts = _fake_per_k_dist_input()
    d = agg._dist(counts)
    for key in ("n_k", "median", "mean", "ci95_percentile", "min", "max",
               "frac_k_ge_majority", "majority_robust_p2p5_ge_8", "per_k"):
        assert key in d
    assert d["n_k"] == len(counts)
    assert d["min"] <= d["median"] <= d["max"]
    assert 0.0 <= d["frac_k_ge_majority"] <= 1.0
    # majority_robust_p2p5_ge_8 should be True iff the 2.5th percentile clears 8
    assert d["majority_robust_p2p5_ge_8"] == (d["ci95_percentile"][0] >= agg.MAJORITY)


def test_aggregate_flip_table_detects_split_stable_vs_sensitive_datasets():
    """A dataset flagged in every k is split-stable; one flagged in only some k
    is split-sensitive -- the flip-frequency table must distinguish them."""
    records_by_k = {}
    for k in range(6):
        records_by_k[k] = [
            {"did": 1, "name": "always_gap", "status": "ok",
             "aurc_delta_excludes0_degrade": True, "grouped_undercovers": False,
             "repair_excludes0_pos": True},
            {"did": 2, "name": "never_gap", "status": "ok",
             "aurc_delta_excludes0_degrade": False, "grouped_undercovers": False,
             "repair_excludes0_pos": True},
            {"did": 3, "name": "flips", "status": "ok",
             "aurc_delta_excludes0_degrade": bool(k % 2), "grouped_undercovers": False,
             "repair_excludes0_pos": True},
        ]
    tab = agg._flip_table(
        records_by_k,
        gap_flag=lambda r: r["aurc_delta_excludes0_degrade"] or r["grouped_undercovers"],
        repair_flag=lambda r: r["repair_excludes0_pos"])
    assert tab["always_gap"]["gap_flag_freq"] == 1.0
    assert tab["always_gap"]["gap_split_stable"] is True
    assert tab["never_gap"]["gap_flag_freq"] == 0.0
    assert tab["never_gap"]["gap_split_stable"] is True
    assert tab["flips"]["gap_flag_freq"] == 0.5
    assert tab["flips"]["gap_split_stable"] is False
