# q5 — Mises au point (corrections de vote) & qualité de données (art.16 RGPD)

*Valide/teste §2.2 de la revue des specs. Données : open data AN, scrutins leg 16 (close) et leg 17 (en cours). Corpus figé de 159 lois jugeables (93 leg 16 / 66 leg 17).*

## TL;DR

- **80 / 159 votes de référence** portent une mise au point publiée par l'AN (**50.3 %**) : leg 16 = 43/93, leg 17 = 37/66.
- Sur ces votes de référence : **172 corrections individuelles** de position (un député qui rectifie son vote).
- **167 de ces 172 corrections (97.1 %) changent la CLASSE de congruence** du député (pour / contre / neutre) — donc peuvent FAIRE BASCULER le signe d'une paire citoyen-député sur la loi concernée.
- Dont **13 bascules franches pour↔contre** (inversion complète du signe) sur les seuls votes de référence.
- Enjeu RGPD art.16 : afficher le décompte brut sans appliquer la mise au point = publier une **donnée inexacte sur une personne nommée** — le député X est affiché « pour » alors que l'AN a officiellement enregistré sa rectification en « contre » (ou inversement).

- ⚠️ **Piège de données trouvé** : le champ `has_mise_au_point` de la lib (anlib) est **faux pour toute la leg 17** (il vaut `True` pour les 7397 scrutins). On utilise donc « ≥ 1 correction individuelle réelle » comme seul critère fiable — voir §0.

## 0. Piège de données : le flag `has_mise_au_point` n'est pas fiable

Avant tout chiffre : **ne pas se fier au booléen `has_mise_au_point`**. En leg 17, chaque scrutin porte un `miseAuPoint` *squelette* `{abstentions:[null,null], nonVotants:[null,null], nonVotantsVolontaires:[null,null], pours:null, contres:null}`. Les listes `[null,null]` sont *truthy* en Python, donc le test `any(mp.get(k) ...)` renvoie `True` même quand il n'y a **aucune** correction.

| Législature | scrutins | `has_mise_au_point` == True | ≥ 1 correction RÉELLE | flag fiable ? |
|---|---:|---:|---:|---|
| 16 | 4106 | 935 | 929 | **NON** |
| 17 | 7397 | 7397 | 1343 | **NON** |

**Conséquence** : tout comptage « combien de scrutins ont une mise au point ? » basé sur le flag est trompeur en leg 17 (il dirait 100 %). Le seul critère correct est de **compter les votants réels dans les buckets** (en gérant le motif objet-vs-tableau `[null, {votant:[...]}]`). Toute la suite de ce rapport utilise ce critère. C'est aussi une recommandation pour le pipeline : corriger `has_mp` pour qu'il teste la présence d'au moins un `votant`, pas la truthiness du bucket.

## 1. Sémantique de la mise au point (ce qu'une correction signifie)

Le champ `scrutin.miseAuPoint` de l'open data AN est structuré en buckets `pours / contres / abstentions / nonVotants / nonVotantsVolontaires`. **Un député listé dans le bucket K déclare que sa position aurait dû être K.** En croisant avec la ventilation nominale brute (`ventilationVotes`, position telle qu'enregistrée au moment du scrutin), on récupère la *transition* `recorded → corrected` :

- `contre → pour` / `pour → contre` : le boîtier a enregistré l'inverse de l'intention → **inversion du signe**.
- `pour/contre → abstention` ou `→ nonvotant` : le député retire son vote → **perte du signe**.
- `non_recense → pour/contre` : député non recensé dans la ventilation (absent/non-votant non listé) qui déclare une intention → **gain d'un signe**.

Le code de référence (art.16 RGPD) impose l'exactitude : la donnée affichée doit refléter la rectification officielle, pas la saisie brute du boîtier de vote.

