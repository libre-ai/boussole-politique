#!/usr/bin/env python3
"""
q1-funnel — Entonnoir du corpus & coût de chaque exclusion.

Valide/teste : revue §4 (corpus étroit/biaisé) + §2.5 (ratifications).

Quantifie le passage : LOIS PROMULGUÉES -> CORPUS JUGEABLE (vote public AN sur l'ensemble).
Pour chaque exclusion, chiffre ce qu'elle retire + exemples nommés réels :
  (a) ratifications sans vote public d'ensemble
  (b) lois passées sans scrutin public d'ensemble (main levée / scrutin non-ensemble)
  (c) budgets/lois de finances passés au 49.3 (PLF/PLFSS/PLFR — nommément)
  (d) résolutions/motions (jamais des lois — exclues en amont du périmètre "loi")

Consomme le corpus FIGÉ (out/corpus.json) ; reconstruit l'arbre des PERDUES via anlib.
Sépare leg 16 (close) et leg 17 (en cours).
"""
from __future__ import annotations
import sys, os, json, re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anlib

OUT = os.path.join(HERE, "..", "out")
CORPUS = os.path.join(OUT, "corpus.json")

FIN_PROCS = {
    "Projet de loi de finances de l'année",
    "Projet de loi de finances rectificative",
    "Projet de loi de financement de la sécurité sociale",
    "Projet de loi relative aux résultats de la gestion et portant approbation des comptes",
}

# ---------------------------------------------------------------------------
# Attribution de législature pour les PERDUES (sans vote de réf daté)
# leg16 : jun 2022 -> 30 jun 2024 ; leg17 : 1 jul 2024 -> en cours.
# On prend la date la plus tardive d'un acte daté du dossier (PROM, DEBATS-DEC…).
# ---------------------------------------------------------------------------
LEG17_START = "2024-07-01"

def _all_acte_dates(node):
    out = []
    if isinstance(node, dict):
        dt = node.get("dateActe")
        if dt:
            out.append(dt)
        for v in node.values():
            out += _all_acte_dates(v)
    elif isinstance(node, list):
        for v in node:
            out += _all_acte_dates(v)
    return out

def leg_of_dossier(d, sidx, ref_vote=None):
    """Législature de rattachement.
    Pour une loi JUGEABLE : législature du VOTE DE RÉFÉRENCE (= ce que fait corpus.json,
    règle autoritative — un texte voté en leg 16 mais promulgué en 17 reste imputé au vote).
    Pour une loi PERDUE (pas de vote de réf) : date d'acte la plus tardive (PROM/DEBATS)."""
    # 1) loi jugeable : législature du vote de référence (source autoritative)
    if ref_vote is not None:
        return ref_vote.legislature
    # 2) loi perdue : date d'acte la plus tardive (incl. scrutins AN référencés)
    dates = []
    for acte, leg, num in d.an_vote_refs():
        s = sidx.get((leg, num))
        if s and s.date:
            dates.append(s.date)
    dates += _all_acte_dates(d.raw["dossierParlementaire"].get("actesLegislatifs"))
    dates = [x for x in dates if x]
    if dates:
        return 17 if max(dates) >= LEG17_START else 16
    # 3) fallback préfixe uid (L15 reportés -> 16)
    m = re.search(r"DLR5L(\d+)N", d.uid)
    if m:
        return 17 if int(m.group(1)) >= 17 else 16
    return 16

# ---------------------------------------------------------------------------
# Reconstruction de l'arbre de l'entonnoir (PROM-loi -> jugeable)
# ---------------------------------------------------------------------------
def build_funnel_tree():
    dossiers = anlib.load_all_dossiers()
    sidx = anlib.load_all_scrutins()

    prom_loi = [(uid, d) for uid, d in dossiers.items() if d.is_loi and d.promulguee]

    rows = []  # un enregistrement par loi promulguée
    for uid, d in prom_loi:
        an_refs = d.an_vote_refs()
        votes = []
        for acte, vleg, num in an_refs:
            s = sidx.get((vleg, num))
            if s is not None:
                votes.append((acte, s))
        votes_ens = [(a, s) for (a, s) in votes
                     if s.type_code in ("SPO", "SPS") and s.is_ensemble]
        if not an_refs:
            stage = "sans_voteref_an"
        elif votes_ens:
            stage = "jugeable"
        elif any(s.is_ensemble for _, s in votes):
            stage = "voteref_non_public"
        else:
            stage = "voteref_non_ensemble"
        # législature : vote de réf (jugeable) sinon date d'acte (perdues)
        if votes_ens:
            votes_ens.sort(key=lambda x: (x[1].date, x[1].numero))
            leg = leg_of_dossier(d, sidx, ref_vote=votes_ens[-1][1])
        else:
            leg = leg_of_dossier(d, sidx)
        # marqueurs 49.3 : voteRef de type motion (MOTION-VOTE) ou actes ENGAGT/49
        motion_refs = [(a, s) for (a, s) in votes if s.type_code == "MOC"]
        ref_num = votes_ens[-1][1].numero if votes_ens else None
        ref_tc = votes_ens[-1][1].type_code if votes_ens else None
        rows.append({
            "uid": uid, "titre": d.titre, "procedure": d.procedure, "leg": leg,
            "stage": stage, "is_ratification": d.is_ratification,
            "is_finance": d.procedure in FIN_PROCS,
            "n_an_refs": len(an_refs), "n_votes_found": len(votes),
            "n_motion_refs": len(motion_refs),
            "ref_num": ref_num, "ref_tc": ref_tc,
            "votes_ens_objets": [s.objet for _, s in votes_ens],
            "non_ens_objets": [(s.numero, s.type_code, s.objet) for _, s in votes][:6],
        })
    return rows, sidx

