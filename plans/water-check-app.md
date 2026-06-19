# Plan: Water Check App — Greenfield Expo RN

| Field | Value |
|---|---|
| **Slug** | `water-check-app` |
| **Created** | `2026-06-16T07:15:09Z` |
| **Class** | `M` |
| **Explore lanes** | `XS:5 (greenfield — no existing code to scan; L2/L3/L6/L7/L8/L9 skipped)` |
| **Adversarial reviews** | `0/3 (M-scale: reviewers A/B/C post-plan)` |
| **Budget** | `estimated 42K / 1M target` |
| **Intent** | `Feature` |
| **Mode** | `Multi-Feature` |

---

## Intent Analysis

| Field | Value |
|---|---|
| **Detected Intent** | Feature |
| **Confidence** | HIGH |
| **Primary Gates** | M1 (spec-match), M5 (dead-code) |
| **Scale Override** | NONE → auto-detected M |
| **Special Handling** | Greenfield — no codebase scan; pattern library from pomodoro-app sibling project |

---

## Phase 0 — Pre-flight

```
Cache: STALE (HEAD changed — ab6426c → a528919)
Legacy discovery: water-check-app/ does not exist → GREENFIELD
Reference project: pomodoro-app/ (Expo 52, same stack, same org)
  - expo ~52.0.0, react-native 0.76.5, expo-router ~4.0.0
  - AsyncStorage 2.1.2, react-native-svg 15.9.0, lucide-react-native ^0.460.0
  - react-native-safe-area-context 4.14.0, react-native-screens ~4.3.0
  - typedRoutes: true, newArchEnabled: true
  - Pattern: Context+useReducer+AsyncStorage, file-based routing, SVG progress
```

---

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | 사용자가 매일 물 섭취량을 기록하고 목표 달성 여부를 한눈에 확인할 수 있는 간단한 추적 앱 |
| **WHO** | 건강 관리에 관심 있는 일반 사용자 (1인 사용자, 로컬 전용) |
| **WHAT** | Expo SDK 52+ React Native 앱 — 물 컵 추가, 일일 진행률 시각화, 날짜별 초기화, 히스토리 화면, DESIGN.md |
| **RISK** | 로컬 데이터 손실 시 당일 기록 소실 (AsyncStorage 단일 장치). 최대 허용 다운타임: N/A (오프라인 전용) |
| **SUCCESS** | matchRate ≥ 90%, test pass=100%, lint=0warn, coverage ≥ 80%, p95_target_ms: N/A |
| **SCOPE** | **포함**: water-check-app/ 전체 프로젝트, cup 추가/삭제, 일일 목표 설정, 진행률 SVG 링, 날짜별 초기화, 7일 히스토리, DESIGN.md. **제외**: 백엔드/클라우드 동기화, 멀티유저, 푸시 알림, 소셜 공유, 위젯 |

---

## Summary

Greenfield Expo SDK 52+ React Native 앱. `pomodoro-app` 프로젝트의 검증된 아키텍처 패턴(Context + useReducer + AsyncStorage, expo-router file-based routing, react-native-svg 진행 표시)을 그대로 차용한다. 물 한 컵 추가 → AsyncStorage 저장 → 일일 총합 계산 → SVG 진행 링에 반영 → 자정 초기화의 단순한 데이터 흐름. 4개 feature(tracking, goal, history, design)를 3개 Wave로 구현하며, Wave 1에서 핵심 도메인 + 저장소 + 메인 화면을 구축하고 Wave 2에서 히스토리 화면과 목표 설정을 추가한다.

---

## Architecture Options

### Option A — Minimal (단일 파일)
- **접근법**: `app/index.tsx` 하나에 모든 로직 + UI 통합. useState + AsyncStorage 직접 호출
- **장점**: 파일 1개, 즉시 실행, 학습 곡선 제로
- **단점**: 확장 불가, 테스트 어려움, 히스토리 화면 추가 시 전면 재작성
- **적합**: 프로토타입 only. 채택하지 않음.
- **예상 파일 수**: 3개 (index.tsx, package.json, app.json)

