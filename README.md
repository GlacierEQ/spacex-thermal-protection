# Thermal Scenario Mesh

> **Independent local thermal-scenario engineering exhibit. Not affiliated with, endorsed by, or connected to SpaceX.**

This repository demonstrates deterministic **multi-tile thermal scenario modeling** across Python and an Odin reference implementation. It preserves data-oriented mesh structure, thermal-gradient analysis, simplified ablation/integrity arithmetic, bounded spectral analysis, and scenario sensitivity calculations while keeping the evidence boundary explicit.

## Recruiter surface

The useful engineering capability is not a claim to control or predict a real spacecraft. It is the ability to build and test a bounded thermal-state model with:

- deterministic multi-tile state evolution;
- local gradient-history and spectral anomaly scoring;
- simplified ablation and integrity indices;
- fail-closed validation for malformed/non-finite inputs;
- bounded scenario threshold horizons and severity scores;
- explicit separation between **scenario comparison** and **control authority**;
- a data-oriented Odin implementation kept as a source reference.

## Engineering surface

| Surface | What is actually established |
|---|---|
| `src/alpha/predictive_thermal.py` | Executable Python local scenario model with input validation, bounded histories, gradient/spectral analysis, integrity arithmetic, threshold-horizon scoring, and no-control-authority outputs |
| `src/thermal_mesh.odin` | Checked-in Odin data-oriented reference source preserving mesh/state mechanisms and the same evidence boundary |
| `tests/test_core.py` | Executable Python behavior and adversarial-boundary tests |
| `tests/test_odin_bridge.py` | Static source-contract checks for the Odin reference; **does not claim Odin compilation or execution** |
| `scripts/verify_public_surface.py` | Fail-closed public/machine truth verifier |

### Evidence state

`LOCAL_THERMAL_SCENARIO_MODEL_NOT_FLIGHT_TPS_AUTHORITY`

Outputs historically named `time_to_failure_s`, `confidence`, `recommended_action`, `TrajectoryAdvisor`, and `AdaptiveReentryController` are retained only where needed for API compatibility. Their current contract is narrower:

- `time_to_failure_s` = **modeled threshold horizon**, not validated remaining useful life;
- `confidence` = **bounded scenario severity score**, not calibrated probability/confidence;
- `recommended_action` = **review label**, not a trajectory or hardware command;
- angle-of-attack deltas = **hypothetical scenario inputs**, not flight guidance;
- controller class = **in-memory scenario runner**, not a flight controller.

## Machine proof

Run:

```bash
python -m pytest -q
python scripts/verify_public_surface.py
```

Repository CI runs the same proof against the exact pull-request/head source on supported Python versions.

## Explicit nonclaims

This repository establishes **none** of the following:

- SpaceX affiliation, employment, endorsement, proprietary access, or Starship design authority;
- real spacecraft, heat-shield, TPS-tile, atmospheric, sensor, or flight telemetry;
- calibrated thermal-material properties for an operational vehicle;
- validated Fay-Riddell, CFD, finite-element, ablation, delamination, or structural-failure prediction;
- a real 10–30 second failure precursor, failure probability, confidence calibration, diagnosis, remaining useful life, or certification result;
- trajectory guidance, abort logic, angle-of-attack command authority, flight control, or safety-critical operation;
- live MCP/APEX/AKOS/Mastermind/provider/agent-mesh integration;
- production deployment or operational safety suitability;
- Odin compiler/runtime proof. The Odin file is a reference source until a repository-owned gate explicitly installs and executes an Odin toolchain.

## Next proof gate

The strongest next technical gate is **native Odin compilation/execution bound to an exact source SHA**. Until that exists, the admitted capability must remain the executable Python thermal-scenario model plus the source-verified Odin reference.
