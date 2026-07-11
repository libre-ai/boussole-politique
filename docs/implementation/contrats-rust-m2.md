# M2 — contrats Rust initiaux

- **Statut** : implémentés, revue/compilation bloquées localement par l’absence de toolchain Rust
- **Date** : 2026-07-11

## Périmètre livré

- workspace Rust 2024 limité à `crates/domain` et `crates/scoring` ;
- aucune dépendance Dioxus ou axum ;
- contrats minimaux Faits/VAA/Citoyen ;
- groupe pris au vote et position rectifiée explicites dans `VoteFact` ;
- polarité sérialisée en `-1/+1` ;
- positions citoyennes sérialisées en `-2/-1/+1/+2/sans_avis/passer` ;
- score entier, compteurs d’abstention/non-vote/donnée manquante ;
- score indéfini si `den == 0` ;
- score calculé mais non affichable sous `N_MIN` ;
- majorité de groupe avec égalité et absence de direction distinguées ;
- copie bit-à-bit de `vecteurs-test.json` dans `fixtures/scoring/`.

## Portée des tests d’or

Les dix cas synthétiques contiennent les entrées par énoncé et sont donc recalculables intégralement, y compris `polarite = -1`.

Les trois profils réels du fixture ne contiennent que des **sorties agrégées**, pas les votes d’entrée par énoncé. Le test Rust vérifie leur gel et le cas `Éric Ciotti × SOC = 333‰, n=3`, mais ne prétend pas les recalculer. Une future fixture opposable devra embarquer les entrées réelles minimales pour fermer ce point en Rust.

## Gates préparés

```sh
./scripts/check-rust.sh
```

Le script exécute :

1. l’interdiction Dioxus/axum dans les deux crates ;
2. `cargo fmt --all --check` ;
3. clippy sur tous targets/features avec warnings interdits ;
4. les tests workspace ;
5. le build `wasm32-unknown-unknown`.

## Blocage observé

`cargo`, `rustc` et `rustup` sont absents de l’environnement courant. Aucun résultat de compilation, clippy, test Rust ou build WASM n’est donc déclaré. `Cargo.lock` sera produit et revu par la première résolution Cargo ; il ne doit pas être fabriqué manuellement.
