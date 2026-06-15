#!/bin/sh
# Evidence collector for project-status-readme (FAST mode — M1, M2, M3 gates)
EVID=".omo/ulw-loop/evidence/project-status-readme"

echo "=== M1 Spec Match ==="
grep -c "Project Status" README.md > "$EVID-m1.txt" 2>&1
grep -c "88\.6" README.md >> "$EVID-m1.txt" 2>&1
grep -c "90" README.md >> "$EVID-m1.txt" 2>&1

echo "=== M2 Post-Edit Verification ==="
grep -A 5 "Project Status" README.md > "$EVID-m2.txt" 2>&1

echo "=== M3 Regression Baseline ==="
wc -l README.md > "$EVID-m3.txt" 2>&1
