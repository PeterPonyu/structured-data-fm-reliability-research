# Structure paper companion

Static HTML companion for the KBS tabular reliability audit.
No npm. Python 3 stdlib only.

```bash
python site/build.py
```

Writes `docs/` (GitHub Pages artifact). Does not overwrite `manuscripts/figures/`
or any manuscript TeX/PDF.

GitHub Actions (`.github/workflows/pages.yml`) runs the same command and uploads
`docs/` with the official Pages actions. The workflow watches
`pages/structure-companion` only (no `main`, no PR deploy). `paper_*.pdf` is not
copied into `docs/` on this isolation stretch.

## Layout

```
site/
  build.py
  css/portal.css
  js/keytoggle.js          # optional; both key conditions stay in the DOM
  templates/page.html
  content/*.md
  data/                    # frozen table extracts (no workstation paths)
docs/                      # generated; not the manuscript tree
```

## Identity

Structure / KBS only. Do not copy GEO, JCP, RotCert, ASR, or Inspect assets.
