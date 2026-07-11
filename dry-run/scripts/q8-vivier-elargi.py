#!/usr/bin/env python3
"""Q8 — Confrontation empirique du vivier VAA élargi sur les législatures 16 et 17.

Ce script ne sélectionne aucun énoncé. Il mesure le pool mécanique :
- votes d'ensemble liés à une procédure législative, y compris les textes rejetés ;
- premières parties budgétaires ;
- amendements, comme vivier secondaire nécessitant une curation « structurant » ;
- motions de censure, inventoriées dans une branche séparée hors score.

Aucune taxonomie thématique n'est disponible dans les dumps : la couverture thématique
reste donc explicitement NON PROUVÉE. Python reste ici l'oracle de dry-run ; l'ETL cible
sera réimplémenté en Rust après stabilisation du contrat.
"""
from __future__ import annotations

import collections
import glob
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRY_RUN = HERE.parent
OUT_DIR = DRY_RUN / "out"
OVERRIDES_PATH = DRY_RUN / "fixtures" / "vivier-link-overrides.json"
sys.path.insert(0, str(HERE))
import anlib  # noqa: E402

DISCRIMINANCE_DEFAULT = 0.20
PARTICIPATION_DEFAULT = 0.20
PUBLIC_TYPES = {"SPO", "SPS"}

LEG16_LABELS = {
    "PO800538": "RE",
    "PO800520": "RN",
    "PO800490": "LFI",
    "PO800508": "LR",
    "PO800484": "DEM",
    "PO800514": "HOR",
    "PO830170": "SOC",
    "PO800502": "GDR",
    "PO800532": "LIOT",
    "PO800526": "ECO",
    "PO793087": "NI",
    "PO800496": "GDR-old",
}
MAIN_GROUPS = {
    16: {"LFI", "GDR", "ECO", "SOC", "DEM", "RE", "HOR", "LIOT", "LR", "RN"},
    17: {"LFI-NFP", "GDR", "ECOS", "SOC", "DEM", "EPR", "HOR", "LIOT", "DR", "RN"},
}


def text(value):
    if isinstance(value, dict):
        return value.get("#text") or value.get("text") or ""
    return value or ""


def group_labels() -> dict[str, str]:
    labels = dict(LEG16_LABELS)
    pattern = os.path.join(anlib.DATA, "amo10-17", "json", "organe", "PO*.json")
    for path in glob.glob(pattern):
        with open(path, encoding="utf-8") as handle:
            organe = (json.load(handle).get("organe") or {})
        if organe.get("codeType") != "GP":
            continue
        uid = text(organe.get("uid"))
        if uid:
            labels[uid] = text(organe.get("libelleAbrev")) or text(organe.get("libelle")) or uid
    return labels


def classify_scope(scrutin: anlib.Scrutin) -> str:
    normalized = anlib.norm_title(scrutin.objet)
    if scrutin.type_code == "MOC":
        return "motion"
    # Une première partie peut aussi contenir « l'ensemble » : la catégorie budget prime.
    if "premiere partie" in normalized:
        return "premiere_partie"
    if scrutin.is_ensemble:
        return "ensemble"
    if re.search(r"\bamendement(?:s)?\b", normalized):
        return "amendement"
    if re.search(r"\bl'article\b|\barticle\s+(?:premier|unique|\d+)", normalized):
        return "article"
    return "autre"


