# Meta-Review: blackcow-plan

| Field | Value |
|---|---|
| **Reviewed** | 2026-06-16T00:00:00Z |
| **Reviewer** | blackcow-skill-review (Metis 大将) |
| **Skill Version** | 2.0.0 (frontmatter), mtime 2026-06-14 |
| **Skill Path** | `~/.reasonix/skills/blackcow-plan.md` (810 lines, 34,304 bytes) |

## Overall Score

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| R1 Syntax & Structure | 55 | 15% | 8.3 |
| R2 Gate Completeness | 78 | 30% | 23.4 |
| R3 Parallelism Efficiency | 72 | 25% | 18.0 |
| R4 Cost Efficiency | 68 | 15% | 10.2 |
| R5 Staleness/Freshness | 60 | 15% | 9.0 |
| **TOTAL** | — | **100%** | **69** |

---

## Dimension Details

### R1: Syntax & Structure — Score 55/100

**Frontmatter: largely valid with one critical gap.** All required fields present (name, description, runAs, version, model, model_tiers, allowed-tools). However, `allowed-tools` **omits 6 tools** that the Phase 1 Dispatch Protocol (line ~162) instructs subagents to use: `grep`, `ls`, `bash`, `lsp_definition`, `lsp_references`, `lsp_hover`. The first three have cross-platform aliases (`grep→search_content`, `ls→list_directory`, `bash→run_command`), but `lsp_*` are **phantom tools with no Reasonix equivalent** — subagents dispatched with these will error at runtime.

