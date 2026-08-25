"""Build a fresh Reviewer workspace from an explicit public allowlist."""

from __future__ import annotations

import json
from pathlib import Path
import shutil

from .contracts import TaskPackage, validate_id


def _write_json(path: Path, value: object) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(path)


def prepare_reviewer_workspace(
    root: str | Path,
    attempt_id: str,
    task: TaskPackage,
    skill: str,
) -> Path:
    """Copy only snapshot, diff, public metadata, and the current Skill."""

    safe_attempt = validate_id(attempt_id, "attempt_id")
    # Validate and hash the declared snapshot before copying any bytes. This
    # rejects a symlink escape without leaving leaked content in a workspace.
    public_payload = task.public_payload()
    workspace = Path(root).resolve() / safe_attempt
    if workspace.exists():
        raise FileExistsError(f"Reviewer workspace already exists: {workspace}")
    workspace.mkdir(parents=True)
    shutil.copytree(task.snapshot, workspace / "snapshot")
    shutil.copy2(task.diff, workspace / "review.diff")
    (workspace / "SKILL.md").write_text(skill, encoding="utf-8", newline="\n")
    _write_json(workspace / "task.json", public_payload)
    return workspace


__all__ = ["prepare_reviewer_workspace"]
