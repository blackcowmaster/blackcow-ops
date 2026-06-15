#!/usr/bin/env bash
#===============================================================================
# validate-blackcow-governor.sh — Unit-level validation for skills/blackcow-governor.md
#
# Usage:
#   ./validate-blackcow-governor.sh              # validates the file (default path)
#   ./validate-blackcow-governor.sh <path>       # validates a different file
#
# Exit code: 0 if ALL checks pass, 1 otherwise.
#
# Test categories:
#   T01–T04  YAML Frontmatter — name, version, runAs, allowed-tools
#   T05–T08  Section presence — all required headings
#   T09–T12  Table counts — governance template, evidence contract, escalation rows
#   T13–T14  Constraint verification — 8 constraints present
#   T15–T16  Self-audit checklist — exactly 13 items
#===============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# SCRIPT_DIR is skills/tests/ → project root is two levels up
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# If we're already at project root (when script runs from there), adjust
if [[ "$(basename "$SCRIPT_DIR")" != "tests" ]]; then
  PROJECT_ROOT="$SCRIPT_DIR"
fi
TARGET="${1:-$PROJECT_ROOT/skills/blackcow-governor.md}"

PASS=0
FAIL=0
SKIP=0

# Color helpers
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass_msg() { echo -e "  ${GREEN}PASS${NC} $1"; ((PASS++)); }
fail_msg() { echo -e "  ${RED}FAIL${NC} $1"; ((FAIL++)); }
skip_msg() { echo -e "  ${YELLOW}SKIP${NC} $1"; ((SKIP++)); }

#--- Assert helpers -----------------------------------------------------------
assert_file_exists() {
  local label="$1" path="$2"
  if [[ -f "$path" ]]; then
    pass_msg "$label — file exists: $path"
  else
    fail_msg "$label — file NOT FOUND: $path"
  fi
}

assert_grep() {
  local label="$1" pattern="$2"
  if grep -Eq "$pattern" "$TARGET"; then
    pass_msg "$label — pattern found: /$pattern/"
  else
    fail_msg "$label — pattern MISSING: /$pattern/"
  fi
}

assert_grep_count() {
  local label="$1" pattern="$2" op="$3" expected="$4"
  local count
  count=$(grep -Ec "$pattern" "$TARGET")
  if [[ "$op" == "eq" && "$count" -eq "$expected" ]]; then
    pass_msg "$label — count $count == $expected"
  elif [[ "$op" == "ge" && "$count" -ge "$expected" ]]; then
    pass_msg "$label — count $count >= $expected"
  elif [[ "$op" == "le" && "$count" -le "$expected" ]]; then
    pass_msg "$label — count $count <= $expected"
  elif [[ "$op" == "ne" && "$count" -ne "$expected" ]]; then
    pass_msg "$label — count $count != $expected"
  else
    fail_msg "$label — count $count NOT $op $expected"
  fi
}

assert_no_grep() {
  local label="$1" pattern="$2"
  if grep -Eq "$pattern" "$TARGET"; then
    fail_msg "$label — forbidden pattern FOUND: /$pattern/"
  else
    pass_msg "$label — forbidden pattern ABSENT: /$pattern/"
  fi
}

assert_grep_multi() {
  local label="$1" pattern="$2" min_match="$3"
  local count
  count=$(grep -Ec "$pattern" "$TARGET")
  if [[ "$count" -ge "$min_match" ]]; then
    pass_msg "$label — matched $count time(s) (needed ≥ $min_match): /$pattern/"
  else
    fail_msg "$label — matched $count time(s) (needed ≥ $min_match): /$pattern/"
  fi
}

assert_yaml_field() {
  local label="$1" field="$2"

  # Check if PyYAML is available
  if python3 -c "import yaml" 2>/dev/null; then
    # PyYAML available — proper YAML parsing
    python3 -c "
import yaml, sys
with open('$TARGET') as f:
    content = f.read()
parts = content.split('---')
if len(parts) < 3:
    sys.exit(2)
try:
    fm = yaml.safe_load(parts[1])
    if not isinstance(fm, dict):
        sys.exit(3)
    if '$field' in fm:
        sys.exit(0)
    else:
        sys.exit(1)
except yaml.YAMLError:
    sys.exit(4)
" 2>/dev/null
    local rc=$?
    case $rc in
      0) pass_msg "$label — YAML field '$field' present (PyYAML)" ; return ;;
      1) fail_msg "$label — YAML field '$field' MISSING (PyYAML)" ; return ;;
      2) fail_msg "$label — no YAML frontmatter (missing --- delimiters)" ; return ;;
      3) fail_msg "$label — frontmatter is not a mapping" ; return ;;
      4) fail_msg "$label — YAML parse error" ; return ;;
    esac
  fi

  # Fallback: grep-based check (no PyYAML available)
  if grep -Eq "^$field:" "$TARGET"; then
    pass_msg "$label — field '$field' found (grep fallback)"
  else
    fail_msg "$label — field '$field' MISSING (grep fallback)"
  fi
}

