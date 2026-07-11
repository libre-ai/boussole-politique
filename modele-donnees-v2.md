# Modèle de données v2 — pivot VAA (Boussole Politique)

> Statut : conception arrêtée le 2026-06-16. Remplace le modèle v1 des specs v0.1 §3, invalidé au contact
> des données réelles par le dry-run (`dry-run/out/`). Documents jumeaux : `formule-congruence.md` (la
> formule), `vecteurs-test.json` (la spec exécutable). Sources confrontées : `dry-run/SCHEMA-NOTES.md`
> (pièges du schéma OpenData AN), `dry-run/scripts/anlib.py` (normalisation de référence),
> `revue-specs-2026-06-12.md` (la revue).

## Pourquoi v2

Le modèle v1 (`Loi` + vote de référence unique ; `position ∈ {pour,contre,abstention,absent}` ;
`SignalRejet` singulier ; périmètre « loi promulguée + scrutin public d'ensemble ») **ne survit pas au
réel** : « absent » n'existe pas dans la donnée AN, 22 % des textes ont une version votée ≠ promulguée,
0..6 motions de censure par texte, mandats multiples par circonscription, mises au point publiées par
l'AN. Et le périmètre est biaisé par construction (40 % des lois perdues, budgets/ratifications
effondrés, reveal plat).

**Décision** : repenser l'unité jugée *façon VAA* (Voting Advice Application) — l'unité n'est plus « la
loi promulguée » mais l'**énoncé** adossé à un **scrutin sélectionné** — et refonder le modèle pour la
réalité parlementaire.

## Principe directeur — la défendabilité est déplacée

Sélectionner des énoncés discriminants règle le *reveal plat* par construction (on filtre le bruit
unanime), **mais déplace tout le risque de neutralité sur la `Sélection`** — un acte éditorial qui
rapproche le projet de Datan (« scrutins choisis »). Conséquence, posée comme exigence de premier rang :

> La défendabilité ne repose plus sur l'exhaustivité mécanique, mais sur **(1)** un critère de sélection
> **versionné et justifié cas par cas**, **(2)** un **partenariat académique** légitimant la méthode,
> **(3)** une **couche faits qui reste exhaustive et auditable** sous la couche curatée.

## Vue d'ensemble — trois couches

```
COUCHE FAITS      exhaustive · dérivée mécaniquement · publique · auditable · jamais éditée à la main
  Scrutin · Vote · Texte · Élu · Mandat · AffiliationGroupe · Groupe · MotionCensure

COUCHE VAA        curatée · gouvernée par charte · versionnée            ← LE PIVOT
  ÉnoncéVAA (l'unité jugée) · Sélection (le critère, le moat déplacé)

COUCHE CITOYEN    local-first · jamais transmise en clair à nos serveurs
  PositionCitoyen
```

Notation : `?` = optionnel/nullable · `[]` = collection · `→` = référence · `{a|b}` = énumération.

---

## Couche FAITS

Source unique : OpenData AN (`data.assemblee-nationale.fr`). Règle de conflit : l'AN officielle
l'emporte, divergence loggée. Chaque enregistrement porte sa **provenance** (URL source + horodatage
d'ingestion + hash). Pipeline **idempotent** : entièrement re-dérivable, jamais retouché à la main.

### `Scrutin` — un vote nominatif

| Champ | Type | Source / dérivation |
|---|---|---|
| `id` | `(legislature, numero)` | `scrutin.legislature`, `scrutin.numero` |
| `date` | `Date` | `scrutin.dateScrutin` |
| `type` | `{SPO | SPS | MOC}` | `scrutin.typeVote.codeTypeVote` |
| `objet` | `String` | `scrutin.objet.libelle` (texte libre) |
| `lecture` | `Lecture?` | **dérivé** du suffixe de `objet` (« (première lecture) », « (texte de la CMP) », « (lecture définitive) »… cf. `anlib.parse_lecture`) |
| `sur_ensemble` | `bool` | **dérivé** : `objet` contient « l'ensemble » (`anlib.is_ensemble`) |
| `portee` | `{ensemble | premiere_partie | amendement | motion | autre}` | **dérivé** (cf. §Vivier) |
| `sort` | `{adopté | rejeté}` | `scrutin.sort.code` |
| `texte` | `→ Texte ?` | `scrutin.objet.dossierLegislatif.dossierRef` ; **souvent vide sur les votes d'ensemble** → fallback matching de titre (`anlib.link_scrutin`) |
| `decompte` | `{pour, contre, abstentions, nonVotants, nonVotantsVolontaires}` | `scrutin.syntheseVote.decompte` |
| `votants`, `exprimes`, `requis` | `int` | `scrutin.syntheseVote.*` |

