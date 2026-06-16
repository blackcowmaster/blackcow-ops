<div align="center">
  <h1>BlackCow Ops</h1>
  <p><strong>7 self-improving workflow skills for Reasonix + DeepSeek.</strong></p>
  <p>
    <a href="#install">Install</a> · <a href="#quick-start">Quick Start</a> ·
    <a href="README.ko.md">한국어</a> · <a href="README.ja.md">日本語</a> · <a href="README.zh-cn.md">简体中文</a>
  </p>
</div>

---

## What it is

BlackCow Ops is a set of 7 Reasonix skills that form a **govern → plan → execute → verify → evolve** pipeline for coding tasks. It enforces BKIT — an 11-gate quality taxonomy — tuned for DeepSeek's cost advantage. A typo fix costs ~$0.001; a multi-file feature costs ~$0.03.

**Honest score: 90.0/100** (11-dimension average). Score rubric fixed at baseline — no moving goalposts.

> Procedure cannot raise a model's ceiling — it can only light the path to reach it. When BlackCow hits the ceiling, it escalates. It never pretends.

## Skills

| Skill | Role |
|---|---|
| `blackcow-governor` | Preflight controller. Selects mode, gates, observable level, and PDCA budget before any work begins. |
| `blackcow-plan` | Strategic planner. Progressive widening, architecture options, decision-complete plans. |
| `blackcow-loop` | Execution engine. 5 modes (FAST~ESCALATE), PDCA, findings gate, O0-O4 verification. |
| `blackcow-qa` | Quality assurance. Conditional 11-gate evaluation with numeric thresholds. |
| `blackcow-librarian` | Project memory. Structure caching, failure-pattern memory, trend analysis. |
| `blackcow-skill-review` | Meta-auditor. Trend tracking and staleness detection for the skills themselves. |
| `blackcow-skill-evolver` | Safe evolution engine. Triple-safety gates for applying reviewed changes to skills. |

## Install

```bash
git clone https://github.com/blackcowmaster/blackcow-ops.git
cp blackcow-ops/skills/*.md ~/.reasonix/skills/
```

Restart Reasonix. All 7 skills are available globally.

## Quick Start

```
# Cache your codebase (once)
blackcow-librarian --command=init-deep

# Govern a task (mode, gates, budget)
blackcow-governor "Add OAuth2 authentication"

# Plan the implementation
blackcow-plan "Add OAuth2 authentication" --govern=oauth

# Execute the plan
blackcow-loop "Execute plans/oauth.md" --mode=standard --trust-level=2

# Verify quality
blackcow-qa "src/auth/" --gates=auto
```

Invoke via `run_skill` or the `/` shortcut: `/blackcow-plan Add OAuth2`

## Key Strengths

- **PRD to implementation.** Reads specs, infers tech stack, decomposes into independent units, and dispatches parallel planning. Asks before deciding — never silently picks your stack.
- **Cost-optimized for DeepSeek.** 5 execution modes scale from $0.001 (typo fix) to ~$0.10 (full security audit). Progressive widening starts cheap and widens only when needed.
- **11-gate quality.** M1-M5 (implementation), S1-S3 (security), P1-P3 (performance). Every gate has a numeric threshold and requires evidence to pass.
- **Findings gate.** Issues discovered during review are tracked and must be resolved before completion. No silent acceptance of known bugs.
- **Failure-pattern memory.** Past failures are recorded with effectiveness scores. High-effectiveness fixes are auto-applied; low-effectiveness patterns trigger escalation.
- **Subagent O4 verification.** Browser screenshots via Playwright CLI (`npx playwright screenshot`) — no native puppeteer dependency needed in subagents.
- **CLI bridge.** Subagents can use any CLI tool (`supabase`, `aws`, `firebase`, `docker`) via `run_command`. Authenticated tools require user confirmation.
- **Self-audit.** Every skill has a structured self-audit checklist. Skills review and evolve themselves.

## Architecture

```
blackcow-governor ──→ blackcow-plan ──→ blackcow-loop ──→ blackcow-qa
   (preflight)         (design)          (execute)         (verify)

blackcow-skill-review ──→ blackcow-skill-evolver
      (audit skills)          (fix skills)

                    blackcow-librarian
               (caching + memory + trends)
```

## Why DeepSeek

BlackCow was designed for models cheap enough to be wasteful. DeepSeek pricing (~$0.14/1M flash input) enables patterns that would be cost-prohibitive elsewhere: 15 parallel discovery lanes, 8 QA agents, 7 PDCA cycles.

## Reference

- **[BKIT](https://github.com/popup-studio-ai/bkit-claude-code)** — 11-gate quality taxonomy. Apache 2.0.

## License

Apache 2.0 — [LICENSE](LICENSE) · [NOTICE](NOTICE)

---

<div align="center"><p>Built with BlackCow Ops, by BlackCow Ops.</p></div>
