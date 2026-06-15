# Plan: Expo React Native Login Screen — Architecture Decision

| Field | Value |
|---|---|
| **Slug** | `sim-expo-login` |
| **Created** | `2025-06-19` |
| **Class** | `XS` (greenfield evaluation, no codebase) |
| **Explore lanes** | `2 research subagents dispatched, both returned` |
| **Adversarial reviews** | `skipped (XS)` |
| **Budget** | `greenfield — research-based, no local code surveyed` |

## Intent Analysis (Phase -1)
| Field | Value |
|---|---|
| **Detected Intent** | Feature |
| **Confidence** | HIGH |
| **Primary Gates** | M1 (spec-match), M5 (dead-code) |
| **Special Handling** | Greenfield — all lanes adapted to research against Expo docs/ecosystem |

---

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | 사용자가 Expo managed workflow에서 안전하고 유지보수 가능한 로그인 화면을 구현할 수 있도록, expo-auth-session(OAuth)과 custom email/password 폼 방식 간의 트레이드오프를 평가하고 최적 경로를 제시한다. |
| **WHO** | Expo React Native 개발자 (managed workflow, Expo Go + development build 사용) |
| **WHAT** | `plans/sim-expo-login.md` — 구현 계획 (아키텍처 결정 + 파일 목록 + Waves). 구현 코드는 포함하지 않음. |
| **RISK** | 잘못된 auth 방식 선택 시: 개발 생산성 저하 (Expo Go 불가), 보안 취약점 (토큰 저장 실수), Provider 락인, 앱스토어 거부. |
| **SUCCESS** | matchRate N/A (greenfield), 결정 근거가 명확하고 반박 가능한 트레이드오프 매트릭스가 포함되어 있으며, 구현 Wave가 구체적인 파일 목록 + 검증 명령과 함께 제시됨. |
| **SCOPE** | 포함: 로그인 화면, 토큰 저장, 인증 상태 관리, 기본 에러 핸들링. 제외: 회원가입, 비밀번호 재설정, 소셜 프로필 연동, 푸시 알림, 백엔드 구현. |

---

## Summary

Expo managed workflow에서 로그인을 구현하는 두 경로 — (A) `expo-auth-session`을 통한 OAuth 2.0/OIDC 소셜 로그인, (B) `react-hook-form` + `zod` + `expo-secure-store`를 활용한 custom email/password 폼 — 를 평가했다. **권장: Option C (Pragmatic)** — email/password를 먼저 구축하고, OAuth는 Phase 2에서 추가. 이유: (1) expo-auth-session은 development build를 **강제**하므로 Expo Go 빠른 이터레이션이 불가능하고, (2) email/password 스택은 100% pure JS로 managed workflow 제약이 전혀 없으며, (3) 두 방식 모두 `expo-secure-store` 기반 토큰 저장이라는 공통 인프라를 공유하므로 순차적 추가가 자연스럽다.

---

## Architecture Options

### Option A — OAuth 전용 (expo-auth-session)
- **접근법**: `expo-auth-session` + `expo-web-browser`로 Google/Apple/GitHub 등 OAuth 2.0/OIDC provider 연동. PKCE(S256) 기본 적용.
- **장점**: 
  - 비밀번호 관리 부담 제로 (사용자 측도, 개발자 측도)
  - Social login으로 전환율 높음
  - `AuthSession.refreshAsync()`로 토큰 갱신 first-class 지원
  - PKCE로 client secret 없이도 안전한 auth code flow
- **단점**: 
  - **Expo Go에서 테스트 불가** — 반드시 development build 필요 (`expo.scheme` 커스텀 필요)
  - Google/Facebook built-in provider는 **deprecated** — `@react-native-google-signin/google-signin` 등 별도 SDK 필요
  - Provider별 redirect URI 등록 필요 (개발/스테이징/프로덕션 각각)
  - Auth proxy 제거됨 (v5) — `https://auth.expo.io/...` 프록시 플로우 사용 불가
  - OAuth provider 장애 시 로그인 전체 마비
