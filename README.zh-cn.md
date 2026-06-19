<div align="center">
  <h1>BlackCow Ops</h1>
  <p><strong>为 Reasonix + DeepSeek 打造的 8 个自我改进工作流技能。</strong></p>
  <p>
    <a href="#安装">安装</a> · <a href="#快速开始">快速开始</a> ·
    <a href="README.md">English</a> · <a href="README.ko.md">한국어</a> · <a href="README.ja.md">日本語</a>
  </p>
</div>

---

## 这是什么

BlackCow Ops 是一套 8 个 Reasonix 技能，构成编码任务的 **govern → plan → execute → verify → evolve** 流水线，并提供显式本地 swarm 控制平面。强制执行 BKIT 11 门质量体系，并针对 DeepSeek 的成本优势进行了优化。修复拼写错误约 $0.001，多文件功能约 $0.03。

**诚实分数：90.6/100**（11 维度平均）。评分标准固定 — 不移动目标。

> 流程无法提升模型的上限，只能照亮通往上限的道路。当触及上限时，BlackCow 会升级而非伪装。

## 技能

| 技能 | 角色 |
|---|---|
| `blackcow-governor` | 预检控制器。在工作开始前选择模式、门、可观测级别和 PDCA 预算。 |
| `blackcow-plan` | 战略设计器。渐进式扩展、架构选项、决策完备的计划。 |
| `blackcow-loop` | 执行引擎。TRY(2-3分钟)+STANDARD/FULL。PDCA、Findings Gate、Visual Review(codex)、O0-O4 验证。 |
| `blackcow-swarm` | 显式 DeepSeek/Reasonix swarm 控制平面。估算、规划、运行、恢复、取消并清理本地并行 worker。 |
| `blackcow-qa` | 质量保证。基于数值阈值的条件式 11 门评估。 |
| `blackcow-librarian` | 项目记忆。结构缓存、故障模式记忆、趋势分析。 |
| `blackcow-skill-review` | 元审计。对技能本身进行趋势跟踪和陈旧性检测。 |
| `blackcow-skill-evolver` | 安全进化引擎。通过三重安全门应用经审查的变更。 |

## 安装

```bash
git clone https://github.com/blackcowmaster/blackcow-ops.git
cp blackcow-ops/skills/*.md ~/.reasonix/skills/
```

重启 Reasonix 后，8 个技能全局可用。

## 快速开始

```
# 缓存代码库（仅首次）
blackcow-librarian --command=init-deep

# 任务管控（模式、门、预算）
blackcow-governor "添加 OAuth2 认证"

# 实现计划
blackcow-plan "添加 OAuth2 认证" --govern=oauth

# 执行计划
blackcow-loop "Execute plans/oauth.md" --mode=standard --trust-level=2

# 质量验证
blackcow-qa "src/auth/" --gates=auto
```

通过 `run_skill` 或 `/` 快捷键调用：`/blackcow-plan 添加 OAuth2 认证`

## 核心优势

- **从 PRD 到实现。** 读取规格、推断技术栈、分解为独立单元并分派并行计划。决定之前先询问 — 绝不替用户擅自选择技术栈。
- **DeepSeek 成本优化。** 5 种执行模式从 $0.001（拼写修复）扩展到 ~$0.10（完整安全审计）。渐进式扩展仅在需要时增加成本。
- **11 门质量体系。** M1-M5（实现）、S1-S3（安全）、P1-P3（性能）。每道门都有数值阈值，通过需提供证据。
- **Findings Gate。** 审查中发现的问题会被追踪，必须在完成前解决。不默许已知缺陷。
- **故障模式记忆。** 历史故障按有效性评分记录。高有效性修复自动应用，低有效性模式触发升级。
- **视觉审查。** DeepSeek V4 无原生视觉。安装 codex CLI 时通过 `codex exec --image` 分析截图。无 codex 时自动跳过。
- **子智能体 O4 验证。** Playwright CLI 浏览器截图。
- **CLI 桥接。** 子智能体可通过 `run_command` 使用任意 CLI 工具（`supabase`、`aws`、`firebase`、`docker`）。需认证的工具要求用户确认。
- **自我审计。** 每个技能都有结构化的自我审计清单。技能自我审查、自我进化。

## 架构

```
blackcow-governor ──→ blackcow-plan ──→ blackcow-loop ──→ blackcow-qa
   (预检)             (设计)          (执行)          (验证)
                         │
                         └──→ blackcow-swarm
                              (显式并行 worker)

blackcow-skill-review ──→ blackcow-skill-evolver
      (审计技能)              (修复技能)

                    blackcow-librarian
               (缓存 + 记忆 + 趋势)
```

## 为什么选择 DeepSeek

BlackCow 为足够便宜以至于可以浪费的模型而设计。DeepSeek 的价格（flash ~$0.14/1M 输入）使得在其他地方成本高昂的模式成为可能：15 条并行发现通道、8 个 QA 智能体、7 个 PDCA 循环。

## 参考

- **[BKIT](https://github.com/popup-studio-ai/bkit-claude-code)** — 11 门质量体系。Apache 2.0。

## 许可证

Apache 2.0 — [LICENSE](LICENSE) · [NOTICE](NOTICE)

---

<div align="center"><p>由 BlackCow Ops 构建，由 BlackCow Ops 创造。</p></div>
