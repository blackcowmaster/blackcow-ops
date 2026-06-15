#!/usr/bin/env bash
# ============================================================================
# validate-blackcow-governor-contract.sh
# Contract-level validation for skills/blackcow-governor.md
#
# Verifies the governance decision template's data shape:
#   1. Skill file exists with correct frontmatter
#   2. Governance template (inside Phase 1 code block) produces valid markdown
#      with exactly 8 tables
#   3. Each table has the correct column headers
#   4. All enum fields use valid values (Mode, Trust Level, O-Level)
#   5. All 11 gates (M1-M5, S1-S3, P1-P3) are present in Gate Selection
#   6. Failure-Pattern Feed has correct effectiveness thresholds
#
# Usage: ./skills/tests/validate-blackcow-governor-contract.sh
# Returns: 0 if all contracts pass, 1 otherwise
# ============================================================================

set -euo pipefail

SKILL_FILE="skills/blackcow-governor.md"
HOMEDIR_SKILL="$HOME/.reasonix/skills/blackcow-governor.md"
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

pass() {
    local test_name="$1"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo "  ✅ PASS: $test_name"
}

fail() {
    local test_name="$1"
    local detail="${2:-}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo "  ❌ FAIL: $test_name${detail:+ — $detail}"
}

heading() {
    echo ""
    echo "━━━ $1 ━━━"
}

# === Helper: extract the Phase 1 governance template code block ===
# The template is inside a ```markdown fence in Phase 1.
extract_template() {
    awk 'BEGIN{in_fence=0; phase1=0}
        /^## Phase 1/ {phase1=1}
        phase1 && /^```markdown/ {in_fence=1; next}
        phase1 && in_fence && /^```/ {exit}
        in_fence {print}' "$SKILL_FILE"
}

# -------- 1. FILE EXISTENCE & INVOKABILITY --------
heading "1. File Existence & Invokability"

TOTAL_TESTS=$((TOTAL_TESTS + 1))
[[ -f "$SKILL_FILE" ]] || { echo "FATAL: Target file not found: $SKILL_FILE" >&2; exit 1; }
pass "Skill file exists at $SKILL_FILE"

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -f "$HOMEDIR_SKILL" ]; then
    pass "Skill file exists at $HOMEDIR_SKILL (run_skill target)"
else
    fail "Skill file exists at $HOMEDIR_SKILL (run_skill target)" \
         "The skill must be installed under ~/.reasonix/skills/ for run_skill to find it"
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if grep -q '^name: blackcow-governor' "$SKILL_FILE"; then
    pass "Frontmatter name matches 'blackcow-governor' (run_skill identifier)"
else
    fail "Frontmatter name matches 'blackcow-governor'"
fi

# -------- 2. GOVERNANCE TEMPLATE: EXACTLY 8 TABLES --------
heading "2. Template Table Count (must be exactly 8)"

TEMPLATE=$(extract_template)

# Count table header rows: lines that start with "|" and have a separator row
# (line with |---|---) below them. Simpler: count header rows that match
# markdown table header patterns.
TABLE_HEADERS=$(echo "$TEMPLATE" | grep -c '^| [A-Za-z].*|.*|$')
# More precise: count lines that look like markdown table headers
# (| word | word | ... |) followed by a separator line
TABLE_HEADER_LINES=$(echo "$TEMPLATE" | grep -cE '^\|[ A-Za-z_-]+(\|[ A-Za-z_-]+)+\|$')

TOTAL_TESTS=$((TOTAL_TESTS + 1))
# Count tables by counting separator rows (|---|...)
TABLE_COUNT=$(echo "$TEMPLATE" | grep -cE '^\|[- ]+\|')
if [ "$TABLE_COUNT" -eq 8 ]; then
    pass "Template contains exactly 8 tables (counted: $TABLE_COUNT)"
else
    fail "Template table count" "Expected 8, found $TABLE_COUNT. Extract returned $(echo "$TEMPLATE" | wc -l) lines"
fi

# -------- 3. TABLE COLUMN HEADERS --------
heading "3. Table Column Headers"

