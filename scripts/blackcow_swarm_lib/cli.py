from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .config import ConfigError, JsonValue, load_config, merge_cli_overrides
from .estimate import estimate_task
from .lifecycle import cancel_run, cleanup_run, execute_mock_run, execute_reasonix_run, status_run
from .lifecycle_scratch import execute_reasonix_scratch_run
from .run_diagnostics import diagnose_run
from .run_loop import RunExecutor, execute_run_loop
from .runner import RunnerError
from .schema import SchemaError
from .state import StateError, execute_dry_run
from .task_graph import create_dry_run_plan


MODES = ("serial", "qa", "discovery", "review", "coder", "full", "adaptive")
INTENSITIES = ("normal", "high", "max")
POLICIES = ("off", "suggest", "auto", "force")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="blackcow_swarm.py",
        description="BlackCow Swarm local Reasonix control plane.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    _add_estimate_parser(subparsers)
    _add_plan_parser(subparsers)
    _add_run_parser(subparsers)
    _add_run_loop_parser(subparsers)
    _add_run_id_parser(subparsers, "resume")
    _add_run_id_parser(subparsers, "cancel")
    _add_run_id_parser(subparsers, "status")
    _add_run_id_parser(subparsers, "cleanup")
    return parser


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mode", choices=MODES, default="adaptive")
    parser.add_argument("--intensity", choices=INTENSITIES, default="high")
    parser.add_argument("--policy", choices=POLICIES, default="auto")
    parser.add_argument("--max-workers", type=int)
    parser.add_argument("--run-id")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", action="store_true")


def _add_estimate_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("estimate", help="Estimate swarm viability for a task.")
    parser.add_argument("task")
    _add_common_options(parser)
    parser.set_defaults(handler=_handle_estimate)


def _add_plan_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("plan", help="Create a swarm task graph.")
    parser.add_argument("task")
    _add_common_options(parser)
    parser.set_defaults(handler=_handle_plan)


def _add_run_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("run", help="Run a swarm task graph.")
    parser.add_argument("--task-graph", required=True)
    parser.add_argument("--runner", choices=("reasonix", "reasonix-scratch", "mock"), default="reasonix")
    parser.add_argument("--mode", choices=MODES, default="adaptive")
    parser.add_argument("--intensity", choices=INTENSITIES, default="high")
    parser.add_argument("--policy", choices=POLICIES, default="auto")
    parser.add_argument("--max-workers", type=int)
    parser.add_argument("--run-id")
    parser.add_argument("--dry-run", action="store_true")
    parser.set_defaults(handler=_handle_run)


def _add_run_loop_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("run-loop", help="Run a task graph with bounded automatic retries.")
    parser.add_argument("--task-graph", required=True)
    parser.add_argument("--runner", choices=("reasonix", "reasonix-scratch", "mock"), default="reasonix")
    parser.add_argument("--run-id")
    parser.add_argument("--attempts", type=int, default=3)
    parser.set_defaults(handler=_handle_run_loop)


def _add_run_id_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    command: str,
) -> None:
    parser = subparsers.add_parser(command, help=f"{command.title()} a swarm run.")
    parser.add_argument("--run-id", required=True)
    handlers = {
        "resume": _handle_resume,
        "cancel": _handle_cancel,
        "status": _handle_status,
        "cleanup": _handle_cleanup,
    }
    parser.set_defaults(handler=handlers[command])


def _placeholder(args: argparse.Namespace) -> int:
    print(f"{args.command}: not implemented")
    return 0


