export const meta = {
  name: 'boussole-politique-dry-run',
  description: "Dry-run analytique sur l'open data AN par-dessus une fondation figée (corpus.json) : 7 analyses en éventail, vérification adverse de chacune, puis synthèse en rapport unique.",
  phases: [
    { title: 'Analyse', detail: '7 analyses indépendantes du corpus jugeable' },
    { title: 'Vérification', detail: 'recalcul adverse du chiffre-clé de chaque analyse par une autre méthode' },
    { title: 'Synthèse', detail: 'rapport dry-run consolidé répondant aux questions de conception' },
  ],
};

const DIR = '/home/cos/Bureau/dev/boussole-politique/dry-run';
const CRIB = `
ENVIRONNEMENT (déjà en place, fondation vérifiée — NE PAS reconstruire) :
- Module Python : ${DIR}/scripts/anlib.py. Charge ainsi :
    import sys; sys.path.insert(0, '${DIR}/scripts'); import anlib, json
- Corpus FIGÉ (consomme-le, ne le re-dérive pas) : ${DIR}/out/corpus.json
    { funnel, by_leg:{16,17}, n_lois:159, lois:[ {dossier_uid,titre,procedure,ref_leg,ref_numero,
      ref_acte,ref_solennel,saisine_cc,has_cmp,lecture_definitive,nouvelle_lecture,is_ratification,
      version_drift, votes:[{acte,leg,numero,date,type(SPO|SPS),sort,pour,contre,abst,nonvotant,votants,has_mise_au_point}] } ] }
    Le "vote de référence" d'une loi = celui dont numero==ref_numero (dernier vote AN public d'ensemble).
- API anlib utile :
    anlib.load_scrutins(16|17) -> tuple[Scrutin] ; Scrutin a : numero,date,legislature,type_code,sort,objet,
      d_pour/d_contre/d_abst/d_nonvotant, nb_votants, has_mise_au_point, et la méthode
      .positions_nominales() -> itère (acteur_ref, position∈{pour,contre,abstention,nonvotant}, par_delegation:bool, groupe_ref, cause).
      groupe_ref = groupe AU MOMENT DU VOTE (PO...). C'est la source correcte pour agréger par groupe.
    anlib.load_all_scrutins() -> dict {(leg,numero):Scrutin} ; anlib.load_all_dossiers() -> {uid:Dossier}
      Dossier a : titre, procedure, acte_codes(set), .saisine_cc, .has_cmp, .lecture_definitive, .promulguee, .an_vote_refs()
    anlib.load_dossiers(16|17) ; un PA acteur AMO10 : ${DIR}/data/amo10-17/json/acteur/PA*.json ;
      organes (groupes) : ${DIR}/data/amo10-17/json/organe/PO*.json. SIEGES_AN=577.
- Pièges (voir ${DIR}/SCHEMA-NOTES.md) : objet-vs-tableau (anlib.as_list), apostrophes ' vs ’,
  "absent" n'existe PAS dans la donnée (à dériver), nonVotants ont une cause (causePositionVote),
  certains acteurRef des scrutins ne sont PAS dans AMO10 (députés partis — trou à quantifier).
CONSIGNES :
- Écris un Python net dans ${DIR}/scripts/<id>.py, exécute-le, et ÉCRIS ton rapport détaillé (chiffres,
  tableaux markdown, échantillons nommés réels) dans ${DIR}/out/<id>.md ET tes chiffres machine dans ${DIR}/out/<id>.json.
- Donne des chiffres EXACTS et des EXEMPLES réels (numéros de scrutin, titres de loi). Pas de généralités.
- Sépare toujours leg 16 (close) et leg 17 (en cours). Sois quantitatif et honnête sur les limites.
`;