class DossierLinker:
    """Lien rapide scrutin→dossier, sans masquer les ambiguïtés.

    Priorité : dossierRef direct, voteRef d'acte, puis matching de titre. Le matching
    reproduit les seuils d'anlib mais utilise un index inversé pour éviter O(S×D).
    """

    def __init__(self, dossiers: dict[str, anlib.Dossier], overrides: dict[tuple[int, int], str]):
        self.dossiers = dossiers
        self.overrides = overrides
        self.title_index = anlib.build_title_index(dossiers)
        self.inverted: dict[str, set[str]] = collections.defaultdict(set)
        for uid, tokens in self.title_index.items():
            for token in tokens:
                self.inverted[token].add(uid)
        self.vote_refs: dict[tuple[int, int], set[str]] = collections.defaultdict(set)
        for uid, dossier in dossiers.items():
            for _, leg, numero in dossier.an_vote_refs():
                self.vote_refs[(leg, numero)].add(uid)

    def link(self, scrutin: anlib.Scrutin) -> tuple[str | None, str, dict]:
        if scrutin.dossier_ref:
            if scrutin.dossier_ref in self.dossiers:
                return scrutin.dossier_ref, "dossier_ref", {}
            return None, "dossier_ref_orpheline", {"dossier_ref": scrutin.dossier_ref}

        refs = self.vote_refs.get((scrutin.legislature, scrutin.numero), set())
        if len(refs) == 1:
            return next(iter(refs)), "vote_ref", {}
        if len(refs) > 1:
            return None, "vote_ref_ambigu", {"candidats": sorted(refs)}

        override = self.overrides.get((scrutin.legislature, scrutin.numero))
        if override:
            if override not in self.dossiers:
                return None, "override_orphelin", {"dossier_uid": override}
            return override, "curated_override", {}

        object_tokens = anlib._content_tokens(scrutin.objet)
        candidates: set[str] = set()
        for token in object_tokens:
            candidates.update(self.inverted.get(token, set()))

        scored = []
        for uid in candidates:
            dossier_tokens = self.title_index[uid]
            shared = len(dossier_tokens & object_tokens)
            if shared >= 2:
                scored.append((shared / len(dossier_tokens), shared, uid))
        scored.sort(reverse=True)
        if not scored:
            return None, "non_lie", {}
        best_recall, best_shared, best_uid = scored[0]
        second_recall = scored[1][0] if len(scored) > 1 else 0.0
        detail = {
            "rappel": round(best_recall, 4),
            "tokens_partages": best_shared,
            "marge": round(best_recall - second_recall, 4),
        }
        if best_recall >= 0.60 and best_shared >= 2 and best_recall - second_recall >= 0.15:
            return best_uid, "titre", detail
        return None, "titre_ambigu", detail


@dataclass
class Candidate:
    legislature: int
    numero: int
    date: str
    scope: str
    type_vote: str
    sort: str
    objet: str
    dossier_uid: str | None
    dossier_titre: str | None
    procedure: str | None
    link_method: str
    pour: int
    contre: int
    abstentions: int
    non_votants: int
    exprimes: int
    votants: int
    part_minorite: float
    participation: float

    @property
    def passes_default(self) -> bool:
        return (
            self.exprimes > 0
            and self.part_minorite >= DISCRIMINANCE_DEFAULT
            and self.participation >= PARTICIPATION_DEFAULT
        )

    @property
    def is_linked_law(self) -> bool:
        return self.dossier_uid is not None and self.procedure in anlib.PROC_LOI


@dataclass
class Motion:
    legislature: int
    numero: int
    date: str
    article: str
    sort: str
    pour: int
    objet: str


def motion_article(scrutin: anlib.Scrutin) -> str:
    normalized = anlib.norm_title(scrutin.objet)
    if re.search(r"article\s+49\s+alinea\s+3", normalized):
        return "49.3"
    if re.search(r"article\s+49\s+alinea\s+2", normalized):
        return "49.2"
    return "inconnu"


def load_overrides() -> tuple[dict[tuple[int, int], str], dict]:
    raw = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
    overrides = {}
    for entry in raw.get("entries", []):
        key = (int(entry["scrutin"]["legislature"]), int(entry["scrutin"]["numero"]))
        if key in overrides:
            raise ValueError(f"override dupliqué pour {key}")
        overrides[key] = entry["dossier_uid"]
    return overrides, raw


