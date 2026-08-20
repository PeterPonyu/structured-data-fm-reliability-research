# structured-data-fm-reliability-research

Python scripts for a split-conditioned selective-prediction reliability
audit on keyed tabular data. A frozen predictor is wrapped in
split-conformal prediction and scored under a random row split versus a
leave-group-out or rolling-origin split. No financial, medical, or
business deployment claims.

Code archive: Zenodo DOI [10.5281/zenodo.21130297](https://doi.org/10.5281/zenodo.21130297).

Public Pages is a code and protocol leaf, not a findings page:
https://peterponyu.github.io/structured-data-fm-reliability-research/

## Protocol

1. Compare **random** vs **leave-group-out / rolling-origin** on a dataset that
   has an entity or time key.
2. Test whether split-conformal coverage survives the deployment split.
   Report worst-group coverage, not only marginal.
3. If it does not, rank abstention by the model-native uncertainty score
   (classification: 1 − max *p*; regression: quantile-interval width). Scope:
   retained-set selective risk, **not** restoring a coverage guarantee.

**Key included** keeps the split key in the feature matrix. **Key excluded**
drops the key and is the conservative bound.

## Reproduce

Pinned Python dependencies are in `requirements.txt`. No bulk data is stored
here: OpenML datasets and Folktables / ACS PUMS 2018 are fetched on demand.
Tabular-foundation-model weights come from the Hugging Face Hub on first use.
Dataset licenses are not covered by this repository’s MIT license.

```bash
pip install -r requirements.txt
./smoke_test.sh
```

Further scripts live under `experiments/`. Results change only by rerunning
those scripts locally.
