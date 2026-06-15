# Governance Decision: ecosystem-health-parallel

| Field | Value |
|---|---|
| **Task** | Add parallel execution support to `skills/tests/validate-blackcow-ecosystem-health.sh` with configurable concurrency limit, output ordering preservation, and `--parallel` flag |
| **Governed at** | 2026-06-21T00:00:00Z |
| **Detected Intent** | Performance — pure runtime optimization; no functional change to validation logic |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | STANDARD | Single-file change but with non-trivial shell concurrency concerns: semaphore patterns, temp-file output capture, ordered merge, SIGINT handling. User explicitly notes "inherently iterative — expect PDCA cycles." Not trivially batchable. |
| **Trust Level** | L2 | Shell concurrency is error-prone. Background-process management, race conditions on shared state, and signal propagation all require human review before production gate. |
| **Bootstrap Lanes** | 3 | (A) Core parallel execution engine + semaphore, (B) Output capture + ordered merge, (C) Edge cases: SIGINT cleanup, timeout interaction, --parallel flag validation |
| **PDCA Max Cycles** | 4 | Shell concurrency bugs are typically found in PDCA; budget 4 cycles to cover semaphore starvation, zombie processes, output ordering drift, and signal handling |
| **Adversarial Reviewers** | 3 | XS→S task (1 file, additive ≈150 lines). 3 reviewers cover: shell correctness, concurrency safety, output fidelity |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal — verify --parallel flag, concurrency limit, output ordering, background processes |
| M2 test-pass | ✅ | Universal — run with --parallel, verify all 10 scripts complete, same pass/fail counts |
| M3 regression | ✅ | Universal — sequential mode (no --parallel) must produce identical output to before |
| M4 lint | ✅ | Shell script modified — `bash -n` must pass; check for common bash concurrency anti-patterns (missing `wait`, unquoted vars in subshells) |
| M5 dead-code | ❌ | No deletions expected in diff (additive change: parallel path added alongside sequential) |
| S1 dataFlow | ❌ | No type/schema files changed |
| S2 auth | ❌ | No auth/route files changed |
| S3 injection | ❌ | No handler/input files changed — script already handles sub-script invocation securely |
| P1 query | ❌ | No DB/repository files changed |
| P2 memory | ❌ | No collection/buffer files changed |
| P3 latency | ❌ | No p95_target_ms in plan — though latency improvement IS the task goal, P3 applies to product code latency, not test harness runtime |

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | O2 |
| **Max Capability** | O2 (no capabilities.json found; shell execution + text diff available; no browser) |
| **Browser Available?** | NO |
| **Capped?** | O2 (natural cap — no runtime visualization needed for shell script verification) |
| **Fallback Strategy** | Run script with `--parallel` and `--verbose`; diff output vs `--quiet` sequential run; verify pass/fail/skip counts match; verify wall-clock time reduction |
| **Residual Risk** | Low-Medium. Shell background-process patterns are well-understood but platform-dependent: `wait -n` requires bash ≥4.3; `flock` may not be available; mktemp must be available. Risk: script may behave differently on macOS (BSD userland) vs Linux (GNU). |

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| Stage 1 | uncertainty_score < 30 | 3 |
| Stage 2 | 30 ≤ uncertainty < 60 | 7 |
| Stage 3 | uncertainty ≥ 60 | 10 |

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| No new evidence | 1 cycle with Δ=0 | Re-dispatch D1 (pro) → plan re-eval → user |
| Same gate ×2 | Same gate fails twice | ESCALATE to user |
| Budget near limit | 80% of max cycles (cycle ≥ 3) | ESCALATE |
| Scope creep | D2 flags non-health.sh file touched | Return to planner |
| Zombie processes | Background process count > concurrency limit after completion | ESCALATE with process listing |
| Output mismatch | Parallel output pass/fail totals ≠ sequential totals | ESCALATE to user with diff |

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| _none_ | _none_ | No failure-patterns.jsonl found; no prior failures in this area | _N/A_ | _N/A_ | _N/A_ |

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (discovery)** | ~6K (read target + 2 sample scripts + memory/qa files + REASONIX) |
| **Tokens (TDD + PDCA)** | ~18K (4 cycles × ~4.5K: implement → test → fix → retest for concurrency bugs) |
| **Tokens (QA)** | ~6K (4-gate evaluation: M1 spec, M2 test-pass, M3 regression diff, M4 bash -n) |
| **Total estimated** | ~30K |
| **Est. cost (flash)** | ~$0.004 |
| **Est. cost (pro)** | ~$0.09 |
| **Est. cost (blended)** | ~$0.05 |
| **Historical ROI** | N/A (no loop-roi.jsonl; first task in this area) |
| **Budget utilization** | 6% of STANDARD mode budget |
| **Recommendation** | PROCEED |

