# Governance Decision: ecosystem-health-json-flag

| Field | Value |
|---|---|
| **Task** | Wire the already-parsed `--json` flag to suppress text output and emit a specified JSON schema to stdout |
| **Governed at** | 2026-06-21T06:00:00Z |
| **Detected Intent** | Quality / Feature — add machine-readable output contract; `--json` flag exists but is dead code |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | FAST | Single-file, purely additive, flag already parsed, schema precisely specified, no concurrency, no PDCA expected. The change is: (a) gate all `echo`/`printf`/`log_*`/`header` calls on `! $JSON_OUT`, (b) build and emit JSON to stdout at end, (c) compute `elapsed_s`. |
| **Trust Level** | L3 | Shell scripting but straightforward: conditional output suppression + JSON construction. The existing Python-based JSON writer proves the data structures are already correct. |
| **Bootstrap Lanes** | 1 | Single change path: (A) output gating + JSON emission. No parallel lanes needed for FAST mode. |
| **PDCA Max Cycles** | 1 | FAST mode — implement, run ecosystem-health to verify, done. If M1/M2/M3 fail, escalate to user immediately (no budget for iterative PDCA). |
| **Adversarial Reviewers** | 0 | FAST mode — no adversarial review needed for additive output-format change |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal — verify JSON schema fields exactly match spec: `scripts[].{name,pass,fail,skip,score,status}`, `aggregate.{pass,fail,skip,score}`, `traffic_light`, `elapsed_s` |
| M2 test-pass | ✅ | Universal — `bash script.sh --json | python3 -m json.tool` must produce valid JSON; all fields present; `elapsed_s > 0` |
| M3 regression | ✅ | Universal — without `--json`, output must be identical (diff against prior run) |
| M4 lint | ✅ | Shell script modified — `bash -n` must pass |
| M5 dead-code | ❌ | No deletions — additive change only |
| S1 dataFlow | ❌ | No type/schema files |
| S2 auth | ❌ | No auth/route files |
| S3 injection | ❌ | No handler/input files |
| P1 query | ❌ | No DB files |
| P2 memory | ❌ | No collection/buffer files |
| P3 latency | ❌ | No p95_target_ms |

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | O2 |
| **Max Capability** | O2 (no browser, no capabilities.json) |
| **Browser Available?** | NO |
| **Capped?** | O2 (natural cap — shell execution + JSON validation sufficient) |
| **Fallback Strategy** | `python3 -m json.tool` for schema validation; `diff` for regression; `bash -n` for lint |
| **Residual Risk** | Low. JSON construction via `python3 -c` already works in the script. Risk: `python3` not available → JSON emission fails. Mitigation: fall back to bash-native JSON construction (printf with manual escaping). |

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| Stage 1 | uncertainty_score < 30 | 1 |
| Stage 2 | 30 ≤ uncertainty < 60 | N/A (FAST mode caps at 1 cycle) |
| Stage 3 | uncertainty ≥ 60 | N/A |

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| Any gate fails | M1/M2/M3/M4 failure on first cycle | ESCALATE to user — no PDCA budget in FAST mode |
| python3 unavailable | `command -v python3` fails | Fall back to bash-native JSON (printf with escaping) |
| JSON invalid | `python3 -m json.tool` fails | ESCALATE |

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| _none_ | _none_ | No failure-patterns.jsonl; no prior failures in this area | _N/A_ | _N/A_ | _N/A_ |

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (discovery)** | ~4K (read target script + memory files + governance history) |
| **Tokens (TDD + PDCA)** | ~3K (single implementation + verify) |
| **Tokens (QA)** | ~4K (4-gate evaluation) |
| **Total estimated** | ~11K |
| **Est. cost (flash)** | ~$0.001 |
| **Est. cost (pro)** | ~$0.03 |
| **Est. cost (blended)** | ~$0.02 |
| **Historical ROI** | N/A (no loop-roi.jsonl) |
| **Budget utilization** | 2% of FAST mode budget |
| **Recommendation** | PROCEED |

---

## Preflight Implementation Notes

### Current State

The `--json` flag is parsed at line 43:
```bash
--json)    JSON_OUT=true ;;
```

But `JSON_OUT` is never referenced again. The script always:
1. Outputs text headers, per-script logs, tables, traffic light (stdout)
2. Writes file-based JSON to `.omo/governor/ecosystem-health-report.json` (file)

### Required Changes

**1. Gate all stdout output on `! $JSON_OUT`**

Every `echo`, `printf`, `log_info`, `log_ok`, `log_warn`, `log_err`, `header` call must be wrapped:
```bash
$JSON_OUT || echo "..."
$JSON_OUT || log_info "..."
$JSON_OUT || header "..."
```

Alternatively, redefine the helper functions:
```bash
if $JSON_OUT; then
  log_info() { :; }
  log_ok()   { :; }
  log_warn() { :; }
  log_err()  { :; }
  header()   { :; }
fi
```

This is cleaner — redefine once, no per-call gating needed. The `echo` and `printf` calls for the table output still need individual gating (or early-return after JSON emission).

**2. Compute `elapsed_s`**

Add before the main loop:
```bash
EPOCH_START=$(date +%s)
```

At JSON emission time:
```bash
EPOCH_END=$(date +%s)
ELAPSED_S=$((EPOCH_END - EPOCH_START))
```

