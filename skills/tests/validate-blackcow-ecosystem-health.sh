#!/usr/bin/env bash
# ============================================================================
# validate-blackcow-ecosystem-health.sh — Unified Health Report Runner
#
# Runs ALL validate-*.sh scripts in skills/tests/ (excluding itself) and
# produces a unified health report with:
#   • Per-script pass/fail/skip counts and score percentage
#   • A traffic-light summary (RED / YELLOW / GREEN)
#   • Aggregate ecosystem health score
#   • Detailed failure listing for any script that doesn't pass cleanly
#
# Usage:
#   bash skills/tests/validate-blackcow-ecosystem-health.sh
#   bash skills/tests/validate-blackcow-ecosystem-health.sh --json     # machine-readable
#   bash skills/tests/validate-blackcow-ecosystem-health.sh --verbose  # stream sub-script output live
#   bash skills/tests/validate-blackcow-ecosystem-health.sh --quiet    # summary only
#   bash skills/tests/validate-blackcow-ecosystem-health.sh --summary  # 80-char Unicode box-drawing compact report
#
# Exit code: 0 if GREEN, 1 if YELLOW, 2 if RED
# ============================================================================

set -euo pipefail

# --- Config -----------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$SKILLS_DIR/.." && pwd)"
REPORT_DIR="${PROJECT_ROOT}/.omo/governor"
HEALTH_LOG="${REPORT_DIR}/ecosystem-health-report.txt"
HEALTH_JSON="${REPORT_DIR}/ecosystem-health-report.json"

JSON_OUT=false
VERBOSE=false
QUIET=false
SUMMARY_OUT=false
TIMEOUT_SEC=120  # per-script timeout
START_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)
START_EPOCH=$(date +%s)

# Scripts run from PROJECT_ROOT because many validate-*.sh use relative paths
# like "skills/blackcow-governor.md" that resolve from the project root.
cd "$PROJECT_ROOT"

for arg in "$@"; do
  case "$arg" in
    --json)    JSON_OUT=true; VERBOSE=false ;;
    --verbose) VERBOSE=true ;;
    --quiet)   QUIET=true ;;
    --summary) SUMMARY_OUT=true ;;
  esac
done

# --- JSON mode: suppress all normal stdout ---
if $JSON_OUT; then
  exec 3>&1 1>/dev/null
fi

# --- Color helpers -----------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# --- State ------------------------------------------------------------------
declare -a SCRIPT_NAMES=()
declare -a SCRIPT_PASS=()
declare -a SCRIPT_FAIL=()
declare -a SCRIPT_SKIP=()
declare -a SCRIPT_TOTAL=()
declare -a SCRIPT_SCORE=()
declare -a SCRIPT_EXIT=()
declare -a SCRIPT_DURATION=()
declare -a SCRIPT_ERRORS=()

OVERALL_PASS=0
OVERALL_FAIL=0
OVERALL_SKIP=0
OVERALL_TOTAL=0
SCRIPTS_RUN=0
SCRIPTS_PASSED=0
SCRIPTS_FAILED=0

# --- Helpers -----------------------------------------------------------------
# In --summary mode, suppress info/ok like --quiet (the box is the output).
_quiet_or_summary() { $QUIET || $SUMMARY_OUT; }
log_info()  { _quiet_or_summary || echo -e "  ${CYAN}ℹ${NC}  $*"; }
log_ok()    { _quiet_or_summary || echo -e "  ${GREEN}✅${NC} $*"; }
log_warn()  { echo -e "  ${YELLOW}⚠️${NC}  $*"; }
log_err()   { echo -e "  ${RED}❌${NC} $*"; }
header()    { echo ""; echo -e "${BOLD}━━━ $* ━━━${NC}"; }

