"""Fige le corpus jugeable en artefact JSON (consommé par les agents du workflow) +
validations croisées finales de la fondation."""
import anlib, json, collections, os

c = anlib.build_corpus()
lois = c["lois"]
sidx = anlib.load_all_scrutins()

# --- per-législature (selon la législature du vote de référence) ---
def ref_leg(l):
    for a, s in l.votes:
        if s.numero == l.ref_dernier:
            return s.legislature
    return None
by_leg = collections.Counter(ref_leg(l) for l in lois)
print("Corpus jugeable par législature (du vote de référence):", dict(by_leg))

# --- validation croisée : voteRefs vs détection-ensemble indépendante ---
# tout scrutin AN public d'ensemble adopté devrait, s'il conclut une loi promulguée,
# apparaître comme vote de réf de cette loi. On mesure le recouvrement.
all_scrutins_16 = anlib.load_scrutins(16)
all_scrutins_17 = anlib.load_scrutins(17)
ens_adopte = [s for s in (all_scrutins_16 + all_scrutins_17)
              if s.is_ensemble and s.type_code in ("SPO", "SPS") and s.sort == "adopté"]
ref_numeros = {(s.legislature, s.numero) for l in lois for _, s in l.votes}
ens_couverts = sum(1 for s in ens_adopte if (s.legislature, s.numero) in ref_numeros)
print(f"\nScrutins ensemble publics ADOPTÉS (toutes procédures) = {len(ens_adopte)}")
print(f"  dont rattachés à une loi jugeable via voteRefs = {ens_couverts}")
print(f"  non rattachés (résolutions, lois non promulguées, navette en cours...) = {len(ens_adopte) - ens_couverts}")

# --- audit des 82 'sans voteRef AN' : par procédure (vraies exclusions ?) ---
dossiers = anlib.load_all_dossiers()
prom_loi = {u: d for u, d in dossiers.items() if d.is_loi and d.promulguee}
sans = {u: d for u, d in prom_loi.items() if not d.an_vote_refs()}
print(f"\nPROM-loi sans voteRef AN = {len(sans)} ; par procédure:")
for proc, n in collections.Counter(d.procedure for d in sans.values()).most_common():
    print(f"   {n:3d}  {proc}")
# combien ont au moins un acte de promulgation mais procédure ratification (= traités, vote main levée)
print("   -> dont ratifications:", sum(d.is_ratification for d in sans.values()))

# --- export JSON figé ---
def serialize(l):
    return {
        "dossier_uid": l.dossier_uid, "titre": l.titre, "procedure": l.procedure,
        "ref_leg": ref_leg(l), "ref_numero": l.ref_dernier, "ref_acte": l.ref_dernier_acte,
        "ref_solennel": l.ref_solennel, "saisine_cc": l.saisine_cc, "has_cmp": l.has_cmp,
        "lecture_definitive": l.lecture_definitive, "nouvelle_lecture": l.nouvelle_lecture,
        "is_ratification": l.is_ratification, "version_drift": l.version_drift,
        "votes": [{"acte": a, "leg": s.legislature, "numero": s.numero, "date": s.date,
                   "type": s.type_code, "sort": s.sort,
                   "pour": s.d_pour, "contre": s.d_contre, "abst": s.d_abst,
                   "nonvotant": s.d_nonvotant, "votants": s.nb_votants,
                   "has_mise_au_point": s.has_mise_au_point} for a, s in l.votes],
    }
out = {
    "generated_note": "Corpus jugeable via lien autoritatif voteRefs. Voir SCHEMA-NOTES.md.",
    "funnel": c["funnel"], "by_leg": dict(by_leg),
    "n_lois": len(lois), "lois": [serialize(l) for l in lois],
}
path = os.path.join(os.path.dirname(__file__), "..", "out", "corpus.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)
print(f"\n✓ corpus figé -> {os.path.relpath(path)} ({os.path.getsize(path)//1024} Ko)")
