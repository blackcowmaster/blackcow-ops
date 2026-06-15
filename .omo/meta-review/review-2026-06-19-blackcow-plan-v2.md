# Meta-Review: blackcow-plan

| Field | Value |
|---|---|
| **Reviewed** | 2026-06-19T10:30:00Z |
| **Reviewer** | blackcow-skill-review (Metis 大将) |
| **Skill Version** | 2.0.0 (declared `updated: 2026-06-19`, mtime 2026-06-15T00:14:43Z) |
| **Skill Type** | PLANNER — produces decision-complete plans; never edits product code |
| **File** | `skills/blackcow-plan.md` (35,928 bytes, ~830 lines) |

## Overall Score

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| R1 Syntax & Structure | 78 | 15% | 11.7 |
| R2 Gate Completeness | 65 | 30% | 19.5 |
| R3 Parallelism Efficiency | 60 | 25% | 15.0 |
| R4 Cost Efficiency | 55 | 15% | 8.3 |
| R5 Staleness/Freshness | 80 | 15% | 12.0 |
| **TOTAL** | — | **100%** | **66.5** |

> **Trend**: 63.0 → 64.0 → 72.8 → **66.5**. The drop from 72.8 reflects deeper adversarial scrutiny (R6 findings integrated) and discovery of the invalid model name `deepseek-v4-lite` which undermines cost-tier routing. Prior reviews averaged R2 gate scores of 72-74; the 100% lane score was rejected as over-generous after cross-reference with R6 adversarial findings.

---

## Dimension Details

### R1: Syntax & Structure — 78/100

**Strengths**: Valid YAML frontmatter, consistent heading hierarchy (H1→H2→H3), well-formed markdown tables, no broken cross-references (all 6 sibling skills exist), clear phase labeling, all lane prompts have RETURN EXACTLY with numbered output schemas, Phase -1 IntentGate present and functional.

**Issues Found**:

| # | File:Line | Issue | Severity |
|---|---|---|---|
| 1 | L1 (frontmatter) | `allowed-tools` uses kebab-case — platform install API uses camelCase `allowedTools`. May fail parsing on some frontmatter readers. | MED |
| 2 | ~190-386 (all L1-L10 prompts), 587-707 (all reviewer prompts) | 23 code blocks lack language markers (bare ``` instead of ```text). All contain NL prompts so severity is LOW, but consistency would improve with `text` markers. | LOW |
| 3 | 185 | `task()` pseudo-code used throughout instead of platform-native `explore()`. The adaptation note at L177 documents the mapping (`task` → `explore`, `description` → `task`), but readers must mentally translate ~20 dispatch blocks. | MED |
| 4 | 217 | XL dispatch block has no code block of its own — only prose note "same as M, but all lanes use model=pro." Should have explicit dispatch block showing `model=pro` on every lane. | MED |
| 5 | 587-592 | Phase 4 reviewer dispatch block hardcodes all 5 reviewers unconditionally. Text at L583 and L595-600 correctly says "M = 3 reviewers, XL = 5 reviewers," but the dispatch code doesn't show the M-scale (3-reviewer) variant. A planner following literally would dispatch 5 for M-scale. | MED |
| 6 | 587-707 | Reviewer prompts use "RETURN:" instead of "RETURN EXACTLY:" — inconsistent with lane prompt convention (all L1-L10 use "RETURN EXACTLY:"). | LOW |
| 7 | 23 | `## Mode Detection` is a level-2 heading at same rank as phases but with no phase prefix. Minor structural inconsistency. | LOW |

---

### R2: Gate Completeness — 65/100

**PLANNER note**: This skill is a PLANNER — it ensures plan templates cover all gates, not that gates are enforced at plan-generation time. Scoring reflects **plan-template coverage**, not runtime enforcement. However, the adversarial review (R6) identified several structural weaknesses that prior reviews missed.

#### Gate Coverage Matrix

