# Elsevier *Information Sciences* submission kit

`paper_els.tex` is the **venue-format rendering** of the canonical `../paper.tex` for submission to
*Information Sciences* (Elsevier, ISSN 0020-0255). The science is identical to `../paper.tex`, which
stays canonical — **make content/number edits there first, then re-port**. This directory changes only
the document class, front matter, Elsevier declarations, and the float sizing of one wide table.

## Why Information Sciences

Retargeted from Springer *Data Mining and Knowledge Discovery* per
`docs/records/VENUE-RELIABILITY-SCAN-2026-07-16.md` (Q2, structured section). Information Sciences has
the deepest in-venue precedent of any candidate for this exact paper type (conformal prediction +
selective classification + tabular learning) and a documented editorial screen that *rewards* rigorous,
well-validated audit-style work rather than penalizing it. `../springer_dmkd/` is kept untouched as the
fallback kit.

## Build

```
latexmk -pdf paper_els.tex
```

Self-contained: the class (`elsarticle.cls`), the numbered bib style (`elsarticle-num.bst`), and both
`.bib` files are vendored here (the class/bst also exist in system TeX Live). Figures are read from
`../figures/` via `\graphicspath`.

## What changed vs `../paper.tex` (format only, no science)

- **Class:** `article` (+ `authblk`, `abstract` env, `\bibliographystyle{plainnat}`) →
  `\documentclass[preprint,review,12pt]{elsarticle}` with an elsarticle `\begin{frontmatter}` block
  (`\title`, `\author`/`\affiliation`/`\ead`, `abstract` env, `\begin{keyword}...\end{keyword}`).
  `review` gives a single-column, double-spaced manuscript, the Elsevier-preferred format for peer
  review.
- **Reference style:** `\bibliographystyle{elsarticle-num}` — numbered `[n]`, ordered by first
  appearance, with article titles. This matches Information Sciences' Vancouver-style numbered format.
- **Declarations added** (Elsevier GATE-0): CRediT authorship contribution statement, Declaration of
  competing interest, Declaration of generative-AI use (TODO-USER), Funding (TODO-USER), and a Data
  availability statement. The canonical Data & Code Availability text is carried verbatim.
- **One format-only float fix:** the 7-column FM table (Table 1) is set `\footnotesize` and wrapped in
  `\resizebox{\linewidth}` so it fits the elsarticle single-column measure. No numbers, claims, or body
  prose differ from canonical. `microtype` + `\emergencystretch` + `xurl` absorb residual overfull from
  12pt double-spacing and break the long GitHub/Zenodo URLs.

## Reference expansion (2026-07-16)

The canonical bibliography was expanded from 27 to **46 resolved references** (+19), to reach the low
end of the Information Sciences range (scan Q3: ~40 typical). Every added reference was **live-verified
this session** against Crossref (`api.crossref.org/works/<doi>`) or the arXiv API — title, authors,
year, venue, volume/pages taken from the resolved record, no fabrication. The additions are woven into
the Introduction, Related Work, and Methods with a substantive clause each (no citation dumps). They
include the in-venue Information Sciences conformal/selective/tabular cluster the reviewer pool is
drawn from:

- He et al. (2025), *Conjunction subspaces test for conformal and selective classification*,
  Inf. Sci. 707 — `10.1016/j.ins.2025.122037`
- Campagner et al. (2021), *Three-way decision and conformal prediction*, Inf. Sci. 579 —
  `10.1016/j.ins.2021.08.009`
- Grisci et al. (2021), *Relevance aggregation ... on tabular data*, Inf. Sci. 559 —
  `10.1016/j.ins.2021.01.052`
- plus Tanha et al. (2022, CPSSDS), Kamiran et al. (2018, reject option), Shen et al. (2022, reject
  inference) — all `10.1016/j.ins.*` — and 13 further conformal/selective/tabular/UQ references
  (Papadopoulos 2002, Vovk 2013, Barber 2021 jackknife+, Gibbs & Candès 2021, Romano 2019 CQR,
  Chow 1970, Herbei & Wegkamp 2006, Cortes et al. 2016, Grinsztajn 2022, Gorishniy 2021, Schultz 2024,
  Abdar 2021, Gawlikowski 2023). The full BibTeX (with the added entries verified) is in `refs.bib`.

## GATE-0 checklist (Information Sciences)

| Item | Status | Where |
|---|---|---|
| Manuscript (elsarticle, single-column double-spaced for review) | DONE | `paper_els.tex` |
| Highlights (3–5 bullets, ≤85 chars each) | DONE | `highlights.txt` |
| Keywords (≤6) | DONE | 6 keywords in `\begin{keyword}` |
| Abstract (single paragraph) | DONE | front matter; **TODO-USER: confirm ≤ ~200 words if the journal enforces a cap** |
| CRediT authorship contribution statement | DONE | in `paper_els.tex` |
| Declaration of competing interest | DONE (none declared) | in `paper_els.tex` |
| Data availability statement | DONE | in `paper_els.tex` |
| References numbered `[n]`, order-of-appearance, with titles | DONE | `elsarticle-num` |
| Cover letter | DONE | `cover_letter.md` |
| Author affiliation (org/city/country) | **TODO-USER** | `\affiliation[inst1]` placeholders |
| ORCID (0009-0001-8329-0108) | supply in EM portal | front matter comment |
| Funding statement | **TODO-USER** | Funding section |
| Declaration of generative-AI use | **TODO-USER** | GenAI section (or delete if N/A) |
| Suggested reviewers (3–5) | **TODO-USER** | `cover_letter.md` |
| Citation author lists for the 2026-wave arXiv `@misc` entries | pending human verification (same as canonical) | `refs.bib` |

## Build stats (last clean build)

- `latexmk` exit 0, **44 pages** (single-column, *double-spaced* `review` mode — the final typeset
  Information Sciences article will be roughly half this; the canonical `article`-class build is 23
  pages). 0 errors, 0 undefined citations/references, 0 overfull boxes > 20 pt, **46 references**
  resolved via `elsarticle-num`.
- Information Sciences imposes no hard page limit on full-length research articles; length is
  acceptable for the venue.

## Note on the forthcoming p5 TableShift subsection

A confirmatory TableShift (p5) results subsection is planned for later integration. Because
`paper_els.tex` mirrors the canonical section skeleton exactly, that subsection should be added to
`../paper.tex` first and then re-ported here (re-run the front-matter wrap; the only local hand-edit is
the Table 1 `\resizebox`).
