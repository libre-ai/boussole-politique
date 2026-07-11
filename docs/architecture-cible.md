# Boussole Politique — note d'architecture cible

- **Statut** : proposition
- **Cible** : Rust-first, Dioxus 0.7 web/PWA, local-first

## 1. Décision d'ensemble

Boussole Politique doit être un produit autonome. Il consomme les kits Libre AI par contrats, sans leur déléguer son domaine, sa méthodologie VAA ou son expérience civique.

```text
Sources AN/Légifrance
        │
        ▼
 ETL Rust déterministe ──► couche Faits ──► rapport d'anomalies
        │                       │
        │                       ▼
        │                pool de sélection
        │                       │
        ▼                       ▼
 artefacts immuables ◄── sélection VAA versionnée + éditorial
        │
        ├──► hébergement statique / API Rust de lecture optionnelle
        │
        ▼
 Dioxus 0.7 PWA ──► stockage citoyen local ──► scoring Rust/WASM
                              │
                              └──► export/import local explicite
```

Le chemin critique ne requiert ni compte, ni base de données serveur, ni LLM, ni télémétrie.

## 2. Migration depuis les choix historiques

### Hono/Bun

Le couple Hono/Bun des specs v0.1–v0.5 est désormais un choix historique contradictoire avec la cible Rust/Dioxus.

Décision proposée :

1. **MVP** : publier des datasets immuables et fragmentés sur un hébergement statique. C'est plus simple, cacheable, forkable et cohérent avec une API uniquement publique.
2. **Si des requêtes serveur deviennent nécessaires** : utiliser un petit service **axum** en lecture seule.
3. **Dioxus server functions** : acceptables comme adaptateur de transport pour les lectures simples, mais pas comme emplacement du domaine ou du scoring.
4. Ne conserver Bun/Node que pour l'outillage déjà justifié, notamment Playwright/Tailwind ; aucun runtime JavaScript métier.

Cette migration supprime une pile de production sans perdre de capacité produit. Elle rapproche les tests, les types et l'observabilité du reste du workspace Rust.

### Template et design system

La source cible annoncée est `client-kit/templates/dioxus-app`. Dans l'état local observé, elle existe encore sous `libre-ai/portal/templates/dioxus-app`, et `dioxus-app-template` est un miroir public dont l'automatisation de synchronisation reste à terminer.

Au démarrage du repo :

- instancier depuis la source canonique disponible, sans prétendre que le miroir est généré tant que ce n'est pas prouvé ;
- conserver les gates du template : fmt, clippy, tests, Playwright multi-moteur, budget WASM, licences, static smoke ;
- remplacer le domaine de démonstration, pas les patrons éprouvés ;
- consommer le bundle Libre IA Design System 2.0 généré : tokens, thèmes, composants génériques, fontes locales, rapport de contraste et manifest hashé ;
- interdire les couleurs codées en dur dans les styles produit ;
- ne pas copier les valeurs de tokens dans une seconde source manuelle.

## 3. Structure de dépôt proposée

```text
boussole-politique/
  Cargo.toml
  Cargo.lock
  rust-toolchain.toml
  deny.toml
  Dioxus.toml

  apps/
    web/                         # shell Dioxus 0.7 + PWA
      src/
      assets/
        libre-ia/               # distribution client-kit générée/vérifiée
      e2e/

  crates/
    domain/                      # types et invariants Faits/VAA/Citoyen, sans renderer
    scoring/                     # fonctions pures, entières, WASM-ready
    dataset/                     # schemas, manifestes, validation, lecture des fragments
    selection/                   # filtre mécanique + rapports ; aucune curation cachée
    etl/                         # pipeline et adaptateurs AN/Légifrance
    app-core/                    # cas d'usage et ports stockage/réseau, sans Dioxus
    api/                         # axum lecture seule, optionnel
    ui/                          # composants Dioxus propres au métier

  data/
    sources/                     # inventaires/hashes, pas forcément les dumps lourds Git
    facts/                       # sorties dérivées ou petits samples
    selections/                 # versions immuables + justifications
    editorial/                  # formulations/résumés/versioning/sources
    samples/

  fixtures/
    scoring/vecteurs-test.json
    etl/an/leg16/
    etl/an/leg17/
    datasets/
    citizen-exports/

  docs/
    spec-v1.md
    architecture-cible.md
    charte-neutralite.md
    modele-menace.md
    donnees-personnelles.md
    plan-mvp.md
    adr/
    methodology/
    legal/

  schemas/                       # JSON Schema et formats publics versionnés
  proofs/                        # rapports acceptés, références et hashes
  scripts/                       # orchestration locale minimale
  xtask/                         # tâches Rust reproductibles
```

