# AGENTS.md

Canonical agent-context surface for this repository. `CLAUDE.md` is a minimal adapter that imports this file.

## Purpose

Boussole Politique compares a person's civic priorities to sourced public votes — locally, privately, without profiling. It computes a transparent comparison with exact denominators, abstentions, and missing data visible, all on device; no political label, no voting advice, no account.

## Scope / Non-scope

- **Reserved home.** This repository is the public reserved home of Boussole Politique. The product is being rebuilt in the canonical base repository [`libre-ai/libre-ai`](https://github.com/libre-ai/libre-ai) (multi-repo topology, [ADR-0008](https://github.com/libre-ai/libre-ai/blob/main/docs/adr/0008-multi-repo-target-topology-and-brand.md)); it reopens as the real product repository when the owner activates it (wave 4).
- The legacy implementation carried here (Rust workspace `crates/domain` + `crates/scoring`, `apps/web`, dry-run assets) is **frozen for reference**.
- Non-scope: new product development in this repository until activation.

## Commands

Verified against `Cargo.toml`, `scripts/`, and `.github/workflows/ci.yml`:

- `./scripts/check-rust.sh` — full Rust gate: forbids `dioxus`/`axum` in `crates/domain` and `crates/scoring`, then `cargo fmt --all --check`, `cargo clippy --workspace --all-targets --all-features -- -D warnings`, `cargo test --workspace --all-targets --all-features`, `cargo build --workspace --target wasm32-unknown-unknown`.
- `python3 scripts/check-dry-run-portability.py` — dry-run portability check.
- `python3 scripts/verify-m1-sensitivity.py` — M1 sensitivity verification.
- `node --check dry-run/scripts/workflow-dry-run.js` — dry-run script syntax check.
- `./scripts/generate-assets.sh` / `python3 scripts/test-assets.py` — brand assets.

## CI gates

- `ci` (`.github/workflows/ci.yml`) — jobs: `rust-contracts`, `dry-run-portability`, `brand-assets`.
- `Context hygiene` (`.github/workflows/context-hygiene.yml`).

## Links

- [README](README.md) · [Français](README.fr.md)
- [docs/product-readiness.md](docs/product-readiness.md) — canonical readiness cockpit
- [docs/architecture-cible.md](docs/architecture-cible.md), [docs/charte-neutralite.md](docs/charte-neutralite.md), [docs/modele-menace.md](docs/modele-menace.md), [docs/donnees-personnelles.md](docs/donnees-personnelles.md)
- [specs-v0.5.md](specs-v0.5.md), [formule-congruence.md](formule-congruence.md), [modele-donnees-v2.md](modele-donnees-v2.md), [roadmap.md](roadmap.md)
