#!/usr/bin/env bash
# BKIT 11-Gate Evidence Collector — input-sanitization
set -euo pipefail
SLUG="input-sanitization"
EVID=".omo/ulw-loop/evidence"

echo "=== M1 spec-match ==="
echo "Check: sanitizeText exists, trim→stripTags→htmlEscape order, emoji preserved"
grep -n "sanitizeText" src/lib/sanitize.ts 2>/dev/null || echo "M1_FAIL: sanitizeText not found"
grep -n "trim\|stripTags\|htmlEscape\|replace.*<[^>]*>" src/lib/sanitize.ts 2>/dev/null || echo "M1_WARN: pipeline steps unclear"

echo "=== M2 test-pass ==="
npm test 2>&1 | tail -5

echo "=== M2 coverage ==="
npx jest --coverage --collectCoverageFrom='src/lib/sanitize.ts' 2>&1 | tail -20

echo "=== M3 regression ==="
npm test -- --forceExit 2>&1 | grep -E "Tests:|Test Suites:" | tail -2

echo "=== M4 lint ==="
npx eslint src/ --max-warnings 0 2>&1 || true

echo "=== M5 dead-code ==="
echo "Manual check: grep for unreferenced exports in sanitize.ts"

echo "=== S1 dataFlow ==="
echo "Check: GET /api/tasks/:id → no double-escaping in response"
echo "Check: empty description '' → null in DB"

echo "=== S2 auth ==="
echo "Check: all entry points behind auth middleware"

echo "=== S3 injection ==="
echo "Check: no XSS payload survives POST/PUT"

echo "=== P1 query ==="
echo "Check: no N+1 in sanitization path"

echo "=== P2 memory ==="
echo "Check: no unbounded growth in string operations"

echo "=== P3 latency ==="
echo "Check: sanitizeText sub-ms for 5000-char input"
