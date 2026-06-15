#!/usr/bin/env bash
# =============================================================================
# Validate-BlackCow-Governor Integration
# =============================================================================
# L2 integration-level validation for skills/blackcow-governor.md.
#
# Checks four cross-file integration invariants:
#   1. Phase 2 Dispatch Referents — every skill name dispatched by the
#      governor's Phase 2 section (blackcow-plan, blackcow-loop, blackcow-qa,
#      blackcow-skill-review) must exist as skills/blackcow-<name>.md on disk
#   2. --govern Flag Adoption — every consumer listed in the Cross-Skill
#      Evidence Contract for governor's governance.md (plan, loop, qa) must
#      parse `--govern=<slug>` in their Input section
#   3. Cross-Skill Evidence Contract Alignment — each artifact row in the
#      governor's contract table has a matching producer→consumer handshake
#      in the downstream skill (e.g., plan reads governor, loop reads plan,
#      qa reads loop, librarian produces structure-cache, etc.)
#   4. Model Tier Consistency — all 7 blackcow-* skills define the same
#      budget/pro model names in their frontmatter model_tiers
#
# Usage:
#   bash skills/tests/validate-blackcow-governor-integration.sh
#   bash skills/tests/validate-blackcow-governor-integration.sh --verbose
# =============================================================================

set -euo pipefail

VERBOSE=false
[[ "${1:-}" == "--verbose" ]] && VERBOSE=true

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
GOVERNOR_FILE="${SKILL_DIR}/blackcow-governor.md"
[[ -f "$GOVERNOR_FILE" ]] || { echo "FATAL: Target file not found: $GOVERNOR_FILE" >&2; exit 1; }
INSTALL_SH="${SKILL_DIR}/install.sh"

PASS=0
FAIL=0
ERRORS=()

header()   { echo ""; echo "━━━ $* ━━━"; }
pass()     { PASS=$((PASS+1)); echo "  ✅ PASS: $*"; }
fail()     { FAIL=$((FAIL+1)); echo "  ❌ FAIL: $*"; ERRORS+=("$*"); }
info()     { $VERBOSE && echo "  ℹ️  $*"; }

# =============================================================================
# 1. Phase 2 Dispatch — every name called by run_skill() exists on disk
# =============================================================================
header "1 — Phase 2 Dispatch Referents"

# Extract all run_skill({ name: "blackcow-..." }) calls from the Phase 2 dispatch
# Lines 151-162 of governor.md
DISPATCHED_SKILLS=$(grep -o 'run_skill({ name: "blackcow-[^"]*"' "${GOVERNOR_FILE}" | sed 's/run_skill({ name: "*//;s/"$//' | sort -u)

echo "  Skills dispatched by Phase 2:"
while IFS= read -r name; do
  echo "    • ${name}.md"
done <<< "$DISPATCHED_SKILLS"

# Verify each dispatched skill exists on disk
ALL_DISPATCHED_EXIST=true
while IFS= read -r name; do
  [[ -z "$name" ]] && continue
  if [[ -f "${SKILL_DIR}/${name}.md" ]]; then
    pass "Dispatched skill ${name}.md exists on disk"
  else
    fail "Dispatched skill ${name}.md is MISSING from skills/ (Phase 2 references it)"
    ALL_DISPATCHED_EXIST=false
  fi
done <<< "$DISPATCHED_SKILLS"

if $ALL_DISPATCHED_EXIST; then
  pass "All Phase 2 dispatch referents present on disk"
fi

# Count how many unique skills are dispatched (should be 3 or 4)
DISPATCH_COUNT=$(echo "$DISPATCHED_SKILLS" | grep -c . || true)
info "Unique skills dispatched: ${DISPATCH_COUNT}"

# Verify each dispatched skill has a get_skill_extra entry in install.sh
# (install.sh refactored from associative arrays to case functions — commit 3f4086a)
echo ""
echo "  Checking install.sh get_skill_extra entries for dispatched skills:"

# Extract function definitions once
GET_SKILL_EXTRA_WIN_DEF=$(sed -n '/^get_skill_extra_win()/,/^}/p' "${INSTALL_SH}" 2>/dev/null)
GET_SKILL_EXTRA_MAC_DEF=$(sed -n '/^get_skill_extra_mac()/,/^}/p' "${INSTALL_SH}" 2>/dev/null)

