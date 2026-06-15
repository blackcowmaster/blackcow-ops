# Governance Decision: sql-pattern-audit

| Field | Value |
|---|---|
| **Task** | Analyze the Express CRUD app (`sim-express-crud`) for SQL query patterns. Tech stack: TypeScript/PostgreSQL/Express. Analysis only — no code changes. |
| **Governed at** | 2026-07-14T22:00:00Z |
| **Detected Intent** | Quality (code audit / pattern survey) |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | FAST | Read-only analysis. No code mutation, no test execution, no adversarial review needed. Single-lane discovery sufficient. STANDARD would add unnecessary plan/review overhead. |
| **Trust Level** | L0 | Read-only survey. No guardrails needed. |
| **Bootstrap Lanes** | 1 | Single lane: `src/repositories/tasks.repository.ts` + migration + pool — all SQL lives here. |
| **PDCA Max Cycles** | 0 | No implementation — nothing to iterate. |
| **Adversarial Reviewers** | 0 | Analysis artifact, no code changes to review. |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal (analysis quality) |
| M2 test-pass | ❌ | No code changes — no tests to run |
| M3 regression | ❌ | No code changes — no regression surface |
| M4 lint | ❌ | No source files in diff |
| M5 dead-code | ❌ | No deletions |
| S1 dataFlow | ✅ | SQL query structure IS the data flow for this analysis |
| S2 auth | ❌ | Auth not relevant to SQL pattern survey |
| S3 injection | ✅ | SQL injection assessment is core to this analysis |
| P1 query | ✅ | Primary gate — SQL query performance patterns |
| P2 memory | ❌ | No collection/buffer concerns |
| P3 latency | ❌ | No p95 target; static analysis only |

**Active gates (4/11):** M1, S1, S3, P1

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | O0 |
| **Max Capability** | O4 (from capabilities.json) |
| **Browser Available?** | YES |
| **Capped?** | O0 (by choice — static analysis only, no runtime verification needed) |
| **Fallback Strategy** | N/A — all verification is source-level |
| **Residual Risk** | None. Static analysis covers all 4 active gates. No runtime behavior to miss. |

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| Stage 1 | uncertainty_score < 30 | 1 |
| Stage 2 | 30 ≤ uncertainty < 60 | 1 |
| Stage 3 | uncertainty ≥ 60 | 1 |

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| No new evidence | 1 cycle with Δ=0 | N/A — no PDCA cycles |
| Same gate ×2 | Same gate fails twice | ESCALATE to user |
| Budget near limit | 80% of max cycles | N/A — no PDCA cycles |
| Scope creep | D2 flags scope change | Return to planner |

## Failure-Pattern Feed

### Context-Tag Filtering Verification

The user explicitly requested verification that `context_tags` filtering distinguishes FP-010 (database/postgresql) from FP-001~FP-004 (tools-mapping/bash).

**Filter: `task_area == "database" AND context_tags CONTAINS "postgresql"`**

| Pattern ID | Gate | task_area | context_tags | Match? | Rationale |
|---|---|---|---|---|---|
| FP-001 | M3 | tools-mapping | *(absent)* | ❌ | `task_area` ≠ database. No context_tags field. |
| FP-002 | M3 | tools-mapping | *(absent)* | ❌ | `task_area` ≠ database. No context_tags field. |
| FP-003 | M3 | tools-mapping | *(absent)* | ❌ | `task_area` ≠ database. No context_tags field. |
| FP-004 | M3 | tools-mapping | *(absent)* | ❌ | `task_area` ≠ database. No context_tags field. |
| **FP-010** | **P1** | **database** | **["typescript","postgresql","express"]** | ✅ | All filter criteria match. |

**Filtering verdict: CORRECT.** Simple two-field filter (`task_area` + `context_tags`) cleanly separates FP-010 (database, postgresql, express) from FP-001~FP-004 (tools-mapping, bash). No false positives, no false negatives.

### Matched Failure Pattern (FP-010)

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| FP-010 | P1 | `Date.toISOString()` drops microsecond digits, causing PostgreSQL keyset cursor pagination to silently exclude rows with identical timestamps | 2026-06-27T12:00:00Z | 90 | **Already fixed in codebase.** Fix verified below. |

