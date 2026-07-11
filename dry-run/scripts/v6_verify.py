#!/usr/bin/env python3
"""Independent adversarial verification of q6-censure headline.
Does NOT import the analysis script. Reads raw JSON files directly + corpus.json.
Reuses anlib ONLY as an independent cross-check oracle at the end.
"""
from workspace_paths import DATA_DIR, DRY_RUN_DIR, OUT_DIR, REPO_ROOT, SCRIPTS_DIR
import json, glob, os, re, sys
from collections import defaultdict, Counter

DATA = str(DATA_DIR)
OUT = str(OUT_DIR)

def as_list(x):
    return x if isinstance(x, list) else ([] if x is None else [x])

def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

# ---------------------------------------------------------------------------
# 1. Recensement des motions de censure (filtre type_code == MOC) — RAW files
# ---------------------------------------------------------------------------
def collect_motions(leg):
    rows = []
    for p in glob.glob(f"{DATA}/scrutins-{leg}/json/*.json"):
        s = load_json(p)["scrutin"]
        if s.get("typeVote", {}).get("codeTypeVote") != "MOC":
            continue
        titre = s.get("titre", "") or ""
        # normalise apostrophes
        t = titre.replace("’", "'")
        if re.search(r"alin[ée]a 2", t):
            al = "49.2"
        elif re.search(r"alin[ée]a 3", t):
            al = "49.3"
        else:
            al = "??"
        dec = s.get("syntheseVote", {}).get("decompte", {})
        rows.append({
            "leg": int(leg),
            "numero": int(s["numero"]),
            "date": s.get("dateScrutin"),
            "alinea": al,
            "sort": s.get("sort", {}).get("code"),
            "pour": int(dec.get("pour", 0) or 0),
            "contre": int(dec.get("contre", 0) or 0),
            "abst": int(dec.get("abstentions", 0) or 0),
            "votants": int(s.get("syntheseVote", {}).get("nombreVotants", 0) or 0),
            "libelle": s.get("typeVote", {}).get("libelleTypeVote"),
        })
    return sorted(rows, key=lambda r: r["numero"])

m16 = collect_motions(16)
m17 = collect_motions(17)
allm = m16 + m17

def summ(ms):
    return {
        "total": len(ms),
        "n_49_2": sum(1 for r in ms if r["alinea"] == "49.2"),
        "n_49_3": sum(1 for r in ms if r["alinea"] == "49.3"),
        "n_unclassified": sum(1 for r in ms if r["alinea"] == "??"),
        "adoptees": sum(1 for r in ms if r["sort"] == "adopté"),
        "rejetees": sum(1 for r in ms if r["sort"] == "rejeté"),
        "libelles": dict(Counter(r["libelle"] for r in ms)),
    }

R = {"leg16": summ(m16), "leg17": summ(m17), "total": summ(allm)}

# adoptee detail
adopted = [r for r in allm if r["sort"] == "adopté"]

# ---------------------------------------------------------------------------
# 2. Cardinalité par date (séance)
# ---------------------------------------------------------------------------
def card_by_date(ms):
    c = Counter(r["date"] for r in ms)
    hist = Counter(c.values())
    multi = {d: n for d, n in c.items() if n >= 2}
    return {
        "distinct_dates": len(c),
        "hist": dict(hist),
        "dates_multi": dict(sorted(multi.items())),
        "max": max(c.values()) if c else 0,
        "max_date": max(c, key=c.get) if c else None,
    }

cd16 = card_by_date(m16)
cd17 = card_by_date(m17)
# combined keyed by (leg,date)
comb = Counter((r["leg"], r["date"]) for r in allm)
comb_hist = dict(Counter(comb.values()))

# ---------------------------------------------------------------------------
# 3. Lien 49.3 -> texte via actes *-MOTION-VOTE (voteRef -> scrutin MOC)
# ---------------------------------------------------------------------------
def extract_voterefs(node):
    """Pull every voteRef string under a node's voteRef / voteRefs key (object-or-list-or-string)."""
    refs = []
    for key in ("voteRefs", "voteRef"):
        vr = node.get(key)
        if vr is None:
            continue
        # vr may be a string, an object {voteRef:...}, or a list of either
        for item in as_list(vr):
            if isinstance(item, str):
                refs.append(item)
            elif isinstance(item, dict):
                inner = item.get("voteRef")
                for ii in as_list(inner):
                    if isinstance(ii, str):
                        refs.append(ii)
    return refs

def walk_actes(node, out):
    """Recursively collect (codeActe, voteRef_scrutin_uid) from an actes tree."""
    if isinstance(node, dict):
        code = node.get("codeActe")
        if code and "MOTION-VOTE" in code:
            refs = extract_voterefs(node)
            if not refs:
                out.append((code, None))
            for r in refs:
                out.append((code, r))
        # recurse all values
        for v in node.values():
            walk_actes(v, out)
    elif isinstance(node, list):
        for v in node:
            walk_actes(v, out)

