# Structure code-and-protocol leaf (Pages source)

Static HTML for the public code and protocol page.
No npm. Python 3 stdlib only. Does not copy figure binaries or table extracts.

```bash
python site/build.py
```

Writes `docs/` (GitHub Pages artifact).

GitHub Actions (`.github/workflows/pages.yml`) runs the same command and uploads
`docs/` with the official Pages actions. The workflow watches
`pages/structure-companion` only (no `main`, no PR deploy).

## Layout

```
site/
  build.py
  css/portal.css
  templates/page.html
  content/*.md
docs/                      # generated
```

## Identity

Code and protocol only. Do not stamp result numbers, figure binaries, or
article-companion chrome onto this leaf.
