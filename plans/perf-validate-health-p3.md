# Plan: Optimize validate-blackcow-ecosystem-health.sh Runtime

| Field | Value |
|---|---|
| **Slug** | `perf-validate-health-p3` |
| **Created** | `2026-06-15T19:30:00Z` |
| **Class** | **XS** (single script, ~50 lines modified) |
| **Explore lanes** | 7 dispatched (L1,L2,L3,L4,L5,L7,L9), all returned |
| **Adversarial reviews** | 0/0 (XS scale — skipped) |
| **Budget** | ~85K tokens / 128K target |

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | Runtime of 5.2s blocks PR workflows and local dev loops; target p95 < 3000ms for responsive CI feedback. |
| **WHO** | Developers running `bash skills/tests/validate-blackcow-ecosystem-health.sh` in pre-commit hooks and CI pipelines. |
| **WHAT** | Optimized shell script with parallel sub-script execution, --quiet short-circuit, and micro-optimizations. |
| **RISK** | Parallelization could break output ordering or exit-code semantics. Regression risk confined to this single script. All 59 L1-L5 tests must remain green. |
| **SUCCESS** | matchRate ≥ 90% (byte-identical output for default/--json/--summary modes; --quiet fixes are intentional behavioral corrections), test pass=100% (all 59 L1-L5 tests), lint=0warn, p95 < 3000ms (projected ≤1000ms). |
| **SCOPE** | **IN:** `skills/tests/validate-blackcow-ecosystem-health.sh` only. **OUT:** all 9 sub-scripts (`validate-*.sh`), all 5 test files (`test-l[1-5]-ecosystem-health.sh`), other ecosystem scripts. |

## Summary

The script runs 9 sub-scripts **serially** (dominant bottleneck: ~4.5s of the 5.2s total). Each sub-script is independent — no data dependencies between them. By parallelizing with background jobs + `wait`, we reduce this to max(single_script) ≈ 600ms. Two additional bugs are fixed: the ASCII banner leaks in `--quiet` mode, and the full formatting pipeline (per-script table, traffic-light box, health-score breakdown) runs wastefully even when `--quiet` suppresses normal output. Micro-optimizations eliminate redundant `date` forks, consolidate the python3 JSON generation into pure bash, and remove dead `TIMEOUT_SEC` code. Projected runtime: ≤1000ms (80% reduction).

## Architecture Options

### Only Viable Option — Parallel-First with Defensive Fallbacks

- **접근법**: Three waves of increasing risk/reward. Wave 1 (parallelization) delivers ~75% of the savings (~3.9s). Wave 2 (--quiet short-circuit) fixes bugs + ~150ms. Wave 3 (micro-optimizations) adds ~100ms. Each wave is independently verifiable with the existing 59-test suite.
- **장점**: Can stop after Wave 1 if parallelization proves sufficient. Each wave is a discrete, revertible commit. Zero new dependencies.
- **단점**: Wave 1 carries the highest implementation risk (`set -euo pipefail` + `wait` exit-code semantics).
- **적합**: Performance optimization on a well-tested, single-responsibility script.
- **예상 파일 수**: 1 file modified, 0 new files.

## Codebase Survey (7-Lane Summary)

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| Surface | 706 lines, 4 output modes (default/--quiet/--json/--summary). Main loop lines 327-403 is the critical path. | explore lane 1 | — |
| Call Graph | **9 serial `bash` spawns** in main loop. ~140-170 external process spawns per full run. `parse_counts` ~12 spawns per call (Pattern 1). | explore lane 2 + cross-checked line 343 | P1 |
| Data Shapes | 9 parallel arrays populated in one pass. **6+ redundant post-loop iterations** (text report, JSON file, JSON stdout, per-script table, failure details, health breakdown). `parse_counts` correctly skipped in --verbose (line 350). | explore lane 3 | S1 |
| Tests | **59 active tests** across L1-L5 pyramid. Custom bash framework (PASS/FAIL counters). No CI integration. No performance baselines. | explore lane 4 | M2, M3 |
| Config | `TIMEOUT_SEC=120` is **dead code** (never wired to `timeout`). `--json` overrides `--verbose`. `set -euo pipefail` active. | explore lane 5 | — |
| Git | 4 commits, all same-day (2026-06-15). Conventional Commits + freeform. No reverts. No TODO/FIXME/HACK. Tied for #1 hottest file in skills/tests/. | lane 7 | — |
| Performance | **7 bottlenecks verified.** #1 serial loop (~4.5s → ~600ms, 8× speedup). #2 banner in --quiet. #3 formatting in --quiet. #4 parse_counts inefficiency. #5 redundant iterations. #6 python3 JSON fork. #7 excessive date forks. | lane 9 (pro deep-dive) | P1, P2, P3 |

