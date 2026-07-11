"""Repository-relative paths shared by the historical dry-run scripts."""

from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
DRY_RUN_DIR = SCRIPTS_DIR.parent
REPO_ROOT = DRY_RUN_DIR.parent
DATA_DIR = DRY_RUN_DIR / "data"
OUT_DIR = DRY_RUN_DIR / "out"
