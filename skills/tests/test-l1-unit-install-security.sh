#!/usr/bin/env bash
# ============================================================================
# L1 Unit Tests — install.sh path validation functions
#
# Tests: resolve_path(), validate_install_path()
# ============================================================================
set -euo pipefail

PASS=0; FAIL=0; TOTAL=0
pass() { PASS=$((PASS+1)); TOTAL=$((TOTAL+1)); echo "  ✅ PASS: $1"; }
fail() { FAIL=$((FAIL+1)); TOTAL=$((TOTAL+1)); echo "  ❌ FAIL: $1"; }

# Source the helper functions from install.sh (extract them)
source_helpers() {
  eval "$(sed -n '/^resolve_path()/,/^}/p' skills/install.sh)"
  eval "$(sed -n '/^validate_install_path()/,/^}/p' skills/install.sh)"
}
source_helpers

echo "=== L1 Unit Tests: install.sh path validation functions ==="
echo ""

# ========================================================================
# resolve_path() tests
# ========================================================================
echo "--- resolve_path ---"

result=$(resolve_path "$HOME/.reasonix/skills")
[[ -n "$result" ]] && pass "resolve_path: returns non-empty for existing dir" || fail "resolve_path: empty result for $HOME/.reasonix/skills"

result=$(resolve_path "$HOME/.reasonix/skills/nonexistent")
[[ -n "$result" ]] && pass "resolve_path: returns non-empty for nonexistent path (realpath -m)" || fail "resolve_path: empty for nonexistent path"

result=$(resolve_path "/tmp")
[[ "$result" == "/tmp" || "$result" == "/private/tmp" ]] && pass "resolve_path: resolves /tmp correctly (got: $result)" || fail "resolve_path: /tmp → $result (expected /tmp or /private/tmp)"

# ========================================================================
# validate_install_path() — Attack Vectors (must FAIL with FATAL)
# ========================================================================
echo ""
echo "--- Attack Vectors (must FAIL) ---"

# Test 1: .. traversal — classic path traversal
output=$(validate_install_path "/tmp/../etc/passwd" 2>&1) && fail "T1: .. traversal should have failed" || pass "T1: .. traversal blocked"

# Test 2: .. anywhere — foo../bar pattern
output=$(validate_install_path "foo../bar" 2>&1) && fail "T2: .. anywhere should have failed" || pass "T2: .. anywhere blocked"

# Test 3: // double sep
output=$(validate_install_path "//etc/cron.d" 2>&1) && fail "T3: // should have failed" || pass "T3: double-slash blocked"

# Test 4: Null byte injection
output=$(validate_install_path $'/tmp/good\x00/etc' 2>&1) && fail "T4: null byte should have failed" || pass "T4: null byte blocked"

# Test 5: Symlink TOCTOU — create symlink, then validate
SYMLINK_TEST_DIR="/tmp/install-path-test-$$"
mkdir -p "$SYMLINK_TEST_DIR"
ln -sf /etc "$SYMLINK_TEST_DIR/evil_link" 2>/dev/null || true
output=$(validate_install_path "$SYMLINK_TEST_DIR/evil_link" 2>&1) && fail "T5: symlink to /etc should have failed" || pass "T5: symlink TOCTOU blocked"
rm -rf "$SYMLINK_TEST_DIR"

# Test 6: Home-relative confusion — ~/../../etc
output=$(validate_install_path "~/../../etc" 2>&1) && fail "T6: ~/../../etc should have failed" || pass "T6: home-relative confusion blocked"

# ========================================================================
# validate_install_path() — Benign Paths (must PASS)
# ========================================================================
echo ""
echo "--- Benign Paths (must PASS) ---"

# Test 7: Default path
result=$(validate_install_path "$HOME/.reasonix/skills" 2>&1)
[[ -n "$result" && "$result" == "$HOME"* ]] && pass "T7: default path resolves" || fail "T7: default path failed: $result"

# Test 8: Relative inside HOME — pass in absolute path under .reasonix
result=$(validate_install_path "$HOME/.reasonix/skills/custom" 2>&1)
[[ -n "$result" && "$result" == "$HOME"* ]] && pass "T8: subdirectory under .reasonix resolves" || fail "T8: subdirectory failed: $result"

# Test 9: Standard ~ expansion
result=$(validate_install_path "~/.reasonix/skills" 2>&1)
[[ -n "$result" && "$result" == "$HOME"* ]] && pass "T9: ~ expansion resolves correctly" || fail "T9: ~ expansion failed: $result"

# Test 10: Subdirectory
result=$(validate_install_path "$HOME/.reasonix/skills/v2" 2>&1)
[[ -n "$result" && "$result" == "$HOME"* ]] && pass "T10: subdirectory v2 resolves" || fail "T10: subdirectory failed: $result"

# ========================================================================
# validate_install_path() — Edge Cases
# ========================================================================
echo ""
echo "--- Edge Cases ---"

# Test 11: Empty string
output=$(validate_install_path "" 2>&1) && fail "T11: empty string should have failed" || pass "T11: empty string blocked"

# Test 12: Trailing ..
output=$(validate_install_path "/tmp/foo/.." 2>&1) && fail "T12: trailing .. should have failed" || pass "T12: trailing .. blocked"

# Test 13: Triple slash (contains //)
output=$(validate_install_path "///etc" 2>&1) && fail "T13: /// should have failed (contains //)" || pass "T13: triple slash blocked"

# Test 14: Already-resolved safe path under .reasonix
result=$(validate_install_path "$HOME/.reasonix/skills" 2>&1)
[[ -n "$result" ]] && pass "T14: already-resolved safe path passes" || fail "T14: already-resolved failed: $result"

# Test 15: Path with spaces
result=$(validate_install_path "$HOME/.reasonix/my skills" 2>&1)
[[ -n "$result" ]] && pass "T15: path with spaces resolves" || fail "T15: path with spaces failed: $result"

# Test 16: Path that doesn't exist yet (realpath -m coverage)
result=$(validate_install_path "$HOME/.reasonix/skills/nonexistent" 2>&1)
[[ -n "$result" ]] && pass "T16: nonexistent path resolves (realpath -m)" || fail "T16: nonexistent path failed: $result"

# Test 17: Prefix bypass attempt — .reasonixfoo should be blocked
output=$(validate_install_path "$HOME/.reasonixfoo/skills" 2>&1) && fail "T17: .reasonixfoo should have been blocked" || pass "T17: .reasonixfoo prefix bypass blocked"

# Test 18: Exact ALLOWED_PREFIX path allowed
result=$(validate_install_path "$HOME/.reasonix" 2>&1)
[[ -n "$result" ]] && pass "T18: exact prefix path allowed" || fail "T18: exact prefix path failed: $result"

# ========================================================================
# Summary
# ========================================================================
echo ""
echo "========================================"
SCORE=$(( PASS * 100 / TOTAL ))
echo "Results: $PASS passed, $FAIL failed, 0 skipped (total $TOTAL checks)"
echo "Score: ${SCORE}%"
echo "========================================"

exit $(( FAIL > 0 ? 1 : 0 ))
