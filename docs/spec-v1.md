# Boussole Politique — spécification produit v1.0

- **Statut** : proposition consolidée, à faire valider avant implémentation
- **Nom de dépôt cible** : `libre-ai/boussole-politique`
- **Nom public provisoire** : **Boussole Politique**
- **Sources remplacées sans les effacer** : `specs-v0.1.md` à `specs-v0.5.md`, complétées par le modèle v2, la formule, les vecteurs, le dry-run et la revue du 12 juin 2026

## 1. Résumé

Boussole Politique est une application civique local-first. Elle présente des énoncés adossés à des scrutins parlementaires, sans afficher préalablement les groupes ou étiquettes politiques. Le citoyen se positionne sur son appareil, puis l'application compare ses positions aux votes publics des élus et aux positions majoritaires des groupes.

Le résultat décrit une **congruence factuelle et bornée** : « a voté comme toi sur les énoncés que tu as jugés ». Il ne mesure ni la valeur morale, ni la compétence, ni la fiabilité, ni la représentativité globale d'un élu. Ce n'est ni une consigne de vote, ni un sondage, ni un classement politique.

### Proposition de langage public

Le slogan de travail « Qui croire ? Regarde les votes, pas les étiquettes. » est mémorable mais crée une tension : « qui croire » suggère une note de confiance morale que le produit interdit. Il peut rester une piste de campagne, pas une promesse méthodologique.

Sous-titre recommandé pour le produit :

> **Compare tes positions aux votes, sans étiquette.**

Le nom **Boussole Politique** reste le choix par défaut, sous réserve de recherche d'antériorité, disponibilité des domaines et avis juridique. Il est plus durable que « Nous Président » et plus distinctif que `mes-elus`, mais « boussole » peut laisser croire à une recommandation électorale : l'onboarding doit explicitement nier cette interprétation.

## 2. Principes non négociables

1. **Local-first réel** : aucun vecteur individuel de positions politiques ne quitte l'appareil par défaut.
2. **Sans compte** : le parcours MVP est complet sans création de compte.
3. **Pas de palmarès** : aucun classement national, partageable ou non, des élus.
4. **Pas de chiffre nu** : toute congruence est accompagnée de `n`, du dénominateur pondéré, de la couverture et des limites applicables.
5. **Pas de confiance morale** : aucun score de confiance, probité, qualité ou représentativité.
6. **Faits, sélection, citoyen séparés** : aucune donnée locale n'entre dans les datasets publics ; aucune décision éditoriale ne se déguise en fait source.
7. **Sélection opposable** : chaque inclusion ou exclusion VAA est versionnée, justifiée et auditable.
8. **IA facultative et non autoritative** : aucune IA n'est requise dans le MVP. Toute future IA est grounded, citée, évaluée et explicitement faillible.
9. **Sobriété civique** : pas de feed infini, streak, badge, notification creuse, carte d'attaque ou mécanique virale.
10. **Accessibilité comme condition de sortie** : le parcours essentiel vise RGAA/WCAG AA et ne dépend jamais de la seule couleur.

## 3. Ce que le produit est — et n'est pas

### Le produit est

- un outil de positionnement civique à froid ;
- un VAA fondé sur des votes parlementaires réels ;
- une expérience privée par défaut ;
- un commun de code, données, méthode et preuves ;
- un moyen d'explorer accords, désaccords, abstentions et couverture.

### Le produit n'est pas

- une application de vote électoral ;
- un conseil pour choisir un candidat ;
- une mesure exhaustive du mandat d'un élu ;
- un réseau social ou une plateforme de campagne ;
- un baromètre de « l'opinion des Français » ;
- un outil de prédiction ;
- un résumé automatique de l'actualité parlementaire.

## 4. Les trois couches de données

### 4.1 Faits

La couche **Faits** est exhaustive dans un périmètre source et temporel déclaré. Elle est dérivée mécaniquement des sources officielles et n'est jamais corrigée manuellement.

Entités minimales :

- `Scrutin` ;
- `Vote` ;
- `Texte` et actes législatifs ;
- `Elu`, `Mandat`, `AffiliationGroupe`, `Groupe` ;
- `MotionCensure` ;
- `Provenance` et anomalies de réconciliation.

Règles :

- l'Open Data de l'Assemblée nationale est autoritatif pour scrutins et votes ;
- les mises au point officielles sont ingérées ; le calcul emploie la position rectifiée et l'interface permet de voir l'originale ;
- le groupe est celui au moment du scrutin ;
- « absent » n'est pas une donnée AN. Toute estimation éventuelle est étiquetée comme telle et n'entre pas dans la congruence ;
- « présence » est proscrit : on parle de **participation aux scrutins retenus** ;
- chaque fait comporte source, instant d'ingestion, hash de la source et version du parseur ;
- un matching ambigu entre scrutin et dossier fait échouer ou met en quarantaine l'enregistrement : il ne choisit jamais silencieusement.

### 4.2 VAA / éditorial

