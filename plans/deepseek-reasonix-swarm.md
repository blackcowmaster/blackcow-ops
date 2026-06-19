# DeepSeek Reasonix Swarm Implementation Plan

## TL;DR
> **Summary**: Add a local BlackCow Swarm control plane that runs DeepSeek through configurable Reasonix worker processes, starts with safe read-only/QA parallelism, then adds isolated writer worktrees, race groups, patch tournaments, resume/cancel, and cross-skill integration.
> **Deliverables**:
> - `skills/blackcow-swarm.md` as the 8th BlackCow skill, plus updates to `blackcow-loop`, `blackcow-plan`, `blackcow-qa`, installer, README files, and ecosystem validators.
> - `scripts/blackcow_swarm.py` CLI entrypoint plus importable stdlib Python modules under `scripts/blackcow_swarm_lib/`.
> - JSON schemas, root `blackcow.swarm.json`, stdlib `unittest` suite, shell contract tests, deterministic fixtures, and manual-QA evidence commands.
> - Runtime state under `.omo/swarm/runs/<run_id>/` and isolated writer worktrees under `.worktrees/swarm/<run_id>/`.
> **Effort**: XL
> **Parallel**: YES - 3 waves
> **Critical Path**: Task 1 -> Task 2 -> Task 6 -> Task 7 -> Task 8 -> Task 9 -> Task 10 -> Task 12

## Context
### Original Request
- User asked to read the attached DeepSeek/Reasonix agent swarm implementation prompt and design a plan.
- Source prompt: `/Users/jeong-yugyeong/.codex/attachments/9436e3b9-a9b4-43da-a470-0641181895f5/pasted-text.txt`.
- Prompt requires real local process orchestration, not prose-only parallelism: DeepSeek is the worker engine, Reasonix is the worker runtime, and BlackCow Swarm is the scheduler/control plane.

### Interview Summary
- No blocking user questions remain. The prompt gives UX, scope, non-goals, file targets, runtime layout, CLI commands, acceptance criteria, test scenarios, and implementation priority.
- This is an architecture-tier brownfield plan. Existing BlackCow skills and shell validators must be updated coherently rather than adding an isolated script.
- Planning-only mode: this plan is the deliverable; no production code should be changed by the planner.

### Metis Review (gaps addressed)
- **Default behavior conflict**: Plain `blackcow-loop "task"` must keep existing non-swarm TRY/governance behavior. Swarm activates only when a swarm flag is present or the user explicitly invokes `blackcow-swarm`. `blackcow.swarm.json` may default `default_policy: auto` inside the swarm subsystem, but `blackcow-loop` must not auto-delegate without explicit swarm activation.
- **Dangerous writer approval**: In `policy=auto`, risky writer surfaces produce `requires_approval: true` and do not run writer swarm unless `--yes` is provided. `--dry-run` never requires approval because it does not run workers.
- **Runner placeholders**: `ReasonixRunner` validates only these placeholders: `{skill}`, `{prompt_file}`, `{result_json}`, `{workspace}`, `{run_id}`, `{task_id}`, `{replica_id}`. Missing `{skill}`, `{prompt_file}`, or `{result_json}` is fatal; unknown placeholders are fatal.
- **Patch tie-break**: Tournament order is deterministic: applies cleanly, changed tests pass, no high security risk, higher `score.overall`, smaller changed-line count, earlier completion time, lexical `replica_id`.
- **Concurrency proof**: `MockRunner` records `started_at` and `finished_at`; tests assert overlapping intervals and wall-clock below serial threshold.
- **Cancel semantics**: `cancel` marks pending tasks `CANCELLED`, sends SIGTERM to active worker PIDs, escalates to SIGKILL after a configurable grace period, and records events.
- **Cleanup semantics**: Default cleanup preserves `estimate.json`, `task_graph.json`, `state.json`, `events.jsonl`, `final_judgement.json`, worker `result.json`, and reports. It removes worktrees and large stdout/stderr logs/patches according to loser policy. No purge mode in MVP.
- **Dependency policy**: MVP uses Python 3.11+ and stdlib only. Tests use `unittest`; JSON schema files are validated by an in-repo minimal validator for the prompt-required fields/enums instead of adding `jsonschema`. Config uses JSON (`blackcow.swarm.json`) so stdlib-only remains honest; YAML/TOML config is explicitly postponed until a dependency or parser decision is accepted.
- **Patch safety corrections from high-accuracy review**: Patch extraction must stage all changes with `git -C <worker_tree> add -A` and write `git -C <worker_tree> diff --cached --binary > <patch_path>` so new, deleted, and binary files are represented. Default patch application target is `.worktrees/swarm/<run_id>/integration`; `--apply-target=main` is an explicit dangerous mode only. Dependent writer worktrees are based on the current integration checkpoint after upstream winning patches, not always the original base commit.
- **Runtime safety corrections from high-accuracy review**: Scheduler owns process heartbeat and launches worker process groups; worker heartbeat is optional progress evidence. Missing/invalid `result.json` is `FAILED_RETRYABLE`, not success. Worker prompts include anti-gaming rules forbidding changed check commands, skipped/deleted tests, weakened assertions, fake exit conditions, and fake result JSON.
- **Import layout**: Avoid `scripts/blackcow_swarm.py` vs package-name ambiguity by placing modules under `scripts/blackcow_swarm_lib/`.
- **Runtime artifact policy**: Add `.omo/swarm/runs/` and `.worktrees/swarm/` to `.gitignore`; track schemas, config, tests, fixtures, and skill/docs only.

## Work Objectives
### Core Objective
Implement a local DeepSeek/Reasonix swarm runtime for BlackCow that can estimate tasks, build DAG task graphs, run read-only and writer workers safely, select candidate patches, resume/cancel/cleanup runs, and integrate with existing BlackCow skills without breaking the current default flow.

### Deliverables
- New files:
  - `skills/blackcow-swarm.md`
  - `scripts/blackcow_swarm.py`
  - `scripts/blackcow_swarm_lib/{__init__.py,cli.py,config.py,estimate.py,schema.py,task_graph.py,state.py,runner.py,scheduler.py,worktree.py,tournament.py,judge.py}`
  - `schemas/swarm-task.schema.json`, `schemas/swarm-result.schema.json`, `schemas/swarm-estimate.schema.json`, `schemas/swarm-final-judgement.schema.json`
  - `blackcow.swarm.json`
  - `tests/test_swarm_*.py`, `tests/fixtures/*.json`
  - `skills/tests/validate-blackcow-swarm.sh`
