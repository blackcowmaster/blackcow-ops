# blackcow-governor — End-to-End Validation Scenarios

> **Level:** L5 E2E (multi-phase, cross-skill orchestration: governor→plan→loop→qa)
> **Skill under test:** `skills/blackcow-governor.md` (v2.0.0)
> **Test date:** (fill on run)
> **Tester:** human-in-the-loop or CI pipeline

## Prerequisites / Infrastructure

All scenarios require the following **runtime services running**:

| Service | Required For | Notes |
|---|---|---|
| **Reasonix agent runtime** | All scenarios | Must support `run_skill`, `explore`, `write_file`, `read_file`, `search_content`, `glob`, `run_command` |
| **Git repository** | All scenarios | Current HEAD resolvable; repo with at least a seed project (see per-scenario seed) |
| **`~/.reasonix/skills/`** | All scenarios | `blackcow-governor.md`, `blackcow-plan.md`, `blackcow-loop.md`, `blackcow-qa.md` all installed via `skills/install.sh` |
| **`explore` subagent** | Phase 0 discovery | Governor dispatch of discovery lanes |
| **`.omo/` directory structure** | All scenarios | `.omo/governor/`, `.omo/ulw-loop/`, `.omo/memory/`, `.omo/library/` all writable |
| **Model service (deepseek-v4-pro)** | Governor (pro-tier) + loop Phase 5 adversarial | Rate limits must be respected |
| **Model service (deepseek-v4-flash)** | Governor discovery lanes | Budget-tier routing |
| **Puppeteer MCP** | Scenarios 5 (browser detection) | Must be registerable via `add_mcp_server` |
| **`curl` / `run_command`** | Scenarios 4 (execution), 5 (fallback strategy) | For smoke-test verification |

---

## Global Setup (run before any scenario)

```bash
# 1. Install all pipeline skills
bash skills/install.sh

# 2. Verify skills are findable
for skill in blackcow-governor blackcow-plan blackcow-loop blackcow-qa; do
  test -f ~/.reasonix/skills/${skill}.md && echo "${skill}: OK" || echo "${skill}: MISSING"
done

# 3. Create seed project
mkdir -p /tmp/bcow-gov-e2e/src
cat > /tmp/bcow-gov-e2e/src/app.ts << 'EOF'
import express from 'express';
const app = express();
app.get('/api/health', (_req, res) => res.json({ status: 'ok' }));
app.post('/api/login', (req, res) => {
  const { username, password } = req.body;
  if (username === 'admin' && password === 'secret') {
    return res.json({ token: 'mock-jwt' });
  }
  return res.status(401).json({ error: 'Unauthorized' });
});
app.get('/api/profile', (req, res) => {
  const token = req.headers.authorization;
  if (!token) return res.status(401).json({ error: 'No auth' });
  return res.json({ name: 'Test User', email: 'test@example.com' });
});
app.listen(3000);
EOF

cat > /tmp/bcow-gov-e2e/src/db.ts << 'EOF'
import sqlite3 from 'sqlite3';
const db = new sqlite3.Database(':memory:');
db.run("CREATE TABLE users (id INT, name TEXT, email TEXT)");
export function getUser(id: number) {
  return db.get(`SELECT * FROM users WHERE id = ${id}`);
}
EOF

cat > /tmp/bcow-gov-e2e/package.json << 'EOF'
{ "name": "bcow-gov-e2e", "version": "1.0.0", "dependencies": { "express": "^4.18.0", "sqlite3": "^5.1.0" } }
EOF

cd /tmp/bcow-gov-e2e && git init && git add -A && git commit -m "seed"

# 4. Create pipeline directories
mkdir -p /tmp/bcow-gov-e2e/.omo/governor
mkdir -p /tmp/bcow-gov-e2e/.omo/ulw-loop/evidence
mkdir -p /tmp/bcow-gov-e2e/.omo/memory
mkdir -p /tmp/bcow-gov-e2e/.omo/library
mkdir -p /tmp/bcow-gov-e2e/plans
mkdir -p /tmp/bcow-gov-e2e/tests

# 5. Seed failure-patterns memory (used by Scenarios 1, 2)
cat > /tmp/bcow-gov-e2e/.omo/memory/failure-patterns.jsonl << 'EOF'
{"id":"FP-001","gate":"S2","symptom":"Unguarded /api/health endpoint exposed","task_area":"auth","last_seen":"2026-05-20T10:00:00Z","effectiveness":85,"fix":"Add auth middleware check to health route","reappeared_after_fix":false}
{"id":"FP-002","gate":"S3","symptom":"Raw SQL string interpolation in db.ts getUser","task_area":"database","last_seen":"2026-05-18T14:30:00Z","effectiveness":30,"fix":"Replace with parameterized query","reappeared_after_fix":true}
EOF

# 6. Seed loop ROI history
cat > /tmp/bcow-gov-e2e/.omo/memory/loop-roi.jsonl << 'EOF'
{"task_area":"auth","score_per_token":0.42,"total_tokens":45000,"recommendation":"PROCEED","timestamp":"2026-06-01"}
{"task_area":"api_endpoint","score_per_token":0.85,"total_tokens":12000,"recommendation":"PROCEED","timestamp":"2026-06-10"}
EOF

# 7. Seed capabilities (no browser for Scenario 5; browser available for others)
cat > /tmp/bcow-gov-e2e/.omo/ulw-loop/capabilities.json << 'EOF'
{"browser_available": true, "max_o_level": "O4", "tools": ["curl", "run_command", "puppeteer"]}
EOF

echo "=== Global Setup Complete ==="
```

---

## Scenario 1 — FAST Mode: Typo/Config Change, Skip Plan, Minimal QA

**Goal:** Governor receives a trivial config-fix task. It decides **FAST** mode (cheapest pipeline). Plan is skipped entirely. Loop executes a single TDD cycle with Hashline (no PDCA). QA runs only universal gates (M1/M2/M3). Entire pipeline finishes in ~12K tokens.

### Input

```json
{
  "skill": "blackcow-governor",
  "arguments": "Fix typo in /api/health endpoint: change 'status' field from 'ok' to 'healthy' in src/app.ts at /tmp/bcow-gov-e2e",
  "working_directory": "/tmp/bcow-gov-e2e"
}
```

### Expected Governance Decision

File: `.omo/governor/fix-typo-health-endpoint-governance.md`

