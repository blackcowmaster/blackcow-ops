# Plan: Mobile Workout Tracker — 8-Unit PRD Decomposition

| Field | Value |
|---|---|
| **Slug** | `workout-tracker-decomp` |
| **Created** | 2026-06-28T00:00:00Z |
| **Class** | **XL** (8 units, 7 features, greenfield mobile app) |
| **Explore lanes** | 0 dispatched (greenfield — no mobile codebase exists) |
| **Adversarial reviews** | 1/1 passed — 4 issues resolved, 0 rejections |
| **Budget** | ~20K tokens / 128K target |

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | 사용자가 운동 기록, 진행 상황 시각화, 리마인더 알림, 오프라인 로깅+동기화가 가능한 모바일 운동 추적기를 원함 |
| **WHO** | 개인 운동자 (헬스장 이용자, 홈트레이닝) — iOS + Android |
| **WHAT** | 8개 유닛(U0~U7)으로 분해된 Expo React Native 모바일 앱 아키텍처 문서 |
| **RISK** | 오프라인 동기화(U6)는 아키텍처상 가장 복잡한 유닛. 동기화 상태 머신 오류 시 데이터 손실 가능성. Expo managed workflow 제약으로 BLE/애플워치 등 네이티브 모듈 필요 시 bare workflow로 마이그레이션 필요 |
| **SUCCESS** | 모든 PRD 요구사항(운동 기록, 진행 차트, 리마인더, 오프라인 동기화)이 유닛에 커버됨. 각 유닛이 독립적으로 개발·테스트 가능. 유닛 간 의존성 그래프에 순환 없음. 차트 데이터 컨트랙트(U3→U4) 및 동기화 인터페이스(U3→U6)가 U0에 동결됨 |
| **SCOPE** | 포함: 8개 유닛(U0~U7), Expo managed workflow, TypeScript, expo-router, expo-sqlite, expo-notifications, victory-native, zustand, Supabase / 제외: 애플워치/Wear OS, 소셜 공유, 영양 추적, 실시간 협업 운동, bare workflow 마이그레이션 |

## Summary

Greenfield React Native 운동 추적 앱을 Expo managed workflow로 구축. 7개 기능(Auth, Exercise Library, Workout Logger, Progress Charts, Reminders, Offline Sync, Settings)을 8개 유닛으로 분해. U0(Scaffold)가 직렬 선행조건이며, U1/U2/U5/U7은 4× 병렬 개발 가능. U3(Logger)와 U4(Charts)는 U2 완료 후 2× 병렬. U6(Sync)는 데이터 모델 안정화 후 최후미에 배치. 모든 유닛은 mock 데이터로 독립 개발·테스트 가능.

## Architecture Options

### Option A — Monolith Screen-per-Feature
- **접근법**: 단일 Expo 앱, 모든 기능을 스크린 단위로 구분. zustand store 하나로 전역 상태 관리
- **장점**: 가장 빠른 MVP 출시, 파일 수 적음, Expo Go에서 즉시 테스트
- **단점**: 오프라인 동기화 레이어가 Logger/Exercise Library와 강결합. 리팩토링 비용 높음
- **적합**: 1인 개발, 2주 내 MVP
- **예상 파일 수**: ~30개

### Option B — Layered Clean Architecture (Repository Pattern)
- **접근법**: Interface/Application/Domain/Infrastructure 4계층. Repository 추상화로 SQLite/Supabase 교체 가능
- **장점**: U6(Sync) 추가 시 Repository만 교체. 테스트 용이성 최상. 장기 유지보수성
- **적합**: 팀 규모 3인 이상, 장기 프로젝트
- **예상 파일 수**: ~80개

### Option C — Pragmatic Store-Facade (권장)
- **접근법**: zustand store가 data-access facade 역할. 각 store가 `syncAdapter` 인터페이스를 통해 U6에 연결. U3는 `useWorkoutStore`를 통해 저장 — U6 도입 시 store 내부만 교체
- **장점**: Option A의 속도 + Option B의 확장성. U3→U6 save-path 충돌 해결됨. 리팩토링 없이 U6 추가 가능
- **적합**: 대부분의 Expo 프로젝트 (1~3인 팀, 4~8주)
- **예상 파일 수**: ~50개

