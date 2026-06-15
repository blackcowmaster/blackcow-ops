#!/usr/bin/env bash
# ============================================================================
# L5 E2E Tests — validate-blackcow-ecosystem-health.sh
#
# End-to-end: run the health check against the full ecosystem and verify
# all outputs are coherent.
# ============================================================================
set -euo pipefail

PASS=0; FAIL=0; TOTAL=0
pass() { PASS=$((PASS+1)); TOTAL=$((TOTAL+1)); echo "  ✅ PASS: $1"; }
fail() { FAIL=$((FAIL+1)); TOTAL=$((TOTAL+1)); echo "  ❌ FAIL: $1"; }

SCRIPT="skills/tests/validate-blackcow-ecosystem-health.sh"
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "=== L5 E2E Tests: ecosystem-health full pipeline ==="
echo ""

# --- Collect both outputs ---
json_out=$(bash -c "cd '$PROJECT_ROOT' && bash '$SCRIPT' --json" 2>/dev/null) || true
text_out=$(bash -c "cd '$PROJECT_ROOT' && bash '$SCRIPT'" 2>/dev/null) || true

# Test 1: JSON and text agree on aggregate score
echo "--- Cross-mode consistency: aggregate score ---"
json_score=$(echo "$json_out" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['aggregate']['score'])" 2>/dev/null)
text_score=$(echo "$text_out" | grep "Aggregate:" | tail -1 | grep -oE '[0-9]+%' | grep -oE '[0-9]+' || echo "0")
if [[ "$json_score" == "$text_score" ]]; then
  pass "Aggregate score matches: JSON=$json_score%, text=$text_score%"
else
  fail "Aggregate score mismatch: JSON=$json_score%, text=$text_score%"
fi

# Test 2: JSON and text agree on traffic light
echo "--- Cross-mode consistency: traffic light ---"
json_tl=$(echo "$json_out" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['traffic_light'])" 2>/dev/null)
if echo "$text_out" | grep -q "RED.*Failures" && [[ "$json_tl" == "RED" ]]; then
  pass "Traffic light matches: both RED"
elif echo "$text_out" | grep -q "YELLOW.*Warnings" && [[ "$json_tl" == "YELLOW" ]]; then
  pass "Traffic light matches: both YELLOW"
elif echo "$text_out" | grep -q "GREEN.*Healthy" && [[ "$json_tl" == "GREEN" ]]; then
  pass "Traffic light matches: both GREEN"
else
  fail "Traffic light mismatch: JSON=$json_tl, text=$(echo "$text_out" | grep 'Traffic light:' | head -1)"
fi

# Test 3: Script count matches between modes
echo "--- Cross-mode consistency: script count ---"
json_count=$(echo "$json_out" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d['scripts']))" 2>/dev/null)
text_count=$(echo "$text_out" | grep "Scripts run:" | grep -oE '[0-9]+' | head -1 || echo "0")
if [[ "$json_count" == "$text_count" ]]; then
  pass "Script count matches: $json_count scripts"
else
  fail "Script count mismatch: JSON=$json_count, text=$text_count"
fi

# Test 4: Per-script names match between modes
echo "--- Cross-mode consistency: script names ---"
json_names=$(echo "$json_out" | python3 -c "
import json,sys
d=json.load(sys.stdin)
for s in d['scripts']: print(s['name'])
" 2>/dev/null | sort)
text_names=$(echo "$text_out" | grep -E '^\s+validate-' | awk '{print $1}' | sort)
if [[ "$json_names" == "$text_names" ]]; then
  pass "Script names match between JSON and text"
else
  fail "Script name mismatch"
fi

# Test 5: JSON exit code reflects traffic light
echo "--- Exit code vs traffic light ---"
bash -c "cd '$PROJECT_ROOT' && bash '$SCRIPT' --json" >/dev/null 2>&1; json_ec=$?
if [[ "$json_tl" == "GREEN" && "$json_ec" -eq 0 ]]; then
  pass "GREEN → exit 0"
elif [[ "$json_tl" == "YELLOW" && "$json_ec" -eq 1 ]]; then
  pass "YELLOW → exit 1"
elif [[ "$json_tl" == "RED" && "$json_ec" -eq 2 ]]; then
  pass "RED → exit 2"
else
  fail "Exit code mismatch: $json_tl → exit $json_ec (expected GREEN→0, YELLOW→1, RED→2)"
fi

# Test 6: File-based JSON report was written
echo "--- Artifact: file-based JSON ---"
if [[ -f "$PROJECT_ROOT/.omo/governor/ecosystem-health-report.json" ]]; then
  pass "File-based JSON report exists"
else
  fail "File-based JSON report missing"
fi

# Test 7: File-based text report was written
echo "--- Artifact: file-based text report ---"
if [[ -f "$PROJECT_ROOT/.omo/governor/ecosystem-health-report.txt" ]]; then
  pass "File-based text report exists"
else
  fail "File-based text report missing"
fi

# Test 8: All expected skill groups appear
echo "--- Skill group coverage ---"
for group in "governor" "plan" "cross-skill" "ecosystem"; do
  if echo "$text_out" | grep -q "$group"; then
    pass "Skill group '$group' appears in report"
  else
    fail "Skill group '$group' missing from report"
  fi
done

# Test 9: No crash on consecutive runs (idempotency)
echo "--- Idempotency: consecutive runs ---"
bash -c "cd '$PROJECT_ROOT' && bash '$SCRIPT' --json" >/dev/null 2>&1; ec1=$?
bash -c "cd '$PROJECT_ROOT' && bash '$SCRIPT' --json" >/dev/null 2>&1; ec2=$?
if [[ "$ec1" -eq "$ec2" ]]; then
  pass "Consecutive runs produce same exit code: $ec1"
else
  fail "Consecutive runs: exit codes differ ($ec1 vs $ec2)"
fi

# Test 10: Pipeline integration: JSON → python → valid
echo "--- Pipeline: --json | python3 -m json.tool ---"
if echo "$json_out" | python3 -m json.tool >/dev/null 2>&1; then
  pass "JSON pipes to python3 -m json.tool successfully"
else
  fail "JSON pipe to python3 -m json.tool failed"
fi

# --- Summary ---
echo ""
echo "========================================"
echo "Results: $PASS passed, $FAIL failed, 0 skipped (total $TOTAL checks)"
echo "Score: $(( TOTAL > 0 ? PASS * 100 / TOTAL : 0 ))%"
echo "========================================"

exit $(( FAIL > 0 ? 1 : 0 ))