| Field | Expected Value | Rationale |
|---|---|---|
| **Detected Intent** | Bug | Single-field change, trivially small diff |
| **Mode** | FAST | 1-line change, no design needed, no new functionality |
| **Trust Level** | L3 | Learned pattern (typo fix), low risk |
| **Bootstrap Lanes** | Cache-only (skip 7+2) | Governor 0.2 loop ROI shows api_endpoint area has high ROI → trust L3 |
| **PDCA Max Cycles** | 0 | FAST mode: no iterative improvement needed |
| **Adversarial Reviewers** | 0 | XS scale + FAST mode |
| **O-Level** | O1 | Backend-only change, smoke via curl |
| **Gate Subset** | M1, M2, M4 (3 gates) | FAST mode: M1 (spec-match), M2 (test-pass), M4 (lint). No M3/M5/S/P gates |
| **Failure-Pattern Feed** | None active | Typo task area doesn't match FP-001 (auth) or FP-002 (database) |
| **Loop ROI Recommendation** | PROCEED | api_endpoint area has 0.85 score/token |
| **Total Est. Cost (blended)** | ~$0.02 | ~12K tokens × blended rate |

### Expected Execution Flow

| Step | Phase | Skill | Expected Behavior | Verification |
|---|---|---|---|---|
| 1 | Phase 0.1 | Governor | Loads failure-patterns.jsonl — no matching patterns for "typo" area | `search_content` or read confirms FP list, none match "typo" |
| 2 | Phase 0.2 | Governor | Loads loop-roi.jsonl — api_endpoint area: 0.85 score/token, PROCEED | ROI estimate in decision doc shows recommendation = PROCEED |
| 3 | Phase 0.3 | Governor | Runs `git diff --name-only HEAD~1` to detect change surface | Diff detection logged in decision preamble |
| 4 | Phase 0.3b | Governor | Checks capabilities.json — browser available, O4 max | Capability check noted |
| 5 | Phase 0.4 | Governor | Evidence index check: no completion-report.md exists (first run) | Noted: "No prior evidence index" |
| 6 | Phase 1 | Governor | **Decides FAST mode.** Gates: M1, M2, M4 (universal + lint). O-Level: O1. PDCA: 0. Lanes: cache-only. | Decision doc written with all fields populated |
| 7 | Phase 2 Dispatch | Governor | **Plan SKIPPED** (FAST mode rule: "skip for FAST mode"). Directly dispatches loop. | No `run_skill({name:"blackcow-plan"})` call. Dispatch section shows only loop + qa |
| 8 | Phase 1 TDD | Loop | Reads governance decision from `.omo/governor/`. Uses FAST mode. Executes 1 edit (change 'ok' → 'healthy'). Hashline verification passes. | Edit applied. Hashline evidence written. |
| 9 | Phase 2 Gap Detection | Loop | **SKIPPED** (FAST mode: no gap detection) | No gap-report.md written |
| 10 | Phase 2a PDCA | Loop | **SKIPPED** (FAST mode: PDCA Max = 0) | No PDCA cycles executed |
| 11 | Phase 3 Verification | Loop | Runs M2 (test-pass) only per FAST mode mapping. If no tests exist, writes characterization test then verifies pass. | Test output evidence in `.omo/ulw-loop/evidence/` |
| 12 | Phase 4-5 | Loop | **SKIPPED** (FAST mode: no manual QA, no adversarial QA) | No QA agents dispatched |
| 13 | Phase 7 Completion | Loop | Writes completion-report.md with Evidence Compaction Index | Report written, gates referenced |
| 14 | QA Phase 0 | QA | Loads governor decision: gate subset = M1, M2, M4. Loads evidence index from loop completion report. | Log confirms "Governor-limited gate subset: 3 gates" |
| 15 | QA Phase 1 | QA | Evaluates only M1, M2, M4. No S-gates or P-gates evaluated. Each receives numeric score. | QA report shows exactly 3 gates scored, others marked `NOT_EVALUATED` |
| 16 | QA Evidence | QA | Appends to qa-history.jsonl with run metadata | History entry has correct gate_scores keys (M1, M2, M4 only) |

### Expected Output Artifacts

| Artifact | Path | Must Contain |
|---|---|---|
| Governance decision | `.omo/governor/fix-typo-health-endpoint-governance.md` | Mode=FAST, PDCA Max=0, Gates=M1/M2/M4, O-Level=O1, Total Est. Cost ~12K |
| Loop completion report | `.omo/ulw-loop/completion-report.md` | mode=FAST, evidence index with M1/M2/M4 entries |
| QA report | `.omo/ulw-loop/qa-report.md` or `.omo/memory/qa-history.jsonl` | Only M1/M2/M4 scored, others `NOT_EVALUATED` |

### Edge Cases / Negative Tests

| Test | Input Variation | Expected Outcome |
|---|---|---|
| 1a — No git repo | Working directory lacks `.git` | Governor falls back to filesystem scan; mode still FAST but trust level drops to L2 |
| 1b — FAST mode but large diff (>10 files) | Changes span 15 files | Governor overrides to STANDARD (FAST is for 1-line changes only). Decision doc explains override with evidence |
| 1c — Failure pattern matches | Typo in `db.ts` where FP-002 (S3 injection) exists | Governor notes pattern but doesn't escalate (typo fix doesn't touch SQL); still FAST mode |

---

## Scenario 2 — STANDARD Mode with Security Intent

**Goal:** Task touches auth middleware and a SQL query. Governor detects Security intent via file paths (auth routes + raw SQL in db.ts). Decision selects **STANDARD** mode with **S1-S3 gates** added. Plan is generated with security review lanes. Loop runs with 3 adversarial reviewers including a red-team PoC agent. QA evaluates 7 gates (M1-M5 + S1-S3).

### Input

```json
{
  "skill": "blackcow-governor",
  "arguments": "Add role-based access control to /api/profile endpoint: only users with 'admin' role should access it. Fix SQL injection in db.ts getUser by switching to parameterized queries. Project at /tmp/bcow-gov-e2e",
  "working_directory": "/tmp/bcow-gov-e2e"
}
```

### Expected Governance Decision

File: `.omo/governor/add-rbac-api-profile-governance.md`

