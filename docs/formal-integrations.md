# Formal integrations

[中文](formal-integrations.zh-CN.md)

The dependency-free core is intentionally smaller than a formal experiment
environment. Real operation needs explicit external integrations.

## SkillOpt

Use the official [Microsoft SkillOpt repository](https://github.com/microsoft/SkillOpt).
The public boundary was validated against base commit
`3c8873f016397817dcd40c3e5436d92fe19372b8`. Pin a reviewed revision for each
formal run.

The module integrations/skillopt.py exposes SkillOptProposalBoundary for an
operator-owned callable. It passes only the current Skill and bounded
trajectory summaries. It does not vendor or reimplement SkillOpt Trainer,
reflection, merge, or gate behavior.

A production adapter should be tested against the exact selected upstream
revision. A matching version number alone is not sufficient evidence of
identical code.

## Code-review scorer

The earlier private environment used an adapter boundary around
[Alibaba AACR-Bench](https://github.com/alibaba/aacr-bench) at commit
`b3072489eace26efca8bcf2b1ac6a24ba64f82c1`. Neither its code nor its data is
included here.

Operators may implement EvaluatorBackend using that pinned scorer or another
task-specific deterministic evaluator. Keep reference labels available only
to the Controller/Evaluator and distinguish adapter-derived measurements from
official leaderboard metrics.

## Reviewer model

ReviewerBackend is deliberately provider-neutral. A model-backed
implementation must explicitly configure model identity, reasoning settings,
sandbox, network, tools, credentials, concurrency, timeout, and retention.
Each attempt must begin with fresh context and must not read another attempt,
selection labels, final labels, or private references.

## Optional audit store

The core writes JSON receipts and does not require HeavenBase. An operator may
add a detached HeavenBase or other audit-store sidecar that reads only
completed artifacts, verifies hashes, and stores compact provenance.

The sidecar must not:

- alter current or best Skill;
- change a score or gate decision;
- feed hidden reference material into training;
- make an incomplete official artifact appear complete;
- write into a shared state tree used by another run.

No private HeavenBase wheel, local-path dependency, database, or source
checkout is included in this repository.

## Data locations

Keep all of the following outside Git:

- task snapshots and review diffs;
- train, selection, held-out, or final labels;
- model prompts, responses, conversations, and raw traces;
- trajectory packages and candidate outputs;
- scores, reports, receipts, and run databases;
- model credentials and isolated backend state.

The public release guard is an additional check, not a substitute for an
operator review of Git history and generated archives.
