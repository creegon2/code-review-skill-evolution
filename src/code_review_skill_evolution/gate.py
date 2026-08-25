"""Mechanical selection rules for candidate Skills."""

from __future__ import annotations

from collections.abc import Sequence

from .contracts import GateDecision, Score


def aggregate_scores(scores: Sequence[Score]) -> Score:
    if not scores:
        raise ValueError("at least one score is required")
    count = float(len(scores))
    return Score(
        primary=sum(score.primary for score in scores) / count,
        secondary=sum(score.secondary for score in scores) / count,
        details={"task_count": len(scores), "aggregation": "arithmetic_mean"},
    )


def strict_gate(incumbent: Score, candidate: Score) -> GateDecision:
    """Accept only a strict lexicographic improvement."""

    if candidate.primary > incumbent.primary:
        return GateDecision(True, "primary_improved", incumbent, candidate)
    if (
        candidate.primary == incumbent.primary
        and candidate.secondary > incumbent.secondary
    ):
        return GateDecision(True, "primary_tied_secondary_improved", incumbent, candidate)
    return GateDecision(False, "no_strict_improvement", incumbent, candidate)


__all__ = ["aggregate_scores", "strict_gate"]
