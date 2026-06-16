# Plan: PATCH /api/tasks/:id — Partial Update Endpoint

| Field | Value |
|---|---|
| **Slug** | `sim-express-crud-patch` |
| **Created** | 2025-07-16 |
| **Class** | **M** (moderate — 4 files, ~250 net new lines, 3 layers touched) |
| **Explore lanes** | 10 dispatched, 10 returned |
| **Adversarial reviews** | 3/3 passed (M-scale: Reviewers A, B, C) |
| **Budget** | ~70K tokens / 115K effective |

---

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | PUT currently implements partial-update semantics under a full-replacement verb. Adding a proper PATCH endpoint provides REST-semantic correctness and a dedicated surface for partial-update edge cases (empty-title rejection vs. title-absent preservation). |
| **WHO** | API consumers (frontend apps, integration clients) that need to update individual task fields without sending the full resource. |
| **WHAT** | New `PATCH /api/tasks/:id` route, `patchTaskSchema` with pre-sanitize validation, `patch` controller handler. Reuses existing `TasksService.update()` and `TasksRepository.update()` (already partial-update capable). |
| **RISK** | Low. No existing behavior modified. New route, new schema — falls through to identical service/repo layers. Failure impact: isolated to PATCH endpoint; PUT/DELETE/GET unaffected. |
| **SUCCESS** | matchRate ≥ 90%, test pass=100%, lint=0warn, coverage ≥ 80%, p95_target_ms: N/A (reuses existing query path) |
| **SCOPE** | **Included:** `src/schemas/task.schema.ts` (new schema), `src/routes/tasks.routes.ts` (new route), `src/controllers/tasks.controller.ts` (new handler), `__tests__/routes/tasks.routes.test.ts` (new test suite). **Excluded:** `src/services/`, `src/repositories/`, `src/lib/` — no changes needed. |

---

## Summary

Add a `PATCH /api/tasks/:id` endpoint with true partial-update semantics. The existing repository (`TasksRepository.update`) already builds dynamic `SET` clauses from only the fields present in the DTO (`dto.title !== undefined` checks) — so the infrastructure is already partial-update ready. The work is: (1) create a `patchTaskSchema` that fixes a whitespace-title bypass bug by using `z.preprocess` to sanitize **before** `.min(1)` validation, (2) add the route wired through the existing middleware chain (`auth` → `validateParams` → `validateBody` → controller), (3) add a thin `patch` controller handler that delegates to `tasksService.update()`, and (4) write a comprehensive test suite covering the subtle "not provided vs. provided-as-empty" distinction.

---

## Architecture Options

### Option A — Minimal (PUT alias)
- **접근법**: Register PATCH as an alias of PUT — same route handler, same schema, no new code except one line in routes.
- **장점**: Zero risk, instant.
- **단점**: No whitespace-title fix, identical REST semantics for PUT/PATCH, no test coverage for PATCH-specific edge cases.
- **적합**: Only if the task is purely cosmetic ("add PATCH verb").
- **예상 파일 수**: 1 file, 1 line changed.

### Option B — Clean (Dedicated PATCH with schema fix + full tests)
- **접근법**: New `patchTaskSchema` using `z.preprocess` for title (sanitize-before-validate pattern), new controller, new route, exhaustive test suite.
- **장점**: Fixes whitespace-title bypass, REST-semantic correctness, full edge-case coverage, forward-proof (PUT and PATCH schemas can diverge).
- **단점**: More code, but contained to 4 files.
- **적합**: Production-quality API that cares about HTTP semantics.
- **예상 파일 수**: 4 files, ~200 net new lines.

### Option C — Pragmatic (권장)
- **접근법**: Same as Option B, but reuse the existing `updateTaskSchema` name-space (export both `updateTaskSchema` AND `patchTaskSchema` from `task.schema.ts`, where `patchTaskSchema` is the fixed version and `updateTaskSchema` is unchanged for backward compatibility). No service/repo changes.
- **장점**: Balanced — fixes the bug for PATCH, keeps PUT unchanged (no regression risk), full test coverage, REST-semantic correctness.
- **적합**: **This is the recommendation.** The task explicitly calls out "the distinction between 'not provided' vs 'provided-as-empty' is subtle and easy to get wrong" — this approach proves correctness through tests.

