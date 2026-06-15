#!/usr/bin/env bash
# ============================================================================
# L4 System Tests — install.sh full end-to-end flow
#
# Tests the complete install pipeline in a temp environment:
#   1. Complete install flow to a temp target dir
#   2. All blackcow-*.md files are installed
#   3. allowed-tools lines differ between macOS and Windows
#   4. Non-blackcow .md files are skipped
#   5. Test suite validate-*.sh scripts are made executable
#   6. REASONIX_PLATFORM=windows env var override
#   7. --dry-run flag writes nothing
#   8. --target and --install-path are aliases
#   9. Path outside ~/.reasonix is rejected
#
# Usage:
#   bash skills/tests/test-l4-system-install-security.sh
#   REASONIX_PLATFORM=windows bash skills/tests/test-l4-system-install-security.sh
# ============================================================================
set -euo pipefail

PASS=0; FAIL=0; TOTAL=0
pass() { PASS=$((PASS+1)); TOTAL=$((TOTAL+1)); echo "  ✅ PASS: $1"; }
fail() { FAIL=$((FAIL+1)); TOTAL=$((TOTAL+1)); echo "  ❌ FAIL: $1"; }

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SKILLS_DIR="${PROJECT_ROOT}/skills"
INSTALL_SCRIPT="${SKILLS_DIR}/install.sh"

# Count blackcow-*.md files in the source
BLACKCOW_COUNT=0
for f in "${SKILLS_DIR}"/blackcow-*.md; do
  [[ -f "$f" ]] && BLACKCOW_COUNT=$((BLACKCOW_COUNT + 1))
done

echo "=== L4 System Tests: install.sh (end-to-end) ==="
echo "  Source:         ${SKILLS_DIR}"
echo "  Blackcow files: ${BLACKCOW_COUNT}"
echo ""

# ============================================================================
# Setup: reusable temp workspace
# ============================================================================
setup_workspace() {
  local suffix="$1"
  local ws
  ws=$(mktemp -d "/tmp/l4-install-ws-${suffix}-XXXXXX")
  echo "$ws"
}

cleanup_workspace() {
  local ws="$1"
  rm -rf "$ws" 2>/dev/null || true
}

# Run install.sh from the skills dir with the given args, capturing both
# stdout+stderr and exit code.
run_install() {
  local target_dir="$1"
  shift
  # Run from PROJECT_ROOT so SOURCE_DIR resolves to skills/ via dirname $0
  cd "$PROJECT_ROOT"
  bash "$INSTALL_SCRIPT" --target "$target_dir" "$@" 2>&1 || true
}

# Extract the allowed-tools line from an installed skill file
get_allowed_tools() {
  local skill_file="$1"
  grep "^allowed-tools:" "$skill_file" 2>/dev/null || echo ""
}

# ============================================================================
# Test 1: Complete install flow to a temp target dir
# ============================================================================
echo "--- Test 1: Complete install flow ---"

T1_WS=$(setup_workspace "t1")
T1_TARGET="${HOME}/.reasonix/skills-test-$$-t1"
mkdir -p "$T1_TARGET"
# We need the parent to exist; validation checks under ~/.reasonix

output=$(run_install "$T1_TARGET" 2>&1) || true

if echo "$output" | grep -q "Installation complete"; then
  pass "T1: install.sh completes with success message"
else
  fail "T1: install.sh did not produce 'Installation complete' — output: ${output:0:200}"
fi

if [[ -d "$T1_TARGET" ]]; then
  pass "T1: target directory exists after install"
else
  fail "T1: target directory missing: $T1_TARGET"
fi

if ls "${T1_TARGET}"/blackcow-*.md &>/dev/null 2>&1; then
  pass "T1: at least one blackcow-*.md file installed"
else
  fail "T1: no blackcow-*.md files found in target: $(ls -la "$T1_TARGET" 2>&1)"
fi

# Validate file contents — check for YAML frontmatter integrity
first_file=$(ls "${T1_TARGET}"/blackcow-*.md 2>/dev/null | head -1)
if [[ -n "$first_file" ]] && head -1 "$first_file" | grep -q "^---"; then
  pass "T1: installed file starts with YAML frontmatter"
else
  fail "T1: installed file missing YAML frontmatter delimiter"
fi

cleanup_workspace "$T1_WS"
rm -rf "$T1_TARGET"
echo ""

# ============================================================================
# Test 2: All blackcow-*.md files are installed
# ============================================================================
echo "--- Test 2: All blackcow-*.md files installed ---"

T2_TARGET="${HOME}/.reasonix/skills-test-$$-t2"
mkdir -p "$T2_TARGET"

run_install "$T2_TARGET" >/dev/null 2>&1 || true

