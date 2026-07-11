# Q7 — Simulation de congruence : le reveal discrimine-t-il ?

**Valide la revue :** §1 (formule de congruence) + §4 (le reveal discrimine-t-il ?).
**Date :** 2026-06-13. **Corpus figé :** `out/corpus.json` — 159 lois jugeables (93 en leg 16 close, 66 en leg 17 en cours).
**Tous les chiffres :** `out/q7-simulation.json`. **Code :** `scripts/q7-simulation.py`.

---

## TL;DR — Verdict

**Sur la donnée réelle, le score de congruence SÉPARE NETTEMENT les groupes. Ce n'est PAS une machine à ~80 %.**
L'écart de congruence médian entre le meilleur et le pire groupe, pour un député pris comme citoyen, est de
**66,7 points** (leg 16 ET leg 17). Le groupe d'origine du député ressort en tête dans 52 % (leg 16) à 65 % (leg 17)
des cas, et dans le top-2 dans **86 %** des cas. Quasiment aucun député (< 1 %) n'a un écart < 30 pts.

**MAIS trois nuances destructrices pour le produit :**
1. **Le centre-droit est un magma indiscernable.** DEM / EPR / HOR / LIOT / DR (leg 17) scorent **89–97 % entre eux** —
   la congruence ne les sépare pas. Idem RE / DEM / HOR / LR en leg 16 (94–100 %). Le reveal discrimine *gauche vs reste*,
   beaucoup moins *au sein du bloc de gouvernement*.
2. **Le corpus est 100 % de lois ADOPTÉES** (159/159). « Toujours-pour » et « suiveur-de-la-majorité-AN » sont donc le
   MÊME citoyen, qui score **100 % avec DEM, 97 % EPR, mais 43 % LFI**. La congruence mesure en partie « soutenez-vous la
   majorité qui gouverne ? » plus que le positionnement idéologique fin. Un béni-oui-oui ressemble à un centriste de pouvoir.
3. **Le dénominateur est une bombe.** 22–31 % des paires partagent < 10 lois ; un « 100 % sur 1 loi » (Alexandra Martin,
   EPR) se classe #25 quand un « 83 % sur 53 lois » (Marine Hamelet, RN) se classe #340. Sans plancher de dénominateur,
   le classement est du bruit en tête.

---

## §1 — La formule pinnée (implémentée telle quelle, aucune autre)

```
citoyen sur loi L : v ∈ {-2, -1, +1, +2}        (abstention / skip EXCLUS)
député au vote de réf de L : pour -> +1 ; contre -> -1   (abstention / nonvotant / absent EXCLUS du score)
paire (citoyen, député) sur les lois où les DEUX ont une valeur :
    accord  si sign(v) == sign(dir)
    poids   = |v|
    congruence = Σ(poids des accords) / Σ(poids des lois comptées)
    + on conserve n = nombre de lois comptées (le dénominateur)
```

Source des directions : `Scrutin.positions_nominales()` (groupe_ref = groupe au moment du vote) sur les
**votes de référence** (`numero == ref_numero`) des 159 lois du corpus. Les positions `pour`/`contre` deviennent ±1 ;
`abstention` et `nonvotant` ne produisent **aucune entrée** (exclusion stricte conforme spec).

**Étendue de la matrice :** 605 députés distincts apparaissent dans les votes de réf leg 16, 636 en leg 17
(> 577 car des députés ont été remplacés en cours de mandat — partielles, ministres, démissions).

---

## Note méthodo — libellés de groupes leg 16

Les codes `PO800xxx` de la 16e législature **ne sont pas** dans `amo10-17/json/organe/` (qui ne couvre que la 17e).
Mapping établi par **identification nominale** sur le scrutin n° 3966 (le plus participé de la 16e, 569 votants),
en reconnaissant les députés ré-élus :

