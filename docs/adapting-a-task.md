# Adapting another task

[中文](adapting-a-task.zh-CN.md)

The framework ships with one synthetic demo task. To run it on your own
code-review material, you define the task boundary and implement the three
backend interfaces. This guide walks through each step.

## 1. Define the task boundary

Decide, for your task format, which of the four `TaskPackage` slots each
piece of material goes into:

- **snapshot** — the code tree the Reviewer may read (a directory);
- **diff** — the change under review;
- **metadata** — anything else the Reviewer is allowed to know (repository
  name, change description, …);
- **private_reference** — the answer key, stored *outside* the snapshot
  directory.

The split is the whole game: everything in the first three slots reaches the
Reviewer, and only the fourth reaches the Evaluator. If you are unsure which
side something belongs on, ask "would a human reviewer get this?" — if not,
it is reference material.

`TaskPackage` enforces the obvious mistakes at construction time (answer key
inside the snapshot, metadata keys that look like labels — `gold`,
`expected`, `oracle`, and similar are rejected by name), but it cannot know
your data. Keep real task material out of this repository entirely; only the
adapter code belongs here.

## 2. Implement `ReviewerBackend`

One method: `review(request) -> FindingBatch`. The request carries a fresh
workspace path, the public task payload, the current Skill text, and an
attempt ID.

For a model-backed implementation, the recurring theme is *fresh and pinned*:

- pin the backend and model identity, so runs are comparable;
- start every attempt with a fresh conversation — a reused conversation
  carries knowledge between attempts, which quietly breaks the comparison
  between incumbent and candidate;
- set an execution timeout, and disable network access, tools, and shared
  state you have not explicitly approved;
- if you keep raw model traces, keep them under the external run root,
  subject to your own data policy.

## 3. Implement `EvaluatorBackend`

One method: `score(task, findings) -> Score`. It runs only after the Reviewer
has finished, and it is the only backend allowed to read
`task.private_reference`.

Prefer a deterministic scorer — the gate compares two Skills by their scores,
and scorer randomness shows up as phantom differences between them. Record
"the scorer could not decide" differently from "the Reviewer found nothing";
collapsing ambiguity into a confident 0 or 1 poisons the very signal the
Optimizer learns from.

## 4. Implement `OptimizerBackend`

One method: `propose(request) -> str`, returning one non-empty candidate
Skill. The request contains the current Skill and the bounded per-attempt
summaries, and that is all the Optimizer will ever get — no answer keys, no
transcripts.

To use official SkillOpt, wrap your pinned checkout's proposal call in
`SkillOptProposalBoundary` (see
[Formal integrations](formal-integrations.md)). Leave SkillOpt's own
training loop, reflection, and state where they are; the boundary only
carries the request across.

Resist adding side channels. A report generator or audit store that starts
nudging which candidate gets proposed or accepted is a second, invisible
optimizer, and results stop being attributable to the one you configured.

## 5. Test with fakes before spending money

Before connecting a real model, clone what `demo.py` does for your task
format: generate a tiny synthetic task in a temporary directory, drive the
pipeline with fake backends, and assert the properties that matter —

- the answer key's bytes and path never appear in the Reviewer's workspace;
- every attempt gets its own workspace;
- incumbent and candidate both rerun on the selection set;
- an equal score is rejected, a strictly better one is accepted;
- the final stage runs the accepted Skill;
- the terminal receipt is complete and schema-valid;
- nothing is written inside the Git checkout.

These tests are cheap, deterministic, and catch exactly the class of leakage
bug that is expensive to discover after a paid run.

## 6. Pre-flight checklist for a real run

- Real tasks and answer keys live outside Git.
- Train, selection, and final task IDs are frozen and disjoint.
- Model, scorer, SkillOpt revision, prompt, and configuration are pinned.
- You have audited what the Reviewer can actually see in its workspace.
- The run root is external and empty.
- Network, concurrency, timeout, and cost policies are explicit.
- Nobody will "quickly fix" a stage inside a running run — changes wait for
  the next run.
- Publication review covers generated archives as well as Git files.