> ⚠️ **Portée juridique exacte (important, à ne pas surinterpréter).** À l'Assemblée, la mise au point **ne modifie pas le résultat proclamé** du scrutin (art. 70 al. 4 IAN) : elle a une valeur *déclarative*, inscrite au compte rendu « à toutes fins utiles ». Donc une bascule de signe NE change PAS le sort de la loi. **Mais** elle change la **position individuelle nominative** du député — et c'est précisément cette donnée nominative (et la congruence citoyen↔député calculée dessus) qui est concernée par l'art.16 RGPD. Le produit doit afficher la position rectifiée, pas le décompte proclamé.

## 2. Combien de votes de référence ont une mise au point ?

*(« avec mise au point » = au moins une correction individuelle réelle, cf §0.)*

| Législature | votes réf. | avec mise au point | % | corrections indiv. | dont basculantes |
|---|---:|---:|---:|---:|---:|
| **16** (close) | 93 | 43 | 46.2 | 75 | 72 |
| **17** (en cours) | 66 | 37 | 56.1 | 97 | 95 |
| **Total** | 159 | 80 | 50.3 | 172 | 167 |

## 3. Corrections par type de cible (sur les votes de référence)

| Bucket miseAuPoint | position corrigée | n corrections |
|---|---|---:|
| `pours` | pour | 114 |
| `contres` | contre | 26 |
| `abstentions` | abstention | 22 |
| `nonVotants` | nonvotant | 10 |

### Transitions recorded → corrected (votes de référence)

| recorded (brut) | → corrected (mise au point) | n | bascule signe ? |
|---|---|---:|---|
| non_recense | pour | 90 | OUI |
| non_recense | contre | 22 | OUI |
| abstention | pour | 14 | OUI |
| contre | abstention | 10 | OUI |
| contre | pour | 10 | OUI (pour↔contre) |
| pour | abstention | 8 | OUI |
| pour | nonvotant | 6 | OUI |
| non_recense | abstention | 4 | non |
| contre | nonvotant | 3 | OUI |
| pour | contre | 3 | OUI (pour↔contre) |
| abstention | nonvotant | 1 | non |
| abstention | contre | 1 | OUI |

**Lecture** : 167 corrections changent la classe de congruence (lignes « OUI »), 5 la laissent inchangée (ex. `pour → pour` purement technique, ou neutre → neutre).

## 4. Une correction peut-elle faire basculer le signe de congruence ? — OUI, exemples nommés

Le signe de congruence d'une paire citoyen↔député sur une loi dépend de la classe de la position du député : **pour (+)**, **contre (−)**, ou **neutre (abstention/non-votant, 0)**. Toute correction qui change cette classe peut inverser le verdict de congruence affiché. Sur les **votes de référence** :

- **167 corrections basculantes** au total ; **13** sont des inversions franches `pour↔contre`.
- **143 portent un nom dans AMO10** (députés actifs) ; **24 portent sur des députés partis** (hors AMO10 — voir limite §6).

### Échantillon nommé (priorité aux inversions pour↔contre)