**FP-010 Fix verification in current code (`src/repositories/tasks.repository.ts`):**
- ✅ Cursor construction uses PostgreSQL-native: `t.created_at::text \|\| '_' \|\| t.id::text as _cursor` (line 57) — NOT `Date.toISOString()`
- ✅ Cursor parsing uses `lastIndexOf('_')` (line 31) — safe delimiter strategy
- ✅ Directional comparison uses PostgreSQL row comparison: `(t.created_at, t.id) < (> ) ($X::timestamptz, $Y::uuid)` (line 35) — preserves microsecond precision
- **Verdict: FP-010 fix is correctly applied and intact.**

**Feed rules:**
- `effectiveness ≥ 80` → apply known fix automatically before PDCA
- `effectiveness 40-79` → suggest fix, require confirmation
- `effectiveness < 40` → escalate gate priority, do NOT auto-apply (fix unreliable)
- `reappeared_after_fix: true` → mark pattern as CRITICAL, require architectural review

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (discovery)** | ~8K |
| **Tokens (analysis)** | ~5K |
| **Tokens (governance doc)** | ~3K |
| **Total estimated** | ~16K |
| **Est. cost (flash)** | $0.002 |
| **Est. cost (pro)** | $0.007 |
| **Est. cost (blended)** | ~$0.005 |
| **Historical ROI** | 0.78 score/token (feature area) |
| **Budget utilization** | ~30% of FAST mode budget |
| **Recommendation** | PROCEED |

---

# SQL Query Pattern Analysis — Express CRUD App

## Scope

All SQL lives in two files:
- **`src/repositories/tasks.repository.ts`** — 204 lines, 6 methods, all application SQL
- **`src/lib/db/migrations/001_create_tasks.sql`** — 47 lines, DDL + indexes + trigger

## Pattern Catalog

### Pattern 1: Universal Parameterized Queries (`$N` binding)

**Every query** uses `$1, $2, …$N` positional parameters via `pg.Pool.query()`. Zero instances of string concatenation, template literal injection, or dynamic SQL construction with user values.

```sql
-- findById: 2 params
SELECT * FROM tasks WHERE id = $1 AND user_id = $2 AND deleted_at IS NULL

-- create: 6 params  
INSERT INTO tasks (user_id, title, description, status, priority, due_date)
VALUES ($1, $2, $3, $4, $5, $6) RETURNING *

-- remove: 2 params
UPDATE tasks SET deleted_at = NOW() WHERE id = $1 AND user_id = $2 AND deleted_at IS NULL
  RETURNING *
```

**Verdict (S3): PASS.** SQL injection surface = 0. All user input flows through pg parameterized binding. Verified by `grep` in prior QA run: `grep -rn '\${' src/repositories/` → only `$${paramIdx++}` (JavaScript param counter, not SQL interpolation).

---

### Pattern 2: Keyset Cursor Pagination (FP-010 Fixed)

The `findAll()` method supports two pagination modes:

#### Cursor Mode (primary)
```sql
-- Cursor construction: PostgreSQL-native — preserves microsecond precision
SELECT t.*, t.created_at::text || '_' || t.id::text as _cursor
FROM tasks t
WHERE t.user_id = $1 AND t.deleted_at IS NULL
  AND (t.created_at, t.id) > ($2::timestamptz, $3::uuid)  -- directional
ORDER BY t.created_at ASC, t.id ASC
LIMIT $4
```

- Cursor built in SQL, not JS → avoids `Date.toISOString()` precision loss (FP-010)
- Row-value comparison `(created_at, id) < (…)` is index-friendly
- Composite index `idx_tasks_created_at_id` supports this exact sort order
- Cursor parsing: `lastIndexOf('_')` — safe because neither `timestamptz::text` nor `uuid::text` contains `_`

#### Offset Mode (fallback)
```sql
SELECT t.* FROM tasks t
WHERE t.user_id = $1 AND t.deleted_at IS NULL
ORDER BY t.created_at DESC, t.id DESC
LIMIT $2 OFFSET $3
```
- Classic offset pattern. Works but degrades at high offsets.
- Available as fallback; cursor mode is the default.

**Verdict (P1): PASS.** Pagination architecture is sound. Cursor mode has proper index backing and avoids the JS precision bug.

---

### Pattern 3: Soft-Delete via `deleted_at`

```sql
-- Filtered on every read
WHERE t.deleted_at IS NULL

-- Soft-delete — never actually removes rows
UPDATE tasks SET deleted_at = NOW()
WHERE id = $1 AND user_id = $2 AND deleted_at IS NULL
RETURNING *
```

- No `DELETE FROM` anywhere in the codebase
- `deleted_at IS NULL` filter is on every SELECT query (findAll, findById)
- Partial indexes use `WHERE deleted_at IS NULL` for efficiency

