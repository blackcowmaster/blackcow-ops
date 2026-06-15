# Plan: Extract PaginationService from TasksRepository

| Field | Value |
|---|---|
| **Slug** | `extract-pagination-service` |
| **Created** | `2026-06-27T00:00:00Z` |
| **Class** | **M** (medium — single feature, 5 files changed, ~200 loc moved) |
| **Explore lanes** | 8 dispatched (L1–L7, L10), all returned, zero contradictions |
| **Adversarial reviews** | 3/3 (A/B/C — M-scale Quality intent) |
| **Budget** | estimated ~55K tokens / 128K effective (dynamic) |

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | `TasksRepository.findAll()` currently mixes raw SQL execution with pagination math (cursor parsing, offset calculation, nextCursor extraction), violating single-responsibility. Extracting pagination into a dedicated service keeps the repository focused on DB queries and makes pagination reusable. |
| **WHO** | `TasksRepository` consumers (TasksService → TasksController), future repositories needing pagination. |
| **WHAT** | New `src/lib/pagination.ts` with `PaginationService` class; slimmed `TasksRepository.findAll()` that delegates pagination math to the service; updated controller that delegates `hasMore` to the service. |
| **RISK** | Pagination is a critical data-access path. Regression risk is HIGH if cursor encoding/decoding changes. All 30 pagination tests (17 repo + 13 routes) must pass unchanged. Max acceptable downtime: 0 (test-gated). |
| **SUCCESS** | matchRate ≥ 90% (behavior-preserving), test pass=100% (`npm test`), lint=0warn (`npm run lint`), coverage ≥ 80%, p95_target_ms: N/A (no perf change expected) |
| **SCOPE** | **IN**: `src/repositories/tasks.repository.ts` (lines 28–104, findAll), `src/controllers/tasks.controller.ts` (lines 12–27, getAll), new `src/lib/pagination.ts`. **OUT**: All other repository methods (create, update, remove, bulkCreate, transaction, findById), test files, DB schema, middleware, config. |

## Summary

Extract the ~120 lines of pagination logic from `TasksRepository.findAll()` into a new `PaginationService` class at `src/lib/pagination.ts`. The repository retains raw SQL execution but receives cursor clauses, offset values, and sorting from the service. The controller's `hasMore` computation moves into the service alongside `nextCursor` extraction. All 30 existing pagination tests must pass without modification to their assertion logic — this is a strictly behavior-preserving refactor. The new service follows the established class+singleton pattern (`TasksRepository` / `TasksService`), uses `AppError` for domain errors, and imports `query` from `src/lib/db/pool.ts`.

## Architecture Options

### Option A — Minimal (서비스로 단순 이동)
- **접근법**: `findAll`의 cursor/offset 분기 전체를 PaginationService로 복사. Repository는 service가 반환한 SQL + params를 실행만 함.
- **장점**: 최소 변경, 리스크 최저. 기존 테스트 assertion을 하나도 변경하지 않음.
- **단점**: PaginationService가 SQL 문자열을 직접 조립하게 되어 Infrastructure 레이어 침범. 재사용성 낮음.
- **적합**: 긴급 핫픽스
- **예상 파일 수**: 3개

### Option B — Clean (범용 PaginationService)
- **접근법**: 테이블/컬럼을 파라미터로 받는 범용 `paginate<T>()` 메서드. Repository는 service에 table metadata + filters를 전달.
- **장점**: 모든 리소스에 재사용 가능, 높은 추상화. SQL 인젝션 방지를 위한 allowlist 검증 내장.
- **단점**: 기존 findAll의 동작을 완전히 재현하기 위해 많은 파라미터 필요. 추상화 오버헤드. 테스트가 간접적으로 영향받을 가능성.
- **적합**: 여러 리소스에 pagination이 필요한 대규모 프로젝트
- **예상 파일 수**: 3개 + types 확장

### Option C — Pragmatic (Task-specific, math-only extraction) ✅ 권장
- **접근법**: PaginationService는 순수 수학/변환 로직만 담당. Cursor 파싱, offset 계산, nextCursor 추출, hasMore 판단, cursor WHERE clause 문자열 생성. Repository는 service가 반환한 clause/params를 SQL에 주입하고 실행. SQL 자체는 repository에 남음.
- **장점**: Repository는 "raw SQL 실행"에 집중. Service는 "pagination math"에 집중. 기존 동작 완전 보존. 테스트 assertion 변경 최소화. 패턴 일관성 유지.
- **적합**: 이 리팩토링의 목표와 정확히 일치
- **예상 파일 수**: 3개

