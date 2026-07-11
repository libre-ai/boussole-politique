# Nous Président *(nom provisoire — voir §10)* — Spécifications v0.1

> **En une phrase.** Un commun numérique qui présente au citoyen des lois définitivement adoptées,
> dépouillées de toute étiquette politique, le laisse se positionner à froid, puis lui révèle
> *a posteriori* quels élus ont voté comme lui.

---

## 1. Principes directeurs (non négociables)

| Principe | Conséquence de conception |
|---|---|
| **Dépassionner** | Pas de fil d'actu, pas de classement viral, pas de dopamine. Une loi = une carte, focus unique. |
| **Asynchrone / froid** | On ne juge qu'une loi *finie et stabilisée*. Aucune course à l'actualité. |
| **Aveugle au parti** | Couleur politique masquée jusqu'au *reveal*. Aucun signal tribal au moment du jugement. |
| **Le citoyen seul juge** | L'outil ne recommande pas, ne défend pas : il *révèle une coïncidence factuelle*. |
| **Commun numérique** | Code, données et méthodologie publics. La transparence est la défense, pas une option. |
| **Souveraineté / RGPD by design** | Positions citoyennes = donnée sensible (art. 9) → traitées côté client, jamais exigées côté serveur. |

---

## 2. Périmètre MVP

**Inclus**
- Assemblée nationale, **législature en cours** uniquement.
- **Lois définitivement adoptées** ayant fait l'objet d'un **scrutin public sur l'ensemble du texte**.
- Vote de référence = **dernier scrutin public AN sur l'ensemble** (vote conforme, texte de CMP, ou lecture définitive).

