#!/usr/bin/env bash
# ============================================================================
# L3 Contract Tests — install.sh public interface contracts
#
# Contracts validated (per skills/install.sh documented API):
#   C1 — Platform detection returns exactly "windows" or "macos"
#   C2 — allowed-tools line format: "allowed-tools: tool1, tool2, ..."
#   C3 — Output files are valid Markdown with YAML frontmatter (--- ... ---)
#   C4 — validate_install_path: resolved path on stdout on success;
#        "FATAL: ..." on stderr + exit 1 on failure
#   C5 — Exit codes: 0 for success, 1 for errors
#   C6 — --target and --install-path are mutually exclusive
#   C7 — --dry-run must not create/modify files
#
# Usage:
#   bash skills/tests/test-l3-contract-install-security.sh
#   bash skills/tests/test-l3-contract-install-security.sh --verbose
#
# Returns: 0 if ALL contract validations pass, 1 otherwise
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALLER="${SKILLS_DIR}/install.sh"

PASS=0; FAIL=0; SKIP=0; TOTAL=0
VERBOSE=false
[[ "${1:-}" == "--verbose" ]] && VERBOSE=true

pass()   { PASS=$((PASS+1)); TOTAL=$((TOTAL+1)); echo "  ✅ PASS: $1"; }
fail()   { FAIL=$((FAIL+1)); TOTAL=$((TOTAL+1)); echo "  ❌ FAIL: $1"; }
skip()   { SKIP=$((SKIP+1)); TOTAL=$((TOTAL+1)); echo "  ⏭️  SKIP: $1"; }
heading(){ echo ""; echo "━━━ $1 ━━━"; }

# --- Pre-flight --------------------------------------------------------------
if [[ ! -f "$INSTALLER" ]]; then
  echo "FATAL: install.sh not found at $INSTALLER" >&2
  exit 1
fi

# --- Bash version check ---
# install.sh uses `declare -A` (associative arrays) which requires bash ≥ 4.
# Function-level contracts (C1, C4) are tested by sourcing individual functions
# (no `declare -A` needed). Script-level contracts (C2, C3, C5, C6, C7) need
# to run the full script, so they're skipped on bash < 4.
BASH_MAJOR=${BASH_VERSINFO[0]:-0}
CAN_RUN_SCRIPT=false
if [[ "$BASH_MAJOR" -ge 4 ]]; then
  CAN_RUN_SCRIPT=true
else
  echo "  ⚠️  Bash ${BASH_VERSION}: script-level tests skipped (install.sh requires bash 4+)"
  echo "     Function-level contracts (C1, C4) still run."
fi

# --- Helper: source a function from install.sh by name ----------------------
source_function() {
  local func_name="$1"
  eval "$(sed -n "/^${func_name}()/,/^}/p" "$INSTALLER")"
}

# --- Helper: safe temp dirs under $HOME/.reasonix for validate_install_path --
# validate_install_path() requires targets under $HOME/.reasonix/.
# We create uniquely-named test subdirectories there and clean them up.
L3_TEST_PREFIX="${HOME}/.reasonix/skills/.l3-contract-test"

cleanup() {
  # Remove any .l3-contract-test-* dirs we created under ~/.reasonix/skills/
  for d in "${HOME}/.reasonix/skills"/.l3-contract-test-*; do
    [[ -d "$d" ]] && rm -rf "$d" 2>/dev/null || true
  done
  # Also remove any under ~/.reasonix/ directly (for validate path tests)
  for d in "${HOME}/.reasonix"/.l3-contract-test-*; do
    [[ -d "$d" ]] && rm -rf "$d" 2>/dev/null || true
  done
}
trap cleanup EXIT

# ============================================================================
# C1 — Platform Detection Contract
# ============================================================================
heading "C1 — Platform Detection (must return 'windows' or 'macos')"

source_function "detect_platform"

# C1a: Unmodified detection returns one of the two valid values
result=$(detect_platform)
if [[ "$result" == "windows" || "$result" == "macos" ]]; then
  pass "C1a: detect_platform returns '$result' (valid: windows|macos)"