> **Invariant** : `decompte.pour + decompte.contre == exprimes` ; réconciliation loggée si écart.
> **Tous** les scrutins sont chargés (pas seulement ceux d'ensemble) — c'est le vivier de la couche VAA.

### `Vote` — la position nominale d'un élu à un scrutin

| Champ | Type | Source / dérivation |
|---|---|---|
| `scrutin` | `→ Scrutin` | — |
| `elu` | `→ Élu` | `votant.acteurRef` (PA…) |
| `position` | `{pour | contre | abstention | nonvotant}` | bucket `decompteNominatif.{pours|contres|abstentions|nonVotants}` |
| `par_delegation` | `bool` | `votant.parDelegation` |
| `cause` | `String?` | `votant.causePositionVote` (pour les non-votants) |
| `groupe_au_vote` | `→ Groupe` | `ventilationVotes…groupe.organeRef` — **le groupe au moment du vote** ⭐ |
| `mise_au_point` | `{position_rectifiee}?` | champ structuré `scrutin.miseAuPoint` — correction publiée par l'AN ⭐ |

> **Règles** : le score utilise la **position rectifiée** si une mise au point existe ; l'UI affiche les
> deux (évite une demande de rectification RGPD art. 16 sur un fait que l'AN a elle-même corrigé).
> Le `groupe_au_vote` est la source autoritative de l'affiliation datée — *gratuite*, fournie par la
> ventilation, jamais l'affiliation courante.

### `Texte` — le dossier législatif

| Champ | Type | Source / dérivation |
|---|---|---|
| `uid` | `String` | `dossierParlementaire.uid` (DLR…) |
| `titre` | `String` | `titreDossier.titre` |
| `procedure` | `String` | `procedureParlementaire.libelle` (détermine `is_loi`, `is_ratification`) |
| `actes` | `Acte[]` | arbre récursif `actesLegislatifs` (codeActe : `AN1`, `CMP`, `ANLDEF`, `PROM`, `CC-SAISIE`…) |
| `statut` | `{en_cours | promulgué | rejeté | censuré}` | **dérivé** : présence acte `PROM` ; saisine/décision CC |
| `decision_cc` | `{url, articles_censures[], version_diffère}?` | acte `CC-SAISIE`/`CC-DEC` ⭐ |
| `version_drift` | `bool` | **dérivé** : le scrutin de réf n'est pas la dernière lecture (CMP/NLEC postérieure) ⭐ |

### `Élu` · `Mandat` · `AffiliationGroupe` · `Groupe`

| Entité | Champs | Source |
|---|---|---|
| `Élu` | `pa_uid`, `nom?`, `prenom?` | `acteur` AMO10 — **nom nullable** : les députés partis (démission, ministre, partielle) ne sont pas dans le dump des actifs → `PA…` sans nom, mais leurs votes/groupe restent présents (trou AMO10 : 9,4 % leg17, 35,9 % leg16) |
| `Mandat` ⭐ | `elu →`, `circonscription`, `debut`, `fin?`, `cause_fin?` | mandats `typeOrgane = ASSEMBLEE`, datés — une circonscription = **une chronologie de titulaires** |
| `AffiliationGroupe` ⭐ | `elu →`, `groupe →`, `debut`, `fin?` | mandats `typeOrgane = GP`, datés (recoupe `Vote.groupe_au_vote`) |
| `Groupe` | `po_uid`, `libelle`, `abrev`, `legislature` | `organe` `codeType = GP` |

### `MotionCensure` ⭐ — 0..n par texte

| Champ | Type | Note |
|---|---|---|
| `texte` | `→ Texte ?` | rattachée via 49.3 ; une 49.2 (spontanée) n'a pas de texte |
| `lecture` | `Lecture?` | plusieurs engagements possibles par texte (un par lecture) |
| `type` | `{art_49_2 | art_49_3}` | **dérivé** du titre (« article 49, alinéa 2/3 ») |
| `sort` | `{adopté | rejeté}` | censure **adoptée** ⇒ texte tombé (hors corpus jugeable) |
| `votants_pour` | `→ Élu[]` | qui a voté la censure (fait vérifiable) |

> Le modèle v1 (`motion_censure_url` singulier) est **faux** : réalité 0..6 motions par texte, plusieurs
> le même jour (PLF 2026 : 6 motions). Signal = « a voté la censure » ; **jamais** d'inférence « les
> autres soutenaient le texte ». Hors score principal.

---

## Couche VAA / ÉDITORIALE — le pivot

### `ÉnoncéVAA` — l'unité que le citoyen juge

| Champ | Type | Note |
|---|---|---|
| `id` | `String` | identifiant stable de l'énoncé |
| `scrutin` | `→ Scrutin` | le « vote-clé » sélectionné |
| `resume_neutre` | `→ ResumeVersion` | couche éditoriale, **versionné**, gouverné par la charte |
| `themes` | `→ Theme[]` | taxonomie FR (paramètre ouvert) |
| `polarite` | `{pour = +1 | pour = -1}` | sens du « pour » pour l'orientation citoyenne (rare : un « pour » qui *supprime* un dispositif) |
| `caveat_version` | `bool` | vrai si le texte promulgué diffère du texte voté (`Scrutin → Texte.version_drift`/`decision_cc`) → caveat obligatoire affiché |

`ResumeVersion` : `{texte, version, date, auteur, sources[], statut ∈ {brouillon|publié|contesté}}`.

### `Sélection` — le critère, versionné (le moat déplacé)

| Champ | Type | Note |
|---|---|---|
| `version` | `SemVer` | publiée, immuable, signée |
| `enonces` | `EntreeSelection[]` | le jeu actif |
| `EntreeSelection` | `{scrutin →, statut, critere, justification}` | par énoncé |
| `statut` | `{pool_auto | curé | écarté}` | filtre mécanique vs décision éditoriale vs rejet tracé |
| `critere` | `{discriminance, participation, themes[], importance}` | mesuré + motivé |

> La `Sélection` **absorbe le `vote_reference_override`** de la revue : choisir explicitement quel
> scrutin devient un énoncé *est* l'override généralisé — mais tracé, justifié, gouverné, jamais une
> retouche silencieuse des faits.

---

## Couche CITOYEN (local-first)

### `PositionCitoyen`

| Champ | Type | Note |
|---|---|---|
| `enonce` | `→ ÉnoncéVAA` | — |
| `valeur` | `{-2 | -1 | +1 | +2 | sans_avis | passer}` | `sans_avis` (définitif, entre dans le flux C) ≠ `passer` (juger plus tard) ⭐ |
| `resume_version` | `String` | la version du résumé jugée ⭐ → « ce résumé a changé depuis ton avis » |
| `horodatage_local` | `DateTime` | jamais transmis par défaut |
| `phase` | `{pré_reveal | post_reveal}` | ⭐ permet le score « à froid » sur les positions pré-reveal |

> **Invariant d'or** (reformulé honnêtement, cf. revue §2.3.3) : aucune position individuelle ne parvient
> *en clair* à *nos* serveurs ; rien d'individuel ne sort sans acte explicite de l'utilisateur. Le
> BYO-key (LLM) est une **exception explicite** à étiqueter, pas un cas compatible.

---

## Règles de dérivation délicates

- **`absent` n'est pas un champ** : c'est une **dérivation** `sièges(577) − (votants + nonVotants
  déclarés) − sièges_vacants`, marquée explicitement *estimée et fragile* (trou AMO10). Jamais affirmée
  sur un nommé sans réserve. Alimente l'indicateur « participation », pas le score.
- **`version_drift` / `decision_cc`** : déclencheur = **promulgation** (acte `PROM`), pas « adoption ».
  Si le texte promulgué diffère (CMP réécrite, censure CC partielle — ex. loi immigration, décision
  n° 2023-863 DC : ~30 articles censurés), `caveat_version = true`.
- **Précédence multi-scrutins** (règle écrite, déterministe) : un scrutin public d'ensemble sur la
  **version finale** prime sur un 49.3 antérieur ; un 49.3 **terminal** prime sur un scrutin d'une
  version antérieure.
- **Navette** : plusieurs lectures → un seul `Texte` ; le scrutin de réf d'un énoncé est explicité par la
  `Sélection`, pas deviné.
- **Ratifications** : exclues *seulement* si sans scrutin public ; une ratification avec scrutin public
  (type CETA) est éligible au vivier.
- **Lois omnibus** : badge « multi-volets », volets énumérés sans hiérarchie ; congruence par volet
  impossible (le vote AN est global) — limite assumée et affichée.

---

## Couche Sélection — critère hybride + vivier élargi

### Vivier (couche faits, élargi)

Au-delà des seuls votes d'ensemble. `Scrutin.portee` route chaque scrutin :

| Portée | Détection | Éligible au vivier |
|---|---|---|
| `ensemble` | `objet` contient « l'ensemble » | oui |
| `premiere_partie` | `objet` contient « première partie » (budgets) | oui — récupère les PLF/PLFSS perdus au 49.3 |
| `amendement` | `objet.dossierLegislatif` peuplé, hors ensemble | oui si **structurant** (curation) |
| `motion` | type `MOC` | oui — branche 49.3 comme signal factuel |
| `autre` | résolutions art. 34-1… | non (pas une loi) |

### Pipeline de sélection (hybride)

1. **Filtre mécanique** → pool éligible : discriminance (`part_minorité = min(pour,contre)/exprimés ≥
   seuil`, défaut 0,20, le seuil « discriminant » de q2), participation ≥ seuil, couverture thématique.
   Reproductible, publié.
2. **Curation éditoriale** dans le pool : justifiée cas par cas, versionnée, visant la couverture des
   clivages et la **symétrie gauche/droite** (inclure des votes *rejetés* / propositions d'opposition
   pour casser le biais pro-majorité), adossée au **partenariat académique**.
3. **Branche 49.3** : traitée comme signal factuel hors score (qui a voté la censure), pour ne pas perdre
   les budgets structurants.
4. **Angle mort assumé** : la congruence ne sépare pas le bloc de gouvernement (DEM≈EPR≈HOR≈DR à
   89-97 %) — communiqué, jamais survendu.

---

## Couverture des cas réels (preuve de complétude)

| Cas réel (revue / dry-run) | Traitement v2 |
|---|---|
| CMP réécrite / censure CC (22 %) | `Texte.version_drift` + `decision_cc` + `ÉnoncéVAA.caveat_version` |
| « absent » inexistant | dérivation explicite + indicateur « participation », jamais affirmé sur un nommé |
| 0..n motions de censure | `MotionCensure` multiple ; censure adoptée ⇒ hors corpus |
| Mandats multiples / changements de groupe | `Mandat` + `AffiliationGroupe` datés ; `Vote.groupe_au_vote` |
| Mises au point | `Vote.mise_au_point` → score sur position rectifiée |
| Budgets au 49.3 perdus | vivier `premiere_partie` + branche 49.3 signal |
| Reveal plat (q2) | sélection par discriminance (filtre le bruit unanime) |
| Faux 100 % à petit n (q7) | plancher `N_MIN` (cf. `formule-congruence.md`) |
| Biais pro-majorité (q7) | curation incluant votes rejetés / opposition |
| Centre-droit indiscernable (q7) | assumé + communiqué |
| Résumé corrigé après jugement | `PositionCitoyen.resume_version` |
| Safari ITP / perte locale | export/import + `storage.persist()` (couche app, hors modèle) |

---

## Vérification (état au 2026-06-16)

- ✅ **Formule** : réimplémentée en arithmétique entière (`dry-run/scripts/formule_v2.py`), **parité
  exacte** float↔int et **cohérence** avec les chiffres publiés du dry-run sur 3 profils réels
  (Panot/Le Pen/Ciotti). 10 cas synthétiques, dont la polarité inversée, + 3 cas réels figés dans
  `vecteurs-test.json`.
- ⏳ **Re-dérivation idempotente** : la couche faits doit re-dériver le corpus dry-run (159 lois) à
  l'identique — acquis pour le périmètre v1 (`q1 match=true`) ; à re-vérifier sur le vivier élargi à
  l'implémentation de l'ETL Rust.
- ⏳ **Confrontation du vivier élargi** : passer `portee` sur leg 16+17, vérifier que le pool de sélection
  est non vide, thématiquement couvrant et symétrique — chantier ETL.

## Paramètres ouverts

| Paramètre | Défaut | À arbitrer avec |
|---|---|---|
| `N_MIN` (plancher) | 10 | partenariat académique |
| seuil de discriminance | 0,20 | id. |
| taxonomie de thèmes FR | — | sous-ensemble EuroVoc (~15 thèmes) |
| nombre cible d'énoncés actifs | ~30-40 | méthodo VAA (Wahl-O-Mat ≈ 38) |

## Hors périmètre de ce chantier (séquence aval)

Spec v1.0 consolidée + ADR · charte de neutralité autonome · ETL Rust + dataset signé · app web WASM ·
niveau 0 analytics · LLM grounded · mobiles UniFFI · sync E2E · télémétrie DP. Transverse avant mise en
ligne : association + directeur de publication + revue juridique (RGPD élus, AI Act, marque/nom).
