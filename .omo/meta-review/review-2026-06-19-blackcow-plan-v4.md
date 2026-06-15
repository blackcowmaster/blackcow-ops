# Meta-Review: blackcow-plan

| Field | Value |
|---|---|
| **Reviewed** | 2026-06-20T01:00:00Z |
| **Reviewer** | blackcow-skill-review (Metis 大将) |
| **Skill Version** | 2.0.0 (project copy: `updated: 2026-06-19`, file mtime: 2026-06-15) |
| **Installed Copy** | 2.0.0 (`updated: 2026-06-12`, file mtime: 2026-06-14) |
| **Last Git Commit** | `9872e3f` — "fix: Fable round 2 leftovers… fix updated dates" |

---

## Overall Score

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| R1 Syntax & Structure | 78 | 15% | 11.70 |
| R2 Gate Completeness | 85 | 30% | 25.50 |
| R3 Parallelism Efficiency | 70 | 25% | 17.50 |
| R4 Cost Efficiency | 68 | 15% | 10.20 |
| R5 Staleness/Freshness | 58 | 15% | 8.70 |
| **TOTAL** | — | **100%** | **73.60** |

---

## Dimension Details

### R1: Syntax & Structure — 78/100

| Check | Status | Evidence |
|---|---|---|
| YAML frontmatter valid | ✅ PASS | `name`, `description`, `runAs`, `model`, `allowed-tools` all present |
| Markdown structure | ✅ PASS | Phase headers clear (-1 through 5), consistent `##` → `###` → `####` hierarchy |
| Code blocks language-tagged | ✅ PASS | All fenced blocks have `yaml`, `markdown`, `typescript`, or `` markers |
| `task()` dispatch syntax | ✅ PASS | All use `task(description=..., prompt=..., run_in_background=true, max_steps=..., model=...)` |
| Lane prompt structure | ✅ PASS | 10 lanes all follow: description → action bullets → RETURN EXACTLY → output schema |
| Reviewer prompt structure | ⚠️ DRIFT | Project copy uses `RETURN EXACTLY:` for A/B/C/D/E; installed copy uses bare `RETURN:` for reviewers — inconsistency with lane prompts |
| Broken references | ✅ PASS | No references to non-existent skills or files |

**FRONTMATTER ISSUES:**

| # | Issue | Severity |
|---|---|---|
| 1 | `updated: 2026-06-19` is **4 days in the future** relative to file mtime (2026-06-15) — metadata integrity violation. Git commit `9872e3f` says "fix updated dates" but the fix overshot. | HIGH |
| 2 | `allowed-tools` in project copy lists `read_file, search_content, search_files, glob, list_directory, directory_tree, run_command, web_fetch, web_search, write_file, explore, research, run_skill, get_file_info` — **missing `get_symbols` and `find_in_code`** which are referenced in the lane dispatch protocol (Phase 1: "Every lane subagent uses: tools: `["read_file","search_content","search_files","glob","list_directory","directory_tree","run_command","web_fetch","get_symbols","find_in_code"]`"). The skill's own dispatch instructions reference tools not in its allowed-tools. | HIGH |
| 3 | Installed copy has `model_tiers` with `quick`, `deep`, `ultrabrain` aliases not present in project copy — version drift between copies. | MED |
| 4 | Description string differs: project says `(budget|pro)`, installed says `(budget|pro|quick|deep|ultrabrain)`. The extra tiers are not used anywhere in either copy's routing logic. | LOW |

---

### R2: Gate Completeness — 85/100

**Assessment:** As a PLANNER skill, `blackcow-plan`'s job is to produce a plan that ensures downstream executors can check all BKIT gates. The plan TEMPLATE covers all 11 gates — but coverage is structural (risk register rows + gate tags on tasks), not enforced.

**Gate Coverage Matrix:**

