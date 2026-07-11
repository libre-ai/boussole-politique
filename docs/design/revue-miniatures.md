# Revue locale des miniatures

- **Support** : `proofs/brand/icon-size-sheet.png`
- **Statut** : inspection technique/visuelle préparatoire ; revue humaine produit en attente
- **Date** : 2026-07-11

## Observé sur les rendus générés

- à **16 px**, le cercle, l’axe double et le centre restent distinguables ; les nœuds deviennent secondaires, sans perte d’une information politique ;
- à **32 et 48 px**, les deux extrémités ont la même taille, le même contraste et la même forme ;
- à **192 et 512 px**, les quatre repères cardinaux, les deux nœuds et le centre sont nets ;
- la superposition de contrôle confirme que traits et nœuds restent dans le cercle sûr maskable de rayon 40 % ;
- le fond est opaque dans tous les PNG ;
- aucune opposition rouge/vert, aucun côté coloré et aucune flèche ne désignent une direction correcte ;
- la carte sociale conserve une hiérarchie froide et lisible, avec l’icône séparée du texte méthodologique.

## Risques encore ouverts

- le signe peut être perçu comme une mire, un maillon ou une boussole malgré l’absence d’aiguille ;
- le nom « Boussole Politique » peut produire une attente de recommandation que l’icône seule ne peut corriger ;
- le centre vert est sémantiquement documenté comme marque, mais cette lecture doit être testée avec des personnes extérieures au projet ;
- les wordmarks utilisent `currentColor` et déclarent les fontes locales sans les embarquer : le rendu exact dépendra de la consommation correcte du bundle `client-kit` dans la future PWA ;
- aucune validation App Store/Play, recherche d’antériorité ou revue juridique n’a été effectuée.

## Décision

Les rendus passent les contrôles techniques et sont suffisamment lisibles pour poursuivre le prototype. Ils ne sont pas déclarés validés comme identité publique finale. Une revue humaine comparative des trois pistes reste nécessaire avant gel de marque.