- Modified files:
  - `skills/blackcow-loop.md`, `skills/blackcow-plan.md`, `skills/blackcow-qa.md`, `skills/install.sh`
  - `skills/tests/validate-blackcow-ecosystem.sh`, `skills/tests/validate-cross-skill-contract.sh`, related skill integration tests
  - `README.md`, `README.ko.md`, `README.ja.md`, `README.zh-cn.md`, `.gitignore`

### Definition of Done (verifiable conditions with commands)
- `python scripts/blackcow_swarm.py --help` exits 0 and lists `estimate plan run resume cancel status cleanup`.
- `python scripts/blackcow_swarm.py estimate "Implement team invite flow" --intensity high` emits valid estimate JSON.
- `python scripts/blackcow_swarm.py plan "Implement team invite flow" --intensity high --dry-run` writes `.omo/swarm/runs/<run_id>/task_graph.json`.
- `python scripts/blackcow_swarm.py run --task-graph tests/fixtures/task_graph.simple.json --dry-run` prints worker commands and does not invoke Reasonix.
- `python -m unittest discover -s tests -p 'test_swarm_*.py'` passes.
- `bash skills/tests/validate-blackcow-swarm.sh` passes.
- `bash skills/tests/validate-blackcow-ecosystem.sh --quiet` passes with the 8-skill topology.
- `bash skills/install.sh --dry-run` includes `blackcow-swarm.md`.

### Must Have
- No Kimi.
- No direct DeepSeek API calls in MVP; workers run through configurable Reasonix command templates.
- `MockRunner` for deterministic tests without Reasonix.
- Read-only workers restricted to run artifact writes only.
- Writer workers always use git worktrees; winning patches are applied to the dedicated integration worktree by default. Main checkout mutation is allowed only through explicit `--apply-target=main --yes`.
- `normal`, `high`, and `max` intensity profiles from the prompt.
- `off`, `suggest`, `auto`, `force` policies and `serial`, `qa`, `discovery`, `review`, `coder`, `full`, `adaptive` modes.
- Heartbeat, timeout, retry, resume, cancel, status, cleanup, final judgement.
- Existing `blackcow-loop` non-swarm behavior preserved.

### Must NOT Have
- No Kubernetes or remote worker cluster.
- No mandatory DB server.
- No full automatic deployment.
- No writer swarm for dangerous surfaces in auto mode without `--yes`.
- No shell command construction with `shell=True`; command templates must execute as argument lists.
- No runtime artifacts tracked in git.
- No Ponytail or looping-skills dependency in MVP; only anti-gaming and independent verifier principles are adopted now.

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: TDD with stdlib `unittest` for Python runtime; shell contract tests for skills/installer; no pytest dependency.
- QA policy: Every task has exact command scenarios and evidence paths.
- Evidence: `evidence/task-{N}-{slug}.txt` or JSON artifacts under `evidence/`.
- Manual-QA channel for CLI/data-shaped criteria: bash/tmux command transcripts. Browser/computer-use not applicable because the surface is CLI plus files.

## Execution Strategy
### Parallel Execution Waves
Wave 1: [1, 2, 3, 4]
- Foundation with no production worker execution: CLI/module skeleton, config/profiles/estimator, schemas/fixtures, new skill ecosystem registration.

Wave 2: [5, 6, 7, 8]
- Runtime core: task graph, runner abstraction, state/events, scheduler/read-only/dry-run.

Wave 3: [9, 10, 11, 12]
- Write-capable orchestration and integrations: worktrees, race/tournament/judge, heartbeat/resume/cancel/cleanup/throttle, cross-skill loop/plan/qa and final ecosystem validation.

### Dependency Matrix (full, all tasks)
| Task | Depends On | Blocks |
|---|---|---|
| 1 | none | 5, 6, 7 |
| 2 | none | 5, 6, 7, 8, 11 |
| 3 | none | 5, 6, 7, 8, 10 |
| 4 | none | 12 |
| 5 | 1, 2, 3 | 8, 12 |
| 6 | 1, 2, 3 | 7, 8, 9, 10, 11 |
| 7 | 1, 2, 6 | 8, 11 |
| 8 | 5, 6, 7 | 9, 10, 11, 12 |
| 9 | 6, 8 | 10 |
| 10 | 6, 8, 9 | 12 |
| 11 | 2, 6, 8 | 12 |
| 12 | 4, 5, 8, 10, 11 | final |

## TODOs
> Implementation + Test = ONE task. Never separate.
> EVERY task MUST have: References + Acceptance Criteria + QA Scenarios.

- [x] 1. Build CLI and stdlib Python module skeleton

  **What to do**: Add `scripts/blackcow_swarm.py` as a thin entrypoint importing `scripts/blackcow_swarm_lib/cli.py`. Add `argparse` subcommands `estimate`, `plan`, `run`, `resume`, `cancel`, `status`, `cleanup`. Add `tests/test_swarm_cli.py` first with RED assertions for missing help/subcommands, then implement. Use Python 3.11+ stdlib only.
  **Must NOT do**: Do not execute Reasonix. Do not add pytest/jsonschema/PyYAML. Do not create a package named `scripts/blackcow_swarm/`.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: [5, 6, 7] | Blocked By: []

  **References**:
  - Pattern: `package.json:6` - existing project commands show repo already has Node scripts, so Python runtime must be explicit and separate.
  - Pattern: `skills/tests/validate-blackcow-plan-contract.sh:45` - existing contract tests start with file existence and frontmatter/shape checks.
  - API/Type: `pasted-text.txt:1026` - required swarm CLI subcommands.
  - External: `https://docs.python.org/3/library/argparse.html` - official `argparse` behavior.

  **Acceptance Criteria**:
  - [ ] `python -m unittest tests.test_swarm_cli.TestCli.test_help_lists_all_subcommands` fails before implementation and passes after.
  - [ ] `python scripts/blackcow_swarm.py --help` exits 0 and stdout contains `estimate`, `plan`, `run`, `resume`, `cancel`, `status`, `cleanup`.
  - [ ] `python scripts/blackcow_swarm.py run --help` exits 0 and stdout contains `--task-graph`, `--dry-run`, `--mode`, `--intensity`, `--max-workers`.
  - [ ] `python scripts/blackcow_swarm.py nope` exits non-zero and stderr contains `invalid choice`.

  **QA Scenarios**:
  ```
  Scenario: CLI help happy path
    Tool: bash
    Steps: mkdir -p evidence && python scripts/blackcow_swarm.py --help > evidence/task-1-cli-help.txt
    Expected: evidence/task-1-cli-help.txt contains all seven subcommands.
    Evidence: evidence/task-1-cli-help.txt

  Scenario: Invalid subcommand failure
    Tool: bash
    Steps: mkdir -p evidence && (python scripts/blackcow_swarm.py nope > evidence/task-1-invalid.out 2> evidence/task-1-invalid.err; echo $? > evidence/task-1-invalid.code)
    Expected: evidence/task-1-invalid.code is non-zero and stderr contains invalid choice.
    Evidence: evidence/task-1-invalid.err
  ```

  **Commit**: YES | Message: `feat(swarm): add cli skeleton` | Files: `scripts/blackcow_swarm.py`, `scripts/blackcow_swarm_lib/__init__.py`, `scripts/blackcow_swarm_lib/cli.py`, `tests/test_swarm_cli.py`

