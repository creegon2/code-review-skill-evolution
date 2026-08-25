# Code Review Skill Evolution

[中文说明](README.zh-CN.md)

A framework that improves an AI code reviewer's playbook automatically: run
review tasks, score the results against a hidden answer key, propose a better
playbook, and adopt the new version only if it measurably wins.

## The idea in one minute

When an AI reviews code, its behavior is steered by a **Skill** — a markdown
document of instructions like *"check every changed early-return path for
resource cleanup"*. Normally people tune that document by hand. This framework
turns the tuning into a loop:

1. **Review.** The AI (the *Reviewer*) works through a set of training tasks
   using the current Skill and reports findings — file, line range, severity,
   summary.
2. **Score.** A judge (the *Evaluator*) compares those findings against a
   private answer key the Reviewer never sees, and produces a score.
3. **Propose.** An *Optimizer* looks at the score summaries and proposes an
   improved candidate Skill.
4. **Compete.** The old Skill (*incumbent*) and the new one (*candidate*) both
   run on a fresh set of selection tasks. The candidate is adopted only if it
   strictly beats the incumbent.
5. **Measure.** The winner runs once on a held-out final task set, and the
   whole run is recorded in a receipt file.

A self-improving loop like this is easy to rig by accident: the answer key
leaks into the Reviewer's workspace, the Optimizer peeks at the answers, or
the final measurement reuses tasks the Skill was trained on. Most of the code
in this repository exists to make that kind of cheating structurally
impossible — every role sees only what it is supposed to see, and the tests
verify it. [Architecture](docs/architecture.md) walks through the specific
boundaries.

## What's in the box — and what isn't

This repository contains the orchestration framework only: the pipeline, the
data contracts between roles, the isolation rules, tests, and documentation.

It contains **no benchmark data, no model access, and no experiment
results**. To run a real experiment you bring your own review tasks, model
backend, scorer, and — if you want the full Skill-optimization algorithm — a
pinned checkout of [Microsoft SkillOpt](https://github.com/microsoft/SkillOpt).
[Formal integrations](docs/formal-integrations.md) explains how each of those
plugs in.

## Quick start (no model, no network)

The built-in demo runs the entire loop with a synthetic one-bug task and fake
Reviewer/Evaluator/Optimizer backends. It proves the wiring and the isolation
rules work; it says nothing about real review quality.

Requires Python 3.10+:

~~~bash
python -m venv .venv
# Activate .venv with the command for your shell, then:
python -m pip install -e ".[dev]"
python -m pytest
python -m code_review_skill_evolution
~~~

By default everything happens in a temporary directory that is cleaned up
afterwards. To keep the outputs, point `--run-root` at a directory **outside**
this repository (the runner refuses to write inside the Git checkout, so that
generated artifacts can never end up in a commit):

~~~bash
python -m code_review_skill_evolution --run-root /absolute/external/run
~~~

## Who does what

| Role | What it does | What it deliberately cannot do |
|---|---|---|
| Reviewer | Reviews one task in a fresh workspace, returns findings | See the answer key, other attempts, or final-set labels |
| Evaluator | Scores finished findings against the private answer key | Edit the Skill or the Reviewer's output |
| Optimizer | Proposes a candidate Skill from score summaries | See the answer key or raw model conversations |
| Gate | Compares incumbent vs. candidate scores, purely mechanically | Accept a candidate on anyone's gut feeling |
| Pipeline (controller) | Freezes inputs, runs the stages in order, writes the receipt | Patch up outputs or change configuration mid-run |
| Audit sidecar (optional) | Mirrors completed, hashed artifacts to an external store | Feed anything back into the loop |

Reviewer, Evaluator, and Optimizer are injected interfaces (see
`backends.py`), so any of them can be backed by a real model, a deterministic
scorer, or official SkillOpt.

## Where the data lives

Two rules cover most of the data-handling design:

- **The answer key stays with the judge.** A Reviewer workspace is built from
  an allowlist — code snapshot, review diff, current Skill, public metadata —
  and nothing else. The private reference must live *outside* the snapshot
  directory, because the workspace is a copy of the snapshot: anything inside
  would be handed straight to the Reviewer.
- **Run outputs stay out of Git.** Every run writes to an external directory,
  never into the checkout. Before publishing changes, run the release guard
  to double-check nothing private slipped in:

~~~bash
python scripts/public_release_check.py --all-files
python -m build
python scripts/public_release_check.py --archives
~~~

## Repository layout

~~~text
src/code_review_skill_evolution/   the framework (no third-party dependencies)
  contracts.py                     data shapes passed between roles
  pipeline.py                      the evolution loop itself
  gate.py                          strict candidate-vs-incumbent comparison
  isolation.py                     builds allowlisted Reviewer workspaces
  demo.py                          the synthetic offline demo
  integrations/skillopt.py         thin boundary for official SkillOpt
tests/unit/                        contract, gate, and isolation tests
tests/integration/                 end-to-end synthetic run
examples/                          runnable offline example
docs/                              architecture, workflow, adapter guide
scripts/                           public-release guard
~~~

## Documentation

- [Architecture and trust boundaries](docs/architecture.md) — the roles, the
  contracts, and why each wall exists
- [Workflow](docs/workflow.md) — one run, stage by stage
- [Adapting another task](docs/adapting-a-task.md) — plugging in your own
  review format
- [Formal integrations](docs/formal-integrations.md) — connecting a real
  model, scorer, SkillOpt checkout, or audit store
- [Design sources](docs/design-sources.md) — where the repository structure
  comes from

## Status and license

Version 0.1.0 is a reference implementation: the offline paths are meant to
be reproducible, and no real benchmark results are included. Original code is
released under the [MIT License](LICENSE); external integrations keep their
own licenses.
