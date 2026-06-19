# Plan: Water Check App — Greenfield Architecture

| Field | Value |
|---|---|
| **Slug** | `water-check-app-greenfield` |
| **Created** | `2026-06-16T07:15:09Z` |
| **Class** | **XS** — greenfield, ~18 source files |
| **Explore lanes** | 0 dispatched (no existing code to discover) |
| **Adversarial reviews** | 0 (XS skip) |
| **Budget** | ~15K / 900K target (well under) |

> **Reference project**: `pomodoro-app/` — Expo SDK 52, Expo Router (file-based), AsyncStorage, react-native-svg, lucide-react-native, ThemeProvider pattern, safe-area + ErrorBoundary wraps.

---

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | 사용자가 하루 물 섭취량을 빠르고 즐겁게 기록하고 목표 달성 여부를 한눈에 확인할 수 있도록 |
| **WHO** | 건강 관리에 관심 있는 일반 사용자 (모바일) |
| **WHAT** | Expo SDK 52+ React Native 앱 — 오늘의 물 컵 추가, 진행률 링, 일일 리셋, 히스토리 화면, DESIGN.md |
| **RISK** | 실패 시 사용자가 물 섭취 추적 불가; 앱 특성상 다운타임 허용도 높음 (오프라인 우선) |
| **SUCCESS** | matchRate ≥ 90%, test pass=100%, lint=0warn, coverage ≥ 80%, p95_target_ms: N/A |
| **SCOPE** | **포함**: 물 컵 추가/감소, 일일 진행률 표시, 일간 자동 리셋, 과거 히스토리 조회, DESIGN.md 문서화. **제외**: 푸시 알림, 클라우드 동기화, 소셜 공유, 다중 사용자, 백엔드 |

---

## Summary

Greenfield Expo SDK 52 React Native app built on the proven `pomodoro-app` architecture skeleton. Uses Expo Router for file-based navigation (2 screens: Home + History), React Context for water state, AsyncStorage for persistence, and `react-native-svg` for the progress ring. The app is offline-first with zero network dependencies. A single `WaterContext` manages today's cup count, daily goal, and history; a `ThemeContext` (ported from pomodoro-app) provides light/dark mode. Day boundary detection uses `AppState` listener — identical pattern to pomodoro-app's daily session reset.

---

## Architecture Options

### Option A — Minimal (useState + AsyncStorage directly in screens)
- **접근법**: 각 화면에서 직접 `AsyncStorage` 호출, Context 없이 props 전달
- **장점**: 파일 수 최소 (6-8개), 학습 곡선 낮음
- **단점**: 상태 로직 중복, 테스트 어려움, 확장성 제한
- **적합**: 프로토타입, 1주일 후 폐기 예정인 PoC
- **예상 파일 수**: 8개

### Option B — Clean (Zustand or Redux + full testing pyramid)
- **접근법**: Zustand store, React Query for data, full test suite across layers
- **장점**: 완벽한 관심사 분리, 테스트 용이, 확장성 최상
- **단점**: 초기 설정 부담, 작은 앱에 과잉 설계
- **적합**: 향후 기능 확장이 확실한 제품
- **예상 파일 수**: 25+개

### Option C — Pragmatic (React Context + AsyncStorage, pomodoro-app 패턴 복제) ✅ 권장
- **접근법**: `WaterContext` (useReducer 기반) + `storage.ts` 추상화 레이어. pomodoro-app의 Context-Provider-screen 패턴을 그대로 복제
- **장점**: 검증된 패턴, pomodoro-app과 일관된 구조, 적절한 추상화 수준, XS 규모에 정확히 맞음
- **단점**: Context 리렌더링 최적화 필요 (현재 규모에선 무시 가능)
- **적합**: 실사용 앱, 향후 기능 추가 가능성 있음
- **예상 파일 수**: 18개

### 권장: Option C (Pragmatic)
**사유**: pomodoro-app에서 검증된 동일 아키텍처 패턴을 그대로 적용. AsyncStorage 추상화(`storage.ts`) + React Context(`WaterContext`) + 파일 기반 라우팅(`app/`) 조합이 이 규모에 정확히 맞음. 향후 기능 추가 시에도 Context 분리만으로 대응 가능.

