# Q2 — Participation & polarisation des votes de référence

**Mandat :** tester le §4 de la revue — le « reveal plat » (risque épistémique n°1). Si une grande part des 159 votes de référence sont quasi-unanimes, un score de congruence calculé dessus rendra ~la même valeur pour TOUS les groupes : un reveal qui n'apprend rien. On le mesure.

Corpus : **159 votes de référence** (1 par loi promulguée jugeable), leg 16 = 93, leg 17 = 66. Source : `out/corpus.json` (figé).

## TL;DR — le verdict

- **80/159 votes de référence (50.3%) sont quasi-unanimes** (minorité < 10% des exprimés). Seulement **54 (34.0%) sont discriminants** (minorité ≥ 20%).
- Marge gagnante médiane = **0.806** (|pour−contre|/exprimés). Part minorité médiane = **0.097**.
- Participation médiane = **154 votants/577** (26.7%) ; exprimés médian = **141/577** (24.4%).
- **La prédiction du §4 se vérifie au chiffre près** : un score de congruence calculé sur les **159 votes de réf** donne une moyenne inter-groupes de **0.82** avec **6/9 groupes au-dessus de 80%** (et 8/9 au-dessus de 60%). Tout le monde « congrue » à ~80% : reveal qui n'apprend rien.
- **Pourquoi : c'est mécanique.** Sur les votes quasi-unanimes l'écart de score entre groupes majeurs n'est que de **0.081** (min 0.9189, max 1.0 — tous collés). Sur les discriminants il explose à **0.962** (min 0.0385, max 1.0). Comme la moitié des votes de réf sont quasi-unanimes, ils noient le signal des discriminants.

> **Implication produit :** un score de congruence agrégé sur les 159 votes de référence donnera ~80-95% pour quasi tous les groupes et n'aura aucun pouvoir discriminant. Le signal exploitable se concentre sur les **54 votes discriminants** (et un peu sur les intermédiaires). Il faut pondérer/filtrer par polarisation, sinon le reveal est cosmétique.

## 1. Distribution de la polarisation (classes)

Classe selon la part de la minorité dans les exprimés : quasi-unanime `< 10%`, intermédiaire `[10%, 20%)`, discriminant `≥ 20%`.

| Périmètre | n | quasi-unanime | intermédiaire | discriminant |
|---|--:|--:|--:|--:|
| global | 159 | 80 (50.3%) | 25 (15.7%) | 54 (34.0%) |
| leg16 | 93 | 51 (54.8%) | 14 (15.1%) | 28 (30.1%) |
| leg17 | 66 | 29 (43.9%) | 11 (16.7%) | 26 (39.4%) |
| global_sans_ratif | 151 | 75 (49.7%) | 25 (16.6%) | 51 (33.8%) |
| ratifications | 8 | 5 (62.5%) | 0 (0.0%) | 3 (37.5%) |

Lecture : leg 16 (close) = **54.8%** quasi-unanimes vs leg 17 (en cours) = **43.9%**. Les 8 ratifications sont quasi-unanimes à 62.5% — elles gonflent mécaniquement le taux.

## 2. Participation

`votants` = pour+contre+abst (présents qui votent) ; `exprimés` = pour+contre. Dénominateur = 577 sièges.

| Périmètre | votants médian | % 577 | votants moyen | exprimés médian | % 577 |
|---|--:|--:|--:|--:|--:|
| global | 154 | 26.7% | 227 | 141 | 24.4% |
| leg16 | 145 | 25.1% | 196 | 125 | 21.7% |
| leg17 | 184 | 31.9% | 270 | 165 | 28.6% |

Quantiles de la participation (`votants/577`) :

| Périmètre | p0 | p10 | p25 | p50 | p75 | p90 | p100 |
|---|--:|--:|--:|--:|--:|--:|--:|
| global | 6% | 12% | 18% | 27% | 59% | 91% | 99% |
| leg16 | 6% | 12% | 17% | 25% | 40% | 74% | 99% |
| leg17 | 7% | 15% | 19% | 32% | 86% | 92% | 99% |

