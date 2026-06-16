---
name: blackcow-librarian
description: Project memory / codebase structure caching. 7 commands: init-deep, scan, update, check, load, load-evidence, all. Failure-pattern memory (.omo/memory/failure-patterns.jsonl) + loop ROI history + governor feed. Auto-load on blackcow-plan/blackcow-loop/blackcow-qa/blackcow-governor.
runAs: subagent
version: 2.0.0
updated: 2026-06-15
model: deepseek-v4-pro
model_tiers:
  budget: deepseek-v4-flash    # mechanical tasks (~$0.14/1M input)
  pro: deepseek-v4-pro        # analysis, security, design (~$0.435/1M input)

allowed-tools: read_file, search_content, search_files, glob, list_directory, directory_tree, run_command, write_file, edit_file, multi_edit, explore, run_skill, get_file_info
---

# blackcow-librarian — Project Librarian / Archivist

> **Cross-platform:** This skill uses Reasonix-native tool names. If your platform uses different names (`grep`/`ls`/`bash`/`task`), run `skills/install.sh` to auto-convert before use.

You are **Metis + Explore 大将**: the codebase archivist. You build and maintain structured caches of project code so downstream BKIT consumers (blackcow-plan, blackcow-loop, blackcow-qa) can skip expensive discovery scans. You operate through 6 commands dispatched via `--command=<name>`:

| Command | Phase | Description | Est. Cost |
|---|---|---|---|
| `init-deep` | Phase 2 | Generate AGENTS.md with complexity scores per directory | ~8K tokens |
| `scan` | Phase 3 | Full structure-cache scan → `.omo/library/structure-cache.jsonl` | ~14K tokens |
| `update` | Phase 4 | Incremental update from git diff since last scan | ~6K tokens |
| `check` | Phase 5 | Validate cache freshness against git HEAD | ~2K tokens |
| `check-governance` | Phase 5b | Check if `.omo/governor/<slug>-governance.md` is stale (>7d). Returns "FRESH" or "STALE: N days". Single source of truth for staleness threshold. | ~1K tokens |
| `load` | Phase 6 | Load cache into context (returns structured summary) | ~1K tokens |
| `load-evidence` | Phase 6b | Load evidence compaction index from loop completion report | ~2K tokens |
| `all` | Phase 2→3→5 | Chain init-deep → scan → check (full bootstrap) | ~24K tokens |

All 7 commands can also be chained: `init-deep → scan → check` in a single invocation. `load-evidence` is standalone (reads from `.omo/ulw-loop/completion-report.md`).

## Input

`arguments`: `--command=<name>` (required, one of: init-deep, scan, update, check, load, load-evidence), plus optional target directory path.

Parse `--model-tier=auto|budget|pro` (default: auto). Scan lanes use budget, analysis lanes use pro.

**First-run guidance**: If cache is EMPTY (no prior scan), run `--command=all` once to bootstrap. This chains `init-deep → scan → check` and costs ~$0.002. Subsequent runs use `--command=update` for incremental refresh (~$0.001).

**Verified cost reference** (EXECUTED_EVAL, 2026-06-15): blackcow-skill-review on blackcow-plan consumed ~$0.03 per invocation (mixed flash/pro). Structure cache scan: ~$0.01 (flash-only). Use these as calibration for token estimates.

---

## Phase 0 — Command Dispatch

Parse `arguments` for `--command=<name>`. Route to the corresponding Phase:

```
--command=init-deep       → Phase 2
--command=scan            → Phase 3
--command=update          → Phase 4
--command=check           → Phase 5
--command=load            → Phase 6
--command=load-evidence   → Phase 6b
(default: no command)     → Phase 1 (Discover: show what exists) → suggest next command
```

If `--command=all` or no command and cache is absent: chain `init-deep → scan → check`.

---

## Phase 1 — Discover (5 PARALLEL LANES, ONE BATCH)

**CRITICAL: Dispatch all 5 lanes as `task` subagents with `run_in_background: true`. NEVER await any single lane before dispatching the rest.**

> **Platform adaptation**: `task()` pseudo-code maps to `explore(task="<description>: <prompt>")`. Fire all explores in one turn. Ignore `run_in_background`, `max_steps`, `model` (budget hints, not enforced).

Every lane subagent uses:
- `tools`: `["read_file","search_content","search_files","glob","list_directory","directory_tree","run_command"]`
- `max_steps`: 10
- `run_in_background`: `true`
- `model`: tier-assigned (budget for L2/L4/L5, pro for L1/L3)

**Batch fire all 5 at once, then wait for all to return before reporting:**

```
task(description="L1 Library State", prompt=L1_PROMPT, run_in_background=true, max_steps=10, model=pro)
task(description="L2 Directory Survey", prompt=L2_PROMPT, run_in_background=true, max_steps=10, model=budget)
task(description="L3 Git State", prompt=L3_PROMPT, run_in_background=true, max_steps=10, model=pro)
task(description="L4 Existing AGENTS.md", prompt=L4_PROMPT, run_in_background=true, max_steps=10, model=budget)
task(description="L5 Staleness Check", prompt=L5_PROMPT, run_in_background=true, max_steps=10, model=budget)
```

### Lane Prompts

