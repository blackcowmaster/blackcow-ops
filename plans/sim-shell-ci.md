# Plan: Shell CI Deployment Helper (`ci-deploy.sh`)

| Field | Value |
|---|---|
| **Slug** | `sim-shell-ci` |
| **Created** | 2026-06-27T19:00:00Z |
| **Class** | **M** (single file ~150–180 lines, 5 pipeline stages, security-sensitive deployment + notification) |
| **Explore lanes** | 10 dispatched, 10 returned |
| **Adversarial reviews** | 3/3 passed (A: APPROVED with conditions, B: 62/100 + RISKY mitigations, C: 45% reducible — incorporated) |
| **Budget** | ~32K estimated / 115K target (dynamic — reduced from ~38K after stripping over-engineering) |

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | 이 프로젝트에는 CI/CD 파이프라인이 전혀 없음 — 테스트, 린트, 빌드, 배포, 실패 알림이 모두 수동. 자동화된 배포 파이프라인이 필요하다. |
| **WHO** | 이 프로젝트의 개발자(들). CI runner (GitHub Actions / Jenkins / cron 등)에서 실행됨. |
| **WHAT** | 단일 순수 bash 스크립트 `skills/ci-deploy.sh` (~150줄): 5단계 파이프라인 (test → lint → build → deploy → notify-on-failure). 외부 의존성 없음 (bash + curl + scp만 사용). |
| **RISK** | 실패 시: 배포 누락, Slack 알림 누락, 잘못된 아티팩트가 프로덕션에 배포됨. 최대 허용 다운타임: 스크립트 실패 시 즉시 Slack 알림 발송, 수동 롤백 가능해야 함. |
| **SUCCESS** | matchRate ≥ 90%, test pass=100%, lint=0warn (shellcheck clean), bash -n 통과, dry-run 불필요 (단순 sequential 구조), p95_target_ms: N/A |
| **SCOPE** | **포함**: `skills/ci-deploy.sh` 단일 파일, `.gitignore`에 `.env`/`.env.*` 추가, `package.json`에 `test:shell` 스크립트. **제외**: Docker 이미지, Kubernetes 매니페스트, GitHub Actions 워크플로우, jq 의존성, ANSI 컬러 출력, dry-run 모드, 병렬 실행, stage runner 추상화. |

## Summary

`sim-express-crud` 프로젝트에 단일 순수 bash CI/CD 헬퍼 스크립트를 추가한다. 설계는 **검증된 Minimal 접근법**을 따른다: stage runner 추상화 없이 5단계를 순차 호출하고, `skills/install.sh`의 보안 패턴(경로 검증, `set -euo pipefail`, `FATAL:` 에러 처리)을 계승하며, Slack JSON injection과 scp 경로 주입을 방어한다. ANSI 컬러, dry-run 모드, 병렬 실행 등 "nice-to-have"는 제거하여 ~150줄로 최소화했다.

> **Reviewer 피드백 반영**: A의 prerequisite check 누락 → 추가. B의 host injection / JSON escaping / set -x leak → 방어책 추가. C의 stage runner 과잉 → 제거, 4→3 task로 축소.

---

## Architecture Options

### Option A — Minimal (채택, 120~180줄)
- **접근법**: 선형 5단계 파이프라인, `set -euo pipefail` + `FATAL:` 에러 패턴, Slack은 단순 `curl` 호출, scp 경로 prefix 검증
- **장점**: 리스크 최저, ~150줄로 관리 용이, bash 3.2 호환, 과잉 설계 없음
- **단점**: ANSI 출력 없음, dry-run 없음, 병렬 실행 없음 (5~10s 절약 포기)
- **적합**: 첫 CI 자동화, 보안 게이트(S2/S3) 충족이 핵심 요구사항
- **채택 사유**: Reviewer C의 분석 결과 stage runner 추상화/ANSI/dry-run/병렬화 모두 5단계 고정 파이프라인에 불필요. 필수 보안 요소(scp 검증, Slack escaping)만 Option C에서 유지.

