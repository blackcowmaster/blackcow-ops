from __future__ import annotations

import json
import re
import shlex
from pathlib import Path
from typing import Final

from .config import JsonValue
from .design_gate import GateResult


GENERATED_ARTIFACTS = ("node_modules", ".expo")
NO_INSTALL_SCRIPT_NAMES = ("typecheck", "lint")
NODE_MODULE_REQUIRED_TOOLS = ("eslint", "expo", "react-native")
DEPRECATED_MODULE_RESOLUTION = ("node", "node10")
IMPORT_SPECIFIER_PATTERN: Final = re.compile(
    r"(?:import\s+(?:type\s+)?[\s\S]*?\s+from\s*|export\s+[\s\S]*?\s+from\s*|import\s*)['\"]([^'\"]+)['\"]"
)
DECLARE_MODULE_PATTERN: Final = re.compile(r"declare\s+module\s+['\"]([^'\"]+)['\"]")
SOURCE_SUFFIXES = (".ts", ".tsx")


def run_expo_clean_gate(project_root: Path, project: str) -> GateResult:
    project_path = project_root / project
    package_json = project_path / "package.json"
    tsconfig_json = project_path / "tsconfig.json"
    if not package_json.exists():
        return GateResult(ok=False, message=f"missing package.json: {package_json}")
    if not tsconfig_json.exists():
        return GateResult(ok=False, message=f"missing tsconfig.json: {tsconfig_json}")

    package_payload = _read_json(package_json, "package.json")
    if not isinstance(package_payload, dict):
        return GateResult(ok=False, message="package.json must contain a JSON object")
    tsconfig_payload = _read_json(tsconfig_json, "tsconfig.json")
    if not isinstance(tsconfig_payload, dict):
        return GateResult(ok=False, message="tsconfig.json must contain a JSON object")

    issue = _generated_artifact_issue(project_path)
    if issue:
        return GateResult(ok=False, message=issue)
    issue = _tsconfig_issue(project_path, tsconfig_payload)
    if issue:
        return GateResult(ok=False, message=issue)
    issue = _script_issue(package_payload, project_path)
    if issue:
        return GateResult(ok=False, message=issue)
    issue = _source_import_issue(project_path, tsconfig_payload)
    if issue:
        return GateResult(ok=False, message=issue)
    return GateResult(ok=True, message=f"Expo/RN clean scaffold gate passed: {project}")


def _read_json(path: Path, label: str) -> JsonValue:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"__blackcow_error__": f"invalid {label}: {exc}"}


def _generated_artifact_issue(project_path: Path) -> str:
    for name in GENERATED_ARTIFACTS:
        if (project_path / name).exists():
            return f"generated artifact must not be committed for scratch workers: {name}"
    return ""


def _tsconfig_issue(project_path: Path, payload: dict[str, JsonValue]) -> str:
    error = payload.get("__blackcow_error__")
    if isinstance(error, str):
        return error
    extends = payload.get("extends")
    if isinstance(extends, str) and _requires_node_modules(extends) and not (project_path / "node_modules").exists():
        return (
            f"tsconfig extends {extends!r}, but scratch acceptance runs before npm install; "
            "use a self-contained tsconfig or a relative local base config"
        )
    compiler_options = payload.get("compilerOptions")
    if not isinstance(compiler_options, dict):
        return ""
    if "baseUrl" in compiler_options and "ignoreDeprecations" not in compiler_options:
        return "tsconfig compilerOptions.baseUrl triggers TypeScript 6 deprecation errors; remove it or set ignoreDeprecations"
    module_resolution = compiler_options.get("moduleResolution")
    if isinstance(module_resolution, str) and module_resolution.lower() in DEPRECATED_MODULE_RESOLUTION:
        return f"tsconfig moduleResolution={module_resolution!r} is deprecated; use bundler or omit it"
    return ""


def _requires_node_modules(extends: str) -> bool:
    if extends.startswith((".", "/", "~")):
        return False
    return True


def _script_issue(package_payload: dict[str, JsonValue], project_path: Path) -> str:
    scripts = package_payload.get("scripts")
    if not isinstance(scripts, dict):
        return "package.json must define scripts for typecheck and lint"
    for script_name in NO_INSTALL_SCRIPT_NAMES:
        value = scripts.get(script_name)
        if not isinstance(value, str) or not value.strip():
            return f"package.json missing usable {script_name} script"
        binary = _first_binary(value)
        if binary in NODE_MODULE_REQUIRED_TOOLS and not (project_path / "node_modules").exists():
            return (
                f"package script {script_name!r} uses {binary!r}, but scratch acceptance runs before npm install; "
                "use a no-install local check script or TypeScript command that can run in the controller"
            )
    return ""


