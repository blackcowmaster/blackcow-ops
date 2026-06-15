# Meta-Review: blackcow-plan

| Field | Value |
|---|---|
| **Reviewed** | 2026-06-14T22:35:42Z |
| **Reviewer** | blackcow-skill-review (Metis 大将) |
| **Skill Version** | 2.0.0 (updated 2026-06-12, git 9872e3f) |
| **Skill Path** | `skills/blackcow-plan.md` (34,117 bytes, 807 lines) |

## Overall Score

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| R1 Syntax & Structure | **85** | 15% | 12.75 |
| R2 Gate Completeness | **78** | 30% | 23.40 |
| R3 Parallelism Efficiency | **78** | 25% | 19.50 |
| R4 Cost Efficiency | **80** | 15% | 12.00 |
| R5 Staleness/Freshness | **60** | 15% | 9.00 |
| **TOTAL** | — | **100%** | **76.65** |

> **Adversarial adjustment applied.** R2/R3/R4 scores were lowered from 92/93/89 to 78/78/80 based on R6 Devil's Advocate challenges and XR1/XR2 cross-reference findings. The primary driver: the skill has **structural completeness on paper** but **operational failures at runtime** due to tool mismatches and undefined XL-scale prompts.

---

## Dimension Details

### R1: Syntax & Structure — 85/100

**Strengths:**
- 807 lines, 21 level-2 headings, all consistent and well-numbered (Phase -1 through Phase 5)
- YAML frontmatter valid with all required fields (`name`, `description`, `runAs`, `model`, `allowed-tools`)
- All 10 `L*_PROMPT` sections follow the canonical 4-section structure (Context → Action → RETURN EXACTLY → Format)
- All `task()` dispatch blocks have correct syntax with `run_in_background=true`, `max_steps`, `model` parameters
- "RETURN EXACTLY" sections define clear numbered output schemas with file:line evidence requirements

**Issues:**

| # | File:Line | Issue | Severity |
|---|---|---|---|
| 1 | `skills/blackcow-plan.md:14` | `web_search` in `allowed-tools` — tool does not exist in current environment (only `web_fetch` is available) | HIGH |
| 2 | `skills/blackcow-plan.md:14,159` | `lsp_definition`, `lsp_references`, `lsp_hover` in lane dispatch tools (line 159) but **NOT** in frontmatter `allowed-tools` (line 14). Subagents may be refused these tools. | HIGH |
| 3 | `skills/blackcow-plan.md:159` | Legacy tool names in dispatch protocol: `grep` → should be `search_content`, `ls` → `list_directory`, `bash` → `run_command` | MED |
| 4 | `skills/blackcow-plan.md:100,134,787` | 3 code blocks missing language markers (bare ` ``` ` instead of ` ```bash `) | LOW |
| 5 | `skills/blackcow-plan.md:594,615,636,655,676` | RVA-RVE reviewer prompts use `RETURN:` instead of `RETURN EXACTLY:` — inconsistent with L1-L10 lane prompts | LOW |

---

### R2: Gate Completeness — 78/100 *(originally 92, downgraded by adversarial review)*

**Gate Coverage Matrix:**

