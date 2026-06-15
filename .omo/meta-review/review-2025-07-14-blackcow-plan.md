# Meta-Review: blackcow-plan

| Field | Value |
|---|---|
| **Reviewed** | 2025-07-14T23:00:00Z |
| **Reviewer** | blackcow-skill-review (Metis 大将) |
| **Skill Version** | 2.0.0 (frontmatter `updated: 2026-06-12`, git `9872e3f`) |
| **Skill Path** | `skills/blackcow-plan.md` (34,850 bytes, ~807 lines) |
| **Previous Score** | 76.65 (2026-06-14) → **0 of 15 recommendations addressed** |

## Overall Score

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| R1 Syntax & Structure | **65** | 15% | 9.75 |
| R2 Gate Completeness | **72** | 30% | 21.60 |
| R3 Parallelism Efficiency | **65** | 25% | 16.25 |
| R4 Cost Efficiency | **72** | 15% | 10.80 |
| R5 Staleness/Freshness | **55** | 15% | 8.25 |
| **TOTAL** | — | **100%** | **66.65** |

> **Score trajectory**: 76.65 → 66.65 (−10.0 pts). The decline is driven by (a) 0/15 prior recommendations remaining unresolved, (b) R6 adversarial audit revealing the `task()` dispatch pseudo-code convention has no enforcement mechanism, and (c) new findings around nested code-block breakage and IntentGate routing not reflecting detected intent. The skill's **design quality remains excellent**, but its **operational readiness has degraded** due to accumulated deferred maintenance.

---

## Dimension Details

### R1: Syntax & Structure — 65/100

**Strengths:**
- Valid YAML frontmatter with all required fields (`name`, `description`, `runAs`, `model`, `allowed-tools`, `version`, `updated`, `model_tiers`)
- Well-organized phase structure (Phase -1 through Phase 5 + Constraints), 21 level-2/3 headings
- All 10 L1-L10 lane prompts follow the canonical 4-section structure (Context → Action → RETURN EXACTLY → Format)
- All dispatch blocks consistently use `run_in_background=true, max_steps=N, model=tier`
- "RETURN EXACTLY" sections define clear numbered output schemas

**Issues:**

