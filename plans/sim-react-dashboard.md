# Plan: React Dashboard Widget Component

| Field | Value |
|---|---|
| **Slug** | `sim-react-dashboard` |
| **Created** | 2026-06-15 |
| **Class** | **M** (single component, cross-cutting: fetch, state, responsive, props API) |
| **Explore lanes** | 5 research lanes dispatched, all returned |
| **Adversarial reviews** | Greenfield — research-grounded, no adversarial panel needed |
| **Budget** | ~45K tokens used / 115K effective |
| **Intent** | Feature |

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | 대시보드에서 반복적으로 사용되는 데이터 위젯의 일관된 UI/UX 패턴을 단일 컴포넌트로 표준화하여 개발 속도 향상 및 사용자 경험 통일 |
| **WHO** | 대시보드를 사용하는 운영자/분석가 (데스크톱 + 태블릿 + 모바일) |
| **WHAT** | `DashboardWidget` React 컴포넌트 — props 기반 설정, API 데이터 페칭, 로딩/에러/빈 상태 처리, 반응형 레이아웃 |
| **RISK** | 신규 컴포넌트이므로 기존 기능 회귀 없음. 실패 시 대시보드 UI 일관성 저하 |
| **SUCCESS** | matchRate ≥ 90% (props spec vs 구현), test pass=100%, lint=0warn, coverage ≥ 85%, p95 render < 200ms (widget 단독) |
| **SCOPE** | **포함**: `DashboardWidget` 컴포넌트, props 타입, 상태 머신, 데이터 페칭 훅, 로딩/에러/빈 상태 UI, 반응형 스타일, 단위/통합 테스트. **제외**: 대시보드 레이아웃 엔진(react-grid-layout), 인증/인가, 백엔드 API 구현 |

## Summary

`DashboardWidget` is a single, configurable React component that encapsulates the full data-display lifecycle for dashboard panels. It accepts a strongly-typed props interface (including a `queryConfig` for TanStack Query), manages a discriminated-union state machine (`idle → loading → success | error | empty`), and renders appropriate sub-views for each state. The widget chrome (header, actions, menu) follows Grafana's `PanelChrome` discriminated-union pattern, while the body content uses render props for consumer flexibility. Responsive behavior is handled via CSS Grid `auto-fit` on the outer dashboard and container queries within the widget. Zustand provides scoped UI state (collapse, local filters); TanStack Query handles server-state caching, polling, and invalidation.

## Architecture Options

### Option A — Minimal (useEffect + fetch, single useState)

- **접근법**: `useEffect` + `fetch` 로 데이터 로딩, `useState<{data, loading, error}>` 단일 객체로 상태 관리, 인라인 스타일로 반응형 처리
- **장점**: 의존성 제로, 코드 50줄 이내, 학습 곡선 없음
- **단점**: 캐시 없음, 중복 요청, refetch 로직 수동 구현, 타입 안전성 낮음, 위젯 8개 이상 시 성능 저하
- **적합**: 프로토타입, 단일 위젯 PoC
- **예상 파일 수**: 1개

### Option B — Clean (TanStack Query + Zustand + Container Queries + Storybook)

- **접근법**: TanStack Query v5로 서버 상태, Zustand Context-scoped store로 UI 상태, discriminated union 상태 머신, container queries로 위젯 내부 반응형, Storybook으로 시각적 테스트
- **장점**: 최고 수준의 타입 안전성, 캐시/폴링/재시도 내장, 위젯 N개 확장 가능, 컴파일 타임에 상태 처리 강제
- **단점**: 의존성 3개 추가, 러닝 커브 존재, 초기 설정 비용
- **적합**: 프로덕션 대시보드, 다수 위젯, 장기 유지보수
- **예상 파일 수**: 8~10개

### Option C — Pragmatic (TanStack Query + discriminated union, CSS Modules)

- **접근법**: TanStack Query v5로 서버 상태만 처리, UI 상태는 `useState`/`useReducer`로 국소화, discriminated union 상태 머신 적용, CSS Modules로 스타일링, container queries 사용
- **장점**: 균형 잡힌 의존성 (TanStack Query만 추가), 탄탄한 타입 안전성, CSS 런타임 비용 제로
- **적합**: 대부분의 일반 대시보드 개발 — 본 계획의 권장안
- **예상 파일 수**: 6~8개

