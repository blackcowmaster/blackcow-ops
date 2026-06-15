# Plan: Input Validation Guards for validate-*.sh Scripts

| Field | Value |
|---|---|
| **Slug** | `validate-input-guard` |
| **Created** | `2026-06-15T20:30:00Z` |
| **Class** | **M** (10 files, moderate complexity) |
| **Explore lanes** | 9 dispatched (L1-L8 inc. L8×2; L9/L10 skipped per Security intent), all returned |
| **Adversarial reviews** | 5/5 passed — 1 critical finding (exit-code collision resolved), 1 architecture challenge (dual-path detection addressed) |
| **Budget** | estimated ~45K tokens / 128K target |

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | validate-*.sh 스크립트들이 대상 스킬 파일이 없을 때 모호한 grep 에러를 내거나 조용히 실패함. 특히 plan.sh와 governor.sh는 항상 exit 0을 반환하여 ecosystem-health가 실패를 감지하지 못함. |
| **WHO** | BKIT pipeline 운영자, CI/CD 시스템, `bash skills/tests/validate-blackcow-ecosystem-health.sh` 실행자 |
| **WHAT** | 9개 validate 스크립트 + 1개 ecosystem-health 오케스트레이터에 파일 존재 preflight guard 추가. 대상 파일 부재 시 stderr에 `FATAL: Target file not found: <path>` 출력 후 exit 1. ecosystem-health.sh는 기존 parse_counts 파이프라인으로 이를 자연스럽게 감지. |
| **RISK** | 기존 테스트 회귀(M3) — 모든 변경은 additive-only. exit 1을 이미 사용하는 스크립트와의 충돌은 없음 (이미 exit 1 사용 중인 contract/integration 스크립트들은 preflight guard를 먼저 통과한 후에만 테스트 로직이 실행되므로 충돌 없음) |
| **SUCCESS** | matchRate ≥ 95%, 모든 스크립트가 대상 파일 부재 시 `FATAL: Target file not found:` stderr 출력 후 exit 1, plan.sh/governor.sh는 더 이상 파일 부재 시 exit 0을 반환하지 않음, ecosystem-health가 이를 FAIL로 정상 분류, 기존 유효한 대상에 대한 모든 테스트 100% 통과 |
| **SCOPE** | **포함**: `skills/tests/validate-blackcow-plan.sh`, `validate-blackcow-governor.sh`, `validate-blackcow-plan-contract.sh`, `validate-blackcow-governor-contract.sh`, `validate-blackcow-plan-integration.sh`, `validate-blackcow-governor-integration.sh`, `validate-blackcow-governor-system.sh`, `validate-cross-skill-contract.sh`, `validate-blackcow-ecosystem.sh`, `validate-blackcow-ecosystem-health.sh`. **제외**: `skills/install.sh`, `skills/blackcow-*.md` 스킬 파일, `.omo/` 하위 디렉토리, python3 -c injection 취약점 수정 (별도 follow-up) |

## Summary

10개 validate 스크립트에 최소한의 preflight guard(한 줄)를 추가한다. 각 스크립트가 테스트 시작 전에 대상 파일 존재를 확인하고, 없으면 stderr에 명확한 에러 메시지를 출력한 후 exit 1로 종료한다. ecosystem-health.sh 오케스트레이터는 이미 `2>&1`로 stderr를 캡처하고 `|| local_exit=$?`로 exit code를 감지하므로, 추가 변경 없이 guard 실패를 정상 감지한다. 이 접근법은 Reviewer E의 미니멀리즘 분석(83% 감축 가능)을 반영하여, 불필요한 함수 추상화나 exit code 3 같은 새 컨벤션을 도입하지 않는다.

## Architecture Options

### Option A — Minimal (inline one-liner) ✅ 권장
- **접근법**: 각 스크립트의 TARGET/SKILL_FILE 정의 직후에 `[[ -f "$VAR" ]] || { echo "FATAL: Target file not found: $VAR" >&2; exit 1; }` 추가. 다중 파일 스크립트는 모든 주요 파일을 확인.
- **장점**: 리스크 최저, 10줄 미만 변경, 기존 exit code 컨벤션과 충돌 없음, ecosystem-health 변경 불필요
- **단점**: 코드 중복 (10개 파일에 동일 패턴)
- **적합**: 이 하드닝 작업
- **예상 파일 수**: 9개 스크립트 + ecosystem-health(선택적 강화)