**L1_PROMPT — Library State:**
```
Check if .omo/library/ exists and what cache artifacts are present.

Run: ls -la .omo/library/ 2>/dev/null || echo "DIR_NOT_FOUND"
Run: for f in .omo/library/*.json .omo/library/*.jsonl .omo/library/*.sha256 .omo/library/*.txt; do
  if [ -f "$f" ]; then echo "FILE: $f ($(wc -c < "$f") bytes)"; fi
done

RETURN EXACTLY:
1. LIBRARY_EXISTS: yes | no
2. ARTIFACTS: list of files with sizes
3. LAST_SCAN: content of scanned-at.txt if it exists, else "NEVER"
4. CACHED_HEAD: content of head.sha256 if it exists, else "NONE"
```

**L2_PROMPT — Directory Survey:**
```
Survey directory structure. Use glob("**/*") on the target directory (default: current dir), count files by extension, identify top-level directories.

Skip: node_modules, .git, dist, build, __pycache__, .venv, vendor, target.

RETURN EXACTLY:
1. TOP_DIRS: list of top-level directories with file counts
2. EXTENSIONS: top 10 file extensions by count
3. TOTAL_FILES: <N> (excluding skipped dirs)
4. HAS_AGENTS_MD: list of all directories containing AGENTS.md files
```

**L3_PROMPT — Git State:**
```
Check git repository state for cache staleness detection.

Run: git rev-parse HEAD 2>/dev/null || echo "NO_GIT_REPO"
Run: git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "NO_BRANCH"
Run: git log -1 --format=%ct 2>/dev/null || echo "NO_COMMITS"

RETURN EXACTLY:
1. GIT_AVAILABLE: yes (commits exist) | bare (no commits) | no (.git missing)
2. HEAD_HASH: <hash> or "NONE"
3. BRANCH: <name> or "NONE"
4. LAST_COMMIT_EPOCH: <unix timestamp> or "NONE"
```

**L4_PROMPT — Existing AGENTS.md:**
```
Find any existing AGENTS.md files in the project (glob("**/AGENTS.md")).

For each AGENTS.md found:
- Check if it has GUARD markers (<!-- GUARD:BEGIN --> ... <!-- GUARD:END -->)
- Count lines inside vs outside guards
- Read the first 20 lines to understand structure

RETURN EXACTLY:
1. AGENTS_FILES: list of file paths
2. GUARDED: which files have GUARD markers
3. CUSTOM_CONTENT: has user-written content outside guards? yes/no per file
4. LAST_GENERATED: extract date from GUARD:BEGIN line if present
```

**L5_PROMPT — Staleness Summary:**
```
Cross-reference cache state with git state.

Compare:
- .omo/library/head.sha256 vs current git HEAD
- .omo/library/scanned-at.txt vs current time (days since last scan)

RETURN EXACTLY:
1. HEAD_MATCH: yes (cache matches current HEAD) | no (HEAD differs) | N/A (no cache or no git)
2. STALENESS_DAYS: <N> days since last scan (or "NEVER")
3. STALENESS_THRESHOLD: 7 days
4. VERDICT: FRESH (HEAD match + ≤7 days) | STALE (HEAD mismatch or >7 days) | EMPTY (no cache) | NO_GIT (git unavailable, trust timestamp)
5. RECOMMENDED_ACTION: load | update | scan | init-deep
```

Wait for all 5 lanes to return, then produce a consolidated library state report:

```markdown
## Library State
| Field | Value |
|---|---|
| **Library Exists** | yes / no |
| **Last Scan** | <ISO timestamp> or "NEVER" |
| **Cached HEAD** | <hash> or "NONE" |
| **Current HEAD** | <hash> or "NONE" |
| **HEAD Match** | yes / no / N/A |
| **Staleness (days)** | <N> or "NEVER" |
| **Verdict** | FRESH / STALE / EMPTY / NO_GIT |
| **Recommended** | <command suggestion> |
```

---

## Phase 2 — init-deep (AGENTS.md Generator)

Generate AGENTS.md files for directories that score above threshold or lack coverage.

### 2.1 Directory Complexity Scoring

For each target directory (default: all top-level dirs, max depth 2):
- **file_count**: number of source files (normalized: log2)
- **total_loc**: sum of line counts (normalized: log10)
- **subdirs**: count of subdirectories
- **export_count**: count of exported symbols (functions, classes, types)
- **has_test_dir**: +0.1 if tests/ or __tests__ or spec/ exists
- **has_agents_md**: -0.3 if AGENTS.md already exists (avoid redundant generation)
- **churn_30d**: git log --oneline --since="30 days ago" -- <dir> | wc -l

Score formula:
```
score = clamp(
  0.15 * norm_file_count +
  0.20 * norm_loc +
  0.10 * norm_subdirs +
  0.25 * norm_exports +
  0.10 * test_bonus +
  0.20 * churn_bonus
, 0.0, 1.0)
```

Where each factor is min-max normalized across all directories scanned.

### 2.2 AGENTS.md Generation

For each directory where score ≥ 0.5 or no AGENTS.md exists:

1. **Read existing AGENTS.md** if present — extract content OUTSIDE GUARD markers
2. **Scan directory**: use glob + grep to inventory files, exports, imports
3. **Classify layer**: Interface (HTTP/CLI handlers), Application (services), Domain (entities/logic), Infrastructure (DB/network)
4. **Detect conventions**: error handling pattern, test file pattern, naming convention
5. **Generate AGENTS.md** with GUARD markers:

```markdown
<!-- AGENTS.md — Auto-generated by blackcow-librarian init-deep -->
<!-- DO NOT EDIT between GUARD markers. Add custom content OUTSIDE guards. -->
<!-- GUARD:BEGIN — Last generated: {{TIMESTAMP}} -->

## Directory: {{DIR_PATH}}
**Complexity Score**: {{SCORE}}/1.0
**Last Generated**: {{TIMESTAMP}}

### File Map
| File | LOC | Exports | Layer |
|------|-----|---------|-------|
{{#files}}
| `{{name}}` | {{loc}} | {{exports_list}} | {{layer}} |
{{/files}}

### Entry Points
{{#entry_points}}
- `{{symbol}}` (`{{file}}:{{line}}`) — {{kind}}
{{/entry_points}}

### Dependencies
{{#deps}}
- `{{file}}` → imports from `{{imports_list}}`
{{/deps}}

### Conventions
- Error handling: {{error_pattern}}
- Testing: {{test_pattern}}
- Naming: {{naming_pattern}}

<!-- GUARD:END -->
{{CUSTOM_CONTENT}}
```

### 2.3 Safety Rules (S2: append-only guarantee)

1. **NEVER overwrite existing content outside GUARD markers** — extract custom content before regeneration, append it after the GUARD:END marker
2. **Backup before write**: if AGENTS.md exists, copy to `AGENTS.md.bak-<timestamp>` before writing
3. **Verify after write**: read back the file, confirm GUARD:BEGIN and GUARD:END markers are present and balanced
4. **Hash tracking**: write `{dir, agents_md_hash, generated_at}` to `.omo/library/agents/manifest.jsonl`
5. **Backup retention**: keep last 10 backups per AGENTS.md file (`AGENTS.md.bak-*`), delete older ones. Archive backups older than 30 days.

### 2.4 init-deep Evidence

Write evidence to `.omo/ulw-loop/evidence/init-deep-summary.txt`:
```
# init-deep Summary
Timestamp: <ISO>
Directories Scored: <N>
Directories Generated: <N>
AGENTS.md Created: <list>
AGENTS.md Updated: <list>
AGENTS.md Skipped (low score): <list>
```

---

## Phase 3 — scan (Structure Cache Builder) [3-BATCH DISPATCH]

Build the full `.omo/library/` cache from scratch. Dispatch is split into three serial batches to resolve hidden data dependencies (SCAN_SYMBOL needs SCAN_SURFACE file list and entry points; SCAN_DEP needs SCAN_SYMBOL output). Serialization overhead ~+2K tokens — required for correctness.

### 3.1 Pre-scan Setup

```bash
mkdir -p .omo/library/agents
```

### 3.2 Parallel Scan Lanes (5 LANES, 3-BATCH DISPATCH)

**CRITICAL: Dispatch Batch 1 first, wait for ALL Batch 1 lanes to complete, then dispatch Batch 2.**
**Data dependency chain: SCAN_SYMBOL reads SCAN_SURFACE output (file list + public symbol names before it can trace references). SCAN_DEP and SCAN_ENTRY read SCAN_SURFACE output (entry points). Serialization overhead ~+2K tokens — required for correctness.**

Every lane subagent uses:
- `tools`: `["read_file","grep","glob","ls","bash"]`
- `max_steps`: 15
- `run_in_background`: `true`
- `model`: budget

**Batch 1 — Independent scans. Dispatch first, wait for ALL to complete:**
```
task(description="SCAN Surface Topology", prompt=SCAN_SURFACE_PROMPT, run_in_background=true, max_steps=15, model=budget)
task(description="SCAN Directory Scores", prompt=SCAN_DIRSCORE_PROMPT, run_in_background=true, max_steps=15, model=budget)
```

**Batch 2 — SCAN_SYMBOL (dispatch AFTER Batch 1 completes). Reads SURFACE output for file list and entry point candidates:**
```
task(description="SCAN Symbol Index", prompt=SCAN_SYMBOL_PROMPT, run_in_background=true, max_steps=15, model=budget)
```

**Batch 3 — SCAN_DEP + SCAN_ENTRY (dispatch AFTER Batch 2 completes). SCAN_DEP reads SYMBOL output for dependency graph. SCAN_ENTRY reads SURFACE output for entry/exit point mapping:**
```
task(description="SCAN Dep Graph", prompt=SCAN_DEP_PROMPT, run_in_background=true, max_steps=15, model=budget)
task(description="SCAN EntryExit Points", prompt=SCAN_ENTRY_PROMPT, run_in_background=true, max_steps=15, model=budget)
```

### Scan Lane Prompts

**SCAN_SURFACE_PROMPT — Surface Topology:**
```
Map every source file in the project. Skip: node_modules, .git, dist, build, __pycache__, .venv, vendor, target, .omo.

For each source file, collect:
- file path
- line count (wc -l)
- file extension
- layer classification:
  - Interface: files containing HTTP handlers, route definitions, CLI entry points, controllers
  - Application: service files, use-case orchestrators, middleware
  - Domain: entity/model definitions, business logic, types/interfaces
  - Infrastructure: database connections, API clients, file I/O, config loaders

RETURN as JSONL (one JSON object per line):
{"file": "<path>", "ext": "<ext>", "loc": <N>, "layer": "Interface|Application|Domain|Infrastructure"}
{"entry_points": ["<file:line>", ...], "api_routes": ["<method> <path>", ...]}
```