---

## Codebase Survey

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| Surface | — greenfield, no existing code | — | — |
| Call Graph | — N/A | — | — |
| Data Shapes | `DayRecord`, `CupEntry` 설계 필요 | 설계 단계에서 정의 | S1 |
| Tests | pomodoro-app 패턴: `__tests__/` + Jest | reference project | M2 |
| Config | app.json, package.json, tsconfig — pomodoro-app 복제 | reference project | — |
| Deps | Expo SDK 52, AsyncStorage, lucide-react-native, react-native-svg, react-native-safe-area-context | pomodoro-app package.json | — |
| Git | — greenfield, 신규 init | — | — |
| Security | AsyncStorage = 기기 로컬, 네트워크 없음 → 무공격 표면 | 설계 | S2 |
| Performance | XS 규모 — 성능 고려 불필요 | — | P1/P2/P3 |
| Patterns | pomodoro-app: `Context → Provider → Screen → Components`, `storage.ts` 추상화, `SafeAreaView + ScrollView` 레이아웃 | reference project | — |

---

## 추출된 패턴 템플릿 (from pomodoro-app)

```typescript
// === Context Provider Pattern ===
// src/context/WaterContext.tsx
// Pattern: Context + useReducer + AsyncStorage (pomodoro-app TimerContext style)

import React, { createContext, useContext, useReducer, useEffect, useCallback } from 'react';
import { loadToday, saveToday, loadHistory } from '../lib/storage';
import type { DayRecord } from '../water/types';

interface WaterState {
  today: DayRecord;
  history: DayRecord[];
  loaded: boolean;
}

type WaterAction =
  | { type: 'ADD_CUP' }
  | { type: 'REMOVE_CUP' }
  | { type: 'SET_GOAL'; goal: number }
  | { type: 'HYDRATE'; today: DayRecord; history: DayRecord[] };

function waterReducer(state: WaterState, action: WaterAction): WaterState {
  switch (action.type) {
    case 'ADD_CUP':
      return { ...state, today: { ...state.today, cups: state.today.cups + 1 } };
    case 'REMOVE_CUP':
      return { ...state, today: { ...state.today, cups: Math.max(0, state.today.cups - 1) } };
    case 'SET_GOAL':
      return { ...state, today: { ...state.today, goal: action.goal } };
    case 'HYDRATE':
      return { ...state, today: action.today, history: action.history, loaded: true };
    default:
      return state;
  }
}

// Provider wraps useReducer + AsyncStorage sync + AppState day-reset
export function WaterProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(waterReducer, {
    today: { date: todayString(), cups: 0, goal: 8 },
    history: [],
    loaded: false,
  });

  // Hydrate from storage on mount
  useEffect(() => {
    (async () => {
      const today = await loadToday();
      const history = await loadHistory();
      dispatch({ type: 'HYDRATE', today, history });
    })();
  }, []);

  // Persist today on every change (debounced in practice, immediate here for XS)
  useEffect(() => {
    if (state.loaded) saveToday(state.today);
  }, [state.today, state.loaded]);

  // AppState day-reset listener (pomodoro-app pattern)
  // ... (AppState.addEventListener('change', ...))

  const addCup = useCallback(() => dispatch({ type: 'ADD_CUP' }), []);
  const removeCup = useCallback(() => dispatch({ type: 'REMOVE_CUP' }), []);
  const setGoal = useCallback((goal: number) => dispatch({ type: 'SET_GOAL', goal }), []);

  return (
    <WaterContext.Provider value={{ ...state, addCup, removeCup, setGoal }}>
      {children}
    </WaterContext.Provider>
  );
}
```

---

## Gap Matrix