- [x] 2. Add JSON config loader, intensity profiles, and estimator policy

  **What to do**: Add root `blackcow.swarm.json` with the prompt's defaults and normal/high/max profiles. Implement stdlib JSON config parsing and CLI override merging in `config.py`. Implement `estimate.py` with the prompt's JSON output, heuristic thresholds, auto policy, and dangerous writer detection. Add tests first for default profiles, CLI overrides, runner command template placeholder validation, tiny task auto rejection, high adaptive recommendation, and risky writer approval.
  **Must NOT do**: Do not let `blackcow-loop` auto-delegate merely because config says `default_policy: auto`. Do not use `shell=True` or unvalidated template placeholders. Do not add YAML/TOML config in MVP.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: [5, 6, 7, 8, 11] | Blocked By: []

  **References**:
  - API/Type: `pasted-text.txt:138` - use root config when no `config/` directory exists.
  - API/Type: `pasted-text.txt:146` - configurable Reasonix command template.
  - API/Type: `pasted-text.txt:175` - policy/mode/intensity enums.
  - API/Type: `pasted-text.txt:251` - profile values.
  - API/Type: `pasted-text.txt:306` - estimator JSON fields.
  - API/Type: `pasted-text.txt:354` - auto execution criteria and risky write surfaces.
  - Review: `d6c91205 pasted-text.txt:68` - stdlib-only and YAML config are a conflict; MVP config must be JSON or TOML.

  **Acceptance Criteria**:
  - [ ] `python -m unittest tests.test_swarm_config tests.test_swarm_estimator` fails before implementation and passes after.
  - [ ] `python scripts/blackcow_swarm.py estimate "Implement team invite flow" --intensity high` emits JSON with `recommended_intensity` in `normal|high|max`.
  - [ ] `python scripts/blackcow_swarm.py estimate "Change auth policy and package-lock.json" --policy auto` emits JSON with `requires_approval: true` or `writer_swarm_allowed: false`.
  - [ ] Invalid template missing `{result_json}` fails with a clear error in tests.

  **QA Scenarios**:
  ```
  Scenario: Estimate happy path
    Tool: bash
    Steps: mkdir -p evidence && python scripts/blackcow_swarm.py estimate "Implement team invite flow" --intensity high > evidence/task-2-estimate.json
    Expected: JSON parses and has expected_speedup >= 1.0 plus recommended_workers > 0.
    Evidence: evidence/task-2-estimate.json

  Scenario: Risky writer auto approval gate
    Tool: bash
    Steps: mkdir -p evidence && python scripts/blackcow_swarm.py estimate "Change auth policy and package-lock.json" --policy auto > evidence/task-2-risky.json
    Expected: JSON includes requires_approval true or writer_swarm_allowed false.
    Evidence: evidence/task-2-risky.json
  ```

  **Commit**: YES | Message: `feat(swarm): add config and estimator` | Files: `blackcow.swarm.json`, `scripts/blackcow_swarm_lib/config.py`, `scripts/blackcow_swarm_lib/estimate.py`, `tests/test_swarm_config.py`, `tests/test_swarm_estimator.py`

- [x] 3. Add schemas, fixtures, and strict artifact validation

  **What to do**: Add four JSON schema files and deterministic fixtures. Implement `schema.py` with stdlib JSON loading and explicit required-field/enum validation matching the schema files. Tests must reject missing required task fields, invalid task kind, invalid result status, and invalid score ranges.
  **Must NOT do**: Do not accept malformed worker JSON. Do not add external schema dependencies.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: [5, 6, 7, 8, 10] | Blocked By: []

  **References**:
  - API/Type: `pasted-text.txt:376` - task graph example.
  - API/Type: `pasted-text.txt:434` - required task fields.
  - API/Type: `pasted-text.txt:448` - allowed task kinds.
  - API/Type: `pasted-text.txt:461` - success/failure result shape.
  - API/Type: `pasted-text.txt:1049` - acceptance criteria requiring valid task graph and MockRunner tests.

  **Acceptance Criteria**:
  - [ ] `python -m unittest tests.test_swarm_schema` fails before implementation and passes after.
  - [ ] `python -m json.tool schemas/swarm-task.schema.json >/dev/null` exits 0; repeat for all schema files.
  - [ ] `tests/fixtures/task_graph.simple.json` validates successfully.
  - [ ] `tests/fixtures/task_graph.invalid-missing-kind.json` is rejected by `schema.validate_task_graph`.

  **QA Scenarios**:
  ```
  Scenario: Valid fixtures pass
    Tool: bash
    Steps: mkdir -p evidence && python -m unittest tests.test_swarm_schema.TestSchemas.test_valid_fixtures -v | tee evidence/task-3-valid-fixtures.txt
    Expected: output contains OK.
    Evidence: evidence/task-3-valid-fixtures.txt

  Scenario: Missing required field fails
    Tool: bash
    Steps: mkdir -p evidence && python -m unittest tests.test_swarm_schema.TestSchemas.test_invalid_task_missing_kind -v | tee evidence/task-3-invalid-fixture.txt
    Expected: output contains OK because the test asserts rejection.
    Evidence: evidence/task-3-invalid-fixture.txt
  ```

  **Commit**: YES | Message: `feat(swarm): add schemas and fixtures` | Files: `schemas/*.json`, `tests/fixtures/*.json`, `scripts/blackcow_swarm_lib/schema.py`, `tests/test_swarm_schema.py`

