# Governance Decision: sim-express-crud-patch

| Field | Value |
|---|---|
| **Task** | Add PATCH /api/tasks/:id endpoint with partial-update semantics. Only provided fields are updated; missing fields keep existing values. Empty-string `title` rejected with 400. Distinguish "not provided" (keep existing) vs "provided-as-empty" (reject). Tests: partial update, empty title rejection, no-op patch, invalid fields. |
| **Governed at** | 2026-06-27T20:15:00Z |
| **Detected Intent** | Feature |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | STANDARD | Well-scoped feature addition: 1 new endpoint + 1 schema + 1 controller method + 1 service method + tests. ~5 files changed, ~80 lines net new code. Reuses existing repository.update() infrastructure. |
| **Trust Level** | L2 | Established Express/TypeScript/Zod patterns in codebase. Schema-driven validation already proven. Existing PUT endpoint provides template. |
| **Bootstrap Lanes** | 3 | Parallel: schema + controller/service + route. Tests sequential on implementation. |
| **PDCA Max Cycles** | 2 | Implementation with test-driven verification. 2 cycles for fix-verify loops. |
| **Adversarial Reviewers** | 0 | Simple feature, well-trodden pattern. Tests + gate QA sufficient. |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal — verify PATCH partial-update semantics, empty-title rejection, no-op behavior |
| M2 test-pass | ✅ | Universal — new PATCH tests must pass |
| M3 regression | ✅ | Existing 92 tests (routes + repository + sanitize) must not break |
| M4 lint | ✅ | `.ts` files in diff (routes, controller, schema, service, types, tests) |
| M5 dead-code | ❌ | No deletions expected; net-new code only |
| S1 dataFlow | ✅ | New `PatchTaskDto` type + `patchTaskSchema` → controller.patch → service.patch → repository.update chain |
| S2 auth | ✅ | Route-level `auth(true)` already covers all task routes; verify PATCH inherits it |
| S3 injection | ✅ | New schema uses Zod `.transform(sanitizeText)` for title/description; repository queries are parameterized |
| P1 query | ❌ | Reuses existing `repository.update()` — already parameterized with `$N` placeholders |
| P2 memory | ❌ | No collection/buffer concerns |
| P3 latency | ❌ | No p95 target specified |

**Active gates (7/11):** M1, M2, M3, M4, S1, S2, S3

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | O2 |
| **Max Capability** | O4 (from capabilities.json — Playwright available) |
| **Browser Available?** | YES (O4 capable) |
| **Capped?** | O4 → O2 (API endpoint — browser E2E provides no additional signal over supertest integration tests) |
| **Fallback Strategy** | supertest integration tests with testcontainers PostgreSQL |
| **Residual Risk** | None. PATCH is a pure API concern; supertest covers all verification dimensions. |

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| Stage 1 | uncertainty_score < 30 | 3 |
| Stage 2 | 30 ≤ uncertainty < 60 | 5 |
| Stage 3 | uncertainty ≥ 60 | 7 |

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| No new evidence | 1 cycle with Δ=0 | Re-dispatch → plan re-eval → user |
| Same gate ×2 | Same gate fails twice | ESCALATE to user |
| Budget near limit | 80% of max cycles (1.6 → 2) | ESCALATE |
| Scope creep | New requirements beyond PATCH endpoint | Return to planner |
| Test failure cascade | >3 tests fail same gate | Halt, fix root cause |

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| FP-010 | P1 | Date.toISOString() drops microsecond digits in keyset pagination | 2026-06-27T12:00:00Z | 90 | **Not applicable** — PATCH reuses existing `repository.update()`, no pagination code touched. Skip. |

**Feed verdict**: No failure patterns match the `express-crud-patch` task area. FP-010 is in the same codebase but targets pagination cursor construction, untouched by this feature.

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (implementation)** | ~12K |
| **Tokens (testing + fix)** | ~8K |
| **Tokens (QA — 7 gates)** | ~8K |
| **Total estimated** | ~28K |
| **Est. cost (flash)** | $0.004 |
| **Est. cost (pro)** | $0.012 |
| **Est. cost (blended)** | ~$0.008 |
| **Historical ROI** | 0.78 score/token (feature area) |
| **Budget utilization** | ~56% of STANDARD mode budget |
| **Recommendation** | PROCEED |

## Technical Design Notes

