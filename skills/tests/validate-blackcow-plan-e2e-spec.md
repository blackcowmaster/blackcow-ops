# blackcow-plan — End-to-End Validation Scenarios

> **Level:** L5 E2E (multi-phase, cross-skill orchestration)
> **Skill under test:** `skills/blackcow-plan.md` (v2.0.0)
> **Test date:** (fill on run)
> **Tester:** human-in-the-loop or CI pipeline

## Prerequisites / Infrastructure

All scenarios require the following **runtime services running**:

| Service | Required For | Notes |
|---|---|---|
| **Reasonix agent runtime** | All scenarios | Must support `run_skill`, `explore` (parallel subagents), `write_file`, `read_file`, `search_content`, `glob`, `run_command` |
| **Git repository** | All scenarios | Current HEAD must be resolveable; repo must have at least a seed project (see per-scenario seed) |
| **`~/.reasonix/skills/`** | All scenarios | `blackcow-plan.md` must be installed here via `skills/install.sh` |
| **`explore` subagent** | Phase 1 lane dispatch | Must support parallel fire + collect (all lanes dispatched in one turn) |
| **`blackcow-governor` skill** | Scenario 3 | Must be installed at `~/.reasonix/skills/blackcow-governor.md` |
| **Model service (deepseek-v4-pro)** | Phase 1 pro-tier lanes (L2/L3/L6/L8/L9) | Rate limits respected; model fallback policy tested separately |
| **Model service (deepseek-v4-flash)** | Phase 1 budget-tier lanes (L1/L4/L5/L7/L10) | |
| **File system** | Plan output | `plans/` directory writable |
| **`.omo/` directory structure** | Scenario 3 | `.omo/governor/` must exist for governor decision loading |
| **`web_fetch` / `web_search`** | L6 (Dependency Audit) | Only if `--features` triggers dep-check; else mocked |

---

## Global Setup (run before any scenario)

```bash
# 1. Install skills
bash skills/install.sh

# 2. Verify skill is findable
test -f ~/.reasonix/skills/blackcow-plan.md && echo "OK" || echo "MISSING"

# 3. Create seed project (tiny, for XS-scale tasks)
mkdir -p /tmp/bcow-e2e-seed/src
cat > /tmp/bcow-e2e-seed/src/app.ts << 'EOF'
export function greet(name: string): string {
  return `Hello, ${name}!`;
}
EOF
cat > /tmp/bcow-e2e-seed/src/server.ts << 'EOF'
import { greet } from './app.js';
console.log(greet("World"));
EOF
cat > /tmp/bcow-e2e-seed/package.json << 'EOF'
{ "name": "e2e-seed", "version": "1.0.0" }
EOF
cd /tmp/bcow-e2e-seed && git init && git add -A && git commit -m "seed"

# 4. Create plans/ directory (output target)
mkdir -p /tmp/bcow-e2e-seed/plans
```

---

## Scenario 1 — Simple Task: Context Anchor + Options + Waves

**Goal:** A user invokes blackcow-plan with a simple single-feature task. The full pipeline runs, producing a plan file with Context Anchor (WHY/WHO/WHAT/RISK/SUCCESS/SCOPE), architectural options, and wave progression.

### Input

```json
{
  "skill": "blackcow-plan",
  "arguments": "Add a health-check endpoint to the seed project at /tmp/bcow-e2e-seed. Endpoint should return { status: 'ok' } at GET /health.",
  "working_directory": "/tmp/bcow-e2e-seed"
}
```

### Expected Execution Flow