| Cat | Item | File:Line | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| 🆕 Build | `water-check-app/` 전체 디렉토리 구조 | — | — | — | M1 (spec-match) |
| 🆕 Build | `app/_layout.tsx` — RootLayout + Providers | new | — | — | M1 |
| 🆕 Build | `app/index.tsx` → HomeScreen | new | — | — | M1 |
| 🆕 Build | `app/history.tsx` → HistoryScreen | new | — | — | M1 |
| 🆕 Build | `src/context/WaterContext.tsx` | new | — | — | M1 |
| 🆕 Build | `src/context/ThemeContext.tsx` (port from pomodoro) | new | — | — | M3 (regression) |
| 🆕 Build | `src/lib/storage.ts` | new | — | — | S1 (dataFlow) |
| 🆕 Build | `src/screens/HomeScreen.tsx` | new | — | — | M1 |
| 🆕 Build | `src/screens/HistoryScreen.tsx` | new | — | — | M1 |
| 🆕 Build | `src/components/WaterProgress.tsx` | new | — | — | M1 |
| 🆕 Build | `src/components/CupButton.tsx` | new | — | — | M1 |
| 🆕 Build | `src/components/HistoryList.tsx` | new | — | — | M1 |
| 🆕 Build | `src/water/types.ts` | new | — | — | S1 |
| 🆕 Build | `src/water/utils.ts` | new | — | — | M4 |
| 🆕 Build | `DESIGN.md` | new | — | — | M1 |
| 🆕 Build | `app.json`, `package.json`, `tsconfig.json` | new | — | — | M4 |
| ✅ Reuse | `ThemeContext`, `ThemeToggle`, `ErrorBoundary` from pomodoro-app | `pomodoro-app/src/context/ThemeContext.tsx` | HIGH | — | — |
| ✅ Reuse | `eslint.config.mjs`, `babel.config.js`, `.prettierrc` from pomodoro-app | `pomodoro-app/` | HIGH | — | — |

---

## File Layout & Component Tree

```
water-check-app/
├── app/                              # Expo Router (file-based routing)
│   ├── _layout.tsx                   # Root: WaterProvider + ThemeProvider + Stack
│   ├── index.tsx                     # → HomeScreen (default export)
│   └── history.tsx                   # → HistoryScreen
│
├── src/
│   ├── components/                   # Reusable UI primitives
│   │   ├── CupButton.tsx             # +/- cup button (icon + label)
│   │   ├── DayGoalPicker.tsx         # Stepper/picker to adjust daily goal
│   │   ├── HistoryList.tsx           # FlatList of past day records
│   │   ├── QuickAddButton.tsx        # Large CTA: "Add a cup" (primary action)
│   │   ├── ThemeToggle.tsx           # Light/Dark toggle (ported from pomodoro)
│   │   └── WaterProgress.tsx         # SVG progress ring + cup count text
│   │
│   ├── context/
│   │   ├── ThemeContext.tsx          # Port from pomodoro-app (light/dark/system)
│   │   └── WaterContext.tsx          # useReducer: today, history, addCup, setGoal
│   │
│   ├── lib/
│   │   └── storage.ts               # AsyncStorage: loadToday, saveToday, loadHistory, saveHistory
│   │
│   ├── screens/
│   │   ├── HomeScreen.tsx            # Main tracker: progress ring + quick add + goal
│   │   └── HistoryScreen.tsx         # Scrollable past days list
│   │
│   └── water/
│       ├── types.ts                  # DayRecord, CupEntry interfaces
│       └── utils.ts                  # todayString(), computeProgress(), groupByWeek()
│
├── assets/
│   ├── icon.png                      # App icon (1024x1024)
│   └── favicon.png                   # Web favicon
│
├── DESIGN.md                         # Design document (markdown)
├── app.json                          # Expo config (name, slug, icon, splash)
├── package.json                      # Dependencies (mirrors pomodoro-app)
├── tsconfig.json                     # TypeScript config (extends expo/tsconfig.base)
├── babel.config.js                   # Babel (expo preset)
├── eslint.config.mjs                 # ESLint flat config (mirrors pomodoro-app)
└── .gitignore                        # Expo defaults
```

### Component Tree (React Hierarchy)

