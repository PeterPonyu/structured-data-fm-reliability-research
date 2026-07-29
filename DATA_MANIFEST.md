# DATA_MANIFEST.md — data provenance for structured-data-fm-reliability-research

Written 2026-07-02 as part of the provenance sweep (git baseline `baseline-2026-07-02`).

## Summary

**No bulk datasets are stored in this repository.** All experiment data is pulled
on demand at run time (see FABLE-HANDOFF.md §5 "Existing assets"). No tracked or
gitignored file exceeds 50 MB; no data directory exceeds 200 MB (repo total ≈ 2.3 MB
excluding `.git`). Consequently there are no gitignored data paths requiring
per-file SHA256 entries; this manifest instead records the download sources so an
external party can re-materialize the inputs.

## Data sources (fetched on demand, not stored)

| Source | What | How fetched | Used by |
|---|---|---|---|
| OpenML (no auth) | 14 keyed CORE14 datasets (dids: 151, 188, 1590, 6332, 40701, 41021, 41162, 41540, 42563, 42727, 42728, 42729, 42731, 42732), capped at 30,000 rows each | `openml` Python package 0.15.1 (`openml.datasets.get_dataset(did)`), cached by openml in its default user cache dir (outside this repo) | `experiments/nd1_split_conditioned_audit.py`, `nd1_s2_lightgbm_mondrian.py`, `nd1_s2_p4_calsize_diag.py`, `nd1_tabicl_fm_arm*.py`, `nd1_tabdpt_fm_arm.py`, `nd1_tabpfn25_arm.py`, `census_*.py` |
| OpenML-CC18 (no auth) | 16 additional keyed EXTENDED16 classification datasets (dids: 3, 23, 29, 31, 38, 46, 50, 307, 469, 1461, 1480, 1486, 4534, 23381, 40668, 40975) added 2026-07-09 (EXPANSION-PLAN §2.2 deliverable 3), selectable via `--grid extended30`; selection rule documented in `experiments/dataset_registry.py`'s module docstring | same `openml` package/cache as CORE14 | `experiments/dataset_registry.py` (registry); consumed by any FM arm run with `--grid extended30` |
| Folktables / ACS PUMS 2018 | ACS state-level tasks for the spatial-OOD arm | `folktables` package 0.0.12 (downloads ACS PUMS on demand, cache outside this repo) | `experiments/p4_tableshift.py` |
| Hugging Face Hub (`jingang/TabICL`) | TabICLv2 classifier + regressor checkpoints (`tabicl` package 2.1.1) | downloaded by `tabicl` on first use to the HF cache (outside this repo); `experiments/prefetch_checkpoints.py` (added 2026-07-09) warms + content-verifies BOTH checkpoints up front so a mid-run network hiccup on the regressor checkpoint (the 2026-07-09 container failure, `POST-ANALYSIS.md` Arm 3) can't silently truncate dataset coverage | `experiments/nd1_tabicl_fm_arm.py`, `nd1_tabicl_fm_arm_full14.py`, `nd1_tabicl_fm_arm_leakage_ablation.py`, `nd1_fm_scaling_arm.py` |
| Hugging Face Hub (`Layer6/TabDPT`) | TabDPT checkpoint (`tabdpt1_2.safetensors`, ~103MB; `tabdpt` package 1.2.0) added 2026-07-09 as the second FM-roster member (EXPANSION-PLAN §2.2 deliverable 2; verified via web search against the HF repo + `layer6ai-labs/TabDPT-inference` source) | downloaded by `tabdpt` on first use (`TabDPTEstimator.download_weights()`) to the HF cache (outside this repo); no license/token gate | `experiments/nd1_tabdpt_fm_arm.py` |
| (token-gated) TabPFN-2.5 weights (`Prior-Labs/tabpfn_2_5`) | requires interactive license acceptance / `TABPFN_TOKEN` — never downloaded automatically | n/a unless `TABPFN_TOKEN` is set | `experiments/nd1_tabpfn25_arm.py` (audit body implemented 2026-07-09, still guarded; blocked-run error record in `experiments/results/nd2_mini_spike.json`) |
| (blocked) M4 monthly via GluonTS | SSL failure at fetch time — never downloaded | n/a | `experiments/nd2_mini_spike.py` |

The frozen record of *which* OpenML datasets qualify (and why) is tracked in-repo:
`experiments/results/census_final_triage.json`,
`experiments/results/openml_groupkey_census.json`,
`experiments/results/openml_groupkey_census_verified.json`.

## Gitignored paths (none contain data at time of writing)

| Path pattern | Reason ignored | Contents at baseline |
|---|---|---|
| `experiments/__pycache__/` | Python bytecode (generated junk) | 4 `.pyc` files |
| `.omc/` | orchestration-tool session state, not research artifacts | ~44 KB JSON state |
| `*.aux`, `*.log` (LaTeX), `*.out`, `*.bbl`, `*.blg`, `*.fls`, `*.fdb_latexmk`, `*.synctex.gz` | LaTeX build junk | none present at baseline |
| `.cache/`, `hf_cache/`, `huggingface/`, `openml_cache/`, `data/raw/` | pre-emptive: keep future download caches out of git | none present at baseline |

Note: `experiments/results/*.log` (census_run.log, census_verify.log, nd1_s2_run.log)
are experiment provenance logs, explicitly un-ignored and tracked in git.
