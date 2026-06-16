# Governance Decision: workout-tracker-decomp

| Field | Value |
|---|---|
| **Task** | PRD decomposition: Mobile Workout Tracker — log exercises, progress charts, reminder notifications, offline-first with sync. 7-feature mobile app (Auth, Exercise Library, Workout Logger, Progress Charts, Reminders, Offline Sync, Settings) |
| **Governed at** | 2026-06-28T00:00:00Z |
| **Tech Stack** | **Expo (React Native managed workflow)** + TypeScript + expo-router + expo-sqlite + expo-notifications + victory-native + zustand + Supabase — auto-selected (user deferred: "No tech stack specified — you need to figure out what to use") |
| **Detected Intent** | Feature (greenfield mobile app — planning phase, no implementation) |
| **Existing Codebase** | Express/TypeScript backend (task manager API) — NO RELATION to this PRD. Pure greenfield decomposition. |
| **Branch** | `dev` |

---

## Phase 0.0a — Tech Stack Inference

### Signals Detected

| Signal | Source | Suggestion |
|---|---|---|
| Mobile app, iOS + Android | "mobile app for tracking daily workouts" | React Native |
| Push/local notifications needed | "reminder notifications" | Expo managed (expo-notifications) |
| Offline-first with sync | "work offline and sync when online" | expo-sqlite + sync queue |
| Charts/visualization | "see progress charts" | victory-native (Expo-compatible) |
| No custom native modules required | No camera, BLE, or filesystem deps mentioned | Expo managed workflow |
| Relational data (exercises, workouts, sets, reps) | Workout domain model inherently relational | SQLite (expo-sqlite) |
| Auth needed | Implicit — user-specific data | Supabase Auth (email/password + social) |
| Real-time sync not required | "sync when online" (not real-time) | REST API + sync queue sufficient |

### Stack Decision: Expo Managed Workflow

**Why Expo over bare React Native:**
- The previous `rn-task-manager-decomp` used bare workflow and required 10 tasks just for navigation + native linking setup (Podfile, MainActivity, AndroidManifest, CocoaPods)
- Expo managed workflow eliminates ALL of that: zero native config for navigation (expo-router), notifications (expo-notifications), SQLite (expo-sqlite), secure storage (expo-secure-store)
- `expo-sqlite` is now a first-party Expo module (SDK 52+) with full TypeScript support
- `expo-notifications` handles scheduled local notifications without APNs/FCM setup
- `expo-router` gives file-based routing with deep linking for free
- OTA updates via EAS — critical for rapid iteration on a new app

**Why victory-native over react-native-chart-kit:**
- victory-native has better TypeScript support and active maintenance
- Composable chart primitives (line, bar, area) for workout progression tracking
- Works with both Expo and bare workflow
- `react-native-chart-kit` has had spotty maintenance and fewer chart types

**Why Supabase over Firebase or custom backend:**
- PostgreSQL gives proper relational queries for workout data (exercises → workouts → sets)
- Row-Level Security (RLS) for multi-tenant auth
- Built-in Auth with email/password and social providers
- REST API auto-generated from database schema — zero backend code for CRUD
- Real-time subscriptions available if needed later (live workout sharing)
- The existing Express backend could serve as a BFF if needed, but Supabase eliminates backend development entirely

**Auto-selection note**: User deferred stack choice ("you need to figure out what to use"). Per Phase 0.0b rule #4, first suggestion auto-selected. User may override by re-invoking governor with a different stack preference.

### Context Tags

```
["react-native", "expo", "typescript", "expo-sqlite", "expo-notifications", "victory-native", "zustand", "supabase", "mobile", "offline-first"]
```

---

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | **STANDARD** | Planning-only PRD decomposition. Moderate scope (7 features, 8 units). No code to change. No security emergency. STANDARD provides full gate coverage without over-orchestration. |
| **Trust Level** | **L2** | Human-described requirements. Well-understood patterns (FlatList, zustand, expo-router, victory-native, Supabase). No novel algorithms. L2 allows PDCA budget for decomposition refinement. |
| **Bootstrap Lanes** | **3** | Unit 0 (scaffold) is serial; Units 1-6 are highly parallelizable. 3 lanes matches the FAN-OUT surface for Phase 2. |
| **PDCA Max Cycles** | **2** | Decomposition is a 1-pass exercise. Allow 1 refinement cycle if unit boundaries shift or missing feature coverage detected. |
| **Adversarial Reviewers** | **1** | Medium-large scope (7 features) — single adversarial reviewer sufficient for decomposition QA. |

