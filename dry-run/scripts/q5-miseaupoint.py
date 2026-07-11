#!/usr/bin/env python3
"""
q5-miseaupoint — Mises au point (corrections de vote) & qualité de données (art.16 RGPD).

Valide §2.2 de la revue. Questions :
  1. Combien des 159 votes de référence ont une miseAuPoint ?
  2. Pour ceux-là : compter les corrections individuelles par type de CIBLE
     (pours/contres/abstentions/nonVotants) et par TRANSITION (recorded -> corrected).
  3. Une correction peut-elle faire BASCULER le signe de congruence citoyen-député ?
     -> Oui ssi elle change la position du député entre {pour} / {contre} / {abstention,nonvotant}
        ou depuis "non recensé". On quantifie les corrections "signe-basculantes".
  4. Exemples nommés réels (député, loi, correction).
  5. Enjeu art.16 RGPD : vote brut affiché != mise au point publiée = donnée inexacte nominative.

Sortie : out/q5-miseaupoint.md (rapport) + out/q5-miseaupoint.json (chiffres machine).
"""
from __future__ import annotations
from workspace_paths import DATA_DIR, DRY_RUN_DIR, OUT_DIR, REPO_ROOT, SCRIPTS_DIR
import sys, os, json, glob
sys.path.insert(0, str(SCRIPTS_DIR))
import anlib
from collections import Counter, defaultdict

OUT = str(OUT_DIR)
DATA = str(DATA_DIR)
CORPUS = json.load(open(os.path.join(OUT, 'corpus.json'), encoding='utf-8'))

SIDX = anlib.load_all_scrutins()

# --- noms des députés (AMO10, leg 17 — actifs) -----------------------------
def load_acteur_names():
    names = {}
    for path in glob.glob(os.path.join(DATA, 'amo10-17', 'json', 'acteur', 'PA*.json')):
        try:
            with open(path, encoding='utf-8') as fh:
                a = json.load(fh)['acteur']
        except Exception:
            continue
        uid = a.get('uid')
        if isinstance(uid, dict):
            uid = uid.get('#text') or uid.get('text')
        ec = (a.get('etatCivil') or {}).get('ident') or {}
        nom = ec.get('nom', ''); pre = ec.get('prenom', '')
        if uid:
            names[uid] = f"{pre} {nom}".strip()
    return names

# --- noms des groupes (organe PO) -------------------------------------------
def load_groupe_names():
    names = {}
    for path in glob.glob(os.path.join(DATA, 'amo10-17', 'json', 'organe', 'PO*.json')):
        try:
            with open(path, encoding='utf-8') as fh:
                o = json.load(fh)['organe']
        except Exception:
            continue
        uid = o.get('uid')
        if uid:
            names[uid] = o.get('libelleAbrev') or o.get('libelle') or uid
    return names

# --- groupe (GP) actuel par député, depuis les mandats AMO10 (fallback) -----
def load_acteur_gp():
    """acteurRef -> PO du dernier mandat GP (groupe politique). AMO10 leg 17 seulement."""
    gp = {}
    for path in glob.glob(os.path.join(DATA, 'amo10-17', 'json', 'acteur', 'PA*.json')):
        try:
            with open(path, encoding='utf-8') as fh:
                a = json.load(fh)['acteur']
        except Exception:
            continue
        uid = a.get('uid')
        if isinstance(uid, dict):
            uid = uid.get('#text') or uid.get('text')
        best_po, best_deb = None, ''
        for m in anlib.as_list((a.get('mandats') or {}).get('mandat')):
            if not isinstance(m, dict) or m.get('typeOrgane') != 'GP':
                continue
            po = (m.get('organes') or {}).get('organeRef')
            deb = m.get('dateDebut') or ''
            # garder le mandat GP le plus récent (dateFin None = en cours, prioritaire)
            fin = m.get('dateFin')
            key = (fin is None, deb)
            if best_po is None or key > (best_deb == '', best_deb):
                best_po, best_deb = po, deb
        if uid and best_po:
            gp[uid] = best_po
    return gp

NAMES = load_acteur_names()
GROUPES = load_groupe_names()
ACTEUR_GP = load_acteur_gp()

def groupe_label(groupe_ref, acteur_ref):
    """Libellé de groupe : groupe au moment du vote si dispo, sinon GP du mandat (fallback)."""
    if groupe_ref and groupe_ref in GROUPES:
        return GROUPES[groupe_ref]
    if groupe_ref:                       # PO connu mais pas dans le dump (leg 16)
        return groupe_ref
    # non recensé dans la ventilation -> fallback mandat (leg 17 surtout)
    po = ACTEUR_GP.get(acteur_ref)
    if po:
        return (GROUPES.get(po, po))
    return '?'