| Député | Groupe | Loi (vote de réf.) | Brut → Rectifié | Type |
|---|---|---|---|---|
| José Beaurain | PO800520 | Maintien provisoire d'un dispositif de veille et de sécur… (n°15, leg 16) | `pour → contre` | inversion pour↔contre |
| Jocelyn Dessigny | PO800520 | Maintien provisoire d'un dispositif de veille et de sécur… (n°15, leg 16) | `pour → contre` | inversion pour↔contre |
| Jean-Luc Bourgeaux | PO800508 | Ratification de la résolution A.1152 (32) relative aux am… (n°1412, leg 16) | `contre → pour` | inversion pour↔contre |
| Julie Lechanteux | PO800520 | Faciliter le passage et l’obtention de l’examen du permis… (n°1801, leg 16) | `contre → pour` | inversion pour↔contre |
| René Pilato | PO800490 | Transposition de l’accord national interprofessionnel rel… (n°3009, leg 16) | `pour → contre` | inversion pour↔contre |
| Joël Bruneau | LIOT | Proposition de loi relative au droit de vote par correspo… (n°2244, leg 17) | `contre → pour` | inversion pour↔contre |
| Pouria Amirshahi | ECOS | Projet de loi de programmation pour la refondation de May… (n°2975, leg 17) | `contre → pour` | inversion pour↔contre |
| Boris Tavernier | ECOS | Projet de loi de programmation pour la refondation de May… (n°2975, leg 17) | `contre → pour` | inversion pour↔contre |
| Pouria Amirshahi | ECOS | Département-Région de Mayotte (n°2976, leg 17) | `contre → pour` | inversion pour↔contre |
| Boris Tavernier | ECOS | Département-Région de Mayotte (n°2976, leg 17) | `contre → pour` | inversion pour↔contre |
| Erwan Balanant | DEM | Proposition de loi visant à soutenir les collectivités te… (n°5844, leg 17) | `contre → pour` | inversion pour↔contre |
| Richard Ramos | DEM | Proposition de loi visant à soutenir les collectivités te… (n°5844, leg 17) | `contre → pour` | inversion pour↔contre |
| Michel Castellani | LIOT | Proposition de loi portant pérennisation du contrat de pr… (n°7039, leg 17) | `contre → pour` | inversion pour↔contre |
| Pierre Henriet | HOR | Projet de loi de finances rectificative pour 2022 (n°624, leg 16) | `non_recense → pour` | gain/perte signe |
| Laurent Jacobelli | RN | Proposition de loi créant une aide universelle d'urgence … (n°837, leg 16) | `non_recense → pour` | gain/perte signe |
| Hubert Ott | DEM | Limiter l'engrillagement des espaces naturels et protéger… (n°891, leg 16) | `non_recense → pour` | gain/perte signe |
| Anne-Laure Blin | DR | Projet de loi relatif à l’accélération de la production d… (n°897, leg 16) | `non_recense → contre` | gain/perte signe |
| Michel Herbillon | DR | Convention d’entraide judiciaire en matière pénale entre … (n°906, leg 16) | `non_recense → pour` | gain/perte signe |

### Cas détaillé

**Proposition de loi relative au renforcement de la sûreté dans les transports** — vote de référence n°1041 (leg 17, 2025-03-18, sort : *adopté*).
Décompte brut proclamé : pour=303, contre=135, abst=7, non-votants=1.
Mise au point AN : 8 corrections, dont 8 basculantes. Députés nommés ayant rectifié leur signe :

- **Alexandre Sabatou** (RN) : enregistré `non_recense` → rectifié `pour`.
- **Kévin Pfeffer** (RN) : enregistré `non_recense` → rectifié `pour`.
- **Jean-Luc Bourgeaux** (DR) : enregistré `non_recense` → rectifié `pour`.
- **Hubert Brigand** (DR) : enregistré `non_recense` → rectifié `pour`.
- **Dominique Potier** (SOC) : enregistré `non_recense` → rectifié `pour`.
- **Anna Pic** (SOC) : enregistré `non_recense` → rectifié `pour`.
- **Constance de Pélichy** (LIOT) : enregistré `non_recense` → rectifié `pour`.
- **Harold Huwart** (LIOT) : enregistré `non_recense` → rectifié `pour`.

## 5. Enjeu art.16 RGPD — exactitude des données nominatives

L'article 16 du RGPD donne à toute personne le droit d'obtenir la rectification des données inexactes la concernant. Ici la personne nommée est un **député** et la donnée est sa **position de vote**, affichée publiquement et utilisée pour calculer une congruence citoyen↔élu.

**Le constat factuel** : l'AN publie elle-même la rectification (`miseAuPoint`). Afficher le décompte/position **brut** (saisie boîtier) en ignorant cette rectification revient à publier une donnée que l'autorité source a déjà reconnue inexacte. Concrètement :

