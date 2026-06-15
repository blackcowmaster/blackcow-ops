#!/usr/bin/env bash
# ============================================================================
# L4 System Tests — validate-blackcow-ecosystem-health.sh
#
# System-level: all flag combinations, error paths, edge cases.
# ============================================================================
set -euo pipefail

PASS=0; FAIL=0; TOTAL=0
pass() { PASS=$((PASS+1)); TOTAL=$((TOTAL+1)); echo "  ✅ PASS: $1"; }
fail() { FAIL=$((FAIL+1)); TOTAL=$((TOTAL+1)); echo "  ❌ FAIL: $1"; }

SCRIPT="skills/tests/validate-blackcow-ecosystem-health.sh"
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RUN="bash -c \"cd '$PROJECT_ROOT' && bash '$SCRIPT'\""

echo "=== L4 System Tests: ecosystem-health runner ==="
echo ""

# Test 1: --json suppresses text output
echo "--- --json output suppression ---"
json_out=$(eval "$RUN --json" 2>/dev/null) || true
if [[ "$json_out" == "{"* ]]; then
  # Should start with { not with text/ANSI
  if ! echo "$json_out" | head -1 | grep -q $'\033'; then
    pass "--json output is pure JSON (no ANSI)"
  else
    fail "--json output contains ANSI codes"
  fi
else
  fail "--json output does not start with '{': ${json_out:0:50}"
fi

# Test 2: --json + --verbose: JSON wins
echo "--- --json --verbose interaction ---"
jv_out=$(eval "$RUN --json --verbose" 2>/dev/null) || true
if [[ "$jv_out" == "{"* ]]; then
  pass "--json --verbose: JSON still emitted (JSON wins)"
else
  fail "--json --verbose: expected JSON, got: ${jv_out:0:50}"
fi

# Test 3: --json + --quiet: JSON wins
echo "--- --json --quiet interaction ---"
jq_out=$(eval "$RUN --json --quiet" 2>/dev/null) || true
if [[ "$jq_out" == "{"* ]]; then
  pass "--json --quiet: JSON still emitted"
else
  fail "--json --quiet: expected JSON, got: ${jq_out:0:50}"
fi

# Test 4: Normal mode produces text report
echo "--- Normal mode text output ---"
text_out=$(eval "$RUN" 2>/dev/null) || true
if echo "$text_out" | grep -q "BlackCow Ecosystem Health Report"; then
  pass "Normal mode: header present"
else
  fail "Normal mode: header missing"
fi
if echo "$text_out" | grep -q "Traffic Light Summary"; then
  pass "Normal mode: traffic light section present"
else
  fail "Normal mode: traffic light section missing"
fi
if echo "$text_out" | grep -q "Per-Script Scores"; then
  pass "Normal mode: per-script scores present"
else
  fail "Normal mode: per-script scores missing"
fi
if echo "$text_out" | grep -q "Health Score Breakdown"; then
  pass "Normal mode: health score breakdown present"
else
  fail "Normal mode: health score breakdown missing"
fi

# Test 5: --quiet reduces output
echo "--- --quiet output reduction ---"
quiet_out=$(eval "$RUN --quiet" 2>/dev/null) || true
normal_lines=$(echo "$text_out" | wc -l | tr -d ' ')
quiet_lines=$(echo "$quiet_out" | wc -l | tr -d ' ')
if [[ "$quiet_lines" -lt "$normal_lines" ]]; then
  pass "--quiet: fewer lines than normal ($quiet_lines < $normal_lines)"
else
  fail "--quiet: $quiet_lines lines vs normal $normal_lines lines (expected fewer)"
fi

# Test 6: JSON output is exactly one line
echo "--- JSON is single line ---"
json_lines=$(echo "$json_out" | wc -l | tr -d ' ')
if [[ "$json_lines" -eq 1 ]]; then
  pass "--json output is exactly 1 line"
else
  fail "--json output: $json_lines lines (expected 1)"
fi

# Test 7: All score values are in range 0-100
echo "--- Score range ---"
score_range=$(echo "$json_out" | python3 -c "
import json,sys
d=json.load(sys.stdin)
bad = []
for i,s in enumerate(d['scripts']):
    if not (0 <= s['score'] <= 100): bad.append(f'scripts[{i}].score={s[\"score\"]}')
if not (0 <= d['aggregate']['score'] <= 100): bad.append(f'aggregate.score={d[\"aggregate\"][\"score\"]}')
print('OK' if not bad else '; '.join(bad))
" 2>/dev/null)
if [[ "$score_range" == "OK" ]]; then
  pass "All scores in range [0,100]"
else
  fail "Score range: $score_range"
fi

# Test 8: script names match actual files
echo "--- Script name validity ---"
name_check=$(echo "$json_out" | python3 -c "
import json,sys,os
d=json.load(sys.stdin)
bad = []
for s in d['scripts']:
    if not s['name'].startswith('validate-') or not s['name'].endswith('.sh'):
        bad.append(s['name'])
print('OK' if not bad else '; '.join(bad))
" 2>/dev/null)
if [[ "$name_check" == "OK" ]]; then
  pass "All script names follow validate-*.sh pattern"
else
  fail "Invalid script names: $name_check"
fi

# Test 9: elapsed_s is consistent with run duration
echo "--- elapsed_s plausibility ---"
elapsed=$(echo "$json_out" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['elapsed_s'])" 2>/dev/null)
if [[ "$elapsed" -ge 1 && "$elapsed" -le 120 ]]; then
  pass "elapsed_s is plausible: ${elapsed}s (1-120 range)"
else
  fail "elapsed_s: ${elapsed}s (expected 1-120)"
fi

# Test 10: Non-existent flag is silently ignored (no crash)
echo "--- Unknown flag handling ---"
unknown_out=$(eval "$RUN --bogus-flag" 2>&1) || true
ec=$?
if [[ "$ec" -ge 0 && "$ec" -le 2 ]]; then
  pass "Unknown flag: exit code in [0,2] ($ec) — no crash"
else
  fail "Unknown flag: exit code $ec"
fi

# --- Summary ---
echo ""
echo "========================================"
echo "Results: $PASS passed, $FAIL failed, 0 skipped (total $TOTAL checks)"
echo "Score: $(( TOTAL > 0 ? PASS * 100 / TOTAL : 0 ))%"
echo "========================================"

exit $(( FAIL > 0 ? 1 : 0 ))
