# Governance Decision: sim-express-crud-pagination-extract

| Field | Value |
|---|---|
| **Task** | Extract pagination logic from `tasks.repository.ts` into `src/lib/pagination.ts` PaginationService. Repository handles only raw DB queries. All pagination math (cursor building, offset calculation, hasMore determination) moves to the service. Update all call sites. |
| **Governed at** | 2026-07-15T00:00:00Z |
| **Detected Intent** | Quality (cross-cutting refactor) |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | STANDARD | Cross-cutting refactor of core data-access path — medium risk. Cannot use FAST (subtle bugs possible in pagination edge cases: cursor parsing, offset math, sort direction). Not FULL (behavior-preserving, no new features, no exploration needed). Existing 39+ test suite provides safety net. |
| **Trust Level** | L2 | Code mutation with comprehensive test suite. Repository tests directly cover both cursor and offset modes. Route integration tests verify end-to-end. |
| **Bootstrap Lanes** | 3 | Three well-understood concerns: (1) PaginationService design, (2) repository refactoring, (3) controller refactoring. Codebase already fully mapped — no exploration needed. |
| **PDCA Max Cycles** | 2 | One cycle for implementation + test verification. One reserve cycle for edge-case fixes. |
| **Adversarial Reviewers** | 3 | Medium scope. Cross-cutting change touches repository, controller, and new service. Pagination edge cases (empty result, cursor parsing boundaries, sort direction) justify multi-reviewer scrutiny. |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal — behavior must be exactly preserved: same SQL results, same response shape, same cursor format |
| M2 test-pass | ✅ | Universal — all 39+ existing tests must pass unchanged (tests should not need modification) |
| M3 regression | ✅ | Universal — zero behavioral regressions. Pagination outputs must be byte-identical for same inputs. |
| M4 lint | ✅ | TypeScript compilation (`tsc --noEmit`) must pass. New file introduces new import graph. |
| M5 dead-code | ✅ | Deletions in repository (cursor parsing, offset math, hasMore logic removed from `findAll`). Must verify no orphaned code, no stale imports. |
| S1 dataFlow | ✅ | Response DTO mapping unchanged (`{ data, meta: { page, limit, total, hasMore, cursor? } }`). Verify no internal fields leak through refactored path. |
| S2 auth | ❌ | No auth middleware, route, or token handling changes. |
| S3 injection | ✅ | Cursor parsing introduces string splitting (`lastIndexOf('_')`) on user-supplied cursor values. Must verify no SQL injection via crafted cursor strings. |
| P1 query | ✅ | SQL query structure changes — `_cursor` expression reference moves, cursor WHERE clause built externally. Must verify parameterized queries preserved, no string interpolation of cursor values. |
| P2 memory | ❌ | No collection/buffer concerns. PaginationService is stateless. |
| P3 latency | ❌ | No p95 target specified. Refactor should not regress query performance (same SQL, same parameterization). |

**Active gates (8/11):** M1, M2, M3, M4, M5, S1, S3, P1

## Change Surface

Based on codebase analysis (no git diff available — project at `/`, not a git repo):

| File | Change | Lines |
|---|---|---|
| `src/lib/pagination.ts` | **NEW** — PaginationService class with: `CURSOR_EXPR` constant, `resolveOrderDir()`, `decodeCursor()`, `buildCursorCondition()`, `calculateOffset()`, `determineHasMore()`, `extractNextCursor()` | ~80 |
| `src/repositories/tasks.repository.ts` | **MODIFIED** — `findAll` method: strip cursor parsing, cursor WHERE clause construction, offset calculation, `nextCursor` extraction, `hasMore` logic. Delegate to PaginationService. Add import. | -40 / +25 |
| `src/controllers/tasks.controller.ts` | **MODIFIED** — `getAll` handler: replace inline `hasMore` ternary with `paginationService.determineHasMore()`. Add import. | -3 / +6 |

### PaginationService Design Contract

