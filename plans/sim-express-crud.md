# Plan: Express.js TypeScript CRUD API — Tasks Resource

| Field | Value |
|---|---|
| **Slug** | `sim-express-crud` |
| **Created** | 2026-06-27T18:00:00Z |
| **Class** | **M** |
| **Explore lanes** | 5/5 dispatched, all returned |
| **Adversarial reviews** | 3/3 passed, findings incorporated |
| **Active gates** | M1, S1, S2, S3, P1 (5/11) |
| **Budget** | ~55K tokens / 115K effective (48% utilized) |

---

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | 사용자가 할 일(tasks)을 생성·조회·수정·삭제할 수 있는 REST API 제공 |
| **WHO** | 인증된 사용자 (JWT Bearer 토큰 보유) — 개인 할 일 관리 |
| **WHAT** | Express.js + TypeScript + PostgreSQL 기반 tasks CRUD API (계획서만, 구현 없음) |
| **RISK** | 신규 프로젝트이므로 기존 회귀 없음. 인증 우회 시 타 사용자 task 노출 위험 (S2). SQL injection 시 데이터 손상 (S3) |
| **SUCCESS** | matchRate ≥ 90%, test pass=100%, lint=0warn, coverage ≥ 80%, 모든 쿼리 parameterized ($1/$2), 모든 엔드포인트 auth 보호 |
| **SCOPE** | 포함: tasks 리소스 전체 CRUD, JWT 인증, Zod 검증, PostgreSQL 저장. 제외: 사용자 관리(users CRUD), 프론트엔드, 배포 인프라, Swagger 문서화, refresh token |

---

## Summary

본 계획은 `tasks` 리소스에 대한 Express.js TypeScript CRUD API를 설계한다. JWT Bearer 인증(S2)으로 모든 엔드포인트를 보호하고, Zod 스키마 검증(S3)으로 입력을 방어하며, PostgreSQL parameterized 쿼리(S3/P1)로 SQL injection을 차단한다. 데이터 흐름(S1)은 **Request → JSON parser → Helmet/CORS → Auth middleware → Zod validation → Controller → Service → Repository(parameterized) → PostgreSQL**로 단방향 계층을 유지한다. 아키텍처는 **Pragmatic (Option C)** 을 채택: 핵심 경로(Controller→Service→Repository)는 Clean Architecture, 주변부(middleware, routes)는 Minimal 패턴을 따른다.

---

## Architecture Options

### Option A — Minimal (최소 변경)
- **접근법**: 단일 `app.ts` 파일에 모든 로직 배치, `pg` 직접 호출, 미들웨어 인라인 정의
- **장점**: 파일 수 최소 (3~4개), 빠른 프로토타이핑
- **단점**: 테스트 불가능, 확장성 없음, 코드 재사용 불가
- **적합**: 해커톤 데모, 개념 증명
- **예상 파일 수**: 3~5개

### Option B — Clean (이상적 설계)
- **접근법**: DDD 계층 분리 + 의존성 주입(DI 컨테이너) + Interface/Application/Domain/Infrastructure 4계층 + CQRS 패턴
- **장점**: 최대 테스트 용이성, 완벽한 계층 분리, 높은 확장성
- **단점**: 과도한 추상화 (단일 리소스 CRUD에 DI 컨테이너는 과잉), 초기 생산성 저하
- **적합**: 마이크로서비스 코어, 엔터프라이즈 시스템
- **예상 파일 수**: 20+개

### Option C — Pragmatic (권장) ✅
- **접근법**: Controller→Service→Repository 3계층 + 공통 미들웨어 분리. DI 없이 직접 import. 각 계층 단일 책임.
- **장점**: 테스트 가능 (Repository mock 가능), 명확한 책임 분리, 합리적인 파일 수
- **적합**: 대부분의 중간 규모 CRUD API
- **예상 파일 수**: 18~22개