### 권장: Option C (Pragmatic Store-Facade)
**사유**: U3(Logger)의 save-path를 `useWorkoutStore` facade로 설계하여, Phase 3에서는 Supabase 직접 저장, Phase 4(U6 도입)에서는 store 내부만 sync queue로 교체 — "painful retrofit" 리스크 제거. Option A는 U6 추가 시 재작성 필요. Option B는 greenfield 1~3인 팀에 과잉 설계.

## Codebase Survey Summary

| Lane | Key Finding | BKIT Gate |
|---|---|---|
| Surface | Greenfield — no mobile codebase. Existing project is unrelated Express backend (`sim-express-crud`) | — |
| Stack | Package.json shows Node.js/Express/TypeScript — irrelevant to React Native. Tech stack auto-selected per governance: Expo managed + TypeScript | — |
| Pre-flight | No `app.json`, no `expo` deps, no `apps/` monorepo. Pure greenfield mobile app | — |

## Gap Matrix

| Cat | Item | Evidence | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| 🆕 | U0 — Expo scaffold (`create-expo-app` + expo-router + zustand + shared types) | Governance §U0 | — | — | M1 |
| 🆕 | U1 — Supabase Auth (email/password + social + expo-secure-store) | Governance §U1 | — | — | M1 |
| 🆕 | U2 — Exercise Library (FlatList/SectionList + search + custom exercises) | Governance §U2 | — | — | M1 |
| 🆕 | U3 — Workout Logger (dynamic set form + rest timer + CRUD) | Governance §U3 | — | MED | M1 (save-path routing via store facade) |
| 🆕 | U4 — Progress Charts (victory-native line/bar + streak calendar + PR detection) | Governance §U4 | — | — | M1, D3 (chart-data-contract) |
| 🆕 | U5 — Reminders (expo-notifications scheduling + deep link) | Governance §U5 | — | — | M1 |
| 🆕 | U6 — Offline Sync (expo-sqlite + sync queue + LWW conflict) | Governance §U6 | — | HIGH | M1, S1 (dataFlow integrity) |
| 🆕 | U7 — Settings (units toggle + dark mode + data export + notification prefs) | Governance §U7 | — | — | M1 |
| 🔧 | U5↔U7 boundary — notification scheduling UI vs global notification prefs ownership | Reviewer A finding | HIGH | MED | M1 (boundary conflict) |
| 🔧 | U3↔U6 save-path — U3's `useWorkoutStore` must be designed as facade from day one | Reviewer A finding | HIGH | HIGH | M1, S1 (save-path routing) |
| ⚠️ | Workout History screen — browsing past completed workouts as chronological list | Reviewer A finding | HIGH | MED | M1 (missing from explicit scope) |
| ⚠️ | Workout templates — save-as-template / apply-template flows | Reviewer A finding | — | LOW | — (deferred post-MVP) |

## Waves

### Wave 1 — Foundation (1 task, serial, ~1 session)

- [ ] **u0-scaffold**: Expo project scaffold with TypeScript template, expo-router file-based routing, zustand store patterns, shared types (`Exercise`, `Workout`, `Set`, `ProgressDataPoint`, `User`, `AuthState`, `SyncOperation`), Supabase client stub, theme context, folder structure
  - **Files**: `app.json`, `tsconfig.json`, `src/app/_layout.tsx`, `src/app/index.tsx`, `src/types/exercise.ts`, `src/types/workout.ts`, `src/types/set.ts`, `src/types/progress.ts`, `src/types/auth.ts`, `src/types/sync.ts`, `src/lib/supabase.ts`, `src/theme/ThemeContext.tsx`, `src/stores/` (store patterns)
  - **Worker**: heavy
  - **Token est:** ~4K
  - **Gate:** M1 (spec-match: all shared types defined, contracts frozen)
  - **Verify:** `npx tsc --noEmit` passes on shared types. `npx expo start` renders navigation shell with placeholder screens
  - **Evidence:** `.omo/workout-tracker/evidence/u0-types-check.txt`, `.omo/workout-tracker/evidence/u0-expo-start.txt`
  - **CRITICAL:** The `useWorkoutStore` facade must define a `syncAdapter` interface from day one (Option C). U3 writes through the store; U6 later implements the adapter.

