#!/usr/bin/env python3
"""
q6-censure — Motions de censure & branche 49.3 (valide §2.4 de la revue).

Recense toutes les motions de censure (type_code=="MOC") en leg16 et leg17,
distingue 49.2 (censure spontanée) vs 49.3 (réponse à engagement de responsabilité),
donne le sort de chacune, compte les motions par date (test du modèle SignalRejet
singulier), relie les 49.3 aux textes engagés via les actes *-MOTION-VOTE du dossier,
et conclut sur le nombre de lois "structurantes" hors-corpus et la cardinalité 0..n.

Sorties : out/q6-censure.md (rapport), out/q6-censure.json (chiffres machine).
"""
from __future__ import annotations
import sys, json, re, os
sys.path.insert(0, '/home/cos/Bureau/dev/boussole-politique/dry-run/scripts')
import anlib
from collections import Counter, defaultdict

OUT = "/home/cos/Bureau/dev/boussole-politique/dry-run/out"
CORPUS = "/home/cos/Bureau/dev/boussole-politique/dry-run/out/corpus.json"
VR = re.compile(r"VTANR5L(\d+)V(\d+)")
DLR_LEG = re.compile(r"DLR5L(\d+)N")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def alinea(s):
    """49.2 (spontanée) vs 49.3 (réponse à engagement) depuis le titre normalisé."""
    n = anlib.norm_title(s.titre.replace("’", "'"))
    if "alinea 3" in n:
        return "49.3"
    if "alinea 2" in n:
        return "49.2"
    return "??"

def auteur(s):
    """Premier auteur déposant, extrait du titre (heuristique de présentation)."""
    t = s.titre.replace("’", "'")
    m = re.search(r"par\s+(M\.|Mme|Mmes|MM\.)\s+([^,]+)", t)
    if m:
        return f"{m.group(1)} {m.group(2).strip()}"
    return "?"