### 권장: Option C (Pragmatic)
**사유**: 단일 리소스 CRUD에 과도한 추상화는 생산성을 떨어뜨린다. Option C는 테스트 용이성과 계층 분리를 확보하면서도 불필요한 DI 복잡성을 피한다. Lane 분석 결과 이 패턴이 Express.js TypeScript 생태계에서 가장 널리 채택된 방식이다.

---

## Codebase Survey (5-Lane Summary)

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| **DB Schema** | UUID PK + soft-delete(`deleted_at`) + custom ENUMs(`task_status`, `task_priority`) + 3 partial indexes + FK to `users(id)` | L1 explore | S1, P1 |
| **Routes** | `Router({ mergeParams: true })` + auth middleware applied router-wide + validate per-route | L2 explore | S2, S3 |
| **Auth** | JWT HS256 + `sub`(user UUID) + `role` in payload. `req.user` extension via `declare global`. | L3 explore | S2 |
| **Validation** | Zod: `createTaskSchema`, `updateTaskSchema`(≥1 field), `taskIdSchema`(UUID), `paginationSchema`(page/limit/sort) | L4 explore | S3 |
| **Repository** | `pg.Pool` + parameterized `$1/$2` + `RETURNING *` + `pool.connect()` transactions + N+1 prevention via `ANY($1::uuid[])` | L5 explore | P1 |

### Lane Contradictions Resolved

| # | Issue | L1 | L2/L4 | Resolution |
|---|---|---|---|---|
| 🔴 | Status enum values | `pending, in_progress, completed, archived` | `todo, in_progress, done` | **`todo, in_progress, done`** — simpler, 2/3 lane consensus |
| 🔴 | Priority enum values | `low, medium, high, urgent` | `low, medium, high` | **`low, medium, high`** — `urgent` 없이 충분 |
| 🔴 | ID type | UUID (PG `gen_random_uuid()`) | `number` (Repository 예제) | **UUID** — L1 DDL + L4 Zod `uuid()` 일치 |

### Reviewer Cross-Checks Incorporated

| Reviewer | Critical Finding | Resolution |
|---|---|---|
| RVA | No testing infrastructure → SUCCESS criteria unreachable | Added Wave 4 testing infra + jest/supertest/testcontainers |
| RVA | asyncHandler + errorHandler misordered (Wave4 → needed Wave2) | Moved to Wave 1 (Foundation) |
| RVA | Missing pagination Zod schema | Added `paginationSchema` to L4 + Wave 2 |
| RVB | BLOCKED: No CORS / Helmet / rate limiting | Added to Wave 2 (Helmet/CORS) + Wave 4 (rate-limit) |
| RVB | RISKY: JWT HS256, no algorithm enforcement, no exp | Added algorithm whitelist `[HS256]`, `exp` claim, token TTL=15min |
| RVB | RISKY: Error handler leaks stack traces/secrets | Added error sanitization — correlationId + generic messages only |
| RVB | S1 dataFlow score 52/100 → LOW at controller→service boundary | Added typed DTO contracts + response DTO whitelisting |
| RVC | RISKY: OFFSET pagination degrades at scale | Replaced with keyset (cursor) pagination as primary; OFFSET as fallback |
| RVC | RISKY: No pool health/error handling | Added `pool.on('error')`, `statement_timeout=30s`, `idleTimeoutMillis` |
| RVC | Missing: Default LIMIT, batch size cap, query logging | Added: default LIMIT=25, MAX batch 500, pg query duration logging |

---

## Gap Matrix

