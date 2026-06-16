# Plan: Profile Settings Page (Unit B)

| Field | Value |
|---|---|
| **Slug** | `simple-app-profile` |
| **Created** | 2025-07-19 |
| **Class** | **M** (3 sub-features, each with multiple API endpoints + UI states, dependency on Unit A auth) |
| **Intent** | Feature — greenfield planning from PRD |
| **Explore lanes** | Research-mode (3 domain probes substituted for 10-lane codebase survey; no codebase exists) |
| **Adversarial reviews** | 0 (governance directive: no code to review; plans reviewed via M1 spec-match only) |
| **Budget** | ~25 K tokens estimated / 128 K target |

---

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | 사용자가 자신의 계정 정보를 확인하고, 프로필 정보를 수정하며, 비밀번호 변경 및 계정 삭제를 안전하게 수행할 수 있는 중앙 설정 공간 제공 |
| **WHO** | 인증된 일반 사용자 (Unit A — email/password auth 완료된 사용자) |
| **WHAT** | 프로필 조회 화면, 프로필 편집 폼, 아바타 업로드 플레이스홀더, 이메일 변경(인증 포함), 비밀번호 변경, 계정 삭제(확정 확인 포함) — 모두 스택 비의존적 API 계약 + 컴포넌트 명세로 제공 |
| **RISK** | 이메일 변경 미검증 시 계정 탈취 가능, 계정 삭제 실수 시 데이터 복구 불가, 세션 하이재킹 시 비밀번호 변경으로 계정 영구 탈취. 최대 허용 다운타임: N/A (계획 단계) |
| **SUCCESS** | matchRate ≥ 90%, 모든 API 엔드포인트가 명세된 보안 요구사항 충족, 모든 폼 상태 머신이 정의됨, WCAG 2.2 AA 접근성 패턴 포함, NIST SP 800-63B 패스워드 정책 준수, GDPR 삭제 권리(Article 17) 고려 |
| **SCOPE** | **포함**: 프로필 조회(표시명, 이메일, 아바타 플레이스홀더, 계정 메타데이터), 프로필 편집(표시명 변경, 이메일 변경+인증, 아바타 업로드 플레이스홀더), 계정 설정(비밀번호 변경, 계정 삭제+확정 확인). **제외**: 실제 파일 업로드 파이프라인 구현, 이메일 발송 인프라, 다크모드(Unit C), 인증 시스템(Unit A), 관리자 패널, OAuth 소셜 계정 연동 |

---

## Summary

본 계획은 인증된 사용자(Unit A 의존)의 프로필 관리 기능을 스택 비의존적 API 계약 및 컴포넌트 명세로 정의한다. 핵심 설계 결정은 다음과 같다:

- **이메일 변경**: OWASP 권장 3단계 프로세스 — (1) 현재 비밀번호로 재인증, (2) 새 이메일로 확인 메일 발송, (3) 기존 이메일로 보안 알림. 확인 전까지 기존 이메일 유지.
- **비밀번호 변경**: NIST SP 800-63B 준수 — 최소 8자(MFA 있는 경우) 또는 15자(단일 인증), Have I Been Pwned 블록리스트 검사, 문자 조합 강제 금지. 변경 후 모든 세션 무효화.
- **계정 삭제**: GDPR Article 17 고려 — 소프트 삭제(즉시 비활성화) → 유예 기간(14일) → 익명화 → 영구 삭제. 확정 전 3단계 확인(사용자명 입력, "DELETE" 구문 입력, 비밀번호 재인증).
- **아바타**: 클릭-업로드 플레이스홀더(파일 선택기 열기까지만). 실제 업로드 파이프라인은 제외.

모든 폼은 표준 상태 머신(`IDLE → DIRTY → SAVING → SUCCESS/ERROR`)을 따르며, WCAG 2.2 AA 접근성 패턴(`aria-describedby`, `role="alert"`, 초점 관리)을 포함한다.

---

## Architecture Options

### Option A — Minimal (단일 페이지, 인라인 편집)

- **접근법**: 하나의 설정 페이지에 모든 필드를 인라인 편집 가능하게 배치. 각 필드 옆에 "Edit" 버튼 → 인라인 전환 → 저장/취소. 탭/섹션 구분 없음.
- **장점**: 파일 수 최소 (~1-2개), 내비게이션 불필요, 구현 시간 최소
- **단점**: 계정 삭제 같은 파괴적 액션이 일반 필드와 같은 페이지에 배치되어 UX 위험, 모바일에서 스크롤 과다, 향후 설정 항목 추가 시 혼잡
- **적합**: PoC, 프로토타입
- **예상 컴포넌트 수**: ~5개

### Option B — Clean (탭/섹션 분리, 전체 페이지 전환)

- **접근법**: "Profile", "Security", "Danger Zone" 3개 탭/섹션으로 완전 분리. 각 탭은 독립된 라우트. 모든 변경은 전용 확인 모달 동반. 아바타는 전용 업로드 페이지.
- **장점**: 관심사 완벽 분리, 파괴적 액션 격리, 확장성 최고, 접근성 최적 (ARIA Tabs 패턴)
- **단점**: 파일 수 증가, 탭 전환 시 상태 손실 가능성, 오버엔지니어링 위험 (간단한 앱에 과도)
- **적합**: 대규모 SaaS, 엔터프라이즈
- **예상 컴포넌트 수**: ~12개

### Option C — Pragmatic (2섹션 페이지 + 모달) ★ 권장

