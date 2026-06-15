# Governance Decision: sim-express-crud-pagination-meta

| Field | Value |
|---|---|
| **Task** | Add `mode=cursor|offset` query param to GET /api/tasks. Response: `{ data: [...], meta: { page, limit, total, hasMore } }`. Tests for both modes. |
| **Governed at** | 2026-07-14T12:00:00Z |
| **Detected Intent** | Feature |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | FAST | Incremental change to an existing, tested API. 7 files changed, all well-understood. No exploration needed — codebase already mapped. |
| **Trust Level** | L2 | Code mutation with existing test suite as safety net. 39 existing tests provide regression guard. |
| **Bootstrap Lanes** | 0 | No exploration needed — code structure already known. |
| **PDCA Max Cycles** | 1 | Single straightforward change. |
| **Adversarial Reviewers** | 0 | Minimal scope. |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal — response shape must match `{ data, meta: { page, limit, total, hasMore } }` |
| M2 test-pass | ✅ | Universal — existing 39 tests + new pagination mode tests |
| M3 regression | ✅ | All existing tests must pass; response shape change is additive |
| M4 lint | ✅ | tsc --noEmit must pass |
| S1 dataFlow | ✅ | Response DTO mapping changes — verify no internal fields leaked |
| S3 injection | ✅ | New `mode` param passes through Zod validation |
| P1 query | ✅ | New OFFSET SQL path must be parameterized |

**Active gates (7/11):** M1, M2, M3, M4, S1, S3, P1

## Change Surface (git diff)

| File | Change |
|---|---|
| `src/schemas/task.schema.ts` | Add `mode: z.enum(['cursor','offset']).default('cursor')` |
| `src/types/api.ts` | `ApiMeta`: `totalPages`→`hasMore`; add `mode` to `PaginatedQuery` |
| `src/repositories/tasks.repository.ts` | Add OFFSET pagination path; `FindAllResult` gets `hasMore` |
| `src/lib/response.ts` | `paginated()`: emit `{ page, limit, total, hasMore }`; cursor in cursor mode |
| `src/controllers/tasks.controller.ts` | Pass `mode`, compute `hasMore` per-mode |
| `__tests__/routes/tasks.routes.test.ts` | Add cursor-mode + offset-mode pagination tests |
| `__tests__/repositories/tasks.repository.test.ts` | Add offset pagination repo test |

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | O2 |
| **Verification** | Jest test suite: existing 39 + new pagination mode tests |

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| FP-010 | P1 | Date.toISOString() drops microsecond digits in keyset cursor | 2026-06-27 | 90 | Already fixed — PostgreSQL-native cursor construction in place. No action needed. |

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| Regression | Any existing test fails | Revert and diagnose |
| Budget near limit | N/A (FAST mode, ~15K tokens) | ESCALATE |

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens** | ~12K |
| **Est. cost (blended)** | ~$0.004 |
| **Historical ROI** | 0.78 score/token (feature area) |
| **Recommendation** | PROCEED |
