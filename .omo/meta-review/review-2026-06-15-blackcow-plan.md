# Meta-Review: blackcow-plan

| Field | Value |
|---|---|
| **Reviewed** | 2026-06-15T00:48:22Z |
| **Reviewer** | blackcow-skill-review (Metis 大将) |
| **Skill Version** | 2.0.0 (declared `updated: 2025-07-14`, mtime `2026-06-15T00:39:12Z`) |
| **Skill Type** | PLANNER — produces decision-complete plans; never edits product code |

## Overall Score

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| R1 Syntax & Structure | 85 | 15% | 12.75 |
| R2 Gate Completeness | 62 | 30% | 18.60 |
| R3 Parallelism Efficiency | 55 | 25% | 13.75 |
| R4 Cost Efficiency | 45 | 15% | 6.75 |
| R5 Staleness/Freshness | 42 | 15% | 6.30 |
| **TOTAL** | — | **100%** | **58.15** |

## Dimension Details

### R1: Syntax & Structure — 85/100

**Strengths**: Valid YAML frontmatter with all required fields. Consistent heading hierarchy (no skipped levels). All 20 `task()` dispatch blocks have correct parameters. All referenced skills (blackcow-loop, blackcow-librarian) exist on disk. No "RETURN" vs "RETURN EXACTLY" inconsistency — all 15 lane and reviewer prompts consistently use `RETURN EXACTLY:`.

**Issues Found**:

| # | File:Line | Issue | Severity |
|---|---|---|---|
| 1 | ~119, 153, 188, 197, 232, 243, 259, 276, 301, 320, 338, 359, 379, 401, 514, 602, 621, 641, 664, 683, 704 | **21 of 27 code blocks lack language markers** (bare ` ``` ` instead of ` ```text ` or ` ```markdown `) | LOW |
| 2 | ~177 | **`get_symbols` and `find_in_code`** referenced in Phase 1 dispatch protocol tool list but **absent from frontmatter `allowed-tools`**. Subagents attempting to use these tools may be denied at runtime. | MED |
| 3 | 12 | `web_search`, `research`, `run_skill`, `get_file_info` in `allowed-tools` but never explicitly invoked in any lane prompt body | LOW |
| 4 | ~195-208 | Static `task()` dispatch blocks show all 10 lanes unconditionally — visually contradicts the Intent-Based Dispatch Adjustment (lines 210-228) that says to skip lanes per intent | MED |

### R2: Gate Completeness — 62/100

This is a **PLANNER** skill. Scoring measures plan-template coverage of gates, not runtime enforcement. The Risk Register template (Phase 3e) documents all 11 BKIT gates. However, coverage is severely degraded by IntentGate and missing SUCCESS thresholds.

**Gate Coverage Matrix**:

| Gate | Risk Register | SUCCESS | Data Lane | Reviewer | IntentGate Risk | Overall |
|---|---|---|---|---|---|---|
| M1 spec-match | ✅ `M1_spec_match` | ✅ matchRate ≥ 90% | ❌ no lane | RVA | Emergency: no RVA | ⚠️ Partial |
| M2 test-pass | ✅ `M2_test_pass` | ✅ test pass=100% | ✅ L4 | RVA | Emergency: lost | ✅ Covered |
| M3 regression | ✅ `M3_regression` | ✅ coverage ≥ 80% | ✅ L4 | RVA | Emergency: lost | ✅ Covered |
| M4 lint-clean | ✅ `M4_lint_clean` | ✅ lint=0warn | ❌ no lane | RVA | Emergency: lost | ⚠️ Partial |
| M5 dead-code | ✅ `M5_dead_code` | ❌ MISSING | ❌ no lane | RVA | Emergency: lost | ⚠️ Template-only |
| S1 dataFlow | ✅ `S1_dataFlow` | ❌ MISSING | ✅ L3+L8 | RVB | Perf/Bug/Quality/Emergency: L8+RVB dropped | 🔴 Degraded |
| S2 auth | ✅ `S2_auth` | ❌ MISSING | ✅ L5+L8 | RVB | Same as S1 | 🔴 Degraded |
| S3 injection | ✅ `S3_injection` | ❌ MISSING | ✅ L8 | RVB | Same as S1 | 🔴 Degraded |
| P1 query | ✅ `P1_query` | ❌ MISSING | ✅ L9 | RVC | Bug/Sec/Quality/Emergency: L9 dropped | 🔴 Degraded |
| P2 memory | ✅ `P2_memory` | ❌ MISSING | ✅ L9 | RVC | Same as P1 | 🔴 Degraded |
| P3 latency | ✅ `P3_latency` | ✅ p95_target_ms | ✅ L9 | RVC | Bug/Sec/Quality/Emergency: L9 dropped | ⚠️ Degraded |

**IntentGate Gate Loss Summary**:

| Intent Class | Gates Fully Preserved | Gates Lost | Notes |
|---|---|---|---|
| **Feature** | 11/11 | 0 | Only clean intent class |
| **Performance** | 8/11 | S1, S2, S3 | L8 + RVB skipped |
| **Bug Fix** | 5/11 | S1, S2, S3, P1, P2, P3 | L8 + L9 skipped |
| **Security** | 8/11 | P1, P2, P3 | L9 skipped |
| **Quality** | 5/11 | S1, S2, S3, P1, P2, P3 | L8 + L9 skipped; RVB skipped |
| **Emergency** | 2/11 (M2, M3) | S1-S3, P1-P3, M1, M4, M5 degraded | XS lanes only, no reviewers |

**CRITICAL finding — IntentGate is documentation-only**: The Intent-Based Dispatch Adjustment table (lines 210-228) says "DO NOT blindly dispatch all 10 lanes" and provides intent-to-lane mappings. But the Dispatch Protocol above it (lines 195-208) shows hardcoded `task()` blocks dispatching all 10 lanes unconditionally. There is **no executable branching logic**. A subagent following the last-seen concrete code would dispatch all 10 lanes for every intent, wasting tokens and violating the intent optimization design.

### R3: Parallelism Efficiency — 55/100

**Strengths**: Phase 1 dispatches all 10 lanes in one batch (correct). Phase 4 dispatches all reviewers in parallel (correct). Platform adaptation note correctly maps `task()` → `explore()`.

**Issues Found**:

| # | File:Line | Issue | Severity |
|---|---|---|---|
| 1 | 42-47 | **Phase -1 IntentGate runs serially BEFORE Phase 0**. Zero data dependency between them — IntentGate parses `arguments` string, Cache Load reads filesystem. They could run concurrently but the instructions enforce serial ordering. | MED |
| 2 | 425-436 | **Phase 2 header says "run in ONE parallel batch" but lists 6 sequential inline operations** (grep → grep → read_file → contradiction → flag → layer check). None are dispatched as subagents. Mislabeled parallelism. | MED |
| 3 | 468-592 | **Phase 3 (Design) is a rigid serial waterfall**: 3a→3b→3c→3d→3e. All 5 sub-phases depend only on Phase 0/1 outputs, not on each other. They could be dispatched as parallel subagents. | MED |
| 4 | 232-252 vs 258-282 | **L1 (Surface Topology) and L2 (Call Graph) overlap ~40-50%**. Both trace ENTRY→EXIT paths with layer tags. L1's redundant flow diagram could be dropped in favor of L2's call-level precision. | MED |
| 5 | 39-41 | **Multi-feature mode generates per-feature plans sequentially**. After DAG is built, per-feature Phase 1-5 pipelines are independent and could run in parallel. | MED |
| 6 | 133 | **XL Scale table says "triple review" but Phase 4 uses 5 reviewers** ("Quintuple Adversarial Review"). Terminological contradiction persists. | LOW |
| 7 | 833 | **Constraint #3 says "Dispatch ALL lanes (XS:5, M:10, XL:10)" unconditionally** — directly contradicts Intent-Based Dispatch Adjustment that filters lanes per intent. | HIGH |

**Parallelism Health**: Only ~20% of the total skill process (Phase 1 lane dispatch + Phase 4 reviewer dispatch) is genuinely parallel. Phases -1, 2, 3, and multi-feature mode are serial or mislabeled.

### R4: Cost Efficiency — 45/100

**Strengths**: Lane-tier routing logic is sound (I/O lanes on budget, analysis lanes on pro). L8 (Security) and reviewers always forced to pro. XS skips Phase 4 entirely.

**Issues Found**:

| # | Finding | Detail | Severity |
|---|---|---|---|
| 1 | **Token estimates systematically ignore output tokens** | Skill claims Phase 1 M-scale = "10 lanes × ~5K = ~50K" but each lane returns 3-8K output. Realistic M-scale: ~112K input + ~88K output = **~201K total** vs declared 115K effective budget. **75% over budget.** | CRITICAL |
| 2 | **L6 web_fetch has no cap** | "For EVERY direct dependency... check latest version (use web_fetch)" — 50 deps = 50 web_fetch calls. No timeout, no limit, no caching. Single worst unbounded cost risk. | HIGH |
| 3 | **Phase 4 reviewer outputs NOT wired into Phase 5** | 5 pro-tier reviewers consume ~55-100K tokens but the Phase 5 plan template has only one review-related field (`N/N passed`). No per-reviewer findings section, no verdict incorporation mechanism. | HIGH |
| 4 | **Phase 4 token estimate off by 3-7×** | Skill claims Phase 4 = "~5K (M: 3 reviewers)" at line 163. Reality: each reviewer gets full draft plan (~25K) + prompt (~3K) = ~28K input + ~5K output = ~33K each. 3 reviewers = ~100K for Phase 4 alone. | HIGH |
| 5 | **Dead model tiers in installed copy** | `~/.reasonix/skills/blackcow-plan.md` defines `quick`/`deep`/`ultrabrain` tiers but none are ever dispatched in the plan skill. The description advertises `(budget|pro|quick|deep|ultrabrain)` falsely. | MED |
| 6 | **Reviewer C (Feasibility) and E (Minimalism) could use budget tier** | Both are gap-finding/pruning tasks, not deep synthesis. Switching to budget saves ~$0.07/1K output each. | LOW |
| 7 | **XS still dispatches 5 explore subagents** | For trivial single-file changes, 5 subagents is overkill. Could be reduced to 3 (L1, L4, L10). | LOW |

**Token Estimate for M-Scale (realistic)**:

| Phase | Input Tokens | Output Tokens | Total |
|---|---|---|---|
| Skill prompt + context (~9K) | 9,000 | — | 9,000 |
| Phase 1: 10 lanes × ~1K prompt + ~5K output | 10,000 | 50,000 | 60,000 |
| Phase 2: Cross-check (grep + read_file) | 3,000 | 3,000 | 6,000 |
| Phase 3: Design (5 sub-sections) | 5,000 | 10,000 | 15,000 |
| Phase 4: 3 reviewers × (~25K draft + ~5K output) | 75,000 | 15,000 | 90,000 |
| Phase 5: Synthesize | 10,000 | 10,000 | 20,000 |
| **Total** | **112,000** | **88,000** | **~200,000** |

Fits 115K budget? **NO** — overshoots by ~85K.

### R5: Staleness/Freshness — 42/100

**Strengths**: File actively modified (mtime today, 3 git commits in 3 days). All 6 referenced skills exist. No TODO/FIXME/HACK markers. BKIT taxonomy consistent throughout.

**Issues Found**:

| # | Finding | Detail | Severity |
|---|---|---|---|
| 1 | **`updated: 2025-07-14` is 11 months stale** | mtime is `2026-06-15`, last git commit is `2026-06-12`. The frontmatter date was manually rolled back to a pre-git value. Breaks any automation relying on `updated` for staleness detection. | CRITICAL |
| 2 | **3 divergent copies of the file exist** | `skills/blackcow-plan.md` (2-tier, has Intent dispatch), `~/.reasonix/skills/blackcow-plan.md` (5-tier, missing Intent dispatch table), `.bak` (5-tier, generic DAG example). The installed copy at `~/.reasonix/` lacks the Intent-Based Dispatch Adjustment — all 10 lanes would fire for every intent. | CRITICAL |
| 3 | **DAG example references creating already-existing files** | Phase 3d DAG tasks say "Create blackcow-skill-review.md" and "Create blackcow-skill-evolver.md" — both files already exist in `skills/`. Stale example data from initial authorship. `.bak` version has a generic OAuth example that avoids this. | MED |
| 4 | **XL reviewer count: "triple" vs "quintuple" vs "5"** | Scale table (line 133): "triple review". Phase 4 heading: "Quintuple Adversarial Review". Intent dispatch: "3-5". Description: "3-5". Three different terms for the same concept. | MED |
| 5 | **`get_symbols`/`find_in_code` absent from allowed-tools in ALL copies** | Dispatch protocol references these tools but they're missing from the allowed-tools frontmatter. `install.sh`'s `SKILL_EXTRA_MAC` also omits them for blackcow-plan. Runtime deny risk. | MED |
| 6 | **15 historical reviews show volatile scores (62-77) with no improvement trend** | Mean score ~69.2 over 11 months. Same critical issues recur (Intent dispatch not wired, `updated` field wrong, model tier drift). The review process reports but doesn't drive fixes. | HIGH |

**Trend Analysis (13 blackcow-plan reviews)**:

| Date | Score | R2 (Gates) | Trend |
|---|---|---|---|
| 2025-07-14 | 66.65 | 72 | Baseline |
| 2026-06-14 (peak) | 76.65 | 78 | ↑ Best score |
| 2026-06-15 (low) | 62.40 | 66 | ↓ Dip |
| 2026-06-16 | 69.00 | 78 | ↑ Recovery |
| 2026-06-18 | 63.00 | 72 | ↓ Dip |
| 2026-06-19 | 72.80 | 74 | ↑ Recovery |
| 2026-06-20 | 73.60 | 85 | ↑ Latest |

**Verdict**: Oscillating around ~69 with no monotonic improvement. The review process has frequency (14 reviews in 6 days) but no corrective loop — same CRITICAL findings flagged repeatedly without remediation.

## Cross-Reference Escalations

| # | Severity | Finding |
|---|---|---|
| E1 | **CRITICAL** | **Version fragmentation**: 3 divergent copies exist. `~/.reasonix/skills/blackcow-plan.md` (installed) is missing the 17-line Intent-Based Dispatch Adjustment table — meaning all 10 lanes always fire, defeating the intent-optimization design. Must re-run `install.sh` to sync. |
| E2 | **CRITICAL** | **`updated: 2025-07-14` is data corruption**: The field was rolled back to a pre-git date that doesn't correspond to any committed version. The git commit 9872e3f explicitly said "fix updated dates" but the working tree reverted. |
| E3 | **HIGH** | **Constraint #3 vs Intent table contradiction**: Constraint #3 says "Dispatch ALL lanes" which overrides the Intent-Based Dispatch Adjustment's lane filtering. Subagents reading Constraints as authoritative would skip intent filtering. |
| E4 | **HIGH** | **Review process is unhealthy**: 15 reviews, same CRITICAL issues recur (Intent table missing from installed copy, `updated` field wrong, `get_symbols`/`find_in_code` allowlist gap). The meta-review reports but does not drive corrective action. |
| E5 | **HIGH** | **SUCCESS enforces only 5 of 11 gates**: M5, S1, S2, S3, P1, P2 have no threshold in the Context Anchor SUCCESS template. The `--completion-promise` auto-generated from SUCCESS will not gate on these. |

## Recommendations

### Critical
| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| C1 | `updated` field is 11 months stale (2025-07-14) | Line 8 | Set to `2026-06-15`. Add pre-commit hook or review-gate to enforce `updated` is bumped on change. | TRIVIAL |
| C2 | 3 divergent file copies; installed copy missing Intent dispatch table | `~/.reasonix/skills/blackcow-plan.md` | Run `skills/install.sh` to sync installed copy from canonical source. Verify post-sync: `diff skills/blackcow-plan.md ~/.reasonix/skills/blackcow-plan.md`. | LOW |
| C3 | Token estimates ignore output tokens; realistic M-scale ~201K vs 115K budget | Lines 155-175 | Rewrite Context Budget section with realistic estimates including output tokens. Add note that Phase 4 reviewer duplication is the primary budget consumer. Consider draft-plan deduplication strategy. | MED |

### High
| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| H1 | Intent dispatch not wired — static `task()` blocks dispatch all 10 lanes unconditionally | Lines 195-208 vs 210-228 | Move static blocks AFTER intent adjustment section with "Feature intent only" label. Add conditional pseudocode showing lane selection per intent. | MED |
| H2 | Constraint #3 says "Dispatch ALL lanes" contradicting intent filtering | Line 833 | Rewrite: "Dispatch intent-appropriate lanes per Phase -1 IntentGate classification. Batch fire all selected lanes." | TRIVIAL |
| H3 | Phase 4 reviewer outputs not wired into Phase 5 template | Lines 722 vs 737-810 | Add "Reviewer Findings" section to Phase 5 plan template with per-reviewer verdict table + resolution notes. | LOW |
| H4 | L6 web_fetch has no cap | Lines 285-295 | Add: "Cap at 15 dependencies. For projects with >15 deps, prioritize by relevance to task scope." | TRIVIAL |
| H5 | `get_symbols`/`find_in_code` missing from allowed-tools | Line 13 | Add to frontmatter `allowed-tools`. Update `install.sh` SKILL_EXTRA_MAC if needed. | TRIVIAL |

### Medium
| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| M1 | Phase -1 IntentGate serial before Phase 0 | Lines 42-47 vs 100-120 | Allow parallel execution: "Phase -1 and Phase 0.0 may run concurrently. Merge results before Phase 1." | TRIVIAL |
| M2 | Phase 2 labeled "parallel batch" but runs sequentially | Lines 425-436 | Relabel to "Sequential Verification" or dispatch items 1-3 as parallel explore subagents. | LOW |
| M3 | Phase 3 is serial waterfall (3a→3b→3c→3d→3e) | Lines 468-592 | Dispatch sub-phases as parallel subagents — they share only Phase 1/2 inputs, not each other's outputs. | MED |
| M4 | L1/L2 overlap ~40-50% on entry→exit tracing | Lines 232-282 | Drop L1's ENTRY→EXIT flow diagram; let L2 produce the sole call-graph flow. L1 focuses on file tree + exports only. | LOW |
| M5 | DAG example creates already-existing skill files | Lines ~500-550 | Replace with generic OAuth/session example as in `.bak` version. | TRIVIAL |
| M6 | XL reviewer count: "triple" vs "quintuple" vs "5" | Lines 133, 598, 3 | Unify to "5" or "Quintuple" everywhere. Change line 133: "triple review" → "quintuple review." | TRIVIAL |
| M7 | Dead model tiers (`quick`/`deep`/`ultrabrain`) in installed copy | `~/.reasonix/skills/blackcow-plan.md:11-13` | Remove from description and model_tiers. Keep only `budget`/`pro` to match canonical source. Run `install.sh` to sync. | TRIVIAL |

### Low
| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| L1 | 21 code blocks lack language markers | ~119-704 | Add `text` or `markdown` language markers to all bare ``` blocks. | TRIVIAL |
| L2 | Multi-feature per-feature plans generated sequentially | Lines 39-41 | Dispatch per-feature Phase 1-5 pipelines in parallel after master plan + DAG are built. | MED |
| L3 | `web_search`, `research`, `run_skill`, `get_file_info` in allowed-tools but never used in lane prompts | Line 12 | Remove unused tools or document their intended use case. | TRIVIAL |
| L4 | Reviewer C (Feasibility) and E (Minimalism) could use budget tier | Lines 603-607 | Change `model=pro` to `model=budget` for RVC and RVE. | TRIVIAL |
| L5 | XS dispatches 5 lanes for trivial tasks | Lines 189-193 | Consider reducing to 3 lanes (L1, L4, L10) for <200-line single-file changes. | LOW |

## Evolution Readiness

- **Safe to auto-evolve?**: **NO — requires manual actions first**
  - C2 (run `install.sh` to sync copies) must be done manually
  - C3 (rewrite token budget estimates) requires design judgment
  - H1 (restructure dispatch protocol) requires careful restructuring
  
- **Quick wins safe to auto-apply**: C1 (fix `updated`), H3 (add reviewer section to Phase 5 template), H4 (cap L6 web_fetch), H5 (add tools to allowed-tools), M1 (allow Phase -1 ∥ Phase 0), M5 (replace DAG example), M6 (unify reviewer count terms), M7 (remove dead tiers), L1 (add language markers), L3 (clean allowed-tools), L4 (downgrade RVC/RVE tiers)

- **Backup recommended before**: Phase 1 dispatch blocks (lines 188-238), Context Budget section (lines 154-175), Phase 5 plan template (lines 737-810)

- **Estimated evolution tokens**: ~25-35K for TRIVIAL+LOW fixes. ~60-80K for full remediation including MED+HIGH.

## Review Process Health Assessment

**UNHEALTHY**. 15 reviews over 11 months with volatile scores (62-77 range, mean ~69) and no monotonic improvement trend. The same CRITICAL findings flagged repeatedly:

- `updated` field wrong: flagged in 10+ reviews, still `2025-07-14`
- Version drift: flagged in 6+ reviews, `.bak` and `~/.reasonix` still diverge
- `get_symbols`/`find_in_code` allowlist gap: flagged in every review, never fixed
- Intent dispatch not wired: flagged in 3+ reviews, static blocks still unconditional

The meta-review process reports but does not gate. Remediation requires either:
a) Gate `blackcow-skill-evolver` auto-evolution behind review score ≥ 75 (currently 58.15 — would block), or
b) Add a review SLA: CRITICAL findings must be resolved before the next meta-review cycle.
