#!/usr/bin/env bash
# =============================================================================
# BlackCow Ops — Cross-Platform Skill Installer
# =============================================================================
# Detects the host Reasonix platform (Windows vs macOS/Linux) and installs
# skills with the correct `allowed-tools` frontmatter for that platform.
#
# Usage:
#   bash skills/install.sh                  # install to ~/.reasonix/skills/
#   bash skills/install.sh --dry-run        # show what would change, don't write
#   bash skills/install.sh --target ~/custom/skills/      # custom target dir
#   bash skills/install.sh --install-path ~/custom/skills/ # alias for --target
# =============================================================================

set -euo pipefail

# =============================================================================
# Path Validation — Security Hardening (governed: install-path-security)
# =============================================================================
# resolve_path(raw_path) → resolved absolute path (stdout)
# Tiered fallback for cross-platform realpath:
#   1. realpath -m (GNU coreutils / macOS with coreutils)
#   2. python3 -c "import os; print(os.path.realpath(...))" (macOS 10.15+)
#   3. readlink -f (GNU)
#   4. cd "$dir" && pwd -P (POSIX ultimate fallback)

resolve_path() {
  local dir="$1"

  # Tier 1: realpath -m (doesn't require path to exist)
  if command -v realpath &>/dev/null; then
    realpath -m "$dir" 2>/dev/null && return 0
  fi

  # Tier 2: python3
  if command -v python3 &>/dev/null; then
    python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" "$dir" 2>/dev/null && return 0
  fi

  # Tier 3: readlink -f
  if command -v readlink &>/dev/null && readlink -f / &>/dev/null 2>&1; then
    readlink -f "$dir" 2>/dev/null && return 0
  fi

  # Tier 4: cd + pwd -P (POSIX, requires parent dir to exist)
  local parent
  parent=$(dirname "$dir")
  if [[ -d "$parent" ]]; then
    (
      cd "$parent" 2>/dev/null || exit 1
      echo "$(pwd -P)/$(basename "$dir")"
    ) 2>/dev/null && return 0
  fi

  # All tiers failed
  echo "FATAL: Cannot resolve path: $dir (no realpath/python3/readlink available)" >&2
  exit 1
}

# validate_install_path(raw_path) → resolved absolute path (stdout)
# Blocks 6 traversal vectors:
#   1. Empty string
#   2. Null byte injection (defense-in-depth)
#   3. Home-relative confusion (~ expansion before .. check)
#   4. Dot-dot traversal (.. anywhere in path)
#   5. Double-slash bypass (// anywhere)
#   6. Resolved path outside allowed prefix

validate_install_path() {
  local raw="$1"
  local ALLOWED_PREFIX="${HOME}/.reasonix"

  # Step 1: reject empty
  if [[ -z "$raw" ]]; then
    echo "FATAL: --install-path / --target requires a non-empty path" >&2
    exit 1
  fi

  # Step 2: reject null bytes (defense-in-depth — bash already truncates)
  if [[ "$(printf '%s' "$raw" | tr -d '\000')" != "$raw" ]]; then
    echo "FATAL: Path contains null bytes: ${raw}" >&2
    exit 1
  fi

  # Step 3: expand ~ to $HOME (before further checks)
  local expanded="$raw"
  if [[ "$raw" == '~/'* ]]; then
    expanded="${HOME}${raw#'~'}"
  elif [[ "$raw" == '~' ]]; then
    expanded="${HOME}"
  fi

  # Step 4: reject dot-dot traversal (.. anywhere)
  if [[ "$expanded" == *..* ]]; then
    echo "FATAL: Path traversal detected (..): ${raw}" >&2
    exit 1
  fi

  # Step 5: reject double-slash (// anywhere)
  if [[ "$expanded" == *//* ]]; then
    echo "FATAL: Double-slash detected (//): ${raw}" >&2
    exit 1
  fi

  # Step 6: resolve to absolute path (symlink defense)
  local resolved
  if ! resolved=$(resolve_path "$expanded"); then
    echo "FATAL: Cannot resolve path: ${raw}" >&2
    exit 1
  fi

  # Step 7: prefix check — resolved path must equal ALLOWED_PREFIX or be under ALLOWED_PREFIX/
  if [[ "$resolved" != "${ALLOWED_PREFIX}" && "$resolved" != "${ALLOWED_PREFIX}/"* ]]; then
    echo "FATAL: Path outside allowed prefix (${ALLOWED_PREFIX}): ${raw} → ${resolved}" >&2
    exit 1
  fi

  echo "$resolved"
}

DRY_RUN=false
TARGET_DIR="${HOME}/.reasonix/skills"
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"

# Parse args — collect raw values first, check conflicts, then validate
INSTALL_FLAG_USED=""
RAW_TARGET_DIR=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --target)
      if [[ -n "$INSTALL_FLAG_USED" ]]; then
        echo "FATAL: --target and --install-path are mutually exclusive" >&2
        exit 1
      fi
      INSTALL_FLAG_USED="--target"
      RAW_TARGET_DIR="$2"
      shift 2
      ;;
    --install-path)
      if [[ -n "$INSTALL_FLAG_USED" ]]; then
        echo "FATAL: --target and --install-path are mutually exclusive" >&2
        exit 1
      fi
      INSTALL_FLAG_USED="--install-path"
      RAW_TARGET_DIR="$2"
      shift 2
      ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# Validate the target path after all args are parsed
