from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "LOCAL_THERMAL_SCENARIO_MODEL_NOT_FLIGHT_TPS_AUTHORITY"
APPROVED_CAPABILITIES = [
    "deterministic-local-multi-tile-thermal-scenario-modeling",
    "bounded-local-thermal-gradient-and-spectral-analysis",
    "source-verified-odin-data-oriented-reference",
    "installable-local-python-product",
    "direct-deterministic-operability",
    "pinned-native-odin-compile-run-gate",
]
PINNED_ODIN_SHA = "d858c0a182bb28d7b04b04dbb8aed592a9c96c84e4400ee917c74b45848a4d87"


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    readme = text("README.md")
    python_source = text("src/alpha/predictive_thermal.py")
    odin_source = text("src/thermal_mesh.odin")
    native_gate = text("scripts/ci/verify_odin.sh")
    capabilities = json.loads(text("machine/capabilities.json"))
    excellence = json.loads(text("machine/excellence-state.json"))
    contract = json.loads(text("machine/target-contract.json"))
    gaps = json.loads(text("machine/crystallization/gap-matrix.json"))

    assert TOKEN in readme and TOKEN in python_source and TOKEN in odin_source
    assert "Not affiliated with, endorsed by, or connected to SpaceX" in readme
    assert "exact-head workflow receipt" in readme
    assert PINNED_ODIN_SHA in native_gate
    assert "dev-2026-08" in native_gate
    assert "native-odin-thermal.json" in native_gate

    for forbidden in ("ABORT_TRAJECTORY", "REDUCE_HEAT_FLUX_30_DEG", "ADJUST_AOA_REDUCE_Q"):
        assert forbidden not in readme
        assert forbidden not in python_source
        assert forbidden not in odin_source

    assert capabilities["evidence_state"] == TOKEN
    assert capabilities["capabilities"] == APPROVED_CAPABILITIES
    assert excellence["state"] == "TESTED"
    assert excellence["principal_state"] == "TESTED"
    assert excellence["evidence_state"] == TOKEN
    for gate in (
        "PYTHON_DETERMINISTIC_PROOF",
        "ADVERSARIAL_BOUNDARY",
        "PUBLIC_TRUTH_BOUNDARY",
        "ODIN_SOURCE_CONTRACT",
        "ODIN_NATIVE_EXECUTION",
    ):
        assert excellence["gates"][gate] == "REQUIRES_CURRENT_HEAD_RECEIPT"
    assert excellence["gates"]["FLIGHT_TPS_AUTHORITY"] == "NOT_CLAIMED"
    assert excellence["proof_receipt"]["state"] == "EXTERNAL_EXACT_HEAD_RECEIPT_REQUIRED"
    assert "never self-asserts" in excellence["proof_receipt"]["binding_rule"]
    assert contract["current"]["state"] == "FUNCTIONAL_CRYSTALLIZATION_CANDIDATE"
    assert contract["evidence_state"] == TOKEN
    assert contract["next_gate"] == "exact-head native Odin execution receipt plus terminal crystallization receipt"
    assert gaps["gaps"] == []

    print(json.dumps({
        "status": "PASS",
        "evidence_state": TOKEN,
        "capabilities": APPROVED_CAPABILITIES,
        "native_odin_gate_present": True,
        "native_odin_execution_self_proven": False,
        "flight_control_authority": False,
        "admission_requires_external_exact_head_receipts": True,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
