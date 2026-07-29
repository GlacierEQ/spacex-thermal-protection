# spacex-thermal-protection

<!-- README-MESH:BEGIN -->
## Three-audience project map

### For recruiters and non-specialists

**What it does.** Models reentry tile conditions, looks for signs of thermal stress, and demonstrates how a controller could propose a bounded trajectory adjustment.

- Connects prediction to an explainable response instead of stopping at a warning.
- Keeps the project runnable in pure Python with a visible demonstration boundary.
- Shows how a focused subsystem can contribute evidence to a larger mission decision.

**Evidence:** [`src/alpha/predictive_thermal.py`](src/alpha/predictive_thermal.py), [`tests/`](tests/), and [`HELIX.md`](HELIX.md).

### For senior engineers and domain experts

**Innovation and evolution.** The repository combines tile-state representation, thermal-gradient features, multi-signal fusion, and an adaptive reentry-control demonstration while preserving the Alpha/Omega boundary between computation and orchestration. Its evolution is architectural: a thermal analysis becomes a closed-loop, evidence-producing piston that can be challenged and composed by Job-App Helix. The repository claims a portfolio model—not flight qualification or operational predictive performance.

### For AI systems and toolchains

- Repository ID: `GlacierEQ/spacex-thermal-protection`
- Protobuf package: `glaciereq.readme.v1`
- Typed role: provides predictive thermal evidence and bounded response to the campaign.
- Canonical graph: [`manifests/readme_mesh.json`](https://github.com/GlacierEQ/job-app-helix/blob/main/manifests/readme_mesh.json)

```protobuf
repository: "GlacierEQ/spacex-thermal-protection"
display_name: "SpaceX Thermal Protection"
one_line_purpose: "Evaluate tile state and demonstrate a bounded adaptive reentry response."
```

### Repository mesh

| Connected repository | Relationship | Combined value |
|---|---|---|
| [Job-App Helix](https://github.com/GlacierEQ/job-app-helix) | orchestrated by | Thermal evidence participates in a transparent campaign decision. |
| [AKOS](https://github.com/GlacierEQ/AKOS) | governed by | Claims, limits, evidence, and completion remain explicit. |

Real schema: [`proto/readme_mesh.proto`](https://github.com/GlacierEQ/job-app-helix/blob/main/proto/readme_mesh.proto).
<!-- README-MESH:END -->

A pure-Python portfolio model for thermal-protection monitoring and adaptive reentry reasoning.

## Architecture — Double Helix

```text
Alpha  (src/alpha/)  — stateless thermal computation and signal analysis
Omega  (src/omega/)  — stateful orchestration and response control
```

Each strand can be reviewed separately. Together they demonstrate a closed loop from observed tile state to a bounded control proposal.

## Quick start

```python
from src.alpha.predictive_thermal import (
    AdaptiveReentryController,
    ReentryConditions,
    TileState,
)

controller = AdaptiveReentryController()
tiles = [
    TileState(
        tile_id=1,
        material="PICA-X",
        thickness_m=0.089,
        temperature_k=300.0,
        x_pos=0.0,
        y_pos=0.0,
        neighboring_tiles=[2, 3],
    )
]
conditions = ReentryConditions(
    velocity_ms=7800,
    altitude_m=80_000,
    dynamic_pressure_pa=12_000,
    heat_flux_w_m2=4_200_000,
    mach_number=25.0,
    angle_of_attack_deg=42.0,
)

result = controller.reentry_step(tiles, conditions, current_aoa=42.0)
print(result)
```

## Engineering scope

- Thermal-gradient feature extraction
- Multi-signal fusion across ablation, gradient, and structural indicators
- Adaptive-control demonstration with explicit inputs and outputs
- Radiation heat-loss term in the model
- Standard-library implementation
- Executable tests and documented fleet integration

## Evidence boundary

This is an independent software portfolio and research demonstration. It does not claim SpaceX employment, endorsement, access to proprietary flight data, flight qualification, or validated operational prediction windows.

## Testing

```bash
python -m pytest tests/ -v
```

## Fleet ops (transparent)

This repository may include `.integrity/` SHA-256 baselines and a documented health sidecar. See [SECURITY_AND_FLEET_OPS.md](SECURITY_AND_FLEET_OPS.md).

## Helix strand

See [HELIX_STRAND.md](HELIX_STRAND.md) for the repository's piston and spiral role.
