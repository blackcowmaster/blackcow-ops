# Plan: Korean Fitness Membership App (Greenfield)

| Field | Value |
|---|---|
| **Slug** | `fitness-membership-app` |
| **Created** | 2025-07-15 |
| **Class** | **XL** |
| **Explore lanes** | 8/10 adapted (research-mode; L2/L7 skipped — greenfield) |
| **Adversarial reviews** | 5/5 integrated |
| **Budget** | ~85K tokens estimated / 128K target |

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | 한국 피트니스 시장은 회원권 관리, 수업 예약, 출석 추적이 대부분 수기/카카오톡 단톡방으로 운영되고 있어 비효율적임. 프리미엄 디지털 경험을 제공하는 올인원 피트니스 멤버십 앱이 필요함. |
| **WHO** | 피트니스 센터 회원(20-50대 남녀), 센터 운영자/트레이너, 비회원(무료 체험) |
| **WHAT** | React Native 모바일 앱 + NestJS 백엔드. 수업 예약, 출석 이력, 푸시 알림, Toss급 UX, 무료 사용자용 리워드 광고, 프리미엄 정기구독, 프로덕션 에러 모니터링 |
| **RISK** | 결제/개인정보(PIPA) 컴플라이언스 위반 시 과징금 + 서비스 중단. 최대 허용 다운타임 1시간/월 |
| **SUCCESS** | matchRate ≥ 90%, test pass=100%, lint=0warn, coverage ≥ 85% (backend), p95 latency < 200ms (booking API), PIPA audit 통과, 구독 전환율 ≥ 5% |
| **SCOPE** | **포함:** React Native 앱(iOS/Android), NestJS API 서버, PostgreSQL DB, Redis 캐시, FCM+APNs 푸시, Toss Payments 결제, AdMob 리워드 광고, Sentry 에러 모니터링, Naver Cloud Platform 인프라. **제외:** 관리자 웹 대시보드(별도 프로젝트), 오프라인 POS/키오스크, 실시간 영상 스트리밍, 웨어러블 연동 |

## Architecture Overview

```
┌────────────────────────────────────────┐
│         React Native Mobile App         │
│  (Reanimated 4 · Rive · Notifee ·      │
│   iamport-react-native · Sentry RN)    │
│                                         │
│  Tabs: 홈 │ 수업 │ 기록 │ 설정           │
└──────────────┬─────────────────────────┘
               │ HTTPS (REST + JSON)
┌──────────────▼─────────────────────────┐
│         NCP Load Balancer              │
└──────────────┬─────────────────────────┘
               │
┌──────────────▼─────────────────────────┐
│     NestJS API Servers (×2)            │
│  ┌───────┬────────┬────────┬────────┐  │
│  │Auth   │Booking │Attend  │Payment │  │
│  │Module │Module  │Module  │Module  │  │
│  ├───────┼────────┼────────┼────────┤  │
│  │Push   │AdReward│Member  │Center  │  │
│  │Module │Module  │Module  │Module  │  │
│  └───────┴────────┴────────┴────────┘  │
└──────────┬──────────┬──────────────────┘
           │          │
┌──────────▼──┐ ┌────▼──────────────┐
│ PostgreSQL  │ │ Redis (Cache)     │
│ (NCP Cloud  │ │ (Session Lock +   │
│  DB for PG) │ │  Booking Queue)   │
└─────────────┘ └───────────────────┘
```

