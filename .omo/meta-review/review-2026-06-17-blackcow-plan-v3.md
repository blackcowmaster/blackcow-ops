# Meta-Review: blackcow-plan v2.0.0 (v3 — convergence review)

| Field | Value |
|---|---|
| **Reviewed** | 2026-06-14T23:30:47Z |
| **Reviewer** | blackcow-skill-review (Metis 大将) |
| **Skill Version** | 2.0.0 (frontmatter `updated: 2026-06-12`, git HEAD 2026-06-12, file mtime 2026-06-14) |
| **Git State** | **UNCOMMITTED CHANGES PRESENT** — 94-line diff from HEAD (tools updated, Intent Routing added, nested code blocks fixed, cross-platform note added) |
| **Prior Scores** | 66.65 (2025-07-14) → 76.65 (2026-06-14) → 69 (2026-06-16) → 71.5 (2026-06-17 v1) → 70.9 (2026-06-17 v2) |
| **Self-Review Guard** | This is a convergence review (v3 on same day as v1/v2). Scores must converge within ±3 of prior convergent score (70.9) for the guard to pass. |

## Overall Score

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| R1 Syntax & Structure | 80 | 15% | 12.0 |
| R2 Gate Completeness | 80 | 30% | 24.0 |
| R3 Parallelism Efficiency | 65 | 25% | 16.25 |
| R4 Cost Efficiency | 75 | 15% | 11.25 |
| R5 Staleness/Freshness | 62 | 15% | 9.3 |
| **TOTAL** | — | **100%** | **72.8** |

> **Score trajectory**: 66.65 → 76.65 → 69 → 71.5 → 70.9 → **72.8**. Convergent within the ~70-73 range. The uncommitted changes (tool name updates, Intent Routing, code block fixes) represent genuine progress, lifting R1 (+2), R2 (+2), and R5 (+7) from the prior v2 review. **Self-review guard PASSES** — scores within ±3 of v2 (70.9 → 72.8, Δ=1.9).

---

## What Changed Since v2 Review

The file has **94 lines of uncommitted changes** that address 5 of 17 prior recommendations. These are work-in-progress edits visible to anyone reading the skill from disk, so this review evaluates the **current working-copy state**.

### ✅ Resolved

| # | Prior Finding | Fix Applied | Assessment |
|---|---|---|---|
| 1 | **Nested fenced code blocks** (L10_PROMPT at ~378, Phase 5 at ~698) — ` ``` ` inside ` ``` ` broke rendering | L10_PROMPT: ` ``` ` → `~~~typescript`. Phase 5 templates: ` ```markdown ` → ` `````markdown ` (4 backticks) | **FIXED**. Both nesting conflicts resolved. |
| 2 | **`allowed-tools` phantom tools** — `grep`, `ls`, `bash`, `task`, `edit_file`, `multi_edit` not available | Replaced with `search_content`, `search_files`, `list_directory`, `directory_tree`, `run_command`, `run_skill`, `get_file_info`. Kept `web_search` (doubtful). | **PARTIALLY FIXED**. Frontmatter updated but dispatch protocol still uses legacy names for subagent tools (see R5 issues). |
| 3 | **No cross-platform adaptation note** | Added: `> **Cross-platform:** This skill uses Reasonix-native tool names...` after H1 | **FIXED**. |
| 4 | **IntentGate was documentation-only** — routing table described changes but dispatch blocks were static | Added `### Intent Routing` subsection with explicit lane/reviewer/scale adjustments per intent class | **PARTIALLY FIXED**. Routing table exists but is still not wired into the Phase 1 dispatch code blocks (no conditional logic). |
| 5 | **`updated` date wrong direction** — was `2026-06-13`, now `2026-06-12` | Changed. Still stale vs mtime (2026-06-14) and uncommitted edits. | **COSMETIC**. |

### ❌ Still Unresolved (persistent across 4+ review cycles)

