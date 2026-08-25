"""Public, data-free orchestration core for code-review Skill evolution."""

from .backends import (
    EvaluatorBackend,
    OptimizationRequest,
    OptimizerBackend,
    ReviewerBackend,
    ReviewerRequest,
)
from .contracts import (
    AttemptSummary,
    Finding,
    FindingBatch,
    GateDecision,
    RunResult,
    Score,
    TaskPackage,
)
from .pipeline import EvolutionPipeline, PipelineConfig, new_run_id

__version__ = "0.1.0"

__all__ = [
    "AttemptSummary",
    "EvaluatorBackend",
    "EvolutionPipeline",
    "Finding",
    "FindingBatch",
    "GateDecision",
    "OptimizationRequest",
    "OptimizerBackend",
    "PipelineConfig",
    "ReviewerBackend",
    "ReviewerRequest",
    "RunResult",
    "Score",
    "TaskPackage",
    "new_run_id",
]
