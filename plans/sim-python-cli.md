# Plan: sim-python-cli — Batch File Processor

| Field | Value |
|---|---|
| **Slug** | `sim-python-cli` |
| **Created** | 2025-07-17 |
| **Class** | `M` |
| **Intent** | Feature (HIGH confidence) |
| **Explore lanes** | 5 research lanes dispatched, all returned |
| **Adversarial reviews** | 3 reviewers (M-scale) |
| **Budget** | ~55K tokens research / 128K target |

---

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | 사용자가 대규모 디렉토리의 파일들을 CLI에서 안전하게 병렬 배치 처리할 수 있는 도구 필요 |
| **WHO** | DevOps 엔지니어, 데이터 엔지니어 — 수천~수십만 개 파일을 스크립트로 일괄 처리하는 사용자 |
| **WHAT** | Python 패키지 (`sim-python-cli`): argparse CLI + multiprocessing 병렬 처리 + Rich 진행 표시줄 + glob 파일 선택 + 오류 복구 |
| **RISK** | 단일 파일 실패가 전체 배치를 중단시키지 않아야 함. 대용량 디렉토리에서 메모리 고갈 없이 동작해야 함 |
| **SUCCESS** | matchRate ≥ 90%, test pass=100%, lint=0warn, coverage ≥ 80%, 100K 파일 디렉토리에서 메모리 ≤ 512 MiB 유지 |
| **SCOPE** | 포함: CLI 인터페이스, 파일 검색(glob), 병렬 처리 엔진, 진행 표시줄, 오류 복구, JSONL 오류 로그. 제외: 파일 처리 로직 자체(플러그인 형태), GUI, 네트워크 전송, 파일 시스템 이벤트 감시 |

---

## Summary

A Python CLI tool (`sim-python-cli`) that scans directories using lazy glob patterns, dispatches files to a configurable pool of worker processes, displays Rich-powered multi-level progress (overall + per-worker), isolates per-file failures with tenacity-based retry, and emits structured JSONL error logs. The tool itself is a *framework* — the actual per-file processing logic is injected via a user-provided callable (plugin pattern). This keeps the tool reusable across diverse batch-processing use cases (image resizing, log parsing, checksum verification, etc.).

---

## Architecture Options

### Option A — Minimal (단일 스크립트)
- **접근법**: 단일 `.py` 파일, `argparse` + `multiprocessing.Pool` + `tqdm.process_map`, 기본 `try/except` 오류 처리
- **장점**: 구현 속도 최고, 의존성 최소 (tqdm만 추가)
- **단점**: 확장 불가능, 오류 복구 미흡, 재사용성 낮음, Rich UI 불가
- **적합**: 일회성 스크립트
- **예상 파일 수**: 1개

### Option B — Clean (플러그인 아키텍처)
- **접근법**: 풀 패키지 구조, 추상 `Processor` 베이스 클래스, `ProcessPoolExecutor` + `max_tasks_per_child`, Rich `Live` + `Progress` 조합, tenacity 재시도, JSONL 오류 로그, `pyproject.toml` + `click`/`typer` CLI
- **장점**: 최대 확장성, 프로덕션 품질, 완벽한 오류 처리
- **단점**: 구현 범위 넓음, 의존성 증가, 초기 개발 시간 ↑
- **적합**: 장기 유지보수되는 팀 도구
- **예상 파일 수**: 12~15개

### Option C — Pragmatic (권장)
- **접근법**: 깔끔한 패키지 구조 유지, `argparse` (요구사항), `multiprocessing.Pool.imap_unordered`, Rich 진행 표시줄, tenacity 재시도, JSONL 오류 로그, 플러그인 콜백 패턴 (간단한 `Callable` 기반)
- **장점**: Option B의 핵심 품질 유지 + Option A의 단순함, 요구사항 완전 충족
- **단점**: 추후 subcommand 추가 시 리팩토링 필요
- **적합**: 요구사항에 정확히 부합하는 첫 버전
- **예상 파일 수**: 8개

---