---

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal — verify each unit maps to a user requirement (log exercises, progress charts, reminders, offline sync) |
| M2 test-pass | ❌ | No code — deferred to implementation phase |
| M3 regression | ❌ | Greenfield — no existing tests to regress |
| M4 lint | ❌ | No code to lint |
| M5 dead-code | ❌ | No code |
| S1 dataFlow | ✅ | Verify data dependencies between units are sound (Exercise → Workout → Set → Progress, sync queue contract) |
| S2 auth | ❌ | Deferred to Unit 1 implementation |
| S3 injection | ❌ | N/A for planning |
| P1 query | ❌ | N/A for planning |
| P2 memory | ❌ | N/A for planning |
| P3 latency | ❌ | N/A for planning |
| **D1 unit-isolation** | ✅ | Custom gate: verify each unit can be developed/tested independently with mock data |
| **D2 fan-out-validity** | ✅ | Custom gate: verify parallelization constraints are correct for 8-unit decomposition |
| **D3 chart-data-contract** | ✅ | Custom gate: verify Progress Charts unit defines a clear data contract that Workout Logger can fulfill |

**Gate subset**: M1, S1, D1, D2, D3 — 5 planning gates. All implementation gates deferred.

---

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | **O0** |
| **Max Capability** | O4 (browser/Playwright per capabilities.json) |
| **Browser Available?** | YES — but irrelevant to React Native/Expo |
| **Capped?** | O4 → O0 (no Expo toolchain — no Metro bundler, no Expo Go, no iOS Simulator, no Android Emulator, no `npx expo start`) |
| **Fallback Strategy** | Static review only. Unit boundaries validated via dependency graph analysis, not runtime. Data contracts validated via TypeScript type-checking (can run `npx tsc --noEmit` on type definitions). |
| **Residual Risk** | **LOW** — decomposition is a planning artifact. No runtime behavior to verify. Risk is architectural, not operational. |

---

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| Stage 1 | uncertainty_score < 30 | 3 |
| Stage 2 | 30 ≤ uncertainty < 60 | 5 |
| Stage 3 | uncertainty ≥ 60 | 8 |

*Note: Conservative widening since this is greenfield. Max lanes capped at 8 (one per unit). Wider than the task-manager decomposition (6 units) due to more features (7 vs 5).*

---

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| Unit boundary conflict | Two units claim same responsibility (e.g., both U3 and U4 claim chart data preparation) | Re-decompose, flag to user |
| Missing requirement coverage | User requirement not covered by any unit | Add unit or merge into existing |
| Scope creep | New unit emerges outside described scope (e.g., "social sharing", "Apple Watch integration") | Return to planner, flag |
| Dependency cycle | A → B and B → A in unit graph | Break cycle via shared interface unit or data contract |
| Chart data contract ambiguity | U4 (Charts) and U3 (Logger) have incompatible data shapes | Freeze contract in U0 shared types, escalate to user if tradeoff needed |

---

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Relevance | Action |
|---|---|---|---|---|
| — | — | — | — | — |

**Feed rules**: All 10 existing failure patterns (FP-001 through FP-010) target the Express/TypeScript backend and Reasonix tooling — shell scripts, PostgreSQL keyset pagination, tools-mapping, cross-reference gaps. **Zero relevance to React Native, Expo, or mobile development.** No patterns loaded. New patterns will be recorded if discovered during implementation.

