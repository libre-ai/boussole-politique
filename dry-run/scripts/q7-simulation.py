#!/usr/bin/env python3
"""
q7-simulation — Simulation de congruence : le reveal discrimine-t-il ?

Valide la revue : §1 (formule pinnée) + §4 (discrimination du reveal).

FORMULE PINNÉE (et aucune autre) :
- citoyen sur loi L : v ∈ {-2,-1,+1,+2} ; abstention/skip exclus.
- député au vote de réf de L : pour->+1, contre->-1 ; abstention/nonvotant/absent -> EXCLUS.
- paire (citoyen,député) sur les lois où les DEUX ont une valeur :
    accord si sign(v)==sign(dir) ; poids = |v| ;
    congruence = Σ(poids des accords) / Σ(poids des lois comptées) ; on garde n (dénominateur).

Source : positions_nominales() (groupe_ref = groupe au moment du vote) sur les votes de réf du corpus.
"""
from __future__ import annotations
import sys, json, os, glob, math, random, statistics
from collections import defaultdict, Counter

sys.path.insert(0, '/home/cos/Bureau/dev/boussole-politique/dry-run/scripts')
import anlib

OUT = '/home/cos/Bureau/dev/boussole-politique/dry-run/out'
CORPUS = json.load(open(os.path.join(OUT, 'corpus.json')))

# ---------------------------------------------------------------------------
# Libellés de groupes (PO -> abrév lisible)
#   leg17 : depuis amo10-17/json/organe/PO*.json (codeType GP)
#   leg16 : non présents dans amo10-17 -> mapping établi par identification nominale
#           (députés ré-élus reconnaissables, vérifié sur scrutin 3966)
# ---------------------------------------------------------------------------
def txt(x):
    if isinstance(x, dict):
        return x.get('#text') or x.get('text') or ''
    return x

GROUP_LABELS = {}
for p in glob.glob('/home/cos/Bureau/dev/boussole-politique/dry-run/data/amo10-17/json/organe/PO*.json'):
    o = json.load(open(p))['organe']
    if o.get('codeType') == 'GP':
        GROUP_LABELS[o['uid']] = o.get('libelleAbrev') or o.get('libelle')

# Mapping leg16 (vérifié par identification nominale sur scrutin 3966, cf. rapport)
LEG16 = {
    'PO800538': 'RE',       # Renaissance/Ensemble (~170)
    'PO800520': 'RN',       # Rassemblement National (~88)
    'PO800490': 'LFI',      # La France insoumise - NUPES (~75)
    'PO800508': 'LR',       # Les Républicains (~62)
    'PO800484': 'DEM',      # Démocrate / MoDem (~50)
    'PO800514': 'HOR',      # Horizons (~30)
    'PO830170': 'SOC',      # Socialistes - NUPES (~31)
    'PO800502': 'GDR',      # Gauche démocrate et républicaine / communistes (~22)
    'PO800532': 'LIOT',     # Libertés, Indépendants, Outre-mer et Territoires (~22)
    'PO800526': 'ECO',      # Écologiste - NUPES (~22)
    'PO793087': 'NI',       # Non-inscrits (~7)
    'PO800496': 'GDR-old',  # apparait dans qq votes anciens
}
GROUP_LABELS.update(LEG16)

# Axe gauche->droite approximatif pour interpréter les écarts (purement descriptif)
AXIS = {
    'LFI': 0, 'GDR': 1, 'ECO': 2, 'SOC': 3, 'DEM': 5, 'RE': 5, 'EPR': 5,
    'HOR': 6, 'LIOT': 5, 'LR': 7, 'DR': 7, 'RN': 9, 'NI': 5, 'NFP': 1,
    'LFI-NFP': 0, 'ECOS': 2, 'UDDPLR': 8,
}

def glabel(po):
    return GROUP_LABELS.get(po, po)

