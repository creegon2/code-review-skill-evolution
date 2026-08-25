# 工作流与状态转换

[English](workflow.md)

## 状态拓扑

~~~text
prepared
  -> inputs_frozen
  -> train_reviewer_completed
  -> train_evaluated
  -> candidate_proposed
  -> incumbent_selection_completed
  -> candidate_selection_completed
  -> gate_decided
  -> final_evaluated
  -> terminal
~~~

外部运行根目录完成校验并创建后，任何后续异常都会写入失败的终态回执，并停止运行。在创建回执之前，框架会拒绝无效的输出位置。框架不会补填缺失字段，也不会从其他运行继续执行。

## 1. 冻结输入

Controller 会对初始 Skill、每个 diff、每棵 snapshot tree 以及每个 private reference 计算哈希。manifest 记录哈希和公开元数据，不记录机器路径。Reviewer 运行前会冻结 Split identities。

## 2. 运行训练 Reviewer

对于每个 train task，Controller 都会创建一个全新的 allowlist workspace，并将其传给 ReviewerBackend。原始 private reference 永远不会复制到该 workspace 中。

## 3. rollout 后评估

只有在 FindingBatch 完成定稿后，EvaluatorBackend 才会运行。它可以读取由 Controller 管理的 private reference，并返回一个 Score。对于 operator-supplied scorer，确定性是 formal run 的要求；但注入协议本身无法证明这一点。Finding 和 score 会写入外部运行根目录下。

## 4. 提出一个 candidate

Optimizer 接收有界的 AttemptSummary 值。在正式的 SkillOpt 部署中，固定版本的 official runtime 应执行反思和 candidate 构造。offline smoke 只使用确定性的 fake 来演练这次交接。

## 5. 重新运行 selection

Incumbent Skill 和 candidate Skill 都会在同一个冻结的 selection set 上接受全新的 attempt。任何一次运行都不会复用训练 workspace。两者的 score 会分别聚合。

## 6. 应用严格 gate

只有满足以下条件之一，candidate 才会被接受：

1. 它的 aggregate primary score 更高；或
2. primary score 持平，且它的 aggregate secondary score 更高。

结果相同或更低都会被拒绝。手动 promotion 不属于参考工作流。

## 7. 最终评估

只有被接受的 Skill 才会在互不重叠的 final set 上运行。final score 是针对确切所提供的数据、模型、scorer 和 configuration 的测量证据，不会自动成为可泛化性的证据。

## 8. 写入终态回执

回执包含 manifest hash、按顺序排列的 stage status、gate inputs 和 decision、被接受的 Skill hash，以及 final aggregate score。回执有意不声称框架或 Skill 在普遍意义上有效。

## 恢复规则

配置和实现变更应发生在两次运行之间。发生失败或设计变更后，启动新的 run identity 和目录。绝不要手动修改活动运行的 trace、candidate、score 或 receipt。