if [[ -n "$RAW_TARGET_DIR" ]]; then
  TARGET_DIR="$(validate_install_path "$RAW_TARGET_DIR")"
else
  # Default path: resolve to ensure it passes validation
  TARGET_DIR="$(validate_install_path "${HOME}/.reasonix/skills" 2>/dev/null || echo "${HOME}/.reasonix/skills")"
fi

# =============================================================================
# Platform Detection
# =============================================================================
# Strategy: check the OS type + Reasonix tool availability hints.
# Windows Reasonix typically uses: grep, ls, bash, task
# macOS/Linux Reasonix typically uses: search_content, list_directory, run_command, explore

detect_platform() {
  local os
  os=$(uname -s 2>/dev/null || echo "Unknown")

  case "$os" in
    MINGW*|MSYS*|CYGWIN*|Windows_NT)
      echo "windows"
      ;;
    Darwin|Linux)
      # On macOS/Linux, some users may still have older Windows-style Reasonix.
      # Default to macOS tools; user can override with REASONIX_PLATFORM env var.
      if [[ "${REASONIX_PLATFORM:-}" == "windows" ]]; then
        echo "windows"
      else
        echo "macos"
      fi
      ;;
    *)
      echo "macos"  # default fallback
      ;;
  esac
}

PLATFORM=$(detect_platform)
echo "→ Detected platform: ${PLATFORM}"

# =============================================================================
# Tool name sets per platform
# =============================================================================

# Common tools (same name on both platforms)
COMMON_TOOLS="read_file, glob, web_fetch, write_file, edit_file, multi_edit"

# Windows-specific
WIN_TOOLS="grep, ls, bash, task"

# macOS-specific
MAC_TOOLS="search_content, search_files, list_directory, directory_tree, run_command, web_search, explore, research, run_skill, get_file_info"

# Skill-specific additional tools
# (tools beyond the common set that each skill needs)
# NOTE: Functions (not associative arrays) for bash 3.2 (macOS default) compat.

# Returns extra Windows tools for a given skill name, or empty string.
get_skill_extra_win() {
  local skill="$1"
  case "$skill" in
    blackcow-plan.md|blackcow-loop.md|blackcow-qa.md|blackcow-governor.md)
      echo "explore, research"
      ;;
    blackcow-librarian.md|blackcow-skill-review.md|blackcow-skill-evolver.md)
      echo "explore, research"
      ;;
    *)
      echo ""
      ;;
  esac
}

# Returns extra macOS tools for a given skill name, or empty string.
get_skill_extra_mac() {
  local skill="$1"
  case "$skill" in
    blackcow-plan.md|blackcow-loop.md|blackcow-qa.md)
      echo "get_symbols, find_in_code"
      ;;
    blackcow-governor.md)
      echo "get_symbols, find_in_code, ask_choice"
      ;;
    blackcow-librarian.md)
      echo "get_symbols, find_in_code"
      ;;
    blackcow-skill-review.md)
      echo "get_symbols"
      ;;
    blackcow-skill-evolver.md)
      echo "get_symbols, find_in_code"
      ;;
    *)
      echo ""
      ;;
  esac
}

# =============================================================================
# Install
# =============================================================================

