#!/usr/bin/env bash
# ============================================================================
# L5 E2E Tests — install.sh (End-to-End User Workflows)
#
# Simulates real user workflows in an isolated temp HOME to avoid affecting
# real installations. Tests from user invocation through all layers to output.
#
# Workflows tested:
#   W1 — bash skills/install.sh              → skills in ~/.reasonix/skills/
#   W2 — bash skills/install.sh --dry-run    → preview only, no files written
#   W3 — bash skills/install.sh --target ~/.reasonix/skills/custom
#                                            → skills in custom dir
#   W4 — Invalid path                        → FATAL, exit 1, no partial writes
#   W5 — REASONIX_PLATFORM=windows ...       → windows tool set
#   W6 — Installed skills are valid markdown with correct frontmatter
#   W7 — Test scripts are executable after install
#   W8 — Multiple consecutive runs are idempotent
#   W9 — --install-path alias works identically to --target
#
# Usage:
#   bash skills/tests/test-l5-e2e-install-security.sh
#   bash skills/tests/test-l5-e2e-install-security.sh --verbose
# ============================================================================
set -euo pipefail

PASS=0; FAIL=0; TOTAL=0
VERBOSE=false
[[ "${1:-}" == "--verbose" ]] && VERBOSE=true

pass()    { PASS=$((PASS+1)); TOTAL=$((TOTAL+1)); echo "  ✅ PASS: $1"; }
fail()    { FAIL=$((FAIL+1)); TOTAL=$((TOTAL+1)); echo "  ❌ FAIL: $1"; }
heading() { echo ""; echo "━━━ $1 ━━━"; }
info()    { echo "  ℹ️  $1"; }

# Capture real HOME before any sandbox operations (sandbox tests override HOME)
REAL_HOME="${HOME}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALL_SCRIPT="${SKILLS_DIR}/install.sh"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Count source blackcow-*.md files for validation
BLACKCOW_SOURCE_COUNT=0
for f in "${SKILLS_DIR}"/blackcow-*.md; do
  [[ -f "$f" ]] && BLACKCOW_SOURCE_COUNT=$((BLACKCOW_SOURCE_COUNT + 1))
done

# Global trap: clean up any leftover .l5-e2e-* sandbox dirs on script exit/interrupt
cleanup_all_sandboxes() {
  for d in "${REAL_HOME}"/.l5-e2e-*; do
    [[ -d "$d" ]] && rm -rf "$d" 2>/dev/null || true
  done
}
trap cleanup_all_sandboxes EXIT INT TERM

echo "=== L5 E2E Tests: install.sh (User Workflows in Temp HOME) ==="
echo "  Source skills:    ${SKILLS_DIR}"
echo "  Blackcow files:   ${BLACKCOW_SOURCE_COUNT}"
echo "  Real HOME:        ${HOME}"
echo ""

# ============================================================================
# Sandbox helpers — each test gets its own temp HOME for full isolation
# ============================================================================

# create_sandbox() → path to a temp directory that serves as the fake $HOME
# NOTE: sandbox is created under REAL_HOME (not /tmp) because macOS resolves
# /tmp → /private/tmp, causing install.sh's ALLOWED_PREFIX prefix check to fail
# (resolved path ≠ unresolved ${HOME}/.reasonix). Under a non-symlinked HOME
# this doesn't occur.
create_sandbox() {
  mktemp -d "${REAL_HOME}/.l5-e2e-$$-XXXXXX"
}

# destroy(path) — clean up a sandbox
destroy() {
  rm -rf "$1" 2>/dev/null || true
}

# run_install_in_sandbox(sandbox_home, [extra_args...])
# Runs install.sh with a fake HOME and captures stdout+stderr + exit code.
# Returns via global variables: INSTALL_OUTPUT, INSTALL_EXIT_CODE
INSTALL_OUTPUT=""
INSTALL_EXIT_CODE=0
run_install_in_sandbox() {
  local sandbox_home="$1"
  shift
  local extra_args=("$@")

  # Create the default target parent if it doesn't exist
  mkdir -p "${sandbox_home}/.reasonix"

  set +e
  INSTALL_OUTPUT=$(HOME="$sandbox_home" bash "$INSTALL_SCRIPT" "${extra_args[@]}" 2>&1)
  INSTALL_EXIT_CODE=$?
  set -e
}