# Groupes "réels" à analyser par législature (on exclut NI / micro-groupes inconsistants
# pour la comparaison de discrimination, mais on les garde dans les données brutes)
MAIN_GROUPS = {
    16: ['LFI', 'GDR', 'ECO', 'SOC', 'DEM', 'RE', 'HOR', 'LIOT', 'LR', 'RN'],
    17: ['LFI-NFP', 'GDR', 'ECOS', 'SOC', 'DEM', 'EPR', 'HOR', 'LIOT', 'DR', 'RN'],
}

# ---------------------------------------------------------------------------
# Construction des matrices de vote par législature
#   dir_by_law[leg][numero][acteurRef] = +1 (pour) / -1 (contre)   [abst/nonvotant EXCLUS]
#   group_of[leg][numero][acteurRef]   = PO du groupe au moment du vote
# ---------------------------------------------------------------------------
sidx = anlib.load_all_scrutins()

# liste des votes de référence par législature
REFS = {16: [], 17: []}
for l in CORPUS['lois']:
    REFS[l['ref_leg']].append((l['ref_numero'], l['titre'], l['ref_acte'], l['dossier_uid']))

# index acteur -> nom (amo10-17, leg17 + ré-élus)
NAMES = {}
for p in glob.glob('/home/cos/Bureau/dev/boussole-politique/dry-run/data/amo10-17/json/acteur/PA*.json'):
    a = json.load(open(p))['acteur']
    uid = txt(a['uid'])
    ec = (a.get('etatCivil') or {}).get('ident') or {}
    NAMES[uid] = (txt(ec.get('prenom', '')) + ' ' + txt(ec.get('nom', ''))).strip()

def name(ref):
    return NAMES.get(ref, ref)

# Pour chaque législature : pour chaque loi de réf, positions nominales
# dir_dep[leg][dep][numero] = +1/-1     (vote du député, abst/nonvotant exclus)
# grp_dep[leg][dep] = Counter des PO (groupe dominant du député sur le corpus)
# grp_at_vote[leg][numero][dep] = PO au moment de CE vote
dir_dep = {16: defaultdict(dict), 17: defaultdict(dict)}
grp_at_vote = {16: defaultdict(dict), 17: defaultdict(dict)}
grp_counter = {16: defaultdict(Counter), 17: defaultdict(Counter)}
law_meta = {16: {}, 17: {}}
# trou AMO10 : acteurRef présents dans scrutins mais absents d'amo10
unknown_actors = {16: set(), 17: set()}
all_actors = {16: set(), 17: set()}

for leg in (16, 17):
    for numero, titre, acte, uid in REFS[leg]:
        s = sidx.get((leg, numero))
        if s is None:
            continue
        law_meta[leg][numero] = {'titre': titre, 'acte': acte, 'date': s.date,
                                 'sort': s.sort, 'type': s.type_code, 'dossier': uid}
        for ref, pos, deleg, gref, cause in s.positions_nominales():
            if ref is None:
                continue
            all_actors[leg].add(ref)
            if ref not in NAMES:
                unknown_actors[leg].add(ref)
            grp_at_vote[leg][numero][ref] = gref
            grp_counter[leg][ref][gref] += 1
            if pos == 'pour':
                dir_dep[leg][ref][numero] = +1
            elif pos == 'contre':
                dir_dep[leg][ref][numero] = -1
            # abstention / nonvotant : EXCLUS (pas d'entrée)

# groupe dominant d'un député sur le corpus (pour l'agrégation "député-comme-citoyen")
dep_group = {16: {}, 17: {}}
for leg in (16, 17):
    for ref, c in grp_counter[leg].items():
        dep_group[leg][ref] = c.most_common(1)[0][0]

