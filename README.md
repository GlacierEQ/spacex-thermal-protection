# SpaceX Thermal Protection — Odin Reentry Thermal Physics Engine 🛡️

> **Odin data-oriented reentry thermal physics solver for Starship Heatshield TPS tiles.**

[![Odin](https://img.shields.io/badge/Odin-v0.1.0+-blue)]()
[![Python](https://img.shields.io/badge/Python-3.9+-blue)]()
[![Domain](https://img.shields.io/badge/Domain-Aerospace%20Thermal-red)]()

---

## 🎯 For Recruiters & Hiring Managers

This repository implements **SpaceX Thermal Protection** — solving Mach 25 atmospheric reentry thermal equilibrium for heatshield tiles in Odin. It demonstrates:

- **Odin data-oriented architecture** with zero hidden control flow and explicit memory allocators
- **Radiative + conductive heat transfer solvers** modeling Mach 25 shock layer heating
- **Tile ablation and degradation tracking** calculating thermal margins across thousands of TPS tiles
- **Python simulation test wrapper** verifying temperature state output

**Why this matters**: Reentry thermal protection systems require deterministic physics solvers where memory layout and allocation strategy are controlled explicitly down to the byte.

---

## 🔬 For Engineers & Technical Reviewers

### Core Components

| Component | Language | Purpose |
|---|---|---|
| `src/reentry_thermal.odin` | Odin | Data-oriented heat transfer & shock layer physics solver |
| `tests/test_odin_bridge.py` | Python | Test wrapper verifying thermal calculations |

---

## 🤖 ML/AI & Programmatic Mesh Integration

- **MCP Tool**: `tps_thermal_margin()` — tile heat status queryable by flight agents
- **Mastermind Sidecar**: Connected to APEX Highway mesh
- **SHA-256 Integrity**: Tracked in `.integrity/file_hashes.json`

---

## ⚡ Quick Start

```bash
python3 tests/test_odin_bridge.py
```