### 권장: Option C (Pragmatic)
**사유**: The existing `updateTaskSchema` has a documented whitespace-title bypass (Lane 3 + Lane 6 confirmed: `"   "` passes `.min(1)`, then `sanitizeText` trims to `""`, stored as empty). Fixing this in `patchTaskSchema` via `z.preprocess` is the right place — it establishes the correct pattern for the semantically-correct verb without risking PUT regression. All other layers (service, repository) are already correct.

---

## Codebase Survey (10-Lane Summary)

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| **L1 Surface** | Clean 5-layer architecture: Interface (routes/controllers) → Application (services) → Domain (types/errors) → Infrastructure (repos/lib/db) → DB. No barrel files. | `src/routes/` → `src/controllers/` → `src/services/` → `src/repositories/` + `src/lib/db/` | — |
| **L2 Call Graph** | PUT flow: `auth → validateParams → validateBody → controller.update → service.update → repo.findById(→404/403) → repo.update → DB`. Service does redundant `findById` before `update` (double query — L9). Repository `update()` correctly builds dynamic SET from `dto.field !== undefined`. | `src/services/tasks.service.ts:20-33`, `src/repositories/tasks.repository.ts:101-119` | S1 |
| **L3 Data Shapes** | ⚠️ **Whitespace-title bypass**: `"   "` passes `.min(1)` (length 3), `sanitizeText` trims to `""`, transform `v ? sanitizeText(v) : v` returns `""` (falsy). Repository writes `""` to DB. Also: `"<script>"` stripped to `""` same path. `.optional()` correctly handles absent vs. present. | `src/schemas/task.schema.ts:22-23`, `src/lib/sanitize.ts:17-34` | S1 (dataFlow integrity) |
| **L4 Tests** | 47 test cases in Jest+supertest+testcontainers. No PATCH tests exist. No empty-title-on-PUT test. No skipped/disabled tests. CI: `jest --forceExit --detectOpenHandles`. | `__tests__/routes/tasks.routes.test.ts` (25-476) | M2, M3 |
| **L5 Config** | `tsconfig strict:true`, `exactOptionalPropertyTypes:false` (allows `dto.title !== undefined` pattern). ESLint skips `__tests__/`. Jest coverage threshold ≥60%. | `tsconfig.json`, `jest.config.ts`, `.eslintrc.json` | — |
| **L6 Deps** | Zod 4.4.3. Express 5.2.1. `z.preprocess` available in Zod 4. Express 5 `router.patch()` supported. All deps compatible. | `package.json`, runtime verification | — |
| **L7 Git** | `src/` is gitignored — no git history on target files. Zero TODO/FIXME/HACK in codebase. Clean single-author style. | `.gitignore:30`, search across all `.ts` files | — |
| **L8 Security** | `z.object()` strips unknown keys (no mass assignment). Parameterized queries prevent SQL injection. `sanitizeText` strip+escape for XSS. Auth at router level (`taskRoutes.use(auth(true))`) automatically covers new PATCH route. Ownership enforced at repo `WHERE user_id = $N`. | `src/middleware/validate.ts:9`, `src/repositories/tasks.repository.ts:85,131-159`, `src/routes/tasks.routes.ts:8` | S2, S3 |
| **L9 Performance** | Service `update()` does redundant `findById` SELECT before `repository.update()` UPDATE — double query on every PATCH/PUT. Repository `update()` correctly builds minimal SET (only changed columns). Not blocking; documented for future optimization. | `src/services/tasks.service.ts:24-33`, `src/repositories/tasks.repository.ts:101-119` | P1 |
| **L10 Patterns** | Consistent pattern across all CRUD: `route.verb(path, ...middleware, controller.handler)` → controller extracts `req.params`/`req.body`/`req.user!.sub`, calls service, calls `success()`/`created()` with `taskToResponse()`. Service: `findById` → validate → `repo.operation` → return. PATCH follows this exactly. | `src/routes/tasks.routes.ts:14-18`, `src/controllers/tasks.controller.ts:36-42`, `src/services/tasks.service.ts:18-33` | M1 |

---

## Gap Matrix