**Code blocks: nearly all bare.** Of ~30 code blocks, only 1 has a language marker (`markdown` at line 68). All lane prompts and dispatch blocks use bare ` ``` ` fences. This impacts readability in markdown renderers.

**L10_PROMPT has a broken nested code block (HIGH severity).** At line ~378, an inner ` ``` ` intended to open a TypeScript code template instead **closes the outer code block**, dumping the template text into raw markdown and leaving an orphaned ` ``` ` at line 395.

**L11–L15 prompts completely missing.** XL-mode advertises 15 lanes but only L1–L10 prompts are defined. Lines ~191–193 give prose descriptions ("security/performance extensions" for L11/L12, "documentation, i18n, accessibility" for L13-L15) but no prompt text, no `task()` dispatch code, and no RETURN EXACTLY sections.

**Heading structure: clean.** All phases (-1 through 5) use consistent H2/H3 hierarchy with no level skips.

**Cross-references: all valid.** All 5 referenced skill names (blackcow-loop, blackcow-qa, blackcow-skill-review, blackcow-skill-evolver, blackcow-librarian) exist in `skills/`.

**Lane prompts (L1-L10): all follow 4-section structure** with clear RETURN EXACTLY sections. Reviewer prompts (RVA-RVE) use bare `RETURN:` instead of `RETURN EXACTLY:` — minor inconsistency.

---

### R2: Gate Completeness — Score 78/100

**Verdict: All 11 BKIT gates are structurally present in the plan template but operationally hollow for 3 gates.** The skill is a PLANNER — it must ensure its output plan covers the gates, not enforce gates itself. It does this well for 8 of 11 gates.

| Gate | Status | Evidence |
|---|---|---|
| **M1** spec-match | **COVERED** ✅ | Context Anchor: `matchRate ≥ 90%`. Risk Register. Reviewer A. |
| **M2** test-pass | **COVERED** ✅ | Context Anchor: `test pass=100%`. L4 Test Topography. Risk Register. Wave template Gate tag. |
| **M3** regression | **COVERED** ✅ | Risk Register: `0 regressions`. Gap Matrix 🔧 Modify/M3. IntentGate Bug Fix → M3 primary. |
| **M4** lint-clean | **COVERED** ✅ | Context Anchor: `lint=0warn`. Risk Register. IntentGate Quality → M4 primary. |
| **M5** dead-code | **TEMPLATE-ONLY** ⚠️ | Risk Register exists. Gap Matrix 🗑️ Delete/M5. **But no lane (L1–L10) hunts for unreferenced code.** L1 lists exports but doesn't cross-reference callers. L2 traces FROM a symbol, won't find orphans. |
| **S1** dataFlow | **COVERED** ✅ | L3 Data Shape Inventory + S1 tags. Risk Register. Reviewer B dataFlow score. |
| **S2** auth | **TEMPLATE-ONLY** ⚠️ | L8 audits auth. Risk Register has `curl → 401` verification. **But the Waves template (the execution skeleton) has no auth-verification step wired in.** A plan can satisfy all template requirements while producing code with zero auth protection. |
| **S3** injection | **COVERED** ✅ | L8 injection surface audit. Risk Register. Reviewer B. |
| **P1** query | **COVERED** ✅ | L9 N+1 patterns, tagged P1. Risk Register. Reviewer C. |
| **P2** memory | **COVERED** ✅ | L9 unbounded loops, tagged P2. Risk Register. Reviewer C. |
| **P3** latency | **COVERED** ✅ | Context Anchor: `p95_target_ms`. L9 latency section. Risk Register. Reviewer C. |

**Phase -1 IntentGate: informational only.** The intent classification table correctly maps 6 intent classes to primary gates, but the dispatch protocol is entirely static — no conditional lane reordering, no tier override based on detected intent. The `--force-pro` flag exists but IntentGate doesn't auto-activate it.

**Gate Coverage Matrix:**

| M1 | M2 | M3 | M4 | M5 | S1 | S2 | S3 | P1 | P2 | P3 |
|---|---|---|---|---|---|---|---|---|---|---|
| COVERED | COVERED | COVERED | COVERED | TEMPLATE | COVERED | TEMPLATE | COVERED | COVERED | COVERED | COVERED |

**Deduction rationale:** 3 of 11 gates (M5, S2) have Risk Register entries but no operational mechanism to ensure the plan enforces them — template-only coverage. IntentGate is documentation, not routing. Score reflects 8/11 fully covered + 3/11 partially covered.

---

### R3: Parallelism Efficiency — Score 72/100

**Phase 1 (Collect): Correctly parallel.** All 10 defined lanes (L1–L10) dispatched with `run_in_background=true` in one batch. No await-then-dispatch anti-patterns. Lanes are genuinely independent.

**Phase 4 (Review): Correctly parallel.** All 5 reviewers dispatched simultaneously with `run_in_background=true`. Scale gating explicit (XS=skip, M=3/5, XL=5/5).

**Critical defects:**

1. **L11–L15 prompts missing (CRITICAL).** XL mode advertises 15 parallel lanes but only 10 have defined prompts. At runtime, 5 lane dispatches would receive undefined prompt variables → silent failure or hallucination. Deduction: **−15 points.**

2. **Phase 2 "parallel batch" is sequential.** Lines ~405–416 say "run these in ONE parallel batch" but list 6 inline grep/read_file operations with no `task()` dispatch code. No parallelism mechanism exists for these cross-checks. Deduction: **−3 points.**

3. **M-scale reviewer count inconsistency.** Scale Classification table (line ~115) says "Full lanes, 1 reviewer." Reviewer Selection table (line ~577) says "A, B, C (3)" for M. Phase 4 dispatch code shows 5 task calls with textual gating. Token budget (line ~143) says "3 reviewers." **Three different numbers for the same scale.** Deduction: **−3 points.**

4. **Phase 4 plan dependency obscured.** Reviewer prompts say `<FULL DRAFT PLAN>` — but the plan isn't written until Phase 3 completes, which requires Phase 2, which requires Phase 1 results. The "batch fire all lanes at once" language in Phase 1/4 is correct for intra-phase, but the inter-phase dependency (Phase 1→2→3→4) is real and not a parallelism defect — it's architecturally necessary.

**Lane overlap: minimal.** L1/L2 trace same paths at different granularities (file-tree vs call-site). L6/L8 both touch security at package vs application level. No duplicative lanes.

**Lane count: XS=5, M=10 correct. XL=15 is broken until L11-L15 prompts are defined.**

---

### R4: Cost Efficiency — Score 68/100

**Model-tier routing: logically sound but under-documented.**

| Lane | Current Tier | Assessment |
|---|---|---|
| L1 Surface | budget ✅ | glob/ls/read_file — cheap |
| L2 Call Graph | pro ✅ | recursive trace needs reasoning |
| L3 Data Shapes | pro ✅ | type extraction + transform analysis |
| L4 Tests | budget ✅ | glob + read_file patterns |
| L5 Config | budget ✅ | glob + read_file extraction |
| L6 Deps | pro ✅ | web_fetch + advisory analysis |
| L7 Git | budget ✅ | bash git commands |
| L8 Security | pro (forced) ✅ | correct forced override |
| L9 Performance | pro ✅ | hotspot classification |
| L10 Patterns | budget ⚠️ | borderline — code template extraction needs mild reasoning |
| Reviewers A-E | pro ✅ | adversarial review is analysis-critical |

**Dead frontmatter aliases: 3 tiers defined but never used.** `quick`, `deep`, `ultrabrain` exist in `model_tiers` (lines 11-13) but zero dispatch blocks reference them. `--model-tier=ultrabrain` silently falls back to `auto` mode. Adds ~50 tokens of prompt bloat + user confusion.

**Token estimates: undercounted by ~30%.**

| Component | File's estimate | Reality (main-window) |
|---|---|---|
| Skill prompt | — | ~15K |
| Phase 0 pre-flight | — | ~3K |
| Phase 1 lane results (10 × ~3K) | 50K (subagent) | **~30K** (accumulated in main) |
| Phase 2 cross-check | 5K | ~5K |
| Phase 3 design | 10K | ~15K |
| Phase 4 reviewer results (3 × ~4K) | 5K | **~12K** (accumulated in main) |
| Phase 5 synthesize + plan | 5K | ~12K |
| **Estimated peak** | ~75K | **~92K** |
| **Effective budget** | 115K | 115K |
| **Headroom** | ~40K | **~23K (20%)** |

File's estimates count only subagent token burn, not results accumulated in main context. The 92K peak still fits within 115K effective budget but with only 20% margin — any single lane exceeding 6K output would push toward the limit. The split-to-two-plans safety valve (line ~147) is adequate.

**Consolidation opportunity: Merge L4 (Tests) + L5 (Config)** into single budget subagent. Both use glob + read_file. Estimated savings: ~3K main-window tokens per invocation.

**No dollar cost estimate is computed** from the stated rates ($0.07/1M budget, $0.14/1M pro). Estimated per-invocation subagent cost for M-scale: **~$0.006** (budget lanes) + **~$0.003** (pro lanes) + **~$0.002** (reviewers) = **~$0.011 total**.

---

### R5: Staleness/Freshness — Score 60/100

**Age: 0–2 days.** File mtime is 2026-06-14 (2 days ago). Frontmatter `updated:` says 2026-06-12 (stale tag, not bumped on last edit). Actively maintained.

**Outdated references:**

| Reference | Issue | Severity |
|---|---|---|
| `deepseek-v4-lite` | May not be current model name (enum may have changed) | HIGH |
| `lsp_definition`, `lsp_references`, `lsp_hover` | Phantom tools — no equivalents exist | HIGH |
| `grep`, `ls`, `bash` | Cross-platform aliases without `install.sh` | MED |
| `task()` dispatch | Conceptual API, not a real tool function | HIGH |
| `.omo/library/structure-cache.jsonl` | Directory does not exist | MED |
| `.omo/ulw-loop/evidence/` | Directory does not exist | MED |
| L11–L15 prompts | Referenced but never defined | HIGH |
| RVA–RVE use `RETURN:` not `RETURN EXACTLY:` | Inconsistent with L1–L10 | LOW |

**Incomplete sections:**
- `skills/blackcow-plan.md:192` — L11–L15 described in prose but no prompt definitions
- `skills/blackcow-plan.md:14` — `allowed-tools` omits tools dispatch protocol references

**No TODO/FIXME/HACK markers found in the file.**

**Freshness recommendation: Monthly.** Active edits but phantom tools, missing XL lane definitions, and model name uncertainty warrant monthly review until resolved.

---

## Recommendations

### Critical (score impact ≥ 10 points each)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| 1 | **L11–L15 lane prompts missing** — XL mode is broken | `~line 192` | Define L11_PROMPT through L15_PROMPT with full 4-section structure (context + action + RETURN EXACTLY + format). Suggested: L11=API Contract Audit, L12=Error Handling Audit, L13=Documentation Audit, L14=i18n/L10n Audit, L15=Accessibility Audit | Medium |
| 2 | **Phantom `lsp_*` tools** — subagents will fail at runtime | `~line 162` | Remove `lsp_definition`, `lsp_references`, `lsp_hover` from the dispatch protocol tools array. Replace with `search_content` (for `grep`) and `list_directory` (for `ls`). Add `get_file_info` for mtime checks in L4. | Small |
| 3 | **M5 (dead-code) has no data-collection lane** | `Phase 1 lane list` | Add dead-code hunting to L1 (Surface Topology): after listing exports, cross-reference each export against L2's caller count. Or add explicit dead-code check to Phase 2 cross-checks. | Small |

### High (score impact 5–10 points each)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| 4 | **S2 (auth) verification not wired into Waves template** | `Phase 3d Waves`, `~line 490` | Add an explicit auth-verification checkpoint to the Wave template: `- [ ] Auth gate: verify all entry points protected (S2)` with `curl` verification command | Small |
| 5 | **IntentGate is informational, not operational** | `Phase -1`, `~lines 51–82` | Wire IntentGate output to dispatch: if Security intent → force L8 to pro tier (already happens) AND add `--force-pro` auto-activation. If Bug Fix → add characterization test step to Wave 1. | Medium |
| 6 | **Broken nested code block in L10_PROMPT** | `~line 378` | Escape inner triple-backticks with 4-backtick fences, or indent the TypeScript template with 4 spaces instead of a fenced block | Small |
| 7 | **Phase 2 "parallel batch" is sequential** | `~lines 405–416` | Either dispatch cross-checks as 3–4 parallel `task()` subagents, or relabel section from "ONE parallel batch" to "Sequential verification checklist" | Small |
| 8 | **M-scale reviewer count inconsistency** | `~line 115` vs `~line 577` | Change Scale Classification table: "1 reviewer" → "3 reviewers" to match Phase 4 Reviewer Selection table | Tiny |

### Medium (score impact 2–5 points each)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| 9 | **Dead `model_tiers` aliases (`quick`, `deep`, `ultrabrain`)** | `~lines 11–13` | Remove the three alias lines from `model_tiers`. They're never referenced in dispatch and add confusion. | Tiny |
| 10 | **Bare triple-backtick code blocks** (29 of 30) | Throughout | Add language markers: `text` for lane prompts, `yaml` for DAG examples, `bash` for git commands | Small |
| 11 | **Frontmatter `updated:` stale** (2026-06-12 vs mtime 2026-06-14) | `~line 5` | Bump to actual last-modification date | Tiny |
| 12 | **Reviewer prompts use `RETURN:` not `RETURN EXACTLY:`** | `~lines 585–676` | Standardize to `RETURN EXACTLY:` for consistency with L1–L10 | Tiny |

### Low (score impact < 2 points)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| 13 | **No dollar cost estimate computed** from stated rates | `~line 133` | Add a one-line dollar estimate for each scale: "M-scale: ~$0.011/invocation" | Tiny |
| 14 | **L7 omitted from cost-routing table** (line 126 says "L1, L4, L5, L10" but L7 is also budget) | `~line 126` | Add L7 to the budget-tier list in the Model-Tier Cost Routing table | Tiny |
| 15 | **`.omo/library/` and `.omo/ulw-loop/` paths don't exist** | `~lines 88, 740` | Either implement blackcow-librarian cache infrastructure, or add a grace note: "paths created on first use" | Small |

---

## Evolution Readiness

- **Safe to auto-evolve?**: **NO** — 3 CRITICAL findings (missing L11-L15, phantom tools, M5 lane gap) require manual design decisions before automated evolution.
- **Backup recommended before**: Phase 1 Dispatch Protocol (tool array), Phase 3d Waves template, L10_PROMPT code block, frontmatter `model_tiers` and `allowed-tools`.
- **Estimated evolution tokens**: ~12K (fixing 15 recommendations across ~30 line changes).
- **Post-evolution re-review**: Required — 3 CRITICAL items must be verified resolved.

---

## Cross-Reference & Contradiction Findings

| Finding | Lanes | Resolution |
|---|---|---|
| R2 claims M5/S2 COVERED, R6 argues TEMPLATE-ONLY | R2 vs R6 | **R6 sustained.** M5 has no data-collection lane; S2 verification isn't wired into the Waves execution template. Gates are structurally present in Risk Register but not operationally enforced in plan output. Scores adjusted accordingly. |
| R2 claims IntentGate maps correctly, R6 argues it's documentation-only | R2 vs R6 | **R6 sustained.** IntentGate produces an informational table but doesn't alter dispatch behavior. No conditional tier routing, no lane reordering, no forced pro activation based on intent. |
| R3 says Phase 2 "parallel batch", R6 says it's sequential | R3 vs R6 | **R6 sustained.** No `task()` dispatch code exists for Phase 2 cross-checks — they're inline operations. |
| R4 says ~70K tokens, R6 says ~340K | R4 vs R6 | **R4 closer to reality.** R6's 340K conflates subagent-internal tokens with main-window tokens. Subagent tokens don't accumulate in main context. R4's 92K peak estimate is more accurate, though still ~30% above the file's own 70K estimate. |
| R5 says "fresh, 0 days old" but finds phantom tools | R5 self-contradiction | File is actively maintained but carries latent bugs (lsp_* tools) from earlier versions. Freshness doesn't guarantee correctness. |

---
