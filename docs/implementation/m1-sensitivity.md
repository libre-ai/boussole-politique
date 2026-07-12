# M1 — preuve de sensibilité du vivier

Statut : **conditional**.

La registration `docs/methodology/m1-gate-registration.v1.json` a été établie après le Q8 exploratoire mais avant toute sélection canonique. Elle ne prétend pas transformer rétroactivement l'exploration en pré-enregistrement. Elle fige les paramètres et gates qui devront encadrer la prochaine décision de sélection.

`python3 scripts/verify-m1-sensitivity.py` extrait de façon bornée les cinq snapshots archivés, exécute Q8 deux fois et exige des sorties identiques byte pour byte. La preuve déterministe est écrite dans `proofs/methodology/m1-sensitivity.json`.

## Résultat courant

- 117 candidats cœur au filtre exploratoire ;
- 95 candidats cœur avec lien direct ou porté par un acte ;
- deux législatures couvertes ;
- 84 scrutins adoptés contre 11 rejetés dans le cœur à lien fort ;
- 12 combinaisons de seuils reproduites ;
- bidirectionnalité descriptive des groupes, sans preuve de neutralité idéologique.

## Gates bloquantes

- symétrie politique non prouvée ;
- taxonomie et couverture thématiques absentes ;
- cinq overrides budgétaires encore proposés pour revue croisée ;
- importance normative des amendements non définie.

Aucune sélection canonique, curation finale ou promesse PWA n'est autorisée par cette preuve. La prochaine étape est de produire le mapping thématique versionné et la procédure de revue indépendante, pas d'optimiser les seuils en fonction d'un résultat politique observé.
