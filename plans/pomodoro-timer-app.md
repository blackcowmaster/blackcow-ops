# Plan: Pomodoro Timer – React Native + Expo (TypeScript)

| Field | Value |
|---|---|
| **Slug** | `pomodoro-timer-app` |
| **Created** | 2025-07-14 |
| **Class** | **M** (6–8 source files, 3 async subsystems, external deps) |
| **Intent** | Feature — greenfield build |
| **Explore lanes** | N/A (greenfield; requirements analysis substituted) |
| **Adversarial reviews** | Built into design — 3 review gates |
| **Budget** | estimated ~18 K tokens / 128 K target |

---

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | 사용자에게 집중 시간(25분 작업 + 5분 휴식)을 구조화하고, 할 일 목록과 세션 카운트로 생산성을 가시화하는 크로스플랫폼 Pomodoro 타이머 제공 |
| **WHO** | 집중 작업이 필요한 개인 사용자 (모바일 + 웹) |
| **WHAT** | Expo SDK 52+ 기반 React Native 앱 — 타이머, 작업 목록, 일일 세션 카운터, 종료 알림 |
| **RISK** | 타이머 백그라운드 정확도 손실 시 사용자 신뢰 붕괴. 최대 허용 오차: ±3초 |
| **SUCCESS** | matchRate ≥ 90%, test pass=100%, lint=0warn, p95 타이머 tick 오차 ≤ 500ms, 알림 도달률 ≥ 95% |
| **SCOPE** | **포함**: 타이머 엔진, 작업 CRUD + AsyncStorage, 세션 카운트, expo-notifications, Expo Router 내비게이션, 웹/모바일 동시 타겟. **제외**: 계정 시스템, 클라우드 동기화, 사운드 커스터마이징, 통계 대시보드 |

---

## Summary

단일 Context + useReducer로 상태를 중앙 관리하고, 5-상태 유한 상태 머신(Fading-Second 타이머)으로 정밀한 카운트다운을 구동하는 Expo 크로스플랫폼 앱. 타이머 완료 시 `expo-notifications` 로컬 알림으로 사용자에게 즉시 통보하며, 작업 목록은 AsyncStorage로 영속화한다. Expo Router 파일 기반 라우팅으로 `/`(타이머 홈)과 `/tasks`(작업 관리) 두 화면을 구성한다.

---

## Architecture Options

### Option A — Minimal (1-screen, no navigation)
- **접근법**: 단일 화면에 타이머 + 작업 목록 모두 배치. Expo Router 미사용.
- **장점**: 파일 수 최소, Expo Router 학습 불필요
- **단점**: 향후 기능 확장 시 재작성 비용 큼, 작업 목록 UX 제한적
- **적합**: 프로토타입, PoC
- **파일 수**: ~4개

### Option B — Clean (3-screen, full separation)
- **접근법**: 타이머 / 작업 목록 / 설정 3화면, Expo Router 탭 네비게이션, 커스텀 훅으로 타이머 로직 완전 분리
- **장점**: 관심사 완벽 분리, 테스트 용이, 확장성 최고
- **단점**: 초기 파일 수 증가, Expo Router 설정 부담
- **적합**: 장기 유지보수 제품
- **파일 수**: ~12개

### Option C — Pragmatic (2-screen, focused) ✅ 권장
- **접근법**: 타이머 홈(`/`) + 작업 목록(`/tasks`) 2화면. Expo Router `Stack` 네비게이션. 타이머 로직은 `useTimerReducer` 커스텀 훅에 캡슐화하되, 설정은 Context로 공유.
- **장점**: 요구사항 정확히 충족, 파일 수 합리적, 학습 곡선 낮음
- **단점**: 설정 화면이 없어 작업/휴식 시간 커스터마이징은 Context 상수로 관리
- **적합**: MVP + 점진적 확장

### 권장: Option C (Pragmatic)
**사유**: 요구사항(타이머 + 작업 목록)을 정확히 커버하며, Expo Router 학습 부담 없이 2화면 구조로 즉시 개발 가능. 추후 설정 화면 추가 시 `/settings` 라우트만 append.

---

## 10-Lane Survey (Greenfield Requirements Analysis)