| PO | Membres (~) | Groupe | Députés identifiants |
|---|---|---|---|
| PO800538 | 170 | **RE** | Le Grip, Klinkert, Rixain |
| PO800520 | 88 | **RN** | M. Le Pen, Chenu, Odoul |
| PO800490 | 75 | **LFI** | Autain, Bernalicis, Prud'homme |
| PO800508 | 62 | **LR** | Herbillon, Breton, Gosselin |
| PO800484 | 50 | **DEM** | Vigier, Balanant, Mette |
| PO830170 | 31 | **SOC** | Faure, Garot, Battistel |
| PO800514 | 30 | **HOR** | Marcangeli, Magnier, Bouyx |
| PO800526 | 22 | **ECO** | Sas, Chatelain, Thierry |
| PO800532 | 22 | **LIOT** | de Courson, Naegelen, Serva |
| PO800502 | 22 | **GDR** | Sansu, Peu, Lecoq |
| PO793087 | 7 | **NI** | Habib, Besse |

---

## §4.1 — DÉPUTÉ-COMME-CITOYEN : le test de discrimination

On prend **chaque député** comme un « citoyen » (ses propres votes : pour → +2, contre → −2) et on calcule sa
congruence avec **chaque groupe** (via la position majoritaire du groupe, méthode b). On mesure l'**écart** =
congruence(meilleur groupe) − congruence(pire groupe), sur les 10 groupes principaux, pour les députés ayant ≥ 5 lois
communes avec ≥ 2 groupes.

| Métrique | leg 16 | leg 17 |
|---|---|---|
| n députés évalués | 594 | 612 |
| écart **médian** | **0,667** (66,7 pts) | **0,667** (66,7 pts) |
| écart moyen | 0,640 | 0,666 |
| écart p10 / p25 | 0,33 / 0,55 | 0,46 / 0,57 |
| écart p75 / p90 | 0,75 / 0,86 | 0,77 / 0,86 |
| écart min / max | 0,02 / 1,00 | 0,03 / 1,00 |
| **% écart < 15 pts** | **0,0 %** | **0,0 %** |
| % écart < 30 pts | 0,8 % | 0,3 % |
| **groupe d'origine = #1** | **52,4 %** | **64,9 %** |
| groupe d'origine ∈ top-2 | **86,0 %** | **85,5 %** |

**Lecture : le reveal discrimine fortement.** Le critère d'échec posé par le mandat (« écart médian < ~15 pts ⇒ ne
discrimine pas ») est massivement réfuté : l'écart médian est de **66,7 pts**, et **0,0 %** des députés ont un écart
< 15 pts. Un député de gauche-comme-citoyen score bien à gauche, mal à droite, et inversement.

### Exemples nominaux réels (leg 17)

**Mathilde Panot (LFI-NFP)** comme citoyenne — gradient monotone parfait, écart 81 pts :
`LFI-NFP 100 % · ECOS 87 % · GDR 82 % · SOC 54 % · EPR 32 % · DEM 29 % · RN 29 % · HOR 26 % · LIOT 23 % · DR 19 %`

**Marine Le Pen (RN)** comme citoyenne — écart 70 pts, sommet RN/droite, creux gauche :
`RN 100 % · DR 83 % · LIOT 78 % · DEM 74 % · HOR 74 % · EPR 70 % · SOC 50 % · ECOS 41 % · GDR 39 % · LFI-NFP 30 %`

**Éric Ciotti (LR, leg 16)** — écart 83 pts :
`LR 100 % · DEM 93 % · RE 93 % · HOR 93 % · RN 69 % · LIOT 62 % · GDR 45 % · ECO 27 % · LFI 17 %`

**Boris Vallaud (SOC, leg 17)** — le cas « pivot » qui dévoile la nuance n°2 :
`SOC 97 % · DEM 83 % · EPR 83 % · HOR 80 % · LIOT 77 % · DR 77 % · GDR 74 % · ECOS 72 % · RN 59 % · LFI-NFP 54 %`
Vallaud a un écart de seulement 43 pts et son **pire** groupe est… LFI-NFP. Le SOC vote « pour » beaucoup de lois
adoptées (compromis), donc un citoyen-SOC ressemble à un citoyen de gouvernement. C'est l'angle mort du corpus
« 100 % adopté » (cf. §4.4).

### La matrice GROUPE × GROUPE (position majoritaire vs position majoritaire), leg 17

Ligne = citoyen-groupe (votes majoritaires, ±2) ; colonne = direction majoritaire du groupe. En % de congruence.

