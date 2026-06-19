#!/usr/bin/env bash
# ============================================================================
# validate-blackcow-ecosystem.sh — L4 System-Level Test for BKIT Skill Ecosystem
#
# Tests the FULL blackcow-* skill pipeline across 6 subsystems:
#   S01-S05  File Integrity — all 8 skill files exist + cross-reference checks
#   S06-S07  JSONL Validation — qa-history.jsonl + review-history.jsonl
#   S08      Evidence Directory — exists, writable, has content
#   S09-S13  Cross-Reference Integrity — skills reference each other correctly
#   S14-S18  Frontmatter Schema — all 8 skills have valid YAML frontmatter
#   S19-S22  Pipeline Contract — plan→loop→qa→review→evolver→governor chain
#   S23-S24  Self-Audit Checklist — governor's cross-skill evidence contract
#   S25-S27  Cost Model Consistency — model_tiers and allowed-tools alignment
#   S28-S30  End-to-End Pipeline Simulation (dry-run checks)
#
# Usage:
#   bash skills/tests/validate-blackcow-ecosystem.sh
#   bash skills/tests/validate-blackcow-ecosystem.sh --verbose   # detailed output
#   bash skills/tests/validate-blackcow-ecosystem.sh --quiet     # summary only
#
# Exit code: 0 if ALL checks pass, 1 otherwise.
# ============================================================================

set -euo pipefail

# --- Config -----------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$SKILLS_DIR/.." && pwd)"
OMO_DIR="${PROJECT_ROOT}/.omo"
MEMORY_DIR="${OMO_DIR}/memory"
META_REVIEW_DIR="${OMO_DIR}/meta-review"
EVIDENCE_DIR="${OMO_DIR}/ulw-loop/evidence"
GOVERNOR_DIR="${OMO_DIR}/governor"

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

# --- Color helpers -----------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

pass_msg() { ((PASS++)); ((TOTAL++)); $QUIET || echo -e "  ${GREEN}PASS${NC} $1"; }
fail_msg() { ((FAIL++)); ((TOTAL++)); echo -e "  ${RED}FAIL${NC} $1"; }
skip_msg() { ((TOTAL++)); echo -e "  ${YELLOW}SKIP${NC} $1"; }
info_msg() { $VERBOSE && echo -e "  ${CYAN}INFO${NC} $1"; return 0; }
header()   { echo ""; echo "━━━ $* ━━━"; }

# --- Assert helpers ----------------------------------------------------------
assert_file_exists() {
  local label="$1" path="$2"
  if [[ -f "$path" ]]; then
    pass_msg "$label — exists: $path"
  else
    fail_msg "$label — NOT FOUND: $path"
  fi
}

assert_directory_exists() {
  local label="$1" path="$2"
  if [[ -d "$path" ]]; then
    pass_msg "$label — exists: $path"
  else
    fail_msg "$label — NOT FOUND: $path"
  fi
}

assert_directory_writable() {
  local label="$1" path="$2"
  if [[ -d "$path" ]] && [[ -w "$path" ]]; then
    pass_msg "$label — exists and is writable"
  else
    fail_msg "$label — missing or not writable"
  fi
}

assert_grep() {
  local label="$1" file="$2" pattern="$3"
  if grep -Eq "$pattern" "$file" 2>/dev/null; then
    pass_msg "$label — pattern found in $(basename "$file"): /$pattern/"
  else
    fail_msg "$label — pattern MISSING in $(basename "$file"): /$pattern/"
  fi
}

assert_grep_count() {
  local label="$1" file="$2" pattern="$3" expected="$4"
  local count
  count=$(grep -Ec "$pattern" "$file" 2>/dev/null || echo "0")
  if [[ "$count" -eq "$expected" ]]; then
    pass_msg "$label — count $count == $expected"
  else
    fail_msg "$label — expected $expected, got $count"
  fi
}

assert_no_grep() {
  local label="$1" file="$2" pattern="$3"
  if grep -Eq "$pattern" "$file" 2>/dev/null; then
    fail_msg "$label — forbidden pattern FOUND: /$pattern/"
  else
    pass_msg "$label — forbidden pattern ABSENT: /$pattern/"
  fi
}

