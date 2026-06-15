# Plan: Production Hardening — Express 5 CRUD API

| Field | Value |
|---|---|
| **Slug** | `production-hardening` |
| **Created** | 2026-06-27T20:00:00Z |
| **Class** | **M** |
| **Explore lanes** | 9 dispatched, 9 returned (L9 skipped — Quality intent) |
| **Adversarial reviews** | 3/3 passed, findings incorporated |
| **Active gates** | M3, M4, M5, S1, S2, S3 (plus P1 for H3/M4) |
| **Budget** | ~75K tokens / 115K effective (65% utilized) |

---

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | 기능적으로 동작하는 Express 5 CRUD API에 19개의 프로덕션 갭이 존재 — 인증 우회, DoS, 로깅 부재, 운영 미성숙도 해결 필요 |
| **WHO** | 운영팀(SRE), 보안 감사자, 온콜 엔지니어 — 로그·메트릭·헬스체크를 통해 시스템 상태를 관측 가능해야 함 |
| **WHAT** | 4개 웨이브로 구성된 프로덕션 하드닝: rate limiting, JWT 하드닝, structured logging, graceful shutdown, pool 튜닝, API 버저닝, audit logging, Docker/CI |
| **RISK** | C1(rate limit)·C2(JWT fallback)·C3(timeout) 미적용 시 DoS + 인증 우회 가능. 기존 39개 테스트 중 1개 실패(H4). 변경 범위: 8개 소스 파일 + 2개 테스트 파일 + package.json |
| **SUCCESS** | 모든 38개(+) 테스트 통과(test pass=100%), lint=0warn, rate-limit 429 응답 확인, /health가 DB 상태 반영, structured log에서 Authorization 헤더 제외 확인, graceful shutdown 시 활성 연결 0 |
| **SCOPE** | 포함: app.ts, server.ts, auth.ts, pool.ts, errorHandler.ts, tasks.controller.ts, tasks.routes.ts, __tests__/*. 제외: 신규 기능 추가, DB 스키마 변경, 프론트엔드, 사용자 관리 |

---

## Summary

본 계획은 사전 감사에서 식별된 19개 프로덕션 갭을 4단계 웨이브로 해결한다. **Wave 1(CRITICAL)** 은 인증 우회·DoS·IP 신뢰·요청 타임아웃을 즉시 차단하고, **Wave 2(HIGH)** 는 구조화 로깅·그레이스풀 셧다운·헬스체크 DB 핑·깨진 테스트 수정으로 운영 가시성을 확보한다. **Wave 3(MEDIUM)** 은 압축·요청 ID 전파·Pool 환경변수·DB 재연결·API 버저닝·감사 로깅으로 운영 성숙도를 높이고, **Wave 4(LOW)** 는 Prometheus·Docker·CI/CD 등 배포 인프라를 구축한다. 아키텍처는 기존 Pragmatic 패턴을 그대로 유지하며, 각 변경은 최소 침습적(minimal diff)으로 적용된다.

---

## Architecture Options

### Option A — Minimal (개별 파일 패치)
- **접근법**: 각 갭을 독립적 패치로 적용. 파일 간 의존성 최소화, 웨이브 내 병렬화 극대화
- **장점**: 리스크 최저, 리뷰 범위 협소, 롤백 용이
- **단점**: 일관된 패턴 부재 (예: 모든 로깅이 pino로 통일되지 않을 수 있음)
- **적합**: 핫픽스, 긴급 패치
- **예상 파일 수**: 10~12개

### Option B — Clean (전면 아키텍처 개선)
- **접근법**: DI 컨테이너 도입, 미들웨어 체인 재설계, 모든 설정 중앙화, 로거/메트릭 추상화 계층
- **장점**: 최대 일관성, 장기 유지보수성, 모든 갭이 아키텍처 수준에서 해결
- **단점**: 변경 범위 과도 (20+ 파일), 기존 기능 회귀 위험, 웨이브 간 의존성 복잡
- **적합**: 메이저 버전 업그레이드, 팀 확장 시점
- **예상 파일 수**: 20+개

### Option C — Pragmatic (권장) ✅
- **접근법**: 기존 패턴과 파일 구조를 유지하며 각 갭을 최소 변경으로 해결. 개별 파일 패치지만 일관된 규칙 적용 (모든 로깅 → pino, 모든 타임아웃 → server.ts, 모든 설정 → envalid)
- **장점**: 리스크·일관성·속도의 균형, 기존 38개 합격 테스트 보존, 리뷰어 부담 최소
- **적합**: 프로덕션 직전 하드닝
- **예상 파일 수**: 12~15개

### 권장: Option C (Pragmatic)
**사유**: Lane 10 분석 결과 기존 코드베이스는 factory-function 미들웨어 + singleton pool + envalid 검증의 일관된 패턴을 이미 따르고 있다. Option C는 이 패턴을 확장하여 각 갭을 해결한다. Reviewer C의 지적대로 M5(API 버저닝)는 실익이 낮아 연기 권장되나, 계획에 포함한다.

---

## Codebase Survey (9-Lane Summary)

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| **L1 — Surface** | 미들웨어 체인: json→helmet→cors→(/health 분기)→auth→validate→controller. `/health`는 auth 없음. auth.ts는 `process.env` 직접 읽음 (envalid 우회). | explore lane 1 | S2 |
| **L2 — Call Graph** | JWT_SECRET fallback `'dev-secret-change-me'`는 20자 — envalid ≥32자 검증을 우회. SIGTERM 핸들러는 `server.close()`만 호출 — `closeIdleConnections()` 누락. `/health`는 DB ping 없음. | explore lane 2 + cross-check | S2, P1 |
| **L3 — Data Shapes** | Task→TaskResponse 변환 시 `user_id` + `deleted_at` 제외 (올바름). 그러나 `toJSON()` 가드 없음 — 실수로 `res.json(task)` 시 내부 필드 노출 위험. `req.user!.sub` non-null assertion. | explore lane 3 | S1 |
| **L4 — Tests** | 39개 테스트 (repo 17, routes 22). 1개 실패: "should handle identical timestamps in keyset pagination" — `timestamptz::text`의 세션 타임존 의존성. `to_char()` 사용으로 고정 가능. | explore lane 4 | M2 |
| **L5 — Config** | 이중 설정 경로: `server.ts`(envalid) + `auth.ts`/`pool.ts`/`app.ts`(process.env 직접). JWT_EXPIRY dead config. Pool max/idleTimeout/etc 하드코딩. `JWT_SECRET` 평문 폴백 심각. | explore lane 5 | S2 |
| **L6 — Dependencies** | express-rate-limit 8.5.2 (Express 5 호환), pino 10.3.1 + pino-http (Express 5 호환), compression 1.8.1 (호환). 모든 기존 의존성 보안 권고 없음 (jsonwebtoken v9.0.3은 CVE 패치됨). Redis store는 프로덕션에서 rate-limit에 필요. | explore lane 6 | — |
| **L7 — Git** | 커밋 74+ 라운드. TODO/FIXME/HACK 0개 (제로 톨러런스). F-003 OPEN: service.remove/update의 403 소유권 검사가 도달 불가능 (findById가 이미 user_id 필터링). `src/` 디렉토리가 .gitignore에 있음 — 시뮬레이션 생성 코드. | explore lane 7 | M5 |
| **L8 — Security** | 4개 Critical/High 발견: ① JWT fallback `dev-secret-change-me` (S2), ② trust proxy 누락 (S3), ③ rate limit 부재 (S1), ④ HTTP 타임아웃 부재 (S2). errorHandler 스택트레이스 sanitize 양호. /health 정보 누출 없음. | explore lane 8 | S1,S2,S3 |
| **L10 — Patterns** | 미들웨어는 factory function 패턴: `export function name(config?) { return (req,res,next) => {...} }`. 오류는 AppError throw 또는 next(err). Singleton pool: module-level `let _pool` + guard. Plan 템플릿: Context Anchor + Gap Matrix + Waves + Risk Register. | explore lane 10 | — |

---

## Gap Matrix

| Cat | Item | Evidence | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| 🔧 | `auth.ts:6` — JWT_SECRET fallback `\|\| 'dev-secret-change-me'` 제거 | L8/L5/L2 확인 | HIGH | **CRITICAL** | S2 (auth bypass) |
| 🔧 | `app.ts` — `app.set('trust proxy', …)` 추가 | L8 확인 | HIGH | **CRITICAL** | S3 (IP spoofing) |
| 🆕 | `app.ts` — express-rate-limit 미들웨어 추가 (100req/15min) | L6/L8 확인 | HIGH | **CRITICAL** | S1 (DoS) |
| 🔧 | `server.ts` — `server.timeout` + `server.keepAliveTimeout` 설정 | L8 확인 | HIGH | **CRITICAL** | S2 (resource exhaustion) |
| 🆕 | `app.ts` — pino-http 요청 로깅 미들웨어 (Authorization redact) | L6 확인 | HIGH | **HIGH** | — (observability) |
| 🔧 | `server.ts`/`pool.ts`/`errorHandler.ts`/`migrate.ts` — 8개 console.* → pino 변환 | L1/L2 확인 | HIGH | **HIGH** | — (observability) |
| 🔧 | `server.ts` — `server.closeIdleConnections()` → `server.close()` 순서 적용 | L2 확인 | HIGH | **HIGH** | — (data loss) |
| 🔧 | `app.ts:44` — `/health`에 `pool.query('SELECT 1')` 추가, 실패 시 sanitized degraded 응답 | L2/L8 확인 | HIGH | **HIGH** | P1 (availability) |
| 🔧 | `tasks.repository.ts:44` — `t.created_at::text` → `to_char(t.created_at, 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"')` | L4/H4 확인 | MED | **HIGH** | M2 (test pass) |
| 🆕 | `app.ts` — compression() 미들웨어 추가 (pino-http 다음, rate-limit 이전) | L6 확인 | HIGH | **MEDIUM** | — (bandwidth) |
| 🆕 | `app.ts` + `errorHandler.ts` — X-Request-ID 수신/생성/응답/로그 전파 | L10 확인 | HIGH | **MEDIUM** | — (traceability) |
| 🔧 | `pool.ts` + `server.ts` — DB_POOL_MAX, DB_IDLE_TIMEOUT, DB_CONN_TIMEOUT, DB_STMT_TIMEOUT env vars | L5 확인 | HIGH | **MEDIUM** | P1 (pool tuning) |
| 🆕 | `src/lib/db/retry.ts` — `connectWithRetry()` with exponential backoff | Reviewer C 권장 | HIGH | **MEDIUM** | P1 (startup resilience) |
| 🔧 | `app.ts` + `tasks.routes.ts` + `__tests__/routes/*` — `/api/tasks` → `/api/v1/tasks` | Reviewer A/C 분석 | HIGH | **MEDIUM** | M1 (versioning) |
| 🆕 | `src/middleware/auditLog.ts` — CREATE/UPDATE/DELETE 시 userId + operation + resourceId 로깅 | L2/L10 확인 | HIGH | **MEDIUM** | S1 (audit trail) |
| 🆕 | Prometheus metrics endpoint + prom-client | Greenfield | MED | **LOW** | — (monitoring) |
| 🆕 | Refresh token flow (신규 auth 엔드포인트) | Reviewer B 경고 | LOW | **LOW** | S2 (auth 확장) |
| 🆕 | `POST/GET /api/v1/tasks/bulk` | Greenfield | MED | **LOW** | — (batch ops) |
| 🆕 | `Dockerfile` (multi-stage, tsc 빌드) | Reviewer C 설계 | HIGH | **LOW** | — (deployment) |
| 🆕 | `.github/workflows/ci.yml` | Greenfield | HIGH | **LOW** | M2 (CI/CD) |
| 🗑️ | CSP 튜닝 — JSON API에 무의미, Helmet 기본값 유지 또는 CSP 비활성화 | Reviewer B/C 확인 | HIGH | **LOW** | S3 (no-op) |

---

## Waves

### Wave 1 — CRITICAL (4 tasks, parallel, ~15K tokens)

**⚠️ Production gate: 이 4개 태스크가 완료되기 전까지는 절대 프로덕션에 배포하지 말 것.**

- [ ] **C1-rate-limit**: `app.ts`에 express-rate-limit 추가
  - **Worker:** light
  - **Token est:** ~3K
  - **Files:** `package.json` (dep), `src/app.ts` (middleware)
  - **Action:**
    1. `npm i express-rate-limit@^8.5.2`
    2. `app.ts` 상단에 `import rateLimit from 'express-rate-limit'` 추가
    3. CORS 뒤, 라우트 앞에 미들웨어 등록:
       ```typescript
       const apiLimiter = rateLimit({
         windowMs: 15 * 60 * 1000,  // 15분
         max: 100,                   // IP당 100회
         standardHeaders: true,
         legacyHeaders: false,
         message: { data: null, error: 'Too many requests, please try again later.' },
       });
       app.use('/api/', apiLimiter);
       ```
    4. rate-limit는 trust proxy(C4)에 의존 — 등록 순서: `cors → rateLimit → routes`
  - **Verify:**
    - `for i in $(seq 1 101); do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/api/tasks -H "Authorization: Bearer <token>"; done | sort | uniq -c` → 100개 200 + 1개 429
    - `grep "express-rate-limit" package.json` → 존재
  - **Gate:** S1 (DoS 보호)
  - **Evidence:** `.omo/ulw-loop/evidence/production-hardening-w1-c1.txt`

- [ ] **C2-jwt-secret**: `auth.ts`에서 하드코딩 폴백 제거, 지연 평가(lazy-read) 패턴 적용
  - **Worker:** light
  - **Token est:** ~2K
  - **Files:** `src/middleware/auth.ts`
  - **Action:**
    1. `auth.ts:6`의 `const JWT_SECRET = process.env.JWT_SECRET || 'dev-secret-change-me'` 를 아래로 교체:
       ```typescript
       const getJwtSecret = (): string => {
         const secret = process.env.JWT_SECRET;
         if (!secret) throw new Error('JWT_SECRET environment variable is required');
         return secret;
       };
       ```
    2. `jwt.verify(token, JWT_SECRET, ...)` → `jwt.verify(token, getJwtSecret(), ...)` (호출 시점 평가)
    3. `grep -rn "dev-secret-change-me" src/` → 0 matches
  - **Verify:**
    - `grep "dev-secret-change-me" src/middleware/auth.ts` → 0 matches
    - `JWT_SECRET="" npm test` → auth test에서 적절한 오류 (envalid가 server.ts에서 먼저 실패하거나, test가 JWT_SECRET을 명시적으로 설정)
    - Reviewer A 피드백: lazy-read 패턴은 test가 `process.env.JWT_SECRET`을 import 전에 설정하면 안전
  - **Gate:** S2 (인증 우회 방지)
  - **Evidence:** `.omo/ulw-loop/evidence/production-hardening-w1-c2.txt`

- [ ] **C3-timeout**: `server.ts`에 HTTP 수준 타임아웃 설정
  - **Worker:** light
  - **Token est:** ~1K
  - **Files:** `src/server.ts`
  - **Action:**
    1. `const server = app.listen(env.PORT, ...)` 직후 추가:
       ```typescript
       server.timeout = 30_000;           // 30s — inactive socket timeout
       server.keepAliveTimeout = 65_000;  // slightly > ALB default (60s)
       server.headersTimeout = 66_000;    // slightly > keepAliveTimeout
       ```
    2. 값은 환경변수화 가능하나, 우선 하드코딩 후 M3 패턴에서 통합
  - **Verify:**
    - `node -e "const s = require('./dist/server').default; console.log(s.timeout, s.keepAliveTimeout)"` → `30000 65000`
  - **Gate:** S2 (리소스 고갈 방지)
  - **Evidence:** `.omo/ulw-loop/evidence/production-hardening-w1-c3.txt`

- [ ] **C4-trust-proxy**: `app.ts`에 trust proxy 설정 + 환경변수화
  - **Worker:** light
  - **Token est:** ~2K
  - **Files:** `src/app.ts`, `src/server.ts` (envalid), `.env.example`
  - **Action:**
    1. `app.ts`에서 `const app = express()` 직후:
       ```typescript
       // Reviewer B 권장: loopback/linklocal/uniquelocal CIDR 자동 감지
       app.set('trust proxy', ['loopback', 'linklocal', 'uniquelocal']);
       ```
    2. 또는 환경변수: `app.set('trust proxy', process.env.TRUST_PROXY === 'true' ? 1 : false)`
    3. `.env.example`에 `# TRUST_PROXY=true` 추가
  - **Verify:**
    - `node -e "const a = require('./dist/app').app; console.log(a.get('trust proxy'))"` → `['loopback', 'linklocal', 'uniquelocal']` 또는 `1`
    - `curl -H "X-Forwarded-For: 1.2.3.4" localhost:3000/api/tasks` → `req.ip`가 `1.2.3.4` (신뢰된 프록시 뒤에서만)
  - **Gate:** S3 (IP 기반 보호 정확성)
  - **Evidence:** `.omo/ulw-loop/evidence/production-hardening-w1-c4.txt`

---

### Wave 2 — HIGH (4 tasks, H1 먼저, H2/H3/H4 병렬, ~25K tokens)

**⚠️ H1은 다른 모든 로깅 작업의 선행 조건. H2/H3/H4는 H1 이후 병렬 가능.**

- [ ] **H1-structured-logging**: pino + pino-http 도입, 모든 console.* → pino 변환
  - **Worker:** heavy
  - **Token est:** ~8K
  - **Files:** `package.json`, `src/app.ts`, `src/server.ts`, `src/middleware/errorHandler.ts`, `src/lib/db/pool.ts`, `src/lib/db/migrate.ts`, **신규** `src/lib/logger.ts`
  - **Action:**
    1. `npm i pino@^10.3.1 pino-http@^10`
    2. `src/lib/logger.ts` 신규 생성:
       ```typescript
       import pino from 'pino';
       export const logger = pino({
         level: process.env.LOG_LEVEL || 'info',
         ...(process.env.NODE_ENV === 'development' && {
           transport: { target: 'pino-pretty', options: { colorize: true } },
         }),
       });
       ```
    3. `app.ts`에 pino-http 미들웨어를 **가장 먼저** 등록 (json 파싱 이전):
       ```typescript
       import { pinoHttp } from 'pino-http';
       import { logger } from './lib/logger';
       app.use(pinoHttp({
         logger,
         // Reviewer B: Authorization 헤더 redact 필수
         redact: ['req.headers.authorization', 'req.headers.cookie'],
         // 요청 ID 자동 생성 + 응답 헤더에 포함
         genReqId: (req) => req.headers['x-request-id'] as string || crypto.randomUUID(),
       }));
       ```
    4. `server.ts` — `console.log('[server] Listening...')` → `logger.info({ port: env.PORT }, 'server started')`
    5. `pool.ts` — `console.error('[pg pool] Unexpected error...')` → `logger.error({ err }, 'pg pool idle client error')`, slow query `console.warn` → `logger.warn({ duration, query: text.substring(0,200) }, 'slow query')`
    6. `errorHandler.ts` — `console.error(\`[\${correlationId}] Unexpected error...\`)` → `logger.error({ correlationId, err }, 'unexpected error')`
    7. `migrate.ts` — `console.log('[migrate] ...')` → `logger.info('migration complete')`
  - **Verify:**
    - `npm start 2>&1 | head -1` → JSON 라인 (pino 출력)
    - `curl -H "Authorization: Bearer secret123" localhost:3000/health 2>/dev/null; npm start 2>&1 | grep "authorization"` → `[Redacted]` 또는 authorization 키 자체가 없음
    - `grep -rn "console\." src/` → 0 matches (또는 의도적인 디버그 로그만 남음)
  - **Gate:** — (observability)
  - **Evidence:** `.omo/ulw-loop/evidence/production-hardening-w2-h1.txt`

- [ ] **H2-graceful-shutdown**: `server.closeIdleConnections()` + 활성 연결 추적
  - **Worker:** medium
  - **Token est:** ~4K
  - **Files:** `src/server.ts`
  - **Action:**
    1. 활성 연결 카운터 추가:
       ```typescript
       let activeConnections = 0;
       server.on('connection', () => { activeConnections++; });
       server.on('close', () => { activeConnections--; });
       ```
    2. SIGTERM/SIGINT 핸들러 재작성 (순서 중요 — Reviewer A):
       ```typescript
       const shutdown = async (signal: string) => {
         logger.info({ signal, activeConnections }, 'shutdown initiated');
         // 1. 신규 요청 거부를 위해 idle connection 즉시 종료
         server.closeIdleConnections();
         // 2. 기존 연결이 완료될 때까지 대기 (grace period)
         server.close(async () => {
           logger.info('all connections closed, draining pool');
           await endPool();
           logger.info('shutdown complete');
           process.exit(0);
         });
         // 3. 강제 종료 폴백 (30s)
         setTimeout(() => {
           logger.error('forced shutdown after timeout');
           process.exit(1);
         }, 30_000).unref();
       };
       process.on('SIGTERM', () => shutdown('SIGTERM'));
       process.on('SIGINT', () => shutdown('SIGINT'));
       ```
  - **Verify:**
    - `curl -H "Connection: keep-alive" localhost:3000/health & sleep 0.5; kill -TERM $(pgrep -f 'node.*server')` → 로그에 `shutdown initiated` + `activeConnections: 1` + `shutdown complete`
    - 프로세스가 30초 이내에 정상 종료
  - **Gate:** — (data integrity)
  - **Evidence:** `.omo/ulw-loop/evidence/production-hardening-w2-h2.txt`

- [ ] **H3-health-db-ping**: `/health` 엔드포인트에 DB 연결 확인 추가
  - **Worker:** light
  - **Token est:** ~3K
  - **Files:** `src/app.ts`
  - **Action:**
    1. `app.ts`의 `/health` 핸들러 수정:
       ```typescript
       import { getPool } from './lib/db/pool';
       app.get('/health', async (_req, res) => {
         try {
           await getPool().query('SELECT 1');
           res.json({ status: 'ok', timestamp: new Date().toISOString() });
         } catch {
           // Reviewer B: 오류 상세는 응답에 포함하지 않음
           res.status(503).json({ status: 'degraded', timestamp: new Date().toISOString() });
         }
       });
       ```
    2. `asyncHandler`로 감싸지 않음 — 내부에서 try/catch
  - **Verify:**
    - `curl localhost:3000/health` → `{"status":"ok","timestamp":"..."}`
    - `docker stop <pg-container>; curl localhost:3000/health` → `{"status":"degraded","timestamp":"..."}` (503)
    - 응답에 DB 에러 메시지, connection string, 호스트명 없음 확인
  - **Gate:** P1 (availability monitoring)
  - **Evidence:** `.omo/ulw-loop/evidence/production-hardening-w2-h3.txt`

- [ ] **H4-test-fix**: keyset cursor pagination 테스트 실패 진단 및 수정
  - **Worker:** heavy
  - **Token est:** ~5K
  - **Files:** `src/repositories/tasks.repository.ts`, `__tests__/repositories/tasks.repository.test.ts`
  - **Action:**
    1. **진단 먼저**: `npx jest --verbose __tests__/repositories/tasks.repository.test.ts -t "identical timestamps"` 실행하여 정확한 실패 메시지 확인
    2. **근본 원인**: L4 분석 결과 `t.created_at::text`는 세션 타임존에 의존. Docker testcontainers PG의 타임존이 호스트와 달라 `timestamptz::text` 출력 형식이 달라지고, `lastIndexOf('_')`로 파싱한 커서가 `::timestamptz` 재변환 시 불일치
    3. **수정**: `tasks.repository.ts:44`의 커서 생성식을 변경:
       ```sql
       -- Before: t.created_at::text || '_' || t.id::text as _cursor
       -- After:  to_char(t.created_at, 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"') || '_' || t.id::text as _cursor
       ```
       그리고 WHERE 절의 커서 파싱도 맞춰서 수정 (UTC ISO 포맷을 `::timestamptz`로 캐스팅):
       ```typescript
       // cursorCreatedAt은 이제 항상 "2026-06-27T12:00:00.123456Z" 형식
       const clause = `AND (t.created_at, t.id) ${direction} ($${paramIdx}::timestamptz, $${paramIdx + 1}::uuid)`;
       ```
    4. `npm test` → 39/39 통과 확인
  - **Verify:**
    - `npx jest --verbose __tests__/repositories/tasks.repository.test.ts -t "identical timestamps"` → PASS
    - `npm test` → 39/39 통과, 0 failures
  - **Gate:** M2 (test pass=100%)
  - **Evidence:** `.omo/ulw-loop/evidence/production-hardening-w2-h4.txt`

---

### Wave 3 — MEDIUM (6 tasks, 모두 병렬, ~20K tokens)

**의존성: H1(structured logging)이 완료되어야 M2/M6이 pino를 사용할 수 있음. 나머지는 독립적.**

- [ ] **M1-compression**: 응답 압축 미들웨어 추가
  - **Worker:** light
  - **Token est:** ~2K
  - **Files:** `package.json`, `src/app.ts`
  - **Action:**
    1. `npm i compression@^1.8.1 && npm i -D @types/compression`
    2. `app.ts`에 pino-http 다음, rate-limit 이전에 등록:
       ```typescript
       import compression from 'compression';
       app.use(compression());  // pino-http 이후, rate-limit 이전
       ```
  - **Verify:**
    - `curl -s -H "Authorization: Bearer <token>" -H "Accept-Encoding: gzip" localhost:3000/api/tasks --compressed -w "%{size_download}" -o /dev/null` → 압축된 크기가 원본보다 작음
    - 응답 헤더에 `Content-Encoding: gzip` 확인
  - **Gate:** — (bandwidth 효율)
  - **Evidence:** `.omo/ulw-loop/evidence/production-hardening-w3-m1.txt`

- [ ] **M2-request-id**: X-Request-ID 헤더 수신/생성/응답/로그 전파
  - **Worker:** medium
  - **Token est:** ~3K
  - **Files:** `src/app.ts`, `src/middleware/errorHandler.ts`
  - **Action:**
    1. pino-http 설정에 `genReqId` 추가 (H1에서 이미 수행):
       ```typescript
       genReqId: (req) => req.headers['x-request-id'] as string || crypto.randomUUID(),
       ```
    2. 응답 헤더에 request ID 포함 미들웨어 추가:
       ```typescript
       app.use((req, res, next) => {
         res.setHeader('X-Request-ID', req.id as string);
         next();
       });
       ```
    3. `errorHandler.ts`의 `correlationId`를 `req.id`로 대체:
       ```typescript
       const correlationId = (req as any).id || crypto.randomUUID();
       ```
  - **Verify:**
    - `curl -v localhost:3000/health 2>&1 | grep -i x-request-id` → 응답 헤더에 UUID 존재
    - `curl -H "X-Request-ID: test-123" localhost:3000/health` → 응답 헤더에 `X-Request-ID: test-123`
    - 로그에서 `reqId: "test-123"` 확인
  - **Gate:** — (분산 추적)
  - **Evidence:** `.omo/ulw-loop/evidence/production-hardening-w3-m2.txt`

- [ ] **M3-pool-config**: Pool 파라미터 환경변수화
  - **Worker:** light
  - **Token est:** ~2K
  - **Files:** `src/lib/db/pool.ts`, `src/server.ts`, `.env.example`
  - **Action:**
    1. `pool.ts`의 `getPoolConfig()` 수정:
       ```typescript
       function getPoolConfig(): PoolConfig {
         return {
           connectionString: process.env.DATABASE_URL,
           max: parseInt(process.env.DB_POOL_MAX || '10', 10),
           idleTimeoutMillis: parseInt(process.env.DB_IDLE_TIMEOUT || '30000', 10),
           connectionTimeoutMillis: parseInt(process.env.DB_CONN_TIMEOUT || '5000', 10),
           statement_timeout: parseInt(process.env.DB_STMT_TIMEOUT || '30000', 10),
         };
       }
       ```
    2. `.env.example`에 추가:
       ```
       # DB_POOL_MAX=10
       # DB_IDLE_TIMEOUT=30000
       # DB_CONN_TIMEOUT=5000
       # DB_STMT_TIMEOUT=30000
       ```
  - **Verify:**
    - `DB_POOL_MAX=5 npx tsx -e "import {getPool} from './src/lib/db/pool'; console.log(getPool().options.max)"` → `5`
  - **Gate:** P1 (pool 튜닝)
  - **Evidence:** `.omo/ulw-loop/evidence/production-hardening-w3-m3.txt`

- [ ] **M4-db-retry**: DB 연결 재시도 with exponential backoff
  - **Worker:** medium
  - **Token est:** ~3K
  - **Files:** **신규** `src/lib/db/retry.ts`, `src/server.ts`
  - **Action:**
    1. `src/lib/db/retry.ts` 신규 생성 (Reviewer C 권장 — pool과 분리):
       ```typescript
       import { getPool } from './pool';
       import { logger } from '../logger';

       export async function connectWithRetry(
         maxRetries = 5,
         baseDelayMs = 1000,
       ): Promise<void> {
         for (let attempt = 1; attempt <= maxRetries; attempt++) {
           try {
             await getPool().query('SELECT 1');
             logger.info({ attempt }, 'database connection established');
             return;
           } catch (err) {
             if (attempt === maxRetries) {
               logger.fatal({ err, attempts: maxRetries }, 'database connection failed after max retries');
               throw err;
             }
             const delay = baseDelayMs * Math.pow(2, attempt - 1);
             logger.warn({ attempt, nextRetryMs: delay, err }, 'database connection failed, retrying');
             await new Promise(r => setTimeout(r, delay));
           }
         }
       }
       ```
    2. `server.ts`에서 `app.listen()` 전에 호출:
       ```typescript
       await connectWithRetry();
       const server = app.listen(env.PORT, () => { ... });
       ```
  - **Verify:**
    - 정상 실행 시: 로그에 `database connection established` (attempt 1)
    - `docker stop <pg> && npm start` → 로그에 `retrying` 여러 번 → 최종 `fatal` 또는 `docker start <pg>` 이후 복구
  - **Gate:** P1 (startup resilience)
  - **Evidence:** `.omo/ulw-loop/evidence/production-hardening-w3-m4.txt`

- [ ] **M5-api-versioning**: `/api/tasks` → `/api/v1/tasks` 프리픽스 추가
  - **Worker:** medium
  - **Token est:** ~4K
  - **Files:** `src/app.ts`, `src/routes/tasks.routes.ts`, `__tests__/routes/tasks.routes.test.ts`
  - **Action:**
    1. `app.ts:36`: `app.use('/api/tasks', taskRoutes)` → `app.use('/api/v1/tasks', taskRoutes)`
    2. `tasks.routes.ts`: 주석의 URL 경로 업데이트 (5개 주석, 기능적 영향 없음)
    3. `tasks.routes.test.ts`: **26개 URL 문자열** `/api/tasks` → `/api/v1/tasks` (Reviewer A 카운트)
       ```bash
       # sed로 일괄 치환 후 수동 확인
       sed -i '' "s|/api/tasks|/api/v1/tasks|g" __tests__/routes/tasks.routes.test.ts
       ```
    4. `npm test` → 모든 테스트가 `/api/v1/tasks`로 요청
  - **Verify:**
    - `curl localhost:3000/api/tasks` → 404
    - `curl localhost:3000/api/v1/tasks -H "Authorization: Bearer <token>"` → 200
    - `npm test` → 39/39 통과
  - **Gate:** M1 (API versioning)
  - **Evidence:** `.omo/ulw-loop/evidence/production-hardening-w3-m5.txt`

- [ ] **M6-audit-logging**: CREATE/UPDATE/DELETE 작업에 userId 감사 로깅
  - **Worker:** medium
  - **Token est:** ~3K
  - **Files:** `src/middleware/auditLog.ts` (신규), `src/routes/tasks.routes.ts`
  - **Action:**
    1. `src/middleware/auditLog.ts` 생성:
       ```typescript
       import { Request, Response, NextFunction } from 'express';
       import { logger } from '../lib/logger';

       export function auditLog(action: string) {
         return (req: Request, res: Response, next: NextFunction): void => {
           res.on('finish', () => {
             if (res.statusCode < 400) {
               // Reviewer B: allowlist 접근 — userId만, token은 제외
               logger.info({
                 audit: true,
                 userId: req.user?.sub,
                 action,
                 resourceId: req.params.id || 'N/A',
                 statusCode: res.statusCode,
                 // ip는 trust proxy(C4) 이후 정확한 클라이언트 IP
                 ip: req.ip,
               }, `audit: ${action}`);
             }
           });
           next();
         };
       }
       ```
    2. `tasks.routes.ts`에서 POST/PUT/DELETE 라우트에만 추가 (GET 제외):
       ```typescript
       taskRoutes.post('/', validateBody(createTaskSchema), auditLog('CREATE_TASK'), controller.create);
       taskRoutes.put('/:id', validateParams(taskIdSchema), validateBody(updateTaskSchema), auditLog('UPDATE_TASK'), controller.update);
       taskRoutes.delete('/:id', validateParams(taskIdSchema), auditLog('DELETE_TASK'), controller.remove);
       ```
  - **Verify:**
    - `curl -X POST .../api/v1/tasks -d '{"title":"test"}'` → 로그에서 `"audit":true,"userId":"<uuid>","action":"CREATE_TASK"` 확인
    - 로그에서 `authorization` 키가 없는지 확인 (pino redact)
    - GET 요청에서는 audit 로그가 없음 확인
  - **Gate:** S1 (audit trail)
  - **Evidence:** `.omo/ulw-loop/evidence/production-hardening-w3-m6.txt`

---

### Wave 4 — LOW (5 tasks, 모두 병렬, ~15K tokens)

- [ ] **L1-prometheus**: `/metrics` 엔드포인트 추가
  - **Worker:** medium
  - **Token est:** ~3K
  - **Files:** `package.json`, `src/metrics.ts` (신규), `src/app.ts`
  - **Action:**
    1. `npm i prom-client@^15`
    2. `src/metrics.ts` 생성 — 기본 메트릭 (http_request_duration_seconds, http_requests_total, nodejs_*)
    3. `app.ts`에 `/metrics` 라우트 추가 (auth 없이, rate-limit 적용)
  - **Verify:** `curl localhost:3000/metrics` → Prometheus 텍스트 포맷 출력
  - **Gate:** — (monitoring)
  - **Evidence:** `.omo/ulw-loop/evidence/production-hardening-w4-l1.txt`

- [ ] **L2-refresh-token**: Refresh token flow 구현
  - **Worker:** heavy
  - **Token est:** ~5K
  - **Files:** `src/routes/auth.routes.ts` (신규), `src/middleware/auth.ts`, `src/types/auth.ts`
  - **Action:**
    1. Reviewer B 경고: short-lived access + long-lived refresh 분리, refresh token rotation 필수, httpOnly cookie 권장
    2. `/auth/login`, `/auth/refresh`, `/auth/logout` 엔드포인트
    3. refresh token은 DB 저장 또는 stateless with rotation
  - **Verify:** Access token 만료 후 refresh로 새 토큰 발급, refresh token 1회 사용 후 rotation
  - **Gate:** S2 (auth 확장)
  - **Evidence:** `.omo/ulw-loop/evidence/production-hardening-w4-l2.txt`

- [ ] **L3-bulk-endpoints**: `POST /api/v1/tasks/bulk` + `GET /api/v1/tasks/bulk` 엔드포인트
  - **Worker:** medium
  - **Token est:** ~3K
  - **Files:** `src/controllers/tasks.controller.ts`, `src/routes/tasks.routes.ts`, `src/services/tasks.service.ts`
  - **Action:** 기존 `bulkCreate` + `findAll`을 라우트에 노출, batch size cap 500 유지
  - **Verify:** `curl -X POST .../api/v1/tasks/bulk -d '[{"title":"B1"},{"title":"B2"}]'` → 201, 2개 task 생성
  - **Gate:** M1 (batch ops)
  - **Evidence:** `.omo/ulw-loop/evidence/production-hardening-w4-l3.txt`

- [ ] **L4-dockerfile**: Multi-stage Dockerfile + .dockerignore
  - **Worker:** medium
  - **Token est:** ~3K
  - **Files:** `Dockerfile` (신규), `.dockerignore` (신규)
  - **Action:**
    1. Multi-stage: `node:22-alpine` → `npm ci` → `npm run build` → production image (dist/ + node_modules/ only)
    2. Reviewer C 설계: `tsc` 빌드 (tsx 사용 안 함), CommonJS 유지
    3. `.dockerignore`: node_modules, coverage, .git, __tests__, .omo
  - **Verify:** `docker build -t tasks-api . && docker run -p 3000:3000 --env-file .env tasks-api` → `curl localhost:3000/health` → 200
  - **Gate:** — (deployment)
  - **Evidence:** `.omo/ulw-loop/evidence/production-hardening-w4-l4.txt`

- [ ] **L5-cicd**: GitHub Actions CI/CD 파이프라인
  - **Worker:** medium
  - **Token est:** ~3K
  - **Files:** `.github/workflows/ci.yml` (신규)
  - **Action:**
    1. `ci.yml`: checkout → install → lint → typecheck → test (with testcontainers) → build
    2. Docker build + push (선택적)
  - **Verify:** PR 생성 시 CI 실행, lint 실패 시 빨간불, test 실패 시 빨간불
  - **Gate:** M2 (CI/CD)
  - **Evidence:** `.omo/ulw-loop/evidence/production-hardening-w4-l5.txt`

> **L6 (CSP 튜닝) — Reviewer B/C 합의로 DROP.** JSON API에 CSP 헤더는 무의미. Helmet 7 기본값 유지 또는 `helmet({ contentSecurityPolicy: false })`로 1줄 변경. 별도 태스크 불필요.

---

## Risk Register (BKIT 11-Gate Taxonomy)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| rate-limit 미적용 DoS | **S1_dataFlow** | CRIT | 100req/15min 초과 시 429 | express-rate-limit + trust proxy | `for i in $(seq 101); do curl ...; done` |
| JWT fallback으로 인증 우회 | **S2_auth** | CRIT | fallback 문자열 0 matches | lazy-read `getJwtSecret()` + envalid gate | `grep "dev-secret-change-me" src/` → 0 |
| HTTP 무제한 연결 리소스 고갈 | **S2_auth** | HIGH | server.timeout=30s | `server.timeout` + `keepAliveTimeout` | `node -e`로 설정값 확인 |
| 프록시 뒤 IP 기반 보호 무력화 | **S3_injection** | HIGH | `req.ip` = 실제 클라이언트 IP | `trust proxy` — loopback/linklocal/uniquelocal | `X-Forwarded-For` 테스트 |
| structured log에 토큰 노출 | **S1_dataFlow** | HIGH | Authorization 헤더 로그 0건 | pino-http `redact: ['req.headers.authorization']` | `grep "Bearer"` on log output → 0 |
| shutdown 중 in-flight 요청 데이터 손실 | **S1_dataFlow** | HIGH | 활성 연결 0까지 대기 | `closeIdleConnections()` → `server.close()` → `endPool()` | keep-alive 연결 후 SIGTERM 테스트 |
| DB 장애 시 health 체크 false-positive | **P1_query** | MED | DB down → 503 degraded | `SELECT 1` ping with try/catch | `docker stop pg && curl /health` |
| timestamptz::text 타임존 의존성 | **M2_test_pass** | MED | test pass=100% | `to_char()`로 UTC ISO 명시적 포맷 | `npm test` → 39/39 |
| pool 설정 하드코딩 — 과소/과대 할당 | **P1_query** | LOW | env var로 재정의 가능 | DB_POOL_MAX, DB_IDLE_TIMEOUT 등 | `DB_POOL_MAX=5` 설정값 확인 |
| DB 시작 지연 시 앱 crash-loop | **P1_query** | MED | 5회 재시도 with backoff | `connectWithRetry()` in `server.ts` | DB off → app retry log 확인 |
| API 버전 변경 시 테스트 URL 불일치 | **M3_regression** | MED | 39/39 pass | sed 일괄 치환 + 수동 확인 | `npm test` |
| audit log에 민감 필드 포함 | **S1_dataFlow** | LOW | 로그에 userId만, token 없음 | allowlist: `userId`, `action`, `resourceId`, `ip` | 로그 grep 검증 |
| Request ID 누락으로 분산 추적 단절 | — | LOW | 모든 응답에 X-Request-ID | pino-http `genReqId` + 응답 헤더 | `curl -v` → X-Request-ID |
| compression 미적용 대역폭 낭비 | — | LOW | Accept-Encoding: gzip → 압축 | compression 미들웨어 | `curl --compressed` → Content-Encoding: gzip |

---

## Execution Command

```
blackcow-loop "Execute plans/production-hardening.md" --completion-promise='All 39 tests pass (test pass=100%), lint=0warn, rate-limit returns 429, /health reflects DB status, structured logs exclude Authorization header, graceful shutdown drains active connections to 0' --trust-level=2
```

### Parallelism Guide
- **Wave 1**: C1, C2, C3, C4 — 4 tasks 완전 병렬 (독립적)
- **Wave 2**: H1 먼저(로깅 인프라), H2/H3/H4 병렬 (H1 완료 후)
- **Wave 3**: M1~M6 전부 병렬 (M2/M6만 H1 의존성 — 이미 충족)
- **Wave 4**: L1~L5 전부 병렬 (독립적)
- **총 예산**: ~75K / 115K effective (65% utilized)