installed_count=0
for f in "${SKILLS_DIR}"/blackcow-*.md; do
  bname=$(basename "$f")
  if [[ -f "${T2_TARGET}/${bname}" ]]; then
    installed_count=$((installed_count + 1))
  else
    fail "T2: missing installed file: ${bname}"
  fi
done

if [[ "$installed_count" -eq "$BLACKCOW_COUNT" ]]; then
  pass "T2: all ${BLACKCOW_COUNT} blackcow-*.md files installed (found ${installed_count})"
else
  # If no individual failures above, count mismatch
  : "individual failures reported above"
fi

# Spot-check known skills
for skill in blackcow-plan.md blackcow-loop.md blackcow-qa.md blackcow-governor.md blackcow-librarian.md blackcow-skill-review.md blackcow-skill-evolver.md; do
  if [[ -f "${T2_TARGET}/${skill}" ]]; then
    pass "T2: ${skill} present"
  else
    fail "T2: ${skill} missing"
  fi
done

rm -rf "$T2_TARGET"
echo ""

# ============================================================================
# Test 3: allowed-tools lines differ between macOS and Windows
# ============================================================================
echo "--- Test 3: Platform-specific allowed-tools ---"

T3_MAC_TARGET="${HOME}/.reasonix/skills-test-$$-t3-mac"
T3_WIN_TARGET="${HOME}/.reasonix/skills-test-$$-t3-win"
mkdir -p "$T3_MAC_TARGET" "$T3_WIN_TARGET"

# Install for macOS (default)
REASONIX_PLATFORM="" run_install "$T3_MAC_TARGET" >/dev/null 2>&1 || true

# Install for Windows via env override
REASONIX_PLATFORM=windows run_install "$T3_WIN_TARGET" >/dev/null 2>&1 || true

# Compare allowed-tools lines for each skill
for skill in blackcow-plan.md blackcow-loop.md blackcow-qa.md blackcow-governor.md; do
  mac_tools=$(get_allowed_tools "${T3_MAC_TARGET}/${skill}")
  win_tools=$(get_allowed_tools "${T3_WIN_TARGET}/${skill}")

  if [[ -z "$mac_tools" ]]; then
    fail "T3: macOS ${skill} has no allowed-tools line"
    continue
  fi
  if [[ -z "$win_tools" ]]; then
    fail "T3: Windows ${skill} has no allowed-tools line"
    continue
  fi

  # macOS should have macOS-specific tools
  if echo "$mac_tools" | grep -q "search_content"; then
    pass "T3: macOS ${skill} includes 'search_content'"
  else
    fail "T3: macOS ${skill} missing 'search_content': ${mac_tools:0:120}"
  fi

  # Windows should have Windows-specific tools
  if echo "$win_tools" | grep -q "grep, ls, bash, task"; then
    pass "T3: Windows ${skill} includes Windows tools"
  else
    fail "T3: Windows ${skill} missing 'grep, ls, bash, task': ${win_tools:0:120}"
  fi

  # Common tools should appear on both
  if echo "$mac_tools" | grep -q "read_file" && echo "$win_tools" | grep -q "read_file"; then
    pass "T3: common tool 'read_file' appears on both platforms for ${skill}"
  else
    fail "T3: common tool 'read_file' missing on one platform for ${skill}"
  fi

  # The two lines must differ
  if [[ "$mac_tools" != "$win_tools" ]]; then
    pass "T3: allowed-tools lines differ between platforms for ${skill}"
  else
    fail "T3: allowed-tools lines are IDENTICAL for ${skill} — expected platform divergence"
  fi
done

rm -rf "$T3_MAC_TARGET" "$T3_WIN_TARGET"
echo ""

# ============================================================================
# Test 4: Non-blackcow .md files are skipped
# ============================================================================
echo "--- Test 4: Non-blackcow files skipped ---"

T4_WS=$(setup_workspace "t4")
# Copy install.sh and a subset of blackcow files to the temp workspace
cp "$INSTALL_SCRIPT" "${T4_WS}/"
cp "${SKILLS_DIR}"/blackcow-plan.md "${T4_WS}/"
cp "${SKILLS_DIR}"/blackcow-loop.md "${T4_WS}/"

# Create a rogue non-blackcow .md file
cat > "${T4_WS}/README.md" <<'EOF'
---
name: readme
description: Not a blackcow skill
---
# README — Should NOT be installed
EOF

cat > "${T4_WS}/notes.md" <<'EOF'
---
name: notes
description: Another non-skill file
---
# Notes — Should also NOT be installed
EOF

T4_TARGET="${HOME}/.reasonix/skills-test-$$-t4"
mkdir -p "$T4_TARGET"

# Run install.sh from the temp workspace (so SOURCE_DIR = T4_WS)
cd "$PROJECT_ROOT"
bash "${T4_WS}/install.sh" --target "$T4_TARGET" 2>&1 || true

