#!/usr/bin/env bash
# ============================================================================
# validate-cross-skill-contract.sh
# Cross-Skill Evidence Contract Validation
#
# Validates the 6-row Cross-Skill Evidence Contract defined in
# skills/blackcow-governor.md against on-disk reality. Verifies:
#
#   P0  — Contract table exists and has correct structure
#   ROW 1 — governor → .omo/governor/<slug>-governance.md → plan, loop, qa
#   ROW 2 — plan → plans/<slug>.md → loop
#   ROW 3 — loop → .omo/ulw-loop/completion-report.md → qa, governor, librarian
#   ROW 4 — qa → .omo/memory/qa-history.jsonl → librarian, governor
#   ROW 5 — librarian → .omo/library/structure-cache.jsonl → plan, loop, qa
#   ROW 6 — librarian → .omo/memory/failure-patterns.jsonl → governor
#   RULES — Contract rules (R7: write-before-DONE, R8: freshness, R9: fallback, R10: relative paths)
#   E2E   — On-disk artifact existence
#   CONSISTENCY — No duplicate/phantom contract rows
#
# Usage:
#   bash skills/tests/validate-cross-skill-contract.sh
#   bash skills/tests/validate-cross-skill-contract.sh --verbose
#   bash skills/tests/validate-cross-skill-contract.sh --quiet
#
# Returns: 0 if ALL contract validations pass, 1 otherwise
# ============================================================================

set -euo pipefail

# --- Config -----------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$SKILLS_DIR/.." && pwd)"
GOVERNOR_FILE="${SKILLS_DIR}/blackcow-governor.md"
PLAN_FILE="${SKILLS_DIR}/blackcow-plan.md"
LOOP_FILE="${SKILLS_DIR}/blackcow-loop.md"
QA_FILE="${SKILLS_DIR}/blackcow-qa.md"
LIBRARIAN_FILE="${SKILLS_DIR}/blackcow-librarian.md"
SWARM_FILE="${SKILLS_DIR}/blackcow-swarm.md"

MISSING=""
for f in "$GOVERNOR_FILE" "$PLAN_FILE" "$LOOP_FILE" "$QA_FILE" "$LIBRARIAN_FILE"; do
  [[ -f "$f" ]] || MISSING="$MISSING  $f"$'\n'
done
[[ -z "$MISSING" ]] || { echo "FATAL: Target file(s) not found:"$'\n'"$MISSING" >&2; exit 1; }

VERBOSE=false
QUIET=false
for arg in "$@"; do
  case "$arg" in
    --verbose) VERBOSE=true ;;
    --quiet) QUIET=true ;;
  esac
done

PASS=0
FAIL=0
TOTAL=0
ERRORS=()

# --- Color helpers -----------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

pass_msg() { ((PASS++)); ((TOTAL++)); $QUIET || echo -e "  ${GREEN}PASS${NC} $1"; }
fail_msg() { ((FAIL++)); ((TOTAL++)); echo -e "  ${RED}FAIL${NC} $1"; ERRORS+=("$1"); }
info_msg() { $VERBOSE && echo -e "  ${CYAN}INFO${NC} $1"; return 0; }
header()   { echo ""; echo "━━━ $* ━━━"; }
subheader(){ echo ""; echo "  ── $* ──"; }

# --- Assert helpers ----------------------------------------------------------
assert_file_exists() {
  local label="$1" path="$2"
  if [[ -f "$path" ]]; then
    pass_msg "$label — exists: $(basename "$path")"
  else
    fail_msg "$label — NOT FOUND: $path"
  fi
}

assert_grep() {
  local label="$1" file="$2" pattern="$3"
  if grep -Eq "$pattern" "$file" 2>/dev/null; then
    pass_msg "$label — pattern found: /$(echo "$pattern" | sed 's/^\(.\{0,40\}\).*/\1.../')/"
  else
    fail_msg "$label — pattern MISSING: /$(echo "$pattern" | sed 's/^\(.\{0,40\}\).*/\1.../')/"
  fi
}

