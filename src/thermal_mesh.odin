// thermal_mesh.odin — local data-oriented thermal scenario reference
//
// This source preserves the repository's Odin memory-layout and mesh-oriented
// thermal arithmetic as an illustrative reference implementation. It is not a
// proprietary SpaceX/Starship model, flight-safety system, calibrated TPS
// predictor, or trajectory-control implementation.
package main

import "core:fmt"
import "core:math"

EVIDENCE_STATE       :: "LOCAL_THERMAL_SCENARIO_MODEL_NOT_FLIGHT_TPS_AUTHORITY"
STEFAN_BOLTZMANN     :: 5.670374419e-8
REFERENCE_DENSITY    :: 1700.0
MAX_TILES            :: 18_000
MAX_SCENARIO_HORIZON :: 84.0

Material_Type :: enum {
	PICA_X,
	TUFROC,
	HRSI,
	LSI,
	AETB,
}

material_conductivity :: proc(m: Material_Type) -> f64 {
	switch m {
	case .PICA_X: return 0.5
	case .TUFROC: return 1.2
	case .HRSI:   return 0.8
	case .LSI:    return 0.6
	case .AETB:   return 0.3
	}
	return 0.5
}

material_ablation_rate :: proc(m: Material_Type) -> f64 {
	switch m {
	case .PICA_X: return 0.0001
	case .TUFROC: return 0.00005
	case .HRSI:   return 0.00008
	case .LSI:    return 0.00006
	case .AETB:   return 0.00003
	}
	return 0.0001
}

Tile_Thermal_State :: struct {
	tile_id:          u32,
	surface_temp:     f64,
	heat_flux:        f64,
	wear_ratio:       f64,
	thickness_m:      f64,
	material:         Material_Type,
	integrity_index:  f64,
	ablation_depth_m: f64,
	threshold_reached: bool,
}

Scenario_Conditions :: struct {
	velocity_ms:         f64,
	altitude_m:          f64,
	dynamic_pressure_pa: f64,
	heat_flux_w_m2:      f64,
	mach_number:         f64,
	angle_of_attack_deg: f64,
}

Scenario_Result :: struct {
	tile_id:                     u32,
	modeled_threshold_horizon_s: f64,
	scenario_mode:               string,
	severity_score:              f64,
	review_label:                string,
	evidence_state:              string,
}

Thermal_Mesh :: struct {
	tiles:           [MAX_TILES]Tile_Thermal_State,
	tile_count:      u32,
	total_integrity: f64,
}

compute_density :: proc(altitude_m: f64) -> f64 {
	if altitude_m < 0 {
		return 0
	}
	return 1.225 * math.exp(-altitude_m / 8500.0)
}

// Illustrative local heat-load index. It is not a validated Fay-Riddell solver.
compute_heat_load_index :: proc(velocity_ms: f64, rho: f64) -> f64 {
	if velocity_ms < 0 || rho < 0 {
		return 0
	}
	v_kms := velocity_ms / 1000.0
	return 1.83e-4 * math.sqrt(rho) * v_kms * v_kms * v_kms
}

compute_full_thermal_step :: proc(
	state: ^Tile_Thermal_State,
	conditions: ^Scenario_Conditions,
	dt: f64,
) {
	if state.thickness_m <= 0 || dt < 0 || conditions.heat_flux_w_m2 < 0 {
		return
	}
	k := material_conductivity(state.material)
	ablation_rate := material_ablation_rate(state.material)
	conduction_loss := min(
		conditions.heat_flux_w_m2,
		k * conditions.heat_flux_w_m2 / (1.0 + state.thickness_m * 1000.0),
	)
	radiation_loss := STEFAN_BOLTZMANN * math.pow(state.surface_temp, 4) * 0.85
	net_heat := conditions.heat_flux_w_m2 - conduction_loss - radiation_loss
	thermal_mass := max(state.thickness_m * REFERENCE_DENSITY * 1000.0, 1e-9)
	state.surface_temp = max(0.0, state.surface_temp + net_heat * dt / thermal_mass)
	state.ablation_depth_m += ablation_rate * conditions.heat_flux_w_m2 * dt / 1e6
	remaining := state.thickness_m - state.ablation_depth_m
	state.threshold_reached = remaining <= 0.001
	state.wear_ratio = min(1.0, max(0.0, 1.0 - remaining / state.thickness_m))
}

compute_integrity_index :: proc(
	state: ^Tile_Thermal_State,
	heat_flux: f64,
	dynamic_pressure: f64,
) -> f64 {
	if state.thickness_m <= 0 || heat_flux < 0 || dynamic_pressure < 0 {
		return 0
	}
	thickness_ratio := max(
		0.0,
		(state.thickness_m - state.ablation_depth_m) / state.thickness_m,
	)
	load_index := heat_flux / 1e6 + dynamic_pressure / 1e4
	state.integrity_index = min(1.0, max(0.0, thickness_ratio / (1.0 + load_index)))
	return state.integrity_index
}

