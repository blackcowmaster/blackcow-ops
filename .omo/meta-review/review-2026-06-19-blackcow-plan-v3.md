# Meta-Review: blackcow-plan

| Field | Value |
|---|---|
| **Reviewed** | 2026-06-19T12:30:00Z |
| **Reviewer** | blackcow-skill-review (Metis 大将) |
| **Skill Version** | 2.0.0 (declared `updated: 2026-06-19`, mtime 2026-06-15T00:29:17Z) |
| **Skill Type** | PLANNER — produces decision-complete plans; never edits product code |

## Overall Score

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| R1 Syntax & Structure | 72 | 15% | 10.8 |
| R2 Gate Completeness | 65 | 30% | 19.5 |
| R3 Parallelism Efficiency | 60 | 25% | 15.0 |
| R4 Cost Efficiency | 52 | 15% | 7.8 |
| R5 Staleness/Freshness | 70 | 15% | 10.5 |
| **TOTAL** | — | **100%** | **63.6** |

> **Score context**: Down from 72.8 (v2, 2026-06-19 08:15). The drop reflects R6 adversarial challenge sustained on all three dimensions — the Intent Routing table is unwired (R2), Phase 2/3 are serial despite "parallel" labeling (R3), and real token costs are 3-5× the declared estimates (R4). The global install staleness (P0 deployment hazard) is a new escalation this cycle.

---

## Dimension Details

### R1: Syntax & Structure — 72/100

**Strengths**: Valid YAML frontmatter, consistent heading hierarchy (H1→H2→H3), well-formed markdown tables, no broken cross-references to sibling skills.

**Issues Found**:

| # | File:Line | Issue | Severity |
|---|---|---|---|
| 1 | 190–386, 587–707 | 17 bare ``` blocks without language markers (`text`/`markdown`/`yaml`). All lane prompts and reviewer prompts affected. | LOW |
| 2 | 131, 167 vs 600, 616 | **Triple/quintuple inconsistency**: Scale table (line 131) says "triple review" for XL, Phase 1 note (line 167) says "triple adversarial review", but Phase 4 header (line 600) says "Quintuple Adversarial Review" and reviewer table (line 616) shows 5 reviewers (A,B,C,D,E). Triple and quintuple are incompatible. | MED |
| 3 | 185 | `task()` pseudo-code used throughout ~20 dispatch blocks instead of platform-native `explore()`. Adaptation note exists but requires mental translation. | MED |
| 4 | 14 | `allowed-tools` uses kebab-case — may not match platform's `allowedTools` (camelCase) convention. | LOW |

---

### R2: Gate Completeness — 65/100

> **Methodology note**: This score measures **operational enforcement coverage** — can the downstream executor actually verify each gate? R2's subagent scored 90 on template coverage (gate appears in Risk Register). The honest PLANNER-adjusted score is 65. The 25-point gap is because 7/11 gates exist in templates but are structurally unreachable by the executor.

**Gate Coverage Matrix**:

| Gate | Status | Evidence | Enforcement Gap |
|---|---|---|---|
| **M1** spec-match | ✅ COVERED | SUCCESS `matchRate ≥ 90%`; Gap Matrix; Risk Register; RVA checks spec match | None — wired through SUCCESS + RVA |
| **M2** test-pass | ✅ COVERED | SUCCESS `test pass=100%`; L4 collects CI command; Risk Register; per-step gate tag | None — wired through SUCCESS |
| **M3** regression | ⚠️ RISK REGISTER ONLY | Gap Matrix `🔧 Modify → M3`; Risk Register row "0 regressions" | **NOT in SUCCESS criteria**. Executor has no `--completion-promise` threshold for regressions. |
| **M4** lint-clean | ✅ COVERED | SUCCESS `lint=0warn`; Risk Register row | None — wired through SUCCESS |
| **M5** dead-code | ❌ TEMPLATE HOLLOW | Gap Matrix `🗑️ Delete → M5`; Risk Register row | **Zero data-collection lanes**. No lane searches for unused exports. L1 lists exports but never cross-references callers. Gap Matrix `🗑️ Delete` rows are populated by guesswork. |
| **S1** dataFlow | ⚠️ WEAK | L3 flags `DATAFLOW RISKS` with S1 tag; L8 checks data exposure; RVB scores dataFlow integrity | **NOT in SUCCESS criteria**. RVB's DATAFLOW INTEGRITY SCORE is produced but never gates plan acceptance. |
| **S2** auth | ⚠️ WEAK | L8 checks auth middleware; Risk Register row; RVB security review | **NOT in SUCCESS criteria**. No `curl → 401` verification wired into Waves template. |
| **S3** injection | ⚠️ WEAK | L8 audits injection surfaces; Risk Register row; RVB | **NOT in SUCCESS criteria**. No input-sanitization checkpoint in execution contract. |
| **P1** query | ⚠️ WEAK | L9 checks N+1 patterns; Risk Register row; RVC checks P-thresholds | **NOT in SUCCESS criteria**. Only P3 (latency) appears in SUCCESS. |
| **P2** memory | ⚠️ WEAK | L9 checks unbounded growth; Risk Register row | **NOT in SUCCESS criteria**. |
| **P3** latency | ✅ COVERED | SUCCESS `p95_target_ms: <N>`; L9 gathers latency data; Risk Register | None — wired through SUCCESS |

**CRITICAL finding — Intent Routing is NOT wired to dispatch**:

The Phase -1 Intent Routing table (lines 89–103) describes lane adjustments per intent class (Performance skips L8+Reviewer B, Emergency runs only L1-L5, etc.). However, Phase 1 dispatch blocks (lines 190–219) fire all 10 lanes unconditionally — zero `if`/`switch` branching on intent class. The "Intent-Based Dispatch Adjustment" section (lines 221–240) says "After dispatching... REMOVE lanes" — but subagents dispatched with `run_in_background=true` cannot be retroactively cancelled. **The routing table is documentation that a human operator must follow manually; it is not wired to automated dispatch.**

**IntentGate Gate Loss (if routing WERE wired)**:

| Intent | Gates Without Data Collection | Reviewer Gaps |
|---|---|---|
| Performance | S1, S2, S3 (L8 skipped) | Reviewer B (Security) skipped |
| Bug Fix | P1, P2, P3 (L9 skipped) | Reviewer D (Architecture) skipped |
| Security | P1, P2, P3 (L9 skipped) | — |
| Quality | S1, S2, S3, P1, P2, P3 (L8+L9 skipped) | Reviewer B skipped |
| Emergency | S1-S3, P1-P3 (L6-L10 skipped) | ALL reviewers skipped |

**Reviewer B+ ghost**: Security intent routing (line ~91) references "Reviewer B+" — a reviewer that does not exist in any dispatch block or prompt definition. Only Reviewers A-E are defined (lines 606–610).

---

### R3: Parallelism Efficiency — 60/100

**Strengths**: Phase 1 dispatches all 10 lanes in one true parallel batch. Phase 4 dispatches all reviewers simultaneously. Adaptive lane count (XS=5, M=10, XL=10) is well-designed. Wave-level parallelism with DAG notation in Phase 3d is architecturally sound.

**Issues Found**:

| # | File:Line | Issue | Severity |
|---|---|---|---|
| 1 | 47–57 | **Phase -1 IntentGate serial before Phase 0**. IntentGate (parse arguments, classify intent) and Phase 0.0 Cache Load have zero data dependency. They could run in parallel. Every invocation pays this serial latency. | MED |
| 2 | 425–436 | **Phase 2 "ONE parallel batch" is false labeling**. Listed as parallel but contains 6 sequential `search_content`/`read_file` operations — NO subagent dispatches. These are inline grep commands in the main agent. | MED |
| 3 | 438–588 | **Phase 3 Design is a pure serial waterfall**: 3a (Context Anchor) → 3b (Arch Options) → 3c (Gap Matrix) → 3d (Waves) → 3e (Risk Register). Each depends on the previous. Architecturally correct (output feeds input) but contributes 4-8 minutes of serial wall-clock. | MED |
| 4 | 39–41 | **Multi-feature per-feature plans generated sequentially**. After dependency graph is built, independent features could dispatch parallel Phase 1-5 pipelines. | MED |
| 5 | 232–282 | **L1 and L2 overlap on entry→exit tracing**. L1's ENTRY→EXIT flow diagram and L2's upstream/downstream call chains trace the same conceptual path at different granularity. ~40% of L1 and ~30% of L2 produce redundant diagrams. | LOW |
| 6 | 131, 167 vs 600 | **Reviewer count inconsistency**: Scale table says M="1 reviewer", Phase 4 says M=3. XL described as "triple" vs "quintuple." | MED |

**Batch integrity**: Phase 1 (10 lanes) and Phase 4 (5 reviewers) are correctly batch-dispatched. Phase 2 is falsely labeled as parallel. Everything else is sequential.

---

### R4: Cost Efficiency — 52/100

**Strengths**: Lane-tier routing is well-justified — budget for I/O-bound lanes (L1/L4/L5/L7/L10), pro for analysis lanes (L2/L3/L6/L8/L9). L8 and all reviewers forced to pro regardless of `--model-tier`. XS scale skips Phase 4 entirely (correct cost trade-off).

**Issues Found**:

| # | Finding | Detail | Severity |
|---|---|---|---|
| 1 | **Token estimates ignore output tokens** | Skill claims M-scale Phase 1 ≈ 50K (10 lanes × 5K input). Realistic: 10 lanes × (5K input + 4K output) + tool-reads within subagents = ~130K for Phase 1 alone. Total invocation ≈ 290-364K vs claimed ~70K — **3-5× undercount**. Exceeds declared 115K effective budget, triggering Constraint #10 plan-split. | **CRITICAL** |
| 2 | **Intent routing unwired — all lanes always run** | Every invocation pays for all 10 lanes regardless of intent. Performance intent pays for L8 (Security) despite routing table claiming to skip it. Emergency intent pays for L6-L10. Tokens burned on data the plan claims to avoid. | **HIGH** |
| 3 | **Phase 4 reviewer outputs unused** | Phase 5 says "incorporate ALL findings" but plan template shows only "Adversarial reviews: N/N passed" as a summary field. No resolution table, no rejection reconciliation, no evidence findings change the plan. 99K tokens (M-scale, 3 reviewers × 33K) with uncertain marginal value. | HIGH |
| 4 | **XS scale is wasteful** | 5 explore subagents for tasks <200 lines in 1 file. Each explore has ~700 token overhead + tool setup. A single `read_file` would suffice for most XS tasks. | MED |
| 5 | **L6 web_fetch unbounded** | "For EVERY direct dependency… check latest version (use web_fetch)." 50-dependency project = 50 web_fetch calls. No cap, no "top N" constraint. | MED |
| 6 | **L6 has no gate binding** | Dependency Audit contributes to no specific BKIT gate. Its output (version delta table) informs no threshold in SUCCESS or Risk Register. Pure information — no gate depends on it. | MED |

**Realistic Token Estimate (M-scale, 10 lanes + 3 reviewers)**:

| Component | Input | Output | Total |
|---|---|---|---|
| Parent agent (Phase -1→Phase 5) | 50K | 22K | 72K |
| Phase 1 — 5 budget lanes (L1/L4/L5/L7/L10) | 55K | 10K | 65K |
| Phase 1 — 5 pro lanes (L2/L3/L6/L8/L9) | 80K | 15K | 95K |
| Phase 2 (parent) | 5K | 3K | 8K |
| Phase 3 (parent) | 5K | 10K | 15K |
| Phase 4 — 3 reviewers (each gets full plan ≈30K) | 93K | 6K | 99K |
| Phase 5 (parent) | 5K | 3K | 8K |
| **TOTAL** | **~293K** | **~71K** | **~364K** |

> **Declared budget**: ~70K. **Actual**: ~364K. **Undercount factor**: 5.2×.
> 
> **Est. cost**: ~$0.076 per M-scale invocation (budget $0.07/1M in, pro $0.14/1M in).

---

### R5: Staleness/Freshness — 70/100

**Strengths**: File modified 4 days ago (mtime 2026-06-15). All 6 sibling skills exist. BKIT 11-gate taxonomy consistently applied. No TODO/FIXME/HACK markers. Active development evident from 12+ review cycles.

**Issues Found**:

| # | Finding | Detail | Severity |
|---|---|---|---|
| 1 | **Global install critically stale** | `~/.reasonix/skills/blackcow-plan.md` uses `deepseek-v4-lite` (possibly invalid model), has 5-tier aliases (`quick`/`deep`/`ultrabrain` — 3 dead), `updated: 2026-06-12`. `run_skill` loads from global, not local. ALL 6 global skill files are stale. | **CRITICAL** |
| 2 | **Frontmatter future-date claim** | `updated: 2026-06-19` declared but mtime is 2026-06-15 — 4-day gap. Aspirational metadata, not factual. | MED |
| 3 | **Recurring issues across 12+ reviews** | Dead model tiers, triple/quintuple inconsistency, bare code blocks, unwired Intent Routing — all flagged repeatedly without resolution. Process failure, not staleness. | HIGH |
| 4 | **Score trend oscillating without direction** | Scores range 62-77 across 12 reviews with 5-10 point volatility day-over-day. Staleness subscore improving (55→80) but total scores show no clear convergence. Adversarial criteria tighten each cycle. | MED |

**Trend Analysis (blackcow-plan only, from review-history.jsonl)**:

| Date | Score | Trend |
|---|---|---|
| 2025-07-14 | 66.65 | 11-month-old baseline |
| 2026-06-14 22:35 | 76.65 | Peak |
| 2026-06-15 00:35 | 62.40 | Trough (adversarial review introduced) |
| 2026-06-16 | 69.00 | Partial recovery |
| 2026-06-17 00:00 | 71.50 | — |
| 2026-06-18 00:00 | 63.00 | Drop (critical count rose to 4) |
| 2026-06-19 08:15 | 72.80 | Recovery (model name partially fixed) |
| 2026-06-19 10:30 | 66.50 | Deeper scrutiny (R6 Devil's Advocate) |
| **2026-06-19 12:30** | **63.60** | **This review — R6 sustained on all dimensions** |

**Freshness Recommendation**: **Weekly** while under active development. Downgrade to monthly once global install is synced and recurring issues are resolved.

---

## Cross-Reference Escalations

| # | Finding | Severity | Detail |
|---|---|---|---|
| **E1** | **Global install critically stale — ALL 6 skills** | **CRITICAL** | `~/.reasonix/skills/blackcow-plan.md` uses `deepseek-v4-lite` (possibly invalid model), has 5-tier aliases, and is 7 days behind local. `run_skill` loads from global. Run `bash skills/install.sh` immediately. |
| **E2** | **Intent-Based Dispatch Adjustment is documentation theater** | **CRITICAL** | Phase 1 dispatch fires all 10 lanes unconditionally (lines 190-219). "After dispatching... REMOVE lanes" (line 221) is impossible — subagents can't be cancelled. The routing table (lines 89-103) has zero code path to enforcement. |
| **E3** | **SUCCESS contract enforces only 4/11 BKIT gates** | **HIGH** | Context Anchor SUCCESS has `matchRate ≥ 90%`, `test pass=100%`, `lint=0warn`, `p95_target_ms`. That's M1, M2, M4, P3 only. M3, M5, S1-S3, P1-P2 exist in Risk Register but are invisible to `blackcow-loop`'s `--completion-promise`. |
| **E4** | **Reviewer B+ ghost** | **HIGH** | Security intent routing (line ~91) references "Reviewer B+" — no such reviewer defined. Only A-E exist. Security-critical intents promise adversarial scrutiny that cannot be delivered. |
| **E5** | **Token budget claims off by 5.2×** | **HIGH** | Declared ~70K per M invocation. Realistic estimate: ~364K. Exceeds 115K effective budget by 3.2×, triggering plan-split for nearly every invocation. |
| **E6** | **Phase 4 reviewer outputs structurally unused** | **MED** | Phase 5 plan template has no resolution table, no rejection loop. 99K reviewer tokens (M-scale) consumed with advisory-only output. |

---

## Recommendations

### Critical (score < 70 equivalent impact)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| C1 | Global install stale — `run_skill` loads wrong file | `~/.reasonix/skills/blackcow-plan.md` | Run `bash skills/install.sh` to sync all 6 skills. Verify `deepseek-v4-flash` in global install after sync. | TRIVIAL |
| C2 | Intent-Based Dispatch Adjustment unwired | 89–103 vs 190–219 | Rewrite Phase 1 dispatch to conditionally build lane list based on intent class BEFORE dispatching. Remove "after dispatching, REMOVE lanes" language. OR remove the routing table and document that all lanes always run. | HIGH |
| C3 | SUCCESS enforces only 4/11 gates | 418–424 | Expand SUCCESS template to include: M3 (0 regressions), M5 (0 unused exports), S1 (integrity ≥ 85%), S2 (all entry points protected), S3 (all inputs validated), P1 (no N+1), P2 (pagination present). | LOW |

### High

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| H1 | Reviewer B+ ghost | ~91 | Remove "Reviewer B+" reference from Security intent row. Either define a real Reviewer B+ prompt or document that existing Reviewer B (Security) suffices. | TRIVIAL |
| H2 | Token estimates off by 5.2× | 145–175 | Replace estimates with realistic numbers including output tokens and subagent tool-read overhead. Add explicit note: "M-scale ≈ 290-364K total across all threads. Typical invocation exceeds 115K effective budget — plan-split expected for most M/XL tasks." | LOW |
| H3 | Phase 4 reviewer outputs not structurally incorporated | 700–810 | Add "Review Resolution" table to Phase 5 plan template: per-reviewer findings with ACCEPTED/REJECTED/COMPROMISE disposition. Gate Phase 5 completion on resolution of all CRITICAL reviewer findings. | MED |
| H4 | Phase 2 mislabeled as "parallel batch" | 425–436 | Relabel to "Sequential Cross-Check" or dispatch 2-3 parallel explore subagents for independent verification domains. | LOW |

### Medium

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| M1 | Triple/quintuple inconsistency | 131, 167 | Change "triple review" → "quintuple review" on lines 131 and 167 to match Phase 4's 5-reviewer implementation. | TRIVIAL |
| M2 | Frontmatter `updated: 2026-06-19` future-date claim | 6 | Set `updated:` to actual last-edit date (2026-06-15) or commit changes and align. | TRIVIAL |
| M3 | XS scale wasteful (5 explore for trivial tasks) | 145 | Reduce XS to 3 lanes: drop L3 (Data Shape — tiny codebase has minimal types) and L5 (Config — single-file projects have no config matrix). | LOW |
| M4 | L6 web_fetch unbounded + no gate binding | 355–377 | Cap web_fetch calls at 15 dependencies. Add BKIT gate tag to L6 output (M3: regression risk from breaking dependency changes). OR skip L6 entirely for intents where no dependency changes expected. | LOW |
| M5 | Phase -1 IntentGate serial before Phase 0 | 47 vs 100–120 | Restructure: run IntentGate analysis AND Cache Load as parallel operations. Intent classification has zero dependency on cache staleness. | LOW |
| M6 | L1/L2 overlap on entry→exit tracing | 232–282 | Remove ENTRY→EXIT flow requirement from L1. Keep file tree + public API surface + layer integrity. Let L2 own all call-level tracing. Saves ~2K tokens per Phase 1. | LOW |

### Low

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| L1 | 17 bare ``` blocks lacking language markers | 190–386, 587–707 | Add `text` or `markdown` language markers to all bare ``` blocks. | TRIVIAL |
| L2 | `task()` pseudo-code in ~20 dispatch blocks | 185, 210, 217, 587+ | Either: (a) replace all `task()` with `explore()` in the skill body, or (b) add a one-time adaptation block at the top that maps syntax. Current mid-stream mapping at line ~185 is easy to miss. | LOW |
| L3 | `allowed-tools` kebab-case vs platform `allowedTools` | 14 | Verify platform convention and align. | TRIVIAL |
| L4 | L6 no gate binding | 355–377 | Add `BKIT Gate: M3 (regression)` tag to L6 prompt output schema. | TRIVIAL |
| L5 | M-scale reviewer dispatch hardcodes all 5 | 605–610 | Add M-scale dispatch block with 3 `explore()` calls (A, B, C) alongside the XL 5-call block. | LOW |

---

## Evolution Readiness

- **Safe to auto-evolve?**: **PARTIALLY**. 8 of 17 recommendations are TRIVIAL effort and safe to auto-apply (L1, M1, M2, H1, L3, L4, C1, H2). Critical finding C2 (rewiring Intent dispatch) requires manual design decision — wire it or remove it. Critical finding C3 (expanding SUCCESS) requires agreement on gate thresholds.
- **Backup recommended before**: Phase -1 IntentGate (lines 47–108), Phase 1 dispatch protocol (lines 175–240), Phase 3d DAG (lines 534–580), Context Anchor SUCCESS (lines 418–424), Phase 4 reviewer dispatch (lines 600–640).
- **Estimated evolution tokens**: ~50-65K for full remediation of all CRITICAL + HIGH findings. ~15K for TRIVIAL-only quick wins.
- **Quick wins (safe to auto-apply)**: L1 (language markers), M1 (triple→quintuple), M2 (bump updated date), H1 (remove Reviewer B+ ghost), L3 (allowed-tools case), L4 (L6 gate tag), C1 (run install.sh), H2 (update token estimates).
