# Meta-Review: blackcow-plan v2.0.0

| Field | Value |
|---|---|
| **Reviewed** | 2026-06-18T05:30:00Z |
| **Reviewer** | blackcow-skill-review (Metis 大将) |
| **Skill Version** | 2.0.0 (frontmatter `updated: 2026-06-12`, file mtime 2026-06-14) |
| **File** | `skills/blackcow-plan.md` — 830 lines, 35,888 bytes |
| **Prior Scores** | 66.65 (2025-07-14) → 76.65 (2026-06-14) → 69 (2026-06-16) → 71.5 (2026-06-17) → 70.9 (2026-06-17 v2) → 72.8 (2026-06-17 v3) → 63.25 (2026-06-18) |
| **Self-Review Guard** | NOT a self-review (reviewing blackcow-plan, not blackcow-skill-review). R6 Devil's Advocate active. |

## Overall Score

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| R1 Syntax & Structure | 67 | 15% | 10.05 |
| R2 Gate Completeness | 72 | 30% | 21.60 |
| R3 Parallelism Efficiency | 55 | 25% | 13.75 |
| R4 Cost Efficiency | 62 | 15% | 9.30 |
| R5 Staleness/Freshness | 62 | 15% | 9.30 |
| **TOTAL** | — | **100%** | **64.00** |

> **Score trajectory**: 66.65 → 76.65 → 69 → 71.5 → 70.9 → 72.8 → 63.25 → **64.00**. The 0.75-point uptick from the prior review reflects a slightly more generous R5 staleness assessment (62 vs 58) and R4 cost assessment (62 vs 60), offset by a marginally lower R1 syntax score (67 vs 68). Core findings are consistent: XL scale remains broken, reviewer count contradictions persist, and phantom tools are still listed.

---

## Dimension Details

### R1: Syntax & Structure — 67/100

**Strengths**: Valid YAML frontmatter with all required fields present. Clear phase progression (Phase -1 through Phase 5). Consistent H2/H3 heading hierarchy. All cross-skill references resolve correctly — all 5 sibling skills present. L1-L10 lane prompts all have `RETURN EXACTLY:` with explicit numbered output schemas. IntentGate (Phase -1) adds useful intent classification layer. Nested fenced code blocks resolved (L10 uses `~~~typescript` inside backtick blocks). No dangling/truncated content between lines 500-830.

**Key Issues**:

| # | File:Line | Issue | Severity |
|---|---|---|---|
| 1 | ~131, 593 | **M-scale reviewer count internal contradiction**: Scale Classification table says "1 reviewer"; Phase 4 Reviewer Selection says "A, B, C (3)" | **HIGH** |
| 2 | ~131, 594 | **XL-scale reviewer count mismatch**: Scale Classification says "triple review" (3); Phase 4 says "A, B, C, D, E (5)" | **HIGH** |
| 3 | ~584-590 | **Phase 4 dispatch block unconditionally shows all 5 reviewers** — no conditional block for M (3 reviewers) or XS (skip) | **HIGH** |
| 4 | ~604-705 | **RVA-RVE reviewer prompts use `RETURN:` instead of `RETURN EXACTLY:`** — 5/5 reviewer prompts break the protocol convention established by L1-L10 | **HIGH** |
| 5 | Multiple | **~85% of code blocks lack language markers** — dispatch blocks, lane prompts, execution commands use bare ``` fences | **MED** |
| 6 | ~580 | **Phase 4 heading "Quintuple Adversarial Review"** implies always 5 reviewers, but M gets 3 and XS gets 0 | **MED** |
| 7 | ~395-406 | **L10_PROMPT `RETURN EXACTLY` appears outside code block** — structurally unusual but functionally correct | **LOW** |
| 8 | ~11-13 | **`model_tiers` is non-standard frontmatter** — valid YAML but aliases `quick`, `deep`, `ultrabrain` never referenced in dispatch | **LOW** |
| 9 | ~14 | **`allowed-tools` uses kebab-case** — may be silently ignored by `install_skill` API expecting camelCase | **LOW** |

**Broken References**: **None found.** All 5 referenced sibling skills (`blackcow-loop`, `blackcow-qa`, `blackcow-librarian`, `blackcow-skill-review`, `blackcow-skill-evolver`) exist in `skills/`. All DAG example targets resolve correctly.

---

### R2: Gate Completeness — 72/100

> **Note**: The R2 explore lane returned 100/100 (all gates "COVERED"), but cross-reference lanes XR1/XR2 and R6 Devil's Advocate identified that this conflates **structural documentation** (gate mentioned in Risk Register) with **operational enforcement** (gate wired end-to-end from data collection → verification → SUCCESS anchoring). This synthesized 72/100 accounts for the documentation-to-execution gap. For a PLANNER skill, template-level gate documentation IS valuable — the plan output documents the gate even if the skill doesn't self-enforce — but 100/100 is inflated.

**Strengths**: Risk Register (Phase 3e) provides comprehensive structural coverage of all 11 BKIT gates with numeric thresholds, mitigation strategies, and verification commands. Data-collection lanes correctly mapped: L3→S1, L4→M2/M3, L8→S1/S2/S3, L9→P1/P2/P3. Constraint #13 enforces numeric thresholds. IntentGate (Phase -1) classifies intent and adjusts gate emphasis. Reviewer prompts cover gate categories (RVA: M1-M5, RVB: S1-S3, RVC: P1-P3). Plan template includes Gap Matrix with BKIT Gate column and Codebase Survey with gate-to-lane mapping.

**Gate Coverage Matrix**:

| Gate | Status | Evidence | Operational Gap |
|---|---|---|---|
| **M1** spec-match | ✅ WIRED | Context Anchor `matchRate ≥ 90%` + Gap Matrix "Build" row + Risk Register M1 + RVA per-step check | — |
| **M2** test-pass | ✅ WIRED | Context Anchor `test pass=100%` + L4 test topography + Risk Register M2 + Wave `Gate: M2` tags + RVA | — |
| **M3** regression | ✅ WIRED | Gap Matrix "Modify" row M3 + L4 + Risk Register M3 + IntentGate priority for Bug Fix | SUCCESS anchor omits M3 threshold |
| **M4** lint-clean | ✅ WIRED | Context Anchor `lint=0warn` + Risk Register M4 + Constraint #13 + RVA | — |
| **M5** dead-code | ⚠️ TEMPLATE-ONLY | Gap Matrix "Delete" row M5 + Risk Register M5 + RVA | **No lane hunts unreferenced exports.** No Phase 2 step for orphaned exports. |
| **S1** dataFlow | ✅ WIRED | L3 dataflow risks + L8 security surface + Risk Register S1 + RVB dataFlow integrity score | — |
| **S2** auth | ⚠️ TEMPLATE-ONLY | L8 auth audit + Risk Register S2 + RVB | **`curl → 401` only in Risk Register, not in Waves template.** Performance intent skips L8+RVB creating S2 coverage void. |
| **S3** injection | ✅ WIRED (conditional gap) | L8 injection surfaces + Risk Register S3 + RVB | **Performance intent skips L8+RVB** — S3 coverage void for perf tasks |
| **P1** query | ⚠️ WEAK | L9 N+1 detection + Risk Register P1 + RVC composite P1-P3 check | Composite bullet in RVC; SUCCESS anchor omits P1 threshold |
| **P2** memory | ⚠️ WEAK | L9 unbounded growth + Risk Register P2 + RVC composite P1-P3 check | Same composite collapse as P1; SUCCESS anchor omits P2 threshold |
| **P3** latency | ⚠️ WEAK | L9 latency + Risk Register P3 + Context Anchor `p95_target_ms` + RVC composite P1-P3 check | Only P-gate with SUCCESS threshold; composite-only adversarial review |

**Summary**: 5/11 gates fully wired end-to-end (M1-M4, S1). S3 wired but has conditional coverage gap under Performance intent. M5/S2 template-only. P1-P3 weak (collective adversarial review, minimal SUCCESS anchoring). **Critical finding**: Context Anchor SUCCESS enforces only 4/11 gates (M1, M2, M4, P3). The auto-generated `--completion-promise` derives from SUCCESS — 7 gates are never runtime-enforced.

**Intent Routing Gate Impact**: Performance intent skips L8 and Reviewer B → creates S-gate (S1/S2/S3) coverage black hole for perf tasks. Bug Fix intent skips L9/L10 → removes P-gate data collection. These conditional gaps are not documented in the Intent Routing table.

---

### R3: Parallelism Efficiency — 55/100

**Strengths**: Phase 1 batch-and-wait pattern correctly specified for XS and M scales — all lanes dispatched with `run_in_background=true` before awaiting. Phase 4 reviewer dispatch follows same pattern. Lane independence verified — no hidden data dependencies between L1-L10 (cross-referencing happens in Phase 2 after all return). Correct cost-tier routing in dispatch (budget for L1/L4/L5/L7/L10, pro for L2/L3/L6/L8/L9). Intent routing correctly skips lanes for appropriate intent classes (8/10 routing decisions are sound).

**Key Issues**:

| # | File:Line | Issue | Severity |
|---|---|---|---|
| 1 | ~191-193 | **XL scale broken — 5 of 15 lanes undefined**: L11-L15 prompts are prose-only ("Security/performance extensions", "documentation, i18n, accessibility"). Zero `task()` dispatch code, zero prompt text. XL is non-functional. Flagged across 6+ consecutive reviews without resolution. | **CRITICAL** |
| 2 | ~404-416 | **Phase 2 claims "ONE parallel batch" but is entirely sequential**: Header says parallel; body lists 6 inline grep/read_file operations. Steps 4-6 (contradiction check, layer integrity) depend on steps 1-3 (symbol verification). Zero `task()` dispatches. | **HIGH** |
| 3 | ~179 | **Platform adaptation says "Ignore `run_in_background`"** — the `task()` pseudo-code maps to `explore()`, which is synchronous. The plan's core parallelism guarantee relies on a mechanism the adaptation says to ignore. | **HIGH** |
| 4 | ~207-209 | **No M-scale conditional dispatch for Phase 4**: Only the full 5-reviewer block shown. Implementer must guess which 3 of 5 to drop for M-scale. | **MED** |
| 5 | ~175-207 | **`task()` is pseudo-code, not real tool API**: All ~20 dispatch calls use a function signature that doesn't exist in any tool namespace. Real platform mapping would use `explore`/`research`. | **MED** |
| 6 | ~490-510 | **Wave DAG has no executable dispatch**: Wave-level parallelism claims "Tasks within a wave run in parallel" but no `task(…, run_in_background=true)` dispatch code shown. DAG yaml is documentation-only. | **MED** |

**Overlap Issues**:

| Lane A vs Lane B | Overlap | Severity |
|---|---|---|
| **L1 (Surface Topology) vs L2 (Call Graph)** | Both independently trace request flow with BKIT layer tagging. ~60% output redundancy on entry/exit points. | **MEDIUM** |
| **L3 (Data Shape) vs L8 (Security)** | L3 flags "DATAFLOW RISKS with BKIT S1 tag" — security analysis in a data-shape lane. L8 also covers S1. | **MEDIUM** |
| **L2 (Call Graph) vs L9 (Performance)** | L2 annotates every call-site side-effect (DB, HTTP, FS). L9 looks for N+1 queries. Both visit DB-call sites independently. | **MEDIUM** |

**Lane Count Assessment**:

| Scale | Advertised | Functional | Verdict |
|---|---|---|---|
| XS | 5 lanes (L1-L5) | ✅ All defined | Correct |
| M | 10 lanes (L1-L10) | ✅ All defined | Correct |
| XL | 15 lanes (L1-L15) | ❌ L11-L15 undefined | **Broken — cap at 10 lanes + 5 reviewers until defined** |

**Inter-phase serial gates**: Phase -1→0→1→2→3→4→5 are architecturally sequential — only 2 of 5 phases (Phase 1 and Phase 4) contain internal parallelism. This is inherent to plan generation but unacknowledged as a latency constraint.

---

### R4: Cost Efficiency — 62/100

**Strengths**: Model-tier routing correctly implemented in dispatch: budget for L1/L4/L5/L7/L10, pro for L2/L3/L6/L8/L9. L8 forced pro regardless of tier flag. All reviewers use pro. Adaptive lane scaling (XS:5, M:10, XL:10) prevents waste on small tasks. Context Budget guard (115K) protects orchestrator from context overflow. Intent routing saves tokens: Performance skips L8+RVB (~10K saved), Bug Fix skips L9+L10+RVD (~15K saved).

**Key Issues**:

| # | Finding | Severity |
|---|---|---|
| 1 | **Token estimates undercounted — documented 70K vs realistic ~85K for M-scale**: Phase 4 documented as "5K" for 3 reviewers but should be 3×5K=15K. Total M-scale is ~85K, pushing closer to the 115K guardrail. | **HIGH** |
| 2 | **`deepseek-v4-lite` model name likely stale**: The API uses `deepseek-v4-flash`, not `-lite`. Mentioned in 4 places (frontmatter model_tiers.budget, model_tiers.quick, cost-routing table, comment). | **HIGH** |
| 3 | **Pricing data 2-3× off actual API prices**: Skill claims $0.07/1M for budget, $0.14/1M for pro. Real DeepSeek pricing is ~$0.14/1M (flash) and ~$0.435/1M (pro) at cache miss. | **MED** |
| 4 | **Multi-feature mode cost undocumented**: `--features=a,b,c` runs full Phase 1-5 pipeline independently per feature with zero context sharing. 3 features = 3× cost. No warning. | **MED** |
| 5 | **`.omo/library/` cache directory doesn't exist**: Cache integration (Phase 0.0) has been aspirational across 6 review cycles. Claimed ~3K savings are fictional. | **MED** |
| 6 | **L7 omitted from cost-routing table "Use for" column**: Table lists "L1, L4, L5, L10" but misses L7. Auto-mode prose correctly includes L7. Documentation defect only. | **LOW** |
| 7 | **Dead frontmatter aliases**: `quick`, `deep`, `ultrabrain` defined in `model_tiers` but never referenced in any dispatch block. | **LOW** |

**Cost Estimate — M-scale Feature Intent (all 10 lanes + 3 reviewers)**:

| Component | Budget Tokens | Pro Tokens | Est. Cost |
|---|---|---|---|
| Phase 1: 5 budget subagents (L1,L4,L5,L7,L10) | ~25K | — | ~$0.0035 |
| Phase 1: 5 pro subagents (L2,L3,L6,L8,L9) | — | ~25K | ~$0.011 |
| Phase 2-5: orchestrator + 3 reviewers + synthesis | — | ~35K | ~$0.015 |
| **Total M invocation** | **~85K** | | **~$0.03** |

> Documented estimate: ~70K. Realistic: ~85K. The ~15K gap is from Phase 4 using "5K" for 3 reviewers when it should be 3×5K=15K.

**Consolidation Opportunities**: L1+L2 merge and L4+L5 merge were evaluated — both would save negligible tokens (~$0.0005/invocation) while degrading lane independence. **Not recommended.**

---

### R5: Staleness/Freshness — 62/100

**Strengths**: File is actively maintained (7 reviews in 4 days). All cross-skill references resolve correctly. Zero TODO/FIXME/HACK markers in the skill text. Cross-platform adaptation note present. Nested code blocks fixed. BKIT 11-gate taxonomy matches current standard. `deepseek-v4-pro` model name still valid.

**Key Issues**:

| Reference | Location | Expected | Actual | Severity |
|---|---|---|---|---|
| L11-L15 prompts | ~191-193 | 5 defined prompts with `RETURN EXACTLY` blocks | **Undefined prose-only** — 6+ review cycles without resolution | **CRITICAL** |
| `deepseek-v4-lite` | line 9, ~137 | `deepseek-v4-flash` (per API) | `deepseek-v4-lite` — may not resolve at runtime | **HIGH** |
| M-scale reviewer count | ~133 vs ~593 | Unified number | **"1 reviewer" vs "3 reviewers"** — 6+ cycles unresolved | **HIGH** |
| `grep`, `ls`, `bash` in dispatch protocol | ~159 | `search_content`, `list_directory`, `run_command` | Legacy names in subagent tools list — frontmatter updated but dispatch wasn't | **HIGH** |
| `updated: 2026-06-12` | line 8 | `2026-06-14` (mtime) or `2026-06-18` (today) | 2-6 days stale | **LOW** |
| `.omo/library/` cache directory | ~108-112 | Directory with cache files | **Does NOT exist** — aspirational across 6 cycles | **MED** |
| `web_search` in allowed-tools | line 14 | Documented use case | Added without any lane prompt using it | **MED** |
| "OmO hyperplan" references | ~601, 667, 688 | Current naming ("BKIT") | Survives in 3 places — older naming convention | **LOW** |

**Previously flagged but FIXED**:
- `lsp_definition`, `lsp_hover`, `lsp_references` phantom tools — **removed** from frontmatter but may still linger in dispatch protocol
- Nested code block rendering bugs — **fixed**

**Freshness Recommendation**: **Weekly** until CRITICAL items resolved (L11-L15 definition, model name update, reviewer count unification). Then **monthly** for routine checks. The 6-cycle persistence of CRITICAL items suggests a process gap — recommendations should shift from "review more often" to constraint-based ("cap XL at 10 lanes until L11-L15 defined").

---

## Devil's Advocate Challenge (R6)

### R2 Challenge: Gate Completeness
- **Score assigned**: 72/100
- **R6 proposed**: ~58/100
- **R6 argument**: Gap Matrix covers only 3/11 gates (M1, M3, M5). Codebase Survey has 4/10 lanes with `—` gate mapping. 5/11 gates are template-only or weak. IntentGate doesn't change plan output template. True operational coverage is ~5/11 = 45%.
- **Verdict**: PARTIALLY AGREE. R6 correctly identifies the documentation-to-execution gap. But for a PLANNER skill, Risk Register template coverage IS valuable structural coverage. The plan output documents gates even if the skill doesn't self-enforce. **Score sustained at 72** — the 8-point drop from prior 80+ scores already accounts for this gap.

### R3 Challenge: Parallelism
- **Score assigned**: 55/100
- **R6 proposed**: ~40/100
- **R6 argument**: XL scale broken for 6 cycles with no fix. Phase 2 "parallel" label misleading. Wave parallelism is documentation-only. Only 2 of 5 phases contain parallelism. Even within Phase 1, the slowest lane determines wall-clock time.
- **Verdict**: PARTIALLY AGREE on severity of XL being broken. **Score sustained at 55.** XS and M (the common cases) work correctly: Phase 1 batch-fire, Phase 4 reviewer dispatch, and lane independence are solid. The 55 reflects that ~55% of the parallelism surface is functional.

### R4 Challenge: Cost Efficiency
- **Score assigned**: 62/100
- **R6 proposed**: ~40/100
- **R6 argument**: Token estimates contradictory (50K vs 65K for XL Phase 1 in same file), 5K/lane optimistic, L6 web_fetch unbounded, Phase 4 reviewer costs undercounted, `deepseek-v4-lite` stale.
- **Verdict**: PARTIALLY AGREE. The 5K/lane estimate is indeed optimistic for max_steps=15 subagents. But the 115K guardrail protects the orchestrator, not subagent spend (which bills separately). The model name staleness and token arithmetic errors are documentation defects, not cost-architecture flaws. **Score sustained at 62** — good routing design, sloppy documentation.

### Biggest Blind Spot (R6)
> **"The uncommitted changes update the frontmatter to use platform-native tool names but leave the dispatch protocol and all lane prompts using legacy names — creating a NEW class of bug where the skill appears platform-compatible but fails at runtime."**

**Validated**: Frontmatter lists `search_content`, `search_files`, `list_directory`, `directory_tree`, `run_command`; dispatch protocol at ~159 still lists `grep`, `ls`, `bash`. Subagents dispatched with legacy tools could fail silently on platforms where only native names are recognized.

---

## Cross-Reference Escalations

| # | Finding | Severity | Details |
|---|---|---|---|
| E1 | **Performance intent creates S-gate coverage black hole** | **HIGH** | Routing table skips L8 (Security) AND Reviewer B (Security) for Performance intent. S1/S2/S3 have zero data-collection AND zero adversarial review for perf tasks. A Performance task touching auth middleware would have no security gate coverage. |
| E2 | **Context Anchor SUCCESS enforces only 4/11 gates** | **HIGH** | `--completion-promise` derives from SUCCESS, which has thresholds for M1/M2/M4/P3 only. 7/11 gates are never runtime-enforced by the downstream executor. |
| E3 | **Frontmatter-dispatch tool mismatch creates runtime failure risk** | **HIGH** | Frontmatter uses platform-native tool names; dispatch protocol uses legacy names. The "install.sh conversion" claim is unverified and may not handle tool-name conversion in dispatch protocol code blocks. |
| E4 | **R2 methodology conflates structural docs with operational wiring** | **MED** | 5/11 gates marked TEMPLATE-ONLY or WEAK across prior reviews were not penalized in scoring. A Risk Register row ≠ end-to-end gate enforcement. R2 needs to differentiate "documented" from "wired." |

---

## Recommendations

### Critical (score impact >10 points)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| C1 | **L11-L15 prompts undefined — XL scale non-functional** | ~191-193 | Define L11_PROMPT through L15_PROMPT with full 4-section structure, OR cap XL at 10 lanes + 5 reviewers and remove 15-lane claim from Scale Classification | **Heavy** |
| C2 | **Dispatch protocol tools mismatch** | ~159 | Update dispatch protocol tools list to platform-native names: `["read_file","search_content","search_files","glob","list_directory","directory_tree","run_command","web_fetch"]`. Remove `grep`, `ls`, `bash`. | **Light** |

### High (score impact 5-10 points)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| H1 | **RVA-RVE use `RETURN:` not `RETURN EXACTLY:`** | ~604-705 | Standardize all 5 reviewer prompts to `RETURN EXACTLY:`. | **Light** |
| H2 | **M-scale reviewer count: "1" vs "3"** | ~133 vs ~593 | Unify to "3" in Scale Classification table. Add M-scale conditional reviewer dispatch block (A, B, C only). | **Light** |
| H3 | **XL-scale reviewer count: "triple review" vs "5"** | ~134 vs ~593 | Unify to "5" in Scale Classification table. | **Light** |
| H4 | **Token estimates undercounted (70K vs ~85K)** | ~140-149 | Update documented estimate to ~85K. Fix Phase 4 from "5K" to "15K" for M-scale (3 reviewers × 5K). | **Light** |
| H5 | **Multi-feature mode cost undocumented** | ~35-41 | Add cost warning: "N features = N× single-feature cost. Use single-plan mode for dependent features." | **Light** |
| H6 | **Phase 2 "parallel batch" label misleading** | ~404 | Relabel: "Sequential Verification Checklist" with note that steps 4-6 depend on steps 1-3. | **Light** |
| H7 | **Performance intent voids S-gate coverage** | ~95-103 | Add note: "⚠️ Performance intent skips L8 and Reviewer B — S1/S2/S3 gates rely on Risk Register entries only. For security-sensitive performance work, override with `--force-security-gates`." | **Medium** |
| H8 | **`deepseek-v4-lite` → `deepseek-v4-flash`** | line 9, ~137 | Update model name in frontmatter and cost-routing table to match API provisioning. | **Light** |

### Medium (score impact 2-5 points)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| M1 | **24 code blocks lack language markers** | Multiple | Add `bash`, `yaml`, `markdown`, `text` markers to bare ``` fences. | **Light** |
| M2 | **M5 dead-code — no cross-reference step** | ~404-416 | Add to Phase 2: "Cross-reference L1 exports against L2 caller counts — flag any export with 0 callers." | **Light** |
| M3 | **S2 auth `curl → 401` not in Waves template** | ~484-510 | Add to Wave 4: `- [ ] Auth gate: verify all entry points return 401 for invalid auth (S2)` | **Light** |
| M4 | **RVC_PROMPT P-gates composite** | ~648 | Split composite "P1~P3" bullet into 3 per-gate checks: P1, P2, P3 individually. | **Light** |
| M5 | **Context Anchor SUCCESS omits 7/11 gate thresholds** | ~454-461 | Add M3, M5, S1, S2, S3, P1, P2 thresholds to SUCCESS template or note they're in Risk Register. | **Medium** |
| M6 | **`.omo/library/` cache directory doesn't exist** | ~108-112 | Either create directory + implement cache generation, OR mark as "FUTURE" with implementation note. | **Medium** |
| M7 | **`web_search` in allowed-tools without documented use** | line 14 | Document which lane uses `web_search` (L6 uses `web_fetch` directly) or remove from allowed-tools. | **Light** |

