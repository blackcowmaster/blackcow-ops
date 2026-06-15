#!/usr/bin/env bash
# collect-evidence.sh — BKIT 11-gate evidence collector for perf-validate-health-p3
set -euo pipefail

SLUG="perf-validate-health-p3"
EVID="${SLUG}"
DIR=".omo/ulw-loop/evidence"

# ---- M1: spec-match ----
collect_M1() {
  echo "=== M1: spec-match ==="
  # Diff default mode output before/after
  if [[ -f "${DIR}/${EVID}-m1-default-before.txt" && -f "${DIR}/${EVID}-m1-default-after.txt" ]]; then
    diff "${DIR}/${EVID}-m1-default-before.txt" "${DIR}/${EVID}-m1-default-after.txt" && echo "M1_DEFAULT: IDENTICAL" || echo "M1_DEFAULT: DIFFER"
  fi
  if [[ -f "${DIR}/${EVID}-m1-json-before.txt" && -f "${DIR}/${EVID}-m1-json-after.txt" ]]; then
    diff "${DIR}/${EVID}-m1-json-before.txt" "${DIR}/${EVID}-m1-json-after.txt" && echo "M1_JSON: IDENTICAL" || echo "M1_JSON: DIFFER"
  fi
  if [[ -f "${DIR}/${EVID}-m1-summary-before.txt" && -f "${DIR}/${EVID}-m1-summary-after.txt" ]]; then
    diff "${DIR}/${EVID}-m1-summary-before.txt" "${DIR}/${EVID}-m1-summary-after.txt" && echo "M1_SUMMARY: IDENTICAL" || echo "M1_SUMMARY: DIFFER"
  fi
}

# ---- M2: test-pass ----
collect_M2() {
  echo "=== M2: test-pass ==="
  echo "Test results from: ${DIR}/${EVID}-m2-test.txt"
}

# ---- M3: regression ----
collect_M3() {
  echo "=== M3: regression ==="
  echo "Regression count from: ${DIR}/${EVID}-m3-regression.txt"
}

# ---- M4: lint ----
collect_M4() {
  echo "=== M4: lint ==="
  echo "Lint warnings from: ${DIR}/${EVID}-m4-lint.txt"
}

# ---- M5: dead-code ----
collect_M5() {
  echo "=== M5: dead-code ==="
  grep -c "TIMEOUT_SEC" skills/tests/validate-blackcow-ecosystem-health.sh 2>/dev/null && echo "M5_DEADCODE: STILL_PRESENT" || echo "M5_DEADCODE: CLEAN"
}

# ---- S1: dataFlow ----
collect_S1() {
  echo "=== S1: dataFlow ==="
  echo "JSON structure validation:"
  if [[ -f "${DIR}/${EVID}-s1-json-structure.txt" ]]; then
    cat "${DIR}/${EVID}-s1-json-structure.txt"
  fi
}

# ---- S2: auth ----
collect_S2() {
  echo "=== S2: auth ==="
  echo "S2: N/A (shell script, no auth surface)"
}

# ---- S3: injection ----
collect_S3() {
  echo "=== S3: injection ==="
  echo "S3 injection surface audit from: ${DIR}/${EVID}-s3-injection.txt"
}

# ---- P1: query ----
collect_P1() {
  echo "=== P1: query ==="
  echo "External process spawn count from: ${DIR}/${EVID}-p1-query.txt"
}

# ---- P2: memory ----
collect_P2() {
  echo "=== P2: memory ==="
  echo "Temp file leak check from: ${DIR}/${EVID}-p2-memory.txt"
}

# ---- P3: latency ----
collect_P3() {
  echo "=== P3: latency ==="
  echo "Runtime measurement from: ${DIR}/${EVID}-p3-latency.txt"
}

# ---- Run all ----
mkdir -p "$DIR"
for gate in M1 M2 M3 M4 M5 S1 S2 S3 P1 P2 P3; do
  echo ""
  "collect_${gate}"
done

echo ""
echo "=== SUMMARY ==="
echo "Evidence directory: ${DIR}/"
ls -la "${DIR}/${EVID}-"* 2>/dev/null || echo "(no evidence files yet)"
