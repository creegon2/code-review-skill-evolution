from __future__ import annotations

import json
from pathlib import Path

from code_review_skill_evolution.contracts import TaskPackage
from code_review_skill_evolution.isolation import prepare_reviewer_workspace


def test_workspace_is_built_from_public_allowlist(tmp_path: Path) -> None:
    snapshot = tmp_path / "input" / "snapshot"
    snapshot.mkdir(parents=True)
    (snapshot / "main.py").write_text("value = 1\n", encoding="utf-8")
    diff = tmp_path / "input" / "review.diff"
    diff.write_text("+value = 1\n", encoding="utf-8")
    reference = tmp_path / "controller-only" / "reference.json"
    reference.parent.mkdir()
    reference.write_text('{"secret_marker":"never-copy"}\n', encoding="utf-8")
    task = TaskPackage("isolated-task", snapshot, diff, reference)

    workspace = prepare_reviewer_workspace(
        tmp_path / "workspaces",
        "attempt-1",
        task,
        "# Skill\n",
    )

    assert (workspace / "snapshot" / "main.py").is_file()
    assert (workspace / "review.diff").is_file()
    assert (workspace / "SKILL.md").is_file()
    task_json = (workspace / "task.json").read_text(encoding="utf-8")
    assert "secret_marker" not in task_json
    assert "reference.json" not in task_json
    assert not any(path.name == "reference.json" for path in workspace.rglob("*"))
    assert json.loads(task_json)["task_id"] == "isolated-task"
