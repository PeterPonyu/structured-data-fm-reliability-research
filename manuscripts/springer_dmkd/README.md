# Springer *Data Mining and Knowledge Discovery* (DMKD) submission port

`paper_svjour.tex` is the **venue-format rendering** of the canonical
`../paper.tex` for submission to *Data Mining and Knowledge Discovery* (DMKD,
Springer, SCIE) as a **benchmark-and-audit** contribution. The science is
identical to `../paper.tex`, which stays canonical — **make content/number edits
there first, then re-port**. This directory only changes the class, frontmatter,
and float sizing.

## Venue: retargeted Machine Learning → DMKD (frozen rule)

This kit was originally the *Machine Learning* (method-track) port. It was
retargeted to DMKD per the study's own preregistered venue rule
(`../../PREREG-REMEDY-EVAL-2026-07-13.md`, lines 76–81): **G1 = FAIL → DMKD**. The
exploratory coverage-remedy evaluation (`../../g1_remedies_2026-07-13/`) rejected
the coverage-restoration hypothesis (no distribution-free remedy robustly restores
group-conditional coverage; median worst-group coverage ≈ 0.81), so the paper's
headline is the honest **negative-coverage / positive-selection** prescription — a
benchmark plus audit, not a new coverage-restoring method. DMKD is the frozen-rule
target for that contribution class. Both journals use the **same** Springer Nature
`sn-jnl` class, so the retarget is a framing change only (cover letter + this
README + the line-1 tex comment); no LaTeX class change was needed.

## Build

```
latexmk -pdf paper_svjour.tex
```
Self-contained: the class, bib style, and both `.bib` files are vendored here.
Figures are read from `../figures/` via `\graphicspath`.

## Class / style provenance (vendored, not in system texmf)

| File | Source |
|---|---|
| `sn-jnl.cls` | Springer Nature LaTeX template, copied from a prior local Springer submission at `/home/zeyufu/Desktop/labs/_previous/PanODE-LAB/article/sn-template/sn-jnl.cls` (official Springer template dir, incl. `user-manual.pdf`). The same class serves DMKD and Machine Learning. |
| `sn-mathphys-num.bst` | Same template's `bst/` dir — Math & Physical Sciences **numbered** reference style. |
| `refs.bib`, `shared.bib` | Copied from `../` (identical to the canonical paper's bibliography). |

`sn-jnl.cls` loads `natbib` (so the canonical `\citep`/`\citet` work) and
`hyperref` internally; it does **not** load `cleveref`, so `paper_svjour.tex` adds
`\usepackage{cleveref}` after the class. Documentclass:
`\documentclass[pdflatex,sn-mathphys-num]{sn-jnl}` → numbered `[n]` citations.

## What changed vs `../paper.tex` (format only, no science)

- `article` frontmatter (`\author`+`authblk`, `abstract` environment,
  `\bibliographystyle{plainnat}`) → Springer `\author*`/`\affil`, `\abstract{}`
  command, `\keywords{}`, and class-driven numbered bibliography (no explicit
  `\bibliographystyle`).
- Added a Springer **Declarations** section (Funding, Conflict of interest,
  Ethics, Consent, Data availability, Code availability, Author contribution).
  Data/Code availability carry the canonical paper's text; Funding and Conflict of
  interest are **TODO-USER** placeholders.
- **Table 1** (7-column FM table) overflowed the narrower single column by 68 pt
  under reflow; fixed with `\footnotesize` + `\tabcolsep=3.5pt` (0 overfull boxes
  now). No rotation/splitting needed. All other floats reflowed cleanly.

## TODO-USER before submission

- **Affiliation** (`\affil*[1]`): org / city / country — currently placeholders.
  Name (`Zeyu Fu`) and email (`fuzeyu09@gmail.com`) carried from the canonical paper;
  ORCID `0009-0001-8329-0108` can be added on the SNAPP portal.
- **Funding** and **Conflict of interest** declarations.
- **Abstract citations:** the canonical abstract cites the four model papers
  (`[n]` here). Springer permits this, but confirm against *DMKD*'s author
  instructions if a citation-free abstract is required.
- Citation **author lists** for the flagged 2026-wave `\misc` entries and
  `ma2024tabdpt` remain pending human verification in `refs.bib` (same as canonical).

## Build stats (last clean build)

- `latexmk` exit 0, **20 pages**, 0 errors, 0 undefined citations/references,
  27 references resolved via `sn-mathphys-num`. (Page count is post-G1-integration;
  the pre-G1 build was 19 pages.)
