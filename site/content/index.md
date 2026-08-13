# Conformal Coverage Fails Under Grouped and Temporal Shift but Uncertainty Abstention Repairs Selective Risk: A Preregistered Tabular Audit

<p class="meta">Zeyu Fu · State Key Laboratory of Trauma and Chemical Poisoning, Institute of Combined Injury, Army Medical University, Chongqing, China · <a href="mailto:fuzeyu09@gmail.com">fuzeyu09@gmail.com</a></p>

<p class="meta">Submitted to <em>Knowledge-Based Systems</em>. DMKD track superseded.</p>

{{verdict_table}}

<p>Scope: no financial, medical, or business deployment claims.</p>

<p>
  <a href="https://github.com/PeterPonyu/structured-data-fm-reliability-research/blob/main/manuscripts/kbs/paper_kbs.pdf">Submitted PDF</a>
  ·
  <a href="https://github.com/PeterPonyu/structured-data-fm-reliability-research">GitHub</a>
  ·
  Zenodo DOI <a href="https://doi.org/10.5281/zenodo.21130297">10.5281/zenodo.21130297</a> (reserved draft; not yet public)
</p>

## Thesis

<ol class="thesis">
  <li>Random-split validation overstates reliability for keyed tabular models: the split that matters at deployment is leave-group-out or rolling-origin, not a row-wise hold-out.</li>
  <li>On 14 public OpenML datasets with a defensible entity or time key, grouped and temporal splits push plain split-conformal below its 0.90 target (median worst-group coverage about 0.81 on the held-out TableShift arm).</li>
  <li>No tested distribution-free conformal remedy restores group-conditional coverage at the majority level (<strong>H1 REJECT</strong>).</li>
  <li>Ranking the same test items by a free uncertainty score and abstaining on the highest-risk ones beats random deferral on 13 of 14 exploratory datasets and matches a budget-matched tuned selector on held-out TableShift (<strong>H2 CONFIRM</strong>).</li>
  <li>Repair remains far below an oracle ceiling (median repair ratio 0.34 vs 0.75); the prescription is selective-risk fallback, not a restored coverage guarantee.</li>
  <li>The collapse is model-agnostic across XGBoost, LightGBM, TabICLv2, and TabDPT: tabular foundation models do not auto-repair the gap.</li>
  <li>The preregistered Stage-2 conjunctive gate evaluates to <strong>KILL</strong> because the grouped-gap count is split-realization-fragile and key-inclusion-sensitive; only the repair count is load-bearing.</li>
  <li>The contribution is a reusable protocol — keyed split comparison, coverage test, uncertainty abstention fallback — not a new estimator.</li>
</ol>
