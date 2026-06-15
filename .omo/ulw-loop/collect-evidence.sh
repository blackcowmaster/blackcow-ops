#!/usr/bin/env bash
# Evidence collector for install-path-security
# Gates: M1, M2, M3, M4, M5, S1, S3
set -euo pipefail

SLUG="install-path-security"
EVD=".omo/ulw-loop/evidence"

echo "=== BKIT 11-Gate Evidence Collector: ${SLUG} ==="

# M1 - spec-match
echo "--- M1 spec-match ---"
echo "M1: Plan requires: validate_install_path() blocks 6 vectors, resolve_path() 4-tier fallback, --install-path alias, both flags validated, mutual exclusion"
echo "STATUS: MANUAL_VERIFY"

# M2 - test-pass
echo "--- M2 test-pass ---"
TEST_FILE="skills/tests/test-l1-unit-install-security.sh"
if [[ -f "$TEST_FILE" ]]; then
  bash "$TEST_FILE" > "${EVD}/${SLUG}-m2-test.txt" 2>&1 && echo "M2: PASS" || echo "M2: FAIL"
else
  echo "M2: SKIP (test file not found)"
fi

# M3 - regression
echo "--- M3 regression ---"
echo "M3: Verify --target /tmp/test still works, default path still works"
bash skills/install.sh --dry-run --target /tmp/test 2>&1 | grep -q "Installed" && echo "M3a --target: PASS" || echo "M3a --target: FAIL"
bash skills/install.sh --dry-run 2>&1 | grep -q "Installed" && echo "M3b default: PASS" || echo "M3b default: FAIL"

# M4 - lint
echo "--- M4 lint ---"
# shellcheck if available
if command -v shellcheck &>/dev/null; then
  shellcheck skills/install.sh > "${EVD}/${SLUG}-m4-lint.txt" 2>&1 || true
  WARNINGS=$(grep -c "warning" "${EVD}/${SLUG}-m4-lint.txt" 2>/dev/null || echo "0")
  echo "M4: $WARNINGS warnings"
else
  echo "M4: SKIP (shellcheck not available)"
fi

# M5 - dead-code
echo "--- M5 dead-code ---"
echo "M5: All branches in validate_install_path() exercised by tests"
echo "STATUS: MANUAL_VERIFY (check test coverage)"

# S1 - dataFlow
echo "--- S1 dataFlow ---"
echo "S1: TARGET_DIR → validate_install_path() → mkdir -p → sed >"
echo "STATUS: MANUAL_VERIFY (trace data flow)"

# S3 - injection
echo "--- S3 injection ---"
echo "S3: 6 attack vectors blocked: .., //, null byte, symlink TOCTOU, absolute path, home-relative"
echo "STATUS: MANUAL_VERIFY (check test results)"

echo ""
echo "=== Collector done ==="
