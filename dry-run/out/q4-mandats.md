# q4-mandats — Dérivation de l'absence, trou de données mandats, groupes datés

**Mandat** : valider/tester la revue **§2.2** (« absent » n'existe pas dans la donnée) et **§2.7** (mandats/groupes datés).
**Corpus** : 159 lois jugeables figées (`out/corpus.json`) — 93 leg 16 (close), 66 leg 17 (en cours).
**Vote de référence d'une loi** = scrutin dont `numero == ref_numero` (dernier vote public AN d'ensemble).
**Source d'autorité du groupe** = `groupe_ref` dans la ventilation, c.-à-d. **le groupe au moment du vote**.
**AMO10** = `data/amo10-17/json/acteur/PA*.json` : **577** acteurs = snapshot des députés **actifs** de la leg 17, **sans historique**.

> **Conclusion en une phrase** : « absent » n'est PAS dérivable honnêtement. La donnée listée est partielle (médiane
> ~124-186 députés énumérés par vote de référence), `577 − listés` sur-compte massivement l'absence (médiane **431** leg 16,
> **391** leg 17), `sum(nombreMembresGroupe) != listés` dans **100 %** des votes de référence, **14-25 %** des votes exprimés
> sont **par délégation** (présence physique nulle), et AMO10 ignore **60** (leg 17) / **217** (leg 16) députés qui votent
> pourtant sur les votes de référence. Un indicateur de **participation** (a pris part au scrutin) est calculable ; un
> indicateur de **présence** ne l'est pas.

---

## (a) Trou « députés partis » — acteurRef hors AMO10

AMO10 ne contient que les **577 députés actifs** au moment du dump (snapshot leg 17). Tout député ayant quitté son siège
(démission, nomination au gouvernement, décès, invalidation, remplacement par suppléant après partielle) **disparaît
d'AMO10 mais reste dans les ventilations** des scrutins où il a voté.

| | leg 16 (close) | leg 17 (en cours) |
|---|---:|---:|
| acteurRef distincts — **tous** scrutins | 617 | 642 |
| … dont **dans** AMO10 | 392 | 576 |
| … dont **HORS** AMO10 (trou) | **225** | **66** |
| acteurRef distincts — **votes de référence** | 605 | 636 |
| … **HORS** AMO10 sur votes de référence | **217** | **60** |
| AMO10 jamais vus dans un scrutin | 0 | 1 |

- **Union des deux législatures** : 827 acteurRef distincts, dont **251 hors AMO10**.
- **Leg 16** : le trou est massif (225/617 ≈ 36 %) — logique, AMO10 ne couvre PAS la leg 16, donc tout député leg 16 non
  réélu/encore actif est absent. **Pour la leg 16, AMO10 est quasi inutilisable comme référentiel d'appartenance.**
- **Leg 17** : 66 députés votent mais ne sont pas dans le snapshot actuel (≈ 11 % de 577). Ce sont les « partis » de la
  législature en cours : ministres (mandat suspendu), démissionnaires, sièges repris en partielle.
- Le seul AMO10 « jamais vu en scrutin » (leg 17) est un député entré très tardivement ou n'ayant pris part à aucun scrutin
  d'ensemble du corpus.

**Conséquence directe pour la dérivation d'« absent »** : on ne peut pas faire `membres − présents` car on n'a pas la
liste fiable des **membres à la date du vote**. AMO10 donne 577 *aujourd'hui*, pas la composition historique. Échantillon
d'IDs « partis » leg 17 : `PA1327, PA267306, PA267561, PA2960, PA335758, PA408578, PA605694, PA605991, PA606098, …`
(non présents dans AMO10 → noms non résolvables depuis le snapshot, ce qui est précisément le symptôme du trou).

---

## (b) Peut-on dériver « absent » = (membres AN à la date) − (votants + nonVotants listés) ? — **Non**

Deux dénominateurs candidats : **577** (constante de sièges) ou **`sum(nombreMembresGroupe)`** (membres déclarés par
groupe *au moment du vote*, présent dans la ventilation). Les deux échouent.

### b.1 — `577 − listés` et `sum(NMG) − listés` sur les votes de référence

