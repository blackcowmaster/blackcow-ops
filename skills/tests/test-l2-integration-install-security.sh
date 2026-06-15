#!/usr/bin/env bash
# ============================================================================
# L2 Integration Tests — install.sh module-to-module interactions
#
# Tests the full install pipeline with mock source directories to verify:
#   1. .md file reading and filtering (blackcow-* only)
#   2. allowed-tools line replacement for macos and windows platforms
#   3. Platform detection output correctness
#   4. --dry-run mode doesn't write any files
#   5. chmod +x applied to validate-*.sh test scripts
#   6. Default target path when no --target flag is given
#
# NOTE: Target directories MUST be under $HOME/.reasonix/ because
#       validate_install_path() enforces that prefix. We use
#       $HOME/.reasonix/.l2-test-<PID>/ as a temporary workspace.
# ============================================================================
set -euo pipefail

PASS=0; FAIL=0; TOTAL=0
pass() { PASS=$((PASS+1)); TOTAL=$((TOTAL+1)); echo "  ✅ PASS: $1"; }
fail() { FAIL=$((FAIL+1)); TOTAL=$((TOTAL+1)); echo "  ❌ FAIL: $1"; }
info() { echo "  ℹ️  $1"; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_SH="$(cd "$SCRIPT_DIR/.." && pwd)/install.sh"

echo "=== L2 Integration Tests: install.sh module interactions ==="
echo ""

# ============================================================================
# Global test workspace (under $HOME/.reasonix/ for path validation)
# ============================================================================
TEST_WORKSPACE="${HOME}/.reasonix/.l2-test-$$"
cleanup() {
  rm -rf "$TEST_WORKSPACE"
}
trap cleanup EXIT
mkdir -p "$TEST_WORKSPACE"

# ============================================================================
# Helper: build a mock source directory tree
# ============================================================================
setup_mock_source() {
  local mock_root="$1"

  mkdir -p "$mock_root/tests"

  # Copy a minimal install.sh into the mock root
  # (SOURCE_DIR = $(dirname "$0"), so it sets input dir from own location)
  cp "$INSTALL_SH" "${mock_root}/install.sh"
  chmod +x "${mock_root}/install.sh"

  # Create mock skill files (matching ^blackcow-.*\.md$)
  cat > "${mock_root}/blackcow-alpha.md" << 'MOCKMD'
---
name: blackcow-alpha
allowed-tools: read_file, search_content, search_files, glob, list_directory, directory_tree, run_command, web_fetch, write_file
---
# blackcow-alpha

Mock skill for integration testing.
MOCKMD

  cat > "${mock_root}/blackcow-beta.md" << 'MOCKMD'
---
name: blackcow-beta
allowed-tools: read_file, search_content, search_files, glob, list_directory, directory_tree, run_command, web_search, write_file
---
# blackcow-beta

Another mock skill for integration testing.
MOCKMD

  # Create a non-skill .md file (must NOT be installed — filtered by ^blackcow-)
  cat > "${mock_root}/README.md" << 'MOCKMD'
# Project README

This is NOT a blackcow skill file.
MOCKMD

  cat > "${mock_root}/notes.md" << 'MOCKMD'
# Scratch notes

Also not a skill.
MOCKMD

  # Create mock test scripts (initially NOT executable)
  echo "#!/usr/bin/env bash" > "${mock_root}/tests/validate-mock.sh"
  echo "#!/usr/bin/env bash" > "${mock_root}/tests/validate-alpha-golden.sh"
  echo "#!/usr/bin/env bash" > "${mock_root}/tests/validate-beta-golden.sh"
  echo "#!/usr/bin/env bash" > "${mock_root}/tests/validate-mock-ecosystem.sh"
  chmod -x "${mock_root}/tests/"*.sh 2>/dev/null || true
}

# ============================================================================
# 1. install.sh correctly reads .md files from SOURCE_DIR and filters
#    Only files matching ^blackcow-.*\.md$ should be installed.
#    Non-matching .md files (README.md, notes.md) must be skipped.
# ============================================================================
echo "--- Test 1: .md file reading and filtering ---"

T1_SOURCE="${TEST_WORKSPACE}/t1-source"
T1_TARGET="${TEST_WORKSPACE}/t1-target"
mkdir -p "$T1_TARGET"
setup_mock_source "$T1_SOURCE"

# Run install.sh from the mock source, installing into the mock target
bash "${T1_SOURCE}/install.sh" --target "$T1_TARGET" > /dev/null 2>&1 || true

# Verify blackcow-alpha.md was installed
if [[ -f "${T1_TARGET}/blackcow-alpha.md" ]]; then
  pass "T1a: blackcow-alpha.md installed to target"
else
  fail "T1a: blackcow-alpha.md NOT found in target"
fi

# Verify blackcow-beta.md was installed
if [[ -f "${T1_TARGET}/blackcow-beta.md" ]]; then
  pass "T1b: blackcow-beta.md installed to target"
else
  fail "T1b: blackcow-beta.md NOT found in target"
fi

# Verify README.md was NOT installed (filtered out — not ^blackcow-)
if [[ ! -f "${T1_TARGET}/README.md" ]]; then
  pass "T1c: README.md correctly excluded (non-blackcow)"
else
  fail "T1c: README.md was incorrectly installed (should be filtered)"
fi

# Verify notes.md was NOT installed (filtered out)
if [[ ! -f "${T1_TARGET}/notes.md" ]]; then
  pass "T1d: notes.md correctly excluded (non-blackcow)"
else
  fail "T1d: notes.md was incorrectly installed (should be filtered)"
fi

# Verify exactly 2 skill files were installed (find avoids set -e failures on empty glob)
INSTALLED_COUNT=$(find "${T1_TARGET}" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l)
if [[ "$INSTALLED_COUNT" -eq 2 ]]; then
  pass "T1e: exactly 2 skill files installed (expected count)"
else
  fail "T1e: expected 2 installed files, found $INSTALLED_COUNT"
fi

# ============================================================================
# 2. allowed-tools lines are correctly replaced on macOS platform (default)
#    The installed file should have the MAC_TOOLS set, not the original.
# ============================================================================
echo ""
echo "--- Test 2: allowed-tools replacement (macOS) ---"

T2_SOURCE="${TEST_WORKSPACE}/t2-source"
T2_TARGET="${TEST_WORKSPACE}/t2-target"
mkdir -p "$T2_TARGET"
setup_mock_source "$T2_SOURCE"

# Clear any REASONIX_PLATFORM override for default (macOS) behavior
unset REASONIX_PLATFORM

bash "${T2_SOURCE}/install.sh" --target "$T2_TARGET" > /dev/null 2>&1 || true

# Read the installed allowed-tools line from blackcow-alpha.md
INSTALLED_ALLOWED=$(grep "^allowed-tools:" "${T2_TARGET}/blackcow-alpha.md" | head -1)

# Verify it contains macOS-specific tools (from MAC_TOOLS in install.sh)
if echo "$INSTALLED_ALLOWED" | grep -q "search_content"; then
  pass "T2a: macOS platform — 'search_content' present in installed allowed-tools"
else
  fail "T2a: macOS platform — 'search_content' MISSING from installed allowed-tools"
fi

if echo "$INSTALLED_ALLOWED" | grep -q "explore"; then
  pass "T2b: macOS platform — 'explore' present in installed allowed-tools"
else
  fail "T2b: macOS platform — 'explore' MISSING from installed allowed-tools"
fi

# Verify the installed line does NOT match the original (proving replacement occurred)
ORIGINAL="allowed-tools: read_file, search_content, search_files, glob, list_directory, directory_tree, run_command, web_fetch, write_file"
if [[ "$INSTALLED_ALLOWED" != "$ORIGINAL" ]]; then
  pass "T2c: macOS platform — allowed-tools line was replaced (no longer matches original)"
else
  fail "T2c: macOS platform — allowed-tools line is UNCHANGED (replacement may have failed)"
fi

# Verify the frontmatter key "allowed-tools:" is preserved
if echo "$INSTALLED_ALLOWED" | grep -q "^allowed-tools:"; then
  pass "T2d: allowed-tools frontmatter key preserved after replacement"
else
  fail "T2d: allowed-tools frontmatter key MISSING after replacement"
fi

# Verify the installed line includes common tools
if echo "$INSTALLED_ALLOWED" | grep -q "read_file"; then
  pass "T2e: common tool 'read_file' present in macos install"
else
  fail "T2e: common tool 'read_file' MISSING from macos install"
fi

# --- Now test Windows platform via REASONIX_PLATFORM env var ---
T2_WIN_TARGET="${TEST_WORKSPACE}/t2-win-target"
mkdir -p "$T2_WIN_TARGET"

REASONIX_PLATFORM=windows bash "${T2_SOURCE}/install.sh" --target "$T2_WIN_TARGET" > /dev/null 2>&1 || true

WIN_INSTALLED_ALLOWED=$(grep "^allowed-tools:" "${T2_WIN_TARGET}/blackcow-alpha.md" | head -1)

# Verify it contains Windows-specific tools
if echo "$WIN_INSTALLED_ALLOWED" | grep -q "grep"; then
  pass "T2f: Windows platform — 'grep' present in installed allowed-tools"
else
  fail "T2f: Windows platform — 'grep' MISSING from installed allowed-tools"
fi

if echo "$WIN_INSTALLED_ALLOWED" | grep -q "bash"; then
  pass "T2g: Windows platform — 'bash' present in installed allowed-tools"
else
  fail "T2g: Windows platform — 'bash' MISSING from installed allowed-tools"
fi

# Verify macOS tools are NOT present in Windows build
if ! echo "$WIN_INSTALLED_ALLOWED" | grep -q "explore"; then
  pass "T2h: Windows platform — macOS tool 'explore' correctly excluded"
else
  fail "T2h: Windows platform — macOS tool 'explore' should NOT be present"
fi

# Verify COMMON_TOOLS are present in both platform installs
for tool in "read_file" "glob" "web_fetch" "write_file" "edit_file" "multi_edit"; do
  if ! echo "$INSTALLED_ALLOWED" | grep -q "$tool"; then
    fail "T2-mac-common: macOS — common tool '$tool' MISSING"
  fi
  if ! echo "$WIN_INSTALLED_ALLOWED" | grep -q "$tool"; then
    fail "T2-win-common: Windows — common tool '$tool' MISSING"
  fi
done
pass "T2i: All common tools present in both platform installs"

# Verify the two platforms produce DIFFERENT allowed-tools lines
if [[ "$INSTALLED_ALLOWED" != "$WIN_INSTALLED_ALLOWED" ]]; then
  pass "T2j: macOS and Windows produce different allowed-tools lines"
else
  fail "T2j: macOS and Windows produced IDENTICAL allowed-tools lines (platform detection failed)"
fi

# ============================================================================
# 3. Platform detection output (macOS vs Windows)
#    install.sh prints "→ Detected platform: <platform>" on stdout.
# ============================================================================
echo ""
echo "--- Test 3: Platform detection output ---"

T3_SOURCE="${TEST_WORKSPACE}/t3-source"
T3_TARGET="${TEST_WORKSPACE}/t3-target"
mkdir -p "$T3_TARGET"
setup_mock_source "$T3_SOURCE"

# Default (no env var) → should detect "macos" on non-Windows hosts
OUTPUT_DEFAULT=$(unset REASONIX_PLATFORM; bash "${T3_SOURCE}/install.sh" --target "$T3_TARGET" 2>&1) || true
if echo "$OUTPUT_DEFAULT" | grep -q "Detected platform: macos"; then
  pass "T3a: Default platform detection outputs 'macos'"
else
  fail "T3a: Default platform detection: expected 'macos' in output"
  echo "   Output was: $(echo "$OUTPUT_DEFAULT" | grep 'Detected platform')"
fi

# REASONIX_PLATFORM=windows → should output "windows"
T3_WIN_TARGET="${TEST_WORKSPACE}/t3-win-target"
mkdir -p "$T3_WIN_TARGET"
OUTPUT_WIN=$(REASONIX_PLATFORM=windows bash "${T3_SOURCE}/install.sh" --target "$T3_WIN_TARGET" 2>&1) || true
if echo "$OUTPUT_WIN" | grep -q "Detected platform: windows"; then
  pass "T3b: REASONIX_PLATFORM=windows outputs 'windows'"
else
  fail "T3b: REASONIX_PLATFORM=windows: expected 'windows' in output"
  echo "   Output was: $(echo "$OUTPUT_WIN" | grep 'Detected platform')"
fi

# Verify the summary footer includes platform info for windows
if echo "$OUTPUT_WIN" | grep -q "Installation complete for platform: windows"; then
  pass "T3c: Summary footer confirms 'platform: windows'"
else
  fail "T3c: Summary footer missing platform confirmation for windows"
fi

# Explicit REASONIX_PLATFORM=macos
T3_MAC_TARGET="${TEST_WORKSPACE}/t3-mac-target"
mkdir -p "$T3_MAC_TARGET"
OUTPUT_MAC=$(REASONIX_PLATFORM=macos bash "${T3_SOURCE}/install.sh" --target "$T3_MAC_TARGET" 2>&1) || true
if echo "$OUTPUT_MAC" | grep -q "Detected platform: macos"; then
  pass "T3d: REASONIX_PLATFORM=macos outputs 'macos'"
else
  fail "T3d: REASONIX_PLATFORM=macos: expected 'macos' in output"
  echo "   Output was: $(echo "$OUTPUT_MAC" | grep 'Detected platform')"
fi

# Verify summary footer for macos
if echo "$OUTPUT_MAC" | grep -q "Installation complete for platform: macos"; then
  pass "T3e: Summary footer confirms 'platform: macos'"
else
  fail "T3e: Summary footer missing platform confirmation for macos"
fi

# Verify platform indicator in footer for all three runs
if echo "$OUTPUT_DEFAULT" | grep -q "Mode:"; then
  info "Default run shows mode line (expected: no --dry-run so no mode line)"
fi

# ============================================================================
# 4. --dry-run mode doesn't write any files
#    With --dry-run, install.sh prints "[DRY-RUN]" and skips the sed write.
#    The target directory should remain empty (no .md files).
# ============================================================================
echo ""
echo "--- Test 4: --dry-run mode doesn't write files ---"

T4_SOURCE="${TEST_WORKSPACE}/t4-source"
T4_TARGET="${TEST_WORKSPACE}/t4-target"
mkdir -p "$T4_TARGET"
setup_mock_source "$T4_SOURCE"

# Run with --dry-run
OUTPUT_DRY=$(bash "${T4_SOURCE}/install.sh" --dry-run --target "$T4_TARGET" 2>&1) || true

# Verify output contains [DRY-RUN] markers for each skill
DRY_COUNT=$(echo "$OUTPUT_DRY" | grep -c "\[DRY-RUN\]" || true)
if [[ "$DRY_COUNT" -ge 2 ]]; then
  pass "T4a: --dry-run output contains [DRY-RUN] markers ($DRY_COUNT found)"
else
  fail "T4a: --dry-run output has only $DRY_COUNT [DRY-RUN] markers (expected ≥2)"
fi

# Verify NO .md files were written to the target (count via find, avoid set -e trap on glob)
DRY_RUN_FILES=$(find "${T4_TARGET}" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l)
if [[ "$DRY_RUN_FILES" -eq 0 ]]; then
  pass "T4b: --dry-run wrote 0 .md files to target directory"
else
  fail "T4b: --dry-run wrote $DRY_RUN_FILES files (expected 0)"
fi

# Verify output confirms dry-run mode in summary
if echo "$OUTPUT_DRY" | grep -q "Mode: DRY-RUN"; then
  pass "T4c: Summary footer confirms 'Mode: DRY-RUN'"
else
  fail "T4c: Summary footer missing DRY-RUN mode confirmation"
fi

# Verify no "✅ Installed to:" lines appear (those are real installs)
if echo "$OUTPUT_DRY" | grep -q "✅ Installed to:"; then
  fail "T4d: --dry-run shows '✅ Installed to:' lines (should only show [DRY-RUN])"
else
  pass "T4d: --dry-run output has no 'Installed to:' lines"
fi

# ============================================================================
# 5. chmod +x is applied to validate-*.sh test scripts
#    install.sh runs: chmod +x "$TEST_DIR"/validate-*.sh 2>/dev/null || true
#    where TEST_DIR = SOURCE_DIR/tests
# ============================================================================
echo ""
echo "--- Test 5: chmod +x applied to test scripts ---"

T5_SOURCE="${TEST_WORKSPACE}/t5-source"
T5_TARGET="${TEST_WORKSPACE}/t5-target"
mkdir -p "$T5_TARGET"
setup_mock_source "$T5_SOURCE"

# Precondition: verify validate-*.sh files are NOT executable before install
NON_EXEC_BEFORE=0
for f in "${T5_SOURCE}/tests/"validate-*.sh; do
  [[ ! -x "$f" ]] && NON_EXEC_BEFORE=$((NON_EXEC_BEFORE + 1))
done
if [[ "$NON_EXEC_BEFORE" -eq 4 ]]; then
  pass "T5a: Precondition — all 4 validate-*.sh files are NOT executable before install"
else
  fail "T5a: Precondition — only $NON_EXEC_BEFORE/4 files are non-executable (test setup issue)"
fi

# Run install.sh
bash "${T5_SOURCE}/install.sh" --target "$T5_TARGET" > /dev/null 2>&1 || true

# After install, verify files are now executable
EXEC_AFTER=0
for f in "${T5_SOURCE}/tests/"validate-*.sh; do
  [[ -x "$f" ]] && EXEC_AFTER=$((EXEC_AFTER + 1))
done
if [[ "$EXEC_AFTER" -eq 4 ]]; then
  pass "T5b: All 4 validate-*.sh files are executable after install.sh runs"
else
  fail "T5b: Only $EXEC_AFTER/4 validate-*.sh files executable (expected all 4)"
  ls -la "${T5_SOURCE}/tests/"
fi

# Verify the echo confirmation appeared in output
INSTALL_OUTPUT=$(bash "${T5_SOURCE}/install.sh" --target "$T5_TARGET" 2>&1) || true
if echo "$INSTALL_OUTPUT" | grep -q "All validate-.*\.sh scripts made executable"; then
  pass "T5c: install.sh outputs chmod confirmation message"
else
  fail "T5c: install.sh missing chmod confirmation message"
fi

# ============================================================================
# 6. Default target path (no --target flag)
#    Without --target, install.sh resolves ~/.reasonix/skills via
#    validate_install_path. With --dry-run we can observe where it
#    would install without writing anything.
# ============================================================================
echo ""
echo "--- Test 6: Default path behavior (no --target flag) ---"

T6_SOURCE="${TEST_WORKSPACE}/t6-source"
setup_mock_source "$T6_SOURCE"

# Run with --dry-run but NO --target → uses default ~/.reasonix/skills
# Must not exist as a TARGET yet — validate_install_path resolves it safely
OUTPUT_DEFAULT_PATH=$(bash "${T6_SOURCE}/install.sh" --dry-run 2>&1) || true

# Verify the output mentions .reasonix/skills as the install location
TARGET_LINE=$(echo "$OUTPUT_DEFAULT_PATH" | grep "Target:" | head -1)
if echo "$TARGET_LINE" | grep -q "${HOME}/.reasonix/skills"; then
  pass "T6a: Default target path resolves to ${HOME}/.reasonix/skills"
else
  fail "T6a: Default target path: expected '${HOME}/.reasonix/skills', got '$TARGET_LINE'"
fi

# Verify dry-run with default path still processes files
DRY_DEFAULT_COUNT=$(echo "$OUTPUT_DEFAULT_PATH" | grep -c "\[DRY-RUN\]" || true)
if [[ "$DRY_DEFAULT_COUNT" -ge 2 ]]; then
  pass "T6b: Dry-run with default path processes all skill files ($DRY_DEFAULT_COUNT [DRY-RUN] markers)"
else
  fail "T6b: Dry-run with default path: only $DRY_DEFAULT_COUNT [DRY-RUN] markers (expected ≥2)"
fi

# Verify the default path also mentions .reasonix/skills in summary
if echo "$OUTPUT_DEFAULT_PATH" | grep -q "Target:.*\.reasonix/skills"; then
  pass "T6c: Summary line shows .reasonix/skills target"
else
  fail "T6c: Summary line missing .reasonix/skills reference"
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "========================================"
SCORE=$(( TOTAL > 0 ? PASS * 100 / TOTAL : 0 ))
echo "Results: $PASS passed, $FAIL failed, 0 skipped (total $TOTAL checks)"
echo "Score: ${SCORE}%"
echo "========================================"

exit $(( FAIL > 0 ? 1 : 0 ))