### 권장: Option C (Pragmatic)
**사유**: L10 분석 결과 코드베이스는 class+singleton 패턴을 일관되게 사용하며, `src/lib/response.ts`처럼 순수 유틸리티 모듈이 lib에 위치함. Option C는 이 패턴을 그대로 따르면서 "repository = raw queries, service = math"라는 요구사항을 가장 정확히 충족. Option B의 범용 추상화는 이 프로젝트 규모(단일 리소스)에서 과잉 설계.

## Codebase Survey (8-Lane Summary, Quality Intent)

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| Surface (L1) | Clean layered architecture: Interface→Application→Infrastructure. Controller directly computes `hasMore` (line 14-16) — this math must move. | `tasks.controller.ts:14-16` | — |
| Call Graph (L2) | `findAll` has 1 prod call site (`tasks.service.ts:8`) + 16 test call sites. Cursor building fully in repo (lines 38-80), offset in repo (83-104), hasMore in controller (14-16). | `tasks.repository.ts:38-104`, `tasks.controller.ts:14-16` | S1 (data flow) |
| Data Shapes (L3) | `PaginatedQuery` → `PaginationInput` (Zod) → `FindAllResult` → `ApiMeta`. Key transform: `nextCursor: string\|null` → `hasMore: boolean` + `cursor: string\|undefined`. Cursor format: `"<timestamptz-text>_<UUID>"`. | `api.ts:16-26`, `repository.ts:5-11`, `controller.ts:14-16` | S1 |
| Tests (L4) | 30 pagination tests (17 repo, 13 routes). Zero skipped/disabled. **No test directly unit-tests `hasMore` logic** — it's covered only by integration tests. Key gap: empty results in cursor mode, cursor injection, concurrent writes. | `repository.test.ts`, `routes.test.ts` | M2, M3 |
| Config (L5) | Default limit=25, max=100 hardcoded in Zod schema. No env overrides. No feature flags. Cursor delimiter `_` hardcoded in repo line 41. | `task.schema.ts:36-38` | — |
| Deps (L6) | All deps at latest. No pagination npm package installed. `uuid` package unused (can be removed separately). | `package.json` | — |
| Git (L7) | Simulation repo — `src/` is gitignored. Zero commit history for target files. Zero TODO/FIXME/HACK. | `.gitignore:21` | — |
| Patterns (L10) | Class+singleton export is the universal pattern (`TasksRepository`, `TasksService`). `src/lib/` contains utility modules (`response.ts`, `db/pool.ts`). Error handling: `AppError` for domain errors. | `repository.ts:13,155`, `service.ts:6,57` | M1 |

## Gap Matrix

| Cat | Item | Evidence | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| ✅ Reuse | `query()` from `src/lib/db/pool.ts` | `pool.ts:32` | HIGH | — | — |
| ✅ Reuse | `AppError` for invalid sort/cursor | `errors/AppError.ts` | HIGH | — | — |
| ✅ Reuse | `PaginatedQuery`, `FindAllResult`, `ApiMeta` types | `api.ts`, `repository.ts` | HIGH | — | — |
| 🔧 Modify | `TasksRepository.findAll()` — remove cursor/offset math, delegate to PaginationService | `repository.ts:28-104` | HIGH | HIGH | M3 (regression) |
| 🔧 Modify | `TasksController.getAll()` — delegate `hasMore` to PaginationService | `controller.ts:12-27` | HIGH | MED | M3 |
| 🔧 Modify | `FindAllResult` — keep in repo but confirm it still returns `nextCursor` (service computes it, repo returns it) | `repository.ts:5-11` | HIGH | LOW | M1 |
| 🆕 Build | `src/lib/pagination.ts` — `PaginationService` class | — | — | — | M1 (spec-match) |
| 🗑️ Delete | Cursor parsing logic (`lastIndexOf('_')`, `substring`) from repository | `repository.ts:41-47` | HIGH | LOW | M5 (dead-code) |
| 🗑️ Delete | Offset calculation (`(page-1)*limit`) from repository | `repository.ts:83` | HIGH | LOW | M5 |
| 🗑️ Delete | `_cursor` column stripping from repository | `repository.ts:69-72` | HIGH | LOW | M5 |
| 🗑️ Delete | `nextCursor` extraction from repository | `repository.ts:76-78` | HIGH | LOW | M5 |
| 🗑️ Delete | `hasMore` computation from controller | `controller.ts:14-16` | HIGH | MED | M3 |