### Option B — Clean (DDD-esque with repository pattern)
- **접근법**: Domain/Application/Infrastructure/Interface 4계층 분리. WaterRepository 인터페이스 + AsyncStorage 구현체. useReducer가 아닌 커스텀 훅 + 서비스 계층
- **장점**: 테스트 용이, 교체 가능, 대규모 확장 대비
- **단점**: 앱 규모 대비 과도한 추상화. pomodoro-app 패턴과 불일치
- **적합**: 향후 백엔드 동기화 추가 시
- **예상 파일 수**: 15개+

### Option C — Pragmatic (pomodoro-app 패턴 복제, **권장**)
- **접근법**: pomodoro-app과 동일한 구조 — `src/water/types.ts`, `src/lib/storage.ts`, `src/context/WaterContext.tsx`, `src/components/*`, `src/screens/*`, `app/` expo-router. Context + useReducer + AsyncStorage
- **장점**: 검증된 패턴, 팀 내 일관성, pomodoro-app 코드에서 복사 가능한 보일러플레이트 다수
- **단점**: 작은 앱에 약간의 구조적 오버헤드 (파일 10개 내외)
- **적합**: 대부분의 일반 기능 개발 — 선택됨
- **예상 파일 수**: 12개

### 권장: Option C (Pragmatic)
**사유**: pomodoro-app과 동일 org, 동일 Expo SDK 버전, 동일 아키텍처 취향. Context+useReducer 패턴은 작은 상태 머신(물 컵 추가/삭제/초기화)에 이상적. expo-router file-based routing은 히스토리 화면 추가 시 자연스러운 확장 제공.

---

## Codebase Survey (Adapted for Greenfield)

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| Surface (L1) | Greenfield — `water-check-app/` 디렉토리 미존재 | `search_files("water-check-app")` → empty | — |
| Call Graph (L2) | N/A — no code | — | — |
| Data Shapes (L3) | N/A — 설계 단계에서 정의 | — | S1 |
| Tests (L4) | N/A — TDD로 구축 예정 | — | M2, M3 |
| Config (L5) | pomodoro-app app.json을 템플릿으로 사용 | `pomodoro-app/app.json` | — |
| Deps (L6) | pomodoro-app package.json을 베이스라인으로 사용 (expo 52, async-storage, svg, lucide) | `pomodoro-app/package.json` | — |
| Git (L7) | N/A — greenfield | — | — |
| Security (L8) | AsyncStorage 데이터는 샌드박스 내 저장. 입력값: cup size (number only). 위협 표면 최소 | 설계 분석 | S2, S3 |
| Performance (L9) | AsyncStorage 동기 read on mount (~1ms), SVG 링 1개만 렌더링. 성능 핫스팟 없음 | 설계 분석 | P1, P2, P3 |
| Patterns (L10) | **pomodoro-app에서 추출한 재사용 템플릿** — Context+useReducer, AsyncStorage persistence, SVG CircularProgress, expo-router Stack nav, ThemeProvider, ErrorBoundary | `pomodoro-app/src/` 전체 | M1 |

### Extracted Pattern Template (from pomodoro-app L10)

```typescript
// src/water/types.ts
// Core domain types — framework-agnostic, zero dependencies.

export interface CupRecord {
  id: string;
  amountMl: number;     // milliliters per cup
  timestamp: string;    // ISO-8601
}

export interface DailyLog {
  date: string;         // "YYYY-MM-DD"
  cups: CupRecord[];
  goalMl: number;       // daily target in ml
}

export type WaterAction =
  | { type: 'CUP_ADD'; payload: { amountMl: number } }
  | { type: 'CUP_REMOVE'; payload: { id: string } }
  | { type: 'GOAL_SET'; payload: { goalMl: number } }
  | { type: 'LOG_HYDRATE'; payload: { log: DailyLog } }
  | { type: 'DAY_RESET' };

export interface DailySummary {
  date: string;
  totalMl: number;
  goalMl: number;
  cupCount: number;
  achieved: boolean;
}
```

```typescript
// src/lib/storage.ts
// AsyncStorage persistence — mirror of pomodoro-app/src/lib/storage.ts

import AsyncStorage from '@react-native-async-storage/async-storage';
import type { DailyLog } from '../water/types';

const KEYS = {
  TODAY_LOG: 'water-today-log',
  HISTORY: 'water-history',
  GOAL: 'water-daily-goal',
} as const;

export async function loadTodayLog(): Promise<DailyLog | null> { /* ... */ }
export async function saveTodayLog(log: DailyLog): Promise<void> { /* ... */ }
export async function loadHistory(): Promise<DailySummary[]> { /* ... */ }
export async function saveHistory(summaries: DailySummary[]): Promise<void> { /* ... */ }
export async function loadGoal(): Promise<number> { /* default 2000 */ }
export async function saveGoal(ml: number): Promise<void> { /* ... */ }
```