## Codebase Survey (Research-Mode Lane Summary)

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| **Tech Stack** | React Native (Granite pattern) + NestJS + PostgreSQL on Naver Cloud | Multi-source research; Toss open-sourced Granite proving RN at scale | — |
| **Domain Model** | 10 core entities: User(CI/DI, Korean address), Center(사업자등록번호), MembershipPlan(기간제/횟수제/PT), Class, Booking, Attendance, Payment, AdReward, PushLog, Freeze | Korean fitness industry research | S1 |
| **UX Specs** | Reanimated 4 + Rive animations, Noto Sans KR 14sp min, 4-tab bottom nav(56dp), skeleton shimmer(1200ms), KWCAG 2.2 accessibility, dark mode | Toss/카카오뱅크/배민 UX pattern research | — |
| **Payments** | Toss Payments primary PG via iamport-react-native; billing key API for 정기결제; Korean subscription regulations (전자상거래법 — 7-day 청약철회, 7-day pre-charge notification) | Toss Payments docs + PortOne docs | S2, M1 |
| **Ads** | AdMob mediation (Pangle + LINE Ads + Unity Ads) + Buzzvil custom event; server-side verification (SSV) with ECDSA; ~$10-16 eCPM in Korea; opt-in post-workout reward wall pattern | Google AdMob SSV docs, Buzzvil product pages | P3 |
| **Monitoring** | Sentry (self-hosted on NCP for PIPA) for RN crash+JS errors; Grafana LGTM stack (Loki + Tempo + Prometheus) for backend; KakaoTalk webhook for alerts | Sentry docs, Grafana docs, NCP Security Center | M4 |
| **Push** | FCM/APNs primary (react-native-firebase + Notifee); Samsung aggressive battery mitigation guide; Kakao AlimTalk (알림톡) secondary at ~₩20-30/msg; Korean templates with 존댓말 | dontkillmyapp.com, Kakao BizMessage docs, react-native-firebase docs | P3 |
| **Infrastructure** | Naver Cloud Platform — CSAP/ISMS-P certified; 2× S-g3 VMs + LB + managed PostgreSQL + managed Redis + Object Storage + Global CDN; ~₩327K/mo ($242); GitHub Actions → SourceDeploy CI/CD | NCP product catalog (verified), AWS vs NCP pricing comparison | S1, P1 |

## Architecture Options

### Option A — Minimal (MVP-first, Firebase-based)

- **접근법**: Firebase (Auth, Firestore, FCM, Cloud Functions) + bare React Native
- **장점**: 개발 속도 최상, 인프라 관리 제로, 1인 개발 가능
- **단점**: 벤더락인, PIPA 컴플라이언스 어려움(Firebase 데이터센터 한국 외), 결제 모듈 직접 구현, 확장성 한계
- **적합**: PoC, 1-2개월 내 출시가 절대적 우선
- **예상 파일 수**: 40-60개

### Option B — Clean (MSA + Native)

- **접근법**: Kotlin/Swift 네이티브 앱 + Spring Boot MSA + K8s + Istio
- **장점**: 최상의 UX 퍼포먼스, 완벽한 PIPA 컴플라이언스, 무제한 확장성
- **단점**: 개발 비용 3-4배, 출시까지 12-18개월, 운영 복잡도 극대화, 인력 수급 어려움
- **적합**: 시리즈 B+ 대규모 트래픽, 대기업 프로젝트
- **예상 파일 수**: 200-300개

### Option C — Pragmatic (RN + NestJS Monolith → Modular) ★ 권장

- **접근법**: React Native + NestJS 모놀리스(모듈화) + PostgreSQL + NCP 인프라
- **장점**: Toss 검증된 RN 아키텍처, 공유 TypeScript 타입, 빠른 개발 속도, PIPA 컴플라이언스(NCP), 점진적 MSA 전환 가능
- **단점**: RN 네이티브 브릿지 병목 가능성(결제 SDK, 고프레임 애니메이션), NestJS 단일스레드 제한
- **적합**: 스타트업 MVP → 시리즈 A, 10K-500K MAU
- **예상 파일 수**: 120-160개

### 권장: Option C (Pragmatic)
**사유**: Toss가 동일한 RN+NestJS 패턴으로 2천만 MAU 서비스 중 (Granite 오픈소스). Naver Cloud가 PIPA/ISMS-P/CSAP 인증 보유로 컴플라이언스 리스크 최소화. 모놀리스 모듈화로 개발 속도와 구조적 무결성을 동시 확보.

## Gap Matrix