La couche **VAA** sélectionne et formule les unités jugées. Elle est curatée, immuable par version et régie par la charte de neutralité.

Une `EnonceVaa` comporte au minimum :

- un identifiant stable ;
- un scrutin public de référence ;
- une **formulation d'énoncé** versionnée, distincte du contexte explicatif ;
- un résumé factuel versionné ;
- des sources ancrées ;
- une polarité explicite entre « accord avec l'énoncé » et vote `pour/contre` ;
- des thèmes versionnés ;
- les caveats de version votée/promulguée, décision du Conseil constitutionnel et texte multi-volets ;
- l'entrée de sélection qui justifie sa présence.

Une `Selection` comporte :

- un identifiant et une version sémantique ;
- les paramètres pré-enregistrés du filtre mécanique ;
- le pool complet des candidats ;
- les éléments retenus et écartés ;
- pour chacun, critères mesurés, justification et relectures ;
- un rapport de couverture et de sensibilité.

La sélection ne sera jamais qualifiée de « neutre ». Elle doit être **explicite, reproductible dans sa partie mécanique, contestable dans sa partie éditoriale et évaluée indépendamment**.

### 4.3 Citoyen

La couche **Citoyen** reste sur l'appareil :

- `enonce_id` ;
- valeur `-2`, `-1`, `+1`, `+2`, `sans_avis` ou `passer` ;
- version de la formulation et du résumé vus ;
- instant local ;
- phase `pre_reveal` ou `post_reveal` ;
- historique de révision, si la révision est activée.

`sans_avis` signifie « je ne prends pas position » ; `passer` signifie « je reviendrai plus tard ». Aucun des deux n'entre dans le score.

## 5. Sélection VAA

La sélection est le risque central du produit.

### 5.1 Vivier

Le vivier peut inclure :

- votes d'ensemble ;
- premières parties budgétaires ;
- amendements structurants, selon une règle curatée ;
- textes ou propositions rejetés ;
- ratifications disposant d'un scrutin public pertinent.

Les motions de censure liées au 49.3 restent une branche informative hors congruence. « A voté la censure » n'autorise aucune inférence sur ceux qui ne l'ont pas votée.

### 5.2 Filtre et curation

1. Construire le pool par règles publiées : qualité du lien au texte, participation, discriminance et données suffisantes.
2. Produire un rapport automatique sans modifier les faits.
3. Curater un ensemble limité avec justification cas par cas.
4. Vérifier la couverture des thèmes, types de textes, résultats et coalitions observées.
5. Faire relire la méthode par des compétences indépendantes en science politique, droit parlementaire et méthodologie VAA.
6. Publier la version comme un artefact immuable ; toute modification crée une nouvelle version.

La « symétrie gauche/droite » n'est pas une métrique suffisante : elle réintroduit des catégories idéologiques éditoriales. Le rapport doit privilégier des mesures observables et publier les choix normatifs restants.

## 6. Parcours MVP

### 6.1 Onboarding

L'application explique en langage clair :

- ce qu'elle compare ;
- ce qu'elle ne conclut pas ;
- que les positions restent sur l'appareil ;
- que la sélection est curatée ;
- que l'étiquette politique est masquée avant le reveal, sans prétendre rendre les textes méconnaissables.

Aucun compte, adresse ou circonscription n'est demandé pour commencer.

### 6.2 Jugement

- Une carte à la fois, dans un lot fini.
- Formulation, contexte factuel, caveats et sources accessibles avant la réponse.
- Réponses : « tout à fait en désaccord », « plutôt en désaccord », « plutôt d'accord », « tout à fait d'accord », « sans avis », « plus tard ».
- Aucun swipe binaire.
- Ordre du lot déterministe ou stratifié selon une règle publiée ; une graine locale peut éviter un ordre identique sans remonter de donnée.
- Le miroir de compréhension, s'il est inclus, reste optionnel, local, non noté et non bloquant.

### 6.3 Reveal

Décision v1 proposée : **reveal par lot de cinq, déclenché par l'utilisateur**. Cela réduit l'apprentissage progressif des étiquettes pendant le jugement. Le lot et le seuil restent des paramètres méthodologiques à tester.

Le reveal montre d'abord :

- accords et divergences par énoncé ;
- position majoritaire des groupes, avec leur nom ;
- selon le choix local de circonscription, les titulaires concernés sur la période ;
- abstentions et non-votes séparés ;
- congruence seulement si le seuil propre à la paire est atteint.

Il ne montre pas :

- de top/bottom des 577 élus ;
- de podium ;
- de recommandation électorale ;
- de couleur comme seul codage ;
- de score de « confiance ».

Les groupes sont traités visuellement à égalité. Le MVP privilégie des libellés textuels et une apparence monochrome plutôt que des couleurs idéologiques non autoritatives.

### 6.4 Révision

La réponse pré-reveal n'est jamais écrasée. Une révision post-reveal, si autorisée, crée une nouvelle entrée et n'altère pas le calcul « à froid ». L'interface distingue les deux.

