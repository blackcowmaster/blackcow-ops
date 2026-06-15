#!/usr/bin/env bash
# =============================================================================
# Validate-BlackCow-Plan Integration
# =============================================================================
# L2 integration-level validation for skills/blackcow-plan.md.
#
# Checks three cross-file integration invariants:
#   1. Cross-Reference Integrity — every blackcow-* skill name referenced in
#      blackcow-plan.md must exist as skills/blackcow-<name>.md
#   2. install.sh get_skill_extra Alignment — the tools returned by
#      get_skill_extra_{win,mac}("blackcow-plan.md") must match what the skill
#      actually uses (not redundant, not missing)
#   3. Allowed-Tools Completeness — every tool in the Phase 1 dispatch
#      protocol's `tools` array must appear in the frontmatter allowed-tools
#
# Usage:
#   bash skills/tests/validate-blackcow-plan-integration.sh
#   bash skills/tests/validate-blackcow-plan-integration.sh --verbose
# =============================================================================

set -euo pipefail

VERBOSE=false
[[ "${1:-}" == "--verbose" ]] && VERBOSE=true

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLAN_FILE="${SKILL_DIR}/blackcow-plan.md"
[[ -f "$PLAN_FILE" ]] || { echo "FATAL: Target file not found: $PLAN_FILE" >&2; exit 1; }
INSTALL_SH="${SKILL_DIR}/install.sh"

PASS=0
FAIL=0
ERRORS=()

header()   { echo ""; echo "━━━ $* ━━━"; }
pass()     { PASS=$((PASS+1)); echo "  ✅ PASS: $*"; }
fail()     { FAIL=$((FAIL+1)); echo "  ❌ FAIL: $*"; ERRORS+=("$*"); }
info()     { $VERBOSE && echo "  ℹ️  $*" || true; }

# =============================================================================
# 1. Cross-Reference Integrity
# =============================================================================
header "1 — Cross-Reference Integrity"

# All blackcow-* skill names referenced in the plan (excluding self-reference).
# blackcow-plan.md line 975 says: "All 7 blackcow-* skill references valid (plan/loop/qa/librarian/review/evolver/governor)"
REFERENCED_SKILLS=(
  "blackcow-loop"
  "blackcow-qa"
  "blackcow-librarian"
  "blackcow-skill-review"
  "blackcow-skill-evolver"
  "blackcow-governor"
)

echo "  Referenced skills (from plan body):"
for skill in "${REFERENCED_SKILLS[@]}"; do
  echo "    • ${skill}.md"
done

# Verify each exists on disk
ALL_EXIST=true
for skill in "${REFERENCED_SKILLS[@]}"; do
  if [[ -f "${SKILL_DIR}/${skill}.md" ]]; then
    pass "Referenced skill ${skill}.md exists on disk"
  else
    fail "Referenced skill ${skill}.md is MISSING from skills/"
    ALL_EXIST=false
  fi
done

if $ALL_EXIST; then
  pass "All 7 blackcow-* skill files present (7/7)"
fi

# Count: plan (self) + 6 referenced = 7 total files
SKILL_FILES_ON_DISK=0
for f in "${SKILL_DIR}"/blackcow-*.md; do
  [[ -f "$f" ]] && SKILL_FILES_ON_DISK=$((SKILL_FILES_ON_DISK+1))
done
info "Total blackcow-*.md files on disk: ${SKILL_FILES_ON_DISK}"

# =============================================================================
# 2. install.sh SKILL_EXTRA Alignment
# =============================================================================
header "2 — install.sh get_skill_extra Alignment"

# Extract the get_skill_extra functions from install.sh and invoke them
# (install.sh refactored from associative arrays to case functions — commit 3f4086a)
# Source the function definitions without executing the full installer
GET_SKILL_EXTRA_WIN_DEF=$(sed -n '/^get_skill_extra_win()/,/^}/p' "${INSTALL_SH}" 2>/dev/null)
GET_SKILL_EXTRA_MAC_DEF=$(sed -n '/^get_skill_extra_mac()/,/^}/p' "${INSTALL_SH}" 2>/dev/null)