**Exclus du score principal (signalés en clair dans l'UX)**
- **Ratifications de conventions/traités** et textes techniques sans scrutin public.
- **Lois adoptées par 49.3** → traitées en **catégorie séparée** (cf. §4.4), jamais en pour/contre.
- Votes à main levée (aucune trace nominative).

**Hors périmètre MVP** : Sénat, Parlement européen (phase 2), amendements, votes intermédiaires de navette.

---

## 3. Modèle de données

Entités minimales (la donnée de vote est publique → librement stockable et rediffusable).

### `Loi`
- `id` (slug stable)
- `titre_officiel`
- `intitule_neutre` — reformulation courte, neutre *(couche moat, §6)*
- `description_neutre` — « ce que le texte fait concrètement », factuel, sans adjectif orienté
- `themes[]` — `{ theme_id, poids }` (multi-valué)
- `source_legifrance_url`, `dossier_legislatif_url`
- `mode_adoption` — `scrutin_public` | `49_3` | `exclu`
- `vote_reference_id` *(nullable si 49.3)*
- `date_adoption_definitive`
- `version`, `historique[]` *(git-tracked, cf. §6)*

### `VoteReference`
- `id`, `loi_id`
- `date`, `scrutin_officiel_url`
- `resultat` — adopté | rejeté
- `positions[]` → `{ elu_id, position }` où `position ∈ { pour, contre, abstention, absent }`

### `Elu`
- `id`, `nom`, `circonscription`, `groupe_id` *(masqué jusqu'au reveal)*
- `mandat_debut`, `mandat_fin` *(nullable)*

### `Theme`
- `id`, `libelle`, `parent_id` *(taxonomie ; mapping EuroVoc prévu en phase 2 UE)*

### `PositionCitoyen` *(local-first, jamais envoyée au serveur par défaut)*
- `loi_id`
- `valeur` — `{ -2, -1, +1, +2 }` ou `sans_avis`
- `horodatage_local`

### Branche 49.3 — `SignalRejet`
- `loi_id`, `motion_censure_url`
- `votants_pour_censure[]` → `{ elu_id }` *(seule donnée nominative disponible)*

---

## 4. Règles métier

### 4.1 Échelle de positionnement citoyen
4 modalités bipolaires + abstention :
`Fortement contre (-2)` · `Un peu contre (-1)` · `Un peu pour (+1)` · `Fortement pour (+2)` · `Sans avis (exclu du calcul)`.

### 4.2 Direction de l'élu
Sur le vote de référence : `pour` → +1, `contre` → -1, `abstention` → 0, `absent` → *non comptabilisé* (cf. 4.5).

### 4.3 Score de congruence (défaut v0.1)
Pour chaque loi où **le citoyen a un avis** ET **l'élu a une direction (`pour`/`contre`)** :
- **Accord** si `signe(valeur_citoyen) == signe(direction_elu)`.
- **Poids** = intensité du citoyen (`|valeur|` : `1` ou `2`) → un « fortement » pèse double.
- `abstention` de l'élu = demi-désaccord (poids/2) — *paramètre ouvert à révision*.

```
congruence = Σ(poids des accords) / Σ(poids des lois comptabilisées)
```
Exprimée en %, pondérable par les thèmes choisis par le citoyen (§4.6).

### 4.4 Traitement du 49.3 (catégorie séparée, hors score)
- Aucun « pour la loi » disponible → **signal nul** côté soutien.
- Seule donnée : **qui a voté la motion de censure** (rejet actif du texte *et* du gouvernement).
- Affichage dédié, libellé sans ambiguïté : *« Loi passée sans vote (49.3). Voici les seuls députés ayant activement tenté de la rejeter en votant la censure — ce n'est pas un vote sur la loi. »*
- **Jamais** agrégé au score de congruence principal.

### 4.5 Absence / participation (choix méthodo clé)
- Un élu `absent` sur une loi jugée par le citoyen → **loi exclue de son ratio de congruence** (l'absence ne pénalise pas le score, pour ne pas en faire un jugement implicite).
- Mais elle alimente un indicateur **séparé et transparent** : `taux de présence sur tes sujets`.
- Deux chiffres distincts au reveal : *« a voté comme toi à X % »* **et** *« était présent sur Y % de tes lois »*.

### 4.6 Pondération par thèmes
- Le citoyen surpondère des thèmes (santé, fiscalité, environnement…).
- Une loi multi-thèmes contribue au prorata de ses `poids` de thèmes croisés avec ceux du citoyen.
- ⚠️ L'étiquetage thématique est un acte d'interprétation (2ᵉ vecteur de biais) → versionné et sourcé comme les résumés.

---

## 5. Architecture technique

```
                 ┌─────────────────────────────────────────────┐
                 │  GitHub public (code + données + méthodo)    │
                 └─────────────────────────────────────────────┘
   Sources open data                Cœur Rust                    Clients
 ┌────────────────────┐      ┌──────────────────────┐      ┌──────────────────┐
 │ data.gouv (Datan)  │ ───▶ │ ETL (batch)          │ ───▶ │ API Hono (Bun)   │
 │ AN open data       │      │  normalise → JSON/CSV│      │  lecture seule   │
 │ Légifrance         │      │                      │      │  données publ.   │
 └────────────────────┘      │ Moteur de score      │      └──────────────────┘
                             │  (lib Rust)          │              │
                             └──────────┬───────────┘     ┌────────┴────────┐
                              WASM ◀────┼────▶ UniFFI      │                 │
                                        │                  ▼                 ▼
                                 ┌──────▼──────┐    ┌────────────┐   ┌────────────┐
                                 │ App web     │    │ Android    │   │ iOS        │
                                 │ (front+Bun) │    │ (Kotlin)   │   │ (Swift)    │
                                 └─────────────┘    └────────────┘   └────────────┘
                              Positions citoyennes = stockage LOCAL sur chaque client
```

**Décisions**
- **Cœur Rust** : (a) pipeline ETL batch qui produit le dataset normalisé (open data versionné), (b) **bibliothèque de scoring** unique.
- **Scoring côté client** : Rust → **WASM** (web), Rust → **UniFFI** (Kotlin/Swift). Le calcul tourne sur l'appareil → les positions ne transitent jamais → anonymat + art. 9 réglés par construction.
- **API (Bun + Hono)** : sert **uniquement la donnée publique** (lois, résumés, votes, thèmes) en lecture. Pas de PII par défaut.
- **Compte optionnel** : sert *seulement* à la synchro multi-appareils. Active alors un traitement art. 9 → **consentement explicite** + positions chiffrées côté client avant envoi. Désactivé = zéro donnée serveur.
- **Pas d'app desktop** (web couvre).
- **Tout en dépôt public** dès le départ : code, dataset, et **charte + historique des résumés**.

**Phasage de la surface** (mainteneur solo) :
1. Pipeline Rust + dataset open data + API Hono.
2. App web (WASM scoring) — premier produit utilisable.
3. Mobiles Kotlin/Swift via UniFFI.

---

## 6. Couche reformulation — le *moat* et le risque

Maintenue **par toi seul au départ**. Tenable uniquement si le **process** est transparent et contestable :

- **Charte de neutralité** écrite et publique : règles de rédaction (factuel, pas d'adjectif évaluatif, deux niveaux intitulé/description, interdits explicites). Chaque résumé est jugeable *contre la charte*, pas contre ton intention.
- **Versioning git** : chaque `intitule_neutre` / `description_neutre` / `themes` a un historique public. Toute modification est un commit traçable.
- **Sourcing obligatoire** : lien Légifrance + dossier législatif sur chaque loi. Le citoyen peut vérifier.
- **Mécanisme de correction** ouvert (issues GitHub + formulaire) : contestation publique, réponse traçable.
- **Backlog initial** : les lois déjà adoptées dans la législature en cours = bosse one-shot à rédiger avant lancement.

---

## 7. UX

- **Deck de cartes** : une loi à la fois, pile finie, pas de feed.
- **Résumé neutre d'abord** : `intitule_neutre` puis `description_neutre`. Déroulé minimal avant de pouvoir se positionner (anti-réflexe).
- **Positionnement par choix explicite** : 4 niveaux + « sans avis ». *Pas* de swipe-réflexe (le swipe binaire ne mappe pas 4 modalités et récompense la précipitation). Métaphore carte ✅, geste réflexe ❌.
- **Reveal ciblé**, jamais avant le positionnement :
  - **ton député** (circo) : a voté comme toi / contre toi / absent ;
  - agrégat par **groupe** (couleur dévoilée maintenant) ;
  - **score de congruence** cumulé + **taux de présence**, qui s'affinent loi après loi.
- **Notifications événementielles plafonnées** : déclencheur = *« une nouvelle loi est prête à juger »*. L'utilisateur règle un **plafond** d'interruption (défaut **1 digest / semaine**, max 1/jour). Jamais de ping creux.

---

## 8. Conformité & gouvernance

- **RGPD art. 9** : positions = opinions politiques. Par défaut, jamais collectées (local-first). Compte = opt-in, consentement explicite, chiffrement client.
- **Donnée des élus** : votes = donnée publique, OK. **Aucune** donnée judiciaire / procédure (art. 10) dans le MVP.
- **Neutralité = cible** : open-source + open data + charte + corrections publiques = la seule défense crédible contre contestation et récupération.
- **Présomption de représentation** : afficher clairement que « a voté comme toi sur N lois » ≠ « te représente » (le vote est une fraction du mandat, souvent discipliné).

---

## 9. Risques & points ouverts

| Risque | Statut / parade |
|---|---|
| Toi = éditeur unique des résumés | Process transparent (§6) ; ouvrir la rédaction à terme. |
| Sélection des lois = acte éditorial | Critère mécanique (scrutin public sur l'ensemble) + documenté publiquement. |
| Froid vs. actionnable surtout en période électorale | Assumer un outil de **culture civique**, pas de consigne de vote. |
| Surface large / mainteneur solo | Phasage strict (§5). Web avant mobiles. |
| Traitement de l'absence | Défaut posé (§4.5), explicitement ouvert à révision. |
| Modèle de soutien (commun ≠ revenus) | À définir : asso / mécénat / subvention civic-tech. **Ouvert.** |
| Nom « Nous Président » | Connotation Hollande 2012 + à vérifier INPI/domaine. **Ouvert.** |

---

## 10. Roadmap

1. **Socle données** — ETL Rust, dataset open data versionné, API Hono lecture seule.
2. **Couche reformulation** — charte + rédaction du backlog législature en cours.
3. **App web** — scoring WASM, deck de cartes, reveal, notifications plafonnées.
4. **Mobiles** — Kotlin/Swift via UniFFI.
5. **Phase 2 UE** — Parlement européen (HowTheyVote en couche faits, EuroVoc pour les thèmes), vocabulaire « règlement/directive », vote de référence = vote final en plénière.

---
*v0.1 — document de cadrage. Choix méthodo (pondération abstention, taxonomie thèmes FR, gouvernance éditoriale) destinés à évoluer.*