- [x] 4. Register `blackcow-swarm` in the skill ecosystem

  **What to do**: Add `skills/blackcow-swarm.md` with existing BlackCow frontmatter fields, model tiers, Reasonix-native allowed tools, mission, inputs, procedure, and output contract from the prompt. Update `skills/install.sh` tool-extra cases, `README*.md` skill count/table, `skills/tests/validate-blackcow-ecosystem.sh`, `skills/tests/validate-cross-skill-contract.sh`, and add `skills/tests/validate-blackcow-swarm.sh`.
  **Must NOT do**: Do not globally install skills during tests except with `bash skills/install.sh --dry-run` or temp HOME/target paths. Do not drop any existing skill from validators.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: [12] | Blocked By: []

  **References**:
  - Pattern: `skills/blackcow-plan.md:1` - required frontmatter fields.
  - Pattern: `skills/install.sh:211` - skill-specific extra tool cases.
  - Pattern: `skills/install.sh:258` - installer copies every `blackcow-*.md`.
  - Pattern: `skills/tests/validate-blackcow-ecosystem.sh:169` - current hardcoded seven-skill list.
  - Pattern: `README.md:20` - current skill table.
  - API/Type: `pasted-text.txt:859` - skill draft contents.

  **Acceptance Criteria**:
  - [ ] `bash skills/tests/validate-blackcow-swarm.sh` fails before `skills/blackcow-swarm.md` exists and passes after.
  - [ ] `bash skills/install.sh --dry-run | grep blackcow-swarm.md` exits 0.
  - [ ] `bash skills/tests/validate-blackcow-ecosystem.sh --quiet` recognizes 8 skills instead of failing on 7-skill assumptions.
  - [ ] README files mention `blackcow-swarm` and still describe existing pipeline accurately.

  **QA Scenarios**:
  ```
  Scenario: New skill contract passes
    Tool: bash
    Steps: mkdir -p evidence && bash skills/tests/validate-blackcow-swarm.sh | tee evidence/task-4-skill-contract.txt
    Expected: output reports zero failures.
    Evidence: evidence/task-4-skill-contract.txt

  Scenario: Installer dry-run includes swarm
    Tool: bash
    Steps: mkdir -p evidence && bash skills/install.sh --dry-run | tee evidence/task-4-install-dry-run.txt
    Expected: output contains blackcow-swarm.md.
    Evidence: evidence/task-4-install-dry-run.txt
  ```

  **Commit**: YES | Message: `feat(swarm): register swarm skill` | Files: `skills/blackcow-swarm.md`, `skills/install.sh`, `skills/tests/validate-blackcow-swarm.sh`, `skills/tests/validate-blackcow-ecosystem.sh`, `skills/tests/validate-cross-skill-contract.sh`, `README*.md`

- [x] 5. Implement task graph generation, shared guardrails, and `plan --dry-run`

  **What to do**: Implement `task_graph.py` and `python scripts/blackcow_swarm.py plan "<task>" --dry-run`. The preflight graph generator should create run dir, `estimate.json`, `task_graph.json`, `shared_context.md`, and a minimal graph with discovery, coder/review/qa/judge tasks based on mode/intensity. `shared_context.md` must include anti-gaming guardrails: workers may not change check commands, skip/delete tests, weaken assertions, fake exit conditions, mark success without valid `result.json`, or continue past max iterations without reporting a blocker. Validate output with `schema.py`. Do not invoke Reasonix.
  **Must NOT do**: Do not require `blackcow-plan --emit-task-graph` yet; this is the orchestrator fallback graph.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: [8, 12] | Blocked By: [1, 2, 3]

  **References**:
  - API/Type: `pasted-text.txt:376` - task graph format.
  - API/Type: `pasted-text.txt:517` - run directory layout.
  - API/Type: `pasted-text.txt:825` - stable shared prompt context format.
  - API/Type: `pasted-text.txt:1040` - dry-run behavior.
  - Review: `d6c91205 pasted-text.txt:162` - anti-gaming guardrails must be included now without adding looping-skills.

  **Acceptance Criteria**:
  - [ ] `python -m unittest tests.test_swarm_task_graph` fails before implementation and passes after.
  - [ ] `python scripts/blackcow_swarm.py plan "Implement team invite flow" --intensity high --dry-run --run-id swarm-test-plan` writes `.omo/swarm/runs/swarm-test-plan/task_graph.json`.
  - [ ] Generated task graph validates and every task has `id`, `kind`, `skill`, `prompt`, `read_only`, `depends_on`, `writes`, `replicas`, `timeout_minutes`.
  - [ ] Dangerous write surfaces in task prompt produce no full coder swarm unless `--yes`.
  - [ ] `.omo/swarm/runs/<run_id>/shared_context.md` contains the anti-gaming guardrail text verbatim enough for `rg "do_not_skip_or_delete_tests|result.json"`.

  **QA Scenarios**:
  ```
  Scenario: Dry-run plan creates graph
    Tool: bash
    Steps: mkdir -p evidence && python scripts/blackcow_swarm.py plan "Implement team invite flow" --intensity high --dry-run --run-id swarm-qa-plan | tee evidence/task-5-plan.txt
    Expected: .omo/swarm/runs/swarm-qa-plan/task_graph.json exists and validates.
    Evidence: evidence/task-5-plan.txt

  Scenario: Malformed run id rejected
    Tool: bash
    Steps: mkdir -p evidence && (python scripts/blackcow_swarm.py plan "x" --run-id ../bad --dry-run > evidence/task-5-bad-run.out 2> evidence/task-5-bad-run.err; echo $? > evidence/task-5-bad-run.code)
    Expected: non-zero exit and stderr contains invalid run-id.
    Evidence: evidence/task-5-bad-run.err
  ```

  **Commit**: YES | Message: `feat(swarm): generate task graphs` | Files: `scripts/blackcow_swarm_lib/task_graph.py`, `scripts/blackcow_swarm_lib/cli.py`, `tests/test_swarm_task_graph.py`