### Option B — Clean (shared preflight lib)
- **접근법**: `skills/tests/lib/preflight.sh` 생성 후 각 스크립트에서 source
- **장점**: DRY, 일관된 에러 처리
- **단점**: lib 파일 의존성 추가, Reviewer D 지적: 5개 assert_file_exists 중복이 이미 존재하지만 새 lib 도입은 또 다른 미사용 추상화 위험
- **예상 파일 수**: 10개 + lib

### Option C — Wrapper (ecosystem-health injection)
- **접근법**: ecosystem-health.sh가 각 sub-script 실행 전에 파일 존재 확인
- **장점**: validate 스크립트 변경 없음
- **단점**: stand-alone 실행 시 (ecosystem-health 없이 직접 실행) 보호 안 됨, ecosystem-health가 각 스크립트의 대상 파일을 알아야 함
- **예상 파일 수**: 1개 (ecosystem-health.sh만)

### 권장: Option A (Minimal inline one-liner)
**사유**: Reviewer E의 미니멀리즘 분석이 설득력 있음 — 12-task 계획을 2-task로 83% 감축 가능. Reviewer D의 dual-path detection 우려는 inline guard가 exit 1을 사용하고 ecosystem-health가 기존 parse_counts로 처리하므로 발생하지 않음. Reviewer B는 TOCTOU/S3 이슈를 SAFE로 판정. Reviewer C는 모든 변경이 feasible함을 확인.

## Codebase Survey (9-Lane Summary)

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| Surface | 2 scripts accept CLI override ($1), 2 use hardcoded relative paths, `assert_file_exists` defined but dead in 5 scripts | L1 explore | — |
| Call Graph | Only ecosystem-health.sh calls other scripts; 8/10 use `set -euo pipefail`; plan.sh/governor.sh always exit 0 | L2 explore | S1 |
| Data Shapes | 8 scripts use SCRIPT_DIR-derived paths (robust), 2 contract scripts use cwd-relative hardcoded paths (fragile) | L3 explore | S1 |
| Tests | No CI exists; ecosystem-health.sh is the only test runner; `assert_file_exists` defined in 5 files, never called | L4 explore | M2, M3 |
| Config | No shared config/lib; bash 4.0 minimum; no env var dependencies; 2 scripts lack `set -euo pipefail` | L5 explore | — |
| Deps | python3 is critical dependency (all 10 scripts); stat has macOS/Linux fallback; PyYAML optional | L6 explore | — |
| Git | Only 2 commits, 8 files committed once each, 2 untracked; no TODO/FIXME/HACK | L7 explore | — |
| Security | CRITICAL: 6 python3 -c injection sites in plan.sh+governor.sh (deferred); All grep/awk/sed properly quoted; No eval | L8 explore (×2) | S3 |

**Reviewer Synthesis:**

| Reviewer | Key Finding | Resolution |
|---|---|---|
| A (Correctness) | Exit code collision: plan uses exit 1, some scripts already exit 1 on test failure | **Accepted**: exit 1 is correct — guard fires BEFORE test logic, so no collision. Scripts that already exit 1 (contract/integration) will exit 1 from guard instead of from test logic — same exit code, same behavior in ecosystem-health. |
| B (Security) | S3 injection vulns not fixed but scope separation accepted; output poisoning low risk | **Accepted**: python3 -c injection deferred to follow-up plan. Guard message is simple enough that output poisoning is negligible. |
| C (Feasibility) | governor-system.sh should NOT guard all 6 upfront (lazy for consumer files in T4) | **Accepted**: guard only GOVERNOR_FILE upfront; consumer files checked lazily in T4 block |
| D (Architecture) | Dual-path detection concern: exit-code + parse_counts | **Resolved**: guard's exit 1 + stderr message → captured by `2>&1` → parse_counts sees no test output → `total=0` fallback → `local_exit=1` → `fail=1`. Single path through existing logic. No new detection channel needed. |
| E (Minimalism) | 83% reduction possible; plan-contract.sh + governor-contract.sh already hardened; one-liner suffices | **Accepted**: Using inline one-liner, not function. contract scripts already have `[ -f ]` check, just need early-exit behavior (currently they fail-but-continue). |