## Codebase Survey (Research Summary)

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| Surface (argparse) | Factory function `build_parser()` + argument groups + `set_defaults(func=)` dispatch | HTTPie `ParserSpec` pattern, Python docs | — |
| Call Graph (multiprocessing) | `Pool.imap_unordered()` for streaming, `initializer` for worker setup, signal handling critical (SIGINT → `pool.terminate()`) | Python docs, pythonspeed.com | P1 |
| Data Shapes (greenfield) | Plugin pattern: `Callable[[Path], ProcessResult]` + dataclass results | N/A — greenfield design | S1 |
| Tests (greenfield) | pytest with `tmp_path` fixtures, mock filesystem for glob tests, `ProcessPoolExecutor` integration tests | Standard pytest patterns | M2, M3 |
| Config (greenfield) | argparse flags only (no config file for v1): `--workers`, `--glob`, `--retries`, `--output-dir` | N/A | — |
| Deps | `rich` (latest), `tenacity` (latest), stdlib only otherwise | pepy.tech | — |
| Git (greenfield) | N/A — new repository | — | — |
| Security | Input: glob pattern → no injection risk. Output: file writes to `--output-dir`. No eval/exec | Design review | S3 |
| Performance | `imap_unordered` + `chunksize` tuning, `os.scandir`-backed `glob.iglob` for lazy iteration | Python docs | P1, P3 |
| Patterns | Plugin callback pattern: user provides `ProcessingFn = Callable[[Path], Result]` | Standard Python plugin pattern | — |

---

## Gap Matrix

| Cat | Item | Evidence | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| ✅ Reuse | stdlib `argparse`, `multiprocessing`, `pathlib`, `glob` | — | HIGH | — | — |
| ✅ Reuse | `rich.progress.Progress` + `rich.live.Live` for composed progress | Rich docs | HIGH | — | — |
| ✅ Reuse | `tenacity.retry` decorator for per-file retry | tenacity docs | HIGH | — | — |
| 🆕 Build | `src/sim_python_cli/cli.py` — argparse interface | — | — | — | M1 |
| 🆕 Build | `src/sim_python_cli/engine.py` — multiprocessing dispatch | — | — | — | P1, P3 |
| 🆕 Build | `src/sim_python_cli/progress.py` — Rich progress integration | — | — | — | — |
| 🆕 Build | `src/sim_python_cli/discovery.py` — lazy glob file discovery | — | — | — | — |
| 🆕 Build | `src/sim_python_cli/recover.py` — error isolation + retry | — | — | — | M3 |
| 🆕 Build | `src/sim_python_cli/models.py` — dataclasses | — | — | — | S1 |
| 🆕 Build | `src/sim_python_cli/__main__.py` — entry point | — | — | — | — |
| 🆕 Build | `pyproject.toml` — package config + deps | — | — | — | M4 |
| 🆕 Build | `tests/` — test suite (pytest) | — | — | — | M2 |

---

## Waves

### Wave 1 — Foundation (4 tasks, parallel, ≤80K tokens)
Sets up the package skeleton, data models, and file discovery — zero dependencies between tasks.

- [ ] **w1-s1**: Create package skeleton — `pyproject.toml`, `src/sim_python_cli/__init__.py`, `__main__.py`
  - **Worker:** `mini`
  - **Token est:** ~3K
  - **Files:** `pyproject.toml`, `src/sim_python_cli/__init__.py`, `src/sim_python_cli/__main__.py`
  - **Verify:** `python -c "import sim_python_cli"` succeeds
  - **Gate:** M4 (lint clean)

- [ ] **w1-s2**: Implement data models — `ProcessResult`, `BatchResult`, `FileTask` dataclasses
  - **Worker:** `mini`
  - **Token est:** ~3K
  - **Files:** `src/sim_python_cli/models.py`
  - **Verify:** `python -c "from sim_python_cli.models import ProcessResult, BatchResult, FileTask; print('OK')"`
  - **Gate:** S1 (data shape integrity)

- [ ] **w1-s3**: Implement lazy file discovery — `discover_files(glob_pattern, root_dir)` using `glob.iglob` + `os.scandir` fallback
  - **Worker:** `medium`
  - **Token est:** ~5K
  - **Files:** `src/sim_python_cli/discovery.py`
  - **Verify:** `python -c "from sim_python_cli.discovery import discover_files; files = list(discover_files('*.txt', '.')); assert isinstance(files, list)"`
  - **Gate:** P3 (memory — must be O(1) in file count)

- [ ] **w1-s4**: Implement Rich progress module — `ProgressManager` wrapping `rich.progress.Progress` + multiprocessing.Queue for worker updates
  - **Worker:** `medium`
  - **Token est:** ~6K
  - **Files:** `src/sim_python_cli/progress.py`
  - **Verify:** Unit test that ProgressManager renders without crash, handles worker completion signals
  - **Gate:** — (UI component)