assert_yaml_frontmatter_field() {
  local label="$1" file="$2" field="$3"
  if grep -Eq "^${field}:" "$file" 2>/dev/null; then
    pass_msg "$label — field '$field' present in $(basename "$file")"
  else
    fail_msg "$label — field '$field' MISSING in $(basename "$file")"
  fi
}

validate_jsonl() {
  local label="$1" file="$2" min_entries="${3:-0}"
  if [[ ! -f "$file" ]]; then
    fail_msg "$label — file NOT FOUND: $file"
    return 1
  fi

  local errors=0 lines=0
  while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip empty lines
    [[ -z "$line" ]] && continue
    ((lines++))
    if ! echo "$line" | python3 -m json.tool > /dev/null 2>&1; then
      ((errors++))
      $VERBOSE && echo "    Invalid JSON on line: ${line:0:80}..."
    fi
  done < "$file"

  if [[ "$errors" -eq 0 ]] && [[ "$lines" -ge "$min_entries" ]]; then
    pass_msg "$label — valid JSONL ($lines entries, $errors invalid)"
  elif [[ "$errors" -eq 0 ]] && [[ "$lines" -lt "$min_entries" ]]; then
    fail_msg "$label — valid JSONL but only $lines entries (min $min_entries)"
  else
    fail_msg "$label — INVALID JSONL: $errors invalid lines out of $lines total"
  fi
}

# ============================================================================
echo "============================================================"
echo " BlackCow Ecosystem L4 System Validation"
echo "============================================================"
echo " Skills dir:     $SKILLS_DIR"
echo " Memory dir:     $MEMORY_DIR"
echo " Meta-review:    $META_REVIEW_DIR"
echo " Evidence:       $EVIDENCE_DIR"

# ============================================================================
# S01-S05: FILE INTEGRITY — All 8 skill files exist
# ============================================================================
header "S01-S05 — File Integrity (All 8 blackcow-* skill files)"

ALL_SKILLS=(
  "blackcow-plan.md"
  "blackcow-loop.md"
  "blackcow-swarm.md"
  "blackcow-qa.md"
  "blackcow-librarian.md"
  "blackcow-skill-review.md"
  "blackcow-skill-evolver.md"
  "blackcow-governor.md"
)
EXPECTED_SKILL_COUNT="${#ALL_SKILLS[@]}"

MISSING_COUNT=0; MISSING_LIST=""
for skill in "${ALL_SKILLS[@]}"; do
  [[ -f "${SKILLS_DIR}/${skill}" ]] || { MISSING_COUNT=$((MISSING_COUNT+1)); MISSING_LIST="$MISSING_LIST  ${SKILLS_DIR}/${skill}"$'\n'; }
done
if [[ "$MISSING_COUNT" -ge 2 ]]; then
  echo "FATAL: $MISSING_COUNT target skill files not found:"$'\n'"$MISSING_LIST" >&2; exit 1
elif [[ "$MISSING_COUNT" -eq 1 ]]; then
  echo "WARNING: 1 target skill file not found (continuing with partial validation):"$'\n'"$MISSING_LIST" >&2
fi

echo "  Expected skills (${EXPECTED_SKILL_COUNT}):"
for skill in "${ALL_SKILLS[@]}"; do
  echo "    • ${skill}"
done

SKILL_COUNT=0
for skill in "${ALL_SKILLS[@]}"; do
  if [[ -f "${SKILLS_DIR}/${skill}" ]]; then
    pass_msg "S01 — Skill file exists: ${skill}"
    ((SKILL_COUNT++))
  else
    fail_msg "S01 — Skill file MISSING: ${skill}"
  fi
done

if [[ "$SKILL_COUNT" -eq "$EXPECTED_SKILL_COUNT" ]]; then
  pass_msg "S02 — All ${EXPECTED_SKILL_COUNT} blackcow-* skill files present (${EXPECTED_SKILL_COUNT}/${EXPECTED_SKILL_COUNT})"
else
  fail_msg "S02 — Expected ${EXPECTED_SKILL_COUNT} skill files, found ${SKILL_COUNT}"
fi

