# BKIT — The 11-Gate Quality Taxonomy

> Adapted and extended from [BKIT by POPUP STUDIO](https://github.com/popup-studio-ai/bkit-claude-code) (Apache 2.0).
> Original taxonomy: M1-M10 + S1. BlackCow reorganizes into M1-M5 (Implementation), S1-S3 (Security), P1-P3 (Performance).

## Overview

BKIT (Build Kit) is a quality taxonomy that structures every agent execution through **11 numbered gates**. Each gate has:

- A **numeric threshold** — pass/fail is measurable, not subjective
- A **dedicated audit subagent** — one agent owns one gate
- **Verifiable evidence** — every gate result is captured to a file

BlackCow's version adds a **3-category structure** and **numerous Reasonix-native thresholds** that were absent in the original taxonomy.

## M-Gates: Implementation Quality

| Gate | Name | Threshold | Audit Agent | Description |
| --- | --- | --- | --- | --- |
| **M1** | spec-match | ≥ 90% | QA_M1 | Code matches the plan specification. Every MUST requirement has file:line evidence. |
| **M2** | test-pass | 100% pass, coverage ≥ 80% | QA_M2 / VERIFY_M2 | All tests pass with no failures. Coverage meets threshold. |
| **M3** | regression | 0 new failures | QA_M3 / VERIFY_M3 | No existing functionality broken. Call sites preserved. Baseline tests still pass. |
| **M4** | lint-clean | 0 warnings | QA_M4 / VERIFY_M4 | Linter reports zero warnings. Format is consistent. |
| **M5** | dead-code | 0 unreferenced exports | QA_M5 / CLEANUP_M5 | No unused functions, classes, types, or imports left behind. |

## S-Gates: Security

| Gate | Name | Threshold | Audit Agent | Description |
| --- | --- | --- | --- | --- |
| **S1** | dataFlow integrity | ≥ 85% | QA_S1 / GATE_S1 | Data shapes don't change format between layers. No lossy transforms. Null safety maintained. |
| **S2** | auth coverage | 100% entry points guarded | QA_S2 / GATE_S2 | Every HTTP handler, CLI command, and entry point has auth middleware/guard. |
| **S3** | injection surface | 0 unhandled surfaces | QA_S3 / GATE_S3 | No eval(), raw SQL concatenation, innerHTML injection, or command injection. |

**Enhanced by BlackCow**: S-gate findings with CRITICAL/HIGH severity are escalated to **Red Team PoC engineers** who attempt working exploits. False positives are downgraded; confirmed exploits are escalated.

## P-Gates: Performance

| Gate | Name | Threshold | Audit Agent | Description |
| --- | --- | --- | --- | --- |
| **P1** | query efficiency | 0 N+1 patterns | QA_P1 / GATE_P1 | No N+1 queries. All database operations have limits/pagination. |
| **P2** | memory bounds | all collections bounded | QA_P2 / GATE_P2 | No unbounded arrays, maps, recursion, or buffers. Pagination where applicable. |
| **P3** | latency | p95 < target | QA_P3 / GATE_P3 | 95th percentile latency meets the plan's target. No sync blocking in async contexts. |

## How Gates Are Evaluated

### In blackcow-loop
```
Phase 1: TDD + Hashline → M2 (test-pass) checked inline
Phase 2: Gap Detection → M1 (spec-match) measured
Phase 3: Verification → M2, M3, M4 checked as 3 parallel subagents
Phase 5: Adversarial QA → All 8 gates dispatched as parallel subagents
  - S1, S2, S3, M1: model=pro (analytical)
  - P1, P2, P3, M5: model=budget (mechanical)
  - PoC_S3, PoC_S1S2: model=pro (exploit engineering)
Phase 6: Cleanup → M5 dead code removed, M4 lint auto-fixed (3 parallel)
```

### In blackcow-qa (standalone)
```
Phase 1: All 11 gates dispatched as ONE parallel batch
  - M1, S1, S2, S3, P3: model=pro
  - M2, M3, M4, M5, P1, P2: model=budget
```

## Gate Coverage by Skill

| Skill | M1 | M2 | M3 | M4 | M5 | S1 | S2 | S3 | P1 | P2 | P3 | Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **blackcow-plan** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 11/11 (plan covers these) |
| **blackcow-loop** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 11/11 (actively checked) |
| **blackcow-qa** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 11/11 (evaluates all) |
| **blackcow-skill-review** | — | — | — | — | — | — | — | — | — | — | — | N/A (audits skill files, not code) |
| **blackcow-skill-evolver** | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | — | — | — | — | — | 1/11 (edits markdown, limited applicability) |
| **blackcow-librarian** | ✅ | — | ✅ | — | ✅ | ✅ | — | — | — | ✅ | ✅ | 6/11 (caching + data integrity) |

## PDCA Iterator

When `gap-detector` finds `matchRate < 90%` (M1 spec-match failure):

1. **D1 Root Cause Diagnosis** — Why do gaps exist? File:line fixes.
2. **D2 Fastest Fix Path** — Minimal changes to reach ≥ 90%.

Up to 7 PDCA cycles (DeepSeek-optimized from BKIT's original 5). Adaptive ceiling: if success rate >95% for 3 consecutive runs, cycles auto-reduce.

## Trust Level Impact on Gates

| Trust Level | Max PDCA Cycles | Auto-Fix | Auto-Commit | Gate Strictness |
| --- | --- | --- | --- | --- |
| L0 Manual | 0 | Never | Never | Full manual review |
| L1 Assisted | 1 | 1 cycle | Never | All gates checked |
| L2 Semi-Auto | 3 | 3 cycles | After all gates | Default |
| L3 Auto-Review | 7 | 7 cycles | After M1-M5+S1-S3 | Full + load test |
| L4 Full-Auto | 7 | 7 cycles | Auto | Full + load + resume |

## Comparison with Original BKIT

| Aspect | Original BKIT (POPUP STUDIO) | BlackCow BKIT |
| --- | --- | --- |
| **Gate structure** | M1-M10 + S1 (11 gates, mixed domains) | M1-M5 + S1-S3 + P1-P3 (11 gates, 3 categories) |
| **Platform** | Claude Code plugin | Reasonix skill files |
| **Audit mechanism** | Single gap-detector | 8-11 parallel subagents per gate |
| **PDCA cycles** | Max 5 | Max 7 (DeepSeek-optimized) |
| **Red Team** | Not included | PoC exploit engineers |
| **Evidence format** | Reports | JSONL + structured snapshots + trend analysis |
| **Cost model** | GPT-5 (~$0.50+/cycle) | DeepSeek (~$0.005/cycle) |
