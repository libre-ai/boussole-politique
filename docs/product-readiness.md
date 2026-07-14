# Cockpit local — Boussole Politique

- **Date canonique** : 2026-07-14
- **Snapshot** : `main@2c58f02`
- **Maturité officielle** : `contract-first`
- **Disponibilité** : `discovery`
- **Chemin local** : partiel / méthodologique
- **Lecture** : aucun claim d’application publique

Liens de contexte : [README](../README.md) · [roadmap](../roadmap.md)

## Verdict court

Ce dépôt est au stade de preuve documentaire et de contrats. Il n’est pas prêt pour publication.

**0 issue ouverte ≠ readiness** : la readiness dépend des preuves et des gates ci-dessous.

## Prouvé

| Domaine | Preuve |
|---|---|
| Dry-run AN 16/17 | `README.md`, `docs/implementation/m1-sensitivity.md`, `scripts/verify-m1-sensitivity.py`, CI |
| Formule + contrats Rust purs | `README.md`, `docs/implementation/contrats-rust-m2.md`, `crates/domain`, `crates/scoring`, `scripts/check-rust.sh`, CI |
| Assets déterministes | `README.md`, `.github/workflows/ci.yml`, `scripts/generate-assets.sh`, `scripts/test-assets.py` |
| Contrôles natif/WASM | `README.md`, `.github/workflows/ci.yml`, `scripts/check-rust.sh` |
| Sensibilité M1 scriptée | `scripts/verify-m1-sensitivity.py`, `docs/implementation/m1-sensitivity.md` |

## Partiel

- spec / architecture / identité proposées : `docs/spec-v1.md`, `docs/architecture-cible.md`, `docs/design/*`
- M1 : verdict `conditional`
- vivier déséquilibré : adopté/rejeté et couverture restent insuffisants pour une sélection canonique

## Bloqué

- sélection canonique
- symétrie / couverture
- revue indépendante
- shell Dioxus / axum local
- revue juridique

## Gates

- **P0** — fermer M1 / contrats + shell local
- **P1** — revue indépendante + pilote local
- **P2** — revue juridique + publication

## Notes

- aucun claim d’application publique
- aucune readiness déduite du seul nombre d’issues
