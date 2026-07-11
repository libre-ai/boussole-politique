# q6-censure — Motions de censure & branche 49.3

**Valide / teste :** revue §2.4 (branche 49.3 / motions de censure).  
**Corpus consommé :** `out/corpus.json` (159 lois jugeables : 93 leg16 + 66 leg17, FIGÉ).  
**Source motions :** `anlib.load_scrutins(16|17)`, filtre `type_code=='MOC'`.

## 0. Piège de filtre corrigé (à signaler)

Le mandat demande de filtrer `type_libelle=="motion de censure"`. **Ce filtre ne capture que la leg17.** En **leg16, les 34 motions portent `type_libelle=="scrutin public solennel"`** (et non "motion de censure") — seul `type_code=="MOC"` est stable sur les deux législatures. J'utilise donc `type_code=="MOC"`.

| leg | `type_code=='MOC'` | `type_libelle=='motion de censure'` | libellés vus dans MOC |
|---|---|---|---|
| 16 | **34** | 0 | {'scrutin public solennel': 34} |
| 17 | **22** | 22 | {'motion de censure': 22} |

## 1. Recensement et classification 49.2 / 49.3

Distinction par le titre du scrutin : « article 49, **alinéa 2** » = censure spontanée (initiative de députés) ; « article 49, **alinéa 3** » = réponse à un engagement de responsabilité du Gouvernement sur un texte. La classification est **100 % nette** (0 motion non classée sur 56).

| | leg16 (close) | leg17 (en cours) | total |
|---|---|---|---|
| Motions de censure (MOC) | 34 | 22 | 56 |
| dont **49.2** (spontanées) | 6 | 11 | 17 |
| dont **49.3** (sur un texte) | 28 | 11 | 39 |
| adoptées (gvt renversé) | 0 | 1 | 1 |
| rejetées | 34 | 21 | 55 |

**Une seule motion adoptée sur toute la période : la n°519 (leg17).** Toutes les autres (55) ont été rejetées — c'est le régime normal du 49.3 : le gouvernement n'est renversé que si la majorité absolue (289) vote la censure.

### Focus : motion n°519 du 2024-12-04 (ADOPTÉE)

- **Scrutin n°519, leg17, 2024-12-04**, 49.3, **ADOPTÉE** avec **331 voix pour** (seuil 289), 0 contre, 0 abstention.
- Engagement de responsabilité du **gouvernement Barnier** sur le **PLFSS 2025 (version CMP)** — dossier d'engagement `DLR5L17N50975`, titreChemin `49al3CMPPLFSS2025`.
- Conséquence : **gouvernement renversé** ; le dossier d'engagement n'a **aucun acte `PROM`** → la version du texte engagée **est tombée**. (Un PLFSS « pour 2026 » distinct sera promulgué plus tard, dans la mandature suivante.)

### Détail leg16 (close, 34 motions)