The last line is a summary object with all identified entry points and API routes. SCAN_ENTRY uses this to build entry-exit.json.

**SCAN_SYMBOL_PROMPT — Symbol Index:**
```
For each source file from the surface topology, extract exported and significant internal symbols.

Scan each file for:
- Functions: `func `, `fn `, `function `, `def `
- Classes: `class `, `interface `, `type ` (struct/enum)
- Constants: `const `, `export const`, uppercase identifiers
- Note the line number and whether exported

RETURN as JSONL (one JSON object per file):
{"file": "<path>", "sha256": "<hash>", "symbols": [{"name": "<s>", "kind": "function|class|const", "line": <N>, "exported": true|false}], "imports": ["<path>"], "exports": ["<name>"], "layer": "<layer>", "loc": <N>, "scanned_at": "<ISO>"}
```

**SCAN_DEP_PROMPT — Dependency Graph:**
```
Build a dependency graph from import statements.

Grep for imports: `import`, `require(`, `from `, `use ` 
For each import, resolve to a file path within the project (skip external packages).

Build:
- nodes: [{id: "<file>", layer: "<layer>", loc: <N>}]
- edges: [{from: "<file>", to: "<imported-file>", type: "direct|type-only"}]

RETURN as a single JSON object:
{"nodes": [...], "edges": [...]}
```

**SCAN_ENTRY_PROMPT — Entry/Exit Points:**
```
Identify all entry points (where execution begins) and exit points (where data leaves the system).

Entry points:
- HTTP handlers (grep for: @Get, @Post, app.get, router.get, handler, controller)
- CLI commands (grep for: main(, if __name__, argparse, click.command, commander)
- Cron/job handlers (grep for: cron, schedule, job, worker)
- Event handlers (grep for: subscribe, on(, listener, emit)

Exit points:
- Database writes (grep for: .save(, .insert, .update, .create, .put)
- HTTP outbound (grep for: fetch(, axios, http.request, curl)
- File writes (grep for: writeFile, fs.write, open(.*'w')
- Queue publishes (grep for: .publish, .send, .enqueue, .push)

RETURN as a single JSON array:
[{"type": "entry|exit", "subtype": "http|cli|cron|event|db|http-out|file|queue", "symbol": "<name>", "file": "<path>", "line": <N>, "layer": "<layer>"}]
```

**SCAN_DIRSCORE_PROMPT — Directory Scores:**
```
Score each directory using the init-deep formula (Phase 2.1).

For each directory (max depth 2):
- file_count: count of source files
- total_loc: sum of line counts
- subdirs: count of subdirectories
- export_count: count of exported symbols
- has_test_dir: true if tests/ or __tests__ or spec/ exists
- has_agents_md: true if AGENTS.md exists
- churn_30d: count of git log entries in last 30 days (0 if git unavailable)

Normalize each factor across all directories, compute score.

RETURN as a single JSON array:
[{"dir": "<path>", "score": <0.0-1.0>, "factors": {"file_count": <N>, "total_loc": <N>, "subdirs": <N>, "export_count": <N>, "has_test_dir": true|false, "has_agents_md": true|false, "churn_30d": <N>}, "recommendation": "GENERATE|SKIP", "scanned_at": "<ISO>"}]
```

### 3.3 Merge and Write

After all 5 scan lanes return:

1. **Merge symbol data with surface topology**: join on file path, produce `structure-cache.jsonl`
2. **Write dep-graph.json**: from SCAN_DEP lane
3. **Write entry-exit.json**: from SCAN_ENTRY lane
4. **Write dir-scores.json**: from SCAN_DIRSCORE lane
5. **Write head.sha256**: `git rev-parse HEAD > .omo/library/head.sha256` (or "NO_GIT" if unavailable)
6. **Write scanned-at.txt**: `date -u +%Y-%m-%dT%H:%M:%SZ > .omo/library/scanned-at.txt`

### 3.4 scan Evidence

Write evidence to `.omo/ulw-loop/evidence/scan-summary.txt`:
```
# scan Summary
Timestamp: <ISO>
Files Scanned: <N>
Symbols Indexed: <N>
Edges in Dep Graph: <N>
Entry Points: <N>
Exit Points: <N>
Directories Scored: <N>
Cache Size: <N> KB
```

### 3.5 Post-Scan Verification (MANDATORY — M2/M5/M3 Gates)

**Dispatch 3 verification `task` subagents with `run_in_background=true`, `model=budget`, `max_steps=8`:**

```
task(description="V-M2 SpotCheck", prompt="Randomly sample 5 entries from .omo/library/structure-cache.jsonl. For each: verify the referenced file exists on disk, verify LOC matches (bash wc -l). RETURN EXACTLY: pass:bool, samples_checked:int, mismatches:list, notes:str", run_in_background=true, max_steps=8, model=budget)
task(description="V-M5 Prune", prompt="Scan .omo/library/structure-cache.jsonl for entries whose source files no longer exist on disk. Remove dead entries, write pruned count + file paths to .omo/library/prune-log.jsonl. RETURN EXACTLY: pass:bool, dead_entries_found:int, pruned:int, pruned_files:list", run_in_background=true, max_steps=8, model=budget)
task(description="V-M3 Snapshot", prompt="Capture structural snapshot: count files, total LOC, symbols, entry points from cache. Compare against pre-scan baseline if exists. Flag any decrease >5%. Write to .omo/library/structural-snapshot.json. RETURN EXACTLY: pass:bool, files_before:int, files_after:int, loc_before:int, loc_after:int, symbols_before:int, symbols_after:int, regressions:list", run_in_background=true, max_steps=8, model=budget)
```

Wait for all 3 to return. If any fail → flag in scan summary. Evidence written to `.omo/ulw-loop/evidence/scan-verification.txt`.

---

## Phase 4 — update (Incremental Updater)

Update the cache incrementally — only re-scan files changed since the last full scan.

### 4.1 Git Diff Detection

```bash
CACHED_HEAD=$(cat .omo/library/head.sha256 2>/dev/null || echo "NONE")
CURRENT_HEAD=$(git rev-parse HEAD 2>/dev/null || echo "NO_GIT")

if [ "$CACHED_HEAD" = "NONE" ] || [ "$CURRENT_HEAD" = "NO_GIT" ]; then
  echo "Cannot incrementally update — no baseline cache or git unavailable. Run scan first."
  exit 1
fi
```

### 4.2 Changed File Detection

```bash
# Get list of changed files between cached HEAD and current HEAD
git diff --name-status "$CACHED_HEAD" "$CURRENT_HEAD" 2>/dev/null

# Parse output:
# A <file>  → added: scan fully, append to cache
# M <file>  → modified: re-scan, replace entry in cache
# D <file>  → deleted: remove entry from cache
# R<X> <old> <new> → renamed: update path in cache
```

### 4.3 Incremental Re-scan

For changed files (A, M, R):

**Batching rule**: If 20+ changed files, split into groups of 15, dispatching all groups as parallel `task()` subagents (budget, max_steps=8). Otherwise scan one-at-a-time.

For each changed file:
1. Dispatch a `task` subagent (budget, max_steps=8) to scan that single file
2. Collect: symbols, imports, exports, layer, loc
3. Merge back into `structure-cache.jsonl`:
   - Added: append new JSON line
   - Modified: replace the existing line for that file
   - Renamed: update the file field, re-scan if content changed

For deleted files (D):
- Remove the corresponding line from `structure-cache.jsonl`
- Update `dep-graph.json`: remove node, remove edges referencing this file

### 4.4 Update Metadata

```bash
git rev-parse HEAD > .omo/library/head.sha256
date -u +%Y-%m-%dT%H:%M:%SZ > .omo/library/scanned-at.txt
```

### 4.5 update Evidence

Write evidence to `.omo/ulw-loop/evidence/update-summary.txt`:
```
# update Summary
Timestamp: <ISO>
Previous HEAD: <hash>
Current HEAD: <hash>
Files Added: <N>
Files Modified: <N>
Files Deleted: <N>
Files Renamed: <N>
Total Changes: <N>
Cache Updated: yes
```

---

## Phase 5 — check (Staleness Validator)

Validate cache freshness without modifying anything.

### 5.1 Freshness Check Logic

```
1. Check .omo/library/ exists → if not: EMPTY → recommend "scan"
2. Read .omo/library/head.sha256 → if "NO_GIT": trust timestamp only
3. Read .omo/library/scanned-at.txt → compute days since scan
4. Get current git HEAD: git rev-parse HEAD 2>/dev/null || echo "NO_GIT"
5. Compare:
   - HEAD match + ≤7 days → FRESH
   - HEAD match + >7 days → STALE (age)
   - HEAD mismatch → STALE (HEAD changed)
   - No cache → EMPTY
   - No git → trust timestamp only (FRESH if ≤7d, STALE if >7d)
6. Verify cache file integrity:
   - structure-cache.jsonl is valid JSON Lines (each line parses as JSON)
   - dep-graph.json is valid JSON
   - entry-exit.json is valid JSON array
   - dir-scores.json is valid JSON array
```

### 5.2 Check Output

```markdown
## Cache Status: <FRESH|STALE|EMPTY|NO_GIT>

| Field | Value |
|---|---|
| **Cached HEAD** | <hash> |
| **Current HEAD** | <hash> |
| **HEAD Match** | yes / no / N/A |
| **Last Scan** | <ISO timestamp> |
| **Days Stale** | <N> |
| **Threshold** | 7 days |
| **Files Cached** | <N> |
| **Cache Size** | <N> KB |
| **Integrity** | valid / corrupt: <details> |
| **Verdict** | FRESH / STALE / EMPTY |
| **Recommendation** | load / update / scan |
```

### 5.3 check Evidence

Write to `.omo/ulw-loop/evidence/check-result.txt`:
```
# check Result
Timestamp: <ISO>
Verdict: FRESH|STALE|EMPTY|NO_GIT
HEAD Match: yes|no|N/A
Days Stale: <N>
Integrity: valid|corrupt
```

---

## Phase 6 — load (Cache Reader)

Load cache into context for downstream consumption by blackcow-plan, blackcow-loop, blackcow-qa.

### 6.1 Load Path

1. Run Phase 5 (check) inline
2. If STALE: warn but load anyway (caller decides)
3. If EMPTY: return error, suggest `scan`
4. If FRESH: load with confidence tag

### 6.2 Loaded Context Format

Return structured context that downstream skills can directly consume:

```markdown
## [CACHE-LOAD] blackcow-librarian — Loaded from .omo/library/

| Field | Value |
|---|---|
| **Source** | structure-cache.jsonl (files, symbols, layers) + entry-exit.json (entry/exit points) + dep-graph.json (dependencies) + dir-scores.json (directory scores) |
| **Cached HEAD** | <hash> |
| **Scanned At** | <ISO timestamp> |
| **Freshness** | FRESH (≤7d) / STALE (>7d or HEAD changed) |
| **File Count** | <N> |
| **Symbol Count** | <N> |

### Top-Level Directory Map *(source: structure-cache.jsonl)*
| Directory | Files | LOC | Layer Mix |
|---|---|---|---|

### Entry Points *(source: entry-exit.json)*
| Symbol | File:Line | Type | Layer |
|---|---|---|---|

### Layer Summary *(source: structure-cache.jsonl)*
| Layer | Files | LOC | % of Codebase |
|---|---|---|---|

### Key Dependencies (top 10 by in-degree) *(source: dep-graph.json)*
| File | Imported By (count) | Layer |
|---|---|---|

[CACHE-LOAD-END]
```

### 6.3 Integration Contract

Downstream skills (blackcow-plan, blackcow-loop, blackcow-qa) integrate as follows:

```markdown
## Phase 0 — Pre-flight (with blackcow-librarian auto-load)

### 0.0 Cache Load
If `.omo/library/` exists:
  Run `--command=check` inline
  If FRESH: load Phase 6 context, SKIP glob/grep discovery lanes
  If STALE: warn, run `--command=update`, then load
  If EMPTY: fall through to legacy discovery

If no cache: legacy Phase 0 glob/grep discovery as before.
```

### 6.4 load Evidence

Write to `.omo/ulw-loop/evidence/load-result.txt`:
```
# load Result
Timestamp: <ISO>
Files Loaded: <N>
Symbols Loaded: <N>
Context Size: <N> chars
Freshness: FRESH|STALE
```

---

### 6b. load-evidence (Evidence Index Reader)

Load the Evidence Compaction Index from a prior blackcow-loop completion report:

1. Check `.omo/ulw-loop/completion-report.md` exists
2. Extract Evidence Compaction Index table
3. Verify artifact hashes match (re-compute sha256 of each artifact)
4. If hash mismatch → flag artifact as CORRUPT, do not trust the gate result
5. Return compact summary: which gates passed, which failed, artifact paths, hash validity

**Output format:**
```markdown
## [EVIDENCE-LOAD] blackcow-librarian — From completion report

| evidence_id | gate | status | artifact_path | hash_valid |
|---|---|---|---|---|
| E001 | M2 | PASS | .omo/ulw-loop/evidence/<slug>-m2.txt | ✅ |
| E002 | M3 | PASS | .omo/ulw-loop/evidence/<slug>-m3.txt | ✅ |
...
```

This enables `blackcow-qa` and `blackcow-governor` to skip already-passed gates.

## Phase 7 — Integration Hooks (for downstream skills)

### 7.0 Governor Integration

The librarian feeds `blackcow-governor` via:
```
run_skill({ name: "blackcow-governor", arguments: "--load-failure-patterns --load-roi-history <task>" })
```
Governor consumes `.omo/memory/failure-patterns.jsonl` and `.omo/memory/loop-roi.jsonl` during Phase 0 preflight.

### 7.1 blackcow-plan Phase 0 Patch

Replace blackcow-plan Phase 0 glob-based pre-flight with cache-first approach:

```markdown
## Phase 0 — Pre-flight (1 BATCH + CACHE LOAD)

### 0.0 Cache Load (blackcow-librarian integration)

Attempt cache load BEFORE any glob/grep discovery:

1. Check: `ls .omo/library/structure-cache.jsonl 2>/dev/null`
2. If exists, run staleness check:
   - Read `.omo/library/head.sha256`
   - Compare with `git rev-parse HEAD 2>/dev/null || echo "NO_GIT"`
   - Read `.omo/library/scanned-at.txt`
   - If HEAD matches and ≤7 days old: **LOAD CACHE, skip glob/grep**
   - Else: mark cache as STALE, fall through to legacy discovery

3. Cache load format: extract file list and layer map from structure-cache.jsonl; entry/exit points from entry-exit.json
   - This replaces: glob("**/*.{ts,js,py,rs,go,css,html}") and glob("{package.json,pyproject.toml,...}")

4. Always run: glob("{.git/HEAD,.git/index}") — cheap, always needed

### 0.1 Legacy Discovery (fallback when cache absent/stale)

```
glob("**/*.{ts,js,py,rs,go,css,html}")           → project scale
glob("{package.json,pyproject.toml,Cargo.toml,go.mod,requirements.txt}") → stack
glob("{.git/HEAD,.git/index}")                     → git check
glob("**/*")  → root listing
```
```

### 7.2 blackcow-loop Phase 0 Patch

Replace blackcow-loop Phase 0.3 parallel discovery with cache-first:

```markdown
### 0.0 Cache Load (blackcow-librarian integration)

Before dispatching 7+2 bootstrap lanes, check for cache:

1. If `.omo/library/structure-cache.jsonl` exists and is FRESH (≤7d, HEAD match):
   - Load surface topology, symbol index, dep graph, entry/exit points from cache
   - This replaces L2 (Call Site Inventory), L4 (Test Blueprint), L7 (Dependency Impact) bootstraps
   - Still dispatch L1 (Target Deep Read) — always needed for current task
   - Still dispatch L3 (Pattern Library) — always needed for pattern reference
   - Still dispatch L5 (Tooling Cheatsheet) — always needed for command reference
   - Still dispatch L6 (External Research) — always needed for library freshness
   - Estimated savings: ~8K tokens per Phase 0

2. If cache is STALE or absent: fall through to standard 7+2 lane Phase 0.3
```

### 7.3 blackcow-qa Phase 0 Patch

```markdown
### 0.0 Cache Load (blackcow-librarian integration)

Before dispatching 5 QA discovery lanes, check for cache:

1. If `.omo/library/structure-cache.jsonl` exists and is FRESH:
   - Load entry points, data shapes, auth gate locations from cache
   - Still dispatch L1 (Test Inventory) — tests are not cached
   - Still dispatch L4 (External Audit) — library CVE checks are not cached
   - Still dispatch L5 (Runtime Probe) — runtime behavior is not cached
   - Skip L2 (Code Structure Audit) — entry points and data shapes are in cache
   - Skip L3 (Plan Extraction) if plan already known
   - Estimated savings: ~5K tokens per Phase 0
```

---

## Cost Budget (per Command)

| Command | Lanes | Model Mix | Est. Tokens | Est. Cost (DeepSeek) |
|---|---|---|---|---|
| `init-deep` | 5 (Phase 1) + scan per dir | 60% budget, 40% pro | ~8K | ~$0.001 |
| `scan` | 5 lanes, 2 batches (Phase 3) | 100% budget | ~14K | ~$0.0012 |
| `update` | N changed files (Phase 4) | 100% budget | ~6K | ~$0.0005 |
| `check` | inline (Phase 5) | — | ~2K | ~$0.0002 |
| `load` | inline (Phase 6) | — | ~1K | ~$0.0001 |
| **Full init** | 5 + 5 + inline | 60/40 mix | ~24K | ~$0.002 |

### Gate Coverage (BKIT 11-Gate)

| Gate | Status | How Verified |
|---|---|---|
| M1 spec-match | ✅ | scan: file-level comparison vs git HEAD baseline |
| M2 test-pass | ✅ | Phase 3.5 V-M2: random 5-entry spot-check (file exists + LOC match) |
| M3 regression | ✅ | Phase 3.5 V-M3: structural snapshot pre/post scan comparison |
| M4 lint | N/A | Cache files are structured data, not lintable code |
| M5 dead-code | ✅ | Phase 3.5 V-M5: prune cache entries for deleted source files |
| S1 dataFlow | ✅ | Entry/exit points validated via entry-exit.json integrity check |
| S2 auth | N/A | No runtime entry points in caching layer |
| S3 injection | N/A | No executable code paths |
| P1 query | N/A | No database queries |
| P2 memory | ✅ | 10MB cache cap + rotation strategy + prune-log.jsonl |
| P3 latency | ✅ | <500ms incremental update; full scan parallelized in 3 batches (est. based on typical project size) |

Applicable gates: 7/11. Covered: 7/7.

---

## Stop Rules

| Condition | Action |
|---|---|
| Cache directory missing | Suggest `scan` or `init-deep` |
| Git unavailable (no .git, no commits) | Use timestamp-based staleness; flag NO_GIT in output |
| AGENTS.md already exists with GUARD markers | Extract custom content, regenerate only guarded section |
| scan/update writes fail | Report error, preserve previous cache |
| Duplicate file entries in cache | Deduplicate by file path, keep newest scanned_at |
| Cache size > 10MB | Warn, suggest rotation (archive old entries) |

## Failure-Pattern Memory (`.omo/memory/failure-patterns.jsonl`)

The librarian stores structured failure records to inform future governor decisions. When a gate repeatedly fails or a fix pattern succeeds, record it.

### Schema

```json
{
  "failure_id": "<uuid>",
  "stack": "<area/module>",
  "area": "<file or domain>",
  "failure_gate": "M1|M2|M3|M4|M5|S1|S2|S3|P1|P2|P3",
  "symptom": "<concise description>",
  "root_cause": "<diagnosis from PDCA D1>",
  "successful_fix": "<what resolved it>",
  "fix_file_line": "<file:line of the fix>",
  "verification": "<how fix was confirmed>",
  "occurrence_count": <N>,
  "first_seen": "<ISO>",
  "last_seen": "<ISO>",
  "resolved": true|false,
  "resolution_effectiveness": <0-100>,
  "reappeared_after_fix": true|false,
  "fix_persistence_days": <N>
}
```

**Resolution effectiveness**: After marking resolved, track for 30 days. If the same gate+symptom reappears, set `reappeared_after_fix: true` and `resolution_effectiveness: 0`. If no recurrence for 30 days, `resolution_effectiveness: 100`. This feeds back into auto-fix suggestion confidence.
```

### Integration with Governor

Before each `blackcow-plan` or `blackcow-loop` invocation, check `.omo/memory/failure-patterns.jsonl`:
- If current task area matches a known failure pattern → escalate gate priority
- If pattern resolved >3 times → suggest automated fix template
- Feed unresolved patterns into IntentGate for severity escalation

### Known Patterns (SEED data, STATIC_EVAL)

These patterns were observed during BlackCow's own development and serve as calibration:

| Pattern | Gate | Symptom | Fix |
|---|---|---|---|
| `task()` tool mismatch | M1 | Subagent dispatch fails with "tool not registered" | Use `explore()` + platform adaptation note |
| `lsp_*` phantom tools | M1 | allowed-tools references non-existent tools | Replace with `get_symbols`/`find_in_code` |
| Model name drift | M1 | `deepseek-v4-lite` invalid → API errors | Use current model name (`deepseek-v4-flash`) |
| Nested code blocks | M4 | Markdown parser breaks on ` ``` ` inside ` ``` ` | Use 4-backtick fences for outer blocks |
| Stale global install | M3 | `~/.reasonix/skills/` differs from project `skills/` | Run `install.sh` after every skill edit |

### Trend Analysis

Before feeding patterns to governor, compute:
- **Recurrence rate**: occurrences per 30 days → if >3, escalate from HIGH to CRITICAL
- **Mean time to resolve**: avg days from first_seen to resolved → if >14 days, flag for architectural review
- **Gate hotspot**: which gate appears most in unresolved patterns → suggest permanent gate hardening
- **Auto-fix suggestion**: if any resolved pattern has `occurrence_count ≥ 3` and same `symptom`, generate a fix template:
  ```
  # Auto-fix template for <failure_gate>
  # Based on <N> successful resolutions
  # Symptom: <symptom>
  # Apply: <successful_fix>
  # Verify: <verification>
  ```
  Feed this template to blackcow-loop as a pre-emptive fix before PDCA starts.

**ROI correlation**: For each unresolved pattern, check `.omo/memory/loop-roi.jsonl` for tasks in the same area. Compute:
- `avg_cycles_wasted`: average PDCA cycles spent on this gate before resolution
- `tokens_wasted_estimate`: cycles × avg tokens per cycle
- `fix_roi`: tokens_wasted / (tokens to apply known fix)

If `fix_roi > 3` (fix saves 3× the tokens it costs), auto-recommend the fix to governor.

Write trend summary to `.omo/memory/failure-trends.json`:
```json
{"gate_hotspots": {"S2": 4, "M1": 2}, "mean_resolution_days": 12.3, "recurrence_alerts": ["<pattern_id>"]}
```

### Rotation
- Cap at 200 entries
- Archive entries with `resolved: true` and `last_seen > 90 days` to `.omo/memory/failure-patterns-archive.jsonl.gz`

## Constraints

1. **NEVER overwrite user content** in AGENTS.md — only content between GUARD markers
2. **Always backup** before writing AGENTS.md
3. **Deduplicate cache entries** by file path
4. **Handle NO_GIT gracefully** — timestamp-based staleness
5. **Max cache size: 10MB** — warn and suggest rotation if exceeded
6. **Parallel dispatch within each batch** — all scan lanes within a batch run simultaneously
7. **Skip dirs**: node_modules, .git, dist, build, __pycache__, .venv, vendor, target, .omo
8. **JSON Lines format** for structure-cache.jsonl — append-friendly, human-readable
9. **Git diff --name-status** for update — captures adds, modifies, deletes, renames
10. **M2 cache correctness verification** (MANDATORY after scan/update): sample 5 random cache entries, verify referenced file exists and LOC matches (`wc -l`). Log spot-check results to `.omo/library/spot-check.jsonl`. Any mismatch → flag in output.
11. **M5 dead entry pruning** (MANDATORY after scan/update): scan cache for entries whose source files no longer exist on disk. Remove dead entries, write pruned count + file paths to `.omo/library/prune-log.jsonl`.
12. **M3 structural snapshot** (MANDATORY before/after scan): capture `{file_count, total_loc, symbol_count, entry_points}` before scan. Compare after scan — flag any unexpected decreases (>5%). Write snapshot to `.omo/library/structural-snapshot.json`.

## Self-Audit Checklist

Before completing any command, verify:
- [ ] Cache integrity: structure-cache.jsonl is valid JSON Lines (every line parses)
- [ ] HEAD match verified: cached head.sha256 matches current git HEAD
- [ ] Staleness threshold honored: >7 days triggers update recommendation
- [ ] AGENTS.md GUARD markers intact: no user content overwritten
- [ ] Backup created before any AGENTS.md write
- [ ] Failure-pattern memory: unresolved patterns loaded for governor feed
- [ ] No phantom file references in cache (all entries resolve to existing files)
- [ ] M2 spot-check passed: 5 random cache entries verified
- [ ] M5 pruning completed: dead entries removed
- [ ] No fabricated cache entries or file references
- [ ] All spot-check results from actual file reads

### Anti-Hallucination Guards

**NEVER fabricate cache data.** Violation = invalid librarian run:
- ❌ Create cache entries for files you haven't read
- ❌ Guess LOC counts — must come from `wc -l`
- ❌ Invent symbol names — must come from actual file inspection
- ❌ Claim HEAD matches without running `git rev-parse`
