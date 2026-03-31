# Architecture notes

This repository tracks the **reference CLI** and configuration surfaces for the Recursive Coherence Engine (RCE) stack. The interactive binary (`agi`) performs session bootstrap: weight initialization, coherence checks, signal lock, and live manifold / semantic stream visualization.

## Planes

1. **Input plane** — tokenized stream with optional tool traces (future).
2. **RCE core** — Topological Stability Layer (TSL), sub-quadratic attention router, recursive coherence heads, manifold projector.
3. **Output plane** — decoded semantic stream plus diagnostics suitable for terminal visualization.

## Configuration

- `config/default.yaml` — conservative defaults for interactive sessions.
- `config/rce-7b.yaml` — model card parameters aligned with public benchmarks.
- `config/topology.toml` — scaffold metadata for TSL (build-time constants).

## Weights

Model artifacts are **not distributed** in this repository; see `weights/README.md`.
