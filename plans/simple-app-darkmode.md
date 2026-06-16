# Plan: Persistent Dark Mode Toggle (Unit C)

| Field | Value |
|---|---|
| **Slug** | `simple-app-darkmode` |
| **Created** | 2025-07-19T12:00:00Z |
| **Class** | **M** |
| **Explore lanes** | 10 dispatched, 10 returned — full consensus |
| **Adversarial reviews** | 0 (planning-only per `simple-app-prd` governance) |
| **Budget** | ~18K tokens estimated / 115K effective budget |

## Intent Analysis

| Field | Value |
|---|---|
| **Detected Intent** | Feature |
| **Confidence** | HIGH |
| **Primary Gates** | M1 (spec-match), M5 (dead-code) |
| **Scale Override** | M — self-contained client-side feature; no frontend foundation exists; must define patterns from scratch |
| **Special Handling** | Stack-agnostic per governance. Plan defines mechanism, contracts, and integration pattern without assuming React/Vue/etc. Zero backend changes for core feature. |

---

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | 사용자에게 밝은 테마/어두운 테마 선택권을 제공하고, 그 선택을 방문 간에 유지하여 접근성과 사용자 경험을 향상시킨다. |
| **WHO** | 모든 최종 사용자 — 저시력 사용자, 야간 사용자, 미적 선호가 있는 사용자 |
| **WHAT** | `data-theme` 속성 기반 CSS 변수 테마 시스템 + localStorage 지속성 + 토글 UI + 시스템 감지 폴백 |
| **RISK** | 실패 시: 잘못된 테마 플래시(FOIT), localStorage 불일치. 최대 허용 다운타임: N/A (클라이언트 전용 기능) |
| **SUCCESS** | matchRate ≥ 90%, 테마 전환 0ms 지연, 새로고침 후 테마 유지율 100%, FOIT 없음, CSS 변수 100% 커버리지 |
| **SCOPE** | **포함:** CSS 변수 토큰 시스템(light + dark), `data-theme` 속성 토글 로직, localStorage 지속성 계층, `prefers-color-scheme` 감지, 초기 로드 FOIT 방지, 토글 UI 컴포넌트(스택 무관). **제외:** 서버사이드 테마 저장, 사용자별 서버 기본값, 프레임워크별 구현 세부사항 |

---

## Summary

이 계획은 어떤 프론트엔드 스택(React, Vue, Svelte, vanilla HTML)에도 적용 가능한 **스택-무관 다크 모드 시스템**을 정의한다. 핵심 메커니즘은 CSS 커스텀 프로퍼티 + `data-theme` 속성 + `localStorage` + `prefers-color-scheme` 미디어 쿼리다. Zero npm 의존성. 현재 프로젝트가 Express.js 백엔드 전용이므로, 이 계획은 향후 구축될 프론트엔드 앱에 드롭인할 수 있는 **모듈 명세**로 작성된다. 10개 레인 전수 조사 결과, 프로젝트 내 테마 관련 코드는 전무하며, 백엔드 변경 없이 클라이언트 전용으로 구현 가능하다.

---

## Architecture Options

### Option A — Minimal (순수 CSS 미디어 쿼리)
- **접근법**: `prefers-color-scheme` 미디어 쿼리만 사용. 토글 UI 없음. 사용자가 OS 설정으로만 제어.
- **장점**: 코드 5줄, 유지보수 제로, FOIT 없음
- **단점**: 사용자 재정의 불가, localStorage 없음, OS 설정과 다른 선호를 가진 사용자 배제
- **적합**: 빠른 PoC, OS 설정만으로 충분한 경우
- **예상 파일 수**: 1개 (CSS only)

### Option B — Clean (서버 백엔드 테마)
- **접근법**: `GET/PATCH /api/settings/theme` API + DB `user_preferences` 테이블 + 클라이언트 동기화. 서버가 테마 기본값 소유.
- **장점**: 기기 간 동기화 가능, 서버 검증, 사용자별 기본값
- **단점**: 백엔드 변경 7개 파일 필요, 네트워크 지연, 오프라인 미지원, JWT 필요
- **적합**: 멀티 디바이스 사용자, 엔터프라이즈
- **예상 파일 수**: 8개 (백엔드 7 + 프론트엔드 1)

