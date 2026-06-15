# Meta-Review: blackcow-plan

| Field | Value |
|---|---|
| **Reviewed** | 2026-06-20T01:15:00Z |
| **Reviewer** | blackcow-skill-review (Metis 大将) |
| **Skill Version** | 2.0.0 (repo: `updated: 2026-06-15`, file mtime: 2026-06-15; installed: `updated: 2026-06-12`, file mtime: 2026-06-14) |
| **Last Git Commit** | `9872e3f` — 2026-06-12 "fix: Fable round 2 leftovers… fix updated dates" |
| **Lines** | 845 (repo) / 830 (installed) — 15-line delta |

---

## Overall Score

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| R1 Syntax & Structure | 72 | 15% | 10.80 |
| R2 Gate Completeness | 64 | 30% | 19.20 |
| R3 Parallelism Efficiency | 67 | 25% | 16.75 |
| R4 Cost Efficiency | 62 | 15% | 9.30 |
| R5 Staleness/Freshness | 55 | 15% | 8.25 |
| **TOTAL** | — | **100%** | **64.30** |

### Score Trends

| Date | Total | R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|---|---|
| 2026-06-14 (v1) | 72.80 | 80 | 80 | 65 | 75 | 62 |
| 2026-06-15 (v2) | 58.15 | 85 | 62 | 55 | 45 | 42 |
| 2026-06-17 (v3) | 70.90 | 78 | 78 | 65 | 75 | 55 |
| 2026-06-19 (v4) | 73.60 | 78 | 85 | 70 | 68 | 58 |
| **2026-06-20 (v5)** | **64.30** | **72** | **64** | **67** | **62** | **55** |

**Why the drop from v4?** XR2 cross-reference revealed R2 self-audit gap: structural gate tagging ≠ enforceable gate coverage (36-point inflation corrected). R5 downgraded for installed copy using non-existent model name `deepseek-v4-lite`. R4 pricing errors confirmed (2-3× understated).

---

## Dimension Details

### R1: Syntax & Structure — 72/100

| Check | Status | Evidence |
|---|---|---|
| YAML frontmatter | ✅ PASS | All 8 required fields present |
| Heading hierarchy | ✅ PASS | H1→H2→H3, no skipped levels |
| `task()` dispatch syntax | ✅ PASS | All use correct `task(description=..., prompt=..., run_in_background=true, max_steps=..., model=...)` |
| Lane prompt structure | ✅ PASS | All 10 L1-L10 have context→action→RETURN EXACTLY→output schema |
| Reviewer prompts | ✅ PASS | All 5 RVA-RVE use `RETURN EXACTLY:` (fixed from v4's `RETURN:` drift) |
| `updated` date accuracy | ✅ FIXED | `2026-06-15` matches file mtime (was `2026-06-19` future-date in v4) |
| Broken references | ✅ PASS | No references to non-existent skills/files |
| Bare code fences | ❌ 14+ bare ``` | L1-L10 lane prompts, dispatch blocks, and Waves example lack language markers |
| `allowed-tools` mismatch | ❌ 2 missing | `get_symbols` and `find_in_code` referenced in Phase 1 dispatch protocol but absent from frontmatter `allowed-tools` |

**FRONTMATTER ISSUES:**

| # | Issue | Severity |
|---|---|---|
| 1 | 14+ bare code fences (` ``` `) without language markers across L1-L10 prompts, dispatch blocks, Waves example. Suggest ` ```text ` or ` ```yaml `. | MED |
| 2 | `allowed-tools` missing `get_symbols, find_in_code` — tools listed in Phase 1 dispatch protocol for lane subagents but absent from frontmatter whitelist. If runtime enforces `allowed-tools`, lanes will fail. | HIGH |
| 3 | `allowed-tools` uses CSV string format rather than YAML list — consumer may need `.split(",")`. | LOW |

---

### R2: Gate Completeness — 64/100

**Assessment:** All 11 BKIT gates have structural presence (Risk Register rows, lane coverage, reviewer assignments). However, only **4 of 11 gates** have actionable numeric thresholds in the Context Anchor SUCCESS field — the plan's single contract for gate verification. The remaining 7 gates have placeholder, qualitative, or no thresholds in the SUCCESS field. This is a **36-point self-audit gap** from the claimed 100.

**Gate Coverage Matrix:**