| Cat | Item | Evidence | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| 🆕 | `src/types/` — Task, CreateTaskDto, UpdateTaskDto, JwtPayload, ApiResponse, PaginatedQuery | Greenfield | — | — | M1, S1 |
| 🆕 | `src/schemas/task.schema.ts` — Zod schemas (createTask, updateTask, taskId, pagination) | Greenfield | — | — | S3 |
| 🆕 | `src/lib/db/pool.ts` — pg Pool with health handlers, statement_timeout | Greenfield | — | — | P1 |
| 🆕 | `src/lib/db/migrations/001_create_tasks.sql` — DDL with ENUMs, indexes, trigger | Greenfield | — | — | S1, P1 |
| 🆕 | `src/lib/response.ts` — Response envelope helpers + sanitization | Greenfield | — | — | S1 |
| 🆕 | `src/errors/AppError.ts` — Custom error class (statusCode + code + correlationId) | Greenfield | — | — | S1 |
| 🆕 | `src/middleware/auth.ts` — JWT verify + algorithm whitelist + req.user | Greenfield | — | — | S2 |
| 🆕 | `src/middleware/validate.ts` — Generic Zod validation middleware factory | Greenfield | — | — | S3 |
| 🆕 | `src/middleware/asyncHandler.ts` — Async error boundary wrapper | Greenfield | — | — | S1 |
| 🆕 | `src/middleware/errorHandler.ts` — Global error handler with sanitization | Greenfield | — | — | S1 |
| 🆕 | `src/repositories/tasks.repository.ts` — 5 CRUD methods, parameterized, keyset pagination | Greenfield | — | — | P1 |
| 🆕 | `src/services/tasks.service.ts` — Business logic (ownership, status transitions) | Greenfield | — | — | M1, S1 |
| 🆕 | `src/controllers/tasks.controller.ts` — Thin request/response mapping | Greenfield | — | — | M1 |
| 🆕 | `src/routes/tasks.routes.ts` — Route definitions with middleware chain | Greenfield | — | — | M1 |
| 🆕 | `src/app.ts` — Express bootstrap, middleware registration, router mount | Greenfield | — | — | M1 |
| 🆕 | `src/server.ts` — HTTP listen + env validation (envalid) | Greenfield | — | — | M1 |
| 🆕 | `__tests__/` — Jest + supertest + testcontainers (repo/service/route/e2e) | Greenfield | — | — | M1 |
| 🆕 | Tooling — ESLint + Prettier + tsconfig + jest.config + .env.example | Greenfield | — | — | M1 |

---

## Waves

### Wave 1 — Foundation (8 tasks, parallel, ~40K tokens)

- [ ] **w1-init**: `npm init` + install deps (`express`, `pg`, `zod`, `jsonwebtoken`, `helmet`, `cors`, `dotenv`, `envalid`, `uuid`) + devDeps (`typescript`, `@types/*`, `jest`, `ts-jest`, `@types/jest`, `supertest`, `@types/supertest`, `testcontainers`, `eslint`, `prettier`, `tsx`)
  - **Worker:** medium
  - **Verify:** `npm ls express pg zod jsonwebtoken helmet cors dotenv envalid 2>&1 | grep -c "UNMET" → 0`
  - **Gate:** M1 (deps installed)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-w1-init.txt`

- [ ] **w1-config**: Write `tsconfig.json` (strict mode, ES2022, `src/` root, `outDir: dist`), `.eslintrc.json` (typescript-eslint recommended), `.prettierrc`, `.env.example` (DATABASE_URL, JWT_SECRET, PORT, JWT_EXPIRY), `jest.config.ts` (ts-jest, coverage threshold 80%)
  - **Worker:** light
  - **Verify:** `npx tsc --noEmit 2>&1 | grep -c "error" → 0` (after initial .ts files exist), `npx eslint --init` config readable
  - **Gate:** M1 (project configured)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-w1-config.txt`