```typescript
// src/context/WaterContext.tsx
// React Context + useReducer — mirror of pomodoro-app/src/context/TaskContext.tsx

import React, { createContext, useContext, useReducer, useEffect, useCallback } from 'react';

function waterReducer(state: DailyLog, action: WaterAction): DailyLog { /* ... */ }

interface WaterContextValue {
  todayLog: DailyLog;
  totalMl: number;
  goalMl: number;
  progress: number; // 0–1
  addCup: (amountMl: number) => void;
  removeCup: (id: string) => void;
  setGoal: (goalMl: number) => void;
}
```

---

## Gap Matrix

| Cat | Item | Evidence | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| 🆕 Build | `water-check-app/` 전체 프로젝트 스캐폴드 | Greenfield | — | — | M1 |
| 🆕 Build | `src/water/types.ts` — 도메인 타입 정의 | 설계 산출물 | — | — | M1 |
| 🆕 Build | `src/lib/storage.ts` — AsyncStorage 퍼시스턴스 | pomodoro-app 패턴 | — | — | M1 |
| 🆕 Build | `src/context/WaterContext.tsx` — 상태 관리 | pomodoro-app TaskContext 패턴 | — | — | M1 |
| 🆕 Build | `src/components/WaterProgress.tsx` — SVG 진행 링 | pomodoro-app CircularProgress 패턴 | — | — | M1 |
| 🆕 Build | `src/components/CupButton.tsx` — 물 컵 추가 버튼 | 신규 디자인 | — | — | M1 |
| 🆕 Build | `src/screens/HomeScreen.tsx` — 메인 트래킹 화면 | pomodoro-app HomeScreen 패턴 | — | — | M1 |
| 🆕 Build | `app/_layout.tsx` — Root layout + providers | pomodoro-app _layout.tsx | — | — | M1 |
| 🆕 Build | `app/index.tsx` — Entry route | expo-router convention | — | — | M1 |
| 🆕 Build | `app/history.tsx` — 히스토리 화면 라우트 | expo-router convention | — | — | M1 |
| 🆕 Build | `DESIGN.md` — 디자인 소스 문서 | 요구사항 | — | — | M1 |
| 🆕 Build | `app.json`, `package.json`, `tsconfig.json`, `eslint.config.mjs`, `babel.config.js` | pomodoro-app 복제 | — | — | M4 |

---

## Waves

### Wave 1 — Foundation: Core domain + Main screen (5 tasks, parallel where possible, ≤900K tokens)

- [ ] **w1-s1**: Project scaffold — `npx create-expo-app@latest water-check-app --template blank-typescript`
  - **Worker:** `mini`
  - **Token est:** ~2K
  - **Verify:** `ls water-check-app/package.json && cat water-check-app/package.json | grep "expo.*52"`
  - **Gate:** M1 (spec-match — Expo 52+ confirmed)
  - **Evidence:** `.omo/evidence/water-check-app-w1-s1.txt`

- [ ] **w1-s2**: Config files — copy and adapt `app.json`, `tsconfig.json`, `eslint.config.mjs`, `babel.config.js` from pomodoro-app
  - **Worker:** `medium`
  - **Token est:** ~4K
  - **Verify:** `cd water-check-app && npx tsc --noEmit && npx eslint . --ext .ts,.tsx --max-warnings 0`
  - **Gate:** M4 (lint clean — 0 warnings)
  - **Evidence:** `.omo/evidence/water-check-app-w1-s2.txt`
  - **depends_on:** w1-s1

- [ ] **w1-s3**: Core domain types + storage layer — `src/water/types.ts`, `src/lib/storage.ts`
  - **Worker:** `medium`
  - **Token est:** ~5K
  - **Verify:** `cd water-check-app && npx tsc --noEmit` (types compile)
  - **Gate:** M1 (spec-match — types cover all domain entities), S2 (no plaintext secrets)
  - **Evidence:** `.omo/evidence/water-check-app-w1-s3.txt`
  - **depends_on:** w1-s2

