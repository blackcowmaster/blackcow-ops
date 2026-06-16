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

**Honest score: 90.6/100** (11-dimension average). Score rubric fixed at baseline — no moving goalposts.

> Procedure cannot raise a model's ceiling — it can only light the path to reach it. When BlackCow hits the ceiling, it escalates. It never pretends.

## Skills

| Skill | Role |
|---|---|
| `blackcow-governor` | Preflight controller. Selects mode, gates, observable level, and PDCA budget before any work begins. |
| `blackcow-plan` | Strategic planner. Progressive widening, architecture options, decision-complete plans. |
| `blackcow-loop` | Execution engine. TRY mode (2-3 min) + STANDARD/FULL. PDCA on failure, Findings Gate, Visual Review (codex), O0-O4 verification. |
| `blackcow-qa` | Quality assurance. Conditional 11-gate evaluation with numeric thresholds. |
| `blackcow-librarian` | Project memory. Structure caching, failure-pattern memory, trend analysis. |
| `blackcow-skill-review` | Meta-auditor. Trend tracking and staleness detection for the skills themselves. |
| `blackcow-skill-evolver` | Safe evolution engine. Triple-safety gates for applying reviewed changes to skills. |

## Install

```bash
git clone https://github.com/blackcowmaster/blackcow-ops.git
bash blackcow-ops/skills/install.sh
```

Restart Reasonix. All 7 skills with correct platform-specific tool names are available globally.

## Quick Start

```
# New projects are created in ~/Downloads/blackcow_project/

# 80% of tasks: just ask Loop (TRY mode, ~3 min)
blackcow-loop "Build a Pomodoro timer app"

# Complex tasks: full pipeline
blackcow-governor "Add OAuth2 with role-based access"
blackcow-loop "Execute plans/oauth.md" --govern=oauth
blackcow-qa "src/auth/" --govern=oauth
```

Invoke via `run_skill` or the `/` shortcut: `/blackcow-plan Add OAuth2`

## Key Strengths

- **PRD to implementation.** Reads specs, infers tech stack, decomposes into independent units, and dispatches parallel planning. Asks before deciding — never silently picks your stack.
- **DeepSeek-native.** TRY mode implements directly in ~3 minutes for most tasks. Governor only intervenes when needed — try first, govern when stuck. 90% of tasks never touch the heavy pipeline.
- **11-gate quality.** M1-M5 (implementation), S1-S3 (security), P1-P3 (performance). Every gate has a numeric threshold and requires evidence to pass.
- **Findings gate.** Issues discovered during review are tracked and must be resolved before completion. No silent acceptance of known bugs.
- **Failure-pattern memory.** Past failures are recorded with effectiveness scores. High-effectiveness fixes are auto-applied; low-effectiveness patterns trigger escalation.
- **Visual review.** Screenshots analyzed by codex CLI for UI feedback — readability, contrast, spacing, hierarchy. Works on iOS simulator and web. Falls back gracefully if codex is unavailable.
- **Simulator automation.** `xcrun simctl` boot, screenshot, and app launch — full mobile development cycle without leaving the terminal.
- **Workspace isolation.** All new projects created under `~/Downloads/blackcow_project/` — never pollutes the tool directory.
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
