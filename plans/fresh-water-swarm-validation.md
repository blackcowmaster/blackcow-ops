# Fresh Water Swarm Validation

## TL;DR
> Summary:      Validate a fresh Reasonix-backed BlackCow Swarm run that generates `swarm-water-check-app`, proves timing/skill usage/quality gates, and fixes only swarm control-plane defects found during the run.
> Deliverables:
> - Fresh run artifacts under `.omo/swarm/runs/fresh-water-swarm-live/`
> - ULW evidence under `.omo/ulw-loop/fresh-water-swarm-20260617/evidence/`
> - Control-plane RED to GREEN evidence for every pipeline defect
> - Final review gate packet with prompts, transcripts, acceptance logs, screenshots, speed evidence, and final judgement
> Effort:       Large
> Risk:         High - live Reasonix, Expo, simulator, visual review, dirty checkout, and prompt-contract surfaces can fail independently.

## Scope
### Must have
- Run a fresh BlackCow Swarm/Reasonix generation for target `swarm-water-check-app`; prior `water-check-app/`, `pomodoro-app/`, and `.omo/swarm/runs/water-check-live*` are reference-only and must not count as proof.
- Use existing dry-run graph `.omo/swarm/runs/fresh-water-swarm-plan/task_graph.json` as the planned acceptance source, then execute live with run id `fresh-water-swarm-live`.
- Prove measured elapsed time, worker timing, and speedup using `state.json` and `scripts/blackcow_speed_gate.py`.
- Prove worker prompt/transcript usage of `blackcow-*` skills plus React Native architecture/design skill context.
- If the generated app has defects, do not hand-edit the app. Fix only `scripts/blackcow_swarm*`, `scripts/blackcow_reasonix_acp_worker.py`, `skills/blackcow-*.md`, schemas, or tests, and only through RED to GREEN.
- Capture all proof under `.omo/ulw-loop/fresh-water-swarm-20260617/evidence/` and `.omo/swarm/runs/fresh-water-swarm-live/`.
- Final review gate may start only after C001, C002, and C003 below pass.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Do not manually modify `swarm-water-check-app/**` to make acceptance pass.
- Do not reuse prior app directories, prior run screenshots, prior visual reviews, or root `evidence/*` as fresh proof.
- Do not weaken, skip, delete, or replace the dry-run acceptance checks.
- Do not claim success from dry-run output, stdout prose, or missing/invalid `result.json`.
- Do not install host-level tools from workers (`brew`, `apt`, `sudo`, `npm -g`, `npx playwright install`, global browser/Codex installers).
- Do not apply generated patches directly to the main checkout unless the task graph and command explicitly require approved dangerous mode; default proof is via swarm integration worktree and final selected patch.

### ULW criteria
- C001 happy path: `python3 scripts/blackcow_swarm.py run --task-graph .omo/swarm/runs/fresh-water-swarm-plan/task_graph.json --runner reasonix --run-id fresh-water-swarm-live` exits 0; `.omo/swarm/runs/fresh-water-swarm-live/final_judgement.json` has `status=SUCCEEDED`; `swarm-water-check-app/package.json` exists; all dry-run acceptance checks pass against `fresh-water-swarm-live`; `state.json` contains worker `started_at` and `finished_at`; `scripts/blackcow_speed_gate.py --run-dir .omo/swarm/runs/fresh-water-swarm-live --min-speedup 1.1` passes. Manual QA channel: tmux, plus acceptance-owned web/native screenshots.
- C002 edge/adversarial: dirty root, preexisting target, prompt skill omission, missing simulator/Codex/browser, or failed acceptance never causes fake success. The controller must emit structured failure/preflight/feedback evidence and re-enter a control-plane RED to GREEN loop. Manual QA channel: tmux.
- C003 regression: existing swarm estimator, task graph, scheduler, worktree isolation, prompt contract, acceptance runner, native/web/design/speed gates, and `blackcow-loop` no-default-swarm behavior remain intact. Manual QA channel: tmux.

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: TDD + Python `unittest` for control-plane defects; tests-after for fresh generated app only through swarm-owned acceptance commands.
- QA policy: every task has agent-executed scenarios.
- Evidence: `.omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-<N>-fresh-water-swarm-validation.<ext>`

## Execution strategy
### Parallel execution waves
> Target 5-8 tasks per wave. <3 per wave (except final) = under-splitting.
> Extract shared dependencies as Wave-1 tasks to maximize parallelism.

Wave 1 (no dependencies):
- Task 1: Establish fresh evidence boundary and preflight manifest
- Task 2: Add RN skill visibility prompt contract
- Task 3: Add dirty-root writer preflight contract

Wave 2 (after Wave 1):
- Task 4: Run fresh live Reasonix swarm and measure elapsed time
- Task 5: Audit worker prompts, transcripts, results, and skill usage

Wave 3 (after Wave 2):
- Task 6: Execute acceptance, native/web smoke, visual, and speed gates
- Task 7: Run control-plane RED to GREEN loop for any failed gate

Wave 4 (after Wave 3):
- Task 8: Assemble final review gate packet and commit-ready state

Critical path: Task 1 -> Task 3 -> Task 4 -> Task 6 -> Task 7 -> Task 8

