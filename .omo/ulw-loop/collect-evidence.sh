#!/usr/bin/env bash
# Evidence collector for validate-input-guard
# Gates: M1 (spec-match), M2 (test-pass/coverage), M3 (regression), M4 (lint)

SLUG="validate-input-guard"
EVIDENCE_DIR=".omo/ulw-loop/evidence"

echo "=== M1 SPEC MATCH ==="
echo "Checking each script has preflight guard..."
for script in skills/tests/validate-blackcow-*.sh skills/tests/validate-cross-skill-contract.sh; do
    name=$(basename "$script")
    if grep -q 'FATAL: Target file not found' "$script" 2>/dev/null; then
        echo "  $name: GUARD PRESENT"
    else
        echo "  $name: MISSING GUARD"
    fi
done

echo ""
echo "=== M2 TEST PASS ==="
echo "Running ecosystem-health with valid targets..."
bash skills/tests/validate-blackcow-ecosystem-health.sh 2>&1 | tail -5

echo ""
echo "=== M2 PREFLIGHT VERIFICATION ==="
echo "Testing missing-target behavior..."
for script in skills/tests/validate-blackcow-plan.sh skills/tests/validate-blackcow-governor.sh; do
    name=$(basename "$script")
    result=$(bash "$script" /nonexistent 2>&1)
    exit_code=$?
    if [[ "$exit_code" -eq 1 ]] && echo "$result" | grep -q "FATAL: Target file not found"; then
        echo "  $name: PASS (exit=$exit_code, FATAL present)"
    else
        echo "  $name: FAIL (exit=$exit_code)"
    fi
done

echo ""
echo "=== M3 REGRESSION ==="
echo "Running all scripts with valid targets..."
bash skills/tests/validate-blackcow-ecosystem-health.sh 2>&1 | grep -E '(PASSED|FAILED|Total)'

echo ""
echo "=== M4 LINT ==="
echo "ShellCheck results:"
shellcheck skills/tests/validate-blackcow-*.sh skills/tests/validate-cross-skill-contract.sh 2>&1 | tail -20