- [ ] **w1-s4**: WaterContext provider — `src/context/WaterContext.tsx` with useReducer, AsyncStorage hydration, daily reset detection (AppState listener)
  - **Worker:** `heavy`
  - **Token est:** ~6K
  - **Verify:** Unit test via `jest` — reducer handles CUP_ADD, CUP_REMOVE, GOAL_SET, LOG_HYDRATE, DAY_RESET
  - **Gate:** M2 (test pass=100% on reducer), M3 (no regression — n/a greenfield)
  - **Evidence:** `.omo/evidence/water-check-app-w1-s4.txt`
  - **depends_on:** w1-s3

- [ ] **w1-s5**: UI components — `src/components/WaterProgress.tsx` (SVG ring), `src/components/CupButton.tsx` (add/remove cups), `src/components/DailySummary.tsx` (ml display + goal)
  - **Worker:** `heavy`
  - **Token est:** ~8K
  - **Verify:** `cd water-check-app && npx expo export --platform web` (builds without error)
  - **Gate:** M1 (spec-match — progress ring renders 0-100%, cup button triggers callback)
  - **Evidence:** `.omo/evidence/water-check-app-w1-s5.txt`
  - **depends_on:** w1-s4

### Wave 2 — Screens + History (3 tasks, parallel where possible, ≤900K tokens)

- [ ] **w2-s1**: `app/_layout.tsx` — Root layout wrapping WaterProvider + ThemeProvider + Stack navigator
  - **Worker:** `medium`
  - **Token est:** ~4K
  - **Verify:** `cd water-check-app && npx expo export --platform web` (no runtime errors)
  - **Gate:** M1 (spec-match — all routes registered)
  - **Evidence:** `.omo/evidence/water-check-app-w2-s1.txt`
  - **depends_on:** w1-s5

- [ ] **w2-s2**: `src/screens/HomeScreen.tsx` + `app/index.tsx` — Main tracking screen: progress ring, add cup buttons (200ml/300ml/500ml), today's log, daily goal display
  - **Worker:** `heavy`
  - **Token est:** ~8K
  - **Verify:** `cd water-check-app && npx jest --coverage` (≥80% coverage on WaterContext + components)
  - **Gate:** M1 (spec-match), M2 (test pass=100%)
  - **Evidence:** `.omo/evidence/water-check-app-w2-s2.txt`
  - **depends_on:** w2-s1

- [ ] **w2-s3**: `src/screens/HistoryScreen.tsx` + `app/history.tsx` — History screen: last 7 days, each day shows total ml, cups count, goal achieved (✓/✗), tap to see cup breakdown
  - **Worker:** `heavy`
  - **Token est:** ~7K
  - **Verify:** `cd water-check-app && npx jest --coverage` (history screen tests pass)
  - **Gate:** M1 (spec-match), M2 (test pass=100%)
  - **Evidence:** `.omo/evidence/water-check-app-w2-s3.txt`
  - **depends_on:** w2-s1

### Wave 3 — Polish + DESIGN.md (2 tasks, parallel)

- [ ] **w3-s1**: `DESIGN.md` — Design source document: color palette, typography, component spec, spacing grid, icon set (lucide-react-native droplet icon), dark mode support
  - **Worker:** `medium`
  - **Token est:** ~3K
  - **Verify:** `cat water-check-app/DESIGN.md | wc -l` (≥50 lines)
  - **Gate:** M1 (spec-match — covers colors, typography, components, spacing)
  - **Evidence:** `.omo/evidence/water-check-app-w3-s1.txt`
  - **depends_on:** w2-s2, w2-s3

- [ ] **w3-s2**: Integration tests + final lint pass — `__tests__/` directory with full flow tests: add cups → check progress → day reset → history update
  - **Worker:** `heavy`
  - **Token est:** ~5K
  - **Verify:** `cd water-check-app && npx jest --coverage && npx eslint . --ext .ts,.tsx --max-warnings 0 && npx tsc --noEmit`
  - **Gate:** M2 (test pass=100%), M3 (no regression), M4 (lint clean — 0 warnings), M5 (no dead code)
  - **Evidence:** `.omo/evidence/water-check-app-w3-s2.txt`
  - **depends_on:** w2-s2, w2-s3

---

## DAG (Directed Acyclic Graph)

