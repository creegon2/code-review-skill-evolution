# 第三方说明

[English](THIRD_PARTY_NOTICES.md)

本文件是便于中文读者了解依赖边界的说明。许可证、版权及其他法律信息以
[英文原文](THIRD_PARTY_NOTICES.md)和各上游项目发布的文件为准。

本仓库不内置第三方源代码、benchmark 数据、模型输出或二进制包。下面列出的
集成都在仓库之外完成，并且都是可选项。

## Microsoft SkillOpt

- 项目：Microsoft SkillOpt
- 来源：https://github.com/microsoft/SkillOpt
- 许可证：MIT
- 本框架验证集成边界时使用的公开基线：
  `3c8873f016397817dcd40c3e5436d92fe19372b8`
- 版权：Copyright (c) 2026 Microsoft Corporation

公开核心没有复制 SkillOpt 的 Trainer、reflection、merge 或 gate 逻辑。启用
正式集成时，操作者需要自行取得上游代码，并在对应 checkout 中保留其许可证。

## Alibaba AACR-Bench

- 项目：Alibaba AACR-Bench
- 来源：https://github.com/alibaba/aacr-bench
- 许可证：Apache License 2.0
- 最初验证代码评审 scorer 边界时参考的提交：
  `b3072489eace26efca8bcf2b1ac6a24ba64f82c1`

本仓库不包含 AACR-Bench 的代码或数据。它的数据集可能包含来自其他项目的
材料；操作者需要自行确认相应的访问权限、署名要求和再分发条件。

## HeavenBase

- 项目：HeavenBase
- 公开发行信息：https://pypi.org/project/heavenbase/
- 许可证：MIT

HeavenBase 不是公开核心的依赖。操作者可以将独立的审计存储 sidecar 作为可选
集成自行实现；本仓库不发布任何私有 wheel，也不包含指向本机路径的依赖。