| n° | date | al. | sort | pour | contre | abst | votants | auteur | texte engagé (acte) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2022-07-11 | 49.2 | rejeté | 146 | 0 | 0 | 146 | Mme Mathilde Panot |  |
| 358 | 2022-10-24 | 49.3 | rejeté | 239 | 0 | 0 | 239 | Mmes Cyrielle Chatelain et M |  |
| 359 | 2022-10-24 | 49.3 | rejeté | 90 | 0 | 0 | 90 | Mme Marine Le Pen et 89 memb |  |
| 360 | 2022-10-24 | 49.3 | rejeté | 150 | 0 | 0 | 150 | M. Boris Vallaud |  |
| 485 | 2022-10-31 | 49.3 | rejeté | 90 | 0 | 0 | 90 | Mme Marine Le Pen et 88 memb |  |
| 486 | 2022-10-31 | 49.3 | rejeté | 218 | 0 | 0 | 218 | Mme Mathilde Panot et 74 mem |  |
| 494 | 2022-11-04 | 49.3 | rejeté | 188 | 0 | 0 | 188 | Mme Mathilde Panot et 74 mem |  |
| 632 | 2022-11-25 | 49.3 | rejeté | 85 | 0 | 0 | 85 | Mme Mathilde Panot et 74 mem |  |
| 634 | 2022-11-28 | 49.3 | rejeté | 93 | 0 | 0 | 93 | Mme Mathilde Panot et 74 mem |  |
| 664 | 2022-12-02 | 49.3 | rejeté | 87 | 0 | 0 | 87 | Mme Mathilde Panot |  |
| 744 | 2022-12-11 | 49.3 | rejeté | 78 | 0 | 0 | 78 | Mme Mathilde Panot et 74 mem |  |
| 780 | 2022-12-13 | 49.3 | rejeté | 102 | 0 | 0 | 102 | Mme Mathilde Panot et 74 mem |  |
| 822 | 2022-12-17 | 49.3 | rejeté | 101 | 0 | 0 | 101 | M. André Chassaigne |  |
| 1097 | 2023-02-17 | 49.2 | rejeté | 89 | 0 | 0 | 89 | Mme Marine Le Pen et 87 de s |  |
| 1240 | 2023-03-20 | 49.3 | rejeté | 278 | 0 | 0 | 278 | M. Bertrand Pancher et 90 me |  |
| 1241 | 2023-03-20 | 49.3 | rejeté | 94 | 0 | 0 | 94 | Mme Marine Le Pen et 87 memb |  |
| 1800 | 2023-06-12 | 49.2 | rejeté | 239 | 0 | 0 | 239 | M. Boris Vallaud |  |
| 2610 | 2023-09-29 | 49.3 | rejeté | 193 | 0 | 0 | 193 | M. Boris Vallaud |  |
| 2798 | 2023-10-20 | 49.3 | rejeté | 89 | 0 | 0 | 89 | Mme Marine Le Pen et 87 memb |  |
| 2799 | 2023-10-20 | 49.3 | rejeté | 219 | 0 | 0 | 219 | Mme Mathilde Panot et 102 me |  |
| 2809 | 2023-10-30 | 49.3 | rejeté | 223 | 0 | 0 | 223 | Mmes Mathilde Panot et Cyrie |  |
| 2810 | 2023-10-30 | 49.3 | rejeté | 88 | 0 | 0 | 88 | Mme Marine Le Pen et 87 memb |  |
| 2887 | 2023-11-04 | 49.3 | rejeté | 89 | 0 | 0 | 89 | Mme Mathilde Panot et 77 mem |  |
| 2944 | 2023-11-09 | 49.3 | rejeté | 167 | 0 | 0 | 167 | Mme Mathilde Panot et 77 mem |  |
| 2989 | 2023-11-15 | 49.3 | rejeté | 143 | 0 | 0 | 143 | M. André Chassaigne |  |
| 3046 | 2023-11-26 | 49.3 | rejeté | 89 | 0 | 0 | 89 | Mme Mathilde Panot et 77 mem |  |
| 3067 | 2023-11-29 | 49.3 | rejeté | 145 | 0 | 0 | 145 | Mme Mathilde Panot et 74 mem |  |
| 3116 | 2023-12-04 | 49.3 | rejeté | 108 | 0 | 0 | 108 | Mme Mathilde Panot |  |
| 3210 | 2023-12-16 | 49.3 | rejeté | 75 | 0 | 0 | 75 | Mme Mathilde Panot et 77 mem |  |
| 3211 | 2023-12-18 | 49.3 | rejeté | 110 | 0 | 0 | 110 | Mme Mathilde Panot et 77 mem |  |
| 3215 | 2023-12-21 | 49.3 | rejeté | 116 | 0 | 0 | 116 | Mmes Mathilde Panot |  |
| 3335 | 2024-02-05 | 49.2 | rejeté | 124 | 0 | 0 | 124 | Mme Mathilde Panot |  |
| 4020 | 2024-06-03 | 49.2 | rejeté | 222 | 0 | 0 | 222 | Mme Mathilde Panot | motion_censure_lfi_gdr_ecolo_3 (AN21-MOTION-VOTE) |
| 4021 | 2024-06-03 | 49.2 | rejeté | 89 | 0 | 0 | 89 | Mme Marine Le Pen et 87 dépu | motion_censure_RN_2 (AN21-MOTION-VOTE) |

### Détail leg17 (en cours, 22 motions)