| Gate | Status | Context Anchor SUCCESS Threshold | Risk Register | Lane Coverage | Reviewer |
|---|---|---|---|---|---|
| **M1** spec-match | ✅ COVERED | `matchRate ≥ 90%` (numeric) | ✅ | L1, L2, L10 | RVA |
| **M2** test-pass | ✅ COVERED | `test pass=100%, coverage ≥ 80%` (numeric) | ✅ | L4 | RVA |
| **M3** regression | ⚠️ PARTIAL | ❌ Not in SUCCESS field | ✅ `0 regressions` | L4, L7 | RVA |
| **M4** lint-clean | ✅ COVERED | `lint=0warn` (numeric) | ✅ | — | RVA |
| **M5** dead-code | ⚠️ PARTIAL | ❌ Not in SUCCESS field | ✅ `0 unused exports` | — | RVE |
| **S1** dataFlow | ⚠️ PARTIAL | ❌ Not in SUCCESS field | ✅ `integrity ≥ 85%` | L3, L8 | RVB |
| **S2** auth | ⚠️ PARTIAL | ❌ Not in SUCCESS field | ✅ `모든 진입점 보호` (qualitative) | L5, L8 | RVB |
| **S3** injection | ⚠️ PARTIAL | ❌ Not in SUCCESS field | ✅ `모든 입력 검증` (qualitative) | L8 | RVB |
| **P1** query | ⚠️ PARTIAL | ❌ Not in SUCCESS field | ✅ `No N+1, index used` (qualitative) | L9 | RVC |
| **P2** memory | ⚠️ PARTIAL | ❌ Not in SUCCESS field | ✅ `No unbounded growth` (qualitative) | L9 | RVC |
| **P3** latency | ⚠️ PARTIAL | `p95_target_ms: <N> or N/A` (placeholder) | ✅ `p95 < target` | L9 | RVC |

**Intent Table Bugs (Phase -1 routing vs Phase 1 dispatch):**

| # | Bug | Detail | Severity |
|---|---|---|---|
| 1 | **Bug Fix skips L6 without routing authorization** | Phase -1 routing says "Skip L9/L10"; Phase 1 dispatch silently adds L6=❌ and L8=❌ | MED |
| 2 | **Performance skips L6/L10 without routing authorization** | Phase -1 routing says "Skip L8; add L9 deep-dive"; Phase 1 dispatch silently adds L6=❌, L10=❌ | MED |
| 3 | **Emergency forces all 5 lanes to pro (✅p)** | Phase -1 says "XS lanes only (L1-L5)" but XS normally uses budget tier for L1/L4/L5. Mechanical lanes forced to pro — wasteful. | LOW |
| 4 | **Security skips L9 (Performance)** | DoS is a security concern. Performance profiling directly informs availability impact. Should be ✅ at budget tier. | MED |

**Threshold Consistency:**

| Issue | Detail |
|---|---|
| Context Anchor SUCCESS field incomplete | Only M1, M2, M4, P3 thresholds present. M3, M5, S1-S3, P1-P2 thresholds only in Risk Register |
| S2/S3 thresholds are qualitative | "모든 진입점 보호" / "모든 입력 검증" — pass/fail booleans, not numeric |
| Constraint 13 violated | "All quality gates must have explicit numeric thresholds" — but S2, S3, P1, P2 use non-numeric thresholds |

---

### R3: Parallelism Efficiency — 67/100

| Check | Status | Evidence |
|---|---|---|
| Phase 1 batch dispatch | ✅ PASS | All lanes dispatched with `run_in_background=true` |
| Phase 4 reviewer dispatch | ✅ PASS | 3-5 reviewers dispatched simultaneously |
| Intent-based lane skipping | ✅ PASS | Reduces dispatch count for non-Feature intents |
| Lane independence | ✅ PASS | L1-L10 are independent reads of different aspects |

**Serialization & Design Issues:**

