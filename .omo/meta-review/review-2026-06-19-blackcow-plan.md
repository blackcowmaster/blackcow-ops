# Meta-Review: blackcow-plan

| Field | Value |
|---|---|
| **Reviewed** | 2026-06-19T08:15:00Z |
| **Reviewer** | blackcow-skill-review (Metis 大将) |
| **Skill Version** | 2.0.0 (declared `updated: 2026-06-12`, mtime 2026-06-14T23:59:12Z) |
| **Skill Type** | PLANNER — produces decision-complete plans; never edits product code |

## Overall Score

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| R1 Syntax & Structure | 84 | 15% | 12.6 |
| R2 Gate Completeness | 74 | 30% | 22.2 |
| R3 Parallelism Efficiency | 66 | 25% | 16.5 |
| R4 Cost Efficiency | 65 | 15% | 9.8 |
| R5 Staleness/Freshness | 78 | 15% | 11.7 |
| **TOTAL** | — | **100%** | **72.8** |

## Dimension Details

### R1: Syntax & Structure — 84/100

**Strengths**: Valid YAML frontmatter, consistent heading hierarchy (H1→H2→H3), well-formed markdown tables, no broken cross-references (all 6 referenced skills exist), clear phase labeling, file is complete at 830 lines (35,888 bytes).

**Issues Found**:

| # | File:Line | Issue | Severity |
|---|---|---|---|
| 1 | ~190-386 (all L1-L10 prompts), 587-707 (all RVA-RVE prompts) | Code blocks lack language markers (bare ``` instead of ```text or ```markdown) | LOW |
| 2 | ~185 | `task()` pseudo-code used throughout instead of platform-native `explore()`. Platform adaptation note documents the mapping, but readers must mentally translate ~20 dispatch blocks. | MED |
| 3 | 587-707 | Reviewer prompts use "RETURN:" instead of "RETURN EXACTLY:" (deviates from lane prompt convention) | LOW |
| 4 | 719-730 vs 734-813 | Two near-identical plan template blocks (redundant but not broken) | LOW |
| 5 | ~244-386 | Lane prompts merge context+action into single paragraph; no explicit section headers (content is present, just not sectioned) | LOW |
| 6 | 14 | `web_search` in allowed-tools but no lane prompt documents its use case | LOW |

### R2: Gate Completeness — 74/100

**Key finding**: This is a **PLANNER** skill. Per the meta-review skill's own rubric, planners should ensure the PLAN covers all gates — not that the planner executes gate enforcement at plan-generation time. R2 scoring must measure **plan-template coverage**, not runtime enforcement.

**Gate Coverage Matrix**:

| Gate | Status | Justification |
|---|---|---|
| **M1** spec-match | ✅ COVERED | `matchRate ≥ 90%` in Context Anchor SUCCESS; Gap Matrix row; Risk Register row |
| **M2** test-pass | ✅ COVERED | `test pass=100%` in SUCCESS; L4 gathers CI command; Risk Register row |
| **M3** regression | ✅ COVERED | Gap Matrix `🔧 Modify → M3`; Risk Register row "0 regressions" |
| **M4** lint-clean | ✅ COVERED | `lint=0warn` in SUCCESS; Risk Register row "0 warnings" |
| **M5** dead-code | ⚠️ TEMPLATE-ONLY | Gap Matrix has `🗑️ Delete → M5`; Risk Register row exists. But no data-collection lane maps to M5 (no lane searches for dead exports) |
| **S1** dataFlow | ✅ COVERED | L3 returns TRANSFORMATION MAP with BKIT S1 tag; L8 returns S1=dataFlow; RVB checks dataFlow |
| **S2** auth | ✅ COVERED | L8 checks auth middleware; Risk Register row; Plan template maps Config→S2 |
| **S3** injection | ✅ COVERED | L8 audits injection surfaces (`eval`, SQL concat); Risk Register row |
| **P1** query | ⚠️ WEAK | L9 checks N+1 patterns; Risk Register row. But SUCCESS anchor absent (p95_target_ms covers P3 only). Adversarial review composite, not gate-specific |
| **P2** memory | ⚠️ WEAK | L9 checks unbounded growth; Risk Register row. Same SUCCESS gap as P1 |
| **P3** latency | ✅ COVERED | `p95_target_ms` in SUCCESS; L9 gathers latency data; Risk Register row |

**CRITICAL findings — IntentGate drops gates**:

The Phase -1 Intent Routing table (lines 89-103) skips lanes for specific intents:
- **Performance intent**: Skips L8 (Security) → S1/S2/S3 data-collection REMOVED. Skips RVB (Security reviewer) → no adversarial S-gate review.
- **Quality intent**: Skips L8+L9 → all S+P gates data-collection REMOVED.
- **Emergency intent**: Only L1-L5 run → M5 + all S/P gates data-collection REMOVED. Phase 4 cancelled entirely.
- **Bug Fix intent**: Skips L9+L10 → P-gates data-collection REMOVED.

Additionally, the **Intent Routing table is documentation-only** — Phase 1 dispatch blocks (lines 175-207) are unconditionally static and never branch on intent class. The routing mechanism is **not wired**.

Furthermore, the **Context Anchor SUCCESS criteria enforce only 4/11 gates** (M1, M2, M4, P3). M3, M5, S1, S2, S3, P1, P2 exist in the Risk Register but are absent from the plan's execution contract.

**Score rationale**: 74 reflects strong template coverage (all 11 gates appear in Risk Register) but penalizes heavily for: (a) IntentGate drops S+P gates for 4/6 intent classes, (b) routing not wired to dispatch, (c) SUCCESS enforces only 36% of gates.

### R3: Parallelism Efficiency — 66/100

**Strengths**: Phase 1 dispatches all 10 lanes in one batch with correct platform adaptation. Phase 4 dispatches all reviewers in parallel. Adaptive lane count (XS=5, M=10, XL=10) is well-designed.

**Issues Found**:

| # | File:Line | Issue | Severity |
|---|---|---|---|
| 1 | 47 | Phase -1 IntentGate is serial BEFORE Phase 0. Could run in parallel with Phase 0.0 Cache Load (zero data dependency). | MED |
| 2 | 425-436 | Phase 2 header says "run these in ONE parallel batch" but lists 6 sequential inline grep/read_file operations — no subagent dispatches. Misleading labeling. | MED |
| 3 | 468-554 | Phase 3 (Design) is a serial waterfall: 3a→3b→3c→3d→3e. Each sub-phase depends on the previous. User waits through all 5 sequentially. | MED |
| 4 | 39-41 | Multi-feature mode writes per-feature plans sequentially. After the dependency graph is built, per-feature Phase 1-5 pipelines are independent and could dispatch in parallel across features. | MED |
| 5 | 212 vs 597 | XL description says "triple adversarial review" at line 212 but Phase 4 table at line 597 says XL uses 5 reviewers (A,B,C,D,E). Contradiction. | LOW |
| 6 | 232-252 vs 258-282 | L1 (Surface Topology) and L2 (Call Graph) both trace entry→exit paths. ~40% of L1 effort and ~30% of L2 effort produce redundant diagrams. Intentional cross-validation, but documented overlap. | LOW |

**Score rationale**: 66 reflects real Phase 1/4 parallelism offset by serial Phase -1 bottleneck, misleading Phase 2 label, serial Phase 3 waterfall, and missed multi-feature parallelization opportunity.

### R4: Cost Efficiency — 65/100

**Strengths**: Lane-tier routing is well-justified — budget for I/O-bound lanes (L1/L4/L5/L7/L10), pro for analysis lanes (L2/L3/L6/L8/L9). L8 (Security) and all reviewers forced to pro regardless of `--model-tier`. XS scale skips Phase 4 entirely (correct cost trade-off). Estimated ~$0.015 per M-scale invocation is negligible.

**Issues Found**:

| # | Finding | Detail | Severity |
|---|---|---|---|
| 1 | Dead model tiers | `quick`, `deep`, `ultrabrain` defined in frontmatter but never dispatched in any lane. `ultrabrain` has one consumer (blackcow-skill-review R6) but blackcow-plan never invokes it. Flagged across 10+ prior meta-reviews with zero remediation. | MED |
| 2 | Token estimates optimistic | Skill claims Phase 1 M-scale = "10 lanes × ~5K = ~50K" but ignores OUTPUT tokens (3-5K per lane). Realistic M-scale: 10 lanes × (5K input + 4K output) = ~90K from Phase 1 alone. Total invocation ≈ 120-125K, exceeding declared 115K effective budget. | MED |
| 3 | XS not as cheap as advertised | Constraint 15 says "XS:5 lanes × ~20K" — but that's 100K for Phase 1 alone, not the ~40K total claimed. For trivial tasks, 5 explore subagents is overkill. | MED |
| 4 | L6 web_fetch unbounded | "check latest version (use web_fetch on the package registry)" for EVERY direct dependency. No cap specified. 50-dependency project = 50 web_fetch calls. | LOW |
| 5 | Phase 4 marginal value unclear | XL's 5 pro-tier reviewers cost ~40K tokens but their output scores go unused — written and forgotten. | LOW |

**Token Estimate for M-Scale**: ~68.5K input + ~51K output = ~120K total across all threads. Cost ≈ $0.015 (50% budget, 50% pro split).

### R5: Staleness/Freshness — 78/100

**Strengths**: File modified ~5 days ago (mtime 2026-06-14). All 6 referenced skills exist with consistent sizes. BKIT 11-gate taxonomy consistent across files. Active development evident from 4 git commits + uncommitted working-copy fixes. No TODO/FIXME/HACK markers in file body.

**Issues Found**:

| # | Finding | Detail | Severity |
|---|---|---|---|
| 1 | Declared `updated: 2026-06-12` vs mtime `2026-06-14` | 2-day gap. File was edited after declared update date without bumping the field. | MED |
| 2 | DAG example references creating already-existing skills | Phase 3d DAG example (lines ~500-550): task-C creates `blackcow-skill-review.md`, task-D creates `blackcow-skill-evolver.md`. These files exist — stale example data from initial authorship. Users who copy this verbatim would overwrite existing files. | HIGH |
| 3 | `web_search` in allowed-tools but undocumented | Listed at line 14, no lane prompt documents its use. L6 uses `web_fetch` directly. | LOW |
| 4 | Dead tiers persist across 10+ reviews | `quick`/`deep`/`ultrabrain` aliases flagged repeatedly without remediation — process failure, not staleness. | MED |

**Freshness Recommendation**: **Weekly** review while under active development. Downgrade to monthly once working-copy changes are committed.

## Cross-Reference Escalations

| # | Contradiction | Severity | Detail |
|---|---|---|---|
| E1 | **IntentGate creates S-gate coverage black hole** | **CRITICAL** | R2 claimed 100% gate coverage but R3 found Performance/Quality/Emergency intents skip L8 (Security) + RVB (Security reviewer). S1/S2/S3 data-collection entirely removed for 4/6 intent classes. The Intent Routing table is **documentation-only** — Phase 1 dispatch blocks are unconditionally static and never branch on intent. |
| E2 | **SUCCESS enforces only 4/11 gates** | **HIGH** | Context Anchor SUCCESS has thresholds for M1, M2, M4, P3 only. M3, M5, S1-S3, P1-P2 are in Risk Register but absent from the execution contract. Downstream executor (blackcow-loop) can't gate on them. |
| E3 | **XS and Emergency get zero reviewer validation** | **HIGH** | R2 assumed adversarial review covers all gates, but Phase 4 is cancelled for XS and Emergency. Reviewer count is internally inconsistent: Scale Classification says M=1 reviewer, Phase 4 dispatch says M=3. |
| E4 | **R2 scoring methodology conflates template vs enforcement** | **HIGH** | R2 subagent scored 100 measuring static template coverage. Cross-reference downgraded to 72-78 applying executor-level criteria to a PLANNER. Honest PLANNER-adjusted score: 74 (template coverage strong, but 3 gates template-only, IntentGate conditional gaps real). |

## Recommendations

### Critical (score < 70 equivalent impact)
| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| C1 | IntentGate drops S-gates for Performance/Quality/Emergency intents | 89-103 | Add residual security scan even when L8 skipped (e.g., lightweight grep for `eval(`, `password`, `secret` in target files via a budget subagent). Or document that these intents accept reduced gate coverage with explicit user confirmation. | MED |
| C2 | Intent Routing table not wired to dispatch | 89-103 vs 175-207 | Either: (a) add conditional dispatch logic that reads intent class and skips lanes per routing table, or (b) remove the routing table and document that all lanes always run regardless of intent. Current state is false documentation. | HIGH |

### High (score 70-84)
| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| H1 | DAG example references creating already-existing skill files | ~500-550 | Replace example with a non-self-referential scenario (e.g., feature development tasks) and add caveat: "This is an illustrative example — adjust to your project." | LOW |
| H2 | Context Anchor SUCCESS enforces only 4/11 gates | 418-424 | Add explicit thresholds for M3 (0 regressions), M5 (0 unused exports), S1 (integrity ≥ 85%), S2 (all entry points protected), S3 (all inputs validated), P1 (no N+1), P2 (pagination present) to the SUCCESS template. | LOW |
| H3 | XS/Emergency lack any adversarial review | 133, 597 | For Emergency: add 1 fast-track reviewer (budget tier, max 5 steps) that checks only CRITICAL gates. For XS: consider 1 lightweight reviewer. | MED |

### Medium (score 85-94 equivalent)
| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| M1 | Dead model tiers (`quick`, `deep`, `ultrabrain`) flagged 10+ times | 11-13 | Remove `quick` and `deep` aliases (zero consumers). Keep `ultrabrain` only if documented as reserved for adversarial review in other skills. | LOW |
| M2 | mtime/updated field mismatch | 3, file mtime | Bump `updated:` to `2026-06-14` or commit changes and align dates. | TRIVIAL |
| M3 | Token budget estimates ignore output tokens | 155-175 | Revise estimate to include output: M-scale Phase 1 ≈ 90K (not 50K). Add explicit note that total invocation may hit 120-125K. | LOW |
| M4 | Phase 2 labeled "parallel batch" but runs sequentially | 425-436 | Relabel to "Sequential Verification Checklist" or dispatch 2-3 parallel explore subagents for independent grep/read_file checks. | LOW |
| M5 | Phase -1 IntentGate serial before Phase 0 | 47, 100-120 | Restructure: run Phase -1 IntentGate AND Phase 0.0 Cache Load in parallel (zero data dependency). Both feed into Phase 0.1. | LOW |

### Low
| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| L1 | Code blocks lack language markers | ~190-386, 587-707 | Add `text` or `markdown` language markers to all bare ``` blocks. | TRIVIAL |
| L2 | Reviewer prompts use "RETURN:" not "RETURN EXACTLY:" | 587-707 | Standardize to "RETURN EXACTLY:" for consistency with lane prompts. | TRIVIAL |
| L3 | `web_search` in allowed-tools, undocumented use case | 14 | Either remove from allowed-tools or document use case in L6 or a new lane. | TRIVIAL |
| L4 | XL "triple" vs "5" reviewer count inconsistency | 212 vs 597 | Change line 212 "triple adversarial review" to "quintuple adversarial review." | TRIVIAL |
| L5 | L1/L2 produce redundant entry→exit diagrams | 232-282 | Have L1 produce file-level topology only; have L2 produce call-level chain; drop L1's redundant ENTRY→EXIT flow or mark as derived from L2. | LOW |
| L6 | Multi-feature per-feature plans generated sequentially | 39-41 | Dispatch per-feature Phase 1-5 pipelines in parallel after master plan + DAG are built. | MED |

## Evolution Readiness

- **Safe to auto-evolve?**: **YES, with guardrails** — 6 of 17 recommendations are TRIVIAL/LOW effort. Critical finding C2 (wiring Intent Routing) requires manual design decision first.
- **Backup recommended before**: Phase -1 IntentGate section (lines 47-108), Phase 1 dispatch protocol (lines 175-207), Phase 3d DAG example (lines 500-550), Phase 3e Risk Register + Context Anchor SUCCESS (lines 418-424, 558-588).
- **Estimated evolution tokens**: ~35-45K for full remediation of all HIGH+MED findings.
- **Quick wins (safe to auto-apply)**: L1 (language markers), L2 (RETURN→RETURN EXACTLY), L3 (web_search), L4 (triple→quintuple), M2 (bump updated date), M1 (remove dead tiers).
