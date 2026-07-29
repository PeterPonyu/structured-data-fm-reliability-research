#!/usr/bin/env bash
# fetch_data.sh -- pre-warm every on-demand data/checkpoint download this repo
# needs, BEFORE running the decisive-experiment arms, so a mid-run network
# hiccup doesn't waste GPU time. No bulk data is stored in-repo (see
# DATA_MANIFEST.md); everything here is fetched into each package's own cache
# dir (outside this repo) by the SAME packages the experiment scripts import.
#
# Sources (see DATA_MANIFEST.md for the authoritative table):
#   - OpenML (no auth):        14 keyed dataset ids, via the `openml` package,
#                               cached under ~/.cache/openml (openml.config).
#   - Folktables / ACS PUMS 2018: via the `folktables` package, cached under
#                               $DATA_ROOT (default /tmp/folktables_data).
#   - TabICLv2 checkpoint:     via the `tabicl` package -> Hugging Face Hub,
#                               cached under ~/.cache/huggingface/hub.
#   - TabPFN weights / M4:     NOT fetched here -- license/token-gated (see
#                               nd1_tabpfn25_arm.py). Skip unless TABPFN_TOKEN
#                               is set.
#
# Usage:
#   ./fetch_data.sh                 # uses $PYTHON, else python3
#   PYTHON=/path/to/python ./fetch_data.sh
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-python3}"

echo "fetch_data: using $PY"

echo "[1/3] pre-warming OpenML cache for the 14 keyed datasets ..."
"$PY" - <<'PYEOF'
import warnings
warnings.filterwarnings("ignore")
import openml

DIDS = [151, 188, 1590, 6332, 40701, 41021, 41162, 41540,
        42563, 42727, 42728, 42729, 42731, 42732]
for did in DIDS:
    try:
        ds = openml.datasets.get_dataset(did, download_data=True,
                                         download_qualities=False,
                                         download_features_meta_data=True)
        print(f"  ok   did={did:>6}  {ds.name}")
    except Exception as e:
        print(f"  FAIL did={did:>6}  {type(e).__name__}: {e}")
PYEOF

echo "[2/3] pre-warming Folktables ACS PUMS 2018 cache (used by p4_tableshift.py) ..."
"$PY" - <<'PYEOF'
import os
os.environ.setdefault("DATA_ROOT", "/tmp/folktables_data")
try:
    from folktables import ACSDataSource
    src = ACSDataSource(survey_year="2018", horizon="1-Year", survey="person",
                        root_dir=os.environ["DATA_ROOT"])
    src.get_data(states=["CA"], download=True)  # smallest representative pull
    print("  ok   folktables ACS 2018 (CA) cached under", os.environ["DATA_ROOT"])
except Exception as e:
    print(f"  FAIL folktables: {type(e).__name__}: {e}")
PYEOF

echo "[3/3] pre-warming TabICLv2 checkpoint from Hugging Face Hub (used by the FM arm) ..."
"$PY" - <<'PYEOF'
try:
    from tabicl import TabICLClassifier
    # Instantiating + a tiny .fit() forces the checkpoint download without
    # requiring a GPU (device="cpu"); it is a no-op if already cached.
    import numpy as np
    clf = TabICLClassifier(n_estimators=1, allow_auto_download=True,
                           device="cpu", verbose=False)
    X = np.random.RandomState(0).normal(size=(20, 3))
    y = (X[:, 0] > 0).astype(int)
    clf.fit(X, y)
    print("  ok   TabICLv2 checkpoint cached under ~/.cache/huggingface/hub")
except Exception as e:
    print(f"  FAIL tabicl: {type(e).__name__}: {e}")
PYEOF

echo
echo "fetch_data: done. TabPFN-2.5 weights were NOT fetched (license-gated; set"
echo "TABPFN_TOKEN and see experiments/nd1_tabpfn25_arm.py if you have a token)."
