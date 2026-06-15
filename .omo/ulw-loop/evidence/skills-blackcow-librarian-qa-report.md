# QA Report: skills/blackcow-librarian.md

| Field | Value |
|---|---|
| **Target** | `skills/blackcow-librarian.md` |
| **Evaluated** | 2026-06-20T00:00:00Z |
| **Gates Mode** | `auto` |
| **Gates Dispatched** | M1, M2, M3, M5 (4/11) |
| **Git HEAD** | `3bddf48` (branch: `dev`) |
| **Diff Size** | +3/-1 lines (13 total) — added "First-run guidance" |
| **PDCA Cycles** | 0 (first QA run for this slug) |

---

## 11-Gate Scorecard

| Gate | Score | Weight | Weighted | Status |
|---|---|---|---|---|
| **M1** Spec Match | **100** /100 | 15% | 15.0 | ✅ PASS |
| **M2** Test Pass | **71** /100 | 15% | 10.7 | ⚠️ WARN |
| **M3** Regression | **90** /100 | 10% | 9.0 | ✅ PASS |
| M4 Lint | — | — | — | NOT TRIGGERED (.md file) |
| **M5** Dead Code | **80** /100 | 5% | 4.0 | ⚠️ WARN |
| S1 DataFlow | — | — | — | NOT TRIGGERED |
| S2 Auth | — | — | — | NOT TRIGGERED |
| S3 Injection | — | — | — | NOT TRIGGERED |
| P1 Query | — | — | — | NOT TRIGGERED |
| P2 Memory | — | — | — | NOT TRIGGERED |
| P3 Latency | — | — | — | NOT TRIGGERED |
| **WEIGHTED TOTAL** | | **45%** (eval weight) | **38.7/45** | **86/100** |

> **Scaling note**: Only 4 of 11 gates triggered (universal M1-M3 + M5 from deletion detection). Weighted total scaled to evaluated gates: 38.7/45.0 = **86/100**.

---

## Gate Details

### M1 — Spec Match: 10/10 = 100% ✅

The skill satisfies all 10 BKIT shared conventions:

| # | Convention | Evidence |
|---|---|---|
| 1 | YAML frontmatter (8 fields) | `:1-14` — all present |
| 2 | Cross-platform note | `:17-18` |
| 3 | 大将 persona ("Metis + Explore 大将") | `:19` |
| 4 | Phase-structured body (0→6b) | Full document |
| 5 | Parallel task() dispatch with run_in_background | `:100-112`, `:380-390`, `:434-442` |
| 6 | Model-tier routing (budget/pro) | `:10-12`, `:102-108` |
| 7 | Constraints section (12 items) | `:883-897` |
| 8 | Self-Audit Checklist (11 items) | `:898-911` |
| 9 | Evidence writing to `.omo/ulw-loop/evidence/` | `:264`, `:419`, `:442`, `:502`, `:564`, `:641` |
| 10 | Cost tracking (Cost Budget table) | `:758-766` |

**Missing sections** (vs plan/qa/loop):
- **Anti-Hallucination Guards** — present in plan/qa/loop, absent here despite librarian performing discovery+write operations that risk fabricated cache entries
- Hard Stop Rules — no explicit STOP/ESCALATE conditions

---

### M2 — Test Pass (Structural Integrity): 5/7 = 71% ⚠️

| # | Check | Result |
|---|---|---|
| 1 | YAML frontmatter valid | ✅ PASS |
| 2 | Phase numbers sequential | ✅ PASS |
| 3 | Cross-references resolve | ✅ PASS |
| 4 | 7 commands → implementations | ✅ PASS |
| 5 | Task() model-tier consistency | ❌ **FAIL** — L1/L3 assigned `pro` for mechanical tasks (directory check, git rev-parse). Tier taxonomy says budget=mechanical. |
| 6 | Phase descriptions match dispatch | ❌ **FAIL** — `load-evidence` has no dispatch routing entry; Input section lists only 5 of 7 commands |
| 7 | Constraints internally consistent | ✅ PASS |

**Failure details:**

**F5 (model-tier):** `:77,79` — Phase 1 L1 ("Library State": check if `.omo/library/` exists) and L3 ("Git State": `git rev-parse`) use `model=pro`. Both are mechanical operations. Frontmatter defines `budget` = "mechanical tasks" and `pro` = "analysis, security, design". Should be `budget`.

**F6 (dispatch gap):** `:47-54` — Phase 0 routing block maps only 5 commands: `init-deep→2, scan→3, update→4, check→5, load→6`. Both `load-evidence` and `all` are absent. `:34` — Input section enum: "one of: init-deep, scan, update, check, load" (5, not 7).

---

### M3 — Regression: 1 regression, score 90 ✅

**What changed (HEAD~1 → HEAD):**
- **Added**: "First-run guidance" paragraph — recommends `--command=all` for bootstrap (~$0.002), then `--command=update` for subsequent (~$0.001)
- **Removed**: Nothing (0 content lines deleted)
- All command references in new text are correct (`--command=all`, `--command=update`, `init-deep → scan → check`)

