package thermal_mesh

import "core:fmt"

Tile_Thermal_State :: struct {
    tile_id:      u32,
    surface_temp: f64, // Kelvin
    heat_flux:    f64, // MW/m^2
    pica_x_wear:  f64, // Wear ratio 0.0 - 1.0
}

compute_reentry_step :: proc(state: ^Tile_Thermal_State, dt: f64) {
    heat_absorbed := state.heat_flux * dt * 0.042
    state.surface_temp += heat_absorbed
    if state.surface_temp > 1923.15 { // 1650°C ablation limit
        state.pica_x_wear += dt * 0.001
    }
}
