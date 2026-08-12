#!/usr/bin/env python3
"""Execute the canonical local thermal-scenario product surface directly."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alpha.predictive_thermal import EVIDENCE_STATE  # noqa: E402
from thermal_scenario_cli import build_demo_receipt  # noqa: E402


def main() -> int:
    receipt = build_demo_receipt()
    print(json.dumps(receipt, indent=2, sort_keys=True))
    valid = (
        receipt["evidence_state"] == EVIDENCE_STATE
        and receipt["gradient"]["tile_a"] == 0
        and receipt["gradient"]["tile_b"] == 1
        and receipt["scenario"]["tiles_updated"] == 2
        and receipt["scenario"]["prediction_count"] == 2
        and receipt["scenario"]["control_authority"] is False
        and receipt["external_inputs_consumed"] == 0
        and receipt["external_actions_executed"] == 0
        and len(receipt["digest"]) == 64
    )
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