## Gap Matrix

| Cat | Item | Evidence | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| ✅ Reuse | `parse_counts` function (no changes needed — correctly skipped in --verbose) | `:125-196` | HIGH | — | — |
| ✅ Reuse | `print_summary_box` (no changes needed) | `:189-313` | HIGH | — | — |
| ✅ Reuse | All log helpers (`log_info`, `log_ok`, `log_warn`, `log_err`, `header`) | `:86-91` | HIGH | — | — |
| 🔧 Modify | Main serial loop → parallel with temp files + ordered output | `:327-403` | HIGH | med | M3 (regression), P3 (latency) |
| 🔧 Modify | Banner guard: `! $SUMMARY_OUT` → `! $SUMMARY_OUT && ! $QUIET` | `:314` | HIGH | low | M4 (lint), M1 (spec) |
| 🔧 Modify | Normal output block (`else` branch): wrap in `if ! $QUIET; then … fi` | `:517-671` | HIGH | low | M3 (regression), M1 (spec) |
| 🔧 Modify | Remove 2 `date +%s` forks inside loop; use `$SECONDS` diff | `:333, 346` | HIGH | low | P1 (query) |
| 🔧 Modify | Consolidate JSON file generation: replace python3 with pure-bash emitter | `:443-477` | HIGH | low | M5 (dead-code), P1 (query) |
| 🗑️ Delete | `TIMEOUT_SEC=120` (dead code — never wired to `timeout` command) | `:36` | HIGH | low | M5 (dead-code) |
| 🆕 Build | Temp-directory infrastructure: `mktemp -d` + EXIT trap | — | — | — | M2 (test), P2 (memory) |

## Waves

### Wave 1 — Parallelization (dominant bottleneck, ~3.9s savings)

- [ ] **task-A: Parallel sub-script execution with ordered output collection**
  - **Action**: Replace serial `for script_path` loop (lines 327-403) with 3-phase approach:
    1. **Launch**: Iterate SCRIPTS, launch each as `bash "$script_path" &> "$TMPDIR/out_$i" &`, collect PIDs and file paths
    2. **Wait**: Iterate PIDs, `wait "$pid" || true; exit_codes[$i]=$?` — `|| true` prevents `set -e` from killing orchestrator on sub-script failure
    3. **Process**: Iterate SCRIPTS in original `find | sort` order, read `$TMPDIR/out_$i`, call `parse_counts`, populate `SCRIPT_*` arrays, log results
  - **Files**: `skills/tests/validate-blackcow-ecosystem-health.sh:327-403`
  - **Worker**: heavy
  - **Token est**: ~25K
  - **Key implementation detail**: The `|| true` on `wait` is critical. Without it, `set -e` would terminate the orchestrator when any sub-script exits non-zero. Exit codes are captured in an array, not from `wait`'s return value.
  - **Output ordering guarantee**: Processing phase iterates SCRIPTS in the same `find | sort -z` order as pre-optimization. `log_info`/`log_ok`/`log_warn`/`log_err` fire in original order. Arrays populated in original order. Byte-identical output for default/json/summary modes.
  - **Verify**: `bash skills/tests/test-l5-e2e-ecosystem-health.sh` (all 10 tests pass) + manual runtime measurement
  - **Gate**: M2 (test pass=100%), M3 (0 regressions), P3 (p95 < 3000ms)
  - **Evidence**: `.omo/ulw-loop/evidence/perf-validate-health-p3-w1-a.txt`