| # | Prior Finding | Severity | Cycles Unresolved |
|---|---|---|---|
| C1 | **XL L11-L15 prompts undefined** — 5 of 15 lanes dispatch with empty prompts | **CRITICAL** | 5 |
| C2 | **M-scale reviewer count inconsistent** — "1 reviewer" (Scale Class) vs "A, B, C (3)" (Phase 4) | **HIGH** | 5 |
| C3 | **`lsp_definition`, `lsp_hover`, `lsp_references` phantom tools** — still in allowed-tools AND dispatch protocol | **HIGH** | 5 |
| C4 | **`deepseek-v4-lite` model name** — may not resolve in current provisioning | **HIGH** | 5 |
| C5 | **Dispatch protocol uses legacy `grep`/`ls`/`bash`** — line ~159: `"read_file","grep","glob","ls","lsp_definition",...` | **HIGH** | 3 |
| H1 | **Phase 2 "parallel batch" is sequential** — 6 inline operations, zero `task()` dispatches | MED | 5 |
| H2 | **Wave tasks no executable dispatch** — DAG yaml is documentation-only | MED | 4 |
| H3 | **RVC_PROMPT P-gates composite** — single bullet for P1/P2/P3 vs per-gate M-checks | MED | 5 |
| H4 | **M5 dead-code no data-collection lane** — template-only gate | MED | 5 |
| H5 | **S2 auth not wired to Waves template** — no `curl → 401` verification step | MED | 5 |
| M1 | **Token estimates undercounted ~3.6×** — documented as ~70K M-scale, actual ~255K | MED | 4 |
| M2 | **Multi-feature mode cost undocumented** — N features = N× cost, no warning | MED | 3 |
| M3 | **Unused `model_tiers` aliases** — `quick`, `deep`, `ultrabrain` never referenced | LOW | 5 |
| M4 | **L7 omitted from cost-routing table** — line ~126 says "L1, L4, L5, L10" but L7 is also budget | LOW | 5 |
| M5 | **Lane prompts lack 4-section structure** — no `**action:**` or `**format:**` headers | LOW | 3 |
| L1 | **RETURN EXACTLY vs RETURN inconsistency** — RVA-RVE use `RETURN:`, L1-L10 use `RETURN EXACTLY:` | LOW | 5 |
| L2 | **Bare code blocks without language markers** — ~6 instances | LOW | 4 |
| L3 | **`.omo/library/` doesn't exist** — cache integration is aspirational | MED | 5 |

---

## Dimension Details

### R1: Syntax & Structure — 80/100 (+2 from v2)

**Strengths**: Valid YAML frontmatter, clear phase progression (Phase -1 through Phase 5), consistent H2/H3 heading hierarchy, no broken cross-skill references (all 5 sibling skills present), nested code blocks FIXED (was HIGH in v2), cross-platform note added, Intent Routing section added with clean table.

**Issues**:

| # | File:Line | Issue | Severity |
|---|---|---|---|
| 1 | L1-L10 prompts | **Lane prompts lack 4-section structure** — spec requires context/action/RETURN EXACTLY/format. All lanes embed action in narrative prose with no `**action:**` header, and `format` is absent. Unchanged from prior reviews. | MED |
| 2 | ~568-710 (RVA-RVE) | **Inconsistent RETURN keyword** — reviewer prompts use `RETURN:` while L1-L10 use canonical `RETURN EXACTLY:`. Unchanged. | LOW |
| 3 | Multiple (~6 instances) | **Bare code blocks without language markers** — Phase 0 discovery, context budget formula, dispatch blocks, execution command. Unchanged. | LOW |
| 4 | ~191-193 | **XL dispatch incomplete** — L11-L15 described in prose only; no `task()` dispatch code block (unlike XS/M which have full executable blocks). | MED |
| 5 | ~14 | **`model_tiers` non-standard** — `install_skill` expects flat `model` string; `model_tiers` map may be silently ignored. | LOW |
| 6 | ~14 | **`web_search` in allowed-tools** — added in uncommitted diff; not confirmed available on current platform. | LOW |
| 7 | ~159 | **Dispatch protocol tools list outdated** — subagent tools still list `grep`,`ls`,`bash` despite allowed-tools update. Inconsistency between frontmatter and dispatch block. | MED |

