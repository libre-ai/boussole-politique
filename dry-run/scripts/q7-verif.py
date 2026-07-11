#!/usr/bin/env python3
"""
q7-verif — VÉRIFICATION ADVERSE INDÉPENDANTE du chiffre-clé de q7-simulation.

Chiffre-clé contesté :
  "écart de congruence médian de 66,7 points (0,667) entre meilleur et pire groupe
   pour un député-comme-citoyen (leg 16 ET leg 17), avec 0,0 % des députés sous le
   seuil d'échec de 15 pts."

MÉTHODE INDÉPENDANTE :
  - On NE réutilise PAS q7-simulation.py.
  - On NE passe PAS par anlib.positions_nominales(). On lit les fichiers scrutins
    JSON BRUTS directement (data/scrutins-16|17/json/VTANR5L*V*.json) et on re-parse
    ventilationVotes.organe.groupes.groupe[] nous-mêmes.
  - Seule entrée figée consommée : la LISTE des votes de référence (leg, ref_numero)
    issue de out/corpus.json (input figé autorisé).
  - Mapping label de groupe : leg17 depuis organe/PO*.json (codeType GP) ; leg16 depuis
    le mapping documenté. On teste aussi la sensibilité au mapping (labels bruts PO).

FORMULE (relue dans le rapport, ré-implémentée à neuf) :
  - député au vote de réf : pour->+1, contre->-1 ; abstention/nonvotant EXCLUS.
  - citoyen = chaque député, ses propres votes : +1->+2, -1->-2.
  - direction d'un groupe sur une loi = majorité pour/contre des votants du groupe
    (égalité -> exclu).
  - congruence(citoyen, groupe) = sum(|v| accords) / sum(|v| comptés), v=±2 => poids 2.
    accord si sign(v)==sign(dir_groupe). Lois comptées = celles où le groupe a une
    direction ET le citoyen a voté. min 5 lois communes par groupe.
  - spread = max_g congruence - min_g congruence sur les groupes ayant n>=5,
    si >=2 groupes qualifient.
  - chiffre = MÉDIANE des spreads sur les députés.
"""
from __future__ import annotations
from workspace_paths import DATA_DIR, DRY_RUN_DIR, OUT_DIR, REPO_ROOT, SCRIPTS_DIR
import json, glob, os, statistics, re
from collections import defaultdict, Counter

OUT = str(OUT_DIR)
DATA = str(DATA_DIR)

def as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]

def txt(x):
    if isinstance(x, dict):
        return x.get('#text') or x.get('text') or ''
    return x

# ---------------------------------------------------------------------------
# 1) Entrée figée : liste des votes de référence (leg, ref_numero) du corpus
# ---------------------------------------------------------------------------
CORPUS = json.load(open(os.path.join(OUT, 'corpus.json')))
REF_NUMEROS = {16: {}, 17: {}}   # numero -> titre
for l in CORPUS['lois']:
    REF_NUMEROS[l['ref_leg']][l['ref_numero']] = l['titre']
print("corpus refs:", {leg: len(v) for leg, v in REF_NUMEROS.items()})

# ---------------------------------------------------------------------------
# 2) Mapping label de groupe
# ---------------------------------------------------------------------------
GROUP_LABELS = {}
for p in glob.glob(os.path.join(DATA, 'amo10-17/json/organe/PO*.json')):
    o = json.load(open(p))['organe']
    if o.get('codeType') == 'GP':
        GROUP_LABELS[o['uid']] = o.get('libelleAbrev') or o.get('libelle')

LEG16 = {
    'PO800538': 'RE', 'PO800520': 'RN', 'PO800490': 'LFI', 'PO800508': 'LR',
    'PO800484': 'DEM', 'PO800514': 'HOR', 'PO830170': 'SOC', 'PO800502': 'GDR',
    'PO800532': 'LIOT', 'PO800526': 'ECO', 'PO793087': 'NI', 'PO800496': 'GDR-old',
}
GROUP_LABELS.update(LEG16)