### Wave 2 — Core (2 tasks, parallel after Wave 1, ≤40K tokens)
Depends on Wave 1 models + progress. These two are independent of each other.

- [ ] **w2-s1**: Implement error recovery — `ErrorHandler` with tenacity retry, JSONL error logging, resumable skip-list
  - **Worker:** `heavy`
  - **Token est:** ~8K
  - **Files:** `src/sim_python_cli/recover.py`
  - **Verify:** Unit test: inject `IOError` → retries 3x → logs to JSONL → raises after exhaustion
  - **Gate:** M3 (regression — must not lose already-processed files)

- [ ] **w2-s2**: Implement CLI interface — `build_parser()` with argument groups: `File selection`, `Processing`, `Output`
  - **Worker:** `medium`
  - **Token est:** ~5K
  - **Files:** `src/sim_python_cli/cli.py`
  - **Verify:** `python -m sim_python_cli --help` renders all groups; `--workers 4 --glob "*.txt"` parses correctly
  - **Gate:** M1 (spec-match — all 6 requirements covered by flags)

### Wave 3 — Integration (1 task, serial on Wave 2, ≤25K tokens)

- [ ] **w3-s1**: Implement processing engine — `BatchEngine.run()` wires discovery → pool dispatch → progress → error recovery
  - **Worker:** `heavy`
  - **Token est:** ~10K
  - **Files:** `src/sim_python_cli/engine.py`
  - **Verify:** Integration test: create 50 temp files, run with `--workers 2`, verify all processed, progress shown, errors in JSONL
  - **Gate:** M2 (test pass=100%), P1 (no N+1, correct chunksize)

### Wave 4 — Hardening (3 tasks, parallel, ≤30K tokens)

- [ ] **w4-s1**: Write test suite — pytest with `tmp_path`, mock `ProcessingFn`, parametrize glob patterns, error injection
  - **Worker:** `heavy`
  - **Token est:** ~8K
  - **Files:** `tests/test_cli.py`, `tests/test_engine.py`, `tests/test_discovery.py`, `tests/test_recover.py`
  - **Verify:** `pytest --cov=sim_python_cli --cov-report=term` → coverage ≥ 80%
  - **Gate:** M2 (test pass=100%), M3 (regression)

- [ ] **w4-s2**: Signal handling + graceful shutdown — SIGINT → `pool.terminate()`, SIGTERM → drain current chunk then exit
  - **Worker:** `medium`
  - **Token est:** ~4K
  - **Files:** `src/sim_python_cli/engine.py` (amendment)
  - **Verify:** Start processing 1000 files, send SIGINT, verify pool terminated within 2s, no zombie processes
  - **Gate:** P3 (latency — shutdown within 2s)

- [ ] **w4-s3**: CLI polish — `--dry-run`, `--verbose`, `--resume`, `--chunksize`, colored help, `--version`
  - **Worker:** `medium`
  - **Token est:** ~4K
  - **Files:** `src/sim_python_cli/cli.py` (amendment)
  - **Verify:** `--dry-run` lists files without processing; `--resume` skips completed files from JSONL
  - **Gate:** M1 (spec-match)

---

## Risk Register (BKIT 11-Gate)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| CLI flags don't cover all 6 requirements | `M1_spec_match` | HIGH | matchRate ≥ 90% | 6 requirements → 6 flag groups mapped explicitly | Compare plan vs argparse help output |
| Worker crashes lose processed-file state | `M3_regression` | HIGH | 0 lost files | JSONL progress file written per-completion, not per-batch | Kill worker mid-batch → resume → verify no re-processing |
| Large directory loads all paths into memory | `P3_latency` | HIGH | memory ≤ 512 MiB at 100K files | `glob.iglob()` generator, never `list()` | `memory_profiler` on 100K-file directory |
| SIGINT leaves zombie workers | `P3_latency` | MED | shutdown ≤ 2s | SIGINT handler → `pool.terminate()` → `pool.join()` | `timeout 2 python -m sim_python_cli --glob '**/*'` then Ctrl-C |
| Per-file error crashes entire batch | `M3_regression` | MED | 0 batch aborts | Inner try/except in worker, never re-raise at pool level | Inject `ValueError` in 1 of 100 files → 99 succeed |
| JSONL error log grows unbounded | `P2_memory` | LOW | log ≤ 10 MiB/day | Rotate or cap at configurable limit (v2 concern) | Documented limitation |
| Injection via glob pattern | `S3_injection` | LOW | no shell expansion | `glob.iglob()` uses `os.scandir` internally, no shell | Code audit: confirm no `os.system()` or `subprocess(shell=True)` |

