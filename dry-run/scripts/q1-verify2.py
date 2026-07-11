#!/usr/bin/env python3
"""
Definitive check of WHETHER the frozen corpus under-counts 'jugeable'.

Independent logic (no reuse of q1-funnel.py):
  For every PROMULGATED loi (PROM acte in raw dossiers), find ALL public
  ensemble scrutins (SPO/SPS, objet matches "l'ensemble (du|de la|de l') ...")
  whose TITLE CORE matches the dossier title with HIGH PRECISION
  (token-jaccard >= 0.9 OR one core is a substring of the other after norm).
  Classify by reading suffix. A loi *should be jugeable* iff at least one such
  matched ensemble scrutin exists on its FINAL reading, where FINAL =
  {texte de la commission(/mixte paritaire), lecture definitive, nouvelle
   lecture} OR (premiere/unique lecture AND the dossier has no later AN reading
   acte CMP*/ANNLEC*/ANLDEF*/AN2*). Then compare to the frozen corpus set.
"""
from workspace_paths import DATA_DIR, DRY_RUN_DIR, OUT_DIR, REPO_ROOT, SCRIPTS_DIR
import json, glob, re, unicodedata
from collections import defaultdict

DATA = str(DATA_DIR)
OUT = str(OUT_DIR)

def as_list(x):
    return x if isinstance(x, list) else ([] if x is None else [x])

def norm(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s).replace("’", "'").replace("ʼ", "'")
    return re.sub(r"\s+", " ", s.lower()).strip()

def toks(s):
    return set(t for t in re.findall(r"[a-z0-9àâäéèêëîïôöùûüç]+", s) if len(t) > 3)

# ---- raw dossiers: PROM set, title, family, acte-code set ----
PROC_FAMILY = {
    "Proposition de loi ordinaire": "PPL",
    "Projet de loi ordinaire": "PJL",
    "Projet de ratification des traités et conventions": "RATIF",
    "Projet ou proposition de loi organique": "ORGANIQUE",
    "Projet ou proposition de loi constitutionnelle": "CONSTIT",
    "Projet de loi de finances rectificative": "FINANCE",
    "Projet de loi de financement de la sécurité sociale": "FINANCE",
    "Projet de loi de finances de l'année": "FINANCE",
}

def walk_codes(node, codes):
    if node is None:
        return
    if isinstance(node, dict) and "acteLegislatif" in node:
        node = node["acteLegislatif"]
    for a in as_list(node):
        if not isinstance(a, dict):
            continue
        c = a.get("codeActe")
        if c:
            codes.add(c)
        walk_codes(a.get("actesLegislatifs"), codes)

prom = {}
for d in ("dossiers-16", "dossiers-17"):
    for f in glob.glob(f"{DATA}/{d}/json/dossierParlementaire/*.json"):
        try:
            dp = json.load(open(f)).get("dossierParlementaire") or {}
        except Exception:
            continue
        u = dp.get("uid")
        if not u:
            continue
        codes = set()
        walk_codes(dp.get("actesLegislatifs"), codes)
        if "PROM" not in codes:
            continue
        proc = (dp.get("procedureParlementaire") or {}).get("libelle")
        prom[u] = {
            "title": (dp.get("titreDossier") or {}).get("titre"),
            "tnorm": norm((dp.get("titreDossier") or {}).get("titre")),
            "family": PROC_FAMILY.get(proc, "OTHER"),
            "codes": codes,
        }
for u, r in prom.items():
    r["tset"] = toks(r["tnorm"])
    # does the dossier have an AN reading later than the first?
    r["has_later_an"] = any(
        c.startswith(("CMP-DEBATS-AN", "ANNLEC", "ANLDEF", "AN2", "AN3", "ANLUNI"))
        for c in r["codes"]
    ) or "CMP-DEC" in r["codes"]

# ---- ensemble scrutins ----
RE_ENS = re.compile(r"l'ensemble (du|de la|de l') ")
RE_TYPE = re.compile(
    r"l'ensemble (?:du|de la|de l') "
    r"(?:projet de loi|proposition de loi)"
    r"(?: organique| constitutionnelle| de finances[^ ]*| de financement[^ ]*)? "
)
FINAL = ("texte de la commission", "lecture definitive", "nouvelle lecture")
INTERMEDIATE_ONLY = ("premiere lecture", "deuxieme lecture", "premiere partie", "seconde partie")

