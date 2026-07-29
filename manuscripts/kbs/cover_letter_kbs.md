Dear Prof. Jie Lu,

We submit "Conformal Coverage Fails Under Grouped and Temporal Shift but Uncertainty Abstention Repairs Selective Risk: A Preregistered Tabular Audit" for consideration in Knowledge-Based Systems.

The manuscript presents an explicit-key decision protocol for testing whether reliability claims survive the grouped or temporal split expected at deployment. It separates two questions that are often conflated: whether a conformal coverage guarantee transfers, and whether uncertainty can still improve retained-set selective risk when that guarantee fails. Practitioners compare random with leave-group-out or rolling-origin evaluation, test coverage under the deployment-aligned split, and use model-native uncertainty for abstention only as a selective-risk fallback.

Across 14 keyed OpenML datasets and four configurations spanning gradient boosting and tabular foundation models, grouped and temporal evaluation exposes reliability degradation, but the preregistered Stage-2 gate on the majority degradation count evaluates to KILL after reconciling RNG order and key inclusion. We therefore report that count as a split-realization distribution, not a confirmed majority finding. A separate held-out, preregistered TableShift evaluation has nine open tasks, six evaluable under a frozen endpoint rule. It rejects coverage restoration by the tested remedies (H1 REJECT) while the free uncertainty score ties or beats a budget-matched, 12-trial-tuned selector on all six evaluable tasks across all 20 repeats (H2 CONFIRM). Four of six endpoints use the frozen fallback construct, which the manuscript discloses explicitly.

This combination of explicit deployment keys, auditable decision rules, negative remedy evidence, and reproducible held-out evaluation fits Knowledge-Based Systems as decision support under distribution shift rather than as a new conformal algorithm.

The manuscript is original, is not under consideration elsewhere, and all declarations accompany the submission.

Sincerely,
Zeyu Fu
fuzeyu09@gmail.com
