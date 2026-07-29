# Text Polish Pass — 2026-07-17

Scope: `springer_dmkd/paper_svjour.tex` (primary), `paper.tex`, `infosci/paper_els.tex`.
Backups: `*.bak-pre-textpolish` for each file. Figure files/scripts untouched.

## Task 1 — Decorative LaTeX inventory

| Command | Before | After |
|---|---|---|
| `\textbf` | 8 | 6 |
| `\emph` | 12 | 9 |
| `\textit`, `\underline`, `\textsc`, color/box commands | 0 | 0 |
| `\paragraph{...}` (run-in headings) | 24 | 24 (unchanged) |

All 24 `\paragraph` run-in headings are the class's structural mechanism (used throughout Methods/Results/Discussion/Limitations); none are manually-bolded fakes, so none needed converting. Reported as "kept" — structural, not decorative.

**`\textbf` kept (6, all judged load-bearing):**
- 2× first/only definitional statement of the two preregistered hypotheses ("Frozen ahead of any confirmatory number: **H1 (coverage restoration)**...; **H2 (selective prescription)**...") — the sole place these terms are defined.
- 4× cells in the confirmatory verdict table (`tab:p5verdict`): **H1 (coverage restoration)** / **REJECT**, **H2 (selective prescription)** / **CONFIRM** — the single scannable bottom-line row among many statistic rows in that table.

**`\textbf` removed (2):** "H1 is REJECTed." and "H2 is CONFIRMed." — both were redundant reinforcement immediately after paragraph headings that already state `(REJECT)`/`(CONFIRM)` in their titles; unbolded to plain text, sentence kept.

**`\emph` removed (3), reasons:**
- `selective` — 2nd use (line ~109), repeat of the abstract's first use (line 48).
- `post-hoc reinterpretation` — 2nd verbatim use (in the Results-opener paragraph, cut as part of the redundancy trim below); first use in Introduction kept.
- `post-hoc` — 3rd instance of the same term family (ACS section); habitual, not a new contrastive first-use.

**`\emph` kept (9):** first-use technical/contrastive terms — `grouped`, `collapse` (abstract), `uncertainty-taxonomy`, `post-hoc reinterpretation` (first use, Intro), `exchangeable`, `confirmatory`, `exploratory/descriptive`, `distribution-free` — each appears once and marks a term central to the paper's precise scoping.

No colored text, boxes, frames, `\textsc`, or `\textit` were found in any of the three files.

## Task 2 — Redundancy cuts

1. **Results-section confirmatory/exploratory paragraph** (`\section{Results}` opener). Cut the clause fully re-deriving the Stage-2 gate's KILL verdict and the "why both a KILL and a SUCCESS would have been uninformative" justification — this is stated in full in `\cref{sec:limitations}`, which the paper's own Limitations section explicitly says is meant to be the single place this is stated ("stated here once, in full, rather than scattered across the paper"). Replaced with a short pointer.
   - Before: "...\Cref{sec:limitations} gives the dedicated rigor check behind that labeling choice: it reports plainly that our conjunctive Stage-2 gate on the gap count evaluated to KILL under the reconciled protocol, and that the confirmatory/exploratory labels used throughout this section are therefore a *post-hoc reinterpretation* adopted after that failure, not a claim of overall preregistered success---together with the full split-realization fragility analysis showing why both a KILL and a SUCCESS on that single-draw gate would have been uninformative."
   - After: "...\Cref{sec:limitations} gives the dedicated rigor check behind that labeling choice: our conjunctive Stage-2 gate on the gap count evaluated to KILL under the reconciled protocol, so the confirmatory/exploratory labels used throughout this section are a post-hoc reinterpretation, not a claim of overall preregistered success."
   - No numbers in this clause; ~26 words cut.

2. **"Roster and frozen endpoint rule" paragraph** (TableShift confirmatory section) restated "frozen ... before any confirmatory number was ..." three times in one paragraph. Cut the 2nd and 3rd restatements, keeping the fact stated once plus the two new points each sentence was actually making (fallback-heavy composition; endpoint-blind construction).
   - Before: "The frozen rule chose this split mechanically, before any confirmatory number was inspected, but..." / "The rule itself is pre-committed and endpoint-blind---frozen before any task's confirmatory number existed, and it selects an endpoint..."
   - After: "That split was chosen by the same frozen rule, and..." / "The rule is endpoint-blind---it selects an endpoint..."
   - No numbers touched (the `$4$`/`$6$` task counts in between are untouched); ~45 words cut.

3. **Table~\ref{tab:learned} prose** immediately preceding the table restated the same three medians the table displays two lines below.
   - Before: "...with statistically indistinguishable median repair ratios ($0.339$ vs.\ $0.338$), both far below the oracle ceiling of $0.745$ (ranking by the true loss)."
   - After: "...with statistically indistinguishable median repair ratios, both far below the oracle ceiling (Table~\ref{tab:learned}; oracle ranks by the true loss)."
   - This is the one cut that removes numeric tokens from prose (`0.339`, `0.338`, `0.745`); all three values remain intact in the table itself and in the abstract/Introduction (each value's other occurrences were untouched — verified below).

No throat-clearing openers or 3-deep nested parentheticals were found elsewhere worth cutting; the paper's heavy confirmatory/exploratory hedging is substantive disclosure (required by its own preregistration framing), not filler, so it was left alone outside the three cuts above.

## Numeric safety check

Ran a whole-document numeric-token diff (old backup vs. new) for all three files: on changed lines, the only numeric tokens removed-without-being-re-added were `0.338`, `0.339`, `0.745` (the intentional Table~\ref{tab:learned} duplicate-trim, cut #3 above); zero new numeric tokens were introduced anywhere; and — critically — **zero numeric tokens vanished from any document entirely** (all three values still appear in their tables/earlier mentions). Identical result for all three files. No number, citation, or table value changed.

## Word counts

| File | Before | After | Δ |
|---|---|---|---|
| `springer_dmkd/paper_svjour.tex` | 9363 | 9313 | −50 |
| `paper.tex` | 9363 | 9313 | −50 |
| `infosci/paper_els.tex` | 9611 | 9561 | −50 |

## Build

`latexmk -pdf` on `springer_dmkd/paper_svjour.tex`: **exit 0**. Page count unchanged at **28 pages** before and after (the trim was too small to shift a page break). `paper.tex` and `infosci/paper_els.tex` left edited but not rebuilt, per instructions.
