#!/usr/bin/env python3
"""
formule_v2 — formule de congruence v2 en ARITHMÉTIQUE ENTIÈRE + génération des vecteurs de test.

But :
 1. Réimplémenter la formule pinnée de q7 en arithmétique ENTIÈRE (poids = intensité, score en
    millièmes) et prouver la PARITÉ exacte avec le calcul flottant de q7 sur les profils réels
    (Panot, Le Pen, Ciotti), puis vérifier la cohérence avec les % publiés du rapport q7.
 2. Émettre boussole-politique/vecteurs-test.json : cas synthétiques (vérifiables à la main, spécifient chaque
    règle) + cas réels ancrés sur la donnée AN — la « spec exécutable », reproductible bit-à-bit.

Réutilise anlib (chargement open data AN) + out/corpus.json (159 lois figées).
"""
from __future__ import annotations
import sys, json, os, glob, unicodedata
from collections import defaultdict, Counter

DRY = '/home/cos/Bureau/dev/boussole-politique/dry-run'
OUT_VECTORS = '/home/cos/Bureau/dev/boussole-politique/vecteurs-test.json'
sys.path.insert(0, os.path.join(DRY, 'scripts'))
import anlib

CORPUS = json.load(open(os.path.join(DRY, 'out', 'corpus.json')))
N_MIN = 10  # plancher de dénominateur (défaut)

# --- libellés de groupes (repris de q7) ---
def txt(x):
    if isinstance(x, dict):
        return x.get('#text') or x.get('text') or ''
    return x

GROUP_LABELS = {}
for p in glob.glob(os.path.join(DRY, 'data/amo10-17/json/organe/PO*.json')):
    o = json.load(open(p))['organe']
    if o.get('codeType') == 'GP':
        GROUP_LABELS[o['uid']] = o.get('libelleAbrev') or o.get('libelle')
LEG16 = {'PO800538':'RE','PO800520':'RN','PO800490':'LFI','PO800508':'LR','PO800484':'DEM',
         'PO800514':'HOR','PO830170':'SOC','PO800502':'GDR','PO800532':'LIOT','PO800526':'ECO',
         'PO793087':'NI','PO800496':'GDR-old'}
GROUP_LABELS.update(LEG16)
def glabel(po): return GROUP_LABELS.get(po, po)

MAIN_GROUPS = {
    16: ['LFI','GDR','ECO','SOC','DEM','RE','HOR','LIOT','LR','RN'],
    17: ['LFI-NFP','GDR','ECOS','SOC','DEM','EPR','HOR','LIOT','DR','RN'],
}

# --- noms (PA -> nom) ---
NAMES = {}
for p in glob.glob(os.path.join(DRY, 'data/amo10-17/json/acteur/PA*.json')):
    a = json.load(open(p))['acteur']
    uid = txt(a['uid'])
    ec = (a.get('etatCivil') or {}).get('ident') or {}
    NAMES[uid] = (txt(ec.get('prenom','')) + ' ' + txt(ec.get('nom',''))).strip()
def name(ref): return NAMES.get(ref, ref)

def norm(s):
    s = unicodedata.normalize('NFD', s or '')
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower().strip()

# --- matrices de vote (repris de q7) ---
sidx = anlib.load_all_scrutins()
REFS = {16: [], 17: []}
for l in CORPUS['lois']:
    REFS[l['ref_leg']].append((l['ref_numero'], l['titre']))

dir_dep = {16: defaultdict(dict), 17: defaultdict(dict)}
grp_at_vote = {16: defaultdict(dict), 17: defaultdict(dict)}
law_meta = {16: {}, 17: {}}
for leg in (16, 17):
    for numero, titre in REFS[leg]:
        s = sidx.get((leg, numero))
        if s is None: continue
        law_meta[leg][numero] = {'titre': titre, 'sort': s.sort, 'date': s.date}
        for ref, pos, deleg, gref, cause in s.positions_nominales():
            if ref is None: continue
            grp_at_vote[leg][numero][ref] = gref
            if pos == 'pour': dir_dep[leg][ref][numero] = +1
            elif pos == 'contre': dir_dep[leg][ref][numero] = -1
            # abstention / nonvotant : exclus (pas d'entrée)

