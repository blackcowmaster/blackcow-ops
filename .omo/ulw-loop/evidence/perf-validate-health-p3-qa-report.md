# QA Report: validate-blackcow-ecosystem-health.sh

| Field | Value |
|---|---|
| **Slug** | `perf-validate-health-p3` |
| **Target** | `skills/tests/validate-blackcow-ecosystem-health.sh` |
| **Plan** | `plans/perf-validate-health-p3.md` |
| **Gates Requested** | M1, M2, M3, M4, M5, P3 (custom) |
| **Governance** | `perf-validate-health-p3` |
| **QA Timestamp** | 2026-06-20T20:00:00Z |
| **Model Tier** | auto |

---

## 11-Gate Scorecard (6 of 11 evaluated)

| Gate | Score | Threshold | Status | Key Evidence |
|---|---|---|---|---|
| **M1** spec-match | **93** | ≥ 90% | ✅ PASS | 6/7 tasks fully implemented; byte-identical output confirmed for default/json/summary. Task E (date→$SECONDS for elapsed) partially done — loop-level forks removed, but line 709 still forks `date +%s`. Task A exit-code recovery uses temp-file sentinels instead of plan's `wait "$pid" \|\| true` — functionally equivalent. |
| **M2** test-pass | **100** | 100% | ✅ PASS | 64/64 across L1(16)+L2(11)+L3(11)+L4(13)+L5(13). All exit 0. No skipped tests. |
| **M3** regression | **100** | 0 | ✅ PASS | 0 regressions. All 57+ call sites intact. All 9 sub-scripts execute. TMPDIR+trap present. --quiet guards in place. No python3 re-introduced. TIMEOUT_SEC absent. |
| **M4** lint | **90** | 0 warn | ⚠️ WARN | 0 syntax errors (`bash -n` clean). ShellCheck not installed. 2 style warnings: (1) unquoted boolean vars in 14 `if $VAR` expressions — `[[ $VAR == true ]]` preferred; (2) `$TMPDIR` shadows system env var — use `SCRIPT_TMPDIR` instead. No errors. |
| **M5** dead-code | **100** | 0 | ✅ PASS | 0 unreferenced symbols. TIMEOUT_SEC removed (0 grep matches). python3 absent (pure-bash JSON confirmed). All 8 functions have callers. All variables used. `parse_counts` all 5 patterns reachable. |
| **P3** latency | **70** | p95 < 3000ms | ⚠️ WARN | **Default mode**: p95=2640ms ✅ (12% below 3000ms). **--json mode**: p95≈3760ms ❌ (25% over target). **--quiet mode**: p95≈3580ms ❌. The plan specified `p95 < 3000ms` without mode restriction. Default mode passes but --json/--quiet exceed the target due to pure-bash JSON builder overhead (~1s from repeated `printf` calls in fd-redirect context). |
| **S1** dataFlow | — | — | NOT EVALUATED | Not in gate selection. |
| **S2** auth | — | — | NOT EVALUATED | N/A for shell script. |
| **S3** injection | — | — | NOT EVALUATED | Not in gate selection. |
| **P1** query | — | — | NOT EVALUATED | Not in gate selection. |
| **P2** memory | — | — | NOT EVALUATED | Not in gate selection. |

### Weighted Total (selected gates only)

| Gate | Weight | Score | Weighted |
|---|---|---|---|
| M1 | 15% | 93 | 13.95 |
| M2 | 15% | 100 | 15.00 |
| M3 | 10% | 100 | 10.00 |
| M4 | 5% | 90 | 4.50 |
| M5 | 5% | 100 | 5.00 |
| P3 | 10% | 70 | 7.00 |
| **TOTAL** | **60%** | — | **55.45 / 60** |

**Weighted Total: 92 / 100**

---

## Gate Details

### M1 — Spec Match (93/100)

**Plan**: `plans/perf-validate-health-p3.md` — 7 tasks (A–G) across 3 waves.

| Task | Status | Evidence |
|---|---|---|
| **A** — Parallel execution | ✅ | `:272-279` (launch), `:282` (wait), `:286+` (process). Exit codes via temp-file sentinels instead of `wait "$pid" \|\| true` — functionally equivalent. |
| **B** — TMPDIR + trap | ✅ | `:49-50`. Exact match to plan. |
| **C** — Banner guard fix | ✅ | `:258`: `! $SUMMARY_OUT && ! $QUIET`. Exact match. |
| **D** — Output block guard | ✅ | `:555-704`: `elif ! $QUIET`. Functionally equivalent to plan's wrap-in-fi. |
| **E** — Date fork reduction | ⚠️ Partial | Loop-level `date +%s` removed (duration hardcoded to 0 in parallel mode). **Line 709 still forks `date +%s`** for elapsed: `ELAPSED_S=$(( $(date +%s) - START_EPOCH ))`. Plan intended `$SECONDS` builtin. |
| **F** — Pure-bash JSON | ✅ | `:470-514`. Zero `python3` references. JSON structure matches plan. |
| **G** — TIMEOUT_SEC removal | ✅ | 0 grep matches. Fully removed. |

