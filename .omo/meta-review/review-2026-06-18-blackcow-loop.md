# Meta-Review: blackcow-loop

| Field | Value |
|---|---|
| **Reviewed** | 2026-06-18T22:00:00Z |
| **Reviewer** | blackcow-skill-review (Metis 大将) |
| **Skill Version** | 2.0.0 (mtime: 2026-06-14T23:40:41Z) |

## Overall Score

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| R1 Syntax & Structure | 62 | 15% | 9.30 |
| R2 Gate Completeness | 68 | 30% | 20.40 |
| R3 Parallelism Efficiency | 78 | 25% | 19.50 |
| R4 Cost Efficiency | 72 | 15% | 10.80 |
| R5 Staleness/Freshness | 62 | 15% | 9.30 |
| **TOTAL** | — | **100%** | **69.30** |

> **Verdict**: Below the 70-point threshold for "safe to auto-evolve." Manual review recommended before evolution. The skill has strong architectural design (11-gate coverage, phased pipeline, checkpoint resilience) but is undermined by **critical syntax bugs in variable names** that render 3 of 11 gates non-functional.

---

## Dimension Details

### R1: Syntax & Structure — 62/100

**Frontmatter**: `allowed-tools` lists `lsp_definition`, `lsp_hover`, `lsp_references` — these do not exist in the current Reasonix toolset. The correct equivalents are `get_symbols` and `find_in_code` (already in the list). Model tiers (`budget`, `pro`, `quick`, `deep`, `ultrabrain`) are all valid.

**🔴 CRITICAL Findings (6 instances)**:

| # | File:Line | Issue |
|---|---|---|
| 1 | L629 | `prompt=QA_**SP1_PROMPT` — `**` markdown bold markers leaked into code-block variable name |
| 2 | L630 | `prompt=QA_**SP2_PROMPT` — same `**` leak |
| 3 | L641 | `prompt=QA_POC_S1**SP2_PROMPT` — same `**` leak |
| 4 | L662 | Heading `**QA_**SP1_PROMPT — DataFlow Integrity:**` — `**` breaks markdown bold span |
| 5 | L679 | Heading `**QA_**SP2_PROMPT — Auth Gate Audit:**` — same |
| 6 | L798 | Heading `**QA_POC_S1**SP2_PROMPT — DataFlow + Auth Exploit Attempt:**` — same |

**Impact**: These are not cosmetic — they are **dispatch failures**. The `task()` calls reference identifiers that cannot resolve to any defined prompt section. S1 (DataFlow), S2 (Auth), and the PoC exploit step are dead code at runtime. The effective gate count drops from 11 to 8-9.

**🟠 HIGH Findings**:
- L319-320: Stray code fence wraps `**L6_PROMPT — External Research:**` heading, rendering it as literal code text
- L322-332: L6 prompt body is NOT inside a code block (unlike all other lane prompts L1-L5, L7)
- L14: Invalid `lsp_definition`, `lsp_hover`, `lsp_references` in `allowed-tools`
- L153,622,824: Non-Reasonix tool names (`grep`, `ls`, `bash`, `lsp_definition`, `lsp_references`) in `tools` arrays

