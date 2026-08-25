"""Dependency-injection boundaries for Reviewer, Optimizer, and Evaluator."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

from .contracts import AttemptSummary, FindingBatch, Score, TaskPackage


@dataclass(frozen=True)
class ReviewerRequest:
    attempt_id: str
    workspace: Path
    task: Mapping[str, Any]
    skill: str


@dataclass(frozen=True)
class OptimizationRequest:
    current_skill: str
    trajectories: tuple[Mapping[str, Any], ...]

    @classmethod
    def from_attempts(
        cls,
        current_skill: str,
        attempts: Sequence[AttemptSummary],
    ) -> "OptimizationRequest":
        return cls(
            current_skill=current_skill,
            trajectories=tuple(attempt.optimizer_payload() for attempt in attempts),
        )


class ReviewerBackend(Protocol):
    def review(self, request: ReviewerRequest) -> FindingBatch:
        """Run one fresh Reviewer attempt."""


class OptimizerBackend(Protocol):
    def propose(self, request: OptimizationRequest) -> str:
        """Return one candidate Skill from bounded trajectory summaries."""


class EvaluatorBackend(Protocol):
    def score(self, task: TaskPackage, findings: FindingBatch) -> Score:
        """Evaluate findings with controller-only task material."""


__all__ = [
    "EvaluatorBackend",
    "OptimizationRequest",
    "OptimizerBackend",
    "ReviewerBackend",
    "ReviewerRequest",
]
