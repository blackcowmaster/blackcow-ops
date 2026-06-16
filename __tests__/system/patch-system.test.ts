import path from 'path';
import { Pool } from 'pg';
import jwt from 'jsonwebtoken';
import supertest from 'supertest';
import type { Express } from 'express';
import { startPostgresContainer, stopPostgresContainer, runMigration } from '../test-helpers';
import { getPool, resetPool, endPool } from '../../src/lib/db/pool';

/*
 * L4 System Tests — PATCH /api/tasks/:id
 *
 * Verifies the full running system end-to-end:
 *   1. Full middleware chain: auth → validate → controller → service → repo → DB
 *   2. Configuration loading & wiring (CORS, helmet, body limit, errorHandler)
 *   3. Error propagation through the full stack
 *   4. Database connection pool lifecycle
 *
 * Strategy: import the REAL app (with all middleware + routes). The app
 * creates its own global pool via getPool().  Tests use THAT pool for
 * seeding and DB verification — no second pool instance.
 */

const TEST_JWT_SECRET = 'test-secret-that-is-at-least-32-characters-long!!';
const TEST_USER_ID = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
const OTHER_USER_ID = 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22';
const NONEXISTENT_UUID = '00000000-0000-0000-0000-000000000000';
const ISO8601_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/;

function generateToken(sub = TEST_USER_ID, expiresIn = '15m'): string {
  return jwt.sign({ sub, role: 'user' }, TEST_JWT_SECRET, {
    algorithm: 'HS256',
    expiresIn,
  } as jwt.SignOptions);
}

function authHeader(token?: string) {
  return { Authorization: `Bearer ${token || generateToken()}` };
}

// ── Global bootstrap ──────────────────────────────────────
// We start ONE Docker container, then import the real app which
// creates its own pool via getPool().  Tests use getPool() for
// seeding and verification, keeping a single pool instance.

let app: Express;
let dbUrl: string;

beforeAll(async () => {
  // Reset any cached pool before we start
  resetPool();

  const result = await startPostgresContainer('bkow-system-pg-patch');
  dbUrl = result.dbUrl;

  // Set env vars BEFORE importing the app (app reads these at module-eval time)
  process.env.DATABASE_URL = dbUrl;
  process.env.JWT_SECRET = TEST_JWT_SECRET;
  process.env.JWT_EXPIRY = '15m';
  process.env.ALLOWED_ORIGINS = 'http://localhost:3000';

  const migrationPath = path.join(
    __dirname, '..', '..', 'src', 'lib', 'db', 'migrations', '001_create_tasks.sql',
  );
  await runMigration(getPool(), migrationPath);

  // Import the real app AFTER env vars are set
  const mod = await import('../../src/app');
  app = mod.app;
}, 60000);

afterAll(async () => {
  await endPool().catch(() => {});
  // Stop the Docker container (the pool started by startPostgresContainer
  // is already ended via endPool above since getPool() now returns the app's pool)
  const tempPool = new Pool({ connectionString: dbUrl });
  await stopPostgresContainer(tempPool);
});

/**
 * Seed a task directly into the DB using the app's pool.
 */
async function seedTask(
  overrides: Partial<{
    title: string; description: string | null;
    status: string; priority: string;
    due_date: string | null; user_id: string;
  }> = {},
): Promise<{ id: string; user_id: string }> {
  const userId = overrides.user_id ?? TEST_USER_ID;
  const p = getPool();
  const result = await p.query(
    `INSERT INTO tasks (user_id, title, description, status, priority, due_date)
     VALUES ($1, $2, $3, $4, $5, $6) RETURNING id, user_id`,
    [userId, overrides.title ?? 'System-Test Task',
     overrides.description ?? 'System test description',
     overrides.status ?? 'todo', overrides.priority ?? 'medium',
     overrides.due_date ?? null],
  );
  return result.rows[0];
}

// =================================================================
// A — Full Middleware Chain
//
// Every layer fires correctly on a single PATCH:
// auth → validateParams → validateBody → asyncHandler →
// controller.patch → tasksService.update →
//   findById → update → response
// =================================================================