def glabel(po):
    return GROUP_LABELS.get(po, po)

MAIN_GROUPS = {
    16: ['LFI', 'GDR', 'ECO', 'SOC', 'DEM', 'RE', 'HOR', 'LIOT', 'LR', 'RN'],
    17: ['LFI-NFP', 'GDR', 'ECOS', 'SOC', 'DEM', 'EPR', 'HOR', 'LIOT', 'DR', 'RN'],
}

# noms (pour exemples)
NAMES = {}
for p in glob.glob(os.path.join(DATA, 'amo10-17/json/acteur/PA*.json')):
    a = json.load(open(p))['acteur']
    uid = txt(a['uid'])
    ec = (a.get('etatCivil') or {}).get('ident') or {}
    NAMES[uid] = (txt(ec.get('prenom', '')) + ' ' + txt(ec.get('nom', ''))).strip()
def name(ref):
    return NAMES.get(ref, ref)

# ---------------------------------------------------------------------------
# 3) Lecture BRUTE des scrutins de référence -> directions par député + groupe-au-vote
#    On scanne tous les fichiers, on ne garde que ceux dont numero est un ref de la leg.
# ---------------------------------------------------------------------------
# dir_dep[leg][acteurRef][numero] = +1/-1
# grp_at_vote[leg][numero][acteurRef] = PO
# grp_counter[leg][acteurRef] = Counter(PO)
dir_dep = {16: defaultdict(dict), 17: defaultdict(dict)}
grp_at_vote = {16: defaultdict(dict), 17: defaultdict(dict)}
grp_counter = {16: defaultdict(Counter), 17: defaultdict(Counter)}
all_actors = {16: set(), 17: set()}
unknown_actors = {16: set(), 17: set()}
found_refs = {16: set(), 17: set()}
# double-compte sentinel : un acteur qui apparait 2x dans le meme scrutin
dup_in_scrutin = {16: 0, 17: 0}

for leg in (16, 17):
    for path in glob.glob(os.path.join(DATA, f'scrutins-{leg}/json/VTANR5L{leg}V*.json')):
        s = json.load(open(path))['scrutin']
        numero = int(s['numero'])
        if numero not in REF_NUMEROS[leg]:
            continue
        # sécurité : la législature du fichier doit matcher
        if int(s.get('legislature', leg)) != leg:
            continue
        found_refs[leg].add(numero)
        seen_this = set()
        vv = s.get('ventilationVotes') or {}
        organe = vv.get('organe') or {}
        groupes = (organe.get('groupes') or {}).get('groupe')
        for g in as_list(groupes):
            gref = g.get('organeRef')
            dn = (g.get('vote') or {}).get('decompteNominatif') or {}
            for key, sign in (('pours', +1), ('contres', -1),
                              ('abstentions', 0), ('nonVotants', 0)):
                bucket = dn.get(key)
                if not bucket:
                    continue
                votants = bucket.get('votant') if isinstance(bucket, dict) else bucket
                for v in as_list(votants):
                    if not isinstance(v, dict):
                        continue
                    ref = v.get('acteurRef')
                    if ref is None:
                        continue
                    if ref in seen_this:
                        dup_in_scrutin[leg] += 1
                    seen_this.add(ref)
                    all_actors[leg].add(ref)
                    if ref not in NAMES:
                        unknown_actors[leg].add(ref)
                    grp_at_vote[leg][numero][ref] = gref
                    grp_counter[leg][ref][gref] += 1
                    if sign == +1:
                        dir_dep[leg][ref][numero] = +1
                    elif sign == -1:
                        dir_dep[leg][ref][numero] = -1
                    # abst/nonvotant exclus

print("found refs:", {leg: len(found_refs[leg]) for leg in (16, 17)},
      "expected:", {leg: len(REF_NUMEROS[leg]) for leg in (16, 17)})
