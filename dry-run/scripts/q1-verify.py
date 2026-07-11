#!/usr/bin/env python3
"""
q1-verify.py — RECALCUL ADVERSE INDÉPENDANT du chiffre-clé de q1-funnel.md.

On NE réutilise PAS anlib.build_corpus ni q1-funnel.py. On relit les JSON bruts
(dossiers + scrutins), on ré-implémente la grammaire à la main et on reconstruit
l'entonnoir 266 -> 159 deux fois :

  VOIE A (réplique la règle spec, code indépendant) :
    loi promulguée (acte PROM) + procédure produisant une loi
    + >=1 voteRef AN pointant un scrutin SPO/SPS dont l'objet contient "l'ensemble".

  VOIE B (orthogonale, sans voteRefs du tout) :
    pour chaque scrutin SPO/SPS "sur l'ensemble", on extrait le fragment de titre
    de objet.libelle et on le matche par tokens au titre du dossier promulgué.
    Donne un compte de "jugeable" totalement indépendant du lien voteRefs.

Les deux voies sont comparées au headline ET entre elles (les écarts révèlent
double-comptes / apostrophes / objet-vs-tableau / dénominateurs).
"""
import json, glob, re, unicodedata, os
from collections import Counter, defaultdict

DATA = "/home/cos/Bureau/dev/boussole-politique/dry-run/data"
OUT = "/home/cos/Bureau/dev/boussole-politique/dry-run/out"

# --------------------------------------------------------------------------
def aslist(x):
    if x is None: return []
    return x if isinstance(x, list) else [x]

def norm(s):
    if not s: return ""
    s = unicodedata.normalize("NFKC", s).replace("’", "'").replace("ʼ", "'")
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = s.lower()
    return re.sub(r"\s+", " ", s).strip()

# scrutin "sur l'ensemble" : objet normalisé contient le mot "ensemble" précédé de "l'"
RE_ENSEMBLE = re.compile(r"l'ensemble\b")
def is_ensemble(objet):
    return bool(RE_ENSEMBLE.search(norm(objet)))

PROC_LOI = {
    "Proposition de loi ordinaire", "Projet de loi ordinaire",
    "Projet ou proposition de loi organique", "Projet ou proposition de loi constitutionnelle",
    "Projet de ratification des traités et conventions",
    "Projet de loi de finances rectificative", "Projet de loi de finances de l'année",
    "Projet de loi de financement de la sécurité sociale",
    "Projet de loi relative aux résultats de la gestion et portant approbation des comptes",
    "Proposition de loi présentée en application de l'article 11 de la Constitution",
}
FAM = {
    "Proposition de loi ordinaire": "PPL",
    "Projet de loi ordinaire": "PJL",
    "Projet de ratification des traités et conventions": "RATIF",
    "Projet ou proposition de loi organique": "ORGANIQUE",
    "Projet ou proposition de loi constitutionnelle": "CONSTIT",
    "Projet de loi de finances rectificative": "FINANCE",
    "Projet de loi de financement de la sécurité sociale": "FINANCE",
    "Projet de loi de finances de l'année": "FINANCE",
    "Projet de loi relative aux résultats de la gestion et portant approbation des comptes": "FINANCE",
    "Proposition de loi présentée en application de l'article 11 de la Constitution": "PPL_ART11",
}

VOTEREF_RE = re.compile(r"VTANR5L(\d+)V(\d+)")