| Step | Phase | Expected Behavior | Verification |
|---|---|---|---|
| 1 | Pre-invocation | Skill resolved from `~/.reasonix/skills/blackcow-plan.md` | `run_skill` returns without "skill not found" error |
| 2 | Phase -1 IntentGate | Intent classified as **Feature** ("add", "endpoint" signals). Confidence HIGH. Primary gates: M1/M5. Scale default (auto-detect). | Output contains `## Intent Analysis` table with `Detected Intent = Feature` |
| 3 | Phase 0 Pre-flight | Scale auto-detected from seed project (2 files, <200 lines → **XS**). Lanes set to 5 (L1-L5). Budget tier: L1/L4/L5 → flash; Pro tier: L2/L3 → pro. | Plan intro contains `Scale Class: XS`, `Lanes: 5` |
| 4 | Phase 1 Collect (Stage 1) | L1 (Surface Topology) dispatched first via `explore`. Symbol table, file tree, entry point (server.ts) identified. | Stage 1 evidence produced: file tree, entry/exit flow |
| 4b | Phase 1 — Progressive Widening | Uncertainty scored. 2 files, known call chain → **uncertainty < 30** → stop at Stage 1. No Stage 2/3 dispatch. | Widening decision log shows `sufficient_at_stage: 1`, remaining stages NOT dispatched |
| 5 | Phase 2 Cross-Check | Lane evidence reconciled. No contradictions (single-file addition). | Phase 2 section lists evidence sources and confirms consistency |
| 6 | Phase 3 Design | Context Anchor emitted: **WHY** (monitoring), **WHO** (ops team), **WHAT** (GET /health returns JSON), **RISK** (low), **SUCCESS** (curl returns 200), **SCOPE** (one file: server.ts). 3 architectural options presented. | Context Anchor table has all 6 fields. Options list ≥2 alternatives. |
| 7 | Phase 4 — Adversarial Review | **XS scale → SKIPPED.** No reviewer dispatched. | Plan explicitly states "Phase 4 skipped (XS scale)" |
| 8 | Phase 5 Synthesize | Plan file written to `plans/<slug>-plan.md`. File includes Context Anchor, intent analysis, lane summaries, options, waves. | File exists at `plans/add-health-check-endpoint-plan.md` (or slug equivalent) |
| 9 | Self-audit checklist | All items validated (frontmatter, fences, no lsp_*, BKIT gates, budget ≤900K). | No errors in output |

### Expected Output Artifacts

| Artifact | Path | Must Contain |
|---|---|---|
| Plan file | `plans/<slug>-plan.md` | `## Intent Analysis`, Context Anchor table (WHY/WHO/WHAT/RISK/SUCCESS/SCOPE), 3+ waves, `## Risk Register` with ≥3 BKIT gates |
| Widening history | `.omo/memory/widening-history.jsonl` | Entry with `sufficient_at_stage: 1` |

### Edge Cases / Negative Tests

| Test | Input Variation | Expected Outcome |
|---|---|---|
| 1a — Empty args | `arguments: ""` | IntentGate confidence LOW → fallback to Feature class, request clarification |
| 1b — Phantom file ref | Arguments reference non-existent file | L1 lane reports file missing; plan flags as discovery failure |
| 1c — Model pro unavailable | Model service rate-limited on pro | L2/L3 fall back to flash for mechanical sub-tasks; L8 escalation logged to `model-fallback.jsonl` |

---

## Scenario 2 — Multi-Feature Mode (`--features=a,b`)

**Goal:** User invokes with `--features=auth,payments`. Master plan + per-feature plans are generated, with a feature dependency graph.

### Input

```json
{
  "skill": "blackcow-plan",
  "arguments": "--features=auth,payments Add user authentication (login/signup) and payment processing (checkout/webhook) to the seed project at /tmp/bcow-e2e-seed",
  "working_directory": "/tmp/bcow-e2e-seed"
}
```

### Expected Execution Flow

| Step | Phase | Expected Behavior | Verification |
|---|---|---|---|
| 1 | Mode Detection | `--features=auth,payments` triggers **Multi-Feature** mode. Not a sprint (no `--sprint=` flag). | Mode detection log shows "Multi-Feature" |
| 2 | Feature Parsing | Feature list: `["auth", "payments"]` parsed. | Output shows feature list |
| 3 | Phase 0 Pre-flight | Scale auto-detected. Context Budget: ≤900K per feature group. | Budget allocation per feature shown |
| 4 | **Feature Dependency Graph** | Features analyzed for inter-dependency. auth likely has no dependency on payments; payments may depend on auth (user identity). Graph: `auth → payments` (directed edge if dependency exists). | Dependency section lists features and their relationships |
| 5 | Master Plan | `plans/<slug>-master.md` written first. Contains: feature list, dependency graph (text diagram), context budget allocation, ordering (auth first, then payments). | Master plan file exists with `## Feature Dependency Graph`, `## Execution Order` |
| 6 | Per-Feature Plans | Each feature runs independent Phase 1-5 pipeline. auth plan identifies user model, JWT/session. payments plan identifies Stripe integration, webhook handler. | Files exist: `plans/<slug>-auth-plan.md`, `plans/<slug>-payments-plan.md` |
| 7 | Per-Feature Context Anchors | Each plan has its own Context Anchor (auth: WHY=user mgmt, WHO=end-users; payments: WHY=revenue, WHO=finance). | Each per-feature plan contains full Context Anchor table |
| 8 | Independent Lane Dispatch | auth and payments get separate lane dispatches. auth lanes focus on middleware/routes; payments lanes focus on API/webhook. | Lane summaries in each plan differ (different files, symbols, deps) |