def build_rows():
    dossiers = anlib.load_all_dossiers()
    overrides, overrides_raw = load_overrides()
    linker = DossierLinker(dossiers, overrides)
    candidates: list[Candidate] = []
    motions: list[Motion] = []
    all_scope = collections.Counter()
    link_diagnostics = collections.Counter()

    for leg in (16, 17):
        for scrutin in anlib.load_scrutins(leg):
            scope = classify_scope(scrutin)
            all_scope[(leg, scope)] += 1
            if scope == "motion":
                motions.append(Motion(
                    legislature=leg,
                    numero=scrutin.numero,
                    date=scrutin.date,
                    article=motion_article(scrutin),
                    sort=scrutin.sort,
                    pour=scrutin.d_pour,
                    objet=scrutin.objet,
                ))
                continue
            if scope not in {"ensemble", "premiere_partie", "amendement"}:
                continue

            uid, method, _ = linker.link(scrutin)
            link_diagnostics[(leg, scope, method)] += 1
            dossier = dossiers.get(uid) if uid else None
            exprimes = scrutin.d_pour + scrutin.d_contre
            votants = scrutin.d_pour + scrutin.d_contre + scrutin.d_abst
            candidates.append(Candidate(
                legislature=leg,
                numero=scrutin.numero,
                date=scrutin.date,
                scope=scope,
                type_vote=scrutin.type_code,
                sort=scrutin.sort,
                objet=scrutin.objet,
                dossier_uid=uid,
                dossier_titre=dossier.titre if dossier else None,
                procedure=dossier.procedure if dossier else None,
                link_method=method,
                pour=scrutin.d_pour,
                contre=scrutin.d_contre,
                abstentions=scrutin.d_abst,
                non_votants=scrutin.d_nonvotant,
                exprimes=exprimes,
                votants=votants,
                part_minorite=(min(scrutin.d_pour, scrutin.d_contre) / exprimes if exprimes else 0.0),
                participation=votants / anlib.SIEGES_AN,
            ))
    return candidates, motions, all_scope, link_diagnostics, overrides_raw


def count_by(rows, attribute):
    return dict(sorted(collections.Counter(getattr(row, attribute) for row in rows).items(), key=lambda item: str(item[0])))


def sensitivity(rows: list[Candidate]):
    result = []
    for discriminance in (0.10, 0.20, 0.30):
        for participation in (0.10, 0.20, 0.30, 0.50):
            selected = [
                row for row in rows
                if row.exprimes > 0
                and row.part_minorite >= discriminance
                and row.participation >= participation
            ]
            result.append({
                "discriminance_min": discriminance,
                "participation_min": participation,
                "n": len(selected),
                "ensemble": sum(row.scope == "ensemble" for row in selected),
                "premiere_partie": sum(row.scope == "premiere_partie" for row in selected),
                "amendement": sum(row.scope == "amendement" for row in selected),
                "adopte": sum(row.sort == "adopté" for row in selected),
                "rejete": sum(row.sort == "rejeté" for row in selected),
                "dossiers": len({row.dossier_uid for row in selected if row.dossier_uid}),
            })
    return result


def majority_by_group(scrutin: anlib.Scrutin, labels: dict[str, str]):
    counts = collections.defaultdict(collections.Counter)
    for _, position, _, group_ref, _ in scrutin.positions_nominales():
        if position in {"pour", "contre"} and group_ref:
            counts[labels.get(group_ref, group_ref)][position] += 1
    directions = {}
    for group, count in counts.items():
        if count["pour"] > count["contre"]:
            directions[group] = "pour"
        elif count["contre"] > count["pour"]:
            directions[group] = "contre"
        else:
            directions[group] = "egalite"
    return directions


def group_balance(rows: list[Candidate]):
    labels = group_labels()
    sidx = anlib.load_all_scrutins()
    result = {}
    for leg in (16, 17):
        counts = collections.defaultdict(collections.Counter)
        for row in rows:
            if row.legislature != leg:
                continue
            scrutin = sidx[(leg, row.numero)]
            for group, direction in majority_by_group(scrutin, labels).items():
                if group in MAIN_GROUPS[leg]:
                    counts[group][direction] += 1
        result[str(leg)] = {}
        for group in sorted(MAIN_GROUPS[leg]):
            count = counts[group]
            directional = count["pour"] + count["contre"]
            result[str(leg)][group] = {
                "pour": count["pour"],
                "contre": count["contre"],
                "egalite": count["egalite"],
                "n_directionnel": directional,
                "part_cote_minoritaire": round(min(count["pour"], count["contre"]) / directional, 4)
                if directional else None,
                "bidirectionnel": count["pour"] > 0 and count["contre"] > 0,
            }
    return result


