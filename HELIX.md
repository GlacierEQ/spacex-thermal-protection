# HELIX Architecture — spacex-thermal-protection

## Double Helix Pattern

**Alpha (What)** — Pure physics models, stateless computation
- predictive_thermal

**Omega (How)** — Controllers, orchestration, stateful management  
- 

## Design Principles

- Zero external dependencies (stdlib only)
- Stateless alpha, stateful omega
- SHA-256 file integrity verification
- Shadow watchdog daemon monitoring
- Mastermind sidecar coordination

## Data Flow

```
Alpha Models → Omega Controllers → Mastermind Sidecar → Shadow Infrastructure
```
