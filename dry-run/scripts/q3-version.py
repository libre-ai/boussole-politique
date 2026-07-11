#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
q3-version — Décalage version votée / version promulguée.
Valide §2.1 de la revue (version votée ≠ version promulguée).

Mesure, sur le corpus FIGÉ des 159 lois jugeables, combien ont un texte voté
(au vote de référence) potentiellement DIFFÉRENT du texte promulgué :
  (a) saisine du Conseil constitutionnel (+ détection censure via CC-CONCLUSION/statutConclusion) ;
  (b) passage en CMP avec vote de référence en lecture antérieure
      (ref_acte = AN1-DEBATS-DEC alors que le dossier a une CMP postérieure) ;
  (c) nouvelle lecture / lecture définitive (rang de lecture plus tardif existe).

On NE re-dérive PAS le corpus : on consomme out/corpus.json. On enrichit chaque
loi avec les actes CC du dossier (anlib.load_all_dossiers()[uid].raw) et on
ré-apparie les scrutins d'ensemble de lecture postérieure non liés (voteRefs nuls).
"""
from __future__ import annotations
from workspace_paths import DATA_DIR, DRY_RUN_DIR, OUT_DIR, REPO_ROOT, SCRIPTS_DIR
import sys, json, os
sys.path.insert(0, str(SCRIPTS_DIR))
import anlib
from collections import Counter, defaultdict

OUT = str(OUT_DIR)
CORPUS = os.path.join(OUT, "corpus.json")

# --- statutConclusion.fam_code -> interprétation "le texte promulgué diffère du texte voté ?" ---
STATUT_LIB = {
    "TCD01": "Conforme",                 # texte intact -> PAS de drift dû au CC
    "TCD02": "Partiellement conforme",   # CENSURE PARTIELLE -> articles retirés -> DRIFT
    "TCD03": "Conforme avec réserve",    # réserves d'interprétation -> texte intact mais portée bornée
    # (aucune décision "Non conforme"/censure totale dans le corpus)
}
STATUT_CENSURE = {"TCD02"}  # familles qui retirent des dispositions du texte promulgué

# rang de lecture (repris d'anlib._ACTE_RANG) : plus haut = plus tardif dans la navette
ACTE_RANG = anlib._ACTE_RANG

# marqueurs de lecture (parse_lecture) signalant un scrutin d'ensemble POSTÉRIEUR au 1er passage
# NB: la leg 16 (été 2022) écrit parfois "texte de la commission paritaire" (sans "mixte").
LECTURE_POSTERIEURE = {
    "texte de la commission mixte paritaire", "texte de la commission paritaire",
    "nouvelle lecture", "lecture definitive", "deuxieme lecture", "troisieme lecture",
}
# codeActe de décision AN postérieure -> date à laquelle chercher un scrutin d'ensemble non lié
POSTERIOR_DEC_ACTES = ("CMP-DEBATS-AN-DEC", "ANNLEC-DEBATS-DEC", "ANLDEF-DEBATS-DEC",
                       "AN2-DEBATS-DEC", "AN3-DEBATS-DEC")


def walk_actes(node):
    if isinstance(node, dict):
        if "codeActe" in node:
            yield node
        for v in node.values():
            yield from walk_actes(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_actes(v)


def cc_conclusions(dossier):
    """Retourne la liste des conclusions CC d'un dossier : (fam_code, libelle, numDecision, annee, url)."""
    out = []
    dd = dossier.raw.get("dossierParlementaire") or {}
    for a in walk_actes(dd.get("actesLegislatifs")):
        if a.get("codeActe") == "CC-CONCLUSION":
            sc = a.get("statutConclusion") or {}
            fam = sc.get("fam_code") if isinstance(sc, dict) else None
            lib = sc.get("libelle") if isinstance(sc, dict) else (sc if isinstance(sc, str) else None)
            out.append({
                "fam_code": fam, "libelle": lib,
                "num_decision": a.get("numDecision"), "annee": a.get("anneeDecision"),
                "url": a.get("urlConclusion"),
            })
    return out


