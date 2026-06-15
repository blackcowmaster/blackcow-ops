# Plan: Add --json stdout flag to ecosystem-health script

| Field | Value |
|---|---|
| **Slug** | `ecosystem-health-json-flag` |
| **Created** | `2025-07-16T00:00:00Z` |
| **Class** | `XS` |
| **Explore lanes** | `5 dispatched, 5 returned` |
| **Adversarial reviews** | `0 (XS skip)` |
| **Budget** | `estimated 8K tokens / 128K target` |

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | `--json` flag is dead code — parsed but never read. Machine consumers need structured JSON on stdout. |
| **WHO** | CI/CD pipelines, monitoring dashboards, automated governance systems |
| **WHAT** | `skills/tests/validate-blackcow-ecosystem-health.sh` modified to emit specified JSON schema to stdout when `--json` is passed |
| **RISK** | Low — single file, purely additive, zero behavioral change without `--json` |
| **SUCCESS** | matchRate ≥ 90%, test pass=100%, lint=0warn, coverage ≥ 80%, p95_target_ms: N/A |
| **SCOPE** | ONLY `skills/tests/validate-blackcow-ecosystem-health.sh`; no other files touched |

## Summary

The `--json` flag in `validate-blackcow-ecosystem-health.sh` is currently dead code — it sets `JSON_OUT=true` but that variable is never read. The script always prints human-readable tables and always writes JSON to a disk file (not stdout). This plan makes `--json` functional: it suppresses all text output and prints a single JSON object to stdout matching the required schema. The implementation uses `exec` fd redirection to avoid touching every output call site, keeping the change minimal (~30 net new lines) and backward-compatible.

## Codebase Survey (5-Lane Summary)

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| Surface | 453-line script, 7 major output sections, `--json` parsed at line 43 but never read | explore lane 1 | — |
| Call Graph | `JSON_OUT` has exactly 2 references: init (line 31) and set (line 43). Never read. | explore lane 2 | S1 |
| Data Shapes | 3 gaps vs required schema: missing `scripts[].status`, missing `elapsed_s`, flat `aggregate` | explore lane 3 | S1 |
| Tests | No dedicated tests exist; `.omo/ulw-loop/collect-evidence.sh` invokes for M2/M3 gates | explore lane 4 | M2, M3 |
| Patterns | No existing `--json`→stdout pattern; `for arg; case` flag pattern is project standard | explore lane 10 + governance doc | — |

## Gap Matrix

| Cat | Item | Evidence | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| 🔧 Modify | `START_TIME`: add `START_EPOCH=$(date +%s)` for elapsed computation | `skills/tests/validate-blackcow-ecosystem-health.sh:31` | HIGH | low | M1 |
| 🔧 Modify | Arg parsing: `--json` also sets `VERBOSE=false` to prevent streamed sub-script output | `:41-46` | HIGH | low | M3 |
| 🆕 Build | `exec` fd redirection gate after arg parsing: save fd 3, redirect fd 1 to /dev/null when JSON_OUT | — | — | low | M3 |
| 🆕 Build | JSON stdout emission block: bash-native `printf` building exact schema | — | — | low | M1 |
| 🆕 Build | `ELAPSED_S=$(( $(date +%s) - START_EPOCH ))` computation | — | — | low | M1 |

## Waves

### Wave 1 — Implementation (1 task, ≤15K tokens)

- [ ] **step-1**: Implement `--json` stdout flag in `skills/tests/validate-blackcow-ecosystem-health.sh`
  - **Worker:** `medium`
  - **Token est:** ~5K
  - **Files:** `skills/tests/validate-blackcow-ecosystem-health.sh`
  - **Verify:** `bash skills/tests/validate-blackcow-ecosystem-health.sh --json 2>/dev/null | python3 -m json.tool > /dev/null && echo "VALID JSON"`
  - **Gate:** M1 (spec-match), M2 (test pass=100%)
  - **Evidence:** `.omo/ulw-loop/evidence/ecosystem-health-json-flag-w1-s1.txt`

## Risk Register (BKIT 11-Gate)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| JSON schema mismatch | `M1_spec_match` | HIGH | matchRate ≥ 90% | Validate output against schema with `python3 -m json.tool` | `bash ... --json \| python3 -c "import json,sys; d=json.load(sys.stdin); assert 'scripts' in d; assert 'aggregate' in d; assert 'traffic_light' in d; assert 'elapsed_s' in d; assert all(k in s for s in d['scripts'] for k in ['name','pass','fail','skip','score','status'])"` |
| Backward compat broken | `M3_regression` | HIGH | 0 regressions | `exec` redirection only activates when `JSON_OUT=true` | Run without `--json`, verify all text output identical |
| JSON invalid (special chars in script names) | `M1_spec_match` | LOW | valid JSON | Script names are `validate-*.sh` — no quotes or backslashes | `python3 -m json.tool` parse test |
| Verbose mode leaks text in JSON mode | `M3_regression` | MED | no text on stdout | `--json` forces `VERBOSE=false` | Run `--json --verbose`, verify only JSON on stdout |

