# Nous Président *(provisoire)* — Spécifications v0.2

> **Addendum à la v0.1.** Couche *exploration des réponses*, *auto-contrôle de compréhension*
> et *intégration LLM*. La v0.1 (périmètre, modèle de données, scoring, archi Rust/Hono, UX deck)
> reste la base ; ce document ne la répète pas.

---

## 0. Décisions actées & principe de séquencement

| Sujet | Décision |
|---|---|
| Stratégie modèle/donnée | **Les trois options** : on-device, Clever AI souverain, BYO-key — avec **pour/contre explicites, choix laissé à l'utilisateur**. |
| Mécanisme de compréhension | **Auto-contrôle non bloquant** (miroir), jamais une notation. |
| Premier livrable v0.2 | **Niveau 0 — analytics déterministe, sans LLM.** |

**Principe de séquencement.** L'architecture LLM (§4) est la *cible*. Ce qui se construit **d'abord** = le niveau 0 (§2) + l'auto-contrôle miroir (§3), qui **ne requièrent aucun LLM**. Le LLM n'arrive qu'ensuite, en couche optionnelle.

---

## 1. Règle d'or LLM (rappel + extension)

Gravée, applicable à **tout** usage d'un modèle (niveaux 1 et 2) :

1. **Le LLM ne produit jamais d'autorité.** Il est strictement *grounded* sur deux sources : le **texte officiel** (Légifrance/dossier législatif) et le **résumé neutre versionné** (moat v0.1). Il **cite** systématiquement.
2. **Le jugement reste ancré à la carte gouvernée.** Le chat est *exploration*, jamais la source du verdict. L'interface sépare visuellement « ce que dit le texte / ton résumé » (autorité) de « réponse assistée » (exploration, faillible).
3. **Refus de spéculer** : hors de ses sources, le modèle répond « non couvert par le texte » plutôt que d'inventer.
4. **Aucune opinion** : le modèle n'évalue pas la loi, ne suggère pas de position, ne juge pas la compréhension du citoyen.

---

## 2. Niveau 0 — Analytics déterministe *(premier livrable)*

« Interroger la donnée de ses réponses » est à ~80 % du **calcul**, pas du LLM. Tout est dérivable de :
`PositionCitoyen` (local) × `VoteReference.positions` × `Loi.themes` × `Elu`.

### 2.1 Requêtes canoniques (moteur Rust, 100 % local)
- **Qui a voté comme moi** : congruence par **groupe**, par **mon député**, top/bottom élus.
- **Mes divergences** : lois où je m'oppose à mon député (liste sourcée).
- **Profil thématique** : sur quels thèmes j'ai le plus d'avis / suis le plus tranché.
- **Congruence pondérée** : score recalculé selon mes thèmes prioritaires (§4.6 v0.1).
- **Présence** : taux de présence de mon député **sur mes sujets** (indicateur séparé, cf. §4.5 v0.1).
- **Couverture** : nb de lois jugées, % sans avis, répartition pour/contre/abstention de mes positions.
- **Évolution** : congruence cumulée dans le temps (à mesure que je juge).

### 2.2 Implémentation
- Calculs dans la **lib Rust** (WASM web / UniFFI mobile) → s'exécutent **sur l'appareil**.
- **Aucune** position envoyée au serveur. L'API Hono ne fournit que la donnée publique (lois, votes, thèmes).
- Sortie = données structurées → rendues en **insight cards + graphes** (réutilise le composant chart).

### 2.3 UX (sans LLM)
- Pas de champ texte libre au niveau 0. Exploration par **chips de questions pré-construites** + filtres (thème, période, groupe).
- Chaque insight est **traçable** : clic → liste des lois qui le composent → lien Légifrance.
- Ton sobre, factuel, zéro classement viral (cohérence *dépassionner*).

> Le texte libre en langage naturel (« pose ta question ») est précisément ce qu'ajoutent les niveaux 1/2. Au niveau 0, on ne simule pas l'IA : on donne des requêtes nettes.

---

## 3. Auto-contrôle « miroir » *(non bloquant — ship niveau 0)*

Objectif : favoriser la délibération **sans juger** la compréhension.

- Après lecture du résumé, champ **optionnel** : « En une phrase, que fait cette loi selon toi ? »
- L'appli affiche **côte à côte** : la reformulation du citoyen ↔ le **résumé neutre officiel** (versionné).
- **Aucune notation, aucune IA** au niveau 0 : pure mise en miroir. Le citoyen s'auto-évalue.
- **Non bloquant** : on peut sauter l'étape et se positionner quand même.
- Le citoyen reste seul juge — de la loi **et** de sa propre compréhension.