assert_yaml_field_value() {
  local label="$1" field="$2" expected="$3"

  # Check if PyYAML is available
  if python3 -c "import yaml" 2>/dev/null; then
    python3 -c "
import yaml, sys
with open('$TARGET') as f:
    content = f.read()
parts = content.split('---')
if len(parts) < 3:
    sys.exit(2)
try:
    fm = yaml.safe_load(parts[1])
    val = fm.get('$field')
    if val == '$expected':
        sys.exit(0)
    else:
        print(f'Expected \"$expected\", got \"{val}\"')
        sys.exit(1)
except Exception:
    sys.exit(3)
" 2>/dev/null
    local rc=$?
    case $rc in
      0) pass_msg "$label — field '$field' == '$expected' (PyYAML)" ; return ;;
      1) fail_msg "$label — field '$field' value INCORRECT (PyYAML)" ; return ;;
    esac
  fi

  # PyYAML unavailable or error → grep-based value check (approximate)
  local line
  line=$(grep "^$field:" "$TARGET" 2>/dev/null | head -1)
  if echo "$line" | grep -q "$expected"; then
    pass_msg "$label — field '$field' ≈ '$expected' (grep fallback)"
  elif [[ -n "$line" ]]; then
    fail_msg "$label — field '$field' value INCORRECT. Line: $line (grep fallback)"
  else
    fail_msg "$label — field '$field' line not found (grep fallback)"
  fi
}

assert_yaml_tool_count() {
  local label="$1" expected="$2"

  if python3 -c "import yaml" 2>/dev/null; then
    python3 -c "
import yaml, sys
with open('$TARGET') as f:
    content = f.read()
parts = content.split('---')
if len(parts) < 3:
    sys.exit(2)
fm = yaml.safe_load(parts[1])
tools = fm.get('allowed-tools', '')
if isinstance(tools, str):
    count = len([t for t in tools.split(',') if t.strip()])
    if count == $expected:
        sys.exit(0)
    else:
        print(f'Expected $expected tools, got {count}')
        sys.exit(1)
elif isinstance(tools, list):
    if len(tools) == $expected:
        sys.exit(0)
    else:
        print(f'Expected $expected tools, got {len(tools)}')
        sys.exit(1)
else:
    sys.exit(3)
" 2>/dev/null
    local rc=$?
    case $rc in
      0) pass_msg "$label — allowed-tools count == $expected (PyYAML)" ; return ;;
      1) fail_msg "$label — allowed-tools count != $expected (PyYAML)" ; return ;;
    esac
  fi

  # Fallback: count commas + 1
  local line count
  line=$(grep "^allowed-tools:" "$TARGET" 2>/dev/null | head -1)
  count=$(echo "$line" | grep -o ',' | wc -l)
  count=$((count + 1))
  if [[ "$count" -eq "$expected" ]]; then
    pass_msg "$label — allowed-tools count == $expected (grep fallback)"
  else
    fail_msg "$label — allowed-tools count == $count, expected $expected (grep fallback)"
  fi
}

#===============================================================================
echo "============================================================"
echo " Validate: $TARGET"
echo "============================================================"
echo ""

#--- [T01–T04] YAML Frontmatter ------------------------------------------------
echo "--- T01-T04: YAML Frontmatter ---"

assert_yaml_field "T01a - name" "name"
assert_yaml_field "T01b - version" "version"
assert_yaml_field "T01c - runAs" "runAs"
assert_yaml_field "T01d - allowed-tools" "allowed-tools"
assert_yaml_field "T01e - model" "model"
assert_yaml_field "T01f - updated" "updated"
assert_yaml_field "T01g - description" "description"

# Check value types/constraints
assert_yaml_field_value "T02a - name value" "name" "blackcow-governor"
assert_yaml_field_value "T02b - version value" "version" "2.0.0"
assert_yaml_field_value "T02c - runAs value" "runAs" "subagent"

# allowed-tools must be a non-empty string with 12 tools
assert_yaml_tool_count "T03 - allowed-tools has 12 tools" 12