- **예상 파일 수**: 6~8개 (provider configs, auth hook, session storage, redirect handler)
- **적합**: B2C 앱, 소셜 로그인이 핵심 UX인 경우, development build 워크플로우에 이미 적응된 팀

### Option B — Email/Password 전용 (Custom Form)
- **접근법**: `react-hook-form` + `zod` 폼 검증 → 백엔드 API 호출 → JWT `expo-secure-store` 저장 → Axios interceptor로 토큰 갱신. `expo-local-authentication`으로 생체인증 추가 가능.
- **장점**:
  - **Expo Go에서 100% 작동** — development build 불필요 (초기 개발 속도 ↑)
  - 모든 라이브러리가 pure JS — managed workflow 제약 zero
  - 백엔드와의 결합도를 직접 제어 가능 (토큰 구조, 갱신 전략, 세션 정책)
  - Provider dependency 없음 — 서비스 장애에 강함
  - 폼 커스터마이징 무제한 (디자인 시스템과 완전 통합)
- **단점**:
  - 비밀번호 관리 부담 (복잡도 규칙, 해싱은 백엔드에서)
  - "비밀번호 찾기" 플로우 필요 → scope 확장
  - Social login 대비 전환율 낮을 수 있음
  - 토큰 갱신 로직 직접 구현 (Axios interceptor + mutex 패턴)
- **예상 파일 수**: 8~10개 (form schema, screen, auth context, secure store wrapper, API client, interceptor, biometric hook)
- **적합**: B2B 앱, 엔터프라이즈, 기존 email/password 백엔드가 있는 경우, Expo Go 빠른 이터레이션이 중요한 초기 단계

### Option C — Pragmatic: Email/Password 우선, OAuth 추가 (권장)
- **접근법**: Option B로 시작하여 견고한 auth 인프라(토큰 저장, 갱신, AuthContext)를 구축한 후, 동일 인프라 위에 expo-auth-session을 Phase 2로 추가. 두 방식이 동일한 `expo-secure-store` + `AuthContext`를 공유.
- **장점**: Option B의 모든 장점 + OAuth 확장 경로 확보. 리스크 분산.
- **단점**: 초기 구현량이 Option A보다 많음. Phase 2에서 development build 전환 필요.
- **예상 파일 수**: Phase 1: 8개, Phase 2: +4개
- **적합**: 대부분의 일반적인 앱. **권장.**

### 권장: Option C (Pragmatic)
**사유**: (1) Expo Go 호환성으로 초기 개발 속도가 Option A보다 2~3배 빠르며, (2) 구축된 auth 인프라(SecureStore, AuthContext, API client)가 OAuth 추가 시 그대로 재사용되므로 throwaway 작업이 없고, (3) expo-auth-session의 development build 강제라는 critical gotcha를 초기 단계에서 회피할 수 있다.

---

## Tradeoff Matrix: expo-auth-session vs Custom Email/Password

| 평가 축 | expo-auth-session (OAuth) | Custom Email/Password | 승자 |
|---|---|---|---|
| **Expo Go 호환** | ❌ Development build 필수 | ✅ 100% Expo Go | **Custom** |
| **초기 설정 복잡도** | 높음 (scheme, redirect URI, provider 등록) | 낮음 (폼 + API 호출) | **Custom** |
| **보안 부담** | 낮음 (PKCE, 비밀번호 없음) | 중간 (토큰 저장, 전송 직접 관리) | **OAuth** |
| **사용자 경험** | 1-tap 로그인, 높은 전환율 | ID/PW 입력 필요 | **OAuth** |
| **Provider 리스크** | Provider 장애 = 로그인 불가 | 자체 백엔드만 의존 | **Custom** |
| **유지보수** | Provider SDK 변경 추적 필요 | 직접 제어, 변경 범위 예측 가능 | **Custom** |
| **토큰 갱신** | `AuthSession.refreshAsync()` 내장 | Axios interceptor 직접 구현 | **OAuth** |
| **Google/Apple 로그인** | Built-in deprecated → 별도 SDK | N/A (해당 없음) | **무승부** |
| **커스터마이징** | 제한적 (OAuth UI는 provider 제어) | 완전 자유 | **Custom** |
| **Managed workflow 적합도** | ⚠️ Development build 필요 | ✅ 완벽 호환 | **Custom** |