# ---------------------------------------------------------------------------
# Strip ANSI escape codes. Reads from $1 if given, otherwise reads stdin
# (pipe-compatible). Handles empty input gracefully.
# ---------------------------------------------------------------------------
strip_ansi() {
  if [[ $# -gt 0 ]] && [[ -n "${1:-}" ]]; then
    echo "${1}" | sed 's/\x1b\[[0-9;]*[a-zA-Z]//g'
  elif [[ ! -t 0 ]]; then
    sed 's/\x1b\[[0-9;]*[a-zA-Z]//g'
  else
    echo ""
  fi
}

# Safely extract an integer from grep output. Handles multi-line, empty, and
# ANSI-polluted results. Returns 0 if nothing found.
safe_int() {
  local val
  local input="${1:-}"
  if [[ -z "$input" ]]; then
    echo "0"
    return
  fi
  val=$(echo "$input" | strip_ansi | grep -oE '[0-9]+' | head -1 2>/dev/null || true)
  val="${val:-0}"
  if [[ "$val" =~ ^[0-9]+$ ]]; then
    echo "$val"
  else
    echo "0"
  fi
}

# Parse pass/fail/skip from a script's stdout.
parse_counts() {
  local output="${1:-}"
  local clean pass fail skip total

  if [[ -z "$output" ]]; then
    echo "0 0 0 0"
    return
  fi

  clean=$(strip_ansi "$output")

  # Pattern 1: "Results: N passed, N failed, N skipped (total N checks)"
  if echo "$clean" | grep -qE "Results:.*passed.*failed.*skipped" 2>/dev/null; then
    pass=$(echo "$clean" | grep -oE '[0-9]+ passed' | head -1 | grep -oE '[0-9]+' || echo "0")
    fail=$(echo "$clean" | grep -oE '[0-9]+ failed' | head -1 | grep -oE '[0-9]+' || echo "0")
    skip=$(echo "$clean" | grep -oE '[0-9]+ skipped' | head -1 | grep -oE '[0-9]+' || echo "0")
    total=$((pass + fail + skip))
    echo "$pass $fail $skip $total"
    return
  fi

  # Pattern 2: "Total tests: N" with "Passed:" / "Failed:"
  if echo "$clean" | grep -qE "Total tests: +[0-9]+" 2>/dev/null; then
    total=$(safe_int "$(echo "$clean" | grep -E 'Total tests:' | tail -1 || true)")
    pass=$(safe_int "$(echo "$clean" | grep -E 'Passed:' | tail -1 || true)")
    fail=$(safe_int "$(echo "$clean" | grep -E 'Failed:' | tail -1 || true)")
    skip=$((total - pass - fail))
    [[ "$skip" -lt 0 ]] && skip=0
    echo "$pass $fail $skip $total"
    return
  fi

  # Pattern 3: "Passed: N" / "Failed: N" (integration/contract style)
  if echo "$clean" | grep -qE "Passed: +[0-9]+" 2>/dev/null; then
    pass=$(safe_int "$(echo "$clean" | grep -E 'Passed:' | tail -1 || true)")
    fail=$(safe_int "$(echo "$clean" | grep -E 'Failed:' | tail -1 || true)")
    total=$((pass + fail))
    skip=0
    echo "$pass $fail $skip $total"
    return
  fi

  # Pattern 4: "Results: N passed, N failed" (simpler format)
  if echo "$clean" | grep -qE "Results:.*passed.*failed" 2>/dev/null; then
    pass=$(safe_int "$(echo "$clean" | grep -oE '[0-9]+ passed' | head -1 || true)")
    fail=$(safe_int "$(echo "$clean" | grep -oE '[0-9]+ failed' | head -1 || true)")
    total=$((pass + fail))
    skip=0
    echo "$pass $fail $skip $total"
    return
  fi

  # Pattern 5: PASS/FAIL line counters (ecosystem/system tests)
  local p f
  p=$(echo "$clean" | grep -cE '^[[:space:]]*(PASS|✅[[:space:]]*PASS)' 2>/dev/null || true)
  f=$(echo "$clean" | grep -cE '^[[:space:]]*(FAIL|❌[[:space:]]*FAIL)' 2>/dev/null || true)
  p=$(safe_int "$p")
  f=$(safe_int "$f")
  if [[ "$p" -gt 0 || "$f" -gt 0 ]]; then
    pass=$p
    fail=$f
    total=$((pass + fail))
    skip=0
    echo "$pass $fail $skip $total"
    return
  fi

  echo "0 0 0 0"
}

# ---------------------------------------------------------------------------
# print_summary_box — 80-char Unicode box-drawing compact report
#
# Layout (every line exactly 80 chars):
#   ┌─ 78×─ ─┐   top border
#   │  title + timestamp (right-aligned)    │
#   ├─ 78×─ ─┤   header separator
#   │  %-45s %24s       │   per-script rows
#   ├─ 78×─ ─┤   footer separator
#   │  AGGREGATE line                        │
#   └─ 78×─ ─┘   bottom border
#
# Tension resolution for script names > 45 chars:
#   Name takes its own full-width line; stats follow on an indented line.
# ---------------------------------------------------------------------------
print_summary_box() {
  local BAR   # 78 '─' characters (Unicode box-drawing horizontal)
  BAR=$(printf '%-78s' '' | tr ' ' '─')

  # ---- per-script status label -------------------------------------------
  _status_label() {
    local f="$1" s="$2"
    if [[ "$f" -eq 0 && "$s" -eq 0 ]]; then echo "PASS"
    elif [[ "$f" -eq 0 ]]; then echo "WARN"
    else echo "FAIL"
    fi
  }

  # ---- aggregate status label (no emoji — pure ASCII inside box) ---------
  _agg_label() {
    case "$TRAFFIC" in
      GREEN)  echo "GREEN"  ;;
      YELLOW) echo "YELLOW" ;;
      RED)    echo "RED"    ;;
    esac
  }

  # ---- stats string: "P:XX F:XX S:XX XXX% XXXX" (exactly 27 chars) ------
  _stats_str() {
    local p="$1" f="$2" s="$3" sc="$4" st="$5"
    printf "P:%3d F:%3d S:%3d %3d%% %-4s" "$p" "$f" "$s" "$sc" "$st"
  }

  # ---- print one per-script row ------------------------------------------
  _script_row() {
    local name="$1" p="$2" f="$3" s="$4" sc="$5"
    local st stats
    st=$(_status_label "$f" "$s")
    stats=$(_stats_str "$p" "$f" "$s" "$sc" "$st")

    local name_len=${#name}
    if [[ "$name_len" -le 45 ]]; then
      # Fits on one line: │ %-45s %27s    │  (80 chars)
      printf "│ %-45s %27s    │\n" "$name" "$stats"
    else
      # Overflow guard: name on its own line, stats indented below
      printf "│ %-78s │\n" "$name"
      printf "│   %27s                                                    │\n" "$stats"
    fi
  }

  # ---- top border --------------------------------------------------------
  printf "┌%s┐\n" "$BAR"

  # ---- title row ---------------------------------------------------------
  local title="BlackCow Ecosystem Health Summary"
  local ts
  ts=$(date -u +"%Y-%m-%d %H:%M UTC")
  local rhs="${ts}"
  local lhs_len=${#title}
  local rhs_len=${#rhs}
  local pad=$((76 - lhs_len - rhs_len))
  [[ "$pad" -lt 1 ]] && pad=1
  local padding
  padding=$(printf '%*s' "$pad" '')
  printf "│ %s%s%s │\n" "$title" "$padding" "$rhs"

  # ---- header separator --------------------------------------------------
  printf "├%s┤\n" "$BAR"

  # ---- per-script rows ---------------------------------------------------
  for i in "${!SCRIPT_NAMES[@]}"; do
    _script_row \
      "${SCRIPT_NAMES[$i]}" \
      "${SCRIPT_PASS[$i]}" \
      "${SCRIPT_FAIL[$i]}" \
      "${SCRIPT_SKIP[$i]}" \
      "${SCRIPT_SCORE[$i]}"
  done

  # ---- footer separator --------------------------------------------------
  printf "├%s┤\n" "$BAR"

  # ---- aggregate row -----------------------------------------------------
  local agg_label ag_stats
  agg_label=$(_agg_label)
  ag_stats=$(_stats_str "$OVERALL_PASS" "$OVERALL_FAIL" "$OVERALL_SKIP" "$AGGREGATE_SCORE" "$agg_label")
  printf "│ %-45s %27s    │\n" "AGGREGATE" "$ag_stats"

  # ---- bottom border -----------------------------------------------------
  printf "└%s┘\n" "$BAR"
}

# --- Find all validate scripts ----------------------------------------------
SCRIPTS=()
while IFS= read -r -d '' f; do
  basename=$(basename "$f")
  [[ "$basename" == "validate-blackcow-ecosystem-health.sh" ]] && continue
  SCRIPTS+=("$f")
done < <(find "$SCRIPT_DIR" -maxdepth 1 -name 'validate-*.sh' -print0 2>/dev/null | sort -z)

if [[ ${#SCRIPTS[@]} -eq 0 ]]; then
  echo "ERROR: No validate-*.sh scripts found in $SCRIPT_DIR"
  exit 2
fi

# --- Header -----------------------------------------------------------------
if ! $SUMMARY_OUT; then
  echo "╔══════════════════════════════════════════════════════════════════╗"
  echo "║       BlackCow Ecosystem Health Report                          ║"
  echo "║       $(date -u +%Y-%m-%d\ %H:%M:%S\ UTC)                              ║"
  echo "║       Project: $(basename "$PROJECT_ROOT")                                          ║"
  echo "╚══════════════════════════════════════════════════════════════════╝"
fi

# --- Run all scripts --------------------------------------------------------
if ! $SUMMARY_OUT; then
  header "Running ${#SCRIPTS[@]} Validation Scripts"
fi

for script_path in "${SCRIPTS[@]}"; do
  script_name=$(basename "$script_path")
  SCRIPT_NAMES+=("$script_name")

  log_info "Running: $script_name ..."

  script_start=$(date +%s)
  local_output=""
  local_exit=0

  if $VERBOSE; then
    echo "  ── ${script_name} output ──"
    bash "$script_path" 2>&1 || local_exit=$?
    echo "  ── end ${script_name} ──"
    local_output="[streamed — see above]"
  else
    local_output=$(bash "$script_path" 2>&1) || local_exit=$?
  fi

  script_end=$(date +%s)
  duration=$((script_end - script_start))

  pass=0; fail=0; skip=0; total=0
  if ! $VERBOSE; then
    read -r pass fail skip total < <(parse_counts "$local_output")
  else
    if [[ "$local_exit" -eq 0 ]]; then pass=1; total=1; else fail=1; total=1; fi
  fi

  pass=$(safe_int "$pass")
  fail=$(safe_int "$fail")
  skip=$(safe_int "$skip")
  total=$((pass + fail + skip))

  if [[ "$total" -eq 0 ]]; then
    if [[ "$local_exit" -eq 0 ]]; then pass=1; total=1; else fail=1; total=1; fi
  fi

  score=0
  if [[ "$total" -gt 0 ]]; then
    score=$(awk "BEGIN {printf \"%.0f\", ($pass / $total) * 100}")
  fi

  SCRIPT_PASS+=("$pass")
  SCRIPT_FAIL+=("$fail")
  SCRIPT_SKIP+=("$skip")
  SCRIPT_TOTAL+=("$total")
  SCRIPT_SCORE+=("$score")
  SCRIPT_EXIT+=("$local_exit")
  SCRIPT_DURATION+=("$duration")

  OVERALL_PASS=$((OVERALL_PASS + pass))
  OVERALL_FAIL=$((OVERALL_FAIL + fail))
  OVERALL_SKIP=$((OVERALL_SKIP + skip))
  OVERALL_TOTAL=$((OVERALL_TOTAL + total))
  SCRIPTS_RUN=$((SCRIPTS_RUN + 1))

  if [[ "$fail" -eq 0 ]]; then
    SCRIPTS_PASSED=$((SCRIPTS_PASSED + 1))
  else
    SCRIPTS_FAILED=$((SCRIPTS_FAILED + 1))
  fi

  if [[ "$fail" -eq 0 && "$skip" -eq 0 ]]; then
    log_ok "$script_name — ${score}% (${pass}/${total}) — ${duration}s"
  elif [[ "$fail" -eq 0 ]]; then
    log_warn "$script_name — ${score}% (${pass}/${total}, ${skip} skipped) — ${duration}s"
  else
    log_err "$script_name — ${score}% (${pass}/${total}, ${fail} failed) — ${duration}s"
    if ! $VERBOSE; then
      flines=$(echo "$local_output" | strip_ansi | grep -E '(FAIL|❌ FAIL)' | head -3 || true)
      SCRIPT_ERRORS+=("$flines")
    else
      SCRIPT_ERRORS+=("[see output above]")
    fi
  fi
done

# --- Aggregate Score ---------------------------------------------------------
if [[ "$OVERALL_TOTAL" -gt 0 ]]; then
  AGGREGATE_SCORE=$(awk "BEGIN {printf \"%.0f\", ($OVERALL_PASS / $OVERALL_TOTAL) * 100}")
else
  AGGREGATE_SCORE=0
fi

# --- Traffic Light -----------------------------------------------------------
TRAFFIC="GREEN"
TRAFFIC_LABEL="🟢 GREEN — Ecosystem Healthy"
EXIT_CODE=0

if [[ "$OVERALL_FAIL" -gt 0 ]]; then
  TRAFFIC="RED"
  TRAFFIC_LABEL="🔴 RED — Failures Detected"
  EXIT_CODE=2
elif [[ "$OVERALL_SKIP" -gt 0 ]] || [[ "$SCRIPTS_FAILED" -gt 0 ]]; then
  TRAFFIC="YELLOW"
  TRAFFIC_LABEL="🟡 YELLOW — Warnings / Skips Present"
  EXIT_CODE=1
fi

# --- Write report files (always, even in --summary mode) --------------------
mkdir -p "$REPORT_DIR"

{
  echo "# BlackCow Ecosystem Health Report"
  echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "Traffic light: $TRAFFIC"
  echo "Scripts run: $SCRIPTS_RUN | Passed: $SCRIPTS_PASSED | Failed: $SCRIPTS_FAILED"
  echo "Aggregate score: ${AGGREGATE_SCORE}%"
  echo ""
  echo "## Per-Script Results"
  for i in "${!SCRIPT_NAMES[@]}"; do
    echo "- ${SCRIPT_NAMES[$i]}: ${SCRIPT_SCORE[$i]}% (P:${SCRIPT_PASS[$i]} F:${SCRIPT_FAIL[$i]} S:${SCRIPT_SKIP[$i]})"
  done
} > "$HEALTH_LOG"

if command -v python3 &>/dev/null; then
  python3 -c "
import json
scripts = []
$(
  for i in "${!SCRIPT_NAMES[@]}"; do
    echo "scripts.append({"
    echo "    'name': '${SCRIPT_NAMES[$i]}',"
    echo "    'pass': ${SCRIPT_PASS[$i]},"
    echo "    'fail': ${SCRIPT_FAIL[$i]},"
    echo "    'skip': ${SCRIPT_SKIP[$i]},"
    echo "    'total': ${SCRIPT_TOTAL[$i]},"
    echo "    'score': ${SCRIPT_SCORE[$i]},"
    echo "    'exit_code': ${SCRIPT_EXIT[$i]},"
    echo "    'duration_s': ${SCRIPT_DURATION[$i]}"
    echo "})"
  done
)
report = {
    'traffic_light': '$TRAFFIC',
    'aggregate_score': $AGGREGATE_SCORE,
    'scripts_run': $SCRIPTS_RUN,
    'scripts_passed': $SCRIPTS_PASSED,
    'scripts_failed': $SCRIPTS_FAILED,
    'total_checks': $OVERALL_TOTAL,
    'total_pass': $OVERALL_PASS,
    'total_fail': $OVERALL_FAIL,
    'total_skip': $OVERALL_SKIP,
    'generated_at': '$START_TIME',
    'scripts': scripts
}
with open('$HEALTH_JSON', 'w') as f:
    json.dump(report, f, indent=2)
print(f'  JSON report written to: $HEALTH_JSON')
" 2>/dev/null || true
fi

# --- Output: --summary path vs normal path -----------------------------------
if $SUMMARY_OUT; then
  # Compact 80-char Unicode box — the entire report in one box.
  echo ""
  print_summary_box
  echo ""
  echo "  Traffic light:  ${TRAFFIC}"
  echo "  Aggregate:      ${AGGREGATE_SCORE}%"
  echo "  Runtime:        $(date -u +%Y-%m-%dT%H:%M:%SZ) (started ${START_TIME})"
  echo "  Text report written to: $HEALTH_LOG"

  # Show any failures inline after the box
  if [[ "$SCRIPTS_FAILED" -gt 0 ]]; then
    echo ""
    echo "━━━ Failure Details ━━━"
    for i in "${!SCRIPT_NAMES[@]}"; do
      if [[ "${SCRIPT_FAIL[$i]}" -gt 0 ]]; then
        echo ""
        script_exit="${SCRIPT_EXIT[$i]:-0}"
        script_total="${SCRIPT_TOTAL[$i]:-0}"
        if [[ "$script_exit" -ne 0 ]] && [[ "$script_total" -eq 0 ]]; then
          echo -e "  ${RED}${BOLD}${SCRIPT_NAMES[$i]}${NC} — NOT FOUND (preflight guard)"
        else
          echo -e "  ${RED}${BOLD}${SCRIPT_NAMES[$i]}${NC} — ${SCRIPT_FAIL[$i]} failure(s):"
        fi
        et="${SCRIPT_ERRORS[$i]:-}"
        if [[ "$et" == "[see output above]" ]]; then
          echo "    [details streamed above — re-run without --verbose for captured output]"
        elif [[ -n "$et" ]]; then
          echo "$et" | while IFS= read -r line; do
            [[ -z "$line" ]] && continue
            echo "    ${line}"
          done
        else
          echo "    (no details captured — re-run with --verbose)"
        fi
      fi
    done
  fi

else
  # --- Normal full report ---------------------------------------------------
  header "Per-Script Scores"

  printf "  %-50s %6s %6s %6s %7s %8s  %s\n" \
    "SCRIPT" "PASS" "FAIL" "SKIP" "SCORE" "TIME(s)" "STATUS"
  printf "  %-50s %6s %6s %6s %7s %8s  %s\n" \
    "──────────────────────────────────────────────────" \
    "──────" "──────" "──────" "───────" "────────" "──────"

  for i in "${!SCRIPT_NAMES[@]}"; do
    name="${SCRIPT_NAMES[$i]}"
    p="${SCRIPT_PASS[$i]}"
    f="${SCRIPT_FAIL[$i]}"
    s="${SCRIPT_SKIP[$i]}"
    sc="${SCRIPT_SCORE[$i]}"
    d="${SCRIPT_DURATION[$i]}"

    if [[ "$f" -eq 0 && "$s" -eq 0 ]]; then
      status="🟢 PASS"
    elif [[ "$f" -eq 0 ]]; then
      status="🟡 WARN"
    else
      status="🔴 FAIL"
    fi

    printf "  %-50s %6d %6d %6d %6d%% %7ds  %s\n" \
      "$name" "$p" "$f" "$s" "$sc" "$d" "$status"
  done

  echo ""
  printf "  %-50s %6d %6d %6d %6d%%\n" \
    "AGGREGATE" "$OVERALL_PASS" "$OVERALL_FAIL" "$OVERALL_SKIP" "$AGGREGATE_SCORE"

  # --- Traffic Light Display -------------------------------------------------
  header "Traffic Light Summary"

  case "$TRAFFIC" in
    GREEN)
      echo -e "  ${GREEN}${BOLD}╔════════════════════════════════════════╗${NC}"
      echo -e "  ${GREEN}${BOLD}║  🟢  ECOSYSTEM HEALTHY                 ║${NC}"
      echo -e "  ${GREEN}${BOLD}║  All ${SCRIPTS_RUN} scripts passed cleanly.        ║${NC}"
      echo -e "  ${GREEN}${BOLD}╚════════════════════════════════════════╝${NC}"
      ;;
    YELLOW)
      echo -e "  ${YELLOW}${BOLD}╔════════════════════════════════════════╗${NC}"
      echo -e "  ${YELLOW}${BOLD}║  🟡  ECOSYSTEM WARNINGS                ║${NC}"
      echo -e "  ${YELLOW}${BOLD}║  ${SCRIPTS_PASSED}/${SCRIPTS_RUN} scripts passed; warnings/skips present. ║${NC}"
      echo -e "  ${YELLOW}${BOLD}╚════════════════════════════════════════╝${NC}"
      ;;
    RED)
      echo -e "  ${RED}${BOLD}╔════════════════════════════════════════╗${NC}"
      echo -e "  ${RED}${BOLD}║  🔴  ECOSYSTEM FAILURES                ║${NC}"
      echo -e "  ${RED}${BOLD}║  ${SCRIPTS_FAILED}/${SCRIPTS_RUN} scripts have failures.              ║${NC}"
      echo -e "  ${RED}${BOLD}╚════════════════════════════════════════╝${NC}"
      ;;
  esac

  echo ""
  echo "  Traffic light:  ${TRAFFIC}"
  echo "  Scripts run:    ${SCRIPTS_RUN}"
  echo "  Scripts passed: ${SCRIPTS_PASSED}"
  echo "  Scripts failed: ${SCRIPTS_FAILED}"
  echo "  Total checks:   ${OVERALL_TOTAL}"
  echo "  Passed:         ${OVERALL_PASS}"
  echo "  Failed:         ${OVERALL_FAIL}"
  echo "  Skipped:        ${OVERALL_SKIP}"
  echo "  Aggregate:      ${AGGREGATE_SCORE}%"
  echo "  Runtime:        $(date -u +%Y-%m-%dT%H:%M:%SZ) (started ${START_TIME})"

  # --- Detailed failures -----------------------------------------------------
  if [[ "$SCRIPTS_FAILED" -gt 0 ]]; then
    header "Failure Details"
    for i in "${!SCRIPT_NAMES[@]}"; do
      if [[ "${SCRIPT_FAIL[$i]}" -gt 0 ]]; then
        echo ""
        script_exit="${SCRIPT_EXIT[$i]:-0}"
        script_total="${SCRIPT_TOTAL[$i]:-0}"
        if [[ "$script_exit" -ne 0 ]] && [[ "$script_total" -eq 0 ]]; then
          echo -e "  ${RED}${BOLD}${SCRIPT_NAMES[$i]}${NC} — NOT FOUND (preflight guard)"
        else
          echo -e "  ${RED}${BOLD}${SCRIPT_NAMES[$i]}${NC} — ${SCRIPT_FAIL[$i]} failure(s):"
        fi
        et="${SCRIPT_ERRORS[$i]:-}"
        if [[ "$et" == "[see output above]" ]]; then
          echo "    [details streamed above — re-run without --verbose for captured output]"
        elif [[ -n "$et" ]]; then
          echo "$et" | while IFS= read -r line; do
            [[ -z "$line" ]] && continue
            echo "    ${line}"
          done
        else
          echo "    (no details captured — re-run with --verbose)"
        fi
      fi
    done
  fi

  # --- Health score breakdown ------------------------------------------------
  header "Health Score Breakdown"
  echo "  Scoring methodology:"
  echo "    • Script score = passed_checks / total_checks × 100"
  echo "    • Aggregate = sum(passed) / sum(total) × 100"
  echo ""
  echo "  ── Per-Skill Grouping ──"
  echo ""

  GOV_SCORE=0; GOV_COUNT=0
  PLAN_SCORE=0; PLAN_COUNT=0
  CROSS_SCORE=0; CROSS_COUNT=0
  ECO_SCORE=0; ECO_COUNT=0
  OTHER_SCORE=0; OTHER_COUNT=0

  for i in "${!SCRIPT_NAMES[@]}"; do
    name="${SCRIPT_NAMES[$i]}"
    score="${SCRIPT_SCORE[$i]}"
    if echo "$name" | grep -q "governor"; then
      GOV_SCORE=$((GOV_SCORE + score)); GOV_COUNT=$((GOV_COUNT + 1))
    elif echo "$name" | grep -q "plan"; then
      PLAN_SCORE=$((PLAN_SCORE + score)); PLAN_COUNT=$((PLAN_COUNT + 1))
    elif echo "$name" | grep -q "cross-skill"; then
      CROSS_SCORE=$((CROSS_SCORE + score)); CROSS_COUNT=$((CROSS_COUNT + 1))
    elif echo "$name" | grep -qE "ecosystem[^-]"; then
      ECO_SCORE=$((ECO_SCORE + score)); ECO_COUNT=$((ECO_COUNT + 1))
    else
      OTHER_SCORE=$((OTHER_SCORE + score)); OTHER_COUNT=$((OTHER_COUNT + 1))
    fi
  done

  print_skill_line() {
    local skill="$1" total_score="$2" count="$3"
    if [[ "$count" -gt 0 ]]; then
      local avg
      avg=$(awk "BEGIN {printf \"%.0f\", $total_score / $count}")
      if [[ "$avg" -eq 100 ]]; then
        echo -e "  ${GREEN}🟢${NC} ${skill}: ${avg}% (${count} script(s))"
      elif [[ "$avg" -ge 80 ]]; then
        echo -e "  ${YELLOW}🟡${NC} ${skill}: ${avg}% (${count} script(s))"
      else
        echo -e "  ${RED}🔴${NC} ${skill}: ${avg}% (${count} script(s))"
      fi
    fi
  }

  print_skill_line "governor" "$GOV_SCORE" "$GOV_COUNT"
  print_skill_line "plan" "$PLAN_SCORE" "$PLAN_COUNT"
  print_skill_line "cross-skill" "$CROSS_SCORE" "$CROSS_COUNT"
  print_skill_line "ecosystem" "$ECO_SCORE" "$ECO_COUNT"
  print_skill_line "other" "$OTHER_SCORE" "$OTHER_COUNT"

  $QUIET || echo ""
  log_info "Text report written to: $HEALTH_LOG"
fi

# --- Final exit --------------------------------------------------------------
if ! $SUMMARY_OUT; then
  echo ""
  echo "============================================================"
  echo -e "  ${BOLD}${TRAFFIC_LABEL}${NC}"
  echo "============================================================"
fi

# --- JSON stdout emission ---
if $JSON_OUT; then
  exec 1>&3 3>&-                    # restore original stdout
  ELAPSED_S=$(( $(date +%s) - START_EPOCH ))

  printf '{'
  printf '"scripts":['
  first=true
  for i in "${!SCRIPT_NAMES[@]}"; do
    $first || printf ','
    first=false
    if [[ "${SCRIPT_FAIL[$i]}" -gt 0 ]]; then status="FAIL"; else status="PASS"; fi
    printf '{"name":"%s","pass":%d,"fail":%d,"skip":%d,"score":%d,"status":"%s"}' \
      "${SCRIPT_NAMES[$i]}" "${SCRIPT_PASS[$i]}" "${SCRIPT_FAIL[$i]}" \
      "${SCRIPT_SKIP[$i]}" "${SCRIPT_SCORE[$i]}" "$status"
  done
  printf '],'
  printf '"aggregate":{"pass":%d,"fail":%d,"skip":%d,"score":%d},' \
    "$OVERALL_PASS" "$OVERALL_FAIL" "$OVERALL_SKIP" "$AGGREGATE_SCORE"
  printf '"traffic_light":"%s",' "$TRAFFIC"
  printf '"elapsed_s":%d' "$ELAPSED_S"
  printf '}\n'
fi

exit $EXIT_CODE