### Pourquoi `apps/web` plutôt que `crates/app`

Le shell Dioxus est une cible de rendu. Le mettre dans `apps/web` rend visible la frontière avec `app-core`, renderer-independent. Une future cible native consommerait `domain`, `scoring` et `app-core` sans dépendre de Dioxus web.

## 4. Responsabilités des crates

### `domain`

Possède les types métier et invariants : identifiants typés, scrutin, vote, mandat, groupe daté, énoncé, version éditoriale, sélection et position citoyenne sérialisable. Aucune I/O, aucun type Dioxus/axum, aucune décision de stockage.

Les types citoyen peuvent vivre dans cette crate pour partager le contrat, mais aucun dataset public ne doit les contenir.

### `scoring`

- fonctions pures ;
- arithmétique entière ;
- aucune date système, réseau, aléatoire ou état global ;
- application explicite de la polarité ;
- résultats structurés avec dénominateurs et raisons de non-affichage ;
- agrégation de groupe séparée ;
- compilation native et `wasm32-unknown-unknown` ;
- préparation UniFFI ultérieure sans imposer UniFFI au MVP.

### `dataset`

Possède les formats publiés, leur validation, leurs migrations compatibles et le chargement fragmenté. Il vérifie versions, hashes, références et cohérence interne. Il ne décide pas quels scrutins sélectionner.

Formats initiaux proposés :

- `bp.facts.v1` ;
- `bp.selection.v1` ;
- `bp.editorial.v1` ;
- `bp.dataset-manifest.v1` ;
- `bp.citizen-export.v1` ;
- `bp.score.v1`.

JSON est préférable pour les premières fixtures opposables. Le format de diffusion web (JSON compressé, CBOR ou autre) doit être choisi après mesure de taille et de décodage, sans modifier le modèle canonique.

### `selection`

Calcule le pool, les mesures de discriminance/participation et les rapports de couverture. Les décisions humaines sont des fichiers de données revus en PR, jamais des branches de code ou exceptions silencieuses.

### `etl`

CLI/bibliothèque native, hors WASM : téléchargement explicite, parsing, normalisation, quarantaine, validation, génération déterministe. Les adaptateurs de source sont séparés du modèle canonique. Toute ambiguïté produit un diagnostic stable.

### `app-core`

Orchestre les cas d'usage : charger un manifest, composer un lot, enregistrer localement une réponse, déclencher un reveal, calculer une vue et importer/exporter. Il définit des ports ; `apps/web` fournit les adaptateurs IndexedDB, fetch et fichier.

### `ui`

Contient seulement les composants Dioxus porteurs d'un sens Boussole Politique :

- carte d'énoncé ;
- contrôle de position à six états ;
- caveat de version ;
- reveal accord/divergence ;
- explication du dénominateur ;
- historique pré/post reveal ;
- parcours d'import/export.

Les boutons, champs, dialogues, focus, tokens, thèmes, touch targets et primitives ARIA génériques viennent de `client-kit`/Dioxus Primitives.

### `api`

Optionnelle. Sert seulement des ressources publiques, avec GET/HEAD, ETag, cache et compression. Elle ne dépend jamais du stockage citoyen et ne reçoit aucune position. Une route de santé ne contient aucune métrique utilisateur.

## 5. Frontière avec l'écosystème Libre AI

| Domaine | Possède | Ne possède pas |
|---|---|---|
| **Boussole Politique** | modèle parlementaire, sélection VAA, formule, UX de jugement/reveal, données citoyennes locales, ETL métier | design system générique, preuve générique, registry d'artefacts, orchestration agentique |
| **client-kit** | tokens, fontes, a11y, i18n UI générique, primitives, adapters, template Dioxus | carte d'énoncé, wording civique, lots/reveal, méthodologie VAA |
| **context-kit** | ingestion/référencement génériques, `SourceRef`, mémoire/retrieval réutilisable | vérité AN, matching parlementaire, sélection, résumé neutre, positions citoyennes |
| **proof-kit** | inspecteurs et formats de preuves : datasets, DB/security, a11y, usage des tokens, evidence reports | décision de publier, correction des faits, validation scientifique finale |
| **artifact-supply** | manifestes de release, checksums, signatures, provenance, rétention et distribution | contenu du dataset, règles ETL, sélection VAA, calcul de score |
| **agent-factory** | plans, dry-runs, gates, approvals et orchestration bornée | décisions éditoriales, ownership produit, données citoyennes, vérité méthodologique |

