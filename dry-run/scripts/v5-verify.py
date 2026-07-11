#!/usr/bin/env python3
"""
INDEPENDENT adversarial verification of q5-miseaupoint.
Reads RAW scrutin JSON directly. Does NOT import anlib, does NOT reuse q5 script.
Parses miseAuPoint buckets + ventilationVotes nominal positions by hand.
"""
from workspace_paths import DATA_DIR, DRY_RUN_DIR, OUT_DIR, REPO_ROOT, SCRIPTS_DIR
import json, glob, os
from collections import Counter, defaultdict

DATA = str(DATA_DIR)
CORPUS = str(OUT_DIR / "corpus.json")

def as_list(x):
    if isinstance(x, list):
        return x
    if x is None:
        return []
    return [x]

# miseAuPoint bucket name -> corrected position class
BUCKET_TO_POS = {
    "pours": "pour",
    "contres": "contre",
    "abstentions": "abstention",
    "nonVotants": "nonvotant",
    "nonVotantsVolontaires": "nonvotant",  # 5th bucket — treat as nonvotant
}

def extract_votants_from_bucket(bucket):
    """Return list of acteurRef from a miseAuPoint bucket, handling all shapes:
       - null
       - [null, null]            (empty skeleton)
       - {"votant": obj|array}
       - [null, {"votant": obj|array}]
    """
    if bucket is None:
        return []
    refs = []
    if isinstance(bucket, dict):
        for v in as_list(bucket.get("votant")):
            if isinstance(v, dict) and v.get("acteurRef"):
                refs.append(v["acteurRef"])
    elif isinstance(bucket, list):
        for el in bucket:
            if isinstance(el, dict):
                # could be {"votant":...} OR a bare votant dict
                if "votant" in el:
                    for v in as_list(el.get("votant")):
                        if isinstance(v, dict) and v.get("acteurRef"):
                            refs.append(v["acteurRef"])
                elif el.get("acteurRef"):
                    refs.append(el["acteurRef"])
    return refs

def parse_mise_au_point(mp):
    """Return dict acteurRef -> corrected_position (last bucket wins if dup, but flag dups)."""
    out = {}
    dups = []
    if not isinstance(mp, dict):
        return out, dups
    for bucket_name, pos in BUCKET_TO_POS.items():
        for ref in extract_votants_from_bucket(mp.get(bucket_name)):
            if ref in out and out[ref] != pos:
                dups.append((ref, out[ref], pos))
            out[ref] = pos
    return out, dups

def recorded_positions(scrutin):
    """acteurRef -> recorded position from ventilationVotes. Not in any bucket => non_recense."""
    out = {}
    groups = scrutin.get("ventilationVotes", {}).get("organe", {}).get("groupes", {})
    for g in as_list(groups.get("groupe")):
        dn = (g.get("vote") or {}).get("decompteNominatif") or {}
        for bucket_name, pos in [("pours","pour"),("contres","contre"),
                                  ("abstentions","abstention"),("nonVotants","nonvotant")]:
            bucket = dn.get(bucket_name)
            if bucket is None:
                continue
            for v in as_list(bucket.get("votant") if isinstance(bucket, dict) else None):
                if isinstance(v, dict) and v.get("acteurRef"):
                    out[v["acteurRef"]] = pos
    return out

def load_scrutin(leg, numero):
    if leg == 17:
        p = f"{DATA}/scrutins-17/json/VTANR5L17V{numero}.json"
    else:
        p = f"{DATA}/scrutins-16/json/VTANR5L16V{numero}.json"
    if not os.path.exists(p):
        # leg16 filenames may differ; glob
        cands = glob.glob(f"{DATA}/scrutins-{leg}/json/*V{numero}.json")
        if cands:
            p = cands[0]
        else:
            return None
    with open(p) as f:
        return json.load(f)["scrutin"]

CONGRUENCE = {"pour":"+", "contre":"-", "abstention":"0", "nonvotant":"0", "non_recense":"0"}

# -------- load AMO10 actor names --------
def load_amo10_names():
    names = {}
    for p in glob.glob(f"{DATA}/amo10-17/json/acteur/PA*.json"):
        try:
            with open(p) as f:
                a = json.load(f)["acteur"]
            uid = a["uid"]
            if isinstance(uid, dict):
                uid = uid.get("#text") or uid.get("@xsi:type") or str(uid)
            ident = a.get("etatCivil", {}).get("ident", {})
            names[uid] = f"{ident.get('prenom','?')} {ident.get('nom','?')}".strip()
        except Exception:
            pass
    return names

