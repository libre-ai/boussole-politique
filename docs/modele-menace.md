# Boussole Politique — modèle de menace MVP

- **Statut** : proposition
- **Périmètre** : PWA sans compte, artefacts publics de lecture, positions locales

## 1. Actifs à protéger

1. Positions et historique politique du citoyen.
2. Intégrité des faits, sélections, résumés et formules.
3. Authenticité des artefacts officiels.
4. Confidentialité des exports locaux.
5. Disponibilité raisonnable du service public.
6. Réputation méthodologique et absence de fausse attribution.

## 2. Frontières de confiance

- navigateur/appareil du citoyen : contient les données sensibles ; hors contrôle total du projet ;
- origine web et service worker : code autorisé à lire le stockage local ;
- hébergement public : ne contient que code et données publiques ;
- chaîne CI/release : peut altérer code, sélection et datasets ;
- sources AN/Légifrance : autoritatives mais formats et disponibilité variables ;
- dépendances et `client-kit` : supply chain à vérifier ;
- fichiers d'import : entrée hostile potentielle.

## 3. Menaces prioritaires

| Menace | Impact | Défense MVP |
|---|---|---|
| Exfiltration par analytics, logs ou requête | critique | aucun tracker, aucun endpoint write, CSP, test canari réseau |
| XSS lisant IndexedDB | critique | pas de HTML non sûr, CSP, revue dépendances, rendu texte par défaut |
| Service worker compromis ou obsolète | critique | versionnement, intégrité/release, stratégie d'update explicite, pas de cache citoyen |
| Import forgé/corrompu | élevé | schéma strict, limites de taille, validation avant transaction, pas d'URLs actives |
| Dépôt/CI compromis | critique | MFA matériel, branches protégées, revues, commits/tags signés, secrets minimaux |
| Dataset ou sélection substitué | élevé | hashes dans manifest, signatures à terme, origine officielle vérifiable |
| Matching ETL faux mais plausible | élevé | fail closed, quarantaine, fixtures, provenance, rapports d'anomalies |
| Capture décontextualisée d'un score | élevé | aucun export social/palmarès, contexte adjacent obligatoire, limites visibles |
| Fork utilisant la marque | moyen/élevé | politique de marque, page d'authenticité, releases vérifiables |
| Perte du stockage local | élevé pour l'usager | persistance best-effort, export/import, avertissement honnête |
| Appareil partagé/volé | élevé | pas de promesse de secret au repos ; effacement ; chiffrement d'export optionnel futur |
| DDoS | moyen | données statiques, CDN/cache, aucune opération coûteuse publique |
| Déni de service par gros dataset | moyen | fragments bornés, budgets taille/mémoire, validation |

## 4. Abus méthodologiques

- curation opportuniste pour favoriser un résultat ;
- inversion erronée de polarité ;
- score affiché sous le seuil ;
- omission d'une mise au point ;
- confusion groupe actuel/groupe au vote ;
- changement silencieux d'un résumé déjà jugé ;
- classement reconstituable depuis une route dédiée.

Défenses : formats immuables, revues, vecteurs publics, rapports de sélection, composants exigeant le dénominateur, aucune route de ranking et preuve indépendante par `proof-kit`.

## 5. Données explicitement interdites côté serveur MVP

- position ou texte du miroir citoyen ;
- historique de consultation associé à un identifiant ;
- circonscription choisie ;
- export citoyen ;
- identifiant stable d'appareil ;
- token push ;
- empreinte navigateur ajoutée par le produit ;
- clé d'export.

Les logs d'infrastructure peuvent voir une IP au transport : minimiser leur rétention et ne pas prétendre « aucune donnée » au sens absolu. Documenter l'hébergeur et sa configuration.

## 6. Hypothèses et limites

- un navigateur ou OS compromis peut lire les positions ; l'application web ne peut pas l'empêcher ;
- un utilisateur peut faire une capture d'écran ; l'anti-instrumentalisation réduit les formats prêts à l'emploi, pas la possibilité physique ;
- un export non chiffré est sensible ; l'interface doit le dire avant création ;
- la signature garantit l'origine, pas la justesse méthodologique ;
- l'open source facilite l'audit mais ne constitue pas un audit.

## 7. Tests de sécurité initiaux

- canari de position absent de toutes requêtes, URLs et logs e2e ;
- CSP sans `unsafe-inline`/origines tierces non justifiées ;
- rendu d'une formulation contenant HTML/script comme texte inerte ;
- import surdimensionné, récursif, doublonné, version inconnue et hash invalide ;
- mise à jour de service worker sans perte de données ;
- artefact au hash invalide refusé ;
- scan dépendances/licences ;
- recherche automatisée de secrets et données sensibles dans preuves/builds ;
- vérification qu'aucun POST/PUT/PATCH de données citoyennes n'existe.

## 8. Menaces futures exigeant une nouvelle revue

Compte, sync E2E, BYO-key, LLM cloud, notifications, télémétrie, agrégats, mobile natif et géocodage changent les frontières de confiance. Aucun ne doit être ajouté par extension de cette analyse : chacun requiert un threat model et une décision juridique propres.