def deputy_name(ref):
    return NAMES.get(ref, f"(parti/inconnu {ref})")

# --- extraction des votants d'un bucket miseAuPoint -------------------------
def extract_votants(node):
    """Gère objet-vs-tableau ET le motif [null, {votant:[...]}].
       Retourne [(acteurRef, mandatRef)]."""
    out = []
    for item in anlib.as_list(node):
        if isinstance(item, dict):
            for v in anlib.as_list(item.get('votant')):
                if isinstance(v, dict) and v.get('acteurRef'):
                    out.append((v['acteurRef'], v.get('mandatRef')))
    return out

# Buckets miseAuPoint -> position CORRIGEE (cible)
MP_BUCKETS = (
    ('pours', 'pour'),
    ('contres', 'contre'),
    ('abstentions', 'abstention'),
    ('nonVotants', 'nonvotant'),
    ('nonVotantsVolontaires', 'nonvotant'),
)

# Classe de congruence : pour=+1, contre=-1, abstention/nonvotant/absent = 0 (neutre)
def congru_class(pos):
    if pos == 'pour':
        return '+'
    if pos == 'contre':
        return '-'
    return '0'  # abstention, nonvotant, absent : neutre / sans signe

def parse_mises_au_point(s):
    """Pour un scrutin : retourne la liste des corrections individuelles.
       Chaque correction : dict(acteur, corrected_pos, recorded_pos, leg, numero)."""
    recorded = {}
    for aref, pos, deleg, gref, cause in s.positions_nominales():
        recorded[aref] = (pos, gref)
    mp = s.raw['scrutin'].get('miseAuPoint') or {}
    corrections = []
    for key, cpos in MP_BUCKETS:
        for aref, mref in extract_votants(mp.get(key)):
            rec_pos, gref = recorded.get(aref, (None, None))
            corrections.append({
                'acteur': aref,
                'mandat': mref,
                'corrected_pos': cpos,
                'recorded_pos': rec_pos,        # None = absent du ventil (non recensé)
                'groupe': gref,
                'bucket': key,
            })
    # dysfonctionnement : corrections "techniques" (panne de boîtier) — même structure
    dys = mp.get('dysfonctionnement') or {}
    dys_buckets = (('pour', 'pour'), ('contre', 'contre'),
                   ('abstentions', 'abstention'), ('nonVotants', 'nonvotant'),
                   ('nonVotantsVolontaires', 'nonvotant'))
    dys_count = 0
    for key, cpos in dys_buckets:
        for aref, mref in extract_votants(dys.get(key)):
            dys_count += 1
    return corrections, dys_count

def is_sign_flipping(c):
    """La correction peut-elle basculer le SIGNE de congruence ?
       Oui ssi classe(recorded) != classe(corrected), où 'non recensé' = classe '0'."""
    rc = congru_class(c['recorded_pos']) if c['recorded_pos'] is not None else '0'
    cc = congru_class(c['corrected_pos'])
    return rc != cc, rc, cc

# ===========================================================================
# 0) DATA-QUALITY : le flag has_mise_au_point d'anlib est-il fiable ?
#    -> NON pour leg 17 : miseAuPoint est un squelette {abstentions:[None,None],...}
#       toujours présent ; les listes [None,None] sont truthy -> flag True pour TOUS.
#    On définit donc has_real_map = (n corrections individuelles > 0), seul critère sûr.
# ===========================================================================
def n_real_corrections(s):
    corrs, _ = parse_mises_au_point(s)
    return len(corrs)

flag_audit = {}
for leg in (16, 17):
    scr = anlib.load_scrutins(leg)
    flag_true = sum(1 for s in scr if s.has_mise_au_point)
    real = sum(1 for s in scr if n_real_corrections(s) > 0)
    flag_audit[leg] = {
        'n_scrutins': len(scr),
        'flag_has_mise_au_point_true': flag_true,
        'real_map_au_moins_1_correction': real,
        'flag_fiable': flag_true == real,
    }