| n° | date | al. | sort | pour | contre | abst | votants | auteur | texte engagé (acte) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2024-10-08 | 49.2 | rejeté | 197 | 0 | 0 | 197 | M. Boris Vallaud | motion_censure_soc_1024_1 (AN21-MOTION-VOTE) |
| 519 | 2024-12-04 | 49.3 | **ADOPTÉE** | 331 | 0 | 0 | 331 | Mme Mathilde Panot | 49al3CMPPLFSS2025 (AN21-MOTION-VOTE); plfss_pour_2025 (CMP-MOTION-VOTE) |
| 526 | 2025-01-16 | 49.2 | rejeté | 131 | 0 | 0 | 131 | Mme Mathilde Panot et 57 dép | motion_censure_panot_57_collegues (AN21-MOTION-VOTE) |
| 693 | 2025-02-05 | 49.3 | rejeté | 128 | 0 | 0 | 128 | Mme Mathilde Panot et 90 dép | engagement_responsabilite_gouvernement_plf_2025_cmp (AN21-MOTION-VOTE); PLF2025 (CMP-MOTION-VOTE) |
| 694 | 2025-02-05 | 49.3 | rejeté | 122 | 0 | 0 | 122 | Mme Mathilde Panot et 91 dép | plfss_pour_2025 (ANNLEC-MOTION-VOTE); 49_3_plfssP1 (AN21-MOTION-VOTE) |
| 739 | 2025-02-10 | 49.3 | rejeté | 115 | 0 | 0 | 115 | Mme Mathilde Panot et 70 dép | plfss_pour_2025 (ANNLEC-MOTION-VOTE); engagement_resp_P2_plfss2025 (AN21-MOTION-VOTE) |
| 791 | 2025-02-12 | 49.3 | rejeté | 121 | 0 | 0 | 121 | Mme Mathilde Panot et 73 dép | plfss_pour_2025 (ANNLEC-MOTION-VOTE); engagement_responsabilite_plfss2025_nlle_lecture_P3 (AN21-MOTION-VOTE) |
| 842 | 2025-02-19 | 49.2 | rejeté | 181 | 0 | 0 | 181 | M. Boris Vallaud et 65 déput | motion_censure_vallaud_65_collegues_2025 (AN21-MOTION-VOTE) |
| 2222 | 2025-06-04 | 49.2 | rejeté | 116 | 0 | 0 | 116 | Mme Aurélie Trouvé et 57 dép | motion_censure_trouve_303525 (AN21-MOTION-VOTE) |
| 2876 | 2025-07-01 | 49.2 | rejeté | 189 | 0 | 0 | 189 | M. Boris Vallaud et 65 déput | motion_censure_socialistes (AN21-MOTION-VOTE) |
| 3058 | 2025-10-16 | 49.2 | rejeté | 271 | 0 | 0 | 271 | Mme Mathilde Panot et 86 dép |  |
| 3059 | 2025-10-16 | 49.2 | rejeté | 144 | 0 | 0 | 144 | Mme Marine Le Pen |  |
| 4986 | 2026-01-14 | 49.2 | rejeté | 256 | 0 | 0 | 256 | Mme Mathilde Panot et 57 dép | motion_censure_LFI_Panot_57_14 (AN21-MOTION-VOTE) |
| 4987 | 2026-01-14 | 49.2 | rejeté | 142 | 0 | 0 | 142 | Mme Marine Le Pen et 57 dépu | motiondecensure_RN_15 (AN21-MOTION-VOTE) |
| 5154 | 2026-01-23 | 49.3 | rejeté | 269 | 0 | 0 | 269 | Mme Mathilde Panot | engagement_responsabilite_gouvernement_partie1_plf_2026 (AN21-MOTION-VOTE); PLF_2026 (ANNLEC-MOTION-VOTE) |
| 5155 | 2026-01-23 | 49.3 | rejeté | 142 | 0 | 0 | 142 | Mme Marine Le Pen | engagement_responsabilite_gouvernement_partie1_plf_2026 (AN21-MOTION-VOTE); PLF_2026 (ANNLEC-MOTION-VOTE) |
| 5193 | 2026-01-27 | 49.3 | rejeté | 267 | 0 | 0 | 267 | Mme Cyrielle Chatelain | engagement_responsabilite_gouvernement_plf_2026_2emepartie (AN21-MOTION-VOTE); PLF_2026 (ANNLEC-MOTION-VOTE) |
| 5194 | 2026-01-27 | 49.3 | rejeté | 140 | 0 | 0 | 140 | Mme Marine Le Pen | engagement_responsabilite_gouvernement_plf_2026_2emepartie (AN21-MOTION-VOTE); PLF_2026 (ANNLEC-MOTION-VOTE) |
| 5284 | 2026-02-02 | 49.3 | rejeté | 260 | 0 | 0 | 260 | M. Stéphane Peu | PLF_2026 (ANLDEF-MOTION-VOTE); engagement_responsabilite_gouvernement_lectdefinitive_pfl_2026 (AN21-MOTION-VOTE) |
| 5285 | 2026-02-02 | 49.3 | rejeté | 135 | 0 | 0 | 135 | Mme Marine Le Pen | PLF_2026 (ANLDEF-MOTION-VOTE); engagement_responsabilite_gouvernement_lectdefinitive_pfl_2026 (AN21-MOTION-VOTE) |
| 5730 | 2026-02-25 | 49.2 | rejeté | 140 | 0 | 0 | 140 | M. Jean-Philippe Tanguy et 5 | motion_censure_rn_022026 (AN21-MOTION-VOTE) |
| 5731 | 2026-02-25 | 49.2 | rejeté | 108 | 0 | 0 | 108 | Mme Mathilde Panot et 57 dép | motion_censure_Panot_57_collegues_23022026 (AN21-MOTION-VOTE) |

