# 正式集成

[English](formal-integrations.md)

这个无依赖核心有意保持得比正式实验环境更小。要进行真实运行，必须明确配置
外部集成。

## SkillOpt

请使用官方的 [Microsoft SkillOpt 仓库](https://github.com/microsoft/SkillOpt)。
公开边界已基于提交
`3c8873f016397817dcd40c3e5436d92fe19372b8` 完成验证。每次正式运行都应固定
使用一个经过审查的版本。

模块 `integrations/skillopt.py` 为由操作者负责提供的可调用对象暴露
`SkillOptProposalBoundary`。它只传入当前 Skill 和有界的轨迹摘要；不会在本仓库中打包或重新实现
SkillOpt 的 Trainer、reflection、merge 或 gate 行为。

生产适配器应针对所选择的确切上游版本进行测试。仅有相同的版本号，不能证明
代码完全相同。

## 代码评审评分器

早期的私有环境曾围绕 [Alibaba AACR-Bench](https://github.com/alibaba/aacr-bench)
使用一层适配器边界，使用的提交是 `b3072489eace26efca8bcf2b1ac6a24ba64f82c1`。
本仓库不包含它的代码或数据。

操作者可以使用这个固定版本的评分器，或其他面向具体任务的确定性评估器，实现
`EvaluatorBackend`。参考标签只能提供给 Controller/Evaluator；同时要把适配器产生的测量结果与官方排行榜指标区分开。

## Reviewer 模型

`ReviewerBackend` 有意保持与模型提供商无关。基于模型的实现必须明确配置模型身份、推理设置、沙箱、网络、工具、凭据、并发数、超时和保留策略。
每次尝试都必须从全新的上下文开始，并且不得读取其他尝试、选择标签、最终标签或私有参考资料。

## 可选的审计存储

核心会写入 JSON 回执，不要求使用 HeavenBase。操作者可以额外接入一个与主流程分离的 HeavenBase 或其他审计存储旁路组件；该组件只能读取已完成的产物、核验哈希，并保存精简的来源信息。

旁路组件不得：

- 修改当前 Skill 或最佳 Skill；
- 更改分数或 gate 决策；
- 将隐藏的参考资料送入训练；
- 把未完成的官方产物伪装成已完成；
- 写入另一次运行正在使用的共享状态树。

本仓库不包含任何私有 HeavenBase wheel、本地路径依赖、数据库或源码检出副本。

## 数据位置

以下所有内容都应放在 Git 之外：

- 任务快照和评审差异；
- train、selection、held-out 或 final 标签；
- 模型提示词、响应、对话和原始轨迹；
- 轨迹包和候选输出；
- 分数、报告、回执和运行数据库；
- 模型凭据和隔离的后端状态。

公开发布防护是额外的一项检查，不能替代操作者对 Git 历史和生成归档文件的审查。
