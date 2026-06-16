# Governance Decision: rn-task-manager-decomp

| Field | Value |
|---|---|
| **Task** | PRD decomposition: React Native Task Manager — 5-feature mobile app (Auth, Task List, Task Detail, Settings, Offline) |
| **Governed at** | 2026-06-17T00:00:00Z |
| **Detected Intent** | Feature (greenfield mobile app — planning phase, no implementation) |
| **Existing Codebase** | Express/TypeScript backend — NO RELATION to this PRD. Pure greenfield decomposition. |
| **Branch** | `dev` |

---

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | **STANDARD** | Planning-only PRD decomposition. Moderate scope (5 features, 6 units). No code to change. No security emergency. STANDARD provides full gate coverage without over-orchestration. |
| **Trust Level** | **L2** | Human-reviewed PRD. Clear tech stack. Well-understood patterns (FlatList, zustand, react-navigation). No novel algorithms. L2 allows PDCA budget for decomposition refinement. |
| **Bootstrap Lanes** | **3** | Unit 0 (scaffold) is serial; Units 1-4 are parallelizable. 3 lanes matches the FAN-OUT surface. |
| **PDCA Max Cycles** | **2** | Decomposition is a 1-pass exercise. Allow 1 refinement cycle if unit boundaries shift. |
| **Adversarial Reviewers** | **1** | Medium scope — single adversarial reviewer sufficient for decomposition QA. |

---

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal — verify each unit maps to a PRD requirement |
| M2 test-pass | ❌ | No code — deferred to implementation phase |
| M3 regression | ❌ | Greenfield — no existing tests to regress |
| M4 lint | ❌ | No code to lint |
| M5 dead-code | ❌ | No code |
| S1 dataFlow | ✅ | Verify data dependencies between units are sound (shared types, API contract) |
| S2 auth | ❌ | Deferred to Unit 1 implementation |
| S3 injection | ❌ | N/A for planning |
| P1 query | ❌ | N/A for planning |
| P2 memory | ❌ | N/A for planning |
| P3 latency | ❌ | N/A for planning |
| **D1 unit-isolation** | ✅ | Custom gate: verify each unit can be developed/tested independently |
| **D2 fan-out-validity** | ✅ | Custom gate: verify parallelization constraints are correct |

**Gate subset**: M1, S1, D1, D2 — 4 planning gates. All implementation gates deferred.

---

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | **O0** |
| **Max Capability** | O4 (browser/Playwright per capabilities.json) |
| **Browser Available?** | YES — but irrelevant to React Native |
| **Capped?** | O4 → O0 (no RN toolchain — no Metro, no Expo, no iOS Simulator, no Android Emulator) |
| **Fallback Strategy** | Static review only. Unit boundaries validated via dependency graph analysis, not runtime. |
| **Residual Risk** | **LOW** — decomposition is a planning artifact. No runtime behavior to verify. Risk is architectural, not operational. |

---

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| Stage 1 | uncertainty_score < 30 | 3 |
| Stage 2 | 30 ≤ uncertainty < 60 | 5 |
| Stage 3 | uncertainty ≥ 60 | 6 |

*Note: Conservative widening since this is greenfield. Max lanes capped at 6 (one per unit).*

---

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| Unit boundary conflict | Two units claim same responsibility | Re-decompose, flag to user |
| Missing PRD coverage | PRD requirement not covered by any unit | Add unit or merge into existing |
| Scope creep | New unit emerges outside PRD scope | Return to planner, flag |
| Dependency cycle | A → B and B → A in unit graph | Break cycle via shared interface unit |

---

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Relevance | Action |
|---|---|---|---|---|
| — | — | — | — | — |

**Feed rules**: All 10 existing failure patterns (FP-001 through FP-010) target the Express/TypeScript backend — shell scripts, PostgreSQL, tools-mapping. Zero relevance to React Native or mobile development. **No patterns loaded.**

