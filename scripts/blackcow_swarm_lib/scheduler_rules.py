from __future__ import annotations

import fnmatch
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Final


REPLICA_SUFFIX = re.compile(r"-r[1-9][0-9]*$")
ACTIVE_STATES: Final = ("PENDING", "READY", "LEASED", "RUNNING")
REPOSITORY_WIDE_WRITES: Final = ("**", "**/*")
SINGLE_WRITER_PATTERNS: Final = (
    "package-lock.json", "**/package-lock.json", "pnpm-lock.yaml", "**/pnpm-lock.yaml", "yarn.lock", "**/yarn.lock",
    "npm-shrinkwrap.json", "**/npm-shrinkwrap.json", "bun.lock", "**/bun.lock", "bun.lockb", "**/bun.lockb",
    "Cargo.lock", "**/Cargo.lock", "go.sum", "**/go.sum", "poetry.lock", "**/poetry.lock", "Pipfile.lock",
    "**/Pipfile.lock", "uv.lock", "**/uv.lock", "requirements.txt", "**/requirements.txt", "pyproject.toml",
    "**/pyproject.toml", "package.json", "**/package.json", "pnpm-workspace.yaml", "**/pnpm-workspace.yaml",
    ".github/**", "infra/**", "infrastructure/**", "terraform/**", "*.tf", "*.tfvars", "Dockerfile",
    "docker-compose*.yml", "docker-compose*.yaml", "k8s/**", "helm/**", "auth/**", "**/auth/**",
    "**/permissions/**", "**/rbac/**",
)


def task_group_id(task_id_or_replica_id: str) -> str:
    return REPLICA_SUFFIX.sub("", task_id_or_replica_id)


def worker_run_succeeded(states: Mapping[str, str]) -> bool:
    groups: dict[str, list[str]] = {}
    for task_id, state in states.items():
        groups.setdefault(task_group_id(task_id), []).append(state)
    return all("SUCCEEDED" in group_states for group_states in groups.values())


def worker_status(states: Mapping[str, str]) -> str:
    return "SUCCEEDED" if worker_run_succeeded(states) else "FAILED"


def task_report_keys(task_ids: Iterable[tuple[str, str]]) -> dict[str, str]:
    pairs = tuple(task_ids)
    replica_ids = [replica_id for _, replica_id in pairs]
    if len(set(replica_ids)) != len(replica_ids):
        raise ValueError("duplicate replica_id")
    counts = Counter(task_id for task_id, _ in pairs)
    return {
        replica_id: replica_id if counts[task_id] > 1 else task_id
        for task_id, replica_id in pairs
    }


def dependency_satisfied(dependency: str, succeeded_tasks: set[str], succeeded_groups: set[str]) -> bool:
    return dependency in succeeded_tasks or task_group_id(dependency) in succeeded_groups


def dependency_failed(dependency: str, failed_groups: set[str]) -> bool:
    return task_group_id(dependency) in failed_groups


def failed_task_groups(task_groups_by_key: dict[str, str], states: dict[str, str], succeeded_groups: set[str]) -> set[str]:
    groups = set(task_groups_by_key.values())
    return {
        group
        for group in groups
        if group not in succeeded_groups
        and all(states[key] not in ACTIVE_STATES for key, task_group in task_groups_by_key.items() if task_group == group)
    }


def single_writer_patterns(writes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(pattern for pattern in SINGLE_WRITER_PATTERNS if any(write_scope_matches(write, pattern) for write in writes))


def write_scope_matches(write_scope: str, pattern: str) -> bool:
    scope = write_scope.strip("/")
    locked = pattern.strip("/")
    if scope in REPOSITORY_WIDE_WRITES:
        return False
    if fnmatch.fnmatchcase(scope, locked) or fnmatch.fnmatchcase(locked, scope):
        return True
    return _root_parent_scope_can_contain_nested_risk(scope, locked)


def _root_parent_scope_can_contain_nested_risk(scope: str, locked: str) -> bool:
    return _is_root_parent_scope(scope) and locked.startswith("**/")


def _is_root_parent_scope(scope: str) -> bool:
    if not scope.endswith("/**"):
        return False
    return "/" not in scope.removesuffix("/**")