| Cat | Item | Evidence | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| ✅ **Reuse** | `TasksRepository.update()` — already handles partial updates via `dto.field !== undefined` | `src/repositories/tasks.repository.ts:101-119` | HIGH | — | — |
| ✅ **Reuse** | `TasksService.update()` — existence check + ownership validation + delegate to repo | `src/services/tasks.service.ts:18-33` | HIGH | — | — |
| ✅ **Reuse** | `taskIdSchema` — UUID param validation | `src/schemas/task.schema.ts:63-65` | HIGH | — | S3 |
| ✅ **Reuse** | `validateParams`, `validateBody` middleware | `src/middleware/validate.ts:22-23` | HIGH | — | S3 |
| ✅ **Reuse** | `auth(true)` — route-level JWT enforcement | `src/routes/tasks.routes.ts:8` | HIGH | — | S2 |
| ✅ **Reuse** | `taskToResponse`, `success` — response formatting | `src/lib/response.ts:5-13,17-20` | HIGH | — | — |
| 🔧 **Modify** | `src/schemas/task.schema.ts` — add `patchTaskSchema` with `z.preprocess` title fix | New schema, ~25 lines | HIGH | LOW | M3 (regression risk on shared imports) |
| 🔧 **Modify** | `src/routes/tasks.routes.ts` — add PATCH route | New route line | HIGH | LOW | — |
| 🔧 **Modify** | `src/controllers/tasks.controller.ts` — add `patch` handler | New exported function, ~10 lines | HIGH | LOW | M2 |
| 🆕 **Build** | `__tests__/routes/tasks.routes.test.ts` — PATCH test suite | New describe block, ~120 lines | — | — | M1, M2, S1 |
| 🗑️ **Delete** | Nothing to delete | — | — | — | M5 |

---

## Waves

### Wave 1 — Foundation (3 tasks, parallel, ≤35K tokens)

- [ ] **w1-schema**: Create `patchTaskSchema` in `src/schemas/task.schema.ts`
  - **Worker:** `mini`
  - **Token est:** ~5K
  - **Action:** Add `patchTaskSchema` after `updateTaskSchema` (line ~30). Uses `z.preprocess(sanitizeText, z.string().min(1).max(200).optional())` for title — sanitizes BEFORE `.min(1)` validation, catching whitespace and script-tag inputs that collapse to empty. Other fields (`description`, `status`, `priority`, `due_date`) identical to `updateTaskSchema`. Include `.refine(data => Object.keys(data).length > 0)` for empty-body rejection. Export the schema.
  - **Verify:** `npx tsc --noEmit` — zero type errors.
  - **Gate:** M3 (no regression on existing schemas), S3 (input validation)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-patch-w1-schema.txt`

  ```typescript
  // Key design — z.preprocess shifts sanitization BEFORE validation:
  //   "   " → preprocess(trim) → "" → .min(1) rejects → 400 ✅
  //   absent → preprocess(undefined) → undefined → .optional() → field omitted ✅
  //   "hello" → preprocess → "hello" → passes → in output ✅
  export const patchTaskSchema = z.object({
    title: z.preprocess(
      sanitizeText,
      z.string().min(1, 'Title must not be empty').max(200, 'Title must be 200 characters or less').optional(),
    ),
    description: z.string().max(5000, 'Description must be 5000 characters or less').optional()
      .transform((v) => v ? sanitizeText(v) : v),
    status: taskStatusEnum.optional(),
    priority: taskPriorityEnum.optional(),
    due_date: z.string().datetime({ message: 'Invalid ISO 8601 date' }).optional(),
  }).refine((data) => Object.keys(data).length > 0, {
    message: 'At least one field must be provided for update',
  });
  ```

- [ ] **w1-controller**: Add `patch` handler in `src/controllers/tasks.controller.ts`
  - **Worker:** `mini`
  - **Token est:** ~2K
  - **Action:** Add `patch` export after `update` (line ~43). Identical shape to `update` handler: extract `req.params.id`, `req.body` (as `UpdateTaskDto` — compatible type), `req.user!.sub`, call `tasksService.update(id, userId, dto)`, respond with `success(res, taskToResponse(task))`. Wrapped in `asyncHandler`.
  - **Verify:** `npx tsc --noEmit` — zero type errors. `UpdateTaskDto` type compatibility confirmed (both schemas produce same shape).
  - **Gate:** M1 (spec-match — delegate to correct service method)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-patch-w1-controller.txt`