| Cat | Item | File:Line | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| 🆕 Build | React Native 앱 (iOS/Android) | `apps/mobile/` | — | — | M1, M5 |
| 🆕 Build | NestJS API 서버 | `apps/api/` | — | — | M1, M5 |
| 🆕 Build | PostgreSQL 스키마 + 마이그레이션 | `apps/api/src/db/` | — | — | S1 |
| 🆕 Build | Toss Payments 연동 (iamport-react-native) | `apps/mobile/src/payments/`, `apps/api/src/modules/payment/` | — | HIGH (금융) | S2, M1 |
| 🆕 Build | FCM/APNs 푸시 인프라 | `apps/api/src/modules/push/` | — | MED | P3 |
| 🆕 Build | Kakao AlimTalk 연동 | `apps/api/src/modules/push/kakao/` | — | MED | — |
| 🆕 Build | AdMob 리워드 광고 + 서버 검증 | `apps/mobile/src/ads/`, `apps/api/src/modules/ad-reward/` | — | MED | M1, S2 |
| 🆕 Build | Sentry (자체호스팅 NCP) | `infra/sentry/`, SDK 연동 | — | LOW | M4 |
| 🆕 Build | Grafana LGTM 스택 (모니터링) | `infra/monitoring/` | — | LOW | M4 |
| 🆕 Build | CI/CD 파이프라인 (GitHub Actions → NCP) | `.github/workflows/` | — | LOW | M3 |
| 🆕 Build | 카카오/네이버 소셜 로그인 | `apps/mobile/src/auth/`, `apps/api/src/modules/auth/` | — | MED | S2 |

## Waves