### Option C — Pragmatic (CSS 변수 + localStorage + 시스템 폴백) ★ 권장
- **접근법**: CSS 커스텀 프로퍼티 토큰 시스템 + `data-theme` 속성 + `localStorage` 지속성 + `prefers-color-scheme` 초기 감지 + FOIT 방지 인라인 스크립트 + 토글 UI
- **장점**: Zero npm 의존성, 네트워크 지연 없음, 오프라인 작동, 모든 스택 호환, 업계 표준 패턴
- **단점**: 기기 간 동기화 없음 (허용 가능), 서버 사이드 렌더링 시 FOIT 방지 추가 고려 필요
- **적합**: 대부분의 일반 앱 — 이 PRD의 Units A-C 조합에 최적
- **예상 파일 수**: 3-4개 (CSS 토큰 파일, 테마 JS 모듈, 토글 컴포넌트, FOIT 방지 인라인 스크립트)

### 권장: Option C (Pragmatic)
**사유**: L6 분석 결과 dark mode는 zero npm 의존성으로 구현 가능하며, L8 보안 감사 결과 `localStorage`가 테마 선호도 저장에 충분히 안전하고, L9 성능 분석 결과 클라이언트 전용 접근이 백엔드에 제로 레이턴시 영향을 미친다. L10 패턴 분석 결과 백엔드는 3계층 아키텍처를 따르므로, 클라이언트 전용 테마가 아키텍처 무결성을 훼손하지 않는다.

---

## Codebase Survey (10-Lane Summary)

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| L1 Surface | 순수 Express JSON API — `express.static`/`res.render`/`res.sendFile` 전무, `public/`/`static/`/`views/` 디렉토리 없음 | 26개 `src/` 파일 전수 검사, `theme`/`dark`/`style`/`css` 검색 0건 | — |
| L2 Call Graph | 미들웨어 체인: `json → helmet → cors → /health → /api/tasks → errorHandler`. 사용자 선호도/프로필 인프라 제로 | `src/app.ts:11-41`, `src/middleware/` 전 파일 | S1 |
| L3 Data Shapes | `ApiResponse<T>` 래퍼, Zod 검증 패턴, `JwtPayload { sub, role }`. 사용자 설정 타입 없음. | `src/types/api.ts`, `src/schemas/task.schema.ts` | S1 |
| L4 Tests | Jest 30 + supertest + testcontainers. 5계층 테스트(unit/integration/contract/system/e2e). 커버리지 임계값 60%. DOM 테스트 환경 없음(`jsdom` 미설치). | `jest.config.ts:13-21`, `__tests__/` 12개 파일 | M2, M3 |
| L5 Config | `ALLOWED_ORIGINS=http://localhost:3000`. `tsconfig`에 `"dom"` lib 없음. 프론트엔드 빌드 파이프라인 없음. | `.env`, `tsconfig.json`, `package.json` scripts | — |
| L6 Deps | 27개 패키지 모두 백엔드 전용. Dark mode zero-dep 가능 (CSS vars + localStorage + prefers-color-scheme). | `package.json` 전수 분석 | — |
| L7 Git | Conventional Commits 혼합. Dark mode 관련 커밋 0건. `plans/` 20개 중 dark mode 언급 없음. `src/` 내 TODO/FIXME 0건. | `git log --oneline -30`, `git log --grep="dark\|theme"` | — |
| L8 Security | JWT Bearer 인증. `localStorage` 테마 저장은 LOW 위험(XSS로 읽을 수 있으나 민감 데이터 아님). CSP `style-src` 이미 `'unsafe-inline'` 허용 — 테마 클래스 전환 충돌 없음. `script-src 'self'` — 인라인 스크립트는 FOIT 방지용 `<script>` 태그만 허용 필요. | `src/middleware/auth.ts`, `node_modules/helmet/` 기본 CSP | S2, S3 |
| L9 Performance | 서버는 JSON만 반환 — dark mode가 서버에 미치는 영향 제로. FOIT 리스크: `<head>` 내 인라인 동기 스크립트로 해결 가능. CSS 변수 ~1-2KB. localStorage 읽기 sub-ms. | `src/server.ts`, `src/app.ts` | P1(N/A), P2(LOW), P3(LOW) |
| L10 Patterns | Controller→Service→Repository 3계층. `AppError` + `asyncHandler` + `errorHandler`. Zod 열거형 검증. 참조 템플릿: `src/controllers/tasks.controller.ts` 구조. | `src/` 전 계층 파일:라인 분석 | — |