- **접근법**: 단일 페이지 내 "Profile" + "Account" 두 섹션으로 구분. 프로필 섹션은 인라인 편집, 계정 섹션은 전용 모달(비밀번호 변경, 계정 삭제)로 보호. 아바타는 클릭-업로드 플레이스홀더.
- **장점**: 요구사항 정확히 충족, 간결한 내비게이션, 파괴적 액션은 모달로 격리, 접근성 충족 가능, 파일 수 합리적
- **단점**: 향후 섹션이 5+개로 늘어나면 리팩토링 필요
- **적합**: MVP + 점진적 확장
- **예상 컴포넌트 수**: ~8개

### 권장: Option C (Pragmatic)
**사유**: PRD 요구사항(3개 기능 영역)을 2섹션으로 자연스럽게 매핑. 계정 삭제/비밀번호 변경을 모달로 격리하여 UX 안전성 확보. 파일 수와 복잡도가 "simple app" 취지에 부합. 향후 설정 항목 추가 시 섹션 분할로 대응 가능.

---

## Requirements Analysis (Research-Mode Lane Summary)

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| **L1 UX Patterns** | 아바타: 이니셜 폴백 + 호버 오버레이 "Change photo" + 클릭 시 파일 선택기. 이메일 변경: 3단계 (재인증 → 새 이메일 확인 → 기존 이메일 알림). 계정 삭제: 다층 확인 (사용자명 입력 + "DELETE" 구문 입력 + 비밀번호) | NNGroup, GitHub, Linear, Stripe, Radix UI Avatar 패턴 (see research) | M1 |
| **L2 Security** | 이메일 변경: OWASP 양방향 확인 (기존+새 주소 모두 확인). 비밀번호: NIST SP 800-63B — 최소 8자/15자, HIBP 블록리스트, 문자 조합 규칙 금지, 변경 후 세션 재생성. GDPR 삭제: 소프트삭제 → 유예 → 익명화 → 영구삭제 | OWASP Cheat Sheet, NIST SP 800-63B, GDPR Article 17 (see research) | S2, S3 |
| **L3 Accessibility** | 폼 오류: `aria-describedby` + `role="alert"` 오류 요약 + `aria-invalid`. 모달: `<dialog>` + 초점 트랩 + Esc 닫기 + 트리거로 초점 반환. 아바타 alt: 표시명이 근처에 있으면 `alt=""` (장식), 없으면 `alt="사용자 이름의 프로필 사진"`. 탭 탐색: ARIA Tabs 패턴 | WCAG 2.2 AA, ARIA APG, MDN (see research) | M1 |
| **L4 Data Model** | `UserProfile` (displayName, email, emailVerified, avatarUrl, createdAt, updatedAt), `EmailChangeRequest` (userId, newEmail, token, expiresAt, confirmedAt), `AccountDeletion` (userId, status, requestedAt, scheduledDeletionAt, cancelledAt) | Derived from requirements | S1 |
| **L5 API Contracts** | 8 REST 엔드포인트: `GET /api/me`, `PATCH /api/me`, `POST /api/me/avatar` (placeholder), `POST /api/me/email-change`, `GET /api/verify-email`, `POST /api/me/change-password`, `POST /api/me/delete-account`, `POST /api/me/cancel-deletion` | RESTful conventions | M1 |
| **L6 State Management** | 폼 상태 머신: `IDLE → DIRTY → SAVING → SUCCESS/ERROR`. 낙관적 업데이트: 아바타(즉시 미리보기). 비관적: 이메일 변경, 비밀번호 변경, 계정 삭제. 세션 만료 처리: 파괴적 액션 전 재인증 확인 | Derived from UX research | M1 |
| **L7 Error Handling** | 네트워크 오류: 토스트 + 재시도. 유효성 검증 실패: 인라인 필드 오류. 세션 만료: 재로그인 리다이렉트. 이메일 중복: 특정 메시지 "This email is already in use". 속도 제한: 429 → "Too many attempts. Try again in N minutes." | Standard patterns | M1 |
| **L8 Security Surface** | 세션 하이재킹 방지: 모든 민감 작업에서 현재 비밀번호 재확인. 이메일 변경 시 양방향 확인. 계정 삭제 시 3중 확인. 비밀번호 변경 후 모든 세션 무효화 + 신규 세션 발급. 토큰 만료: 이메일 확인 토큰 1시간 TTL | OWASP Session Management Cheat Sheet | S2 |
| **L9 Performance** | 프로필 조회: 단일 GET 요청 (응답 < 200ms 목표). 이메일 확인: 비동기 메일 발송 → 폴링 또는 WebSocket으로 상태 업데이트. 아바타: 클라이언트 측 리사이즈 후 업로드 (대역폭 절약). | General best practices | P3 |
| **L10 Patterns** | PRD 3유닛 구조 — Unit A(인증)가 세션/사용자 컨텍스트 제공. Unit B는 인증된 사용자 객체에 의존. 탭/섹션 구분은 Facebook/Google/GitHub 설정 페이지의 표준 패턴 | Industry standard | — |

---

## Component Hierarchy (Framework-Agnostic)