const ANALYSES = [
  {
    id: 'q1-funnel',
    review: '§4 (corpus étroit/biaisé) + §2.5 (ratifications)',
    titre: 'Entonnoir du corpus & coût de chaque exclusion',
    mandat: `Quantifie l'entonnoir : lois promulguées -> jugeables (vote public AN sur l'ensemble). Pour CHAQUE exclusion,
chiffre ce qu'elle retire et donne des exemples nommés : (a) ratifications sans vote public, (b) lois passées à main levée,
(c) budgets/lois de finances passés au 49.3 (PLF/PLFSS/PLFR — identifie-les nommément ; ce sont les lois les plus structurantes),
(d) résolutions/motions (jamais des lois). Croise avec funnel de corpus.json. Donne la taille finale du corpus jugeable
par législature et la part que représentent les textes les plus importants PERDUS. Évalue : le corpus restant est-il
représentatif de l'activité législative, ou biaisé vers certains types de textes ?`,
  },
  {
    id: 'q2-polarisation',
    review: '§4 (le reveal plat — risque épistémique n°1)',
    titre: 'Participation & polarisation des votes de référence',
    mandat: `Sur les 159 votes de référence : distribution de la PARTICIPATION (votants/577, et exprimés/577) et de la
POLARISATION. Définis un vote "discriminant" (ex. la minorité fait >=20% des exprimés) vs "quasi-unanime" (minorité <10%).
Donne : % de votes quasi-unanimes, médiane de participation, histogramme de la marge gagnante. CRUCIAL : si une grande part
des votes de référence sont quasi-unanimes, un score de congruence calculé dessus donnera ~80% pour TOUS les groupes =
reveal qui n'apprend rien. Mesure-le. Sépare leg16/leg17. Donne les 10 votes les plus serrés et les plus unanimes (titres réels).`,
  },
  {
    id: 'q3-version',
    review: '§2.1 (version votée ≠ promulguée)',
    titre: 'Décalage version votée / version promulguée (CC, CMP, lecture)',
    mandat: `Mesure combien de lois jugeables ont un texte voté (au vote de référence) potentiellement DIFFÉRENT du texte promulgué :
(a) saisine du Conseil constitutionnel (champ saisine_cc) — et tente de détecter si le CC a CENSURÉ (cherche dans le dossier
les actes CC-CONCLUSION / leur statut, via anlib.load_all_dossiers()[uid].raw) ; (b) passage en CMP (has_cmp) avec vote de
référence en lecture antérieure (ref_acte = AN1-DEBATS-DEC alors que le dossier a une CMP postérieure) ; (c) nouvelle lecture /
lecture définitive. Pour chaque cas, donne le compte et des exemples nommés (ex. loi immigration 2024 si présente : saisine CC
et censure partielle). Conclus : sur quelle fraction du corpus le citoyen jugerait-il un texte qui n'est pas celui promulgué ?`,
  },
  {
    id: 'q4-mandats',
    review: '§2.2 ("absent" n\'existe pas) + §2.7 (mandats/groupes datés)',
    titre: 'Dérivation de l\'absence, trou de données mandats, groupes datés',
    mandat: `Sur les votes de référence : (a) compte les acteurRef présents dans les ventilations qui NE SONT PAS dans AMO10
(data/amo10-17/json/acteur/) = trou "députés partis" ; quantifie-le, c'est ce qui rend la dérivation d'"absent" risquée.
(b) Pour un vote donné, peut-on dériver "absent" = (membres de l'AN à la date) − (votants+nonvotants listés) ? Estime la
composition (groupes PO, nombreMembresGroupe est dans la ventilation) et montre la difficulté. (c) Compte les votes par
délégation (par_delegation=True) — "présence" est donc impropre. (d) Taxonomie des causePositionVote des nonVotants (président
de séance, etc.) avec comptes. (e) Détecte les changements de groupe : un même acteurRef apparaît-il sous des groupe_ref
différents selon les scrutins ? Combien de députés concernés ? Conclus sur la faisabilité d'un indicateur "présence" honnête.`,
  },
  {
    id: 'q5-miseaupoint',
    review: '§2.2 (mises au point / art.16 RGPD)',
    titre: 'Mises au point (corrections de vote) et qualité de données',
    mandat: `Combien des 159 votes de référence ont une miseAuPoint (has_mise_au_point) ? Pour ceux-là, ouvre le scrutin
(anlib.load_all_scrutins()[(leg,numero)].raw['scrutin']['miseAuPoint']) et compte les corrections individuelles par type
(pours/contres/abstentions/nonVotants). Une correction change la position d'un député : pourrait-elle FAIRE BASCULER le signe
de congruence d'une paire citoyen-député sur cette loi ? Donne des exemples nommés (député, loi, correction). Évalue l'enjeu
art.16 RGPD (exactitude) : afficher le vote brut sans la mise au point publiée par l'AN = donnée inexacte sur une personne nommée.`,
  },
  {
    id: 'q6-censure',
    review: '§2.4 (branche 49.3 / motions de censure)',
    titre: 'Motions de censure & branche 49.3',
    mandat: `Recense toutes les motions de censure (anlib.load_scrutins : type_libelle=="motion de censure") en leg16 et leg17.
Distingue 49.2 (censure spontanée) vs 49.3 (réponse à engagement de responsabilité sur un texte) via le titre ("alinéa 2"/"alinéa 3").
Compte-les, donne le sort de chacune (la motion du 2024-12-04 n°519 a été ADOPTÉE → gouvernement renversé, texte tombé). Combien
de motions par date (plusieurs déposées le même jour par groupes différents = le modèle SignalRejet singulier de la spec est faux) ?
Tente de relier les 49.3 aux lois de finances promulguées (les budgets exclus du corpus jugeable). Conclus : combien de lois
"structurantes" passent par cette branche hors-score, et le modèle de données spec (1 motion) tient-il face à la réalité (0..n) ?`,
  },
  {
    id: 'q7-simulation',
    review: '§1 (formule) + §4 (le reveal discrimine-t-il ?)',
    titre: 'Simulation de congruence — le reveal discrimine-t-il ?',
    mandat: `LE test central. Implémente la formule de congruence PINNÉE suivante (et AUCUNE autre) :
- citoyen sur loi L : v∈{-2,-1,+1,+2} ; abstention/skip exclus.
- député au vote de référence de L : pour->+1, contre->-1 ; abstention/nonvotant/absent -> EXCLUS du score.
- paire (citoyen,député) sur les lois où les DEUX ont une valeur : accord si sign(v)==sign(dir) ; poids=|v| ;
  congruence = Σ(poids des accords)/Σ(poids des lois comptées) ; garde aussi le dénominateur (n lois comptées).
Utilise positions_nominales() (groupe_ref = groupe au moment du vote) sur les votes de référence du corpus.
ANALYSES À PRODUIRE :
(1) DÉPUTÉ-COMME-CITOYEN (profils réels, non circulaires) : prends chaque député comme un "citoyen" (ses propres votes ±,
   pour->+2, contre->-2) et calcule sa congruence avec CHAQUE groupe. Mesure l'ÉCART de congruence entre groupes (max-min).
   Un gauche-comme-citoyen doit scorer haut avec la gauche, bas avec la droite. Donne la distribution de cet écart : si l'écart
   médian est faible (<~15pts), le reveal ne discrimine pas.
(2) Congruence par GROUPE — calcule-la de DEUX façons et compare : (a) moyenne des congruences paire-à-paire des membres,
   (b) position majoritaire du groupe par loi puis congruence. Divergent-elles ? (la spec ne tranche pas — montre l'impact.)
(3) PROBLÈME DU DÉNOMINATEUR : distribution du nb de lois comptées par paire ; instabilité du classement top/bottom députés
   quand le dénominateur est petit (un "100% sur 3 lois" écrase un "82% sur 60 lois"). Quantifie.
(4) Quelques archétypes synthétiques (toujours-pour, toujours-contre, suiveur-de-majorité, aléatoire-graine-fixe) pour sanity.
CONCLUS sans complaisance : sur la donnée réelle, le score de congruence sépare-t-il les groupes, ou est-ce une machine à ~80% ?`,
  },
];

