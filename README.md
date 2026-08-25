# Code Review Skill Evolution

[中文说明](README.zh-CN.md)

A data-free reference framework for connecting code-review tasks to an
auditable Skill learning and selection loop.

This repository publishes orchestration code, role boundaries, contracts,
tests, and process documentation. It intentionally does **not** publish
benchmark tasks, source snapshots, diffs from real projects, private labels,
model conversations, trajectories, scores, run receipts, databases, or
credentials.

## What this repository is

The framework makes one small but complete topology executable:

~~~text
operator-owned external inputs
  -> freeze identities
  -> isolated Reviewer rollout
  -> controller-only evaluation (deterministic for formal runs)
  -> bounded trajectory summary
  -> candidate Skill proposal
  -> incumbent and candidate rerun on selection tasks
  -> strict mechanical gate
  -> final evaluation
  -> terminal receipt in an external run directory
~~~

The default quick start uses a synthetic task and fake backends. It verifies
the wiring and isolation rules without a model, account, network request,
benchmark checkout, or audit database. It is not an experiment result.

## Role boundaries

| Role | Responsibility | Must not do |
|---|---|---|
| Reviewer | Inspect one fresh task workspace and return schema-valid findings | Read private references, other attempts, or final-test labels |
| Evaluator | Compare completed findings with controller-only references | Modify the Skill or Reviewer output |
| Optimizer | Propose a candidate from bounded trajectory summaries | Read raw references or become a second evaluator |
| Selection gate | Compare incumbent and candidate scores mechanically | Promote a candidate by manual preference |
| Runner | Freeze inputs, connect stages, and write receipts | Repair outputs or change configuration inside a run |
| Optional audit sidecar | Mirror completed provenance to an external store | Feed scores or parent decisions back into training |

The public core treats Reviewer, Evaluator, and Optimizer as injected
interfaces. A formal deployment can bind the optimizer to official
[Microsoft SkillOpt](https://github.com/microsoft/SkillOpt), bind the evaluator
to an operator-owned deterministic scorer, and bind the Reviewer to an
approved model backend.

## Quick start: offline framework smoke

Python 3.10 or newer is required. Create and activate a virtual environment,
then run:

~~~bash
python -m venv .venv
# Activate .venv with the command for your shell, then:
python -m pip install -e ".[dev]"
python -m pytest
python -m code_review_skill_evolution
~~~

The smoke creates all inputs and outputs under a temporary directory and then
removes them. To retain synthetic artifacts outside the checkout:

~~~bash
python -m code_review_skill_evolution --run-root /absolute/external/run
~~~

The runner rejects an output directory inside the Git checkout.

## Formal operation requires external inputs

| Category | Operator-provided input |
|---|---|
| Task material | Snapshots, diffs, task metadata, and private evaluator references |
| Skill engine | A pinned official SkillOpt checkout or another explicit Optimizer backend |
| Reviewer | Provider/backend, model identity, credentials, quota, timeout, and sandbox policy |
| Evaluator | Deterministic task-specific scorer and any separately controlled Judge |
| Frozen identity | Initial Skill, task manifest, split manifest, configuration, and hashes |
| Isolation | Fresh attempt workspaces and a run root outside the source checkout |
| Audit | Optional detached store and retention policy |
| Execution policy | Network, approval, concurrency, wall-time, and cost limits |

None of these formal inputs are bundled here. See
[Formal integrations](docs/formal-integrations.md) before connecting a real
backend.

## Data and publication boundary

The Reviewer workspace is built from an allowlist: the current snapshot,
review diff, current Skill, and public task metadata. The private reference
must live outside the snapshot and is passed only to the Evaluator after the
Reviewer stops. The Optimizer receives score and finding-count summaries, not
the private reference or raw model trace.

Formal artifacts must remain in an operator-owned directory outside Git. Run
the release guard before every public change:

~~~bash
python scripts/public_release_check.py --all-files
python -m build
python scripts/public_release_check.py --archives
~~~

The synthetic smoke is test evidence for framework wiring only. It does not
show that a Skill improves on a real code-review benchmark, another model, or
unseen data.

## Repository layout

~~~text
src/code_review_skill_evolution/   dependency-free orchestration core
tests/unit/                        deterministic contract tests
tests/integration/                 synthetic end-to-end smoke
examples/                          runnable offline example
docs/                              architecture, workflow, and adapter guide
scripts/                           public-release guard
.github/                           CI and contribution templates
~~~

This layout follows the common public Python project pattern used by actively
maintained agent and evaluation repositories while keeping this companion
small. The design-source notes are in
[docs/design-sources.md](docs/design-sources.md).

## Documentation

- [Architecture and trust boundaries](docs/architecture.md)
- [Workflow and state transitions](docs/workflow.md)
- [Adapting another task](docs/adapting-a-task.md)
- [Formal integrations](docs/formal-integrations.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

## Project status

Version 0.1.0 is a reference implementation and POC infrastructure. The
offline unit and end-to-end paths are intended to be reproducible. No real
benchmark outcome or generalization claim is included.

## License

Original code in this repository is released under the [MIT License](LICENSE).
External integrations retain their own licenses.
