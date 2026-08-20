# structured-data-fm-reliability-research

Split-conditioned selective-prediction audit for keyed tabular models, including
open-weights tabular foundation models. Random-split validation is compared
with leave-group-out and rolling-origin splits. No financial, medical, or
business deployment claims.

Code archive: Zenodo DOI [10.5281/zenodo.21130297](https://doi.org/10.5281/zenodo.21130297).

## Question

Does split-conformal coverage at α = 0.10 (target 0.90) survive the split that
matters at deployment — leave-group-out or rolling-origin — on datasets that
actually have an entity or time key? If it does not, does ranking items by a
free uncertainty score and abstaining on the highest-risk ones repair
retained-set selective risk?

## Verdicts

| Gate | Result |
| --- | --- |
| H1 coverage restoration (held-out TableShift) | REJECT |
| H2 uncertainty vs tuned selector (held-out TableShift) | CONFIRM |
| Stage-2 conjunctive gate (exploratory 14) | KILL |
| Repair vs random deferral (exploratory 14, all arms) | 13/14 (load-bearing) |

- On 14 public OpenML datasets with a defensible entity or time key, grouped
  and temporal splits push plain split-conformal below its 0.90 target (median
  worst-group coverage about 0.81 on the held-out TableShift arm).
- No tested distribution-free conformal remedy restores group-conditional
  coverage at the majority level (**H1 REJECT**).
- Uncertainty-ranked abstention beats random deferral on 13 of 14 exploratory
  datasets and matches a budget-matched tuned selector on held-out TableShift
  (**H2 CONFIRM**).
- Repair remains far below an oracle ceiling (median repair ratio 0.34 vs
  0.75). The prescription is selective-risk fallback, not a restored coverage
  guarantee.
- The collapse is model-agnostic across XGBoost, LightGBM, TabICLv2, and
  TabDPT: tabular foundation models do not auto-repair the gap.
- The Stage-2 conjunctive gate evaluates to **KILL** because the grouped-gap
  count is split-realization-fragile and key-inclusion-sensitive. Only the
  repair count is load-bearing.

The contribution is a reusable protocol — keyed split comparison, coverage
test, uncertainty abstention fallback — not a new estimator.

## Protocol

1. Compare **random** vs **leave-group-out / rolling-origin** on a dataset that
   has an entity or time key.
2. Test whether split-conformal coverage at α = 0.10 survives the deployment
   split. Report worst-group coverage, not only marginal.
3. If it does not, rank abstention by the model-native uncertainty score
   (classification: 1 − max *p*; regression: quantile-interval width). Scope:
   retained-set selective risk, **not** restoring a coverage guarantee.

**Key included** is the headline condition (the split key stays in the feature
matrix). **Key excluded** is the conservative bound (the key is dropped).
Leave-group-out test keys are unseen categories; retaining the encoded key can
inflate collapse, so key-out is the conservative degradation bound.
Grouped-gap counts shift 8/14 → 6/14 (XGBoost) and 7/14 → 5/14 (LightGBM).
Repair stays 13/14 in both conditions.

## Quarantine

“Quarantine” here is a split of roles, not a data-quality dump.

| Item | Status | Cite as a result? |
| --- | --- | --- |
| Exploratory remedy ladder vs TableShift confirmatory arm | Quarantined (no overlap; *K* = 10 vs *K* = 20) | Cite the split of roles, not a pooled count |
| Stage-2 conjunctive gate | KILL | Yes, as KILL |
| Mondrian mechanism, key excluded | KILL | Yes, as KILL |
| Grouped-gap / AURC-degrade majority | Split-realization distribution | No as a headline majority |
| TabPFN-2.5 | Blocked (license token); never downloaded | No |
| ND2 time-series / M4 | Blocked (token + SSL); the blocked-run record is an error log | No |
| F7 post-hoc power | Supporting; independence idealization overstates power | Yes, with those caveats |
| F8 within-dataset calibration-size sweep | Negative; no cross-sectional dose-response | Yes, as negative |
| Mock / fabricated artifacts | None | — |

## Reproduce

Pinned Python dependencies are in `requirements.txt`. No bulk data is stored
here: OpenML datasets and Folktables / ACS PUMS 2018 are fetched on demand.
TabICLv2 weights come from the Hugging Face Hub on first use. TabPFN weights
and M4-monthly are not downloaded. Dataset licenses are not covered by this
repository’s MIT license.

```bash
pip install -r requirements.txt
./smoke_test.sh
python experiments/census_openml_groupkeys.py
python experiments/census_verify_groupkeys.py
python experiments/nd1_split_conditioned_audit.py
python experiments/nd1_s2_lightgbm_mondrian.py
python experiments/nd1_s2_p4_calsize_diag.py
python experiments/p4_tableshift.py
python experiments/nd1_tabicl_fm_arm_full14.py   # GPU
```

Key-excluded ablation: rerun Stage-1 / Stage-2 with `EXCLUDE_KEY=1`. Results
change only by rerunning the scripts.

Companion site (isolation-live):
https://peterponyu.github.io/structured-data-fm-reliability-research/