Participation très variable : de quelques dizaines de votants (textes consensuels votés en séance creuse) à >500 (scrutins solennels mobilisés).

## 3. Histogramme de la marge gagnante

Marge gagnante = `|pour − contre| / exprimés`. **1.0 = unanime**, **0.0 = 50/50 parfait**. Bins de largeur 0.1.

| bin marge | global | leg16 | leg17 |          |
|---|--:|--:|--:|---|
| [0.0, 0.1) | 9 | 4 | 5 | ##### |
| [0.1, 0.2) | 5 | 4 | 1 | ### |
| [0.2, 0.3) | 7 | 2 | 5 | #### |
| [0.3, 0.4) | 6 | 3 | 3 | ### |
| [0.4, 0.5) | 14 | 8 | 6 | ####### |
| [0.5, 0.6) | 11 | 6 | 5 | ###### |
| [0.6, 0.7) | 14 | 8 | 6 | ####### |
| [0.7, 0.8) | 13 | 7 | 6 | ####### |
| [0.8, 0.9) | 5 | 5 | 0 | ### |
| [0.9, 1.0] | 75 | 46 | 29 | ######################################## |

La masse est écrasée vers la droite (marge ≥ 0.8) : la grande majorité des lois promulguées passent par des votes larges. Le bas du spectre (marge < 0.2, votes serrés) est clairsemé.

Histogramme de la part de la minorité (`min(pour,contre)/exprimés`, miroir) :

| bin part minorité | global | leg16 | leg17 |          |
|---|--:|--:|--:|---|
| [0.0, 0.1) | 80 | 51 | 29 | ######################################## |
| [0.1, 0.2) | 25 | 14 | 11 | ############ |
| [0.2, 0.3) | 26 | 15 | 11 | ############# |
| [0.3, 0.4) | 12 | 4 | 8 | ###### |
| [0.4, 0.5) | 16 | 9 | 7 | ######## |
| [0.5, 0.6) | 0 | 0 | 0 |  |
| [0.6, 0.7) | 0 | 0 | 0 |  |
| [0.7, 0.8) | 0 | 0 | 0 |  |
| [0.8, 0.9) | 0 | 0 | 0 |  |
| [0.9, 1.0] | 0 | 0 | 0 |  |

## 4. Test du « reveal plat » (le cœur du §4)

Pour chaque vote, on calcule par groupe un **score de congruence binaire** : la position majoritaire du groupe (pour vs contre) coïncide-t-elle avec le sort de la loi (adopté→pour attendu, rejeté→contre attendu) ? On agrège par groupe (part de votes congruents) puis on mesure la **dispersion inter-groupes**. Groupes « majeurs » = présents avec un pour/contre sur ≥ 50% des votes du sous-ensemble.

| Sous-ensemble | n votes | groupes majeurs | score min | score max | **spread (max−min)** | écart-type |
|---|--:|--:|--:|--:|--:|--:|
| quasi_unanime_global | 80 | 9 | 0.9189 | 1.0 | **0.0811** | 0.027 |
| discriminant_global | 54 | 8 | 0.0385 | 1.0 | **0.9615** | 0.3923 |
| tous_global | 159 | 9 | 0.4545 | 1.0 | **0.5455** | 0.1876 |
| quasi_unanime_leg16 | 51 | 11 | 0.9189 | 1.0 | **0.0811** | 0.0255 |
| discriminant_leg16 | 28 | 11 | 0.0385 | 1.0 | **0.9615** | 0.3372 |
| tous_leg16 | 93 | 11 | 0.4545 | 1.0 | **0.5455** | 0.1701 |
| quasi_unanime_leg17 | 29 | 12 | 0.9412 | 1.0 | **0.0588** | 0.0212 |
| discriminant_leg17 | 26 | 12 | 0.12 | 1.0 | **0.88** | 0.3309 |
| tous_leg17 | 66 | 12 | 0.431 | 1.0 | **0.569** | 0.1768 |