## Waves

### Wave 1 — Foundation: PaginationService (2 tasks, parallel, ~40K tokens)

- [ ] **task-A**: Create `src/lib/pagination.ts` with `PaginationService` class
  - **Worker:** `heavy`
  - **Token est:** ~12K
  - **Files:** `src/lib/pagination.ts` (new)
  - **Action:** Create the service with these methods:
    1. `parseCursor(cursor: string): { createdAt: string; id: string }` — splits on last `_`, returns parts
    2. `buildCursorWhere(cursor: string | undefined, order: 'asc' | 'desc', paramIdx: number): { clause: string; params: unknown[]; nextIdx: number }` — returns `AND (t.created_at, t.id) > ($N, $N+1)` or empty string
    3. `buildCursorExpression(): string` — returns `t.created_at::text || '_' || t.id::text as _cursor`
    4. `extractNextCursor(rows: any[], limit: number): string | null` — returns last row's `_cursor` or null
    5. `stripCursorColumn(rows: any[]): any[]` — removes `_cursor` from each row
    6. `computeOffset(page: number, limit: number): number` — returns `(page-1) * limit`
    7. `computeHasMore(mode: 'cursor' | 'offset', nextCursor: string | null, page: number, limit: number, total: number): boolean` — cursor: `nextCursor !== null`, offset: `page * limit < total`
  - **Verify:** `npx tsc --noEmit` (typecheck passes)
  - **Gate:** M1 (spec-match), M4 (lint clean)
  - **Evidence:** `.omo/ulw-loop/evidence/extract-pagination-w1-a.txt`
  - **Pattern:** Follow `TasksService` class structure — no constructor, all async or pure methods, singleton export

- [ ] **task-B**: Update `src/types/api.ts` — add `PaginateParams` interface if needed, review `FindAllResult` compatibility
  - **Worker:** `mini`
  - **Token est:** ~4K
  - **Files:** `src/types/api.ts` (modify)
  - **Action:** Verify `FindAllResult.nextCursor: string | null` stays compatible with the new service. Add `CursorParts` type if needed: `{ createdAt: string; id: string }`. No breaking changes to existing types.
  - **Verify:** `npx tsc --noEmit`
  - **Gate:** M1 (spec-match)
  - **Evidence:** `.omo/ulw-loop/evidence/extract-pagination-w1-b.txt`

### Wave 2 — Core: Refactor Repository + Controller (2 tasks, serial on Wave 1, ~30K tokens)

- [ ] **task-C**: Refactor `TasksRepository.findAll()` to delegate pagination math to `PaginationService`
  - **Worker:** `heavy`
  - **Token est:** ~18K
  - **Files:** `src/repositories/tasks.repository.ts` (modify, lines 14-104)
  - **Action:**
    1. Import `paginationService` from `../lib/pagination`
    2. In `findAll()`:
       - Remove: cursor parsing (lines 41-47), cursor WHERE clause (lines 38-48), `_cursor` column concatenation in SELECT (line 52), `_cursor` stripping (lines 69-72), `nextCursor` extraction (lines 76-78), offset calculation (line 83)
       - Replace with calls to `paginationService`:
         - `const cursorClause = paginationService.buildCursorWhere(pq.cursor, pq.order, paramIdx)` → inject clause + params
         - `const cursorExpr = paginationService.buildCursorExpression()` → use in SELECT
         - `const offset = paginationService.computeOffset(pq.page, pq.limit)` → use in OFFSET
         - After query: `const tasks = paginationService.stripCursorColumn(result.rows)`
         - After query: `const nextCursor = paginationService.extractNextCursor(result.rows, pq.limit)`
    3. Keep unchanged: WHERE clause building (status/priority filters), ORDER BY, LIMIT, `Promise.all([query, countQuery])`, total count extraction
  - **Verify:** `npm test -- --testPathPattern="tasks.repository"` (all 17 repo tests pass)
  - **Gate:** M2 (test pass=100%), M3 (0 regressions)
  - **Evidence:** `.omo/ulw-loop/evidence/extract-pagination-w2-c.txt`