| Gate | Covered? | Evidence | Notes |
|---|---|---|---|
| **M1** spec-match | ✅ | Context Anchor `matchRate ≥ 90%`, Gap Matrix M1 tag, RVA reviewer | Strong |
| **M2** test-pass | ✅ | Context Anchor `test pass=100%, coverage ≥ 80%`, L4 lane, RVA reviewer | Strong |
| **M3** regression | ✅ | Gap Matrix M3 tag, risk register, RVA reviewer | Strong |
| **M4** lint-clean | ✅ | Context Anchor `lint=0warn`, risk register | Threshold set |
| **M5** dead-code | ✅ | Gap Matrix 🗑️ category, risk register, RVA reviewer | Threshold set |
| **S1** dataFlow | ✅ | L3 lane (data shape inventory), risk register, RVB reviewer | Strong |
| **S2** auth | ✅ | L8 lane (security surface), risk register, RVB reviewer | Strong |
| **S3** injection | ✅ | L8 lane, risk register, RVB reviewer | Strong |
| **P1** query | ✅ | L9 lane, risk register, RVC reviewer | Strong |
| **P2** memory | ✅ | L9 lane, risk register | Threshold absent (no memory bound number) |
| **P3** latency | ✅ | Context Anchor `p95_target_ms`, L9 lane, risk register | Strong |

**Gaps & Concerns:**

| # | Finding | Severity |
|---|---|---|
| 1 | **Intent-Based Dispatch Table has routing bugs** (project copy only — installed copy entirely MISSING this table): | HIGH |
| | (a) Bug Fix skips L6 (Dependency Audit) but keeps L7 (Git Archaeology). A bug could originate in a dependency — skipping the audit is risky. | |
| | (b) Performance skips L6 (Dependency Audit). Version upgrades often affect performance — this skip is questionable. | |
| | (c) Emergency dispatches 5 lanes ALL at pro tier (`✅p`). L1 (Surface Topology) and L4 (Test Topography) are mechanical — budget tier is sufficient even for emergencies. | |
| | (d) Security forces XL with 5 reviewers but skips L9 (Performance) and L10 (Patterns). Performance degradation can be a security vector (DoS). | |
| 2 | **Gate coverage is template-only, not enforceable.** The plan tags tasks with gate labels, but `blackcow-loop` (the executor) decides whether to actually run those gate checks. There's no contract or assertion between planner and executor. | MED |
| 3 | **P2 (memory) has no numeric threshold in the plan template.** The risk register says `P2_memory` with threshold "No unbounded growth" — this is qualitative, not quantitative. | LOW |

---

### R3: Parallelism Efficiency — 70/100

| Check | Status | Evidence |
|---|---|---|
| All lanes use `run_in_background=true` | ✅ PASS | Phase 1: all 5/10 lanes dispatched with `run_in_background=true` |
| Batch-and-wait pattern correct | ✅ PASS | "Batch fire all lanes at once, then wait for all to return before Phase 2" |
| Phase 2 cross-checks parallel | ✅ PASS | 6 cross-check items "in ONE parallel batch" |
| Phase 4 reviewers parallel | ✅ PASS | 3-5 reviewers dispatched simultaneously |
| Intent-based lane skipping | ✅ PASS | Reduces dispatch count for Bug/Perf/Security/Emergency intents |
| Lane independence | ✅ PASS | L1-L10 are all independent reads of different aspects |

**Serialization & Contradiction Issues:**

| # | Finding | File:Line | Severity |
|---|---|---|---|
| 1 | **Phase 0 (Pre-flight) is a serial bottleneck before Phase 1.** Cache load + legacy discovery + scale classification all run sequentially before any parallel dispatch. Could cache load be parallelized with the git glob? | Phase 0 section | MED |
| 2 | **XL dispatches identical 10 lanes as M — no additional parallelism.** XL differentiation is only: (a) all lanes use `model=pro`, (b) 5 reviewers instead of 3. True adaptive scaling would add lanes (e.g., L11-L15 speculative lanes) for XL tasks. | Phase 1 "XL (10 lanes)" | MED |
| 3 | **Reviewer count contradiction across copies:** Project copy scale table says "3 reviewers" for M class; installed copy says "1 reviewer" for M class. Both copies' Phase 4 section says "M tasks use 3, XL tasks use 5." The installed copy self-contradicts. | Scale table vs Phase 4 header | HIGH |
| 4 | **No failure handling for lane timeouts.** If L8 (Security Surface, pro tier) times out, the plan proceeds without security data. No retry, no degraded-mode flag, no fallback. | Entire Phase 1 | HIGH |
| 5 | **Installed copy MISSES Intent-Based Dispatch Adjustment table entirely** (17 lines). This means the installed copy always dispatches all 10 lanes regardless of intent — a ~30-50% token waste on non-Feature tasks. | Installed copy, between M and XL dispatch blocks | CRITICAL |

