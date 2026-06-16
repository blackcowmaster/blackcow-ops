# Governance Decision: simple-app-prd

| Field | Value |
|---|---|
| **Task** | PRD for a simple app: (A) email/password auth, (B) profile settings page, (C) persistent dark-mode toggle |
| **Governed at** | 2025-07-19T12:00:00Z |
| **Detected Intent** | Feature — greenfield planning/decomposition, three independent units, no tech stack specified |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | **STANDARD** | Planning-only pipeline with FAN-OUT parallel dispatch. Not FAST (real decomposition work required across 3 units). Not FULL (no implementation, no adversarial review needed). |
| **Trust Level** | **L3** (Auto) | No code mutations; only markdown plans produced. Zero risk to existing codebase. |
| **Bootstrap Lanes** | **3** | One per independent feature unit — FAN-OUT parallel dispatch per user directive |
| **PDCA Max Cycles** | **0** | No implementation — plan artifacts are the terminal output. PDCA loop not reached. |
| **Adversarial Reviewers** | **0** | No code to review; plans reviewed via M1 spec-match only |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal — PRD completeness check (all 3 units decomposed) |
| M2 test-pass | ❌ DEFERRED | No implementation; deferred to implementation phase |
| M3 regression | ❌ DEFERRED | No existing codebase to regress; deferred to implementation phase |
| M4 lint | ❌ N/A | No source code produced |
| M5 dead-code | ❌ N/A | No source code produced |
| S1 dataFlow | ❌ N/A | No data flow to validate (tech stack not specified) |
| S2 auth | ❌ N/A | No auth implementation |
| S3 injection | ❌ N/A | No handlers/inputs |
| P1 query | ❌ N/A | No database queries |
| P2 memory | ❌ N/A | No memory-sensitive code |
| P3 latency | ❌ N/A | No latency targets |

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | **O0** (text-only verification) |
| **Max Capability** | O4 (Playwright screenshots available) |
| **Browser Available?** | YES |
| **Capped?** | O4 → O0 (planning-only — no UI artifact to observe) |
| **Fallback Strategy** | M1 spec-match via checklist enumeration of decomposed units |
| **Residual Risk** | Low — PRD decomposition correctness is the only quality dimension |

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| Stage 1 | N/A (planning-only) | 3 (initial FAN-OUT) |
| Stage 2 | N/A | N/A |
| Stage 3 | N/A | N/A |

**Note:** Widening policy not activated for planning-only pipelines. Each unit gets exactly 1 lane in FAN-OUT dispatch.

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| Plan missing sub-features | Any unit plan lacks decomposition | Return to planner for that unit only |
| Cross-unit conflict | Dependencies emerge between parallel units | Collapse conflicting units, re-dispatch sequentially |

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| — | — | No patterns match task area `greenfield-feature-planning` | — | — | Clean run |

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (discovery)** | ~4K |
| **Tokens (planning ×3 FAN-OUT)** | ~12K (3 × ~4K per unit plan) |
| **Tokens (QA — M1 only)** | ~2K |
| **Total estimated** | ~18K |
| **Est. cost (blended)** | ~$0.02 |
| **Historical ROI** | 0.78 score/token (feature work category) |
| **Budget utilization** | ~18% of STANDARD mode budget (~100K) |
| **Recommendation** | **PROCEED** |

## FAN-OUT Dispatch Plan

Three independent units, dispatched in parallel:

| Lane | Unit | Plan Slug | Dependency |
|---|---|---|---|
| A | User authentication (email/password) | `simple-app-auth` | None |
| B | Profile settings page | `simple-app-profile` | None |
| C | Dark mode toggle (persistent) | `simple-app-darkmode` | None |

**Parallelism rationale:** All three features are explicitly independent per the PRD. No shared state, no cross-unit API contracts, no ordering constraints. Each can be planned in isolation without waiting for any other.

## Post-Governance Self-Audit

After pipeline completes, verify:

- [ ] All 3 plan files written to `plans/simple-app-*.md`
- [ ] Each plan contains decomposition into sub-features
- [ ] No cross-unit coupling detected (independence assertion holds)
- [ ] M1 spec-match: 3/3 units have plans
- [ ] Governance decision loaded by downstream skills via `--govern=simple-app-prd`
