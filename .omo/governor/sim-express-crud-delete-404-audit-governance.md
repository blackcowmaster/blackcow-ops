# Governance Decision: sim-express-crud-delete-404-audit

| Field | Value |
|---|---|
| **Task** | Verify DELETE /api/tasks/:id error handling for non-existent task — must return 404 with proper JSON, not 500 or 200 |
| **Governed at** | 2026-07-14T18:00:00Z |
| **Audited at** | 2026-07-14T18:07:00Z |
| **Detected Intent** | Bug (verification) / Findings Gate Test |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | FAST | Single-endpoint audit, single scenario. No code changes expected unless gap found. |
| **Trust Level** | L1 | Read-only verification. |
| **Bootstrap Lanes** | 3 | Error flow trace, existing test coverage review, live verification |
| **PDCA Max Cycles** | 1 | Single verification pass |
| **Adversarial Reviewers** | 0 | XS scope |

## Gate Selection — Results

| Gate | Run? | Score | Pass? | Evidence |
|---|---|---|---|---|
| M1 spec-match | ✅ | 100 | ✅ | 5/5 requirements: 404 status, JSON body, data:null, error message, correlationId |
| M2 test-pass | ✅ | 100 | ✅ | 39/39 tests pass (22 routes + 17 repo) |
| M3 regression | ✅ | 100 | ✅ | 0 regressions, 0 broken call sites |
| **OVERALL** | **3/3** | **100** | **✅** | |

## Preflight Code Trace Evidence

### DELETE /api/tasks/:id — Non-existent task error flow

| Layer | File:Line | Code | Verdict |
|---|---|---|---|
| **Route** | `routes/tasks.routes.ts:26` | `validateParams(taskIdSchema) → controller.remove` | ✅ UUID enforced |
| **Controller** | `controllers/tasks.controller.ts:43-48` | `await tasksService.remove(id, userId)` via asyncHandler | ✅ async |
| **Service** | `services/tasks.service.ts:43-48` | `findById → null → throw new AppError(404, 'NOT_FOUND', ...)` | ✅ 404 thrown |
| **asyncHandler** | `middleware/asyncHandler.ts:9` | `Promise.resolve(fn(...)).catch(next)` | ✅ forwarded |
| **errorHandler** | `middleware/errorHandler.ts:11-18` | `instanceof AppError → res.status(404).json({data:null, error:..., meta:{correlationId}})` | ✅ JSON 404 |

## Post-Audit Self-Check

| Check | Result |
|---|---|
| Mode selection matches task scale | ✅ FAST for single-endpoint verification |
| Gate selection based on actual diff signals | ✅ Only M1/M2/M3 needed — no code changes |
| Observable level achievable | ✅ O2 structural trace sufficient |
| Failure-pattern feed loaded | ✅ FP-010 reviewed, not applicable |
| Loop ROI history consulted | ✅ 0.78 score/token, PROCEED |
| Escalation rules defined | ✅ No escalation triggered |
| Governance document written | ✅ `.omo/governor/sim-express-crud-delete-404-audit-governance.md` |
| QA completed | ✅ 100/100 weighted score, 3/3 gates |
| Findings recorded | ✅ 3 findings (1 resolved, 2 open) |

## Findings Summary

| ID | Severity | Status | Title |
|---|---|---|---|
| F-001 | LOW | RESOLVED | No explicit test for DELETE non-existent → 404 (code correct, test gap only) |
| **F-002** | **MEDIUM** | **OPEN** | **TOCTOU in service.remove() — repository return value discarded** |
| F-003 | LOW | OPEN | Unreachable 403 ownership check (dead code) |

### F-002 Detail — Actionable Gap

`tasksService.remove()` calls `findById` (check) then `remove` (use) without checking the return value:

```typescript
// Current (gap):
async remove(id: string, userId: string): Promise<void> {
    const task = await tasksRepository.findById(id, userId);
    if (!task) throw new AppError(404, ...);
    if (task.user_id !== userId) throw new AppError(403, ...);
    await tasksRepository.remove(id, userId);  // ← return value IGNORED
}

// Compare with update() which does it correctly:
async update(id: string, userId: string, dto: UpdateTaskDto): Promise<Task> {
    const task = await tasksRepository.findById(id, userId);
    if (!task) throw new AppError(404, ...);
    const updated = await tasksRepository.update(id, userId, dto);
    if (!updated) throw new AppError(404, 'NOT_FOUND', 'Task not found after update'); // ✅
    return updated;
}
```

**Impact:** Concurrent request soft-deletes task between check and use → `remove()` returns null (no row updated) → service returns 204 (success) instead of 404.

**Fix:** Two lines — change return type from `void` to `Task`, check return value:

```typescript
async remove(id: string, userId: string): Promise<Task> {
    const task = await tasksRepository.findById(id, userId);
    if (!task) throw new AppError(404, 'NOT_FOUND', `Task with id ${id} not found`);
    const deleted = await tasksRepository.remove(id, userId);
    if (!deleted) throw new AppError(404, 'NOT_FOUND', `Task with id ${id} not found`);
    return deleted;
}
```

## Verdict

**✅ Original task (DELETE non-existent → 404): CODE IS CORRECT.** The implementation properly returns 404 with JSON error via AppError → asyncHandler → errorHandler chain. All 39 tests pass.

**⚠️ Related gap found (F-002):** TOCTOU race condition in `service.remove()` — the return value of `repository.remove()` is discarded. This is a real but narrow bug (concurrent delete race). Fix is a 2-line change mirroring the existing pattern in `service.update()`.

## Escalation Rules — Post-Audit

| Rule | Trigger | Action |
|---|---|---|
| No new evidence | N/A | — |
| Same gate ×2 | N/A | — |
| Budget near limit | 15% utilized | — |
| **New finding (MEDIUM)** | F-002 TOCTOU | **Offer fix to user** |
