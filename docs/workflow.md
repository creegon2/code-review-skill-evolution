# Workflow and state transitions

## State topology

~~~text
prepared
  -> inputs_frozen
  -> train_reviewer_completed
  -> train_evaluated
  -> candidate_proposed
  -> incumbent_selection_completed
  -> candidate_selection_completed
  -> gate_decided
  -> final_evaluated
  -> terminal
~~~

After the external run root has been validated and created, any subsequent
exception writes a failed terminal receipt and stops the run. Invalid output
locations are rejected before a receipt is created. The framework does not
fill missing fields or continue from a different run.

## 1. Freeze inputs

The Controller hashes the initial Skill, each diff, each snapshot tree, and
each private reference. The manifest records hashes and public metadata, not
machine paths. Split identities are frozen before a Reviewer runs.

## 2. Run the training Reviewer

For each train task, the Controller creates a fresh allowlisted workspace and
passes it to ReviewerBackend. The Reviewer returns a FindingBatch. The raw
private reference is never copied into that workspace.

## 3. Evaluate after rollout

EvaluatorBackend runs only after the finding batch is finalized. It can read
the controller-owned private reference and returns a Score. Determinism is a
formal-run requirement for the operator-supplied scorer, not something the
injection protocol can prove by itself. Findings and score are written under
the external run root.

## 4. Propose one candidate

The Optimizer receives bounded AttemptSummary values. In a formal SkillOpt
deployment, the pinned official runtime should perform reflection and
candidate construction. The offline smoke uses a deterministic fake solely to
exercise the handoff.

## 5. Rerun selection

Incumbent and candidate Skills each receive fresh attempts on the same frozen
selection set. Neither run reuses the training workspace. Their scores are
aggregated independently.

## 6. Apply the strict gate

The candidate is accepted only if:

1. its aggregate primary score is higher; or
2. primary scores tie and its aggregate secondary score is higher.

Equal or lower results are rejected. Manual promotion is outside the
reference workflow.

## 7. Final evaluation

Only the accepted Skill runs on the disjoint final set. The final score is
measurement evidence for the exact supplied data, models, scorer, and
configuration. It is not automatically evidence of generalization.

## 8. Write the terminal receipt

The receipt includes the manifest hash, ordered stage status, gate inputs and
decision, accepted Skill hash, and final aggregate score. It intentionally
does not claim that the framework or Skill is universally effective.

## Recovery rule

Configuration and implementation changes happen between runs. Start a new
run identity and directory after a failure or design change. Never manually
patch an active run's trace, candidate, score, or receipt.
