# 公开仓库设计来源

[English](design-sources.md)

本仓库有意采用了一套精简版结构，其设计参考了以下仍在积极维护的公开 Python Agent 和评测项目中可见的做法：

- [Microsoft SkillOpt](https://github.com/microsoft/SkillOpt)：指南/参考文档，以及明确的 benchmark 适配器边界。
- [OpenAI Agents SDK for Python](https://github.com/openai/openai-agents-python)：`src` 目录布局、分离的测试与示例，以及聚焦的 CI。
- [Giskard OSS](https://github.com/Giskard-AI/giskard-oss)：在 CI 中验证的离线示例，以及按包分离的测试。
- [DeepEval](https://github.com/confident-ai/deepeval)：公开示例、文档、测试、贡献文件，以及面向维护者的项目元数据。

本项目采用这些项目共有的最小集合：`src`、`tests`、`examples`、`docs`、CI、`LICENSE`、`CONTRIBUTING`、`SECURITY` 和发布检查。但本项目并未复制它们的大型数据目录、Web 应用、单仓库多层结构或特定产品集成。
