# Governance Decision: sim-express-crud (IMPLEMENTATION)

| Field | Value |
|---|---|
| **Task** | IMPLEMENT Express.js TypeScript CRUD API for tasks resource — write all code, tests, verify 5 gates |
| **Governed at** | 2026-06-27T19:00:00Z |
| **Detected Intent** | Feature (Implementation — real code, not plan-only) |
| **Parent Governance** | `.omo/governor/sim-express-crud-governance.md` (plan-only, completed) |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | FULL | Real code implementation with all 4 waves, testcontainers integration tests, coverage gates. Overrides parent STANDARD (plan-only). |
| **Trust Level** | L2 | Standard implementation — no adversarial review needed (plan already had 3 reviewers). Code follows well-trodden Express/TypeScript patterns. |
| **Bootstrap Lanes** | 5 | Per plan: db schema, routes, auth, validation, repository (plan's 5-lane survey already done) |
| **PDCA Max Cycles** | 3 | Implementation with test-driven verification. 3 cycles for fix-verify loops. |
| **Adversarial Reviewers** | 0 | Plan already had 3 adversarial reviewers (RVA/RVB/RVC). Code implements reviewed plan. |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal — verify plan→code traceability |
| M2 test-pass | ✅ | Universal — tests must pass |
| M3 regression | ❌ | No existing Express codebase — greenfield |
| M4 lint | ✅ | Source files in diff (all new .ts files) |
| M5 dead-code | ❌ | No deletions in diff |
| S1 dataFlow | ✅ | Type/schema files — verify request→controller→service→repo chain |
| S2 auth | ✅ | Auth middleware — JWT verify, algorithm enforcement |
| S3 injection | ✅ | Input validation — Zod schemas + parameterized queries |
| P1 query | ✅ | Repository — parameterized queries, keyset pagination, N+1 prevention |
| P2 memory | ❌ | No collection/buffer concerns |
| P3 latency | ❌ | No p95 target specified |

**Active gates (7/11):** M1, M2, M4, S1, S2, S3, P1

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | O2 |
| **Max Capability** | O2 (from capabilities.json) |
| **Browser Available?** | NO |
| **Capped?** | O2 → O2 (no cap) |
| **Fallback Strategy** | curl-based API smoke tests + Jest/supertest integration tests with testcontainers |
| **Residual Risk** | No browser-based E2E testing (O3). Mitigated by comprehensive supertest integration tests + curl smoke tests. |

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| Stage 1 | uncertainty_score < 30 | 3 |
| Stage 2 | 30 ≤ uncertainty < 60 | 7 |
| Stage 3 | uncertainty ≥ 60 | 10 |

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| No new evidence | 1 cycle with Δ=0 | Re-dispatch → plan re-eval → user |
| Same gate ×2 | Same gate fails twice | ESCALATE to user |
| Budget near limit | 80% of max cycles (2.4 → 2) | ESCALATE |
| Scope creep | New requirements beyond plan scope | Return to planner |
| Test failure cascade | >3 tests fail same wave | Halt wave, fix root cause |

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| — | — | No patterns match "express-crud" task area | — | — | — |

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (implementation)** | ~70K |
| **Tokens (testing + fix)** | ~25K |
| **Tokens (QA — 7 gates)** | ~15K |
| **Total estimated** | ~110K |
| **Est. cost (flash)** | $0.015 |
| **Est. cost (pro)** | $0.049 |
| **Est. cost (blended)** | ~$0.032 |
| **Historical ROI** | 0.78 score/token (feature area) |
| **Budget utilization** | ~96% of FULL mode budget |
| **Recommendation** | PROCEED |

## Implementation Strategy

Waves executed per plan with these adaptations:
- **Docker available** → testcontainers PostgreSQL works (`postgres:16-alpine`)
- **No local psql** → migration validation via testcontainers + programmatic checks
- **No browser** → API verification via supertest + curl smoke tests only

### Wave Execution Order
1. **Wave 1** (Foundation): deps + config + types + schemas + errors + db + response — all parallel
2. **Wave 2** (Core): auth + validate + repository + security-headers + app bootstrap — parallel on Wave 1
3. **Wave 3** (Integration): service → controller → routes → server — sequential on Wave 2
4. **Wave 4** (Hardening): rate-limit + repo tests + integration tests + lint — parallel on Wave 3

### Verification Gates Per Wave
| Wave | Gates Verified |
|---|---|
| W1 | M1 (deps, config), S1 (types, error sanitization), S3 (Zod schemas) |
| W2 | S2 (auth), S3 (validation), P1 (repository), M1 (app bootstrap) |
| W3 | M1 (controllers, routes, server), S1 (data flow) |
| W4 | M2 (tests pass), M4 (lint), S2 (auth tests), S3 (injection tests), P1 (query tests) |