|          | LFI | GDR | ECOS | SOC | DEM | EPR | HOR | LIOT | DR | RN |
|----------|----:|----:|----:|----:|----:|----:|----:|----:|----:|----:|
| **LFI-NFP** | 100 | 82 | 87 | 62 | 43 | 43 | 40 | 40 | 38 | 45 |
| **GDR**     | 82 | 100 | 98 | 85 | 62 | 62 | 62 | 62 | 60 | 60 |
| **ECOS**    | 87 | 98 | 100 | 82 | 61 | 61 | 61 | 61 | 59 | 60 |
| **SOC**     | 62 | 85 | 82 | 100 | 84 | 84 | 84 | 84 | 82 | 71 |
| **DEM**     | 43 | 62 | 61 | 84 | 100 | **97** | **97** | 92 | **95** | 87 |
| **EPR**     | 43 | 62 | 61 | 84 | **97** | 100 | **97** | 89 | 92 | 85 |
| **HOR**     | 40 | 62 | 61 | 84 | **97** | **97** | 100 | 92 | **95** | 85 |
| **LIOT**    | 40 | 62 | 61 | 84 | 92 | 89 | 92 | 100 | **97** | 84 |
| **DR**      | 38 | 60 | 59 | 82 | **95** | 92 | **95** | **97** | 100 | 88 |
| **RN**      | 45 | 60 | 60 | 71 | 87 | 85 | 85 | 84 | 88 | 100 |

**Trois blocs sautent aux yeux :**
- **Bloc gauche** (LFI / GDR / ECOS / SOC) : cohésion interne moyenne 83 %, min 62 % (LFI↔SOC).
- **Bloc centre-droit** (DEM / EPR / HOR / LIOT / DR) : cohésion interne moyenne **94 %**, min 89 % — **quasi indiscernable**.
- **RN** : isolé, mais plus proche du centre-droit (84–88 %) que de la gauche (45–60 %).

La frontière gauche/centre-droit est franche (LFI vs DR = 38 %). La frontière à l'**intérieur** du bloc de gouvernement
est inexistante. La matrice leg 16 raconte la même histoire (RE/DEM/HOR = 99–100 % entre eux ; LFI vs RE = 45 %).

---

## §4.2 — Congruence par GROUPE : deux méthodes, divergent-elles ?

La spec ne tranche pas entre (a) **moyenne des congruences paire-à-paire des membres** et (b) **position majoritaire du
groupe puis congruence**. On fixe un citoyen de référence = la position médiane (majoritaire) du groupe lui-même, puis :
(a) moyenne sur les membres de congruence(citoyen, membre) ; (b) congruence(citoyen, majorité-du-groupe). L'écart (b)−(a)
mesure la cohésion interne / l'effet d'agrégation.

| Groupe (leg 17) | (a) moy. paire-à-paire | (b) majorité | Δ (b−a) | n membres |
|---|---:|---:|---:|---:|
| LFI-NFP | 1,000 | 1,000 | 0,000 | 72 |
| RN | 1,000 | 1,000 | 0,000 | 127 |
| HOR | 0,995 | 1,000 | 0,005 | 41 |
| SOC | 0,993 | 1,000 | 0,007 | 67 |
| DR | 0,992 | 1,000 | 0,008 | 60 |
| DEM | 0,991 | 1,000 | 0,009 | 39 |
| ECOS | 0,989 | 1,000 | 0,011 | 38 |
| EPR | 0,988 | 1,000 | 0,012 | 110 |
| GDR | 0,987 | 1,000 | 0,013 | 18 |
| **LIOT** | **0,942** | 1,000 | **0,058** | 25 |

**Conclusion :** les deux méthodes **convergent presque parfaitement** (Δ ≤ 1,3 pt sauf LIOT). La méthode (b) majore
mécaniquement (b ≥ a) car la majorité est par définition l'opinion la plus alignée. **L'exception est LIOT** (Δ = 5,8 pts) :
groupe « attrape-tout » sans discipline, ses membres divergent de leur propre majorité. **Recommandation produit :** méthode
(b) — position majoritaire — est plus stable, plus interprétable, et ne dépend pas de l'effectif. La méthode (a) ne se
justifie que si l'on veut pénaliser explicitement les groupes indisciplinés (LIOT, NI).