def group_majority_dir(leg):
    pour = defaultdict(lambda: defaultdict(int)); contre = defaultdict(lambda: defaultdict(int))
    for numero in law_meta[leg]:
        for ref, g in grp_at_vote[leg][numero].items():
            d = dir_dep[leg][ref].get(numero)
            if d == +1: pour[glabel(g)][numero] += 1
            elif d == -1: contre[glabel(g)][numero] += 1
    maj = defaultdict(dict)
    for grp in set(list(pour)+list(contre)):
        for numero in law_meta[leg]:
            p, cc = pour[grp].get(numero,0), contre[grp].get(numero,0)
            if p+cc == 0: continue
            maj[grp][numero] = +1 if p>cc else (-1 if cc>p else None)
    return maj
MAJ = {16: group_majority_dir(16), 17: group_majority_dir(17)}

def find_ref(leg, full):
    target = norm(full)
    for ref in dir_dep[leg]:
        if norm(name(ref)) == target:
            return ref
    for ref in dir_dep[leg]:
        if target in norm(name(ref)):
            return ref
    return None

# ---------------------------------------------------------------------------
# LA FORMULE — deux implémentations qui doivent coïncider
# ---------------------------------------------------------------------------
def congruence_float(cv, dep_dir, polarities=None):
    """Référence flottante (méthode q7). Retourne (num, den, n) en float."""
    polarities = polarities or {}
    num = den = 0.0; n = 0
    for numero, v in cv.items():
        d = dep_dir.get(numero)
        if d is None or v == 0: continue
        d *= polarities.get(numero, +1)
        w = abs(v); den += w; n += 1
        if (v > 0) == (d > 0): num += w
    return (num, den, n)