### Expected Output Artifacts

| Artifact | Path | Must Contain |
|---|---|---|
| Master plan | `plans/<slug>-master.md` | Feature list, dependency graph, ordering, budget allocation |
| Auth plan | `plans/<slug>-auth-plan.md` | Full 5-phase output scoped to auth files |
| Payments plan | `plans/<slug>-payments-plan.md` | Full 5-phase output scoped to payments files |

### Edge Cases / Negative Tests

| Test | Input Variation | Expected Outcome |
|---|---|---|
| 2a — Single feature `--features=a` | `--features=a` | Treated as Multi-Feature mode (not Single-Feature fallback). Master + one per-feature plan generated. |
| 2b — Circular dependency | Features A depends on B, B depends on A | Dependency graph flagged with CYCLE WARNING; ordering falls back to alphabetical |
| 2c — Budget overflow | 10 features, each needing 200K tokens (total 2M > 900K) | Split into two sequential plan batches (Foundation Plan + Integration Plan) per budget splitting rule |

---

## Scenario 3 — Governor Mode (`--govern=<slug>`)

**Goal:** User invokes with `--govern=my-feature`. The governor decision is loaded from `.omo/governor/my-feature-governance.md`. Phase -1 IntentGate is **skipped**. Mode/gate/widening policy from the governor document is used instead.

### Setup (prerequisite for this scenario)

Before invoking blackcow-plan, create a governor decision file:

```bash
mkdir -p .omo/governor
cat > .omo/governor/my-feature-governance.md << 'GOVEOF'
# Governance Decision: my-feature

| Field | Value |
|---|---|
| **Task** | Add health-check endpoint |
| **Governed at** | 2026-06-15T12:00:00Z |
| **Detected Intent** | Feature |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | STANDARD | Pre-approved feature work |
| **Trust Level** | L3 | Known codebase area |
| **Bootstrap Lanes** | 10 | Full standard lanes |
| **PDCA Max Cycles** | 2 | Low risk |

## Gate Subset

| Gate | Weight | Threshold | Active |
|---|---|---|---|
| M1 | 15% | 80% | YES |
| M2 | 15% | 90% | YES |
| M3 | 10% | 90% | YES |
| S1 | 10% | 80% | YES |
| S2 | 10% | 80% | YES |
| S3 | 10% | 80% | YES |

## Widening Policy

| Parameter | Value |
|---|---|
| **Start Stage** | 2 |
| **Max Stage** | 2 |
| **Uncertainty Threshold Stage1→2** | 40 |
| **Uncertainty Threshold Stage2→3** | (never) |

## Escalation Rules

| Trigger | Action |
|---|---|
| Gate score < threshold | Auto-escalate to human |
| PDCA exceeds max cycles | Notify human reviewer |

## Evidence Index Prewrite

- L1 Surface topology: required
- L2 Call graph: required
- L3 Data shapes: required
- L4 Tests: skip (no test infra)
- L5 Config: required
GOVEOF
```

### Input

```json
{
  "skill": "blackcow-plan",
  "arguments": "--govern=my-feature Add health-check endpoint",
  "working_directory": "/tmp/bcow-e2e-seed"
}
```

### Expected Execution Flow

| Step | Phase | Expected Behavior | Verification |
|---|---|---|---|
| 1 | Input Parsing | `--govern=my-feature` detected. Path constructed: `.omo/governor/my-feature-governance.md`. | Log shows "Governor mode: loading .omo/governor/my-feature-governance.md" |
| 2 | Governor Load | File read successfully. Governance fields extracted: Mode=STANDARD, Trust=L3, Lanes=10, Gates=M1/M2/M3/S1/S2/S3, Widening start=Stage2, max=Stage2. | Output shows loaded governance parameters |
| 3 | **Phase -1 IntentGate SKIPPED** | IntentGate analysis is NOT run. The governor's Detected Intent ("Feature") is used directly. No intent classification table generated from user text. | No `## Intent Analysis` section before Phase 0. Instead, `## Governor Override: Intent = Feature` appears. |
| 4 | Phase 0 Pre-flight | Scale auto-detected (XS from 2 files, <200 lines) but **overridden by governor's Bootstrap Lanes=10**. Lanes = 10 (M-scale), not 5. | Plan states "Lanes: 10 (governor override: Bootstrap Lanes)" |
| 5 | Phase 1 — Widening Policy | Governor policy: start at Stage 2, max Stage 2. Stage 1 is **skipped**. Lanes L1-L4 dispatched immediately (Stage 2 bundle). | Widening log shows `initial_stage: 2`, no Stage 1 ran |
| 6 | Phase 1 — Gate Subset | Only gates listed in governor's active set (M1/M2/M3/S1/S2/S3) are included in Risk Register. Lanes L7/L9/L10 may still run (part of 10-lane dispatch) but their gates are not in the scoring set. | Risk Register omits gates M4/M5/P1/P2/P3. Output notes "Governor-limited gate subset: 6 of 11 gates active." |
| 7 | Phase 2+ | Normal cross-check, design, review (M-scale = 3 reviewers), synthesize. | Standard flow |
| 8 | Plan Output | Plan file written. Includes `## Governor Override` section documenting the source decision. | Plan file contains `Governed by: my-feature-governance.md` |