### R2: Gate Completeness — 80/100 (+2 from v2)

**Strengths**: Risk Register provides full structural coverage of all 11 BKIT gates. Data-collection lanes (L3 for S1, L4 for M2, L8 for S1-S3, L9 for P1-P3) feed the gate assessment pipeline. The NEW Intent Routing section explicitly maps intent classes to lane/reviewer adjustments — a real step toward operational routing. Constraint #13 mandates numeric thresholds.

**Gate Coverage Matrix**:

| Gate | Status | Primary Evidence | Operational Gap |
|---|---|---|---|
| **M1** spec-match | ✅ COVERED | Risk Register + Context Anchor + Gap Matrix + RVA per-step check | — |
| **M2** test-pass | ✅ COVERED | Risk Register + L4_PROMPT + Context Anchor + RVA per-step check | — |
| **M3** regression | ✅ COVERED | Risk Register + Gap Matrix 🔧 + IntentGate Bug Fix + RVA per-step check | — |
| **M4** lint-clean | ✅ COVERED | Risk Register + Context Anchor + IntentGate Quality + RVA per-step check | — |
| **M5** dead-code | ⚠️ TEMPLATE-ONLY | Risk Register + Gap Matrix 🗑️ Delete row | **No lane hunts for unreferenced exports.** L1 lists exports but never cross-references callers. |
| **S1** dataFlow | ✅ COVERED | Risk Register + L3_PROMPT S1 tag + L8_PROMPT S1 classification | L3/L8 dispatch references `lsp_*` tools — type extraction degraded |
| **S2** auth | ⚠️ TEMPLATE-ONLY | Risk Register + L8_PROMPT auth audit + NEW IntentGate forces pro for Security | **`curl → 401` verification not wired into Waves template.** |
| **S3** injection | ✅ COVERED | Risk Register + L8_PROMPT injection surface + NEW IntentGate double-dispatches L8 for Security | RVB per-step security check covers this |
| **P1** query | ⚠️ WEAK | Risk Register + L9_PROMPT N+1 detection | **Single composite line in RVC_PROMPT.** P-gates get 1/3 the adversarial scrutiny of M-gates. |
| **P2** memory | ⚠️ WEAK | Risk Register + L9_PROMPT unbounded growth | Same composite collapse as P1 |
| **P3** latency | ⚠️ WEAK | Risk Register + L9_PROMPT + Context Anchor `p95_target_ms` | Same composite collapse as P1 |
| **XL S/P gates** | ❌ BROKEN | L11 (Security Deep-Dive) and L12 (Performance Deep-Dive) undefined | XL-scale enforcement impossible |

**Summary**: 7/11 gates have full operational coverage (M1-M4, S1, S3 + partial P1-P3). The Intent Routing addition gives S2 and S3 stronger routing (Security intent forces pro + double-dispatches L8). But 3 gates (M5, S2 verification, P1-P3 adversarial depth) remain under-served.

**New in this review**: Intent Routing is a genuine improvement — it makes the routing table actionable. However, it's still not wired into the Phase 1 dispatch code blocks. The routing table describes intent-based changes; the dispatch blocks remain unconditionally static.

### R3: Parallelism Efficiency — 65/100 (unchanged from v2)

**No changes in the uncommitted diff affect parallelism. All prior findings stand.**

