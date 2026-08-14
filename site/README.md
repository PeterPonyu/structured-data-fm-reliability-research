# Structure tabular reliability audit (Pages source)

Static HTML for keyed-split coverage, H1/H2, quarantine, and abstention.
No npm. Python 3 stdlib only.

```bash
python site/build.py
```

Writes `docs/` (GitHub Pages artifact). Does not restyle source figure binaries.

GitHub Actions (`.github/workflows/pages.yml`) runs the same command and uploads
`docs/` with the official Pages actions. The workflow watches
`pages/structure-companion` only (no `main`, no PR deploy).

## Layout

```
site/
  build.py
  css/portal.css
  js/keytoggle.js          # optional; both key conditions stay in the DOM
  templates/page.html
  content/*.md
  data/                    # frozen table extracts (no workstation paths)
  figures/                 # web-only binaries the runner cannot rasterize
docs/                      # generated
```

## Identity

Structure science only (keyed splits, H1/H2, quarantine, abstention).
Do not copy GEO, JCP, RotCert, ASR, or Inspect assets.
