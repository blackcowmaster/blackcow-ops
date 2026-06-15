# Meta-Review: blackcow-plan v2.0.0

| Field | Value |
|---|---|
| **Reviewed** | 2026-06-18T01:15:00Z |
| **Reviewer** | blackcow-skill-review (Metis 大将) |
| **Skill Version** | 2.0.0 (frontmatter `updated: 2026-06-12`, git HEAD 9872e3f 2026-06-12, file mtime 2026-06-14) |
| **Git State** | **UNCOMMITTED CHANGES PRESENT** — 51-line diff from HEAD (36 insertions, 15 deletions) |
| **Prior Scores** | 66.65 (2025-07-14) → 76.65 (2026-06-14) → 69 (2026-06-16) → 71.5 (2026-06-17) → 70.9 (2026-06-17 v2) → 72.8 (2026-06-17 v3) |
| **Self-Review Guard** | This is NOT a self-review (reviewing blackcow-plan, not blackcow-skill-review). No self-consistency check required. |

## Overall Score

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| R1 Syntax & Structure | 68 | 15% | 10.20 |
| R2 Gate Completeness | 72 | 30% | 21.60 |
| R3 Parallelism Efficiency | 55 | 25% | 13.75 |
| R4 Cost Efficiency | 60 | 15% | 9.00 |
| R5 Staleness/Freshness | 58 | 15% | 8.70 |
| **TOTAL** | — | **100%** | **63.25** |

> **Score trajectory**: 66.65 → 76.65 → 69 → 71.5 → 70.9 → 72.8 → **63.25**. This review is the most rigorous to date — 6 parallel independent lanes, 2 cross-reference lanes, and a devil's advocate challenge. The drop reflects applying stricter operational-enforcement criteria (not just structural presence) to R2, penalizing broken XL scale in R3, and docking R4 for unfixed cost documentation gaps. Prior reviews were generous on template-coverage vs. wired-coverage and did not penalize 5-cycle-unresolved CRITICAL items in scoring.

---

## Dimension Details

### R1: Syntax & Structure — 68/100

