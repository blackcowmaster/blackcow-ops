# Meta-Review: blackcow-plan (v6)

| Field | Value |
|---|---|
| **Reviewed** | 2026-06-15T14:25:00Z |
| **Reviewer** | blackcow-skill-review (Metis 大将) |
| **Skill Version** | 2.0.0 (mtime 2026-06-15T08:44:18Z) |
| **Repo file** | `skills/blackcow-plan.md` (1050 lines) |
| **Installed copy** | `~/.reasonix/skills/blackcow-plan.md` (⚠️ known stale) |

## Overall Score

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| R1 Syntax & Structure | 70 | 15% | 10.5 |
| R2 Gate Completeness | 64 | 30% | 19.2 |
| R3 Parallelism Efficiency | 50 | 25% | 12.5 |
| R4 Cost Efficiency | 62 | 15% | 9.3 |
| R5 Staleness/Freshness | 60 | 15% | 9.0 |
| **TOTAL** | — | **100%** | **60.5** |

> 📉 **Trend**: Continuing decline. Previous scores: 76.65 (Jun 14 peak) → 73.60 (Jun 20) → 64.30 (Jun 20 v5) → **60.5** (this review). The decline reflects progressively tighter scoring methodology and accumulating unresolved findings, not necessarily worsening file quality.

---

## Dimension Details

### R1: Syntax & Structure — 70/100

**Strengths:**
- YAML frontmatter structurally valid with `---` open/close markers (lines 1-15)
- Heading hierarchy clean: H1 → H2 → H3, no skipped levels
- All fences balanced (36 triple-backtick pairs, 2 quadruple-backtick pairs, 1 tilde block)
- No broken references to other skills (all 7 blackcow-* skill names verified)
- No `lsp_*` tool references (clean)
- Self-Audit Checklist present and comprehensive (lines 1022-1050)

**Issues:**

| # | File:Line | Issue | Severity |
|---|---|---|---|
| S1 | Line 13 | `allowed-tools` is a YAML string (comma-separated), not a list. Should be `[read_file, search_content, ...]` or block sequence. | LOW |
| S2 | Lines 62-72, 164-176, 197-202, 226-250, 281-301, 343-355, 386-388, 403-569 | **~30+ bare code fences** without language markers. All L1-L9 prompt blocks, formula blocks, command examples, ASCII diagrams lack markers. | **HIGH** |
| S3 | Line 1023 | **Self-contradiction**: Self-Audit Checklist item says "No bare code blocks — every fence has a language marker" but the file itself has ~30 bare fences. | **HIGH** |

**Verdict**: The file is structurally sound but ~30 bare fences and a self-contradictory audit rule create a 30-point gap between the file's self-audit expectations and reality.

---

### R2: Gate Completeness — 64/100

> ⚠️ **Score recalibrated**. R2 subagent reported 100/100 (all 11 gates "covered" in Risk Register template). Cross-reference (XR1) found that progressive widening structurally prevents evidence collection for 5 gates (S2, S3, P1, P2, P3) in the common case. Previous meta-review v5 already corrected R2 from 100→64 for the self-audit threshold gap. This review confirms 64 is the honest score, with a further potential downward pressure to 52-56 due to the widening-evidence gap (see E1 below).

**Covered Gates (with evidence):**

| Gate | Evidence | Quality |
|---|---|---|
| M1 spec-match | Risk Register (line 711), Context Anchor SUCCESS `matchRate ≥ 90%` (line 645), Gap Matrix 🆕→M1 (line 691), RVA review | ✅ Numeric threshold |
| M2 test-pass | Risk Register (line 713), Context Anchor `test pass=100%, coverage ≥ 80%`, L4 lane, per-step Verify commands | ✅ Numeric threshold |
| M3 regression | Risk Register (line 715), Gap Matrix 🔧→M3, L4 existing test identification | ⚠️ No SUCCESS threshold |
| M4 lint-clean | Risk Register (line 717), Context Anchor `lint=0warn` | ✅ Numeric threshold |
| M5 dead-code | Risk Register (line 719), Gap Matrix 🗑️→M5, grep-for-references verification | ⚠️ No SUCCESS threshold |
| S1 dataFlow | Risk Register (line 721), L3 Data Shape lane (S1 tagging), L8 Security lane, RVB review | ⚠️ No SUCCESS threshold; evidence collection gated behind Stage 3 widening |
| S2 auth | Risk Register (line 723), L5 Config + L8 Security lanes, RVB review | ⚠️ No SUCCESS threshold; evidence gated behind Stage 3 |
| S3 injection | Risk Register (line 725), L8 Security (injection audit), RVB review | ⚠️ No SUCCESS threshold; evidence gated behind Stage 3 |
| P1 query | Risk Register (line 727), L9 Performance (N+1 detection), RVC review | ⚠️ No SUCCESS threshold; evidence gated behind Stage 3 |
| P2 memory | Risk Register (line 729), L9 Performance (unbounded growth), RVC review | ⚠️ No SUCCESS threshold; evidence gated behind Stage 3 |
| P3 latency | Risk Register (line 731), Context Anchor `p95_target_ms: <N> or N/A` (placeholder), L9 Performance, RVC review | ⚠️ Placeholder threshold; evidence gated behind Stage 3 |