---

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (governor — this doc)** | ~3K |
| **Tokens (plan — unit specs)** | ~5K |
| **Tokens (loop — decomposition pass)** | ~2K |
| **Tokens (QA — gate verification)** | ~3K |
| **Total estimated** | ~13K |
| **Est. cost (flash)** | ~$0.003 |
| **Est. cost (pro)** | ~$0.08 |
| **Est. cost (blended)** | ~$0.04 |
| **Historical ROI** | N/A — no mobile/RN history in loop-roi.jsonl. Closest: `feature` at 0.78 score/token. |
| **Budget utilization** | <1% of STANDARD mode budget |
| **Recommendation** | **PROCEED** — trivial cost for high-value architectural clarity |

---

## Phase 0.5 — Unit Decomposition

### Unit Dependency Graph

```
Unit 0: Project Scaffold ─────────────────────────┐
  (FAST, infrastructure)                           │
                                                   │
     ┌─────────────────────────────────────────────┤
     │                                             │
     ▼                                             ▼
Unit 1: Auth ────────────┐              Unit 4: Settings
  (STANDARD, auth)        │                (FAST, preferences)
     │                    │                     │
     │ (mockable)         │                     │ (no deps)
     ▼                    │                     │
Unit 2: Task List ────────┤                     │
  (STANDARD, ui/list)     │                     │
     │                    │                     │
     ├────────────────────┤                     │
     │ (shared model)     │                     │
     ▼                    ▼                     │
Unit 3: Task Detail      Unit 5: Offline ◄──────┘
  (STANDARD, ui/form)      (FULL, sync)     (needs stable
     │                         │              data model
     │                         │              + net detection)
     └─────────┬───────────────┘
               │
          [shared: Task type, API client, auth token]
```

### Unit Assessments

---

#### Unit 0: Project Scaffold

| Field | Value |
|---|---|
| **Unit ID** | U0 |
| **Summary** | `npx react-native init`, TypeScript config, folder structure, react-navigation skeleton, zustand store setup, shared types (`Task`, `User`, `AuthState`), API client stub |
| **Mode** | **FAST** |
| **Domain Tags** | `infrastructure`, `react-native`, `typescript`, `navigation`, `state` |
| **FAN-OUT** | **NO** — serial prerequisite. All other units depend on scaffold. |
| **Dependencies** | None |
| **Depended on by** | U1, U2, U3, U4, U5 |
| **Independent test** | `npm run ios` / `npm run android` renders navigation shell with placeholder screens |
| **PRD coverage** | Cross-cutting — enables all 5 features |
| **Estimated effort** | XS (1 session) — mechanical, well-documented |

---

#### Unit 1: Auth (Email/Password Login + Token Storage)

| Field | Value |
|---|---|
| **Unit ID** | U1 |
| **Summary** | Login/Register screens, auth zustand store, `expo-secure-store` token persistence, API client with auth header injection, auto-login from stored token |
| **Mode** | **STANDARD** |
| **Domain Tags** | `auth`, `security`, `storage`, `react-native`, `expo`, `zustand` |
| **FAN-OUT** | **YES** — parallel with U2/U3/U4. Mock API responses enable independent development. |
| **Dependencies** | U0 (scaffold, shared types) |
| **Depended on by** | U2, U3, U5 (via auth token) |
| **Independent test** | Mock API: login → token stored → auto-login on relaunch → logout clears token |
| **PRD coverage** | Feature 1 — Auth |
| **Estimated effort** | M (2-3 sessions) — security-sensitive, needs error handling |
| **Risk** | Token storage is security-critical. `expo-secure-store` API is well-known → **LOW risk**. |
| **Note** | `expo-secure-store` requires Expo modules in bare workflow. Verify `expo` package is in U0 scaffold. |

---

#### Unit 2: Task List (FlatList + Pull-to-refresh + Priority Badges)