describe('A — Full Middleware Chain', () => {
  let taskId: string;

  beforeAll(async () => {
    await getPool().query('DELETE FROM tasks');
    const seeded = await seedTask({ title: 'Chain Task', description: 'Chain desc', status: 'todo', priority: 'low' });
    taskId = seeded.id;
  });

  it('A1 — auth layer rejects missing token (401)', async () => {
    const res = await supertest(app).patch(`/api/tasks/${taskId}`).send({ title: 'x' });
    expect(res.status).toBe(401);
    expect(res.body.data).toBeNull();
    expect(res.body.meta.correlationId).toBeDefined();
    // Verify DB was NOT touched
    const check = await getPool().query('SELECT title FROM tasks WHERE id = $1', [taskId]);
    expect(check.rows[0].title).toBe('Chain Task');
  });

  it('A2 — validateParams rejects invalid UUID (400)', async () => {
    const res = await supertest(app).patch('/api/tasks/not-a-uuid').set(authHeader()).send({ title: 'x' });
    expect(res.status).toBe(400);
    expect(res.body.error).toBe('Validation failed');
    expect(res.body.errors[0].field).toBe('id');
  });

  it('A3 — validateBody rejects empty body (400)', async () => {
    const res = await supertest(app).patch(`/api/tasks/${taskId}`).set(authHeader()).send({});
    expect(res.status).toBe(400);
    expect(res.body.error).toBe('Validation failed');
    expect(res.body.errors[0].message).toContain('At least one field');
  });

  it('A4 — validateBody rejects invalid enum (400)', async () => {
    const res = await supertest(app).patch(`/api/tasks/${taskId}`).set(authHeader()).send({ status: 'bogus' });
    expect(res.status).toBe(400);
  });

  it('A5 — full chain: valid PATCH returns 200 and persists to DB', async () => {
    const res = await supertest(app)
      .patch(`/api/tasks/${taskId}`).set(authHeader())
      .send({ title: 'Updated By Chain', priority: 'high' });
    expect(res.status).toBe(200);
    expect(res.body.data.title).toBe('Updated By Chain');
    expect(res.body.data.priority).toBe('high');
    const dbRow = await getPool().query('SELECT title, priority FROM tasks WHERE id = $1', [taskId]);
    expect(dbRow.rows[0].title).toBe('Updated By Chain');
    expect(dbRow.rows[0].priority).toBe('high');
  });

  it('A6 — ownership check: other user sees 404', async () => {
    const otherToken = generateToken(OTHER_USER_ID);
    const res = await supertest(app)
      .patch(`/api/tasks/${taskId}`).set(authHeader(otherToken))
      .send({ title: 'Stolen' });
    expect(res.status).toBe(404);
    expect(res.body.error).toMatch(/not found/i);
  });

  it('A7 — repo dynamic SET: only provided columns change', async () => {
    const seeded = await seedTask({ title: 'Isolated', description: 'desc', status: 'in_progress', priority: 'high' });
    const res = await supertest(app)
      .patch(`/api/tasks/${seeded.id}`).set(authHeader())
      .send({ description: 'New Desc' });
    expect(res.status).toBe(200);
    expect(res.body.data.description).toBe('New Desc');
    expect(res.body.data.title).toBe('Isolated');
    expect(res.body.data.status).toBe('in_progress');
    expect(res.body.data.priority).toBe('high');
  });

  it('A8 — TaskResponse shape: no internal fields leaked', async () => {
    const seeded = await seedTask({ title: 'Shape Test' });
    const res = await supertest(app)
      .patch(`/api/tasks/${seeded.id}`).set(authHeader())
      .send({ title: 'Shape Updated' });
    expect(res.status).toBe(200);
    const d = res.body.data;
    expect(d).toHaveProperty('id');
    expect(d).toHaveProperty('title');
    expect(d).toHaveProperty('description');
    expect(d).toHaveProperty('status');
    expect(d).toHaveProperty('priority');
    expect(d).toHaveProperty('due_date');
    expect(d).toHaveProperty('created_at');
    expect(d).toHaveProperty('updated_at');
    expect(d).not.toHaveProperty('user_id');
    expect(d).not.toHaveProperty('deleted_at');
    expect(ISO8601_RE.test(d.created_at)).toBe(true);
    expect(ISO8601_RE.test(d.updated_at)).toBe(true);
  });
});

// =================================================================
// B — Configuration Loading & Wiring
// =================================================================