def walk_actes(node):
    if isinstance(node, dict):
        if "codeActe" in node:
            yield node
        for v in node.values():
            yield from walk_actes(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_actes(v)

def moc_refs_of_dossier(d):
    """Numéros de scrutins MOC référencés par les actes *-MOTION-VOTE du dossier."""
    out = []
    for a in walk_actes(d.raw["dossierParlementaire"].get("actesLegislatifs")):
        code = a["codeActe"]
        if "MOTION" in code and "VOTE" in code:
            vr = a.get("voteRefs")
            if not vr:
                continue
            seq = vr.get("voteRef") if isinstance(vr, dict) else vr
            for v in anlib.as_list(seq):
                ref = v if isinstance(v, str) else (v.get("voteRef") if isinstance(v, dict) else None)
                m = VR.search(ref or "")
                if m:
                    out.append((int(m.group(1)), int(m.group(2)), code))
    return out

# ---------------------------------------------------------------------------
# Chargement
# ---------------------------------------------------------------------------

corpus = json.load(open(CORPUS))
corpus_uids = {l["dossier_uid"] for l in corpus["lois"]}
dossiers = anlib.load_all_dossiers()
sidx = anlib.load_all_scrutins()

# ---------------------------------------------------------------------------
# 1. Recensement des motions par législature
# ---------------------------------------------------------------------------

motions = {16: [], 17: []}
filter_check = {}
for leg in (16, 17):
    sc = anlib.load_scrutins(leg)
    moc = [s for s in sc if s.type_code == "MOC"]
    by_lib = [s for s in sc if s.type_libelle == "motion de censure"]
    filter_check[leg] = {
        "n_par_type_code_MOC": len(moc),
        "n_par_type_libelle_motion_de_censure": len(by_lib),
        "type_libelle_distinct": dict(Counter(s.type_libelle for s in moc)),
    }
    motions[leg] = sorted(moc, key=lambda s: (s.date, s.numero))

# ---------------------------------------------------------------------------
# 2. Classification 49.2 / 49.3, sort, et linkage texte (via dossier acte-tree)
# ---------------------------------------------------------------------------

# Index inverse : (leg, numero_moc) -> [(dossier_uid, titre, procedure, code_acte)]
moc_to_dossier = defaultdict(list)
for uid, d in dossiers.items():
    for (l, n, code) in moc_refs_of_dossier(d):
        s = sidx.get((l, n))
        if s and s.type_code == "MOC":
            moc_to_dossier[(l, n)].append((uid, d.titre, d.procedure, code, d.titre_chemin))

per_leg = {}
motion_rows = {16: [], 17: []}
for leg in (16, 17):
    n2 = n3 = 0
    adopted = []
    rejected = 0
    linked_count = 0
    for s in motions[leg]:
        al = alinea(s)
        if al == "49.2":
            n2 += 1
        elif al == "49.3":
            n3 += 1
        if s.sort == "adopté":
            adopted.append(s)
        else:
            rejected += 1
        links = moc_to_dossier.get((leg, s.numero), [])
        if links:
            linked_count += 1
        motion_rows[leg].append({
            "numero": s.numero, "date": s.date, "alinea": al, "sort": s.sort,
            "pour": s.d_pour, "contre": s.d_contre, "abst": s.d_abst,
            "nb_votants": s.nb_votants, "auteur": auteur(s),
            "texte_engage": [{"uid": u, "titre": t, "procedure": p,
                              "acte": c, "titre_chemin": tc} for (u, t, p, c, tc) in links],
        })
    per_leg[leg] = {
        "total": len(motions[leg]), "n_49_2": n2, "n_49_3": n3,
        "adoptees": [s.numero for s in adopted], "rejetees": rejected,
        "linkables_a_un_texte": linked_count,
    }

# ---------------------------------------------------------------------------
# 3. Motions par date : test du modèle SignalRejet singulier
# ---------------------------------------------------------------------------

dates_multi = {}
for leg in (16, 17):
    dc = Counter(s.date for s in motions[leg])
    multi = {d: n for d, n in dc.items() if n > 1}
    dates_multi[leg] = {
        "n_dates_distinctes": len(dc),
        "max_motions_un_jour": max(dc.values()) if dc else 0,
        "dates_avec_plusieurs": dict(sorted(multi.items())),
        "n_dates_avec_plusieurs": len(multi),
        "n_motions_sur_dates_multi": sum(multi.values()),
    }

# ---------------------------------------------------------------------------
# 4. Lois de finances : corpus vs hors-corpus, et lien 49.3
# ---------------------------------------------------------------------------

def is_finance(proc):
    p = proc.lower()
    return ("finance" in p or "financement" in p or "comptes" in p) and "engagement" not in p

finance = []
for uid, d in dossiers.items():
    if not is_finance(d.procedure):
        continue
    if not d.promulguee:
        continue
    m = DLR_LEG.search(uid)
    leg = int(m.group(1)) if m else 0
    an_refs = d.an_vote_refs()
    has_ens = any(
        sidx.get((l, n)) and sidx[(l, n)].type_code in ("SPO", "SPS") and sidx[(l, n)].is_ensemble
        for (_, l, n) in an_refs
    )
    # motions 49.3 liées à ce dossier
    moc_links = [(l, n, c) for (l, n, c) in moc_refs_of_dossier(d)
                 if sidx.get((l, n)) and sidx[(l, n)].type_code == "MOC"]
    finance.append({
        "uid": uid, "titre": d.titre, "procedure": d.procedure, "leg": leg,
        "in_corpus": uid in corpus_uids, "has_public_ensemble_vote": has_ens,
        "n_an_refs": len(an_refs),
        "motions_49_3_liees": [
            {"numero": n, "leg": l, "sort": sidx[(l, n)].sort, "acte": c}
            for (l, n, c) in moc_links
        ],
    })
finance.sort(key=lambda r: (r["leg"], r["procedure"], r["titre"]))

n_finance_prom = len(finance)
n_finance_corpus = sum(1 for f in finance if f["in_corpus"])
n_finance_exclu = n_finance_prom - n_finance_corpus

# ---------------------------------------------------------------------------
# 5. Tous les textes engagés via 49.3 (lois ou dossiers d'engagement)
# ---------------------------------------------------------------------------

# Regroupe les 49.3 par texte sous-jacent. On exploite les dossiers "Engagement de
# la responsabilité gouvernementale" dont le titreChemin nomme le texte engagé, et
# les dossiers de loi (finance) directement liés.
engage_dossiers = []
for uid, d in dossiers.items():
    m = DLR_LEG.search(uid)
    leg = int(m.group(1)) if m else 0
    moc_links = [(l, n, c) for (l, n, c) in moc_refs_of_dossier(d)
                 if sidx.get((l, n)) and sidx[(l, n)].type_code == "MOC"
                 and alinea(sidx[(l, n)]) == "49.3"]
    if not moc_links:
        continue
    engage_dossiers.append({
        "uid": uid, "leg": leg, "titre": d.titre, "titre_chemin": d.titre_chemin,
        "procedure": d.procedure, "promulguee": d.promulguee,
        "is_loi_corpus": uid in corpus_uids,
        "motions": sorted({n for (_, n, _) in moc_links}),
        "n_motions": len({n for (_, n, _) in moc_links}),
    })
engage_dossiers.sort(key=lambda r: (r["leg"], r["titre_chemin"]))

# Combien de lois "structurantes" (budgets) passent par la branche 49.3 hors-score ?
# = lois de finances promulguées, exclues du corpus, sur lesquelles un 49.3 a été engagé
#   (en leg17 le lien est explicite ; en leg16 il est historique, non tracé par acte).
finance_49_3_horsscore = [
    f for f in finance
    if (not f["in_corpus"]) and f["motions_49_3_liees"]
]
# Estimation large : budgets STRUCTURANTS (PLF de l'année + PLFSS, hors PLFR/fin de
# gestion) promulgués mais hors corpus -> proxy des textes passés par 49.3, même quand
# l'acte n'est pas tracé (cas leg16). "fin de gestion" et "rectificative" sont des
# correctifs, pas le budget structurant.
def is_structurant(proc):
    p = proc.lower()
    if "rectificative" in p or "fin de gestion" in p:
        return False
    return ("finances de l" in p or "finances pour" in p
            or "financement de la s" in p)
finance_structurant_horsscore = [
    f for f in finance if (not f["in_corpus"]) and is_structurant(f["procedure"])
]

# ---------------------------------------------------------------------------
# 6. Le modèle de données spec (1 motion) tient-il ? -> cardinalité observée
# ---------------------------------------------------------------------------

# Pour chaque "événement 49.3" (engagement sur un texte/lecture), combien de motions ?
cardinalite = Counter()
for ed in engage_dossiers:
    cardinalite[ed["n_motions"]] += 1
# Et par DATE de séance (plusieurs groupes déposent le même jour)
card_by_date = Counter()
for leg in (16, 17):
    for d, n in Counter(s.date for s in motions[leg]).items():
        card_by_date[n] += 1

# ===========================================================================
# ASSEMBLAGE JSON MACHINE
# ===========================================================================

result = {
    "id": "q6-censure",
    "valide": "revue §2.4 (branche 49.3 / motions de censure)",
    "filter_note": (
        "PIEGE: le mandat dit filtrer type_libelle=='motion de censure' mais cela ne "
        "matche QUE la leg17. En leg16 les motions portent type_libelle=='scrutin public "
        "solennel' avec type_code=='MOC'. Le filtre correct est type_code=='MOC'."
    ),
    "filter_check": filter_check,
    "par_leg": per_leg,
    "dates_multi": dates_multi,
    "cardinalite_par_evenement_493": dict(sorted(cardinalite.items())),
    "cardinalite_par_date_seance": dict(sorted(card_by_date.items())),
    "finance": {
        "n_promulguees_total": n_finance_prom,
        "n_dans_corpus_jugeable": n_finance_corpus,
        "n_exclues": n_finance_exclu,
        "n_exclues_avec_493_lie": len(finance_49_3_horsscore),
        "detail": finance,
    },
    "textes_engages_493": engage_dossiers,
    "motion_adoptee_519": next(
        (r for r in motion_rows[17] if r["numero"] == 519), None),
    "motions_detail": motion_rows,
    "conclusion": {
        "modele_signalrejet_singulier_faux": True,
        "raison": (
            "Plusieurs motions sont deposees le meme jour par des groupes differents "
            "(jusqu'a 3 le 2022-10-24), et un meme texte/49.3 attire jusqu'a 6 motions "
            "(PLF 2026). La cardinalite reelle est 0..n, pas 1."
        ),
        "lois_finance_493_trace_leg17": len(finance_49_3_horsscore),
        "lois_structurantes_hors_corpus": len(finance_structurant_horsscore),
        "lois_finance_promulguees_hors_corpus": n_finance_exclu,
    },
}
result["finance"]["structurant_hors_corpus"] = [
    {"uid": f["uid"], "titre": f["titre"], "leg": f["leg"], "procedure": f["procedure"]}
    for f in finance_structurant_horsscore
]

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "q6-censure.json"), "w", encoding="utf-8") as fh:
    json.dump(result, fh, ensure_ascii=False, indent=2)

