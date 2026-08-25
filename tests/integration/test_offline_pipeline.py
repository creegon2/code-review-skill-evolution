from __future__ import annotations

import json
from pathlib import Path

from code_review_skill_evolution.demo import run_demo


def test_offline_demo_runs_complete_topology(tmp_path: Path) -> None:
    checkout_root = Path(__file__).resolve().parents[2]
    run_root = tmp_path / "external-run"
    result = run_demo(checkout_root, run_root)

    assert result["status"] == "complete"
    assert result["gate"]["accepted"] is True
    assert result["final_score"]["primary"] == 1.0
    receipt = json.loads(
        (run_root / "terminal-receipt.json").read_text(encoding="utf-8")
    )
    assert [stage["name"] for stage in receipt["stages"]] == [
        "freeze_inputs",
        "reviewer_rollout_and_evaluation",
        "candidate_proposal",
        "strict_selection_gate",
        "final_evaluation",
    ]
    assert receipt["status"] == "complete"
    assert receipt["gate"]["accepted"] is True

    for task_path in (run_root / "workspaces").rglob("task.json"):
        serialized = task_path.read_text(encoding="utf-8").casefold()
        assert "controller-only" not in serialized
        assert "reference_path" not in serialized


def test_pipeline_refuses_to_write_run_artifacts_inside_checkout(tmp_path: Path) -> None:
    checkout_root = tmp_path / "checkout"
    checkout_root.mkdir()
    inside = checkout_root / "runs" / "attempt"

    from code_review_skill_evolution.pipeline import PipelineConfig

    try:
        PipelineConfig(
            run_id="bad-run",
            run_root=inside,
            checkout_root=checkout_root,
            initial_skill="# Skill\n",
            train_tasks=(),
            selection_tasks=(),
            final_tasks=(),
        )
    except ValueError as exc:
        assert "outside the Git checkout" in str(exc)
    else:
        raise AssertionError("PipelineConfig accepted an in-checkout run_root")


def test_demo_rejects_checkout_output_before_creating_inputs(tmp_path: Path) -> None:
    checkout_root = tmp_path / "checkout"
    checkout_root.mkdir()
    blocked = checkout_root / "blocked" / "run"

    try:
        run_demo(checkout_root, blocked)
    except ValueError as exc:
        assert "outside the Git checkout" in str(exc)
    else:
        raise AssertionError("run_demo accepted an in-checkout run_root")
    assert not (checkout_root / "blocked").exists()


def test_demo_can_run_twice_under_one_external_parent(tmp_path: Path) -> None:
    checkout_root = tmp_path / "checkout"
    checkout_root.mkdir()
    assert run_demo(checkout_root, tmp_path / "run-one")["status"] == "complete"
    assert run_demo(checkout_root, tmp_path / "run-two")["status"] == "complete"