```
<ProfileSettingsPage>                       // 인증 가드 — Unit A 세션 필요
│
├── <PageHeader
│     title="Settings"
│     backNavigation="/" />                // 뒤로가기
│
├── <ErrorBoundary fallback={<ErrorState />}>
│
│   ├── SECTION 1: Profile
│   │   ├── <SectionHeader title="Profile" />
│   │   │
│   │   ├── <AvatarSection>                // 아바타 + 표시명
│   │   │   ├── <Avatar
│   │   │   │   src: string | null
│   │   │   │   alt: string                // "" (장식) 또는 사용자명
│   │   │   │   fallback: string           // 이니셜 (예: "JD")
│   │   │   │   size: "lg" | "md" | "sm"
│   │   │   │   editable: boolean />
│   │   │   │   └── <AvatarOverlay         // 호버 시 "Change photo" 오버레이
│   │   │   │       onHover: () => void />
│   │   │   │
│   │   │   └── <DisplayNameField
│   │   │       value: string
│   │   │       onChange: (name: string) => void
│   │   │       onSave: () => Promise<void>
│   │   │       state: FormState           // IDLE | DIRTY | SAVING | SUCCESS | ERROR
│   │   │       error?: string />
│   │   │
│   │   ├── <EmailSection>                 // 이메일 관리
│   │   │   ├── <EmailDisplay
│   │   │   │   email: string
│   │   │   │   verified: boolean
│   │   │   │   verificationStatus: 'none' | 'pending' | 'verified' | 'expired' />
│   │   │   │
│   │   │   └── <EmailChangeFlow>          // 조건부 렌더링 (이메일 변경 시작 시)
│   │   │       ├── <PasswordReauthPrompt  // 1단계: 현재 비밀번호 입력
│   │   │       │   onSubmit: (password: string) => Promise<void>
│   │   │       │   onCancel: () => void />
│   │   │       ├── <NewEmailInput         // 2단계: 새 이메일 입력
│   │   │       │   value: string
│   │   │       │   onChange: (email: string) => void
│   │   │       │   onSubmit: () => Promise<void> />
│   │   │       └── <VerificationBanner    // 3단계: 확인 메일 발송 완료
│   │   │           email: string
│   │   │           onResend: () => Promise<void>
│   │   │           onCancel: () => void />
│   │   │
│   │   └── <AccountMeta>                  // 계정 메타데이터 (읽기 전용)
│   │       ├── <MetaItem label="Member since" value={createdAt} />
│   │       ├── <MetaItem label="Last updated" value={updatedAt} />
│   │       └── <MetaItem label="Account ID" value={userId} />
│   │
│   ├── SECTION 2: Account
│   │   ├── <SectionHeader title="Account" />
│   │   │
│   │   ├── <ChangePasswordButton          // → 비밀번호 변경 모달 열기
│   │   │   label="Change password"
│   │   │   onClick: () => void />
│   │   │
│   │   └── <DeleteAccountButton            // → 계정 삭제 모달 열기
│   │       label="Delete account"
│   │       variant="destructive"           // 빨간색/위험 스타일
│   │       onClick: () => void />
│   │
│   └── <ToastContainer                     // 전역 알림
│       position="bottom-right"
│       toasts: Toast[] />
│
├── <ChangePasswordModal>                   // 모달 다이얼로그
│   ├── <ModalHeader title="Change password" onClose={closeModal} />
│   ├── <CurrentPasswordField ... />
│   ├── <NewPasswordField
│   │   showStrengthMeter: true
│   │   minLength: 8
│   │   blocklistCheck: true />             // HIBP API 연동
│   ├── <ConfirmNewPasswordField ... />
│   ├── <PasswordRequirements>              // 길이, HIBP 통과 여부
│   │   requirements: PasswordRule[] />
│   ├── <ModalActions>
│   │   <CancelButton />
│   │   <SubmitButton
│   │       label="Update password"
│   │       disabled={!isValid}
│   │       loading={isSaving} />
│   └── </ModalActions>
│
└── <DeleteAccountModal>                    // 모달 다이얼로그 (role="alertdialog")
    ├── <ModalHeader title="Delete account" variant="destructive" />
    ├── <WarningBanner>                     // 빨간색 경고
    │   "This action is permanent. All your data will be scheduled for deletion."
    ├── <DataExportLink />                  // "Download your data before deleting"
    ├── <ConfirmUsernameInput               // 1차 확인
    │   label='Type your username to confirm: "{username}"'
    │   expectedValue={username} />
    ├── <ConfirmPhraseInput                 // 2차 확인
    │   label='Type "DELETE" to confirm'
    │   expectedValue="DELETE" />
    ├── <CurrentPasswordField               // 3차 확인: 비밀번호 재인증
    │   label="Enter your password to confirm" />
    ├── <DeletionConsequences>
    │   "After {deletionDate}, your data will be permanently deleted. You can cancel until then."
    ├── <ModalActions>
    │   <CancelButton />
    │   <DeleteButton                       // 세 확인이 모두 통과해야 활성화
    │       label="Delete my account"
    │       disabled={!allConfirmed}
    │       loading={isDeleting} />
    └── </ModalActions>
```

---

## Data Model (Stack-Agnostic)

### Core Entities

```
UserProfile {
  id: string (UUID)
  displayName: string (1-100 chars, trimmed)
  email: string (valid email, unique, indexed)
  emailVerified: boolean
  avatarUrl: string | null
  createdAt: ISO-8601 datetime
  updatedAt: ISO-8601 datetime
}

EmailChangeRequest {
  id: string (UUID)
  userId: string (FK → UserProfile.id)
  currentEmail: string           // snapshot at time of request (for rollback)
  newEmail: string
  confirmationToken: string      // cryptographically random, SHA-256 hashed for storage
  tokenExpiresAt: ISO-8601       // 1 hour TTL
  confirmedAt: ISO-8601 | null   // null until verified
  createdAt: ISO-8601
}

AccountDeletion {
  id: string (UUID)
  userId: string (FK → UserProfile.id)
  status: 'pending' | 'scheduled' | 'cancelled' | 'completed'
  requestedAt: ISO-8601
  scheduledDeletionAt: ISO-8601  // default: now + 14 days
  cancelledAt: ISO-8601 | null
  completedAt: ISO-8601 | null
  reason: string | null          // optional feedback
}

PasswordChangeAudit {
  id: string (UUID)
  userId: string (FK → UserProfile.id)
  changedAt: ISO-8601
  ipAddress: string
  userAgent: string
}
```

