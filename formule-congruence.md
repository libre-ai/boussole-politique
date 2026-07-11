# Formule de congruence — spécification exécutable (Boussole Politique v2)

> Statut : **spec exécutable**. Ce document définit la formule ; `vecteurs-test.json` la *prouve*. Toute
> implémentation (Rust → WASM/Kotlin/Swift) doit reproduire les vecteurs **bit-à-bit**. Validée le
> 2026-06-16 contre le calcul flottant de référence (`dry-run/scripts/q7-simulation.py`) : parité exacte
> + cohérence avec les chiffres publiés du dry-run. Générateur : `dry-run/scripts/formule_v2.py`.

## 1. Ce que la formule calcule

La **congruence** d'une paire `(citoyen, élu)` : la proportion pondérée d'énoncés VAA sur lesquels les
deux sont du même côté, parmi ceux où **les deux** ont une position tranchée. Un nombre dans `[0, 1000]`
(millièmes) **plus un dénominateur `n`** — jamais l'un sans l'autre (« pas de chiffre nu », v0.4).

L'unité jugée est l'**énoncé VAA** (un scrutin sélectionné), pas la loi (cf. `modele-donnees-v2.md`).

## 2. Domaines

```
citoyen sur un énoncé : v ∈ {-2, -1, +1, +2}  |  sans_avis  |  passer
élu au scrutin de l'énoncé : pour | contre | abstention | nonvotant | absent
```