---

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (governor — this doc)** | ~5K |
| **Tokens (plan — unit specs for 8 units)** | ~8K |
| **Tokens (loop — decomposition pass)** | ~3K |
| **Tokens (QA — gate verification)** | ~4K |
| **Total estimated** | ~20K |
| **Est. cost (flash)** | ~$0.005 |
| **Est. cost (pro)** | ~$0.12 |
| **Est. cost (blended)** | ~$0.06 |
| **Historical ROI** | N/A — no mobile/RN history in loop-roi.jsonl. Closest: `feature` at 0.78 score/token. |
| **Budget utilization** | <2% of STANDARD mode budget |
| **Recommendation** | **PROCEED** — trivial cost for high-value architectural clarity on a 7-feature mobile app. |

---

## Phase 0.5 — Unit Decomposition

### Feature Map (User Requirements → Units)

| User Requirement | Unit | Unit ID |
|---|---|---|
| Log exercises | Workout Logger | U3 |
| See progress charts | Progress Charts | U4 |
| Get reminder notifications | Reminders | U5 |
| Work offline | Offline Sync | U6 |
| Sync when online | Offline Sync | U6 |
| (implied) User accounts | Auth | U1 |
| (implied) Exercise library | Exercise Library | U2 |
| (implied) App preferences | Settings | U7 |

### Unit Dependency Graph

```
Unit 0: Project Scaffold ────────────────────────────────────────┐
  (FAST, infrastructure: Expo + TypeScript + expo-router +        │
   zustand + shared types)                                        │
                                                                  │
     ┌────────────────────────────────────────────────────────────┤
     │                                                            │
     ▼                                                            ▼
Unit 1: Auth ────────────┐                            Unit 7: Settings
  (STANDARD, supabase)    │                              (FAST, preferences)
     │                    │                                  │
     │ (token via         │                                  │ (no data deps,
     │  supabase-js)      │                                  │  consumes theme)
     ▼                    │                                  │
Unit 2: Exercise Library  │                                  │
  (STANDARD, ui/list)     │                                  │
     │                    │                                  │
     │ (Exercise type)    │                                  │
     ▼                    │                                  │
Unit 3: Workout Logger ───┤                                  │
  (STANDARD, ui/form)     │                                  │
     │                    │                                  │
     ├────────────────────┤                                  │
     │ (Workout + Set     │                                  │
     │  types)            │                                  │
     ▼                    ▼                                  │
Unit 4: Progress Charts  Unit 6: Offline Sync ◄─────────────┘
  (STANDARD, ui/charts)    (FULL, sync)        (needs stable
     │                         │                data model + net
     │                         │                detection)
     │                         │
     └─────────┬───────────────┘
               │
          [shared: Exercise, Workout, Set, ProgressDataPoint types;
           Supabase client; auth session]
```

### Unit 5: Reminders — Special Position

```
Unit 5: Reminders ◄── depends on: U0 (scaffold), U7 (notification prefs)
  (STANDARD, expo-notifications)     │
     │                                │
     └── NO dependency on U3/U4 ─────┘
         (Reminders are scheduled independently
          of actual workout logging)
```

---

### Unit Assessments

---

#### Unit 0: Project Scaffold

| Field | Value |
|---|---|
| **Unit ID** | U0 |
| **Summary** | `npx create-expo-app` with TypeScript template, expo-router setup (file-based routing), zustand store patterns, shared types (`Exercise`, `Workout`, `Set`, `ProgressDataPoint`, `User`, `AuthState`), Supabase client initialization, theme context, folder structure (`src/app/`, `src/components/`, `src/stores/`, `src/types/`, `src/lib/`, `src/hooks/`) |
| **Mode** | **FAST** |
| **Domain Tags** | `infrastructure`, `expo`, `react-native`, `typescript`, `expo-router`, `zustand`, `supabase` |
| **FAN-OUT** | **NO** — serial prerequisite. All other units depend on scaffold. |
| **Dependencies** | None |
| **Depended on by** | U1, U2, U3, U4, U5, U6, U7 |
| **Independent test** | `npx expo start` renders navigation shell with placeholder screens on Expo Go (iOS + Android) |
| **PRD coverage** | Cross-cutting — enables all 7 features |
| **Estimated effort** | XS (1 session) — mechanical, well-documented. `create-expo-app` does 80% of the work. |
| **Key difference from bare RN scaffold** | No Podfile, no MainActivity, no AndroidManifest edits, no CocoaPods. Expo handles all native config. |

