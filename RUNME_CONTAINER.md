# RUNME_CONTAINER.md — decisive-experiment arms on a fresh AutoDL container

Target machine: AutoDL container, RTX 4090D (24 GB), conda `base` env with
torch (cu128) preinstalled. This document is the exact ordered command
sequence; `run_all_arms.sh` runs steps 1-6 for you (`fetch_data.sh` for step 2).

These arms implement the top items from `NEXT-EXPERIMENTS.md` ("Still
deferred"), reconciled against the actual file (item 1 turned out to already
be DONE on disk despite the doc still calling it "TOP item" — see step 3
below). Every new script is additive: it writes a NEW provenance-stamped
result JSON under `experiments/results/`, never touching an existing tracked
JSON.

## 0. Before you start

- **Do not skip hooks / do not force-push / do not touch existing result
  JSONs.** Results only change by running a script; a script producing a NEW
  filename is how this portfolio adds evidence without risking existing
  tracked numbers.
- Every arm below supports `--smoke` (tiny synthetic data, CPU, no network,
  seconds) if you want to sanity-check the environment before spending GPU
  time. `run_all_arms.sh` runs the full pytest+smoke pre-flight automatically.

## 1. Environment setup

```bash
cd structured-data-fm-reliability-research

# torch (cu128) is already in the container's conda base env — do NOT
# reinstall it. Everything else:
pip install -r requirements.txt
pip install -e ../reliability-commons   # local `relmetrics` package, not on PyPI
# (if reliability-commons lives elsewhere:)
# export RELIABILITY_COMMONS=/path/to/reliability-commons

pip install pytest   # not in requirements.txt; only needed to run tests/
```

Verify: `python -c "import torch; print(torch.cuda.is_available())"` should
print `True`.

## 2. Data expectations

No bulk data is stored in this repo (see `DATA_MANIFEST.md`). Everything is
pulled on demand by the packages that use it:

| Source | Package | Cache location | Needed by |
|---|---|---|---|
| OpenML (14 keyed datasets, no auth) | `openml` | `~/.cache/openml` | items 2, 3, 4 |
| Folktables / ACS PUMS 2018 | `folktables` | `$DATA_ROOT` (default `/tmp/folktables_data`) | not rerun by this ledger (item 6, out of scope here) |
| TabICLv2 checkpoint | `tabicl` -> Hugging Face Hub | `~/.cache/huggingface/hub` | item 3 |
| TabPFN-2.5 weights | `tabpfn` | n/a | item 5 (blocked, license token) |

