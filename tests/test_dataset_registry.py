"""Tests for the shared dataset_registry module (EXPANSION-PLAN-2026-07-09
§2.2, deliverable 3: "Dataset grid 14->~30"). Offline, no network -- these
tests check the registry's static structure and the --grid plumbing, not
live OpenML metadata (that was verified manually against real OpenML data
while building the registry; see the executor's report for the scan output).
"""
import argparse

import pytest

import dataset_registry as reg


def test_core14_matches_frozen_dataset_ids():
    """CORE14 must reproduce the exact 14 dataset ids used by the already-
    tracked result JSONs -- reordering or dropping any of these would silently
    break reproducibility of existing headline numbers."""
    expected_ids = [151, 188, 1590, 6332, 40701, 41021, 41162, 41540,
                    42563, 42727, 42728, 42729, 42731, 42732]
    assert [s["did"] for s in reg.CORE14] == expected_ids
    assert len(reg.CORE14) == 14


def test_extended16_adds_16_new_ids_no_overlap_with_core14():
    core_ids = {s["did"] for s in reg.CORE14}
    ext_ids = {s["did"] for s in reg.EXTENDED16}
    assert len(reg.EXTENDED16) == 16
    assert core_ids.isdisjoint(ext_ids)


def test_every_spec_has_required_fields():
    for spec in reg.CORE14 + reg.EXTENDED16:
        assert set(spec) == {"did", "name", "key", "kind"}
        assert spec["kind"] in ("group", "time")
        assert isinstance(spec["did"], int)
        assert spec["name"] and spec["key"]


def test_get_datasets_core14_default():
    ds = reg.get_datasets("core14")
    assert len(ds) == 14
    assert [s["did"] for s in ds] == [s["did"] for s in reg.CORE14]


def test_get_datasets_extended30_is_union():
    ds = reg.get_datasets("extended30")
    assert len(ds) == 30
    ids = {s["did"] for s in ds}
    assert ids == {s["did"] for s in reg.CORE14} | {s["did"] for s in reg.EXTENDED16}


def test_get_datasets_returns_fresh_copies_not_shared_refs():
    a = reg.get_datasets("core14")
    a[0]["name"] = "MUTATED"
    b = reg.get_datasets("core14")
    assert b[0]["name"] != "MUTATED"


def test_get_datasets_unknown_grid_raises():
    with pytest.raises(ValueError):
        reg.get_datasets("nope")


def test_add_grid_arg_wires_argparse_default_core14():
    parser = argparse.ArgumentParser()
    reg.add_grid_arg(parser)
    args = parser.parse_args([])
    assert args.grid == "core14"
    args2 = parser.parse_args(["--grid", "extended30"])
    assert args2.grid == "extended30"


def test_add_grid_arg_rejects_invalid_choice():
    parser = argparse.ArgumentParser()
    reg.add_grid_arg(parser)
    with pytest.raises(SystemExit):
        parser.parse_args(["--grid", "bogus"])