**Gate Coverage Matrix:**

| M1 | M2 | M3 | M4 | M5 | S1 | S2 | S3 | P1 | P2 | P3 |
|---|---|---|---|---|---|---|---|---|---|---|
| COVERED | COVERED | PARTIAL | COVERED | PARTIAL | PARTIAL | PARTIAL | PARTIAL | PARTIAL | PARTIAL | PARTIAL |

**Key Gap**: Only 4 of 11 gates (M1, M2, M4, P3-partial) have numeric thresholds in the Context Anchor SUCCESS field — the plan's single verification contract with the executor. The remaining 7 gates exist in the Risk Register but lack measurable exit criteria.

**Widening-Evidence Gap (XR1/E1 — CRITICAL)**: For Feature, Bug Fix, Performance, and Quality intents (the majority of invocations), progressive widening may stop at Stage 2 (uncertainty ≤ 60), meaning L8 (Security, S2/S3) and L9 (Performance, P1/P2/P3) never dispatch. Five gates have zero evidence collection for most tasks. The "Force FULL widening" escape only triggers for SECURITY intent or uncertainty > 85.

---

### R3: Parallelism Efficiency — 50/100

**Core Contradiction — CRITICAL:**

The skill contains two mutually exclusive dispatch instructions within the same Phase 1 section:

| Line | Instruction |
|---|---|
| 266-269 | **"CRITICAL: You MUST dispatch all lanes as task subagents in ONE batch... NEVER await any single lane before dispatching the rest."** |
| 322 | **"Do NOT dispatch all selected lanes at once. Use staged widening to minimize token spend: Stage 1 → 2 → 3."** |

Both cannot be true. Progressive widening **by definition** serializes dispatch: Stage 2 cannot start until Stage 1's uncertainty score is computed. Stage 3 cannot start until Stage 2's results are analyzed. This creates 3 sequential wait-points that destroy the "ONE batch" parallelism promise.

**Impact**: For a typical multi-file feature (uncertainty ~50), the pipeline becomes: dispatch L1 → await → score → dispatch L2-L4 → await → score → STOP (never reaches L5-L10). This is 2-3× slower than a single batch and leaves 5 gates unevidenced.

| # | File:Line | Issue | Severity |
|---|---|---|---|
| P1 | Lines 266-269 vs 322 | Widening contradicts "ONE batch" dispatch — structural conflict across 4 locations (lines 266, 322, 1004, 1036) | **CRITICAL** |
| P2 | Lines 614-620 | Phase 2 labeled "parallel batch" but has zero `task()` or `explore()` dispatch. 6 inline sequential grep/read operations with no subagent isolation or retry. | **HIGH** |
| P3 | Lines 1028/1036 | Self-Audit Checklist requires BOTH progressive widening AND one-batch dispatch (items that are mutually exclusive) | **HIGH** |
| P4 | Lines 400-415 vs 485-500 | L3 (Data Shapes) ↔ L8 (Security): both lanes independently classify S1/dataFlow risks | MED |
| P5 | Lines 420-440 vs 485-500 | L5 (Config) ↔ L8 (Security): both lanes independently search for secrets/credentials | MED |
| P6 | Lines 350-360 vs 365-385 | L1 (Surface Topology) ↔ L2 (Call Graph): both independently tag BKIT layers | LOW |

**Resolution**: Progressive widening is a legitimate token-saving optimization but must be decoupled from dispatch timing. Recommend: fire all selected lanes in parallel, analyze results in Stage-priority order, stop processing when uncertainty drops below threshold (remaining results become "bonus evidence").

---

### R4: Cost Efficiency — 62/100

**Model-Tier Routing**: All 10 lane assignments correct ✅. Intent-based overrides (Bug Fix→L2 pro, Quality→L7 pro, Emergency→all pro) well-reasoned.

**Token Estimate (M-scale, cache miss):**

| Component | Tokens | Cost |
|---|---|---|
| Parent agent (Phases -1→5) | ~62.5K input + ~30K output | ~$0.040 |
| 10 lane subagents (5 budget + 5 pro) | ~335K combined internal | ~$0.119 |
| 3 reviewer subagents (all pro) | ~24K combined | ~$0.010 |
| **Grand total** | **~452K** | **~$0.17** |