# 3a. Metadata table: | Field | Value |
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$TEMPLATE" | grep -q '^| Field | Value |'; then
    pass "Metadata table: headers are | Field | Value |"
else
    fail "Metadata table: headers" "Expected | Field | Value |"
fi

# 3b. Mode Selection: | Decision | Value | Rationale |
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$TEMPLATE" | grep -q '^| Decision | Value | Rationale |'; then
    pass "Mode Selection: headers are | Decision | Value | Rationale |"
else
    fail "Mode Selection: headers" "Expected | Decision | Value | Rationale |"
fi

# 3c. Gate Selection: | Gate | Run? | Trigger Signal |
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$TEMPLATE" | grep -q '^| Gate | Run? | Trigger Signal |'; then
    pass "Gate Selection: headers are | Gate | Run? | Trigger Signal |"
else
    fail "Gate Selection: headers" "Expected | Gate | Run? | Trigger Signal |"
fi

# 3d. Observable Level: | Decision | Value |
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$TEMPLATE" | grep -q '^| Decision | Value |$'; then
    pass "Observable Level: headers are | Decision | Value |"
else
    fail "Observable Level: headers" "Expected | Decision | Value |"
fi

# 3e. Progressive Widening Policy: | Stage | Trigger Threshold | Max Lanes |
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$TEMPLATE" | grep -q '^| Stage | Trigger Threshold | Max Lanes |'; then
    pass "Progressive Widening Policy: headers are | Stage | Trigger Threshold | Max Lanes |"
else
    fail "Progressive Widening Policy: headers" "Expected | Stage | Trigger Threshold | Max Lanes |"
fi

# 3f. Escalation Rules: | Rule | Trigger | Action |
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$TEMPLATE" | grep -q '^| Rule | Trigger | Action |'; then
    pass "Escalation Rules: headers are | Rule | Trigger | Action |"
else
    fail "Escalation Rules: headers" "Expected | Rule | Trigger | Action |"
fi

# 3g. Failure-Pattern Feed: | Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$TEMPLATE" | grep -q '^| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |'; then
    pass "Failure-Pattern Feed: headers are | Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |"
else
    fail "Failure-Pattern Feed: headers" "Expected 6-column header"
fi

# 3h. Loop ROI Estimate: | Metric | Estimate |
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$TEMPLATE" | grep -q '^| Metric | Estimate |'; then
    pass "Loop ROI Estimate: headers are | Metric | Estimate |"
else
    fail "Loop ROI Estimate: headers" "Expected | Metric | Estimate |"
fi


# -------- 4. ENUM FIELD VALIDATION --------
heading "4. Enum Field Values"

# 4a. Mode values must include FAST, STANDARD, FULL, SIEGE, ESCALATE
TOTAL_TESTS=$((TOTAL_TESTS + 1))
MODE_LINE=$(echo "$TEMPLATE" | grep '| \*\*Mode\*\* |')
if echo "$MODE_LINE" | grep -q 'FAST'; then
    pass "Mode enum: contains FAST"
else
    fail "Mode enum: FAST missing"
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$MODE_LINE" | grep -q 'STANDARD'; then
    pass "Mode enum: contains STANDARD"
else
    fail "Mode enum: STANDARD missing"
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$MODE_LINE" | grep -q 'FULL'; then
    pass "Mode enum: contains FULL"
else
    fail "Mode enum: FULL missing"
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$MODE_LINE" | grep -q 'SIEGE'; then
    pass "Mode enum: contains SIEGE"
else
    fail "Mode enum: SIEGE missing"
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$MODE_LINE" | grep -q 'ESCALATE'; then
    pass "Mode enum: contains ESCALATE"
else
    fail "Mode enum: ESCALATE missing"
fi

# 4b. Trust Level values L0-L4
TOTAL_TESTS=$((TOTAL_TESTS + 1))
TRUST_LINE=$(echo "$TEMPLATE" | grep '| \*\*Trust Level\*\* |')
if echo "$TRUST_LINE" | grep -q 'L0-L4'; then
    pass "Trust Level: range L0-L4 present"