const ANALYSIS_SCHEMA = {
  type: 'object',
  required: ['id', 'headline', 'metrics', 'verdict', 'report_path'],
  properties: {
    id: { type: 'string' },
    headline: { type: 'string', description: 'LE chiffre-clé quantifié, en une phrase' },
    metrics: { type: 'object', description: 'paires clé->valeur (nombres/chaînes) reproductibles', additionalProperties: true },
    examples: { type: 'array', items: { type: 'string' }, description: 'exemples nommés réels (scrutin/loi)' },
    verdict: { type: 'string', description: 'conclusion de conception : ce que ça implique pour le produit' },
    surprises: { type: 'array', items: { type: 'string' } },
    report_path: { type: 'string' },
  },
};

const VERIFY_SCHEMA = {
  type: 'object',
  required: ['id', 'recomputed', 'matches', 'method', 'confidence'],
  properties: {
    id: { type: 'string' },
    recomputed: { type: 'string', description: 'le chiffre-clé recalculé par TOI, indépendamment' },
    matches: { type: 'boolean', description: 'concorde-t-il avec le headline de l\'analyse ?' },
    method: { type: 'string', description: 'méthode indépendante employée (jq, autre calcul...)' },
    discrepancies: { type: 'array', items: { type: 'string' } },
    confidence: { type: 'string', enum: ['haute', 'moyenne', 'basse'] },
  },
};

phase('Analyse');
log(`Fondation figée : 159 lois jugeables (93 leg16 + 66 leg17). Lancement de ${ANALYSES.length} analyses + vérification adverse.`);