| Field | Expected Value | Rationale |
|---|---|---|
| **Detected Intent** | Security | Task explicitly mentions "SQL injection", touches auth route + DB layer |
| **Mode** | STANDARD | Multiple files (app.ts + db.ts), security-sensitive but not SIEGE scale |
| **Trust Level** | L2 | Security-sensitive → semi-autonomous, human oversight via adversarial review |
| **Bootstrap Lanes** | 7 (cache-assisted) | STANDARD mode default |
| **PDCA Max Cycles** | 3 | STANDARD mode max |
| **Adversarial Reviewers** | 3 | M-scale; includes 1 security-focused red-team agent |
| **Gate Subset** | M1, M2, M3, M4, M5, S1, S2, S3 | Universal (M1-M3) + lint (M4) + dead-code (M5, may delete old auth) + ALL S-gates (security intent). P-gates skipped. |
| **O-Level** | O2 | API endpoint change → smoke + body verification via curl |
| **Failure-Pattern Feed** | FP-002 active, FP-001 active | S3 task area matches FP-002 (SQL injection, effectiveness 30% → escalate gate priority). S2 task area matches FP-001 (unguarded endpoint, effectiveness 85% → apply known fix). |
| **Failure-Pattern Actions** | FP-002: escalate S3 gate priority. FP-001: apply known fix (add auth middleware check) automatically before PDCA. | Effectiveness ≥80 → auto-apply. Effectiveness <40 → escalate priority. |
| **Loop ROI Recommendation** | PROCEED | auth area has 0.42 score/token — moderate but acceptable |
| **Total Est. Cost (blended)** | ~$0.08 | ~95K tokens (STANDARD budget) |

### Expected Execution Flow

| Step | Phase | Skill | Expected Behavior | Verification |
|---|---|---|---|---|
| 1 | Phase 0.1 | Governor | Loads failure-patterns.jsonl. FP-001 (S2, effectiveness=85) matches auth task → auto-apply fix. FP-002 (S3, effectiveness=30) matches DB task → escalate S3 priority. | Decision doc's Failure-Pattern Feed shows both patterns with action annotations |
| 2 | Phase 0.2 | Governor | Loads loop-roi.jsonl for "auth" area (0.42 score/token). Below recommendation threshold? Pros check: moderate ROI, PROCEED. | Loop ROI estimate shows recommendation = PROCEED |
| 3 | Phase 0.3 | Governor | `git diff --name-only HEAD~1` or file scan detects src/app.ts (auth routes) + src/db.ts (SQL) → S-gates triggered | Gate selection shows S1/S2/S3 = `✅ Type/schema/auth/handler files in diff` |
| 4 | Phase 1 | Governor | **Decides STANDARD + Security add-ons.** Gates include all M-gates + all S-gates. S3 priority escalated due to FP-002. | Decision doc gate table shows S3 with escalation annotation |
| 5 | Phase 2 Dispatch | Governor | **Plan dispatched.** `run_skill({name:"blackcow-plan", arguments: "--govern=add-rbac-api-profile ..."})` | Dispatch section shows plan invocation |
| 6 | Phase -1 IntentGate | Plan | **SKIPPED** — governor already classified intent as Security. Plan uses governor's intent directly. | Plan shows `## Governor Override: Intent = Security` |
| 7 | Phase 1 L8 Security | Plan | Security lane dispatched (L8) per STANDARD mode + security signals | Lane summary includes security analysis |
| 8 | Plan Output | Plan | Plan written with full Context Anchor. RBAC design, parameterized query approach. Risk Register includes S1/S2/S3 gates. | Plan file includes all 8 active gates (M1-M5 + S1-S3) |
| 9 | Phase 1 TDD | Loop | Executes RBAC implementation + parameterized query fix. | Code changes applied |
| 10 | Phase 2a PDCA | Loop | Up to 3 PDCA cycles. Gap detection runs. | PDCA iterations ≤ 3 |
| 11 | Phase 3 Verification | Loop | M2 (test-pass), M3 (regression), M4 (lint) all verified. Security-specific tests also run. | Verification evidence per gate |
| 12 | Phase 5 Adversarial QA | Loop | **3 agents dispatched:** 1 standard reviewer, 1 security-focused (red-team), 1 code-pattern. No PoC exploits (STANDARD mode, not SIEGE). | Phase 5 output shows 3 agent reviews |
| 13 | Phase 7 Completion | Loop | Completion report with Evidence Compaction Index. Gate scores for M1-M5 + S1-S3. | Evidence index includes all 8 active gates |
| 14 | QA Phase 0 | QA | Loads governor gate subset (M1-M5 + S1-S3 = 8 gates). Loads evidence index from loop completion. | Skips gates that loop already passed (hash match). Re-evaluates only failed/missing gates. |
| 15 | QA Phase 1 | QA | Evaluates gates not covered by evidence index. S1 (dataFlow), S2 (auth), S3 (injection) all run with pro-tier analysis. | S2 audit checks that /api/profile is guarded with role check. S3 audit checks db.ts uses parameterized query. |
| 16 | QA Report | QA | All 8 gates scored numerically. Residual risk noted if any gate failed. Failure-pattern auto-population: if S3 fails again (3rd consecutive), creates new FP entry. | QA report shows gate scores + residual risk + maybe new FP entry |

### Expected Output Artifacts

| Artifact | Path | Must Contain |
|---|---|---|
| Governance decision | `.omo/governor/add-rbac-api-profile-governance.md` | Mode=STANDARD, Gates=M1-M5+S1-S3, PDCA=3, Adversarial Reviewers=3, Failure-Pattern Feed with FP-001 (auto-apply) + FP-002 (escalate) |
| Plan file | `plans/<slug>-plan.md` | Governor Override section, 8 active gates, RBAC design, parameterized SQL |
| Completion report | `.omo/ulw-loop/completion-report.md` | mode=STANDARD, 8 gate entries in evidence index |
| QA history | `.omo/memory/qa-history.jsonl` | 8 gates scored; failure-pattern auto-population entry if S3 failed consecutively |

### Edge Cases / Negative Tests

| Test | Input Variation | Expected Outcome |
|---|---|---|
| 2a — Security + Performance mixed | Task mentions both "SQL injection" and "p95 latency <200ms" | Governor detects dual intent (Security + Performance). Gate subset = M-gates + S-gates + P-gates. Mode upgrades to FULL (to accommodate both). |
| 2b — Auto-fix fails (FP-001 effectiveness was stale) | Fix from FP-001 no longer applies (middleware API changed) | Governor notes "Known fix attempt FAILED" in decision. S2 priority escalated. Failure pattern updated with `reappeared_after_fix: true`. |
| 2c — No S3 evaluation possible | db.ts doesn't exist (user removed it in a prior commit) | S3 gate marked `NOT_EVALUATED` (no injection surface found). QA reports "S3: N/A — no database code in scope." Residual risk documented. |

