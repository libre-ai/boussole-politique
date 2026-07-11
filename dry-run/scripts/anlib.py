"""
anlib — bibliothèque de chargement/normalisation de l'open data AN pour le dry-run.

Colonne vertébrale du dry-run : charge scrutins + dossiers + acteurs d'une législature,
normalise les pièges de format (objet-vs-tableau, apostrophes), et expose :
  - load_scrutins(leg) -> list[Scrutin]
  - load_dossiers(leg) -> dict[uid -> Dossier]
  - link_scrutin_to_dossier(...) : dossierRef direct, sinon matching de titre
  - build_corpus(leg) : lois jugeables + vote(s) de référence (règle spec v0.1)

Aucune dépendance externe (stdlib only). Établi par inspection directe — voir SCHEMA-NOTES.md.
"""
from __future__ import annotations
import json, os, re, glob, unicodedata
from dataclasses import dataclass, field
from functools import lru_cache

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
SIEGES_AN = 577

# ---------------------------------------------------------------------------
# Normalisation de format
# ---------------------------------------------------------------------------

def as_list(x):
    """XML->JSON : un singleton devient un objet, plusieurs une liste. None -> []."""
    if x is None:
        return []
    return x if isinstance(x, list) else [x]

def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def norm_title(s: str) -> str:
    """Normalise un titre pour matching : apostrophes, accents, casse, espaces, ponctuation."""
    if not s:
        return ""
    s = s.replace("’", "'").replace("ʼ", "'")
    s = _strip_accents(s).lower()
    s = re.sub(r"[^a-z0-9'’ ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

# suffixes de lecture dans l'objet d'un scrutin d'ensemble (précieux : identifient la lecture)
LECTURE_SUFFIXES = [
    "premiere lecture", "deuxieme lecture", "nouvelle lecture", "lecture definitive",
    "texte de la commission mixte paritaire", "lecture unique",
]

def parse_lecture(objet_libelle: str) -> str | None:
    """Extrait le marqueur de lecture entre parenthèses d'un objet de scrutin d'ensemble."""
    m = re.search(r"\(([^)]*)\)\s*\.?\s*$", objet_libelle or "")
    if not m:
        return None
    inside = norm_title(m.group(1))
    for suf in LECTURE_SUFFIXES:
        if suf in inside:
            return suf
    return inside or None

# l'objet d'un scrutin d'ensemble : "l'ensemble de la {proposition de loi ...} {titre} ({lecture})."
_ENSEMBLE_RE = re.compile(r"l'ensemble\s+(?:de\s+la|du|des|de\s+l'|de)\s+", re.I)

def is_ensemble(objet_libelle: str) -> bool:
    n = (objet_libelle or "").replace("’", "'")
    return bool(re.search(r"l'ensemble\b", n, re.I))

# ---------------------------------------------------------------------------
# Chargement
# ---------------------------------------------------------------------------

@dataclass
class Scrutin:
    numero: int
    date: str
    legislature: int
    type_code: str          # SPO | SPS | (motion) ...
    type_libelle: str
    sort: str               # adopté | rejeté
    objet: str
    dossier_ref: str | None  # depuis objet.dossierLegislatif.dossierRef (peut être None)
    titre: str
    demandeur: str
    nb_votants: int
    suffrages_exprimes: int
    suffrages_requis: int
    d_pour: int
    d_contre: int
    d_abst: int
    d_nonvotant: int
    has_mise_au_point: bool
    raw: dict = field(repr=False, default=None)

    @property
    def lecture(self):
        return parse_lecture(self.objet)

    @property
    def is_ensemble(self):
        return is_ensemble(self.objet)

    def positions_nominales(self):
        """Itère (acteur_ref, position, par_delegation, groupe_ref) depuis la ventilation.
        position ∈ {pour, contre, abstention, nonvotant}. groupe_ref = groupe AU MOMENT DU VOTE."""
        vv = self.raw["scrutin"].get("ventilationVotes") or {}
        organe = vv.get("organe") or {}
        groupes = (organe.get("groupes") or {}).get("groupe")
        for g in as_list(groupes):
            gref = g.get("organeRef")
            dn = (g.get("vote") or {}).get("decompteNominatif") or {}
            for key, pos in (("pours", "pour"), ("contres", "contre"),
                             ("abstentions", "abstention"), ("nonVotants", "nonvotant")):
                bucket = dn.get(key)
                if not bucket:
                    continue
                votants = bucket.get("votant") if isinstance(bucket, dict) else bucket
                for v in as_list(votants):
                    if not isinstance(v, dict):
                        continue
                    yield (v.get("acteurRef"), pos, v.get("parDelegation") == "true"
                           or v.get("parDelegation") is True, gref, v.get("causePositionVote"))

def _int(x, default=0):
    try:
        return int(x)
    except (TypeError, ValueError):
        return default

@lru_cache(maxsize=None)
def load_scrutins(leg: int) -> tuple:
    out = []
    for path in glob.glob(os.path.join(DATA, f"scrutins-{leg}", "json", "*.json")):
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
        s = raw["scrutin"]
        objet = s.get("objet") or {}
        dl = objet.get("dossierLegislatif")
        dref = dl.get("dossierRef") if isinstance(dl, dict) else None
        syn = (s.get("syntheseVote") or {})
        dec = (syn.get("decompte") or {})
        mp = s.get("miseAuPoint") or {}
        has_mp = any(mp.get(k) for k in ("pours", "contres", "abstentions", "nonVotants", "nonVotantsVolontaires"))
        out.append(Scrutin(
            numero=_int(s.get("numero")),
            date=s.get("dateScrutin", ""),
            legislature=_int(s.get("legislature"), leg),
            type_code=(s.get("typeVote") or {}).get("codeTypeVote", ""),
            type_libelle=(s.get("typeVote") or {}).get("libelleTypeVote", ""),
            sort=(s.get("sort") or {}).get("code", ""),
            objet=objet.get("libelle", "") or "",
            dossier_ref=dref,
            titre=s.get("titre", "") or "",
            demandeur=((s.get("demandeur") or {}).get("texte") or ""),
            nb_votants=_int(syn.get("nombreVotants")),
            suffrages_exprimes=_int(syn.get("suffragesExprimes")),
            suffrages_requis=_int(syn.get("nbrSuffragesRequis")),
            d_pour=_int(dec.get("pour")), d_contre=_int(dec.get("contre")),
            d_abst=_int(dec.get("abstentions")), d_nonvotant=_int(dec.get("nonVotants")),
            has_mise_au_point=has_mp,
            raw=raw,
        ))
    out.sort(key=lambda s: (s.date, s.numero))
    return tuple(out)

# Procédures qui produisent une LOI (≠ résolution, rapport, engagement de responsabilité…)
PROC_LOI = {
    "Proposition de loi ordinaire", "Projet de loi ordinaire",
    "Projet ou proposition de loi organique", "Projet ou proposition de loi constitutionnelle",
    "Projet de ratification des traités et conventions",
    "Projet de loi de finances rectificative", "Projet de loi de finances de l'année",
    "Projet de loi de financement de la sécurité sociale",
    "Projet de loi relative aux résultats de la gestion et portant approbation des comptes",
    "Proposition de loi présentée en application de l'article 11 de la Constitution",
}
PROC_RATIFICATION = "Projet de ratification des traités et conventions"

def _walk_actes(node):
    """Parcours récursif de l'arbre actesLegislatifs ; yield chaque acte (dict avec codeActe)."""
    if isinstance(node, dict):
        if "codeActe" in node:
            yield node
        for v in node.values():
            yield from _walk_actes(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk_actes(v)

VOTEREF_RE = re.compile(r"VTANR5L(\d+)V(\d+)")

@dataclass
class Dossier:
    uid: str
    titre: str
    titre_chemin: str
    procedure: str
    acte_codes: set         # tous les codeActe présents
    vote_refs: list = field(default_factory=list)  # [(acte_code, leg, numero)] — lien autoritatif
    raw: dict = field(repr=False, default=None)

    def an_vote_refs(self):
        """voteRefs sur des décisions AN (exclut le Sénat). [(acte_code, leg, numero)]."""
        return [(c, l, n) for (c, l, n) in self.vote_refs
                if c.startswith("AN") or c.startswith("CMP-DEBATS-AN")]

    @property
    def is_loi(self):
        return self.procedure in PROC_LOI
    @property
    def is_ratification(self):
        return self.procedure == PROC_RATIFICATION
    @property
    def promulguee(self):
        return "PROM" in self.acte_codes
    @property
    def saisine_cc(self):
        return any(c.startswith("CC-SAISIE") or c == "CC" for c in self.acte_codes)
    @property
    def has_cmp(self):
        return "CMP" in self.acte_codes
    @property
    def lecture_definitive(self):
        return any(c.startswith("ANLDEF") for c in self.acte_codes)
    @property
    def nouvelle_lecture(self):
        return any(c.startswith("ANNLEC") or c.startswith("SNNLEC") for c in self.acte_codes)
    @property
    def engagement_resp(self):  # 49.3 laisse une trace ? à confirmer dans l'analyse
        return any("49" in c or "ENGAGT" in c or "RESP" in c for c in self.acte_codes)

@lru_cache(maxsize=None)
def load_dossiers(leg: int) -> dict:
    out = {}
    for path in glob.glob(os.path.join(DATA, f"dossiers-{leg}", "json", "dossierParlementaire", "*.json")):
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
        d = raw.get("dossierParlementaire") or {}
        td = d.get("titreDossier") or {}
        codes = set()
        vote_refs = []
        for a in _walk_actes(d.get("actesLegislatifs")):
            codes.add(a["codeActe"])
            vr = a.get("voteRefs")
            if vr:
                for v in as_list(vr.get("voteRef") if isinstance(vr, dict) else vr):
                    ref = v if isinstance(v, str) else (v.get("voteRef") if isinstance(v, dict) else None)
                    m = VOTEREF_RE.search(ref or "")
                    if m:
                        vote_refs.append((a["codeActe"], int(m.group(1)), int(m.group(2))))
        uid = d.get("uid")
        if not uid:
            continue
        out[uid] = Dossier(
            uid=uid,
            titre=td.get("titre", "") or "",
            titre_chemin=td.get("titreChemin", "") or "",
            procedure=(d.get("procedureParlementaire") or {}).get("libelle", "") or "",
            acte_codes=codes,
            vote_refs=vote_refs,
            raw=raw,
        )
    return out

def load_all_dossiers() -> dict:
    """Fusionne les dumps dossiers de toutes les législatures disponibles (ils se chevauchent).
    Un dossier peut être référencé depuis plusieurs dumps ; on garde la version la plus complète."""
    merged = {}
    for leg in (16, 17):
        for uid, d in load_dossiers(leg).items():
            if uid not in merged or len(d.acte_codes) > len(merged[uid].acte_codes):
                merged[uid] = d
    return merged

def load_all_scrutins() -> dict:
    """Index (leg, numero) -> Scrutin sur toutes les législatures chargées."""
    idx = {}
    for leg in (16, 17):
        for s in load_scrutins(leg):
            idx[(s.legislature, s.numero)] = s
    return idx

# ---------------------------------------------------------------------------
# Lien scrutin -> dossier (dossierRef direct, sinon matching de titre)
# ---------------------------------------------------------------------------

# mots vides + boilerplate procédural à retirer avant matching par tokens
_STOP = set("""
le la les l un une des du de d a au aux et en pour sur dans par ou se sa son ses leur leurs
ce cette ces qui que dont au-x est aux à
ensemble proposition projet loi organique constitutionnelle resolution motion texte
visant relative relatif relatives relatifs portant tendant fixant creant instituant
premiere deuxieme troisieme nouvelle lecture definitive unique lectures
commission mixte paritaire adoptee adopte adoptees modifie modifiee senat assemblee nationale
partie article articles application alinea constitution gouvernement premiere
mesures diverses dispositions relatives portant
""".split())

def _content_tokens(s: str) -> set:
    """Tokens significatifs (boilerplate procédural retiré) pour matching scrutin<->dossier."""
    toks = norm_title(s).replace("'", " ").split()
    return {t for t in toks if len(t) >= 3 and t not in _STOP}

def build_title_index(dossiers: dict):
    """index : uid -> set de tokens significatifs (titre + titre_chemin)."""
    idx = {}
    for uid, d in dossiers.items():
        toks = _content_tokens(d.titre) | set(
            t for t in d.titre_chemin.replace("_", " ").split() if len(t) >= 3 and t not in _STOP)
        if toks:
            idx[uid] = toks
    return idx

def link_scrutin(s: Scrutin, dossiers: dict, title_idx, *, min_recall=0.6, min_shared=2) -> tuple:
    """Lie un scrutin à son dossier. dossierRef direct prioritaire ; sinon recouvrement de
    tokens significatifs (gère la dérive de titre). Retourne (uid, methode|raison)."""
    if s.dossier_ref:
        return (s.dossier_ref, "ref") if s.dossier_ref in dossiers else (None, "ref_orpheline")
    otoks = _content_tokens(s.objet)
    if not otoks:
        return (None, "non_lie")
    best_uid, best_score, best_shared, second = None, 0.0, 0, 0.0
    for uid, dtoks in title_idx.items():
        shared = len(dtoks & otoks)
        if shared < min_shared:
            continue
        recall = shared / len(dtoks)          # part des tokens du dossier retrouvés dans l'objet
        if recall > best_score:
            second = best_score
            best_uid, best_score, best_shared = uid, recall, shared
        elif recall > second:
            second = recall
    # accepter si rappel suffisant, assez de tokens partagés, et marge sur le 2e candidat
    if best_uid and best_score >= min_recall and best_shared >= min_shared and (best_score - second) >= 0.15:
        return (best_uid, "titre")
    return (None, "non_lie")

# ---------------------------------------------------------------------------
# Corpus jugeable + vote de référence (règle spec v0.1 §2)
# ---------------------------------------------------------------------------

@dataclass
class LoiJugeable:
    dossier_uid: str
    titre: str
    procedure: str
    promulguee: bool
    saisine_cc: bool
    has_cmp: bool
    lecture_definitive: bool
    nouvelle_lecture: bool
    is_ratification: bool
    # votes AN sur l'ensemble liés par voteRefs, triés par date : [(acte_code, Scrutin)]
    votes: list
    ref_dernier: int          # numero du DERNIER vote AN d'ensemble (règle spec v0.1)
    ref_dernier_acte: str     # code d'acte du vote de référence (= quelle lecture)
    ref_solennel: int | None  # numero du dernier vote SOLENNEL d'ensemble (règle alt. revue)
    version_drift: bool       # le vote de réf n'est PAS la dernière lecture (CMP/NLEC postérieure)

# actes de décision AN qui portent (en principe) sur l'ensemble d'un texte
_DECISION_ACTES = ("AN1-DEBATS-DEC", "AN2-DEBATS-DEC", "AN3-DEBATS-DEC",
                   "ANNLEC-DEBATS-DEC", "ANLDEF-DEBATS-DEC", "CMP-DEBATS-AN-DEC", "ANLUNI-DEBATS-DEC")
# rang de lecture pour détecter la lecture FINALE (plus haut = plus tardif dans la navette)
_ACTE_RANG = {"AN1-DEBATS-DEC": 1, "AN2-DEBATS-DEC": 3, "AN3-DEBATS-DEC": 5,
              "ANLUNI-DEBATS-DEC": 1, "CMP-DEBATS-AN-DEC": 6, "ANNLEC-DEBATS-DEC": 7,
              "ANLDEF-DEBATS-DEC": 8}

def build_corpus(prom_only=True):
    """Corpus jugeable via le lien AUTORITATIF voteRefs (toutes législatures fusionnées).
    Règle spec v0.1 : loi promulguée + ≥1 scrutin public AN sur l'ensemble ;
    vote de référence = dernier scrutin public AN d'ensemble."""
    dossiers = load_all_dossiers()
    sidx = load_all_scrutins()
    lois = []
    funnel = {"prom_loi": 0, "sans_voteref_an": 0, "voteref_non_ensemble": 0,
              "voteref_non_public": 0, "jugeable": 0}
    for uid, d in dossiers.items():
        if not d.is_loi:
            continue
        if prom_only and not d.promulguee:
            continue
        funnel["prom_loi"] += 1
        an_refs = d.an_vote_refs()
        if not an_refs:
            funnel["sans_voteref_an"] += 1
            continue
        votes = []
        for acte, leg, num in an_refs:
            s = sidx.get((leg, num))
            if s is None:
                continue
            votes.append((acte, s))
        # ne garder que les votes publics sur l'ensemble
        votes_ens = [(a, s) for (a, s) in votes
                     if s.type_code in ("SPO", "SPS") and s.is_ensemble]
        if not votes_ens:
            # le dossier a des voteRefs AN mais aucun n'est un vote public d'ensemble
            if any(s.is_ensemble for _, s in votes):
                funnel["voteref_non_public"] += 1
            else:
                funnel["voteref_non_ensemble"] += 1
            continue
        funnel["jugeable"] += 1
        votes_ens.sort(key=lambda x: (x[1].date, x[1].numero))
        ref_acte, ref_s = votes_ens[-1]
        solennels = [(a, s) for (a, s) in votes_ens if s.type_code == "SPS"]
        # version drift : le vote de réf n'est pas la lecture finale du dossier
        max_rang = max((_ACTE_RANG.get(a, 0) for a, _ in votes_ens), default=0)
        drift = _ACTE_RANG.get(ref_acte, 0) < max_rang
        lois.append(LoiJugeable(
            dossier_uid=uid, titre=d.titre, procedure=d.procedure,
            promulguee=d.promulguee, saisine_cc=d.saisine_cc, has_cmp=d.has_cmp,
            lecture_definitive=d.lecture_definitive, nouvelle_lecture=d.nouvelle_lecture,
            is_ratification=d.is_ratification,
            votes=votes_ens, ref_dernier=ref_s.numero, ref_dernier_acte=ref_acte,
            ref_solennel=(solennels[-1][1].numero if solennels else None),
            version_drift=drift,
        ))
    return {"dossiers_total": len(dossiers), "funnel": funnel, "lois": lois}

if __name__ == "__main__":
    c = build_corpus()
    f = c["funnel"]
    print(f"dossiers fusionnés={c['dossiers_total']}  PROM-loi={f['prom_loi']}")
    print(f"  - sans voteRef AN         : {f['sans_voteref_an']}")
    print(f"  - voteRef non-ensemble    : {f['voteref_non_ensemble']}")
    print(f"  - voteRef ensemble non-pub: {f['voteref_non_public']}")
    print(f"  => CORPUS JUGEABLE        : {f['jugeable']}")
    lois = c["lois"]
    print(f"\nsaisine CC={sum(l.saisine_cc for l in lois)}  CMP={sum(l.has_cmp for l in lois)}  "
          f"lecture def={sum(l.lecture_definitive for l in lois)}  ratif={sum(l.is_ratification for l in lois)}")
    print(f"version drift (réf ≠ dernière lecture)={sum(l.version_drift for l in lois)}")
    print(f"ref via solennel disponible={sum(l.ref_solennel is not None for l in lois)}")
    from collections import Counter
    print("acte du vote de référence:", dict(Counter(l.ref_dernier_acte for l in lois)))
