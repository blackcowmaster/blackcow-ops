from __future__ import annotations

import subprocess
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Protocol

from . import scheduler_rules as rules
from .forbidden_sources import forbidden_source_violation, forbidden_sources_from_prompt, write_forbidden_source_report
from .runner import RunnerOutcome, WorkerTask
from .scheduler_patch_scope import patch_scope_violation, write_patch_scope_violation_report
from .scheduler_read_guard import git_status, write_dirty_diff, write_writer_root_diff
from .scheduler_types import ScheduledTask, ScheduleEvent, ScheduleReport, TaskInterval, TaskRun
from .scheduler_worker import copy_to_audit_dir, failed_writer_run, worker_task, writer_artifact_dir
from .worktree import PatchCandidate, WorktreeError, WorktreeManager


class RunnerProtocol(Protocol):
    def run(self, task: WorkerTask) -> RunnerOutcome: ...


class SchedulerDependencyError(ValueError):
    pass


class Scheduler:
    def __init__(self, max_workers: int) -> None:
        self.max_workers = max(1, max_workers)
        self._single_writer_locks = {pattern: threading.Lock() for pattern in rules.SINGLE_WRITER_PATTERNS}
        self._worktree_setup_lock = threading.Lock()

    def run(
        self,
        tasks: list[ScheduledTask],
        runner: RunnerProtocol,
        repo_root: Path,
        run_dir: Path,
    ) -> ScheduleReport:
        report_keys = rules.task_report_keys((task.task_id, task.replica_id) for task in tasks)
        tasks_by_key = {report_keys[task.replica_id]: task for task in tasks}
        task_groups_by_key = {key: rules.task_group_id(task.task_id) for key, task in tasks_by_key.items()}
        pending = dict(tasks_by_key)
        states = {key: "PENDING" for key in tasks_by_key}
        intervals: dict[str, TaskInterval] = {}
        events: list[ScheduleEvent] = []
        succeeded_tasks: set[str] = set()
        succeeded_groups: set[str] = set()
        failed_groups: set[str] = set()
        while pending:
            ready = [
                task
                for task in pending.values()
                if all(rules.dependency_satisfied(dependency, succeeded_tasks, succeeded_groups) for dependency in task.depends_on)
            ]
            if not ready:
                blocked = [
                    task for task in pending.values() if any(rules.dependency_failed(dependency, failed_groups) for dependency in task.depends_on)
                ]
                if not blocked:
                    raise SchedulerDependencyError("dependency cycle or unsatisfied dependency")
                self._block_tasks(blocked, pending, states, intervals, events, report_keys)
                failed_groups = rules.failed_task_groups(task_groups_by_key, states, succeeded_groups)
                continue
            for task in ready:
                key = report_keys[task.replica_id]
                states[key] = "READY"
                events.append(ScheduleEvent("READY", key))
            read_only_ready = [task for task in ready if task.read_only]
            runs = self._run_read_only(read_only_ready, runner, repo_root, run_dir, report_keys) if read_only_ready else []
            runs.extend(self._run_writers([task for task in ready if not task.read_only], runner, repo_root, run_dir, report_keys))
            for run in runs:
                states[run.task_id] = run.state
                intervals[run.task_id] = run.interval
                events.extend(run.events)
                pending.pop(run.task_id, None)
                if run.state == "SUCCEEDED":
                    succeeded_tasks.add(run.task_id)
                    succeeded_groups.add(task_groups_by_key[run.task_id])
            failed_groups = rules.failed_task_groups(task_groups_by_key, states, succeeded_groups)
        return ScheduleReport(states=states, intervals=intervals, events=events)

    def _block_tasks(
        self,
        tasks: list[ScheduledTask],
        pending: dict[str, ScheduledTask],
        states: dict[str, str],
        intervals: dict[str, TaskInterval],
        events: list[ScheduleEvent],
        report_keys: dict[str, str],
    ) -> None:
        now = time.time()
        for task in tasks:
            key = report_keys[task.replica_id]
            states[key] = "BLOCKED"
            intervals[key] = TaskInterval(key, now, now)
            events.append(ScheduleEvent("BLOCKED", key))
            pending.pop(key, None)

    def _run_read_only(
        self,
        tasks: list[ScheduledTask],
        runner: RunnerProtocol,
        repo_root: Path,
        run_dir: Path,
        report_keys: dict[str, str],
    ) -> list[TaskRun]:
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(tasks))) as pool:
            futures = [pool.submit(self._run_one, task, report_keys[task.replica_id], runner, repo_root, run_dir) for task in tasks]
            return [future.result() for future in as_completed(futures)]

    def _run_writers(
        self,
        tasks: list[ScheduledTask],
        runner: RunnerProtocol,
        repo_root: Path,
        run_dir: Path,
        report_keys: dict[str, str],
    ) -> list[TaskRun]:
        locked_tasks = [task for task in tasks if rules.single_writer_patterns(task.writes)]
        safe_tasks = [task for task in tasks if not rules.single_writer_patterns(task.writes)]
        runs = [self._run_locked_writer(task, report_keys[task.replica_id], runner, repo_root, run_dir) for task in locked_tasks]
        with ThreadPoolExecutor(max_workers=max(1, min(self.max_workers, len(safe_tasks)))) as pool:
            futures = [pool.submit(self._run_one, task, report_keys[task.replica_id], runner, repo_root, run_dir) for task in safe_tasks]
            runs.extend(future.result() for future in futures)
        return runs

    def _run_locked_writer(
        self,
        task: ScheduledTask,
        report_key: str,
        runner: RunnerProtocol,
        repo_root: Path,
        run_dir: Path,
    ) -> TaskRun:
        locks = [self._single_writer_locks[pattern] for pattern in rules.single_writer_patterns(task.writes)]
        for lock in locks:
            lock.acquire()
        try:
            return self._run_one(task, report_key, runner, repo_root, run_dir)
        finally:
            for lock in reversed(locks):
                lock.release()

    def _run_one(self, task: ScheduledTask, report_key: str, runner: RunnerProtocol, repo_root: Path, run_dir: Path) -> TaskRun:
        events = [ScheduleEvent("LEASED", report_key), ScheduleEvent("RUNNING", report_key)]
        started_at = time.time()
        before = git_status(repo_root, run_dir) if task.read_only else ""
        root_before = git_status(repo_root, run_dir) if not task.read_only else {}
        worktree_manager = WorktreeManager(repo_root) if not task.read_only else None
        worker_tree = None
        worker_artifacts = None
        patch_candidate: PatchCandidate | None = None
        try:
            if task.read_only:
                workspace = repo_root
                job = worker_task(task, repo_root=repo_root, run_dir=run_dir, workspace=workspace)
            else:
                assert worktree_manager is not None
                try:
                    with self._worktree_setup_lock:
                        worker_tree = worktree_manager.create_writer_worktree(
                            run_dir.name,
                            task.replica_id,
                            forbidden_paths=forbidden_sources_from_prompt(task.prompt),
                        )
                except (WorktreeError, subprocess.CalledProcessError) as exc:
                    return failed_writer_run(report_key, task, run_dir, started_at, events, "setup", exc)
                worker_artifacts = writer_artifact_dir(workspace=worker_tree, run_dir=run_dir, replica_id=task.replica_id)
                job = worker_task(task, repo_root=repo_root, run_dir=run_dir, workspace=worker_tree)
            outcome = runner.run(job)
            if worker_artifacts is not None:
                copy_to_audit_dir(worker_artifacts, run_dir / "workers" / task.replica_id)
            if worker_tree is not None:
                if worker_artifacts is not None:
                    shutil.rmtree(worker_artifacts, ignore_errors=True)
                try:
                    patch_candidate = worktree_manager.capture_patch(worker_tree, run_dir.name, task.replica_id, task.writes)
                except (WorktreeError, subprocess.CalledProcessError) as exc:
                    return failed_writer_run(report_key, task, run_dir, started_at, events, "capture", exc)
        finally:
            if worker_tree is not None:
                worktree_manager.remove_worktree(worker_tree)
        after = git_status(repo_root, run_dir) if task.read_only else before
        root_after = git_status(repo_root, run_dir) if not task.read_only else root_before
        interval = TaskInterval(report_key, outcome.started_at, outcome.finished_at)
        state = outcome.status
        if patch_candidate is not None and state == "SUCCEEDED" and patch_scope_violation(patch_candidate):
            write_patch_scope_violation_report(run_dir, task, patch_candidate)
            state = "FAILED_RETRYABLE"
            events.append(ScheduleEvent("PATCH_SCOPE_VIOLATION", report_key))
        if state == "SUCCEEDED":
            violation = forbidden_source_violation(task.prompt, job.result_json)
            if violation is not None:
                write_forbidden_source_report(run_dir, report_key, task.prompt, job.result_json, violation)
                state = "PROTOCOL_VIOLATION"
                events.append(ScheduleEvent("FORBIDDEN_SOURCE_VIOLATION", report_key))
        if task.read_only and before != after:
            write_dirty_diff(repo_root, run_dir, report_key, before, after)
            state = "PROTOCOL_VIOLATION"
            events.append(ScheduleEvent("PROTOCOL_VIOLATION", report_key))
        elif not task.read_only and root_before != root_after:
            write_writer_root_diff(repo_root, run_dir, report_key, root_before, root_after)
            state = "PROTOCOL_VIOLATION"
            events.append(ScheduleEvent("PROTOCOL_VIOLATION", report_key))
        else:
            events.append(ScheduleEvent(state, report_key))
        return TaskRun(report_key, state, interval, tuple(events))
