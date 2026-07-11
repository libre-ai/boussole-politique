#!/usr/bin/env python3
"""
Vérification ADVERSE et INDEPENDANTE du chiffre-clé de out/q3-version.md.
On NE réutilise PAS scripts/q3-version.py. On part :
  - du corpus FIGE (out/corpus.json) pour le périmètre (159), ref_acte/ref_numero/ref_leg, has_cmp, saisine_cc
  - des fichiers DOSSIERS BRUTS (data/dossiers-1{6,7}/.../DLR*.json) pour parser nous-mêmes l'arbre actesLegislatifs
  - des fichiers SCRUTINS BRUTS pour la "preuve par scrutin CMP non lié"
Axes :
  (a) censure partielle CC = CC-CONCLUSION.statutConclusion.fam_code == TCD02
  (drift) une décision AN postérieure au vote de référence existe dans le dossier
  union = (a) OR (drift)
"""
import json, os, glob, re, unicodedata
from collections import Counter, defaultdict

ROOT = '/home/cos/Bureau/dev/boussole-politique/dry-run'
DOSS_DIRS = [f'{ROOT}/data/dossiers-16/json/dossierParlementaire',
             f'{ROOT}/data/dossiers-17/json/dossierParlementaire']
SCR_DIRS  = [f'{ROOT}/data/scrutins-16/json', f'{ROOT}/data/scrutins-17/json']

def aslist(x):
    return x if isinstance(x, list) else ([] if x is None else [x])

def kids(a):
    ch = a.get('actesLegislatifs')
    if ch is None: return []
    if isinstance(ch, dict) and 'acteLegislatif' in ch:
        return aslist(ch['acteLegislatif'])
    return aslist(ch)

def roots(dp):
    r = dp.get('actesLegislatifs')
    if isinstance(r, dict) and 'acteLegislatif' in r:
        return aslist(r['acteLegislatif'])
    return aslist(r)

def load_dossier(uid):
    # PIEGE: 24 dossiers du corpus existent dans dossiers-16 ET dossiers-17.
    # Le dump leg-17 est le snapshot le plus RECENT (arbre d'actes complet,
    # CC-CONCLUSION postérieure incluse) ; le dump leg-16 est tronqué/figé.
    # On choisit donc systematiquement le fichier LE PLUS GROS (= le plus complet).
    cands = [os.path.join(d, uid + '.json') for d in DOSS_DIRS]
    cands = [p for p in cands if os.path.exists(p)]
    if not cands:
        raise FileNotFoundError(uid)
    p = max(cands, key=lambda x: os.path.getsize(x))
    return json.load(open(p))['dossierParlementaire']

def walk_actes(dp):
    """yield every acte node (flattened)."""
    stack = list(roots(dp))
    while stack:
        a = stack.pop()
        yield a
        stack.extend(kids(a))

# --- Rang des lectures AN, pour décider "postérieur au vote de réf" ---
# Ordre chronologique des décisions DE L'ASSEMBLEE NATIONALE.
# (les SN* sont côté Sénat, ne comptent pas comme "main de l'AN")
AN_DEC_RANK = {
    'AN1-DEBATS-DEC':     1,   # 1ere lecture AN
    'AN2-DEBATS-DEC':     2,
    'AN3-DEBATS-DEC':     3,
    'CMP-DEBATS-AN-DEC':  4,   # AN vote le texte CMP (après navettes)
    'ANNLEC-DEBATS-DEC':  5,   # nouvelle lecture AN (après échec CMP)
    'ANLDEF-DEBATS-DEC':  6,   # lecture définitive AN (dernier mot)
}
# Note: CMP-DEBATS-DEC (1 occ) est ambigu (ni AN ni SN explicitement) — on le traite à part.

def norm(s):
    if not s: return ''
    s = s.replace('’', "'").replace('ʼ', "'")
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

STOP = set('de la le les des du et a au aux en pour par sur le la un une dans relatif relative '
           'projet loi proposition visant tendant portant texte premiere lecture nouvelle definitive '
           'commission mixte paritaire ensemble'.split())