---

#### Unit 1: Auth (Email/Password + Social Login via Supabase)

| Field | Value |
|---|---|
| **Unit ID** | U1 |
| **Summary** | Login/Register screens, Supabase Auth integration (`@supabase/supabase-js`), `expo-secure-store` for session token persistence, auth zustand store (`useAuthStore`), auto-login from stored session, logout, password reset flow, optional: Google/Apple social login |
| **Mode** | **STANDARD** |
| **Domain Tags** | `auth`, `security`, `storage`, `expo`, `supabase`, `zustand`, `expo-secure-store` |
| **FAN-OUT** | **YES** — parallel with U2, U3, U4, U5, U7. Mock Supabase client enables independent development. |
| **Dependencies** | U0 (scaffold, shared `User`/`AuthState` types, Supabase client stub) |
| **Depended on by** | U2, U3, U4, U6 (via auth session for API calls) |
| **Independent test** | Mock Supabase: register → session stored → auto-login on relaunch → logout clears session → password reset email triggered |
| **PRD coverage** | Implied — User accounts |
| **Estimated effort** | M (2-3 sessions) — security-sensitive, multiple auth flows (login, register, reset, social) |
| **Risk** | Session persistence is security-critical. `expo-secure-store` API is well-known → **LOW risk**. Supabase Auth is battle-tested. |

---

#### Unit 2: Exercise Library (Browse + Search + Custom Exercises)

| Field | Value |
|---|---|
| **Unit ID** | U2 |
| **Summary** | Exercise list screen with category filters (Chest, Back, Legs, Shoulders, Arms, Core, Cardio), search bar with debounced text input, exercise detail card (name, muscle group, equipment, instructions), "Add Custom Exercise" flow (name, category, notes), FlatList with section list by category |
| **Mode** | **STANDARD** |
| **Domain Tags** | `ui`, `list`, `expo`, `react-native`, `search`, `zustand` |
| **FAN-OUT** | **YES** — parallel with U1, U3, U4, U5, U7. Mock exercise data enables independent development. |
| **Dependencies** | U0 (scaffold, shared `Exercise` type, Supabase client), U1 (auth session — mockable) |
| **Depended on by** | U3 (exercise selection for workout logging) |
| **Independent test** | FlatList renders 50 exercises across categories, search filters by name/muscle, tap category filters list, add custom exercise → persists to store, empty state when no results |
| **PRD coverage** | Implied — Exercise library (prerequisite for "log exercises") |
| **Estimated effort** | M (2-3 sessions) — search debouncing, category filtering, section list performance |
| **Risk** | Large exercise library (100+ exercises) needs performant section list → **LOW risk**. Expo's FlatList/SectionList handles this well with `getItemLayout`. |

---

#### Unit 3: Workout Logger (Log Sets, Reps, Weight, Duration)

| Field | Value |
|---|---|
| **Unit ID** | U3 |
| **Summary** | Workout session screen: select exercises from library (U2), log sets (weight × reps × RPE), add/remove sets dynamically, rest timer between sets, workout duration tracker, notes field, save workout (creates `Workout` with `Set[]`), edit past workouts, swipe-to-delete set, plate calculator (optional) |
| **Mode** | **STANDARD** |
| **Domain Tags** | `ui`, `form`, `expo`, `react-native`, `zustand`, `timer` |
| **FAN-OUT** | **YES** — parallel with U1, U2, U5, U7. Mock exercise data + mock save. |
| **Dependencies** | U0 (scaffold, shared `Workout`/`Set` types), U1 (auth session — mockable), U2 (exercise selection — mockable with stub exercise list) |
| **Depended on by** | U4 (progress data source), U6 (offline workout queue) |
| **Independent test** | Select exercise → add 3 sets with weight/reps → rest timer counts down → save workout → workout appears in history → edit workout → add/remove sets → delete workout |
| **PRD coverage** | "log exercises" — primary user requirement |
| **Estimated effort** | L (3-4 sessions) — complex form with dynamic set management, timer logic, optimistic updates |
| **Risk** | **MEDIUM** — Dynamic form (variable number of sets) with real-time timer. Mitigate with: zustand for local form state (not React state), `setInterval` cleanup on unmount, optimistic save with rollback. |

