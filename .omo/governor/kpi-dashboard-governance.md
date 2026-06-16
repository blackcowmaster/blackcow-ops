# Governance Decision: kpi-dashboard

| Field | Value |
|---|---|
| **Task** | Plan a KPI dashboard for team project tracking. Pulls data from existing PostgreSQL database, displays charts. Frontend framework undecided — framework-agnostic architecture plan. Plan only, no implementation. |
| **Governed at** | 2026-07-16T00:00:00Z |
| **Detected Intent** | Feature |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | FAST | Plan-only directive from user: "Plan only, no implementation." Zero code surface, zero runtime, zero side effects. Consistent with `sim-react-dashboard` and `sim-expo-login` plan-only precedents. |
| **Trust Level** | L4 | Maximum trust. Output is a Markdown plan document — no risk of breaking existing code, no security surface. Human reviews the plan before any implementation begins. |
| **Bootstrap Lanes** | 2 | Broader scope than `sim-react-dashboard` (widget) — this is an application-level architecture. Two lanes: (1) database/KPI schema exploration, (2) frontend charting/framework survey. Slight parallelism justified. |
| **PDCA Max Cycles** | 0 | No implementation to iterate on. Plan quality evaluated at write-time by planner self-audit. |
| **Adversarial Reviewers** | 0 | No code surface to attack. Architecture analysis is analytical, not adversarial. |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal — plan must address all requirements |
| M2 test-pass | ❌ | No code to test |
| M3 regression | ❌ | No existing dashboard codebase — nothing to regress against |
| M4 lint | ❌ | Plan is Markdown, not executable |
| M5 dead-code | ❌ | No code changes |
| S1 dataFlow | ❌ | No type/schema files in diff; no runtime data flow to analyze |
| S2 auth | ❌ | No auth/route files in diff |
| S3 injection | ❌ | No handler/input files in diff |
| P1 query | ❌ | No DB/repository files in diff (governance/skills only) |
| P2 memory | ❌ | No collection/buffer files in diff |
| P3 latency | ❌ | No p95 target specified |

**Active gates: 1/12 (M1 only).** All other gates N/A for a plan-only task with zero code surface.

**Diff signal**: `.omo/governor/workout-tracker-decomp-governance.md`, `plans/workout-tracker-decomp.md`, `skills/blackcow-governor.md` — all `.omo` and skills infrastructure files. Zero relevance to KPI dashboard planning. No gate triggers from diff.

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | O0 |
| **Max Capability** | O4 (from capabilities.json — Playwright screenshots available) |
| **Browser Available?** | YES |
| **Capped?** | N/A — plan-only, no runtime verification possible or needed |
| **Fallback Strategy** | Manual human review of the plan document against the requirement checklist |
| **Residual Risk** | Minimal. Risk lives in architecture decisions (framework, charting library, query patterns) that will be validated during implementation governance. FP-010 (PostgreSQL keyset cursor microsecond truncation) flagged for awareness in query design section. |

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| Stage 1 | uncertainty_score < 30 | 2 |
| Stage 2 | 30 ≤ uncertainty < 60 | 2 |
| Stage 3 | uncertainty ≥ 60 | 2 |

Capped at 2 lanes: (1) database/KPI schema survey, (2) frontend charting + framework survey. Slightly wider than `sim-react-dashboard` (1 lane) due to broader scope, but no need for full multi-lane exploration on a plan-only task.

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| Plan fails M1 | Plan doesn't cover all requirements | Re-dispatch planner with explicit requirement checklist |
| Scope creep | Planner starts implementing code, generating JSX/TSX/SQL DDL, or choosing framework without user input | HALT — remind: plan only, framework-agnostic, user decides framework |
| Framework lock-in | Planner commits to React/Vue/Svelte/Angular without presenting tradeoffs | Re-dispatch with explicit multi-framework comparison requirement |

