"""Deterministic local thermal-scenario model.

This module preserves the repository's reusable thermal-gradient, ablation,
integrity, spectral, and multi-tile scenario mechanisms while explicitly
bounding their authority. It does not model proprietary SpaceX systems, ingest
flight telemetry, predict real heat-shield failure, estimate calibrated
probabilities or remaining useful life, or issue trajectory / hardware commands.

All thresholds, material constants, stress rates, horizons, and response labels
are illustrative scenario assumptions unless independently validated elsewhere.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

EVIDENCE_STATE = "LOCAL_THERMAL_SCENARIO_MODEL_NOT_FLIGHT_TPS_AUTHORITY"
MAX_SCENARIO_HORIZON_S = 84.0
MAX_TILE_COUNT = 18_000
ANOMALY_THRESHOLD = 2.5
STEFAN_BOLTZMANN = 5.670374419e-8

# Illustrative coefficients used only by the local scenario model.
THERMAL_CONDUCTIVITY_TILES = {
    "PICA-X": 0.5,
    "TUFROC": 1.2,
    "HRSI": 0.8,
    "LRSI": 0.6,
    "AETB": 0.3,
}
ABLATION_RATES = {
    "PICA-X": 0.0001,
    "TUFROC": 0.00005,
    "HRSI": 0.00008,
    "LRSI": 0.00006,
    "AETB": 0.00003,
}


def _finite(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def _nonnegative(value: float, name: str) -> float:
    value = _finite(value, name)
    if value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


def _unit_interval(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class TileState:
    tile_id: int
    material: str
    thickness_m: float
    temperature_k: float
    x_pos: float
    y_pos: float
    neighboring_tiles: list[int] = field(default_factory=list)
    delamination_risk: float = 0.0
    ablation_depth_m: float = 0.0
    is_compromised: bool = False

    def validate(self) -> None:
        if isinstance(self.tile_id, bool) or not isinstance(self.tile_id, int):
            raise ValueError("tile_id must be a non-boolean integer")
        if self.tile_id < 0:
            raise ValueError("tile_id must be non-negative")
        if self.material not in THERMAL_CONDUCTIVITY_TILES:
            raise ValueError(f"unsupported illustrative material: {self.material}")
        self.thickness_m = _nonnegative(self.thickness_m, "thickness_m")
        if self.thickness_m <= 0:
            raise ValueError("thickness_m must be positive")
        self.temperature_k = _nonnegative(self.temperature_k, "temperature_k")
        self.x_pos = _finite(self.x_pos, "x_pos")
        self.y_pos = _finite(self.y_pos, "y_pos")
        self.ablation_depth_m = _nonnegative(self.ablation_depth_m, "ablation_depth_m")
        self.delamination_risk = _unit_interval(_finite(self.delamination_risk, "delamination_risk"))
        for neighbor in self.neighboring_tiles:
            if isinstance(neighbor, bool) or not isinstance(neighbor, int) or neighbor < 0:
                raise ValueError("neighboring tile ids must be non-negative integers")


@dataclass
class ThermalGradient:
    tile_a: int
    tile_b: int
    delta_t: float
    distance_m: float
    gradient_k_per_m: float
    anomaly_score: float = 0.0
    evidence_state: str = EVIDENCE_STATE


@dataclass
class ReentryConditions:
    velocity_ms: float
    altitude_m: float
    dynamic_pressure_pa: float
    heat_flux_w_m2: float
    mach_number: float
    angle_of_attack_deg: float

    def validate(self) -> None:
        self.velocity_ms = _nonnegative(self.velocity_ms, "velocity_ms")
        self.altitude_m = _nonnegative(self.altitude_m, "altitude_m")
        self.dynamic_pressure_pa = _nonnegative(
            self.dynamic_pressure_pa, "dynamic_pressure_pa"
        )
        self.heat_flux_w_m2 = _nonnegative(self.heat_flux_w_m2, "heat_flux_w_m2")
        self.mach_number = _nonnegative(self.mach_number, "mach_number")
        self.angle_of_attack_deg = _finite(
            self.angle_of_attack_deg, "angle_of_attack_deg"
        )


@dataclass
class PredictionResult:
    """Backward-compatible local scenario result.

    `time_to_failure_s` is a modeled threshold horizon, not validated remaining
    useful life. `confidence` is a bounded scenario severity score, not a
    calibrated probability or statistical confidence. `recommended_action` is a
    local review label and never a vehicle or trajectory command.
    """

    tile_id: int
    time_to_failure_s: float
    failure_mode: str
    confidence: float
    recommended_action: str
    evidence_state: str = EVIDENCE_STATE


class ThermalGradientAnalyzer:
    """Bounded local tile-gradient and spectral scenario analyzer."""

    def __init__(self, anomaly_threshold: float = ANOMALY_THRESHOLD):
        self.anomaly_threshold = _nonnegative(anomaly_threshold, "anomaly_threshold")
        self._gradient_history: dict[tuple[int, int], list[float]] = {}
        self._baseline_gradients: dict[tuple[int, int], float] = {}

    def compute_gradient(self, tile_a: TileState, tile_b: TileState) -> ThermalGradient:
        tile_a.validate()
        tile_b.validate()
        dx = tile_b.x_pos - tile_a.x_pos
        dy = tile_b.y_pos - tile_a.y_pos
        distance = math.hypot(dx, dy)
        if distance <= 1e-10:
            raise ValueError("tile positions must be distinct for gradient evaluation")

        delta_t = tile_b.temperature_k - tile_a.temperature_k
        gradient = delta_t / distance
        key = (tile_a.tile_id, tile_b.tile_id)
        history = self._gradient_history.setdefault(key, [])
        history.append(gradient)
        del history[:-100]
        anomaly = self._compute_anomaly_score(key, gradient)
        return ThermalGradient(
            tile_a=tile_a.tile_id,
            tile_b=tile_b.tile_id,
            delta_t=delta_t,
            distance_m=distance,
            gradient_k_per_m=gradient,
            anomaly_score=anomaly,
        )

    def _compute_anomaly_score(self, key: tuple[int, int], current: float) -> float:
        history = self._gradient_history.get(key, [])
        if len(history) < 10:
            return 0.0
        if key not in self._baseline_gradients:
            self._baseline_gradients[key] = sum(history[:10]) / 10
        baseline = self._baseline_gradients[key]
        recent = history[-10:]
        mean = sum(recent) / len(recent)
        variance = sum((value - mean) ** 2 for value in recent) / len(recent)
        std = math.sqrt(variance)
        if std <= 1e-12:
            return 0.0 if abs(current - baseline) <= 1e-12 else float("inf")
        return abs(current - baseline) / std

    def detect_delamination_precursors(self, tiles: list[TileState]) -> list[ThermalGradient]:
        """Return scenario anomalies; this does not diagnose delamination."""
        if len(tiles) > MAX_TILE_COUNT:
            raise ValueError(f"tile count exceeds bounded local limit {MAX_TILE_COUNT}")
        tile_map = {tile.tile_id: tile for tile in tiles}
        if len(tile_map) != len(tiles):
            raise ValueError("tile ids must be unique")
        anomalies: list[ThermalGradient] = []
        seen: set[tuple[int, int]] = set()
        for tile in tiles:
            tile.validate()
            for neighbor_id in tile.neighboring_tiles:
                if neighbor_id not in tile_map:
                    continue
                pair = tuple(sorted((tile.tile_id, neighbor_id)))
                if pair in seen:
                    continue
                seen.add(pair)
                gradient = self.compute_gradient(tile, tile_map[neighbor_id])
                if gradient.anomaly_score > self.anomaly_threshold:
                    anomalies.append(gradient)
        return anomalies

    def fourier_anomaly_detect(self, tile_id: int, window_size: int = 64) -> dict:
        if isinstance(tile_id, bool) or not isinstance(tile_id, int) or tile_id < 0:
            raise ValueError("tile_id must be a non-negative integer")
        if isinstance(window_size, bool) or not isinstance(window_size, int) or window_size < 8:
            raise ValueError("window_size must be an integer >= 8")
        keys = sorted(key for key in self._gradient_history if tile_id in key)
        if not keys:
            return {
                "anomaly": False,
                "dominant_bin": 0,
                "spectral_energy": 0.0,
                "high_frequency_ratio": 0.0,
                "evidence_state": EVIDENCE_STATE,
            }
        data = self._gradient_history[keys[0]][-min(window_size, 128) :]
        if len(data) < 8:
            return {
                "anomaly": False,
                "dominant_bin": 0,
                "spectral_energy": 0.0,
                "high_frequency_ratio": 0.0,
                "evidence_state": EVIDENCE_STATE,
            }
        n = len(data)
        mean = sum(data) / n
        centered = [value - mean for value in data]
        magnitudes: list[float] = []
        for frequency_bin in range(n // 2):
            real = sum(
                centered[index]
                * math.cos(2 * math.pi * frequency_bin * index / n)
                for index in range(n)
            )
            imag = sum(
                centered[index]
                * math.sin(2 * math.pi * frequency_bin * index / n)
                for index in range(n)
            )
            magnitudes.append(math.hypot(real, imag) / n)
        total_energy = sum(value * value for value in magnitudes)
        split = len(magnitudes) // 2
        high_energy = sum(value * value for value in magnitudes[split:])
        ratio = high_energy / total_energy if total_energy > 0 else 0.0
        dominant = magnitudes.index(max(magnitudes)) if magnitudes else 0
        return {
            "anomaly": ratio > 0.3,
            "dominant_bin": dominant,
            "spectral_energy": total_energy,
            "high_frequency_ratio": ratio,
            "evidence_state": EVIDENCE_STATE,
        }


class HeatShieldPredictor:
    """Local deterministic thermal threshold-horizon evaluator.

    Historical class name is retained for compatibility. Results are scenario
    estimates from illustrative coefficients, not verified heat-shield failure
    predictions or flight-safety authority.
    """

    def __init__(self):
        self.gradient_analyzer = ThermalGradientAnalyzer()
        self._integrity_indices: dict[int, float] = {}

    def update_tile_state(self, tile: TileState, heat_flux: float, dt: float) -> TileState:
        tile.validate()
        heat_flux = _nonnegative(heat_flux, "heat_flux")
        dt = _nonnegative(dt, "dt")
        conductivity = THERMAL_CONDUCTIVITY_TILES[tile.material]
        ablation_rate = ABLATION_RATES[tile.material]

        # Deliberately simple lumped scenario arithmetic. `conductivity` scales a
        # bounded loss term; it is not a validated TPS conduction solver.
        conduction_loss = min(heat_flux, conductivity * heat_flux / (1.0 + tile.thickness_m * 1000))
        radiation_loss = STEFAN_BOLTZMANN * tile.temperature_k**4 * 0.85
        net_heat = heat_flux - conduction_loss - radiation_loss
        thermal_mass = max(tile.thickness_m * 1_700_000.0, 1e-9)
        tile.temperature_k = max(0.0, tile.temperature_k + net_heat * dt / thermal_mass)
        tile.ablation_depth_m += ablation_rate * heat_flux * dt / 1e6
        tile.is_compromised = tile.thickness_m - tile.ablation_depth_m <= 0.001
        return tile

    def compute_integrity_index(
        self, tile: TileState, heat_flux: float, dynamic_pressure: float
    ) -> float:
        tile.validate()
        heat_flux = _nonnegative(heat_flux, "heat_flux")
        dynamic_pressure = _nonnegative(dynamic_pressure, "dynamic_pressure")
        thickness_ratio = max(
            0.0,
            (tile.thickness_m - tile.ablation_depth_m) / tile.thickness_m,
        )
        load_index = heat_flux / 1e6 + dynamic_pressure / 1e4
        integrity = _unit_interval(thickness_ratio / (1.0 + load_index))
        self._integrity_indices[tile.tile_id] = integrity
        return integrity

    def predict_failure(
        self,
        tile: TileState,
        conditions: ReentryConditions,
        time_horizon_s: float = MAX_SCENARIO_HORIZON_S,
    ) -> PredictionResult:
        tile.validate()
        conditions.validate()
        time_horizon_s = _nonnegative(time_horizon_s, "time_horizon_s")
        if time_horizon_s <= 0:
            raise ValueError("time_horizon_s must be positive")

        remaining = tile.thickness_m - tile.ablation_depth_m
        if remaining <= 0.001:
            return PredictionResult(
                tile_id=tile.tile_id,
                time_to_failure_s=0.0,
                failure_mode="SCENARIO_ABLATION_THRESHOLD_REACHED",
                confidence=1.0,
                recommended_action="REVIEW_CRITICAL_SCENARIO",
            )

        rate = ABLATION_RATES[tile.material]
        ablation_per_s = rate * conditions.heat_flux_w_m2 / 1e6
        time_to_ablation = remaining / ablation_per_s if ablation_per_s > 0 else math.inf
        integrity = self.compute_integrity_index(
            tile, conditions.heat_flux_w_m2, conditions.dynamic_pressure_pa
        )
        stress_rate = conditions.heat_flux_w_m2 / 1e6 * 0.05 + conditions.dynamic_pressure_pa / 1e4 * 0.02
        time_to_stress = integrity / stress_rate if stress_rate > 0 and integrity > 0 else math.inf
        modeled_horizon = min(time_to_ablation, time_to_stress)
        mode = (
            "SCENARIO_ABLATION_THRESHOLD"
            if time_to_ablation <= time_to_stress
            else "SCENARIO_STRESS_THRESHOLD"
        )

        recent_gradients = [
            history[-1]
            for key, history in self.gradient_analyzer._gradient_history.items()
            if tile.tile_id in key and history
        ]
        if recent_gradients and abs(sum(recent_gradients) / len(recent_gradients)) > 5000:
            modeled_horizon *= 0.5
            mode = "SCENARIO_GRADIENT_" + mode

        bounded_horizon = min(modeled_horizon, time_horizon_s)
        severity_score = _unit_interval(1.0 - bounded_horizon / time_horizon_s)
        if bounded_horizon < 5:
            label = "REVIEW_CRITICAL_SCENARIO"
        elif bounded_horizon < 15:
            label = "REVIEW_HIGH_LOAD_SCENARIO"
        elif bounded_horizon < 30:
            label = "REVIEW_ELEVATED_SCENARIO"
        else:
            label = "OBSERVE_SCENARIO"
        return PredictionResult(
            tile_id=tile.tile_id,
            time_to_failure_s=bounded_horizon,
            failure_mode=mode,
            confidence=severity_score,
            recommended_action=label,
        )


class TrajectoryAdvisor:
    """Local angle-of-attack sensitivity scenario calculator.

    Historical class name is retained. Returned deltas are hypothetical inputs
    for scenario comparison only; they are not guidance or control commands.
    """

    def __init__(self):
        self._sensitivity_cache: dict[str, float] = {}

    def compute_heat_flux_sensitivity(
        self, tile_x: float, tile_y: float, current_aoa: float
    ) -> float:
        tile_x = _finite(tile_x, "tile_x")
        tile_y = _finite(tile_y, "tile_y")
        current_aoa = _finite(current_aoa, "current_aoa")
        key = f"{tile_x:.4f}_{tile_y:.4f}_{current_aoa:.4f}"
        if key not in self._sensitivity_cache:
            theta = math.atan2(tile_y, tile_x)
            self._sensitivity_cache[key] = (
                math.cos(theta) ** 2
                * 0.5
                * math.sin(2 * math.radians(current_aoa))
            )
        return self._sensitivity_cache[key]

    def recommend_trajectory_correction(
        self,
        compromised_tiles: list[tuple[int, float]],
        current_aoa: float,
        max_aoa_change: float = 5.0,
    ) -> dict:
        current_aoa = _finite(current_aoa, "current_aoa")
        max_aoa_change = _nonnegative(max_aoa_change, "max_aoa_change")
        if not compromised_tiles:
            return {
                "aoa_correction": 0.0,
                "modeled_aoa": current_aoa,
                "scenario_heat_delta_pct": 0.0,
                "action": "NO_SCENARIO_CHANGE",
                "control_authority": False,
                "evidence_state": EVIDENCE_STATE,
            }
        cleaned: list[tuple[int, float]] = []
        for tile_id, horizon in compromised_tiles:
            if isinstance(tile_id, bool) or not isinstance(tile_id, int) or tile_id < 0:
                raise ValueError("compromised tile ids must be non-negative integers")
            cleaned.append((tile_id, _nonnegative(horizon, "modeled_horizon")))
        tile_id, horizon = min(cleaned, key=lambda item: item[1])
        ratio = _unit_interval(1.0 - min(horizon, MAX_SCENARIO_HORIZON_S) / MAX_SCENARIO_HORIZON_S)
        modeled_delta = max_aoa_change * ratio
        return {
            "aoa_correction": -modeled_delta,
            "modeled_aoa": current_aoa - modeled_delta,
            "scenario_heat_delta_pct": modeled_delta * 2.5,
            "action": "COMPARE_ALTERNATIVE_SCENARIO",
            "critical_tile": tile_id,
            "modeled_threshold_horizon_s": horizon,
            "control_authority": False,
            "evidence_state": EVIDENCE_STATE,
        }


class AdaptiveReentryController:
    """In-memory multi-tile scenario runner; not a flight controller."""

    def __init__(self):
        self.predictor = HeatShieldPredictor()
        self.advisor = TrajectoryAdvisor()
        self._correction_history: list[dict] = []

    def reentry_step(
        self,
        tiles: list[TileState],
        conditions: ReentryConditions,
        current_aoa: float,
        dt: float = 0.1,
    ) -> dict:
        if len(tiles) > MAX_TILE_COUNT:
            raise ValueError(f"tile count exceeds bounded local limit {MAX_TILE_COUNT}")
        conditions.validate()
        current_aoa = _finite(current_aoa, "current_aoa")
        dt = _nonnegative(dt, "dt")
        ids = [tile.tile_id for tile in tiles]
        if len(ids) != len(set(ids)):
            raise ValueError("tile ids must be unique")

        updated_tiles = [
            self.predictor.update_tile_state(tile, conditions.heat_flux_w_m2, dt)
            for tile in tiles
        ]
        self.predictor.gradient_analyzer.detect_delamination_precursors(updated_tiles)
        predictions = [
            self.predictor.predict_failure(tile, conditions) for tile in updated_tiles
        ]
        elevated = [
            (result.tile_id, result.time_to_failure_s)
            for result in predictions
            if result.time_to_failure_s < 30.0
        ]
        scenario = self.advisor.recommend_trajectory_correction(
            elevated, current_aoa
        )
        self._correction_history.append(
            {
                "prediction_count": len(predictions),
                "elevated_count": len(elevated),
                "scenario": scenario,
            }
        )
        del self._correction_history[:-100]
        integrity = [
            self.predictor._integrity_indices.get(tile.tile_id, 1.0)
            for tile in updated_tiles
        ]
        return {
            "tiles_updated": len(updated_tiles),
            "predictions": [
                {
                    "tile_id": result.tile_id,
                    "modeled_threshold_horizon_s": round(result.time_to_failure_s, 3),
                    "scenario_mode": result.failure_mode,
                    "severity_score": round(result.confidence, 6),
                    "review_label": result.recommended_action,
                    "evidence_state": result.evidence_state,
                }
                for result in predictions
            ],
            "scenario": scenario,
            "max_integrity_index": max(integrity, default=1.0),
            "min_integrity_index": min(integrity, default=1.0),
            "control_authority": False,
            "evidence_state": EVIDENCE_STATE,
        }