def cc_saisines(dossier):
    """Codes de saisine CC présents + cas (qui a saisi)."""
    codes = sorted(c for c in dossier.acte_codes if c.startswith("CC-SAISIE") or c == "CC")
    cas = set()
    dd = dossier.raw.get("dossierParlementaire") or {}
    for a in walk_actes(dd.get("actesLegislatifs")):
        ca = a.get("codeActe") or ""
        if ca.startswith("CC-SAISIE"):
            cs = a.get("casSaisine")
            if isinstance(cs, dict) and cs.get("libelle"):
                cas.add(cs["libelle"])
    return codes, sorted(cas)


def acte_dates(dossier):
    """codeActe -> liste de dates (ISO court) présentes pour cet acte dans le dossier."""
    out = defaultdict(list)
    dd = dossier.raw.get("dossierParlementaire") or {}
    for a in walk_actes(dd.get("actesLegislatifs")):
        ca = a.get("codeActe")
        da = a.get("dateActe")
        if ca and da:
            out[ca].append(da[:10])
    return out


def find_unlinked_posterior_scrutin(dossier, sidx, ref_date, ref_numero, posterior_dates):
    """Cherche un scrutin public d'ensemble de LECTURE POSTÉRIEURE (CMP / NLEC / LDEF / 2e lecture)
    qui correspond au dossier mais n'est PAS le vote de référence (voteRef nul = non lié).

    Passe 1 (titre) : recouvrement de tokens significatifs, rappel >= 0.45, postérieur à ref_date.
    Passe 2 (date-ancrée) : si une décision AN postérieure (CMP/NLEC/LDEF...) a une date connue,
      on accepte un scrutin d'ensemble CE JOUR-LÀ avec marqueur de lecture postérieure et >=2 tokens
      partagés (seuil de rappel relâché — gère les titres très raccourcis/dérivés).
    Retourne le meilleur candidat (le plus tardif) avec sa méthode, ou None."""
    toks = anlib._content_tokens(dossier.titre)
    if not toks:
        return None
    pdates = set(posterior_dates or [])
    best = None  # (date, num, leg, lec, shared, recall, sort, objet, methode)
    for (leg, num), s in sidx.items():
        if num == ref_numero:
            continue
        if s.type_code not in ("SPO", "SPS") or not s.is_ensemble:
            continue
        lec = s.lecture or ""
        if lec not in LECTURE_POSTERIEURE:
            continue
        otoks = anlib._content_tokens(s.objet)
        shared = len(toks & otoks)
        recall = shared / max(1, len(toks))
        methode = None
        if s.date > ref_date and shared >= 2 and recall >= 0.45:
            methode = "titre"
        elif s.date in pdates and shared >= 2:
            methode = "date+titre"
        if methode is None:
            continue
        cand = (s.date, num, leg, lec, shared, recall, s.sort, s.objet, methode)
        # préférer "titre" (plus fiable) puis le plus tardif
        if best is None or (methode == "titre" and best[8] != "titre") or \
           (methode == best[8] and cand[0] > best[0]):
            best = cand
    if best:
        return {"date": best[0], "numero": best[1], "leg": best[2], "lecture": best[3],
                "shared_tokens": best[4], "recall": round(best[5], 2), "sort": best[6],
                "objet": best[7], "methode": best[8]}
    return None