---

## Preflight Architecture Notes

### Current Execution Model (Sequential)

```
for script_path in "${SCRIPTS[@]}"; do
    local_output=$(bash "$script_path" 2>&1) || local_exit=$?
    parse_counts "$local_output"
    # ... accumulate into arrays
done
```

**Bottleneck:** 10 scripts × ~2-10s each = 20-100s wall-clock. Scripts are independent — no data dependencies between iterations except output parsing which is post-hoc.

### Target Parallel Architecture

```
# Semaphore pattern with configurable concurrency
MAX_JOBS=4  # or --parallel N
RUNNING=0

for script_path in "${SCRIPTS[@]}"; do
    # Wait if at capacity
    while [[ $RUNNING -ge $MAX_JOBS ]]; do
        wait -n
        RUNNING=$((RUNNING - 1))
    done

    # Launch in background, capture output to temp file
    tmpfile=$(mktemp)
    (
        bash "$script_path" >"$tmpfile" 2>&1
        echo $? >"${tmpfile}.exit"
    ) &
    RUNNING=$((RUNNING + 1))
    # Store tmpfile → script_name mapping for ordered output
done

# Drain remaining
wait
```

### Key Design Decisions (to be resolved in plan)

1. **Semaphore mechanism:** `wait -n` (bash ≥4.3) vs `jobs -p | wc -l` polling. Prefer `wait -n` for efficiency; fallback to polling if bash <4.3 detected.

2. **Output capture:** Per-script temp files vs named pipes vs process substitution. Temp files are simplest and most portable.

3. **Output ordering:** Store results indexed by script position, then iterate in original order to print. This guarantees output ordering matches sequential even if scripts finish out of order.

4. **Signal handling:** `trap` for SIGINT/SIGTERM to kill background children. Without this, Ctrl-C leaves zombie bash processes.

5. **Timeout interaction:** Current 120s per-script timeout (unused variable). Parallel execution should still respect per-script timeouts via `timeout` command or `( sleep $TIMEOUT; kill $$ ) &` pattern.

6. **JSON output:** Must aggregate results identically to sequential mode.

### Race Condition Risks

| Risk | Mitigation |
|---|---|
| Two scripts writing to same temp file | Use `mktemp` with unique names per script |
| `$RUNNING` counter decrement race | Only the main process touches `$RUNNING` — all decrements happen in the `wait -n` loop |
| Sub-script uses same temp file names internally | Each sub-script gets its own `TMPDIR` or unique prefix |
| `wait -n` returns before temp file is fully written | Temp file write + exit code write are atomic within the subshell; `wait -n` returns only after subshell exit |
| JSON output written concurrently | All aggregation happens in the main process after all background jobs complete |

### Platform Considerations

| Feature | Linux (GNU) | macOS (BSD) | Notes |
|---|---|---|---|
| `mktemp` | Yes | Yes | Slight flag differences; use `mktemp /tmp/eco-health.XXXXXX` (BSD-compatible) |
| `wait -n` | bash ≥4.3 | bash ≥4.3 | macOS ships bash 3.2; user may have Homebrew bash 5.x. Detect and fall back to polling. |
| `flock` | Yes | No (alternative: `shlock`) | Avoid flock; use `mkdir` as mutex if needed |
| `timeout` | GNU coreutils | No (use `gtimeout` from coreutils) | Use `{ sleep $sec; kill $$; } &` pattern instead — more portable |
| `/dev/shm` | Yes | No | Don't use; stick to `$TMPDIR` or `/tmp` |

**Recommendation:** Target bash ≥4.0 with `wait -n` as primary path, polling fallback for bash 3.x. Add bash version detection at script startup.

---

## Self-Audit Checklist

- [ ] Mode selection matches task scale (STANDARD for single-file with concurrency complexity)
- [ ] Gate selection based on actual change surface (shell script, additive, no deletions)
- [ ] Observable level is achievable (O2 via shell execution + diff)
- [ ] Failure-pattern feed loaded from memory (none found — honest)
- [ ] Loop ROI history consulted (none found — honest)
- [ ] Escalation rules defined with concrete actions including concurrency-specific triggers
- [ ] Governance document written to `.omo/governor/ecosystem-health-parallel-governance.md`
- [ ] No invented diff signals or failure patterns
- [ ] Mode escalation justified by evidence (STANDARD, not FAST: concurrency has real edge cases)
- [ ] Platform portability risks documented (bash version, macOS vs Linux)
- [ ] Race condition risks enumerated with mitigations
- [ ] All downstream skills (plan/loop/qa) can honor governance decisions
