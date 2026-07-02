"""Where the official demo dataset lives on disk.

The dataset directory is resolved in this order:

  1. ``QUANTSTREAM_DATA_DIR`` environment variable (explicit override).
  2. ``<repo-root>/data/demo`` found by walking up from the current working
     directory looking for a repo marker (a directory holding both ``Makefile``
     and ``services/``).
  3. The same search starting from this module's location (covers editable
     installs run from an unrelated CWD).
  4. ``<cwd>/data/demo`` as a last resort.

Keeping this deterministic and env-overridable is what lets the demo run the same
way locally, in CI, and inside the Docker image (which sets the env var).
"""

from __future__ import annotations

import os
from pathlib import Path

ENV_VAR = "QUANTSTREAM_DATA_DIR"
_DATA_SUBPATH = ("data", "demo")


def _looks_like_repo_root(path: Path) -> bool:
    return (path / "Makefile").is_file() and (path / "services").is_dir()


def _search_upward(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        if _looks_like_repo_root(candidate):
            return candidate
    return None


def repo_root() -> Path | None:
    """Best-effort repo root, or None if it cannot be located."""
    return _search_upward(Path.cwd()) or _search_upward(Path(__file__).resolve())


def resolve_data_dir() -> Path:
    """Absolute path to the demo dataset directory (may not exist yet)."""
    override = os.environ.get(ENV_VAR)
    if override:
        return Path(override).expanduser().resolve()

    root = repo_root()
    if root is not None:
        return root.joinpath(*_DATA_SUBPATH)

    return Path.cwd().joinpath(*_DATA_SUBPATH)