if [[ -f "${T4_TARGET}/README.md" ]]; then
  fail "T4: non-blackcow README.md was installed (should have been skipped)"
else
  pass "T4: README.md correctly skipped"
fi

if [[ -f "${T4_TARGET}/notes.md" ]]; then
  fail "T4: non-blackcow notes.md was installed (should have been skipped)"
else
  pass "T4: notes.md correctly skipped"
fi

# Verify blackcow files still installed
if [[ -f "${T4_TARGET}/blackcow-plan.md" ]]; then
  pass "T4: blackcow-plan.md installed alongside skipped files"
else
  fail "T4: blackcow-plan.md missing after install with rogue files"
fi

if [[ -f "${T4_TARGET}/blackcow-loop.md" ]]; then
  pass "T4: blackcow-loop.md installed alongside skipped files"
else
  fail "T4: blackcow-loop.md missing after install with rogue files"
fi

cleanup_workspace "$T4_WS"
rm -rf "$T4_TARGET"
echo ""

# ============================================================================
# Test 5: Test suite validate-*.sh scripts are made executable
# ============================================================================
echo "--- Test 5: Test scripts made executable ---"

# The install script does: chmod +x "$TEST_DIR"/validate-*.sh
# where TEST_DIR = SOURCE_DIR/tests

# First, verify tests exist in the source
if ls "${SKILLS_DIR}/tests/validate-"*.sh &>/dev/null 2>&1; then
  pass "T5: validate-*.sh scripts exist in source tests dir"
else
  fail "T5: no validate-*.sh scripts found in ${SKILLS_DIR}/tests/"
fi

# The install script runs from SOURCE_DIR/tests directly — it chmods
# scripts inside the SOURCE, not the target. So we check after a normal
# install that those scripts (which already exist) have their +x bit set.
# But to be safe, let's observe their state before and after.

# Record a known script's permissions before
BEFORE_SCRIPT="${SKILLS_DIR}/tests/validate-blackcow-plan.sh"
if [[ -f "$BEFORE_SCRIPT" ]]; then
  before_perms=$(stat -c "%A" "$BEFORE_SCRIPT" 2>/dev/null || stat -f "%Sp" "$BEFORE_SCRIPT" 2>/dev/null || echo "unknown")
  before_x=false
  if [[ -x "$BEFORE_SCRIPT" ]]; then
    before_x=true
  fi
fi

T5_TARGET="${HOME}/.reasonix/skills-test-$$-t5"
mkdir -p "$T5_TARGET"

run_install "$T5_TARGET" >/dev/null 2>&1 || true

# Check the same script is now executable
if [[ -f "$BEFORE_SCRIPT" ]] && [[ -x "$BEFORE_SCRIPT" ]]; then
  pass "T5: validate-blackcow-plan.sh is executable after install"
else
  fail "T5: validate-blackcow-plan.sh is NOT executable (before: ${before_perms})"
fi

# Ideally check all validate-*.sh scripts
all_executable=true
non_exec=()
for f in "${SKILLS_DIR}"/tests/validate-*.sh; do
  if [[ -f "$f" ]] && [[ ! -x "$f" ]]; then
    all_executable=false
    non_exec+=("$(basename "$f")")
  fi
done

if $all_executable; then
  pass "T5: all validate-*.sh scripts are executable after install"
else
  fail "T5: some scripts not executable: ${non_exec[*]}"
fi

rm -rf "$T5_TARGET"
echo ""

# ============================================================================
# Test 6: REASONIX_PLATFORM=windows env var override
# ============================================================================
echo "--- Test 6: REASONIX_PLATFORM override ---"

T6_TARGET="${HOME}/.reasonix/skills-test-$$-t6"
mkdir -p "$T6_TARGET"

# Install with windows override
cd "$PROJECT_ROOT"
output=$(REASONIX_PLATFORM=windows bash "$INSTALL_SCRIPT" --target "$T6_TARGET" 2>&1) || true

# Check that it detected windows
if echo "$output" | grep -q "Detected platform: windows"; then
  pass "T6: platform detected as 'windows' with REASONIX_PLATFORM=windows"
else
  fail "T6: platform not detected as windows — output: ${output:0:150}"
fi

# Verify installed files have Windows-specific allowed-tools
for skill in blackcow-plan.md blackcow-qa.md; do
  tools=$(get_allowed_tools "${T6_TARGET}/${skill}")
  if echo "$tools" | grep -qE "(grep|ls|bash|task)"; then
    pass "T6: ${skill} has Windows tools after override"
  else
    fail "T6: ${skill} missing Windows tools after override: ${tools:0:120}"
  fi
done

# Verify macOS tools are NOT present in windows install
for skill in blackcow-plan.md blackcow-qa.md; do
  tools=$(get_allowed_tools "${T6_TARGET}/${skill}")
  if echo "$tools" | grep -q "search_content"; then
    fail "T6: ${skill} has macOS tool 'search_content' after Windows override"
  else
    pass "T6: ${skill} correctly omits macOS tools after Windows override"
  fi
