# BlackCow Swarm Control-Plane Continuation

## TL;DR
> Summary:      Continue the BlackCow Swarm control-plane work by making writer workspaces truly isolated, allowing writer replica expansion only after that isolation is real, tightening cleanup edge cases, and proving the behavior with RED->GREEN unittest evidence plus tmux QA artifacts.
> Deliverables:
> - C001: writer tasks run in `.worktrees/swarm/<run_id>/<replica_id>` and writer task graphs expand replicas when worktree isolation is enabled.
> - C002: malformed ids remain rejected, ignored stale swarm artifacts do not block worktree creation, and cleanup removes writer worktrees plus patch artifacts without removing audit files.
> - C003: full swarm regression and BlackCow skill validation run in tmux with captured evidence.
> - C002 resolution path that never hand-edits `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/goals.json`.
> Effort:       Medium
> Risk:         Medium - scheduler/worktree/lifecycle behavior intersects git worktrees, ignored artifacts, and worker result paths.

## Scope
### Must have
- Preserve the goal boundary in `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/brief.md:1`: improve `blackcow-swarm`/Reasonix control plane, not the water-check app.
- Keep all manual QA artifacts under `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/`.
- Use TDD for every behavior change: add/adjust the named failing test first, capture RED, implement the smallest passing change, capture GREEN.
- C001 must add or update these exact test ids:
  - `tests.test_swarm_scheduler.TestScheduler.test_writer_tasks_use_isolated_worktree_workspace`
  - `tests.test_swarm_task_graph.TestSwarmTaskGraph.test_writer_replicas_expand_when_worktree_isolation_enabled`
- C002 must add or retain these exact test ids:
  - `tests.test_swarm_worktree.TestWorktree.test_create_writer_worktree_allows_ignored_dirty_swarm_artifacts`
  - `tests.test_swarm_worktree.TestWorktree.test_rejects_path_traversal_ids`
  - `tests.test_swarm_cancel_cleanup.TestCancelCleanup.test_cleanup_purges_writer_worktrees_and_patches`
- Keep code changes small and scoped to `scripts/blackcow_swarm_lib/*` plus `tests/test_swarm_*.py`.
- Make writer result/prompt paths compatible with `WorkerTask` validation, which requires `prompt_file` and `result_json` to be under `workspace` in `scripts/blackcow_swarm_lib/runner.py:260-268`.
- Preserve BlackCow skill-backed prompts in `scripts/blackcow_swarm_lib/skill_contract.py:27-72`.
- Preserve existing timing behavior in `scripts/blackcow_swarm_lib/runner.py:237-244` and lifecycle state timing in `scripts/blackcow_swarm_lib/lifecycle.py:116-143` and `scripts/blackcow_swarm_lib/lifecycle.py:167-194`.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Must NOT edit any file under `water-check-app/`.
- Must NOT hand-edit `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/goals.json`.
- Must NOT commit, stage, or squash anything. Every task has `Commit: NO`.
- Must NOT run a live Reasonix writer swarm against the dirty main checkout.
- Must NOT expand large/risky files unless the task explicitly owns that file: `scripts/blackcow_swarm_lib/lifecycle.py`, `scripts/blackcow_swarm_lib/runner.py`, `scripts/blackcow_reasonix_acp_worker.py`.
- Must NOT weaken or delete existing tests. If an existing test encodes the old "single writer until isolation" contract, rename/update it to the new C001 contract in the same RED test edit.
- Must NOT treat `--dry-run` as completion evidence for C001 writer isolation.
- Must NOT leave tmux sessions, temp repos, `.worktrees/swarm/<test-run>`, or QA-only artifacts outside the evidence directory.

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: TDD + Python `unittest`
- QA policy: every task has agent-executed scenarios
- Evidence: `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-<N>-blackcow-swarm-control-plane-continuation.<ext>`

## Execution strategy
### Parallel execution waves
> Target 5-8 tasks per wave. <3 per wave (except final) = under-splitting.
> Extract shared dependencies as Wave-1 tasks to maximize parallelism.

Wave 1 (no dependencies):
- Task 1: Main agent audits C002 loop state and records the non-hand-edit resolution path.
- Task 2: Worker A owns scheduler writer isolation and patch capture.
- Task 3: Worker B owns task-graph writer replica expansion.
- Task 4: Worker C owns C002 worktree/cleanup edge coverage.

Wave 2 (after Wave 1):
- Task 5: Main agent captures C001 and C002 criterion tmux QA artifacts.
- Task 6: Main agent captures C003 full regression tmux QA artifact.

Wave 3 (after Wave 2):
- Task 7: Main agent performs final scope/evidence audit and cleanup receipt capture.

Critical path: Task 2 -> Task 5 -> Task 6 -> Task 7

