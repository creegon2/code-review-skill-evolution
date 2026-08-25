# Architecture and trust boundaries

## Purpose

The project is a small orchestration companion, not a benchmark bundle,
leaderboard submission, hosted service, model, or replacement for SkillOpt.
Its job is to make the boundaries between task execution, evaluation, Skill
proposal, selection, and audit explicit and testable.

## Components

~~~text
                         operator-owned external inputs
                                      |
                                      v
                              Pipeline Controller
                         /          |           \
                        v           v            v
             isolated Reviewer   Evaluator    Optimizer
                 workspace       private       bounded
                 public only     reference     summaries
                        \           |            /
                         \          v           /
                          +---- strict gate ----+
                                      |
                                      v
                         external receipts/artifacts
                                      |
                                      v
                         optional read-only sidecar
~~~

- Pipeline Controller freezes identities, creates fresh workspaces, calls each
  role in order, applies the gate, and writes a terminal receipt.
- Reviewer Backend receives one workspace, current Skill, attempt identity,
  and public task payload.
- Evaluator Backend receives the completed finding batch and the full
  controller-owned TaskPackage, including the private reference.
- Optimizer Backend receives the current Skill and bounded AttemptSummary
  objects. It does not receive TaskPackage objects, references, or raw traces.
- Selection gate is a deterministic lexicographic comparison of aggregate
  primary and secondary scores.
- Optional sidecar may mirror completed, hashed provenance after a stage
  finishes. It is not part of the learning decision.

## Core contracts

TaskPackage separates four inputs:

1. snapshot directory;
2. review diff;
3. public task metadata;
4. controller-only private reference.

The constructor rejects a private reference stored inside the snapshot,
because copying the snapshot would otherwise leak it to the Reviewer.
Snapshot symlinks are rejected during hashing so an apparently local snapshot
cannot silently include bytes outside the declared tree.

FindingBatch uses a fixed six-field finding shape: file, start line, end line,
severity, summary, and description. Score contains a primary and secondary
number between zero and one plus JSON details.

AttemptSummary is the only trajectory object given to the Optimizer. It
contains task identity, split, Skill hash, finding count, score, and a bounded
failure string. It contains no raw model conversation or reference material.

## Authority

- The Reviewer owns findings, not their correctness.
- The Evaluator owns measurements, not Skill edits.
- The Optimizer owns candidate proposals, not promotion.
- The strict gate owns candidate acceptance for this reference pipeline.
- The Controller owns run state and receipts, not task answers.
- A sidecar owns only its detached provenance copy.

A formal SkillOpt integration should leave Trainer, reflection, merge,
current/best state, and the official gate with the pinned upstream runtime.
The public SkillOpt boundary wraps an operator-supplied call; it does not copy
those algorithms.

## Isolation model

Each attempt gets a new directory. The framework copies only:

- snapshot;
- review diff;
- current Skill;
- public task JSON.

The private reference stays at its operator-owned path and reaches only the
Evaluator. Train, selection, and final task IDs must be disjoint. The run root
must be outside the Git checkout. A reused non-empty run root is rejected
instead of being merged with old artifacts.

## Failure and recovery

The terminal receipt records either complete or failed. A failed stage does
not get repaired in place. Change configuration, code, model, data, or scorer
only at a new run boundary and use a new run root. Do not splice unrelated
outputs or infer missing artifacts from an incomplete directory.

## Extension points

Implement the three protocols in backends.py:

- ReviewerBackend;
- EvaluatorBackend;
- OptimizerBackend.

Custom gate policies may be introduced only as explicit, versioned code and
must have focused tests. Optional stores and report formatters should consume
completed receipts without becoming a second Trainer.
