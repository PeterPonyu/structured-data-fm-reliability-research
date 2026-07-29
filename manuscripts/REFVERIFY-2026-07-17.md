# Reference Accuracy + Ordering Verification — DMKD submission (2026-07-17)

Build: `manuscripts/springer_dmkd/paper_svjour.tex` / `paper_svjour.bbl` (45 rendered entries), sourced from `refs.bib` + `shared.bib`.

## Task 1 — Reference accuracy (live verification of all 45 .bbl entries)

Verified live against arXiv abstract pages, DOI resolver (doi.org), Crossref API, DBLP, NeurIPS/ICLR proceedings pages, and publisher pages (Elsevier/ScienceDirect, Springer, IEEE Xplore, Wiley, Project Euclid, Nature).

| # | Key | Verdict | Notes |
|---|---|---|---|
| 1 | geifman2017selective | VERIFIED | DBLP confirms authors/venue/pages 4878–4887 |
| 2 | chow1970reject | VERIFIED | DOI resolves to IEEE Xplore |
| 3 | herbei2006reject | VERIFIED | DOI resolves to Wiley |
| 4 | cortes2016rejection | VERIFIED | DOI resolves to Springer ALT chapter |
| 5 | jones2021selective | VERIFIED | ICLR 2021 poster + arXiv confirm authors |
| 6 | kamiran2018reject | VERIFIED | DOI resolves to ScienceDirect |
| 7 | papadopoulos2002inductive | VERIFIED | DOI resolves to Springer ECML chapter |
| 8 | vovk2005algorithmic | VERIFIED | DOI resolves to Springer book page |
| 9 | angelopoulos2023conformal | VERIFIED | DOI resolves to publisher (Now Publishers/Emerald) |
| 10 | vanschoren2014openml | VERIFIED | DOI resolves correctly; DBLP year note: commonly cited as 2014, acceptable |
| 11 | chen2016xgboost | VERIFIED | DOI resolves to ACM |
| 12 | ke2017lightgbm | VERIFIED | DBLP confirms author order + pages 3146–3154 |
| 13 | qu2026tabicl | VERIFIED | arXiv:2602.11139 matches title/authors |
| 14 | ma2024tabdpt | **FIXED** | Author order was wrong (Kamkari before Labach); arXiv:2410.18164 abstract page gives ...Hosseinzadeh, **Labach, Kamkari**, Cresswell... Corrected in refs.bib (+ mirrored in `../refs.bib`, `../infosci/refs.bib`) |
| 15 | tfm_uncertainty_esann2026 | VERIFIED | arXiv:2605.28554 matches |
| 16 | beyondiid2026 | VERIFIED | arXiv:2606.30410, 10-author order matches |
| 17 | tabpfn_openenv2025 | VERIFIED | arXiv:2505.16226 matches |
| 18 | helli2024driftresilient | VERIFIED | arXiv:2411.10634; genuinely accepted at NeurIPS 2024 (confirmed on arXiv listing) |
| 19 | tabpfn_uncdecomp2026 | VERIFIED | arXiv:2602.04596 matches |
| 20 | distreg_tfm2026 | VERIFIED | arXiv:2603.08206 matches |
| 21 | gardner2023tableshift | VERIFIED | NeurIPS 2023 D&B proceedings page confirms authors/venue |
| 22 | whyshift2023 | **FIXED** | Author order was wrong (Wang before Liu); NeurIPS D&B proceedings page gives **Liu, Jiashuo** first. Corrected in refs.bib (+ mirrored in `../refs.bib`, `../infosci/refs.bib`) |
| 23 | wildtab2023 | VERIFIED | Flagged as suspicious (solo author) pre-check; confirmed correct on arXiv:2312.01792 abstract page — sole author is genuinely Sergey Kolesnikov |
| 24 | subpop2025conformal | VERIFIED | arXiv:2506.05583 matches |
| 25 | audited2026conformal | VERIFIED | arXiv:2606.14909 matches |
| 26 | campagner2021threeway | VERIFIED | DOI resolves to ScienceDirect |
| 27 | he2025conjunction | VERIFIED | DOI resolves to ScienceDirect |
| 28 | shen2022reject | VERIFIED | DOI resolves to ScienceDirect |
| 29 | grisci2021relevance | VERIFIED | DOI resolves to ScienceDirect |
| 30 | tanha2022cpssds | VERIFIED | DOI resolves to ScienceDirect |
| 31 | gibbs2021adaptive | VERIFIED | arXiv:2106.00170; genuinely published NeurIPS 2021 (pp. 1660–1672) — note field already accurate, no change required |
| 32 | vovk2013conditional | VERIFIED | DOI resolves to Springer (Machine Learning journal) |
| 33 | barber2021jackknife | VERIFIED | DOI resolves to Annals of Statistics (Project Euclid) |
| 34 | grinsztajn2022trees | VERIFIED | arXiv:2207.08815; genuinely published NeurIPS 2022 D&B track — note field already accurate |
| 35 | gorishniy2021revisiting | VERIFIED | arXiv:2106.11959; genuinely published NeurIPS 2021 — note field already accurate |
| 36 | schultz2024convgen | VERIFIED | DOI resolves to ScienceDirect (Pattern Recognition) |
| 37 | abdar2021review | VERIFIED | Crossref confirms all fields |
| 38 | gawlikowski2023survey | VERIFIED | Crossref confirms; "Suppl 1" issue notation matches Springer's own listing |
| 39 | vovk2003mondrian | VERIFIED | Real working paper, found on Royal Holloway research portal |
| 40 | lei2018distribution | VERIFIED | Crossref confirms all fields |
| 41 | tibshirani2019covariate | VERIFIED | NeurIPS proceedings page confirms authors/venue |
| 42 | barber2023beyond | VERIFIED | DOI resolves to Annals of Statistics |
| 43 | ding2021retiring | VERIFIED | DBLP confirms authors/pages 6478–6490 |
| 44 | hollmann2025tabpfn | VERIFIED | Crossref/DOI resolves to Nature; confirmed TabPFN v2, vol 637 pp 319–326 |
| 45 | tabpfn25_2025 | VERIFIED | arXiv:2511.08667; full 26-author order matches exactly |