---

#### Unit 4: Progress Charts (Weight Progression, Volume, Streaks)

| Field | Value |
|---|---|
| **Unit ID** | U4 |
| **Summary** | Progress dashboard: line chart for weight progression per exercise (1RM estimate or max weight over time), bar chart for total volume per workout (sets × reps × weight), streak calendar (days worked out this month), body measurement tracking (optional: weight, body fat %), date range picker (1W, 1M, 3M, 6M, 1Y, All), chart annotations for PRs (personal records) |
| **Mode** | **STANDARD** |
| **Domain Tags** | `ui`, `charts`, `expo`, `react-native`, `victory-native`, `data-visualization` |
| **FAN-OUT** | **YES** — parallel with U1, U2, U5, U7. Can be built with mock progress data. |
| **Dependencies** | U0 (scaffold, shared `ProgressDataPoint` type), U1 (auth session — mockable), U3 (workout data source — mockable) |
| **Depended on by** | None (read-only consumer) |
| **Independent test** | Render line chart with 30 days of mock bench press data → Y-axis shows weight, X-axis shows dates → switch to bar chart (volume) → change date range to 3M → PR annotation visible → streak calendar shows correct days |
| **PRD coverage** | "see progress charts" — primary user requirement |
| **Estimated effort** | L (3-4 sessions) — multiple chart types, date range filtering, PR detection algorithm, responsive chart sizing |
| **Risk** | **MEDIUM** — victory-native has a learning curve. SVG rendering performance on Android with large datasets. Mitigate with: data aggregation on query (not render), `victory-native` v41+ (Skia renderer for GPU-accelerated charts), limit data points to ~100 per chart. |

---

#### Unit 5: Reminders (Scheduled Local Notifications)

| Field | Value |
|---|---|
| **Unit ID** | U5 |
| **Summary** | Reminder configuration screen: toggle workout reminders on/off, select days of week (Mon-Sun), set reminder time per day, multiple reminder slots per day (e.g., morning + evening), notification channel setup (Android), `expo-notifications` scheduling API (`scheduleNotificationAsync` with `DailyTriggerInput`), notification tap → deep link to workout logger, "Rest Day" skip logic, Snooze function |
| **Mode** | **STANDARD** |
| **Domain Tags** | `notifications`, `expo`, `react-native`, `expo-notifications`, `scheduling`, `deep-linking` |
| **FAN-OUT** | **YES** — independent unit. Zero data dependencies on other feature units. |
| **Dependencies** | U0 (scaffold), U7 (notification preferences — mockable) |
| **Depended on by** | None |
| **Independent test** | Enable reminders → select Mon/Wed/Fri at 7:00 AM → verify 3 scheduled notifications → tap notification → app opens to workout logger → disable reminders → verify all cancelled → snooze → notification fires after delay |
| **PRD coverage** | "get reminder notifications" — primary user requirement |
| **Estimated effort** | M (2-3 sessions) — notification scheduling is straightforward but requires careful testing of trigger accuracy and deep linking |
| **Risk** | **MEDIUM** — Notification scheduling differences between iOS and Android. iOS limits to 64 scheduled notifications; Android requires notification channels. Mitigate with: `expo-notifications` abstracts platform differences, `DailyTriggerInput` for recurring, test on both platforms. |

---

#### Unit 6: Offline Sync (SQLite Local Cache + Supabase Sync)

