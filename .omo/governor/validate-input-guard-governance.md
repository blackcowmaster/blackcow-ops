# Governance Decision: validate-input-guard

| Field | Value |
|---|---|
| **Task** | Add input validation guards to all validate-*.sh scripts in skills/tests/ |
| **Governed at** | 2026-06-20T18:00:00Z |
| **Detected Intent** | Security — Defense in depth / input validation hardening |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | STANDARD | Cross-cutting change touching 9+ shell scripts with varying target-file patterns. Straightforward pattern but requires per-script adaptation — not trivially batchable. |
| **Trust Level** | L2 | Human should review consistency across scripts. Pattern is mechanical but wrong guard could break existing test harness. |
| **Bootstrap Lanes** | 3 | One per script category: (A) unit test scripts, (B) contract/integration scripts, (C) ecosystem meta-scripts |
| **PDCA Max Cycles** | 3 | 1 cycle for guard addition, 1 for ecosystem-health update, 1 for verification |
| **Adversarial Reviewers** | 3 | M-size task — 3 reviewers for contract/integration scripts |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal |
| M2 test-pass | ✅ | Universal |
| M3 regression | ✅ | Universal |
| M4 lint | ✅ | Shell scripts in diff |
| M5 dead-code | ❌ | No deletions in diff (additive change) |
| S1 dataFlow | ❌ | No type/schema files in diff |
| S2 auth | ❌ | No auth/route files in diff |
| S3 injection | ❌ | No handler/input files in diff — the guard being added IS the injection defense |
| P1 query | ❌ | No DB/repository files in diff |
| P2 memory | ❌ | No collection/buffer files in diff |
| P3 latency | ❌ | No p95_target_ms in plan |

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | O2 |
| **Max Capability** | O4 |
| **Browser Available?** | NO — shell scripts, no browser needed |
| **Capped?** | O4 → O2 (no browser tooling available; O2 = verify via shell execution of modified scripts) |
| **Fallback Strategy** | Run modified scripts with missing target files to verify guards fire correctly; run with valid targets to verify no regression |
| **Residual Risk** | Minimal — shell `[[ -f ]]` test is deterministic; risk is in edge-case paths (symlinks, permissions) |

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
| Budget near limit | 80% of max cycles | ESCALATE |
| Scope creep | D2 flags scope change | Return to planner |

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| _none_ | _none_ | _no prior failures in this area_ | _N/A_ | _N/A_ | _N/A_ |

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (discovery)** | ~8K |
| **Tokens (TDD + PDCA)** | ~12K |
| **Tokens (QA)** | ~5K |
| **Total estimated** | ~25K |
| **Est. cost (flash)** | ~$0.003 |
| **Est. cost (pro)** | ~$0.08 |
| **Est. cost (blended)** | ~$0.04 |
| **Historical ROI** | N/A (new task area) |
| **Budget utilization** | 5% of STANDARD mode budget |
| **Recommendation** | PROCEED |

---

## Preflight Audit Summary

### Scripts Audited (10 total)

| # | Script | Target Variable | Current Guard? | Pattern |
|---|---|---|---|---|
| 1 | `validate-blackcow-plan.sh` | `TARGET` (from $1 or default) | ❌ None | Unit test; runs grep/YAML on TARGET |
| 2 | `validate-blackcow-governor.sh` | `TARGET` (from $1 or default) | ❌ None | Unit test; runs grep/YAML on TARGET |
| 3 | `validate-blackcow-plan-contract.sh` | `SKILL_FILE` (hardcoded) | ⚠️ Partial | Checks as test assertion, doesn't exit early |
| 4 | `validate-blackcow-governor-contract.sh` | `SKILL_FILE` (hardcoded) | ⚠️ Partial | Checks as test assertion, doesn't exit early |
| 5 | `validate-blackcow-plan-integration.sh` | `PLAN_FILE` (from SKILL_DIR) | ❌ None | Integration; no existence check before grep |
| 6 | `validate-blackcow-governor-integration.sh` | `GOVERNOR_FILE` (from SKILL_DIR) | ❌ None | Integration; no existence check before grep |
| 7 | `validate-blackcow-governor-system.sh` | `GOVERNOR_FILE` (from SKILLS_DIR) | ❌ None | System test; no existence check |
| 8 | `validate-cross-skill-contract.sh` | Multiple (GOVERNOR_FILE, PLAN_FILE, etc.) | ❌ None | Uses assert_file_exists as test assertion only |
| 9 | `validate-blackcow-ecosystem.sh` | ALL_SKILLS array | ⚠️ Partial | Checks in loop but doesn't exit early |
| 10 | `validate-blackcow-ecosystem-health.sh` | (runner — invokes others) | N/A | Runner; handles sub-script exit codes |