---

## §4.3 — LE PROBLÈME DU DÉNOMINATEUR

### Distribution du nombre de lois comptées par paire (citoyen-député × député)

Échantillon de paires de députés (≤ 30 000 par leg, graine 42) ; n = lois où les **deux** ont voté pour ou contre.

| Métrique | leg 16 (/93 lois) | leg 17 (/66 lois) |
|---|---:|---:|
| paires échantillonnées | 30 000 | 30 000 |
| n médian | 12 | 16 |
| n moyen | 12,8 | 15,0 |
| n min | 0 | 0 |
| p10 | 5,0 | 3,0 |
| p25 / p75 | 9 / 17 | 11 / 20 |
| p90 / n max | 21 / 54 | 23 / 46 |
| **% paires avec n < 5** | **8,3 %** | **11,7 %** |
| **% paires avec n < 10** | **30,8 %** | **22,4 %** |

Le citoyen ne vote pas sur 159 lois : il vote sur celles qu'il connaît. La **médiane de chevauchement est ~12–16 lois**,
mais une paire sur 4–3 partage **moins de 10 lois**. À ces volumes, la congruence est très bruitée.

### Instabilité du classement (citoyen = position majoritaire RE/EPR)

On classe tous les députés par congruence avec le citoyen « majorité du grand groupe de gouvernement ».

| Métrique | leg 16 (cit. RE) | leg 17 (cit. EPR) |
|---|---:|---:|
| députés classés | 605 | 636 |
| députés à **congruence = 100 %** | **269** | **131** |
| … dont avec n < 10 lois | 19 | **33** |
| … dont avec n ≥ 20 lois | 212 | 78 |
| Top-20 (tri par cong. seule, départage aléatoire) avec n < 10 | 1 / 20 | **9 / 20** |

**Le pathos en un exemple (leg 17) :** **Alexandra Martin (Gironde, EPR)** affiche **100 % sur 1 seule loi** et se classe
**#25** ; **Marine Hamelet (RN)**, à **83 % sur 53 lois**, se classe **#340**. (Ici c'est cohérent que la RN soit basse —
on mesure la congruence avec EPR — mais le scandale est le 100 %/1-loi qui squatte le haut du tableau.)
**Leg 16 :** PA720170 (RE, député parti — d'où l'absence de nom) = **100 % sur 2 lois**, classé #218, devant un 81 %/58 lois (#365).

**Probabilité de faux 100 %.** Un citoyen réellement aligné à 82 % avec un député affiche **100 %** par pur hasard avec
probabilité 0,82^k : **55 % sur 3 lois**, 37 % sur 5 lois, 14 % sur 10 lois. Autrement dit, **un votant ordinaire à 82 %
a une chance sur deux d'être affiché « 100 % de congruence » s'il n'a renseigné que 3 lois.** Le « 100 % sur 3 lois écrase
le 82 % sur 60 lois » du mandat est exact et omniprésent.

**Recommandation produit :** imposer un **plancher de dénominateur** (n ≥ 10–15) avant d'afficher un score, OU afficher un
intervalle de confiance / rétrécir le score vers 50 % quand n est petit (shrinkage bayésien). Sans cela, tout
« classement des élus les plus proches de vous » est dominé par des artefacts à faible n.

---

## §4.4 — ARCHÉTYPES SYNTHÉTIQUES (sanity check)

Citoyens synthétiques sur les lois de réf, congruence vs position majoritaire de chaque groupe (leg 17) :

| Archétype | LFI | GDR | ECOS | SOC | DEM | EPR | HOR | LIOT | DR | RN | écart |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| toujours_pour | 43 | 62 | 61 | 84 | **100** | 97 | 97 | 92 | 95 | 87 | 57 |
| toujours_contre | 57 | 38 | 39 | 16 | **0** | 3 | 3 | 8 | 5 | 13 | 57 |
| suiveur_majorité_AN | 43 | 62 | 61 | 84 | 100 | 97 | 97 | 92 | 95 | 87 | 57 |
| opposant_majorité_AN | 57 | 38 | 39 | 16 | 0 | 3 | 3 | 8 | 5 | 13 | 57 |
| **aléatoire_graine42** | 39 | 50 | 48 | 60 | 62 | 59 | 62 | 61 | 64 | 50 | **25** |