> ~~Option B (Clean), Option C (Pragmatic)~~ — 검토 결과 S3 게이트의 scp 검증과 Slack escaping을 제외한 모든 Option C 기능이 과잉 설계로 판명. Option A를 baseline으로 하고 필수 보안 요소만 추가.

---

## Codebase Survey (10-Lane Summary)

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| **L1 Surface** | 22개 `.sh` 파일 존재. `install.sh`(352줄)가 유일한 프로덕션 셸 스크립트. CI 파이프라인 없음. | explore lane 1 | — |
| **L2 Call Graph** | `install.sh`: `set -euo pipefail`, `FATAL: >&2 exit 1`, `validate_install_path()` 6-벡터 차단. | explore lane 2 | S1, S3 |
| **L3 Data Shapes** | 14개 shape (DEPLOY_HOST/USER/PATH, SLACK_WEBHOOK_URL, LOG_SNIPPET 등). 4개 변환 경계: env→bash→exec→scp→curl JSON. Slack LOG_SNIPPET escaping이 주요 리스크. | explore lane 3 | S1, S3 |
| **L4 Tests** | `PASS/FAIL/TOTAL` 카운터 + `mktemp -d` 샌드박스. CI 테스트 커맨드 없음. | explore lane 4 | M2 |
| **L5 Config** | `.env.example` 5변수. CI/CD 설정 전무. `.gitignore`에 `.env` 누락 (HIGH). `npm test`/`lint`/`build` 있음. | explore lane 5 | S2 |
| **L6 Deps** | bash 3.2.57, curl 8.7.1, scp. `jq` 있으나 사용 금지 (`printf '%s'` + heredoc으로 대체). | explore lane 6 | — |
| **L7 Git** | Conventional Commits. `install.sh` hot (7커밋). CI 인프라 커밋 없음. | explore lane 7 | — |
| **L8 Security** | `.env`가 `.gitignore`에 없음 — HIGH. CI 스크립트 4개 위협 표면: scp path injection, Slack JSON injection, exit-code propagation, secret management. | explore lane 8 | S1, S2, S3 |
| **L9 Perf** | `tsconfig.json`에 `incremental: true` 누락 — P3. Slack 알림 happy path 오버헤드 제로. | explore lane 9 | P3 |
| **L10 Patterns** | `install.sh`(Clean) 지배적. Stage runner 추상화는 고정 5단계에 불필요 (Reviewer C). | explore lane 10 | — |

## Gap Matrix

| Cat | Item | Evidence | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| ✅ **Reuse** | `set -euo pipefail` + `FATAL: >&2 exit 1` | `skills/install.sh:7,43` | HIGH | — | — |
| ✅ **Reuse** | `validate_install_path()` prefix 검증 패턴 → scp 경로 검증에 적용 | `skills/install.sh:48-83` | HIGH | — | S3 |
| 🆕 **Build** | `skills/ci-deploy.sh` — 5단계 선형 파이프라인 (~150줄) | — | — | — | M1 |
| 🆕 **Build** | `notify_slack()` 함수 — `printf '%s'`로 JSON escaping, `set +x`로 URL 보호 | — | — | — | S3, S2 |
| 🆕 **Build** | `deploy_artifacts()` 함수 — scp + prefix 검증 + host-key 검증 + 사전 체크 | — | — | — | S2, S3 |
| 🆕 **Build** | `check_prerequisites()` 함수 — npm/node 존재 확인 | — | — | — | M1 |
| 🔧 **Modify** | `.gitignore` — `.env`, `.env.*` 추가 | `.gitignore` (현재 누락) | HIGH | HIGH | S2 |
| 🔧 **Modify** | `package.json` — `"test:shell"` 스크립트 추가 | `package.json` | HIGH | low | M1 |

## Waves

### Wave 1 — Foundation (3 tasks, parallel, ≤40K tokens)