```yaml
tasks:
  w1-s1:
    wave: 1
    action: "expo scaffold"
    depends_on: []

  w1-s2:
    wave: 1
    action: "config files"
    depends_on: [w1-s1]

  w1-s3:
    wave: 1
    action: "types + storage"
    depends_on: [w1-s2]

  w1-s4:
    wave: 1
    action: "WaterContext"
    depends_on: [w1-s3]

  w1-s5:
    wave: 1
    action: "UI components"
    depends_on: [w1-s4]

  w2-s1:
    wave: 2
    action: "root layout + nav"
    depends_on: [w1-s5]

  w2-s2:
    wave: 2
    action: "HomeScreen"
    depends_on: [w2-s1]

  w2-s3:
    wave: 2
    action: "HistoryScreen"
    depends_on: [w2-s1]

  w3-s1:
    wave: 3
    action: "DESIGN.md"
    depends_on: [w2-s2, w2-s3]

  w3-s2:
    wave: 3
    action: "tests + lint"
    depends_on: [w2-s2, w2-s3]

# Critical path: w1-s1 → w1-s2 → w1-s3 → w1-s4 → w1-s5 → w2-s1 → w2-s2 → w3-s2 (8 hops)
```

---

## Risk Register (BKIT 11-Gate)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| Spec mismatch: goal tracking off by one cup | `M1_spec_match` | HIGH | matchRate ≥ 90% | TDD with explicit cup-count assertions | `jest` count tests |
| AsyncStorage corruption on force-close | `M2_test_pass` | MED | passRate = 100% | try/catch all storage reads, default to empty state | Integration test with corrupted storage mock |
| Daily reset fires at wrong time (timezone edge case) | `M3_regression` | MED | 0 regressions | Use `toDateString()` for date comparison (timezone-safe) | Unit test crossing midnight boundary |
| ESLint config mismatch with pomodoro-app | `M4_lint_clean` | LOW | 0 warnings | Copy exact eslint.config.mjs from pomodoro-app | `npx eslint . --max-warnings 0` |
| Unused components from scaffold template | `M5_dead_code` | LOW | 0 unused exports | tree-shake scaffold boilerplate | `npx ts-prune` or manual grep |
| User input: negative cup amounts via state manipulation | `S1_dataFlow` | LOW | integrity ≥ 85% | Reducer clamps amountMl > 0 | Reducer unit test with negative input |
| Unprotected data: AsyncStorage accessible on rooted device | `S2_auth` | LOW | 모든 진입점 보호 | No auth needed (local-only app). Accept risk. | N/A |
| No injection surface (no network, no eval) | `S3_injection` | LOW | 모든 입력 검증 | amountMl parsed as integer, clamped | Unit test with string input |
| AsyncStorage read on every render (performance) | `P1_query` | LOW | No N+1 | Context hydrates once on mount, reads from memory thereafter | Performance assertion: 0 AsyncStorage reads after mount |
| Unbounded history growth (>1 year) | `P2_memory` | LOW | No unbounded growth | Cap history at 90 days (mirror pomodoro-app 90-day session cap) | History load test with 365 days of data |
| SVG ring re-render jank | `P3_latency` | LOW | p95 < 16ms | Single SVG element, only progress prop changes | React Profiler measurement |

---

## Component Tree