**Extension LLM (niveaux 1/2, optionnelle).** Le modèle peut surligner « ce que le résumé officiel mentionne et que ta phrase ne reprend pas » — formulé comme **complément factuel**, jamais « tu as tort ». Toujours optionnel, toujours non bloquant.

---

## 4. Stratégie LLM cible — trois options, choix éclairé

Construite **après** le niveau 0. Abstraction unique côté cœur :

```rust
trait InferenceProvider {
    fn answer_grounded(&self, question: &str, sources: &[Source]) -> Answer; // cite obligatoire
}
// impls : LocalProvider · CleverProvider · ByoKeyProvider
```

### 4.1 Tableau comparatif **montré à l'utilisateur** avant choix
*(la transparence est le produit : l'utilisateur décide en connaissance de cause)*

| Option | Où vont tes données | Souveraineté | Qualité | Hors-ligne | Coût pour toi |
|---|---|---|---|---|---|
| **Local (on-device)** | Restent sur l'appareil | Totale | Modeste | Oui | Gratuit |
| **Clever AI souverain** | Cloud souverain (FR), traitement contractuel | Forte | Bonne | Non | Abonnement |
| **Ton abonnement (BYO-key)** | Chez **ton** fournisseur (souvent hors UE) | ⚠️ Aucune garantie | Variable (selon ton modèle) | Non | Gratuit (tu paies déjà ton abo) |

Affiché tel quel, sans pousser une option. Choix réversible à tout moment.

### 4.2 Consentement & conformité par option
- **Local** : aucun consentement spécifique (rien ne sort).
- **Clever / BYO-key** : envoi d'opinions politiques = **donnée sensible (art. 9)** → **consentement explicite**, écran dédié : *« Tes positions seront envoyées à [fournisseur] pour générer la réponse. »* Granulaire, révocable.
- **BYO-key** étiqueté en permanence : *« Hors périmètre souverain — données traitées par ton fournisseur. »*

### 4.3 Sécurité
- Clés BYO stockées en **Keychain (iOS) / Keystore (Android)**, jamais sur le serveur, jamais en clair.
- Provider Clever : endpoint dédié, pas de log des positions, rétention nulle côté Nous Président.

---

## 5. Monétisation (open-core)

| Tier | Contenu | Prix |
|---|---|---|
| **Commun / gratuit** | Données + API + méthodo + app cœur + **niveau 0** + **niveau 1 local** + **BYO-key** | Gratuit, open-source |
| **Souverain / payant** | **Niveau 2 Clever AI** : Q&A de meilleure qualité, hébergement + instanciation souveraine, traitement contractuel | Abonnement |

**Garde-fou non négociable** : la mission cœur (juger les lois, voir qui a voté comme toi, explorer ses réponses) est **pleinement utilisable gratuitement et sans IA**. Le LLM est un **confort**, jamais le seul chemin vers la compréhension. La monétisation porte sur l'**hébergement souverain + le traitement respectueux**, pas sur l'accès au savoir.

---

## 6. Risques & points ouverts (mise à jour)

| Risque | Parade / statut |
|---|---|
| LLM contredit local-first / art. 9 | Niveau 0 sans IA ; niveaux 1/2 opt-in + consentement ; BYO/Clever clairement étiquetés. |
| LLM contredit la neutralité versionnée | Règle d'or §1 : *grounded* + cite + jamais autorité ; séparation visuelle autorité/exploration. |
| Solo maintainer × 3 adaptateurs | Abstraction `InferenceProvider` ; construits **après** niveau 0. |
| Qualité plancher du modèle on-device pour du juridique | À tester ; reste cantonné au Q&A *grounded*, jamais en autonomie. |
| Règles stores sur BYO-key | À vérifier (App Store / Play) avant implémentation. |
| Hallucination sur texte juridique | Grounding strict + citation ; « non couvert par le texte » par défaut. |
| Paternalisme du contrôle de compréhension | Réglé : miroir non bloquant, zéro notation. |

---

## 7. Séquencement v0.2

1. **Niveau 0 — analytics déterministe** (Rust local) + insight cards/graphes + chips de requêtes.
2. **Auto-contrôle miroir** (côte-à-côte, sans IA).
3. **Abstraction `InferenceProvider`** + écran de choix comparatif (§4.1) + flux de consentement.
4. **Provider Local** (on-device) — Q&A *grounded*.
5. **Provider BYO-key** — étiqueté hors souveraineté.
6. **Provider Clever AI souverain** — tier payant, hébergement + traitement contractuel.

---
*v0.2 — addendum de cadrage. Points encore ouverts (hérités v0.1) : pondération de l'abstention, taxonomie thèmes FR, nom & INPI. Nouveau : choix du modèle on-device, modalités d'abonnement du tier souverain.*