def motion_links(leg):
    """Return dict uid -> {titre, titreChemin, set of scrutin numeros referenced by MOTION-VOTE acts}."""
    links = {}
    moc_numeros = set(r["numero"] for r in (m16 if leg == 16 else m17))
    for p in glob.glob(f"{DATA}/dossiers-{leg}/json/dossierParlementaire/*.json"):
        d = load_json(p)["dossierParlementaire"]
        out = []
        walk_actes(d.get("actesLegislatifs"), out)
        if not out:
            continue
        scrutins = set()
        for code, vr in out:
            if not vr:
                continue
            mnum = re.search(r"V(\d+)$", vr)
            if mnum:
                scrutins.add(int(mnum.group(1)))
        if scrutins:
            links[d["uid"]] = {
                "titre": d.get("titreDossier", {}).get("titre"),
                "titreChemin": d.get("titreDossier", {}).get("titreChemin"),
                "procedure": d.get("procedureParlementaire", {}).get("libelle"),
                "scrutins": sorted(scrutins),
                "moc_scrutins": sorted(scrutins & moc_numeros),
            }
    return links

links16 = motion_links(16)
links17 = motion_links(17)

# count MOC motions (49.3) reliees a un texte par leg
def motions_reliees(links, ms):
    by_al = {r["numero"]: r["alinea"] for r in ms}
    reliee_all = set()
    reliee_493 = set()
    for uid, info in links.items():
        for n in info["moc_scrutins"]:
            reliee_all.add(n)
            if by_al.get(n) == "49.3":
                reliee_493.add(n)
    return reliee_all, reliee_493

rel16_all, rel16_493 = motions_reliees(links16, m16)
rel17_all, rel17_493 = motions_reliees(links17, m17)

n_493_leg16 = R["leg16"]["n_49_3"]
n_493_leg17 = R["leg17"]["n_49_3"]

# Cardinality per 49.3 dossier-event (leg17): how many MOC-49.3 motions per dossier
by_al17 = {r["numero"]: r["alinea"] for r in m17}
card_event_493_leg17 = Counter()
dossier_493_motions = {}
for uid, info in links17.items():
    n493 = [n for n in info["moc_scrutins"] if by_al17.get(n) == "49.3"]
    if n493:
        card_event_493_leg17[len(n493)] += 1
        dossier_493_motions[uid] = {"titreChemin": info["titreChemin"], "n": len(n493), "scrutins": n493}

# max motions on one text (leg17)
max_text_n = max((v["n"] for v in dossier_493_motions.values()), default=0)
max_text = [v for v in dossier_493_motions.values() if v["n"] == max_text_n]

# ---------------------------------------------------------------------------
# 4. dossierRef / referenceLegislative in scrutins (claim: 0)
# ---------------------------------------------------------------------------
def scrutin_self_ref(leg):
    """count MOC scrutins that themselves carry a non-empty dossierLegislatif / referenceLegislative."""
    n_with = 0
    for p in glob.glob(f"{DATA}/scrutins-{leg}/json/*.json"):
        s = load_json(p)["scrutin"]
        if s.get("typeVote", {}).get("codeTypeVote") != "MOC":
            continue
        obj = s.get("objet", {})
        dl = obj.get("dossierLegislatif")
        rl = s.get("referenceLegislative")
        if (dl and str(dl).strip()) or (rl and str(rl).strip()):
            n_with += 1
    return n_with

selfref16 = scrutin_self_ref(16)
selfref17 = scrutin_self_ref(17)

# ---------------------------------------------------------------------------
# 5. Lois de finances promulguées : corpus vs exclues
#    Independent of analysis: scan ALL dossiers for finance procedure + PROM, then
#    intersect with corpus.json membership.
# ---------------------------------------------------------------------------
corpus = load_json(f"{OUT}/corpus.json")
corpus_uids = set(l["dossier_uid"] for l in corpus["lois"])

FINANCE_PAT = re.compile(r"financ|finances|s[ée]curit[ée] sociale|PLF|PLFSS|PLFR", re.I)

def has_prom(d):
    codes = []
    def w(n):
        if isinstance(n, dict):
            if n.get("codeActe"):
                codes.append(n["codeActe"])
            for v in n.values():
                w(v)
        elif isinstance(n, list):
            for v in n:
                w(v)
    w(d.get("actesLegislatifs"))
    return any(c == "PROM" for c in codes)

