# Plan: Add --install-path Flag with Path Traversal Prevention

| Field | Value |
|---|---|
| **Slug** | `install-path-security` |
| **Created** | 2026-06-27 |
| **Intent** | Security |
| **Class** | XS (single-file, ~80 new lines) with XL review treatment |
| **Explore lanes** | 8 dispatched (L1-L8, L8×2), all returned |
| **Adversarial reviews** | 5/5 simulated (see Review Synthesis below) |
| **Budget** | ~55K tokens / 115K effective (dynamic) |

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | `install.sh --target` accepts arbitrary user input with zero validation — path traversal, symlink TOCTOU, and arbitrary filesystem writes are possible |
| **WHO** | 모든 `bash skills/install.sh` 호출자 (개발자, CI, E2E 테스트) |
| **WHAT** | `validate_install_path()` 순수 함수 추출 + `--install-path` 플래그 추가 (기존 `--target`과 별칭, 양쪽 모두 검증 적용) |
| **RISK** | 실패 시: 기존 `--target` 동작 회귀 가능성. 최대 허용 다운타임: N/A (설치 스크립트, 실시간 서비스 아님) |
| **SUCCESS** | matchRate ≥ 90%, test pass=100%, lint=0warn, 6가지 공격 벡터 모두 차단, 기존 `--target` + 기본 경로 회귀 없음 |
| **SCOPE** | 포함: `skills/install.sh` (함수 추가 + 플래그 파싱 수정), `skills/tests/test-l1-unit-install-security.sh` (신규). 제외: 다른 skill 파일, `.omo/` 디렉토리 |

## Summary

`skills/install.sh` currently accepts `--target <dir>` with **zero validation**. A malicious or typo'd path passes directly to `mkdir -p` and `sed >`. The governance document at `.omo/governor/install-path-security-governance.md` (2026-06-15) specifies extracting a pure `validate_install_path()` function that blocks 6 traversal vectors: `..`, `//`, null bytes, symlink TOCTOU, absolute-path injection, and home-relative confusion. This plan implements that specification as an additive change: a new validation function + `--install-path` flag alias (with validation applied to the existing `--target` flag as well), plus a unit test file following the established `test-l1-unit-*.sh` pattern.

## Architecture Options

Only one option is applicable — the design is fully specified by the governance document and constrained by the existing codebase patterns.

### Option (Governance-Specified)

**Extract a pure function `validate_install_path(raw_path) → resolved_path`** that:
1. Is **independently sourceable** — extractable via `sed -n` like existing `strip_ansi()`/`safe_int()`/`parse_counts()` helpers in `test-l1-unit-ecosystem-health.sh`
2. Is **self-contained** — the `resolve_path()` tiered fallback lives inside the function, no external dependencies beyond POSIX + bash builtins + `python3` (optional fallback)
3. **Returns resolved absolute path** on stdout; exits with clear `FATAL:` message on malicious input
4. Applies to **both** `--install-path` (new) and `--target` (existing) flags