while IFS= read -r name; do
  [[ -z "$name" ]] && continue
  basename="${name}.md"
  
  # Check win function
  if [[ -n "$GET_SKILL_EXTRA_WIN_DEF" ]]; then
    eval "$GET_SKILL_EXTRA_WIN_DEF" 2>/dev/null
    WIN_RESULT=$(get_skill_extra_win "${basename}" 2>/dev/null || echo "")
    if [[ -n "$WIN_RESULT" ]]; then
      pass "install.sh get_skill_extra_win returns '${WIN_RESULT}' for ${basename}"
    else
      fail "install.sh get_skill_extra_win returns empty for ${basename} (needed for Windows platform)"
    fi
  else
    fail "install.sh is MISSING get_skill_extra_win function"
  fi
  
  # Check mac function
  if [[ -n "$GET_SKILL_EXTRA_MAC_DEF" ]]; then
    eval "$GET_SKILL_EXTRA_MAC_DEF" 2>/dev/null
    MAC_RESULT=$(get_skill_extra_mac "${basename}" 2>/dev/null || echo "")
    if [[ -n "$MAC_RESULT" ]]; then
      pass "install.sh get_skill_extra_mac returns '${MAC_RESULT}' for ${basename}"
    else
      fail "install.sh get_skill_extra_mac returns empty for ${basename} (needed for macOS/Linux platform)"
    fi
  else
    fail "install.sh is MISSING get_skill_extra_mac function"
  fi
done <<< "$DISPATCHED_SKILLS"

# =============================================================================
# 2. --govern Flag Adoption (every consumer in the Evidence Contract)
# =============================================================================
header "2 — --govern Flag Adoption in Downstream Skills"

# The Cross-Skill Evidence Contract says:
#   producer=governor, artifact=governance.md, consumers=plan, loop, qa
#   loaded via: --govern=<slug>

# Check every consumer skill parses --govern in its Input section
CONSUMER_SKILLS=("blackcow-plan" "blackcow-loop" "blackcow-qa")

echo "  Contract: governor → governance.md → consumers via --govern=<slug>"
echo "  Consumers to check: ${CONSUMER_SKILLS[*]}"
echo ""

for skill in "${CONSUMER_SKILLS[@]}"; do
  skill_file="${SKILL_DIR}/${skill}.md"
  if [[ ! -f "$skill_file" ]]; then
    fail "Consumer skill ${skill}.md NOT FOUND on disk"
    continue
  fi

  # Check for --govern=<slug> in the Input section (first ~50 lines)
  if grep -q -- '--govern=' "$skill_file" 2>/dev/null; then
    pass "${skill}.md parses --govern flag (adopts governor contract)"
  else
    fail "${skill}.md does NOT parse --govern flag — contract broken (governor expects consumers to load governance.md via --govern=<slug>)"
  fi

  # Check for governance.md file path reference
  if grep -q "governance\.md" "$skill_file" 2>/dev/null; then
    info "${skill}.md explicitly references governance.md path"
  else
    info "${skill}.md does not name governance.md explicitly (may use slug-based path construction)"
  fi
done

# Check that skill-review (also dispatched) does NOT need --govern
# (It's not in the contract table, so it's fine if it doesn't have it)
SKILL_REVIEW_FILE="${SKILL_DIR}/blackcow-skill-review.md"
if grep -q -- '--govern=' "$SKILL_REVIEW_FILE" 2>/dev/null; then
  info "blackcow-skill-review.md has --govern flag (not required by contract, but future-compatible)"
else
  pass "blackcow-skill-review.md correctly does NOT require --govern (not in Evidence Contract)"
fi

# =============================================================================
# 3. Cross-Skill Evidence Contract — verify each row has a matching handshake
# =============================================================================
header "3 — Cross-Skill Evidence Contract Alignment"

echo "  Verifying each contract row has a matching producer→consumer handshake ..."
echo ""

# Row 1: governor → governance.md → plan, loop, qa  (via --govern=<slug>)
echo "  ── Row 1: blackcow-governor → .omo/governor/<slug>-governance.md → plan, loop, qa"
if grep -q -e '--govern=' "${SKILL_DIR}/blackcow-plan.md" 2>/dev/null; then
  pass "  plan: loads governor artifact via --govern=<slug>"
else
  fail "  plan: MISSING --govern=<slug> parsing"
fi
if grep -q -e '--govern=' "${SKILL_DIR}/blackcow-loop.md" 2>/dev/null; then
  pass "  loop: loads governor artifact via --govern=<slug>"
else
  fail "  loop: MISSING --govern=<slug> parsing"
fi
if grep -q -e '--govern=' "${SKILL_DIR}/blackcow-qa.md" 2>/dev/null; then
  pass "  qa:   loads governor artifact via --govern=<slug>"
