# Taxonomie thématique v0 — cadrage EuroVoc

- **Statut** : proposition de travail, mapping officiel à vérifier
- **But** : mesurer la couverture de la sélection sans inventer une taxonomie propre opaque

## 1. Décision proposée

Utiliser un sous-ensemble français d'**EuroVoc** comme vocabulaire canonique, avec :

- identifiants EuroVoc officiels et stables ;
- libellés français vendus dans le dataset ;
- version du vocabulaire source ;
- relation explicite entre thème citoyen et concepts EuroVoc ;
- multi-étiquetage autorisé ;
- historique de chaque mapping éditorial.

Aucun identifiant EuroVoc n'est inscrit dans ce document avant vérification contre une distribution officielle. Les libellés ci-dessous sont des catégories d'interface proposées, pas encore des concepts canoniques.

## 2. Catégories citoyennes candidates

Environ quinze catégories, à confronter au corpus :

1. Institutions et vie démocratique
2. Justice et droits fondamentaux
3. Sécurité et défense
4. Relations internationales et Europe
5. Économie et entreprises
6. Travail et emploi
7. Fiscalité et finances publiques
8. Protection sociale et retraites
9. Santé
10. Éducation, recherche et culture
11. Environnement, énergie et climat
12. Agriculture et alimentation
13. Logement, territoires et transports
14. Numérique, médias et communications
15. Immigration, asile et intégration

La liste n'est pas un menu idéologique. Elle doit être testée pour les chevauchements, angles morts et catégories surchargées.

## 3. Contrat de mapping

```text
Theme {
  id_local
  libelle_fr
  eurovoc_concepts[] {
    uri
    id
    libelle_fr
    eurovoc_version
  }
  statut = propose | publie | conteste | retire
  justification
  sources[]
  version
}

EnonceTheme {
  enonce_id
  theme_id
  relation = principal | secondaire
  justification
  reviewer_refs[]
  version
}
```

Le MVP n'utilise pas de poids thématique dans le score. `principal/secondaire` sert uniquement à la navigation et au rapport de couverture.

## 4. Règles

- au moins un thème principal par énoncé ;
- thèmes secondaires seulement si l'effet matériel est présent dans le texte voté ;
- pas de thème déduit uniquement de l'auteur, du groupe ou du débat médiatique ;
- pas de catégorie « divers » publiée sans justification ;
- un texte omnibus peut avoir plusieurs thèmes principaux ;
- le mapping est éditorial, versionné et contestable ;
- une suggestion automatique ou LLM n'est jamais publiée sans revue.

## 5. Mesures de couverture

Publier pour chaque sélection :

- nombre et part d'énoncés par thème principal ;
- nombre de thèmes sans énoncé ;
- concentration maximale d'un thème ;
- croisement thème × type de scrutin ;
- croisement thème × adopté/rejeté ;
- croisement thème × législature ;
- énoncés multi-thèmes ;
- changements de mapping entre versions.

Ces mesures décrivent la sélection ; elles ne prouvent pas sa neutralité.

## 6. Travail nécessaire pour fermer le gate Q8

1. Récupérer une distribution EuroVoc officielle et en figer la version/hash.
2. Vérifier les URI et libellés français.
3. Mapper les quinze catégories candidates vers les concepts officiels.
4. Étiqueter en double aveugle un échantillon du vivier cœur.
5. Mesurer l'accord inter-annotateurs et documenter les désaccords.
6. Réviser les catégories puis étiqueter le lot pilote.
7. Publier le rapport de couverture et les mappings.

Le gate `couverture_thematique` reste **non prouvé** jusqu'à l'achèvement de ces étapes.