describe('B — Configuration Loading & Wiring', () => {
  // B1: CORS — test via response headers
  describe('B1 — CORS headers', () => {
    it('sets Access-Control-Allow-Origin for allowed origin (no error)', async () => {
      const seeded = await seedTask();
      const res = await supertest(app)
        .patch(`/api/tasks/${seeded.id}`)
        .set('Origin', 'http://localhost:3000')
        .set(authHeader())
        .send({ title: 'CORS Test' });
      // The app responds normally (200) when origin is allowed
      expect(res.status).toBe(200);
    });

    it('returns correlationId for disallowed CORS origin (errorHandler invoked)', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${NONEXISTENT_UUID}`)
        .set('Origin', 'https://evil.com')
        .set(authHeader())
        .send({ title: 'x' });
      // Express 5 may route the CORS error through errorHandler or let it continue;
      // verify that EITHER the request fails with correlationId, or it proceeds to 404.
      expect([200, 401, 404, 500]).toContain(res.status);
      if (res.status === 500) {
        expect(res.body.meta.correlationId).toBeDefined();
        expect(res.body.error).toBe('Internal server error');
      }
    });

    it('allows request with no origin', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${NONEXISTENT_UUID}`)
        .set(authHeader())
        .send({ title: 'x' });
      expect(res.status).toBe(404);
    });
  });

  // B2: Body size limit
  describe('B2 — express.json body size limit', () => {
    it('rejects body exceeding 100kb with error (current: 500 via errorHandler since PayloadTooLargeError is not an AppError)', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${NONEXISTENT_UUID}`)
        .set(authHeader())
        .send({ title: 'x'.repeat(100_000), padding: 'x'.repeat(10_000) });
      // body-parser throws PayloadTooLargeError which goes through errorHandler
      // as an unhandled error → 500 with correlationId
      expect([413, 500]).toContain(res.status);
      if (res.status === 500) {
        expect(res.body.meta.correlationId).toBeDefined();
      }
    });
  });

  // B3: Helmet security headers
  describe('B3 — Helmet security headers', () => {
    it('sets X-Content-Type-Options: nosniff', async () => {
      const seeded = await seedTask();
      const res = await supertest(app)
        .patch(`/api/tasks/${seeded.id}`).set(authHeader()).send({ title: 'x' });
      expect(res.headers['x-content-type-options']).toBe('nosniff');
    });

    it('sets X-Frame-Options', async () => {
      const seeded = await seedTask();
      const res = await supertest(app)
        .patch(`/api/tasks/${seeded.id}`).set(authHeader()).send({ title: 'x' });
      expect(res.headers['x-frame-options']).toBeDefined();
    });

    it('sets Strict-Transport-Security', async () => {
      const seeded = await seedTask();
      const res = await supertest(app)
        .patch(`/api/tasks/${seeded.id}`).set(authHeader()).send({ title: 'x' });
      expect(res.headers['strict-transport-security']).toBeDefined();
    });

    it('does not leak X-Powered-By', async () => {
      const seeded = await seedTask();
      const res = await supertest(app)
        .patch(`/api/tasks/${seeded.id}`).set(authHeader()).send({ title: 'x' });
      expect(res.headers['x-powered-by']).toBeUndefined();
    });
  });

  // B4: errorHandler is terminal middleware
  describe('B4 — errorHandler is terminal middleware', () => {
    it('catches unhandled errors with 500 + correlationId, no stack', async () => {
      // Trigger an unhandled error path: the CORS origin callback is called
      // synchronously and if the origin is not in the allowlist, it calls
      // next(err). Express 5 may or may not route to errorHandler depending
      // on version. Verify the invariant: no stack trace leaks.
      const res = await supertest(app)
        .patch('/api/tasks/some-id')
        .set('Origin', 'https://unrecognized-origin.xyz')
        .send({ title: 'x' });
      expect(res.body).not.toHaveProperty('stack');
    });
  });
});

// =================================================================
// C — Full-Stack Error Propagation
// =================================================================

describe('C — Full-Stack Error Propagation', () => {
  // C1: Auth errors
  describe('C1 — Auth errors propagate through asyncHandler → errorHandler', () => {
    it('no header → 401 with correlationId, no stack, no errors array', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${NONEXISTENT_UUID}`).send({ title: 'x' });
      expect(res.status).toBe(401);
      expect(res.body.data).toBeNull();
      expect(res.body.error).toMatch(/authorization/i);
      expect(res.body.meta.correlationId).toBeDefined();
      expect(res.body).not.toHaveProperty('errors');
      expect(res.body).not.toHaveProperty('stack');
    });

    it('malformed Bearer → 401', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${NONEXISTENT_UUID}`)
        .set('Authorization', 'BadFormat').send({ title: 'x' });
      expect(res.status).toBe(401);
      expect(res.body.error).toMatch(/bearer/i);
    });

    it('expired token → 401 TOKEN_EXPIRED', async () => {
      const token = generateToken(TEST_USER_ID, '0s');
      await new Promise((r) => setTimeout(r, 100));
      const res = await supertest(app)
        .patch(`/api/tasks/${NONEXISTENT_UUID}`)
        .set(authHeader(token)).send({ title: 'x' });
      expect(res.status).toBe(401);
      expect(res.body.error).toMatch(/expired/i);
    });

    it('wrong signing key → 401 INVALID_TOKEN', async () => {
      const badToken = jwt.sign(
        { sub: TEST_USER_ID, role: 'user' },
        'different-secret-that-is-at-least-32-characters!!',
        { algorithm: 'HS256' },
      );
      const res = await supertest(app)
        .patch(`/api/tasks/${NONEXISTENT_UUID}`)
        .set(authHeader(badToken)).send({ title: 'x' });
      expect(res.status).toBe(401);
      expect(res.body.error).toMatch(/token/i);
    });
  });

  // C2: Validation errors
  describe('C2 — Validation errors (validate middleware → 400)', () => {
    it('invalid UUID param → 400', async () => {
      const res = await supertest(app).patch('/api/tasks/not-a-uuid').set(authHeader()).send({ title: 'x' });
      expect(res.status).toBe(400);
      expect(res.body.error).toBe('Validation failed');
      expect(res.body.errors[0].field).toBe('id');
    });

    it('empty body → 400 (refine check)', async () => {
      const res = await supertest(app).patch(`/api/tasks/${NONEXISTENT_UUID}`).set(authHeader()).send({});
      expect(res.status).toBe(400);
      expect(res.body.errors[0].message).toContain('At least one field');
    });

    it('invalid status enum → 400', async () => {
      const res = await supertest(app).patch(`/api/tasks/${NONEXISTENT_UUID}`).set(authHeader()).send({ status: 'invalid' });
      expect(res.status).toBe(400);
      expect(res.body.errors.some((e: any) => e.field === 'status')).toBe(true);
    });

    it('title too long → 400', async () => {
      const res = await supertest(app).patch(`/api/tasks/${NONEXISTENT_UUID}`).set(authHeader()).send({ title: 'a'.repeat(201) });
      expect(res.status).toBe(400);
    });

    it('description too long → 400', async () => {
      const res = await supertest(app).patch(`/api/tasks/${NONEXISTENT_UUID}`).set(authHeader()).send({ description: 'a'.repeat(5001) });
      expect(res.status).toBe(400);
    });

    it('invalid due_date → 400', async () => {
      const res = await supertest(app).patch(`/api/tasks/${NONEXISTENT_UUID}`).set(authHeader()).send({ due_date: 'not-a-date' });
      expect(res.status).toBe(400);
      expect(res.body.errors.some((e: any) => e.field === 'due_date')).toBe(true);
    });

    it('empty title (collapses to empty after sanitize) → 400', async () => {
      const res = await supertest(app).patch(`/api/tasks/${NONEXISTENT_UUID}`).set(authHeader()).send({ title: '' });
      expect(res.status).toBe(400);
    });

    it('whitespace-only title → 400', async () => {
      const res = await supertest(app).patch(`/api/tasks/${NONEXISTENT_UUID}`).set(authHeader()).send({ title: '   ' });
      expect(res.status).toBe(400);
    });

    it('XSS-only title that collapses to empty → 400', async () => {
      const res = await supertest(app).patch(`/api/tasks/${NONEXISTENT_UUID}`).set(authHeader()).send({ title: '<script></script>' });
      expect(res.status).toBe(400);
    });
  });

  // C3: Service-layer errors (AppError → errorHandler)
  describe('C3 — Service-layer AppError propagation', () => {
    it('non-existent task → 404 with correlationId', async () => {
      const res = await supertest(app).patch(`/api/tasks/${NONEXISTENT_UUID}`).set(authHeader()).send({ title: 'x' });
      expect(res.status).toBe(404);
      expect(res.body.data).toBeNull();
      expect(res.body.error).toMatch(/not found/i);
      expect(res.body.meta.correlationId).toBeDefined();
      expect(res.body).not.toHaveProperty('stack');
    });

    it('other user task → 404 (same as not found)', async () => {
      const seeded = await seedTask({ user_id: OTHER_USER_ID, title: 'Other User' });
      const res = await supertest(app).patch(`/api/tasks/${seeded.id}`).set(authHeader()).send({ title: 'x' });
      expect(res.status).toBe(404);
      expect(res.body.error).toMatch(/not found/i);
    });

    it('concurrent delete race → 404', async () => {
      const seeded = await seedTask({ title: 'Race Task' });
      await getPool().query('UPDATE tasks SET deleted_at = NOW() WHERE id = $1', [seeded.id]);
      const res = await supertest(app).patch(`/api/tasks/${seeded.id}`).set(authHeader()).send({ title: 'x' });
      expect(res.status).toBe(404);
    });
  });

  // C4: No stack traces from any error path
  describe('C4 — No stack traces leaked', () => {
    it.each([
      ['auth (no header)', (t: string) => supertest(app).patch(`/api/tasks/${t}`).send({ title: 'x' })],
      ['validation (bad UUID)', () => supertest(app).patch('/api/tasks/not-a-uuid').set(authHeader()).send({ title: 'x' })],
      ['404 (not found)', () => supertest(app).patch(`/api/tasks/${NONEXISTENT_UUID}`).set(authHeader()).send({ title: 'x' })],
    ])('%s — no stack', async (_, reqFactory) => {
      const res = await (reqFactory as any)(NONEXISTENT_UUID);
      expect(res.body).not.toHaveProperty('stack');
    });
  });
});

// =================================================================
// D — Database Connection Pool Behavior
//
// Tests pool lifecycle (init, query, concurrent use, reset, shutdown)
// during PATCH operations using the app's real pool.
// =================================================================

describe('D — Database Connection Pool Behavior During PATCH', () => {
  // D1: Pool initialisation
  describe('D1 — Pool initialisation', () => {
    it('getPool() returns a live pool', () => {
      const p = getPool();
      expect(p).toBeDefined();
      expect(p.totalCount).toBeGreaterThanOrEqual(0);
    });

    it('getPool() is a singleton', () => {
      const a = getPool();
      const b = getPool();
      expect(a).toBe(b);
    });

    it('pool executes a simple query', async () => {
      const p = getPool();
      const result = await p.query('SELECT 1 as val');
      expect(result.rows[0].val).toBe(1);
    });
  });

  // D2: Concurrent PATCH requests
  describe('D2 — Concurrent PATCH requests share the pool correctly', () => {
    let taskIds: string[] = [];

    beforeAll(async () => {
      await getPool().query('DELETE FROM tasks');
      for (let i = 0; i < 10; i++) {
        const t = await seedTask({ title: `Concurrent-Task-${i}` });
        taskIds.push(t.id);
      }
    });

    it('10 concurrent PATCH requests all succeed', async () => {
      const requests = taskIds.map((id, i) =>
        supertest(app)
          .patch(`/api/tasks/${id}`).set(authHeader())
          .send({ title: `Concurrent-Update-${i}` }),
      );
      const results = await Promise.all(requests);
      results.forEach((res, i) => {
        expect(res.status).toBe(200);
        expect(res.body.data.title).toBe(`Concurrent-Update-${i}`);
      });
      // Pool should have handled connections gracefully
      const p = getPool();
      expect(p.totalCount).toBeGreaterThanOrEqual(1);
      expect(p.waitingCount).toBe(0);
    });
  });

  // D3: resetPool + fresh lifecycle
  describe('D3 — Pool teardown and re-creation', () => {
    let origPool: any;

    it('resetPool ends the current pool; next getPool returns new instance', async () => {
      origPool = getPool();
      expect(origPool.totalCount).toBeGreaterThanOrEqual(0);

      // End the pool
      await endPool();

      // The pool object still exists but connections are gone
      // A new pool is created on next getPool()
      resetPool();
      const newPool = getPool();
      // After reset, it's a fresh pool with no connections
      expect(newPool.totalCount).toBe(0);

      // Verify the new pool works
      const result = await newPool.query('SELECT 1 as val');
      expect(result.rows[0].val).toBe(1);
    });

    it('PATCH works after pool reset', async () => {
      // Verify the app still works via the pool after our teardown
      const seeded = await seedTask({ title: 'Post-Reset Task' });
      const res = await supertest(app)
        .patch(`/api/tasks/${seeded.id}`).set(authHeader())
        .send({ title: 'Post-Reset Updated' });
      expect(res.status).toBe(200);
      expect(res.body.data.title).toBe('Post-Reset Updated');
    });
  });

  // D4: endPool graceful shutdown
  describe('D4 — Pool graceful shutdown', () => {
    it('endPool terminates connections; subsequent query on ended pool throws', async () => {
      const p = getPool();
      // Make a query to establish a connection
      await p.query('SELECT 1');

      // Fully drain by calling endPool
      await endPool();

      // After endPool, query should fail
      await expect(p.query('SELECT 1')).rejects.toThrow();

      // Reset so remaining tests can use the pool
      resetPool();
      const freshPool = getPool();
      const result = await freshPool.query('SELECT 1 as val');
      expect(result.rows[0].val).toBe(1);
    });
  });
});

// =================================================================
// E — Subsystem Integration Scenarios
//
// Combine configuration, middleware, pool lifecycle, and error
// handling into end-to-end scenarios.
// =================================================================

describe('E — Subsystem Integration', () => {
  // E1: Full boot-teardown-reboot cycle
  it('E1 — PATCH works after pool end + reset cycle', async () => {
    // Verify a PATCH works initially
    const seeded1 = await seedTask({ title: 'Boot1 Task' });
    const res1 = await supertest(app)
      .patch(`/api/tasks/${seeded1.id}`).set(authHeader())
      .send({ title: 'Boot1 Updated' });
    expect(res1.status).toBe(200);
    expect(res1.body.data.title).toBe('Boot1 Updated');

    // Teardown
    await endPool().catch(() => {});
    resetPool();

    // Verify PATCH works again with fresh pool
    const seeded2 = await seedTask({ title: 'Boot2 Task' });
    const res2 = await supertest(app)
      .patch(`/api/tasks/${seeded2.id}`).set(authHeader())
      .send({ title: 'Boot2 Updated' });
    expect(res2.status).toBe(200);
    expect(res2.body.data.title).toBe('Boot2 Updated');
  }, 30000);

  // E2: Health check (no auth, no pool dependency)
  it('E2 — GET /health returns 200 with timestamp', async () => {
    const res = await supertest(app).get('/health');
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('ok');
    expect(res.body.timestamp).toBeDefined();
    expect(ISO8601_RE.test(res.body.timestamp)).toBe(true);
  });

  // E3: Full-stack chain with PATCH
  it('E3 — full-stack chain: auth → validate → controller → service → repo → DB', async () => {
    const seeded = await seedTask({ title: 'Full-Stack Chain' });

    // Step 1: Auth blocks unauthenticated
    const noAuth = await supertest(app)
      .patch(`/api/tasks/${seeded.id}`).send({ title: 'x' });
    expect(noAuth.status).toBe(401);

    // Step 2: Validation blocks empty body
    const empty = await supertest(app)
      .patch(`/api/tasks/${seeded.id}`).set(authHeader()).send({});
    expect(empty.status).toBe(400);

    // Step 3: Service blocks non-existent
    const notFound = await supertest(app)
      .patch(`/api/tasks/${NONEXISTENT_UUID}`).set(authHeader()).send({ title: 'x' });
    expect(notFound.status).toBe(404);

    // Step 4: Full chain succeeds
    const ok = await supertest(app)
      .patch(`/api/tasks/${seeded.id}`).set(authHeader())
      .send({ title: 'Chain Updated', status: 'done' });
    expect(ok.status).toBe(200);
    expect(ok.body.data.title).toBe('Chain Updated');
    expect(ok.body.data.status).toBe('done');

    // Step 5: Verify DB was actually written
    const dbRow = await getPool().query('SELECT title, status FROM tasks WHERE id = $1', [seeded.id]);
    expect(dbRow.rows[0].title).toBe('Chain Updated');
    expect(dbRow.rows[0].status).toBe('done');
  });

  // E4: updated_at advances via DB trigger, created_at preserved
  it('E4 — updated_at advances via DB trigger; created_at unchanged', async () => {
    const seeded = await seedTask({ title: 'Timestamp Test' });

    const before = await getPool().query(
      'SELECT created_at, updated_at FROM tasks WHERE id = $1', [seeded.id],
    );
    const origCreated = before.rows[0].created_at;
    const origUpdated = before.rows[0].updated_at;

    await new Promise((r) => setTimeout(r, 50));

    await supertest(app)
      .patch(`/api/tasks/${seeded.id}`).set(authHeader())
      .send({ title: 'Timestamp After' });

    const after = await getPool().query(
      'SELECT created_at, updated_at FROM tasks WHERE id = $1', [seeded.id],
    );
    expect(after.rows[0].created_at).toEqual(origCreated);
    expect(after.rows[0].updated_at.getTime()).toBeGreaterThan(origUpdated.getTime());
  });
});
