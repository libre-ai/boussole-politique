#!/usr/bin/env python3
"""
q2-polarisation — Participation & polarisation des votes de référence.

Teste §4 de la revue (le "reveal plat", risque épistémique n°1) :
si une grande part des 159 votes de référence sont quasi-unanimes, un score de
congruence calculé dessus rend ~même valeur pour TOUS les groupes => reveal qui
n'apprend rien. On le MESURE.

Définitions (toutes sur le vote de référence = numero==ref_numero de chaque loi) :
  - votants  = pour + contre + abst              (= nb_votants AN ; abstention = présent)
  - exprimés = pour + contre                      (= suffrages_exprimes AN ; abst exclue)
  - participation_votants  = votants  / 577
  - participation_exprimes = exprimés / 577
  - minorité = min(pour, contre)
  - part_minorite = minorité / exprimés           (0 = unanime, 0.5 = parfaitement partagé)
  - marge_gagnante = |pour - contre| / exprimés   (1 = unanime, 0 = 50/50)
  - quasi-unanime   : part_minorite < 0.10
  - intermédiaire   : 0.10 <= part_minorite < 0.20
  - discriminant    : part_minorite >= 0.20

Reveal-flatness : pour chaque vote on calcule, par groupe, un "score de congruence"
binaire = la position majoritaire du groupe (pour/contre) coïncide-t-elle avec le sort
adopté/rejeté de la loi ? Un score de congruence agrégé par groupe sur des votes
quasi-unanimes converge vers ~même valeur pour tous les groupes (tout le monde a voté
pareil). On quantifie l'écart inter-groupes.
"""
from workspace_paths import DATA_DIR, DRY_RUN_DIR, OUT_DIR, REPO_ROOT, SCRIPTS_DIR
import sys, json, statistics
from collections import Counter, defaultdict
sys.path.insert(0, str(SCRIPTS_DIR))
import anlib

CORPUS = str(OUT_DIR / "corpus.json")
OUT_JSON = str(OUT_DIR / "q2-polarisation.json")
OUT_MD = str(OUT_DIR / "q2-polarisation.md")
SIEGES = anlib.SIEGES_AN  # 577

QUASI_UNANIME = 0.10   # part minorité < 10% des exprimés
DISCRIMINANT = 0.20    # part minorité >= 20% des exprimés


def pct(n, d):
    return 100.0 * n / d if d else 0.0


def quantiles(xs, qs=(0, 10, 25, 50, 75, 90, 100)):
    """Quantiles simples (interpolation linéaire), xs trié."""
    s = sorted(xs)
    out = {}
    n = len(s)
    if n == 0:
        return {q: None for q in qs}
    for q in qs:
        if q == 0:
            out[q] = s[0]
        elif q == 100:
            out[q] = s[-1]
        else:
            pos = (q / 100) * (n - 1)
            lo = int(pos)
            frac = pos - lo
            out[q] = s[lo] + frac * (s[min(lo + 1, n - 1)] - s[lo]) if lo + 1 < n else s[lo]
    return out


def histogram(xs, edges):
    """Compte par bin [edges[i], edges[i+1]) ; dernier bin inclusif à droite."""
    counts = [0] * (len(edges) - 1)
    for x in xs:
        placed = False
        for i in range(len(edges) - 1):
            lo, hi = edges[i], edges[i + 1]
            if (lo <= x < hi) or (i == len(edges) - 2 and x == hi):
                counts[i] += 1
                placed = True
                break
        if not placed and x < edges[0]:
            counts[0] += 1
    return counts


def load_corpus():
    with open(CORPUS, encoding='utf-8') as fh:
        return json.load(fh)


def ref_vote_record(loi):
    """Retourne le dict du vote de référence d'une loi."""
    for v in loi['votes']:
        if v['numero'] == loi['ref_numero'] and v['leg'] == loi['ref_leg']:
            return v
    return None


