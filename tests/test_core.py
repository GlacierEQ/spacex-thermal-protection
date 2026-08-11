from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alpha.predictive_thermal import (  # noqa: E402
    AdaptiveReentryController,
    EVIDENCE_STATE,
    HeatShieldPredictor,
    ReentryConditions,
    ThermalGradientAnalyzer,
    TileState,
    TrajectoryAdvisor,
)


def tile(tile_id: int = 0, *, temperature_k: float = 300.0) -> TileState:
    return TileState(
        tile_id=tile_id,
        material="PICA-X",
        thickness_m=0.05,
        temperature_k=temperature_k,
        x_pos=float(tile_id),
        y_pos=0.0,
    )


def conditions() -> ReentryConditions:
    return ReentryConditions(
        velocity_ms=7000,
        altitude_m=80000,
        dynamic_pressure_pa=1000,
        heat_flux_w_m2=500000,
        mach_number=20,
        angle_of_attack_deg=40,
    )


def test_gradient_analyzer_is_bounded_and_deterministic() -> None:
    left = tile(0, temperature_k=300)
    right = tile(1, temperature_k=500)
    left.neighboring_tiles = [1]
    right.neighboring_tiles = [0]
    gradient = ThermalGradientAnalyzer().compute_gradient(left, right)
    assert gradient.gradient_k_per_m == pytest.approx(200.0)
    assert gradient.evidence_state == EVIDENCE_STATE


def test_gradient_rejects_coincident_tiles() -> None:
    left = tile(0)
    right = tile(1)
    right.x_pos = left.x_pos
    right.y_pos = left.y_pos
    with pytest.raises(ValueError, match="distinct"):
        ThermalGradientAnalyzer().compute_gradient(left, right)


def test_predictor_rejects_nonfinite_and_negative_inputs() -> None:
    predictor = HeatShieldPredictor()
    sample = tile()
    with pytest.raises(ValueError, match="finite"):
        predictor.update_tile_state(sample, math.nan, 0.1)
    with pytest.raises(ValueError, match="non-negative"):
        predictor.compute_integrity_index(sample, -1.0, 0.0)
    invalid = conditions()
    invalid.dynamic_pressure_pa = -1
    with pytest.raises(ValueError, match="non-negative"):
        predictor.predict_failure(sample, invalid)


def test_local_threshold_result_is_not_flight_authority() -> None:
    result = HeatShieldPredictor().predict_failure(tile(), conditions())
    assert 0 <= result.confidence <= 1
    assert result.time_to_failure_s >= 0
    assert result.evidence_state == EVIDENCE_STATE
    assert result.failure_mode.startswith("SCENARIO_")
    assert result.recommended_action in {
        "REVIEW_CRITICAL_SCENARIO",
        "REVIEW_HIGH_LOAD_SCENARIO",
        "REVIEW_ELEVATED_SCENARIO",
        "OBSERVE_SCENARIO",
    }
    assert "ABORT" not in result.recommended_action
    assert "ADJUST_AOA" not in result.recommended_action


def test_integrity_index_is_bounded() -> None:
    predictor = HeatShieldPredictor()
    value = predictor.compute_integrity_index(tile(), 500000, 1000)
    assert 0 <= value <= 1


def test_scenario_advisor_explicitly_has_no_control_authority() -> None:
    advisor = TrajectoryAdvisor()
    result = advisor.recommend_trajectory_correction([(0, 15.0)], 40.0)
    assert result["action"] == "COMPARE_ALTERNATIVE_SCENARIO"
    assert result["control_authority"] is False
    assert result["evidence_state"] == EVIDENCE_STATE
    assert math.isfinite(result["aoa_correction"])


def test_multi_tile_runner_is_local_evidence_only() -> None:
    first = tile(0, temperature_k=300)
    second = tile(1, temperature_k=350)
    first.neighboring_tiles = [1]
    second.neighboring_tiles = [0]
    report = AdaptiveReentryController().reentry_step(
        [first, second], conditions(), current_aoa=40.0, dt=0.1
    )
    assert report["tiles_updated"] == 2
    assert report["control_authority"] is False
    assert report["evidence_state"] == EVIDENCE_STATE
    assert all(
        item["evidence_state"] == EVIDENCE_STATE for item in report["predictions"]
    )


def test_duplicate_tile_ids_fail_closed() -> None:
    with pytest.raises(ValueError, match="unique"):
        AdaptiveReentryController().reentry_step(
            [tile(0), tile(0)], conditions(), current_aoa=40.0
        )
