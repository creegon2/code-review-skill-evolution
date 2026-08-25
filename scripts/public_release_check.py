"""Fail when a public source tree contains common private-release artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import tarfile
from typing import Iterable, Sequence
import zipfile


FORBIDDEN_SEGMENTS = {
    "artifacts",
    "candidate-runs",
    "codex-home",
    "datasets",
    "evidence",
    "formal-runs",
    "gold",
    "instances",
    "labels",
    "raw-traces",
    "references",
    "receipts",
    "results",
    "runs",
    "snapshots",
    "traces",
}
FORBIDDEN_SUFFIXES = {
    ".7z",
    ".db",
    ".jsonl",
    ".parquet",
    ".p12",
    ".pem",
    ".pfx",
    ".sqlite",
    ".sqlite3",
    ".whl",
    ".zip",
}
CONTENT_PATTERNS = {
    "Windows user path": re.compile(r"[A-Za-z]:[\\/]Users[\\/]", re.IGNORECASE),
    "macOS user path": re.compile(r"/Users/[^/]+/"),
    "Linux user path": re.compile(r"/home/[^/]+/"),
    "GitHub classic token": re.compile(r"gh" + r"p_[A-Za-z0-9]{20,}"),
    "GitHub fine-grained token": re.compile(r"github_" + r"pat_[A-Za-z0-9_]{20,}"),
    "private key": re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
    "OpenAI-style secret": re.compile(r"sk-" + r"[A-Za-z0-9_-]{20,}"),
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "Slack token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{16,}"),
    "Hugging Face token": re.compile(r"hf_[A-Za-z0-9]{20,}"),
    "generic secret assignment": re.compile(
        r"(?:api[_-]?key|access[_-]?token|secret[_-]?key)"
        r"\s*[:=]\s*[\"']?[A-Za-z0-9_./+-]{16,}",
        re.IGNORECASE,
    ),
    "private source repository": re.compile(
        r"creegon2/" + r"skill-evolution-system",
        re.IGNORECASE,
    ),
    "formal experiment run id": re.compile(r"faithful-" + r"20[0-9]{6}T"),
}
TEXT_SUFFIXES = {
    ".cfg",
    ".cmd",
    ".csv",
    ".ini",
    ".json",
    ".lock",
    ".md",
    ".ndjson",
    ".py",
    ".rst",
    ".sql",
    ".tsv",
    ".toml",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
TEXT_FILENAMES = {
    "METADATA",
    "PKG-INFO",
    "RECORD",
    "WHEEL",
}
LOCAL_ONLY_SEGMENTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "venv",
}


def _git_files(root: Path) -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        return []
    return [
        root / part.decode("utf-8")
        for part in completed.stdout.split(b"\0")
        if part
    ]


def _all_files(root: Path) -> list[Path]:
    return [
        path
        for path in root.rglob("*")
        if path.is_file()
        and not {
            part.casefold() for part in path.relative_to(root).parts
        }.intersection(LOCAL_ONLY_SEGMENTS)
    ]


def inspect(root: Path, files: Iterable[Path]) -> list[str]:
    failures: list[str] = []
    scanner = (root / "scripts" / "public_release_check.py").resolve()
    for path in files:
        relative = path.resolve().relative_to(root).as_posix()
        parts = {part.casefold() for part in Path(relative).parts}
        blocked = sorted(parts.intersection(FORBIDDEN_SEGMENTS))
        if blocked:
            failures.append(f"{relative}: forbidden path segment {blocked[0]!r}")
        if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            failures.append(f"{relative}: forbidden release suffix {path.suffix}")
        if path.resolve() == scanner or path.suffix.casefold() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            failures.append(f"{relative}: non-UTF-8 text file")
            continue
        for label, pattern in CONTENT_PATTERNS.items():
            if pattern.search(text):
                failures.append(f"{relative}: matched {label}")
    return failures


def _archive_member_failures(
    archive_label: str,
    member_name: str,
    content: bytes | None,
) -> list[str]:
    relative = member_name.replace("\\", "/").lstrip("/")
    failures: list[str] = []
    parts = {part.casefold() for part in Path(relative).parts}
    blocked = sorted(parts.intersection(FORBIDDEN_SEGMENTS))
    if blocked:
        failures.append(
            f"{archive_label}!{relative}: forbidden path segment {blocked[0]!r}"
        )
    suffix = Path(relative).suffix.casefold()
    if suffix in FORBIDDEN_SUFFIXES:
        failures.append(
            f"{archive_label}!{relative}: forbidden release suffix {suffix}"
        )
    if (
        content is None
        or relative.endswith("scripts/public_release_check.py")
        or (
            suffix not in TEXT_SUFFIXES
            and Path(relative).name not in TEXT_FILENAMES
        )
    ):
        return failures
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        failures.append(f"{archive_label}!{relative}: non-UTF-8 text file")
        return failures
    for label, pattern in CONTENT_PATTERNS.items():
        if pattern.search(text):
            failures.append(f"{archive_label}!{relative}: matched {label}")
    return failures


def inspect_archives(root: Path) -> tuple[list[str], int]:
    dist = root / "dist"
    archives = sorted(dist.glob("*.whl")) + sorted(dist.glob("*.tar.gz"))
    failures: list[str] = []
    for archive in archives:
        label = archive.relative_to(root).as_posix()
        if archive.suffix.casefold() == ".whl":
            with zipfile.ZipFile(archive) as bundle:
                for info in bundle.infolist():
                    if info.is_dir():
                        continue
                    failures.extend(
                        _archive_member_failures(label, info.filename, bundle.read(info))
                    )
        else:
            with tarfile.open(archive, "r:*") as bundle:
                for member in bundle.getmembers():
                    if not member.isfile():
                        continue
                    stream = bundle.extractfile(member)
                    failures.extend(
                        _archive_member_failures(
                            label,
                            member.name,
                            None if stream is None else stream.read(),
                        )
                    )
    if not archives:
        failures.append("dist/: no wheel or source archive found")
    return failures, len(archives)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all-files", action="store_true")
    parser.add_argument("--archives", action="store_true")
    parser.add_argument("--root", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    root = (args.root or Path(__file__).resolve().parents[1]).resolve()
    files = _all_files(root) if args.all_files else _git_files(root)
    if not files:
        print("public release check: no files selected")
        return 2
    failures = inspect(root, files)
    archive_count = 0
    if args.archives:
        archive_failures, archive_count = inspect_archives(root)
        failures.extend(archive_failures)
    if failures:
        print("public release check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    suffix = f", {archive_count} archives" if args.archives else ""
    print(f"public release check passed: {len(files)} files{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
