# q3 — Décalage version votée / version promulguée (CC, CMP, lecture)

**Valide la revue §2.1 : « la version votée au scrutin de référence ≠ la version promulguée ».**
Corpus FIGÉ consommé : `out/corpus.json` — **159 lois jugeables** (93 leg 16 close, 66 leg 17 en cours).
Le « vote de référence » d'une loi = dernier scrutin public AN d'ensemble lié par `voteRefs` (`numero == ref_numero`).

Script : `scripts/q3-version.py` · chiffres machine : `out/q3-version.json`.

---

## TL;DR — le chiffre-clé

> **Au moins 35 lois sur 159 (22,0 %) sont jugées par le citoyen sur un texte qui n'est pas exactement celui qui a été promulgué.**
> Décomposition : **19** ont subi une **censure partielle** du Conseil constitutionnel (des articles ont disparu *après* le vote), et **20** ont un **vote de référence pris à une lecture antérieure** alors qu'une lecture postérieure (CMP / nouvelle lecture / lecture définitive) a re-décidé du texte à l'AN — **4 cumulent les deux**. L'union vaut **35**.
>
> Le clivage 16/17 est net : **leg 16 = 27/93 (29,0 %)**, **leg 17 = 8/66 (12,1 %)**. La leg 17 est moins « driftée » surtout parce que beaucoup de ses CMP sont **récentes et non encore re-votées/liées**, et parce qu'elle a proportionnellement plus de saisines CC jugées *conformes*.
>
> **Et ce 22 % est un plancher.** La loi la plus emblématique du décalage — **loi immigration 2024** (« contrôler l'immigration, améliorer l'intégration », **décision 2023‑863 DC, partiellement conforme**, ~1/3 des articles censurés) — n'est **même pas dans le corpus** : ses `voteRefs` AN sont nuls, donc elle est *injugeable* par la règle actuelle. Le problème §2.1 frappe donc aussi des lois que le périmètre laisse tomber.

---

## Méthode (3 axes du mandat)

| Axe | Définition opérationnelle | Source dans la donnée |
|---|---|---|
| **(a) Saisine CC + censure** | `saisine_cc` (corpus) ; puis on lit dans le dossier l'acte `CC-CONCLUSION` et son `statutConclusion.fam_code` | `anlib.load_all_dossiers()[uid].raw` → arbre `actesLegislatifs` |
| **(b) CMP avec réf en lecture antérieure** | `ref_acte == AN1-DEBATS-DEC` **alors que** le dossier a une CMP (`has_cmp`) | corpus `ref_acte`, `has_cmp` + acte `CMP-DEBATS-AN-DEC` du dossier |
| **(c) Nouvelle lecture / lecture définitive** | une décision AN de **rang de lecture plus tardif** que le vote de réf existe dans le dossier | `acte_codes` ∩ {`CMP-DEBATS-AN-DEC`, `ANNLEC-DEBATS-DEC`, `ANLDEF-DEBATS-DEC`, `AN2/AN3-DEBATS-DEC`} vs `ref_acte` |

**Vocabulaire CC découvert** (sur les 62 conclusions CC de tous les dossiers) — `statutConclusion.fam_code` :

| fam_code | libellé | texte promulgué vs voté | n (tous dossiers) |
|---|---|---|---|
| `TCD01` | Conforme | **identique** (pas de drift CC) | 24 |
| `TCD02` | **Partiellement conforme** | **des articles RETIRÉS** → drift | 33 |
| `TCD03` | Conforme avec réserve | texte intact, **portée bornée** par réserves | 5 |

> Il n'existe **aucune décision « Non conforme » / censure totale** dans le corpus : le drift CC est toujours *partiel*.
> Qui saisit (parmi les 45 lois saisies) : 60 députés (34), de droit art. 61‑1 lois organiques (8), 60 sénateurs (5), Premier ministre (5).

---

## Résultats agrégés

