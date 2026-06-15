# Plan: Input Sanitization — Trim, HTML-Escape, Strip Tags, Preserve Emoji

| Field | Value |
|---|---|
| **Slug** | `input-sanitization` |
| **Created** | `2026-06-16T19:00:00Z` |
| **Class** | **M** (4 files, ~250 new lines) |
| **Explore lanes** | `10 dispatched, 10 returned` |
| **Adversarial reviews** | `3/3 passed` |
| **Budget** | `~45K tokens / 115K dynamic target` |

---

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | 제목과 설명 필드에 저장되는 HTML/스크립트가 프론트엔드에서 렌더링될 때 stored XSS 취약점을 방지 |
| **WHO** | tasks API 소비자(프론트엔드 앱), 보안 감사자 |
| **WHAT** | `src/lib/sanitize.ts` 유틸리티 + Zod schema `.transform()` 적용 + 단위/통합 테스트 |
| **RISK** | 실패 시: sanitization 누락으로 XSS 방어 실패. 최대 허용 다운타임: N/A (순수 추가 기능) |
| **SUCCESS** | matchRate ≥ 90%, test pass=100%, lint=0warn, coverage ≥ 80% (sanitize.ts), p95_target_ms: N/A |
| **SCOPE** | 포함: `title`, `description` 필드 (CREATE + UPDATE). 제외: pagination params, status/priority enums, auth headers |

---

## Summary

`POST/PUT /api/tasks` 엔드포인트로 들어오는 `title`과 `description`에 대해 **trim → strip HTML tags → HTML-escape** 파이프라인을 Zod `.transform()`으로 적용한다. 이모지는 유니코드 문자열이므로 자연스럽게 보존된다. Sanitization은 **쓰기 시점**(Zod parse 단계)에 적용되어 DB에는 항상 클린 데이터가 저장되며, 읽기 경로(taskToResponse, GET)에서는 추가 처리 불필요. 별도 라이브러리 없이 순수 문자열 연산으로 구현.

---

## Architecture Options

### Option A — Minimal (최소 변경)
- **접근법**: `task.schema.ts` 내 title/description 필드에 인라인 `.transform()` 람다로 sanitization 로직 직접 작성
- **장점**: 파일 1개만 수정, 가장 빠름
- **단점**: 유틸리티 재사용 불가, 단위 테스트 어려움, 로직 중복
- **적합**: 긴급 패치 (이 경우 아님)
- **예상 파일 수**: 1개

### Option B — Clean (이상적 설계)
- **접근법**: `src/lib/sanitize.ts` + `src/lib/sanitize-rule.ts`로 규칙/유틸 분리, DI 가능한 Sanitizer 클래스, zod schema와 완전 분리, 통합 테스트 전용 E2E 시나리오
- **장점**: 완전한 테스트 커버리지, 최대 재사용성
- **단점**: 과도한 추상화, M 규모 작업에 불필요한 복잡도
- **적합**: 다중 엔티티 sanitization이 필요한 대형 프로젝트
- **예상 파일 수**: 5개

### Option C — Pragmatic (현실적 타협) ✅ **권장**
- **접근법**: 단일 `src/lib/sanitize.ts` 유틸리티 모듈 (순수 함수), Zod schema의 title/description에 `.transform()` 적용, `__tests__/lib/sanitize.test.ts` 단위 테스트, 기존 routes 통합 테스트에 XSS 페이로드 케이스 4건 추가
- **장점**: 기존 코드베이스 패턴(`src/lib/response.ts` Clean 패턴 + Zod transform)과 일치, 단위 테스트 가능, 최소한의 변경
- **적합**: 이 작업의 정확한 규모
- **예상 파일 수**: 4개 (2 new + 2 modified)

---

