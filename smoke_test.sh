#!/usr/bin/env bash
# Fast (<2 min) offline smoke test: core modules import, the Stage-1 pipeline
# runs on a synthetic fixture, and tracked result JSONs have expected keys.
# Does NOT touch the network and does NOT rewrite any result JSON.
#
# Usage:
#   ./smoke_test.sh                 # uses $PYTHON, else the conda "dl" env,
#                                   # else python3
#   PYTHON=/path/to/python ./smoke_test.sh
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -n "${PYTHON:-}" ]]; then
  PY="$PYTHON"
elif [[ -x "$HOME/miniconda3/envs/dl/bin/python" ]]; then
  PY="$HOME/miniconda3/envs/dl/bin/python"
else
  PY="python3"
fi

echo "smoke_test: using $PY"
exec "$PY" "$REPO/tests/smoke_test.py"