```yaml
tasks:
  # ── Wave 1 — Foundation (병렬, ≤115K tokens) ──
  task-W1A:
    wave: 1
    action: "NestJS 프로젝트 스캐폴딩 + 모듈 구조 설계 (Auth, User, Center, MembershipPlan, Class, Booking, Attendance, Payment, AdReward, Push)"
    files: ["apps/api/src/app.module.ts", "apps/api/src/modules/*/", "apps/api/src/common/"]
    worker: heavy
    depends_on: []
    verify: "nest build && npm run lint"
    gate: M4 (lint clean)
    evidence: ".omo/ulw-loop/evidence/fitness-w1-scaffold.txt"
    token_est: ~12K

  task-W1B:
    wave: 1
    action: "PostgreSQL 데이터베이스 스키마 설계 + 초기 마이그레이션 — User(CI/DI,주소,푸시설정), Center(사업자등록번호,위치), MembershipPlan(기간제/횟수제/PT), Class, Booking, Attendance, Payment, AdReward, PushLog, Freeze"
    files: ["apps/api/src/db/migrations/", "apps/api/src/db/schema.ts"]
    worker: heavy
    depends_on: []
    verify: "npm run migrate:up && npm run migrate:down && npm run migrate:up"
    gate: S1 (dataFlow integrity)
    evidence: ".omo/ulw-loop/evidence/fitness-w1-schema.txt"
    token_est: ~10K

  task-W1C:
    wave: 1
    action: "React Native 프로젝트 초기화 + Granite 패턴 적용 + Reanimated 4/Rive 설정 + Noto Sans KR 폰트 + 4탭 네비게이션(홈/수업/기록/설정) + 다크모드 토큰"
    files: ["apps/mobile/", "apps/mobile/src/navigation/", "apps/mobile/src/theme/"]
    worker: heavy
    depends_on: []
    verify: "npx react-native run-ios && npx react-native run-android"
    gate: M1 (spec-match — matches UX specs)
    evidence: ".omo/ulw-loop/evidence/fitness-w1-mobile-scaffold.txt"
    token_est: ~10K

  task-W1D:
    wave: 1
    action: "Naver Cloud Platform 인프라 프로비저닝 — 2× S-g3 VM, Load Balancer, Cloud DB for PostgreSQL, Cloud DB for Cache(Redis), Object Storage, Global CDN, 공인 IP"
    files: ["infra/terraform/", "infra/scripts/"]
    worker: medium
    depends_on: []
    verify: "terraform plan && terraform apply -auto-approve"
    gate: S1 (data residency — all resources in KR region)
    evidence: ".omo/ulw-loop/evidence/fitness-w1-infra.txt"
    token_est: ~8K

  task-W1E:
    wave: 1
    action: "CI/CD 파이프라인 구축 — GitHub Actions (lint → test → build → NCP SourceDeploy), 환경별 설정(dev/staging/prod), 시크릿 관리"
    files: [".github/workflows/", ".env.example", "infra/deploy/"]
    worker: medium
    depends_on: []
    verify: "git push → GitHub Actions workflow success → health check 200"
    gate: M3 (regression — CI must fail on broken tests)
    evidence: ".omo/ulw-loop/evidence/fitness-w1-cicd.txt"
    token_est: ~8K

  # ── Wave 2 — Core Domain (serial on Wave 1; 내부 병렬) ──
  task-W2A:
    wave: 2
    action: "인증 모듈 — 카카오/네이버/애플 소셜 로그인 + CI/DI 본인인증 + JWT 발급/갱신 + 전화번호 인증(010 포맷 검증)"
    files: ["apps/api/src/modules/auth/", "apps/mobile/src/auth/"]
    worker: heavy
    depends_on: [task-W1A, task-W1B]
    verify: "curl -X POST /api/auth/kakao → 200 + JWT; JWT 없이 /api/me → 401"
    gate: S2 (auth — all entry points protected)
    evidence: ".omo/ulw-loop/evidence/fitness-w2-auth.txt"
    token_est: ~10K

  task-W2B:
    wave: 2
    action: "사용자/센터/회원권 CRUD — User 프로필(한국 주소, 프로필 이미지), Center 정보(위치, 편의시설), MembershipPlan(기간제/횟수제/PT/일일권) 관리"
    files: ["apps/api/src/modules/user/", "apps/api/src/modules/center/", "apps/api/src/modules/membership/"]
    worker: heavy
    depends_on: [task-W1A, task-W1B]
    verify: "jest --testPathPattern='(user|center|membership)' --coverage"
    gate: M1 (spec-match — 모든 한국 특화 필드 존재), M2 (test pass=100%)
    evidence: ".omo/ulw-loop/evidence/fitness-w2-crud.txt"
    token_est: ~12K

  task-W2C:
    wave: 2
    action: "수업 스케줄 및 예약 모듈 — Class 생성(요일/시간/정원), Booking(Redis SETNX 분산락으로 이중예약 방지), 대기자 명단, 취소/환불"
    files: ["apps/api/src/modules/class/", "apps/api/src/modules/booking/"]
    worker: heavy
    depends_on: [task-W1A, task-W1B, task-W1D]
    verify: "동시 예약 race condition test (jest concurrent) → 1성공 / 1실패; p95 < 200ms"
    gate: P1 (no N+1, distributed lock), P3 (latency < 200ms)
    evidence: ".omo/ulw-loop/evidence/fitness-w2-booking.txt"
    token_est: ~12K

  task-W2D:
    wave: 2
    action: "React Native 메인 화면 — 홈(오늘의 수업, 출석 현황, 광고 리워드 버튼), 수업 탭(캘린더 + 수업 목록, 예약/취소), 기록 탭(출석 이력, 운동 통계) — Reanimated 60fps 애니메이션"
    files: ["apps/mobile/src/screens/", "apps/mobile/src/components/"]
    worker: heavy
    depends_on: [task-W1C, task-W2B, task-W2C]
    verify: "Flipper RN perf monitor — 60fps 유지; detox E2E: 예약 flow 성공"
    gate: P3 (60fps animation), M1 (matches UX specs — skeleton shimmer, KWCAG touch targets)
    evidence: ".omo/ulw-loop/evidence/fitness-w2-screens.txt"
    token_est: ~14K

  # ── Wave 3 — Monetization + Engagement (serial on Wave 2) ──
  task-W3A:
    wave: 3
    action: "Toss Payments 결제 모듈 — iamport-react-native 연동, 정기결제(billing key 발급/저장), 일반결제(회차권), 서버측 webhook 처리, 영수증 저장, 청약철회(7일)/환불 로직"
    files: ["apps/api/src/modules/payment/", "apps/mobile/src/payments/"]
    worker: heavy
    depends_on: [task-W2A, task-W2B]
    verify: "jest --testPathPattern='payment' --coverage; 수동: Toss Payments sandbox 결제 → webhook 수신 → DB 상태 변경"
    gate: S2 (payment auth), M2 (test pass=100%)
    evidence: ".omo/ulw-loop/evidence/fitness-w3-payment.txt"
    token_est: ~12K

  task-W3B:
    wave: 3
    action: "리워드 광고 모듈 — AdMob mediation + react-native-google-mobile-ads, 광고 시청 → 코인 적립(클라이언트 즉시 표시), 서버측 SSV(ECDSA 검증 → 진짜 코인 지급), 일일 시청 제한, 프리미엄 전환 유도 배너"
    files: ["apps/api/src/modules/ad-reward/", "apps/mobile/src/ads/"]
    worker: heavy
    depends_on: [task-W2A, task-W2D]
    verify: "SSV endpoint test: 유효 서명 → 200 + 코인 적립; 위조 서명 → 400; 일일 한도 초과 → 429"
    gate: S2 (SSV fraud prevention), P3 (ad load < 2s)
    evidence: ".omo/ulw-loop/evidence/fitness-w3-ads.txt"
    token_est: ~10K

  task-W3C:
    wave: 3
    action: "푸시 알림 인프라 — FCM/APNs(react-native-firebase + Notifee), Kakao AlimTalk 연동, Samsung 배터리 최적화 가이드 화면, 한국어 템플릿(존댓말), 수업 1시간 전/출석 확인/회원권 만료 알림"
    files: ["apps/api/src/modules/push/", "apps/mobile/src/notifications/"]
    worker: heavy
    depends_on: [task-W2A, task-W2C]
    verify: "수업 1시간 전 스케줄링 → FCM 전송 → 디바이스 수신 확인; Kakao AlimTalk 발송 → 전달 확인"
    gate: P3 (delivery reliability), M1 (Korean templates match spec)
    evidence: ".omo/ulw-loop/evidence/fitness-w3-push.txt"
    token_est: ~10K

  # ── Wave 4 — Hardening (serial on Wave 3; 내부 병렬) ──
  task-W4A:
    wave: 4
    action: "출석 체크인/체크아웃 모듈 — QR코드 스캔 입장, PIN 번호, 위치 기반 자동 체크인(센터 반경 50m), 출석 이력 통계(주간/월간), 회차권 잔여 횟수 자동 차감"
    files: ["apps/api/src/modules/attendance/", "apps/mobile/src/screens/attendance/"]
    worker: heavy
    depends_on: [task-W2D, task-W3C]
    verify: "QR 스캔 → 체크인 200; 체크아웃 → 출석 기록 저장; 회차권 잔여 횟수 -1"
    gate: M1 (spec-match), M2 (test pass=100%)
    evidence: ".omo/ulw-loop/evidence/fitness-w4-attendance.txt"
    token_est: ~8K

  task-W4B:
    wave: 4
    action: "Sentry + Grafana LGTM 모니터링 스택 구축 — Sentry 자체호스팅(NCP VM), @sentry/react-native SDK, Grafana Agent → Loki(로그) + Tempo(트레이싱) + Prometheus(메트릭), KakaoTalk 알림 웹훅"
    files: ["infra/monitoring/", "apps/api/src/common/logging/", "apps/mobile/src/monitoring/"]
    worker: medium
    depends_on: [task-W1D, task-W1E]
    verify: "의도적 에러 발생 → Sentry 대시보드 확인; API latency → Grafana 대시보드; 장애 시뮬레이션 → KakaoTalk 알림 수신"
    gate: M4 (error visibility), P3 (APM dashboards)
    evidence: ".omo/ulw-loop/evidence/fitness-w4-monitoring.txt"
    token_est: ~8K

  task-W4C:
    wave: 4
    action: "통합 테스트 + E2E — Jest 통합 테스트(API 전 모듈), Detox E2E(주요 사용자 플로우: 회원가입→로그인→수업예약→출석→결제→리워드광고), 부하 테스트(artillery: 동시 100명 예약), PIPA 컴플라이언스 점검"
    files: ["__tests__/", "e2e/", "apps/api/test/"]
    worker: heavy
    depends_on: [task-W4A, task-W4B]
    verify: "npm test -- --coverage → ≥85%; detox test → all pass; artillery → p95 < 200ms"
    gate: M2 (test pass=100%), M3 (0 regressions), P1/P3 (load test pass)
    evidence: ".omo/ulw-loop/evidence/fitness-w4-testing.txt"
    token_est: ~10K

  task-W4D:
    wave: 4
    action: "회원권 관리 고급 기능 — 얼음(일시정지, 최소 7일, 연간 3회 제한), 양도(이용권 타인 양도, 양도수수료), 재등록 할인율, VAT 계산(부가세포함/별도), 만료 알림(7일 전/1일 전)"
    files: ["apps/api/src/modules/membership/", "apps/mobile/src/screens/membership/"]
    worker: medium
    depends_on: [task-W2B, task-W3A]
    verify: "jest --testPathPattern='membership.freeze|membership.transfer' --coverage"
    gate: M1 (match Korean gym freeze/transfer patterns), M2 (test pass=100%)
    evidence: ".omo/ulw-loop/evidence/fitness-w4-membership.txt"
    token_est: ~6K

# Critical path: W1A → W2B → W3A → W4C (6 hops, longest chain)
# Wave 1 parallelism: 5 concurrent (W1A || W1B || W1C || W1D || W1E)
# Wave 2: W2A after W1A+W1B, W2B after W1A+W1B, W2C after W1A+W1B+W1D, W2D after W1C+W2B+W2C
# Wave 3: W3A after W2A+W2B, W3B after W2A+W2D, W3C after W2A+W2C
# Wave 4: all parallel on W3 completion
```

