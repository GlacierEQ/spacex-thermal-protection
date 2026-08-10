// thermal_mesh.odin — Odin data-oriented reentry thermal physics solver
// for Starship TPS tiles. Zero hidden control flow, explicit memory layout.
//
// Implements:
//   - Material property tables (PICA-X, TUFROC, HRSI, LSI, AETB)
//   - Shock-layer heat flux (Fay-Riddell simplified)
//   - 1D heat conduction + radiation + ablation
//   - Structural integrity index
//   - Failure prediction (ablation breach / structural failure)
//   - Mesh-wide simulation over 18 000 tiles
//   - Trajectory sensitivity (heat-flux dQ/dα)
package thermal_mesh

import "core:fmt"
import "core:math"

// ── Physical Constants ──────────────────────────────────────────
EARTH_RADIUS_KM     :: 6378.137     // WGS-84 (km)
STEFAN_BOLTZMANN    :: 5.670374419e-8  // W·m⁻²·K⁻⁴
PICA_X_DENSITY      :: 1700.0       // kg/m³
ABLAION_THRESHOLD_K :: 1923.15      // 1650 °C — PICA-X charring onset
MAX_TILES           :: 18_000       // Starship tile count
CONFIDENCE_FLOOR    :: 0.31415      // π-ish floor

// ── Material Types ──────────────────────────────────────────────
Material_Type :: enum {
	PICA_X,
	TUFROC,
	HRSI,
	LSI,
	AETB,
}

// material_conductivity returns thermal conductivity (W/m·K)
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

// material_ablation_rate returns ablation rate (m/MW·s)
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

// ── Core Data Structures ────────────────────────────────────────
Tile_Thermal_State :: struct {
	tile_id:           u32,
	surface_temp:      f64,  // Kelvin
	heat_flux:         f64,  // MW/m²
	pica_x_wear:       f64,  // Wear ratio 0.0 – 1.0
	thickness_m:       f64,  // Tile thickness (m)
	material:          Material_Type,
	integrity:         f64,  // 0.0 (gone) → 1.0 (pristine)
	ablation_depth_m:  f64,  // Cumulative ablation (m)
	is_compromised:    bool,
}

Reentry_Conditions :: struct {
	velocity_ms:           f64,  // m/s
	altitude_m:            f64,  // m
	dynamic_pressure_pa:   f64,  // Pa
	heat_flux_w_m2:        f64,  // W/m²
	mach_number:           f64,
	angle_of_attack_deg:   f64,
}

Prediction_Result :: struct {
	tile_id:              u32,
	time_to_failure_s:    f64,
	failure_mode:         string,
	confidence:           f64,
	recommended_action:   string,
}

Thermal_Mesh :: struct {
	tiles:           [MAX_TILES]Tile_Thermal_State,
	tile_count:      u32,
	total_integrity: f64,
}

// ── Atmospheric Density Model (Exponential) ─────────────────────
compute_density :: proc(altitude_m: f64) -> f64 {
	H    := 8500.0       // Scale height (m)
	rho0 := 1.225       // Sea-level density (kg/m³)
	return rho0 * math.exp(-altitude_m / H)
}

// ── Shock-Layer Heat Flux (Fay-Riddell Simplified) ──────────────
// q ~ ρ^0.5 · v³  →  returns MW/m²
compute_heat_flux :: proc(velocity_ms: f64, rho: f64) -> f64 {
	v_kms := velocity_ms / 1000.0
	q_w_m2 := 1.83e-4 * math.sqrt(rho) * v_kms * v_kms * v_kms
	return q_w_m2 / 1e6
}

// ── Basic Reentry Step (Original — preserved for API compat) ────
compute_reentry_step :: proc(state: ^Tile_Thermal_State, dt: f64) {
	heat_absorbed := state.heat_flux * dt * 0.042
	state.surface_temp += heat_absorbed
	if state.surface_temp > ABLAION_THRESHOLD_K {
		state.pica_x_wear += dt * 0.001
	}
}

