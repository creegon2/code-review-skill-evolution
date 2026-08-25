# Public repository design sources

The repository uses a deliberately small version of structures visible in
actively maintained public Python agent and evaluation projects:

- [Microsoft SkillOpt](https://github.com/microsoft/SkillOpt): guide/reference
  documentation and explicit benchmark-adapter boundaries.
- [OpenAI Agents SDK for Python](https://github.com/openai/openai-agents-python):
  src layout, separate tests and examples, and focused CI.
- [Giskard OSS](https://github.com/Giskard-AI/giskard-oss): offline examples
  validated in CI and package-level test separation.
- [DeepEval](https://github.com/confident-ai/deepeval): visible examples,
  documentation, tests, contribution files, and maintainer-facing project
  metadata.

This project adopts the common minimum: src, tests, examples, docs, CI,
LICENSE, CONTRIBUTING, SECURITY, and release checks. It does not copy their
large data directories, web applications, monorepo layers, or product-specific
integrations.
