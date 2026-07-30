from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable


VENDOR_ROOT = Path(__file__).resolve().parent / "vendor"
if not (VENDOR_ROOT / "identifiers" / "normalize.py").exists():
    raise RuntimeError("dependency not materialized; run fetch_dependency.py")

sys.path.insert(0, str(VENDOR_ROOT))

from identifiers.normalize import UnsafeIdentifier, normalize_identifier  # noqa: E402


def canonicalize_external_keys(raw_keys: Iterable[str]) -> list[str]:
    """Normalize and deduplicate externally supplied keys in encounter order."""
    seen: set[str] = set()
    canonical: list[str] = []

    for raw in raw_keys:
        key = normalize_identifier(raw)
        if key not in seen:
            seen.add(key)
            canonical.append(key)

    return canonical


__all__ = [
    "UnsafeIdentifier",
    "canonicalize_external_keys",
    "normalize_identifier",
]
