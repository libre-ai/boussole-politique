# v5 — Vérification adverse INDÉPENDANTE de q5 (mises au point / qualité de données)

*Méthode : ré-extraction directe du champ `scrutin.miseAuPoint` et de `ventilationVotes` dans les JSON bruts (`data/scrutins-{16,17}/json/`), SANS réutiliser `scripts/q5-miseaupoint.py`, SANS utiliser `anlib.positions_nominales()` ni le flag `has_mise_au_point`. Deux moteurs indépendants : (a) Python maison `scripts/v5-verify.py` ; (b) pipeline `jq` pur en ligne de commande. Liste des 159 votes de référence prise telle quelle dans `out/corpus.json`.*

## Verdict : CONCORDE (à une nuance de libellé près, non bloquante)

Tous les chiffres-clés du headline sont reproduits à l'identique par deux méthodes indépendantes. **80/159 (50,3 %)** votes de référence portent une mise au point réelle ; **172** corrections individuelles, dont **167 basculantes (97,1 %)** et **13 inversions franches pour↔contre**. La seule divergence trouvée est un chiffre secondaire (`exemples_nommes_amo10`) dont le dénominateur implicite diffère — détaillée au §3, sans incidence sur le headline.

## 1. Table de concordance (headline + metrics)

| Métrique | Analyse q5 | Recalcul v5 (Python brut) | Recalcul jq pur | Concorde |
|---|---:|---:|---:|:--:|
| n_ref | 159 | 159 | 159 | OUI |
| n_ref_avec_map_reelle | 80 | 80 | 80 | OUI |
| pct_ref_avec_map | 50.3 | 50.3 | — | OUI |
| leg16_ref_avec_map | 43/93 | 43/93 | — | OUI |
| leg17_ref_avec_map | 37/66 | 37/66 | — | OUI |
| n_corrections_sur_ref | 172 | 172 | 172 | OUI |
| corrections_par_cible.pours | 114 | 114 | — | OUI |
| corrections_par_cible.contres | 26 | 26 | — | OUI |
| corrections_par_cible.abstentions | 22 | 22 | — | OUI |
| corrections_par_cible.nonVotants | 10 | 10 | — | OUI |
| n_corrections_basculantes | 167 | 167 | — | OUI |
| pct_basculantes | 97.1 | 97.1 | — | OUI |
| n_corrections_neutres | 5 | 5 | — | OUI |
| pour_contre_francs_sur_ref | 13 | 13 | — | OUI |
| global_leg16 scrutins avec map | 929/4106 (22.6%) | 929/4106 (22.6%) | — | OUI |
| global_leg17 scrutins avec map | 1343/7397 (18.2%) | 1343/7397 (18.2%) | — | OUI |
| global_leg16_corrections | 1907 | 1907 | — | OUI |
| global_leg17_corrections | 2827 | 2827 | — | OUI |
| flag_BUG_leg17 (buggy True) | 7397/7397 | 7397 | 7397 | OUI |
| flag_leg16 (buggy True) | 935 | 935 | 935 | OUI |
| exemples_deputes_hors_amo10 | 24 | 24 | — | OUI |
| **exemples_nommes_amo10** | **143** | **148** (sur 172) / **143** (sur 167) | — | **nuance §3** |

Toutes les 12 transitions `recorded→corrected` du §3 du rapport q5 sont reproduites à l'unité près (voir §2).

## 2. Transitions recorded → corrected (recalcul indépendant)

| recorded (brut) | → corrected | n (v5) | n (q5) | bascule classe ? |
|---|---|---:|---:|:--:|
| non_recense | pour | 90 | 90 | OUI |
| non_recense | contre | 22 | 22 | OUI |
| abstention | pour | 14 | 14 | OUI |
| contre | abstention | 10 | 10 | OUI |
| contre | pour | 10 | 10 | OUI (franc) |
| pour | abstention | 8 | 8 | OUI |
| pour | nonvotant | 6 | 6 | OUI |
| non_recense | abstention | 4 | 4 | non |
| contre | nonvotant | 3 | 3 | OUI |
| pour | contre | 3 | 3 | OUI (franc) |
| abstention | nonvotant | 1 | 1 | non |
| abstention | contre | 1 | 1 | OUI |
| **Total** | | **172** | **172** | **167 OUI / 5 non** |

Les **13 francs** = 10 (`contre→pour`) + 3 (`pour→contre`). Les **5 neutres** = 4 (`non_recense→abstention`) + 1 (`abstention→nonvotant`), tous deux internes à la classe « 0 ». Identique au rapport.

> Note : `metrics.transitions_top` ne liste que les 9 plus fréquentes (il tronque `non_recense→abstention:4`, `abstention→nonvotant:1`, `abstention→contre:1`). Le tableau §3 du `.md`, lui, liste les 12 et concorde à 100 %.

## 3. Le SEUL écart : `exemples_nommes_amo10` 143 vs 148 — c'est un dénominateur, pas un bug