## Gap Matrix

| Cat | Item | Evidence | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| 🔧 Modify | Add preflight one-liner to plan.sh after TARGET= | `skills/tests/validate-blackcow-plan.sh:24` | HIGH | MED | M1, S1 |
| 🔧 Modify | Add preflight one-liner to governor.sh after TARGET= | `skills/tests/validate-blackcow-governor.sh:26` | HIGH | MED | M1, S1 |
| 🔧 Modify | Strengthen existing `[ -f ]` check to early-exit in plan-contract.sh | `skills/tests/validate-blackcow-plan-contract.sh:49` (already has check) | HIGH | LOW | M1 |
| 🔧 Modify | Strengthen existing `[ -f ]` check to early-exit in governor-contract.sh | `skills/tests/validate-blackcow-governor-contract.sh:59` (already has check) | HIGH | LOW | M1 |
| 🔧 Modify | Add preflight one-liner to plan-integration.sh after PLAN_FILE= | `skills/tests/validate-blackcow-plan-integration.sh:37` | HIGH | MED | M1 |
| 🔧 Modify | Add preflight one-liner to governor-integration.sh after GOVERNOR_FILE= | `skills/tests/validate-blackcow-governor-integration.sh:38` | HIGH | MED | M1 |
| 🔧 Modify | Add preflight one-liner for GOVERNOR_FILE only in governor-system.sh | `skills/tests/validate-blackcow-governor-system.sh:35` | HIGH | MED | M1 |
| 🔧 Modify | Add preflight for 5 files in cross-skill-contract.sh | `skills/tests/validate-cross-skill-contract.sh:34-38` | HIGH | MED | M1 |
| 🔧 Modify | Add graduated guard (≥2 missing → exit) in ecosystem.sh | `skills/tests/validate-blackcow-ecosystem.sh:46-52` (ALL_SKILLS array) | HIGH | LOW | M1 |
| 🔧 Modify | Add NOT FOUND summary line to ecosystem-health.sh failure output | `skills/tests/validate-blackcow-ecosystem-health.sh:330` (traffic light section) | MED | LOW | M3 |
| 🆕 Build | Verify: all scripts fail with clear message when target missing | New test run | — | — | M2 |

## Waves

### Wave 1 — Core Guards (4 tasks, parallel, ≤20K tokens)

- [ ] **task-A**: Add preflight to `validate-blackcow-plan.sh`
  - **Action**: After `TARGET="${1:-$PROJECT_ROOT/skills/blackcow-plan.md}"` (line 24), insert:
    ```bash
    [[ -f "$TARGET" ]] || { echo "FATAL: Target file not found: $TARGET" >&2; exit 1; }
    ```
  - **Worker:** `mini`
  - **Token est:** ~2K
  - **Verify:** `bash skills/tests/validate-blackcow-plan.sh /nonexistent → exit 1 + stderr "FATAL: Target file not found: /nonexistent"`
  - **Gate:** M1 (spec-match), M3 (regression: `bash skills/tests/validate-blackcow-plan.sh` should still pass)
  - **Evidence:** `.omo/ulw-loop/evidence/validate-input-guard-w1-a.txt`

- [ ] **task-B**: Add preflight to `validate-blackcow-governor.sh`
  - **Action**: After `TARGET="${1:-$PROJECT_ROOT/skills/blackcow-governor.md}"` (line 26), insert same one-liner
  - **Worker:** `mini`
  - **Token est:** ~2K
  - **Verify:** `bash skills/tests/validate-blackcow-governor.sh /nonexistent → exit 1 + FATAL`
  - **Gate:** M1, M3
  - **Evidence:** `.omo/ulw-loop/evidence/validate-input-guard-w1-b.txt`