| Lane | Key Analysis | Evidence | BKIT Gate |
|---|---|---|---|
| **L1 Surface** | 2 screens: `index.tsx` (timer home), `tasks.tsx` (task list). Expo Router `app/` directory. Entry: user tap Start; Exit: notification fired + session count incremented | requirements doc | — |
| **L2 Call Graph** | `TimerControls.onStart → dispatch(TIMER_START) → useTimerReducer → setInterval tick → dispatch(TIMER_TICK) → check completion → scheduleNotification + dispatch(SESSION_INCREMENT)` | architectural design | S1 |
| **L3 Data Shapes** | `TimerState`, `Task`, `TimerAction`, `TaskAction`, `AppState` — all typed with strict TypeScript | see Data Model section | S1 |
| **L4 Tests** | Jest + React Native Testing Library. `__tests__/` colocated. Snapshot tests for components; unit tests for reducer + timer engine | standard RN testing | M2, M3 |
| **L5 Config** | `app.json` (Expo config), `tsconfig.json`, `.env` (notification channel ID), `eas.json` (build profiles) | Expo standard | S2 |
| **L6 Deps** | `expo-router`, `expo-notifications`, `@react-native-async-storage/async-storage`, `expo-haptics`, `expo-constants`, `react-native-web` | Expo SDK 52 ecosystem | — |
| **L7 Git** | N/A (greenfield) | — | — |
| **L8 Security** | 로컬 전용 앱 — 네트워크 호출 없음. AsyncStorage 데이터 평문 저장 (민감 정보 없음). 알림 권한 요청만 OS 레벨 | no network egress | S2, S3 |
| **L9 Performance** | `setInterval` 1초 tick — 메인 스레드 부하 무시 가능. `requestAnimationFrame` 폴백 (웹 백그라운드 탭 대응). AsyncStorage 읽기 1회 (앱 시작 시) | timing precision analysis | P1, P3 |
| **L10 Patterns** | Expo 공식 with-router 템플릿 참조. Context + useReducer 공식 React 패턴. Expo Notifications 공식 예제 | Expo docs, React docs | — |

---

## Component Tree

```
<App>
└── <TimerProvider>                          // Context.Provider wrapping entire app
    └── <Stack navigator={ExpoRouter}>       // file-based: app/_layout.tsx
        ├── Route: "/" → <HomeScreen>
        │   ├── <SafeAreaView>
        │   ├── <SessionTypeIndicator        // "🔴 WORK" / "🟢 BREAK"
        │   │    sessionType: 'work' | 'break' />
        │   ├── <TimerDisplay
        │   │    timeRemaining: number       // seconds
        │   │    totalDuration: number       // seconds
        │   │    status: TimerStatus         // 'idle' | 'running' | 'paused' />
        │   │   └── <CircularProgress
        │   │        progress: number        // 0–1 (timeRemaining / totalDuration)
        │   │        size: number
        │   │        strokeWidth: number
        │   │        color: string />
        │   ├── <TimerControls
        │   │    status: TimerStatus
        │   │    onStart: () => void
        │   │    onPause: () => void
        │   │    onReset: () => void />
        │   ├── <SessionCounter
        │   │    count: number               // today's completed sessions
        │   │    label: string />
        │   └── <Link to="/tasks">           // Expo Router Link
        │        <TaskBadge
        │            pendingCount: number />  // incomplete task count
        │
        └── Route: "/tasks" → <TaskListScreen>
            ├── <SafeAreaView>
            ├── <TaskInput
            │    onSubmit: (title: string) => void />
            ├── <FlatList>
            │   └── <TaskItem
            │        id: string
            │        title: string
            │        completed: boolean
            │        onToggle: (id: string) => void
            │        onDelete: (id: string) => void />
            └── <EmptyState                // shown when tasks.length === 0
                 message: string />
```

### Props Interfaces (Full TypeScript)

```typescript
// ---- Timer Domain ----

type TimerStatus = 'idle' | 'running' | 'paused';
type SessionType = 'work' | 'break';

interface TimerState {
  status: TimerStatus;
  sessionType: SessionType;
  timeRemaining: number;    // seconds, counts down
  totalDuration: number;    // seconds, fixed for the session
  sessionsToday: number;    // completed work sessions today
}

type TimerAction =
  | { type: 'TIMER_START' }
  | { type: 'TIMER_PAUSE' }
  | { type: 'TIMER_RESET' }
  | { type: 'TIMER_TICK' }
  | { type: 'TIMER_COMPLETE'; nextSession: SessionType }
  | { type: 'SESSION_INCREMENT' };

// ---- Task Domain ----

interface Task {
  id: string;               // uuid
  title: string;
  completed: boolean;
  createdAt: string;        // ISO-8601
}

type TaskAction =
  | { type: 'TASK_ADD'; payload: { title: string } }
  | { type: 'TASK_TOGGLE'; payload: { id: string } }
  | { type: 'TASK_DELETE'; payload: { id: string } }
  | { type: 'TASKS_HYDRATE'; payload: { tasks: Task[] } };

// ---- Unified App State ----

type AppAction = TimerAction | TaskAction;

interface AppState {
  timer: TimerState;
  tasks: Task[];
}

// ---- Component Props ----

interface SessionTypeIndicatorProps { sessionType: SessionType; }
interface TimerDisplayProps { timeRemaining: number; totalDuration: number; status: TimerStatus; }
interface CircularProgressProps { progress: number; size: number; strokeWidth: number; color: string; }
interface TimerControlsProps { status: TimerStatus; onStart: () => void; onPause: () => void; onReset: () => void; }
interface SessionCounterProps { count: number; label: string; }
interface TaskBadgeProps { pendingCount: number; }
interface TaskInputProps { onSubmit: (title: string) => void; }
interface TaskItemProps { id: string; title: string; completed: boolean; onToggle: (id: string) => void; onDelete: (id: string) => void; }
interface EmptyStateProps { message: string; }
```