- [ ] **task-B: Temp-directory infrastructure**
  - **Action**: Add before main loop:
    ```bash
    TMPDIR=$(mktemp -d "${TMPDIR:-/tmp}/ecosystem-health.XXXXXX")
    trap 'rm -rf "$TMPDIR"' EXIT
    ```
  - **Files**: `skills/tests/validate-blackcow-ecosystem-health.sh` (new block after config, before script discovery)
  - **Worker**: mini
  - **Token est**: ~5K
  - **Verify**: `bash skills/tests/test-l4-system-ecosystem-health.sh` — no temp files leak; kill -INT mid-run, verify cleanup
  - **Gate**: M2 (test pass=100%), P2 (memory — no leak)
  - **Evidence**: `.omo/ulw-loop/evidence/perf-validate-health-p3-w1-b.txt`

### Wave 2 — --quiet Short-Circuit (~150ms savings)

- [ ] **task-C: Banner guard fix**
  - **Action**: Change line 314: `if ! $SUMMARY_OUT; then` → `if ! $SUMMARY_OUT && ! $QUIET; then`
  - **Files**: `skills/tests/validate-blackcow-ecosystem-health.sh:314`
  - **Worker**: mini
  - **Token est**: ~3K
  - **Verify**: `bash skills/tests/validate-blackcow-ecosystem-health.sh --quiet 2>&1 | grep -c "BlackCow Ecosystem Health Report"` → 0
  - **Gate**: M3 (--quiet contract: no non-error stdout), M4 (lint)
  - **Evidence**: `.omo/ulw-loop/evidence/perf-validate-health-p3-w2-c.txt`

- [ ] **task-D: Normal output block guard**
  - **Action**: Wrap the `else` branch of `if $SUMMARY_OUT` (lines 517-671) in `if ! $QUIET; then … fi`. This suppresses: per-script scores table, traffic-light box, health-score breakdown, and final exit banner when --quiet is active.
  - **Files**: `skills/tests/validate-blackcow-ecosystem-health.sh:517-671`
  - **Worker**: medium
  - **Token est**: ~12K
  - **Tension note**: This INTENTIONALLY changes --quiet output (currently the banner + table + box + breakdown leak into stdout despite --quiet). The user explicitly requested this fix. Byte-identical output is preserved for default, --json, and --summary modes. --json stdout path (lines 685-697) is unaffected since it executes before the guarded block.
  - **Verify**: `diff <(before default) <(after default)` → empty; `diff <(before --json) <(after --json)` → empty; `diff <(before --summary) <(after --summary)` → empty; `bash ... --quiet 2>&1 | wc -l` → reduced
  - **Gate**: M1 (spec-match for default/json/summary), M3 (regression for non-quiet modes)
  - **Evidence**: `.omo/ulw-loop/evidence/perf-validate-health-p3-w2-d.txt`

### Wave 3 — Micro-Optimizations (~100ms savings)

- [ ] **task-E: Date fork reduction in loop**
  - **Action**: Replace two `date +%s` forks (lines 333, 346) in the main loop with `$SECONDS`-based timing. At loop start: `loop_start=$SECONDS`. Inside iteration: `script_start=$(( SECONDS - loop_start ))` before sub-script, `script_end=$(( SECONDS - loop_start ))` after, `duration=$(( script_end - script_start ))`.
  - **Files**: `skills/tests/validate-blackcow-ecosystem-health.sh:333, 346`
  - **Worker**: mini
  - **Token est**: ~5K
  - **Note**: `$SECONDS` is a bash builtin (seconds since shell start) — zero fork cost. In Wave 1 parallel mode, all sub-scripts share the same `$SECONDS` clock, so relative durations remain accurate.
  - **Verify**: Duration values within ±1s of pre-optimization for all 9 scripts
  - **Gate**: P1 (query reduction: 2 forks → 0 per iteration)
  - **Evidence**: `.omo/ulw-loop/evidence/perf-validate-health-p3-w3-e.txt`

