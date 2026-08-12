"""Source and pinned-native-gate contract tests for the Odin reference."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ODIN = ROOT / "src" / "thermal_mesh.odin"
GATE = ROOT / "scripts" / "ci" / "verify_odin.sh"


def source() -> str:
    return ODIN.read_text(encoding="utf-8")


def test_odin_reference_exists_and_declares_local_evidence_boundary() -> None:
    text = source()
    assert 'EVIDENCE_STATE       :: "LOCAL_THERMAL_SCENARIO_MODEL_NOT_FLIGHT_TPS_AUTHORITY"' in text
    assert "local data-oriented thermal scenario reference" in text
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
        "main :: proc()",
    ):
        assert token in text


def test_odin_reference_uses_scenario_not_flight_command_semantics() -> None:
    text = source()
    for token in (
        "ABORT_TRAJECTORY",
        "REDUCE_HEAT_FLUX_30_DEG",
        "ADJUST_AOA_REDUCE_Q",
        "recommended_action",
        "confidence:",
        "Failure Prediction",
        "Starship TPS",
    ):
        assert token not in text
    assert "control authority" in text.lower()
    assert "severity_score" in text
    assert "review_label" in text


def test_native_gate_is_exact_release_and_digest_pinned() -> None:
    gate = GATE.read_text(encoding="utf-8")
    assert "dev-2026-08" in gate
    assert "odin-linux-amd64-dev-2026-08.tar.gz" in gate
    assert "d858c0a182bb28d7b04b04dbb8aed592a9c96c84e4400ee917c74b45848a4d87" in gate
    assert "$ODIN_BIN check src/thermal_mesh.odin -file" in gate
    assert "$ODIN_BIN build src/thermal_mesh.odin -file" in gate
    assert "native-odin-thermal.json" in gate
