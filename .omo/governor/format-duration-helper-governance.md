# Governance Decision: format-duration-helper

| Field | Value |
|---|---|
| **Task** | Add `formatDuration()` helper to `src/pomodoro/sessionStats.ts` — converts seconds to `"25m"` or `"1h 30m"` format. Pure function, include tests in `__tests__/pomodoro/sessionStats.test.ts`. |
| **Governed at** | 2025-07-17T19:50:00Z |
| **Detected Intent** | Feature |

---

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | **FAST** | XS task: 1 pure function (~10 lines) + ~5-8 test cases. Additive only — appends to existing file and test file. Zero dependencies, zero I/O, zero async. Established test infrastructure (42 existing tests in sessionStats.test.ts, 149 pomodoro tests total). |
| **Trust Level** | **L3** | Established codebase with consistent patterns. Slight deduction from L4 because this is net-new domain logic with edge-case surface (zero seconds, <60s, exact hours, multi-hour+minutes combos, negative input). |
| **Bootstrap Lanes** | **1** | Single function with tightly-coupled test cases. No parallel exploration justified. |
| **PDCA Max Cycles** | **1** | One cycle sufficient for a pure function with well-bounded interface. Second cycle only if tests reveal logic errors. |
| **Adversarial Reviewers** | **0** | XS task with zero I/O surface, zero auth surface, zero injection surface. Pure formatting function. |

---

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | **Universal.** Must cover: (a) seconds < 60 → `"Xs"` or `"Xm"` format, (b) seconds ≥ 60 → minutes-only when < 3600, (c) seconds ≥ 3600 → `"Xh Ym"` format, (d) exact hours omit minutes, (e) pure function — no side effects. |
| M2 test-pass | ✅ | **Universal.** New test cases in `__tests__/pomodoro/sessionStats.test.ts` must pass. |
| M3 regression | ✅ | **Universal.** All existing 149 pomodoro tests must continue to pass. Purely additive — no existing logic modified, so regression risk is near-zero. |
| M4 lint | ✅ | Modified TypeScript source file. Must pass ESLint and Prettier. |
| M5 dead-code | ❌ | Purely additive — no deletions, no dead code to detect. |
| S1 dataFlow | ❌ | No type/schema files in diff. New function is a pure string formatter — no data flow risk. |
| S2 auth | ❌ | No auth/route files in diff. Pure computation module. |
| S3 injection | ❌ | No handler/input files in diff. Pure computation — no DOM, no URL, no user input. |
| P1 query | ❌ | No DB/repository files in diff. In-memory computation only. |
| P2 memory | ❌ | No collection/buffer files in diff. O(1) computation. |
| P3 latency | ❌ | No p95 target. O(1) string formatting — sub-microsecond execution. |

**Active gates: 4/12 (M1, M2, M3, M4).** All security and performance gates are N/A for a pure string-formatting function.

**Diff signal analysis:** No git repo available. Task is explicitly scoped to additive-only: append one function to `src/pomodoro/sessionStats.ts` and test cases to `__tests__/pomodoro/sessionStats.test.ts`. Zero existing code modifications.

---

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | **O0** |
| **Max Capability** | O4 (from capabilities.json — playwright screenshots verified) |
| **Browser Available?** | YES |
| **Capped?** | N/A — pure string formatting. No rendering, no DOM, no network. O0 (static analysis + unit tests) is the correct verification level. |
| **Fallback Strategy** | Jest unit tests provide complete functional verification. Manual verification: import function in Node REPL, call with sample values, verify outputs. |
| **Residual Risk** | **Minimal.** The only risk is logic errors in the formatting boundary conditions: (a) zero seconds, (b) seconds < 60, (c) 60–3599 seconds, (d) ≥ 3600 with remainder, (e) exact hours, (f) negative input handling. Unit tests covering all boundaries mitigate this fully. |

---

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| Stage 1 | uncertainty_score < 30 | 1 |
| Stage 2 | 30 ≤ uncertainty < 60 | 1 |
| Stage 3 | uncertainty ≥ 60 | 1 |

All stages capped at **1 lane**. Single cohesive function — no decomposition benefit from parallel lanes.

---

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| No new evidence | 1 cycle with Δ=0 | Re-dispatch D1 (pro) → function re-eval → user |
| Same gate ×2 | Same gate fails twice | ESCALATE to user with failure log |
| Budget near limit | 80% of max cycles (i.e., 1 cycle used) | ESCALATE to user (only 1 PDCA cycle budgeted) |
| Existing test regression | Any pre-existing test fails | HALT immediately — do not proceed until fixed. Regression is unexpected (no source mods). |

---

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| — | — | **No patterns match `pomodoro` / `format` / `duration` domain.** | — | — | — |

**Feed rules check:** All 10 existing patterns (FP-001 through FP-010) scanned. Domains covered: `tools-mapping` (7 patterns), `cross-reference` (2 patterns), `database` (1 pattern). All domains are disjoint from this task. **Zero patterns applied.**

---

## Spec Detail: `formatDuration`

### Function Signature

```typescript
/**
 * Format a duration in seconds into a human-readable string.
 *
 * - seconds < 60: returns "Xs" (e.g., 45 → "45s")
 * - 60 ≤ seconds < 3600: returns "Xm" (e.g., 1500 → "25m")
 * - seconds ≥ 3600 with zero remainder: returns "Xh" (e.g., 3600 → "1h")
 * - seconds ≥ 3600 with remainder: returns "Xh Ym" (e.g., 5400 → "1h 30m")
 * - zero seconds: returns "0s"
 * - negative seconds: returns "0s" (defensive fallback)
 *
 * Pure function — no side effects, no external state, no mutation.
 *
 * @param seconds  Duration in seconds (integer or float; truncated to int)
 * @returns Human-readable duration string
 */
export function formatDuration(seconds: number): string;
```