| # | File:Line | Issue | Severity |
|---|---|---|---|
| 1 | `skills/blackcow-plan.md:713-727` | **Nested code block breaks template rendering.** The outer ```` ```markdown ```` block contains an inner ```` ``` ```` at line 717. In standard Markdown, the inner fence **prematurely closes the outer block**, dumping the Parallelism Guide text (lines 723-726) raw outside any code fence. The plan template is corrupted. | **CRITICAL** |
| 2 | `skills/blackcow-plan.md:189,207-209` | **L11_PROMPT through L15_PROMPT are entirely undefined.** Only 10 of 15 advertised XL lane prompts exist. | **CRITICAL** |
| 3 | `skills/blackcow-plan.md:14` | `allowed-tools` uses kebab-case; the `install_skill` API parameter is camelCase `allowedTools`. Frontmatter parsers expecting `allowedTools` will get `null` — silently losing the tool authorization list. | **HIGH** |
| 4 | `skills/blackcow-plan.md:159` | Lane dispatch protocol's `tools` array uses legacy names: `grep` (→`search_content`), `ls` (→`list_directory`), `bash` (→`run_command`), `lsp_definition`/`lsp_references`/`lsp_hover` (→`get_symbols`/`find_in_code`). Platform Tool Mapping table documents the aliases, but subagents receive tool authorization by exact name — legacy names may be rejected. | **HIGH** |
| 5 | `skills/blackcow-plan.md:14,159` | Two conflicting tool lists: frontmatter `allowed-tools` (14 canonical tools + `web_search`) vs dispatch protocol `tools` array (9 legacy-name tools + unauthorized `lsp_*`). Dual source of truth. | **HIGH** |
| 6 | `skills/blackcow-plan.md:17` | `## Platform Tool Mapping` (H2) appears **before** `# blackcow-plan` (H1) at line 33. H1 should be the first heading. | MED |
| 7 | `skills/blackcow-plan.md:*` | **24 of 30 code blocks (80%) lack language markers** — bare ```` ``` ```` instead of ```` ```bash ```` or ```` ```markdown ````. | MED |
| 8 | `skills/blackcow-plan.md:185-203` | Dispatch calls use `task(description=...)` instead of `task(name=...)` as specified by the parent `blackcow-skill-review` syntax check. All 15 calls consistently use `description=` — this is a shared convention across all 6 blackcow skills. | LOW |

**R2 note on `task()`**: The dispatch pseudo-code uses `task()` as a convention shared across **all 6 skill files** (blackcow-plan, blackcow-loop, blackcow-qa, blackcow-skill-review, blackcow-skill-evolver, blackcow-librarian). On this platform, the orchestrator maps `task()` to `explore` / `research` per the Platform Tool Mapping table. This is a **system-wide convention**, not a skill-local defect. The R6 Devil's Advocate finding that "task() doesn't exist so all dispatch is inoperable" — while technically correct at the tool-API level — overstates the impact since the mapping is documented.

---

### R2: Gate Completeness — 72/100

**Gate Coverage Matrix:**

| Gate | Status | Evidence (file:line) | Assessment |
|---|---|---|---|
| **M1** spec-match | ⚠️ PARTIAL | Context Anchor SUCCESS (line 410), Gap Matrix M1 tag (line 449), Risk Register (line 471), RVA_PROMPT | **Self-referential failure**: skill advertises XL=15 lanes but only 10 prompts exist. Own spec-match rate = 67%. For XL invocations, M1 FAILS. |
| **M2** test-pass | ✅ COVERED | Context Anchor SUCCESS (line 410), Risk Register (line 472), L4_PROMPT (lines 316-340), RVA_PROMPT | Strong coverage with concrete `npm test -- --coverage` verification |
| **M3** regression | ✅ COVERED | Risk Register (line 473), Gap Matrix M3 tag (line 447), IntentGate Bug Fix class | Strong coverage. Risk register demands `0 regressions`. |
| **M4** lint-clean | ✅ COVERED | Context Anchor SUCCESS (line 410), Risk Register (line 474), IntentGate Quality class | Adequate with `npm run lint` verification |
| **M5** dead-code | ✅ COVERED | Risk Register (line 475), Gap Matrix M5 tag (line 450), IntentGate Feature class | Adequate with `grep for references` verification |
| **S1** dataFlow | ⚠️ DEGRADED | L3_PROMPT (lines 280-310), Risk Register (line 476), RVB_PROMPT | L3 structurally addresses S1, but dispatches with `lsp_*` tools absent from frontmatter `allowed-tools`. Operational capability compromised. |
| **S2** auth | ⚠️ DEGRADED | L8_PROMPT (lines 395-410), Risk Register (line 477), RVB_PROMPT | Same tool degradation as S1. L8 uses `grep` not `search_content`. |
| **S3** injection | ⚠️ DEGRADED | L8_PROMPT (lines 395-410), Risk Register (line 478), RVB_PROMPT | Same tool degradation as S1. |
| **P1** query | ⚠️ WEAK | L9_PROMPT (lines 355-380), Risk Register (line 479), RVC_PROMPT (single composite line at 636) | RVC gives P-gates a **single composite check** ("Will the resulting code meet P1~P3 thresholds?") vs RVA's **per-M-gate** scrutiny. Verification "Query count assertion" is vague — no concrete CLI. |
| **P2** memory | ⚠️ WEAK | L9_PROMPT (line 358), Risk Register (line 480), RVC_PROMPT (line 636) | Same weak RVC check. "Memory profiling" is not a concrete verification command. |
| **P3** latency | ⚠️ WEAK | L9_PROMPT (lines 361-362), Context Anchor SUCCESS (line 410), Risk Register (line 481), RVC_PROMPT (line 636) | Best P-gate evidence (Context Anchor p95 field), but still weak adversarial review. "Load test" is vague. |

**Critical gaps:**
1. **IntentGate detects intent but doesn't change dispatch routing.** When "Security" is detected, it claims "All S-gates double-weighted, forced pro tier" — but the dispatch protocol is static with no conditional routing. L3 (budget) and L9 (budget) stay on budget tier regardless. IntentGate is **documentation, not mechanism**.
2. **Scale Classification table contradiction**: M scale says "1 reviewer" (line 130) but Phase 4 Reviewer Selection says "3 reviewers" (line 570). Executors see conflicting instructions.
3. **XS scale skips all adversarial gate verification** — gates are template-documented but never challenged.
4. **XL scale: L11-L15 missing** → no extended S/P gate data collection for largest projects.

---

### R3: Parallelism Efficiency — 65/100

**Strengths:**
- All Phase 1 and Phase 4 dispatch calls use `run_in_background=true` — 100% compliance
- Batch-and-wait pattern correct: dispatch-all-then-await-all in both Phase 1 and Phase 4
- All 10 defined lanes (L1-L10) are genuinely independent — no hidden data dependencies between them
- No overlap issues found — lanes are well-scoped with distinct responsibilities
- L1 vs L2 overlap is intentional cross-verification (layer tags), not wasted work

**Issues:**

| # | File:Line | Issue | Severity |
|---|---|---|---|
| 1 | `skills/blackcow-plan.md:189,207-209` | **XL parallelism tier is broken.** Skill advertises 15 lanes (XS:5, M:10, XL:15) but only 10 prompts exist. L11-L15 dispatch would send subagents with **no prompt text** → hallucination/error at runtime. 5 of 15 lanes are undefined. | **CRITICAL** |
| 2 | `skills/blackcow-plan.md:404-415` | Phase 2 header says "run these in **ONE parallel batch**" but lists 6 sequential inline grep/read_file operations. No `task()` dispatch, no parallelism. Language is misleading — inflates perceived parallelism. | MED |
| 3 | `skills/blackcow-plan.md:582-586` | Phase 4 dispatch block always shows all 5 reviewers. For M scale (3 reviewers), there's no separate dispatch block — the planner must manually select which 3 of 5 to use. No guidance on which reviewers to drop. | MED |
| 4 | `skills/blackcow-plan.md:560` | Phase 4 title "Quintuple Adversarial Review" over-promises — only XL gets 5 reviewers; M gets 3; XS gets 0. | LOW |
| 5 | `skills/blackcow-plan.md:48,55` | Multi-feature mode: "Feature Dependency Graph" determines cross-feature deps, then claims each per-feature plan runs "independently." If feature B depends on A, B's plan CANNOT be independent — A's outputs are B's inputs. Cross-feature context passing is undocumented. | MED |

**XL Broken Detail:**
When XL scale is invoked:
1. Phase 0 correctly classifies as XL, sets `lanes=15`
2. Phase 1 reaches the XL prose description (line 207): "Additional deep-dive lanes dispatched with same protocol, model=pro for L11/L12..."
3. **No L11_PROMPT through L15_PROMPT exist anywhere.** Verified via `search_content` across all 7 skill files — zero matches.
4. The orchestrator must **improvise** all 5 prompts with no guidance.
5. Phase 5 plan template's "Codebase Survey (10-Lane Summary)" table has only 10 rows — XL output will pack 15 lanes into a 10-slot table, truncating or breaking.

---

### R4: Cost Efficiency — 72/100

**Model-Tier Routing:**

| Lane | Tier | Verdict |
|---|---|---|
| L1, L4, L5, L7, L10 | budget | ✅ Correct — discovery/read tasks |
| L2, L3, L6, L8, L9 | pro | ✅ Correct — analysis/security tasks |
| L8 | pro (hardcoded) | ✅ Correct — security always pro |
| Phase 4 Reviewers A-E | pro | ✅ Correct — adversarial review is analysis-critical |
| Phase 2 Cross-Check | inline (no subagent) | ✅ Optimal — zero subagent overhead |
| **Orchestrator** | **always pro** | ⚠️ Could use budget for trivial XS runs (~$0.01 savings per trivial invocation) |

**Cost Estimates (including subagent context):**

| Scale | Est. Total API Tokens | Est. Cost | Key Drivers |
|---|---|---|---|
| **XS** (5 lanes, no review) | ~180K | ~$0.02 | 3 budget lanes + 2 pro lanes + orchestrator context |
| **M** (10 lanes + 3 reviewers) | ~340K | ~$0.05 | 5 budget + 5 pro lanes + 3 pro reviewers + orchestrator |
| **XL** (15 lanes + 5 reviewers) | ~550K | ~$0.09 | 7 budget + 8 pro lanes + 5 pro reviewers + orchestrator |

> Assumes DeepSeek v4 pricing: budget input=$0.07/M, pro input=$0.14/M, output=$0.28/M. Costs may drop ~30-40% if codebase files are context-cached from prior runs.

**Issues:**

| # | Issue | Severity |
|---|---|---|
| 1 | **Context Budget table underreports by 3-6×.** The table (lines 140-145) claims M-scale ≈ 70K tokens but only counts orchestrator-context tokens. Total API consumption with subagent contexts is ~340K. The split-to-two-plans threshold at 115K would fire on **every M and XL invocation** — making two-plan splits the norm, not the exception. | **HIGH** |
| 2 | **Phase 4 reviewer context is off by ~30× for XL.** The table estimates Phase 4 ≈ 15K, but 5 reviewers × ~95K full plan context = 475K tokens just for review input. This alone would trigger the split threshold. | **HIGH** |
| 3 | **Dead `model_tiers` aliases:** `quick`, `deep`, `ultrabrain` are defined (lines 17-19) but **never referenced** in any dispatch command. A user trying `--model-tier=ultrabrain` would silently default to `auto` since the tier parser (line 137) only accepts `auto|budget|pro`. UX bug — no error, wrong model. | MED |
| 4 | **`--force-pro` doesn't auto-detect security projects.** IntentGate detects Security intent but doesn't auto-force pro tier across all lanes. L3 (budget) and L9 (budget) stay on budget tier even when the user has a security-critical task. | MED |
| 5 | **No cost telemetry.** Skill doesn't log actual token consumption — no feedback loop to validate or refine budget estimates. | MED |

**Consolidation Opportunity:**
- **Merge L4 (Test Topography) + L7 (Git Archaeology)**: Both run git/bash commands and grep for patterns. L4's "recent test changes" and L7's "hot files" overlap in their target code regions. Estimated savings: ~$0.003-0.005 per M invocation (~10-15% subagent cost reduction). Low risk — same toolset, same target files.

---

### R5: Staleness — 55/100

**Age:** 2.6 days since git commit (2026-06-12). File mtime: 2026-06-14. The file is **chronologically fresh** but **content-stale** — 0 of 15 previous review recommendations have been addressed.

**Unresolved Previous Findings (100% regression):**

| # | Finding | Severity | Status |
|---|---|---|---|
| **CR1** | XL broken — L11-L15 undefined | CRITICAL | ❌ UNRESOLVED |
| **CR2** | Tool names mismatch (3 conflicting lists) | CRITICAL | ❌ UNRESOLVED |
| **H1** | LSP tools unauthorized in frontmatter | HIGH | ❌ UNRESOLVED |
| **H2** | P-gates weak adversarial review | HIGH | ❌ UNRESOLVED |
| **H3** | XS skips Phase 4 entirely | HIGH | ❌ UNRESOLVED |
| **M1** | Context budget table misleading | MED | ❌ UNRESOLVED |
| **M2** | No cost telemetry | MED | ❌ UNRESOLVED |
| **M3** | `web_search` phantom tool | MED | ✅ FALSE POSITIVE — `web_search` IS a valid tool |
| **L1** | 3 code blocks missing language markers | LOW | ❌ UNRESOLVED |
| **L2** | `RETURN:` not `RETURN EXACTLY:` (RVA-RVE) | LOW | ❌ UNRESOLVED |
| **L3** | Dead `model_tiers` aliases | LOW | ❌ UNRESOLVED |
| **L4** | Phase 2 "parallel batch" language | LOW | ❌ UNRESOLVED |
| **L5** | "Quintuple" title over-promises | LOW | ❌ UNRESOLVED |

**New staleness findings (not in previous review):**

| # | Reference | File:Line | Expected | Actual | Severity |
|---|---|---|---|---|---|
| 1 | `deepseek-v4-lite` | lines 9,11,12,13,140 | `deepseek-v4-flash` (current lite-tier name) | `deepseek-v4-lite` — model name may not match provisioned tier | **HIGH** |
| 2 | `.omo/library/` | line 102 | Cache directory should exist | **Does not exist** — cache-load always falls through to legacy discovery | MED |
| 3 | Nested code block breakage | line 713-727 | Valid markdown template | Broken template — inner ``` closes outer fence | **HIGH** (new) |
| 4 | `allowed-tools` vs `allowedTools` | line 14 | CamelCase key expected by `install_skill` | kebab-case used — parser mismatch | **HIGH** (new) |