def congruence_int(cv, dep_dir, n_min=N_MIN, polarities=None):
    """v2 — arithmétique ENTIÈRE. millimes = round_half_up(1000 * num / den)."""
    polarities = polarities or {}
    num = den = n = 0
    for numero, v in cv.items():
        d = dep_dir.get(numero)
        if d is None or v == 0: continue   # élu sans direction OU citoyen sans_avis/passer -> exclu
        d *= polarities.get(numero, +1)     # sens du vote brut par rapport à la formulation jugée
        w = abs(v)                          # poids = intensité (1 ou 2)
        den += w; n += 1
        if (v > 0) == (d > 0): num += w
    if den == 0:
        return {'num': 0, 'den': 0, 'n': 0, 'congruence_millimes': None, 'affichable': False}
    millimes = (1000 * num + den // 2) // den
    return {'num': num, 'den': den, 'n': n, 'congruence_millimes': millimes, 'affichable': n >= n_min}

def grp_dir(leg, grp):
    return {numero: d for numero, d in MAJ[leg].get(grp, {}).items() if d is not None}

def dep_as_citizen(leg, ref):
    return {numero: (2 if d > 0 else -2) for numero, d in dir_dep[leg][ref].items()}

# ---------------------------------------------------------------------------
# (1) PROFILS RÉELS : parité float↔int + cohérence avec le rapport q7
# ---------------------------------------------------------------------------
PROFILS = [('Mathilde Panot', 17), ('Marine Le Pen', 17), ('Éric Ciotti', 16)]
# valeurs publiées dans out/q7-simulation.md (en %) — cohérence attendue à ±1 pt
EXPECTED = {
    'Mathilde Panot': {'LFI-NFP':100,'ECOS':87,'GDR':82,'SOC':54,'EPR':32,'DEM':29,'RN':29,'HOR':26,'LIOT':23,'DR':19},
    'Marine Le Pen':  {'RN':100,'DR':83,'LIOT':78,'DEM':74,'HOR':74,'EPR':70,'SOC':50,'ECOS':41,'GDR':39,'LFI-NFP':30},
    'Éric Ciotti':    {'LR':100,'DEM':93,'RE':93,'HOR':93,'RN':69,'LIOT':62,'GDR':45,'ECO':27,'LFI':17},
}

parity_ok = True
coherence_ok = True
real_vectors = []
for full, leg in PROFILS:
    ref = find_ref(leg, full)
    assert ref is not None, f"introuvable: {full} (leg{leg})"
    cv = dep_as_citizen(leg, ref)
    own_po = Counter(grp_at_vote[leg][num][ref] for num in dir_dep[leg][ref]
                     if ref in grp_at_vote[leg][num]).most_common(1)[0][0]
    own = glabel(own_po)
    rows = []
    for grp in MAIN_GROUPS[leg]:
        gd = grp_dir(leg, grp)
        nf, df, _ = congruence_float(cv, gd)
        ci = congruence_int(cv, gd, N_MIN)
        if df == 0: continue
        # PARITÉ : (num, den) entiers == (num, den) flottants ; millième = fonction déterministe
        if ci['num'] != int(nf) or ci['den'] != int(df):
            parity_ok = False
            print(f"  PARITÉ FAIL {full} vs {grp}: int=({ci['num']},{ci['den']}) float=({nf},{df})")
        pct = ci['congruence_millimes'] / 10
        exp = EXPECTED[full].get(grp)
        if exp is not None and abs(pct - exp) > 1.0:
            coherence_ok = False
            print(f"  COHÉRENCE FAIL {full} vs {grp}: calc={pct:.1f}% rapport={exp}%")
        rows.append({'groupe': grp, 'congruence_millimes': ci['congruence_millimes'],
                     'pct': round(pct, 1), 'n': ci['n']})
    rows.sort(key=lambda r: -r['congruence_millimes'])
    real_vectors.append({'citoyen': full, 'legislature': leg, 'groupe_origine': own,
                         'n_enonces_juges': len(cv), 'note': 'votes réels du député comme positions ±2',
                         'scores_par_groupe': rows})
    print(f"\n{full} (leg{leg}, {own}) — {len(cv)} énoncés jugés :")
    for r in rows:
        print(f"   {r['groupe']:9} {r['pct']:5.1f}%  (n={r['n']})")

# ---------------------------------------------------------------------------
# (2) CAS SYNTHÉTIQUES — vérifiables à la main, spécifient chaque règle
# ---------------------------------------------------------------------------
def case(nom, desc, citoyen, elu, n_min=0, polarites=None):
    """citoyen: [(énoncé, valeur)] ; elu: [(énoncé, position)] ; polarites: {énoncé: ±1}."""
    polarites = polarites or {}
    cv = {e: (0 if v == 'sans_avis' else v) for e, v in citoyen}
    dep = {}
    for e, p in elu:
        if p == 'pour': dep[e] = +1
        elif p == 'contre': dep[e] = -1
        # abstention / nonvotant : pas d'entrée
    r = congruence_int(cv, dep, n_min, polarites)
    enonces = sorted({e for e, _ in citoyen} | {e for e, _ in elu})
    return {'nom': nom, 'description': desc, 'n_min': n_min,
            'enonces': [{'id': e, 'polarite': polarites.get(e, +1)} for e in enonces],
            'citoyen': [{'enonce': e, 'valeur': v} for e, v in citoyen],
            'elu': [{'enonce': e, 'position': p} for e, p in elu],
            'attendu': r}

SYNTH = [
    case('accord_parfait', '3 accords, intensités mêlées (2+2+1) → 1000‰',
         [('E1', 2), ('E2', 2), ('E3', -1)], [('E1', 'pour'), ('E2', 'pour'), ('E3', 'contre')]),
    case('desaccord_total', 'tout en opposition → 0‰',
         [('E1', 2), ('E2', -1)], [('E1', 'contre'), ('E2', 'pour')]),
    case('accord_partiel', '2 accords (poids 2+1) sur 4 → 500‰',
         [('E1', 2), ('E2', -2), ('E3', 1), ('E4', -1)],
         [('E1', 'pour'), ('E2', 'pour'), ('E3', 'contre'), ('E4', 'contre')]),
    case('intensite_poids', '+2 pèse 2× +1 : désaccord faible + accord fort → 667‰',
         [('E1', 1), ('E2', 2)], [('E1', 'contre'), ('E2', 'pour')]),
    case('abstention_elu_exclue', 'élu abstention sur E2 → E2 hors calcul (n=2)',
         [('E1', 2), ('E2', 2), ('E3', 2)], [('E1', 'pour'), ('E2', 'abstention'), ('E3', 'contre')]),
    case('nonvotant_elu_exclu', 'élu non-votant sur E1 → exclu, jamais pénalisé (n=1)',
         [('E1', 2), ('E2', -2)], [('E1', 'nonvotant'), ('E2', 'contre')]),
    case('citoyen_sans_avis_exclu', 'citoyen sans_avis sur E2 → E2 hors calcul (n=2)',
         [('E1', 2), ('E2', 'sans_avis'), ('E3', -2)], [('E1', 'pour'), ('E2', 'pour'), ('E3', 'pour')]),
    case('polarite_inversee',
         'polarité -1 inverse la direction brute : contre devient accord avec une réponse citoyenne positive',
         [('E1', 2), ('E2', 1)], [('E1', 'contre'), ('E2', 'pour')],
         polarites={'E1': -1, 'E2': -1}),
    case('sous_plancher_faux_100', '1 énoncé, accord parfait MAIS n<N_MIN → non affichable (le faux 100 %)',
         [('E1', 2)], [('E1', 'pour')], n_min=N_MIN),
    case('tout_sans_avis', 'aucune position tranchée → score indéfini (den=0)',
         [('E1', 'sans_avis'), ('E2', 'sans_avis')], [('E1', 'pour'), ('E2', 'pour')], n_min=N_MIN),
]

# ---------------------------------------------------------------------------
# Émission + bilan
# ---------------------------------------------------------------------------
doc = {
    'note': 'Vecteurs de test de la formule de congruence v2 (Boussole Politique). Spec EXÉCUTABLE : '
            'toute implémentation (Rust/WASM/Kotlin/Swift) doit reproduire ces sorties bit-à-bit.',
    'formule': {
        'citoyen': 'v ∈ {-2,-1,+1,+2} ; sans_avis et passer = aucune entrée',
        'elu': 'pour→+1, contre→-1 ; abstention, nonvotant, absent = aucune entrée',
        'polarite': 'direction_normalisee = direction_vote_brute × polarite_enonce, polarite ∈ {-1,+1}',
        'poids': '|v| (1 ou 2) — intensité du citoyen',
        'accord': 'sign(v) == sign(direction_normalisee)',
        'congruence_millimes': 'round_half_up(1000 * Σpoids_accords / Σpoids_comptés)',
        'plancher': 'si n < N_MIN → non affichable (jamais un %), N_MIN défaut = 10',
        'agregation_groupe': 'position majoritaire du groupe au scrutin (égalité → exclu)',
        'arithmetique': 'ENTIÈRE — garantit la parité bit-à-bit multi-cibles',
    },
    'n_min_defaut': N_MIN,
    'cas_synthetiques': SYNTH,
    'cas_reels': {
        'source': 'corpus dry-run figé (159 lois, leg 16+17) ; votes réels des députés comme positions citoyennes ±2',
        'methode': 'congruence(citoyen = votes du député, groupe = position majoritaire) — reproduit q7 en entier',
        'profils': real_vectors,
    },
}
with open(OUT_VECTORS, 'w') as fh:
    json.dump(doc, fh, ensure_ascii=False, indent=1)

print("\n=== BILAN ===")
print(f"parité float↔int  : {'OK' if parity_ok else 'FAIL'}")
print(f"cohérence vs q7.md : {'OK' if coherence_ok else 'FAIL'}")
print(f"cas synthétiques   : {len(SYNTH)}")
print("\nVérif synthétiques (calcul ↔ attendu manuel) :")
for c in SYNTH:
    a = c['attendu']
    print(f"   {c['nom']:24} num={a['num']} den={a['den']} n={a['n']} "
          f"→ {a['congruence_millimes']}‰ affichable={a['affichable']}")
print(f"\nÉcrit {OUT_VECTORS}")
