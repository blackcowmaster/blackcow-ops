# Governance Decision: pomodoro-remaining-waves

| Field | Value |
|---|---|
| **Task** | Implement ALL remaining waves from the Pomodoro plan — Wave 2 (Core UI), Wave 3 (Task List + Navigation), Wave 4 (Notifications, Dark Mode, Stats, Hardening). Full React Native + Expo SDK 52+ app. |
| **Parent Plan** | `plans/pomodoro-timer-app.md` (849 lines) |
| **Parent Governance** | `pomodoro-wave1-governance.md` (core logic complete) |
| **Governed at** | 2026-07-14T04:00:00Z |
| **Detected Intent** | Feature — greenfield React Native app UI + integration |
| **Context Tags** | `react-native`, `expo`, `typescript`, `expo-router`, `expo-notifications`, `asyncstorage`, `dark-mode` |

---

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | **FULL** | Massive implementation surface: ~30 files across UI components, navigation, notifications, dark mode, stats display, context providers, Expo Router screens, and app scaffolding. User directive: "Full implementation. Don't stop at planning — actually build it." |
| **Trust Level** | **L2** | Large new code surface. Well-specified by existing plan (component tree, props interfaces, state management, notification strategy all documented). But React Native + Expo has platform-specific gotchas. |
| **Bootstrap Lanes** | **5** | Parallel file creation for independent component groups |
| **PDCA Max Cycles** | **5** | Large surface area; some RN-specific issues likely |
| **Adversarial Reviewers** | **3** | M-scale app with auth-free surface |

---

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal — must match plan's component tree + props interfaces |
| M2 test-pass | ✅ | Universal — existing 107 pomodoro tests must still pass |
| M3 regression | ✅ | Universal — Express backend must not break |
| M4 lint | ⚠️ | New source files (ESLint v10.5.0 incompatible — manual style check) |
| M5 dead-code | ❌ | Greenfield — no deletions |
| S1 dataFlow | ✅ | TimerContext → components data flow; task persistence flow |
| S2 auth | ✅ | expo-notifications permission flow |
| S3 injection | ✅ | Task input sanitization; notification content |
| P1 query | ❌ | AsyncStorage only — no DB queries |
| P2 memory | ❌ | No buffer/collection leaks expected |
| P3 latency | ❌ | No p95 targets |

**Active gates: 7/12**

---

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | **O0** |
| **Max Capability** | O4 |
| **Capped?** | O4 → O0 (no device/emulator in sandbox) |
| **Fallback Strategy** | TypeScript compilation + Jest tests for verification |
| **Residual Risk** | Medium — RN visual behavior cannot be verified without device |

---

## Tech Stack (Confirmed)

| Dimension | Decision |
|---|---|
| Framework | React Native + Expo SDK 52+ (managed workflow) |
| Language | TypeScript (strict) |
| Navigation | Expo Router (file-based) |
| State | React Context + useReducer |
| Storage | @react-native-async-storage/async-storage |
| Notifications | expo-notifications |
| UI | React Native core components + StyleSheet |
| Icons | lucide-react-native (tree-shakeable) |
| SVG | react-native-svg (CircularProgress) |

---

## Deliverables

~30 files across 5 directories:
- `pomodoro-app/` — Expo app root (package.json, app.json, tsconfig.json, babel.config.js)
- `pomodoro-app/app/` — Expo Router screens (_layout.tsx, index.tsx, tasks.tsx)
- `pomodoro-app/src/pomodoro/` — Core logic (copied/adapted from Express project)
- `pomodoro-app/src/context/` — TimerContext, TaskContext, ThemeContext
- `pomodoro-app/src/components/` — 12 UI components
- `pomodoro-app/src/screens/` — HomeScreen, TaskListScreen
- `pomodoro-app/src/lib/` — notifications, storage, theme utilities
- `pomodoro-app/src/styles/` — theme tokens, colors

---

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| — | — | **No patterns match React Native / Expo / mobile domain.** | — | — | Clean run |

10 existing patterns scanned. All domains (`tools-mapping`, `cross-reference`, `database`) disjoint from mobile UI. Zero applied.

---

## Verdict

**PROCEED — FULL mode, L2 trust, 7 active gates.** User directive overrides normal governance escalaion. Build all remaining waves directly. Existing plan specifies every component interface, state transition, and integration point. Core logic already tested (107 tests passing).