| Statistique (votes de référence) | leg 16 | leg 17 |
|---|---:|---:|
| Positions nominatives **listées** : médiane (min–max) | 146 (36–569) | 186 (44–569) |
| `sum(nombreMembresGroupe)` : médiane (min–max) | 577 (572–577) | 576 (574–577) |
| **« absent » = 577 − listés** : médiane (min–max) | **431** (8–541) | **391** (8–533) |
| « absent » = sum(NMG) − listés : médiane (min–max) | 428 (8–541) | 390 (6–533) |
| votes où **listés == sum(NMG)** | **0/93** | **0/66** |
| votes où **sum(NMG) != 577** | 17/93 | 33/66 |

**Lecture** : la « dérivation » donnerait une **médiane de 431 absents** (leg 16) pour la loi de référence — c.-à-d. qu'on
déclarerait **les trois quarts de l'Assemblée « absents »** pour la plupart des lois. C'est absurde : sur un **scrutin public
ordinaire (SPO)**, la ventilation nominative n'énumère PAS l'Assemblée entière — elle ne liste que les votants effectivement
décomptés. Le non-listé n'est **pas** une absence prouvée ; c'est un **silence de la donnée**.

### b.2 — Le type de vote pilote tout : SPS vs SPO

| Positions listées (votes de réf.) | leg 16 | leg 17 |
|---|---:|---:|
| **SPS** (solennel) — médiane (min–max) | 540 (148–569) — n=12 | 517 (408–569) — n=23 |
| **SPO** (ordinaire) — médiane (min–max) | 124 (36–433) — n=81 | 132 (44–477) — n=43 |

Sur un **solennel**, ~517-540 députés sont listés (proche de 577) → `577 − listés` ≈ 40-60, vaguement plausible comme
« absents+excusés ». Sur un **ordinaire**, ~124-132 listés → `577 − listés` ≈ 445 : ininterprétable. Or **65 % des votes
de référence sont des SPO** (81/93 leg 16 ; 43/66 leg 17). **Le même calcul d'« absent » change de sens selon que le vote
de référence est solennel ou ordinaire** — donc l'indicateur n'est pas comparable d'une loi à l'autre.

### b.3 — Le dénominateur lui-même n'est pas stable

`sum(nombreMembresGroupe)` (la composition déclarée de l'AN à la date) **n'est pas 577** : il oscille (572–577 leg 16,
574–577 leg 17) et diffère de 577 dans **17/93** et **33/66** votes de référence. Détail leg 17 : NMG=574 (×2), 575 (×16),
576 (×15), 577 (×33). Sièges vacants, ministres comptés/décomptés, partielles en cours : la « taille de l'AN » à un instant
*t* n'est ni 577 ni une constante. **Même le dénominateur officiel de l'AN bouge d'un vote à l'autre.**

> **Verdict (b)** : « absent » n'est dérivable ni par `577 − listés` (faux pour 65 % des votes, type SPO), ni par
> `sum(NMG) − listés` (jamais nul, dénominateur instable). Le « non-listé » mélange absents, excusés, en mission, et
> simplement non-décomptés. **On ne peut pas séparer ces cas avec la donnée disponible.**

---

## (c) Votes par délégation — « présence » est intrinsèquement impropre

`parDelegation=true` signifie que le député **n'était pas physiquement présent** : un collègue a porté son vote (art. 62
du Règlement, délégation de vote). Compter ce vote comme une « présence » est faux par construction.

| Votes **exprimés** (pour/contre/abstention) sur votes de référence | leg 16 | leg 17 |
|---|---:|---:|
| par délégation (total) | 2 571 | 4 456 |
| en personne (total) | 15 647 | 13 348 |
| **% exprimés par délégation** | **14,1 %** | **25,0 %** |
| % moyen par vote de référence | 11,5 % | 18,3 % |
| % max sur un vote de référence | 44,2 % | 42,7 % |
| députés ayant ≥1 vote par délégation (sur votes de réf.) | 536 | 594 |

- En leg 17, **1 vote exprimé sur 4 est une délégation**. Quasiment tous les députés (594) en ont émis au moins une.
- **Exemple nommé** : loi **« L'industrie verte »** (leg 16, scrutin **n° 2519**) — **137 votes sur 310 exprimés (44,2 %)
  par délégation**. Sur ce vote, près de la moitié des « votants » n'étaient pas dans l'hémicycle.