def analyse_one(loi, scrutin):
    v = ref_vote_record(loi)
    pour, contre, abst = v['pour'], v['contre'], v['abst']
    nonvot = v['nonvotant']
    votants = pour + contre + abst
    exprimes = pour + contre
    minorite = min(pour, contre)
    majorite = max(pour, contre)
    part_min = minorite / exprimes if exprimes else 0.0
    marge = (majorite - minorite) / exprimes if exprimes else 1.0
    if part_min < QUASI_UNANIME:
        cls = 'quasi_unanime'
    elif part_min < DISCRIMINANT:
        cls = 'intermediaire'
    else:
        cls = 'discriminant'
    return {
        'dossier_uid': loi['dossier_uid'],
        'titre': loi['titre'],
        'procedure': loi['procedure'],
        'leg': loi['ref_leg'],
        'numero': loi['ref_numero'],
        'acte': loi['ref_acte'],
        'type': v['type'],
        'date': v['date'],
        'sort': v['sort'],
        'pour': pour, 'contre': contre, 'abst': abst, 'nonvotant': nonvot,
        'votants': votants, 'exprimes': exprimes,
        'part_votants': votants / SIEGES,
        'part_exprimes': exprimes / SIEGES,
        'minorite': minorite, 'majorite': majorite,
        'part_minorite': part_min,
        'marge_gagnante': marge,
        'classe': cls,
        'is_ratification': loi['is_ratification'],
    }


def group_congruence(scrutin, sort_loi):
    """Pour un scrutin, retourne {groupe_ref: (congruent_bool|None)}.
    Congruent = la position majoritaire (pour vs contre) du groupe == sens du sort.
    sort_loi adopté -> sens attendu 'pour' ; rejeté -> 'contre'. None si le groupe
    n'a ni pour ni contre (que abstention/nonvotant) -> indéfini."""
    sens_attendu = 'pour' if sort_loi == 'adopté' else 'contre'
    gp = defaultdict(lambda: Counter())
    for aref, pos, deleg, gref, cause in scrutin.positions_nominales():
        gp[gref][pos] += 1
    out = {}
    for gref, c in gp.items():
        p, co = c['pour'], c['contre']
        if p == 0 and co == 0:
            out[gref] = None
            continue
        maj_pos = 'pour' if p >= co else 'contre'
        out[gref] = (maj_pos == sens_attendu)
    return out


