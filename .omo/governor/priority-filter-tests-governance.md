# Governance Decision: priority-filter-tests

| Field | Value |
|---|---|
| **Task** | Bug fix: GET /api/tasks should support filtering by priority (?priority=high|medium|low) — dual-mode cursor/offset with filtered total count |
| **Governed at** | 2026-06-15T23:50:00Z |
| **Completed at** | 2026-06-15T23:55:00Z |
| **Detected Intent** | Feature (but implementation already exists — this is a test-gap-fill) |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | **FAST** | Zero code changes — implementation already exists and works. Only adding tests. |
| **Trust Level** | **L3** | Feature is pre-verified by repo tests. Route tests are additive and non-destructive. |
| **Bootstrap Lanes** | 1 | Single lane: read existing route test file, identify insertion points, write tests |
| **PDCA Max Cycles** | 1 | Tests should pass first try — implementation is already correct. |
| **Adversarial Reviewers** | 0 | FAST mode, test-only change, no production code touched |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ❌ | No plan/spec change — tests verify existing behavior |
| M2 test-pass | ✅ | Universal — new + existing tests must pass |
| M3 regression | ✅ | Universal — existing 54 tests must not break |
| S1 dataFlow | ✅ | Priority filter → controller → service → repo → COUNT. Verify filtered total in both modes |

## Preflight Discovery

### Code Audit: Feature Already Implemented

| Layer | File | Status | Evidence |
|---|---|---|---|
| Zod validation | `src/schemas/task.schema.ts:43` | ✅ DONE | `priority: taskPriorityEnum.optional()` in `paginationSchema` |
| Type definition | `src/types/api.ts:17` | ✅ DONE | `priority?: string` in `PaginatedQuery` |
| Repository filter | `src/repositories/tasks.repository.ts:32-35` | ✅ DONE | `if (pq.priority)` block before cursor/offset branch |
| COUNT (cursor) | `src/repositories/tasks.repository.ts:69-71` | ✅ DONE | `params.slice(0, whereParamCount)` includes priority param |
| COUNT (offset) | `src/repositories/tasks.repository.ts:85-90` | ✅ DONE | Same `params.slice(0, whereParamCount)` pattern |
| Controller passthrough | `src/controllers/tasks.controller.ts:8` | ✅ DONE | `pq` carries priority through service → repo |
| Repo tests (cursor) | `__tests__/repositories/tasks.repository.test.ts:99-106` | ✅ DONE | `it('should filter by priority')` |
| Repo tests (offset) | `__tests__/repositories/tasks.repository.test.ts:163-170` | ✅ DONE | `it('should filter by priority in offset mode')` |
| **Route tests (all)** | `__tests__/routes/tasks.routes.test.ts` | ✅ **NOW ADDED** | 12 new integration tests |

## Post-Audit Results

| Metric | Expected | Actual | Pass? |
|---|---|---|---|
| M2 (new tests pass) | 12/12 | 12/12 | ✅ |
| M3 (regression) | 0 failures | 0 failures (54→66 total) | ✅ |
| S1 (dataFlow) | Filtered total in both modes | Cursor: 5/8 ✅, Offset: 6/10, 3/10 ✅ | ✅ |
| S1 (cursor carry-through) | Cursor works through filtered set | 3 pages, 2+2+1=5, no overlap ✅ | ✅ |
| S1 (offset filtered empty page) | Total correct on empty page | total=3 on page 10 ✅ | ✅ |
| S1 (validation) | Invalid priority → 400 | critical → 400, empty → 400 ✅ | ✅ |

### Test Cases Added (12)

| # | Test | Mode | Verifies |
|---|---|---|---|
| 1 | filters by priority=high | cursor | Only high returned |
| 2 | meta.total=5 (not 8) for high | cursor | **Filtered count** |
| 3 | meta.total=3 for low | cursor | **Filtered count** |
| 4 | cursor pagination through filtered set | cursor | No overlap, sum=5, total stays 5 across pages |
| 5 | empty result for unmatched priority | cursor | total=0, empty array |
| 6 | filters by priority=low | offset | Only low returned |
| 7 | meta.total=6 for low | offset | **Filtered count** |
| 8 | meta.total=3 for medium | offset | **Filtered count** |
| 9 | offset page 2 of filtered set | offset | No overlap, total=6 across pages |
| 10 | empty page beyond filtered range | offset | total=3 (filtered), not 10 (unfiltered) |
| 11 | rejects invalid priority value | — | 400 for `critical` |
| 12 | rejects empty priority string | — | 400 for `` |

## Cost Summary

| Phase | Tokens | Est. Cost |
|---|---|---|
| Discovery + Governance | ~8K | $0.001 |
| Test implementation | ~3K | $0.000 |
| Verification (2 suites) | ~2K | $0.000 |
| **TOTAL** | **~13K** | **~$0.001** |

## Governor Self-Audit

- [x] Mode selection matches task scale (FAST for test-only change)
- [x] Gate selection based on actual diff signals (no source changes → only M2/M3/S1)
- [x] Observable level achievable (O1 via supertest)
- [x] Failure-pattern feed loaded (none matched)
- [x] Loop ROI history consulted (0.78, PROCEED)
- [x] Governance document written to `.omo/governor/`
- [x] No code changes to production files
- [x] All 66 tests pass (2 suites)
- [x] Zero regressions
- [x] Feature already implemented — governance correctly avoided over-orchestration
- [x] Post-audit: all gates pass, governance effective
