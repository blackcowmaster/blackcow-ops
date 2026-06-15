<div align="center">
  <h1>BlackCow Ops</h1>

  <p><strong>基于 BKIT 的智能体工程框架。</strong><br />
  Reasonix + DeepSeek 原生。</p>

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
> **BlackCow Ops 由 7 个自我改进的 Reasonix 技能**组成，形成完整的 **govern → plan → execute → verify → evolve** 流水线。强制执行 BKIT 11 门质量体系（M1-M5 实现，S1-S3 安全，P1-P3 性能），针对 DeepSeek 的成本优势（~$0.14/1M flash，~$0.435/1M pro）进行了优化。FAST 模式修复拼写错误约 $0.001；FULL 模式多文件功能约 $0.03。

## 项目状态

| 指标 | 分数 |
| --- | --- |
| **BlackCow Ops 分数** | **96.2 / 100** |
| **目标** | ~~突破 90 分~~ ✅ 已达成！ |

> 11 个质量维度的综合指标。详见[质量分数演进](#质量分数演进)。

## 安装

```bash
git clone https://github.com/blackcowmaster/blackcow-ops.git
cp blackcow-ops/skills/*.md ~/.reasonix/skills/
```

重启 Reasonix 后，7 个 `blackcow-*` 技能全局可用。

## 适用场景

| 场景 | 建议 |
| --- | --- |
| **Reasonix + DeepSeek** | **即用。** 已为 DeepSeek 优化，7 个技能零配置使用。 |
| **Reasonix + 其他模型** | **未测试。** 需针对不同提供商调整。修改 YAML 中的 `model_tiers`。 |
| **Claude Code、Codex CLI 等** | **需要移植。** BKIT 方法论不依赖特定框架。需重写工具调用。 |
| **仅需 11 门方法论** | **免费。** 参阅 `docs/BKIT.md`。Apache 2.0。 |

## 命令

| 命令 | 说明 |
| --- | --- |
| `blackcow-governor` | 流水线控制器。模式/门/O 级别/PDCA 预算选择。加载故障模式记忆和 ROI 历史。 |
| `blackcow-plan` | 战略设计器。3 阶段渐进式扩展，10 条发现通道，3 种架构选项。 |
| `blackcow-loop` | 执行引擎。5 种模式，原生 review+security_review，Phase 2.2 Root Cause，Findings Gate，O0-O4 验证。 |
| `blackcow-qa` | 质量保证。条件门选择，11 门评估，L1-L5 测试金字塔。 |
| `blackcow-librarian` | 项目记忆。7 个命令，结构缓存，故障模式记忆，趋势分析。 |
| `blackcow-skill-review` | 元审计。趋势跟踪，陈旧性检测。⚠️ 分数可能波动 — 仅用于趋势分析。 |
| `blackcow-skill-evolver` | 安全进化引擎。三重安全（范围锁定→备份→批准→验证）。 |

## 流水线

```
blackcow-governor ──→ blackcow-plan ──→ blackcow-loop ──→ blackcow-qa
   (预检)             (设计)          (执行)          (验证)

blackcow-skill-review ──→ blackcow-skill-evolver
      (审计技能)              (修复技能)

                    blackcow-librarian
               (缓存 + 记忆 + 趋势)
```

## 快速开始

```
# 1. 缓存代码库（仅首次）
blackcow-librarian --command=init-deep

# 2. 预检
blackcow-governor "添加 OAuth2 用户认证"

# 3. 功能设计
blackcow-plan "添加 OAuth2 用户认证" --govern=auth

# 4. 执行计划
blackcow-loop "Execute plans/user-auth.md" --mode=standard --trust-level=2

# 5. 质量验证
blackcow-qa "src/auth/" --gates=auto
```

## Reasonix 中调用

```
run_skill({ name: "blackcow-plan", arguments: "添加 OAuth2 认证" })
```

或使用斜杠快捷键：`/blackcow-plan 添加 OAuth2 认证`

## 主要功能

| 功能 | 说明 |
| --- | --- |
| **BKIT 11 门质量** | M1-M5（实现），S1-S3（安全），P1-P3（性能）。全部有数值阈值和证据要求。 |
| **5 种执行模式** | FAST → STANDARD → FULL → SIEGE → ESCALATE。按模式分配通道/门/PDCA 预算。 |
| **条件门选择** | 通过 git diff 信号 + 按语言模式自动选择需要的门。 |
| **渐进式扩展** | 3 阶段不确定性驱动的发现。从最便宜的开始，仅在需要时扩展。 |
| **O0-O4 可观测验证** | O0（无）→ O4（浏览器自动化）。自动检测可用工具，诚实设限。 |
| **Findings Gate** | 追踪 PDCA 中发现的所有缺口。未解决的 finding 阻止完成。吸收自 FableCodex。 |
| **原生工具集成** | Loop Phase 5 使用 Reasonix `review` + `security_review` — 更快、更准、更便宜。 |
| **PDCA 证据规范** | 硬停止规则：无新证据→停止，同一失败×2→ESCALATE。 |

## 架构

```
blackcow-ops/
├── skills/                          ← 7 个技能 + 安装脚本
│   ├── blackcow-governor.md         ← 流水线控制器
│   ├── blackcow-plan.md             ← 战略设计器
│   ├── blackcow-loop.md             ← 执行引擎
│   ├── blackcow-qa.md               ← 质量保证
│   ├── blackcow-librarian.md        ← 项目记忆
│   ├── blackcow-skill-review.md     ← 元审计
│   ├── blackcow-skill-evolver.md    ← 安全进化引擎
│   └── install.sh                   ← 跨平台安装
├── docs/BKIT.md                     ← 11 门参考
├── README.md (EN/KO/JA/ZH-CN)
├── LICENSE
└── NOTICE
```

## 为什么选择 DeepSeek？

BlackCow 专为**足够便宜以至于可以浪费**的模型而设计。

| 模式 | 意义 |
| --- | --- |
| 15 条并行发现通道 | 每次完整分析代码库 |
| 8 QA + 2 PoC 智能体 | 审计所有门，尝试所有漏洞 |
| 7 个 PDCA 循环 | 绝不满足于"够好" |
| 每次调用元审查 | 持续自我改进循环 |

> **plan→execute→verify 单循环估算成本**：$0.03 以下（DeepSeek）。基于 token 计数的估算。

## 质量分数演进

**分数驱动的自我进化循环**（73 轮，38 次提交）。每轮：打分 → 识别弱点 → 最小修复 → 重新打分 → 仅在改进时采纳。

| 轮次 | 分数 | 关键改进 |
|---|---:|---:|---|
| baseline | **57.0** | 初始 11 维度评估 |
| R1-R3 | **71.1** | allowed-tools 兼容性，跨平台 install.sh |
| R4-R6 | **84.4** | O0-O4 可观测性，证据索引 |
| R10 | **90.7** | `blackcow-governor` — 流水线控制器 |
| R21-R40 | **91.4** | 全部 11 维度 ≥90 |
| R51-R55 | **91.5** | Governor E2E 验证，完整流水线 |
| R56-R60 | **93.0** | Failure Pattern Memory 上线，9 个故障自动修复 |
| R61-R65 | **94.0** | S1+S3 门触发，真实 PDCA 循环 |
| R66-R70 | **95.5** | 7 智能体多领域，11/11 门全覆盖 |
| R71 | **96.0** | O4 可观测验证（puppeteer） |
| R72 | **96.2** | Findings Gate（FableCodex），TOCTOU 漏洞修复 |

| 维度 | 基线 (57) | 当前 (96.2) |
|---|---:|---:|---:|
| Reasonix 原生 | 52 | 91 |
| DeepSeek 适配 | 78 | 92 |
| 循环预算控制 | 48 | 92 |
| 渐进式扩展 | 40 | 91 |
| 条件门选择 | 38 | 91 |
| PDCA 证据规范 | 58 | 91 |
| 可观测验证 | 30 | 90 |
| 证据压缩 | 45 | 91 |
| 故障模式记忆 | 40 | 92 |
| 自我审查集成 | 65 | 93 |
| 安全性 / 反幻觉 | 80 | 91 |

**+69% 提升。评分标准固定 — 不移动目标。**

## 这是什么？

**BlackCow Ops** 将 BKIT 质量方法论引入 Reasonix 智能体运行时，并针对 DeepSeek 进行了优化。

> *"OmO 教会我们编排。BKIT 教会我们设门。DeepSeek 教会我们不再数 token。BlackCow 三者兼备。"*

## 致谢

- **[BKIT by POPUP STUDIO](https://github.com/popup-studio-ai/bkit-claude-code)** — 原始 11 门质量体系。Apache 2.0。
- **[OmO / oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent)** — 纪律智能体，并行编排。
- **[Gajae-Code](https://github.com/Yeachan-Heo/gajae-code)** — deep-interview，tmux 工作器。
- **[pi-team](https://github.com/minzique/pi-team)** — 多智能体轮转通信。
- **[Claw Code](https://github.com/ultraworkers/claw-code)** — 自我改进循环灵感。

## 许可证

Apache 2.0 — 参阅 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。

---

<div align="center">
  <p>由 BlackCow Ops 构建，由 BlackCow Ops 创造。</p>
</div>