### Expected Behavior Matrix

| Input (seconds) | Output | Rationale |
|---|---|---|
| `0` | `"0s"` | Zero case |
| `30` | `"30s"` | Sub-minute |
| `59` | `"59s"` | Sub-minute boundary |
| `60` | `"1m"` | Exactly 1 minute |
| `1500` | `"25m"` | Typical Pomodoro work session |
| `300` | `"5m"` | Typical Pomodoro break session |
| `3599` | `"59m"` | Just under 1 hour |
| `3600` | `"1h"` | Exactly 1 hour — no minutes |
| `5400` | `"1h 30m"` | 1.5 hours |
| `7200` | `"2h"` | Exactly 2 hours |
| `7260` | `"2h 1m"` | 2 hours + 1 minute |
| `9000` | `"2h 30m"` | 2.5 hours |
| `3661` | `"1h 1m"` | Edge: 1h + 1m |
| `-5` | `"0s"` | Negative defensive fallback |
| `-3600` | `"0s"` | Large negative defensive fallback |

### Design Constraints (from Evidence)

Based on analysis of existing code and prior QA findings:

- **Same module, same style**: `formatDuration` lives in `src/pomodoro/sessionStats.ts`, following the existing patterns (JSDoc, pure functions, zero dependencies).
- **No new imports**: Function uses only `Math.floor()` — zero external dependencies.
- **Export alongside existing exports**: Added to the existing export list. No new barrel file needed.
- **Tests in existing test file**: New `describe('formatDuration', ...)` block appended to `__tests__/pomodoro/sessionStats.test.ts`, following the established test patterns (Jest, `describe`/`it` blocks, explicit expected values).
- **Import in tests**: Add `formatDuration` to the existing import statement from `../../src/pomodoro/sessionStats`.

---

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (Phase 0 discovery + governance)** | ~6K (5 files read + this governance document) |
| **Tokens (function implementation)** | ~1K (1 function, ~15 lines) |
| **Tokens (unit tests)** | ~3K (1 describe block, ~15 test cases) |
| **Tokens (QA — M1/M2/M3/M4)** | ~2K (4-gate verification) |
| **Total estimated** | **~12K** |
| **Est. cost (flash)** | $0.00 |
| **Est. cost (pro)** | $0.00 |
| **Est. cost (blended)** | $0.00 |
| **Historical ROI** | **0.78** score/token (feature task baseline from `loop-roi.jsonl`, `task_area: feature`) |
| **Budget utilization** | ~9% of FAST mode budget (~128K) |
| **Recommendation** | **PROCEED** — minimal cost (~12K tokens), zero risk (pure computation, additive-only), well-constrained scope (1 function, 15 boundary cases). |

---

## Post-Governance Self-Audit

| # | Check | Result |
|---|---|---|
| 1 | Mode selection matches task scale | ✅ FAST for XS pure-function addition. Not over-orchestrated. |
| 2 | Gate selection based on actual diff signals | ✅ Purely additive — no app code modifications. M1-M4 active; all S/P gates correctly skipped. |
| 3 | Observable level achievable with available tooling | ✅ O0 — Jest unit tests sufficient. O4 exists but irrelevant for pure string formatting. |
| 4 | Failure-pattern feed loaded from memory | ✅ 10 patterns loaded. 0 relevant to pomodoro/format domain. |
| 5 | Loop ROI history consulted for scope recommendation | ✅ Feature ROI 0.78 → PROCEED. |
| 6 | Escalation rules defined with concrete actions | ✅ 4 rules: no-evidence, same-gate×2, budget-limit, regression. |
| 7 | Governance document written to `.omo/governor/` | ✅ `format-duration-helper-governance.md` |
| 8 | No invented diff signals or failure patterns | ✅ All cited from actual files on disk. |
| 9 | Mode escalation justified by evidence | ✅ FAST justified: XS scope (1+1 files, additive-only), pure computation, no I/O. |
| 10 | Downstream skills will honor governance decisions | ✅ Plan/loop/qa will receive `--govern=format-duration-helper`. |
| 11 | Prior QA finding incorporated | ✅ `pomodoro-wave1-qa` S1 finding ("TIMER_RESET wipes sessionsToday") — not relevant here. `formatDuration` is a pure string formatter with no state dependency. |
| 12 | Cross-skill contract honored | ✅ Evidence index loaded. Capabilities detected. Memory consulted. |
| 13 | Skill-review appropriately scoped | ✅ FAST mode — no adversarial review needed. Self-audit checklist suffices. |

---

## Verdict

**GOVERNANCE: PROCEED.** FAST mode, L3 trust, 4 active gates (M1-M4), O0 observable, 1 PDCA cycle budgeted. XS pure-function task with well-bounded interface. Zero risk to existing code (purely additive). 15 boundary cases defined in spec matrix.

**Key design directive for downstream skills:**
> `formatDuration` is a pure function that takes `seconds: number` and returns a human-readable string. It lives alongside the existing `SessionRecord`/`SessionStats` exports in `src/pomodoro/sessionStats.ts`. Tests append to the existing `__tests__/pomodoro/sessionStats.test.ts` file. No new files, no new dependencies, no existing-code modifications.