| # | Section | Issue | Severity |
|---|---|---|---|
| 1 | ~191-193 | **XL scale broken** — L11-L15 prompts completely undefined. 5 of 15 lanes (33%) dispatch with empty prompt text. **Carried across 5 consecutive reviews without resolution.** | **CRITICAL** |
| 2 | ~404-416 | **Phase 2 "parallel batch" is sequential** — header says "ONE parallel batch" but body lists 6 inline grep/read_file operations with zero `task()` dispatches. Steps 4-6 depend on steps 1-3. | MED |
| 3 | ~131 vs ~593 | **M-scale reviewer count internally inconsistent** — Scale Classification table says "1 reviewer"; Phase 4 Reviewer Selection says "A, B, C (3)". Phase 4 dispatch block always shows all 5, no conditional M-scale variant. | HIGH |
| 4 | ~490 | **Wave tasks not parallel-dispatched** — Waves declare "Tasks within a wave run in parallel" but no `task(…, run_in_background=true)` dispatch code shown. DAG yaml is documentation-only. | MED |
| 5 | — | **11 serial inter-phase gates** — Phase -1→0→1→2→3a→3b→3c→3d→3e→4→5 with zero overlap or pipelining. Architecturally necessary but not acknowledged as a latency constraint. | LOW |

### R4: Cost Efficiency — 75/100 (unchanged from v2)

**No changes in the uncommitted diff affect cost structure.**

**Strengths**: Model-tier routing well-designed. Budget lanes (L1/L4/L5/L7/L10) correctly assigned to budget. Pro lanes (L2/L3/L6/L8/L9) correctly assigned to pro. Critical override forces L8 and reviewers to pro. `.omo/library` cache integration saves ~3K tokens. Adaptive lane scaling prevents waste on small tasks.

**Issues**:

| # | Finding | Severity |
|---|---|---|
| 1 | **Token estimates undercounted ~3.6×** — documented ~70K M-scale; actual ~255K total API tokens | MED |
| 2 | **Multi-feature mode costs multiply linearly** — `--features=a,b,c` runs full Phase 1-5 per feature, no context sharing | MED |
| 3 | **Unused `model_tiers` aliases** — `quick`, `deep`, `ultrabrain` defined in frontmatter but never referenced | LOW |
| 4 | **L7 omitted from cost-routing table** — "budget tier for lanes L1, L4, L5, L10" but L7 also budget | LOW |

### R5: Staleness/Freshness — 62/100 (+7 from v2)

**Significant improvement from the uncommitted changes**, but core staleness issues remain.

**Progress**: The `allowed-tools` update removes `grep`, `ls`, `bash`, `task`, `edit_file`, `multi_edit` — addressing 4 of the 9 stale references from v2. The cross-platform note acknowledges platform differences. Nested code blocks fixed. Intent Routing section added.

**Remaining staleness**:

| Reference | Location | Expected | Actual | Severity |
|---|---|---|---|---|
| `deepseek-v4-lite` (model_tiers.budget) | line 9 | `deepseek-v4-flash` or valid model | `deepseek-v4-lite` — unconfirmed in provisioning | HIGH |
| `lsp_definition`, `lsp_hover`, `lsp_references` | lines 14, 159 | Valid tools | **NOT available on current platform** | **HIGH** |
| `grep`, `ls`, `bash` in DISPATCH PROTOCOL | line ~159 | `search_content`, `list_directory`, `run_command` | **Legacy names still in subagent tools list** despite frontmatter update. Inconsistency. | HIGH |
| `task()` function calls | ~20 occurrences | `explore` / `research` | `task()` is a DSL concept, not a real tool | MED |
| `run_in_background`, `max_steps` params | ~20 occurrences | Platform-specific | Not available on all platforms | MED |
| `web_search` (allowed-tools) | line 14 | Confirm availability | May not be available — was flagged unavailable in v2 review | LOW |
| `.omo/library/` directory | lines 108-112 | Directory should exist | **Still does NOT exist** | MED |
| `updated: 2026-06-12` | line 8 | `2026-06-14` (mtime) | 2 days stale vs mtime, also doesn't reflect uncommitted edits | LOW |
| L11-L15 prompts | ~191-193 | 5 prompts defined | **Still undefined — 5th review** | **CRITICAL** |
| Dispatch protocol tools mismatch | ~14 vs ~159 | Consistent tools | Frontmatter uses new names; dispatch still uses legacy | MED |

**Freshness Recommendation**: **Weekly** until CRITICAL items resolved (L11-L15, lsp_* removal, dispatch protocol tools update, model name). Then **monthly**.