Pre-warm all of these (so a mid-run network hiccup doesn't waste GPU time):

```bash
./fetch_data.sh
```

This is idempotent — safe to rerun; it no-ops on anything already cached.

## 3. Item 1 — K-repeated folds: already done, nothing to run

`NEXT-EXPERIMENTS.md` still lists this as the "TOP item" / "Still deferred",
but reconciling against the repo state (not just the doc text) shows it was
already implemented and executed: `experiments/results/split_repeats/`
contains 100 per-k JSONs (Stage-1 K=30, Stage-2 K=20, both feature conditions)
plus `aggregate-split-repeats-2026-07-02.json` and
`findings-split-repeats-2026-07-02.md`, all git-committed (`git log --oneline`
shows `depth: pre-declare + implement repeated split realizations` and `depth:
repeated split realizations -> split-level CIs...`). **Do not rerun the full
sweep** (~2 h wall-clock) — there is nothing new to gain from it, and rerunning
would not change the analysis. `tests/test_split_repeats.py` covers this arm's
core logic (the `rng_for` derivation and the aggregate script's
fold-blocking-aware statistics) against synthetic fixtures.

If you DO want to extend the sweep (e.g. more repeats), set `REPEAT_K` when
invoking `nd1_split_conditioned_audit.py` / `nd1_s2_lightgbm_mondrian.py`
directly, then rerun `nd1_split_repeats_aggregate.py`.

## 4. Item 2 — calibration-size diagnostic rerun (CPU, ~1-2 min)

Reruns the Mondrian calibration-size diagnostic under the reconciled
per-context RNG discipline (`rng_for`), fixing the pre-fix-RNG staleness called
out in `NEXT-EXPERIMENTS.md` item 2. Depends only on the already-tracked
Stage-2 JSONs (present in-repo; no extra prerequisite run needed).

```bash
python experiments/nd1_s2_p4_calsize_diag_reconciled.py
EXCLUDE_KEY=1 python experiments/nd1_s2_p4_calsize_diag_reconciled.py
```

Writes `experiments/results/nd1_s2_p4_calsize_diag_reconciled.json` and
`..._keyexcluded.json`.

## 5. Item 4 — tuned-GBM baseline rerun (CPU, ~15-25 min)

Reruns the Stage-1 audit protocol with a small per-dataset/per-model
randomized hyperparameter search (12 trials by default; see
`N_TUNE_TRIALS`), tuned ONLY on an inner holdout of the random-split training
fold (never touches the grouped/time test fold or its calibration set — the
leakage-safety invariant `tests/test_tuned_gbm_baseline.py` checks).

```bash
python experiments/nd1_tuned_gbm_baseline.py
EXCLUDE_KEY=1 python experiments/nd1_tuned_gbm_baseline.py
```

Writes `experiments/results/nd1_tuned_gbm_baseline.json` and
`..._keyexcluded.json`.

## 6. Item 3 — FM-arm leakage ablation + larger ensembles (**the one GPU item**, ~1-4 GPU-h)

Run this LAST (after all CPU arms) and only once `fetch_data.sh` has cached
the TabICLv2 checkpoint. Reruns the TabICLv2 full-14-dataset arm under the
reconciled RNG discipline, with:
- the key-excluded leakage ablation (`EXCLUDE_KEY=1`, mirrors Stage-1/2), and
- a larger ensemble (`TABICL_N_EST`, default 16 vs the frozen run's 4).

The embedded GBM reference block is now read LIVE from the on-disk reconciled
Stage-1 JSON at run time (never hardcoded), fixing the staleness disclosed in
the paper's Limitations section.

```bash
# key-included (realistic protocol), default n_estimators=16:
python experiments/nd1_tabicl_fm_arm_leakage_ablation.py

# key-excluded (leakage ablation):
EXCLUDE_KEY=1 python experiments/nd1_tabicl_fm_arm_leakage_ablation.py

# optionally, an even larger ensemble (more GPU time, budget permitting):
TABICL_N_EST=32 python experiments/nd1_tabicl_fm_arm_leakage_ablation.py
```

Writes `experiments/results/nd1_tabicl_fm_arm_leakage_ablation.json` and
`..._keyexcluded.json`. Each dataset is checkpointed incrementally in spirit
(errors on one dataset are recorded as `status: "error"` and the run
continues) so a partial failure does not lose already-computed datasets'
results within that process's stdout log — redirect to a log file:

```bash
python experiments/nd1_tabicl_fm_arm_leakage_ablation.py 2>&1 | tee experiments/results/nd1_tabicl_fm_arm_leakage_ablation_run.log
```

## 7. Item 5 — TabPFN-2.5 arm: stub only, do not run without a token

`experiments/nd1_tabpfn25_arm.py` is a guarded stub
(`REQUIRES_USER_TOKEN = True`). Without `TABPFN_TOKEN` set it exits 1 with the
exact remediation steps (see `experiments/results/nd2_mini_spike.json` for the
prior blocked-run evidence). **Do not attempt to bypass the guard or fabricate
a result.** If a token becomes available, see the script's module docstring
for the implementation plan (port `nd1_tabicl_fm_arm_leakage_ablation.py`'s
protocol to `tabpfn.TabPFNClassifier`/`TabPFNRegressor`), implement it, verify
it against real weights, THEN remove the guard.

## 8. Verifying everything worked

```bash
python -m pytest tests/ -v      # 30 tests, offline, seconds
./smoke_test.sh                 # pre-existing offline smoke check, <2 min
```

Then spot-check the new JSONs parse and carry a `provenance` block:

```bash
python - <<'PY'
import json, glob
for f in glob.glob("experiments/results/nd1_s2_p4_calsize_diag_reconciled*.json") + \
         glob.glob("experiments/results/nd1_tuned_gbm_baseline*.json") + \
         glob.glob("experiments/results/nd1_tabicl_fm_arm_leakage_ablation*.json"):
    d = json.load(open(f))
    assert "provenance" in d, f"{f} missing provenance stamp"
    print(f, "ok, git_sha=", d["provenance"].get("git_sha"))
PY
```

## Ordering summary (= `run_all_arms.sh`)

1. `python -m pytest tests/ -q` + `./smoke_test.sh` (pre-flight, offline)
2. Item 1: nothing to run (already done, see §3)
3. Item 2: calsize reconciled, key-included then key-excluded (CPU)
4. Item 4: tuned-GBM baseline, key-included then key-excluded (CPU)
5. `./fetch_data.sh` (idempotent cache pre-warm)
6. Item 3: FM leakage ablation, key-included then key-excluded (**GPU, last**)
7. Item 5: skipped unless `TABPFN_TOKEN` is set (stub only even then)
