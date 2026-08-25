# 架构与信任边界

[English](architecture.md)

## 目的

本项目是一个小型编排框架，不是基准测试数据包、排行榜提交、托管服务或
模型，也不是 SkillOpt 的替代品。它的职责是让任务执行、评估、Skill 提案、
选择和审计之间的边界明确且可测试。

## 组件

~~~text
                         操作者拥有的外部输入
                                      |
                                      v
                              Pipeline Controller
                         /          |           \
                        v           v            v
             隔离的 Reviewer    Evaluator    Optimizer
                 工作区       私有 reference   受限摘要
                 仅含公开内容
                        \           |            /
                         \          v           /
                          +-------严格 gate------+
                                      |
                                      v
                         外部 receipts/artifacts
                                      |
                                      v
                         可选的只读 sidecar
~~~

- Pipeline Controller 冻结各项身份，创建全新的工作区，按顺序调用每个角色，
  执行 gate，并写入终态 receipt。
- Reviewer Backend 接收一个工作区、当前 Skill、attempt identity 和公开的
  task payload。
- Evaluator Backend 接收已完成的 finding batch，以及由 Controller 持有的
  完整 TaskPackage，其中包括私有 reference。
- Optimizer Backend 接收当前 Skill 和受限的 AttemptSummary 对象。它不会
  接收 TaskPackage 对象、reference 或原始 trace。
- Selection gate 按顺序比较 primary 和 secondary 聚合分数，比较规则是
  确定性的。
- 可选 sidecar 可以在某个阶段完成后，镜像保存带哈希的可追溯信息。它不参与
  学习决策。

## 核心契约

TaskPackage 将四类输入分开：

1. snapshot directory；
2. review diff；
3. public task metadata；
4. controller-only private reference。

如果 private reference 存放在 snapshot 内，构造函数会拒绝该输入，因为复制
snapshot 会把它泄露给 Reviewer。计算哈希时也会拒绝 snapshot 中的符号链接，
避免一个看似本地的 snapshot 悄悄包含声明目录树之外的内容。

FindingBatch 中的每个 finding 固定包含六个字段：file、start line、end line、
severity、summary 和 description。Score 包含 primary 和 secondary 两个数值，
二者都在零到一之间，另外还包含 JSON details。

AttemptSummary 是提供给 Optimizer 的唯一 trajectory 对象。它包含 task
identity、split、Skill hash、finding count、score 和长度受限的 failure
string，不包含原始模型对话或 reference material。

## 权限归属

- Reviewer 负责 findings，但不负责其正确性。
- Evaluator 负责 measurements，但不负责修改 Skill。
- Optimizer 负责候选提案，但不负责晋级。
- strict gate 负责决定候选在这条参考流程中是否通过。
- Controller 负责运行状态和 receipts，但不负责任务答案。
- sidecar 只负责其脱离主流程的 provenance 副本。

正式的 SkillOpt 集成应让 Trainer、reflection、merge、current/best state 以及 official gate 继续由固定版本的上游 runtime 管理。公开的 SkillOpt 边界封装一个由操作者提供的调用，不复制这些算法。

## 隔离模型

每次 attempt 都会获得一个新目录。框架只复制以下内容：

- snapshot；
- review diff；
- current Skill；
- public task JSON。

private reference 保留在操作者拥有的路径中，只会传给 Evaluator。train、
selection 和 final 的 task ID 必须彼此不重叠。run root 必须位于 Git checkout
之外。系统会拒绝使用非空的旧 run root，不会把新结果与旧 artifacts 合并。

## 失败与恢复

终态 receipt 会记录 complete 或 failed。某个阶段失败后，不会在原位置修复。只有在新的 run 边界才能修改 configuration、code、model、data 或 scorer，并且必须使用新的 run root。不要拼接互不相关的 outputs，也不要根据不完整目录推断缺失的 artifacts。

## 扩展点

在 backends.py 中实现以下三个协议：

- ReviewerBackend；
- EvaluatorBackend；
- OptimizerBackend。

只有作为明确的、有版本控制的代码引入，并且配有聚焦测试，才能加入自定义 gate policies。可选的 stores 和 report formatters 应消费已完成的 receipts，而不能变成第二个 Trainer。