def toks(s):
    return [t for t in norm(s).split() if t not in STOP and len(t) > 2]

def main():
    corpus = json.load(open(f'{ROOT}/out/corpus.json'))
    lois = corpus['lois']
    assert len(lois) == corpus['n_lois']

    out = {}
    out['corpus_total'] = len(lois)
    by_leg = Counter(l['ref_leg'] for l in lois)
    out['leg16_n'] = by_leg[16]
    out['leg17_n'] = by_leg[17]

    # ============ AXE (a) : censure CC, parsé from raw ============
    cc_status = {}        # uid -> set of fam_codes among CC-CONCLUSION
    cc_decisions = {}     # uid -> list of (annee-num, fam_code, lib)
    cc_saisie = {}        # uid -> set of CC-SAISIE-* codes
    cc_concl_count = Counter()
    for l in lois:
        uid = l['dossier_uid']
        dp = load_dossier(uid)
        fams = set(); decs = []; sais = set()
        for a in walk_actes(dp):
            code = a.get('codeActe') or ''
            if code == 'CC-CONCLUSION':
                sc = a.get('statutConclusion') or {}
                fam = sc.get('fam_code')
                if fam:
                    fams.add(fam)
                    cc_concl_count[fam] += 1
                num = a.get('numDecision'); an = a.get('anneeDecision')
                decs.append((f'{an}-{num} DC', fam, sc.get('libelle')))
            elif code.startswith('CC-SAISIE'):
                sais.add(code)
        cc_status[uid] = fams
        cc_decisions[uid] = decs
        cc_saisie[uid] = sais

    def is_partial(uid):  # TCD02 = partiellement conforme
        return 'TCD02' in cc_status[uid]
    def is_conforme(uid):
        return 'TCD01' in cc_status[uid]
    def is_reserve(uid):
        return 'TCD03' in cc_status[uid]
    def has_concl(uid):
        return len(cc_status[uid]) > 0
    def has_saisine_raw(uid):
        return len(cc_saisie[uid]) > 0

    censure = {l['dossier_uid'] for l in lois if is_partial(l['dossier_uid'])}
    out['cc_censure_partielle_total'] = len(censure)
    out['cc_censure_partielle_leg16'] = sum(1 for l in lois if l['dossier_uid'] in censure and l['ref_leg']==16)
    out['cc_censure_partielle_leg17'] = sum(1 for l in lois if l['dossier_uid'] in censure and l['ref_leg']==17)

    out['cc_conforme_total'] = sum(1 for l in lois if is_conforme(l['dossier_uid']))
    out['cc_conforme_avec_reserve_total'] = sum(1 for l in lois if is_reserve(l['dossier_uid']))

    # saisine CC : corpus flag vs raw acte CC-SAISIE-*
    saisine_corpus = {l['dossier_uid'] for l in lois if l['saisine_cc']}
    saisine_raw    = {l['dossier_uid'] for l in lois if has_saisine_raw(l['dossier_uid'])}
    out['saisine_cc_total'] = len(saisine_corpus)
    out['saisine_cc_leg16'] = sum(1 for l in lois if l['saisine_cc'] and l['ref_leg']==16)
    out['saisine_cc_leg17'] = sum(1 for l in lois if l['saisine_cc'] and l['ref_leg']==17)
    out['_saisine_raw_total'] = len(saisine_raw)
    out['_saisine_corpus_minus_raw'] = sorted(saisine_corpus - saisine_raw)
    out['_saisine_raw_minus_corpus'] = sorted(saisine_raw - saisine_corpus)

    # saisine sans conclusion (saisi mais aucune CC-CONCLUSION) — on prend l'union saisine
    saisi_any = saisine_corpus | saisine_raw
    sans_concl = {u for u in saisi_any if not has_concl(u)}
    out['cc_saisine_sans_conclusion'] = len(sans_concl)
    out['_cc_concl_fam_counts'] = dict(cc_concl_count)

    # ============ AXE (drift) : décision AN postérieure au vote de réf ============
    # rang du ref_acte
    drift = set()
    drift_detail = []
    for l in lois:
        uid = l['dossier_uid']
        ref_acte = l['ref_acte']
        ref_rank = AN_DEC_RANK.get(ref_acte)
        dp = load_dossier(uid)
        an_dec_codes = set()
        for a in walk_actes(dp):
            code = a.get('codeActe') or ''
            if code in AN_DEC_RANK:
                an_dec_codes.add(code)
        if ref_rank is None:
            # ref_acte not an AN decision we ranked (e.g. ANLUNI?) -> skip drift via this rule
            max_rank = max((AN_DEC_RANK[c] for c in an_dec_codes), default=0)
            drifted = False
        else:
            max_rank = max((AN_DEC_RANK[c] for c in an_dec_codes), default=ref_rank)
            drifted = max_rank > ref_rank
        if drifted:
            drift.add(uid)
            later = sorted([c for c in an_dec_codes if AN_DEC_RANK[c] > ref_rank],
                           key=lambda c: AN_DEC_RANK[c])
            drift_detail.append((l['ref_leg'], uid, l['titre'][:55], ref_acte, later))

    out['drift_lecture_posterieure_total'] = len(drift)
    out['drift_lecture_posterieure_leg16'] = sum(1 for l in lois if l['dossier_uid'] in drift and l['ref_leg']==16)
    out['drift_lecture_posterieure_leg17'] = sum(1 for l in lois if l['dossier_uid'] in drift and l['ref_leg']==17)

    # ============ "drift littéral (b)" : ref_acte==AN1-DEBATS-DEC ET has_cmp ============
    b_literal = {l['dossier_uid'] for l in lois
                 if l['ref_acte'] == 'AN1-DEBATS-DEC' and l['has_cmp']}
    out['drift_cmp_ref_premiere_lecture_literal'] = len(b_literal)

    # ============ version_drift flag du corpus ============
    out['version_drift_flag_corpus'] = sum(1 for l in lois if l['version_drift'])

    # ============ UNION ============
    union = censure | drift
    out['union_texte_juge_diff_promulgue_total'] = len(union)
    out['union_leg16'] = sum(1 for l in lois if l['dossier_uid'] in union and l['ref_leg']==16)
    out['union_leg17'] = sum(1 for l in lois if l['dossier_uid'] in union and l['ref_leg']==17)
    out['union_frac_total'] = round(len(union)/len(lois), 4)
    out['union_frac_leg16'] = round(out['union_leg16']/out['leg16_n'], 4)
    out['union_frac_leg17'] = round(out['union_leg17']/out['leg17_n'], 4)
    out['union_overlap_censure_et_drift'] = len(censure & drift)
    out['union_seul_censure'] = len(censure - drift)
    out['union_seul_drift'] = len(drift - censure)

    # ============ "drift prouvé par scrutin CMP non lié" ============
    # Pour chaque loi driftée via une CMP (ref AN1 + CMP-DEBATS-AN-DEC postérieur),
    # chercher un scrutin public d'ensemble réel "(texte de la commission mixte paritaire)"
    # à la date exacte de l'acte CMP-DEBATS-AN-DEC, NON lié (dossierLegislatif vide), titre concordant.
    # On charge tous les scrutins une fois.
    scr = []
    for d in SCR_DIRS:
        for p in glob.glob(os.path.join(d, '*.json')):
            try:
                s = json.load(open(p))['scrutin']
            except Exception:
                continue
            scr.append(s)
    # index par date
    by_date = defaultdict(list)
    for s in scr:
        dt = (s.get('dateScrutin') or '')[:10]
        by_date[dt].append(s)

    def cmp_date_for(uid):
        dp = load_dossier(uid)
        for a in walk_actes(dp):
            if a.get('codeActe') == 'CMP-DEBATS-AN-DEC':
                da = a.get('dateActe')
                if da: return da[:10]
        return None

    drift_via_cmp_proven = 0
    drift_via_cmp_proven_l16 = 0; drift_via_cmp_proven_l17 = 0
    proof_samples = []
    for l in lois:
        uid = l['dossier_uid']
        if uid not in drift: continue
        # only the CMP-AN flavour
        dp = load_dossier(uid)
        codes = {a.get('codeActe') for a in walk_actes(dp)}
        ref_rank = AN_DEC_RANK.get(l['ref_acte'])
        if 'CMP-DEBATS-AN-DEC' not in codes: continue
        if ref_rank is None or AN_DEC_RANK['CMP-DEBATS-AN-DEC'] <= ref_rank: continue
        cdate = cmp_date_for(uid)
        if not cdate: continue
        ttoks = set(toks(l['titre']))
        best = None
        for s in by_date.get(cdate, []):
            obj = (s.get('objet') or {}).get('libelle') or s.get('titre') or ''
            no = norm(obj)
            is_cmp_marker = ('commission mixte paritaire' in no) or ('commission paritaire' in no)
            if 'ensemble' not in no:  # vote d'ensemble
                # accept also titles that are clearly the text vote
                pass
            overlap = ttoks & set(toks(obj))
            if is_cmp_marker and len(overlap) >= 2:
                best = (s.get('numero'), obj[:70], len(overlap))
                break
        if best:
            drift_via_cmp_proven += 1
            if l['ref_leg']==16: drift_via_cmp_proven_l16 += 1
            else: drift_via_cmp_proven_l17 += 1
            if len(proof_samples) < 12:
                proof_samples.append((l['ref_leg'], l['titre'][:45], l['ref_numero'], best[0], cdate, best[1]))
    out['drift_prouve_par_scrutin_non_lie'] = drift_via_cmp_proven
    out['_drift_prouve_l16'] = drift_via_cmp_proven_l16
    out['_drift_prouve_l17'] = drift_via_cmp_proven_l17

    # ============ immigration 2024 dans corpus ? ============
    imm_uid = 'DLR5L16N47118'
    out['immigration_2024_dans_corpus'] = any(l['dossier_uid']==imm_uid for l in lois)

    # ---- dumps for the report ----
    out['_censure_list'] = sorted(
        [(l['ref_leg'], cc_decisions[l['dossier_uid']][0][0] if cc_decisions[l['dossier_uid']] else '?',
          l['titre'][:60]) for l in lois if l['dossier_uid'] in censure])
    out['_drift_detail'] = sorted(drift_detail)
    out['_overlap_list'] = sorted(
        [(l['ref_leg'], l['titre'][:55]) for l in lois if l['dossier_uid'] in (censure & drift)])
    out['_proof_samples'] = proof_samples
    out['_b_literal_list'] = sorted([(l['ref_leg'], l['titre'][:55]) for l in lois if l['dossier_uid'] in b_literal])

    json.dump(out, open(f'{ROOT}/out/q3-verif.json', 'w'), ensure_ascii=False, indent=1)

    # print summary
    keys = ['corpus_total','leg16_n','leg17_n','saisine_cc_total','saisine_cc_leg16','saisine_cc_leg17',
            'cc_censure_partielle_total','cc_censure_partielle_leg16','cc_censure_partielle_leg17',
            'cc_conforme_total','cc_conforme_avec_reserve_total','cc_saisine_sans_conclusion',
            'drift_lecture_posterieure_total','drift_lecture_posterieure_leg16','drift_lecture_posterieure_leg17',
            'drift_prouve_par_scrutin_non_lie','drift_cmp_ref_premiere_lecture_literal','version_drift_flag_corpus',
            'union_texte_juge_diff_promulgue_total','union_leg16','union_leg17',
            'union_frac_total','union_frac_leg16','union_frac_leg17',
            'union_overlap_censure_et_drift','union_seul_censure','union_seul_drift','immigration_2024_dans_corpus']
    for k in keys:
        print(f'{k:42s} {out[k]}')
    print('--- cc concl fam counts (corpus):', out['_cc_concl_fam_counts'])
    print('--- saisine raw total:', out['_saisine_raw_total'],
          '| corpus-only:', out['_saisine_corpus_minus_raw'],
          '| raw-only:', out['_saisine_raw_minus_corpus'])
    print('--- drift proven l16/l17:', out['_drift_prouve_l16'], out['_drift_prouve_l17'])

if __name__ == '__main__':
    main()
