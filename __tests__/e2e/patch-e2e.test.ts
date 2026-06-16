import path from 'path';
import { Pool } from 'pg';
import jwt from 'jsonwebtoken';
import supertest from 'supertest';
import type { Application } from 'express';
import { startPostgresContainer, stopPostgresContainer, runMigration } from '../test-helpers';

// ── Constants ─────────────────────────────────────────────

const TEST_JWT_SECRET = 'test-secret-that-is-at-least-32-characters-long!!';
const TEST_USER_ID = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
const OTHER_USER_ID = 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22';

function generateToken(sub = TEST_USER_ID, expiresIn = '15m'): string {
  return jwt.sign({ sub, role: 'user' }, TEST_JWT_SECRET, {
    algorithm: 'HS256',
    expiresIn,
  } as jwt.SignOptions);
}

function authHeader(token?: string) {
  return { Authorization: `Bearer ${token || generateToken()}` };
}

// ── L5 E2E Test Suite: PATCH /api/tasks/:id ─────────────
//
// These tests cover end-to-end scenarios NOT tested by the
// existing routes-level, contract, or integration tests:
//
//   E2E-1: Concurrent updates — two simultaneous PATCH requests to the same task
//   E2E-2: PATCH after DELETE — full lifecycle: POST → DELETE → PATCH (expect 404)
//   E2E-3: Unicode/emoji in title and description via PATCH
//   E2E-4: Boundary — very long strings at the limit via PATCH
//   E2E-5: Full lifecycle chain: POST → GET → PATCH → GET → DELETE → PATCH (404)

