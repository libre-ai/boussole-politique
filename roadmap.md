# Boussole Politique — État & roadmap

> Plan vivant du projet. Tenu à jour à chaque chantier. Dernière révision : **2026-07-14**.
> Cockpit local : `docs/product-readiness.md`.
> Mode : *monde idéal* (sans contrainte de temps/budget ; on n'arbitre que sur l'exactitude, la
> complétude, la qualité). La roadmap aval reprend et actualise `revue-specs-2026-06-12.md` §5.

## 1. Où on en est

| Étape | Date | Statut |
|---|---|---|
| Cadrage conceptuel (specs v0.1 → v0.5) | — | ✅ saturé |
| Revue critique des specs | 2026-06-12 | ✅ |
| Dry-run sur données réelles AN (leg 16+17, 159 lois) | 2026-06-13 | ✅ 7 analyses vérifiées |
| **Pivot VAA + modèle de données v2 + formule + vecteurs** | **2026-06-16** | ✅ |
| **Confrontation du vivier élargi (Q8)** | **2026-07-11** | 🟡 viable mais validation conditionnelle |
| **Spec v1 + architecture + chartes MVP** | **2026-07-11** | 🟡 propositions à valider |
| **Contrat de polarité exécutable** | **2026-07-11** | ✅ formule + 10e vecteur synthétique |
| **Identité et assets PWA provisoires** | **2026-07-11** | 🟡 génération/hash/dimensions/safe zone passent ; revue humaine en attente |
| **Workspace `domain` + `scoring`** | **2026-07-11** | 🟡 code et tests d’or préparés ; gates Rust prouvés en CI avec toolchain verrouillée |

Q8 trouve un vivier cœur de **117 scrutins exploratoires** (overrides proposés inclus), dont **95 à lien
source fort**, au filtre de travail (discriminance ≥ 0,20 ; participation ≥ 0,20), sur les deux
législatures. Il contient les deux sorts et des directions de groupe bidirectionnelles, mais reste
déséquilibré (84 adoptés / 11 rejetés dans le sous-ensemble fort). Restent non prouvés : symétrie
politique, couverture thématique et caractère structurant des amendements.

Les assets de marque sont reproductibles deux fois à hashes identiques dans l’environnement local ; les
contrôles XML, dimensions, opacité, contrastes, manifest et zone sûre maskable passent. La piste visuelle
reste une **proposition**, pas une icône de store validée. Le workspace Rust contient les contrats purs
et les dix tests synthétiques ; la CI atteste aussi `fmt`/`clippy`/tests/`build` WASM avec la toolchain verrouillée `1.85.1`. En local, l’exécution manuelle dépend simplement de l’outillage installé.

## 2. Registre de décisions (ADR)

### Actées (2026-06-16)

| # | Décision | Pourquoi |
|---|---|---|
| 1 | **Pivot VAA** : l'unité jugée = `ÉnoncéVAA` adossé à un scrutin sélectionné (≠ loi promulguée) | règle le *reveal plat* par construction (filtrage par discriminance) |
| 2 | **Sélection hybride** : filtre mécanique → pool → curation éditoriale tracée + partenariat académique | la sélection devient le moat ; défendabilité = versioning + académique + faits auditables |
| 3 | **Vivier élargi + branche 49.3** : votes d'ensemble + amendements structurants + 1ʳᵉˢ parties de budget + textes/motions rejetés | récupère les budgets perdus et élargit les sorts observés ; la symétrie reste à prouver |
| 4 | **Abstention de l'élu exclue** du score + indicateur séparé | abstention AN polysémique ; toute valeur encoderait une interprétation contestable |
| 5 | **Agrégation par position majoritaire** du groupe | stable, indépendante de l'effectif (q7 §4.2) |
| 6 | **Plancher de dénominateur** `N_MIN = 10` | neutralise les faux 100 % à petit n (q7 §4.3) |
| 7 | **Arithmétique entière** (poids ×2, millièmes) | parité bit-à-bit WASM/Kotlin/Swift |
| 8 | **Modèle 3 couches** Faits (exhaustif) / VAA (curaté) / Citoyen (local-first) | sépare faits et éditorial ; préserve l'auditabilité |
| 9 | Hérité revue : `mise_au_point`→position rectifiée · `groupe_au_vote` · `Mandat`/`Affiliation` datés · `sans_avis`≠`passer` · `resume_version` · `phase` pré/post-reveal | survie au réel + RGPD art. 16 |

### Ouvertes (à trancher)