XL-scale: ~750K / ~$0.35. XS-scale: ~180K / ~$0.06.

**Issues:**

| # | Issue | Impact | Severity |
|---|---|---|---|
| C1 | L1 + L10 redundant file scans (~8K-15K tokens) — both independently glob/read to understand project structure | ~$0.004/invocation | MED |
| C2 | L2 + L3 overlapping source reads (~10K-20K tokens) — call sites involve data shapes | ~$0.009/invocation | LOW |
| C3 | Progressive widening overhead (~2K-5K per stage decision) may exceed savings for tasks always needing Stage 3 | ~$0.002/invocation | LOW |
| C4 | All 5 reviewers on pro tier — Reviewer C (Feasibility) and E (Minimalism) could use budget | ~$0.003-0.006/invocation | LOW |
| C5 | Phase 2 re-verification (~3K-5K) re-searches symbols subagents already reported with file:line | ~$0.002/invocation | LOW |
| C6 | Stale-cache penalty (~3K on every cache miss) — paid on most first-run invocations | ~$0.001/invocation | LOW |

**Positive cost control**: Intent-based lane skipping saves 30-60% of Phase 1 cost for non-Feature intents. This is the single best cost-control mechanism.

**Consolidation opportunities**: Merge L1+L10 (~$0.004 saved) and L5+L6 (~$0.002 saved) — low risk, quick wins.

---

### R5: Staleness/Freshness — 60/100

| Metric | Value |
|---|---|
| **Repo file age** | 0 days (mtime 2026-06-15T08:44:18Z) |
| **Installed copy age** | Unknown (last install date not tracked) |
| **Known critical issues unresolved** | 4 (from v5 meta-review, 2026-06-20) |
| **Known high issues unresolved** | 7 (from v5 meta-review) |
| **Review history entries** | 18 (Jul 2025 – Jun 2026) |
| **Score trend** | Declining: 76.65 → 64.30 → 60.5 |

**Why 60, not 92**: The repo file is fresh (0 days old) but:
1. The file predates the v5 meta-review (2026-06-20) and has NOT been updated with its findings — 4 critical + 7 high issues remain unresolved.
2. The **installed copy** (`~/.reasonix/skills/blackcow-plan.md`) is critically stale: uses `deepseek-v4-lite` (non-existent model → API 400), missing Intent-Based Dispatch table (30-50% token waste). This is the runtime-relevant copy.
3. The installed copy staleness is a **project-wide** issue: all 6 installed skills use `deepseek-v4-lite` (confirmed by search_content).

**Score trend (18 reviews):** Range 54.60–76.65, average 66.90, latest 64.30 (v5) → 60.5 (this review). The decline reflects tighter scoring methodology and accumulating unresolved findings.

**Freshness recommendation**: Resolve critical findings before next review. Weekly review cadence appropriate given governance staleness window (7 days).

---

## Recommendations

### Critical (score < 70 on individual dimension, or structural)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **C1** | Progressive Widening contradicts "ONE batch" dispatch — two opposite instructions in same Phase 1 | Lines 266-269 vs 322; Lines 1004, 1036 | Decouple widening from dispatch timing: fire all lanes in parallel, analyze results in Stage-priority order. OR remove "ONE batch" claim and document Phase 1 as a 3-stage serial pipeline. | **L — restructure Phase 1 logic** |
| **C2** | Widening silently skips L8/L9 for non-Security intents — 5 gates (S2, S3, P1, P2, P3) never evidenced for Feature/BugFix/Performance/Quality tasks | Lines 303-354 | Add rule: "If any S-gate or P-gate is in the intent's primary gate set, force Stage 3 dispatch of L8/L9 regardless of uncertainty_score." | **S — add gate-aware widening rule** |
| **C3** | Installed copy uses `deepseek-v4-lite` (non-existent model) — runtime-breaking on all budget-tier lanes | `~/.reasonix/skills/blackcow-plan.md` line 9 | Re-run `skills/install.sh` to sync installed copies. Fix is mechanical — the repo copy has correct model names. | **XS — re-run install.sh** |
| **C4** | Only 4/11 gates have numeric thresholds in Context Anchor SUCCESS field | Line 645 (SUCCESS field) | Add numeric thresholds for M3, M5, S1, S2, S3, P1, P2. Even placeholder ranges (e.g., "0 regressions", "0 unused exports", "integrity ≥ 85%") are better than nothing. | **M — add 7 thresholds** |