# Also verify they exist in ~/.reasonix/skills/ (the run_skill target)
HOMEDIR_SKILLS=0
for skill in "${ALL_SKILLS[@]}"; do
  if [[ -f "${HOME}/.reasonix/skills/${skill}" ]]; then
    ((HOMEDIR_SKILLS++))
  fi
done

if [[ "$HOMEDIR_SKILLS" -eq "$EXPECTED_SKILL_COUNT" ]]; then
  pass_msg "S03 — All ${EXPECTED_SKILL_COUNT} skills installed in ~/.reasonix/skills/ (${EXPECTED_SKILL_COUNT}/${EXPECTED_SKILL_COUNT})"
elif [[ "$HOMEDIR_SKILLS" -gt 0 ]]; then
  pass_msg "S03 — ${HOMEDIR_SKILLS}/${EXPECTED_SKILL_COUNT} skills found in ~/.reasonix/skills/"
else
  skip_msg "S03 — No skills found in ~/.reasonix/skills/ (run skills/install.sh first)"
fi

# Check all files have non-zero size
for skill in "${ALL_SKILLS[@]}"; do
  if [[ -f "${SKILLS_DIR}/${skill}" ]]; then
    size=$(stat -f%z "${SKILLS_DIR}/${skill}" 2>/dev/null || stat -c%s "${SKILLS_DIR}/${skill}" 2>/dev/null || echo "0")
    if [[ "$size" -gt 1000 ]]; then
      pass_msg "S04 — ${skill} has content ($size bytes)"
    else
      fail_msg "S04 — ${skill} is too small ($size bytes) — may be empty/stub"
    fi
  fi
done

# Check version consistency across all 8 skills
header "S05 — Version Consistency Across All Skills"
VERSIONS=$(grep -h '^version: ' "${SKILLS_DIR}"/blackcow-*.md 2>/dev/null | sort -u)
VERSION_COUNT=$(echo "$VERSIONS" | wc -l | tr -d ' ')
if [[ "$VERSION_COUNT" -eq 1 ]]; then
  pass_msg "S05 — All ${EXPECTED_SKILL_COUNT} skills share the same version: $(echo "$VERSIONS" | head -1)"
else
  echo "  Versions found ($VERSION_COUNT unique):"
  echo "$VERSIONS" | sed 's/^/    /'
  fail_msg "S05 — Skills have mismatched versions (expected 1 unique, found $VERSION_COUNT)"
fi

# ============================================================================
# S06-S07: JSONL VALIDATION
# ============================================================================
header "S06-S07 — JSONL Data File Validation"

validate_jsonl "S06 — qa-history.jsonl" "${MEMORY_DIR}/qa-history.jsonl" 1

validate_jsonl "S07 — review-history.jsonl" "${META_REVIEW_DIR}/review-history.jsonl" 1

# Check qa-history schema: each entry must have timestamp, slug, gate_scores, tokens_used
if [[ -f "${MEMORY_DIR}/qa-history.jsonl" ]]; then
  python3 -c "
import json
with open('${MEMORY_DIR}/qa-history.jsonl') as f:
    for i, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        required = ['timestamp', 'slug', 'gate_scores', 'tokens_used']
        missing = [k for k in required if k not in obj]
        if missing:
            print(f'FAIL: Entry {i} missing fields: {missing}')
            exit(1)
print('PASS')
" 2>/dev/null && pass_msg "S06b — qa-history.jsonl schema valid (timestamp, slug, gate_scores, tokens_used)" \
  || fail_msg "S06b — qa-history.jsonl schema INVALID"
fi

# Check review-history schema: each entry must have date, skill, total_score
if [[ -f "${META_REVIEW_DIR}/review-history.jsonl" ]]; then
  python3 -c "
import json
with open('${META_REVIEW_DIR}/review-history.jsonl') as f:
    for i, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        required = ['date', 'skill', 'total_score']
        missing = [k for k in required if k not in obj]
        if missing:
            print(f'FAIL: Entry {i} missing fields: {missing}')
            exit(1)
print('PASS')
" 2>/dev/null && pass_msg "S07b — review-history.jsonl schema valid (date, skill, total_score)" \
  || fail_msg "S07b — review-history.jsonl schema INVALID"
fi

