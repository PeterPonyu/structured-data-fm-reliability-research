# Cover letter — Data Mining and Knowledge Discovery (DMKD, Springer)

Date: 17 July 2026

Dear Prof. Hüllermeier, Editor-in-Chief,

We submit our manuscript, "Group- and Time-Split Coverage in Tabular Models Fails to Certify, but
Uncertainty Abstention Robustly Repairs Selective Risk: A Preregistered Audit with Held-Out
Confirmatory Replication," for consideration in *Data Mining and Knowledge Discovery*.

Tabular models are routinely validated with random splits, but deployment shifts are usually
grouped --- a new entity, region, or time period. Across 14 public OpenML datasets carrying an
entity or time key, and a preregistered, held-out confirmatory replication on TableShift, the paper
shows two things. First, moving to leave-group-out or rolling-origin splits leaves split-conformal
coverage below its nominal target, and no tested distribution-free remedy restores it at the
majority level. Second, the repairable part is selective risk: uncertainty-ranked abstention beats
random deferral on 13 of 14 datasets, model-agnostically across gradient-boosted models and tabular
foundation models, surviving multiplicity correction and confirmed without exception on the held-out
tasks. The resulting prescription is deliberately minimal --- plain split-conformal plus uncertainty
abstention, scoped to selective reliability rather than a coverage guarantee.

As a benchmark-and-audit study with a preregistered confirmatory arm and honestly reported negative
results, we believe the paper sits squarely in DMKD's tradition of rigorous evaluation and benchmark
contributions. The manuscript states its preregistration outcomes plainly, including which counts
are confirmatory and which are exploratory.

This manuscript is original work and is not under consideration elsewhere.

Thank you for your consideration.

Sincerely,

Zeyu Fu\
ORCID: 0009-0001-8329-0108\
e-mail: fuzeyu09@gmail.com\
State Key Laboratory of Trauma and Chemical Poisoning, Institute of Combined Injury,\
Army Medical University, Chongqing, China

---
**Note on venue (record only; optional in the pasted letter):** an earlier port of this kit targeted
*Machine Learning* (Springer). We retargeted to DMKD per the study's own frozen venue rule after the
remedy evaluation returned a confirmed negative on coverage restoration.

**Suggested reviewers** (portal field — TODO-USER: supply three; leave blank if you prefer the
editors choose): expertise areas (a) conformal prediction / selective classification, (b) tabular ML
(gradient boosting / tabular foundation models), (c) distribution shift / reliability under
group/temporal shift.