### High (significant quality/operational impact)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **H1** | Phase 2 labeled "parallel batch" but has zero subagent dispatch — 6 sequential inline operations | Lines 614-620 | Either dispatch each cross-check as `explore()` with `run_in_background=true`, or rename to "Phase 2 — Manual Cross-Check" and drop the parallel claim. | **M — dispatch or relabel** |
| **H2** | ~30 bare code fences without language markers — Self-Audit Checklist says "No bare code blocks" | Lines 164-569 (all lane prompts, formulas, command examples) | Add ` ```text ` or ` ```yaml ` markers to all bare fences. | **M — ~30 markers to add** |
| **H3** | Self-Audit Checklist requires BOTH progressive widening AND one-batch dispatch — mutually exclusive | Lines 1028, 1036 | Make items conditional: "If widening used: Stage log recorded with evidence at each stage." Remove contradictory one-batch requirement from same checklist section. | **S — edit 2 checklist items** |
| **H4** | Widening quality gate (30% resolution rule) has zero verification — trust-the-planner with no audit trail | Lines 374-376 | Add Phase 2 cross-check item: "Verify widening decision log shows resolution rate ≥ 30% at each stage boundary." Add to Reviewer A (Correctness) prompt. | **S — add verification** |
| **H5** | L5↔L8 duplicate secrets scanning — both lanes independently grep for credentials | L5_PROMPT (lines ~486-488), L8_PROMPT (lines ~537-539) | L8 should reference L5's output instead of re-searching. Add note: "Cross-reference L5's SECRET REFERENCES output; only flag L5-missed findings." | **S — add cross-reference** |
| **H6** | Phase 1 has no failure/retry/degraded-mode handling — single lane timeout = silent gate data loss | Phase 1 section | Add: "If any subagent times out, mark the lane as [DEGRADED] in the plan and note which gates lack evidence. Retry once with max_steps=20. If still failing, proceed without that lane's data." | **M — add failure protocol** |

### Medium (quality improvement)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **M1** | `allowed-tools` is a YAML string, not a list | Line 13 | Convert to `[read_file, search_content, ...]` (flow sequence) | **XS** |
| **M2** | L1+L10 redundant file scans (~8K-15K tokens wasted) | L1_PROMPT, L10_PROMPT | L10 should reuse L1's file tree output. Add instruction: "Use L1's FILE TREE as input; only search for similar implementations within identified files." | **S** |
| **M3** | XL scale differentiation nullified — `model=pro` is decorative per platform adaptation note | Line ~298 | For XL: add 2 extra lanes (L11 Cross-Module Integration, L12 Deployment Topology) or accept that XL == M + 5 reviewers + all-pro | **M** |
| **M4** | Reviewer C and E could use budget tier (saves ~$0.003-0.006) | Lines ~780-785 | Change Reviewer C (Feasibility) and Reviewer E (Minimalism) to `model=budget` | **XS** |

### Low (cosmetic / nice-to-have)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **L1** | L1↔L2 both independently tag BKIT layers | L1_PROMPT, L2_PROMPT | L2 should reference L1's layer tags instead of re-deriving | **XS** |
| **L2** | Phase 2 re-verification re-searches symbols subagents already reported with file:line | Lines 614-620 | Add: "Trust subagent file:line references unless contradiction detected." Skip re-verification if Lane data includes file:line evidence. | **XS** |

---

## Evolution Readiness

| Question | Answer |
|---|---|
| **Safe to auto-evolve?** | **NO** — requires manual resolution of C1 (widening contradiction) first |
| **Backup recommended before** | Entire Phase 1 section (lines 260-570) — widening rewrite touches dispatch protocol |
| **Estimated evolution tokens** | ~40K (substantial — Phase 1 logic restructuring) |
| **Quickest safe fix** | C3 (re-run install.sh) + H2 (add language markers) + M4 (reviewer tier change) = ~15 min, no logic risk |
| **Hardest fix** | C1 — requires deciding whether to keep widening (and remove one-batch claim) or keep one-batch (and remove widening) |

---

## Cross-Reference & Methodology Notes

### Review System Reliability

- **18 reviews in ~1 year**, 14 in a 6-day burst (Jun 14-20, 2026) — review churn, not steady quality improvement
- **Score oscillation**: 54.60–76.65 range (22-point spread) for essentially the same file version
- **R2 systematic inflation**: R2 subagent consistently returns 100/100, but cross-reference always finds only 4-8/11 gates truly enforceable. This calibration error has persisted across 5+ review rounds without correction.
- **Self-review bias**: The review framework uses `model=ultrabrain` for R6 (non-existent model — same class of bug it penalizes). The reviewer's own pricing table uses stale numbers. Systemic blindness: the review system has perfect vision for others' faults and no mirror.

### Installed Copy Emergency

**CRITICAL**: All 6 installed skills (`~/.reasonix/skills/blackcow-*.md`) reference `deepseek-v4-lite` — a non-existent model name. Every budget-tier lane dispatched by any skill will fail with an API 400 error. Re-run `skills/install.sh` immediately. This is a project-wide issue, not isolated to blackcow-plan.
