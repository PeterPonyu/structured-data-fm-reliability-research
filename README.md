# structured-data-fm-reliability-research

Code archive: Zenodo DOI 10.5281/zenodo.21130297 (reserved; draft record, activates on publish).

Split-conditioned selective-prediction reliability audit for tabular models,
including an open-weights tabular foundation model (ND1). Broader workspace
scope: benchmark reliability, leakage, calibration, and split sensitivity for
tabular and time-series foundation models. No financial, medical, or business
deployment claims.

## Thesis

Random-split validation overstates tabular-model reliability: on 14 public
OpenML datasets with defensible entity/time keys, moving from random to
leave-group-out / rolling-origin splits collapses risk-coverage (AURC) and
split-conformal coverage (e.g. electricity 0.909 → 0.588, Airlines 0.897 →
0.217). Uncertainty-ranked abstention repairs most of the damage (beats random
deferral on 13/14 datasets in every arm, Holm-robust), the effect is
model-agnostic across XGBoost, LightGBM, and the TabICLv2 tabular foundation
model (which does NOT auto-repair the gap), and a Mondrian group-conditional
conformal add-on is a clean pre-registered null. The contribution is a
reliability-evaluation protocol / benchmark audit, not a new estimator.

## Repo layout

```
experiments/                     analysis pipelines (Python; ~3,700 LOC)
  census_openml_groupkeys.py       Stage-0: OpenML group-key census (145 -> 23 candidates)
  census_verify_groupkeys.py       Stage-0: real-data verification of candidates
  nd1_split_conditioned_audit.py   Stage-1: XGBoost split-conditioned audit (14 datasets)
  nd1_s2_lightgbm_mondrian.py      Stage-2: XGBoost+LightGBM + Mondrian conformal
  nd1_s2_p4_calsize_diag.py        calibration-size diagnostic
  p4_tableshift.py                 TableShift-class Folktables/ACS spatial-OOD arm
  nd1_tabicl_fm_arm.py             TabICLv2 FM pilot (3 datasets, GPU)
  nd1_tabicl_fm_arm_full14.py      TabICLv2 FM full 14-dataset sweep (GPU)
  nd2_mini_spike.py                ND2 time-series spike (BLOCKED: TabPFN token)
  results/                         result JSONs (provenance-stamped), run logs,
                                   findings memos, preregistration
manuscripts/
  paper.tex / paper.pdf            complete compiled draft; every number traces
                                   to the result JSONs (none hand-edited)
  figures/                         F1-F5 (PDF+PNG) + R scripts + derived CSVs
tests/smoke_test.py, smoke_test.sh fast offline smoke test (<2 min)
DATA_MANIFEST.md                   data provenance: what is fetched, from where
NEXT-EXPERIMENTS.md                deferred / not-run experiments
directions/, research/             direction bank
```

## Reproducing

### 1. Environment

All tracked results were produced in a conda env (`dl`) with Python 3.13.7 on
Linux; pinned versions are in `requirements.txt`:

```bash
pip install -r requirements.txt
pip install -e ../reliability-commons   # local `relmetrics` package (not on PyPI)
```

If `reliability-commons` is checked out elsewhere, point the scripts at it:

```bash
export RELIABILITY_COMMONS=/path/to/reliability-commons
```

R (figures only): R >= 4.x with `ggplot2`, `jsonlite`, `scales`, `patchwork`,
plus the shared plot theme `ggtheme.R` (path overridable via `GGTHEME_R`,
see below). No other R dependencies.

### 2. Data

No bulk data is stored in this repo — everything is fetched on demand; see
`DATA_MANIFEST.md` for the full source table. In short:

- **OpenML** (no auth): the 14 keyed datasets are fetched by dataset id via the
  `openml` package and cached in its default user cache dir.
- **Folktables / ACS PUMS 2018**: downloaded on demand by the `folktables`
  package into `DATA_ROOT` (env var; default `/tmp/folktables_data`).
- **TabICLv2 checkpoint**: pulled from the Hugging Face Hub by `tabicl` on
  first use.
- **TabPFN weights / M4-monthly**: NOT downloaded (license token / SSL block);
  the blocked-run record is `experiments/results/nd2_mini_spike.json`.

Data licenses are NOT covered by this repo's MIT license: each OpenML dataset
carries its own license (see its OpenML page), ACS PUMS is US Census public
data subject to Census terms, the TabICLv2 checkpoint follows its Hugging Face
model-card license, and TabPFN weights are license-gated (never fetched here).