- `sans_avis` et `passer` : **aucune entrée** (le citoyen n'a pas tranché).
- `abstention`, `nonvotant`, `absent` de l'élu : **aucune entrée** (l'élu n'a pas de direction).
  L'absence ne pénalise jamais ; elle est comptée à part (§6).

## 3. Table de contribution (exhaustive)

Direction brute de l'élu `dir_brut` : `pour → +1`, `contre → -1`. Chaque énoncé porte une
`polarite ∈ {-1, +1}` qui relie le sens du vote à la formulation jugée :
`dir = dir_brut × polarite`. Poids `w = |v| ∈ {1, 2}`.

La table suivante présente le cas `polarite = +1`. Avec `polarite = -1`, les lignes `pour` et `contre`
sont inversées avant comparaison.

| élu \ citoyen | `+2` | `+1` | `-1` | `-2` | `sans_avis` / `passer` |
|---|---|---|---|---|---|
| **pour** (dir +1) | accord, `+2/+2` | accord, `+1/+1` | désaccord, `0/+1` | désaccord, `0/+2` | exclu |
| **contre** (dir −1) | désaccord, `0/+2` | désaccord, `0/+1` | accord, `+1/+1` | accord, `+2/+2` | exclu |
| **abstention** | exclu | exclu | exclu | exclu | exclu |
| **nonvotant** | exclu | exclu | exclu | exclu | exclu |
| **absent** (dérivé) | exclu | exclu | exclu | exclu | exclu |

`a/b` = contribution `(numérateur, dénominateur)`. « accord » ⟺ `sign(v) == sign(dir)`.

## 4. Algorithme (arithmétique entière)

```
num = den = n = 0
pour chaque énoncé E où le citoyen a une valeur v ≠ sans_avis/passer :
    dir_brut = direction de l'élu au scrutin de E
    si dir_brut est absente (abstention/nonvotant/absent) : continuer   # E exclu
    dir = dir_brut × polarite(E)  # polarite vaut obligatoirement -1 ou +1
    w   = |v|                    # 1 ou 2
    den += w
    n   += 1
    si sign(v) == sign(dir) : num += w
si den == 0 : congruence = INDÉFINIE          # aucun énoncé commun tranché
sinon       : congruence_millimes = (1000*num + den/2) // den      # round half-up, ENTIER
```

**Pourquoi l'entier.** Le score est calculé une fois en Rust puis exécuté sur WASM / Kotlin / Swift.
En flottant, `num/den` peut diverger du dernier bit selon la cible → deux appareils afficheraient des
scores différents et la transparence s'effondre. `round_half_up(1000·num/den)` sur des entiers est
**identique partout** et testable en CI. (Parité float↔entier prouvée sur les 3 profils réels.)

## 5. Plancher de dénominateur (garde-fou n°1)

Le dry-run (q7) montre que **22-31 % des paires partagent < 10 énoncés** : un « 100 % sur 1 énoncé »
est du bruit qui squatte le haut des classements.

```
si n < N_MIN : ne pas afficher de pourcentage — afficher « pas assez d'énoncés (n/N_MIN) »
N_MIN défaut = 10        # paramètre ouvert, à arbitrer avec le partenariat académique
```

Le score `congruence_millimes` reste calculé (pour l'audit) mais `affichable = (n ≥ N_MIN)`.

*Option (non retenue par défaut) — shrinkage bayésien* : au lieu de masquer, rétrécir vers 500‰ :
`millimes_shrink = round_half_up(1000·(num + α·den_prior/2) / (den + α·den_prior))`, qui tend vers
`num/den` quand `den` grandit et vers 500 quand `den → 0`. Plus lisse, mais moins honnête qu'un franc
« pas assez d'énoncés » ; gardé en réserve.

## 6. Indicateurs séparés (jamais fondus dans le score)

- **Participation aux scrutins retenus** (≠ « présence ») : part des énoncés du citoyen où l'élu a une
  direction `pour/contre`. Exclut le président de l'AN et les non-votes structurels. Affichée à côté du
  score, jamais agrégée dedans.
- **Abstentions de l'élu** : « s'est abstenu sur N de tes énoncés » — comptées, jamais converties en
  demi-désaccord (l'abstention AN est polysémique ; toute valeur numérique encoderait une interprétation
  contestable).

## 7. Agrégation par groupe

Congruence avec un **groupe** = congruence contre sa **position majoritaire** au scrutin (méthode b) :
`maj_dir[groupe][énoncé] = +1` si plus de votants `pour` que `contre`, `-1` si l'inverse, **exclu** si
égalité parfaite. Stable, indépendante de l'effectif. (Le dry-run q7 §4.2 montre que la moyenne
paire-à-paire ne diverge que pour les groupes indisciplinés type LIOT, +5,8 pts.) Le groupe est toujours
celui **au moment du vote** (`groupe_au_vote`), jamais l'affiliation courante.

## 8. Polarité et vecteurs validés

Les vecteurs synthétiques couvrent obligatoirement `polarite = -1`. Cas canonique : un vote brut
`contre` avec polarité `-1` devient une direction normalisée positive et s'accorde avec une réponse
citoyenne positive. Une implémentation qui ignore ce champ doit échouer en CI.

### Vecteurs réels validés (extrait de `vecteurs-test.json`)

Chaque député pris comme citoyen (ses votes → ±2), congruence vs position majoritaire de chaque groupe :

| Citoyen (leg) | meilleur groupe | … | pire groupe | écart |
|---|---|---|---|---|
| **Mathilde Panot** (17, LFI-NFP) | LFI-NFP 100 % | SOC 53,6 % · EPR 32,3 % | DR 19,4 % | **80,6 pts** |
| **Marine Le Pen** (17, RN) | RN 100 % | EPR 69,6 % · SOC 50 % | LFI-NFP 30 % | **70,0 pts** |
| **Éric Ciotti** (16, LR) | LR 100 % | RN 69,2 % · GDR 45,5 % | LFI 16,7 % | **83,3 pts** |

Le gradient gauche↔droite est net. **Mais** Ciotti vs SOC = 33,3 % **sur n=3** : sous `N_MIN`, donc
**non affichable** — exactement le faux score que le plancher neutralise.

## 9. Limites assumées (à communiquer, pas masquer)

- **Bloc de gouvernement indiscernable** : la congruence sépare gauche / centre-droit / RN mais pas
  DEM≈EPR≈HOR≈DR (89-97 % entre eux, q7). Ne pas survendre la granularité.
- **Biais pro-majorité** si le vivier ne contient que des lois adoptées : un « toujours-pour » ressemble
  à un soutien parfait du gouvernement. Corrigé par le vivier élargi + curation symétrique
  (cf. `modele-donnees-v2.md` §Sélection).

## 10. Paramètres ouverts

| Paramètre | Défaut | À arbitrer |
|---|---|---|
| `N_MIN` (plancher) | 10 | partenariat académique |
| shrinkage vs plancher | plancher | — |
| pondération thématique | hors v0 | taxonomie de thèmes FR |
