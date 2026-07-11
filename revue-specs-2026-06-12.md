# Revue critique des specs v0.1 → v0.5

> **Statut.** Revue externe des cinq documents de cadrage, demandée le 12 juin 2026.
> **Méthode.** Lecture intégrale des 5 versions ; contre-revue par un second relecteur indépendant
> (sans accès aux conclusions du premier, pour croiser les angles morts) ; vérification web des
> faits concurrentiels. Les faits sensibles sont datés dans le texte.
>
> **Cadre de la revue — « monde idéal » (décision du 12/06/2026).** Ce projet est mené sans
> contrainte de temps, de ROI ni de budget ; l'apprentissage et la complétude sont des objectifs
> en soi. **Aucun argument fondé sur la charge de travail n'est recevable** dans cette revue.
> Le challenge porte exclusivement sur : exactitude, complétude, qualité méthodologique et
> épistémique, conformité, excellence d'ingénierie. La pile complète (Rust + WASM + UniFFI,
> apps natives, API, trois providers LLM, télémétrie DP) est un objectif assumé, pas une dérive.

---

## 0. Verdict

Le cadrage est **remarquablement lucide sur la posture** — neutralité, art. 9, séparation
faits/éditorial, anti-instrumentalisation, gouvernance, télémétrie anonymisée à la source — et
**encore aveugle sur la matière** : la donnée parlementaire réelle, l'arithmétique de son propre
score, et la qualité épistémique de ce que le reveal révélera. Cinq versions déclarent le cadrage
« saturé » sans qu'aucune n'ait prévu de confronter une seule règle à l'open data réel.

La conclusion de v0.5 (« la suite utile = charte ou schéma de données ») est inversée. La suite,
c'est : **(1) un dry-run sur les données réelles de la législature — l'oracle de tes règles —
et (2) la formule de congruence en pseudo-code exhaustif avec vecteurs de test.** Tout le reste
(modèle de données v2, ETL, charte, clients) se construit dessus.

### Ce qui tient très bien (à ne pas toucher)

- La séparation **couche faits / couche éditoriale** (v0.3 §1) — c'est la colonne vertébrale du projet.
- Le **49.3 hors score, sans inférence** (v0.1 §4.4, durci v0.4 §3).
- La **charte versionnée et contestable** (v0.3 §2) — jugeable contre la charte, pas contre l'intention.
- Le « **pas de chiffre nu** » et les exports auto-contextualisés (v0.4 §2).
- La lucidité sur le **biais d'auto-sélection** des agrégats (v0.5 §4.3) — rarissime à ce stade.
- Le **miroir non bloquant** (v0.2 §3) et le **niveau 0 sans LLM d'abord** (v0.2 §2).
- Le réflexe de **proportionnalité** du volet défensif (v0.4).

---

## 1. La formule de congruence est indéfinie (v0.1 §4.3)

C'est la faille la plus nette du corpus : **la formule centrale du produit admet plusieurs
lectures incompatibles.**

1. **Contradiction frontale.** La condition d'inclusion exige que « l'élu a une direction
   (`pour`/`contre`) » — ce qui **exclut** l'abstention. Deux lignes plus bas : « `abstention`
   de l'élu = demi-désaccord (poids/2) » — ce qui **l'inclut**. Les deux phrases ne peuvent pas
   être vraies en même temps.
2. **« Demi-désaccord (poids/2) » a au moins trois lectures** : (i) numérateur += 0,
   dénominateur += poids/2 ; (ii) numérateur += poids/2, dénominateur += poids ;
   (iii) poids/2 aux deux. Sur un profil de 15 lois dont 4 abstentions d'élu, l'écart entre ces
   lectures dépasse 10 points de score.
