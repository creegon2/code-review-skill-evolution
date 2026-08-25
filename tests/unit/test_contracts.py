from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from code_review_skill_evolution.contracts import (
    AttemptSummary,
    Finding,
    Score,
    TaskPackage,
)
from code_review_skill_evolution.hashing import sha256_text


def make_task(tmp_path: Path) -> TaskPackage:
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    (snapshot / "app.py").write_text("print('ok')\n", encoding="utf-8")
    diff = tmp_path / "change.diff"
    diff.write_text("+print('ok')\n", encoding="utf-8")
    reference = tmp_path / "controller" / "expected.json"
    reference.parent.mkdir()
    reference.write_text(json.dumps({"expected": []}), encoding="utf-8")
    return TaskPackage("task-1", snapshot, diff, reference, {"repository": "fixture"})


def test_task_public_payload_excludes_reference(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    payload = task.public_payload()
    serialized = json.dumps(payload).casefold()
    assert "private_reference" not in serialized
    assert "expected.json" not in serialized
    assert payload["task_id"] == "task-1"


def test_reference_must_not_live_inside_snapshot(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    diff = tmp_path / "change.diff"
    diff.write_text("diff\n", encoding="utf-8")
    reference = snapshot / "expected.json"
    reference.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="outside"):
        TaskPackage("task-1", snapshot, diff, reference)


def test_nested_controller_metadata_is_rejected(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    with pytest.raises(ValueError, match="controller-only"):
        TaskPackage(
            "task-2",
            task.snapshot,
            task.diff,
            task.private_reference,
            {"nested": {"oracle": "SECRET"}},
        )
    with pytest.raises(TypeError, match="JSON-safe"):
        TaskPackage(
            "task-3",
            task.snapshot,
            task.diff,
            task.private_reference,
            {"bad": object()},
        )


def test_diff_symlink_is_rejected_before_workspace_copy(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    linked_diff = tmp_path / "linked.diff"
    try:
        os.symlink(task.private_reference, linked_diff)
    except OSError:
        pytest.skip("symlink creation is not available in this environment")
    with pytest.raises(ValueError, match="diff may not be a symlink"):
        TaskPackage(
            "task-linked-diff",
            task.snapshot,
            linked_diff,
            task.private_reference,
        )


def test_contracts_reject_invalid_values() -> None:
    with pytest.raises(ValueError):
        Finding("../escape.py", 1, 1, "Major", "summary", "description")
    with pytest.raises(ValueError):
        Finding("app.py", 5, 2, "Major", "summary", "description")
    with pytest.raises(ValueError):
        Score(1.1, 0.0)


def test_optimizer_summary_excludes_evaluator_details() -> None:
    attempt = AttemptSummary(
        task_id="task-1",
        split="train",
        skill_sha256=sha256_text("# Skill\n"),
        finding_count=1,
        score=Score(
            0.5,
            0.25,
            details={"reference_path": "controller-only", "raw_trace": "private"},
        ),
    )
    serialized = json.dumps(attempt.optimizer_payload()).casefold()
    assert "reference_path" not in serialized
    assert "raw_trace" not in serialized
    assert "controller-only" not in serialized

    with pytest.raises(ValueError, match="opaque code"):
        AttemptSummary(
            task_id="task-1",
            split="train",
            skill_sha256=sha256_text("# Skill\n"),
            finding_count=0,
            score=Score(0.0),
            failure="failed at controller-only/reference.json",
        )