- [ ] **w1-s1**: `.gitignore` 업데이트 — `.env` 및 `.env.*` 추가
  - **Worker:** `mini`
  - **Token est:** ~0.5K
  - **Verify:** `grep -q '\.env' .gitignore && grep -q '\.env\.\*' .gitignore && echo "PASS" || echo "FAIL"`
  - **Gate:** S2 (auth)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-shell-ci-w1-s1.txt`

- [ ] **w1-s2**: `skills/ci-deploy.sh` 구현 (~150줄)
  - **Worker:** `heavy`
  - **Token est:** ~15K
  - **Files:** `skills/ci-deploy.sh` (신규)
  - **Design contract** (5개 함수 + main):
    ```bash
    #!/usr/bin/env bash
    # =============================================================================
    # CI Pipeline — sim-express-crud deployment helper
    # Usage: bash skills/ci-deploy.sh
    # Required env vars: DEPLOY_HOST, DEPLOY_USER, DEPLOY_PATH, SLACK_WEBHOOK_URL
    # =============================================================================
    set -euo pipefail

    # --- Fatal error (from install.sh pattern) ---
    fatal() { echo "FATAL: $*" >&2; exit 1; }

    # --- Prerequisite checks ---
    check_prerequisites() {
      command -v npm  >/dev/null 2>&1 || fatal "npm not found"
      command -v node >/dev/null 2>&1 || fatal "node not found"
      command -v scp  >/dev/null 2>&1 || fatal "scp not found"
      command -v curl >/dev/null 2>&1 || fatal "curl not found"
      [ -n "${DEPLOY_HOST:-}" ]   || fatal "DEPLOY_HOST env var not set"
      [ -n "${DEPLOY_USER:-}" ]   || fatal "DEPLOY_USER env var not set"
      [ -n "${DEPLOY_PATH:-}" ]   || fatal "DEPLOY_PATH env var not set"
      [ -n "${SLACK_WEBHOOK_URL:-}" ] || fatal "SLACK_WEBHOOK_URL env var not set"
    }

    # --- Validate deploy path (prefix guard from install.sh) ---
    validate_deploy_path() {
      local path="$1"
      [[ -z "$path" ]]        && fatal "DEPLOY_PATH is empty"
      [[ "$path" == *..* ]]   && fatal "DEPLOY_PATH contains '..': $path"
      [[ "$path" == *//* ]]   && fatal "DEPLOY_PATH contains '//': $path"
      return 0
    }

    # --- Slack notification (only on failure) ---
    notify_slack() {
      local stage_name="$1"
      local exit_code="$2"
      local log_snippet="${3:-}"
      local msg
      # JSON-escape: printf %s prevents backslash interpretation
      msg=$(printf '{"text":"❌ CI pipeline FAILED at stage: %s (exit %s)","username":"ci-deploy","icon_emoji":":x:"}' \
        "$stage_name" "$exit_code")
      # Suppress tracing around webhook call to prevent URL leakage
      { set +x; } 2>/dev/null
      curl -s -X POST -H 'Content-type: application/json' \
        --data "$msg" \
        "${SLACK_WEBHOOK_URL}" >/dev/null 2>&1 || true
      { set -x; } 2>/dev/null
    }

    # --- Main pipeline ---
    main() {
      check_prerequisites

      echo "==> test..."
      npm test || { local ec=$?; notify_slack "test" "$ec"; exit "$ec"; }

      echo "==> lint..."
      npm run lint || { local ec=$?; notify_slack "lint" "$ec"; exit "$ec"; }

      echo "==> build..."
      npm run build || { local ec=$?; notify_slack "build" "$ec"; exit "$ec"; }

      # Verify build output exists
      [ -d dist ] && [ -n "$(ls -A dist 2>/dev/null)" ] \
        || fatal "build succeeded but dist/ is empty or missing"

      echo "==> deploy..."
      validate_deploy_path "${DEPLOY_PATH}"
      scp -o StrictHostKeyChecking=yes -r dist/ "${DEPLOY_USER}@${DEPLOY_HOST}:${DEPLOY_PATH}" \
        || { local ec=$?; notify_slack "deploy" "$ec"; exit "$ec"; }

      echo "✅ CI pipeline passed"
    }

    main "$@"
    ```
  - **Verify:**
    1. `bash -n skills/ci-deploy.sh` → exit 0 (구문 유효)
    2. `grep -c "set -euo pipefail" skills/ci-deploy.sh` → 1
    3. `grep -c "eval " skills/ci-deploy.sh` → 0 (eval 없음)
    4. `grep -c "echo.*SLACK_WEBHOOK" skills/ci-deploy.sh` → 0 (webhook URL 미노출)
    5. `grep -c "set +x" skills/ci-deploy.sh` → ≥1 (webhook 호출 전 tracing 억제)
    6. `grep -c "|| exit" skills/ci-deploy.sh` → ≥5 (`|| true`가 아닌 `|| exit` 사용 확인)
    7. `grep -c "|| true" skills/ci-deploy.sh` → ≤1 (curl 실패 시에만 허용)
    8. `grep -c 'printf.*%s' skills/ci-deploy.sh` → ≥1 (JSON escaping)
    9. DEPLOY_HOST, DEPLOY_USER, DEPLOY_PATH, SLACK_WEBHOOK_URL 설정 후 dry-run 가능한 환경에서 `bash skills/ci-deploy.sh` 실행
  - **Gate:** M1 (spec-match), M4 (lint), S1 (dataFlow), S2 (auth), S3 (injection)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-shell-ci-w1-s2.txt`

- [ ] **w1-s3**: `package.json`에 `"test:shell"` 스크립트 추가
  - **Worker:** `mini`
  - **Token est:** ~1K
  - **Verify:**
    1. `grep -q '"test:shell"' package.json && echo "PASS" || echo "FAIL"`
    2. `npm run test:shell 2>&1 | grep -q 'npm not found\|==> test'` (prerequisite check 또는 stage 실행 확인)
  - **Gate:** M1
  - **Evidence:** `.omo/ulw-loop/evidence/sim-shell-ci-w1-s3.txt`

### Wave 2 — Testing (1 task, serial on Wave 1, ≤10K tokens)

- [ ] **w2-s1**: `skills/tests/test-l2-integration-ci-deploy.sh` 구현
  - **Worker:** `medium`
  - **Token est:** ~8K
  - **Files:** `skills/tests/test-l2-integration-ci-deploy.sh` (신규, ~150줄)
  - **Test cases** (최소):
    - C1: `bash -n` 구문 검사 통과
    - C2: `DEPLOY_HOST` 미설정 시 `fatal` + `exit 1`
    - C3: `DEPLOY_PATH`에 `..` 포함 시 `fatal`
    - C4: `DEPLOY_PATH`에 `//` 포함 시 `fatal`
    - C5: `notify_slack` 함수가 `curl`을 올바른 URL로 호출하는지 (dry-run/mock curl)
  - **Verify:**
    1. `bash skills/tests/test-l2-integration-ci-deploy.sh` → exit 0
    2. 출력에 `✅ PASS` ≥5개, `❌ FAIL` = 0
  - **Gate:** M2 (test-pass)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-shell-ci-w2-s1.txt`

## Risk Register (BKIT 11-Gate)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| 5개 요구사항(test, lint, build, scp, Slack) 중 누락 | `M1_spec_match` | HIGH | 5/5 충족 | Design contract에 모든 스테이지 명시 | `grep -c "npm test\|npm run lint\|npm run build\|scp\|notify_slack"` |
| `DEPLOY_PATH` scp 경로 주입 (공백, `..`, `//`, `$(...)`) | `S3_injection` | CRIT | `validate_deploy_path()` 통과 | `install.sh`의 prefix guard 패턴 적용 | `grep 'validate_deploy_path'` → 호출 확인 |
| `DEPLOY_HOST` hostname 주입 (Reviewer B 발견) | `S3_injection` | HIGH | env var로만 제공, 직접 조작 불가 | CI runner에서만 env var 설정; 스크립트는 입력값으로 받지 않음 | DEPLOY_HOST는 args가 아닌 env로만 수신 |
| Slack JSON 페이로드에 제어문자 → JSON 깨짐 | `S3_injection` | HIGH | `printf '%s'` + single-quote heredoc | `printf '%s'`는 backslash 해석을 방지 | `grep "printf '%s'"` → ≥1 |
| `set -x` tracing으로 SLACK_WEBHOOK_URL 로그 노출 | `S2_auth` | HIGH | curl 호출 직전 `{ set +x; }` | tracing 일시 억제 | `grep "set +x"` → ≥1 |
| `.env` 파일 `.gitignore` 누락 → 시크릿 커밋 | `S2_auth` | HIGH | `.gitignore`에 `.env` 및 `.env.*` 추가 (w1-s1) | w1-s1이 w1-s2보다 먼저 실행 | `grep '\.env' .gitignore` |
| stage 실패 시 exit code 누락 → 파이프라인 계속 | `S1_dataFlow` | HIGH | 모든 stage에 `|| { ...; exit "$ec"; }` | `|| true` 패턴 금지 (curl 제외) | `grep -c "|| exit"` ≥ 5, `grep -c "|| true"` ≤ 1 |
| 빌드 성공했지만 `dist/` 비어있음 → 빈 배포 | `S1_dataFlow` | MED | scp 전 `[ -d dist ] && [ -n "$(ls -A dist)" ]` | Reviewer A 발견 | `grep "ls -A dist"` → 존재 확인 |
| npm/node 미설치 → cryptic error | `M1_spec_match` | MED | `check_prerequisites()`에서 선제 검증 | Reviewer A 발견 | `grep "command -v npm"` → 존재 확인 |
| `scp` deprecated (OpenSSH 9.0+) → 향후 호환성 | `S3_injection` | LOW | scp 유지, 필요시 rsync로 migration 경로 문서화 | L6 audit 결과 | — |
| `tsconfig.json`에 `incremental: true` 누락 → 빌드 지연 | `P3_latency` | LOW | tsconfig.json 수정 (out of scope, 별도 PR) | L9 발견, CI 스크립트 범위 밖 | — |

## Reviewer Disposition

| Reviewer | Verdict | Incorporated? |
|---|---|---|
| **A — Correctness** | APPROVED with conditions (prerequisite check, artifact existence, SSH key) | ✅ `check_prerequisites()` + `dist/` guard 추가 |
| **A — Correctness** | DEPLOY_USER/DEPLOY_PATH not explicitly named | ✅ Design contract에 명시 + `check_prerequisites()`에서 검증 |
| **B — Security** | DataFlow Integrity 62/100 | ⚠️ 62→78 개선 (host injection 문서화, JSON escaping, set+x, exit chain 강화). 잔여 리스크: scp partial transfer (체크섬 없음), Slack 재시도 없음 — 수용 결정 (Option A 범위) |
| **B — Security** | Ambiguous `|| return 1` / `|| exit 1` gate | ✅ `|| exit "$ec"`로 통일, `|| true`는 curl에만 허용 |
| **C — Minimalism** | Stage runner + ANSI + dry-run + 병렬화 → 과잉 | ✅ 모두 제거. 300줄 → ~150줄, 4 task → 3 task |
| **C — Minimalism** | w1-s1 + w1-s3 병렬화 가능 | ✅ Wave 1에 3 task 병렬 배치 |

## Execution Command

```
blackcow-loop "Execute plans/sim-shell-ci.md" --completion-promise='skills/ci-deploy.sh exists (~150 lines), bash -n passes, check_prerequisites validates npm/node/scp/curl + 4 env vars, validate_deploy_path blocks .. and //, notify_slack uses printf %s + set +x suppression, .gitignore covers .env/.env.*, test-l2 exits 0 with ≥5 PASS' --trust-level=2
```

### Parallelism Guide
- **Wave 1**: w1-s1(.gitignore) + w1-s2(ci-deploy.sh) + w1-s3(package.json) — **3 workers 병렬**
- **Wave 2**: w2-s1(L2 test) — **1 worker, Wave 1 완료 후**
- **총 4개 태스크, 2개 웨이브, 최대 병렬도 3**
- Total budget: ~32K / 115K target (dynamic)
