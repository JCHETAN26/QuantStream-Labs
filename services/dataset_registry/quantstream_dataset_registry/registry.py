"""Dataset acquisition: cache-first, Hugging Face optional, offline-generatable.

Two entry points:

  ``ensure_dataset()``  — used by the demo. Never touches the network. Uses the
                          committed/cached dataset if it verifies, otherwise
                          regenerates it deterministically. This is what keeps the
                          local/Docker demo from ever being fragile.

  ``fetch_dataset()``   — used by ``make fetch-hf-demo``. Prefers a valid local
                          cache, then Hugging Face (if the extra + network are
                          available), then local generation. Always verifies
                          SHA-256 and fails loudly on mismatch.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from . import hf
from .bootstrap import HASHED_FILES, HF_REPO, write_dataset
from .checksums import (
    SHA256SUMS_NAME,
    VerifyResult,
    parse_sha256sums,
    sha256_bytes,
    verify_directory,
    verify_or_raise,
)
from .paths import resolve_data_dir

DATA_FILES = HASHED_FILES
PROVENANCE_NAME = ".provenance.json"


@dataclass(frozen=True)
class DatasetStatus:
    data_dir: Path
    source: str  # "cache" | "huggingface" | "generated"
    revision: str
    verify: VerifyResult

    @property
    def ready(self) -> bool:
        return self.verify.ok


def _load_sums(directory: Path) -> dict[str, str] | None:
    path = directory / SHA256SUMS_NAME
    if not path.is_file():
        return None
    return parse_sha256sums(path.read_text(encoding="utf-8"))


def _local_is_valid(directory: Path) -> VerifyResult | None:
    sums = _load_sums(directory)
    if sums is None:
        return None
    return verify_directory(directory, sums)


def _write_provenance(directory: Path, source: str, revision: str) -> None:
    payload = {"source": source, "revision": revision, "hf_repo": HF_REPO}
    (directory / PROVENANCE_NAME).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _generate(directory: Path) -> DatasetStatus:
    built = write_dataset(directory)
    sums = {name: sha256_bytes(built.files[name]) for name in HASHED_FILES}
    verify = verify_or_raise(directory, sums)
    _write_provenance(directory, "generated", "local")
    return DatasetStatus(directory, "generated", "local", verify)


def ensure_dataset(data_dir: Path | None = None, *, strict: bool = True) -> DatasetStatus:
    """Guarantee a valid dataset on disk without any network access.

    Behaviour, by design, for the demo path:

      * SHA256SUMS present and valid  -> use it (source="cache").
      * SHA256SUMS present but INVALID -> raise ChecksumError when ``strict`` (the
        default), so a tampered/corrupted file is never silently papered over.
        With ``strict=False`` (debug mode) it is regenerated instead.
      * No SHA256SUMS at all           -> generate it (offline fallback for a fresh
        environment or the Docker image).
    """
    directory = data_dir or resolve_data_dir()
    local = _local_is_valid(directory)
    if local is not None:
        if local.ok:
            return DatasetStatus(directory, "cache", _cached_revision(directory), local)
        if strict:
            verify_or_raise(directory, _load_sums(directory) or {})
        # non-strict: fall through and regenerate
    return _generate(directory)


def _cached_revision(directory: Path) -> str:
    path = directory / PROVENANCE_NAME
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8")).get("revision", "cache")
        except (ValueError, OSError):
            return "cache"
    return "cache"


def fetch_dataset(
    data_dir: Path | None = None,
    *,
    prefer_hf: bool = True,
    revision: str | None = None,
    force: bool = False,
    allow_generate: bool = True,
) -> DatasetStatus:
    """Fetch + verify the dataset for ``make fetch-hf-demo``.

    Order: valid local cache (unless ``force``) -> Hugging Face -> local generation.
    Verification runs against the dataset's shipped SHA256SUMS and raises on any
    mismatch.
    """
    directory = data_dir or resolve_data_dir()

    if not force:
        local = _local_is_valid(directory)
        if local is not None and local.ok:
            return DatasetStatus(directory, "cache", _cached_revision(directory), local)

    if prefer_hf and hf.is_available():
        try:
            download = hf.download_snapshot(HF_REPO, directory, revision=revision)
            sums = _load_sums(directory)
            if sums is None:
                raise hf.HFUnavailable("downloaded snapshot is missing SHA256SUMS")
            verify = verify_or_raise(directory, sums)
            _write_provenance(directory, "huggingface", download.revision)
            return DatasetStatus(directory, "huggingface", download.revision, verify)
        except hf.HFUnavailable:
            if not allow_generate:
                raise

    if not allow_generate:
        raise hf.HFUnavailable(
            "Hugging Face unavailable and local generation disabled"
        )
    return _generate(directory)
