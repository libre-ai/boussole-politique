#!/usr/bin/env python3
"""
q4-mandats — Dérivation de l'absence, trou de données mandats, groupes datés.

Valide/teste la revue §2.2 ("absent" n'existe pas) + §2.7 (mandats/groupes datés).

Mandat :
 (a) acteurRef présents dans les ventilations mais ABSENTS d'AMO10 = trou "députés partis".
 (b) Peut-on dériver "absent" = (membres AN à la date) − (votants+nonvotants) ? Difficulté.
 (c) Votes par délégation (parDelegation=True) — "présence" est donc impropre.
 (d) Taxonomie des causePositionVote des nonVotants (PAN/PSE/MG) avec comptes.
 (e) Changements de groupe : même acteurRef sous des groupe_ref différents selon les scrutins.
 -> Conclusion sur la faisabilité d'un indicateur "présence" honnête.

Consomme le corpus FIGÉ (out/corpus.json) ; n'utilise anlib que pour charger scrutins/organes.
"""
from __future__ import annotations
from workspace_paths import DATA_DIR, DRY_RUN_DIR, OUT_DIR, REPO_ROOT, SCRIPTS_DIR
import sys, os, json, glob, collections, statistics

ROOT = str(DRY_RUN_DIR)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import anlib  # noqa: E402

SIEGES_AN = 577
ACTEUR_DIR = os.path.join(ROOT, "data", "amo10-17", "json", "acteur")
ORGANE_DIR = os.path.join(ROOT, "data", "amo10-17", "json", "organe")

# Décodage des causePositionVote (référentiel AN). Confirmé empiriquement (voir rapport).
CAUSE_LABELS = {
    "PAN": "Président de l'Assemblée nationale (ne vote pas par tradition)",
    "PSE": "Président de séance (préside, ne prend pas part au vote)",
    "MG":  "Membre du Gouvernement (mandat de député suspendu)",
}


def _txt_uid(node):
    u = node.get("uid")
    if isinstance(u, dict):
        return u.get("#text")
    return u


def load_amo_actors():
    """uid -> 'Prénom Nom' pour les députés ACTIFS (snapshot AMO10, leg 17)."""
    names = {}
    for p in glob.glob(os.path.join(ACTEUR_DIR, "PA*.json")):
        with open(p, encoding="utf-8") as fh:
            act = json.load(fh)["acteur"]
        ec = (act.get("etatCivil") or {}).get("ident") or {}
        names[_txt_uid(act)] = f"{ec.get('prenom','')} {ec.get('nom','')}".strip()
    return names


def load_amo_groups():
    """uid -> {abrev, libelle, codeType, leg} pour les organes présents dans AMO10 (leg 17)."""
    out = {}
    for p in glob.glob(os.path.join(ORGANE_DIR, "PO*.json")):
        with open(p, encoding="utf-8") as fh:
            o = json.load(fh)["organe"]
        out[_txt_uid(o)] = {
            "abrev": o.get("libelleAbrev"),
            "libelle": o.get("libelle"),
            "codeType": o.get("codeType"),
            "leg": o.get("legislature"),
        }
    return out


