# Nous Président *(provisoire)* — Spécifications v0.3

> **Addendum à v0.1 + v0.2.** Piliers **non-fonctionnels** qui font la fiabilité et la durabilité
> d'un commun civique. Ordre = priorité retenue : ETL → Charte → Accessibilité → Gouvernance.
> Les versions précédentes (features, archi, LLM) restent la base et ne sont pas répétées.

---

## 1. Pipeline ETL & intégrité des données

Principe fondateur : **séparation stricte de deux couches**.
- **Couche FAITS** — dérivée automatiquement des sources, **jamais éditée à la main**.
- **Couche ÉDITORIALE** — résumés & thèmes, écrits à la main, gouvernés par la charte (§2).

La confiance vient de cette frontière : un fait n'est jamais retouché, une interprétation est toujours traçable.

### 1.1 Sources (autoritatives d'abord)
| Source | Usage | Statut |
|---|---|---|
| **AN open data** (data.assemblee-nationale.fr) | Scrutins, députés, organes/groupes, dossiers législatifs | **Autoritative** |
| **Légifrance / API PISTE** | Texte officiel, statut de promulgation | Autoritative |
| **Datan / data.gouv** | Confort, recoupement | Dérivée (jamais arbitre) |
| HowTheyVote, EUR-Lex/OEIL | Phase 2 UE | Autoritative (UE) |

Règle de conflit : en cas de divergence, **l'AN officielle l'emporte** ; la divergence est *loggée*, pas masquée.

### 1.2 Détection d'une « loi jugeable »
Critère mécanique (donc défendable) :
1. Texte **adopté définitivement / promulgué** (statut dossier législatif).
2. Possédant un **scrutin public sur l'ensemble** à l'AN.

Routage automatique :
- `scrutin public sur l'ensemble` → **loi jugeable** (couche faits standard).
- `engagement de responsabilité (49.3)` → **branche 49.3** (signal censure, hors score — §4.4 v0.1).
- `ratification` / `main levée` / pas de scrutin nominatif → **exclu**, étiqueté.

### 1.3 Navette
- Plusieurs lectures → **une seule entité `Loi`**.
- Vote de référence = **dernier scrutin public AN sur l'ensemble** (règle v0.1).
- Résolution d'ambiguïté documentée et déterministe (pas d'arbitrage au cas par cas non tracé).

### 1.4 Intégrité, reproductibilité, corrections
- **Pipeline idempotent et déterministe** : le dataset est entièrement **re-dérivable depuis les sources**.
- **Provenance** par enregistrement : URL source + horodatage d'ingestion + hash de la source.
- **Corrections officielles** (errata sur un scrutin) : jamais corrigées à la main → on **re-dérive** et on commit. La correction est visible dans l'historique.
- **Validation** (types Rust + contrôles) : chaque scrutin réconcilie ses totaux, chaque `elu_id` résout, chaque loi a sa source.
- **Dataset = commun** : publié versionné (GitHub Releases + miroir data.gouv), licence ouverte (Etalab/ODbL), schéma documenté, **changelog**.

### 1.5 Cadence
- Job **batch basse fréquence** (ex. quotidien) qui interroge les feeds AN. Publication des lois = *bursty*, aucun temps réel nécessaire — cohérent avec *asynchrone/froid*.
- Détection d'une nouvelle loi jugeable → déclenche (a) la tâche de rédaction éditoriale (§2), (b) la notification plafonnée (UX v0.1).

---

## 2. Charte de neutralité *(keystone)*

Document **public et versionné** régissant la couche éditoriale (`intitule_neutre`, `description_neutre`, `themes`). C'est la clé de voûte du moat (v0.1) **et** le référentiel de grounding du LLM (v0.2). Destiné à devenir un livrable autonome.

### 2.1 Principes de rédaction
- **Factualité** : décrire ce que le texte *fait*, jamais ce qu'il *vaut*.
- **Interdits explicites** : adjectifs évaluatifs (« ambitieux », « controversé »), verbes orientés (préférer le terme du texte à un synonyme connoté), superlatifs, euphémismes, **attribution d'intention**.
- **Symétrie** : présenter ce que le texte change sans cadrage gain/perte.
- **Multi-objet** : une loi fourre-tout → énumérer les volets factuellement, **sans hiérarchie implicite** (ordre, poids des mots).
- **Sourcing obligatoire** : chaque affirmation traçable au texte officiel.
- **Longueur bornée** : intitulé et description plafonnés (contrainte anti-éditorialisation).
- **Langue claire** : accessible (lien §3).

### 2.2 Process
1. Rédaction → **auto-revue contre checklist de la charte** → commit versionné → publication.
2. Métadonnées par résumé : `version`, `date`, `auteur`, `sources[]`, `statut ∈ {brouillon, publié, contesté}`.

### 2.3 Contestation & correction
- Canal public : issues GitHub + formulaire in-app.
- **Correction factuelle** (erreur) → corrigée vite, diff visible.
- **Contestation de neutralité** (désaccord) → débat public, arbitrage **selon la charte** (et à terme le comité, §4).
- Tout signalement reçoit une réponse traçable.