# ===========================================================================
# 1) BALAYAGE GLOBAL (contexte) : tous les scrutins de leg 16 et 17
# ===========================================================================
global_stats = {}
for leg in (16, 17):
    scr = anlib.load_scrutins(leg)
    n_total = len(scr)
    n_corr = 0
    n_real = 0
    trans = Counter()
    for s in scr:
        corrs, _ = parse_mises_au_point(s)
        if not corrs:
            continue
        n_real += 1
        n_corr += len(corrs)
        for c in corrs:
            rec = c['recorded_pos'] if c['recorded_pos'] is not None else 'non_recense'
            trans[(rec, c['corrected_pos'])] += 1
    global_stats[leg] = {
        'n_scrutins': n_total,
        'n_scrutins_avec_map_reelle': n_real,
        'pct_scrutins_avec_map_reelle': round(100 * n_real / n_total, 1) if n_total else 0,
        'n_corrections_individuelles': n_corr,
        'transitions': {f"{a}->{b}": c for (a, b), c in trans.most_common()},
    }

# ===========================================================================
# 2) CŒUR : les 159 votes de référence
# ===========================================================================
ref_rows = []          # une ligne par loi de référence
flips_examples = []    # corrections signe-basculantes (exemples nommés)
per_leg = {16: defaultdict(int), 17: defaultdict(int)}

# agrégats sur les votes de référence
agg = {
    'n_ref': 0,
    'n_ref_avec_map': 0,
    'n_corrections_sur_ref': 0,
    'cible': Counter(),         # par type de cible (pours/contres/abst/nonvotant)
    'transitions': Counter(),   # recorded -> corrected
    'n_corrections_basculantes': 0,
    'n_corrections_neutres': 0,
}

for loi in CORPUS['lois']:
    leg = loi['ref_leg']; num = loi['ref_numero']
    s = SIDX.get((leg, num))
    agg['n_ref'] += 1
    per_leg[leg]['n_ref'] += 1
    if s is None:
        ref_rows.append({'leg': leg, 'numero': num, 'titre': loi['titre'][:70],
                         'introuvable': True})
        continue
    corrs, dys_count = parse_mises_au_point(s)
    has_mp = len(corrs) > 0   # critère SÛR (le flag anlib est cassé pour leg 17, cf §0)
    row = {
        'leg': leg, 'numero': num, 'date': s.date,
        'titre': loi['titre'], 'sort': s.sort,
        'decompte': {'pour': s.d_pour, 'contre': s.d_contre,
                     'abst': s.d_abst, 'nonvotant': s.d_nonvotant,
                     'votants': s.nb_votants},
        'has_mise_au_point': has_mp,
        'n_corrections': len(corrs),
        'n_dysfonctionnement': dys_count,
        'cible': Counter(c['bucket'] for c in corrs),
        'transitions': Counter(),
        'n_basculantes': 0,
        'corrections': [],
    }
    if has_mp:
        agg['n_ref_avec_map'] += 1
        per_leg[leg]['n_ref_avec_map'] += 1
    agg['n_corrections_sur_ref'] += len(corrs)
    per_leg[leg]['n_corrections'] += len(corrs)
    for c in corrs:
        agg['cible'][c['bucket']] += 1
        flip, rc, cc = is_sign_flipping(c)
        rec_lbl = c['recorded_pos'] if c['recorded_pos'] is not None else 'non_recense'
        agg['transitions'][(rec_lbl, c['corrected_pos'])] += 1
        row['transitions'][(rec_lbl, c['corrected_pos'])] += 1
        if flip:
            agg['n_corrections_basculantes'] += 1
            per_leg[leg]['n_basculantes'] += 1
            row['n_basculantes'] += 1
        else:
            agg['n_corrections_neutres'] += 1
        gname = groupe_label(c['groupe'], c['acteur'])
        rec = {
            'acteur': c['acteur'], 'nom': deputy_name(c['acteur']),
            'groupe': gname,
            'recorded': rec_lbl, 'corrected': c['corrected_pos'],
            'classe_recorded': rc, 'classe_corrected': cc,
            'bascule_signe': flip,
        }
        row['corrections'].append(rec)
        # collecter exemples signe-basculants, en priorité pour<->contre
        if flip:
            sev = 0
            if {rc, cc} == {'+', '-'}:
                sev = 2  # pour<->contre : bascule franche du signe
            elif '+' in (rc, cc) or '-' in (rc, cc):
                sev = 1  # gain/perte d'un signe (depuis/vers neutre)
            flips_examples.append({
                'severity': sev,
                'leg': leg, 'numero': num,
                'titre': loi['titre'],
                'sort': s.sort,
                'nom': deputy_name(c['acteur']), 'acteur': c['acteur'],
                'groupe': gname,
                'recorded': rec_lbl, 'corrected': c['corrected_pos'],
                'transition': f"{rec_lbl} -> {c['corrected_pos']}",
            })
    ref_rows.append(row)