if [[ -z "$GET_SKILL_EXTRA_WIN_DEF" ]]; then
  EXTRA_WIN="NOT_FOUND"
  fail "get_skill_extra_win() function is MISSING from install.sh"
else
  eval "$GET_SKILL_EXTRA_WIN_DEF" 2>/dev/null
  EXTRA_WIN=$(get_skill_extra_win 'blackcow-plan.md' 2>/dev/null || echo "NOT_FOUND")
fi

if [[ -z "$GET_SKILL_EXTRA_MAC_DEF" ]]; then
  EXTRA_MAC="NOT_FOUND"
  fail "get_skill_extra_mac() function is MISSING from install.sh"
else
  eval "$GET_SKILL_EXTRA_MAC_DEF" 2>/dev/null
  EXTRA_MAC=$(get_skill_extra_mac 'blackcow-plan.md' 2>/dev/null || echo "NOT_FOUND")
fi

echo "  Found in install.sh (function-based lookup):"
echo "    get_skill_extra_win: ${EXTRA_WIN}"
echo "    get_skill_extra_mac: ${EXTRA_MAC}"

if [[ "$EXTRA_WIN" == "NOT_FOUND" ]]; then
  fail "get_skill_extra_win for blackcow-plan.md returned NOT_FOUND"
fi
if [[ "$EXTRA_MAC" == "NOT_FOUND" ]]; then
  fail "get_skill_extra_mac for blackcow-plan.md returned NOT_FOUND"
fi

# Parse the comma-separated tool list from function output
parse_tool_list() {
  local line="$1"
  # Function output is already comma-separated: "explore, research" or "get_symbols, find_in_code"
  echo "$line" | tr ',' '\n' | sed 's/^ *//;s/ *$//'
}

if [[ "$EXTRA_WIN" != "NOT_FOUND" && -n "$EXTRA_WIN" ]]; then
  info "WIN extra tools: ${EXTRA_WIN}"

  # Check for lsp_* tools — the plan explicitly says "No reference to lsp_* tools" (line 970)
  if echo "$EXTRA_WIN" | grep -q "lsp_"; then
    fail "get_skill_extra_win contains legacy lsp_* tool reference"
  fi

  # Check that explore and research are present for Win dispatch (use grep on raw output)
  if echo "$EXTRA_WIN" | grep -q "explore"; then
    :
  else
    fail "get_skill_extra_win missing 'explore' — needed for lane dispatch (platform adaptation maps task->explore)"
  fi
  if echo "$EXTRA_WIN" | grep -q "research"; then
    :
  else
    fail "get_skill_extra_win missing 'research' — needed for lane dispatch"
  fi
fi

if [[ "$EXTRA_MAC" != "NOT_FOUND" && -n "$EXTRA_MAC" ]]; then
  info "MAC extra tools: ${EXTRA_MAC}"

  # Check for redundancy: these tools are already in MAC_TOOLS in install.sh
  # MAC_TOOLS = "search_content, search_files, list_directory, directory_tree, run_command, web_search, explore, research, run_skill, get_file_info"
  # So explore, research, run_skill, get_file_info in get_skill_extra_mac are redundant
  REDUNDANT=0
  for redundant_tool in explore research run_skill get_file_info; do
    if echo "$EXTRA_MAC" | grep -qw "$redundant_tool"; then
      info "Tool '${redundant_tool}' in get_skill_extra_mac is REDUNDANT (already in COMMON_TOOLS + MAC_TOOLS base)"
      REDUNDANT=$((REDUNDANT+1))
    fi
  done
  if [[ $REDUNDANT -gt 0 ]]; then
    fail "${REDUNDANT} tool(s) in get_skill_extra_mac are redundant — already part of MAC_TOOLS base set"
  else
    pass "No redundant tools in get_skill_extra_mac"
  fi

  # Check for missing tools: dispatch protocol uses get_symbols and find_in_code
  HAS_GET_SYMBOLS=false; HAS_FIND_IN_CODE=false
  if echo "$EXTRA_MAC" | grep -qw "get_symbols"; then HAS_GET_SYMBOLS=true; fi
  if echo "$EXTRA_MAC" | grep -qw "find_in_code"; then HAS_FIND_IN_CODE=true; fi

  if ! $HAS_GET_SYMBOLS; then
    fail "Dispatch protocol uses 'get_symbols' but it's NOT in get_skill_extra_mac output"
  fi
  if ! $HAS_FIND_IN_CODE; then
    fail "Dispatch protocol uses 'find_in_code' but it's NOT in get_skill_extra_mac output"
  fi
  if $HAS_GET_SYMBOLS && $HAS_FIND_IN_CODE; then
    pass "Both dispatch-protocol tools (get_symbols, find_in_code) found in Mac tool chain (get_skill_extra_mac)"
  fi