---

## Scenario 3 — `--govern` Reuse: Governor Writes, Plan Loads

**Goal:** A prior governor run already produced a governance decision for "add-health-check". A new invocation of blackcow-plan with `--govern=add-health-check` loads that decision. Plan skips Phase -1 IntentGate entirely. Mode/gates/widening policy come from the loaded document. The downstream loop and qa also use the same governance file.

### Setup (prerequisite)

```bash
# Create a prior governance decision (simulating a previous governor run)
cat > /tmp/bcow-gov-e2e/.omo/governor/add-health-check-governance.md << 'GOVEOF'
# Governance Decision: add-health-check

| Field | Value |
|---|---|
| **Task** | Add a GET /api/status endpoint returning `{ alive: true }` |
| **Governed at** | 2026-06-15T10:00:00Z |
| **Detected Intent** | Feature |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | STANDARD | Small feature, single endpoint |
| **Trust Level** | L3 | Known codebase area (express app) |
| **Bootstrap Lanes** | 10 | STANDARD default |
| **PDCA Max Cycles** | 2 | Low risk feature |
| **Adversarial Reviewers** | 0 | XS scale → skip |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal |
| M2 test-pass | ✅ | Universal |
| M3 regression | ✅ | Universal |
| M4 lint | ✅ | Source files in diff |
| M5 dead-code | ❌ | No deletions |
| S1 dataFlow | ❌ | No type/schema files |
| S2 auth | ❌ | No auth/route files |
| S3 injection | ❌ | No handler/input files |
| P1 query | ❌ | No DB files |
| P2 memory | ❌ | No collection files |
| P3 latency | ❌ | No p95_target_ms in plan |

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | O2 |
| **Max Capability** | O4 |
| **Browser Available?** | YES |
| **Capped?** | No |
| **Residual Risk** | None |

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| Stage 1 | uncertainty_score < 30 | 3 |
| Stage 2 | 30 ≤ uncertainty < 60 | 7 |
| Stage 3 | uncertainty ≥ 60 | 10 |

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Total estimated** | ~45K |
| **Est. cost (blended)** | $0.04 |
| **Historical ROI** | 0.85 score/token (api_endpoint) |
| **Recommendation** | PROCEED |
GOVEOF

cd /tmp/bcow-gov-e2e
```

### Input

```json
{
  "skill": "blackcow-plan",
  "arguments": "--govern=add-health-check Add a GET /api/status endpoint returning { alive: true } to /tmp/bcow-gov-e2e",
  "working_directory": "/tmp/bcow-gov-e2e"
}
```

### Expected Execution Flow

| Step | Phase | Skill | Expected Behavior | Verification |
|---|---|---|---|---|
| 1 | Input Parsing | Plan | `--govern=add-health-check` detected. Path = `.omo/governor/add-health-check-governance.md`. | Log shows "Governor mode: loading .omo/governor/add-health-check-governance.md" |
| 2 | Governor Load | Plan | Governance decision loaded. Fields extracted: Mode=STANDARD, Trust=L3, Lanes=10, Gates=M1/M2/M3/M4, PDCA=2, O-Level=O2, Widening=Stage1-3. | Plan output shows loaded governance parameters |
| 3 | **Phase -1 IntentGate SKIPPED** | Plan | No intent classification runs. Governor's "Feature" intent used directly. | No `## Intent Analysis` section. Instead `## Governor Override: Intent = Feature` appears. |
| 4 | Phase 0 Pre-flight | Plan | Scale auto-detected. Governor's Bootstrap Lanes=10 overrides auto-scale. | Plan states "Lanes: 10 (governor override)" |
| 5 | Phase 1 — Widening | Plan | Governor policy: progressive widening from Stage 1. Standard uncertainty thresholds used. | Widening history shows initial_stage=1 |
| 6 | Phase 1 — Gate Subset | Plan | Only 4 gates active (M1/M2/M3/M4). Risk Register omits M5/S1/S2/S3/P1/P2/P3. | Plan explicitly states "Governor-limited gate subset: 4 of 11 gates active" |
| 7 | Phase 2-5 | Plan | Normal cross-check, design, review (governor says 0 reviewers → skip). Synthesize. | Plan file produced without adversarial review section |
| 8 | Governor Override Section | Plan | Plan file includes `## Governor Override` block documenting source decision, staleness check (<7d → fresh). | Plan contains `Governed by: add-health-check-governance.md`, date check showing FRESH |
| 9 | Loop Dispatch | (user) | Loop called with `--govern=add-health-check` | Loop loads same governance. PDCA=2, O2 verification. |
| 10 | Loop Phase 3 | Loop | M2 verification passes. O2 verification via curl: `curl -s GET /api/status` returns `{ alive: true }`. | Observable evidence written, O2 verified |
| 11 | QA Dispatch | (user) | QA called with `--govern=add-health-check` | QA loads governor gate subset (M1/M2/M3/M4 = 4 gates). Only those evaluated. |

### Expected Output Artifacts

| Artifact | Path | Must Contain |
|---|---|---|
| Plan file | `plans/<slug>-plan.md` | `## Governor Override` block, 4 active gates, Lanes=10, Trust=L3 |
| Completion report | `.omo/ulw-loop/completion-report.md` | mode=STANDARD, O2 verification evidence |
| QA report | `.omo/memory/qa-history.jsonl` | Only M1/M2/M3/M4 scored |

### Edge Cases / Negative Tests

| Test | Input Variation | Expected Outcome |
|---|---|---|
| 3a — Missing governor file | `--govern=nonexistent` | Plan falls back to full Phase -1 IntentGate + auto-detection. Warning logged: "Governor file not found at .omo/governor/nonexistent-governance.md" |
| 3b — Stale governor (>7 days) | Governor decision dated 2026-01-01 | Plan loads decision but flags as STALE. Re-runs IntentGate for cross-check. Warning: "Governor decision is 165 days old — consider re-running governor" |
| 3c — Stale with override | User adds `--stale-ok` flag | Plan loads governor decision without staleness warning. Still runs IntentGate cross-check but does NOT override governor's intent. |
| 3d — Governor mode=FAST | Governor has Mode=FAST, Trust=L4 | Plan reduces lanes to 5 (FAST bootstrap). Plan Phase 4 (review) skipped entirely. Plan notes "Governor FAST mode — minimal pipeline." |
| 3e — Plan invoked without `--govern`, prior governor file exists | No `--govern` flag but `.omo/governor/` has a matching decision | Plan does NOT auto-discover governor files. Runs full Phase -1 IntentGate. Governor file is ignored unless explicitly loaded. |

