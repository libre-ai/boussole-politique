# Construction de l’icône

## Grille canonique

- canevas : `512 × 512` unités ;
- fond opaque plein cadre : encre `#111827` ; le masque de plateforme décide des coins ;
- centre : `(256, 256)` ;
- cercle de repérage : rayon `148`, trait `20` ;
- repères cardinaux : quatre segments identiques de `32` unités ;
- deux nœuds : carrés arrondis identiques de `48 × 48`, tournés de 45° ;
- segments de comparaison : même longueur, même épaisseur `24`, sans flèche ;
- centre de marque : disque vert `#22C55E`, rayon `28`.

Le vert est centré : il n’indique ni accord, ni vote « pour », ni correction politique. Les deux extrémités sont géométriquement et chromatiquement équivalentes.

## Zone de sécurité maskable

La zone sûre PWA est le cercle centré de rayon `204.8` (40 % du côté). En incluant l’épaisseur des traits, le contenu signifiant est borné dans un rayon de `190` unités. Le fond opaque couvre tout le canevas et peut être rogné par le masque de la plateforme.

- rayon sûr normalisé : `0.40` ;
- rayon maximal du contenu, traits inclus : `0.37109375` ;
- marge radiale restante : `14.8` unités.

## Réductions

- **16 px** : silhouette attendue = cercle, axe double et centre ; les petits détails ne portent aucune information exclusive ;
- **32/48 px** : les deux nœuds doivent rester équivalents et le centre distinct ;
- **192/512 px** : construction complète, sans détail additionnel absent des petites tailles.

La planche `proofs/brand/icon-size-sheet.png` est générée pour les contrôles à 16, 32, 48, 192 et 512 px. Une inspection humaine reste requise avant de qualifier la lisibilité de validée.

## Variantes

- `icon.svg` : copie de diffusion déterministe de la source canonique ;
- `icon-monochrome.svg` : symbole sans fond, en noir uniforme, destiné aux contextes monochromes ;
- icônes PWA : fond opaque ;
- variantes maskable : même construction, le contenu étant déjà dans la safe zone ;
- aucune variante rouge/verte ou « pour/contre ».

## Texte alternatif

Texte court recommandé : **« Icône Boussole Politique »**.

Description longue : **« Un repère circulaire relie deux directions identiques autour d’un centre vert neutre. »**