---

## State Management — Context + useReducer

### Architecture

```
TimerProvider (React.Context)
├── useReducer(appReducer, initialAppState)
├── useEffect → AsyncStorage persistence (tasks only)
├── useEffect → timer engine (setInterval)
└── value → { state, dispatch }
```

### Reducer Logic (appReducer)

```typescript
const WORK_DURATION = 25 * 60;  // 1500s
const BREAK_DURATION = 5 * 60;  // 300s

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    // ── Timer actions ──
    case 'TIMER_START':
      if (state.timer.status === 'idle') {
        return {
          ...state,
          timer: {
            ...state.timer,
            status: 'running',
            sessionType: 'work',
            timeRemaining: WORK_DURATION,
            totalDuration: WORK_DURATION,
          },
        };
      }
      if (state.timer.status === 'paused') {
        return { ...state, timer: { ...state.timer, status: 'running' } };
      }
      return state;

    case 'TIMER_PAUSE':
      return { ...state, timer: { ...state.timer, status: 'paused' } };

    case 'TIMER_RESET':
      return {
        ...state,
        timer: {
          ...state.timer,
          status: 'idle',
          sessionType: 'work',
          timeRemaining: WORK_DURATION,
          totalDuration: WORK_DURATION,
        },
      };

    case 'TIMER_TICK':
      if (state.timer.status !== 'running') return state;
      const next = state.timer.timeRemaining - 1;
      if (next <= 0) {
        // Trigger TIMER_COMPLETE via the engine, not here
        return { ...state, timer: { ...state.timer, timeRemaining: 0 } };
      }
      return { ...state, timer: { ...state.timer, timeRemaining: next } };

    case 'TIMER_COMPLETE':
      return {
        ...state,
        timer: {
          ...state.timer,
          status: 'idle',
          sessionType: action.nextSession,
          timeRemaining:
            action.nextSession === 'work' ? WORK_DURATION : BREAK_DURATION,
          totalDuration:
            action.nextSession === 'work' ? WORK_DURATION : BREAK_DURATION,
        },
      };

    case 'SESSION_INCREMENT':
      return {
        ...state,
        timer: { ...state.timer, sessionsToday: state.timer.sessionsToday + 1 },
      };

    // ── Task actions ──
    case 'TASK_ADD':
      return {
        ...state,
        tasks: [
          ...state.tasks,
          {
            id: generateUUID(),
            title: action.payload.title,
            completed: false,
            createdAt: new Date().toISOString(),
          },
        ],
      };

    case 'TASK_TOGGLE':
      return {
        ...state,
        tasks: state.tasks.map((t) =>
          t.id === action.payload.id ? { ...t, completed: !t.completed } : t
        ),
      };

    case 'TASK_DELETE':
      return {
        ...state,
        tasks: state.tasks.filter((t) => t.id !== action.payload.id),
      };

    case 'TASKS_HYDRATE':
      return { ...state, tasks: action.payload.tasks };

    default:
      return state;
  }
}
```

### Context Provider Shape

```typescript
interface TimerContextValue {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
}

const TimerContext = createContext<TimerContextValue | undefined>(undefined);

function TimerProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialAppState);

  // Hydrate tasks on mount
  useEffect(() => {
    AsyncStorage.getItem('pomodoro-tasks').then((json) => {
      if (json) {
        const tasks = JSON.parse(json) as Task[];
        dispatch({ type: 'TASKS_HYDRATE', payload: { tasks } });
      }
    });
  }, []);

  // Persist tasks on change
  useEffect(() => {
    AsyncStorage.setItem('pomodoro-tasks', JSON.stringify(state.tasks));
  }, [state.tasks]);

  // Timer engine (see Timer Engine Architecture below)
  useTimerEngine(state.timer, dispatch);

  return (
    <TimerContext.Provider value={{ state, dispatch }}>
      {children}
    </TimerContext.Provider>
  );
}
```

---

## Timer Engine Architecture — State Machine

### State Diagram

```
                    ┌─────────┐
          RESET ──→ │  IDLE   │ ←── COMPLETE (auto-transition)
                    └────┬────┘
                         │ START
                         ▼
                    ┌─────────┐
          PAUSE ──→ │ RUNNING │ ←── RESUME
                    └────┬────┘
                         │ TICK → timeRemaining=0?
                         ▼
                    ┌──────────┐
                    │ COMPLETE │
                    └────┬─────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
     work 완료 → break 시작    break 완료 → work 시작
     (session++)               (no session++)
              │                     │
              └──────────┬──────────┘
                         ▼
                      IDLE (자동)
```

### useTimerEngine Hook