def main():
    corpus = load_corpus()
    lois = corpus['lois']
    sidx = anlib.load_all_scrutins()

    rows = []
    for loi in lois:
        s = sidx[(loi['ref_leg'], loi['ref_numero'])]
        rows.append(analyse_one(loi, s))

    # ---- agrégats par législature + global ----
    def block(subset, label):
        n = len(subset)
        if n == 0:
            return {'label': label, 'n': 0}
        votants = [r['votants'] for r in subset]
        exprimes = [r['exprimes'] for r in subset]
        part_vot = [r['part_votants'] for r in subset]
        part_exp = [r['part_exprimes'] for r in subset]
        part_min = [r['part_minorite'] for r in subset]
        marge = [r['marge_gagnante'] for r in subset]
        classes = Counter(r['classe'] for r in subset)
        n_qu = classes['quasi_unanime']
        n_int = classes['intermediaire']
        n_disc = classes['discriminant']
        adopte = sum(1 for r in subset if r['sort'] == 'adopté')
        rejete = sum(1 for r in subset if r['sort'] != 'adopté')
        return {
            'label': label,
            'n': n,
            'n_quasi_unanime': n_qu,
            'n_intermediaire': n_int,
            'n_discriminant': n_disc,
            'pct_quasi_unanime': round(pct(n_qu, n), 1),
            'pct_intermediaire': round(pct(n_int, n), 1),
            'pct_discriminant': round(pct(n_disc, n), 1),
            'n_adopte': adopte, 'n_rejete': rejete,
            'votants_median': statistics.median(votants),
            'votants_mean': round(statistics.mean(votants), 1),
            'exprimes_median': statistics.median(exprimes),
            'part_votants_median': round(statistics.median(part_vot), 4),
            'part_votants_mean': round(statistics.mean(part_vot), 4),
            'part_exprimes_median': round(statistics.median(part_exp), 4),
            'part_minorite_median': round(statistics.median(part_min), 4),
            'part_minorite_mean': round(statistics.mean(part_min), 4),
            'marge_gagnante_median': round(statistics.median(marge), 4),
            'marge_gagnante_mean': round(statistics.mean(marge), 4),
            'q_part_votants': {str(k): round(v, 4) for k, v in quantiles(part_vot).items()},
            'q_part_minorite': {str(k): round(v, 4) for k, v in quantiles(part_min).items()},
            'q_marge_gagnante': {str(k): round(v, 4) for k, v in quantiles(marge).items()},
        }

    leg16 = [r for r in rows if r['leg'] == 16]
    leg17 = [r for r in rows if r['leg'] == 17]
    blocks = {
        'global': block(rows, 'global'),
        'leg16': block(leg16, 'leg16'),
        'leg17': block(leg17, 'leg17'),
    }

    # ratifications often unanimous -> show with/without
    non_ratif = [r for r in rows if not r['is_ratification']]
    ratif = [r for r in rows if r['is_ratification']]
    blocks['global_sans_ratif'] = block(non_ratif, 'global_sans_ratif')
    blocks['ratifications'] = block(ratif, 'ratifications')

    # ---- histogramme marge gagnante ----
    edges = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0001]
    hist_marge = {
        'edges': edges,
        'global': histogram([r['marge_gagnante'] for r in rows], edges),
        'leg16': histogram([r['marge_gagnante'] for r in leg16], edges),
        'leg17': histogram([r['marge_gagnante'] for r in leg17], edges),
    }
    # histogramme part minorité
    hist_minorite = {
        'edges': edges,
        'global': histogram([r['part_minorite'] for r in rows], edges),
        'leg16': histogram([r['part_minorite'] for r in leg16], edges),
        'leg17': histogram([r['part_minorite'] for r in leg17], edges),
    }

    # ---- top 10 serrés / unanimes ----
    by_tight = sorted(rows, key=lambda r: (r['part_minorite'], -r['exprimes']), reverse=True)
    by_unanime = sorted(rows, key=lambda r: (r['part_minorite'], -r['exprimes']))

    def slim(r):
        return {
            'leg': r['leg'], 'numero': r['numero'], 'acte': r['acte'], 'type': r['type'],
            'date': r['date'], 'sort': r['sort'],
            'pour': r['pour'], 'contre': r['contre'], 'abst': r['abst'], 'nonvotant': r['nonvotant'],
            'exprimes': r['exprimes'], 'votants': r['votants'],
            'part_minorite': round(r['part_minorite'], 4),
            'marge_gagnante': round(r['marge_gagnante'], 4),
            'part_votants': round(r['part_votants'], 4),
            'classe': r['classe'],
            'titre': r['titre'],
        }

    top_tight = [slim(r) for r in by_tight[:10]]
    top_unanime = [slim(r) for r in by_unanime[:10]]

    # =====================================================================
    # REVEAL-FLATNESS : simulation du score de congruence par groupe
    # =====================================================================
    # Pour chaque sous-ensemble de votes, on calcule par groupe la part de votes
    # où le groupe est congruent avec le sort. Puis on regarde la DISPERSION
    # inter-groupes (écart max-min, écart-type). Faible dispersion => reveal plat.
    def congruence_simulation(subset, label):
        # groupes "majeurs" : on retient les groupes présents (avec un pour/contre)
        # sur >= 50% des votes du sous-ensemble pour éviter le bruit des micro-groupes.
        n = len(subset)
        if n == 0:
            return {'label': label, 'n': 0, 'groupes': {}}
        gpres = Counter()
        gcong = Counter()
        gtot_defini = Counter()
        for r in subset:
            s = sidx[(r['leg'], r['numero'])]
            cong = group_congruence(s, r['sort'])
            for gref, val in cong.items():
                gpres[gref] += 1
                if val is not None:
                    gtot_defini[gref] += 1
                    if val:
                        gcong[gref] += 1
        # garder groupes présents sur >=50% des votes
        majeurs = {g for g, c in gpres.items() if c >= 0.5 * n and gtot_defini[g] > 0}
        scores = {}
        for g in majeurs:
            scores[g] = gcong[g] / gtot_defini[g]
        vals = list(scores.values())
        if vals:
            spread = max(vals) - min(vals)
            stdev = statistics.pstdev(vals) if len(vals) > 1 else 0.0
            mean = statistics.mean(vals)
        else:
            spread = stdev = mean = 0.0
        return {
            'label': label, 'n': n,
            'n_groupes_majeurs': len(majeurs),
            'score_min': round(min(vals), 4) if vals else None,
            'score_max': round(max(vals), 4) if vals else None,
            'score_mean': round(mean, 4),
            'spread_max_min': round(spread, 4),
            'stdev_inter_groupes': round(stdev, 4),
            'scores_par_groupe': {g: round(v, 4) for g, v in sorted(scores.items(), key=lambda kv: -kv[1])},
        }

    # noms de groupes — leg17 depuis AMO10 (codes présents) ; leg16 absent du dump
    # (AMO10 = leg17 only, cf. SCHEMA-NOTES), donc labels dérivés des effectifs
    # (nombreMembresGroupe) recoupés avec la composition publique AN 2022-2024.
    groupe_names = {}
    import glob, os
    for path in glob.glob(os.path.join(anlib.DATA, 'amo10-17', 'json', 'organe', 'PO*.json')):
        try:
            with open(path, encoding='utf-8') as fh:
                o = json.load(fh).get('organe') or {}
            uid = o.get('uid')
            if uid:
                groupe_names[uid] = {
                    'libelle': o.get('libelle', ''),
                    'abrev': o.get('libelleAbrev', ''),
                }
        except Exception:
            pass
    # leg16 : labels dérivés (effectif max observé en ventilation). Les gros groupes
    # sont sans ambiguïté ; les petits (~22-31) marqués avec leur effectif comme garde-fou.
    # Identités confirmées par effectif + pattern de vote (ex. scrutin 3966 agri, 2024-05-28).
    # Les groupes intermittents/petits (PO800496, PO800532, PO830170) sont étiquetés
    # avec un drapeau de prudence : le dump leg16 des organes n'est pas publié.
    LEG16_GROUPS = {
        'PO800538': ('RE', 'Renaissance (~169-172, vote majorité)'),
        'PO800520': ('RN', 'Rassemblement National (~88-89)'),
        'PO800490': ('LFI-NUPES', 'La France insoumise-NUPES (~75)'),
        'PO800508': ('LR', 'Les Républicains (~61-62)'),
        'PO800484': ('DEM', 'Démocrate/MoDem (~50-51, vote majorité)'),
        'PO800514': ('HOR', 'Horizons & app. (~31, vote majorité)'),
        'PO800526': ('GDR', 'Gauche démocrate & rép. (~21-23, gauche)'),
        'PO800502': ('LIOT', 'Libertés Indép. O-mer Territ. (~22, centristes)'),
        # zone non certifiée (codes intermittents, dump leg16 organes absent) :
        'PO800496': ('SOC?', 'Socialistes? (~31, présent 74/93)'),
        'PO830170': ('ECOLO?', 'Écologiste? (~31, présent 19/93, gauche)'),
        'PO800532': ('GAUCHE?~22', 'groupe gauche ~22 (présent 93/93, non certifié)'),
        'PO793087': ('NI', 'Non-inscrits (~7-9)'),
    }
    for uid, (ab, lib) in LEG16_GROUPS.items():
        groupe_names.setdefault(uid, {'libelle': lib, 'abrev': ab})
    # leg17 : code transitoire absent d'AMO10 (groupe éphémère, ~16 membres, nov24->juil25)
    groupe_names.setdefault('PO847173', {'libelle': 'groupe droite éphémère leg17 (~16, non certifié)',
                                         'abrev': 'UDR?~16'})

    def name_scores(sim):
        named = {}
        for g, v in sim.get('scores_par_groupe', {}).items():
            nm = groupe_names.get(g, {})
            label = nm.get('abrev') or nm.get('libelle') or g
            named[f"{label} ({g})"] = v
        return named

    reveal = {}
    # global congruence: les votes de réf sont presque tous adoptés, mais la simulation
    # mesure quand même la dispersion inter-groupes par sous-ensemble.
    for key, sub in (('quasi_unanime_global', [r for r in rows if r['classe'] == 'quasi_unanime']),
                     ('discriminant_global', [r for r in rows if r['classe'] == 'discriminant']),
                     ('quasi_unanime_leg16', [r for r in leg16 if r['classe'] == 'quasi_unanime']),
                     ('discriminant_leg16', [r for r in leg16 if r['classe'] == 'discriminant']),
                     ('quasi_unanime_leg17', [r for r in leg17 if r['classe'] == 'quasi_unanime']),
                     ('discriminant_leg17', [r for r in leg17 if r['classe'] == 'discriminant']),
                     ('tous_leg16', leg16),
                     ('tous_leg17', leg17),
                     ('tous_global', rows)):
        sim = congruence_simulation(sub, key)
        sim['scores_nommes'] = name_scores(sim)
        reveal[key] = sim

    # ---- couverture AMO10 : trou des acteurRef absents du dump acteurs ----
    acteurs = set()
    for path in glob.glob(os.path.join(anlib.DATA, 'amo10-17', 'json', 'acteur', 'PA*.json')):
        acteurs.add(os.path.basename(path).replace('.json', ''))
    seen_refs = set()
    missing_refs = set()
    for r in rows:
        s = sidx[(r['leg'], r['numero'])]
        for aref, pos, deleg, gref, cause in s.positions_nominales():
            if aref:
                seen_refs.add(aref)
                if aref not in acteurs:
                    missing_refs.add(aref)
    couverture = {
        'acteurs_amo10': len(acteurs),
        'acteurs_distincts_dans_votes_ref': len(seen_refs),
        'acteurs_votes_ref_absents_amo10': len(missing_refs),
        'pct_absents': round(pct(len(missing_refs), len(seen_refs)), 2),
        'note': 'Trou AMO10 = députés partis (ministres, démissions, partielles). '
                'Sans impact sur cette analyse car on agrège par groupe AU MOMENT DU VOTE '
                '(positions_nominales fournit groupe_ref), pas via le dump acteurs.',
    }

    # ---------------------------------------------------------------------
    # Sortie JSON machine
    # ---------------------------------------------------------------------
    result = {
        'meta': {
            'n_lois': len(rows),
            'definitions': {
                'votants': 'pour+contre+abst (nb_votants AN, abstention=present)',
                'exprimes': 'pour+contre (suffrages_exprimes AN, abst exclue)',
                'part_minorite': 'min(pour,contre)/exprimes',
                'marge_gagnante': '|pour-contre|/exprimes',
                'quasi_unanime': f'part_minorite < {QUASI_UNANIME}',
                'discriminant': f'part_minorite >= {DISCRIMINANT}',
                'sieges_an': SIEGES,
            },
        },
        'blocks': blocks,
        'hist_marge_gagnante': hist_marge,
        'hist_part_minorite': hist_minorite,
        'top_10_serres': top_tight,
        'top_10_unanimes': top_unanime,
        'reveal_flatness': reveal,
        'couverture_amo10': couverture,
        'rows': rows,
    }
    with open(OUT_JSON, 'w', encoding='utf-8') as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)

    # ---------------------------------------------------------------------
    # Rapport markdown
    # ---------------------------------------------------------------------
    write_markdown(result, groupe_names)

    # résumé console
    g = blocks['global']
    print(f"n={g['n']}  quasi-unanimes={g['n_quasi_unanime']} ({g['pct_quasi_unanime']}%)  "
          f"discriminants={g['n_discriminant']} ({g['pct_discriminant']}%)")
    print(f"part_minorite mediane={g['part_minorite_median']}  "
          f"marge mediane={g['marge_gagnante_median']}  "
          f"votants mediane={g['votants_median']} ({round(100*g['part_votants_median'],1)}% des 577)")
    print(f"reveal flat (quasi-unanime global): spread inter-groupes="
          f"{reveal['quasi_unanime_global']['spread_max_min']}  "
          f"vs discriminant={reveal['discriminant_global']['spread_max_min']}")
    return result


