# 架构与信任边界

[English](architecture.md)

## 为什么要修这么多墙

这条流水线改进的正是引导 Reviewer 行为的那份文档，所以它是一个自我改进的
循环——而自我改进的循环有几种可预测的翻车方式：

1. **答案泄漏。** 标准答案出现在 Reviewer（或 Optimizer）能读到的地方，
   分数从此失去意义。
2. **自己给自己打分。** 提出改进的组件同时裁判改进是否有效。
3. **事后篡改。** 输入或产物被悄悄改动，事后没人说得清当时到底跑了什么。

设计里的每一道边界都在堵这三个口子中的一个。下面某条规则如果显得过分较真，
它防的通常是那种等结果已经错了才会被发现的泄漏。

## 角色和术语表

| 术语 | 含义 |
|---|---|
| **Skill** | 引导 Reviewer 的 markdown 方法论文档，也就是被进化的对象。 |
| **Reviewer** | 评审代码、输出 finding。正式运行接模型，demo 里是假实现。 |
| **Evaluator** | 拿私有标准答案给 finding 打分的裁判。 |
| **Optimizer** | 根据分数摘要提出候选 Skill。 |
| **Controller / pipeline** | 编排者：冻结输入、按序执行各阶段、写回执。 |
| **Gate** | 决定候选者能否取代在位者的机械规则。 |
| **Attempt** | Reviewer 对一个任务的一次评审，每次都在全新 workspace 里。 |
| **Split** | 任务属于三个互不重叠集合中的哪一个：train（训练）、selection（选拔）、final（终测）。 |
| **在位者 / 候选者** | incumbent / candidate：当前 Skill vs 新提出的 Skill。 |
| **Receipt（回执）** | 一次运行留下的 JSON 存档：输入哈希、各阶段结果、gate 裁决、终测分数。 |
| **Sidecar** | 可选的只读审计镜像。 |

## 组件如何连接

~~~text
        操作者提供的输入（任务、标准答案、初始 Skill）
                          |
                          v
                   Pipeline Controller
          /               |                \
         v                v                 v
     Reviewer         Evaluator         Optimizer
  能看到：快照、    能看到：finding    只能看到：
  diff、Skill、     + 私有标准答案     分数摘要
  公开元数据
         \                |                /
          \               v               /
           +-------- 严格 gate ----------+
                          |
                          v
             回执与产物（仓库之外）
                          |
                          v
              可选的只读审计 sidecar
~~~

Reviewer、Evaluator、Optimizer 是 `backends.py` 里的 `Protocol` 接口，
流水线不关心背后是什么实现。正式部署时，Optimizer 接官方
[Microsoft SkillOpt](https://github.com/microsoft/SkillOpt)，Evaluator 接
确定性打分器，Reviewer 接真实模型后端。

## 数据契约

隔离规则真正落地的地方是 `contracts.py` 里的数据类型——大多在构造函数里
校验，所以非法对象根本无法被创建出来。

**TaskPackage** 打包一个任务的四份输入：代码快照目录、评审 diff、公开
元数据、私有标准答案（`private_reference`）。其中两条校验规则值得解释：

- *标准答案必须在快照目录之外。* Reviewer 的 workspace 是把快照整个拷贝
  出来建的，答案放在快照里就等于原样拷给了 Reviewer。
- *快照里不允许有 symlink。* symlink 可以指向机器上任何位置，会让一个看似
  自包含的快照悄悄带进未声明的文件——包括标准答案。

公开元数据还会按键名过滤：包含 `answer`、`gold`、`label`、`oracle`、
`reference`、`secret` 等片段的键一律拒绝——这类字段属于 Evaluator，不该
出现在 Reviewer 能读的材料里。

**Finding / FindingBatch** 是 Reviewer 的输出：每条 finding 有文件、起止
行号、严重级别（`Critical`/`Major`/`Minor`/`Trivial`/`Info`）、摘要和描述。
文件路径必须是相对路径，且不能逃出快照。

**Score** 是 Evaluator 的输出：primary 和 secondary 两个 0 到 1 之间的
数字，外加自由格式的 JSON 详情。详情留在控制器一侧，永远不会转发给
Optimizer。

**AttemptSummary** 是 Optimizer 对一次 attempt *唯一*能看到的东西：任务
ID、split、Skill 哈希、finding 数量、两个分数，顶多再加一个不透明的失败码。
没有答案，没有模型对话，没有文件路径。这是刻意的：Optimizer 的职责是根据
结果改进 Skill，给它更多信息就是重新打开泄漏的口子。

## 权责划分

每个角色只拥有一种决定权，因此没有角色能给自己的工作打分：

- Reviewer 拥有 finding 本身，但无权判定其对错。
- Evaluator 拥有测量结果，但无权改 Skill。
- Optimizer 拥有提案权，但无权决定是否采纳。
- Gate 拥有采纳权——按固定机械规则，不掺判断。
- Controller 拥有运行状态和回执，但不碰任务答案。
- Sidecar 只拥有它那份独立的拷贝。

接入官方 SkillOpt 时，其 Trainer、reflection、merge、gate 逻辑全部留在
固定版本的上游 checkout 里。这边的边界类（`integrations/skillopt.py`）
只负责把当前 Skill 和受限摘要传过去，不复刻任何算法。

## 运行时隔离

- 每次 attempt 都新建一个 workspace 目录，里面只有四样东西：快照拷贝、
  评审 diff、当前 Skill、公开任务 JSON。attempt 之间零复用，谁也看不到
  谁的状态。
- 标准答案原地不动，始终在操作者自己的路径下，只有 Evaluator 在 Reviewer
  结束之后才会打开它。
- train、selection、final 三组任务 ID 必须互不重叠。终测集的意义就是在
  Skill 从未影响过的任务上测它，一旦重叠，终测分数就退化成了训练分数。
- run root 必须在 Git checkout 之外且初始为空——既保证生成产物进不了
  版本库，也防止两次运行的产物混在一起。

## 运行失败时

一次运行只有两种收场：回执写着 `complete` 或 `failed`。失败的阶段不做原地
修补——改好配置、代码或数据之后，用新的 run root 开一次*新的*运行。把不同
运行的产物拼在一起、或手改已有运行目录，都会毁掉回执存在的意义：目录里的
一切都确实来自记录在案的那组输入。

## 扩展框架

实现 `backends.py` 里的三个协议：`ReviewerBackend`、`EvaluatorBackend`、
`OptimizerBackend`。完整步骤见[适配你自己的任务](adapting-a-task.zh-CN.md)。

需要不同的采纳规则时，在 `gate.py` 旁边写成显式的、有版本、有测试的代码，
而不是留一个手动放行口。报表生成器和审计存储只该消费已完成的回执——它们
一旦开始影响哪个 Skill 胜出，就成了第二个隐形的 Optimizer。
