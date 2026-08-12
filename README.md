# Thermal Scenario Laboratory

**Installable local multi-tile thermal scenario software with bounded Python gradient, ablation, integrity, spectral, and threshold-horizon analysis plus a repository-owned pinned native Odin compile/run gate.**

> **Not affiliated with, endorsed by, or connected to SpaceX.** This repository is an independent GlacierEQ engineering portfolio project. It does not contain proprietary SpaceX systems, flight/TPS telemetry, calibrated spacecraft models, trajectory authority, or hardware-control access.

Evidence state: `LOCAL_THERMAL_SCENARIO_MODEL_NOT_FLIGHT_TPS_AUTHORITY`

## Working product surface

The repository now has one coherent local/reference thermal laboratory:

- validated multi-tile local state with illustrative material coefficients;
- bounded thermal-gradient histories and spectral scenario analysis;
- simplified local conduction/radiation/ablation/integrity arithmetic;
- bounded scenario threshold horizons and severity/review labels;
- explicit alternative-angle scenario comparison with `control_authority: false`;
- installable `thermal-scenario-demo` Python product surface with deterministic SHA-256 receipt;
- direct `scripts/operate.py` execution of the real thermal mechanisms;
- data-oriented Odin reference implementing the same bounded local scenario vocabulary;
- exact Odin compiler release/digest pin, native check/build/execute gate, and machine-readable native proof artifact.

Historical class names such as `HeatShieldPredictor`, `TrajectoryAdvisor`, and `AdaptiveReentryController` remain for compatibility. They do **not** establish validated heat-shield failure prediction, trajectory guidance, flight control, or TPS authority.

## Install and run Python

```bash
python -m pip install .
thermal-scenario-demo
python scripts/operate.py
```

## Native Odin gate

`scripts/ci/verify_odin.sh` pins the official Odin `dev-2026-08` Linux amd64 archive and its exact SHA-256, checks the compiler archive before extraction, compiles the checked-in `src/thermal_mesh.odin`, executes the resulting native program, verifies the evidence/control-boundary output, and emits `.verification-artifacts/native-odin-thermal.json`.

**Source presence is not native proof.** Passing native Odin execution is admitted only through an **exact-head workflow receipt** from the CI job that runs this gate. The repository does not self-certify a future CI result.

## Repository proof

```bash
bash scripts/ci/verify_python.sh
bash scripts/ci/verify_odin.sh
```

CI runs Python 3.11 and 3.13 verification plus one pinned native Odin job. The Public Thermal Scenario Truth Gate independently verifies the evidence ceiling and exact capability allowlist.

## Evidence boundary

This repository does not establish:

- SpaceX affiliation, endorsement, employment, or proprietary access;
- real spacecraft, re-entry, TPS, tile, trajectory, or flight telemetry;
- calibrated heat-shield failure probability, remaining useful life, diagnosis, or certification;
- trajectory guidance, abort authority, angle-of-attack commands, or hardware control;
- production deployment, flight readiness, safety suitability, scale, or performance;
- live MCP, APEX, AKOS, Mastermind, provider, or agent-mesh integration.

A natively executed local Odin scenario is still a **local scenario model**, not flight/TPS authority.