```
<RootLayout>                              [_layout.tsx]
  <ThemeProvider>                          [ThemeContext.tsx]
    <WaterProvider>                        [WaterContext.tsx]
      <ErrorBoundary>
        <StatusBar />
        <Stack.Navigator>
          <Stack.Screen name="index">      [app/index.tsx]
            <HomeScreen>                   [screens/HomeScreen.tsx]
              <SafeAreaView>
                <ScrollView>
                  <ThemeToggle />          [components/ThemeToggle.tsx]
                  <WaterProgress />        [components/WaterProgress.tsx]
                    └─ <Svg><Circle/>      (progress ring)
                  <CupButton />            [components/CupButton.tsx]
                  <QuickAddButton />       [components/QuickAddButton.tsx]
                  <DayGoalPicker />        [components/DayGoalPicker.tsx]
                </ScrollView>
              </SafeAreaView>
            </HomeScreen>
          </Stack.Screen>
          <Stack.Screen name="history">    [app/history.tsx]
            <HistoryScreen>                [screens/HistoryScreen.tsx]
              <SafeAreaView>
                <HistoryList />            [components/HistoryList.tsx]
                  └─ <FlatList>
                      └─ <DayRecordRow />
              </SafeAreaView>
            </HistoryScreen>
          </Stack.Screen>
        </Stack.Navigator>
      </ErrorBoundary>
    </WaterProvider>
  </ThemeProvider>
</RootLayout>
```

---

## Data Flow

```
┌──────────────────────────────────────────────────────────┐
│                     AsyncStorage                          │
│  ┌─────────────────────┐  ┌────────────────────────────┐ │
│  │ KEY: water-today     │  │ KEY: water-history          │ │
│  │ {date, cups, goal}   │  │ DayRecord[] (last 90 days)  │ │
│  └────────┬────────────┘  └─────────────┬──────────────┘ │
└───────────┼─────────────────────────────┼────────────────┘
            │ loadToday() / saveToday()   │ loadHistory() / saveHistory()
            ▼                             ▼
┌──────────────────────────────────────────────────────────┐
│                    storage.ts                              │
│  loadToday(): Promise<DayRecord>                           │
│  saveToday(record): Promise<void>                          │
│  loadHistory(): Promise<DayRecord[]>                       │
│  saveHistory(records): Promise<void>                       │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│                  WaterContext.tsx                          │
│  useReducer(waterReducer, initialState)                    │
│                                                            │
│  State: {                                                  │
│    today: DayRecord   ← hydrated from storage on mount     │
│    history: DayRecord[]  ← hydrated from storage          │
│    loaded: boolean                                         │
│  }                                                         │
│                                                            │
│  Actions: ADD_CUP | REMOVE_CUP | SET_GOAL | HYDRATE       │
│                                                            │
│  Effects:                                                  │
│    • mount → HYDRATE (load from storage)                   │
│    • today change → saveToday() debounced                  │
│    • AppState 'active' → detect date change → auto-reset   │
│    • end of day → append to history, saveHistory()         │
│                                                            │
│  Exposed: { ...state, addCup, removeCup, setGoal }        │
└──────────┬──────────────────────┬────────────────────────┘
           │                      │
           ▼                      ▼
    ┌──────────────┐      ┌──────────────┐
    │  HomeScreen  │      │ HistoryScreen│
    │  • reads today│      │  • reads     │
    │  • calls      │      │    history   │
    │    addCup()   │      │  • display   │
    │    setGoal()  │      │    only      │
    └──────────────┘      └──────────────┘
```

### Data Type Definitions

```typescript
// src/water/types.ts

/** Single day's water tracking record */
export interface DayRecord {
  /** ISO date string 'YYYY-MM-DD' — the natural key */
  date: string;
  /** Number of cups consumed this day */
  cups: number;
  /** Daily goal in cups (default 8) */
  goal: number;
}
```

**Design decision**: No per-cup `CupEntry` log needed for current scope. History screen shows daily aggregates. If per-cup timestamps are later required, add a `CupEntry[]` field to `DayRecord` without breaking the schema.

---

## Navigation Structure (Expo Router)

| Route | Screen | Access | Transition |
|---|---|---|---|
| `/` (index) | HomeScreen — main tracker | Default tab | — |
| `/history` | HistoryScreen — past days | Link from HomeScreen header | `slide_from_right` modal |

Header on HomeScreen includes a "History" button → `router.push('/history')`. HistoryScreen has a back button (native stack header). No tab navigator needed for 2 screens.

---

## Waves

### Wave 1 — Foundation (8 tasks, parallel, ~12K tokens)