ens = []
for leg in (16, 17):
    for f in glob.glob(f"{DATA}/scrutins-{leg}/json/*.json"):
        try:
            sc = json.load(open(f)).get("scrutin") or {}
        except Exception:
            continue
        if (sc.get("typeVote") or {}).get("codeTypeVote") not in ("SPO", "SPS"):
            continue
        ob = (sc.get("objet") or {}).get("libelle") or ""
        nob = norm(ob)
        if not RE_ENS.search(nob):
            continue
        m = RE_TYPE.search(nob)
        frag = nob[m.end():] if m else nob
        sufm = re.search(r"\(([^)]*)\)\.?\s*$", frag)
        suffix = sufm.group(1) if sufm else ""
        core = re.sub(r"\([^)]*\)\.?\s*$", "", frag).strip(" .,'")
        ens.append({
            "leg": leg, "n": sc.get("numero"), "suffix": suffix,
            "core": core, "cset": toks(core),
            "sort": (sc.get("sort") or {}).get("code"),
            "type": (sc.get("typeVote") or {}).get("codeTypeVote"),
            "is_final_reading": any(k in suffix for k in FINAL),
        })

# ---- corpus frozen jugeable set ----
corpus = json.load(open(f"{OUT}/corpus.json"))
jug = {l["dossier_uid"] for l in corpus["lois"]}

# ---- precise matching ----
def precise_match(tnorm, tset, core, cset):
    if not tset or not cset:
        return False
    # substring either way (strong)
    if len(core) > 20 and (core in tnorm or tnorm in core):
        return True
    inter = tset & cset
    jac = len(inter) / len(tset | cset)
    return jac >= 0.9

# For each promulgated loi, collect precise ensemble matches and decide "should be jugeable"
should = {}
for u, r in prom.items():
    matches = []
    for sc in ens:
        if precise_match(r["tnorm"], r["tset"], sc["core"], sc["cset"]):
            matches.append(sc)
    if not matches:
        should[u] = (False, [])
        continue
    # qualifying = final-reading vote, OR (no later AN reading -> first/unique reading vote counts)
    qual = []
    for sc in matches:
        if sc["is_final_reading"]:
            qual.append(sc)
        elif not r["has_later_an"]:
            # the only AN reading is the first/unique one -> its ensemble vote is final
            qual.append(sc)
    should[u] = (len(qual) > 0, matches)

should_set = {u for u, (ok, _) in should.items() if ok}

# misses = should-be-jugeable per our independent rule, but NOT in corpus
misses = sorted(should_set - jug)
# false-includes our rule rejects but corpus keeps (sanity: should be few; corpus may keep
#   leg15 reported laws whose ensemble vote is in leg15 dump we don't have)
corpus_only = sorted(jug - should_set)

# classify misses by family + whether match was on a final reading
miss_detail = []
for u in misses:
    ok, matches = should[u]
    fin = [m for m in matches if m["is_final_reading"]]
    use = fin if fin else matches
    best = use[0]
    miss_detail.append({
        "uid": u, "family": prom[u]["family"], "title": prom[u]["title"],
        "leg": best["leg"], "scrutin": best["n"], "suffix": best["suffix"],
        "type": best["type"], "sort": best["sort"], "has_later_an": prom[u]["has_later_an"],
    })

miss_by_fam = defaultdict(int)
for m in miss_detail:
    miss_by_fam[m["family"]] += 1

out = {
    "n_prom": len(prom),
    "n_corpus_jug": len(jug),
    "n_should_jug_indep": len(should_set),
    "n_misses": len(misses),
    "miss_by_family": dict(miss_by_fam),
    "misses": miss_detail,
    "n_corpus_only": len(corpus_only),
    "corpus_only": corpus_only,
}
print(json.dumps(out, indent=2, ensure_ascii=False))
json.dump(out, open(f"{OUT}/q1-verify2.json", "w"), indent=2, ensure_ascii=False)