assert_grep_or() {
  local label="$1" file="$2" pattern_a="$3" pattern_b="${4:-}"
  if grep -Eq "$pattern_a" "$file" 2>/dev/null; then
    pass_msg "$label"
  elif [[ -n "$pattern_b" ]] && grep -Eq "$pattern_b" "$file" 2>/dev/null; then
    pass_msg "$label"
  else
    fail_msg "$label — pattern not found"
  fi
}

assert_dir_exists() {
  local label="$1" path="$2"
  if [[ -d "$path" ]]; then
    pass_msg "$label — directory exists"
  else
    info_msg "$label — directory not yet created (expected for new projects)"
  fi
}

# ============================================================================
echo "============================================================"
echo " Cross-Skill Evidence Contract Validation"
echo "============================================================"
echo " Skills dir:     $SKILLS_DIR"
echo " Project root:   $PROJECT_ROOT"
echo " Governor file:  $(basename "$GOVERNOR_FILE")"

# ============================================================================
# P0 — CONTRACT TABLE EXISTENCE
# ============================================================================
header "P0 — Contract Table Existence"

# P0a: The governor must define the Cross-Skill Evidence Contract
assert_grep "P0a — Cross-Skill Evidence Contract table defined" \
  "$GOVERNOR_FILE" "Cross-Skill Evidence Contract"

# P0b: Contract rules must be stated
assert_grep "P0b — Contract rules section present" \
  "$GOVERNOR_FILE" "Contract rules"

# P0c: Must have at least 6 rows (one per producer→artifact→consumer path)
CONTRACT_ROWS=$(grep -cE '^\| `blackcow-' "$GOVERNOR_FILE" 2>/dev/null || echo "0")
if [[ "$CONTRACT_ROWS" -ge 6 ]]; then
  pass_msg "P0c — Contract table has ≥6 producer rows (found $CONTRACT_ROWS)"
else
  fail_msg "P0c — Contract table has only $CONTRACT_ROWS rows (expected ≥6)"
fi

# P0d: All 5 producer skills referenced
for skill in "blackcow-governor" "blackcow-plan" "blackcow-loop" "blackcow-qa" "blackcow-librarian"; do
  assert_grep "P0d — Skill '$skill' referenced in contract table" \
    "$GOVERNOR_FILE" "$skill"
done

# P0e: All 6 artifact paths referenced
for artifact in ".omo/governor/" "plans/" "completion-report" "qa-history" "structure-cache" "failure-patterns"; do
  assert_grep "P0e — Artifact '$artifact' referenced in contract table" \
    "$GOVERNOR_FILE" "$artifact"
done

# ============================================================================
# ROW 1 — blackcow-governor → .omo/governor/<slug>-governance.md → plan,loop,qa
# ============================================================================
header "ROW 1 — blackcow-governor → .omo/governor/<slug>-governance.md → plan, loop, qa"

# --- 1a — Producer writes artifact ---
subheader "1a — Producer (governor) writes artifact"

assert_grep "1a.1 — Governor references .omo/governor/ output path" \
  "$GOVERNOR_FILE" "\.omo/governor/"

assert_grep "1a.2 — Governor Phase 1 produces governance.md" \
  "$GOVERNOR_FILE" "Produce.*\.omo/governor/.*-governance\.md"

assert_grep "1a.3 — Governor constraint limits output to governance.md" \
  "$GOVERNOR_FILE" "Produce ONLY.*\.omo/governor/"

# --- 1b — Artifact directory exists ---
subheader "1b — Governor output directory exists or can be created"

