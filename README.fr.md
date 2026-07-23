[English](README.md) · **Français**

> [!NOTE]
> **Réservé · futur foyer de Boussole Politique** — reconstruit dans le dépôt de base canonique [`libre-ai/libre-ai`](https://github.com/libre-ai/libre-ai) ([topologie multi-dépôts, ADR-0008](https://github.com/libre-ai/libre-ai/blob/main/docs/adr/0008-multi-repo-target-topology-and-brand.md)).
> Ce dépôt rouvrira comme dépôt produit réel lorsque le propriétaire l'activera, consommant la base comme dépendance versionnée. Les fondations décrites ci-dessous sont **en cours de construction** — avec des liens vers le code qui existe déjà.

# Boussole Politique

**Comparez vos priorités civiques aux votes publics sourcés — localement, en privé, sans profilage.** Vous répondez à des affirmations sourcées équilibrées, et Boussole calcule une comparaison transparente avec dénominateurs exacts, abstentions et données manquantes visibles — entièrement sur votre appareil. Pas de label idéologique, pas de conseil électoral, pas de compte requis. Les données politiques restent chiffrées, locales et sous votre contrôle.

Le cas de base auquel elle répond : _« montrez-moi où mes positions s'alignent avec le registre public »_ — indépendamment de tout label idéologique ou soutien, en utilisant uniquement les données que vous confirmez et vérifiez vous-même.

## Ce qui la distingue

- **Méthode transparente, pas une recommandation.** Chaque comparaison vous montre la formule de calcul, la version du jeu de données, la méthode de sélection, les votes considérés ou manquants, et qui l'a examinée — avant de répondre. Le résultat lie votre ensemble de réponses exact et la version de la méthode ; si l'un change, il se recalcule.
- **Local par défaut, chiffré au repos.** Vos réponses ne quittent jamais votre appareil. Les données d'opinion politique (article 9 RGPD) sont sauvegardées localement sous une enveloppe AES-256-GCM, clé vers une phrase de passe obligatoire (minimum 12 caractères, PBKDF2-SHA256 600 000 itérations). Pas de serveur, pas d'analytique, pas de profil.
- **Refus du vote public sans examen.** Les jeux de données des votes publics et les méthodes de calcul ne sont publiés qu'après approbation explicite d'examinateurs indépendants (méthodologie _et_ légalité/confidentialité) sur les hashs exacts du jeu de données et de la méthode. Pas de publication automatique, pas d'auto-approbation par agent.
- **Sources visibles, agrégats uniquement.** Chaque vote public est sourcé (registre législatif, sondage public, enquête publiée). Les identités individuelles ne sont jamais calculées ou exposées ; seuls les totaux de votes agrégés au-delà d'un seuil minimum (au moins 5, exclusion des petits groupes). Les sources et méthodes d'extraction sont documentées et vérifiables.
- **Déterministe et auditables.** La même personne, les mêmes réponses, la même méthode et le même jeu de données produisent toujours des résultats identiques. La comparaison est calculée localement par un composant WASM déterministe ; les résultats peuvent être reproduits hors ligne.
- **Accessible hors ligne.** Le questionnaire complet, le jeu de données et le calcul sont disponibles hors ligne après un seul téléchargement. Accessible au clavier et aux lecteurs d'écran ; pas d'indicateurs graphiques uniquement.

## État — spécifié publiquement, fondations en construction

Boussole Politique est reconstruite à partir de contrats verrouillés. **Elle n'est pas encore publique** ; le questionnaire côté client et la persistance locale viennent d'abord, et une bonne partie existe déjà et est prouvée dans le dépôt de base :

| Fondation                                                      | État          | Preuve                                                                                                                                                                                                          |
| -------------------------------------------------------------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`boussole-method.v2`** — schéma verrouillé de méthode        | ✅ publié     | Schéma committé ; monde WIT et sémantique normative ([contracts/wit/boussole-scoring-v2/world.wit](https://github.com/libre-ai/libre-ai/blob/main/contracts/wit/boussole-scoring-v2/world.wit))                 |
| **`boussole-response-set.v2`** — schéma verrouillé de réponses | ✅ publié     | Schéma committé ; persistance des réponses validée                                                                                                                                                              |
| **Questionnaire client** — baseline SSR accessible             | ✅ construit  | React PWA, hydratation locale uniquement ; accessible au clavier/lecteur d'écran ; hors ligne ([#186](https://github.com/libre-ai/libre-ai/pull/186))                                                           |
| **Adaptateur IndexedDB** — magasin local de réponses           | ✅ construit  | Chiffrement symétrique AES-256-GCM, protégé par phrase de passe ; restauration hors ligne testée ([#185](https://github.com/libre-ai/libre-ai/pull/185), [#206](https://github.com/libre-ai/libre-ai/pull/206)) |
| **Contrôles de propriété des données** — export / suppression  | ✅ construit  | Export initié par l'utilisateur (sans identité) et suppression irréversible ; aucune effacement serveur nécessaire ([#189](https://github.com/libre-ai/libre-ai/pull/189))                                      |
| **Aperçu de mise à jour du jeu de données**                    | ✅ construit  | L'utilisateur peut voir l'impact avant d'accepter ; migration de réponses compatible ([#160](https://github.com/libre-ai/libre-ai/pull/160))                                                                    |
| **Garde-fou sans transmission** — preuve d'interception réseau | ✅ testé      | Tests E2E confirmant zéro transmission de réponse/résultat sur le fil ([#182](https://github.com/libre-ai/libre-ai/pull/182))                                                                                   |
| **Cœur de calcul candidat** — comparaison WASM déterministe    | ⏳ suite      | Monde WIT et vecteurs de test golden verrouillés ; implémentation Rust/WASM en attente                                                                                                                          |
| Examen et publication du jeu de données/méthode public         | ⏳ en attente | Examinateurs indépendants (méthodologie et légalité/confidentialité) requis (ADR-0002) ; aucun calcul public jusqu'à approbation explicite                                                                      |

Ce dépôt est `private` jusqu'à ce qu'un audit de secrets autorise sa réouverture publique (vague 4). **Cible de référence :** gouvernance des applications électorales (ex. Wahl-O-Mat, iSideWith) — sourçage transparent et calcul local déterministe plutôt que recommandation.

## Comment ça fonctionne

1. **Examiner d'abord** — vous lisez la version du jeu de données, les sources de votes publics, la méthode de sélection, la formule de calcul, le traitement des abstentions et données manquantes, preuves d'examen et limitations — avant de répondre.
2. **Répondre localement** — vous répondez à des affirmations sourcées équilibrées. Les réponses sont sauvegardées uniquement dans IndexedDB sous chiffrement AES-256-GCM protégé par phrase de passe, jamais transmises ou enregistrées.
3. **Calculer localement** — un moteur WASM déterministe évalue votre ensemble de réponses par rapport au jeu de données de votes publics en utilisant la méthode approuvée. La comparaison est transparente : dénominateur visible, votes manquants, contribution par affirmation, abstentions.
4. **Exporter ou supprimer** — vous pouvez exporter un résultat local sans identité (hashs de réponses, version du jeu de données, résultat de comparaison) pour vos dossiers, ou supprimer irréversiblement toutes les réponses locales. Pas de table serveur, pas de compte, pas de récupération.

## Architecture — assemblée à partir de briques interopérables

Boussole Politique est un produit assemblé à partir de briques versionnées indépendamment ; chacune est utilisable et testable seule, et le produit est leur composition (la cible multi-dépôts de [l'ADR-0008](https://github.com/libre-ai/libre-ai/blob/main/docs/adr/0008-multi-repo-target-topology-and-brand.md)).

| Brique                                              | Rôle                                                            | Interface exposée / consommée                                                                                                                                                                                                                                                        |
| --------------------------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Schéma `boussole-method.v2`**                     | Définition de méthode et contrat de calcul verrouillés          | JSON Schema + monde WIT ; définit groupement d'affirmations, seuil d'agrégation, exclusion des petits groupes, liaison de version                                                                                                                                                    |
| **Schéma `boussole-response-set.v2`**               | Enveloppe de réponses utilisateur verrouillée                   | JSON Schema ; sauvegardée dans IndexedDB, chiffrée ; lie version exacte du jeu de données/méthode et hashs de réponses                                                                                                                                                               |
| **Questionnaire client (React PWA)**                | Baseline SSR, UI de questionnaire local, contrôleur persistance | GET jeu de données, rendre affirmations, accepter/ignorer/supprimer réponses, chiffrer vers IndexedDB, aperçu de mises à jour                                                                                                                                                        |
| **Magasin IndexedDB + chiffrement symétrique**      | Stockage local persistant avec chiffrement au repos             | Enveloppe AES-256-GCM clé vers phrase de passe obligatoire ; dérivation PBKDF2-SHA256 600 000 ; local uniquement, clé sans échappatoire                                                                                                                                              |
| **Cœur de calcul candidat** (Rust → composant WASM) | Moteur de comparaison déterministe (en attente)                 | Monde WIT `boussole-scoring-v2` : `compare(method, dataset, response_set) → comparison`, sans capacité                                                                                                                                                                               |
| **Contrats** — interopérabilité verrouillée         | Faits sourcés, jeu de données de votes, sémantique de calcul    | `boussole-method.v2`, `boussole-response-set.v2`, monde WIT, `SEMANTICS.md`, vecteurs de test golden ([contracts/fixtures/boussole-scoring-v2/golden-vectors.v1.json](https://github.com/libre-ai/libre-ai/blob/main/contracts/fixtures/boussole-scoring-v2/golden-vectors.v1.json)) |

L'application de questionnaire effectue l'autorisation (phrase de passe protège lecture/écriture), passe les octets de demande/réponse canoniques au moteur de calcul (quand prêt), et le moteur ne détient aucun jeton et n'effectue aucune I/O. Tout consommateur qui parle les contrats peut valider la même comparaison localement.

## Où se déroule le travail

Tout le développement actif est dans le dépôt de base, sous :

- `apps/boussole` — l'hôte produit (PWA questionnaire, persistance locale, aperçu de mise à jour, UI d'export/suppression)
- `contracts/schemas/boussole-method.v2.schema.json` et `boussole-response-set.v2.schema.json` — schémas verrouillés
- `contracts/wit/boussole-scoring-v2/` — définition du monde WIT, sémantique normative, vecteurs de test golden
- `contracts/fixtures/boussole-scoring-v2/golden-vectors.v1.json` — suite de tests de conformité pour le cœur Rust/WASM en attente
- [`docs/apps/boussole.md`](https://github.com/libre-ai/libre-ai/blob/main/docs/apps/boussole.md) — cahier des charges produit complet

Pour suivre l'avancement ou contribuer, ouvrez des issues et pull requests dans [`libre-ai/libre-ai`](https://github.com/libre-ai/libre-ai). Ce dépôt reste réservé jusqu'à son activation.

## Licence

EUPL-1.2.
