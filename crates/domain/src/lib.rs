//! Contrats métier purs de Boussole Politique.
//!
//! Cette crate sépare les faits parlementaires, la couche VAA éditoriale et
//! les positions citoyennes locales. Elle ne réalise aucune I/O et ne dépend
//! d'aucun renderer ou serveur.

use core::fmt;
use serde::{Deserialize, Serialize};

macro_rules! string_id {
    ($name:ident) => {
        #[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
        #[serde(transparent)]
        pub struct $name(String);

        impl $name {
            /// Construit un identifiant non vide.
            pub fn new(value: impl Into<String>) -> Result<Self, EmptyIdentifier> {
                let value = value.into();
                if value.trim().is_empty() {
                    Err(EmptyIdentifier)
                } else {
                    Ok(Self(value))
                }
            }

            #[must_use]
            pub fn as_str(&self) -> &str {
                &self.0
            }
        }
    };
}

/// Erreur produite lorsqu'un identifiant textuel est vide.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct EmptyIdentifier;

impl fmt::Display for EmptyIdentifier {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("un identifiant métier ne peut pas être vide")
    }
}

impl std::error::Error for EmptyIdentifier {}

string_id!(EnonceId);
string_id!(ElectedOfficialId);
string_id!(GroupId);
string_id!(EditorialVersion);

/// Identifie un scrutin sans dépendre d'un libellé éditorial.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct ScrutinId {
    pub legislature: u16,
    pub numero: u32,
}

/// Direction binaire uniquement lorsqu'une position est tranchée.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Direction {
    Negative,
    Positive,
}

impl Direction {
    #[must_use]
    pub const fn invert(self) -> Self {
        match self {
            Self::Negative => Self::Positive,
            Self::Positive => Self::Negative,
        }
    }
}

/// Relie le vote « pour » à la formulation exacte de l'énoncé.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "i8", into = "i8")]
pub enum Polarity {
    VoteAgainstMeansAgreement,
    VoteForMeansAgreement,
}

impl Polarity {
    #[must_use]
    pub const fn normalize(self, raw: Direction) -> Direction {
        match self {
            Self::VoteAgainstMeansAgreement => raw.invert(),
            Self::VoteForMeansAgreement => raw,
        }
    }
}

impl TryFrom<i8> for Polarity {
    type Error = InvalidPolarity;

    fn try_from(value: i8) -> Result<Self, Self::Error> {
        match value {
            -1 => Ok(Self::VoteAgainstMeansAgreement),
            1 => Ok(Self::VoteForMeansAgreement),
            value => Err(InvalidPolarity(value)),
        }
    }
}

impl From<Polarity> for i8 {
    fn from(value: Polarity) -> Self {
        match value {
            Polarity::VoteAgainstMeansAgreement => -1,
            Polarity::VoteForMeansAgreement => 1,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct InvalidPolarity(pub i8);

impl fmt::Display for InvalidPolarity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "polarité invalide {}, attendu -1 ou 1", self.0)
    }
}

impl std::error::Error for InvalidPolarity {}

/// Position citoyenne conservée localement.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "CitizenPositionWire", into = "CitizenPositionWire")]
pub enum CitizenPosition {
    StronglyDisagree,
    Disagree,
    Agree,
    StronglyAgree,
    NoOpinion,
    Later,
}