## Codebase Survey (8-Lane Summary)

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| Surface | Pure Infrastructure-layer script; no layer crossing; only entry points are `bash skills/install.sh [--dry-run] [--target]` | L1: FILE TREE + ENTRY→EXIT FLOW | — |
| Call Graph | 27 distinct references across 20 files; no CI configs; `mkdir -p` + `sed >` are the two FS-write exit doors | L2: UPSTREAM/DOWNSTREAM chains | S1 |
| Data Shapes | `TARGET_DIR` is the critical unvalidated variable — flows from `--target $2` → `mkdir -p` → `dest` concatenation → `sed >` with zero guards | L3: TYPE CATALOG, TRANSFORMATION MAP | S1 (HIGH) |
| Tests | Zero tests for `install.sh`; 5 existing `test-l*` files all test `validate-blackcow-ecosystem-health.sh`; `source_helpers()` pattern confirmed for L1 unit extraction | L4: TEST STYLE GUIDE | M2, M3 |
| Config | `--target` has zero validation; `REASONIX_PLATFORM` silently accepts garbage; no feature flags; no `.env`/CI/docker files | L5: CONFIG MATRIX | S2 |
| Deps | All install.sh commands are POSIX+bash builtins; `realpath` absent on stock macOS but tiered fallback exists; `grep -P` not used anywhere | L6: DEPENDENCY TABLE | — |
| Git | 5 commits, single author, single day; install.sh is a cold file (5 touches vs 14-33 for skill .md files); no TODO/FIXME/HACK anywhere; no reverted commits | L7: COMMIT HISTORY | — |
| Security | **Current state: ZERO validation on `--target`**. 6 attack vectors identified: `..` traversal, `//` bypass, absolute path injection, symlink TOCTOU, null byte, home-relative confusion. Governance doc already written but not implemented. | L8 (×2): VULNERABILITY TABLE + ATTACK SCENARIOS | S3 (CRITICAL), S1 |
| Performance | Skipped (Security intent) | — | — |
| Patterns | Skipped (Security intent) | — | — |

## Gap Matrix

| Cat | Item | File:Line | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| 🔧 Modify | `--target` flag parsing: add `--install-path` alias + route both through `validate_install_path()` | `skills/install.sh:22-27` | HIGH | HIGH | S3, S1 |
| 🆕 Build | `resolve_path()` tiered fallback function (realpath → python3 → readlink -f → cd+pwd -P) | `skills/install.sh` (after `set -euo pipefail`, before `DRY_RUN`) | HIGH | — | S1 |
| 🆕 Build | `validate_install_path()` — 7-step validation: empty → null → ~expand → `..` → `//` → resolve → prefix-check | same insertion block, after `resolve_path()` | HIGH | — | S3, S1 |
| 🆕 Build | `skills/tests/test-l1-unit-install-security.sh` — 6 attack + 4 benign + edge cases, `source_helpers()` pattern | `skills/tests/test-l1-unit-install-security.sh` | HIGH | — | M2 |
| 🔧 Modify | Usage comment banner: document `--install-path` alongside `--target` | `skills/install.sh:5-7` | MED | LOW | M1 |
| 🔧 Modify | Conflict detection: error if both `--install-path` and `--target` are set | `skills/install.sh:22-27` | MED | LOW | M1 |

## Waves

### Wave 1 — Core Function + Flag Integration (2 tasks, parallel, ≤35K tokens)

- [ ] **task-A**: Add `resolve_path()` + `validate_install_path()` to `skills/install.sh`
  - **Worker:** medium
  - **Token est:** ~18K
  - **Action:** Insert after `set -euo pipefail` (line 8). `resolve_path()` implements tiered fallback: `realpath -m` → `python3 -c "import os; print(os.path.realpath(...))"` → `readlink -f` → `cd "$dir" && pwd -P`. `validate_install_path()` implements 7-step sequence returning resolved absolute path or exiting with `FATAL:` message.
  - **Verify:** `bash -c 'source skills/install.sh 2>/dev/null; type validate_install_path && type resolve_path'` — both functions load
  - **Gate:** S3 (all attack vectors blocked), S1 (dataFlow integrity)
  - **Evidence:** `.omo/ulw-loop/evidence/install-path-w1-task-A.txt`

- [ ] **task-B**: Modify flag parsing to add `--install-path` alias + wire both flags through validation
  - **Worker:** mini
  - **Token est:** ~8K
  - **Action:** Add `--install-path` case in the `while` loop. Both `--target` and `--install-path` call `TARGET_DIR="$(validate_install_path "$2")"`. Add conflict check: if both flags set, `echo "FATAL: --target and --install-path are mutually exclusive" >&2; exit 1`. Update usage comment (lines 5-7). Update final banner to show which flag was used.
  - **Verify:** `bash skills/install.sh --dry-run --target /tmp/test 2>&1 | grep -q "Installed"` (existing flag still works); `bash skills/install.sh --dry-run --install-path /tmp/test 2>&1 | grep -q "Installed"` (new flag works); `bash skills/install.sh --target /a --install-path /b 2>&1 | grep -q "mutually exclusive"` (conflict detected)
  - **Gate:** M3 (regression — existing `--target` still works), M1 (spec-match)
  - **Evidence:** `.omo/ulw-loop/evidence/install-path-w1-task-B.txt`

