# Code Review Skill Evolution

[English README](README.md)

这是一个不带实验数据的公开参考框架，用来把代码评审任务接进一条可审计的
Skill 学习与选择流程。

仓库只发布编排代码、角色边界、数据契约、测试和流程文档；不发布真实任务、
项目源码快照、diff、私有标签、模型对话、trajectory、分数、运行 receipt、
数据库或凭据。

## 它具体跑什么

~~~text
操作者在仓库外准备输入
  -> 冻结身份和哈希
  -> Reviewer 在独立 workspace 中执行
  -> Controller 使用私有参考做评测（正式运行应使用确定性 scorer）
  -> 只把受限轨迹摘要交给 Optimizer
  -> 生成候选 Skill
  -> incumbent 和 candidate 在 selection 任务上分别重跑
  -> 严格机械 gate
  -> final 评估
  -> 在仓库外写终态 receipt
~~~

默认 quick start 使用临时合成任务和 fake backend，不需要模型账号、网络、
benchmark checkout 或 HeavenBase。它证明框架连线和隔离契约能跑通，不是
真实实验成绩。

## 角色边界

| 角色 | 负责 | 不负责 |
|---|---|---|
| Reviewer | 读取当前任务允许看到的材料，输出结构化 finding | 读取私有参考、其他 attempt 或 final 标签 |
| Evaluator | Reviewer 停止后，用 Controller 私有材料评分 | 修改 Skill 或 Reviewer 输出 |
| Optimizer | 根据受限轨迹摘要提出候选 Skill | 读取 raw reference 或代替 Evaluator |
| Gate | 机械比较 incumbent 与 candidate | 人工偏好式晋级 |
| Runner | 冻结输入、串联阶段、写 receipt | 在运行中手补产物或改配置 |
| 可选 sidecar | 把已完成 provenance 镜像到外部审计存储 | 反向改变 Trainer 的 gate 或父 Skill |

## 本地离线运行

需要 Python 3.10 或更新版本。先创建并按当前 shell 的方式激活虚拟环境，再运行：

~~~bash
python -m venv .venv
# 激活 .venv 后：
python -m pip install -e ".[dev]"
python -m pytest
python -m code_review_skill_evolution
~~~

默认产生的合成输入和输出都在临时目录，命令结束后会清理。要保留合成产物，
必须指定 Git checkout 之外的绝对目录：

~~~bash
python -m code_review_skill_evolution --run-root /absolute/external/run
~~~

## 正式运行还需要什么

正式运行需要操作者另外提供：任务快照与 diff、私有参考标签、固定 SkillOpt
或其他 Optimizer、Reviewer 模型与权限、任务专用 scorer、冻结 split 与
配置、独立 workspace、仓库外 run root，以及网络、时间、并发和成本政策。

这些内容不会随公开仓库发布。具体边界见
[正式集成说明](docs/formal-integrations.zh-CN.md)。

## 公开边界

Reviewer workspace 只复制 snapshot、review diff、当前 Skill 和公开任务
metadata。private reference 必须放在 snapshot 之外，只能在 Reviewer 结束后
交给 Evaluator。Optimizer 只接收分数、finding 数量等受限摘要，不接收
private reference 或 raw trace。

每次公开前运行：

~~~bash
python scripts/public_release_check.py --all-files
python -m build
python scripts/public_release_check.py --archives
~~~

合成 smoke 只能证明框架流程可执行，不能证明 Skill 在真实 benchmark、其他
模型或未见数据上会提升。

## 目录

~~~text
src/code_review_skill_evolution/   无外部依赖的编排核心
tests/unit/                        确定性契约测试
tests/integration/                 合成端到端测试
examples/                          离线示例
docs/                              架构、流程与适配说明
scripts/                           公开发布检查
.github/                           CI 与贡献模板
~~~

## 文档

- [中文文档导航](docs/index.zh-CN.md)
- [架构与信任边界](docs/architecture.zh-CN.md)
- [工作流与状态](docs/workflow.zh-CN.md)
- [如何适配新任务](docs/adapting-a-task.zh-CN.md)
- [正式集成](docs/formal-integrations.zh-CN.md)
- [公开仓库的设计参考](docs/design-sources.zh-CN.md)
- [第三方说明](THIRD_PARTY_NOTICES.zh-CN.md)

当前 0.1.0 是参考实现和 POC 基础设施，不包含任何真实 benchmark 结论。
仓库原创代码使用 [MIT License](LICENSE)。
