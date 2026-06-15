<div align="center">
  <h1>BlackCow Ops</h1>

  <p><strong>受 BKIT 启发的智能体工程框架。</strong><br />
  专为 Reasonix + DeepSeek 构建。</p>

  <p>
    <a href="#安装">安装</a>
    ·
    <a href="#快速开始">快速开始</a>
    ·
    <a href="README.md">English</a>
    ·
    <a href="README.ko.md">한국어</a>
    ·
    <a href="README.ja.md">日本語</a>
  </p>
</div>

<hr />

> [!NOTE]
> **BlackCow Ops 是一套 6 个自我改进的 Reasonix 技能**，构成完整的 plan→execute→verify→evolve 流水线。它强制执行 BKIT — 一个带有数值阈值的 11 门质量分类体系，针对 DeepSeek 的成本优势进行了适配。
>
> 以 DeepSeek 的价格（~$0.14/1M 输入 token），运行 15 条并行发现通道 + 8 个对抗性 QA 智能体 + 7 个 PDCA 循环，总成本不到 **$0.03**。

## 项目状态

| 指标 | 分数 |
| --- | --- |
| **BlackCow Ops 分数** | **94.0 / 100** |
| **目标** | ~~突破 90 分~~ ✅ 已达成！ |

> BlackCow Ops 分数是 11 个质量维度的综合指标。详见[质量分数演进](#质量分数演进)。

## 安装

```bash
# 克隆到 Reasonix 技能目录
git clone https://github.com/blackcowmaster/blackcow-ops.git
cp blackcow-ops/skills/*.md ~/.reasonix/skills/
```

重启 Reasonix。6 个 `blackcow-*` 技能现已全局可用。

## 适用场景

| 场景 | 建议 |
| --- | --- |
| **使用 Reasonix + DeepSeek** | **原生。** 所有模型层级、上下文预算和 PDCA 循环次数均已针对 DeepSeek 调优。零配置使用全部 6 个技能。 |
| **使用 Reasonix + 其他模型** | **未经测试。** Reasonix 通过 AI SDK 支持其他提供商（Anthropic、OpenAI、Google 等），但 BlackCow 仅在 DeepSeek 上测试过。如尝试其他模型，请修改每个技能 YAML 头部的 `model_tiers` 并调整上下文预算。结果不作保证。 |
| **使用 Claude Code、Codex CLI、OpenCode 或其他框架** | **需要移植。** BKIT 方法论独立于任何特定框架。当前 `.md` 技能文件是 Reasonix 原生的 — 需要为目标框架重写 `task`、`edit_file`、`multi_edit` 等工具调用。 |
| **只需要 11 门质量方法论** | **免费。** 阅读 `docs/BKIT.md` — 分类体系、阈值和审计智能体设计均有文档记录。适用于任何工作流。Apache 2.0。 |

## 命令

| 命令 | 功能 |
| --- | --- |
| `blackcow-plan` | 战略规划器。从 10 个角度分析代码库，提出 3 种架构方案，编写决策完备的计划。绝不编写产品代码。 |
| `blackcow-loop` | 执行引擎。TDD + Hashline 内容验证 + PDCA 迭代器 + 10 智能体对抗性 QA。只有全部 11 个质量门产生超阈值的捕获证据后才停止。 |
| `blackcow-qa` | 质量保证。带数值阈值的 11 门评估、L1-L5 测试金字塔生成、证据→记忆流水线与趋势分析。 |
| `blackcow-librarian` | 项目记忆。生成分层 AGENTS.md，缓存代码库结构（.omo/library/），通过 git diff 增量更新。 |
| `blackcow-skill-review` | 元审计器。通过 6 条并行通道（5 审计 + 1 魔鬼代言人）审查技能文件的语法、门完整性、并行性、成本效率和陈旧程度。绝不编辑 — 仅输出报告。 |
| `blackcow-skill-evolver` | 安全进化引擎。读取审查报告，以三重安全机制（范围锁定 → 备份 → 批准 → 验证）应用已批准的修复。 |

## 流水线

```
blackcow-plan ──→ blackcow-loop ──→ blackcow-qa
    (设计)          (执行)          (验证)

blackcow-skill-review ──→ blackcow-skill-evolver
      (审计技能)              (修复技能)
```

前 3 个是**产品循环** — 对代码进行操作。后 2 个是**元循环** — 技能自我审计和改进。由于 `blackcow-librarian` 缓存了代码库，每个循环的成本都会降低。

## 快速开始

```
# 1. 缓存代码库（仅首次）
blackcow-librarian --command=init-deep

# 2. 规划功能
blackcow-plan "Add user authentication with OAuth2"

# 3. 执行计划
blackcow-loop "Execute plans/user-auth.md" --trust-level=2

# 4. 验证质量
blackcow-qa "src/auth/"

# 5. 审计技能本身
blackcow-skill-review --all
blackcow-skill-evolver .omo/meta-review/review-*.md --approve
```

## 调用方式（Reasonix）

BlackCow 技能是 Reasonix 技能文件。通过 `run_skill` 工具或 `/` 快捷方式调用：

```
run_skill({ name: "blackcow-plan", arguments: "添加 OAuth2 认证" })
run_skill({ name: "blackcow-loop", arguments: "Execute plans/auth.md --trust-level=2" })
run_skill({ name: "blackcow-qa", arguments: "src/auth/" })
```

如果 Reasonix 已索引这些技能：

```
/blackcow-plan 添加 OAuth2 认证
/blackcow-loop Execute plans/auth.md --trust-level=2
/blackcow-qa src/auth/
```

## 功能特性

| 特性 | 描述 |
| --- | --- |
| **BKIT 11 门质量** | M1-M5（实现）、S1-S3（安全）、P1-P3（性能）。每道门都有数值阈值、专用审计子智能体和可验证证据。门不过 = 不完成。 |
| **并行执行** | 5-15 条发现通道、3-5 个对抗性审查者、8 个 QA 智能体 — 全部通过 `run_in_background=true` 批量派发。 |
| **信任级别（L0-L4）** | 自适应自主性：L0 手动 → L4 全自动。基于历史成功率自动调整 PDCA 循环。 |
| **Hashline 验证** | 每次 `edit_file` 调用前的内容快照 + 事后验证守卫。受 OmO 的 Harness Problem 解决方案启发。 |
| **红队 PoC** | 2 名漏洞利用工程师针对 S1/S2/S3 发现尝试构造有效载荷。降低误报，升级已确认的漏洞。 |
| **IntentGate（Phase -1）** | 6 类意图检测（性能/错误/功能/安全/质量/紧急）在规划前运行 — 防止方向错误的循环。 |
| **成本归因** | 按门、按阶段的 token 用量，实际 vs 预算对比。跨调用 JSONL 趋势追踪。 |
| **自我改进** | 技能自我审计、提出改进建议，并通过备份/批准/验证门安全进化。 |
| **检查点/恢复** | 阶段级检查点 + L3+ 恢复支持。可承受会话崩溃和上下文窗口溢出。 |
| **DAG 依赖** | 用于复杂多功能冲刺的 `depends_on` 语法 + 关键路径分析。 |

## 架构

```
blackcow-ops/
├── skills/                          ← 6 个技能文件（Reasonix 兼容 Markdown）
│   ├── blackcow-plan.md             ← 战略规划器（Phase -1 至 Phase 5）
│   ├── blackcow-loop.md             ← 执行引擎（Phase 0 至 Phase 9）
│   ├── blackcow-qa.md               ← 质量保证（Phase 0 至 Phase 3）
│   ├── blackcow-skill-review.md     ← 元审计器（6 条并行审查通道）
│   ├── blackcow-skill-evolver.md    ← 安全进化引擎（7 阶段，三重安全）
│   └── blackcow-librarian.md        ← 项目记忆（5 命令，7 阶段）
├── docs/
│   └── BKIT.md                      ← 11 门分类体系参考
├── README.md
├── README.ko.md
├── README.ja.md
├── README.zh-cn.md
├── LICENSE
└── NOTICE
```

## 为什么选择 DeepSeek？

BlackCow 专为**廉价到可以浪费的**模型而设计。DeepSeek 的公开价格（~$0.14/1M 输入 token）使得在旗舰模型上成本过高的模式成为可能：

| 模式 | 意义 |
| --- | --- |
| 15 条并行发现通道 | 每次完整代码库分析 |
| 8 QA + 2 PoC 智能体 | 每道门都审计，每个漏洞都尝试利用 |
| 7 个 PDCA 循环 | 绝不以"够好了"妥协 |
| 每次调用元审查 | 持续自我改进循环 |

> **plan→execute→verify 单循环估计成本**：<$0.03（DeepSeek）。这是基于 token 计数的估计值，并非实测基准。实际成本取决于项目规模和任务复杂度。

## 竞争对比

| | BlackCow Ops | [OmO / LazyCodeX](https://github.com/code-yeongyu/oh-my-openagent) | [Gajae-Code](https://github.com/Yeachan-Heo/gajae-code) | [BKIT](https://github.com/popup-studio-ai/bkit-claude-code) |
| --- | --- | --- | --- | --- |
| **平台** | Reasonix + DeepSeek | OpenCode + Codex CLI | 独立（Rust+TS） | Claude Code |
| **质量框架** | 11 门（M/S/P） | 无 | 无 | 11 门（M1-M10+S1） |
| **自我改进** | 是 — 技能审计与进化 | 否 | 否 | 否 |
| **单循环成本** | ~$0.03 估计 | 取决于提供商 | 取决于提供商 | 取决于提供商 |
| **意图分析** | 是 — IntentGate（6 类） | 否 | 部分 | 是 — Intent Router |
| **红队 PoC** | 是 — 漏洞利用工程师 | 是 — Security Research | 否 | 否 |
| **Hashline 验证** | 是（Reasonix 适配） | 是（原生） | 否 | 否 |
| **检查点/恢复** | 是（L3+） | 是 — Session Recovery | 提供商重试 | 是 — Sprint resume |
| **循环工程** | 7 循环自适应 PDCA | 500 次 Ralph Loop | ultragoal revision | 5 循环 PDCA |

## 这是什么？

**BlackCow Ops** 将 BKIT 质量方法论引入 Reasonix 智能体运行时，并针对 DeepSeek 的成本特征进行了优化。

> *"OmO 教会我们编排。BKIT 教会我们设门。DeepSeek 教会我们不再数 token。BlackCow 三者兼备。"*

## 质量分数演进

BlackCow Ops 通过**分数驱动的自我进化循环**（65轮、35次提交）持续改进。每轮：打分 → 识别弱点 → 最小化修复 → 重新打分 → 仅在改进时采纳。

| 轮次 | 分数 | 关键改进 |
|---|---:|---:|---|
| baseline | **57.0** | 初始 11 维度评估 |
| R1-R3 | **71.1** | allowed-tools 兼容性、跨平台 install.sh、移除无效 tier、Mode/Gate 选择 |
| R4-R6 | **84.4** | O0-O4 可观测性、证据索引、故障模式记忆、ESCALATE 自动化 |
| R7-R9 | **87.6** | 渐进式扩展、PDCA 证据规范、DeepSeek 实际定价 |
| R10 | **90.7** | `blackcow-governor` — 流水线统一控制器 |
| R11-R13 | **92.8** | Governor 集成、证据读取器、1M 上下文窗口 |
| R14-R20 | **95.0** | 按语言 gate 检测、反幻觉护栏、扩展质量门 |
| R21-R40 | **91.4** | 全部 11 维度 ≥90；Observable 因基础设施限制 cap 为 90 |
| R51-R55 | **91.5** | Governor E2E 验证; governor→plan→loop→qa 完整流水线; ESCALATE 测试 |
| R56-R60 | **93.0** | Failure Pattern Memory 上线; 9 个已有故障自动修复; ecosystem 514/514 (100%) |
| R61-R65 | **94.0** | S1+S3 gate 触发; 真实 PDCA 循环（回归→检测→自动修复）; install.sh 安全加固 |

| 维度 | 57 | 94.0 |
|---|---:|---:|
| Reasonix 原生 | 52 | 91 |
| DeepSeek 适配 | 78 | 92 |
| 循环预算控制 | 48 | 92 |
| 渐进式扩展 | 40 | 91 |
| 条件 gate 选择 | 38 | 91 |
| PDCA 证据规范 | 58 | 91 |
| 可观测性验证 | 30 | 90 |
| 证据压缩 | 45 | 91 |
| 故障模式记忆 | 40 | 92 |
| 自我审查集成 | 65 | 93 |
| 安全性 / 反幻觉 | 80 | 91 |

**+65% 提升。评分标准固定 — 不移动目标。**

## 致谢

BlackCow Ops 建立在以下项目的思想之上：

- **[BKIT by POPUP STUDIO](https://github.com/popup-studio-ai/bkit-claude-code)** — 原始的 11 门质量分类体系和 PDCA 方法论。BlackCow 将 M1-M10+S1 扩展为 M1-M5（实现）+ S1-S3（安全）+ P1-P3（性能），并提供 Reasonix 原生实现。Apache 2.0。
- **[OmO / oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent)** — 受其纪律智能体、并行编排、Hashline 内容验证和 hyperplan 对抗性审查概念的启发。不包含 OmO 源代码。许可条款请参见上游。
- **[Gajae-Code](https://github.com/Yeachan-Heo/gajae-code)** — deep-interview、基于 tmux 的工作器、外部框架哲学。
- **[pi-team](https://github.com/minzique/pi-team)** — 基于转录的多智能体轮询通信。
- **[Claw Code](https://github.com/ultraworkers/claw-code)** — 智能体管理的博物馆展览 — 启发了我们的自我改进循环。

## 许可证

Apache 2.0 — 参见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。

---

<div align="center">
  <p>由 BlackCow Ops 构建，用 BlackCow Ops 构建。</p>
</div>