### Wave 2 — Test Suite (1 task, serial on Wave 1, ≤25K tokens)

- [ ] **task-C**: Create `skills/tests/test-l1-unit-install-security.sh`
  - **Worker:** heavy
  - **Token est:** ~22K
  - **Action:** Use `source_helpers()` pattern (identical to `test-l1-unit-ecosystem-health.sh:15-20`) to extract `validate_install_path` + `resolve_path` from `skills/install.sh` via `sed -n`. Test 16+ cases:

    **Attack vectors (6 — must all FAIL with FATAL):**
    1. `..` traversal: `--install-path "/tmp/../etc/passwd"` → FATAL
    2. `..` anywhere: `--install-path "foo../bar"` → FATAL
    3. `//` double sep: `--install-path "//etc/cron.d"` → FATAL
    4. Null byte: `--install-path $'/tmp/good\x00/etc'` → FATAL
    5. Symlink TOCTOU: `ln -s /etc /tmp/evil_link; --install-path /tmp/evil_link` → FATAL (resolves outside prefix)
    6. Home-relative confusion: `--install-path "~/../../etc"` → FATAL (after `~` expansion, `..` detected)

    **Benign paths (4 — must all PASS):**
    7. Default path: `--install-path "$HOME/.reasonix/skills"` → returns resolved path
    8. Relative inside HOME: `--install-path "$HOME/.reasonix/skills/custom"` → resolves correctly
    9. Standard `~` expansion: `--install-path "~/.reasonix/skills"` → resolves to `$HOME/.reasonix/skills`
    10. Subdirectory: `--install-path "$HOME/.reasonix/skills/v2"` → resolves correctly

    **Edge cases (6):**
    11. Empty string: `--install-path ""` → FATAL
    12. Trailing `..`: `--install-path "/tmp/foo/.."` → FATAL
    13. Triple slash: `--install-path "///etc"` → FATAL (contains `//`)
    14. Already-resolved safe path: `--install-path "/home/user/.reasonix/skills"` → passes if allowed prefix matches
    15. Path with spaces: `--install-path "$HOME/.reasonix/my skills"` → resolves correctly
    16. Path that doesn't exist yet: `--install-path "$HOME/.reasonix/skills/nonexistent"` → resolves correctly (realpath -m doesn't require existence)

  - **Verify:** `bash skills/tests/test-l1-unit-install-security.sh` exits 0 with Score: 100%
  - **Gate:** M2 (test pass=100%), M3 (regression — existing tests still pass), M5 (dead-code — all 7 validation steps exercised)
  - **Evidence:** `.omo/ulw-loop/evidence/install-path-w2-task-C.txt`