**Freshness Recommendation:** **Expedited refresh immediately** — before any XL-scale invocation. Monthly review schedule thereafter. If hosting platform changes tool/model names, trigger unscheduled refresh within 24 hours.

---

## Cross-Reference Findings

### Contradictions Detected

| # | Lanes | Finding | Severity |
|---|---|---|---|
| **C1** | R2 ↔ R3 | R2 says S/P gates are "COVERED structurally." R3 confirms L11-L15 undefined → XL can't collect extended S/P data. **Paper coverage ≠ operational coverage for XL.** | HIGH |
| **C2** | R2 ↔ R5 | R2 scores gate coverage at 72. R5 shows 0/15 previous recommendations resolved — including CR1 (XL broken), H1 (LSP tools), H2 (P-gates). **Score reflects design intent, not runtime readiness.** | HIGH |
| **C3** | R1 internal | Two conflicting tool lists: frontmatter `allowed-tools` (14 canonical) vs dispatch protocol `tools` (9 legacy + unauthorized `lsp_*`). **Dual source of truth for tool authorization.** | HIGH |
| **C4** | R3 ↔ R2 | R3 Phase 2 "parallel batch" is sequential. R2 uses this Phase 2 to verify gate data. If Phase 2 is a bottleneck, all gate verification is delayed. In practice, Phase 2 is cheap O(1) so impact is LOW. | LOW |