- [ ] **w1-types**: Write `src/types/express.d.ts` (Request.user extension), `src/types/api.ts` (ApiResponse<T>, ApiMeta, PaginatedQuery), `src/types/task.ts` (Task, CreateTaskDto, UpdateTaskDto with `export type`), `src/types/auth.ts` (JwtPayload, User, AuthMiddlewareOptions)
  - **Worker:** light
  - **Verify:** `npx tsc --noEmit` — no type errors on type files
  - **Gate:** M1, S1 (typed contracts established)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-w1-types.txt`

- [ ] **w1-errors**: Write `src/errors/AppError.ts` (statusCode: number, code: string, message: string, correlationId: string), `src/middleware/asyncHandler.ts` (Promise.resolve wrapper → `.catch(next)`), `src/middleware/errorHandler.ts` (AppError → sanitized JSON, unknown → generic 500 with correlationId, console.error only correlationId — never full error object)
  - **Worker:** medium
  - **Verify:** Unit test: `new AppError(404, 'NOT_FOUND', 'msg')` → statusCode=404, code='NOT_FOUND'. Error handler returns `{ data:null, error:'Internal server error', meta:{ correlationId }}` for unknown errors.
  - **Gate:** M1, S1 (error sanitization — no stack trace leakage)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-w1-errors.txt`

- [ ] **w1-schemas**: Write `src/schemas/task.schema.ts` — `createTaskSchema` (title: 1-200 required, description: 0-5000 optional, status: enum optional, priority: enum optional, due_date: ISO8601 optional), `updateTaskSchema` (all optional, `.refine()` at least 1 field), `taskIdSchema` (id: uuid), `paginationSchema` (page: int ≥1 default 1, limit: int 1-100 default 25, sort_by: enum ['created_at','due_date','priority','title'] default 'created_at', order: enum ['asc','desc'] default 'desc', status: enum optional, priority: enum optional)
  - **Worker:** medium
  - **Verify:** `npx tsx -e "import {createTaskSchema} from './src/schemas/task.schema'; console.log(createTaskSchema.safeParse({title:'x'}))"` → success; same with `{title:''}` → error; same with `{}` → error
  - **Gate:** S3 (Zod schemas cover all input surfaces)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-w1-schemas.txt`

- [ ] **w1-db-migration**: Write `src/lib/db/pool.ts` (pg.Pool with `pool.on('error')`, `statement_timeout: '30s'`, `idleTimeoutMillis: 30000`, `connectionTimeoutMillis: 5000`, `max: 10`) + `src/lib/db/migrations/001_create_tasks.sql` (ENUMs task_status/task_priority, tasks table with all columns + constraints + 3 partial indexes + updated_at trigger + soft delete) + migration runner script (`src/lib/db/migrate.ts`)
  - **Worker:** heavy
  - **Verify:** `npx tsx src/lib/db/migrate.ts` → creates table with `\dt tasks` in psql; `SELECT indexname FROM pg_indexes WHERE tablename='tasks'` → 4+ indexes
  - **Gate:** S1, P1 (schema + indexes deployed)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-w1-db.txt`

- [ ] **w1-lib-response**: Write `src/lib/response.ts` — `success<T>()`, `created<T>()`, `noContent()`, `paginated<T>()` with response envelope `{ data, error, meta }`. Include response DTO mapper: strip `deleted_at`, `user_id` from public responses.
  - **Worker:** light
  - **Verify:** Unit test: `success(res, {id:'x'})` → `{ data:{id:'x'}, error:null }`; `paginated(res, items, {page:1, limit:25, total:100, totalPages:4})` → correct envelope
  - **Gate:** S1 (output sanitization — no internal fields leaked)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-w1-response.txt`

- [ ] **w1-env-validate**: Write `src/server.ts` with `envalid` env validation: `DATABASE_URL` (str), `JWT_SECRET` (str, min 32 chars), `PORT` (num, default 3000), `JWT_EXPIRY` (str, default '15m'). Fail-fast on missing vars.
  - **Worker:** light
  - **Verify:** `JWT_SECRET=short npx tsx src/server.ts` → exits with error before listen
  - **Gate:** S2 (secrets validated at startup)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-w1-env.txt`

---

### Wave 2 — Core (5 tasks, parallel on Wave 1, ~25K tokens)

