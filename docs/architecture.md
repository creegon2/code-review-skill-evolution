# Architecture and trust boundaries

[中文](architecture.zh-CN.md)

## Why so many walls

The pipeline improves the very document that steers the Reviewer, so it is a
self-improving loop — and self-improving loops fail in predictable ways:

1. **Answer leakage.** The answer key ends up somewhere the Reviewer (or the
   Optimizer) can read it, and scores become meaningless.
2. **Self-grading.** The component that proposes an improvement also judges
   whether the improvement worked.
3. **Retroactive tampering.** Inputs or outputs get quietly edited after the
   fact, so nobody can tell what actually ran.

Every boundary in this design blocks one of those three failure modes. If a
rule below seems fussy, it is usually guarding against leakage you would not
notice until the results were already wrong.

## The cast

| Term | Meaning |
|---|---|
| **Skill** | A markdown playbook that steers the Reviewer. The thing being evolved. |
| **Reviewer** | Reviews code and reports findings. In real use, a model; in the demo, a fake. |
| **Evaluator** | Judges findings against the private answer key and returns a score. |
| **Optimizer** | Proposes a new candidate Skill from score summaries. |
| **Controller / pipeline** | The orchestrator: freezes inputs, runs stages in order, writes the receipt. |
| **Gate** | The mechanical rule deciding whether the candidate replaces the incumbent. |
| **Attempt** | One Reviewer pass over one task, in its own fresh workspace. |
| **Split** | Which of the three disjoint task sets a task belongs to: train, selection, or final. |
| **Incumbent / candidate** | The current Skill vs. the newly proposed one. |
| **Receipt** | The JSON record a run leaves behind: input hashes, stage results, gate decision, final score. |
| **Sidecar** | An optional read-only mirror of finished artifacts for auditing. |

## How the pieces connect

~~~text
        operator-supplied inputs (tasks, answer keys, initial Skill)
                              |
                              v
                      Pipeline Controller
          /                   |                    \
         v                    v                     v
     Reviewer             Evaluator             Optimizer
  sees: snapshot,      sees: findings +      sees: score summaries
  diff, Skill,         private answer key    only
  public metadata
         \                    |                    /
          \                   v                   /
           +----------- strict gate -------------+
                              |
                              v
              receipts and artifacts (outside Git)
                              |
                              v
               optional read-only audit sidecar
~~~

Reviewer, Evaluator, and Optimizer are `Protocol` interfaces in
`backends.py` — the pipeline never cares what implements them. A formal
deployment binds the Optimizer to official
[Microsoft SkillOpt](https://github.com/microsoft/SkillOpt), the Evaluator to
a deterministic scorer, and the Reviewer to a real model backend.

## The contracts

The data shapes in `contracts.py` are where the isolation rules are actually
enforced — mostly in constructors, so an invalid object cannot exist at all.

**TaskPackage** bundles one task's four inputs: a code snapshot directory, a
review diff, public metadata, and the private answer key (the
`private_reference`). Two of its validation rules are worth explaining:

- *The answer key must live outside the snapshot directory.* The Reviewer's
  workspace is created by copying the snapshot, so an answer key stored
  inside the snapshot would be copied straight to the Reviewer.
- *Snapshot symlinks are rejected.* A symlink could point anywhere on the
  machine, letting an innocent-looking snapshot silently pull in files that
  were never declared — including the answer key.

Public metadata is also screened by key name: keys containing fragments like
`answer`, `gold`, `label`, `oracle`, `reference`, or `secret` are rejected,
because those fields belong to the Evaluator, not in material the Reviewer
can read.

**Finding / FindingBatch** is the Reviewer's output: each finding has a file,
start/end line, severity (`Critical`/`Major`/`Minor`/`Trivial`/`Info`),
summary, and description. File paths must be relative and stay inside the
snapshot.

**Score** is the Evaluator's output: a primary and a secondary number, each
between 0 and 1, plus free-form JSON details. The details stay with the
controller and are never forwarded to the Optimizer.

**AttemptSummary** is the *only* thing the Optimizer ever sees about an
attempt: task ID, split, Skill hash, finding count, the two score numbers,
and at most an opaque failure code. No answer key, no model conversation, no
file paths. This is deliberate: the Optimizer's job is to improve the Skill
from outcomes, and anything richer would reopen the leakage hole.

## Who owns what

Each role owns exactly one kind of decision, so no role can grade its own
work:

- The Reviewer owns its findings — not whether they are correct.
- The Evaluator owns the measurements — not the Skill.
- The Optimizer owns the proposal — not whether it is adopted.
- The gate owns adoption — by a fixed mechanical rule, not judgment.
- The controller owns run state and receipts — not task answers.
- A sidecar owns only its detached copy.

When official SkillOpt is plugged in, its own Trainer, reflection, merge, and
gate logic stay in the pinned upstream checkout. The boundary class here
(`integrations/skillopt.py`) only passes the current Skill and the bounded
summaries across; it does not reimplement any of the algorithm.

## Isolation at runtime

- Every attempt gets a brand-new workspace directory containing exactly four
  things: the snapshot copy, the review diff, the current Skill, and the
  public task JSON. Nothing is reused between attempts, so one attempt can
  never see another's state.
- The answer key never moves. It stays at its operator-owned path and is
  opened only by the Evaluator, after the Reviewer has finished.
- Train, selection, and final task IDs must be disjoint. The final set exists
  to measure the accepted Skill on tasks it has never influenced; any overlap
  would turn the final score into a training score.
- The run root must be outside the Git checkout and must start empty. This
  keeps generated artifacts out of version control and prevents two runs from
  silently mixing their outputs.

## When a run fails

A run ends in exactly one of two receipts: `complete` or `failed`. A failed
stage is not patched in place — fix the configuration, code, or data, then
start a *new* run with a new run root. Splicing outputs from different runs,
or hand-editing an existing run directory, destroys the property the receipt
exists to provide: that everything in the directory came from the recorded
inputs.

## Extending the framework

Implement the three protocols in `backends.py`: `ReviewerBackend`,
`EvaluatorBackend`, `OptimizerBackend`. See
[Adapting another task](adapting-a-task.md) for a walkthrough.

If you need a different acceptance rule, write it as explicit, versioned,
tested code next to `gate.py` — not as a manual override. Report generators
and audit stores should consume finished receipts; the moment one of them
starts influencing which Skill wins, it has become a second, hidden
optimizer.