def main():
    corpus = json.load(open(CORPUS))
    refs = [(l["ref_leg"], l["ref_numero"], l["titre"], l["dossier_uid"]) for l in corpus["lois"]]
    amo_names = load_amo10_names()

    # ---- PER-REFERENCE-VOTE analysis ----
    per_leg = {16: Counter(), 17: Counter()}
    n_ref_with_map = {16:0, 17:0}
    corrections_total = 0
    corrections_by_target = Counter()
    transitions = Counter()
    basculantes = 0
    neutres = 0
    pour_contre_francs = 0
    francs_examples = []
    named_in_amo = 0
    not_in_amo = 0
    dup_bucket_cases = []
    nvv_corrections = 0  # corrections coming specifically from nonVotantsVolontaires
    detail_rows = []

    for leg, num, titre, uid in refs:
        per_leg[leg]["ref"] += 1
        scr = load_scrutin(leg, num)
        if scr is None:
            print(f"MISSING scrutin leg{leg} n{num}")
            continue
        mp = scr.get("miseAuPoint")
        corrections, dups = parse_mise_au_point(mp)
        for d in dups:
            dup_bucket_cases.append((leg, num, d))
        if not corrections:
            continue
        n_ref_with_map[leg] += 1
        rec = recorded_positions(scr)
        # count nvv separately
        nvv_refs = set(extract_votants_from_bucket(mp.get("nonVotantsVolontaires"))) if isinstance(mp, dict) else set()
        for ref, corr_pos in corrections.items():
            corrections_total += 1
            corrections_by_target[corr_pos] += 1
            rec_pos = rec.get(ref, "non_recense")
            transitions[(rec_pos, corr_pos)] += 1
            if ref in nvv_refs and corr_pos == "nonvotant":
                nvv_corrections += 1
            c_before = CONGRUENCE[rec_pos]
            c_after = CONGRUENCE[corr_pos]
            if c_before != c_after:
                basculantes += 1
            else:
                neutres += 1
            if {rec_pos, corr_pos} == {"pour","contre"}:
                pour_contre_francs += 1
                francs_examples.append((leg, num, titre, ref, amo_names.get(ref, "(hors AMO10)"), f"{rec_pos}->{corr_pos}"))
            if ref in amo_names:
                named_in_amo += 1
            else:
                not_in_amo += 1
            detail_rows.append({"leg":leg,"num":num,"acteurRef":ref,"rec":rec_pos,"corr":corr_pos,
                                "bascule": c_before!=c_after})

    # ---- GLOBAL context (all scrutins) ----
    global_stats = {}
    for leg in (16, 17):
        files = glob.glob(f"{DATA}/scrutins-{leg}/json/*.json")
        n_scrutins = len(files)
        n_with_real = 0
        n_corr = 0
        flag_true = 0
        for p in files:
            with open(p) as f:
                scr = json.load(f)["scrutin"]
            mp = scr.get("miseAuPoint")
            corr, _ = parse_mise_au_point(mp)
            if corr:
                n_with_real += 1
                n_corr += len(corr)
            # replicate the BUGGY flag logic: any bucket truthy?
            if isinstance(mp, dict):
                any_truthy = any(mp.get(k) for k in ("pours","contres","abstentions","nonVotants","nonVotantsVolontaires"))
                if any_truthy:
                    flag_true += 1
        global_stats[leg] = {"n_scrutins":n_scrutins, "n_with_real_map":n_with_real,
                             "pct": round(100*n_with_real/n_scrutins,1), "n_corrections":n_corr,
                             "buggy_flag_true": flag_true}

    n_ref_total = sum(per_leg[l]["ref"] for l in (16,17))
    n_ref_map_total = n_ref_with_map[16] + n_ref_with_map[17]

    result = {
        "n_ref": n_ref_total,
        "n_ref_avec_map_reelle": n_ref_map_total,
        "pct_ref_avec_map": round(100*n_ref_map_total/n_ref_total,1),
        "leg16_ref_avec_map": f"{n_ref_with_map[16]}/{per_leg[16]['ref']}",
        "leg17_ref_avec_map": f"{n_ref_with_map[17]}/{per_leg[17]['ref']}",
        "n_corrections_sur_ref": corrections_total,
        "corrections_par_cible": dict(corrections_by_target),
        "n_corrections_basculantes": basculantes,
        "pct_basculantes": round(100*basculantes/corrections_total,1) if corrections_total else 0,
        "n_corrections_neutres": neutres,
        "pour_contre_francs_sur_ref": pour_contre_francs,
        "nonVotantsVolontaires_corrections_sur_ref": nvv_corrections,
        "transitions": {f"{a}->{b}": n for (a,b),n in sorted(transitions.items(), key=lambda kv:-kv[1])},
        "exemples_nommes_amo10": named_in_amo,
        "exemples_deputes_hors_amo10": not_in_amo,
        "dup_bucket_cases": [{"leg":l,"num":n,"ref":d[0],"pos1":d[1],"pos2":d[2]} for (l,n,d) in dup_bucket_cases],
        "francs_examples": [{"leg":l,"num":n,"titre":t[:50],"ref":r,"nom":nm,"trans":tr} for (l,n,t,r,nm,tr) in francs_examples],
        "global": global_stats,
    }
    # per-leg breakdown of corrections & basculantes
    pl = {16:{"corr":0,"basc":0}, 17:{"corr":0,"basc":0}}
    for row in detail_rows:
        pl[row["leg"]]["corr"] += 1
        if row["bascule"]:
            pl[row["leg"]]["basc"] += 1
    result["per_leg_corrections"] = pl

    out_json = str(OUT_DIR / "v5-verify.json")
    json.dump(result, open(out_json,"w"), ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