- [ ] **task-F: JSON file generation consolidation**
  - **Action**: Replace python3-based JSON file generation (lines 443-477) with pure-bash JSON emitter that reuses the existing output pattern from lines 685-697. Write to `$HEALTH_JSON` using the same `printf`-based approach. Remove the `if command -v python3` check entirely — bash JSON emission has no external dependency.
  - **Files**: `skills/tests/validate-blackcow-ecosystem-health.sh:443-477`
  - **Worker**: medium
  - **Token est**: ~15K
  - **Verify**: `diff <(python3 -m json.tool .omo/governor/ecosystem-health-report.json) <(python3 -m json.tool .omo/governor/ecosystem-health-report.json.after)` → identical structure
  - **Gate**: M1 (byte-identical JSON), M5 (dead-code: python3 dependency removed), P1 (1 fork removed)
  - **Evidence**: `.omo/ulw-loop/evidence/perf-validate-health-p3-w3-f.txt`

- [ ] **task-G: Dead code removal**
  - **Action**: Remove line 36: `TIMEOUT_SEC=120` — declared but never passed to any `timeout` command. Sub-scripts run as `bash "$script_path"` without time limit regardless.
  - **Files**: `skills/tests/validate-blackcow-ecosystem-health.sh:36`
  - **Worker**: mini
  - **Token est**: ~2K
  - **Verify**: `grep -c "TIMEOUT_SEC" skills/tests/validate-blackcow-ecosystem-health.sh` → 0
  - **Gate**: M5 (dead-code)
  - **Evidence**: `.omo/ulw-loop/evidence/perf-validate-health-p3-w3-g.txt`

## Risk Register (BKIT 11-Gate)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| Parallelization breaks output ordering | `M1_spec_match` | HIGH | byte-identical for default/json/summary | Process in original `find \| sort` order after parallel collection. Arrays populated in original order. | `diff <(before) <(after)` for default, --json, --summary |
| `wait` + `set -e` kills orchestrator on sub-script failure | `M3_regression` | HIGH | 0 crashes on any sub-script exit code (0, 1, 2+) | `wait "$pid" \|\| true` pattern; exit codes captured in array before `|| true` discards them | Run with deliberately-failing sub-script; verify orchestrator continues |
| Temp files leak on SIGTERM/SIGINT | `P2_memory` | MED | 0 leaked files after any exit path (normal, error, signal) | `trap 'rm -rf "$TMPDIR"' EXIT` — EXIT trap fires on all termination paths | `ls "$TMPDIR"` after `kill -INT` mid-run |
| --quiet output changes (intentional) break downstream consumers | `M1_spec_match` | LOW | --json consumers unaffected; --quiet consumers get leaner output | --quiet fix is a bug correction per user request; --json path completely unchanged | L3 contract tests: JSON schema validation unchanged |
| `parse_counts` regression from loop restructuring | `M3_regression` | LOW | 0 parse regressions across all 9 sub-scripts | `parse_counts` function itself is unchanged; only its input source changes (temp file vs variable) | All 59 L1-L5 tests pass; manual spot-check per-script scores |
| `$SECONDS` drift across parallel jobs gives inaccurate durations | `P3_latency` | LOW | duration ±1s acceptable for monitoring purposes | Document that parallel durations reflect wall-clock not CPU time; `$SECONDS` is monotonic | L4 system test: elapsed_s sanity check (range adjusted to 0.5-10s) |
| Existing tests assume serial execution order | `M3_regression` | LOW | 0 test failures | Tests use `parse_counts` on captured output, not timing assertions. L5 E2E tests check cross-mode consistency. | `bash skills/tests/test-l1-unit-ecosystem-health.sh && bash skills/tests/test-l2-integration-ecosystem-health.sh && ...` |

## Execution Command

```
blackcow-loop "Execute plans/perf-validate-health-p3.md" --completion-promise='p95 < 3000ms, test pass=100%, byte-identical output for default/--json/--summary modes' --trust-level=2
```

### Parallelism Guide
- Wave 1: task-A and task-B can run in parallel (B is infrastructure, A consumes it)
- Wave 2: task-C and task-D can run in parallel (independent sections)
- Wave 3: tasks E, F, G can run in parallel (independent micro-optimizations)
- Total budget: ~85K / 128K target