def row_summary(rows: list[Candidate]):
    return {
        "n": len(rows),
        "par_legislature": count_by(rows, "legislature"),
        "par_portee": count_by(rows, "scope"),
        "par_sort": count_by(rows, "sort"),
        "par_type_vote": count_by(rows, "type_vote"),
        "par_methode_lien": count_by(rows, "link_method"),
        "dossiers_distincts": len({row.dossier_uid for row in rows if row.dossier_uid}),
        "par_procedure": dict(collections.Counter(row.procedure for row in rows).most_common()),
    }


def slim(row: Candidate):
    return {
        "legislature": row.legislature,
        "numero": row.numero,
        "date": row.date,
        "portee": row.scope,
        "sort": row.sort,
        "type_vote": row.type_vote,
        "dossier_uid": row.dossier_uid,
        "methode_lien": row.link_method,
        "pour": row.pour,
        "contre": row.contre,
        "abstentions": row.abstentions,
        "exprimes": row.exprimes,
        "participation": round(row.participation, 4),
        "part_minorite": round(row.part_minorite, 4),
        "objet": row.objet,
    }


def build_report():
    candidates, motions, all_scope, link_diagnostics, overrides_raw = build_rows()

    public_law = [row for row in candidates if row.type_vote in PUBLIC_TYPES and row.is_linked_law]
    core = [row for row in public_law if row.scope in {"ensemble", "premiere_partie"}]
    amendments = [row for row in public_law if row.scope == "amendement"]
    pool = [row for row in public_law if row.passes_default]
    core_pool = [row for row in core if row.passes_default]
    amendment_pool = [row for row in amendments if row.passes_default]
    strong_methods = {"dossier_ref", "vote_ref"}
    core_pool_strong = [row for row in core_pool if row.link_method in strong_methods]
    blocked_first_parts = [
        row for row in candidates
        if row.scope == "premiere_partie"
        and (not row.is_linked_law or row.link_method not in strong_methods)
    ]

    balanced = sorted(
        core_pool_strong,
        key=lambda row: (-row.part_minorite, -row.participation, row.legislature, row.numero),
    )
    procedures = collections.Counter(row.procedure for row in core_pool)
    all_bidirectional = group_balance(pool)
    core_bidirectional = group_balance(core_pool_strong)

    result = {
        "meta": {
            "format": "boussole-politique.vivier-report.v1",
            "legislatures": [16, 17],
            "discriminance_defaut": DISCRIMINANCE_DEFAULT,
            "participation_defaut": PARTICIPATION_DEFAULT,
            "definition_discriminance": "min(pour, contre) / (pour + contre)",
            "definition_participation": "(pour + contre + abstentions) / 577",
            "avertissement": "Rapport exploratoire Python. Ne constitue ni une sélection VAA ni un dataset canonique.",
        },
        "tous_scrutins_par_portee": {
            str(leg): {scope: count for (row_leg, scope), count in sorted(all_scope.items()) if row_leg == leg}
            for leg in (16, 17)
        },
        "overrides": {
            "format": overrides_raw.get("format"),
            "status": overrides_raw.get("status"),
            "n": len(overrides_raw.get("entries", [])),
            "path": str(OVERRIDES_PATH.relative_to(DRY_RUN)),
        },
        "liens": {
            str(leg): {
                scope: dict(sorted(collections.Counter({
                    method: count
                    for (row_leg, row_scope, method), count in link_diagnostics.items()
                    if row_leg == leg and row_scope == scope
                }).items()))
                for scope in ("ensemble", "premiere_partie", "amendement")
            }
            for leg in (16, 17)
        },
        "candidats_publics_lies_a_une_loi": row_summary(public_law),
        "vivier_core_avant_filtre": row_summary(core),
        "vivier_core_filtre_defaut": row_summary(core_pool),
        "vivier_core_filtre_lien_fort": row_summary(core_pool_strong),
        "vivier_amendements_filtre_defaut": row_summary(amendment_pool),
        "pool_total_filtre_defaut": row_summary(pool),
        "sensibilite": sensitivity(public_law),
        "premieres_parties_bloquees_par_lien": [slim(row) for row in blocked_first_parts],
        "motions": {
            "n": len(motions),
            "par_legislature": count_by(motions, "legislature"),
            "par_article": count_by(motions, "article"),
            "par_sort": count_by(motions, "sort"),
        },
        "equilibre_groupes_pool_total": all_bidirectional,
        "equilibre_groupes_core": core_bidirectional,
        "core_top_30_plus_serres": [slim(row) for row in balanced[:30]],
        "procedures_core": dict(procedures.most_common()),
        "gates": {
            "pool_non_vide": {
                "statut": "passe" if core_pool_strong else "echoue",
                "n_core_exploratoire": len(core_pool),
                "n_core_lien_fort": len(core_pool_strong),
            },
            "deux_legislatures": {
                "statut": "passe" if {row.legislature for row in core_pool_strong} == {16, 17} else "echoue"
            },
            "sorts_adopte_et_rejete": {
                "statut": "passe" if {row.sort for row in core_pool_strong} >= {"adopté", "rejeté"} else "echoue"
            },
            "groupes_bidirectionnels": {
                "statut": "passe" if all(
                    item["bidirectionnel"]
                    for groups in core_bidirectional.values()
                    for item in groups.values()
                    if item["n_directionnel"]
                ) else "partiel",
                "note": "Mesure descriptive pour/contre, pas preuve d'équilibre idéologique.",
            },
            "symetrie_du_vivier_core": {
                "statut": "non_prouve",
                "note": (
                    f"Le cœur à lien fort reste déséquilibré par sort ({sum(row.sort == 'adopté' for row in core_pool_strong)} "
                    f"adoptés / {sum(row.sort == 'rejeté' for row in core_pool_strong)} rejetés) et certains groupes "
                    "n'ont qu'environ 10 % de directions du côté minoritaire. La bidirectionnalité ne suffit pas."
                ),
            },
            "couverture_thematique": {
                "statut": "non_prouve",
                "note": "Aucune taxonomie thématique structurée dans les dumps inspectés.",
            },
            "amendements_structurants": {
                "statut": "non_prouve",
                "note": "Le filtre détecte des amendements, pas leur importance normative.",
            },
            "liens_source": {
                "statut": "partiel",
                "note": (
                    "Le titre est nécessaire pour une part importante, surtout en législature 16. "
                    "Cinq premières parties disposent désormais d'overrides proposés mais non relus à deux."
                ),
            },
            "verdict_global": "conditionnel",
        },
    }
    return result