| Gate | Status | Evidence | Weakness |
|---|---|---|---|
| **M1** spec-match | ✅ COVERED | `matchRate ≥ 90%` in Context Anchor SUCCESS (L445); Gap Matrix row; Risk Register row; RVA reviewer covers M1 | None |
| **M2** test-pass | ✅ COVERED | `test pass=100%` in SUCCESS; L4 gathers CI command; Risk Register row; RVA covers M2 | None |
| **M3** regression | ✅ COVERED | Gap Matrix `🔧 Modify → M3`; Risk Register row "0 regressions"; RVA covers backward-compat | SUCCESS anchor absent (not in completion promise) |
| **M4** lint-clean | ✅ COVERED | `lint=0warn` in SUCCESS; Risk Register row "0 warnings"; RVA covers linting | None |
| **M5** dead-code | ⚠️ WEAK | Gap Matrix has `🗑️ Delete → M5`; Risk Register row exists | **No data-collection lane maps to M5** — no lane searches for dead exports/unused code. Risk Register row is a placeholder enforced by nothing. R6 correctly identifies this as name-dropping, not coverage. |
| **S1** dataFlow | ✅ COVERED | L3 returns TRANSFORMATION MAP with BKIT S1 tag; L8 returns S1=dataFlow findings; RVB checks dataFlow integrity | Intentional cross-validation between L3 and L8 |
| **S2** auth | ✅ COVERED | L8 checks auth middleware; Risk Register row; RVB checks auth weakening | None |
| **S3** injection | ✅ COVERED | L8 audits injection surfaces (SQL concat, eval, dynamic code); Risk Register row; RVB checks injection surfaces | None |
| **P1** query | ⚠️ WEAK | L9 checks N+1 patterns; Risk Register row | **SUCCESS anchor absent** — only P3 (p95_target_ms) appears in completion promise. P1 threshold defined only in Risk Register, unreachable by `--completion-promise` |
| **P2** memory | ⚠️ WEAK | L9 checks unbounded growth; Risk Register row | Same SUCCESS gap as P1 |
| **P3** latency | ✅ COVERED | `p95_target_ms` in SUCCESS; L9 gathers latency data; Risk Register row | None |

#### Critical Gate Findings (from R6 adversarial cross-reference)

| # | Finding | File:Line | Severity |
|---|---|---|---|
| **G1** | **Reviewer B+ ghost**: Security intent routing (L91) says "add Reviewer B+" — but only Reviewers A–E exist (L588-592). No Reviewer B+ dispatch block, prompt, or definition exists. For security-critical intent, the plan promises a reviewer that doesn't exist. | L91 | **CRITICAL** |
| **G2** | **M5 dead-code has zero collection lanes**: Gap Matrix tags Delete items as M5, Risk Register has a row, but no Phase 1 lane gathers data on dead exports. The gate is template-only — it will always appear "clean" because no data feeds into it. | L566 (Risk Register), L190-386 (all lanes) | **HIGH** |
| **G3** | **3 of 10 lanes produce zero gate-tagged output**: L6 (Dependency Audit), L7 (Git Archaeology), and L10 (Pattern Library) return findings with no BKIT gate tags. 30% of Phase 1 capacity produces untagged intelligence that never feeds into any gate enforcement. | L286-421 (L6, L7, L10 prompts) | **HIGH** |
| **G4** | **IntentGate routing is documentation-only**: The Intent Routing table (L89-103) lists lane adjustments per intent class, but Phase 1 dispatch blocks (L190-209) are hardcoded — they never branch on intent class. The planner must manually remember to apply routing. | L89-103 vs L190-209 | **HIGH** |
| **G5** | **SUCCESS enforces only 4/11 gates**: Context Anchor SUCCESS criteria (L445) covers M1, M2, M4, P3 only. M3, M5, S1, S2, S3, P1, P2 exist only in the Risk Register. The downstream `--completion-promise` derives from SUCCESS, making 7/11 gates invisible to the executor. | L445 vs L558-578 (Risk Register) | **HIGH** |

---

### R3: Parallelism Efficiency — 60/100