describe('L5 E2E — PATCH /api/tasks/:id', () => {
  let pool: Pool;
  let app: Application;

  beforeAll(async () => {
    const result = await startPostgresContainer('bkow-e2e-patch-pg');
    pool = result.pool;

    process.env.DATABASE_URL = result.dbUrl;
    process.env.JWT_SECRET = TEST_JWT_SECRET;
    process.env.JWT_EXPIRY = '15m';
    process.env.ALLOWED_ORIGINS = '*';

    const migrationPath = path.join(
      __dirname, '..', '..', 'src', 'lib', 'db', 'migrations', '001_create_tasks.sql',
    );
    await runMigration(pool, migrationPath);

    const mod = await import('../../src/app');
    app = mod.app;
  }, 60000);

  afterAll(async () => {
    await stopPostgresContainer(pool);
  });

  // ═══════════════════════════════════════════════════════════
  // E2E-1: Concurrent updates — two PATCH requests to the same task
  // ═══════════════════════════════════════════════════════════
  //
  // Validates that two near-simultaneous PATCHes to different fields
  // on the same task both succeed and neither update is lost.

  describe('E2E-1: Concurrent updates', () => {
    let concurrencyTaskId: string;

    beforeAll(async () => {
      const res = await supertest(app)
        .post('/api/tasks')
        .set(authHeader())
        .send({ title: 'Concurrent Base', description: 'Initial', status: 'todo', priority: 'medium' });
      concurrencyTaskId = res.body.data.id;
    });

    it('two concurrent PATCH requests both succeed and merge correctly', async () => {
      // Fire two PATCH requests simultaneously (no await between them)
      const patchTitle = supertest(app)
        .patch(`/api/tasks/${concurrencyTaskId}`)
        .set(authHeader())
        .send({ title: 'Concurrent Title Update' });

      const patchDesc = supertest(app)
        .patch(`/api/tasks/${concurrencyTaskId}`)
        .set(authHeader())
        .send({ description: 'Concurrent Description Update' });

      const [res1, res2] = await Promise.all([patchTitle, patchDesc]);

      // Both must succeed
      expect(res1.status).toBe(200);
      expect(res2.status).toBe(200);

      // Read the final state
      const getRes = await supertest(app)
        .get(`/api/tasks/${concurrencyTaskId}`)
        .set(authHeader());
      expect(getRes.status).toBe(200);

      // Both updates must be reflected (order doesn't matter)
      const finalTask = getRes.body.data;
      expect(finalTask.title).toBe('Concurrent Title Update');
      expect(finalTask.description).toBe('Concurrent Description Update');
      // Other fields unchanged
      expect(finalTask.status).toBe('todo');
      expect(finalTask.priority).toBe('medium');
    });
  });

  // ═══════════════════════════════════════════════════════════
  // E2E-2: PATCH after DELETE — lifecycle: POST → DELETE → PATCH (404)
  // ═══════════════════════════════════════════════════════════
  //
  // Validates that a soft-deleted task returns 404 on PATCH.

  describe('E2E-2: PATCH after DELETE', () => {
    let deleteTaskId: string;

    beforeAll(async () => {
      const res = await supertest(app)
        .post('/api/tasks')
        .set(authHeader())
        .send({ title: 'Will be deleted', description: 'Gone soon' });
      deleteTaskId = res.body.data.id;
    });

    it('POST → DELETE → PATCH returns 404', async () => {
      // Verify task exists
      const getRes1 = await supertest(app)
        .get(`/api/tasks/${deleteTaskId}`)
        .set(authHeader());
      expect(getRes1.status).toBe(200);

      // DELETE
      const delRes = await supertest(app)
        .delete(`/api/tasks/${deleteTaskId}`)
        .set(authHeader());
      expect(delRes.status).toBe(204);

      // Verify task is gone
      const getRes2 = await supertest(app)
        .get(`/api/tasks/${deleteTaskId}`)
        .set(authHeader());
      expect(getRes2.status).toBe(404);

      // PATCH should return 404
      const patchRes = await supertest(app)
        .patch(`/api/tasks/${deleteTaskId}`)
        .set(authHeader())
        .send({ title: 'Should fail' });
      expect(patchRes.status).toBe(404);
      expect(patchRes.body.error).toMatch(/not found/i);
      expect(patchRes.body.data).toBeNull();
    });
  });

  // ═══════════════════════════════════════════════════════════
  // E2E-3: Unicode/emoji in title and description via PATCH
  // ═══════════════════════════════════════════════════════════
  //
  // Validates that emoji and CJK characters survive the
  // sanitization pipeline on PATCH (not just POST).

  describe('E2E-3: Unicode/emoji in title and description', () => {
    let unicodeTaskId: string;

    beforeAll(async () => {
      const res = await supertest(app)
        .post('/api/tasks')
        .set(authHeader())
        .send({ title: 'Unicode Base' });
      unicodeTaskId = res.body.data.id;
    });

    it('PATCH with emoji title — emoji preserved', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${unicodeTaskId}`)
        .set(authHeader())
        .send({ title: 'Task 🎉🚀✨' });
      expect(res.status).toBe(200);
      expect(res.body.data.title).toBe('Task 🎉🚀✨');
    });

    it('PATCH with CJK and accented characters in description', async () => {
      const desc = '日本語 Español Français: éèêëàâäùûüç';
      const res = await supertest(app)
        .patch(`/api/tasks/${unicodeTaskId}`)
        .set(authHeader())
        .send({ description: desc });
      expect(res.status).toBe(200);
      expect(res.body.data.description).toBe(desc);
    });

    it('PATCH with mixed HTML + emoji — tags stripped, emoji preserved', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${unicodeTaskId}`)
        .set(authHeader())
        .send({ title: '<b>Bold 🎯</b>', description: '<a href="x">Link 🔗</a>' });
      expect(res.status).toBe(200);
      expect(res.body.data.title).toBe('Bold 🎯');
      expect(res.body.data.description).toBe('Link 🔗');
    });

    it('PATCH with ampersand + emoji — & escaped, emoji preserved', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${unicodeTaskId}`)
        .set(authHeader())
        .send({ title: 'Fish & Chips 🐟🍟' });
      expect(res.status).toBe(200);
      expect(res.body.data.title).toBe('Fish &amp; Chips 🐟🍟');
    });
  });

  // ═══════════════════════════════════════════════════════════
  // E2E-4: Very long strings — boundary testing via PATCH
  // ═══════════════════════════════════════════════════════════
  //
  // Validates that field-length limits are enforced at the
  // HTTP/PATCH endpoint, not just at the schema unit level.

  describe('E2E-4: Very long strings (boundary)', () => {
    let boundaryTaskId: string;

    beforeAll(async () => {
      const res = await supertest(app)
        .post('/api/tasks')
        .set(authHeader())
        .send({ title: 'Boundary Base' });
      boundaryTaskId = res.body.data.id;
    });

    it('PATCH title at exactly 200 chars — accepted', async () => {
      const title200 = 'a'.repeat(200);
      const res = await supertest(app)
        .patch(`/api/tasks/${boundaryTaskId}`)
        .set(authHeader())
        .send({ title: title200 });
      expect(res.status).toBe(200);
      expect(res.body.data.title).toBe(title200);
    });

    it('PATCH title at 201 chars — rejected with 400', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${boundaryTaskId}`)
        .set(authHeader())
        .send({ title: 'a'.repeat(201) });
      expect(res.status).toBe(400);
      expect(res.body.error).toBe('Validation failed');
    });

    it('PATCH description at exactly 5000 chars — accepted', async () => {
      const desc5000 = 'x'.repeat(5000);
      const res = await supertest(app)
        .patch(`/api/tasks/${boundaryTaskId}`)
        .set(authHeader())
        .send({ description: desc5000 });
      expect(res.status).toBe(200);
      expect(res.body.data.description).toBe(desc5000);
    });

    it('PATCH description at 5001 chars — rejected with 400', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${boundaryTaskId}`)
        .set(authHeader())
        .send({ description: 'x'.repeat(5001) });
      expect(res.status).toBe(400);
      expect(res.body.error).toBe('Validation failed');
    });
  });

  // ═══════════════════════════════════════════════════════════
  // E2E-5: Full lifecycle chain
  //   POST → GET (verify created) → PATCH → GET (verify update)
  //   → DELETE → PATCH (verify 404)
  // ═══════════════════════════════════════════════════════════
  //
  // Single continuous scenario exercising the full lifecycle of a task.

  describe('E2E-5: Full lifecycle chain', () => {
    it('POST → GET → PATCH → GET → DELETE → PATCH', async () => {
      // ── STEP 1: POST — create task ─────────────────────
      const createRes = await supertest(app)
        .post('/api/tasks')
        .set(authHeader())
        .send({ title: 'Lifecycle Task', description: 'E2E chain', priority: 'high' });
      expect(createRes.status).toBe(201);
      const taskId = createRes.body.data.id;
      expect(taskId).toBeDefined();

      // ── STEP 2: GET — verify created state ─────────────
      const getRes1 = await supertest(app)
        .get(`/api/tasks/${taskId}`)
        .set(authHeader());
      expect(getRes1.status).toBe(200);
      expect(getRes1.body.data.title).toBe('Lifecycle Task');
      expect(getRes1.body.data.description).toBe('E2E chain');
      expect(getRes1.body.data.status).toBe('todo');
      expect(getRes1.body.data.priority).toBe('high');
      const created_at = getRes1.body.data.created_at;
      const updated_at_1 = getRes1.body.data.updated_at;

      // ── STEP 3: PATCH — update title + status ──────────
      const patchRes = await supertest(app)
        .patch(`/api/tasks/${taskId}`)
        .set(authHeader())
        .send({ title: 'Lifecycle Patched', status: 'in_progress' });
      expect(patchRes.status).toBe(200);
      expect(patchRes.body.data.title).toBe('Lifecycle Patched');
      expect(patchRes.body.data.status).toBe('in_progress');

      // ── STEP 4: GET — verify patch persisted, timestamps ──
      const getRes2 = await supertest(app)
        .get(`/api/tasks/${taskId}`)
        .set(authHeader());
      expect(getRes2.status).toBe(200);
      expect(getRes2.body.data.title).toBe('Lifecycle Patched');
      expect(getRes2.body.data.status).toBe('in_progress');
      expect(getRes2.body.data.description).toBe('E2E chain'); // unchanged
      expect(getRes2.body.data.priority).toBe('high');         // unchanged
      expect(getRes2.body.data.created_at).toBe(created_at);   // never changes
      expect(getRes2.body.data.updated_at).not.toBe(updated_at_1); // advanced

      // ── STEP 5: DELETE — soft-delete ───────────────────
      const delRes = await supertest(app)
        .delete(`/api/tasks/${taskId}`)
        .set(authHeader());
      expect(delRes.status).toBe(204);

      // Verify task is gone
      const getRes3 = await supertest(app)
        .get(`/api/tasks/${taskId}`)
        .set(authHeader());
      expect(getRes3.status).toBe(404);

      // ── STEP 6: PATCH after DELETE — should be 404 ────
      const patchAfterDelete = await supertest(app)
        .patch(`/api/tasks/${taskId}`)
        .set(authHeader())
        .send({ title: 'Should be 404' });
      expect(patchAfterDelete.status).toBe(404);
      expect(patchAfterDelete.body.error).toMatch(/not found/i);
      expect(patchAfterDelete.body.data).toBeNull();
    });
  });
});
