# Governance Decision: sim-express-crud-keyset-fix

| Field | Value |
|---|---|
| **Task** | Fix keyset cursor pagination: identical timestamps break cursor-based pagination |
| **Governed at** | 2026-06-27T19:30:00Z |
| **Detected Intent** | Bug |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | FAST | Single bug fix with clear diagnosis path. No multi-lane exploration needed. |
| **Trust Level** | L2 | Code mutation — verify through existing test suite. |
| **Bootstrap Lanes** | 0 | Bug already localized; no exploration needed. |
| **PDCA Max Cycles** | 1 | Root cause identified in Phase 2.2 diagnosis before any fix applied. |
| **Adversarial Reviewers** | 0 | Minimal scope — 3 files changed. |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal |
| M2 test-pass | ✅ | Universal — 17 repo + 22 route tests pass |
| M3 regression | ✅ | All 39 existing tests still pass |
| S1 dataFlow | ✅ | Controller → Service → Repository flow unchanged; cursor now originates in PostgreSQL |
| P1 query | ✅ | Keyset pagination now unified (no OFFSET fallback needed); still parameterized |

## Root Cause Diagnosis (Phase 2.2)

**Hypothesis**: `Date.toISOString()` truncates PostgreSQL `timestamptz` microsecond precision to milliseconds.

**Evidence chain**:
1. PostgreSQL stores `timestamptz` at microsecond precision: `2026-06-27 12:00:00.123456+00`
2. `pg` driver returns timestamps as JavaScript `Date` objects (millisecond precision)
3. Controller + test construct cursor via `new Date(created_at).toISOString()` → `2026-06-27T12:00:00.123Z`
4. PostgreSQL re-interprets cursor as `2026-06-27T12:00:00.123000Z`
5. Row comparison `(created_at, id) < (cursor_ts, cursor_id)` fails: `.123456 < .123000` = FALSE
6. Items with same-millisecond timestamps are excluded from subsequent pages

**Diagnostic test confirmed**: 0 of 1 expected items returned on page 2 when all tasks share `2026-06-27T12:00:00.123456Z`.

## Fix Applied

| File | Change |
|---|---|
| `src/repositories/tasks.repository.ts` | PostgreSQL constructs cursor natively: `created_at::text \|\| '_' \|\| id::text as _cursor`. Return `nextCursor` in result. Parse incoming cursor with `lastIndexOf('_')`. Removed OFFSET fallback — keyset pagination unified. |
| `src/controllers/tasks.controller.ts` | Use `nextCursor` from service layer instead of constructing via `toISOString()` |
| `__tests__/repositories/tasks.repository.test.ts` | Updated keyset test to use `nextCursor`. Added edge-case test: 3 tasks with identical `created_at` — verifies all 3 tasks returned across pages with no duplicates. |

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | O2 |
| **Verification** | 17 repository tests + 22 route tests = 39 total, all passing |

## Verification

```
Tests:       39 passed, 39 total
Test Suites: 2 passed, 2 total
```

- ✅ Existing keyset test passes (uses `nextCursor`)
- ✅ New identical-timestamp edge case test passes
- ✅ All 22 route/integration tests pass (controller change non-breaking)
- ✅ TypeScript compiles with zero errors
- ✅ `nextCursor` contains full microsecond precision (verified: `2026-06-27 12:00:00.123456+00`)