### Validation Rules

| Field | Rule | Error Message |
|---|---|---|
| `displayName` | 1-100 chars, not whitespace-only | "Display name must be 1-100 characters" |
| `newEmail` | Valid RFC 5322 email, not same as current, unique | "Please enter a valid email address" / "Email is the same as current" / "Email already in use" |
| `currentPassword` | Must match authenticated user's password | "Current password is incorrect" |
| `newPassword` | Min 8 chars (MFA) / 15 chars (no MFA), not in HIBP blocklist, not same as current | "Password must be at least 8 characters" / "This password has been compromised — choose another" |
| `confirmPassword` | Must match `newPassword` | "Passwords don't match" |
| `confirmUsername` | Must match current `displayName` exactly | "Doesn't match your username" |
| `confirmPhrase` | Must be exactly "DELETE" | "Type DELETE to confirm" |

---

## API Contracts (REST, Stack-Agnostic)

All endpoints require `Authorization: Bearer <session_token>` from Unit A.

### 1. Read Profile

```http
GET /api/me
Authorization: Bearer <token>

→ 200 OK
{
  "id": "uuid",
  "displayName": "Jane Doe",
  "email": "jane@example.com",
  "emailVerified": true,
  "avatarUrl": null,
  "createdAt": "2025-01-15T09:00:00Z",
  "updatedAt": "2025-07-19T14:30:00Z"
}

→ 401 Unauthorized
{ "error": "unauthorized", "message": "Invalid or expired session" }
```

### 2. Update Display Name

```http
PATCH /api/me
Content-Type: application/json
Authorization: Bearer <token>

{ "displayName": "Jane D." }

→ 200 OK
{ "displayName": "Jane D.", "updatedAt": "2025-07-19T15:00:00Z" }

→ 400 Bad Request
{ "error": "validation_error", "field": "displayName", "message": "Display name must be 1-100 characters" }
```

### 3. Avatar Upload Placeholder

```http
POST /api/me/avatar
Content-Type: multipart/form-data
Authorization: Bearer <token>

[file] ← 선택된 이미지 파일

→ 200 OK
{ "avatarUrl": "https://cdn.example.com/avatars/uuid.jpg" }

→ 413 Payload Too Large
{ "error": "file_too_large", "message": "Avatar must be under 2 MB" }

→ 415 Unsupported Media Type
{ "error": "invalid_type", "message": "Only JPEG and PNG images are supported" }
```

> **참고**: 실제 파일 업로드 파이프라인은 본 계획 범위 밖. 플레이스홀더로 API 시그니처만 정의.

### 4. Request Email Change

```http
POST /api/me/email-change
Content-Type: application/json
Authorization: Bearer <token>

{ "newEmail": "jane.new@example.com", "currentPassword": "********" }

→ 200 OK
{
  "status": "verification_sent",
  "message": "Check jane.new@example.com for a verification link. A notification was also sent to your current email.",
  "expiresAt": "2025-07-19T16:00:00Z"
}

→ 400 Bad Request
{ "error": "validation_error", "field": "newEmail", "message": "Email already in use" }

→ 403 Forbidden
{ "error": "password_mismatch", "message": "Current password is incorrect" }

→ 429 Too Many Requests
{ "error": "rate_limited", "message": "Too many attempts. Try again in 15 minutes.", "retryAfter": 900 }
```

### 5. Verify Email Change

```http
GET /api/verify-email?token=<secure_token>

→ 302 Found (redirect to settings page with success)
Location: /settings?email_verified=true

→ 400 Bad Request
{ "error": "invalid_token", "message": "Verification link is invalid or expired" }
```

### 6. Change Password

```http
POST /api/me/change-password
Content-Type: application/json
Authorization: Bearer <token>

{
  "currentPassword": "********",
  "newPassword": "********",
  "confirmPassword": "********"
}

→ 200 OK
{
  "message": "Password updated. All other sessions have been revoked.",
  "newSessionToken": "<new_session_token>"    // 기존 세션 무효화, 새 세션 발급
}

→ 400 Bad Request
{ "error": "validation_error", "field": "newPassword", "message": "This password has been compromised in a data breach — choose another" }

→ 403 Forbidden
{ "error": "password_mismatch", "message": "Current password is incorrect" }
```

### 7. Delete Account

```http
POST /api/me/delete-account
Content-Type: application/json
Authorization: Bearer <token>

{
  "confirmUsername": "Jane D.",
  "confirmPhrase": "DELETE",
  "currentPassword": "********",
  "reason": "optional_feedback"           // 선택적 피드백
}

→ 202 Accepted
{
  "status": "deletion_scheduled",
  "message": "Account scheduled for deletion. You can cancel by logging in before 2025-08-02T15:00:00Z.",
  "scheduledDeletionAt": "2025-08-02T15:00:00Z",
  "dataExportUrl": "/api/me/export-data"
}

→ 400 Bad Request
{ "error": "validation_error", "message": "Confirmation fields don't match" }

→ 403 Forbidden
{ "error": "password_mismatch", "message": "Current password is incorrect" }
```

### 8. Cancel Account Deletion

```http
POST /api/me/cancel-deletion
Authorization: Bearer <token>

→ 200 OK
{ "status": "deletion_cancelled", "message": "Account deletion has been cancelled." }

→ 404 Not Found
{ "error": "not_found", "message": "No pending deletion found" }
```

---

## State Machines

### Form State Machine (모든 폼 공통)

