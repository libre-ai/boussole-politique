#!/usr/bin/env python3
"""
v-q2-check — VÉRIFICATION ADVERSE INDÉPENDANTE du chiffre-clé de q2-polarisation.

Méthode INDÉPENDANTE (ne réutilise PAS q2-polarisation.py) :
  1. Polarisation : parse corpus.json à la main, arithmétique maison, classes recomptées.
  2. Cross-check SOURCE : pour CHAQUE vote de référence, on relit le fichier scrutin BRUT
     (data/scrutins-*/json/) en parsant le JSON nous-mêmes (pas anlib.load_scrutins),
     et on vérifie que pour/contre/abst du corpus == decompte de la synthèse AN.
     => attrape les divergences corpus<->source (apostrophe, objet-vs-tableau, mauvais vote).
  3. Congruence : ré-agrégée depuis la ventilation nominative brute, boucle maison.
     On reproduit la règle "groupe majeur = présent (avec pour/contre) sur >=50% des votes"
     et la moyenne inter-groupes, mais on l'écrit indépendamment + on teste des variantes.
"""
import sys, json, glob, os, re, statistics, unicodedata
from collections import Counter, defaultdict

CORPUS = '/home/cos/Bureau/dev/boussole-politique/dry-run/out/corpus.json'
DATA = '/home/cos/Bureau/dev/boussole-politique/dry-run/data'
OUT_JSON = '/home/cos/Bureau/dev/boussole-politique/dry-run/out/v-q2-check.json'
SIEGES = 577
QU = 0.10   # quasi-unanime  : part minorité < 10%
DISC = 0.20  # discriminant  : part minorité >= 20%


def as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


# ---------------------------------------------------------------------------
# 1. Charger corpus + sélectionner le vote de référence indépendamment
# ---------------------------------------------------------------------------
corpus = json.load(open(CORPUS, encoding='utf-8'))
lois = corpus['lois']

# Index brut des fichiers scrutins : (leg, numero) -> chemin, parsé à la main.
scrutin_path = {}
for leg in (16, 17):
    for p in glob.glob(os.path.join(DATA, f'scrutins-{leg}', 'json', '*.json')):
        # on lit juste numero+leg depuis le contenu (les noms de fichiers varient)
        with open(p, encoding='utf-8') as fh:
            raw = json.load(fh)
        s = raw['scrutin']
        num = int(s['numero'])
        lg = int(s.get('legislature', leg))
        scrutin_path[(lg, num)] = p

raw_cache = {}
def load_raw(leg, num):
    k = (leg, num)
    if k not in raw_cache:
        with open(scrutin_path[k], encoding='utf-8') as fh:
            raw_cache[k] = json.load(fh)
    return raw_cache[k]


def ref_vote(loi):
    """Vote de référence = numero==ref_numero & leg==ref_leg (def. de l'analyse).
    On le sélectionne nous-mêmes depuis la liste votes du corpus."""
    cands = [v for v in loi['votes'] if v['numero'] == loi['ref_numero'] and v['leg'] == loi['ref_leg']]
    return cands[0] if cands else None