else
  fail "  qa:   MISSING --govern=<slug> parsing"
fi

# Row 2: plan → plans/<slug>.md → loop  (via "Execute plans/<slug>.md")
echo ""
echo "  ── Row 2: blackcow-plan → plans/<slug>.md → loop"
if grep -q "plans/" "${SKILL_DIR}/blackcow-plan.md" 2>/dev/null; then
  pass "  plan: writes plans/<slug>.md"
else
  fail "  plan: does NOT reference plans/ output"
fi
if grep -q "plans/" "${SKILL_DIR}/blackcow-loop.md" 2>/dev/null; then
  pass "  loop: reads plans/<slug>.md (referenced in Input or body)"
else
  ## fallback: check for "Execute plans" in the Input description
  if grep -q -i "plan reference\|Execute.*plan" "${SKILL_DIR}/blackcow-loop.md" 2>/dev/null; then
    pass "  loop: accepts plan reference (alternative contract handshake)"
  else
    fail "  loop: does NOT reference plans/ — contract row may be mismatched"
  fi
fi

# Row 3: loop → completion-report.md → qa, governor, librarian
echo ""
echo "  ── Row 3: blackcow-loop → .omo/ulw-loop/completion-report.md → qa, governor, librarian"
if grep -q "completion-report" "${SKILL_DIR}/blackcow-loop.md" 2>/dev/null; then
  pass "  loop: writes completion-report.md"
else
  fail "  loop: does NOT reference completion-report.md"
fi
QA_LOADS_EVIDENCE=false
if grep -q "completion-report" "${SKILL_DIR}/blackcow-qa.md" 2>/dev/null; then
  pass "  qa: reads completion-report.md (evidence index)"
  QA_LOADS_EVIDENCE=true
else
  fail "  qa: does NOT reference completion-report.md — cannot load evidence index"
fi
if grep -q "completion-report" "${SKILL_DIR}/blackcow-governor.md" 2>/dev/null; then
  pass "  governor: loads completion-report.md (Phase 0.4 evidence index)"
else
  fail "  governor: does NOT reference completion-report.md — Phase 0.4 cannot load evidence"
fi
if grep -q "completion-report" "${SKILL_DIR}/blackcow-librarian.md" 2>/dev/null; then
  pass "  librarian: references completion-report.md"
else
  info "  librarian: may load completion-report indirectly (not a hard contract failure)"
fi

# Row 4: qa → qa-history.jsonl → librarian, governor
echo ""
echo "  ── Row 4: blackcow-qa → .omo/memory/qa-history.jsonl → librarian, governor"
if grep -q "qa-history" "${SKILL_DIR}/blackcow-qa.md" 2>/dev/null; then
  pass "  qa: writes qa-history.jsonl"
else
  fail "  qa: does NOT reference qa-history.jsonl"
fi
if grep -q "qa-history" "${SKILL_DIR}/blackcow-governor.md" 2>/dev/null; then
  pass "  governor: loads qa-history.jsonl (failure-pattern auto-population)"
else
  fail "  governor: does NOT reference qa-history.jsonl"
fi
if grep -q "qa-history\|failure-patterns" "${SKILL_DIR}/blackcow-librarian.md" 2>/dev/null; then
  pass "  librarian: references qa-history or failure-patterns"
else
  info "  librarian: may consume qa-history indirectly"
fi

# Row 5: librarian → structure-cache.jsonl → plan, loop, qa
echo ""
echo "  ── Row 5: blackcow-librarian → .omo/library/structure-cache.jsonl → plan, loop, qa"
if grep -q "structure-cache" "${SKILL_DIR}/blackcow-librarian.md" 2>/dev/null; then
  pass "  librarian: writes structure-cache.jsonl"
else
  fail "  librarian: does NOT reference structure-cache.jsonl"
fi
if grep -q "structure-cache\|cache" "${SKILL_DIR}/blackcow-plan.md" 2>/dev/null; then
  pass "  plan: loads structure cache from librarian"
else
  info "  plan: may load cache without explicit structure-cache name"
fi
if grep -q "structure-cache\|Phase 0 cache" "${SKILL_DIR}/blackcow-loop.md" 2>/dev/null; then
  pass "  loop: loads structure cache from librarian"
else
  info "  loop: may use cache indirectly"
fi
if grep -q "structure-cache\|Cache Load\|cache" "${SKILL_DIR}/blackcow-qa.md" 2>/dev/null; then
  pass "  qa: loads structure cache from librarian (Phase 0.0)"