### Low (score impact <2 points)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| L1 | **Unused `model_tiers` aliases** (`quick`, `deep`, `ultrabrain`) | ~11-13 | Remove or document as reserved for future use. | **Light** |
| L2 | **L7 omitted from cost-routing table "Use for" column** | ~144 | Add L7: `"grep, glob, ls, basic read tasks (L1, L4, L5, L7, L10)"` | **Light** |
| L3 | **`updated` field stale** | line 8 | Bump to 2026-06-18 to match latest review date. | **Light** |
| L4 | **Phase 4 heading "Quintuple" misleading for M-scale** | ~580 | Change to "Adversarial Review" or "Scale-Gated Adversarial Review." | **Light** |

---

## Evolution Readiness

- **Safe to auto-evolve?**: **YES** — for Light-effort items only (H1-H6, H8, M1-M4, M7, L1-L4). These are documentation fixes, label changes, and parameter updates.
- **Manual review required for**: C1 (L11-L15 design — requires architectural decision), C2 (dispatch protocol rewrite — could break subagent execution), H7 (intent routing change — security-sensitive), M5 (SUCCESS anchor redesign), M6 (cache implementation).
- **Backup recommended before**: C1, C2, H7, M5, M6 — est. ~35K tokens for evolution.
- **If L11-L15 cannot be designed**: Cap XL at 10 lanes + 5 reviewers and adjust Scale Classification to reflect reality. This is a 1-line change that removes the CRITICAL staleness finding.

---

## Execution Command (for blackcow-skill-evolver)

```
blackcow-skill-evolver --skill=blackcow-plan --review=.omo/meta-review/review-2026-06-18-blackcow-plan-v2.md --trust-level=2 --apply=Light
```

> To apply Medium/High/Critical items, escalate `--trust-level` or approve individually.

---

## Self-Review Guard

| Check | Result |
|---|---|
| **Is this a self-review?** | **NO.** Reviewing `blackcow-plan.md`, not `blackcow-skill-review.md`. No deterministic re-run required. |
| **R6 Devil's Advocate active?** | **YES.** Challenge provided for R2, R3, R4 with proposed alternative scores. |
| **Cross-reference lanes active?** | **YES.** XR1 and XR2 identified 4 escalations (E1-E4). |
| **Score trajectory consistent?** | Prior: 66.65 → 76.65 → 69 → 71.5 → 70.9 → 72.8 → 63.25. New: **64.00**. The 0.75-point uptick reflects marginal differences in lane assessments, not score instability. Both reviews identify the same CRITICAL/HIGH items. |