---

## Devil's Advocate Audit (R6)

### R2 Challenge: Gate Completeness
- **R2 assigned**: 80/100 (prior v2: 78)
- **R6 proposed**: 62/100
- **R6 argument**: The +2 bump for Intent Routing is generous. The routing table still has zero effect on dispatch — the dispatch code blocks remain unconditionally static. IntentGate classification and Intent Routing are now TWO documentation-only layers instead of one. No conditional logic anywhere. "Emergency: Force XS" says skip L6-L10 but the dispatch block always shows all 10 `task()` calls. The routing table increases the documentation-to-execution gap, not decreases it.
- **Verdict**: PARTIALLY AGREE. The routing table DOES add value as a reference for the human operator reading the skill. But R6 is correct that it's still not programmatically wired. The +2 bump reflects improved documentation quality, not operational enforcement. **Score sustained at 80** — structural coverage is genuinely better (Intent Routing is a real specification), even if automation is still absent.

### R3 Challenge: Parallelism
- **R3 assigned**: 65/100 (unchanged from v2)
- **R6 proposed**: 50/100
- **R6 argument**: XL scale has been broken for 5 review cycles. At what point does "XL supported" become false advertising? A feature that doesn't work isn't a feature — it's a bug. If XL is genuinely unsupported, the Scale Classification table should say "XL: NOT YET IMPLEMENTED" or the lane count should be capped at 10. 5 reviews without fixing this is a process failure, not just a technical one.
- **Verdict**: AGREE on the severity. XL scale being broken for 5 cycles is a systemic failure. **Score sustained at 65** reflects the fact that M-scale (the common case) works correctly, but XL is indeed broken. The score floor shouldn't drop below 65 because the parallelism architecture for XS and M is genuinely solid.

### R4 Challenge: Cost Efficiency
- **R4 assigned**: 75/100 (unchanged from v2)
- **R6 proposed**: 55/100
- **R6 argument**: The ~3.6× token undercount is a recurring finding (4 cycles) with no fix. 10 subagents independently rediscover the codebase — no shared cache layer. L6 can make 50+ `web_fetch` calls with no throttle. The "context budget" guardrail (115K) is computed against main-agent context only, ignoring ~140K of subagent API tokens — it's guarding the wrong thing.
- **Verdict**: PARTIALLY AGREE. The token undercount is real and unfixed. However, the cost in absolute terms is still cheap (~$0.03 for M-scale). The 115K guardrail protects the main agent from context overflow, which IS the critical failure mode (subagents are stateless). **Score sustained at 75** — good design, sloppy documentation.

### Biggest Blind Spot (R6)
> **"The uncommitted changes are a partial fix in the wrong direction — they update the frontmatter to use platform-native tool names but leave the dispatch protocol and all lane prompts using the legacy names. This creates a NEW class of bug: a skill whose metadata says it's platform-adapted but whose runtime behavior (lane prompts, dispatch tools) is still on the legacy platform. The skill will appear compatible but fail at runtime."**

This is a **regression risk** introduced by the uncommitted changes. The frontmatter update creates a false sense of platform compatibility while the runtime dispatch still references unavailable tools (`grep`, `ls`, `bash`, `lsp_*`). The cross-platform note says "run `skills/install.sh` to auto-convert" but there's no evidence `install.sh` exists or handles this conversion.

---

## Cross-Reference Findings (Phase 2)

### Contradiction: Frontmatter vs Dispatch Protocol Tools
- **Frontmatter (line 14)**: `allowed-tools: read_file, search_content, search_files, glob, list_directory, directory_tree, run_command, web_fetch, web_search, write_file, explore, research, run_skill, get_file_info, lsp_definition, lsp_hover, lsp_references`
- **Dispatch Protocol (line ~159)**: `tools: ["read_file","grep","glob","ls","lsp_definition","lsp_references","lsp_hover","bash","web_fetch"]`
- **Resolution**: Frontmatter was updated in uncommitted changes; dispatch protocol was NOT. This means subagents would be dispatched with legacy tool names that the platform doesn't recognize. **ESCALATION: HIGH** — this is a runtime-breaking inconsistency.

