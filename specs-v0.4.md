# Nous Président *(provisoire)* — Spécifications v0.4

> **Addendum à v0.1 → v0.3.** Couche **adverse & défensive** : modèle de menace, résistance à
> l'instrumentalisation, conformité sortante (diffamation / droit de réponse), intégrité &
> authenticité. Principe directeur : **proportionnalité** — nommer toutes les menaces, ne traiter
> à fond que les existentielles, différer le reste à un baseline sécurité sans sur-ingénierie.

---

## 0. Décisions actées

| Sujet | Décision |
|---|---|
| Instrumentalisation | **Active + restrictive** : design anti-décontextualisation + clarifications publiques + limitation des exports weaponisables. |
| Droit de réponse des élus | **Faits seuls, renvoi au canal légal externe** (pas d'espace élu in-app ; *obligation légale maintenue*). |
| Période électorale | **Service inchangé toute l'année** (posture éditoriale ; *caveat légal à vérifier*). |

---

## 1. Modèle de menace

| Acteur / vecteur | Impact | Statut |
|---|---|---|
| Vol / réquisition d'une base d'opinions citoyennes | Atteinte massive vie privée | ✅ **Défendu par design** (local-first, pas de base centrale) |
| Astroturfing, gaming du score, faux engagement | Manipulation des résultats | ✅ **Défendu** (pas de feed social ni classement viral) |
| Accusation de trafic / opacité des données | Réputation | ✅ **Défendu** (open data + provenance + reproductibilité, v0.3 §1) |
| « Tu as biaisé ce résumé » | Crédibilité | ✅ **Cadré** (séparation faits/éditorial + charte versionnée + contestation publique) |
| **Instrumentalisation partisane** de l'output | Réputation, capture du sens | ⚠️ **Résiduel → §2** |
| **Diffamation / présomption** (résumé, cadrage 49.3) | Juridique | ⚠️ **Résiduel → §3** |
| **Droit de réponse** d'un élu | Juridique | ⚠️ **Résiduel → §4** |
| **Fork malveillant** rediffusé sous ton nom | Réputation, intégrité | ⚠️ **Résiduel → §5** |
| Deps vulnérables, DDoS, abus d'API, vol de clé BYO | Disponibilité / sécurité | 🔧 **Baseline → §7** |
| Sur-interprétation (média/citoyen) : « congruence = représentation » | Mécompréhension nuisible | ✅ **Atténué** (disclaimers v0.1/v0.2) + §2 |

L'essentiel du résiduel est **juridique et communicationnel**, pas technique. Tu n'as pas à bâtir une forteresse.

---

## 2. Défense anti-instrumentalisation *(active + restrictive)*

L'output neutre ne doit pas devenir munition partisane décontextualisée.

### 2.1 Restrictions de design
- **Aucun classement national partageable.** La congruence est un signal **personnel** (toi ↔ tes élus), jamais un palmarès exportable.
- **Pas de chiffre nu.** La congruence ne s'affiche/s'exporte jamais sans son **dénominateur** (nb de lois jugées) + le **taux de présence** + l'avertissement *« a voté comme toi ≠ te représente »*.
- **Partage limité à son propre parcours.** Impossible de générer une « carte attaque » prête à l'emploi sur un élu ou un groupe tiers.
- **Exports auto-contextualisés.** Tout partage embarque obligatoirement : rappel méthodo (*« sur N lois que TU as jugées »*), date, lien vers la méthodologie, filigrane. Pas d'export d'un chiffre seul.

### 2.2 Clarifications & droits
- **Réponse rapide** quand l'outil est cité de travers (canal officiel, correctif public).
- **CGU / mentions légales** : usage à des fins de campagne décontextualisée interdit ; **marque protégée** (droit d'exiger la cessation d'un usage trompeur).

### 2.3 Tension assumée
Restreindre le partage **réduit la viralité et la croissance**. C'est un choix délibéré, cohérent avec *dépassionner / anti-dopamine* — acté comme arbitrage de croissance, pas comme oubli.

---

## 3. Conformité sortante & risque juridique

Le risque de diffamation naît surtout de la **couche éditoriale** et du **cadrage 49.3**.

- **49.3 — règle renforcée.** « A voté la motion de censure » est un **fait vérifiable** (scrutin nominatif) → admis. Toute formulation qui *infère* une position sur la loi est **interdite** (déjà v0.1 §4.4). Strictement factuel, lien vers le scrutin, **jamais d'inférence**.
- **Directeur de publication** (LCEN) : responsabilité éditoriale nommée (v0.3 §4.1), chaîne de responsabilité claire.
- **Diligence démontrable** : charte + versioning git + sourcing = preuve de bonne foi éditoriale → atténue le risque diffamation. Le versioning sert aussi de **preuve d'historique**.
- **Revue juridique préalable** recommandée avant mise en ligne : statuts asso, DP, CGU, politique de contestation, cadrage 49.3.

---

## 4. Droit de réponse — *faits seuls + canal légal*

**Choix produit** : pas d'espace élu in-app (aucune tribune de réponse/contextualisation hébergée).

⚠️ **Ce choix ne supprime pas l'obligation légale.** Une demande de droit de réponse valide (LCEN art. 6) **doit** être traitée par le directeur de publication selon la procédure légale (délais, publication). Le spec décrit donc une **procédure**, pas une feature.

**Trois canaux distincts — ne jamais confondre :**
1. **Erreur factuelle sur un vote** → corrigée par **re-dérivation** du pipeline (v0.3 §1). Un vote *correct* n'est pas « corrigible » : c'est un fait public.
2. **Contestation de neutralité d'un résumé** → **canal charte public** (v0.3 §2.3).
3. **Droit de réponse d'un élu sur sa présentation** → **canal légal externe** (DP, mentions légales), hors produit.

**Avantage** : surface produit minimale, aucune tribune politique à modérer dans l'app, cohérent avec *« le citoyen seul juge / faits seuls »*.

---

## 5. Intégrité & authenticité

Le dataset est ouvert (commun) → le *fork* est autorisé. Le risque est la **fausse attribution**.

- **Releases signées** : checksums + signature cryptographique. La « version officielle » est authentifiable ; un fork altéré ne l'est pas.
- **Marque protégée** : la licence autorise le fork du *code/données*, mais pas l'usage du **nom** ni du label « données officielles ». Un fork doit se renommer.
- **Identité** : dépôt INPI (point ouvert sur le nom, v0.1), comptes officiels, page publique de **vérification d'authenticité**.
- **La transparence est la défense** : méthodo + diffs publics réfutent les accusations par la preuve, pas par l'affirmation.

---

## 6. Période électorale — *inchangé*

- **Posture** : aucun comportement induit par le calendrier politique. La **prévisibilité est une affirmation de neutralité** (« on ne module pas selon l'élection ») — à communiquer publiquement comme engagement de constance.
- ⚠️ **Caveat légal** : « inchangé » est une posture éditoriale/opérationnelle ; elle ne préjuge pas d'obligations légales éventuelles en période électorale (communication, réserve). À **vérifier avec un juriste** ; toute obligation prime sur la posture.

---

## 7. Baseline sécurité technique *(proportionné, différé)*

Surface réduite car **pas de PII côté serveur** (local-first). Donc baseline sobre :
- **Dépendances** (Rust/JS) : lockfiles, audit, mises à jour régulières.
- **API** : rate limiting (v0.1), données publiques **cacheables** → DDoS facilement absorbé par CDN/cache.
- **Clés BYO** : Keychain / Keystore (v0.2), jamais serveur, jamais en clair.
- **Pas de sur-ingénierie** au lancement : ni SOC, ni bug bounty. À réévaluer selon l'audience.

---

## 8. État du cadrage & suite

Les quatre versions couvrent désormais : **produit/archi** (v0.1), **IA/monétisation** (v0.2), **institutionnel/opérationnel** (v0.3), **défensif** (v0.4). Le cadrage est globalement complet.

**Points ouverts consolidés**

| Point | Origine | Statut |
|---|---|---|
| Pondération de l'abstention | v0.1 | Ouvert |
| Taxonomie thèmes FR | v0.1 | Ouvert |
| Nom & INPI/domaine | v0.1 | Ouvert (bloque aussi §5) |
| Modèle on-device (juridique FR) | v0.2 | Ouvert |
| Modalités d'abonnement tier souverain | v0.2 | Ouvert |
| Critère du lot d'amorçage | v0.3 | Ouvert |
| Revue juridique préalable (DP, CGU, 49.3, période électorale) | v0.4 | **À planifier** |

**Pivot recommandé : du cadrage vers les livrables.** Deux candidats :
- **Charte de neutralité** en document autonome — ton outil de travail quotidien et ta meilleure défense (transverse v0.1 → v0.4).
- **Schéma de données + contrat d'API** prêt à coder en Rust — pour démarrer l'implémentation.

---
*v0.4 — addendum de cadrage. Clôt le volet défensif. Prochaine étape : passer en mode production (charte ou schéma de données).*
