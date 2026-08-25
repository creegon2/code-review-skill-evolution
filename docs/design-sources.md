# Design sources

[中文](design-sources.zh-CN.md)

The repository layout is not invented here — it is the common minimum shared
by actively maintained public Python agent/evaluation projects, kept
deliberately small:

- [Microsoft SkillOpt](https://github.com/microsoft/SkillOpt) — the
  guide-style documentation and the explicit benchmark-adapter boundary.
- [OpenAI Agents SDK for Python](https://github.com/openai/openai-agents-python)
  — the `src/` layout with separate `tests/` and `examples/`, and focused CI.
- [Giskard OSS](https://github.com/Giskard-AI/giskard-oss) — offline examples
  that CI actually runs, and package-level test separation.
- [DeepEval](https://github.com/confident-ai/deepeval) — visible examples,
  docs, tests, and contributor-facing project files.

What this project takes from them: `src/`, `tests/`, `examples/`, `docs/`,
CI, LICENSE, CONTRIBUTING, SECURITY, and release checks. What it leaves
behind: their data directories, web apps, monorepo layers, and
product-specific integrations.