// ── Full Thermal Step (Conduction + Radiation + Ablation) ──────
compute_full_thermal_step :: proc(state: ^Tile_Thermal_State, conditions: ^Reentry_Conditions, dt: f64) {
	k            := material_conductivity(state.material)
	ablation_rate := material_ablation_rate(state.material)

	// Net heat: incoming flux − conduction loss − radiation loss
	q_conduction  := k * conditions.heat_flux_w_m2 / max(state.thickness_m, 0.001)
	q_radiation   := STEFAN_BOLTZMANN * math.pow(state.surface_temp, 4) * 0.85
	net_heat      := conditions.heat_flux_w_m2 - q_conduction - q_radiation

	// Temperature change
	dT := net_heat * dt / (state.thickness_m * PICA_X_DENSITY)
	state.surface_temp = max(state.surface_temp + dT, 0.0)

	// Ablation
	state.ablation_depth_m += ablation_rate * conditions.heat_flux_w_m2 * dt / 1e6
	remaining := state.thickness_m - state.ablation_depth_m
	if remaining <= 0.001 {
		state.is_compromised = true
		state.integrity = 0.0
	} else {
		state.pica_x_wear = 1.0 - remaining / state.thickness_m
	}
}

// ── Structural Integrity Index (0.0 → 1.0) ──────────────────────
compute_integrity_index :: proc(state: ^Tile_Thermal_State, heat_flux: f64, dynamic_pressure: f64) -> f64 {
	thickness_ratio := max(0.0, (state.thickness_m - state.ablation_depth_m) / max(state.thickness_m, 1e-9))
	thermal_stress   := heat_flux / 1e6
	vibration_stress := dynamic_pressure / 1e4
	stress_factor    := 1.0 / (1.0 + thermal_stress + vibration_stress)
	integrity        := thickness_ratio * stress_factor
	state.integrity  = integrity
	return integrity
}

// ── Failure Prediction ──────────────────────────────────────────
predict_failure :: proc(state: ^Tile_Thermal_State, conditions: ^Reentry_Conditions, time_horizon_s: f64) -> Prediction_Result {
	ablation_rate        := material_ablation_rate(state.material)
	remaining_thickness  := state.thickness_m - state.ablation_depth_m

	if remaining_thickness <= 0.001 {
		return Prediction_Result{
			tile_id              = state.tile_id,
			time_to_failure_s    = 0.0,
			failure_mode         = "ABLATION_BREACH",
			confidence           = 1.0,
			recommended_action   = "ABORT_TRAJECTORY",
		}
	}

	var time_to_ablation: f64
	if conditions.heat_flux_w_m2 > 0 {
		time_to_ablation = remaining_thickness / (ablation_rate * conditions.heat_flux_w_m2 / 1e6)
	} else {
		time_to_ablation = 1e9
	}

	integrity        := compute_integrity_index(state, conditions.heat_flux_w_m2, conditions.dynamic_pressure_pa)
	thermal_load     := conditions.heat_flux_w_m2 / 1e6
	vibration_load   := conditions.dynamic_pressure_pa / 1e4
	stress_rate      := thermal_load * 0.05 + vibration_load * 0.02

	var time_to_stress_failure: f64
	if stress_rate > 0 && integrity > 0 {
		time_to_stress_failure = integrity / stress_rate
	} else {
		time_to_stress_failure = 1e9
	}

	min_time := min(time_to_ablation, time_to_stress_failure)

	failure_mode := if time_to_ablation <= time_to_stress_failure { "ABLATION_BREACH" } else { "STRUCTURAL_FAILURE" }

	confidence := CONFIDENCE_FLOOR
	if min_time < time_horizon_s {
		confidence = min(0.95, CONFIDENCE_FLOOR + (1 - CONFIDENCE_FLOOR) * (1 - min_time / time_horizon_s))
	}

	action := "MONITOR"
	if min_time < 5.0 {
		action = "ABORT_TRAJECTORY"
	} else if min_time < 15.0 {
		action = "REDUCE_HEAT_FLUX_30_DEG"
	} else if min_time < 30.0 {
		action = "ADJUST_AOA_REDUCE_Q"
	}

	return Prediction_Result{
		tile_id              = state.tile_id,
		time_to_failure_s    = min(min_time, time_horizon_s),
		failure_mode         = failure_mode,
		confidence           = confidence,
		recommended_action   = action,
	}
}

