from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "LOCAL_THERMAL_SCENARIO_MODEL_NOT_FLIGHT_TPS_AUTHORITY"
APPROVED_CAPABILITIES = [
    "deterministic-local-multi-tile-thermal-scenario-modeling",
    "bounded-local-thermal-gradient-and-spectral-analysis",
    "source-verified-odin-data-oriented-reference",
]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    readme = text("README.md")
    python_source = text("src/alpha/predictive_thermal.py")
    odin_source = text("src/thermal_mesh.odin")
    bridge = text("tests/test_odin_bridge.py")
    capabilities = json.loads(text("machine/capabilities.json"))
    excellence = json.loads(text("machine/excellence-state.json"))
    contract = json.loads(text("machine/target-contract.json"))

    assert TOKEN in readme
    assert TOKEN in python_source
    assert TOKEN in odin_source
    assert "Not affiliated with, endorsed by, or connected to SpaceX" in readme
    assert "does not claim Odin compilation or execution" in readme
    assert "do NOT claim to compile or execute Odin" in bridge

    for forbidden in (
        "ABORT_TRAJECTORY",
        "REDUCE_HEAT_FLUX_30_DEG",
        "ADJUST_AOA_REDUCE_Q",
    ):
        assert forbidden not in readme
        assert forbidden not in python_source
        assert forbidden not in odin_source

    assert capabilities["evidence_state"] == TOKEN
    assert capabilities["capabilities"] == APPROVED_CAPABILITIES
    assert excellence["state"] == "TESTED"
    assert excellence["principal_state"] == "TESTED"
    assert excellence["evidence_state"] == TOKEN
    assert excellence["gates"]["ODIN_NATIVE_EXECUTION"] == "NOT_PROVEN"
    assert excellence["gates"]["FLIGHT_TPS_AUTHORITY"] == "NOT_CLAIMED"
    assert contract["current"]["state"] == "TESTED"
    assert contract["evidence_state"] == TOKEN
    assert contract["next_gate"] == (
        "native Odin compilation and execution bound to exact source SHA"
    )

    print(
        json.dumps(
            {
                "status": "PASS",
                "evidence_state": TOKEN,
                "capabilities": APPROVED_CAPABILITIES,
                "odin_runtime_proven": False,
                "flight_control_authority": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