3. **« Congruence par groupe »** (reveal v0.1 §7, requêtes canoniques v0.2 §2.1) n'a de formule
   nulle part : moyenne des congruences des membres ? congruence contre la position majoritaire
   du groupe à chaque scrutin ? Les deux donnent des résultats différents dès qu'un groupe se
   divise. Et « le groupe » : celui du député **à la date du scrutin** (présent dans la donnée
   scrutin de l'AN) ou `Elu.groupe_id` actuel — champ unique du modèle, faux dès le premier
   changement de groupe ?
4. **Pondération thématique** (§4.6) : « au prorata de ses poids de thèmes croisés avec ceux du
   citoyen » — croisés comment (produit scalaire ? min ? normalisé par quoi ?) ; et si
   l'intersection thèmes-citoyen ∩ thèmes-loi est vide, la loi a un poids nul et sort
   silencieusement du dénominateur — potentiellement sous le seuil de significativité sans que
   l'UI le sache.
5. **Le seuil de significativité est mal placé.** « ≥ 5 lois jugées » (v0.3 §3.3) porte sur le
   citoyen, pas sur le **dénominateur de chaque paire citoyen↔élu**. Un citoyen juge 10 lois ;
   le député X n'a pris part qu'à 3 d'entre elles : le score affiché repose sur 3 points. Le
   « top/bottom élus » (v0.2 §2.1) sur des dénominateurs hétérogènes produit un classement
   statistiquement mensonger (les extrêmes seront mécaniquement les petits dénominateurs).
   Question annexe non tranchée : « jugées » inclut-il « sans avis » ?

### Correctif

Écrire la formule en **pseudo-code exhaustif**, cas par cas :
`{pour, contre, abstention, non_votant, absent} × {avis ±1/±2, sans avis}`, avec la définition
de la congruence de groupe, de la pondération thématique (formule fermée), du seuil par paire,
et **des vecteurs de test chiffrés publiés dans le dépôt**.

**Recommandation sur l'abstention** : l'**exclure du score** (comme l'absence) et la compter dans
un indicateur séparé (« s'est abstenu sur N de tes lois »). L'abstention à l'AN est polysémique
(bienveillante, hostile, stratégique de groupe) : toute valeur numérique encode une
interprétation contestable, et « le moins d'interprétation possible » est l'ADN du projet. Si une
valeur est conservée malgré tout, une seule règle, écrite, avec sa justification dans la charte
méthodologique.

> **Vecteurs de test = spec exécutable.** Des fixtures publiées (positions citoyennes × scrutins
> connus → scores attendus) font trois choses à la fois : elles *sont* la spécification (non
> ambiguë), elles garantissent la **parité bit à bit** entre les cibles (WASM, Kotlin, Swift)
> en CI, et elles transforment la transparence méthodologique en artefact vérifiable — quiconque
> conteste le score peut rejouer les exemples. C'est la version ingénierie de la charte.

---

## 2. La mécanique parlementaire réelle va casser les règles posées

Chaque point ci-dessous est un cas réel, daté, qui met en défaut une règle des specs. C'est le
bloc le plus important de la revue : chacun est une munition potentielle contre la crédibilité
du produit — et leur traitement complet est précisément ce que « sans compromis » veut dire.

### 2.1 Version votée ≠ version promulguée

- **CMP votées à main levée.** Les conclusions de CMP passent souvent sans scrutin public. Le
  « dernier scrutin public AN sur l'ensemble » pointe alors sur la 1ʳᵉ lecture — un texte parfois
  réécrit en profondeur par la CMP. Le citoyen juge la loi promulguée ; le député référencé a
  voté un autre texte. La règle v0.1 §2 matche silencieusement deux versions différentes.
- **Censure partielle du Conseil constitutionnel — absente des 5 versions.** Cas canonique :
  loi immigration, décision n° 2023-863 DC du 25 janvier 2024, une trentaine d'articles censurés
  dont les plus clivants. Le texte voté et le texte promulgué sont matériellement différents.
  Le modèle `Loi` n'a aucun champ pour la décision CC, et le déclencheur v0.3 §1.2
  (« adopté définitivement / promulgué ») confond deux événements séparés par la fenêtre de
  saisine — une loi peut même être intégralement censurée et jamais promulguée.

**Correctifs.** Ajouter `decision_cc` au modèle (`url`, articles censurés, drapeau
`version_votee_differe`) ; déclencher le pipeline sur **promulgation** uniquement ; stocker la
**version de texte attachée au scrutin de référence** ; quand elle diffère du texte promulgué
(CMP réécrite, censure partielle), afficher un caveat obligatoire sur la carte — ou exclure la
loi, selon une règle écrite.

### 2.2 « Absent » n'existe pas dans la donnée de l'AN

Le modèle `position ∈ {pour, contre, abstention, absent}` (v0.1 §3) ne correspond pas au format
réel des scrutins, qui listent `pours / contres / abstentions / nonVotants` (avec cause :
présidence de séance, etc.). **L'absence est une catégorie dérivée** : elle exige de reconstruire
la composition exacte de l'Assemblée à la date du scrutin (démissions, décès, ministres remplacés
par leur suppléant, sièges vacants, élections partielles). Toute erreur de reconstruction
fabrique un faux « absent » — une affirmation factuelle erronée sur une personne nommée.

En cascade :

- Le **président de l'Assemblée ne vote jamais** : sans traitement, son « taux de présence sur
  tes sujets » affichera 0 %.
- Les **délégations de vote** signifient qu'un votant n'était pas physiquement présent :
  « présence » est un terme impropre.
- Les **mises au point** (corrections de vote publiées par l'AN : un député a voté « pour » par
  erreur de boîtier) contredisent v0.4 §4 (« un vote correct n'est pas corrigible : c'est un fait
  public ») : l'AN publie elle-même le correctif. Les ignorer expose à une demande de
  rectification fondée (art. 16 RGPD — exactitude), de la part d'un élu, sur un fait que la
  source officielle a déjà corrigé.

**Correctifs.** Étendre l'énumération : `{pour, contre, abstention, non_votant(cause), absent}`
avec « absent » documenté comme **dérivation** (algorithme de reconstruction des mandats
publié) ; ingérer les mises au point et trancher publiquement (recommandation : le score utilise
la **position rectifiée**, l'UI affiche les deux) ; renommer « taux de présence » en
« **participation aux scrutins retenus** » — c'est exactement le reproche durable fait aux
statistiques d'absence de NosDéputés ; exclure de l'indicateur le président de l'AN et les cas
structurels de non-vote.

### 2.3 La participation réelle des scrutins ordinaires

Sur les scrutins publics ordinaires, la participation tombe couramment sous 30 % des 577
(fins de navette, séances de nuit). Conséquences directes : les dénominateurs par paire
citoyen↔député s'effondrent (cf. §1.5), et « ton député a participé à 15 % de tes lois » devient
un chiffre vrai mais trompeur — exactement le type de munition que v0.4 §2 veut neutraliser.

**Correctifs.** Quand un **scrutin solennel** existe sur la version finale du texte, le préférer
comme vote de référence (à articuler avec la règle de version, §2.1) ; afficher
systématiquement le dénominateur de chaque paire (déjà dans l'esprit « pas de chiffre nu ») ;
mesurer la distribution réelle de participation dans le dry-run (§4) avant de figer la règle.

### 2.4 La branche 49.3 est sous-modélisée

- `SignalRejet` porte un `motion_censure_url` **singulier**. Réalité : plusieurs motions par
  engagement (chaque groupe d'opposition dépose la sienne), plusieurs engagements par texte
  (un par lecture). Modéliser **0..n motions par engagement, par lecture**.
- **Censure adoptée = texte rejeté.** Le 4 décembre 2024, la motion de censure sur le 49.3 du
  PLFSS a été adoptée : le texte est tombé, il n'entre jamais dans le corpus. Le routage v0.3
  §1.2 doit filtrer sur « censure rejetée ».
- **Règle de précédence absente.** Un texte peut cumuler un vrai scrutin public sur l'ensemble à
  une lecture et un 49.3 à une autre. `mode_adoption` est un enum exclusif : il lui faut une
  règle écrite (recommandation : un scrutin public sur l'ensemble de la **version finale** prime
  sur un 49.3 antérieur ; un 49.3 terminal prime sur un scrutin d'une version antérieure).
- Nuance de fond à graver dans le libellé : voter la censure d'un groupe rival n'est pas la seule
  manière de s'opposer au texte — des députés hostiles au texte refusent la motion d'un autre
  groupe. « A voté la censure = a activement tenté de rejeter la loi » est procéduralement exact
  (la censure fait tomber le texte) mais ne doit jamais glisser vers « les autres soutenaient » —
  le libellé v0.1 §4.4 le dit déjà ; le verrouiller dans la charte.

### 2.5 Ratifications : l'exclusion catégorielle contredit le routage mécanique

v0.1 §2 exclut « ratifications de conventions/traités » en bloc ; v0.3 §1.2 route par « scrutin
public sur l'ensemble ». Les deux règles divergent exactement sur les cas intéressants : la
ratification du CETA a fait l'objet d'un scrutin public serré et hautement signifiant
(juillet 2019). **Règle corrigée : « ratification adoptée sans scrutin public » = exclue ; une
ratification avec scrutin public sur l'ensemble est jugeable.**

### 2.6 Le critère « 100 % mécanique » est une fiction partielle — l'assumer

- La qualification « sur l'ensemble » se détecte en parsant le champ `objet` du scrutin —
  **du texte libre**, pas un champ structuré fiable.
- Les manœuvres procédurales produisent des cas qu'aucune règle générale ne route correctement :
  en juillet 2025 (loi Duplomb), la motion de rejet préalable a été votée **par les soutiens du
  texte** pour court-circuiter le débat et aller directement en CMP — il n'existe donc aucun vote
  AN de première lecture sur le fond.

**Correctif.** Prévoir une table `vote_reference_override` **curatée à la main, publique,
versionnée, justifiée cas par cas**. C'est plus honnête — et plus défendable au sens de la
charte — que de prétendre à un critère intégralement mécanique qui ne l'est pas. La frontière
faits/éditorial de v0.3 reste intacte : l'override est une décision éditoriale *tracée*, pas une
retouche silencieuse de faits.

### 2.7 Modéliser des mandats, pas des élus

Le modèle `Elu` (id, nom, circonscription, groupe_id) ne peut représenter ni les élections
partielles (plusieurs en législature 17, dont après annulations), ni les suppléants de ministres,
ni les changements de groupe, ni « ta circonscription a eu deux députés sur la période jugée ».

**Correctifs.**

- Entité **`Mandat`** : `elu_id`, `circonscription`, `date_debut`, `date_fin`, `cause_fin` ;
  une circonscription = une chronologie de titulaires.
- **Affiliation de groupe datée** (l'étiquette au moment du scrutin figure dans la donnée
  scrutin elle-même : l'utiliser comme source pour les agrégats par groupe).
- Au reveal : « ta circo a eu 2 députés sur tes 14 lois » est un état de première classe de
  l'UI, pas un cas d'erreur.
- **Résolution adresse → circonscription : 100 % côté client** (table communes→circos embarquée,
  désambiguïsation manuelle pour les communes à cheval sur plusieurs circos). Un géocodage par
  appel serveur ferait transiter la localisation de l'utilisateur — trahison directe du
  local-first juré par l'architecture.

---

## 3. La boucle utilisateur a des trous en plein centre

### 3.1 Révision post-reveal — non spécifiée

Zéro ligne en cinq versions sur la question : **peut-on modifier sa position après avoir vu le
reveal ?** Si oui sans précaution : biais de conformité (je découvre que « mon » groupe a voté
pour, je corrige mon −1 en +1) et tout le récit « à froid » s'effondre. Si non : il faut le
concevoir. L'`horodatage_local` unique de `PositionCitoyen` implique aujourd'hui un écrasement
silencieux — le pire des trois mondes.

**Recommandation** : verrou par loi au moment du reveal, ou édition avec **historique** où le
score « à froid » est calculé sur la version pré-reveal (les deux versions coexistent,
étiquetées). Dans tous les cas : décision écrite.

### 3.2 Cadence du reveal — LE choix de design manquant

Reveal par carte (implicite v0.1 §7) : dès la 3ᵉ loi, le citoyen a appris la cartographie
politique des thèmes — la cécité au parti se dégrade carte après carte. Reveal **par lot**
(juger N, révéler N) préserve l'aveuglement plus longtemps et structure des « sessions » de
jugement cohérentes avec l'esprit « à froid ». C'est le choix de design central du produit ;
il n'est posé nulle part. **Recommandation : par lot (N = 5), avec reveal à la demande une fois
le lot complété.**

### 3.3 Persistance locale et sync — le sujet difficile du local-first

- **Safari (ITP) peut purger le stockage local (IndexedDB compris) après ~7 jours sans visite**
  — précisément le pattern d'usage d'un produit « froid, basse fréquence ». L'utilisateur revient
  au digest mensuel : ses 20 jugements ont disparu. À spécifier comme exigences de premier rang :
  `navigator.storage.persist()`, PWA installable, **export/import fichier en un clic** (format
  documenté, chiffrable), test de récupération.
- **La sync E2E mérite une vraie spec, pas une phrase.** « Positions chiffrées côté client avant
  envoi » (v0.1 §5) ouvre le vrai sujet : dérivation et garde de la clé, perte d'appareil,
  récupération (custodial = retour du risque ; non-custodial = perte de clé définitive — à dire
  à l'utilisateur), rotation, multi-appareils concurrent. C'est un des plus beaux morceaux
  d'ingénierie du projet : le traiter comme tel, avec son propre document.
- **Incohérence d'invariant à résoudre.** v0.5 : « aucun vecteur de positions individuel ne
  quitte jamais l'appareil ». Mais v0.1 prévoit la sync (un vecteur individuel **chiffré** sort)
  et v0.2 le BYO-key (positions envoyées **en clair** au fournisseur LLM choisi, souvent hors
  UE). Reformuler l'invariant honnêtement — « aucune position individuelle ne parvient en clair
  à *nos* serveurs ; rien d'individuel ne sort sans acte explicite de l'utilisateur » — et
  étiqueter le BYO-key comme **exception explicite** à l'invariant, pas comme un cas compatible.

### 3.4 Version du résumé jugé

Les résumés sont versionnés (v0.3 §2)… mais `PositionCitoyen` ne stocke pas la version jugée.
Si un résumé est corrigé après contestation — le mécanisme prévu par la charte ! — des jugements
ont été rendus sur une information erronée, sans notification ni invalidation possibles.
**Correctif** : `resume_version` dans `PositionCitoyen` + règle de matérialité (correction
mineure vs substantielle) déclenchant « ce résumé a changé depuis ton avis — relire / rejuger ? ».

### 3.5 Compléments de boucle

- **« Sans avis » ≠ « passer ».** Une seule modalité pour deux intentions (« je n'ai pas
  d'opinion » vs « je jugerai plus tard ») : le taux de sans-avis (flux C de v0.5) mesurera un
  mélange ininterprétable. Deux états distincts ; seul « sans avis » est définitif.
- **L'ordre du deck après l'amorçage est un acte éditorial** (effet de primauté) : critère
  documenté et versionné, comme le lot d'amorçage (chronologique, ou tirage stratifié par thème
  avec graine locale).
- **Lois omnibus** : une position unique −2..+2 sur un texte à 8 volets est une perte
  d'information structurelle — et le vote des députés étant lui aussi global, une congruence
  par volet est *impossible par construction*. Assumer la limite, l'afficher (badge
  « loi multi-volets », volets énumérés sans hiérarchie, cf. charte §2.1), et la documenter
  dans la méthodo plutôt que la laisser découvrir par un critique.

---

## 4. Le risque épistémique : un reveal qui n'apprend rien

C'est le risque produit n° 1, et il est structurel, pas hypothétique :

- **Le corpus filtré est étroit et biaisé.** Les budgets — les lois les plus structurantes —
  passent au 49.3 (hors score) ; une grande part des lois promulguées sont des ratifications
  (exclues sauf scrutin public, §2.5) ; beaucoup du reste passe à main levée (exclu). Ce qui
  reste sur-représente les textes conflictuels *et* les textes consensuels votés solennellement.
- **Les scrutins quasi unanimes ne discriminent pas.** Un score calculé majoritairement sur des
  votes à 500 contre 30 donnera ~80 % de congruence avec *tous* les groupes : un reveal qui
  n'apprend rien.
- **La discipline de groupe rend le reste prévisible.** Un citoyen pro-gouvernement découvrira
  que les députés du bloc gouvernemental votent comme lui ; un opposant, l'inverse. Le produit
  risque d'être une machine à confirmer les appartenances — sauf si la valeur se déplace vers ce
  qui surprend : les **divergences** (v0.2 §2.1), les dissidences, les abstentions, le
  par-thème.
- **« Législature en cours uniquement » remet le compteur à zéro à chaque dissolution** — et la
  période en est riche. Le corpus est l'otage d'un décret.
- Remarque d'honnêteté sur « aveugle au parti » : pour les lois saillantes (retraites,
  immigration), le citoyen sait qui gouverne — l'anonymat est partiel par nature. La vraie
  valeur du dispositif est le **jugement structuré à froid**, pas une cécité parfaite ;
  le formuler ainsi évite de survendre.

### Le dry-run comme oracle de conception

Avant de figer les règles (pas pour décider si le projet mérite d'exister — il est déjà décidé) :
un script sur l'open data AN de la législature courante qui mesure :

1. **Taille du corpus jugeable** par la règle v0.1/v0.3, et ce que chaque exclusion coûte
   (combien de 49.3, de main levée, de ratifications, de CMP sans scrutin).
2. **Distribution de participation** des scrutins de référence retenus (→ règle solennel vs
   dernier scrutin, §2.3).
3. **Distribution de polarisation** (marge pour/contre) → combien de scrutins discriminants.
4. **Simulation de profils citoyens synthétiques** (5-6 archétypes) → les scores de groupes
   s'écartent-ils d'au moins ~10 points ? Le top/bottom députés est-il stable ou du bruit ?
5. **Inventaire des cas tordus réels** (§2.1-2.6) sur la législature : chaque règle écrite est
   confrontée à chaque loi réelle, et chaque exception alimente `vote_reference_override`.

Si la discriminance est faible : les leviers sont **multi-législatures** (élargir le corpus dans
le temps — le modèle de données doit le permettre de toute façon, cf. §2.7 et la fragilité aux
dissolutions), l'affichage premier des **divergences** plutôt que du score global, et une vue
« scrutins disputés » séparée. Le choix entre ces leviers se fait sur données, pas sur intuition.

> **Ce produit est un VAA — et c'est une chance.** Les Voting Advice Applications (Wahl-O-Mat
> allemand, smartvote suisse, euandi européen) constituent un champ de recherche établi, avec
> deux acquis directement réutilisables : la **sélection d'énoncés discriminants** (leur réponse
> au problème « matching plat » — le Wahl-O-Mat retient ~38 thèses sur des centaines) et les
> **formules de matching** étudiées et comparées (distances, intensité, traitement du neutre).
> S'y adosser règle aussi la question du partenariat académique appelé par v0.3 §4.3 : un labo
> de science politique a toutes les raisons de co-concevoir la méthodo d'un VAA sur votes réels —
> dès la phase méthodo, pas après le build.

---

## 5. Excellence d'ingénierie (monde idéal)

La pile complète est l'objectif ; la revue porte donc sur *comment la rendre excellente*, pas sur
son périmètre.

- **Une seule implémentation du score, partout.** Rust → WASM (web) et UniFFI (mobiles) dès le
  premier jour élimine par construction tout problème de parité entre implémentations. Corollaire
  à spécifier : **arithmétique entière** (poids ×2, scores en millièmes) plutôt que flottants —
  l'égalité bit à bit entre cibles devient trivialement testable avec les vecteurs d'or (§1) en CI.
- **ETL de qualité forteresse.** Le schéma de l'open data AN **change entre législatures** et sa
  qualité varie : fixtures archivées par législature dans le dépôt, tests de contrat sur
  l'ingestion, **property-based testing** (proptest) sur les invariants (totaux de scrutins
  réconciliés, tout `elu_id` résout vers un mandat couvrant la date, toute loi a sa source),
  **fuzzing** des parseurs XML/JSON (cargo-fuzz). La règle v0.3 « re-dériver, jamais retoucher »
  devient exécutoire : le pipeline refuse de produire si un invariant casse.
- **Le dataset versionné est l'artefact de pérennité ; l'API le sert.** Releases signées +
  checksums (déjà en v0.4 §5), **builds reproductibles**, provenance par enregistrement (déjà
  v0.3 §1.4). L'API Hono est une couche de confort au-dessus d'artefacts immuables
  (content-hash, ETags, cache public) — c'est cette hiérarchie qui garantit la forkabilité et la
  survie du commun (v0.3 §4.5), quel que soit le destin du serveur.
- **LLM : le vrai défi est le grounding sur des textes longs.** Une loi de finances fait des
  centaines de pages ; aucun modèle on-device ne la tient en contexte. Spécifier : unité de
  grounding = **l'article** (la structure Légifrance la donne), retrieval local sur les articles,
  **citations ancrées** (numéro d'article, lien), « non couvert par le texte » par défaut. Et un
  **harness d'évaluation publié** : jeu de questions/réponses de référence par loi, scores par
  provider, dans le dépôt — l'éval publique est au LLM ce que la charte est aux résumés. Détail
  de spec à corriger : `fn answer_grounded(&self, …) -> Answer` doit être async, retourner un
  `Result`, et prévoir le streaming — la signature actuelle est intenable pour des providers
  réseau à travers WASM et UniFFI.
- **Flux B (v0.5) : construit, et publié sous condition statistique.** La DP locale est un beau
  sujet ; l'honnêteté épistémique exige de ne **publier** un agrégat que lorsque la taille de
  cohorte rend le bruit ε interprétable (en deçà : collecte oui, publication non), avec
  intervalle d'incertitude affiché et ε public (déjà prévu). Le caveat d'auto-sélection de
  v0.5 §4.3 reste affiché en clair sur chaque agrégat.
- **Notifications : résoudre la contradiction, pas la contourner.** Le push (web/mobile) exige de
  stocker des tokens d'abonnement côté serveur — des identifiants par appareil, dans un projet
  qui se vante de n'en émettre aucun (v0.5 §3). Traitement « choix éclairé » cohérent avec v0.2
  §4.1 : digest in-app à l'ouverture + RSS/newsletter par défaut ; push opt-in avec son
  trade-off affiché ; **UnifiedPush** supporté sur Android (cohérence souveraineté, utilisateurs
  dégooglisés). Et séquencement corrigé : la notification part **après** publication du résumé
  (v0.3 §1.5 déclenche aujourd'hui rédaction et notification en parallèle — on notifierait une
  carte sans résumé).
- **Accessibilité en livrable de premier rang.** RGAA audité réellement (pas « visé »), **FALC
  comme version de chaque résumé** (presque personne ne le fait ; pour un outil dont la thèse est
  la légitimité démocratique, c'est un différenciateur de mission), glossaire contextuel (déjà
  prévu), graphes du niveau 0 doublés de tableaux de données accessibles.
- **Le threat model oublie la compromission du dépôt officiel.** v0.4 couvre le fork malveillant,
  pas la prise de contrôle du dépôt — or le dépôt *est* le moat éditorial et la preuve
  d'historique. 2FA matériel, branches protégées, **commits signés**, et à terme revue croisée
  obligatoire sur la couche éditoriale.

---

## 6. Angles juridiques manqués

1. **Les élus sont aussi des personnes concernées RGPD.** Les cinq versions pensent « art. 9
   citoyen » ; or le produit **score des personnes physiques nommées** (congruence,
   participation, signal censure). Les votes sont des données manifestement rendues publiques
   (art. 9.2.e) — mais le traitement reste soumis au RGPD : base légale documentée (intérêt
   légitime / liberté d'information, art. 85), **exactitude** (art. 16 — directement percutée
   par les mises au point, §2.2), **droit d'opposition** (art. 21 — refusable pour un
   traitement d'intérêt public, mais la demande doit être *instruite*). Il manque un **4ᵉ canal**
   dans v0.4 §4 : « demandes d'exercice de droits RGPD par un élu », distinct des trois autres.
2. **AI Act, art. 50** : un assistant conversationnel grand public sur des textes de loi relève
   des obligations de transparence applicables **août 2026** — donc avant les niveaux 1/2.
   À ajouter à la checklist de revue juridique de v0.4 §3.
3. **Fiscalité de l'association.** Encaisser un abonnement (tier souverain, v0.2 §5) dans une
   asso 1901 visant un agrément d'intérêt général soulève gestion désintéressée, sectorisation /
   filialisation, fiscalisation des activités lucratives — avec des effets possibles sur le
   mécénat espéré. Avis fiscal **avant** de figer l'open-core dans les statuts.
4. **La défense anti-fork de v0.4 §5 repose sur une marque non déposée** (point ouvert depuis
   v0.1). Et le nom est doublement à trancher : « Nous Président » promet un président pour un
   produit qui matche des *députés* (en plus de la connotation 2012), et le dossier s'appelle
   déjà `mes-elus`. Trancher, déposer à l'INPI, *puis* communiquer.
5. **Créer l'association et nommer le directeur de publication avant la mise en ligne publique**
   (v0.3 §4.1 le dit « sans attendre » — en faire un *blocker* de lancement) : sinon la
   responsabilité LCEN est portée personnellement.
6. Pour mémoire — déjà identifié et bien vu : régime des sondages (loi du 19 juillet 1977) pour
   la publication d'agrégats d'opinion (v0.5 §4.1), avec sa sensibilité particulière en période
   électorale.

---

## 7. Positionnement : écrire la page « pourquoi pas Datan »

Vérifié le 12/06/2026 : **Datan propose déjà un quiz « savoir si vous avez les mêmes convictions
que votre député »**, plus des votes décryptés et des statistiques par député/groupe. Les specs
ne le citent que comme source de données (v0.1 §5, rétrogradé « confort » en v0.3 §1.1).

La différenciation réelle existe et elle est forte — mais elle n'est argumentée nulle part :

| Axe | Datan | Ce projet |
|---|---|---|
| Corpus | Scrutins choisis (votes « clés ») | **Toutes** les lois adoptées, critère public |
| Moment du jugement | Étiquettes visibles | **À l'aveugle, à froid, avant reveal** |
| Données citoyennes | Serveur | **Local-first, art. 9 by design** |
| Temporalité | Quiz ponctuel | **Congruence cumulative** dans le temps |
| Gouvernance | Site éditorial | **Commun** : données + méthodo + charte versionnées |

L'exercice (une page) vaut comme test de positionnement et deviendra le pitch. À nourrir des
leçons du créneau : **Elyze** (viralité massive en 2022, controverses méthodologiques et RGPD,
abandon post-élection — leçon : la méthodo opposable n'est pas optionnelle), **TheyWorkForYou**
(résumés de votes durablement contestés au Royaume-Uni — leçon : toute *dérivation* d'un vote est
un acte éditorial qui doit être contestable), **NosDéputés** (polémiques « présence » — leçon :
§2.2), **La Fabrique de la Loi** (la navette, complémentaire).

---

## 8. Quick wins

- **Consolider les 5 addenda en une spec unique** + journal de décisions (ADR). Les
  contradictions inter-versions existent déjà : invariant v0.5 vs sync v0.1 / BYO-key v0.2
  (§3.3) ; « top/bottom élus » v0.2 vs « aucun palmarès » v0.4 (un classement personnel des 577
  se capture d'écran — le limiter aux groupes, ou afficher le dénominateur par paire en dur dans
  le composant) ; exclusion des ratifications v0.1 vs routage v0.3 (§2.5).
- **Taxonomie de thèmes : partir d'un sous-ensemble d'EuroVoc en français** (~15 thèmes
  citoyens). Ferme un point ouvert depuis v0.1 et prépare la phase UE (le mapping était déjà
  prévu dans ce sens).
- **Licence du dataset : trancher « Etalab/ODbL »** — deux logiques incompatibles (permissive vs
  share-alike) séparées d'un slash. Recommandation : **Licence Ouverte 2.0**, alignée sur les
  sources. La couche éditoriale peut vivre sous CC BY-SA si l'attribution-défense compte.
- **SLA éditorial public** (« résumé sous 30 jours après promulgation ») : le « froid » du
  produit le permet, autant le contractualiser — et chiffrer le backlog initial (lois jugeables ×
  2-4 h de rédaction honnête par loi) pour planifier la rédaction comme un chantier à part
  entière, avec **vie-publique.fr comme matière première sourcée** (utile comme source citée ;
  pas comme autorité de neutralité — c'est un service gouvernemental).
- **Les exports embarquent la pondération thématique appliquée** : sinon le citoyen règle ses
  poids jusqu'au chiffre qui l'arrange, puis partage (v0.4 autorise le partage de son parcours).
- **Financement aligné commun** : NGI0 / NLnet (privacy + commons + open source) est exactement
  la cible du projet — à ajouter aux pistes « compatibles » de v0.3 §4.4.

---

## 9. Décisions à trancher (les tiennes — avec recommandations)

| # | Décision | Recommandation de la revue |
|---|---|---|
| 1 | Abstention de l'élu dans le score | **Exclue** du ratio + indicateur séparé (§1) |
| 2 | Cadence du reveal | **Par lot de 5**, reveal à la demande (§3.2) |
| 3 | Révision post-reveal | **Verrou par loi** (ou historique pré/post, score à froid sur le pré) (§3.1) |
| 4 | Mises au point | Score sur la **position rectifiée**, affichage des deux (§2.2) |
| 5 | Groupe affiché au reveal | **Groupe à la date du scrutin** (donnée scrutin) ; vue « groupe actuel » secondaire (§1) |
| 6 | Périmètre temporel du corpus | Modèle **multi-législatures** d'office ; périmètre UX décidé après dry-run (§4) |
| 7 | Le nom | Trancher (`mes-elus` est déjà plus juste sémantiquement), déposer INPI, puis communiquer (§6.4) |

---

## 10. Roadmap de construction complète (ordonnée par dépendances)

0. **Dry-run open data** (§4) — l'oracle : corpus, participation, polarisation, profils
   synthétiques, inventaire des cas tordus réels.
1. **Formule exécutable** (§1) — pseudo-code exhaustif + vecteurs de test publiés.
2. **Modèle de données v2** — `Mandat`, affiliations datées, `decision_cc`, mises au point,
   `non_votant`, 0..n motions de censure, `resume_version`, multi-législatures,
   `vote_reference_override`.
3. **Consolidation** des 5 addenda en spec v1.0 + journal de décisions (§8) — intégrant les
   décisions du §9.
4. **ETL Rust** (fixtures par législature, property tests, fuzzing) → **dataset signé,
   reproductible** → API en couche au-dessus (§5).
5. **Charte de neutralité** complète + backlog de résumés + **FALC** + glossaire (§5, §8).
6. **App web** — scoring WASM (arithmétique entière), deck, reveal par lot, export/import,
   `storage.persist()`, RGAA.
7. **Niveau 0 analytics** + miroir (v0.2) — divergences mises en avant (§4).
8. **Providers LLM** (local → BYO-key → Clever) — grounding par article, citations ancrées,
   harness d'éval publié, trait async (§5).
9. **Mobiles** Kotlin/Swift via UniFFI + UnifiedPush (§5).
10. **Sync E2E** — avec sa spec de gestion de clés dédiée (§3.3).
11. **Télémétrie** v0.5 — flux A, puis C, puis B sous condition statistique (§5).

Transverse, avant toute mise en ligne publique : association + directeur de publication + revue
juridique (§6) ; comité scientifique dès la phase méthodo (§4).

---

*Revue du 12 juin 2026 — contre-revue indépendante croisée, faits vérifiés à cette date
(décision CC n° 2023-863 du 25/01/2024 ; censure du 04/12/2024 ; quiz Datan ; AI Act art. 50
applicable août 2026). Les specs v0.1 → v0.5 n'ont pas été modifiées : chaque point de cette
revue est une proposition d'intégration pour la consolidation v1.0.*
