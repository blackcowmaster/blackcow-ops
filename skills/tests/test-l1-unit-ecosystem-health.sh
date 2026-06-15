#!/usr/bin/env bash
# ============================================================================
# L1 Unit Tests — validate-blackcow-ecosystem-health.sh helper functions
#
# Tests: strip_ansi(), safe_int(), parse_counts()
# ============================================================================
set -euo pipefail

PASS=0; FAIL=0; TOTAL=0
pass() { PASS=$((PASS+1)); TOTAL=$((TOTAL+1)); echo "  ✅ PASS: $1"; }
fail() { FAIL=$((FAIL+1)); TOTAL=$((TOTAL+1)); echo "  ❌ FAIL: $1"; }

# Source the helper functions from the target script (extract them)
source_helpers() {
  # Extract strip_ansi, safe_int, parse_counts from the target
  eval "$(sed -n '/^strip_ansi()/,/^}/p' skills/tests/validate-blackcow-ecosystem-health.sh)"
  eval "$(sed -n '/^safe_int()/,/^}/p' skills/tests/validate-blackcow-ecosystem-health.sh)"
  eval "$(sed -n '/^parse_counts()/,/^}/p' skills/tests/validate-blackcow-ecosystem-health.sh)"
}
source_helpers

echo "=== L1 Unit Tests: ecosystem-health helper functions ==="
echo ""

# --- strip_ansi tests ---
echo "--- strip_ansi ---"

result=$(strip_ansi $'\033[0;32mPASS\033[0m')
[[ "$result" == "PASS" ]] && pass "strip_ansi removes green ANSI codes" || fail "strip_ansi green: got '$result'"

result=$(strip_ansi $'\033[0;31mFAIL\033[0m')
[[ "$result" == "FAIL" ]] && pass "strip_ansi removes red ANSI codes" || fail "strip_ansi red: got '$result'"

result=$(strip_ansi "")
[[ "$result" == "" ]] && pass "strip_ansi empty string → empty" || fail "strip_ansi empty: got '$result'"

result=$(echo "plain text" | strip_ansi)
[[ "$result" == "plain text" ]] && pass "strip_ansi pipe: plain text unchanged" || fail "strip_ansi pipe: got '$result'"

result=$(echo $'\033[1;33mWARN\033[0m' | strip_ansi)
[[ "$result" == "WARN" ]] && pass "strip_ansi pipe: removes ANSI from piped input" || fail "strip_ansi pipe ANSI: got '$result'"

# --- safe_int tests ---
echo ""
echo "--- safe_int ---"

val=$(safe_int "42")
[[ "$val" == "42" ]] && pass "safe_int '42' → 42" || fail "safe_int '42': got '$val'"

val=$(safe_int "0")
[[ "$val" == "0" ]] && pass "safe_int '0' → 0" || fail "safe_int '0': got '$val'"

val=$(safe_int "")
[[ "$val" == "0" ]] && pass "safe_int empty → 0" || fail "safe_int empty: got '$val'"

val=$(safe_int "abc")
[[ "$val" == "0" ]] && pass "safe_int 'abc' → 0 (non-numeric)" || fail "safe_int 'abc': got '$val'"

val=$(safe_int "  123  ")
[[ "$val" == "123" ]] && pass "safe_int '  123  ' → 123" || fail "safe_int whitespace: got '$val'"

val=$(safe_int "there are 42 things")
[[ "$val" == "42" ]] && pass "safe_int extracts first number from mixed text" || fail "safe_int mixed: got '$val'"

# --- parse_counts tests ---
echo ""
echo "--- parse_counts ---"

# Pattern 1: "Results: N passed, N failed, N skipped (total N checks)"
read -r p f s t < <(parse_counts "Results: 10 passed, 2 failed, 1 skipped (total 13 checks)")
[[ "$p" == "10" && "$f" == "2" && "$s" == "1" && "$t" == "13" ]] && pass "parse_counts Pattern 1: Results:" || fail "parse_counts P1: got p=$p f=$f s=$s t=$t"

# Pattern 2: "Total tests: N" with "Passed:" / "Failed:"
read -r p f s t < <(parse_counts $'Total tests: 20\nPassed: 18\nFailed: 2')
[[ "$p" == "18" && "$f" == "2" && "$t" == "20" ]] && pass "parse_counts Pattern 2: Total tests:" || fail "parse_counts P2: got p=$p f=$f s=$s t=$t"

# Pattern 3: "Passed: N" / "Failed: N"
read -r p f s t < <(parse_counts $'Passed: 5\nFailed: 1')
[[ "$p" == "5" && "$f" == "1" && "$t" == "6" ]] && pass "parse_counts Pattern 3: Passed:/Failed:" || fail "parse_counts P3: got p=$p f=$f s=$s t=$t"

# Empty input
read -r p f s t < <(parse_counts "")
[[ "$p" == "0" && "$f" == "0" && "$s" == "0" && "$t" == "0" ]] && pass "parse_counts empty → all zeros" || fail "parse_counts empty: got p=$p f=$f s=$s t=$t"

# ANSI-polluted input
read -r p f s t < <(parse_counts $'Results: \033[0;32m10 passed\033[0m, \033[0;31m2 failed\033[0m, 1 skipped (total 13 checks)')
[[ "$p" == "10" && "$f" == "2" && "$s" == "1" && "$t" == "13" ]] && pass "parse_counts with ANSI codes" || fail "parse_counts ANSI: got p=$p f=$f s=$s t=$t"

# --- Summary ---
echo ""
echo "========================================"
echo "Results: $PASS passed, $FAIL failed, 0 skipped (total $TOTAL checks)"
echo "Score: $(( PASS * 100 / TOTAL ))%"
echo "========================================"

exit $(( FAIL > 0 ? 1 : 0 ))