done

rm -rf "$T6_TARGET"
echo ""

# ============================================================================
# Test 7: --dry-run flag writes nothing
# ============================================================================
echo "--- Test 7: --dry-run writes nothing ---"

T7_TARGET="${HOME}/.reasonix/skills-test-$$-t7"
mkdir -p "$T7_TARGET"

cd "$PROJECT_ROOT"
output=$(bash "$INSTALL_SCRIPT" --target "$T7_TARGET" --dry-run 2>&1) || true

# Should mention dry-run
if echo "$output" | grep -q "DRY-RUN"; then
  pass "T7: dry-run mode is indicated in output"
else
  fail "T7: dry-run mode not indicated in output: ${output:0:150}"
fi

# Should NOT have installed files
installed=false
for f in "${T7_TARGET}"/blackcow-*.md; do
  if [[ -f "$f" ]]; then
    installed=true
    break
  fi
done

if $installed; then
  fail "T7: files were written despite --dry-run flag"
else
  pass "T7: no files written in dry-run mode"
fi

rm -rf "$T7_TARGET"
echo ""

# ============================================================================
# Test 8: --target and --install-path are aliases
# ============================================================================
echo "--- Test 8: --target and --install-path aliases ---"

T8_TARGET="${HOME}/.reasonix/skills-test-$$-t8"
T8_PATH="${HOME}/.reasonix/skills-test-$$-t8-path"
mkdir -p "$T8_TARGET" "$T8_PATH"

cd "$PROJECT_ROOT"
out_target=$(bash "$INSTALL_SCRIPT" --target "$T8_TARGET" 2>&1) || true
out_path=$(bash "$INSTALL_SCRIPT" --install-path "$T8_PATH" 2>&1) || true

# Both should complete
if echo "$out_target" | grep -q "Installation complete"; then
  pass "T8: --target completes successfully"
else
  fail "T8: --target did not complete: ${out_target:0:150}"
fi

if echo "$out_path" | grep -q "Installation complete"; then
  pass "T8: --install-path completes successfully"
else
  fail "T8: --install-path did not complete: ${out_path:0:150}"
fi

# Both should have installed files
if ls "${T8_TARGET}"/blackcow-*.md &>/dev/null 2>&1; then
  pass "T8: --target installed files to correct dir"
else
  fail "T8: --target dir is empty"
fi

if ls "${T8_PATH}"/blackcow-*.md &>/dev/null 2>&1; then
  pass "T8: --install-path installed files to correct dir"
else
  fail "T8: --install-path dir is empty"
fi

# Mutually exclusive: both flags should fail
cd "$PROJECT_ROOT"
mutex_out=$(bash "$INSTALL_SCRIPT" --target "$T8_TARGET" --install-path "$T8_TARGET" 2>&1) || true
if echo "$mutex_out" | grep -q "mutually exclusive"; then
  pass "T8: --target and --install-path together blocked as mutually exclusive"
else
  fail "T8: mutually exclusive flags not rejected — output: ${mutex_out:0:150}"
fi

rm -rf "$T8_TARGET" "$T8_PATH"
echo ""

# ============================================================================
# Test 9: Path outside ~/.reasonix is rejected
# ============================================================================
echo "--- Test 9: Path validation rejects /tmp ---"

cd "$PROJECT_ROOT"
out=$(bash "$INSTALL_SCRIPT" --target "/tmp/evil-path" 2>&1) || true
if echo "$out" | grep -q "FATAL"; then
  pass "T9: /tmp/evil-path rejected with FATAL"
else
  fail "T9: /tmp/evil-path was NOT rejected — output: ${out:0:200}"
fi

# Test with path under different prefix
out2=$(bash "$INSTALL_SCRIPT" --target "/etc/cron.d" 2>&1) || true
if echo "$out2" | grep -q "FATAL"; then
  pass "T9: /etc/cron.d rejected with FATAL"
else
  fail "T9: /etc/cron.d was NOT rejected — output: ${out2:0:200}"
fi

# Test with dot-dot traversal
out3=$(bash "$INSTALL_SCRIPT" --target "${HOME}/.reasonix/skills/../../etc" 2>&1) || true
if echo "$out3" | grep -q "FATAL"; then
  pass "T9: path with .. traversal rejected"
else
  fail "T9: path with .. was NOT rejected — output: ${out3:0:200}"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================
echo "========================================"
SCORE=$(( TOTAL > 0 ? PASS * 100 / TOTAL : 0 ))
echo "Results: $PASS passed, $FAIL failed, 0 skipped (total $TOTAL checks)"
echo "Score: ${SCORE}%"
echo "========================================"

exit $(( FAIL > 0 ? 1 : 0 ))