# ---------------------------------------------------------------------------
def main():
    corpus = json.load(open(CORPUS, encoding="utf-8"))
    funnel = corpus["funnel"]
    by_leg_jug = corpus["by_leg"]  # {"16":93,"17":66} attribué par ref_leg

    rows, sidx = build_funnel_tree()

    # --- Sanity check : nos comptes doivent matcher le funnel figé ---
    stage_counts = Counter(r["stage"] for r in rows)
    sanity = {
        "prom_loi": len(rows),
        "sans_voteref_an": stage_counts["sans_voteref_an"],
        "voteref_non_ensemble": stage_counts["voteref_non_ensemble"],
        "voteref_non_public": stage_counts["voteref_non_public"],
        "jugeable": stage_counts["jugeable"],
        "corpus_funnel": funnel,
        "match": (stage_counts["jugeable"] == funnel["jugeable"]
                  and len(rows) == funnel["prom_loi"]),
    }
    # vérifie aussi que jugeable par leg == corpus by_leg
    jug_leg = Counter(r["leg"] for r in rows if r["stage"] == "jugeable")
    sanity["jugeable_by_leg_match"] = (
        jug_leg[16] == by_leg_jug["16"] and jug_leg[17] == by_leg_jug["17"])

    # --- Entonnoir par législature ---
    def leg_breakdown(stage):
        c = Counter(r["leg"] for r in rows if r["stage"] == stage)
        return {"16": c[16], "17": c[17]}

    funnel_by_leg = {
        "prom_loi": {"16": sum(1 for r in rows if r["leg"] == 16),
                     "17": sum(1 for r in rows if r["leg"] == 17)},
        "sans_voteref_an": leg_breakdown("sans_voteref_an"),
        "voteref_non_ensemble": leg_breakdown("voteref_non_ensemble"),
        "voteref_non_public": leg_breakdown("voteref_non_public"),
        "jugeable_recompute": leg_breakdown("jugeable"),
        "jugeable_corpus": by_leg_jug,
    }

    # --- (a) RATIFICATIONS ---
    ratifs = [r for r in rows if r["is_ratification"]]
    ratif_in = [r for r in ratifs if r["stage"] == "jugeable"]
    ratif_lost = [r for r in ratifs if r["stage"] != "jugeable"]
    ratif_stats = {
        "prom_total": len(ratifs),
        "in_corpus": len(ratif_in),
        "lost": len(ratif_lost),
        "in_corpus_by_leg": {"16": sum(1 for r in ratif_in if r["leg"] == 16),
                             "17": sum(1 for r in ratif_in if r["leg"] == 17)},
        "lost_by_leg": {"16": sum(1 for r in ratif_lost if r["leg"] == 16),
                        "17": sum(1 for r in ratif_lost if r["leg"] == 17)},
        "lost_by_stage": dict(Counter(r["stage"] for r in ratif_lost)),
    }

    # --- (b) MAIN LEVÉE / scrutin non-public d'ensemble ---
    # = sans_voteref_an (aucun scrutin AN public) + voteref_non_ensemble
    #   (scrutin AN existe mais pas sur l'ensemble : ex. votes partiels) — hors ratif & finance
    main_levee = [r for r in rows if r["stage"] in ("sans_voteref_an", "voteref_non_ensemble")]
    ml_non_ratif_non_fin = [r for r in main_levee if not r["is_ratification"] and not r["is_finance"]]
    # Sous-classer voteref_non_ensemble : artefact de COUVERTURE (tous scrutins référencés
    # absents du dump, ex. dossiers leg15 reportés) vs PERTE PROCÉDURALE réelle (scrutins
    # présents mais aucun n'est un vote public d'ensemble : voix/main levée, vote partiel, 49.3).
    nonens = [r for r in rows if r["stage"] == "voteref_non_ensemble"]
    cov_absent = [r for r in nonens if r["n_votes_found"] == 0]   # refs AN mais 0 scrutin trouvé
    true_nonens = [r for r in nonens if r["n_votes_found"] > 0]   # scrutins présents, non-ensemble
    nonens_split = {
        "total": len(nonens),
        "artefact_couverture_legislature": len(cov_absent),
        "perte_procedurale_reelle": len(true_nonens),
        "artefact_par_proc": dict(Counter(r["procedure"] for r in cov_absent)),
        "perte_reelle_par_proc": dict(Counter(r["procedure"] for r in true_nonens)),
        "artefact_echantillon": [{"leg": r["leg"], "titre": r["titre"], "proc": r["procedure"]}
                                 for r in sorted(cov_absent, key=lambda x: x["titre"])[:8]],
        "perte_reelle_echantillon": [
            {"leg": r["leg"], "titre": r["titre"], "proc": r["procedure"],
             "n_motion_refs": r["n_motion_refs"], "non_ens_objets": r["non_ens_objets"]}
            for r in sorted(true_nonens, key=lambda x: (x["leg"], x["titre"]))],
    }

    # --- (c) FINANCES / 49.3 ---
    fin = [r for r in rows if r["is_finance"]]
    fin_in = [r for r in fin if r["stage"] == "jugeable"]
    fin_lost = [r for r in fin if r["stage"] != "jugeable"]
    fin_with_motion = [r for r in fin if r["n_motion_refs"] > 0]
    fin_stats = {
        "prom_total": len(fin),
        "in_corpus": len(fin_in),
        "lost": len(fin_lost),
        "with_censure_motion_ref": len(fin_with_motion),
        "by_proc": dict(Counter(r["procedure"] for r in fin)),
        "lost_by_leg": {"16": sum(1 for r in fin_lost if r["leg"] == 16),
                        "17": sum(1 for r in fin_lost if r["leg"] == 17)},
    }

    # --- (d) RÉSOLUTIONS / MOTIONS : jamais des lois ---
    # Quantifier l'activité de vote AN qui ne produit AUCUNE loi : scrutins d'ensemble
    # sur des résolutions/motions + motions de censure. Mesure l'écart "activité de vote"
    # vs "lois jugeables".
    res_motion = {"16": {}, "17": {}}
    for leg in (16, 17):
        scrutins = anlib.load_scrutins(leg)
        n_ens = sum(1 for s in scrutins if s.is_ensemble and s.type_code in ("SPO", "SPS"))
        n_moc = sum(1 for s in scrutins if s.type_code == "MOC")
        # scrutins d'ensemble rattachés à une loi jugeable (via ref_num du corpus)
        ref_nums = set()
        for l in corpus["lois"]:
            if l["ref_leg"] == leg:
                ref_nums.add(l["ref_numero"])
        n_ens_loi = sum(1 for s in scrutins if s.is_ensemble and s.numero in ref_nums)
        res_motion[str(leg)] = {
            "scrutins_total": len(scrutins),
            "scrutins_ensemble_public": n_ens,
            "scrutins_ensemble_rattaches_loi_jugeable": n_ens_loi,
            "scrutins_ensemble_hors_loi_jugeable": n_ens - n_ens_loi,
            "motions_de_censure": n_moc,
        }

    # ---------------------------------------------------------------------------
    # Échantillons nommés réels
    # ---------------------------------------------------------------------------
    def sample_titles(lst, n=8):
        return [{"leg": r["leg"], "titre": r["titre"], "proc": r["procedure"],
                 "n_an_refs": r["n_an_refs"]} for r in lst[:n]]

    # Finances perdues : NOMMÉMENT toutes (ce sont les + structurantes)
    fin_lost_named = sorted(
        [{"leg": r["leg"], "titre": r["titre"], "n_an_refs": r["n_an_refs"],
          "n_motion_refs": r["n_motion_refs"], "stage": r["stage"],
          "non_ens_objets": r["non_ens_objets"]} for r in fin_lost],
        key=lambda x: (x["leg"], x["titre"]))
    fin_in_named = sorted(
        [{"leg": r["leg"], "titre": r["titre"], "ref_num": r["ref_num"], "ref_tc": r["ref_tc"]}
         for r in fin_in], key=lambda x: (x["leg"], x["titre"]))

    ratif_in_named = sorted(
        [{"leg": r["leg"], "titre": r["titre"], "ref_num": r["ref_num"], "ref_tc": r["ref_tc"]}
         for r in ratif_in], key=lambda x: (x["leg"], x["ref_num"] or 0))
    ratif_lost_named = sample_titles(sorted(ratif_lost, key=lambda r: (r["leg"], r["titre"])), 10)

    ml_named = sample_titles(sorted(ml_non_ratif_non_fin, key=lambda r: (r["leg"], r["titre"])), 12)

    # ---------------------------------------------------------------------------
    # PART des textes les plus importants PERDUS
    # ---------------------------------------------------------------------------
    # Les lois de finances = textes les plus structurants. Combien promulgués vs jugeables.
    importance = {
        "finance_prom": len(fin),
        "finance_jugeable": len(fin_in),
        "finance_perdues": len(fin_lost),
        "finance_part_perdue_pct": round(100 * len(fin_lost) / len(fin), 1) if fin else 0,
        # part des finances dans le corpus jugeable
        "finance_part_du_corpus_pct": round(100 * len(fin_in) / funnel["jugeable"], 1),
    }

    # ---------------------------------------------------------------------------
    # Représentativité : composition PROM vs CORPUS par type
    # ---------------------------------------------------------------------------
    def proc_family(p):
        if p == anlib.PROC_RATIFICATION:
            return "ratification"
        if p in FIN_PROCS:
            return "finance/budget"
        if p == "Proposition de loi ordinaire":
            return "PPL ordinaire"
        if p == "Projet de loi ordinaire":
            return "PJL ordinaire"
        if "organique" in p:
            return "organique"
        if "constitutionnelle" in p:
            return "constitutionnelle"
        return "autre"

    def repr_table(subset):
        pf = Counter(proc_family(r["procedure"]) for r in subset)
        cf = Counter(proc_family(r["procedure"]) for r in subset if r["stage"] == "jugeable")
        tot_p = len(subset)
        tot_c = sum(1 for r in subset if r["stage"] == "jugeable")
        out = {}
        for fam in sorted(set(pf) | set(cf)):
            np_, nc = pf[fam], cf[fam]
            out[fam] = {
                "promulguees": np_, "jugeables": nc,
                "taux_survie_pct": round(100 * nc / np_, 1) if np_ else None,
                "part_prom_pct": round(100 * np_ / tot_p, 1) if tot_p else 0,
                "part_corpus_pct": round(100 * nc / tot_c, 1) if tot_c else 0,
            }
        return out

    representativity = repr_table(rows)
    representativity_by_leg = {
        "16": repr_table([r for r in rows if r["leg"] == 16]),
        "17": repr_table([r for r in rows if r["leg"] == 17]),
    }

    # ---------------------------------------------------------------------------
    result = {
        "sanity": sanity,
        "funnel_global": funnel,
        "funnel_by_leg": funnel_by_leg,
        "ratifications": ratif_stats,
        "main_levee": {
            "total_sans_vote_public_ensemble": len(main_levee),
            "dont_non_ratif_non_finance": len(ml_non_ratif_non_fin),
            "by_stage": dict(Counter(r["stage"] for r in main_levee)),
            "voteref_non_ensemble_split": nonens_split,
        },
        "finances": fin_stats,
        "resolutions_motions": res_motion,
        "importance_textes_structurants": importance,
        "representativity": representativity,
        "representativity_by_leg": representativity_by_leg,
        "echantillons": {
            "finance_perdues_TOUTES": fin_lost_named,
            "finance_jugeables": fin_in_named,
            "ratif_dans_corpus": ratif_in_named,
            "ratif_perdues_echantillon": ratif_lost_named,
            "main_levee_echantillon": ml_named,
        },
    }
    with open(os.path.join(OUT, "q1-funnel.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)

    # Console summary
    print("SANITY match:", sanity["match"], "| prom_loi", sanity["prom_loi"],
          "jugeable", sanity["jugeable"])
    print("Ratif:", ratif_stats["prom_total"], "prom ->", ratif_stats["in_corpus"], "corpus,",
          ratif_stats["lost"], "perdues")
    print("Finance:", fin_stats["prom_total"], "prom ->", fin_stats["in_corpus"], "corpus,",
          fin_stats["lost"], "perdues")
    print("Funnel by leg:", json.dumps(funnel_by_leg, ensure_ascii=False))
    return result

if __name__ == "__main__":
    main()