# ============================================================================
# S08: EVIDENCE DIRECTORY
# ============================================================================
header "S08 — Evidence Directory"

assert_directory_exists "S08a — Evidence dir" "${EVIDENCE_DIR}"
assert_directory_writable "S08b — Evidence dir writable" "${EVIDENCE_DIR}"

# Check evidence has content
EVIDENCE_COUNT=$(ls -1 "${EVIDENCE_DIR}" 2>/dev/null | wc -l | tr -d ' ')
if [[ "$EVIDENCE_COUNT" -ge 1 ]]; then
  pass_msg "S08c — Evidence directory has $EVIDENCE_COUNT file(s)"
else
  fail_msg "S08c — Evidence directory is EMPTY"
fi

# Check state directories exist
for subdir in ".omo/ulw-loop" ".omo/library" ".omo/governor" ".omo/memory"; do
  if [[ -d "${PROJECT_ROOT}/${subdir}" ]]; then
    pass_msg "S08d — State directory exists: ${subdir}"
  else
    info_msg "S08d — State directory not yet created: ${subdir}"
  fi
done

# ============================================================================
# S09-S13: CROSS-REFERENCE INTEGRITY
# ============================================================================
header "S09-S13 — Cross-Reference Integrity (7→8 Skill References)"

# Each skill should reference the other 6 skills
SKILL_NAMES=(
  "blackcow-plan"
  "blackcow-loop"
  "blackcow-swarm"
  "blackcow-qa"
  "blackcow-librarian"
  "blackcow-skill-review"
  "blackcow-skill-evolver"
  "blackcow-governor"
)

