#!/usr/bin/env bash
set -euo pipefail

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

command -v cargo >/dev/null 2>&1 || {
  printf '%s\n' 'gate Rust bloqué: cargo est absent de cet environnement.' >&2
  exit 127
}

if grep -R --include='Cargo.toml' -E '(dioxus|axum)' crates/domain crates/scoring; then
  printf '%s\n' 'dépendance Dioxus/axum interdite dans domain ou scoring' >&2
  exit 1
fi

cargo fmt --all --check
cargo clippy --workspace --all-targets --all-features -- -D warnings
cargo test --workspace --all-targets --all-features
cargo build --workspace --target wasm32-unknown-unknown