### Wave 2 — Parallel Features (4 tasks, 4× parallel, ~6–8 sessions total)

- [ ] **u1-auth**: Supabase Auth (email/password + social), expo-secure-store session persistence, auth zustand store, login/register/reset/logout screens
  - **Files**: `src/app/(auth)/login.tsx`, `src/app/(auth)/register.tsx`, `src/app/(auth)/reset-password.tsx`, `src/stores/useAuthStore.ts`, `src/hooks/useSession.ts`, `src/lib/supabase.ts` (extend)
  - **Worker**: medium
  - **Token est:** ~3K
  - **Gate:** M1 (all auth flows: login, register, reset, logout, auto-login from stored session)
  - **Verify:** Mock Supabase: register → session stored → auto-login → logout clears session → password reset email triggered
  - **Evidence:** `.omo/workout-tracker/evidence/u1-auth-flows.txt`
  - **Deps:** U0 (scaffold, `User`/`AuthState` types, Supabase client stub)

- [ ] **u2-exercise-library**: Exercise list with category filters, search bar, exercise detail card, "Add Custom Exercise" flow, FlatList/SectionList
  - **Files**: `src/app/(tabs)/exercises.tsx`, `src/app/exercise/[id].tsx`, `src/components/ExerciseCard.tsx`, `src/components/ExerciseSelect.tsx`, `src/components/CategoryFilter.tsx`, `src/stores/useExerciseStore.ts`, `src/lib/exerciseSeedData.ts` (preloaded library)
  - **Worker**: medium
  - **Token est:** ~3K
  - **Gate:** M1 (search filters by name/muscle, category filters list, custom exercise persists)
  - **Verify:** FlatList renders 50+ exercises across categories, search debounce filters correctly, tap category filters list, add custom exercise → persists to store, empty state when no results
  - **Evidence:** `.omo/workout-tracker/evidence/u2-exercise-list.txt`
  - **Deps:** U0 (scaffold, `Exercise` type), U1 (auth session — mockable)

- [ ] **u5-reminders**: Reminder configuration screen, expo-notifications scheduling, day-of-week + time selection, multiple slots, deep link to logger, snooze
  - **Files**: `src/app/(tabs)/reminders.tsx`, `src/stores/useReminderStore.ts`, `src/lib/notifications.ts`, `src/hooks/useNotificationPermissions.ts`
  - **Worker**: medium
  - **Token est:** ~2K
  - **Gate:** M1 (notifications scheduled, tap → deep link, disable cancels all, snooze fires after delay)
  - **Verify:** Enable reminders → Mon/Wed/Fri 7:00 AM → verify 3 scheduled → tap notification opens app → disable → verify cancelled → snooze test
  - **Evidence:** `.omo/workout-tracker/evidence/u5-reminders.txt`
  - **Deps:** U0 (scaffold), U7 (notification preferences — mockable)
  - **BOUNDARY NOTE:** U5 exclusively owns the workout-reminder scheduling UI (day/time selection). U7 owns only sound/vibration/global defaults. Do NOT build scheduling UI in U7.

- [ ] **u7-settings**: Units toggle (lbs/kg), dark mode toggle, theme context, notification preferences (sound, vibration), data export (JSON/CSV), account management, app info
  - **Files**: `src/app/(tabs)/settings.tsx`, `src/stores/useSettingsStore.ts`, `src/theme/ThemeContext.tsx` (extend), `src/lib/export.ts`
  - **Worker**: mini
  - **Token est:** ~2K
  - **Gate:** M1 (units toggle, dark mode persist across restart, data export produces valid JSON)
  - **Verify:** Toggle lbs→kg → verify display, toggle dark mode → all screens re-render → kill app → relaunch → prefs preserved → export → valid JSON
  - **Evidence:** `.omo/workout-tracker/evidence/u7-settings.txt`
  - **Deps:** U0 (scaffold, theme context)
  - **NOTE:** U7 provides `notificationPrefs` (sound, vibration, global defaults) consumed by U5. U5 owns the scheduling UI.

