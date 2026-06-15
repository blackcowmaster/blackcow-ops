# Governance Decision: sim-python-cli

| Field | Value |
|---|---|
| **Task** | Plan a Python CLI tool for batch file processing — argparse, multiprocessing, progress bar, large directories, file glob patterns, error recovery. Plan only. |
| **Governed at** | 2026-06-28T00:00:00Z |
| **Detected Intent** | Feature |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | STANDARD | Plan-only, but 6 explicit requirements spanning CLI design, concurrency, UX, scale, and resilience. FAST would skip adversarial review and leave edge-case gaps (multiprocessing deadlocks, glob edge cases, error-recovery race conditions). FULL/SIEGE overkill for no-code artifact. |
| **Trust Level** | L3 | Plan-only — no code mutated, no test surface, zero side effects. High trust is safe. |
| **Bootstrap Lanes** | 3 | Lane 1: CLI interface + file discovery (argparse, glob patterns, directory traversal). Lane 2: Processing pipeline + error recovery (multiprocessing, worker pools, retry/backoff, partial-failure handling). Lane 3: Progress reporting + integration (tqdm/rich progress, signal handling, graceful shutdown). Interdependent but parallelizable at discovery stage. |
| **PDCA Max Cycles** | 0 | Plan-only — no implementation to iterate on. |
| **Adversarial Reviewers** | 2 | Medium-low. No runtime code surface to attack, but plan should be stress-tested for: (a) multiprocessing edge cases — deadlocks, fork-safety, pickle serialization failures, (b) error-recovery gaps — partial failures, corrupted files, permission errors, (c) glob/DOS — degenerate patterns on large trees. |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal — plan must self-verify against all 6 requirements |
| M2 test-pass | ❌ | No code surface; plan-only task |
| M3 regression | ❌ | No existing codebase; greenfield |
| M4 lint | ❌ | No source files in diff |
| M5 dead-code | ❌ | No source files in diff |
| S1 dataFlow | ✅ | Plan must specify data flow: glob expansion → file queue → worker pool dispatch → per-file result → aggregate report. Multiprocessing requires explicit data-flow design (queues, shared state constraints, serialization boundaries). |
| S2 auth | ❌ | No auth concerns in CLI batch processing |
| S3 injection | ❌ | CLI args only — no network input surface. Glob pattern injection noted as plan consideration but not a gate trigger. |
| P1 query | ❌ | No DB/repository files |
| P2 memory | ✅ | Multiprocessing + "large directories" triggers memory concern. Plan must address: chunking/batching strategy, per-worker memory budget, `maxtasksperchild` for leak prevention, queue backpressure when producer outruns consumers. |
| P3 latency | ❌ | No p95 target specified |

**Active gates (3/11):** M1, S1, P2

**Diff signal**: N/A — greenfield task, no existing codebase.

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | O1 |
| **Max Capability** | O2 (from capabilities.json) |
| **Browser Available?** | NO |
| **Capped?** | O1 (plan-only — no runtime artifact to instrument or observe) |
| **Fallback Strategy** | Structural plan review: check all 6 requirements addressed, data-flow trace present, memory strategy explicit. Cross-reference against Python multiprocessing best practices (PEP 371, `concurrent.futures`, `multiprocessing.Pool` pitfalls). |
| **Residual Risk** | Plan cannot be runtime-verified (O2+ requires executable code). Multiprocessing correctness (fork safety, pickle boundaries, queue deadlocks) can only be validated at plan level — actual bugs surface only at implementation. Risk accepted for plan-only task. |

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| Stage 1 | N/A | 3 |
| Stage 2 | N/A | 3 |
| Stage 3 | N/A | 3 |

*Widening disabled — plan-only task with fixed 3-lane discovery, zero PDCA cycles.*

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| Plan fails self-audit | M1 score < 90% on requirements coverage | Return plan to blackcow-plan for revision |
| Scope creep | Plan exceeds 6 stated requirements (e.g., adds monitoring, daemon mode, config file parsing) | Return to planner with scope boundary warning |
| Missing data flow | S1 gate: plan lacks explicit data-flow trace from glob to results | Return to planner with S1 gap |
| Missing memory strategy | P2 gate: plan lacks batching/chunking/backpressure design | Return to planner with P2 gap |

*PDCA-based escalation (no evidence, same gate ×2, budget near limit) are N/A for plan-only tasks.*

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| — | — | No patterns match Python / CLI / multiprocessing / file-processing domain | — | — | No action |

**Feed rules**: All 9 existing patterns (FP-001 through FP-009) are in `tools-mapping` and `cross-reference` domains — disjoint from this task. No pattern feed applied.

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (discovery + preflight)** | ~8K |
| **Tokens (plan writing — 3-lane exploration)** | ~20K |
| **Tokens (adversarial review × 2)** | ~8K |
| **Tokens (self-audit + QA — 3 gates)** | ~6K |
| **Tokens (TDD + PDCA)** | 0 (plan-only) |
| **Total estimated** | ~42K |
| **Est. cost (flash)** | ~$0.006 |
| **Est. cost (pro)** | ~$0.63 |
| **Est. cost (blended)** | ~$0.32 |
| **Historical ROI** | 0.78 score/token (feature tasks from loop-roi.jsonl) |
| **Budget utilization** | ~76% of STANDARD mode budget (~55K) |
| **Recommendation** | PROCEED — greenfield plan with 6 concrete requirements. Cost is moderate, scope is bounded, risk is zero (plan-only). |

## Post-Governance Self-Audit Plan

| # | Check | Expectation |
|---|---|---|
| 1 | Plan file exists | `plans/sim-python-cli.md` created |
| 2 | argparse design covered | Subcommands, argument groups, mutually exclusive groups, defaults |
| 3 | multiprocessing design covered | Pool/Process choice, worker count strategy, `maxtasksperchild`, fork vs spawn |
| 4 | Progress bar covered | tqdm/rich integration, per-file vs aggregate progress, multiprocess-safe reporting |
| 5 | Large directories covered | `os.scandir` vs `os.listdir`, streaming/chunking, memory bounds |
| 6 | File glob patterns covered | `pathlib.Path.glob`, `glob.glob`, recursive, exclusion patterns |
| 7 | Error recovery covered | Per-file try/except, retry/backoff, partial-failure report, graceful shutdown on SIGTERM |
| 8 | Data flow trace present (S1) | Glob → queue → workers → results → report; serialization boundaries explicit |
| 9 | Memory strategy present (P2) | Chunk size / batch size, `maxtasksperchild`, queue `maxsize` backpressure |
| 10 | No implementation | No `.py` files created, no code mutated |
| 11 | Governance honored | Plan references mode/trust/gates from this decision |

## Phase 2 Dispatch

```
# 1. Plan (STANDARD mode, 3-lane discovery)
run_skill({ name: "blackcow-plan", arguments: "Plan a Python CLI tool for batch file processing. Requirements: (1) argparse for CLI interface, (2) multiprocessing for parallel file processing, (3) progress bar (tqdm or rich), (4) must handle large directories efficiently, (5) file glob patterns for file selection, (6) error recovery with per-file failure isolation and retry. Write plan to plans/sim-python-cli.md. Do NOT implement — plan only. --mode=STANDARD --govern=sim-python-cli" })

# 2. Self-review plan (STANDARD mode — optional but recommended for 6-requirement task)
run_skill({ name: "blackcow-skill-review", arguments: "--skill=blackcow-plan" })

# 3-5. SKIPPED — user directive: "Do NOT implement — plan only"
```
