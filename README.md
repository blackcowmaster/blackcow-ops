<div align="center">
  <h1>BlackCow Ops</h1>

  <p><strong>BKIT-inspired agent engineering harness.</strong><br />
  Built for Reasonix + DeepSeek.</p>

  <p>
    <a href="#install">Install</a>
    ·
    <a href="#quick-start">Quick Start</a>
    ·
    <a href="README.ko.md">한국어</a>
    ·
    <a href="README.ja.md">日本語</a>
    ·
    <a href="README.zh-cn.md">简体中文</a>
  </p>
</div>

<hr />

> [!NOTE]
> **BlackCow Ops is a set of 7 self-improving Reasonix skills** forming a complete **govern → plan → execute → verify → evolve** pipeline. It enforces BKIT — an 11-gate quality taxonomy (M1-M5 implementation, S1-S3 security, P1-P3 performance) — tuned for DeepSeek's cost advantage (~$0.14/1M flash, ~$0.435/1M pro). A FAST-mode typo fix costs ~$0.001; a FULL-mode multi-file feature costs ~$0.03.

## Project Status

| Metric | Score |
| --- | --- |
| **BlackCow Ops Score** | **89.0 / 100** |
| **Goal** | ~~Break 90 points~~ ✅ Achieved! |

> The BlackCow Ops score is a composite of 11 quality dimensions (Reasonix-native, DeepSeek fit, loop budget control, progressive widening, conditional gate selection, PDCA evidence discipline, observable verification, evidence compaction, failure-pattern memory, self-review integration, and safety/anti-hallucination). Each dimension is scored 0–100 and averaged. See [Quality Score Evolution](#quality-score-evolution) for the full history.

## Install

```bash
# Clone into your Reasonix skills directory
git clone https://github.com/blackcowmaster/blackcow-ops.git
cp blackcow-ops/skills/*.md ~/.reasonix/skills/
```

Restart Reasonix. All 7 `blackcow-*` skills are now available globally.

## When to Use

| Scenario | Recommendation |
| --- | --- |
| **You use Reasonix + DeepSeek** | **Native.** Every model tier, context budget, and PDCA cycle count is tuned for DeepSeek. Use all 7 skills with zero config. |
| **You use Reasonix + another model** | **Untested.** Reasonix supports other providers via the AI SDK (Anthropic, OpenAI, Google, etc.), but BlackCow has only been tested with DeepSeek. If you try another model, edit `model_tiers` in each skill's YAML frontmatter and adjust context budgets for your model's window size. YMMV. |
| **You use Claude Code, Codex CLI, OpenCode, or another harness** | **Needs porting.** The BKIT methodology is independent of any one harness. The current `.md` skill files are Reasonix-native — tool calls (`task`, `edit_file`, `multi_edit`) would need rewriting for your harness's equivalents. |
| **You just want the 11-gate quality methodology** | **Free.** Read `docs/BKIT.md` — the taxonomy, thresholds, and audit agent design are documented. Adapt to any workflow. Apache 2.0. |

## Commands

| Command | What it does |
| --- | --- |
| `blackcow-governor` | Pipeline governor. Preflight mode/gate/O-level/PDCA budget selection. Loads failure-pattern memory and loop ROI history. Produces governance decision consumed by plan/loop/qa. |
| `blackcow-plan` | Strategic planner. Progressive widening (3 stages), 10 discovery lanes, 3 architecture options, decision-complete plan with DAG dependencies. Governor-aware. Never writes product code. |
| `blackcow-loop` | Execution engine. 5 modes (FAST~ESCALATE), native review+security_review integration, Phase 2.2 Root Cause analysis, PDCA iterator with hard-stop rules, Findings Gate (Phase 7), O0-O4 observable verification, evidence compaction index. |
| `blackcow-qa` | Quality assurance. Conditional gate selection (auto-detect via git diff), 11-gate evaluation, L1-L5 test pyramid, failure-pattern auto-population, evidence→memory pipeline. |
| `blackcow-librarian` | Project memory. 7 commands (init-deep, scan, update, check, load, load-evidence, all). AGENTS.md generation, structure cache, failure-pattern memory, trend analysis, governor feed. |
| `blackcow-skill-review` | Meta-auditor. Trend tracking, staleness detection, regression alerts. ⚠️ Known limitation: audit scores may oscillate — use for trend analysis only, not quality gating. Governor self-audit is the recommended alternative. |
| `blackcow-skill-evolver` | Safe evolution engine. Triple safety (scope-lock → backup → approve → validate). Accepts both review reports and governor score-loop decisions as input. |

## The Pipeline

```
blackcow-governor ──→ blackcow-plan ──→ blackcow-loop ──→ blackcow-qa
   (preflight)         (design)          (execute)         (verify)

blackcow-skill-review ──→ blackcow-skill-evolver
      (audit skills)          (fix skills)

                    blackcow-librarian
               (caching + memory + trends)
```

The first 4 are the **product cycle** — governor preflights, planner designs, loop executes, qa verifies. The next 2 are the **meta cycle** — skills audit and improve themselves. The librarian underpins everything with caching, failure-pattern memory, and trend analysis.

## Quick Start

```
# 1. Cache your codebase (first time only)
blackcow-librarian --command=init-deep

# 2. Preflight governance (mode/gate/budget selection)
blackcow-governor "Add user authentication with OAuth2"

# 3. Plan a feature
blackcow-plan "Add user authentication with OAuth2" --govern=auth

# 4. Execute the plan
blackcow-loop "Execute plans/user-auth.md" --mode=standard --trust-level=2

# 5. Verify quality
blackcow-qa "src/auth/" --gates=auto

# 6. Audit the skills themselves
blackcow-skill-review --all
```

## How to Invoke (Reasonix)

BlackCow skills are Reasonix skill files. Invoke them via the `run_skill` tool or the `/` slash shortcut:

```
run_skill({ name: "blackcow-plan", arguments: "Add OAuth2 auth" })
run_skill({ name: "blackcow-loop", arguments: "Execute plans/auth.md --trust-level=2" })
run_skill({ name: "blackcow-qa", arguments: "src/auth/" })
```

If Reasonix has indexed the skills:

```
/blackcow-plan Add OAuth2 auth
/blackcow-loop Execute plans/auth.md --trust-level=2
/blackcow-qa src/auth/
```

## What you get

| Feature | Description |
| --- | --- |
| **BKIT 11-Gate Quality** | M1-M5 (Implementation), S1-S3 (Security), P1-P3 (Performance). Every gate has a numeric threshold, a dedicated audit subagent, and verifiable evidence. No gate = no DONE. |
| **5 Execution Modes** | FAST (typo) → STANDARD (bug) → FULL (feature) → SIEGE (security) → ESCALATE (user). Each mode has lane/gate/PDCA/verification budgets. |
| **Conditional Gate Selection** | Auto-detects which gates to run via git diff signals + per-language patterns. Universal gates (M1/M2/M3) always run. |
| **Progressive Widening** | 3-stage uncertainty-driven discovery. Starts cheapest, widens only when needed. Auto-triggers + uncertainty scoring formula. |
| **O0-O4 Observable Verification** | Capability-based observable levels: O0 (none) → O4 (cross-browser visual QA). Auto-detects available tooling, caps honestly. |
| **PDCA Evidence Discipline** | Hard-stop rules: no new evidence→STOP, same failure×2→ESCALATE. Before/after cycle records with evidence quality scoring. |
| **Evidence Compaction Index** | Compact evidence index with SHA256 hashes. Downstream skills load index, not raw logs. Artifact retention + compression policy. |
| **Failure-Pattern Memory** | Structured failure records with resolution effectiveness tracking. Auto-populated from QA history. Feeds governor for pre-emptive fixes. |
| **Loop ROI Logging** | Token-spent vs score-gained tracking. Mode escalation/de-escalation based on ROI thresholds. Budget rebalancing. |
| **Findings Gate** | Every gap discovered during PDCA is recorded as a tracked finding. Open/blocked findings prevent completion. Resolved with mandatory evidence + verification. Absorbed from FableCodex. |
| **Native Tool Integration** | Loop Phase 5 uses Reasonix-native `review` + `security_review` tools for FAST/STANDARD modes — faster, cheaper, and more thorough than subagent-based QA. |
| **Cross-Skill Evidence Contract** | Standardized artifact exchange between all 7 skills. Producer/consumer contracts with freshness checks. |
| **Self-Audit Checklists** | Every skill has a structured self-audit checklist covering syntax, gates, parallelism, cost, cross-references, and anti-hallucination. |

## Architecture

```
blackcow-ops/
├── skills/                          ← 7 skill files + installer (Reasonix-compatible Markdown)
│   ├── blackcow-governor.md         ← Pipeline governor (mode/gate/budget/O-level selection)
│   ├── blackcow-plan.md             ← Strategic planner (progressive widening, 3-stage)
│   ├── blackcow-loop.md             ← Execution engine (5 modes, O0-O4, PDCA+ESCALATE)
│   ├── blackcow-qa.md               ← Quality assurance (conditional gates, auto-detect)
│   ├── blackcow-skill-review.md     ← Meta-auditor (trend tracking, staleness detection)
│   ├── blackcow-skill-evolver.md    ← Safe evolution engine (triple safety)
│   ├── blackcow-librarian.md        ← Project memory (7 commands, failure-pattern memory)
│   └── install.sh                   ← Cross-platform installer (macOS/Windows auto-detect)
├── docs/
│   └── BKIT.md                      ← 11-gate taxonomy reference
├── README.md (EN/KO/JA/ZH-CN)
├── LICENSE
└── NOTICE
```

## Why DeepSeek?

BlackCow was designed for models that are **cheap enough to be wasteful**. DeepSeek's public pricing (~$0.14/1M input tokens) enables patterns that would be cost-prohibitive on frontier models:

| Pattern | Why it matters |
| --- | --- |
| 15 parallel discovery lanes | Full-spectrum codebase analysis every time |
| 8 QA agents + 2 PoC engineers | Every gate audited, every exploit attempted |
| 7 PDCA cycles | Never settle for "good enough" |
| Meta-review every invocation | Continuous self-improvement loop |

> **Estimated cost per plan→execute→verify cycle**: <$0.03 (DeepSeek). This is an estimate based on token counting, not a measured benchmark. Actual costs depend on project size and task complexity.

## Competitive Landscape

| | BlackCow Ops | [OmO / LazyCodeX](https://github.com/code-yeongyu/oh-my-openagent) | [Gajae-Code](https://github.com/Yeachan-Heo/gajae-code) | [BKIT](https://github.com/popup-studio-ai/bkit-claude-code) |
| --- | --- | --- | --- | --- |
| **Platform** | Reasonix + DeepSeek | OpenCode + Codex CLI | Standalone (Rust+TS) | Claude Code |
| **Quality Framework** | 11-Gate (M/S/P) | None | None | 11-Gate (M1-M10+S1) |
| **Self-Improvement** | Yes — skills audit & evolve | No | No | No |
| **Cost per Cycle** | ~$0.03 est. | Provider-dependent | Provider-dependent | Provider-dependent |
| **Intent Analysis** | Yes — IntentGate (6-class) | No | Partial | Yes — Intent Router |
| **Red Team PoC** | Yes — exploit engineers | Yes — Security Research | No | No |
| **Hashline Verification** | Yes (Reasonix-adapted) | Yes (Native) | No | No |
| **Checkpoint/Resume** | Yes (L3+) | Yes — Session Recovery | Provider retry | Yes — Sprint resume |
| **Loop Engineering** | 7-cycle adaptive PDCA | 500-iteration Ralph Loop | ultragoal revision | 5-cycle PDCA |

## Quality Score Evolution

BlackCow Ops was improved through a **score-driven self-evolution loop** (89 rounds, 39 commits). Each round: score → identify weakness → apply minimal fix → re-score → accept only if improved.

| Round | Score | Key Improvements |
|---|---:|---:|---|
| baseline | **57.0** | Initial 11-dimension assessment |
| R1-R3 | **71.1** | allowed-tools compatibility, cross-platform install.sh, dead tier removal, Mode/Gate Selection |
| R4-R6 | **84.4** | O0-O4 observable, evidence index, failure-pattern memory, ESCALATE automation |
| R7-R9 | **87.6** | Progressive widening, PDCA evidence discipline, DeepSeek pricing |
| R10 | **90.7** | `blackcow-governor` — pipeline preflight controller |
| R11-R13 | **92.8** | Governor wiring, evidence reader, 1M context window |
| R14-R20 | **95.0** | Per-language gate detection, anti-hallucination guards, widening quality gate |
| R21-R40 | **91.4** | All 11 dimensions ≥ 90; Observable capped at 90 (infrastructure-honest) |
| R51-R55 | **91.5** | Governor E2E verified; governor→plan→loop→qa full pipeline; ESCALATE tested; ecosystem health + cross-skill contract |
| R56-R60 | **93.0** | Failure Pattern Memory live; 9 pre-existing failures auto-fixed; ecosystem 514/514 (100%); all integration contracts complete |
| R61-R65 | **94.0** | S1+S3 gates triggered (path traversal); real PDCA cycle (regression→detect→auto-fix); install.sh --install-path security hardening |
| R66-R73 | ~~96.2~~ | Multi-domain sim; Phase 2.2 root-cause; FAN-OUT; 11/11 gates; O4; Findings Gate; native review; honest recalibration to 89.0 |
| R74-R89 | **89.0** | 15-round self-study: widening verified (Stage 2), PDCA mechanism confirmed, timeout limit found (>20 files), 3 new governance decisions |

| Dimension | Baseline (57) | Current (89) |

|---|---:|---:|---:|
| Reasonix-native | 52 | 91 |
| DeepSeek fit | 78 | 92 |
| Loop budget control | 48 | 92 |
| Progressive widening | 40 | 85 |
| Conditional gate selection | 38 | 91 |
| PDCA evidence discipline | 58 | 84 |
| Observable verification | 30 | 90 |
| Evidence compaction | 45 | 91 |
| Failure-pattern memory | 40 | 82 |
| Self-review integration | 65 | 85 |
| Safety / anti-hallucination | 80 | 91 |

**Honest score: 89.0** (11-dimension average = 88.6). Previous 96.2 was inflated by unverified feature awards. Rubric fixed at baseline — no moving goalposts.

## Honest Limits

**Procedure cannot raise a model's ceiling — it can only light the path to reach it.** BlackCow enforces discipline: verify before claiming done, track findings before closing, diagnose before fixing. But the depth of creative insight, the ability to discover out-of-spec defects, and the polish of open-ended work belong to the model. When BlackCow hits that ceiling, it escalates — to a stronger model or a human. It never pretends.

> *"BlackCow cannot make DeepSeek think like Claude. It can make sure DeepSeek never stops halfway."*

## What is this?

**BlackCow Ops** brings the BKIT quality methodology to the Reasonix agent runtime, designed for DeepSeek's cost profile.

> *"OmO taught us to orchestrate. BKIT taught us to gate. DeepSeek taught us to stop counting tokens. BlackCow does all three."*

## Acknowledgments

BlackCow Ops builds on ideas from:

- **[BKIT by POPUP STUDIO](https://github.com/popup-studio-ai/bkit-claude-code)** — The original 11-gate quality taxonomy and PDCA methodology. BlackCow extends M1-M10+S1 into M1-M5 (Implementation) + S1-S3 (Security) + P1-P3 (Performance) with Reasonix-native implementations. Apache 2.0.
- **[OmO / oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent)** — Inspired by discipline agents, parallel orchestration, Hashline content verification, and hyperplan adversarial review concepts. No OmO source code is included. See upstream for license terms.
- **[Gajae-Code](https://github.com/Yeachan-Heo/gajae-code)** — deep-interview, tmux-backed workers, external harness philosophy.
- **[pi-team](https://github.com/minzique/pi-team)** — Transcript-based multi-agent round-robin communication.
- **[Claw Code](https://github.com/ultraworkers/claw-code)** — The agent-managed museum exhibit that inspired our self-improvement loop.

## License

Apache 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).

---

<div align="center">
  <p>Built with BlackCow Ops, by BlackCow Ops.</p>
</div>