---

## Scenario 4 — Escalation Trigger: PDCA Budget Exhausted

**Goal:** Governor sets PDCA Max Cycles = 3 (STANDARD mode). Loop's Phase 2a PDCA iterator runs 3 cycles without closing the gap (same gate fails twice). Hard stop rule fires: ESCALATE. Escalation log written. User is notified. Pipeline pauses pending resolution.

### Input

```json
{
  "skill": "blackcow-governor",
  "arguments": "Refactor sqlite3 queries in db.ts to use parameterized statements. The raw SQL interpolation is a security risk. Project at /tmp/bcow-gov-e2e",
  "working_directory": "/tmp/bcow-gov-e2e"
}
```

### Expected Governance Decision

File: `.omo/governor/refactor-sql-parameterized-governance.md`

| Field | Expected Value | Rationale |
|---|---|---|
| **Detected Intent** | Security | Explicitly mentions "SQL injection", "security risk" |
| **Mode** | STANDARD | Single file refactor, security-sensitive but small scope |
| **Trust Level** | L2 | Security-sensitive → semi-auto with human oversight |
| **PDCA Max Cycles** | 3 | STANDARD mode max |
| **Escalation Rules** | Budget near limit (80%) → ESCALATE, Same gate ×2 → ESCALATE | From governor's escalation rule table in decision doc |
| **Gate Subset** | M1-M5 + S1, S2, S3 | Universal + security gates |
| **Failure-Pattern Feed** | FP-002 active (S3 injection, effectiveness=30 → escalate priority) | FP-002's low effectiveness means the known fix is unreliable → governor notes this as escalation risk |

### Setup for ESCALATE Simulation

Before running the loop, pre-seed a failing condition to guarantee PDCA exhaust:

```bash
# Make the SQL injection harder to fix — introduce a secondary templating pattern
cat > /tmp/bcow-gov-e2e/src/db.ts << 'EOF'
import sqlite3 from 'sqlite3';
const db = new sqlite3.Database(':memory:');
db.run("CREATE TABLE users (id INT, name TEXT, email TEXT)");

function sanitize(val: string): string {
  return val.replace(/'/g, "''");  // insufficient — still vulnerable to other patterns
}

export function getUser(id: number): any {
  // Pattern 1: raw interpolation
  const query = `SELECT * FROM users WHERE id = ${id}`;
  return db.get(query);
}

export function findUser(name: string): any {
  // Pattern 2: insufficient sanitization
  const query = `SELECT * FROM users WHERE name = '${sanitize(name)}'`;
  return db.get(query);
}
EOF

cd /tmp/bcow-gov-e2e && git add -A && git commit -m "Add second injection pattern"
```

### Expected Execution Flow

| Step | Phase | Skill | Expected Behavior | Verification |
|---|---|---|---|---|
| 1 | Phase 1 | Governor | Decides STANDARD mode, PDCA Max=3. Notes FP-002 (effectiveness=30) → escalation risk flagged early. | Decision doc includes "Escalation risk: FP-002 fix unreliable (effectiveness=30)". |
| 2 | Dispatch | Governor | plan → loop → qa dispatched | Standard pipeline |
| 3 | Phase 1 TDD | Loop | First edit: attempts parameterized query on `getUser`. Uses `?` placeholder. Hashline verification passes. | Edit applied successfully |
| 4 | Phase 2 Gap Detection | Loop | Gap detector identifies `findUser` still uses sanitize+interpolation → only partial fix (matchRate ~50%). | gap-report.md shows "findUser still vulnerable" |
| 5 | Phase 2a PDCA Cycle 1 | Loop | Second edit: attempts to fix `findUser`. Uses parameterized query. Tests pass in isolation. | Evidence: cycle-1 results |
| 6 | Phase 2 Gap Redetection | Loop | **Same gate fails again**: S3 score still fails because the `sanitize` function is removed but new injection surfaces found in another query pattern (e.g., ORDER BY with dynamic column). MatchRate still < threshold. | Gap report shows S3 failure persisting |
| 7 | Phase 2a PDCA Cycle 2 | Loop | Third edit: different approach (whitelist column names). Hashline passes. | Evidence: cycle-2 results |
| 8 | Phase 2 Gap Redetection | Loop | S3 score still < threshold. PDCA cycles used = 2 of 3. Budget utilization = 66%. Not yet at 80% limit. | Loop continues |
| 9 | Phase 2a PDCA Cycle 3 | Loop | Fourth edit: exhaustive fix attempt. Hashline passes. | Evidence: cycle-3 results |
| 10 | Phase 2 Gap Redetection | Loop | S3 score STILL < threshold. PDCA cycles used = 3 of 3 = 100%. Budget utilized. | **Trigger: Budget near limit (100% ≥ 80%)** |
| 11 | **ESCALATE Fires** | Loop | Hard stop rule 3: "No improvement near budget limit → ESCALATE or ask user." Also rule 2: "Same gate fails twice" fires (S3 failed on cycles 1, 2, 3). | escalation-log.jsonl entry written |
| 12 | Automated Actions | Loop | D1 dispatched (pro-tier analysis) to identify root cause. D1 identifies: "SQL schema uses dynamic column names in ORDER BY — parameterized queries cannot parameterize column identifiers. Need schema redesign." | D1 report produced |
| 13 | Plan Re-evaluation | (auto) | Loop dispatches `blackcow-plan` for architectural re-evaluation: "Redesign db.ts schema to eliminate dynamic column names while preserving sort functionality." | Plan re-evaluation triggered |
| 14 | **Pipeline PAUSED** | (user) | ESCALATE_REQUIRED emitted with reason, failing gate, cycles count. Human must decide: (a) approve plan re-eval output, (b) accept partial fix, (c) abort. | User prompt displayed with options |
| 15 | (Resume) | (user) | After user resolution, PDCA counter resets to 0, loop restarts Phase 2 with new plan. | Loop restarts with fresh budget |

### ESCALATE Log Entry

Expected entry in `.omo/memory/escalation-log.jsonl`:

```json
{
  "timestamp": "<ISO>",
  "run_id": "<uuid>",
  "trigger_rule": 3,
  "also_triggered": [2],
  "failing_gate": "S3",
  "cycles_before_escalate": 3,
  "pdca_budget": 3,
  "budget_utilization_pct": 100,
  "resolution": "plan_regenerated",
  "d1_finding": "SQL schema uses dynamic column names in ORDER BY — parameterized queries cannot parameterize column identifiers. Need schema redesign."
}
```

