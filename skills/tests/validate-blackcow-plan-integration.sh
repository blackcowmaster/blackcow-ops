#!/usr/bin/env bash
# =============================================================================
# Validate-BlackCow-Plan Integration
# =============================================================================
# L2 integration-level validation for skills/blackcow-plan.md.
#
# Checks three cross-file integration invariants:
#   1. Cross-Reference Integrity — every blackcow-* skill name referenced in
#      blackcow-plan.md must exist as skills/blackcow-<name>.md
#   2. install.sh SKILL_EXTRA Alignment — the tools listed in
#      SKILL_EXTRA_{WIN,MAC}["blackcow-plan.md"] must match what the skill
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
INSTALL_SH="${SKILL_DIR}/install.sh"

PASS=0
FAIL=0
ERRORS=()

header()   { echo ""; echo "━━━ $* ━━━"; }
pass()     { PASS=$((PASS+1)); echo "  ✅ PASS: $*"; }
fail()     { FAIL=$((FAIL+1)); echo "  ❌ FAIL: $*"; ERRORS+=("$*"); }
info()     { $VERBOSE && echo "  ℹ️  $*"; }

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
header "2 — install.sh SKILL_EXTRA Alignment"

# Extract the SKILL_EXTRA lines for blackcow-plan from install.sh
EXTRA_WIN=$(grep -E '^SKILL_EXTRA_WIN\["blackcow-plan\.md"\]=' "${INSTALL_SH}" || echo "NOT_FOUND")
EXTRA_MAC=$(grep -E '^SKILL_EXTRA_MAC\["blackcow-plan\.md"\]=' "${INSTALL_SH}" || echo "NOT_FOUND")

echo "  Found in install.sh:"
echo "    SKILL_EXTRA_WIN: ${EXTRA_WIN}"
echo "    SKILL_EXTRA_MAC: ${EXTRA_MAC}"

if [[ "$EXTRA_WIN" == "NOT_FOUND" ]]; then
  fail "SKILL_EXTRA_WIN[\"blackcow-plan.md\"] is MISSING from install.sh"
fi
if [[ "$EXTRA_MAC" == "NOT_FOUND" ]]; then
  fail "SKILL_EXTRA_MAC[\"blackcow-plan.md\"] is MISSING from install.sh"
fi

# Parse the tool lists out of the assignments
parse_tool_list() {
  local line="$1"
  # Extract value between the quotes after the =
  echo "$line" | sed -E 's/^[^=]+="(.*)"$/\1/'
}

if [[ "$EXTRA_WIN" != "NOT_FOUND" ]]; then
  WIN_TOOLS_STR=$(parse_tool_list "$EXTRA_WIN")
  IFS=', ' read -ra WIN_TOOLS <<< "$WIN_TOOLS_STR"
  info "WIN extra tools: ${WIN_TOOLS[*]}"

  # Check for lsp_* tools — the plan explicitly says "No reference to lsp_* tools" (line 970)
  for tool in "${WIN_TOOLS[@]}"; do
    if [[ "$tool" == lsp_* ]]; then
      fail "WIN SKILL_EXTRA contains legacy '${tool}' — plan skill says 'No reference to lsp_* tools' (line 970)"
    fi
  done

  # Check that explore and research are present for Win dispatch
  has_explore=false; has_research=false
  for tool in "${WIN_TOOLS[@]}"; do
    [[ "$tool" == "explore" ]] && has_explore=true
    [[ "$tool" == "research" ]] && has_research=true
  done
  $has_explore || fail "WIN SKILL_EXTRA missing 'explore' — needed for lane dispatch (platform adaptation maps task→explore)"
  $has_research || fail "WIN SKILL_EXTRA missing 'research' — needed for lane dispatch"
fi

if [[ "$EXTRA_MAC" != "NOT_FOUND" ]]; then
  MAC_TOOLS_STR=$(parse_tool_list "$EXTRA_MAC")
  IFS=', ' read -ra MAC_TOOLS <<< "$MAC_TOOLS_STR"
  info "MAC extra tools: ${MAC_TOOLS[*]}"

  # Check for redundancy: these tools are already in MAC_TOOLS in install.sh
  # MAC_TOOLS = "search_content, search_files, list_directory, directory_tree, run_command, web_search, explore, research, run_skill, get_file_info"
  # So explore, research, run_skill, get_file_info in SKILL_EXTRA_MAC are redundant
  REDUNDANT=0
  for tool in "${MAC_TOOLS[@]}"; do
    case "$tool" in
      explore|research|run_skill|get_file_info)
        info "Tool '${tool}' in SKILL_EXTRA_MAC is REDUNDANT (already in COMMON_TOOLS + MAC_TOOLS base)"
        REDUNDANT=$((REDUNDANT+1))
        ;;
    esac
  done
  if [[ $REDUNDANT -gt 0 ]]; then
    fail "${REDUNDANT} tool(s) in SKILL_EXTRA_MAC are redundant — already part of MAC_TOOLS base set"
  else
    pass "No redundant tools in SKILL_EXTRA_MAC"
  fi

  # Check for missing tools: dispatch protocol uses get_symbols and find_in_code
  # but neither MAC_TOOLS nor SKILL_EXTRA_MAC includes them
  HAS_GET_SYMBOLS=false; HAS_FIND_IN_CODE=false
  for tool in "${MAC_TOOLS[@]}"; do
    [[ "$tool" == "get_symbols" ]] && HAS_GET_SYMBOLS=true
    [[ "$tool" == "find_in_code" ]] && HAS_FIND_IN_CODE=true
  done
  # Also check in full MAC_TOOLS base
  BASE_MAC_TOOLS="search_content search_files list_directory directory_tree run_command web_search explore research run_skill get_file_info"
  for bt in $BASE_MAC_TOOLS; do
    [[ "$bt" == "get_symbols" ]] && HAS_GET_SYMBOLS=true
    [[ "$bt" == "find_in_code" ]] && HAS_FIND_IN_CODE=true
  done

  if ! $HAS_GET_SYMBOLS; then
    fail "Dispatch protocol uses 'get_symbols' but it's NOT in SKILL_EXTRA_MAC or MAC_TOOLS base"
  fi
  if ! $HAS_FIND_IN_CODE; then
    fail "Dispatch protocol uses 'find_in_code' but it's NOT in SKILL_EXTRA_MAC or MAC_TOOLS base"
  fi
  if $HAS_GET_SYMBOLS && $HAS_FIND_IN_CODE; then
    pass "Both dispatch-protocol tools (get_symbols, find_in_code) found in Mac tool chain"
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
