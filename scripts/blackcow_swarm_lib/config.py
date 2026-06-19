from __future__ import annotations

import json
import string
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import TypeAlias


JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "blackcow.swarm.json"
POLICIES = ("off", "suggest", "auto", "force")
MODES = ("serial", "qa", "discovery", "review", "coder", "full", "adaptive")
INTENSITIES = ("normal", "high", "max")
RUNNERS = ("reasonix", "reasonix-scratch", "mock")
ALLOWED_PLACEHOLDERS = frozenset(
    ("skill", "prompt_file", "result_json", "workspace", "run_id", "task_id", "replica_id", "read_only")
)
REQUIRED_PLACEHOLDERS = frozenset(("skill", "prompt_file", "result_json"))


class ConfigError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RunnerConfig:
    runner_type: str
    command_template: tuple[str, ...]
    cwd_mode: str
    require_json_result: bool


@dataclass(frozen=True, slots=True)
class IntensityProfile:
    max_total_workers: int
    max_readonly_workers: int
    max_writer_workers: int
    timeout_seconds: int
    retry_limit: int
    heartbeat_seconds: int
    cancel_grace_seconds: int


@dataclass(frozen=True, slots=True)
class SwarmConfig:
    default_policy: str
    default_mode: str
    default_intensity: str
    cost_multiplier_limit: float
    runner: RunnerConfig
    intensity: Mapping[str, IntensityProfile]
    single_writer_paths: tuple[str, ...]
    risky_writer_patterns: tuple[str, ...]
    anti_gaming: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RuntimeOptions:
    mode: str
    intensity: str
    policy: str
    max_workers: int | None


def load_config(path: Path | None = None) -> SwarmConfig:
    config_path = path if path is not None else DEFAULT_CONFIG_PATH
    try:
        payload: JsonValue = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"config file not found: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON in {config_path}: {exc.msg}") from exc

    root = _as_mapping(payload, "root")
    swarm = _as_mapping(_required(root, "swarm"), "swarm")
    intensity_payload = _as_mapping(_required(swarm, "intensity"), "swarm.intensity")
    intensity = {
        name: _parse_profile(_as_mapping(_required(intensity_payload, name), f"swarm.intensity.{name}"), name)
        for name in INTENSITIES
    }
    return SwarmConfig(
        default_policy=_enum_string(swarm, "default_policy", POLICIES),
        default_mode=_enum_string(swarm, "default_mode", MODES),
        default_intensity=_enum_string(swarm, "default_intensity", INTENSITIES),
        cost_multiplier_limit=_optional_float(swarm, "cost_multiplier_limit", 6.0),
        runner=_parse_runner(_as_mapping(_required(swarm, "runner"), "swarm.runner")),
        intensity=MappingProxyType(intensity),
        single_writer_paths=_optional_string_tuple(swarm, "single_writer_paths"),
        risky_writer_patterns=_optional_string_tuple(swarm, "risky_writer_patterns"),
        anti_gaming=_optional_string_tuple(swarm, "anti_gaming"),
    )


def merge_cli_overrides(
    config: SwarmConfig,
    *,
    mode: str | None,
    intensity: str | None,
    policy: str | None,
    max_workers: int | None,
) -> RuntimeOptions:
    merged_mode = mode if mode is not None else config.default_mode
    merged_intensity = intensity if intensity is not None else config.default_intensity
    merged_policy = policy if policy is not None else config.default_policy
    _ensure_enum(merged_mode, MODES, "mode")
    _ensure_enum(merged_intensity, INTENSITIES, "intensity")
    _ensure_enum(merged_policy, POLICIES, "policy")
    if max_workers is not None and max_workers < 1:
        raise ConfigError("max_workers must be greater than zero")
    return RuntimeOptions(
        mode=merged_mode,
        intensity=merged_intensity,
        policy=merged_policy,
        max_workers=max_workers,
    )


def validate_command_template(template: Sequence[str]) -> None:
    seen: set[str] = set()
    formatter = string.Formatter()
    for part in template:
        for _, field_name, _, _ in formatter.parse(part):
            if field_name is None:
                continue
            if field_name == "":
                raise ConfigError("runner command template contains an empty placeholder")
            if field_name not in ALLOWED_PLACEHOLDERS:
                raise ConfigError(f"runner command template uses unknown placeholder: {field_name}")
            seen.add(field_name)
    missing = sorted(REQUIRED_PLACEHOLDERS.difference(seen))
    if missing:
        raise ConfigError(f"runner command template missing required placeholder(s): {', '.join(missing)}")


