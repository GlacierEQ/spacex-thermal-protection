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


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_public_front_door_preserves_non_affiliation_and_receipt_boundary() -> None:
    readme = read("README.md")
    assert "Not affiliated with, endorsed by, or connected to SpaceX" in readme
    assert TOKEN in readme
    assert "exact-head workflow receipt" in readme
    assert "trajectory guidance" in readme


def test_source_surfaces_remove_flight_command_tokens() -> None:
    combined = "\n".join([read("src/alpha/predictive_thermal.py"), read("src/thermal_mesh.odin")])
    for forbidden in ("ABORT_TRAJECTORY", "REDUCE_HEAT_FLUX_30_DEG", "ADJUST_AOA_REDUCE_Q"):
        assert forbidden not in combined
    assert combined.count(TOKEN) >= 2


def test_machine_capability_surface_is_exact_whitelist() -> None:
    payload = json.loads(read("machine/capabilities.json"))
    assert payload["evidence_state"] == TOKEN
    assert payload["capabilities"] == APPROVED_CAPABILITIES


def test_machine_state_requires_external_receipt_for_native_odin() -> None:
    state = json.loads(read("machine/excellence-state.json"))
    assert state["state"] == "TESTED"
    assert state["principal_state"] == "TESTED"
    for gate in (
        "PYTHON_DETERMINISTIC_PROOF",
        "ADVERSARIAL_BOUNDARY",
        "PUBLIC_TRUTH_BOUNDARY",
        "ODIN_SOURCE_CONTRACT",
        "ODIN_NATIVE_EXECUTION",
    ):
        assert state["gates"][gate] == "REQUIRES_CURRENT_HEAD_RECEIPT"
    assert state["gates"]["FLIGHT_TPS_AUTHORITY"] == "NOT_CLAIMED"
    receipt = state["proof_receipt"]
    assert receipt["state"] == "EXTERNAL_EXACT_HEAD_RECEIPT_REQUIRED"
    assert set(receipt["required"]) == {"CI", "Public Thermal Scenario Truth Gate"}
    assert "never self-asserts" in receipt["binding_rule"]


def test_native_odin_gate_is_present_without_source_self_certification() -> None:
    gate = read("scripts/ci/verify_odin.sh")
    assert "native-odin-thermal.json" in gate
    assert "d858c0a182bb28d7b04b04dbb8aed592a9c96c84e4400ee917c74b45848a4d87" in gate
    contract = json.loads(read("machine/target-contract.json"))
    assert contract["next_gate"] == "exact-head native Odin execution receipt plus terminal crystallization receipt"
