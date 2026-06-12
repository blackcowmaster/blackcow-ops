<div align="center">
  <h1>🐂 BlackCow Ops</h1>

  <p><strong>The agent engineering harness for Reasonix + DeepSeek.</strong><br />
  BKIT-inspired 11-gate quality. Self-improving skills. ~$0.005 per cycle.</p>

  <p>
    <a href="#-install">Install</a>
    ·
    <a href="#-quick-start">Quick Start</a>
    ·
    <a href="#-philosophy">Philosophy</a>
    ·
    <a href="README.ko.md">한국어</a>
  </p>
</div>

<hr />

> [!NOTE]
> **BlackCow Ops is a set of 6 self-improving Reasonix skills** that form a complete plan→execute→verify→evolve pipeline. It enforces BKIT — an 11-gate quality taxonomy with numeric thresholds — adapted and extended for DeepSeek's cost advantage.
>
> At DeepSeek pricing (~$0.14/1M input), running 15 parallel discovery lanes + 8 adversarial QA agents + 7 PDCA cycles costs less than **$0.03 total**. The equivalent pipeline on GPT-5 would cost $3-5.

## 🚀 Install

```bash
# Clone into your Reasonix skills directory
git clone https://github.com/blackcowmaster/blackcow-ops.git
cp blackcow-ops/skills/*.md ~/.reasonix/skills/
```

Restart Reasonix. The 6 `blackcow-*` skills are now available globally.

## ⚡ Commands

| Command | What it does |
| --- | --- |
| `blackcow-plan` | Strategic planner. Analyzes codebase from 10 angles, proposes 3 architecture options, writes a decision-complete plan. Never writes product code. |
| `blackcow-loop` | Execution engine. TDD + Hashline content verification + PDCA iterator + 10-agent adversarial QA. Stops only when all 11 gates produce captured evidence above threshold. |
| `blackcow-qa` | Quality assurance. 11-gate evaluation with numeric thresholds, L1-L5 test pyramid generation, evidence→memory pipeline with trend analysis. |
| `blackcow-librarian` | Project memory. Generates hierarchical AGENTS.md, caches codebase structure (.omo/library/), incremental update via git diff. |
| `blackcow-skill-review` | Meta-auditor. Reviews skill files for syntax, gate completeness, parallelism, cost efficiency, and staleness. 5 parallel discovery lanes. Never edits — only reports. |
| `blackcow-skill-evolver` | Safe evolution engine. Reads review reports, applies approved fixes with triple safety (scope-lock → backup → approve → validate). |

## 🔄 The Pipeline

```
blackcow-plan ──→ blackcow-loop ──→ blackcow-qa
    (design)        (execute)        (verify)

blackcow-skill-review ──→ blackcow-skill-evolver
      (audit skills)          (fix skills)
```

The first 3 are the **product cycle** — they work on your code. The last 2 are the **meta cycle** — the skills audit and improve themselves. Every cycle gets cheaper because `blackcow-librarian` caches the codebase.

## 🎯 Quick Start

```
# 1. Cache your codebase (first time only)
blackcow-librarian --command=init-deep

# 2. Plan a feature
blackcow-plan "Add user authentication with OAuth2"

# 3. Execute the plan
blackcow-loop "Execute plans/user-auth.md" --trust-level=2

# 4. Verify quality
blackcow-qa "src/auth/"

# 5. Audit the skills themselves
blackcow-skill-review --all
blackcow-skill-evolver .omo/meta-review/review-*.md --approve
```

## 🧩 What you get

| Feature | Description |
| --- | --- |
| 🎯 **BKIT 11-Gate Quality** | M1-M5 (Implementation), S1-S3 (Security), P1-P3 (Performance). Every gate has a numeric threshold, a dedicated audit subagent, and verifiable evidence. No gate = no DONE. |
| 🔀 **Parallel Execution** | 5-15 discovery lanes, 3-5 adversarial reviewers, 8 QA agents — all batch-dispatched with `run_in_background=true`. |
| 🎛️ **Trust Level (L0-L4)** | Adaptive autonomy: L0 manual → L4 full-auto. PDCA cycles auto-adjust based on historical success rate. |
| 🛡️ **Hashline Verification** | Pre-edit content snapshots + post-edit verification guard every `edit_file` call. Inspired by OmO's Harness Problem solution. |
| 🔴 **Red Team PoC** | 2 exploit engineers attempt working payloads against S1/S2/S3 findings. Downgrades false positives, escalates confirmed exploits. |
| 🧠 **IntentGate (Phase -1)** | 6-class intent detection (Performance/Bug/Feature/Security/Quality/Emergency) runs BEFORE any planning — prevents misdirected cycles. |
| 📊 **Cost Attribution** | Per-gate, per-phase token accounting with actual vs budget comparison. JSONL trend tracking across invocations. |
| 🔄 **Self-Improvement** | Skills audit themselves, propose improvements, and safely evolve with backup/approval/validation gates. |
| 💾 **Checkpoint/Resume** | Phase-level checkpoint with resume support (L3+). Survives session crashes and context window overflows. |
| 🧹 **DAG Dependencies** | `depends_on` syntax with critical path analysis for complex multi-feature sprints. |

