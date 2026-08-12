"""Deterministic executable surface for the local thermal scenario laboratory."""
from __future__ import annotations

import argparse
import hashlib
import json
from typing import Any

from alpha.predictive_thermal import (
    EVIDENCE_STATE,
    AdaptiveReentryController,
    ReentryConditions,
    ThermalGradientAnalyzer,
    TileState,
)


def _digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _tile(tile_id: int, temperature_k: float, x_pos: float, neighbors: list[int]) -> TileState:
    return TileState(
        tile_id=tile_id,
        material="PICA-X",
        thickness_m=0.05,
        temperature_k=temperature_k,
        x_pos=x_pos,
        y_pos=0.0,
        neighboring_tiles=neighbors,
    )


def build_demo_receipt() -> dict[str, Any]:
    """Exercise gradient, spectral, multi-tile scenario, and non-control semantics."""
    analyzer = ThermalGradientAnalyzer()
    last_gradient = None
    for index in range(12):
        left = _tile(0, 300.0, 0.0, [1])
        right = _tile(1, 330.0 + index * 2.0, 1.0, [0])
        last_gradient = analyzer.compute_gradient(left, right)
    spectrum = analyzer.fourier_anomaly_detect(0, window_size=12)

    controller = AdaptiveReentryController()
    tiles = [
        _tile(0, 300.0, 0.0, [1]),
        _tile(1, 330.0, 1.0, [0]),
    ]
    conditions = ReentryConditions(
        velocity_ms=7000.0,
        altitude_m=80000.0,
        dynamic_pressure_pa=1000.0,
        heat_flux_w_m2=500000.0,
        mach_number=20.0,
        angle_of_attack_deg=40.0,
    )
    scenario = controller.reentry_step(tiles, conditions, current_aoa=40.0, dt=0.1)

    predictions = scenario["predictions"]
    receipt: dict[str, Any] = {
        "schema": "glaciereq.thermal-scenario-lab.demo.v1",
        "evidence_state": EVIDENCE_STATE,
        "gradient": {
            "tile_a": last_gradient.tile_a if last_gradient else None,
            "tile_b": last_gradient.tile_b if last_gradient else None,
            "gradient_k_per_m": None if last_gradient is None else round(last_gradient.gradient_k_per_m, 6),
            "anomaly_score": None if last_gradient is None else round(last_gradient.anomaly_score, 6),
        },
        "spectral": {
            "dominant_bin": spectrum["dominant_bin"],
            "spectral_energy": round(spectrum["spectral_energy"], 6),
            "high_frequency_ratio": round(spectrum["high_frequency_ratio"], 6),
            "evidence_state": spectrum["evidence_state"],
        },
        "scenario": {
            "tiles_updated": scenario["tiles_updated"],
            "prediction_count": len(predictions),
            "min_integrity_index": round(scenario["min_integrity_index"], 6),
            "max_integrity_index": round(scenario["max_integrity_index"], 6),
            "review_labels": [item["review_label"] for item in predictions],
            "modeled_threshold_horizons_s": [item["modeled_threshold_horizon_s"] for item in predictions],
            "comparison_action": scenario["scenario"]["action"],
            "control_authority": scenario["control_authority"],
        },
        "external_inputs_consumed": 0,
        "external_actions_executed": 0,
    }
    receipt["digest"] = _digest(receipt)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute the independent local thermal scenario laboratory")
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    args = parser.parse_args(argv)
    receipt = build_demo_receipt()
    print(json.dumps(receipt, sort_keys=True, indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