def markdown(result):
    core = result["vivier_core_filtre_defaut"]
    core_strong = result["vivier_core_filtre_lien_fort"]
    amendment = result["vivier_amendements_filtre_defaut"]
    total = result["pool_total_filtre_defaut"]
    lines = [
        "# Q8 — Confrontation du vivier VAA élargi",
        "",
        "## Verdict",
        "",
        "Le pivot VAA est **viable en volume**, mais sa validation reste **conditionnelle**. Le vivier cœur "
        "(votes d'ensemble + premières parties, sans amendements) est déjà "
        f"non vide avec **{core['n']} candidats exploratoires** au filtre par défaut, dont **{core_strong['n']}** "
        "ont un lien source direct ou porté par un acte. Ce sous-ensemble fort contient les deux sorts et chaque "
        "groupe vote dans les deux directions, mais il reste fortement déséquilibré en faveur des scrutins "
        f"adoptés (**{core_strong['par_sort'].get('adopté', 0)} contre "
        f"{core_strong['par_sort'].get('rejeté', 0)}**). "
        "La symétrie politique et la couverture thématique ne sont donc pas démontrées ; le caractère "
        "structurant des amendements et une partie des liens scrutin→dossier ne sont pas encore prouvés.",
        "",
        "> Recommandation : utiliser d'abord le **vivier cœur comme banc de revue**, pas comme sélection déjà",
        "> équilibrée. Ne mobiliser les amendements qu'après définition d'une rubrique publique de « caractère",
        "> structurant » et durcissement des liens source.",
        "",
        "## Paramètres exploratoires",
        "",
        f"- discriminance minimale : `{result['meta']['discriminance_defaut']:.2f}` ;",
        f"- participation minimale : `{result['meta']['participation_defaut']:.2f}` des 577 sièges ;",
        "- discriminance = `min(pour, contre)/(pour+contre)` ;",
        "- les motions de censure restent hors score.",
        "",
        "Ces paramètres ne sont pas validés académiquement et ne doivent pas être choisis pour produire un "
        "résultat politique désiré.",
        "",
        "## 1. Taille du vivier",
        "",
        "| Périmètre | n | L16 | L17 | ensemble | 1re partie | amendement | adopté | rejeté | dossiers |",
        "|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|",
    ]

    def table_row(label, block):
        legs = block["par_legislature"]
        scopes = block["par_portee"]
        sorts = block["par_sort"]
        return (
            f"| {label} | {block['n']} | {legs.get(16, legs.get('16', 0))} | "
            f"{legs.get(17, legs.get('17', 0))} | {scopes.get('ensemble', 0)} | "
            f"{scopes.get('premiere_partie', 0)} | {scopes.get('amendement', 0)} | "
            f"{sorts.get('adopté', 0)} | {sorts.get('rejeté', 0)} | {block['dossiers_distincts']} |"
        )

    lines.extend([
        table_row("candidats publics liés à une loi", result["candidats_publics_lies_a_une_loi"]),
        table_row("cœur avant filtre", result["vivier_core_avant_filtre"]),
        table_row("cœur, filtre défaut (exploratoire)", core),
        table_row("**cœur, filtre défaut + lien fort**", core_strong),
        table_row("amendements, filtre défaut", amendment),
        table_row("total, filtre défaut", total),
        "",
        "Le nombre d'amendements montre que la discriminance ne suffit pas à définir l'importance : une "
        "sélection automatique dans ce pool serait méthodologiquement indéfendable.",
        "",
        "## 2. Sensibilité aux seuils",
        "",
        "| discrim. min | participation min | n total | ensemble | 1re partie | amendements | adopté | rejeté |",
        "|--:|--:|--:|--:|--:|--:|--:|--:|",
    ])
    for row in result["sensibilite"]:
        lines.append(
            f"| {row['discriminance_min']:.2f} | {row['participation_min']:.2f} | {row['n']} | "
            f"{row['ensemble']} | {row['premiere_partie']} | {row['amendement']} | "
            f"{row['adopte']} | {row['rejete']} |"
        )

    lines.extend([
        "",
        "## 3. Diversité des positions majoritaires de groupe — vivier cœur",
        "",
        "Cette mesure vérifie seulement que chaque groupe vote parfois pour et parfois contre dans le pool. "
        "Elle ne prouve ni neutralité, ni équilibre gauche/droite, ni qualité thématique.",
        "",
    ])
    for leg in ("16", "17"):
        lines.extend([
            f"### Législature {leg}",
            "",
            "| Groupe | pour | contre | égalité | part du côté minoritaire | bidirectionnel |",
            "|---|--:|--:|--:|--:|---|",
        ])
        for group, item in result["equilibre_groupes_core"][leg].items():
            minority = item["part_cote_minoritaire"]
            lines.append(
                f"| {group} | {item['pour']} | {item['contre']} | {item['egalite']} | "
                f"{minority:.1%} | {'oui' if item['bidirectionnel'] else 'non'} |"
                if minority is not None else
                f"| {group} | 0 | 0 | {item['egalite']} | — | non |"
            )
        lines.append("")

    links = result["liens"]
    lines.extend([
        "## 4. Qualité des liens scrutin → dossier",
        "",
        "| législature | portée | dossierRef | voteRef | override proposé | titre | ambigu/non lié |",
        "|---:|---|--:|--:|--:|--:|--:|",
    ])
    for leg in ("16", "17"):
        for scope in ("ensemble", "premiere_partie", "amendement"):
            item = links[leg][scope]
            uncertain = sum(
                value for key, value in item.items()
                if key not in {"dossier_ref", "vote_ref", "curated_override", "titre"}
            )
            lines.append(
                f"| {leg} | {scope} | {item.get('dossier_ref', 0)} | {item.get('vote_ref', 0)} | "
                f"{item.get('curated_override', 0)} | {item.get('titre', 0)} | {uncertain} |"
            )

    blocked = result["premieres_parties_bloquees_par_lien"]
    lines.extend([
        "",
        f"**{len(blocked)} premières parties passent par un override proposé** plutôt que par un lien fort "
        "(direct ou porté par un acte). Elles ne doivent pas entrer dans une sélection canonique avant "
        "relecture croisée de `fixtures/vivier-link-overrides.json`.",
        "",
        "## 5. Branche motions de censure",
        "",
        f"- {result['motions']['n']} motions ;",
        f"- par article : `{result['motions']['par_article']}` ;",
        f"- par sort : `{result['motions']['par_sort']}` ;",
        "- hors congruence, sans inférence sur les non-votants.",
        "",
        "## 6. Gates",
        "",
        "| Gate | Statut |",
        "|---|---|",
    ])
    for name, gate in result["gates"].items():
        if name == "verdict_global":
            continue
        lines.append(f"| `{name}` | **{gate['statut']}** |")

    lines.extend([
        "",
        "## 7. Décision proposée",
        "",
        "1. **Geler le seuil uniquement comme hypothèse**, pas comme vérité méthodologique.",
        "2. Composer pour revue un lot pilote de 10–15 énoncés dans le vivier cœur, sans le publier comme équilibré.",
        "3. Ajouter un mapping thématique EuroVoc avant d'affirmer la couverture.",
        "4. Résoudre les premières parties budgétaires bloquées par des liens d'actes ou overrides publiés.",
        "5. Définir une rubrique « amendement structurant » avant toute inclusion d'amendement.",
        "6. Publier inclusions **et exclusions**, puis demander une revue indépendante.",
        "",
        "## Limites",
        "",
        "- Le matching par titre est exploratoire : sa validation historique n'atteint que 71 % sur les cas dotés d'une référence directe en législature 17.",
        "- Les dumps ne donnent pas une taxonomie thématique exploitable directement.",
        "- `sort=adopté/rejeté` décrit le sort du scrutin, pas une polarité idéologique.",
        "- La bidirectionnalité d'un groupe ne garantit pas une sélection équilibrée.",
        "- Le rapport mesure un vivier ; il ne choisit aucun énoncé et ne formule aucun résumé.",
        "",
    ])
    return "\n".join(lines)


def main():
    result = build_report()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "q8-vivier-elargi.json"
    md_path = OUT_DIR / "q8-vivier-elargi.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    md_path.write_text(markdown(result), encoding="utf-8")
    core = result["vivier_core_filtre_defaut"]
    strong = result["vivier_core_filtre_lien_fort"]
    print(
        "Q8 terminé — vivier cœur exploratoire:", core["n"],
        "| lien fort:", strong["n"],
        "| adopté/rejeté (fort):",
        f"{strong['par_sort'].get('adopté', 0)}/{strong['par_sort'].get('rejeté', 0)}",
        "| verdict:", result["gates"]["verdict_global"],
    )
    print("Écrit:", json_path)
    print("Écrit:", md_path)


if __name__ == "__main__":
    main()
