# Governance Decision: rust-rewrite

| Field | Value |
|---|---|
| **Task** | Rewrite entire BlackCow pipeline (7 skills) from Markdown/bash to compiled Rust binary |
| **Governed at** | 2026-06-20T20:00:00Z |
| **Detected Intent** | **ARCHITECTURAL REWRITE** — complete paradigm shift from LLM-native Markdown skills to compiled Rust binary |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | **ESCALATE** | Task is outside BKIT pipeline scope. This is a human engineering project, not an agent-executed code change. Governor cannot dispatch to plan/loop/qa. |
| **Trust Level** | N/A | Pipeline cannot execute this task at any trust level. |
| **Bootstrap Lanes** | 0 | No plan can be produced by blackcow-plan for an architectural rewrite of the planning system itself. |
| **PDCA Max Cycles** | 0 | Not applicable. |
| **Adversarial Reviewers** | 0 | Not applicable. |

### Why ESCALATE is the only correct mode:

| Factor | Evidence |
|---|---|
| **Scope** | 7 skills, 6,025 lines of Markdown → estimated 30-60K lines of Rust. Multi-week human engineering project. |
| **Paradigm shift** | Current: LLM-interpreted prose instructions. Target: compiled deterministic code. These are fundamentally different architectures — not a 1:1 translation. |
| **Evolution cliff** | 40 rounds of self-improvement (R1-R40), 64 commits, achieving 91.4/100 on 11-dimension quality. A rewrite discards all of this. |
| **Self-referential problem** | Rewriting `blackcow-plan` means you lose the planning capability mid-rewrite. Rewriting `blackcow-loop` means you lose execution. Rewriting `blackcow-qa` means you lose verification. Every skill rewritten breaks the pipeline that could validate it. |
| **Infrastructure gap** | No Rust toolchain detected. No Cargo.toml. No test harness for compiled languages. M2-M5, S1-S3, P1-P3 gates are all NOT_TRIGGERED against Rust source. |
| **Pipeline self-scope** | BKIT governs agent-executed tasks within the Reasonix runtime. It does not govern its own architectural replacement. |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ❌ | No plan can exist — blackcow-plan itself is a rewrite target |
| M2 test-pass | ❌ | No Rust toolchain, no test harness |
| M3 regression | ❌ | Baseline cannot be established — no Rust codebase exists |
| M4 lint | ❌ | No Rust compiler/clippy available |
| M5 dead-code | ❌ | No codebase |
| S1 dataFlow | ❌ | No data flow to analyze |
| S2 auth | ❌ | No entry points |
| S3 injection | ❌ | No input surfaces |
| P1 query | ❌ | No database |
| P2 memory | ❌ | No collections |
| P3 latency | ❌ | No runtime |

**All 11 gates: NOT_TRIGGERED.** The BKIT quality framework has no applicability to a non-existent Rust codebase.

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | **O0** — No observable verification possible |
| **Max Capability** | O0 (no Rust toolchain, no browser for visual verification) |
| **Browser Available?** | YES (but irrelevant — no Rust Wasm target) |
| **Capped?** | O0 (no capability) |
| **Fallback Strategy** | Human code review only |
| **Residual Risk** | **MAXIMUM** — Complete loss of all 40-round evolution gains. No automated quality gates apply. |

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| N/A | N/A | 0 |

**Widening is disabled.** There are no discovery lanes to widen — this task has no intersection with the BKIT pipeline's operating domain.

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| **Immediate ESCALATE** | Task scope exceeds pipeline domain | **ESCALATE to user with full risk assessment** |
| **No pipeline dispatch** | Self-referential rewrite | Do NOT invoke blackcow-plan, blackcow-loop, or blackcow-qa |
| **Governor-only output** | Outside pipeline scope | Governance document only — no downstream dispatch |

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| N/A | — | No failure patterns exist for this task class | — | — | — |

**No patterns apply.** This is a novel task category: "rewrite the pipeline itself in a different language."

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (discovery)** | ~3K (this governance doc) |
| **Tokens (TDD + PDCA)** | N/A — pipeline cannot execute |
| **Tokens (QA)** | N/A — no gates trigger |
| **Total estimated** | ~3K |
| **Est. cost (flash)** | ~$0.0004 |
| **Est. cost (pro)** | ~$0.0013 |
| **Est. cost (blended)** | ~$0.0005 |
| **Historical ROI** | N/A — no comparable task in loop-roi.jsonl |
| **Budget utilization** | 0% — no pipeline budget allocated |
| **Recommendation** | **ESCALATE TO USER — DO NOT PROCEED THROUGH PIPELINE** |

---

## Governor's Assessment

### What the user is asking for:

Rewrite 7 LLM-native Reasonix skill files (6,025 lines of Markdown prose) into a single compiled Rust binary. The skills are:

| Skill | Lines | Role | Rust equivalents needed |
|---|---|---|---|
| `blackcow-governor` | 261 | Preflight mode/gate/O-level selection | CLI flag parsing + git diff analysis + JSON/YAML config |
| `blackcow-plan` | 1,050 | Strategic planner with 3-stage widening | LLM orchestration (API calls), DAG dependency resolution |
| `blackcow-loop` | 1,413 | Execution engine with 5 modes, PDCA, O0-O4 | TDD runner, hashline verification, subprocess management |
| `blackcow-qa` | 715 | 11-gate quality assurance | Test runner, lint integration, security scanning |
| `blackcow-librarian` | 920 | Project memory, 7 commands | File system crawler, JSONL database, cache management |
| `blackcow-skill-review` | 305 | Meta-auditor | Markdown parser, trend analysis |
| `blackcow-skill-evolver` | 312 | Safe evolution engine | File backup, diff application, regression detection |

### Fundamental architectural problem:

The current skills are **LLM-native** — they describe *how an LLM should think and act*. They say things like:

> "If uncertainty > 30, widen to stage 2"
> "Dispatch 8 QA subagents in parallel"
> "If matchRate < 90%, run PDCA cycle"

A Rust binary cannot "think" or "dispatch subagents." It must either:
1. **Call LLM APIs** (becoming an LLM client, not a replacement), or
2. **Reimplement everything deterministically** (losing all reasoning/judgment capabilities that give BKIT its quality)

### What a Rust rewrite would actually be:

**Option A: LLM client wrapper** — A Rust binary that calls DeepSeek/Claude APIs with the same prompts currently in the Markdown files. This preserves BKIT's quality but is just a packaging change (Markdown → Rust string literals). The value proposition is unclear — Reasonix already handles LLM orchestration.

**Option B: Deterministic reimplementation** — A Rust binary that replaces all LLM reasoning with deterministic algorithms. This loses:
- Progressive widening (uncertainty-driven → rule-driven, strictly worse)
- PDCA adaptive diagnosis (LLM analysis → pattern matching, strictly worse)
- Adversarial QA reasoning (LLM judgment → static rules, strictly worse)
- Self-review trend analysis (LLM comprehension → regex, strictly worse)

**Option C: Hybrid** — Rust binary for deterministic parts (file I/O, git ops, test running, hashing) + LLM API calls for reasoning parts. This is essentially Option A with Rust wrapping.

### Recommendation:

**DO NOT proceed with this rewrite through the BKIT pipeline.** Instead, consider:

1. **If the goal is portability beyond Reasonix:** Extract the BKIT prompt logic into a format that multiple LLM runtimes can consume (YAML/JSON config + prompt templates). Rust can be a *distribution mechanism* but the intelligence must remain LLM-native.

2. **If the goal is performance:** Profile first. The current bottleneck is LLM API latency, not Markdown parsing overhead. Rust wrapping won't help.

3. **If the goal is a standalone tool:** Design it as a new project (`blackcow-cli`) that *invokes* the BKIT methodology, rather than rewriting the methodology itself. The Rust binary would call LLM APIs with BKIT prompts.

4. **If the goal is to reduce LLM dependency:** This fundamentally changes what BKIT *is*. The 11-gate quality comes from LLM reasoning. Without it, you have a conventional linter/test runner — useful but not BKIT.

### If the user insists on proceeding:

The governor cannot plan or execute this. The user must:
1. Create a new Rust project (`cargo init blackcow-cli`)
2. Design the architecture (Option A/B/C above)
3. Write the code manually (or use a separate LLM session for code generation)
4. After the Rust binary exists, use `blackcow-qa` to verify it as a *target*, not as a replacement for the pipeline itself

---

## Post-Governance Self-Audit

| Checklist Item | Status |
|---|---|
| Mode selection matches task scale | ✅ ESCALATE — correct for architectural rewrite |
| Gate selection based on actual diff signals | ✅ All NOT_TRIGGERED — no Rust codebase exists |
| Observable level achievable | ✅ O0 — honest admission of no capability |
| Failure-pattern feed loaded | ✅ None applicable |
| Loop ROI history consulted | ✅ None applicable (no history for this task class) |
| Escalation rules defined | ✅ Immediate ESCALATE with rationale |
| Governance document written | ✅ `.omo/governor/rust-rewrite-governance.md` |
| No invented signals/patterns | ✅ All claims backed by evidence |
| Mode escalation justified | ✅ Task is outside pipeline's operating domain |
| No downstream dispatch | ✅ Plan/loop/qa NOT invoked |
| Self-audit complete | ✅ |