def main():
    corpus = json.load(open(CORPUS, encoding="utf-8"))
    lois = corpus["lois"]
    dossiers = anlib.load_all_dossiers()
    sidx = anlib.load_all_scrutins()

    N = len(lois)
    by_leg = {16: [l for l in lois if l["ref_leg"] == 16],
              17: [l for l in lois if l["ref_leg"] == 17]}

    enriched = []
    for l in lois:
        uid = l["dossier_uid"]
        d = dossiers.get(uid)
        rec = dict(l)  # shallow copy of corpus fields
        rec.pop("votes", None)
        rec["votes_actes"] = [v["acte"] for v in l["votes"]]
        # --- (a) CC ---
        concls = cc_conclusions(d) if d else []
        codes_saisine, cas_saisine = (cc_saisines(d) if d else ([], []))
        rec["cc_codes_saisine"] = codes_saisine
        rec["cc_cas_saisine"] = cas_saisine
        rec["cc_conclusions"] = concls
        fams = [c["fam_code"] for c in concls if c["fam_code"]]
        rec["cc_censure_partielle"] = any(f in STATUT_CENSURE for f in fams)
        rec["cc_conforme"] = bool(fams) and all(f == "TCD01" for f in fams)
        rec["cc_reserve"] = any(f == "TCD03" for f in fams)
        rec["cc_saisine_sans_conclusion"] = (l["saisine_cc"] and not concls)
        # --- (b) CMP avec vote de réf en lecture antérieure ---
        has_cmp_an_dec = bool(d and "CMP-DEBATS-AN-DEC" in d.acte_codes)
        rec["has_cmp_an_dec_act"] = has_cmp_an_dec
        ref_in_cmp = l["ref_acte"] == "CMP-DEBATS-AN-DEC"
        # drift CMP "mandat (b)" : référence = 1ère lecture AN MAIS le dossier a une CMP
        rec["drift_cmp_ref_premiere_lecture"] = (
            l["ref_acte"] == "AN1-DEBATS-DEC" and l["has_cmp"]
        )
        # --- (c) nouvelle lecture / lecture définitive postérieure au vote de réf ---
        rec["has_nlec_an_dec_act"] = bool(d and "ANNLEC-DEBATS-DEC" in d.acte_codes)
        rec["has_ldef_an_dec_act"] = bool(d and "ANLDEF-DEBATS-DEC" in d.acte_codes)
        ref_rang = ACTE_RANG.get(l["ref_acte"], 0)
        # rang max parmi TOUS les actes de décision AN du dossier (pas seulement ceux liés)
        dossier_decision_actes = [c for c in (d.acte_codes if d else set())
                                  if c in ACTE_RANG]
        max_rang_dossier = max((ACTE_RANG.get(c, 0) for c in dossier_decision_actes), default=0)
        rec["ref_rang"] = ref_rang
        rec["max_rang_dossier"] = max_rang_dossier
        # drift "dossier" : une décision AN de lecture plus tardive existe que celle votée en réf
        rec["drift_lecture_posterieure_dossier"] = max_rang_dossier > ref_rang
        # --- preuve : scrutin d'ensemble postérieur réel mais non lié ? ---
        ref_date = max(v["date"] for v in l["votes"])  # date du vote de réf (dernier lié)
        unlinked = None
        if rec["drift_lecture_posterieure_dossier"] and d:
            adates = acte_dates(d)
            posterior_dates = []
            for ca in POSTERIOR_DEC_ACTES:
                posterior_dates.extend(adates.get(ca, []))
            unlinked = find_unlinked_posterior_scrutin(
                d, sidx, ref_date, l["ref_numero"], posterior_dates)
        rec["unlinked_posterior_scrutin"] = unlinked
        enriched.append(rec)

    # ----------------------------------------------------------------------
    # AGRÉGATS
    # ----------------------------------------------------------------------
    def agg(subset):
        n = len(subset)
        saisine = [l for l in subset if l["saisine_cc"]]
        censure = [l for l in subset if l["cc_censure_partielle"]]
        conforme = [l for l in subset if l["cc_conforme"]]
        reserve = [l for l in subset if l["cc_reserve"]]
        sans_concl = [l for l in subset if l["cc_saisine_sans_conclusion"]]
        cmp_ref1 = [l for l in subset if l["drift_cmp_ref_premiere_lecture"]]
        drift_dossier = [l for l in subset if l["drift_lecture_posterieure_dossier"]]
        drift_proven = [l for l in subset if l["unlinked_posterior_scrutin"]]
        drift_corpus = [l for l in subset if l["version_drift"]]
        # UNION "texte jugé != texte promulgué" : censure partielle OU lecture postérieure existe
        union = [l for l in subset if l["cc_censure_partielle"] or l["drift_lecture_posterieure_dossier"]]
        return {
            "n": n,
            "saisine_cc": len(saisine),
            "cc_censure_partielle": len(censure),
            "cc_conforme": len(conforme),
            "cc_reserve": len(reserve),
            "cc_saisine_sans_conclusion": len(sans_concl),
            "cmp_present": sum(1 for l in subset if l["has_cmp"]),
            "drift_cmp_ref_premiere_lecture": len(cmp_ref1),
            "drift_lecture_posterieure_dossier": len(drift_dossier),
            "drift_prouve_par_scrutin_non_lie": len(drift_proven),
            "version_drift_corpus_flag": len(drift_corpus),
            "union_texte_juge_diff_promulgue": len(union),
            "union_frac": round(len(union) / n, 4) if n else 0.0,
        }

    out = {
        "note": "Décalage version votée/promulguée — valide revue §2.1. Corpus figé out/corpus.json (159 lois).",
        "statut_cc_legende": STATUT_LIB,
        "total": agg(lois_to_rec(enriched)),
        "leg16": agg([r for r in enriched if r["ref_leg"] == 16]),
        "leg17": agg([r for r in enriched if r["ref_leg"] == 17]),
        "exemples": {},
        "lois_enrichies": enriched,
    }

    # --- exemples nommés réels ---
    def ex(r):
        return {
            "leg": r["ref_leg"], "uid": r["dossier_uid"], "titre": r["titre"],
            "ref_acte": r["ref_acte"], "ref_numero": r["ref_numero"],
            "cc_conclusions": r["cc_conclusions"],
            "drift_cmp_ref_premiere_lecture": r["drift_cmp_ref_premiere_lecture"],
            "drift_lecture_posterieure_dossier": r["drift_lecture_posterieure_dossier"],
            "unlinked_posterior_scrutin": r["unlinked_posterior_scrutin"],
        }

    out["exemples"]["cc_censure_partielle"] = [
        ex(r) for r in enriched if r["cc_censure_partielle"]
    ]
    out["exemples"]["drift_cmp_ref_premiere_lecture"] = [
        ex(r) for r in enriched if r["drift_cmp_ref_premiere_lecture"]
    ]
    out["exemples"]["drift_prouve_par_scrutin_non_lie"] = [
        ex(r) for r in enriched if r["unlinked_posterior_scrutin"]
    ]

    # --- cas hors corpus : la loi immigration 2024 (exclue car voteRefs nuls) ---
    immig = dossiers.get("DLR5L16N47118")
    if immig:
        out["hors_corpus_immigration_2024"] = {
            "uid": "DLR5L16N47118",
            "titre": immig.titre,
            "promulguee": immig.promulguee,
            "saisine_cc": immig.saisine_cc,
            "has_cmp": immig.has_cmp,
            "cc_conclusions": cc_conclusions(immig),
            "dans_corpus": any(l["dossier_uid"] == "DLR5L16N47118" for l in lois),
            "raison_exclusion": "voteRefs AN nuls (AN1-DEBATS-DEC et CMP-DEBATS-AN-DEC sans voteRef) -> non jugeable par la règle voteRefs",
        }

    json.dump(out, open(os.path.join(OUT, "q3-version.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # ----------------------------------------------------------------------
    # CONSOLE
    # ----------------------------------------------------------------------
    print("=== TOTAL (159) ===")
    for k, v in out["total"].items():
        print(f"  {k:42s} {v}")
    print("\n=== LEG 16 ===")
    for k, v in out["leg16"].items():
        print(f"  {k:42s} {v}")
    print("\n=== LEG 17 ===")
    for k, v in out["leg17"].items():
        print(f"  {k:42s} {v}")
    print("\nCensure partielle CC:", len(out["exemples"]["cc_censure_partielle"]))
    print("Immigration 2024 dans corpus ?",
          out.get("hors_corpus_immigration_2024", {}).get("dans_corpus"))
    return out


def lois_to_rec(enriched):
    return enriched


if __name__ == "__main__":
    main()