impl CitizenPosition {
    /// Retourne la direction et le poids, ou `None` pour `sans_avis`/`passer`.
    #[must_use]
    pub const fn directional_weight(self) -> Option<(Direction, u8)> {
        match self {
            Self::StronglyDisagree => Some((Direction::Negative, 2)),
            Self::Disagree => Some((Direction::Negative, 1)),
            Self::Agree => Some((Direction::Positive, 1)),
            Self::StronglyAgree => Some((Direction::Positive, 2)),
            Self::NoOpinion | Self::Later => None,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(untagged)]
enum CitizenPositionWire {
    Direction(i8),
    State(CitizenPositionState),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
enum CitizenPositionState {
    #[serde(rename = "sans_avis")]
    NoOpinion,
    #[serde(rename = "passer")]
    Later,
}

impl TryFrom<CitizenPositionWire> for CitizenPosition {
    type Error = InvalidCitizenPosition;

    fn try_from(value: CitizenPositionWire) -> Result<Self, Self::Error> {
        match value {
            CitizenPositionWire::Direction(-2) => Ok(Self::StronglyDisagree),
            CitizenPositionWire::Direction(-1) => Ok(Self::Disagree),
            CitizenPositionWire::Direction(1) => Ok(Self::Agree),
            CitizenPositionWire::Direction(2) => Ok(Self::StronglyAgree),
            CitizenPositionWire::Direction(value) => Err(InvalidCitizenPosition(value)),
            CitizenPositionWire::State(CitizenPositionState::NoOpinion) => Ok(Self::NoOpinion),
            CitizenPositionWire::State(CitizenPositionState::Later) => Ok(Self::Later),
        }
    }
}

impl From<CitizenPosition> for CitizenPositionWire {
    fn from(value: CitizenPosition) -> Self {
        match value {
            CitizenPosition::StronglyDisagree => Self::Direction(-2),
            CitizenPosition::Disagree => Self::Direction(-1),
            CitizenPosition::Agree => Self::Direction(1),
            CitizenPosition::StronglyAgree => Self::Direction(2),
            CitizenPosition::NoOpinion => Self::State(CitizenPositionState::NoOpinion),
            CitizenPosition::Later => Self::State(CitizenPositionState::Later),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct InvalidCitizenPosition(pub i8);

impl fmt::Display for InvalidCitizenPosition {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            formatter,
            "position citoyenne invalide {}, attendu -2, -1, 1 ou 2",
            self.0
        )
    }
}

impl std::error::Error for InvalidCitizenPosition {}

/// Position officielle d'un élu. L'absence reste explicitement estimée.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum VotePosition {
    #[serde(rename = "pour")]
    For,
    #[serde(rename = "contre")]
    Against,
    #[serde(rename = "abstention")]
    Abstention,
    #[serde(rename = "nonvotant")]
    NonVoter,
    #[serde(rename = "absent")]
    EstimatedAbsent,
}

impl VotePosition {
    #[must_use]
    pub const fn direction(self) -> Option<Direction> {
        match self {
            Self::For => Some(Direction::Positive),
            Self::Against => Some(Direction::Negative),
            Self::Abstention | Self::NonVoter | Self::EstimatedAbsent => None,
        }
    }
}

/// Fait de vote minimal : groupe daté et éventuelle mise au point officielle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct VoteFact {
    pub scrutin_id: ScrutinId,
    pub elected_official_id: ElectedOfficialId,
    pub group_at_vote: GroupId,
    pub original_position: VotePosition,
    pub corrected_position: Option<VotePosition>,
}

impl VoteFact {
    #[must_use]
    pub const fn effective_position(&self) -> VotePosition {
        match self.corrected_position {
            Some(position) => position,
            None => self.original_position,
        }
    }
}

/// Contrat minimal d'un énoncé VAA versionné.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EnonceVaa {
    pub id: EnonceId,
    pub scrutin_id: ScrutinId,
    pub polarity: Polarity,
    pub formulation_version: EditorialVersion,
    pub summary_version: EditorialVersion,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum AnswerPhase {
    #[serde(rename = "pre_reveal")]
    PreReveal,
    #[serde(rename = "post_reveal")]
    PostReveal,
}

/// Réponse locale. Aucun type de transport ou serveur n'est associé à ce type.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CitizenAnswer {
    pub enonce_id: EnonceId,
    pub value: CitizenPosition,
    pub formulation_version: EditorialVersion,
    pub summary_version: EditorialVersion,
    pub local_timestamp: String,
    pub phase: AnswerPhase,
}

#[cfg(test)]
mod tests {
    use super::{CitizenPosition, Direction, Polarity, VotePosition};

    #[test]
    fn inverse_polarity_reverses_a_raw_vote() {
        assert_eq!(
            Polarity::VoteAgainstMeansAgreement.normalize(Direction::Negative),
            Direction::Positive
        );
    }

    #[test]
    fn non_directional_positions_have_no_weight() {
        assert_eq!(CitizenPosition::NoOpinion.directional_weight(), None);
        assert_eq!(CitizenPosition::Later.directional_weight(), None);
        assert_eq!(VotePosition::Abstention.direction(), None);
        assert_eq!(VotePosition::NonVoter.direction(), None);
        assert_eq!(VotePosition::EstimatedAbsent.direction(), None);
    }
}
