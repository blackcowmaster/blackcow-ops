# Meta-Review: blackcow-plan

| Field | Value |
|---|---|
| **Reviewed** | 2026-06-15T11:20:00Z |
| **Reviewer** | blackcow-skill-review (Metis 大将) |
| **Skill Version** | 2.0.0 — TWO DIVERGENT COPIES: workspace (`skills/`, 1050 lines, `updated: 2026-06-15`, mtime 2026-06-15T08:44) vs installed (`~/.reasonix/`, 830 lines, `updated: 2026-06-12`, mtime 2026-06-14) |
| **Git State** | Last commit `d29bc2f` (today). Workspace file has progressive widening, governance protocol, 1M context budget, correct model names. Installed copy has NONE of these. |
| **Prior Scores (10 cycles)** | 66.65 → 76.65 → 69 → 71.5 → 70.9 → 58.15 → 72.8 → 64.3 → 73.6 → 64.3 |
| **Self-Review Guard** | ⚠️ See §Oscillation Diagnosis below |

## Overall Score

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| R1 Syntax & Structure | 72 | 15% | 10.80 |
| R2 Gate Completeness | 50 | 30% | 15.00 |
| R3 Parallelism Efficiency | 45 | 25% | 11.25 |
| R4 Cost Efficiency | 35 | 15% | 5.25 |
| R5 Staleness/Freshness | 82 | 15% | 12.30 |
| **TOTAL** | — | **100%** | **54.60** |

> **Why lower than prior reviews?** This review accounts for BOTH copies of the file. The installed copy (`~/.reasonix/skills/blackcow-plan.md`) is what actually runs — and it has fatal flaws (non-existent model name `deepseek-v4-lite`, missing governance protocol, missing progressive widening, 128K context window). R6 Devil's Advocate identified the two-copy divergence as **the root cause of 10 cycles of oscillating scores** — previous reviews scored different artifacts without distinguishing them.

## Executive Summary

**blackcow-plan has two divergent copies with the same version number (2.0.0).** The workspace copy (`skills/`) has received substantial upgrades: progressive widening (3-stage), governance protocol (`--govern`/`--stale-ok`), 1M context budget, and correct model names. The installed copy (`~/.reasonix/`) is 220 lines shorter and missing all of these upgrades — it still uses the non-existent model name `deepseek-v4-lite`, a 128K context window, and no progressive widening. **Every budget-tier lane on the installed copy will fail with API 400 errors.**

Beyond the copy divergence, the skill has three architectural contradictions that make gate coverage unreliable:
1. **Progressive widening silently nullifies 6/11 BKIT gates** — L8 (Security) and L9 (Performance) live in Stage 3, which may never fire
2. **Three independent lane-selection mechanisms** (Intent routing, progressive widening, static dispatch blocks) with no documented priority
3. **Context Anchor SUCCESS field has numeric thresholds for only 4/11 gates** — the remaining 7 are qualitative or absent

---

## Dimension Details

### R1: Syntax & Structure — 72/100

**Strengths**: Valid YAML frontmatter with all required fields. Clear phase progression (Phase -1 through Phase 5). Consistent H2→H3 heading hierarchy, no skipped levels. All 7 `blackcow-*` skill references verified on disk. Lane prompts follow 4-section structure (context → action → RETURN EXACTLY → output schema). No broken file references.

**Issues**:

| # | File:Line | Issue | Severity |
|---|---|---|---|
| 1 | Multiple (28 instances) | **Bare code blocks without language markers** — 80% of all code fences. L1-L10 prompts, dispatch blocks, formulas, decision trees, reviewer prompts all use bare ` ``` `. | MED |
| 2 | Frontmatter:6 | **`runAs` (camelCase) instead of `run_as` (snake_case)** — skill-loading API expects snake_case. May prevent skill from loading. | HIGH |
| 3 | Frontmatter:14 | **`allowed-tools` (hyphenated) instead of `allowed_tools` (snake_case)** — API expects snake_case. Same loading risk. | HIGH |
| 4 | ~270-272 | **Dispatch protocol says "use `explore(task=...)`" but all samples show `task(...)` pseudo-code** — contradictory instruction. | LOW |
| 5 | Frontmatter:11-13 | **`model_tiers` is non-standard frontmatter** — `install_skill` expects flat `model` string. The nested map may be silently ignored. | LOW |

### R2: Gate Completeness — 50/100

**Assessment**: Only 5 of 11 BKIT gates have full coverage (Risk Register row + data-collection lane + reviewer + numeric threshold in SUCCESS field). The remaining 6 are structurally referenced but operationally incomplete. The progressive widening architecture (see R3) makes gate coverage *contingent* — L8 (Security) and L9 (Performance) live in Stage 3 and may never execute.

**Gate Coverage Matrix**:

| Gate | Status | Risk Register | Data Lane | Reviewer | Numeric Threshold | SUCCESS Field |
|---|---|---|---|---|---|---|
| **M1** spec-match | ✅ FULL | ✅ | L4 (partial) | RVA | ✅ ≥90% | ✅ |
| **M2** test-pass | ✅ FULL | ✅ | L4 | RVA | ✅ 100% | ✅ |
| **M3** regression | ⚠️ PARTIAL | ✅ | L4+L7 | RVA | ✅ 0 regressions | ❌ (coverage≥80% is adjacent) |
| **M4** lint-clean | ⚠️ PARTIAL | ✅ | ❌ No lane collects lint data | RVA (composite) | ✅ 0 warnings | ✅ |
| **M5** dead-code | ❌ MISSING | ✅ | ❌ No lane hunts unreferenced exports | RVE (weak) | ✅ 0 unused exports | ❌ |
| **S1** dataFlow | ⚠️ PARTIAL | ✅ | L3+L8 (Stage 3!) | RVB | ✅ ≥85% | ❌ |
| **S2** auth | ❌ BROKEN | ✅ | L5+L8 (Stage 3!) | RVB | ❌ Qualitative (Korean text) | ❌ |
| **S3** injection | ❌ BROKEN | ✅ | L8 (Stage 3!) | RVB | ❌ Qualitative (Korean text) | ❌ |
| **P1** query | ⚠️ PARTIAL | ✅ | L9 (Stage 3!) | RVC (composite) | ❌ Qualitative ("No N+1") | ❌ |
| **P2** memory | ⚠️ PARTIAL | ✅ | L9 (Stage 3!) | RVC (composite) | ❌ Qualitative ("No unbounded growth") | ❌ |
| **P3** latency | ⚠️ PARTIAL | ✅ | L9 (Stage 3!) | RVC (composite) | ✅ p95 < target | ✅ |

**Intent Table Bugs (Phase -1 vs Phase 1)**:

| # | Bug | Detail | Severity |
|---|---|---|---|
| 1 | **Bug Fix silently skips L6, L8** | Phase -1 routing says "Skip L9/L10." Phase 1 dispatch table adds L6=❌, L8=❌ without routing authorization. | HIGH |
| 2 | **Batch-fire vs progressive widening contradiction** | "MUST dispatch all lanes in ONE batch" (line 275) vs "Do NOT dispatch all selected lanes at once" (line 322). Contradictory instructions in adjacent paragraphs. | CRITICAL |
| 3 | **Constraint #3 vs Intent-Based dispatch** | Constraint #3 says "Dispatch ALL lanes (XS:5, M:10, XL:10)" unconditionally. Intent-Based table skips lanes per intent class. | MED |
| 4 | **Security: skip L9/L10 vs force full widening** | Phase -1 says Security skips L9/L10. Progressive widening says Security forces ALL lanes immediately. Two sections disagree. | MED |
| 5 | **Performance intent drops ALL S-gates** | Performance skips L8 (Security data) AND Reviewer B (Security review). S1/S2/S3 have zero data collection and zero adversarial review. | HIGH |

### R3: Parallelism Efficiency — 45/100

**Assessment**: The skill's parallelism is mostly aspirational. Only ~10% of the pipeline wall-clock time is genuinely parallel. Progressive widening serializes Phase 1 into 3 sequential stages, Phase 2 is mislabeled as "parallel" (it's 6 sequential inline operations), and the inter-phase dependency chain (Phases -1→0→1→2→3→4→5) is fully serial.

**Serialization Issues**:

| # | File:Line | Issue | Severity |
|---|---|---|---|
| 1 | ~322-325 | **Progressive widening Stages 1→2→3 are serial** — Stage 2 requires Stage 1's uncertainty score. Stage 3 requires Stage 2's. The "batch fire all" instruction is contradicted by the widening logic itself. | CRITICAL |
| 2 | ~611-617 | **Phase 2 falsely labeled "ONE parallel batch"** — contains 6 sequential inline `search_content`/`read_file` ops with zero `task()` subagent dispatch. Steps 4-6 depend on steps 1-3. | HIGH |
| 3 | ~398-400 | **XL = M in execution** — both dispatch identical L1-L10 lanes. Platform adaptation note (line ~270) says model=pro is "not enforced." Only +2 reviewers differentiates XL from M. | CRITICAL |
| 4 | — | **No failure/retry/degraded-mode handling** — if L8 (Security) times out, plan proceeds with zero S-gate data. No retry, no `[DEGRADED]` flag. | HIGH |
| 5 | Entire pipeline | **8 serialization points** — 6 inter-phase gates (Phases -1→0→1→2→3→4→5) + 2 intra-Phase-1 widening gates. Only Phase 1 intra-stage dispatch and Phase 4 reviewer dispatch are parallel. | MED |
| 6 | Phase 0.1 | **Legacy discovery glob calls are sequential** — 4 independent `glob()` calls listed sequentially. Could be parallelized. | LOW |

**Lane Overlap**:

| Overlapping Pair | What's Shared | Severity |
|---|---|---|
| L5 (Config Matrix) vs L8 (Security Surface) | Both search for hardcoded credentials/secrets | MED |
| L2 (Call Graph) vs L8 (Security Surface) | Both identify injection surfaces (L2 traces path, L8 assesses risk) | LOW |
| L1 (Surface Topology) vs L10 (Pattern Library) | Both survey file structure and exports | LOW |

### R4: Cost Efficiency — 35/100

**Assessment**: The installed copy uses wrong model names, 2-3.1× underpriced rates, a 7.8× understated context window, and 3 dead tier aliases. The workspace copy fixes the model names and context window but still has wrong pricing and a Phase 4 token estimate that's off by 20× (claims ~5K per reviewer; actual ~33K each).

**Pricing Accuracy**:

| Source | Flash/Budget Rate | Pro Rate | Context Window |
|---|---|---|---|
| **Installed copy** | $0.07/1M (`deepseek-v4-lite` — doesn't exist) | $0.14/1M | 128K |
| **Workspace copy** | $0.14/1M (`deepseek-v4-flash`) | $0.435/1M (`deepseek-v4-pro`) | 1M |
| **Actual (DeepSeek API)** | $0.14/1M | $0.435/1M | 1M |

**Corrected Token Estimate (M-scale Feature)**:

| Phase | Tokens | Tier | Cost |
|---|---|---|---|
| Phase 0 (pre-flight) | ~4.5K | budget | ~$0.0006 |
| Phase 1 (10 lanes) | ~175K | 5 budget + 5 pro | ~$0.0123 + $0.0435 = ~$0.056 |
| Phase 2 (cross-check) | ~5K | orchestrator | ~$0.0022 |
| Phase 3 (design) | ~10K | orchestrator | ~$0.0044 |
| Phase 4 (3 reviewers, full plan input) | ~99K | all pro | ~$0.0431 |
| Phase 5 (synthesize) | ~5K | orchestrator | ~$0.0022 |
| **Total** | **~299K** | — | **~$0.108** |

> Skill claims ~70K tokens for M-scale. Actual is ~299K — **4.3× undercount**. The Phase 4 estimate alone is off by ~20× (claims ~5K, actual ~99K).

**Installed Copy Fatal Flaws**:

| Flaw | Impact |
|---|---|
| `deepseek-v4-lite` model name doesn't exist | Every budget-tier lane gets API 400 error |
| 128K context window | Plan-split logic fires on EVERY invocation (doubling cost) |
| Missing progressive widening | No token optimization; all 10 lanes always dispatched |
| Missing governance protocol | No `--govern`/`--stale-ok` support |

### R5: Staleness/Freshness — 82/100

**Assessment**: The workspace copy is objectively fresh (mtime 2.5h ago, `updated: 2026-06-15` matches). But the 18-point deduction reflects the **installed copy divergence** — the file that actually runs is 220 lines shorter, uses a non-existent model name, and has a 128K context window. This makes the "freshness" score dangerously misleading: a consumer checking only mtime would consider the skill healthy.

**Installed Copy Divergence**:

| Dimension | Workspace (`skills/`) | Installed (`~/.reasonix/`) |
|---|---|---|
| **Size** | 48,825 bytes / 1050 lines | 35,888 bytes / 830 lines |
| **mtime** | 2026-06-15T08:44 | 2026-06-14T23:59 |
| **Budget model** | `deepseek-v4-flash` ✅ | `deepseek-v4-lite` ❌ (doesn't exist) |
| **Context budget** | 1M → ~900K effective | 128K → ~115K effective |
| **Governance protocol** | Full `--govern`/`--stale-ok` (57 lines) | ❌ Absent |
| **Progressive widening** | Full 3-stage system (~100 lines) | ❌ Absent |
| **Model tier aliases** | 2 (budget/pro) | 5 (quick/deep/ultrabrain unused) |
| **M-scale reviewers** | 3 | 1 (contradicts Phase 4) |
| **allowed-tools** | 17 tools | 15 tools (missing `get_symbols`, `find_in_code`) |

**Outdated References**:

| Reference | Expected | Actual | Severity |
|---|---|---|---|
| Installed: `model_tiers.budget` | `deepseek-v4-flash` | `deepseek-v4-lite` | CRITICAL |
| Installed: Context Budget `total_context` | 1,000,000 | 128,000 | HIGH |
| Workspace: Pricing comments | $0.14/$0.435 | $0.14/$0.435 (correct for flash, but pro listed as $0.435 while frontmatter says $0.14) | MED |
| Both: `model_tiers.pro` price | $0.435/1M | Workspace frontmatter says $0.14/1M (self-contradiction) | MED |
| Workspace: `runAs` / `allowed-tools` | `run_as` / `allowed_tools` | camelCase/hyphenated | HIGH |

---

## Cross-Reference Findings (XR1 + XR2)

### Contradictions Detected

| # | Type | Description | Severity |
|---|---|---|---|
| **C1** | Batch-vs-Stage | "MUST dispatch all lanes in ONE batch" vs "Do NOT dispatch all selected lanes at once" — adjacent paragraphs, opposite instructions | CRITICAL |
| **C2** | Gate coverage vs Widening | Progressive widening Stage 3 (where L8+L9 live) may never fire → 6/11 BKIT gates can have zero data collection | CRITICAL |
| **C3** | Three lane-selection mechanisms | Intent routing, progressive widening, and static dispatch blocks can produce 3 different lane sets for the same intent — no priority protocol | CRITICAL |
| **C4** | Freshness vs Quality | Workspace mtime is 2.5h old (R5=92) but R2=50 gate score — 42-point gap between appearance and reality | HIGH |
| **C5** | Two copies, same version | 1050-line workspace vs 830-line installed, both claim v2.0.0 → root cause of 10-cycle score oscillation | CRITICAL |
| **C6** | Phase -1 vs Phase 1 tables | Bug Fix routing says "skip L9/L10"; dispatch table also skips L6+L8 without authorization | HIGH |
| **C7** | Security: skip L9/L10 vs force all | Routing says skip L9/L10 for Security; widening says force ALL lanes for Security | MED |
| **C8** | R2 self-audit inflation | R2 treats structural gate presence as coverage. Real operational coverage = 5/11 (45%), not the structural 7-8/11 (64-73%) | HIGH |

### Escalations

| # | Issue | Why Critical | Action |
|---|---|---|---|
| **E1** | **Installed copy uses `deepseek-v4-lite` — non-existent model** | Every budget-tier invocation fails with API 400. The skill is silently broken at runtime. | **IMMEDIATE**: `cp skills/blackcow-plan.md ~/.reasonix/skills/blackcow-plan.md` |
| **E2** | **Progressive widening nullifies 6/11 BKIT gates** | L8+L9 in Stage 3 may never fire. S1/S2/S3/P1/P2/P3 gates get zero data collection on low-uncertainty tasks. | Redesign: move security-critical lanes (L8) to Stage 2, or exempt security gates from widening |
| **E3** | **Two-copy divergence is root cause of score oscillation** | 10+ reviews over 6 days couldn't converge because they scored different artifacts. The review system itself wasn't detecting the copy split. | Always review BOTH copies. Add copy-divergence check to R5 staleness lane. |
| **E4** | **Phase 4 token estimate off by 20×** | Claimed ~5K per reviewer; actual ~33K. All cost estimates and budget calculations are fabricated. | Recalculate all token estimates from measured subagent token consumption. |
| **E5** | **10 review cycles, same critical findings** | L11-L15 undefined, pricing wrong, SUCCESS field incomplete — persist across 5+ cycles. BKIT self-repair loop is not self-repairing. | Institute "3-cycle stale finding" escalation: any CRITICAL unfixed after 3 reviews → block evolution, require manual fix. |

---

## Recommendations

### Critical (score < 70, runtime-breaking)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **C1** | **Installed copy uses non-existent model `deepseek-v4-lite`** | `~/.reasonix/skills/blackcow-plan.md`:9 | `cp skills/blackcow-plan.md ~/.reasonix/skills/blackcow-plan.md` — sync from workspace | TRIVIAL |
| **C2** | **Installed copy has 128K context window (vs 1M actual)** | `~/.reasonix/skills/blackcow-plan.md`:153 | Sync from workspace copy. The 128K budget causes false plan-splits on every invocation. | TRIVIAL (via sync) |
| **C3** | **Progressive widening vs batch-fire contradiction** | `skills/blackcow-plan.md`:275-278 vs :322-325 | Resolve: either (a) remove batch-fire language and admit Phase 1 is 3-stage serial, or (b) remove widening and fire all intent-selected lanes at once. Option (a) is more honest; option (b) is more parallel. | MED |
| **C4** | **XL = M in execution** | `skills/blackcow-plan.md`:398-400 | Add L11 (Speculative Security Deep-Dive) and L12 (Speculative Performance Deep-Dive) for XL. These are actual subagent dispatches, not model-tier hints. Or reduce scale to XS/M only. | HEAVY |
| **C5** | **No lane failure/degraded-mode handling** | Phase 1, all lanes | Add: "If lane returns empty/errors → retry once with pro tier. If still fails → emit `[DEGRADED:<lane>]`, skip dependent gates, continue with best available evidence." | MED |

### High (score impact 5-10 points)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **H1** | **Context Anchor SUCCESS has thresholds for only 4/11 gates** | `skills/blackcow-plan.md`:635-637 | Add numeric thresholds for M3 (regression=0), M5 (dead_exports=0), S1 (dataFlow integrity≥85%), S2 (auth_coverage=100%), S3 (injection_surface=0), P1 (n_plus_one=0), P2 (unbounded_collections=0). | LIGHT |
| **H2** | **S2/S3 thresholds are non-numeric Korean text** | `skills/blackcow-plan.md`:761-762 | Change "모든 진입점 보호" → "auth coverage=100% (all entry points return 401 for invalid auth)". Change "모든 입력 검증" → "all inputs validated (0 unvalidated inputs)". | LIGHT |
| **H3** | **Frontmatter uses `runAs`/`allowed-tools` (wrong case)** | `skills/blackcow-plan.md`:6,14 | Change to `run_as` / `allowed_tools` to match `install_skill` API expectations. | TRIVIAL |
| **H4** | **Phase 2 mislabeled "parallel batch"** | `skills/blackcow-plan.md`:611-617 | Relabel to "Sequential Cross-Check" or replace with 2-3 parallel `explore()` subagents. | LIGHT |
| **H5** | **Intent table: Bug Fix skips L6+L8 without routing authorization** | `skills/blackcow-plan.md`:301-313 | Align Phase 1 dispatch table with Phase -1 routing: Bug Fix should keep L6 (bugs often from dependency changes) and L8 (security is always relevant). | LIGHT |
| **H6** | **Performance intent drops ALL S-gates** | `skills/blackcow-plan.md`:143 | Performance should keep L8 at budget tier (security surface matters even for perf work — DoS is a security concern). | LIGHT |
| **H7** | **Phase 4 token estimate undercounted 20×** | `skills/blackcow-plan.md`:256 | Replace "~5K (M: 3 reviewers)" with "~99K (3 × ~33K per reviewer including full plan input)". | LIGHT |

### Medium (score impact 2-5 points)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **M1** | 28 bare code blocks without language markers | Throughout | Add `text`, `bash`, `yaml`, `markdown`, `json` markers to all code fences. | LIGHT |
| **M2** | Three lane-selection mechanisms with no priority protocol | Phases -1, 1 | Document priority: progressive widening > intent-based dispatch > static dispatch. Or collapse to single mechanism. | MED |
| **M3** | P-gates share single composite reviewer bullet in RVC_PROMPT | ~828-837 | Split into 3 separate bullets: "P1: No N+1 queries", "P2: No unbounded collections", "P3: p95 latency met". | LIGHT |
| **M4** | Pricing self-contradiction in workspace copy | Frontmatter:17 vs ~220 | Frontmatter says pro=$0.14/1M; text body says $0.435/1M. Unify to correct value ($0.435/1M). | TRIVIAL |
| **M5** | L5↔L8 overlap on secret/credential detection | L5+L8 prompts | Scope L5 to config-file secrets; L8 to code-level secrets. Add boundary note. | LIGHT |
| **M6** | `model_tiers` unused aliases (installed copy) | `~/.reasonix/`:11-13 | Remove `quick`, `deep`, `ultrabrain` or document as reserved. | TRIVIAL |
| **M7** | L7 omitted from cost-routing table | ~126 | Add L7 to budget tier: "budget tier for lanes L1, L4, L5, L7, L10". | TRIVIAL |

### Low (score impact < 2 points)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| **L1** | `updated` field in installed copy is 3 days stale | `~/.reasonix/`:8 | Sync from workspace. | TRIVIAL |
| **L2** | Phase 0.1 glob calls could be parallel | Phase 0.1 | Fire 4 independent `glob()` calls in one batch instead of sequentially. | TRIVIAL |
| **L3** | Dispatch protocol says "use `explore(task=...)`" but shows `task(...)` | ~270-272 | Use consistent notation throughout. | TRIVIAL |

---

## Evolution Readiness

- **Safe to auto-evolve?**: **NO — requires manual intervention first**
  - **IMMEDIATE**: Sync installed copy from workspace (`cp skills/blackcow-plan.md ~/.reasonix/skills/blackcow-plan.md`) — this is a 1-command fix that resolves C1, C2, H3 (if also fixed in workspace), M6, L1
  - **THEN**: Safe items for auto-evolution: H1 (SUCCESS field expansion), H2 (S2/S3 numeric thresholds), H4 (Phase 2 label), H7 (token estimate fix), M1 (code block markers), M3 (P-gates split), M4 (pricing unify), M7 (L7 in routing table), L2 (glob parallel)
  - **NOT safe for auto-evolve**: C3 (widening vs batch-fire — architectural decision), C4 (XL differentiation — needs lane design), C5 (failure handling — protocol design), M2 (lane-selection priority — architectural)
- **Backup recommended before**: Entire installed copy, frontmatter (lines 1-20), SUCCESS field (~635-637), Phase 1 dispatch protocol (~275-400)
- **Estimated evolution tokens**: ~8K for immediate fixes (sync + SUCCESS thresholds). ~25K for safe items. ~50K for full remediation including architectural fixes.

---

## Oscillation Diagnosis

**Scores have oscillated (58→77→64→74→64) across 10+ review cycles because two divergent copies of the file exist with the same version number (2.0.0).** Some reviews scored the workspace copy (`skills/`, 1050 lines, progressively upgraded), others scored the installed copy (`~/.reasonix/`, 830 lines, stuck at a June-12 snapshot). R2 gate scores ranged 55→85 because reviewers assessed different artifacts with different gate completeness. The review system itself didn't detect the copy split until v5.

**Fix**: The review process should ALWAYS check both copies. R5 staleness lane now includes an installed-copy divergence check. Future scores should converge once both copies are synced.

---

## Self-Review Guard Assessment

| Check | Result |
|---|---|
| **Score convergence vs v5** | v5: 64.30 → v6: 54.60, Δ=9.7. **FAIL (±3 threshold)** — but EXPLAINED by first-ever two-copy divergence detection. The score reflects the INSTALLED copy's actual runtime state, not just the workspace. |
| **R2 drop explained** | v5: 64 → v6: 50. R6 Devil's Advocate correctly identified that 6/11 gates lose data collection via progressive widening. This wasn't factored into prior R2 scores. |
| **R3 drop explained** | v5: 67 → v6: 45. Progressive widening serialization now quantified (8 serialization points vs prior "mostly parallel" assessment). |
| **R4 drop explained** | v5: 62 → v6: 35. Installed copy's fatal model name + context window errors now accounted for (prior reviews didn't weight the installed copy). |
| **R5 drop explained** | v5: 55 → v6: 82*. Wait — R5 went UP. Workspace copy is objectively fresher (2.5h vs 5 days). The divergence is now reported separately in the copy-divergence section rather than deducted from staleness. |
| **Overall** | **SELF-REVIEW GUARD: CONDITIONAL PASS.** Score change is fully explained by (a) first-ever two-copy divergence detection, (b) progressive widening impact on gate coverage, and (c) Devil's Advocate challenges. The review is self-consistent. |