---

## Codebase Survey (Research Summary — Greenfield)

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| **L1 Surface** | Greenfield — no existing code. Target: Expo SDK 52+, managed workflow, expo-router 기반 파일 구조 가정. | — | — |
| **L2 Call Graph** | N/A — 신규 구축. Auth flow: `LoginScreen → API call → SecureStore.save → AuthContext.setUser → Protected routes` | Architecture diagram below | S1 |
| **L3 Data Shapes** | `LoginForm: { email: string, password: string }` → `AuthResponse: { accessToken, refreshToken, user: { id, email } }`. zod schema로 타입 추론. | Research subagent | S1 |
| **L4 Tests** | Jest + React Native Testing Library. Form validation unit tests, API mock, AuthContext integration test. | Standard Expo testing stack | M2, M3 |
| **L5 Config** | `app.json`: `expo.scheme` (Phase 2 OAuth), `ios.config.usesNonExemptEncryption: false` (SecureStore). `.env`: `API_BASE_URL`. | expo-secure-store docs | S2 |
| **L6 Deps** | `react-hook-form@7`, `zod@3`, `@hookform/resolvers@3`, `expo-secure-store`, `axios@1`, `expo-local-authentication` (optional). All pure JS. | Research subagent | — |
| **L7 Git** | Conventional Commits 권장: `feat(auth): add login form with zod validation` | Standard | — |
| **L8 Security** | SecureStore > AsyncStorage (Keychain/Keystore 암호화). Android Auto Backup 주의 (`configureAndroidBackup: true`). iOS Keychain 재설치 지속성 주의. Axios interceptor에 mutex로 토큰 갱신 stampede 방지. | Research subagent | S1, S2, S3 |
| **L9 Performance** | react-hook-form은 uncontrolled inputs → keystroke당 리렌더 없음 (Formik 대비 우수). SecureStore 비동기 → 초기 토큰 로드 시 splash screen 유지. | Research subagent | P1, P3 |
| **L10 Patterns** | Expo 공식 가이드 + 커뮤니티 표준: `AuthContext` (React Context) + `SecureStore` wrapper + Axios interceptor. react-hook-form + zod가 Formik + yup을 대체 중. | Research subagent | — |

---

## Architecture Flow (Email/Password — Option B/C Phase 1)

