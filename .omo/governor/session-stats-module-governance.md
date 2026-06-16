# Governance Decision: session-stats-module

| Field | Value |
|---|---|
| **Task** | Add a session statistics module (`src/pomodoro/sessionStats.ts`) tracking: total sessions completed today, total focus minutes, current streak (consecutive days with ≥1 session). Pure TypeScript — no React dependency. Include unit tests. |
| **Governed at** | 2025-07-17T18:30:00Z |
| **Detected Intent** | Feature |

---

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | **FAST** | XS task: 1 source file + 1 test file. Pure computation module — zero dependencies, zero I/O, zero async. Well-defined interface (3 functions). Existing codebase has established patterns (`timerReducer.ts`, `timerEngine.ts`) and strong test infra. No diff in any existing source file — purely additive. |
| **Trust Level** | **L3** | Established codebase with 95%+ test coverage, consistent patterns, strict TypeScript. Slight deduction from L4 because this is net-new domain logic with edge-case surface (midnight rollover, empty history, streak gaps). |
| **Bootstrap Lanes** | **1** | Single module with 3 tightly-coupled functions. No parallel exploration justified. |
| **PDCA Max Cycles** | **1** | One cycle should be sufficient for a pure computation module with well-bounded interface. Second cycle only if tests reveal logic errors. |
| **Adversarial Reviewers** | **0** | XS task with zero I/O surface, zero auth surface, zero injection surface. No attack vector in a pure function that computes dates and counts. |

---

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | **Universal.** Must cover: (a) total sessions completed today, (b) total focus minutes, (c) current streak (consecutive days with ≥1 session). |
| M2 test-pass | ✅ | **Universal.** New test file `__tests__/pomodoro/sessionStats.test.ts` must pass. |
| M3 regression | ✅ | **Universal.** Existing 125+ tests (`timerReducer.test.ts` 80+, `timerEngine.test.ts` 45+) must continue to pass. No existing source files modified — purely additive, so regression risk is near-zero, but verification is mandatory. |
| M4 lint | ✅ | New TypeScript source file. Must pass `eslint src/pomodoro/sessionStats.ts --max-warnings 0` and Prettier formatting. |
| M5 dead-code | ❌ | No deletions in diff. Purely additive — no dead code to detect. |
| S1 dataFlow | ❌ | No type/schema files in diff. New module exports 3 functions with primitive return types — no data flow risk. |
| S2 auth | ❌ | No auth/route files in diff. Pure computation module. |
| S3 injection | ❌ | No handler/input files in diff. Module receives structured `SessionRecord[]` — no user input, no DOM, no URL parsing. |
| P1 query | ❌ | No DB/repository files in diff. Module is in-memory computation only. |
| P2 memory | ❌ | No collection/buffer files in diff. Input is bounded array; O(n) single-pass computation. |
| P3 latency | ❌ | No p95 target specified. O(n) over small arrays (≤365 entries) — sub-millisecond execution. |

**Active gates: 4/12 (M1, M2, M3, M4).** All security and performance gates are N/A for a pure computation module with no I/O, no auth, and no data mutation.

**Diff signal analysis:** `git diff --name-only HEAD~1` returns only `skills/blackcow-governor.md` and `skills/blackcow-loop.md`. Zero app-code changes. Confirms purely additive task — no gate triggers from existing code surface.

---

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | **O0** |
| **Max Capability** | O4 (from capabilities.json — playwright screenshots verified) |
| **Browser Available?** | YES |
| **Capped?** | N/A — pure computation. No rendering, no DOM, no network. O0 (static analysis + unit tests) is the correct verification level. |
| **Fallback Strategy** | Jest unit tests provide complete functional verification. Manual verification: import module in Node REPL, call with sample data, verify outputs. |
| **Residual Risk** | **Minimal.** The only risk is logic errors in date arithmetic (leap years, DST transitions, timezone handling). Unit tests covering boundary conditions mitigate this. Recommendation: tests must include (a) same-day sessions, (b) cross-midnight sessions, (c) empty history, (d) single-entry history, (e) streak with gaps, (f) DST spring-forward/fall-back days. |

---

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| Stage 1 | uncertainty_score < 30 | 1 |
| Stage 2 | 30 ≤ uncertainty < 60 | 1 |
| Stage 3 | uncertainty ≥ 60 | 1 |

All stages capped at **1 lane**. Single cohesive module — no decomposition benefit from parallel lanes. Widening would introduce integration cost with zero parallelism gain.

---

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| No new evidence | 1 cycle with Δ=0 | Re-dispatch D1 (pro) → module re-eval → user |
| Same gate ×2 | Same gate fails twice | ESCALATE to user with failure log |
| Budget near limit | 80% of max cycles (i.e., 1 cycle used) | ESCALATE to user (only 1 PDCA cycle budgeted) |
| Existing test regression | Any pre-existing test fails | HALT immediately — do not proceed until fixed. Regression is unexpected (no source mods). |
| Date-edge bugs found | DST or timezone test fails | ESCALATE — may need `date-fns` or `luxon` dependency, which changes scope |

---

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| — | — | **No patterns match `pomodoro` / `stats` / `date-computation` domain.** | — | — | — |

**Feed rules check:** All 10 existing patterns (FP-001 through FP-010) scanned. Domains covered: `tools-mapping` (7 patterns), `cross-reference` (2 patterns), `database` (1 pattern). All domains are disjoint from this task. **Zero patterns applied.**

