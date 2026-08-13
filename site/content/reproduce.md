# Reproduce

Frozen numbers on this site are stamped from committed table extracts shipped with the companion. Figures regenerate from on-disk result records via `make figures` in the manuscript tree. This page is the only place that names archive filenames.

## Smoke test

Offline, under two minutes: core imports, Stage-1 pipeline on a synthetic fixture, validation of tracked result records.

```
./smoke_test.sh
```

## Data

No bulk data is stored in the repository. OpenML datasets are fetched on demand (no authentication). Folktables / ACS PUMS 2018 is downloaded on demand. See `DATA_MANIFEST.md` for licenses: they are **not** covered by this repository’s MIT license.

## Figures from result records

```
cd manuscripts
make figures
```

Requires R ≥ 4 with ggplot2, jsonlite, scales, and patchwork, plus the vendored plot theme. Python experiment code used the `dl` environment with pins in `requirements.txt`.

## Archive pointers (filenames only)

- `nd1_s2_lightgbm_mondrian.json` and `nd1_s2_lightgbm_mondrian_keyexcluded.json` — CORE14 GBM coverage, repair, Mondrian, Stage-2 gate
- `nd1_tabicl_fm_arm_leakage_ablation.json` — TabICLv2 CORE14 table
- `nd1_tabdpt_fm_arm.json` — TabDPT key-included arm (no key-out coverage points)
- `nd1_learned_selector_baseline.json` — learned vs free vs oracle headline
- `p4_tableshift_result.json` — ACS exploratory arm
- `p5-arm results.json` — held-out TableShift roster and H1/H2 aggregate
- `aggregate-split-repeats-2026-07-02.json` — F6 split-realization counts
- `nd2_mini_spike.json` — blocked-run error log (not a result)

## Links

- GitHub: https://github.com/PeterPonyu/structured-data-fm-reliability-research
- Reserved DOI: https://doi.org/10.5281/zenodo.21130297 (draft deposition)
- Submitted PDF: https://github.com/PeterPonyu/structured-data-fm-reliability-research/blob/main/manuscripts/kbs/paper_kbs.pdf (not copied into this Pages artifact)