const results = await pipeline(
  ANALYSES,
  (a) => agent(
    `Tu es analyste de données parlementaires. Analyse à produire : « ${a.titre} ».\n` +
    `Elle valide/teste ce point de la revue : ${a.review}.\n\nMANDAT :\n${a.mandat}\n${CRIB}\n` +
    `Identifiant de sortie : ${a.id} (donc ${DIR}/scripts/${a.id}.py, ${DIR}/out/${a.id}.md, ${DIR}/out/${a.id}.json). ` +
    `Retourne le JSON structuré demandé.`,
    { label: a.id, phase: 'Analyse', schema: ANALYSIS_SCHEMA }
  ),
  (analysis, a) => analysis == null ? null : agent(
    `Tu es vérificateur adverse. Une analyse « ${a.titre} » a produit ce chiffre-clé :\n` +
    `headline = "${analysis.headline}"\nmetrics = ${JSON.stringify(analysis.metrics)}\n\n` +
    `Ta mission : RECALCULER ce chiffre-clé par une MÉTHODE INDÉPENDANTE (idéalement jq/bash en ligne de commande sur les ` +
    `fichiers bruts ${DIR}/data/..., PAS le script python de l'analyse que tu ne dois pas réutiliser), et dire s'il concorde. ` +
    `Lis ${DIR}/out/${a.id}.md pour comprendre sa méthode, puis recoupe. Si tu trouves un écart, donne le bon chiffre et la cause. ` +
    `Sois sceptique : cherche les double-comptes, les apostrophes ratées, les objet-vs-tableau, les dénominateurs douteux.\n${CRIB}\n` +
    `Retourne le JSON structuré demandé.`,
    { label: `verif:${a.id}`, phase: 'Vérification', schema: VERIFY_SCHEMA }
  ).then((v) => ({ analysis, verify: v }))
);

const ok = results.filter(Boolean);
phase('Synthèse');
log(`${ok.length}/${ANALYSES.length} analyses vérifiées. Synthèse du rapport dry-run.`);

const digest = ok.map((r) => {
  const a = r.analysis, v = r.verify;
  return `### ${a.id}\nheadline: ${a.headline}\nverdict: ${a.verdict}\nmetrics: ${JSON.stringify(a.metrics)}\n` +
    `exemples: ${(a.examples || []).join(' | ')}\nsurprises: ${(a.surprises || []).join(' | ')}\n` +
    `VÉRIF: ${v ? `${v.matches ? 'CONCORDE' : '⚠ ÉCART'} (${v.confidence}) recalc=${v.recomputed}${v.discrepancies && v.discrepancies.length ? ' | ' + v.discrepancies.join('; ') : ''}` : 'manquante'}`;
}).join('\n\n');

const synth = await agent(
  `Tu es l'architecte du projet « Boussole Politique ». Tu as lancé un dry-run sur l'open data réel de l'Assemblée nationale ` +
  `(législatures 16 close et 17 en cours) pour CONFRONTER les règles de tes specs v0.1→v0.5 à la donnée. ` +
  `Voici les résultats des 7 analyses, chacune vérifiée de façon adverse :\n\n${digest}\n\n` +
  `Les rapports détaillés sont dans ${DIR}/out/*.md (lis-les tous pour les tableaux et exemples). ` +
  `La revue critique de référence est dans /home/cos/Bureau/dev/boussole-politique/revue-specs-2026-06-12.md.\n\n` +
  `ÉCRIS le rapport de synthèse dans ${DIR}/out/RAPPORT-DRY-RUN.md, structuré ainsi :\n` +
  `1. Verdict en 5 lignes : le dry-run valide-t-il la faisabilité du produit, et quel est le risque n°1 confirmé ?\n` +
  `2. Le corpus réel (chiffres par législature, coût des exclusions, biais).\n` +
  `3. Le risque du "reveal plat" : tranché par les données (polarisation + simulation). Le score discrimine-t-il OUI/NON, preuves chiffrées.\n` +
  `4. Les pièges de la mécanique parlementaire confirmés par la donnée (version/CC, absent/mandats, mises au point, censure) avec les compteurs réels.\n` +
  `5. Décisions de conception que le dry-run TRANCHE (ex. abstention exclue, vote solennel préféré, multi-législatures obligatoire, formule de groupe à fixer) — chacune appuyée sur un chiffre.\n` +
  `6. Ce que le dry-run NE peut pas trancher et qu'il reste à décider.\n` +
  `7. Tableau de fiabilité : pour chaque analyse, son chiffre-clé et si la vérification adverse a concordé.\n` +
  `Sois quantitatif, cite les nombres réels, honnête sur les limites. Réponds en français. Retourne un résumé en 10 lignes de ton verdict.`,
  { label: 'synthese', phase: 'Synthèse' }
);

return { analyses: ok.length, rapport: `${DIR}/out/RAPPORT-DRY-RUN.md`, verdict: synth };