**Lecture décisive :** sur les votes quasi-unanimes le spread inter-groupes est ~quasi nul (global 0.0811), c.-à-d. tous les groupes scorent pareil — le reveal n'apprend rien. Sur les votes discriminants le spread explose (global 0.9615) : c'est là, et seulement là, que les groupes se séparent. Comme 50.3% des votes de réf sont quasi-unanimes, le score agrégé brut est dominé par du bruit unanime.

Scores de congruence par groupe, **par législature** (les codes de groupe diffèrent entre leg16 `PO8005xx` et leg17 `PO845xxx` ; on ne les mélange pas). On compare DISCRIMINANT (signal) vs QUASI-UNANIME (bruit).

### Leg 16

DISCRIMINANT — là où les groupes se séparent :

- DEM (PO800484) : **1.000**
- RE (PO800538) : **1.000**
- HOR (PO800514) : **1.000**
- LR (PO800508) : **0.852**
- GAUCHE?~22 (PO800532) : **0.696**
- NI (PO793087) : **0.571**
- SOC? (PO800496) : **0.500**
- RN (PO800520) : **0.500**
- GDR (PO800526) : **0.174**
- LIOT (PO800502) : **0.174**
- LFI-NUPES (PO800490) : **0.038**

QUASI-UNANIME — tous collés en haut (reveal plat) :

- SOC? (PO800496) : 1.000
- GDR (PO800526) : 1.000
- RE (PO800538) : 1.000
- LR (PO800508) : 1.000
- HOR (PO800514) : 1.000
- GAUCHE?~22 (PO800532) : 1.000
- DEM (PO800484) : 0.980
- RN (PO800520) : 0.977
- NI (PO793087) : 0.967
- LIOT (PO800502) : 0.951
- LFI-NUPES (PO800490) : 0.919

### Leg 17

DISCRIMINANT :

- NI (PO840056) : **1.000**
- DEM (PO845454) : **1.000**
- EPR (PO845407) : **0.962**
- HOR (PO845470) : **0.962**
- DR (PO845425) : **0.880**
- LIOT (PO845485) : **0.800**
- RN (PO845401) : **0.708**
- UDR?~16 (PO847173) : **0.692**
- SOC (PO845419) : **0.565**
- GDR (PO845514) : **0.167**
- ECOS (PO845439) : **0.125**
- LFI-NFP (PO845413) : **0.120**

QUASI-UNANIME :

- SOC (PO845419) : 1.000
- RN (PO845401) : 1.000
- LIOT (PO845485) : 1.000
- NI (PO840056) : 1.000
- GDR (PO845514) : 1.000
- DR (PO845425) : 1.000
- DEM (PO845454) : 1.000
- ECOS (PO845439) : 1.000
- EPR (PO845407) : 0.966
- HOR (PO845470) : 0.966
- LFI-NFP (PO845413) : 0.955
- UDR?~16 (PO847173) : 0.941

## 5. Les 10 votes de référence les plus serrés

| # | leg | scrutin | type | date | sort | pour | contre | abst | exprimés | part minorité | titre |
|--:|--:|--:|---|---|---|--:|--:|--:|--:|--:|---|
| 1 | 17 | 4442 | SPS | 2025-12-02 | adopté | 217 | 213 | 84 | 430 | 49.5% | Projet de loi de finances de fin de gestion pour 2025 |
| 2 | 17 | 4758 | SPS | 2025-12-16 | adopté | 247 | 232 | 90 | 479 | 48.4% | Projet de loi de financement de la sécurité sociale pour 2026 |
| 3 | 16 | 3709 | SPO | 2024-04-30 | adopté | 38 | 34 | 0 | 72 | 47.2% | Confidentialité des consultations des juristes d’entreprise |
| 4 | 17 | 3182 | SPS | 2025-10-28 | adopté | 279 | 247 | 9 | 526 | 47.0% | Proposition de loi organique visant à reporter le renouvellement génér… |
| 5 | 17 | 1304 | SPS | 2025-04-07 | adopté | 204 | 180 | 24 | 384 | 46.9% | Proposition de loi organique visant à harmoniser le mode de scrutin au… |
| 6 | 17 | 1303 | SPS | 2025-04-07 | adopté | 206 | 181 | 25 | 387 | 46.8% | Renforcement de la parité dans les fonctions électives et exécutives d… |
| 7 | 16 | 3370 | SPO | 2024-02-14 | adopté | 64 | 55 | 1 | 119 | 46.2% | Faciliter la mise à disposition aux régions du réseau routier national… |
| 8 | 16 | 3966 | SPS | 2024-05-28 | adopté | 272 | 232 | 65 | 504 | 46.0% | Souveraineté en matière agricole et renouvellement des générations en … |
| 9 | 16 | 15 | SPO | 2022-07-12 | adopté | 221 | 187 | 24 | 408 | 45.8% | Maintien provisoire d'un dispositif de veille et de sécurité sanitaire… |
| 10 | 17 | 6184 | SPS | 2026-04-14 | adopté | 275 | 225 | 30 | 500 | 45.0% | Projet de loi de simplification de la vie économique |