# ---------------------------------------------------------------------------
# 2. Recompute polarisation + cross-check contre la source brute
# ---------------------------------------------------------------------------
rows = []
source_mismatches = []
sel_anomalies = []
for loi in lois:
    v = ref_vote(loi)
    if v is None:
        sel_anomalies.append((loi['dossier_uid'], 'no_ref_vote', loi['ref_leg'], loi['ref_numero']))
        continue
    pour, contre, abst, nonvot = v['pour'], v['contre'], v['abst'], v['nonvotant']
    exprimes = pour + contre
    votants = pour + contre + abst
    minorite = min(pour, contre)
    majorite = max(pour, contre)
    part_min = minorite / exprimes if exprimes else 0.0
    marge = (majorite - minorite) / exprimes if exprimes else 1.0
    cls = 'quasi_unanime' if part_min < QU else ('discriminant' if part_min >= DISC else 'intermediaire')

    # --- cross-check contre le fichier scrutin BRUT ---
    raw = load_raw(loi['ref_leg'], loi['ref_numero'])
    s = raw['scrutin']
    syn = s.get('syntheseVote') or {}
    dec = syn.get('decompte') or {}
    src_pour = int(dec.get('pour') or 0)
    src_contre = int(dec.get('contre') or 0)
    src_abst = int(dec.get('abstentions') or 0)
    src_nonvot = int(dec.get('nonVotants') or 0)
    src_sort = (s.get('sort') or {}).get('code', '')
    src_type = (s.get('typeVote') or {}).get('codeTypeVote', '')
    src_ensemble = bool(re.search(r"l'ensemble\b", (((s.get('objet') or {}).get('libelle') or '').replace('’', "'")), re.I))
    if (src_pour, src_contre, src_abst) != (pour, contre, abst):
        source_mismatches.append({
            'uid': loi['dossier_uid'], 'leg': loi['ref_leg'], 'num': loi['ref_numero'],
            'corpus': [pour, contre, abst], 'source': [src_pour, src_contre, src_abst]})
    rows.append({
        'uid': loi['dossier_uid'], 'titre': loi['titre'], 'leg': loi['ref_leg'],
        'numero': loi['ref_numero'], 'type': v['type'], 'sort': v['sort'],
        'src_sort': src_sort, 'src_type': src_type, 'src_ensemble': src_ensemble,
        'pour': pour, 'contre': contre, 'abst': abst, 'nonvot': nonvot,
        'exprimes': exprimes, 'votants': votants,
        'part_minorite': part_min, 'marge': marge, 'classe': cls,
        'is_ratification': loi['is_ratification'],
        'part_votants': votants / SIEGES, 'part_exprimes': exprimes / SIEGES,
    })


def classes_count(subset):
    c = Counter(r['classe'] for r in subset)
    n = len(subset)
    return {
        'n': n,
        'quasi_unanime': c['quasi_unanime'],
        'intermediaire': c['intermediaire'],
        'discriminant': c['discriminant'],
        'pct_quasi_unanime': round(100 * c['quasi_unanime'] / n, 1) if n else 0,
        'pct_intermediaire': round(100 * c['intermediaire'] / n, 1) if n else 0,
        'pct_discriminant': round(100 * c['discriminant'] / n, 1) if n else 0,
    }


glob_rows = rows
leg16 = [r for r in rows if r['leg'] == 16]
leg17 = [r for r in rows if r['leg'] == 17]
ratif = [r for r in rows if r['is_ratification']]
sans_ratif = [r for r in rows if not r['is_ratification']]

pol = {
    'global': classes_count(glob_rows),
    'leg16': classes_count(leg16),
    'leg17': classes_count(leg17),
    'ratifications': classes_count(ratif),
    'global_sans_ratif': classes_count(sans_ratif),
}

medians = {}
for label, sub in (('global', glob_rows), ('leg16', leg16), ('leg17', leg17)):
    medians[label] = {
        'part_minorite_median': round(statistics.median([r['part_minorite'] for r in sub]), 4),
        'marge_median': round(statistics.median([r['marge'] for r in sub]), 4),
        'votants_median': statistics.median([r['votants'] for r in sub]),
        'exprimes_median': statistics.median([r['exprimes'] for r in sub]),
        'part_votants_median': round(statistics.median([r['part_votants'] for r in sub]), 4),
        'part_exprimes_median': round(statistics.median([r['part_exprimes'] for r in sub]), 4),
    }

# sorts: combien adoptés / rejetés ?
sorts = Counter(r['sort'] for r in rows)
src_sorts = Counter(r['src_sort'] for r in rows)


# ---------------------------------------------------------------------------
# 3. Congruence INDÉPENDANTE depuis la ventilation nominative brute
# ---------------------------------------------------------------------------
def group_majpos_from_raw(raw):
    """Retourne {gref: 'pour'|'contre'|None} en lisant decompteNominatif brut.
    None si le groupe n'a ni pour ni contre."""
    vv = (raw['scrutin'].get('ventilationVotes') or {})
    organe = vv.get('organe') or {}
    groupes = (organe.get('groupes') or {}).get('groupe')
    out = {}
    for g in as_list(groupes):
        gref = g.get('organeRef')
        dn = (g.get('vote') or {}).get('decompteNominatif') or {}
        def cnt(key):
            b = dn.get(key)
            if not b:
                return 0
            votants = b.get('votant') if isinstance(b, dict) else b
            return len([x for x in as_list(votants) if isinstance(x, dict)])
        p = cnt('pours')
        co = cnt('contres')
        if p == 0 and co == 0:
            out[gref] = None
        else:
            out[gref] = 'pour' if p >= co else 'contre'
    return out