- [ ] **task-D**: Refactor `TasksController.getAll()` to delegate `hasMore` to `PaginationService`
  - **Worker:** `medium`
  - **Token est:** ~8K
  - **Files:** `src/controllers/tasks.controller.ts` (modify, lines 12-27)
  - **Action:**
    1. Import `paginationService` from `../lib/pagination`
    2. Replace lines 14-16:
       ```ts
       // Before:
       const hasMore = pq.mode === 'cursor'
         ? nextCursor !== null
         : pq.page * pq.limit < total;
       // After:
       const hasMore = paginationService.computeHasMore(pq.mode, nextCursor, pq.page, pq.limit, total);
       ```
    3. Everything else (destructuring, `taskToResponse`, `paginated()` call) stays identical
  - **Verify:** `npm test -- --testPathPattern="tasks.routes"` (all 13 pagination route tests pass)
  - **Gate:** M2 (test pass=100%), M3 (0 regressions)
  - **Evidence:** `.omo/ulw-loop/evidence/extract-pagination-w2-d.txt`

### Wave 3 — Hardening: Full Test Suite + Lint (1 task, serial on Wave 2, ~10K tokens)

- [ ] **task-E**: Run full test suite + lint + typecheck
  - **Worker:** `medium`
  - **Token est:** ~8K
  - **Files:** All modified files
  - **Action:**
    1. `npm test` — all 47 tests (30 pagination + 17 CRUD/auth/validation) must pass
    2. `npm run lint` — 0 warnings
    3. `npx tsc --noEmit` — 0 errors
    4. Verify no dead exports: `grep -r "PaginationService" src/` confirms it's only imported where needed, old pagination symbols removed from repository
  - **Verify:** All three commands exit 0
  - **Gate:** M2 (test pass=100%), M4 (lint 0warn), M5 (no dead code)
  - **Evidence:** `.omo/ulw-loop/evidence/extract-pagination-w3-e.txt`

## Risk Register (BKIT 11-Gate)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| Cursor parsing changes break keyset pagination | `M3_regression` | HIGH | 0 regressions | `parseCursor` must replicate exact `lastIndexOf('_')` + `substring` logic. Identical-timestamp test (repo line 92) must pass. | `npm test -- --testPathPattern="tasks.repository"` |
| Offset calculation changes shift pages | `M3_regression` | HIGH | 0 regressions | `computeOffset` must return `(page-1) * limit`. Offset mode tests (page overlap, partial last page, beyond-range) must pass. | `npm test -- --testPathPattern="tasks.routes"` |
| hasMore logic diverges between cursor/offset | `M3_regression` | HIGH | 0 regressions | `computeHasMore` must match exact controller logic: cursor→`nextCursor!==null`, offset→`page*limit<total`. | Route pagination tests |
| `_cursor` column leaks to API response | `S1_dataFlow` | MED | cursor never in response | `stripCursorColumn` must destructure `_cursor` out completely before returning. Test: `expect(res.body.data[0]._cursor).toBeUndefined()`. | `npm test -- --testPathPattern="tasks.routes"` |
| nextCursor null vs undefined mismatch | `M1_spec_match` | MED | matchRate ≥ 90% | Controller maps `nextCursor ?? undefined` — service must return `null` not `undefined`. `extractNextCursor` returns `string \| null`. | `npm test -- --testPathPattern="cursor"` |
| Lint errors in new file | `M4_lint_clean` | MED | 0 warnings | Follow existing code style: 2-space indent, single quotes, semicolons, trailing commas. Run `npm run lint:fix` after creation. | `npm run lint` |
| Dead pagination code left in repository | `M5_dead_code` | LOW | 0 unused exports | After refactor, grep repository for `lastIndexOf`, `_cursor`, `offset =` — none should remain. | `grep -n "lastIndexOf\|_cursor\|offset =" src/repositories/tasks.repository.ts` |
| Type imports reference moved symbols | `M1_spec_match` | LOW | tsc 0 errors | `FindAllResult` stays in repository. No new types exported from repository that consumers depended on. | `npx tsc --noEmit` |

## Execution Command

```
blackcow-loop "Execute plans/extract-pagination-service.md" --completion-promise='npm test passes 100%, npm run lint has 0 warnings, npx tsc --noEmit has 0 errors, all 30 pagination tests unchanged in assertion logic' --trust-level=2
```

### Parallelism Guide
- Wave 1: task-A || task-B (2 workers in parallel)
- Wave 2: task-C → then task-D (sequential — C must pass before D is meaningful, but D can start once C's test pattern is known)
- Wave 3: task-E (serial on Wave 2)
- Total budget: ~50K / 115K effective tokens