```
                    ┌─────────┐
       INIT ──────→ │  IDLE   │ ←────── SUCCESS (2초 후)
                    └────┬────┘                 │
                         │ 필드 변경             │
                         ▼                      │
                    ┌─────────┐                 │
                    │  DIRTY  │                 │
                    └────┬────┘                 │
                         │ 저장 요청             │
                         ▼                      │
                    ┌─────────┐                 │
                    │ SAVING  │─────────────────┘
                    └────┬────┘
                         │ 서버 오류
                         ▼
                    ┌─────────┐
                    │  ERROR  │────→ DIRTY (재시도)
                    └─────────┘
```

### Email Change Flow

```
VIEW_PROFILE ──→ [Change email 클릭]
    │
    ▼
CONFIRM_PASSWORD (현재 비밀번호 입력 → POST /api/me/email-change)
    │
    ├── 실패 → ERROR (비밀번호 불일치 / 이메일 중복)
    │
    ▼
VERIFICATION_SENT (배너: "확인 메일 발송됨")
    │
    ├── 새 이메일에서 확인 링크 클릭 → GET /api/verify-email
    │       │
    │       ├── 유효 → EMAIL_VERIFIED (기존 이메일로 보안 알림 발송)
    │       └── 만료/무효 → EXPIRED (재전송 옵션)
    │
    └── [Cancel] → VIEW_PROFILE (기존 이메일 유지)
```

### Account Deletion Flow

```
VIEW_ACCOUNT ──→ [Delete account 클릭]
    │
    ▼
DELETE_MODAL_OPEN (role="alertdialog")
    │
    ├── 1. 사용자명 입력 (displayName과 정확히 일치)
    ├── 2. "DELETE" 구문 입력
    ├── 3. 현재 비밀번호 입력
    │
    ├── [Cancel] → VIEW_ACCOUNT (모달 닫힘, 초점: Delete account 버튼으로 반환)
    │
    ▼
CONFIRM_DELETE (POST /api/me/delete-account)
    │
    ├── 실패 → ERROR (비밀번호 불일치 / 확인 필드 불일치)
    │
    ▼
DELETION_SCHEDULED (202 Accepted)
    │
    ├── 세션 무효화, 로그아웃 처리
    ├── 14일 유예 기간 시작
    │
    ├── 유예 기간 내 로그인 → "계정 삭제 예정입니다. 취소하시겠습니까?"
    │       ├── [Cancel deletion] → POST /api/me/cancel-deletion → VIEW_PROFILE
    │       └── [Proceed] → 로그아웃
    │
    └── 14일 경과 → 영구 삭제 (백그라운드 작업)
```

---

## Gap Matrix

| Cat | Item | Evidence | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| 🆕 Build | `GET /api/me` — 프로필 조회 API | API Contracts section | — | — | M1 |
| 🆕 Build | `PATCH /api/me` — 표시명 수정 API | API Contracts section | — | — | M1 |
| 🆕 Build | `POST /api/me/avatar` — 아바타 업로드 플레이스홀더 API | API Contracts section | — | — | M1 |
| 🆕 Build | `POST /api/me/email-change` — 이메일 변경 요청 API | API Contracts + OWASP 양방향 확인 | — | MED (계정 탈취) | S2 |
| 🆕 Build | `GET /api/verify-email` — 이메일 확인 API | API Contracts section | — | — | M1 |
| 🆕 Build | `POST /api/me/change-password` — 비밀번호 변경 API | API Contracts + NIST SP 800-63B | — | HIGH (세션 하이재킹) | S2, S3 |
| 🆕 Build | `POST /api/me/delete-account` — 계정 삭제 요청 API | API Contracts + GDPR Article 17 | — | CRIT (데이터 복구 불가) | S2, M1 |
| 🆕 Build | `POST /api/me/cancel-deletion` — 삭제 취소 API | API Contracts section | — | — | M1 |
| 🆕 Build | `ProfileSettingsPage` + 섹션 레이아웃 | Component Hierarchy | — | — | M1 |
| 🆕 Build | `AvatarSection` (이니셜 폴백 + 호버 오버레이 + 파일 선택기) | Radix UI Avatar 패턴, WCAG 2.2 AA | — | LOW | M1 |
| 🆕 Build | `EmailChangeFlow` (3단계: 재인증→입력→확인) | OWASP Cheat Sheet | — | MED | S2 |
| 🆕 Build | `ChangePasswordModal` (세션 회전 포함) | NIST SP 800-63B, OWASP Session Management | — | HIGH | S2 |
| 🆕 Build | `DeleteAccountModal` (3중 확인 + 유예 기간) | GDPR Article 17, NNGroup confirmation patterns | — | CRIT | S2, M1 |
| 🆕 Build | 폼 상태 머신 (`IDLE→DIRTY→SAVING→SUCCESS/ERROR`) | UX Research | — | LOW | M1 |
| 🆕 Build | WCAG 2.2 AA 접근성: `aria-describedby`, `role="alert"`, 초점 관리, ARIA Tabs | WCAG 2.2, ARIA APG (see research) | — | MED | M1 |
| ⬜ Dependency | Unit A 인증 세션 + 사용자 객체 | PRD — Unit A가 세션 토큰 및 사용자 ID 제공 | — | HIGH (의존성) | — |
| ⬜ Dependency | 이메일 발송 인프라 (확인 메일, 보안 알림) | EmailChangeFlow, AccountDeletion flow | — | MED (인프라) | — |

---

## Waves