## Codebase Survey (10-Lane Summary)

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| **L1 Surface** | 7개 HTTP 진입점, 모든 쓰기는 repository.create/update로 수렴. 검증 미들웨어 → controller → service → repository → SQL | `src/routes/tasks.routes.ts:12-24`, `src/repositories/tasks.repository.ts:117-172` | S1 (dataFlow) |
| **L2 Call Graph** | title/description 흐름: HTTP body → Zod parse → CreateTaskDto/UpdateTaskDto → repository SQL params → DB. 중간 변환: `dto.description \|\| null` (undefined → null) | `src/schemas/task.schema.ts:7-15`, `src/repositories/tasks.repository.ts:119-129` | S1 |
| **L3 Data Shapes** | title: required, max 200, VARCHAR(200) NOT NULL. description: optional, max 5000, TEXT nullable. Zod→DTO 사이 형식 변경 없음 | `src/types/task.ts:10-24`, migration SQL | S1 |
| **L4 Tests** | Jest 30 + ts-jest + supertest + testcontainers. 3개 테스트 파일, skipped/disabled 0건. 커버리지 threshold: 60% global | `jest.config.ts:9-16`, `__tests__/routes/tasks.routes.test.ts` | M2, M3 |
| **L5 Config** | zod v4.4.3, express v5.2.1, helmet v7.2.0. `.env.example` 존재, JWT_SECRET 하드코딩 fallback 발견 (`auth.ts:6`) | `package.json`, `src/middleware/auth.ts:6` | S2 |
| **L6 Deps** | Zod v4 `.transform()` + `.pipe()` 지원 확인 (코드베이스 내 `paginationSchema`에서 이미 사용 중). 타 sanitization 라이브러리 없음 — 순수 구현 | `src/schemas/task.schema.ts:48,53`, zod v4 type definitions | — |
| **L7 Git** | Conventional Commits + R-round 혼합. src/는 gitignored (시뮬레이션 생성). TODO/FIXME/HACK 0건 | `git log --oneline -20` | — |
| **L8 Security** | **현재 title/description sanitization 전무.** Helmet 헤더만 설정. XSS: stored HTML이 프론트엔드에서 innerHTML로 렌더링될 경우 취약. SQLi는 parameterized query로 방어됨 | 전체 `src/` 검색 결과 0건, `task.schema.ts`에 `.transform(sanitize*)` 없음 | **S3 CRITICAL** |
| **L9 Performance** | O(n) 문자열 연산, 최대 5000 chars × 100 tasks/write. V8에서 sub-ms. 쓰기 시점 sanitization이 읽기 시점보다 효율적 | N+1 0건, 병목 없음 | P1/P2/P3 pass |
| **L10 Patterns** | Dominant: **Clean** (`src/lib/response.ts` — 순수 함수 export, 제네릭 타입). Zod transform: **Pragmatic** (`task.schema.ts` paginationSchema). `src/lib/` 디렉토리에 새 유틸리티 배치가 일관된 패턴 | `src/lib/response.ts:7-44`, `src/schemas/task.schema.ts:46-54` | — |

---

## Gap Matrix

| Cat | Item | Evidence | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| 🆕 Build | `src/lib/sanitize.ts` — `sanitizeText()` 유틸리티 함수 | — | — | — | M1 (spec-match) |
| 🆕 Build | `__tests__/lib/sanitize.test.ts` — 단위 테스트 (trim, stripTags, htmlEscape, emoji, edge cases) | — | — | — | M2 (test pass) |
| 🔧 Modify | `src/schemas/task.schema.ts` — `createTaskSchema.title` + `.transform(sanitizeText)` | L6: `.transform()` pattern exists at line 48,53 | HIGH | med | M1, M3 |
| 🔧 Modify | `src/schemas/task.schema.ts` — `createTaskSchema.description` + `.transform(sanitizeText)` | L6: same pattern | HIGH | med | M1, M3 |
| 🔧 Modify | `src/schemas/task.schema.ts` — `updateTaskSchema.title` + `.transform(sanitizeText)` (optional guard) | L6: same | HIGH | med | M1, M3 |
| 🔧 Modify | `src/schemas/task.schema.ts` — `updateTaskSchema.description` + `.transform(sanitizeText)` (optional guard) | L6: same | HIGH | med | M1, M3 |
| 🔧 Modify | `__tests__/routes/tasks.routes.test.ts` — XSS 페이로드 통합 테스트 4건 추가 | L4: 기존 S3 Validation 블록 존재 | HIGH | low | M2, S3 |
| ✅ Reuse | Zod `.transform()` 패턴 — `paginationSchema` 기존 사용 | `src/schemas/task.schema.ts:46-54` | HIGH | — | — |
| ✅ Reuse | 테스트 헬퍼 (`test-helpers.ts`, `generateToken`, `authHeader`) | `__tests__/test-helpers.ts`, routes test | HIGH | — | — |
| 🗑️ Delete | 없음 | — | — | — | — |

---

## Waves

### Wave 1 — Foundation: Sanitize Utility (1 task, ≤20K tokens)

- [ ] **w1-s1**: Create `src/lib/sanitize.ts` — `sanitizeText()` function
  - **Worker:** `mini`
  - **Token est:** ~8K
  - **Verify:** `npx tsx -e "const {sanitizeText}=require('./src/lib/sanitize'); console.assert(sanitizeText('<script>alert(1)</script>')==='alert(1)'); console.assert(sanitizeText('🎉')==='🎉'); console.log('OK')"` → `OK`
  - **Gate:** M1 (spec-match: trim → stripTags → htmlEscape 순서, emoji 보존)
  - **Evidence:** `.omo/ulw-loop/evidence/input-sanitization-w1-s1.txt`
  - **Files:** `src/lib/sanitize.ts` (new)

