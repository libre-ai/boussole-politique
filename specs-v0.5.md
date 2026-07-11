# Nous Président *(provisoire)* — Spécifications v0.5

> **Addendum à v0.1 → v0.4.** Remontée de données **anonymisée par conception**.
> Invariant absolu hérité du projet : **aucun vecteur de positions individuel ne quitte jamais
> l'appareil.** Seules des contributions agrégées et bruitées *à la source* sortent.

---

## 0. Décisions actées

| Sujet | Décision |
|---|---|
| Finalité | **Les trois**, strictement séparées : (A) amélioration produit, (B) insight civique agrégé, (C) validation méthodo. |
| Technique | **Proportionnée à la sensibilité** (arbitrée par finalité, §2). |
| Publication | **Possible sous opt-in éclairé** (méthode + utilité expliquées) + garde-fous (§4). |

---

## 1. Principe directeur — anonymisation à la source

- **On ne collecte jamais d'individuel.** L'appareil **agrège et bruite localement** ; seule une contribution anonyme est émise. Réutilise la lib Rust (WASM/UniFFI) de v0.2.
- **Conséquence RGPD** : si l'anonymisation est *vraiment* irréversible (Considérant 26 RGPD), les données émises sont **hors champ**. Mais :
  - Le statut « anonymisation vraie » se **démontre** (AIPD, §5), il ne s'affirme pas.
  - L'**opt-in reste exigé** : éthique, confiance, et parce que le traitement *on-device avant* anonymisation touche de la donnée art. 9.
  - Le consentement est alors un **engagement de transparence**, pas la base légale d'un traitement de données personnelles (il n'y en a plus côté serveur).
- **Collecte open source** : le code de télémétrie est dans le dépôt public → **auditable**. Pour un commun, la collecte elle-même doit être vérifiable, pas seulement promise.

---

## 2. Les trois flux (séparation stricte)

| Flux | Quoi | Sensibilité | Technique | Publication |
|---|---|---|---|---|
| **A. Comportemental** | Décrochage, étape sautée, perf, erreurs, *quelle* loi abandonnée — **jamais la position** | Faible (aucune opinion) | Agrégats à seuil (k-anonymity) | Publiable (faible risque) |
| **B. Insight civique** | Distribution agrégée des positions par loi | **Art. 9** | **Local DP obligatoire** (bruit borné, ε public) + seuil de cohorte | Publiable **sous conditions strictes** (§4) |
| **C. Validation méthodo** | Qualité du matching, taux de « sans avis », couverture | Faible-moyenne | Agrégats à seuil | Interne / agrégé |

**Cloisonnement** : aucun flux ne se joint à un autre. Aucune corrélation permettant de relier comportement + opinion + appareil. **Opt-in distinct et granulaire par flux** (on peut accepter A sans B).

---

## 3. Comment ça marche

- **Agrégation 100 % côté client** (Rust), puis émission.
- **Local DP (flux B)** : *randomized response* / mécanisme de Laplace. **Budget de confidentialité ε public et documenté** → la garantie est compréhensible et vérifiable.
- **Aucun identifiant stable émis** : pas de device ID persistant → pas de chaînage temporel ré-identifiant. Émissions non corrélables.
- **Seuil de cohorte** : aucun agrégat exposé sous un nombre minimal de contributeurs (`k` à fixer).
- **Transport** : émission **opportuniste, non temps réel** (cohérent froid/asynchrone), via l'API souveraine (Clever/Hono), **sans log d'IP exploitable** (IP tronquée / non journalisée).
- **Minimisation** : on ne collecte que ce qui sert la finalité déclarée. Pas de « au cas où ».

---

## 4. Publication des agrégats — encadrement

**Condition utilisateur (acquise)** : opt-in explicite + explication de la méthode + du « pourquoi c'est utile », par flux.

**Trois résidus que le consentement ne dissout PAS :**

1. **Régime sondage** (loi du 19 juillet 1977 / Commission des sondages). Un agrégat publié d'opinions politiques peut être qualifié de sondage, surtout en période électorale → **vérification juridique**. Possible restriction de la **publication des agrégats d'opinion** en période sensible. *(Nuance vs v0.4 : le produit reste « inchangé » toute l'année ; mais publier un agrégat est un acte distinct qui, lui, pourrait devoir se suspendre près d'un scrutin.)*
2. **Instrumentalisation** (v0.4 §2). Tout agrégat d'opinion publié hérite des garde-fous v0.4 : **jamais de chiffre nu**, contextualisation obligatoire (nb de contributeurs, ε, méthode), **pas de framing « palmarès »**.
3. **Biais d'auto-sélection.** Les contributeurs ne sont **pas représentatifs** de la population (panel auto-sélectionné, non probabiliste). Toute publication doit l'afficher en clair — sinon tu fabriques une fausse « opinion des Français ». Faille épistémique majeure, non négociable.

**Flux A (comportemental)** : publiable librement (aucune opinion, faible risque).

---

## 5. Gouvernance & transparence de la collecte

- **Politique de données publique** : quoi, pourquoi, ε, seuils, rétention.
- **Rétention** : agrégats uniquement. **Aucune contribution individuelle stockée** (par construction).
- **AIPD / analyse d'impact** documentée — même si potentiellement hors RGPD : l'art. 9 en jeu + le doute légitime sur « anonymisation vraie » justifient la prudence. Cohérent avec l'exigence de conformité du projet.
- **Révocabilité** : opt-out à tout moment. ⚠️ Mais une contribution **déjà agrégée et bruitée n'est pas retirable** (par nature) → à expliquer honnêtement *au moment* de l'opt-in.
- **Audit externe** du pipeline de collecte facilité par l'open source.

---

## 6. Cohérence avec les versions précédentes

| Pilier antérieur | Effet de v0.5 |
|---|---|
| Local-first / art. 9 (v0.1/v0.2) | **Préservé** : rien d'individuel ne sort. |
| Anti-instrumentalisation (v0.4 §2) | **Étendu** à la publication d'agrégats. |
| Service inchangé en période électorale (v0.4 §6) | **Précisé** : le produit oui ; la *publication d'agrégats d'opinion* sous réserve juridique. |
| Commun / open core (v0.3) | Code de collecte **open source et auditable**. |

---

## 7. Points ouverts (ajouts v0.5)

| Point | Statut |
|---|---|
| Valeur d'ε (budget DP) — arbitrage utilité/confidentialité | Ouvert |
| Seuil `k` de cohorte | Ouvert |
| Qualification sondage + posture publication en période électorale | **Juridique — à vérifier** |
| Démonstration formelle du statut « anonymisation vraie » (AIPD) | À produire |
| Hébergement collecte (Clever) + non-log IP | À spécifier |

---
*v0.5 — addendum de cadrage. Le local-first n'est pas trahi : il est étendu par une télémétrie anonymisée à la source. Après quoi le cadrage est saturé — la suite utile est en production (charte de neutralité ou schéma de données/API).*
