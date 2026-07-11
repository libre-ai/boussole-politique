# Vérification adverse — Q2 « Participation & polarisation des votes de référence »

**Vérificateur :** recalcul indépendant (parse maison de `corpus.json` + ré-agrégation depuis les fichiers scrutins BRUTS via `decompteNominatif`), SANS réutiliser `q2-polarisation.py`.
**Date :** 2026-06-13. **Scripts :** `dry-run/scripts/v-q2-check.py` ; chiffres machine `dry-run/out/v-q2-check.json`.

## Verdict : CONCORDE (confiance haute)

Tous les chiffres du headline sont reproduits **au chiffre près** par une méthode indépendante. Un seul écart mineur et **non-substantiel** sur le décompte des groupes de congruence (9 vs 10), dû à un choix méthodo défendable sur les blocs de groupe vides — il ne change pas la conclusion.

| Chiffre du headline | Analyse (q2) | Mon recalcul indépendant | Concorde |
|---|--:|--:|:--:|
| n votes de référence | 159 | 159 | OUI |
| leg16 / leg17 | 93 / 66 | 93 / 66 | OUI |
| % quasi-unanime global (min < 10%) | 50,3 % (80) | 50,3 % (80/159) | OUI |
| % intermédiaire global | 15,7 % (25) | 15,7 % (25) | OUI |
| % discriminant global (min ≥ 20%) | 34,0 % (54) | 34,0 % (54) | OUI |
| % QU leg16 / leg17 | 54,8 / 43,9 | 54,8 / 43,9 | OUI |
| % disc leg16 / leg17 | 30,1 / 39,4 | 30,1 / 39,4 | OUI |
| part minorité médiane | 0,0972 | 0,0972 | OUI |
| marge gagnante médiane | 0,8056 | 0,8056 | OUI |
| votants médian / part % | 154 / 26,7 % | 154 / 26,7 % | OUI |
| exprimés médian / part % | 141 / 24,4 % | 141 / 24,4 % | OUI |
| n ratifications / % QU | 8 / 62,5 % | 8 / 62,5 % | OUI |
| congruence moyenne (tous, global) | **0,82** (0,8213) | **0,8244** | OUI (~) |
| spread QU / disc / tous | 0,0811 / 0,9615 / 0,5455 | 0,0811 / 0,9615 / 0,5455 | OUI |
| couverture AMO10 absents | 29,76 % | 29,76 % (244/820) | OUI |
| vote le plus serré | leg17 4442 217/213 (49,5%) | idem | OUI |
| vote le plus unanime | leg17 4947 496/0 | idem | OUI |
| **groupes au-dessus de 80%** | **6/9** | **7/10** (incl. NI) | ÉCART MINEUR |

## Le seul écart : « 6/9 groupes au-dessus de 80% » → 7/10 selon ma méthode

**Cause identifiée (pas un bug, un choix méthodo) : les blocs de groupe VIDES.**

Le headline dit « 6 des 9 groupes majeurs au-dessus de 80 % ». Mon recalcul trouve **10 groupes majeurs**, dont **7 au-dessus de 80 %**, parce que j'inclus un 10e groupe : **PO793087 = Non-inscrits (leg16)**, score 0,8519 (> 80%).

La divergence vient de la définition de « groupe présent sur ≥ 50 % des 159 votes » (seuil = 79,5 votes) :

- **Analyse** (via `anlib.positions_nominales()`) : ce générateur n'itère QUE les électeurs réellement listés dans les buckets `pours/contres/abstentions/nonVotants`. Le bloc Non-inscrits est **présent mais VIDE** (0 pour, 0 contre, 0 abst, 0 nonvotant) dans **33 des 159 scrutins** → le groupe n'est compté présent que **60 fois** → 60 < 79,5 → **exclu**. D'où 9 groupes.
- **Mon recalcul** (lecture directe de `ventilationVotes.organe.groupes.groupe[]`) : j'enregistre la clé du groupe dès que le **bloc existe** dans la ventilation, même vide → présence = **93** → 93 ≥ 79,5 → **inclus**. D'où 10 groupes.

J'ai prouvé que les deux méthodes donnent des comptes pour/contre **identiques** groupe par groupe (1815/1815 cellules (scrutin, groupe) concordent, 0 divergence) : la seule différence est le traitement des blocs vides pour le critère de présence.

