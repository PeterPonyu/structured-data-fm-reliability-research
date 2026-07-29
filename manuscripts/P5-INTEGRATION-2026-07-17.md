# P5 (TableShift confirmatory arm) integration into the structured-data paper

**Source of truth:** `p5_tableshift_pulled_2026-07-17/p5_tableshift_remedy_2026-07-15/{RESULTS.md,results.json,p5_*.json}`,
`experiments/p5_tableshift_remedy.py` docstring, `PREREG-REMEDY-EVAL-2026-07-13.md`,
`experiments/tableshift_registry.py`. Aggregate verdict: 9/9 tasks ok, **H1 = REJECT**, **H2 = CONFIRM**,
frozen venue read = DMKD (primary).

**Note:** this file was edited by two independent passes in the same session (a second agent added the
abstract sentence and wrapped both new tables in `\resizebox`; this pass added the body subsection, the
Discussion sentence, and a table-width fix). Both passes' edits landed on non-overlapping text spans and
compose cleanly — verified below with forced rebuilds of the final on-disk state, not assumptions.

## Placement

No standalone P5/TableShift design doc exists under `docs/`; the runner docstring and the existing
`\subsection*{Exploratory audit: do distribution-free remedies restore group-conditional coverage? (No.)}`
both say the confirmatory test is "reserved for a held-out TableShift family the exploratory data cannot
contaminate." Placement used: a new `\subsection*{Confirmatory coverage-remedy evaluation on the held-out
TableShift roster}` immediately after that subsection and before `\section{Discussion}`, in all three
manuscripts (`manuscripts/paper.tex`, `manuscripts/springer_dmkd/paper_svjour.tex`,
`manuscripts/infosci/paper_els.tex`; body prose is identical across all three except venue-specific figure
widths and citation style, confirmed by diff before editing). `.bak-pre-p5` backups exist for all three,
reconstructed to exactly the pre-edit state (verified: diffing each backup against the edit's own old-strings
is empty).

Also updated: the "future work" sentence in the existing Folktables/ACS subsection (previously promised a
"full confirmatory TableShift run is deferred to future work"), now points forward to the new subsection
instead of promising it; and one sentence folded into the Discussion section's coverage-restoration paragraph
tying the confirmatory replication to the exploratory G1 finding (there is no separate `\section{Conclusion}`
in this paper; Discussion is the terminal narrative section). The abstract in all three files also gained a
closing sentence stating the H1/H2 verdicts (added by the concurrent pass; verified accurate against the
numbers below, left as-is).

## Numbers used (exact, from `results.json`'s `aggregate` block)

- Roster: 9/9 tasks ok, `full_coverage=true`, K=20 split-repeats each, N=400-bootstrap CIs.
- 3 excluded-by-rule (endpoint `marginal_gap_only`, 0 eval groups): `diabetes_readmission`, `nhanes_lead`,
  `physionet`. 6 evaluable: `brfss_diabetes` (primary, 5 groups), `acsunemployment` (primary, 15 groups),
  `brfss_blood_pressure` (fallback/AGEG5YR, 7), `acsincome` (fallback/AGEP, 71), `acspubcov` (fallback/AGEP,
  50), `acsfoodstamps` (fallback/AGEP, 44).
- H1: `n_any_remedy_restores_coverage` min/median/max across K = 3/3.0/4; majority threshold = 4 -> **REJECT**.
  Per remedy: weighted_cp 3/3.0/4, mondrian_inferred 0/0.0/0, mondrian_unc_decile 0/0.0/1.
  `median_split_conformal_worst_group_cov` = 0.7968 -> 0.797; `median_split_conformal_group_gap` = 0.1345 ->
  0.135. Supplementary multiplicity (gap-reduction, k0, Holm/BH): reject on 5/6 tasks (all but
  `acsunemployment`, p=0.165).
- H2: `n_uncertainty_ties_or_beats_tuned` = 6/6.0/6 (constant across all 20 repeats) -> **CONFIRM**.
  Supplementary multiplicity (repair-ratio delta, tuned-minus-uncertainty): p=1.000 on all 6 tasks, no reject.
- Descriptive marginal id_test-vs-ood_test gap (only 3/9 tasks have `id_test_available=true`):
  `physionet` +0.094, `brfss_diabetes` +0.040, `diabetes_readmission` -0.018.
- Venue read (frozen §2 mapping, H1 rejected + H2 confirmed): DMKD (primary).

## Deviations disclosed (mechanical loader adapters, per house style, no internal filenames rendered)

One paragraph in the new subsection covers all three, cross-checked against `tableshift_registry.py`:
(i) categorical domain-column passthrough for ACS tasks (frozen empty `PreprocessorConfig` + domain column
only); (ii) case-corrected isolated cache directory for the NHANES loader (works around an uppercase/
lowercase filename mismatch in TableShift's own downloader that would otherwise silently substitute BRFSS
data lacking the needed fields); (iii) `usecols`-restricted reads for the wide ACS person/household files
(memory only, no content change). Validated by reproducing `acsincome` against a `.goodref` reference file
before adoption — diffed field-by-field: only `elapsed_sec` and `timestamp_utc` differ, everything else
byte-identical. No endpoint rule was modified.

## Table content

`tab:p5roster` (9 rows): per-task frozen endpoint, n-groups, H1/H2-tally membership. `tab:p5verdict`: median
split-conformal worst-group coverage/gap, per-remedy min/median/max restoration counts, H1/H2 verdict rows.
No dash placeholder cells in either table.

## Build status (forced rebuilds of final on-disk state, `latexmk -g`, just run)

| Build | latexmk exit | Pages (was, before P5) | New overfulls vs. pre-P5 baseline |
|---|---|---|---|
| `manuscripts/paper.tex` | 0 | 23 (21) | none — all 6 pre-existing warnings unchanged in magnitude/content, only line numbers shifted |
| `manuscripts/springer_dmkd/paper_svjour.tex` | 0 | 25 (22) | none — one new 3.99pt table overfull was introduced and fixed (`\footnotesize`+`\tabcolsep`, matching this file's own existing convention for its wide FM table); final set matches pre-P5 baseline exactly |
| `manuscripts/infosci/paper_els.tex` | 0 | 47 (42) | none — two new overfulls (50.5pt, 41.3pt, both new tables exceeding the elsarticle column) were introduced and fixed the same way; the concurrent pass's `\resizebox` wrap on top of that fix is redundant but harmless (verified: table renders at normal, readable size, page 31-32) |

Baselines established by temporarily rebuilding each file's `.bak-pre-p5` copy in place and diffing warning
sets against the final build — not assumed. Changed pages rendered to PNG and visually inspected: `paper.tex`
pp. 15-17 (subsection heading, both tables, Discussion sentence), `paper_svjour.tex` pp. 17-19, `paper_els.tex`
pp. 30-32 — all render without truncation, overlap, or illegible text in any of the three.

## Known pre-existing cosmetic issue (not introduced by this edit, not fixed)

`paper_els.tex` (InfoSci/elsarticle build only) double-periods every `\paragraph{...}` title that itself ends
in `.` or `)` — e.g. the pre-existing `\paragraph{The mechanism.}` renders as "The mechanism..", identically
to this pass's new `\paragraph{H2: ... (CONFIRM).}`. This is an elsarticle-class-wide rendering quirk present
before this edit; new paragraph titles were kept consistent with the existing house style (ending in a
period) rather than diverging to work around it. Flagging for a separate pass if the venue submission wants
it cleaned up document-wide.
