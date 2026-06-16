#!/usr/bin/env bash
# BKIT 11-Gate Evidence Collector — sim-express-crud-patch
# After each gate, run: bash .omo/ulw-loop/collect-evidence.sh <gate> <status>
SLUG="sim-express-crud-patch"
EVDIR=".omo/ulw-loop/evidence"
mkdir -p "$EVDIR"

gate="${1:-M1}"
status="${2:-PENDING}"

case "$gate" in
  M1) echo "M1 spec-match: $status" > "$EVDIR/${SLUG}-m1-spec.txt" ;;
  M2) echo "M2 test-pass+coverage: $status" > "$EVDIR/${SLUG}-m2-test.txt" ;;
  M3) echo "M3 regression: $status" > "$EVDIR/${SLUG}-m3-regression.txt" ;;
  M4) echo "M4 lint: $status" > "$EVDIR/${SLUG}-m4-lint.txt" ;;
  M5) echo "M5 dead-code: $status" > "$EVDIR/${SLUG}-m5-deadcode.txt" ;;
  S1) echo "S1 dataFlow: $status" > "$EVDIR/${SLUG}-s1-dataflow.txt" ;;
  S2) echo "S2 auth: $status" > "$EVDIR/${SLUG}-s2-auth.txt" ;;
  S3) echo "S3 injection: $status" > "$EVDIR/${SLUG}-s3-injection.txt" ;;
  P1) echo "P1 query: $status" > "$EVDIR/${SLUG}-p1-query.txt" ;;
  P2) echo "P2 memory: $status" > "$EVDIR/${SLUG}-p2-memory.txt" ;;
  P3) echo "P3 latency: $status" > "$EVDIR/${SLUG}-p3-latency.txt" ;;
  *) echo "Unknown gate: $gate" ;;
esac
echo "Evidence: $EVDIR/${SLUG}-${gate}-*.txt → $status"