else
  fail "  qa: does NOT reference structure cache — cannot load librarian artifacts"
fi

# Row 6: librarian → failure-patterns.jsonl → governor
echo ""
echo "  ── Row 6: blackcow-librarian → .omo/memory/failure-patterns.jsonl → governor"
if grep -q "failure-patterns" "${SKILL_DIR}/blackcow-librarian.md" 2>/dev/null; then
  pass "  librarian: writes failure-patterns.jsonl"
else
  fail "  librarian: does NOT reference failure-patterns.jsonl"
fi
if grep -q "failure-patterns" "${SKILL_DIR}/blackcow-governor.md" 2>/dev/null; then
  pass "  governor: loads failure-patterns.jsonl (Phase 0.1)"
else
  fail "  governor: does NOT reference failure-patterns.jsonl"
fi

# =============================================================================
# 3b. Phase 2 Dispatch Completeness — verify --govern=<slug> propagated to loop
# =============================================================================
header "3b — Phase 2 Dispatch --govern Propagation (Integration Gap Check)"

echo "  Checking that the governor passes --govern flag to each downstream skill..."
echo ""

# Extract the run_skill arguments from Phase 2 to check --govern propagation
PLAN_ARGS=$(grep -A1 'run_skill.*blackcow-plan' "${GOVERNOR_FILE}" 2>/dev/null | grep 'arguments' | head -1)
LOOP_ARGS=$(grep -A1 'run_skill.*blackcow-loop' "${GOVERNOR_FILE}" 2>/dev/null | grep 'arguments' | head -1)
QA_ARGS=$(grep -A1 'run_skill.*blackcow-qa' "${GOVERNOR_FILE}" 2>/dev/null | grep 'arguments' | head -1)

info "Plan dispatch args:   ${PLAN_ARGS}"
info "Loop dispatch args:   ${LOOP_ARGS}"
info "QA dispatch args:     ${QA_ARGS}"

# Plan must receive --govern=<slug>
if echo "$PLAN_ARGS" | grep -q -- '--govern=<slug>' 2>/dev/null; then
  pass "Phase 2 passes --govern=<slug> to blackcow-plan"
else
  fail "Phase 2 dispatch for blackcow-plan MISSING --govern=<slug> flag"
fi

# QA must receive --govern=<slug>  (contract says qa consumes governance.md via --govern)
# Note: qa also receives --gates=<selected> which is derived from governance
if echo "$QA_ARGS" | grep -q -- '--govern=<slug>' 2>/dev/null; then
  pass "Phase 2 passes --govern=<slug> to blackcow-qa"
else
  fail "Phase 2 dispatch for blackcow-qa MISSING --govern=<slug> flag"
fi

# Loop must receive --govern=<slug> (contract says loop consumes governance.md via --govern)
# The loop skill's Input section says it parses --govern=<slug>
# If the governor doesn't pass it, loop cannot load the governance decision
# Even though loop receives --gates=<selected> (derived from governance),
# the contract requires --govern=<slug> so loop can independently load
# PDCA budget, escalation rules, widening policy, etc.
if echo "$LOOP_ARGS" | grep -q -- '--govern=<slug>' 2>/dev/null; then
  pass "Phase 2 passes --govern=<slug> to blackcow-loop"
else
  fail "Phase 2 dispatch for blackcow-loop MISSING --govern=<slug> flag — loop supports it (line 23 of loop.md) but governor doesn't pass it. Loop receives --gates=<selected> but cannot load PDCA budget, escalation rules, or widening policy from governance.md independently."
fi

# =============================================================================
# 4. Model Tier Consistency — all 7 skills define same model_tiers
# =============================================================================
header "4 — Model Tier Definitions Across All Skills"

echo "  Checking model_tiers in all blackcow-*.md files..."
echo ""

# Collect all unique budget/pro model names from frontmatter model_tiers
ALL_SKILL_FILES=()
for f in "${SKILL_DIR}"/blackcow-*.md; do
  [[ -f "$f" ]] && ALL_SKILL_FILES+=("$f")
done

# Only extract model_tiers lines from frontmatter (between first and second ---)
# Strategy: find lines with exactly "  budget:" or "  pro:" (indented under model_tiers)
# that appear before the content body starts (i.e., before the second --- delimiter)
UNIQUE_BUDGET_MODELS=$(grep -h '^  budget: ' "${SKILL_DIR}"/blackcow-*.md 2>/dev/null | sort -u)
UNIQUE_PRO_MODELS=$(grep -h '^  pro: ' "${SKILL_DIR}"/blackcow-*.md 2>/dev/null | sort -u)

