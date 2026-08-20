# Protocol

A practitioner procedure with two load-bearing steps: a keyed-split coverage
test, then uncertainty abstention if coverage fails.

1. Compare **random** vs **leave-group-out / rolling-origin** on a dataset that
   actually has an entity or time key.
2. Test whether split-conformal coverage survives the deployment split. Report
   worst-group coverage, not only marginal.
3. If it does not, rank abstention by the model-native uncertainty score
   (classification: 1 − max *p*; regression: quantile-interval width). Scope:
   retained-set selective risk, **not** restoring a coverage guarantee.

**Key included** keeps the split key in the feature matrix. **Key excluded**
drops the key and is the conservative bound: leave-group-out test keys are
unseen categories, so retaining an encoded key can inflate collapse.

The exploratory remedy ladder is kept separate from the held-out
spatial-OOD arm (no shared rows). That split of roles is what “quarantine”
means here, not a data-quality dump.

This path does not host figures or result numbers.