```
CURSOR_EXPR → "t.created_at::text || '_' || t.id::text"
resolveOrderDir('desc'|'asc') → 'DESC'|'ASC'
decodeCursor(cursor) → { createdAt, id }      // lastIndexOf('_') split
buildCursorCondition(cursor?, order, paramIdx) → { condition, nextParamIdx }
calculateOffset(page, limit) → number          // (page-1)*limit
determineHasMore(mode, resultCount, limit, total, page) → boolean
extractNextCursor(mode, rows, limit) → string|null
```

### Repository `findAll` After Refactor

```
1. Build WHERE clause (status, priority, user_id, deleted_at) — UNCHANGED
2. orderDir ← paginationService.resolveOrderDir(pq.order)
3. If cursor mode: cursorCondition ← paginationService.buildCursorCondition(pq.cursor, pq.order, paramIdx)
4. SELECT: use paginationService.CURSOR_EXPR for _cursor, plug cursorCondition.clause
5. COUNT: UNCHANGED (uses whereClause only)
6. Execute both queries — UNCHANGED
7. Strip _cursor from rows — UNCHANGED
8. nextCursor ← paginationService.extractNextCursor(pq.mode, result.rows, pq.limit)
```

### Controller `getAll` After Refactor

```
hasMore ← paginationService.determineHasMore(pq.mode, tasks.length, pq.limit, total, pq.page)
// Replaces: pq.mode === 'cursor' ? nextCursor !== null : pq.page * pq.limit < total
```

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | O2 |
| **Max Capability** | O4 (from capabilities.json — browser available) |
| **Browser Available?** | YES |
| **Capped?** | O4 → O2 (browser-based API testing not needed — unit/integration test suite sufficient for behavior-preserving refactor) |
| **Fallback Strategy** | Jest test suite: 39+ tests covering cursor pagination, offset pagination, edge cases (identical timestamps, empty results, page-beyond-range). Route integration tests with supertest verify full request/response cycle. |
| **Residual Risk** | Low. Refactor is mechanical — extract-and-delegate. All pagination edge cases already tested. Risk集中在 cursor delimiter change (if `_` ever appears in timestamptz::text or UUID — currently impossible per PostgreSQL spec). |

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
| Budget near limit | 80% of max cycles (1.6 → 2) | ESCALATE |
| Scope creep | D2 flags scope change (e.g., type changes, test modifications) | Return to planner |
| Test regression | Any existing test fails | Immediate halt, revert, diagnose |
| Cursor format change | FP-010 pattern re-triggers (timestamptz precision loss) | ESCALATE — architectural review required |

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| FP-010 | P1 | Date.toISOString() drops microsecond digits, causing PostgreSQL keyset cursor pagination to silently exclude rows with identical timestamps | 2026-06-27 | 90 | **ARCHITECTURAL CONSTRAINT**: PaginationService MUST use PostgreSQL-native cursor construction (`created_at::text \|\| '_' \|\| id::text`). Must NOT use JS Date serialization. Must use `lastIndexOf('_')` for cursor parsing. Already fixed in current code — refactor must preserve this pattern exactly. |

**Feed rules:**
- `effectiveness ≥ 80` → apply known fix automatically before PDCA
- `effectiveness 40-79` → suggest fix, require confirmation
- `effectiveness < 40` → escalate gate priority, do NOT auto-apply (fix unreliable)
- `reappeared_after_fix: true` → mark pattern as CRITICAL, require architectural review

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (discovery)** | ~8K |
| **Tokens (implementation — plan + code)** | ~18K |
| **Tokens (PDCA — test + fix)** | ~10K |
| **Tokens (QA — 8 gates)** | ~12K |
| **Total estimated** | ~48K |
| **Est. cost (flash)** | ~$0.005 |
| **Est. cost (pro)** | ~$0.022 |
| **Est. cost (blended)** | ~$0.014 |
| **Historical ROI** | 0.78 score/token (feature area — sim-express-crud tasks consistently high-value, low-regret) |
| **Budget utilization** | ~65% of STANDARD mode budget |
| **Recommendation** | PROCEED |