else
    fail "Trust Level: range L0-L4" "Got: $TRUST_LINE"
fi

# Verify each individual trust level is valid in context (part of L0-L4 range)
for tl in L0 L1 L2 L3 L4; do
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    # Check that the trust level appears in context — either in the range "L0-L4"
    # or as a standalone reference within the document
    if grep -q "L0-L4" "$SKILL_FILE"; then
        pass "Trust Level $tl covered by range L0-L4 in skill file"
    else
        fail "Trust Level $tl covered by range L0-L4 in skill file"
    fi
done

# 4c. O-Level values O0-O4
TOTAL_TESTS=$((TOTAL_TESTS + 1))
OLEVEL_LINE=$(echo "$TEMPLATE" | grep '| \*\*O-Level\*\* |')
if echo "$OLEVEL_LINE" | grep -q 'O0 / O1 / O2 / O3 / O4'; then
    pass "O-Level: all 5 values (O0-O4) present"
else
    fail "O-Level: expected O0/O1/O2/O3/O4" "Got: $OLEVEL_LINE"
fi

# Also check for all five O-Level values individually
for ol in O0 O1 O2 O3 O4; do
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if echo "$OLEVEL_LINE" | grep -q "$ol"; then
        pass "O-Level value $ol present"
    else
        fail "O-Level value $ol missing"
    fi
done


# -------- 5. ALL 11 GATES IN GATE SELECTION --------
heading "5. Gate Selection — All 11 Gates"

GATES=(
    "M1 spec-match"
    "M2 test-pass"
    "M3 regression"
    "M4 lint"
    "M5 dead-code"
    "S1 dataFlow"
    "S2 auth"
    "S3 injection"
    "P1 query"
    "P2 memory"
    "P3 latency"
)

for gate in "${GATES[@]}"; do
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if echo "$TEMPLATE" | grep -q "^| $gate "; then
        pass "Gate '${gate}' present in Gate Selection table"
    else
        fail "Gate '${gate}' present in Gate Selection table"
    fi
done

# Verify exactly 11 gate rows (no more, no fewer)
TOTAL_TESTS=$((TOTAL_TESTS + 1))
# Extract the Gate Selection section and count rows starting with |
GATE_ROWS=$(echo "$TEMPLATE" \
    | awk '/^\| Gate \| Run\? \| Trigger Signal \|/{found=1; next} /^\|---/{if(found){sep=1; next}} found && sep && /^\| *M[0-9]/{count++; next} found && sep && /^\| *S[0-9]/{count++; next} found && sep && /^\| *P[0-9]/{count++; next} /^##/ && found{exit} END{print count+0}')
if [ "$GATE_ROWS" -eq 11 ]; then
    pass "Gate Selection has exactly 11 gate rows (counted: $GATE_ROWS)"
else
    fail "Gate Selection row count" "Expected 11 gates, found $GATE_ROWS"
fi

# Verify universal gates (M1, M2, M3) are always marked ✅ (not ✅/❌)
TOTAL_TESTS=$((TOTAL_TESTS + 1))
UNIVERSAL_OK=0
UNIVERSAL_FAIL=0
for ug in "M1 spec-match" "M2 test-pass" "M3 regression"; do
    ug_line=$(echo "$TEMPLATE" | grep "^| $ug ")
    if echo "$ug_line" | grep -q "✅$" || echo "$ug_line" | grep -q "✅ |"; then
        UNIVERSAL_OK=$((UNIVERSAL_OK + 1))
    else
        UNIVERSAL_FAIL=$((UNIVERSAL_FAIL + 1))
    fi
done
if [ "$UNIVERSAL_FAIL" -eq 0 ]; then
    pass "Universal gates (M1-M3) all marked ✅ (not conditional)"
else
    fail "Universal gates (M1-M3) all marked ✅" "Found $UNIVERSAL_FAIL gate(s) not marked ✅"
fi


# -------- 6. FAILURE-PATTERN FEED THRESHOLDS --------
heading "6. Failure-Pattern Feed — Effectiveness Thresholds"

