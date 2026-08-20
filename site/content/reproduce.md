# Reproduce

Pinned Python dependencies are in `requirements.txt`. No bulk data is stored
in the public archive: OpenML datasets and Folktables / ACS PUMS 2018 are
fetched on demand. Tabular-foundation-model weights come from the Hugging Face
Hub on first use. Dataset licenses are **not** covered by the code archive’s
MIT license.

```bash
pip install -r requirements.txt
./smoke_test.sh
```

Further scripts live under `experiments/` in the repository. Results change
only by rerunning those scripts locally.

## Links

- Code: https://github.com/PeterPonyu/structured-data-fm-reliability-research
- Zenodo: https://doi.org/10.5281/zenodo.21130297