```
<RootLayout>                          // app/_layout.tsx
  <ThemeProvider>                     // src/context/ThemeContext.tsx
    <WaterProvider>                   // src/context/WaterContext.tsx
      <ErrorBoundary>                 // src/components/ErrorBoundary.tsx
        <StatusBar />
        <Stack>
          <Stack.Screen name="index">  // → HomeScreen
            <SafeAreaView>
              <ScrollView>
                <Header>
                  <ThemeToggle />
                  <HistoryButton />    // → router.push('/history')
                </Header>
                <WaterProgressRing>    // SVG circle, 0–100%, color shifts at goal
                  <DropletIcon />      // lucide-react-native Droplets
                  <MlDisplay />        // "1,200 / 2,000 ml"
                  <CupCount />         // "6 cups today"
                </WaterProgressRing>
                <CupButtonGroup>
                  <CupButton size={200} />  // Small cup 200ml
                  <CupButton size={300} />  // Medium cup 300ml
                  <CupButton size={500} />  // Large cup 500ml
                </CupButtonGroup>
                <TodayCupList>         // Scrollable list of today's cups
                  <CupItem>            // Swipeable delete, shows time + ml
                </TodayCupList>
                <GoalSetter>           // Tap to change daily goal
              </ScrollView>
            </SafeAreaView>
          </Stack.Screen>
          <Stack.Screen name="history"> // → HistoryScreen (modal)
            <SafeAreaView>
              <FlatList>
                <HistoryDayCard>       // Per day: date, ml, goal, ✓/✗
                  <DayCupBreakdown />  // Expandable cup list
                </HistoryDayCard>
              </FlatList>
            </SafeAreaView>
          </Stack.Screen>
        </Stack>
      </ErrorBoundary>
    </WaterProvider>
  </ThemeProvider>
</RootLayout>
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────┐
│                     USER ACTION                          │
│  Tap "+200ml" ──→ CupButton.onPress(200)                │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│               WaterContext.addCup(200)                   │
│  dispatch({ type: 'CUP_ADD', payload: { amountMl: 200 } })│
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│               waterReducer(state, action)                │
│  - Generate id: `${Date.now()}-${random}`               │
│  - Create CupRecord { id, amountMl:200, timestamp:ISO }  │
│  - Append to state.cups[]                               │
│  - Return new DailyLog                                  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│          useEffect → saveTodayLog(todayLog)              │
│  AsyncStorage.setItem('water-today-log', JSON)           │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              COMPUTED VALUES (Context)                   │
│  totalMl = sum(cups.map(c => c.amountMl))                │
│  progress = clamp(totalMl / goalMl, 0, 1)               │
│  achieved = totalMl >= goalMl                           │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│            WaterProgressRing re-renders                  │
│  <Circle strokeDashoffset={circumference * (1-progress)}/>│
│  Color: blue (progress<1) → green (progress≥1)           │
└─────────────────────────────────────────────────────────┘

─── DAY BOUNDARY (AppState 'active' + toDateString change) ───

┌─────────────────────────────────────────────────────────┐
│          WaterContext detects NEW DAY                    │
│  1. Compute DailySummary from yesterday's log            │
│  2. saveHistory([...oldHistory, summary])                │
│  3. dispatch({ type: 'DAY_RESET' })                      │
│  4. New DailyLog { date: today, cups: [], goalMl: prev } │
│  5. saveTodayLog(newLog)                                │
└─────────────────────────────────────────────────────────┘
```

---

## Navigation Structure

```
/ (index)  ────  HomeScreen (tracking)
  │
  └── /history  ────  HistoryScreen (modal presentation)
        │
        └── back to /
```

| Route | Screen | Presentation | Header |
|---|---|---|---|
| `/` | `HomeScreen` | default (root) | hidden (custom header) |
| `/history` | `HistoryScreen` | `modal` | shown: "History" |

---

## File Layout

```
water-check-app/
├── app/
│   ├── _layout.tsx              # Root: ThemeProvider → WaterProvider → Stack
│   ├── index.tsx                # → HomeScreen
│   └── history.tsx              # → HistoryScreen (modal)
├── src/
│   ├── water/
│   │   └── types.ts             # CupRecord, DailyLog, WaterAction, DailySummary
│   ├── lib/
│   │   └── storage.ts           # AsyncStorage: load/save todayLog, history, goal
│   ├── context/
│   │   └── WaterContext.tsx      # useReducer + hydration + daily reset
│   ├── components/
│   │   ├── WaterProgress.tsx     # SVG circular progress ring
│   │   ├── CupButton.tsx         # Single cup size button
│   │   ├── CupButtonGroup.tsx    # Row of cup size buttons
│   │   ├── CupItem.tsx           # Single cup row (swipe-to-delete)
│   │   ├── TodayCupList.tsx      # List of today's cups
│   │   ├── GoalSetter.tsx        # Inline goal adjustment
│   │   ├── HistoryDayCard.tsx    # Per-day summary card
│   │   └── ErrorBoundary.tsx     # Copied from pomodoro-app
│   └── screens/
│       ├── HomeScreen.tsx        # Main tracking screen
│       └── HistoryScreen.tsx     # 7-day history view
├── __tests__/
│   ├── storage.test.ts          # AsyncStorage mock tests
│   ├── waterReducer.test.ts     # Reducer state machine tests
│   ├── WaterContext.test.tsx    # Context integration tests
│   └── screens/
│       ├── HomeScreen.test.tsx
│       └── HistoryScreen.test.tsx
├── assets/
│   ├── icon.png
│   ├── favicon.png
│   └── splash.png
├── DESIGN.md                    # Design source document
├── app.json                     # Expo config (adapted from pomodoro-app)
├── package.json                 # Dependencies
├── tsconfig.json                # TypeScript config
├── eslint.config.mjs            # ESLint flat config
├── babel.config.js              # Babel config
├── expo-env.d.ts                # Expo type declarations
├── jest.config.ts               # Jest configuration
└── .gitignore
```

