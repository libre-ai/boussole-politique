**English** · [Français](README.fr.md)

> [!NOTE]
> **Reserved · future home of Boussole Politique** — rebuilt in the canonical base repository [`libre-ai/libre-ai`](https://github.com/libre-ai/libre-ai) ([multi-repo topology, ADR-0008](https://github.com/libre-ai/libre-ai/blob/main/docs/adr/0008-multi-repo-target-topology-and-brand.md)).
> This repository will reopen as the real product repository when the owner activates it, consuming the base as a versioned dependency. The foundations described below are **being built now** — with links to the code that already exists.

# Boussole Politique

**Compare your civic priorities to sourced public votes — locally, privately, without profiling.** A person responds to symmetric sourced statements, and Boussole computes a transparent comparison with exact denominators, abstentions, and missing data visible — all on device. No political label, no voting advice, no account required. Political opinion data stays encrypted, local, and under user control.

The canonical brief it answers: _"show me where my positions align with the public record"_ — independent of any ideological label or endorsement, using only data the person confirms and audits themselves.

## Why it's different

- **Transparent method, not a recommendation.** Every comparison shows you the scoring formula, dataset version, selection method, which votes were considered or missing, and who reviewed it — before you respond. The result binds your exact response set and method version; if either changes, it recomputes.
- **Local by default, encrypted at rest.** Responses never leave your device. Art. 9 political-opinion data is persisted locally under an AES-256-GCM envelope, keyed to a mandatory passphrase (minimum 12 chars, PBKDF2-SHA256 600k). No server, no analytics, no profile.
- **Deny public scoring without review.** Public voting datasets and scoring methods are published only after independent methodological _and_ privacy/legal reviewers explicitly approve exact dataset/method hashes. No automatic publication, no agent self-approval.
- **Sources visible, aggregates only.** Every public vote is sourced (legislative record, public survey, published poll). Individual identities are never computed or exposed; only aggregated vote counts above a minimum threshold (at least 5, small-group exclusion). Sources and extraction methods are documented and reviewable.
- **Deterministic and auditable.** The same person, responses, method and dataset always produce identical results. Comparison is computed locally by a deterministic WASM component; results can be reproduced offline.
- **Accessible offline.** The full questionnaire, dataset, and scoring are available offline after one download. Keyboard and screen reader accessible; no graphics-only indicators.

## Status — spec-published, foundations under construction

Boussole Politique is being rebuilt from locked contracts. It is **not released yet**; the client-side questionnaire and local persistence come first, and a good part already exists and is proven in the base repository:

| Foundation                                                      | State        | Evidence                                                                                                                                                                                        |
| --------------------------------------------------------------- | ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`boussole-method.v2`** — locked method/scoring schema         | ✅ published | Schema committed; WIT world and normative semantics ([contracts/wit/boussole-scoring-v2/world.wit](https://github.com/libre-ai/libre-ai/blob/main/contracts/wit/boussole-scoring-v2/world.wit)) |
| **`boussole-response-set.v2`** — locked local response schema   | ✅ published | Schema committed; response persistence validated                                                                                                                                                |
| **Client questionnaire** — accessible SSR baseline              | ✅ built     | React PWA, hydrating local-only; keyboard/screen reader accessible; offline capable ([#186](https://github.com/libre-ai/libre-ai/pull/186))                                                     |
| **IndexedDB adapter** — persistent local response store         | ✅ built     | Symmetric encryption AES-256-GCM, passphrase-gated; tested offline restore ([#185](https://github.com/libre-ai/libre-ai/pull/185), [#206](https://github.com/libre-ai/libre-ai/pull/206))       |
| **Data ownership controls** — export / confirmed delete         | ✅ built     | User-initiated local export (non-identifying) and irreversible delete; no server erasure needed ([#189](https://github.com/libre-ai/libre-ai/pull/189))                                         |
| **Dataset upgrade preview** — recompute with new method/dataset | ✅ built     | User can preview impact before accepting; response migration compatible ([#160](https://github.com/libre-ai/libre-ai/pull/160))                                                                 |
| **No-transmission guard** — network interception proof          | ✅ tested    | E2E tests confirm zero response/result transmission on the wire ([#182](https://github.com/libre-ai/libre-ai/pull/182))                                                                         |
| **Scoring core candidate** — pure WASM deterministic comparison | ⏳ next      | WIT world and golden test vectors locked; Rust/WASM implementation pending                                                                                                                      |
| Public dataset/method review and publication                    | ⏳ pending   | Independent methodological and legal/privacy approvers required (ADR-0002); no public scoring until explicit approval                                                                           |

This repository is `private` until a secrets audit clears it for public reopening (wave 4). **Benchmark target:** Voting Advice Application governance (e.g. Wahl-O-Mat, iSideWith) — transparent sourcing and deterministic local scoring rather than recommendation.

## How it works

1. **Inspect first** — user reads dataset version, public voting sources, selection method, scoring formula, treatment of abstentions and missing data, review evidence, and any limitations — all before responding.
2. **Respond locally** — user answers symmetric sourced statements. Responses are saved only to IndexedDB under passphrase-gated AES-256-GCM encryption, never transmitted or logged.
3. **Compute locally** — deterministic WASM evaluates the person's response set against the public vote dataset using the approved method. Comparison is transparent: visible denominator, missing votes, per-statement contribution, and any abstentions.
4. **Export or delete** — user can export a non-identifying local result (response hashes, dataset version, comparison result) for their records, or irreversibly delete all local responses. No server table, no account, no recovery.

## Architecture — built from interoperable bricks

Boussole Politique is a product assembled from independently versioned bricks; each is usable and testable on its own, and the product is their composition (the multi-repo target of [ADR-0008](https://github.com/libre-ai/libre-ai/blob/main/docs/adr/0008-multi-repo-target-topology-and-brand.md)).

| Brick                                              | Role                                                         | Interface it exposes / consumes                                                                                                                                                                                                                                                  |
| -------------------------------------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`boussole-method.v2` schema**                    | Locked method definition and scoring contract                | JSON Schema + WIT world; defines statement grouping, aggregation floor, small-group exclusion, method version binding                                                                                                                                                            |
| **`boussole-response-set.v2` schema**              | Locked user response envelope                                | JSON Schema; persisted to IndexedDB, encrypted; binds exact dataset/method version and response hashes                                                                                                                                                                           |
| **Client questionnaire (React PWA)**               | SSR baseline, local questionnaire UI, persistence controller | GET dataset, render statements, accept/skip/delete responses, encrypt-to-IndexedDB, preview upgrades                                                                                                                                                                             |
| **IndexedDB store + symmetric encryption**         | Persistent local storage with at-rest encryption             | AES-256-GCM envelope keyed to mandatory passphrase; PBKDF2-SHA256 600k derivation; local-only, no unlock key escapes                                                                                                                                                             |
| **Scoring core candidate** (Rust → WASM component) | Deterministic comparison engine (pending)                    | WIT world `boussole-scoring-v2`: `compare(method, dataset, response_set) → comparison`, capability-free                                                                                                                                                                          |
| **Contracts** — locked interoperability            | Sourced facts, voting dataset, scoring semantics             | `boussole-method.v2`, `boussole-response-set.v2`, WIT world, `SEMANTICS.md`, golden test vectors ([contracts/fixtures/boussole-scoring-v2/golden-vectors.v1.json](https://github.com/libre-ai/libre-ai/blob/main/contracts/fixtures/boussole-scoring-v2/golden-vectors.v1.json)) |

The questionnaire app performs authorization (passphrase gates read/write), passes canonical request/response bytes to the scoring engine (when ready), and the engine holds no token and performs no I/O. Any consumer that speaks the contracts can validate the same comparison locally.

## Where the work happens

All active development is in the base repository, under:

- `apps/boussole` — the product host (PWA questionnaire, local persistence, upgrade preview, export/delete UI)
- `contracts/schemas/boussole-method.v2.schema.json` and `boussole-response-set.v2.schema.json` — locked schemas
- `contracts/wit/boussole-scoring-v2/` — WIT world definition, normative semantics, and golden test vectors
- `contracts/fixtures/boussole-scoring-v2/golden-vectors.v1.json` — conformance test suite for the pending Rust/WASM core
- [`docs/apps/boussole.md`](https://github.com/libre-ai/libre-ai/blob/main/docs/apps/boussole.md) — the full product brief

To follow progress or contribute, open issues and pull requests in [`libre-ai/libre-ai`](https://github.com/libre-ai/libre-ai). This repository stays reserved until activation.

## License

EUPL-1.2.