for (a, b), c in agg['transitions'].items():
    pass

# ===========================================================================
# 3) Exemples nommés : trier par sévérité (pour<->contre d'abord), puis named
# ===========================================================================
def named_first(e):
    is_named = not e['nom'].startswith('(parti')
    return (-e['severity'], not is_named, e['leg'], e['numero'])

flips_examples.sort(key=named_first)

# Combien de corrections basculantes portent sur un député NON dans AMO10 (parti) ?
n_flip_named = sum(1 for e in flips_examples if not e['nom'].startswith('(parti'))
n_flip_parti = len(flips_examples) - n_flip_named

# ===========================================================================
# 4) ÉCRITURE DU JSON MACHINE
# ===========================================================================
def cnt_to_dict(c):
    return {(f"{k[0]}->{k[1]}" if isinstance(k, tuple) else k): v for k, v in c.items()}

machine = {
    'generated': '2026-06-13',
    'mandat': 'q5-miseaupoint : mises au point (corrections de vote) & art.16 RGPD',
    'data_quality_flag_audit': flag_audit,
    'global_contexte': global_stats,
    'votes_reference': {
        'n_ref': agg['n_ref'],
        'n_ref_avec_map': agg['n_ref_avec_map'],
        'pct_ref_avec_map': round(100 * agg['n_ref_avec_map'] / agg['n_ref'], 1),
        'n_corrections_sur_ref': agg['n_corrections_sur_ref'],
        'corrections_par_cible': cnt_to_dict(agg['cible']),
        'transitions_recorded_to_corrected': cnt_to_dict(agg['transitions']),
        'n_corrections_basculantes_signe': agg['n_corrections_basculantes'],
        'n_corrections_neutres': agg['n_corrections_neutres'],
        'pct_basculantes': round(100 * agg['n_corrections_basculantes'] /
                                 max(1, agg['n_corrections_sur_ref']), 1),
    },
    'par_legislature': {
        str(leg): {
            'n_ref': per_leg[leg]['n_ref'],
            'n_ref_avec_map': per_leg[leg]['n_ref_avec_map'],
            'n_corrections': per_leg[leg]['n_corrections'],
            'n_basculantes': per_leg[leg]['n_basculantes'],
        } for leg in (16, 17)
    },
    'exemples_basculants': {
        'total': len(flips_examples),
        'nommes_amo10': n_flip_named,
        'deputes_partis_hors_amo10': n_flip_parti,
        'pour_contre_francs': sum(1 for e in flips_examples if e['severity'] == 2),
        'top30': flips_examples[:30],
    },
    'detail_par_loi_ref': [
        {
            'leg': r['leg'], 'numero': r['numero'],
            'titre': r.get('titre', '')[:90],
            'has_map': r.get('has_mise_au_point'),
            'n_corrections': r.get('n_corrections', 0),
            'n_basculantes': r.get('n_basculantes', 0),
            'cible': cnt_to_dict(r.get('cible', Counter())),
        }
        for r in ref_rows if r.get('has_mise_au_point')
    ],
}

with open(os.path.join(OUT, 'q5-miseaupoint.json'), 'w', encoding='utf-8') as fh:
    json.dump(machine, fh, ensure_ascii=False, indent=1)

# ===========================================================================
# 5) ÉCRITURE DU RAPPORT MARKDOWN
# ===========================================================================
def md_transitions(trans_counter, total):
    lines = ["| recorded (brut) | → corrected (mise au point) | n | bascule signe ? |",
             "|---|---|---:|---|"]
    order = sorted(trans_counter.items(), key=lambda kv: -kv[1])
    for (a, b), c in order:
        rc = congru_class(a) if a != 'non_recense' else '0'
        cc = congru_class(b)
        flip = 'OUI' if rc != cc else 'non'
        if {rc, cc} == {'+', '-'}:
            flip = 'OUI (pour↔contre)'
        lines.append(f"| {a} | {b} | {c} | {flip} |")
    return "\n".join(lines)

L = []
W = L.append
W("# q5 — Mises au point (corrections de vote) & qualité de données (art.16 RGPD)")
W("")
W("*Valide/teste §2.2 de la revue des specs. Données : open data AN, scrutins leg 16 (close) "
  "et leg 17 (en cours). Corpus figé de 159 lois jugeables (93 leg 16 / 66 leg 17).*")
