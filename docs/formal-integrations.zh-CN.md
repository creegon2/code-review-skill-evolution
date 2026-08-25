# 正式集成

[English](formal-integrations.md)

仓库里的核心零第三方依赖就能跑——也正因如此，它自己跑不了真实实验。本文
列出正式运行需要外接的组件，以及各自的规则。

## SkillOpt（Optimizer）

用官方 [Microsoft SkillOpt 仓库](https://github.com/microsoft/SkillOpt)。
这边的边界层是对着基线 commit `3c8873f016397817dcd40c3e5436d92fe19372b8`
验证的；每次正式运行钉死一个审过的版本，并拿你的适配器对着那个确切版本
测试——版本号相同不等于代码相同。

`integrations/skillopt.py` 提供 `SkillOptProposalBoundary`：一个薄包装，
包住你从固定 checkout 里提供的调用。它传入当前 Skill 和受限的 attempt
摘要，期待返回一个候选 Skill。它刻意不搬运、不复刻 SkillOpt 的 Trainer、
reflection、merge、gate 逻辑——那些留在上游，才能对着钉死的 commit 审计。

## 代码评审打分器（Evaluator）

本框架的前身私有环境用的是围绕
[Alibaba AACR-Bench](https://github.com/alibaba/aacr-bench)（commit
`b3072489eace26efca8bcf2b1ac6a24ba64f82c1`）的适配层。其代码和数据都不在
本仓库里。

你可以用那个打分器或任何确定性的任务专用打分器实现 `EvaluatorBackend`。
无论选哪个，两条规则不变：参考标签只有控制器和 Evaluator 可读；经你的
适配层得出的测量结果要如实标注来源——它们不是官方榜单数字。

## Reviewer 模型

`ReviewerBackend` 刻意保持提供商中立。接真实模型时必须钉死模型身份和推理
设置，并显式配置沙箱、网络、工具、凭据、并发、超时和 trace 保留策略。每次
attempt 从全新上下文开始，不能读到其他 attempt、选拔或终测标签、标准
答案——框架在磁盘上强制的隔离，你的后端要在模型上下文里同样守住。

## 可选的审计存储

核心只写普通 JSON 回执，不需要数据库。想要更长期的溯源，可以加一个
sidecar（HeavenBase 或别的都行）：读已完成的产物、核验哈希、存一份紧凑
拷贝。

唯一的设计规则：sidecar 对循环是只读的。它不能改 Skill 或分数、不能把
参考材料回灌进训练、不能把未完成的产物包装成完成的、不能和另一次运行共享
状态。能影响实验的审计记录，就不再是审计记录了。

## 哪些东西留在 Git 之外

运行接触或产出的一切都在 checkout 之外：快照和 diff、任何 split 的标签、
prompt 和模型 trace、候选 Skill、分数、回执、运行数据库、凭据。

`scripts/public_release_check.py` 会在公开发布前扫一遍防事故，但它是安全
网，不能替代审查本身——Git 历史和生成的归档包也要看。
