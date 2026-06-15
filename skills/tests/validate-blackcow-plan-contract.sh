#!/usr/bin/env bash
# ============================================================================
# validate-blackcow-plan-contract.sh
# Contract-level validation for skills/blackcow-plan.md
#
# Tests:
#   1. Skill file exists and is invokable via run_skill(name="blackcow-plan")
#   2. YAML frontmatter schema (name, runAs, model, model_tiers,
#      allowed-tools, version semver, updated ISO date)
#   3. All lane prompts (L1-L10) follow the "RETURN EXACTLY:" contract pattern
#   4. All review board prompts (RVA-RVE) follow the "RETURN EXACTLY:" pattern
#   5. Context Anchor template has all required fields (WHY, WHO, WHAT,
#      RISK, SUCCESS, SCOPE)
#
# Usage: ./skills/tests/validate-blackcow-plan-contract.sh
# Returns: 0 if all contracts pass, 1 otherwise
# ============================================================================

set -euo pipefail

SKILL_FILE="skills/blackcow-plan.md"
HOMEDIR_SKILL="$HOME/.reasonix/skills/blackcow-plan.md"
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

# -------- 1. FILE EXISTENCE & INVOKABILITY --------
heading "1. File Existence & Invokability"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [ -f "$SKILL_FILE" ]; then
    pass "Skill file exists at $SKILL_FILE"
else
    fail "Skill file exists at $SKILL_FILE"
fi

# The ~/.reasonix/skills/ copy is where the runtime actually reads from.
# Check it exists too (run_skill resolves from the skills index).
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -f "$HOMEDIR_SKILL" ]; then
    pass "Skill file exists at $HOMEDIR_SKILL (run_skill target)"
else
    fail "Skill file exists at $HOMEDIR_SKILL (run_skill target)" \
         "The skill must be installed under ~/.reasonix/skills/ for run_skill to find it"
fi

# Check that the name in frontmatter matches what run_skill expects
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if grep -q '^name: blackcow-plan' "$SKILL_FILE"; then
    pass "Frontmatter name matches 'blackcow-plan' (run_skill identifier)"
else
    fail "Frontmatter name matches 'blackcow-plan'"
fi


# -------- 2. YAML FRONTMATTER SCHEMA --------
heading "2. YAML Frontmatter Schema"

# Extract frontmatter (between leading --- and closing ---)
FRONTMATTER=$(sed -n '/^---$/,/^---$/p' "$SKILL_FILE" | sed '1d;$d')

# 2a. Must have opening and closing --- markers
TOTAL_TESTS=$((TOTAL_TESTS + 1))
FM_OPEN=$(head -1 "$SKILL_FILE")
FM_CLOSE=$(grep -n "^---$" "$SKILL_FILE" | tail -1 | cut -d: -f1)
if [ "$FM_OPEN" = "---" ] && [ -n "$FM_CLOSE" ] && [ "$FM_CLOSE" -gt 1 ]; then
    pass "YAML frontmatter has opening AND closing --- markers"
else
    fail "YAML frontmatter markers" "Expected opening '---' on line 1 and closing '---'"
fi

# 2b. name
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$FRONTMATTER" | grep -Eq '^name:\s+.+'; then
    pass "Field: name"
else
    fail "Field: name" "Missing or empty"
fi

# 2c. runAs: subagent
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$FRONTMATTER" | grep -Eq '^runAs:\s+subagent'; then
    pass "Field: runAs = subagent"
else
    fail "Field: runAs" "Expected 'subagent', got: $(echo "$FRONTMATTER" | grep '^runAs:' || echo 'missing')"
fi

# 2d. model (must have a value)
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$FRONTMATTER" | grep -Eq '^model:\s+\S+'; then
    pass "Field: model (value: $(echo "$FRONTMATTER" | grep '^model:' | head -1 | sed 's/.*: *//'))"
else
    fail "Field: model" "Missing or empty"
fi

# 2e. model_tiers (must list at least budget and pro)
TOTAL_TESTS=$((TOTAL_TESTS + 1))
TIER_BUDGET=$(echo "$FRONTMATTER" | grep -c 'budget:')
TIER_PRO=$(echo "$FRONTMATTER" | grep -c 'pro:')
if [ "$TIER_BUDGET" -ge 1 ] && [ "$TIER_PRO" -ge 1 ]; then
    pass "Field: model_tiers (budget + pro present)"