- [ ] **task-C**: Strengthen `validate-blackcow-plan-contract.sh`
  - **Action**: Replace the existing `if [ -f "$SKILL_FILE" ]; then pass "..."; else fail "..."; fi` (lines 49-53) with preflight guard that exits 1 on missing file. The HOMEDIR_SKILL check (line 56) is informational only — keep as `fail()` but don't exit.
  - **Worker:** `mini`
  - **Token est:** ~2K
  - **Verify:** `bash skills/tests/validate-blackcow-plan-contract.sh` from wrong directory → exit 1 + FATAL
  - **Gate:** M1, M3
  - **Evidence:** `.omo/ulw-loop/evidence/validate-input-guard-w1-c.txt`

- [ ] **task-D**: Strengthen `validate-blackcow-governor-contract.sh`
  - **Action**: Same as task-C: replace `if [ -f "$SKILL_FILE" ]` pass/fail with preflight guard exit 1
  - **Worker:** `mini`
  - **Token est:** ~2K
  - **Verify:** `bash skills/tests/validate-blackcow-governor-contract.sh` from wrong directory → exit 1 + FATAL
  - **Gate:** M1, M3
  - **Evidence:** `.omo/ulw-loop/evidence/validate-input-guard-w1-d.txt`

### Wave 2 — Integration + Multi-File Guards (4 tasks, parallel, ≤20K tokens)

- [ ] **task-E**: Add preflight to `validate-blackcow-plan-integration.sh`
  - **Action**: After `PLAN_FILE="${SKILL_DIR}/blackcow-plan.md"` (line 37), insert one-liner. Also add optional check for `INSTALL_SH` (line 37) — warn but don't exit if missing.
  - **Worker:** `mini`
  - **Token est:** ~2K
  - **Verify:** `PLAN_FILE` missing → exit 1; `INSTALL_SH` missing → warn, continue
  - **Gate:** M1, M3
  - **Evidence:** `.omo/ulw-loop/evidence/validate-input-guard-w2-e.txt`

- [ ] **task-F**: Add preflight to `validate-blackcow-governor-integration.sh`
  - **Action**: After `GOVERNOR_FILE="${SKILL_DIR}/blackcow-governor.md"` (line 38), insert one-liner
  - **Worker:** `mini`
  - **Token est:** ~2K
  - **Verify:** GOVERNOR_FILE missing → exit 1 + FATAL
  - **Gate:** M1, M3
  - **Evidence:** `.omo/ulw-loop/evidence/validate-input-guard-w2-f.txt`

- [ ] **task-G**: Add preflight to `validate-blackcow-governor-system.sh`
  - **Action**: After `GOVERNOR_FILE="${SKILLS_DIR}/blackcow-governor.md"` (line 35), insert one-liner for GOVERNOR_FILE only. Consumer skill files (plan/loop/qa) are checked lazily inside T4 block — no upfront check needed (per Reviewer C).
  - **Worker:** `mini`
  - **Token est:** ~2K
  - **Verify:** GOVERNOR_FILE missing → exit 1; consumer file missing → T4 tests fail (not preflight)
  - **Gate:** M1, M3
  - **Evidence:** `.omo/ulw-loop/evidence/validate-input-guard-w2-g.txt`

- [ ] **task-H**: Add preflight to `validate-cross-skill-contract.sh`
  - **Action**: After the 5 FILE variables (lines 34-38), add a loop that checks all 5 files. If ANY missing, print all missing paths and exit 1:
    ```bash
    MISSING=""
    for f in "$GOVERNOR_FILE" "$PLAN_FILE" "$LOOP_FILE" "$QA_FILE" "$LIBRARIAN_FILE"; do
      [[ -f "$f" ]] || MISSING="$MISSING  $f"$'\n'
    done
    [[ -z "$MISSING" ]] || { echo "FATAL: Target file(s) not found:"$'\n'"$MISSING" >&2; exit 1; }
    ```
  - **Worker:** `medium`
  - **Token est:** ~3K
  - **Verify:** Any of the 5 missing → exit 1 + list of all missing files
  - **Gate:** M1, M3
  - **Evidence:** `.omo/ulw-loop/evidence/validate-input-guard-w2-h.txt`