### Wave 3 — Core Features (2 tasks, 2× parallel, ~6–8 sessions total)

- [ ] **u3-workout-logger**: Workout session screen, exercise selection from U2, dynamic set form (weight × reps × RPE), rest timer, workout duration tracker, notes, save/edit/delete workouts, **Workout History screen** (chronological list of past workouts), swipe-to-delete set
  - **Files**: `src/app/(tabs)/log.tsx`, `src/app/workout/[id].tsx`, `src/app/workout/history.tsx`, `src/components/SetRow.tsx`, `src/components/RestTimer.tsx`, `src/stores/useWorkoutStore.ts` (facade with `syncAdapter` interface), `src/hooks/useRestTimer.ts`
  - **Worker**: heavy
  - **Token est:** ~4K
  - **Gate:** M1 (exercise selection, dynamic set add/remove, rest timer, save/edit/delete, history list), S1 (save-path routes through `useWorkoutStore` facade — NOT direct Supabase call)
  - **Verify:** Select exercise → add 3 sets → rest timer counts down → save → workout appears in history → edit → add/remove sets → delete → history updated. Verify save goes through `useWorkoutStore.syncAdapter` interface.
  - **Evidence:** `.omo/workout-tracker/evidence/u3-logger.txt`, `.omo/workout-tracker/evidence/u3-history.txt`
  - **Deps:** U0 (scaffold, `Workout`/`Set` types), U1 (auth session — mockable), U2 (`ExerciseSelect` component, `Exercise` type)
  - **CRITICAL:** `useWorkoutStore` MUST implement a `syncAdapter` interface: `{ saveWorkout, updateWorkout, deleteWorkout, getWorkouts }`. In Wave 3, the adapter calls Supabase directly. In Wave 4 (U6), the adapter is swapped for a sync-queue adapter. This prevents the U3↔U6 save-path retrofit problem identified by adversarial review.
  - **SCOPE ADDITION:** Workout History screen (`src/app/workout/history.tsx`) explicitly included — chronological list of all past workouts with quick stats. This was identified as a missing screen in adversarial review.