# ---------------------------------------------------------------------------
# FORMULE PINNÉE
# ---------------------------------------------------------------------------
def congruence(citizen_votes: dict, dep_dir: dict):
    """citizen_votes: {numero: v in {-2,-1,1,2}} ; dep_dir: {numero: +1/-1}.
    Retourne (congruence_float_or_None, n_lois_comptees, poids_accord, poids_total)."""
    num = 0.0
    den = 0.0
    n = 0
    for numero, v in citizen_votes.items():
        d = dep_dir.get(numero)
        if d is None:          # député abst/nonvotant/absent sur cette loi -> exclue
            continue
        if v == 0:             # citoyen sans valeur -> exclue (ne devrait pas arriver)
            continue
        w = abs(v)
        den += w
        n += 1
        if (v > 0) == (d > 0):
            num += w
    if den == 0:
        return (None, 0, 0.0, 0.0)
    return (num / den, n, num, den)

# ---------------------------------------------------------------------------
# Profil GROUPE : direction par loi
#   (a) pour la congruence paire-à-paire : on calcule contre chaque MEMBRE du groupe.
#   (b) position majoritaire du groupe : maj_dir[leg][grp][numero] = +1/-1
#       (majorité des votants pour/contre du groupe ; abst/nonvotant exclus ; égalité -> None)
# ---------------------------------------------------------------------------
def group_majority_dir(leg):
    """maj[grp][numero] = +1/-1/None selon la position majoritaire des votants du groupe."""
    pour = defaultdict(lambda: defaultdict(int))   # [grp][numero] -> n pour
    contre = defaultdict(lambda: defaultdict(int))
    for numero in law_meta[leg]:
        for ref, g in grp_at_vote[leg][numero].items():
            d = dir_dep[leg][ref].get(numero)
            if d == +1:
                pour[glabel(g)][numero] += 1
            elif d == -1:
                contre[glabel(g)][numero] += 1
    maj = defaultdict(dict)
    for grp in set(list(pour) + list(contre)):
        for numero in law_meta[leg]:
            p = pour[grp].get(numero, 0)
            cc = contre[grp].get(numero, 0)
            if p + cc == 0:
                continue
            if p > cc:
                maj[grp][numero] = +1
            elif cc > p:
                maj[grp][numero] = -1
            else:
                maj[grp][numero] = None  # parfaite égalité -> indéterminé
    return maj

MAJ = {16: group_majority_dir(16), 17: group_majority_dir(17)}

# membres d'un groupe (par groupe dominant)
members_of = {16: defaultdict(list), 17: defaultdict(list)}
for leg in (16, 17):
    for ref, g in dep_group[leg].items():
        members_of[leg][glabel(g)].append(ref)

# ---------------------------------------------------------------------------
# ANALYSE (1) : DÉPUTÉ-COMME-CITOYEN
#   Chaque député devient un "citoyen" : ses propres votes pour->+2, contre->-2.
#   On calcule sa congruence avec CHAQUE groupe (via la position MAJORITAIRE du groupe,
#   méthode (b) — c'est la définition naturelle de "congruence avec un groupe").
#   Écart = max congruence - min congruence sur les groupes principaux.
#   On exclut l'auto-comparaison ? Non : on garde tous les groupes ; le test est de
#   savoir si un député de gauche score haut à gauche / bas à droite.
# ---------------------------------------------------------------------------
def dep_as_citizen_votes(leg, ref):
    """Votes du député en tant que citoyen : pour->+2, contre->-2 (abst/nonvotant exclus)."""
    return {numero: (2 if d > 0 else -2) for numero, d in dir_dep[leg][ref].items()}

def congruence_vs_group_majority(citizen_votes, leg, grp, min_n=1):
    maj = MAJ[leg].get(grp, {})
    dep_dir = {numero: d for numero, d in maj.items() if d is not None}
    return congruence(citizen_votes, dep_dir)