### Dependency matrix
| Task | Depends on | Blocks | Can parallelize with |
|------|------------|--------|----------------------|
| 1    | none       | 4, 6, 8 | 2, 3 |
| 2    | none       | 4, 5, 8 | 1, 3 |
| 3    | none       | 4, 7, 8 | 1, 2 |
| 4    | 1, 2, 3    | 5, 6, 7, 8 | none |
| 5    | 4          | 7, 8 | 6 |
| 6    | 4          | 7, 8 | 5 |
| 7    | 5, 6       | 8 | none |
| 8    | 5, 6, 7    | final verification | none |

## Todos
> Implementation + Test = ONE task. Never separate.
> Every task MUST have: References + Acceptance Criteria + QA Scenarios + Commit.

- [ ] 1. Establish fresh evidence boundary and preflight manifest

  What to do: Create `.omo/ulw-loop/fresh-water-swarm-20260617/evidence/`. Capture current `git status --short`, confirm `fresh-water-swarm-plan` artifacts exist, archive or fail on any preexisting `swarm-water-check-app` before live proof, and write `fresh-boundary.json` listing forbidden proof sources.
  Must NOT do: Do not delete prior app/run directories without preserving an artifact; do not treat any reference-only app as fresh proof.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [4, 6, 8] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `.omo/ulw-loop/fresh-water-swarm-20260617/notepad.md:22` - fresh evidence boundary and forbidden prior proof sources.
  - Pattern:  `.omo/swarm/runs/fresh-water-swarm-plan/estimate.json:2` - serial estimate and speed expectation source.
  - Pattern:  `.omo/swarm/runs/fresh-water-swarm-plan/task_graph.json:10` - required acceptance checks from dry-run graph.
  - Pattern:  `skills/blackcow-swarm.md:126` - required run artifact directory contract.

  Acceptance criteria (agent-executable only):
  - [ ] `test -f .omo/swarm/runs/fresh-water-swarm-plan/task_graph.json`
  - [ ] `test -f .omo/swarm/runs/fresh-water-swarm-plan/estimate.json`
  - [ ] `test -f .omo/ulw-loop/fresh-water-swarm-20260617/evidence/fresh-boundary.json`
  - [ ] `python3 - <<'PY'\nimport json, pathlib\np=pathlib.Path('.omo/ulw-loop/fresh-water-swarm-20260617/evidence/fresh-boundary.json')\nd=json.loads(p.read_text())\nassert d['target']=='swarm-water-check-app'\nassert 'water-check-app/' in d['forbidden_proof_sources']\nassert 'pomodoro-app/' in d['forbidden_proof_sources']\nPY`

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Fresh boundary manifest is usable
    Tool:     tmux
    Steps:    tmux new-session -d -s ulw-qa-C001-boundary "cd /Users/jeong-yugyeong/Project/blackcow-ops; { test -f .omo/ulw-loop/fresh-water-swarm-20260617/evidence/fresh-boundary.json; python3 -m json.tool .omo/ulw-loop/fresh-water-swarm-20260617/evidence/fresh-boundary.json; } > .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-1-fresh-water-swarm-validation.txt 2>&1"; while tmux has-session -t ulw-qa-C001-boundary 2>/dev/null; do sleep 1; done; test -s .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-1-fresh-water-swarm-validation.txt
    Expected: capture contains JSON with target `swarm-water-check-app` and no command failure text
    Evidence: .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-1-fresh-water-swarm-validation.txt

  Scenario: Prior proof is rejected
    Tool:     bash
    Steps:    python3 - <<'PY' > .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-1-fresh-water-swarm-validation-error.txt\nimport json, pathlib\nblocked={'water-check-app/','pomodoro-app/','.omo/swarm/runs/water-check-live*'}\nd=json.loads(pathlib.Path('.omo/ulw-loop/fresh-water-swarm-20260617/evidence/fresh-boundary.json').read_text())\nassert blocked.issubset(set(d['forbidden_proof_sources']))\nprint('FORBIDDEN_SOURCES_RECORDED')\nPY
    Expected: evidence contains `FORBIDDEN_SOURCES_RECORDED`
    Evidence: .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-1-fresh-water-swarm-validation-error.txt
  ```

  Commit: NO | Message: `chore(swarm): capture fresh validation boundary` | Files: [.omo/ulw-loop/fresh-water-swarm-20260617/evidence/fresh-boundary.json]

- [ ] 2. Add RN skill visibility prompt contract

  What to do: Write a failing test proving that a new Expo/RN worker prompt includes explicit React Native architecture/design skill context names and actionable excerpts, then update only prompt/shared-context/control-plane code until it passes. The expected permanent contract: coder/review/qa prompts for React Native Expo tasks include `react-native-architecture`, `react-native-design`, and at least one Expo/native styling instruction, alongside existing `blackcow-*` `Active Skill Source` sections.
  Must NOT do: Do not edit generated app files; do not replace embedded BlackCow source with labels; do not require workers to recursively call `run_skill`.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [4, 5, 8] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `scripts/blackcow_swarm_lib/skill_contract.py:27` - current worker prompt builder.
  - Pattern:  `scripts/blackcow_swarm_lib/skill_contract.py:60` - existing `Active Skill Source` section for BlackCow skills.
  - Pattern:  `scripts/blackcow_swarm_lib/shared_context.py:26` - design/native guidance already added to shared context.
  - Test:     `tests/test_swarm_skill_contract.py:18` - existing prompt contract test pattern.
  - API/Type: `schemas/swarm-result.schema.json:5` - result JSON remains required after prompt changes.
  - Pattern:  `/Users/jeong-yugyeong/.agents/skills/react-native-architecture/SKILL.md:12` - skill applies to new React Native/Expo projects.
  - Pattern:  `/Users/jeong-yugyeong/.agents/skills/react-native-design/SKILL.md:12` - skill applies to cross-platform mobile apps.
  - External: `https://docs.expo.dev/more/create-expo/` - Expo official project creation reference.
  - External: `https://docs.expo.dev/router/installation/` - Expo Router entry/dependency reference.

  Acceptance criteria (agent-executable only):
  - [ ] RED captured: `python3 -m unittest tests.test_swarm_skill_contract.TestSkillContractPrompt.test_react_native_worker_prompt_embeds_rn_skill_context` fails before implementation and evidence is saved to `.omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-2-red.txt`
  - [ ] GREEN captured: same command exits 0 after implementation and evidence is saved to `.omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-2-green.txt`
  - [ ] `python3 scripts/blackcow_swarm.py run --task-graph .omo/swarm/runs/fresh-water-swarm-plan/task_graph.json --dry-run --run-id fresh-water-swarm-prompt-audit` creates prompts that contain `react-native-architecture`, `react-native-design`, and `blackcow-loop`.
  - [ ] `python3 -m unittest tests.test_swarm_skill_contract` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: RN skill context appears in planned coder prompt
    Tool:     tmux
    Steps:    tmux new-session -d -s ulw-qa-C001-rn-prompt "cd /Users/jeong-yugyeong/Project/blackcow-ops; { python3 scripts/blackcow_swarm.py run --task-graph .omo/swarm/runs/fresh-water-swarm-plan/task_graph.json --dry-run --run-id fresh-water-swarm-prompt-audit; grep -R 'react-native-architecture' .omo/swarm/runs/fresh-water-swarm-prompt-audit/prompts; grep -R 'react-native-design' .omo/swarm/runs/fresh-water-swarm-prompt-audit/prompts; grep -R 'Active Skill Source' .omo/swarm/runs/fresh-water-swarm-prompt-audit/prompts; } > .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-2-fresh-water-swarm-validation.txt 2>&1"; while tmux has-session -t ulw-qa-C001-rn-prompt 2>/dev/null; do sleep 2; done; test -s .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-2-fresh-water-swarm-validation.txt
    Expected: capture contains all three grep matches
    Evidence: .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-2-fresh-water-swarm-validation.txt

  Scenario: Non-RN task does not get bogus RN context
    Tool:     bash
    Steps:    python3 scripts/blackcow_swarm.py plan "Implement team invite flow" --dry-run --run-id fresh-water-non-rn-prompt-audit > .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-2-fresh-water-swarm-validation-error.txt; python3 scripts/blackcow_swarm.py run --task-graph .omo/swarm/runs/fresh-water-non-rn-prompt-audit/task_graph.json --dry-run --run-id fresh-water-non-rn-prompt-audit >> .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-2-fresh-water-swarm-validation-error.txt; ! grep -R "react-native-architecture" .omo/swarm/runs/fresh-water-non-rn-prompt-audit/prompts >> .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-2-fresh-water-swarm-validation-error.txt
    Expected: command exits 0 because grep finds no RN skill context for non-RN task
    Evidence: .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-2-fresh-water-swarm-validation-error.txt
  ```

  Commit: YES | Message: `test(swarm): require RN skill context in worker prompts` | Files: [tests/test_swarm_skill_contract.py, scripts/blackcow_swarm_lib/skill_contract.py, scripts/blackcow_swarm_lib/shared_context.py]

- [ ] 3. Add dirty-root writer preflight contract

  What to do: Because the current checkout is dirty, define and implement deterministic writer preflight behavior before the live run. Preferred behavior: allow isolated writer worktrees from `HEAD` when dirty paths do not overlap `swarm-water-check-app/**`, `blackcow.swarm.json`, `scripts/blackcow_swarm*`, or the live run dir, and write a dirty-baseline artifact. Required fallback: if overlap exists, fail before writer execution with a structured preflight artifact and no fake `SUCCEEDED`.
  Must NOT do: Do not revert or overwrite user changes; do not clean the root checkout; do not apply generated app edits to main checkout as a workaround.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [4, 7, 8] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `scripts/blackcow_swarm_lib/worktree.py:29` - writer worktree creation currently asserts clean root.
  - Pattern:  `scripts/blackcow_swarm_lib/worktree.py:59` - current dirty-root failure message.
  - Pattern:  `scripts/blackcow_swarm_lib/scheduler.py:140` - writer worktree creation happens inside scheduler run.
  - Pattern:  `scripts/blackcow_swarm_lib/scheduler_read_guard.py:7` - existing dirty status capture/ignore pattern.
  - Test:     `tests/test_swarm_worktree.py:63` - ignored swarm artifacts behavior.
  - Test:     `tests/test_swarm_scheduler.py:143` - preexisting dirty baseline allowed for read-only tasks.
  - Pattern:  `skills/blackcow-swarm.md:65` - writer replicas must not share one checkout.

  Acceptance criteria (agent-executable only):
  - [ ] RED captured: new dirty-root writer preflight test fails before implementation and evidence is saved to `.omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-3-red.txt`.
  - [ ] GREEN captured: new test passes after implementation and evidence is saved to `.omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-3-green.txt`.
  - [ ] `python3 -m unittest tests.test_swarm_worktree tests.test_swarm_scheduler` exits 0.
  - [ ] Dirty preflight artifact exists at `.omo/swarm/runs/fresh-water-swarm-live/preflight/dirty-root.json` or a documented `FAILED_PRECONDITION` artifact exists before any Reasonix writer starts.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Dirty unrelated root paths do not block isolated writer proof
    Tool:     tmux
    Steps:    tmux new-session -d -s ulw-qa-C002-dirty "cd /Users/jeong-yugyeong/Project/blackcow-ops; git status --short > .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-3-root-status.txt; python3 -m unittest tests.test_swarm_worktree tests.test_swarm_scheduler > .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-3-fresh-water-swarm-validation.txt 2>&1"; while tmux has-session -t ulw-qa-C002-dirty 2>/dev/null; do sleep 2; done; test -s .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-3-fresh-water-swarm-validation.txt
    Expected: unittest output reports OK and root status artifact is present
    Evidence: .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-3-fresh-water-swarm-validation.txt

  Scenario: Dirty target path fails before writer execution
    Tool:     bash
    Steps:    python3 -m unittest tests.test_swarm_worktree.TestWorktree.test_dirty_target_path_blocks_writer_preflight > .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-3-fresh-water-swarm-validation-error.txt 2>&1
    Expected: evidence contains `OK` and the test asserts no worker `result.json` is created after target-overlap preflight failure
    Evidence: .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-3-fresh-water-swarm-validation-error.txt
  ```

  Commit: YES | Message: `fix(swarm): handle dirty root writer preflight explicitly` | Files: [scripts/blackcow_swarm_lib/worktree.py, scripts/blackcow_swarm_lib/scheduler.py, scripts/blackcow_swarm_lib/scheduler_read_guard.py, tests/test_swarm_worktree.py, tests/test_swarm_scheduler.py]

- [ ] 4. Run fresh live Reasonix swarm and measure elapsed time

  What to do: Execute the live run once prerequisites pass. Capture wall-clock start/end, `/usr/bin/time -p`, command transcript, `status`, `events.jsonl`, worker directories, and final judgement. If live Reasonix command shape is unavailable, stop and treat it as control-plane failure evidence under Task 7.
  Must NOT do: Do not run `--dry-run` as live proof; do not switch to mock runner for C001; do not manually patch `swarm-water-check-app`.

  Parallelization: Can parallel: NO | Wave 2 | Blocks: [5, 6, 7, 8] | Blocked by: [1, 2, 3]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `skills/blackcow-swarm.md:29` - internal control-plane run command contract.
  - API/Type: `scripts/blackcow_swarm_lib/cli.py:154` - run dispatch selects dry-run, mock, or Reasonix.
  - API/Type: `scripts/blackcow_swarm_lib/lifecycle.py:127` - live Reasonix run entrypoint.
  - API/Type: `scripts/blackcow_swarm_lib/runner.py:136` - Reasonix runner process execution.
  - Pattern:  `.omo/swarm/runs/fresh-water-swarm-plan/task_graph.json:47` - coder task has 6 replicas in dry-run graph.
  - Pattern:  `skills/blackcow-swarm.md:140` - do not pretend dry-run is a live writer swarm.

  Acceptance criteria (agent-executable only):
  - [ ] `.omo/ulw-loop/fresh-water-swarm-20260617/evidence/C001-live-run.tmux.txt` exists and contains the live command.
  - [ ] `.omo/ulw-loop/fresh-water-swarm-20260617/evidence/C001-live-time.txt` exists and contains `real`.
  - [ ] `.omo/swarm/runs/fresh-water-swarm-live/state.json` exists.
  - [ ] `.omo/swarm/runs/fresh-water-swarm-live/events.jsonl` exists.
  - [ ] `.omo/swarm/runs/fresh-water-swarm-live/final_judgement.json` exists, even if status is `FAILED`.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Live swarm command runs under tmux with timing
    Tool:     tmux
    Steps:    tmux new-session -d -s ulw-qa-C001-live "cd /Users/jeong-yugyeong/Project/blackcow-ops; mkdir -p .omo/ulw-loop/fresh-water-swarm-20260617/evidence; echo 'COMMAND: python3 scripts/blackcow_swarm.py run --task-graph .omo/swarm/runs/fresh-water-swarm-plan/task_graph.json --runner reasonix --run-id fresh-water-swarm-live' > .omo/ulw-loop/fresh-water-swarm-20260617/evidence/C001-live-run.tmux.txt; date -u +'%Y-%m-%dT%H:%M:%SZ' > .omo/ulw-loop/fresh-water-swarm-20260617/evidence/C001-live-start.txt; /usr/bin/time -p python3 scripts/blackcow_swarm.py run --task-graph .omo/swarm/runs/fresh-water-swarm-plan/task_graph.json --runner reasonix --run-id fresh-water-swarm-live > .omo/ulw-loop/fresh-water-swarm-20260617/evidence/C001-live-run.out 2> .omo/ulw-loop/fresh-water-swarm-20260617/evidence/C001-live-time.txt; code=\$?; echo EXIT:\$code >> .omo/ulw-loop/fresh-water-swarm-20260617/evidence/C001-live-run.tmux.txt; date -u +'%Y-%m-%dT%H:%M:%SZ' > .omo/ulw-loop/fresh-water-swarm-20260617/evidence/C001-live-end.txt; exit \$code"; while tmux has-session -t ulw-qa-C001-live 2>/dev/null; do sleep 10; done; cat .omo/ulw-loop/fresh-water-swarm-20260617/evidence/C001-live-run.out >> .omo/ulw-loop/fresh-water-swarm-20260617/evidence/C001-live-run.tmux.txt; cat .omo/ulw-loop/fresh-water-swarm-20260617/evidence/C001-live-time.txt >> .omo/ulw-loop/fresh-water-swarm-20260617/evidence/C001-live-run.tmux.txt
    Expected: tmux capture contains `EXIT:0` for happy path or nonzero exit with structured failure artifacts for Task 7
    Evidence: .omo/ulw-loop/fresh-water-swarm-20260617/evidence/C001-live-run.tmux.txt

  Scenario: Dry-run cannot satisfy live proof
    Tool:     bash
    Steps:    python3 - <<'PY' > .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-4-fresh-water-swarm-validation-error.txt\nimport json, pathlib\nstate=pathlib.Path('.omo/swarm/runs/fresh-water-swarm-live/state.json')\nassert state.exists(), 'live state missing'\np=json.loads(state.read_text())\nassert p.get('status') != 'DRY_RUN', p.get('status')\nprint('LIVE_STATE_NOT_DRY_RUN')\nPY
    Expected: evidence contains `LIVE_STATE_NOT_DRY_RUN`
    Evidence: .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-4-fresh-water-swarm-validation-error.txt
  ```

  Commit: NO | Message: `chore(swarm): capture fresh live run evidence` | Files: [.omo/swarm/runs/fresh-water-swarm-live/**, .omo/ulw-loop/fresh-water-swarm-20260617/evidence/**]

- [ ] 5. Audit worker prompts, transcripts, results, and skill usage

  What to do: Inspect `.omo/swarm/runs/fresh-water-swarm-live/workers/*/prompt.md`, `reasonix-transcript.jsonl`, `stdout.log`, `stderr.log`, and `result.json`. Prove every worker used valid `blackcow-*` skill context, coder/review/qa prompts include RN skill context, result JSON is schema-valid, and no transcript weakens checks or claims success without artifacts.
  Must NOT do: Do not infer skill usage from task labels alone; do not ignore missing transcripts; do not accept stdout prose as success.

  Parallelization: Can parallel: YES | Wave 2 | Blocks: [7, 8] | Blocked by: [4]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `scripts/blackcow_swarm_lib/skill_contract.py:40` - prompt starts as BlackCow skill-backed worker.
  - Pattern:  `scripts/blackcow_swarm_lib/skill_contract.py:63` - cross-skill evidence contract.
  - Pattern:  `scripts/blackcow_reasonix_acp_worker.py:157` - default transcript path.
  - API/Type: `scripts/blackcow_reasonix_acp_worker.py:140` - result JSON validation helper.
  - API/Type: `scripts/blackcow_swarm_lib/runner.py:188` - invalid/missing results become retryable/final failures.
  - Pattern:  `skills/blackcow-swarm.md:222` - required output evidence paths.

  Acceptance criteria (agent-executable only):
  - [ ] `python3 - <<'PY' ...` validates every worker `result.json` with `scripts.blackcow_swarm_lib.schema.validate_result`.
  - [ ] `grep -R "Active Skill Source" .omo/swarm/runs/fresh-water-swarm-live/workers` finds all prompt files.
  - [ ] `grep -R "react-native-architecture" .omo/swarm/runs/fresh-water-swarm-live/workers` finds coder/review/qa prompts for RN task.
  - [ ] `grep -R "react-native-design" .omo/swarm/runs/fresh-water-swarm-live/workers` finds coder/review/qa prompts for RN task.
  - [ ] Audit script writes `.omo/ulw-loop/fresh-water-swarm-20260617/evidence/worker-skill-audit.json` with `status=PASS`.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Worker skill audit passes
    Tool:     bash
    Steps:    python3 scripts/blackcow_audit_worker_skills.py --run-dir .omo/swarm/runs/fresh-water-swarm-live --require blackcow-loop --require blackcow-qa --require blackcow-plan --require react-native-architecture --require react-native-design --output .omo/ulw-loop/fresh-water-swarm-20260617/evidence/worker-skill-audit.json > .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-5-fresh-water-swarm-validation.txt 2>&1
    Expected: command exits 0 and JSON output has `status` equal `PASS`
    Evidence: .omo/ulw-loop/fresh-water-swarm-20260617/evidence/worker-skill-audit.json

  Scenario: Missing RN skill context is detected
    Tool:     bash
    Steps:    python3 scripts/blackcow_audit_worker_skills.py --run-dir .omo/swarm/runs/fresh-water-swarm-live --require react-native-architecture --require react-native-design --simulate-missing react-native-design --output .omo/ulw-loop/fresh-water-swarm-20260617/evidence/worker-skill-audit-negative.json > .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-5-fresh-water-swarm-validation-error.txt 2>&1; test $? -ne 0
    Expected: command exits nonzero and negative JSON names `react-native-design` as missing
    Evidence: .omo/ulw-loop/fresh-water-swarm-20260617/evidence/worker-skill-audit-negative.json
  ```

  Commit: YES | Message: `test(swarm): audit worker skill usage artifacts` | Files: [scripts/blackcow_audit_worker_skills.py, tests/test_swarm_skill_contract.py]