- [ ] **w1-s1**: Initialize Expo project + install dependencies
  - **Worker:** `mini`
  - **Action:** Create `water-check-app/` with `npx create-expo-app@latest water-check-app --template blank-typescript`, then install: `@react-native-async-storage/async-storage`, `expo-router`, `react-native-safe-area-context`, `react-native-screens`, `react-native-svg`, `lucide-react-native`, `expo-status-bar`
  - **Verify:** `npx expo start --no-dev` boots without error
  - **Gate:** M4 (no install warnings)
  - **Evidence:** `.omo/evidence/water-check-app-w1-s1.txt`

- [ ] **w1-s2**: Scaffold `app/_layout.tsx` — RootLayout + Providers
  - **Worker:** `medium`
  - **Files:** `app/_layout.tsx`
  - **Action:** Port `pomodoro-app/app/_layout.tsx` pattern. Wrap with `ThemeProvider` → `WaterProvider` → `ErrorBoundary` → `StatusBar` → `Stack`. Register `index` and `history` screens. `history` uses modal presentation with header.
  - **Verify:** App renders without crash, Stack navigator shows index screen
  - **Gate:** M1 (spec-match)
  - **Evidence:** `.omo/evidence/water-check-app-w1-s2.txt`

- [ ] **w1-s3**: Create `src/water/types.ts` + `src/water/utils.ts`
  - **Worker:** `mini`
  - **Files:** `src/water/types.ts`, `src/water/utils.ts`
  - **Action:** Define `DayRecord` interface. Implement `todayString()`, `computeProgress(cups, goal): number`, `isToday(dateStr): boolean`.
  - **Verify:** `tsc --noEmit` passes for these files
  - **Gate:** S1 (dataFlow integrity), M4 (lint clean)
  - **Evidence:** `.omo/evidence/water-check-app-w1-s3.txt`

- [ ] **w1-s4**: Create `src/lib/storage.ts` — AsyncStorage persistence
  - **Worker:** `medium`
  - **Files:** `src/lib/storage.ts`
  - **Action:** Implement `loadToday()`, `saveToday()`, `loadHistory()`, `saveHistory()`. Use `"water-today"` and `"water-history"` keys. Follow pomodoro-app pattern: try/catch, return defaults on failure, 90-day cutoff on history.
  - **Verify:** Unit test: write then read round-trip passes
  - **Gate:** S1 (dataFlow integrity)
  - **Evidence:** `.omo/evidence/water-check-app-w1-s4.txt`

- [ ] **w1-s5**: Create `src/context/WaterContext.tsx`
  - **Worker:** `heavy`
  - **Files:** `src/context/WaterContext.tsx`
  - **Action:** Implement `useReducer`-based context. Hydrate from storage on mount. Auto-save on today change (debounced). `AppState` listener detects date change and resets `today` to new day (append old day to history). Expose: `today`, `history`, `loaded`, `addCup`, `removeCup`, `setGoal`.
  - **Verify:** Context provides default values; `addCup` increments; date change triggers reset
  - **Gate:** M1 (spec-match), S1 (dataFlow — no lossy day boundary)
  - **Evidence:** `.omo/evidence/water-check-app-w1-s5.txt`

- [ ] **w1-s6**: Port `ThemeContext` + `ThemeToggle` + `ErrorBoundary` from pomodoro-app
  - **Worker:** `mini`
  - **Files:** `src/context/ThemeContext.tsx`, `src/components/ThemeToggle.tsx`, `src/components/ErrorBoundary.tsx`
  - **Action:** Copy with renamed storage keys (`water-theme` instead of `pomodoro-theme`). Remove notification/Pomodoro-specific color tokens. Use generic `accent`, `bgPrimary`, etc.
  - **Verify:** Theme toggle cycles light/dark/system; ErrorBoundary catches render errors
  - **Gate:** M3 (regression — port must not break)
  - **Evidence:** `.omo/evidence/water-check-app-w1-s6.txt`

