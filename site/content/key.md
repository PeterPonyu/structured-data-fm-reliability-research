# Key included vs key excluded

This comparison is first-class, not a buried limitation.

- **Default (KBS headline) = key included.** The leave-group-out / rolling-origin key stays in the feature matrix.
- **Conservative bound = key excluded.** The split key is dropped from features.

Leave-group-out test keys are unseen categories. Retaining the encoded key can inflate collapse (an ID-generalization artifact), so key-out is the conservative degradation bound.

Grouped-gap count shifts 8/14 → 6/14 (XGBoost) and 7/14 → 5/14 (LightGBM). Repair stays 13/14 in both conditions. TabDPT has no key-excluded coverage points in the key-out coverage panel; that absence is disclosed, not imputed.

Visual evidence in the print figures: F2 C/D, F3 C, F6 C/D, and F4 B. Both conditions remain in the page source if scripting is disabled.

{{key_toggle}}

{{key_count_table}}

{{key_coverage_tables}}