| Field | Value |
|---|---|
| **Unit ID** | U6 |
| **Summary** | Local SQLite database via `expo-sqlite` (exercises, workouts, sets, sync_queue tables), network listener (`expo-network` / `@react-native-community/netinfo`), sync queue (pending creates/updates/deletes as JSON operations), conflict resolution (last-write-wins with server timestamp), sync-on-reconnect trigger, sync status indicator (synced / pending / error), background sync (optional — Expo TaskManager), initial data seed (preloaded exercise library) |
| **Mode** | **FULL** |
| **Domain Tags** | `storage`, `network`, `sync`, `expo`, `react-native`, `expo-sqlite`, `offline`, `supabase` |
| **FAN-OUT** | **YES** — but LATE. Should start after U2+U3 data models are stable. |
| **Dependencies** | U0 (scaffold), U1 (auth session), U2 (stable `Exercise` type), U3 (stable `Workout`/`Set` types + API contract) |
| **Depended on by** | None (wraps U2+U3 data layer) |
| **Independent test** | Log workout offline → stored in SQLite → sync queue has 1 pending → go online → workout synced to Supabase → verify server has data → edit workout offline → queued → go online → update synced → delete offline → synced → simulate conflict: edit same workout on two devices → last-write-wins → network drop mid-sync → retry with exponential backoff |
| **PRD coverage** | "work offline and sync when online" — primary user requirement |
| **Estimated effort** | XL (5-6 sessions) — cross-cutting, SQLite schema design, sync state machine, conflict resolution, error recovery |
| **Risk** | **HIGH** — Sync is inherently complex. Race conditions, partial sync failures, conflict resolution, storage limits, SQLite migration on schema change. Mitigate with: strict queue ordering (FIFO), idempotency keys (UUID per operation), exponential backoff (1s, 2s, 4s, 8s, 16s, max 60s), conflict strategy documented in plan, `expo-sqlite` migrations via version table, preloaded exercise library as seed data. |
| **Mode justification** | FULL mode selected (not STANDARD) because: cross-cutting concern touching auth, data model, network, and storage; complex state machine (online/offline/syncing/error/conflict); SQLite schema design requires review; conflict resolution strategy requires design review; highest risk unit in the app. |

---

#### Unit 7: Settings (Units, Theme, Notification Prefs, Data Export)

| Field | Value |
|---|---|
| **Unit ID** | U7 |
| **Summary** | Settings screen: unit system toggle (lbs/kg), dark mode toggle (persisted to AsyncStorage/expo-sqlite), theme context provider wrapping entire app, notification preferences (sound, vibration, reminder time defaults consumed by U5), data export (JSON/CSV of workout history), account management (change email, delete account via Supabase), app version/info |
| **Mode** | **FAST** |
| **Domain Tags** | `ui`, `preferences`, `theme`, `expo`, `react-native`, `zustand`, `export` |
| **FAN-OUT** | **YES** — most independent unit. Zero API dependencies for core functionality. |
| **Dependencies** | U0 (scaffold, theme context) |
| **Depended on by** | U5 (notification preferences), U4 (unit system for chart labels), U3 (unit system for weight input) |
| **Independent test** | Toggle lbs→kg → verify display, toggle dark mode → all screens re-render with dark theme → persist → kill app → relaunch → prefs preserved → export data → JSON file contains all workouts → delete account → session cleared |
| **PRD coverage** | Implied — App preferences |
| **Estimated effort** | XS (1 session) — simple toggles, well-understood theming pattern, data export is straightforward JSON serialization |
| **Risk** | **LOW** — Standard preferences pattern. Theme context needs to wrap navigation container. Data export may be large for power users (years of data). |

---

### FAN-OUT Execution Schedule

```
Phase 1 (Serial):     U0 ────────── [Expo scaffold complete]
                      │
Phase 2 (Parallel):   ├── U1 ─── [Auth complete]
                      ├── U2 ─── [Exercise Library complete]
                      ├── U5 ─── [Reminders complete]
                      └── U7 ─── [Settings complete]
                      │
Phase 3 (Parallel):   ├── U3 ─── [Workout Logger complete]  ← depends on U2
                      └── U4 ─── [Progress Charts complete]  ← depends on U3 (data contract)
                      │
Phase 4 (Late):       └── U6 ─── [Offline Sync complete]     ← depends on U2+U3 stable
                           │
Phase 5 (Integrate):       └── End-to-end integration pass
```

**Parallelism**: 
- Phase 2 achieves 4× parallelism (U1, U2, U5, U7 all independent)
- Phase 3 achieves 2× parallelism (U3, U4 — U4 can start with mock data before U3 completes)
- Phase 4 is serial (U6 must wait for stable data models)