def _handle_estimate(args: argparse.Namespace) -> int:
    try:
        config = load_config()
        options = merge_cli_overrides(
            config,
            mode=args.mode,
            intensity=args.intensity,
            policy=args.policy,
            max_workers=args.max_workers,
        )
        estimate = estimate_task(
            args.task,
            config,
            requested_intensity=options.intensity,
            requested_policy=options.policy,
            requested_mode=options.mode,
            max_workers=options.max_workers,
        )
    except (ConfigError, ValueError) as exc:
        print(f"estimate error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(estimate.to_json(), indent=2, sort_keys=True))
    return 0


def _handle_plan(args: argparse.Namespace) -> int:
    if not args.dry_run:
        print("plan error: plan currently requires --dry-run", file=sys.stderr)
        return 2
    try:
        config = load_config()
        options = merge_cli_overrides(
            config,
            mode=args.mode,
            intensity=args.intensity,
            policy=args.policy,
            max_workers=args.max_workers,
        )
        artifacts = create_dry_run_plan(
            args.task,
            config,
            options,
            run_id=args.run_id,
            project_root=_project_root(),
            approve_dangerous=args.yes,
        )
    except (ConfigError, ValueError) as exc:
        print(f"plan error: {exc}", file=sys.stderr)
        return 2
    payload = {
        "dry_run": True,
        "run_id": artifacts.run_id,
        "run_dir": str(artifacts.run_dir),
        "estimate": str(artifacts.estimate_path),
        "task_graph": str(artifacts.task_graph_path),
        "shared_context": str(artifacts.shared_context_path),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _handle_run(args: argparse.Namespace) -> int:
    try:
        if args.dry_run:
            output = execute_dry_run(Path(args.task_graph), args.run_id, _project_root())
        elif args.runner == "mock":
            output = execute_mock_run(Path(args.task_graph), args.run_id, _project_root())
        elif args.runner == "reasonix-scratch":
            output = execute_reasonix_scratch_run(Path(args.task_graph), args.run_id, _project_root())
        else:
            output = execute_reasonix_run(Path(args.task_graph), args.run_id, _project_root())
        _add_diagnosis_if_failed(output)
    except (ConfigError, RunnerError, SchemaError, StateError, ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"run error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(output, indent=2, sort_keys=True))
    return _run_exit_code(output)


def _handle_run_loop(args: argparse.Namespace) -> int:
    try:
        output = execute_run_loop(
            Path(args.task_graph),
            base_run_id=args.run_id,
            project_root=_project_root(),
            attempts=args.attempts,
            executor=_executor_for(args.runner),
        )
    except (ConfigError, RunnerError, SchemaError, StateError, ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"run-loop error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(output, indent=2, sort_keys=True))
    return _run_exit_code(output)


def _handle_resume(args: argparse.Namespace) -> int:
    try:
        summary = status_run(_project_root(), args.run_id)
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"resume error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"resume": True, **summary}, indent=2, sort_keys=True))
    return 0


def _handle_cancel(args: argparse.Namespace) -> int:
    try:
        final_judgement = cancel_run(_project_root(), args.run_id)
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"cancel error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"cancelled": True, "final_judgement": str(final_judgement)}, indent=2, sort_keys=True))
    return 0


def _handle_status(args: argparse.Namespace) -> int:
    try:
        summary = status_run(_project_root(), args.run_id)
        summary["diagnosis"] = diagnose_run(_project_root(), args.run_id).to_json()
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"status error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _handle_cleanup(args: argparse.Namespace) -> int:
    try:
        summary = cleanup_run(_project_root(), args.run_id)
    except ValueError as exc:
        print(f"cleanup error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _executor_for(runner: str) -> RunExecutor:
    if runner == "mock":
        return execute_mock_run
    if runner == "reasonix-scratch":
        return execute_reasonix_scratch_run
    return execute_reasonix_run


def _add_diagnosis_if_failed(output: dict[str, JsonValue]) -> None:
    status = output.get("status")
    run_id = output.get("run_id")
    if status == "SUCCEEDED" or not isinstance(run_id, str):
        return
    try:
        output["diagnosis"] = diagnose_run(_project_root(), run_id).to_json()
    except (ValueError, FileNotFoundError, json.JSONDecodeError):
        return


def _run_exit_code(output: dict[str, JsonValue]) -> int:
    status = output.get("status")
    if status in ("FAILED", "BLOCKED", "CANCELLED"):
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = args.handler
    return handler(args)