else
  fail "C1a: detect_platform returned '$result' — expected 'windows' or 'macos'"
fi

# C1b: REASONIX_PLATFORM=windows forces "windows" on any OS
result=$(REASONIX_PLATFORM=windows detect_platform)
if [[ "$result" == "windows" ]]; then
  pass "C1b: REASONIX_PLATFORM=windows → 'windows'"
else
  fail "C1b: REASONIX_PLATFORM=windows → '$result' (expected 'windows')"
fi

# C1c: REASONIX_PLATFORM=macos forces "macos" (on non-Windows kernel)
if [[ "$(uname -s)" != MINGW* && "$(uname -s)" != MSYS* && "$(uname -s)" != CYGWIN* && "$(uname -s)" != Windows_NT ]]; then
  result=$(REASONIX_PLATFORM=macos detect_platform)
  if [[ "$result" == "macos" ]]; then
    pass "C1c: REASONIX_PLATFORM=macos → 'macos'"
  else
    fail "C1c: REASONIX_PLATFORM=macos → '$result' (expected 'macos')"
  fi
else
  # On Windows, detect_platform returns "windows" regardless of REASONIX_PLATFORM
  result=$(REASONIX_PLATFORM=macos detect_platform)
  if [[ "$result" == "windows" ]]; then
    pass "C1c: on Windows kernel, detect_platform returns 'windows' (env var ignored for kernel match)"
  else
    fail "C1c: on Windows kernel, expected 'windows', got '$result'"
  fi
fi

# ============================================================================
# C2 — allowed-tools line format contract
# ============================================================================
heading "C2 — allowed-tools line format"

if ! $CAN_RUN_SCRIPT; then
  skip "C2: requires bash ≥ 4 (install.sh uses declare -A)"
else
  TARGET_MAC="${HOME}/.reasonix/skills/.l3-contract-test-c2-mac"
  TARGET_WIN="${HOME}/.reasonix/skills/.l3-contract-test-c2-win"

  # --- C2a: macOS platform produces valid allowed-tools lines ---
  REASONIX_PLATFORM=macos bash "$INSTALLER" --target "$TARGET_MAC" > /dev/null 2>&1 || true

  mac_allowed_lines=0
  mac_bad_format=0
  for f in "$TARGET_MAC"/blackcow-*.md; do
    [[ -f "$f" ]] || continue
    line=$(grep "^allowed-tools:" "$f" | head -1)
    if [[ -z "$line" ]]; then
      mac_bad_format=$((mac_bad_format + 1))
      continue
    fi
    mac_allowed_lines=$((mac_allowed_lines + 1))
    # Extract the value part after "allowed-tools: "
    value="${line#allowed-tools: }"
    # Must not be empty
    if [[ -z "$value" ]]; then
      mac_bad_format=$((mac_bad_format + 1))
      continue
    fi
    # Must be comma-separated tool names (alphanum, underscore, hyphen)
    if ! echo "$value" | grep -qE '^[a-zA-Z_][a-zA-Z0-9_-]*(, ?[a-zA-Z_][a-zA-Z0-9_-]*)*$'; then
      mac_bad_format=$((mac_bad_format + 1))
      $VERBOSE && echo "       (malformed: $line)"
    fi
  done

  if [[ "$mac_allowed_lines" -gt 0 && "$mac_bad_format" -eq 0 ]]; then
    pass "C2a: macOS — $mac_allowed_lines skill files with valid allowed-tools format"
  else
    fail "C2a: macOS — $mac_allowed_lines valid, $mac_bad_format malformed"
  fi
  $VERBOSE && echo "       (macOS output in: $TARGET_MAC)"

  # --- C2b: Windows platform produces valid allowed-tools lines ---
  REASONIX_PLATFORM=windows bash "$INSTALLER" --target "$TARGET_WIN" > /dev/null 2>&1 || true

  win_allowed_lines=0
  win_bad_format=0
  for f in "$TARGET_WIN"/blackcow-*.md; do
    [[ -f "$f" ]] || continue
    line=$(grep "^allowed-tools:" "$f" | head -1)
    if [[ -z "$line" ]]; then
      win_bad_format=$((win_bad_format + 1))
      continue
    fi
    win_allowed_lines=$((win_allowed_lines + 1))
    value="${line#allowed-tools: }"
    if [[ -z "$value" ]]; then
      win_bad_format=$((win_bad_format + 1))
      continue
    fi
    if ! echo "$value" | grep -qE '^[a-zA-Z_][a-zA-Z0-9_-]*(, ?[a-zA-Z_][a-zA-Z0-9_-]*)*$'; then
      win_bad_format=$((win_bad_format + 1))
      $VERBOSE && echo "       (malformed: $line)"
    fi
  done

  if [[ "$win_allowed_lines" -gt 0 && "$win_bad_format" -eq 0 ]]; then
    pass "C2b: Windows — $win_allowed_lines skill files with valid allowed-tools format"
  else
    fail "C2b: Windows — $win_allowed_lines valid, $win_bad_format malformed"
  fi
  $VERBOSE && echo "       (Windows output in: $TARGET_WIN)"

  # --- C2c: macOS and Windows produce different tool sets (cross-platform contract) ---
  mac_tools_set=$(grep -h "^allowed-tools:" "$TARGET_MAC"/blackcow-*.md 2>/dev/null | sort -u || true)
  win_tools_set=$(grep -h "^allowed-tools:" "$TARGET_WIN"/blackcow-*.md 2>/dev/null | sort -u || true)
  if [[ "$mac_tools_set" != "$win_tools_set" ]]; then
    pass "C2c: macOS and Windows produce distinct allowed-tools lines (cross-platform contract)"
  else
    fail "C2c: macOS and Windows allowed-tools lines identical — platform substitution broken"
  fi

  rm -rf "$TARGET_MAC" "$TARGET_WIN"
