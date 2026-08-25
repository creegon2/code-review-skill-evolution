# Workflow: one run, stage by stage

[中文](workflow.zh-CN.md)

A run is one full turn of the evolution loop: baseline, proposal, competition,
final measurement. The stages always execute in this order, and each one
appends its result to the eventual receipt:

~~~text
freeze inputs
  -> Reviewer runs the training tasks
  -> Evaluator scores the training attempts
  -> Optimizer proposes one candidate Skill
  -> incumbent reruns on the selection tasks
  -> candidate reruns on the same selection tasks
  -> gate picks the winner
  -> winner runs the final tasks
  -> terminal receipt written
~~~

If any stage throws after the run directory exists, the pipeline writes a
`failed` receipt recording how far it got, and stops. It never skips a stage,
fills in a missing value, or resumes into a half-finished directory.

## 1. Freeze the inputs

Before anything runs, the controller hashes the initial Skill, every diff,
every snapshot tree, and every answer key, and writes the hashes into a
manifest. From here on, "which inputs did this run use?" has a precise,
checkable answer — if a file changes afterwards, its hash will no longer
match. The manifest records hashes and public metadata, not machine paths.

## 2. Run the Reviewer on the training tasks

For each training task, the controller builds a fresh workspace containing
only the allowlisted four items (snapshot copy, diff, current Skill, public
task JSON) and hands it to the Reviewer, which returns a batch of findings.
The answer key is never copied into any workspace.

## 3. Score the training attempts

Only after a finding batch is final does the Evaluator get involved. It reads
the answer key, compares, and returns a score. Ordering matters: the
Evaluator holds the answers, so it must not touch an attempt that is still in
progress. Findings and scores are written under the run root as they are
produced.

For formal runs the scorer should be deterministic — same findings, same
score — so that the incumbent-vs-candidate comparison in stage 6 reflects the
Skills, not scorer noise.

## 4. Propose one candidate

The Optimizer receives the current Skill plus one bounded summary per
training attempt (scores and finding counts — see
[AttemptSummary](architecture.md#the-contracts)) and returns exactly one
candidate Skill. In a formal deployment this is where official SkillOpt does
its reflection; the offline demo uses a deterministic fake that simply
appends a rule, which is enough to exercise the handoff.

## 5. Rerun both Skills on the selection tasks

The incumbent and the candidate each get fresh attempts on the same frozen
selection set — tasks that neither Skill trained on. Both start from clean
workspaces; nothing from the training stage is reused. Their scores are
aggregated (arithmetic mean) separately.

## 6. Apply the gate

The candidate is adopted only if it strictly wins:

1. its aggregate primary score is higher, or
2. primary scores tie and its aggregate secondary score is higher.

A tie goes to the incumbent. This is deliberately conservative: a candidate
that merely matches the incumbent has not demonstrated anything, and
accepting it would let the Skill drift on noise. There is no manual override
in this pipeline — if a human wants to promote a Skill anyway, that decision
belongs outside the framework, where it is visible as a human decision.

## 7. Final evaluation

Whichever Skill won runs once on the final task set — tasks that influenced
neither training nor selection. This is the run's headline number: a
measurement of the accepted Skill on data it has never touched, for this
specific combination of tasks, model, scorer, and configuration.

## 8. Write the terminal receipt

The receipt (`terminal-receipt.json`) records the manifest hash, each stage's
status, the gate's inputs and decision, the accepted Skill's hash, and the
final aggregate score. Anyone holding the receipt and the run directory can
verify what ran, in what order, with which inputs, and how it scored.

## Changing things between runs

Configuration, code, model, data, and scorer changes all happen at run
boundaries: finish (or abandon) the current run, change what you need, start
a new run with a new empty run root. Never edit an existing run directory —
its whole value is that it faithfully reflects one recorded configuration.
