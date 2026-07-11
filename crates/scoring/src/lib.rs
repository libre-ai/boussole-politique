//! Calcul entier, pur et déterministe de la congruence.

use boussole_domain::{CitizenPosition, Polarity, VotePosition};

pub const DEFAULT_N_MIN: u64 = 10;

/// Une paire de positions sur un même énoncé.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ScoreEntry {
    pub citizen: CitizenPosition,
    /// `None` signifie donnée manquante, et non abstention.
    pub representative: Option<VotePosition>,
    pub polarity: Polarity,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NonDisplayReason {
    UndefinedNoCommonPosition,
    BelowMinimum { n: u64, minimum: u64 },
}

/// Résultat contextualisé. Le score n'est jamais la seule sortie.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ScoreResult {
    pub num: u64,
    pub den: u64,
    pub n: u64,
    pub milliemes: Option<u16>,
    pub displayable: bool,
    pub non_display_reason: Option<NonDisplayReason>,
    pub abstentions: u64,
    pub non_voters: u64,
    pub missing_data: u64,
}

/// Calcule la congruence sans flottants ni état global.
#[must_use]
pub fn score(
    entries: impl IntoIterator<Item = ScoreEntry>,
    minimum_common_statements: u64,
) -> ScoreResult {
    let mut num = 0_u64;
    let mut den = 0_u64;
    let mut n = 0_u64;
    let mut abstentions = 0_u64;
    let mut non_voters = 0_u64;
    let mut missing_data = 0_u64;

    for entry in entries {
        let Some((citizen_direction, weight)) = entry.citizen.directional_weight() else {
            continue;
        };
        let Some(representative) = entry.representative else {
            missing_data += 1;
            continue;
        };
        let Some(raw_direction) = representative.direction() else {
            match representative {
                VotePosition::Abstention => abstentions += 1,
                VotePosition::NonVoter | VotePosition::EstimatedAbsent => non_voters += 1,
                VotePosition::For | VotePosition::Against => unreachable!("directional vote"),
            }
            continue;
        };

        let normalized_direction = entry.polarity.normalize(raw_direction);
        let weight = u64::from(weight);
        den += weight;
        n += 1;
        if citizen_direction == normalized_direction {
            num += weight;
        }
    }

    let milliemes = if den == 0 {
        None
    } else {
        let numerator = 1000_u128 * u128::from(num) + u128::from(den / 2);
        let rounded = numerator / u128::from(den);
        Some(u16::try_from(rounded).expect("a congruence is always between 0 and 1000"))
    };

    let non_display_reason = if den == 0 {
        Some(NonDisplayReason::UndefinedNoCommonPosition)
    } else if n < minimum_common_statements {
        Some(NonDisplayReason::BelowMinimum {
            n,
            minimum: minimum_common_statements,
        })
    } else {
        None
    };

    ScoreResult {
        num,
        den,
        n,
        milliemes,
        displayable: non_display_reason.is_none(),
        non_display_reason,
        abstentions,
        non_voters,
        missing_data,
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GroupExclusionReason {
    Tie,
    NoDirectionalVote,
}

/// Position majoritaire et indicateurs séparés d'un groupe pour un scrutin.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GroupMajorityResult {
    pub position: Option<VotePosition>,
    pub exclusion_reason: Option<GroupExclusionReason>,
    pub for_votes: u64,
    pub against_votes: u64,
    pub abstentions: u64,
    pub non_voters: u64,
    pub missing_data: u64,
}

/// Agrège une position majoritaire sans convertir les abstentions en direction.
#[must_use]
pub fn group_majority(
    positions: impl IntoIterator<Item = Option<VotePosition>>,
) -> GroupMajorityResult {
    let mut result = GroupMajorityResult {
        position: None,
        exclusion_reason: None,
        for_votes: 0,
        against_votes: 0,
        abstentions: 0,
        non_voters: 0,
        missing_data: 0,
    };

    for position in positions {
        match position {
            Some(VotePosition::For) => result.for_votes += 1,
            Some(VotePosition::Against) => result.against_votes += 1,
            Some(VotePosition::Abstention) => result.abstentions += 1,
            Some(VotePosition::NonVoter | VotePosition::EstimatedAbsent) => {
                result.non_voters += 1;
            }
            None => result.missing_data += 1,
        }
    }

    match result.for_votes.cmp(&result.against_votes) {
        core::cmp::Ordering::Greater => result.position = Some(VotePosition::For),
        core::cmp::Ordering::Less => result.position = Some(VotePosition::Against),
        core::cmp::Ordering::Equal if result.for_votes == 0 => {
            result.exclusion_reason = Some(GroupExclusionReason::NoDirectionalVote);
        }
        core::cmp::Ordering::Equal => {
            result.exclusion_reason = Some(GroupExclusionReason::Tie);
        }
    }

    result
}

#[cfg(test)]
mod tests {
    use super::{GroupExclusionReason, NonDisplayReason, ScoreEntry, group_majority, score};
    use boussole_domain::{CitizenPosition, Polarity, VotePosition};

    const POSITIVE: Polarity = Polarity::VoteForMeansAgreement;

    #[test]
    fn denominator_zero_is_undefined() {
        let result = score(
            [ScoreEntry {
                citizen: CitizenPosition::NoOpinion,
                representative: Some(VotePosition::For),
                polarity: POSITIVE,
            }],
            10,
        );

        assert_eq!(result.den, 0);
        assert_eq!(result.milliemes, None);
        assert!(!result.displayable);
        assert_eq!(
            result.non_display_reason,
            Some(NonDisplayReason::UndefinedNoCommonPosition)
        );
    }

    #[test]
    fn inverse_polarity_is_applied() {
        let result = score(
            [ScoreEntry {
                citizen: CitizenPosition::StronglyAgree,
                representative: Some(VotePosition::Against),
                polarity: Polarity::VoteAgainstMeansAgreement,
            }],
            0,
        );

        assert_eq!(result.num, 2);
        assert_eq!(result.den, 2);
        assert_eq!(result.milliemes, Some(1000));
    }

    #[test]
    fn exclusions_are_counted_but_not_scored() {
        let result = score(
            [
                ScoreEntry {
                    citizen: CitizenPosition::Agree,
                    representative: Some(VotePosition::Abstention),
                    polarity: POSITIVE,
                },
                ScoreEntry {
                    citizen: CitizenPosition::Agree,
                    representative: Some(VotePosition::NonVoter),
                    polarity: POSITIVE,
                },
                ScoreEntry {
                    citizen: CitizenPosition::Agree,
                    representative: None,
                    polarity: POSITIVE,
                },
            ],
            0,
        );

        assert_eq!(result.abstentions, 1);
        assert_eq!(result.non_voters, 1);
        assert_eq!(result.missing_data, 1);
        assert_eq!(result.den, 0);
    }

    #[test]
    fn score_below_minimum_is_calculated_but_hidden() {
        let result = score(
            [ScoreEntry {
                citizen: CitizenPosition::StronglyAgree,
                representative: Some(VotePosition::For),
                polarity: POSITIVE,
            }],
            10,
        );

        assert_eq!(result.milliemes, Some(1000));
        assert!(!result.displayable);
        assert_eq!(
            result.non_display_reason,
            Some(NonDisplayReason::BelowMinimum { n: 1, minimum: 10 })
        );
    }

    #[test]
    fn weighted_round_half_up_is_integer_only() {
        let result = score(
            [
                ScoreEntry {
                    citizen: CitizenPosition::Agree,
                    representative: Some(VotePosition::Against),
                    polarity: POSITIVE,
                },
                ScoreEntry {
                    citizen: CitizenPosition::StronglyAgree,
                    representative: Some(VotePosition::For),
                    polarity: POSITIVE,
                },
            ],
            0,
        );

        assert_eq!(result.num, 2);
        assert_eq!(result.den, 3);
        assert_eq!(result.milliemes, Some(667));
    }

    #[test]
    fn group_tie_is_excluded() {
        let result = group_majority([
            Some(VotePosition::For),
            Some(VotePosition::Against),
            Some(VotePosition::Abstention),
        ]);

        assert_eq!(result.position, None);
        assert_eq!(result.exclusion_reason, Some(GroupExclusionReason::Tie));
        assert_eq!(result.abstentions, 1);
    }

    #[test]
    fn group_without_direction_is_distinct_from_tie() {
        let result = group_majority([
            Some(VotePosition::Abstention),
            Some(VotePosition::NonVoter),
            None,
        ]);

        assert_eq!(result.position, None);
        assert_eq!(
            result.exclusion_reason,
            Some(GroupExclusionReason::NoDirectionalVote)
        );
    }
}
