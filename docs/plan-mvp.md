# Boussole Politique — plan MVP, décisions et backlog initial

- **Statut** : proposition réaliste, ordonnée par réduction de risque

## 1. Définition du MVP

Le MVP prouve une boucle complète sur un corpus limité mais réel : charger une sélection VAA versionnée, juger localement un lot d'énoncés, révéler sobrement les votes de groupes et d'élus, calculer une congruence avec dénominateur, puis exporter/importer les réponses sans envoi serveur.

Le MVP ne promet pas encore une couverture nationale exhaustive de toutes les législatures, une validation académique achevée, du mobile natif, de l'IA, de la synchronisation ou des agrégats d'opinion.

## 2. Étapes et gates

### M0 — Cadre consolidé

Livrables :

- spec v1 ;
- note d'architecture ;
- charte de neutralité ;
- modèle de menace ;
- politique de données personnelles ;
- ADRs initiaux ;
- registre des décisions ouvertes.

Gate : aucune contradiction connue n'est laissée implicite ; les paramètres non validés sont nommés comme hypothèses.

### M1 — Validation empirique du pivot VAA

- router le vivier élargi sur les législatures 16 et 17 ;
- mesurer participation, discriminance, données manquantes et couverture ;
- tester plusieurs paramètres sans choisir après avoir regardé le résultat souhaité ;
- publier un rapport de sensibilité ;
- définir le protocole de curation et rechercher une revue académique.

Gate : le pool est assez fourni et divers pour un premier lot ; sinon, le produit s'arrête au prototype méthodologique au lieu de fabriquer un reveal artificiel.

### M2 — Contrats Rust et scoring

- types Faits/VAA/Citoyen ;
- formats versionnés ;
- score entier ;
- polarité explicite ;
- position majoritaire de groupe ;
- vecteurs historiques importés puis complétés ;
- propriétés mathématiques testées.

Gate : sorties bit-à-bit identiques en natif et WASM ; aucun score affichable sous le seuil.

### M3 — ETL AN minimal

- ingestion de fixtures archivées d'une législature close, puis de la législature courante ;
- scrutins, votes, groupes au vote, mises au point, dossiers, actes récursifs, mandats disponibles et motions ;
- provenance, quarantaine et diagnostics ;
- génération reproductible de petits artefacts publics.

Gate : deux exécutions sur les mêmes snapshots produisent les mêmes hashes ; toute ambiguïté est visible.

### M4 — Sélection et éditorial pilote

- filtre mécanique ;
- rapport de pool ;
- sélection pilote de 10 à 15 énoncés, suffisante pour tester `N_MIN=10` sans prétendre constituer le corpus final ;
- formulation, résumé, sources, polarité, caveats et justifications ;
- revue croisée selon la charte.

Gate : chaque énoncé relie sans ambiguïté formulation, scrutin, version, sources et justification de sélection.

### M5 — Dioxus PWA local-first

- instanciation du template `client-kit` ;
- design system Libre AI consommé comme artefact vérifié ;
- onboarding ;
- lot fini ;
- réponses six états ;
- IndexedDB et persistance ;
- mode hors-ligne du shell et des données du lot.

Gate : le parcours fonctionne sans compte et sans endpoint d'écriture ; test réseau sans fuite de positions.

### M6 — Reveal sobre

- reveal par lot de cinq ;
- accords/divergences ;
- position des groupes et, si sélection locale d'une circonscription, mandats concernés ;
- score + `n` + `den` + couverture ;
- abstentions/non-votes séparés ;
- aucun classement.

Gate : aucun composant ne peut afficher un pourcentage sans contexte obligatoire ; aucune information ne dépend de la seule couleur.

### M7 — Export/import local

- format public `bp.citizen-export.v1` ;
- aperçu et validation ;
- import transactionnel ;
- migrations ;
- effacement complet ;
- gestion des versions éditoriales obsolètes.

Gate : round-trip exact, import corrompu refusé sans perte des données existantes.

### M8 — Preuves et pré-lancement

- preuves dataset/méthode/reproductibilité ;
- inspection sécurité et absence de fuite ;
- rapport a11y automatisé et revue manuelle ;
- rapport design tokens/contraste ;
- revue juridique et procédures ;
- page limites/méthodologie visible.