### Expected Output Artifacts

| Artifact | Path | Must Contain |
|---|---|---|
| Governance decision | `.omo/governor/refactor-sql-parameterized-governance.md` | PDCA Max=3, Escalation Rules table with budget/same-gate triggers, FP-002 flagged |
| Gap report | `.omo/ulw-loop/gap-report.md` | S3 failure persisting across cycles |
| PDCA history | `.omo/ulw-loop/evidence/<slug>-pdca-cycles.json` or `.omo/memory/pdca-history.jsonl` | 3 cycles executed, each with gap delta |
| Escalation log | `.omo/memory/escalation-log.jsonl` | Entry with trigger_rule=3, failing_gate="S3", budget_utilization_pct=100 |
| D1 analysis | `.omo/ulw-loop/evidence/<slug>-d1-report.md` | Root cause: dynamic column names prevent full parameterization |

### Edge Cases / Negative Tests

| Test | Input Variation | Expected Outcome |
|---|---|---|
| 4a — First-cycle resolution | Fix succeeds on PDCA cycle 1 (matchRate 100%) | No escalation. PDCA stops early (max not reached). Evidence shows "gap closed @ cycle 1". Completion report written normally. |
| 4b — Budget near limit (80%) | 2 of 3 cycles used, matchRate 88% but improving | ESCALATE rule 3 fires (80% threshold). User asked: "Continue with last cycle or accept partial result?" User can approve cycle 3 or accept 88%. |
| 4c — Trust Level L4 (Full-Auto) | Governor sets L4 despite security context | At L4, PDCA Max = 7. Loop auto-commits after gates pass. If escalation fires, auto-dispatch plan re-eval WITHOUT pausing for user. ESCALATE still logged. |
| 4d — No new evidence (rule 1) | After PDCA cycle 2, delta=0 (same gaps, same scores, no file changes) | ESCALATE rule 1 fires BEFORE budget exhaustion. Loop stops immediately. Escalation: "No new evidence after cycle 2 — re-dispatch D1 + plan re-eval." |

---

## Scenario 5 — Observable Level Capping: No Browser Available

**Goal:** Governor detects that browser/puppeteer tooling is unavailable (capabilities.json declares no browser). Task involves a UI change that would ideally need O2/O3 verification. Governor caps max O-Level to O1. Fallback strategy documented. Residual risk reported by QA.

### Setup

```bash
# Overwrite capabilities to simulate no-browser environment
cat > /tmp/bcow-gov-e2e/.omo/ulw-loop/capabilities.json << 'EOF'
{"browser_available": false, "max_o_level": "O1", "tools": ["curl", "run_command"]}
EOF

cd /tmp/bcow-gov-e2e
```

### Input

```json
{
  "skill": "blackcow-governor",
  "arguments": "Add a 'Forgot Password' link to the login page response in /api/login: after 'Unauthorized' error, include { error: 'Unauthorized', resetLink: '/forgot-password' }. Project at /tmp/bcow-gov-e2e",
  "working_directory": "/tmp/bcow-gov-e2e"
}
```

### Expected Governance Decision

File: `.omo/governor/add-forgot-password-link-governance.md`

| Field | Expected Value | Rationale |
|---|---|---|
| **Detected Intent** | Feature | Adding a response field, no security/performance concern |
| **Mode** | STANDARD | Single-file change but adds response contract change (ideally O2) |
| **Trust Level** | L3 | Known endpoint, low-risk addition |
| **O-Level** | **O1** (capped from O2) | Change type "API endpoint (modified)" would ideally be O2 (body verify), but no browser → cap to O1 (smoke: endpoint responds) |
| **Max Capability** | O1 | From capabilities.json: browser_available=false, curl+run_command only |
| **Browser Available?** | NO | Capabilities check result |
| **Capped?** | **O2 → O1 (no browser tooling)** | Explicit capping annotation |
| **Fallback Strategy** | DOM snapshot via `curl | grep` for expected strings. API-level state verification (POST then GET). Supplement with unit tests. | Fallback documented |
| **Residual Risk** | Cannot visually verify the reset link renders correctly in browser. Link text and URL correctness confirmed via curl + unit tests. | Risk noted |
| **Gate Subset** | M1-M5 | Universal + lint + dead-code. No S/P gates (no auth/db/files changed in diff). |

### Expected Execution Flow

| Step | Phase | Skill | Expected Behavior | Verification |
|---|---|---|---|---|
| 1 | Phase 0.3b | Governor | Reads capabilities.json → browser_available=false, max_o_level=O1. Cannot register puppeteer. | Capability detection log shows "Browser: NO, Max O-Level: O1" |
| 2 | Phase 1 | Governor | O2 ideal → capped to O1. Fallback strategy: curl smoke test + unit test for response body. Residual risk documented. | Decision doc's Observable Level section shows the cap + fallback + residual risk |
| 3 | Dispatch | Governor | plan → loop → qa dispatched | Standard pipeline |
| 4 | Plan | Plan | Plan generated with Context Anchor. O-Level noted as O1 (capped). Fallback: "Verify via curl + unit test." | Plan mentions O1 verification strategy |
| 5 | Loop Phase 1 TDD | Loop | Edit: adds `resetLink: '/forgot-password'` to error response in /api/login. | Edit applied |
| 6 | Loop Phase 3 Verification | Loop | Runs M2 (test-pass), M3 (regression). Fails O2 verification check → gracefully degrades to O1. | O1 curl smoke: `curl -s -X POST -d '{"username":"bad","password":"creds"}' /api/login` returns the new field |
| 7 | Loop Phase 4 Manual QA | Loop | **Capped to O1.** Fallback: `curl | grep resetLink` to confirm field presence. No browser verification. | Evidence: `.omo/ulw-loop/evidence/<slug>-observable.json` contains `capped_from: "O2"`, `browser_available: false`, `residual_risk: "<text>"` |
| 8 | Loop Completion | Loop | Completion report includes observable verification: O1 achieved, O2 deferred. Evidence index populated. | Report notes "O2 verification deferred — requires browser tooling" |
| 9 | QA Phase 0 | QA | Loads governor decision. Reads O-Level cap (O2→O1), fallback strategy. | QA notes "Observable level capped — residual risk evaluation mode" |
| 10 | QA Report | QA | Runs M1-M5 evaluation. In report summary, includes a **Residual Risk Section**: "O2 observable verification was not performed (no browser tooling). The /forgot-password link field presence was verified via curl and unit test. Visual rendering (link styling, positioning, accessibility) was NOT verified. Risk: LOW — link is a JSON field, not rendered HTML. Full O2 verification requires puppeteer MCP." | QA report contains residual risk subsection |
| 11 | Failure-Pattern | QA | If S3/S2 patterns existed, they'd be checked. Not applicable here (no S-gates active). | N/A |

