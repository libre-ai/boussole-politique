#!/usr/bin/env python3
"""
Vérification ADVERSE INDÉPENDANTE de q4-mandats.
Méthode: parsing BRUT des fichiers scrutin JSON (PAS anlib.positions_nominales,
PAS le script q4-mandats.py). On reconstruit tout à la main pour recouper.
"""
import json, os, glob, statistics
from collections import defaultdict

DATA = "/home/cos/Bureau/dev/boussole-politique/dry-run/data"
CORPUS = "/home/cos/Bureau/dev/boussole-politique/dry-run/out/corpus.json"
SIEGES_AN = 577

def as_list(x):
    if x is None: return []
    return x if isinstance(x, list) else [x]

# ---- 1. AMO10 acteurs (snapshot 577 députés actifs leg17) ----
amo10_files = glob.glob(f"{DATA}/amo10-17/json/acteur/PA*.json")
amo10_ids = set()
for f in amo10_files:
    uid = os.path.basename(f)[:-5]  # PA....json
    amo10_ids.add(uid)
# cross-check via uid field
amo10_uid_field = set()
for f in amo10_files:
    with open(f) as fh:
        d = json.load(fh)
    uid = d["acteur"]["uid"]
    if isinstance(uid, dict):  # XML->JSON piège: {"#text": "PA..."}
        uid = uid["#text"]
    amo10_uid_field.add(uid)
assert amo10_ids == amo10_uid_field, "filename != uid mismatch"
N_AMO10 = len(amo10_ids)

# ---- 2. charge corpus -> set des votes de référence (leg, numero) ----
with open(CORPUS) as fh:
    corpus = json.load(fh)
ref_votes = {}  # (leg, numero) -> titre
for loi in corpus["lois"]:
    ref_votes[(int(loi["ref_leg"]), int(loi["ref_numero"]))] = loi["titre"]

# ---- 3. parse brut d'un scrutin ----
def parse_scrutin(path):
    with open(path) as fh:
        s = json.load(fh)["scrutin"]
    leg = int(s["legislature"])
    numero = int(s["numero"])
    typ = s.get("typeVote", {}).get("codeTypeVote")
    date = s.get("dateScrutin")
    sort = s.get("sort", {}).get("code")
    groupes = as_list(s.get("ventilationVotes", {}).get("organe", {}).get("groupes", {}).get("groupe"))
    sum_nmg = 0
    listed = 0           # toutes positions nominatives listées (pour+contre+abst+nonvotant)
    exprimes_pers = 0    # pour/contre/abst en personne
    exprimes_deleg = 0   # pour/contre/abst par délégation
    cause_counts = defaultdict(int)
    cause_actors = defaultdict(set)
    actors_seen = set()
    actors_deleg = set()
    po_refs = []
    for g in groupes:
        nmg = g.get("nombreMembresGroupe")
        if nmg is not None:
            sum_nmg += int(nmg)
        po = g.get("organeRef")
        po_refs.append(po)
        dn = g.get("vote", {}).get("decompteNominatif", {})
        for cat in ("pours", "contres", "abstentions", "nonVotants"):
            block = dn.get(cat)
            if not block: continue
            votants = as_list(block.get("votant"))
            for v in votants:
                if v is None: continue
                listed += 1
                aref = v.get("acteurRef")
                if aref: actors_seen.add(aref)
                deleg = str(v.get("parDelegation")).lower() == "true"
                if cat in ("pours", "contres", "abstentions"):
                    if deleg:
                        exprimes_deleg += 1
                        if aref: actors_deleg.add(aref)
                    else:
                        exprimes_pers += 1
                else:  # nonVotants
                    cause = v.get("causePositionVote")
                    cause_counts[cause] += 1
                    if aref: cause_actors[cause].add(aref)
    return dict(leg=leg, numero=numero, typ=typ, date=date, sort=sort,
                sum_nmg=sum_nmg, listed=listed,
                exprimes_pers=exprimes_pers, exprimes_deleg=exprimes_deleg,
                cause_counts=dict(cause_counts), cause_actors={k:v for k,v in cause_actors.items()},
                actors_seen=actors_seen, actors_deleg=actors_deleg, po_refs=po_refs)