- [x] 6. Implement runner abstraction, MockRunner, and ReasonixRunner

  **What to do**: Implement `WorkerRunner`, `MockRunner`, and `ReasonixRunner` in `runner.py`. `MockRunner` reads deterministic fixture behavior, writes result JSON, stdout/stderr logs, optional progress heartbeat, and timestamps. `ReasonixRunner` builds argument-list subprocess commands from validated templates, launches workers in their own process group (`subprocess.Popen(..., start_new_session=True)`), captures stdout/stderr, enforces output JSON existence, handles missing Reasonix as a fatal runner error, and never uses shell interpolation. Missing or invalid `result.json` is not success; it becomes `FAILED_RETRYABLE` unless task retry policy says fatal.
  **Must NOT do**: Do not execute Reasonix in unit tests. Do not allow path traversal in prompt/result/workspace paths.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: [7, 8, 9, 10, 11] | Blocked By: [1, 2, 3]

  **References**:
  - API/Type: `pasted-text.txt:140` - Reasonix runtime, no direct DeepSeek API call.
  - API/Type: `pasted-text.txt:165` - `WorkerRunner.run` interface.
  - API/Type: `pasted-text.txt:173` - `MockRunner` required for tests.
  - API/Type: `pasted-text.txt:461` - worker result JSON.
  - API/Type: `pasted-text.txt:731` - heartbeat file format.
  - Review: `d6c91205 pasted-text.txt:129` - scheduler owns heartbeat and subprocesses need process groups for cancellation.
  - Review: `d6c91205 pasted-text.txt:151` - worker self-report is not proof; valid `result.json` and structured evidence are required.

  **Acceptance Criteria**:
  - [ ] `python -m unittest tests.test_swarm_runner` fails before implementation and passes after.
  - [ ] `MockRunner` can simulate success, retryable failure, timeout, malformed JSON, and slow task.
  - [ ] `ReasonixRunner` command construction test proves template placeholders are substituted as argument list.
  - [ ] Missing required result JSON returns `failed_retryable` or fatal per task config and records an event.
  - [ ] `ReasonixRunner` cancellation test verifies the runner stores process group metadata and uses process-group termination for children.

  **QA Scenarios**:
  ```
  Scenario: MockRunner success writes result
    Tool: bash
    Steps: mkdir -p evidence && python -m unittest tests.test_swarm_runner.TestMockRunner.test_success_result_written -v | tee evidence/task-6-mock-success.txt
    Expected: output contains OK and test verifies result.json exists.
    Evidence: evidence/task-6-mock-success.txt

  Scenario: Bad runner template rejected
    Tool: bash
    Steps: mkdir -p evidence && python -m unittest tests.test_swarm_runner.TestReasonixRunner.test_rejects_unknown_placeholder -v | tee evidence/task-6-bad-template.txt
    Expected: output contains OK because test asserts rejection.
    Evidence: evidence/task-6-bad-template.txt
  ```

  **Commit**: YES | Message: `feat(swarm): add worker runners` | Files: `scripts/blackcow_swarm_lib/runner.py`, `tests/test_swarm_runner.py`

- [x] 7. Implement state, events, locking, and dry-run run execution

  **What to do**: Implement `state.py` with `state.json`, `events.jsonl`, atomic writes via temp-file rename, and a single-orchestrator lock file under the run dir. Implement `run --dry-run` to load a task graph, validate it, write state/events, render worker prompts/commands, and print execution plan without invoking workers.
  **Must NOT do**: Do not run workers in dry-run. Do not corrupt state if interrupted; write events append-only.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: [8, 11] | Blocked By: [1, 3, 6]

  **References**:
  - API/Type: `pasted-text.txt:517` - run directory layout.
  - API/Type: `pasted-text.txt:699` - scheduler states.
  - API/Type: `pasted-text.txt:1040` - dry-run outputs estimate, graph, worker command, no Reasonix.
  - Pattern: `skills/blackcow-loop.md:54` - existing pipeline writes phase transitions to `.omo/pipeline.log`; swarm should use structured events.

  **Acceptance Criteria**:
  - [ ] `python -m unittest tests.test_swarm_state` fails before implementation and passes after.
  - [ ] `python scripts/blackcow_swarm.py run --task-graph tests/fixtures/task_graph.simple.json --dry-run --run-id swarm-qa-dry` exits 0.
  - [ ] `.omo/swarm/runs/swarm-qa-dry/state.json` and `events.jsonl` exist.
  - [ ] Dry-run stdout contains the Reasonix command template but no worker result directories are created as running workers.

  **QA Scenarios**:
  ```
  Scenario: Dry-run run creates state only
    Tool: bash
    Steps: mkdir -p evidence && python scripts/blackcow_swarm.py run --task-graph tests/fixtures/task_graph.simple.json --dry-run --run-id swarm-qa-dry | tee evidence/task-7-dry-run.txt
    Expected: state.json and events.jsonl exist; no Reasonix process is started.
    Evidence: evidence/task-7-dry-run.txt

  Scenario: Concurrent state lock rejected
    Tool: bash
    Steps: mkdir -p evidence && python -m unittest tests.test_swarm_state.TestStateLock.test_second_lock_fails -v | tee evidence/task-7-lock.txt
    Expected: output contains OK because second lock is rejected.
    Evidence: evidence/task-7-lock.txt
  ```

  **Commit**: YES | Message: `feat(swarm): add run state and dry-run` | Files: `scripts/blackcow_swarm_lib/state.py`, `scripts/blackcow_swarm_lib/cli.py`, `tests/test_swarm_state.py`

- [x] 8. Implement DAG scheduler, read-only concurrency, and single-writer locks

  **What to do**: Implement `scheduler.py` dependency resolution, READY/LEASED/RUNNING/SUCCEEDED/FAILED/TIMED_OUT transitions, retry counters, read-only parallel execution through `MockRunner`, read-only dirty-checks, and single-writer path lock planning. Before each read-only worker, record `git status --porcelain`; after completion, verify no product-file diff was introduced. If a read-only worker dirties the repo, mark it as a protocol violation, capture the diff under the run reports directory, and revert only paths that are safe and explicitly inside temporary/runtime outputs. Use overlap timestamps to prove concurrency. Single-writer path list must include prompt paths such as lockfiles, migrations, workflows, infra/deploy, `.env*`, auth policy, billing.
  **Must NOT do**: Do not run writer workers in root checkout. Do not run two tasks concurrently if their `writes` overlap a single-writer path. Do not silently ignore read-only worker writes.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: [9, 10, 11, 12] | Blocked By: [2, 3, 5, 6, 7]

  **References**:
  - API/Type: `pasted-text.txt:70` - implementation goals include DAG scheduler and read-only/writer split.
  - API/Type: `pasted-text.txt:699` - state machine.
  - API/Type: `pasted-text.txt:797` - single-writer paths and behavior.
  - API/Type: `pasted-text.txt:1070` - test scenarios for read-only concurrency and single-writer lock.
  - Review: `d6c91205 pasted-text.txt:189` - read-only workers must not dirty the repo silently.

  **Acceptance Criteria**:
  - [ ] `python -m unittest tests.test_swarm_scheduler` fails before implementation and passes after.
  - [ ] Three read-only tasks with `max_workers=3` overlap in time and complete faster than a serial threshold.
  - [ ] A read-only worker that modifies a product file is marked protocol violation and its diff is captured.
  - [ ] Two writer tasks targeting `pnpm-lock.yaml` are not scheduled concurrently.
  - [ ] Dependency task does not become READY until dependencies succeeded or an accepted winner exists.

  **QA Scenarios**:
  ```
  Scenario: Read-only tasks run concurrently
    Tool: bash
    Steps: mkdir -p evidence && python -m unittest tests.test_swarm_scheduler.TestScheduler.test_read_only_tasks_overlap -v | tee evidence/task-8-concurrency.txt
    Expected: output contains OK and test asserts overlapping started_at/finished_at intervals.
    Evidence: evidence/task-8-concurrency.txt

  Scenario: Single-writer lock serializes lockfile writers
    Tool: bash
    Steps: mkdir -p evidence && python -m unittest tests.test_swarm_scheduler.TestScheduler.test_single_writer_lockfile_tasks_not_concurrent -v | tee evidence/task-8-single-writer.txt
    Expected: output contains OK and test asserts no overlap.
    Evidence: evidence/task-8-single-writer.txt
  ```

  **Commit**: YES | Message: `feat(swarm): schedule dag workers` | Files: `scripts/blackcow_swarm_lib/scheduler.py`, `tests/test_swarm_scheduler.py`