### Observable Evidence Format

Expected content in `.omo/ulw-loop/evidence/<slug>-observable.json`:

```json
{
  "phase": "4",
  "observable_level": "O1",
  "capped_from": "O2",
  "browser_available": false,
  "residual_risk": "O2 verification deferred — requires browser tooling. Field presence verified via curl + unit test. Visual rendering (link styling, positioning, accessibility) NOT verified. Risk: LOW — field is JSON response body, not rendered HTML.",
  "screenshots": [],
  "interactions_verified": ["POST /api/login with bad credentials returns resetLink field"],
  "fallback_strategy": "curl smoke test + unit test for response body assertion",
  "capabilities_snapshot": {"browser_available": false, "max_o_level": "O1", "tools": ["curl", "run_command"]}
}
```

### Expected Output Artifacts

| Artifact | Path | Must Contain |
|---|---|---|
| Governance decision | `.omo/governor/add-forgot-password-link-governance.md` | O2→O1 cap, Fallback Strategy, Residual Risk, Browser Available=NO |
| Plan file | `plans/<slug>-plan.md` | O1 verification plan, curl-based smoke test |
| Observable evidence | `.omo/ulw-loop/evidence/<slug>-observable.json` | `capped_from: "O2"`, `browser_available: false`, `residual_risk` populated |
| QA report | `.omo/memory/qa-history.jsonl` or report file | Residual risk section documenting deferred O2 verification |

### Edge Cases / Negative Tests