| # | Finding | File:Line | Severity |
|---|---|---|---|
| 1 | **Phase 2 falsely labeled "parallel batch"** — 6 cross-check items are inline grep/read operations in the main agent with NO `task()` or `explore()` dispatch. No `run_in_background`, no subagent isolation. They execute sequentially in the planner's context. | `skills/blackcow-plan.md`: lines 428-436 | **HIGH** |
| 2 | **Phase 0 is entirely serial** — Cache load → legacy discovery → scale classification → tier routing → budget estimation all sequential before Phase 1 parallelism. ~4.5K tokens burned before any parallel work begins. Cache load and `glob(.git/HEAD)` have no data dependency and could parallelize. | Phase 0 section | MED |
| 3 | **XL = M in execution** — XL dispatches identical 10 lanes as M. Platform adaptation note (line ~185) says to "ignore `model` parameters (they are budget hints, not enforced)." If `model=pro` is decorative, XL differentiation collapses to just +2 reviewers. | Phase 1 XL section + line 185 | **CRITICAL** |
| 4 | **No failure/retry/degraded-mode handling** — If any Phase 1 lane times out (L8 Security especially), plan proceeds blind. No retry, no `[DEGRADED]` flag, no gate-skipping protocol. Single-point-of-failure for S1/S2/S3 gate data. | Entire Phase 1 | **HIGH** |
| 5 | **L5↔L8 overlap on secrets detection** — L5 (Config Matrix) and L8 (Security Surface) both grep for credentials. L5 via config files, L8 via codebase-wide scan. L5's "PLAINTEXT SECRET ALERTS" effectively re-does L8's work. | L5_PROMPT + L8_PROMPT | LOW |
| 6 | **Fallback glob calls in Phase 0.1 are sequential** — 4 independent `glob()` calls listed sequentially. Could be batched. | Phase 0.1 | LOW |

---

### R4: Cost Efficiency — 62/100

| Check | Status |
|---|---|
| Lane-tier routing | ✅ Correct: budget for L1/L4/L5/L7/L10, pro for L2/L3/L6/L8/L9 |
| Critical override (L8+reviewers always pro) | ✅ Enforced |
| Intent-based savings | ✅ Reduces lane count for non-Feature intents |

**Issues:**

| # | Finding | Severity |
|---|---|---|
| 1 | **Pricing 2-3× understated** — Skill says flash=$0.07/1M, pro=$0.14/1M. Actual DeepSeek API cache-miss pricing: flash=$0.14/1M (2× under), pro=$0.435/1M (3.1× under). Every cost estimate is wrong. | **CRITICAL** |
| 2 | **Context window 8× understated** — Skill assumes 128K. Actual DeepSeek v4 window: 1M tokens. The 115K effective budget and "split into sequential plans" rule are built on wrong numbers. | **HIGH** |
| 3 | **Token estimates too low** — Phase 1 M-scale claimed at ~50K. With 10 lanes × 15 max_steps × ~600 tokens/step, realistic is ~90K for Phase 1 alone. Total M-scale: ~130K (vs claimed ~88K). Still fits in 1M window — plan-split rule never fires in practice. | MED |
| 4 | **Emergency pro-tier waste** — L1 (glob/ls), L4 (file patterns), L5 (config glob) forced to pro tier. Pro offers zero advantage for I/O-bound mechanical tasks. ~15K tokens overpriced at 3.1×. | LOW |
| 5 | **Model names verified valid** — `deepseek-v4-flash` and `deepseek-v4-pro` confirmed on api-docs.deepseek.com. Old names `deepseek-chat`/`deepseek-reasoner` being deprecated 2026-07-24. Project copy names are ahead of the curve. ✅ | — |
| 6 | **Consolidation opportunity** — Merge L4 (Test Topography) + L5 (Config Matrix): both are glob-heavy discovery with complementary scope. Estimated savings: ~4K tokens. | LOW |

**Token Estimate (Typical M-Scale Feature Invocation, Corrected Pricing):**

| Phase | Est. Tokens | Tier Mix | Est. Cost @ Actual Pricing |
|---|---|---|---|
| Phase 0 (pre-flight) | ~4.5K | budget | ~$0.0006 |
| Phase 1 (10 lanes) | ~90K | 5 budget + 5 pro | ~$0.0063 + ~$0.0196 = ~$0.026 |
| Phase 2 (cross-check) | ~5K | budget | ~$0.0007 |
| Phase 3 (design) | ~10K | pro | ~$0.0044 |
| Phase 4 (3 reviewers) | ~15K | all pro | ~$0.0065 |
| Phase 5 (synthesize) | ~5K | pro | ~$0.0022 |
| **Total** | **~130K** | — | **~$0.040** |

> Previously claimed: ~88K tokens @ ~$0.008. Real: ~130K tokens @ ~$0.040 — **5× cost increase**.

---

### R5: Staleness/Freshness — 55/100