```typescript
function useTimerEngine(timer: TimerState, dispatch: React.Dispatch<AppAction>) {
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(0);
  const expectedRef = useRef<number>(0);

  useEffect(() => {
    if (timer.status === 'running') {
      // Drift-compensating setInterval: recalibrate each tick
      startTimeRef.current = Date.now();
      expectedRef.current = timer.timeRemaining;

      intervalRef.current = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000);
        const actual = expectedRef.current - elapsed;

        if (actual <= 0) {
          // Timer completed
          clearInterval(intervalRef.current!);
          const nextSession: SessionType =
            timer.sessionType === 'work' ? 'break' : 'work';

          if (timer.sessionType === 'work') {
            dispatch({ type: 'SESSION_INCREMENT' });
            scheduleCompletionNotification('work');
          } else {
            scheduleCompletionNotification('break');
          }

          dispatch({ type: 'TIMER_COMPLETE', nextSession });
        } else {
          dispatch({ type: 'TIMER_TICK' });
          // Sync reducer's timeRemaining to actual for drift correction
          // (handled by TIMER_TICK reducing by 1, but we can force-sync if drift > 1s)
        }
      }, 1000);
    }

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [timer.status, timer.sessionType]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);
}
```

**Drift Compensation**: `Date.now()` 기준 경과 초를 계산하여 `setInterval` 누적 오차를 보정한다. 1초 tick마다 실제 경과 시간과 비교해 보정 — p95 오차 ≤ 500ms 보장.

### Timer Engine Key Decisions

| Decision | Rationale |
|---|---|
| `setInterval` 1s vs `requestAnimationFrame` | 1초 단위 UI 업데이트에 충분. 웹 백그라운드 탭에서 `setInterval`이 스로틀되지만, 포그라운드 복귀 시 `Date.now()` 보정으로 즉시 동기화 |
| Reducer-driven vs local state | Reducer가 단일 진실 공급원(single source of truth). 디버깅과 테스트가 단순해짐 |
| `TIMER_COMPLETE` 액션 분리 | `TIMER_TICK`이 0을 감지하면 `useTimerEngine`에서 `TIMER_COMPLETE`를 dispatch — 효과(notification)와 상태 전이를 분리 |
| Work → Break 자동 전환 | `TIMER_COMPLETE` 핸들러가 `nextSession`을 계산. 사용자가 수동으로 break 시작할 필요 없음 |

---

## Navigation — Expo Router

### File Structure

```
app/
├── _layout.tsx        // Root layout: Stack navigator + TimerProvider wrap
├── index.tsx          // Home screen (timer) — route: "/"
└── tasks.tsx          // Task list screen — route: "/tasks"
```

### `app/_layout.tsx` — Root Layout

```typescript
import { Stack } from 'expo-router';
import { TimerProvider } from '../src/context/TimerContext';

export default function RootLayout() {
  return (
    <TimerProvider>
      <Stack>
        <Stack.Screen name="index" options={{ title: 'Pomodoro', headerShown: false }} />
        <Stack.Screen name="tasks" options={{ title: 'Tasks', presentation: 'modal' }} />
      </Stack>
    </TimerProvider>
  );
}
```

### Routing Table

| Route | Screen | Navigation Method | Transition |
|---|---|---|---|
| `/` | HomeScreen (timer) | Initial route | — |
| `/tasks` | TaskListScreen | `<Link href="/tasks">` or `router.push('/tasks')` | Modal slide-up (iOS) / standard (Android/Web) |

---

## Data Model

### Persistence Strategy

| Data | Storage | Key | Serialization | Hydrate Timing |
|---|---|---|---|
| Tasks | AsyncStorage | `pomodoro-tasks` | `JSON.stringify(Task[])` | App mount (once) |
| Session count | In-memory only | — | — | Reset daily (midnight check on app foreground) |
| Timer state | In-memory only | — | — | Reset on app cold start |

**Daily Session Reset**: 앱이 foreground로 올라올 때 `AppState.addEventListener('change')`로 날짜 변경을 감지, 자정이 지났으면 `sessionsToday`를 0으로 리셋.

### TypeScript Data Types

```typescript
// src/types.ts

export type TimerStatus = 'idle' | 'running' | 'paused';
export type SessionType = 'work' | 'break';

export interface TimerState {
  status: TimerStatus;
  sessionType: SessionType;
  timeRemaining: number;
  totalDuration: number;
  sessionsToday: number;
}

export interface Task {
  id: string;
  title: string;
  completed: boolean;
  createdAt: string;
}

export interface AppState {
  timer: TimerState;
  tasks: Task[];
}
```

---

## Notification Strategy

### Architecture

```
Timer Complete
    │
    ├── work session finishes
    │       ├── dispatch(SESSION_INCREMENT)
    │       ├── scheduleNotificationAsync({ title: "🎉 Work session done!", body: "Take a 5-min break" })
    │       └── haptic feedback (expo-haptics)
    │
    └── break session finishes
            ├── scheduleNotificationAsync({ title: "☕ Break over!", body: "Time to focus" })
            └── haptic feedback (expo-haptics)
```

