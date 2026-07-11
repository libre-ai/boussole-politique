# Protocole de sélection VAA v1 — proposition

- **Statut** : à relire indépendamment avant constitution d'une sélection publique
- **Donnée d'entrée** : couche Faits exhaustive dans le périmètre déclaré
- **Sortie** : version immuable de `Selection`, distincte des faits

## 1. But

Construire un ensemble limité d'énoncés qui permette une comparaison informative sans choisir les scrutins en fonction du résultat politique attendu. La sélection ne prétend ni résumer toute l'activité parlementaire, ni être neutre par nature.

## 2. Ordre obligatoire

1. Geler un snapshot des faits.
2. Pré-enregistrer paramètres, quotas et rubriques.
3. Produire le pool mécanique et son rapport.
4. Examiner les candidats sans calculer les profils citoyens réels.
5. Documenter chaque inclusion et exclusion.
6. Faire relire faits, polarité et sélection par des personnes distinctes.
7. Publier le rapport de sensibilité.
8. Signer une version immuable.

Il est interdit d'ajuster la sélection après observation de positions citoyennes ou pour rapprocher/éloigner un groupe d'un profil.

## 3. Viviers

### Cœur

- vote public sur l'ensemble d'un texte relevant d'une procédure législative ;
- première partie d'un budget ;
- texte adopté ou rejeté ;
- lien au dossier direct, porté par un acte ou override public relu.

Le cœur est prioritaire. Q8 trouve 95 candidats à lien fort au seuil exploratoire et montre qu'un pilote n'a pas besoin d'ouvrir immédiatement le vivier des amendements.

### Amendements

Un amendement n'est éligible qu'après revue de son caractère structurant. La discriminance seule ne suffit jamais.

### Motions de censure

Branche informative hors congruence. « A voté la censure » ne permet aucune inférence sur les autres élus.

## 4. Filtres mécaniques exploratoires

- `part_minorite = min(pour, contre) / (pour + contre)` ;
- `participation = (pour + contre + abstentions) / 577` ;
- défaut de travail Q8 : `part_minorite ≥ 0,20` et `participation ≥ 0,20`.

Ces seuils ne deviennent normatifs qu'après analyse de sensibilité et revue méthodologique. Un seuil ne constitue pas une preuve d'importance politique.

## 5. Rubrique « amendement structurant »

Chaque critère est répondu et sourcé. Une simple majorité de cases ne suffit pas : la décision reste motivée.

### Admissibilité

- [ ] Le scrutin porte bien sur un amendement identifié et son texte est disponible.
- [ ] Le lien au dossier, à l'article et à la lecture est non ambigu.
- [ ] Le vote `pour/contre` mappe sans ambiguïté vers la formulation proposée.
- [ ] L'amendement n'est pas purement rédactionnel, de coordination ou de correction matérielle.
- [ ] L'effet ne peut pas être présenté honnêtement comme un vote global sur une loi.

### Indices de caractère structurant

- création ou suppression d'un droit, d'une obligation, d'un prélèvement ou d'une dépense substantielle ;
- modification matérielle du champ des bénéficiaires, personnes assujetties ou sanctions ;
- modification d'un montant, seuil ou calendrier central au dispositif ;
- suppression ou remplacement d'un article essentiel ;
- effet budgétaire documenté et non marginal ;
- changement de gouvernance ou de compétence institutionnelle ;
- conséquence durable au-delà d'une coordination technique.

### Exclusions par défaut

- amendement rédactionnel ou de précision sans effet normatif matériel ;
- amendement d'appel ou cavalier dont la portée juridique est incertaine ;
- amendement retiré, tombé ou sans scrutin nominatif exploitable ;
- formulation nécessitant d'attribuer une intention ;
- effet impossible à expliquer dans les limites de la carte ;
- doublon substantiel d'un autre énoncé déjà retenu.

### Preuve à joindre

- texte avant/après ou diff juridique ;
- exposé sommaire, utilisé comme déclaration de l'auteur et non comme fait ;
- article concerné ;
- scrutin et décompte ;
- estimation budgétaire officielle si invoquée ;
- justification d'inclusion et objections de la relecture.

## 6. Couverture et équilibre

Le rapport de sélection publie au minimum :

- thèmes et sous-thèmes ;
- législatures et périodes ;
- projets/propositions, textes adoptés/rejetés ;
- votes d'ensemble, budgets et amendements ;
- distributions de participation et discriminance ;
- direction majoritaire de chaque groupe ;
- caveats de version ;
- nombre d'énoncés issus de la majorité et de l'opposition, sans supposer que cette dimension suffit ;
- doublons et dépendances entre scrutins.

Ni la bidirectionnalité des groupes, ni un ratio adopté/rejeté, ni une « symétrie gauche/droite » subjective ne prouvent seuls l'équilibre. Les métriques sont publiées ensemble avec leurs limites.

## 7. Curation

Chaque `EntreeSelection` porte :

```text
scrutin_id
statut = retenu | écarté | à_revoir
vivier = coeur | amendement | motion_hors_score
mesures
thèmes
critères_appliqués
justification
sources
conflits_d_interets
relectures
version
```

Une exclusion est conservée. Une modification de justification ou de polarité produit une nouvelle version.

## 8. Relectures minimales

- vérification du lien factuel ;
- vérification juridique de l'effet ;
- vérification de la formulation et de la polarité ;
- revue de sélection globale ;
- revue indépendante de la méthode avant revendication publique.

Une même personne peut cumuler des rôles dans un prototype interne, mais la dérogation est visible. Elle n'est pas suffisante pour une publication durable.

## 9. Gates avant publication

- aucun lien ambigu non déclaré ;
- aucun amendement sans rubrique complète ;
- aucun énoncé sans polarité testée ;
- couverture thématique mesurée sur une taxonomie versionnée ;
- rapport de sensibilité publié ;
- inclusions et exclusions disponibles ;
- aucun score citoyen utilisé pour composer la sélection ;
- relecture indépendante enregistrée.
