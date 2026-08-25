"""Deterministic hashing helpers used by the public orchestration core."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_json(value: Any) -> str:
    """Serialize JSON with stable ordering and no non-standard numbers."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: str | Path) -> str:
    target = Path(path)
    digest = hashlib.sha256()
    with target.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_tree(root: str | Path) -> str:
    """Hash relative names and bytes while rejecting symlink escapes."""

    base = Path(root).resolve()
    if not base.is_dir():
        raise NotADirectoryError(base)
    rows: list[dict[str, str]] = []
    for path in sorted(base.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise ValueError(f"snapshot trees may not contain symlinks: {path}")
        if path.is_file():
            rows.append(
                {
                    "path": path.relative_to(base).as_posix(),
                    "sha256": sha256_file(path),
                }
            )
    return sha256_text(canonical_json(rows))


__all__ = [
    "canonical_json",
    "sha256_bytes",
    "sha256_file",
    "sha256_text",
    "sha256_tree",
]
