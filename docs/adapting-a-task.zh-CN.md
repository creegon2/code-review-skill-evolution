# 适配你自己的任务

[English](adapting-a-task.md)

框架自带的只有一个合成 demo 任务。要在你自己的代码评审材料上跑，需要定义
任务边界并实现三个后端接口。本文逐步说明。

## 1. 定义任务边界

针对你的任务格式，决定每份材料归入 `TaskPackage` 四个槽位中的哪一个：

- **snapshot** —— Reviewer 可以读的代码树（一个目录）；
- **diff** —— 待评审的变更；
- **metadata** —— 其他允许 Reviewer 知道的信息（仓库名、变更描述等）；
- **private_reference** —— 标准答案，放在快照目录*之外*。

这个划分就是整件事的核心：前三样全部到达 Reviewer，只有第四样到达
Evaluator。拿不准某份材料归哪边时，问一句"人类评审员拿得到这个吗？"——
拿不到的就是参考答案材料。

`TaskPackage` 会在构造时拦住明显的错误（答案放进了快照、元数据键名长得像
标签——`gold`、`expected`、`oracle` 之类会被按名拒绝），但它不认识你的
数据。真实任务材料完全不要进这个仓库，仓库里只放适配器代码。

## 2. 实现 `ReviewerBackend`

只有一个方法：`review(request) -> FindingBatch`。request 里有全新的
workspace 路径、公开任务 payload、当前 Skill 文本和 attempt ID。

接真实模型时，反复出现的主题是*全新且钉死*：

- 钉死后端和模型身份，保证运行之间可比；
- 每次 attempt 都从全新对话开始——复用对话会让知识在 attempt 之间流动，
  悄悄破坏在位者与候选者的比较；
- 设执行超时，关掉未经明确批准的网络、工具和共享状态；
- 要保留原始模型 trace 的话，放在外部 run root 之下，按你自己的数据政策管。

## 3. 实现 `EvaluatorBackend`

只有一个方法：`score(task, findings) -> Score`。它在 Reviewer 结束之后才
运行，并且是唯一被允许读 `task.private_reference` 的后端。

优先用确定性打分器——gate 靠分数比较两份 Skill，打分器的随机性会表现为两
者之间的幻影差异。另外，"打分器判不了"要和"Reviewer 什么都没找到"分开
记录；把模糊情况硬压成确信的 0 或 1，污染的正是 Optimizer 赖以学习的信号。

## 4. 实现 `OptimizerBackend`

只有一个方法：`propose(request) -> str`，返回一个非空候选 Skill。request
里是当前 Skill 和每个 attempt 的受限摘要——Optimizer 能拿到的仅此而已，
没有答案，没有对话记录。

要用官方 SkillOpt，把你固定版本 checkout 的提案调用包进
`SkillOptProposalBoundary`（见[正式集成](formal-integrations.zh-CN.md)）。
SkillOpt 自己的训练循环、reflection 和状态留在原处，边界类只负责把请求
递过去。

抵制加旁路的诱惑：报表生成器或审计存储一旦开始影响提案或采纳，它就是第二
个看不见的 Optimizer，结果从此说不清归功于谁。

## 5. 先用假后端测试，再花钱

接真实模型之前，照着 `demo.py` 的做法给你的任务格式来一遍：在临时目录里
生成一个微型合成任务，用假后端驱动流水线，把要紧的性质都断言到：

- 标准答案的内容和路径都没出现在 Reviewer 的 workspace 里；
- 每次 attempt 都有自己的 workspace；
- 在位者和候选者都在选拔集上重跑了；
- 分数打平被拒绝、严格更优被接受；
- 终测阶段跑的是被采纳的那份 Skill；
- 终态回执完整且符合 schema；
- 没有任何东西写进 Git checkout。

这些测试便宜、确定，而且恰好逮得住那类等付费运行跑完才会暴露的泄漏 bug。

## 6. 正式运行前的检查单

- 真实任务和标准答案都在 Git 之外。
- train、selection、final 三组任务 ID 已冻结且互不重叠。
- 模型、打分器、SkillOpt 版本、prompt、配置都已钉死。
- 审计过 Reviewer 在 workspace 里实际能看到什么。
- run root 在仓库外且为空。
- 网络、并发、超时、成本政策都已写明。
- 没有人会在运行中途"顺手修一下"某个阶段——改动等下一次运行。
- 发布审查覆盖生成的归档包，不只是 Git 文件。