**Trois enseignements de sanity :**
1. **`aléatoire` se comporte comme prévu** : congruence ~39–64 %, centrée autour de 50 %, écart inter-groupes faible (25 pts,
   le résidu venant du déséquilibre pour/contre du corpus). Le score ne « voit » aucun signal là où il n'y en a pas. ✓
2. **`toujours_pour` ≡ `suiveur_majorité_AN`** (lignes identiques) — parce que **les 159 lois du corpus sont toutes
   adoptées** (93/93 en leg 16, 66/66 en leg 17). Un « toujours-oui » est mécaniquement un « suiveur de la majorité ».
3. **`toujours_pour` n'est PAS neutre** : il score **100 % avec DEM, 97 % EPR/HOR, 95 % DR… mais 43 % LFI**. Le béni-oui-oui
   est classé comme un parfait soutien du gouvernement. C'est le **biais structurel** du périmètre : congruence ≈
   « soutien à la majorité qui fait passer les lois ». Pour mesurer le clivage gauche/droite *symétriquement*, il faudrait
   intégrer des votes rejetés ou des propositions d'opposition — absents du corpus « lois promulguées ».

---

## Limites & honnêteté

- **Trou AMO10 (députés partis).** Les `acteurRef` des scrutins incluent des élus non présents dans `amo10-17` (dump des
  actifs seulement) : **35,9 % en leg 16** (217/605 — normal, législature close, beaucoup remplacés) et **9,4 % en leg 17**
  (60/636). Ces députés n'ont **pas de nom** (apparaissent comme `PA######`) mais leurs votes et leur groupe-au-moment-du-vote
  sont **présents** dans la ventilation, donc leur congruence est calculable. Seul l'affichage nominal est dégradé.
- **Corpus 100 % adopté** (cf. §4.4) : biais pro-majorité non corrigeable sans élargir le périmètre.
- **Indiscernabilité du bloc de gouvernement** : DEM/EPR/HOR/LIOT/DR (leg 17) à 89–97 % — la congruence ne sépare pas le
  centre-droit. Un utilisateur centriste recevra un quasi-ex-æquo entre 5 groupes.
- **Position majoritaire vs unanimité** : sur les rares lois où un groupe se divise quasi 50/50, `maj_dir = None` (la loi
  est exclue pour ce groupe). C'est conservateur et conforme à l'esprit « exclure l'ambigu ».
- **Aucune pondération temporelle** : un vote de 2022 pèse comme un vote de 2024 (leg 16). La spec ne le demande pas.

---

## Verdict de conception

**Le reveal de congruence FONCTIONNE comme discriminateur gauche/droite** (écart médian 67 pts, 0 % sous 15 pts,
matrice en blocs nette). Ce n'est pas une machine à 80 %. **Mais il faut le ceinturer de deux garde-fous, sinon il ment :**

1. **Plancher de dénominateur obligatoire** (n ≥ 10–15) ou shrinkage : sans ça, 22–31 % des appariements reposent sur < 10
   lois et le haut du classement est saturé de faux 100 %. **C'est le risque produit n°1.**
2. **Communiquer l'angle mort « bloc de gouvernement »** : la congruence sépare gauche / centre-droit / RN, mais **pas** les
   composantes du bloc présidentiel + LR (DEM≈EPR≈HOR≈DR à 90–97 %). Ne pas survendre une granularité que la donnée n'a pas.
3. **Assumer le biais pro-majorité** dû au périmètre 100 %-adopté (« toujours-oui » = soutien parfait au gouvernement).
   Si l'objectif est de positionner sur l'axe gauche/droite *symétriquement*, le corpus actuel sur-récompense le vote « pour ».

Méthode d'agrégation par groupe : **utiliser la position majoritaire** (méthode b), stable et indépendante de l'effectif ;
la moyenne paire-à-paire (a) ne diverge significativement que pour les groupes indisciplinés (LIOT, +5,8 pts).