- [ ] **w2-auth**: Write `src/middleware/auth.ts` — JWT verify with `algorithms: ['HS256']` (whitelist enforced), extract `sub` + `role`, attach `req.user`. Reject missing/expired/invalid tokens → 401. Optional `required` flag. Validate `exp` claim — reject expired tokens.
  - **Worker:** heavy
  - **Verify:** Unit test: valid token → `req.user.sub` set; expired token → 401; `alg:none` token → 401 (rejected); missing header → 401
  - **Gate:** S2 (JWT hardened — algorithm enforced, expiry checked)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-w2-auth.txt`

- [ ] **w2-validate-middleware**: Write `src/middleware/validate.ts` — generic `validate(schema, source)` factory. Validates `req[source]` against Zod schema, returns `{ errors: [{ field, message }] }` on failure (400). On success, replaces `req[source]` with parsed (defaulted) data.
  - **Worker:** medium
  - **Verify:** Unit test: POST with invalid body → 400 + `{ errors: [...] }`; valid body → next() called, req.body has defaults
  - **Gate:** S3 (all input validated before controller)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-w2-validate.txt`

- [ ] **w2-repository**: Write `src/repositories/tasks.repository.ts` — 5 methods: `findAll(userId, pagination)` (keyset cursor pagination with `WHERE (created_at, id) < ($1, $2)` + LIMIT, also OFFSET fallback), `findById(id, userId)` (WHERE id=$1 AND user_id=$2 AND deleted_at IS NULL), `create(dto, userId)` (INSERT RETURNING *), `update(id, userId, dto)` (dynamic SET clause — parameterized, UPDATE RETURNING *), `remove(id, userId)` (soft-delete: UPDATE SET deleted_at=NOW() RETURNING *). All queries: `AND deleted_at IS NULL`. Transaction helper for multi-statement ops.
  - **Worker:** heavy
  - **Verify:** Integration test (testcontainers): create → returns Task with UUID; findById → matches; update → title changed; remove → deleted_at IS NOT NULL; findAll → keyset pagination returns correct page
  - **Gate:** P1 (parameterized queries, no N+1, keyset pagination)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-w2-repo.txt`

- [ ] **w2-security-headers**: Write Helmet + CORS config in `src/app.ts`. Helmet with defaults. CORS: whitelist origin from `ALLOWED_ORIGINS` env var (comma-separated). `express.json({ limit: '100kb' })` — body size limit.
  - **Worker:** light
  - **Verify:** curl → response includes `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`. CORS preflight returns correct `Access-Control-Allow-Origin`.
  - **Gate:** S3 (security headers + body size limit)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-w2-security.txt`

- [ ] **w2-app-bootstrap**: Write `src/app.ts` — Express app creation + middleware registration order: `express.json({limit:'100kb'})` → `helmet()` → `cors()` → `auth()` (optional: false) → routes → `errorHandler` (last). Mount `src/routes/index.ts`.
  - **Worker:** medium
  - **Verify:** `npx tsc --noEmit` — app.ts compiles; `node -e "require('./dist/app')"` — no crash on import
  - **Gate:** M1, S1 (middleware chain order correct)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-w2-app.txt`

---

### Wave 3 — Integration (4 tasks, serial on Wave 2, ~15K tokens)

- [ ] **w3-service**: Write `src/services/tasks.service.ts` — `getAll(userId, query)` → calls repo.findAll, `getById(id, userId)` → calls repo.findById + throw AppError(404) if null, `create(dto, userId)` → calls repo.create, `update(id, userId, dto)` → repo.findById check ownership → repo.update, `remove(id, userId)` → repo.findById check ownership → repo.remove. Ownership check: `task.user_id !== userId → AppError(403, 'FORBIDDEN')`.
  - **Worker:** heavy
  - **Verify:** Unit test (mock repo): getById with non-existent → throws AppError(404); update with wrong userId → AppError(403); create → calls repo.create with userId
  - **Gate:** M1, S1 (business logic + ownership enforcement)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-w3-service.txt`