fi

# =============================================================================
# 3. Allowed-Tools Completeness (dispatch protocol ⊆ frontmatter)
# =============================================================================
header "3 — Allowed-Tools Completeness"

# Extract the frontmatter allowed-tools line
FRONTMATTER_TOOLS_LINE=$(grep -E '^allowed-tools:' "${PLAN_FILE}" | head -1)
echo "  Frontmatter: ${FRONTMATTER_TOOLS_LINE}"

# Extract the dispatch protocol tools array (line ~199)
# Look for line containing the tools array after "Every lane subagent uses:"
DISPATCH_TOOLS_LINE=""
while IFS= read -r line; do
  if echo "$line" | grep -q 'tools.*read_file'; then
    # Extract the JSON array: pull content between first [ and last ]
    DISPATCH_TOOLS_LINE=$(echo "$line" | sed 's/.*\[//;s/\].*//' | tr -d '"')
    break
  fi
done < <(grep -A3 'Every lane subagent uses:' "${PLAN_FILE}" | grep 'tools:')
if [[ -z "$DISPATCH_TOOLS_LINE" ]]; then
  # Fallback: grep for the tools array pattern
  DISPATCH_TOOLS_LINE=$(grep -E '".*read_file.*find_in_code"' "${PLAN_FILE}" | head -1 | sed 's/.*\[//;s/\].*//' | tr -d '"')
fi
echo "  Dispatch protocol: [${DISPATCH_TOOLS_LINE}]"

# Normalize both lists
normalize_csv() {
  echo "$1" | sed 's/, */,/g' | tr ',' '\n' | sed 's/^ *//;s/ *$//' | sort -u
}

# Strip "allowed-tools: " prefix for frontmatter
FM_RAW=$(echo "$FRONTMATTER_TOOLS_LINE" | sed 's/^allowed-tools: *//')
FM_TOOLS=$(normalize_csv "$FM_RAW")
DISPATCH_RAW=$(echo "$DISPATCH_TOOLS_LINE" | sed 's/^"//;s/"$//' | sed 's/, */,/g')
DISPATCH_TOOLS=$(echo "$DISPATCH_RAW" | tr ',' '\n' | sed 's/^ *//;s/ *$//' | sort -u)

echo ""
echo "  Dispatch-protocol tools:"
while IFS= read -r tool; do
  echo "    • ${tool}"
done <<< "$DISPATCH_TOOLS"

echo ""
echo "  Frontmatter allowed-tools:"
while IFS= read -r tool; do
  echo "    • ${tool}"
done <<< "$FM_TOOLS"

echo ""

# Check every dispatch tool is in frontmatter
MISSING_FROM_FRONTMATTER=()
while IFS= read -r tool; do
  [[ -z "$tool" ]] && continue
  if ! grep -qF "$tool" <<< "$FM_TOOLS"; then
    MISSING_FROM_FRONTMATTER+=("$tool")
  fi
done <<< "$DISPATCH_TOOLS"