### Wave 2 — Integration: Schema Transforms (1 task, ≤15K tokens)

- [ ] **w2-s1**: Modify `src/schemas/task.schema.ts` — add `.transform(sanitizeText)` to title + description in both `createTaskSchema` and `updateTaskSchema`
  - **Worker:** `mini`
  - **Token est:** ~6K
  - **Dependencies:** Wave 1 complete
  - **Verify:** `npx tsc --noEmit` → no errors; `npm test` → 기존 테스트 전수 통과 (M3 regression)
  - **Gate:** M1 (spec-match: 4개 transform 추가), M3 (기존 테스트 0 regression), M4 (lint 0 warnings)
  - **Evidence:** `.omo/ulw-loop/evidence/input-sanitization-w2-s1.txt`
  - **Files:** `src/schemas/task.schema.ts` (modified)

### Wave 3 — Hardening: Tests (2 tasks, parallel, ≤25K tokens)

- [ ] **w3-s1**: Create `__tests__/lib/sanitize.test.ts` — 20+ 단위 테스트
  - **Worker:** `medium`
  - **Token est:** ~12K
  - **Dependencies:** Wave 1 complete
  - **Verify:** `npx jest __tests__/lib/sanitize.test.ts --coverage` → all pass + coverage ≥ 80%
  - **Gate:** M2 (test pass=100%, coverage ≥ 80%), M4 (lint 통과)
  - **Evidence:** `.omo/ulw-loop/evidence/input-sanitization-w3-s1.txt`
  - **Files:** `__tests__/lib/sanitize.test.ts` (new)

- [ ] **w3-s2**: Add XSS integration test cases to `__tests__/routes/tasks.routes.test.ts`
  - **Worker:** `mini`
  - **Token est:** ~8K
  - **Dependencies:** Wave 2 complete
  - **Verify:** `npx jest __tests__/routes/tasks.routes.test.ts` → all pass (기존 + 신규)
  - **Gate:** M2 (test pass=100%), S3 (XSS payload 거부 확인), M3 (0 regressions)
  - **Evidence:** `.omo/ulw-loop/evidence/input-sanitization-w3-s2.txt`
  - **Files:** `__tests__/routes/tasks.routes.test.ts` (modified)

---

## Risk Register (BKIT 11-Gate)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| transform 순서 오류 (escape 후 strip → 태그 문자 소실) | `M1_spec_match` | HIGH | matchRate ≥ 90% | 명시적 순서: trim → stripTags → htmlEscape. 단위 테스트로 검증 | `sanitizeText('<script>alert("xss")</script>') === 'alert(&quot;xss&quot;)'` |
| optional 필드 undefined 처리 누락 | `M1_spec_match` | MED | matchRate ≥ 90% | `.transform((v) => v ? sanitizeText(v) : v)` 패턴 사용 | 단위 테스트: `sanitizeText(undefined) === undefined` |
| 기존 테스트 회귀 (M3) | `M3_regression` | MED | 0 regressions | Wave 2 완료 후 `npm test` 전수 실행 | CI: `npm test -- --forceExit` |
| sanitization 이중 적용 (escape된 데이터 재escape) | `S1_dataFlow` | MED | integrity ≥ 85% | 쓰기 시점에만 적용, 읽기 경로(taskToResponse)는 그대로 | `GET /api/tasks/:id` 응답에서 `&amp;`가 `&amp;amp;`로 나타나지 않는지 확인 |
| 이모지/유니코드 손상 | `M1_spec_match` | LOW | 모든 유니코드 보존 | regex 기반 (HTML 태그만 타겟, 유니코드 범위 건드리지 않음) | 단위 테스트: 🎉🌟💯, 한글, 日本語, العربية 보존 확인 |
| Zod v4 `.transform()` 반환 타입 불일치 | `M1_spec_match` | LOW | 타입체크 통과 | v4 `.transform()`이 ZodPipe를 반환 — `.pipe()` 없이 단독 사용 시 타입 추론 문제 가능성 | `npx tsc --noEmit` 통과 |
| 설명 필드 빈 문자열 → null 강제변환 부작용 | `S1_dataFlow` | LOW | integrity ≥ 85% | `sanitizeText('')`는 `''` 반환 → repository에서 `dto.description \|\| null`이 null로 변환. 기존 동작과 일치 | 통합 테스트: `{description: ''}` → DB에 null 저장 확인 |

---

## Design Detail: `sanitizeText()` Specification

