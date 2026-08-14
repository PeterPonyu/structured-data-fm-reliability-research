# Tables

Tables are the native object of this audit. Coverage below 0.90 is vermillion; coverage at or above 0.90 is green. Interval columns are mute. Dataset names are human-readable (never OpenML ids).

<p class="legend">
  <span><i class="swatch restore"></i>coverage ≥ 0.90</span>
  <span><i class="swatch fail"></i>coverage &lt; 0.90</span>
</p>

## CORE14 — XGBoost and LightGBM (key included)

AURC, grouped split-conformal coverage, and grouped repair ratio on the 14 keyed OpenML datasets. Headline numbers, key included.

{{core14_table}}

<p class="note">Download: <a href="{{root}}data/p4_table.csv">p4_table.csv</a></p>

## TabICLv2 — coverage and grouped repair

Leakage-ablated TabICLv2 arm (key retained). Same 14 datasets.

{{fm_table}}

## Learned selector vs free uncertainty vs oracle

Grouped split, XGBoost, 14 keyed datasets.

{{learned_table}}

## TableShift roster (held-out confirmatory)

Nine open tasks. Three are excluded-by-rule from the H1/H2 tally; six are evaluable.

{{p5_roster_table}}

## H1 / H2 confirmatory verdicts

Six evaluable held-out tasks, K=20 split-repeats.

{{p5_verdict_table}}

## ACS exploratory repair and RAC1P coverage gap

Folktables ACS 2018, leave-states-out spatial OOD. Four tasks × two GBMs.

{{acs_table}}

## Headline counts, key-in vs key-out

{{key_count_table}}