- [ ] **w1-route**: Add PATCH route in `src/routes/tasks.routes.ts`
  - **Worker:** `mini`
  - **Token est:** ~1K
  - **Action:** Add `taskRoutes.patch('/:id', validateParams(taskIdSchema), validateBody(patchTaskSchema), controller.patch);` after the PUT route (line ~18). Import `patchTaskSchema` from `'../schemas/task.schema'` (add to existing import). Add `patch` to controller import.
  - **Verify:** `npx tsc --noEmit` — zero type errors. Route order: PATCH /:id must come BEFORE DELETE /bulk AND DELETE /:id (Express resolves first-match for literal paths, but `:id` is a param — same priority as PUT, order among them doesn't matter as long as `/bulk` stays above `/:id`).
  - **Gate:** S2 (auth — inherits `taskRoutes.use(auth(true))` at line 8)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-patch-w1-route.txt`

### Wave 2 — Core: Tests (serial on Wave 1, ≤30K tokens)

- [ ] **w2-tests**: Add PATCH test suite in `__tests__/routes/tasks.routes.test.ts`
  - **Worker:** `heavy`
  - **Token est:** ~25K
  - **Action:** Add `describe('PATCH /api/tasks/:id — Partial Update', ...)` block after the existing `M1 — CRUD` block. Tests:

    | # | Test | Request | Expected | Gate |
    |---|------|---------|----------|------|
    | 1 | Partial update — title only | `PATCH {title:"New Title"}` | 200, title="New Title", other fields unchanged | M1 |
    | 2 | Partial update — description only | `PATCH {description:"New desc"}` | 200, description="New desc", title unchanged | M1 |
    | 3 | Partial update — multiple fields | `PATCH {title:"X", status:"done"}` | 200, both updated, others unchanged | M1 |
    | 4 | **Empty title → 400** | `PATCH {title:""}` | 400, error contains "Title must not be empty" | S3 |
    | 5 | **Whitespace-only title → 400** | `PATCH {title:"   "}` | 400 (preprocess trim → "" → .min(1) rejects) | S3 |
    | 6 | **Script-tag title → 400** | `PATCH {title:"<script>alert(1)</script>"}` | 400 (preprocess strips → "" → .min(1) rejects) | S3 |
    | 7 | **Title NOT provided → keep existing** | `PATCH {description:"only desc"}` | 200, title preserved from original | M1 |
    | 8 | No-op patch (same values) | `PATCH {title:"<same as current>"}` | 200, data unchanged | M1 |
    | 9 | Invalid status enum | `PATCH {status:"invalid"}` | 400, validation error | S3 |
    | 10 | Empty body → 400 | `PATCH {}` | 400, "At least one field must be provided" | S3 |
    | 11 | Non-existent task → 404 | `PATCH <random-uuid> {title:"x"}` | 404 | M1 |
    | 12 | Other user's task → 404 | `PATCH <other-user-task> {title:"x"}` with other user's token | 404 (ownership hidden) | S2 |
    | 13 | XSS — HTML tags stripped from title | `PATCH {title:"<b>Bold</b>"}` | 200, title="Bold" | S1 |
    | 14 | XSS — script stripped from description | `PATCH {description:"<script>x</script>"}` | 200, description="x" | S1 |

  - **Verify:** `npm test -- --testPathPattern="tasks.routes"` — all 14 new tests pass + all 47 existing tests pass (61 total, zero regressions).
  - **Gate:** M2 (test pass=100%), M3 (zero regressions), S1 (dataFlow integrity — title not corrupted by sanitization)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-patch-w2-tests.txt`

### Wave 3 — Hardening (serial on Wave 2, ≤10K tokens)

- [ ] **w3-lint**: Run lint and format checks
  - **Worker:** `mini`
  - **Token est:** ~1K
  - **Action:** `npm run lint` and `npm run format:check`
  - **Verify:** Zero warnings, zero format violations.
  - **Gate:** M4 (lint-clean = 0 warnings)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-patch-w3-lint.txt`

- [ ] **w3-coverage**: Verify coverage thresholds
  - **Worker:** `mini`
  - **Token est:** ~1K
  - **Action:** `npm run test:coverage` — confirm branches/functions/lines/statements ≥ 60% (jest.config.ts threshold). The new PATCH path exercises the existing `service.update()` and `repository.update()` code paths, so coverage should increase.
  - **Verify:** Coverage report shows no drop below thresholds.
  - **Gate:** M2 (coverage ≥ 80% target for new code paths)
  - **Evidence:** `.omo/ulw-loop/evidence/sim-express-crud-patch-w3-coverage.txt`

---

## Risk Register (BKIT 11-Gate)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| Whitespace-title bypass in existing PUT | `S1_dataFlow` | MED | No regression | Not fixed in `updateTaskSchema` (backward compat); fixed in new `patchTaskSchema` via `z.preprocess` | Test #5 (whitespace → 400) |
| Script-tag-title collapses to empty → stored | `S1_dataFlow` | MED | No regression | Same — fixed in `patchTaskSchema`, not in PUT | Test #6 (script-tag → 400) |
| PATCH breaks existing PUT behavior | `M3_regression` | HIGH | 0 regressions | Separate schema (`patchTaskSchema` vs `updateTaskSchema`). No shared mutation. PUT unchanged. | Full test suite: 47 existing + 14 new = 61 passing |
| PATCH forgets auth middleware | `S2_auth` | LOW | All routes protected | Auth applied at router level (`taskRoutes.use(auth(true))`) — any new route on `taskRoutes` inherits it automatically. | Test #12 (other user → 404) |
| Unknown fields injected via PATCH body | `S3_injection` | LOW | No unknown keys reach repo | `z.object()` defaults to `.strip()` — unknown keys silently removed during `schema.parse()`. | Test #9 (invalid enum → 400 confirms Zod validation runs) |
| Double query on every PATCH (findById + update) | `P1_query` | LOW | Acceptable for now | Existing pattern in `TasksService.update()`. Not introduced by this change. Documented for future optimization. | Manual inspection |
| Title-not-provided vs title-empty confusion | `M1_spec_match` | HIGH | matchRate ≥ 90% | `z.preprocess` + `.optional()` guarantees: absent→undefined (keep), ""→reject (400). Test suite covers both paths. | Tests #4 (""→400) + #7 (absent→keep) |
| Dead code from unused imports | `M5_dead_code` | LOW | 0 unused exports | `patchTaskSchema` is exported and imported by routes. `patch` controller is exported and imported by routes. | `npx tsc --noEmit` + ESLint `no-unused-vars` |

---

## Design Note: `z.preprocess` vs `.transform()` for Title

The critical design decision in `patchTaskSchema`:

```
CURRENT (updateTaskSchema) — VALIDATE then SANITIZE:
  z.string().min(1) → .transform(sanitizeText)
  "   " passes .min(1) (length 3) → trim to "" → stored as ""  ← BUG

NEW (patchTaskSchema) — SANITIZE then VALIDATE:
  z.preprocess(sanitizeText, z.string().min(1))
  "   " → trim to "" → .min(1) rejects → 400  ← CORRECT
```

`z.preprocess` runs the sanitizer BEFORE Zod validation. This ensures `.min(1)` operates on the sanitized (trimmed, stripped) value, catching all inputs that collapse to empty. The `undefined` case is handled naturally: `sanitizeText(undefined)` returns `undefined`, `.optional()` allows absence.

For `description`, the existing `.transform()` pattern is kept because: (1) description has no `.min(1)` constraint — empty descriptions are allowed, (2) the transform correctly handles empty strings (falsy → passthrough).

---

## Execution Command

```
blackcow-loop "Execute plans/sim-express-crud-patch.md" --completion-promise='PATCH /api/tasks/:id accepts partial updates, rejects empty/whitespace titles with 400, preserves missing fields, all 14 new tests + 47 existing tests pass, lint=0warn, coverage≥80%' --trust-level=2
```

### Parallelism Guide
- Wave 1: dispatch 3 workers in parallel (schema, controller, route are independent)
- Wave 2: 1 heavy worker (tests — serial on Wave 1 completion)
- Wave 3: dispatch 2 workers in parallel (lint + coverage — serial on Wave 2)
- Total budget: ~70K / 115K tokens