def walk_actes(node):
    """Parcours récursif robuste de l'arbre actesLegislatifs (gère le wrapper
    'acteLegislatif' objet-ou-liste ET la forme directe avec codeActe)."""
    if node is None:
        return
    if isinstance(node, dict):
        if "codeActe" in node:
            yield node
        for v in node.values():
            yield from walk_actes(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_actes(v)

# --------------------------------------------------------------------------
# 1) SCRUTINS bruts -> index (leg, numero) -> meta
# --------------------------------------------------------------------------
def load_scrutins():
    idx = {}
    ens_pub = defaultdict(list)   # leg -> [scrutin meta] pour SPO/SPS ensemble
    moc = defaultdict(int)
    for legdir in (16, 17):
        for p in glob.glob(f"{DATA}/scrutins-{legdir}/json/*.json"):
            s = json.load(open(p, encoding="utf-8"))["scrutin"]
            num = int(s.get("numero"))
            sleg = int(s.get("legislature") or legdir)
            tv = s.get("typeVote") or {}
            code = tv.get("codeTypeVote", "")
            lib = tv.get("libelleTypeVote", "") or ""
            objet = (s.get("objet") or {}).get("libelle", "") or ""
            ens = is_ensemble(objet)
            meta = {"type": code, "sort": (s.get("sort") or {}).get("code", ""),
                    "ensemble": ens, "date": s.get("dateScrutin", ""),
                    "objet": objet, "objet_norm": norm(objet)}
            idx[(sleg, num)] = meta
            if code in ("SPO", "SPS") and ens:
                ens_pub[sleg].append({"numero": num, **meta})
            if code == "MOC" or "motion de censure" in lib.lower():
                moc[sleg] += 1
    return idx, ens_pub, moc

# --------------------------------------------------------------------------
# 2) DOSSIERS bruts -> fusion par uid (garder le + d'actes)
# --------------------------------------------------------------------------
def load_dossiers():
    merged = {}
    for legdir in (16, 17):
        for p in glob.glob(f"{DATA}/dossiers-{legdir}/json/dossierParlementaire/*.json"):
            d = json.load(open(p, encoding="utf-8"))["dossierParlementaire"]
            uid = d.get("uid")
            if not uid:
                continue
            actes = list(walk_actes(d.get("actesLegislatifs")))
            codes = set(a["codeActe"] for a in actes)
            an_refs, all_refs = [], []
            date_max = ""
            for a in actes:
                code = a["codeActe"]
                if code.startswith("PROM") or "DEBATS" in code:
                    dt = a.get("dateActe")
                    if dt and dt > date_max:
                        date_max = dt
                vr = a.get("voteRefs")
                if vr:
                    inner = vr.get("voteRef") if isinstance(vr, dict) else vr
                    for ref in aslist(inner):
                        refstr = ref if isinstance(ref, str) else (ref.get("voteRef") if isinstance(ref, dict) else None)
                        m = VOTEREF_RE.search(refstr or "")
                        if m:
                            tup = (code, int(m.group(1)), int(m.group(2)))
                            all_refs.append(tup)
                            if code.startswith("AN") or code.startswith("CMP-DEBATS-AN"):
                                an_refs.append(tup)
            rec = {"uid": uid, "titre": (d.get("titreDossier") or {}).get("titre", "") or "",
                   "procedure": (d.get("procedureParlementaire") or {}).get("libelle", "") or "",
                   "codes": codes, "an_refs": an_refs, "all_refs": all_refs,
                   "date_max": date_max, "dossier_leg": int(d.get("legislature") or legdir)}
            if uid not in merged or len(codes) > len(merged[uid]["codes"]):
                merged[uid] = rec
    return merged

def leg_from_date(dt):
    if not dt: return None
    return 17 if dt >= "2024-07-01" else 16

def tokset(s):
    return set(t for t in re.findall(r"[a-z0-9]+", s) if len(t) > 3)

def extract_fragment(objet_norm):
    """Du 'l'ensemble (du|de la|de l') <type de loi> <TITRE> (lecture).' -> <TITRE> tokens."""
    m = re.search(r"l'ensemble (?:du|de la|de l'|des|de) (?:projet de loi de finances[^ ]*"
                  r"|projet de loi de financement[^ ]*|projet de loi organique|proposition de loi organique"
                  r"|projet de loi constitutionnelle|proposition de loi constitutionnelle"
                  r"|projet de loi|proposition de loi|proposition de resolution|proposition)\b", objet_norm)
    frag = objet_norm[m.end():] if m else objet_norm
    frag = re.sub(r"\([^)]*\)\.?\s*$", "", frag).strip(" .,'")
    return frag

# ==========================================================================
def main():
    sidx, ens_pub, moc = load_scrutins()
    dossiers = load_dossiers()

    # ----- VOIE A : entonnoir par voteRefs -----
    funnel = {"prom_loi": 0, "sans_voteref_an": 0, "voteref_non_ensemble": 0,
              "voteref_non_public": 0, "jugeable": 0}
    rows = []
    for uid, d in dossiers.items():
        if d["procedure"] not in PROC_LOI:
            continue
        if "PROM" not in d["codes"]:
            continue
        funnel["prom_loi"] += 1
        fam = FAM.get(d["procedure"], "OTHER")
        an_refs = d["an_refs"]
        status, ref_leg, ref_num = None, None, None
        artefact15 = False
        if not an_refs:
            funnel["sans_voteref_an"] += 1
            status = "sans_voteref_an"
        else:
            votes = [(c, l, n, sidx.get((l, n))) for (c, l, n) in an_refs]
            missing = [(c, l, n) for (c, l, n, s) in votes if s is None]
            present = [(c, l, n, s) for (c, l, n, s) in votes if s is not None]
            ens_pub_v = [(c, l, n, s) for (c, l, n, s) in present
                         if s["type"] in ("SPO", "SPS") and s["ensemble"]]
            if ens_pub_v:
                funnel["jugeable"] += 1
                status = "jugeable"
                ens_pub_v.sort(key=lambda x: (x[3]["date"], x[2]))
                _, ref_leg, ref_num, _ = ens_pub_v[-1]
            else:
                if any(s["ensemble"] for (_, _, _, s) in present):
                    funnel["voteref_non_public"] += 1
                    status = "voteref_non_public"
                else:
                    funnel["voteref_non_ensemble"] += 1
                    status = "voteref_non_ensemble"
                # artefact leg15 : un voteRef AN pointe un scrutin ABSENT des dumps
                if missing:
                    artefact15 = True
        leg_attr = ref_leg if status == "jugeable" else leg_from_date(d["date_max"])
        rows.append({"uid": uid, "titre": d["titre"], "procedure": d["procedure"],
                     "family": fam, "status": status, "leg_attr": leg_attr,
                     "ref_leg": ref_leg, "ref_num": ref_num,
                     "n_an_refs": len(an_refs), "artefact15": artefact15})

    prom_loi = funnel["prom_loi"]
    jugeable = funnel["jugeable"]
    perdues = prom_loi - jugeable

    def pct(n, d): return round(100.0 * n / d, 1) if d else None

    # ----- familles (VOIE A) -----
    fam_table = {}
    for fam in ("PPL", "PJL", "RATIF", "ORGANIQUE", "CONSTIT", "FINANCE", "PPL_ART11"):
        p = sum(1 for r in rows if r["family"] == fam)
        jg = sum(1 for r in rows if r["family"] == fam and r["status"] == "jugeable")
        fam_table[fam] = {"prom": p, "jug": jg, "survie_pct": pct(jg, p),
                          "part_prom_pct": pct(p, prom_loi), "part_corpus_pct": pct(jg, jugeable),
                          "derive_pts": round(pct(jg, jugeable) - pct(p, prom_loi), 1) if p and jugeable else None}

    def fam_leg(fam, leg, status=None):
        return sum(1 for r in rows if r["family"] == fam and r["leg_attr"] == leg
                   and (status is None or r["status"] == status))

    # ----- par législature -----
    jug16 = sum(1 for r in rows if r["status"] == "jugeable" and r["leg_attr"] == 16)
    jug17 = sum(1 for r in rows if r["status"] == "jugeable" and r["leg_attr"] == 17)
    prom16 = sum(1 for r in rows if r["leg_attr"] == 16)
    prom17 = sum(1 for r in rows if r["leg_attr"] == 17)

    # ----- artefacts leg15 dans voteref_non_ensemble -----
    vne = [r for r in rows if r["status"] == "voteref_non_ensemble"]
    vne_art = sum(1 for r in vne if r["artefact15"])
    vne_reel = len(vne) - vne_art

    # ----- scrutins ensemble hors loi -----
    ens_total = {leg: len(set(s["numero"] for s in ens_pub[leg])) for leg in (16, 17)}
    ens_in_jug = {16: set(), 17: set()}
    for uid, d in dossiers.items():
        if d["procedure"] not in PROC_LOI or "PROM" not in d["codes"]:
            continue
        for (c, l, n) in d["an_refs"]:
            s = sidx.get((l, n))
            if s and s["type"] in ("SPO", "SPS") and s["ensemble"]:
                if l in ens_in_jug:
                    ens_in_jug[l].add(n)
    hors_loi = {leg: ens_total[leg] - len(ens_in_jug[leg]) for leg in (16, 17)}

    # ----- VOIE B : jugeable orthogonal par matching de titre (sans voteRefs) -----
    prom_rows = [r for r in rows]
    prom_tok = {r["uid"]: tokset(norm(r["titre"])) for r in prom_rows}
    indep_jug = set()
    indep_detail = {}
    for r in prom_rows:
        tset = prom_tok[r["uid"]]
        if not tset:
            continue
        best = None
        for leg in (16, 17):
            for sc in ens_pub[leg]:
                fset = tokset(extract_fragment(sc["objet_norm"]))
                if not fset:
                    continue
                inter = tset & fset
                denom = min(len(tset), len(fset))
                score = len(inter) / denom if denom else 0
                if best is None or score > best[0]:
                    best = (score, leg, sc["numero"], len(fset))
        if best and best[0] >= 0.6 and best[3] >= 2:
            indep_jug.add(r["uid"])
            indep_detail[r["uid"]] = best
    corpus_jug_uids = {r["uid"] for r in rows if r["status"] == "jugeable"}
    indep_only = sorted(indep_jug - corpus_jug_uids)
    corpus_only = sorted(corpus_jug_uids - indep_jug)
    fam_jug_indep = Counter(next(r["family"] for r in rows if r["uid"] == u) for u in indep_jug)

    # ----- cross-check contre corpus.json figé -----
    corpus = json.load(open(f"{OUT}/corpus.json", encoding="utf-8"))
    frozen_jug_uids = {l["dossier_uid"] for l in corpus["lois"]}
    A_vs_frozen_only = sorted(corpus_jug_uids - frozen_jug_uids)
    frozen_vs_A_only = sorted(frozen_jug_uids - corpus_jug_uids)

    result = {
        "VOIE_A_voteRefs": {
            "prom_loi": prom_loi, "sans_scrutin_AN": funnel["sans_voteref_an"],
            "scrutin_non_ensemble": funnel["voteref_non_ensemble"],
            "scrutin_ensemble_non_public": funnel["voteref_non_public"],
            "jugeable": jugeable, "perdues_total": perdues,
            "taux_survie_global_pct": pct(jugeable, prom_loi),
            "jugeable_leg16": jug16, "jugeable_leg17": jug17,
            "prom_leg16": prom16, "prom_leg17": prom17,
        },
        "familles": fam_table,
        "ratif": {
            "prom": fam_table["RATIF"]["prom"], "jug": fam_table["RATIF"]["jug"],
            "perdues": fam_table["RATIF"]["prom"] - fam_table["RATIF"]["jug"],
            "survie_pct": fam_table["RATIF"]["survie_pct"],
            "survie_leg16_pct": pct(fam_leg("RATIF", 16, "jugeable"), fam_leg("RATIF", 16)),
            "survie_leg17_pct": pct(fam_leg("RATIF", 17, "jugeable"), fam_leg("RATIF", 17)),
            "prom16": fam_leg("RATIF", 16), "jug16": fam_leg("RATIF", 16, "jugeable"),
            "prom17": fam_leg("RATIF", 17), "jug17": fam_leg("RATIF", 17, "jugeable"),
            "part_prom_pct": fam_table["RATIF"]["part_prom_pct"],
            "part_corpus_pct": fam_table["RATIF"]["part_corpus_pct"],
            "derive_pts": fam_table["RATIF"]["derive_pts"],
        },
        "finance": {
            "prom": fam_table["FINANCE"]["prom"], "jug": fam_table["FINANCE"]["jug"],
            "perdues": fam_table["FINANCE"]["prom"] - fam_table["FINANCE"]["jug"],
            "survie_pct": fam_table["FINANCE"]["survie_pct"],
            "survie_leg16_pct": pct(fam_leg("FINANCE", 16, "jugeable"), fam_leg("FINANCE", 16)),
            "survie_leg17_pct": pct(fam_leg("FINANCE", 17, "jugeable"), fam_leg("FINANCE", 17)),
            "prom16": fam_leg("FINANCE", 16), "jug16": fam_leg("FINANCE", 16, "jugeable"),
            "prom17": fam_leg("FINANCE", 17), "jug17": fam_leg("FINANCE", 17, "jugeable"),
            "part_corpus_pct": fam_table["FINANCE"]["part_corpus_pct"],
        },
        "ppl": {
            "prom": fam_table["PPL"]["prom"], "jug": fam_table["PPL"]["jug"],
            "part_prom_pct": fam_table["PPL"]["part_prom_pct"],
            "part_corpus_pct": fam_table["PPL"]["part_corpus_pct"],
            "derive_pts": fam_table["PPL"]["derive_pts"],
        },
        "artefacts": {
            "scrutin_non_ensemble_artefact_leg15": vne_art,
            "scrutin_non_ensemble_reel": vne_reel,
            "scrutin_non_ensemble_total": len(vne),
        },
        "scrutins_ensemble": {
            "total_leg16": ens_total[16], "total_leg17": ens_total[17],
            "dans_loi_leg16": len(ens_in_jug[16]), "dans_loi_leg17": len(ens_in_jug[17]),
            "hors_loi_leg16": hors_loi[16], "hors_loi_leg17": hors_loi[17],
            "motions_censure_leg16": moc[16], "motions_censure_leg17": moc[17],
        },
        "VOIE_B_titre_orthogonale": {
            "jugeable_indep": len(indep_jug),
            "fam_jug_indep": dict(fam_jug_indep),
            "indep_seulement_n": len(indep_only),
            "corpus_seulement_n": len(corpus_only),
            "indep_seulement": [(u, next(r["titre"][:60] for r in rows if r["uid"]==u)) for u in indep_only][:15],
            "corpus_seulement": [(u, next(r["titre"][:60] for r in rows if r["uid"]==u),
                                  next(r["family"] for r in rows if r["uid"]==u)) for u in corpus_only][:15],
        },
        "cross_check_corpus_fige": {
            "n_dossiers_merged": len(dossiers),
            "frozen_n_lois": corpus["n_lois"],
            "A_jugeable_n": len(corpus_jug_uids),
            "A_seulement_vs_fige": A_vs_frozen_only,
            "fige_seulement_vs_A": frozen_vs_A_only,
            "identique": len(A_vs_frozen_only) == 0 and len(frozen_vs_A_only) == 0,
        },
    }

    samples = {
        "ratif_perdues_leg16": [r["titre"][:70] for r in rows if r["family"]=="RATIF" and r["status"]!="jugeable" and r["leg_attr"]==16][:6],
        "ratif_jugeables": sorted([(r["ref_leg"], r["ref_num"], r["titre"][:60]) for r in rows if r["family"]=="RATIF" and r["status"]=="jugeable"]),
        "finance_perdues": sorted([(r["leg_attr"], r["titre"][:60]) for r in rows if r["family"]=="FINANCE" and r["status"]!="jugeable"]),
        "finance_jugeables": sorted([(r["ref_leg"], r["ref_num"], r["titre"][:60]) for r in rows if r["family"]=="FINANCE" and r["status"]=="jugeable"]),
        "artefact_leg15": [r["titre"][:70] for r in vne if r["artefact15"]],
        "sans_scrutin_AN_sample": [(r["family"], r["titre"][:55]) for r in rows if r["status"]=="sans_voteref_an"][:8],
    }

    json.dump({"result": result, "samples": samples},
              open(f"{OUT}/q1-verify.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # ---- impression console comparée ----
    A = result["VOIE_A_voteRefs"]
    print("="*72)
    print("VOIE A (voteRefs, code indépendant)        | headline")
    print(f"  prom_loi            = {A['prom_loi']:>4}                   | 266")
    print(f"  sans scrutin AN     = {A['sans_scrutin_AN']:>4}                   | 82")
    print(f"  scrutin non-ensemble= {A['scrutin_non_ensemble']:>4}                   | 25")
    print(f"  ensemble non-public = {A['scrutin_ensemble_non_public']:>4}                   | 0")
    print(f"  JUGEABLE            = {A['jugeable']:>4}                   | 159")
    print(f"  PERDUES             = {A['perdues_total']:>4}                   | 107")
    print(f"  taux survie global  = {A['taux_survie_global_pct']:>5} %               | 59,8")
    print(f"  jugeable 16/17      = {A['jugeable_leg16']}/{A['jugeable_leg17']}                 | 93/66")
    print(f"  prom     16/17      = {A['prom_leg16']}/{A['prom_leg17']}               | 157/109")
    print("-"*72)
    r = result["ratif"]
    print(f"RATIF prom/jug/perd/surv = {r['prom']}/{r['jug']}/{r['perdues']}/{r['survie_pct']}% | 65/8/57/12,3")
    print(f"  survie 16={r['survie_leg16_pct']}% 17={r['survie_leg17_pct']}% | 17,9 / 3,8")
    print(f"  prom16/jug16={r['prom16']}/{r['jug16']} prom17/jug17={r['prom17']}/{r['jug17']}")
    print(f"  part prom/corpus={r['part_prom_pct']}%/{r['part_corpus_pct']}% derive={r['derive_pts']} | 24,4/5,0/-19,4")
    f = result["finance"]
    print(f"FINANCE prom/jug/perd/surv = {f['prom']}/{f['jug']}/{f['perdues']}/{f['survie_pct']}% | 14/4/10/28,6")
    print(f"  survie 16={f['survie_leg16_pct']}% 17={f['survie_leg17_pct']}% | 12,5 / 50,0")
    print(f"  part corpus={f['part_corpus_pct']}% | 2,5")
    p = result["ppl"]
    print(f"PPL prom/jug={p['prom']}/{p['jug']} part prom/corpus={p['part_prom_pct']}%/{p['part_corpus_pct']}% derive={p['derive_pts']} | 47,7/62,3/+14,6")
    print("-"*72)
    for fam in ("ORGANIQUE", "CONSTIT", "PJL"):
        t = fam_table[fam]
        print(f"{fam}: prom/jug={t['prom']}/{t['jug']} survie={t['survie_pct']}%")
    print("-"*72)
    a = result["artefacts"]; sc = result["scrutins_ensemble"]
    print(f"non-ens artefact leg15={a['scrutin_non_ensemble_artefact_leg15']} reel={a['scrutin_non_ensemble_reel']} (tot {a['scrutin_non_ensemble_total']}) | 11/14/25")
    print(f"scrutins ens total 16/17={sc['total_leg16']}/{sc['total_leg17']} hors-loi 16/17={sc['hors_loi_leg16']}/{sc['hors_loi_leg17']} | 128/135")
    print(f"motions censure 16/17={sc['motions_censure_leg16']}/{sc['motions_censure_leg17']} | 34/22")
    print("-"*72)
    b = result["VOIE_B_titre_orthogonale"]
    print(f"VOIE B (titre, SANS voteRefs): jugeable={b['jugeable_indep']}  (A={A['jugeable']}, headline 159)")
    print(f"  indep seulement={b['indep_seulement_n']}  corpus seulement={b['corpus_seulement_n']}")
    cc = result["cross_check_corpus_fige"]
    print(f"X-check vs corpus.json figé: A={cc['A_jugeable_n']} figé={cc['frozen_n_lois']} identique={cc['identique']}")
    print(f"  dossiers merged={cc['n_dossiers_merged']}")
    print("="*72)

if __name__ == "__main__":
    main()