def congruence_block(subset):
    """Réplique indépendante : score par groupe = part de votes où la position
    majoritaire du groupe == sens attendu (adopté->pour, rejeté->contre).
    Groupe majeur = présent (avec pour/contre défini) sur >=50% des votes du sous-ensemble."""
    n = len(subset)
    if n == 0:
        return {}
    present = Counter()      # nb de votes où le groupe a un pour/contre (défini)
    seen = Counter()         # nb de votes où le groupe apparaît (même indéfini)
    congru = Counter()       # nb de votes congruents
    for r in subset:
        raw = load_raw(r['leg'], r['numero'])
        sens = 'pour' if r['sort'] == 'adopté' else 'contre'
        majpos = group_majpos_from_raw(raw)
        for gref, mp in majpos.items():
            seen[gref] += 1
            if mp is not None:
                present[gref] += 1
                if mp == sens:
                    congru[gref] += 1
    majeurs = {g for g in seen if seen[g] >= 0.5 * n and present[g] > 0}
    scores = {g: congru[g] / present[g] for g in majeurs}
    return scores


def summarize(scores):
    vals = list(scores.values())
    if not vals:
        return {}
    return {
        'n_groupes_majeurs': len(vals),
        'score_min': round(min(vals), 4),
        'score_max': round(max(vals), 4),
        'score_mean': round(statistics.mean(vals), 4),
        'spread': round(max(vals) - min(vals), 4),
        'above_80': sum(1 for v in vals if v > 0.80),
        'above_60': sum(1 for v in vals if v > 0.60),
        'scores': {g: round(v, 4) for g, v in sorted(scores.items(), key=lambda kv: -kv[1])},
    }


qu_global = [r for r in glob_rows if r['classe'] == 'quasi_unanime']
disc_global = [r for r in glob_rows if r['classe'] == 'discriminant']
qu_l16 = [r for r in leg16 if r['classe'] == 'quasi_unanime']
disc_l16 = [r for r in leg16 if r['classe'] == 'discriminant']
qu_l17 = [r for r in leg17 if r['classe'] == 'quasi_unanime']
disc_l17 = [r for r in leg17 if r['classe'] == 'discriminant']

congru = {
    'tous_global': summarize(congruence_block(glob_rows)),
    'tous_leg16': summarize(congruence_block(leg16)),
    'tous_leg17': summarize(congruence_block(leg17)),
    'quasi_unanime_global': summarize(congruence_block(qu_global)),
    'discriminant_global': summarize(congruence_block(disc_global)),
    'quasi_unanime_leg16': summarize(congruence_block(qu_l16)),
    'discriminant_leg16': summarize(congruence_block(disc_l16)),
    'quasi_unanime_leg17': summarize(congruence_block(qu_l17)),
    'discriminant_leg17': summarize(congruence_block(disc_l17)),
}

# ---------------------------------------------------------------------------
# Variante de robustesse : moyenne PONDÉRÉE par taille de groupe au lieu de
# moyenne simple inter-groupes (test de sensibilité du 0.82).
# ---------------------------------------------------------------------------
def congruence_weighted(subset):
    """Score agrégé pondéré : somme(congruent) / somme(défini) sur tous groupes majeurs.
    (pondère par le nb d'occurrences ~ taille/présence du groupe)."""
    n = len(subset)
    present = Counter(); seen = Counter(); congru = Counter()
    for r in subset:
        raw = load_raw(r['leg'], r['numero'])
        sens = 'pour' if r['sort'] == 'adopté' else 'contre'
        for gref, mp in group_majpos_from_raw(raw).items():
            seen[gref] += 1
            if mp is not None:
                present[gref] += 1
                if mp == sens:
                    congru[gref] += 1
    majeurs = {g for g in seen if seen[g] >= 0.5 * n and present[g] > 0}
    num = sum(congru[g] for g in majeurs)
    den = sum(present[g] for g in majeurs)
    return round(num / den, 4) if den else None