Gate : aucun lancement public tant que les blockers juridiques, éditoriaux et de confidentialité ne sont pas traités.

## 3. Décisions ouvertes à trancher

| Décision | Défaut de travail | Condition de décision |
|---|---|---|
| Nom et slogan | Boussole Politique ; sous-titre factuel | recherche INPI/domaines + test de compréhension non électoral |
| Formulation des réponses | accord/désaccord avec un énoncé | test utilisateur et validation de la polarité |
| `N_MIN` | 10 par paire | analyse de sensibilité + avis méthodologique |
| Seuil de discriminance | 0,20 | rapport sur leg 16/17, pré-enregistrement avant curation finale |
| Taille de sélection | 30–40 à terme ; 10–15 pilote | couverture et fatigue mesurées sans télémétrie intrusive |
| Taille du lot | 5 | test de compréhension et effet de révélation |
| Révision post-reveal | historique, pré-reveal immuable | test UX ; ne jamais écraser l'original |
| Taxonomie | sous-ensemble français EuroVoc | atelier éditorial + stabilité inter-législatures |
| Résolution de circonscription | choix manuel local au MVP | éviter tout géocodage serveur |
| Licence faits | Licence Ouverte 2.0 si compatible avec chaque source | revue des licences source |
| Licence éditoriale | CC BY-SA à étudier | stratégie d'attribution et anti-fausse-attribution |
| Format de diffusion | JSON pour contrats, compression après benchmark | budget téléchargement/décodage |
| API | aucune au MVP si statique suffit | besoin produit mesuré |
| Validation académique | revue avant revendication publique forte | partenaire et protocole à établir |

## 4. Contradictions historiques résolues par v1

| Ancienne position | Position v1 |
|---|---|
| unité = loi promulguée avec vote final | unité = énoncé VAA adossé à un scrutin sélectionné |
| sélection mécanique exhaustive | faits exhaustifs dans le périmètre ; VAA curatée et justifiée |
| abstention = demi-désaccord | abstention exclue, indicateur séparé |
| `absent` source | absence seulement dérivée/fragile, hors score |
| « taux de présence » | participation aux scrutins retenus |
| ratifications exclues en bloc | éligibles si le scrutin est pertinent |
| une motion de censure | 0..n motions par texte/lecture |
| groupe actuel | groupe au moment du vote |
| seuil après cinq lois citoyennes | seuil `N_MIN` par paire |
| reveal carte par carte | reveal par lot, défaut 5 |
| top/bottom élus | supprimé : incompatible anti-palmarès |
| Hono/Bun en production | artefacts statiques puis axum si besoin |
| front Bun | Dioxus 0.7 web/PWA |
| compte/sync dans le premier produit | hors MVP |
| télémétrie DP et write API | hors MVP et future spec autonome |
| pondération thématique | hors score MVP |
| invariant « rien ne sort jamais » avec BYO/sync | MVP : rien ne sort ; toute future exception exige acte explicite et spec dédiée |

## 5. Risques majeurs et garde-fous

### Sélection VAA capturable

**Risque** : fabriquer le résultat par choix des énoncés.

**Garde-fous** : pool publié, inclusions et exclusions justifiées, paramètres pré-enregistrés, versions immuables, rapport de sensibilité, revue indépendante et canal de contestation.

### Formulation/polarité orientée

**Risque** : une formulation apparemment neutre inverse ou simplifie le scrutin.

**Garde-fous** : formulation distincte du résumé, polarité revue à deux, sources ancrées, tests `polarite=-1`, caveats et historique.

### Surinterprétation du score

**Risque** : « 80 % » devient « bon représentant ».

**Garde-fous** : phrase canonique, dénominateurs, seuil, limites adjacentes au chiffre, divergences détaillées, aucun palmarès ni partage.

### Donnée parlementaire imparfaite

**Risque** : faux lien, élu manquant, mauvaise version ou mise au point ignorée.

**Garde-fous** : fail closed, quarantaine, fixtures multi-législatures, provenance, position rectifiée, groupe daté, caveat de dérive.

### Perte des données locales

**Risque** : purge Safari/ITP ou changement d'appareil.

