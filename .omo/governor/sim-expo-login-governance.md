# Governance Decision: sim-expo-login

| Field | Value |
|---|---|
| **Task** | Plan an Expo React Native login screen — evaluate expo-auth-session vs custom email/password form with managed-workflow tradeoffs. Plan only; no implementation. |
| **Governed at** | 2026-07-14T00:00:00Z |
| **Detected Intent** | Feature |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | FAST | Plan-only task. No implementation, no test suite, no runtime. Full PDCA loop and QA phase are wasted cycles. |
| **Trust Level** | L4 | Maximum trust. Output is a Markdown plan document — zero risk of breaking existing code, no security surface, no runtime behavior. Plan quality is self-contained. |
| **Bootstrap Lanes** | 1 | Single plan file output. No parallel exploration needed for a two-option tradeoff. |
| **PDCA Max Cycles** | 0 | No implementation to iterate on. Plan quality is evaluated at write-time by the planner itself. |
| **Adversarial Reviewers** | 0 | No code surface to attack. Tradeoff evaluation is analytical, not adversarial. |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal — plan must address all three requirements: (1) evaluate expo-auth-session, (2) evaluate custom email/password, (3) managed-workflow tradeoffs |
| M2 test-pass | ❌ | No code to test |
| M3 regression | ❌ | No existing codebase — greenfield plan, nothing to regress |
| M4 lint | ❌ | Plan is Markdown, not executable |
| M5 dead-code | ❌ | No code changes |
| S1 dataFlow | ❌ | No data flow to analyze |
| S2 auth | ❌ | Plan advises on auth, but no auth code to audit |
| S3 injection | ❌ | No input handlers |
| P1 query | ❌ | No database layer |
| P2 memory | ❌ | No runtime collections |
| P3 latency | ❌ | No performance targets |

**Active gates: 1/12 (M1 only).** All other gates are N/A for a plan-only task with zero code surface.

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | O0 |
| **Max Capability** | O2 (from capabilities.json) |
| **Browser Available?** | NO |
| **Capped?** | N/A — plan-only, no runtime verification possible or needed |
| **Fallback Strategy** | Manual human review of the plan document against the three requirements |
| **Residual Risk** | None. The plan is a static recommendation document. Any risk lives in the *implementation* that follows — which will have its own governance cycle with full gates. |

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| Stage 1 | uncertainty_score < 30 | 1 |
| Stage 2 | 30 ≤ uncertainty < 60 | 1 |
| Stage 3 | uncertainty ≥ 60 | 1 |

All stages capped at 1 lane — single document output, no parallel exploration paths needed for a two-option tradeoff evaluation.

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| Plan fails M1 | Plan doesn't cover all three requirements | Re-dispatch planner with explicit checklist |
| Scope creep | Planner starts implementing code | HALT — remind: plan only |

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| — | — | No relevant patterns for Expo/React Native/login domain | — | — | — |

**Feed rules check:** Zero matching patterns. All 9 existing patterns are in `tools-mapping` / `cross-reference` domains — no overlap with mobile UI planning.

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (discovery)** | ~2K (governance decision + preflight reads) |
| **Tokens (plan writing)** | ~4K (tradeoff analysis + recommendation document) |
| **Tokens (QA/M1 check)** | ~1K (spec-match verification) |
| **Total estimated** | ~7K |
| **Est. cost (flash)** | $0.00 (well under flash tier limit) |
| **Est. cost (pro)** | $0.00 |
| **Est. cost (blended)** | $0.00 |
| **Historical ROI** | 0.78 score/token (feature task baseline from loop-roi.jsonl) |
| **Budget utilization** | ~3% of FAST mode budget |
| **Recommendation** | PROCEED |

## Post-Governance Self-Audit (FINAL)

| Check | Result |
|---|---|
| Mode selection matches task scale | ✅ FAST for plan-only, zero code surface |
| Gate selection based on actual diff signals | ✅ Diff unrelated (eco-health files), only M1 active |
| Observable level achievable | ✅ O0 — no runtime, no browser needed |
| Failure-pattern feed loaded | ✅ 9 patterns loaded, 0 relevant to task domain |
| Loop ROI history consulted | ✅ 0.78 feature baseline confirms PROCEED |
| Escalation rules defined | ✅ 2 rules: M1 fail → re-dispatch, scope creep → HALT |
| Governance document at correct path | ✅ `.omo/governor/sim-expo-login-governance.md` |
| No invented diff signals or failure patterns | ✅ All cited from actual on-disk files |
| Downstream skill consumed governance | ✅ `blackcow-plan` invoked with `--govern=sim-expo-login` |
| Skill-review skipped (FAST mode) | ✅ |
| Post-mortem skipped (no implementation) | ✅ |

## M1 Gate Verification

| Requirement | Coverage | Status |
|---|---|---|
| Evaluate expo-auth-session | 28 references (Option A section, tradeoff matrix, Phase 2 tasks) | ✅ |
| Evaluate custom email/password | 14 references (Option B section, Wave tasks, risk register) | ✅ |
| Managed workflow tradeoffs | 17 references (Expo Go compatibility, development build constraints, tradeoff matrix "Managed workflow 적합도" row) | ✅ |

## Verdict

**GOVERNANCE EFFECTIVE.** All 11 self-audit checks pass. M1 gate (only active gate) passes 3/3 requirements. Plan written to `plans/sim-expo-login.md` (327 lines, 18.7 KB).

**Decision:** Option C — email/password Phase 1, OAuth Phase 2.
**Critical rationale:** Expo Go compatibility. `expo-auth-session` requires development build (`expo.scheme`), killing the fast-iteration loop. Email/password stack is 100% pure JS, zero managed workflow issues. Shared SecureStore + AuthContext infrastructure means nothing is thrown away when OAuth is added later.

**Pipeline completed:** governor → plan. Loop and QA skipped per FAST mode governance (plan-only, no code surface).