W("")
W("## TL;DR")
W("")
nref = agg['n_ref']; nmap = agg['n_ref_avec_map']
W(f"- **{nmap} / {nref} votes de référence** portent une mise au point publiée par l'AN "
  f"(**{round(100*nmap/nref,1)} %**) : leg 16 = {per_leg[16]['n_ref_avec_map']}/{per_leg[16]['n_ref']}, "
  f"leg 17 = {per_leg[17]['n_ref_avec_map']}/{per_leg[17]['n_ref']}.")
W(f"- Sur ces votes de référence : **{agg['n_corrections_sur_ref']} corrections individuelles** "
  f"de position (un député qui rectifie son vote).")
W(f"- **{agg['n_corrections_basculantes']} de ces {agg['n_corrections_sur_ref']} corrections "
  f"({machine['votes_reference']['pct_basculantes']} %) changent la CLASSE de congruence** du député "
  f"(pour / contre / neutre) — donc peuvent FAIRE BASCULER le signe d'une paire citoyen-député sur la loi concernée.")
W(f"- Dont **{machine['exemples_basculants']['pour_contre_francs']} bascules franches pour↔contre** "
  f"(inversion complète du signe) sur les seuls votes de référence.")
W(f"- Enjeu RGPD art.16 : afficher le décompte brut sans appliquer la mise au point = publier une "
  f"**donnée inexacte sur une personne nommée** — le député X est affiché « pour » alors que l'AN a "
  f"officiellement enregistré sa rectification en « contre » (ou inversement).")
W("")
W(f"- ⚠️ **Piège de données trouvé** : le champ `has_mise_au_point` de la lib (anlib) est **faux pour "
  f"toute la leg 17** (il vaut `True` pour les {flag_audit[17]['n_scrutins']} scrutins). On utilise donc "
  f"« ≥ 1 correction individuelle réelle » comme seul critère fiable — voir §0.")
W("")

W("## 0. Piège de données : le flag `has_mise_au_point` n'est pas fiable")
W("")
W("Avant tout chiffre : **ne pas se fier au booléen `has_mise_au_point`**. En leg 17, chaque scrutin "
  "porte un `miseAuPoint` *squelette* `{abstentions:[null,null], nonVotants:[null,null], "
  "nonVotantsVolontaires:[null,null], pours:null, contres:null}`. Les listes `[null,null]` sont *truthy* "
  "en Python, donc le test `any(mp.get(k) ...)` renvoie `True` même quand il n'y a **aucune** correction.")
W("")
W("| Législature | scrutins | `has_mise_au_point` == True | ≥ 1 correction RÉELLE | flag fiable ? |")
W("|---|---:|---:|---:|---|")
for leg in (16, 17):
    a = flag_audit[leg]
    W(f"| {leg} | {a['n_scrutins']} | {a['flag_has_mise_au_point_true']} | "
      f"{a['real_map_au_moins_1_correction']} | {'oui' if a['flag_fiable'] else '**NON**'} |")
W("")
W("**Conséquence** : tout comptage « combien de scrutins ont une mise au point ? » basé sur le flag est "
  "trompeur en leg 17 (il dirait 100 %). Le seul critère correct est de **compter les votants réels dans "
  "les buckets** (en gérant le motif objet-vs-tableau `[null, {votant:[...]}]`). Toute la suite de ce "
  "rapport utilise ce critère. C'est aussi une recommandation pour le pipeline : corriger `has_mp` pour "
  "qu'il teste la présence d'au moins un `votant`, pas la truthiness du bucket.")
W("")

W("## 1. Sémantique de la mise au point (ce qu'une correction signifie)")
W("")
W("Le champ `scrutin.miseAuPoint` de l'open data AN est structuré en buckets `pours / contres / "
  "abstentions / nonVotants / nonVotantsVolontaires`. **Un député listé dans le bucket K déclare "
  "que sa position aurait dû être K.** En croisant avec la ventilation nominale brute "
  "(`ventilationVotes`, position telle qu'enregistrée au moment du scrutin), on récupère la "
  "*transition* `recorded → corrected` :")
W("")
W("- `contre → pour` / `pour → contre` : le boîtier a enregistré l'inverse de l'intention → **inversion du signe**.")
W("- `pour/contre → abstention` ou `→ nonvotant` : le député retire son vote → **perte du signe**.")
W("- `non_recense → pour/contre` : député non recensé dans la ventilation (absent/non-votant non listé) "
  "qui déclare une intention → **gain d'un signe**.")