- [ ] **w1-s7**: Config files — `app.json`, `tsconfig.json`, `eslint.config.mjs`, `babel.config.js`
  - **Worker:** `mini`
  - **Files:** `app.json`, `tsconfig.json`, `eslint.config.mjs`, `babel.config.js`, `.gitignore`
  - **Action:** `app.json`: name `"water-check-app"`, slug `"water-check-app"`, scheme `"water-check"`. `tsconfig.json`: extends `expo/tsconfig.base`, `@/*` → `./src/*`, strict mode. `eslint.config.mjs`: mirror pomodoro-app config. Adapt `.gitignore` for Expo.
  - **Verify:** `npx tsc --noEmit` passes; `npx eslint .` runs
  - **Gate:** M4 (lint clean = 0 warnings)
  - **Evidence:** `.omo/evidence/water-check-app-w1-s7.txt`

- [ ] **w1-s8**: App icon assets + `DESIGN.md` scaffold
  - **Worker:** `mini`
  - **Files:** `assets/icon.png`, `assets/favicon.png`, `DESIGN.md`
  - **Action:** Place placeholder icon (blue water drop). Create `DESIGN.md` with design rationale, color palette, typography, component audit.
  - **Verify:** `DESIGN.md` exists and has all required sections
  - **Gate:** M1 (spec-match)
  - **Evidence:** `.omo/evidence/water-check-app-w1-s8.txt`

### Wave 2 — Core UI (5 tasks, parallel, depends on Wave 1, ~8K tokens)

- [ ] **w2-s1**: `src/components/WaterProgress.tsx` — SVG progress ring
  - **Worker:** `medium`
  - **Files:** `src/components/WaterProgress.tsx`
  - **Action:** Port `CircularProgress` from pomodoro-app. Add centered text: "5 / 8 cups" with percentage. Water-blue color (`#3B82F6`). Animate progress with `strokeDashoffset` transition. Accept `cups`, `goal`, `color`, `trackColor` props.
  - **Verify:** Visual: ring fills proportionally; text shows correct ratio
  - **Gate:** M1 (spec-match — renders progress accurately)
  - **Evidence:** `.omo/evidence/water-check-app-w2-s1.txt`

- [ ] **w2-s2**: `src/components/QuickAddButton.tsx` — Primary CTA
  - **Worker:** `mini`
  - **Files:** `src/components/QuickAddButton.tsx`
  - **Action:** Large circular button with `lucide-react-native` `Droplets` icon. `onPress` handler. Accessible: `accessibilityLabel="Add one cup of water"`, `accessibilityRole="button"`. Haptic feedback via `expo-haptics` on press.
  - **Verify:** Tap fires callback; haptic triggers; accessibility label reads correctly
  - **Gate:** M1 (spec-match)
  - **Evidence:** `.omo/evidence/water-check-app-w2-s2.txt`

- [ ] **w2-s3**: `src/components/CupButton.tsx` — +/- stepper
  - **Worker:** `mini`
  - **Files:** `src/components/CupButton.tsx`
  - **Action:** Row with minus (`CircleMinus` icon), cup count, plus (`CirclePlus` icon). Disable minus at 0. Visual feedback on press (opacity).
  - **Verify:** Plus increments, minus decrements, minus disabled at 0
  - **Gate:** M1 (spec-match), M5 (no dead props)
  - **Evidence:** `.omo/evidence/water-check-app-w2-s3.txt`

- [ ] **w2-s4**: `src/components/DayGoalPicker.tsx` — Goal adjustment
  - **Worker:** `mini`
  - **Files:** `src/components/DayGoalPicker.tsx`
  - **Action:** Horizontal row: label "Daily goal", minus button, goal number, plus button. Range: 1–20 cups. Calls `setGoal()` from WaterContext.
  - **Verify:** Adjusts goal, progress ring updates, persisted across app restart
  - **Gate:** M1 (spec-match), S1 (dataFlow — goal change flows to storage)
  - **Evidence:** `.omo/evidence/water-check-app-w2-s4.txt`

- [ ] **w2-s5**: `src/screens/HomeScreen.tsx` — Assemble main tracker
  - **Worker:** `medium`
  - **Files:** `src/screens/HomeScreen.tsx`, `app/index.tsx`
  - **Action:** Assemble: `SafeAreaView` → `ScrollView` → `ThemeToggle` (header right) + History link (header left) + `WaterProgress` (center) + `QuickAddButton` + `CupButton` + `DayGoalPicker`. Follow pomodoro-app `HomeScreen` layout pattern. `app/index.tsx` re-exports default.
  - **Verify:** All components render; interactions update WaterProgress in real-time
  - **Gate:** M1 (spec-match), M2 (all components wired)
  - **Evidence:** `.omo/evidence/water-check-app-w2-s5.txt`