- [x] 9. Implement writer worktree isolation, complete patch capture, and write-scope enforcement

  **What to do**: Implement `worktree.py` for sanitized branch/worktree names, dirty root preflight, `git worktree add`, writer workspace path selection, complete patch capture, write-scope enforcement, and loser cleanup hooks. Patch extraction must run `git -C <worker_tree> add -A` followed by `git -C <worker_tree> diff --cached --binary > <patch_path>` so new, deleted, and binary files are included. Workers may stage files only for extraction; workers must never commit. After patch extraction, list changed files from the patch and compare them against the task's `writes` globs; out-of-scope changes become `NEEDS_REVIEW` or `FAILED_FATAL` unless the task explicitly allows them. Root checkout is never used as writer workspace. Add tests with temp git repos.
  **Must NOT do**: Do not modify root checkout from a worker. Do not use plain `git diff` for patch extraction. Do not allow worker commits. Do not ignore dirty worktree conflicts when applying a winner later.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: [10] | Blocked By: [6, 8]

  **References**:
  - API/Type: `pasted-text.txt:566` - runtime worktree layout.
  - API/Type: `pasted-text.txt:577` - read-only vs writer worker isolation.
  - API/Type: `pasted-text.txt:588` - writer uses `git worktree add`.
  - API/Type: `pasted-text.txt:596` - patch generation after worker ends.
  - API/Type: `pasted-text.txt:602` - root checkout only receives integrator-applied patch.
  - Review: `d6c91205 pasted-text.txt:86` - patch extraction must include new/deleted/binary files using staged binary diff.
  - Review: `d6c91205 pasted-text.txt:201` - changed files in extracted patch must be checked against task write globs.

  **Acceptance Criteria**:
  - [ ] `python -m unittest tests.test_swarm_worktree` fails before implementation and passes after.
  - [ ] Writer workspace path is `.worktrees/swarm/<run_id>/<replica_id>`.
  - [ ] Patch file is written to `.omo/swarm/runs/<run_id>/patches/<replica_id>.patch`.
  - [ ] Patch extraction includes untracked new files, deleted files, and binary file changes.
  - [ ] Out-of-scope changed files are detected and candidate status becomes `NEEDS_REVIEW` or `FAILED_FATAL`.
  - [ ] Malicious `run_id=../bad` or `replica_id=../../x` is rejected.

  **QA Scenarios**:
  ```
  Scenario: Writer worktree created and patch captured
    Tool: bash
    Steps: mkdir -p evidence && python -m unittest tests.test_swarm_worktree.TestWorktree.test_writer_patch_created_outside_root -v | tee evidence/task-9-worktree.txt
    Expected: output contains OK and test verifies root checkout unchanged before integration and patch was created with staged binary diff semantics.
    Evidence: evidence/task-9-worktree.txt

  Scenario: Write scope violation rejected
    Tool: bash
    Steps: mkdir -p evidence && python -m unittest tests.test_swarm_worktree.TestWorktree.test_out_of_scope_patch_is_rejected -v | tee evidence/task-9-write-scope.txt
    Expected: output contains OK because test asserts NEEDS_REVIEW or FAILED_FATAL for an out-of-scope file.
    Evidence: evidence/task-9-write-scope.txt

  Scenario: Traversal identifiers rejected
    Tool: bash
    Steps: mkdir -p evidence && python -m unittest tests.test_swarm_worktree.TestWorktree.test_rejects_path_traversal_ids -v | tee evidence/task-9-traversal.txt
    Expected: output contains OK because test asserts rejection.
    Evidence: evidence/task-9-traversal.txt
  ```

  **Commit**: YES | Message: `feat(swarm): isolate writer worktrees` | Files: `scripts/blackcow_swarm_lib/worktree.py`, `scripts/blackcow_swarm_lib/scheduler.py`, `tests/test_swarm_worktree.py`, `.gitignore`