All other escalation rules (no evidence, same gate ×2, budget near limit) are N/A for plan-only tasks.

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| FP-010 | P1 | `Date.toISOString()` drops microsecond digits in PostgreSQL keyset cursor pagination | 2026-06-27T12:00:00Z | 90 | **Flag for awareness**: Plan's query design section should note PostgreSQL-native cursor construction preference. Do NOT apply fix — no code exists yet. |

**Feed rules check:** FP-010 is the only DB-domain pattern. Effectiveness ≥ 80, but this is a plan — no fix to apply. Flagged as architectural guidance for query design section. FP-001 through FP-009 are all in `tools-mapping`/`cross-reference` domains — completely disjoint from KPI dashboard planning. Zero patterns auto-applied.

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (discovery + governance)** | ~4K (preflight reads + this document — more files than sim-react-dashboard due to DB infra survey) |
| **Tokens (plan writing)** | ~15K (application-level architecture: DB schema survey, KPI query design, charting library survey, framework comparison matrix, component tree, data flow, deployment considerations — broader than single widget) |
| **Tokens (QA/M1 check)** | ~1.5K (spec-match verification against requirement checklist) |
| **Total estimated** | ~20.5K |
| **Est. cost (flash)** | $0.00 (well under flash tier limit) |
| **Est. cost (pro)** | $0.00 |
| **Est. cost (blended)** | $0.00 |
| **Historical ROI** | 0.78 score/token (feature task baseline from loop-roi.jsonl); 0.85 (documentation baseline). Blended estimate: ~0.80 |
| **Budget utilization** | ~5% of FAST mode budget |
| **Recommendation** | PROCEED — minimal cost, zero risk, constrained scope. Scope is broader than sim-react-dashboard (application vs component), but still plan-only with no implementation risk. |

## Post-Governance Self-Audit

| Check | Expectation |
|---|---|
| Plan file exists | `plans/kpi-dashboard.md` created |
| Framework-agnostic | Plan presents ≥2 framework options with tradeoff analysis; does NOT lock in React/Vue/etc. without justification |
| PostgreSQL integration | Query patterns documented; connection strategy; existing `pg` pool vs new connection considered |
| KPI schema | Example KPI definitions + SQL query sketches; aggregation strategy (materialized views vs live queries) |
| Charting library survey | ≥2 charting libraries compared (e.g., Recharts, Chart.js, D3, ECharts, Observable Plot) |
| Data flow diagram | PostgreSQL → API layer → frontend data flow documented |
| Loading/error/empty states | All three states addressed for each KPI widget |
| Responsive strategy | Dashboard layout adapts to desktop/tablet views |
| Auth consideration | How the dashboard authenticates against existing JWT auth (or separate) |
| Scope boundary | Clearly states what is IN scope (architecture plan) and OUT of scope (implementation, framework decision) |
| Self-audit checklist | Plan includes its own M1 verification checklist |
| No code emitted | Zero SQL DDL, zero JSX/TSX, zero `npm install` commands in plan output |

## Phase 2 Dispatch

```
# 1. Plan (FAST mode, plan-only — no loop, no QA)
run_skill({ name: "blackcow-plan", arguments: "Plan a KPI dashboard application for team project tracking. Requirements: (1) Pull data from existing PostgreSQL database, (2) Display charts for project KPIs, (3) Frontend framework is UNDECIDED — present ≥2 framework options with tradeoff analysis, do NOT lock in, (4) Framework-agnostic architecture — component tree, data flow, route design should be portable, (5) Charting library survey (≥2 options), (6) Loading/error/empty states for all KPI widgets, (7) Responsive layout strategy, (8) Auth integration strategy, (9) Query design patterns for PostgreSQL (note FP-010 cursor precision). Plan only, NO implementation. Write to plans/kpi-dashboard.md. --mode=FAST --govern=kpi-dashboard" })

# 2-5. SKIPPED — user directive: 'Plan only, no implementation.'
#   Loop, QA, skill-review, and post-mortem are all N/A for FAST/plan-only tasks.
```