```yaml
tasks:
  # ── Wave 1 — Foundation (4 tasks, parallel, ≤40 K tokens) ──
  task-W1A:
    wave: 1
    action: "데이터베이스 스키마 — UserProfile, EmailChangeRequest, AccountDeletion, PasswordChangeAudit 테이블 생성 + 인덱스(email unique, userId FK, confirmationToken hash index)"
    files: ["migrations/", "schema/"]
    worker: medium
    depends_on: []
    verify: "migrate up → tables exist; migrate down → clean rollback"
    gate: S1 (dataFlow integrity)
    token_est: ~6K

  task-W1B:
    wave: 1
    action: "API 라우트 스캐폴딩 — 8개 엔드포인트 라우트 정의 (GET/PATCH /api/me, POST /api/me/avatar, POST /api/me/email-change, GET /api/verify-email, POST /api/me/change-password, POST /api/me/delete-account, POST /api/me/cancel-deletion) + 인증 미들웨어 + 속도 제한 미들웨어 (email-change: 3/hour, change-password: 5/hour, delete-account: 2/day, verify-email: 10/hour)"
    files: ["routes/profile.ts", "middleware/auth.ts", "middleware/rateLimit.ts"]
    worker: heavy
    depends_on: []
    verify: "curl 각 엔드포인트 → 401 (인증 없음); 인증 토큰 포함 → 적절한 응답 코드"
    gate: S2 (auth — all 8 endpoints guarded)
    token_est: ~8K

  task-W1C:
    wave: 1
    action: "프로필 조회/수정 API 구현 — GET /api/me (UserProfile 반환), PATCH /api/me (displayName 업데이트), POST /api/me/avatar (파일 업로드 플레이스홀더 — 파일 선택기까지, 실제 처리 파이프라인은 스텁)"
    files: ["handlers/profile.ts", "handlers/avatar.ts", "validators/profile.ts"]
    worker: medium
    depends_on: [task-W1A]
    verify: "GET → 200 + UserProfile; PATCH {displayName} → 200 + updatedAt; PATCH {displayName: ''} → 400"
    gate: M1 (spec-match — matches API Contracts)
    token_est: ~5K

  task-W1D:
    wave: 1
    action: "폼 상태 머신 + 유효성 검증 유틸리티 — `FormState` 상태 머신, `validateEmail`, `validatePassword` (NIST 규칙: 길이 + HIBP 블록리스트), `validateDisplayName` 유틸리티 함수"
    files: ["utils/formState.ts", "utils/validators.ts", "utils/passwordStrength.ts"]
    worker: medium
    depends_on: []
    verify: "단위 테스트: 모든 유효성 검증 함수 — 유효/무효 입력에 대해 올바른 결과 반환; HIBP API 호출 모킹 테스트"
    gate: M2 (test pass=100%)
    token_est: ~4K

  # ── Wave 2 — Core Features (3 tasks, parallel; depends on Wave 1) ──
  task-W2A:
    wave: 2
    action: "이메일 변경 API 구현 — POST /api/me/email-change (현재 비밀번호 검증 → EmailChangeRequest 생성 → 새 이메일로 확인 토큰 발송 → 기존 이메일로 보안 알림), GET /api/verify-email (토큰 검증 → EmailChangeRequest.confirmedAt 설정 → UserProfile.email 업데이트 → user.emailVerified = true)"
    files: ["handlers/emailChange.ts", "handlers/verifyEmail.ts", "services/emailService.ts"]
    worker: heavy
    depends_on: [task-W1B, task-W1A]
    verify: "통합 테스트: 이메일 변경 요청 → EmailChangeRequest 레코드 생성 → 유효 토큰으로 확인 → UserProfile.email 업데이트; 만료 토큰 → 400; 중복 이메일 → 400; 속도 제한 3회 초과 → 429"
    gate: S2 (OWASP 양방향 확인), M2 (test pass=100%)
    token_est: ~8K

  task-W2B:
    wave: 2
    action: "비밀번호 변경 API 구현 — POST /api/me/change-password (현재 비밀번호 검증 → NIST 규칙 검증 + HIBP 블록리스트 확인 → 비밀번호 해시(Argon2id 권장) → PasswordChangeAudit 기록 → 모든 기존 세션 무효화 → 새 세션 발급 + Set-Cookie)"
    files: ["handlers/changePassword.ts", "services/passwordService.ts", "services/sessionService.ts"]
    worker: heavy
    depends_on: [task-W1B, task-W1D]
    verify: "통합 테스트: 유효한 변경 → 200 + 새 세션 토큰 + 기존 세션 무효화 확인; 현재 비밀번호 불일치 → 403; HIBP 블록리스트 비밀번호 → 400; 길이 미달 → 400; 변경 후 기존 세션으로 API 호출 → 401"
    gate: S2 (세션 회전), S3 (Argon2id 해시), M2 (test pass=100%)
    token_est: ~8K

  task-W2C:
    wave: 2
    action: "계정 삭제 API 구현 — POST /api/me/delete-account (3중 확인: displayName 일치 + 'DELETE' 구문 + 현재 비밀번호 검증 → AccountDeletion.status='scheduled', scheduledDeletionAt=now+14d → 세션 무효화 + 로그아웃), POST /api/me/cancel-deletion (status='cancelled')"
    files: ["handlers/deleteAccount.ts", "handlers/cancelDeletion.ts", "services/deletionService.ts"]
    worker: heavy
    depends_on: [task-W1B, task-W1A]
    verify: "통합 테스트: 3중 확인 통과 → 202 + scheduledDeletionAt=now+14d; 사용자명 불일치 → 400; 'DELETE' 구문 불일치 → 400; 비밀번호 불일치 → 403; 속도 제한 2회/일 초과 → 429; 취소 → 200; 없는 삭제 취소 → 404"
    gate: S2 (3중 재인증), M2 (test pass=100%)
    token_est: ~8K

  # ── Wave 3 — UI (3 tasks, parallel; depends on Wave 2) ──
  task-W3A:
    wave: 3
    action: "ProfileSettingsPage + Profile 섹션 UI 구현 — 페이지 레이아웃(2섹션), AvatarSection(Avatar + AvatarOverlay + DisplayNameField, 이니셜 폴백, 호버 오버레이, 파일 선택기 연결, 낙관적 업데이트), EmailSection(EmailDisplay + EmailChangeFlow 3단계 위자드), AccountMeta 읽기 전용 섹션"
    files: ["components/ProfileSettingsPage.tsx", "components/AvatarSection.tsx", "components/EmailSection.tsx", "components/AccountMeta.tsx"]
    worker: heavy
    depends_on: [task-W1C, task-W2A]
    verify: "WCAG 감사: aria-describedby 연결 확인, role='alert' 오류 요약, 아바타 alt='' (표시명과 함께 렌더링), 키보드 탐색 가능; 모든 폼 상태 머신 상태(IDLE/DIRTY/SAVING/SUCCESS/ERROR) 시각적 확인"
    gate: M1 (spec-match — matches Component Hierarchy), WCAG 2.2 AA 체크리스트
    token_est: ~10K

  task-W3B:
    wave: 3
    action: "ChangePasswordModal UI 구현 — 모달 다이얼로그(<dialog> 또는 동등), 현재/새/확인 비밀번호 필드, 실시간 비밀번호 강도 표시기(HIBP API 연동), NIST 요구사항 체크리스트 표시(길이, 블록리스트 통과), 초점 트랩 + Esc 닫기 + 트리거로 초점 반환"
    files: ["components/ChangePasswordModal.tsx", "components/PasswordStrengthMeter.tsx"]
    worker: medium
    depends_on: [task-W2B, task-W1D]
    verify: "스크린리더 테스트: 모달 열기 → 초점 이동, Tab 순환, Esc → 초점 반환; 유효하지 않은 비밀번호 → 실시간 오류 + 제출 버튼 비활성화; 성공 → 토스트 + 모달 닫힘"
    gate: M1 (spec-match — matches Component Hierarchy), WCAG 2.2 AA (초점 관리)
    token_est: ~6K

  task-W3C:
    wave: 3
    action: "DeleteAccountModal UI 구현 — role='alertdialog' 모달, 경고 배너, 데이터 내보내기 링크, 사용자명 입력(displayName과 비교), 'DELETE' 구문 입력, 비밀번호 재인증 필드, 3개 확인이 모두 통과되어야 버튼 활성화, 로딩/에러/성공 상태, 초점 트랩 + Esc 닫기"
    files: ["components/DeleteAccountModal.tsx", "components/ConfirmationInput.tsx"]
    worker: medium
    depends_on: [task-W2C]
    verify: "스크린리더: role='alertdialog' → 경고 내용 즉시 읽음; 하나라도 불일치 → 버튼 비활성화; 모두 통과 → 버튼 활성화; 성공 → 202 수신 + 로그아웃 처리; Esc → 초점이 Delete account 버튼으로 반환"
    gate: M1 (spec-match — matches Component Hierarchy + 3중 확인), WCAG 2.2 AA
    token_est: ~6K

  # ── Wave 4 — Hardening (3 tasks, parallel; depends on Wave 3) ──
  task-W4A:
    wave: 4
    action: "통합 테스트 — 전체 프로필 플로우: GET 프로필 → 표시명 수정 → 이메일 변경(3단계) → 비밀번호 변경 → 계정 삭제(3중 확인) → 삭제 취소 → 프로필 복원. 각 실패 케이스 포함(잘못된 비밀번호, 만료 토큰, 중복 이메일, 속도 제한)"
    files: ["tests/integration/profile.test.ts", "tests/integration/emailChange.test.ts", "tests/integration/passwordChange.test.ts", "tests/integration/accountDeletion.test.ts"]
    worker: heavy
    depends_on: [task-W3A, task-W3B, task-W3C]
    verify: "npm test -- --coverage → 모든 통합 테스트 통과, coverage ≥ 80%"
    gate: M2 (test pass=100%), M3 (no regressions vs Wave 1-3)
    token_est: ~8K

  task-W4B:
    wave: 4
    action: "접근성 감사 — WCAG 2.2 AA 전체 체크리스트: (1) 모든 폼 필드에 <label> + aria-describedby 오류 연결, (2) 모달: 초점 트랩 + Esc + 트리거 초점 반환, (3) 오류 요약: role='alert' + tabindex='-1' + 초점 이동, (4) 아바타: alt='' (장식) / alt='사용자명의 프로필 사진' (정보), (5) 색상 대비: 모든 텍스트/오류/성공 상태 4.5:1 이상, (6) 키보드: 모든 상호작용 Tab/Enter/Esc로 접근 가능"
    files: ["tests/a11y/profile-a11y.test.ts", "docs/ACCESSIBILITY.md"]
    worker: medium
    depends_on: [task-W3A, task-W3B, task-W3C]
    verify: "axe-core 자동 검사 → 0 violations; 수동 체크리스트 6/6 통과"
    gate: M1 (accessibility spec-match)
    token_est: ~5K

  task-W4C:
    wave: 4
    action: "보안 감사 — (1) OWASP 이메일 변경 체크리스트 (양방향 확인, 토큰 TTL 1h, 토큰 해시 저장), (2) NIST 비밀번호 정책 준수 (길이, HIBP, 해시 알고리즘, 문자 조합 강제 금지), (3) 세션 관리 (비밀번호 변경 후 모든 세션 무효화, 새 세션 ID 발급, HttpOnly; Secure; SameSite=Strict), (4) 속도 제한 (이메일 변경 3/h, 비밀번호 변경 5/h, 계정 삭제 2/d), (5) GDPR 삭제 플로우 (소프트삭제 → 14일 유예 → 익명화 → 영구삭제)"
    files: ["docs/SECURITY.md", "tests/security/profile-security.test.ts"]
    worker: medium
    depends_on: [task-W2A, task-W2B, task-W2C]
    verify: "OWASP 체크리스트 5/5, NIST 체크리스트 5/5, 속도 제한 테스트 통과, GDPR 삭제 플로우 문서화"
    gate: S2 (auth + session), S3 (password hashing)
    token_est: ~5K

# Critical path: W1B → W2A → W3A → W4A (4 hops)
# Wave 1 parallelism: 4 concurrent (W1A || W1B || W1C || W1D)
# Wave 2: W2A after W1B+W1A, W2B after W1B+W1D, W2C after W1B+W1A (3 parallel)
# Wave 3: W3A after W1C+W2A, W3B after W2B+W1D, W3C after W2C (3 parallel)
# Wave 4: W4A after W3A+W3B+W3C, W4B after W3A+W3B+W3C, W4C after W2A+W2B+W2C (3 parallel)
```