### Implementation Outline

```typescript
// src/lib/notifications.ts
import * as Notifications from 'expo-notifications';
import * as Haptics from 'expo-haptics';
import { Platform } from 'react-native';

export async function requestPermissions(): Promise<boolean> {
  const { status } = await Notifications.requestPermissionsAsync();
  return status === 'granted';
}

export async function scheduleCompletionNotification(
  sessionType: 'work' | 'break'
): Promise<void> {
  // Cancel any pending notifications first
  await Notifications.cancelAllScheduledNotificationsAsync();

  const isWork = sessionType === 'work';
  await Notifications.scheduleNotificationAsync({
    content: {
      title: isWork ? '🎉 Work Session Complete!' : '☕ Break Over!',
      body: isWork ? 'Great job! Take a 5-minute break.' : 'Break finished. Ready to focus?',
      sound: true,
    },
    trigger: null, // immediate
  });

  // Haptic feedback
  if (Platform.OS !== 'web') {
    await Haptics.notificationAsync(
      isWork
        ? Haptics.NotificationFeedbackType.Success
        : Haptics.NotificationFeedbackType.Warning
    );
  }
}

// Notification handler setup (called once in _layout.tsx)
export function setupNotificationHandler(): void {
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowAlert: true,
      shouldPlaySound: true,
      shouldSetBadge: false,
    }),
  });
}
```

### Notification Flow by Platform

| Platform | Foreground Behavior | Background Behavior | Permission Model |
|---|---|---|---|
| **iOS** | Alert via `setNotificationHandler` → `shouldShowAlert: true` | System notification center | Prompt on first `requestPermissionsAsync` call |
| **Android** | Heads-up notification (channel: "pomodoro-alerts") | System tray | Auto-granted (Android 13+ requires runtime prompt) |
| **Web** | `Notification` API — browser permission dialog | Service Worker required for background (out of scope for MVP) | Browser permission dialog on first call |

---

## Cross-Platform Adaptation Table

| Feature | iOS | Android | Web (Expo Web) |
|---|---|---|---|
| **Timer tick** | `setInterval` + `Date.now()` drift compensation | Same as iOS | Same; background tabs throttle `setInterval` → `Date.now()` recalibrates on focus |
| **Background timer** | Not supported (iOS kills JS after ~30s bg). Foreground-only MVP | Foreground-only MVP | Foreground-only MVP |
| **Notifications** | `expo-notifications` → APNs | `expo-notifications` → FCM | `expo-notifications` → Web Notification API (`Notification`) |
| **Haptics** | `expo-haptics` → `UIImpactFeedbackGenerator` | `expo-haptics` → `Vibration` API | No-op (not available) |
| **AsyncStorage** | Native `NSUserDefaults` (via expo) | Native `SharedPreferences` (via expo) | `localStorage` fallback (via expo) |
| **SafeArea** | `react-native-safe-area-context` — dynamic island / notch | Status bar + navigation bar insets | CSS `env(safe-area-inset-*)` via `react-native-web` |
| **Navigation** | Stack modal slide-up | Standard stack push | CSS transitions via `react-native-web` |
| **Fonts** | San Francisco (system) | Roboto (system) | System font stack |
| **Status bar** | `expo-status-bar` light/dark | `expo-status-bar` light/dark | N/A (browser viewport) |
| **Splash screen** | `expo-splash-screen` | `expo-splash-screen` | Custom HTML splash via `webpack` config |

### Platform-Specific Code Strategy

```
src/
├── lib/
│   ├── notifications.ts      // platform-agnostic; expo-notifications handles abstraction
│   ├── haptics.ts            // if (Platform.OS === 'web') return; else Haptics.impactAsync()
│   └── timer.ts              // fully cross-platform (Date.now + setInterval)
```

No `.ios.ts` / `.android.ts` file extensions needed — `expo-*` modules provide runtime abstraction. Only `Platform.OS` checks for web-only exclusions (haptics).

---

## Gap Matrix

| Cat | Item | Evidence | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| 🆕 | Timer engine (`useTimerEngine`) | Design above | — | MED | M1 (spec-match: 25/5 min 정확도) |
| 🆕 | TimerProvider + appReducer | State Management section | — | LOW | M1 |
| 🆕 | HomeScreen (timer UI) | Component Tree section | — | LOW | M1 |
| 🆕 | TaskListScreen (CRUD UI) | Component Tree section | — | LOW | M1 |
| 🆕 | AsyncStorage persistence layer | Data Model section | — | LOW | M3 (regression: 기존 데이터 손실 없음) |
| 🆕 | expo-notifications integration | Notification Strategy section | — | MED | S2 (알림 권한) |
| 🆕 | Expo Router navigation | Navigation section | — | LOW | M1 |
| 🆕 | Cross-platform web target | Adaptation Table | — | MED | M2 (웹 + 모바일 동시 테스트) |
| 🆕 | Daily session counter + reset | Data Model section | — | LOW | M1 |

