from __future__ import annotations

from collections.abc import Mapping, Sequence

from .config import INTENSITIES, MODES, POLICIES, JsonValue


TASK_KINDS = ("discovery", "qa", "review", "coder", "writer", "integration", "judge")
RESULT_STATUSES = ("SUCCEEDED", "FAILED_RETRYABLE", "FAILED_FINAL", "CANCELLED", "TIMED_OUT")
FINAL_STATUSES = ("SUCCEEDED", "FAILED", "CANCELLED", "BLOCKED")
SCORE_FIELDS = ("overall", "correctness", "safety", "tests")


class SchemaError(ValueError):
    pass


def validate_task_graph(payload: JsonValue) -> None:
    root = _mapping(payload, "task_graph")
    _non_empty_string(_required(root, "run_id", "task_graph"), "task_graph.run_id")
    tasks = _list(_required(root, "tasks", "task_graph"), "task_graph.tasks")
    task_ids: set[str] = set()
    for index, task_payload in enumerate(tasks):
        task = _mapping(task_payload, f"task_graph.tasks[{index}]")
        task_id = _non_empty_string(_required(task, "id", f"tasks[{index}]"), f"tasks[{index}].id")
        if task_id in task_ids:
            raise SchemaError(f"duplicate task id: {task_id}")
        task_ids.add(task_id)
        _enum(_string_required(task, "kind", index), TASK_KINDS, f"tasks[{index}].kind")
        _non_empty_string(_required(task, "title", f"tasks[{index}]"), f"tasks[{index}].title")
        _non_empty_string(_required(task, "skill", f"tasks[{index}]"), f"tasks[{index}].skill")
        _non_empty_string(_required(task, "prompt", f"tasks[{index}]"), f"tasks[{index}].prompt")
        _string_list(_required(task, "depends_on", f"tasks[{index}]"), f"tasks[{index}].depends_on")
        _bool(_required(task, "read_only", f"tasks[{index}]"), f"tasks[{index}].read_only")
        _string_list(_required(task, "writes", f"tasks[{index}]"), f"tasks[{index}].writes")
        _string_list(_required(task, "write_scope", f"tasks[{index}]"), f"tasks[{index}].write_scope")
        _string_list(_required(task, "acceptance_checks", f"tasks[{index}]"), f"tasks[{index}].acceptance_checks")
        _positive_int(_required(task, "replicas", f"tasks[{index}]"), f"tasks[{index}].replicas")
        _positive_int(_required(task, "max_replicas", f"tasks[{index}]"), f"tasks[{index}].max_replicas")
        _positive_int(_required(task, "timeout_minutes", f"tasks[{index}]"), f"tasks[{index}].timeout_minutes")
    for index, task_payload in enumerate(tasks):
        task = _mapping(task_payload, f"task_graph.tasks[{index}]")
        for dependency in _string_list(_required(task, "depends_on", f"tasks[{index}]"), f"tasks[{index}].depends_on"):
            if dependency not in task_ids:
                raise SchemaError(f"tasks[{index}].depends_on references unknown task: {dependency}")


def validate_result(payload: JsonValue) -> None:
    root = _mapping(payload, "result")
    _non_empty_string(_required(root, "task_id", "result"), "result.task_id")
    _non_empty_string(_required(root, "replica_id", "result"), "result.replica_id")
    _enum(_string(_required(root, "status", "result"), "result.status"), RESULT_STATUSES, "result.status")
    _string(_required(root, "summary", "result"), "result.summary")
    _string_list(_required(root, "artifacts", "result"), "result.artifacts")
    _string_list(_required(root, "changed_files", "result"), "result.changed_files")
    _validate_score(_mapping(_required(root, "score", "result"), "result.score"), "score")