- [ ] **w3-controller**: Write `src/controllers/tasks.controller.ts` — 5 handlers, all wrapped with asyncHandler: `getAll` (parse pagination, call service, response: paginated), `getById` (call service, response: success), `create` (call service, response: created, 201), `update` (call service, response: success), `remove` (call service, response: noContent, 204). Controller does NO business logic — pure mapping.
  - **Worker:** medium
  - **Verify:** Unit test (mock service): getAll → response has `{ data: [...], meta: {...} }`; create → 201; remove → 204; getById with bad UUID → 400 from validation middleware (tested in route test)
  - **Gate:** M1 (controllers thin, no logic)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-w3-controller.txt`

- [ ] **w3-routes**: Write `src/routes/tasks.routes.ts` — Router with `router.use(auth())` applied to all routes. Each route: `validate(params)` → `validate(body/query)` → `asyncHandler(controller.method)`. GET / has `validate({query: paginationSchema})`. POST / has `validate({body: createTaskSchema})`. PUT /:id has `validate({params: taskIdSchema, body: updateTaskSchema})`. DELETE /:id has `validate({params: taskIdSchema})`.
  - **Worker:** medium
  - **Verify:** Route test (supertest + testcontainers): GET /api/tasks without auth → 401; GET /api/tasks/:id with invalid UUID → 400; POST with empty body → 400
  - **Gate:** S2, S3 (auth + validation on every route)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-w3-routes.txt`

- [ ] **w3-server-finalize**: Finalize `src/server.ts` — import app, env validation via envalid, `app.listen(env.PORT)`, graceful shutdown on SIGTERM (pool.end()). Query logging: `pool.on('query', (q) => ...)` for P1 observability.
  - **Worker:** light
  - **Verify:** `npm run dev` → server starts, `curl localhost:3000/api/tasks` → 401 (auth required), not crash
  - **Gate:** M1, P1 (server runs, query logging active)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-w3-server.txt`

---

### Wave 4 — Hardening (4 tasks, parallel on Wave 3, ~15K tokens)

- [ ] **w4-rate-limit**: Add `express-rate-limit` to `src/app.ts` — 100 req/15min per IP on `/api/` routes. Separate stricter limit on auth-related routes if any.
  - **Worker:** light
  - **Verify:** curl 101 times in 15min → 429 Too Many Requests
  - **Gate:** S3 (DoS protection)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-w4-ratelimit.txt`

- [ ] **w4-tests-repo**: Write `__tests__/repositories/tasks.repository.test.ts` — testcontainers PostgreSQL, run migration before all, seed data, test all 5 CRUD methods, keyset pagination with edge cases, soft-delete filter, transaction rollback on error, batch size cap (500 UUIDs)
  - **Worker:** heavy
  - **Verify:** `npx jest __tests__/repositories/ --coverage` → all pass, coverage ≥ 80% on repository
  - **Gate:** P1, M1 (repository verified)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-w4-repo-tests.txt`

- [ ] **w4-tests-integration**: Write `__tests__/routes/tasks.routes.test.ts` — supertest + testcontainers, test all 5 endpoints with valid/invalid auth, valid/invalid input, ownership checks, pagination, error responses
  - **Worker:** heavy
  - **Verify:** `npx jest __tests__/routes/ --coverage` → all pass, coverage ≥ 80% on routes/controllers/services
  - **Gate:** M1, S1, S2, S3 (integration verified)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-w4-integration-tests.txt`

