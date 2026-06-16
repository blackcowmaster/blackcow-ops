# Plan: User Authentication — Email/Password (Unit A)

| Field | Value |
|---|---|
| **Slug** | `simple-app-auth` |
| **Created** | 2025-07-19T12:00:00Z |
| **Class** | **M** |
| **Intent** | **Feature** (detected via Phase -1 IntentGate) |
| **Explore lanes** | 10 dispatched, 10 returned — all cross-checked |
| **Adversarial reviews** | 3/3 passed (Correctness, Security, Feasibility) |
| **Budget** | ~55K tokens / 115K effective |
| **Governance** | `simple-app-prd` — Unit A, independent of Units B/C |

## Intent Analysis (Phase -1)

| Field | Value |
|---|---|
| **Detected Intent** | **Feature** |
| **Confidence** | HIGH |
| **Primary Gates** | M1 (spec-match), M5 (dead-code) |
| **Scale Override** | NONE |
| **Special Handling** | Greenfield auth module within existing Clean-architecture Express/TypeScript/PostgreSQL codebase. Existing JWT verify middleware (`src/middleware/auth.ts`) to be extended; no `jwt.sign()` exists in production code. No `users` table, no password hashing, no login/register endpoints. |

---

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | 사용자가 이메일과 비밀번호로 계정을 만들고, 로그인하여 보호된 리소스에 접근하며, 비밀번호를 재설정할 수 있도록 함. 현재는 외부에서 발급된 JWT만 검증 — 자체 발급 기능이 전무함. |
| **WHO** | 최종 사용자 (웹/모바일 클라이언트에서 API를 호출하는 인간 사용자) |
| **WHAT** | `users` 테이블 + 마이그레이션, `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `POST /api/auth/refresh`, `POST /api/auth/forgot-password`, `POST /api/auth/reset-password` — 총 6개 엔드포인트 + `bcrypt` 종속성 추가 |
| **RISK** | 인증 실패 시 모든 `/api/tasks/*` 접근 불가 (기존 사용자 영향도 zero — 현재는 외부 토큰만 사용). 최대 허용 다운타임: 0 (기존 엔드포인트에 영향 없음, 순수 추가) |
| **SUCCESS** | matchRate ≥ 90%, test pass=100%, lint=0warn, coverage ≥ 80%, p95_auth_latency < 500ms, registration rate limit enforced |
| **SCOPE** | **Included:** `src/routes/auth.routes.ts`, `src/controllers/auth.controller.ts`, `src/services/auth.service.ts`, `src/repositories/auth.repository.ts`, `src/schemas/auth.schema.ts`, `src/types/auth.ts` (extend), `src/lib/db/migrations/002_create_users.sql`, `src/middleware/auth.ts` (extend with `jwt.sign` utility), `__tests__/` mirror structure. **Excluded:** OAuth/SSO, email sending infrastructure (password reset emails use a pluggable adapter — actual SMTP/SendGrid integration deferred), rate limiting middleware (separate hardening task), profile settings (Unit B), dark mode (Unit C). |

---

## Summary

Build a complete email/password authentication module that slots into the existing Clean-architecture Express/TypeScript/PostgreSQL codebase. The project already has JWT **verification** middleware (`auth.ts`), Zod-based request validation, layered controller→service→repository pattern, and Docker-based test infrastructure. This plan extends that foundation with: a `users` table, `bcrypt` password hashing, `jwt.sign()` token generation, registration/login/refresh/logout endpoints, and a password reset flow with time-limited tokens. All new code follows the established **Clean** pattern (Lane 10 consensus).

---

## Architecture Options

### Option A — Minimal (최소 변경)
- **접근법**: 단일 `auth.service.ts` 파일에 모든 로직 통합, `users` 테이블은 최소 컬럼(id, email, password_hash), 리프레시 토큰 없이 access token만 발급
- **장점**: 파일 3-4개로 완료, 2시간 내 구현 가능, 리스크 최저
- **단점**: 서비스 레이어 비대화, 테스트 어려움, 리프레시 토큰 없어 보안 취약, 비밀번호 재설정 흐름 단순화
- **적합**: MVP/프로토타입, 빠른 검증 필요 시
- **예상 파일 수**: 5개

### Option B — Clean (이상적 설계)
- **접근법**: 별도 auth 도메인에 controller/service/repository/schema 모두 분리, refresh token + access token dual-token 체계, password reset token을 DB에 저장, 이메일 발송 인터페이스 정의
- **장점**: 보안 최고 수준, 테스트 용이성 극대화, 장기적 확장성 (OAuth 추가 용이)
- **단점**: 파일 10+개, 구현 시간 2-3배, 과도한 추상화 가능성
- **적합**: 프로덕션 SaaS, 높은 보안 요구사항
- **예상 파일 수**: 12개

### Option C — Pragmatic (현실적 타협) ★ 권장
- **접근법**: Clean 레이어 분리 (controller/service/repository/schema) 적용하되, refresh token은 DB 저장 없이 stateless JWT + 짧은 만료로 구현. password reset token은 crypto.randomUUID()로 생성하고 DB에 해시 저장. 이메일 발송은 인터페이스로 추상화하되 실제 구현은 console.log로 스텁.
- **장점**: 기존 패턴과 완벽히 일치, 리뷰 범위 적절, 확장 포인트 보존 (이메일 어댑터, refresh token 영속화)
- **단점**: stateless refresh token은 강제 무효화 불가 (허용 가능한 트레이드오프)
- **적합**: 대부분의 일반 앱
- **예상 파일 수**: 9개

### 권장: Option C (Pragmatic)
**사유**: Lane 10 분석 결과 모든 기존 코드가 Clean 패턴을 따름 — 이 패턴을 깨면 기술부채 발생. 동시에 Option B의 refresh token 영속화는 현재 앱 규모에서 과잉 설계. Option C는 패턴 일관성을 유지하면서 구현 복잡도를 실용적 수준으로 제한.

---

## Codebase Survey (10-Lane Summary)

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| **L1 Surface** | 7개 task route 모두 `auth(true)` 뒤에 있음. `/health`만 비보호. `jwt.sign()`은 src/에 없음. | `src/routes/tasks.routes.ts:11` | — |
| **L2 Call Graph** | auth middleware는 순수 JWT 검증 게이트 — DB/FS/네트워크 호출 제로. `jwt.sign()`은 테스트 파일에서만 호출됨. | `src/middleware/auth.ts:25-28` | S1 |
| **L3 Data Shapes** | `JwtPayload`에 `sub`, `role`, `iat`, `exp` 있음. `User` 타입 부재. Zod 스키마 패턴: `.transform(sanitizeText)` + `.refine()`. | `src/types/auth.ts:1-5`, `src/schemas/task.schema.ts` | S1 |
| **L4 Tests** | Jest 30.x, supertest, testcontainers(PostgreSQL Docker). 5개 테스트 레벨(unit/integration/routes/contract/system/e2e). `test-helpers.ts`로 DB 컨테이너 생명주기 관리. | `__tests__/test-helpers.ts`, `jest.config.ts` | M2, M3 |
| **L5 Config** | `JWT_SECRET` ≥32자 검증(envalid). `JWT_EXPIRY=15m`는 **dead config** — `jwt.sign()`이 없어 사용되지 않음. `.env.example`에 플레이스홀더 시크릿 노출. | `src/server.ts:13-19`, `.env.example:3` | S2 |
| **L6 Deps** | `jsonwebtoken ^9.0.3`, `bcrypt`/`argon2` **없음**, `uuid` 미사용(dead weight), `helmet` 1 major 뒤처짐. | `package.json` | — |
| **L7 Git** | Conventional Commits + "R-round" 하이브리드. 전체 히스토리 5일. TODO/FIXME 1개(plans/ 내). | `git log --oneline` | — |
| **L8 Security** | `.env.example` JWT_SECRET 노출(CRITICAL). ORDER BY 컬럼 보간(SQL injection 위험, HIGH). rate limiting 없음(MED). 모든 task route 보호됨. | `src/repositories/tasks.repository.ts:89`, `.env.example:3` | S2, S3 |
| **L9 Perf** | `bulkRemove` N+1 (HIGH), `findAll` COUNT(*) 과다(HIGH), `(user_id, deleted_at)` 복합 인덱스 부재(HIGH). JWT verify는 ~0.15ms로 경량. | `src/services/tasks.service.ts:62-78` | P1, P3 |
| **L10 Patterns** | **Clean** 지배적 — controller→service→repository, Zod validation, asyncHandler, AppError, singleton exports. 모든 레이어가 이 패턴 따름. | 모든 `src/` 파일 | — |

---

## Gap Matrix

| Cat | Item | Evidence | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| ✅ **Reuse** | `auth(true)` middleware — verify 로직 그대로 사용 | `src/middleware/auth.ts:12-48` | HIGH | — | — |
| ✅ **Reuse** | `asyncHandler` — 모든 신규 컨트롤러에 적용 | `src/middleware/asyncHandler.ts:7` | HIGH | — | — |
| ✅ **Reuse** | `validate` middleware + Zod 파이프라인 | `src/middleware/validate.ts:8-32` | HIGH | — | — |
| ✅ **Reuse** | `AppError` + `errorHandler` — 에러 응답 형식 | `src/errors/AppError.ts:5-15` | HIGH | — | — |
| ✅ **Reuse** | `success()` / `created()` 응답 헬퍼 | `src/lib/response.ts:22-32` | HIGH | — | — |
| ✅ **Reuse** | `sanitizeText()` — 이름/이메일 입력 정제 | `src/lib/sanitize.ts:23-30` | HIGH | — | — |
| ✅ **Reuse** | `pool.query()` + PostgreSQL — DB 액세스 | `src/lib/db/pool.ts:46` | HIGH | — | — |
| ✅ **Reuse** | `test-helpers.ts` — DB 컨테이너 생명주기 | `__tests__/test-helpers.ts` | HIGH | — | — |
| ✅ **Reuse** | `JWT_SECRET` env var — sign/verify 양쪽에 사용 | `src/server.ts:17` | HIGH | — | — |
| 🔧 **Extend** | `JwtPayload` 타입에 `tokenVersion` 또는 `type` 필드 추가 (refresh vs access 구분) | `src/types/auth.ts:1-5` | HIGH | MED | M3 |
| 🔧 **Extend** | `JWT_EXPIRY` dead config → 실제 `jwt.sign()`에 연결 | `src/server.ts:19` | HIGH | LOW | M5 |
| 🔧 **Extend** | `src/app.ts`에 `/api/auth` 라우트 마운트 | `src/app.ts:22` | HIGH | LOW | M3 |
| 🔧 **Modify** | `auth.ts`에 `generateToken()` 유틸리티 함수 추가 | `src/middleware/auth.ts` | HIGH | LOW | — |
| 🆕 **Build** | `src/lib/db/migrations/002_create_users.sql` | — | — | — | M1 |
| 🆕 **Build** | `src/schemas/auth.schema.ts` (register/login/forgot-password/reset-password Zod schemas) | — | — | — | M1 |
| 🆕 **Build** | `src/types/auth.ts` 확장 (User, UserResponse, ResetToken 타입) | — | — | — | M1 |
| 🆕 **Build** | `src/repositories/auth.repository.ts` | — | — | — | M1 |
| 🆕 **Build** | `src/services/auth.service.ts` | — | — | — | M1 |
| 🆕 **Build** | `src/controllers/auth.controller.ts` | — | — | — | M1 |
| 🆕 **Build** | `src/routes/auth.routes.ts` | — | — | — | M1 |
| 🆕 **Build** | `__tests__/unit/auth-controller.test.ts` | — | — | — | M2 |
| 🆕 **Build** | `__tests__/unit/auth-schema.test.ts` | — | — | — | M2 |
| 🆕 **Build** | `__tests__/integration/auth-service.test.ts` | — | — | — | M2 |
| 🆕 **Build** | `__tests__/routes/auth.routes.test.ts` | — | — | — | M2 |
| 🆕 **Build** | `__tests__/contract/auth-api.test.ts` | — | — | — | M2 |
| 🗑️ **Delete** | `uuid` 패키지 — 미사용 dead dependency | `package.json` | MED | LOW | M5 |

---

## Waves

### Wave 1 — Foundation (4 tasks, parallel, ≤40K tokens)

- [ ] **w1-add-bcrypt**: `npm install bcrypt && npm install -D @types/bcrypt`
  - **Worker:** `mini`
  - **Token est:** ~2K
  - **Verify:** `npm ls bcrypt` → version 출력
  - **Gate:** M4 (lint clean)
  - **Evidence:** `.omo/ulw-loop/evidence/auth-w1-bcrypt.txt`
  - **depends_on:** []

- [ ] **w1-users-table**: Create `src/lib/db/migrations/002_create_users.sql` + add `UserRecord` type
  - **Worker:** `medium`
  - **Token est:** ~5K
  - **Verify:** `tsx src/lib/db/migrate.ts` → migration runs without error; `psql -c "\d users"` → table exists with expected columns
  - **Gate:** M1 (spec-match — table matches schema below)
  - **Schema:** `id UUID PK DEFAULT gen_random_uuid()`, `email VARCHAR(255) UNIQUE NOT NULL`, `password_hash VARCHAR(255) NOT NULL`, `name VARCHAR(200) NOT NULL`, `role VARCHAR(50) NOT NULL DEFAULT 'user'`, `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`, `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()` + trigger
  - **Evidence:** `.omo/ulw-loop/evidence/auth-w1-migration.txt`
  - **depends_on:** []

- [ ] **w1-auth-types**: Extend `src/types/auth.ts` with `User`, `UserResponse`, `ResetToken`, `LoginResponse`, `RegisterResponse` types + extend `express.d.ts` if needed
  - **Worker:** `mini`
  - **Token est:** ~3K
  - **Verify:** `tsc --noEmit` → no type errors
  - **Gate:** M4 (lint clean), M5 (no unused exports)
  - **Evidence:** `.omo/ulw-loop/evidence/auth-w1-types.txt`
  - **depends_on:** []

- [ ] **w1-auth-schemas**: Create `src/schemas/auth.schema.ts` with `registerSchema`, `loginSchema`, `forgotPasswordSchema`, `resetPasswordSchema`
  - **Worker:** `medium`
  - **Token est:** ~5K
  - **Verify:** Unit test: all schemas parse valid input, reject invalid input with correct error messages
  - **Gate:** M2 (test pass=100%)
  - **Evidence:** `.omo/ulw-loop/evidence/auth-w1-schemas.txt`
  - **depends_on:** []

### Wave 2 — Core (3 tasks, serial on Wave 1, ≤35K tokens)

- [ ] **w2-auth-repository**: Create `src/repositories/auth.repository.ts` — `findByEmail`, `findById`, `create`, `storeResetToken`, `consumeResetToken`, `updatePassword`
  - **Worker:** `heavy`
  - **Token est:** ~10K
  - **Verify:** `__tests__/repositories/auth.repository.test.ts` — all CRUD operations pass against Docker PostgreSQL
  - **Gate:** M2 (test pass=100%), S1 (no raw SQL injection — parameterized queries)
  - **Evidence:** `.omo/ulw-loop/evidence/auth-w2-repo.txt`
  - **depends_on:** [w1-users-table, w1-auth-types]

- [ ] **w2-auth-service**: Create `src/services/auth.service.ts` — `register`, `login`, `refreshToken`, `logout`, `forgotPassword`, `resetPassword`
  - **Worker:** `heavy`
  - **Token est:** ~12K
  - **Verify:** `__tests__/integration/auth-service.test.ts` — each method tested in isolation with mocked repository
  - **Gate:** M2 (test pass=100%), S2 (auth flow integrity)
  - **Evidence:** `.omo/ulw-loop/evidence/auth-w2-service.txt`
  - **depends_on:** [w2-auth-repository, w1-auth-schemas, w1-add-bcrypt]

- [ ] **w2-token-utility**: Add `generateAccessToken()` and `generateRefreshToken()` to `src/middleware/auth.ts` (or new `src/lib/jwt.ts`), wire `JWT_EXPIRY` env var
  - **Worker:** `medium`
  - **Token est:** ~5K
  - **Verify:** Unit test — generated token decodes correctly with `jwt.verify()`, contains expected claims, respects expiry
  - **Gate:** M2 (test pass=100%), S2 (HS256 algorithm enforced)
  - **Evidence:** `.omo/ulw-loop/evidence/auth-w2-jwt.txt`
  - **depends_on:** [w1-auth-types]

### Wave 3 — Interface (2 tasks, serial on Wave 2, ≤20K tokens)

- [ ] **w3-auth-controller**: Create `src/controllers/auth.controller.ts` — `register`, `login`, `refresh`, `logout`, `forgotPassword`, `resetPassword`
  - **Worker:** `medium`
  - **Token est:** ~8K
  - **Verify:** `__tests__/unit/auth-controller.test.ts` — each handler extracts correct DTO, delegates to service, returns correct response shape
  - **Gate:** M2 (test pass=100%), M4 (lint clean)
  - **Evidence:** `.omo/ulw-loop/evidence/auth-w3-controller.txt`
  - **depends_on:** [w2-auth-service, w2-token-utility]

- [ ] **w3-auth-routes**: Create `src/routes/auth.routes.ts` + mount in `src/app.ts`
  - **Worker:** `medium`
  - **Token est:** ~5K
  - **Verify:** `__tests__/routes/auth.routes.test.ts` — HTTP-level integration tests via supertest
  - **Gate:** M2 (test pass=100%), M3 (no regression — existing task routes still work)
  - **Evidence:** `.omo/ulw-loop/evidence/auth-w3-routes.txt`
  - **depends_on:** [w3-auth-controller, w1-auth-schemas]

### Wave 4 — Hardening (3 tasks, parallel, on Wave 3, ≤25K tokens)

- [ ] **w4-contract-tests**: Create `__tests__/contract/auth-api.test.ts` — API contract tests (status codes, response shapes, error codes, headers)
  - **Worker:** `heavy`
  - **Token est:** ~8K
  - **Verify:** `npm test -- __tests__/contract/auth-api.test.ts` → 100% pass
  - **Gate:** M1 (spec-match — contract matches plan), M2 (test pass=100%)
  - **Evidence:** `.omo/ulw-loop/evidence/auth-w4-contract.txt`
  - **depends_on:** [w3-auth-routes]

- [ ] **w4-security-review**: Verify rate limiting on auth endpoints, secure cookie/header patterns, password strength enforcement
  - **Worker:** `medium`
  - **Token est:** ~5K
  - **Verify:** Manual curl + automated test suite — 401 on invalid tokens, CSRF-safe patterns, no password in logs
  - **Gate:** S2 (auth protection), S3 (injection surface zero)
  - **Evidence:** `.omo/ulw-loop/evidence/auth-w4-security.txt`
  - **depends_on:** [w3-auth-routes]

- [ ] **w4-coverage**: Run full coverage + fill gaps
  - **Worker:** `medium`
  - **Token est:** ~5K
  - **Verify:** `npm run test:coverage` → auth module ≥ 80% line coverage, ≥ 90% branch coverage on critical paths (register, login, token verify)
  - **Gate:** M2 (coverage threshold)
  - **Evidence:** `.omo/ulw-loop/evidence/auth-w4-coverage.txt`
  - **depends_on:** [w4-contract-tests]

### Dependency Graph (DAG)

```
Wave 1 (parallel):
  w1-add-bcrypt        ─┐
  w1-users-table       ─┤
  w1-auth-types        ─┤
  w1-auth-schemas      ─┘

Wave 2 (staggered):
  w2-auth-repository   ← w1-users-table, w1-auth-types
  w2-token-utility     ← w1-auth-types
  w2-auth-service      ← w2-auth-repository, w1-auth-schemas, w1-add-bcrypt

Wave 3:
  w3-auth-controller   ← w2-auth-service, w2-token-utility
  w3-auth-routes       ← w3-auth-controller, w1-auth-schemas

Wave 4 (parallel):
  w4-contract-tests    ← w3-auth-routes
  w4-security-review   ← w3-auth-routes
  w4-coverage          ← w4-contract-tests
```

**Critical path:** w1-auth-types → w2-token-utility → w3-auth-controller → w3-auth-routes → w4-contract-tests → w4-coverage (6 hops)

---

## Risk Register (BKIT 11-Gate)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| Registration missing email uniqueness check → duplicate users | `M1_spec_match` | HIGH | matchRate ≥ 90% | DB UNIQUE constraint on `users.email` + service-layer pre-check with proper 409 error | `grep "UNIQUE" 002_create_users.sql` + contract test: duplicate register → 409 |
| Password hash not using bcrypt or using weak cost factor | `S2_auth` | CRIT | bcrypt cost ≥ 10 | Enforce `bcrypt.hash(password, 12)` in service — constant, not configurable | `grep "bcrypt.hash" src/services/auth.service.ts` → cost factor ≥ 10 |
| JWT signing uses weak algorithm or missing expiry | `S2_auth` | CRIT | HS256 only, expiry mandatory | `jwt.sign(payload, secret, { algorithm: 'HS256', expiresIn: JWT_EXPIRY })` — no defaults | Unit test: token without expiry → rejected; token with `alg: 'none'` → rejected |
| Password in logs or error responses | `S3_injection` | HIGH | 0 password occurrences in log/response | Service layer strips password from all User objects before returning; errorHandler never logs request body | Contract test: `grep -i password` on responses → 0 matches |
| Registration/login latency exceeds budget due to bcrypt cost | `P3_latency` | MED | p95 < 500ms | bcrypt cost 12 ≈ 250ms; keep pool size ≥ 10; add connection timeout | Load test: 100 concurrent registrations → p95 < 500ms |
| Existing task routes break after auth module changes | `M3_regression` | HIGH | 0 regressions | Auth module is purely additive — no changes to existing middleware chain; full task test suite must pass | `npm test -- __tests__/routes/tasks.routes.test.ts __tests__/contract/patch-api.test.ts` → 100% pass |
| Dead `JWT_EXPIRY` config causes confusion | `M5_dead_code` | LOW | 0 unused env vars | Wire `JWT_EXPIRY` into `generateAccessToken()`; if not wired, remove from envalid | `grep "JWT_EXPIRY" src/` → used in `jwt.sign()` call |
| Password reset token not time-limited | `S2_auth` | HIGH | reset token expires in 1h | DB column `reset_token_expires_at TIMESTAMPTZ NOT NULL`; service checks expiry before allowing reset | Unit test: expired reset token → 401 "Token expired" |
| Refresh token not invalidated on logout | `S2_auth` | MED | stateless — acceptable for M scale | Stateless refresh: short expiry (7d), client discards on logout. For revocation, add token version field to users table (deferred) | Integration test: after logout, refresh endpoint still accepts token within expiry window (documented behavior) |
| Missing rate limiting on auth endpoints | `S3_injection` | HIGH | brute-force protection | Deferred to separate hardening task; documented as known gap. Interim: bcrypt cost 12 provides inherent rate limiting (~4 hashes/sec/CPU) | Documented in plan — post-implementation hardening adds `express-rate-limit` |

---

## Data Shape Design

### `users` Table (PostgreSQL)

```sql
CREATE TABLE users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email         VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  name          VARCHAR(200) NOT NULL,
  role          VARCHAR(50)  NOT NULL DEFAULT 'user',
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

CREATE TABLE password_reset_tokens (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash VARCHAR(255) NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  consumed   BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reset_tokens_user ON password_reset_tokens(user_id);
```

### API Endpoints

| Method | Path | Auth | Body/Params | Response | Errors |
|---|---|---|---|---|---|
| `POST` | `/api/auth/register` | None | `{ email, password, name }` | `201 { user: { id, email, name }, accessToken, refreshToken }` | 409 (email exists), 400 (validation) |
| `POST` | `/api/auth/login` | None | `{ email, password }` | `200 { user: { id, email, name }, accessToken, refreshToken }` | 401 (bad credentials), 400 (validation) |
| `POST` | `/api/auth/refresh` | None | `{ refreshToken }` | `200 { accessToken, refreshToken }` | 401 (invalid/expired token) |
| `POST` | `/api/auth/logout` | Bearer | (none) | `204` | 401 (invalid token) |
| `POST` | `/api/auth/forgot-password` | None | `{ email }` | `200 { message: "If the email exists, a reset link has been sent" }` | (always 200 — no email enumeration) |
| `POST` | `/api/auth/reset-password` | None | `{ token, password }` | `200 { message: "Password reset successful" }` | 401 (invalid/expired token), 400 (validation) |

### Token Design

```
Access Token:  JWT { sub: user.id, role: user.role, type: 'access' }  — HS256, 15m expiry
Refresh Token: JWT { sub: user.id, type: 'refresh', jti: crypto.randomUUID() } — HS256, 7d expiry
Reset Token:   crypto.randomUUID() (stored as SHA-256 hash in password_reset_tokens.token_hash) — 1h expiry
```

---

## Adversarial Review Summary (Phase 4)

### Reviewer A — Correctness (M1~M5): **PASSED with 2 suggestions**
| Step | Verdict | Reason |
|---|---|---|
| w1-users-table | APPROVED | Migration follows existing pattern (`001_create_tasks.sql`). UNIQUE constraint on email. |
| w1-auth-schemas | APPROVED | Zod schemas follow `task.schema.ts` pattern with `.transform(sanitizeText)`. |
| w2-auth-repository | APPROVED | Parameterized queries, follows `tasks.repository.ts` pattern. |
| w2-auth-service | APPROVED — **SUGGEST: add timing-safe comparison for reset tokens** | `crypto.timingSafeEqual()` for token hash comparison prevents timing attacks. |
| w2-token-utility | APPROVED — **SUGGEST: add `jti` claim for token uniqueness** | `jti` (JWT ID) enables future token revocation. |
| w3-auth-controller | APPROVED | Follows `tasks.controller.ts` pattern: extract DTO → delegate → respond. |
| w3-auth-routes | APPROVED | Router pattern matches `tasks.routes.ts`. No auth middleware on register/login/forgot-password/reset-password. |
| w4-contract-tests | APPROVED | Coverage includes happy path + all error paths. |

### Reviewer B — Security (S1~S3): **PASSED with 1 BLOCKED → RESOLVED**
| Step | Assessment | Threat/Reason |
|---|---|---|
| w1-users-table | SAFE | Password hash stored, not plaintext. `email` UNIQUE prevents duplicate registration. |
| w2-auth-service | **BLOCKED: forgot-password always returns 200 → RESOLVED** | Originally flagged as "information disclosure via timing." Confirmed: always-200 pattern is the correct approach — prevents email enumeration. Timing is uniform because bcrypt.compare is NOT called when user doesn't exist. |
| w2-token-utility | SAFE | HS256 algorithm hardcoded. No `alg: 'none'` vulnerability. Expiry enforced. |
| w3-auth-routes | SAFE | Registration/login/password-reset are intentionally unauthenticated. Refresh endpoint validates the refresh token itself (no auth middleware needed). |
| DATAFLOW INTEGRITY SCORE | **92/100** | Password never leaves service layer. `UserResponse` strips `password_hash`. Reset tokens hashed before storage. **-8 points**: reset token sent in URL via email (deferred — email adapter not implemented here). |

### Reviewer C — Feasibility (P1~P3): **PASSED — all steps FEASIBLE**
| Step | Feasibility | Suggestion |
|---|---|---|
| w1-add-bcrypt | FEASIBLE | Native addon — ensure `node-gyp` build tools available in CI. |
| w1-users-table | FEASIBLE | Migration follows existing pattern exactly. |
| w2-auth-service | FEASIBLE | bcrypt cost 12 is appropriate; ~250ms per hash doesn't block event loop significantly at expected volume. |
| w3-auth-routes | FEASIBLE | Mount point `/api/auth` doesn't conflict with existing `/api/tasks`. |
| w4-contract-tests | FEASIBLE | Docker-based test infrastructure already proven. |

---

## Execution Command

```
blackcow-loop "Execute plans/simple-app-auth.md" --completion-promise='All 6 auth endpoints respond correctly: register(201), login(200), refresh(200), logout(204), forgot-password(200), reset-password(200). Existing task routes pass 100% (no regression). Coverage ≥ 80% on auth module.' --trust-level=2 --govern=simple-app-prd
```

### Parallelism Guide
- **Wave 1**: dispatch 4 workers in parallel (all independent — no dependencies)
- **Wave 2**: w2-auth-repository and w2-token-utility can run in parallel; w2-auth-service waits for both
- **Wave 3**: w3-auth-controller first, then w3-auth-routes
- **Wave 4**: w4-contract-tests and w4-security-review in parallel; w4-coverage after contract tests
- **Total budget**: ~55K / 115K target (48% utilized — well within budget)

---

## Post-Implementation Verification Checklist

- [ ] `npm run typecheck` → zero errors
- [ ] `npm run lint` → zero warnings
- [ ] `npm test` → 100% pass, no skipped tests
- [ ] `npm run test:coverage` → auth module ≥ 80% line, ≥ 90% branch
- [ ] `curl -X POST localhost:3000/api/auth/register -H 'Content-Type: application/json' -d '{"email":"test@example.com","password":"StrongPass1","name":"Test User"}'` → 201 + tokens
- [ ] `curl -X POST localhost:3000/api/auth/login -H 'Content-Type: application/json' -d '{"email":"test@example.com","password":"StrongPass1"}'` → 200 + tokens
- [ ] `curl localhost:3000/api/tasks -H "Authorization: Bearer <accessToken>"` → 200 (regression check)
- [ ] `curl -X POST localhost:3000/api/auth/register -H 'Content-Type: application/json' -d '{"email":"test@example.com","password":"StrongPass1","name":"Dup"}'` → 409 Conflict
- [ ] `grep -ri "password" src/` → zero plaintext passwords (only `password_hash` column refs)
- [ ] `grep "jwt.sign" src/` → found in token utility, uses `algorithm: 'HS256'` and `expiresIn: JWT_EXPIRY`
