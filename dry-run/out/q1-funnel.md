# Q1 — Entonnoir du corpus & coût de chaque exclusion

**Mandat :** quantifier le passage *lois promulguées → corpus jugeable* (texte ayant reçu un **scrutin public AN sur l'ensemble**), chiffrer chaque exclusion avec exemples nommés, et juger si le corpus restant est représentatif.
**Confronte :** revue §4 (corpus étroit/biaisé) + §2.5 (ratifications).
**Source :** corpus FIGÉ `out/corpus.json` (consommé, non re-dérivé) ; arbre des perdues reconstruit via `anlib` sur les dumps dossiers (leg 16+17 fusionnés, 5 593 dossiers) et scrutins (4 106 en leg 16, 7 397 en leg 17).
**Sanity check :** la reconstruction reproduit le funnel figé à l'identique (prom_loi=266, jugeable=159, et le découpage 93/66 par législature). `match=true`.

---

## 1. L'entonnoir global (toutes législatures)

| Étape | N | % des promulguées | Ce que l'étape retire |
|---|---:|---:|---|
| **Lois promulguées** (procédure produisant une loi) | **266** | 100 % | — point de départ |
| – sans aucun scrutin public AN | −82 | −30,8 % | adoptées sans scrutin public d'ensemble (voix/main levée) + budgets 49.3 |
| – scrutin AN référencé mais aucun *sur l'ensemble* | −25 | −9,4 % | votes partiels (1ʳᵉ partie de PLF), motions, **+ artefacts de couverture** (voir §3b) |
| – scrutin d'ensemble non public | −0 | 0 % | (catégorie vide) |
| **= CORPUS JUGEABLE** | **159** | **59,8 %** | textes avec ≥1 scrutin public AN sur l'ensemble |

**40 % des lois promulguées (107/266) ne reçoivent jamais de scrutin public d'ensemble à l'AN** et sortent du périmètre. Le filtre « scrutin public sur l'ensemble » n'est pas neutre : il frappe très inégalement selon le type de texte (§4).

---

## 2. L'entonnoir par législature (16 close vs 17 en cours)

| Étape | Leg 16 | Leg 17 |
|---|---:|---:|
| Lois promulguées | 157 | 109 |
| – sans scrutin public AN | −50 | −32 |
| – scrutin non-ensemble | −14 | −11 |
| **= Corpus jugeable** | **93** (59,2 %) | **66** (60,6 %) |

> Attribution de législature : pour une loi **jugeable**, c'est la législature de son **vote de référence** (règle de `corpus.json` — un texte voté en 16 mais promulgué en 17 reste imputé au vote ; 11 cas). Pour une loi **perdue** (pas de vote de réf), c'est la date d'acte la plus tardive (PROM/DEBATS). Le taux de survie ~60 % est stable entre les deux législatures.

---

## 3. Coût de chaque exclusion (avec exemples nommés réels)

### 3.a Ratifications de traités/conventions — **l'exclusion la plus massive** (§2.5)

| | Leg 16 | Leg 17 | Total |
|---|---:|---:|---:|
| Ratifications promulguées | 39 | 26 | **65** |
| → dans le corpus (vote public eu lieu) | 7 | 1 | **8** |
| → **PERDUES** | 32 | 25 | **57** |
| **Taux de survie** | 17,9 % | **3,8 %** | **12,3 %** |

**Les ratifications sont 24,4 % des lois promulguées mais seulement 5,0 % du corpus jugeable.** 88 % d'entre elles sont adoptées **sans scrutin public d'ensemble** (vote à main levée, procédure simplifiée pour les conventions internationales). En leg 17, **une seule ratification sur 26** a reçu un scrutin public.

*Ratifications PERDUES (échantillon réel, leg 16) :*
- Accord France–Andorre (amélioration de la connexion routière entre Andorre et l'autoroute A9)
- Accord France–Pays-Bas relatif à la coopération en matière de défense
- Convention d'entraide judiciaire en matière pénale France–Émirats arabes unis
- Accord de siège entre la France et la **Banque des règlements internationaux**
- Accord France–Canada relatif au déploiement d'agents

*Ratifications qui ENTRENT dans le corpus (« type CETA » — un scrutin public a eu lieu, parfois solennel) :*
- Leg 16, scrutin n°906 [SPO] : Convention d'entraide judiciaire pénale France–[Émirats]
- Leg 16, scrutin n°1197 [SPO] : 1ᵉʳ amendement et protocole à la **convention d'Espoo**
- Leg 16, scrutin n°2390 [SPO] : Accords France–Sénégal du 7 septembre 2021
- Leg 16, scrutin n°3208/3209 [SPO] : conventions fiscales France–Danemark, traité d'entraide pénale
- Leg 17, scrutin n°2460 **[SPS, solennel]** : ratification de la résolution LP.3(4) (protocole de Londres)

→ **Conclusion §2.5 :** la sélection « scrutin public d'ensemble » exclut quasi toute la diplomatie parlementaire. Les 8 ratifications retenues sont retenues par **hasard procédural** (un groupe a demandé un scrutin public), pas parce qu'elles seraient plus importantes que les 57 autres. C'est un biais de sélection, pas un tri par enjeu.

### 3.b Lois passées sans scrutin public d'ensemble (« main levée ») — hors finances/ratif

L'agrégat « pas de scrutin public d'ensemble » pèse **107 lois** (82 sans aucun scrutin AN + 25 avec scrutin non-ensemble). **Fait notable : les 82 ont toutes un acte `AN…-DEBATS-DEC`** — l'AN *a* statué et adopté le texte, mais **aucun scrutin public n'est attaché** à cette décision (adoption à main levée / sans vote enregistré). Hors ratifications et finances, il reste **40 lois ordinaires** perdues ainsi.

*Lois ordinaires (PPL/PJL) perdues faute de scrutin public d'ensemble (échantillon, leg 16) :*
- « Assurer la pérennité des établissements de spectacles cinématographiques » (PPL)
- « Calculer la retraite de base des non-salariés agricoles… » (PPL)
- « Lutte contre les abus et les fraudes au compte personnel de formation » (PPL)
- « Programmation des finances publiques pour les années 2023 à 2027 » (PJL) *(loi de programmation, hors champ finances stricto sensu)*

**⚠️ Distinction d'honnêteté importante (catégorie « scrutin non-ensemble », 25 lois) :** elle mélange deux causes radicalement différentes :

| Sous-cause | N | Nature |
|---|---:|---|
| **Artefact de couverture de données** | 11 | dossiers reportés de la **législature 15** : leurs scrutins (n° leg 15) **ne sont pas dans nos dumps** (leg 16+17 seulement). Ces lois seraient probablement jugeables si on avait les données. |
| **Perte procédurale réelle** | 14 | scrutins présents dans la donnée, mais aucun n'est un vote public d'ensemble |

*Exemples d'artefacts de couverture (NE PAS compter comme exclusion procédurale) :* « **Lutte contre le dérèglement climatique** » (loi Climat-Résilience, voteRefs = scrutins leg 15 n°3738 et 3891, absents du dump), « Lutte contre la maltraitance animale », « Démocratiser le sport en France ». Ces trois grandes lois sont « perdues » par **trou de données**, pas par exclusion de règle.

*Perte procédurale réelle (14) :* 8 ratifications (voix), 3 PPL, et **3 budgets** (voir §3.c).

### 3.c Budgets / lois de finances passés au 49.3 — **les textes les plus structurants, et les plus perdus** (cœur du §4)

| | Leg 16 | Leg 17 | Total |
|---|---:|---:|---:|
| Lois de finances/budget promulguées (PLF, PLFSS, PLFR, fin de gestion) | 8 | 6 | **14** |
| → dans le corpus | 1 | 3 | **4** |
| → **PERDUES** | 7 | 3 | **10** |
| **Taux de survie** | 12,5 % | 50,0 % | **28,6 %** |

**71,4 % des lois de finances promulguées sont hors corpus.** Elles ne représentent que **2,5 % du corpus jugeable** (4 textes) alors qu'elles structurent l'essentiel de la dépense et de la fiscalité de l'État.

**Les 10 lois de finances PERDUES, nommément :**

*Leg 16 (49.3 systématique, aucun scrutin public d'ensemble — `an_refs=0`, l'AN a statué via `ANLDEF/ANNLEC-DEBATS-DEC` sans scrutin) :*
1. **Loi de finances pour 2023** (PLF 2023)
2. **Loi de finances pour 2024** (PLF 2024)
3. **Loi de financement de la sécurité sociale pour 2023** (PLFSS 2023)
4. **Loi de financement de la sécurité sociale pour 2024** (PLFSS 2024)
5. **LFR pour 2022** (loi de finances rectificative)
6. **LFSS rectificative pour 2023** (la « réforme des retraites » budgétaire)
7. **Loi de finances de fin de gestion pour 2023**

*Leg 17 (49.3 → motions de censure, ou vote sur la seule 1ʳᵉ partie — jamais l'ensemble) :*
8. **PLF 2025** : seul scrutin AN d'ensemble lié = n°438 [SPS] sur **« la première partie »** (rejetée) ; puis motion de censure n°693 (49.3).
9. **PLF 2026** : n°4241 [SPS] sur la 1ʳᵉ partie (rejetée) + **6 motions de censure** 49.3 (n°5154, 5155, 5193, 5194, 5284, 5285). Aucun vote d'ensemble.
10. **PLFSS 2025** : aucun vote d'ensemble ; **3 motions de censure 49.3** (n°694, 739, 791). Rappel : la censure n°519 du 04/12/2024 **adoptée** a renversé le gouvernement Barnier — l'événement budgétaire le plus marquant de la législature, totalement invisible dans un corpus « scrutins d'ensemble ».

**Les 4 lois de finances qui ENTRENT dans le corpus** sont précisément celles **sans 49.3** ou avec un vote final tenu :
- Leg 16, n°624 [SPO] : **PLFR 2022** (texte CMP — voté à main levée puis scrutin public)
- Leg 17, n°518 [SPO] : **PLF de fin de gestion 2024** (texte CMP)
- Leg 17, n°4442 [SPS] : **PLF de fin de gestion 2025**
- Leg 17, n°4758 [SPS] : **PLFSS 2026** (lecture définitive)

→ Les budgets « ordinaires » de fin de gestion (petits textes techniques) passent ; les **grands budgets annuels (PLF/PLFSS de l'année), de loin les plus importants, sortent tous**. Le corpus retient les budgets mineurs et perd les majeurs.

### 3.d Résolutions / motions — jamais des lois (exclues en amont)

Les propositions de résolution et motions ne produisent **pas** de loi : elles sont exclues du périmètre « loi » dès la définition (filtre `is_loi`). Mais elles mobilisent une **part majeure de l'activité de vote public d'ensemble** de l'AN :

| | Leg 16 | Leg 17 |
|---|---:|---:|
| Scrutins publics « sur l'ensemble » (SPO+SPS) | 221 | 201 |
| → rattachés à une **loi jugeable** | 93 | 66 |
| → **hors loi jugeable** (résolutions, textes non promulgués, lectures intermédiaires…) | **128** (58 %) | **135** (67 %) |
| Motions de censure (MOC) | 34 | 22 |

**Plus de la moitié des scrutins d'ensemble de l'AN ne débouchent pas sur une loi jugeable** (résolutions art. 34-1, lectures intermédiaires d'un même texte, textes finalement non promulgués). Un corpus « scrutins d'ensemble » bruts surreprésenterait massivement l'activité symbolique (résolutions) ; le filtre `is_loi`+`promulguée` est donc nécessaire — mais il est *correct* sur ce point, contrairement aux exclusions (a)/(c) qui amputent de vraies lois.

---

## 4. La part des textes les plus importants PERDUS

| Famille de texte | Promulguées | Jugeables | **Taux de survie** |
|---|---:|---:|---:|
| **Lois de finances / budget** | 14 | 4 | **28,6 %** |
| **Ratifications de traités** | 65 | 8 | **12,3 %** |
| Lois organiques | 11 | 11 | 100 % |
| Loi constitutionnelle | 1 | 1 | 100 % |
| PJL ordinaires | 48 | 36 | 75,0 % |
| PPL ordinaires | 127 | 99 | 78,0 % |

Les **deux familles les plus structurantes pour l'action publique** — les budgets (toute la fiscalité/dépense) et les engagements internationaux — sont **celles qui survivent le moins** (29 % et 12 %). À l'inverse, lois organiques (souvent procédure exigeant un vote solennel) et constitutionnelle survivent à 100 %.

---

## 5. Le corpus restant est-il représentatif ? **Non — il est biaisé par construction.**

Composition par famille, **promulguées → corpus** (la dérive mesure le biais) :

| Famille | Part des promulguées | Part du corpus | Dérive |
|---|---:|---:|---:|
| **PPL ordinaires** | 47,7 % | **62,3 %** | **+14,6 pts** (surreprésentée) |
| PJL ordinaires | 18,0 % | 22,6 % | +4,6 pts |
| Organiques | 4,1 % | 6,9 % | +2,8 pts |
| **Finances/budget** | 5,3 % | **2,5 %** | **−2,8 pts** (sous-représentée) |
| **Ratifications** | 24,4 % | **5,0 %** | **−19,4 pts** (effondrée) |

### Le même biais, par législature

**Leg 16** (promulguées → corpus) : PPL 45,9 % → **60,2 %** ; ratifications 24,8 % → **7,5 %** ; finances 5,1 % → **1,1 %**.
**Leg 17** (promulguées → corpus) : PPL 50,5 % → **65,2 %** ; ratifications 23,9 % → **1,5 %** ; finances 5,5 % → **4,5 %**.

Le biais est **stable et même accentué en leg 17** : le corpus jugeable est, aux deux tiers, composé de **propositions de loi ordinaires**. Il sous-pondère gravement (i) la diplomatie (ratifications quasi absentes) et (ii) le budget (les grandes lois de finances annuelles toutes absentes).

### Verdict de représentativité

Le corpus jugeable **n'est pas un échantillon neutre de l'activité législative** : c'est l'ensemble des textes ayant déclenché un *scrutin public d'ensemble*, ce qui est fortement corrélé au **type de procédure** (PPL/PJL ordinaires et organiques quasi toujours votés au scrutin ; ratifications à main levée ; budgets au 49.3) plutôt qu'à l'enjeu. La revue a raison sur les deux points :
- **§2.5 (ratifications)** : confirmé — 88 % perdues, le filtre les élimine quasi intégralement.
- **§4 (corpus étroit/biaisé)** : confirmé — 40 % des lois perdues, et la perte est *sélective* : elle vide le corpus des budgets et des traités tout en le concentrant sur les PPL ordinaires.

---

## 6. Limites & honnêteté méthodologique

1. **Artefact de couverture leg 15 (11 lois).** Sur les 25 « scrutin non-ensemble », **11 sont des dossiers reportés de la législature 15** dont les scrutins ne figurent pas dans nos dumps (leg 16+17). Des grandes lois comme **Climat-Résilience** y figurent : elles sont « perdues » par **trou de données**, pas par règle. La **perte procédurale réelle de cette catégorie est de 14, pas 25.** Cela ne change pas les conclusions sur ratifications/budgets (qui reposent surtout sur les 82 « sans scrutin AN », tous dotés d'un acte AN-DEC).
2. **Attribution de législature des perdues.** Faute de vote de référence, elle s'appuie sur la date d'acte la plus tardive (PROM/DEBATS). Robuste mais non infaillible pour les textes à cheval sur la dissolution de juin 2024.
3. **Leg 17 en cours.** Les chiffres leg 17 sont arrêtés à l'état du dump (dernier scrutin ~fév. 2026) ; les budgets 2026 viennent d'être promulgués, le ratio peut bouger.
4. **« 49.3 » n'a pas de code d'acte propre** dans la donnée : on l'infère du **patron observé** (acte `ANLDEF/ANNLEC-DEBATS-DEC` sans scrutin d'ensemble + voteRefs de type `MOTION-VOTE`/scrutins `MOC`). C'est cohérent sur tous les PLF/PLFSS examinés, mais c'est une inférence, pas un champ déclaré.

---

### Fichiers
- Script : `/home/cos/Bureau/dev/boussole-politique/dry-run/scripts/q1-funnel.py`
- Chiffres machine : `/home/cos/Bureau/dev/boussole-politique/dry-run/out/q1-funnel.json`
- Source figée consommée : `/home/cos/Bureau/dev/boussole-politique/dry-run/out/corpus.json`