### Wave 3 — Ecosystem + Verification (2 tasks, serial on Wave 1+2, ≤20K tokens)

- [ ] **task-I**: Add graduated preflight to `validate-blackcow-ecosystem.sh`
  - **Action**: After the ALL_SKILLS loop (around line 52), add a check: count missing files. If ≥2 missing, exit 1 with FATAL listing all missing. If 1 missing, print WARNING to stderr and continue (ecosystem can be partially healthy). If 0 missing, proceed normally.
    ```bash
    MISSING_COUNT=0; MISSING_LIST=""
    for skill in "${ALL_SKILLS[@]}"; do
      [[ -f "${SKILLS_DIR}/${skill}" ]] || { MISSING_COUNT=$((MISSING_COUNT+1)); MISSING_LIST="$MISSING_LIST  ${SKILLS_DIR}/${skill}"$'\n'; }
    done
    if [[ "$MISSING_COUNT" -ge 2 ]]; then
      echo "FATAL: $MISSING_COUNT target skill files not found:"$'\n'"$MISSING_LIST" >&2; exit 1
    elif [[ "$MISSING_COUNT" -eq 1 ]]; then
      echo "WARNING: 1 target skill file not found (continuing with partial validation):"$'\n'"$MISSING_LIST" >&2
    fi
    ```
  - **Worker:** `medium`
  - **Token est:** ~3K
  - **Verify:** 2+ skills missing → exit 1; 1 skill missing → WARNING, continue; 0 missing → silent
  - **Gate:** M1, M3
  - **Evidence:** `.omo/ulw-loop/evidence/validate-input-guard-w3-i.txt`

- [ ] **task-J**: Minimal enhancement to `validate-blackcow-ecosystem-health.sh`
  - **Action**: In the failure details section (around line 371), add a check: if `parse_counts` returned 0/0/0 (total=0) and `local_exit` is non-zero, label the failure as "NOT FOUND (preflight guard)" in the failure details output. This is purely cosmetic — the existing logic already correctly counts this as a failure via the `total==0 → fail=1` fallback (line 136-138). No exit-code convention changes needed.
  - **Worker:** `mini`
  - **Token est:** ~2K
  - **Verify:** Run ecosystem-health with one script having a missing target → failure details show "NOT FOUND (preflight guard)"
  - **Gate:** M3
  - **Evidence:** `.omo/ulw-loop/evidence/validate-input-guard-w3-j.txt`

### Wave 4 — Validation (1 task, ≤10K tokens)

- [ ] **task-K**: Full regression + preflight verification
  - **Action**: 
    1. Run `bash skills/tests/validate-blackcow-ecosystem-health.sh` — all 10 scripts must pass with valid targets
    2. For each script with a CLI override (plan.sh, governor.sh): run with `/nonexistent` path → verify exit 1 + FATAL message
    3. For contract scripts: run from wrong directory → verify exit 1 + FATAL
    4. For cross-skill-contract.sh: temporarily rename one skill file → verify exit 1 + lists missing file
    5. For ecosystem.sh: temporarily rename 2 skill files → verify exit 1; rename 1 → verify WARNING but continues
    6. Verify ecosystem-health.sh correctly reports all results
  - **Worker:** `heavy`
  - **Token est:** ~5K
  - **Verify:** All checks pass as described above
  - **Gate:** M2 (test pass=100%), M3 (0 regressions)
  - **Evidence:** `.omo/ulw-loop/evidence/validate-input-guard-w4-k.txt`

