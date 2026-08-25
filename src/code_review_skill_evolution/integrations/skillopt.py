"""Public provenance and a narrow adapter boundary for official SkillOpt."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, Mapping

from ..backends import OptimizationRequest


OFFICIAL_REPOSITORY = "https://github.com/microsoft/SkillOpt"
VALIDATED_BASE_COMMIT = "3c8873f016397817dcd40c3e5436d92fe19372b8"


class SkillOptProposalBoundary:
    """Wrap an operator-owned official SkillOpt proposal call.

    The public core does not copy Trainer, reflection, merge, or gate logic.
    A formal integration supplies a callable backed by the pinned official
    checkout and receives only summary trajectories.
    """

    def __init__(
        self,
        propose: Callable[[str, Sequence[Mapping[str, Any]]], str],
    ) -> None:
        self._propose = propose

    def propose(self, request: OptimizationRequest) -> str:
        candidate = self._propose(
            request.current_skill,
            request.trajectories,
        )
        if not isinstance(candidate, str) or not candidate.strip():
            raise ValueError("official SkillOpt integration returned an empty candidate")
        return candidate


__all__ = [
    "OFFICIAL_REPOSITORY",
    "SkillOptProposalBoundary",
    "VALIDATED_BASE_COMMIT",
]