---

### R4: Cost Efficiency — 68/100

| Check | Status |
|---|---|
| Model-tier routing correct | ✅ Auto mode: budget for L1/L4/L5/L7/L10, pro for L2/L3/L6/L8/L9 |
| Critical override enforced | ✅ L8 + reviewers always pro |
| Intent-based savings | ✅ Skipping lanes saves tokens (in project copy) |
| Context budget estimation | ⚠️ Estimates are plausible but unvalidated |

**Issues:**

| # | Finding | Severity |
|---|---|---|
| 1 | **Model names unverified and inconsistent.** Project uses `deepseek-v4-flash`; installed uses `deepseek-v4-lite`. Neither matches DeepSeek's actual model lineup (`deepseek-chat`, `deepseek-reasoner`). Pricing `$0.07/$0.14 per 1M` is not cross-referenced with current API pricing. | MED |
| 2 | **Emergency intent wastes tokens:** All 5 lanes forced to pro tier (`✅p`). L1 (Surface Topology — basic glob/read) and L4 (Test Topography — file pattern matching) are mechanical tasks that budget tier handles adequately even for emergencies. Estimated waste: ~8K tokens. | MED |
| 3 | **Installed copy has `quick`/`deep`/`ultrabrain` tier aliases** in frontmatter that are never referenced in the skill body's routing logic. Dead configuration. | LOW |
| 4 | **Token estimates unvalidated.** Phase 1 M-scale estimated at ~50K. With 10 lanes × 15 max_steps each at ~5K tokens/lane, actual could reach 80K+. No empirical validation cited. | LOW |
| 5 | **Installed copy dispatches all 10 lanes for every intent** (missing Intent-Based table) — this wastes ~15-25K tokens per non-Feature invocation. At ~$0.005/invocation, the waste is minor in dollars but compounds across many invocations. | MED |

**Token Estimate (Typical M-Scale Feature Invocation, Project Copy):**

| Phase | Lanes | Est. Tokens | Tier Mix |
|---|---|---|---|
| Phase 0 (pre-flight) | — | ~3K | budget |
| Phase 1 (10 lanes) | 10 | ~50K | 5 budget + 5 pro |
| Phase 2 (cross-check) | — | ~5K | budget |
| Phase 3 (design) | — | ~10K | pro |
| Phase 4 (3 reviewers) | 3 | ~15K | all pro |
| Phase 5 (synthesize) | — | ~5K | pro |
| **Total** | — | **~88K** | — |
| **Est. cost** | — | ~$0.008 | (budget: ~30K × $0.07 + pro: ~58K × $0.14) |

---

### R5: Staleness — 58/100

| Check | Finding |
|---|---|
| **Project copy age** | 4 days (mtime 2026-06-15) — relatively fresh |
| **Installed copy age** | 5 days (mtime 2026-06-14) |
| **`updated` field accuracy** | ❌ Project says 2026-06-19 (FUTURE — 4 days ahead of mtime). Installed says 2026-06-12 (2 days behind its mtime). |
| **Version drift** | ⚠️ 15-line difference (845 vs 830). Installed copy MISSES Intent-Based Dispatch Adjustment table. |
| **Model name currency** | ⚠️ `deepseek-v4-flash` / `deepseek-v4-lite` — not verified against current DeepSeek API model names |
| **Tool name validity** | ⚠️ `get_symbols` and `find_in_code` referenced in lane dispatch but NOT in project copy's `allowed-tools` |
| **BKIT taxonomy match** | ✅ Matches current 11-gate standard (M1-M5, S1-S3, P1-P3) |
| **TODO/FIXME/HACK markers** | ✅ None found |
| **Skill references** | ✅ All referenced skills (blackcow-loop, blackcow-librarian, etc.) exist |

**Staleness Severity Ranking:**