**🟡 MEDIUM**: 36 of 47 code blocks (77%) have no language markers (bare ```)

### R2: Gate Completeness — 68/100

| Gate | Status | Evidence | Notes |
|---|---|---|---|
| **M1** spec-match | ⚠️ PARTIAL | QA_M1_PROMPT (L710), Self-Critique #1 (L440) | No fallback when invoked without a plan reference. `<plan reference>` placeholder sent literally to subagent. |
| **M2** test-pass | ✅ COVERED | Phase 1.2-1.3 TDD, VERIFY_M2_PROMPT (L531) | 100% pass / ≥80% coverage thresholds |
| **M3** regression | ✅ COVERED | L2 Call Site baseline, VERIFY_M3_PROMPT (L543) | 0 failures threshold |
| **M4** lint-clean | ✅ COVERED | VERIFY_M4_PROMPT (L553), CLEANUP_M4_PROMPT (L853) | 0 warnings threshold |
| **M5** dead-code | ✅ COVERED | QA_M5_PROMPT (L762), CLEANUP_M5_PROMPT (L837), Self-Critique #8 | 0 dead exports threshold |
| **S1** dataFlow | ❌ BROKEN | QA_**SP1_PROMPT (L629, L662) — name has `**` leak | **Dispatch fails** — variable name unresolvable |
| **S2** auth | ❌ BROKEN | QA_**SP2_PROMPT (L630, L679) — name has `**` leak | **Dispatch fails** — variable name unresolvable. Also: output format (`guarded?`/`gap?` booleans) incompatible with threshold format (100% = `<X>/<Y>` ratio) |
| **S3** injection | ✅ COVERED | QA_S3_PROMPT (L628, L646) | 0 injection surfaces threshold |
| **P1** query | ✅ COVERED | QA_P1_PROMPT (L697), Self-Critique #2 | 0 N+1 patterns threshold |
| **P2** memory | ✅ COVERED | QA_P2_PROMPT (L731), Self-Critique #3 | 0 unbounded growth threshold |
| **P3** latency | ⚠️ UNMEASURABLE | QA_P3_PROMPT (L744) | Threshold `p95 < target` — `target` is **never defined** anywhere in the file. Prompt returns qualitative "est. latency impact" — no numeric p95 measurement. |

**Missed Gates**: None structurally (all 11 documented). **Broken Gates**: S1, S2 (dispatch failure due to `**` bug), P3 (unmeasurable threshold), M1 (no plan-fallback). **Effective gate coverage**: 8 of 11 operational (73% → scored 68 for documentation quality).

### R3: Parallelism Efficiency — 78/100

**Strengths**:
- 27 subagent dispatches across 7 phases, all using `run_in_background: true` where applicable
- Phase 0.3: 7 bootstrap lanes + Phase 0.4: 2 speculative lanes — all 9 dispatched in ONE batch ✅
- Phase 2a: 2 PDCA diagnosticians parallel ✅
- Phase 3: 3 verifiers parallel ✅
- Phase 5 Batch 1: 8 QA agents parallel ✅
- Phase 6: 3 cleanup agents parallel ✅
- Batch-and-wait pattern correctly applied in every batch

**Weaknesses**:

| # | Issue | Impact |
|---|---|---|
| 1 | **Phase 1.3 GREEN is entirely serial** due to Hashline 0.5 — each `edit_file` triggers 4-5 sequential bash commands (cat, md5sum, wc, diff). For 30 edits ≈ 150 sequential subprocess calls. | Major serial bottleneck in the implementation phase. Largely missed by initial R3 scoring. |
| 2 | **Phase 3 → Phase 4 serialization** — main agent sits idle during verification instead of running Phase 4 Manual-QA concurrently. | Wastes wall-clock time on every invocation. |
| 3 | L1/L2 duplicate reads — both independently grep the same target files for symbol discovery vs call site inventory. | Token waste (not parallelism issue per se, but efficiency overlap). |

**Lane Count Assessment**: All lane counts match recommended levels — 7 bootstrap + 2 speculative = 9 discovery lanes, 2 PDCA, 3 verification, 8 QA + 2 PoC, 3 cleanup. Cache-skippable L2/L4/L7 correctly documented for librarian integration.

### R4: Cost Efficiency — 72/100

**Model-Tier Routing**: Excellent. 22 of 32 subagent dispatches use `budget` tier. Only genuinely analytical lanes (security S1/S2/S3, PDCA D1/D2, PoC engineers) use `pro`. One minor over-assignment: L6 (External Research — mechanical version/CVE lookups) could be `budget` instead of `pro`.

**Token Estimate (FULL mode, 0 PDCA cycles)**:

| Phase | Lanes | Est. Tokens | Tier | Est. Cost |
|---|---|---|---|---|
| 0.3 Bootstrap (7 lanes) | mixed | 21K | mixed | ~$0.00210 |
| 0.4 Speculative (2 lanes) | budget | 6K | budget | ~$0.00042 |
| 1 TDD | inline | 8K | pro | ~$0.00112 |
| 3 Verification (3 lanes) | budget | 6K | budget | ~$0.00042 |
| 4 Manual-QA | inline | 2K | pro | ~$0.00028 |
| 5 Batch 1 QA (8 lanes) | mixed | 24K | mixed | ~$0.00231 |
| 5 Batch 2 PoC (2 lanes) | pro | 8K | pro | ~$0.00112 |
| 6 Cleanup (3 lanes) | budget | 6K | budget | ~$0.00042 |
| 7-9 Commit+Report | inline | 4K | pro | ~$0.00056 |
| **Subtotal (productive)** | **32 agents** | **85K** | — | **~$0.00875** |
| **+ Hidden waste** | | | | |
| Hashline bash overhead (~30 edits) | inline | ~18K | pro | ~$0.00252 |
| Bootstrap duplicate reads (L1↔L2↔L7) | n/a | ~10K | mixed | ~$0.00070 |
| Checkpoint context churn (9 writes) | inline | ~8K | pro | ~$0.00112 |
| **TOTAL (FULL, typical)** | | **~121K** | | **~$0.013** |

**Worst case (7 PDCA cycles)**: ~163K tokens, ~$0.019.

**Consolidation Opportunities**: L4+L5 (Test Blueprint + Tooling Cheatsheet) could merge → saves ~2K tokens. Phase 6 Cleanup (3 agents) could be single agent → saves ~3K tokens. Savings negligible at DeepSeek pricing (<$0.001 per run); significant at GPT-4 pricing (~$0.12).

### R5: Staleness — 62/100

**Age**: 4 days (2026-06-14 → 2026-06-18). Chronologically fresh.

**Critical Platform Gaps**:

| Reference | Expected | Actual | Severity |
|---|---|---|---|
| `task()` function (20+ call sites) | `explore` (platform subagent tool) | `task(description=..., run_in_background=true, max_steps=N, model=...)` | CRITICAL |
| `lsp_definition`, `lsp_hover`, `lsp_references` | Not available in current toolset | Listed in `allowed-tools` and `tools` arrays | CRITICAL |
| `deepseek-v4-lite` model | `deepseek-v4-flash` | Used as `budget`/`quick` tier | HIGH |
| `grep`, `ls`, `bash` in tools arrays | `search_content`, `list_directory`, `run_command` | Used in 3 lane protocol sections | HIGH |
| `md5sum` in Hashline bash | `md5` on macOS | Used at L368 | MED |

**install.sh Gap**: The cross-platform note says "run `skills/install.sh` to auto-convert" — but `install.sh` only patches the `allowed-tools` frontmatter line. It does NOT fix inline `task()` calls, `grep`/`ls`/`bash` references, `md5sum` platform differences, or the `**` variable name bug.

---

## Recommendations

### Critical (score < 70) — MUST FIX before use

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| C1 | S1 DataFlow gate dispatch broken — `QA_**SP1_PROMPT` unresolvable | L629, L662 | Rename to `QA_S1_PROMPT` (remove `**` and `P`) | Trivial |
| C2 | S2 Auth gate dispatch broken — `QA_**SP2_PROMPT` unresolvable | L630, L679 | Rename to `QA_S2_PROMPT` (remove `**` and `P`) | Trivial |
| C3 | PoC S1S2 exploit dispatch broken — `QA_POC_S1**SP2_PROMPT` | L641, L798 | Rename to `QA_POC_S1_S2_PROMPT` (remove `**`) | Trivial |
| C4 | `task()` not a valid platform tool — 20+ call sites across all phases | L180-186, 486-489, 522-525, 617-645, 695-700, 820-850 | Replace with platform-native subagent dispatch (`explore`). Note: `run_in_background`, `max_steps`, `model` params may not be available — adapt. | Large |
| C5 | `lsp_definition`, `lsp_hover`, `lsp_references` in allowed-tools and tools arrays | L14, L153, L622, L824 | Remove from frontmatter; replace in tools arrays with `get_symbols`, `find_in_code` | Small |

### High (score 70-84)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| H1 | P3 latency threshold undefined — `p95 < target` but `target` never set | L948, L744-760 | Define default target (e.g., `500ms`) or mechanism to derive from plan. Add numeric return field to QA_P3_PROMPT. | Small |
| H2 | S2 threshold format mismatch — dashboard expects `100% = <X>/<Y>`, prompt returns booleans | L679-695, L947 | Change QA_S2_PROMPT to return `guarded: <N>/<M>` ratio. | Small |
| H3 | M1 spec-match has no fallback when no plan exists — sends literal `<plan reference>` | L720-723 | Add conditional: `if plan → QA_M1; else → skip M1 with note "no plan — spec-match deferred"` | Small |
| H4 | L6 prompt body not in code block; stray code fence around L6 heading | L317-336 | Move L6 prompt into code block like L1-L5/L7 | Trivial |
| H5 | `deepseek-v4-lite` model name — may be stale | L9, L11, L27 | Verify against current model availability; update to `deepseek-v4-flash` if needed | Small |
| H6 | `grep`/`ls`/`bash` in tools arrays — not Reasonix-native | L153, L622, L824 | Replace with `search_content`/`list_directory`/`run_command` in tools lists | Small |
| H7 | Phase 4 HTTP channel assumes running server — no startup, no fallback | L581-587 | Add server detection; skip HTTP channel with note if server not available | Small |

### Medium (score 85-94)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| M1 | 36 of 47 code blocks lack language markers | Throughout | Add language annotations (`bash`, `json`, `markdown`) | Small |
| M2 | `md5sum` is Linux-only; fails on macOS | L368-380 | Use `md5 -r` on macOS, or detect platform with `uname` | Small |
| M3 | Phase 3→Phase 4 serialization — main agent idle during verification | L527-537 | Run Phase 4 manual checks concurrently with Phase 3 subagents | Medium |
| M4 | L1↔L2 duplicate symbol reads — same grep work | L190, L226 | Accept as parallelism trade-off; or have L2 consume L1 output (adds serialization) | N/A (design choice) |

### Low (score 95+)

| # | Finding | File:Line | Fix | Effort |
|---|---|---|---|---|
| L1 | L6 External Research over-tiered (pro when budget suffices) | L292-310 | Change to `model=budget` | Trivial |
| L2 | Consolidation candidates: L4+L5, Phase 6 3→1 agent | L240-310, L820-870 | Merge if moving to expensive model; skip at DeepSeek pricing | Medium |
| L3 | Cross-platform note overpromises install.sh coverage | L19 | Clarify: "install.sh patches allowed-tools only; manual conversion needed for inline tool names and dispatch syntax" | Trivial |

---

## Evolution Readiness

- **Safe to auto-evolve?**: **NO** — requires manual review for Critical findings C1-C5.
- **Blocking defects**: 3 broken gate dispatches (S1, S2, PoC), `task()` platform incompatibility, phantom `lsp_*` tools.
- **Backup recommended before**: All `task()` call sites (20+ locations), Phase 5 QA dispatch blocks (L617-645), Hashline shell commands (L360-400).
- **Estimated evolution tokens**: ~25K (C1-C5 fixes + H1-H7 adjustments + M1-M3 polish).
- **Post-evolution re-review**: Recommended after Critical fixes applied. Blocking defects are trivially fixable (C1-C3: remove `**` characters) but C4 (`task()` migration) is a structural rewrite.