// Historical name retained in the repository's Python API only. This Odin
// reference returns a modeled threshold horizon and scenario score, not failure
// probability, remaining useful life, or flight guidance.
evaluate_scenario :: proc(
	state: ^Tile_Thermal_State,
	conditions: ^Scenario_Conditions,
	time_horizon_s: f64,
) -> Scenario_Result {
	horizon := min(max(time_horizon_s, 0.001), MAX_SCENARIO_HORIZON)
	remaining := state.thickness_m - state.ablation_depth_m
	if remaining <= 0.001 {
		return Scenario_Result{
			tile_id = state.tile_id,
			modeled_threshold_horizon_s = 0,
			scenario_mode = "SCENARIO_ABLATION_THRESHOLD_REACHED",
			severity_score = 1.0,
			review_label = "REVIEW_CRITICAL_SCENARIO",
			evidence_state = EVIDENCE_STATE,
		}
	}

	rate := material_ablation_rate(state.material) * conditions.heat_flux_w_m2 / 1e6
	time_to_ablation := 1e9
	if rate > 0 {
		time_to_ablation = remaining / rate
	}
	integrity := compute_integrity_index(
		state,
		conditions.heat_flux_w_m2,
		conditions.dynamic_pressure_pa,
	)
	stress_rate := conditions.heat_flux_w_m2 / 1e6 * 0.05 +
		conditions.dynamic_pressure_pa / 1e4 * 0.02
	time_to_stress := 1e9
	if stress_rate > 0 && integrity > 0 {
		time_to_stress = integrity / stress_rate
	}
	modeled := min(time_to_ablation, time_to_stress)
	bounded := min(modeled, horizon)
	severity := min(1.0, max(0.0, 1.0 - bounded / horizon))
	mode := if time_to_ablation <= time_to_stress {
		"SCENARIO_ABLATION_THRESHOLD"
	} else {
		"SCENARIO_STRESS_THRESHOLD"
	}
	label := "OBSERVE_SCENARIO"
	if bounded < 5 {
		label = "REVIEW_CRITICAL_SCENARIO"
	} else if bounded < 15 {
		label = "REVIEW_HIGH_LOAD_SCENARIO"
	} else if bounded < 30 {
		label = "REVIEW_ELEVATED_SCENARIO"
	}
	return Scenario_Result{
		tile_id = state.tile_id,
		modeled_threshold_horizon_s = bounded,
		scenario_mode = mode,
		severity_score = severity,
		review_label = label,
		evidence_state = EVIDENCE_STATE,
	}
}

init_mesh :: proc(mesh: ^Thermal_Mesh, material: Material_Type, thickness_m: f64) {
	if thickness_m <= 0 {
		mesh.tile_count = 0
		mesh.total_integrity = 0
		return
	}
	for i in 0..<MAX_TILES {
		mesh.tiles[i] = Tile_Thermal_State{
			tile_id = u32(i),
			surface_temp = 300.0,
			heat_flux = 0.0,
			wear_ratio = 0.0,
			thickness_m = thickness_m,
			material = material,
			integrity_index = 1.0,
			ablation_depth_m = 0.0,
			threshold_reached = false,
		}
	}
	mesh.tile_count = MAX_TILES
	mesh.total_integrity = 1.0
}

update_mesh :: proc(
	mesh: ^Thermal_Mesh,
	conditions: ^Scenario_Conditions,
	dt: f64,
) {
	if mesh.tile_count == 0 {
		mesh.total_integrity = 0
		return
	}
	rho := compute_density(conditions.altitude_m)
	load_index := compute_heat_load_index(conditions.velocity_ms, rho)
	total := 0.0
	for i in 0..<mesh.tile_count {
		tile := &mesh.tiles[i]
		tile.heat_flux = load_index
		compute_full_thermal_step(tile, conditions, dt)
		total += compute_integrity_index(
			tile,
			conditions.heat_flux_w_m2,
			conditions.dynamic_pressure_pa,
		)
	}
	mesh.total_integrity = total / f64(mesh.tile_count)
}

compute_heat_flux_sensitivity :: proc(
	tile_x: f64,
	tile_y: f64,
	current_aoa: f64,
) -> f64 {
	theta := math.atan2(tile_y, tile_x)
	return math.cos(theta) * math.cos(theta) * 0.5 *
		math.sin(2 * math.to_radians(current_aoa))
}

main :: proc() {
	mesh := Thermal_Mesh{}
	init_mesh(&mesh, .PICA_X, 0.05)
	conditions := Scenario_Conditions{
		velocity_ms = 7000,
		altitude_m = 80000,
		dynamic_pressure_pa = 1000,
		heat_flux_w_m2 = 500000,
		mach_number = 20,
		angle_of_attack_deg = 40,
	}
	update_mesh(&mesh, &conditions, 0.1)
	result := evaluate_scenario(&mesh.tiles[0], &conditions, MAX_SCENARIO_HORIZON)
	fmt.printf("Evidence: %s\n", result.evidence_state)
	fmt.printf("Scenario: %s horizon %.2fs severity %.3f\n",
		result.scenario_mode,
		result.modeled_threshold_horizon_s,
		result.severity_score,
	)
	fmt.printf("Review label: %s (no control authority)\n", result.review_label)
}
