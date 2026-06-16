# Plan: KPI Dashboard for Team Project Tracking

| Field | Value |
|---|---|
| **Slug** | `kpi-dashboard` |
| **Created** | 2025-07-10 |
| **Class** | XS (FAST mode) |
| **Explore lanes** | 5/5 dispatched, all returned |
| **Adversarial reviews** | 0 (XS — skipped per FAST mode) |
| **Budget** | ~40K / 115K target |

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | 팀 프로젝트 진행 상황을 시각적으로 파악할 수 있는 KPI 대시보드가 필요하다. 기존 PostgreSQL 기반 작업(task) 데이터를 차트로 표시하여 의사결정 속도를 높인다. |
| **WHO** | 프로젝트 매니저, 팀 리드, 개별 기여자 — 각자 자신의 user_id 범위의 작업을 조회 |
| **WHAT** | 프레임워크-불가지론적 KPI 대시보드 아키텍처 설계 문서. 구체적 구현이 아닌 **선택지 분석 + 설계 청사진** 제공. |
| **RISK** | 실패 시 기존 태스크 API에 영향 없음 (Read-only 대시보드). 신규 API 엔드포인트가 기존 DB pool을 공유하므로 connection 고갈 가능성 (현재 max 10). |
| **SUCCESS** | (1) ≥2개 프레임워크 비교 분석 완료, (2) ≥2개 차트 라이브러리 비교 분석 완료, (3) 모든 KPI 위젯에 대해 로딩/에러/빈 상태 설계 문서화, (4) PostgreSQL KPI 쿼리 패턴이 FP-010 cursor precision을 준수, (5) 반응형 레이아웃 전략 문서화 |
| **SCOPE** | **IN**: 설계 문서 (컴포넌트 트리, 데이터 흐름, 라우트 설계, 쿼리 패턴, 상태 처리, 프레임워크/차트 라이브러리 비교). **OUT**: 실제 구현 코드, 배포 구성, CI/CD 파이프라인, 데이터베이스 스키마 변경 |

## Summary

기존 Express.js + PostgreSQL 백엔드 위에 **읽기 전용 KPI 대시보드 프론트엔드**를 설계한다. 프레임워크를 확정하지 않고 React, Vue, Svelte 3종을 비교 분석하며, 어떤 프레임워크로도 구현 가능한 **프레임워크-불가지론적 아키텍처 청사진**을 제시한다. KPI 데이터는 PostgreSQL에서 직접 집계 쿼리로 추출하며, 기존 `src/lib/db/pool.ts`에 KPI 전용 query 함수를 추가하거나 새 `/api/kpi/*` 라우트를 신설한다. 차트 라이브러리는 Recharts, Chart.js, ECharts 3종을 비교한다.

---

## Architecture Options — Frontend Framework (Requirement #3)

### Option A — React 18+ (with Vite)

| 항목 | 분석 |
|---|---|
| **생태계** | 가장 큰 생태계. 차트, 폼, 상태관리, 라우팅 라이브러리 풍부 |
| **러닝 커브** | 중간 — JSX, hooks, useEffect/useMemo 등 개념 숙지 필요 |
| **상태 관리** | 내장: useState/useReducer/Context. 외부: Zustand (경량), Redux Toolkit, Jotai, TanStack Query |
| **차트 통합** | Recharts (React-native), Nivo, visx, Victory — React 친화적 옵션 다수 |
| **라우팅** | React Router v6/v7 (표준). TanStack Router (타입 안전) |
| **반응형** | CSS Modules, Tailwind CSS, Styled Components, MUI — 선택지 풍부 |
| **번들 크기** | React + ReactDOM ≈ 42 KiB gzip. Vite 번들링 효율적 |
| **채용 가능성** | 최고 — 시장 점유율 1위, 인력 풀 풍부 |
| **적합 시나리오** | 대규모 팀, 장기 유지보수, 풍부한 생태계 활용 시 |

### Option B — Vue 3 (Composition API + Vite)

| 항목 | 분석 |
|---|---|
| **생태계** | React 다음으로 큼. VueUse, Pinia, Vue Router, Nuxt 등 |
| **러닝 커브** | 낮음 — SFC(Single File Component) 직관적, template 문법 HTML과 유사 |
| **상태 관리** | 내장: reactive/ref/computed. 외부: Pinia (공식), TanStack Vue Query |
| **차트 통합** | vue-chartjs (Chart.js 래퍼), Vue ECharts, Vue-ApexCharts |
| **라우팅** | Vue Router 4 (공식, Composition API 지원) |
| **반응형** | Tailwind CSS, Vuetify, PrimeVue, Quasar |
| **번들 크기** | Vue ≈ 22 KiB gzip (React보다 작음). Vite 번들링 |
| **채용 가능성** | 중간 — 아시아/유럽 시장 강세, 북미는 React 우세 |
| **적합 시나리오** | 중소규모 팀, 빠른 프로토타이핑, 점진적 도입 |

### Option C — Svelte 4/5 (with SvelteKit)

| 항목 | 분석 |
|---|---|
| **생태계** | 작지만 성장 중. SvelteKit, Threlte, Melt UI |
| **러닝 커브** | 가장 낮음 — HTML/CSS/JS에 가까운 문법, 반응성은 `$:` 라벨과 `$state` rune |
| **상태 관리** | 내장: stores(writable/derived). 외부: 거의 불필요 (내장 stores로 충분) |
| **차트 통합** | LayerChart, svelte-echarts, Pancake — React/Vue보다 옵션 적음 |
| **라우팅** | SvelteKit (파일 기반 라우팅, 내장) |
| **반응형** | Tailwind CSS, Skeleton UI, Flowbite-Svelte |
| **번들 크기** | 0 KiB 런타임 (컴파일 타임에 사라짐). 전체 앱 크기 최소 |
| **채용 가능성** | 낮음 — 시장 점유율 소수, 인력 풀 좁음 |
| **적합 시나리오** | 소규모 팀, 성능 최우선, 번들 크기 제약이 있는 환경 |