**Counts: 43 VERIFIED, 2 FIXED, 0 UNVERIFIABLE.**

### Fixes applied
Both fixes are author-order corrections (confirmed independently by a second live check against the primary source before editing), applied to `refs.bib` and mirrored identically to `../refs.bib` and `../infosci/refs.bib` (same entries existed verbatim in all three). A one-line `%` comment documenting the correction and source was added above each entry in all three files, per the existing convention (no changes to any rendering `note=` field).

- **ma2024tabdpt**: author order corrected from `...Kamkari, Hamidreza and Labach, Alex...` to `...Labach, Alex and Kamkari, Hamidreza...` (arXiv:2410.18164 abstract page).
- **whyshift2023**: author order corrected from `Wang, Tianyu and Liu, Jiashuo...` to `Liu, Jiashuo and Wang, Tianyu...` (NeurIPS 2023 D&B proceedings page).

Three entries (gibbs2021adaptive, grinsztajn2022trees, gorishniy2021revisiting) were double-checked for whether their existing venue `note=` fields ("NeurIPS 2021/2022 D&B track") were accurate placeholders vs. real venues — all three are genuinely published there, so the existing note text was left as-is (no defect to fix).

## Task 2 — Ordering

### (a) Citations
Extracted the full sequence of bracketed citation numbers from the compiled PDF (`pdftotext -layout`) in reading order, restricted to the body text (before the References section, which starts at line 1194 of the text dump). Flattened all comma/range groups (e.g. `[7–9]` → 7,8,9) and took the first occurrence position of each number 1–45.

**Result: the first-occurrence sequence is exactly 1, 2, 3, ..., 45 — strictly increasing, zero inversions.** The numeric style (`sn-mathphys-num.bst`) numbers by first citation, and it is behaving correctly here; no float-placement artifacts were observed in the citation numbering.

### (b) Figure/Table cross-references
Checked `\newlabel` entries in `paper_svjour.aux` for the true assigned numbers, and all `\ref{fig:...}`/`\ref{tab:...}` occurrences in `paper_svjour.tex` in source-line order.

**Tables: no violation.** First-\ref line numbers are strictly increasing: Table 1 (`tab:learned`, line 389) < Table 2 (`tab:fm`, line 447) < Table 3 (`tab:p5roster`, line 624) < Table 4 (`tab:p5verdict`, line 643).

**Figures: real violation, not a float artifact.** Assigned numbers (from `paper_svjour.aux`): `fig:overview`=1, `fig:f1`=2, `fig:f2`=3, `fig:f3`=4, `fig:f6`=5, `fig:f4`=6, `fig:f5`=7.

- `paper_svjour.tex:93` (Abstract) and `paper_svjour.tex:184` (Introduction) both write `Fig.~\ref{fig:f3}A` — i.e. **Figure 4** is first cross-referenced in the Abstract, before any other figure.
- **Figure 1** (`fig:overview`) is **never referenced via `\ref` anywhere in the body text** — it appears as a captioned figure on p.6 but is not pointed to by name/number in the prose.
- **Figure 2** (`fig:f1`) and **Figure 3** (`fig:f2`) are first referenced together at `paper_svjour.tex:289`, in the Results section — i.e. after Figure 4 has already been referenced twice.
- Figures 5, 6, 7 are first referenced at lines 326, 372, 534 respectively, correctly after 2/3 and in ascending order among themselves.

So the actual first-reference order is **4, 2, 3, 5, 6, 7** (Figure 1 never appears), rather than the expected 1, 2, 3, 4, 5, 6, 7. This is a genuine ordering violation, not a float-placement or `.bst`-sorting artifact — the Abstract and Introduction deliberately preview a Results-section panel (Figure 4A, the GBM-agnosticism scatter) to make an early argumentative point about GBM correlation, before the reader has encountered Figures 1–3. Per your instruction not to restructure the paper, no change was made; flagging for the author's decision (options: renumber so the previewed panel is Figure 1, add an explicit forward-reference caveat, or accept as an intentional preview and leave as-is).

## Build status
Ran `latexmk -pdf` after the two bib fixes. **Exit code 0.** No `undefined` or `multiply defined` warnings in the log (checked via `grep -i "undefined\|multiply defined"` — only unrelated LaTeX/hyperref/pdfTeX cosmetic warnings present, e.g. underfull hboxes and float-specifier/bookmark-level notices). `paper_svjour.bbl` was regenerated and confirmed to carry both corrected author orders (`Ma, Junwei ... Labach, Alex and Kamkari, Hamidreza ...` and `Liu et~al.` / `Liu, J., Wang, T., ...`). Output: 28 pages, `paper_svjour.pdf` rebuilt successfully.