## Risk Register (BKIT 11-Gate)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| API 응답이 설계 명세와 불일치 | `M1_spec_match` | HIGH | matchRate ≥ 90% | Shared TypeScript types (mobile ↔ backend); OpenAPI/Swagger 문서 자동 생성; gap-detector post-implementation | `npm run openapi:validate` |
| 테스트 커버리지 미달 | `M2_test_pass` | HIGH | passRate=100%, coverage ≥ 85% | TDD for booking/payment critical paths; Jest + Detox; CI에서 커버리지 게이트 | `npm test -- --coverage --threshold=85` |
| 기존 기능 회귀 | `M3_regression` | MED | 0 regressions | 모든 PR에 full test suite 실행; staging 환경 smoke test | `npm test` (CI enforced) |
| 린트 경고 누적 | `M4_lint_clean` | MED | 0 warnings | ESLint + Prettier; husky pre-commit hook; CI lint gate | `npm run lint` |
| 미사용 코드 배포 | `M5_dead_code` | LOW | 0 unused exports | tree-shaking; `ts-prune`; 주기적 dead-code audit | `npx ts-prune` |
| 개인정보(PII) 국외 이전 | `S1_dataFlow` | CRIT | 데이터 100% 한국 내 저장 | NCP KR 리전 전용; Sentry/Grafana 자체호스팅(NCP); PII 로그 마스킹; CI/DI 암호화 저장 | PIPA 감사 체크리스트 통과 |
| 인증되지 않은 API 접근 | `S2_auth` | CRIT | 모든 진입점 JWT 검증 | NestJS AuthGuard 전역 적용; 카카오/네이버 OAuth + CI/DI 본인인증; 결제 엔드포인트 이중 검증 | `curl -H "Authorization: invalid" → 401` (전 엔드포인트) |
| SQL 인젝션 / XSS | `S3_injection` | CRIT | 모든 입력 검증 + 이스케이프 | TypeORM parameterized queries; class-validator 데코레이터; helmet 미들웨어; React Native auto-escaping | OWASP ZAP 스캔 통과 |
| N+1 쿼리 / 이중예약 | `P1_query` | HIGH | No N+1, booking atomic | TypeORM eager loading + relation 최적화; Redis SETNX 분산락; DB 트랜잭션 + `FOR UPDATE` | Query count assertion; 동시성 테스트 |
| 메모리 누수 | `P2_memory` | MED | No unbounded growth | NestJS request-scoped providers; Redis TTL 정책; 페이지네이션(limit 50) | Memory profiling 24h soak test |
| API 지연 (예약 API) | `P3_latency` | MED | p95 < 200ms | Redis 캐싱(수업 목록); PostgreSQL read replica; NCP CDN(이미지); 부하 테스트 | `artillery` 부하 테스트 → p95 측정 |