**Relevant prior finding from qa-history:** `pomodoro-wave1-qa` (2025-07-17) found S1=94 with finding: *"TIMER_RESET wipes sessionsToday"*. This is directly relevant — the new stats module MUST NOT rely on `TimerState.sessionsToday` as an authoritative source, since it gets wiped on reset. The stats module should instead receive a persistent `SessionRecord[]` as input, making it independent of the in-memory timer state. This finding informs the module's interface design but does not gate it — it's an architectural constraint.

---

## Interface Design Constraints (from Evidence)

Based on analysis of existing code (`timerReducer.ts`, `types.ts`, `timerEngine.ts`) and the prior QA finding:

### Input Shape

```typescript
/** A single completed session record (persisted by the caller). */
interface SessionRecord {
  /** ISO-8601 timestamp of session completion */
  completedAt: string;
  /** Duration in seconds (typically 1500 for work, 300 for break) */
  durationSeconds: number;
  /** Session type */
  type: 'work' | 'break';
}
```

### Output Shape

```typescript
interface SessionStats {
  /** Total work sessions completed today (local date) */
  sessionsToday: number;
  /** Total focus minutes today (work sessions only) */
  totalFocusMinutes: number;
  /** Consecutive days (including today) with ≥1 work session */
  currentStreak: number;
}
```

### Exported Functions

```typescript
/** Compute session statistics from completed session history. */
export function computeSessionStats(history: SessionRecord[]): SessionStats;

/** Helper: get today's date string in local timezone (YYYY-MM-DD). */
export function getTodayDateString(): string;

/** Helper: check if two date strings are consecutive calendar days. */
export function isConsecutiveDay(day1: string, day2: string): boolean;
```

### Design Rationale

- **Stateless module**: `computeSessionStats(history)` is a pure function — the caller owns persistence. No class, no mutation, no side effects.
- **No React**: Zero imports from React. Usable in any JS/TS environment.
- **No `TimerState` dependency**: Stats module receives `SessionRecord[]` — invulnerable to `TIMER_RESET` wiping `sessionsToday`.
- **Local timezone**: Streaks and "today" use the local calendar date, not UTC. This matches user expectation (midnight = local midnight, not UTC midnight).
- **Work sessions only for focus minutes**: Break sessions do not count toward `totalFocusMinutes` or `currentStreak`.

---

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (Phase 0 discovery + governance)** | ~5K (6 files read + this governance document) |
| **Tokens (module implementation)** | ~3K (1 source file, ~80 lines) |
| **Tokens (unit tests)** | ~5K (1 test file, ~30 test cases) |
| **Tokens (QA — M1/M2/M3/M4)** | ~2K (4-gate verification) |
| **Total estimated** | **~15K** |
| **Est. cost (flash)** | $0.00 |
| **Est. cost (pro)** | $0.00 |
| **Est. cost (blended)** | $0.00 |
| **Historical ROI** | **0.78** score/token (feature task baseline from `loop-roi.jsonl`, `task_area: feature`) |
| **Budget utilization** | ~12% of FAST mode budget (~128K) |
| **Recommendation** | **PROCEED** — minimal cost (~15K tokens), zero risk (pure computation, no existing file modifications), well-constrained scope (3 functions, 3 stats), established test infrastructure. |

---

## Post-Governance Self-Audit

| # | Check | Result |
|---|---|---|
| 1 | Mode selection matches task scale | ✅ FAST for XS pure-computation addition. Not over-orchestrated. |
| 2 | Gate selection based on actual diff signals | ✅ Only skill files in diff — zero app code. M1-M4 active; all S/P gates correctly skipped. |
| 3 | Observable level achievable with available tooling | ✅ O0 — Jest unit tests sufficient. O4 exists but irrelevant. |
| 4 | Failure-pattern feed loaded from memory | ✅ 10 patterns loaded. 0 relevant to pomodoro/stats domain. |
| 5 | Loop ROI history consulted for scope recommendation | ✅ Feature ROI 0.78 → PROCEED. |
| 6 | Escalation rules defined with concrete actions | ✅ 5 rules: no-evidence, same-gate×2, budget-limit, regression, date-edge. |
| 7 | Governance document written to `.omo/governor/` | ✅ `session-stats-module-governance.md` |
| 8 | No invented diff signals or failure patterns | ✅ All cited from actual files on disk. |
| 9 | Mode escalation justified by evidence | ✅ FAST justified: XS scope (1+1 files), pure computation, additive-only, no I/O. |
| 10 | Downstream skills will honor governance decisions | ✅ Plan/loop/qa will receive `--govern=session-stats-module`. |
| 11 | Prior QA finding incorporated | ✅ `pomodoro-wave1-qa` S1 finding ("TIMER_RESET wipes sessionsToday") informed interface constraint — stats module MUST use persistent `SessionRecord[]`, not `TimerState.sessionsToday`. |
| 12 | Cross-skill contract honored | ✅ Evidence index loaded. Capabilities detected. Memory consulted. |
| 13 | Skill-review appropriately scoped | ✅ FAST mode — no adversarial review needed. Self-audit checklist suffices. |

---

## Verdict

**GOVERNANCE: PROCEED.** FAST mode, L3 trust, 4 active gates (M1-M4), O0 observable, 1 PDCA cycle budgeted. XS pure-computation task with well-bounded interface. Zero risk to existing code (purely additive). Prior QA finding incorporated as architectural constraint.

**Key design directive for downstream skills:**
> The stats module MUST accept `SessionRecord[]` as input — it MUST NOT read `TimerState.sessionsToday`. The prior QA audit (`pomodoro-wave1-qa`, S1=94) identified that `TIMER_RESET` wipes `sessionsToday`, making it unreliable as a stats source. Stats persistence is the caller's responsibility; the module is a pure computation function.