```
┌─────────────────────────────────────────────────────┐
│                    LoginScreen                       │
│  ┌───────────────────────────────────────────────┐  │
│  │  react-hook-form + zod                         │  │
│  │  Controller(TextInput) × 2 (email, password)   │  │
│  │  onBlur validation → inline error messages     │  │
│  │  handleSubmit → onSubmit()                     │  │
│  └───────────────────┬───────────────────────────┘  │
└──────────────────────┼──────────────────────────────┘
                       │ POST /auth/login
                       ▼
┌─────────────────────────────────────────────────────┐
│              api.ts (Axios instance)                 │
│  ┌───────────────────────────────────────────────┐  │
│  │  Request interceptor: attach Bearer token      │  │
│  │  Response interceptor: 401 → refresh → retry  │  │
│  │  Mutex queue: prevent concurrent refresh       │  │
│  └───────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────┘
                   │ accessToken + refreshToken
                   ▼
┌─────────────────────────────────────────────────────┐
│              secureStore.ts                          │
│  ┌───────────────────────────────────────────────┐  │
│  │  expo-secure-store                             │  │
│  │  saveTokens() / getAccessToken() / clearTokens │  │
│  │  iOS Keychain / Android EncryptedSharedPrefs   │  │
│  └───────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────┘
                   │ user object
                   ▼
┌─────────────────────────────────────────────────────┐
│              AuthContext.tsx                          │
│  ┌───────────────────────────────────────────────┐  │
│  │  React Context + useReducer                    │  │
│  │  State: { user, isLoading, isSignedIn }        │  │
│  │  Actions: SIGN_IN, SIGN_OUT, RESTORE_TOKEN     │  │
│  │  SplashScreen.preventAutoHideAsync() until     │  │
│  │  RESTORE_TOKEN completes                       │  │
│  └───────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────┘
                   │ useAuth() hook
                   ▼
┌─────────────────────────────────────────────────────┐
│              Protected Routes / Navigation            │
│  expo-router: (app)/_layout.tsx checks isSignedIn    │
│  Redirect: !isSignedIn → /login, isSignedIn → /home │
└─────────────────────────────────────────────────────┘
```

---

## Gap Matrix

| Cat | Item | Evidence | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| ✅ **Reuse** | `expo-secure-store` — Phase 1, 2 공통 토큰 저장소 | Expo SDK built-in | HIGH | — | — |
| ✅ **Reuse** | `AuthContext` — Phase 1 구축 후 Phase 2 OAuth에서도 동일하게 사용 | 설계 의도 | HIGH | — | — |
| 🔧 **Modify** | `app.json` — Phase 2에서 `expo.scheme` 추가 | expo-auth-session 요구사항 | HIGH | low | M3 |
| 🆕 **Build** | `LoginScreen` + form validation | Greenfield | — | — | M1 |
| 🆕 **Build** | `secureStore.ts` wrapper | Greenfield | — | — | S1 |
| 🆕 **Build** | `api.ts` (Axios + interceptor) | Greenfield | — | — | S2 |
| 🆕 **Build** | `AuthContext.tsx` | Greenfield | — | — | M1 |
| 🆕 **Build** | `useBiometric.ts` (optional) | Greenfield | — | — | — |
| 🗑️ **Delete** | 없음 — greenfield | — | — | — | M5 |

---

## Waves

### Phase 1 — Email/Password Auth (8 tasks, ≤115K tokens)

#### Wave 1 — Foundation (4 tasks, parallel)
- [ ] **step-1**: Install dependencies → `package.json`
  - **Worker:** `mini`
  - **Token est:** ~2K
  - **Action:** `npx expo install react-hook-form @hookform/resolvers zod expo-secure-store axios`
  - **Verify:** `npx expo install --check` returns clean
  - **Gate:** M4 (dependency audit clean)
  - **Evidence:** `.omo/evidence/w1-s1-deps.txt`

- [ ] **step-2**: Create `src/lib/secureStore.ts` — token persistence wrapper
  - **Worker:** `mini`
  - **Token est:** ~3K
  - **Action:** Implement `saveTokens(access, refresh)`, `getAccessToken()`, `getRefreshToken()`, `clearTokens()` using `expo-secure-store`
  - **Verify:** Unit test: `saveTokens` → `getAccessToken` roundtrip
  - **Gate:** S1 (data at rest encrypted)
  - **Evidence:** `.omo/evidence/w1-s2-securestore.test.ts`

- [ ] **step-3**: Create `src/lib/api.ts` — Axios instance with interceptor
  - **Worker:** `medium`
  - **Token est:** ~5K
  - **Action:** Implement request interceptor (attach Bearer), response interceptor (401 → refresh → retry with mutex queue), `login(email, password)` method
  - **Verify:** Mock 401 → refresh → retry flow in test
  - **Gate:** S2 (token refresh stampede prevention), S3 (no token in logs)
  - **Evidence:** `.omo/evidence/w1-s3-api.test.ts`