### Escalations

| # | Issue | Spans | Severity |
|---|---|---|---|
| **E1** | **Tool Surface Integrity Failure** — 3 independent tool lists disagree. Frontmatter has `search_content`/`list_directory`/`run_command`. Dispatch protocol uses `grep`/`ls`/`bash`. Lane prompts mix both. No lane can execute with correct tool access as written. | R1, R2, R3, R5 | **CRITICAL** |
| **E2** | **XL Scale Path Broken** — L11-L15 prompts undefined. Skill advertises 15-lane capability but only implements 10. Any XL invocation dispatches 5 subagents with no prompt text. | R2, R3, R5 | **CRITICAL** |
| **E3** | **Design-Time vs Runtime Divergence** — R2 checks for *presence* of gate-addressing language, not *mechanism*. L3→S1 covered on paper but L3 can't access `lsp_*` tools. IntentGate detects Security but doesn't change routing. Coverage is aspirational, not operational. | R2, R5 | HIGH |
| **E4** | **All 6 skills share `task()` convention** — blackcow-plan, blackcow-loop, blackcow-qa, blackcow-skill-review, blackcow-skill-evolver, blackcow-librarian all use `task()` dispatch pseudo-code. Platform mapping says `task → explore / research`. This is a **system-wide convention** — not a bug unique to blackcow-plan — but it creates fragility if the mapping changes. | R1, R3, R4 | MED |
| **E5** | **IntentGate is documentation, not routing** — Security intent detected but dispatch stays static. P-gates in RVC get single composite line vs per-gate scrutiny. These two facts together mean security-critical and performance-critical projects get no stronger verification than general features. | R2, R4 | MED |