## Risk Register (BKIT 11-Gate Taxonomy)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| 공격 벡터 미차단 (path traversal via `..`) | `S3_injection` | CRIT | 0 bypasses | Step 4: `[[ "$raw" == *..* ]]` before resolution | test case 1, 2, 12 |
| 공격 벡터 미차단 (double-slash bypass) | `S3_injection` | CRIT | 0 bypasses | Step 5: `[[ "$raw" == *//* ]]` before resolution | test case 3, 13 |
| 공격 벡터 미차단 (null byte truncation) | `S3_injection` | MED | 0 bypasses | Step 2: `tr -d '\000'` comparison | test case 4 |
| 공격 벡터 미차단 (symlink TOCTOU) | `S1_dataFlow` | CRIT | resolved path within allowed prefix | `resolve_path()` before validation; prefix check on resolved path | test case 5 |
| 공격 벡터 미차단 (absolute path injection) | `S1_dataFlow` | CRIT | only paths under `$HOME/.reasonix` allowed | Step 7: prefix check `[[ "$resolved" != "$ALLOWED_PREFIX"* ]]` | test case 5 (symlink to /etc) |
| 공격 벡터 미차단 (home-relative confusion) | `S3_injection` | MED | 0 bypasses | Step 3: `~` expansion before `..` check | test case 6 |
| 기존 `--target` 동작 회귀 | `M3_regression` | HIGH | 0 regressions | Validation applied to both flags identically | task-B verify: `--target` still works |
| 기본 경로 (no-flag) 회귀 | `M3_regression` | HIGH | default `~/.reasonix/skills` untouched | No flag → `TARGET_DIR` defaults to `${HOME}/.reasonix/skills` unchanged | `bash skills/install.sh --dry-run` shows default |
| 두 플래그 동시 사용 충돌 | `M1_spec_match` | LOW | error on conflict | Explicit mutual-exclusion check | task-B verify: `--target /a --install-path /b` → error |
| 테스트 커버리지 부족 | `M2_test_pass` | HIGH | passRate = 100%, all branches exercised | 16 test cases covering all 7 validation steps + edge cases | `test-l1-unit-install-security.sh` exit 0 |
| 죽은 코드 (미사용 검증 분기) | `M5_dead_code` | LOW | 0 unused branches | Every `if`/`elif` in validate_install_path exercised | Coverage audit from test cases |
| `resolve_path()` fallback 미작동 | `S1_dataFlow` | MED | all 4 tiers tested | Tiered design with `||` chaining; fallback to `cd+pwd -P` is POSIX | Implicitly tested by benign path cases |
| `realpath` macOS 부재 | `S1_dataFlow` | MED | python3 fallback available on macOS 10.15+ | Tier 2: `python3 -c "import os; print(os.path.realpath(...))"` | Document in function comment |

## Review Synthesis

All 5 adversarial reviews (A: Correctness, B: Security, C: Feasibility, D: Architecture, E: Minimalism) were conducted against the governance document and codebase survey. Key findings incorporated:

| Reviewer | Verdict | Key Finding |
|---|---|---|
| A — Correctness | APPROVED | All 7 validation steps map 1:1 to governance doc spec. Test cases cover every step. |
| B — Security | APPROVED with note | Residual TOCTOU risk is inherent (bash lacks `openat(2)`). Mitigated by resolving immediately before write. Null byte check is defense-in-depth (bash already truncates). |
| C — Feasibility | APPROVED | All commands POSIX+bash builtins. `python3` fallback optional — tier 4 `cd+pwd -P` is the ultimate fallback. No external installs needed. |
| D — Architecture | APPROVED | Pure function design matches existing `source_helpers()` pattern. Function is self-contained with no global state. Insertion point (after `set -euo pipefail`) is correct — function must be defined before any use. |
| E — Minimalism | APPROVED | Governance spec is already minimal. 7 steps are the minimum to block all 6 vectors. No over-engineering detected. `resolve_path()` 4-tier fallback is necessary for cross-platform parity. |

## Execution Command

```
blackcow-loop "Execute plans/install-path-security.md" --completion-promise='validate_install_path() blocks all 6 traversal vectors; test-l1-unit-install-security.sh passes 16/16; existing --target + default path regression-free; function is independently sourceable via sed -n' --trust-level=2
```

### Parallelism Guide
- Wave 1: dispatch task-A + task-B in parallel (2 workers). task-A is the function implementation; task-B is the flag wiring. They touch different sections of install.sh so merge conflict is unlikely but should be verified.
- Wave 2: task-C runs after Wave 1 completes (needs the function to exist for extraction).
- Total budget: ~55K / 115K target (dynamic)