| Mesure | Total (159) | Leg 16 (93) | Leg 17 (66) |
|---|---:|---:|---:|
| Saisine CC | **45** | 22 | 23 |
| → CC **censure partielle** (TCD02) | **19** | 12 | 7 |
| → CC conforme (TCD01) | 21 | 8 | 13 |
| → CC conforme avec réserve (TCD03) | 4 | 1 | 3 |
| → saisine **sans conclusion** dans le dump | 1 | 1 | 0 |
| Loi avec CMP (`has_cmp`) | 84 | 56 | 28 |
| **(b)** réf = 1ʳᵉ lecture AN **+ CMP présente** | **23** | 21 | 2 |
| **(c)** lecture AN postérieure existe > réf *(drift dossier)* | **20** | 18 | 2 |
| └ drift **prouvé** par un scrutin d'ensemble réel non lié | 18 | 17 | 1 |
| Flag `version_drift` du corpus | **0** | 0 | 0 |
| **UNION : texte jugé ≠ promulgué** (censure **OU** drift) | **35** | **27** | **8** |
| **Fraction du corpus** | **22,0 %** | **29,0 %** | **12,1 %** |

Chevauchement de l'union (35) : **15** par la seule censure CC, **16** par le seul drift de lecture, **4** par les deux
(JO Paris 2024, loi justice 2023‑2027, plein emploi, énergies renouvelables — chacune CMP *et* partiellement censurée).

### Pourquoi le flag `version_drift` du corpus vaut 0 partout — et pourquoi c'est trompeur

Le corpus calcule `version_drift` en comparant le rang du `ref_acte` au rang **max parmi les votes _liés_** (`votes_ens`).
Or quand la CMP n'a **pas** de `voteRef`, son scrutin n'entre jamais dans `votes_ens` : le seul vote lié est l'AN1, donc
« réf == dernière lecture liée » et le flag reste **False**. Le drift est ainsi **structurellement invisible** au corpus.
En recalculant le rang max sur **tous les actes de décision du dossier** (liés ou non), on récupère **20 lois driftées**.

---

## (a) Censure partielle du Conseil constitutionnel — 19 lois, exemples nommés

Chaque ligne : le CC a **retiré des dispositions** du texte voté ; le citoyen a jugé un texte plus large que la loi promulguée.

| Leg | Décision DC | Lecture du vote de réf | Loi |
|---|---|---|---|
| 16 | 2022‑843 DC | AN 1ʳᵉ | **Mesures d'urgence pour la protection du pouvoir d'achat** |
| 16 | 2023‑850 DC | CMP | **Jeux Olympiques et Paralympiques de 2024** |
| 16 | 2023‑851 DC | CMP | Accélération des procédures liées à la construction (nucléaire) |
| 16 | 2023‑853 DC | AN 2ᵉ | Protéger les logements contre l'occupation illicite |
| 16 | 2023‑854 DC | CMP | **Programmation militaire 2024‑2030** |
| 16 | 2023‑855 DC | CMP | **Orientation et programmation de la justice 2023‑2027** |
| 16 | 2023‑856 DC | CMP | Ouverture, modernisation et responsabilité du corps judiciaire |
| 16 | 2023‑858 DC | CMP | **Pour le plein emploi** |
| 16 | 2023‑848 DC | CMP | Accélération de la production d'énergies renouvelables |
| 16 | 2024‑865 DC | nouvelle lecture | Renforcer la lutte contre les dérives sectaires |
| 16 | 2024‑866 DC | AN 1ʳᵉ | **Sécuriser et réguler l'espace numérique (SREN)** |
| 16 | 2025‑876 DC | AN 1ʳᵉ | **Souveraineté agricole et renouvellement des générations** |
| 17 | 2025‑878 DC | CMP | Renforcement de la sûreté dans les transports |
| 17 | 2025‑885 DC | CMP | **Sortir la France du piège du narcotrafic** |
| 17 | 2025‑886 DC | CMP | **Restaurer l'autorité de la justice à l'égard des mineurs délinquants** |
| 17 | 2025‑887 DC | AN 1ʳᵉ | Contre toutes les fraudes aux aides publiques |
| 17 | 2025‑896 DC | CMP | Simplification du droit de l'urbanisme et du logement |
| 17 | 2025‑899 DC | lecture définitive | **PLFSS pour 2026** |
| 17 | 2026‑903 DC | CMP | Simplification de la vie économique |