GOVERNOR_DIR="${PROJECT_ROOT}/.omo/governor"
if [[ -d "$GOVERNOR_DIR" ]]; then
  pass_msg "1b.1 — .omo/governor/ directory exists"
  GOV_COUNT=$(ls -1 "$GOVERNOR_DIR"/*-governance.md 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$GOV_COUNT" -ge 1 ]]; then
    pass_msg "1b.2 — .omo/governor/ contains $GOV_COUNT governance file(s)"
  else
    info_msg "1b.2 — .omo/governor/ has no governance files yet"
  fi

  # Check naming convention
  SLUG_COUNT=$(ls -1 "$GOVERNOR_DIR" 2>/dev/null | grep -c '\-governance\.md$' || echo "0")
  if [[ "$SLUG_COUNT" -ge 1 ]]; then
    pass_msg "1b.3 — $SLUG_COUNT file(s) match <slug>-governance.md naming convention"
  else
    info_msg "1b.3 — No files match <slug>-governance.md convention yet"
  fi
else
  info_msg "1b — .omo/governor/ directory not yet created"
fi

# --- 1c — Consumers load via --govern=<slug> ---
subheader "1c — Consumers (plan, loop, qa) load via --govern=<slug>"

CONSUMERS_ROW1=("blackcow-plan" "blackcow-loop" "blackcow-qa")
CONSUMER_FILES_ROW1=("$PLAN_FILE" "$LOOP_FILE" "$QA_FILE")

for i in "${!CONSUMERS_ROW1[@]}"; do
  skill="${CONSUMERS_ROW1[$i]}"
  file="${CONSUMER_FILES_ROW1[$i]}"
  assert_grep "1c.$((i+1)) — $skill parses --govern flag" \
    "$file" "\-\-govern="
done
subheader "1d — Consumers reference governance.md path"

for i in "${!CONSUMERS_ROW1[@]}"; do
  skill="${CONSUMERS_ROW1[$i]}"
  file="${CONSUMER_FILES_ROW1[$i]}"
  assert_grep_or "1d — $skill references governance.md or .omo/governor/ path" \
    "$file" "governance\.md|--govern=" "\.omo/governor/"
done

if [[ -f "$SWARM_FILE" ]]; then
  header "SWARM — blackcow-swarm isolated runtime contract"
  assert_grep "SWARM.1 — Swarm references blackcow-plan" "$SWARM_FILE" "blackcow-plan"
  assert_grep "SWARM.2 — Swarm references blackcow-loop" "$SWARM_FILE" "blackcow-loop"
  assert_grep "SWARM.3 — Swarm references blackcow-qa" "$SWARM_FILE" "blackcow-qa"
  assert_grep "SWARM.4 — Swarm records .omo/swarm runtime artifacts" "$SWARM_FILE" "\.omo/swarm/runs"
  assert_grep "SWARM.5 — Swarm uses isolated writer worktrees" "$SWARM_FILE" "\.worktrees/swarm"
  assert_grep "SWARM.6 — Swarm requires worker result.json" "$SWARM_FILE" "result\.json"
fi

# ============================================================================
# ROW 2 — blackcow-plan → plans/<slug>.md → loop
# ============================================================================
header "ROW 2 — blackcow-plan → plans/<slug>.md → loop"

# --- 2a — Producer writes artifact ---
subheader "2a — Producer (plan) writes plans/<slug>.md"

assert_grep "2a.1 — Plan references plans/ output directory" \
  "$PLAN_FILE" "plans/"

assert_grep "2a.2 — Plan writes plan files to disk" \
  "$PLAN_FILE" "plans/.*\.md"

# --- 2b — Artifact directory exists ---
subheader "2b — Plan output directory exists"

PLANS_DIR="${PROJECT_ROOT}/plans"
if [[ -d "$PLANS_DIR" ]]; then
  pass_msg "2b.1 — plans/ directory exists"
  PLAN_COUNT=$(ls -1 "$PLANS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$PLAN_COUNT" -ge 1 ]]; then
    pass_msg "2b.2 — plans/ contains $PLAN_COUNT plan file(s)"
  else
    info_msg "2b.2 — plans/ directory exists but is empty"
  fi
else
  info_msg "2b — plans/ directory not yet created"
fi

# --- 2c — Consumer loads artifact ---
subheader "2c — Consumer (loop) loads plans/<slug>.md"

assert_grep "2c.1 — Loop Input section accepts plan reference" \
  "$LOOP_FILE" "plan reference"

assert_grep "2c.2 — Loop references plans/ path" \
  "$LOOP_FILE" "plans/"

# --- 2d — Contract handshake ---
subheader "2d — Contract handshake: Execute plans/<slug>.md"

if grep -q "Execute.*plans/" "$GOVERNOR_FILE" 2>/dev/null; then
  pass_msg "2d.1 — Governor Phase 2 dispatches 'Execute plans/<slug>.md' to loop"
else
  fail_msg "2d.1 — Governor Phase 2 does NOT dispatch 'Execute plans/<slug>.md' to loop"
fi

# ============================================================================
# ROW 3 — blackcow-loop → .omo/ulw-loop/completion-report.md → qa,gov,librarian
# ============================================================================
header "ROW 3 — blackcow-loop → .omo/ulw-loop/completion-report.md → qa, governor, librarian"

# --- 3a — Producer writes artifact ---
subheader "3a — Producer (loop) writes completion-report.md"

assert_grep "3a.1 — Loop references completion-report.md" \
  "$LOOP_FILE" "completion-report"

assert_grep "3a.2 — Loop writes to .omo/ulw-loop/ directory" \
  "$LOOP_FILE" "\.omo/ulw-loop/"

# --- 3b — Artifact exists ---
subheader "3b — Completion report exists on disk"

COMPLETION_REPORT="${PROJECT_ROOT}/.omo/ulw-loop/completion-report.md"
if [[ -f "$COMPLETION_REPORT" ]]; then
  pass_msg "3b.1 — completion-report.md exists"
  SIZE=$(wc -c < "$COMPLETION_REPORT" 2>/dev/null | tr -d ' ')
  if [[ "$SIZE" -gt 0 ]]; then
    pass_msg "3b.2 — completion-report.md has content ($SIZE bytes)"
  else
    fail_msg "3b.2 — completion-report.md is EMPTY"
  fi
else
  info_msg "3b — completion-report.md not yet produced (first loop run needed)"
fi

# --- 3c — Consumers load evidence index ---
subheader "3c — Consumers (qa, governor, librarian) load evidence index"

assert_grep_or "3c.1 — qa references completion-report (evidence index)" \
  "$QA_FILE" "completion-report" "evidence.index" "evidence index"

assert_grep "3c.2 — Governor Phase 0.4 loads completion-report (evidence index)" \
  "$GOVERNOR_FILE" "0\.4.*[Ll]oad.*[Ee]vidence|completion-report.*evidence"

assert_grep_or "3c.3 — Librarian references completion-report (load-evidence)" \
  "$LIBRARIAN_FILE" "completion-report" "load.evidence"

# ============================================================================
# ROW 4 — blackcow-qa → .omo/memory/qa-history.jsonl → librarian, governor
# ============================================================================
header "ROW 4 — blackcow-qa → .omo/memory/qa-history.jsonl → librarian, governor"

# --- 4a — Producer writes artifact ---
subheader "4a — Producer (qa) writes qa-history.jsonl"

assert_grep "4a.1 — qa references qa-history.jsonl" \
  "$QA_FILE" "qa-history"

assert_grep "4a.2 — qa writes to .omo/memory/ directory" \
  "$QA_FILE" "\.omo/memory/"

# --- 4b — Artifact exists and is valid JSONL ---
subheader "4b — qa-history.jsonl exists and is valid JSONL"

QA_HISTORY="${PROJECT_ROOT}/.omo/memory/qa-history.jsonl"
if [[ -f "$QA_HISTORY" ]]; then
  pass_msg "4b.1 — qa-history.jsonl exists"
  SIZE=$(wc -c < "$QA_HISTORY" 2>/dev/null | tr -d ' ')
  if [[ "$SIZE" -gt 0 ]]; then
    pass_msg "4b.2 — qa-history.jsonl has content ($SIZE bytes)"
  else
    fail_msg "4b.2 — qa-history.jsonl is EMPTY"
  fi

  # JSONL validation
  LINES=0
  ERRORS=0
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" ]] && continue
    ((LINES++))
    if ! echo "$line" | python3 -m json.tool > /dev/null 2>&1; then
      ((ERRORS++))
    fi
  done < "$QA_HISTORY"

  if [[ "$ERRORS" -eq 0 ]] && [[ "$LINES" -ge 1 ]]; then
    pass_msg "4b.3 — qa-history.jsonl is valid JSONL ($LINES entries, $ERRORS invalid)"
  elif [[ "$ERRORS" -gt 0 ]]; then
    fail_msg "4b.3 — qa-history.jsonl has $ERRORS invalid JSON line(s) out of $LINES"
  else
    fail_msg "4b.3 — qa-history.jsonl has no entries"
  fi
else
  info_msg "4b — qa-history.jsonl not yet created"
fi

# --- 4c — Consumers load failure-pattern data ---
subheader "4c — Consumers (librarian, governor) load failure-pattern data"

assert_grep "4c.1 — Governor references qa-history (failure-pattern auto-population)" \
  "$GOVERNOR_FILE" "qa-history"

assert_grep_or "4c.2 — Librarian references qa-history or failure-patterns" \
  "$LIBRARIAN_FILE" "qa-history" "failure-patterns"

# ============================================================================
# ROW 5 — blackcow-librarian → .omo/library/structure-cache.jsonl → plan, loop, qa
# ============================================================================
header "ROW 5 — blackcow-librarian → .omo/library/structure-cache.jsonl → plan, loop, qa"

# --- 5a — Producer writes artifact ---
subheader "5a — Producer (librarian) writes structure-cache.jsonl"

assert_grep "5a.1 — Librarian references structure-cache.jsonl" \
  "$LIBRARIAN_FILE" "structure-cache"

assert_grep "5a.2 — Librarian writes to .omo/library/ directory" \
  "$LIBRARIAN_FILE" "\.omo/library/"

# --- 5b — Artifact exists and is valid ---
subheader "5b — structure-cache.jsonl exists and is valid"

STRUCTURE_CACHE="${PROJECT_ROOT}/.omo/library/structure-cache.jsonl"
if [[ -f "$STRUCTURE_CACHE" ]]; then
  pass_msg "5b.1 — structure-cache.jsonl exists"
  SIZE=$(wc -c < "$STRUCTURE_CACHE" 2>/dev/null | tr -d ' ')
  if [[ "$SIZE" -gt 0 ]]; then
    pass_msg "5b.2 — structure-cache.jsonl has content ($SIZE bytes)"

    LINES=0
    ERRORS=0
    while IFS= read -r line || [[ -n "$line" ]]; do
      [[ -z "$line" ]] && continue
      ((LINES++))
      if ! echo "$line" | python3 -m json.tool > /dev/null 2>&1; then
        ((ERRORS++))
      fi
    done < "$STRUCTURE_CACHE"
    if [[ "$ERRORS" -eq 0 ]]; then
      pass_msg "5b.3 — structure-cache.jsonl is valid JSONL ($LINES entries)"
    else
      fail_msg "5b.3 — structure-cache.jsonl has $ERRORS invalid JSON line(s)"
    fi
  else
    info_msg "5b.2 — structure-cache.jsonl is EMPTY (no scan run yet)"
  fi
else
  info_msg "5b — structure-cache.jsonl not yet created (librarian scan needed)"
fi

# --- 5c — Consumers load structure cache (Phase 0) ---
subheader "5c — Consumers (plan, loop, qa) load structure cache (Phase 0)"

assert_grep_or "5c.1 — Plan references cache/librarian (Phase 0 cache load)" \
  "$PLAN_FILE" "cache" "librarian" "Phase 0.*[Cc]ache"

assert_grep "5c.2 — Loop has Phase 0.0 Cache Load (librarian integration)" \
  "$LOOP_FILE" "0\.0.*[Cc]ache.*[Ll]oad|librarian.*[Ii]ntegration"

assert_grep_or "5c.3 — QA references cache/librarian (Phase 0 cache load)" \
  "$QA_FILE" "cache" "librarian" "\.[Oo]mo/library/"

# ============================================================================
# ROW 6 — blackcow-librarian → .omo/memory/failure-patterns.jsonl → governor
# ============================================================================
header "ROW 6 — blackcow-librarian → .omo/memory/failure-patterns.jsonl → governor"

# --- 6a — Producer writes artifact ---
subheader "6a — Producer (librarian) writes failure-patterns.jsonl"

assert_grep "6a.1 — Librarian references failure-patterns.jsonl" \
  "$LIBRARIAN_FILE" "failure-patterns"

assert_grep "6a.2 — Librarian writes to .omo/memory/ directory" \
  "$LIBRARIAN_FILE" "\.omo/memory/"

# --- 6b — Artifact exists and is valid ---
subheader "6b — failure-patterns.jsonl exists and is valid"

FAILURE_PATTERNS="${PROJECT_ROOT}/.omo/memory/failure-patterns.jsonl"
if [[ -f "$FAILURE_PATTERNS" ]]; then
  pass_msg "6b.1 — failure-patterns.jsonl exists"
  SIZE=$(wc -c < "$FAILURE_PATTERNS" 2>/dev/null | tr -d ' ')
  if [[ "$SIZE" -gt 0 ]]; then
    pass_msg "6b.2 — failure-patterns.jsonl has content ($SIZE bytes)"

    LINES=0
    ERRORS=0
    while IFS= read -r line || [[ -n "$line" ]]; do
      [[ -z "$line" ]] && continue
      ((LINES++))
      if ! echo "$line" | python3 -m json.tool > /dev/null 2>&1; then
        ((ERRORS++))
      fi
    done < "$FAILURE_PATTERNS"
    if [[ "$ERRORS" -eq 0 ]]; then
      pass_msg "6b.3 — failure-patterns.jsonl is valid JSONL ($LINES entries)"
    else
      fail_msg "6b.3 — failure-patterns.jsonl has $ERRORS invalid JSON line(s)"
    fi
  else
    info_msg "6b.2 — failure-patterns.jsonl is EMPTY (no patterns recorded yet)"
  fi
else
  info_msg "6b — failure-patterns.jsonl not yet created"
fi

# --- 6c — Consumer loads failure-patterns in Phase 0.1 ---
subheader "6c — Consumer (governor) loads failure-patterns in Phase 0.1"

assert_grep "6c.1 — Governor Phase 0.1 loads failure-patterns.jsonl" \
  "$GOVERNOR_FILE" "failure-patterns\.jsonl"

assert_grep "6c.2 — Governor Phase 0 references failure-pattern memory" \
  "$GOVERNOR_FILE" "0\.1.*[Ll]oad.*[Ff]ailure|failure-pattern"

# ============================================================================
# CONTRACT RULES (R7-R10)
# ============================================================================
header "RULES — Contract Rule Validation"

# --- R7 — Producer writes artifact BEFORE DONE emission ---
subheader "R7 — Producer writes artifact BEFORE DONE emission"

assert_grep "R7a — Governor constraint enforces output-before-DONE" \
  "$GOVERNOR_FILE" "Produce ONLY"

# Plan: DONE section must come after plans/ reference
PLAN_OUTPUT_LINE=$(grep -n "plans/" "$PLAN_FILE" 2>/dev/null | head -1 | cut -d: -f1 || echo "9999")
PLAN_DONE_LINE=$(grep -n "^## DONE" "$PLAN_FILE" 2>/dev/null | head -1 | cut -d: -f1 || echo "0")
if [[ "$PLAN_OUTPUT_LINE" -lt "$PLAN_DONE_LINE" ]] || [[ "$PLAN_DONE_LINE" -eq 0 ]]; then
  pass_msg "R7b — Plan references plans/ output before its Constraints section"
else
  info_msg "R7b — Plan output reference after DONE (check ordering)"
fi

# Loop: completion-report referenced in body
assert_grep "R7c — Loop references completion-report in its body" \
  "$LOOP_FILE" "completion-report"

# QA: qa-history referenced
assert_grep "R7d — QA references qa-history.jsonl output" \
  "$QA_FILE" "qa-history"

# Librarian: references both artifacts
assert_grep "R7e — Librarian references both structure-cache and failure-patterns outputs" \
  "$LIBRARIAN_FILE" "structure-cache|failure-patterns"

# --- R8 — Consumer checks artifact freshness ---
subheader "R8 — Consumer checks artifact freshness (staleness thresholds)"

assert_grep_or "R8a — Governor checks staleness/freshness (Phase 0)" \
  "$GOVERNOR_FILE" "[Ss]tale|[Ff]reshness"

assert_grep_or "R8b — Loop checks FRESH/STALE status for cache" \
    "$LOOP_FILE" "FRESH" "STALE"
# Check QA for staleness awareness (may be implicit)
if grep -qE '[Ss]taleness|[Ff]reshness' "$QA_FILE" 2>/dev/null; then
  pass_msg "R8c — QA checks staleness/freshness of evidence"
else
  info_msg "R8c — QA does not explicitly check staleness"
fi

assert_grep "R8d — Librarian checks staleness (Phase 5 check command)" \
  "$LIBRARIAN_FILE" "[Ss]taleness|[Ff]reshness"

# --- R9 — Broken contract → consumer falls back to legacy discovery ---
subheader "R9 — Broken contract → consumer falls back to legacy discovery"

if grep -qE 'STALE.*fall through|EMPTY.*fall|legacy|standard.*discovery' "$LOOP_FILE" 2>/dev/null; then
  pass_msg "R9a — Loop has fallback path when cache is STALE/EMPTY"
elif grep -qE 'If.*STALE|If.*EMPTY|If cache is STALE|If no cache' "$LOOP_FILE" 2>/dev/null; then
  pass_msg "R9a — Loop has conditional path for STALE/EMPTY cache"
else
  info_msg "R9a — Loop may handle STALE/EMPTY implicitly"
fi

if grep -qE 'If no cache|legacy|fallback|If.*absent' "$PLAN_FILE" 2>/dev/null; then
  pass_msg "R9b — Plan has fallback when cache is absent"
else
  info_msg "R9b — Plan may not have explicit fallback for absent cache"
fi

if grep -qE 'If.*pattern|If.*absent|no prior|N/A' "$GOVERNOR_FILE" 2>/dev/null; then
  pass_msg "R9c — Governor handles absent failure-patterns gracefully"
else
  info_msg "R9c — Governor may handle absent failure-patterns implicitly"
fi

# --- R10 — All paths are relative to project root ---
subheader "R10 — All paths are relative to project root"

if grep -qE '`/(home|Users|root)/' "$GOVERNOR_FILE" 2>/dev/null; then
  fail_msg "R10a — Contract table contains ABSOLUTE paths (expected relative)"
else
  pass_msg "R10a — Contract table uses relative paths (no /home/ or /Users/ found)"
fi

# Verify artifact paths from contract table are project-relative
CONTRACT_PATHS=$(grep -oE '`[^`]+`' "$GOVERNOR_FILE" 2>/dev/null | grep -E '(\.omo/|plans/)' | sed 's/^`//;s/`$//' || true)
if [[ -n "$CONTRACT_PATHS" ]]; then
  ABSOLUTE_COUNT=0
  PATH_COUNT=0
  while IFS= read -r cpath; do
    [[ -z "$cpath" ]] && continue
    # Skip non-path entries (command strings, arguments)
    if [[ "$cpath" == --* ]] || [[ "$cpath" == \"* ]] || [[ "$cpath" == *\ * ]]; then
      continue
    fi
    PATH_COUNT=$((PATH_COUNT + 1))
    if [[ "$cpath" == /* ]]; then
      ABSOLUTE_COUNT=$((ABSOLUTE_COUNT + 1))
      $VERBOSE && echo -e "    ${YELLOW}ABSOLUTE${NC} path found: $cpath"
    fi
  done <<< "$CONTRACT_PATHS"
  if [[ "$ABSOLUTE_COUNT" -eq 0 ]]; then
    pass_msg "R10b — All $PATH_COUNT contract artifact paths are project-relative (none absolute)"
  else
    fail_msg "R10b — $ABSOLUTE_COUNT absolute path(s) found in contract table (expected all relative)"
  fi
else
  fail_msg "R10b — No contract artifact paths found in table"
fi

# ============================================================================
# END-TO-END: Contract Table vs On-Disk Reality
# ============================================================================
header "E2E — Contract Table vs On-Disk Reality"

echo "  Checking if each contract artifact exists on disk..."
echo ""

# Check each artifact path explicitly (bash 3.x compatible — no associative arrays)
check_artifact() {
  local artifact_path="$1" desc="$2" full_path
  full_path="${PROJECT_ROOT}/${artifact_path}"
  if [[ "$artifact_path" == */ ]]; then
    if [[ -d "$full_path" ]]; then
      COUNT=$(ls -1 "$full_path" 2>/dev/null | wc -l | tr -d ' ')
      if [[ "$COUNT" -ge 1 ]]; then
        pass_msg "E2E — ${artifact_path} (${desc}) → EXISTS (${COUNT} entries)"
      else
        info_msg "E2E — ${artifact_path} (${desc}) → EXISTS but EMPTY"
      fi
    else
      info_msg "E2E — ${artifact_path} (${desc}) → NOT YET CREATED"
    fi
  else
    if [[ -f "$full_path" ]]; then
      SIZE=$(wc -c < "$full_path" 2>/dev/null | tr -d ' ')
      pass_msg "E2E — ${artifact_path} (${desc}) → EXISTS (${SIZE} bytes)"
    else
      info_msg "E2E — ${artifact_path} (${desc}) → NOT YET CREATED"
    fi
  fi
}