- [ ] **step-4**: Create `src/schemas/auth.ts` — zod validation schemas
  - **Worker:** `mini`
  - **Token est:** ~2K
  - **Action:** `loginSchema: z.object({ email: z.string().email(), password: z.string().min(8) })`, export inferred `LoginForm` type
  - **Verify:** Unit test: valid/invalid email, short password, empty fields
  - **Gate:** M2 (validation pass=100%)
  - **Evidence:** `.omo/evidence/w1-s4-schema.test.ts`

#### Wave 2 — Core (3 tasks, depends on Wave 1)
- [ ] **step-5**: Create `src/contexts/AuthContext.tsx` — auth state management
  - **Worker:** `heavy`
  - **Token est:** ~8K
  - **Action:** React Context + `useReducer`. State: `{ user, isLoading, isSignedIn }`. `signIn(credentials)`, `signOut()`, `restoreToken()` on mount. Integrate `SplashScreen.preventAutoHideAsync()`.
  - **Verify:** Integration test: `restoreToken` → `isSignedIn: true` → `signOut` → `isSignedIn: false`
  - **Gate:** M1 (state transitions correct), M2 (test pass=100%)
  - **Evidence:** `.omo/evidence/w2-s5-authcontext.test.tsx`

- [ ] **step-6**: Create `src/components/LoginForm.tsx` — login screen UI
  - **Worker:** `heavy`
  - **Token est:** ~8K
  - **Action:** `react-hook-form` `Controller` wrapping `TextInput` for email + password. `zodResolver` integration. Inline error display. Submit button with loading state. `autoCapitalize="none"` on email. `secureTextEntry` on password.
  - **Verify:** Component test: render → type → submit → calls `onSubmit` with form data. Error display on invalid input.
  - **Gate:** M1 (spec-match: all fields present, validation visible), M4 (accessibility labels)
  - **Evidence:** `.omo/evidence/w2-s6-loginform.test.tsx`

- [ ] **step-7**: Wire navigation guard — `(app)/_layout.tsx`
  - **Worker:** `medium`
  - **Token est:** ~4K
  - **Action:** expo-router root layout: read `isSignedIn` from `useAuth()`, redirect `!isSignedIn → /login`, `isSignedIn → /(tabs)`. Handle `isLoading` state with splash screen.
  - **Verify:** Navigation test: signed-out → redirect to /login. signed-in → redirect to /(tabs).
  - **Gate:** M3 (no regression on existing routes)
  - **Evidence:** `.omo/evidence/w2-s7-navigation.test.tsx`

#### Wave 3 — Hardening (1 task, depends on Wave 2)
- [ ] **step-8**: Error handling + biometric opt-in
  - **Worker:** `medium`
  - **Token est:** ~5K
  - **Action:** Add `expo-local-authentication` for biometric login toggle. Network error toast. `401` on app start → force logout. `SecureStore` unavailable fallback (log warning, block login).
  - **Verify:** E2E test: bad credentials → error message → form remains. Biometric prompt → cancel → fallback to password.
  - **Gate:** S2 (auth bypass prevention), M2 (error paths tested)
  - **Evidence:** `.omo/evidence/w3-s8-error.test.tsx`

### Phase 2 — OAuth Addition (deferred, 4 tasks)

- [ ] **step-9**: Configure `expo.scheme` in `app.json` + install `expo-auth-session` + `expo-web-browser`
- [ ] **step-10**: Create `src/lib/oauth.ts` — `useProxy`-less OAuth flow with `AuthSession.AuthRequest` + PKCE
- [ ] **step-11**: Add "Sign in with Google/Apple" buttons to `LoginScreen`
- [ ] **step-12**: OAuth callback handler → same `AuthContext.signIn()` path → shared `SecureStore`

---