## 2. Motions par date — le modèle `SignalRejet` singulier est FAUX

La spec modélise un signal de rejet **unique** (1 motion ↔ 1 événement). La donnée montre que **plusieurs motions sont déposées le même jour par des groupes différents** (typiquement une motion « de gauche » NFP/LFI et une motion RN/UDR), votées dans la même séance.

| leg | dates distinctes | max motions / jour | dates à ≥2 motions | motions concernées |
|---|---|---|---|---|
| 16 | 27 | 3 | 6 | 13 |
| 17 | 15 | 2 | 7 | 14 |

**Dates leg16 à plusieurs motions :** 2022-10-24 (3), 2022-10-31 (2), 2023-03-20 (2), 2023-10-20 (2), 2023-10-30 (2), 2024-06-03 (2).

**Dates leg17 à plusieurs motions :** 2025-02-05 (2), 2025-10-16 (2), 2026-01-14 (2), 2026-01-23 (2), 2026-01-27 (2), 2026-02-02 (2), 2026-02-25 (2).

Exemple le plus dense : **2022-10-24, 3 motions** déposées le même jour (n°358, 359, 360) en réponse au 49.3 sur le PLF 2023 (1re partie). Un modèle à 1 ligne perdrait 2 des 3 signaux.

## 3. Lien 49.3 → textes : la branche hors-score

Aucune motion (0/56) ne porte de `dossierRef` ni de `referenceLegislative` dans sa donnée de scrutin — **le texte visé n'est PAS dans le scrutin**. Le lien autoritatif passe par l'**arbre d'actes du dossier** : les actes `*-MOTION-VOTE` (ex. `CMP-MOTION-VOTE`, `ANNLEC-MOTION-VOTE`, `ANLDEF-MOTION-VOTE`) portent un `voteRef` vers le scrutin de censure.

**Asymétrie de complétude (limite à documenter) :** ce lien n'est exploitable que pour la **leg17 (20/22 motions reliées à un dossier, dont 11/11 des 49.3)**. En **leg16, seules 2/34** motions sont reliées par acte — et ce sont des **49.2** (n°4020/4021, 2024-06-03) ; **aucune des 28 motions 49.3 de la leg16 n'est tracée** vers son texte (le dump dossiers leg16 ne porte pas ces `voteRefs` sur les engagements budgétaires). Le rattachement leg16 reste donc *historique* (connu hors donnée : 49.3 répétés sur PLF 2023, PLFSS 2023, PLF 2024…), non vérifiable par les actes.

### 3.1 Lois de finances promulguées : corpus vs exclues

Sur **14 lois de finances/PLFSS/PLFR/comptes promulguées** (toutes législatures), **seules 4 entrent dans le corpus jugeable** (elles ont un scrutin public AN sur l'ensemble) ; **10 sont exclues** (pas de vote public d'ensemble → passées par 49.3 ou navette sans vote AN final).

| leg | proc. | dans corpus ? | vote public ensemble ? | motions 49.3 liées | titre |
|---|---|---|---|---|---|
| 16 | PL PLFSS | exclue | False | — | Financement de la sécurité sociale pour 2023 |
| 16 | PL PLFSS | exclue | False | — | Projet de loi de financement de la sécurité so |
| 16 | PL PLFSS | exclue | False | — | Projet de loi de financement rectificative de  |
| 16 | PL fin. de l'année | exclue | False | — | Projet de loi de finances pour 2023 |
| 16 | PL fin. de l'année | exclue | False | — | Projet de loi de finances pour 2024 |
| 16 | PL fin. rectificative | exclue | False | — | Loi de finances rectificative pour 2022 |
| 16 | PL fin. rectificative | exclue | False | — | Projet de loi de finances de fin de gestion po |
| 16 | PL fin. rectificative | **CORPUS** | True | — | Projet de loi de finances rectificative pour 2 |
| 17 | PL PLFSS | exclue | False | n519(ado), n694(rej), n739(rej), n791(rej) | Projet de loi de financement de la sécurité so |
| 17 | PL PLFSS | **CORPUS** | True | — | Projet de loi de financement de la sécurité so |
| 17 | PL fin. de l'année | exclue | False | n693(rej) | Projet de loi de finances pour 2025 |
| 17 | PL fin. de l'année | exclue | False | n5154(rej), n5155(rej), n5193(rej), n5194(rej), n5284(rej), n5285(rej) | Projet de loi de finances pour 2026 |
| 17 | PL fin. rectificative | **CORPUS** | True | — | Projet de loi de finances de fin de gestion po |
| 17 | PL fin. rectificative | **CORPUS** | True | — | Projet de loi de finances de fin de gestion po |

