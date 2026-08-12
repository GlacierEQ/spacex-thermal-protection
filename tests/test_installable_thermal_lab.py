from __future__ import annotations

import json
import subprocess
import sys

from alpha.predictive_thermal import EVIDENCE_STATE
from thermal_scenario_cli import build_demo_receipt


def test_demo_receipt_exercises_real_thermal_mechanisms() -> None:
    receipt = build_demo_receipt()
    assert receipt["evidence_state"] == EVIDENCE_STATE
    assert receipt["gradient"]["tile_a"] == 0
    assert receipt["gradient"]["tile_b"] == 1
    assert receipt["spectral"]["evidence_state"] == EVIDENCE_STATE
    assert receipt["scenario"]["tiles_updated"] == 2
    assert receipt["scenario"]["prediction_count"] == 2
    assert receipt["scenario"]["control_authority"] is False
    assert receipt["external_inputs_consumed"] == 0
    assert receipt["external_actions_executed"] == 0
    assert len(receipt["digest"]) == 64


def test_operate_script_is_direct_and_machine_readable() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/operate.py"],
        check=True,
        capture_output=True,
        text=True,
    )
    receipt = json.loads(result.stdout)
    assert receipt["evidence_state"] == EVIDENCE_STATE
    assert receipt["scenario"]["comparison_action"] in {
        "COMPARE_ALTERNATIVE_SCENARIO",
        "NO_SCENARIO_CHANGE",
    }