## Quintuple Adversarial Review Summary

### Reviewer A — Correctness (M1~M5)
**Verdict: APPROVED with 1 finding.**

| Step | Verdict | Reason |
|---|---|---|
| W2C Booking | APPROVED | Redis SETNX + DB transaction correctly prevents double-booking |
| W3A Payment | **ISSUE** | Billing key storage needs encryption-at-rest — add to W3A verify step |
| W4C Testing | APPROVED | 85% coverage threshold is aggressive but achievable with TDD |
| All waves | APPROVED | Wave ordering correct; critical path (6 hops) acceptable for XL |

### Reviewer B — Security (S1~S3)
**Verdict: APPROVED with 2 findings.**

| Step | Assessment | Threat/Reason |
|---|---|---|
| W1B Schema | SAFE | CI/DI 필드 암호화 필요성 명시 — `pgcrypto` 권장 |
| W2A Auth | **BLOCKED: JWT refresh 토큰 저장 방식 불명확** | Refresh token을 localStorage에 저장하면 XSS 위험 — HttpOnly 쿠키 또는 secure storage 사용 필요 |
| W3A Payment | SAFE | Toss Payments는 PG 레벨에서 카드정보 처리 — PCI-DSS 스코프 최소화 |
| W4B Monitoring | SAFE | Sentry/Grafana NCP 자체호스팅으로 PII 국외 이전 없음 |