---

## Devil's Advocate Summary (R6)

| Challenge | Prev Score | Proposed | Verdict |
|---|---|---|---|
| R2 Gate Completeness | 78 | 58 | **Partially sustained.** `task()` dispatch IS a shared convention across all skills, not a unique failure. But IntentGate not routing + P-gate single-line review + M1 self-referential failure (67% spec-match for XL) are real. Score adjusted to 72. |
| R3 Parallelism | 78 | 55 | **Partially sustained.** XL is truly broken (5/15 prompts missing). Phase 2 "parallel" label is misleading. But all Phase 1/Phase 4 `run_in_background=true` dispatches are correct for the 10 defined lanes. Score adjusted to 65. |
| R4 Cost Efficiency | 80 | 62 | **Partially sustained.** Phase 4 token estimate off by ~30× for XL is a real finding. Dead aliases are MED not LOW. But model-tier routing is correct for all defined lanes, and consolidation opportunities are marginal. Score adjusted to 72. |
| **Biggest Blind Spot** | — | — | **The `task()` dispatch pseudo-code convention is undocumented as a convention.** All 6 skill files use it, the Platform Tool Mapping documents `task → explore/research`, but no skill explicitly states "`task()` is pseudo-code; the orchestrator maps it to available subagent tools." If a new executor agent doesn't know this convention, it would fail silently on every dispatch. |