**Byte-identical output verification** (per plan M1 criteria):
- Default mode: `diff` → empty ✅
- `--json` mode: `diff` → empty ✅
- `--summary` mode: `diff` → empty ✅
- `--quiet` mode: intentionally changed (bug fix) ✅
- JSON file structure: identical to plan spec ✅

### M2 — Test Pass (100/100)

All 5 test suites pass. Raw bash harness (no bats/shunit2). No coverage tool.

| Suite | Checks | Status |
|---|---|---|
| L1 Unit | 16/16 | ✅ |
| L2 Integration | 11/11 | ✅ |
| L3 Contract | 11/11 | ✅ |
| L4 System | 13/13 | ✅ |
| L5 E2E | 13/13 | ✅ |

**Note**: L1 test hangs on `strip_ansi ""` without stdin redirect — workaround: `bash test-l1-unit-ecosystem-health.sh < /dev/null`.

### M3 — Regression (100/100)

**0 regressions.** Baseline from `.omo/ulw-loop/completion-report.md` (11/11 gates passed, 57 call sites).

- All 8 functions have callers intact
- Parallel architecture (Phase 1→2→3) verified intact
- TMPDIR + `trap EXIT` present
- `--quiet` guards in place (banner, running header, output block, final exit)
- No python3 re-introduced
- TIMEOUT_SEC fully absent
- Runtime: 9/9 sub-scripts execute, 445/445 checks pass, GREEN exit 0

### M4 — Lint (90/100)

| Category | Count | Detail |
|---|---|---|
| **Errors** | **0** | `bash -n` clean parse. Shebang, `set -euo pipefail`, trap cleanup all present. |
| **Warnings** | **2** (15 locations) | (1) Unquoted boolean vars: 14 `if $JSON_OUT`/`if $QUIET` expressions — ShellCheck SC2086; safer with `[[ $VAR == true ]]`. (2) `$TMPDIR` shadows system env var at line 32 — use `SCRIPT_TMPDIR`. |

**ShellCheck**: NOT installed — zero static analysis available. This is the single biggest lint gap.

### M5 — Dead Code (100/100)

**0 unreferenced exports. 0 dead symbols.**

- `TIMEOUT_SEC=120`: absent (grep → 0 matches)
- `python3`: absent (line 470 comment confirms deliberate pure-bash approach)
- All 8 functions verified reachable: `strip_ansi` (3 callers), `safe_int` (12+), `parse_counts` (2), `print_summary_box` (1), nested helpers (4 — called within `print_summary_box`)
- All variables used: `START_EPOCH`→line 709, `ELAPSED_S`→line 726, `SKILLS_DIR`→derives `PROJECT_ROOT`
- `parse_counts` all 5 patterns reachable via distinct format matching

### P3 — Latency (70/100)

**Target**: p95 < 3000ms (from plan Context Anchor `p95_target_ms: 3000`)

| Mode | p95 | vs Target | Status |
|---|---|---|---|
| **Default** | 2640ms | −360ms (12% margin) | ✅ PASS |
| `--json` | ~3760ms | +760ms (25% over) | ❌ FAIL |
| `--quiet` | ~3580ms | +580ms (19% over) | ❌ FAIL |
| `--summary` | ~2910ms | −90ms (3% margin) | ✅ PASS |

**Hotspots identified**:
1. `--json` mode: pure-bash JSON builder (lines 690-720) adds ~1s from repeated `printf` calls in fd-redirect context → heredoc approach could recover ~800ms
2. Orchestrator: 8× `date` forks (~40ms) — replace with `printf '%(...)T' -1` (bash 4.2+)
3. Orchestrator: 2× `awk` calls (~20ms) — use bash arithmetic `$((pass * 100 / total))`
4. `parse_counts`: 24× `grep` + 23× `sed` (~235ms) — use `[[ =~ ]]` regex + `${var//}` expansion
5. Bottleneck child (`validate-blackcow-ecosystem.sh`): ~300ms in 40× grep + 15× date

**Note**: The plan's completion report claimed p95≈2550ms. Current measurement shows 2640ms for default mode — a ~90ms degradation, still within threshold. The --json mode regression is new and exceeds the target.

---

## Test Pyramid Status

