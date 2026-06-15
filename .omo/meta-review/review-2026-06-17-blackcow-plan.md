# Meta-Review: blackcow-plan

| Field | Value |
|---|---|
| **Reviewed** | 2026-06-17T00:00:00Z |
| **Reviewer** | blackcow-skill-review (Metis 大将) |
| **Skill Version** | 2.0.0 (frontmatter), updated 2026-06-12, modified 2026-06-14 |
| **File** | skills/blackcow-plan.md (34,347 bytes, ~810 lines) |
| **Prior Scores** | 66.65 (2025-07-14) → 76.65 (2026-06-14) → 69 (2026-06-16) |

## Overall Score

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| R1 Syntax & Structure | 88 | 15% | 13.2 |
| R2 Gate Completeness | 72 | 30% | 21.6 |
| R3 Parallelism Efficiency | 70 | 25% | 17.5 |
| R4 Cost Efficiency | 70 | 15% | 10.5 |
| R5 Staleness/Freshness | 58 | 15% | 8.7 |
| **TOTAL** | — | **100%** | **71.5** |

> **Score trajectory**: 66.65 → 76.65 → 69 → **71.5**. The score is relatively stable in the high-60s/low-70s range, suggesting genuine quality constraints rather than reviewer noise. The 76.65 spike appears to be an outlier (likely R2 over-scoring).

## Dimension Details

### R1: Syntax & Structure — 88/100

**Strengths**: Well-organized with clear phase progression (Phase -1 through Phase 5), consistent H2/H3 heading hierarchy, valid YAML frontmatter with all required fields, no broken cross-skill references (all 5 sibling skills confirmed present).

**Issues found**:

| # | File:Line | Issue | Severity |
|---|---|---|---|
| 1 | ~378-393 | **Nested fenced code block** inside L10_PROMPT — inner ` ``` ` closes outer block prematurely, dumping template text into raw markdown | MED |
| 2 | ~698-712 | **Nested fenced code block** in Phase 5 output template — inner ` ``` ` breaks outer ` ```markdown` fence, orphaned closing fence | MED |
| 3 | ~191-193 | **XL dispatch incomplete** — L11-L15 described in prose only; no `task()` dispatch code block provided (unlike XS/M which have full executable blocks) | MED |
| 4 | ~568 (RVA-RVE) | **Inconsistent RETURN keyword** — reviewer prompts use `RETURN:` while L1-L10 use canonical `RETURN EXACTLY:` | LOW |
| 5 | Multiple locations | **Code blocks without language markers** — Phase 0 discovery, context budget formula, all dispatch blocks, execution command example (~6 instances) | LOW |
| 6 | ~14 | **model_tiers** — valid YAML but non-standard for `install_skill` which expects flat `model` string; may be silently ignored by tooling | LOW |

### R2: Gate Completeness — 72/100

The Risk Register (Phase 3e, lines ~558-571) provides **structural coverage of all 11 BKIT gates** with explicit severity, numeric thresholds, mitigations, and verification commands. However, operational enforcement is uneven — 4 gates are template-only with no data-collection lane or execution-template wiring.

**Gate Coverage Matrix**:

| Gate | Status | Primary Evidence | Operational Gap |
|---|---|---|---|
| **M1** spec-match | ✅ COVERED | Risk Register + Context Anchor SUCCESS + Gap Matrix | — |
| **M2** test-pass | ✅ COVERED | Risk Register + L4_PROMPT + Context Anchor SUCCESS | — |
| **M3** regression | ✅ COVERED | Risk Register + Gap Matrix + IntentGate | — |
| **M4** lint-clean | ✅ COVERED | Risk Register + Context Anchor SUCCESS + IntentGate | — |
| **M5** dead-code | ⚠️ TEMPLATE-ONLY | Risk Register + Gap Matrix `🗑️ Delete` row | **No lane hunts for unreferenced exports.** L1 lists exports but never cross-references callers. L2 traces FROM symbols, won't find orphans. |
| **S1** dataFlow | ✅ COVERED | Risk Register + L3_PROMPT + L8_PROMPT | L3's dispatch includes phantom `lsp_*` tools (see R5) — type-extraction accuracy degraded |
| **S2** auth | ⚠️ TEMPLATE-ONLY | Risk Register + L8_PROMPT + IntentGate | **`curl → 401` verification not wired into Waves template.** A plan can satisfy every template field without auth protection. |
| **S3** injection | ✅ COVERED | Risk Register + L8_PROMPT + IntentGate | — |
| **P1** query | ⚠️ WEAK | Risk Register + L9_PROMPT | **Single composite line in RVC_PROMPT.** P-gates get 1/3 the adversarial scrutiny of M-gates (RVA has per-M-gate checks; RVC collapses P1-P3 into one bullet). |
| **P2** memory | ⚠️ WEAK | Risk Register + L9_PROMPT | Same as P1 |
| **P3** latency | ⚠️ WEAK | Risk Register + L9_PROMPT + Context Anchor SUCCESS | Same as P1 |
| **XL S/P gates** | ❌ BROKEN | L11 (Security Deep-Dive) and L12 (Performance Deep-Dive) undefined | XL-scale S/P gate data collection structurally impossible |

**Key finding**: The skill has a systematic gap between **documented gate coverage** (Risk Register entries, taxonomy rows) and **operational enforcement** (data-collection lane prompts, execution-template wiring). Four gates (M5, S2, P1, P2, P3) are documented but not operationally enforced.

### R3: Parallelism Efficiency — 70/100

**Strengths**: Correct batch-and-wait pattern for Phase 1 (all lanes dispatched with `run_in_background=true` before any await) and Phase 4 (5 reviewers dispatched simultaneously). Lane independence is genuine — all 10 defined lanes have distinct concerns. Lane counts match scale spec (XS=5, M=10).

**Issues**:

| # | Section | Issue | Severity |
|---|---|---|---|
| 1 | ~191-193 | **XL scale broken** — L11-L15 prompts undefined. 5 of 15 lanes (33%) would receive empty prompts at runtime. Carried across 3 prior reviews unresolved. | **CRITICAL** |
| 2 | ~404-416 | **Phase 2 "parallel batch" is sequential** — header says "ONE parallel batch" but body lists 6 inline grep/read_file operations with zero `task()` dispatches | MED |
| 3 | ~115 vs ~577 | **M-scale reviewer count inconsistent** — Scale Classification table says "1 reviewer", Phase 4 table says "A, B, C (3)" | MED |
| 4 | ~490 | **Wave tasks not parallel-dispatched** — Waves declare "Tasks within a wave run in parallel" but no `task(…, run_in_background=true)` dispatch code shown | LOW |
| 5 | — | **11 serial inter-phase gates** — Phase -1→0→1→2→3a→3b→3c→3d→3e→4→5 with no overlap or pipelining | LOW |

### R4: Cost Efficiency — 70/100

**Strengths**: Model-tier routing is well-designed — budget lanes (L1/L4/L5/L7/L10) correctly assigned to `deepseek-v4-lite`, pro lanes (L2/L3/L6/L8/L9) correctly assigned to `deepseek-v4-pro`. Critical override forces L8 and reviewers to pro tier regardless of `--model-tier` flag. `.omo/library` cache integration saves ~3K tokens.

**Issues**:

| # | Finding | Severity |
|---|---|---|
| 1 | **Token estimates undercounted ~3.6×** — plan claims ~70K M-scale; actual review estimates ~255K total API tokens (main-agent peak ~92K). The 115K effective budget guardrail provides sufficient headroom for main-agent context, but the documented estimates are misleading. | MED |
| 2 | **Multi-feature mode costs multiply linearly** — `--features=a,b,c` runs full Phase 1-5 per feature with zero context sharing. 3 features = 3× cost (~$0.09). No warning documented. | MED |
| 3 | **Unused model_tiers aliases** — `quick`, `deep`, `ultrabrain` defined in frontmatter but never referenced by any dispatch block. Dead config. | LOW |
| 4 | **L7 omitted from cost-routing table** — line 126 lists budget lanes as "L1, L4, L5, L10" but omits L7 (which IS budget). Documentation gap, not routing bug. | LOW |

**Cost estimate (M-scale)**:

| Component | Tokens | Cost |
|---|---|---|
| Phase 1 budget lanes (5× @ $0.07/M) | ~75K | $0.005 |
| Phase 1 pro lanes (5× @ $0.14/M) | ~100K | $0.014 |
| Phase 2-3-5 (main agent) | ~20K | $0.003 |
| Phase 4 reviewers (3× pro) | ~45K | $0.006 |
| Main agent preamble + orchestration | ~15K | $0.002 |
| **Total** | **~255K** | **~$0.03** |

### R5: Staleness — 58/100

**Active maintenance** (modified today, 2026-06-14) but carries **0 of 15+ recommendations resolved across 3 prior review cycles** (2025-07-14 → 2026-06-14 → 2026-06-16). The skill is edited frequently without addressing documented defects.

| # | Reference | Expected | Actual | Severity |
|---|---|---|---|---|
| 1 | `deepseek-v4-lite` (model_tiers) | `deepseek-v4-flash` (current lite-tier) | `deepseek-v4-lite` (may resolve to invalid model) | **HIGH** |
| 2 | `lsp_definition`, `lsp_hover`, `lsp_references` | Not available as tools | Listed in allowed-tools and dispatch protocol | **HIGH** |
| 3 | `web_search` in allowed-tools | Not available | Listed in frontmatter line 14 | MED |
| 4 | `grep`/`ls`/`bash` in lane prompts | `search_content`/`list_directory`/`run_command` (native) | Legacy aliases used throughout | MED |
| 5 | `task()` function | No such tool; maps to `explore`/`research` | Used 50+ times as literal API call | **HIGH** |
| 6 | `run_in_background`, `max_steps` params | Not valid on any real tool | Used on every dispatch | **HIGH** |
| 7 | `.omo/library/structure-cache.jsonl` | Directory `.omo/library/` does not exist | Referenced in Phase 0.0 cache load | MED |
| 8 | `updated: 2026-06-12` | Should be `2026-06-14` (actual mtime) | Stale by 2 days | LOW |
| 9 | **XL L11-L15 prompts** | Should exist for version 2.0.0 | Entirely undefined — carried across 3 reviews | **CRITICAL** |

**Freshness recommendation**: Weekly review until CRITICAL items resolved (L11-L15 prompts, phantom tools, model name). Then quarterly.

---

## Recommendations

### Critical (score impact >10 points)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| C1 | **XL scale broken — L11-L15 prompts undefined** | ~191-193 | Define L11_PROMPT (API Contract Audit / S-gate deep-dive), L12_PROMPT (Error Handling / P-gate deep-dive), L13_PROMPT (Documentation Audit), L14_PROMPT (i18n/l10n Audit), L15_PROMPT (Accessibility Audit). Each with full 4-section structure. | Heavy |
| C2 | **Phantom tools in dispatch protocol** | ~14, ~159 | Remove `lsp_definition`, `lsp_hover`, `lsp_references`, `web_search` from allowed-tools. Replace `grep`→`search_content`, `ls`→`list_directory`, `bash`→`run_command` in dispatch blocks. | Medium |
| C3 | **`task()` is not a real tool** | Throughout | Document that `task()` maps to platform-native subagent dispatch (`explore`/`research`). Add platform-tool-mapping table at top of skill (matching the pattern in blackcow-skill-review.md). | Medium |

### High (score impact 5-10 points)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| H1 | **M5 dead-code — no data-collection lane** | ~404 (Phase 2) | Add dead-code cross-reference step: "For every export found by L1, search_content for references — flag orphans as M5 findings." Or augment L1 prompt to cross-reference exports against L2 caller counts. | Light |
| H2 | **S2 auth not wired into Waves template** | ~490 | Add explicit auth-verification checkpoint to Wave 4 (Hardening): `- [ ] Auth gate: verify all entry points protected (S2) — curl -H "Authorization: invalid" → 401` | Light |
| H3 | **P-gates get 1/3 adversarial scrutiny of M-gates** | ~636 (RVC_PROMPT) | Expand RVC_PROMPT with per-gate P1/P2/P3 checks: "P1: Confirm no N+1 queries remain (query count assertion)", "P2: Confirm no unbounded collections (pagination check)", "P3: Confirm p95 latency target met (load test result)" | Light |
| H4 | **IntentGate is documentation, not routing** | ~51-82 | Wire IntentGate output into dispatch: when IntentClass=Security → auto-activate `--force-pro`; when Performance → force L9 pro tier. Currently the table describes routing changes but dispatch protocol is entirely static. | Medium |
| H5 | **Nested code blocks break markdown rendering** | ~378-393, ~698-712 | Use 4-backtick fences for outer blocks when inner blocks use 3-backtick. Or replace inner code blocks with indented code blocks. | Light |

### Medium (score impact 2-5 points)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| M1 | **Token estimates undercounted ~3.6×** | ~140-149 | Add note: "Estimates cover orchestrator context only. Actual API tokens ~3.6× higher. Main-window peak for M-scale: ~92K (within 115K budget). Two-plan splits expected only for XL tasks." | Light |
| M2 | **Multi-feature mode cost undocumented** | ~35-41 | Add cost warning: "Each feature runs independently — N features = N× cost. Consider `--features=` only when features share no context. For dependent features, use single plan with DAG." | Light |
| M3 | **Phase 2 "parallel batch" is misleading** | ~404 | Relabel to "Sequential Verification Checklist" or dispatch 3-4 parallel task subagents for the verify steps. | Light |
| M4 | **M-scale reviewer count inconsistent** | ~115 vs ~577 | Unify to "3 reviewers (A, B, C)" in both the Scale Classification table and Phase 4 Reviewer Selection table. | Light |
| M5 | **`deepseek-v4-lite` model name outdated** | ~11 | Update to `deepseek-v4-flash` (current lite-tier name) or generic `budget-model` with platform-mapping table. | Light |
| M6 | **`updated` field stale** | ~8 | Bump to `2026-06-14` (actual mtime). Automate via git hook or install.sh. | Trivial |

### Low (score impact <2 points)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| L1 | Code blocks missing language markers | ~6 instances | Add `bash`, `yaml`, `markdown` markers | Trivial |
| L2 | `RETURN:` vs `RETURN EXACTLY:` inconsistency | RVA-RVE prompts | Standardize on `RETURN EXACTLY:` | Trivial |
| L3 | Unused `model_tiers`: `quick`, `deep`, `ultrabrain` | ~11-13 | Remove or document as future-reserved aliases | Trivial |
| L4 | L7 omitted from cost-routing table | ~126 | Add L7 to budget lane list: "L1, L4, L5, L7, L10" | Trivial |
| L5 | Wave tasks lack explicit dispatch code | ~490 | Add `task()` dispatch examples for wave-level tasks with `depends_on` | Light |

---

## Evolution Readiness

- **Safe to auto-evolve?**: **NO** — requires manual review for C1-C3 (XL lane design, tool surface rewrite, dispatch protocol clarification)
- **Backup recommended before**: Entire file — changes touch frontmatter, dispatch blocks, lane prompts, Waves template, and IntentGate routing
- **Estimated evolution tokens**: ~15-20K (substantial rewrite of dispatch protocol + 5 new lane prompts)
- **Blockers for blackcow-skill-evolver**:
  1. L11-L15 prompt design requires architectural decisions (what 5 lanes for XL scale?)
  2. Tool dispatch protocol rewrite needs cross-platform awareness (mapping `task()` to `explore`/`research`)
  3. `model_tiers` model name correction depends on current provisioning catalog
  4. IntentGate routing changes affect Phase 1 dispatch logic (non-trivial conditional)

---

## Cross-Reference Summary

| Contradiction | Lanes | Resolution |
|---|---|---|
| R2 says 100% gate coverage, R3 says XL S/P lanes undefined | R2 ↔ R3 | **R3 sustained.** Gates are structurally documented (Risk Register) but XL-scale enforcement is impossible. Score reflects template coverage, not operational coverage. |
| R2 says M5 COVERED, R6 says TEMPLATE-ONLY | R2 ↔ R6 | **R6 sustained.** M5 has Risk Register entry but no lane hunts for dead code. |
| R2 says S2 COVERED, XR1 says not wired to Waves | R2 ↔ XR1 | **XR1 sustained.** Auth verification exists in Risk Register but absent from execution template. |
| R4 says $0.03/invocation, plan says ~70K tokens | R4 ↔ Plan | Plan undercounts by ~3.6× (counts only orchestrator context). Actual cost still cheap (~$0.03). Safety margins sufficient. |

---

## Self-Review Note

This review (of blackcow-plan by blackcow-skill-review) shares the same systemic limitation identified in R2's methodology: **template coverage vs. operational coverage**. Future iterations of blackcow-skill-review should add an "operational enforcement" check to the R2 gate audit — verifying not just that gates are mentioned, but that they have (a) a data-collection lane prompt, (b) a verification step in the output template, and (c) authorized tooling to execute.
