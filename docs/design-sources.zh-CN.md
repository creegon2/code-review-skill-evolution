# 仓库结构的出处

[English](design-sources.md)

这个仓库的布局不是自创的——它是活跃维护的公开 Python agent/评测项目共有
的最小公约数，再刻意做小：

- [Microsoft SkillOpt](https://github.com/microsoft/SkillOpt) —— 指南式
  文档和显式的 benchmark 适配器边界。
- [OpenAI Agents SDK for Python](https://github.com/openai/openai-agents-python)
  —— `src/` 布局、tests 与 examples 分离、聚焦的 CI。
- [Giskard OSS](https://github.com/Giskard-AI/giskard-oss) —— CI 真的会跑
  的离线示例、包级测试分离。
- [DeepEval](https://github.com/confident-ai/deepeval) —— 面向贡献者的
  示例、文档、测试和项目元文件。

从它们那里取的：`src/`、`tests/`、`examples/`、`docs/`、CI、LICENSE、
CONTRIBUTING、SECURITY、发布检查。没取的：数据目录、Web 应用、monorepo
层级、产品专属集成。