- Mon recalcul du **nombre de corrections dont l'`acteurRef` est présent dans le dump AMO10** (577 acteurs actifs) donne :
  - sur les **172 corrections** : **148 nommées / 24 hors-AMO10**
  - sur les **167 basculantes** seulement : **143 nommées / 24 hors-AMO10**
- La valeur `metrics.exemples_nommes_amo10 = 143` correspond donc au comptage **sur les 167 basculantes** — ce que le §4 du `.md` énonce explicitement (« Sur les 167 corrections basculantes : 143 portent un nom dans AMO10 ; 24 sur des députés partis »). 143 + 24 = 167. Cohérent.
- Le `24` (hors-AMO10) concorde dans les deux lectures car **les 24 corrections hors-AMO10 sont toutes basculantes**.
- Décomposition par législature (recalcul indépendant) : hors-AMO10 = **19 (leg16) + 5 (leg17)**. Les 19 de la 16 sont des députés partis, absents du dump AMO10 (= leg17 actifs) — limite déjà documentée au §6 de q5, confirmée ici, **pas un bug**.

Conclusion : le chiffre 143 est exact relativement à son dénominateur (167 basculantes). L'étiquette `exemples_nommes_amo10` dans le bloc `metrics` est juste un peu ambiguë (on pourrait croire « sur 172 »). Aucune incidence sur le headline.

## 4. Validation par législature (séparée, leg16 close / leg17 en cours)

| Législature | votes réf. | avec map réelle | corrections | basculantes | nommées AMO10 | hors-AMO10 |
|---|---:|---:|---:|---:|---:|---:|
| 16 (close) | 93 | 43 | 75 | 72 | 56 | 19 |
| 17 (en cours) | 66 | 37 | 97 | 95 | 92 | 5 |
| **Total** | **159** | **80** | **172** | **167** | **148** | **24** |

Concorde avec le tableau §2 du rapport q5 (75/72 leg16, 97/95 leg17).

## 5. Vérifications ponctuelles sur exemples nommés (jq direct)

- **Scrutin 15, leg16** (« Maintien provisoire d'un dispositif de veille et de sécurité ») : `miseAuPoint.contres.votant` = `[PA793158, PA793166]` ; ces deux `acteurRef` sont enregistrés dans `decompteNominatif.pours`. Donc **José Beaurain (PA793158) et Jocelyn Dessigny (PA793166) : `pour→contre`** — inversion franche confirmée à la source, identique au §4 de q5.
- Les 13 francs recalculés incluent bien Beaurain, Dessigny, Bourgeaux (n1412), Lechanteux (n1801), Pilato (n3009) côté leg16 ; Bruneau (n2244), Amirshahi + Tavernier (n2975 et n2976), Balanant + Ramos (n5844), Castellani (n7039) côté leg17. Liste identique à celle du `.md`.

## 6. Pièges examinés (et écartés)

- **Flag `has_mise_au_point` cassé (leg17)** : reproduit indépendamment — 7397/7397 « True » avec la logique truthy (`[null,null]` est truthy), alors que seulement **1343** scrutins portent un votant réel. L'analyse a bien évité ce piège en comptant les votants. Critère de comptage validé.
- **Objet-vs-tableau** : les buckets `pours`/`contres` sont `null` ou `{votant: obj|array}` ; `abstentions`/`nonVotants`/`nonVotantsVolontaires` sont TOUJOURS un tableau `[null, …]`, vide (`[null,null]`) ou `[null, {votant: obj|array}]`. Mon extracteur gère les 4 formes. Sans cela on raterait les 22 abstentions + 10 nonVotants (qui sortent 0 si on ne teste que `type==object`). Vérifié.
- **5e bucket `nonVotantsVolontaires`** : présent dans le schéma mais **0 correction** sur les 159 votes de référence (donc n'affecte pas le total 172). Il existe ailleurs (1 cas global vu). Le `corrections_par_cible` de q5 (4 buckets) est donc exact pour le périmètre référence.
- **Double-compte (un même acteurRef dans 2 buckets du même scrutin)** : recherché, **0 cas** sur les votes de référence (`dup_bucket_cases = []`). Pas de double-comptage.
- **Apostrophes** : non pertinent ici — l'extraction passe par `acteurRef` (PA…) et numéros de scrutin, pas par matching de libellé.
- **Dénominateur 159** : pris de `corpus.json` (93+66), figé, non re-dérivé. n_ref=159 par construction.

## 7. Limites de ma propre vérification

- Je consomme la liste des 159 votes de référence du corpus figé sans la re-construire : si le périmètre (choix du vote de référence par loi) était faux, je le propagerais. Mais ce n'est pas l'objet du chiffre-clé q5 (qui porte sur les mises au point *étant donné* le périmètre).
- Résolution des noms : dump AMO10 = 577 acteurs actifs leg17 ; les noms des 19 députés partis de la leg16 ne sont pas résolus (limite partagée et documentée). Le signe et la transition restent exacts (basés sur `acteurRef`).

---
*Fichiers : `scripts/v5-verify.py`, `out/v5-verify.json`. Méthodes croisées : Python brut + jq pur, concordantes.*
