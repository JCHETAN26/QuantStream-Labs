"""Thin, optional Hugging Face Hub adapter.

Hugging Face is a *dataset registry*, not a runtime dependency. ``huggingface_hub``
is an optional extra; if it is not installed, or there is no network, the caller
falls back to the committed/local dataset. Nothing here is imported at package load
time — the import happens inside the functions so the whole system works offline.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HFDownload:
    revision: str
    local_dir: Path


class HFUnavailable(RuntimeError):
    """Raised when Hugging Face cannot be used (no library or no network)."""


def is_available() -> bool:
    try:
        import huggingface_hub  # noqa: F401
    except ImportError:
        return False
    return True


def download_snapshot(
    repo_id: str,
    destination: Path,
    *,
    revision: str | None = None,
    filenames: tuple[str, ...] | None = None,
) -> HFDownload:
    """Download the dataset snapshot into ``destination``.

    Returns the resolved revision (commit hash) so it can be pinned/recorded.
    Raises HFUnavailable if the hub library is missing or the download fails.
    """
    try:
        from huggingface_hub import snapshot_download
        from huggingface_hub.utils import HfHubHTTPError
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise HFUnavailable(
            "huggingface_hub is not installed; install the 'hf' extra or run offline"
        ) from exc

    destination.mkdir(parents=True, exist_ok=True)
    try:
        resolved = snapshot_download(
            repo_id=repo_id,
            repo_type="dataset",
            revision=revision,
            local_dir=str(destination),
            allow_patterns=list(filenames) if filenames else None,
        )
    except (HfHubHTTPError, OSError, ValueError) as exc:  # network / auth / not found
        raise HFUnavailable(f"Hugging Face download failed: {exc}") from exc

    return HFDownload(revision=_resolve_revision(repo_id, revision), local_dir=Path(resolved))


def _resolve_revision(repo_id: str, revision: str | None) -> str:
    """Best-effort resolution of the concrete commit hash for provenance."""
    try:
        from huggingface_hub import HfApi

        info = HfApi().dataset_info(repo_id, revision=revision)
        return info.sha or (revision or "unknown")
    except Exception:  # noqa: BLE001 - provenance is best-effort, never fatal
        return revision or "unknown"