**Strengths**: Valid YAML frontmatter, clear phase progression (Phase -1 through Phase 5), consistent H2/H3 heading hierarchy, all cross-skill references resolve correctly (all 5 sibling skills present), `install.sh` exists, nested fenced code blocks resolved (L10 uses `~~~typescript` inside ```, Phase 5 uses 4-backtick wrapping). Lane prompts L1-L10 all have `RETURN EXACTLY:` with explicit output schemas. IntentGate (Phase -1) adds useful intent classification layer.

**Issues**:

| # | File:Line | Issue | Severity |
|---|---|---|---|
| 1 | ~604-621, 624-644, 647-663, 666-684, 687-705 | **RVA-RVE reviewer prompts use `RETURN:` instead of `RETURN EXACTLY:`** — All 5 reviewer prompts break the protocol convention established by L1-L10 (10/10 use `RETURN EXACTLY:`). Structural inconsistency. | **CRITICAL** |
| 2 | ~121-126, 155-159, 188-208, 215-419, 585-705, 721-723, 808-810 | **24 code blocks lack language markers** — All dispatch blocks, lane prompts, and execution commands use bare ``` fences with no `bash`, `yaml`, `markdown`, or `text` tag. Widespread across the file. | **HIGH** |
| 3 | ~133 | **Scale Classification M-scale: "1 reviewer"** vs Phase 4 (~593): "A, B, C (3)" — direct internal contradiction. | **HIGH** |
| 4 | ~134 | **Scale Classification XL-scale: "triple review" (3)** vs Phase 4 (~593): "A, B, C, D, E (5)" — direct internal contradiction. | **HIGH** |
| 5 | ~191-193 | **XL dispatch incomplete** — L11-L15 described in prose only ("Security/performance extensions", "documentation, i18n, accessibility"); no `task()` dispatch code block or prompt text. | **CRITICAL** |
| 6 | ~14 | **`lsp_definition`, `lsp_hover`, `lsp_references` in allowed-tools** — phantom tools not available on any current platform. | **HIGH** |
| 7 | ~159 | **Dispatch protocol tools list outdated** — subagent tools list references legacy `grep`, `ls`, `bash` despite frontmatter using platform-native names. Inconsistency between frontmatter and dispatch. | **HIGH** |
| 8 | ~14 | **`web_search` in allowed-tools** — unconfirmed availability; added in uncommitted changes without documented use case. | **MED** |
| 9 | ~384-419 | **L10_PROMPT uses `~~~typescript` (tilde fence)** inside backtick-fenced code block — valid per CommonMark (different fence chars) but may confuse renderers. | **MED** |
| 10 | ~11-13 | **`model_tiers` non-standard frontmatter** — valid YAML but not part of standard skill spec; aliases `quick`, `deep`, `ultrabrain` never referenced in dispatch code. | **LOW** |

**Broken References**: None. All cross-skill references (blackcow-loop, blackcow-qa, blackcow-skill-review, blackcow-skill-evolver, blackcow-librarian) resolve to existing files. `skills/install.sh` exists.

---

### R2: Gate Completeness — 72/100

> **Note**: The R2 explore subagent returned 100/100 (all gates "COVERED"), but the cross-reference lanes (XR1, XR2) and Devil's Advocate (R6) identified that this conflates structural documentation (gate mentioned in Risk Register) with operational enforcement (gate wired end-to-end). This synthesized score accounts for the documentation-to-execution gap.

**Strengths**: Risk Register (Phase 3e) provides comprehensive structural coverage of all 11 BKIT gates with numeric thresholds, mitigation strategies, and verification commands. Data-collection lanes are correctly mapped: L3→S1, L4→M2, L8→S1/S2/S3, L9→P1/P2/P3. Constraint #13 enforces numeric thresholds. IntentGate (Phase -1) classifies intent and adjusts gate emphasis. Reviewer prompts cover gate categories (RVA: M1-M5, RVB: S1-S3, RVC: P1-P3).

**Gate Coverage Matrix**:

| Gate | Status | Evidence | Operational Gap |
|---|---|---|---|
| **M1** spec-match | ✅ **WIRED** | IntentGate → Gap Matrix → Risk Register M1 → Context Anchor SUCCESS `matchRate ≥ 90%` → RVA per-step check | — |
| **M2** test-pass | ✅ **WIRED** | IntentGate → L4 lane → Risk Register M2 → Context Anchor SUCCESS `test pass=100%` → RVA per-step check | — |
| **M3** regression | ✅ **WIRED** | IntentGate → Gap Matrix `🔧 Modify` → L4 → Risk Register M3 → RVA per-step check | SUCCESS anchor omits M3 threshold |
| **M4** lint-clean | ✅ **WIRED** | IntentGate → Risk Register M4 → Context Anchor SUCCESS `lint=0warn` → RVA per-step check | — |
| **M5** dead-code | ⚠️ **TEMPLATE-ONLY** | Gap Matrix `🗑️ Delete` → Risk Register M5 → RVA | **No lane hunts unreferenced exports.** L1 lists exports; L2 traces from target symbol only. No Phase 2 cross-reference step finds orphaned exports. |
| **S1** dataFlow | ✅ **WIRED** | IntentGate → L3 + L8 dual lanes → Risk Register S1 → RVB dataFlow integrity score | SUCCESS anchor omits S1 threshold |
| **S2** auth | ⚠️ **TEMPLATE-ONLY** | L8 auth audit → Risk Register S2 → RVB security assessment | **`curl → 401` exists only in Risk Register, not wired into Waves template.** No Wave step executes auth verification. SUCCESS anchor omits S2 threshold. **Performance intent skips L8 AND RVB — S2 coverage void for perf tasks.** |
| **S3** injection | ✅ **WIRED** | IntentGate → L8 injection surface search → Risk Register S3 → RVB | **Performance intent skips L8 AND RVB — S3 coverage void for perf tasks.** |
| **P1** query | ⚠️ **WEAK** | L9 N+1 detection → Risk Register P1 → RVC composite P1-P3 check | **Single composite bullet in RVC_PROMPT.** P-gates get 1/3 the adversarial scrutiny of M-gates. SUCCESS anchor omits P1 threshold. |
| **P2** memory | ⚠️ **WEAK** | L9 unbounded growth detection → Risk Register P2 → RVC composite P1-P3 check | Same composite collapse as P1. SUCCESS anchor omits P2 threshold. |
| **P3** latency | ⚠️ **WEAK** | L9 latency → Risk Register P3 → Context Anchor SUCCESS `p95_target_ms` → RVC composite P1-P3 check | Only P-gate with SUCCESS anchor threshold. Still composite-only adversarial review. |

**Summary**: 5/11 gates fully wired end-to-end (M1-M4, S1). S3 is wired but has conditional coverage gap (Performance intent). M5 and S2 are structurally documented but lack operational wiring. P1-P3 have data-collection lanes but weak adversarial review and minimal SUCCESS anchoring. The Intent Routing table introduces NEW conditional gaps: Performance intent skips all S-gate coverage (L8 + RVB removed), Bug Fix intent skips P-gate data collection (L9/L10 skipped).

**Key finding**: Context Anchor SUCCESS (the plan's execution contract) enforces only 4/11 gates (M1, M2, M4, P3). The auto-generated `--completion-promise` derives from SUCCESS, meaning 7 gates are never runtime-enforced by the downstream executor.

---

### R3: Parallelism Efficiency — 55/100

**Strengths**: Phase 1 batch-and-wait pattern correctly specified for XS and M scales — all lanes dispatched with `run_in_background=true` before awaiting. Phase 4 reviewer dispatch follows same pattern. Lane independence verified — no hidden data dependencies between L1-L10 (cross-referencing happens in Phase 2 after all return). Correct cost-tier routing in dispatch (budget for L1/L4/L5/L7/L10, pro for L2/L3/L6/L8/L9).

**Issues**:

| # | Section | Issue | Severity |
|---|---|---|---|
| 1 | ~191-193 | **XL scale broken — 5 of 15 lanes undefined.** L11-L15 prompts are prose descriptions only ("Security/performance extensions", "documentation, i18n, accessibility"). Zero `task()` dispatch code, zero prompt text. XL is non-functional. **Flagged across 6 consecutive reviews (2025-07-14 through 2026-06-18) without resolution.** | **CRITICAL** |
| 2 | ~404-416 | **Phase 2 claims "ONE parallel batch" but is entirely sequential.** Header says parallel; body lists 6 inline grep/read_file operations. Steps 4-6 (contradiction check, layer integrity) depend on steps 1-3 (symbol verification). Zero `task()` dispatches. | **HIGH** |
| 3 | ~133 vs ~593 | **M-scale reviewer count internally inconsistent.** Scale Classification table: "1 reviewer." Phase 4 Reviewer Selection: "A, B, C (3)." Phase 4 dispatch block always shows 5 reviewers with no M-scale conditional variant. | **HIGH** |
| 4 | ~134 vs ~593 | **XL-scale reviewer count internally inconsistent.** Scale Classification table: "triple review" (3). Phase 4 Reviewer Selection: "5." Both contradict each other. | **HIGH** |
| 5 | ~490-510 | **Wave DAG has no executable dispatch.** Wave-level parallelism claims "Tasks within a wave run in parallel" but no `task(…, run_in_background=true)` dispatch code shown. DAG yaml is documentation-only. Appropriate for a planner (generates plans, doesn't execute) but the claim of parallelism is aspirational. | **MED** |
| 6 | ~207-209 | **No M-scale conditional dispatch for Phase 4.** Only the full 5-reviewer block shown. Implementer must guess which 3 of 5 to drop for M-scale. | **MED** |
| 7 | ~175-207 | **`task()` is pseudo-code, not real tool API.** All ~20 dispatch calls use `task(description=..., prompt=..., run_in_background=..., max_steps=..., model=...)` — this function signature doesn't exist in any tool namespace. Real platform mapping would use `explore`/`research` with platform-specific parameters. | **MED** |
| 8 | — | **11 inter-phase serial gates.** Phase -1→0→1→2→3a→3b→3c→3d→3e→4→5 — architecturally necessary but unacknowledged as latency constraint. | **LOW** |

**Overlap Issues**:

| File:Line | Lane A vs Lane B | Overlap |
|---|---|---|
| ~213-230 vs ~232-249 | **L1 (Surface Topology) vs L2 (Call Graph)** | Both independently trace request flow with BKIT layer tagging. ~60% output redundancy. L2 could consume L1's entry/exit points. |
| ~250-265 vs ~344-365 | **L3 (Data Shape) vs L8 (Security)** | L3 flags "DATAFLOW RISKS with BKIT S1 tag" — security analysis in a data-shape lane. L8 also covers S1. Overlap in S1 territory. |
| ~213-230 vs ~384-419 | **L1 (Surface Topology) vs L10 (Pattern Library)** | Both survey codebase structure and naming. ~20% file discovery overlap. L10 could consume L1's file tree. |

**Lane Count Assessment**:

| Scale | Current | Functional? | Fix |
|---|---|---|---|
| XS (5) | L1-L5 fully defined | ✅ Yes | — |
| M (10) | L1-L10 fully defined | ✅ Yes | — |
| XL (15) | L1-L10 defined + L11-L15 prose-only | ❌ **Broken** | Define L11-L15_PROMPT with 4-section structure, OR cap XL at 10 lanes + 5 reviewers |

---

### R4: Cost Efficiency — 60/100

**Strengths**: Model-tier routing correctly implemented in dispatch code: budget for L1/L4/L5/L7/L10, pro for L2/L3/L6/L8/L9, L8 forced pro, all reviewers pro. Adaptive lane scaling prevents waste on small tasks. `.omo/library` cache integration concept would save ~3K tokens if implemented. Context Budget guard (115K) protects orchestrator from context overflow.

**Issues**:

| # | Finding | Severity |
|---|---|---|
| 1 | **Token estimates wrong.** Documented ~70K for M-scale. With subagent API overhead (prompts, tool definitions, system context): ~116K realistic total. This exceeds the 115K effective budget, triggering the "split into two plans" logic on every M-scale invocation — doubling latency and cost. | **HIGH** |
| 2 | **Multi-feature mode cost undocumented.** `--features=a,b,c` runs full Phase 1-5 pipeline independently per feature with zero context sharing. 3 features = 3× cost (~$0.039). No warning anywhere. | **HIGH** |
| 3 | **`.omo/library/` cache directory doesn't exist.** Cache integration (Phase 0.0) has been aspirational across 6 review cycles. The claimed ~3K savings are fictional. | **MED** |
| 4 | **Context Budget guards wrong resource.** The 115K guardrail protects main-agent context window from overflow (correct). But it ignores ~140K of subagent API tokens. Subagent spend is unguarded. | **MED** |
| 5 | **Dead frontmatter aliases.** `quick`, `deep`, `ultrabrain` defined in `model_tiers` but never referenced in any dispatch block in this file. Three lines of dead config. | **LOW** |
| 6 | **L7 omitted from cost-routing table.** Table at ~144 lists budget lanes as "L1, L4, L5, L10" — misses L7. Auto-mode prose at ~147 correctly includes L7. Documentation defect, not routing bug. | **LOW** |
| 7 | **10 subagents independently re-discover codebase.** L1-L10 each run independent `glob`/`grep`/`read_file` on same files. L6 can make 50+ `web_fetch` calls per dependency with no throttle. No shared cache layer across lanes. | **MED** |

**Token & Cost Estimate (M-scale)**:

| Component | Tokens | Rate | Cost |
|---|---|---|---|
| Phase 1: 5 budget subagents (~7K each incl. overhead) | ~35K | $0.07/M | $0.00245 |
| Phase 1: 5 pro subagents (~7K each incl. overhead) | ~35K | $0.14/M | $0.00490 |
| Phase 2-5: orchestrator + review | ~46K | $0.14/M | $0.00644 |
| **Total per M invocation** | **~116K** | — | **~$0.014** |

> Documented estimate: ~70K / 128K. Realistic: ~116K. Gap: +66%.

**Consolidation assessment**: Consolidation opportunities (L1+L2 merge, L4+L5 merge) save negligible amounts (~$0.0005/invocation) and would degrade lane independence. Not recommended.

---

### R5: Staleness/Freshness — 58/100

**Strengths**: File is actively maintained (6 reviews, recent uncommitted edits, 51-line working-copy diff). All cross-skill references resolve correctly. Zero TODO/FIXME/HACK markers in the skill text. Cross-platform adaptation note present. Nested code blocks fixed. BKIT 11-gate taxonomy matches current standard.

**Issues**:

| Reference | Location | Expected | Actual | Severity |
|---|---|---|---|---|
| `lsp_definition`, `lsp_hover`, `lsp_references` | lines 14, ~159 | Valid available tools | **NOT available on any current platform** — phantom tools persist in both frontmatter AND dispatch protocol | **CRITICAL** |
| L11-L15 prompts | ~191-193 | 5 defined prompts with `RETURN EXACTLY` blocks | **Undefined prose-only** — 6 review cycles without resolution | **CRITICAL** |
| `deepseek-v4-lite` (model_tiers.budget) | line 9 | Confirmed model name in provisioning | Unconfirmed — only `deepseek-v4-pro` documented; `deepseek-v4-lite` may not resolve | **HIGH** |
| M-scale reviewer count | ~133 vs ~593 | Unified number | **1 reviewer vs 3 reviewers** — internal inconsistency, 6 cycles | **HIGH** |
| `grep`, `ls`, `bash` in dispatch protocol | ~159 | `search_content`, `list_directory`, `run_command` | **Legacy names in subagent tools list** — frontmatter updated but dispatch wasn't | **HIGH** |
| `updated: 2026-06-12` | line 8 | `2026-06-14` (mtime) or `2026-06-18` (today) |  **2-6 days stale**; doesn't reflect uncommitted edits | **LOW** |
| `.omo/library/` directory | ~108-112 | Directory with cache files | **Does NOT exist** — cache integration is aspirational | **MED** |
| Intent Routing table | ~89-103 | Wired into dispatch code blocks | **Documentation-only** — Phase 1 dispatch blocks remain unconditionally static | **MED** |
| `task()` pseudo-code | ~20 occurrences | Platform-native dispatch API (`explore`/`research`) | **DSL concept, not real tool** — acceptable as convention across skill files | **MED** |
| `web_search` (allowed-tools) | line 14 | Confirm availability | Added in uncommitted diff; no documented use case in any lane prompt | **MED** |

**Freshness Recommendation**: **Weekly** until CRITICAL items resolved (L11-L15, lsp_* removal, dispatch protocol tools update). Then **monthly**.

**Historical note**: The same CRITICAL items (L11-L15, lsp_* phantom tools) have been flagged in every review since 2025-07-14 (6 cycles). Weekly review cadence has not triggered remediation. Recommendation should shift from process-based ("review more often") to constraint-based ("cap XL at 10 lanes until L11-L15 defined").

---

## Devil's Advocate Challenge (R6)

### R2 Challenge: Gate Completeness
- **Assigned score**: 72/100
- **R6 proposed**: 58/100
- **R6 argument**: M5, S2, P1, P2, P3 are structurally documented in Risk Register but have zero operational enforcement — no data-collection lane (M5), no Waves verification step (S2), composite-only adversarial review (P1-P3). Intent Routing adds a documentation layer without touching dispatch. The plan scores 5/11 fully-wired gates = 45%, not 72%.
- **Verdict**: PARTIALLY AGREE. R6 is correct that 5 gates are template-only or weak. But the Risk Register IS meaningful structural coverage for a PLANNER — the plan output documents the gate even if the skill doesn't auto-enforce it. **Score sustained at 72** (not 80 from prior reviews — the 8-point drop accounts for the documentation-to-execution gap that prior reviews underweighted).

### R3 Challenge: Parallelism
- **Assigned score**: 55/100
- **R6 proposed**: 40/100
- **Argument**: XL scale broken for 6 cycles. Phase 2 "parallel" label is misleading. Wave parallelism is documentation-only. 60% of parallelism surface is broken, misleading, or aspirational.
- **Verdict**: AGREE on severity of XL being broken, but **score sustained at 55**. XS and M (the common cases) work correctly. Phase 1 batch-fire, Phase 4 reviewer dispatch, and lane independence are solid. The 55 reflects ~55% functional parallelism surface.

### R4 Challenge: Cost Efficiency
- **Assigned score**: 60/100
- **R6 proposed**: 45/100
- **Argument**: Token undercount (1.66×), fictional cache savings, unguarded subagent spend, multi-feature silent multiplier, dead frontmatter aliases.
- **Verdict**: PARTIALLY AGREE. The token undercount isn't 3.6× as claimed in prior reviews (that figure conflated subagent API tokens with orchestrator tokens incorrectly — subagent tokens are billed separately and don't threaten the orchestrator window). The real issue is that the 115K guard triggers false-positive "split plan" decisions. **Score sustained at 60** — good routing design, sloppy documentation.

### Biggest Blind Spot (R6)
> **"The uncommitted changes update the frontmatter to use platform-native tool names but leave the dispatch protocol and all lane prompts using legacy names — creating a NEW class of bug where the skill appears platform-compatible but fails at runtime."**

**Validated**: The frontmatter `allowed-tools` lists `search_content`, `search_files`, `list_directory`, `directory_tree`, `run_command`; the dispatch protocol at ~159 still lists `grep`, `ls`, `bash`, `lsp_definition`, `lsp_hover`, `lsp_references`. Subagents dispatched with these tools would fail. This is a **regression risk** introduced by the partial uncommitted fixes. The cross-platform note says "run `skills/install.sh` to auto-convert" but `install.sh` may not handle tool-name conversion in dispatch protocol code blocks.

---

## Cross-Reference Escalations (Phase 1)

| # | Finding | Severity | Details |
|---|---|---|---|
| E1 | **Performance intent creates 3-gate coverage black hole** | **HIGH** | When user signals Performance intent, Routing table skips L8 (Security) AND Reviewer B (Security). This means S1 (dataFlow), S2 (auth), S3 (injection) have ZERO data-collection AND ZERO adversarial review for perf tasks. A Performance task touching auth middleware or data transformation would have no security gate coverage. R2's gate matrix doesn't subtract for this conditional gap. |
| E2 | **Context Anchor SUCCESS enforces only 4/11 gates** | **HIGH** | The `--completion-promise` derives from Context Anchor SUCCESS, which has thresholds for M1/M2/M4/P3 only. M3, M5, S1-S3, P1-P2 exist in Risk Register but are unenforceable at execution time. The downstream executor can never verify 7/11 gates. |
| E3 | **Frontmatter-dispatch tool mismatch creates runtime failure** | **HIGH** | Frontmatter uses platform-native tool names; dispatch protocol uses legacy names (`grep`/`ls`/`bash`). Subagents would fail at dispatch with unrecognized tool errors. The "install.sh conversion" claim is unverified. |
| E4 | **R2 methodology conflates structural docs with operational wiring** | **MED** | 5/11 gates marked TEMPLATE-ONLY or WEAK in prior reviews were not penalized in scoring. A Risk Register row ≠ end-to-end gate enforcement. R2 needs to differentiate "documented" from "wired." |

---

## Recommendations

### Critical (score impact >10 points)
| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| C1 | **L11-L15 prompts undefined — XL scale non-functional** | ~191-193 | Define L11_PROMPT through L15_PROMPT with full 4-section structure (context + action + RETURN EXACTLY + format), OR cap XL at 10 lanes + 5 reviewers and remove the 15-lane claim from Scale Classification | **Heavy** |
| C2 | **`lsp_definition`, `lsp_hover`, `lsp_references` phantom tools** | lines 14, ~159 | Remove from BOTH frontmatter `allowed-tools` AND dispatch protocol tools list. Update L3/L8 lane prompts that reference lsp_* to use alternative discovery methods (`search_content` for type definitions). | **Medium** |
| C3 | **Dispatch protocol tools mismatch — frontmatter updated, dispatch left with legacy names** | ~159 | Update dispatch protocol tools list to `["read_file","search_content","search_files","glob","list_directory","directory_tree","run_command","web_fetch"]`. Remove `lsp_*`, `grep`, `ls`, `bash`. | **Light** |

### High (score impact 5-10 points)
| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| H1 | **RVA-RVE use `RETURN:` not `RETURN EXACTLY:`** | ~604-705 | Standardize all 5 reviewer prompts to `RETURN EXACTLY:`. | **Light** |
| H2 | **M-scale reviewer count: "1" vs "3"** | ~133 vs ~593 | Unify to "3" in Scale Classification table. Add M-scale conditional reviewer dispatch block (A, B, C only). | **Light** |
| H3 | **XL-scale reviewer count: "triple review" vs "5"** | ~134 vs ~593 | Unify to "5" in Scale Classification table. | **Light** |
| H4 | **Token estimates undercounted (70K vs 116K)** | ~140-149 | Update documented estimate to ~116K. Add note: "Subagent API overhead (~2K per dispatch) pushes realistic total above the documented estimate. The 115K guard protects the orchestrator context window, not subagent API spend." | **Light** |
| H5 | **Multi-feature mode cost undocumented** | ~35-41 | Add: `> **Cost**: Each feature runs full Phase 1-5 independently. N features = N× single-feature cost. Use single-plan mode for dependent features.` | **Light** |
| H6 | **Phase 2 "parallel batch" label misleading** | ~404 | Relabel: "Sequential Verification Checklist" or add note: "These checks are sequential by necessity; cross-references depend on prior verification results." | **Light** |
| H7 | **Performance intent voids S-gate coverage** | ~95-103 | Add note in Intent Routing: "⚠️ Performance intent skips L8 and Reviewer B — S1/S2/S3 gates rely on Risk Register entries only. For security-sensitive performance work, override with `--force-security-gates`." OR route Performance to keep RVB. | **Medium** |

### Medium (score impact 2-5 points)
| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| M1 | **24 code blocks lack language markers** | Multiple | Add `bash`, `yaml`, `markdown`, `text` markers to all bare ``` fences. | **Light** |
| M2 | **M5 dead-code — no cross-reference step** | ~404-416 | Add to Phase 2: "Cross-reference L1 exports against L2 caller counts — flag any export with 0 callers as M5 dead-code candidate." | **Light** |
| M3 | **S2 auth `curl → 401` not in Waves template** | ~484-510 | Add to Wave 4 (Hardening): `- [ ] Auth gate: verify all entry points return 401 for invalid auth (S2)` | **Light** |
| M4 | **RVC_PROMPT P-gates composite** | ~648 | Split composite "P1~P3" bullet into 3 per-gate checks: "P1: No N+1 queries?", "P2: No unbounded collections?", "P3: p95 latency met?" | **Light** |
| M5 | **Context Anchor SUCCESS omits 7/11 gate thresholds** | ~454-461 | Add M3, M5, S1, S2, S3, P1, P2 thresholds to SUCCESS template, or add note: "Additional gate thresholds in Risk Register." | **Medium** |
| M6 | **`.omo/library/` cache directory doesn't exist** | ~108-112 | Either create directory + implement cache generation in blackcow-librarian, OR mark as "FUTURE" with note: "Cache integration planned but not yet implemented — Phase 0 always falls through to legacy discovery." | **Medium** |
| M7 | **`deepseek-v4-lite` model name unconfirmed** | line 9 | Verify against current provisioning. Update to confirmed model name or generic `budget-model`. | **Light** |
| M8 | **`web_search` added without documented use case** | line 14 | Document which lane uses `web_search` (L6 dependency audit uses `web_fetch` directly), or remove from allowed-tools. | **Light** |

### Low (score impact <2 points)
| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| L1 | **Unused `model_tiers` aliases** — `quick`, `deep`, `ultrabrain` | lines 11-13 | Remove or document as reserved for future use. | **Light** |
| L2 | **L7 omitted from cost-routing table** | ~144 | Update: "budget tier for lanes L1, L4, L5, L7, L10". | **Light** |
| L3 | **`updated` field stale** | line 8 | Bump to reflect actual last-modified date, or automate via git hook. | **Trivial** |
| L4 | **11 inter-phase serial gates unacknowledged** | — | Add note in Context Budget: "Inter-phase serialization is architecturally necessary; parallelism lives inside Phase 1 and Phase 4 batch dispatches." | **Light** |
| L5 | **`model_tiers` non-standard frontmatter field** | line 8 | Document as extension or migrate to standard skill metadata format. | **Light** |
| L6 | **Wave DAG has no executable dispatch** | ~490-510 | Add note: "Wave DAG is consumed by blackcow-loop (the executor); this skill only generates the plan structure." | **Light** |

---

## Evolution Readiness

- **Safe to auto-evolve?**: **YES — with constraints.** Items C3, H1-H6, M1-M4, M7-M8, L1-L6 are safe for auto-evolution (lightweight, well-specified fixes).
- **NOT safe for auto-evolve**: C1 (L11-L15 needs architectural design — 5 new lane prompts), C2 (lsp_* removal affects L3/L8 lane prompt semantics), H7 (Intent Routing logic restructuring), M5 (SUCCESS template restructuring), M6 (directory/process creation).
- **Backup recommended before**: Dispatch protocol (~159), Scale Classification table (~131-134), RVA-RVE prompts (~604-705), L3/L8 lane prompts, Phase 2 (~404-416), Waves template (~484-510), Context Anchor SUCCESS (~454-461), frontmatter (~8-14).
- **Estimated evolution tokens**: ~15-20K for safe items (tools consistency, code block markers, label fixes, per-gate reviewer checks). ~40-55K for full remediation including L11-L15 definition and Intent Routing wiring.
- **Recommended approach**: 
  1. Commit current uncommitted changes (they're genuine improvements — cross-platform note, IntentGate, tool name updates)
  2. Auto-evolve safe items (C3, H1-H6, M1-M4, M7-M8, L1-L6) — est. ~18K tokens
  3. Manual design pass for C1, C2, H7, M5, M6 — est. ~45K tokens
  4. If L11-L15 cannot be designed, cap XL at 10 lanes + 5 reviewers and adjust Scale Classification

---

## Self-Review Guard

| Check | Result |
|---|---|
| **Is this a self-review?** | **NO.** Reviewing `blackcow-plan.md`, not `blackcow-skill-review.md`. No deterministic re-run required. |
| **R6 (Devil's Advocate) active?** | **YES.** Challenge provided for R2, R3, R4 with proposed alternative scores. |
| **Cross-reference lanes active?** | **YES.** XR1 and XR2 identified 4 escalations (E1-E4). |
| **Score trajectory consistent?** | Prior: 66.65 → 76.65 → 69 → 71.5 → 70.9 → 72.8. New: **63.25**. The drop reflects stricter operational-enforcement criteria and penalty for 6-cycle-unresolved CRITICALs — not score instability. |