---

## Gap Matrix

| Cat | Item | Evidence | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| ✅ Reuse | `ApiResponse<T>` 래퍼 — 필요 시 설정 엔드포인트에서 재사용 가능 | `src/lib/response.ts:17-19` | HIGH | — | — |
| ✅ Reuse | `auth(true)` 미들웨어 — 사용자 식별 필요 시 | `src/middleware/auth.ts:1-70` | HIGH | — | — |
| ✅ Reuse | CSP `style-src 'unsafe-inline'` — CSS 변수/클래스 전환 호환 | `src/app.ts:13` (helmet 기본값) | HIGH | — | — |
| 🆕 Build | CSS 변수 토큰 파일 — `light` + `dark` 팔레트 (~50개 토큰) | — | — | — | M1 (spec-match) |
| 🆕 Build | 테마 JS 모듈 — `getTheme()` / `setTheme()` / `toggleTheme()` + localStorage | — | — | — | M1 |
| 🆕 Build | FOIT 방지 인라인 스크립트 — `<head>` 내 동기 실행 | — | — | — | M1, P3 |
| 🆕 Build | 토글 UI 컴포넌트 — 스택 무관 명세 (버튼/스위치) | — | — | — | M1 |
| 🆕 Build | `prefers-color-scheme` 미디어 쿼리 리스너 — OS 변경 감지 | — | — | — | M1 |
| 🔧 Modify | `src/app.ts` — CSP `script-src`에 `'unsafe-inline'` 추가 필요 시 (FOIT 스크립트용) | `src/app.ts:13` | MED | LOW | S3 |

---

## Waves

### Wave 1 — Foundation: CSS Token System + Core Theme Logic (4 tasks, parallel, ≤50K tokens)

- [ ] **w1-css-tokens**: CSS 커스텀 프로퍼티 토큰 파일 생성 — `light` + `dark` 색상 팔레트 정의
  - **Files:** `client/src/styles/theme-tokens.css`
  - **Worker:** medium
  - **Token est:** ~12K
  - **Verify:** 모든 토큰이 `:root`와 `[data-theme="dark"]` 양쪽에 정의되었는지 육안 검증 + CSS 파서 유효성
  - **Gate:** M1 (spec-match) — 토큰 커버리지: 배경, 텍스트, 테두리, 그림자, 액센트, 링크, 에러, 성공, 경고, 비활성화
  - **Evidence:** `.omo/ulw-loop/evidence/darkmode-w1-tokens.txt`

- [ ] **w1-theme-module**: 테마 상태 관리 JS 모듈 — `getTheme()`, `setTheme(mode)`, `toggleTheme()`, `initTheme()`
  - **Files:** `client/src/lib/theme.js` (또는 `theme.ts`)
  - **Worker:** medium
  - **Token est:** ~10K
  - **Verify:** `getTheme()` → `'light'|'dark'|'system'`, `setTheme('dark')` → `document.documentElement.dataset.theme === 'dark'` + `localStorage.getItem('theme') === 'dark'`, `toggleTheme()` → light↔dark 순환, `initTheme()` → localStorage 우선 → `prefers-color-scheme` 폴백
  - **Gate:** M1, M2 — 단위 테스트: `describe('theme module', ...)`
  - **Evidence:** `.omo/ulw-loop/evidence/darkmode-w1-module.txt`

- [ ] **w1-foit-guard**: FOIT 방지 인라인 스크립트 — `<head>` 최상단에 배치, 동기 실행으로 페인트 전 테마 적용
  - **Files:** `client/index.html` 내 `<script>` 블록 (또는 프레임워크별 동등)
  - **Worker:** mini
  - **Token est:** ~5K
  - **Verify:** 페이지 로드 시 `data-theme` 속성이 첫 페인트 전에 설정됨 (Performance API로 검증), 깜빡임 없음
  - **Gate:** P3 (latency) — 동기 스크립트 실행 ≤1ms, DOM 조작 1회
  - **Evidence:** `.omo/ulw-loop/evidence/darkmode-w1-foit.txt`