| Gate | Status | Evidence | Adversarial Assessment |
|---|---|---|---|
| **M1** spec-match | ⚠️ PARTIAL | Context Anchor, Gap Matrix, Risk Register all reference M1. **But** the skill's own spec (15 XL lanes) doesn't match its implementation (10 prompts defined). Self-referential M1 failure. | **Demoted from COVERED** — the plan template works but the skill itself fails spec-match for XL scale. |
| **M2** test-pass | ✅ COVERED | IntentGate, Context Anchor, Risk Register, RVA review | Strong coverage |
| **M3** regression | ✅ COVERED | IntentGate, Gap Matrix, Risk Register, RVA review | Strong coverage |
| **M4** lint-clean | ✅ COVERED | IntentGate, Context Anchor, Risk Register, RVA review | Adequate |
| **M5** dead-code | ✅ COVERED | IntentGate, Gap Matrix, Risk Register, RVA review | Adequate |
| **S1** dataFlow | ⚠️ DEGRADED | L3 lane + RVB review architecturally sound, but L3 operates with degraded tooling (missing `lsp_*` in parent `allowed-tools`, wrong tool names `grep`/`ls`) | **Demoted from COVERED** — structural design correct, operational capability compromised |
| **S2** auth | ⚠️ DEGRADED | L8 lane (pro, forced) + RVB review. Same tool mismatch affects L8. | Same tool degradation as S1 |
| **S3** injection | ⚠️ DEGRADED | L8 lane + RVB review. Same tool mismatch. | Same tool degradation as S1 |
| **P1** query | ⚠️ WEAK | L9 lane + RVC single composite line. Per-gate scrutiny absent. | Coverage exists but is qualitatively much weaker than M-gates |
| **P2** memory | ⚠️ WEAK | L9 lane + RVC single composite line. | Same as P1 |
| **P3** latency | ⚠️ WEAK | L9 lane + Context Anchor + RVC single composite line. | Same as P1 |

**Key gaps:**
- **XS scale skips Phase 4 entirely** — zero adversarial gate verification for small tasks. The risk register still documents gates, but no reviewer challenges them.
- **P-gates receive single-line composite check** from RVC vs. M-gates' dedicated per-gate scrutiny from RVA.
- **S-gates siloed in single reviewer** (RVB) — no cross-validation unlike M-gates which span RVA+RVD.
- **L11-L15 undefined** means XL-scale plans cannot collect extended security/performance data, weakening S/P gate coverage for the largest projects.

---

### R3: Parallelism Efficiency — 78/100 *(originally 93, downgraded by adversarial review)*

**Strengths:**
- All Phase 1 and Phase 4 `task()` calls use `run_in_background=true` — 100% compliance
- Batch-and-wait pattern correct: dispatch-all-then-await-all in both Phase 1 and Phase 4
- All lanes truly independent (parameterized from `arguments`, not sibling output)
- No serialization anti-patterns in dispatch logic
- Lane overlap is intentional for cross-verification (L1 vs L2 layer tags, L3 vs L8 S1 data flow)

**Issues:**

| # | File:Line | Issue | Severity |
|---|---|---|---|
| 1 | `skills/blackcow-plan.md:189` | **XL parallelism tier is broken.** Skill advertises 15 lanes (XS:5, M:10, XL:15) but only L1-L10 prompts are defined. L11-L15 dispatches would send subagents with **no prompt text** — they'd fail or hallucinate. This is not a documentation gap; it's a functional defect in the XL parallelism architecture. | **CRITICAL** |
| 2 | `skills/blackcow-plan.md:404` | Phase 2 header says "run these in **ONE parallel batch**" but operations are inline grep/read_file — sequential by execution model. No `task()` dispatches. Language is misleading. | LOW |
| 3 | `skills/blackcow-plan.md:560` | Phase 4 header says "Quintuple Adversarial Review" as if always 5 reviewers, but only XL gets 5. M gets 3, XS gets 0. Title over-promises. | LOW |

---

### R4: Cost Efficiency — 80/100 *(originally 89, downgraded by adversarial review)*

**Model-Tier Routing:**

| Lane | Current Tier | Verdict |
|---|---|---|
| L1, L4, L5, L7, L10 | budget | ✅ Correct — discovery/read tasks |
| L2, L3, L6, L8, L9 | pro | ✅ Correct — analysis/security tasks |
| Phase 4 Reviewers A-E | pro | ✅ Correct — adversarial review is analysis-critical |
| Phase 2 Cross-Check | N/A (planner-inline) | ✅ Optimal — zero subagent overhead |

**Cost Estimates (M-scale):**