analysis1 = {16: {}, 17: {}}
spread_rows = {16: [], 17: []}
for leg in (16, 17):
    groups = MAIN_GROUPS[leg]
    for ref in dep_group[leg]:
        cv = dep_as_citizen_votes(leg, ref)
        if not cv:
            continue
        own = glabel(dep_group[leg][ref])
        scores = {}
        for grp in groups:
            cong, n, _, _ = congruence_vs_group_majority(cv, leg, grp, min_n=5)
            if cong is not None and n >= 5:   # min 5 lois communes pour stabilité
                scores[grp] = (cong, n)
        if len(scores) < 2:
            continue
        vals = {g: s[0] for g, s in scores.items()}
        gmax = max(vals, key=vals.get)
        gmin = min(vals, key=vals.get)
        spread = vals[gmax] - vals[gmin]
        own_score = vals.get(own)
        own_rank = None
        if own in vals:
            ranked = sorted(vals, key=vals.get, reverse=True)
            own_rank = ranked.index(own) + 1
        spread_rows[leg].append({
            'ref': ref, 'name': name(ref), 'own_group': own,
            'spread': round(spread, 4), 'best_group': gmax, 'best': round(vals[gmax], 4),
            'worst_group': gmin, 'worst': round(vals[gmin], 4),
            'own_score': round(own_score, 4) if own_score is not None else None,
            'own_rank': own_rank, 'n_groups': len(vals),
        })

for leg in (16, 17):
    sp = [r['spread'] for r in spread_rows[leg]]
    own_top1 = sum(1 for r in spread_rows[leg] if r['own_rank'] == 1)
    own_top2 = sum(1 for r in spread_rows[leg] if r['own_rank'] and r['own_rank'] <= 2)
    analysis1[leg] = {
        'n_deputes': len(sp),
        'spread_min': round(min(sp), 4) if sp else None,
        'spread_p10': round(statistics.quantiles(sp, n=10)[0], 4) if len(sp) >= 10 else None,
        'spread_p25': round(statistics.quantiles(sp, n=4)[0], 4) if len(sp) >= 4 else None,
        'spread_median': round(statistics.median(sp), 4) if sp else None,
        'spread_mean': round(statistics.mean(sp), 4) if sp else None,
        'spread_p75': round(statistics.quantiles(sp, n=4)[2], 4) if len(sp) >= 4 else None,
        'spread_p90': round(statistics.quantiles(sp, n=10)[8], 4) if len(sp) >= 10 else None,
        'spread_max': round(max(sp), 4) if sp else None,
        'own_group_is_top1': own_top1,
        'own_group_is_top2': own_top2,
        'own_top1_pct': round(100 * own_top1 / len(sp), 1) if sp else None,
        'own_top2_pct': round(100 * own_top2 / len(sp), 1) if sp else None,
        'pct_spread_lt_15': round(100 * sum(1 for x in sp if x < 0.15) / len(sp), 1) if sp else None,
        'pct_spread_lt_30': round(100 * sum(1 for x in sp if x < 0.30) / len(sp), 1) if sp else None,
    }

# ---------------------------------------------------------------------------
# Matrice GROUPE x GROUPE (méthode b : majorité vs majorité)
#   congruence du "citoyen-groupe gA" (votes maj de gA, +2/-2) vs majorité de gB.
# ---------------------------------------------------------------------------
def group_majority_as_citizen(leg, grp):
    maj = MAJ[leg].get(grp, {})
    return {numero: (2 if d > 0 else -2) for numero, d in maj.items() if d is not None}

groupxgroup = {16: {}, 17: {}}
for leg in (16, 17):
    groups = MAIN_GROUPS[leg]
    for ga in groups:
        cv = group_majority_as_citizen(leg, ga)
        row = {}
        for gb in groups:
            cong, n, _, _ = congruence_vs_group_majority(cv, leg, gb)
            row[gb] = {'cong': round(cong, 4) if cong is not None else None, 'n': n}
        groupxgroup[leg][ga] = row