**Verdict (S1): PASS.** Data integrity preserved. Accidental hard-deletes impossible.

---

### Pattern 4: Dynamic WHERE Clause Building

`findAll()` builds the WHERE clause programmatically with optional filters:

```typescript
const conditions: string[] = ['t.user_id = $1', 't.deleted_at IS NULL'];
const params: unknown[] = [userId];
let paramIdx = 2;

if (pq.status) {
  conditions.push(`t.status = $${paramIdx++}`);
  params.push(pq.status);
}
if (pq.priority) {
  conditions.push(`t.priority = $${paramIdx++}`);
  params.push(pq.priority);
}
```

- Incremental `$N` numbering via `paramIdx` counter → always sequential
- No string interpolation of user values into SQL
- Condition list always starts with mandatory filters (user_id + soft-delete)
- When running COUNT query, params are sliced: `params.slice(0, whereParamCount)` to exclude pagination params

**Verdict (S3): PASS.** Dynamic SQL construction is safe — only column names and operators are hardcoded; all values go through the params array.

---

### Pattern 5: Dynamic SET Clause for UPDATE

```typescript
const setClauses: string[] = [];
if (dto.title !== undefined) {
  setClauses.push(`title = $${paramIdx++}`);
  params.push(dto.title);
}
// ... one branch per updatable field

const sql = `
  UPDATE tasks
  SET ${setClauses.join(', ')}
  WHERE id = $${paramIdx++} AND user_id = $${paramIdx++} AND deleted_at IS NULL
  RETURNING *
`;
```

- Only sets columns that are actually provided in the DTO
- Param numbering is sequential across SET and WHERE clauses
- Empty update (no fields provided) returns `null` — handled by service layer
- Uses `RETURNING *` to return the full updated row

**Verdict (S3/P1): PASS.** No risk of overwriting unmentioned columns with NULL. Efficient — only modified columns are touched.

---

### Pattern 6: Parallel COUNT + SELECT

```typescript
const [result, countResult] = await Promise.all([
  query(selectSql, params),
  query(countSql, params.slice(0, whereParamCount)),
]);
```

- Two queries run in parallel via `Promise.all()`
- COUNT uses a smaller param slice (no pagination params)
- Eliminates sequential round-trip latency
- Results joined: `{ tasks, total, nextCursor }`

**Verdict (P1): PASS.** Efficient use of connection pool. No N+1 problem.

---

### Pattern 7: Bulk INSERT with Batch Cap

```typescript
async bulkCreate(dtos: CreateTaskDto[], userId: string): Promise<Task[]> {
  if (dtos.length > 500) throw new Error('Batch size exceeds maximum of 500');
  if (dtos.length === 0) return [];

  // Build: VALUES ($1,$2,$3,$4,$5,$6), ($7,$8,$9,$10,$11,$12), ...
  const sql = `
    INSERT INTO tasks (user_id, title, description, status, priority, due_date)
    VALUES ${values.join(', ')}
    RETURNING *
  `;
}
```

- Multi-row INSERT in a single round-trip
- Hard cap at 500 rows (enforced before query construction)
- All values parameterized with sequential `$N`
- Returns all inserted rows via `RETURNING *`

**Verdict (P1): PASS.** Batch size cap prevents oversized queries. Single round-trip for bulk operations.

---

### Pattern 8: Transaction Helper

```typescript
async transaction<T>(fn: (client) => Promise<T>): Promise<T> {
  const client = await getClient();
  try {
    await client.query('BEGIN');
    const result = await fn(client);
    await client.query('COMMIT');
    return result;
  } catch (err) {
    await client.query('ROLLBACK');
    throw err;
  } finally {
    client.release();
  }
}
```

- Standard BEGIN/COMMIT/ROLLBACK pattern
- Client released in `finally` → no connection leaks on error
- Generic type `T` preserves return type through transaction
- Currently unused in service layer but available for multi-statement operations

**Verdict (P1): PASS.** Transaction primitive is correct. Connection lifecycle is safe.

---

### Pattern 9: Pool Configuration (P1)

```typescript
{
  connectionString: process.env.DATABASE_URL,
  max: 10,                        // connection pool cap
  idleTimeoutMillis: 30000,       // close idle after 30s
  connectionTimeoutMillis: 5000,  // fail fast on connect (5s)
  statement_timeout: 30000,       // kill queries > 30s
}
pool.on('error', (err) => console.error('[pg pool] Unexpected error on idle client:', err.message));
```