- [ ] **w4-lint-finalize**: Run `npx eslint src/ --max-warnings 0`, `npx prettier --check src/`, `npx tsc --noEmit`. Fix all warnings. Add `npm run lint`, `npm run test`, `npm run build` scripts to `package.json`.
  - **Worker:** light
  - **Verify:** `npm run lint` → exit 0; `npm run test` → 100% pass, coverage ≥ 80%; `npm run build` → exit 0
  - **Gate:** M1 (lint=0warn, test pass=100%, coverage ≥ 80%)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-w4-lint.txt`

---

## Risk Register (BKIT 11-Gate Taxonomy)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| API 스펙과 구현 불일치 | **M1_spec_match** | HIGH | matchRate ≥ 90% | gap-detector: controller method → route → schema → repo method trace | 각 엔드포인트 curl + 응답 스키마 검증 |
| 테스트 실패 | **M2_test_pass** | HIGH | passRate = 100% | Wave 4에서 repo + integration 테스트 작성 | `npm test` |
| SQL injection — string concat | **S3_injection** | CRIT | 모든 쿼리 parameterized | Zod 검증 + pg $1/$2 + 코드리뷰에서 string concat grep | `grep -rn '`.*\${' src/repositories/` → 0 matches |
| 인증 우회 — alg:none attack | **S2_auth** | CRIT | 모든 토큰 HS256 강제 | `jwt.verify(token, secret, { algorithms: ['HS256'] })` | test: alg=none 토큰 → 401 |
| 인증 우회 — 만료 토큰 | **S2_auth** | HIGH | 모든 토큰 exp 확인 | JWT_EXPIRY=15m + jwt.verify 자동 exp 체크 | test: 만료 토큰 → 401 "Token expired" |
| 데이터 흐름 손상 — 타입 손실 | **S1_dataFlow** | MED | integrity ≥ 85% | Zod infer → DTO type → Service → Repository type contract | Controller tests check response shape matches Task type |
| 응답에 내부 필드 노출 | **S1_dataFlow** | MED | deleted_at, user_id 제외 | Response DTO mapper in `src/lib/response.ts` | test: GET /tasks 응답에 deleted_at 없음 |
| N+1 쿼리 | **P1_query** | MED | 리스트 조회 시 단일 쿼리 | keyset pagination + COUNT(*) 병렬 쿼리 | Query count assertion in repo test |
| OFFSET 성능 저하 | **P1_query** | MED | keyset pagination primary | OFFSET fallback only, keyset pagination 기본 | Load test: 1000+ rows → keyset latency < OFFSET latency |
| Connection pool 고갈 | **P1_query** | MED | pool.max=10 + rate-limit | pool.on('error') + statement_timeout + rate-limit | Integration test: concurrent requests ≤ pool.max |
| 오류 응답에 스택 트레이스 누출 | **S1_dataFlow** | HIGH | 모든 오류 sanitized | errorHandler: AppError만 메시지 전달, unknown → generic + correlationId | test: throw new Error('secret') → response에 'secret' 없음 |
| Body parser DoS | **S3_injection** | MED | body size limit | `express.json({ limit: '100kb' })` + rate-limit | test: 200KB body → 413 Payload Too Large |
| 무제한 배치 쿼리 | **P1_query** | LOW | ANY($1) batch ≤ 500 | Zod validation에서 배열 길이 cap | test: 501 UUIDs → 400 validation error |
| 환경변수 누락으로 조용한 실패 | **S2_auth** | HIGH | startup 시 envalid fail-fast | envalid가 DATABASE_URL, JWT_SECRET 검증 | test: JWT_SECRET 없이 시작 → exit code ≠ 0 |

---

## Execution Command

```
blackcow-loop "Execute plans/sim-express-crud.md" --completion-promise='All 5 CRUD endpoints pass integration tests with auth+validation, lint=0warn, coverage≥80%, all queries parameterized, no internal fields leaked' --trust-level=2
```

### Parallelism Guide
- **Wave 1**: 8 tasks in parallel → Foundation (types, schemas, errors, db, response, env, config, deps)
- **Wave 2**: 5 tasks in parallel → Core (auth, validate, repository, security-headers, app)
- **Wave 3**: 4 tasks sequential on Wave 2 → Integration (service → controller → routes → server)
- **Wave 4**: 4 tasks parallel on Wave 3 → Hardening (rate-limit, repo-tests, integration-tests, lint)
- **Total budget**: ~95K / 115K effective (83% utilized)
