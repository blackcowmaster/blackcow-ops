# Governance Decision: bulk-delete

| Field | Value |
|---|---|
| **Task** | Add `DELETE /api/tasks/bulk` endpoint — accepts `{ ids: string[] }`, validates each ID, deletes individually, returns 207 Multi-Status with per-item results |
| **Governed at** | 2026-07-14T00:00:00Z |
| **Detected Intent** | Feature |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | STANDARD | Feature with tricky partial-success semantics; needs proper TDD + QA but not architectural change |
| **Trust Level** | L1 | Established patterns in codebase (single delete already exists); bulk semantics are new but compose from existing primitives |
| **Bootstrap Lanes** | 3 | STANDARD: 3 lanes (happy path, edge cases, auth/ownership) |
| **PDCA Max Cycles** | 3 | STANDARD default |
| **Adversarial Reviewers** | 0 | Not XS task; M complexity, adversarial not needed |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal — verify 207 shape, per-item status enum, error field optionality |
| M2 test-pass | ✅ | Universal — must pass all existing + new tests |
| M3 regression | ✅ | Universal — verify existing DELETE /:id still works, all existing tests pass |
| M4 lint | ✅ | Source files in diff (routes, controller, service, schema, types) |
| M5 dead-code | ❌ | No deletions planned |
| S1 dataFlow | ✅ | Schema + type files in diff (bulkDeleteSchema, BulkDeleteResult type) |
| S2 auth | ✅ | Auth/route files in diff — verify per-item ownership checks, other-user isolation |
| S3 injection | ✅ | Body input files in diff — validate array size limit, UUID format, no SQL injection via IDs |
| P1 query | ✅ | DB access files in diff — N+1 query pattern (individual findById + remove per ID), verify transaction behavior |
| P2 memory | ✅ | Array body could be large — verify size cap enforced |
| P3 latency | ❌ | No p95 target specified; bulk operations inherently N+1 latency |

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | O0 |
| **Max Capability** | O4 |
| **Browser Available?** | YES |
| **Capped?** | No — O0 sufficient (API endpoint, curl + jest verification) |
| **Fallback Strategy** | N/A |
| **Residual Risk** | None |

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
| FP-010 | P1 | Date.toISOString() drops microsecond digits in cursor pagination | 2026-06-27 | 90 | Not relevant to bulk delete (no cursor/pagination involved) — skip |

**Feed rules:**
- No patterns directly relevant to bulk delete. FP-010 applies to cursor pagination only.

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (discovery)** | ~8K |
| **Tokens (TDD + PDCA)** | ~25K |
| **Tokens (QA)** | ~5K |
| **Total estimated** | ~38K |
| **Est. cost (flash)** | $0.038 |
| **Est. cost (pro)** | $0.19 |
| **Est. cost (blended)** | ~$0.076 |
| **Historical ROI** | 0.78 (feature area) |
| **Budget utilization** | ~30% of STANDARD mode budget (~125K) |
| **Recommendation** | PROCEED |

## Design Decisions

### Why individual deletes (not bulk SQL)?
The `DELETE /api/tasks/bulk` endpoint must handle **partial success** — some IDs may be valid and deletable, others may not exist or belong to other users. A single SQL `WHERE id IN (...)` would be all-or-nothing (or would require complex `RETURNING` logic to determine which succeeded). Individual `findById` + `remove` per ID gives clear per-item accountability and matches the existing service-layer ownership checks.

### Why 207 Multi-Status?
Standard HTTP semantics for partial success. 200 would hide failures; 400/422 would reject the whole batch. 207 communicates "I processed everything; here's what happened to each."

### Response shape:
```json
{
  "results": [
    { "id": "uuid-1", "status": "deleted" },
    { "id": "uuid-2", "status": "not_found", "error": "Task with id uuid-2 not found" },
    { "id": "uuid-3", "status": "forbidden", "error": "You do not have permission to delete this task" }
  ]
}
```

### Size limit: 100 IDs max
Prevents abuse. Enforced in Zod schema (`.max(100)` on the array).

### Changes required:
| File | Change |
|---|---|
| `src/schemas/task.schema.ts` | Add `bulkDeleteSchema`: `{ ids: z.array(z.string().uuid()).min(1).max(100) }` |
| `src/types/task.ts` | Add `BulkDeleteResult` interface |
| `src/routes/tasks.routes.ts` | Add `DELETE /bulk` route, note: must be BEFORE `DELETE /:id` |
| `src/controllers/tasks.controller.ts` | Add `bulkRemove` controller |
| `src/services/tasks.service.ts` | Add `bulkRemove` method (loops over IDs, calls existing `remove`-style logic per item) |
| `__tests__/routes/tasks.routes.test.ts` | Add bulk delete test suite |

### Route ordering critical:
Express matches routes in registration order. `DELETE /bulk` must be registered **before** `DELETE /:id` — otherwise Express will match "bulk" as an `:id` param.

## Post-Governance Self-Audit

After pipeline completes:
- [ ] Loop used STANDARD mode
- [ ] QA ran selected gates (M1-M4, S1-S3, P1-P2)
- [ ] Observable level O0 achieved (no browser needed)
- [ ] No ESCALATE events fired
- [ ] Existing tests (all 35+ test cases) still pass