- Pool size 10 — reasonable for Express CRUD
- Statement timeout 30s prevents runaway queries
- Idle timeout 30s prevents stale connections
- Error handler prevents unhandled pool errors from crashing the process

---

### Pattern 10: Slow Query Logging

```typescript
const duration = Date.now() - start;
if (duration > 1000) {
  console.warn(`[pg] Slow query (${duration}ms): ${text.substring(0, 200)}`);
}
```

- Every query is timed
- Queries >1s logged with first 200 chars of SQL
- No PII leakage (params not logged)

**Verdict (P1): PASS.** Basic observability without data leakage.

---

### Pattern 11: Schema Design (DDL)

```sql
-- ENUM types (safe creation with IF NOT EXISTS pattern)
DO $$ BEGIN CREATE TYPE task_status AS ENUM ('todo', 'in_progress', 'done');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Composite index for keyset pagination
CREATE INDEX IF NOT EXISTS idx_tasks_created_at_id
  ON tasks(created_at DESC, id DESC) WHERE deleted_at IS NULL;

-- Partial indexes for filtered queries
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date) WHERE deleted_at IS NULL;

-- Automatic updated_at via trigger
CREATE TRIGGER trg_tasks_updated_at
  BEFORE UPDATE ON tasks FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
```

**Index coverage by query:**
| Query | Index Used |
|---|---|
| `findById(id, userId)` | PK index (id) |
| `findAll(userId, status)` | `idx_tasks_status` |
| `findAll(userId, priority)` | `idx_tasks_priority` |
| `findAll(userId, due_date)` | `idx_tasks_due_date` |
| `findAll(userId)` keyset pagination | `idx_tasks_created_at_id` |
| `findAll(userId)` offset pagination | `idx_tasks_user_id` |

**Verdict (P1/S1): PASS.** Every query path has index coverage. Partial indexes keep index size small by excluding soft-deleted rows.

---

### Pattern 12: `RETURNING *` on All Mutations

```sql
INSERT INTO tasks (…) VALUES (…) RETURNING *
UPDATE tasks SET … WHERE … RETURNING *
UPDATE tasks SET deleted_at = NOW() WHERE … RETURNING *
```

- All three mutation paths (create, update, soft-delete) return the full row
- Eliminates need for separate SELECT after mutation
- Single round-trip for mutation + read-back

**Verdict (P1): PASS.** Efficient mutation pattern.

---

## Summary: Gate-by-Gate Assessment

| Gate | Status | Evidence |
|---|---|---|
| **M1 spec-match** | ✅ | All 6 repository methods match plan specification. 12 distinct SQL patterns cataloged. |
| **S1 dataFlow** | ✅ | SQL query structure is clean: Request→Controller→Service→Repository→pg Pool. No backwards dependencies. Task→TaskResponse DTO strips internal fields. COUNT+SELECT parallelism correct. |
| **S3 injection** | ✅ | 0 SQL injection surfaces. All 12 query patterns use `$N` parameterized binding. Dynamic WHERE/SET use sequential counter — no user strings interpolated into SQL. Zod validation gates all input before it reaches repository. |
| **P1 query** | ✅ | Keyset pagination with proper index backing. FP-010 fix verified (PostgreSQL-native cursor, not JS Date.toISOString()). Parallel COUNT+SELECT. Bulk INSERT capped at 500. Transaction helper with safe connection lifecycle. Pool configured with max=10, statement_timeout=30s, slow-query logging. No N+1 queries. |
| **OVERALL** | **4/4** | **All gates pass. No issues found. FP-010 fix intact.** |

---

## Self-Audit Checklist

- [x] Mode selection matches task scale (FAST for read-only analysis)
- [x] Gate selection based on actual code surface (S1, S3, P1 — the SQL-relevant gates)
- [x] Observable level O0 appropriate for static analysis
- [x] Failure-pattern feed loaded — FP-010 matched via context_tags filter
- [x] Loop ROI history consulted — 0.78 score/token, PROCEED
- [x] Escalation rules defined (minimal — analysis-only task)
- [x] Governance document written to `.omo/governor/sql-pattern-audit-governance.md`
- [x] No invented diff signals or failure patterns
- [x] Mode escalation justified by evidence — FAST is correct for read-only survey
- [x] All downstream dispatch skipped (no plan/loop/qa needed for analysis-only)
- [x] Context-tag filtering verified: FP-010 matched, FP-001~FP-004 excluded