### 권장사항

> **Option A (React) — 조건부 권장.** 생태계 성숙도, 인력 풀, 차트 라이브러리 호환성에서 우위. 단, 팀이 Vue/Svelte 경험이 이미 있는 경우 Option B/C가 더 빠른 개발 속도를 낼 수 있다. **최종 결정은 팀 스킬셋에 위임한다.** 아래 아키텍처 설계는 세 옵션 모두에 이식 가능하게 작성한다.

---

## Codebase Survey (5-Lane Summary)

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| **Surface** | Clean 3-layer architecture: Interface (routes/controllers/middleware) → Application (services/schemas) → Infrastructure (repositories/pool). No circular deps, no barrel files. | `src/routes/` → `src/controllers/` → `src/services/` → `src/repositories/` → `src/lib/db/pool.ts` | — |
| **Call Graph** | **CRITICAL N+1**: `service.bulkRemove` fires 2N+1 sequential queries (no batching). `findAll` uses `Promise.all` for parallel SELECT+COUNT (correct). Double-read in `update`/`remove` (findById then operation — redundant). | `src/services/tasks.service.ts:57-75` (bulkRemove loop), `src/repositories/tasks.repository.ts:60-61` (Promise.all) | **P1** (N+1 in bulkRemove) |
| **Data Shapes** | `Task` (10 fields) → `TaskResponse` (8 fields, drops `user_id` + `deleted_at`). Zod validation with `sanitizeText` on title/description. Cursor pagination uses native PostgreSQL `created_at::text || '_' || id::text` — preserves microsecond precision (FP-010 compliant). | `src/lib/response.ts:5-14` (taskToResponse), `src/repositories/tasks.repository.ts:54` (cursor construction) | **S1** (dataFlow integrity) |
| **Tests** | Jest 30 + ts-jest, 9 test files across 5 levels (unit → E2E). Docker-based real PostgreSQL via raw `docker` CLI (NOT `@testcontainers/postgresql`). 60% global coverage threshold. No skipped tests. No CI pipeline. | `jest.config.ts:11-18`, `__tests__/test-helpers.ts:4-62` | **M2**, **M3** |
| **Config** | 5 env vars: DATABASE_URL, JWT_SECRET, PORT, JWT_EXPIRY, ALLOWED_ORIGINS. **HARDCODED JWT FALLBACK** in `auth.ts:6` (`'dev-secret-change-me'`). `.env.example` committed with placeholder values. No dev/staging/prod separation. CORS error returns 500 not 403. | `src/middleware/auth.ts:6`, `src/app.ts:27` | **S2** (auth), **S3** |

---

## Framework-Agnostic Architecture (Requirement #4)

### Component Tree

```
App
├── AuthProvider                    (auth context: token, user, logout)
│   ├── Layout
│   │   ├── Sidebar                 (navigation + user info)
│   │   ├── Header                  (breadcrumb, KPI date-range picker)
│   │   └── <Outlet />              (route-specific content)
│   │       ├── DashboardPage
│   │       │   ├── KpiGrid
│   │       │   │   ├── KpiCard     (wrapper: loading/error/empty states)
│   │       │   │   │   └── ChartWidget (framework-specific chart renderer)
│   │       │   │   ├── KpiCard
│   │       │   │   │   └── MetricWidget (numeric value display)
│   │       │   │   └── ...
│   │       │   └── DateRangeFilter
│   │       ├── TasksPage           (optional: drill-down table)
│   │       │   └── TaskTable
│   │       └── NotFoundPage
│   └── LoginPage                   (unauthenticated)
```

### Data Flow (Unidirectional)

```
User Action (filter change, page load)
  ↓
Route Params / Query State (date range, status filter, priority filter)
  ↓
KPI Query Hook (useKpi / useQuery / $: reactive statement)
  ↓  ┌─ loading: true
  ↓  ├─ fetch GET /api/kpi/summary?user_id=X&from=Y&to=Z
  ↓  ├─ Authorization: Bearer <token>
  ↓  └─ AbortController for cleanup
  ↓
API Response → Parse → Normalize
  ↓  ┌─ loading: false, data: KpiData
  ↓  ├─ error: null
  ↓  └─ OR → error: AppError, data: null
  ↓
KpiCard receives { data, loading, error }
  ↓  ┌─ loading → Skeleton / Spinner
  ↓  ├─ error   → ErrorDisplay (message + retry button)
  ↓  ├─ empty   → EmptyState ("No tasks in this date range")
  ↓  └─ data    → ChartWidget renders chart
```

### Route Design (Portable)

| Route | Purpose | Auth | Params |
|---|---|---|---|
| `/login` | JWT token acquisition | No | — |
| `/dashboard` | Main KPI view | Yes | `?from=ISO&to=ISO&status=todo,in_progress` |
| `/dashboard/:kpiId` | Single KPI drill-down | Yes | `?from=ISO&to=ISO` |
| `/tasks` | Task table (optional) | Yes | `?page=1&limit=25&status=…` |
| `*` | 404 Not Found | No | — |

> **Portability note:** All routes use plain path strings with query params — compatible with React Router, Vue Router, and SvelteKit file-based routing. No framework-specific route DSL.

### API Layer Abstraction

```typescript
// Framework-agnostic API client (pseudo-code, portable to any framework)
interface KpiApiClient {
  fetchSummary(params: KpiQueryParams, signal?: AbortSignal): Promise<KpiSummary>;
  fetchStatusDistribution(params: KpiQueryParams, signal?: AbortSignal): Promise<StatusDistribution>;
  fetchVelocity(params: KpiQueryParams, signal?: AbortSignal): Promise<VelocityData>;
  fetchBurndown(params: KpiQueryParams, signal?: AbortSignal): Promise<BurndownData>;
  fetchPriorityBreakdown(params: KpiQueryParams, signal?: AbortSignal): Promise<PriorityBreakdown>;
}

interface KpiQueryParams {
  userId: string;
  from?: string;   // ISO 8601
  to?: string;      // ISO 8601
  status?: string;  // comma-separated
}
```

