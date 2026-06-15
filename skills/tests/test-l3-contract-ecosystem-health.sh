#!/usr/bin/env bash
# ============================================================================
# L3 Contract Tests — validate-blackcow-ecosystem-health.sh JSON schema contract
#
# Validates the JSON output contract precisely against the governance spec.
# ============================================================================
set -euo pipefail

PASS=0; FAIL=0; TOTAL=0
pass() { PASS=$((PASS+1)); TOTAL=$((TOTAL+1)); echo "  ✅ PASS: $1"; }
fail() { FAIL=$((FAIL+1)); TOTAL=$((TOTAL+1)); echo "  ❌ FAIL: $1"; }

SCRIPT="skills/tests/validate-blackcow-ecosystem-health.sh"
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "=== L3 Contract Tests: ecosystem-health JSON schema ==="
echo ""

json_output=$(bash -c "cd '$PROJECT_ROOT' && bash '$SCRIPT' --json" 2>/dev/null) || true
schema_ok=true

# Contract point 1: Root is a single JSON object (not array)
echo "--- Root type ---"
if echo "$json_output" | python3 -c "import json,sys; d=json.load(sys.stdin); assert isinstance(d, dict)" 2>/dev/null; then
  pass "Root is a JSON object (dict)"
else
  fail "Root is a JSON object"
  schema_ok=false
fi

# Contract point 2: Exactly 4 top-level keys, no more, no less
echo "--- Exact top-level keys ---"
top_count=$(echo "$json_output" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.keys()))" 2>/dev/null)
if [[ "$top_count" == "4" ]]; then
  pass "Exactly 4 top-level keys: $top_count"
else
  fail "Top-level key count: expected 4, got $top_count"
  schema_ok=false
fi

# Contract point 3: scripts is a JSON array
echo "--- scripts is array ---"
scripts_type=$(echo "$json_output" | python3 -c "import json,sys; d=json.load(sys.stdin); print(type(d['scripts']).__name__)" 2>/dev/null)
if [[ "$scripts_type" == "list" ]]; then
  pass "scripts is a list/array"
else
  fail "scripts type: expected list, got $scripts_type"
  schema_ok=false
fi