### The "not provided" vs "provided-as-empty" distinction

This is the critical subtlety the user flagged. Here's how Zod + Express handles it:

| Client sends | `req.body.title` | Zod `.optional()` | Zod `.min(1)` | Result |
|---|---|---|---|---|
| `{}` | `undefined` | Accepts, field excluded from output | Skipped (field absent) | Keep existing |
| `{title: ""}` | `""` | Passes through (not undefined) | Rejects: "String must contain at least 1 character(s)" | **400** |
| `{title: "Hi"}` | `"Hi"` | Passes through | Accepts | Update title |

**Key insight**: Zod `.optional()` only accepts `undefined`. An empty string `""` is NOT `undefined`, so it flows through to `.min(1)` which rejects it. This gives us the exact behavior we need — no special-casing required.

### Schema design: `patchTaskSchema` vs `updateTaskSchema`

| Aspect | `updateTaskSchema` (PUT) | `patchTaskSchema` (PATCH) |
|---|---|---|
| All fields optional | ✅ | ✅ |
| `.refine()` requires ≥1 field | ✅ (`Object.keys(data).length > 0`) | ❌ (no-op PATCH is valid — return resource as-is) |
| Empty title rejected | ✅ (`.min(1)` catches `""`) | ✅ (same `.min(1)`) |
| Sanitize transform | ✅ (`.transform(sanitizeText)`) | ✅ (same transform) |

### No-op PATCH handling

Sending `PATCH /api/tasks/:id` with `{}` must return `200` with the unchanged resource.
- The repository's `update()` returns `null` when `setClauses.length === 0`
- The service MUST detect this case and return the existing task instead of throwing 404

**Resolution**: `TasksService.patch()` method:
1. Fetch task (404 check) → ownership check (403 check)
2. If no fields to update → return existing task immediately
3. Otherwise → delegate to `repository.update()` as normal

### Files to create/modify

| File | Action | Lines (est.) |
|---|---|---|
| `src/types/task.ts` | MODIFY | +4 (`PatchTaskDto` interface) |
| `src/schemas/task.schema.ts` | MODIFY | +12 (`patchTaskSchema` + type export) |
| `src/services/tasks.service.ts` | MODIFY | +14 (`patch()` method) |
| `src/controllers/tasks.controller.ts` | MODIFY | +8 (`patch` handler) |
| `src/routes/tasks.routes.ts` | MODIFY | +2 (PATCH route) |
| `__tests__/routes/tasks.routes.test.ts` | MODIFY | +65 (PATCH test suite: ~8 test cases) |

## Self-Audit Checklist

- [x] Mode selection matches task scale (STANDARD for 1-endpoint feature)
- [x] Gate selection based on actual diff signals (no deletions → M5/P1/P2/P3 skipped)
- [x] Observable level achievable (O2 via supertest — no browser needed for API)
- [x] Failure-pattern feed loaded — FP-010 unrelated, correctly skipped
- [x] Loop ROI history consulted — 0.78 feature ROI supports PROCEED
- [x] Escalation rules defined with concrete actions
- [x] Governance document written to `.omo/governor/`
- [x] No invented diff signals or failure patterns
- [x] Mode escalation justified by evidence (STANDARD, not over-orchestrated)
- [x] All downstream skills (plan/loop/qa) will honor governance decisions
- [ ] Governance document loaded by at least one downstream skill before execution ← **Phase 2 will verify**
- [ ] Skill-review scheduled for FULL/SIEGE modes ← **N/A (STANDARD mode)**
- [ ] Post-mortem review scheduled after pipeline completion ← **Phase 2 will handle**

## Phase 2 — Dispatch

```
# 1. Plan
run_skill({ name: "blackcow-plan", arguments: "Add PATCH /api/tasks/:id to Express CRUD — partial update, empty title rejection, no-op patch. --mode=STANDARD --govern=sim-express-crud-patch" })

# 2. Execute
run_skill({ name: "blackcow-loop", arguments: "Execute plans/sim-express-crud-patch.md --mode=STANDARD --trust-level=L2 --gates=M1,M2,M3,M4,S1,S2,S3" })

# 3. Verify
run_skill({ name: "blackcow-qa", arguments: "PATCH /api/tasks/:id — partial update, empty title rejection, no-op patch --gates=M1,M2,M3,M4,S1,S2,S3 --govern=sim-express-crud-patch" })
```
