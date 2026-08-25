"""A small end-to-end orchestrator with explicit role and data boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid
from typing import Any, Mapping, Sequence

from .backends import (
    EvaluatorBackend,
    OptimizationRequest,
    OptimizerBackend,
    ReviewerBackend,
    ReviewerRequest,
)
from .contracts import (
    AttemptSummary,
    FindingBatch,
    RunResult,
    Score,
    TaskPackage,
    skill_sha256,
    validate_id,
)
from .gate import aggregate_scores, strict_gate
from .hashing import canonical_json, sha256_text
from .isolation import prepare_reviewer_workspace


def new_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run-{timestamp}-{uuid.uuid4().hex[:12]}"


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(encoded, encoding="utf-8", newline="\n")
    temporary.replace(path)


@dataclass(frozen=True)
class PipelineConfig:
    run_id: str
    run_root: Path
    checkout_root: Path
    initial_skill: str
    train_tasks: tuple[TaskPackage, ...]
    selection_tasks: tuple[TaskPackage, ...]
    final_tasks: tuple[TaskPackage, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "run_id", validate_id(self.run_id, "run_id"))
        run_root = Path(self.run_root).resolve()
        checkout_root = Path(self.checkout_root).resolve()
        if _is_within(run_root, checkout_root):
            raise ValueError("run_root must be outside the Git checkout")
        if not self.initial_skill.strip():
            raise ValueError("initial_skill may not be empty")
        for label, tasks in (
            ("train_tasks", self.train_tasks),
            ("selection_tasks", self.selection_tasks),
            ("final_tasks", self.final_tasks),
        ):
            if not tasks:
                raise ValueError(f"{label} may not be empty")
        all_ids = [
            task.task_id
            for tasks in (self.train_tasks, self.selection_tasks, self.final_tasks)
            for task in tasks
        ]
        if len(all_ids) != len(set(all_ids)):
            raise ValueError("train, selection, and final task IDs must be disjoint")
        object.__setattr__(self, "run_root", run_root)
        object.__setattr__(self, "checkout_root", checkout_root)


class EvolutionPipeline:
    """Run baseline, proposal, strict selection, and final evaluation once."""

    def __init__(
        self,
        *,
        reviewer: ReviewerBackend,
        optimizer: OptimizerBackend,
        evaluator: EvaluatorBackend,
    ) -> None:
        self.reviewer = reviewer
        self.optimizer = optimizer
        self.evaluator = evaluator

    def _attempt(
        self,
        *,
        config: PipelineConfig,
        split: str,
        variant: str,
        skill: str,
        tasks: Sequence[TaskPackage],
    ) -> list[AttemptSummary]:
        summaries: list[AttemptSummary] = []
        skill_hash = skill_sha256(skill)
        for index, task in enumerate(tasks, start=1):
            attempt_id = validate_id(
                f"{split}-{variant}-{index:04d}-{task.task_id}",
                "attempt_id",
            )
            workspace_root = config.run_root / "workspaces"
            workspace = prepare_reviewer_workspace(
                workspace_root,
                attempt_id,
                task,
                skill,
            )
            request = ReviewerRequest(
                attempt_id=attempt_id,
                workspace=workspace,
                task=task.public_payload(),
                skill=skill,
            )
            findings = self.reviewer.review(request)
            if not isinstance(findings, FindingBatch):
                raise TypeError("ReviewerBackend.review must return FindingBatch")
            score = self.evaluator.score(task, findings)
            if not isinstance(score, Score):
                raise TypeError("EvaluatorBackend.score must return Score")
            artifact_root = config.run_root / "artifacts" / attempt_id
            _atomic_json(artifact_root / "findings.json", findings.to_dict())
            _atomic_json(artifact_root / "score.json", score.to_dict())
            summaries.append(
                AttemptSummary(
                    task_id=task.task_id,
                    split=split,
                    skill_sha256=skill_hash,
                    finding_count=len(findings.findings),
                    score=score,
                )
            )
        return summaries

    @staticmethod
    def _stage(
        stages: list[dict[str, Any]],
        name: str,
        status: str,
        **facts: Any,
    ) -> None:
        stages.append({"name": name, "status": status, **facts})

    def run(self, config: PipelineConfig) -> RunResult:
        root = config.run_root
        if root.exists() and any(root.iterdir()):
            raise FileExistsError(f"run_root must be new or empty: {root}")
        root.mkdir(parents=True, exist_ok=True)
        stages: list[dict[str, Any]] = []
        receipt_path = root / "terminal-receipt.json"
        manifest_sha256: str | None = None
        try:
            manifest = {
                "schema": "code-review-skill-evolution-manifest-v1",
                "run_id": config.run_id,
                "initial_skill_sha256": skill_sha256(config.initial_skill),
                "splits": {
                    "train": [task.frozen_identity() for task in config.train_tasks],
                    "selection": [
                        task.frozen_identity() for task in config.selection_tasks
                    ],
                    "final": [
                        task.frozen_identity() for task in config.final_tasks
                    ],
                },
            }
            manifest["identity_sha256"] = sha256_text(canonical_json(manifest))
            manifest_sha256 = manifest["identity_sha256"]
            _atomic_json(root / "manifest.json", manifest)
            self._stage(
                stages,
                "freeze_inputs",
                "complete",
                manifest_sha256=manifest_sha256,
            )

            train = self._attempt(
                config=config,
                split="train",
                variant="incumbent",
                skill=config.initial_skill,
                tasks=config.train_tasks,
            )
            self._stage(stages, "reviewer_rollout_and_evaluation", "complete", task_count=len(train))

            proposal = self.optimizer.propose(
                OptimizationRequest.from_attempts(config.initial_skill, train)
            )
            candidate_hash = skill_sha256(proposal)
            (root / "candidate-skill.md").write_text(
                proposal,
                encoding="utf-8",
                newline="\n",
            )
            self._stage(stages, "candidate_proposal", "complete", candidate_skill_sha256=candidate_hash)

            incumbent_selection = self._attempt(
                config=config,
                split="selection",
                variant="incumbent",
                skill=config.initial_skill,
                tasks=config.selection_tasks,
            )
            candidate_selection = self._attempt(
                config=config,
                split="selection",
                variant="candidate",
                skill=proposal,
                tasks=config.selection_tasks,
            )
            incumbent_score = aggregate_scores(
                [attempt.score for attempt in incumbent_selection]
            )
            candidate_score = aggregate_scores(
                [attempt.score for attempt in candidate_selection]
            )
            gate = strict_gate(incumbent_score, candidate_score)
            accepted_skill = proposal if gate.accepted else config.initial_skill
            self._stage(stages, "strict_selection_gate", "complete", **gate.to_dict())

            final_attempts = self._attempt(
                config=config,
                split="final",
                variant="accepted",
                skill=accepted_skill,
                tasks=config.final_tasks,
            )
            final_score = aggregate_scores([attempt.score for attempt in final_attempts])
            accepted_hash = skill_sha256(accepted_skill)
            self._stage(
                stages,
                "final_evaluation",
                "complete",
                accepted_skill_sha256=accepted_hash,
                score=final_score.to_dict(),
            )
            receipt = {
                "schema": "code-review-skill-evolution-terminal-v1",
                "run_id": config.run_id,
                "status": "complete",
                "manifest_sha256": manifest_sha256,
                "gate": gate.to_dict(),
                "accepted_skill_sha256": accepted_hash,
                "final_score": final_score.to_dict(),
                "stages": stages,
                "outcome_scope": "operator-supplied data and backends only",
            }
            _atomic_json(receipt_path, receipt)
            return RunResult(
                run_id=config.run_id,
                status="complete",
                accepted_skill_sha256=accepted_hash,
                gate=gate,
                final_score=final_score,
                receipt_path=receipt_path,
            )
        except Exception as exc:
            self._stage(
                stages,
                "terminal",
                "failed",
                error_type=type(exc).__name__,
                error=str(exc),
            )
            _atomic_json(
                receipt_path,
                {
                    "schema": "code-review-skill-evolution-terminal-v1",
                    "run_id": config.run_id,
                    "status": "failed",
                    "manifest_sha256": manifest_sha256,
                    "stages": stages,
                },
            )
            raise


__all__ = ["EvolutionPipeline", "PipelineConfig", "new_run_id"]