- [x] 10. Implement race groups, integration worktree tournament, dependent writer bases, and final judge

  **What to do**: Implement race-group replicas, winner selection, loser cancel/discard/archive policies, `tournament.py`, integration target management, and `judge.py`. Default patch application target is `.worktrees/swarm/<run_id>/integration`; expose `--apply-target=integration-worktree` as the default and `--apply-target=main` as an explicit dangerous mode that requires `--yes`. Tournament must check patch existence, apply/check each patch in the integration worktree, run changed/smoke tests when configured, score each candidate, write `reports/tournament.md`, choose winner deterministically, apply the winning patch to the integration worktree, create an internal integrator-only checkpoint commit for downstream writer bases, and write `final_judgement.json`. Dependent writer task worktrees must be based on the current integration checkpoint after upstream accepted winners, not always the original base commit.
  **Must NOT do**: Do not select a patch that fails apply. Do not default to applying a winner to the main checkout. Do not let workers commit; only the integrator may create internal checkpoint commits on `swarm/<run_id>/integration`.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: [12] | Blocked By: [6, 8, 9]

  **References**:
  - API/Type: `pasted-text.txt:608` - race group and speculative execution.
  - API/Type: `pasted-text.txt:646` - candidate scoring criteria.
  - API/Type: `pasted-text.txt:671` - patch tournament steps.
  - API/Type: `pasted-text.txt:684` - tournament report format.
  - API/Type: `pasted-text.txt:1059` - acceptance criteria for race groups, patch winner, loser archive/discard, final judgement.
  - Review: `d6c91205 pasted-text.txt:99` - main checkout must not be default integration target.
  - Review: `d6c91205 pasted-text.txt:117` - dependent writer tasks must use current integration state.

  **Acceptance Criteria**:
  - [ ] `python -m unittest tests.test_swarm_race_group tests.test_swarm_tournament tests.test_swarm_judge` fails before implementation and passes after.
  - [ ] Given C1 replicas where r1 fails, r2 passes, r3 is slow, r2 is selected and r3 is cancelled/discarded when policy allows.
  - [ ] Given two patches where one applies and one does not, clean patch wins.
  - [ ] Default integration target is `.worktrees/swarm/<run_id>/integration`; main checkout is untouched unless `--apply-target=main --yes`.
  - [ ] A C2 writer task depending on C1 starts from an integration checkpoint that contains the selected C1 winner patch.
  - [ ] `final_judgement.json` validates against `schemas/swarm-final-judgement.schema.json`.

  **QA Scenarios**:
  ```
  Scenario: Race group selects first passing candidate
    Tool: bash
    Steps: mkdir -p evidence && python -m unittest tests.test_swarm_race_group.TestRaceGroup.test_failed_fast_pass_slow_selects_passing_candidate -v | tee evidence/task-10-race.txt
    Expected: output contains OK and test verifies C1-r2 winner.
    Evidence: evidence/task-10-race.txt

  Scenario: Patch tournament rejects bad patch
    Tool: bash
    Steps: mkdir -p evidence && python -m unittest tests.test_swarm_tournament.TestTournament.test_clean_patch_beats_non_applying_patch -v | tee evidence/task-10-tournament.txt
    Expected: output contains OK and tournament report names the clean patch winner.
    Evidence: evidence/task-10-tournament.txt

  Scenario: Dependent writer uses integration checkpoint
    Tool: bash
    Steps: mkdir -p evidence && python -m unittest tests.test_swarm_tournament.TestTournament.test_dependent_writer_uses_current_integration_base -v | tee evidence/task-10-dependent-base.txt
    Expected: output contains OK and test verifies C2 base includes selected C1 patch.
    Evidence: evidence/task-10-dependent-base.txt
  ```

  **Commit**: YES | Message: `feat(swarm): select candidate patches` | Files: `scripts/blackcow_swarm_lib/tournament.py`, `scripts/blackcow_swarm_lib/judge.py`, `scripts/blackcow_swarm_lib/scheduler.py`, `tests/test_swarm_race_group.py`, `tests/test_swarm_tournament.py`, `tests/test_swarm_judge.py`

- [x] 11. Implement heartbeat, timeout, retry, resume, cancel, status, cleanup, and throttle

  **What to do**: Complete live run lifecycle commands. Scheduler-owned process heartbeats update lease/process metadata; worker-written heartbeat files are optional progress evidence only. A live but silent subprocess must not be killed merely because a worker heartbeat file is stale; kill only on hard timeout or explicit cancellation. Timeouts become `TIMED_OUT`, then retry or fatal by config. `resume` loads graph/state and does not rerun succeeded tasks. `cancel --run-id` writes `CANCEL_REQUESTED` into the run dir; the active scheduler polls it, terminates active worker process groups, marks pending/running tasks cancelled, and writes `final_judgement.json`. `status` prints machine-readable summary. `cleanup` removes worktrees/large artifacts while preserving audit artifacts. Dynamic throttle handles rate-limit strings/HTTP 429/timeouts by lowering concurrency, with tests using MockRunner stderr.
  **Must NOT do**: Do not leave QA-spawned processes or tmux sessions alive in manual scenarios. Do not delete audit-critical JSON artifacts on cleanup. Do not rely on LLM workers to keep heartbeats alive during long calls.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: [12] | Blocked By: [2, 6, 8]

  **References**:
  - API/Type: `pasted-text.txt:731` - heartbeat format and resume behavior.
  - API/Type: `pasted-text.txt:766` - dynamic throttle triggers/policy.
  - API/Type: `pasted-text.txt:1026` - resume/cancel/status/cleanup commands.
  - API/Type: `pasted-text.txt:1064` - acceptance criteria for timeout, resume, cancel.
  - API/Type: `pasted-text.txt:1106` - resume test scenario.
  - Review: `d6c91205 pasted-text.txt:129` - scheduler owns heartbeat and kills only on hard timeout or cancellation.
  - Review: `d6c91205 pasted-text.txt:213` - crash-safe state and cancellation require atomic writes, lock/pid file, and `CANCEL_REQUESTED`.

  **Acceptance Criteria**:
  - [ ] `python -m unittest tests.test_swarm_resume tests.test_swarm_cancel_cleanup tests.test_swarm_throttle` fails before implementation and passes after.
  - [ ] Resume after D1 succeeded and stale C1 running does not rerun D1 and retries/discards C1.
  - [ ] A live but silent subprocess is not killed until hard timeout.
  - [ ] Cancel marks pending and running tasks cancelled and records `cancel_requested` event.
  - [ ] `cancel --run-id` writes `CANCEL_REQUESTED`; active scheduler observes it and writes final judgement after termination.
  - [ ] Cleanup removes `.worktrees/swarm/<run_id>` but preserves `final_judgement.json`, `events.jsonl`, and `reports/tournament.md` if present.
  - [ ] Repeated rate-limit strings cut active concurrency by 50 percent in tests.

  **QA Scenarios**:
  ```
  Scenario: Resume stale run
    Tool: bash
    Steps: mkdir -p evidence && python -m unittest tests.test_swarm_resume.TestResume.test_succeeded_task_not_rerun_and_stale_running_retried -v | tee evidence/task-11-resume.txt
    Expected: output contains OK and test verifies D1 attempt count unchanged.
    Evidence: evidence/task-11-resume.txt

  Scenario: Cancel running task via tmux transcript
    Tool: tmux
    Steps: tmux new-session -d -s ulw-qa-swarm-cancel 'python scripts/blackcow_swarm.py run --task-graph tests/fixtures/task_graph.slow.json --runner mock --run-id swarm-qa-cancel'; sleep 1; python scripts/blackcow_swarm.py cancel --run-id swarm-qa-cancel; tmux capture-pane -pS -200 -t ulw-qa-swarm-cancel > evidence/task-11-cancel-tmux.txt; tmux kill-session -t ulw-qa-swarm-cancel
    Expected: state.json marks running task CANCELLED and evidence transcript shows cancel event; cleanup receipt records tmux session killed.
    Evidence: evidence/task-11-cancel-tmux.txt
  ```

  **Commit**: YES | Message: `feat(swarm): manage run lifecycle` | Files: `scripts/blackcow_swarm_lib/state.py`, `scripts/blackcow_swarm_lib/scheduler.py`, `scripts/blackcow_swarm_lib/cli.py`, `tests/test_swarm_resume.py`, `tests/test_swarm_cancel_cleanup.py`, `tests/test_swarm_throttle.py`