# ---------------------------------------------------------------------------
# ANALYSE (2) : congruence par GROUPE, deux méthodes
#   (a) moyenne des congruences paire-à-paire des membres : pour un citoyen "test",
#       on mesure congruence(citoyen, chaque membre) puis moyenne. Mais sans citoyen
#       externe, on évalue la COHÉSION : moyenne paire-à-paire INTRA-groupe ?
#   Interprétation correcte de la spec : "congruence d'un groupe" = à quel point le
#   groupe est un répondant cohérent. On compare :
#       (a) citoyen=position-majoritaire-du-groupe ; congruence = moyenne sur les
#           membres de congruence(maj_groupe_comme_citoyen, membre)
#       (b) citoyen=position-majoritaire ; congruence vs position-majoritaire (=1 trivialement)
#   => Ce que demande la spec : comparer (a) "moyenne des congruences paire-à-paire
#      des membres" vs (b) "position majoritaire puis congruence".
#   On l'instancie ainsi : pour un CITOYEN DE RÉFÉRENCE fixé (= la position majoritaire
#   du groupe lui-même, le "votant médian"), méthode (a) = moyenne_{m in groupe}
#   congruence(cit, m) ; méthode (b) = congruence(cit, maj_groupe). L'écart (a) vs (b)
#   mesure la cohésion interne / l'effet d'agrégation.
# ---------------------------------------------------------------------------
analysis2 = {16: {}, 17: {}}
for leg in (16, 17):
    for grp in MAIN_GROUPS[leg]:
        cit = group_majority_as_citizen(leg, grp)   # citoyen = position médiane du groupe
        if not cit:
            continue
        # (a) moyenne paire-à-paire sur les membres
        per_member = []
        for m in members_of[leg][grp]:
            cong, n, _, _ = congruence(cit, dir_dep[leg][m])
            if cong is not None and n >= 3:
                per_member.append(cong)
        method_a = statistics.mean(per_member) if per_member else None
        # (b) congruence vs position majoritaire du groupe
        maj_dir = {numero: d for numero, d in MAJ[leg].get(grp, {}).items() if d is not None}
        cong_b, n_b, _, _ = congruence(cit, maj_dir)
        analysis2[leg][grp] = {
            'method_a_mean_pairwise': round(method_a, 4) if method_a is not None else None,
            'method_b_majority': round(cong_b, 4) if cong_b is not None else None,
            'delta_b_minus_a': round(cong_b - method_a, 4) if (method_a is not None and cong_b is not None) else None,
            'n_members_scored': len(per_member),
            'n_laws_majority': n_b,
        }

# ---------------------------------------------------------------------------
# ANALYSE (3) : PROBLÈME DU DÉNOMINATEUR
#   Distribution du nb de lois comptées par paire (citoyen-réel = chaque député,
#   député = chaque autre député) ; et instabilité du classement top/bottom quand
#   le dénominateur est petit. On utilise un citoyen de référence concret par
#   législature (ex. la position majoritaire de RE / EPR), et on classe TOUS les
#   députés par congruence avec ce citoyen, en notant le dénominateur.
# ---------------------------------------------------------------------------
# (3a) distribution du nb de lois comptées par PAIRE de députés
#   pour échantillon raisonnable : toutes les paires (dep_i citoyen, dep_j) où dep_i
#   est pris comme citoyen ±2. On regarde n = nb lois communes votées (les deux ±).
import itertools
denom_dist = {16: [], 17: []}
for leg in (16, 17):
    deps = list(dep_dep := dir_dep[leg].keys())
    # échantillon : 200 députés max, toutes paires -> trop. On prend n lois communes
    # via comptage : pour chaque paire, |votes_i ∩ votes_j|. Échantillonnage aléatoire fixe.
    rng = random.Random(42)
    deps = [d for d in deps if len(dir_dep[leg][d]) >= 1]
    pairs = []
    if len(deps) > 1:
        # toutes les paires si raisonnable, sinon échantillon de 20000
        all_pairs = list(itertools.combinations(deps, 2))
        if len(all_pairs) > 30000:
            all_pairs = rng.sample(all_pairs, 30000)
        for i, j in all_pairs:
            common = set(dir_dep[leg][i]) & set(dir_dep[leg][j])
            denom_dist[leg].append(len(common))