def _parse_runner(payload: Mapping[str, JsonValue]) -> RunnerConfig:
    template_values = _as_list(_required(payload, "command_template"), "runner.command_template")
    command_template = tuple(_as_string(value, "runner.command_template[]") for value in template_values)
    validate_command_template(command_template)
    return RunnerConfig(
        runner_type=_enum_string(payload, "type", RUNNERS),
        command_template=command_template,
        cwd_mode=_as_string(_required(payload, "cwd_mode"), "runner.cwd_mode"),
        require_json_result=_optional_bool(payload, "require_json_result", True),
    )


def _parse_profile(payload: Mapping[str, JsonValue], name: str) -> IntensityProfile:
    max_total_workers = _positive_int(payload, "max_total_workers", f"intensity.{name}.max_total_workers")
    max_writer_workers = _positive_int(payload, "max_writer_workers", f"intensity.{name}.max_writer_workers")
    return IntensityProfile(
        max_total_workers=max_total_workers,
        max_readonly_workers=_optional_int(
            payload,
            "max_readonly_workers",
            max(max_total_workers - max_writer_workers, 1),
        ),
        max_writer_workers=max_writer_workers,
        timeout_seconds=_positive_int(payload, "timeout_seconds", f"intensity.{name}.timeout_seconds"),
        retry_limit=_optional_int(payload, "retry_limit", 1),
        heartbeat_seconds=_optional_int(payload, "heartbeat_seconds", 10),
        cancel_grace_seconds=_optional_int(payload, "cancel_grace_seconds", 10),
    )


def _required(payload: Mapping[str, JsonValue], key: str) -> JsonValue:
    try:
        return payload[key]
    except KeyError as exc:
        raise ConfigError(f"missing required config key: {key}") from exc


def _as_mapping(value: JsonValue, field: str) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise ConfigError(f"{field} must be an object")
    return value


def _as_list(value: JsonValue, field: str) -> list[JsonValue]:
    if not isinstance(value, list):
        raise ConfigError(f"{field} must be a list")
    return value


def _as_string(value: JsonValue, field: str) -> str:
    if not isinstance(value, str):
        raise ConfigError(f"{field} must be a string")
    return value


def _as_bool(value: JsonValue, field: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigError(f"{field} must be a boolean")
    return value


def _as_int(value: JsonValue, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{field} must be an integer")
    return value


def _enum_string(payload: Mapping[str, JsonValue], key: str, allowed: Sequence[str]) -> str:
    value = _as_string(_required(payload, key), key)
    _ensure_enum(value, allowed, key)
    return value


def _ensure_enum(value: str, allowed: Sequence[str], field: str) -> None:
    if value not in allowed:
        allowed_values = ", ".join(allowed)
        raise ConfigError(f"{field} must be one of: {allowed_values}")


def _positive_int(payload: Mapping[str, JsonValue], key: str, field: str) -> int:
    value = _as_int(_required(payload, key), field)
    if value < 1:
        raise ConfigError(f"{field} must be greater than zero")
    return value


def _optional_int(payload: Mapping[str, JsonValue], key: str, default: int) -> int:
    value = payload.get(key)
    if value is None: return default
    parsed = _as_int(value, key)
    if parsed < 1:
        raise ConfigError(f"{key} must be greater than zero")
    return parsed


def _optional_float(payload: Mapping[str, JsonValue], key: str, default: float) -> float:
    value = payload.get(key)
    if value is None: return default
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ConfigError(f"{key} must be a number")
    return float(value)


def _optional_bool(payload: Mapping[str, JsonValue], key: str, default: bool) -> bool:
    value = payload.get(key)
    if value is None: return default
    return _as_bool(value, key)


def _optional_string_tuple(payload: Mapping[str, JsonValue], key: str) -> tuple[str, ...]:
    value = payload.get(key)
    if value is None: return ()
    return tuple(_as_string(item, f"{key}[]") for item in _as_list(value, key))