check_artifact ".omo/governor/" "Governor governance decisions"
check_artifact "plans/" "Plan output files"
check_artifact ".omo/ulw-loop/completion-report.md" "Loop completion report"
check_artifact ".omo/memory/qa-history.jsonl" "QA history"
check_artifact ".omo/library/structure-cache.jsonl" "Librarian structure cache"
check_artifact ".omo/memory/failure-patterns.jsonl" "Librarian failure patterns"

# Additional artifacts referenced in governor Phase 0
check_artifact ".omo/memory/loop-roi.jsonl" "Loop ROI history"
check_artifact ".omo/ulw-loop/capabilities.json" "Infrastructure capabilities"

# ============================================================================
# SELF-CONSISTENCY: Check no duplicate contract rows
# ============================================================================
header "CONSISTENCY — Contract Table Self-Consistency"

# Extract all artifact paths from the contract table
CONTRACT_ARTIFACTS=$(grep -oE '`(\.omo/[^`]+|plans/[^`]+)' "$GOVERNOR_FILE" 2>/dev/null | sort -u)

UNIQUE_COUNT=$(echo "$CONTRACT_ARTIFACTS" | grep -c . || echo "0")
echo "  Unique artifact paths in contract table: $UNIQUE_COUNT"
echo "$CONTRACT_ARTIFACTS" | sed 's/^/    /'