| Test | Input Variation | Expected Outcome |
|---|---|---|
| 5a — O4 ideal, capped to O1 (UI change) | Task: "Add a password strength indicator UI component to login form" | Ideal O4 (public-facing UI), capped all the way to O1. Governor flags HIGH residual risk. Fallback: CSS unit tests + DOM snapshot via curl. QA reports HIGH residual risk for release. |
| 5b — O0 change (backend-only, no UI surface) | Task: "Add database migration for users table index" | Even without browser, O0 is achievable. No cap needed. Decision: O-Level=O0, "No browser required — backend-only change." No residual risk. |
| 5c — Browser becomes available mid-pipeline | User installs puppeteer MCP after governor but before loop | Loop re-detects browser (Phase 0 capability check) and upgrades to O2. Loop logs "O-Level upgraded from governor's O1 to O2 — browser detected at runtime." Override noted in completion report. |
| 5d — Partial browser (no puppeteer_navigate, only puppeteer_evaluate) | capabilities.json shows `{"tools": ["puppeteer_evaluate"]}` | Governor caps to O1 (can't navigate or screenshot). Fallback: use puppeteer_evaluate to read DOM content. Residual risk: "Can inspect DOM but cannot render or interact visually." |

---

## Post-Scenario Cleanup

```bash
# Remove seed project
rm -rf /tmp/bcow-gov-e2e

# Remove governor test files (if any were left outside seed project)
rm -f .omo/governor/*-governance.md
rm -f .omo/memory/escalation-log.jsonl
rm -f .omo/memory/pdca-history.jsonl
```

---

## Test Coverage Matrix

| Requirement (from governor skill) | Sc1 FAST | Sc2 Security | Sc3 --govern | Sc4 Escalation | Sc5 O-Cap |
|---|---|---|---|---|---|
| Phase 0.1 Failure-Pattern load | ✅ None active | ✅ FP-001/002 matched | N/A (reuse) | ✅ FP-002 → escalate priority | ✅ No patterns |
| Phase 0.2 Loop ROI load | ✅ PROCEED | ✅ PROCEED | N/A | ✅ PROCEED | ✅ PROCEED |
| Phase 0.3 Change surface detection | ✅ git diff | ✅ Files trigger S-gates | N/A | ✅ db.ts detected | ✅ app.ts detected |
| Phase 0.3b Capability detection | ✅ O4 max | ✅ O4 max | N/A | ✅ O4 max | ✅ O1 max (no browser) |
| Phase 0.4 Evidence index load | ✅ No prior index | ✅ No prior index | N/A | ✅ No prior index | ✅ No prior index |
| Mode selection | FAST | STANDARD | STANDARD (loaded) | STANDARD | STANDARD |
| Trust Level assignment | L3 | L2 | L3 (loaded) | L2 | L3 |
| PDCA Max Cycles | 0 | 3 | 2 (loaded) | 3 | 3 |
| Bootstrap Lanes | Cache-only (skip 7+2) | 7 cache-assisted | 10 (loaded) | 7 cache-assisted | 7 cache-assisted |
| Gate subset selection | M1/M2/M4 only | M1-M5+S1-S3 (8) | M1-M4 (4) | M1-M5+S1-S3 (8) | M1-M5 (5) |
| Gate selection based on diff signals | ✅ Typo → M4 | ✅ S-gates from diff | ✅ Loaded from gov | ✅ S-gates from diff | ✅ No S/P from diff |
| Observable level decision | O1 | O2 | O2 (loaded) | O2 | O1 (capped from O2) |
| O-level capping | No | No | No | No | ✅ O2→O1 |
| Fallback strategy | N/A | N/A | N/A | N/A | ✅ curl + unit tests |
| Residual risk documentation | ✅ (none) | ✅ (if capped) | N/A | ✅ (escalation risk) | ✅ (browser gap) |
| Widening policy | Default | Default | Loaded | Default | Default |
| Escalation rules defined | ✅ | ✅ | ✅ | ✅ (triggered) | ✅ |
| Budget near limit (80%) rule | N/A (PDCA=0) | ✅ Defined | ✅ Defined | ✅ **Triggered** | ✅ Defined |
| Same gate ×2 rule | N/A (PDCA=0) | ✅ Defined | ✅ Defined | ✅ **Triggered** | ✅ Defined |
| Failure-pattern auto-apply (eff≥80) | N/A | ✅ FP-001 auto-apply | N/A | N/A | N/A |
| Failure-pattern escalate (eff<40) | N/A | ✅ FP-002 escalate | N/A | ✅ FP-002 escalate | N/A |
| Loop ROI recommendation | PROCEED | PROCEED | N/A | PROCEED | PROCEED |
| Est. cost calculation | ~$0.02 (12K tok) | ~$0.08 (95K tok) | ~$0.04 (45K tok) | ~$0.08 (95K tok) | ~$0.06 (70K tok) |
| Plan dispatch | ⛔ SKIPPED (FAST) | ✅ Dispatched | ✅ Dispatched | ✅ Dispatched | ✅ Dispatched |
| Plan IntentGate skip | N/A (no plan) | ✅ Governor override | ✅ Governor override | ✅ Governor override | ✅ Governor override |
| Loop execution with mode | ✅ FAST | ✅ STANDARD | ✅ STANDARD | ✅ STANDARD (→ESCALATE) | ✅ STANDARD |
| Loop adversarial reviewers | 0 | 3 (1 security) | 0 | 3 | 3 |
| PDCA iterator honor | ✅ 0 cycles | ✅ ≤3 cycles | ✅ ≤2 cycles | ✅ **3 cycles → ESCALATE** | ✅ ≤3 cycles |
| Loop gap detection | ⛔ Skipped | ✅ | ✅ | ✅ **→ ESCALATE** | ✅ |
| Hard stop rule enforcement | N/A | N/A | N/A | ✅ **Rule 2+3** | N/A |
| D1 dispatch on ESCALATE | N/A | N/A | N/A | ✅ D1 dispatched | N/A |
| Plan re-eval on ESCALATE | N/A | N/A | N/A | ✅ Auto-triggered | N/A |
| ESCALATE log written | N/A | N/A | N/A | ✅ `.omo/memory/escalation-log.jsonl` | N/A |
| QA with governor gate subset | ✅ 3 gates | ✅ 8 gates | ✅ 4 gates | ✅ 8 gates | ✅ 5 gates |
| QA residual risk report | N/A | ✅ (if capped) | N/A | ✅ (escalation context) | ✅ (O-level cap) |
| QA evidence index skip | ✅ If loop passed | ✅ If loop passed | ✅ If loop passed | ✅ If loop passed | ✅ If loop passed |
| Post-mortem self-audit | ✅ mode/level match | ✅ mode/level match | ✅ mode/level match | ✅ escalation check | ✅ cap verification |

---

## Cross-Skill Contract Verification Matrix

Each scenario tests that the cross-skill evidence contracts (from governor's Integration Contract section) are honored:

| Contract | Producer → Consumer | Sc1 | Sc2 | Sc3 | Sc4 | Sc5 |
|---|---|---|---|---|---|---|
| `.omo/governor/<slug>-governance.md` → plan | governor → plan | ⛔ Plan skipped | ✅ Loaded | ✅ Loaded — skipped IntentGate | ✅ Loaded | ✅ Loaded |
| `.omo/governor/<slug>-governance.md` → loop | governor → loop | ✅ FAST mode | ✅ STANDARD + S-gates | ✅ PDCA=2, O2 | ✅ PDCA=3, esc rules | ✅ O1 cap |
| `.omo/governor/<slug>-governance.md` → qa | governor → qa | ✅ 3 gates | ✅ 8 gates | ✅ 4 gates | ✅ 8 gates | ✅ 5 gates |
| `plans/<slug>.md` → loop | plan → loop | ⛔ No plan | ✅ Dispatched | ✅ Loaded | ✅ Dispatched | ✅ Dispatched |
| `.omo/ulw-loop/completion-report.md` → qa | loop → qa | ✅ Evidence index | ✅ Evidence index | ✅ Evidence index | ✅ (before esc) | ✅ Evidence index |
| `.omo/memory/qa-history.jsonl` → librarian | qa → librarian | ✅ Appended | ✅ Appended | ✅ Appended | ✅ Appended | ✅ Appended |
| `.omo/memory/failure-patterns.jsonl` → governor | librarian → governor | ✅ Loaded | ✅ Loaded + actions | N/A | ✅ Loaded + escalations | ✅ Loaded |

---

## Infrastructure Readiness Checklist

Before running any scenario, confirm:

```bash
echo "=== Infrastructure Check ==="
echo -n "Reasonix runtime:   "; which reasonix 2>/dev/null || echo "MANUAL (requires running environment)"
echo -n "Governor installed: "; test -f ~/.reasonix/skills/blackcow-governor.md && echo "OK" || echo "MISSING"
echo -n "Plan installed:     "; test -f ~/.reasonix/skills/blackcow-plan.md && echo "OK" || echo "MISSING"
echo -n "Loop installed:     "; test -f ~/.reasonix/skills/blackcow-loop.md && echo "OK" || echo "MISSING"
echo -n "QA installed:       "; test -f ~/.reasonix/skills/blackcow-qa.md && echo "OK" || echo "MISSING"
echo -n "Git available:      "; git --version 2>/dev/null || echo "MISSING"
echo -n "Seed project:       "; test -d /tmp/bcow-gov-e2e/.git && echo "OK" || echo "NOT SET UP"
echo -n ".omo/ governor:     "; test -d /tmp/bcow-gov-e2e/.omo/governor && echo "OK" || echo "NOT SET UP"
echo -n ".omo/ ulw-loop:     "; test -d /tmp/bcow-gov-e2e/.omo/ulw-loop && echo "OK" || echo "NOT SET UP"
echo -n ".omo/ memory:       "; test -d /tmp/bcow-gov-e2e/.omo/memory && echo "OK" || echo "NOT SET UP"
echo -n "Capabilities file:  "; test -f /tmp/bcow-gov-e2e/.omo/ulw-loop/capabilities.json && echo "OK" || echo "NOT SET UP"
echo -n "Failure patterns:   "; test -f /tmp/bcow-gov-e2e/.omo/memory/failure-patterns.jsonl && echo "OK" || echo "NOT SET UP"
echo -n "Loop ROI history:   "; test -f /tmp/bcow-gov-e2e/.omo/memory/loop-roi.jsonl && echo "OK" || echo "NOT SET UP"
echo -n "explore available:  "; grep -q "explore" ~/.reasonix/skills/blackcow-governor.md && echo "OK (frontmatter)" || echo "CHECK install.sh"
echo -n "plans/ writable:    "; mkdir -p /tmp/bcow-gov-e2e/plans && echo "OK" || echo "NOT WRITABLE"
echo "========================"
```

---

## Test Results Record

| Run Date | Tester | Scenarios Run | Pass/Fail | Notes |
|---|---|---|---|---|
| | | | | |