- [ ] 6. Execute acceptance, native/web smoke, visual, and speed gates

  What to do: Re-run the exact acceptance commands from the dry-run graph, substituting `fresh-water-swarm-live` for screenshot/review/speed run-dir paths where needed. Store stdout/stderr for every check. Confirm app existence, typecheck, lint, design gate, native smoke, web smoke, Expo native screenshot/visual review, and speed gate.
  Must NOT do: Do not replace browser/native gates with weaker curl-only checks; do not accept `Something went wrong`; do not accept a simulator home screen or missing `Water` text.

  Parallelization: Can parallel: YES | Wave 3 | Blocks: [7, 8] | Blocked by: [4]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `scripts/blackcow_swarm_lib/acceptance.py:86` - new Expo project acceptance checks.
  - Pattern:  `scripts/blackcow_swarm_lib/task_graph.py:193` - run-level native visual and speed checks.
  - API/Type: `scripts/blackcow_swarm_lib/acceptance_runner.py:20` - acceptance runner writes stdout/stderr and feedback.
  - API/Type: `scripts/blackcow_swarm_lib/design_gate.py:7` - accepted design source filenames.
  - API/Type: `scripts/blackcow_swarm_lib/expo_native_smoke.py:22` - Expo native smoke launches the app and runs visual review.
  - API/Type: `scripts/blackcow_swarm_lib/web_smoke.py:22` - managed web smoke starts app and uses browser smoke.
  - API/Type: `scripts/blackcow_swarm_lib/speed_gate.py:16` - speed gate computes serial duration divided by wall time.

  Acceptance criteria (agent-executable only):
  - [ ] `test -f swarm-water-check-app/package.json`
  - [ ] `cd swarm-water-check-app && npm run typecheck`
  - [ ] `cd swarm-water-check-app && npm run lint`
  - [ ] `python3 scripts/blackcow_design_gate.py --project swarm-water-check-app`
  - [ ] `python3 scripts/blackcow_native_smoke.py --project swarm-water-check-app --platform ios`
  - [ ] `python3 scripts/blackcow_web_smoke.py --project swarm-water-check-app --port 8088 --expect Water --reject 'Something went wrong'`
  - [ ] `python3 scripts/blackcow_expo_native_smoke.py --project swarm-water-check-app --platform ios --screenshot .omo/swarm/runs/fresh-water-swarm-live/screenshots/ios.png --review-output .omo/swarm/runs/fresh-water-swarm-live/visual-review.md --expect Water`
  - [ ] `python3 scripts/blackcow_speed_gate.py --run-dir .omo/swarm/runs/fresh-water-swarm-live --min-speedup 1.1`

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: C001 acceptance suite passes end to end
    Tool:     tmux
    Steps:    tmux new-session -d -s ulw-qa-C001-acceptance "cd /Users/jeong-yugyeong/Project/blackcow-ops; { set -e; test -f swarm-water-check-app/package.json; cd swarm-water-check-app; npm run typecheck; npm run lint; cd ..; python3 scripts/blackcow_design_gate.py --project swarm-water-check-app; python3 scripts/blackcow_native_smoke.py --project swarm-water-check-app --platform ios; python3 scripts/blackcow_web_smoke.py --project swarm-water-check-app --port 8088 --expect Water --reject 'Something went wrong'; python3 scripts/blackcow_expo_native_smoke.py --project swarm-water-check-app --platform ios --screenshot .omo/swarm/runs/fresh-water-swarm-live/screenshots/ios.png --review-output .omo/swarm/runs/fresh-water-swarm-live/visual-review.md --expect Water; python3 scripts/blackcow_speed_gate.py --run-dir .omo/swarm/runs/fresh-water-swarm-live --min-speedup 1.1; } > .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-6-fresh-water-swarm-validation.txt 2>&1"; while tmux has-session -t ulw-qa-C001-acceptance 2>/dev/null; do sleep 10; done; test -s .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-6-fresh-water-swarm-validation.txt
    Expected: capture contains no failing command; screenshot and visual review files exist
    Evidence: .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-6-fresh-water-swarm-validation.txt

  Scenario: Runtime error text is rejected
    Tool:     bash
    Steps:    python3 scripts/blackcow_web_smoke.py --project swarm-water-check-app --port 8088 --expect Water --reject 'Something went wrong' > .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-6-fresh-water-swarm-validation-error.txt 2>&1
    Expected: command exits 0 only when browser output contains `Water` and does not contain `Something went wrong`
    Evidence: .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-6-fresh-water-swarm-validation-error.txt
  ```

  Commit: NO | Message: `test(swarm-water): verify generated app gates` | Files: [.omo/swarm/runs/fresh-water-swarm-live/acceptance/**, .omo/swarm/runs/fresh-water-swarm-live/screenshots/**, .omo/swarm/runs/fresh-water-swarm-live/visual-review.md]

- [ ] 7. Run control-plane RED to GREEN loop for any failed gate

  What to do: For each failure from Tasks 4-6, create a failure packet under `.omo/swarm/runs/fresh-water-swarm-live/feedback/`, write a focused failing control-plane test first, then modify only swarm control-plane/prompt/gate code until the test and failed scenario pass. Re-run the live or minimal reproducer after each fix. Examples: app missing required script means prompt/task-graph defect; native smoke screenshots wrong app means native gate defect; skill audit fail means prompt contract defect; speed gate fail means timing/scheduler defect.
  Must NOT do: Do not edit `swarm-water-check-app/**` directly; do not skip tests; do not weaken acceptance; do not continue after two identical failed fix attempts without recording blocker and escalating to final review as blocked.

  Parallelization: Can parallel: NO | Wave 3 | Blocks: [8] | Blocked by: [5, 6]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `skills/blackcow-swarm.md:155` - failed gates must re-enter coder/review/qa instead of one-to-one user ping-pong.
  - Pattern:  `skills/blackcow-swarm.md:157` - failure feedback packet content.
  - API/Type: `scripts/blackcow_swarm_lib/acceptance_runner.py:68` - feedback packet writer.
  - Pattern:  `scripts/blackcow_swarm_lib/lifecycle_completion.py:48` - acceptance runs before final status.
  - Pattern:  `scripts/blackcow_swarm_lib/judge.py:31` - final judgement writer.
  - Test:     `tests/test_swarm_skill_contract.py:42` - acceptance failure feedback test.

  Acceptance criteria (agent-executable only):
  - [ ] For every failed live gate, `.omo/swarm/runs/fresh-water-swarm-live/feedback/*.json` exists with command, exit code, stdout, stderr, and artifact paths.
  - [ ] Every control-plane change has paired RED evidence `task-7-<slug>-red.txt` and GREEN evidence `task-7-<slug>-green.txt`.
  - [ ] `git diff --name-only` for executor-authored fixes excludes `swarm-water-check-app/**`.
  - [ ] The originally failed scenario from Task 4, 5, or 6 passes after the control-plane fix.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Failed gate produces feedback and no app hand-edit
    Tool:     bash
    Steps:    python3 - <<'PY' > .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-7-fresh-water-swarm-validation.txt\nimport pathlib, subprocess\nfeedback=pathlib.Path('.omo/swarm/runs/fresh-water-swarm-live/feedback')\nprint('feedback_files', sorted(str(p) for p in feedback.glob('*.json')) if feedback.exists() else [])\ndiff=subprocess.run(['git','diff','--name-only'], text=True, capture_output=True, check=False).stdout.splitlines()\nmanual_app_edits=[p for p in diff if p.startswith('swarm-water-check-app/')]\nassert not manual_app_edits, manual_app_edits\nprint('NO_MANUAL_APP_EDITS')\nPY
    Expected: evidence contains `NO_MANUAL_APP_EDITS`
    Evidence: .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-7-fresh-water-swarm-validation.txt

  Scenario: Repeated same blocker stops after two attempts
    Tool:     bash
    Steps:    test -f .omo/ulw-loop/fresh-water-swarm-20260617/evidence/repeated-blocker-policy.txt && grep -q 'STOP_AFTER_TWO_IDENTICAL_FAILURES' .omo/ulw-loop/fresh-water-swarm-20260617/evidence/repeated-blocker-policy.txt > .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-7-fresh-water-swarm-validation-error.txt
    Expected: evidence command exits 0 and policy artifact names the repeated blocker rule
    Evidence: .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-7-fresh-water-swarm-validation-error.txt
  ```

  Commit: YES | Message: `fix(swarm): close fresh water validation gate failure` | Files: [scripts/blackcow_swarm.py, scripts/blackcow_reasonix_acp_worker.py, scripts/blackcow_swarm_lib/**, tests/test_swarm_*.py, schemas/**, skills/blackcow-*.md]

- [ ] 8. Assemble final review gate packet and commit-ready state

  What to do: Create `.omo/ulw-loop/fresh-water-swarm-20260617/final-review-entry.md` with C001-C003 results, artifact paths, reviewer checklist, open risks, and commit list. Enter final review only if all entry conditions below pass.
  Must NOT do: Do not declare complete before final review; do not omit failed-gate history; do not hide dirty-root baseline.

  Parallelization: Can parallel: NO | Wave 4 | Blocks: [final verification] | Blocked by: [5, 6, 7]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `skills/blackcow-swarm.md:206` - output contract fields.
  - Pattern:  `skills/blackcow-swarm.md:222` - required evidence list.
  - Pattern:  `scripts/blackcow_swarm_lib/speed_gate.py:39` - speedup calculation fields.
  - Pattern:  `scripts/blackcow_swarm_lib/schema.py:76` - final judgement validation contract.
  - Test:     `tests/test_swarm_design_native_speed_gates.py:102` - speed gate timing evidence test.

  Acceptance criteria (agent-executable only):
  - [ ] `python3 scripts/blackcow_speed_gate.py --run-dir .omo/swarm/runs/fresh-water-swarm-live --min-speedup 1.1`
  - [ ] `python3 - <<'PY'\nimport json, pathlib\np=pathlib.Path('.omo/swarm/runs/fresh-water-swarm-live/final_judgement.json')\nd=json.loads(p.read_text())\nassert d['status']=='SUCCEEDED', d\nPY`
  - [ ] `test -f .omo/swarm/runs/fresh-water-swarm-live/screenshots/ios.png`
  - [ ] `test -f .omo/swarm/runs/fresh-water-swarm-live/visual-review.md`
  - [ ] `test -f .omo/ulw-loop/fresh-water-swarm-20260617/final-review-entry.md`
  - [ ] `python3 -m unittest discover -s tests -p 'test_swarm_*.py'`

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Final review entry conditions all pass
    Tool:     tmux
    Steps:    tmux new-session -d -s ulw-qa-C003-final "cd /Users/jeong-yugyeong/Project/blackcow-ops; { set -e; python3 -m unittest discover -s tests -p 'test_swarm_*.py'; python3 scripts/blackcow_speed_gate.py --run-dir .omo/swarm/runs/fresh-water-swarm-live --min-speedup 1.1; test -f .omo/swarm/runs/fresh-water-swarm-live/final_judgement.json; test -f .omo/ulw-loop/fresh-water-swarm-20260617/final-review-entry.md; } > .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-8-fresh-water-swarm-validation.txt 2>&1"; while tmux has-session -t ulw-qa-C003-final 2>/dev/null; do sleep 10; done; test -s .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-8-fresh-water-swarm-validation.txt
    Expected: tmux capture shows unittest OK and speed gate pass
    Evidence: .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-8-fresh-water-swarm-validation.txt

  Scenario: Final review blocks if feedback remains open
    Tool:     bash
    Steps:    python3 - <<'PY' > .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-8-fresh-water-swarm-validation-error.txt\nimport json, pathlib\nfeedback=pathlib.Path('.omo/swarm/runs/fresh-water-swarm-live/feedback')\nopen_items=[]\nif feedback.exists():\n  for path in feedback.glob('*.json'):\n    data=json.loads(path.read_text())\n    if not data.get('resolved_by'):\n      open_items.append(str(path))\nassert not open_items, open_items\nprint('NO_OPEN_FEEDBACK')\nPY
    Expected: evidence contains `NO_OPEN_FEEDBACK`
    Evidence: .omo/ulw-loop/fresh-water-swarm-20260617/evidence/task-8-fresh-water-swarm-validation-error.txt
  ```

  Commit: YES | Message: `feat(swarm-water): generate validated water check app via swarm` | Files: [swarm-water-check-app/**, .omo/ulw-loop/fresh-water-swarm-20260617/final-review-entry.md]

## Final verification wave (MANDATORY - after all implementation tasks)
> Runs in PARALLEL. ALL must APPROVE. Surface results to the caller and wait for an explicit "okay" before declaring complete.
- [ ] F1. Plan compliance audit - every task done, every acceptance criterion met
- [ ] F2. Code quality review - diagnostics clean, idioms match, no dead code
- [ ] F3. Real manual QA - every QA scenario executed with evidence captured
- [ ] F4. Scope fidelity - nothing extra shipped beyond Must-Have, nothing Must-NOT-Have introduced

### Final review gate entry conditions
- C001, C002, and C003 are each marked PASS in `.omo/ulw-loop/fresh-water-swarm-20260617/final-review-entry.md`.
- `fresh-water-swarm-live` is a live Reasonix run, not dry-run or mock.
- `final_judgement.json` is schema-valid and `status=SUCCEEDED`.
- Every worker has valid `result.json`; every writer transcript exists or has structured runner failure evidence.
- Prompt/transcript audit proves visible `blackcow-*`, `react-native-architecture`, and `react-native-design` usage.
- Acceptance logs prove package, typecheck, lint, design, native, web, Expo native visual, and speed gates.
- No app hand-edits exist outside worker-generated/selected patch provenance.
- All control-plane fixes have RED and GREEN evidence.
- Open feedback packets are zero, or final review status is `BLOCKED` rather than complete.

## Commit strategy
- One logical change per commit. Conventional Commits (`<type>(<scope>): <subject>` body + footer).
- Atomic: every commit builds and passes tests on its own.
- No "WIP" / "fix typo squash later" commits on the final branch - clean up before merge.
- Commit control-plane fixes before generated app output.
- Reference the plan file path in the final commit footer: `Plan: plans/fresh-water-swarm-validation.md`.

## Success criteria
- All Must-Have shipped; all QA scenarios pass with captured evidence; F1-F4 approved; commit history clean.