analysis3_denom = {}
for leg in (16, 17):
    dd = denom_dist[leg]
    analysis3_denom[leg] = {
        'n_pairs_sampled': len(dd),
        'min': min(dd) if dd else None,
        'p10': round(statistics.quantiles(dd, n=10)[0], 1) if len(dd) >= 10 else None,
        'p25': round(statistics.quantiles(dd, n=4)[0], 1) if len(dd) >= 4 else None,
        'median': statistics.median(dd) if dd else None,
        'mean': round(statistics.mean(dd), 1) if dd else None,
        'p75': round(statistics.quantiles(dd, n=4)[2], 1) if len(dd) >= 4 else None,
        'p90': round(statistics.quantiles(dd, n=10)[8], 1) if len(dd) >= 10 else None,
        'max': max(dd) if dd else None,
        'pct_lt_5': round(100 * sum(1 for x in dd if x < 5) / len(dd), 1) if dd else None,
        'pct_lt_10': round(100 * sum(1 for x in dd if x < 10) / len(dd), 1) if dd else None,
        'total_laws_ref': len(law_meta[leg]),
    }

# (3b) instabilité du top/bottom : citoyen = majorité du grand groupe (RE/EPR).
#   On classe les députés par congruence ; on montre que sans seuil de dénominateur,
#   des "100% sur peu de lois" écrasent des scores robustes.
BIG = {16: 'RE', 17: 'EPR'}
analysis3_rank = {}
top_examples = {16: {}, 17: {}}
for leg in (16, 17):
    cit = group_majority_as_citizen(leg, BIG[leg])
    rows = []
    for ref in dir_dep[leg]:
        cong, n, _, _ = congruence(cit, dir_dep[leg][ref])
        if cong is None:
            continue
        rows.append({'ref': ref, 'name': name(ref), 'group': glabel(dep_group[leg][ref]),
                     'cong': cong, 'n': n})
    # tri SANS seuil (naïf, départage par -n => masque le pb au tout sommet)
    naive = sorted(rows, key=lambda r: (-r['cong'], -r['n']))
    # tri AVEC seuil n>=20 (robuste)
    robust = sorted([r for r in rows if r['n'] >= 20], key=lambda r: (-r['cong'], -r['n']))
    # tri RÉALISTE "leaderboard" : par congruence SEULE, départage aléatoire (pas de bonus n)
    rng_lb = random.Random(7)
    shuffled = rows[:]
    rng_lb.shuffle(shuffled)
    by_cong_only = sorted(shuffled, key=lambda r: -r['cong'])
    lb_top20 = by_cong_only[:20]
    lb_smalln_top20 = sum(1 for r in lb_top20 if r['n'] < 10)
    # exemple concret : un 100%-sur-≤2-lois qui surclasse un ~82%-sur-≥40-lois
    perf_small = sorted([r for r in rows if r['cong'] == 1.0 and r['n'] <= 2], key=lambda r: r['n'])
    robust_mid = sorted([r for r in rows if 0.80 <= r['cong'] < 0.90 and r['n'] >= 40], key=lambda r: -r['n'])
    example_pathology = None
    if perf_small and robust_mid:
        ps, rh = perf_small[0], robust_mid[0]
        idx = [r['ref'] for r in by_cong_only]
        example_pathology = {
            'perfect_smalln': {'name': ps['name'], 'group': ps['group'], 'cong': 1.0, 'n': ps['n'],
                               'rank_pure_cong': idx.index(ps['ref']) + 1},
            'robust_midcong': {'name': rh['name'], 'group': rh['group'], 'cong': round(rh['cong'], 4), 'n': rh['n'],
                               'rank_pure_cong': idx.index(rh['ref']) + 1},
        }
    # combien de "perfect 100%" avec petit n parasitent le top10 naïf ?
    naive_top10 = naive[:10]
    n_perfect_smalln = sum(1 for r in naive_top10 if r['cong'] == 1.0 and r['n'] < 10)
    # médiane du n dans le top10 naïf vs robuste
    analysis3_rank[leg] = {
        'citizen': BIG[leg],
        'n_deputes_scored': len(rows),
        'naive_top10_median_n': statistics.median([r['n'] for r in naive_top10]) if naive_top10 else None,
        'naive_top10_perfect_smalln': n_perfect_smalln,
        'robust_top10_median_n': statistics.median([r['n'] for r in robust[:10]]) if robust[:10] else None,
        'n_deputes_with_perfect_score': sum(1 for r in rows if r['cong'] == 1.0),
        'n_perfect_with_n_lt_10': sum(1 for r in rows if r['cong'] == 1.0 and r['n'] < 10),
        'n_perfect_with_n_ge_20': sum(1 for r in rows if r['cong'] == 1.0 and r['n'] >= 20),
        'leaderboard_pure_cong_top20_with_n_lt_10': lb_smalln_top20,
        'example_pathology': example_pathology,
    }
    top_examples[leg] = {
        'naive_top10': [{'name': r['name'], 'group': r['group'], 'cong': round(r['cong'], 4), 'n': r['n']} for r in naive_top10],
        'robust_top10': [{'name': r['name'], 'group': r['group'], 'cong': round(r['cong'], 4), 'n': r['n']} for r in robust[:10]],
        'naive_bottom10': [{'name': r['name'], 'group': r['group'], 'cong': round(r['cong'], 4), 'n': r['n']} for r in sorted(rows, key=lambda r: (r['cong'], -r['n']))[:10]],
    }

