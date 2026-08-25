# Formal integrations

[中文](formal-integrations.zh-CN.md)

The core in this repository runs with zero third-party dependencies, which is
exactly why it cannot run a real experiment by itself. This page lists the
external pieces a formal run plugs in, and the rules for each.

## SkillOpt (the Optimizer)

Use the official
[Microsoft SkillOpt repository](https://github.com/microsoft/SkillOpt). The
boundary here was validated against base commit
`3c8873f016397817dcd40c3e5436d92fe19372b8`; pin a reviewed revision for each
formal run, and test your adapter against that exact revision — a matching
version number is not proof of matching code.

`integrations/skillopt.py` provides `SkillOptProposalBoundary`, a thin
wrapper around a callable you supply from your pinned checkout. It passes in
the current Skill and the bounded attempt summaries, and expects one
candidate Skill back. It deliberately does not vendor or reimplement
SkillOpt's Trainer, reflection, merge, or gate logic — those stay upstream,
where they can be audited against the pinned commit.

## Code-review scorer (the Evaluator)

The private environment this framework was extracted from used an adapter
around [Alibaba AACR-Bench](https://github.com/alibaba/aacr-bench) at commit
`b3072489eace26efca8bcf2b1ac6a24ba64f82c1`. Neither its code nor its data is
included here.

You can implement `EvaluatorBackend` with that scorer or any deterministic
task-specific one. Two rules regardless of choice: reference labels are
readable by the controller and Evaluator only, and measurements produced
through your adapter should be labeled as such — they are not official
leaderboard numbers.

## Reviewer model

`ReviewerBackend` is provider-neutral on purpose. A model-backed
implementation must pin the model identity and reasoning settings, and
explicitly configure sandbox, network, tools, credentials, concurrency,
timeout, and trace retention. Each attempt starts from a fresh context and
must not be able to read other attempts, selection or final labels, or the
answer key — the isolation the framework enforces on disk, your backend must
also honor in the model's context.

## Optional audit store

The core writes plain JSON receipts and needs no database. If you want
longer-term provenance, add a sidecar (HeavenBase or anything else) that
reads completed artifacts, verifies hashes, and stores a compact copy.

The one design rule: the sidecar is read-only toward the loop. It must not
alter Skills or scores, feed reference material back into training, dress up
an incomplete artifact as complete, or share state with another run. An audit
trail that can influence the experiment is no longer an audit trail.

## What stays out of Git

Everything a run touches or produces lives outside the checkout: snapshots
and diffs, labels for any split, prompts and model traces, candidate Skills,
scores, receipts, run databases, and credentials.

`scripts/public_release_check.py` scans for accidents before a public
release, but it is a safety net, not the review itself — check Git history
and generated archives too.