### Key Finding
Zero scripts have a **pre-flight input validation guard** that checks target file existence and exits with a clear error message before running expensive test logic. Scripts #3, #4, and #9 check existence as *test assertions* but continue running all remaining assertions after a "file not found" — producing cascading, confusing failure output.

---

## Standardized Guard Pattern

Every validate-*.sh script will add this block immediately after the `set -euo pipefail` and variable-initialization section, before any test logic:

```bash
# --- Input Validation: target file must exist ---
if [[ ! -f "$TARGET_FILE" ]]; then
  echo "ERROR: Target file not found: $TARGET_FILE" >&2
  echo "Usage: $0 [<path-to-file>]" >&2
  echo "Default: <default-path>" >&2
  exit 1
fi
```

### Per-Script Adaptation Table

| Script | Variable | Default Path | Accepts Arg? |
|---|---|---|---|
| `validate-blackcow-plan.sh` | `$TARGET` | `$PROJECT_ROOT/skills/blackcow-plan.md` | Yes ($1) |
| `validate-blackcow-governor.sh` | `$TARGET` | `$PROJECT_ROOT/skills/blackcow-governor.md` | Yes ($1) |
| `validate-blackcow-plan-contract.sh` | `$SKILL_FILE` | `skills/blackcow-plan.md` | No |
| `validate-blackcow-governor-contract.sh` | `$SKILL_FILE` | `skills/blackcow-governor.md` | No |
| `validate-blackcow-plan-integration.sh` | `$PLAN_FILE` | `${SKILL_DIR}/blackcow-plan.md` | No |
| `validate-blackcow-governor-integration.sh` | `$GOVERNOR_FILE` | `${SKILL_DIR}/blackcow-governor.md` | No |
| `validate-blackcow-governor-system.sh` | `$GOVERNOR_FILE` | `${SKILLS_DIR}/blackcow-governor.md` | No |
| `validate-cross-skill-contract.sh` | `$GOVERNOR_FILE` (primary); `$PLAN_FILE`, `$LOOP_FILE`, `$QA_FILE`, `$LIBRARIAN_FILE` | `${SKILLS_DIR}/blackcow-governor.md` (primary) | No |
| `validate-blackcow-ecosystem.sh` | `ALL_SKILLS` array (7 files) | `skills/blackcow-*.md` | No |

### Special Cases

**validate-cross-skill-contract.sh**: Has 5 target files. The primary target is `$GOVERNOR_FILE` (the contract table source). Guard all 5 files — if ANY is missing, print which ones and exit. The contract validation is meaningless if any referenced skill file is absent.

**validate-blackcow-ecosystem.sh**: Already iterates ALL_SKILLS and checks existence via `assert_file_exists`. Enhancement: add an early-exit guard — if ≥2 skill files are missing, print a summary and exit before running the full test suite. A single missing file should still run remaining checks (ecosystem can be partially healthy).

**validate-blackcow-ecosystem-health.sh** (runner): Update to add a new check that verifies each validate-*.sh script has the input validation guard pattern. This becomes a meta-check in the ecosystem health report.

---

## Ecosystem Health Script Update

Add a new check to `validate-blackcow-ecosystem-health.sh` that greps each child validate-*.sh for the guard pattern. This ensures the input validation pattern remains enforceable as new validate scripts are added.

```bash
# New check: Input Validation Guard Presence
# Verify each validate-*.sh has the file-exists guard
INPUT_GUARD_PATTERN='if \[\[ ! -f "\$[A-Z_]*" \]\]; then'
```

This check should be added as a pre-run validation step (before executing sub-scripts), or as a separate check row in the health report.

## Post-Governance Self-Audit

After pipeline completes, verify:
- [ ] All 9 non-runner scripts have the guard block
- [ ] Guard uses correct variable name for each script
- [ ] Guard error message goes to stderr (`>&2`)
- [ ] Guard exits with code 1
- [ ] ecosystem-health.sh has the new meta-check
- [ ] Existing tests still pass with valid target files (no regression)
- [ ] Missing-target test: `bash validate-blackcow-plan.sh /nonexistent/path.md` exits 1 with clear error
- [ ] Missing-target test: `bash validate-blackcow-governor-contract.sh` exits 1 if `skills/blackcow-governor.md` is temporarily renamed
