from __future__ import annotations

from typing import Protocol

from .runner import RunnerOutcome, WorkerTask


class RunnerProtocol(Protocol):
    def run(self, task: WorkerTask) -> RunnerOutcome: ...


class RetryingRunner:
    def __init__(self, delegate: RunnerProtocol, retry_limit: int) -> None:
        self.delegate = delegate
        self.retry_limit = max(0, retry_limit)

    def run(self, task: WorkerTask) -> RunnerOutcome:
        attempts = self.retry_limit + 1
        for attempt_index in range(attempts):
            outcome = self.delegate.run(task)
            if outcome.status != "FAILED_RETRYABLE" or attempt_index == self.retry_limit:
                return _with_retry_events(outcome, attempt_index)
        return outcome


def _with_retry_events(outcome: RunnerOutcome, attempt_index: int) -> RunnerOutcome:
    if attempt_index == 0:
        return outcome
    return RunnerOutcome(
        status=outcome.status,
        result_path=outcome.result_path,
        command=outcome.command,
        started_at=outcome.started_at,
        finished_at=outcome.finished_at,
        process=outcome.process,
        events=(*outcome.events, f"retry_attempts={attempt_index}"),
    )
