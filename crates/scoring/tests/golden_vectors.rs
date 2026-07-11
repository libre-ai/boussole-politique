use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;

use boussole_domain::{CitizenPosition, Polarity, VotePosition};
use boussole_scoring::{ScoreEntry, score};
use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct Fixture {
    n_min_defaut: u64,
    cas_synthetiques: Vec<SyntheticCase>,
    cas_reels: RealCases,
}

#[derive(Debug, Deserialize)]
struct SyntheticCase {
    nom: String,
    n_min: u64,
    enonces: Vec<Statement>,
    citoyen: Vec<CitizenRecord>,
    elu: Vec<RepresentativeRecord>,
    attendu: Expected,
}

#[derive(Debug, Deserialize)]
struct Statement {
    id: String,
    polarite: Polarity,
}

#[derive(Debug, Deserialize)]
struct CitizenRecord {
    enonce: String,
    valeur: CitizenPosition,
}

#[derive(Debug, Deserialize)]
struct RepresentativeRecord {
    enonce: String,
    position: VotePosition,
}

#[derive(Debug, Deserialize)]
struct Expected {
    num: u64,
    den: u64,
    n: u64,
    congruence_millimes: Option<u16>,
    affichable: bool,
}

#[derive(Debug, Deserialize)]
struct RealCases {
    profils: Vec<RealProfile>,
}

#[derive(Debug, Deserialize)]
struct RealProfile {
    citoyen: String,
    scores_par_groupe: Vec<RealGroupScore>,
}

#[derive(Debug, Deserialize)]
struct RealGroupScore {
    groupe: String,
    congruence_millimes: u16,
    n: u64,
}

fn fixture() -> Fixture {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/scoring/vecteurs-test.json");
    let bytes = fs::read(path).expect("golden fixture must be readable");
    serde_json::from_slice(&bytes).expect("golden fixture must match its versioned contract")
}

#[test]
fn all_synthetic_vectors_match_bit_for_bit() {
    let fixture = fixture();
    assert_eq!(fixture.n_min_defaut, 10);
    assert_eq!(fixture.cas_synthetiques.len(), 10);

    for case in fixture.cas_synthetiques {
        let polarities: HashMap<_, _> = case
            .enonces
            .into_iter()
            .map(|statement| (statement.id, statement.polarite))
            .collect();
        let representative: HashMap<_, _> = case
            .elu
            .into_iter()
            .map(|record| (record.enonce, record.position))
            .collect();
        let entries = case.citoyen.into_iter().map(|record| ScoreEntry {
            citizen: record.valeur,
            representative: representative.get(&record.enonce).copied(),
            polarity: *polarities
                .get(&record.enonce)
                .expect("every citizen statement must define a polarity"),
        });

        let actual = score(entries, case.n_min);
        assert_eq!(actual.num, case.attendu.num, "{}: num", case.nom);
        assert_eq!(actual.den, case.attendu.den, "{}: den", case.nom);
        assert_eq!(actual.n, case.attendu.n, "{}: n", case.nom);
        assert_eq!(
            actual.milliemes, case.attendu.congruence_millimes,
            "{}: millièmes",
            case.nom
        );
        assert_eq!(
            actual.displayable, case.attendu.affichable,
            "{}: affichable",
            case.nom
        );
    }
}

#[test]
fn inverse_polarity_golden_case_is_present() {
    let fixture = fixture();
    let case = fixture
        .cas_synthetiques
        .iter()
        .find(|case| case.nom == "polarite_inversee")
        .expect("the inverse-polarity regression vector is mandatory");

    assert!(case.enonces.iter().all(|statement| {
        statement.polarite == Polarity::VoteAgainstMeansAgreement
    }));
    assert_eq!(case.attendu.congruence_millimes, Some(667));
}

#[test]
fn real_reference_outputs_remain_frozen_but_are_not_recomputed() {
    let fixture = fixture();
    assert_eq!(fixture.cas_reels.profils.len(), 3);

    let ciotti = fixture
        .cas_reels
        .profils
        .iter()
        .find(|profile| profile.citoyen == "Éric Ciotti")
        .expect("the real Ciotti reference profile must remain present");
    let soc = ciotti
        .scores_par_groupe
        .iter()
        .find(|score| score.groupe == "SOC")
        .expect("the small-n SOC reference must remain present");

    assert_eq!(soc.congruence_millimes, 333);
    assert_eq!(soc.n, 3);
    assert!(soc.n < fixture.n_min_defaut);

    // Le fixture ne contient que les sorties agrégées de ces profils réels,
    // pas leurs entrées par énoncé. Les prétendre recalculées serait faux.
    assert!(fixture.cas_reels.profils.iter().all(|profile| {
        profile.scores_par_groupe.iter().all(|score| {
            score.congruence_millimes <= 1000
        })
    }));
}
