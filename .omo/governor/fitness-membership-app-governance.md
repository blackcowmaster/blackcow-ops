# Governance Decision: fitness-membership-app

| Field | Value |
|---|---|
| **Task** | Korean fitness membership app — class booking, attendance history, push reminders, premium Toss-level UX, rewarded ads (free tier) + subscription (premium), production-ready error monitoring. Plan only — no implementation. |
| **Governed at** | 2026-07-16T12:00:00Z |
| **Detected Intent** | Feature |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | FAST | Plan-only task. Zero code surface, zero runtime, zero side effects. Full PDCA loop and QA phase are wasted cycles. Consistent with sim-react-dashboard and sim-expo-login plan-only precedents. |
| **Trust Level** | L4 | Maximum trust. Output is a Markdown plan document — no risk of breaking existing code, no security surface. Plan quality is self-contained and human-reviewed. |
| **Bootstrap Lanes** | 1 | Single plan document output. Architecture research dispatched internally by planner, not governor. |
| **PDCA Max Cycles** | 0 | No implementation to iterate on. Plan quality evaluated at write-time by planner self-audit. |
| **Adversarial Reviewers** | 0 | No code surface to attack. Architecture analysis is analytical, not adversarial. |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal — plan must address all 8 core requirements |
| M2 test-pass | ❌ | No code to test |
| M3 regression | ❌ | No existing fitness app codebase — nothing to regress against |
| M4 lint | ❌ | Plan is Markdown, not executable |
| M5 dead-code | ❌ | No code changes |
| S1 dataFlow | ❌ | No type/schema files in diff; no runtime data flow to analyze |
| S2 auth | ❌ | No auth/route files in diff |
| S3 injection | ❌ | No handler/input files in diff |
| P1 query | ❌ | No DB/repository files in diff |
| P2 memory | ❌ | No collection/buffer files in diff |
| P3 latency | ❌ | No p95 target specified for existing code |

**Active gates: 1/12 (M1 only).** All other gates N/A for a plan-only task with zero code surface.

**Diff signal**: `skills/blackcow-governor.md` — the governor skill itself. Zero relevance to fitness app architecture. No gate triggers from diff.

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | O0 |
| **Max Capability** | O4 (from capabilities.json) |
| **Browser Available?** | YES (npx playwright) |
| **Capped?** | N/A — plan-only, no runtime verification possible or needed |
| **Fallback Strategy** | Manual human review of the plan document against the 8-requirement checklist |
| **Residual Risk** | None. The plan is a static design document. Any risk lives in the *implementation* that follows — which will have its own governance cycle with full gates. |

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| Stage 1 | uncertainty_score < 30 | 1 |
| Stage 2 | 30 ≤ uncertainty < 60 | 1 |
| Stage 3 | uncertainty ≥ 60 | 1 |

All stages capped at 1 lane — single document output. No parallel exploration needed for architecture-level design.

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| Plan fails M1 | Plan doesn't cover all 8 requirements | Re-dispatch planner with explicit 8-item checklist |
| Scope creep | Planner starts implementing code or generating source files | HALT — remind: plan only |

All other escalation rules (no evidence, same gate ×2, budget near limit) are N/A for plan-only tasks.

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| FP-010 | P1 | Date.toISOString() drops microsecond digits in PostgreSQL keyset cursor pagination | 2026-06-27 | 90 | **Flag for plan**: If fitness app uses PostgreSQL + cursor pagination (attendance history), document known fix in plan. Do NOT auto-apply (no code to fix). |
| — | — | All other 9 patterns (FP-001–FP-009) in tools-mapping / cross-reference domains — disjoint from fitness app architecture | — | — | — |

**Feed rules applied**: FP-010 is relevant if the plan recommends PostgreSQL cursor pagination for attendance history. Flag as architectural note only — no code surface to fix in a plan-only task.

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (discovery + governance)** | ~5K (preflight reads + this document) |
| **Tokens (plan writing)** | ~35K (multi-component architecture: tech stack selection, DB schema, API design, auth strategy, ad integration, subscription model, error monitoring, push notification architecture, Korean UX patterns) |
| **Tokens (QA/M1 check)** | ~2K (spec-match verification against 8 requirements) |
| **Total estimated** | ~42K |
| **Est. cost (flash)** | $0.00 (under flash tier limit for reads; generation may cross into pro) |
| **Est. cost (pro)** | $0.00 |
| **Est. cost (blended)** | $0.00 |
| **Historical ROI** | 0.78 score/token (feature task baseline from loop-roi.jsonl) |
| **Budget utilization** | ~10% of FAST mode budget |
| **Recommendation** | PROCEED — high-value architecture plan, zero risk, constrained scope |

## M1 Spec-Match Checklist (8 Requirements)

The plan MUST address all of the following. Post-plan verification:

| # | Requirement | Verification Signal |
|---|---|---|
| 1 | Class booking | Plan documents booking flow, reservation system, schedule view |
| 2 | Attendance history | Plan documents attendance tracking, history view with filtering/pagination |
| 3 | Push reminders | Plan documents push notification architecture (FCM/APNs), scheduling, deep-linking |
| 4 | Premium Korean UX (Toss-level) | Plan addresses animation patterns, haptic feedback, typography, color system, micro-interactions, empty/loading/error states |
| 5 | Rewarded ads (free tier) | Plan documents ad integration (AdMob rewarded ads), placement strategy, reward economy |
| 6 | Subscription (premium) | Plan documents IAP architecture (RevenueCat/StoreKit), entitlement system, premium feature gating |
| 7 | Production-ready error monitoring | Plan documents error monitoring stack (Sentry/Datadog/Firebase Crashlytics), alerting thresholds, error boundary strategy |
| 8 | Tech stack justification | Plan justifies framework choices with tradeoff analysis (at least 3 options considered) |

## Post-Governance Self-Audit Plan

| Check | Expectation |
|---|---|
| Plan file exists | `plans/fitness-membership-app.md` created |
| Tech stack justified | ≥3 options compared with tradeoffs, explicit recommendation |
| DB schema documented | Entity relationships: users, classes, bookings, attendance, subscriptions, ad_rewards |
| API design | REST or GraphQL endpoints enumerated; auth strategy documented |
| Korean UX patterns | Toss-level polish specified: animations, haptics, typography, color system |
| Ad integration arch | Rewarded ad placement + reward economy documented |
| Subscription arch | IAP flow, entitlement gating, RevenueCat or alternative documented |
| Push notification arch | FCM/APNs integration, scheduling, deep-link routing documented |
| Error monitoring stack | Specific tool chosen, alert thresholds, error boundary strategy |
| Plan is plan-only | No code was mutated, no source files emitted |

## Phase 2 Dispatch

```
# 1. Plan (FAST mode, plan-only — no loop, no QA)
run_skill({ name: "blackcow-plan", arguments: "Plan a Korean fitness membership app. Features: class booking, attendance history, push reminders, premium Toss-level UX, rewarded ads for free users, subscription for premium, production-ready error monitoring. Choose the tech stack (mobile + backend). Write plan to plans/fitness-membership-app.md. Do NOT implement — plan only. --govern=fitness-membership-app" })

# 2-5. SKIPPED — user directive: "Plan only — no implementation"
#   Loop, QA, skill-review, and post-mortem are all N/A for FAST/plan-only tasks.
```