This abstraction ensures the data-fetching layer swaps cleanly between `fetch`, `axios`, or framework-specific fetch wrappers (TanStack Query, Vue Query, SvelteKit `load`).

---

## Charting Library Survey (Requirement #5)

### Option A — Recharts (React)

| 항목 | 분석 |
|---|---|
| **철학** | React 컴포넌트로 차트를 선언적 구성. `<LineChart>`, `<Bar>` 등 JSX 요소로 조립 |
| **장점** | React 생태계와 완벽 통합, 선언적 API 직관적, TypeScript 지원 양호, 커스터마이징 용이 |
| **단점** | React 전용 — Vue/Svelte에서는 사용 불가. 대규모 데이터셋(10K+ 포인트)에서 성능 저하 |
| **KPI 적합 차트** | LineChart(버ンダウン), BarChart(상태 분포), PieChart(우선순위 분포), AreaChart(누적 진행률) |
| **번들 크기** | ~45 KiB gzip (recharts 코어) |
| **라이선스** | MIT |

### Option B — Chart.js 4 (with framework wrapper)

| 항목 | 분석 |
|---|---|
| **철학** | Canvas 기반 범용 차트 라이브러리. `<canvas>` 요소에 데이터를 바인딩 |
| **장점** | **프레임워크 불가지론적** — React(`react-chartjs-2`), Vue(`vue-chartjs`), Svelte(`svelte-chartjs`) 모두 지원. 성능 우수 (Canvas 렌더링). 커뮤니티 + 문서 방대 |
| **단점** | 선언적이지 않음 — `data` + `options` 객체를 구성하는 방식. 애니메이션 커스터마이징이 Recharts보다 복잡 |
| **KPI 적합 차트** | line, bar, doughnut (우선순위 분포), stacked bar (상태×우선순위), radar (팀 성과) |
| **번들 크기** | ~60 KiB gzip (chart.js 코어), + 래퍼별 추가 ~2-5 KiB |
| **라이선스** | MIT |

### Option C — Apache ECharts

| 항목 | 분석 |
|---|---|
| **철학** | 풀스택 차트 엔진. Canvas + SVG 하이브리드 렌더링. 풍부한 차트 유형 |
| **장점** | **가장 다양한 차트 유형** (캘린더 히트맵, 트리맵, 게이지, 샌키 등). 대규모 데이터(100K+ 포인트)에서도 성능 우수. 반응형 내장. Vue(`vue-echarts`), React(`echarts-for-react`), Svelte 래퍼 존재 |
| **단점** | 번들 크기 큼 (~300 KiB gzip full, tree-shaking으로 ~100 KiB). API가 다소 복잡. 한글 문서 부족 |
| **KPI 적합 차트** | line(버ンダウン), bar(상태 분포), pie(우선순위), heatmap(작업 캘린더), gauge(진행률), treemap(카테고리별 분포) |
| **번들 크기** | ~100-300 KiB gzip (트리셰이킹 의존) |
| **라이선스** | Apache 2.0 |

### 권장사항

```
선택 매트릭스:
                    React 전용   Vue/Svelte   번들크기   KPI차트풍부도   러닝커브
Recharts             ★★★         ☆☆☆          ★★★       ★★★            ★★★
Chart.js             ★★★         ★★★          ★★★       ★★☆            ★★★
ECharts              ★★★         ★★★          ★☆☆       ★★★            ★★☆

권장: Option B (Chart.js) — 프레임워크 불가지론적 설계 목표와 가장 부합.
       KPI 차트 요구사항(막대, 선, 도넛)을 모두 충족하며, 세 프레임워크 모두 래퍼 존재.
       ECharts는 추후 고급 시각화(히트맵, 트리맵)가 필요할 때 점진적 도입 검토.
```

---

## Loading / Error / Empty State Design (Requirement #6)

### State Machine (per KpiCard)

```
                  ┌─────────────────────────────┐
                  │         INITIAL              │
                  │  (mount: fetch triggered)    │
                  └──────────┬──────────────────┘
                             │
                    ┌────────▼────────┐
                    │    LOADING      │
                    │ Skeleton/Spinner│
                    └──┬──────┬───────┘
                       │      │
              ┌────────▼─┐  ┌─▼──────────┐
              │   DATA    │  │   ERROR    │
              │ Chart     │  │ Message +  │
              │ rendered  │  │ Retry btn  │
              └──┬───┬────┘  └────┬───────┘
                 │   │            │
         ┌───────▼┐ ┌▼─────────┐ │
         │ EMPTY  │ │ FILTERED │ │ (retry)
         │ "No    │ │ Normal   │ │ → LOADING
         │  data" │ │ display  │ │
         └────────┘ └──────────┘ │
                                 │
              (retry success) ───┘
```

### Implementation Pattern (framework-agnostic pseudo-code)

```typescript
// KpiCard — universal state handler
function KpiCard({ title, queryHook, renderChart, description }: KpiCardProps) {
  // queryHook returns { data, loading, error, refetch, isEmpty }
  const { data, loading, error, isEmpty, refetch } = queryHook();

  // 1. LOADING
  if (loading) return <Skeleton variant="chart" height={300} />;

  // 2. ERROR
  if (error) return (
    <ErrorDisplay
      title={`Failed to load "${title}"`}
      message={error.message}
      correlationId={error.correlationId}
      onRetry={refetch}
    />
  );

  // 3. EMPTY
  if (isEmpty || !data) return (
    <EmptyState
      icon="chart-no-data"
      title={`No data for "${title}"`}
      description="Try adjusting the date range or filters."
      action={{ label: 'Clear filters', onClick: clearFilters }}
    />
  );

  // 4. DATA
  return (
    <Card>
      <CardHeader title={title} description={description} />
      <CardBody>{renderChart(data)}</CardBody>
    </Card>
  );
}
```