### Expected Output Artifacts

| Artifact | Path | Must Contain |
|---|---|---|
| Plan file | `plans/<slug>-plan.md` | `## Governor Override` block, governor-limited gate subset (6 gates), lanes=10 despite XS repo |

### Edge Cases / Negative Tests

| Test | Input Variation | Expected Outcome |
|---|---|---|
| 3a — Missing governor file | `--govern=nonexistent` | Governor load fails → fall back to full Phase -1 IntentGate + auto-detection. Warning logged: "Governor file .omo/governor/nonexistent-governance.md not found". |
| 3b — Stale governor (>7 days) | `updated` field >7 days old | Governor loaded but flagged as STALE. IntentGate re-runs for cross-check. Warning: "Governor decision is N days old — consider re-running governor". |
| 3c — Governor mode=FAST + Trust=L4 | Governor specifies FAST mode, L4 trust | Lanes reduced to 5 (FAST mode bootstrap). Phase 4 (review) skipped entirely (L4 trust → no adversarial review). |

---

## Scenario 4 — Emergency Intent

**Goal:** User invokes with urgent/critical language. Emergency intent detected → XS scale forced (5 lanes L1-L5 only), all reviewers skipped (Phase 4 cancelled), all lanes use pro tier.

### Input

```json
{
  "skill": "blackcow-plan",
  "arguments": "URGENT: production login is broken. Users cannot authenticate. This is a critical hotfix — emergency fix needed immediately.",
  "working_directory": "/tmp/bcow-e2e-seed"
}
```

### Expected Execution Flow

| Step | Phase | Expected Behavior | Verification |
|---|---|---|---|
| 1 | Phase -1 IntentGate | Signals detected: "urgent", "critical", "emergency", "broken". Intent classified as **Emergency**. Confidence HIGH. | Intent Analysis table shows `Detected Intent = Emergency` |
| 2 | **Scale Override: XS** | Regardless of actual project scale (which could be M or XL), Emergency forces XS. Lanes = 5 (L1-L5 only). | Plan states `Scale Override: XS (Emergency intent)`. Lanes = 5, not 10. |
| 3 | **Lane Adjustment** | Only L1-L5 dispatched. L6 (Deps), L7 (Git), L8 (Security), L9 (Performance), L10 (Patterns) all **skipped**. All 5 lanes force `model=pro`. | Dispatch list shows only L1-L5. All annotated `[pro]`. No L6-L10 in list. |
| 4 | Phase 1 Dispatch | 5 lanes dispatched in parallel. Each uses pro-tier model. | 5 `explore` calls fired in one batch |
| 5 | **Phase 4 Reviewers SKIPPED** | Emergency routing: "Skip all reviewers (Phase 4 cancelled)". 0 reviewers. No RVA-RVE prompts dispatched. | Plan explicitly states "Phase 4: SKIPPED (Emergency — no reviewers dispatched)" |
| 6 | Phase 5 Synthesize | Plan produced with emergency preamble, minimal gates (fast-track all gates), XS-size plan. | Plan has emergency banner: `⚠️ EMERGENCY PLAN — Immediate Action Required` |
| 7 | Context Anchor | Emergency context: WHY=production down, WHO=all users affected, RISK=HIGH despite small change. | Context Anchor shows RISK=HIGH (override for emergency) |

### Expected Output Artifacts

| Artifact | Path | Must Contain |
|---|---|---|
| Plan file | `plans/<slug>-plan.md` | Emergency banner, XS scale, 5 lanes only, Phase 4 skipped, all lanes pro |

### Edge Cases / Negative Tests