---

## Waves

### Wave 1 — Foundation (4 tasks, parallel, ≤40 K tokens)

- [ ] **w1-s1: Project scaffolding**
  - **Action**: `npx create-expo-app@latest pomodoro-timer --template blank-typescript` → install deps (`expo-router`, `expo-notifications`, `@react-native-async-storage/async-storage`, `expo-haptics`, `expo-constants`, `react-native-safe-area-context`, `react-native-screens`)
  - **Files**: `package.json`, `app.json`, `tsconfig.json`, `app/_layout.tsx`
  - **Worker**: medium
  - **Token est**: ~3 K
  - **Verify**: `npx expo start --web` → blank Expo Router app renders
  - **Gate**: M1 (spec-match: 프로젝트 구조)

- [ ] **w1-s2: Types + Data Model**
  - **Action**: Create `src/types.ts` with all interfaces from Props Interfaces section above
  - **Files**: `src/types.ts`
  - **Worker**: mini
  - **Token est**: ~2 K
  - **Verify**: `npx tsc --noEmit` → zero type errors
  - **Gate**: M4 (lint clean)

- [ ] **w1-s3: Reducer + Context**
  - **Action**: Implement `appReducer` and `TimerProvider` as specified in State Management section
  - **Files**: `src/context/TimerContext.tsx`, `src/context/__tests__/TimerContext.test.tsx`
  - **Worker**: heavy
  - **Token est**: ~8 K
  - **Verify**: `npx jest src/context/__tests__/` → all reducer transitions pass; `npm run lint` → 0 warnings
  - **Gate**: M2 (test pass=100%), M4

- [ ] **w1-s4: Notification setup**
  - **Action**: Implement `src/lib/notifications.ts` and `src/lib/haptics.ts` as specified
  - **Files**: `src/lib/notifications.ts`, `src/lib/haptics.ts`, `src/lib/__tests__/notifications.test.ts`
  - **Worker**: medium
  - **Token est**: ~4 K
  - **Verify**: mock `expo-notifications` → `scheduleCompletionNotification` resolves; permissions request mock returns `granted`
  - **Gate**: S2 (알림 권한 플로우)

### Wave 2 — Core UI (3 tasks, parallel, ≤35 K tokens; depends on Wave 1)

- [ ] **w2-s1: TimerDisplay + CircularProgress**
  - **Action**: Build `TimerDisplay`, `CircularProgress`, `SessionTypeIndicator` components. Format time as `MM:SS`. CircularProgress uses SVG (`react-native-svg`) with `strokeDashoffset` driven by progress prop.
  - **Files**: `src/components/TimerDisplay.tsx`, `src/components/CircularProgress.tsx`, `src/components/SessionTypeIndicator.tsx`, `src/components/__tests__/TimerDisplay.test.tsx`
  - **Worker**: heavy
  - **Token est**: ~8 K
  - **Verify**: Snapshot test for each component; manual: progress bar visually matches `(timeRemaining / totalDuration)`
  - **Gate**: M1, M2

- [ ] **w2-s2: TimerControls + SessionCounter**
  - **Action**: Build `TimerControls` (Start/Pause/Reset buttons, contextually enabled/disabled per `TimerStatus`) and `SessionCounter` (displays `sessionsToday`). Wire to `useContext(TimerContext)`.
  - **Files**: `src/components/TimerControls.tsx`, `src/components/SessionCounter.tsx`, `src/components/__tests__/TimerControls.test.tsx`
  - **Worker**: medium
  - **Token est**: ~5 K
  - **Verify**: Unit test: Start dispatches `TIMER_START`; Pause dispatches `TIMER_PAUSE`; Reset dispatches `TIMER_RESET`; Pause button disabled when idle; Start button disabled when running
  - **Gate**: M2

- [ ] **w2-s3: useTimerEngine hook**
  - **Action**: Implement the drift-compensating timer engine as designed. Integrate with `TimerProvider` (already scaffolded in w1-s3). On completion: dispatch `TIMER_COMPLETE` + `SESSION_INCREMENT` + `scheduleCompletionNotification`.
  - **Files**: `src/hooks/useTimerEngine.ts`, `src/hooks/__tests__/useTimerEngine.test.ts`
  - **Worker**: heavy
  - **Token est**: ~10 K
  - **Verify**: Jest fake timers: after 1500 ticks (25 min), verify `TIMER_COMPLETE` dispatched with `nextSession='break'`; after 300 ticks (5 min break), verify `nextSession='work'`; drift test: advance `Date.now()` by 2.5s between ticks, verify correction
  - **Gate**: M2 (test pass=100%), P1 (drift ≤ 500ms)