### Contradiction: Allowed-Tools Claims vs Actual Availability
- `lsp_definition`, `lsp_hover`, `lsp_references`: claimed in both frontmatter and dispatch, NOT available on current platform
- `web_search`: added in uncommitted diff, availability unconfirmed
- `run_skill`: added in uncommitted diff — plausible but used for what?
- **Resolution**: 3 phantom tools remain. `web_search` and `run_skill` are new additions that need verification.

---

## Recommendations

### Critical (score impact >10 points)
| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| C1 | **XL L11-L15 prompts undefined** — 5th consecutive review flagging this | ~191-193 | Define L11-L15_PROMPT with 4-section structure, OR reduce XL to 10 lanes + 5 reviewers (removing the broken scale tier) | Heavy |
| C2 | **Dispatch protocol tools mismatch** — frontmatter updated to platform-native names, dispatch block still uses legacy `grep`/`ls`/`bash`/`lsp_*` | ~159 | Update dispatch protocol tools list to match frontmatter: `["read_file","search_content","search_files","glob","list_directory","directory_tree","run_command","web_fetch"]`. Remove `lsp_definition`,`lsp_references`,`lsp_hover` entirely. | Light |
| C3 | **`lsp_definition`, `lsp_hover`, `lsp_references` phantom tools** — in both frontmatter AND dispatch, not available | lines 14, 159 | Remove from allowed-tools and dispatch protocol. L3_PROMPT and L1_PROMPT that reference "lsp_*" need alternative discovery methods. | Medium |

### High (score impact 5-10 points)
| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| H1 | **M-scale reviewer count inconsistent** — "1 reviewer" in Scale Classification vs "3" in Phase 4 | ~131, ~593 | Unify to 3. Add M-scale conditional dispatch block showing exactly 3 `task()` calls (A, B, C). | Light |
| H2 | **`deepseek-v4-lite` model name unconfirmed** — may not resolve | line 9 | Verify against current provisioning. Update to `deepseek-v4-flash` or generic `budget-model`. | Light |
| H3 | **Lane prompts still reference legacy tools** — L1/L2/L3/L7/L8/L9/L10 prompts all use `grep`, `ls`, `bash` | L1-L10 prompts | Update prompt text to use `search_content`, `list_directory`, `run_command`. Match the frontmatter migration. | Medium |
| H4 | **M5 dead-code — no data-collection lane** | Phase 2 | Add dead-code cross-reference: "For every export from L1, search_content for references — flag orphans as M5 findings" | Light |
| H5 | **S2 auth verification not in Waves template** | ~490 | Add to Wave 4 (Hardening): `- [ ] Auth gate: verify all entry points return 401 for invalid auth (S2)` | Light |
| H6 | **Intent Routing unwired** — routing table exists but dispatch blocks are static | ~95-103, ~189-207 | Add conditional dispatch logic or at minimum add a note: "Before dispatching Phase 1, consult Intent Routing table and skip/adjust lanes accordingly." | Medium |