### 권장: Option C (Pragmatic)

**사유**: Option B의 Zustand는 위젯이 대시보드 수준의 복잡한 UI 상태(크로스 위젯 동기화, 복잡한 로컬 필터)를 갖기 전까지 과잉 설계. Option A는 프로덕션 품질 미달. Option C는 TanStack Query의 검증된 데이터 페칭 패턴과 discriminated union의 타입 안전성을 결합하면서도 불필요한 추상화를 피함.

## Codebase Survey (5-Lane Research Summary)

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| Data Fetching | TanStack Query v5: `isPending`/`error`/`data` discriminated pattern + hierarchical key-based cache invalidation + adaptive `refetchInterval` + `refetchIntervalInBackground` | [tanstack.com/query/latest/docs](https://tanstack.com/query/latest/docs/framework/react/overview) | — |
| Props API | Grafana `PanelChrome`: discriminated unions prevent impossible prop combos (`AutoSize \| FixedDimensions`), lazy menu factory `() => ReactElement`, render props for body | [grafana/PanelChrome.tsx](https://github.com/grafana/grafana/blob/main/packages/grafana-ui/src/components/PanelChrome/PanelChrome.tsx) | M1 |
| Responsive | CSS Grid `auto-fit` + `minmax()` for zero-media-query responsiveness; container queries (`@container widget (width > 600px)`) for widget-internal adaptation; Tailwind or CSS Modules | MDN + CSS-Tricks 2025 | — |
| State Mgmt | Zustand `createStore` + React Context (store instance only, not values) for scoped UI state; discriminated union `WidgetStatus<D>` for exhaustive state handling; TanStack Query for server-state | [tkdodo.eu/blog/zustand-and-react-context](https://tkdodo.eu/blog/zustand-and-react-context) + Zustand docs | M1 |
| Testing | Testing Library `findBy*` for async; MSW `server.use()` for per-test handler override; mock `ResizeObserver` for container query logic; `getByRole` priority for a11y | [testing-library.com/docs](https://testing-library.com/docs/react-testing-library/example-intro) + MSW docs | M2, M3 |

## Gap Matrix

| Cat | Item | Evidence | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| 🆕 | `DashboardWidget` component (main) | — | — | — | M1 (spec-match) |
| 🆕 | `DashboardWidgetProps` type definition | Research Lane 2 (Grafana pattern) | HIGH | — | M1 |
| 🆕 | `WidgetStatus<D>` discriminated union type | Research Lane 1, 3 | HIGH | — | M1 |
| 🆕 | `useWidgetQuery` hook (TanStack Query wrapper) | Research Lane 1 | HIGH | — | M1 |
| 🆕 | Sub-components: `WidgetHeader`, `WidgetBody`, `WidgetFooter` | Research Lane 2 | HIGH | — | M1 |
| 🆕 | State views: `LoadingSkeleton`, `ErrorBanner`, `EmptyState`, `WidgetContent` | Research Lane 1 | HIGH | — | M1 |
| 🆕 | Responsive CSS (CSS Modules + container queries) | Research Lane 2, 4 | HIGH | — | — |
| 🆕 | Unit tests: all 5 states + props variation | Research Lane 5 | HIGH | — | M2 |
| 🆕 | MSW handlers for test API mocking | Research Lane 5 | HIGH | — | M2 |

## Waves

### Wave 1 — Foundation: Types & Contracts (3 tasks, parallel, ≤50K tokens)

- [ ] **w1-types**: Define all TypeScript types (`WidgetStatus<D>`, `DashboardWidgetProps`, `WidgetSize`, `WidgetVariant`)
  - **Worker:** `medium`
  - **Token est:** ~8K
  - **Files:** `src/components/DashboardWidget/types.ts`
  - **Verify:** `npx tsc --noEmit` — zero type errors
  - **Gate:** M1 (spec-match: all props documented + typed)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-react-dashboard-w1-types.txt`

- [ ] **w1-hook-contract**: Define `useWidgetQuery` hook signature and `queryConfig` prop interface
  - **Worker:** `medium`
  - **Token est:** ~8K
  - **Files:** `src/components/DashboardWidget/useWidgetQuery.ts`
  - **Verify:** `npx tsc --noEmit` — hook return type matches `WidgetStatus<D>`
  - **Gate:** M1 (spec-match: hook contract matches prop interface)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-react-dashboard-w1-hook.txt`

- [ ] **w1-msw-handlers**: Create MSW handlers for test scenarios (success, empty, error, slow)
  - **Worker:** `mini`
  - **Token est:** ~5K
  - **Files:** `src/components/DashboardWidget/__tests__/mocks/handlers.ts`
  - **Verify:** MSW server starts without errors; handler type matches API contract
  - **Gate:** M2 (test infrastructure ready)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-react-dashboard-w1-msw.txt`

### Wave 2 — Core: Component Implementation (4 tasks, serial on Wave 1, ≤60K tokens)

- [ ] **w2-widget-core**: Implement `DashboardWidget` main component with state machine rendering
  - **Worker:** `heavy`
  - **Token est:** ~15K
  - **Files:** `src/components/DashboardWidget/DashboardWidget.tsx`
  - **Verify:** `npx tsc --noEmit` + renders without crash in test
  - **Gate:** M1 (spec-match: all props consumed, all states rendered)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-react-dashboard-w2-core.txt`

- [ ] **w2-subcomponents**: Implement `WidgetHeader`, `WidgetBody`, `WidgetFooter`
  - **Worker:** `medium`
  - **Token est:** ~10K
  - **Files:** `src/components/DashboardWidget/WidgetHeader.tsx`, `WidgetBody.tsx`, `WidgetFooter.tsx`
  - **Verify:** `npx tsc --noEmit`
  - **Gate:** M1 (spec-match: header/body/footer match props contract)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-react-dashboard-w2-sub.txt`

- [ ] **w2-state-views**: Implement `LoadingSkeleton`, `ErrorBanner`, `EmptyState`
  - **Worker:** `medium`
  - **Token est:** ~12K
  - **Files:** `src/components/DashboardWidget/LoadingSkeleton.tsx`, `ErrorBanner.tsx`, `EmptyState.tsx`
  - **Verify:** `npx tsc --noEmit` + each renders in isolation test
  - **Gate:** M1 + a11y (all views have appropriate ARIA roles)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-react-dashboard-w2-views.txt`

- [ ] **w2-styles**: Implement CSS Modules with container queries for responsive layout
  - **Worker:** `medium`
  - **Token est:** ~10K
  - **Files:** `src/components/DashboardWidget/DashboardWidget.module.css`
  - **Verify:** Visual inspection via Storybook; container query breakpoints trigger at correct widths
  - **Gate:** M4 (lint clean: zero CSS warnings)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-react-dashboard-w2-styles.txt`

### Wave 3 — Integration: Hook + Data Flow (2 tasks, serial on Wave 2, ≤40K tokens)

- [ ] **w3-hook-impl**: Implement `useWidgetQuery` hook wrapping TanStack Query
  - **Worker:** `heavy`
  - **Token est:** ~15K
  - **Files:** `src/components/DashboardWidget/useWidgetQuery.ts`
  - **Verify:** Unit test: hook returns correct status for each MSW scenario; `refetchInterval` fires; cache invalidates on `queryKey` change
  - **Gate:** M2 (test pass=100%), P1 (no duplicate fetches — query deduplication active)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-react-dashboard-w3-hook.txt`

- [ ] **w3-integration**: Wire hook into `DashboardWidget`, verify full data flow
  - **Worker:** `medium`
  - **Token est:** ~10K
  - **Files:** `src/components/DashboardWidget/DashboardWidget.tsx` (update)
  - **Verify:** Integration test: widget renders loading → success/error/empty based on MSW
  - **Gate:** M3 (no regression — all existing tests pass), S1 (data shape preserved through layers)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-react-dashboard-w3-integration.txt`

### Wave 4 — Hardening: Tests & Polish (3 tasks, parallel, ≤50K tokens)

- [ ] **w4-unit-tests**: Write unit tests for all 5 state views + prop variations
  - **Worker:** `heavy`
  - **Token est:** ~18K
  - **Files:** `src/components/DashboardWidget/__tests__/DashboardWidget.test.tsx`
  - **Verify:** `npx vitest --coverage` — coverage ≥ 85%
  - **Gate:** M2 (test pass=100%, coverage ≥ 85%)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-react-dashboard-w4-unit.txt`

- [ ] **w4-a11y-tests**: Write accessibility tests (ARIA roles, keyboard navigation, focus management)
  - **Worker:** `medium`
  - **Token est:** ~10K
  - **Files:** `src/components/DashboardWidget/__tests__/DashboardWidget.a11y.test.tsx`
  - **Verify:** All a11y assertions pass; axe-core reports 0 violations
  - **Gate:** M2 (a11y pass), S2 (interactive elements properly labeled)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-react-dashboard-w4-a11y.txt`

- [ ] **w4-bundle-audit**: Verify bundle size impact and tree-shaking
  - **Worker:** `mini`
  - **Token est:** ~5K
  - **Files:** N/A (analysis only)
  - **Verify:** Widget adds ≤ 5KB gzipped (excluding TanStack Query which is shared); no unused exports
  - **Gate:** M5 (dead-code: zero unused exports), P2 (memory: no unbounded growth)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-react-dashboard-w4-bundle.txt`

## Risk Register (BKIT 11-Gate)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| Props spec과 구현 불일치 | `M1_spec_match` | HIGH | matchRate ≥ 90% | 차이 감지기(gap-detector)로 구현 후 비교 | Plan spec vs code compare |
| 데이터 페칭 테스트 누락 | `M2_test_pass` | HIGH | passRate = 100%, coverage ≥ 85% | MSW로 모든 상태(성공/에러/빈/지연) 모킹 | `npx vitest --coverage` |
| 기존 테스트 회귀 | `M3_regression` | MED | 0 regressions | 신규 컴포넌트이므로 기존 테스트 없음 — 격리된 테스트로 검증 | `npx vitest` |
| Lint 경고 | `M4_lint_clean` | MED | 0 warnings | ESLint + Prettier + stylelint on CSS Modules | `npx eslint . && npx stylelint **/*.css` |
| 미사용 export | `M5_dead_code` | LOW | 0 unused exports | tree-shaking 검증 + 번들 분석 | `npx vite-bundle-visualizer` |
| API 응답 → 상태 머신 변환 누락 | `S1_dataFlow` | MED | integrity ≥ 85% | TypeScript discriminated union으로 컴파일 타임 강제 | Type check across hook → component boundary |
| 접근성 레이블 누락 | `S2_auth` | LOW | 모든 인터랙티브 요소 접근 가능 | `getByRole` 기반 테스트 + axe-core | `npx vitest -- a11y` |
| XSS (데이터 렌더링) | `S3_injection` | HIGH | 모든 데이터 이스케이프 | React의 기본 XSS 방어 + dangerouslySetInnerHTML 사용 금지 | grep for `dangerouslySetInnerHTML` → 0 matches |
| 중복 API 요청 | `P1_query` | MED | No duplicate fetches | TanStack Query 내장 deduplication + `staleTime` 설정 | Query count assertion in test |
| 메모리 누수 (unmounted fetch) | `P2_memory` | LOW | No state update after unmount | TanStack Query 자동 cleanup + AbortController | React strict mode + memory profiling |
| 느린 초기 로딩 | `P3_latency` | MED | p95 render < 200ms | Suspense + lazy loading of heavy sub-views; skeleton UI for perceived performance | React Profiler measurement |

## Props API Design (Detailed)

```typescript
// ── State Machine ──────────────────────────────────
type WidgetStatus<D = unknown> =
  | { type: 'idle' }
  | { type: 'loading' }
  | { type: 'error'; message: string; code?: number; retry: () => void }
  | { type: 'empty'; reason?: string }
  | { type: 'success'; data: D; lastUpdated: Date };

// ── Sizing: discriminated union (Grafana pattern) ──
interface AutoSized {
  width?: never;
  height?: never;
  children: React.ReactNode;
}
interface FixedSized {
  width: number;
  height: number;
  children: (innerWidth: number, innerHeight: number) => React.ReactNode;
}

// ── Main Props ─────────────────────────────────────
interface DashboardWidgetProps<D = unknown> {
  /** Unique widget identifier — used as TanStack Query key prefix */
  id: string;
  /** Widget title shown in header */
  title: string;
  /** Optional tooltip description */
  description?: string;
  /** TanStack Query configuration */
  queryConfig: {
    queryKey: string[];
    queryFn: () => Promise<D>;
    refetchInterval?: number | false;
    refetchIntervalInBackground?: boolean;
    staleTime?: number;
  };
  /** Override loading view */
  loadingView?: React.ReactNode;
  /** Override error view (receives error + retry) */
  errorView?: (error: { message: string; code?: number }, retry: () => void) => React.ReactNode;
  /** Override empty view */
  emptyView?: React.ReactNode;
  /** Render prop for success state */
  children: (data: D, status: { lastUpdated: Date }) => React.ReactNode;
  /** Widget chrome variant */
  variant?: 'card' | 'transparent';
  /** Padding preset */
  padding?: 'none' | 'sm' | 'md';
  /** Header actions (right-aligned) */
  actions?: React.ReactNode;
  /** Lazy menu factory */
  menu?: () => React.ReactNode;
  /** Show header on hover only */
  hoverHeader?: boolean;
  /** Collapsible — controlled */
  collapsed?: boolean;
  onToggleCollapse?: (collapsed: boolean) => void;
  /** Refresh callback (manual trigger) */
  onRefresh?: () => void;
}
```

## State Management Approach

```
┌─────────────────────────────────────────┐
│              DashboardWidget             │
│                                         │
│  ┌─ Props (queryConfig) ─────────────┐  │
│  │         │                         │  │
│  │  useWidgetQuery()  ◄── TanStack   │  │
│  │         │              Query v5   │  │
│  │  WidgetStatus<D>                  │  │
│  │         │                         │  │
│  │  ┌──────┴──────┐                  │  │
│  │  │   switch     │                 │  │
│  │  │ status.type  │                 │  │
│  │  └──┬──┬──┬──┬──┘                 │  │
│  │     │  │  │  │                    │  │
│  │   idle load err empty success     │  │
│  └───────────────────────────────────┘  │
│                                         │
│  UI State (collapse, local filters):    │
│  useState / useReducer (local only)     │
│                                         │
│  Responsive:                             │
│  Container queries on widget wrapper    │
│  resize → CSS adapts, no JS re-render   │
└─────────────────────────────────────────┘

Cross-widget shared state (optional — not in v1):
  → Zustand singleton store
  → timeRange, refreshVersion, global filters
```

### Key decisions:

| Concern | Choice | Rationale |
|---|---|---|
| **Server state** | TanStack Query v5 | Caching, deduplication, background polling, stale-while-revalidate — all built-in |
| **UI state** | `useState` / `useReducer` (local) | Widget-local state (collapse, local filter) doesn't need global store. Option B path: migrate to Zustand `createStore` + Context if cross-widget UI state emerges. |
| **State machine type** | Discriminated union `WidgetStatus<D>` | Exhaustive `switch` enforced by TypeScript — impossible to forget a state |
| **Data flow** | Unidirectional: props → `useWidgetQuery` → `WidgetStatus` → render switch | No side-channel state; every render path traceable from props |
| **Refetch triggers** | `refetchInterval` (polling) + `queryKey` change (dependency) + `onRefresh` callback | Covers scheduled refresh, reactive refresh, and manual refresh |

## Execution Command

```
blackcow-loop "Execute plans/sim-react-dashboard.md" --completion-promise='DashboardWidget renders all 5 states (idle/loading/error/empty/success), test pass=100%, coverage ≥ 85%, lint=0warn, p95 render < 200ms, bundle ≤ 5KB gzipped (excl. shared TanStack Query)' --trust-level=2
```
