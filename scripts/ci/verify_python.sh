#!/usr/bin/env bash
set -euo pipefail

python -m pip install --disable-pip-version-check --quiet pytest 'setuptools>=75' wheel
python -m compileall -q src tests scripts mastermind_sidecar.py
python -m pytest -q
rm -rf dist build *.egg-info src/*.egg-info
python -m pip wheel . --no-deps --no-build-isolation -w dist
python -m pip install --disable-pip-version-check --quiet --force-reinstall dist/*.whl
thermal-scenario-demo --compact > /tmp/thermal-scenario-demo.json
python - <<'PY'
import json
from pathlib import Path
receipt = json.loads(Path('/tmp/thermal-scenario-demo.json').read_text())
assert receipt['evidence_state'] == 'LOCAL_THERMAL_SCENARIO_MODEL_NOT_FLIGHT_TPS_AUTHORITY'
assert receipt['scenario']['tiles_updated'] == 2
assert receipt['scenario']['prediction_count'] == 2
assert receipt['scenario']['control_authority'] is False
assert receipt['external_inputs_consumed'] == 0
assert receipt['external_actions_executed'] == 0
assert len(receipt['digest']) == 64
PY
python scripts/operate.py
python scripts/verify_public_surface.py
python - <<'PY'
import json
from pathlib import Path
caps = json.loads(Path('machine/crystallization/capability-manifest.json').read_text())
gaps = json.loads(Path('machine/crystallization/gap-matrix.json').read_text())
assert caps['capabilities']
assert all(item['state'] == 'WORKING' for item in caps['capabilities'])
assert gaps['gaps'] == []
PY
