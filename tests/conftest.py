"""pytest configuration: put experiments/ on sys.path so test modules can
`import nd1_split_conditioned_audit` etc., exactly like tests/smoke_test.py
does for the (non-pytest) offline smoke check. Also points RELIABILITY_COMMONS
at the sibling reliability-commons checkout when not already set, matching
every experiment script's own fallback (see e.g.
experiments/nd1_split_conditioned_audit.py). Note: each experiment script
now prefers the vendored copy at ../vendor/reliability_metrics over this
fallback, so RELIABILITY_COMMONS/the sibling checkout is only consulted if
the vendored copy is somehow absent."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
EXPERIMENTS = os.path.join(REPO, "experiments")
if EXPERIMENTS not in sys.path:
    sys.path.insert(0, EXPERIMENTS)

os.environ.setdefault(
    "RELIABILITY_COMMONS",
    os.path.join(os.path.dirname(REPO), "reliability-commons"))
