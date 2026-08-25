# 适配另一个任务

[English](adapting-a-task.md)

## 1. 定义任务边界

明确任务的公开输入、仅 Controller 可见的标签、输出 schema 和测量目标。所有真实任务材料都必须放在本仓库之外。

构造 `TaskPackage`，其中包括：

- 唯一任务 ID；
- 不可变的快照目录；
- 评审 diff；
- 位于快照之外的私有 evaluator reference；
- 对 Reviewer 安全的元数据。

不得在公开元数据中放置 gold、oracle、answer、expected 或 reference 字段。

## 2. 实现 `ReviewerBackend`

后端接收包含新 workspace、公开任务 payload、当前 Skill 和 attempt ID 的 `ReviewerRequest`。它必须返回 `FindingBatch`。

对于模型驱动的实现：

- 固定后端和模型身份；
- 强制执行超时；
- 禁用未经批准的网络、工具、插件和共享状态；
- 不得在不同 attempt 之间复用 conversation；
- 仅在外部 run root 下，并按照操作者的数据政策保留原始 trace。

## 3. 实现 `EvaluatorBackend`

Reviewer 完成后，evaluator 才能接收完整的 `TaskPackage`。尽可能使用确定性 scorer。将歧义和 evaluator 失败与 Reviewer 失败分开记录。缺少匹配项时，不得默默将其重新解释为已确认的 bug 或非 bug。

## 4. 实现 `OptimizerBackend`

optimizer 接收包含当前 Skill 和有界 trajectory 摘要的 `OptimizationRequest`。它必须返回一个非空的候选 Skill。

对于正式 SkillOpt 使用，将这一边界绑定到固定版本的官方 checkout，并保持其 Trainer、reflection、merge、current/best state 以及 gate 语义不变。不得在 sidecar 或报告生成器中创建第二条隐藏的晋级路径。

## 5. 添加无模型测试

在测试临时目录下生成一个微型合成任务。使用 fake Reviewer、Evaluator 和 Optimizer backend。验证：

- private reference 的字节和路径不会进入 Reviewer task JSON；
- 每个 attempt 都会获得新的 workspace；
- selection 时 incumbent 和 candidate 都会重新运行；
- 分数相等时拒绝 candidate；
- 严格提升时接受 candidate；
- final evaluation 使用被接受的 Skill；
- 终态 receipt 完整且 schema 有效；
- 正式产物不会写入 Git checkout。

合成 fixture 只测试契约，不是 benchmark 证据。

## 6. 正式运行检查清单

- 真实输入和 reference 存放在 Git 之外。
- train、selection 和 final 的身份已冻结且彼此不重叠。
- model、scorer、SkillOpt、prompt 和 configuration 的身份已固定。
- 已审计 Reviewer 的可见范围。
- 每个 attempt 都使用隔离的 workspace 和 state。
- run root 位于外部且为空。
- 网络、审批、并发、超时和成本政策均已明确。
- 运行期间不会修补任何阶段或重新配置任何阶段。
- 发布审查同时覆盖 Git 文件和生成的 source archive。
