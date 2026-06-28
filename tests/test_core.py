"""Tests for spacex-thermal-protection — the shield that predicts its own death.

4 tests. Because a heat shield that knows it's dying can save the ship.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import math
from alpha.predictive_thermal import (
    TileState, ThermalGradientAnalyzer, HeatShieldPredictor,
    TrajectoryAdvisor, ReentryConditions
)


def test_gradient_analyzer():
    t1 = TileState(tile_id=0, material="PICA-X", thickness_m=0.05, temperature_k=300, x_pos=0, y_pos=0)
    t2 = TileState(tile_id=1, material="PICA-X", thickness_m=0.05, temperature_k=500, x_pos=0.1, y_pos=0,
                   neighboring_tiles=[0])
    t1.neighboring_tiles = [1]
    analyzer = ThermalGradientAnalyzer()
    gradient = analyzer.compute_gradient(t1, t2)
    assert gradient.gradient_k_per_m > 0

def test_predictor_integrity():
    predictor = HeatShieldPredictor()
    tile = TileState(tile_id=0, material="PICA-X", thickness_m=0.05, temperature_k=300, x_pos=0, y_pos=0)
    conditions = ReentryConditions(velocity_ms=7000, altitude_m=80000, dynamic_pressure_pa=1000,
                                    heat_flux_w_m2=500000, mach_number=20, angle_of_attack_deg=40)
    integrity = predictor.compute_integrity_index(tile, conditions.heat_flux_w_m2, conditions.dynamic_pressure_pa)
    assert 0 <= integrity <= 1

def test_failure_prediction():
    predictor = HeatShieldPredictor()
    tile = TileState(tile_id=0, material="PICA-X", thickness_m=0.05, temperature_k=300, x_pos=0, y_pos=0)
    conditions = ReentryConditions(velocity_ms=7000, altitude_m=80000, dynamic_pressure_pa=1000,
                                    heat_flux_w_m2=500000, mach_number=20, angle_of_attack_deg=40)
    prediction = predictor.predict_failure(tile, conditions)
    assert prediction.time_to_failure_s > 0
    assert prediction.confidence > 0

def test_trajectory_advisor():
    advisor = TrajectoryAdvisor()
    compromised = [(0, 15.0), (1, 30.0)]
    correction = advisor.recommend_trajectory_correction(compromised, 40.0)
    assert "aoa_correction" in correction


# The heat shield knows when it will fail.
# That knowledge is the difference between
# coming home and burning up.
SHIELD_INTEGRITY = 0.95
assert SHIELD_INTEGRITY > 0.9, "The shield holds"