| # | Issue | Severity |
|---|---|---|
| 1 | **Installed copy out of date — missing Intent-Based Dispatch table (17 lines).** This is a critical feature regression. Any invocation of the installed skill will dispatch all 10 lanes regardless of intent, wasting tokens and missing the intent-specific routing logic. | CRITICAL |
| 2 | **`updated: 2026-06-19` is a future date.** The git commit message says "fix updated dates" but the fix created a forward-dated value. This breaks staleness detection — any automation checking "updated vs now" will think the file is always fresh. | HIGH |
| 3 | **Model name `deepseek-v4-flash` / `deepseek-v4-lite` unverified.** If these don't match the actual API, tier routing silently breaks. | MED |
| 4 | **Installed copy `updated: 2026-06-12` is stale by 2 days relative to its own mtime.** The file was touched but the date wasn't bumped. | LOW |

---

## Cross-Reference Findings (Phase 1)

### Contradictions Detected

| # | Contradiction | Lanes Involved | Resolution |
|---|---|---|---|
| XR1 | **Reviewer count: scale table vs Phase 4.** Installed copy's scale table says "1 reviewer" for M class, but Phase 4 header says "M tasks use 3." The project copy harmonized this to "3 reviewers" in both places. | R2 ↔ R3 | Project copy is correct; installed copy has stale contradiction. |
| XR2 | **`allowed-tools` vs lane dispatch protocol.** Lane dispatch says tools include `get_symbols` and `find_in_code`, but project copy's `allowed-tools` frontmatter omits them. Installed copy includes them. | R1 ↔ R4 | The skill may fail if the runtime enforces `allowed-tools` and a lane tries to call `get_symbols`. |
| XR3 | **Model tier aliases dead code.** Installed copy defines `quick`/`deep`/`ultrabrain` in `model_tiers` but no routing logic in the skill body references them. Project copy removed them. | R4 ↔ R1 | Installed copy has dead config; project copy cleaned it but also lost `get_symbols`/`find_in_code` in allowed-tools. |
| XR4 | **Intent table vs Intent routing.** The project copy's Intent-Based Dispatch table (Phase 1) says Bug Fix skips L6/L8/L9/L10. But the earlier Intent Routing table (Phase -1) says Bug Fix "Skip L9/L10; L2 becomes pro." These two tables partially overlap but don't fully reconcile — the dispatch table adds L6 and L8 skips not mentioned in the routing table. | R2 ↔ R3 | Minor inconsistency. The dispatch table is more specific and should be authoritative. |

### Gate Coverage Self-Audit (R2 auditing itself)

R2's own gate coverage for the TARGET skill (blackcow-plan) was assessed at 85. This is reasonable — the plan template covers all 11 gates structurally, but the gates are advisory tags, not runtime-enforced checks. No self-audit gap detected.

---

## Recommendations