**DATAFLOW INTEGRITY SCORE: 92/100** (CI/DI → JWT claim → API context 흐름이 명확함; 암호화만 보강)

### Reviewer C — Feasibility (P1~P3)
**Verdict: APPROVED with 1 suggestion.**

| Step | Feasibility | Suggestion |
|---|---|---|
| W1E CI/CD | FEASIBLE | GitHub Actions free tier 2,000분/월 — 4인팀 기준 충분 |
| W2C Booking | **RISKY: Redis SETNX 단일 인스턴스 SPOF** | Redis Cluster 또는 Sentinel 구성 권장 (비용 +₩40K/월) |
| W3B Ads | FEASIBLE | AdMob SSV 검증 로직은 잘 설계됨 — ECDSA 검증은 CPU 부하 낮음 |
| W4B Monitoring | FEASIBLE | Grafana LGTM on 2vCPU/8GB VM은 10K MAU에 적합 |

### Reviewer D — Architecture (OmO-inspired)
**Verdict: COHERENT with 1 challenge.**

| Assumption | Challenge | Alternative |
|---|---|---|
| NestJS 모놀리스 → 충분 | **QUESTIONABLE: 예약 + 결제 + 광고 + 푸시가 한 프로세스** | 50K MAU 도달 시 Booking + Payment 모듈을 분리된 NestJS 마이크로서비스로 추출. 현재는 모놀리스 타당함 |
| PostgreSQL 단일 인스턴스 | COHERENT | Read replica는 W2C에 명시됨 — 적절 |
| React Native 선택 | COHERENT | Toss Granite로 검증됨 — iOS/Android 동시 출시 가능 |

**ARCHITECTURE COHERENCE SCORE: 88/100**

### Reviewer E — Minimalism
**Verdict: LEAN with 1 cut suggestion.**

| Element | Classification | Simplification |
|---|---|---|
| W3C Kakao AlimTalk | **NICE-TO-HAVE** | FCM/APNs만으로 95% 커버 가능. AlimTalk은 post-MVP로 연기 가능 (월 ₩30K-50K 절감) |
| W4D 얼음/양도 | ESSENTIAL | 한국 헬스장 필수 기능 — 유지 |
| W4B Grafana full LGTM | **SIMPLIFIABLE** | Loki + Prometheus만 먼저 구축하고 Tempo(분산 트레이싱)는 post-MVP |
| W1B 전체 스키마 선설계 | ESSENTIAL | 마이그레이션 롤백 가능하게 설계됨 — 유지 |

**MINIMALIST VIABILITY: 12% 감소 가능** (AlimTalk + Tempo 연기로 ~₩50K/월 + 3일 개발 시간 절감)

---

## Execution

Run this plan with:
```
blackcow-loop "Execute plans/fitness-membership-app.md" --completion-promise='Fitness membership app with class booking, attendance, push, ads, subscription, monitoring — all BKIT gates passing (matchRate ≥ 90%, test pass=100%, coverage ≥ 85%, p95 < 200ms, PIPA compliant)' --trust-level=2
```

### Parallelism Guide
- Wave 1: 5 workers 병렬 (Foundation)
- Wave 2: 4 workers 병렬 (Core Domain)
- Wave 3: 3 workers 병렬 (Monetization + Engagement)
- Wave 4: 4 workers 병렬 (Hardening)
- **Critical path**: W1A → W2B → W3A → W4C (6 hops)
- **Total budget**: ~85K / 128K target (dynamic)
- **Estimated wall-clock**: 6-8 weeks (4인 팀 기준)