---

### Integration Contract (Cross-Unit)

#### Shared Artifacts (owned by U0, consumed by all)

| Artifact | Location | Consumers |
|---|---|---|
| `Exercise` type | `src/types/exercise.ts` | U2, U3, U4, U6 |
| `Workout` type | `src/types/workout.ts` | U3, U4, U6 |
| `Set` type | `src/types/set.ts` | U3, U4, U6 |
| `ProgressDataPoint` type | `src/types/progress.ts` | U4 |
| `User` / `AuthState` types | `src/types/auth.ts` | U1, U6 |
| `SyncOperation` type | `src/types/sync.ts` | U6 |
| Supabase client (`createClient`) | `src/lib/supabase.ts` | U1, U2, U3, U4, U6 |
| expo-router navigation types | `src/app/` (file-based, automatic) | All |
| Theme context | `src/theme/ThemeContext.tsx` | U2, U3, U4, U7 |
| zustand store patterns | `src/stores/` | All |

#### Unit Contracts

| Producer | Exports | Consumer | Interface |
|---|---|---|---|
| U1 | `useAuthStore()`, `session`, `signIn()`, `signUp()`, `signOut()` | U2, U3, U4, U6 | zustand store |
| U2 | `useExerciseStore()`, `ExerciseCard`, `ExerciseSelect` | U3 | Store + component |
| U3 | `useWorkoutStore()`, `WorkoutCard`, `workoutHistory` | U4, U6 | Store + data |
| U7 | `useSettingsStore()`, `ThemeProvider`, `unitSystem`, `notificationPrefs` | U3, U4, U5 | zustand store + context |
| U6 | `useOfflineSync()`, `syncStatus`, `pendingCount` | U2, U3 | Hook |

#### Chart Data Contract (U3 → U4)

```typescript
// Defined in U0: src/types/progress.ts
interface ProgressDataPoint {
  date: string;          // ISO-8601 date
  exerciseId: string;
  exerciseName: string;
  maxWeight: number;     // heaviest set that day
  totalVolume: number;   // sum(sets × reps × weight)
  setCount: number;
  workoutDuration: number; // minutes
  estimated1RM: number;  // Epley formula
}

// U3 produces: ProgressDataPoint[]
// U4 consumes: ProgressDataPoint[] → victory-native charts
```

---

## Post-Decomposition Self-Audit

After units are decomposed into separate plans:

- [ ] Each unit maps to at least one user requirement (or implied prerequisite)
- [ ] No unit boundary conflict (two units claiming same responsibility)
- [ ] No missing requirement coverage (log exercises, progress charts, reminders, offline sync all covered)
- [ ] No dependency cycles in unit graph
- [ ] Each unit has an independent test scenario with mock data
- [ ] FAN-OUT schedule respects dependency order (U6 last, U0 first)
- [ ] Shared interface contracts defined for all cross-unit dependencies
- [ ] U6 (Offline Sync) risk acknowledged — FULL mode justified
- [ ] U4 (Progress Charts) data contract defined in U0 shared types
- [ ] Unit 5 (Reminders) confirmed independent — no data coupling with logger
- [ ] Tech stack (Expo managed) confirmed as auto-selected or user-overridden
- [ ] expo-sqlite, expo-notifications, expo-secure-store dependencies noted for U0 scaffold
- [ ] Supabase project setup prerequisite noted (separate from app code)

---

## Constraints

1. **Plan only** — no implementation, no code edits.
2. Produce **unit specifications**, not implementation.
3. Each unit must be independently testable with mock data.
4. Shared type definitions belong to U0 (scaffold), not scattered across units.
5. Mock interfaces must be sufficient for independent unit development.
6. Chart data contract (U3→U4) must be finalized in U0 before either unit starts implementation.
7. Expo managed workflow trades native module flexibility for zero-config setup — if requirements later demand native modules (BLE heart rate monitors, Apple Watch), a migration to bare workflow may be needed. This risk is documented but not addressed in planning.
