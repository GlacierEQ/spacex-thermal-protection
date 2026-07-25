# spacex-thermal-protection

Predicts heat shield tile failure **during** reentry — not after.
Real-time trajectory adjustment to protect compromised tiles.
Pure Python. Zero dependencies. Runs anywhere.

## The Problem Nobody Solved Publicly

Every thermal protection system in the public domain is reactive:
detect damage after landing, analyze, improve next flight.

This one is predictive: thermal gradient anomalies appear 10–30 seconds
before a tile delaminates. Fourier analysis of tile-to-tile temperature
differentials catches the signature. The trajectory adjusts. The tile survives.

One wheel rolls. Four wheels is a vehicle.

## Architecture — Double Helix

```
Alpha  (src/alpha/)  — Pure computation. Physics models. Stateless.
Omega  (src/omega/)  — Control layer. Orchestration. Stateful.
```

Each strand works alone. Together they close the loop.

## Quick Start

```python
from src.alpha.predictive_thermal import AdaptiveReentryController, TileState, ReentryConditions

controller = AdaptiveReentryController()

tiles = [
    TileState(tile_id=1, material="PICA-X", thickness_m=0.089,
              temperature_k=300.0, x_pos=0.0, y_pos=0.0,
              neighboring_tiles=[2, 3]),
]

conditions = ReentryConditions(
    velocity_ms=7800, altitude_m=80_000,
    dynamic_pressure_pa=12_000, heat_flux_w_m2=4_200_000,
    mach_number=25.0, angle_of_attack_deg=42.0,  # always 42
)

result = controller.reentry_step(tiles, conditions, current_aoa=42.0)
print(result)
```

## Key Features

- Delamination precursor detection via Fourier gradient analysis
- Bayesian signal fusion: ablation + gradient + structural integrity
- Real-time trajectory correction via adjoint sensitivity method
- Radiation heat loss included (the term that matters at Mach 25)
- Zero external dependencies — stdlib only
- Mastermind sidecar for cross-domain coordination

## Project Structure

```
spacex-thermal-protection/
├── src/
│   ├── alpha/        # Physics models (stateless)
│   └── omega/        # Controllers (stateful)
├── tests/
├── HELIX.md
├── AGENTS.md
└── mastermind_sidecar.py
```

## Testing

```bash
python -m pytest tests/ -v
```

---

## Fleet ops (transparent)

This repo may include **`.integrity/`** (SHA-256 baselines / watchdog) and/or a health sidecar.
These are **documented multi-repo fleet operations**, not covert implants.

See [SECURITY_AND_FLEET_OPS.md](SECURITY_AND_FLEET_OPS.md) and
`~/GlacierEQ_Swarm/state/PORTFOLIO_SHADOW_AND_GAUNTLET.md`.

## Helix strand

See [HELIX_STRAND.md](HELIX_STRAND.md) — piston/spiral role in the portfolio double helix.