### Dependency matrix
| Task | Depends on | Blocks | Can parallelize with |
|------|------------|--------|----------------------|
| 1    | none       | 7      | 2, 3, 4              |
| 2    | none       | 5, 6, 7 | 1, 3, 4             |
| 3    | none       | 5, 6, 7 | 1, 2, 4             |
| 4    | none       | 5, 6, 7 | 1, 2, 3             |
| 5    | 2, 3, 4    | 6, 7   | none                 |
| 6    | 5          | 7      | none                 |
| 7    | 1, 5, 6    | none   | none                 |

## Todos
> Implementation + Test = ONE task. Never separate.
> Every task MUST have: References + Acceptance Criteria + QA Scenarios + Commit.

- [ ] 1. Audit C002 loop state and choose the non-hand-edit resolution path

  What to do: Main agent only. Read the active loop files and record whether C002 is already concrete. Based on this checkout, `goals.json` already contains concrete C002 wording at `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/goals.json:24-31`, and the ledger shows the accepted C002 revision at `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/ledger.jsonl:6`. If the executor sees a placeholder in another checkout, do not edit `goals.json`; submit a new loop steering action using the exact C002 wording from this plan. If the same `revise_criterion` is rejected twice as "weakened completion", create a new subgoal/criterion with this exact wording instead of weakening C002:
  `edge case (boundary/empty/malformed) via tmux channel: create session ulw-qa-cleanup-cancel, run python3 -m unittest tests.test_swarm_worktree.TestWorktree.test_create_writer_worktree_allows_ignored_dirty_swarm_artifacts tests.test_swarm_worktree.TestWorktree.test_rejects_path_traversal_ids tests.test_swarm_cancel_cleanup.TestCancelCleanup.test_cleanup_purges_writer_worktrees_and_patches -v, capture pane to .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C002-cleanup-cancel-tmux.txt. PASS iff output contains OK, malformed run_id and replica_id are rejected, ignored .omo/swarm and .worktrees artifacts do not block writer worktree creation, and cleanup purges .worktrees/swarm/<run_id> plus worker patch artifacts while preserving audit files.`
  Record the audit in `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-1-c002-state-audit.txt`.

  Must NOT do: Do not edit `goals.json`. Do not mark C002 complete from this audit alone. Do not run implementation tests before Task 2-4 have captured RED.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [7] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/goals.json:24-31` - current concrete C002 scenario and evidence path.
  - Pattern:  `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/ledger.jsonl:3` - earlier C002 rejection reason.
  - Pattern:  `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/ledger.jsonl:6` - accepted strengthened C002 wording.
  - Pattern:  `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/brief.md:1` - scope says control-plane work, not app hand-fix.
  - External: `https://docs.python.org/3/library/unittest.html#test-discovery` - official unittest discovery/test-id reference.

  Acceptance criteria (agent-executable only):
  - [ ] `python3 -m json.tool .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/goals.json >/dev/null` exits 0.
  - [ ] `python3 -c 'import json; from pathlib import Path; p=Path(".omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/goals.json"); data=json.loads(p.read_text()); c2=next(c for c in data["goals"][0]["successCriteria"] if c["id"]=="C002"); assert "placeholder" not in c2["scenario"].lower(); assert "test_cleanup_purges_writer_worktrees_and_patches" in c2["scenario"]; print(c2["scenario"])'` exits 0.
  - [ ] `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-1-c002-state-audit.txt` exists and states either `C002 concrete in current goals.json` or `C002 unresolved; use new subgoal, not hand-edit`.

  QA scenarios (MANDATORY - task incomplete without these):
  > Name the exact tool AND its exact invocation - not "verify it works". Browser use: use Chrome to drive the page; if Chrome is not available, download and use agent-browser (https://github.com/vercel-labs/agent-browser). Computer use: OS-level GUI automation for a non-browser desktop app.
  ```
  Scenario: C002 state audit
    Tool:     tmux
    Steps:    tmux new-session -d -s ulw-qa-c002-state -c /Users/jeong-yugyeong/Project/blackcow-ops 'bash -lc "mkdir -p .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence; python3 -m json.tool .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/goals.json >/dev/null; python3 -c '\''import json; from pathlib import Path; p=Path(\".omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/goals.json\"); data=json.loads(p.read_text()); c2=next(c for c in data[\"goals\"][0][\"successCriteria\"] if c[\"id\"]==\"C002\"); print(c2[\"scenario\"]); assert \"test_cleanup_purges_writer_worktrees_and_patches\" in c2[\"scenario\"]'\''"'; tmux capture-pane -pt ulw-qa-c002-state -S - -E - > .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-1-c002-state-audit.txt; tmux kill-session -t ulw-qa-c002-state
    Expected: artifact contains `test_cleanup_purges_writer_worktrees_and_patches`.
    Evidence: .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-1-c002-state-audit.txt

  Scenario: malformed C002 placeholder detection
    Tool:     bash
    Steps:    python3 -c 'import json; from pathlib import Path; p=Path(".omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/goals.json"); data=json.loads(p.read_text()); c2=next(c for c in data["goals"][0]["successCriteria"] if c["id"]=="C002"); assert "Replace via revise_criterion" not in c2.get("expectedEvidence",""); assert "boundary or malformed-input proof" not in c2.get("expectedEvidence",""); print("C002 is not placeholder")'
    Expected: command exits 0 and prints `C002 is not placeholder`.
    Evidence: .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-1-c002-state-audit-error.txt
  ```

  Commit: NO | Message: `test(ulw): audit c002 criterion state` | Files: [.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-1-c002-state-audit.txt]

- [ ] 2. Make scheduler writer tasks use isolated worktree workspaces and capture patches

  What to do: Delegate to Worker A. File ownership is only `scripts/blackcow_swarm_lib/scheduler.py` and `tests/test_swarm_scheduler.py`. Add `tests.test_swarm_scheduler.TestScheduler.test_writer_tasks_use_isolated_worktree_workspace` first. The test must create a clean temporary git repo, run one writer `ScheduledTask` with `run_dir = repo / ".omo" / "swarm" / "runs" / "run-writer-iso"`, record the `WorkerTask.workspace` seen by the runner, make the runner write `src/writer.txt` inside that workspace, and assert:
  - observed workspace equals `repo / ".worktrees" / "swarm" / "run-writer-iso" / "writer-iso-r1"`;
  - `repo / "src" / "writer.txt"` does not exist;
  - `.omo/swarm/runs/run-writer-iso/patches/writer-iso-r1.patch` exists and mentions `src/writer.txt`;
  - the scheduler state for `writer-iso` is `SUCCEEDED`.
  Capture RED before production changes. Then minimally change `Scheduler._run_one` and `_worker_task` so writer tasks create a `WorktreeManager(repo_root)` worktree, build prompt/result paths under the writer workspace to satisfy `runner.py` validation, call the runner with `workspace=writer_tree`, capture the patch into the main `run_dir`, copy or enrich the writer `result.json` under the main run directory if needed, and remove only test-created worktrees during test cleanup. Keep read-only scheduling unchanged.

  Must NOT do: Do not edit `task_graph.py`, `lifecycle.py`, `runner.py`, `worktree.py`, `blackcow_reasonix_acp_worker.py`, or any `water-check-app/` file. Do not make read-only workers use worktrees. Do not bypass `_validate_worker_paths`.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [5, 6, 7] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `scripts/blackcow_swarm_lib/scheduler.py:80-110` - scheduler run loop and ready-state handling to preserve.
  - Pattern:  `scripts/blackcow_swarm_lib/scheduler.py:125-152` - writer and single-task execution currently call `_run_one` with `repo_root`.
  - Pattern:  `scripts/blackcow_swarm_lib/scheduler.py:155-185` - `_worker_task` currently writes prompt/result under `run_dir` and sets `workspace=repo_root`.
  - API/Type: `scripts/blackcow_swarm_lib/worktree.py:25-57` - `WorktreeManager` create/capture/remove API.
  - API/Type: `scripts/blackcow_swarm_lib/runner.py:42-52` - `WorkerTask` fields.
  - API/Type: `scripts/blackcow_swarm_lib/runner.py:260-268` - path validation that prompt/result must be under workspace.
  - Test:     `tests/test_swarm_scheduler.py:23-43` - existing `make_task` helper.
  - Test:     `tests/test_swarm_scheduler.py:124-133` - temporary git repo setup pattern.
  - External: `https://git-scm.com/docs/git-worktree` - official worktree add/remove behavior; linked worktrees are separate working trees.

  Acceptance criteria (agent-executable only):
  - [ ] RED captured before implementation: `python3 -m unittest tests.test_swarm_scheduler.TestScheduler.test_writer_tasks_use_isolated_worktree_workspace -v` exits nonzero and output is saved to `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C001-red.txt`.
  - [ ] GREEN captured after implementation: `python3 -m unittest tests.test_swarm_scheduler.TestScheduler.test_writer_tasks_use_isolated_worktree_workspace -v` exits 0 and output is saved to `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-2-scheduler-green.txt`.
  - [ ] `python3 -m unittest tests.test_swarm_scheduler -v` exits 0.
  - [ ] `git diff -- tests/test_swarm_scheduler.py scripts/blackcow_swarm_lib/scheduler.py` contains no edits outside the declared files.

  QA scenarios (MANDATORY - task incomplete without these):
  > Name the exact tool AND its exact invocation - not "verify it works". Browser use: use Chrome to drive the page; if Chrome is not available, download and use agent-browser (https://github.com/vercel-labs/agent-browser). Computer use: OS-level GUI automation for a non-browser desktop app.
  ```
  Scenario: writer scheduler isolation
    Tool:     tmux
    Steps:    tmux new-session -d -s ulw-qa-task2-scheduler -c /Users/jeong-yugyeong/Project/blackcow-ops 'bash -lc "python3 -m unittest tests.test_swarm_scheduler.TestScheduler.test_writer_tasks_use_isolated_worktree_workspace -v"'; tmux capture-pane -pt ulw-qa-task2-scheduler -S - -E - > .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-2-blackcow-swarm-control-plane-continuation.txt; tmux kill-session -t ulw-qa-task2-scheduler
    Expected: artifact contains `test_writer_tasks_use_isolated_worktree_workspace` and `OK`.
    Evidence: .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-2-blackcow-swarm-control-plane-continuation.txt

  Scenario: read-only scheduler regression
    Tool:     bash
    Steps:    python3 -m unittest tests.test_swarm_scheduler.TestScheduler.test_read_only_tasks_overlap tests.test_swarm_scheduler.TestScheduler.test_read_only_dirty_repo_is_protocol_violation -v
    Expected: command exits 0 and output contains `OK`.
    Evidence: .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-2-blackcow-swarm-control-plane-continuation-error.txt
  ```

  Commit: NO | Message: `feat(swarm): isolate writer scheduler workspaces` | Files: [scripts/blackcow_swarm_lib/scheduler.py, tests/test_swarm_scheduler.py]

- [ ] 3. Expand writer replicas in generated task graphs only after worktree isolation is available

  What to do: Delegate to Worker B. File ownership is only `scripts/blackcow_swarm_lib/task_graph.py` and `tests/test_swarm_task_graph.py`. Replace the old single-writer test in `tests/test_swarm_task_graph.py:104-119` with `tests.test_swarm_task_graph.TestSwarmTaskGraph.test_writer_replicas_expand_when_worktree_isolation_enabled`. The RED test must create a max-intensity plan for `Create a new React Native Expo water drinking check app in water-check-app` with `max_workers=8`, then assert coder tasks have replicas greater than 1, not greater than `load_config().intensity["max"].max_writer_workers`, and not greater than `options.max_workers`. Capture RED while `_safe_writer_replicas()` still returns `1` at `scripts/blackcow_swarm_lib/task_graph.py:178-179`. Then change the smallest surface in `task_graph.py`: make `_safe_writer_replicas` accept the intensity profile and options, and return `min(profile.max_writer_workers, options.max_workers or profile.max_total_workers, max(2, estimate.recommended_workers))` when `estimate.writer_swarm_allowed` is true and the writer is not blocked. Preserve `1` for blocked/risky writers.

  Must NOT do: Do not edit `scheduler.py`, `lifecycle.py`, `config.py`, or `blackcow.swarm.json`. Do not create a new config flag unless the test proves it is necessary. Do not loosen risky writer approval behavior.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [5, 6, 7] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `scripts/blackcow_swarm_lib/task_graph.py:102-145` - graph construction, blocked writer path, coder task creation.
  - Pattern:  `scripts/blackcow_swarm_lib/task_graph.py:111-115` - existing profile and `writer_replicas` calculation site.
  - Pattern:  `scripts/blackcow_swarm_lib/task_graph.py:128-134` - coder/review/qa/judge task graph shape.
  - Pattern:  `scripts/blackcow_swarm_lib/task_graph.py:178-179` - current hardcoded `_safe_writer_replicas() -> 1`.
  - API/Type: `scripts/blackcow_swarm_lib/config.py:37-45` - `IntensityProfile.max_writer_workers`.
  - API/Type: `scripts/blackcow_swarm_lib/config.py:61-67` - `RuntimeOptions.max_workers`.
  - Pattern:  `scripts/blackcow_swarm_lib/estimate.py:81-90` - `recommended_workers`, `requires_approval`, and `writer_swarm_allowed`.
  - Test:     `tests/test_swarm_task_graph.py:81-102` - dangerous writer remains no coder swarm.
  - Test:     `tests/test_swarm_task_graph.py:176-202` - water-check future project acceptance checks, but do not edit `water-check-app/`.

  Acceptance criteria (agent-executable only):
  - [ ] RED captured before implementation: `python3 -m unittest tests.test_swarm_task_graph.TestSwarmTaskGraph.test_writer_replicas_expand_when_worktree_isolation_enabled -v` exits nonzero and output is saved to `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C001-taskgraph-red.txt`.
  - [ ] GREEN captured after implementation: `python3 -m unittest tests.test_swarm_task_graph.TestSwarmTaskGraph.test_writer_replicas_expand_when_worktree_isolation_enabled tests.test_swarm_task_graph.TestSwarmTaskGraph.test_dangerous_prompt_without_yes_has_no_coder_swarm -v` exits 0 and output is saved to `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-3-taskgraph-green.txt`.
  - [ ] `python3 -m unittest tests.test_swarm_task_graph -v` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  > Name the exact tool AND its exact invocation - not "verify it works". Browser use: use Chrome to drive the page; if Chrome is not available, download and use agent-browser (https://github.com/vercel-labs/agent-browser). Computer use: OS-level GUI automation for a non-browser desktop app.
  ```
  Scenario: writer replica expansion
    Tool:     tmux
    Steps:    tmux new-session -d -s ulw-qa-task3-taskgraph -c /Users/jeong-yugyeong/Project/blackcow-ops 'bash -lc "python3 -m unittest tests.test_swarm_task_graph.TestSwarmTaskGraph.test_writer_replicas_expand_when_worktree_isolation_enabled -v"'; tmux capture-pane -pt ulw-qa-task3-taskgraph -S - -E - > .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-3-blackcow-swarm-control-plane-continuation.txt; tmux kill-session -t ulw-qa-task3-taskgraph
    Expected: artifact contains `test_writer_replicas_expand_when_worktree_isolation_enabled` and `OK`.
    Evidence: .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-3-blackcow-swarm-control-plane-continuation.txt

  Scenario: risky writer remains blocked
    Tool:     bash
    Steps:    python3 -m unittest tests.test_swarm_task_graph.TestSwarmTaskGraph.test_dangerous_prompt_without_yes_has_no_coder_swarm -v
    Expected: command exits 0 and output contains `OK`.
    Evidence: .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-3-blackcow-swarm-control-plane-continuation-error.txt
  ```

  Commit: NO | Message: `feat(swarm): expand safe writer replicas` | Files: [scripts/blackcow_swarm_lib/task_graph.py, tests/test_swarm_task_graph.py]

- [ ] 4. Cover C002 edge cases and purge writer patches during cleanup

  What to do: Delegate to Worker C. File ownership is only `scripts/blackcow_swarm_lib/lifecycle.py`, `tests/test_swarm_cancel_cleanup.py`, and `tests/test_swarm_worktree.py`. Add `tests.test_swarm_worktree.TestWorktree.test_create_writer_worktree_allows_ignored_dirty_swarm_artifacts` as characterization coverage: in the temp git repo, create ignored `.omo/swarm/runs/stale/leftover.txt` and `.worktrees/swarm/stale/leftover.txt`, assert `git status --porcelain` remains empty, then assert `create_writer_worktree("run-ignored", "writer-ignored-r1")` succeeds. Keep `tests.test_swarm_worktree.TestWorktree.test_rejects_path_traversal_ids` and extend it only if needed to include empty ids. Add RED test `tests.test_swarm_cancel_cleanup.TestCancelCleanup.test_cleanup_purges_writer_worktrees_and_patches`: create `.worktrees/swarm/run-clean`, `.omo/swarm/runs/run-clean/patches/writer-1-r1.patch`, audit files `events.jsonl`, `final_judgement.json`, `reports/tournament.md`; call `cleanup_run`; assert worktree dir and `patches/` are removed while audit files remain. Then minimally update `cleanup_run` so it removes `patches` in addition to `workers`, `planned-results`, and `prompts`, while still preserving audit/report files.

  Must NOT do: Do not edit `scheduler.py` or `task_graph.py`. Do not remove `events.jsonl`, `state.json`, `final_judgement.json`, `reports/`, screenshots, visual reviews, or feedback packets. Do not replace `git worktree remove` behavior in `WorktreeManager` unless the RED test proves it is necessary.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [5, 6, 7] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `tests/test_swarm_worktree.py:11-60` - current worktree tests and malformed id test.
  - Pattern:  `tests/test_swarm_worktree.py:61-77` - temp git repo setup with `.gitignore`.
  - API/Type: `scripts/blackcow_swarm_lib/worktree.py:59-67` - clean root check and safe id validation.
  - Pattern:  `scripts/blackcow_swarm_lib/lifecycle.py:88-101` - cleanup currently removes worktrees, workers, planned-results, prompts.
  - Test:     `tests/test_swarm_cancel_cleanup.py:48-68` - cleanup preserves audit files.
  - External: `https://git-scm.com/docs/git-worktree` - official `git worktree remove` and `git worktree prune` behavior.

  Acceptance criteria (agent-executable only):
  - [ ] RED captured before implementation: `python3 -m unittest tests.test_swarm_cancel_cleanup.TestCancelCleanup.test_cleanup_purges_writer_worktrees_and_patches -v` exits nonzero and output is saved to `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C002-red.txt`.
  - [ ] GREEN captured after implementation: `python3 -m unittest tests.test_swarm_worktree.TestWorktree.test_create_writer_worktree_allows_ignored_dirty_swarm_artifacts tests.test_swarm_worktree.TestWorktree.test_rejects_path_traversal_ids tests.test_swarm_cancel_cleanup.TestCancelCleanup.test_cleanup_purges_writer_worktrees_and_patches -v` exits 0 and output is saved to `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C002-green.txt`.
  - [ ] `python3 -m unittest tests.test_swarm_worktree tests.test_swarm_cancel_cleanup -v` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  > Name the exact tool AND its exact invocation - not "verify it works". Browser use: use Chrome to drive the page; if Chrome is not available, download and use agent-browser (https://github.com/vercel-labs/agent-browser). Computer use: OS-level GUI automation for a non-browser desktop app.
  ```
  Scenario: C002 cleanup and malformed edge tests
    Tool:     tmux
    Steps:    tmux new-session -d -s ulw-qa-task4-c002 -c /Users/jeong-yugyeong/Project/blackcow-ops 'bash -lc "python3 -m unittest tests.test_swarm_worktree.TestWorktree.test_create_writer_worktree_allows_ignored_dirty_swarm_artifacts tests.test_swarm_worktree.TestWorktree.test_rejects_path_traversal_ids tests.test_swarm_cancel_cleanup.TestCancelCleanup.test_cleanup_purges_writer_worktrees_and_patches -v"'; tmux capture-pane -pt ulw-qa-task4-c002 -S - -E - > .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-4-blackcow-swarm-control-plane-continuation.txt; tmux kill-session -t ulw-qa-task4-c002
    Expected: artifact contains all three test ids and `OK`.
    Evidence: .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-4-blackcow-swarm-control-plane-continuation.txt

  Scenario: cleanup preserves audit files
    Tool:     bash
    Steps:    python3 -m unittest tests.test_swarm_cancel_cleanup.TestCancelCleanup.test_cleanup_removes_worktrees_and_preserves_audit_files -v
    Expected: command exits 0 and output contains `OK`.
    Evidence: .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-4-blackcow-swarm-control-plane-continuation-error.txt
  ```

  Commit: NO | Message: `fix(swarm): purge writer patch artifacts on cleanup` | Files: [scripts/blackcow_swarm_lib/lifecycle.py, tests/test_swarm_cancel_cleanup.py, tests/test_swarm_worktree.py]

- [ ] 5. Capture official C001 and C002 tmux QA artifacts

  What to do: Main agent only after Tasks 2-4 are GREEN. Run the exact accepted C001 and C002 tmux scenarios from `goals.json`. Save the pane captures to the exact criterion evidence paths. Append cleanup receipts showing `tmux has-session` fails after killing the sessions. This task does not add code; it proves the real CLI/tmux surface required by the loop criteria.

  Must NOT do: Do not substitute direct shell output for tmux captures. Do not run against `water-check-app/`. Do not leave tmux sessions alive.

  Parallelization: Can parallel: NO | Wave 2 | Blocks: [6, 7] | Blocked by: [2, 3, 4]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/goals.json:16-23` - C001 accepted scenario and evidence paths.
  - Pattern:  `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/goals.json:24-31` - C002 accepted scenario and evidence paths.
  - External: `https://man7.org/linux/man-pages/man1/tmux.1.html` - official tmux command reference for `new-session`, `capture-pane`, and `kill-session`.
  - External: `https://docs.python.org/3/library/unittest.html#test-discovery` - official unittest test id invocation behavior.

  Acceptance criteria (agent-executable only):
  - [ ] `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C001-writer-isolation-tmux.txt` exists and contains `OK`.
  - [ ] `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C002-cleanup-cancel-tmux.txt` exists and contains `OK`.
  - [ ] `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C001-green.txt` and `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C002-green.txt` exist.
  - [ ] `tmux has-session -t ulw-qa-writer-isolation` exits nonzero after cleanup.
  - [ ] `tmux has-session -t ulw-qa-cleanup-cancel` exits nonzero after cleanup.

  QA scenarios (MANDATORY - task incomplete without these):
  > Name the exact tool AND its exact invocation - not "verify it works". Browser use: use Chrome to drive the page; if Chrome is not available, download and use agent-browser (https://github.com/vercel-labs/agent-browser). Computer use: OS-level GUI automation for a non-browser desktop app.
  ```
  Scenario: C001 accepted writer-isolation tmux criterion
    Tool:     tmux
    Steps:    tmux new-session -d -s ulw-qa-writer-isolation -c /Users/jeong-yugyeong/Project/blackcow-ops 'bash -lc "python3 -m unittest tests.test_swarm_scheduler.TestScheduler.test_writer_tasks_use_isolated_worktree_workspace tests.test_swarm_task_graph.TestSwarmTaskGraph.test_writer_replicas_expand_when_worktree_isolation_enabled -v"'; tmux capture-pane -pt ulw-qa-writer-isolation -S - -E - > .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C001-writer-isolation-tmux.txt; tmux kill-session -t ulw-qa-writer-isolation; tmux has-session -t ulw-qa-writer-isolation 2>/dev/null || echo "cleanup: ulw-qa-writer-isolation removed" >> .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C001-writer-isolation-tmux.txt
    Expected: artifact contains both C001 test ids, `OK`, and `cleanup: ulw-qa-writer-isolation removed`.
    Evidence: .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C001-writer-isolation-tmux.txt

  Scenario: C002 accepted cleanup-cancel tmux criterion
    Tool:     tmux
    Steps:    tmux new-session -d -s ulw-qa-cleanup-cancel -c /Users/jeong-yugyeong/Project/blackcow-ops 'bash -lc "python3 -m unittest tests.test_swarm_worktree.TestWorktree.test_create_writer_worktree_allows_ignored_dirty_swarm_artifacts tests.test_swarm_worktree.TestWorktree.test_rejects_path_traversal_ids tests.test_swarm_cancel_cleanup.TestCancelCleanup.test_cleanup_purges_writer_worktrees_and_patches -v"'; tmux capture-pane -pt ulw-qa-cleanup-cancel -S - -E - > .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C002-cleanup-cancel-tmux.txt; tmux kill-session -t ulw-qa-cleanup-cancel; tmux has-session -t ulw-qa-cleanup-cancel 2>/dev/null || echo "cleanup: ulw-qa-cleanup-cancel removed" >> .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C002-cleanup-cancel-tmux.txt
    Expected: artifact contains all three C002 test ids, `OK`, and `cleanup: ulw-qa-cleanup-cancel removed`.
    Evidence: .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C002-cleanup-cancel-tmux.txt
  ```

  Commit: NO | Message: `test(swarm): capture c001 c002 tmux evidence` | Files: [.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C001-writer-isolation-tmux.txt, .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C002-cleanup-cancel-tmux.txt]

- [ ] 6. Capture C003 full regression tmux artifact

  What to do: Main agent only after Task 5 passes. Run the accepted C003 command through tmux, capture the pane to the exact evidence path, and append cleanup receipt. If the ecosystem script fails because the local dirty checkout has unrelated pre-existing skill/document changes, do not "fix" unrelated files. Instead, capture the failure output and stop for review. If it passes, save the same output to `C003-green.txt` or copy the pane artifact path into that file.

  Must NOT do: Do not weaken validation scripts. Do not edit skill files unless the failure is directly caused by Tasks 2-4 and the owning worker is recalled. Do not hand-fix unrelated docs or apps.

  Parallelization: Can parallel: NO | Wave 2 | Blocks: [7] | Blocked by: [5]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/goals.json:32-39` - C003 accepted scenario and evidence path.
  - Pattern:  `skills/tests/validate-blackcow-swarm.sh:38-144` - swarm contract validation and success condition.
  - Pattern:  `skills/tests/validate-blackcow-ecosystem.sh:1-22` - ecosystem script purpose and exit-code contract.
  - Pattern:  `tests/test_swarm_scheduler.py:45-122` - adjacent scheduler regression tests.
  - Pattern:  `tests/test_swarm_task_graph.py:29-217` - task graph regression surface.

  Acceptance criteria (agent-executable only):
  - [ ] `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C003-regression-tmux.txt` exists and contains `OK`.
  - [ ] `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C003-regression-tmux.txt` contains `BlackCow Swarm Contract Validation`.
  - [ ] `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C003-regression-tmux.txt` contains either `Results:` with zero failed or the validation script's pass summary.
  - [ ] `tmux has-session -t ulw-qa-regression` exits nonzero after cleanup.

  QA scenarios (MANDATORY - task incomplete without these):
  > Name the exact tool AND its exact invocation - not "verify it works". Browser use: use Chrome to drive the page; if Chrome is not available, download and use agent-browser (https://github.com/vercel-labs/agent-browser). Computer use: OS-level GUI automation for a non-browser desktop app.
  ```
  Scenario: full C003 regression
    Tool:     tmux
    Steps:    tmux new-session -d -s ulw-qa-regression -c /Users/jeong-yugyeong/Project/blackcow-ops 'bash -lc "python3 -m unittest discover -s tests -p '\''test_swarm_*.py'\'' -v && bash skills/tests/validate-blackcow-swarm.sh && bash skills/tests/validate-blackcow-ecosystem.sh --quiet"'; tmux capture-pane -pt ulw-qa-regression -S - -E - > .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C003-regression-tmux.txt; cp .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C003-regression-tmux.txt .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C003-green.txt; tmux kill-session -t ulw-qa-regression; tmux has-session -t ulw-qa-regression 2>/dev/null || echo "cleanup: ulw-qa-regression removed" >> .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C003-regression-tmux.txt
    Expected: artifact contains unittest `OK`, `BlackCow Swarm Contract Validation`, ecosystem validation output, and `cleanup: ulw-qa-regression removed`.
    Evidence: .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C003-regression-tmux.txt

  Scenario: changed-file scope guard
    Tool:     bash
    Steps:    python3 -c 'import subprocess; paths=subprocess.check_output(["git","diff","--name-only","--","scripts","tests","skills","water-check-app"], text=True).splitlines(); bad=[p for p in paths if p.startswith("water-check-app/")]; assert not bad, bad; print("\n".join(paths))'
    Expected: command exits 0 and no path begins with `water-check-app/`.
    Evidence: .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-6-blackcow-swarm-control-plane-continuation-error.txt
  ```

  Commit: NO | Message: `test(swarm): capture full control-plane regression` | Files: [.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C003-regression-tmux.txt, .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C003-green.txt]

- [ ] 7. Final evidence, scope, and cleanup audit

  What to do: Main agent only. Audit that every C001-C003 evidence file exists, every expected RED/GREEN file exists, no tmux sessions remain, no `water-check-app/` path is in the diff, and no task owned by one worker edited another worker's files. Write a concise final audit to `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-7-final-audit.txt`.

  Must NOT do: Do not commit. Do not mark the goal complete unless the active loop mechanism accepts all criteria from captured evidence. Do not delete evidence files.

  Parallelization: Can parallel: NO | Wave 3 | Blocks: [] | Blocked by: [1, 5, 6]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/goals.json:16-39` - all active criteria and expected evidence paths.
  - Pattern:  `.gitignore:18-20` - swarm runtime artifacts are ignored.
  - Pattern:  `scripts/blackcow_swarm_lib/scheduler.py:13-27` - single-writer path patterns must remain intact.
  - Pattern:  `skills/blackcow-swarm.md:159-187` - write isolation and cleanup requirements.

  Acceptance criteria (agent-executable only):
  - [ ] `test -s .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C001-red.txt` exits 0.
  - [ ] `test -s .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C001-green.txt` exits 0.
  - [ ] `test -s .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C002-red.txt` exits 0.
  - [ ] `test -s .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C002-green.txt` exits 0.
  - [ ] `test -s .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/C003-green.txt` exits 0.
  - [ ] `tmux ls` does not list `ulw-qa-writer-isolation`, `ulw-qa-cleanup-cancel`, or `ulw-qa-regression`.
  - [ ] `git diff --name-only -- water-check-app` produces no output.

  QA scenarios (MANDATORY - task incomplete without these):
  > Name the exact tool AND its exact invocation - not "verify it works". Browser use: use Chrome to drive the page; if Chrome is not available, download and use agent-browser (https://github.com/vercel-labs/agent-browser). Computer use: OS-level GUI automation for a non-browser desktop app.
  ```
  Scenario: final artifact and cleanup audit
    Tool:     bash
    Steps:    python3 - <<'PY'\nfrom pathlib import Path\nbase=Path('.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence')\nrequired=['C001-red.txt','C001-green.txt','C001-writer-isolation-tmux.txt','C002-red.txt','C002-green.txt','C002-cleanup-cancel-tmux.txt','C003-green.txt','C003-regression-tmux.txt']\nmissing=[name for name in required if not (base/name).exists() or (base/name).stat().st_size==0]\nassert not missing, missing\nprint('required evidence present')\nPY
    Expected: command exits 0 and prints `required evidence present`.
    Evidence: .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-7-final-audit.txt

  Scenario: water-check scope guard
    Tool:     bash
    Steps:    python3 -c 'import subprocess; paths=subprocess.check_output(["git","diff","--name-only","--","water-check-app"], text=True).splitlines(); assert not paths, paths; print("water-check-app untouched")'
    Expected: command exits 0 and prints `water-check-app untouched`.
    Evidence: .omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-7-final-audit-error.txt
  ```

  Commit: NO | Message: `chore(swarm): audit control-plane continuation evidence` | Files: [.omo/ulw-loop/019ed331-2762-7a10-8e27-394039035a12/evidence/task-7-final-audit.txt]

## Final verification wave (MANDATORY - after all implementation tasks)
> Runs in PARALLEL. ALL must APPROVE. Surface results to the caller and wait for an explicit "okay" before declaring complete.
- [ ] F1. Plan compliance audit - every task done, every acceptance criterion met
- [ ] F2. Code quality review - diagnostics clean, idioms match, no dead code
- [ ] F3. Real manual QA - every QA scenario executed with evidence captured
- [ ] F4. Scope fidelity - nothing extra shipped beyond Must-Have, nothing Must-NOT-Have introduced

## Commit strategy
- One logical change per commit. Conventional Commits (`<type>(<scope>): <subject>` body + footer).
- Atomic: every commit builds and passes tests on its own.
- No "WIP" / "fix typo squash later" commits on the final branch - clean up before merge.
- Reference the plan file path in the final commit footer: `Plan: plans/blackcow-swarm-control-plane-continuation.md`.
- For this request specifically, do not commit. Present draft commit messages only after all evidence passes.

## Success criteria
- All Must-Have shipped; all QA scenarios pass with captured evidence; F1-F4 approved; commit history clean.