- [ ] **u4-progress-charts**: Progress dashboard, victory-native line chart (weight progression per exercise), bar chart (total volume per workout), streak calendar, date range picker (1W/1M/3M/6M/1Y/All), PR annotations, body measurement tracking (optional)
  - **Files**: `src/app/(tabs)/progress.tsx`, `src/components/WeightChart.tsx`, `src/components/VolumeChart.tsx`, `src/components/StreakCalendar.tsx`, `src/components/DateRangePicker.tsx`, `src/lib/progressCalculator.ts` (PR detection, 1RM estimation, streak calc), `src/hooks/useProgressData.ts`
  - **Worker**: heavy
  - **Token est:** ~4K
  - **Gate:** M1 (line chart renders, bar chart renders, date range filters, PR annotations visible), D3 (chart-data-contract — U4 consumes `ProgressDataPoint[]` from U3's store, contract matches U0 types)
  - **Verify:** Render line chart with 30 days mock bench press data → switch to bar chart → change date range to 3M → PR annotation visible → streak calendar correct → unit toggle (lbs/kg) from U7 reflected in axis labels
  - **Evidence:** `.omo/workout-tracker/evidence/u4-charts.txt`
  - **Deps:** U0 (scaffold, `ProgressDataPoint` type), U1 (auth session — mockable), U3 (`useWorkoutStore` — mockable with `ProgressDataPoint[]`), U7 (`unitSystem` from `useSettingsStore` — mockable)
  - **NOTE:** U4 can start with mock `ProgressDataPoint[]` arrays before U3 is complete. The contract is frozen in U0. If U3 changes the contract shape, U4 must re-adapt — but the interface is explicit.

### Wave 4 — Offline Sync (1 task, serial, ~5–6 sessions)

- [ ] **u6-offline-sync**: Local SQLite via expo-sqlite, sync queue (pending creates/updates/deletes), conflict resolution (LWW with server timestamp), network detection, sync-on-reconnect, sync status indicator, initial data seed
  - **Files**: `src/lib/db/schema.ts`, `src/lib/db/migrations/`, `src/lib/db/syncQueue.ts`, `src/lib/network.ts`, `src/hooks/useOfflineSync.ts`, `src/stores/useSyncStore.ts`, `src/lib/db/syncAdapter.ts` (implements `syncAdapter` interface from U3's `useWorkoutStore`)
  - **Worker**: heavy (FULL mode — cross-cutting, SQLite schema, sync state machine, conflict resolution, 5-6 sessions)
  - **Token est:** ~5K
  - **Gate:** M1 (offline save → SQLite → sync queue → online → Supabase sync), S1 (dataFlow integrity — no data loss across offline/online transitions, idempotency keys prevent duplicates)
  - **Verify:** Log workout offline → SQLite has entry → sync queue shows 1 pending → go online → workout synced to Supabase → server has data → edit offline → queued → online → updated → delete offline → synced → conflict simulation (two devices) → LWW → network drop mid-sync → exponential backoff retry
  - **Evidence:** `.omo/workout-tracker/evidence/u6-sync-offline.txt`, `.omo/workout-tracker/evidence/u6-sync-conflict.txt`
  - **Deps:** U0 (scaffold, `SyncOperation` type, `syncAdapter` interface), U1 (auth session), U2 (stable `Exercise` type), U3 (stable `Workout`/`Set` types, `useWorkoutStore` facade)
  - **IMPLEMENTATION:** Replace U3's direct Supabase `syncAdapter` with `src/lib/db/syncAdapter.ts` that writes to local SQLite + enqueues sync operations. U3's code does NOT change — only the adapter implementation changes.

### Wave 5 — Integration (1 task, serial, ~2 sessions)

- [ ] **integration-pass**: End-to-end flow validation, all mock interfaces replaced with real implementations, cross-unit contract verification, performance check (FlatList, chart rendering, sync queue), error boundary testing
  - **Files**: `src/app/_layout.tsx` (finalize navigation), integration test scripts
  - **Worker**: medium
  - **Token est:** ~2K
  - **Gate:** M1 (full user journey: register → browse exercises → log workout offline → view charts → go online → sync → notification fires → settings persist), D1 (unit isolation verified), D2 (fan-out schedule validated — no hidden deps emerged)
  - **Verify:** Full E2E walkthrough on both iOS and Android (Expo Go): register → add custom exercise → log workout with 3 exercises offline → view progress charts → enable reminders → go online → verify Supabase has all data → change units → dark mode toggle → export data → kill app → relaunch → all data persisted
  - **Evidence:** `.omo/workout-tracker/evidence/integration-e2e.txt`

## Risk Register (BKIT Gates)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| Unit does not map to user requirement | `M1_spec_match` | HIGH | 8/8 units covered | Feature map audit (Phase 0.5 governance) | Each unit traces to PRD requirement or justified prerequisite |
| U3↔U6 save-path retrofit (U3 saves direct to Supabase, U6 must intercept) | `S1_dataFlow` | **CRITICAL** | Save path routes through facade | `useWorkoutStore` exposes `syncAdapter` interface from day one (Option C). U3 never calls Supabase directly | Code review: zero direct Supabase calls in U3 components |
| U5↔U7 boundary conflict (scheduling UI ownership) | `M1_spec_match` | MED | U5 owns scheduling, U7 owns global prefs | Documented boundary in both unit specs | Code review: no scheduling UI in `settings.tsx` |
| Chart data contract mismatch (U3 output ≠ U4 input) | `D3_chart_data_contract` | HIGH | `ProgressDataPoint` type frozen in U0 | Contract defined in `src/types/progress.ts` before U3 or U4 start | `npx tsc --noEmit` validates type compatibility across units |
| Dependency cycle between units | `D2_fan_out_validity` | MED | 0 cycles in DAG | Topological sort of unit graph per governance §Phase 0.5 | Visual inspection of dependency graph |
| Offline sync data loss during conflict | `S1_dataFlow` | HIGH | 0 data loss, idempotent operations | UUID per operation, LWW with server timestamp, exponential backoff retry (1s→2s→4s→8s→16s→max 60s) | Conflict simulation test: two devices edit same workout → server has one winner → loser logged |
| Performance regression with large exercise library | `P2_memory` | LOW | FlatList renders 200+ exercises without frame drops | SectionList with `getItemLayout`, memoized `ExerciseCard` | Frame budget: <16ms render per frame, no JS thread blocking during scroll |
| Expo managed workflow limitation — native module needed later | — | LOW | Monitored, not mitigated | Documented risk per governance constraints §8. If BLE/Apple Watch required → bare workflow migration | N/A (planning-only gate) |

## Execution Command

```
blackcow-loop "Execute plans/workout-tracker-decomp.md" --completion-promise='All 8 units decomposed with frozen contracts: Exercise, Workout, Set, ProgressDataPoint, AuthState, SyncOperation types in U0. useWorkoutStore syncAdapter facade ready for U6. Chart data contract (U3→U4) and sync adapter (U3→U6) frozen. Each unit independently testable with mock data. No dependency cycles. All PRD requirements (log exercises, progress charts, reminders, offline sync) covered by specific units.' --trust-level=2
```

### Parallelism Guide
- **Wave 1**: 1 worker (U0 scaffold — serial bottleneck)
- **Wave 2**: 4 workers in parallel (U1, U2, U5, U7 — all independent with mocks)
- **Wave 3**: 2 workers in parallel (U3, U4 — U4 can start with mock ProgressDataPoint[])
- **Wave 4**: 1 worker (U6 — serial, depends on stable U2+U3 data models + `syncAdapter` interface)
- **Wave 5**: 1 worker (integration — serial, depends on all units)
- **Total budget**: ~20K tokens / 128K target

### Unit Dependency Graph (DAG)

```
U0 ─────────────────────────────────────────┐
  (Expo scaffold, types, store patterns,     │
   theme context, syncAdapter interface)     │
                                             │
     ┌───────────────────────────────────────┤
     │                                       │
     ▼                                       ▼
U1 (Auth) ──────┐                  U7 (Settings)
     │          │                       │
     │ (token)  │                       │ (unitSystem,
     ▼          │                       │  notificationPrefs,
U2 (Exercise    │                       │  theme context)
 Library)       │                       │
     │          │                       │
     │ (Exercise│                       │
     │  type)   │                       │
     ▼          │                       │
U3 (Workout ────┤                       │
 Logger)        │                       │
     │          │                       │
     ├──────────┤                       │
     │ (Workout │                       │
     │  + Set   │                       │
     │  types)  │                       │
     ▼          ▼                       ▼
U4 (Progress   U6 (Offline Sync) ◄──────┘
 Charts)         (needs stable U2+U3
     │           data models + syncAdapter
     │           interface from U3)
     │
     └── U5 (Reminders) ← independent,
          needs U7 notificationPrefs only
```

### Post-Decomposition Checklist

- [x] Each unit maps to user requirement or justified prerequisite
- [x] No unit boundary conflict (U5↔U7 documented, U3↔U6 resolved via facade)
- [x] No missing requirement coverage (Workout History added to U3 scope)
- [x] No dependency cycles in unit graph
- [x] Each unit has independent test scenario with mock data
- [x] FAN-OUT schedule respects dependency order
- [x] Shared interface contracts defined for all cross-unit dependencies
- [x] U6 risk acknowledged — FULL mode justified
- [x] U3↔U4 chart data contract (`ProgressDataPoint`) frozen in U0
- [x] U3↔U6 sync adapter interface frozen in U0 (`syncAdapter`)
- [x] U5 confirmed independent — no data coupling with logger
- [x] Workout templates documented as post-MVP deferred enhancement
- [x] Tech stack (Expo managed) auto-selected; user may override via governor re-invoke