| Component | Tokens | Cost |
|---|---|---|
| 5 budget lanes × ~8K | 40,000 | $0.00280 |
| 5 pro lanes × ~12K | 60,000 | $0.00840 |
| Phase 2 cross-check (inline) | ~5,000 | $0.00070 |
| Phase 3 design (planner) | ~25,000 | $0.00350 |
| Phase 4 reviewers (3) × ~19K | 57,000 | $0.00798 |
| Orchestration overhead | ~10,000 | $0.00140 |
| **TOTAL** | **~197,000** | **~$0.025** |

**Issues:**

| # | Issue | Severity |
|---|---|---|
| 1 | **Context budget table underestimates tokens.** Phase 0 table says M-scale ≈70K but this excludes subagent context (~120K+ of the ~197K total). The split-to-two-plans logic uses `effective_budget ≈ 115K` — the misleading table could cause the split threshold to be misjudged. | MED |
| 2 | **Dead frontmatter aliases:** `quick`, `deep`, `ultrabrain` defined (lines 17-19) but never used in dispatch protocol. Only `budget`/`pro` are referenced. | LOW |
| 3 | **No cost telemetry.** Skill doesn't log actual token consumption. No feedback loop to validate or refine budget estimates. | MED |
| 4 | **Reviewer plan duplication.** Each Phase 4 reviewer receives `<FULL DRAFT PLAN>` — for XL (5 reviewers), ~60K tokens of duplicated content. Unavoidable but primary XL cost driver. | LOW |

---

### R5: Staleness — 60/100

**Age:** 4 days since git commit (2026-06-12). File mtime: 2026-06-14 (2 days ago). Frontmatter `updated: 2026-06-12` matches git. **File is fresh by timestamp.**

**Why the low score despite freshness:** The file is recently touched but contains multiple references to tools that **don't exist** in the current environment. Freshness ≠ correctness.

| # | Reference | Expected | Actual | Severity |
|---|---|---|---|---|
| 1 | `web_search` (line 14, `allowed-tools`) | Valid tool | Tool does not exist — only `web_fetch` is available | **HIGH** |
| 2 | `grep` (line 159, lane dispatch tools) | `search_content` | Legacy alias — may be rejected | MED |
| 3 | `ls` (line 159, lane dispatch tools) | `list_directory` | Legacy alias — may be rejected | MED |
| 4 | `bash` (line 159, lane dispatch tools) | `run_command` | Legacy alias — may be rejected | MED |
| 5 | `lsp_definition`, `lsp_references`, `lsp_hover` (line 159) | Present in frontmatter `allowed-tools` | **Absent** — subagents may be refused these tools | MED |
| 6 | `deepseek-v4-pro` / `deepseek-v4-lite` | Current provisioned model name | Unverifiable from sandbox | LOW |
| 7 | **L11-L15 prompts** | Defined in Lane Prompts section | **Entirely absent** — 5/15 lane prompts missing | **CRITICAL** |

**Incomplete sections:**
- `skills/blackcow-plan.md:189` — XL dispatch protocol references L11-L15 but **no L11_PROMPT through L15_PROMPT exist** anywhere in the 807-line file. Only L1-L10 defined (lines 193-393).

**Also affected:** `skills/blackcow-loop.md` and `skills/blackcow-qa.md` share the same `web_search` stale reference (confirmed via cross-file search). A cross-skill fix should touch all three files.

**Freshness Recommendation:** Monthly review. This meta-planner changes infrequently but has infrastructure-level issues (phantom tools, undefined prompts) that degrade reliability across all dependent skills. If the hosting platform changes tool/model names, an immediate refresh is warranted.

---

## Cross-Reference Findings (Phase 1)

### Contradictions Detected