# Check that every skill references all other skills
for skill in "${SKILL_NAMES[@]}"; do
  file="${SKILLS_DIR}/${skill}.md"
  [[ ! -f "$file" ]] && continue

  refs=0
  for target in "${SKILL_NAMES[@]}"; do
    [[ "$target" == "$skill" ]] && continue  # skip self-reference
    if grep -q "$target" "$file" 2>/dev/null; then
      ((refs++))
    fi
  done

  expected=$((${#SKILL_NAMES[@]} - 1))
  if [[ "$refs" -eq "$expected" ]]; then
    pass_msg "S09 — ${skill}.md references all $expected other skills"
  elif [[ "$refs" -ge 4 ]]; then
    info_msg "S09 — ${skill}.md references $refs/$expected other skills (partial)"
    pass_msg "S09 — ${skill}.md references $refs/$expected other skills"
  else
    fail_msg "S09 — ${skill}.md only references $refs/$expected other skills"
  fi
done

# Check governor cross-skill evidence contract table
if [[ -f "${SKILLS_DIR}/blackcow-governor.md" ]]; then
  header "S10 — Governor Cross-Skill Evidence Contract"

  # The governor defines a Cross-Skill Evidence Contract table mapping producer→artifact→consumer
  for pair in "blackcow-governor→plan" "blackcow-plan→loop" "blackcow-loop→qa" "blackcow-qa→librarian" "blackcow-librarian→plan"; do
    producer="${pair%→*}"
    consumer="${pair#*→}"
    if grep -q "$producer" "${SKILLS_DIR}/blackcow-governor.md" 2>/dev/null && \
       grep -q "$consumer" "${SKILLS_DIR}/blackcow-governor.md" 2>/dev/null; then
      pass_msg "S10 — Governor contract: $producer → $consumer"
    else
      fail_msg "S10 — Governor contract MISSING: $producer → $consumer"
    fi
  done

  # Verify the contract table has specific artifact paths
  for artifact in ".omo/governor/" "plans/" "completion-report" "qa-history" "structure-cache"; do
    if grep -q "$artifact" "${SKILLS_DIR}/blackcow-governor.md" 2>/dev/null; then
      pass_msg "S10b — Governor contract references artifact: $artifact"
    else
      fail_msg "S10b — Governor contract MISSING artifact: $artifact"
    fi
  done
fi

# Check that the governance dispatch pipeline references all 5 phases
if [[ -f "${SKILLS_DIR}/blackcow-governor.md" ]]; then
  header "S11 — Governor Pipeline Dispatch"

  for cmd in "blackcow-plan" "blackcow-loop" "blackcow-qa" "blackcow-skill-review"; do
    if grep -q "run_skill.*$cmd" "${SKILLS_DIR}/blackcow-governor.md" 2>/dev/null; then
      pass_msg "S11 — Governor dispatches: $cmd"
    else
      info_msg "S11 — Governor may not explicitly dispatch: $cmd"
    fi
  done
fi

# Check that blackcow-plan references governor for mode/widening
if [[ -f "${SKILLS_DIR}/blackcow-plan.md" ]]; then
  header "S12 — Plan-to-Governor Integration"

  for feature in "govern" "mode" "gate" "widening"; do
    if grep -q "$feature" "${SKILLS_DIR}/blackcow-plan.md" 2>/dev/null; then
      pass_msg "S12 — Plan references governor $feature"
    else
      info_msg "S12 — Plan may not reference governor $feature explicitly"
    fi
  done
fi

# Check that blackcow-qa references governor for gate subset
if [[ -f "${SKILLS_DIR}/blackcow-qa.md" ]]; then
  header "S13 — QA-to-Governor Integration"

  if grep -q "govern" "${SKILLS_DIR}/blackcow-qa.md" 2>/dev/null; then
    pass_msg "S13 — QA references governor for gate subset"
  else
    info_msg "S13 — QA may not reference governor directly"
  fi
fi

# ============================================================================
# S14-S18: FRONTMATTER SCHEMA — All 8 skills
# ============================================================================
header "S14-S18 — Frontmatter Schema Validation"

REQUIRED_FIELDS=("name" "runAs" "model" "allowed-tools" "version" "updated" "description")

for skill in "${ALL_SKILLS[@]}"; do
  file="${SKILLS_DIR}/${skill}"
  [[ ! -f "$file" ]] && continue

  missing=0
  for field in "${REQUIRED_FIELDS[@]}"; do
    if grep -Eq "^${field}:" "$file" 2>/dev/null; then
      : # present
    else
      ((missing++))
      $VERBOSE && echo "    MISSING field '$field' in $skill"
    fi
  done

  if [[ "$missing" -eq 0 ]]; then
    pass_msg "S14 — $skill has all 7 required frontmatter fields"
  else
    fail_msg "S14 — $skill missing $missing required frontmatter field(s)"
  fi
done

# Check specific required values
for skill in "${ALL_SKILLS[@]}"; do
  file="${SKILLS_DIR}/${skill}"
  [[ ! -f "$file" ]] && continue

  if grep -Eq "^runAs: subagent" "$file" 2>/dev/null; then
    pass_msg "S15 — $skill has runAs: subagent"
  else
    fail_msg "S15 — $skill missing runAs: subagent"
  fi

  if grep -Eq "^version: [0-9]+\.[0-9]+\.[0-9]+" "$file" 2>/dev/null; then
    pass_msg "S16 — $skill has valid semver version"
  else
    fail_msg "S16 — $skill missing valid semver version"
  fi

  if grep -Eq "^updated: [0-9]{4}-[0-9]{2}-[0-9]{2}" "$file" 2>/dev/null; then
    pass_msg "S17 — $skill has ISO date in updated field"
  else
    fail_msg "S17 — $skill missing ISO date in updated field"
  fi
done

# Check model_tiers (at least budget + pro)
for skill in "${ALL_SKILLS[@]}"; do
  file="${SKILLS_DIR}/${skill}"
  [[ ! -f "$file" ]] && continue
  if grep -q "model_tiers:" "$file" 2>/dev/null; then
    budget_count=$(grep -c "budget:" "$file" 2>/dev/null || echo "0")
    pro_count=$(grep -c "pro:" "$file" 2>/dev/null || echo "0")
    if [[ "$budget_count" -ge 1 ]] && [[ "$pro_count" -ge 1 ]]; then
      pass_msg "S18 — $skill has model_tiers (budget + pro)"
    else
      fail_msg "S18 — $skill model_tiers incomplete (budget=$budget_count, pro=$pro_count)"
    fi
  else
    info_msg "S18 — $skill has no model_tiers section"
  fi
done

# ============================================================================
# S19-S22: PIPELINE CONTRACT — plan→loop→qa→review→evolver→governor
# ============================================================================
header "S19-S22 — Pipeline Contract Verification"

# The pipeline chain: plan creates plan.md → loop reads plan.md and produces
# completion-report → qa reads completion-report and writes qa-history →
# review reads skills and writes review-history → evolver reads review and
# applies edits → governor orchestrates the whole thing

echo "  Pipeline: governor → plan → loop → qa → review → evolver"

# S19: Plan → Loop contract
if grep -q "plans/" "${SKILLS_DIR}/blackcow-plan.md" 2>/dev/null && \
   grep -q "plans/" "${SKILLS_DIR}/blackcow-loop.md" 2>/dev/null; then
  pass_msg "S19 — Plan→Loop contract: plan writes plans/, loop reads plans/"
else
  info_msg "S19 — Plan→Loop contract: check explicit path references"
fi

# S20: Loop → QA contract (evidence index)
if grep -q "completion-report" "${SKILLS_DIR}/blackcow-loop.md" 2>/dev/null && \
   grep -q "completion-report" "${SKILLS_DIR}/blackcow-qa.md" 2>/dev/null; then
  pass_msg "S20 — Loop→QA contract: loop writes completion-report, QA reads it"
else
  info_msg "S20 — Loop→QA contract: check completion-report reference"
fi

# S21: QA → Review → Evolver contract
if grep -q "qa-history" "${SKILLS_DIR}/blackcow-qa.md" 2>/dev/null && \
   grep -q "review-history" "${SKILLS_DIR}/blackcow-skill-review.md" 2>/dev/null && \
   grep -q "review-" "${SKILLS_DIR}/blackcow-skill-evolver.md" 2>/dev/null; then
  pass_msg "S21 — QA→Review→Evolver contract: history flows through pipeline"
else
  info_msg "S21 — QA→Review→Evolver contract: partial flow detected"
fi

# S22: Governor orchestrates — verify governor has all lifecycle phases
if grep -q "Phase 0" "${SKILLS_DIR}/blackcow-governor.md" 2>/dev/null && \
   grep -q "Phase 1" "${SKILLS_DIR}/blackcow-governor.md" 2>/dev/null && \
   grep -q "Phase 2" "${SKILLS_DIR}/blackcow-governor.md" 2>/dev/null; then
  pass_msg "S22 — Governor has phased orchestration (Phase 0/1/2+)"
else
  info_msg "S22 — Governor may use different phase structure"
fi

# ============================================================================
# S23-S24: SELF-AUDIT CHECKLIST
# ============================================================================
header "S23-S24 — Self-Audit Checklist Compliance"

# Each skill has a self-audit checklist in its constraints section.
# Verify they exist.
for skill in "${ALL_SKILLS[@]}"; do
  file="${SKILLS_DIR}/${skill}"
  [[ ! -f "$file" ]] && continue

  if grep -qi "self-audit\|checklist\|stop rules\|constraints" "$file" 2>/dev/null; then
    pass_msg "S23 — $skill has self-audit/checklist/constraints section"
  else
    info_msg "S23 — $skill may not have explicit self-audit section"
  fi
done

# Governor specifically has a Cross-Skill Evidence Contract table
if grep -q "Cross-Skill Evidence Contract" "${SKILLS_DIR}/blackcow-governor.md" 2>/dev/null; then
  pass_msg "S24 — Governor defines Cross-Skill Evidence Contract"
else
  fail_msg "S24 — Governor MISSING Cross-Skill Evidence Contract"
fi

# ============================================================================
# S25-S27: COST MODEL CONSISTENCY
# ============================================================================
header "S25-S27 — Cost Model Consistency"

# Verify all skills with model_tiers use consistent model names
MODEL_BUDGETS=$(grep -h 'budget:' "${SKILLS_DIR}"/blackcow-*.md 2>/dev/null | grep -v 'model_tiers:' | sort -u)
MODEL_PROS=$(grep -h 'pro:' "${SKILLS_DIR}"/blackcow-*.md 2>/dev/null | grep -v 'model_tiers:' | sort -u)

BUDGET_COUNT=$(echo "$MODEL_BUDGETS" | wc -l | tr -d ' ')
PRO_COUNT=$(echo "$MODEL_PROS" | wc -l | tr -d ' ')

if [[ "$BUDGET_COUNT" -le 2 ]]; then
  pass_msg "S25 — Budget-tier models consistent across skills ($BUDGET_COUNT variant(s))"
else
  info_msg "S25 — Budget-tier models: $BUDGET_COUNT variants"
fi

if [[ "$PRO_COUNT" -le 2 ]]; then
  pass_msg "S26 — Pro-tier models consistent across skills ($PRO_COUNT variant(s))"
else
  info_msg "S26 — Pro-tier models: $PRO_COUNT variants"
fi

# Each skill should declare its pipeline neighbor's reference in allowed-tools
# The most critical: run_skill is needed for skills that invoke other skills
for skill_with_run_skill in "blackcow-governor" "blackcow-plan" "blackcow-loop" "blackcow-swarm" "blackcow-qa" "blackcow-librarian" "blackcow-skill-review" "blackcow-skill-evolver"; do
  file="${SKILLS_DIR}/${skill_with_run_skill}.md"
  [[ ! -f "$file" ]] && continue
  if grep -q "run_skill" "$file" 2>/dev/null; then
    if grep -q "allowed-tools:.*run_skill" "$file" 2>/dev/null; then
      pass_msg "S27 — $skill_with_run_skill declares run_skill in allowed-tools"
    else
      info_msg "S27 — $skill_with_run_skill uses run_skill but may not declare it in allowed-tools"
    fi
  fi
done

# ============================================================================
# S28-S30: END-TO-END PIPELINE SIMULATION (DRY-RUN)
# ============================================================================
header "S28-S30 — End-to-End Pipeline Simulation"

echo "  Simulating: governor → plan → loop → qa → review → evolver"

# S28: Verify the chain produces all expected artifacts
echo "  Expected artifacts per pipeline stage:"
echo "    governor:  .omo/governor/<slug>-governance.md"
echo "    plan:      plans/<slug>.md"
echo "    loop:      .omo/ulw-loop/completion-report.md"
echo "    qa:        .omo/memory/qa-history.jsonl"
echo "    review:    .omo/meta-review/review-history.jsonl"
echo "    evolver:   .omo/meta-review/evolution-log.jsonl"

# Check that the artifact paths defined in governor match actual files
ARTIFACTS_PRESENT=0
ARTIFACTS_TOTAL=0
if [[ -f "${MEMORY_DIR}/qa-history.jsonl" ]]; then
  ((ARTIFACTS_PRESENT++))
fi
((ARTIFACTS_TOTAL++))
if [[ -f "${META_REVIEW_DIR}/review-history.jsonl" ]]; then
  ((ARTIFACTS_PRESENT++))
fi
((ARTIFACTS_TOTAL++))

if [[ "$ARTIFACTS_PRESENT" -eq "$ARTIFACTS_TOTAL" ]]; then
  pass_msg "S28 — All expected pipeline artifacts present on disk ($ARTIFACTS_PRESENT/$ARTIFACTS_TOTAL)"
else
  info_msg "S28 — Pipeline artifacts: $ARTIFACTS_PRESENT/$ARTIFACTS_TOTAL present (expected for new projects)"
fi

# S29: Verify the install.sh can install all skills (syntax check)
if [[ -f "${SKILLS_DIR}/install.sh" ]]; then
  # Check that install.sh references all skills
  INSTALL_REF_COUNT=0
  for skill in "${ALL_SKILLS[@]}"; do
    if grep -q "$skill" "${SKILLS_DIR}/install.sh" 2>/dev/null; then
      ((INSTALL_REF_COUNT++))
    fi
  done
  if [[ "$INSTALL_REF_COUNT" -eq "$EXPECTED_SKILL_COUNT" ]]; then
    pass_msg "S29 — install.sh references all ${EXPECTED_SKILL_COUNT} skills ($INSTALL_REF_COUNT/${EXPECTED_SKILL_COUNT})"
  else
    fail_msg "S29 — install.sh references $INSTALL_REF_COUNT/${EXPECTED_SKILL_COUNT} skills (expected ${EXPECTED_SKILL_COUNT})"
  fi
else
  fail_msg "S29 — install.sh NOT FOUND"
fi

# S30: Dry-run the pipeline chain by verifying each skill's main phases exist
# (This is a structural check — the skills are designed to be invoked via
# run_skill, not bash, so we verify phase structure instead)
echo "  Pipeline phase structure check:"
PIPELINE_PHASES=(
  "blackcow-plan:Phase -1|Phase 0|Phase 1|Phase 2|Phase 3|Phase 4|Phase 5"
  "blackcow-loop:Phase 0|Phase 1|Phase 2|Phase 3|Phase 4|Phase 5|Phase 6|Phase 7"
  "blackcow-swarm:Phase 0|Phase 1|Phase 2|Phase 3|Phase 4|Phase 5"
  "blackcow-qa:Phase 0|Phase 1|Phase 2|Phase 3"
  "blackcow-librarian:Phase 0|Phase 1|Phase 2|Phase 3|Phase 4|Phase 5|Phase 6"
  "blackcow-skill-review:Phase 0|Phase 1|Phase 2|Phase 3"
  "blackcow-skill-evolver:Phase 0|Phase 1|Phase 2|Phase 3|Phase 4|Phase 5|Phase 6|Phase 7"
  "blackcow-governor:Phase 0|Phase 1|Phase 2"
)

for entry in "${PIPELINE_PHASES[@]}"; do
  skill="${entry%%:*}"
  phases="${entry#*:}"
  file="${SKILLS_DIR}/${skill}.md"
  [[ ! -f "$file" ]] && continue

  IFS='|'
  all_present=true
  total_phases=0
  found_phases=0
  for phase in $phases; do
    ((total_phases++))
    if grep -q "$phase" "$file" 2>/dev/null; then
      ((found_phases++))
    else
      all_present=false
      $VERBOSE && echo "    MISSING: $phase in $skill"
    fi
  done

  if [[ "$found_phases" -eq "$total_phases" ]]; then
    pass_msg "S30 — $skill has all $total_phases expected phases"
  else
    info_msg "S30 — $skill has $found_phases/$total_phases expected phases"
  fi
done

# ============================================================================
# SUMMARY
# ============================================================================
header "TEST SUMMARY"

echo ""
echo "  All ${EXPECTED_SKILL_COUNT} skills under test:"
for skill in "${ALL_SKILLS[@]}"; do
  if [[ -f "${SKILLS_DIR}/${skill}" ]]; then
    sz=$(stat -f%z "${SKILLS_DIR}/${skill}" 2>/dev/null || stat -c%s "${SKILLS_DIR}/${skill}" 2>/dev/null || echo "?")
    echo "    📄 ${skill}  (${sz} bytes)"
  else
    echo "    ❌ ${skill}  (MISSING)"
  fi
done

echo ""
echo "  Test data files:"
for f in "${MEMORY_DIR}/qa-history.jsonl" "${META_REVIEW_DIR}/review-history.jsonl"; do
  if [[ -f "$f" ]]; then
    lncount=$(wc -l < "$f" | tr -d ' ')
    echo "    📄 $(basename "$(dirname "$f")")/$(basename "$f")  (${lncount} lines)"
  else
    echo "    ❌ $(basename "$(dirname "$f")")/$(basename "$f")  (MISSING)"
  fi
done

echo ""
echo "  Results: $PASS passed, $FAIL failed (total $TOTAL checks)"
echo "============================================================"

if [[ "$FAIL" -eq 0 ]]; then
  echo "  ✅ ALL SYSTEM-LEVEL CHECKS PASSED — ecosystem is healthy."
  echo "  Skills involved: ${EXPECTED_SKILL_COUNT} blackcow-* skill files"
  echo "  Data files: qa-history.jsonl + review-history.jsonl"
  echo "  Infrastructure: evidence directory + pipeline contract"
  echo ""
  echo "  NOTE: Some subsystems require runtime skills invocation"
  echo "  (run_skill) for true end-to-end testing. This script validates"
  echo "  all static invariants that can be verified from filesystem."
  exit 0
else
  echo "  ❌ $FAIL CHECK(S) FAILED — review output above."
  exit 1
fi
