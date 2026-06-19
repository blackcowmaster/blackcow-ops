from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScheduledTask:
    task_id: str
    replica_id: str
    kind: str
    skill: str
    prompt: str
    depends_on: tuple[str, ...]
    read_only: bool
    writes: tuple[str, ...]
    acceptance_checks: tuple[str, ...]
    timeout_seconds: int


@dataclass(frozen=True, slots=True)
class TaskInterval:
    task_id: str
    started_at: float
    finished_at: float


@dataclass(frozen=True, slots=True)
class ScheduleEvent:
    event: str
    task_id: str


@dataclass(frozen=True, slots=True)
class TaskRun:
    task_id: str
    state: str
    interval: TaskInterval
    events: tuple[ScheduleEvent, ...]


@dataclass(frozen=True, slots=True)
class ScheduleReport:
    states: dict[str, str]
    intervals: dict[str, TaskInterval]
    events: list[ScheduleEvent]
