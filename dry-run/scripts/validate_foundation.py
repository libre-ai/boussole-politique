"""Validation adverse de la fondation AVANT fan-out.
Question centrale : pour chaque LOI PROMULGUÉE, a-t-on trouvé son vote de référence,
et les 'sans vote public' sont-elles de vraies exclusions ou des échecs de lien ?"""
import anlib, collections

def best_candidate(dtoks, ensemble):
    """Meilleur scrutin d'ensemble pour un set de tokens dossier (diagnostic de lien manqué)."""
    best = (0.0, 0, None)
    for s in ensemble:
        otoks = anlib._content_tokens(s.objet)
        shared = len(dtoks & otoks)
        if not dtoks:
            continue
        recall = shared / len(dtoks)
        if recall > best[0]:
            best = (recall, shared, s)
    return best

for leg in (17, 16):
    print(f"\n========== LÉGISLATURE {leg} ==========")
    scrutins = anlib.load_scrutins(leg)
    dossiers = anlib.load_dossiers(leg)
    title_idx = anlib.build_title_index(dossiers)
    ensemble = [s for s in scrutins if s.is_ensemble and s.type_code in ("SPO", "SPS")]

    # mapping dossier -> scrutins ensemble liés
    linked = collections.defaultdict(list)
    methods = collections.Counter()
    for s in ensemble:
        uid, meth = anlib.link_scrutin(s, dossiers, title_idx)
        methods[meth] += 1
        if uid:
            linked[uid].append(s)
    print(f"  ensemble public={len(ensemble)}  méthodes={dict(methods)}")

    prom_loi = {uid: d for uid, d in dossiers.items() if d.promulguee and d.is_loi}
    avec = [u for u in prom_loi if u in linked]
    sans = [u for u in prom_loi if u not in linked]
    print(f"  PROM-loi={len(prom_loi)}  avec vote lié={len(avec)}  sans={len(sans)}")

    # [A] EXACTITUDE : sur les scrutins à ref directe, link_scrutin retrouve-t-il la même chose ?
    ref_ok = ref_bad = 0
    for s in ensemble:
        if s.dossier_ref and s.dossier_ref in dossiers:
            # neutralise la ref pour tester le fallback titre
            saved = s.dossier_ref
            object.__setattr__(s, "dossier_ref", None)
            uid, meth = anlib.link_scrutin(s, dossiers, title_idx)
            object.__setattr__(s, "dossier_ref", saved)
            if uid == saved:
                ref_ok += 1
            else:
                ref_bad += 1
    tot = ref_ok + ref_bad
    print(f"\n  [A] Fallback-titre vs vérité-terrain (refs directes) : "
          f"{ref_ok}/{tot} corrects ({100*ref_ok/tot:.0f}%)" if tot else "  [A] pas de refs directes")

    # [B] LES 'SANS VOTE' SONT-ELLES DE VRAIES EXCLUSIONS ?
    print(f"\n  [B] Audit des {len(sans)} PROM-loi 'sans vote public' — candidat non lié le plus fort :")
    suspects = []
    for uid in sans:
        d = prom_loi[uid]
        dtoks = title_idx.get(uid, set())
        recall, shared, s = best_candidate(dtoks, [x for x in ensemble if x.dossier_ref not in (uid,)])
        # un candidat fort (recall élevé) NON lié = échec de lien suspect
        already_linked_elsewhere = s and anlib.link_scrutin(s, dossiers, title_idx)[0] not in (None, uid)
        if recall >= 0.5 and shared >= 2 and not already_linked_elsewhere:
            suspects.append((uid, d.procedure, recall, shared, s))
    print(f"      exclusions suspectes (candidat fort non attribué ailleurs) : {len(suspects)}")
    for uid, proc, recall, shared, s in suspects[:15]:
        print(f"        {uid} [{proc[:22]}] recall={recall:.2f} shared={shared}  <- scrutin {s.numero}: {s.objet[:70]}")
    # ventilation des exclusions par procédure
    exc = collections.Counter(prom_loi[u].procedure for u in sans)
    print("      ventilation par procédure :", dict(exc))

    # [C] invariant décompte (déjà ✓ mais on reconfirme sur tout le corpus de référence)
    bad = 0
    for uid in avec:
        s = sorted(linked[uid], key=lambda x: (x.date, x.numero))[-1]
        cnt = collections.Counter(p for _, p, _, _, _ in s.positions_nominales())
        if cnt["pour"] != s.d_pour or cnt["contre"] != s.d_contre or cnt["abstention"] != s.d_abst:
            bad += 1
    print(f"\n  [C] invariant décompte sur {len(avec)} votes de référence : mismatch={bad}")
