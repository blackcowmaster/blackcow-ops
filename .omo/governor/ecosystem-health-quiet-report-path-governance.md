# Governance Decision: ecosystem-health-quiet-report-path

| Field | Value |
|---|---|
| **Task** | Fix: --quiet mode suppresses "Text report written to:" line in validate-blackcow-ecosystem-health.sh |
| **Governed at** | 2026-06-27 |
| **Detected Intent** | Bug |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | FAST | Single-file, single-line bug fix with clear root cause. ~2 lines changed. No new features. |
| **Trust Level** | L2 | Well-understood codebase; fix is mechanical (replace log_info suppression with explicit JSON guard). |
| **Bootstrap Lanes** | 1 | Single fix path |
| **PDCA Max Cycles** | 1 | Trivial fix |
| **Adversarial Reviewers** | 0 | XS task |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal |
| M2 test-pass | ✅ | Universal |
| M3 regression | ✅ | Universal |
| M4 lint | ✅ | Shell script in diff |
| M5 dead-code | ❌ | No deletions |
| S1 dataFlow | ❌ | No type/schema changes |
| S2 auth | ❌ | No auth changes |
| S3 injection | ❌ | No input-handling changes |
| P1 query | ❌ | No DB changes |
| P2 memory | ❌ | No collection changes |
| P3 latency | ❌ | No p95 target |

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | O1 |
| **Max Capability** | O2 (capabilities.json) |
| **Browser Available?** | NO |
| **Capped?** | O2 → O1 (no browser; shell-only verification sufficient) |
| **Fallback Strategy** | Run script with --quiet flag, verify text report path appears in output |
| **Residual Risk** | None — fix is mechanical and reversible |

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| Stage 1 | uncertainty_score < 30 | 1 |
| Stage 2 | 30 ≤ uncertainty < 60 | 3 |
| Stage 3 | uncertainty ≥ 60 | 5 |

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| No new evidence | 1 cycle with Δ=0 | ESCALATE to user |
| Same gate ×2 | Same gate fails twice | ESCALATE to user |
| Budget near limit | N/A (FAST mode, 1 cycle) | — |

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| — | — | No matching patterns | — | — | — |

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (discovery)** | ~3K |
| **Tokens (TDD + PDCA)** | ~2K |
| **Tokens (QA)** | ~3K |
| **Total estimated** | ~8K |
| **Est. cost (flash)** | ~$0.002 |
| **Est. cost (pro)** | ~$0.12 |
| **Est. cost (blended)** | ~$0.06 |
| **Historical ROI** | 0.78-0.92 (range from loop-roi.jsonl) |
| **Recommendation** | PROCEED |

## Root Cause Analysis

The file has two output paths:

1. **`--summary` block** (line ~379): Uses direct `echo "  Text report written to: $HEALTH_LOG"` — always visible except in JSON mode (stdout redirect to /dev/null). ✅ CORRECT.

2. **Normal path** (line ~519-520): Uses `log_info "Text report written to: $HEALTH_LOG"` which calls `_quiet_or_summary()` → suppresses when `$QUIET` is true. ❌ BUG.

**Fix**: In the normal path, replace `log_info` suppression with explicit `$JSON_OUT` guard:
```bash
# Before:
  $QUIET || echo ""
  log_info "Text report written to: $HEALTH_LOG"

# After:
  $JSON_OUT || echo ""
  $JSON_OUT || echo "  Text report written to: $HEALTH_LOG"
```

This ensures the text report path is shown in all modes (normal, verbose, quiet, summary) and suppressed ONLY in `--json` mode.