# ---- 4. parse TOUS les scrutins par législature ----
all_scrutins = {16: {}, 17: {}}
for leg, sub in ((16, "scrutins-16"), (17, "scrutins-17")):
    for f in glob.glob(f"{DATA}/{sub}/json/*.json"):
        r = parse_scrutin(f)
        all_scrutins[r["leg"]][r["numero"]] = r

result = {}

# ====== (a) TROU députés partis (hors AMO10) ======
for leg in (16, 17):
    # tous scrutins
    actors_all = set()
    for r in all_scrutins[leg].values():
        actors_all |= r["actors_seen"]
    hors_all = actors_all - amo10_ids
    dans_all = actors_all & amo10_ids
    # votes de référence seulement
    actors_ref = set()
    for (l, n), titre in ref_votes.items():
        if l != leg: continue
        r = all_scrutins[leg].get(n)
        if r: actors_ref |= r["actors_seen"]
    hors_ref = actors_ref - amo10_ids
    result[f"actorRef_distincts_tous_leg{leg}"] = len(actors_all)
    result[f"actorRef_dans_AMO10_leg{leg}"] = len(dans_all)
    result[f"trou_deputes_partis_hors_AMO10_leg{leg}_all"] = len(hors_all)
    result[f"actorRef_distincts_votes_reference_leg{leg}"] = len(actors_ref)
    result[f"trou_hors_AMO10_votes_reference_leg{leg}"] = len(hors_ref)

# union des deux legs
actors_all_union = set()
for leg in (16, 17):
    for r in all_scrutins[leg].values():
        actors_all_union |= r["actors_seen"]
result["actorRef_union_deux_legs"] = len(actors_all_union)
result["trou_union_deux_legs_hors_AMO10"] = len(actors_all_union - amo10_ids)
# AMO10 jamais vus en scrutin
result["AMO10_jamais_vus_leg16"] = len(amo10_ids - set().union(*[r["actors_seen"] for r in all_scrutins[16].values()]))
result["AMO10_jamais_vus_leg17"] = len(amo10_ids - set().union(*[r["actors_seen"] for r in all_scrutins[17].values()]))
# échantillon partis leg17
partis17 = sorted(((set().union(*[r["actors_seen"] for r in all_scrutins[17].values()])) - amo10_ids))
result["echantillon_partis_leg17"] = partis17[:12]

# ====== (b) Dérivation absent : 577 - listés / sum(NMG) - listés sur votes de réf ======
for leg in (16, 17):
    refs = [all_scrutins[leg][n] for (l, n) in ref_votes if l == leg and n in all_scrutins[leg]]
    listed_vals = [r["listed"] for r in refs]
    nmg_vals = [r["sum_nmg"] for r in refs]
    absent_577 = [SIEGES_AN - r["listed"] for r in refs]
    absent_nmg = [r["sum_nmg"] - r["listed"] for r in refs]
    n = len(refs)
    eq = sum(1 for r in refs if r["listed"] == r["sum_nmg"])
    nmg_ne_577 = sum(1 for r in refs if r["sum_nmg"] != SIEGES_AN)
    result[f"n_votes_reference_leg{leg}"] = n
    result[f"listes_mediane_leg{leg}"] = int(statistics.median(listed_vals))
    result[f"listes_min_leg{leg}"] = min(listed_vals)
    result[f"listes_max_leg{leg}"] = max(listed_vals)
    result[f"sumNMG_mediane_leg{leg}"] = int(statistics.median(nmg_vals))
    result[f"sumNMG_min_leg{leg}"] = min(nmg_vals)
    result[f"sumNMG_max_leg{leg}"] = max(nmg_vals)
    result[f"derive_absent_577_moins_listes_mediane_leg{leg}"] = int(statistics.median(absent_577))
    result[f"derive_absent_577_moins_listes_min_leg{leg}"] = min(absent_577)
    result[f"derive_absent_577_moins_listes_max_leg{leg}"] = max(absent_577)
    result[f"derive_absent_sumNMG_moins_listes_mediane_leg{leg}"] = int(statistics.median(absent_nmg))
    result[f"votes_ref_listes_egal_sumNMG_leg{leg}"] = f"{eq}/{n}"
    result[f"votes_ref_sumNMG_diff_577_leg{leg}"] = f"{nmg_ne_577}/{n}"
    # SPS vs SPO médiane listés
    sps = [r["listed"] for r in refs if r["typ"] == "SPS"]
    spo = [r["listed"] for r in refs if r["typ"] == "SPO"]
    result[f"listes_mediane_SPS_leg{leg}"] = int(statistics.median(sps)) if sps else None
    result[f"n_SPS_leg{leg}"] = len(sps)
    result[f"listes_mediane_SPO_leg{leg}"] = int(statistics.median(spo)) if spo else None
    result[f"n_SPO_leg{leg}"] = len(spo)
    # distribution NMG leg17
    if leg == 17:
        nmg_dist = defaultdict(int)
        for r in refs: nmg_dist[r["sum_nmg"]] += 1
        result["sumNMG_distribution_leg17"] = dict(sorted(nmg_dist.items()))

