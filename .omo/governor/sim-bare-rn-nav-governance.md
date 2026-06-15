# Governance Decision: sim-bare-rn-nav

| Field | Value |
|---|---|
| **Task** | Plan React Native bare workflow navigation setup with react-navigation, including native linking on iOS/Android. Plan-only — no implementation. |
| **Governed at** | 2026-06-27T23:00:00Z |
| **Detected Intent** | Feature |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | STANDARD | Plan production required; loop/qa gated by user directive ("plan only") |
| **Trust Level** | L3 | Plan-only — no code mutated, no test surface, zero side effects. High trust warranted. |
| **Bootstrap Lanes** | 1 | Single plan document, no parallelism needed |
| **PDCA Max Cycles** | 0 | Plan-only — no implementation to iterate on |
| **Adversarial Reviewers** | 0 | No code surface to attack; plan document is static artifact |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Plan document must self-verify against requirements |
| M2 test-pass | ❌ | No code surface; plan-only task |
| M3 regression | ❌ | No code changes; no regression risk |
| M4 lint | ❌ | No source files in diff |
| M5 dead-code | ❌ | No source files in diff |
| S1 dataFlow | ❌ | No type/schema files in diff |
| S2 auth | ❌ | No auth/route files in diff |
| S3 injection | ❌ | No handler/input files in diff |
| P1 query | ❌ | No DB/repository files in diff |
| P2 memory | ❌ | No collection/buffer files in diff |
| P3 latency | ❌ | No p95 target specified |

**Diff signal**: `.omo/governor/ecosystem-health-quiet-report-governance.md`, `.omo/governor/ecosystem-health-report.txt`, `skills/tests/validate-blackcow-ecosystem-health.sh` — all `.omo` and test infrastructure. Zero relevance to React Native navigation. No gate triggers from diff.

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | O0 |
| **Max Capability** | O2 (from capabilities.json) |
| **Browser Available?** | NO |
| **Capped?** | O0 (plan-only — no runtime artifact to observe) |
| **Fallback Strategy** | Manual review of plan document against requirements checklist |
| **Residual Risk** | Plan quality depends entirely on blackcow-plan skill knowledge of React Native / react-navigation. No verification loop. |

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| Stage 1 | N/A | 1 |
| Stage 2 | N/A | 1 |
| Stage 3 | N/A | 1 |

*Widening disabled — single-lane plan production with zero PDCA cycles.*

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| Plan fails self-audit | M1 score < 90% on plan self-check | Return plan to blackcow-plan for revision |
| Scope creep | Plan exceeds bare-workflow navigation scope | Return to planner with scope boundary |

All other escalation rules (no evidence, same gate ×2, budget near limit) are N/A for plan-only tasks.

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| — | — | No patterns match React Native / navigation domain | — | — | No action |

**Feed rules**: All 9 existing patterns are in `tools-mapping` and `cross-reference` domains — disjoint from this task. No pattern feed applied.

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (plan production)** | ~12K |
| **Tokens (TDD + PDCA)** | 0 (plan-only) |
| **Tokens (QA)** | 0 (plan-only) |
| **Total estimated** | ~12K |
| **Est. cost (flash)** | ~$0.003 |
| **Est. cost (pro)** | ~$0.18 |
| **Est. cost (blended)** | ~$0.09 |
| **Historical ROI** | 0.78 score/token (feature tasks) |
| **Budget utilization** | ~22% of STANDARD mode budget (~55K) |
| **Recommendation** | PROCEED — minimal cost, zero risk, constrained scope |

## Post-Governance Self-Audit Plan

| Check | Expectation |
|---|---|
| Plan file exists | `plans/sim-bare-rn-nav.md` created |
| Plan covers iOS native linking | CocoaPods podspec / Podfile instructions present |
| Plan covers Android native linking | auto-linking or Manual Linking steps present |
| Plan covers react-navigation core | @react-navigation/native + stack/tab dependency list |
| Plan respects bare workflow | No Expo references; CLI-based setup |
| Plan is plan-only | No code was mutated |

## Phase 2 Dispatch

```
# 1. Plan (STANDARD mode, run plan even in plan-only task)
run_skill({ name: "blackcow-plan", arguments: "Plan React Native bare workflow navigation setup with react-navigation. Must handle native linking on iOS/Android. Write plan to plans/sim-bare-rn-nav.md. Do NOT implement — plan only. --govern=sim-bare-rn-nav" })

# 2-5. SKIPPED — user directive: "Do NOT implement — plan only"
```