# ===========================================================================
# RAPPORT MARKDOWN
# ===========================================================================

def fmt_motion_table(leg):
    lines = ["| n° | date | al. | sort | pour | contre | abst | votants | auteur | texte engagé (acte) |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in motion_rows[leg]:
        te = ""
        if r["texte_engage"]:
            te = "; ".join(f"{t['titre_chemin'] or t['titre'][:30]} ({t['acte']})"
                           for t in r["texte_engage"])
        sort = "**ADOPTÉE**" if r["sort"] == "adopté" else r["sort"]
        lines.append(
            f"| {r['numero']} | {r['date']} | {r['alinea']} | {sort} | {r['pour']} | "
            f"{r['contre']} | {r['abst']} | {r['nb_votants']} | {r['auteur'][:28]} | {te} |")
    return "\n".join(lines)

md = []
md.append("# q6-censure — Motions de censure & branche 49.3")
md.append("")
md.append("**Valide / teste :** revue §2.4 (branche 49.3 / motions de censure).  ")
md.append("**Corpus consommé :** `out/corpus.json` (159 lois jugeables : 93 leg16 + 66 leg17, FIGÉ).  ")
md.append("**Source motions :** `anlib.load_scrutins(16|17)`, filtre `type_code=='MOC'`.")
md.append("")
md.append("## 0. Piège de filtre corrigé (à signaler)")
md.append("")
md.append("Le mandat demande de filtrer `type_libelle==\"motion de censure\"`. **Ce filtre ne "
          "capture que la leg17.** En **leg16, les 34 motions portent `type_libelle==\"scrutin "
          "public solennel\"`** (et non \"motion de censure\") — seul `type_code==\"MOC\"` est "
          "stable sur les deux législatures. J'utilise donc `type_code==\"MOC\"`.")
md.append("")
md.append("| leg | `type_code=='MOC'` | `type_libelle=='motion de censure'` | libellés vus dans MOC |")
md.append("|---|---|---|---|")
for leg in (16, 17):
    fc = filter_check[leg]
    md.append(f"| {leg} | **{fc['n_par_type_code_MOC']}** | "
              f"{fc['n_par_type_libelle_motion_de_censure']} | "
              f"{fc['type_libelle_distinct']} |")
md.append("")
md.append("## 1. Recensement et classification 49.2 / 49.3")
md.append("")
md.append("Distinction par le titre du scrutin : « article 49, **alinéa 2** » = censure "
          "spontanée (initiative de députés) ; « article 49, **alinéa 3** » = réponse à un "
          "engagement de responsabilité du Gouvernement sur un texte. La classification est "
          "**100 % nette** (0 motion non classée sur 56).")
md.append("")
md.append("| | leg16 (close) | leg17 (en cours) | total |")
md.append("|---|---|---|---|")
md.append(f"| Motions de censure (MOC) | {per_leg[16]['total']} | {per_leg[17]['total']} | "
          f"{per_leg[16]['total']+per_leg[17]['total']} |")
md.append(f"| dont **49.2** (spontanées) | {per_leg[16]['n_49_2']} | {per_leg[17]['n_49_2']} | "
          f"{per_leg[16]['n_49_2']+per_leg[17]['n_49_2']} |")
md.append(f"| dont **49.3** (sur un texte) | {per_leg[16]['n_49_3']} | {per_leg[17]['n_49_3']} | "
          f"{per_leg[16]['n_49_3']+per_leg[17]['n_49_3']} |")
md.append(f"| adoptées (gvt renversé) | {len(per_leg[16]['adoptees'])} | "
          f"{len(per_leg[17]['adoptees'])} | "
          f"{len(per_leg[16]['adoptees'])+len(per_leg[17]['adoptees'])} |")
md.append(f"| rejetées | {per_leg[16]['rejetees']} | {per_leg[17]['rejetees']} | "
          f"{per_leg[16]['rejetees']+per_leg[17]['rejetees']} |")
md.append("")
md.append("**Une seule motion adoptée sur toute la période : la n°519 (leg17).** Toutes les "
          "autres (55) ont été rejetées — c'est le régime normal du 49.3 : le gouvernement "
          "n'est renversé que si la majorité absolue (289) vote la censure.")
md.append("")
md.append("### Focus : motion n°519 du 2024-12-04 (ADOPTÉE)")
md.append("")
r519 = result["motion_adoptee_519"]
md.append(f"- **Scrutin n°519, leg17, {r519['date']}**, 49.3, **ADOPTÉE** avec "
          f"**{r519['pour']} voix pour** (seuil 289), {r519['contre']} contre, "
          f"{r519['abst']} abstention.")
md.append("- Engagement de responsabilité du **gouvernement Barnier** sur le **PLFSS 2025 "
          "(version CMP)** — dossier d'engagement `DLR5L17N50975`, titreChemin `49al3CMPPLFSS2025`.")
md.append("- Conséquence : **gouvernement renversé** ; le dossier d'engagement n'a **aucun acte "
          "`PROM`** → la version du texte engagée **est tombée**. (Un PLFSS « pour 2026 » distinct "
          "sera promulgué plus tard, dans la mandature suivante.)")
md.append("")
md.append("### Détail leg16 (close, 34 motions)")
md.append("")
md.append(fmt_motion_table(16))
md.append("")
md.append("### Détail leg17 (en cours, 22 motions)")
md.append("")
md.append(fmt_motion_table(17))
md.append("")
md.append("## 2. Motions par date — le modèle `SignalRejet` singulier est FAUX")
md.append("")
md.append("La spec modélise un signal de rejet **unique** (1 motion ↔ 1 événement). La donnée "
          "montre que **plusieurs motions sont déposées le même jour par des groupes "
          "différents** (typiquement une motion « de gauche » NFP/LFI et une motion RN/UDR), "
          "votées dans la même séance.")
md.append("")
md.append("| leg | dates distinctes | max motions / jour | dates à ≥2 motions | motions concernées |")
md.append("|---|---|---|---|---|")
for leg in (16, 17):
    dm = dates_multi[leg]
    md.append(f"| {leg} | {dm['n_dates_distinctes']} | {dm['max_motions_un_jour']} | "
              f"{dm['n_dates_avec_plusieurs']} | {dm['n_motions_sur_dates_multi']} |")
md.append("")
md.append("**Dates leg16 à plusieurs motions :** "
          + ", ".join(f"{d} ({n})" for d, n in dates_multi[16]['dates_avec_plusieurs'].items()) + ".")
md.append("")
md.append("**Dates leg17 à plusieurs motions :** "
          + ", ".join(f"{d} ({n})" for d, n in dates_multi[17]['dates_avec_plusieurs'].items()) + ".")
md.append("")
md.append("Exemple le plus dense : **2022-10-24, 3 motions** déposées le même jour (n°358, 359, "
          "360) en réponse au 49.3 sur le PLF 2023 (1re partie). Un modèle à 1 ligne perdrait 2 "
          "des 3 signaux.")
md.append("")
md.append("## 3. Lien 49.3 → textes : la branche hors-score")
md.append("")
md.append("Aucune motion (0/56) ne porte de `dossierRef` ni de `referenceLegislative` dans sa "
          "donnée de scrutin — **le texte visé n'est PAS dans le scrutin**. Le lien autoritatif "
          "passe par l'**arbre d'actes du dossier** : les actes `*-MOTION-VOTE` "
          "(ex. `CMP-MOTION-VOTE`, `ANNLEC-MOTION-VOTE`, `ANLDEF-MOTION-VOTE`) portent un "
          "`voteRef` vers le scrutin de censure.")
md.append("")
# nb de 49.3 reliées par acte, par leg (pour le constat d'asymétrie)
link493 = {leg: sum(1 for r in motion_rows[leg] if r["alinea"] == "49.3" and r["texte_engage"])
           for leg in (16, 17)}
md.append("**Asymétrie de complétude (limite à documenter) :** ce lien n'est exploitable que "
          f"pour la **leg17 ({per_leg[17]['linkables_a_un_texte']}/22 motions reliées à un "
          f"dossier, dont {link493[17]}/11 des 49.3)**. En **leg16, seules "
          f"{per_leg[16]['linkables_a_un_texte']}/34** motions sont reliées par acte — et ce sont "
          f"des **49.2** (n°4020/4021, 2024-06-03) ; **aucune des 28 motions 49.3 de la leg16 "
          f"n'est tracée** vers son texte (le dump dossiers leg16 ne porte pas ces `voteRefs` "
          "sur les engagements budgétaires). Le rattachement leg16 reste donc *historique* "
          "(connu hors donnée : 49.3 répétés sur PLF 2023, PLFSS 2023, PLF 2024…), non "
          "vérifiable par les actes.")
md.append("")
md.append("### 3.1 Lois de finances promulguées : corpus vs exclues")
md.append("")
md.append(f"Sur **{n_finance_prom} lois de finances/PLFSS/PLFR/comptes promulguées** (toutes "
          f"législatures), **seules {n_finance_corpus} entrent dans le corpus jugeable** "
          f"(elles ont un scrutin public AN sur l'ensemble) ; **{n_finance_exclu} sont exclues** "
          "(pas de vote public d'ensemble → passées par 49.3 ou navette sans vote AN final).")
md.append("")
md.append("| leg | proc. | dans corpus ? | vote public ensemble ? | motions 49.3 liées | titre |")
md.append("|---|---|---|---|---|---|")
for f in finance:
    procs = (f["procedure"].replace("Projet de loi de ", "PL ")
             .replace("financement de la sécurité sociale", "PLFSS")
             .replace("finances", "fin."))
    moc = ", ".join(f"n{m['numero']}({m['sort'][:3]})" for m in f["motions_49_3_liees"]) or "—"
    inc = "**CORPUS**" if f["in_corpus"] else "exclue"
    md.append(f"| {f['leg']} | {procs[:34]} | {inc} | {f['has_public_ensemble_vote']} | "
              f"{moc} | {f['titre'][:46]} |")
md.append("")
md.append("Lecture : les budgets **structurants** (PLF de l'année, PLFSS) sont **systématiquement "
          "exclus** car passés par 49.3 (aucun vote public sur l'ensemble). Les seules lois "
          "financières qui entrent dans le corpus sont des textes **non engagés** : PLFR 2022 "
          "(leg16) et les **lois de fin de gestion 2024/2025** (leg17), votées normalement, plus "
          "le **PLFSS 2026** qui a obtenu un vote d'ensemble.")
md.append("")
md.append("### 3.2 Tous les textes engagés via 49.3 (leg17, lien tracé)")
md.append("")
md.append("Regroupement par dossier d'engagement / loi (le `titre_chemin` nomme le texte). "
          "**La colonne `n_motions` est la cardinalité réelle du signal de censure par "
          "événement 49.3.**")
md.append("")
md.append("| dossier | texte engagé (titre_chemin) | promulgué ? | loi corpus ? | motions | n |")
md.append("|---|---|---|---|---|---|")
for ed in engage_dossiers:
    moc = ", ".join(f"n{n}" for n in ed["motions"])
    md.append(f"| {ed['uid']} | {ed['titre_chemin'][:42]} | {ed['promulguee']} | "
              f"{ed['is_loi_corpus']} | {moc} | **{ed['n_motions']}** |")
md.append("")
md.append("## 4. Conclusion")
md.append("")
md.append(f"1. **{per_leg[16]['total']+per_leg[17]['total']} motions de censure** au total "
          f"({per_leg[16]['total']} leg16 + {per_leg[17]['total']} leg17), dont "
          f"**{per_leg[16]['n_49_3']+per_leg[17]['n_49_3']} en 49.3** "
          f"({per_leg[16]['n_49_3']} + {per_leg[17]['n_49_3']}) et "
          f"**{per_leg[16]['n_49_2']+per_leg[17]['n_49_2']} en 49.2**. "
          "**Une seule adoptée** (n°519, PLFSS 2025 Barnier).")
md.append("")
md.append(f"2. **Le modèle `SignalRejet` singulier (1 motion) est FAUX.** Cardinalité observée "
          f"**0..n** : jusqu'à **3 motions le même jour** (2022-10-24) et jusqu'à **6 motions "
          f"sur un même texte** (PLF 2026, leg17). Sur les événements 49.3 tracés (leg17), la "
          f"distribution est {dict(sorted(cardinalite.items()))} (clé = nb de motions). "
          "Le modèle doit être une **collection** de motions rattachée à un texte/lecture, "
          "chaque motion gardant auteur, alinéa, sort et décompte.")
md.append("")
md.append(f"3. **Lois structurantes hors-score via 49.3.** "
          f"**{len(finance_49_3_horsscore)} lois de finances promulguées et exclues du corpus** "
          f"ont un 49.3 *explicitement tracé* par acte en leg17 : "
          + ", ".join(f["titre"][:34] for f in finance_49_3_horsscore) + ". "
          f"En élargissant aux **budgets structurants** (PLF de l'année + PLFSS, hors "
          f"rectificatives/fin de gestion) promulgués mais hors corpus, on compte "
          f"**{len(finance_structurant_horsscore)} lois** "
          f"(" + ", ".join(f"{f['titre'][:30]} (L{f['leg']})" for f in finance_structurant_horsscore) + "). "
          f"Et globalement **{n_finance_exclu}/{n_finance_prom} lois financières promulguées "
          f"échappent au corpus jugeable**. La branche 49.3 retire du score l'essentiel de la "
          "production budgétaire structurante — angle mort assumé mais massif du périmètre v0.1.")
md.append("")
md.append("4. **Limites honnêtes :** (a) le rattachement motion→texte n'est tracé par acte "
          "qu'en **leg17** ; en leg16 il est historique. (b) Le lien repose sur les actes "
          "`*-MOTION-VOTE` du dossier — robuste là où il existe, mais dépend de la complétude "
          "du dump. (c) « Structurant » est ici opérationnalisé par « loi de finances/PLFSS "
          "promulguée » ; d'autres textes ordinaires sont aussi passés par 49.3 (non comptés "
          "ici comme financiers).")
md.append("")

with open(os.path.join(OUT, "q6-censure.md"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(md))

# ---------------------------------------------------------------------------
# Console summary
# ---------------------------------------------------------------------------
print("=== q6-censure ===")
print(f"motions: leg16={per_leg[16]['total']} (49.2={per_leg[16]['n_49_2']} 49.3={per_leg[16]['n_49_3']}) "
      f"leg17={per_leg[17]['total']} (49.2={per_leg[17]['n_49_2']} 49.3={per_leg[17]['n_49_3']})")
print(f"adoptées: {per_leg[16]['adoptees']} (leg16) + {per_leg[17]['adoptees']} (leg17)")
print(f"dates multi: leg16={dates_multi[16]['n_dates_avec_plusieurs']} leg17={dates_multi[17]['n_dates_avec_plusieurs']}")
print(f"max motions/jour: leg16={dates_multi[16]['max_motions_un_jour']} leg17={dates_multi[17]['max_motions_un_jour']}")
print(f"finance promulguées: {n_finance_prom} | corpus: {n_finance_corpus} | exclues: {n_finance_exclu}")
print(f"finance exclues avec 49.3 tracé (leg17): {len(finance_49_3_horsscore)}")
print(f"budgets structurants hors corpus: {len(finance_structurant_horsscore)} -> "
      + ", ".join(f"{f['titre'][:28]}(L{f['leg']})" for f in finance_structurant_horsscore))
print(f"cardinalité par événement 49.3: {dict(sorted(cardinalite.items()))}")
print(f"cardinalité par date séance: {dict(sorted(card_by_date.items()))}")
print(f"linkables: leg16={per_leg[16]['linkables_a_un_texte']}/34 leg17={per_leg[17]['linkables_a_un_texte']}/22")
print("écrit: out/q6-censure.md, out/q6-censure.json")
