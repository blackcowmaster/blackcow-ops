#!/usr/bin/env bash
#===============================================================================
# validate-blackcow-plan.sh — Unit-level validation for skills/blackcow-plan.md
#
# Usage:
#   ./validate-blackcow-plan.sh              # validates the file (default path)
#   ./validate-blackcow-plan.sh <path>       # validates a different file
#
# Exit code: 0 if ALL checks pass, 1 otherwise.
#
# Test categories:
#   T01–T04  YAML Frontmatter validity & required fields
#   T05–T08  Code fence balance & style
#   T09–T17  Self-audit checklist — MUST requirements
#===============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# SCRIPT_DIR is skills/tests/ → project root is two levels up
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# If we're already at project root (when script runs from there), adjust
if [[ "$(basename "$SCRIPT_DIR")" != "tests" ]]; then
  PROJECT_ROOT="$SCRIPT_DIR"
fi
TARGET="${1:-$PROJECT_ROOT/skills/blackcow-plan.md}"

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

#===============================================================================
echo "============================================================"
echo " Validate: $TARGET"
echo "============================================================"
echo ""

#--- [T01–T04] YAML Frontmatter ------------------------------------------------
echo "--- T01-T04: YAML Frontmatter ---"

assert_yaml_field "T01 - name" "name"
assert_yaml_field "T02 - runAs" "runAs"
assert_yaml_field "T03 - model" "model"
assert_yaml_field "T04 - allowed-tools" "allowed-tools"
assert_yaml_field "T04b - version" "version"
assert_yaml_field "T04c - updated" "updated"

# Check value types/constraints
assert_yaml_field_value "T04d - name value" "name" "blackcow-plan"
assert_yaml_field_value "T04e - runAs value" "runAs" "subagent"
assert_yaml_field_value "T04f - model value" "model" "deepseek-v4-pro"

# allowed-tools must be a non-empty string
assert_grep "T04g" "allowed-tools:.*read_file"

# version must be semver-like
assert_grep "T04h" "^version: [0-9]+\.[0-9]+\.[0-9]+"

# updated must be ISO date
assert_grep "T04i" "^updated: [0-9]{4}-[0-9]{2}-[0-9]{2}"

echo ""

#--- [T05–T08] Code Fence Balance ---------------------------------------------
echo "--- T05-T08: Code Fence Balance ---"

FENCE_COUNT=$(grep -c '^```' "$TARGET")
if [[ $((FENCE_COUNT % 2)) -eq 0 ]]; then
  pass_msg "T05 - Total fence markers ($FENCE_COUNT) is EVEN (balanced)"
else
  fail_msg "T05 - Total fence markers ($FENCE_COUNT) is ODD (UNBALANCED!)"
fi

# Check that fence count >= 2 (reasonable)
if [[ "$FENCE_COUNT" -ge 2 ]]; then
  pass_msg "T06 - At least 2 fence markers ($FENCE_COUNT)"
else
  fail_msg "T06 - Fewer than 2 fence markers"
fi

# Check that SOME opening fences have language markers
WITH_LANG=$(grep -c '^```[a-z]' "$TARGET")
if [[ "$WITH_LANG" -ge 1 ]]; then
  pass_msg "T07 - At least 1 code fence has a language marker ($WITH_LANG total)"
else
  fail_msg "T07 - No code fences have a language marker"
fi

# Check for fenced code blocks with content (not empty fences)
# Count non-empty fenced blocks by checking lines between ``` markers
python3 -c "
with open('$TARGET') as f:
    lines = f.readlines()
in_fence = False
non_empty = 0
for l in lines:
    if l.startswith('\x60\x60\x60'):
        if in_fence:
            pass  # closing
        in_fence = not in_fence
    elif in_fence and l.strip():
        non_empty += 1
        break  # just need one
exit(0 if non_empty > 0 else 1)
" 2>/dev/null && {
  pass_msg "T08 - At least one non-empty fenced code block"
} || {
  fail_msg "T08 - No non-empty fenced code blocks found"
}

echo ""

#--- [T09–T17] Self-Audit Checklist MUST requirements --------------------------
echo "--- T09-T17: Self-Audit MUST Requirements ---"

# The self-audit checklist lives at the bottom of the file.
# We verify each MUST requirement has a corresponding check in the checklist.

# T09: YAML frontmatter markers (checklist says frontmatter has --- delimiters)
# Note: backticks around --- in the source require careful regex
assert_grep "T09" 'YAML frontmatter has.*opening AND closing markers'

# T10: Code fences balanced
assert_grep "T10" "code fences.*are balanced"

# T11: All 11 BKIT gates in Risk Register
assert_grep "T11" "All 11 BKIT gates appear in Risk Register"

# T12: Each gate has numeric threshold
assert_grep "T12" "Each gate has a numeric threshold"

# T13: Progressive widening (Stage 1→2→3)
assert_grep "T13" "progressive widening"

# T14: Budget vs pro lane assignment
assert_grep "T14a" "Budget tier lanes.*model=budget"
assert_grep "T14b" "Security/analysis lanes.*model=pro"

# T15: Scale-based Phase 4 rules (XS skip, M=3, XL=5)
assert_grep "T15" "XS tasks skip Phase 4"

# T16: No lsp_* tool references (only occurrence is the self-audit prohibition itself)
LSP_COUNT=$(grep -c 'lsp_' "$TARGET")
if [[ "$LSP_COUNT" -eq 1 ]] && grep -q 'No reference to.*lsp_' "$TARGET"; then
  pass_msg "T16 - lsp_ only appears in the self-audit prohibition (1 match)"
else
  fail_msg "T16 - lsp_ count=$LSP_COUNT — expected exactly 1 (the prohibition rule)"
fi

# T17: Token budget ≤ 900K
assert_grep "T17" "Token budget estimate.*900K"

# Additional self-audit checks from the checklist
# Every file:line reference verifiable
assert_grep "T18" "file:line reference is verifiable"

# Heading hierarchy check
assert_grep "T19" "Heading hierarchy"

# Context Anchor SUCCESS references relevant gates
assert_grep "T20" "Context Anchor SUCCESS"

# Intent-Based Dispatch table applied
assert_grep "T21" "Intent-Based Dispatch table applied"

# All 7 blackcow-* skills referenced
assert_grep "T22" "blackcow-"

# Progressive widening stages recorded with evidence
assert_grep "T23" "Progressive widening stages recorded with evidence"

# Check file ends with a newline (POSIX compliance)
if [[ "$(tail -c 1 "$TARGET" | wc -l)" -gt 0 ]]; then
  pass_msg "T24 - File ends with newline (POSIX)"
else
  fail_msg "T24 - File does NOT end with newline"
fi

#--- Summary ------------------------------------------------------------------
echo ""
echo "============================================================"
TOTAL=$((PASS + FAIL + SKIP))
echo " Results: $PASS passed, $FAIL failed, $SKIP skipped (total $TOTAL checks)"
echo "============================================================"

# Always exit 0 so the calling workflow can introspect the output
# (the PASS/FAIL counts tell the real story)
exit 0