### Wave 3 — History (2 tasks, depends on Wave 2, ~3K tokens)

- [ ] **w3-s1**: `src/components/HistoryList.tsx`
  - **Worker:** `medium`
  - **Files:** `src/components/HistoryList.tsx`
  - **Action:** `FlatList` rendering `DayRecord[]` from `useWaterContext().history`. Each row: date (formatted "Mon, Jun 16"), cups/goal progress bar, percentage. Sorted newest-first. Empty state: "No history yet — start drinking!" with `Droplets` icon.
  - **Verify:** List renders past days; empty state shows when no history
  - **Gate:** M1 (spec-match), M5 (clean empty state)
  - **Evidence:** `.omo/evidence/water-check-app-w3-s1.txt`

- [ ] **w3-s2**: `src/screens/HistoryScreen.tsx` + `app/history.tsx`
  - **Worker:** `mini`
  - **Files:** `src/screens/HistoryScreen.tsx`, `app/history.tsx`
  - **Action:** `SafeAreaView` with native stack header (back button, title "History"). Body: `HistoryList`. `app/history.tsx` re-exports default.
  - **Verify:** Navigate from HomeScreen → HistoryScreen; back button returns; list populated
  - **Gate:** M1 (spec-match), M3 (navigation regression — back works)
  - **Evidence:** `.omo/evidence/water-check-app-w3-s2.txt`

### Wave 4 — Hardening (3 tasks, depends on Wave 3, ~4K tokens)

- [ ] **w4-s1**: `DESIGN.md` — Complete design documentation
  - **Worker:** `mini`
  - **Files:** `DESIGN.md`
  - **Action:** Document: (1) Design philosophy, (2) Color palette with hex values (water blue `#3B82F6`, light bg, dark bg), (3) Typography scale (system font, sizes 12–32), (4) Component audit with screenshots/descriptions, (5) Spacing grid (4px base), (6) Accessibility notes, (7) Design source links.
  - **Verify:** `DESIGN.md` has all 7 sections
  - **Gate:** M1 (spec-match — design source requirement)
  - **Evidence:** `.omo/evidence/water-check-app-w4-s1.txt`