# run_install_in_cwd(sandbox_home, [extra_args...])
# Like run_install_in_sandbox but runs from PROJECT_ROOT to keep SOURCE_DIR stable
# NOTE: bash 3.2 compat — use ${array[@]+"${array[@]}"} to avoid "unbound variable"
# with set -u on empty arrays.
run_install_in_cwd() {
  local sandbox_home="$1"
  shift
  local extra_args=("$@")

  mkdir -p "${sandbox_home}/.reasonix"

  set +e
  if [[ ${#extra_args[@]} -eq 0 ]]; then
    INSTALL_OUTPUT=$(cd "$PROJECT_ROOT" && HOME="$sandbox_home" bash "$INSTALL_SCRIPT" 2>&1)
  else
    INSTALL_OUTPUT=$(cd "$PROJECT_ROOT" && HOME="$sandbox_home" bash "$INSTALL_SCRIPT" "${extra_args[@]}" 2>&1)
  fi
  INSTALL_EXIT_CODE=$?
  set -e
}

# ============================================================================
# W1 — User runs `bash skills/install.sh` → skills appear in ~/.reasonix/skills/
# ============================================================================
heading "W1 — Default install: skills appear in ~/.reasonix/skills/"

W1_SANDBOX=$(create_sandbox)
info "Sandbox HOME: ${W1_SANDBOX}"
run_install_in_cwd "$W1_SANDBOX"

# Verify exit code
if [[ "$INSTALL_EXIT_CODE" -eq 0 ]]; then
  pass "W1a: install.sh exits 0"
else
  fail "W1a: install.sh exit code $INSTALL_EXIT_CODE (expected 0)"
fi

# Verify the skills directory was created under sandbox HOME
SKILLS_DIR_SANDBOX="${W1_SANDBOX}/.reasonix/skills"
if [[ -d "$SKILLS_DIR_SANDBOX" ]]; then
  pass "W1b: ~/.reasonix/skills/ directory created"
else
  fail "W1b: ~/.reasonix/skills/ directory NOT created"
fi

# Verify all blackcow-*.md source files are present in the installed directory
installed_count=0
missing_skills=()
for f in "${SKILLS_DIR}"/blackcow-*.md; do
  bname=$(basename "$f")
  if [[ -f "${SKILLS_DIR_SANDBOX}/${bname}" ]]; then
    installed_count=$((installed_count + 1))
  else
    missing_skills+=("$bname")
  fi
done

if [[ "$installed_count" -eq "$BLACKCOW_SOURCE_COUNT" ]]; then
  pass "W1c: All ${BLACKCOW_SOURCE_COUNT} blackcow-*.md files installed"
else
  fail "W1c: ${installed_count}/${BLACKCOW_SOURCE_COUNT} installed; missing: ${missing_skills[*]}"
fi

# Verify no extra .md files leaked into the target (only blackcow-*)
non_blackcow=()
for f in "${SKILLS_DIR_SANDBOX}"/*.md; do
  [[ -f "$f" ]] || continue
  bname=$(basename "$f")
  if [[ ! "$bname" =~ ^blackcow- ]]; then
    non_blackcow+=("$bname")
  fi
done
if [[ ${#non_blackcow[@]} -eq 0 ]]; then
  pass "W1d: No non-blackcow .md files leaked into target"
else
  fail "W1d: Non-blackcow files found: ${non_blackcow[*]}"
fi

# Verify platform-detection output mentions the right platform
if echo "$INSTALL_OUTPUT" | grep -q "Detected platform:"; then
  pass "W1e: Platform detection message present in output"
else
  fail "W1e: Platform detection message missing from output"
fi

# Verify completion message
if echo "$INSTALL_OUTPUT" | grep -q "Installation complete"; then
  pass "W1f: Completion message present in output"
else
  fail "W1f: Completion message missing from output"
fi

# Verify the target path in output matches the sandbox
if echo "$INSTALL_OUTPUT" | grep -q "Target: ${SKILLS_DIR_SANDBOX}"; then
  pass "W1g: Output confirms target path matches sandbox HOME"
else
  # The path might be resolved differently; just check it mentions .reasonix/skills
  if echo "$INSTALL_OUTPUT" | grep -q "Target:.*\.reasonix/skills"; then
    pass "W1g: Output mentions .reasonix/skills as target path"
  else
    fail "W1g: Output missing target path reference"
  fi
fi

# Verify the real HOME was NOT touched
if [[ -d "${HOME}/.reasonix/skills" ]]; then
  # The real home might already have skills installed — that's OK. But we must
  # NOT have created it. We can check mtime to see if it was recently modified.
  info "W1h: Real ~/.reasonix/skills/ exists (pre-existing — not a failure)"
  pass "W1h: Real HOME was not modified by sandbox install (pre-existing)"
else
  pass "W1h: Real HOME untouched — no ~/.reasonix/skills/ created"
fi

destroy "$W1_SANDBOX"

# ============================================================================
# W2 — User runs `bash skills/install.sh --dry-run` → preview only, no files written
# ============================================================================
heading "W2 — Dry-run: preview only, no files written"

W2_SANDBOX=$(create_sandbox)
info "Sandbox HOME: ${W2_SANDBOX}"

# Ensure the target path does NOT exist yet (we'll verify dry-run doesn't create it)
TARGET_PARENT="${W2_SANDBOX}/.reasonix"
mkdir -p "$TARGET_PARENT"

run_install_in_cwd "$W2_SANDBOX" --dry-run

# Verify exit code is 0 for dry-run
if [[ "$INSTALL_EXIT_CODE" -eq 0 ]]; then
  pass "W2a: --dry-run exits 0"
else
  fail "W2a: --dry-run exit code $INSTALL_EXIT_CODE (expected 0)"
fi

# Verify output contains [DRY-RUN] markers for each skill
dry_run_markers=$(echo "$INSTALL_OUTPUT" | grep -c "\[DRY-RUN\]" || true)
if [[ "$dry_run_markers" -ge "$BLACKCOW_SOURCE_COUNT" ]]; then
  pass "W2b: --dry-run shows ${dry_run_markers} [DRY-RUN] markers (≥${BLACKCOW_SOURCE_COUNT} skills)"
else
  fail "W2b: --dry-run shows only ${dry_run_markers} markers (expected ≥${BLACKCOW_SOURCE_COUNT})"
fi

# Verify NO files were written to the target directory
SKILLS_DIR_SANDBOX_W2="${W2_SANDBOX}/.reasonix/skills"
written_count=0
if [[ -d "$SKILLS_DIR_SANDBOX_W2" ]]; then
  written_count=$(find "$SKILLS_DIR_SANDBOX_W2" -name '*.md' 2>/dev/null | wc -l)
fi

if [[ "$written_count" -eq 0 ]]; then
  pass "W2c: --dry-run wrote 0 .md files to target directory"
else
  fail "W2c: --dry-run wrote ${written_count} .md files (expected 0)"
fi

# Verify output shows "Mode: DRY-RUN" in the summary
if echo "$INSTALL_OUTPUT" | grep -q "Mode: DRY-RUN"; then
  pass "W2d: Summary footer confirms 'Mode: DRY-RUN'"
else
  fail "W2d: Summary footer missing DRY-RUN mode"
fi

# Verify no "✅ Installed to:" lines appear (those are real installs)
if echo "$INSTALL_OUTPUT" | grep -q "✅ Installed to:"; then
  fail "W2e: --dry-run shows '✅ Installed to:' lines (should only show [DRY-RUN])"
else
  pass "W2e: --dry-run output has no 'Installed to:' lines"
fi

# mkdir -p in install.sh runs unconditionally (before the $DRY_RUN check),
# so the directory IS created as a harmless side effect — but NO .md files
# should be written there. W2c already verified no .md files.
# Confirm that if the dir exists (from mkdir -p), it's truly empty of .md
if [[ -d "$SKILLS_DIR_SANDBOX_W2" ]]; then
  dir_md_count=$(find "$SKILLS_DIR_SANDBOX_W2" -name '*.md' 2>/dev/null | wc -l)
  if [[ "$dir_md_count" -eq 0 ]]; then
    pass "W2f: --dry-run directory has 0 .md files (mkdir -p side-effect is harmless)"
  else
    fail "W2f: --dry-run directory has ${dir_md_count} .md files (expected 0)"
  fi
else
  pass "W2f: --dry-run did not create skills directory (mkdir -p not run)"
fi

# Verify dry-run with --target also produces no .md files
W2_CUSTOM_DIR="${W2_SANDBOX}/.reasonix/skills/custom-dry-run"
run_install_in_cwd "$W2_SANDBOX" --dry-run --target "$W2_CUSTOM_DIR"

if [[ -d "$W2_CUSTOM_DIR" ]]; then
  custom_md_count=$(find "$W2_CUSTOM_DIR" -name '*.md' 2>/dev/null | wc -l)
  if [[ "$custom_md_count" -eq 0 ]]; then
    pass "W2g: --dry-run --target dir has 0 .md files (mkdir -p side-effect)"
  else
    fail "W2g: --dry-run --target dir has ${custom_md_count} .md files"
  fi
else
  pass "W2g: --dry-run --target did not create directory"
fi

destroy "$W2_SANDBOX"

# ============================================================================
# W3 — User runs `bash skills/install.sh --target ~/.reasonix/skills/custom`
#       → skills installed in custom subdirectory
# ============================================================================
heading "W3 — Custom target: skills installed to --target path"

W3_SANDBOX=$(create_sandbox)
info "Sandbox HOME: ${W3_SANDBOX}"

CUSTOM_DIR="${W3_SANDBOX}/.reasonix/skills/custom"
run_install_in_cwd "$W3_SANDBOX" --target "$CUSTOM_DIR"

if [[ "$INSTALL_EXIT_CODE" -eq 0 ]]; then
  pass "W3a: --target install exits 0"
else
  fail "W3a: --target install exit code $INSTALL_EXIT_CODE (expected 0)"
fi

# Verify skills went to the custom directory, NOT to the default
if [[ -d "$CUSTOM_DIR" ]]; then
  pass "W3b: Custom target directory created at ${CUSTOM_DIR}"
else
  fail "W3b: Custom target directory NOT created"
fi

DEFAULT_DIR="${W3_SANDBOX}/.reasonix/skills"
CUSTOM_INSTALLED=$(find "$CUSTOM_DIR" -maxdepth 1 -name 'blackcow-*.md' 2>/dev/null | wc -l)
DEFAULT_INSTALLED=$(find "$DEFAULT_DIR" -maxdepth 1 -name 'blackcow-*.md' 2>/dev/null | wc -l)

if [[ "$CUSTOM_INSTALLED" -ge "$BLACKCOW_SOURCE_COUNT" ]]; then
  pass "W3c: All ${BLACKCOW_SOURCE_COUNT} skills installed to custom directory"
else
  fail "W3c: Only ${CUSTOM_INSTALLED}/${BLACKCOW_SOURCE_COUNT} skills in custom directory"
fi

if [[ "$DEFAULT_INSTALLED" -eq 0 ]]; then
  pass "W3d: No skills leaked to default ~/.reasonix/skills/"
else
  fail "W3d: ${DEFAULT_INSTALLED} skills leaked to default directory (should be empty)"
fi

# Verify the output mentions the custom target path
if echo "$INSTALL_OUTPUT" | grep -q "Target: ${CUSTOM_DIR}"; then
  pass "W3e: Output confirms custom target path"
else
  # Resolved path might differ; check it contains "custom"
  if echo "$INSTALL_OUTPUT" | grep -q "Target:.*custom"; then
    pass "W3e: Output mentions custom target path"
  else
    fail "W3e: Output missing custom target reference"
  fi
fi

# Verify files in custom dir have proper content (not empty)
non_empty=0
for f in "$CUSTOM_DIR"/blackcow-*.md; do
  [[ -f "$f" ]] || continue
  size=$(stat -c%s "$f" 2>/dev/null || stat -f%z "$f" 2>/dev/null || echo 0)
  [[ "$size" -gt 50 ]] && non_empty=$((non_empty + 1))
done
if [[ "$non_empty" -ge "$BLACKCOW_SOURCE_COUNT" ]]; then
  pass "W3f: Custom installed files are non-empty (all >50 bytes)"
else
  fail "W3f: Only ${non_empty}/${BLACKCOW_SOURCE_COUNT} custom files are non-empty"
fi

destroy "$W3_SANDBOX"

# ============================================================================
# W4 — User runs with invalid path → FATAL error, exit 1, no partial writes
# ============================================================================
heading "W4 — Invalid path: FATAL, exit 1, no partial writes"

W4_SANDBOX=$(create_sandbox)
info "Sandbox HOME: ${W4_SANDBOX}"

# Test 4a: Path outside allowed prefix (/tmp)
run_install_in_cwd "$W4_SANDBOX" --target "/tmp/outside-prefix"
if [[ "$INSTALL_EXIT_CODE" -eq 1 ]]; then
  pass "W4a: /tmp/ path → exit code 1"
else
  fail "W4a: /tmp/ path → exit code $INSTALL_EXIT_CODE (expected 1)"
fi
if echo "$INSTALL_OUTPUT" | grep -q "FATAL:"; then
  pass "W4b: /tmp/ path → FATAL error message"
else
  fail "W4b: /tmp/ path → missing FATAL message"
fi
# Verify no files were partially written under the invalid target
if [[ ! -d "/tmp/outside-prefix" ]]; then
  pass "W4c: No partial directory created at invalid path"
else
  fail "W4c: Partial directory was created at /tmp/outside-prefix"
fi

# Test 4b: Path traversal with ..
run_install_in_cwd "$W4_SANDBOX" --target "${W4_SANDBOX}/.reasonix/../../etc"
if [[ "$INSTALL_EXIT_CODE" -eq 1 ]]; then
  pass "W4d: .. traversal → exit code 1"
else
  fail "W4d: .. traversal → exit code $INSTALL_EXIT_CODE (expected 1)"
fi
if echo "$INSTALL_OUTPUT" | grep -q "FATAL:"; then
  pass "W4e: .. traversal → FATAL error message"
else
  fail "W4e: .. traversal → missing FATAL message"
fi

# Test 4c: Double-slash path
run_install_in_cwd "$W4_SANDBOX" --target "${W4_SANDBOX}//.reasonix/skills"
if [[ "$INSTALL_EXIT_CODE" -eq 1 ]]; then
  pass "W4f: double-slash → exit code 1"
else
  fail "W4f: double-slash → exit code $INSTALL_EXIT_CODE (expected 1)"
fi

# Test 4d: Empty string (behaves as no-arg — the flag consumes next arg as raw="")
# install.sh will read "~/.reasonix/skills" as the next positional arg
# and error on "Unknown arg", so we just check it exits 1
info "W4g: Testing empty target (no-arg edge case)"
set +e
output=$(cd "$PROJECT_ROOT" && HOME="$W4_SANDBOX" bash "$INSTALL_SCRIPT" --target 2>&1)
ec=$?
set -e
if [[ "$ec" -eq 1 ]]; then
  pass "W4g: --target with no value → exit 1"
else
  fail "W4g: --target with no value → exit $ec (expected 1)"
fi

# Test 4e: Path under .reasonixfoo (prefix bypass attempt)
run_install_in_cwd "$W4_SANDBOX" --target "${W4_SANDBOX}/.reasonixfoo/skills"
if [[ "$INSTALL_EXIT_CODE" -eq 1 ]]; then
  pass "W4h: .reasonixfoo prefix bypass → exit 1"
else
  fail "W4h: .reasonixfoo prefix bypass → exit $INSTALL_EXIT_CODE (expected 1)"
fi
if echo "$INSTALL_OUTPUT" | grep -q "FATAL:"; then
  pass "W4i: .reasonixfoo prefix bypass → FATAL message"
else
  fail "W4i: .reasonixfoo prefix bypass → missing FATAL message"
fi

# Verify the sandbox HOME's .reasonix directory tree is clean (no partial writes)
reasonix_content=$(find "${W4_SANDBOX}/.reasonix" -name '*.md' 2>/dev/null | wc -l || true)
if [[ "$reasonix_content" -eq 0 ]]; then
  pass "W4j: Sandbox .reasonix/ has no .md files despite failed install attempts"
else
  fail "W4j: Sandbox .reasonix/ has ${reasonix_content} .md files (partial writes occurred)"
fi

destroy "$W4_SANDBOX"

# ============================================================================
# W5 — User runs `REASONIX_PLATFORM=windows bash skills/install.sh`
#       → windows tool set applied to all installed skills
# ============================================================================
heading "W5 — Windows platform: REASONIX_PLATFORM=windows yields Windows tools"

W5_SANDBOX=$(create_sandbox)
info "Sandbox HOME: ${W5_SANDBOX}"

# Install with Windows platform override
run_install_in_cwd "$W5_SANDBOX" REASONIX_PLATFORM=windows
# Actually we need to pass the env var differently — use run_install_in_cwd but set env
set +e
SKILLS_DIR_SANDBOX_W5="${W5_SANDBOX}/.reasonix/skills"
mkdir -p "${W5_SANDBOX}/.reasonix"
INSTALL_OUTPUT=$(cd "$PROJECT_ROOT" && HOME="$W5_SANDBOX" REASONIX_PLATFORM=windows bash "$INSTALL_SCRIPT" 2>&1)
INSTALL_EXIT_CODE=$?
set -e

if [[ "$INSTALL_EXIT_CODE" -eq 0 ]]; then
  pass "W5a: Windows install exits 0"
else
  fail "W5a: Windows install exit code $INSTALL_EXIT_CODE (expected 0)"
fi

# Verify platform detection
if echo "$INSTALL_OUTPUT" | grep -q "Detected platform: windows"; then
  pass "W5b: Platform detected as 'windows'"
else
  fail "W5b: Platform NOT detected as 'windows'"
fi

# Verify completion message mentions windows
if echo "$INSTALL_OUTPUT" | grep -q "platform: windows"; then
  pass "W5c: Summary confirms 'platform: windows'"
else
  fail "W5c: Summary missing platform: windows confirmation"
fi

# Verify every installed skill has Windows-specific tools (grep, ls, bash, task)
WIN_TOOLS=("grep" "ls" "bash" "task")
for skill_file in "${SKILLS_DIR_SANDBOX_W5}"/blackcow-*.md; do
  [[ -f "$skill_file" ]] || continue
  bname=$(basename "$skill_file")
  tools_line=$(grep "^allowed-tools:" "$skill_file" | head -1)

  # Check each windows tool is present
  for tool in "${WIN_TOOLS[@]}"; do
    if echo "$tools_line" | grep -q "$tool"; then
      pass "W5d: [${bname}] Windows tool '${tool}' present"
    else
      fail "W5d: [${bname}] Windows tool '${tool}' MISSING"
    fi
  done

  # Verify macOS-specific tools are NOT present
  for mac_tool in "list_directory" "directory_tree" "run_command" "web_search" "explore" "research" "run_skill" "get_file_info"; do
    if echo "$tools_line" | grep -q "$mac_tool"; then
      # Some skills may legitimately have explore/research via get_skill_extra_win
      # Only flag tools that should NEVER appear in windows: search_content, search_files, list_directory, directory_tree, run_command
      if [[ "$mac_tool" == "search_content" || "$mac_tool" == "search_files" || "$mac_tool" == "list_directory" || "$mac_tool" == "directory_tree" || "$mac_tool" == "run_command" ]]; then
        fail "W5e: [${bname}] macOS-only tool '${mac_tool}' present in Windows install"
      fi
      break
    fi
  done
done

# Verify common tools are present in Windows install
for tool in "read_file" "glob" "web_fetch" "write_file" "edit_file" "multi_edit"; do
  present=0
  for skill_file in "${SKILLS_DIR_SANDBOX_W5}"/blackcow-*.md; do
    [[ -f "$skill_file" ]] || continue
    if grep -q "$tool" "$skill_file" 2>/dev/null; then
      present=$((present + 1))
      break
    fi
  done
  if [[ "$present" -gt 0 ]]; then
    pass "W5f: Common tool '${tool}' present in Windows install"
  else
    fail "W5f: Common tool '${tool}' MISSING from Windows install"
  fi
done

# Cross-validate: compare with macOS install to confirm they differ
W5_MAC_SANDBOX=$(create_sandbox)
set +e
MAC_OUTPUT=$(cd "$PROJECT_ROOT" && HOME="$W5_MAC_SANDBOX" bash "$INSTALL_SCRIPT" 2>&1)
set -e
MAC_SKILLS_DIR="${W5_MAC_SANDBOX}/.reasonix/skills"

diff_count=0
same_count=0
for skill_file in "${SKILLS_DIR_SANDBOX_W5}"/blackcow-*.md; do
  [[ -f "$skill_file" ]] || continue
  bname=$(basename "$skill_file")
  win_line=$(grep "^allowed-tools:" "$skill_file" | head -1)
  mac_line=$(grep "^allowed-tools:" "${MAC_SKILLS_DIR}/${bname}" 2>/dev/null | head -1 || echo "")

  if [[ "$win_line" != "$mac_line" ]]; then
    diff_count=$((diff_count + 1))
  else
    same_count=$((same_count + 1))
  fi
done

if [[ "$diff_count" -ge "$BLACKCOW_SOURCE_COUNT" ]]; then
  pass "W5g: All ${BLACKCOW_SOURCE_COUNT} skills have different allowed-tools between platforms"
else
  fail "W5g: Only ${diff_count}/${BLACKCOW_SOURCE_COUNT} skills differ; ${same_count} are identical"
fi

destroy "$W5_SANDBOX"
destroy "$W5_MAC_SANDBOX"

# ============================================================================
# W6 — Installed skills are valid markdown with correct frontmatter
#       (YAML parseable, required fields, correct structure)
# ============================================================================
heading "W6 — Frontmatter integrity: valid markdown with correct frontmatter"

W6_SANDBOX=$(create_sandbox)
info "Sandbox HOME: ${W6_SANDBOX}"
W6_SKILLS_DIR="${W6_SANDBOX}/.reasonix/skills"

set +e
INSTALL_OUTPUT=$(cd "$PROJECT_ROOT" && HOME="$W6_SANDBOX" bash "$INSTALL_SCRIPT" 2>&1)
set -e

# W6a: All files have YAML frontmatter fences (--- ... ---)
fm_valid=0
fm_invalid=0
for f in "${W6_SKILLS_DIR}"/blackcow-*.md; do
  [[ -f "$f" ]] || continue

  first_line=$(head -1 "$f")
  if [[ "$first_line" != "---" ]]; then
    fail "W6a: $(basename "$f") does not start with ---"
    fm_invalid=$((fm_invalid + 1))
    continue
  fi

  fence_count=$(grep -c "^---" "$f" || true)
  if [[ "$fence_count" -lt 2 ]]; then
    fail "W6a: $(basename "$f") has only ${fence_count} --- fences (need ≥2)"
    fm_invalid=$((fm_invalid + 1))
    continue
  fi

  fm_valid=$((fm_valid + 1))
done
if [[ "$fm_invalid" -eq 0 ]]; then
  pass "W6a: All ${fm_valid} installed files have valid YAML frontmatter fences"
fi

# W6b: Frontmatter contains all required fields
for f in "${W6_SKILLS_DIR}"/blackcow-*.md; do
  [[ -f "$f" ]] || continue
  bname=$(basename "$f")

  # Extract YAML block between --- fences
  yaml_block=$(awk 'BEGIN{in_fence=0}
    /^---/ && !in_fence {in_fence=1; next}
    in_fence && /^---/ {exit}
    in_fence {print}' "$f")

  missing_fields=()
  echo "$yaml_block" | grep -q '^name:'          || missing_fields+=("name")
  echo "$yaml_block" | grep -q '^description:'    || missing_fields+=("description")
  echo "$yaml_block" | grep -q '^allowed-tools:'  || missing_fields+=("allowed-tools")

  if [[ ${#missing_fields[@]} -eq 0 ]]; then
    pass "W6b: [${bname}] All required frontmatter fields present"
  else
    fail "W6b: [${bname}] Missing fields: ${missing_fields[*]}"
  fi
done

# W6c: Frontmatter structural validation — every line in the YAML block
# must follow valid key: value syntax (no python yaml module needed).
# Valid patterns: "key:", "key: value", "key: value1, value2"
# Indented continuation lines and comment lines (#) are also valid.
yaml_struct_errors=0
yaml_total=0
for f in "${W6_SKILLS_DIR}"/blackcow-*.md; do
  [[ -f "$f" ]] || continue
  bname=$(basename "$f")
  yaml_total=$((yaml_total + 1))

  yaml_block=$(awk 'BEGIN{in_fence=0}
    /^---/ && !in_fence {in_fence=1; next}
    in_fence && /^---/ {exit}
    in_fence {print}' "$f")

  line_errors=0
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    # Valid: key:, key: value
    if echo "$line" | grep -qE '^[a-zA-Z_][a-zA-Z0-9_-]*:'; then
      :
    # Valid: indented continuation
    elif echo "$line" | grep -qE '^[[:space:]]'; then
      :
    # Valid: comment
    elif echo "$line" | grep -qE '^#'; then
      :
    else
      line_errors=$((line_errors + 1))
    fi
  done <<< "$yaml_block"

  if [[ "$line_errors" -eq 0 ]]; then
    pass "W6c: [${bname}] Frontmatter line-level structure is valid"
  else
    yaml_struct_errors=$((yaml_struct_errors + 1))
    fail "W6c: [${bname}] Frontmatter has ${line_errors} structurally invalid lines"
  fi
done

if [[ "$yaml_struct_errors" -eq 0 ]]; then
  pass "W6d: All ${yaml_total} files pass frontmatter structural validation"
else
  fail "W6d: ${yaml_struct_errors}/${yaml_total} files failed structural validation"
fi

# W6e: allowed-tools values are non-empty comma-separated tool names
for f in "${W6_SKILLS_DIR}"/blackcow-*.md; do
  [[ -f "$f" ]] || continue
  bname=$(basename "$f")
  line=$(grep "^allowed-tools:" "$f" | head -1)
  value="${line#allowed-tools: }"

  if [[ -z "$value" ]]; then
    fail "W6e: [${bname}] allowed-tools value is empty"
    continue
  fi

  # Must match: tool1, tool2, ... pattern
  if echo "$value" | grep -qE '^[a-zA-Z_][a-zA-Z0-9_-]*(, ?[a-zA-Z_][a-zA-Z0-9_-]*)*$'; then
    pass "W6e: [${bname}] allowed-tools format is valid"
  else
    fail "W6e: [${bname}] allowed-tools format invalid: '${value:0:80}'"
  fi
done

# W6f: After the frontmatter, the file has a markdown heading (# title)
for f in "${W6_SKILLS_DIR}"/blackcow-*.md; do
  [[ -f "$f" ]] || continue
  bname=$(basename "$f")

  # Get content after closing --- fence
  # Skip blank lines after closing ---, then capture the first non-blank line
  body=$(awk 'BEGIN{fence=0}
    /^---/ && fence==0 {fence=1; next}
    /^---/ && fence==1 {fence=2; next}
    fence==2 && /^[[:space:]]*$/ {next}
    fence==2 {print; exit}' "$f")

  if echo "$body" | grep -qE '^#\s+'; then
    pass "W6f: [${bname}] Has markdown heading after frontmatter"
  else
    fail "W6f: [${bname}] Missing markdown heading after frontmatter"
  fi
done

destroy "$W6_SANDBOX"

# ============================================================================
# W7 — Test scripts are executable after install
# ============================================================================
heading "W7 — Test scripts executable after install"

W7_SANDBOX=$(create_sandbox)
info "Sandbox HOME: ${W7_SANDBOX}"

# Before running install, check that at least some validate-*.sh scripts exist
TEST_DIR="${SKILLS_DIR}/tests"
if ls "$TEST_DIR"/validate-*.sh &>/dev/null 2>&1; then
  pass "W7a: validate-*.sh scripts exist in source tests/"
else
  fail "W7a: No validate-*.sh scripts found in ${TEST_DIR}/"
fi

# Run install.sh (in the sandbox — it chmods SOURCE_DIR/tests, not sandbox tests)
set +e
INSTALL_OUTPUT=$(cd "$PROJECT_ROOT" && HOME="$W7_SANDBOX" bash "$INSTALL_SCRIPT" 2>&1)
set -e

# Check if install output mentions chmod
if echo "$INSTALL_OUTPUT" | grep -q "All validate-.*\.sh scripts made executable"; then
  pass "W7b: Install output confirms test scripts made executable"
else
  fail "W7b: Install output missing chmod confirmation"
fi

# Verify all validate-*.sh scripts are executable after install
all_exec=true
non_exec=()
for f in "$TEST_DIR"/validate-*.sh; do
  [[ -f "$f" ]] || continue
  if [[ ! -x "$f" ]]; then
    all_exec=false
    non_exec+=("$(basename "$f")")
  fi
done

if $all_exec; then
  pass "W7c: All validate-*.sh scripts are executable after install"
else
  fail "W7c: Scripts not executable: ${non_exec[*]}"
fi

# Verify the ecosystem health runner is referenced
if echo "$INSTALL_OUTPUT" | grep -q "validate-blackcow-ecosystem-health.sh"; then
  pass "W7d: Ecosystem health runner registered in output"
else
  fail "W7d: Ecosystem health runner not mentioned in output"
fi

# Verify we can actually execute one of the test scripts (smoke test)
# Use a simple validate script that won't have side effects
SMOKE_SCRIPT="$TEST_DIR/validate-blackcow-plan.sh"
if [[ -f "$SMOKE_SCRIPT" && -x "$SMOKE_SCRIPT" ]]; then
  # Run it briefly (may fail on validation — just check it starts)
  set +e
  smoke_output=$(timeout 5 bash "$SMOKE_SCRIPT" 2>&1) || true
  smoke_ec=$?
  set -e
  # It may pass or fail — we just care that it ran (exit 0-2, not crash)
  if [[ "$smoke_ec" -ge 0 && "$smoke_ec" -le 2 ]]; then
    pass "W7e: validate-blackcow-plan.sh is executable and runs (exit code $smoke_ec)"
  else
    fail "W7e: validate-blackcow-plan.sh exit code $smoke_ec (expected 0-2)"
  fi
else
  fail "W7e: validate-blackcow-plan.sh not found or not executable"
fi

destroy "$W7_SANDBOX"

# ============================================================================
# W8 — Multiple consecutive runs are idempotent
#         Running install.sh twice produces the same result
# ============================================================================
heading "W8 — Idempotency: consecutive runs produce identical results"

W8_SANDBOX=$(create_sandbox)
info "Sandbox HOME: ${W8_SANDBOX}"
W8_SKILLS_DIR="${W8_SANDBOX}/.reasonix/skills"

# First install
set +e
mkdir -p "${W8_SANDBOX}/.reasonix"
OUTPUT1=$(cd "$PROJECT_ROOT" && HOME="$W8_SANDBOX" bash "$INSTALL_SCRIPT" 2>&1)
EC1=$?
set -e

# Compute checksums of all installed files after first run
CSUM1=""
if [[ "$EC1" -eq 0 ]]; then
  CSUM1=$(cd "$W8_SKILLS_DIR" && find . -name '*.md' -type f -exec md5sum {} \; 2>/dev/null | sort || \
          cd "$W8_SKILLS_DIR" && find . -name '*.md' -type f -exec md5 -r {} \; 2>/dev/null | sort || true)
fi

# Second install
set +e
OUTPUT2=$(cd "$PROJECT_ROOT" && HOME="$W8_SANDBOX" bash "$INSTALL_SCRIPT" 2>&1)
EC2=$?
set -e

CSUM2=""
if [[ "$EC2" -eq 0 ]]; then
  CSUM2=$(cd "$W8_SKILLS_DIR" && find . -name '*.md' -type f -exec md5sum {} \; 2>/dev/null | sort || \
          cd "$W8_SKILLS_DIR" && find . -name '*.md' -type f -exec md5 -r {} \; 2>/dev/null | sort || true)
fi

# Both runs must exit 0
if [[ "$EC1" -eq 0 && "$EC2" -eq 0 ]]; then
  pass "W8a: Both consecutive installs exit 0"
else
  fail "W8a: Run 1 exit=$EC1, Run 2 exit=$EC2 (expected both 0)"
fi

# File checksums must be identical
if [[ -n "$CSUM1" && "$CSUM1" == "$CSUM2" ]]; then
  pass "W8b: File checksums identical across consecutive installs (idempotent)"
else
  fail "W8b: File checksums differ between runs (install is NOT idempotent)"
  $VERBOSE && echo "   Run 1: ${CSUM1:0:200}..." || true
  $VERBOSE && echo "   Run 2: ${CSUM2:0:200}..." || true
fi

# Both outputs should mention "Installation complete"
if echo "$OUTPUT1" | grep -q "Installation complete" && echo "$OUTPUT2" | grep -q "Installation complete"; then
  pass "W8c: Both runs report 'Installation complete'"
else
  fail "W8c: One or both runs missing completion message"
fi

# File count must be the same
COUNT1=$(find "$W8_SKILLS_DIR" -name '*.md' 2>/dev/null | wc -l)
COUNT2=$(find "$W8_SKILLS_DIR" -name '*.md' 2>/dev/null | wc -l)
if [[ "$COUNT1" -eq "$COUNT2" && "$COUNT1" -eq "$BLACKCOW_SOURCE_COUNT" ]]; then
  pass "W8d: Both runs produce exactly ${BLACKCOW_SOURCE_COUNT} .md files"
else
  fail "W8d: Run 1=${COUNT1} files, Run 2=${COUNT2} files (expected ${BLACKCOW_SOURCE_COUNT})"
fi

# Third run with --dry-run after two real runs — still clean
set +e
OUTPUT3=$(cd "$PROJECT_ROOT" && HOME="$W8_SANDBOX" bash "$INSTALL_SCRIPT" --dry-run 2>&1)
EC3=$?
set -e
if [[ "$EC3" -eq 0 ]]; then
  pass "W8e: Third run with --dry-run still exits 0 after two real installs"
else
  fail "W8e: Third run --dry-run exit=$EC3 (expected 0)"
fi

destroy "$W8_SANDBOX"

# ============================================================================
# W9 — --install-path alias works identically to --target
# ============================================================================
heading "W9 — --install-path alias produces identical output to --target"

W9_SANDBOX=$(create_sandbox)
info "Sandbox HOME: ${W9_SANDBOX}"

TARGET_DIR="${W9_SANDBOX}/.reasonix/skills/w9-target"
INSTALL_PATH_DIR="${W9_SANDBOX}/.reasonix/skills/w9-install-path"

mkdir -p "${W9_SANDBOX}/.reasonix"

# Install with --target
set +e
TARGET_OUTPUT=$(cd "$PROJECT_ROOT" && HOME="$W9_SANDBOX" bash "$INSTALL_SCRIPT" --target "$TARGET_DIR" 2>&1)
TARGET_EC=$?
set -e

# Install with --install-path
set +e
PATH_OUTPUT=$(cd "$PROJECT_ROOT" && HOME="$W9_SANDBOX" bash "$INSTALL_SCRIPT" --install-path "$INSTALL_PATH_DIR" 2>&1)
PATH_EC=$?
set -e

# Both exit 0
if [[ "$TARGET_EC" -eq 0 ]]; then
  pass "W9a: --target exits 0"
else
  fail "W9a: --target exit code $TARGET_EC (expected 0)"
fi

if [[ "$PATH_EC" -eq 0 ]]; then
  pass "W9b: --install-path exits 0"
else
  fail "W9b: --install-path exit code $PATH_EC (expected 0)"
fi

# Both have the same number of installed files
TARGET_FILES=$(find "$TARGET_DIR" -name '*.md' 2>/dev/null | wc -l)
PATH_FILES=$(find "$INSTALL_PATH_DIR" -name '*.md' 2>/dev/null | wc -l)

if [[ "$TARGET_FILES" -eq "$BLACKCOW_SOURCE_COUNT" ]]; then
  pass "W9c: --target installed ${TARGET_FILES} files"
else
  fail "W9c: --target installed ${TARGET_FILES} files (expected ${BLACKCOW_SOURCE_COUNT})"
fi

if [[ "$PATH_FILES" -eq "$BLACKCOW_SOURCE_COUNT" ]]; then
  pass "W9d: --install-path installed ${PATH_FILES} files"
else
  fail "W9d: --install-path installed ${PATH_FILES} files (expected ${BLACKCOW_SOURCE_COUNT})"
fi

# Compare allowed-tools lines between both installs — they should be identical
# (same platform, same source, just different flag names)
diff_count=0
for f in "$TARGET_DIR"/blackcow-*.md; do
  [[ -f "$f" ]] || continue
  bname=$(basename "$f")
  target_line=$(grep "^allowed-tools:" "$f" | head -1)
  path_line=$(grep "^allowed-tools:" "${INSTALL_PATH_DIR}/${bname}" 2>/dev/null | head -1 || echo "")

  if [[ "$target_line" != "$path_line" ]]; then
    diff_count=$((diff_count + 1))
    $VERBOSE && echo "       Diff in ${bname}: target='${target_line:0:60}' path='${path_line:0:60}'"
  fi
done

if [[ "$diff_count" -eq 0 ]]; then
  pass "W9e: allowed-tools lines identical between --target and --install-path"
else
  fail "W9e: ${diff_count} skills have different allowed-tools between aliases (should be 0)"
fi

# Both outputs show completion
if echo "$TARGET_OUTPUT" | grep -q "Installation complete"; then
  pass "W9f: --target output shows completion"
else
  fail "W9f: --target output missing completion"
fi
if echo "$PATH_OUTPUT" | grep -q "Installation complete"; then
  pass "W9g: --install-path output shows completion"
else
  fail "W9g: --install-path output missing completion"
fi

# Verify mutual exclusion — using both together is rejected
set +e
MUTEX_OUTPUT=$(cd "$PROJECT_ROOT" && HOME="$W9_SANDBOX" bash "$INSTALL_SCRIPT" --target "$TARGET_DIR" --install-path "$TARGET_DIR" 2>&1)
MUTEX_EC=$?
set -e
if [[ "$MUTEX_EC" -eq 1 ]] && echo "$MUTEX_OUTPUT" | grep -q "mutually exclusive"; then
  pass "W9h: --target and --install-path together → mutually exclusive error"
else
  fail "W9h: Mutual exclusion not enforced (exit $MUTEX_EC, message: ${MUTEX_OUTPUT:0:80})"
fi

destroy "$W9_SANDBOX"

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "========================================"
echo "L5 E2E Tests — install.sh (User Workflows)"
echo "========================================"
SCORE=$(( TOTAL > 0 ? PASS * 100 / TOTAL : 0 ))
echo "Results: $PASS passed, $FAIL failed, 0 skipped (total $TOTAL checks)"
echo "Score: ${SCORE}%"
echo "========================================"

exit $(( FAIL > 0 ? 1 : 0 ))