| # | Lanes | Finding | Severity |
|---|---|---|---|
| **C1** | R1 ↔ R2 | R1 found LSP tools missing from `allowed-tools`. R2 assumes L3 delivers S1 coverage. The data-collection lane feeding S1 analysis operates with degraded tooling. **Paper coverage ≠ runtime coverage.** | HIGH |
| **C2** | R5 ↔ R2/R3 | R5 found 4 broken tool refs (web_search phantom, grep/ls/bash legacy names). R2 scored gate coverage at 92 and R3 at 93. A skill with wrong tool names cannot execute any lane as written. **High scores reflect design intent, not operational readiness.** | CRITICAL |
| **C3** | R1 internal | Two conflicting tool lists: frontmatter `allowed-tools` (14 tools, canonical names) vs lane dispatch protocol (9 tools, legacy names + unauthorized lsp_*). **Dual source of truth for tool authorization.** | HIGH |
| **C4** | R5 internally | File is "fresh" (2-4 days old) yet contains phantom tool names. Freshness scoring must distinguish "recently touched" from "validated against current runtime." | MED |

### Escalations (Spanning ≥2 Dimensions)

| # | Issue | Spans | Severity |
|---|---|---|---|
| **E1** | **Tool Surface Integrity Failure** — 3 independent tool lists disagree. Frontmatter has `search_content`/`list_directory`/`run_command`. Dispatch protocol uses `grep`/`ls`/`bash`. Lane prompts mix both. No lane can execute with correct tool access. | R1, R2, R3, R5 | **CRITICAL** |
| **E2** | **XL Scale Path Broken** — L11-L15 prompts undefined. Skill advertises 15-lane capability but only implements 10. Any XL invocation dispatches 5 subagents with no prompt text. | R2, R3, R5 | **CRITICAL** |
| **E3** | **Design-Time vs Runtime Divergence** — R2 checks for *presence* of gate-addressing language, not *mechanism*. L3→S1 covered on paper but L3 can't access `lsp_*` tools. Coverage is aspirational, not operational. | R2, R5 | HIGH |
| **E4** | **Score Inflation from Isolated Audits** — Each review lane audits one dimension. R2 sees perfect gate taxonomy → 92. R3 sees correct dispatch pattern → 93. R5 sees broken tools → 60. No lane checks whether R2's "covered gates" are executable. | R2, R3, R5 | MED |

---

## Recommendations

### 🔴 Critical

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **CR1** | **XL scale broken — L11-L15 prompts undefined** | `skills/blackcow-plan.md:189` | Define L11_PROMPT through L15_PROMPT following the existing 4-section structure. L11: Security Deep-Dive (pro), L12: Performance Deep-Dive (pro), L13: Documentation Audit (budget), L14: i18n/l10n Audit (budget), L15: Accessibility Audit (budget). | Heavy (5 new ~40-line prompt sections) |
| **CR2** | **Tool names mismatch — 3 conflicting tool lists** | `skills/blackcow-plan.md:14,159` | Align all three: (a) remove `web_search` from frontmatter `allowed-tools`; (b) add `lsp_definition`, `lsp_references`, `lsp_hover` to frontmatter OR remove from dispatch protocol; (c) change dispatch protocol `grep`→`search_content`, `ls`→`list_directory`, `bash`→`run_command`; (d) update individual lane prompts (L3 says `grep`, L7 says `bash`) to match canonical names. | Medium (systematic find-and-replace across file) |

### 🟠 High

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **H1** | **S1/S2/S3 gates degraded** — L3/L8 lanes reference `lsp_*` but parent skill doesn't authorize them | `skills/blackcow-plan.md:14,159` | Either add `lsp_definition`, `lsp_references`, `lsp_hover` to frontmatter `allowed-tools`, or update L3/L8 prompts to work with text-level `search_content` only and accept reduced accuracy. Latter option should also downgrade S-gate confidence in risk register. | Light |
| **H2** | **P-gates receive weak adversarial review** — single composite line from RVC vs per-gate scrutiny for M-gates | `skills/blackcow-plan.md:636-676` (RVC_PROMPT) | Expand RVC_PROMPT to include per-gate P1/P2/P3 checks with explicit thresholds, mirroring RVA's per-M-gate structure. | Light |
| **H3** | **XS scale skips all adversarial gate verification** | `skills/blackcow-plan.md:560` | Add a lightweight 1-reviewer pass for XS (correctness-only, 2K tokens) or document the risk explicitly with a Gate Verification Status table: "XS: gates are template-documented but not adversarially reviewed." | Light |