## Implementation Guide

### Changes to `skills/tests/validate-blackcow-ecosystem-health.sh`

**Change 1** (line 31): Add epoch timer alongside ISO-8601.

```bash
# Before:
START_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# After:
START_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)
START_EPOCH=$(date +%s)
```

**Change 2** (lines 41-46): Update arg parsing to suppress verbose in JSON mode.

```bash
# Before:
    --json)    JSON_OUT=true ;;

# After:
    --json)    JSON_OUT=true; VERBOSE=false ;;
```

**Change 3** (after arg parsing, before color helpers): Add stdout suppression gate.

```bash
# After the arg parsing loop (after line 46), insert:
# --- JSON mode: suppress all normal stdout ---
if $JSON_OUT; then
  exec 3>&1 1>/dev/null
fi
```

**Change 4** (before `exit $EXIT_CODE`, after all existing output): Add JSON stdout emission.

```bash
# Before the final exit (before line 492 `exit $EXIT_CODE`), insert:
# --- JSON stdout emission ---
if $JSON_OUT; then
  exec 1>&3 3>&-                    # restore original stdout
  ELAPSED_S=$(( $(date +%s) - START_EPOCH ))

  printf '{'
  printf '"scripts":['
  first=true
  for i in "${!SCRIPT_NAMES[@]}"; do
    $first || printf ','
    first=false
    if [[ "${SCRIPT_FAIL[$i]}" -gt 0 ]]; then status="FAIL"; else status="PASS"; fi
    printf '{"name":"%s","pass":%d,"fail":%d,"skip":%d,"score":%d,"status":"%s"}' \
      "${SCRIPT_NAMES[$i]}" "${SCRIPT_PASS[$i]}" "${SCRIPT_FAIL[$i]}" \
      "${SCRIPT_SKIP[$i]}" "${SCRIPT_SCORE[$i]}" "$status"
  done
  printf '],'
  printf '"aggregate":{"pass":%d,"fail":%d,"skip":%d,"score":%d},' \
    "$OVERALL_PASS" "$OVERALL_FAIL" "$OVERALL_SKIP" "$AGGREGATE_SCORE"
  printf '"traffic_light":"%s",' "$TRAFFIC"
  printf '"elapsed_s":%d' "$ELAPSED_S"
  printf '}\n'
fi
```

### Design Rationale

1. **`exec` fd redirection** over manual `$JSON_OUT ||` gating on every output line: The script has ~40 output call sites across 7 sections. Wrapping each would be error-prone and bloated. The `exec 3>&1 1>/dev/null` pattern silently redirects all stdout to `/dev/null`, then `exec 1>&3 3>&-` restores the original stdout before the JSON `printf` block. This is a standard Unix pattern used in init scripts and daemon management.

2. **Bash-native `printf` over Python**: Avoids the `python3` dependency for stdout emission. The existing Python block (lines 449-479) that writes to `$HEALTH_JSON` disk file is preserved unchanged — it writes to file, not stdout, so no conflict. Script names are `validate-*.sh` patterns, safe from special-character issues.

3. **`VERBOSE=false` when `--json`**: In verbose mode, sub-scripts stream output directly to the terminal (not captured). With `exec 1>/dev/null` that's harmless (goes to null), but setting `VERBOSE=false` is cleaner and avoids the useless work.

4. **`START_EPOCH` separate from `START_TIME`**: The existing `START_TIME` (ISO-8601) is used in the text report header and "Runtime" line. Keeping it avoids changing any existing behavior. `START_EPOCH` is added solely for `elapsed_s` computation.

## Execution Command

```
blackcow-loop "Execute plans/ecosystem-health-json-flag.md" --completion-promise='Running bash skills/tests/validate-blackcow-ecosystem-health.sh --json produces valid JSON on stdout matching schema: {"scripts":[{"name":"...","pass":N,"fail":N,"skip":N,"score":N,"status":"PASS|FAIL"}],"aggregate":{"pass":N,"fail":N,"skip":N,"score":N},"traffic_light":"GREEN|YELLOW|RED","elapsed_s":N}' --trust-level=2
```
