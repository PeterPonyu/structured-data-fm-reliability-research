# Draft blocks for G1 / G2 / G3 (NOT yet integrated into paper.tex)

Prepared 2026-07-11 for the *Machine Learning* (Springer) submission per the
WORKLOAD-GAP-MEMO. **These are drafts for review — `paper.tex` is untouched.**
Integration is one reviewed edit after team-lead verification. G1 numbers trace
to `results_expansion_2026-07-11/nd1_learned_selector_baseline.json`; G2/G3 are
writing-only (no experiment).

---

## G1 — learned-selector baseline result + disclosure paragraph

**Experiment (ran, CPU):** a learned post-hoc abstention selector — a small
XGBoost regressor (100 trees, depth 3) trained on the *calibration fold's*
prediction-level features (classification: max-prob, entropy, margin, $1-\max p$;
regression: interval width, point, lower, upper) to predict per-example loss,
using its predicted risk as the abstention score — evaluated against the paper's
free model-native uncertainty score and the random-deferral floor in the
identical risk-coverage frame (same test folds, calibration carve-out, and AURC
functions, imported from `nd1_split_conditioned_audit.py`; the selector sees only
calibration data). XGBoost Stage-1 arm, 14 keyed datasets, grouped split.

**Result (grouped split, `nd1_learned_selector_baseline.json`):**