### 🟡 Medium

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **M1** | **Context budget table misleading** — ~70K claim excludes subagent context (~120K+ of ~197K total) | `skills/blackcow-plan.md:140-145` | Add a "System-wide tokens" column or footnote clarifying the table counts orchestrator-visible tokens. Update split-to-two-plans threshold to account for total system expenditure. | Light |
| **M2** | **No cost telemetry** — skill can't validate its own estimates | — | Add `total_tokens_consumed` field to the plan output template (Phase 5). Log actual vs estimated for trend analysis. | Light |
| **M3** | **web_search phantom tool** — cross-skill issue affecting blackcow-loop and blackcow-qa too | `skills/blackcow-plan.md:14`, `skills/blackcow-loop.md`, `skills/blackcow-qa.md` | Remove `web_search` from all three skill files' `allowed-tools`. Cross-skill fix. | Light |

### 🟢 Low

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **L1** | 3 code blocks missing language markers | `skills/blackcow-plan.md:100,134,787` | Add `bash` / `python` / `bash` markers respectively. | Trivial |
| **L2** | RVA-RVE use `RETURN:` not `RETURN EXACTLY:` | `skills/blackcow-plan.md:594,615,636,655,676` | Align to `RETURN EXACTLY:` for consistency with L1-L10 prompts. | Trivial |
| **L3** | Dead `model_tiers` aliases (`quick`, `deep`, `ultrabrain`) | `skills/blackcow-plan.md:17-19` | Remove unused aliases or document why they're retained. | Trivial |
| **L4** | Phase 2 "parallel batch" language misleading | `skills/blackcow-plan.md:404` | Change to "sequential cross-check" or dispatch 2-3 parallel verification subagents. | Trivial |
| **L5** | Phase 4 "Quintuple Adversarial Review" title over-promises for XS/M scales | `skills/blackcow-plan.md:560` | Change to "Adversarial Review (scale-gated)" with scale-specific subtitles. | Trivial |

---

## Evolution Readiness

| Assessment | Detail |
|---|---|
| **Safe to auto-evolve?** | **YES — with constraints.** The skill is structurally sound (well-organized, consistent heading levels, valid YAML) and the fixes are mechanical (rename tools, add missing prompts, align language). |
| **Backup recommended before** | L11-L15 prompt additions (new content), tool name replacements across the entire file, frontmatter `allowed-tools` changes. |
| **Estimated evolution tokens** | ~25K (5 new ~40-line prompt sections + systematic tool-name find-and-replace across ~15 references + frontmatter updates) |
| **Post-evolution re-review** | Recommended — verify L11-L15 prompts follow the 4-section structure and tool names are consistent across all three locations (frontmatter, dispatch protocol, individual prompts). |

---

## Summary

`blackcow-plan.md` is a **well-architected planner skill with high design quality** (consistent structure, correct dispatch patterns, full gate taxonomy awareness) that has **critical operational defects** preventing it from functioning correctly at all scales:

1. **XL scale is broken** — 5 of 15 lane prompts are undefined
2. **Tool names are stale** — `web_search` (phantom), `grep`/`ls`/`bash` (legacy names), `lsp_*` (unauthorized)
3. **Gate coverage is aspirational** — all 11 gates are structurally represented but the mechanisms to collect gate-relevant data (L3 for S1, L8 for S2/S3, L9 for P1-P3) operate with degraded or misconfigured tool access

The skill's **total score of 76.65** reflects this gap: excellent design intent held back by runtime-readiness issues. The fixes are mechanical and well-scoped — tool name alignment, L11-L15 prompt authoring, and minor language cleanup. Post-fix, this skill should score 88-92.
