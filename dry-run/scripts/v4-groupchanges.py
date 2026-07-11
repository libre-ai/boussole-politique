#!/usr/bin/env python3
"""Verify leg17 'changements de groupe REELS=8' independently.
Map each multi-PO-ref actor's PO set to libelleAbrev (where resolvable);
count actors with >=2 distinct abbrevs = real moves."""
import json, glob, os
from collections import defaultdict

DATA = "/home/cos/Bureau/dev/boussole-politique/dry-run/data"

def as_list(x):
    if x is None: return []
    return x if isinstance(x, list) else [x]

# PO -> abbrev map from organe dump (GP only relevant but load all)
po_abbrev = {}
for f in glob.glob(f"{DATA}/amo10-17/json/organe/PO*.json"):
    with open(f) as fh:
        o = json.load(fh)["organe"]
    uid = o.get("uid")
    if isinstance(uid, dict): uid = uid.get("#text")
    po_abbrev[uid] = (o.get("libelleAbrev"), o.get("codeType"))

# actor -> set of PO-ref (group at moment of vote), leg17, PO0 excluded
actor_pos = defaultdict(set)
for f in glob.glob(f"{DATA}/scrutins-17/json/*.json"):
    with open(f) as fh:
        s = json.load(fh)["scrutin"]
    groupes = as_list(s.get("ventilationVotes", {}).get("organe", {}).get("groupes", {}).get("groupe"))
    for g in groupes:
        po = g.get("organeRef")
        if not po or po == "PO0": continue
        dn = g.get("vote", {}).get("decompteNominatif", {})
        for cat in ("pours", "contres", "abstentions", "nonVotants"):
            block = dn.get(cat)
            if not block: continue
            for v in as_list(block.get("votant")):
                if v is None: continue
                a = v.get("acteurRef")
                if a: actor_pos[a].add(po)

multi = {a: pos for a, pos in actor_pos.items() if len(pos) > 1}
print(f"multi-PO actors leg17 (brut): {len(multi)}")

# resolve abbrevs
real_moves = []   # >=2 distinct resolvable abbrevs
unresolvable = [] # >=1 PO not in organe dump
same_abbrev = []  # multiple PO but same abbrev (renaming/churn)
for a, pos in multi.items():
    abbrevs = set()
    has_unres = False
    for po in pos:
        ab = po_abbrev.get(po)
        if ab is None:
            has_unres = True
        else:
            abbrevs.add(ab[0])
    if has_unres:
        unresolvable.append((a, sorted(pos), sorted(x for x in abbrevs if x)))
    elif len(abbrevs) > 1:
        real_moves.append((a, sorted(pos), sorted(abbrevs)))
    else:
        same_abbrev.append((a, sorted(pos), sorted(abbrevs)))

print(f"REAL moves (>=2 distinct abbrev, all resolvable): {len(real_moves)}")
for a, pos, abv in sorted(real_moves):
    print(f"   {a}: {abv}  ({pos})")
print(f"same-abbrev (renaming/churn): {len(same_abbrev)}")
print(f"unresolvable (>=1 PO not in dump): {len(unresolvable)}")
# show unresolvable that DO have >=2 distinct resolvable abbrevs (would be real too)
unres_multi_abbrev = [(a,pos,abv) for a,pos,abv in unresolvable if len(abv) >= 2]
print(f"  ...of which already show >=2 distinct resolvable abbrev (extra real moves?): {len(unres_multi_abbrev)}")
for a,pos,abv in unres_multi_abbrev:
    print(f"     {a}: {abv} ({pos})")

out = dict(
    multi_brut=len(multi),
    real_moves=len(real_moves),
    real_moves_detail=[{"acteur": a, "abbrevs": abv} for a, pos, abv in sorted(real_moves)],
    same_abbrev=len(same_abbrev),
    unresolvable=len(unresolvable),
    unres_with_multi_abbrev=len(unres_multi_abbrev),
)
with open("/home/cos/Bureau/dev/boussole-politique/dry-run/out/v4-groupchanges.json", "w") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=2)