// ── Mesh-Wide Simulation ────────────────────────────────────────
init_mesh :: proc(mesh: ^Thermal_Mesh, material: Material_Type, thickness_m: f64) {
	for i in 0..<MAX_TILES {
		mesh.tiles[i] = Tile_Thermal_State{
			tile_id           = u32(i),
			surface_temp      = 300.0,  // Ambient (K)
			heat_flux         = 0.0,
			pica_x_wear       = 0.0,
			thickness_m       = thickness_m,
			material          = material,
			integrity         = 1.0,
			ablation_depth_m  = 0.0,
			is_compromised    = false,
		}
	}
	mesh.tile_count      = MAX_TILES
	mesh.total_integrity = 1.0
}

update_mesh :: proc(mesh: ^Thermal_Mesh, conditions: ^Reentry_Conditions, dt: f64) {
	rho := compute_density(conditions.altitude_m)
	q   := compute_heat_flux(conditions.velocity_ms, rho)

	total_integrity := 0.0
	compromised     := 0

	for i in 0..<mesh.tile_count {
		tile := &mesh.tiles[i]
		tile.heat_flux = q
		compute_full_thermal_step(tile, conditions, dt)
		compute_integrity_index(tile, conditions.heat_flux_w_m2, conditions.dynamic_pressure_pa)
		total_integrity += tile.integrity
		if tile.is_compromised {
			compromised += 1
		}
	}

	if mesh.tile_count > 0 {
		mesh.total_integrity = total_integrity / f64(mesh.tile_count)
	}
}

// ── Trajectory Sensitivity (dQ/dα) ──────────────────────────────
compute_heat_flux_sensitivity :: proc(tile_x: f64, tile_y: f64, current_aoa: f64) -> f64 {
	theta            := math.atan2(tile_y, tile_x)
	stagnation_factor := math.cos(theta) * math.cos(theta)
	sensitivity      := stagnation_factor * 0.5 * math.sin(2 * math.to_radians(current_aoa))
	return sensitivity
}

// ── Entry Point (CLI) ───────────────────────────────────────────
main :: proc() {
	mesh := Thermal_Mesh{}
	init_mesh(&mesh, .PICA_X, 0.05)

	conditions := Reentry_Conditions{
		velocity_ms           = 7000,
		altitude_m            = 80000,
		dynamic_pressure_pa   = 1000,
		heat_flux_w_m2        = 500000,
		mach_number           = 20,
		angle_of_attack_deg   = 40,
	}

	update_mesh(&mesh, &conditions, 0.1)

	fmt.printf("Mesh integrity: %.4f\n", mesh.total_integrity)
	fmt.printf("Tile 0 temp:    %.1f K\n", mesh.tiles[0].surface_temp)
	fmt.printf("Tile 0 wear:    %.4f\n", mesh.tiles[0].pica_x_wear)

	result := predict_failure(&mesh.tiles[0], &conditions, 84.0)
	fmt.printf("Prediction:     %s in %.1fs (confidence %.2f)\n", result.failure_mode, result.time_to_failure_s, result.confidence)
	fmt.printf("Action:         %s\n", result.recommended_action)
}