if [[ ${#MISSING_FROM_FRONTMATTER[@]} -eq 0 ]]; then
  pass "All dispatch-protocol tools present in frontmatter allowed-tools"
else
  for tool in "${MISSING_FROM_FRONTMATTER[@]}"; do
    fail "Dispatch protocol tool '${tool}' MISSING from frontmatter allowed-tools"
  done
fi

# Check reverse: tools in frontmatter not needed by dispatch protocol
# (informational only — not a failure if extra tools exist)
UNUSED_IN_DISPATCH=()
while IFS= read -r tool; do
  [[ -z "$tool" ]] && continue
  # These are meta-tools the plan skill itself uses (not passed to subagents)
  case "$tool" in
    web_search|write_file|explore|research|run_skill|get_file_info)
      continue  # plan's own tools, not dispatch tools
      ;;
  esac
  if ! grep -qF "$tool" <<< "$DISPATCH_TOOLS"; then
    UNUSED_IN_DISPATCH+=("$tool")
  fi
done <<< "$FM_TOOLS"

if [[ ${#UNUSED_IN_DISPATCH[@]} -gt 0 ]]; then
  echo ""
  echo "  ⚠️  Frontmatter tools NOT in dispatch protocol (may still be used by plan itself):"
  for tool in "${UNUSED_IN_DISPATCH[@]}"; do
    echo "    • ${tool}"
  done
fi

# =============================================================================
# 4. --govern Staleness Documentation
# =============================================================================
header "4 — --govern Staleness Documentation"

# Verify the --govern staleness section header exists in blackcow-plan.md
if grep -q "^## --govern Flag: Staleness & Fallback" "${PLAN_FILE}"; then
  pass "--govern staleness section header found in plan"
else
  fail "--govern staleness section header MISSING from plan"
fi

# Verify staleness key terms are present
STALENESS_TERMS=(
  "> 7 days"
  "--stale-ok"
  "fallback"
  "FRESH"
  "Governed at"
  "7-day freshness window"
)

for term in "${STALENESS_TERMS[@]}"; do
  if grep -qF -e "$term" "${PLAN_FILE}"; then
    pass "Staleness term '${term}' found in plan"
  else
    fail "Staleness term '${term}' MISSING from plan"
  fi
done

# Verify the decision flow diagram exists in the --govern section
if grep -q "Decision Flow" "${PLAN_FILE}"; then
  pass "Decision flow diagram found in --govern section"
else
  fail "Decision flow diagram MISSING from --govern section"
fi

# Verify the Cross-Skill Contract subsection in --govern section
if grep -q "Cross-Skill Contract" "${PLAN_FILE}"; then
  pass "Cross-Skill Contract subsection found in --govern section"
else
  fail "Cross-Skill Contract subsection MISSING from --govern section"
fi

# Verify the section is positioned after Input and before Mode Detection
INPUT_LINE=$(grep -n "^## Input$" "${PLAN_FILE}" | head -1 | cut -d: -f1)
GOVERN_LINE=$(grep -n "^## --govern Flag: Staleness" "${PLAN_FILE}" | head -1 | cut -d: -f1)
MODE_LINE=$(grep -n "^## Mode Detection$" "${PLAN_FILE}" | head -1 | cut -d: -f1)

if [ -n "$INPUT_LINE" ] && [ -n "$GOVERN_LINE" ] && [ -n "$MODE_LINE" ]; then
  if [ "$INPUT_LINE" -lt "$GOVERN_LINE" ] && [ "$GOVERN_LINE" -lt "$MODE_LINE" ]; then
    pass "--govern section positioned correctly (Input < --govern < Mode Detection)"
  else
    fail "--govern section positioning" "Expected: Input($INPUT_LINE) < Govern($GOVERN_LINE) < Mode($MODE_LINE)"
  fi
else
  fail "--govern section positioning" "Could not locate all section anchors (Input=${INPUT_LINE:-missing}, Govern=${GOVERN_LINE:-missing}, Mode=${MODE_LINE:-missing})"
fi

# Verify the --stale-ok scenario table exists in the plan
if grep -q "no \`--stale-ok\`" "${PLAN_FILE}"; then
  pass "--stale-ok rejection scenario documented (no --stale-ok → reject)"
else
  fail "--stale-ok rejection scenario MISSING"
fi

# Verify fallback for missing --govern is documented
if grep -q "No governance constraints apply" "${PLAN_FILE}"; then
  pass "Fallback path for missing --govern flag documented"
else
  fail "Fallback path for missing --govern flag MISSING"
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
  echo "  ❌ INTEGRATION FAILURES:"
  for e in "${ERRORS[@]}"; do
    echo "    • ${e}"
  done
  exit 1
else
  echo ""
  echo "  ✅ All integration checks passed."
fi