def bar(n, scale):
    return '#' * int(round(n / scale)) if scale else ''


def write_markdown(res, groupe_names):
    b = res['blocks']
    g, g16, g17 = b['global'], b['leg16'], b['leg17']
    rev = res['reveal_flatness']
    L = []
    A = L.append
    A('# Q2 — Participation & polarisation des votes de référence')
    A('')
    A('**Mandat :** tester le §4 de la revue — le « reveal plat » (risque épistémique n°1). '
      'Si une grande part des 159 votes de référence sont quasi-unanimes, un score de '
      'congruence calculé dessus rendra ~la même valeur pour TOUS les groupes : un reveal '
      'qui n\'apprend rien. On le mesure.')
    A('')
    A(f"Corpus : **{res['meta']['n_lois']} votes de référence** (1 par loi promulguée jugeable), "
      f"leg 16 = {g16['n']}, leg 17 = {g17['n']}. Source : `out/corpus.json` (figé).")
    A('')
    A('## TL;DR — le verdict')
    A('')
    pq = g['pct_quasi_unanime']
    A(f"- **{g['n_quasi_unanime']}/{g['n']} votes de référence ({pq}%) sont quasi-unanimes** "
      f"(minorité < 10% des exprimés). Seulement **{g['n_discriminant']} ({g['pct_discriminant']}%) "
      f"sont discriminants** (minorité ≥ 20%).")
    A(f"- Marge gagnante médiane = **{g['marge_gagnante_median']:.3f}** "
      f"(|pour−contre|/exprimés). Part minorité médiane = **{g['part_minorite_median']:.3f}**.")
    A(f"- Participation médiane = **{int(g['votants_median'])} votants/577** "
      f"({100*g['part_votants_median']:.1f}%) ; exprimés médian = **{int(g['exprimes_median'])}/577** "
      f"({100*g['part_exprimes_median']:.1f}%).")
    qsim = rev['quasi_unanime_global']
    dsim = rev['discriminant_global']
    tsim = rev['tous_global']
    tvals = list(tsim.get('scores_par_groupe', {}).values())
    n_high = sum(1 for v in tvals if v >= 0.80)
    A(f"- **La prédiction du §4 se vérifie au chiffre près** : un score de congruence calculé "
      f"sur les **159 votes de réf** donne une moyenne inter-groupes de **{tsim['score_mean']:.2f}** "
      f"avec **{n_high}/{len(tvals)} groupes au-dessus de 80%** (et {sum(1 for v in tvals if v>=0.60)}/{len(tvals)} "
      f"au-dessus de 60%). Tout le monde « congrue » à ~80% : reveal qui n'apprend rien.")
    A(f"- **Pourquoi : c'est mécanique.** Sur les votes quasi-unanimes l'écart de score entre "
      f"groupes majeurs n'est que de **{qsim['spread_max_min']:.3f}** "
      f"(min {qsim['score_min']}, max {qsim['score_max']} — tous collés). Sur les discriminants "
      f"il explose à **{dsim['spread_max_min']:.3f}** (min {dsim['score_min']}, max {dsim['score_max']}). "
      f"Comme la moitié des votes de réf sont quasi-unanimes, ils noient le signal des discriminants.")
    A('')
    A('> **Implication produit :** un score de congruence agrégé sur les 159 votes de référence '
      'donnera ~80-95% pour quasi tous les groupes et n\'aura aucun pouvoir discriminant. '
      f'Le signal exploitable se concentre sur les **{g["n_discriminant"]} votes discriminants** '
      '(et un peu sur les intermédiaires). Il faut pondérer/filtrer par polarisation, sinon le '
      'reveal est cosmétique.')
    A('')

    # --- Tableau classes ---
    A('## 1. Distribution de la polarisation (classes)')
    A('')
    A('Classe selon la part de la minorité dans les exprimés : '
      'quasi-unanime `< 10%`, intermédiaire `[10%, 20%)`, discriminant `≥ 20%`.')
    A('')
    A('| Périmètre | n | quasi-unanime | intermédiaire | discriminant |')
    A('|---|--:|--:|--:|--:|')
    for blk in (g, g16, g17, b['global_sans_ratif'], b['ratifications']):
        if blk['n'] == 0:
            continue
        A(f"| {blk['label']} | {blk['n']} | "
          f"{blk['n_quasi_unanime']} ({blk['pct_quasi_unanime']}%) | "
          f"{blk['n_intermediaire']} ({blk['pct_intermediaire']}%) | "
          f"{blk['n_discriminant']} ({blk['pct_discriminant']}%) |")
    A('')
    A(f"Lecture : leg 16 (close) = **{g16['pct_quasi_unanime']}%** quasi-unanimes vs "
      f"leg 17 (en cours) = **{g17['pct_quasi_unanime']}%**. "
      f"Les {b['ratifications']['n']} ratifications sont quasi-unanimes à "
      f"{b['ratifications']['pct_quasi_unanime']}% — elles gonflent mécaniquement le taux.")
    A('')

    # --- Participation ---
    A('## 2. Participation')
    A('')
    A('`votants` = pour+contre+abst (présents qui votent) ; `exprimés` = pour+contre. '
      'Dénominateur = 577 sièges.')
    A('')
    A('| Périmètre | votants médian | % 577 | votants moyen | exprimés médian | % 577 |')
    A('|---|--:|--:|--:|--:|--:|')
    for blk in (g, g16, g17):
        A(f"| {blk['label']} | {int(blk['votants_median'])} | "
          f"{100*blk['part_votants_median']:.1f}% | {blk['votants_mean']:.0f} | "
          f"{int(blk['exprimes_median'])} | {100*blk['part_exprimes_median']:.1f}% |")
    A('')
    A('Quantiles de la participation (`votants/577`) :')
    A('')
    A('| Périmètre | p0 | p10 | p25 | p50 | p75 | p90 | p100 |')
    A('|---|--:|--:|--:|--:|--:|--:|--:|')
    for blk in (g, g16, g17):
        q = blk['q_part_votants']
        A(f"| {blk['label']} | " + " | ".join(f"{100*q[str(k)]:.0f}%" for k in (0, 10, 25, 50, 75, 90, 100)) + " |")
    A('')
    A('Participation très variable : de quelques dizaines de votants (textes consensuels '
      'votés en séance creuse) à >500 (scrutins solennels mobilisés).')
    A('')

    # --- Histogramme marge ---
    A('## 3. Histogramme de la marge gagnante')
    A('')
    A('Marge gagnante = `|pour − contre| / exprimés`. **1.0 = unanime**, **0.0 = 50/50 parfait**. '
      'Bins de largeur 0.1.')
    A('')
    hm = res['hist_marge_gagnante']
    edges = hm['edges']
    A('| bin marge | global | leg16 | leg17 |          |')
    A('|---|--:|--:|--:|---|')
    mx = max(hm['global']) or 1
    for i in range(len(edges) - 1):
        lab = f"[{edges[i]:.1f}, {edges[i+1] if edges[i+1]<=1 else 1.0:.1f}{']' if i==len(edges)-2 else ')'}"
        A(f"| {lab} | {hm['global'][i]} | {hm['leg16'][i]} | {hm['leg17'][i]} | "
          f"{bar(hm['global'][i], mx/40)} |")
    A('')
    A('La masse est écrasée vers la droite (marge ≥ 0.8) : la grande majorité des lois '
      'promulguées passent par des votes larges. Le bas du spectre (marge < 0.2, votes serrés) '
      'est clairsemé.')
    A('')
    A('Histogramme de la part de la minorité (`min(pour,contre)/exprimés`, miroir) :')
    A('')
    hp = res['hist_part_minorite']
    A('| bin part minorité | global | leg16 | leg17 |          |')
    A('|---|--:|--:|--:|---|')
    mxp = max(hp['global']) or 1
    for i in range(len(edges) - 1):
        lab = f"[{edges[i]:.1f}, {edges[i+1] if edges[i+1]<=1 else 1.0:.1f}{']' if i==len(edges)-2 else ')'}"
        A(f"| {lab} | {hp['global'][i]} | {hp['leg16'][i]} | {hp['leg17'][i]} | "
          f"{bar(hp['global'][i], mxp/40)} |")
    A('')

    # --- Reveal flatness ---
    A('## 4. Test du « reveal plat » (le cœur du §4)')
    A('')
    A('Pour chaque vote, on calcule par groupe un **score de congruence binaire** : la position '
      'majoritaire du groupe (pour vs contre) coïncide-t-elle avec le sort de la loi '
      '(adopté→pour attendu, rejeté→contre attendu) ? On agrège par groupe (part de votes '
      'congruents) puis on mesure la **dispersion inter-groupes**. Groupes « majeurs » = '
      'présents avec un pour/contre sur ≥ 50% des votes du sous-ensemble.')
    A('')
    A('| Sous-ensemble | n votes | groupes majeurs | score min | score max | **spread (max−min)** | écart-type |')
    A('|---|--:|--:|--:|--:|--:|--:|')
    order = ['quasi_unanime_global', 'discriminant_global', 'tous_global',
             'quasi_unanime_leg16', 'discriminant_leg16', 'tous_leg16',
             'quasi_unanime_leg17', 'discriminant_leg17', 'tous_leg17']
    for k in order:
        s = rev[k]
        if s['n'] == 0:
            A(f"| {k} | 0 | – | – | – | – | – |")
            continue
        A(f"| {k} | {s['n']} | {s['n_groupes_majeurs']} | {s['score_min']} | {s['score_max']} | "
          f"**{s['spread_max_min']}** | {s['stdev_inter_groupes']} |")
    A('')
    A('**Lecture décisive :** sur les votes quasi-unanimes le spread inter-groupes est ~quasi nul '
      f"(global {rev['quasi_unanime_global']['spread_max_min']}), c.-à-d. tous les groupes scorent "
      f"pareil — le reveal n'apprend rien. Sur les votes discriminants le spread explose "
      f"(global {rev['discriminant_global']['spread_max_min']}) : c'est là, et seulement là, "
      f"que les groupes se séparent. Comme {g['pct_quasi_unanime']}% des votes de réf sont "
      f"quasi-unanimes, le score agrégé brut est dominé par du bruit unanime.")
    A('')
    A('Scores de congruence par groupe, **par législature** (les codes de groupe diffèrent '
      'entre leg16 `PO8005xx` et leg17 `PO845xxx` ; on ne les mélange pas). '
      'On compare DISCRIMINANT (signal) vs QUASI-UNANIME (bruit).')
    A('')
    A('### Leg 16')
    A('')
    A('DISCRIMINANT — là où les groupes se séparent :')
    A('')
    for label, val in rev['discriminant_leg16'].get('scores_nommes', {}).items():
        A(f"- {label} : **{val:.3f}**")
    A('')
    A('QUASI-UNANIME — tous collés en haut (reveal plat) :')
    A('')
    for label, val in rev['quasi_unanime_leg16'].get('scores_nommes', {}).items():
        A(f"- {label} : {val:.3f}")
    A('')
    A('### Leg 17')
    A('')
    A('DISCRIMINANT :')
    A('')
    for label, val in rev['discriminant_leg17'].get('scores_nommes', {}).items():
        A(f"- {label} : **{val:.3f}**")
    A('')
    A('QUASI-UNANIME :')
    A('')
    for label, val in rev['quasi_unanime_leg17'].get('scores_nommes', {}).items():
        A(f"- {label} : {val:.3f}")
    A('')

    # --- Top serrés ---
    A('## 5. Les 10 votes de référence les plus serrés')
    A('')
    A('| # | leg | scrutin | type | date | sort | pour | contre | abst | exprimés | part minorité | titre |')
    A('|--:|--:|--:|---|---|---|--:|--:|--:|--:|--:|---|')
    for i, r in enumerate(res['top_10_serres'], 1):
        t = r['titre'].replace('|', '/')
        t = (t[:70] + '…') if len(t) > 70 else t
        A(f"| {i} | {r['leg']} | {r['numero']} | {r['type']} | {r['date']} | {r['sort']} | "
          f"{r['pour']} | {r['contre']} | {r['abst']} | {r['exprimes']} | "
          f"{100*r['part_minorite']:.1f}% | {t} |")
    A('')

    # --- Top unanimes ---
    A('## 6. Les 10 votes de référence les plus unanimes')
    A('')
    A('| # | leg | scrutin | type | date | pour | contre | abst | exprimés | part minorité | titre |')
    A('|--:|--:|--:|---|---|--:|--:|--:|--:|--:|---|')
    for i, r in enumerate(res['top_10_unanimes'], 1):
        t = r['titre'].replace('|', '/')
        t = (t[:70] + '…') if len(t) > 70 else t
        A(f"| {i} | {r['leg']} | {r['numero']} | {r['type']} | {r['date']} | "
          f"{r['pour']} | {r['contre']} | {r['abst']} | {r['exprimes']} | "
          f"{100*r['part_minorite']:.1f}% | {t} |")
    A('')

    # --- limites ---
    A('## 7. Limites & honnêteté méthodo')
    A('')
    cov = res['couverture_amo10']
    A(f"- **Couverture AMO10 :** {cov['acteurs_votes_ref_absents_amo10']} acteurRef présents dans "
      f"les votes de réf ne sont pas dans le dump acteurs ({cov['pct_absents']}% des "
      f"{cov['acteurs_distincts_dans_votes_ref']} distincts). Sans impact ici : l'agrégation se "
      f"fait par `groupe_ref` (groupe au moment du vote, fourni par `positions_nominales`), pas via "
      f"le dump acteurs.")
    A('- **leg 17 en cours :** corpus partiel, susceptible d\'évoluer. Comparaison leg16/leg17 à '
      'lire avec prudence (volumes 93 vs 66).')
    A('- **Score de congruence simulé** = proxy binaire (position majoritaire du groupe vs sort). '
      'Le vrai produit pourra pondérer par taille de groupe ou compter au nominatif ; mais la '
      'conclusion de platitude tient quel que soit le raffinement, car elle vient de la '
      'distribution des votes eux-mêmes (unanimité massive), pas du choix de métrique.')
    A('- **Ratifications :** très consensuelles par nature ; les isoler change peu le verdict '
      'global mais documenté ci-dessus.')
    A('- **Marge sur exprimés** : exclut abstentions et non-votants du dénominateur (choix AN). '
      'Si on rapportait la minorité aux 577 sièges, les marges seraient encore plus écrasées.')
    A('')

    with open(OUT_MD, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L) + '\n')


if __name__ == '__main__':
    main()
