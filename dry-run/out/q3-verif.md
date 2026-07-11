# q3-verif — vérification adverse INDÉPENDANTE du chiffre-clé « décalage version votée / promulguée »

**Verdict : le chiffre-clé CONCORDE. `union = 35/159 (22,0 %)`, leg 16 = 27/93 (29,0 %), leg 17 = 8/66 (12,1 %).**
Recalculé from scratch, sans réutiliser `scripts/q3-version.py`, en parsant moi-même les **dossiers bruts**
(`data/dossiers-1{6,7}/.../DLR*.json`) et les **scrutins bruts**. Script : `scripts/q3-verif.py` · machine : `out/q3-verif.json`.

Méthode indépendante :
- **Périmètre** : consommé du corpus figé `out/corpus.json` (159 lois, `ref_acte`/`ref_numero`/`ref_leg`/`has_cmp`/`saisine_cc`).
- **Axe (a) censure CC** : je marche moi-même l'arbre `actesLegislatifs` (récursif, wrapper `acteLegislatif`, `as_list`) et compte les nœuds `CC-CONCLUSION` dont `statutConclusion.fam_code == TCD02` (« Partiellement conforme »).
- **Axe (drift)** : je calcule le rang de la dernière décision **AN** présente dans le dossier (`AN1<AN2<AN3<CMP-DEBATS-AN-DEC<ANNLEC<ANLDEF`) et le compare au rang du `ref_acte`. Drift = une décision AN de rang strictement supérieur existe.
- **Union** = (a) ∪ (drift). Dénominateurs : 159 / 93 / 66, split par `ref_leg`.

---

## Tableau de concordance

| Mesure | **Moi (indépendant)** | Analyse | Concorde |
|---|---:|---:|:---:|
| corpus_total | 159 | 159 | ✅ |
| leg16_n / leg17_n | 93 / 66 | 93 / 66 | ✅ |
| saisine_cc (tot / 16 / 17) | 45 / 22 / 23 | 45 / 22 / 23 | ✅ |
| **cc_censure_partielle (TCD02)** | **19 / 12 / 7** | **19 / 12 / 7** | ✅ |
| cc_conforme (TCD01) | 21 | 21 | ✅ |
| cc_conforme_avec_reserve (TCD03) | 4 | 4 | ✅ |
| cc_saisine_sans_conclusion | 1 | 1 | ✅ |
| **drift_lecture_posterieure** | **20 / 18 / 2** | **20 / 18 / 2** | ✅ |
| drift_cmp_ref_1ʳᵉ_lecture (b littéral) | 23 | 23 | ✅ |
| version_drift_flag_corpus | 0 | 0 | ✅ |
| **UNION texte jugé ≠ promulgué** | **35 / 27 / 8** | **35 / 27 / 8** | ✅ |
| union_frac (tot / 16 / 17) | 0.2201 / 0.2903 / 0.1212 | idem | ✅ |
| overlap (censure ∧ drift) | 4 | 4 | ✅ |
| seul_censure / seul_drift | 15 / 16 | 15 / 16 | ✅ |
| immigration_2024 dans corpus | False | False | ✅ |
| drift_prouve_par_scrutin_non_lie | **16** | **18** | ⚠️ écart (métrique secondaire) |

Décomposition arithmétique vérifiée indépendamment, **aucun double-compte** :
`union(35) = seul_censure(15) + seul_drift(16) + overlap(4)` ;
`censure(19) = 15 + overlap(4)` ; `drift(20) = 16 + overlap(4)` ; `27 + 8 = 35`.
Les pourcentages tombent EXACTEMENT : `35/159 = 22,01 %`, `27/93 = 29,03 %`, `8/66 = 12,12 %`.

---

## ⚠️ LE PIÈGE QUE J'AI TROUVÉ (et qui n'invalide PAS l'analyse)

Mon **premier** run donnait `censure=16`, `drift=18`, **`union=31`** — un écart de **−4** vs l'analyse. Cause : un piège
de données réel.