# Contract point 4: Each script entry has exactly 6 fields
echo "--- Script entry field count ---"
field_counts=$(echo "$json_output" | python3 -c "
import json,sys
d=json.load(sys.stdin)
counts = [len(s.keys()) for s in d['scripts']]
print(' '.join(str(c) for c in counts))
" 2>/dev/null)
all_six=true
for c in $field_counts; do
  if [[ "$c" != "6" ]]; then all_six=false; fi
done
if $all_six; then
  pass "All script entries have exactly 6 fields"
else
  fail "Script field counts: $field_counts (expected all 6)"
  schema_ok=false
fi

# Contract point 5: Field types are correct
echo "--- Field types ---"
type_check=$(echo "$json_output" | python3 -c "
import json,sys
d=json.load(sys.stdin)
errors = []
for i, s in enumerate(d['scripts']):
    if not isinstance(s['name'], str): errors.append(f'scripts[{i}].name not str')
    if not isinstance(s['pass'], int): errors.append(f'scripts[{i}].pass not int')
    if not isinstance(s['fail'], int): errors.append(f'scripts[{i}].fail not int')
    if not isinstance(s['skip'], int): errors.append(f'scripts[{i}].skip not int')
    if not isinstance(s['score'], int): errors.append(f'scripts[{i}].score not int')
    if not isinstance(s['status'], str): errors.append(f'scripts[{i}].status not str')
if not isinstance(d['aggregate']['pass'], int): errors.append('aggregate.pass not int')
if not isinstance(d['aggregate']['fail'], int): errors.append('aggregate.fail not int')
if not isinstance(d['aggregate']['skip'], int): errors.append('aggregate.skip not int')
if not isinstance(d['aggregate']['score'], int): errors.append('aggregate.score not int')
if not isinstance(d['traffic_light'], str): errors.append('traffic_light not str')
if not isinstance(d['elapsed_s'], int): errors.append('elapsed_s not int')
if errors:
    for e in errors: print(f'ERROR: {e}')
else:
    print('ALL_TYPES_OK')
" 2>/dev/null)
if [[ "$type_check" == "ALL_TYPES_OK" ]]; then
  pass "All field types are correct"
else
  fail "Field type errors: $type_check"
  schema_ok=false
fi

# Contract point 6: No extra fields at top level
echo "--- No extra top-level fields ---"
extra_fields=$(echo "$json_output" | python3 -c "
import json,sys
d=json.load(sys.stdin)
allowed = {'scripts','aggregate','traffic_light','elapsed_s'}
extra = set(d.keys()) - allowed
print(','.join(sorted(extra)) if extra else 'NONE')
" 2>/dev/null)
if [[ "$extra_fields" == "NONE" ]]; then
  pass "No extra top-level fields"
else
  fail "Extra top-level fields: $extra_fields"
  schema_ok=false
fi

# Contract point 7: No extra fields in script entries
echo "--- No extra script fields ---"
script_extra=$(echo "$json_output" | python3 -c "
import json,sys
d=json.load(sys.stdin)
allowed = {'name','pass','fail','skip','score','status'}
all_extra = set()
for s in d['scripts']:
    all_extra.update(set(s.keys()) - allowed)
print(','.join(sorted(all_extra)) if all_extra else 'NONE')
" 2>/dev/null)
if [[ "$script_extra" == "NONE" ]]; then
  pass "No extra fields in script entries"
else
  fail "Extra script entry fields: $script_extra"
  schema_ok=false
fi

# Contract point 8: No extra fields in aggregate
echo "--- No extra aggregate fields ---"
agg_extra=$(echo "$json_output" | python3 -c "
import json,sys
d=json.load(sys.stdin)
allowed = {'pass','fail','skip','score'}
extra = set(d['aggregate'].keys()) - allowed
print(','.join(sorted(extra)) if extra else 'NONE')
" 2>/dev/null)
if [[ "$agg_extra" == "NONE" ]]; then
  pass "No extra fields in aggregate"
else
  fail "Extra aggregate fields: $agg_extra"
  schema_ok=false
fi

# Contract point 9: status is strictly "PASS" or "FAIL"
echo "--- Status enum ---"
status_check=$(echo "$json_output" | python3 -c "
import json,sys
d=json.load(sys.stdin)
bad = [(i,s['status']) for i,s in enumerate(d['scripts']) if s['status'] not in ('PASS','FAIL')]
for i,st in bad: print(f'scripts[{i}].status={st}')
print('OK' if not bad else '')
" 2>/dev/null)
if [[ "$status_check" == "OK" ]]; then
  pass "All status values are PASS or FAIL"
else
  fail "Invalid status values: $status_check"
  schema_ok=false
fi

# Contract point 10: traffic_light is strictly GREEN/YELLOW/RED
echo "--- traffic_light enum ---"
tl=$(echo "$json_output" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['traffic_light'])" 2>/dev/null)
if [[ "$tl" == "GREEN" || "$tl" == "YELLOW" || "$tl" == "RED" ]]; then
  pass "traffic_light is valid enum: $tl"
else
  fail "traffic_light: expected GREEN/YELLOW/RED, got '$tl'"
  schema_ok=false
fi

# Contract point 11: score matches pass/(pass+fail+skip)
echo "--- Score calculation ---"
score_check=$(echo "$json_output" | python3 -c "
import json,sys
d=json.load(sys.stdin)
errors = []
for i,s in enumerate(d['scripts']):
    total = s['pass'] + s['fail'] + s['skip']
    if total > 0:
        expected = round(s['pass'] / total * 100)
        if s['score'] != expected:
            errors.append(f'scripts[{i}].score={s[\"score\"]} expected={expected}')
agg_total = d['aggregate']['pass'] + d['aggregate']['fail'] + d['aggregate']['skip']
if agg_total > 0:
    agg_expected = round(d['aggregate']['pass'] / agg_total * 100)
    if d['aggregate']['score'] != agg_expected:
        errors.append(f'aggregate.score={d[\"aggregate\"][\"score\"]} expected={agg_expected}')
if errors:
    for e in errors: print(f'ERROR: {e}')
else:
    print('ALL_SCORES_CORRECT')
" 2>/dev/null)
if [[ "$score_check" == "ALL_SCORES_CORRECT" ]]; then
  pass "All score values match pass/(pass+fail+skip)"
else
  fail "Score mismatch: $score_check"
  schema_ok=false
fi

# --- Summary ---
echo ""
echo "========================================"
if $schema_ok; then
  echo "Contract: FULLY COMPLIANT"
else
  echo "Contract: VIOLATIONS DETECTED"
fi
echo "Results: $PASS passed, $FAIL failed, 0 skipped (total $TOTAL checks)"
echo "Score: $(( TOTAL > 0 ? PASS * 100 / TOTAL : 0 ))%"
echo "========================================"

exit $(( FAIL > 0 ? 1 : 0 ))
