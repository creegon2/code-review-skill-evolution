"""Public contracts for an isolated code-review Skill evolution run."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping

from .hashing import canonical_json, sha256_file, sha256_text, sha256_tree


_SAFE_ID = re.compile(r"^[A-Za-z0-9._@-]+$")
_SEVERITIES = frozenset({"Critical", "Major", "Minor", "Trivial", "Info"})
_FORBIDDEN_METADATA_KEY_FRAGMENTS = frozenset(
    {
        "answer",
        "credential",
        "expected",
        "gold",
        "label",
        "oracle",
        "reference",
        "secret",
        "token",
        "trace",
    }
)


def validate_id(value: str, label: str) -> str:
    normalized = str(value).strip()
    if not normalized or _SAFE_ID.fullmatch(normalized) is None:
        raise ValueError(f"{label} must match {_SAFE_ID.pattern}")
    return normalized


def _contains(path: Path, possible_child: Path) -> bool:
    try:
        possible_child.relative_to(path)
    except ValueError:
        return False
    return True


def _validate_public_metadata(value: Any, location: str = "metadata") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{location} keys must be strings")
            normalized = re.sub(r"[^a-z0-9]+", "_", key.casefold())
            blocked = sorted(
                fragment
                for fragment in _FORBIDDEN_METADATA_KEY_FRAGMENTS
                if fragment in normalized
            )
            if blocked:
                raise ValueError(
                    f"{location}.{key} is controller-only by key policy "
                    f"({blocked[0]})"
                )
            _validate_public_metadata(nested, f"{location}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _validate_public_metadata(nested, f"{location}[{index}]")
        return
    if value is None or isinstance(value, (str, int, float, bool)):
        return
    raise TypeError(f"{location} must contain JSON-safe public values")


@dataclass(frozen=True)
class TaskPackage:
    """One task with a controller-only reference kept outside its snapshot."""

    task_id: str
    snapshot: Path
    diff: Path
    private_reference: Path
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "task_id", validate_id(self.task_id, "task_id"))
        raw_snapshot = Path(self.snapshot)
        raw_diff = Path(self.diff)
        if raw_snapshot.is_symlink():
            raise ValueError("snapshot root may not be a symlink")
        if raw_diff.is_symlink():
            raise ValueError("diff may not be a symlink")
        snapshot = raw_snapshot.resolve()
        diff = raw_diff.resolve()
        reference = Path(self.private_reference).resolve()
        if not snapshot.is_dir():
            raise NotADirectoryError(snapshot)
        if not diff.is_file():
            raise FileNotFoundError(diff)
        if not reference.is_file():
            raise FileNotFoundError(reference)
        if diff == reference:
            raise ValueError("diff and private_reference must be different files")
        if _contains(snapshot, reference):
            raise ValueError("private_reference must live outside the reviewer snapshot")
        _validate_public_metadata(self.metadata)
        # The round trip both validates non-finite numbers and takes an
        # immutable-by-convention deep copy of nested caller objects.
        normalized_metadata = json.loads(canonical_json(dict(self.metadata)))
        object.__setattr__(self, "snapshot", snapshot)
        object.__setattr__(self, "diff", diff)
        object.__setattr__(self, "private_reference", reference)
        object.__setattr__(self, "metadata", normalized_metadata)

    def public_payload(self) -> dict[str, Any]:
        """Return exactly what the Reviewer may learn from task metadata."""

        return {
            "schema": "code-review-task-public-v1",
            "task_id": self.task_id,
            "snapshot_sha256": sha256_tree(self.snapshot),
            "diff_sha256": sha256_file(self.diff),
            "metadata": dict(self.metadata),
        }

    def frozen_identity(self) -> dict[str, Any]:
        """Return hashes for the Controller receipt without exposing file paths."""

        return {
            **self.public_payload(),
            "private_reference_sha256": sha256_file(self.private_reference),
        }


@dataclass(frozen=True)
class Finding:
    file: str
    start_line: int
    end_line: int
    severity: str
    summary: str
    description: str

    def __post_init__(self) -> None:
        if not self.file or Path(self.file).is_absolute() or ".." in Path(self.file).parts:
            raise ValueError("finding.file must be a safe snapshot-relative path")
        if isinstance(self.start_line, bool) or isinstance(self.end_line, bool):
            raise ValueError("finding line numbers must be integers")
        if int(self.start_line) < 1 or int(self.end_line) < int(self.start_line):
            raise ValueError("finding line range is invalid")
        if self.severity not in _SEVERITIES:
            raise ValueError(f"unsupported severity: {self.severity}")
        if not self.summary.strip() or not self.description.strip():
            raise ValueError("finding summary and description are required")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FindingBatch:
    findings: tuple[Finding, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "code-review-findings-v1",
            "findings": [finding.to_dict() for finding in self.findings],
        }


@dataclass(frozen=True)
class Score:
    primary: float
    secondary: float = 0.0
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for label, value in (("primary", self.primary), ("secondary", self.secondary)):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{label} must be numeric")
            if not math.isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{label} must be finite and between 0 and 1")
        object.__setattr__(self, "primary", float(self.primary))
        object.__setattr__(self, "secondary", float(self.secondary))
        object.__setattr__(self, "details", dict(self.details))

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "details": dict(self.details),
        }


@dataclass(frozen=True)
class AttemptSummary:
    task_id: str
    split: str
    skill_sha256: str
    finding_count: int
    score: Score
    failure: str = ""

    def __post_init__(self) -> None:
        validate_id(self.task_id, "task_id")
        validate_id(self.split, "split")
        if self.finding_count < 0:
            raise ValueError("finding_count must be non-negative")
        if re.fullmatch(r"[0-9a-f]{64}", self.skill_sha256) is None:
            raise ValueError("skill_sha256 must be a lowercase SHA-256 digest")
        if self.failure and _SAFE_ID.fullmatch(self.failure) is None:
            raise ValueError("failure must be an opaque code, not a raw error message")

    def optimizer_payload(self) -> dict[str, Any]:
        """A bounded trajectory summary with no reference or raw model output."""

        return {
            "task_id": self.task_id,
            "split": self.split,
            "skill_sha256": self.skill_sha256,
            "finding_count": self.finding_count,
            # Evaluator details stay controller-side because an injected
            # scorer could otherwise place labels, paths, or raw text here.
            "score": {
                "primary": self.score.primary,
                "secondary": self.score.secondary,
            },
            "failure": self.failure,
        }


@dataclass(frozen=True)
class GateDecision:
    accepted: bool
    reason: str
    incumbent: Score
    candidate: Score

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "reason": self.reason,
            "incumbent": self.incumbent.to_dict(),
            "candidate": self.candidate.to_dict(),
        }


@dataclass(frozen=True)
class RunResult:
    run_id: str
    status: str
    accepted_skill_sha256: str
    gate: GateDecision
    final_score: Score
    receipt_path: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "accepted_skill_sha256": self.accepted_skill_sha256,
            "gate": self.gate.to_dict(),
            "final_score": self.final_score.to_dict(),
            "receipt_path": self.receipt_path.name,
        }


def skill_sha256(skill: str) -> str:
    if not skill.strip():
        raise ValueError("Skill content may not be empty")
    return sha256_text(skill)


__all__ = [
    "AttemptSummary",
    "Finding",
    "FindingBatch",
    "GateDecision",
    "RunResult",
    "Score",
    "TaskPackage",
    "skill_sha256",
    "validate_id",
]