# Feed rules embedded in the template (after the Failure-Pattern Feed table)
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$TEMPLATE" | grep -q 'effectiveness ≥ 80'; then
    pass "Feed rule: effectiveness ≥ 80 threshold present"
else
    fail "Feed rule: effectiveness ≥ 80" "Missing from template"
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$TEMPLATE" | grep -q 'effectiveness 40-79'; then
    pass "Feed rule: effectiveness 40-79 threshold present"
else
    fail "Feed rule: effectiveness 40-79" "Missing from template"
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$TEMPLATE" | grep -q 'effectiveness < 40'; then
    pass "Feed rule: effectiveness < 40 threshold present"
else
    fail "Feed rule: effectiveness < 40" "Missing from template"
fi

# Verify all three rules have correct associated actions
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$TEMPLATE" | grep -qE 'effectiveness ≥ 80.*apply known fix automatically'; then
    pass "Feed rule ≥80: action is 'apply known fix automatically'"
else
    fail "Feed rule ≥80: action mismatch"
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$TEMPLATE" | grep -qE 'effectiveness 40-79.*suggest fix, require confirmation'; then
    pass "Feed rule 40-79: action is 'suggest fix, require confirmation'"
else
    fail "Feed rule 40-79: action mismatch"
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$TEMPLATE" | grep -qE 'effectiveness < 40.*escalate gate priority'; then
    pass "Feed rule <40: action is 'escalate gate priority, do NOT auto-apply'"
else
    fail "Feed rule <40: action mismatch"
fi

# Additional: check reappeared_after_fix criticality rule
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$TEMPLATE" | grep -qE 'reappeared_after_fix.*CRITICAL'; then
    pass "Feed rule: reappeared_after_fix:true → CRITICAL marker present"
else
    fail "Feed rule: reappeared_after_fix:true → CRITICAL" "Missing from template"
fi


# -------- 7. INTEGRATION CONTRACT CROSS-REFERENCE --------
heading "7. Integration Contract — Downstream Skill References"

TOTAL_TESTS=$((TOTAL_TESTS + 1))
for downstream in "blackcow-plan" "blackcow-loop" "blackcow-qa"; do
    if grep -q "### ${downstream} reads" "$SKILL_FILE"; then
        pass "Integration contract section for $downstream present"
    else
        fail "Integration contract section for $downstream" "Missing ### ${downstream} reads"
    fi
done

# Check evidence contract cross-skill table
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if grep -q "Cross-Skill Evidence Contract" "$SKILL_FILE"; then
    pass "Cross-Skill Evidence Contract table present"
else
    fail "Cross-Skill Evidence Contract table" "Missing from skill file"
fi

# ------ SELF-AUDIT CHECKLIST --------
heading "8. Self-Audit Checklist Items"

CHECKLIST_ITEMS=(
    "Mode selection matches task scale"
    "Gate selection based on actual diff signals"
    "Observable level is achievable with available tooling"
    "Failure-pattern feed loaded from memory"
    "Loop ROI history consulted"
    "Escalation rules defined with concrete actions"
    "Governance document written to"
    "No invented diff signals or failure patterns"
    "Mode escalation justified by evidence"
    "All downstream skills.*honor governance"
    "Governance document loaded by at least one downstream skill"
    "Skill-review triggered for FULL/SIEGE modes"
    "Post-mortem review scheduled"
)

for item in "${CHECKLIST_ITEMS[@]}"; do
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if grep -q "$item" "$SKILL_FILE"; then
        pass "Checklist item: '${item}'"
    else
        fail "Checklist item: '${item}'" "Missing from Self-Audit Checklist"
    fi
done


# -------- 9. YAML FRONTMATTER SCHEMA --------
heading "9. YAML Frontmatter Schema"

FRONTMATTER=$(sed -n '/^---$/,/^---$/p' "$SKILL_FILE" | sed '1d;$d')

