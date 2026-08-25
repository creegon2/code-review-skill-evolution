# Code Review Skill Evolution

[English README](README.md)

一个让 AI 代码评审的"方法论"自动进化的框架：跑评审任务、对着隐藏答案打分、
提出改进版方法论，只有新版确实赢过旧版才采纳。

## 一分钟看懂它在干什么

AI 做代码评审时，行为由一份叫 **Skill** 的 markdown 文档引导——里面写着
"检查每个新增的提前 return 是否跳过了资源清理"这类指令。这份文档通常靠人
手工调优，本框架把调优变成一个自动循环：

1. **评审。** AI（称为 *Reviewer*）用当前 Skill 评审一批训练任务，输出
   finding（文件、行号范围、严重级别、问题摘要）。
2. **打分。** 裁判（称为 *Evaluator*）拿 Reviewer 永远看不到的私有标准答案
   对比这些 finding，给出分数。
3. **提议。** *Optimizer* 根据分数摘要，提出一份改进版的候选 Skill。
4. **对决。** 旧 Skill（在位者）和新 Skill（候选者）在另一批全新的选拔任务
   上各跑一遍，候选者只有严格胜出才被采纳。
5. **终测。** 胜者在完全没接触过的终测任务集上跑一次，整轮结果写进一份
   回执（receipt）文件存档。

这种自我改进的循环很容易在不知不觉中"作弊"：标准答案漏进了 Reviewer 的
工作目录、Optimizer 偷看了答案、终测用了训练时见过的任务。本仓库的大部分
代码就是为了让这类作弊在结构上不可能发生——每个角色只能看到它该看的东西，
并且有测试守着。具体的边界设计见[架构文档](docs/architecture.zh-CN.md)。

## 仓库里有什么、没有什么

仓库只包含编排框架本身：流水线、角色之间的数据契约、隔离规则、测试和文档。

**不包含任何评测数据、模型接入和实验结果。** 要跑真实实验，需要你自己提供
评审任务、模型后端、打分器，以及（如果想用完整的 Skill 优化算法）一份固定
版本的 [Microsoft SkillOpt](https://github.com/microsoft/SkillOpt)。各部分
怎么接，见[正式集成说明](docs/formal-integrations.zh-CN.md)。

## 快速上手（不需要模型和网络）

内置 demo 用一个合成的单 bug 任务和假的 Reviewer/Evaluator/Optimizer 把整个
循环跑一遍——它验证的是连线和隔离规则能正常工作，不代表任何真实评审效果。

需要 Python 3.10+：

~~~bash
python -m venv .venv
# 按你的 shell 激活 .venv，然后：
python -m pip install -e ".[dev]"
python -m pytest
python -m code_review_skill_evolution
~~~

默认所有输入输出都在临时目录里，跑完即清理。想保留产物，用 `--run-root`
指定一个**仓库之外**的目录（runner 会拒绝写进 Git checkout 内部，这样生成
的产物永远不会混进提交）：

~~~bash
python -m code_review_skill_evolution --run-root /absolute/external/run
~~~

## 各角色分工

| 角色 | 做什么 | 被刻意禁止做什么 |
|---|---|---|
| Reviewer | 在全新 workspace 里评审一个任务，返回 finding | 看标准答案、别的 attempt、终测标签 |
| Evaluator | 拿私有标准答案给完成的 finding 打分 | 修改 Skill 或 Reviewer 的输出 |
| Optimizer | 根据分数摘要提出候选 Skill | 看标准答案或原始模型对话 |
| Gate | 纯机械地比较在位者和候选者的分数 | 凭任何人的主观偏好放行候选者 |
| Pipeline（控制器） | 冻结输入、按序执行各阶段、写回执 | 中途修补产物或改配置 |
| 审计 sidecar（可选） | 把已完成的产物镜像到外部存储 | 向循环回灌任何信息 |

Reviewer、Evaluator、Optimizer 是注入式接口（见 `backends.py`），可以分别
接真实模型、确定性打分器或官方 SkillOpt。

## 数据放哪里

数据处理的设计基本可以归结为两条规则：

- **标准答案只归裁判。** Reviewer 的 workspace 按白名单构建——代码快照、
  评审 diff、当前 Skill、公开元数据，仅此四样。标准答案必须放在快照目录
  **之外**，因为 workspace 就是快照的一份拷贝：放在里面等于直接发给考生。
- **运行产物不进 Git。** 每次运行都写到仓库外的目录。公开发布前跑一遍
  发布检查，确认没有私有内容混入：

~~~bash
python scripts/public_release_check.py --all-files
python -m build
python scripts/public_release_check.py --archives
~~~

## 目录结构

~~~text
src/code_review_skill_evolution/   框架本体（零第三方依赖）
  contracts.py                     角色间传递的数据契约
  pipeline.py                      进化循环本身
  gate.py                          候选者 vs 在位者的严格比较
  isolation.py                     按白名单构建 Reviewer workspace
  demo.py                          离线合成 demo
  integrations/skillopt.py         官方 SkillOpt 的薄接口层
tests/unit/                        契约、gate、隔离的单元测试
tests/integration/                 端到端合成运行
examples/                          可运行的离线示例
docs/                              架构、流程、适配指南
scripts/                           公开发布检查
~~~

## 文档

- [架构与信任边界](docs/architecture.zh-CN.md) —— 角色、契约，以及每道墙
  为什么存在
- [工作流程](docs/workflow.zh-CN.md) —— 一次运行的逐阶段拆解
- [适配你自己的任务](docs/adapting-a-task.zh-CN.md)
- [正式集成](docs/formal-integrations.zh-CN.md) —— 接真实模型、打分器、
  SkillOpt、审计存储
- [仓库结构的出处](docs/design-sources.zh-CN.md)

## 状态与许可

0.1.0 是参考实现：离线路径可复现，不含真实评测结果。原创代码以
[MIT License](LICENSE) 发布，外部集成各自保留原许可。