missing = {leg: set(REF_NUMEROS[leg]) - found_refs[leg] for leg in (16, 17)}
print("missing ref scrutins:", {leg: sorted(missing[leg]) for leg in (16, 17)})
print("duplicate actor-in-scrutin events:", dup_in_scrutin)

# groupe dominant du député
dep_group = {16: {}, 17: {}}
for leg in (16, 17):
    for ref, c in grp_counter[leg].items():
        dep_group[leg][ref] = c.most_common(1)[0][0]

# ---------------------------------------------------------------------------
# 4) Direction majoritaire par groupe (label) et par loi
# ---------------------------------------------------------------------------
def group_majority_dir(leg):
    pour = defaultdict(lambda: defaultdict(int))
    contre = defaultdict(lambda: defaultdict(int))
    for numero in REF_NUMEROS[leg]:
        if numero not in found_refs[leg]:
            continue
        for ref, po in grp_at_vote[leg][numero].items():
            d = dir_dep[leg][ref].get(numero)
            lab = glabel(po)
            if d == +1:
                pour[lab][numero] += 1
            elif d == -1:
                contre[lab][numero] += 1
    maj = defaultdict(dict)
    for lab in set(list(pour) + list(contre)):
        for numero in REF_NUMEROS[leg]:
            p = pour[lab].get(numero, 0)
            cc = contre[lab].get(numero, 0)
            if p + cc == 0:
                continue
            if p > cc:
                maj[lab][numero] = +1
            elif cc > p:
                maj[lab][numero] = -1
            else:
                maj[lab][numero] = None
    return maj

MAJ = {16: group_majority_dir(16), 17: group_majority_dir(17)}

# ---------------------------------------------------------------------------
# 5) Congruence + spread "député-comme-citoyen"
# ---------------------------------------------------------------------------
def congruence(citizen_votes, dep_dir):
    num = den = 0.0
    n = 0
    for numero, v in citizen_votes.items():
        d = dep_dir.get(numero)
        if d is None:
            continue
        w = abs(v)
        den += w
        n += 1
        if (v > 0) == (d > 0):
            num += w
    if den == 0:
        return (None, 0)
    return (num / den, n)

def compute_spreads(leg, main_groups, group_majority, min_n=5):
    maj_clean = {g: {num: d for num, d in group_majority.get(g, {}).items() if d is not None}
                 for g in main_groups}
    rows = []
    for ref in dep_group[leg]:
        cv = {numero: (2 if d > 0 else -2) for numero, d in dir_dep[leg][ref].items()}
        if not cv:
            continue
        own = glabel(dep_group[leg][ref])
        vals = {}
        ns = {}
        for g in main_groups:
            cong, n = congruence(cv, maj_clean[g])
            if cong is not None and n >= min_n:
                vals[g] = cong
                ns[g] = n
        if len(vals) < 2:
            continue
        gmax = max(vals, key=vals.get)
        gmin = min(vals, key=vals.get)
        spread = vals[gmax] - vals[gmin]
        own_rank = None
        if own in vals:
            ranked = sorted(vals, key=vals.get, reverse=True)
            own_rank = ranked.index(own) + 1
        rows.append({
            'ref': ref, 'name': name(ref), 'own': own, 'spread': spread,
            'best_group': gmax, 'best': vals[gmax], 'worst_group': gmin, 'worst': vals[gmin],
            'own_score': vals.get(own), 'own_rank': own_rank, 'n_groups': len(vals),
            'vals': {g: round(vals[g], 4) for g in vals},
        })
    return rows

