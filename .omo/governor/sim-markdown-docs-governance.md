# Governance Decision: sim-markdown-docs

| Field | Value |
|---|---|
| **Task** | Plan a Markdown API reference documentation generator that reads TypeScript source files with JSDoc comments and produces structured API docs in Markdown format. Plan-only — no implementation. |
| **Governed at** | 2026-06-27T23:00:00Z |
| **Detected Intent** | Feature |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | STANDARD | Plan-only, but spans two architecturally distinct pipelines (parsing/extraction + Markdown rendering) plus CLI surface and file-discovery subsystem. FAST would collapse these into a single-lane monolith, missing parser-tradeoff analysis and template-design alternatives. 2-lane discovery + 1 adversarial reviewer is proportionate. FULL/SIEGE overkill — no runtime, no concurrency, no security surface. |
| **Trust Level** | L3 | Plan-only — no code mutated, no test surface, zero side effects. High trust safe. |
| **Bootstrap Lanes** | 2 | Lane 1: **Parsing pipeline** — TypeScript file discovery (glob), AST parsing strategy (ts.Compiler API vs ts-morph vs babel), JSDoc tag extraction, structured data model. Lane 2: **Output pipeline** — Markdown template design, output file organization (single vs multi-file), table-of-contents generation, CLI interface. Independent at discovery stage. |
| **PDCA Max Cycles** | 0 | Plan-only — no implementation to iterate on. |
| **Adversarial Reviewers** | 1 | Modest. No runtime code to attack, but plan should be stress-tested for: (a) JSDoc edge cases — `@template`, `@overload`, `@deprecated` with message, `@see` links, multiline tags, (b) TypeScript constructs — generics, union types, intersection types, conditional types, type aliases vs interfaces, `export default`, (c) Output edge cases — deeply nested namespaces, circular type references, very long signatures. |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal — plan must address all core requirements (file discovery, JSDoc parsing, Markdown generation, CLI, output organization) |
| M2 test-pass | ❌ | No code to test |
| M3 regression | ❌ | No existing codebase — greenfield |
| M4 lint | ❌ | No source files changed |
| M5 dead-code | ❌ | No source files changed |
| S1 dataFlow | ✅ | Plan must specify data flow: glob pattern → file list → AST parse → JSDoc extraction → structured model → Markdown templates → output files. Two-pipeline architecture requires clear interface contract between parsing and rendering stages. |
| S2 auth | ❌ | No auth/route files in diff; no auth concern in CLI doc generator |
| S3 injection | ❌ | CLI args only — no network input surface. Glob pattern injection noted as plan consideration but not a gate trigger. |
| P1 query | ❌ | No DB/repository files |
| P2 memory | ❌ | No collection/buffer files — single-pass file processing |
| P3 latency | ❌ | No p95 target specified |

**Active gates (2/12):** M1, S1. All remaining gates N/A for plan-only.

**Diff signal**: `.omo/governor/ecosystem-health-quiet-report-governance.md`, `.omo/governor/ecosystem-health-report.txt`, `.omo/meta-review/review-2026-06-15-blackcow-plan.md`, `.omo/meta-review/review-history.jsonl`, `skills/tests/validate-blackcow-ecosystem-health.sh`. All `.omo` infrastructure and test files — zero relevance to TypeScript/JSDoc/Markdown documentation. No gate triggers from diff.

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | O1 |
| **Max Capability** | O2 (from capabilities.json) |
| **Browser Available?** | NO |
| **Capped?** | O1 (plan-only — no runtime artifact to instrument or observe) |
| **Fallback Strategy** | Structural plan review: verify all architectural decisions are justified, data-flow trace is complete, JSDoc tag coverage table exists, parser tradeoff analysis is evidence-based. Cross-reference against TypeScript Compiler API docs, ts-morph docs, and JSDoc spec. |
| **Residual Risk** | Plan cannot be runtime-verified (O2+ requires executable code). JSDoc parsing correctness (tag edge cases, type resolution, generic handling) can only be validated at plan level — actual bugs surface only at implementation. Risk accepted for plan-only task. |

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| Stage 1 | N/A | 2 |
| Stage 2 | N/A | 2 |
| Stage 3 | N/A | 2 |

