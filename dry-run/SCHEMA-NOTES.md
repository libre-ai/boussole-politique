# Notes de schéma — open data AN (établies par inspection directe, 2026-06-13)

Workspace : `dry-run/` à la racine du dépôt — données dans `data/`, scripts dans `scripts/`, sorties dans `out/`.
Outils : python3, jq, unzip, curl (réseau OK). Volumes : tout tient en RAM en python.

## Fichiers disponibles

| Chemin | Contenu | Volume |
|---|---|---|
| `data/scrutins-17/json/VTANR5L17V*.json` | 1 fichier par scrutin, législature 17 (juil. 2024 → en cours) | 7 397 |
| `data/scrutins-16/json/*.json` | idem, législature 16 (2022-2024) | 4 106 |
| `data/dossiers-17/json/dossierParlementaire/DLR5L17N*.json` | 1 fichier par dossier législatif | ~9 486 |
| `data/dossiers-16/json/dossierParlementaire/*.json` | idem leg 16 | ~9 090 |
| `data/amo10-17/json/acteur/PA*.json` + `json/organe/PO*.json` | députés **actifs** + organes (groupes…) | 7 752 |

⚠️ AMO10 = députés **actifs seulement**. Les députés partis en cours de législature (démission, ministre, partielle…)
n'y figurent pas → leur acteurRef apparaît dans les scrutins mais pas dans AMO10. La variante « historique » n'est pas
publiée pour la 17. **Quantifier ce trou fait partie des analyses.**

## Structure d'un scrutin (`.scrutin`)

