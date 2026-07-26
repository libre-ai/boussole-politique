#!/usr/bin/env bash
# Guard: the committed brand manifest and its generator must declare the same licence.
#
# Why this exists, and why it is not a `git diff` against a regeneration:
# `assets/brand/manifest.json` was edited by hand to carry LicenseRef-Trademark
# while `scripts/generate-assets.sh` still wrote "MIT". Running the generator
# would have silently reclassified the brand assets. The CI job that was meant
# to catch this generated, hashed, regenerated and hashed again, then diffed the
# two *generations* — the committed bytes were destroyed before the first hash,
# so the divergence stayed invisible.
#
# A full `git diff --exit-code` after the first generation cannot be used: the
# committed PNGs are no longer byte-reproducible by the CI toolchain (librsvg /
# imagemagick versions are not pinned), so every hash-bearing field would differ
# for reasons unrelated to licensing. This check therefore targets exactly the
# field that broke, and depends on no regeneration at all.

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

MANIFEST="assets/brand/manifest.json"
GENERATOR="scripts/generate-assets.sh"

for f in "$MANIFEST" "$GENERATOR"; do
  if [ ! -f "$f" ]; then
    printf 'FATAL: %s is missing — this check is not looking at anything.\n' "$f" >&2
    exit 2
  fi
done

# `|| true` is load-bearing: under `set -euo pipefail`, a grep that matches
# nothing kills the script before it can report WHY it found nothing. A guard
# that dies silently on a missing field is exactly the failure mode this file
# exists to prevent.
manifest_licence=$(jq -r '.license // empty' "$MANIFEST" 2>/dev/null || true)
generator_licence=$(grep -oE '"license": "[^"]+"' "$GENERATOR" 2>/dev/null | sed 's/.*: "//; s/"$//' | head -1 || true)

# A missing value on either side means the field moved or was renamed: that is a
# broken check, not a passing one. Fail loudly rather than compare two blanks.
declared=0
[ -n "$manifest_licence" ] && declared=$((declared + 1))
[ -n "$generator_licence" ] && declared=$((declared + 1))

printf '   licence declarations examined: %d\n' "$declared"

if [ "$declared" -ne 2 ]; then
  printf 'FATAL: expected a licence field on both sides, found %d — the check is not looking at anything.\n' "$declared" >&2
  printf '       manifest=%s generator=%s\n' "${manifest_licence:-<none>}" "${generator_licence:-<none>}" >&2
  exit 2
fi

if [ "$manifest_licence" != "$generator_licence" ]; then
  printf 'FAIL: the committed manifest and its generator disagree on the licence.\n' >&2
  printf '      %s: %s\n' "$MANIFEST" "$manifest_licence" >&2
  printf '      %s: %s\n' "$GENERATOR" "$generator_licence" >&2
  printf '      Running the generator would overwrite the committed value.\n' >&2
  exit 1
fi

printf 'OK: manifest and generator agree on the licence (%s).\n' "$manifest_licence"