**Échantillons réels du bloc NI vide** (decompte nominatif 0/0/0/0) : leg16 scrutins 907 (accord océan Indien), 2118 (biens culturels spoliés), 2988 (navigation aérienne), 3370 (réseau routier régions), 3045 (bien vieillir), 2710 (négociations commerciales)… 33 au total.

**Impact sur le headline : négligeable.**
- Moyenne inter-groupes : 0,8213 (9 groupes) vs **0,8244** (10 groupes, +NI) — écart de 0,003, le headline arrondit à 0,82 dans les deux cas.
- « au-dessus de 80% » : 6/9 (analyse) vs 7/10 (moi). NI à 0,852 bascule au-dessus du seuil. Les deux énoncés décrivent la **même réalité** (« la grande majorité des groupes congruent à ~80 % »).
- En **part** : 6/9 = 66,7 % des groupes ; 7/10 = 70 %. Pas de retournement de sens.

Lequel est « le bon » ? C'est un arbitrage légitime : « groupe présent à ce vote » peut vouloir dire « au moins un membre a une position enregistrée » (analyse — défendable, un bloc vide = personne du groupe n'a voté/s'est abstenu de façon nominative) ou « le groupe existait à la date du vote » (moi). **Aucun des deux n'est faux.** Le headline gagnerait à préciser le seuil et le traitement des blocs vides, mais le chiffre-clé tient.

## Robustesse : la conclusion ne dépend pas du choix de métrique

J'ai testé une **moyenne pondérée** par présence (somme des congruents / somme des définis sur groupes majeurs) au lieu de la moyenne simple inter-groupes :

| Sous-ensemble | moyenne simple (analyse) | moyenne pondérée (test) |
|---|--:|--:|
| tous global | 0,82 | 0,836 |
| tous leg16 | 0,827 | 0,837 |
| tous leg17 | 0,837 | 0,841 |

→ ~0,82–0,84 quel que soit le mode d'agrégation. Le « reveal plat » est confirmé : sur les votes **quasi-unanimes** le spread inter-groupes est **0,0811** (tous collés à ~0,92–1,0), sur les **discriminants** il explose à **0,9615**. La moitié des votes de référence étant quasi-unanimes, le score agrégé brut est mécaniquement dominé par du bruit unanime.

## Pièges vérifiés et écartés

- **Double-comptage / sélection du vote de réf** : 0 anomalie. Pour chaque loi j'ai re-sélectionné `numero==ref_numero & leg==ref_leg` depuis `votes[]` ; 1 vote de réf par loi, 159 lois, 159 rows. Aucune loi sans vote de réf.
- **Intégrité corpus ↔ source brute** : pour les 159 votes de réf, le triplet (pour, contre, abst) de `corpus.json` == `syntheseVote.decompte` du fichier scrutin brut sur **159/159** (0 mismatch). Pas de dérive corpus/source.
- **« l'ensemble »** : les 159 votes de réf portent bien sur « l'ensemble » (objet du scrutin, après normalisation des apostrophes `'`/`’`) — 159/159.
- **Sort** : `corpus.sort == source.sort` sur 159/159 ; **159 adoptés, 0 rejeté** (cohérent : ce sont des lois promulguées, le vote de réf est forcément une adoption). Le headline ne mentionne pas de rejet — OK.
- **Apostrophes** : la détection « l'ensemble » et le matching ne sont pas affectés (normalisation `’→'` appliquée).
- **Objet-vs-tableau** : géré par `as_list` dans mon parse ; les blocs `votant` singletons sont bien comptés.

## Limites honnêtes

- **AMO10 = leg17 only** : les 244 acteurRef absents (29,76 %) sont surtout des députés leg16 et des partis en cours de mandat. Sans impact sur le chiffre-clé : l'agrégation passe par `groupe_ref` (groupe au moment du vote, dans la ventilation), pas par le dump acteurs. Confirmé.
- **Score de congruence = proxy binaire** (position majoritaire du groupe vs sort). La platitude vient de la distribution des votes (unanimité massive), pas du choix de métrique — confirmé par le test pondéré.
- **leg17 en cours** : corpus partiel (66 vs 93), comparaison à lire avec prudence.
- **Codes de groupe leg16 vs leg17 ne se mélangent pas** : c'est précisément pourquoi le bloc `tous_global` ne retient QUE des codes leg16 (présents 93/159 = 58,5 %) ; les codes leg17 (66/159 = 41,5 %) tombent sous le seuil de 50 %. Le « 9 groupes » global est donc de facto un agrégat **leg16** — point que le headline n'explicite pas, mais le rapport q2 le note (§4).
