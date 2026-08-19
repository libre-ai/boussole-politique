# Boussole Politique

Compare tes positions aux votes, sans étiquette — local-only, chiffrement au repos pour les données sensibles (couche 1).

Pour les électrices et les électeurs, qui rencontre des étiquettes politiques qui remplacent les faits, ce projet permet de comparer ses positions aux votes réellement exprimés, sans étiquette, en produisant des comparaisons position-par-vote sourcées et rejouables, sans dépendre de : aucun compte, aucune transmission — tout reste dans le navigateur.

## État du projet

<!-- libre-ai:project-status:begin -->
<!-- Section générée depuis project.v1.yaml — ne pas éditer à la main. -->

- Situation actuelle : L'application Boussole (garde no-transmission, chiffrement AES-256-GCM au repos pour les données Art. 9) est greffée et verte sur les briques épinglées. La phase data-corpus est éclatée en cinq livrables explicites (moteur Rust/WASM, instance méthode v3, dataset réel v3, énoncés relus polarité, pipeline extraction/provenance), tous encore à faire. Les contrats v3 (micros entiers, forme rationnelle exacte, polarité, taxonomie d'omission) sont livrés en candidate (libre-ai/contracts PR #8, draft, revue indépendante en attente) ; le gate à deux relecteurs externes reste un bloqueur nommé et assumé avant toute exposition publique — le produit avance en comparateur privé complet d'ici là.
- Maturité : usable
- Exposition : spec-published
- Confiance : medium
- Preuves vérifiées le : 2026-08-18
- Avancement : 16,7 % du périmètre actuellement déclaré

<!-- libre-ai:project-status:end -->

## Vérifier

- `bun install && bun run check` — la chaîne de gates du dépôt, tests inclus.
- La fiche [`project.v1.yaml`](./project.v1.yaml) est l'autorité de l'état du projet ; la section « État du projet » ci-dessus en est générée et un gate de flotte échoue si elles divergent.
- La provenance de chaque chemin migré depuis le hub est tracée dans l'index de migration de `libre-ai/libre-ai` (`ecosystem/migration-index.v1.yaml`).