- [ ] **w1-system-listener**: `prefers-color-scheme` 변경 감지 — `matchMedia('(prefers-color-scheme: dark)').addEventListener('change', ...)`
  - **Files:** `client/src/lib/theme.js` 내 `initSystemListener()` 함수
  - **Worker:** mini
  - **Token est:** ~3K
  - **Verify:** OS 다크 모드 전환 시 `data-theme` 속성 실시간 업데이트 (단, 사용자가 명시적 선택을 한 경우 제외)
  - **Gate:** M1 — system 모드일 때만 OS 변경 반영
  - **Evidence:** `.omo/ulw-loop/evidence/darkmode-w1-listener.txt`

### Wave 2 — Integration: Toggle UI + App Shell Wiring (3 tasks, serial on Wave 1, ≤30K tokens)

- [ ] **w2-toggle-component**: 토글 UI 컴포넌트 — 스택 무관 명세 (버튼/스위치, 3상태: light/dark/system 아이콘)
  - **Files:** `client/src/components/ThemeToggle.{jsx,tsx,vue,svelte}` (스택에 따름)
  - **Worker:** medium
  - **Token est:** ~10K
  - **Verify:** 클릭 시 `toggleTheme()` 호출 → `data-theme` 변경 + localStorage 갱신 + 아이콘 전환. 접근성: `aria-label="Toggle theme"`, `role="switch"`, `aria-checked`
  - **Gate:** M1, M4 — lint 0 warnings, a11y 검사 통과
  - **Evidence:** `.omo/ulw-loop/evidence/darkmode-w2-toggle.txt`

- [ ] **w2-app-shell**: 앱 셸/헤더에 ThemeToggle 배치 + `initTheme()` 호출 연결
  - **Files:** `client/src/App.{jsx,tsx,vue,svelte}` 또는 `client/src/layouts/Shell.*`
  - **Worker:** medium
  - **Token est:** ~8K
  - **Verify:** 앱 마운트 시 `initTheme()` 호출, 헤더에 토글 렌더링, 모든 페이지에서 토글 접근 가능
  - **Gate:** M1, M3 — 기존 기능 회귀 없음 (토글 추가 외 변경 없음)
  - **Evidence:** `.omo/ulw-loop/evidence/darkmode-w2-shell.txt`

- [ ] **w2-cross-browser**: 크로스 브라우저 검증 — Chrome, Firefox, Safari, Mobile Safari
  - **Files:** N/A (검증 전용)
  - **Worker:** medium
  - **Token est:** ~8K
  - **Verify:** 모든 브라우저에서 `prefers-color-scheme` 감지 정상, localStorage 읽기/쓰기 정상, CSS 변수 적용 정상, FOIT 없음
  - **Gate:** M2 — 테스트 매트릭스 전원 통과
  - **Evidence:** `.omo/ulw-loop/evidence/darkmode-w2-browsers.txt`

### Wave 3 — Hardening: Edge Cases + Tests (3 tasks, serial on Wave 2, ≤25K tokens)

- [ ] **w3-edge-cases**: 엣지 케이스 처리 — localStorage 손상 시 폴백, private browsing 모드, storage 이벤트(멀티탭 동기화), 시스템 모드에서 사용자 재정의 후 시스템으로 복귀
  - **Files:** `client/src/lib/theme.js` 패치
  - **Worker:** medium
  - **Token est:** ~10K
  - **Verify:** `localStorage.clear()` 후에도 `prefers-color-scheme` 폴백 작동, private browsing에서 setItem 실패 시 조용히 실패, `window.addEventListener('storage', ...)` 로 탭 간 동기화
  - **Gate:** M1, M2 — 엣지 케이스 5개 전원 단위 테스트
  - **Evidence:** `.omo/ulw-loop/evidence/darkmode-w3-edges.txt`

- [ ] **w3-unit-tests**: 테마 모듈 단위 테스트 — `theme.js`의 모든 함수 커버
  - **Files:** `client/src/lib/__tests__/theme.test.{js,ts}`
  - **Worker:** medium
  - **Token est:** ~8K
  - **Verify:** `jest --coverage` → `theme.js` 90%+ 커버리지. `getTheme`, `setTheme`, `toggleTheme`, `initTheme`, `initSystemListener` 전부 테스트
  - **Gate:** M2 (test pass=100%), M4 (lint=0)
  - **Evidence:** `.omo/ulw-loop/evidence/darkmode-w3-tests.txt`