| Décision | Piste | À arbitrer avec |
|---|---|---|
| Cadence du reveal | par lot de 5 (revue) | — |
| Révision post-reveal | verrou par énoncé vs historique pré/post | — |
| `N_MIN`, seuil de discriminance (0,20), nb cible d'énoncés (~30-40) | défauts posés | partenariat académique |
| Taxonomie de thèmes FR | sous-ensemble EuroVoc (~15) | — |
| Nom public + dépôt INPI + domaines | « Boussole Politique » provisoire | juriste |
| Structure asso + financement | asso 1901 / fonds de dotation ; NLnet/NGI0 | juriste + fiscaliste |

## 3. Roadmap aval (ordonnée par dépendances)

**Immédiat — clôture du pivot VAA**
- **A.** ✅ **Confrontation du vivier élargi** : rapport Q8 reproductible sur leg 16+17. Volume,
  diversité adopté/rejeté et bidirectionnalité des groupes passent. Verdict global : **conditionnel**.
- **A1.** ⏳ **Fermer les sous-gates Q8** : faire relire les 5 overrides budgétaires proposés dans
  `dry-run/fixtures/vivier-link-overrides.json`, introduire un mapping thématique EuroVoc mesurable,
  définir la rubrique publique « amendement
  structurant », puis faire relire les seuils et le protocole de sélection indépendamment.

**Court terme — figer le cadre**
- **B.** 🟡 Spec **v1.0 consolidée + architecture** proposée dans `docs/` ; revue humaine et ADRs à faire
  avant de la déclarer normative.
- **C.** 🟡 **Charte de neutralité** proposée dans `docs/charte-neutralite.md` ; à éprouver sur un lot
  pilote et à faire relire.

**Construction (dépendances strictes)**
- **D.** **ETL Rust** : pipeline idempotent, fixtures par législature, property tests (proptest), fuzzing
  des parseurs → **artefacts statiques signés/reproductibles** ; axum en lecture seule seulement si un
  besoin de requête est ensuite démontré.
- **E.** **Couche Sélection VAA** : filtre mécanique + outil de curation versionné (dépend de D + comité
  académique).
- **F.** **Backlog éditorial** : résumés neutres des énoncés + **FALC** + glossaire (dépend de E).
- **G0.** 🟡 **Contrats Rust purs** : `domain` + `scoring`, arithmétique entière et tests d’or préparés.
  Les gates fmt/clippy/tests/build WASM sont prouvés en CI avec la toolchain verrouillée `1.85.1` ; la reprise locale reste dépendante de l’outillage installé. Ne pas
  prétendre que les trois profils réels sont recalculés tant que leurs entrées par énoncé manquent.
- **G.** **App web** : seulement après G0 validé, instancier le shell Dioxus 0.7, puis deck, reveal par
  lot, export/import, `storage.persist()` (Safari ITP) et RGAA AA.
- **H.** **Aucune analytics dans le MVP** ; miroir local éventuel, non bloquant, sans télémétrie —
  **divergences mises en avant** sans transformer le score en palmarès.
- **I.** **Providers LLM** (local → BYO-key → Clever) : grounding par article, citations ancrées, harness
  d'éval, `answer_grounded` async.
- **J.** **Mobiles** Kotlin/Swift via **UniFFI** + UnifiedPush.
- **K.** **Sync E2E** : spec de gestion de clés dédiée (dérivation, perte d'appareil, rotation).
- **L.** **Télémétrie DP** : flux A (comportemental) → C (méthodo) → B (insight, sous condition statistique
  + ε public).

**Transverse — avant toute mise en ligne publique**
- Association + directeur de publication (LCEN) + revue juridique : RGPD élus (art. 16/21 + 4ᵉ canal),
  AI Act art. 50 (avant niveaux LLM), régime des sondages (publication d'agrégats), marque/nom, fiscalité.
- **Comité scientifique / partenariat académique dès la phase méthodo** (= dès la Sélection, étape E).

## 4. Prochaine étape recommandée

**A1 — fermer les sous-gates Q8 avant toute sélection publique.** Commencer par les liens des premières
parties budgétaires, car ils sont factuels et bornés ; en parallèle, spécifier le mapping EuroVoc et la
rubrique « amendement structurant ». Le vivier cœur suffit en volume pour un pilote : ne pas ouvrir le
pool de 3 310 amendements filtrés tant que leur importance normative n'est pas définie.

En parallèle technique borné : faire relire humainement l’identité provisoire, puis rendre disponible la
toolchain Rust verrouillée et exécuter `scripts/check-rust.sh`. Aucun shell Dioxus métier ni serveur axum
avant fermeture de ces contrats.
