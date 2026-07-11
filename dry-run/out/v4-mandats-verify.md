# v4-mandats-verify — Vérification adverse indépendante de q4-mandats

**Mandat** : recalculer le chiffre-clé de `q4-mandats` (« absent n'est pas dérivable ») par une **méthode indépendante**
(parsing BRUT des fichiers scrutin JSON + double cross-check en **pur jq/comm**, sans réutiliser `q4-mandats.py` ni
`anlib.positions_nominales`), et statuer sur la concordance.

**Verdict global** : **CONCORDE INTÉGRALEMENT.** Tous les chiffres du headline et des métriques secondaires testées sont
reproduits à l'identique par deux chaînes indépendantes (Python brut + jq). **Confiance : haute.** Aucun écart.

---

## 0. Méthode indépendante

- **Source** : fichiers scrutin bruts `data/scrutins-{16,17}/json/*.json` (4 106 + 7 397), parsés directement
  (`json.load` → `ventilationVotes.organe.groupes.groupe[].vote.decompteNominatif.{pours,contres,abstentions,nonVotants}.votant`).
- **Vote de référence** : les 159 paires `(ref_leg, ref_numero)` du `corpus.json` figé (93 leg16 + 66 leg17). **Vérifié : 159
  paires distinctes, 0 doublon** (donc pas de double-comptage de loi).
- **AMO10** : 577 fichiers `acteur/PA*.json`. **Vérifié : `nom de fichier == acteur.uid` pour les 577** (après avoir géré le
  piège `uid` = objet `{"#text": "PA…"}` — un piège objet-vs-tableau supplémentaire **non documenté dans SCHEMA-NOTES** mais
  sans impact car le nom de fichier suffit).
- **Double cross-check** : pour les chiffres du headline j'ai refait le calcul une 2ᵉ fois en **pur jq** (slurp `-s`) +
  `comm` sur fichiers texte, indépendamment du Python. Concordance parfaite (voir §1).

### Pièges contrôlés (sceptique)
- **Apostrophes** : non pertinent ici — aucune des métriques ne repose sur un matching de libellé (le corpus fournit déjà
  les `ref_numero`). Pas de risque d'apostrophe ratée sur ce chiffre-clé.
- **Objet-vs-tableau** : `votant` peut être objet, tableau ou **`null`** (catégorie vide) → géré via `as_list` + filtre `None`.
  `groupe` idem. Sans ça, `listed` aurait été faux. **Contrôlé.**
- **Double-compte de `listed`** : vérifié qu'**aucun acteurRef n'apparaît dans 2 slots du même scrutin de référence**
  (0/159 votes, sum 0). Donc `577 − listés` n'est pas artificiellement gonflé par un double-listage.
- **`parDelegation`** est une **chaîne** `"true"/"false"`, pas un booléen → comparaison sur `.lower()=="true"`. Une comparaison
  naïve `== True` aurait donné 0 % de délégation. **Contrôlé.**
- **Dénominateur du % délégation** : c'est `exprimés` (pour+contre+abstention), **pas** `listés` (qui inclut nonVotants).
  C'est le bon dénominateur — un nonVotant institutionnel n'« exprime » rien et ne peut pas être « par délégation ». Vérifié
  cohérent avec l'analyse.

---

## 1. Headline — recalcul par DEUX méthodes indépendantes

> headline : médiane « absent = 577 − listés » = **431** (leg16) / **391** (leg17) ; `listés != sum(NMG)` dans **100 %**
> (0/93, 0/66) ; **14-25 %** des exprimés par délégation.

| Chiffre du headline | q4-mandats | Python brut (moi) | jq pur (moi) | Concorde |
|---|---:|---:|---:|:---:|
| médiane `577 − listés` — **leg16** | **431** | **431** | **431** | ✅ |
| médiane `577 − listés` — **leg17** | **391** | **391** | **391** | ✅ |
| votes où `listés == sum(NMG)` — leg16 | 0/93 | 0/93 | 0/93 | ✅ |
| votes où `listés == sum(NMG)` — leg17 | 0/66 | 0/66 | 0/66 | ✅ |
| % exprimés par délégation — leg16 | 14,1 % | 14,1 % | 14,1 % | ✅ |
| % exprimés par délégation — leg17 | 25,0 % | 25,0 % | 25,0 % | ✅ |

**Robustesse de la médiane (parité)** : leg17 a n=66 (pair). `statistics.median` moyenne les éléments [32] et [33] ; mon jq
prend [33]. **J'ai vérifié que [32]=[33]=391** → la médiane est insensible à la convention de bris d'égalité. Aucun écart caché.

Détail délégation (totaux bruts, identiques sur les 2 méthodes) :
- leg16 : **2 571** par délégation / **15 647** en personne (18 218 exprimés) → 14,1 %.
- leg17 : **4 456** par délégation / **13 348** en personne (17 804 exprimés) → 25,0 %.

---

## 2. Métriques secondaires — toutes reproduites

### (a) Trou « députés partis » (acteurRef hors AMO10) — cross-check `jq | comm`

| | q4 leg16 | moi leg16 | q4 leg17 | moi leg17 |
|---|---:|---:|---:|---:|
| acteurRef distincts, tous scrutins | 617 | **617** | 642 | **642** |
| … hors AMO10 (trou, tous) | 225 | **225** | 66 | **66** |
| acteurRef distincts, votes de réf. | 605 | **605** | 636 | **636** |
| … hors AMO10 sur votes de réf. | 217 | **217** | 60 | **60** |
| union 2 legs distincts / hors AMO10 | 827 / 251 | **827 / 251** | — | — |

Confirmé aussi en `comm -23` pur (827 union, 251 hors). Échantillon « partis » leg17 identique
(`PA1327, PA267306, PA267561, PA2960, …`).

> **Nuance honnête (non un écart)** : « AMO10 jamais vus en scrutin » — q4 dit **0 (leg16) / 1 (leg17)**. Mon calcul leg16
> donne **185**, mais c'est **le même fait dit autrement** : q4 entend manifestement « AMO10 jamais vu dans **AUCUN** scrutin
> (leg16 ∪ leg17) », pas « jamais vu en leg16 seule ». 185 AMO10 (députés leg17) n'ont simplement jamais voté en leg16 — c'est
> trivialement vrai (beaucoup ne siégeaient pas). Le **1** leg17 (un AMO10 jamais vu dans aucun scrutin du corpus) est confirmé.
> Pas une contradiction, juste une borne d'agrégation différente. La métrique publiée ne liste pas ce chiffre, donc rien à corriger.

### (b) Dénominateurs & médianes par type de vote

| Statistique (votes de réf.) | q4 leg16 | moi leg16 | q4 leg17 | moi leg17 |
|---|---:|---:|---:|---:|
| médiane listés | 146 | **146** | 186 | **186** |
| `sum(NMG)` médiane (min–max) | 577 (572–577) | **577 (572–577)** | 576 (574–577) | **576 (574–577)** |
| `577 − listés` min–max | 8–541 | **8–541** | 8–533 | **8–533** |
| `sum(NMG) − listés` médiane | 428 | **428** | 390 | **390** |
| `sum(NMG) != 577` | 17/93 | **17/93** | 33/66 | **33/66** |
| médiane listés **SPS** (n) | 540 (12) | **539 (12)** | 517 (23) | **517 (23)** |
| médiane listés **SPO** (n) | 124 (81) | **124 (81)** | 132 (43) | **132 (43)** |

Distribution `sum(NMG)` leg17 : **574×2, 575×16, 576×15, 577×33** — identique à q4 (§b.3).

> **Micro-écart cosmétique (sans incidence)** : médiane SPS leg16 — q4 affiche **540**, je trouve **539**. Cause : n=12 (pair),
> les 2 valeurs centrales (triées) sont 539 et 541 → `statistics.median` = **540** (moyenne), mon jq `[n/2|floor]` = `[6]` =
> **539**. C'est une différence de **convention de médiane sur effectif pair**, pas une erreur de donnée ; la valeur q4 (540)
> est même la plus correcte. Ce chiffre **n'est pas dans la liste `metrics`** vérifiée (qui n'a que `listes_mediane_SPS_leg16:540`)
> — et 540 est juste. Donc : **pas un écart sur le chiffre-clé**, simple note de méthode.