// ── Tests ───────────────────────────────────────────────────────
when ODIN_TEST {
	import "core:testing"

	test_reentry_step :: proc(t: ^testing.T) {
		state := Tile_Thermal_State{
			tile_id           = 101,
			surface_temp      = 1800.0,
			heat_flux         = 15.0,
			pica_x_wear       = 0.0,
			thickness_m       = 0.05,
			material          = .PICA_X,
			integrity         = 1.0,
			ablation_depth_m  = 0.0,
			is_compromised    = false,
		}
		compute_reentry_step(&state, 1.0)
		if state.surface_temp <= 1800.0 {
			t.fail("Temperature should increase after reentry step")
		}
	}

	test_full_thermal_step :: proc(t: ^testing.T) {
		state := Tile_Thermal_State{
			tile_id           = 102,
			surface_temp      = 300.0,
			heat_flux         = 0.0,
			pica_x_wear       = 0.0,
			thickness_m       = 0.05,
			material          = .PICA_X,
			integrity         = 1.0,
			ablation_depth_m  = 0.0,
			is_compromised    = false,
		}
		conditions := Reentry_Conditions{
			velocity_ms           = 7000,
			altitude_m            = 80000,
			dynamic_pressure_pa   = 1000,
			heat_flux_w_m2        = 500000,
			mach_number           = 20,
			angle_of_attack_deg   = 40,
		}
		compute_full_thermal_step(&state, &conditions, 0.1)
		if state.surface_temp <= 300.0 {
			t.fail("Temperature should increase with heat flux")
		}
	}

	test_integrity_index :: proc(t: ^testing.T) {
		state := Tile_Thermal_State{
			tile_id           = 103,
			surface_temp      = 300.0,
			heat_flux         = 0.0,
			pica_x_wear       = 0.0,
			thickness_m       = 0.05,
			material          = .PICA_X,
			integrity         = 1.0,
			ablation_depth_m  = 0.0,
			is_compromised    = false,
		}
		conditions := Reentry_Conditions{
			velocity_ms           = 7000,
			altitude_m            = 80000,
			dynamic_pressure_pa   = 1000,
			heat_flux_w_m2        = 500000,
			mach_number           = 20,
			angle_of_attack_deg   = 40,
		}
		integrity := compute_integrity_index(&state, conditions.heat_flux_w_m2, conditions.dynamic_pressure_pa)
		if integrity < 0.0 || integrity > 1.0 {
			t.fail("Integrity should be between 0 and 1")
		}
	}

	test_failure_prediction :: proc(t: ^testing.T) {
		state := Tile_Thermal_State{
			tile_id           = 104,
			surface_temp      = 300.0,
			heat_flux         = 0.0,
			pica_x_wear       = 0.0,
			thickness_m       = 0.05,
			material          = .PICA_X,
			integrity         = 1.0,
			ablation_depth_m  = 0.0,
			is_compromised    = false,
		}
		conditions := Reentry_Conditions{
			velocity_ms           = 7000,
			altitude_m            = 80000,
			dynamic_pressure_pa   = 1000,
			heat_flux_w_m2        = 500000,
			mach_number           = 20,
			angle_of_attack_deg   = 40,
		}
		result := predict_failure(&state, &conditions, 84.0)
		if result.time_to_failure_s <= 0.0 {
			t.fail("Time to failure should be positive")
		}
		if result.confidence <= 0.0 {
			t.fail("Confidence should be positive")
		}
	}

	test_mesh_simulation :: proc(t: ^testing.T) {
		mesh := Thermal_Mesh{}
		init_mesh(&mesh, .PICA_X, 0.05)
		if mesh.tile_count != MAX_TILES {
			t.fail("Mesh should have MAX_TILES tiles")
		}
		conditions := Reentry_Conditions{
			velocity_ms           = 7000,
			altitude_m            = 80000,
			dynamic_pressure_pa   = 1000,
			heat_flux_w_m2        = 500000,
			mach_number           = 20,
			angle_of_attack_deg   = 40,
		}
		update_mesh(&mesh, &conditions, 0.1)
		if mesh.total_integrity < 0.0 || mesh.total_integrity > 1.0 {
			t.fail("Mesh integrity should be between 0 and 1")
		}
	}
}