def summarize(rows):
    sp = sorted(r['spread'] for r in rows)
    n = len(sp)
    if n == 0:
        return {}
    own_top1 = sum(1 for r in rows if r['own_rank'] == 1)
    own_top2 = sum(1 for r in rows if r['own_rank'] and r['own_rank'] <= 2)
    return {
        'n_deputes': n,
        'spread_min': round(min(sp), 4),
        'spread_p10': round(statistics.quantiles(sp, n=10)[0], 4) if n >= 10 else None,
        'spread_p25': round(statistics.quantiles(sp, n=4)[0], 4) if n >= 4 else None,
        'spread_median': round(statistics.median(sp), 4),
        'spread_mean': round(statistics.mean(sp), 4),
        'spread_p75': round(statistics.quantiles(sp, n=4)[2], 4) if n >= 4 else None,
        'spread_p90': round(statistics.quantiles(sp, n=10)[8], 4) if n >= 10 else None,
        'spread_max': round(max(sp), 4),
        'own_top1': own_top1, 'own_top1_pct': round(100 * own_top1 / n, 1),
        'own_top2': own_top2, 'own_top2_pct': round(100 * own_top2 / n, 1),
        'pct_spread_lt_15': round(100 * sum(1 for x in sp if x < 0.15) / n, 1),
        'pct_spread_lt_30': round(100 * sum(1 for x in sp if x < 0.30) / n, 1),
    }

result = {'corpus_refs': {leg: len(REF_NUMEROS[leg]) for leg in (16, 17)},
          'found_refs': {leg: len(found_refs[leg]) for leg in (16, 17)},
          'missing_refs': {leg: sorted(missing[leg]) for leg in (16, 17)},
          'dup_actor_in_scrutin': dup_in_scrutin,
          'amo10_gap': {leg: {'n_actors': len(all_actors[leg]),
                              'n_unknown': len(unknown_actors[leg]),
                              'pct_unknown': round(100*len(unknown_actors[leg])/len(all_actors[leg]),1)}
                        for leg in (16,17)},
          'main': {}, 'sensitivity': {}}

print("\n=== ANALYSE 1 RECALCULÉE (mapping documenté) ===")
ROWS = {}
for leg in (16, 17):
    rows = compute_spreads(leg, MAIN_GROUPS[leg], MAJ[leg])
    ROWS[leg] = rows
    summ = summarize(rows)
    result['main'][leg] = summ
    print(f"leg{leg}: n={summ['n_deputes']} median={summ['spread_median']} "
          f"mean={summ['spread_mean']} min={summ['spread_min']} max={summ['spread_max']} "
          f"own_top1={summ['own_top1_pct']}% own_top2={summ['own_top2_pct']}% "
          f"<15pts={summ['pct_spread_lt_15']}% <30pts={summ['pct_spread_lt_30']}%")

