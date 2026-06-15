# Meta-Review: blackcow-plan v2.0.0

| Field | Value |
|---|---|
| **Reviewed** | 2026-06-17T23:30:00Z |
| **Reviewer** | blackcow-skill-review (Metis 大将) |
| **Skill Version** | 2.0.0 (frontmatter `updated: 2026-06-12`, file mtime 2026-06-14) |
| **Prior Scores** | 66.65 (2025-07-14) → 76.65 (2026-06-14) → 69 (2026-06-16) → 71.5 (2026-06-17) |
| **6-Lane Batch Cost** | ~$0.035 (budget + pro + ultrabrain blend) |
| **Cross-Reference Verdict** | 2 contradictions resolved, 1 escalation |

## Overall Score

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| R1 Syntax & Structure | 78 | 15% | 11.7 |
| R2 Gate Completeness | 78 | 30% | 23.4 |
| R3 Parallelism Efficiency | 65 | 25% | 16.3 |
| R4 Cost Efficiency | 75 | 15% | 11.3 |
| R5 Staleness/Freshness | 55 | 15% | 8.3 |
| **TOTAL** | — | **100%** | **70.9** |

> **Score trajectory**: 66.65 → 76.65 → 69 → 71.5 → **70.9**. The score has converged to a stable range (~69-72). The persistent gap between structural design quality (~78) and operational readiness (~55-65) is the dominant pattern. This skill is architecturally sound but stale and incomplete at the edges.

## Cross-Reference Findings (Phase 2)

### Contradiction #1: R2 Gate Score vs R6 Devil's Advocate
- **R2 assigned**: 100/100 — all 11 gates structurally covered in Risk Register + data-collection lanes
- **R6 proposed**: 58/100 — gates are template-only, zero automation for enforcement, IntentGate routing is documentation-only
- **Resolution**: R2 was measuring **structural coverage** (presence in templates/Risk Register) while R6 was measuring **operational enforcement** (automated checking). Both are valid dimensions. For a PLANNER skill, structural coverage IS the primary requirement — the skill ensures plans document all 11 gates. However, R2's own analysis found P-gates have "less adversarial depth" (single composite check in RVC vs per-gate checks in RVA) and 3 gates (M5, S2, P1-P3 composite) are template-only with no data-collection lane wired. **Final R2 score: 78** — full structural credit but docked for operational gaps discovered internally.
- **Escalation**: R2's GATE_COVERAGE_MATRIX flagged "TEMPLATE-ONLY" for 3 gates but still assigned 100. The matrix is the correct artifact; the 100 score was an overstatement.

### Contradiction #2: M-Scale Reviewer Count (R2 vs R3)
- **Scale Classification table (line ~131)**: M = "Full lanes, 1 reviewer"
- **Phase 4 Reviewer Selection (line ~593)**: M = "A, B, C (3)"
- **Phase 4 dispatch block (lines ~586-590)**: Always shows all 5 `task()` calls, no conditional M-scale variant
- **Resolution**: The Phase 4 table (3 reviewers) is the correct intended behavior per the dispatch context. The Scale Classification table is stale — it says "1 reviewer" from an older version. This is a documentation bug, not a logic bug. R3 correctly identified it; R2 didn't flag it because it checked gate coverage, not reviewer count.
- **Escalation**: HIGH — this inconsistency means M-scale users don't know whether they get 1 or 3 adversarial reviewers.

### Escalation from XR1: Phase 2 "Parallel" Label is Misleading
- Phase 2 header says "ONE parallel batch" but the body lists 6 sequential inline operations (grep, read_file, logic checks) with zero `task()` dispatches.
- Steps 4-6 have hidden data dependencies on steps 1-3 (must wait for grep results).
- This is a documentation issue, not a parallelism bug — the operations ARE sequential but the header falsely claims parallelism.
- **Severity**: MED. Does not affect correctness; misleads readers.

---

## Dimension Details

### R1: Syntax & Structure — 78/100

