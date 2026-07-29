#!/usr/bin/env bash
# run_all_arms.sh -- run the decisive-experiment arms from NEXT-EXPERIMENTS.md
# in order: pytest + offline smoke checks first, then CPU arms, then the GPU
# arm last. Every step is idempotent (each writes its own timestamped-provenance
# JSON to experiments/results/, and reruns simply overwrite that SAME new file,
# never an original tracked result JSON).
#
# See RUNME_CONTAINER.md for the full annotated runbook (what each arm does,
# expected wall-clock, prerequisites). This script is the condensed, copy-
# pasteable command sequence for a fresh AutoDL container.
#
# Usage:
#   ./run_all_arms.sh              # everything, in order
#   ./run_all_arms.sh --cpu-only   # skip the GPU arm (item 3)
#   PYTHON=/path/to/python ./run_all_arms.sh
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO"

if [[ -n "${PYTHON:-}" ]]; then
  PY="$PYTHON"
elif [[ -x "$HOME/miniconda3/envs/dl/bin/python" ]]; then
  PY="$HOME/miniconda3/envs/dl/bin/python"
elif command -v python >/dev/null 2>&1; then
  PY="python"
else
  PY="python3"
fi
export PYTHON="$PY"
echo "run_all_arms: using $PY"

CPU_ONLY=0
for arg in "$@"; do
  [[ "$arg" == "--cpu-only" ]] && CPU_ONLY=1
done

section () { echo; echo "=================================================="; echo "$1"; echo "=================================================="; }

# ---------------------------------------------------------------------------
section "[0/6] pre-flight: pytest (offline, seconds) + offline smoke test"
# ---------------------------------------------------------------------------
"$PY" -m pytest tests/ -q
./smoke_test.sh

# ---------------------------------------------------------------------------
section "[1/6] item 1 -- K-repeated folds: ALREADY DONE, not rerun here"
# ---------------------------------------------------------------------------
echo "Stage-1 K=30 / Stage-2 K=20 repeated-split realizations (both feature"
echo "conditions) are already on disk and git-committed:"
echo "  experiments/results/split_repeats/  (100 per-k JSONs)"
echo "  experiments/results/split_repeats/aggregate-split-repeats-2026-07-02.json"
echo "  experiments/results/findings-split-repeats-2026-07-02.md"
echo "NEXT-EXPERIMENTS.md is stale on this item; nothing to run. To EXTEND the"
echo "sweep with more repeats, see nd1_split_conditioned_audit.py / "
echo "nd1_s2_lightgbm_mondrian.py's REPEAT_K env var and rerun"
echo "nd1_split_repeats_aggregate.py afterward."

# ---------------------------------------------------------------------------
section "[2/6] item 2 -- calibration-size diagnostic rerun (CPU, ~1-2 min)"
# ---------------------------------------------------------------------------
"$PY" experiments/nd1_s2_p4_calsize_diag_reconciled.py
EXCLUDE_KEY=1 "$PY" experiments/nd1_s2_p4_calsize_diag_reconciled.py

# ---------------------------------------------------------------------------
section "[3/6] item 4 -- tuned-GBM baseline rerun (CPU, ~15-25 min)"
# ---------------------------------------------------------------------------
"$PY" experiments/nd1_tuned_gbm_baseline.py
EXCLUDE_KEY=1 "$PY" experiments/nd1_tuned_gbm_baseline.py

if [[ "$CPU_ONLY" == "1" ]]; then
  echo
  echo "run_all_arms: --cpu-only given, skipping item 3 (GPU FM arm) and item 5 (stub)."
  exit 0
fi

# content_gate <result-json-path> <arm-label> -- strict CONTENT gate (exit
# codes are never trusted, 2026-07-09 DOFA lesson): asserts the arm's own
# result JSON reports full_coverage=true (every attempted dataset produced an
# "ok" record) before letting the sequence continue.
content_gate () {
  local path="$1" label="$2"
  "$PY" - "$path" "$label" <<'PYEOF'
import json, sys
path, label = sys.argv[1], sys.argv[2]
d = json.load(open(path))
if not d.get("full_coverage"):
    print(f"CONTENT GATE FAILED [{label}]: {d.get('n_ok')}/{d.get('n_attempted')} "
          f"datasets covered in {path}; skipped: {d.get('skipped_names')}",
          file=sys.stderr)
    sys.exit(1)
print(f"content gate OK [{label}]: {d.get('n_ok')}/{d.get('n_attempted')} datasets covered")
PYEOF
}

# ---------------------------------------------------------------------------
section "[4/6] item 3 -- FM-arm leakage ablation + larger ensembles (GPU, ~1-4 GPU-h)"
# ---------------------------------------------------------------------------
echo "Pre-warming data/checkpoint caches (idempotent; no-op if already cached) ..."
PYTHON="$PY" ./fetch_data.sh

echo "Prefetching + content-verifying TabICL classifier+regressor checkpoints"
echo "(closes the 2026-07-09 regressor-checkpoint container-network gap that"
echo "left the FM arm at 7/14 datasets; see POST-ANALYSIS.md Arm 3) ..."
"$PY" experiments/prefetch_checkpoints.py

echo "Running key-included (realistic protocol), n_estimators=${TABICL_N_EST:-16} ..."
"$PY" experiments/nd1_tabicl_fm_arm_leakage_ablation.py
content_gate experiments/results/nd1_tabicl_fm_arm_leakage_ablation.json "TabICL key-included"

echo "Running key-excluded (leakage ablation) ..."
EXCLUDE_KEY=1 "$PY" experiments/nd1_tabicl_fm_arm_leakage_ablation.py
content_gate experiments/results/nd1_tabicl_fm_arm_leakage_ablation_keyexcluded.json "TabICL key-excluded"

# ---------------------------------------------------------------------------
section "[5/6] FM roster expansion -- TabDPT (second FM), TabPFN-2.5 (third, token-gated)"
# ---------------------------------------------------------------------------
echo "Running TabDPT key-included (realistic protocol) ..."
"$PY" experiments/nd1_tabdpt_fm_arm.py
content_gate experiments/results/nd1_tabdpt_fm_arm.json "TabDPT key-included"

echo "Running TabDPT key-excluded (leakage ablation) ..."
EXCLUDE_KEY=1 "$PY" experiments/nd1_tabdpt_fm_arm.py
content_gate experiments/results/nd1_tabdpt_fm_arm_keyexcluded.json "TabDPT key-excluded"

if [[ -n "${TABPFN_TOKEN:-}" ]]; then
  echo "TABPFN_TOKEN is set; running the (now-implemented) TabPFN-2.5 arm ..."
  "$PY" experiments/nd1_tabpfn25_arm.py
  content_gate experiments/results/nd1_tabpfn25_arm.json "TabPFN-2.5 key-included"
  EXCLUDE_KEY=1 "$PY" experiments/nd1_tabpfn25_arm.py
  content_gate experiments/results/nd1_tabpfn25_arm_keyexcluded.json "TabPFN-2.5 key-excluded"
else
  echo "TABPFN_TOKEN not set -- SKIPPED per NEXT-EXPERIMENTS.md item 5 policy."
  echo "(experiments/nd1_tabpfn25_arm.py's audit body is implemented but"
  echo "remains guarded on TABPFN_TOKEN; do not run without a token.)"
fi

# ---------------------------------------------------------------------------
section "[6/6] in-context scaling arm -- TabICL ensemble size x context length (GPU)"
# ---------------------------------------------------------------------------
"$PY" experiments/nd1_fm_scaling_arm.py

section "run_all_arms: all arms complete. New result JSONs are under experiments/results/."