### 2.4 Grounding LLM
La charte **est** le référentiel d'alignement du modèle. Le LLM *cite* (texte + résumé), ne réécrit jamais le résumé, ne produit pas d'autorité (règle d'or v0.2 §1).

### 2.5 Garde-fou solo (transitoire)
Tant que la rédaction est solo : auto-revue contre charte écrite + **publication systématique des diffs** = la défense. Évolution prévue vers relecture croisée puis comité (§4). La charte elle-même est versionnée — c'est un commun.

---

## 3. Accessibilité & légitimité démocratique

Un outil civique que seuls les initiés savent utiliser **rate sa cible**.

### 3.1 Accessibilité technique
- Viser **conformité RGAA / WCAG AA** : contraste, navigation clavier, lecteurs d'écran.
- ⚠️ **Ne jamais coder une information par la seule couleur** — critique ici, car le *reveal* utilise la couleur politique. Toujours doubler par libellé/motif.
- Web léger : vieux appareils, faible bande passante (cohérent local-first + WASM compact). Lutte contre la fracture numérique.

### 3.2 Accessibilité cognitive & langagière
- Résumés en **langage clair** ; envisager une version **FALC** (Facile À Lire et à Comprendre).
- **Glossaire contextuel** : scrutin solennel, CMP, 49.3, navette… expliqués en un tap, sans quitter la carte.

### 3.3 Cold-start (problème structurel)
Un nouvel arrivant a **zéro position** → reveal vide, score non significatif. Réponses :
- **Seuil de significativité** : pas de score affiché avant `N` lois jugées (ex. ≥ 5) ; jauge sobre *« encore X lois pour un premier signal »*.
- **Lot d'amorçage** : proposer d'abord un petit échantillon de lois **variées** (plusieurs thèmes). ⚠️ Le choix de cet échantillon initial **est un acte éditorial** → critère documenté publiquement (ex. diversité thématique + tirage, pas sélection d'opportunité).
- **Pas de gamification** de la complétion (ni streak, ni badge) — cohérence anti-dopamine. Jauge informative, pas incitative.
- **Sans circonscription renseignée** → reveal par **groupe** seulement ; saisie de la circo optionnelle et **locale**.

---

## 4. Gouvernance & pérennité

> Ordonné dernier en *build*, mais reste le **risque de confiance n°1** : un arbitre solo de la neutralité n'est pas crédible dans la durée. À enclencher sans attendre la maturité technique complète.

### 4.1 Structure juridique
- **Association loi 1901** (ou fonds de dotation) : porte la responsabilité, reçoit dons/subventions, **dépersonnalise** le projet.
- **Directeur de publication** : obligation légale (LCEN) pour un service en ligne → responsabilité éditoriale nommée. À anticiper dès la mise en ligne.
- Viser à terme un **agrément/label d'intérêt général**.

### 4.2 Sortie du SPOF (bus factor)
- **Éditorial** : solo → relecture croisée → comité de rédaction formé à la charte.
- **Technique** : doc d'archi + dépôt public + **pipeline reproductible** (§1) → un tiers peut reprendre.
- **Décisionnel** : règles de décision **écrites**, pas dans une seule tête.

### 4.3 Gouvernance de la neutralité
- **Comité / conseil consultatif** mixte (juristes, politistes, journalistes, citoyens) arbitrant les contestations de charte.
- **Partenariat académique** (science politique) pour valider la méthodo (sélection des lois, formule de congruence) → légitimité externe, pas auto-proclamée.
- Rapports publics réguliers.

### 4.4 Financement (point ouvert depuis v0.1)
- **Compatible** : dons, mécénat, subventions civic-tech / open-source (ex. fondations, NGI/NLnet, fonds européens), reversement du **tier souverain payant** (v0.2) à l'association.
- **Refusé** : publicité, vente de données (incompatible art. 9 + ADN), **tout financement partisan**.
- **Règle d'or** : aucun financement créant un conflit d'intérêt politique ; **liste des financeurs publique** ; charte d'indépendance éditoriale vis-à-vis des financeurs.

### 4.5 Pérennité technique
Souveraineté (Clever Cloud), **zéro lock-in**, code + données récupérables par un tiers. Le commun survit à son fondateur.

---

## 5. Points ouverts consolidés

| Point | Version d'origine | Statut |
|---|---|---|
| Pondération de l'abstention dans le score | v0.1 §4.5 | Ouvert |
| Taxonomie de thèmes FR | v0.1 §4.6 | Ouvert |
| Nom & INPI/domaine | v0.1 | Ouvert |
| Modèle on-device retenu (qualité/poids, juridique FR) | v0.2 | Ouvert |
| Modalités d'abonnement du tier souverain | v0.2 | Ouvert |
| Critère du lot d'amorçage (cold-start) | v0.3 §3.3 | Ouvert |
| Modèle de menace / instrumentalisation / droit de réponse élus | — | **v0.4 candidate** |

---
*v0.3 — addendum de cadrage. Prochaine étape naturelle : extraire la **charte de neutralité** en document autonome (livrable rédactionnel), ou poser le **schéma de données + contrat d'API** prêt à coder.*