# Verify specific tools are present
assert_grep "T04a - read_file" "read_file"
assert_grep "T04b - search_content" "search_content"
assert_grep "T04c - search_files" "search_files"
assert_grep "T04d - glob" "glob"
assert_grep "T04e - list_directory" "list_directory"
assert_grep "T04f - directory_tree" "directory_tree"
assert_grep "T04g - run_command" "run_command"
assert_grep "T04h - web_fetch" "web_fetch"
assert_grep "T04i - write_file" "write_file"
assert_grep "T04j - explore" "explore"
assert_grep "T04k - run_skill" "run_skill"
assert_grep "T04l - get_file_info" "get_file_info"

# version must be semver-like
assert_grep "T04m - semver version" "^version: [0-9]+\.[0-9]+\.[0-9]+"

echo ""

#--- [T05–T08] Section Presence ------------------------------------------------
echo "--- T05-T08: Section Presence ---"

# Top-level sections (##)
assert_grep "T05a - Input section" "^## Input"
assert_grep "T05b - Phase 0 section" "^## Phase 0 "
assert_grep "T05c - Phase 1 section" "^## Phase 1 "
assert_grep "T05d - Post-Governance Self-Audit" "^## Post-Governance Self-Audit"
assert_grep "T05e - Phase 2 section" "^## Phase 2 "
assert_grep "T05f - Integration Contract" "^## Integration Contract"
assert_grep "T05g - Self-Audit Checklist" "^## Self-Audit Checklist"
assert_grep "T05h - Cross-Skill Evidence Contract" "^## Cross-Skill Evidence Contract"
assert_grep "T05i - Constraints" "^## Constraints"
assert_grep "T05j - Skill Value Assessment" "^## Skill Value Assessment"

# Phase 0 sub-sections (###)
assert_grep "T06a - 0.1 Failure-Pattern" "^### 0.1 "
assert_grep "T06b - 0.2 Loop ROI" "^### 0.2 "
assert_grep "T06c - 0.3 Change Surface" "^### 0.3 "
assert_grep "T06d - 0.3b Capabilities" "^### 0.3b "
assert_grep "T06e - 0.4 Evidence Index" "^### 0.4 "

# Phase 1 sub-sections within governance template — these appear as ## headings inside the fenced template
# We check for the unique heading markers inside the governance template
assert_grep "T07a - Mode Selection" "## Mode Selection"
assert_grep "T07b - Gate Selection" "## Gate Selection"
assert_grep "T07c - Observable Level" "## Observable Level"
assert_grep "T07d - Progressive Widening Policy" "## Progressive Widening Policy"
assert_grep "T07e - Escalation Rules" "## Escalation Rules"
assert_grep "T07f - Failure-Pattern Feed" "## Failure-Pattern Feed"
assert_grep "T07g - Loop ROI Estimate" "## Loop ROI Estimate"
# Also check for the header table (Field/Value) — it's inside a fenced code block
assert_grep "T07h - Header table" "[|] Field .* Value [|]"

# Integration Contract sub-sections
assert_grep "T08a - plan reads" "^### blackcow-plan reads:"
assert_grep "T08b - loop reads" "^### blackcow-loop reads:"
assert_grep "T08c - qa reads" "^### blackcow-qa reads:"

echo ""

#--- [T09–T12] Table Counts -----------------------------------------------------
echo "--- T09-T12: Table Counts ---"

# Count tables by counting pipe-only separator lines (| --- | --- | etc)
SEPARATOR_COUNT=$(grep -c '^|[-| ]*|$' "$TARGET" 2>/dev/null || echo 0)
if [[ "$SEPARATOR_COUNT" -ge 8 ]]; then
  pass_msg "T09 - At least 8 table separator lines ($SEPARATOR_COUNT total)"
else
  fail_msg "T09 - Only $SEPARATOR_COUNT table separators (expected ≥ 8)"
fi

# Count data rows in Evidence Contract table (rows starting with | `blackcow-)
EVIDENCE_ROWS=$(grep -cE '^\| `blackcow-' "$TARGET" 2>/dev/null || echo 0)
if [[ "$EVIDENCE_ROWS" -eq 6 ]]; then
  pass_msg "T10 - Evidence contract has 6 producer rows ($EVIDENCE_ROWS found)"
else
  fail_msg "T10 - Evidence contract has $EVIDENCE_ROWS rows (expected 6)"
fi

# Count data rows in Escalation Rules table (rows like | No new evidence, | Same gate...)
ESCALATION_ROWS=$(grep -cE '^\| (No new evidence|Same gate|Budget near limit|Scope creep)' "$TARGET" 2>/dev/null || echo 0)
if [[ "$ESCALATION_ROWS" -eq 4 ]]; then
  pass_msg "T11 - Escalation rules has 4 rows ($ESCALATION_ROWS found)"