- [ ] **w3-token-audit**: CSS 토큰 감사 — 누락 토큰 식별, 대비比率 검증
  - **Files:** `client/src/styles/theme-tokens.css`
  - **Worker:** mini
  - **Token est:** ~5K
  - **Verify:** WCAG AA 대비율 (4.5:1 일반 텍스트, 3:1 대형 텍스트). 모든 인터랙티브 요소가 light/dark 양쪽에서 식별 가능.
  - **Gate:** M1 — 대비율 매트릭스 전원 통과
  - **Evidence:** `.omo/ulw-loop/evidence/darkmode-w3-audit.txt`

---

## Risk Register (BKIT 11-Gate)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| CSS 토큰 누락 — 특정 UI 요소가 dark mode에서 보이지 않음 | `M1_spec_match` | HIGH | 100% 토큰 커버리지 | 토큰 감사(w3-token-audit)에서 모든 UI 요소 검증 | 대비율 체크리스트 전수 통과 |
| FOIT — 페이지 로드 시 잘못된 테마 깜빡임 | `P3_latency` | MED | FOIT ≤0ms (첫 페인트 전 적용) | `<head>` 내 동기 인라인 스크립트 | Performance API로 페인트 타이밍 검증 |
| localStorage 접근 실패 — private browsing / storage full | `M1_spec_match` | LOW | 조용한 실패 + 폴백 | try/catch 감싸기, 실패 시 `prefers-color-scheme`만 사용 | private browsing 테스트 |
| XSS 벡터 — localStorage 테마 값이 안전하지 않은 방식으로 DOM에 적용 | `S3_injection` | MED | 값 검증 + safe API만 사용 | `setTheme()` 내 allowlist 검증 (`'light'\|'dark'\|'system'`), `innerHTML` 사용 금지, `dataset.theme`/`classList`만 사용 | 코드 리뷰 + 보안 린트 |
| CSP 충돌 — FOIT 방지 인라인 스크립트 차단 | `S3_injection` | LOW | 스크립트 실행 + CSP 위반 없음 | CSP `script-src`에 `'unsafe-inline'` 추가 또는 nonce/hash 기반 허용 | CSP 위반 콘솔 0건 |
| 멀티탭 불일치 — 탭 A에서 테마 변경, 탭 B에서 반영 안 됨 | `M1_spec_match` | LOW | storage 이벤트로 탭 간 동기화 | `window.addEventListener('storage', ...)` 리스너 | 두 탭 열고 한쪽에서 토글 → 다른 쪽 실시간 반영 |
| 테스트 환경 — jsdom에 `matchMedia` 없음 | `M2_test_pass` | LOW | mock 필요 | `jest.config.ts`에 `jest-environment-jsdom` 추가 + `matchMedia` polyfill mock | `npm test` 통과 |
| 기존 백엔드 회귀 | `M3_regression` | LOW | 백엔드 변경 없음 (Option C) | 클라이언트 전용 기능이므로 백엔드 코드 0건 수정 | `npm test` (백엔드) 전원 통과 |

---

## Theme Token System — Specification

스택에 무관하게 모든 구현이 준수해야 할 CSS 변수 계약:

```css
/* === theme-tokens.css === */

/* Light theme (default) */
:root {
  /* Surface */
  --color-bg-primary: #ffffff;
  --color-bg-secondary: #f5f5f5;
  --color-bg-tertiary: #e8e8e8;
  --color-bg-inverse: #1a1a1a;

  /* Text */
  --color-text-primary: #1a1a1a;
  --color-text-secondary: #666666;
  --color-text-tertiary: #999999;
  --color-text-inverse: #ffffff;
  --color-text-link: #2563eb;

  /* Border */
  --color-border-primary: #d4d4d4;
  --color-border-secondary: #e8e8e8;

  /* Semantic */
  --color-accent: #2563eb;
  --color-accent-hover: #1d4ed8;
  --color-success: #16a34a;
  --color-warning: #d97706;
  --color-error: #dc2626;
  --color-error-bg: #fef2f2;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);

  /* Misc */
  --color-disabled: #a3a3a3;
  --radius-sm: 4px;
  --radius-md: 8px;
}

/* Dark theme */
[data-theme="dark"] {
  --color-bg-primary: #1a1a1a;
  --color-bg-secondary: #262626;
  --color-bg-tertiary: #333333;
  --color-bg-inverse: #ffffff;

  --color-text-primary: #f5f5f5;
  --color-text-secondary: #a3a3a3;
  --color-text-tertiary: #737373;
  --color-text-inverse: #1a1a1a;
  --color-text-link: #60a5fa;

  --color-border-primary: #404040;
  --color-border-secondary: #333333;

  --color-accent: #3b82f6;
  --color-accent-hover: #60a5fa;
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-error-bg: #450a0a;

  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);

  --color-disabled: #525252;
}
```