# ====== (c) Votes par délégation sur votes de référence ======
for leg in (16, 17):
    refs = [all_scrutins[leg][n] for (l, n) in ref_votes if l == leg and n in all_scrutins[leg]]
    tot_deleg = sum(r["exprimes_deleg"] for r in refs)
    tot_pers = sum(r["exprimes_pers"] for r in refs)
    tot_expr = tot_deleg + tot_pers
    pct = round(100 * tot_deleg / tot_expr, 1) if tot_expr else 0
    # pct par vote (pour max & moyenne)
    per_vote_pct = []
    max_pct_vote = None
    for r in refs:
        e = r["exprimes_deleg"] + r["exprimes_pers"]
        if e:
            p = 100 * r["exprimes_deleg"] / e
            per_vote_pct.append(p)
            if max_pct_vote is None or p > max_pct_vote[0]:
                max_pct_vote = (p, r["leg"], r["numero"])
    deput_deleg = set()
    for r in refs: deput_deleg |= r["actors_deleg"]
    result[f"deleg_total_exprimes_leg{leg}"] = tot_deleg
    result[f"pers_total_exprimes_leg{leg}"] = tot_pers
    result[f"pct_votes_exprimes_par_delegation_leg{leg}"] = pct
    result[f"pct_moyen_par_vote_ref_leg{leg}"] = round(statistics.mean(per_vote_pct), 1) if per_vote_pct else 0
    result[f"max_pct_delegation_un_vote_ref_leg{leg}"] = round(max_pct_vote[0], 1) if max_pct_vote else 0
    result[f"max_pct_delegation_vote_id_leg{leg}"] = f"leg{max_pct_vote[1]} n{max_pct_vote[2]}" if max_pct_vote else None
    result[f"deputes_avec_deleg_votes_ref_leg{leg}"] = len(deput_deleg)

# ====== (d) causes nonVotants ======
for leg in (16, 17):
    # votes de référence
    refs = [all_scrutins[leg][n] for (l, n) in ref_votes if l == leg and n in all_scrutins[leg]]
    cause_ct_ref = defaultdict(int)
    cause_act_ref = defaultdict(set)
    for r in refs:
        for c, v in r["cause_counts"].items():
            cause_ct_ref[c] += v
        for c, s in r["cause_actors"].items():
            cause_act_ref[c] |= s
    # tous scrutins
    cause_ct_all = defaultdict(int)
    cause_act_all = defaultdict(set)
    for r in all_scrutins[leg].values():
        for c, v in r["cause_counts"].items():
            cause_ct_all[c] += v
        for c, s in r["cause_actors"].items():
            cause_act_all[c] |= s
    result[f"causes_distinctes_leg{leg}"] = sorted(k for k in cause_ct_all if k)
    result[f"PAN_acteurs_distincts_leg{leg}"] = len(cause_act_all.get("PAN", set()))
    result[f"PSE_acteurs_distincts_leg{leg}"] = len(cause_act_all.get("PSE", set()))
    result[f"MG_acteurs_distincts_leg{leg}"] = len(cause_act_all.get("MG", set()))
    result[f"MG_hors_AMO10_leg{leg}"] = len(cause_act_all.get("MG", set()) - amo10_ids)
    result[f"cause_nonvotant_PAN_tous_leg{leg}"] = cause_ct_all.get("PAN", 0)
    result[f"cause_nonvotant_PSE_tous_leg{leg}"] = cause_ct_all.get("PSE", 0)
    result[f"cause_nonvotant_MG_tous_leg{leg}"] = cause_ct_all.get("MG", 0)
    # PAN identity
    pan_actors = cause_act_all.get("PAN", set())
    if pan_actors:
        result[f"PAN_acteur_id_leg{leg}"] = sorted(pan_actors)