fi

# ============================================================================
# C3 — Output files are valid Markdown with YAML frontmatter
# ============================================================================
heading "C3 — Output file frontmatter integrity"

if ! $CAN_RUN_SCRIPT; then
  skip "C3: requires bash ≥ 4 (install.sh uses declare -A)"
else
  TARGET_FM="${HOME}/.reasonix/skills/.l3-contract-test-c3"
  mkdir -p "$TARGET_FM"

  REASONIX_PLATFORM=macos bash "$INSTALLER" --target "$TARGET_FM" > /dev/null 2>&1 || true

  fm_total=0
  fm_valid=0
  fm_invalid=0
  for f in "$TARGET_FM"/blackcow-*.md; do
    [[ -f "$f" ]] || continue
    fm_total=$((fm_total + 1))

    # Must start with "---"
    first_line=$(head -1 "$f")
    if [[ "$first_line" != "---" ]]; then
      $VERBOSE && echo "       ($(basename "$f"): does not start with ---)"
      fm_invalid=$((fm_invalid + 1))
      continue
    fi

    # Count --- fences: at least 2 (opening + closing)
    fence_count=$(grep -c "^---" "$f" || true)
    if [[ "$fence_count" -lt 2 ]]; then
      $VERBOSE && echo "       ($(basename "$f"): only $fence_count --- fences)"
      fm_invalid=$((fm_invalid + 1))
      continue
    fi

    # Extract the YAML frontmatter block
    yaml_block=$(awk 'BEGIN{in_fence=0}
      /^---/ && !in_fence {in_fence=1; next}
      in_fence && /^---/ {exit}
      in_fence {print}' "$f")

    if [[ -z "$yaml_block" ]]; then
      $VERBOSE && echo "       ($(basename "$f"): empty frontmatter)"
      fm_invalid=$((fm_invalid + 1))
      continue
    fi

    # Must contain required frontmatter fields
    has_name=false; has_description=false; has_allowed_tools=false
    if echo "$yaml_block" | grep -q '^name:';          then has_name=true; fi
    if echo "$yaml_block" | grep -q '^description:';    then has_description=true; fi
    if echo "$yaml_block" | grep -q '^allowed-tools:';  then has_allowed_tools=true; fi

    if $has_name && $has_description && $has_allowed_tools; then
      fm_valid=$((fm_valid + 1))
    else
      fm_invalid=$((fm_invalid + 1))
      local missing=""
      $has_name || missing="$missing name"
      $has_description || missing="$missing description"
      $has_allowed_tools || missing="$missing allowed-tools"
      $VERBOSE && echo "       ($(basename "$f"): missing fields:$missing)"
    fi
  done

  if [[ "$fm_total" -gt 0 && "$fm_invalid" -eq 0 ]]; then
    pass "C3a: All $fm_total output files have valid Markdown with YAML frontmatter + required fields"
  else
    fail "C3a: $fm_valid valid, $fm_invalid invalid out of $fm_total files"
  fi

  # --- C3b: Frontmatter lines follow valid YAML key: value syntax ---
  yaml_syntax_errors=0
  for f in "$TARGET_FM"/blackcow-*.md; do
    [[ -f "$f" ]] || continue
    yaml_block=$(awk 'BEGIN{in_fence=0}
      /^---/ && !in_fence {in_fence=1; next}
      in_fence && /^---/ {exit}
      in_fence {print}' "$f")
    [[ -z "$yaml_block" ]] && continue
    while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      # Valid YAML frontmatter lines: key: value ; indented continuation ; or comment
      if ! echo "$line" | grep -qE '^[a-zA-Z_][a-zA-Z0-9_-]*:' && \
         ! echo "$line" | grep -qE '^[[:space:]]+' && \
         ! echo "$line" | grep -qE '^#'; then
        yaml_syntax_errors=$((yaml_syntax_errors + 1))
        $VERBOSE && echo "       (suspicious YAML in $(basename "$f"): $line)"
      fi
    done <<< "$yaml_block"
  done

  if [[ "$yaml_syntax_errors" -eq 0 ]]; then
    pass "C3b: All frontmatter lines follow valid YAML key: value syntax"
  else
    fail "C3b: $yaml_syntax_errors frontmatter lines have suspicious syntax"
  fi

  rm -rf "$TARGET_FM"
fi

# ============================================================================
# C4 — validate_install_path return value contract
# ============================================================================
heading "C4 — validate_install_path return value contract"

source_function "resolve_path"
source_function "validate_install_path"

# C4a: Success returns a non-empty resolved path on stdout (no "FATAL:" prefix)
result=$(validate_install_path "${HOME}/.reasonix/skills" 2>/dev/null) || true
if [[ -n "$result" && "$result" != "FATAL:"* ]]; then
  pass "C4a: Success returns resolved path on stdout: '$result'"
else
  fail "C4a: Expected resolved path on stdout, got: '$result'"
fi

# C4b: Failure outputs "FATAL: ..." on stderr and exits 1
set +e
output=$(validate_install_path "/tmp/../etc" 2>&1)
exit_code=$?
set -e
if [[ "$output" == "FATAL:"* ]]; then
  pass "C4b: Failure message starts with 'FATAL:' prefix: '${output:0:60}...'"
else
  fail "C4b: Expected 'FATAL:' prefix, got: '${output:0:80}'"
fi
if [[ "$exit_code" -eq 1 ]]; then
  pass "C4c: Failure exits with code 1"
else
  fail "C4c: Expected exit code 1, got $exit_code"
fi

# C4d: Empty string → "FATAL:" on stderr + exit 1
set +e
output=$(validate_install_path "" 2>&1)
exit_code=$?
set -e
if [[ "$output" == "FATAL:"* ]] && [[ "$exit_code" -eq 1 ]]; then
  pass "C4d: Empty string → FATAL + exit 1"
else
  fail "C4d: Empty string: expected FATAL+exit1, got exit=$exit_code output='${output:0:60}'"
fi

# C4e: Dot-dot traversal → "FATAL:" + exit 1
set +e
output=$(validate_install_path "${HOME}/.reasonix/../../etc" 2>&1)
exit_code=$?
set -e
if [[ "$output" == "FATAL:"* ]] && [[ "$exit_code" -eq 1 ]]; then
  pass "C4e: Dot-dot traversal → FATAL + exit 1"
else
  fail "C4e: Dot-dot traversal: expected FATAL+exit1, got exit=$exit_code"
fi

# C4f: Path outside ALLOWED_PREFIX → "FATAL:" + exit 1
set +e
output=$(validate_install_path "/tmp/outside" 2>&1)
exit_code=$?
set -e
if [[ "$output" == "FATAL:"* ]] && [[ "$exit_code" -eq 1 ]]; then
  pass "C4f: Path outside allowed prefix → FATAL + exit 1"
else
  fail "C4f: Outside prefix: expected FATAL+exit1, got exit=$exit_code"
fi

# ============================================================================
# C5 — Exit codes contract
# ============================================================================
heading "C5 — Exit codes (0 success, 1 errors)"

if ! $CAN_RUN_SCRIPT; then
  skip "C5: requires bash ≥ 4 (install.sh uses declare -A)"
else
  # C5a: Normal installation exits 0
  TARGET_EXIT="${HOME}/.reasonix/skills/.l3-contract-test-c5a"
  mkdir -p "$TARGET_EXIT"
  set +e
  REASONIX_PLATFORM=macos bash "$INSTALLER" --target "$TARGET_EXIT" > /dev/null 2>&1
  exit_code=$?
  set -e
  if [[ "$exit_code" -eq 0 ]]; then
    pass "C5a: Normal installation exits 0"
  else
    fail "C5a: Normal installation: expected exit 0, got $exit_code"
  fi
  rm -rf "$TARGET_EXIT"

  # C5b: Unknown argument exits 1
  set +e
  bash "$INSTALLER" --bogus-flag > /dev/null 2>&1
  exit_code=$?
  set -e
  if [[ "$exit_code" -eq 1 ]]; then
    pass "C5b: Unknown argument exits 1"
  else
    fail "C5b: Unknown argument: expected exit 1, got $exit_code"
  fi

  # C5c: --target with path outside allowed prefix exits 1
  set +e
  bash "$INSTALLER" --target "/tmp/outside-allowed" > /dev/null 2>&1
  exit_code=$?
  set -e
  if [[ "$exit_code" -eq 1 ]]; then
    pass "C5c: --target with path outside prefix exits 1"
  else
    fail "C5c: Outside prefix: expected exit 1, got $exit_code"
  fi

  # C5d: Dry-run exits 0
  TARGET_DRY="${HOME}/.reasonix/skills/.l3-contract-test-c5d"
  mkdir -p "$TARGET_DRY"
  set +e
  REASONIX_PLATFORM=macos bash "$INSTALLER" --target "$TARGET_DRY" --dry-run > /dev/null 2>&1
  exit_code=$?
  set -e
  if [[ "$exit_code" -eq 0 ]]; then
    pass "C5d: --dry-run exits 0"
  else
    fail "C5d: --dry-run: expected exit 0, got $exit_code"
  fi
  rm -rf "$TARGET_DRY"
fi

# ============================================================================
# C6 — Mutual exclusion of --target / --install-path
# ============================================================================
heading "C6 — --target and --install-path mutual exclusion"

if ! $CAN_RUN_SCRIPT; then
  skip "C6: requires bash ≥ 4 (install.sh uses declare -A)"
else
  # C6a: Passing both must fail with FATAL + exit 1
  # Note: mutual exclusion is checked during arg parsing (before path validation),
  # so the paths here don't matter — they'll fail at the mutual-exclusion check.
  set +e
  output=$(bash "$INSTALLER" --target "/tmp/foo" --install-path "/tmp/bar" 2>&1)
  exit_code=$?
  set -e
  if [[ "$exit_code" -eq 1 ]] && echo "$output" | grep -q "mutually exclusive"; then
    pass "C6a: --target + --install-path → FATAL: mutually exclusive (exit 1)"
  else
    fail "C6a: Expected exit 1 + 'mutually exclusive', got exit=$exit_code output='${output:0:80}'"
  fi

  # C6b: Reversed order also fails
  set +e
  output=$(bash "$INSTALLER" --install-path "/tmp/bar" --target "/tmp/foo" 2>&1)
  exit_code=$?
  set -e
  if [[ "$exit_code" -eq 1 ]] && echo "$output" | grep -q "mutually exclusive"; then
    pass "C6b: --install-path + --target (reversed) → FATAL: mutually exclusive"
  else
    fail "C6b: Reversed: expected exit 1 + 'mutually exclusive', got exit=$exit_code"
  fi

  # C6c: --target alone works (no conflict) — uses path under $HOME/.reasonix
  TARGET_C6="${HOME}/.reasonix/skills/.l3-contract-test-c6c"
  mkdir -p "$TARGET_C6"
  set +e
  REASONIX_PLATFORM=macos bash "$INSTALLER" --target "$TARGET_C6" > /dev/null 2>&1
  exit_code=$?
  set -e
  if [[ "$exit_code" -eq 0 ]]; then
    pass "C6c: --target alone exits 0"
  else
    fail "C6c: --target alone: expected exit 0, got $exit_code"
  fi
  rm -rf "$TARGET_C6"

  # C6d: --install-path alone works (no conflict) — uses path under $HOME/.reasonix
  TARGET_C6D="${HOME}/.reasonix/skills/.l3-contract-test-c6d"
  mkdir -p "$TARGET_C6D"
  set +e
  REASONIX_PLATFORM=macos bash "$INSTALLER" --install-path "$TARGET_C6D" > /dev/null 2>&1
  exit_code=$?
  set -e
  if [[ "$exit_code" -eq 0 ]]; then
    pass "C6d: --install-path alone exits 0"
  else
    fail "C6d: --install-path alone: expected exit 0, got $exit_code"
  fi
  rm -rf "$TARGET_C6D"
fi

# ============================================================================
# C7 — --dry-run must not create/modify files
# ============================================================================
heading "C7 — --dry-run file system safety"

if ! $CAN_RUN_SCRIPT; then
  skip "C7: requires bash ≥ 4 (install.sh uses declare -A)"
else
  # C7a: --dry-run with valid target directory must not create it
  DRY_TARGET="${HOME}/.reasonix/skills/.l3-contract-test-c7"
  rm -rf "$DRY_TARGET"  # ensure it does NOT exist

  REASONIX_PLATFORM=macos bash "$INSTALLER" --target "$DRY_TARGET" --dry-run > /dev/null 2>&1 || true

  if [[ ! -d "$DRY_TARGET" ]]; then
    pass "C7a: --dry-run did not create target directory"
  else
    fail "C7a: --dry-run created target directory at $DRY_TARGET"
  fi

  # C7b: --dry-run with default target outputs [DRY-RUN] markers instead of writing
  dry_output=$(REASONIX_PLATFORM=macos bash "$INSTALLER" --dry-run 2>&1 || true)
  dry_run_lines=$(echo "$dry_output" | grep -c "\[DRY-RUN\]" || true)
  if [[ "$dry_run_lines" -gt 0 ]]; then
    pass "C7b: --dry-run outputs $dry_run_lines [DRY-RUN] markers (no files written)"
  else
    fail "C7b: --dry-run output missing [DRY-RUN] markers"
  fi

  # C7c: Completion message contains "DRY-RUN"
  if echo "$dry_output" | grep -q "DRY-RUN"; then
    pass "C7c: --dry-run output contains 'DRY-RUN' in completion message"
  else
    fail "C7c: --dry-run output missing 'DRY-RUN' in completion message"
  fi
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "========================================"
echo "L3 Contract Tests — install.sh"
echo "========================================"
SCORE=$(( TOTAL > 0 ? PASS * 100 / TOTAL : 0 ))
echo "Results: $PASS passed, $FAIL failed, $SKIP skipped (total $TOTAL checks)"
echo "Score: ${SCORE}%"
echo "========================================"

exit $(( FAIL > 0 ? 1 : 0 ))