## Risk Register (BKIT 11-Gate)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| Form validation bypass | `M1_spec_match` | HIGH | 모든 입력이 zod schema 통과 | `zodResolver` + `mode: 'onBlur'` + `handleSubmit`만 API 호출 | Unit test: 빈 문자열, SQL injection string, XSS payload |
| Access token 평문 저장 | `S1_dataFlow` | CRIT | SecureStore 사용 (AsyncStorage 금지) | `expo-secure-store` only. 코드리뷰에서 `AsyncStorage` import 금지 | grep `AsyncStorage` → 0 matches in auth module |
| Token refresh stampede | `S2_auth` | HIGH | 동시 401 → 1회만 refresh | Axios interceptor mutex queue 패턴 | Test: 3 concurrent 401 → exactly 1 `POST /auth/refresh` |
| iOS Keychain 재설치 지속 | `S1_dataFlow` | MED | 앱 재설치 시 토큰 폐기 | `clearStoreOnReinstall` flag (version-keyed) | Test: install → login → delete app → reinstall → token 없음 |
| Android Auto Backup 노출 | `S1_dataFlow` | MED | Backup에서 SecureStore 제외 | `expo.android.configureAndroidBackup: true` in `app.json` | Verify: `app.json` config present |
| Development build 전환 리스크 (Phase 2) | `M3_regression` | LOW | Phase 1 기능 회귀 없어야 함 | Phase 1 E2E test suite를 Phase 2에서도 통과 | `npm test` pass=100% after OAuth addition |
| `expo-auth-session` provider deprecation | `M5_dead_code` | LOW | Deprecated provider 사용 금지 | Google/Facebook built-in provider 미사용 → native SDK로 직접 | grep `expo-auth-session/providers` → 0 matches |
| Network error 시 사용자 경험 | `P3_latency` | MED | 타임아웃 10s, 에러 메시지 표시 | Axios `timeout: 10000`, error interceptor → toast | Test: axios mock timeout → toast visible |

---

## Decision Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                      최종 권장 스택                               │
├─────────────────────────────────────────────────────────────────┤
│  Phase 1 (지금): Email/Password                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  react-hook-form + zod     → 폼 검증                       │  │
│  │  expo-secure-store         → 토큰 저장 (Keychain/Keystore) │  │
│  │  axios + interceptor       → API 클라이언트 + 토큰 갱신    │  │
│  │  React Context + useReducer → 인증 상태 관리               │  │
│  │  expo-local-authentication → 생체인증 (optional)           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Phase 2 (나중에): OAuth 추가                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  expo-auth-session + expo-web-browser → OAuth 2.0 + PKCE  │  │
│  │  @react-native-google-signin/google-signin → Google 로그인 │  │
│  │  (동일 AuthContext + SecureStore 공유)                      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**핵심 판단 근거**: Expo Go 호환성. expo-auth-session은 development build를 **강제**하며, 이는 `expo.scheme`이 필요한 모든 OAuth flow의 근본적 제약이다. 초기 개발 단계에서 Expo Go의 빠른 이터레이션(저장 즉시 리로드, QR 코드 공유, Expo Go 클라이언트 내 테스트)을 포기할 이유가 없다. Email/password 스택은 100% Expo Go에서 작동하고, 구축된 인프라는 OAuth 추가 시 그대로 재사용된다. **버리는 작업이 없다.**

---

## Execution Command

```
blackcow-loop "Execute plans/sim-expo-login.md" \
  --completion-promise='LoginScreen with email/password form, SecureStore token persistence, AuthContext, and Axios interceptor. All tests pass. No AsyncStorage for tokens.' \
  --trust-level=2
```

### Parallelism Guide
- **Wave 1**: 4 workers in parallel (deps install, secureStore, api client, schema)
- **Wave 2**: 3 workers in parallel (AuthContext, LoginForm, navigation) — all depend on Wave 1
- **Wave 3**: 1 worker (error handling, biometric)
- **Total budget**: ~40K / 128K target (XS scale, greenfield)