---

## Package Structure

```
sim-python-cli/
├── pyproject.toml
├── README.md
├── src/
│   └── sim_python_cli/
│       ├── __init__.py           # Package marker, exports public API
│       ├── __main__.py           # python -m sim_python_cli entry
│       ├── cli.py                # argparse builder + main() dispatch
│       ├── engine.py             # BatchEngine: orchestrates discovery → pool → progress → recovery
│       ├── worker.py             # Per-file worker function (picklable, top-level)
│       ├── progress.py           # Rich Progress + Live + Queue integration
│       ├── discovery.py          # Lazy glob file discovery
│       ├── recover.py            # ErrorHandler: tenacity retry + JSONL logging
│       └── models.py             # ProcessResult, BatchResult, FileTask dataclasses
└── tests/
    ├── conftest.py               # Shared fixtures (tmp_path, mock_processor)
    ├── test_cli.py
    ├── test_engine.py
    ├── test_discovery.py
    ├── test_recover.py
    └── test_integration.py       # End-to-end with temp directories
```

### Dependency Strategy

| Dependency | Version | Purpose | Justification |
|---|---|---|---|
| `rich` | ≥13.0 | Progress bars + styled terminal output | 588M downloads/month, active maintenance |
| `tenacity` | ≥9.0 | Retry decorator with exponential backoff | Apache 2.0, fork of unmaintained `retrying` |
| `pytest` (dev) | ≥8.0 | Test framework | Standard |
| `pytest-cov` (dev) | ≥6.0 | Coverage | Standard |
| **Everything else** | stdlib | `argparse`, `multiprocessing`, `pathlib`, `glob`, `json`, `signal`, `dataclasses`, `logging`, `typing` | Zero additional runtime deps |

### CLI Interface Design

```
usage: sim-python-cli [-h] --glob GLOB [--root-dir DIR] [--workers N]
                      [--chunksize N] [--retries N] [--output-dir DIR]
                      [--dry-run] [--resume] [--verbose] [--version]
                      PROCESSOR [PROCESSOR_ARGS ...]

Batch file processor with parallel execution.

File selection:
  --glob GLOB          File glob pattern (e.g., "**/*.txt", "*.csv")
  --root-dir DIR       Root directory for glob search (default: .)

Processing:
  --workers N          Number of worker processes (default: cpu_count)
  --chunksize N        Files per worker chunk (default: auto-tuned)
  --retries N          Retry attempts per failed file (default: 3)
  PROCESSOR            Python module:function or path to script
  PROCESSOR_ARGS       Additional arguments passed to processor

Output:
  --output-dir DIR     Directory for output files (default: .)
  --dry-run            List matching files without processing
  --resume             Skip already-processed files (uses errors.jsonl)
  --verbose, -v        Increase log verbosity
  --version            Show version and exit
```

### Plugin Interface (User-Facing)

```python
# The user provides a callable matching this signature:
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProcessResult:
    path: Path
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    duration_ms: float = 0.0

# Option 1: Python import path
#   sim-python-cli --glob "*.png" my_module.resize_image --width 800
#   → imports my_module.resize_image, calls resize_image(path, width=800)

# Option 2: Inline lambda via file
#   sim-python-cli --glob "*.log" ./processors/parse_log.py
#   → exec's the file, looks for `process(path: Path) -> ProcessResult`
```

---

## Execution

Run this plan with:

```
blackcow-loop "Execute plans/sim-python-cli.md" --completion-promise='All 6 requirements met: argparse CLI, multiprocessing, Rich progress, large-dir efficient, glob patterns, error recovery with retry. Test coverage ≥ 80%, memory ≤ 512 MiB at 100K files.' --trust-level=2
```

### Parallelism Guide

- **Wave 1**: 4 parallel workers → saves ~60% time vs serial
- **Wave 2**: 2 parallel workers → saves ~40%
- **Wave 3**: 1 worker (serial on Wave 2)
- **Wave 4**: 3 parallel workers → saves ~50%
- **Total budget**: ~55K tokens research + ~40K implementation → ~95K / 128K target