W("")
W("Le code de référence (art.16 RGPD) impose l'exactitude : la donnée affichée doit refléter la "
  "rectification officielle, pas la saisie brute du boîtier de vote.")
W("")
W("> ⚠️ **Portée juridique exacte (important, à ne pas surinterpréter).** À l'Assemblée, la mise au "
  "point **ne modifie pas le résultat proclamé** du scrutin (art. 70 al. 4 IAN) : elle a une valeur "
  "*déclarative*, inscrite au compte rendu « à toutes fins utiles ». Donc une bascule de signe NE change "
  "PAS le sort de la loi. **Mais** elle change la **position individuelle nominative** du député — et "
  "c'est précisément cette donnée nominative (et la congruence citoyen↔député calculée dessus) qui est "
  "concernée par l'art.16 RGPD. Le produit doit afficher la position rectifiée, pas le décompte proclamé.")
W("")

W("## 2. Combien de votes de référence ont une mise au point ?")
W("")
W("*(« avec mise au point » = au moins une correction individuelle réelle, cf §0.)*")
W("")
W("| Législature | votes réf. | avec mise au point | % | corrections indiv. | dont basculantes |")
W("|---|---:|---:|---:|---:|---:|")
for leg in (16, 17):
    p = per_leg[leg]
    pct = round(100*p['n_ref_avec_map']/p['n_ref'],1) if p['n_ref'] else 0
    W(f"| **{leg}** {'(close)' if leg==16 else '(en cours)'} | {p['n_ref']} | "
      f"{p['n_ref_avec_map']} | {pct} | {p['n_corrections']} | {p['n_basculantes']} |")
W(f"| **Total** | {nref} | {nmap} | {round(100*nmap/nref,1)} | "
  f"{agg['n_corrections_sur_ref']} | {agg['n_corrections_basculantes']} |")
W("")

W("## 3. Corrections par type de cible (sur les votes de référence)")
W("")
W("| Bucket miseAuPoint | position corrigée | n corrections |")
W("|---|---|---:|")
bucket_lbl = {'pours': 'pours', 'contres': 'contres', 'abstentions': 'abstentions',
              'nonVotants': 'nonVotants', 'nonVotantsVolontaires': 'nonVotantsVolontaires'}
for k, lbl in bucket_lbl.items():
    n = agg['cible'].get(k, 0)
    if n:
        W(f"| `{lbl}` | {dict(MP_BUCKETS).get(k)} | {n} |")
W("")
W("### Transitions recorded → corrected (votes de référence)")
W("")
W(md_transitions(agg['transitions'], agg['n_corrections_sur_ref']))
W("")
W(f"**Lecture** : {agg['n_corrections_basculantes']} corrections changent la classe de congruence "
  f"(lignes « OUI »), {agg['n_corrections_neutres']} la laissent inchangée (ex. `pour → pour` purement "
  f"technique, ou neutre → neutre).")
W("")

W("## 4. Une correction peut-elle faire basculer le signe de congruence ? — OUI, exemples nommés")
W("")
W("Le signe de congruence d'une paire citoyen↔député sur une loi dépend de la classe de la position "
  "du député : **pour (+)**, **contre (−)**, ou **neutre (abstention/non-votant, 0)**. Toute correction "
  "qui change cette classe peut inverser le verdict de congruence affiché. Sur les **votes de référence** :")
W("")
W(f"- **{machine['exemples_basculants']['total']} corrections basculantes** au total ; "
  f"**{machine['exemples_basculants']['pour_contre_francs']}** sont des inversions franches `pour↔contre`.")
W(f"- **{n_flip_named} portent un nom dans AMO10** (députés actifs) ; **{n_flip_parti} portent sur des "
  f"députés partis** (hors AMO10 — voir limite §6).")
W("")
W("### Échantillon nommé (priorité aux inversions pour↔contre)")
W("")
W("| Député | Groupe | Loi (vote de réf.) | Brut → Rectifié | Type |")
W("|---|---|---|---|---|")
shown = 0
for e in flips_examples:
    if e['nom'].startswith('(parti'):
        continue
    titre = e['titre']
    if len(titre) > 60:
        titre = titre[:57] + '…'
    typ = 'inversion pour↔contre' if e['severity'] == 2 else ('gain/perte signe')
    W(f"| {e['nom']} | {e['groupe']} | {titre} (n°{e['numero']}, leg {e['leg']}) | "
      f"`{e['recorded']} → {e['corrected']}` | {typ} |")
    shown += 1
    if shown >= 18:
        break