> **Verdict (c)** : un indicateur libellé « présence » serait mensonger jusqu'à ~44 % sur certains votes. Au mieux, on
> mesure une **participation au scrutin** (le vote a été *pris en compte*), pas une présence physique.

---

## (d) Taxonomie des `causePositionVote` des nonVotants

Il n'existe que **3 causes** dans toute la donnée (leg 16 + leg 17), toutes **institutionnelles** — confirmées par
recoupement nominatif :

| Code | Signification (confirmée empiriquement) | Vérification |
|---|---|---|
| **PAN** | Président de l'Assemblée nationale — ne vote pas par tradition | **1 seul acteur** sur les deux législatures : `PA721908` = **Yaël Braun-Pivet** |
| **PSE** | Président de séance — préside, ne prend pas part au vote | 7 (leg 16) / 11 (leg 17) acteurs distincts = vice-présidents rotatifs |
| **MG** | Membre du Gouvernement — mandat de député suspendu | 22 (leg 16) / 39 (leg 17) acteurs ; 23 d'entre eux (leg 17) **hors AMO10** (devenus ministres) |

### Comptes sur les **votes de référence**

| nonVotant par cause (votes de réf.) | leg 16 | leg 17 |
|---|---:|---:|
| PAN | 0 | 57 |
| PSE | 85 | 27 |
| MG | 0 | 66 |
| acteurs distincts PAN / PSE / MG | — / 7 / — | 1 / 8 / 21 |

### Comptes sur **tous** les scrutins (vue d'ensemble)

| nonVotant par cause (tous scrutins) | leg 16 | leg 17 |
|---|---:|---:|
| MG | 28 | 9 991 |
| PSE | 3 930 | 5 174 |
| PAN | 33 | 6 734 |
| acteurs distincts MG / PSE / PAN | 22 / 7 / 1 | 39 / 11 / 1 |

- **MG_actors hors AMO10** : 13 (leg 16) / **23** (leg 17) — confirme que `MG` = ministre (sorti du périmètre député actif).
  Exemples MG identifiables (encore/à nouveau dans AMO10) : **Élisabeth Borne, Laurent Marcangeli, Marc Ferracci, Geneviève
  Darrieussecq, Astrid Panosyan-Bouvet, Yannick Neuder, Olga Givernet, Marie-Agnès Poussier-Winsback**.
- **Aucune cause `causePositionVote` ne signifie « absent »**. Les nonVotants de la donnée sont des **empêchements de
  fonction**, pas des absences. Un député simplement absent ne figure tout bonnement **nulle part** dans la ventilation.

> **Verdict (d)** : les nonVotants PAN/PSE/MG doivent être **exclus du dénominateur** de tout taux (ils ne peuvent
> structurellement pas voter), surtout pas comptés comme « absents ». La donnée ne contient **aucune** catégorie d'absence.

---

## (e) Changements de groupe — `groupe_ref` daté, et sur-comptage à éviter

`groupe_ref` (PO…) est le groupe **au moment du vote** : c'est la bonne source, mais elle est **volatile** dans le temps.

