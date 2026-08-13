# Decision rule

A practitioner procedure matching the paper’s two contributions.

1. Compare **random** vs **leave-group-out / rolling-origin** on a dataset that actually has an entity or time key.
2. Test whether split-conformal coverage at alpha = 0.10 (target 0.90) survives the deployment split; report worst-group coverage, not only marginal.
3. If it does not, rank abstention by the model-native uncertainty score (classification: 1 − max p; regression: quantile-interval width). Scope: retained-set selective risk, **not** restoring a coverage guarantee.

The K=10 remedy audit is **quarantined** from the K=20 TableShift confirmatory arm (no data overlap). That is this paper’s use of “quarantine,” not a data-quality dump.

## Stages

<ol class="stage-list">
  <li>Data with an entity or time key</li>
  <li>Random split | grouped / rolling-origin split</li>
  <li>Frozen predictor (GBM or tabular foundation model)</li>
  <li>Remedy ladder (weighted conformal, Mondrian variants, tuned selector)</li>
  <li>Worst-group evaluation → Restore | Fail</li>
</ol>

<p class="legend">
  <span><i class="swatch random"></i>random split</span>
  <span><i class="swatch grouped"></i>grouped / time split</span>
  <span><i class="swatch restore"></i>Restore (coverage at or above 0.90)</span>
  <span><i class="swatch fail"></i>Fail (coverage below 0.90)</span>
</p>

{{fig0}}
