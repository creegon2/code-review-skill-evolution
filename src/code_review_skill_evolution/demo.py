"""A deterministic, no-model, no-dataset end-to-end smoke demonstration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
import uuid
from typing import Sequence

from .backends import OptimizationRequest, ReviewerRequest
from .contracts import Finding, FindingBatch, Score, TaskPackage
from .pipeline import EvolutionPipeline, PipelineConfig, new_run_id


class FakeReviewer:
    """A deterministic stand-in used only to exercise framework wiring."""

    def review(self, request: ReviewerRequest) -> FindingBatch:
        task_document = json.loads(
            (request.workspace / "task.json").read_text(encoding="utf-8")
        )
        serialized = json.dumps(task_document, ensure_ascii=False).casefold()
        if any(token in serialized for token in ("oracle", "answer", "reference_path")):
            raise RuntimeError("controller-only data reached the Reviewer workspace")
        if "resource cleanup" not in request.skill.casefold():
            return FindingBatch()
        return FindingBatch(
            (
                Finding(
                    file="src/worker.py",
                    start_line=3,
                    end_line=3,
                    severity="Major",
                    summary="Early return skips resource cleanup.",
                    description="Move cleanup before the return or use a guarded cleanup path.",
                ),
            )
        )


class FakeOptimizer:
    def propose(self, request: OptimizationRequest) -> str:
        if not request.trajectories:
            raise ValueError("the fake optimizer requires training summaries")
        return (
            request.current_skill.rstrip()
            + "\n\nCheck every changed early-return path for resource cleanup.\n"
        )


class PrivateReferenceEvaluator:
    """Read a controller-only exact expectation after the Reviewer stops."""

    def score(self, task: TaskPackage, findings: FindingBatch) -> Score:
        expected = json.loads(task.private_reference.read_text(encoding="utf-8"))
        expected_summary = str(expected["summary"])
        matches = [
            finding
            for finding in findings.findings
            if finding.file == expected["file"]
            and finding.start_line == int(expected["line"])
            and finding.summary == expected_summary
        ]
        primary = 1.0 if matches else 0.0
        secondary = min(1.0, len(findings.findings) / max(1, int(expected["count"])))
        return Score(
            primary=primary,
            secondary=secondary,
            details={"exact_match_count": len(matches)},
        )


def _task(root: Path, split: str) -> TaskPackage:
    task_root = root / "inputs" / split
    snapshot = task_root / "snapshot"
    (snapshot / "src").mkdir(parents=True)
    (snapshot / "src" / "worker.py").write_text(
        "def work(resource, stop):\n"
        "    result = resource.read()\n"
        "    if stop:\n"
        "        return result\n"
        "    resource.close()\n"
        "    return result\n",
        encoding="utf-8",
        newline="\n",
    )
    diff = task_root / "review.diff"
    diff.write_text(
        "diff --git a/src/worker.py b/src/worker.py\n"
        "@@ -1,4 +1,6 @@\n"
        "+    if stop:\n"
        "+        return result\n",
        encoding="utf-8",
        newline="\n",
    )
    reference_root = root / "controller-only"
    reference_root.mkdir(exist_ok=True)
    reference = reference_root / f"{split}.json"
    reference.write_text(
        json.dumps(
            {
                "file": "src/worker.py",
                "line": 3,
                "summary": "Early return skips resource cleanup.",
                "count": 1,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return TaskPackage(
        task_id=f"synthetic-{split}",
        snapshot=snapshot,
        diff=diff,
        private_reference=reference,
        metadata={"repository": "synthetic/local", "change": split},
    )


def run_demo(checkout_root: Path, run_root: Path) -> dict[str, object]:
    checkout_root = checkout_root.resolve()
    run_root = run_root.resolve()
    try:
        run_root.relative_to(checkout_root)
    except ValueError:
        pass
    else:
        raise ValueError("run_root must be outside the Git checkout")
    run_root.parent.mkdir(parents=True, exist_ok=True)
    pipeline = EvolutionPipeline(
        reviewer=FakeReviewer(),
        optimizer=FakeOptimizer(),
        evaluator=PrivateReferenceEvaluator(),
    )
    with tempfile.TemporaryDirectory(
        dir=run_root.parent,
        prefix=f".{run_root.name}-inputs-{uuid.uuid4().hex[:8]}-",
    ) as temporary:
        input_root = Path(temporary)
        result = pipeline.run(
            PipelineConfig(
                run_id=new_run_id(),
                run_root=run_root,
                checkout_root=checkout_root,
                initial_skill="# Code Review Skill\n\nReview changed code for correctness.\n",
                train_tasks=(_task(input_root, "train"),),
                selection_tasks=(_task(input_root, "selection"),),
                final_tasks=(_task(input_root, "final"),),
            )
        )
    return result.to_dict()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a synthetic, no-model framework smoke test."
    )
    parser.add_argument(
        "--run-root",
        type=Path,
        help="Optional external output directory. A temporary directory is used by default.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    checkout_root = Path(__file__).resolve().parents[2]
    if args.run_root is not None:
        payload = run_demo(checkout_root, args.run_root.resolve())
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    with tempfile.TemporaryDirectory(prefix="crse-offline-smoke-") as temporary:
        root = Path(temporary)
        payload = run_demo(checkout_root, root / "run")
        payload["artifacts_retained"] = False
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main", "run_demo"]