## 6. Les 10 votes de référence les plus unanimes

| # | leg | scrutin | type | date | pour | contre | abst | exprimés | part minorité | titre |
|--:|--:|--:|---|---|--:|--:|--:|--:|--:|---|
| 1 | 17 | 4947 | SPS | 2025-12-23 | 496 | 0 | 62 | 496 | 0.0% | Projet de loi spéciale prévue par l'article 45 de la loi organique n°2… |
| 2 | 17 | 5728 | SPS | 2026-02-25 | 491 | 0 | 69 | 491 | 0.0% | Soins palliatifs et d’accompagnement |
| 3 | 17 | 525 | SPS | 2024-12-16 | 481 | 0 | 63 | 481 | 0.0% | Projet de loi spéciale prévue par l’article 45 de la loi organique du … |
| 4 | 17 | 790 | SPS | 2025-02-12 | 451 | 0 | 65 | 451 | 0.0% | Projet de loi d'urgence pour Mayotte |
| 5 | 17 | 266 | SPO | 2024-11-06 | 297 | 0 | 0 | 297 | 0.0% | Proposition de loi organique visant à reporter le renouvellement génér… |
| 6 | 16 | 3373 | SPO | 2024-02-29 | 293 | 0 | 0 | 293 | 0.0% | Proposition de loi visant à la nationalisation du groupe Électricité d… |
| 7 | 16 | 3374 | SPO | 2024-02-29 | 207 | 0 | 0 | 207 | 0.0% | Renforcer la protection des mineurs et l’honorabilité dans le sport |
| 8 | 16 | 3336 | SPO | 2024-02-06 | 195 | 0 | 0 | 195 | 0.0% | Garantir le respect du droit à l'image des enfants |
| 9 | 16 | 1742 | SPO | 2023-05-31 | 194 | 0 | 0 | 194 | 0.0% | Lutte contre les arnaques et les dérives des influenceurs sur les rése… |
| 10 | 16 | 2075 | SPO | 2023-06-28 | 191 | 0 | 0 | 191 | 0.0% | Instaurer une majorité numérique et à lutter contre la haine en ligne |

## 7. Limites & honnêteté méthodo

- **Couverture AMO10 :** 244 acteurRef présents dans les votes de réf ne sont pas dans le dump acteurs (29.76% des 820 distincts). Sans impact ici : l'agrégation se fait par `groupe_ref` (groupe au moment du vote, fourni par `positions_nominales`), pas via le dump acteurs.
- **leg 17 en cours :** corpus partiel, susceptible d'évoluer. Comparaison leg16/leg17 à lire avec prudence (volumes 93 vs 66).
- **Score de congruence simulé** = proxy binaire (position majoritaire du groupe vs sort). Le vrai produit pourra pondérer par taille de groupe ou compter au nominatif ; mais la conclusion de platitude tient quel que soit le raffinement, car elle vient de la distribution des votes eux-mêmes (unanimité massive), pas du choix de métrique.
- **Ratifications :** très consensuelles par nature ; les isoler change peu le verdict global mais documenté ci-dessus.
- **Marge sur exprimés** : exclut abstentions et non-votants du dénominateur (choix AN). Si on rapportait la minorité aux 577 sièges, les marges seraient encore plus écrasées.

