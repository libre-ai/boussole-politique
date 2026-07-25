# Assets de marque — hors licence logicielle

> Portée : cette déclaration ne couvre que l'identité visuelle. Le reste du dépôt est multi-licence et déclaré par chemin dans [`REUSE.toml`](../../REUSE.toml) — voir [`LICENSE`](../../LICENSE) pour le résumé.

Les fichiers de `assets/brand/` et leurs dérivés générés dans `apps/web/assets/` **ne sont couverts par aucune licence de logiciel ou de contenu**. Ils relèvent de la politique de marque de l'organisation, [`TRADEMARKS.md`](https://github.com/libre-ai/libre-ai/blob/main/TRADEMARKS.md), et de la section `Trademarks` de [`LICENSING.md`](https://github.com/libre-ai/libre-ai/blob/main/LICENSING.md), qui énonce :

> Software and content licences do not grant rights to the names, logos or marks of Libre AI.

## Pourquoi cette déclaration remplace une licence MIT

Ces fichiers ont été distribués sous licence MIT jusqu'au 2026-07-25, au motif que la table canonique n'a pas de ligne pour les assets de marque. Cette absence n'est pas un oubli : elle est **délibérée**, parce que les marques sont hors du régime de licence.

La contradiction était directe. MIT accorde explicitement le droit de « modify, merge, publish, distribute, sublicense, and/or sell », tandis que `TRADEMARKS.md` exige une **permission écrite préalable** pour altérer un logo ou utiliser une marque en publicité, merchandising ou certification. La licence concédait ce que la politique de marque réserve.

Un logo reste protégé par le droit des marques quelle que soit la licence apposée sur le fichier : le risque juridique réel était donc limité. Mais une déclaration MIT publique est une **invitation explicite** à modifier et redistribuer l'identité visuelle, et c'est cette invitation qui est retirée.

## Ce qui reste permis

L'usage nominatif raisonnable, tel que défini par `TRADEMARKS.md` : citer le projet, déclarer une compatibilité, lier vers le dépôt. La référence ne doit pas suggérer de parrainage, de certification ou de distribution officielle.

Toute autre utilisation — reprise du logo comme identité d'un fork ou d'un service, altération, usage commercial ou promotionnel — requiert une autorisation écrite préalable.

## Ce que cette déclaration ne couvre pas

`construction.md` est de la documentation : il décrit la grammaire géométrique et la construction des marques, il n'est pas lui-même une marque. Il est déclaré `CC-BY-4.0` dans `REUSE.toml`, comme le reste de la documentation éditoriale du dépôt.

## Provenance

L'icône et les compositions ont été créées localement pour ce projet le 2026-07-11, sans service externe de génération d'image. Elles reprennent uniquement la palette et la grammaire géométrique du design system inspecté dans le checkout local.

Les wordmarks déclarent Plus Jakarta Sans et Inter, mais n'embarquent aucune fonte. Leur future consommation PWA doit utiliser les fontes locales distribuées par le kit client, soumises à leurs licences propres.

Le nom public restant provisoire, l'usage de marque et l'antériorité demandent encore une revue juridique.