Lecture : les budgets **structurants** (PLF de l'année, PLFSS) sont **systématiquement exclus** car passés par 49.3 (aucun vote public sur l'ensemble). Les seules lois financières qui entrent dans le corpus sont des textes **non engagés** : PLFR 2022 (leg16) et les **lois de fin de gestion 2024/2025** (leg17), votées normalement, plus le **PLFSS 2026** qui a obtenu un vote d'ensemble.

### 3.2 Tous les textes engagés via 49.3 (leg17, lien tracé)

Regroupement par dossier d'engagement / loi (le `titre_chemin` nomme le texte). **La colonne `n_motions` est la cardinalité réelle du signal de censure par événement 49.3.**

| dossier | texte engagé (titre_chemin) | promulgué ? | loi corpus ? | motions | n |
|---|---|---|---|---|---|
| DLR5L17N51427 | 49_3_plfssP1 | False | False | n694 | **1** |
| DLR5L17N50975 | 49al3CMPPLFSS2025 | False | False | n519 | **1** |
| DLR5L17N50198 | PLF2025 | True | False | n693 | **1** |
| DLR5L17N52428 | PLF_2026 | True | False | n5154, n5155, n5193, n5194, n5284, n5285 | **6** |
| DLR5L17N51462 | engagement_resp_P2_plfss2025 | False | False | n739 | **1** |
| DLR5L17N53689 | engagement_responsabilite_gouvernement_lec | False | False | n5284, n5285 | **2** |
| DLR5L17N53597 | engagement_responsabilite_gouvernement_par | False | False | n5154, n5155 | **2** |
| DLR5L17N51425 | engagement_responsabilite_gouvernement_plf | False | False | n693 | **1** |
| DLR5L17N53619 | engagement_responsabilite_gouvernement_plf | False | False | n5193, n5194 | **2** |
| DLR5L17N51475 | engagement_responsabilite_plfss2025_nlle_l | False | False | n791 | **1** |
| DLR5L17N50588 | plfss_pour_2025 | True | False | n519, n694, n739, n791 | **4** |

## 4. Conclusion

1. **56 motions de censure** au total (34 leg16 + 22 leg17), dont **39 en 49.3** (28 + 11) et **17 en 49.2**. **Une seule adoptée** (n°519, PLFSS 2025 Barnier).

2. **Le modèle `SignalRejet` singulier (1 motion) est FAUX.** Cardinalité observée **0..n** : jusqu'à **3 motions le même jour** (2022-10-24) et jusqu'à **6 motions sur un même texte** (PLF 2026, leg17). Sur les événements 49.3 tracés (leg17), la distribution est {1: 6, 2: 3, 4: 1, 6: 1} (clé = nb de motions). Le modèle doit être une **collection** de motions rattachée à un texte/lecture, chaque motion gardant auteur, alinéa, sort et décompte.

3. **Lois structurantes hors-score via 49.3.** **3 lois de finances promulguées et exclues du corpus** ont un 49.3 *explicitement tracé* par acte en leg17 : Projet de loi de financement de la, Projet de loi de finances pour 202, Projet de loi de finances pour 202. En élargissant aux **budgets structurants** (PLF de l'année + PLFSS, hors rectificatives/fin de gestion) promulgués mais hors corpus, on compte **8 lois** (Financement de la sécurité soc (L16), Projet de loi de financement d (L16), Projet de loi de financement r (L16), Projet de loi de finances pour (L16), Projet de loi de finances pour (L16), Projet de loi de financement d (L17), Projet de loi de finances pour (L17), Projet de loi de finances pour (L17)). Et globalement **10/14 lois financières promulguées échappent au corpus jugeable**. La branche 49.3 retire du score l'essentiel de la production budgétaire structurante — angle mort assumé mais massif du périmètre v0.1.

4. **Limites honnêtes :** (a) le rattachement motion→texte n'est tracé par acte qu'en **leg17** ; en leg16 il est historique. (b) Le lien repose sur les actes `*-MOTION-VOTE` du dossier — robuste là où il existe, mais dépend de la complétude du dump. (c) « Structurant » est ici opérationnalisé par « loi de finances/PLFSS promulguée » ; d'autres textes ordinaires sont aussi passés par 49.3 (non comptés ici comme financiers).