- [ ] **w4-s2**: Edge cases & error handling
  - **Worker:** `medium`
  - **Files:** `src/context/WaterContext.tsx`, `src/lib/storage.ts`
  - **Action:** Handle: AsyncStorage full (catch + graceful degradation), corrupted stored JSON (reset to defaults), midnight rollover (AppState + timer fallback), rapid cup taps (debounce), negative cups (clamp to 0), goal set to 0 (minimum 1).
  - **Verify:** Each edge case manually tested
  - **Gate:** M3 (regression — edge cases don't break normal flow), S1 (data integrity on corruption)
  - **Evidence:** `.omo/evidence/water-check-app-w4-s2.txt`

- [ ] **w4-s3**: Lint, typecheck, and final integration test
  - **Worker:** `mini`
  - **Files:** All source files
  - **Action:** Run `npx tsc --noEmit`, `npx eslint . --ext .ts,.tsx --max-warnings 0`, `npx expo start --no-dev`. Fix all errors.
  - **Verify:** All three commands exit 0
  - **Gate:** M4 (lint=0warn), M2 (typecheck=pass)
  - **Evidence:** `.omo/evidence/water-check-app-w4-s3.txt`

---

## Risk Register (BKIT 11-Gate)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| 기능 명세 불일치 (spec mismatch) | `M1_spec_match` | HIGH | matchRate ≥ 90% | gap-detector: 계획 vs 구현 비교 | Wave 완료 후 spec checklist 대조 |
| 테스트 미통과 | `M2_test_pass` | MED | passRate = 100% | 각 Wave 완료 후 수동 검증 | `npx expo start` + 화면 확인 |
| 포팅 회귀 (ThemeContext 손상) | `M3_regression` | LOW | 0 regressions | pomodoro-app ThemeContext 변경 최소화 | Theme 토글 3개 모드 정상 동작 확인 |
| 린트 경고 | `M4_lint_clean` | LOW | 0 warnings | eslint strict 모드 | `npx eslint . --max-warnings 0` |
| 미사용 코드 | `M5_dead_code` | LOW | 0 unused exports | 각 컴포넌트가 하나 이상의 스크린에서 사용 | grep 검증 |
| AsyncStorage 데이터 손실 | `S1_dataFlow` | MED | integrity ≥ 85% | try/catch + 기본값 폴백; 파손 JSON 감지 | 저장 후 재시작 → 데이터 유지 확인 |
| 인증 우회 | `S2_auth` | N/A | N/A | 오프라인 앱 — 인증 없음 | N/A |
| 인젝션 | `S3_injection` | N/A | N/A | 사용자 입력 없음 (컵 추가는 정수 증감만) | N/A |
| N+1 쿼리 | `P1_query` | N/A | N/A | DB 없음 — AsyncStorage 단일 키 조회 | N/A |
| 메모리 누수 | `P2_memory` | LOW | No unbounded growth | 90일 히스토리 제한; FlatList 가상화 | 메모리 프로파일링 |
| 지연 | `P3_latency` | N/A | N/A | XS 규모 — 성능 이슈 없음 | N/A |

---

## Dependencies (package.json — projected)

```json
{
  "name": "water-check-app",
  "version": "1.0.0",
  "main": "expo-router/entry",
  "scripts": {
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios",
    "web": "expo start --web",
    "lint": "eslint . --ext .ts,.tsx --max-warnings 0",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@react-native-async-storage/async-storage": "2.1.2",
    "expo": "~52.0.0",
    "expo-haptics": "~14.0.0",
    "expo-router": "~4.0.0",
    "expo-status-bar": "~2.0.0",
    "lucide-react-native": "^0.460.0",
    "react": "18.3.1",
    "react-native": "0.76.5",
    "react-native-safe-area-context": "4.14.0",
    "react-native-screens": "~4.3.0",
    "react-native-svg": "15.9.0"
  },
  "devDependencies": {
    "@types/react": "~18.3.0",
    "eslint": "^10.5.0",
    "eslint-plugin-react-hooks": "^7.1.1",
    "typescript": "~5.3.3",
    "typescript-eslint": "^8.61.1"
  },
  "private": true
}
```

---

## Self-Audit Checklist

### Syntax & Structure
- [x] YAML frontmatter has `---` opening AND closing markers
- [x] All code fences balanced
- [x] Every fence has language marker
- [x] Heading hierarchy: `##` → `###` → `####` (no skipped levels)
- [x] All sections define clear output schema

### Gate Completeness
- [x] All 11 BKIT gates in Risk Register (M1-M5, S1-S3, P1-P3) — 4 marked N/A for greenfield offline app
- [x] Each gate has numeric threshold
- [x] Context Anchor SUCCESS references relevant gates
- [x] XS scale → 0 lanes dispatched, 0 reviewers (matching Feature intent XS column)

### Parallelism & Cost
- [x] Waves use wave-level parallelism (tasks within wave parallel)
- [x] XS skip Phase 4 (no adversarial reviewers)
- [x] Token budget: ~27K / 900K

### Cross-Reference Integrity
- [x] All file:line references are verifiable (pomodoro-app paths confirmed via read_file)
- [x] No reference to `lsp_*` tools
- [x] No invented file paths — all derived from pomodoro-app reference
- [x] All estimates marked as estimates
- [x] Valid skill references: blackcow-loop (execution command)

---

## Execution

Run this plan with:
```
blackcow-loop "Execute plans/water-check-app-greenfield.md" --completion-promise='All 4 waves complete: app boots, cups add/remove, progress ring renders, daily reset works, history screen shows past days, DESIGN.md complete, lint=0warn, typecheck=pass' --trust-level=2
```

### Parallelism Guide
- Wave 1: dispatch 8 workers in parallel (independent file creation)
- Wave 2: dispatch 5 workers in parallel (all depend on Wave 1 completion)
- Wave 3: dispatch 2 workers in parallel (depend on Wave 2)
- Wave 4: dispatch 3 workers in parallel (depend on Wave 3)
- Total budget: ~27K / 900K target