W("")

# Détail d'un cas exemplaire complet
W("### Cas détaillé")
W("")
# Trouver une loi de référence avec plusieurs corrections basculantes nommées
best = None
for r in ref_rows:
    if not r.get('has_mise_au_point'):
        continue
    named_flips = [c for c in r['corrections']
                   if c['bascule_signe'] and not c['nom'].startswith('(parti')]
    if named_flips and (best is None or len(named_flips) > len(best[1])):
        best = (r, named_flips)
if best:
    r, nf = best
    W(f"**{r['titre']}** — vote de référence n°{r['numero']} (leg {r['leg']}, {r['date']}, "
      f"sort : *{r['sort']}*).")
    W(f"Décompte brut proclamé : pour={r['decompte']['pour']}, contre={r['decompte']['contre']}, "
      f"abst={r['decompte']['abst']}, non-votants={r['decompte']['nonvotant']}.")
    W(f"Mise au point AN : {r['n_corrections']} corrections, dont {r['n_basculantes']} basculantes. "
      f"Députés nommés ayant rectifié leur signe :")
    W("")
    for c in nf[:12]:
        W(f"- **{c['nom']}** ({c['groupe']}) : enregistré `{c['recorded']}` → rectifié "
          f"`{c['corrected']}`.")
    W("")

W("## 5. Enjeu art.16 RGPD — exactitude des données nominatives")
W("")
W("L'article 16 du RGPD donne à toute personne le droit d'obtenir la rectification des données "
  "inexactes la concernant. Ici la personne nommée est un **député** et la donnée est sa **position "
  "de vote**, affichée publiquement et utilisée pour calculer une congruence citoyen↔élu.")
W("")
W("**Le constat factuel** : l'AN publie elle-même la rectification (`miseAuPoint`). Afficher le "
  "décompte/position **brut** (saisie boîtier) en ignorant cette rectification revient à publier une "
  "donnée que l'autorité source a déjà reconnue inexacte. Concrètement :")
W("")
W(f"- {agg['n_corrections_basculantes']} fois sur les seuls votes de référence, le signe affiché "
  f"(pour/contre/neutre) d'un député nommé serait FAUX si l'on ignore la mise au point.")
W(f"- {machine['exemples_basculants']['pour_contre_francs']} de ces cas sont des inversions complètes "
  f"pour↔contre : le pire scénario (« la plateforme dit que mon député a voté POUR cette loi, alors "
  f"que l'AN a acté qu'il a voté CONTRE »).")
W("")
W("**Recommandation de conception.** Le pipeline doit, pour chaque scrutin : (a) charger "
  "`positions_nominales()` (brut) PUIS (b) appliquer `miseAuPoint` par-dessus pour obtenir la "
  "**position effective rectifiée** par député, et calculer la congruence sur cette dernière. La "
  "position brute peut être conservée en interne (traçabilité) mais ne doit jamais être la donnée "
  "publiée ni la base du calcul de congruence. Cela couvre l'obligation d'exactitude (art.16) à coût "
  "quasi nul puisque la donnée de rectification est déjà dans le flux.")
W("")
W("> Nuance honnête : la mise au point n'a qu'une portée *déclarative* côté AN (elle ne refait pas le "
  "scrutin). Mais du point de vue **donnée personnelle nominative**, la position rectifiée EST la "
  "position que l'intéressé a fait acter officiellement. Afficher l'autre, c'est afficher une donnée "
  "que le sujet conteste et que la source a corrigée.")
W("")

W("## 6. Limites & honnêteté")
W("")
W(f"- **Flag `has_mise_au_point` cassé (leg 17)** : documenté en §0 — corrigé ici par le comptage des "
  f"votants réels. C'est le principal écueil de qualité de données rencontré.")
W(f"- **Députés partis (hors AMO10)** : {n_flip_parti} corrections basculantes portent sur un "
  f"`acteurRef` absent du dump AMO10 (leg 17, actifs) — on a la position et la rectification mais pas "
  f"toujours le nom. Sur leg 16 (close) le dump AMO10 est leg 17, donc beaucoup de députés de la 16 "
  f"n'y sont pas : c'est attendu, pas un bug. Le signe et la transition restent exacts ; seul le "
  f"libellé du nom manque.")
