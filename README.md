# spacex-thermal-protection

Thermal protection system with predictive heat flux modeling for re-entry

## Architecture

**Double Helix (Alpha + Omega)**

- **Alpha** (`src/alpha/`): Pure computation — physics models, stateless transformations
- **Omega** (`src/omega/`): Control layer — orchestration, stateful management

## Quick Start

```python
from src.alpha.predictive_thermal import ThermalModel\nmodel = ThermalModel()\nheat = model.heat_flux(velocity=7800, altitude=80)\nprint(f'Heat flux: {heat:.1f} W/m²')
```

## Key Features

- Zero external dependencies (stdlib only)
- Stateless alpha models, stateful omega controllers
- SHA-256 file integrity verification
- Shadow watchdog daemon monitoring
- Mastermind sidecar for cross-domain coordination

## Project Structure

```
spacex-thermal-protection/
├── src/
│   ├── alpha/        # Physics models (stateless)
│   └── omega/        # Controllers (stateful)
├── tests/            # Unit tests
├── HELIX.md          # Architecture documentation
├── AGENTS.md         # Agent configuration
└── mastermind_sidecar.py  # Cross-domain health
```

## Testing

```bash
python -m pytest tests/ -v
```
