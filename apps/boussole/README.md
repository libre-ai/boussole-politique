# @libre-ai/boussole

Boussole is the couche-1 civic self-positioning app. It runs a questionnaire
**entirely on the citizen's device**: answers are compared against reference
datasets to locate the respondent on published axes, and **nothing is
transmitted** — no response ever leaves local storage.

Work package: `WP-G3-B01`.

## Increment 1 — local response-set domain

`src/domain/response-set.ts` is the pure, offline heart of the local workflow. A
response set binds the exact `datasetId`/`datasetDigest` and `methodId`/
`methodDigest` hashes and holds one answer (integer in `[-5, 5]`) or one skip per
statement.

| Operation            | Guarantee                                                                                                |
| -------------------- | -------------------------------------------------------------------------------------------------------- |
| `startQuestionnaire` | fail-closed: malformed binding, empty/oversized (>1000) or duplicate/malformed statement ids are refused |
| `recordResponse`     | out-of-scale values and unknown statements refused; re-answering replaces in place                       |
| `skipStatement`      | abstention preserved, never hidden                                                                       |
| `deleteResponses`    | erases every response, keeps the binding to restart                                                      |
| `exportResponseSet`  | serializes to `boussole-response-set.v2`; empty export refused                                           |

Refusals share the canonical code `boussole.local_state_corrupt`. The
`response_transmission_forbidden` invariant is **structural** in this module: it
imports nothing and exposes no network path, so there is no channel to violate.
`exportResponseSet` returns a plain, serializable value for a **local file** — a
caller must not upload it. Downstream, the invariant is reinforced by the
absence of any API that accepts responses (spec §Non-goals).

## Increment 2 — local persistence core

`src/persistence/local-response-store.ts` lets a response set survive a reload
without ever leaving the device. It is storage-agnostic: a serializer, a
fail-closed deserializer, a `LocalResponseStore` port, and an in-memory adapter.

| Function                      | Guarantee                                                                                                    |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `serializeResponseSet`        | encodes to a device-local string only (never a network payload)                                              |
| `deserializeResponseSet`      | rebuilds **through the domain** (`startQuestionnaire` + record/skip); any corruption → `local_state_corrupt` |
| `LocalResponseStore` port     | async `save` / `load` / `clear`; `load` surfaces corruption as a `corrupt` result rather than throwing       |
| `createInMemoryResponseStore` | stores the encoded string, so `load` runs the true decode path and rejects tampered bytes                    |

Because rehydration replays through the domain, a tampered store (an out-of-scale
value, an unknown statement id, a malformed binding) can never load into an
invalid state — it is refused, not silently accepted.

### Not yet built (deliberately deferred)

- The concrete **IndexedDB adapter** implementing `LocalResponseStore` (browser
  runtime), the offline **PWA cockpit**, and the upgrade/explain preview.
- The deterministic **Rust/WASM scoring core** (`ComputeLocalComparison`): scoring
  is unavailable rather than approximated by a divergent JS formula.
- **Public scoring** stays compile-disabled until the two methodological and
  legal approvals required by `ADR-0002`.

## License

EUPL-1.2.