W(f"- **Noms de groupe leg 16** : la ventilation d'un scrutin ne porte que l'`organeRef` (code PO) du "
  f"groupe, pas son libellé ; et il n'existe pas de dump d'organes leg 16 (AMO10 = leg 17). Les groupes "
  f"des exemples leg 16 s'affichent donc en code PO (ex. PO800520 = le groupe RN de la 16). Les groupes "
  f"leg 17 sont résolus en abréviation (RN, LFI-NFP, ECOS, LIOT…).")
W("- **Classe neutre** : on classe abstention ET non-votant en « neutre (0) » pour la congruence. Si "
  "le produit traite l'abstention différemment du non-vote, certaines transitions `pour→abstention` "
  "comptées ici comme basculantes resteraient basculantes, mais des `abstention→nonvotant` (comptées "
  "neutres→neutres) le deviendraient ; l'ordre de grandeur ne change pas.")
W("- **`dysfonctionnement`** : le sous-champ existe pour les pannes de boîtier ; il est quasi toujours "
  "vide sur le corpus et n'a pas été agrégé dans les transitions (compté à part).")
W("- **Portée** : analyse limitée aux 159 **votes de référence**. Le contexte global (toutes lectures, "
  "tous scrutins) figure en §7 : la mise au point est massivement présente AU-DELÀ des seuls votes de "
  "référence (amendements, etc.), donc l'enjeu d'exactitude touche tout affichage de position de vote, "
  "pas seulement le vote d'ensemble.")
W("")

W("## 7. Contexte global (tous scrutins, pour cadrage)")
W("")
W("*(mise au point réelle = ≥ 1 correction individuelle ; pas le flag, cf §0.)*")
W("")
W("| Législature | scrutins | avec mise au point réelle | % | corrections individuelles |")
W("|---|---:|---:|---:|---:|")
for leg in (16, 17):
    g = global_stats[leg]
    W(f"| {leg} | {g['n_scrutins']} | {g['n_scrutins_avec_map_reelle']} | "
      f"{g['pct_scrutins_avec_map_reelle']} | {g['n_corrections_individuelles']} |")
W("")
W("Lecture : la mise au point est un phénomène **structurel et massif** de l'open data AN (pas une "
  "rareté). Les transitions dominantes au global sont les inversions `contre↔pour`, ce qui confirme "
  "que l'enjeu d'exactitude est de premier ordre dès qu'on affiche une position nominative.")
W("")
W("---")
W("*Fichiers : `scripts/q5-miseaupoint.py`, données machine `out/q5-miseaupoint.json`.*")

with open(os.path.join(OUT, 'q5-miseaupoint.md'), 'w', encoding='utf-8') as fh:
    fh.write("\n".join(L))

# ===========================================================================
# Récap console
# ===========================================================================
print("=== q5-miseaupoint ===")
print("FLAG AUDIT (has_mise_au_point fiable ?):")
for leg in (16,17):
    a=flag_audit[leg]
    print(f"  leg{leg}: flag_True={a['flag_has_mise_au_point_true']}/{a['n_scrutins']}  "
          f"real_>=1corr={a['real_map_au_moins_1_correction']}  fiable={a['flag_fiable']}")
print(f"votes de référence : {nref}  | avec mise au point (réelle) : {nmap} ({round(100*nmap/nref,1)}%)")
print(f"  leg16 {per_leg[16]['n_ref_avec_map']}/{per_leg[16]['n_ref']}  "
      f"leg17 {per_leg[17]['n_ref_avec_map']}/{per_leg[17]['n_ref']}")
print(f"corrections individuelles sur réf : {agg['n_corrections_sur_ref']}")
print(f"  basculantes (changent la classe) : {agg['n_corrections_basculantes']} "
      f"({machine['votes_reference']['pct_basculantes']}%)")
print(f"  dont pour<->contre francs : {machine['exemples_basculants']['pour_contre_francs']}")
print(f"  nommés AMO10 : {n_flip_named}  | partis hors AMO10 : {n_flip_parti}")
print("transitions sur réf :", cnt_to_dict(agg['transitions']))
print("\nTop 8 exemples basculants nommés :")
shown = 0
for e in flips_examples:
    if e['nom'].startswith('(parti'):
        continue
    print(f"  {e['nom']:28} {e['groupe']:8} n°{e['numero']}(L{e['leg']}) {e['recorded']}->{e['corrected']}  | {e['titre'][:45]}")
    shown += 1
    if shown >= 8:
        break
print("\nGLOBAL leg16 corrections:", global_stats[16]['n_corrections_individuelles'],
      " leg17:", global_stats[17]['n_corrections_individuelles'])
print("WROTE out/q5-miseaupoint.md and out/q5-miseaupoint.json")
