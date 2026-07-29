"""Tests for prefetch_checkpoints.py (EXPANSION-PLAN-2026-07-09 §2.2,
deliverable 1: "regression re-run enablement" -- warm BOTH TabICL
classifier+regressor checkpoints with content verification).

Fast, offline: `verify_checkpoint`'s size-band logic is tested against
synthetic tmp files (mocked-boundary). `test_verify_checkpoint_against_real_cache`
is the caller-shaped real-path test: it exercises the exact same function
against the ACTUAL cached checkpoint files on this machine when present
(this dev box already has both TabICLv2 checkpoints cached, verified
manually against jingang/TabICL), and is skipped (not failed) when the cache
is cold -- a fresh CI box without network is not expected to have ~110MB
model checkpoints lying around.
"""
import os

import pytest

import prefetch_checkpoints as pc


def test_verify_checkpoint_missing_file():
    ok, detail = pc.verify_checkpoint("/no/such/path/checkpoint.ckpt")
    assert ok is False
    assert "does not exist" in detail


def test_verify_checkpoint_none_path():
    ok, detail = pc.verify_checkpoint(None)
    assert ok is False


def test_verify_checkpoint_too_small(tmp_path):
    p = tmp_path / "truncated.ckpt"
    p.write_bytes(b"\x00" * 1024)  # 1 KB, far below MIN_SANE_BYTES
    ok, detail = pc.verify_checkpoint(str(p))
    assert ok is False
    assert "too small" in detail


def test_verify_checkpoint_too_large(tmp_path):
    p = tmp_path / "huge.ckpt"
    with open(p, "wb") as fh:
        fh.seek(pc.MAX_SANE_BYTES + 1024)
        fh.write(b"\x00")
    ok, detail = pc.verify_checkpoint(str(p))
    assert ok is False
    assert "too large" in detail


def test_verify_checkpoint_sane_size_ok(tmp_path):
    p = tmp_path / "plausible.ckpt"
    with open(p, "wb") as fh:
        fh.seek(80 * 1024 * 1024)  # 80 MB, within [MIN, MAX]
        fh.write(b"\x00")
    ok, detail = pc.verify_checkpoint(str(p))
    assert ok is True
    assert "ok" in detail


def test_verify_checkpoint_directory_rejected(tmp_path):
    ok, detail = pc.verify_checkpoint(str(tmp_path))
    assert ok is False
    assert "not a regular file" in detail


def test_checkpoints_dict_has_classifier_and_regressor():
    assert set(pc.CHECKPOINTS) == {"classifier", "regressor"}
    assert pc.CHECKPOINTS["classifier"] == "tabicl-classifier-v2-20260212.ckpt"
    assert pc.CHECKPOINTS["regressor"] == "tabicl-regressor-v2-20260212.ckpt"


def test_fetch_checkpoint_check_only_missing_never_downloads(monkeypatch):
    """check_only=True must never attempt a network download, even when the
    file isn't cached -- verified by asserting the download-path branch is
    unreachable (we monkeypatch hf_hub_download to raise if called with the
    non-local-only signature)."""
    import huggingface_hub

    call_log = []

    def spy_download(*args, **kwargs):
        call_log.append(kwargs.get("local_files_only", False))
        if kwargs.get("local_files_only"):
            from huggingface_hub.utils import LocalEntryNotFoundError
            raise LocalEntryNotFoundError("not cached")
        raise AssertionError("check_only must not trigger a real download")

    monkeypatch.setattr(huggingface_hub, "hf_hub_download", spy_download)
    ok, path, detail = pc.fetch_checkpoint("nonexistent-checkpoint.ckpt", check_only=True)
    assert ok is False
    assert path is None
    assert call_log == [True]


@pytest.mark.parametrize("kind,filename", [
    ("classifier", "tabicl-classifier-v2-20260212.ckpt"),
    ("regressor", "tabicl-regressor-v2-20260212.ckpt"),
])
def test_verify_checkpoint_against_real_cache(kind, filename):
    """Caller-shaped real-path test: runs the real verify_checkpoint() against
    the real local HF cache (no network required if already cached; this dev
    box has both checkpoints warmed and manually verified against
    jingang/TabICL, see the executor's report). Skips gracefully if a fresh
    environment hasn't warmed the cache yet."""
    from huggingface_hub import hf_hub_download
    from huggingface_hub.utils import LocalEntryNotFoundError
    try:
        path = hf_hub_download(repo_id=pc.REPO_ID, filename=filename,
                               local_files_only=True, token=False)
    except LocalEntryNotFoundError:
        pytest.skip(f"{filename} not cached locally; skipping real-path check")
    ok, detail = pc.verify_checkpoint(path)
    assert ok is True, detail