# ---------------------------------------------------------------------------
# ANALYSE (4) : ARCHÉTYPES SYNTHÉTIQUES (sanity check)
#   On crée des citoyens synthétiques et on mesure leur congruence avec chaque
#   groupe (méthode b, majorité). Domaine de lois = toutes les lois de réf de la
#   législature où le citoyen "vote" (toujours-pour/contre = ±2 sur toutes ;
#   suiveur-majorité = +2 si la majorité AN a adopté, -2 sinon ; aléatoire-graine).
# ---------------------------------------------------------------------------
def synthetic_citizens(leg):
    laws = list(law_meta[leg].keys())
    # sort adopté/rejeté de la loi entière (majorité AN)
    an_dir = {}
    for numero in laws:
        m = law_meta[leg][numero]
        an_dir[numero] = +1 if m['sort'] == 'adopté' else -1
    rng = random.Random(2026)
    cits = {
        'toujours_pour': {n: +2 for n in laws},
        'toujours_contre': {n: -2 for n in laws},
        'suiveur_majorite_AN': {n: (2 if an_dir[n] > 0 else -2) for n in laws},
        'opposant_majorite_AN': {n: (-2 if an_dir[n] > 0 else 2) for n in laws},
        'aleatoire_graine42': {n: rng.choice([-2, -1, 1, 2]) for n in laws},
    }
    return cits

analysis4 = {16: {}, 17: {}}
for leg in (16, 17):
    cits = synthetic_citizens(leg)
    for cname, cv in cits.items():
        row = {}
        for grp in MAIN_GROUPS[leg]:
            cong, n, _, _ = congruence_vs_group_majority(cv, leg, grp)
            row[grp] = {'cong': round(cong, 4) if cong is not None else None, 'n': n}
        # écart max-min sur groupes
        vals = [v['cong'] for v in row.values() if v['cong'] is not None]
        row['_spread'] = round(max(vals) - min(vals), 4) if vals else None
        analysis4[leg][cname] = row