BUDGET_MODEL_COUNT=$(echo "$UNIQUE_BUDGET_MODELS" | grep -c . || echo "0")
PRO_MODEL_COUNT=$(echo "$UNIQUE_PRO_MODELS" | grep -c . || echo "0")

echo "  Unique budget-tier entries: ${BUDGET_MODEL_COUNT}"
if [[ "$BUDGET_MODEL_COUNT" -gt 0 ]]; then
  echo "$UNIQUE_BUDGET_MODELS" | sed 's/^/    /'
fi
echo "  Unique pro-tier entries: ${PRO_MODEL_COUNT}"
if [[ "$PRO_MODEL_COUNT" -gt 0 ]]; then
  echo "$UNIQUE_PRO_MODELS" | sed 's/^/    /'
fi
echo ""

# All budget entries should point to deepseek-v4-flash
BUDGET_OK=true
while IFS= read -r line; do
  if ! echo "$line" | grep -q "deepseek-v4-flash" 2>/dev/null; then
    fail "Budget tier variant does NOT use deepseek-v4-flash: ${line}"
    BUDGET_OK=false
  fi
done <<< "$UNIQUE_BUDGET_MODELS"

if $BUDGET_OK && [[ "$BUDGET_MODEL_COUNT" -ge 1 ]]; then
  pass "All budget-tier entries reference deepseek-v4-flash"
fi

# All pro entries should point to deepseek-v4-pro
PRO_OK=true
while IFS= read -r line; do
  if ! echo "$line" | grep -q "deepseek-v4-pro" 2>/dev/null; then
    fail "Pro tier variant does NOT use deepseek-v4-pro: ${line}"
    PRO_OK=false
  fi
done <<< "$UNIQUE_PRO_MODELS"

if $PRO_OK && [[ "$PRO_MODEL_COUNT" -ge 1 ]]; then
  pass "All pro-tier entries reference deepseek-v4-pro"
fi

# Every skill should have model_tiers section
SKILLS_WITH_MODEL_TIERS=0
for f in "${ALL_SKILL_FILES[@]}"; do
  basename=$(basename "$f")
  if grep -q "model_tiers:" "$f" 2>/dev/null; then
    ((SKILLS_WITH_MODEL_TIERS++))
    info "${basename} has model_tiers"
  else
    fail "${basename} is MISSING model_tiers frontmatter"
  fi
done

if [[ "$SKILLS_WITH_MODEL_TIERS" -eq "${#ALL_SKILL_FILES[@]}" ]]; then
  pass "All ${#ALL_SKILL_FILES[@]} skills define model_tiers in frontmatter"
fi

# Also verify model frontmatter field consistency
UNIQUE_MODELS=$(grep -h '^model:' "${SKILL_DIR}"/blackcow-*.md 2>/dev/null | sort -u)
MODEL_COUNT=$(echo "$UNIQUE_MODELS" | grep -c . || echo "0")
echo ""
echo "  Unique 'model:' declarations (top-level, not model_tiers):"
echo "$UNIQUE_MODELS" | sed 's/^/    /'

if [[ "$MODEL_COUNT" -eq 1 ]]; then
  MAIN_MODEL=$(echo "$UNIQUE_MODELS" | head -1 | sed 's/^model: *//')
  pass "All skills share the same top-level model: ${MAIN_MODEL}"
elif [[ "$MODEL_COUNT" -eq 2 ]]; then
  info "Two model variants found (expected if governor or skill-evolver differs)"
  # Check that governor uses deepseek-v4-pro (same as others)
  if grep -q '^model: deepseek-v4-pro' "${GOVERNOR_FILE}" 2>/dev/null; then
    pass "Governor uses deepseek-v4-pro (consistent with pipeline skills)"
  fi
else
  info "${MODEL_COUNT} unique model values found"
fi

# =============================================================================
# Summary
# =============================================================================
header "Summary"
echo "  Passed: ${PASS}"
echo "  Failed: ${FAIL}"
TOTAL=$((PASS + FAIL))
echo "  Total:  ${TOTAL}"

if [[ $FAIL -gt 0 ]]; then
  echo ""
  echo "  ❌ GOVERNOR INTEGRATION FAILURES:"
  for e in "${ERRORS[@]}"; do
    echo "    • ${e}"
  done
  exit 1
else
  echo ""
  echo "  ✅ All governor integration checks passed."
  echo "  Governor Phase 2 → downstream skill contracts validated."
fi