- `numero`, `dateScrutin`, `legislature`, `organeRef` (PO de l'AN), `seanceRef`, `sessionRef`
- `typeVote.libelleTypeVote` ∈ {`scrutin public ordinaire` (7325 en leg 17), `scrutin public solennel` (50), `motion de censure` (22)} ; `codeTypeVote` ∈ {SPO, SPS, MOC?}
- `sort.code` ∈ {`adopté`, `rejeté`}
- `titre` (libellé long), `objet.libelle` (objet du vote), `objet.dossierLegislatif` (ref DLR…), `demandeur.texte`
- `syntheseVote` : `nombreVotants`, `suffragesExprimes`, `nbrSuffragesRequis`, `decompte{pour,contre,abstentions,nonVotants,nonVotantsVolontaires}`
- `ventilationVotes.organe.groupes.groupe[]` : **un bloc par groupe politique tel qu'au moment du vote** —
  `organeRef` (PO du groupe), `nombreMembresGroupe`, `vote.decompteNominatif.{pours,contres,abstentions,nonVotants}.votant`
  avec par votant : `acteurRef` (PA…), `mandatRef`, `parDelegation` (bool), et pour les non-votants : `causePositionVote`.
- `miseAuPoint` : **champ structuré** `{pours, contres, abstentions, nonVotants, nonVotantsVolontaires, dysfonctionnement{...}}` —
  les corrections de vote publiées par l'AN sont DANS la donnée.

### Pièges de format (vérifiés)

1. **Objet vs tableau** (conversion XML→JSON) : `votant` est un **objet** s'il y a 1 votant, un **tableau** sinon.
   Idem potentiellement partout (`groupe`, `acteur.mandats.mandat`, etc.). En python :
   `def as_list(x): return x if isinstance(x, list) else ([] if x is None else [x])`.
2. **Apostrophes** : les libellés mélangent `'` (U+0027) et `’` (U+2019) — « l'ensemble » vs « l’ensemble ».
   Normaliser avant tout matching.
3. **`objet.dossierLegislatif` est VIDE sur les scrutins d'ensemble** (vérifié sur échantillon) alors qu'il est peuplé
   sur ~6280/7397 scrutins (surtout des amendements). La liaison scrutin-d'ensemble ↔ dossier doit passer par
   **matching de titre normalisé** (`objet.libelle` contient le titre du texte, souvent suffixé « (première lecture) »,
   « (texte de la commission mixte paritaire) », « (nouvelle lecture) », « (lecture définitive) » — **ces suffixes sont
   précieux pour identifier la lecture**). Vérifier si `dossierLegislatif` est parfois un objet plutôt qu'une chaîne.
4. **« l'ensemble » ne veut pas dire « loi »** : beaucoup de scrutins d'ensemble portent sur des **propositions de
   résolution** (pas des lois) → filtrer par type de procédure du dossier. 201 scrutins matchent « l('|’)ensemble » en leg 17.
5. **Motions de censure** : le titre distingue « article 49, alinéa 2 » (censure spontanée) et « article 49, alinéa 3 »
   (réponse à un engagement de responsabilité sur un texte). Seules les 49.3 se rattachent à une loi.
   Scrutin n° 519 du 2024-12-04 : motion **adoptée** (gouvernement Barnier renversé, le PLFSS concerné est tombé).
6. `nonVotantsVolontaires` existe en plus de `nonVotants` (décompte synthèse).

## Structure d'un dossier (`.dossierParlementaire`)

- `uid` (DLR5L17N…), `titreDossier.titre` + `titreDossier.titreChemin`, `procedureParlementaire.libelle`
  (ex. « Projet de loi », « Proposition de loi », « Projet de loi de finances de l'année », « Pjl ratification d'ordonnances »…)
- `actesLegislatifs` : **arbre récursif** d'actes — chaque acte a `codeActe`, `libelleActe`, parfois `dateActe`, et des
  enfants dans `actesLegislatifs`. Parcours récursif obligatoire.
- Codes observés (échantillon 400 dossiers leg 17) : `AN1`/`SN1`/`AN2`… (lectures par chambre et rang),
  `ANLUNI` (lecture unique ?), `*-DEPOT`, `*-COM*`, `*-DEBATS`, `*-DEBATS-DEC` (décision de la lecture),
  `CMP`, `CMP-SAISIE`, `CMP-DEC`, `SN1-PROCACC` (procédure accélérée), **`PROM` + `PROM-PUB` (promulgation/publication — 42/400)**.
- Codes À DÉCOUVRIR sur le corpus complet (mission « grammaire ») : lecture définitive (`ANLDEF` ?), engagement 49.3,
  saisine/décision du Conseil constitutionnel, retrait/rejet, motion de rejet préalable.
- **Loi promulguée** = dossier portant un acte `PROM` (avec date, réf JO). C'est l'événement déclencheur du périmètre.

## Structure d'un acteur AMO10 (`.acteur`)

- `uid` (PA…), `etatCivil.ident.{nom,prenom}`,
- `mandats.mandat[]` (⚠️ objet-vs-tableau) : chaque mandat a `typeOrgane` (`ASSEMBLEE`, `GP` = groupe politique,
  `COMPER` = commission…), `organes.organeRef`, `dateDebut`, `dateFin` (null si en cours), `infosQualite`…
- Les **groupes** sont des organes `PO…` (fichiers `json/organe/`) avec `libelle`, `libelleAbrev`, `legislature`.
- Affiliation de groupe **datée** = mandats `GP` successifs → détecter les changements de groupe.
- Élections partielles : mandats `ASSEMBLEE` avec `dateDebut` > 2024-08-01.

## Constantes utiles

- Sièges AN : **577** (dénominateur approximatif ; sièges vacants possibles → l'approximation est un point à documenter).
- Législature 17 : depuis juillet 2024, **toujours en cours** au 2026-06-13 (pas de dump leg 18). Dernier scrutin vu : 2026-02-25+.
- Leg 16 : juin 2022 → juin 2024 (dissolution) — corpus **complet et clos**, parfait pour comparaison.

## Règles des specs à confronter (rappel)

Le périmètre spec v0.1 §2 : loi **définitivement adoptée/promulguée** + **scrutin public sur l'ensemble à l'AN** ;
vote de référence = **dernier** scrutin public AN sur l'ensemble. Exclusions : 49.3 (branche séparée), ratifications,
main levée. Les règles contestées par la revue (`../revue-specs-2026-06-12.md`) :
dernier-scrutin vs scrutin-solennel-préféré, version votée ≠ promulguée, ratifications avec scrutin public (type CETA),
exclusion des absents du ratio, « participation » vs « présence », censure 49.2 vs 49.3.
