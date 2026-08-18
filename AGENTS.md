# Boussole Politique Canonical Agent Rules

## Purpose

Boussole lets voters compare their own stated positions to elected representatives' actual recorded votes, without political labels — a local-only, account-less couche-1 product with at-rest encryption for sensitive responses.
Doctrine lives upstream: https://raw.githubusercontent.com/libre-ai/governance/main/docs/README.md

## Domain doctrine

- No accounts or user profiles; no political labeling of users; no data transmission — everything stays in the browser (`project.v1.yaml` non_goals).
- Sensitive (Art. 9) responses are AES-256-GCM encrypted at rest; the `check-no-transmission` gate proves no outbound primitive from `apps/boussole`.
- Bricks and contracts this repo depends on (`libre-ai/ui`, `libre-ai/web-platform`, `libre-ai/contracts`, `libre-ai/governance`) are consumed pinned by SHA in the manifest, never redefined here.

## Commands

- `bun install` — install dependencies (git-dep pinned bricks included).
- `bun run test` — run `apps/boussole`'s test suite.
- `bun run lint` — Biome CI lint.
- `bun run check` — the full gate chain (toolchain, tests, secret scan, personal-data boundary, no-transmission, lint); run before pushing.

## Working here

- Security > quality > performance > completeness, in that order on conflict.
- Check real state before editing: `git status --short` and `bun run test`.
- English for code, comments and this file; French stays the human conversation language elsewhere.
- Never commit a machine-local absolute filesystem path; use repo-relative paths or `~` instead.