def validate_estimate(payload: JsonValue) -> None:
    root = _mapping(payload, "estimate")
    _non_empty_string(_required(root, "task", "estimate"), "estimate.task")
    _enum(_string_required_named(root, "requested_policy", "estimate"), POLICIES, "estimate.requested_policy")
    _enum(_string_required_named(root, "requested_mode", "estimate"), MODES, "estimate.requested_mode")
    _enum(_string_required_named(root, "requested_intensity", "estimate"), INTENSITIES, "estimate.requested_intensity")
    _enum(_string_required_named(root, "recommended_mode", "estimate"), MODES, "estimate.recommended_mode")
    _enum(_string_required_named(root, "recommended_intensity", "estimate"), INTENSITIES, "estimate.recommended_intensity")
    _positive_int(_required(root, "recommended_workers", "estimate"), "estimate.recommended_workers")
    _positive_int(_required(root, "estimated_serial_minutes", "estimate"), "estimate.estimated_serial_minutes")
    _minimum_number(_required(root, "expected_speedup", "estimate"), "estimate.expected_speedup", 1.0)
    _bool(_required(root, "requires_approval", "estimate"), "estimate.requires_approval")
    _bool(_required(root, "writer_swarm_allowed", "estimate"), "estimate.writer_swarm_allowed")
    _string_list(_required(root, "risk_flags", "estimate"), "estimate.risk_flags")
    _string_list(_required(root, "rationale", "estimate"), "estimate.rationale")


def validate_final_judgement(payload: JsonValue) -> None:
    root = _mapping(payload, "final_judgement")
    _non_empty_string(_required(root, "run_id", "final_judgement"), "final_judgement.run_id")
    _enum(_string_required_named(root, "status", "final_judgement"), FINAL_STATUSES, "final_judgement.status")
    _string(_required(root, "summary", "final_judgement"), "final_judgement.summary")
    patches = _list(_required(root, "selected_patches", "final_judgement"), "final_judgement.selected_patches")
    for index, patch_payload in enumerate(patches):
        patch = _mapping(patch_payload, f"final_judgement.selected_patches[{index}]")
        _non_empty_string(_required(patch, "task_id", f"selected_patches[{index}]"), f"selected_patches[{index}].task_id")
        _non_empty_string(_required(patch, "replica_id", f"selected_patches[{index}]"), f"selected_patches[{index}].replica_id")
        _non_empty_string(_required(patch, "patch_path", f"selected_patches[{index}]"), f"selected_patches[{index}].patch_path")
    _validate_score(_mapping(_required(root, "score", "final_judgement"), "final_judgement.score"), "score")


def _required(payload: Mapping[str, JsonValue], key: str, parent: str) -> JsonValue:
    try:
        return payload[key]
    except KeyError as exc:
        raise SchemaError(f"{parent}.{key} is required") from exc


def _mapping(value: JsonValue, field: str) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise SchemaError(f"{field} must be an object")
    return value


def _list(value: JsonValue, field: str) -> list[JsonValue]:
    if not isinstance(value, list):
        raise SchemaError(f"{field} must be a list")
    return value


def _string(value: JsonValue, field: str) -> str:
    if not isinstance(value, str):
        raise SchemaError(f"{field} must be a string")
    return value


def _non_empty_string(value: JsonValue, field: str) -> str:
    text = _string(value, field)
    if not text:
        raise SchemaError(f"{field} must not be empty")
    return text


def _string_list(value: JsonValue, field: str) -> tuple[str, ...]:
    return tuple(_string(item, f"{field}[]") for item in _list(value, field))


def _bool(value: JsonValue, field: str) -> bool:
    if not isinstance(value, bool):
        raise SchemaError(f"{field} must be a boolean")
    return value


def _positive_int(value: JsonValue, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SchemaError(f"{field} must be an integer")
    if value < 1:
        raise SchemaError(f"{field} must be greater than zero")
    return value


def _number(value: JsonValue, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise SchemaError(f"{field} must be a number")
    return float(value)


def _minimum_number(value: JsonValue, field: str, minimum: float) -> float:
    number = _number(value, field)
    if number < minimum:
        raise SchemaError(f"{field} must be at least {minimum}")
    return number


def _score(value: JsonValue, field: str) -> float:
    number = _number(value, field)
    if number < 0 or number > 100:
        raise SchemaError(f"{field} must be between 0 and 100")
    return number


def _validate_score(payload: Mapping[str, JsonValue], field: str) -> None:
    for score_field in SCORE_FIELDS:
        _score(_required(payload, score_field, field), f"{field}.{score_field}")


def _enum(value: str, allowed: Sequence[str], field: str) -> str:
    if value not in allowed:
        raise SchemaError(f"{field} must be one of: {', '.join(allowed)}")
    return value


def _string_required(task: Mapping[str, JsonValue], key: str, index: int) -> str:
    return _string(_required(task, key, f"tasks[{index}]"), f"tasks[{index}].{key}")


def _string_required_named(payload: Mapping[str, JsonValue], key: str, parent: str) -> str:
    return _string(_required(payload, key, parent), f"{parent}.{key}")