### Medium (score impact 2-5 points)
| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| M1 | **RVC_PROMPT P-gates composite** — P1/P2/P3 single bullet vs per-gate M-checks | ~648 | Split into: "P1: No N+1 queries (query count assertion)", "P2: No unbounded collections (pagination)", "P3: p95 latency met (load test)" | Light |
| M2 | **Phase 2 "parallel batch" misleading** — 6 sequential inline operations | ~404 | Relabel to "Sequential Verification Checklist" or note: "These checks are sequential by necessity; parallelization would require subagent dispatch." | Light |
| M3 | **Token estimates undercounted ~3.6×** | ~140-149 | Add note: "Subagent API tokens ≈ 3.6× orchestrator context. Total API cost for M-scale: ~$0.03. Main-window budget (115K) protects orchestrator from overflow — the critical constraint." | Light |
| M4 | **Multi-feature mode cost undocumented** | ~35-41 | Add: "Each feature runs independently. N features = N× cost. Use single-plan mode for dependent features." | Light |
| M5 | **`.omo/library/` cache path doesn't exist** | ~108-112 | Either create the directory + implement cache generation in blackcow-librarian, OR mark cache integration as "future" with a note. | Medium |
| M6 | **Wave DAG has no executable dispatch** | ~490 | Add `task()` dispatch code block for wave-based execution, or note that DAG is consumed by blackcow-loop (the executor). | Medium |
| M7 | **`web_search` and `run_skill` added without documented use case** | line 14 | Document which lanes use these tools, or remove if unused. `run_skill` for a planner is unusual — planners don't invoke other skills. | Light |

### Low (score impact <2 points)
| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| L1 | **RETURN vs RETURN EXACTLY inconsistency** | ~568-710 | Standardize on `RETURN EXACTLY:` for all reviewer prompts | Light |
| L2 | **Bare code blocks without language markers** | Multiple | Add `bash`, `yaml`, `markdown`, `text` markers to ~6 blocks | Light |
| L3 | **11 serial inter-phase stages** — unacknowledged latency | — | Add note in Context Budget section: "Inter-phase serialization unavoidable; phases depend on prior phase output." | Light |
| L4 | **Unused `model_tiers` aliases** — `quick`, `deep`, `ultrabrain` | lines 11-13 | Remove or document as reserved for future use | Light |
| L5 | **L7 omitted from cost-routing table** | ~126 | Update: "budget tier for lanes L1, L4, L5, L7, L10" | Light |
| L6 | **`updated` field stale** | line 8 | Bump to `2026-06-14` or automate via git hook | Trivial |
| L7 | **Cross-skill integration contract undefined** | N/A | Define plan schema validation between blackcow-plan output and blackcow-loop consumption | Heavy |

---

## Evolution Readiness

- **Safe to auto-evolve?**: **YES — with constraints.** Items C2, H1, H2, H4, H5, M1, M2, M3, M4, M7, L1-L6 are safe for auto-evolution (lightweight, well-specified fixes).
- **NOT safe for auto-evolve**: C1 (L11-L15 needs architectural design), C3 (lsp_* removal affects lane prompt semantics), H3 (prompt text rewrite), H6 (dispatch logic restructuring), L7 (cross-skill contract).
- **Backup recommended before**: Dispatch protocol (~159), Scale Classification table (~131), Phase 4 dispatch (~586-590), L1-L10 prompts.
- **Estimated evolution tokens**: ~18-22K for safe items (tools update, code blocks, labels, routing note). ~35-40K for full remediation including L11-L15.
- **Recommended approach**: Commit the current uncommitted changes first (they're genuine improvements), then auto-evolve the safe items, then tackle C1/C3/H3/H6/L7 in a manual design pass.

---

## Self-Review Guard Assessment

| Check | Result |
|---|---|
| **Score convergence** | v2: 70.9 → v3: 72.8, Δ=1.9. **PASS (±3 threshold)** |
| **R1 consistency** | v2: 78 → v3: 80 (+2). Attributable to nested code block fixes and cross-platform note. **PASS** |
| **R2 consistency** | v2: 78 → v3: 80 (+2). Attributable to Intent Routing section. **PASS** |
| **R3 consistency** | v2: 65 → v3: 65 (0). No parallelism changes. **PASS** |
| **R4 consistency** | v2: 75 → v3: 75 (0). No cost changes. **PASS** |
| **R5 consistency** | v2: 55 → v3: 62 (+7). Attributable to tool name updates and active work-in-progress edits. **PASS (explained by uncommitted changes)** |
| **R6 blind spot** | Identified NEW risk: frontmatter-dispatch tool mismatch creates false platform compatibility. **Valid finding** |
| **Overall** | **SELF-REVIEW GUARD PASSES.** Scores are consistent and change is explained by observable file edits. |