def _source_import_issue(project_path: Path, tsconfig_payload: dict[str, JsonValue]) -> str:
    if (project_path / "node_modules").exists():
        return ""
    source_files = _source_files(project_path)
    if not source_files:
        return ""
    aliases = _path_alias_prefixes(tsconfig_payload)
    imports = _external_imports(source_files, aliases)
    declarations = _module_declarations(project_path)
    missing = sorted(specifier for specifier in imports if not _declaration_covers(specifier, declarations))
    if _needs_react_jsx_runtime(source_files, tsconfig_payload) and not _declaration_covers("react/jsx-runtime", declarations):
        missing.append("react/jsx-runtime")
    if not missing:
        return ""
    return (
        f"typecheck imports external modules before npm install: {_format_specifiers(tuple(missing))}; "
        "add local .d.ts declarations for those modules or make the typecheck script no-install-safe"
    )


def _source_files(project_path: Path) -> tuple[Path, ...]:
    files: list[Path] = []
    for path in project_path.rglob("*"):
        if not path.is_file():
            continue
        if any(part in GENERATED_ARTIFACTS for part in path.relative_to(project_path).parts):
            continue
        if path.name.endswith(".d.ts"):
            continue
        if path.suffix in SOURCE_SUFFIXES:
            files.append(path)
    return tuple(files)


def _external_imports(source_files: tuple[Path, ...], aliases: tuple[str, ...]) -> set[str]:
    specifiers: set[str] = set()
    for source_file in source_files:
        text = source_file.read_text(encoding="utf-8", errors="replace")
        for match in IMPORT_SPECIFIER_PATTERN.finditer(text):
            specifier = match.group(1)
            if _is_external_specifier(specifier, aliases):
                specifiers.add(specifier)
    return specifiers


def _is_external_specifier(specifier: str, aliases: tuple[str, ...]) -> bool:
    if specifier.startswith((".", "/", "#")):
        return False
    return not any(specifier.startswith(alias) for alias in aliases)


def _path_alias_prefixes(payload: dict[str, JsonValue]) -> tuple[str, ...]:
    compiler_options = payload.get("compilerOptions")
    if not isinstance(compiler_options, dict):
        return ()
    paths = compiler_options.get("paths")
    if not isinstance(paths, dict):
        return ()
    prefixes: list[str] = []
    for raw_key in paths:
        if not isinstance(raw_key, str):
            continue
        prefix = raw_key.split("*", maxsplit=1)[0]
        if prefix:
            prefixes.append(prefix)
    return tuple(prefixes)


def _module_declarations(project_path: Path) -> set[str]:
    declarations: set[str] = set()
    for path in project_path.rglob("*.d.ts"):
        if any(part in GENERATED_ARTIFACTS for part in path.relative_to(project_path).parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        declarations.update(match.group(1) for match in DECLARE_MODULE_PATTERN.finditer(text))
    return declarations


def _declaration_covers(specifier: str, declarations: set[str]) -> bool:
    if specifier in declarations:
        return True
    for declaration in declarations:
        if "*" not in declaration:
            continue
        prefix, _, suffix = declaration.partition("*")
        if specifier.startswith(prefix) and specifier.endswith(suffix):
            return True
    return False


def _needs_react_jsx_runtime(source_files: tuple[Path, ...], payload: dict[str, JsonValue]) -> bool:
    if not any(path.suffix == ".tsx" for path in source_files):
        return False
    compiler_options = payload.get("compilerOptions")
    if not isinstance(compiler_options, dict):
        return False
    jsx = compiler_options.get("jsx")
    return isinstance(jsx, str) and jsx.lower() in ("react-jsx", "react-jsxdev")


def _format_specifiers(specifiers: tuple[str, ...]) -> str:
    visible = specifiers[:8]
    suffix = f", +{len(specifiers) - len(visible)} more" if len(specifiers) > len(visible) else ""
    return ", ".join(visible) + suffix


def _first_binary(script: str) -> str:
    try:
        parts = shlex.split(script)
    except ValueError:
        return ""
    for part in parts:
        if "=" in part and not part.startswith(("./", "/", "node")):
            continue
        return Path(part).name
    return ""