| Field | Value |
|---|---|
| **Unit ID** | U2 |
| **Summary** | Task list screen, `FlatList` with `RefreshControl`, priority badge component (color-coded: High=red, Medium=yellow, Low=blue), empty state, loading state, error state |
| **Mode** | **STANDARD** |
| **Domain Tags** | `ui`, `list`, `react-native`, `state`, `zustand` |
| **FAN-OUT** | **YES** — parallel with U1, U3, U4. Mock task data + mock auth token. |
| **Dependencies** | U0 (scaffold, shared `Task` type, API client stub), U1 (auth token — mockable) |
| **Depended on by** | U3 (navigation target), U5 (offline task cache) |
| **Independent test** | FlatList renders 20 mock tasks, pull-to-refresh triggers reload, priority badges render correct colors, tap navigates to detail placeholder |
| **PRD coverage** | Feature 2 — Task List |
| **Estimated effort** | M (2-3 sessions) — multiple UI states, pull-to-refresh edge cases |
| **Risk** | FlatList performance with large datasets → **MEDIUM risk**. Mitigate with `getItemLayout`, `keyExtractor`, `windowSize`. |

---

#### Unit 3: Task Detail (Edit Title/Description/Priority, Mark Complete)

| Field | Value |
|---|---|
| **Unit ID** | U3 |
| **Summary** | Task detail screen (read + edit modes), `TextInput` for title/description, priority picker (segmented control or picker), complete toggle (switch or checkbox), save/cancel, optimistic update |
| **Mode** | **STANDARD** |
| **Domain Tags** | `ui`, `form`, `react-native`, `state`, `navigation`, `zustand` |
| **FAN-OUT** | **YES** — parallel with U1, U2, U4. Shares `Task` type with U2. |
| **Dependencies** | U0 (scaffold, shared types), U1 (auth token — mockable), U2 (navigation source — mock with `navigation.navigate`) |
| **Depended on by** | U5 (offline edit queue) |
| **Independent test** | Navigate with mock task → display all fields → edit title → save → verify optimistic update → edit priority → save → toggle complete → verify UI |
| **PRD coverage** | Feature 3 — Task Detail |
| **Estimated effort** | M (2-3 sessions) — form validation, optimistic update rollback |
| **Risk** | Form state management with optimistic updates → **MEDIUM risk**. Mitigate with zustand middleware for rollback. |

---

#### Unit 4: Settings (Dark Mode Toggle + Notification Preferences)

| Field | Value |
|---|---|
| **Unit ID** | U4 |
| **Summary** | Settings screen, dark mode toggle (persisted to AsyncStorage), notification preferences (push enabled/disabled, reminder time), theme context provider wrapping entire app |
| **Mode** | **FAST** |
| **Domain Tags** | `ui`, `preferences`, `theme`, `react-native`, `zustand` |
| **FAN-OUT** | **YES** — most independent unit. Zero API dependencies. Can be built and tested in isolation. |
| **Dependencies** | U0 (scaffold) |
| **Depended on by** | None (theme is additive — other units render correctly with or without dark mode) |
| **Independent test** | Toggle dark mode → all screens re-render with dark theme → persist → kill app → relaunch → dark mode preserved → toggle notifications → preference persisted |
| **PRD coverage** | Feature 4 — Settings |
| **Estimated effort** | XS (1 session) — simple toggles, well-understood theming pattern |
| **Risk** | Theme context needs to wrap navigation container → **LOW risk**. Standard React Context pattern. |

---

#### Unit 5: Offline (Cache Tasks Locally + Sync When Online)