### State UX Specifications

| State | Visual | Accessibility | Timeout |
|---|---|---|---|
| **Loading** | Skeleton pulse animation (grey placeholder matching chart shape). Spinner overlay for refetch. | `aria-busy="true"`, `aria-label="Loading chart data"` | 10s timeout → auto-switch to error state with "Request timed out" |
| **Error** | Red-bordered card. Error icon + title + message. Correlation ID (copyable). "Retry" button. | `role="alert"`, focus moved to retry button | — |
| **Empty** | Neutral icon (empty chart). Friendly message. Contextual suggestion (e.g., "No tasks completed between Jan 1–Jan 7"). | `aria-label="No data available"` | — |
| **Stale** | Subtle "Data may be outdated" banner at card top. Last-fetched timestamp. "Refresh" link. | `aria-live="polite"` | Stale threshold: 5 minutes |

---

## Responsive Layout Strategy (Requirement #7)

### Breakpoint System

| Breakpoint | Min Width | Columns | KPI Card Width | Sidebar |
|---|---|---|---|---|
| **Mobile** | 0–639px | 1 | Full width, stacked vertically | Hidden (hamburger toggle) |
| **Tablet** | 640–1023px | 2 | 50% each | Collapsed (icon-only) |
| **Desktop** | 1024–1439px | 3 | 33.3% each | Expanded (text + icon) |
| **Wide** | 1440px+ | 4 | 25% each | Expanded |

### CSS Strategy (Framework-Agnostic)

```
접근법: CSS Grid + Container Queries

1. CSS Grid (IE11 irrelevant):
   .kpi-grid {
     display: grid;
     grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
     gap: 1rem;
   }

2. Container Queries (per-card responsiveness):
   @container (min-width: 400px) {
     .chart-container { height: 300px; }
   }
   @container (max-width: 399px) {
     .chart-container { height: 200px; }
   }

3. Chart responsiveness:
   - Chart.js: `options.responsive: true` + `maintainAspectRatio: false`
   - Recharts: `<ResponsiveContainer width="100%" height={…}>`
   - ECharts: `chart.resize()` on container resize (built-in)

4. Sidebar: CSS transform translateX(-100%) + transition on mobile.
   No JS animation library needed.
```

### KPI Card Priority Ordering (Mobile-First)

On mobile (1 column), cards stack in priority order:

1. **Overall Progress** (gauge / percentage) — 가장 중요한 단일 지표
2. **Status Distribution** (stacked bar) — 현재 스냅샷
3. **Velocity Trend** (line chart) — 시간에 따른 변화
4. **Priority Breakdown** (doughnut) — 우선순위 분포
5. **Burndown** (line chart) — 계획 대비 실적
6. **Recent Activity** (table/list) — 최근 변경 사항

---

## Auth Integration Strategy (Requirement #8)

### Current State

```typescript
// src/middleware/auth.ts — existing JWT verification
// Algorithm: HS256, Header: Bearer <token>, Claims: { sub, role, iat?, exp? }
// Token acquired externally (no /api/auth/login endpoint exists yet)
```

### Dashboard Auth Strategy

```
┌─────────────────────────────────────────────────────┐
│                 AUTH FLOW                           │
│                                                     │
│  LoginPage                                          │
│    │  POST /api/auth/login { username, password }   │
│    │  ← { token, expiresAt, user: { id, role } }   │
│    ▼                                                │
│  Store token in memory (NOT localStorage)           │
│    │  + httpOnly cookie for refresh (if implemented)│
│    ▼                                                │
│  AuthProvider wraps entire app                      │
│    │  - Reads token from memory                     │
│    │  - Injects Authorization header into all API   │
│    │    calls via KpiApiClient                      │
│    │  - On 401 response → redirect to /login        │
│    │  - On token expiry → attempt silent refresh    │
│    │    (POST /api/auth/refresh) or force logout    │
│    ▼                                                │
│  Protected Routes                                   │
│    │  Route guard checks AuthProvider.isAuth        │
│    │  Unauthenticated → redirect /login             │
│    │  Authenticated → render DashboardPage          │
│    ▼                                                │
│  API Calls                                          │
│    GET /api/kpi/summary                             │
│    Authorization: Bearer <token>                    │
│    → Backend auth middleware extracts req.user.sub  │
│    → Queries filtered by user_id                    │
└─────────────────────────────────────────────────────┘
```

### New Backend Requirements (minimal)

| Endpoint | Method | Purpose | Auth |
|---|---|---|---|
| `/api/auth/login` | POST | Issue JWT (body: `{ username, password }`) | No |
| `/api/auth/refresh` | POST | Refresh expiring JWT | Yes (old token) |
| `/api/kpi/*` | GET | All KPI endpoints | Yes |

> **Token storage decision:** `sessionStorage` over `localStorage` (XSS risk mitigation). Alternatively, httpOnly cookie issued by backend (requires minor CORS `credentials: true` adjustment — already set in `src/app.ts`).

---

## PostgreSQL KPI Query Patterns (Requirement #9)

### FP-010 Compliance: Cursor Precision

The existing `findAll` cursor construction uses native PostgreSQL casting to preserve microsecond precision:

```sql
-- src/repositories/tasks.repository.ts:54
SELECT t.*, t.created_at::text || '_' || t.id::text as _cursor
```

All KPI queries MUST follow the same pattern when returning paginated results:

```sql
-- CORRECT (preserves microsecond precision)
SELECT ..., t.created_at::text || '_' || t.id::text as _cursor

-- WRONG (truncates microseconds)
SELECT ..., to_char(t.created_at, 'YYYY-MM-DD"T"HH24:MI:SS') || '_' || t.id::text
```

### KPI Query Patterns

#### 1. Status Distribution (per user, within date range)