**24 dossiers du corpus existent en DOUBLE** : une copie dans `data/dossiers-16/.../` ET une dans `data/dossiers-17/.../`.
Ce sont des textes commencés en leg 16 et achevés/votés/jugés en leg 17 (UID préfixe `L16` mais `ref_leg=17` pour 13 d'entre eux).
**Pour les 24, la copie leg-17 est le snapshot RÉCENT et COMPLET ; la copie leg-16 est figée/tronquée** (elle ne contient pas
la `CC-CONCLUSION` postérieure ni la dernière décision de lecture). Exemple `DLR5L16N49868` (simplification vie économique) :
copie leg-16 = 3 402 caractères, **0** `CC-CONCLUSION` ; copie leg-17 = 27 437 caractères, **1** `CC-CONCLUSION` TCD02 (2026-903 DC).

Mon loader naïf prenait `dossiers-16` en premier → il **ratait** 3 censures TCD02 (`DLR5L16N49726` souveraineté agricole 2025-876,
`DLR5L16N49176` sûreté transports 2025-878, `DLR5L16N49868` simplification vie éco 2026-903) et 2 drifts.
**Correctif** : quand un UID existe dans les deux répertoires, prendre **le fichier le plus gros** (= le plus complet).
Après correction → `censure=19`, `drift=20`, `union=35`. **Concordance parfaite.**

> Leçon adverse : l'analyse via `anlib.load_all_dossiers()` a, elle, chargé la bonne copie (la plus récente) — son 35 est juste.
> Le risque inverse aurait été un faux écart de MA part. Je le documente pour que le correctif soit reproductible.

---

## Axe (a) — 19 censures partielles, recalculées du brut (TCD02)

`statutConclusion.fam_code` dans les 40 `CC-CONCLUSION` du corpus : **TCD01=21 (conforme), TCD02=19 (partiel), TCD03=4 (réserve)**.
Les 19 TCD02 (mes nœuds bruts, `numDecision`/`anneeDecision` lus directement) :

| Leg | Décision DC | Loi (titre tronqué) |
|---|---|---|
| 16 | 2022-843 | Mesures d'urgence protection du pouvoir d'achat |
| 16 | 2023-848 | Accélération production d'énergies renouvelables |
| 16 | 2023-850 | Jeux Olympiques et Paralympiques de 2024 |
| 16 | 2023-851 | Accélération procédures construction (nucléaire) |
| 16 | 2023-853 | Protéger les logements contre l'occupation illicite |
| 16 | 2023-854 | Programmation militaire 2024-2030 |
| 16 | 2023-855 | Orientation et programmation de la justice 2023-2027 |
| 16 | 2023-856 | Ouverture/modernisation du corps judiciaire |
| 16 | 2023-858 | Pour le plein emploi |
| 16 | 2024-865 | Lutte contre les dérives sectaires |
| 16 | 2024-866 | Sécuriser et réguler l'espace numérique (SREN) |
| 16 | 2025-876 | **Souveraineté agricole** *(manquée au 1ᵉʳ run — piège doublon)* |
| 17 | 2025-878 | **Renforcement sûreté transports** *(idem)* |
| 17 | 2025-885 | Sortir la France du piège du narcotrafic |
| 17 | 2025-886 | Restaurer l'autorité de la justice / mineurs |
| 17 | 2025-887 | Contre toutes les fraudes aux aides publiques |
| 17 | 2025-896 | Simplification du droit de l'urbanisme et du logement |
| 17 | 2025-899 | PLFSS pour 2026 |
| 17 | 2026-903 | **Simplification de la vie économique** *(idem)* |

Identique (set + décisions) au tableau de `q3-version.md`. La « 1 saisine sans conclusion » = *Prévenir les ingérences
étrangères* (leg 16, `CC-SAISIE-AN` sans `CC-CONCLUSION`) — confirmée, comptée en saisine, pas en censure.

---

## Axe (drift) — 20 lois, recalculé par rang d'acte AN

Mes 20 (18 leg 16 + 2 leg 17) ont toutes `ref_acte = AN1-DEBATS-DEC` mais portent une décision AN postérieure :
**18 via `CMP-DEBATS-AN-DEC`**, **1 via `AN2-DEBATS-DEC`** (*Protéger la population des risques substances* = vapotage,
réf 1ʳᵉ lecture mais 2ᵉ lecture AN existe), **1 leg 17** (*Restitution de biens culturels* + *fraudes aux aides*).
Set identique à l'analyse.

**Overlap censure ∧ drift = 4** (set identique au JSON de l'analyse) :
*Mesures d'urgence pouvoir d'achat*, *SREN*, *Souveraineté agricole*, *Contre toutes les fraudes aux aides publiques*.

> Note : le **texte en prose** de `q3-version.md` (« JO Paris 2024, loi justice 2023-2027, plein emploi, énergies
> renouvelables ») cite **4 exemples qui ne sont PAS le vrai set d'overlap** — ces 4 sont censurées **mais pas driftées**
> (ref_acte = CMP, donc pas de lecture AN postérieure). C'est une **bavure de rédaction**, pas une erreur de chiffre : le
> nombre 4 est correct, et son propre `q3-version.json` liste bien le vrai set (identique au mien). Aucun impact sur 35.

---

## Le seul écart : `drift_prouve_par_scrutin_non_lie` (moi 16 vs analyse 18) — métrique SECONDAIRE

Cet indicateur n'entre **pas** dans le calcul de l'union : le drift est établi structurellement par l'arbre d'actes (20),
le scrutin CMP non lié n'est qu'une **corroboration**. Mon matcher (date exacte de `CMP-DEBATS-AN-DEC` + marqueur « commission
mixte paritaire » + ≥ 2 tokens de titre communs) en trouve 16 ; l'analyse en trouve 18. Les **2 que je rate sont de VRAIS
scrutins CMP** — vérifiés à la main :

- n° **2282** (2023-07-13) « *…restitution des biens culturels…spoliations…persécutions antisémites…* (texte de la CMP) »
- n° **2255** (2023-07-12) « *…renforcer la protection des familles d'enfants atteints d'une maladie…* (texte de la CMP) »

Donc **l'analyse a raison (18)** et c'est MON heuristique qui sous-compte (tokens trop filtrés / clé de date). Cet écart
joue **en faveur** de l'analyse, pas contre. Je ne corrige pas mon matcher : il a rempli son rôle (montrer que ≥ 16/20
drifts sont prouvables par un scrutin réel non rattaché).

---

## « 22 % est un plancher » — vérifié

Loi n° 2024-42 « **pour contrôler l'immigration, améliorer l'intégration** » (`DLR5L16N47118`) :
**promulguée** (actes `PROM`+`PROM-PUB` présents ✓), **`CC-CONCLUSION` = TCD02 décision 2023-863 DC** (✓, lue dans le brut),
**MAIS absente du corpus** (✓ vérifié). Le cas de drift le plus emblématique est bien exclu par des `voteRefs` AN nuls →
le 22 % est un minorant honnête.

---

## Conclusion

Le chiffre-clé **`35/159 (22,0 %)`, leg 16 = 27/93 (29,0 %), leg 17 = 8/66 (12,1 %)** est **exact et reproductible** par une
méthode totalement indépendante (parsing brut des dossiers + comparaison de rang d'actes). Décomposition cohérente, pas de
double-compte, dénominateurs corrects, apostrophes/objet-vs-tableau gérés. **Concordance : haute.**

Réserves (mineures, n'affectant pas le chiffre) :
1. **Bavure de prose** dans `q3-version.md` : les 4 exemples d'overlap nommés en clair sont faux (censurées non driftées) ;
   le nombre 4 et le set réel (dans le JSON) sont justes.
2. Mon `drift_prouve` = 16 < 18 de l'analyse : écart d'**heuristique de matching**, l'analyse étant la plus juste.
3. **Piège data doublon dossiers-16/17** : 24 dossiers en double, copie leg-17 = la bonne. À tout pipeline futur de prendre
   la copie la plus complète sous peine de sous-compter censures et drifts (j'ai perdu 4 d'union avant correction).
4. La définition « différent » mesure l'**existence** d'un écart texte voté/promulgué, pas son ampleur (limite déjà
   honnêtement posée par l'analyse).