```typescript
// src/lib/sanitize.ts

/**
 * Sanitize free-text input before storage.
 *
 * Pipeline (order matters):
 *  1. Trim leading/trailing whitespace
 *  2. Strip HTML tags — remove anything matching `<...>` including
 *     `<script>`, `<img onerror=...>`, self-closing `<br/>`, etc.
 *  3. HTML-escape the five critical entities:
 *     & → &amp;   (MUST be first to avoid double-escaping)
 *     < → &lt;
 *     > → &gt;
 *     " → &quot;
 *     ' → &#x27;
 *
 * Emoji and all other Unicode code points pass through unchanged
 * (regex operates on ASCII HTML syntax only).
 *
 * @returns sanitized string, or null/undefined if input was null/undefined.
 */
export function sanitizeText(input: string | null | undefined): string | null | undefined {
  if (input == null) return input;
  let s = input.trim();
  s = s.replace(/<[^>]*>/g, '');       // strip all HTML tags
  s = s.replace(/&/g, '&amp;');        // escape & first
  s = s.replace(/</g, '&lt;');
  s = s.replace(/>/g, '&gt;');
  s = s.replace(/"/g, '&quot;');
  s = s.replace(/'/g, '&#x27;');
  return s;
}
```

## Design Detail: Schema Transform Pattern

```typescript
// In createTaskSchema:
title: z.string().min(1).max(200).transform(sanitizeText),
// .transform() receives the validated string; sanitizeText returns the clean string.
// The output type is still string — Zod v4's ZodPipe preserves the outer type.

// For optional fields (description, updateTaskSchema fields):
description: z.string().max(5000).optional()
  .transform((v) => v ? sanitizeText(v) : v),
// Guard: only sanitize when the optional value is present (truthy).
// undefined passes through untouched.
```

## Test Case Inventory

### Unit Tests (`__tests__/lib/sanitize.test.ts`) — 22 cases

| # | Category | Input | Expected |
|---|---|---|---|
| 1 | trim | `"  hello  "` | `"hello"` |
| 2 | trim | `"\\n\\ttest\\n"` | `"test"` |
| 3 | trim | `"no-trim"` | `"no-trim"` |
| 4 | stripTags | `"<b>bold</b>"` | `"bold"` |
| 5 | stripTags | `"<script>alert(1)</script>"` | `"alert(1)"` |
| 6 | stripTags | `"<img src=x onerror=alert(1)>"` | `""` |
| 7 | stripTags | `"text <br/> more"` | `"text  more"` |
| 8 | stripTags | `"<a href='x'>link</a>"` | `"link"` |
| 9 | htmlEscape | `"A & B"` | `"A &amp; B"` |
| 10 | htmlEscape | `"a < b > c"` | `"a &lt; b &gt; c"` |
| 11 | htmlEscape | `'say "hello"'` | `"say &quot;hello&quot;"` |
| 12 | htmlEscape | `"it's"` | `"&#x27;it&#x27;s"` or `"it&#x27;s"` |
| 13 | emoji | `"Hello 🎉 world 🌍"` | `"Hello 🎉 world 🌍"` |
| 14 | emoji | `"🎉🌟💯"` | `"🎉🌟💯"` |
| 15 | CJK | `"日本語テスト"` | `"日本語テスト"` |
| 16 | combined | `"  <script>alert('xss')</script> 🎉  "` | `"alert(&#x27;xss&#x27;) 🎉"` |
| 17 | combined | `"<b>Hello & Welcome</b>"` | `"Hello &amp; Welcome"` |
| 18 | null input | `null` | `null` |
| 19 | undefined input | `undefined` | `undefined` |
| 20 | empty string | `""` | `""` |
| 21 | no tags, no special | `"Plain text"` | `"Plain text"` |
| 22 | double-escaping guard | `"&amp;"` | `"&amp;amp;"` (의도적 — 이미 이스케이프된 데이터는 재이스케이프됨) |

### Integration Tests (`__tests__/routes/tasks.routes.test.ts`) — 4 additions to S3 block

| # | Input | Expected |
|---|---|---|
| 23 | `POST {title: "<script>alert(1)</script>"}` | 201, `data.title === "alert(1)"` |
| 24 | `POST {title: "  <b>Hello</b>  ", description: "<img src=x>"}` | 201, title=`"Hello"`, description=`""` |
| 25 | `POST {title: "XSS & 🎉", description: "<a href='x'>click</a>"}` | 201, title=`"XSS &amp; 🎉"`, description=`"click"` |
| 26 | `PUT {description: "<script>evil()</script>"}` | 200, description=`"evil()"` |

---

## Execution Command

```
blackcow-loop "Execute plans/input-sanitization.md" --completion-promise='matchRate ≥ 90%, test pass=100%, lint=0warn, coverage ≥ 80% (sanitize.ts), emoji preserved' --trust-level=2
```

### Parallelism Guide
- Wave 1: single task (no parallel opportunity)
- Wave 2: single task (depends on Wave 1)
- Wave 3: w3-s1 and w3-s2 can run in **parallel** (they have different dependencies and no shared state)
- Total budget: ~30K / 115K target (dynamic)