```sql
-- No pagination needed — always returns 3 rows (todo, in_progress, done)
SELECT
  t.status,
  COUNT(*)::int AS count
FROM tasks t
WHERE t.user_id = $1
  AND t.deleted_at IS NULL
  AND ($2::timestamptz IS NULL OR t.created_at >= $2)
  AND ($3::timestamptz IS NULL OR t.created_at <= $3)
GROUP BY t.status
ORDER BY
  CASE t.status
    WHEN 'todo' THEN 1
    WHEN 'in_progress' THEN 2
    WHEN 'done' THEN 3
  END;
```

#### 2. Velocity Trend (daily completed count, last N days)

```sql
-- Uses generate_series for gap-free date axis (even days with 0 completions)
SELECT
  d.day::date AS date,
  COUNT(t.id)::int AS completed_count
FROM generate_series(
  CURRENT_DATE - INTERVAL '30 days',
  CURRENT_DATE,
  INTERVAL '1 day'
) AS d(day)
LEFT JOIN tasks t
  ON t.status = 'done'
  AND t.user_id = $1
  AND t.deleted_at IS NULL
  AND t.updated_at::date = d.day::date
GROUP BY d.day
ORDER BY d.day ASC;
```

#### 3. Priority Breakdown (count per priority)

```sql
SELECT
  t.priority,
  COUNT(*)::int AS count,
  COUNT(*) FILTER (WHERE t.status = 'done')::int AS done_count,
  COUNT(*) FILTER (WHERE t.status = 'in_progress')::int AS in_progress_count,
  COUNT(*) FILTER (WHERE t.status = 'todo')::int AS todo_count
FROM tasks t
WHERE t.user_id = $1
  AND t.deleted_at IS NULL
  AND ($2::timestamptz IS NULL OR t.created_at >= $2)
  AND ($3::timestamptz IS NULL OR t.created_at <= $3)
GROUP BY t.priority
ORDER BY
  CASE t.priority
    WHEN 'high' THEN 1
    WHEN 'medium' THEN 2
    WHEN 'low' THEN 3
  END;
```

#### 4. Burndown / Cumulative Flow

```sql
-- Cumulative count of tasks created vs completed over time
WITH daily AS (
  SELECT
    d.day::date AS date,
    COUNT(t_created.id) AS created,
    COUNT(t_done.id) AS completed
  FROM generate_series($2::date, $3::date, INTERVAL '1 day') AS d(day)
  LEFT JOIN tasks t_created
    ON t_created.user_id = $1
    AND t_created.deleted_at IS NULL
    AND t_created.created_at::date = d.day::date
  LEFT JOIN tasks t_done
    ON t_done.user_id = $1
    AND t_done.deleted_at IS NULL
    AND t_done.status = 'done'
    AND t_done.updated_at::date = d.day::date
  GROUP BY d.day
)
SELECT
  date,
  SUM(created) OVER (ORDER BY date) AS cumulative_created,
  SUM(completed) OVER (ORDER BY date) AS cumulative_completed
FROM daily
ORDER BY date;
```

#### 5. KPI Summary (single-query aggregate)

```sql
-- Single query for dashboard overview card
SELECT
  COUNT(*) FILTER (WHERE t.status = 'todo')::int AS todo_count,
  COUNT(*) FILTER (WHERE t.status = 'in_progress')::int AS in_progress_count,
  COUNT(*) FILTER (WHERE t.status = 'done')::int AS done_count,
  COUNT(*)::int AS total_count,
  COALESCE(
    ROUND(
      COUNT(*) FILTER (WHERE t.status = 'done')::numeric
      / NULLIF(COUNT(*), 0) * 100, 1
    ), 0
  ) AS completion_rate_pct,
  COUNT(*) FILTER (
    WHERE t.due_date IS NOT NULL
      AND t.due_date < NOW()
      AND t.status != 'done'
  )::int AS overdue_count,
  CASE
    WHEN COUNT(*) FILTER (WHERE t.status = 'in_progress') > 0
    THEN (SELECT title FROM tasks
          WHERE user_id = $1 AND deleted_at IS NULL AND status = 'in_progress'
          ORDER BY priority = 'high' DESC, due_date ASC NULLS LAST
          LIMIT 1)
    ELSE NULL
  END AS next_focus_task
FROM tasks t
WHERE t.user_id = $1
  AND t.deleted_at IS NULL;
```

### Index Utilization

All KPI queries benefit from existing indexes:

| Query | Index Used | Notes |
|---|---|---|
| Status Distribution | `idx_tasks_status` (partial: `WHERE deleted_at IS NULL`) | Already covers the primary filter |
| Velocity Trend | `idx_tasks_created_at_id` | Covers `updated_at::date` range scan |
| Priority Breakdown | No direct index — but `idx_tasks_priority` exists | Add composite if slow |
| Burndown | `idx_tasks_created_at_id` | Dual join, test with EXPLAIN ANALYZE |
| Summary | All partial indexes | Single scan with multiple FILTER aggregates |

### Query Performance Guard

```typescript
// Reuse existing slow-query detection from pool.ts
// Line 37-39: pool.ts already logs queries > 1000ms
// KPI queries should target < 200ms for dashboard responsiveness
// If > 200ms: consider materialized view refreshed every 5 minutes via pg_cron
```

---

## Gap Matrix