---

## Risk Register (BKIT 11-Gate)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| API 응답이 명세와 불일치 | `M1_spec_match` | HIGH | matchRate ≥ 90% | API Contracts section에 모든 엔드포인트 응답 형식 명시; 통합 테스트에서 각 엔드포인트 응답 스키마 검증 | `npm test -- --coverage` |
| 테스트 커버리지 미달 | `M2_test_pass` | HIGH | passRate=100%, coverage ≥ 80% | Wave 4A 통합 테스트; Wave 1D 유효성 검증 단위 테스트; 모든 핸들러에 성공/실패 케이스 포함 | `npm test -- --coverage --threshold=80` |
| Unit A 세션 의존성 파괴 | `M3_regression` | MED | 0 regressions | Unit A 토큰 형식 변경 시 Unit B 전수 테스트; CI에서 통합 테스트 자동 실행 | 통합 테스트 전수 통과 |
| 린트/포매팅 불일치 | `M4_lint_clean` | LOW | 0 warnings | 프로젝트 린트 규칙 준수; Wave 4에서 일괄 확인 | `npm run lint` |
| 미사용 코드 | `M5_dead_code` | LOW | 0 unused exports | 모든 API 핸들러, 유틸리티 함수, 컴포넌트가 명세에 매핑되는지 확인 | gap-detector post-implementation |
| 이메일 변경 시 계정 탈취 | `S1_dataFlow` / `S2_auth` | CRIT | 100% 양방향 확인 | OWASP 양방향 확인(기존+새 주소 모두 확인), 현재 비밀번호 재인증, 토큰 SHA-256 해시 저장, 1시간 TTL | 침투 테스트: 토큰 변조 → 400; 만료 토큰 → 400; 재인증 없이 이메일 변경 → 403 |
| 비밀번호 변경 후 세션 하이재킹 | `S2_auth` | CRIT | 변경 후 모든 세션 무효화 | 비밀번호 변경 시 모든 기존 세션 파기 + 새 세션 ID 발급 + Set-Cookie (HttpOnly; Secure; SameSite=Strict) | 변경 후 기존 세션 토큰으로 API 호출 → 401 |
| 취약한 비밀번호 허용 | `S3_injection` | HIGH | HIBP 블록리스트 100% 검사 | NIST SP 800-63B: 최소 8자/15자, HIBP API k-anonymity 검사, 문자 조합 강제 금지, Argon2id 해시 | HIBP에 등록된 비밀번호 입력 → 400 "compromised" |
| GDPR 삭제 미준수 | `S2_auth` / `S1_dataFlow` | CRIT | 14일 유예 + 익명화 + 영구삭제 | 소프트삭제 → 유예 기간(사용자에게 통지) → PII 익명화 → 법적 보존기간 경과 후 영구 삭제. 로그에 PII 잔존 금지 | GDPR Article 17 체크리스트 6/6 통과; 삭제 후 사용자 데이터 조회 → PII 필드 NULL/익명화 |
| 속도 제한 부재로 무차별 공격 | `S2_auth` | MED | email-change: 3/h, password: 5/h, delete: 2/d | 속도 제한 미들웨어가 모든 민감 엔드포인트에 적용; 429 + Retry-After 헤더 | 부하 테스트: 4회 이메일 변경 → 429 |
| 접근성 위반 | `M1_spec_match` | MED | WCAG 2.2 AA 0 violations | Wave 4B 전용 접근성 감사; axe-core 자동화 + 수동 체크리스트; 모든 모달 초점 관리 검증 | `axe-core` → 0 violations; 수동 체크리스트 6/6 |

---

## Execution Command

```
blackcow-loop "Execute plans/simple-app-profile.md" --completion-promise='Profile settings page with view/edit profile, email change verification, password change, account deletion with confirmation — all BKIT gates passing (matchRate ≥ 90%, test pass=100%, coverage ≥ 80%, WCAG 2.2 AA, NIST SP 800-63B compliant, GDPR Article 17 compliant)' --trust-level=2
```

### Parallelism Guide
- **Wave 1**: 4 workers 병렬 (Foundation — schema, routes, profile API, validators)
- **Wave 2**: 3 workers 병렬 (Core Features — email change, password change, account deletion)
- **Wave 3**: 3 workers 병렬 (UI — profile page, password modal, delete modal)
- **Wave 4**: 3 workers 병렬 (Hardening — integration tests, accessibility audit, security audit)
- **Critical path**: W1B → W2A → W3A → W4A (4 hops)
- **Total budget**: ~25K / 128K target (dynamic)
- **Estimated wall-clock**: 3-5 days (1-2 developers 기준)