Une modification substantielle de la formulation ou du résumé invalide l'affichage du score concerné jusqu'à relecture explicite par le citoyen.

### 6.5 Persistance et portabilité

- IndexedDB ou stockage navigateur structuré ; pas de `localStorage` comme base principale.
- Demande de persistance du stockage quand l'API navigateur le permet.
- PWA installable et utilisable après chargement des données nécessaires.
- Export/import local versionné, documenté et validé avant remplacement des données.
- Aucun export automatique ni partage social dans le MVP.

## 7. Congruence v1

La formule canonique reste entière et déterministe.

Pour chaque énoncé sur lequel le citoyen a une position tranchée :

1. convertir le vote rectifié de l'élu en direction brute (`pour = +1`, `contre = -1`) ;
2. appliquer la polarité de l'énoncé : `direction_normalisee = direction_brute × polarite`, où `polarite ∈ {-1,+1}` ;
3. exclure abstention, non-votant, absence estimée, égalité majoritaire de groupe et donnée manquante ;
4. prendre `w = abs(position_citoyen)` ;
5. ajouter `w` au dénominateur et 1 à `n` ;
6. ajouter `w` au numérateur si les signes concordent.

```text
si den == 0 : score indéfini
sinon : millièmes = (1000 × num + den / 2) // den
```

Sortie obligatoire :

```text
ScoreResult {
  num,
  den,
  n,
  millièmes?,
  affichable,
  raison_non_affichable?,
  abstentions,
  non_votants,
  donnees_manquantes
}
```

Le seuil initial reste `N_MIN = 10` par paire, comme hypothèse à valider. Le score peut être calculé pour audit sous le seuil mais n'est pas affiché.

La congruence d'un groupe emploie sa position majoritaire `pour/contre` au scrutin ; une égalité est exclue. Aucune pondération thématique n'entre dans le MVP tant qu'une formule et ses risques d'instrumentalisation ne sont pas spécifiés.

**Correction indispensable par rapport aux vecteurs actuels** : ajouter des cas à polarité `-1`. Les vecteurs existants ne prouvent que le cas implicite `+1`.

## 8. Indicateurs associés

Toujours séparés du score :

- nombre d'énoncés jugés ;
- `n` commun à chaque paire ;
- dénominateur pondéré `den` ;
- nombre d'abstentions ;
- nombre de non-votes structurels ou déclarés ;
- couverture du lot et des thèmes ;
- participation aux scrutins retenus, avec exclusions documentées.

« A voté comme toi » signifie seulement l'accord de direction après polarité, sur ce corpus et cette version de sélection.

## 9. Données publiques et serveur

Le MVP préfère des **artefacts publics immuables** servis par hébergement statique/CDN : manifestes, index et fragments de données. Une API n'est ajoutée que si un besoin de requête est démontré.

Si un service est nécessaire :

- Rust + axum, éventuellement via les server functions Dioxus 0.7 ;
- endpoints publics en lecture seule ;
- ETag, cache public et URLs versionnées ;
- aucun endpoint de position citoyenne ;
- aucun identifiant de compte dans le MVP ;
- logs limités aux identifiants techniques publics et erreurs, sans contenu citoyen.

## 10. Hors MVP

- synchronisation multi-appareils ;
- compte ;
- LLM local, cloud ou BYO-key ;
- télémétrie comportementale ou différentiellement privée ;
- publication d'agrégats d'opinion ;
- notifications push ;
- applications mobiles natives et UniFFI ;
- pondération personnelle des thèmes ;
- partage de scores ;
- Parlement européen et Sénat.

Ces fonctionnalités ne sont pas annulées. Elles exigent chacune une spécification, une analyse juridique et une preuve séparées.

## 11. Critères de sortie MVP

Le MVP ne peut être présenté publiquement comme méthodologiquement défendable que si :

- le vivier élargi est confronté aux législatures de test ;
- la sélection v1 et ses exclusions sont publiées ;
- le score reproduit tous les vecteurs, y compris polarité inverse ;
- l'ETL est reproductible sur des fixtures archivées ;
- les liens source et caveats sont visibles ;
- aucun vecteur citoyen n'apparaît dans le trafic réseau ;
- l'export/import et les migrations sont testés ;
- le parcours essentiel passe les contrôles a11y automatisés et une revue manuelle ;
- les preuves de dataset, méthode, sécurité locale et accessibilité sont publiées ;
- la structure éditoriale, le directeur de publication et les procédures légales nécessaires sont en place avant mise en ligne publique.

## 12. Limites à afficher

- la sélection VAA est un choix éditorial gouverné, pas la totalité de l'activité parlementaire ;
- les votes ne résument pas un mandat ;
- les groupes peuvent être disciplinés et certains blocs difficiles à distinguer ;
- les textes connus ne sont jamais réellement « aveugles » ;
- un vote global sur un texte multi-volets ne permet pas une congruence par volet ;
- une version votée peut différer de la version promulguée ;
- le score dépend du corpus, de sa version et des réponses du citoyen ;
- aucun résultat ne constitue une recommandation de vote.