| Cat | Item | Evidence | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| ✅ **Reuse** | `src/lib/db/pool.ts` — query wrapper with slow-query logging | `pool.ts:28-38` | HIGH | — | — |
| ✅ **Reuse** | `src/lib/response.ts` — `success()`, `paginated()` response helpers | `response.ts:17-59` | HIGH | — | — |
| ✅ **Reuse** | `src/middleware/auth.ts` — JWT verification middleware | `auth.ts:8-54` | HIGH | — | — |
| ✅ **Reuse** | `src/middleware/asyncHandler.ts` — async error boundary | `asyncHandler.ts:6-9` | HIGH | — | — |
| ✅ **Reuse** | `src/middleware/errorHandler.ts` — global error formatting | `errorHandler.ts:6-28` | HIGH | — | — |
| 🔧 **Modify** | `src/app.ts` — add `/api/kpi/*` route mount, add `/api/auth/*` routes | `app.ts:47-48` | HIGH | med | **M3** (regression) |
| 🔧 **Modify** | `src/middleware/auth.ts:6` — eliminate hardcoded JWT_SECRET fallback | `auth.ts:6` | HIGH | high | **S2** (auth) |
| 🔧 **Modify** | `src/server.ts` — add `JWT_REFRESH_SECRET` to envalid schema | `server.ts:11-18` | HIGH | med | **S2** |
| 🆕 **Build** | `src/routes/kpi.routes.ts` — KPI route definitions | — | — | — | **M1** (spec-match) |
| 🆕 **Build** | `src/controllers/kpi.controller.ts` — KPI endpoint handlers | — | — | — | **M1** |
| 🆕 **Build** | `src/services/kpi.service.ts` — KPI business logic | — | — | — | **M1** |
| 🆕 **Build** | `src/repositories/kpi.repository.ts` — KPI SQL queries (FP-010 compliant) | — | — | — | **M1**, **P1** |
| 🆕 **Build** | `src/schemas/kpi.schema.ts` — KPI query param validation (Zod) | — | — | — | **S3** (injection) |
| 🆕 **Build** | `src/routes/auth.routes.ts` — Login/refresh routes | — | — | — | **S2** |
| 🆕 **Build** | `src/services/auth.service.ts` — JWT issue/refresh logic | — | — | — | **S2** |
| 🆕 **Build** | `frontend/` — Dashboard SPA (framework TBD) | — | — | — | **M1**, **M5** |
| 🆕 **Build** | `frontend/src/api/kpi-client.ts` — Framework-agnostic API client | — | — | — | **M1** |
| 🆕 **Build** | `frontend/src/components/KpiCard/KpiCard.*` — State machine component | — | — | — | **M1** |

---

## Waves

### Wave 1 — Backend Foundation (6 tasks, parallel, ≤40K tokens)

- [ ] **w1-auth-fix**: Eliminate hardcoded JWT fallback in `src/middleware/auth.ts:6`
  - **Action**: Change `process.env.JWT_SECRET || 'dev-secret-change-me'` → throw `AppError` if `JWT_SECRET` is falsy. Envalid in `server.ts` already validates it — this is a defense-in-depth fix.
  - **Worker:** mini
  - **Token est:** ~2K
  - **Verify:** `npm test` — all existing tests pass. `grep -n "dev-secret-change-me" src/` returns zero matches.
  - **Gate:** S2 (auth)
  - **Evidence:** `.omo/ulw-loop/evidence/kpi-dashboard-w1-auth-fix.txt`

- [ ] **w1-kpi-repo**: Create `src/repositories/kpi.repository.ts` with all 5 KPI query methods
  - **Action:** Implement `getStatusDistribution`, `getVelocityTrend`, `getPriorityBreakdown`, `getBurndown`, `getSummary` using FP-010 compliant cursor precision where paginated.
  - **Worker:** heavy
  - **Token est:** ~12K
  - **Verify:** `npm test -- --testPathPattern="kpi.repository"` — all tests pass. EXPLAIN ANALYZE on each query shows index scans (not seq scans) for user_id filter.
  - **Gate:** P1 (query efficiency), M1 (spec-match)
  - **Evidence:** `.omo/ulw-loop/evidence/kpi-dashboard-w1-kpi-repo.txt`

- [ ] **w1-kpi-schema**: Create `src/schemas/kpi.schema.ts` — Zod validation for KPI query params
  - **Action:** Define `kpiQuerySchema` (userId: uuid, from: ISO datetime optional, to: ISO datetime optional, status: enum optional). Reuse existing `taskStatusEnum` from `task.schema.ts`.
  - **Worker:** mini
  - **Token est:** ~2K
  - **Verify:** `npm test -- --testPathPattern="kpi.schema"` — test valid/invalid/edge cases pass.
  - **Gate:** S3 (injection — Zod validation blocks malicious input)
  - **Evidence:** `.omo/ulw-loop/evidence/kpi-dashboard-w1-kpi-schema.txt`

- [ ] **w1-kpi-service**: Create `src/services/kpi.service.ts` — delegates to repository, no business logic yet
  - **Action:** Thin service layer: `getAll` → repo calls. No ownership checks (KPIs are always user-scoped via `user_id` in WHERE clause).
  - **Worker:** medium
  - **Token est:** ~3K
  - **Verify:** `npm test -- --testPathPattern="kpi.service"` — integration tests pass.
  - **Gate:** M1
  - **Evidence:** `.omo/ulw-loop/evidence/kpi-dashboard-w1-kpi-service.txt`

- [ ] **w1-kpi-controller**: Create `src/controllers/kpi.controller.ts` — HTTP handlers for 5 KPI endpoints
  - **Action:** `getSummary`, `getStatusDistribution`, `getVelocity`, `getPriorityBreakdown`, `getBurndown`. Each: extract `req.user!.sub`, parse validated query, call service, return via `success()`.
  - **Worker:** medium
  - **Token est:** ~4K
  - **Verify:** `npm test -- --testPathPattern="kpi.controller"` — unit tests with mocked service pass.
  - **Gate:** M2 (test pass=100%)
  - **Evidence:** `.omo/ulw-loop/evidence/kpi-dashboard-w1-kpi-controller.txt`

- [ ] **w1-kpi-routes**: Create `src/routes/kpi.routes.ts` + mount in `src/app.ts`
  - **Action:** Register `GET /api/kpi/summary`, `/status-distribution`, `/velocity`, `/priority-breakdown`, `/burndown` with `auth(true)` + `validateQuery(kpiQuerySchema)`. Mount in `app.ts` at `/api/kpi`.
  - **Worker:** mini
  - **Token est:** ~2K
  - **Verify:** `npm test -- --testPathPattern="kpi.routes"` — route tests pass. `curl -H "Authorization: Bearer <token>" http://localhost:3000/api/kpi/summary` returns 200 with JSON.
  - **Gate:** S2 (all KPI routes auth-protected), M3 (no regression on existing routes)
  - **Evidence:** `.omo/ulw-loop/evidence/kpi-dashboard-w1-kpi-routes.txt`