else
    fail "Field: model_tiers" "Expected 'budget:' and 'pro:' entries. Found budget=$TIER_BUDGET, pro=$TIER_PRO"
fi

# 2f. allowed-tools (must have at least one tool)
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$FRONTMATTER" | grep -Eq '^allowed-tools:\s+\S+'; then
    TOOL_COUNT=$(echo "$FRONTMATTER" | grep '^allowed-tools:' | sed 's/.*: *//' | tr ',' '\n' | wc -l | tr -d ' ')
    pass "Field: allowed-tools ($TOOL_COUNT tools listed)"
else
    fail "Field: allowed-tools" "Missing or empty"
fi

# 2g. version: must be semver (x.y.z, with optional pre-release)
TOTAL_TESTS=$((TOTAL_TESTS + 1))
VERSION=$(echo "$FRONTMATTER" | grep '^version:' | sed 's/.*: *//')
if echo "$VERSION" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$'; then
    pass "Field: version is valid semver ($VERSION)"
else
    fail "Field: version" "Expected semver (x.y.z), got '$VERSION'"
fi

# 2h. updated: must be ISO 8601 date (YYYY-MM-DD)
TOTAL_TESTS=$((TOTAL_TESTS + 1))
UPDATED=$(echo "$FRONTMATTER" | grep '^updated:' | sed 's/.*: *//')
if echo "$UPDATED" | grep -Eq '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'; then
    pass "Field: updated is ISO date ($UPDATED)"
else
    fail "Field: updated" "Expected ISO 8601 date (YYYY-MM-DD), got '$UPDATED'"
fi


# -------- 3. LANE PROMPTS — RETURN EXACTLY CONTRACT --------
heading "3. Lane Prompts — RETURN EXACTLY Pattern"

LANE_NAMES=("L1" "L2" "L3" "L4" "L5" "L6" "L7" "L8" "L9" "L10")
LANE_PROMPT_START_LINES=()
for lane in "${LANE_NAMES[@]}"; do
    line=$(grep -n "\\*\\*${lane}_PROMPT" "$SKILL_FILE" | head -1 | cut -d: -f1)
    LANE_PROMPT_START_LINES+=("$line")
done

# Check each lane prompt contains "RETURN EXACTLY"
for i in "${!LANE_NAMES[@]}"; do
    lane="${LANE_NAMES[$i]}"
    start="${LANE_PROMPT_START_LINES[$i]}"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ -z "$start" ]; then
        fail "Lane $lane prompt definition" "**${lane}_PROMPT — not found in $SKILL_FILE"
        continue
    fi

    # Find the next fence-closing (```) after the lane header to get the prompt body
    # Lanes are in a code fence block. The header is outside the fence, the prompt inside.
    # Strategy: read from start line, find the first ``` (opens fence), then find the next ```
    prompt_body=$(sed -n "${start},\$p" "$SKILL_FILE" \
        | awk 'BEGIN{in_fence=0} /^```/{if(in_fence==0){in_fence=1;next}else{exit}} in_fence{print}')


    if echo "$prompt_body" | grep -q "RETURN EXACTLY"; then
        pass "Lane $lane prompt — contains 'RETURN EXACTLY'"
    else
        fail "Lane $lane prompt — MISSING 'RETURN EXACTLY' pattern"
    fi
done


# -------- 4. REVIEW BOARD PROMPTS — RETURN EXACTLY CONTRACT --------
heading "4. Review Board Prompts — RETURN EXACTLY Pattern"

REVIEW_NAMES=("RVA" "RVB" "RVC" "RVD" "RVE")
for rev in "${REVIEW_NAMES[@]}"; do
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    # Review prompts are in code fences too, same structure
    rev_line=$(grep -n "\\*\\*${rev}_PROMPT" "$SKILL_FILE" | head -1 | cut -d: -f1)

    if [ -z "$rev_line" ]; then
        fail "Review $rev prompt definition" "**${rev}_PROMPT — not found in $SKILL_FILE"
        continue
    fi

    prompt_body=$(sed -n "${rev_line},\$p" "$SKILL_FILE" \
        | awk 'BEGIN{in_fence=0} /^```/{if(in_fence==0){in_fence=1;next}else{exit}} in_fence{print}')

    if echo "$prompt_body" | grep -q "RETURN EXACTLY"; then
        pass "Review $rev prompt — contains 'RETURN EXACTLY'"
    else
        fail "Review $rev prompt — MISSING 'RETURN EXACTLY' pattern"
    fi