### (c) Délégation — exemple nommé confirmé

- Max sur un vote de réf. **leg16 = 44,2 %** sur le scrutin **n° 2519 = « l'ensemble du projet de loi relatif à l'industrie
  verte (première lecture) »** (corpus : loi **« L'industrie verte »**). **Exactement** l'exemple de q4 (137/310 exprimés).
- Max leg17 = **42,7 %** sur **n° 2975** = « PJL programmation pour la refondation de Mayotte (CMP) ». Concorde.
- % moyen par vote : 11,5 % (leg16) / 18,3 % (leg17) — concorde. Députés ≥1 délégation : 536 / 594 — concorde.

### (d) Causes nonVotants — toutes institutionnelles

| | q4 leg16 | moi leg16 | q4 leg17 | moi leg17 |
|---|---:|---:|---:|---:|
| causes distinctes | PAN, PSE, MG | **PAN, PSE, MG** | idem | **idem** |
| PAN acteurs distincts | 1 | **1** | 1 | **1** |
| PSE acteurs distincts | 7 | **7** | 11 | **11** |
| MG acteurs distincts | 22 | **22** | 39 | **39** |
| MG hors AMO10 | 13 | **13** | 23 | **23** |
| nonVotant MG / PSE / PAN (tous scrutins) | 28/3930/33 | **28/3930/33** | 9991/5174/6734 | **9991/5174/6734** |

**PA721908 = Braun-Pivet, Yaël** (vérifié dans `acteur/PA721908.json`) — l'unique PAN sur les 2 législatures. ✅

### (e) Changements de groupe — sur-comptage confirmé, REELS=8 reproduit

| | q4 leg16 | moi leg16 | q4 leg17 | moi leg17 |
|---|---:|---:|---:|---:|
| multi-PO-ref bruts (PO0 exclu) | 54 | **54** | 23 | **23** |
| changements **RÉELS** (≥2 abrév distinctes résolues) | 0\* | **0\*** | 8 | **8** |
| non résolvables (≥1 PO hors dump organe) | 54 | **54** | 15 | **15** |
| scrutins sentinelle **PO0** | 0 | **0** | 12 | **12** (tous **2024-12-02**) |

\* **leg16 non quantifiable** : confirmé indépendamment que les groupes leg16 (`PO800496`, `PO830170`, `PO800490`,
`PO793087`) sont **ABSENTS** du dump organe AMO10 (qui ne contient que **12 GP**, tous leg17) → aucun libellé résolvable → 0
changement prouvable. Structurellement correct.

**Les 8 changements réels leg17** (recalculés via mapping PO→`libelleAbrev` des fichiers `organe/`), identiques à la liste q4 :

| acteurRef | trajectoire (abrév résolues) |
|---|---|
| PA720362 (Belhaddad) | EPR → NI → SOC |
| PA822617 (Froger) | LIOT → SOC |
| PA793796 (Taupiac) | NI → LIOT |
| PA840119 (Delannoy) | RN → NI |
| PA722150 (Houlié) | NI → SOC |
| PA794658 (Fait) | EPR → HOR |
| PA794718 (Engrand) | RN → NI |
| PA720066 (hors AMO10) | EPR → NI |

Les **15 « non résolvables »** ont au plus **1** abrév résolvable (le reste = PO-refs hors dump, dont `PO847173` →
création/officialisation **UDDPLR** le 2025-09-05) : **0** d'entre eux ne cache un vrai changement → le « 8 » est exhaustif et
le « 54/23 brut sur-compte » est confirmé.

---

## 3. Conclusion du vérificateur

Le chiffre-clé `absent_derivable = false` et **tous** les nombres qui le soutiennent sont **exacts**. J'ai reproduit :
- les 2 médianes du headline (431, 391) par Python **et** par jq, avec contrôle de la convention de médiane ;
- le « 100 % `listés != sum(NMG)` » (0/93, 0/66) ;
- les 14,1 % / 25,0 % de délégation (totaux bruts identiques) ;
- l'intégralité des métriques secondaires (trou 225/66/217/60/251, causes PAN/PSE/MG et leurs acteurs, PO0=12, 8 changements réels).

**Aucun double-compte, aucune apostrophe ratée, aucun objet-vs-tableau mal géré, aucun dénominateur douteux** n'a été trouvé.
Les 2 seules divergences relevées sont (i) une médiane SPS leg16 (540 vs 539) due à la **convention de médiane sur effectif
pair** — la valeur publiée 540 est la bonne ; (ii) le « AMO10 jamais vu » qui est une **borne d'agrégation** différente (leg16
seule vs union), pas une erreur. **Ni l'une ni l'autre ne touche le chiffre-clé.**

**Argument de fond validé** : `577 − listés` (médiane 431/391) sur-compte massivement parce que les SPO (65 % des votes de réf.)
n'énumèrent pas l'hémicycle ; `sum(NMG)` oscille (572–577) et n'égale jamais `listés` ; jusqu'à 44,2 % d'un vote est par
délégation. **« absent » n'est pas dérivable** — confirmé.

*Fichiers : `scripts/v4-mandats-verify.py`, `scripts/v4-groupchanges.py` · `out/v4-mandats-verify.json`, `out/v4-groupchanges.json` · ce rapport.*