### Wave 2 — Auth + Frontend Scaffold (4 tasks, serial on Wave 1, ≤30K tokens)

- [ ] **w2-auth-endpoints**: Create `POST /api/auth/login` + `POST /api/auth/refresh`
  - **Action:** Login: validate credentials (initially env-configured or DB-backed), issue JWT with `{ sub, role, iat, exp }`. Refresh: verify old token, issue new one with extended expiry. Use `jsonwebtoken` (already in deps).
  - **Worker:** heavy
  - **Token est:** ~8K
  - **Verify:** `npm test -- --testPathPattern="auth.routes"`. `curl -X POST -d '{"username":"...","password":"..."}' http://localhost:3000/api/auth/login` returns `{ token, expiresAt, user }`.
  - **Gate:** S2 (auth), S3 (injection — validate body with Zod)
  - **Evidence:** `.omo/ulw-loop/evidence/kpi-dashboard-w2-auth.txt`

- [ ] **w2-frontend-scaffold**: Initialize frontend project with Vite (framework TBD from architecture options)
  - **Action:** `npm create vite@latest frontend -- --template <react|vue|svelte>-ts`. Configure proxy: `frontend/vite.config.ts` → proxy `/api` to `http://localhost:3000`. Set up directory structure per component tree.
  - **Worker:** medium
  - **Token est:** ~4K
  - **Verify:** `cd frontend && npm run dev` → app loads at localhost:5173. `/api/health` proxies to backend successfully.
  - **Evidence:** `.omo/ulw-loop/evidence/kpi-dashboard-w2-scaffold.txt`

- [ ] **w2-api-client**: Build framework-agnostic `KpiApiClient` + `AuthApiClient`
  - **Action:** Implement the `KpiApiClient` interface from the data flow design. Use `fetch` (no axios dependency). Include `AbortController` for cleanup, token injection from `AuthProvider`, error normalization.
  - **Worker:** medium
  - **Token est:** ~5K
  - **Verify:** TypeScript compilation passes. Unit tests mock `fetch` and verify Authorization header injection, error parsing, abort behavior.
  - **Gate:** M2 (test pass=100%)
  - **Evidence:** `.omo/ulw-loop/evidence/kpi-dashboard-w2-api-client.txt`

- [ ] **w2-auth-provider**: Build `AuthProvider` component with login/logout/refresh flow
  - **Action:** Framework-agnostic auth context: stores token in memory (NOT localStorage), provides `login()`, `logout()`, `isAuthenticated`, `user`. Handles 401 interception + silent refresh. Route guard HOC.
  - **Worker:** medium
  - **Token est:** ~6K
  - **Verify:** Unit tests: token stored in memory, 401 triggers redirect, refresh flow works, logout clears state.
  - **Gate:** S2
  - **Evidence:** `.omo/ulw-loop/evidence/kpi-dashboard-w2-auth-provider.txt`

### Wave 3 — KPI Widgets (5 tasks, serial on Wave 2, ≤35K tokens)

- [ ] **w3-kpi-card**: Build `KpiCard` state machine component (loading/error/empty/data)
  - **Action:** Implement the pseudo-code from the state design. Framework-agnostic: props-based rendering. Includes `Skeleton`, `ErrorDisplay`, `EmptyState` sub-components.
  - **Worker:** medium
  - **Token est:** ~5K
  - **Verify:** Render tests for all 4 states. Accessibility: `aria-busy`, `role="alert"`, `aria-label` present.
  - **Gate:** M2, M4 (lint clean)
  - **Evidence:** `.omo/ulw-loop/evidence/kpi-dashboard-w3-kpi-card.txt`

- [ ] **w3-chart-integration**: Integrate Chart.js (or chosen library) with framework wrapper
  - **Action:** Create `ChartWidget` component that wraps chart.js. Configure for responsive resize. Register only needed chart types (bar, line, doughnut) for tree-shaking.
  - **Worker:** medium
  - **Token est:** ~6K
  - **Verify:** Render test with mock data → chart canvas present. Resize observer triggers chart.resize(). No console errors.
  - **Gate:** P3 (latency — chart renders in < 100ms with mock data)
  - **Evidence:** `.omo/ulw-loop/evidence/kpi-dashboard-w3-charts.txt`

- [ ] **w3-summary-widget**: Build Summary KPI widget (completion rate, counts, overdue, next focus)
  - **Action:** `KpiSummaryWidget` — uses `useKpiSummary()` hook → KpiCard. Renders metric numbers + mini progress bar. No chart library needed.
  - **Worker:** medium
  - **Token est:** ~5K
  - **Verify:** All 4 states tested. Empty state when user has 0 tasks. Error state with correlation ID. Data state shows correct completion %.
  - **Gate:** M1, M2
  - **Evidence:** `.omo/ulw-loop/evidence/kpi-dashboard-w3-summary.txt`

- [ ] **w3-distribution-widget**: Build Status Distribution widget (stacked bar)
  - **Action:** `StatusDistributionWidget` — stacked bar chart (todo/in_progress/done). Color scheme: grey/blue/green.
  - **Worker:** medium
  - **Token est:** ~4K
  - **Verify:** 3-bar chart renders. Empty state when all counts are 0. Error state functional.
  - **Gate:** M1, M2
  - **Evidence:** `.omo/ulw-loop/evidence/kpi-dashboard-w3-distribution.txt`

