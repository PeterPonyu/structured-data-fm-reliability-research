# Cover letter — Information Sciences (Elsevier)

Date: TODO-USER

Dear Editor-in-Chief and Editorial Board,

We submit our manuscript, **"Group- and Time-Split Reliability Collapse in Tabular Models is
Model-Agnostic and Partly Repairable by Uncertainty Abstention,"** for consideration in *Information
Sciences* as an original research contribution: a controlled, preregistered reliability audit of
tabular machine-learning models under grouped and temporal distribution shift.

Tabular models are routinely validated with random splits, but real deployment shifts are almost
always grouped — a new entity, region, or time period. On 14 public OpenML datasets that carry a
defensible entity- or time-key, the paper shows that moving from a random split to a
leave-group-out / rolling-origin split causes a large reliability collapse: risk–coverage degrades
suite-wide and split-conformal coverage drops below its nominal target, chiefly on temporal splits.
The load-bearing positive finding is a *repair*: uncertainty-ranked abstention improves selective
reliability substantially over random deferral, beating it on 13 of 14 datasets model-agnostically
across four open, token-free configurations spanning three architecture families (two gradient-boosted
models — XGBoost and LightGBM — and two tabular foundation models — TabICLv2 and TabDPT), surviving
Holm–Bonferroni correction, holding with and without the group key as a feature, and holding under
hyperparameter tuning and repeated split draws. The practical recommendation is deliberately minimal:
plain split-conformal plus uncertainty abstention, with no foundation model, license token, or
Mondrian taxonomy required.

**Fit for Information Sciences.** The paper sits directly within a conformal-prediction and
selective-classification line the journal actively publishes — including the isomorphisms between
three-way (cautious) decision-making and conformal prediction (Campagner et al., *Inf. Sci.* 579,
2021), the pairing of conformal and selective classification through a conjunction-subspaces test (He
et al., *Inf. Sci.* 707, 2025), streaming conformal prediction (Tanha et al., *Inf. Sci.* 584, 2022),
and reject-option methods for tabular decision pipelines (Kamiran et al., *Inf. Sci.* 425, 2018; Shen
et al., *Inf. Sci.* 606, 2022). Our contribution to that line is a rigorously validated empirical
object rather than a new estimator: a split-type × reliability × selective-abstention measurement with
preregistered nulls, multiplicity correction, repeated-split-draw confidence intervals, a
root-caused-and-fixed cross-run reproducibility defect, and an honest map of which distribution-free
remedies do and do not close the coverage gap. We believe this audit-style rigor is well matched to the
journal's editorial emphasis on thorough validation, ablation, and reproducibility.

**Candor about scope.** The manuscript states its status plainly rather than overclaiming. The
Stage-2 preregistered gate was conjunctive and evaluated to KILL under the reconciled protocol, so the
confirmatory-versus-exploratory partition we then use is a disclosed post-hoc reinterpretation; the
grouped-gap count is reported as a fragile, realization-sensitive statistic that we deliberately do not
lead with; the coverage-remedy evaluation is explicitly exploratory (its confirmatory test on a
held-out TableShift family is reserved and preregistered, not yet run); and the mechanistic explanation
for the Mondrian add-on's failure is reported as real-but-key-dependent. We treat these negative and
conditional results — surfaced in the abstract itself — as a core part of the paper's rigor.

We confirm that this manuscript is original, has not been published previously, and is not under
consideration for publication elsewhere in whole or in part. The single author has approved the
submission and declares no competing interests. All datasets are public (OpenML tasks and US Census
ACS PUMS 2018); the frozen result records and the figure scripts that regenerate every figure from
those records accompany the submission, and the code is archived at Zenodo (DOI reserved on a draft
deposition, to be released on publication).

Thank you for your consideration.

Sincerely,

Zeyu Fu
TODO-USER: affiliation line (department, institution, city, country)
e-mail: fuzeyu09@gmail.com
ORCID: 0009-0001-8329-0108

---

**Suggested reviewers** (TODO-USER: supply 3–5; leave blank if you prefer the editors choose). Pick
reviewers without a recent co-authorship or shared-institution conflict with the author:
1. TODO-USER — expertise: conformal prediction / selective classification.
2. TODO-USER — expertise: tabular machine learning (gradient boosting / tabular foundation models).
3. TODO-USER — expertise: distribution shift / reliability and calibration under group/temporal shift.

**Note on venue history:** an earlier port of this manuscript targeted a Springer venue (*Data Mining
and Knowledge Discovery*). It was retargeted to *Information Sciences* because the journal carries the
deepest in-venue precedent for this exact paper type (conformal prediction, selective classification,
tabular reliability) and an editorial screen that rewards rigorous, well-validated audit-style
contributions. No claims or numbers changed in the retarget; only the manuscript class and venue
framing differ.