def main():
    with open(os.path.join(ROOT, "out", "corpus.json"), encoding="utf-8") as fh:
        corpus = json.load(fh)
    sidx = anlib.load_all_scrutins()
    amo_names = load_amo_actors()
    amo_set = set(amo_names)
    glab = load_amo_groups()

    def gname(ref):
        if ref in glab and glab[ref].get("abrev"):
            return glab[ref]["abrev"]
        return ref  # PO non résolu (typiquement groupe leg 16, hors snapshot AMO10)

    out = {
        "meta": {
            "sieges_an": SIEGES_AN,
            "amo10_actors": len(amo_set),
            "amo10_groupes_po": len(glab),
            "n_lois": corpus["n_lois"],
            "by_leg": corpus["by_leg"],
            "note": "AMO10 = snapshot des députés ACTIFS (leg 17). Pas d'historique leg 16.",
        }
    }

    # ----------------------------------------------------------------------
    # (a) Trou "députés partis" : acteurRef dans les ventilations mais hors AMO10
    # ----------------------------------------------------------------------
    seen = {16: set(), 17: set()}
    # acteurs dans les VENTILATIONS des VOTES DE RÉFÉRENCE uniquement
    ref_scrutins = {16: [], 17: []}
    for loi in corpus["lois"]:
        leg, num = loi["ref_leg"], loi["ref_numero"]
        s = sidx.get((leg, num))
        if s is not None:
            ref_scrutins[leg].append((loi, s))
    seen_ref = {16: set(), 17: set()}
    for leg in (16, 17):
        for loi, s in ref_scrutins[leg]:
            for (aref, pos, pard, gref, cause) in s.positions_nominales():
                if aref:
                    seen_ref[leg].add(aref)
        # et tous scrutins (contexte large)
        for s in anlib.load_scrutins(leg):
            for (aref, pos, pard, gref, cause) in s.positions_nominales():
                if aref:
                    seen[leg].add(aref)

    a_block = {}
    for leg in (16, 17):
        all_seen = seen[leg]
        ref_seen = seen_ref[leg]
        a_block[f"leg{leg}"] = {
            "ref_votes_count": len(ref_scrutins[leg]),
            "distinct_acteurRef_all_scrutins": len(all_seen),
            "distinct_acteurRef_in_AMO10_all": len(all_seen & amo_set),
            "distinct_acteurRef_NOT_in_AMO10_all": len(all_seen - amo_set),
            "distinct_acteurRef_ref_votes": len(ref_seen),
            "distinct_acteurRef_ref_votes_NOT_in_AMO10": len(ref_seen - amo_set),
        }
    a_block["union_both_legs_distinct"] = len(seen[16] | seen[17])
    a_block["union_both_legs_NOT_in_AMO10"] = len((seen[16] | seen[17]) - amo_set)
    # quelques noms de "députés partis" identifiables (leg17, hors AMO10 mais qui sont dans noms? non) -> ids
    gone17 = sorted(seen[17] - amo_set)
    a_block["examples_gone_leg17_ids"] = gone17[:15]
    out["a_trou_deputes_partis"] = a_block

    # ----------------------------------------------------------------------
    # (b) Dérivation "absent" : (membres à la date) − (votants+nonvotants)
    # ----------------------------------------------------------------------
    b_block = {}
    detail_rows = {16: [], 17: []}
    for leg in (16, 17):
        listed_l, nmg_l, abs577_l, absnmg_l = [], [], [], []
        sps_listed, spo_listed = [], []
        listed_eq_nmg = 0
        nmg_neq_577 = 0
        nmg_totals = collections.Counter()
        for loi, s in ref_scrutins[leg]:
            pos = list(s.positions_nominales())
            listed = len(pos)
            vv = s.raw["scrutin"].get("ventilationVotes") or {}
            gl = anlib.as_list((vv.get("organe") or {}).get("groupes", {}).get("groupe"))
            nmg = sum(int(g.get("nombreMembresGroupe", 0) or 0) for g in gl)
            abs577 = SIEGES_AN - listed
            absnmg = nmg - listed
            listed_l.append(listed); nmg_l.append(nmg)
            abs577_l.append(abs577); absnmg_l.append(absnmg)
            nmg_totals[nmg] += 1
            if listed == nmg:
                listed_eq_nmg += 1
            if nmg != SIEGES_AN:
                nmg_neq_577 += 1
            if s.type_code == "SPS":
                sps_listed.append(listed)
            else:
                spo_listed.append(listed)
            detail_rows[leg].append({
                "numero": s.numero, "date": s.date, "type": s.type_code,
                "titre": loi["titre"][:90], "listed": listed, "sum_NMG": nmg,
                "absent_577_minus_listed": abs577, "absent_NMG_minus_listed": absnmg,
                "nb_votants_synth": s.nb_votants,
            })

        def stat(xs):
            return {"min": min(xs), "max": max(xs), "median": round(statistics.median(xs), 1),
                    "mean": round(statistics.mean(xs), 1)}

        b_block[f"leg{leg}"] = {
            "ref_vote_types": dict(collections.Counter(s.type_code for _, s in ref_scrutins[leg])),
            "listed_positions": stat(listed_l),
            "sum_nombreMembresGroupe": stat(nmg_l),
            "derived_absent_577_minus_listed": stat(abs577_l),
            "derived_absent_NMG_minus_listed": stat(absnmg_l),
            "ref_votes_listed_equals_sumNMG": f"{listed_eq_nmg}/{len(listed_l)}",
            "ref_votes_sumNMG_not_577": f"{nmg_neq_577}/{len(listed_l)}",
            "distinct_sumNMG_totals": dict(sorted(nmg_totals.items())),
            "SPS_listed": stat(sps_listed) if sps_listed else None,
            "SPO_listed": stat(spo_listed) if spo_listed else None,
        }
    out["b_derivation_absent"] = b_block

    # ----------------------------------------------------------------------
    # (c) Votes par délégation
    # ----------------------------------------------------------------------
    c_block = {}
    for leg in (16, 17):
        pard_true = pard_false = 0
        per_vote_pard = []
        actors_ever_pard = set()
        for loi, s in ref_scrutins[leg]:
            vt = vf = 0
            for (aref, pos, pard, gref, cause) in s.positions_nominales():
                if pos in ("pour", "contre", "abstention"):  # délégation ne concerne que les votants exprimés
                    if pard:
                        vt += 1; actors_ever_pard.add(aref)
                    else:
                        vf += 1
            pard_true += vt; pard_false += vf
            listed_express = vt + vf
            per_vote_pard.append((vt / listed_express) if listed_express else 0.0)
        c_block[f"leg{leg}"] = {
            "par_delegation_true_total": pard_true,
            "par_delegation_false_total": pard_false,
            "pct_express_votes_par_delegation": round(100 * pard_true / max(1, pard_true + pard_false), 1),
            "distinct_actors_ever_par_delegation_in_ref_votes": len(actors_ever_pard),
            "mean_pct_per_ref_vote": round(100 * statistics.mean(per_vote_pard), 1),
            "max_pct_per_ref_vote": round(100 * max(per_vote_pard), 1),
        }
    # exemple : vote de référence avec le plus de délégations
    worst = None
    for leg in (16, 17):
        for loi, s in ref_scrutins[leg]:
            pos = list(s.positions_nominales())
            express = [p for p in pos if p[1] in ("pour", "contre", "abstention")]
            if not express:
                continue
            pct = sum(1 for p in express if p[2]) / len(express)
            if worst is None or pct > worst[0]:
                worst = (pct, leg, s.numero, loi["titre"][:70], sum(1 for p in express if p[2]), len(express))
    c_block["example_max_delegation_ref_vote"] = {
        "pct": round(100 * worst[0], 1), "leg": worst[1], "numero": worst[2],
        "titre": worst[3], "delegated": worst[4], "express_total": worst[5],
    }
    out["c_par_delegation"] = c_block

    # ----------------------------------------------------------------------
    # (d) Taxonomie causePositionVote des nonVotants
    # ----------------------------------------------------------------------
    d_block = {"cause_labels": CAUSE_LABELS}
    for leg in (16, 17):
        # sur votes de référence
        causes_ref = collections.Counter()
        actors_by_cause_ref = collections.defaultdict(set)
        for loi, s in ref_scrutins[leg]:
            for (aref, pos, pard, gref, cause) in s.positions_nominales():
                if pos == "nonvotant":
                    causes_ref[cause] += 1
                    actors_by_cause_ref[cause].add(aref)
        # sur TOUS scrutins (vue d'ensemble) + distinct actors
        causes_all = collections.Counter()
        actors_by_cause_all = collections.defaultdict(set)
        for s in anlib.load_scrutins(leg):
            for (aref, pos, pard, gref, cause) in s.positions_nominales():
                if pos == "nonvotant":
                    causes_all[cause] += 1
                    actors_by_cause_all[cause].add(aref)
        d_block[f"leg{leg}"] = {
            "nonvotant_causes_ref_votes": dict(causes_ref),
            "distinct_actors_by_cause_ref_votes": {c: len(v) for c, v in actors_by_cause_ref.items()},
            "nonvotant_causes_all_scrutins": dict(causes_all),
            "distinct_actors_by_cause_all_scrutins": {c: len(v) for c, v in actors_by_cause_all.items()},
            "MG_actors_not_in_AMO10": len(actors_by_cause_all.get("MG", set()) - amo_set),
            "MG_actors_in_AMO10": len(actors_by_cause_all.get("MG", set()) & amo_set),
        }
    # qui est le PAN ?
    pan_ids = set()
    for s in anlib.load_scrutins(17):
        for (aref, pos, pard, gref, cause) in s.positions_nominales():
            if pos == "nonvotant" and cause == "PAN":
                pan_ids.add(aref)
    d_block["PAN_identity"] = {pid: amo_names.get(pid, "(hors AMO10)") for pid in pan_ids}
    # quelques noms MG dans AMO10
    mg_ids = set()
    for s in anlib.load_scrutins(17):
        for (aref, pos, pard, gref, cause) in s.positions_nominales():
            if pos == "nonvotant" and cause == "MG":
                mg_ids.add(aref)
    d_block["MG_examples_in_AMO10"] = {pid: amo_names[pid] for pid in list(mg_ids & amo_set)[:8]}
    out["d_causes_nonvotants"] = d_block

    # ----------------------------------------------------------------------
    # (e) Changements de groupe : même acteurRef sous des groupe_ref différents
    # ----------------------------------------------------------------------
    e_block = {}
    for leg in (16, 17):
        # chronologie groupe_ref par acteur (1 entrée par scrutin, PO0 exclu)
        seq = collections.defaultdict(list)
        for s in anlib.load_scrutins(leg):
            seen_this = set()
            for (aref, pos, pard, gref, cause) in s.positions_nominales():
                if aref and gref and gref != "PO0" and aref not in seen_this:
                    seen_this.add(aref)
                    seq[aref].append((s.date, s.numero, gref))
        multi = []
        for aref, lst in seq.items():
            distinct = sorted({g for _, _, g in lst})
            if len(distinct) > 1:
                # séquence compressée (transitions réelles)
                comp, prev = [], None
                for d, n, g in lst:
                    if g != prev:
                        comp.append(g); prev = g
                multi.append((aref, distinct, comp))
        # exemples nommés (leg17 résolvables)
        examples = []
        for aref, distinct, comp in multi:
            labs = [gname(g) for g in comp]
            nm = amo_names.get(aref, "(hors AMO10)")
            examples.append({"acteurRef": aref, "nom": nm, "n_distinct_groups": len(distinct),
                             "transition_labels": labs})
        examples.sort(key=lambda x: -x["n_distinct_groups"])
        # honnêteté : séparer changement GENUINE (labels d'abrév distincts) du churn de PO-ref
        # (même abrév sous 2 PO-refs = renommage/constitution de groupe, pas une mutation)
        genuine, samelabel, unresolved = [], [], []
        for aref, lst in seq.items():
            refs = {g for _, _, g in lst}
            if len(refs) <= 1:
                continue
            labels = [glab.get(r, {}).get("abrev") for r in refs]
            labset = {l for l in labels if l}
            if any(l is None for l in labels) and len(labset) <= 1:
                unresolved.append(aref)   # ≥1 PO-ref hors snapshot AMO10 (typique leg16)
            elif len(labset) > 1:
                genuine.append(aref)
            else:
                samelabel.append(aref)    # même abrév, plusieurs PO-refs = renommage
        genuine_named = []
        for aref in genuine:
            labs = [glab.get(r, {}).get("abrev") or r for r in dict.fromkeys(g for _, _, g in seq[aref])]
            genuine_named.append({"acteurRef": aref, "nom": amo_names.get(aref, "(hors AMO10)"),
                                  "transition": labs})
        e_block[f"leg{leg}"] = {
            "deputies_with_multiple_groupe_ref": len(multi),
            "deputies_total_in_scrutins": len(seq),
            "pct_multi": round(100 * len(multi) / max(1, len(seq)), 1),
            "genuine_group_change_diff_label": len(genuine),
            "same_label_rename_churn": len(samelabel),
            "unresolved_po_ref_outside_AMO10": len(unresolved),
            "genuine_examples": genuine_named[:12],
            "examples_raw": examples[:6],
        }
    # PO0 sentinel
    po0_dates = collections.Counter()
    po0_scrutins = 0
    for s in anlib.load_scrutins(17):
        grefs = {p[3] for p in s.positions_nominales()}
        if grefs and grefs <= {"PO0", None}:
            po0_scrutins += 1
            po0_dates[s.date] += 1
    e_block["po0_sentinel_leg17"] = {
        "scrutins_all_groups_PO0": po0_scrutins,
        "dates": dict(po0_dates),
        "note": "Sur ces scrutins le groupe_ref est anonymisé (PO0) -> groupe au moment du vote inconnu.",
    }
    out["e_changements_groupe"] = e_block

    # ----------------------------------------------------------------------
    # Verdict de faisabilité
    # ----------------------------------------------------------------------
    out["verdict"] = {
        "absent_derivable": False,
        "raisons": [
            "AMO10 est un snapshot (577) sans historique : on ne connaît pas la composition de l'AN À LA DATE du vote.",
            f"{a_block['leg17']['distinct_acteurRef_NOT_in_AMO10_all']} acteurRef leg17 (et {a_block['leg16']['distinct_acteurRef_NOT_in_AMO10_all']} leg16) votent mais ne sont pas dans AMO10 (députés partis).",
            "listed != sum(nombreMembresGroupe) dans 100% des votes de référence : le non-listé n'est PAS de l'absence prouvée.",
            "Sur SPO (ordinaire) la ventilation nominale est partielle (mediane ~124-132 listés) -> '577-listed' surcompte massivement l'absence.",
            "Le vote par délégation est un vote SANS présence physique -> 'présence' est intrinsèquement impropre.",
        ],
        "ce_qui_est_honnete": [
            "Un indicateur de PARTICIPATION (a pris part au scrutin = pour/contre/abstention, hors délégation) est calculable et borné par la donnée listée.",
            "Les nonVotants à cause institutionnelle (PAN/PSE/MG) doivent être EXCLUS du dénominateur, pas comptés comme absents.",
            "Le groupe doit venir de groupe_ref au moment du vote (datage par scrutin), jamais du mandat 'courant' AMO10.",
            "Le 'changement de groupe' brut (54 leg16 / 23 leg17) sur-compte : seuls 8 (leg17) sont des mutations à libellé distinct ; le reste est du churn de PO-ref (renommage/constitution de groupe type UDDPLR) ou non résolvable (organes leg16 hors AMO10).",
        ],
    }

    # écriture JSON
    outp = os.path.join(ROOT, "out", "q4-mandats.json")
    with open(outp, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)

    # détail pour le rapport (top / bottom rows)
    out["_detail_rows"] = detail_rows
    print("WROTE", outp)
    # résumé console
    print(json.dumps({k: v for k, v in out.items() if k != "_detail_rows"}, ensure_ascii=False, indent=2)[:60])
    return out


if __name__ == "__main__":
    main()