TOTAL_TESTS=$((TOTAL_TESTS + 1))
FM_OPEN=$(head -1 "$SKILL_FILE")
FM_CLOSE=$(grep -n "^---$" "$SKILL_FILE" | tail -1 | cut -d: -f1)
if [ "$FM_OPEN" = "---" ] && [ -n "$FM_CLOSE" ] && [ "$FM_CLOSE" -gt 1 ]; then
    pass "YAML frontmatter has opening AND closing --- markers"
else
    fail "YAML frontmatter markers"
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$FRONTMATTER" | grep -Eq '^name:\s+.+'; then
    pass "Field: name"
else
    fail "Field: name" "Missing or empty"
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$FRONTMATTER" | grep -Eq '^runAs:\s+subagent'; then
    pass "Field: runAs = subagent"
else
    fail "Field: runAs" "Expected 'subagent'"
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$FRONTMATTER" | grep -Eq '^model:\s+\S+'; then
    pass "Field: model (value: $(echo "$FRONTMATTER" | grep '^model:' | head -1 | sed 's/.*: *//'))"
else
    fail "Field: model" "Missing or empty"
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
TIER_BUDGET=$(echo "$FRONTMATTER" | grep -c 'budget:')
TIER_PRO=$(echo "$FRONTMATTER" | grep -c 'pro:')
if [ "$TIER_BUDGET" -ge 1 ] && [ "$TIER_PRO" -ge 1 ]; then
    pass "Field: model_tiers (budget + pro present)"
else
    fail "Field: model_tiers" "Expected 'budget:' and 'pro:' entries"
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
TOOLS=$(echo "$FRONTMATTER" | grep '^allowed-tools:' | sed 's/.*: *//')
if [ -n "$TOOLS" ]; then
    TOOL_COUNT=$(echo "$TOOLS" | tr ',' '\n' | wc -l | tr -d ' ')
    pass "Field: allowed-tools ($TOOL_COUNT tools listed)"
else
    fail "Field: allowed-tools" "Missing or empty"
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
VERSION=$(echo "$FRONTMATTER" | grep '^version:' | sed 's/.*: *//')
if echo "$VERSION" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$'; then
    pass "Field: version is valid semver ($VERSION)"
else
    fail "Field: version" "Expected semver (x.y.z), got '$VERSION'"
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
UPDATED=$(echo "$FRONTMATTER" | grep '^updated:' | sed 's/.*: *//')
if echo "$UPDATED" | grep -Eq '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'; then
    pass "Field: updated is ISO date ($UPDATED)"
else
    fail "Field: updated" "Expected ISO 8601 date (YYYY-MM-DD), got '$UPDATED'"
fi

# Check for version field matches across all blackcow-* skills (cross-skill consistency)
TOTAL_TESTS=$((TOTAL_TESTS + 1))
GOV_VERSION=$(echo "$FRONTMATTER" | grep '^version:' | sed 's/.*: *//')
if [ -f "skills/blackcow-plan.md" ]; then
    PLAN_VERSION=$(grep '^version:' skills/blackcow-plan.md | sed 's/.*: *//')
    if [ "$GOV_VERSION" = "$PLAN_VERSION" ]; then
        pass "Cross-skill version consistency: governor ($GOV_VERSION) matches plan ($PLAN_VERSION)"
    else
        fail "Cross-skill version consistency" "governor=$GOV_VERSION, plan=$PLAN_VERSION"
    fi
else
    fail "Cross-skill version consistency" "skills/blackcow-plan.md not found for comparison"
fi


# -------- SUMMARY --------
heading "TEST SUMMARY"

TOTAL_TESTS=$((PASSED_TESTS + FAILED_TESTS))
echo "  File under test: $SKILL_FILE"
echo "  Total tests:     $TOTAL_TESTS"
echo "  Passed:         $PASSED_TESTS"
echo "  Failed:         $FAILED_TESTS"

if [ "$FAILED_TESTS" -eq 0 ]; then
    echo ""
    echo "  ✅ ALL CONTRACTS VALIDATED — governance template data shape is correct"
    exit 0
else
    echo ""
    echo "  ❌ $FAILED_TESTS CONTRACT(S) BROKEN — review output above"
    exit 1
fi