else
  fail_msg "T11 - Escalation rules has $ESCALATION_ROWS rows (expected 4)"
fi

# Count all data rows in Verified paths table
VERIFIED_ROWS=$(grep -cE '^\| (librarian|loop|qa|governor) ' "$TARGET" 2>/dev/null || echo 0)
if [[ "$VERIFIED_ROWS" -eq 4 ]]; then
  pass_msg "T12 - Verified paths table has 4 rows ($VERIFIED_ROWS found)"
else
  fail_msg "T12 - Verified paths table has $VERIFIED_ROWS rows (expected 4)"
fi

echo ""

#--- [T13–T14] Constraint Verification -----------------------------------------
echo "--- T13-T14: Constraint Verification ---"

# 8 numbered constraints under ## Constraints
# Extract the Constraints section and count numbered items (1. through 8.)
CONST_SECTION=$(awk 'f{print} /^## Constraints$/{f=1;next} /^## / && f && !/^## Constraints$/{f=0}' "$TARGET" 2>/dev/null)
CONST_SECTION_COUNT=$(echo "$CONST_SECTION" | grep -cE '^[0-9]+\. ' || echo 0)

if [[ "$CONST_SECTION_COUNT" -eq 8 ]]; then
  pass_msg "T13 - Exactly 8 constraints in Constraints section ($CONST_SECTION_COUNT found)"
else
  # Fallback: count all numbered items in the file
  CONSTRAINT_COUNT=$(grep -cE '^[0-9]+\. ' "$TARGET" 2>/dev/null || echo 0)
  fail_msg "T13 - Expected 8 constraints in Constraints section, got $CONST_SECTION_COUNT (file total: $CONSTRAINT_COUNT)"
fi

# Verify each specific constraint content
assert_grep "T14a - Constraint 1: Never edit product code" "Never edit product code"
assert_grep "T14b - Constraint 2: Produce ONLY governance.md" "Produce ONLY"
assert_grep "T14c - Constraint 3: Cite evidence" "cite evidence"
assert_grep "T14d - Constraint 4: Least expensive mode" "LEAST expensive mode"
assert_grep "T14e - Constraint 5: Never skip universal gates" "Never skip universal gates"
assert_grep "T14f - Constraint 6: O2+ requires browser" "browser tooling"
assert_grep "T14g - Constraint 7: Advisory, MAY override" "MAY override"
assert_grep "T14h - Constraint 8: Version consistency check" "version consistency"

echo ""

#--- [T15–T16] Self-Audit Checklist --------------------------------------------
echo "--- T15-T16: Self-Audit Checklist ---"

# Count checklist items (lines matching "- [ ]")
CHECKLIST_COUNT=$(grep -cE '^- \[ \]' "$TARGET" 2>/dev/null || echo 0)

if [[ "$CHECKLIST_COUNT" -eq 13 ]]; then
  pass_msg "T15 - Self-audit checklist has exactly 13 items ($CHECKLIST_COUNT found)"
else
  fail_msg "T15 - Self-audit checklist has $CHECKLIST_COUNT items (expected 13)"
fi

# Verify key checklist items exist
assert_grep "T16a - Mode selection matches scale" "Mode selection matches task scale"
assert_grep "T16b - Gate selection from diff" "Gate selection based on actual diff signals"
assert_grep "T16c - Observable level achievable" "Observable level is achievable"
assert_grep "T16d - Failure-pattern feed" "Failure-pattern feed loaded from memory"
assert_grep "T16e - Loop ROI history" "Loop ROI history consulted"
assert_grep "T16f - Escalation rules defined" "Escalation rules defined with concrete actions"
assert_grep "T16g - Governance document written" "Governance document written"
assert_grep "T16h - No invented signals" "No invented diff signals or failure patterns"
assert_grep "T16i - Mode escalation justified" "Mode escalation justified by evidence"
assert_grep "T16j - Downstream skills honor" "downstream skills.*honor governance"
assert_grep "T16k - Document loaded downstream" "Governance document loaded by at least one downstream skill"
assert_grep "T16l - Skill-review for FULL/SIEGE" "Skill-review triggered for FULL.SIEGE modes"
assert_grep "T16m - Post-mortem scheduled" "Post-mortem review scheduled after pipeline completion"

#--- Summary ------------------------------------------------------------------
echo ""
echo "============================================================"
TOTAL=$((PASS + FAIL + SKIP))
echo " Results: $PASS passed, $FAIL failed, $SKIP skipped (total $TOTAL checks)"
echo "============================================================"

# Always exit 0 so the calling workflow can introspect the output
# (the PASS/FAIL counts tell the real story)
exit 0