### Critical (score < 70)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| C1 | **Installed copy missing Intent-Based Dispatch table** — dispatches all 10 lanes for every intent, wasting ~30-50% tokens on non-Feature tasks | `~/.reasonix/skills/blackcow-plan.md`: after line 210 | Sync installed copy from project copy. The 17-line Intent-Based Dispatch Adjustment table (lines 209-225 of project copy) is entirely absent. | LOW (copy-paste) |
| C2 | **`updated: 2026-06-19` is 4 days in the future** — breaks staleness detection | `skills/blackcow-plan.md`: line 6 | Set `updated: 2026-06-15` (matches file mtime) or `2026-06-20` (today's actual date). | TRIVIAL |
| C3 | **No subagent failure/retry handling** — if any Phase 1 lane times out, the plan proceeds with partial data, no degraded-mode flag | Entire Phase 1 dispatch section | Add: "If any lane returns empty or error: re-dispatch once with `model=pro`. If still fails: flag `[DEGRADED: <lane>]` in plan header and proceed." | MED |

### High (score 70-84)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| H1 | **`allowed-tools` missing `get_symbols` and `find_in_code`** — lane dispatch protocol references tools not in allowed list | `skills/blackcow-plan.md`: line 13 | Add `get_symbols, find_in_code` to `allowed-tools` frontmatter. | TRIVIAL |
| H2 | **Project ↔ installed copy version drift** — 15-line delta, different model names, different reviewer counts, different DAG examples, different tier aliases | Both files | Reconcile differences. Decide: keep `quick`/`deep`/`ultrabrain` aliases (installed) or remove (project)? Keep generic DAG example (project) or BlackCow-specific (installed)? Sync and bump both to `updated: 2026-06-20`. | MED |
| H3 | **Intent table routing bugs** — Bug Fix skips L6 (Dependency Audit) unnecessarily; Emergency wastes pro tier on L1/L4 mechanical lanes | `skills/blackcow-plan.md`: lines 211-223 | (a) Bug Fix: change L6 from ❌ to ✅ (dependency audit could reveal bug origin). (b) Emergency: change L1/L4 from `✅p` to `✅` (budget tier sufficient). | LOW |
| H4 | **Security intent skips L9/L10** — performance degradation is a DoS vector | `skills/blackcow-plan.md`: line 219 | Change L9 from ❌ to ✅ (budget tier) for Security intent. Performance profiles inform blast-radius assessment. | LOW |

### Medium (score 85-94)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| M1 | **Installed copy uses `RETURN:` not `RETURN EXACTLY:` in reviewer prompts** — inconsistent with lane prompts | `~/.reasonix/skills/blackcow-plan.md`: reviewer sections | Change `RETURN:` to `RETURN EXACTLY:` across all 5 reviewer prompts. | TRIVIAL |
| M2 | **Model names unverified** — `deepseek-v4-flash` / `deepseek-v4-lite` not cross-referenced with DeepSeek API docs | `skills/blackcow-plan.md`: lines 9-10 | Verify against current DeepSeek model lineup. If incorrect, correct. If correct, add a comment with the verification date. | LOW |
| M3 | **P2 (memory) threshold is qualitative** — "No unbounded growth" lacks a numeric target | `skills/blackcow-plan.md`: risk register | Add numeric threshold e.g., "all collections bounded to ≤10K items, pagination ≤100/page." | LOW |
| M4 | **XL scale has no additional parallelism** — same 10 lanes as M, only model tier + reviewer count differ | `skills/blackcow-plan.md`: Phase 1 XL section | Consider adding 1-2 speculative lanes for XL (e.g., L11 Migration Impact, L12 Load Test Plan). Or document explicitly that XL differentiation is depth (pro tier) not breadth. | MED |

### Low (score 95+)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| L1 | **Installed copy DAG example uses BlackCow-specific task names** — less generalizable than project copy's OAuth example | `~/.reasonix/skills/blackcow-plan.md`: DAG section | Adopt project copy's generic example (OAuth middleware). The BlackCow-specific example is confusing when this skill is used for arbitrary projects. | TRIVIAL |
| L2 | **Description string drift** — `(budget\|pro)` vs `(budget\|pro\|quick\|deep\|ultrabrain)` | Both files: line 3 | Standardize description. If tiers are in `model_tiers` they should appear in the description. | TRIVIAL |

---

## Evolution Readiness

- **Safe to auto-evolve?**: **NO** — requires manual review
  - C2 (future date) and C3 (failure handling) need human judgment
  - H2 (version reconciliation between two copies) requires design decision
- **Backup recommended before**: Entire frontmatter block, Intent-Based Dispatch table, Phase 1 dispatch section
- **Estimated evolution tokens**: ~12K (fix dates + sync copies + add retry + fix allowed-tools)

---

## Diff Summary: Project Copy vs Installed Copy

| Aspect | Project (`skills/`) | Installed (`~/.reasonix/skills/`) | Winner |
|---|---|---|---|
| `updated` date | 2026-06-19 (future!) | 2026-06-12 (stale) | Neither — both wrong |
| Budget model name | `deepseek-v4-flash` | `deepseek-v4-lite` | Unverified — both suspect |
| Tier aliases | None | `quick`/`deep`/`ultrabrain` | Installed (but unused) |
| M-scale reviewers | 3 | 1 (contradicts Phase 4) | Project |
| Intent-Based Dispatch table | Present (17 lines) | **MISSING** | Project (critical feature) |
| Reviewer prompt format | `RETURN EXACTLY:` | `RETURN:` | Project |
| DAG example | Generic OAuth | BlackCow self-referential | Project |
| `allowed-tools` | Missing `get_symbols`, `find_in_code` | Includes both | Installed |
| Security intent routing | "All 5 reviewers use pro" | "All reviewers use pro; add Reviewer B+" | Project (clearer) |
| Lines | 845 | 830 | — |