**Garde-fous** : `storage.persist()`, PWA, export/import visible, rappel local non intrusif, tests de migration. Ne pas promettre une persistance garantie par le navigateur.

### Fuite d'opinions

**Risque** : logs, URL, crash report, analytics ou import téléversé.

**Garde-fous** : zéro endpoint d'écriture, zéro analytics, canaris e2e réseau, CSP, logs IDs publics seulement, revue des dépendances, suppression locale.

### Instrumentalisation

**Risque** : captures ou cartes d'attaque.

**Garde-fous** : pas de classement/export social, contexte indissociable du score dans le DOM, marque/méthode publiques et correctifs publics. Une capture reste techniquement possible : ne pas prétendre l'empêcher.

### Accessibilité de façade

**Risque** : conformité automatisée mais parcours inutilisable.

**Garde-fous** : tests clavier/lecteur d'écran, revue manuelle RGAA, textes clairs, glossaire, tableaux alternatifs et FALC planifié.

### Confusion design/position politique

**Risque** : vert Libre AI interprété comme « pour ».

**Garde-fous** : le vert reste une couleur d'action ; accord/désaccord et groupes sont nommés et codés par texte/motif, jamais par couleur seule.

## 6. Premières issues / PRs atomiques

### Documentation et décisions

1. **PR — Rebrand documentaire** : nom, promesse, redirections prévues, aucun rename de schema/crate.
2. **PR — Spec v1 + registre de contradictions**.
3. **PR — Charte de neutralité v1**.
4. **PR — ADR modèle trois couches**.
5. **PR — ADR scoring/polarité/seuil**.
6. **PR — Modèle de menace + données personnelles MVP**.
7. **Issue — Recherche nom/INPI/domaines et test de compréhension**.
8. **Issue — Protocole de revue académique de la sélection**.

### Contrats et tests

9. **PR — Workspace Rust vide + gates du template**, sans feature produit.
10. **PR — Types `domain` Faits minimaux et fixtures serde**.
11. **PR — Types VAA + formulation/polarité/version**.
12. **PR — `scoring` sur vecteurs existants**.
13. **PR — Vecteurs polarité inverse, égalité groupe et mise au point**.
14. **PR — Property tests du score**.
15. **PR — JSON Schemas v1 et tests de compatibilité**.

### ETL et sélection

16. **PR — Parseur AN objet-ou-tableau + fixtures**.
17. **PR — Normalisation apostrophes/lectures + ambiguïtés en quarantaine**.
18. **PR — Votes, groupes au vote et mises au point**.
19. **PR — Actes récursifs, promulgation et décisions CC disponibles**.
20. **PR — Motions 49.2/49.3 multiples et précédence**.
21. **PR — Rapport du vivier élargi leg 16**.
22. **PR — Rapport comparatif leg 17 + sensibilité des seuils**.
23. **PR — Format de sélection et linter de justifications**.
24. **PR — Sélection pilote versionnée**.

### PWA

25. **PR — Instanciation Dioxus 0.7 depuis `client-kit/templates/dioxus-app`**.
26. **PR — Consommation vérifiée du Design System 2.0**.
27. **PR — Adaptateur dataset statique + cache par hash**.
28. **PR — Stockage IndexedDB/migrations sans UI**.
29. **PR — Carte d'énoncé accessible**.
30. **PR — Contrôle de position six états au clavier**.
31. **PR — Lots et verrou pré-reveal**.
32. **PR — Reveal groupes sans classement**.
33. **PR — Score contextualisé impossible à rendre sans dénominateur**.
34. **PR — Circonscription manuelle locale et chronologie des mandats**.
35. **PR — Export/import transactionnel**.
36. **PR — Offline/PWA et persistance best-effort**.

### Preuves

37. **PR — Test e2e canari : aucune position dans le réseau**.
38. **PR — Preuve de reproductibilité dataset**.
39. **PR — Rapport `proof-kit` tokens/contraste/a11y**.
40. **PR — Audit manuel RGAA du parcours essentiel**.
41. **PR — Page publique méthode, limites, versions et corrections**.

Chaque PR doit avoir un seul résultat vérifiable. Les PRs de rename, de logique métier et de migration de schéma restent séparées.