mkdir -p "${TARGET_DIR}"

for skill_file in "${SOURCE_DIR}"/*.md; do
  skill_name=$(basename "${skill_file}")
  # Skip non-skill files
  if [[ ! "$skill_name" =~ ^blackcow-.*\.md$ ]]; then
    continue
  fi

  dest="${TARGET_DIR}/${skill_name}"

  echo ""
  echo "── ${skill_name} ──"

  # Build the allowed-tools line for this platform
  if [[ "$PLATFORM" == "windows" ]]; then
    win_line="allowed-tools: ${COMMON_TOOLS}, ${WIN_TOOLS}"
    extra_win=$(get_skill_extra_win "$skill_name")
    if [[ -n "$extra_win" ]]; then
      win_line="${win_line}, ${extra_win}"
    fi
    NEW_ALLOWED="${win_line}"
  else
    mac_line="allowed-tools: ${COMMON_TOOLS}, ${MAC_TOOLS}"
    extra_mac=$(get_skill_extra_mac "$skill_name")
    if [[ -n "$extra_mac" ]]; then
      mac_line="${mac_line}, ${extra_mac}"
    fi
    NEW_ALLOWED="${mac_line}"
  fi

  # Read the source, replace the allowed-tools line
  # Match any line starting with "allowed-tools:"
  OLD_ALLOWED=$(grep "^allowed-tools:" "${skill_file}" | head -1)

  if [[ -z "$OLD_ALLOWED" ]]; then
    echo "  ⚠️  No allowed-tools line found in ${skill_file} — skipping"
    continue
  fi

  echo "  Old: ${OLD_ALLOWED}"
  echo "  New: ${NEW_ALLOWED}"

  if $DRY_RUN; then
    echo "  [DRY-RUN] Would install to: ${dest}"
    continue
  fi

  # Use sed to replace the allowed-tools line
  # Escape special chars for sed
  ESCAPED_OLD=$(echo "$OLD_ALLOWED" | sed 's/[\/&]/\\&/g')
  ESCAPED_NEW=$(echo "$NEW_ALLOWED" | sed 's/[\/&]/\\&/g')

  sed "s/^allowed-tools:.*/${ESCAPED_NEW}/" "${skill_file}" > "${dest}"
  echo "  ✅ Installed to: ${dest}"
done

# =============================================================================
# Test Suite Registration
# =============================================================================
# Make all validate-*.sh scripts executable and register the ecosystem
# health runner as the single entry point for full-suite validation.
TEST_DIR="${SOURCE_DIR}/tests"
if [[ -d "$TEST_DIR" ]]; then
  echo ""
  echo "── Test Suite ──"

  # Make all test scripts executable
  chmod +x "$TEST_DIR"/validate-*.sh 2>/dev/null || true
  echo "  ✅ All validate-*.sh scripts made executable"

  # Register the ecosystem health runner as the unified entry point
  HEALTH_RUNNER="$TEST_DIR/validate-blackcow-ecosystem-health.sh"
  if [[ -f "$HEALTH_RUNNER" ]]; then
    echo "  ✅ Ecosystem health runner registered: validate-blackcow-ecosystem-health.sh"
    echo "     Usage: bash skills/tests/validate-blackcow-ecosystem-health.sh"
    echo "            bash skills/tests/validate-blackcow-ecosystem-health.sh --json"
    echo "            bash skills/tests/validate-blackcow-ecosystem-health.sh --verbose"
  else
    echo "  ⚠️  Ecosystem health runner NOT FOUND at $HEALTH_RUNNER"
  fi
else
  echo "  ⚠️  Test directory NOT FOUND at $TEST_DIR"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Installation complete for platform: ${PLATFORM}"
echo "   Target: ${TARGET_DIR}"
if $DRY_RUN; then
  echo "   Mode: DRY-RUN (no files written)"
fi
echo ""
echo "   Restart Reasonix to load the new skills."
echo "   To install for a different platform, set REASONIX_PLATFORM:"
echo "     REASONIX_PLATFORM=windows bash skills/install.sh"
echo ""
echo "   For O2-O4 observable verification (optional):"
echo "     add_mcp_server({ name: puppeteer, from_catalog: puppeteer })"
echo "     # Enables: puppeteer_navigate, puppeteer_screenshot, puppeteer_click, puppeteer_evaluate"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"