**3. Build and emit JSON to stdout**

When `$JSON_OUT` is true, after all scripts complete and aggregates are computed, emit JSON and exit. The existing Python JSON writer (lines ~480-520) builds a different schema — the new stdout JSON must match the specified schema exactly.

**Specified schema:**
```json
{
  "scripts": [
    {"name": "...", "pass": N, "fail": N, "skip": N, "score": N, "status": "PASS|FAIL"}
  ],
  "aggregate": {"pass": N, "fail": N, "skip": N, "score": N},
  "traffic_light": "GREEN|YELLOW|RED",
  "elapsed_s": N
}
```

**Key differences from existing file JSON:**
- `scripts[]` drops: `total`, `exit_code`, `duration_s`
- `scripts[]` adds: `status` ("PASS" if fail==0, else "FAIL")
- Top-level: replaces `aggregate_score`, `scripts_run`, `scripts_passed`, etc. with `aggregate.{pass,fail,skip,score}` and `elapsed_s`
- `traffic_light` stays at top level (already present in existing JSON)

**4. JSON construction strategy**

Use the existing `python3 -c` pattern (already proven in script). Build the new schema with python3. Fall back to bash-native `printf` if python3 unavailable.

```bash
if $JSON_OUT; then
  EPOCH_END=$(date +%s)
  ELAPSED_S=$((EPOCH_END - EPOCH_START))

  if command -v python3 &>/dev/null; then
    python3 -c "
import json, sys
scripts = []
$(
  for i in "${!SCRIPT_NAMES[@]}"; do
    status="PASS"
    [[ "${SCRIPT_FAIL[$i]}" -gt 0 ]] && status="FAIL"
    echo "scripts.append({"
    echo "    'name': '${SCRIPT_NAMES[$i]}',"
    echo "    'pass': ${SCRIPT_PASS[$i]},"
    echo "    'fail': ${SCRIPT_FAIL[$i]},"
    echo "    'skip': ${SCRIPT_SKIP[$i]},"
    echo "    'score': ${SCRIPT_SCORE[$i]},"
    echo "    'status': '$status'"
    echo "})"
  done
)
report = {
    'scripts': scripts,
    'aggregate': {
        'pass': $OVERALL_PASS,
        'fail': $OVERALL_FAIL,
        'skip': $OVERALL_SKIP,
        'score': $AGGREGATE_SCORE
    },
    'traffic_light': '$TRAFFIC',
    'elapsed_s': $ELAPSED_S
}
json.dump(report, sys.stdout)
print()
"
  else
    # Bash-native fallback
    printf '{'
    printf '"scripts":['
    first=true
    for i in "${!SCRIPT_NAMES[@]}"; do
      $first || printf ','
      first=false
      status="PASS"
      [[ "${SCRIPT_FAIL[$i]}" -gt 0 ]] && status="FAIL"
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
  exit $EXIT_CODE
fi
```

**Note on bash-native fallback:** The bash-native JSON construction is fragile with special characters in script names. Given that script names are `validate-blackcow-*.sh` (no quotes, no backslashes, no unicode), this is safe. If python3 is available (which it typically is), the python path is preferred.

### Output Suppression Strategy

The cleanest approach: redefine output functions when `$JSON_OUT` is true, and place the JSON emission block before all the table/header output (after the main loop completes and aggregates are computed).

The flow:
```
parse args → detect scripts → [JSON: redefine helpers to no-ops] →
run all scripts (log_* calls become no-ops) →
compute aggregates → compute traffic light →
[JSON path]: emit JSON to stdout, exit 0/1/2 →
[text path]: headers, tables, traffic light display (unchanged)
```

This means the JSON emission sits right after the traffic light computation and before the first `header "Per-Script Scores"` call. Clean insertion point.

### Preserve Existing Behavior

- File-based JSON at `$HEALTH_JSON` — KEEP as-is (runs after text output, unchanged)
- Text report at `$HEALTH_LOG` — KEEP as-is
- Exit codes — unchanged (0 GREEN, 1 YELLOW, 2 RED)
- All existing flags (`--verbose`, `--quiet`) — unchanged

### Risk: `--json` + `--verbose` combination

When both `--json` and `--verbose` are passed, `--json` takes precedence (suppress all output, emit JSON only). The `--verbose` flag becomes irrelevant since all output is suppressed. This is the correct behavior — JSON mode is for machine consumers.

---

## Self-Audit Checklist

- [x] Mode selection matches task scale (FAST: single file, additive, flag already exists)
- [x] Gate selection based on actual change surface (shell script, additive, no deletions → M1-M4 only)
- [x] Observable level is achievable (O2 via shell + JSON validation)
- [x] Failure-pattern feed loaded from memory (none found — honest)
- [x] Loop ROI history consulted (none found — honest)
- [x] Escalation rules defined with concrete actions
- [x] Governance document written to `.omo/governor/ecosystem-health-json-flag-governance.md`
- [x] No invented diff signals or failure patterns
- [x] Mode escalation justified by evidence (FAST: flag exists, schema specified, no concurrency)
- [x] All downstream skills (plan/loop/qa) can honor governance decisions
- [x] Implementation strategy documented with insertion points and helper redefinition approach
- [x] JSON schema difference from existing file-based JSON catalogued
- [x] Fallback path defined for missing python3
- [x] `--json` + `--verbose` interaction resolved (JSON wins)