### Wave 3 — Task List + Integration (3 tasks, parallel, ≤30 K tokens; depends on Wave 2)

- [ ] **w3-s1: TaskItem + TaskInput + EmptyState**
  - **Action**: Build `TaskInput` (TextInput + submit button), `TaskItem` (checkbox + swipe-to-delete via `react-native-gesture-handler`), `EmptyState` (illustration + message).
  - **Files**: `src/components/TaskInput.tsx`, `src/components/TaskItem.tsx`, `src/components/EmptyState.tsx`, `src/components/__tests__/TaskItem.test.tsx`
  - **Worker**: heavy
  - **Token est**: ~10 K
  - **Verify**: Snapshot tests; interaction tests: add task → appears in list; toggle → completed style change; swipe → delete → removed from list
  - **Gate**: M2, M5 (ensure deleted tasks not leaked in AsyncStorage)

- [ ] **w3-s2: TaskListScreen**
  - **Action**: Compose `TaskInput` + `FlatList<TaskItem>` + `EmptyState` into `app/tasks.tsx`. Wire to Context. Handle AsyncStorage hydration loading state.
  - **Files**: `app/tasks.tsx`, `src/components/TaskBadge.tsx`
  - **Worker**: medium
  - **Token est**: ~6 K
  - **Verify**: Navigation test: tap badge on Home → navigates to `/tasks`; add 3 tasks → persist → kill app → relaunch → 3 tasks still present
  - **Gate**: M2, M3 (regression: AsyncStorage persistence)

- [ ] **w3-s3: HomeScreen (final assembly)**
  - **Action**: Compose all timer components into `app/index.tsx`. Wire `useTimerEngine` via `TimerProvider`. Add `TaskBadge` with `pendingCount` linking to `/tasks`. Style with `StyleSheet.create`.
  - **Files**: `app/index.tsx`, `src/screens/HomeScreen.tsx`
  - **Worker**: medium
  - **Token est**: ~5 K
  - **Verify**: Full integration test: Start timer → ticks every 1s → after 25 min (simulated with fake timers) → notification fires → session count +1 → timer auto-resets to break mode
  - **Gate**: M2 (integration test), M3 (full flow regression)

### Wave 4 — Hardening (3 tasks, parallel, ≤25 K tokens; depends on Wave 3)

- [ ] **w4-s1: Cross-platform QA**
  - **Action**: Run `npx expo start --web`, test on Chrome/Safari/Firefox. Verify: timer ticks, notifications (`Notification` API), AsyncStorage (`localStorage`), layout at mobile + desktop widths. Run `npx expo run:ios` (sim) and `npx expo run:android` (emulator).
  - **Files**: none (QA only). Add `src/lib/platform.ts` with `isWeb()` helper if needed.
  - **Worker**: medium
  - **Token est**: ~3 K
  - **Verify**: Checklist: web notification permission dialog appears; iOS safe area respected; Android status bar icons visible; no layout overflow at 320px width
  - **Gate**: M1 (cross-platform spec-match)

- [ ] **w4-s2: Edge cases + error boundaries**
  - **Action**: Add `ErrorBoundary` component wrapping each screen. Handle: AsyncStorage read failure (fallback to empty tasks), notification permission denied (silent degrade), app background/foreground transitions (recalibrate timer via `AppState` listener), midnight session reset.
  - **Files**: `src/components/ErrorBoundary.tsx`, updates to `src/context/TimerContext.tsx`
  - **Worker**: medium
  - **Token est**: ~6 K
  - **Verify**: Mock AsyncStorage.getItem throwing → app renders with empty task list. Mock `Date` to 23:59:59 → advance 2s → sessionsToday resets to 0
  - **Gate**: M2, M3

- [ ] **w4-s3: Performance + accessibility audit**
  - **Action**: Audit: ensure `FlatList` uses `keyExtractor` + `getItemLayout`. Ensure `CircularProgress` avoids re-render on parent state change (React.memo). Add `accessibilityLabel` to all interactive elements. Run `npx expo-doctor`.
  - **Files**: updates to existing components
  - **Worker**: mini
  - **Token est**: ~4 K
  - **Verify**: React DevTools profiler: no unnecessary re-renders on timer tick (only `TimerDisplay` subtree). Lighthouse audit (web): ≥ 90 perf score. `expo-doctor` passes
  - **Gate**: P3 (latency: UI frame drops ≤ 0), M4

---

## Risk Register (BKIT 11-Gate)

