"""`quantstream-fetch-dataset` — the entry point behind `make fetch-hf-demo`.

Fetches (or regenerates) the official demo dataset, verifies SHA-256 checksums, and
prints a precise, honest summary. Exits non-zero on any checksum failure.
"""

from __future__ import annotations

import argparse
import sys

from .bootstrap import HF_REPO
from .checksums import ChecksumError
from .registry import DatasetStatus, fetch_dataset

_SOURCE_LABEL = {
    "cache": "local cache (already present)",
    "huggingface": "Hugging Face",
    "generated": "local generation (offline fallback)",
}


def _print_status(status: DatasetStatus) -> None:
    v = status.verify
    print(f"Fetched dataset: {HF_REPO}")
    print(f"Source:          {_SOURCE_LABEL.get(status.source, status.source)}")
    print(f"Revision:        {status.revision}")
    print(f"Files verified:  {v.summary()}")
    print(f"Checksum status: {'PASS' if v.ok else 'FAIL'}")
    print(f"Dataset ready:   {status.data_dir}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch and verify the QuantStream Labs Alpha Mirage dataset."
    )
    parser.add_argument(
        "--force", action="store_true", help="ignore local cache and re-fetch"
    )
    parser.add_argument(
        "--no-hf",
        action="store_true",
        help="skip Hugging Face; use local cache or regenerate offline",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="alias for --no-hf (never touch the network)",
    )
    parser.add_argument(
        "--revision", default=None, help="pin a specific Hugging Face revision"
    )
    args = parser.parse_args(argv)

    try:
        status = fetch_dataset(
            prefer_hf=not (args.no_hf or args.offline),
            revision=args.revision,
            force=args.force,
        )
    except ChecksumError as exc:
        print(f"Checksum status: FAIL\nERROR: {exc}", file=sys.stderr)
        return 1

    _print_status(status)
    return 0 if status.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