def finance_promulguees():
    rows = []
    for leg in (16, 17):
        for p in glob.glob(f"{DATA}/dossiers-{leg}/json/dossierParlementaire/*.json"):
            d = load_json(p)["dossierParlementaire"]
            proc = (d.get("procedureParlementaire", {}) or {}).get("libelle", "") or ""
            titre = (d.get("titreDossier", {}) or {}).get("titre", "") or ""
            # finance = procedure is a finance procedure
            is_fin_proc = bool(re.search(r"financ", proc, re.I))
            if not is_fin_proc:
                continue
            if not has_prom(d):
                continue
            rows.append({
                "leg": leg,
                "uid": d["uid"],
                "titre": titre,
                "procedure": proc,
                "in_corpus": d["uid"] in corpus_uids,
            })
    return rows

fin = finance_promulguees()
fin_total = len(fin)
fin_corpus = sum(1 for r in fin if r["in_corpus"])
fin_excl = fin_total - fin_corpus

# budgets structurants (def A, = l'enumeration de l'analyse) :
#   PLF de l'annee  OU  PLFSS (financement secu, Y COMPRIS le PLFSS rectificatif),
#   en EXCLUANT seulement les PLF rectificatives / fin de gestion.
def is_structurant_A(r):
    p = r["procedure"].lower()
    is_plf_annee = "finances de l" in p          # "Projet de loi de finances de l'annee"
    is_plfss = "financement de la s" in p        # PLFSS, incl. rectificative
    return is_plf_annee or is_plfss

# def B (plus stricte, exclut aussi le PLFSS rectificatif) -> donne 7
def is_structurant_B(r):
    return is_structurant_A(r) and ("rectificat" not in r["titre"].lower())

struct_hors_corpus_A = [r for r in fin if (not r["in_corpus"]) and is_structurant_A(r)]
struct_hors_corpus_B = [r for r in fin if (not r["in_corpus"]) and is_structurant_B(r)]
struct_hors_corpus = struct_hors_corpus_A  # alignement sur l'analyse

# leg17 finance EXCLUE + promulguee avec 49.3 trace par acte
fin_excl_493_trace_leg17 = []
for uid, info in links17.items():
    n493 = [n for n in info["moc_scrutins"] if by_al17.get(n) == "49.3"]
    if not n493:
        continue
    proc = (info.get("procedure") or "")
    if not re.search("financ", proc, re.I):
        continue
    if uid in corpus_uids:
        continue
    fin_excl_493_trace_leg17.append({"uid": uid, "titre": info["titre"], "motions": n493})

result = {
    "recensement": R,
    "adopted_detail": adopted,
    "card_date_leg16": cd16,
    "card_date_leg17": cd17,
    "card_date_combined_hist": comb_hist,
    "links": {
        "leg16_dossiers_with_moc_voteref": len(rel16_all),
        "leg16_49_3_reliees": len(rel16_493),
        "leg17_motions_reliees_all": len(rel17_all),
        "leg17_49_3_reliees": len(rel17_493),
        "leg17_49_3_total": n_493_leg17,
        "leg16_49_3_total": n_493_leg16,
        "scrutin_selfref_moc_leg16": selfref16,
        "scrutin_selfref_moc_leg17": selfref17,
    },
    "card_event_493_leg17": dict(sorted(card_event_493_leg17.items())),
    "max_motions_one_text_leg17": {"n": max_text_n, "texts": max_text},
    "finance": {
        "total_promulguees": fin_total,
        "in_corpus": fin_corpus,
        "exclues": fin_excl,
        "struct_hors_corpus_defA": len(struct_hors_corpus_A),
        "struct_hors_corpus_defB": len(struct_hors_corpus_B),
        "fin_excl_493_trace_leg17": fin_excl_493_trace_leg17,
        "rows": fin,
    },
    "dossier_493_motions_leg17": dossier_493_motions,
}

with open(f"{OUT}/v6.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

# ---- console summary ----
print("=== RECENSEMENT ===")
print(json.dumps(R, ensure_ascii=False, indent=2))
print("\n=== ADOPTED ===", adopted)
print("\n=== CARD DATE leg16 ===", cd16["hist"], "max", cd16["max"], cd16["max_date"], "multi", len(cd16["dates_multi"]))
print("=== CARD DATE leg17 ===", cd17["hist"], "max", cd17["max"], "multi", len(cd17["dates_multi"]))
print("=== CARD DATE combined ===", comb_hist)
print("\n=== LINKS ===", json.dumps(result["links"], ensure_ascii=False, indent=2))
print("=== card_event_493_leg17 ===", result["card_event_493_leg17"])
print("=== max text leg17 ===", max_text_n, [t["titreChemin"] for t in max_text])
print("\n=== FINANCE ===", "total", fin_total, "corpus", fin_corpus, "exclues", fin_excl,
      "struct_hors_corpus_A", len(struct_hors_corpus_A), "struct_hors_corpus_B", len(struct_hors_corpus_B),
      "fin_excl_493_trace_leg17", len(fin_excl_493_trace_leg17))
for r in fin:
    print(f"  leg{r['leg']} corpus={r['in_corpus']!s:5} {r['procedure'][:30]:30} | {r['titre'][:55]}")