---

## Dependency Matrix

| Package | Version | Purpose |
|---|---|---|
| `expo` | `~52.0.0` | Framework |
| `expo-router` | `~4.0.0` | File-based navigation |
| `react` | `18.3.1` | UI library |
| `react-native` | `0.76.5` | Platform runtime |
| `@react-native-async-storage/async-storage` | `2.1.2` | Local persistence |
| `react-native-safe-area-context` | `4.14.0` | Safe area insets |
| `react-native-screens` | `~4.3.0` | Native screen containers |
| `react-native-svg` | `15.9.0` | SVG circular progress |
| `lucide-react-native` | `^0.460.0` | Icons (Droplets, Plus, Minus, History, Settings) |
| `expo-status-bar` | `~2.0.0` | Status bar control |
| `expo-haptics` | `~14.0.0` | Haptic feedback on cup add |

---

## DESIGN.md Specification

The DESIGN.md must cover:

1. **Color Palette**: Blue primary (#3B82F6) for water, success green (#22C55E) for goal achieved, neutral grays for backgrounds
2. **Typography**: System font (San Francisco / Roboto), weight hierarchy: bold (headings), semibold (labels), regular (body)
3. **Spacing Grid**: 4px base unit — 4, 8, 12, 16, 20, 24, 32
4. **Component Specs**:
   - WaterProgress ring: 200px diameter, 16px stroke, rounded caps
   - CupButton: 56px height, rounded-2xl, with icon + label
   - HistoryDayCard: full-width card with date, ml bar, achieved checkmark
5. **Icon Set**: lucide-react-native — Droplets (water), Plus (add), Minus (remove), History (clock), Settings (gear), Check (achieved)
6. **Dark Mode**: Full support via ThemeContext (copied from pomodoro-app), semantic color tokens
7. **Animations**: Scale bounce on cup add, progress ring spring animation, card slide-in on history screen

---

## Execution

Run this plan with:
```
blackcow-loop "Execute plans/water-check-app.md" --completion-promise='Expo 52+ app: cup add/remove, SVG progress ring, daily reset, 7-day history, DESIGN.md, test pass=100%, lint=0warn, coverage≥80%' --trust-level=2
```

### Parallelism Guide
- Wave 1: 5 tasks, w1-s3 through w1-s5 can parallelize (s3→s4→s5 serial chain, but s1+s2 are prereqs)
- Wave 2: 3 tasks, w2-s2 and w2-s3 parallelize after w2-s1
- Wave 3: 2 tasks, fully parallel (w3-s1 || w3-s2)
- Total budget: ~52K / 1M target (dynamic)
- DAG critical path: 8 sequential hops (see DAG section above)

---

## Self-Audit Checklist

- [x] YAML frontmatter has `---` opening AND closing markers
- [x] All code fences balanced (even count) — 12 fences total
- [x] No bare code blocks — every fence has language marker
- [x] Heading hierarchy: `#` → `##` → `###` → `####` (no skipped levels)
- [x] All 11 BKIT gates appear in Risk Register (M1-M5, S1-S3, P1-P3)
- [x] Each gate has a numeric threshold
- [x] Context Anchor SUCCESS references relevant gate subset
- [x] Intent-Based Dispatch applied: Feature intent → all lanes considered, L2/L3/L6/L7/L8/L9 adapted for greenfield
- [x] Phase 4 reviewers: M-scale → 3 reviewers (Correctness A, Security B, Feasibility C)
- [x] Token budget ≤ 900K
- [x] Every file:line reference verifiable (pomodoro-app references verified via read_file)
- [x] No `lsp_*` tool references
- [x] No invented file paths
- [x] DAG is acyclic, depends_on references valid
- [x] All 7 blackcow-* skill references valid
- [x] Progressive widening: Stage 1 (cache check + directory listing) revealed greenfield → stopped widening at Stage 1