| | leg 16 | leg 17 |
|---|---:|---:|
| députés sous **>1** `groupe_ref` distinct (PO0 exclu) | **54** / 617 (8,8 %) | **23** / 642 (3,6 %) |
| … **changement réel** (libellés d'abrév distincts) | 0\* | **8** |
| … **renommage / churn de PO-ref** (même abrév, PO différents) | 0 | 0 |
| … **non résolvable** (≥1 PO-ref hors snapshot AMO10) | **54** | 15 |

\* **Leg 16 : aucun changement résolvable.** Les organes-groupes de la leg 16 (`PO800496`, `PO830170`, `PO800490`,
`PO793087`, …) **ne sont PAS dans le dump organe AMO10** (leg 17 uniquement) → impossible de mettre un libellé sur ces
refs depuis AMO10. Le motif observé est de surcroît une **oscillation A↔B↔A** récurrente sur tout le groupe socialiste
(ex. **Olivier Faure, Guillaume Garot, Boris Vallaud, Marietta Karamanli, Arthur Delaporte** alternent `PO800496 ↔
PO830170` au fil des scrutins) — quasi certainement un **artefact de publication** (deux PO-refs pour le même groupe
selon les lots de scrutins), **pas 54 mutations individuelles**. Le « 54 » brut **sur-compte** donc le phénomène.

**Leg 17 — 8 changements réels** (libellés distincts, donc mutations authentiques), tous nommés :

| acteurRef | Nom | Trajectoire (groupe au moment du vote) |
|---|---|---|
| PA720362 | **Belkhir Belhaddad** | EPR → NI → SOC |
| PA822617 | **Martine Froger** | LIOT → SOC |
| PA793796 | **David Taupiac** | NI → LIOT |
| PA840119 | **Sandra Delannoy** | RN → NI |
| PA722150 | **Sacha Houlié** | NI → SOC |
| PA794658 | **Philippe Fait** | EPR → HOR |
| PA794718 | **Christine Engrand** | RN → NI |
| PA720066 | (hors AMO10) | EPR → NI |

Les **15 autres** « multi-PO-ref » leg 17 sont du **churn de référence** : p.ex. **8 députés** passent de `PO847173` à
`UDDPLR` — or **UDDPLR (PO872880) a été constitué le 2025-09-05** : c'est une **création/officialisation de groupe**
(les fondateurs gardent leur appartenance, seul le PO-ref change), **pas 8 défections** (ex. Charles Alloncle, Éric
Michoux, Gérault Verny, Matthieu Bloch…).

### Artefact PO0 (sentinelle anonyme)

Sur **12 scrutins** leg 17, **tous datés du 2024-12-02**, le `groupe_ref` de tous les groupes est la sentinelle `PO0`
(groupe au moment du vote **non publié / anonymisé**). Sur ces scrutins, l'appartenance de groupe est **inconnue**. C'est
marginal (12/7 397) mais réel : à exclure de toute agrégation par groupe.

> **Verdict (e)** : `groupe_ref` au moment du vote **est** la bonne source (§2.7 a raison), mais (1) il faut **dater par
> scrutin** et jamais utiliser le mandat « courant » d'AMO10 ; (2) le comptage brut de « changements de groupe »
> **sur-compte** (artefacts de PO-ref, renommages, organes leg 16 non résolvables) — le chiffre honnête de **mutations
> individuelles** est **8 en leg 17** et **non quantifiable en leg 16** faute de référentiel d'organes.

---

## Conclusion — faisabilité d'un indicateur « présence » honnête

**« Absent » n'est PAS dérivable** depuis cette donnée. Cinq raisons cumulatives :

1. **Pas de composition datée** : AMO10 est un snapshot (577) sans historique → la liste des **membres à la date du vote**
   est inconnue (et le dénominateur réel oscille 572–577).
2. **Trou « députés partis »** : **66** acteurRef leg 17 (et **225** leg 16) votent sans figurer dans AMO10.
3. **`listés != sum(NMG)` dans 100 %** des votes de référence : le « non-listé » n'est **pas** une absence prouvée.
4. **Ventilation partielle sur SPO** (médiane ~124-132 listés) → `577 − listés` **surcompte massivement** l'absence, et
   65 % des votes de référence sont des SPO.
5. **Vote par délégation** (jusqu'à **44 %** d'un vote) → un vote « compté » sans présence physique : « présence » est
   conceptuellement faux.

**Ce qui EST honnête et calculable :**

- Un indicateur de **participation au scrutin** (a pris part = pour/contre/abstention), borné par la donnée listée, en
  distinguant **vote en personne vs par délégation**.
- **Exclure** systématiquement du dénominateur les nonVotants institutionnels **PAN / PSE / MG** (ils ne peuvent pas voter).
- Agréger par groupe via **`groupe_ref` au moment du vote** (datage par scrutin), **jamais** via le mandat courant AMO10 ;
  exclure les 12 scrutins `PO0`.
- Ne **pas** publier un « taux d'absence ». Au mieux : « X députés ont pris part à ce scrutin (dont Y par délégation) ; la
  ventilation nominale ne permet pas de déduire les absents. »

**Confirmation de la revue** : §2.2 (« absent » n'existe pas → à NE PAS dériver) et §2.7 (mandats/groupes **datés**, source =
`groupe_ref` au vote) sont **tous deux validés** par la donnée.

---

*Fichiers : script `scripts/q4-mandats.py` · chiffres machine `out/q4-mandats.json` · ce rapport `out/q4-mandats.md`.*
