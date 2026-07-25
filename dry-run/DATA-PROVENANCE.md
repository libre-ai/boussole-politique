# Provenance record — Assemblée nationale open data

This is the record required by
[`DATA-PROVENANCE.md`](https://github.com/libre-ai/libre-ai/blob/main/DATA-PROVENANCE.md)
in the base repository, which denies publication of any third-party dataset
until the record below is complete. It covers the five archives under
`dry-run/data/` and the dry-run outputs derived from them.

Every fact here is either verifiable from the repository itself or was checked
against the producer's live portal on 2026-07-25; the verification method is
stated for each, and the two points that remain reconstructed rather than
recorded are named as such in §12.

## 1. Producer and acquisition channel

Producer (the `Concédant` of the licence): **Assemblée nationale**.

Portal: `data.assemblee-nationale.fr`, named as the authoritative source in
[`specs-v0.3.md`](../specs-v0.3.md) §1.1 and
[`modele-donnees-v2.md`](../modele-donnees-v2.md) §51 since the first
specification.

## 2. Dataset identifiers and version hashes

Each local archive is redistributed byte-for-byte as acquired. The upstream path
is relative to `https://data.assemblee-nationale.fr/static/openData/repository/`.

| Local file                  | Upstream archive                                                                                    | Files | SHA-256                                                            |
| --------------------------- | --------------------------------------------------------------------------------------------------- | ----- | ------------------------------------------------------------------ |
| `data/scrutins-17.json.zip` | `17/loi/scrutins/Scrutins.json.zip`                                                                 | 7 397 | `1c16a2eb85c7570aab6e67436e69133dc076e122055ef1927108cebc3043f728` |
| `data/scrutins-16.json.zip` | `16/loi/scrutins/Scrutins.json.zip`                                                                 | 4 106 | `adc5e57d3ad5904fd11e176b531b3d525d4ecfdf78db9587f93a14452601126b` |
| `data/dossiers-17.json.zip` | `17/loi/dossiers_legislatifs/Dossiers_Legislatifs.json.zip`                                         | 9 486 | `a84bb785d17e8eb43cb975ae6898544151757ff4c36f7cf7e346b0e3a476f787` |
| `data/dossiers-16.json.zip` | `16/loi/dossiers_legislatifs/Dossiers_Legislatifs.json.zip`                                         | 9 090 | `6a2369c01a44711362b7c9a79ed13c001400cbb00dc6bade7b05499d2e6d478e` |
| `data/amo10-17.json.zip`    | `17/amo/deputes_actifs_mandats_actifs_organes/AMO10_deputes_actifs_mandats_actifs_organes.json.zip` | 7 752 | `0762983555ebc277d37e75ca20011274a74aa0b2537579bd388536de94c01e67` |

Reproduce with `shasum -a 256 dry-run/data/*.zip`.

### How the mapping was verified

The archives were committed under short local names, and no download script was
kept, so the local-to-upstream mapping was re-established by evidence rather
than assumed:

- **Legislature 16 — proven by hash.** Both archives were downloaded again from
  the upstream paths above on 2026-07-25 and are **bit-for-bit identical** to
  the committed copies (same SHA-256, same byte length). These two datasets are
  closed: the legislature ended with the June 2024 dissolution and the producer
  has not republished them since, so the identity is exact and durable.
- **Legislature 17 — matched by structure and naming.** These are live datasets
  the producer refreshes daily, so a hash comparison against today's copy cannot
  match by construction. The mapping rests on three converging checks: the
  upstream paths differ from the hash-proven legislature 16 paths only by the
  legislature segment (`16` → `17`); the internal file naming matches the
  legislature 17 identifier scheme (`VTANR5L17V*`, `DLR5L17N*`); and for
  `amo10-17`, the internal layout (`json/acteur/`, `json/deport/`, `json/organe/`)
  is identical to the current `AMO10` archive and distinguishes it from the
  `AMO40` and `AMO50` "divisés" variants published alongside it.

## 3. Collection date and method

The producer's generation timestamps are carried inside each archive
(`unzip -l dry-run/data/<file>`) and give the **date of last update of the
Information** that the licence requires be cited:

| Archive                | Producer's last update |
| ---------------------- | ---------------------- |
| `scrutins-17.json.zip` | 2026-06-12             |
| `dossiers-17.json.zip` | 2026-06-12             |
| `amo10-17.json.zip`    | 2026-06-12             |
| `scrutins-16.json.zip` | 2024-06-28             |
| `dossiers-16.json.zip` | 2024-06-28             |

The legislature 16 dates are corroborated externally: the upstream
`Last-Modified` headers read `Fri, 28 Jun 2024 10:22:27 GMT` and
`Fri, 28 Jun 2024 10:16:19 GMT`, which are the same instants as the internal
12:22 and 12:16 Paris timestamps.

Collection was a manual download over HTTPS. [`SCHEMA-NOTES.md`](SCHEMA-NOTES.md)
records `curl` among the tools used and is dated 2026-06-13, one day after the
legislature 17 archives were generated, which brackets the capture to
**2026-06-12/13**. The archives entered this repository with its initial commit
on 2026-07-11.

## 4. Original licence and terms

**Licence Ouverte / Open Licence (Etalab)**, declared as `etalab-2.0` — the SPDX
identifier used in [`REUSE.toml`](../REUSE.toml), with its text in
[`LICENSES/etalab-2.0.txt`](../LICENSES/etalab-2.0.txt).

The producer publishes its terms at
`https://data.assemblee-nationale.fr/licence-ouverte-open-licence`, which states
that the Licence Ouverte applies to its open data.

One discrepancy is recorded rather than smoothed over: the PDF that page links
is the **version 1.0** text of October 2011 (it uses the `Producteur` wording and
states "Cette licence est une version 1.0 de la Licence Ouverte"), while the
declaration here is version 2.0. The declaration follows the owner's ruling of
2026-07-25 (§11) and the fact that `etalab-2.0` is the only Licence Ouverte
version with an SPDX identifier — `etalab-1.0` is not one, so v1.0 is not
expressible in a REUSE declaration. The two versions carry the same operative
obligation, attribution of source and update date, and version 1.0 §"Compatibilité"
provides for reuse to continue under later versions. What binds this repository
is honoured either way, and is honoured in §7.

## 5. Transformations

**On the archives: none.** They are redistributed exactly as acquired — proven
for legislature 16 by the byte-identical hash in §2.

**On the derived outputs:** the scripts under `dry-run/scripts/` decompress the
archives, filter scrutins and dossiers to the perimeter under study, join them
by actor and dossier reference, and aggregate. No hand editing occurs at any
step; `dry-run/out/` is entirely re-derivable from `dry-run/data/`. The known
format hazards handled during the join, and the deduplication rules, are
documented in [`SCHEMA-NOTES.md`](SCHEMA-NOTES.md).

## 6. Copyright and EU sui generis database rights

Copyright over the archives and over the records they contain is the producer's,
and `REUSE.toml` names the Assemblée nationale as sole copyright holder for
`dry-run/data/**`. We wrote none of those bytes.

Sui generis database rights (Directive 96/9/EC, transposed at articles L. 341-1
et seq. of the French Intellectual Property Code) would sit with the producer as
the maker of the database. They are not an obstacle: the Licence Ouverte assigns
to the reuser, non-exclusively and free of charge, the transferable intellectual
property rights the licensor holds over the Information, and guarantees that
third-party rights do not impede the rights it grants. Extraction and reuse of a
substantial part — which the dry-run performs — are therefore covered.

For the derived outputs, our own contribution is the selection, structure and
computation; the underlying records remain the producer's. That split is what
the dual copyright and the `etalab-2.0 AND CC-BY-4.0` expression in
`REUSE.toml` state.

## 7. Redistribution and attribution conditions

The Licence Ouverte permits reproduction, redistribution, adaptation and
commercial use, on one condition: **citing the source (at minimum the name of
the licensor) and the date of the last update of the reused Information**. It
also requires that reuse not mislead third parties as to the content of the
Information, its source or its update date.

This repository discharges that obligation as follows.

> **Attribution** — Assemblée nationale, open data downloaded from
> `https://data.assemblee-nationale.fr/`, under the Licence Ouverte / Open
> Licence. Updates of 2026-06-12 (legislature 17: scrutins, dossiers
> législatifs, AMO10) and 2024-06-28 (legislature 16: scrutins, dossiers
> législatifs). Per-archive update dates are in §3.

The same notice appears in [`LICENSE`](../LICENSE) so that it travels with the
repository. It applies to the archives and to every output derived from them,
including those licensed `CC-BY-4.0` alone: adaptation does not extinguish the
attribution due on the Information it was derived from.

The attribution confers no official character on this reuse and implies no
endorsement by the Assemblée nationale, which the licence states explicitly and
which the neutrality charter restates independently.

The producer supplies the Information as produced, without warranty of accuracy
or of continued availability, and the reuser alone is responsible for the reuse.
Corrections published upstream are handled by re-derivation, not manual edit
(§10).

## 8. Personal data classification

The archives contain **personal data**: named members of the Assemblée
nationale, their `PA…` actor identifiers, their mandates and group affiliations,
and their individual votes.

They contain no special-category data within the meaning of article 9 GDPR held
about private individuals. Political opinions are article 9 data in general, but
what is recorded here is not an opinion inferred about a private person: it is a
vote cast publicly by an elected representative in the exercise of a mandate,
whose publicity is a legal obligation of the institution. The producer publishes
it for that reason.

No citizen data is present in this material, and none is collected by the
product: positions entered by a user stay on the device, as set out in
[`docs/donnees-personnelles.md`](../docs/donnees-personnelles.md).

## 9. Lawful basis, purpose, minimisation, retention

- **Purpose**: deriving the factual layer of a voting-advice application — which
  laws were voted, by whom, how — and the methodology evidence supporting it.
- **Lawful basis**: legitimate interest (article 6(1)(f) GDPR) in publishing
  factual civic information about the public activity of elected
  representatives, on data the institution is required to publish. The balancing
  test is favourable precisely because the processing stays within the purpose
  for which the producer publishes.
- **Minimisation**: the derived outputs keep only what the analysis needs —
  votes, group affiliations, dossier references. Contact details and other
  fields present upstream are not carried into `dry-run/out/`.
- **Retention**: the archives are retained as the reproducibility baseline for
  the published analyses. They are pinned captures, not a live mirror, and are
  replaced rather than accumulated when the perimeter is re-derived.

An open-data licence does not cure a GDPR issue, as the base policy states; the
basis above stands on its own and is not derived from the licence.

## 10. Deletion, correction and source-withdrawal procedure

- **Upstream correction.** Official errata — a corrected scrutin, a `miseAuPoint`
  published by the institution — are never patched by hand. The archive is
  re-downloaded, the hash table in §2 updated, the outputs re-derived and
  committed, leaving the correction visible in the history. This is the integrity
  rule of `specs-v0.3.md` §1.4.
- **Withdrawal by the producer.** If the producer withdraws or restricts a
  dataset, the affected archives and every output derived from them are removed
  from the repository and the removal is recorded here.
- **Individual request.** A request from a data subject is assessed against §8
  and §9. The material is public institutional record, so erasure is not
  automatic; a request that succeeds is executed by removing the records and
  re-deriving, with the outcome recorded here.

## 11. Approval and publication

- **Model-provider terms**: not applicable. No model output is present in this
  material; every figure in `dry-run/out/` is computed by the scripts under
  `dry-run/scripts/`.
- **Accountable approval**: the repository owner ruled on **2026-07-25** that
  the Assemblée nationale data is public open data under the Licence Ouverte /
  Etalab 2.0, lifting the earlier hold that had left the upstream terms
  unsettled.
- **Publication date of this record**: 2026-07-25.

## 12. What remains reconstructed

Stated plainly so the record is not read as firmer than it is:

1. **The exact download URLs used in June 2026 were never recorded.** The paths
   in §2 are the producer's current publication paths, matched to the local
   archives by the evidence in §2 — conclusive for legislature 16 (identical
   hashes), strong but circumstantial for legislature 17. No URL in this record
   is inferred from naming alone; each was retrieved from the producer's own
   dataset pages.
2. **The precise capture instant is bracketed, not logged**, to 2026-06-12/13
   (§3).

Both gaps close the same way, and neither is a reason to hold publication: the
ETL pipeline specified in `specs-v0.3.md` §1.4 records source URL, ingestion
timestamp and source hash per record, replacing the manual capture this record
documents.
