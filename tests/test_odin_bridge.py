"""Source-contract tests for the Odin reference implementation.

These tests intentionally do NOT claim to compile or execute Odin. They verify
that the checked-in Odin source preserves the bounded local scenario contract
and does not expose flight-control or calibrated-prediction language. Runtime
proof in this repository is Python; Odin compilation remains a separate future
gate unless an Odin toolchain is explicitly installed and exercised.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ODIN = ROOT / "src" / "thermal_mesh.odin"


def source() -> str:
    return ODIN.read_text(encoding="utf-8")


def test_odin_reference_exists_and_declares_local_evidence_boundary() -> None:
    text = source()
    assert 'EVIDENCE_STATE       :: "LOCAL_THERMAL_SCENARIO_MODEL_NOT_FLIGHT_TPS_AUTHORITY"' in text
    assert "local data-oriented thermal scenario reference" in text
    assert "not a" in text.lower()
    assert "flight-safety system" in text


def test_odin_reference_preserves_core_data_oriented_mechanisms() -> None:
    text = source()
    for token in (
        "Tile_Thermal_State :: struct",
        "Thermal_Mesh :: struct",
        "compute_full_thermal_step :: proc",
        "compute_integrity_index :: proc",
        "evaluate_scenario :: proc",
        "init_mesh :: proc",
        "update_mesh :: proc",
        "compute_heat_flux_sensitivity :: proc",
    ):
        assert token in text


def test_odin_reference_uses_scenario_not_flight_command_semantics() -> None:
    text = source()
    forbidden = (
        "ABORT_TRAJECTORY",
        "REDUCE_HEAT_FLUX_30_DEG",
        "ADJUST_AOA_REDUCE_Q",
        "recommended_action",
        "confidence:",
        "Failure Prediction",
        "Starship TPS",
    )
    for token in forbidden:
        assert token not in text
    assert "control authority" in text.lower()
    assert "severity_score" in text
    assert "review_label" in text


def test_bridge_explicitly_does_not_claim_odin_execution() -> None:
    own_text = Path(__file__).read_text(encoding="utf-8")
    assert "do NOT claim to compile or execute Odin" in own_text
    assert "Odin compilation remains a separate future gate" in own_text
