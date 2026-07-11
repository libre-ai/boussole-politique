# Direction artistique — identité provisoire

- **Statut** : proposition implémentée pour revue, pas identité finale de store
- **Date** : 2026-07-11
- **Périmètre** : icône, wordmarks et dérivés PWA de Boussole Politique

## Repères observés

Libre IA Design System 2.0 emploie le noir, le blanc, des gris sémantiques et le vert de marque `#22C55E`, avec Inter pour le corps et Plus Jakarta Sans pour l’affichage. Les cartes de dépôts utilisent une grille sobre et des constructions géométriques en traits, proches d’une constellation. Le vert y signale la marque, une action ou un nœud actif.

L’identité produit doit rester civique et froide, sans imiter un organisme public. Elle ne doit suggérer ni vote électoral, ni classement, ni direction politique correcte.

## Pistes examinées

### A — Repère à deux directions équivalentes — retenue provisoirement

Un cercle de repérage porte deux nœuds opposés strictement identiques. Deux segments s’arrêtent avant le centre ; un point vert central représente seulement le point de comparaison local. Il n’y a ni pointe de flèche, ni nord privilégié, ni côté coloré.

**Forces** : compréhensible à petite taille, compatible avec la grammaire constellation, distinct d’une boussole réaliste, symétrie vérifiable. Le vert reste au centre et ne valorise aucune direction.

**Risque résiduel** : le nom et le cercle peuvent toujours évoquer une recommandation. Le langage produit doit continuer à nier cette interprétation.

### B — Cadre cardinal sans aiguille

Quatre repères égaux autour d’un centre, sans axe dominant.

**Forces** : neutralité directionnelle maximale et bonne réduction en favicon.

**Faiblesses** : signe trop générique ; proximité possible avec une mire, un service cartographique ou une identité institutionnelle.

### C — Deux nœuds en orbite

Deux points identiques reliés par une orbite interrompue, le citoyen et le vote étant mis en regard sans flèche.

**Forces** : comparaison explicite, très cohérente avec l’univers constellation.

**Faiblesses** : trop proche du langage visuel générique des autres produits Libre AI ; peut évoquer un duel ou une opposition binaire.

## Décision proposée

La piste A est retenue **pour prototypage et contrôle**, car elle respecte les garde-fous sans transformer la boussole en prescription. Cette décision n’est pas une validation produit, juridique ou utilisateur. Une revue humaine doit notamment tester :

- la compréhension spontanée à 16, 32 et 48 px ;
- l’absence d’association à un parti, à une élection ou à un organisme officiel ;
- l’absence d’un « bon côté » perçu ;
- la distinction avec les autres marques Libre AI ;
- le nom public, encore provisoire.

## Sémantique de couleur

- vert Libre : centre de marque uniquement ;
- blanc/gris : repères et directions équivalentes ;
- fond encre opaque : robustesse PWA et contraste ;
- aucune sémantique accord/désaccord n’est portée par l’icône.

Les informations politiques futures devront toujours être textuelles ou doublées par forme/motif. Cette identité ne crée aucun token produit générique : les tokens restent dans `client-kit`.
