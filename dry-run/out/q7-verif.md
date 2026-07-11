# Q7-verif — Vérification adverse INDÉPENDANTE du chiffre-clé de `q7-simulation`

**Date :** 2026-06-13. **Vérificateur :** adverse. **Cible :** le headline de `out/q7-simulation.md`.
**Code de vérif :** `scripts/q7-verif.py` (n'utilise NI `q7-simulation.py`, NI `anlib.positions_nominales()`).
**Chiffres machine :** `out/q7-verif.json`.

---

## Chiffre-clé contesté

> « Le reveal discrimine fortement : **écart de congruence médian de 66,7 points** entre meilleur et pire groupe pour
> un député-comme-citoyen (**leg 16 ET leg 17**), avec **0,0 %** des députés sous le seuil d'échec de 15 pts. »

## Verdict : **CONCORDE — chiffre confirmé au chiffre près. Confiance haute.**

| Métrique (analyse 1) | Headline / `q7-simulation.json` | **Recalcul indépendant** | Concorde |
|---|---:|---:|:--:|
| écart médian leg 16 | 0,6667 (66,7 pts) | **0,6667** | ✅ |
| écart médian leg 17 | 0,6667 (66,7 pts) | **0,6667** | ✅ |
| % écart < 15 pts (leg 16 / 17) | 0,0 % / 0,0 % | **0,0 % / 0,0 %** | ✅ |
| % écart < 30 pts (leg 16 / 17) | 0,8 % / 0,3 % | **0,8 % / 0,3 %** | ✅ |
| n députés évalués (leg 16 / 17) | 594 / 612 | **594 / 612** | ✅ |
| écart moyen (leg 16 / 17) | 0,640 / 0,666 | **0,6401 / 0,6662** | ✅ |
| écart min / max leg 16 | 0,2302 / 1,00 | **0,2302 / 1,00** | ✅ |
| écart p10 / p25 / p75 / p90 leg 17 | 0,469 / 0,589 / 0,762 / 0,846 | **0,469 / 0,589 / 0,762 / 0,846** | ✅ |
| groupe d'origine #1 (leg 16 / 17) | 52,4 % / 64,9 % | **52,4 % / 64,9 %** | ✅ |
| groupe d'origine ∈ top-2 (leg 16 / 17) | 86,0 % / 85,5 % | **86,0 % / 85,5 %** | ✅ |
| trou AMO10 (leg 16 / 17) | 35,9 % / 9,4 % | **35,9 % (217/605) / 9,4 % (60/636)** | ✅ |

**Toutes les métriques de l'analyse 1 sont reproduites à la 4e décimale.**

---

## Méthode d'indépendance (ce que j'ai fait différemment)

1. **Lecture des scrutins BRUTS.** Je n'appelle pas `anlib.positions_nominales()`. J'ouvre directement les
   `data/scrutins-{16,17}/json/VTANR5L{leg}V*.json`, je re-parse `ventilationVotes.organe.groupes.groupe[]`
   (avec mon propre `as_list`), et je classe pours/contres/abstentions/nonVotants moi-même.
2. **Seule entrée figée consommée :** la liste des 159 votes de référence `(leg, ref_numero)` extraite de
   `out/corpus.json` — c'est l'input figé que la consigne m'autorise à consommer sans le re-dériver.
3. **Re-implémentation à neuf** de : direction du député (±1), citoyen (±2), majorité de groupe par loi
   (égalité → exclu), congruence `Σ|v|accords / Σ|v|comptés`, écart max−min sur 10 groupes, médiane.

**Contrôles d'intégrité passés :**
- **159/159 scrutins de référence retrouvés** dans les fichiers bruts (93 leg 16, 66 leg 17 ; 0 manquant).
- **0 événement « acteur compté deux fois dans le même scrutin »** (`dup_actor_in_scrutin = {16:0, 17:0}`) →
  pas de double-compte par objet-vs-tableau ou par ventilation redondante.
- **159/159 lois `sort = adopté`** (93/93 leg 16, 66/66 leg 17) → la métrique `corpus_pct_lois_adoptees:100` est exacte.

---

## Ce que j'ai cherché à casser (et qui tient)

### 1. « 66,7 = 2/3 trop joli, c'est un hardcode ou un bug »  → NON, c'est structurel

En calculant les écarts en **fractions exactes** (les poids `2` se simplifient, les écarts sont des différences de
ratios d'entiers : 5/7, 3/5, 1/2, 4/5…), la médiane tombe sur **exactement 2/3** dans les DEUX législatures. Ce n'est
pas un hasard suspect : **2/3 est le mode** des écarts (la valeur la plus fréquente) dans les deux corpus.

| Valeur d'écart exacte la + fréquente | leg 16 | leg 17 |
|---|---:|---:|
| **2/3** (= 0,6667) | **34 députés (5,7 %)** | **38 députés (6,2 %)** |
| 5/7 / 3/5 / 1/2 / 4/5 (suivantes) | 19 / 18 / 17 / 15 | 11 / 14 / 13 / 15 |

Le voisinage immédiat de la médiane (indices médian−2 … médian+2) vaut **2/3 partout** dans les deux legs : la médiane
est plantée au cœur du cluster 2/3, pas sur une frontière instable. La coïncidence leg 16 ≡ leg 17 vient de ce que
2/3 domine la distribution des deux côtés — pas d'un report de chiffre.

### 2. « Le mapping de groupes leg 16 (custom, PO→label) fabrique le résultat »  → NON

Test de sensibilité : je rejette le mapping documenté et je prends les **10 PO bruts les plus nombreux** comme
groupes (aucune fusion/renommage). Médiane de l'écart : **0,6667 (leg 16) et 0,6667 (leg 17)** — identique.
Le chiffre ne dépend pas du libellé des groupes. (Le mapping n'affecte que `own_top1` : 52,4 %→76,9 % en leg 16,
car en PO brut l'auto-groupe est trivialement identifié ; mais l'**écart médian**, qui est l'objet du headline, ne bouge pas.)

### 3. « Le seuil n ≥ 5 lois communes est arbitraire et pilote la médiane »  → NON, robuste

| seuil min_n | médiane leg 16 | médiane leg 17 |
|---|---:|---:|
| 1 | 0,6778 | 0,6765 |
| 3 | 0,6750 | 0,6667 |
| **5 (retenu)** | **0,6667** | **0,6667** |
| 10 | 0,6552 | 0,6667 |
| 15 | 0,6458 | 0,6667 |

La médiane reste dans la bande **0,646–0,678** quel que soit le seuil. Le « ~66 points » survit à tout choix
raisonnable. Aucun effet de bord du seuil.

### 4. « discrimine fortement » est-il survendu ?  → NON

Le groupe d'origine du député tombe dans la **moitié basse** du classement seulement **0,4 % (leg 16) / 0,3 % (leg 17)**
du temps. Distribution du rang du groupe d'origine (leg 17) : `#1=397, #2=126, #3=24, #4=27, #5=7, #6=2`. Le gradient
gauche↔droite est réel.

---

## Exemples nominaux recalculés (concordent avec le rapport)

| Député (leg) | Mon écart | Meilleur | Pire | Rapport |
|---|---:|---|---|---|
| **Mathilde Panot** (LFI-NFP, 17) | 0,8065 | LFI-NFP 1,00 | DR 0,19 | « écart 81 pts », LFI 100 % / DR 19 % ✅ |
| **Marine Le Pen** (RN, 17) | 0,700 | RN 1,00 | LFI-NFP 0,30 | « écart 70 pts », RN 100 % / LFI 30 % ✅ |
| **Boris Vallaud** (SOC, 17) | 0,4282 | SOC 0,967 | LFI-NFP 0,538 | « écart 43 pts, pire = LFI-NFP » ✅ |
| **Éric Ciotti** (LR, 16) | 0,8333 | LR 1,00 | LFI 0,167 | « écart 83 pts », LR 100 % / LFI 17 % ✅ |

(Écarts de gradient < 1 pt vs le rapport, dus aux arrondis d'affichage du rapport ; structurellement identiques.)

---

## Limites de ma vérification (honnêteté)

- Je **consomme** la liste des votes de référence du corpus figé (input autorisé). Je n'ai pas re-dérivé le funnel
  scrutin↔dossier ni la règle « dernier vote AN d'ensemble » — ce n'est pas l'objet de ce chiffre-clé (couvert par q1).
  Si le `ref_numero` d'une loi était faux en amont, mon recalcul hériterait de l'erreur ; mais les 159 numéros pointent
  bien vers 159 scrutins existants, tous `adopté`, ce qui est cohérent avec la spec.
- Le headline ne porte QUE sur l'analyse 1 (écart médian + % < 15 pts + top1/top2). Je l'ai vérifié exhaustivement.
  Les nuances §4.2–§4.4 (matrice groupe×groupe, dénominateur, archétypes) ne sont pas re-vérifiées ici ligne à ligne,
  mais les exemples nominaux et le sort 100 %-adopté que j'ai recalculés les corroborent.

---

## Conclusion

Le chiffre-clé **« écart de congruence médian de 66,7 points (leg 16 ET leg 17), 0,0 % sous 15 pts »** est
**exact, reproductible par une méthode indépendante, et robuste** au mapping de groupes comme au seuil de dénominateur.
66,7 pts = exactement **2/3**, qui est la valeur d'écart la plus fréquente dans les deux législatures — un résultat
structurel, pas un artefact. **Aucun écart trouvé.**
