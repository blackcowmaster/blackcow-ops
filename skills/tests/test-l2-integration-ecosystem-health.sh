#!/usr/bin/env bash
# ============================================================================
# L2 Integration Tests — validate-blackcow-ecosystem-health.sh
#
# Tests the script's integration with its sibling validate scripts.
# Focus: JSON output validity, exit codes, stderr cleanliness.
# ============================================================================
set -euo pipefail

PASS=0; FAIL=0; TOTAL=0
pass() { PASS=$((PASS+1)); TOTAL=$((TOTAL+1)); echo "  ✅ PASS: $1"; }
fail() { FAIL=$((FAIL+1)); TOTAL=$((TOTAL+1)); echo "  ❌ FAIL: $1"; }

SCRIPT="skills/tests/validate-blackcow-ecosystem-health.sh"
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "=== L2 Integration Tests: ecosystem-health runner ==="
echo ""

# Test 1: JSON mode produces valid JSON
echo "--- JSON output validity ---"
json_output=$(bash -c "cd '$PROJECT_ROOT' && bash '$SCRIPT' --json" 2>/dev/null) || true
if echo "$json_output" | python3 -c "import json,sys; json.load(sys.stdin)" 2>/dev/null; then
  pass "--json produces valid JSON"
else
  fail "--json produces valid JSON"
fi

# Test 2: JSON has all required top-level keys
echo "--- JSON schema: top-level keys ---"
keys=$(echo "$json_output" | python3 -c "import json,sys; d=json.load(sys.stdin); print(' '.join(sorted(d.keys())))" 2>/dev/null)
expected_keys="aggregate elapsed_s scripts traffic_light"
if [[ "$keys" == "$expected_keys" ]]; then
  pass "JSON top-level keys match spec: $keys"
else
  fail "JSON top-level keys: expected '$expected_keys', got '$keys'"
fi

# Test 3: Each script entry has all required fields
echo "--- JSON schema: script entry fields ---"
script_keys=$(echo "$json_output" | python3 -c "
import json,sys
d=json.load(sys.stdin)
keys = set()
for s in d['scripts']:
    keys.update(s.keys())
print(' '.join(sorted(keys)))
" 2>/dev/null)
expected_script_keys="fail name pass score skip status"
if [[ "$script_keys" == "$expected_script_keys" ]]; then
  pass "Script entry keys match spec: $script_keys"
else
  fail "Script entry keys: expected '$expected_script_keys', got '$script_keys'"
fi

# Test 4: Aggregate object has all required fields
echo "--- JSON schema: aggregate fields ---"
agg_keys=$(echo "$json_output" | python3 -c "import json,sys; d=json.load(sys.stdin); print(' '.join(sorted(d['aggregate'].keys())))" 2>/dev/null)
expected_agg_keys="fail pass score skip"
if [[ "$agg_keys" == "$expected_agg_keys" ]]; then
  pass "Aggregate keys match spec: $agg_keys"
else
  fail "Aggregate keys: expected '$expected_agg_keys', got '$agg_keys'"
fi

# Test 5: elapsed_s is a positive integer
echo "--- JSON: elapsed_s ---"
elapsed=$(echo "$json_output" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['elapsed_s'])" 2>/dev/null)
if [[ "$elapsed" =~ ^[0-9]+$ ]] && [[ "$elapsed" -gt 0 ]]; then
  pass "elapsed_s is positive integer: $elapsed"
else
  fail "elapsed_s: expected positive int, got '$elapsed'"
fi

# Test 6: traffic_light is valid value
echo "--- JSON: traffic_light ---"
tl=$(echo "$json_output" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['traffic_light'])" 2>/dev/null)
if [[ "$tl" == "GREEN" || "$tl" == "YELLOW" || "$tl" == "RED" ]]; then
  pass "traffic_light is valid: $tl"
else
  fail "traffic_light: expected GREEN/YELLOW/RED, got '$tl'"
fi

# Test 7: All script status values are PASS or FAIL
echo "--- JSON: script status values ---"
bad_status=$(echo "$json_output" | python3 -c "
import json,sys
d=json.load(sys.stdin)
bad = [s['status'] for s in d['scripts'] if s['status'] not in ('PASS','FAIL')]
print(len(bad))
" 2>/dev/null)
if [[ "$bad_status" == "0" ]]; then
  pass "All script status values are PASS or FAIL"
else
  fail "Found $bad_status script(s) with invalid status"
fi

# Test 8: JSON mode exit code is valid (0/1/2)
echo "--- Exit codes: JSON mode ---"
bash -c "cd '$PROJECT_ROOT' && bash '$SCRIPT' --json" >/dev/null 2>&1; ec=$?
if [[ "$ec" -ge 0 && "$ec" -le 2 ]]; then
  pass "--json exit code in [0,2]: $ec"
else
  fail "--json exit code: expected 0-2, got $ec"
fi

# Test 9: Normal mode exit code is valid
echo "--- Exit codes: normal mode ---"
bash -c "cd '$PROJECT_ROOT' && bash '$SCRIPT'" >/dev/null 2>&1; ec=$?
if [[ "$ec" -ge 0 && "$ec" -le 2 ]]; then
  pass "normal mode exit code in [0,2]: $ec"
else
  fail "normal mode exit code: expected 0-2, got $ec"
fi

# Test 10: JSON mode writes nothing to stderr
echo "--- Stderr: JSON mode ---"
stderr_output=$(bash -c "cd '$PROJECT_ROOT' && bash '$SCRIPT' --json" 2>&1 1>/dev/null) || true
if [[ -z "$stderr_output" ]]; then
  pass "--json produces no stderr output"
else
  fail "--json stderr: expected empty, got '$stderr_output'"
fi

# Test 11: Aggregate counts are consistent
echo "--- Data consistency: aggregate ---"
consistency=$(echo "$json_output" | python3 -c "
import json,sys
d=json.load(sys.stdin)
agg = d['aggregate']
scripts_total_pass = sum(s['pass'] for s in d['scripts'])
scripts_total_fail = sum(s['fail'] for s in d['scripts'])
scripts_total_skip = sum(s['skip'] for s in d['scripts'])
scripts_total_score = sum(s['pass'] + s['fail'] + s['skip'] for s in d['scripts'])
ok = (agg['pass'] == scripts_total_pass and 
      agg['fail'] == scripts_total_fail and 
      agg['skip'] == scripts_total_skip)
print('OK' if ok else f'MISMATCH: agg(p={agg[\"pass\"]},f={agg[\"fail\"]},s={agg[\"skip\"]}) vs sum(p={scripts_total_pass},f={scripts_total_fail},s={scripts_total_skip})')
" 2>/dev/null)
if [[ "$consistency" == "OK" ]]; then
  pass "Aggregate counts match sum of script counts"
else
  fail "Aggregate consistency: $consistency"
fi

# --- Summary ---
echo ""
echo "========================================"
echo "Results: $PASS passed, $FAIL failed, 0 skipped (total $TOTAL checks)"
echo "Score: $(( TOTAL > 0 ? PASS * 100 / TOTAL : 0 ))%"
echo "========================================"

exit $(( FAIL > 0 ? 1 : 0 ))