# union causes
all_causes = set()
for leg in (16, 17):
    for r in all_scrutins[leg].values():
        for c in r["cause_counts"]:
            if c: all_causes.add(c)
result["causes_nonvotants_distinctes_union"] = sorted(all_causes)
# PAN actor union
pan_union = set()
for leg in (16, 17):
    for r in all_scrutins[leg].values():
        pan_union |= r["cause_actors"].get("PAN", set())
result["PAN_acteurs_distincts"] = len(pan_union)
result["PAN_acteur_id_union"] = sorted(pan_union)

# ====== (e) changements de groupe : po_ref distincts par acteur (PO0 exclu) ======
for leg in (16, 17):
    # acteur -> set des PO-ref vus comme groupe au moment du vote (en excluant PO0)
    actor_pos = defaultdict(set)
    po0_scrutins = set()
    for r in all_scrutins[leg].values():
        # détecte scrutin PO0 sentinelle
        if all(p == "PO0" for p in r["po_refs"] if p) and r["po_refs"]:
            po0_scrutins.add((r["numero"], r["date"]))
        # pour chaque votant, son groupe = le PO du bloc où il apparaît
        # on doit re-parcourir: re-parse pour associer acteur->po
        pass
    result[f"po0_sentinelle_scrutins_leg{leg}"] = len(po0_scrutins)
    if leg == 17:
        result["po0_dates_leg17"] = sorted(set(d for _, d in po0_scrutins))

# pour changements groupe il faut associer acteur->PO par bloc; refaisons un parse ciblé
def actor_to_pos(leg):
    actor_pos = defaultdict(set)
    for f in glob.glob(f"{DATA}/scrutins-{leg}/json/*.json"):
        with open(f) as fh:
            s = json.load(fh)["scrutin"]
        groupes = as_list(s.get("ventilationVotes", {}).get("organe", {}).get("groupes", {}).get("groupe"))
        for g in groupes:
            po = g.get("organeRef")
            if po == "PO0" or not po: continue
            dn = g.get("vote", {}).get("decompteNominatif", {})
            for cat in ("pours", "contres", "abstentions", "nonVotants"):
                block = dn.get(cat)
                if not block: continue
                for v in as_list(block.get("votant")):
                    if v is None: continue
                    aref = v.get("acteurRef")
                    if aref:
                        actor_pos[aref].add(po)
    return actor_pos

for leg in (16, 17):
    ap = actor_to_pos(leg)
    multi = {a: pos for a, pos in ap.items() if len(pos) > 1}
    result[f"changements_groupe_bruts_leg{leg}"] = len(multi)
    result[f"acteurs_total_avec_groupe_leg{leg}"] = len(ap)

# write
OUT = "/home/cos/Bureau/dev/boussole-politique/dry-run/out/v4-mandats-verify.json"
with open(OUT, "w") as fh:
    json.dump(result, fh, ensure_ascii=False, indent=2, default=lambda o: list(o) if isinstance(o, set) else o)

# print summary
print(json.dumps(result, ensure_ascii=False, indent=2, default=lambda o: list(o) if isinstance(o, set) else o))
print(f"\nN_AMO10 = {N_AMO10}")
print(f"ref_votes total = {len(ref_votes)}")