congru_weighted = {
    'tous_global': congruence_weighted(glob_rows),
    'tous_leg16': congruence_weighted(leg16),
    'tous_leg17': congruence_weighted(leg17),
}

# Combien de groupes "majeurs" dans tous_global, et lesquels (leg16 vs leg17 codes) ?
present_all = Counter(); seen_all = Counter()
for r in glob_rows:
    raw = load_raw(r['leg'], r['numero'])
    for gref, mp in group_majpos_from_raw(raw).items():
        seen_all[gref] += 1
        if mp is not None:
            present_all[gref] += 1
groupes_global_diag = {g: {'seen': seen_all[g], 'present': present_all[g], 'pct_seen': round(100*seen_all[g]/len(glob_rows),1)}
                       for g in sorted(seen_all, key=lambda x: -seen_all[x])}

result = {
    'n_lois': len(lois),
    'n_rows': len(rows),
    'by_leg': {'16': len(leg16), '17': len(leg17)},
    'polarisation': pol,
    'medians': medians,
    'sorts_corpus': dict(sorts),
    'sorts_source': dict(src_sorts),
    'n_ratifications': len(ratif),
    'congruence_simple_mean': congru,
    'congruence_weighted_mean': congru_weighted,
    'groupes_global_presence': groupes_global_diag,
    'source_mismatches': source_mismatches,
    'n_source_mismatches': len(source_mismatches),
    'selection_anomalies': sel_anomalies,
    'all_ref_are_ensemble': all(r['src_ensemble'] for r in rows),
    'n_ref_not_ensemble': sum(1 for r in rows if not r['src_ensemble']),
    'corpus_sort_eq_source_sort': sum(1 for r in rows if r['sort'] == r['src_sort']),
}

json.dump(result, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ---- Console summary ----
print('=== POLARISATION (indépendant, corpus.json) ===')
for k, v in pol.items():
    print(f"  {k}: n={v['n']} QU={v['quasi_unanime']}({v['pct_quasi_unanime']}%) "
          f"INT={v['intermediaire']}({v['pct_intermediaire']}%) DISC={v['discriminant']}({v['pct_discriminant']}%)")
print('\n=== MÉDIANES ===')
for k, v in medians.items():
    print(f"  {k}: part_min_med={v['part_minorite_median']} marge_med={v['marge_median']} "
          f"votants_med={v['votants_median']} exp_med={v['exprimes_median']} part_vot_med={v['part_votants_median']}")
print('\n=== SORTS ===')
print('  corpus:', dict(sorts), ' source:', dict(src_sorts))
print('  n_ratifications:', len(ratif))
print('\n=== CONGRUENCE (moyenne simple inter-groupes, indépendant) ===')
for k, v in congru.items():
    if v:
        print(f"  {k}: n_grp={v['n_groupes_majeurs']} mean={v['score_mean']} min={v['score_min']} "
              f"max={v['score_max']} spread={v['spread']} >80%={v['above_80']} >60%={v['above_60']}")
print('\n=== CONGRUENCE pondérée (robustesse) ===')
for k, v in congru_weighted.items():
    print(f"  {k}: weighted_mean={v}")
print('\n=== tous_global scores par groupe ===')
for g, v in congru['tous_global']['scores'].items():
    print(f"  {g}: {v}")
print('\n=== DIAGNOSTIC présence groupes (global, 159 votes) — seuil majeur=79.5 ===')
for g, d in list(groupes_global_diag.items())[:20]:
    flag = 'MAJEUR' if d['seen'] >= 0.5*len(glob_rows) and present_all[g] > 0 else ''
    print(f"  {g}: vu={d['seen']} ({d['pct_seen']}%) defini={d['present']} {flag}")
print('\n=== INTÉGRITÉ SOURCE ===')
print(f"  mismatches corpus<->source brut: {len(source_mismatches)}")
for m in source_mismatches[:10]:
    print('   ', m)
print(f"  anomalies sélection vote réf: {len(sel_anomalies)}")
print(f"  tous votes réf sont 'l'ensemble' (source): {result['all_ref_are_ensemble']} (non-ensemble={result['n_ref_not_ensemble']})")
print(f"  corpus.sort == source.sort sur {result['corpus_sort_eq_source_sort']}/{len(rows)}")