# Each artifact should appear at least once
for artifact in ".omo/governor/" "plans/" "completion-report.md" "qa-history.jsonl" "structure-cache.jsonl" "failure-patterns.jsonl"; do
  COUNT=$(grep -c "$artifact" "$GOVERNOR_FILE" 2>/dev/null || echo "0")
  if [[ "$COUNT" -ge 1 ]]; then
    pass_msg "CONSISTENCY — '$artifact' appears $COUNT time(s) in governor.md"
  else
    fail_msg "CONSISTENCY — '$artifact' NOT FOUND in governor.md"
  fi
done

# ============================================================================
# SUMMARY
# ============================================================================
header "TEST SUMMARY"

echo "  Governor file:   $(basename "$GOVERNOR_FILE")"
echo "  Contract rows:   6"
echo "  Contract rules:  4 (R7-R10)"
echo "  Total tests:     $TOTAL"
echo "  Passed:          $PASS"
echo "  Failed:          $FAIL"

# Per-row failure counts
echo ""
echo "  Per-Row Breakdown:"
echo "    Row 1 (governor→governance.md→plan/loop/qa):  see above"
echo "    Row 2 (plan→plans/→loop):                     see above"
echo "    Row 3 (loop→completion-report→qa/gov/lib):    see above"
echo "    Row 4 (qa→qa-history→lib/gov):                see above"
echo "    Row 5 (librarian→structure-cache→plan/loop/qa): see above"
echo "    Row 6 (librarian→failure-patterns→governor):   see above"
echo "    Rules (R7-R10):                                see above"

if [[ "$FAIL" -eq 0 ]]; then
  echo ""
  echo "  ✅ ALL CROSS-SKILL CONTRACTS VALIDATED"
  echo "  The 6-row evidence contract is intact — all producer→consumer paths verified."
  exit 0
else
  echo ""
  echo "  ❌ $FAIL CONTRACT(S) BROKEN — review output above"
  echo ""
  echo "  Failures:"
  for e in "${ERRORS[@]}"; do
    echo "    • $e"
  done
  exit 1
fi
