#!/usr/bin/env bash
set -euo pipefail

SKILL_FILE="skills/blackcow-swarm.md"
LOOP_FILE="skills/blackcow-loop.md"
TOTAL=0
PASS=0
FAIL=0
CHECK_LOOP_ONLY=false

for arg in "$@"; do
  case "$arg" in
    --check-loop-non-swarm) CHECK_LOOP_ONLY=true ;;
  esac
done

pass() {
  PASS=$((PASS + 1))
  TOTAL=$((TOTAL + 1))
  echo "PASS $1"
}

fail() {
  FAIL=$((FAIL + 1))
  TOTAL=$((TOTAL + 1))
  echo "FAIL $1"
}

assert_grep() {
  local label="$1" pattern="$2"
  if grep -Eq "$pattern" "$SKILL_FILE" 2>/dev/null; then
    pass "$label"
  else
    fail "$label"
  fi
}

echo "BlackCow Swarm Contract Validation"

if $CHECK_LOOP_ONLY; then
  SKILL_FILE="$LOOP_FILE"
  if [[ -f "$LOOP_FILE" ]]; then
    pass "loop skill file exists"
  else
    fail "loop skill file exists"
    echo "Results: $PASS passed, $FAIL failed (total $TOTAL)"
    exit 1
  fi
  assert_grep "loop mentions blackcow-swarm" "blackcow-swarm"
  assert_grep "loop requires explicit swarm activation" "explicit swarm activation|--swarm|--use-swarm"
  assert_grep "loop preserves default TRY behavior" "TRY.*default|default.*TRY|no-swarm"
  echo "Results: $PASS passed, $FAIL failed (total $TOTAL)"
  if [[ "$FAIL" -eq 0 ]]; then
    exit 0
  fi
  exit 1
fi

if [[ -f "$SKILL_FILE" ]]; then
  pass "skill file exists"
else
  fail "skill file exists"
  echo "Results: $PASS passed, $FAIL failed (total $TOTAL)"
  exit 1
fi

for field in name description runAs version updated model allowed-tools; do
  assert_grep "frontmatter field: $field" "^${field}:"
done

assert_grep "frontmatter name is blackcow-swarm" '^name: blackcow-swarm$'
assert_grep "runAs subagent" '^runAs: subagent$'
assert_grep "model tiers present" '^model_tiers:'
assert_grep "budget tier present" '^[[:space:]]+budget:'
assert_grep "pro tier present" '^[[:space:]]+pro:'
assert_grep "allowed tools include run_command" '^allowed-tools:.*run_command'
assert_grep "allowed tools include run_skill" '^allowed-tools:.*run_skill'
assert_grep "agent-executed skill UX" 'agent-executed skill|agent runs'
assert_grep "internal control plane API" 'Internal control-plane API|private implementation entrypoint'
assert_grep "not user-operated service entrypoint" 'not a user-operated daemon|not a separate service entrypoint'
assert_grep "no docker compose service UX" 'docker-compose up -d'
assert_grep "do not ask user to run terminal commands" 'Never tell the user to open a terminal|Do not ask the user to run this command'
assert_grep "completion gate required" 'Completion Gate'
assert_grep "acceptance checks before final judgement" 'acceptance_checks.*final_judgement|final_judgement.*acceptance_checks'
assert_grep "browser smoke required for UI" 'browser-smoke'
assert_grep "runtime error blocks success" 'Something went wrong'
assert_grep "no one-to-one ping-pong fallback" 'one-to-one ping-pong'
assert_grep "failure feedback packet" 'failure feedback packet'
assert_grep "feedback artifacts path" '.omo/swarm/runs/.*/feedback|feedback/'
assert_grep "reasonix ACP worker wrapper" 'blackcow_reasonix_acp_worker\.py'
assert_grep "reasonix ACP command" 'reasonix acp'
assert_grep "reasonix ACP yolo dir" 'acp --yolo --dir|reasonix acp --yolo'
assert_grep "worker prompt embeds active skill source" 'Active Skill Source'
assert_grep "worker forbids recursive run_skill" 'must not call `run_skill`|Do not call run_skill'
assert_grep "label-only worker prompt invalid" 'label-backed|only "Implement candidate patch'
assert_grep "prompt includes shared context" 'shared_context\.md'
assert_grep "prompt includes blackcow-governor excerpts" 'blackcow-governor'
assert_grep "prompt includes blackcow-librarian excerpts" 'blackcow-librarian'
assert_grep "design source gate mentions getdesign.kr" 'getdesign\.kr'
assert_grep "design source gate mentions getdesign.md" 'getdesign\.md'
assert_grep "design source gate mentions DESIGN.md" 'DESIGN\.md'
assert_grep "web design system mentions shadcn/ui" 'shadcn/ui'
assert_grep "React Native native target required" 'React Native'
assert_grep "native simulator gate uses xcrun simctl" 'xcrun simctl'
assert_grep "native gate launches project app" 'blackcow_expo_native_smoke\.py|launching the project app'
assert_grep "rejects arbitrary open simulator screenshot" 'whatever app happened to be open|invalid evidence'
assert_grep "codex image review gate" 'codex exec --image'
assert_grep "speed gate mentions speedup" 'speedup'
assert_grep "speed gate records started_at" 'started_at'
assert_grep "speed gate records finished_at" 'finished_at'

for term in DeepSeek Reasonix blackcow.swarm.json scripts/blackcow_swarm.py MockRunner ReasonixRunner result.json anti-gaming ".worktrees/swarm" ".omo/swarm/runs"; do
  assert_grep "runtime contract mentions $term" "$term"
done

for command in estimate plan run resume cancel status cleanup; do
  assert_grep "CLI command: $command" "\\b${command}\\b"
done

for policy in off suggest auto force; do
  assert_grep "policy enum: $policy" "\\b${policy}\\b"
done

for mode in serial qa discovery review coder full adaptive; do
  assert_grep "mode enum: $mode" "\\b${mode}\\b"
done

for intensity in normal high max; do
  assert_grep "intensity enum: $intensity" "\\b${intensity}\\b"
done

for skill in blackcow-plan blackcow-loop blackcow-qa; do
  assert_grep "cross-skill reference: $skill" "$skill"
done

assert_grep "no Kimi constraint" 'No Kimi|no Kimi'
assert_grep "shell true forbidden" 'shell=True'
assert_grep "approval gate" 'requires_approval|--yes'

echo "Results: $PASS passed, $FAIL failed (total $TOTAL)"
if [[ "$FAIL" -eq 0 ]]; then
  exit 0
fi
exit 1
