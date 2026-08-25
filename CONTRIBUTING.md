# Contributing

Thank you for helping improve the framework.

## Local setup

1. Create and activate a Python 3.10 or newer virtual environment.
2. Install the development extras with `python -m pip install -e ".[dev]"`.
3. Run `python -m pytest`.
4. Run `python -m code_review_skill_evolution`.
5. Run `python scripts/public_release_check.py --all-files`.
6. Build the distributions and run
   `python scripts/public_release_check.py --archives`.

## Scope

Keep pull requests small and explain the role boundary they change. New task
adapters need a deterministic evaluator boundary, a synthetic no-model test,
and evidence that controller-only references do not enter Reviewer or
Optimizer inputs.

Do not commit task snapshots, diffs from real projects, gold or held-out
labels, prompts or model responses, trajectories, scores, run receipts,
databases, caches, credentials, or machine-specific paths. Formal artifacts
must be written to an operator-owned directory outside the Git checkout.

## Tests

Unit tests should be deterministic and offline. External model, benchmark,
SkillOpt, or audit-store tests belong in an explicitly configured integration
environment and must not be required for the default test suite.