**Strengths**: Valid YAML frontmatter with all required fields, well-organized phase progression (Phase -1 through Phase 5), consistent H2/H3 heading hierarchy, zero broken cross-skill references (all 5 sibling skills confirmed present), file is complete and not truncated.

**Issues**:

| # | File:Line | Issue | Severity |
|---|---|---|---|
| 1 | ~378-393 | **Nested fenced code block** in L10_PROMPT — inner ` ``` ` closes outer block prematurely, dumping template text into raw markdown. Same issue at ~698-712 in Phase 5 template. | **HIGH** |
| 2 | L1-L10 prompts | **Lane prompts lack 4-section structure** — spec requires context/action/RETURN EXACTLY/format. All lanes embed action in narrative prose with no `**action:**` header, and `format` is absent. Effectively 2-section (narrative + RETURN EXACTLY). | MED |
| 3 | ~568-710 (RVA-RVE) | **Inconsistent RETURN keyword** — reviewer prompts use `RETURN:` while L1-L10 use canonical `RETURN EXACTLY:`. Prior review flagged this; unresolved. | LOW |
| 4 | Multiple (~6 instances) | **Bare code blocks without language markers** — Phase 0 discovery, context budget formula, dispatch blocks, execution command. | LOW |
| 5 | ~191-193 | **XL dispatch incomplete** — L11-L15 described in prose only; no `task()` dispatch code block (unlike XS/M which have full executable blocks). | MED |
| 6 | ~810 | **Constraint #15 typo**: "subagent" used where "subagent" (concept) is intended. Internally consistent, minor. | LOW |

### R2: Gate Completeness — 78/100

**Strengths**: The Risk Register (Phase 3e) provides structural coverage of all 11 BKIT gates with explicit severity, numeric thresholds, mitigations, and verification commands. Data-collection lanes (L3 for S1, L4 for M2, L8 for S1-S3, L9 for P1-P3) feed the gate assessment pipeline. Constraint #6 mandates "every step: concrete verification command + evidence path + BKIT gate tag." Constraint #13 mandates "all quality gates have explicit numeric thresholds."

**Gate Coverage Matrix**:

| Gate | Status | Primary Evidence | Operational Gap |
|---|---|---|---|
| **M1** spec-match | ✅ COVERED | Risk Register + Context Anchor SUCCESS `matchRate ≥ 90%` + Gap Matrix 🆕 Build tag | RVA checks this per-step |
| **M2** test-pass | ✅ COVERED | Risk Register + L4_PROMPT full test landscape + Context Anchor `test pass=100%` | RVA checks this per-step |
| **M3** regression | ✅ COVERED | Risk Register + Gap Matrix 🔧 Modify tag + IntentGate Bug Fix primary | RVA checks this per-step |
| **M4** lint-clean | ✅ COVERED | Risk Register + Context Anchor `lint=0warn` + IntentGate Quality primary | RVA checks this per-step |
| **M5** dead-code | ⚠️ TEMPLATE-ONLY | Risk Register + Gap Matrix 🗑️ Delete row | **No lane hunts for unreferenced exports.** L1 lists exports but never cross-references callers. L2 traces FROM symbols, won't find orphans. |
| **S1** dataFlow | ✅ COVERED | Risk Register + L3_PROMPT S1 tag + L8_PROMPT S1 classification | L3 dispatch references `lsp_*` tools (see R5 staleness) — type extraction may be degraded |
| **S2** auth | ⚠️ TEMPLATE-ONLY | Risk Register + L8_PROMPT auth audit + IntentGate Security forces pro | **`curl → 401` verification not wired into Waves template or any reviewer prompt.** A plan can satisfy every template field without auth protection. |
| **S3** injection | ✅ COVERED | Risk Register + L8_PROMPT injection surface audit | RVB per-step security check covers this |
| **P1** query | ⚠️ WEAK | Risk Register + L9_PROMPT N+1 detection | **Single composite line in RVC_PROMPT.** P-gates get 1/3 the adversarial scrutiny of M-gates. RVA has per-M-gate checks; RVC collapses P1-P3 into one bullet. |
| **P2** memory | ⚠️ WEAK | Risk Register + L9_PROMPT unbounded growth | Same composite collapse as P1 |
| **P3** latency | ⚠️ WEAK | Risk Register + L9_PROMPT + Context Anchor `p95_target_ms` | Same composite collapse as P1 |

**Summary**: 7/11 gates have full operational coverage (M1-M4, S1, S3, plus partial P1-P3). 3 gates (M5, S2) are template-only with no data-collection lane. 3 gates (P1-P3) have data collection but weakened adversarial review.

### R3: Parallelism Efficiency — 65/100

**Strengths**: Correct batch-and-wait pattern for Phase 1 (all 10 lanes dispatched with `run_in_background: true` before any await) and Phase 4 (5 reviewers dispatched simultaneously). Lane independence is genuine — all 10 defined lanes have distinct concerns with intentional cross-check overlap. Lane counts match scale spec for XS (5) and M (10).

**Issues**:

| # | Section | Issue | Severity |
|---|---|---|---|
| 1 | ~191-193 | **XL scale broken** — L11-L15 prompts completely undefined. 5 of 15 lanes (33%) dispatch with no prompt text. **Carried across 4 consecutive reviews without resolution.** | **CRITICAL** |
| 2 | ~404-416 | **Phase 2 "parallel batch" is sequential** — header says "ONE parallel batch" but body lists 6 inline grep/read_file operations with zero `task()` dispatches. Steps 4-6 depend on steps 1-3. | MED |
| 3 | ~131 vs ~593 | **M-scale reviewer count internally inconsistent** — Scale Classification table says "1 reviewer"; Phase 4 Reviewer Selection says "A, B, C (3)". Phase 4 dispatch block always shows all 5, no conditional M-scale variant. | HIGH |
| 4 | ~490 | **Wave tasks not parallel-dispatched** — Waves declare "Tasks within a wave run in parallel" but no `task(…, run_in_background=true)` dispatch code shown. DAG yaml is documentation-only. | MED |
| 5 | — | **11 serial inter-phase gates** — Phase -1→0→1→2→3a→3b→3c→3d→3e→4→5 with zero overlap or pipelining. Architecturally necessary (can't design before surveying), but not acknowledged as a latency constraint. | LOW |

**Lane Count Assessment**:

| Scale | Current | Recommended | Status |
|---|---|---|---|
| XS | 5 (L1-L5) | 5 — keep | ✅ Correct |
| M | 10 (L1-L10) | 10 — keep | ✅ Correct |
| XL | 10 (L1-L10 defined; L11-L15 missing) | 15 — define L11-L15 OR downgrade to 10 | ❌ Broken |

### R4: Cost Efficiency — 75/100

**Strengths**: Model-tier routing is well-designed — budget lanes (L1/L4/L5/L7/L10) correctly assigned to budget tier, pro lanes (L2/L3/L6/L8/L9) correctly assigned to pro tier. Critical override forces L8 and all reviewers to pro regardless of `--model-tier`. `.omo/library` cache integration saves ~3K tokens per invocation. Adaptive lane scaling prevents waste on small tasks. IntentGate-based lane skipping (e.g., Bug Fix skips L9/L10) saves tokens for focused tasks.

**Issue**: The orchestrator (main agent running all phases) consumes ~55% of total cost ($0.0133 of $0.024 for M-scale) despite doing mostly orchestration, verification, and synthesis. This is inherent to the single-subagent architecture — splitting the orchestrator across phases would add complexity exceeding the savings.

**Model-Tier Assignments**:

| Lane/Task | Current Tier | Recommended | Status |
|---|---|---|---|
| L1 Surface Topology | budget | budget | ✅ |
| L2 Call Graph | pro | pro | ✅ |
| L3 Data Shape | pro | pro | ✅ |
| L4 Test Topography | budget | budget | ✅ |
| L5 Config Matrix | budget | budget | ✅ |
| L6 Dependency Audit | pro | pro | ✅ |
| L7 Git Archaeology | budget | budget | ✅ |
| L8 Security Surface | pro (forced) | pro (forced) | ✅ |
| L9 Performance Profile | pro | pro | ✅ |
| L10 Pattern Library | budget | budget | ✅ |
| Phase 4 Reviewers (M: 3) | pro | pro | ✅ |
| Phase 4 Reviewers (XL: 5) | pro | pro | ✅ |

**Token Estimates**:

| Scale | Est. Tokens (in+out) | Est. Cost |
|---|---|---|
| XS | ~47K | ~$0.005 |
| M | ~186K | ~$0.024 |
| XL (if L11-L15 existed) | ~245K | ~$0.031 |

**Consolidation Opportunities**:

| Consolidation | Est. Savings | Risk |
|---|---|---|
| L1 + L10 merge (single Structural Survey lane) | ~$0.0002/M | Low |
| M-scale reviewers 3→2 | ~$0.001/M | Medium — reduces adversarial diversity |
| Phase 2 inline in orchestrator (no separate phase) | Negligible | Low |

### R5: Staleness/Freshness — 55/100

**Age**: File mtime 2026-06-14 (~3 days ago), git HEAD 2026-06-12 (~5 days ago). Frontmatter `updated: 2026-06-12` is stale vs mtime by ~2 days.

**Key Finding**: The file has been touched recently (frequent mtime updates) but **zero of the 15+ recommendations from the 2026-06-14 review have been resolved**. The core defects (XL L11-L15, nested code blocks, reviewer count inconsistency) persist across 4 review cycles. Freshness is cosmetic, not substantive.

**Outdated References**:

| Reference | Location | Expected | Actual | Severity |
|---|---|---|---|---|
| `deepseek-v4-lite` (model_tiers.budget) | line 9 | `deepseek-v4-flash` or valid model | `deepseek-v4-lite` — name not in current provisioning | HIGH |
| `lsp_definition`, `lsp_hover`, `lsp_references` | lines 14, 180 | Valid tools | These tools are NOT available in the current platform | **HIGH** |
| `grep` (legacy tool name) | ~12 occurrences in prompts | `search_content` | `grep` used in lane dispatch tools & prompts | MED |
| `ls` (legacy tool name) | lines 180, 216 | `list_directory` | `ls` used in dispatch tools | MED |
| `bash` (legacy tool name) | lines 180, 322, 329-330 | `run_command` | `bash` used in dispatch tools & prompts | MED |
| `task()` function calls | ~20 occurrences | `explore` / `research` / `run_skill` | `task()` is a DSL concept, not a real tool | MED |
| `run_in_background` parameter | ~20 occurrences | Platform-specific parameter | Not available on all platforms | MED |
| `max_steps` parameter | ~20 occurrences | Platform-specific parameter | Not available on all platforms | MED |
| `.omo/library/` directory | lines 108-112 | Directory should exist | **`.omo/library/` does NOT exist** — cache integration is aspirational | MED |
| `web_search` (allowed-tools) | line 14 | Available tool | Not available in current platform tool list | LOW |
| `updated: 2026-06-12` | line 8 | `2026-06-14` | 2 days stale vs mtime | LOW |
| L11-L15 prompts | ~191-193 | 5 prompts defined | **None exist** | **CRITICAL** |
| M-scale reviewer count | ~131 vs ~593 | Consistent value | "1 reviewer" vs "A, B, C (3)" | MED |

**Incomplete Sections**:

| File:Line | What's Missing | Severity |
|---|---|---|
| ~191-193 | L11_PROMPT through L15_PROMPT entirely undefined | **CRITICAL** |
| ~378-393 | L10_PROMPT template broken by nested code fence | HIGH |
| ~698-712 | Phase 5 template broken by nested code fence | HIGH |
| ~490 | Wave task dispatch — no executable `task()` block | MED |
| ~108-112 | `.omo/library/` cache directory doesn't exist | MED |

**Freshness Recommendation**: **Weekly review** until CRITICAL items resolved (L11-L15, nested code blocks, LSP tool references, model names). Downgrade to **monthly** after fixes. Platform tool/model changes trigger immediate refresh.

---

## Devil's Advocate Audit (R6)

### R2 Challenge: Gate Completeness
- **R2 assigned**: 100/100 (since downgraded to 78 by cross-reference)
- **R6 proposed**: 58/100
- **R6 argument**: IntentGate routing never actually changes lane dispatch — routing table at lines 150-170 is documentation-only. Context Anchor SUCCESS criteria are static boilerplate, not task-derived. Gap Matrix Confidence column is manually populated with no lane-to-gate traceability. Phase -1 priority rule (`Security > Emergency`) produces wrong routing for `--urgent --features=fix-auth` combos (forces XL when emergency demands XS). No gate-enforcement loop — gates are documented but never programmatically checked.
- **Verdict**: PARTIALLY AGREE. R6 is correct that IntentGate routing is not wired into the Phase 1 dispatch protocol — the dispatch code blocks are static regardless of intent. However, the skill IS a planner, not an executor — its job is to ensure the PLAN documents gate coverage, not to enforce gates at plan-generation time. The 78 score (downgraded from 100) correctly captures both structural coverage and operational gaps.

### R3 Challenge: Parallelism
- **R3 assigned**: 72/100 (since downgraded to 65 by cross-reference)
- **R6 proposed**: 55/100
- **R6 argument**: 12 sequential inter-phase stages with zero pipelining. The full critical path is Phase -1→0→1→2→3a→3b→3c→3d→3e→4→5. No overlap. For XL tasks, wall-clock time could exceed subagent budget before Phase 4 starts. The skill acknowledges this nowhere.
- **Verdict**: AGREE that inter-phase serialization is a significant latency driver. However, this is architecturally necessary (you can't design before surveying). The 65 score reflects the intra-phase parallelism being strong while XL scale is broken and M-scale reviewer count is inconsistent. The inter-phase serialization is a design constraint, not a bug.

### R4 Challenge: Cost Efficiency
- **R4 assigned**: 80/100 (since downgraded to 75 by cross-reference)
- **R6 proposed**: 52/100
- **R6 argument**: 10 subagents independently re-discover the codebase (10× duplicated filesystem walks). L6 calls `web_fetch` for every dependency with no cap (50+ HTTP calls). No "quick-scan" mode for trivial changes. Budget split is reactive (run everything, then split) vs proactive.
- **Verdict**: PARTIALLY AGREE. Duplicated subagent work is a real inefficiency, but it's the cost of lane independence — each subagent needs its own context to produce its specific deliverable. The L6 `web_fetch` cap issue is legitimate (no pagination/throttle). The 75 score reasonably reflects the well-designed routing with acknowledged duplication waste.

### Biggest Blind Spot (R6)
> **"All 5 audit lanes assume blackcow-loop will parse and respect the plan's DAG yaml, wave tables, gate thresholds, and evidence paths — but the skill defines no contract or validation between plan-producer and plan-executor. A plan that satisfies every meta-review dimension could be unexecutable if the executor ignores DAG dependencies or lacks verification tools."**

This is a **cross-skill integration risk** that none of the R1-R5 dimensions measure. The skill's elaborate plan structure (DAG yaml, gate tags in Risk Register, verification commands in Wave steps) assumes a compatible executor. No schema validation, no compatibility test, no contract. This should be addressed in a cross-skill integration test (blackcow-plan output → blackcow-loop consumption).

---

## Recommendations

### Critical (score < 70)
| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| 1 | **XL L11-L15 prompts undefined** — 5 of 15 lanes dispatch with empty prompts. 4th consecutive review flagging this. | ~191-193 | Define L11_PROMPT through L15_PROMPT with 4-section structure matching L1-L10, OR reduce XL to 10 lanes + 5 reviewers | Heavy |
| 2 | **Nested fenced code blocks** — L10_PROMPT (~378-393) and Phase 5 template (~698-712) have inner ` ``` ` that break outer fences | ~378, ~698 | Use 4-space indentation for inner templates, or ```` ``` ```` for outer block | Light |
| 3 | **M-scale reviewer count inconsistent** — Scale Classification says "1 reviewer", Phase 4 says "A, B, C (3)" | ~131, ~593 | Unify to 3 reviewers; add conditional M-scale dispatch block showing 3 `task()` calls | Light |

### High (score 70-84)
| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| 4 | **`lsp_definition`, `lsp_hover`, `lsp_references` in allowed-tools** — not available on current platform | lines 14, 180 | Remove from allowed-tools and dispatch, or add conditional platform detection | Light |
| 5 | **`deepseek-v4-lite` model name** — may not exist in current provisioning | line 9 | Update to `deepseek-v4-flash` or valid budget model | Light |
| 6 | **Lane prompts lack 4-section structure** — all L1-L10 prompts embed action in prose, missing `format` section | L1-L10 prompts | Add `**action:**` and `**format:**` headers to each lane prompt | Medium |
| 7 | **Phase 2 "parallel batch" mislabel** — 6 sequential operations, not parallel | ~404-416 | Restructure: sub-phase A (parallel grep×2 + read_file) → sub-phase B (sequential verification) | Medium |
| 8 | **Template-only gates (M5, S2)** — no data-collection lane wired for dead-code detection or auth verification | Risk Register + L1/L2/L8 | Wire M5 into L1 (cross-reference exports vs callers) and S2 into L8 (auth endpoint mapping) | Medium |

### Medium (score 85-94)
| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| 9 | **RVC_PROMPT collapses P1-P3 into single composite check** — P-gates get 1/3 adversarial scrutiny of M-gates | RVC_PROMPT (~648) | Split RVC_PROMPT performance check into per-gate lines: P1 query, P2 memory, P3 latency | Light |
| 10 | **IntentGate routing not wired to dispatch** — routing table is documentation-only; dispatch blocks are static | ~150-170, ~189-207 | Add conditional logic: if Security intent, double-dispatch L8 and skip L9/L10; if Emergency, dispatch only L1-L5 | Heavy |
| 11 | **`.omo/library/` cache path doesn't exist** — cache integration is documented but unimplemented | ~108-112 | Create `.omo/library/` directory and implement cache generation in blackcow-librarian | Medium |
| 12 | **Wave DAG has no executable dispatch** — yaml dependency graph is documentation-only | ~490 | Add `task()` dispatch code block for wave-based execution, matching Phase 1/4 pattern | Medium |
| 13 | **L6 `web_fetch` has no cap** — could make 50+ HTTP calls for large dependency lists | L6_PROMPT | Add: "For projects with >20 deps, sample the 10 most critical (direct deps, >2 major versions behind)" | Light |

### Low (score 95+)
| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| 14 | **RETURN: vs RETURN EXACTLY: inconsistency** — reviewer prompts use `RETURN:`, lanes use `RETURN EXACTLY:` | ~568-710 | Standardize on `RETURN EXACTLY:` across all prompts | Light |
| 15 | **Bare code blocks without language markers** — ~6 instances | Multiple | Add `text`, `json`, or `js` language markers | Light |
| 16 | **11 serial inter-phase stages** — acknowledge in context budget section | ~140-160 | Add note: "Inter-phase serialization adds ~N sec latency; pipelining opportunities exist but are limited by phase dependencies" | Light |
| 17 | **Cross-skill integration contract undefined** — no schema or compatibility test between planner and executor | N/A | Define a plan schema and add cross-skill integration test (blackcow-plan output → blackcow-loop consumption) | Heavy |

---

## Evolution Readiness

- **Safe to auto-evolve?**: **NO** — requires manual review for Critical items (#1, #2, #3)
- **Backup recommended before**: XL dispatch section (~191-193), L10_PROMPT (~378-393), Scale Classification table (~131), Phase 5 template (~698-712)
- **Estimated evolution tokens**: ~25-35K (defining L11-L15 prompts, fixing nested code blocks, unifying reviewer count)
- **Items safe for auto-evolve**: #4, #5, #9, #14, #15, #16 (lightweight fixes)
- **Items requiring manual design**: #1 (L11-L15 requires architectural decisions), #10 (IntentGate wiring requires dispatch restructuring), #17 (cross-skill contract requires blackcow-loop coordination)