# ---------------------------------------------------------------------------
# 6) SENSIBILITÉ : et si on prend tous les PO bruts comme groupes (pas de mapping) ?
#    Cela teste si le mapping leg16 (custom) influence le chiffre.
# ---------------------------------------------------------------------------
print("\n=== SENSIBILITÉ : groupes = top-10 PO bruts par effectif (sans mapping label) ===")
for leg in (16, 17):
    # top 10 PO par nombre de membres dominants
    po_counts = Counter(dep_group[leg].values())
    top10_po = [po for po, _ in po_counts.most_common(10)]
    # construire majorité par PO brut
    pour = defaultdict(lambda: defaultdict(int)); contre = defaultdict(lambda: defaultdict(int))
    for numero in found_refs[leg]:
        for ref, po in grp_at_vote[leg][numero].items():
            d = dir_dep[leg][ref].get(numero)
            if d == +1: pour[po][numero] += 1
            elif d == -1: contre[po][numero] += 1
    maj_po = defaultdict(dict)
    for po in set(list(pour)+list(contre)):
        for numero in found_refs[leg]:
            p=pour[po].get(numero,0); cc=contre[po].get(numero,0)
            if p+cc==0: continue
            maj_po[po][numero] = +1 if p>cc else (-1 if cc>p else None)
    # spread sur top10 PO bruts (glabel identity -> on remplace dep_group label par PO lui-meme)
    maj_clean = {po: {num:d for num,d in maj_po.get(po,{}).items() if d is not None} for po in top10_po}
    sp = []
    o1 = 0; o2 = 0; tot = 0
    for ref in dep_group[leg]:
        cv = {numero:(2 if d>0 else -2) for numero,d in dir_dep[leg][ref].items()}
        if not cv: continue
        own_po = dep_group[leg][ref]
        vals = {}
        for po in top10_po:
            cong,n = congruence(cv, maj_clean[po])
            if cong is not None and n>=5: vals[po]=cong
        if len(vals)<2: continue
        tot += 1
        sp.append(max(vals.values())-min(vals.values()))
        if own_po in vals:
            ranked = sorted(vals, key=vals.get, reverse=True)
            r = ranked.index(own_po)+1
            if r==1: o1+=1
            if r<=2: o2+=1
    med = round(statistics.median(sp),4) if sp else None
    result['sensitivity'][leg] = {'n':tot,'median':med,'mean':round(statistics.mean(sp),4) if sp else None,
                                  'lt15_pct': round(100*sum(1 for x in sp if x<0.15)/len(sp),1) if sp else None,
                                  'own_top1_pct': round(100*o1/tot,1) if tot else None,
                                  'own_top2_pct': round(100*o2/tot,1) if tot else None}
    print(f"leg{leg}: n={tot} median={med} <15pts={result['sensitivity'][leg]['lt15_pct']}% "
          f"own_top1={result['sensitivity'][leg]['own_top1_pct']}% (top10 PO: {top10_po})")

# ---------------------------------------------------------------------------
# 7) Exemples nominaux pour recoupement (Panot, Le Pen, Ciotti leg16, Vallaud)
# ---------------------------------------------------------------------------
def find_by_name(leg, frag):
    frag = frag.lower()
    for ref in dep_group[leg]:
        if frag in name(ref).lower():
            return ref
    return None

examples = {}
for leg, frag in [(17,'panot'),(17,'le pen'),(17,'vallaud'),(16,'ciotti')]:
    ref = find_by_name(leg, frag)
    if ref:
        row = next((r for r in ROWS[leg] if r['ref']==ref), None)
        if row:
            examples[f'{frag}_leg{leg}'] = {'name':row['name'],'own':row['own'],
                'spread':round(row['spread'],4),'best':(row['best_group'],round(row['best'],4)),
                'worst':(row['worst_group'],round(row['worst'],4)),'vals':row['vals']}
result['examples'] = examples
print("\n=== EXEMPLES NOMINAUX ===")
for k,v in examples.items():
    print(f"{k}: {v['name']} ({v['own']}) spread={v['spread']} best={v['best']} worst={v['worst']}")
    print("   ", v['vals'])

# ---------------------------------------------------------------------------
# 8) Comparaison directe au headline + chargement du json de l'analyse
# ---------------------------------------------------------------------------
ANALYSIS = json.load(open(os.path.join(OUT, 'q7-simulation.json')))
a1 = ANALYSIS['analysis1_depute_as_citizen']
print("\n=== COMPARAISON AU HEADLINE ===")
for leg in (16,17):
    mine = result['main'][leg]
    theirs = a1[str(leg)]
    print(f"leg{leg} median: moi={mine['spread_median']} vs eux={theirs['spread_median']} "
          f"| n: moi={mine['n_deputes']} vs eux={theirs['n_deputes']} "
          f"| <15pts: moi={mine['pct_spread_lt_15']} vs eux={theirs['pct_spread_lt_15']} "
          f"| own_top1: moi={mine['own_top1_pct']} vs eux={theirs['own_top1_pct']} "
          f"| own_top2: moi={mine['own_top2_pct']} vs eux={theirs['own_top2_pct']}")

with open(os.path.join(OUT, 'q7-verif.json'), 'w') as fh:
    json.dump(result, fh, ensure_ascii=False, indent=1)
print("\nWrote", os.path.join(OUT, 'q7-verif.json'))
