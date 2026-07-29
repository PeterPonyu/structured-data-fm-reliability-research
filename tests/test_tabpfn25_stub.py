"""Tests for the TabPFN-2.5 arm's TABPFN_TOKEN guard (NEXT-EXPERIMENTS.md
item 5 / EXPANSION-PLAN-2026-07-09 §2.2 deliverable 2:
experiments/nd1_tabpfn25_arm.py). Verifies the REQUIRES_USER_TOKEN guard
refuses to run without TABPFN_TOKEN. The audit body itself (now implemented,
gated behind this same guard) is tested with the real tabpfn calls stubbed
out in tests/test_tabpfn25_arm.py -- this file only covers the guard, which
must keep behaving identically now that the body past it is real code, not a
NotImplementedError stub.
"""
import pytest

import nd1_tabpfn25_arm as stub


def test_requires_user_token_flag_present():
    assert stub.REQUIRES_USER_TOKEN is True


def test_guard_fails_without_token(monkeypatch, capsys):
    monkeypatch.delenv("TABPFN_TOKEN", raising=False)
    assert stub.check_token_guard() is False
    err = capsys.readouterr().err
    assert "TABPFN_TOKEN" in err
    assert "REQUIRES_USER_TOKEN" in err


def test_guard_passes_with_token(monkeypatch):
    monkeypatch.setenv("TABPFN_TOKEN", "fake-token-for-test")
    assert stub.check_token_guard() is True


def test_main_exits_nonzero_without_token(monkeypatch):
    monkeypatch.delenv("TABPFN_TOKEN", raising=False)
    with pytest.raises(SystemExit) as exc:
        stub.main()
    assert exc.value.code == 1