| Test | Input Variation | Expected Outcome |
|---|---|---|
| 4a — Mixed signals (Emergency + Security) | "URGENT security vulnerability in auth" | Priority resolution: Security(severity) > Emergency. Intent = **Security**, not Emergency. But Emergency flag still noted. Scale = XL (Security forces XL). See conflict resolution table in skill. |
| 4b — Emergency with `--features=a,b` | `--features=a,b URGENT hotfix` | Emergency takes precedence. Multi-Feature mode cancelled. Single XS plan produced for highest-priority feature only. Warning: "Multi-feature mode overridden by Emergency intent". |
| 4c — Emergency with `--govern=slug` | `--govern=slug URGENT` | Governor loaded, but Emergency intent **overrides** governor's lane count and reviewer policy. Governor's gate subset still honored. Plan notes "Emergency override of governor lane policy". |

---

## Post-Scenario Cleanup

```bash
# Remove seed project
rm -rf /tmp/bcow-e2e-seed

# (Optional) Remove governor test file
rm -f .omo/governor/my-feature-governance.md

# (Optional) Clear widening history
rm -f .omo/memory/widening-history.jsonl
```

---

## Test Coverage Matrix

| Requirement (from skill) | Scenario 1 | Scenario 2 | Scenario 3 | Scenario 4 |
|---|---|---|---|---|
| Phase -1 IntentGate runs | ✅ Feature | ✅ Feature | ⛔ Governor skip | ✅ Emergency |
| Intent confidence LOW fallback | ✅ (1a) | — | — | — |
| Scale detection (XS/M/XL) | ✅ XS | ✅ M | ✅ Override | ✅ XS forced |
| Adaptive lane count | ✅ 5 lanes | ✅ 10 lanes | ✅ 10 lanes (override) | ✅ 5 lanes (forced) |
| Progressive widening (3 stages) | ✅ Stage 1 only | ✅ Stage 1→2 | ✅ Stage 2 start | ✅ Stage 1 only |
| Cost-tier routing (budget/pro) | ✅ Mixed | ✅ Mixed | ✅ Mixed | ✅ All pro |
| Context Anchor (6 fields) | ✅ | ✅ per-feature | ✅ | ✅ |
| Architectural options (≥3) | ✅ | ✅ | ✅ | ✅ |
| Waves (≥3) | ✅ | ✅ | ✅ | ✅ |
| Risk Register (≥3 BKIT gates) | ✅ | ✅ | ✅ Governor subset | ✅ Fast-track |
| Phase 4 adversarial review | ⛔ XS skip | ✅ 3 reviewers | ✅ 3 reviewers | ⛔ Emergency skip |
| Multi-feature mode | — | ✅ | — | ⛔ Override (4b) |
| Feature dependency graph | — | ✅ | — | — |
| Governor decision load | — | — | ✅ | ⛔ Override (4c) |
| Governor IntentGate skip | — | — | ✅ | — |
| Governor lane override | — | — | ✅ | — |
| Governor gate subset | — | — | ✅ | — |
| Emergency — XS forced | — | — | — | ✅ |
| Emergency — all pro | — | — | — | ✅ |
| Emergency — skip reviewers | — | — | — | ✅ |
| Emergency — fast-track gates | — | — | — | ✅ |
| Model fallback logging | ✅ (1c) | — | — | — |
| Budget splitting | — | ✅ (2c) | — | — |
| Plan file written to `plans/` | ✅ | ✅ master+per | ✅ | ✅ |
| Widening history logged | ✅ | ✅ | ✅ | ✅ |

---

## Infrastructure Readiness Checklist

Before running any scenario, confirm:

```bash
echo "=== Infrastructure Check ==="
echo -n "Reasonix runtime: "; which reasonix 2>/dev/null || echo "MANUAL (requires running environment)"
echo -n "Skill installed:  "; test -f ~/.reasonix/skills/blackcow-plan.md && echo "OK" || echo "MISSING"
echo -n "Git available:    "; git --version 2>/dev/null || echo "MISSING"
echo -n "Seed project:     "; test -d /tmp/bcow-e2e-seed/.git && echo "OK" || echo "NOT SET UP"
echo -n "explore avail:    "; grep -q "explore" ~/.reasonix/skills/blackcow-plan.md && echo "OK (frontmatter)" || echo "CHECK install.sh"
echo -n "plans/ writable:  "; mkdir -p /tmp/bcow-e2e-seed/plans && echo "OK" || echo "NOT WRITABLE"
echo "========================"
```

---

## Test Results Record

| Run Date | Tester | Scenarios Run | Pass/Fail | Notes |
|---|---|---|---|---|
| | | | | |