- [x] 12. Integrate `blackcow-loop`, `blackcow-plan`, `blackcow-qa`, docs, and final ecosystem validation

  **What to do**: Update existing skills. `blackcow-loop` recognizes swarm flags and delegates only when explicit swarm activation is present; otherwise existing TRY/governance behavior remains. `blackcow-plan` supports `--emit-task-graph` and writes `.omo/swarm/runs/<run_id>/task_graph.json` while preserving normal markdown plans. `blackcow-qa` supports `--gate-worker`, `--gates`, `--emit-json`, `--run-id`, `--task-id` and writes QA worker JSON. Update shell tests and README demo commands. Run full Python and shell verification.
  **Must NOT do**: Do not break `blackcow-loop "task"` with no swarm flags. Do not make QA worker outputs incompatible with existing `.omo/memory/qa-history.jsonl` consumers.

  **Parallelization**: Can Parallel: NO | Wave 3 | Blocks: [final] | Blocked By: [4, 5, 8, 10, 11]

  **References**:
  - Pattern: `skills/blackcow-loop.md:35` - current no-flag TRY behavior to preserve.
  - Pattern: `skills/blackcow-loop.md:25` - current plan reference parsing to preserve.
  - Pattern: `skills/blackcow-plan.md:82` - cross-skill contract section to update.
  - Pattern: `skills/blackcow-qa.md:50` - QA evidence index loading must remain compatible.
  - API/Type: `pasted-text.txt:940` - loop swarm flags and delegation.
  - API/Type: `pasted-text.txt:968` - plan `--emit-task-graph`.
  - API/Type: `pasted-text.txt:997` - QA worker flags and JSON result.
  - API/Type: `pasted-text.txt:1177` - final demo commands.

  **Acceptance Criteria**:
  - [ ] `bash skills/tests/validate-blackcow-swarm.sh` passes.
  - [ ] `bash skills/tests/validate-cross-skill-contract.sh --quiet` passes with swarm contract updates.
  - [ ] `bash skills/tests/validate-blackcow-ecosystem.sh --quiet` passes.
  - [ ] `python -m unittest discover -s tests -p 'test_swarm_*.py'` passes.
  - [ ] `python scripts/blackcow_swarm.py estimate "Implement team invite flow" --intensity high` works.
  - [ ] `python scripts/blackcow_swarm.py plan "Implement team invite flow" --intensity high --dry-run` works.
  - [ ] `python scripts/blackcow_swarm.py run --task-graph .omo/swarm/runs/<run_id>/task_graph.json --dry-run` works for the run id produced by plan.

  **QA Scenarios**:
  ```
  Scenario: Existing loop no-swarm behavior preserved by contract
    Tool: bash
    Steps: mkdir -p evidence && bash skills/tests/validate-blackcow-swarm.sh --check-loop-non-swarm | tee evidence/task-12-loop-non-swarm.txt
    Expected: output verifies no unflagged default delegation to blackcow-swarm.
    Evidence: evidence/task-12-loop-non-swarm.txt

  Scenario: End-to-end dry-run demo
    Tool: bash
    Steps: mkdir -p evidence && RUN_ID=swarm-demo-qa && python scripts/blackcow_swarm.py estimate "Implement team invite flow" --intensity high > evidence/task-12-estimate.json && python scripts/blackcow_swarm.py plan "Implement team invite flow" --intensity high --dry-run --run-id "$RUN_ID" > evidence/task-12-plan.txt && python scripts/blackcow_swarm.py run --task-graph ".omo/swarm/runs/$RUN_ID/task_graph.json" --dry-run --run-id "$RUN_ID" > evidence/task-12-run-dry.txt
    Expected: estimate JSON parses, task_graph.json exists, run dry-run prints worker command plan and invokes no Reasonix worker.
    Evidence: evidence/task-12-estimate.json, evidence/task-12-plan.txt, evidence/task-12-run-dry.txt
  ```

  **Commit**: YES | Message: `feat(swarm): integrate blackcow skills` | Files: `skills/blackcow-loop.md`, `skills/blackcow-plan.md`, `skills/blackcow-qa.md`, `skills/tests/*.sh`, `README*.md`, `.gitignore`

## Final Verification Wave (MANDATORY - after ALL implementation tasks)
> ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
- [x] F1. Plan Compliance Audit
  - Command: `python -m unittest discover -s tests -p 'test_swarm_*.py'`
  - Command: `bash skills/tests/validate-blackcow-swarm.sh`
  - Command: `bash skills/tests/validate-blackcow-ecosystem.sh --quiet`
  - Expected: all exit 0.
- [x] F2. Code Quality Review
  - Command: `python -m compileall scripts/blackcow_swarm.py scripts/blackcow_swarm_lib`
  - Command: `bash -n skills/tests/validate-blackcow-swarm.sh skills/install.sh`
  - Expected: all exit 0.
- [x] F3. Real Manual QA
  - Command: `python scripts/blackcow_swarm.py estimate "Implement team invite flow" --intensity high`
  - Command: `python scripts/blackcow_swarm.py plan "Implement team invite flow" --intensity high --dry-run --run-id swarm-final-qa`
  - Command: `python scripts/blackcow_swarm.py run --task-graph .omo/swarm/runs/swarm-final-qa/task_graph.json --dry-run --run-id swarm-final-qa`
  - Expected: estimate JSON, task graph, state/events, and dry-run command plan are produced.
- [x] F4. Scope Fidelity Check
  - Command: `rg -n "Kimi|kubernetes|kubectl|docker swarm|DeepSeek API" scripts skills schemas tests README*.md`
  - Expected: no implementation path uses Kimi, Kubernetes, remote clusters, or direct DeepSeek API calls; README may mention Kimi only as prohibited.

## Commit Strategy
- One commit per task, in task order, after that task's tests and QA scenarios pass.
- Use Conventional Commits exactly as listed in each task.
- Do not auto-commit unless the user explicitly approves committing.
- If a worker executes this plan, stage only files changed by the task; never stage unrelated dirty files.

## Success Criteria
- All prompt acceptance criteria 1-16 are satisfied.
- All five prompt test scenarios are covered by deterministic tests and command evidence.
- Existing non-swarm BlackCow skill flow remains available.
- The final demo commands from the prompt work.
- No QA process, tmux session, worktree, or temp run remains uncleaned after manual QA except intentionally preserved audit artifacts.