### 3. Smoke test

```bash
./smoke_test.sh          # <2 min, offline; imports core modules, runs the
                         # Stage-1 pipeline on a synthetic fixture, validates
                         # the tracked result JSONs
```

### 4. Run order (CPU unless noted)

```bash
PY=~/miniconda3/envs/dl/bin/python           # env with requirements installed
$PY experiments/census_openml_groupkeys.py   # Stage-0 census    (~min, network)
$PY experiments/census_verify_groupkeys.py   # Stage-0 verify    (~min, network)
$PY experiments/nd1_split_conditioned_audit.py   # Stage-1 XGBoost   (~40 s cached)
$PY experiments/nd1_s2_lightgbm_mondrian.py      # Stage-2 XGB+LGBM  (~4 min cached)
$PY experiments/nd1_s2_p4_calsize_diag.py        # calibration-size diagnostic
$PY experiments/p4_tableshift.py                 # ACS arm (~10 min, downloads ACS)
$PY experiments/nd1_tabicl_fm_arm_full14.py      # FM arm (GPU, >20 min)
```

Key-excluded leakage ablation (Stage-1/Stage-2): rerun with `EXCLUDE_KEY=1`;
outputs go to the `*_keyexcluded.json` twins. All outputs land in
`experiments/results/` and are provenance-stamped (script path, seeds,
timestamp). Results change ONLY by rerunning these scripts — never by editing
JSONs.

### 5. Figures and paper

The manuscript uses the shared `reliability-commons` paper template
(standard article class + natbib + R/ggplot2 figure scripts + Makefile).
Figures are generated ONLY from the on-disk result JSONs (no hardcoded data):

```bash
cd manuscripts
make figures   # Rscript figures/p4_figs.R  -> F1-F4 (+ p4_table.csv)
               # Rscript figures/p5_tableshift.R -> F5, F5a, F5b (+ p5_tableshift_table.csv)
make paper     # figures + copy shared.bib from reliability-commons + latexmk -pdf
```

Bibliography: `shared.bib` is copied from
`../reliability-commons/shared.bib` by `make bib` (override with
`make paper SHARED_BIB=...`); paper-specific entries live in
`manuscripts/refs.bib`. Path overrides for the figure scripts: `GGTHEME_R`
(plot theme; default is the vendored `manuscripts/figures/ggtheme.R`) and
`ND1_RESULTS_ROOT` (results dir; default resolves to
`experiments/results/` relative to the scripts).

## Status (honest, as of 2026-07-02)

- **Solid:** Stage-1 and Stage-2 XGBoost arms are reconciled — bit-for-bit
  identical per-dataset records under the per-context RNG discipline
  (`rng_for`), deterministic across repeats. The abstention-repair claim
  (13/14 in every arm incl. the FM) is Holm-robust. Every manuscript number
  traces to a regenerated, provenance-stamped JSON.
- **Split-realization-sensitive:** the grouped-gap majority count (8/14 XGB,
  7/14 LGBM under the current single split draw; LightGBM sits below the
  preregistered majority). K-repeated split draws are the top deferred item —
  do NOT quote majority counts in a submission before running it
  (NEXT-EXPERIMENTS.md item 1).
- **Stale-RNG arms:** the calibration-size diagnostic and the ACS arm still
  reflect the pre-fix RNG stream (items 2 and 6 in NEXT-EXPERIMENTS.md).
- **FM arm:** frozen at `n_estimators=4`, pre-fix split draws, with a stale
  embedded XGBoost reference block — disclosed in the paper's Limitations;
  rerun is a >20 min GPU job (item 3).
- **Blocked / not-run:** TabPFN-2.5 (license token), ND2 time-series spike
  (token + SSL; blocked-run record kept in `results/nd2_mini_spike.json`),
  tuned-GBM baselines, related-work section and venue formatting. Full ledger:
  `NEXT-EXPERIMENTS.md`.
- **Quarantine:** no mock or fabricated artifacts are present in this repo;
  nothing is quarantine-flagged. The `nd2_mini_spike.json` blocked-run record
  is an error log, not a result — do not cite it as one.
- The paper's "restore coverage to >= 0.90" number is an explicit
  NOT-YET-ACHIEVED target, not a result.