| Check | Finding |
|---|---|
| **Repo copy age** | 5 days (mtime 2026-06-15, today is 2026-06-20) |
| **Git last commit** | 8 days (2026-06-12) — 3-day gap from mtime suggests out-of-band edits |
| **`updated` field accuracy** | ✅ `2026-06-15` matches mtime (FIXED from v4's future-date `2026-06-19`) |
| **Installed copy `updated`** | `2026-06-12` — stale by 8 days, 3 days behind its own mtime (2026-06-14) |
| **Model name: project copy** | ✅ `deepseek-v4-flash` / `deepseek-v4-pro` — verified current on API docs |
| **Model name: installed copy** | ❌ `deepseek-v4-lite` — **DOES NOT EXIST** in DeepSeek API. Will cause API 400 errors. |
| **Pricing** | ❌ Both copies: $0.07/$0.14 — actual is $0.14/$0.435 |
| **Installed copy divergence** | ❌ Missing 17-line Intent-Based Dispatch table; has `quick/deep/ultrabrain` aliases; uses `RETURN:` not `RETURN EXACTLY:`; M-scale=1 reviewer (contradicts Phase 4's 3) |
| **Tool name validity** | ⚠️ `get_symbols` and `find_in_code` in dispatch protocol but missing from repo `allowed-tools` |
| **BKIT taxonomy match** | ✅ Matches current 11-gate standard |
| **TODO/FIXME/HACK markers** | ✅ None found |

**Installed Copy vs Repo Copy — 15-line Delta:**

| Aspect | Repo (`skills/`) | Installed (`~/.reasonix/`) | Winner |
|---|---|---|---|
| Budget model | `deepseek-v4-flash` ✅ | `deepseek-v4-lite` ❌ (doesn't exist) | **Repo** |
| Tier aliases | None | `quick`/`deep`/`ultrabrain` | Installed (unused but harmless) |
| M-scale reviewers | 3 | 1 (contradicts Phase 4) | **Repo** |
| Intent-Based Dispatch table | Present (17 lines) | **MISSING** | **Repo** (critical) |
| Reviewer prompt format | `RETURN EXACTLY:` | `RETURN:` | **Repo** |
| DAG example | Generic OAuth | BlackCow self-referential | Repo (more generalizable) |
| `updated` date | 2026-06-15 | 2026-06-12 | **Repo** |
| Pricing | $0.07/$0.14 | $0.07/$0.14 | **Both wrong** |

---

## Cross-Reference Findings (Phase 1)

### Contradictions Detected

| # | Lanes | Conflict | Resolution | Severity |
|---|---|---|---|---|
| **C1** | R2 vs R3 | R2 claims all 11 gates covered. R3 finds Phase 2 has no dispatch mechanism — cross-checks are inline grep in planner context. Gate verification has no execution mechanism. | Gates are structurally tagged but operationally unverified. R2's 100 score was inflated — corrected to 64. | HIGH |
| **C2** | R3 vs R4 | R3 says `model=pro` is "not enforced" per platform adaptation note. R4 says XL = "all lanes use model=pro." If model param is decorative, XL and M are identical at execution. | Platform adaptation note nullifies XL differentiation. CRITICAL design flaw. | CRITICAL |
| **C3** | R4 vs R5 | R4 verified model names exist on api-docs. R5 claimed they don't exist (said real names are `deepseek-chat`/`deepseek-reasoner`). | **R4 correct, R5 wrong.** `deepseek-v4-flash/pro` are the current canonical names. `deepseek-chat`/`deepseek-reasoner` deprecated 2026-07-24. However, installed copy's `deepseek-v4-lite` genuinely does NOT exist. | HIGH |
| **C4** | R2 vs R5 | R2 gave 100/100 for gate coverage. R5 found only 4/11 gates have numeric thresholds in SUCCESS field. | R2 self-audit gap: 36 points of score inflation. Honest score: ~64. | HIGH |
| **C5** | Phase -1 vs Phase 1 intent tables | Phase -1 routing says Bug Fix skips L9/L10 only. Phase 1 dispatch silently adds L6=❌ and L8=❌. Two tables in same document disagree. | Phase 1 dispatch table should be authoritative (it's more specific). Phase -1 routing table needs alignment. | MED |

### Escalations

| # | Issue | Why Critical | Action |
|---|---|---|---|
| **E1** | **Installed copy uses `deepseek-v4-lite`** | Non-existent model name → API 400 errors on every budget-tier lane invocation. The skill silently breaks at runtime. | Change `deepseek-v4-lite` → `deepseek-v4-flash` in `~/.reasonix/skills/blackcow-plan.md` and run `skills/install.sh`. |
| **E2** | **Installed copy MISSING Intent-Based Dispatch table** | Every non-Feature invocation dispatches all 10 lanes — 30-50% token waste. Bug Fix tasks run Security + Performance lanes needlessly. | Sync installed copy from `skills/blackcow-plan.md`. The 17-line table (lines 210-226 of repo copy) is entirely absent. |
| **E3** | **Pricing 2-3× understated in BOTH copies** | All cost estimates and tier-routing decisions use wrong numbers. Pro tier is 3.1× more expensive than assumed. | Update pricing comments to $0.14/1M (flash) and $0.435/1M (pro). |
| **E4** | **Context window 128K→1M gap** | Budget estimation, safety margin, and plan-split trigger all derive from wrong base. Constraints 10 and 15 are mis-parameterized. | Rewrite Context Budget section (lines 146-178) for 1M window. |
| **E5** | **No failure/degraded-mode handling** | Single lane timeout → silent data loss for dependent gates. L8 failure = no S1/S2/S3 data. | Add retry + `[DEGRADED]` protocol. |

---

## Recommendations

### Critical (score < 70)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **C1** | Installed copy uses `deepseek-v4-lite` — non-existent model name, breaks at runtime | `~/.reasonix/skills/blackcow-plan.md`: line 9 | Change `deepseek-v4-lite` → `deepseek-v4-flash`. Sync from project copy. | **TRIVIAL** |
| **C2** | Pricing 2-3× understated in both copies ($0.07/$0.14 vs actual $0.14/$0.435) | `skills/blackcow-plan.md`: lines 148-149 | Update to actual DeepSeek API pricing: flash=$0.14/1M, pro=$0.435/1M (cache-miss). | **TRIVIAL** |
| **C3** | Context window is 1M not 128K — budget estimation, safety margin, plan-split trigger all wrong | `skills/blackcow-plan.md`: lines 146-178 | Rewrite Context Budget section: `total_context = 1_000_000`, recalculate effective budget ~900K, adjust plan-split threshold, update per-phase estimates. | **MED** |
| **C4** | XL = M in execution — `model=pro` is decorative per platform adaptation note | `skills/blackcow-plan.md`: line 185 + XL section | Either: (a) make model tier enforceable, or (b) add 2+ speculative lanes (L11-L12) for true XL differentiation. | **MED** |
| **C5** | No subagent failure/retry/degraded-mode handling — single lane timeout = silent gate data loss | Entire Phase 1 | Add: "If lane returns empty/errors → retry once with pro. If still fails → flag `[DEGRADED:<lane>]`, skip dependent gates." | **MED** |

### High (score 70-84)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **H1** | Installed copy MISSING Intent-Based Dispatch table (17 lines) — all intents dispatch all 10 lanes | `~/.reasonix/skills/blackcow-plan.md`: between M and XL dispatch blocks | Copy the 17-line `### Intent-Based Dispatch Adjustment` table from project copy. Run `skills/install.sh`. | **LOW** |
| **H2** | `allowed-tools` missing `get_symbols, find_in_code` — tools dispatched to lane subagents but not whitelisted | `skills/blackcow-plan.md`: line 13 | Add `get_symbols, find_in_code` to frontmatter `allowed-tools`. | **TRIVIAL** |
| **H3** | Phase 2 falsely labeled "parallel batch" — 6 sequential grep operations with no subagent dispatch | `skills/blackcow-plan.md`: lines 428-436 | Either: (a) replace with 2-3 parallel `explore()` subagents, or (b) relabel as "Sequential Cross-Check". | **LOW** |
| **H4** | Context Anchor SUCCESS field incomplete — only 4/11 gates have numeric thresholds | `skills/blackcow-plan.md`: lines 452-456 | Merge Risk Register thresholds into SUCCESS field. Add: regression=0, dead_code=0, dataFlow_integrity≥85%, all_entry_points_protected, all_inputs_validated, no_N+1, bounded_collections. | **LOW** |
| **H5** | Intent table: Bug Fix should keep L6 (Dependency Audit) — bugs often originate from dependency changes | `skills/blackcow-plan.md`: line 213 (dispatch table, Bug Fix row) | Change L6 from ❌ to ✅ (budget tier). Remove L8 skip from dispatch table (not in routing table). | **LOW** |
| **H6** | Intent table: Security should keep L9 (Performance, budget tier) — DoS is a security concern | `skills/blackcow-plan.md`: line 219 (dispatch table, Security row) | Change L9 from ❌ to ✅ (budget tier). | **LOW** |

### Medium (score 85-94)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **M1** | 14+ bare code fences without language markers | L1-L10 prompts, dispatch blocks, Waves example | Add ` ```text ` or ` ```yaml ` markers. | **LOW** |
| **M2** | Phase -1 routing table and Phase 1 dispatch table disagree on Bug Fix/Performance lane skips | Phase -1 Intent Routing vs Phase 1 Intent-Based Dispatch | Align Phase -1 routing text with Phase 1 dispatch table (dispatch table is more specific, treat as authoritative). | **LOW** |
| **M3** | S2/S3 thresholds are qualitative ("모든 진입점 보호") — Constraint 13 says thresholds must be numeric | Risk Register | Either: (a) make numeric (e.g., "auth coverage=100%"), or (b) update Constraint 13 to allow boolean pass/fail for binary security gates. | **LOW** |
| **M4** | Installed copy has `quick/deep/ultrabrain` tier aliases unused in routing logic | `~/.reasonix/skills/blackcow-plan.md`: lines 11-13 | Either add routing logic for these aliases or remove them. Keep or discard — but be consistent between copies. | **LOW** |
| **M5** | DAG example in installed copy uses BlackCow self-referential tasks — less generalizable | `~/.reasonix/skills/blackcow-plan.md`: DAG section | Adopt project copy's generic OAuth example for broader applicability. | **LOW** |

### Low (score 95+)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **L1** | L5↔L8 overlap on secret/credential detection | L5_PROMPT + L8_PROMPT | Scope L5 to config-file-only secret detection. Remove "PLAINTEXT SECRET ALERTS" from L5 or limit to env-file patterns. | **TRIVIAL** |
| **L2** | Phase 0.1 fallback glob calls could be batched | Phase 0.1 | Run 4 independent glob calls in parallel rather than sequentially. | **TRIVIAL** |
| **L3** | Installed copy reviewer prompt format: `RETURN:` vs project copy's `RETURN EXACTLY:` | `~/.reasonix/skills/blackcow-plan.md`: reviewer sections | Sync to `RETURN EXACTLY:` for consistency with lane prompts. | **TRIVIAL** |

---

## Evolution Readiness

- **Safe to auto-evolve?**: **NO** — requires manual review
  - C3 (context window rewrite) and C4 (XL differentiation redesign) are architectural changes
  - E1 (installed copy model name) is runtime-breaking — needs immediate fix before any evolution
  - H4 (SUCCESS field expansion) requires deciding which thresholds to surface
- **Backup recommended before**: Frontmatter (lines 1-13), Context Budget section (lines 146-178), Intent-Based Dispatch table (lines 210-226), Phase 1 dispatch protocol
- **Estimated evolution tokens**: ~18K (pricing fix + context window rewrite + SUCCESS field expansion + intent table alignment + failure handling)
- **Quick wins (safe for immediate fix)**: C1 (model name), C2 (pricing), H2 (allowed-tools), H3 (Phase 2 label)

---

## Improvements Since Last Review (v4)

| v4 Finding | Status | Evidence |
|---|---|---|
| `updated: 2026-06-19` (4 days future) | ✅ **FIXED** | Now `2026-06-15` — matches mtime |
| Reviewer prompts `RETURN:` vs `RETURN EXACTLY:` | ✅ **FIXED** | All 5 RVA-RVE now use `RETURN EXACTLY:` |
| Installed copy missing Intent-Based Dispatch table | ❌ **STILL BROKEN** | Installed copy still at 830 lines, table absent |
| Model names unverified | ✅ **VERIFIED** | `deepseek-v4-flash/pro` confirmed on api-docs.deepseek.com |
| M-scale reviewer count contradiction | ✅ **FIXED** in repo copy | Repo scale table and Phase 4 both say 3 reviewers |
| Installed copy `deepseek-v4-lite` | ❌ **NEW CRITICAL** | Not caught in v4 — doesn't exist in API |

---

## Installed Copy Emergency Fix

The installed copy at `~/.reasonix/skills/blackcow-plan.md` has **two runtime-breaking issues**:

1. **`deepseek-v4-lite` is not a real model name** — any budget-tier lane will get API 400
2. **Missing Intent-Based Dispatch table** — all non-Feature invocations waste 30-50% tokens

**Immediate fix:**
```bash
cp skills/blackcow-plan.md ~/.reasonix/skills/blackcow-plan.md
```
Then update pricing comments and context window numbers in the synced copy.