**Regression found:**
| # | Issue | Detail |
|---|---|---|
| 1 | `update` cost contradiction | New text says `~$0.001` but Cost Budget table (`:766`) says `~$0.0005` — **2× discrepancy** |

**Assessment**: Minor cost documentation regression. No structural or functional regressions. The `all` cost (~$0.002) matches the Cost Budget table's "Full init" entry.

---

### M5 — Dead Code Detection: score 80 ⚠️

**Unreferenced entities (3):**

| Entity | Gap |
|---|---|
| `load-evidence` | Missing from Input section (`:34`) and Phase 0 dispatch (`:47-54`) |
| `all` | Missing from Input section (`:34`) |

**Partially implemented (2):**

| Command | Gap |
|---|---|
| `load-evidence` (Phase 6b) | Has implementation but **no evidence-writing section**. Every other phase (2.4, 3.4, 4.5, 5.3, 6.4) writes to `.omo/ulw-loop/evidence/`. |
| `all` | No dedicated section — piggybacks on individual phases. No mention of evidence collection between chained phases. |

**Duplicate content (4):**
- `### 0.0 Cache Load` logic duplicated across Phase 6 Integration Contract (`:629`) and Phase 7 patches for plan (`:693`), loop (`:725`), QA (`:744`). Core staleness-checking decision tree repeated 4×.

**Dead reference (conditional):**
- `.omo/memory/failure-patterns.jsonl` — referenced as input by Governor Integration (`:834`) but doesn't exist on disk yet. Graceful handling needed for first-run.

**Removal assessment**: Nothing is safe to delete outright. All issues are documentation gaps, not useless content.

---

## Test Pyramid Status

**Not generated** — target is a markdown skill file, not executable code. Phase 2 test generation skipped. Structural integrity served as the equivalent of "tests" in M2 evaluation.

---

## Cost Tracking

| Gate | Lanes Dispatched | Est. Tokens | Model Tier | Est. Cost |
|---|---|---|---|---|
| Phase 0 L1 (Test Inventory) | 1 explore | ~4K | budget | ~$0.0003 |
| Phase 0 L2 (Code Structure) | 1 explore | ~5K | budget | ~$0.0004 |
| Phase 0 L3 (Plan Extraction) | 1 explore | ~5K | budget | ~$0.0004 |
| Phase 0 L4 (External Audit) | 1 explore | ~5K | budget | ~$0.0004 |
| Phase 0 L5 (Runtime Probe) | 1 explore | ~5K | budget | ~$0.0004 |
| M1 Spec Match | 1 explore | ~6K | pro | ~$0.0017 |
| M2 Test Pass | 1 explore | ~8K | budget | ~$0.0006 |
| M3 Regression | 1 explore | ~6K | pro | ~$0.0017 |
| M5 Dead Code | 1 explore | ~6K | budget | ~$0.0004 |
| **TOTAL** | **9 lanes** | **~50K** | — | **~$0.0063** |

> Cost model: budget=$0.07/1M input, pro=$0.14/1M input ($0.435/1M output for pro).

---

## Recommendations

### Critical (0)
None.

### High (2)

| # | Gate | Issue | Fix |
|---|---|---|---|
| H1 | M2 | `load-evidence` unreachable via Phase 0 dispatch | Add `--command=load-evidence → Phase 6b` to dispatch block (`:47-54`) and add `load-evidence` + `all` to Input section enum (`:34`) |
| H2 | M5 | `load-evidence` missing evidence section | Add `### 6b.1 load-evidence Evidence` writing `load-evidence-result.txt` to `.omo/ulw-loop/evidence/` |

### Medium (3)

| # | Gate | Issue | Fix |
|---|---|---|---|
| M1 | M2 | L1/L3 assigned `pro` for mechanical tasks | Change Phase 1 L1 and L3 to `model=budget` |
| M2 | M3 | `update` cost ~$0.001 (new text) vs ~$0.0005 (Cost Budget table) | Reconcile to single value |
| M3 | M5 | 4× duplicated cache-load logic across Phase 7 patches | Extract core staleness check into canonical reference, reference from patches |

### Low (2)

| # | Gate | Issue | Fix |
|---|---|---|---|
| L1 | M1 | Missing Anti-Hallucination Guards section | Add guards: "NEVER fabricate cache entries", "NEVER claim scan complete without file reads" |
| L2 | M5 | `failure-patterns.jsonl` referenced as input before creation | Add first-run guard: treat missing file as empty, not error |

---

## Residual Risk

- **Cost estimate accuracy**: The EXECUTED_EVAL "verified" costs (~$0.01/scan) conflict with the table estimates (~14K tokens ≈ $0.0012) by ~8×. The newly added first-run guidance uses the lower estimates — may mislead users about actual costs.
- **Cross-platform tool names**: Phase 3 scan lanes use `grep`/`ls`/`bash` (Windows-native) while frontmatter `allowed-tools` lists Reasonix-native names. `install.sh` handles conversion, but the mismatch could cause runtime failures if install.sh wasn't run.