Règle d'intégration : contrats et artefacts versionnés, pas dépendance aux internes d'un kit. Le produit reste utilisable même si les services non essentiels sont indisponibles.

## 6. Design system Libre AI

Le design system assure la cohérence de marque, mais ne doit pas rendre l'expérience partisane ou promotionnelle.

### À réutiliser

- Inter et Plus Jakarta Sans locales ;
- échelle d'espacement, rayons, focus, touch target 44 px et reduced motion ;
- thèmes clair/sombre sémantiques ;
- boutons, champs, badges, callouts et accordéons génériques ;
- manifest et rapport de contraste vérifiables.

### À concevoir dans le produit

- hiérarchie de lecture d'un énoncé ;
- séparation visuelle Faits / Sélection / « tes réponses » ;
- révélation différée ;
- affichage obligatoire de `n`, `den` et caveats ;
- affichage des sources et de la version ;
- état « données insuffisantes » plus visible qu'un pourcentage caché ;
- tableaux accessibles équivalents aux visualisations.

### Garde-fous

- le vert Libre AI signifie action/focus de marque, jamais « politiquement favorable » ou « accord » à lui seul ;
- accord/désaccord ne repose ni sur rouge/vert ni sur des couleurs de parti ;
- aucun logo ou couleur de groupe avant reveal ;
- après reveal, nom et abréviation suffisent au MVP ;
- les transitions respectent `prefers-reduced-motion` et ne gamifient pas le score.

## 7. Données et diffusion

### Artefacts plutôt qu'API centrale

Un manifest signé à terme référence des fragments immuables :

```text
manifest.json
facts/leg-17/index.json
facts/leg-17/scrutins-0001.json.zst
selection/1.0.0.json
editorial/1.0.0.json
```

Le client met en cache par hash de contenu. Une nouvelle sélection ne réécrit pas la précédente. La publication peut commencer avec checksums + release Git signée ; `artifact-supply` prend ensuite en charge le contrat de distribution sans absorber la génération métier.

### Reproductibilité

Une exécution verrouillée doit produire les mêmes bytes ou un rapport expliquant les champs non déterministes exclus du hash. L'instant d'ingestion appartient au manifest d'exécution ; il ne doit pas rendre arbitrairement instable chaque enregistrement canonique.

## 8. Sécurité et vie privée

- zéro compte et zéro endpoint d'écriture dans le MVP ;
- CSP stricte, fontes et assets locaux ;
- aucune analytics tierce ;
- service worker limité aux artefacts publics et au shell ;
- aucune position dans URL, logs, traces, crash report ou cache HTTP ;
- stockage IndexedDB séparé par version de schéma ;
- import validé avant transaction atomique ;
- export explicite, jamais téléversé ;
- effacement local complet et vérifiable ;
- tests réseau e2e avec une réponse politique « canari » qui ne doit apparaître dans aucune requête.

## 9. Gates recommandés

### Rust

- `cargo fmt --all --check` ;
- clippy workspace, tous targets/features, warnings interdits ;
- tests unitaires et intégration ;
- build WASM des crates client ;
- `cargo deny` et audit ;
- MSRV/toolchain verrouillé.

### Données

- schemas valides ;
- références résolues ;
- totaux réconciliés ;
- mises au point appliquées ;
- provenance complète ;
- génération deux fois, hashes identiques ;
- aucune sélection sans justification.

### Web/PWA

- Playwright Chromium/Firefox/WebKit + viewport mobile ;
- budget WASM et données initiales ;
- offline smoke ;
- import/export round-trip ;
- contrôle de trafic sans fuite ;
- clavier, focus, reduced motion, contraste et lecteur d'écran manuel.

### Preuves

`proof-kit` inspecte et émet des preuves référencées. Le pipeline produit l'objet ; l'inspecteur ne doit pas générer l'objet qu'il certifie. Les gates de publication restent décidés dans le repo produit ou par `agent-factory` selon une politique approuvée.

## 10. ADRs à ouvrir immédiatement

1. `ADR-0000` — instanciation depuis le template Dioxus canonique.
2. `ADR-0001` — modèle en trois couches et dépendances autorisées.
3. `ADR-0002` — artefacts statiques d'abord, axum seulement sur besoin prouvé.
4. `ADR-0003` — formule entière, polarité et seuil par paire.
5. `ADR-0004` — reveal par lots et historique pré/post reveal.
6. `ADR-0005` — stockage IndexedDB et format d'export.
7. `ADR-0006` — formats/licences des faits et de l'éditorial.
8. `ADR-0007` — politique de version et correction éditoriale.
9. `ADR-0008` — consommation vérifiée du design system Libre AI.