done

# Also verify the Phase 3 design phase context anchor section reference
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if grep -q "RETURN EXACTLY" "$SKILL_FILE"; then
    total_return_exactly=$(grep -c "RETURN EXACTLY" "$SKILL_FILE")
    pass "Total 'RETURN EXACTLY' occurrences in file: $total_return_exactly (self-audit cross-check)"
else
    fail "No 'RETURN EXACTLY' found anywhere in the skill file" "The skill would be non-functional"
fi


# -------- 5. CONTEXT ANCHOR TEMPLATE FIELDS --------
heading "5. Context Anchor Template — Required Fields"

# There are TWO Context Anchor templates: one in Phase 3 (design output) and
# one in the Plan Template (final plan output). Both must have all 6 fields.

CONTEXT_ANCHOR_FIELDS=("WHY" "WHO" "WHAT" "RISK" "SUCCESS" "SCOPE")
CONTEXT_ANCHOR_OCCURRENCES=$(grep -c '\*\*WHY\*\*' "$SKILL_FILE")
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ "$CONTEXT_ANCHOR_OCCURRENCES" -ge 2 ]; then
    pass "Context Anchor template appears in ≥2 locations (Phase 3 + Plan Template)"
else
    fail "Context Anchor template appears in ≥2 locations" \
         "Found $CONTEXT_ANCHOR_OCCURRENCES occurrence(s); expected at least 2"
fi

for field in "${CONTEXT_ANCHOR_FIELDS[@]}"; do
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    count=$(grep -c "\\*\\*${field}\\*\\*" "$SKILL_FILE")
    if [ "$count" -ge 2 ]; then
        pass "Context Anchor field '${field}' present in ≥2 locations ($count total)"
    elif [ "$count" -eq 1 ]; then
        fail "Context Anchor field '${field}' found only once" "Expected ≥2 (Phase 3 + Plan Template)"
    else
        fail "Context Anchor field '${field}' MISSING" "Expected in both Phase 3 §3a and Plan Template"
    fi
done


# -------- 6. CONTEXT ANCHOR ORDERING (WHY first, SCOPE last) --------
heading "6. Context Anchor — Field Order & Completeness"

# Check the Phase 3 context anchor table ordering
TOTAL_TESTS=$((TOTAL_TESTS + 1))
anchor_start=$(grep -n "^### 3a. Context Anchor" "$SKILL_FILE" | head -1 | cut -d: -f1)
if [ -n "$anchor_start" ]; then
    # Extract lines from anchor start until next ### or ---
    anchor_block=$(sed -n "${anchor_start},\$p" "$SKILL_FILE" \
        | awk 'BEGIN{count=0} /^\|\*\*WHY\*\*\|/{count++} /^\|\*\*SCOPE\*\*\|/{count++} count==2{print;exit} /^### /{if(count>0)exit} count>0{print}')
    anchor_start_and_block=$(sed -n "${anchor_start},\$p" "$SKILL_FILE" \
        | awk 'BEGIN{count=0} /^### /{if(count>0)exit} {print} /^\|---\|/{count=1}')
    
    # Check WHY appears before SCOPE
    why_line=$(echo "$anchor_start_and_block" | grep -n 'WHY' | head -1 | cut -d: -f1)
    scope_line=$(echo "$anchor_start_and_block" | grep -n 'SCOPE' | head -1 | cut -d: -f1)
    
    if [ -n "$why_line" ] && [ -n "$scope_line" ] && [ "$why_line" -lt "$scope_line" ]; then
        pass "Context Anchor field ordering: WHY before SCOPE (correct)"
    else
        fail "Context Anchor field ordering" "Expected WHY before SCOPE"
    fi
else
    fail "Context Anchor section anchor (### 3a.)" "Could not locate §3a"
fi


# -------- SUMMARY --------
heading "TEST SUMMARY"

echo "  File under test: $SKILL_FILE"
echo "  Total tests:     $TOTAL_TESTS"
echo "  Passed:         $PASSED_TESTS"
echo "  Failed:         $FAILED_TESTS"

if [ "$FAILED_TESTS" -eq 0 ]; then
    echo ""
    echo "  ✅ ALL CONTRACTS VALIDATED — skill is ready for use via run_skill(name=\"blackcow-plan\")"
    exit 0
else
    echo ""
    echo "  ❌ $FAILED_TESTS CONTRACT(S) BROKEN — review output above before using this skill"
    exit 1
fi
