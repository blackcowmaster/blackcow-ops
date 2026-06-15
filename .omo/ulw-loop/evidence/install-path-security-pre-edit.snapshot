#!/usr/bin/env bash
# =============================================================================
# BlackCow Ops — Cross-Platform Skill Installer
# =============================================================================
# Detects the host Reasonix platform (Windows vs macOS/Linux) and installs
# skills with the correct `allowed-tools` frontmatter for that platform.
#
# Usage:
#   bash skills/install.sh              # install to ~/.reasonix/skills/
#   bash skills/install.sh --dry-run    # show what would change, don't write
#   bash skills/install.sh --target ~/custom/skills/  # custom target dir
# =============================================================================

set -euo pipefail

DRY_RUN=false
TARGET_DIR="${HOME}/.reasonix/skills"
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --target) TARGET_DIR="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

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
declare -A SKILL_EXTRA_WIN
declare -A SKILL_EXTRA_MAC

# ── FP-001/FP-002/FP-003/FP-004 auto-fix: remove lsp_* legacy tools,
#     remove redundant tools already in MAC_TOOLS base,
#     add get_symbols + find_in_code for dispatch protocol ──

SKILL_EXTRA_WIN["blackcow-plan.md"]="explore, research"
SKILL_EXTRA_MAC["blackcow-plan.md"]="get_symbols, find_in_code"

SKILL_EXTRA_WIN["blackcow-loop.md"]="explore, research"
SKILL_EXTRA_MAC["blackcow-loop.md"]="get_symbols, find_in_code"

SKILL_EXTRA_WIN["blackcow-qa.md"]="explore, research"
SKILL_EXTRA_MAC["blackcow-qa.md"]="get_symbols, find_in_code"

SKILL_EXTRA_WIN["blackcow-librarian.md"]=""
SKILL_EXTRA_MAC["blackcow-librarian.md"]=""

SKILL_EXTRA_WIN["blackcow-skill-review.md"]=""
SKILL_EXTRA_MAC["blackcow-skill-review.md"]=""

SKILL_EXTRA_WIN["blackcow-skill-evolver.md"]=""
SKILL_EXTRA_MAC["blackcow-skill-evolver.md"]=""

SKILL_EXTRA_WIN["blackcow-governor.md"]="explore, research"
SKILL_EXTRA_MAC["blackcow-governor.md"]=""

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
    if [[ -n "${SKILL_EXTRA_WIN[$skill_name]:-}" ]]; then
      win_line="${win_line}, ${SKILL_EXTRA_WIN[$skill_name]}"
    fi
    NEW_ALLOWED="${win_line}"
  else
    mac_line="allowed-tools: ${COMMON_TOOLS}, ${MAC_TOOLS}"
    if [[ -n "${SKILL_EXTRA_MAC[$skill_name]:-}" ]]; then
      mac_line="${mac_line}, ${SKILL_EXTRA_MAC[$skill_name]}"
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