## 🏗️ Architecture

```
blackcow-ops/
├── skills/                          ← The 6 skill files (Reasonix-compatible Markdown)
│   ├── blackcow-plan.md             ← Strategic planner (Phase -1 to Phase 5)
│   ├── blackcow-loop.md             ← Execution engine (Phase 0 to Phase 9)
│   ├── blackcow-qa.md               ← Quality assurance (Phase 0 to Phase 3)
│   ├── blackcow-skill-review.md     ← Meta-auditor (5 parallel review lanes)
│   ├── blackcow-skill-evolver.md    ← Safe evolution engine (7 phases, triple safety)
│   └── blackcow-librarian.md        ← Project memory (5 commands, 7 phases)
├── docs/
│   └── BKIT.md                      ← 11-gate taxonomy reference
├── README.md
├── README.ko.md
├── LICENSE
└── NOTICE
```

## 🧠 Why DeepSeek?

BlackCow was designed from the ground up for models that are **cheap enough to be wasteful**. DeepSeek at ~$0.14/1M input tokens is ~100x cheaper than GPT-5. This changes what's economically viable:

| Pattern | GPT-5 Cost | DeepSeek Cost | BlackCow Strategy |
| --- | --- | --- | --- |
| 15 discovery lanes | ~$1.50 | ~$0.002 | Always max lanes for XL |
| 8 QA agents + 2 PoC | ~$1.00 | ~$0.001 | Run every gate, every time |
| 7 PDCA cycles | ~$3.50 | ~$0.005 | Never settle for "good enough" |
| Meta-review every invocation | ~$0.75 | ~$0.001 | Continuous self-improvement |

**This is the core insight**: when quality gates cost fractions of a cent, you run them all. You don't optimize for token count — you optimize for gate pass rate.

## 🆚 Competitive Landscape

| | BlackCow Ops | [OmO / LazyCodeX](https://github.com/code-yeongyu/oh-my-openagent) | [Gajae-Code](https://github.com/Yeachan-Heo/gajae-code) | [BKIT](https://github.com/popup-studio-ai/bkit-claude-code) |
| --- | --- | --- | --- | --- |
| **Platform** | Reasonix + DeepSeek | OpenCode + Codex CLI | Standalone (Rust+TS) | Claude Code |
| **Quality Framework** | 11-Gate (M/S/P) | None | None | 11-Gate (M1-M10+S1) |
| **Self-Improvement** | ✅ Skills audit & evolve | ❌ | ❌ | ❌ |
| **Cost per Cycle** | ~$0.005 | ~$0.50+ | Provider-dependent | ~$0.50+ |
| **Intent Analysis** | ✅ IntentGate (6-class) | ❌ | Partial | ✅ Intent Router |
| **Red Team PoC** | ✅ Exploit engineers | ✅ Security Research | ❌ | ❌ |
| **Hashline Verification** | ✅ (Reasonix-adapted) | ✅ (Native) | ❌ | ❌ |
| **Checkpoint/Resume** | ✅ L3+ | ✅ Session Recovery | Provider retry | ✅ Sprint resume |

## 💤 What is this?

**BlackCow Ops** packages the BKIT quality methodology for the Reasonix agent runtime, optimized for DeepSeek's extreme cost advantage.

Think of it as: what if you took OmO's agent harness, added BKIT's quality gates, and tuned everything for a model where 15 parallel lanes cost less than a single GPT-5 inference? That's BlackCow.

> *"OmO taught us to orchestrate. BKIT taught us to gate. DeepSeek taught us to stop counting tokens. BlackCow does all three."*

## 🙏 Acknowledgments

BlackCow Ops builds on ideas from:

- **[BKIT by POPUP STUDIO](https://github.com/popup-studio-ai/bkit-claude-code)** — The original 11-gate quality taxonomy and PDCA methodology. BlackCow extends M1-M10+S1 into M1-M5 (Implementation) + S1-S3 (Security) + P1-P3 (Performance) with Reasonix-native implementations. Apache 2.0.
- **[OmO / oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent)** — Discipline agents, parallel orchestration, Hashline content verification, hyperplan adversarial review.
- **[Gajae-Code](https://github.com/Yeachan-Heo/gajae-code)** — deep-interview, tmux-backed workers, external harness philosophy.
- **[pi-team](https://github.com/minzique/pi-team)** — Transcript-based multi-agent round-robin communication.
- **[Claw Code](https://github.com/ultraworkers/claw-code)** — The agent-managed museum exhibit that inspired our self-improvement loop.

## 📄 License

Apache 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).

---

<div align="center">
  <p>Built with BlackCow Ops, by BlackCow Ops. 🐂</p>
</div>