| Risk | BKIT Class | Severity | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| Timer tick drift accumulates over long sessions | `P1_query` | MED | p95 ≤ 500ms | `Date.now()` 기반 drift compensation (useTimerEngine) | Jest fake timers + Date mocking: 25분 시뮬레이션 후 오차 측정 |
| AsyncStorage write fails → task data loss | `M3_regression` | MED | 0 data loss | try/catch on `setItem`; fallback: in-memory state 유지, 재시도 로직 | Mock `AsyncStorage.setItem` throwing → in-memory tasks unchanged |
| Notification permission denied | `S2_auth` | LOW | 앱 기능 저하 없이 동작 | Notification 실패 시 silent degrade; 타이머는 정상 동작 | Mock `requestPermissionsAsync` → `denied` → 앱 crash 없음 |
| Web background tab timer drift | `P3_latency` | LOW | foreground 복귀 시 1초 내 동기화 | `AppState` 'active' 이벤트에서 `Date.now()` 재보정 | 수동 테스트: 탭 백그라운드 5분 → 복귀 시 시간 점프 없이 정확 |
| Expo SDK 버전 업그레이드 시 breaking change | `M3_regression` | LOW | CI 통과 | `package.json`에 정확한 SDK 버전 고정 (`~52.0.0`) | Dependabot + CI 테스트 |
| Task list 대량(500+) 시 FlatList 성능 저하 | `P2_memory` | LOW | scroll FPS ≥ 55 | `getItemLayout`, `windowSize=10`, `removeClippedSubviews` | 수동 테스트: 500개 task 추가 후 스크롤 FPS 측정 |
| 알림 채널 미설정 (Android) | `S2_auth` | MED | Android 알림 미도달 | `expo-notifications` `setNotificationChannelAsync` 호출 (앱 시작 시) | Android emulator에서 알림 수신 확인 |
| 25분/5분 상수 하드코딩 → 추후 변경 어려움 | `M1_spec_match` | LOW | — | `src/constants.ts`에 `WORK_DURATION`, `BREAK_DURATION` 상수 정의 | grep: `1500` 또는 `300`이 reducer 외부에 하드코딩되지 않았는지 확인 |

---

## Execution

Run this plan with:

```
blackcow-loop "Execute plans/pomodoro-timer-app.md" \
  --completion-promise='All 4 waves complete: timer engine passes drift tests (p95 ≤ 500ms), task CRUD persists via AsyncStorage, notifications fire on session end, cross-platform (web + iOS sim + Android emu) verified, lint=0warn, test pass=100%' \
  --trust-level=2
```

### Parallelism Guide

- **Wave 1**: 4 workers in parallel (scaffold, types, reducer, notifications — all independent)
- **Wave 2**: 3 workers in parallel (TimerDisplay, TimerControls, useTimerEngine — share Context but build independently)
- **Wave 3**: 3 workers in parallel (TaskItem+Input, TaskListScreen, HomeScreen — HomeScreen depends on all timer components from Wave 2; TaskListScreen depends on task components from w3-s1)
- **Wave 4**: 3 workers in parallel (QA, edge-cases, perf audit)
- **Total budget**: ~18 K tokens for plan; ~80 K tokens for 4-wave execution
- **Critical path**: w1-s3 (Reducer) → w2-s3 (useTimerEngine) → w3-s3 (HomeScreen) → w4-s2 (edge cases) = 4 hops

---

## Appendix: File Structure (Post-Implementation)

```
pomodoro-timer/
├── app/
│   ├── _layout.tsx              // Root layout: Stack + TimerProvider
│   ├── index.tsx                // Home screen (timer)
│   └── tasks.tsx                // Task list screen
├── src/
│   ├── types.ts                 // All TypeScript interfaces
│   ├── constants.ts             // WORK_DURATION, BREAK_DURATION, STORAGE_KEY
│   ├── context/
│   │   ├── TimerContext.tsx      // Context + Provider + appReducer
│   │   └── __tests__/
│   │       └── TimerContext.test.tsx
│   ├── hooks/
│   │   ├── useTimerEngine.ts    // Drift-compensating timer loop
│   │   └── __tests__/
│   │       └── useTimerEngine.test.ts
│   ├── lib/
│   │   ├── notifications.ts     // expo-notifications wrapper
│   │   ├── haptics.ts           // expo-haptics wrapper (web no-op)
│   │   ├── platform.ts          // isWeb() helper
│   │   └── __tests__/
│   │       └── notifications.test.ts
│   ├── components/
│   │   ├── TimerDisplay.tsx
│   │   ├── CircularProgress.tsx
│   │   ├── SessionTypeIndicator.tsx
│   │   ├── TimerControls.tsx
│   │   ├── SessionCounter.tsx
│   │   ├── TaskInput.tsx
│   │   ├── TaskItem.tsx
│   │   ├── TaskBadge.tsx
│   │   ├── EmptyState.tsx
│   │   ├── ErrorBoundary.tsx
│   │   └── __tests__/
│   │       ├── TimerDisplay.test.tsx
│   │       ├── TimerControls.test.tsx
│   │       └── TaskItem.test.tsx
│   └── screens/
│       └── HomeScreen.tsx       // (optional separation from app/index.tsx)
├── assets/                      // icon, splash, adaptive-icon
├── app.json                     // Expo config
├── tsconfig.json
├── package.json
├── jest.config.ts
└── README.md
```