**Core batch-fire pattern is correct**: Phase 1 dispatches all lanes with `run_in_background=true` in one batch (L173-176: "CRITICAL: Dispatch ALL lanes… NEVER await any single lane"). Phase 4 dispatches all reviewers similarly. The sequential phase ordering (IntentGate → Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5) has genuine data dependencies that justify serialization.

**Issues dragging the score down**:

| # | File:Line | Issue | Severity | Fix |
|---|---|---|---|---|
| **P1** | 109-110 | **Scale Classification table contradicts Phase 4**: Table says M → **1 reviewer**, but Phase 4 (L595-600) says M → **3 reviewers** (A,B,C). XL table says "triple review" but Phase 4 dispatches 5. | **HIGH** | Update table: M → 3 reviewers, XL → 5 reviewers (match Phase 4's correct values) |
| **P2** | 47-57 | **Multi-feature mode serializes independent features**: Step 6 says per-feature plans run "independently" but doesn't specify parallel dispatch. Features with no dependency edges could run Phase 1 concurrently. | **MED** | Add: "Features with empty `depends_on` sets may dispatch their Phase 1 lanes in parallel across features" |
| **P3** | L5 vs L8 | **L5 (Config Matrix) and L8 (Security Surface) overlap on secret scanning**: L5 output 4 scans for plaintext secrets; L8 re-scans the same files for `password|secret|token|api_key` patterns. ~1.5K tokens wasted per invocation. | **MED** | Make L8's secret check consume L5's output instead of re-scanning; or split: L5 covers config-secrets, L8 covers code-secrets |
| **P4** | 425-436 | **Phase 2 labeled "parallel batch" but runs sequentially**: Header says "in ONE parallel batch" but lists 6 sequential grep/read_file verification steps with no subagent dispatch. False labeling. | **LOW** | Either dispatch these as subagents with `run_in_background`, or relabel as "sequential cross-checks" |
| **P5** | 217 | **XL gets 10 lanes — same as M**: For >1000 lines across 6+ files, 10 lanes = same cardinality as Medium. Differentiation is purely model tier (pro vs mixed). Lane count should scale for XL. | **LOW** | Consider XL=12-15 lanes with additional specialized lanes for larger codebases |
| **P6** | 177 | **Platform adaptation note**: `run_in_background` and `max_steps` described as "budget hints, not enforced." If the host platform actually serializes `explore()` calls, the entire parallelism model collapses. This is a platform-dependency risk, not a skill bug. | **INFO** | Document expected platform capabilities in Constraints section |

---

### R4: Cost Efficiency — 55/100

**Strengths**: Core budget/pro split is correct — cheap discovery lanes (L1/L4/L5/L7/L10) use budget tier; analytical/security lanes (L2/L3/L6/L8/L9) use pro tier. This saves ~30% vs all-pro. L8 security override hard-coded to pro regardless of `--model-tier`. Intent-based lane skipping saves real tokens (Emergency skips 5 lanes + Phase 4). XS skips Phase 4 entirely. Cache load pre-flight saves ~3K tokens when fresh.

**Issues**:

| # | Finding | File:Line | Severity | Impact |
|---|---|---|---|---|
| **C1** | **`deepseek-v4-lite` is an INVALID model name**: The platform's valid models are `deepseek-v4-flash` and `deepseek-v4-pro`. `deepseek-v4-lite` does not exist. If the platform validates model names at dispatch time, ALL budget-tier lane dispatches will fail. Affects all 6 skill files. | L9, L11, L144 + inline body | **CRITICAL** | Complete cost-tier routing failure |
| **C2** | **3 of 5 model tiers are dead aliases**: `quick` = `budget` (deepseek-v4-lite), `deep` = `pro` (deepseek-v4-pro), `ultrabrain` = `pro` (deepseek-v4-pro). Five advertised tiers, two actual models. 60% of the tiering taxonomy is cosmetic. Flagged across 10+ prior reviews with zero remediation. | L8-14 | **HIGH** | Misleading cost documentation; users picking `--model-tier=ultrabrain` pay pro prices for pro model |
| **C3** | **XL mode wastes money**: Forces ALL 10 lanes to pro tier, but 5 of them (L1/L4/L5/L7/L10) are pure grep/glob/read_file operations that gain zero benefit from pro. Waste: ~$0.0014/invocation (5 lanes × ~4K tokens × $0.07 premium). | L217, L127-130 | **MED** | 33% premium on lane costs with zero quality benefit |
| **C4** | **Token budget underestimates output tokens**: Phase 1 budget estimates 20K-50K input but ignores 3-5K output per lane. Realistic M-scale Phase 1: 80K total (input+output). Adding Phase 3 (25-40K, not claimed 10K), Phase 4 reviewers (25K), and Phase 5 (5K) = **125-135K total**, exceeding the 115K effective budget by 9-17%. Constraint #15 triggers budget split → doubles cost. | L145-148, L827 | **MED** | Plan routinely splits into 2 sequential plans, doubling per-invocation cost |
| **C5** | **L6 web_fetch has no cap**: "For EVERY direct dependency… check latest version (use web_fetch)." A 50-dep project = 50 web_fetch calls × 2-3K response each = 100-150K tokens just for L6. No pagination, limit, or "top N" constraint mentioned. | L325-326 | **HIGH** | Potentially unbounded cost for dependency-heavy projects |
| **C6** | **Multi-feature mode has zero shared context**: Each feature dispatches its own full L1-L10 lane set. If 3 features affect overlapping modules, file scans are repeated 3×. A shared discovery cache across features could save ~30%. | L47-57 | **MED** | Linear cost scaling with N features (no sub-linear optimization) |

#### Estimated Costs

| Mode | Input Tokens | Output Tokens | Total | Estimated Cost |
|---|---|---|---|---|
| **XS** (5 lanes, no reviewers) | ~20,000 | ~15,000 | ~35,000 | ~$0.005 |
| **M single-feature** (10 lanes, 3 reviewers) | ~65,000 | ~55,000 | ~120,000 | ~$0.017 |
| **XL single-feature** (10 lanes all-pro, 5 reviewers) | ~75,000 | ~60,000 | ~135,000 | ~$0.024 |
| **Multi-feature (3 features, M-scale)** | ~195,000 | ~165,000 | ~360,000 | ~$0.051 |

> Note: All budgets exceed the declared 115K effective cap for M/XL single-feature, triggering Constraint #15 split → costs may double.

---

### R5: Staleness/Freshness — 80/100

**Strengths**: File modified today (mtime 2026-06-15), all 6 sibling skills confirmed existing at v2.0.0, BKIT 11-gate taxonomy matches canonical standard, no TODO/FIXME/HACK markers in skill body, all referenced tools valid, all phase sections structurally complete across 830 lines.

**Issues**:

| # | Finding | File:Line | Severity |
|---|---|---|---|
| **S1** | **`deepseek-v4-lite` is an invalid model name** — platform only recognizes `deepseek-v4-flash` and `deepseek-v4-pro`. This is the single most impactful staleness issue; it affects all 6 skill files and could break cost-tier routing at dispatch time. | L9, L11, L144 | **CRITICAL** |
| **S2** | **Frontmatter `updated: 2026-06-19` is 4 days ahead of actual mtime** (2026-06-15). Metadata is misleading — suggests the file was edited in the future or the date is aspirational. | L6 | **MED** |
| **S3** | **`plans/` directory doesn't exist** in project root. Referenced as output destination (L40, 715, 724, 811, 817). Should be auto-created or documented as runtime-generated. | L40, 715 | **LOW** |
| **S4** | **`.omo/library/` doesn't exist** — referenced as librarian cache (L108-111). The skill handles this defensively ("If it exists…"), but the reference suggests infrastructure that isn't present. | L108-111 | **LOW** |

**Version accuracy**: v2.0.0 accurately reflects the current feature set (BKIT 11-gate, Context Anchor, 3 Arch Options, adaptive lane scaling, multi-feature mode, cost-tier routing, DAG, IntentGate, librarian integration). All sibling skills are also at v2.0.0.

**Freshness recommendation**: **Monthly review**. The file is actively maintained, BKIT taxonomy is stable, tool list is current. Primary risk is model name deprecation (already an issue with `deepseek-v4-lite`).

---

## Cross-Reference Contradictions (Phase 1 synthesis)

### Contradiction 1: R2 lane scored 100%, R6 adversarial scored 55%

The R2 lane found all 11 gates present in the template and scored 100%. R6 identified 5 structural weaknesses (Reviewer B+ ghost, M5 zero-collection, 3 untagged lanes, IntentGate documentation-only, SUCCESS covering only 4/11 gates). **Resolution**: Adopt 65 — gates are present in the template architecture but several are structurally unreachable or hollow. The 100% score was over-generous for a planner where gate coverage must be enforceable by the downstream executor.

### Contradiction 2: Scale Classification table (L109) vs Phase 4 (L595)

Scale table says M has 1 reviewer; Phase 4 says M has 3 reviewers. **Resolution**: Phase 4's values are correct (matching the description header "3-5 adversarial reviewers scale-gated"). The table must be updated.

### Contradiction 3: Token budget claims vs realistic estimates

Phase 1 budget claims 20K-50K input; R4 lane estimates 120K total for M-scale single-feature. **Resolution**: The skill's context budget documentation systematically ignores output tokens and underestimates Phase 3 generation cost. Realistic M-scale is 120-135K, exceeding the 115K cap.

---

## Recommendations

### Critical (score < 70 on any dimension, or platform-breaking)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **C1** | `deepseek-v4-lite` invalid model name | L9, L11, L144 + all `model: budget` dispatches | Replace all occurrences of `deepseek-v4-lite` with `deepseek-v4-flash` (the valid platform model). Affects all 6 skill files. | **2 min** (global search-replace) |
| **C2** | Reviewer B+ ghost — Security intent routes to non-existent reviewer | L91 | Either (a) remove "add Reviewer B+" from Security intent row, or (b) create Reviewer B+ prompt block with security-specific audit criteria | **5 min** |
| **C3** | IntentGate routing is documentation-only — dispatch blocks don't branch | L89-103 vs L190-209 | Add conditional dispatch logic: if intent=Emergency → dispatch only L1-L5; if intent=BugFix → skip L9,L10; etc. Or add explicit "apply Intent Routing table before dispatching" instruction at L173. | **15 min** |

### High (score 70-84 on dimension, or structural weakness)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **H1** | M5 dead-code has zero collection lanes | L566 + all Phase 1 lanes | Add dead-code detection to L10 (Pattern Library): search for unused exports, orphaned functions, unreferenced modules. Tag output with BKIT M5. | **10 min** |
| **H2** | 3 of 10 lanes produce no gate-tagged output (L6, L7, L10) | L286-421 | Add BKIT gate tag fields to L6/L7/L10 RETURN EXACTLY schemas. L6 → tag outdated deps as M3 (regression risk); L7 → tag hot files as M3 (regression risk); L10 → tag anti-patterns as M4 (lint) or M5 (dead-code). | **10 min** |
| **H3** | SUCCESS enforces only 4/11 gates (M1,M2,M4,P3) | L445 | Expand Context Anchor SUCCESS to include gates currently only in Risk Register: add `regression=0`, `dead_code=0`, `dataFlow_integrity=pass`, `auth=pass`, `injection=0`, `query_n_plus_1=0`. Note: some values may be "N/A" per feature. | **8 min** |
| **H4** | L6 web_fetch has no cap — unbounded cost for N deps | L325-326 | Add: "Limit to top 10 direct dependencies most relevant to the task. Skip devDependencies unless the task explicitly involves tooling." | **2 min** |
| **H5** | 3 of 5 model tiers are dead aliases | L8-14 | Either (a) remove quick/deep/ultrabrain aliases and simplify to budget/pro, or (b) assign ultrabrain to a genuinely different/more-expensive model. Document the remaining tiers honestly. | **5 min** |

### Medium (score 85-94 on dimension, or efficiency gain)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **M1** | Scale Classification table contradicts Phase 4 reviewer count | L109-110 | Update table: M → "3 reviewers (A,B,C)", XL → "5 reviewers (A-E)" | **1 min** |
| **M2** | Multi-feature mode doesn't specify parallel dispatch for independent features | L47-57 | Add explicit instruction: "Features with empty `depends_on` in the dependency graph may dispatch Phase 1 concurrently. Features sharing a dependency edge must run sequentially." | **5 min** |
| **M3** | L5 and L8 overlap on secret scanning | L152-157 vs L174-185 | Make L8 consume L5's secret findings: L8's secret step reads L5 output instead of re-scanning. Or split: L5 = config-secrets, L8 = code-secrets. | **5 min** |
| **M4** | XL mode forces all-pro on lanes that don't benefit | L217 | Keep budget lanes at budget even in XL: L1/L4/L5/L7/L10 stay budget-tier. XL differentiation is reviewer count (5 vs 3) and pro-tier on analytical lanes, not grep operations. | **2 min** |
| **M5** | Token budget documentation ignores output tokens | L145-148, L827 | Update budget estimates: include output token estimates. Realistic M-scale: ~120K (not 70K). Adjust 115K cap or document that split is expected for M-scale. | **5 min** |
| **M6** | 23 code blocks lack language markers | ~30 locations | Add `text` language marker to all bare ``` blocks (single global search-replace). | **1 min** |
| **M7** | Reviewer prompts use "RETURN:" not "RETURN EXACTLY:" | L606, 626, 649, 668, 689 | Replace "RETURN:" with "RETURN EXACTLY:" in all 5 reviewer prompt blocks. | **1 min** |

### Low (cosmetic or edge-case)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **L1** | Frontmatter `updated` date is 4 days ahead of mtime | L6 | Set `updated: 2026-06-15` to match actual mtime, or update the file so mtime matches. | **1 min** |
| **L2** | `plans/` and `.omo/library/` directories don't exist | L40, 108-111 | Add note: "Created at runtime if absent" or add `mkdir -p plans/ .omo/library/` to Phase 0 pre-flight. | **1 min** |
| **L3** | Phase 2 labeled "parallel batch" but runs sequentially | L425-436 | Rename: "in ONE sequential pass" or dispatch as subagents. | **1 min** |
| **L4** | XL dispatch block missing explicit code block | L217 | Add explicit dispatch block showing `model=pro` on every lane. | **2 min** |
| **L5** | `## Mode Detection` heading not phase-prefixed | L23 | Rename to `## Phase -2 — Mode Detection` or nest under `## Overview`. | **1 min** |

---

## Evolution Readiness

- **Safe to auto-evolve?**: **PARTIALLY** — 10 of 17 recommendations are safe for automated application (C1 model name fix, M1 table fix, M6 language markers, M7 RETURN→RETURN EXACTLY, L1 date fix, L2 directory note, L3 relabel, L4 dispatch block, L5 heading rename, H4 web_fetch cap). The remaining 7 recommendations (C2 Reviewer B+, C3 IntentGate dispatch branching, H1 M5 lane, H2 gate tags on L6/L7/L10, H3 SUCCESS expansion, H5 tier cleanup, M2 multi-feature parallelism, M3 L5/L8 dedup, M4 XL tier routing, M5 budget docs) involve structural changes to lane prompts or dispatch logic and should be reviewed before applying.
- **Backup recommended before**: Phase 0 (scale classification table), Phase 1 (lane prompts L6/L7/L10), Phase -1 (IntentGate routing), Phase 3 (Context Anchor SUCCESS), Phase 4 (reviewer dispatch), frontmatter (model tiers)
- **Estimated evolution tokens**: ~18K for the 7 structural changes; ~2K for the 10 safe changes. Total: ~20K.
