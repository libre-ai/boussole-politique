# Q8 — Confrontation du vivier VAA élargi

## Verdict

Le pivot VAA est **viable en volume**, mais sa validation reste **conditionnelle**. Le vivier cœur (votes d'ensemble + premières parties, sans amendements) est déjà non vide avec **117 candidats exploratoires** au filtre par défaut, dont **95** ont un lien source direct ou porté par un acte. Ce sous-ensemble fort contient les deux sorts et chaque groupe vote dans les deux directions, mais il reste fortement déséquilibré en faveur des scrutins adoptés (**84 contre 11**). La symétrie politique et la couverture thématique ne sont donc pas démontrées ; le caractère structurant des amendements et une partie des liens scrutin→dossier ne sont pas encore prouvés.

> Recommandation : utiliser d'abord le **vivier cœur comme banc de revue**, pas comme sélection déjà
> équilibrée. Ne mobiliser les amendements qu'après définition d'une rubrique publique de « caractère
> structurant » et durcissement des liens source.

## Paramètres exploratoires

- discriminance minimale : `0.20` ;
- participation minimale : `0.20` des 577 sièges ;
- discriminance = `min(pour, contre)/(pour+contre)` ;
- les motions de censure restent hors score.

Ces paramètres ne sont pas validés académiquement et ne doivent pas être choisis pour produire un résultat politique désiré.

## 1. Taille du vivier

| Périmètre | n | L16 | L17 | ensemble | 1re partie | amendement | adopté | rejeté | dossiers |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| candidats publics liés à une loi | 7302 | 2511 | 4791 | 391 | 8 | 6903 | 2051 | 5251 | 329 |
| cœur avant filtre | 399 | 208 | 191 | 391 | 8 | 0 | 383 | 16 | 294 |
| cœur, filtre défaut (exploratoire) | 117 | 63 | 54 | 112 | 5 | 0 | 103 | 14 | 90 |
| **cœur, filtre défaut + lien fort** | 95 | 46 | 49 | 93 | 2 | 0 | 84 | 11 | 77 |
| amendements, filtre défaut | 3310 | 1010 | 2300 | 0 | 0 | 3310 | 603 | 2707 | 140 |
| total, filtre défaut | 3427 | 1073 | 2354 | 112 | 5 | 3310 | 706 | 2721 | 173 |

Le nombre d'amendements montre que la discriminance ne suffit pas à définir l'importance : une sélection automatique dans ce pool serait méthodologiquement indéfendable.

## 2. Sensibilité aux seuils

| discrim. min | participation min | n total | ensemble | 1re partie | amendements | adopté | rejeté |
|--:|--:|--:|--:|--:|--:|--:|--:|
| 0.10 | 0.10 | 5933 | 183 | 7 | 5743 | 1227 | 4706 |
| 0.10 | 0.20 | 3806 | 154 | 6 | 3646 | 823 | 2983 |
| 0.10 | 0.30 | 2056 | 119 | 4 | 1933 | 435 | 1621 |
| 0.10 | 0.50 | 507 | 80 | 2 | 425 | 135 | 372 |
| 0.20 | 0.10 | 5326 | 130 | 6 | 5190 | 1053 | 4273 |
| 0.20 | 0.20 | 3427 | 112 | 5 | 3310 | 706 | 2721 |
| 0.20 | 0.30 | 1904 | 90 | 3 | 1811 | 372 | 1532 |
| 0.20 | 0.50 | 478 | 66 | 2 | 410 | 118 | 360 |
| 0.30 | 0.10 | 3736 | 83 | 5 | 3648 | 820 | 2916 |
| 0.30 | 0.20 | 2472 | 73 | 4 | 2395 | 547 | 1925 |
| 0.30 | 0.30 | 1399 | 61 | 2 | 1336 | 293 | 1106 |
| 0.30 | 0.50 | 296 | 43 | 2 | 251 | 89 | 207 |

## 3. Diversité des positions majoritaires de groupe — vivier cœur

Cette mesure vérifie seulement que chaque groupe vote parfois pour et parfois contre dans le pool. Elle ne prouve ni neutralité, ni équilibre gauche/droite, ni qualité thématique.

### Législature 16

| Groupe | pour | contre | égalité | part du côté minoritaire | bidirectionnel |
|---|--:|--:|--:|--:|---|
| DEM | 40 | 6 | 0 | 13.0% | oui |
| ECO | 12 | 27 | 1 | 30.8% | oui |
| GDR | 11 | 29 | 0 | 27.5% | oui |
| HOR | 40 | 6 | 0 | 13.0% | oui |
| LFI | 7 | 37 | 0 | 15.9% | oui |
| LIOT | 25 | 13 | 4 | 34.2% | oui |
| LR | 29 | 15 | 0 | 34.1% | oui |
| RE | 40 | 6 | 0 | 13.0% | oui |
| RN | 20 | 24 | 0 | 45.5% | oui |
| SOC | 3 | 7 | 0 | 30.0% | oui |

### Législature 17

| Groupe | pour | contre | égalité | part du côté minoritaire | bidirectionnel |
|---|--:|--:|--:|--:|---|
| DEM | 39 | 10 | 0 | 20.4% | oui |
| DR | 36 | 13 | 0 | 26.5% | oui |
| ECOS | 12 | 34 | 0 | 26.1% | oui |
| EPR | 37 | 12 | 0 | 24.5% | oui |
| GDR | 13 | 34 | 0 | 27.7% | oui |
| HOR | 35 | 13 | 0 | 27.1% | oui |
| LFI-NFP | 13 | 34 | 0 | 27.7% | oui |
| LIOT | 34 | 11 | 1 | 24.4% | oui |
| RN | 29 | 15 | 0 | 34.1% | oui |
| SOC | 20 | 22 | 2 | 47.6% | oui |

## 4. Qualité des liens scrutin → dossier

| législature | portée | dossierRef | voteRef | override proposé | titre | ambigu/non lié |
|---:|---|--:|--:|--:|--:|--:|
| 16 | ensemble | 0 | 175 | 0 | 36 | 10 |
| 16 | premiere_partie | 0 | 0 | 3 | 0 | 0 |
| 16 | amendement | 0 | 1 | 0 | 2349 | 823 |
| 17 | ensemble | 48 | 123 | 0 | 20 | 9 |
| 17 | premiere_partie | 0 | 3 | 2 | 0 | 0 |
| 17 | amendement | 1339 | 0 | 0 | 3429 | 1528 |

**5 premières parties passent par un override proposé** plutôt que par un lien fort (direct ou porté par un acte). Elles ne doivent pas entrer dans une sélection canonique avant relecture croisée de `fixtures/vivier-link-overrides.json`.

## 5. Branche motions de censure

- 56 motions ;
- par article : `{'49.2': 17, '49.3': 39}` ;
- par sort : `{'adopté': 1, 'rejeté': 55}` ;
- hors congruence, sans inférence sur les non-votants.

## 6. Gates

| Gate | Statut |
|---|---|
| `pool_non_vide` | **passe** |
| `deux_legislatures` | **passe** |
| `sorts_adopte_et_rejete` | **passe** |
| `groupes_bidirectionnels` | **passe** |
| `symetrie_du_vivier_core` | **non_prouve** |
| `couverture_thematique` | **non_prouve** |
| `amendements_structurants` | **non_prouve** |
| `liens_source` | **partiel** |

## 7. Décision proposée

1. **Geler le seuil uniquement comme hypothèse**, pas comme vérité méthodologique.
2. Composer pour revue un lot pilote de 10–15 énoncés dans le vivier cœur, sans le publier comme équilibré.
3. Ajouter un mapping thématique EuroVoc avant d'affirmer la couverture.
4. Résoudre les premières parties budgétaires bloquées par des liens d'actes ou overrides publiés.
5. Définir une rubrique « amendement structurant » avant toute inclusion d'amendement.
6. Publier inclusions **et exclusions**, puis demander une revue indépendante.

## Limites

- Le matching par titre est exploratoire : sa validation historique n'atteint que 71 % sur les cas dotés d'une référence directe en législature 17.
- Les dumps ne donnent pas une taxonomie thématique exploitable directement.
- `sort=adopté/rejeté` décrit le sort du scrutin, pas une polarité idéologique.
- La bidirectionnalité d'un groupe ne garantit pas une sélection équilibrée.
- Le rapport mesure un vivier ; il ne choisit aucun énoncé et ne formule aucun résumé.