---

## Theme Module Contract — Specification

```typescript
// === theme.js/ts — public API ===

type ThemeMode = 'light' | 'dark' | 'system';
type ResolvedTheme = 'light' | 'dark';

// 현재 설정된 모드 반환 (localStorage → 'system' 폴백)
function getTheme(): ThemeMode

// 실제 적용된 테마 반환 ('system'일 경우 OS 감지 결과)
function getResolvedTheme(): ResolvedTheme

// 명시적 테마 설정 (localStorage + data-theme + system listener 해제)
function setTheme(mode: ThemeMode): void

// light ↔ dark 토글 (현재 resolved theme 기준)
function toggleTheme(): void

// 초기화: localStorage → prefers-color-scheme 순으로 테마 적용 + system listener 등록
// 반드시 앱 마운트 전에 호출 (FOIT 방지)
function initTheme(): void
```

---

## FOIT Prevention — Specification

```html
<!-- client/index.html <head> — MUST be first script, synchronous, no defer/async -->
<script>
  (function() {
    var theme = localStorage.getItem('theme');
    if (theme === 'light' || theme === 'dark') {
      document.documentElement.setAttribute('data-theme', theme);
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      document.documentElement.setAttribute('data-theme', 'dark');
    }
    // else: no attribute → CSS defaults to :root (light)
  })();
</script>
```

---

## Toggle UI Component — Specification

| 속성 | 명세 |
|---|---|
| **요소** | `<button>` (권장) 또는 role="switch" checkbox |
| **상태** | 3가지 아이콘: ☀️ (light) / 🌙 (dark) / 💻 (system) |
| **접근성** | `aria-label="Toggle color theme"`, `aria-pressed` (2상태) 또는 `role="switch"` + `aria-checked` |
| **클릭 동작** | `toggleTheme()` 호출 → 아이콘 즉시 변경 + `data-theme` 속성 토글 |
| **위치** | 앱 셸 헤더 우측 (일관된 배치) |
| **초기 상태** | `getTheme()` 결과에 따라 아이콘 설정 |

---

## Execution Command

```
blackcow-loop "Execute plans/simple-app-darkmode.md" --completion-promise='Dark mode toggle works: light↔dark↔system, persisted across reloads via localStorage, no FOIT, CSS tokens cover all UI surfaces, WCAG AA contrast met, zero backend changes' --trust-level=2
```

### Parallelism Guide
- **Wave 1**: 4 workers parallel (CSS tokens, theme module, FOIT guard, system listener) — 서로 의존성 없음
- **Wave 2**: 3 workers sequential on Wave 1 (toggle component → app shell → cross-browser)
- **Wave 3**: 3 workers sequential on Wave 2 (edge cases → unit tests → token audit)
- **Total budget**: ~18K / 115K effective (dynamic)

---

## Stack-Specific Adaptation Notes

이 계획은 **스택 무관** 명세다. 실제 구현 시 프레임워크에 따른 적용:

| 스택 | FOIT 방지 | 토글 컴포넌트 | 테마 모듈 |
|---|---|---|---|
| **Vanilla HTML/JS** | `<head>` 인라인 `<script>` (위 명세 그대로) | `<button>` + `onclick` | `theme.js` 모듈 스크립트 |
| **React** | `index.html` `<head>` 인라인 (CRA/Vite 동일) | `ThemeToggle.tsx` + `useSyncExternalStore` | `theme.ts` → React context 또는 전역 import |
| **Vue** | `index.html` `<head>` 인라인 | `ThemeToggle.vue` + `ref` | `theme.ts` → Pinia store 또는 provide/inject |
| **Svelte** | `app.html` `<head>` 인라인 | `ThemeToggle.svelte` + `$state` | `theme.ts` → Svelte store |
| **Next.js** | `_document.tsx` `<Head>` + `dangerouslySetInnerHTML` | 클라이언트 컴포넌트 (`'use client'`) | 주의: SSR hydration mismatch 방지 위해 `suppressHydrationWarning` 필요 |
| **Astro** | `<head>` 인라인 `<script is:inline>` | Astro 컴포넌트 + `client:load` | `theme.ts` → `client:load` |

---