| | count / value |
|---|---|
| uncertainty beats random deferral | **13/14** (reproduces the paper's headline exactly — frame parity check) |
| learned selector beats random deferral | 12/14 |
| head-to-head, uncertainty **wins** (Δ CI $<0$) | **8/14** |
| head-to-head, learned **wins** (Δ CI $>0$) | 3/14 (all regression: `Airlines_DepDelay_10M`, `nyc-taxi-green`, `house_sales`) |
| head-to-head, tie (Δ CI spans 0) | 3/14 |
| median repair ratio: uncertainty / learned / oracle | **0.339 / 0.338 / 0.745** |

**Honest reading:** the free uncertainty score is **not** a low bar — it matches
a trained meta-abstainer (near-identical median repair, 0.339 vs 0.338) and
*wins the head-to-head on 8 datasets while losing on only 3*, all three regression
tasks where a learned selector can exploit interval geometry beyond raw width.
On classification the uncertainty score is never beaten. The learned selector
also needs calibration *errors* to train, and grouped splits with a dominant
group leave thin calibration folds (`adult` 56, `cylinder-bands` 45 rows), where
it is high-variance — a structural disadvantage the free score does not share.
Both selectors sit far below the oracle ceiling (0.745), i.e. neither is close to
the best-achievable abstention.

**Draft paragraph (Results, after the repair result):**

> To check that abstention's advantage over random deferral is not merely the
> low bar of beating a coin flip, we compare the free model-native uncertainty
> score against a *learned* post-hoc selector — a small gradient-boosted model
> trained on the calibration fold to predict per-example loss from
> prediction-level features (max-probability, entropy, margin for classification;
> interval width and endpoints for regression) — in the identical risk-coverage
> frame (Table~\ref{tab:learned}). Across the 14 keyed datasets under the grouped
> split, the uncertainty score wins the head-to-head on 8 and loses on only 3
> (all regression, where the selector exploits interval geometry), with three
> ties; the median repair ratios are statistically indistinguishable (0.339 vs
> 0.338), and both remain far below the oracle ceiling (0.745). The learned
> selector additionally requires calibration errors to fit, which the
> dominant-group splits (\texttt{adult}, \texttt{cylinder-bands}) barely supply.
> We therefore report the free uncertainty score as the recommended abstention
> signal — competitive with a trained selector and never beaten on classification
> — while disclosing that a learned selector offers a small, dataset-specific edge
> on some regression tasks.

*(This is the honest disclosure the memo required: the learned baseline DOES win
on 3 regression datasets, reported plainly, not massaged.)*

---

## G2 — scope-defense block (keyed-by-construction census)

**Draft (Data & Methods, or a "Scope of the suite" paragraph):**

> **On suite size.** Our headline suite is 14 OpenML datasets, an order of
> magnitude smaller than the 68–111-dataset sweeps typical of tabular *benchmark*
> papers. This is deliberate and constitutive of the study rather than a
> convenience cut: the object of the audit is the *reliability gap under a
> defensible deployment shift*, which requires each dataset to carry a genuine
> entity- or time-key along which a leave-group-out / rolling-origin split
> corresponds to a real distributional change (a new region, merchant, facility,
> or future period). Most tabular benchmark datasets have no such key — an
> arbitrary column split is not a deployment shift — so breadth and
> key-defensibility trade off directly. We therefore ran a three-pass census over
> the OpenML catalogue (name-level candidate screen $\to$ true-cardinality and
> group-balance filter $\to$ hand vetting of each candidate key for deployment
> meaning), which reduced 145 candidate datasets to 23 and then to the 14 with a
> reviewer-defensible key (the frozen census is in
> \texttt{census\_final\_triage.json}). To show the findings are not an artifact
> of this curation we additionally report a 30-dataset breadth extension that adds
> 16 datasets grouped on an \emph{arbitrary} categorical key (Appendix~\ref{...}):
> the repair result persists there, but we keep those datasets out of the headline
> precisely because an arbitrary-key split is not a genuine shift. The suite is
> thus scoped by construction — every headline dataset is one where "grouped
> split" means something — and breadth is supplied by the extension without
> diluting that guarantee.

---

## G3 — formal validity statement (coverage under group shift)

**Draft (Methods, "Why the collapse is expected" — a short formal note, no new
experiment):**

> **Why grouped splits break split-conformal coverage.** Split conformal
> prediction guarantees marginal coverage $\Pr(Y_{n+1}\in \hat C(X_{n+1}))\ge
> 1-\alpha$ under a single assumption: the calibration points
> $(X_i,Y_i)_{i=1}^{n}$ and the test point $(X_{n+1},Y_{n+1})$ are
> \emph{exchangeable} \citep{vovk2005algorithmic,lei2018distribution}. Under a
> random split this holds by construction. Under a leave-group-out / rolling-origin
> split it does \emph{not}: the calibration fold is drawn from the training groups
> $\mathcal G_{\text{tr}}$ while the test point is drawn from disjoint held-out
> groups $\mathcal G_{\text{te}}$, so calibration and test are governed by
> different group-conditional laws $P(\cdot\mid g)$ and are no longer exchangeable.
> The nonconformity scores are then not exchangeable across the calibration/test
> boundary, and the finite-sample coverage guarantee is void — coverage can fall
> arbitrarily below $1-\alpha$ by the amount the score distribution shifts between
> groups. This is the exact regime studied by
> \citet{tibshirani2019covariate,barber2023beyond}: recovering distribution-free
> coverage under such shift requires either a known/estimated likelihood ratio
> between the group laws (weighted conformal) or an explicit robustness budget —
> neither of which a practitioner running plain split conformal supplies. Our
> empirical collapse (Sec.~\ref{sec:results}) is therefore the predicted
> consequence of applying an exchangeability-dependent procedure across a
> group boundary that breaks exchangeability. The abstention repair sidesteps the
> premise rather than restoring it: uncertainty-ranked selective prediction makes
> no exchangeability claim, and by declining the least-confident retained points
> it restores low *conditional* risk on the accepted set without needing the
> group-conditional laws to match — which is why it survives where marginal
> split-conformal coverage does not.

**Citations to add (verified 2026-07-11):**

- `vovk2005algorithmic` — already in the paper (split-conformal exchangeability premise).
- `lei2018distribution` — Lei, G'Sell, Rinaldo, Tibshirani, Wasserman, "Distribution-Free Predictive Inference for Regression," *JASA* 113(523):1094–1111, 2018.
- `tibshirani2019covariate` — Tibshirani, Foygel Barber, Candès, Ramdas, "Conformal Prediction Under Covariate Shift," *NeurIPS 32*, 2019 (arXiv:1904.06019).
- `barber2023beyond` — Barber, Candès, Ramdas, Tibshirani, "Conformal Prediction Beyond Exchangeability," *Annals of Statistics* 51(2):816–845, 2023 (arXiv:2202.13415).

## Sources (citation verification)

- [Conformal Prediction Under Covariate Shift (arXiv:1904.06019)](https://arxiv.org/pdf/1904.06019)
- [Conformal prediction beyond exchangeability (Annals of Statistics 2023; arXiv:2202.13415)](https://projecteuclid.org/journals/annals-of-statistics/volume-51/issue-2/Conformal-prediction-beyond-exchangeability/10.1214/23-AOS2276.full)