| Layer | File | Tests | Status |
|---|---|---|---|
| L1 Unit | `test-l1-unit-ecosystem-health.sh` | 16 | ✅ 100% |
| L2 Integration | `test-l2-integration-ecosystem-health.sh` | 11 | ✅ 100% |
| L3 Contract | `test-l3-contract-ecosystem-health.sh` | 11 | ✅ 100% |
| L4 System | `test-l4-system-ecosystem-health.sh` | 13 | ✅ 100% |
| L5 E2E | `test-l5-e2e-ecosystem-health.sh` | 13 | ✅ 100% |

**Coverage**: No coverage tool available for bash. All critical paths exercised: parse_counts (5 patterns), strip_ansi, parallel execution, --quiet/--json/--summary/--verbose modes, error handling, temp file cleanup.

---

## Recommendations

### Critical (0)
(None)

### High (2)

| # | Gate | Issue | Fix |
|---|---|---|---|
| H1 | P3 | `--json` mode exceeds p95 target (3760ms > 3000ms) | Replace pure-bash JSON `printf` loop with `cat <<EOF` heredoc for ~800ms recovery. Also replace remaining `date +%s` at line 709 with `$SECONDS`. |
| H2 | P3 | `--quiet` mode exceeds p95 target (3580ms > 3000ms) | The --quiet mode runs same workload as default — variance is from system load. Investigate why --quiet is slower than default despite producing less output. |

### Medium (3)

| # | Gate | Issue | Fix |
|---|---|---|---|
| M1 | M4 | ShellCheck not installed — zero static analysis | `brew install shellcheck` and run on all 18 `.sh` files in `skills/tests/`. |
| M2 | M4 | 14 unquoted boolean var expressions | Replace `if $JSON_OUT; then` with `if [[ $JSON_OUT == true ]]; then` throughout. |
| M3 | M1 | Task E — remaining `date +%s` fork at line 709 | Replace `ELAPSED_S=$(( $(date +%s) - START_EPOCH ))` with `ELAPSED_S=$SECONDS`. Remove `START_EPOCH`. |

### Low (4)

| # | Gate | Issue | Fix |
|---|---|---|---|
| L1 | M4 | `$TMPDIR` shadows system env var | Rename to `SCRIPT_TMPDIR` or `HEALTH_TMPDIR`. |
| L2 | P3 | 8× `date` forks in orchestrator (~40ms) | Use `printf '%(%Y-%m-%dT%H:%M:%SZ)T' -1` (bash 4.2+ builtin). |
| L3 | P3 | 2× `awk` calls for score calculation (~20ms) | Use `score=$(( pass * 100 / total ))` — pure bash arithmetic. |
| L4 | P3 | 24× `grep` + 23× `sed` in `parse_counts` (~235ms) | Use `[[ =~ ]]` regex + `${var//pattern/}` parameter expansion. |

---

## Cost Tracking

| Gate | Lanes Dispatched | Est. Tokens | Model Tier | Est. Cost |
|---|---|---|---|---|
| Phase 0 L1 (test inventory) | 1 (explore) | ~8K | budget | ~$0.0006 |
| Phase 0 L2 (code structure) | 1 (explore) | ~6K | pro | ~$0.0008 |
| Phase 0 L3 (plan extraction) | 1 (explore) | ~4K | budget | ~$0.0003 |
| Phase 0 L4 (external audit) | 1 (explore) | ~12K | budget | ~$0.0008 |
| Phase 0 L5 (runtime probe) | 1 (explore) | ~10K | budget | ~$0.0007 |
| M1 spec-match | 1 (explore) | ~8K | pro | ~$0.0011 |
| M2 test-pass | 1 (explore) | ~6K | budget | ~$0.0004 |
| M3 regression | 1 (explore) | ~8K | pro | ~$0.0011 |
| M4 lint | 1 (explore) | ~7K | budget | ~$0.0005 |
| M5 dead-code | 1 (explore) | ~6K | budget | ~$0.0004 |
| P3 latency | 1 (explore) | ~10K | budget | ~$0.0007 |
| Report assembly | — | ~5K | — | ~$0.0003 |
| **TOTAL** | **11 lanes** | **~90K** | — | **~$0.008** |

---

## Residual Risk

- **bash 3.2.57 EOL**: The system bash is 6 major releases behind (latest: 5.3). Shellshock CVEs are patched, but newer CVEs (CVE-2019-18276, CVE-2022-3715) in `set -e` async-list handling and `wordexp` are not backported. Low risk for local test scripts.
- **dash incompatibility**: If anyone runs via `sh script.sh` (where `/bin/sh` → `dash`), `set -o pipefail` will fail. Scripts use `#!/usr/bin/env bash` correctly, so this requires user error.
- **P3 --json mode regression**: Not caught by existing tests (tests validate JSON structure, not latency). Consider adding a latency assertion to L4 system tests.
- **No coverage tooling**: Cannot quantify exactly which code paths are untested. All known paths are exercised, but edge cases in `parse_counts` pattern fallback are not individually testable.