*Widening disabled — plan-only task with fixed 2-lane discovery, zero PDCA cycles.*

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| Plan fails self-audit | M1 score < 90% on requirements coverage | Return plan to blackcow-plan for revision |
| Missing data flow | S1 gate: plan lacks explicit data-flow trace from glob to output | Return to planner with S1 gap |
| Scope creep | Plan exceeds scope (e.g., adds live-reload server, web UI, PDF output, npm publishing) | Return to planner with scope boundary warning |
| Parser analysis shallow | Lane 1 fails to compare ≥2 parser strategies with tradeoffs | Return to planner — request deeper analysis |

*PDCA-based escalation (no evidence, same gate ×2, budget near limit) are N/A for plan-only tasks.*

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| — | — | No patterns match TypeScript / JSDoc / Markdown documentation domain | — | — | No action |

**Feed rules**: All 9 existing patterns (FP-001 through FP-009) are in `tools-mapping` and `cross-reference` domains — completely disjoint from this task. Zero patterns applied.

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (discovery + preflight)** | ~6K |
| **Tokens (plan writing — 2-lane exploration)** | ~14K |
| **Tokens (adversarial review × 1)** | ~4K |
| **Tokens (self-audit + QA — 2 gates)** | ~4K |
| **Tokens (TDD + PDCA)** | 0 (plan-only) |
| **Total estimated** | ~28K |
| **Est. cost (flash)** | ~$0.004 |
| **Est. cost (pro)** | ~$0.42 |
| **Est. cost (blended)** | ~$0.21 |
| **Historical ROI** | 0.85 score/token (documentation tasks), 0.78 score/token (feature tasks) — this task sits at the intersection |
| **Budget utilization** | ~51% of STANDARD mode budget (~55K) |
| **Recommendation** | PROCEED — greenfield plan, well-understood domain (JSDoc→Markdown), moderate architectural depth, cost well within budget. |

## Post-Governance Self-Audit Plan

| # | Check | Expectation |
|---|---|---|
| 1 | Plan file exists | `plans/sim-markdown-docs.md` created |
| 2 | Parser tradeoff analysis | ≥2 parser strategies compared (ts.Compiler API, ts-morph, babel) with tradeoff rationale |
| 3 | JSDoc tag coverage | Table mapping JSDoc tags → Markdown rendering strategy (≥15 tags: `@param`, `@returns`, `@throws`, `@example`, `@deprecated`, `@see`, `@since`, `@template`, `@overload`, `@type`, `@default`, `@remarks`, `@beta`, `@alpha`, `@internal`) |
| 4 | TypeScript construct handling | Plan addresses: generics, union types, intersection types, conditional types, type aliases, interfaces, enums, `export default` |
| 5 | File discovery | Glob-based file selection with configurable patterns, include/exclude filters |
| 6 | CLI interface | CLI flags documented: input glob, output dir, template selection, verbosity |
| 7 | Output organization | Single-file vs multi-file strategy documented; TOC generation strategy |
| 8 | Markdown template design | Template structure documented; heading hierarchy, anchor links, cross-references |
| 9 | Data flow trace (S1) | Explicit data flow: glob → file[] → AST parse → JSDoc extract → structured model → templates → .md files |
| 10 | Adversarial review findings | ≥1 edge case documented from JSDoc/TypeScript stress-testing |
| 11 | No implementation | No `.ts`, `.js`, `.json` files created; no code mutated |
| 12 | Governance honored | Plan references mode/trust/gates from this decision |

## Phase 2 Dispatch

```
# 1. Plan (STANDARD mode, 2-lane discovery)
run_skill({ name: "blackcow-plan", arguments: "Plan a Markdown API reference documentation generator that reads TypeScript source files with JSDoc comments and produces structured API docs in Markdown format. Core requirements: (1) TypeScript file discovery via glob patterns, (2) AST-based JSDoc comment extraction covering the full JSDoc tag vocabulary, (3) structured Markdown output with heading hierarchy, anchor links, and cross-references, (4) CLI interface for input/output configuration, (5) template-driven rendering for customizable output format. Write plan to plans/sim-markdown-docs.md. Do NOT implement — plan only. --mode=STANDARD --govern=sim-markdown-docs" })

# 2. Self-review plan (STANDARD mode — recommended for multi-lane discovery)
run_skill({ name: "blackcow-skill-review", arguments: "--skill=blackcow-plan" })

# 3-5. SKIPPED — user directive: "Do NOT implement — plan only"
#   Loop, QA, and post-mortem are N/A for plan-only tasks.
```
