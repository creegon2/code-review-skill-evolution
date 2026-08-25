# Adapting another task

[中文](adapting-a-task.zh-CN.md)

## 1. Define the task boundary

Identify the task's public inputs, controller-only labels, output schema, and
measurement objective. Keep all real task material outside this repository.

Construct TaskPackage with:

- a unique task ID;
- an immutable snapshot directory;
- a review diff;
- a private evaluator reference outside the snapshot;
- metadata safe for the Reviewer.

Do not place gold, oracle, answer, expected, or reference fields in public
metadata.

## 2. Implement ReviewerBackend

The backend receives ReviewerRequest containing a fresh workspace, public task
payload, current Skill, and attempt ID. It must return FindingBatch.

For a model-backed implementation:

- pin backend and model identity;
- enforce an execution timeout;
- disable unapproved network, tools, plugins, and shared state;
- do not reuse a conversation between attempts;
- retain raw traces only under the external run root and according to the
  operator's data policy.

## 3. Implement EvaluatorBackend

The evaluator receives the full TaskPackage only after the Reviewer completes.
Use a deterministic scorer when possible. Record ambiguity and evaluator
failure separately from Reviewer failure. A missing match should not be
silently reinterpreted as a confirmed bug or non-bug.

## 4. Implement OptimizerBackend

The optimizer receives OptimizationRequest with current Skill and bounded
trajectory summaries. It must return one non-empty candidate Skill.

For formal SkillOpt use, bind this boundary to a pinned official checkout and
leave its Trainer, reflection, merge, current/best state, and gate semantics
intact. Do not create a second hidden promotion path in a sidecar or report
generator.

## 5. Add no-model tests

Generate a tiny synthetic task under a test temporary directory. Use fake
Reviewer, Evaluator, and Optimizer backends. Verify:

- private reference bytes and paths do not reach Reviewer task JSON;
- every attempt gets a new workspace;
- incumbent and candidate both rerun on selection;
- equal scores reject the candidate;
- a strict improvement accepts it;
- final evaluation consumes the accepted Skill;
- the terminal receipt is complete and schema-valid;
- formal artifacts are not written into the Git checkout.

Synthetic fixtures test contracts only. They are not benchmark evidence.

## 6. Formal-run checklist

- Real inputs and references are stored outside Git.
- Train, selection, and final identities are frozen and disjoint.
- Model, scorer, SkillOpt, prompt, and configuration identities are pinned.
- Reviewer visibility was audited.
- Every attempt uses isolated workspace and state.
- Run root is external and empty.
- Network, approval, concurrency, timeout, and cost policies are explicit.
- No stage will be repaired or reconfigured inside the run.
- Publication review covers both Git files and generated source archives.
