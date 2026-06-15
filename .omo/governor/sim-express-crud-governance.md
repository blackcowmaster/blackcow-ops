# Governance Decision: sim-express-crud

| Field | Value |
|---|---|
| **Task** | Plan an Express.js TypeScript CRUD API for a "tasks" resource — PostgreSQL queries, input validation, auth middleware. Plan only. |
| **Governed at** | 2026-06-27T18:00:00Z |
| **Detected Intent** | Feature |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | STANDARD | Plan-only task. Needs multi-lane exploration + adversarial review for completeness. FAST skips reviews (risk of incomplete threat model). FULL/SIEGE overkill for no-code artifact. |
| **Trust Level** | L2 | Plan-only — no code mutation. Standard adversarial review without L3/L4 guardrails. |
| **Bootstrap Lanes** | 5 | DB schema, route design, auth middleware, validation strategy, error/testing patterns. |
| **PDCA Max Cycles** | 2 | Plan review/revision only. |
| **Adversarial Reviewers** | 3 | Medium scope (single-resource CRUD with 3 cross-cutting concerns). |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal |
| M2 test-pass | ❌ | No test infrastructure for this repo; plan-only |
| M3 regression | ❌ | No existing Express codebase; plan-only |
| M4 lint | ❌ | No source files in diff (new feature, unrelated repo) |
| M5 dead-code | ❌ | No deletions in diff |
| S1 dataFlow | ✅ | Plan must specify data flow: request → middleware → validation → controller → service → repository → PostgreSQL |
| S2 auth | ✅ | User explicitly requested auth middleware design |
| S3 injection | ✅ | User explicitly requested input validation; SQL injection prevention in P1 queries |
| P1 query | ✅ | User explicitly requested PostgreSQL query design; parameterized queries, migration strategy |
| P2 memory | ❌ | No collection/buffer concerns for a CRUD plan |
| P3 latency | ❌ | No p95 target specified |

**Active gates (5/11):** M1, S1, S2, S3, P1

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | O2 |
| **Max Capability** | O2 (from capabilities.json) |
| **Browser Available?** | NO |
| **Capped?** | O2 → O2 (no cap needed — max capability matches) |
| **Fallback Strategy** | Plan verification via structural review: check all 5 gates addressed in plan text, cross-reference against Express/TypeScript best-practice patterns |
| **Residual Risk** | Plan cannot be runtime-verified (O3 browser-based API testing unavailable). Risk accepted — plan-only task. |

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| Stage 1 | uncertainty_score < 30 | 3 |
| Stage 2 | 30 ≤ uncertainty < 60 | 7 |
| Stage 3 | uncertainty ≥ 60 | 10 |

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| No new evidence | 1 cycle with Δ=0 | Re-dispatch D1 (pro) → plan re-eval → user |
| Same gate ×2 | Same gate fails twice | ESCALATE to user |
| Budget near limit | 80% of max cycles | ESCALATE |
| Scope creep | D2 flags scope change | Return to planner |

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| — | — | No patterns match task area "express-crud" | — | — | — |

**Feed rules:**
- `effectiveness ≥ 80` → apply known fix automatically before PDCA
- `effectiveness 40-79` → suggest fix, require confirmation
- `effectiveness < 40` → escalate gate priority, do NOT auto-apply (fix unreliable)
- `reappeared_after_fix: true` → mark pattern as CRITICAL, require architectural review

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (discovery)** | ~15K |
| **Tokens (plan writing)** | ~25K |
| **Tokens (QA — 5 gates)** | ~10K |
| **Total estimated** | ~50K |
| **Est. cost (flash)** | $0.007 |
| **Est. cost (pro)** | $0.022 |
| **Est. cost (blended)** | ~$0.015 |
| **Historical ROI** | 0.78 score/token (feature area) |
| **Budget utilization** | ~60% of STANDARD mode budget |
| **Recommendation** | PROCEED |