| Field | Value |
|---|---|
| **Unit ID** | U5 |
| **Summary** | Offline cache service (AsyncStorage), network listener (`@react-native-community/netinfo`), sync queue (pending creates/updates/deletes), conflict resolution strategy (last-write-wins with timestamp), sync-on-reconnect trigger |
| **Mode** | **FULL** |
| **Domain Tags** | `storage`, `network`, `sync`, `react-native`, `offline`, `zustand` |
| **FAN-OUT** | **YES** — but LATE. Should start after U2+U3 data models are stable. Parallel with U4. |
| **Dependencies** | U0 (scaffold), U1 (auth token), U2+U3 (stable `Task` type, API contract), U4 (optional — netinfo for connectivity) |
| **Depended on by** | None |
| **Independent test** | Create task offline → stored in AsyncStorage → go online → task synced to API → edit task offline → queued → go online → update synced → delete offline → synced → verify conflict: edit same task on two devices → last-write-wins |
| **PRD coverage** | Feature 5 — Offline |
| **Estimated effort** | L (4-5 sessions) — cross-cutting, multiple edge cases, conflict resolution |
| **Risk** | **HIGH** — sync is inherently complex. Race conditions, partial sync failures, conflict resolution, storage limits. Mitigate with: strict queue ordering, idempotency keys, exponential backoff for retries, AsyncStorage size monitoring. |
| **Mode justification** | FULL mode selected (not STANDARD) because: cross-cutting concern touching auth, data model, network, and storage; complex state machine (online/offline/syncing/error); conflict resolution strategy requires design review. |

---

### FAN-OUT Execution Schedule

```
Phase 1 (Serial):     U0 ────────── [scaffold complete]
                      │
Phase 2 (Parallel):   ├── U1 ─── [auth complete]
                      ├── U2 ─── [task list complete]
                      ├── U3 ─── [task detail complete]
                      └── U4 ─── [settings complete]
                      │
Phase 3 (Late):       └── U5 ─── [offline complete]
                           │
Phase 4 (Integrate):       └── End-to-end integration pass
```

**Parallelism**: Phase 2 achieves 4× parallelism. U1/U2/U3/U4 can all be developed simultaneously by separate developers/agents with mock interfaces.

---

## Integration Contract (Cross-Unit)

### Shared Artifacts (owned by U0, consumed by all)

| Artifact | Location | Consumers |
|---|---|---|
| `Task` type | `src/types/task.ts` | U2, U3, U5 |
| `User` / `AuthState` types | `src/types/auth.ts` | U1, U5 |
| API client (`fetch` wrapper) | `src/api/client.ts` | U1, U2, U3, U5 |
| Auth token header injection | `src/api/client.ts` | U1 writes, U2/U3/U5 read |
| Navigation type definitions | `src/navigation/types.ts` | U2, U3, U4 |
| Theme context | `src/theme/ThemeContext.tsx` | U2, U3, U4 |
| zustand store patterns | `src/stores/` | All |

### Unit Contracts

| Producer | Exports | Consumer | Interface |
|---|---|---|---|
| U1 | `useAuthStore()`, `login()`, `logout()`, `token` | U2, U3, U5 | zustand store |
| U2 | `TaskCard`, `useTaskListStore()` | U3 | Component + store |
| U4 | `ThemeProvider`, `useTheme()` | U2, U3 | React Context |
| U5 | `useOfflineSync()`, `offlineQueue` | U2, U3 | Hook + store |

---

## Post-Decomposition Self-Audit

After units are decomposed into separate plans:

- [ ] Each unit maps to exactly one PRD feature (or cross-cutting concern)
- [ ] No unit boundary conflict (two units claiming same responsibility)
- [ ] No missing PRD coverage
- [ ] No dependency cycles in unit graph
- [ ] Each unit has an independent test scenario
- [ ] FAN-OUT schedule respects dependency order
- [ ] Shared interface contracts defined for all cross-unit dependencies
- [ ] U5 (Offline) risk acknowledged — FULL mode justified
- [ ] `expo-secure-store` dependency noted for U0 scaffold

---

## Constraints

1. **Plan only** — no implementation, no code edits.
2. Produce **unit specifications**, not implementation.
3. Each unit must be independently testable.
4. Shared type definitions belong to U0 (scaffold), not scattered across units.
5. Mock interfaces must be sufficient for independent unit development.