# ---------------------------------------------------------------------------
# Trou AMO10 (députés partis)
# ---------------------------------------------------------------------------
gap = {}
for leg in (16, 17):
    gap[leg] = {
        'n_actors_in_refs': len(all_actors[leg]),
        'n_unknown_in_amo10': len(unknown_actors[leg]),
        'pct_unknown': round(100 * len(unknown_actors[leg]) / len(all_actors[leg]), 1) if all_actors[leg] else None,
    }

# ---------------------------------------------------------------------------
# Sauvegarde JSON machine
# ---------------------------------------------------------------------------
result = {
    'formula': 'congruence = sum(|v| for accords) / sum(|v| for lois comptees); '
               'citoyen v in {-2,-1,1,2}; depute pour=+1 contre=-1 (abst/nonvotant EXCLUS); '
               'accord si sign(v)==sign(dir); denominateur = n lois comptees gardé.',
    'corpus': {'n_lois': CORPUS['n_lois'], 'leg16': CORPUS['by_leg']['16'], 'leg17': CORPUS['by_leg']['17']},
    'group_labels_leg16_method': 'identification nominale sur scrutin 3966 (deputes re-elus)',
    'amo10_gap': gap,
    'analysis1_depute_as_citizen': analysis1,
    'analysis1_samples': {leg: sorted(spread_rows[leg], key=lambda r: r['spread'])[:8]
                          + sorted(spread_rows[leg], key=lambda r: -r['spread'])[:8] for leg in (16, 17)},
    'analysis2_group_two_methods': analysis2,
    'group_x_group_matrix': groupxgroup,
    'analysis3_denominator_dist': analysis3_denom,
    'analysis3_rank_instability': analysis3_rank,
    'analysis3_spurious_perfect_prob': {
        'note': 'P(votant reellement aligne a p=0.82 affiche 100% par hasard sur k lois)',
        'p_align': 0.82,
        'k3': round(0.82 ** 3, 3), 'k5': round(0.82 ** 5, 3), 'k10': round(0.82 ** 10, 3),
    },
    'analysis3_top_examples': top_examples,
    'analysis4_archetypes': analysis4,
}

with open(os.path.join(OUT, 'q7-simulation.json'), 'w') as fh:
    json.dump(result, fh, ensure_ascii=False, indent=1)

print("=== q7-simulation done ===")
print("corpus:", CORPUS['n_lois'], "lois; leg16", CORPUS['by_leg']['16'], "leg17", CORPUS['by_leg']['17'])
print("AMO10 gap:", gap)
print("\n-- Analysis 1 (depute-as-citizen spread) --")
for leg in (16, 17):
    a = analysis1[leg]
    print(f"  leg{leg}: n={a['n_deputes']} median_spread={a['spread_median']} "
          f"mean={a['spread_mean']} own_top1={a['own_top1_pct']}% own_top2={a['own_top2_pct']}% "
          f"pct<15pts={a['pct_spread_lt_15']}% pct<30pts={a['pct_spread_lt_30']}%")
print("\n-- Analysis 3 (denominator) --")
for leg in (16, 17):
    d = analysis3_denom[leg]
    print(f"  leg{leg}: pairs n_lois median={d['median']} mean={d['mean']} "
          f"p10={d['p10']} pct<5={d['pct_lt_5']}% pct<10={d['pct_lt_10']}% (sur {d['total_laws_ref']} lois)")
    r = analysis3_rank[leg]
    print(f"         perfect-100%={r['n_deputes_with_perfect_score']} "
          f"(dont n<10: {r['n_perfect_with_n_lt_10']}, n>=20: {r['n_perfect_with_n_ge_20']}); "
          f"naive top10 median_n={r['naive_top10_median_n']} vs robust={r['robust_top10_median_n']}")
print("\n-- Analysis 4 (archetypes) leg17 spreads --")
for cname, row in analysis4[17].items():
    print(f"  {cname}: spread={row['_spread']}")
print("\nWrote out/q7-simulation.json")