> **Note d'honnêteté** : « partiellement conforme » va d'**une** disposition retirée à un tiers des articles. La donnée AN
> donne le *statut* et le *numéro de décision* (donc l'URL du Conseil), **pas le compte d'articles censurés** — il faudrait
> parser le texte de la décision pour quantifier l'ampleur. Le décalage est donc **certain dans son existence**, variable dans son ampleur.

> 1 saisine **sans conclusion** dans le dump : *Prévenir les ingérences étrangères en France* (leg 16) — saisine `CC-SAISIE-AN` enregistrée, `CC-CONCLUSION` absente du dossier (décision postérieure au dump). Comptée en saisine, pas en censure.

---

## (b)+(c) Drift de lecture : la référence est prise *avant* la dernière main de l'AN — 20 lois

**Mécanisme** : le dossier porte un `AN1-DEBATS-DEC` (1ʳᵉ lecture) **lié** par `voteRef`, **et** un `CMP-DEBATS-AN-DEC`
(l'AN a voté le texte de la CMP) **dont le `voteRef` est nul**. Le corpus, faute de lien, retient le **vote de 1ʳᵉ lecture**
comme référence — donc un texte **antérieur** à celui issu de la CMP et promulgué. **Preuve** : pour 18 de ces 20 lois, on
retrouve dans les scrutins un **vote public d'ensemble réel** « (texte de la commission mixte paritaire) » à la **date exacte**
de l'acte `CMP-DEBATS-AN-DEC`, simplement **non rattaché** au dossier.

Exemples vérifiés (réf liée → scrutin CMP réel mais non lié) :

| Loi | Réf liée (lecture) | Scrutin CMP réel **non lié** | Sort CMP |
|---|---|---|---|
| **L'industrie verte** | n° 2519 (AN 1ʳᵉ, 2023‑07‑21) | **n° 2721** (CMP, 2023‑10‑10) | adopté |
| Ouvrir le tiers financement (rénovation) | n° 876 (AN 1ʳᵉ, 2023‑01‑19) | **n° 1255** (CMP, 2023‑03‑22) | adopté |
| **Sécuriser et réguler l'espace numérique (SREN)** | n° 2796 (AN 1ʳᵉ, 2023‑10‑17) | **n° 3668** (CMP, 2024‑04‑10) | adopté |
| **Mesures d'urgence pouvoir d'achat** | n° 81 (AN 1ʳᵉ) | **n° 186** (« texte de la commission paritaire », 2022‑08‑03) | adopté |
| Maintien d'un dispositif de veille sanitaire | n° 15 (AN 1ʳᵉ) | **n° 122** (CMP, 2022‑07‑25) | adopté |
| Faciliter la mise en œuvre des JO (sécurité) | n° 2046 (AN 1ʳᵉ) | **n° 2257** (CMP, 2023‑07‑12) | adopté |
| Mesures d'urgence — code du travail | n° 2710 (AN 1ʳᵉ) | **n° 2967** (CMP, 2023‑11‑14) | adopté |

> Cas (b) « littéral » du mandat (réf = `AN1-DEBATS-DEC` **et** `has_cmp`) = **23 lois** (21 leg 16 + 2 leg 17).
> On en retire **3 « fausses alertes »** où la CMP a été convoquée mais **n'a pas débouché sur un vote AN** (CMP non conclusive
> ou Sénat ayant le dernier mot) — donc le vote AN1 *est* la dernière main de l'AN, pas de drift : *renforcer l'accès des
> femmes aux responsabilités*, *vapotage*, *marché locatif en zone tendue*, *transformation des bureaux en logements* (4 dossiers
> sans `CMP-DEBATS-AN-DEC`). D'où **20** drift réels (axe c), pas 23.

> **2 drift non prouvés par scrutin** (sur 20), signalés honnêtement : *Bâtir la société du bien vieillir* (le scrutin CMP existe
> le 2024‑03‑19 mais son objet est très éloigné du titre — appariement non concluant) et *Contre toutes les fraudes aux aides
> publiques* (leg 17 ; aucun scrutin public d'ensemble à la date de la décision CMP — vote probablement à main levée). L'existence
> de l'acte `CMP-DEBATS-AN-DEC` rend le drift très probable, mais je ne l'**affirme** que pour 18/20.

---

## Cas hors corpus — le décalage le plus spectaculaire est *invisible*

**Loi n° 2024‑42 du 26 janvier 2024 « pour contrôler l'immigration, améliorer l'intégration »** (`DLR5L16N47118`) :

- **promulguée** ✓, **saisine CC** ✓ (Président de la République, présidente AN, 60 sénateurs…), **CMP** ✓ ;
- **`CC-CONCLUSION` = décision 2023‑863 DC, « Partiellement conforme »** — le CC a censuré ~1/3 des articles (cavaliers législatifs) ;
- **MAIS** : `AN1-DEBATS-DEC` et `CMP-DEBATS-AN-DEC` ont **`voteRefs` nuls** → `an_vote_refs() == []` → **exclue du corpus**, *injugeable*.

C'est le cœur du problème §2.1 poussé à l'extrême : la loi la plus emblématique de « le texte voté ≠ le texte promulgué »
(et qui plus est largement réécrite en CMP puis amputée par le CC) **échappe entièrement** à l'outil. Le 22 % mesuré est donc
un **plancher** : la même lacune de `voteRefs` qui crée le drift sur 20 lois en **élimine** d'autres du dénominateur.

---

## Limites & honnêteté

1. **« Différent » ≠ « différent et ça change le sens du vote ».** Une censure d'un cavalier ou une retouche CMP marginale
   ne change pas forcément ce qu'un député « pour » soutenait. On mesure l'**existence** d'un écart texte voté/promulgué,
   pas son **ampleur** ni son **caractère substantiel**. Quantifier l'ampleur exigerait de parser les décisions DC et les
   textes CMP vs 1ʳᵉ lecture — hors de la donnée AN structurée.
2. **Le drift de lecture est entièrement imputable à des `voteRefs` manquants** dans les dossiers AN. Si l'AN liait
   correctement le scrutin CMP, le corpus prendrait *automatiquement* la CMP comme référence (rang plus élevé) et le drift
   tomberait à ~0. C'est donc autant un **défaut de données** qu'un défaut de règle — mais l'effet sur le citoyen est réel
   tant que les liens manquent.
3. **Appariement par titre** (passe 2 date‑ancrée incluse) : 18/20 prouvés, 2 non concluants (signalés). Risque de
   faux positif faible (exigence ≥ 2 tokens significatifs + même date d'acte + marqueur de lecture CMP/NLEC/LDEF).
4. **Leg 17 en cours** : plusieurs CMP très récentes (2025‑2026) n'ont pas encore de scrutin lié → le drift leg 17 (2)
   est probablement **sous‑estimé** et augmentera. À recompter à la clôture de la législature.
5. **`CC-SAISIE-DROIT`** (saisine de droit, 10 occurrences tous dossiers) concerne surtout les lois **organiques** : leur
   contrôle CC est automatique, ce qui gonfle mécaniquement le taux de saisine sans toujours produire de censure.

---

## Conclusion (implication produit)

Sur le corpus jugeable, **≈ 1 loi sur 5 (22 %, plancher)** est présentée au citoyen via un vote dont le texte **n'est pas
identique** au texte finalement promulgué — **29 % en leg 16** (corpus clos, donc chiffre fiable), **12 % en leg 17**
(provisoire, appelé à monter). Deux moteurs distincts :

- **Censure CC partielle (19 lois)** : irréductible — le texte promulgué est par construction *plus court* que le texte voté ;
  aucun choix de vote de référence ne corrige cela.
- **Drift de lecture (20 lois)** : **corrigeable** côté produit — il vient de ce que le corpus prend la 1ʳᵉ lecture faute de
  `voteRef` sur la CMP. Préférer le **dernier scrutin solennel/CMP** et **réparer le lien voteRefs** (appariement par
  date+titre, déjà démontré ici à 18/20) éliminerait l'essentiel.

**Recommandation §2.1** : (i) afficher un **bandeau « texte modifié après ce vote »** sur les lois censurées (TCD02) et
driftées, avec lien vers la décision DC ; (ii) **réparer l'appariement CMP** pour que le vote de référence soit la dernière
main réelle de l'AN ; (iii) **élargir le périmètre** aux lois à `voteRefs` nuls mais clairement votées (cf. immigration 2024),
sinon les cas les plus sensibles politiquement restent hors-champ.