- 167 fois sur les seuls votes de référence, le signe affiché (pour/contre/neutre) d'un député nommé serait FAUX si l'on ignore la mise au point.
- 13 de ces cas sont des inversions complètes pour↔contre : le pire scénario (« la plateforme dit que mon député a voté POUR cette loi, alors que l'AN a acté qu'il a voté CONTRE »).

**Recommandation de conception.** Le pipeline doit, pour chaque scrutin : (a) charger `positions_nominales()` (brut) PUIS (b) appliquer `miseAuPoint` par-dessus pour obtenir la **position effective rectifiée** par député, et calculer la congruence sur cette dernière. La position brute peut être conservée en interne (traçabilité) mais ne doit jamais être la donnée publiée ni la base du calcul de congruence. Cela couvre l'obligation d'exactitude (art.16) à coût quasi nul puisque la donnée de rectification est déjà dans le flux.

> Nuance honnête : la mise au point n'a qu'une portée *déclarative* côté AN (elle ne refait pas le scrutin). Mais du point de vue **donnée personnelle nominative**, la position rectifiée EST la position que l'intéressé a fait acter officiellement. Afficher l'autre, c'est afficher une donnée que le sujet conteste et que la source a corrigée.

## 6. Limites & honnêteté

- **Flag `has_mise_au_point` cassé (leg 17)** : documenté en §0 — corrigé ici par le comptage des votants réels. C'est le principal écueil de qualité de données rencontré.
- **Députés partis (hors AMO10)** : 24 corrections basculantes portent sur un `acteurRef` absent du dump AMO10 (leg 17, actifs) — on a la position et la rectification mais pas toujours le nom. Sur leg 16 (close) le dump AMO10 est leg 17, donc beaucoup de députés de la 16 n'y sont pas : c'est attendu, pas un bug. Le signe et la transition restent exacts ; seul le libellé du nom manque.
- **Noms de groupe leg 16** : la ventilation d'un scrutin ne porte que l'`organeRef` (code PO) du groupe, pas son libellé ; et il n'existe pas de dump d'organes leg 16 (AMO10 = leg 17). Les groupes des exemples leg 16 s'affichent donc en code PO (ex. PO800520 = le groupe RN de la 16). Les groupes leg 17 sont résolus en abréviation (RN, LFI-NFP, ECOS, LIOT…).
- **Classe neutre** : on classe abstention ET non-votant en « neutre (0) » pour la congruence. Si le produit traite l'abstention différemment du non-vote, certaines transitions `pour→abstention` comptées ici comme basculantes resteraient basculantes, mais des `abstention→nonvotant` (comptées neutres→neutres) le deviendraient ; l'ordre de grandeur ne change pas.
- **`dysfonctionnement`** : le sous-champ existe pour les pannes de boîtier ; il est quasi toujours vide sur le corpus et n'a pas été agrégé dans les transitions (compté à part).
- **Portée** : analyse limitée aux 159 **votes de référence**. Le contexte global (toutes lectures, tous scrutins) figure en §7 : la mise au point est massivement présente AU-DELÀ des seuls votes de référence (amendements, etc.), donc l'enjeu d'exactitude touche tout affichage de position de vote, pas seulement le vote d'ensemble.

## 7. Contexte global (tous scrutins, pour cadrage)

*(mise au point réelle = ≥ 1 correction individuelle ; pas le flag, cf §0.)*

| Législature | scrutins | avec mise au point réelle | % | corrections individuelles |
|---|---:|---:|---:|---:|
| 16 | 4106 | 929 | 22.6 | 1907 |
| 17 | 7397 | 1343 | 18.2 | 2827 |

Lecture : la mise au point est un phénomène **structurel et massif** de l'open data AN (pas une rareté). Les transitions dominantes au global sont les inversions `contre↔pour`, ce qui confirme que l'enjeu d'exactitude est de premier ordre dès qu'on affiche une position nominative.

---
*Fichiers : `scripts/q5-miseaupoint.py`, données machine `out/q5-miseaupoint.json`.*