## Risk Register (BKIT 11-Gate)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| Guard rejects valid path (false positive) | `M1_spec_match` | HIGH | 0 false positives | Use `[[ -f ]]` which handles symlinks, relative/absolute paths identically | Run all scripts with real targets |
| Missing target not detected (false negative) | `M1_spec_match` | HIGH | 0 false negatives | Guard placed immediately after TARGET definition, before any test logic | Test with `/nonexistent` path |
| Regression: existing tests break | `M3_regression` | MED | 0 regressions | Guard is additive only — no logic changes to assertions | Run ecosystem-health before/after |
| plan.sh/governor.sh no longer exit 0 on missing target | `M3_regression` | MED | New behavior is correct | These scripts always exited 0 even on failure — this was a bug, not a feature. ecosystem-health already handles non-zero exits via `|| local_exit=$?` | Verify ecosystem-health correctly reports failure |
| exit 1 collision with contract/integration scripts | `M3_regression` | LOW | No collision | Contract scripts already exit 1 on test failure. Guard fires BEFORE tests, so exit 1 from guard vs exit 1 from test failure is indistinguishable — both mean "script failed" which is correct | Run script with missing target, verify ecosystem-health reports FAIL |
| Path with spaces/special chars in target | `S1_dataFlow` | MED | All paths quoted | `"$TARGET"` is double-quoted in guard | Test with path containing spaces |
| ecosystem-health misclassifies guard failure | `M3_regression` | LOW | FAIL (not silent pass) | Existing fallback: `total==0 && local_exit!=0 → fail=1` | Verify ecosystem-health reports RED when a script's target is missing |
| HOMEDIR_SKILL (~/.reasonix) missing in contract scripts | `M1_spec_match` | LOW | Informational | Contract scripts already check homedir as separate test — failing this test is correct behavior, not a preflight concern | Existing test behavior preserved |
| Shellcheck warnings on new code | `M4_lint_clean` | LOW | 0 new warnings | All additions use POSIX constructs, no bashisms beyond existing level | `shellcheck skills/tests/*.sh` |

## Reviewer Findings Incorporated

| Reviewer | Finding | Disposition |
|---|---|---|
| A — Correctness | Exit code collision: exit 1 used by contract scripts | **Resolved**: Guard fires before any test logic, so exit 1 from guard is indistinguishable from exit 1 from test failure — both correctly signal "script failed" |
| A — Correctness | HOMEDIR_SKILL unguarded in contract scripts | **Accepted as minor**: Separate test assertion, not preflight concern |
| B — Security | S3 python3 -c injection not fixed — scope separation accepted | **Deferred**: Follow-up plan needed. Guard plan's S3 gate justification corrected |
| B — Security | TOCTOU: SAFE. Exit code: SAFE. Shebang: SAFE | **All accepted** |
| B — Security | Output poisoning via malicious filename: low risk | **Accepted**: Filenames come from version-controlled project directories |
| C — Feasibility | governor-system.sh: guard only GOVERNOR_FILE upfront, lazy for consumers | **Applied**: task-G only guards GOVERNOR_FILE |
| C — Feasibility | All 4 Wave-1 tasks truly parallel. No perf regression | **Accepted** |
| D — Architecture | Dual-path detection concern | **Resolved**: Guard's exit 1 flows through existing `total==0 → fail=1` fallback — single path |
| D — Architecture | 5 assert_file_exists copies already justify shared lib | **Deferred**: This plan is minimal; shared lib extraction would be a separate refactor |
| D — Architecture | ARCHITECTURE COHERENCE SCORE boosted from 38→72 after resolving dual-path | **Applied**: Clarified that no new detection channel is needed |
| E — Minimalism | 83% reduction: 12 tasks → 2 tasks equivalent | **Partially applied**: Reduced to 9 tasks (4 waves), removed unnecessary function abstractions, kept exit 1 (not 3) |
| E — Minimalism | One-liner suffices, no function needed | **Applied**: All guards use inline `[[ -f ]] \|\| { echo FATAL; exit 1; }` |
| E — Minimalism | plan-contract.sh + governor-contract.sh already have checks | **Applied**: tasks C+D only strengthen existing checks to early-exit |

## Execution Command

```
blackcow-loop "Execute plans/validate-input-guard.md" --completion-promise='All 10 validate scripts exit with clear FATAL message when target file missing; ecosystem-health correctly reports failures; no regression on valid targets' --trust-level=2
```

### Parallelism Guide
- Wave 1: dispatch 4 workers in parallel (tasks A-D, independent files)
- Wave 2: dispatch 4 workers in parallel (tasks E-H, independent files)
- Wave 3: 2 workers sequentially (task-I → task-J, ecosystem-health depends on all guards being in place)
- Wave 4: 1 worker (task-K, comprehensive verification)
- Total budget: ~45K / 128K target