- [ ] **w3-velocity-burndown**: Build Velocity Trend + Burndown widgets
  - **Action:** `VelocityWidget` — line chart (30-day completion trend). `BurndownWidget` — dual-line chart (cumulative created vs completed).
  - **Worker:** medium
  - **Token est:** ~5K
  - **Verify:** Line charts render with date axis. Empty state when no data in range. Gap days (0 completions) correctly shown.
  - **Gate:** M1, M2
  - **Evidence:** `.omo/ulw-loop/evidence/kpi-dashboard-w3-velocity.txt`

### Wave 4 — Layout + Polish (3 tasks, serial on Wave 3, ≤15K tokens)

- [ ] **w4-responsive-layout**: Implement CSS Grid responsive layout with sidebar
  - **Action:** `.kpi-grid { grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }`. Sidebar with CSS transform. Container queries for per-card chart height. Mobile hamburger menu.
  - **Worker:** medium
  - **Token est:** ~5K
  - **Verify:** Visual regression at 4 breakpoints. Sidebar collapses on mobile. Cards reflow correctly.
  - **Gate:** M2
  - **Evidence:** `.omo/ulw-loop/evidence/kpi-dashboard-w4-layout.txt`

- [ ] **w4-date-filter**: Build DateRangeFilter component
  - **Action:** Two date inputs (from/to) with preset buttons (7d, 30d, 90d, All). Updates URL query params → triggers KPI hook refetch.
  - **Worker:** mini
  - **Token est:** ~3K
  - **Verify:** Date change updates URL. All KPI widgets refetch. Preset buttons work. Invalid date range shows validation error.
  - **Gate:** M1, M2
  - **Evidence:** `.omo/ulw-loop/evidence/kpi-dashboard-w4-filter.txt`

- [ ] **w4-integration-tests**: End-to-end KPI dashboard test
  - **Action:** Playwright or Cypress test: login → dashboard loads → KPI cards show loading → data appears → filter date range → charts update → logout.
  - **Worker:** heavy
  - **Token est:** ~6K
  - **Verify:** E2E test passes. All 4 KPI card states are exercised. Auth flow works end-to-end.
  - **Gate:** M3 (no regression), M2
  - **Evidence:** `.omo/ulw-loop/evidence/kpi-dashboard-w4-e2e.txt`

---

## Risk Register (BKIT 11-Gate Taxonomy)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| KPI queries cause DB connection exhaustion | **P1** (query) | HIGH | Pool max=10, dashboard adds ≤5 concurrent reads | Separate read-replica or increase pool max to 20. Use `statement_timeout` (already 30s) as safety net | Load test with 50 concurrent dashboard users |
| Hardcoded JWT fallback in production | **S2** (auth) | CRIT | Zero hardcoded secrets in source | Remove `\|\| 'dev-secret-change-me'` from `auth.ts:6`. Throw if JWT_SECRET is falsy after envalid already validated it | `grep -r "dev-secret-change-me" src/` returns zero matches |
| KPI API breaks existing task CRUD | **M3** (regression) | HIGH | 0 regression test failures | New routes under `/api/kpi/*` — no shared code paths with `/api/tasks/*` except pool.ts | `npm test` full suite passes before merge |
| N+1 in existing bulkRemove propagates to KPI data staleness | **P1** (query) | MED | bulkRemove completes < 500ms for 100 items | Existing code — note for future fix. KPI queries are READ-ONLY and unaffected by write-path N+1 | N/A (KPI queries are independent) |
| Chart library bundle bloats initial page load | **P3** (latency) | MED | First paint < 2s on 3G | Tree-shake Chart.js to only bar/line/doughnut. Lazy-load chart components via dynamic import | Lighthouse performance audit > 90 |
| Token stored in localStorage → XSS leak | **S2** (auth) | HIGH | Zero localStorage token storage | Store JWT in memory (closure variable in AuthProvider). Refresh via httpOnly cookie (requires backend support) | Penetration test: `document.cookie`, `localStorage.getItem('token')` both null |
| Unvalidated date range → SQL injection in KPI queries | **S3** (injection) | CRIT | All KPI inputs Zod-validated | Zod schema validates `from`/`to` as ISO 8601 datetime strings. PostgreSQL parameterized queries ($1, $2) prevent injection even if Zod bypassed | `curl "...?from=2024-01-01'; DROP TABLE tasks;--"` → 400 validation error |
| KPI widgets show stale data after task mutation | **S1** (dataFlow) | LOW | Data freshness ≤ 5 min | Client-side stale detection (compare `updated_at` of latest task vs last fetch). "Refresh" button on each KpiCard | Manual test: create task via API, refresh dashboard, new task reflected in counts |
| Empty state confusion — user thinks dashboard is broken | **M1** (spec-match) | LOW | Empty state rendered for all widgets with 0 data | Distinct EmptyState component with contextual message + filter adjustment CTA | Test with newly registered user (0 tasks): all widgets show EmptyState, not error |
| Chart renders with 0 height on mobile | **P3** (latency) | LOW | All chart containers maintain aspect ratio | `maintainAspectRatio: false` + explicit container height. Container queries adjust height per breakpoint | Visual test at 320px, 375px, 414px widths |

---

## Execution

Run this plan with:
```
blackcow-loop "Execute plans/kpi-dashboard.md" --completion-promise='KPI dashboard plan delivered: ≥2 framework options analyzed, ≥2 chart libraries compared, all KPI widgets have loading/error/empty state designs, PostgreSQL query patterns FP-010 compliant, responsive layout strategy documented, auth integration strategy complete.' --trust-level=2
```

### Parallelism Guide
- **Wave 1**: 6 parallel workers (foundation — backend repo/service/controller/routes/schema + auth fix)
- **Wave 2**: 4 parallel workers (auth endpoints + frontend scaffold + API client + auth provider)
- **Wave 3**: 5 parallel workers (all KPI widgets — independent components)
- **Wave 4**: 3 parallel workers (layout + filter + E2E tests)
- **Total budget**: ~120K / 128K (dynamic) — borderline. If exceeded, split Wave 3 into two sub-waves (summary+distribution first, velocity+burndown second).