---

## Recommendations

### 🔴 Critical

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **CR1** | **XL scale broken — L11-L15 prompts undefined** | `skills/blackcow-plan.md:189,207-209` | Define L11_PROMPT through L15_PROMPT following the existing 4-section structure: L11 Security Deep-Dive (pro), L12 Performance Deep-Dive (pro), L13 Documentation Audit (budget), L14 i18n/l10n Audit (budget), L15 Accessibility Audit (budget). Also add XL dispatch block with concrete `task()` calls. Update Phase 5 plan template to accommodate 15 lane rows. | Heavy (~250 lines new content) |
| **CR2** | **Tool names mismatch across 3 locations** | `skills/blackcow-plan.md:14,159, and individual lane prompts` | (a) Change dispatch protocol `tools` array: `grep→search_content`, `ls→list_directory`, `bash→run_command`. (b) Either add `lsp_definition`/`lsp_references`/`lsp_hover` to frontmatter `allowed-tools` OR remove them from dispatch protocol (recommend: add to frontmatter, they're standard LSP tools). (c) Update individual lane prompts (L2, L3, L7, L8, L9, L10) to reference canonical tool names. | Medium (~15 substitutions) |
| **CR3** | **Nested code block breaks plan template** | `skills/blackcow-plan.md:713-727` | Restructure the ```` ```markdown ```` block to avoid nested fences. Either: (a) use 4-backtick outer fence, or (b) indent the inner shell command instead of fencing it, or (c) split into two separate code blocks. | Light |

### 🟠 High

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **H1** | **IntentGate doesn't change dispatch routing** | `skills/blackcow-plan.md:78-96,149,173-203` | Add conditional dispatch logic: when IntentClass=Security, force all lanes to pro (not just L8) and dispatch RVB as first reviewer. When IntentClass=Performance, force L9 to pro and dispatch RVC as first reviewer. | Medium |
| **H2** | **P-gates get single composite check from RVC** | `skills/blackcow-plan.md:636-676` (RVC_PROMPT) | Expand RVC_PROMPT to include per-gate P1/P2/P3 checks with explicit thresholds from Risk Register (No N+1, No unbounded growth, p95 < target). Mirror RVA's per-M-gate structure. | Light |
| **H3** | **Context Budget table underreports by 3-6×** | `skills/blackcow-plan.md:140-145` | Add "Total API Token Estimate" column showing subagent context. Relabel existing column as "Orchestrator Context." Update split-to-two-plans threshold logic to account for subagent token consumption. | Light |
| **H4** | **Phase 4 reviewer context estimate off by ~30× for XL** | `skills/blackcow-plan.md:140-145,582-586` | Fix the Phase 4 row in the Context Budget table: XL = 5 reviewers × ~95K plan = ~475K, not ~15K. Re-evaluate whether two-plan splits are needed for XL. | Light |
| **H5** | **Scale table contradicts Phase 4 reviewer count** | `skills/blackcow-plan.md:130,570` | Align the Scale Classification table (M: "1 reviewer" → "3 reviewers") with Phase 4 Reviewer Selection (M: "A, B, C (3)"). | Trivial |

### 🟡 Medium

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **M1** | **Dead `model_tiers` aliases confuse users** | `skills/blackcow-plan.md:17-19` | Either remove `quick`/`deep`/`ultrabrain` aliases, or add parsing support in Model-Tier Cost Routing (line 137) and document them. If kept, `ultrabrain` should map to reviewers, `deep` to analysis lanes, `quick` to simple edits. | Light |
| **M2** | **`--force-pro` doesn't auto-detect security projects** | `skills/blackcow-plan.md:149,78-88` | Wire IntentGate Security detection to auto-set `--force-pro`. When IntentClass=Security, all lanes run pro regardless of `--model-tier`. | Light |
| **M3** | **Multi-feature cross-feature context undocumented** | `skills/blackcow-plan.md:48-55` | Document how dependent features share context: does feature B re-run Phase 1 from scratch or read feature A's plan file? Specify the mechanism. | Light |
| **M4** | **No cost telemetry in output template** | `skills/blackcow-plan.md:726+` | Add `total_tokens_consumed` and `estimated_cost` fields to the Phase 5 plan template. Log actual vs estimated for trend analysis. | Light |
| **M5** | **`.omo/library/` doesn't exist — cache always falls through** | `skills/blackcow-plan.md:100-114` | Either create the library directory structure at skill install time, or make cache-load gracefully degrade the staleness check (currently `read_file` on nonexistent paths will error). | Light |

### 🟢 Low

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **L1** | 24 of 30 code blocks (80%) lack language markers | throughout | Add `bash`, `markdown`, `python`, `yaml` language markers to bare ```` ``` ```` blocks. | Trivial |
| **L2** | RVA-RVE use `RETURN:` not `RETURN EXACTLY:` | lines 594,615,636,655,676 | Align to `RETURN EXACTLY:` for consistency with L1-L10 prompts. | Trivial |
| **L3** | Phase 2 "parallel batch" language misleading | line 404 | Change to "sequential cross-check" or dispatch 2-3 parallel verification subagents. | Trivial |
| **L4** | "Quintuple Adversarial Review" title over-promises | line 560 | Change to "Adversarial Review (scale-gated: XS=0, M=3, XL=5)". | Trivial |
| **L5** | H2 "Platform Tool Mapping" before H1 title | lines 17,33 | Move H1 to be the first heading (line 17), or move the Platform Tool Mapping section to after the H1. | Trivial |
| **L6** | `allowed-tools` kebab-case vs `allowedTools` camelCase | line 14 | Verify whether the `install_skill` API expects kebab-case or camelCase. If camelCase, rename to `allowedTools`. | Trivial |
| **L7** | M dispatch block missing — only 5-reviewer block shown | lines 582-586 | Add explicit M dispatch block: 3 `task()` calls for Reviewers A, B, C. | Trivial |

---

## Evolution Readiness

| Assessment | Detail |
|---|---|
| **Safe to auto-evolve?** | **YES — with constraints.** The 3 CRITICAL fixes are mechanical: L11-L15 prompt authoring (content creation), tool name substitution (find-and-replace), and nested code block repair (structural fix). None change the skill's architecture or API. |
| **Backup recommended before** | L11-L15 prompt additions (new content, lines 393+), tool name replacements across ~15 references in dispatch protocol + ~10 in lane prompts, nested code block restructure at line 713-727. |
| **Estimated evolution tokens** | ~35K (5 new ~40-line prompt sections + systematic tool-name find-and-replace across ~25 references + frontmatter updates + nested code block repair + M dispatch block). |
| **Post-evolution re-review** | **Recommended.** Verify: (a) L11-L15 prompts follow the 4-section structure, (b) tool names consistent across all three locations (frontmatter, dispatch protocol, individual prompts), (c) plan template accommodates 15 lane rows, (d) nested code block renders correctly. |
| **Cross-skill impact** | CR2 (tool name alignment) should be applied to `blackcow-loop.md`, `blackcow-qa.md`, `blackcow-librarian.md`, `blackcow-skill-review.md`, and `blackcow-skill-evolver.md` as well — all 6 skill files share the same legacy tool names in their dispatch protocols. |

---

## Summary

`blackcow-plan.md` is a **well-architected planner skill with excellent design quality** (consistent structure, correct dispatch patterns, full 11-gate taxonomy awareness, adaptive lane scaling, cost-tier routing) that suffers from **accumulated deferred maintenance**:

1. **XL scale is broken** — 5 of 15 lane prompts are undefined (same as previous review, still unresolved)
2. **Tool names are stale** — `grep`/`ls`/`bash`/`lsp_*` in dispatch protocol vs canonical `search_content`/`list_directory`/`run_command` in frontmatter (same as previous review, still unresolved)
3. **0 of 15 previous review recommendations addressed** — no git commits since the 2026-06-14 review
4. **New findings**: nested code block breaks plan template rendering, IntentGate doesn't change dispatch routing, Phase 4 token estimate off by ~30× for XL
5. **Positive correction**: `web_search` IS a valid tool (previous review's CR2 finding about it was a false positive)

The skill's **design intent remains exceptional** — it has all the right ideas (intent detection, adaptive scaling, adversarial review, cost routing, context budgeting). But the **execution gaps** have widened since the last review. The fixes are well-scoped and mechanical. Post-fix target score: **85-90**.
