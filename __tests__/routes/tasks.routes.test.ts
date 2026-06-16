import path from 'path';
import { Pool } from 'pg';
import jwt from 'jsonwebtoken';
import supertest from 'supertest';
import type { Application } from 'express';
import { startPostgresContainer, stopPostgresContainer, runMigration } from '../test-helpers';

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

describe('Tasks API — Integration', () => {
  let pool: Pool;
  let app: Application;
  let createdTaskId: string;

  beforeAll(async () => {
    const result = await startPostgresContainer('bkow-test-pg-routes');
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

  // ── S2 Auth ─────────────────────────────────────────────

  describe('S2 — Authentication', () => {
    it('401 without auth header', async () => {
      const res = await supertest(app).get('/api/tasks');
      expect(res.status).toBe(401);
    });

    it('401 for malformed auth', async () => {
      const res = await supertest(app)
        .get('/api/tasks')
        .set('Authorization', 'BadFormat');
      expect(res.status).toBe(401);
    });

    it('401 for expired token', async () => {
      const token = generateToken(TEST_USER_ID, '0s');
      await new Promise((r) => setTimeout(r, 100));
      const res = await supertest(app).get('/api/tasks').set(authHeader(token));
      expect(res.status).toBe(401);
    });

    it('401 for invalid signature', async () => {
      const badToken = jwt.sign(
        { sub: TEST_USER_ID, role: 'user' },
        'wrong-secret-that-is-at-least-32-chars!!',
        { algorithm: 'HS256' },
      );
      const res = await supertest(app).get('/api/tasks').set(authHeader(badToken));
      expect(res.status).toBe(401);
    });

    it('200 for valid token', async () => {
      const res = await supertest(app).get('/api/tasks').set(authHeader());
      expect(res.status).toBe(200);
    });
  });

  // ── S3 Validation ───────────────────────────────────────

  describe('S3 — Validation', () => {
    it('400 for empty POST body', async () => {
      const res = await supertest(app).post('/api/tasks').set(authHeader()).send({});
      expect(res.status).toBe(400);
    });

    it('400 for empty title', async () => {
      const res = await supertest(app).post('/api/tasks').set(authHeader()).send({ title: '' });
      expect(res.status).toBe(400);
    });

    it('400 for invalid UUID', async () => {
      const res = await supertest(app).get('/api/tasks/not-a-uuid').set(authHeader());
      expect(res.status).toBe(400);
    });

    it('400 for invalid status enum', async () => {
      const res = await supertest(app)
        .post('/api/tasks')
        .set(authHeader())
        .send({ title: 'X', status: 'bad' });
      expect(res.status).toBe(400);
    });

    it('400 for invalid mode', async () => {
      const res = await supertest(app)
        .get('/api/tasks?mode=invalid')
        .set(authHeader());
      expect(res.status).toBe(400);
    });

    // ── XSS Sanitization ──────────────────────────────

    it('strips <script> from title on POST', async () => {
      const res = await supertest(app)
        .post('/api/tasks')
        .set(authHeader())
        .send({ title: '<script>alert(1)</script>' });
      expect(res.status).toBe(201);
      expect(res.body.data.title).toBe('alert(1)');
    });

    it('strips HTML tags from title and description on POST', async () => {
      const res = await supertest(app)
        .post('/api/tasks')
        .set(authHeader())
        .send({ title: '  <b>Hello</b>  ', description: '<img src=x>' });
      expect(res.status).toBe(201);
      expect(res.body.data.title).toBe('Hello');
      // sanitizeText('') → '' → repository: dto.description || null → null (plan risk register: S1_dataFlow)
      expect(res.body.data.description).toBeNull();
    });

    it('escapes & and preserves emoji in title, strips tags from description on POST', async () => {
      const res = await supertest(app)
        .post('/api/tasks')
        .set(authHeader())
        .send({ title: 'XSS & 🎉', description: "<a href='x'>click</a>" });
      expect(res.status).toBe(201);
      expect(res.body.data.title).toBe('XSS &amp; 🎉');
      expect(res.body.data.description).toBe('click');
    });

    it('strips <script> from description on PUT', async () => {
      // Create a task first
      const createRes = await supertest(app)
        .post('/api/tasks')
        .set(authHeader())
        .send({ title: 'PUT test' });
      const taskId = createRes.body.data.id;
      // Now PUT with XSS payload in description
      const res = await supertest(app)
        .put(`/api/tasks/${taskId}`)
        .set(authHeader())
        .send({ description: '<script>evil()</script>' });
      expect(res.status).toBe(200);
      expect(res.body.data.description).toBe('evil()');
    });
  });

  // ── M1 CRUD ─────────────────────────────────────────────

  describe('M1 — CRUD', () => {
    it('POST 201 create task', async () => {
      const res = await supertest(app)
        .post('/api/tasks')
        .set(authHeader())
        .send({ title: 'Integration test', description: 'desc', priority: 'high' });
      expect(res.status).toBe(201);
      expect(res.body.data.title).toBe('Integration test');
      expect(res.body.data.user_id).toBeUndefined();
      expect(res.body.data.deleted_at).toBeUndefined();
      createdTaskId = res.body.data.id;
    });

    it('GET 200 list tasks — meta shape', async () => {
      const res = await supertest(app).get('/api/tasks').set(authHeader());
      expect(res.status).toBe(200);
      expect(Array.isArray(res.body.data)).toBe(true);
      expect(res.body.meta).toBeDefined();
      // New meta shape: { page, limit, total, hasMore }
      expect(res.body.meta.page).toBe(1);
      expect(res.body.meta.limit).toBe(25);
      expect(typeof res.body.meta.total).toBe('number');
      expect(typeof res.body.meta.hasMore).toBe('boolean');
      // Old fields must not be present
      expect(res.body.meta.totalPages).toBeUndefined();
    });

    it('GET 200 get by id', async () => {
      const res = await supertest(app).get(`/api/tasks/${createdTaskId}`).set(authHeader());
      expect(res.status).toBe(200);
      expect(res.body.data.id).toBe(createdTaskId);
    });

    it('PUT 200 update', async () => {
      const res = await supertest(app)
        .put(`/api/tasks/${createdTaskId}`)
        .set(authHeader())
        .send({ title: 'Updated', status: 'in_progress' });
      expect(res.status).toBe(200);
      expect(res.body.data.title).toBe('Updated');
    });

    it('DELETE 204 soft-delete', async () => {
      const res = await supertest(app).delete(`/api/tasks/${createdTaskId}`).set(authHeader());
      expect(res.status).toBe(204);
      const getRes = await supertest(app).get(`/api/tasks/${createdTaskId}`).set(authHeader());
      expect(getRes.status).toBe(404);
    });

    it('GET 404 not found', async () => {
      const res = await supertest(app)
        .get('/api/tasks/00000000-0000-0000-0000-000000000000')
        .set(authHeader());
      expect(res.status).toBe(404);
    });
  });

  // ── PATCH /api/tasks/:id — Partial Update ────────────────

  describe('PATCH /api/tasks/:id — Partial Update', () => {
    let patchTaskId: string;

    beforeAll(async () => {
      const res = await supertest(app)
        .post('/api/tasks')
        .set(authHeader())
        .send({ title: 'Original Title', description: 'Original desc', status: 'todo', priority: 'low' });
      patchTaskId = res.body.data.id;
    });

    // M1: Partial update — title only
    it('PATCH title only — 200, title updated, other fields unchanged', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${patchTaskId}`)
        .set(authHeader())
        .send({ title: 'New Title' });
      expect(res.status).toBe(200);
      expect(res.body.data.title).toBe('New Title');
      expect(res.body.data.description).toBe('Original desc');
      expect(res.body.data.status).toBe('todo');
      expect(res.body.data.priority).toBe('low');
    });

    // M1: Partial update — description only
    it('PATCH description only — 200, description updated, title unchanged', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${patchTaskId}`)
        .set(authHeader())
        .send({ description: 'New desc' });
      expect(res.status).toBe(200);
      expect(res.body.data.description).toBe('New desc');
      expect(res.body.data.title).toBe('New Title'); // from previous test
    });

    // M1: Partial update — multiple fields
    it('PATCH multiple fields — 200, both updated, others unchanged', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${patchTaskId}`)
        .set(authHeader())
        .send({ title: 'Multi Update', status: 'done' });
      expect(res.status).toBe(200);
      expect(res.body.data.title).toBe('Multi Update');
      expect(res.body.data.status).toBe('done');
      expect(res.body.data.description).toBe('New desc'); // unchanged
    });

    // S3: Empty title → 400
    it('PATCH empty title → 400', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${patchTaskId}`)
        .set(authHeader())
        .send({ title: '' });
      expect(res.status).toBe(400);
      expect(res.body.errors[0].message).toContain('Title');
    });

    // S3: Whitespace-only title → 400
    it('PATCH whitespace-only title → 400', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${patchTaskId}`)
        .set(authHeader())
        .send({ title: '   ' });
      expect(res.status).toBe(400);
    });

    // S3: Script-tag title → 400 (stripped to empty → rejected)
    it('PATCH script-tag that collapses to empty → 400', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${patchTaskId}`)
        .set(authHeader())
        .send({ title: '<script></script>' });
      expect(res.status).toBe(400);
    });

    // M1: Title NOT provided → keep existing
    it('PATCH without title — 200, title preserved', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${patchTaskId}`)
        .set(authHeader())
        .send({ description: 'only desc' });
      expect(res.status).toBe(200);
      expect(res.body.data.title).toBe('Multi Update'); // preserved
      expect(res.body.data.description).toBe('only desc');
    });

    // M1: No-op patch (same values)
    it('PATCH no-op — 200, data unchanged', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${patchTaskId}`)
        .set(authHeader())
        .send({ title: 'Multi Update' });
      expect(res.status).toBe(200);
      expect(res.body.data.title).toBe('Multi Update');
    });

    // S3: Invalid status enum
    it('PATCH invalid status → 400', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${patchTaskId}`)
        .set(authHeader())
        .send({ status: 'invalid' });
      expect(res.status).toBe(400);
    });

    // S3: Empty body → 400
    it('PATCH empty body → 400', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${patchTaskId}`)
        .set(authHeader())
        .send({});
      expect(res.status).toBe(400);
      expect(res.body.errors[0].message).toContain('At least one field');
    });

    // M1: Non-existent task → 404
    it('PATCH non-existent task → 404', async () => {
      const res = await supertest(app)
        .patch('/api/tasks/00000000-0000-0000-0000-000000000000')
        .set(authHeader())
        .send({ title: 'x' });
      expect(res.status).toBe(404);
    });

    // S2: Other user's task → 404
    it('PATCH other user task → 404', async () => {
      const tok = generateToken(OTHER_USER_ID);
      const res = await supertest(app)
        .patch(`/api/tasks/${patchTaskId}`)
        .set(authHeader(tok))
        .send({ title: 'Stolen' });
      expect(res.status).toBe(404);
    });

    // S1: XSS — HTML tags stripped from title
    it('PATCH strips HTML tags from title — 200, tag content preserved', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${patchTaskId}`)
        .set(authHeader())
        .send({ title: '<b>Bold</b>' });
      expect(res.status).toBe(200);
      expect(res.body.data.title).toBe('Bold');
    });

    // S1: XSS — script stripped from description
    it('PATCH strips script from description — 200', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${patchTaskId}`)
        .set(authHeader())
        .send({ description: '<script>x</script>' });
      expect(res.status).toBe(200);
      expect(res.body.data.description).toBe('x');
    });
  });

  // ── S1/S2 Ownership ─────────────────────────────────────

  describe('S1/S2 — Ownership', () => {
    let myTaskId: string;

    beforeAll(async () => {
      const res = await supertest(app)
        .post('/api/tasks')
        .set(authHeader())
        .send({ title: 'Private' });
      myTaskId = res.body.data.id;
    });

    it('other user cannot GET my task', async () => {
      const tok = generateToken(OTHER_USER_ID);
      const res = await supertest(app).get(`/api/tasks/${myTaskId}`).set(authHeader(tok));
      expect(res.status).toBe(404);
    });

    it('other user cannot UPDATE my task', async () => {
      const tok = generateToken(OTHER_USER_ID);
      const res = await supertest(app)
        .put(`/api/tasks/${myTaskId}`)
        .set(authHeader(tok))
        .send({ title: 'Stolen' });
      expect(res.status).toBe(404);
    });

    it('other user cannot DELETE my task', async () => {
      const tok = generateToken(OTHER_USER_ID);
      const res = await supertest(app).delete(`/api/tasks/${myTaskId}`).set(authHeader(tok));
      expect(res.status).toBe(404);
    });
  });

  // ── S3 Security Headers ─────────────────────────────────

  describe('S3 — Security Headers', () => {
    it('Helmet headers present', async () => {
      const res = await supertest(app).get('/api/tasks').set(authHeader());
      expect(res.headers['x-content-type-options']).toBe('nosniff');
    });
  });

  // ── S1 Error Sanitization ───────────────────────────────

  describe('S1 — Error Sanitization', () => {
    it('no stack traces', async () => {
      const res = await supertest(app).get('/api/tasks/not-a-uuid').set(authHeader());
      expect(res.status).toBe(400);
      expect(res.body.stack).toBeUndefined();
    });
  });

  // ── Pagination: Default (Cursor) Mode ───────────────────

  describe('Pagination — Default (Cursor) Mode', () => {
    beforeAll(async () => {
      // Clean slate + seed 7 tasks
      await pool.query('DELETE FROM tasks');
      for (let i = 0; i < 7; i++) {
        await supertest(app)
          .post('/api/tasks')
          .set(authHeader())
          .send({ title: `Cursor-P${i}` });
      }
    });

    it('default mode is cursor', async () => {
      const res = await supertest(app).get('/api/tasks?limit=3').set(authHeader());
      expect(res.status).toBe(200);
      expect(res.body.data).toHaveLength(3);
      // Cursor mode includes cursor field when hasMore=true
      expect(res.body.meta.cursor).toBeDefined();
      expect(res.body.meta.cursor).not.toBeNull();
      expect(res.body.meta.hasMore).toBe(true);
      expect(res.body.meta.total).toBe(7);
      expect(res.body.meta.page).toBe(1);
    });

    it('explicit mode=cursor works same as default', async () => {
      const res = await supertest(app).get('/api/tasks?mode=cursor&limit=3').set(authHeader());
      expect(res.status).toBe(200);
      expect(res.body.meta.cursor).toBeDefined();
      expect(res.body.data).toHaveLength(3);
    });

    it('cursor pagination: second page via cursor', async () => {
      const page1 = await supertest(app).get('/api/tasks?mode=cursor&limit=3').set(authHeader());
      expect(page1.status).toBe(200);
      expect(page1.body.meta.hasMore).toBe(true);
      const cursor = page1.body.meta.cursor;

      const page2 = await supertest(app)
        .get(`/api/tasks?mode=cursor&limit=3&cursor=${encodeURIComponent(cursor)}`)
        .set(authHeader());
      expect(page2.status).toBe(200);
      expect(page2.body.data).toHaveLength(3);

      // Verify no overlap between pages
      const page1Ids = page1.body.data.map((t: any) => t.id);
      const page2Ids = page2.body.data.map((t: any) => t.id);
      const overlap = page1Ids.filter((id: string) => page2Ids.includes(id));
      expect(overlap).toHaveLength(0);
    });

    it('cursor pagination: last page hasMore=false, no cursor', async () => {
      const page1 = await supertest(app).get('/api/tasks?mode=cursor&limit=6').set(authHeader());
      expect(page1.body.meta.hasMore).toBe(true);
      const cursor = page1.body.meta.cursor;

      const page2 = await supertest(app)
        .get(`/api/tasks?mode=cursor&limit=6&cursor=${encodeURIComponent(cursor)}`)
        .set(authHeader());
      expect(page2.status).toBe(200);
      expect(page2.body.data.length).toBeLessThanOrEqual(1);
      expect(page2.body.meta.hasMore).toBe(false);
      expect(page2.body.meta.cursor).toBeUndefined();
    });
  });

  // ── Pagination: Offset Mode ─────────────────────────────

  describe('Pagination — Offset Mode', () => {
    beforeAll(async () => {
      await pool.query('DELETE FROM tasks');
      for (let i = 0; i < 10; i++) {
        await supertest(app)
          .post('/api/tasks')
          .set(authHeader())
          .send({ title: `Offset-P${i}` });
      }
    });

    it('offset mode: first page', async () => {
      const res = await supertest(app)
        .get('/api/tasks?mode=offset&page=1&limit=4')
        .set(authHeader());
      expect(res.status).toBe(200);
      expect(res.body.data).toHaveLength(4);
      expect(res.body.meta.page).toBe(1);
      expect(res.body.meta.limit).toBe(4);
      expect(res.body.meta.total).toBe(10);
      expect(res.body.meta.hasMore).toBe(true);
      // Offset mode: no cursor field
      expect(res.body.meta.cursor).toBeUndefined();
    });

    it('offset mode: second page (page=2)', async () => {
      const res = await supertest(app)
        .get('/api/tasks?mode=offset&page=2&limit=4')
        .set(authHeader());
      expect(res.status).toBe(200);
      expect(res.body.data).toHaveLength(4);
      expect(res.body.meta.page).toBe(2);
      expect(res.body.meta.hasMore).toBe(true);
    });

    it('offset mode: last page hasMore=false', async () => {
      const res = await supertest(app)
        .get('/api/tasks?mode=offset&page=3&limit=4')
        .set(authHeader());
      expect(res.status).toBe(200);
      expect(res.body.data).toHaveLength(2); // 10 total, 8 dispensed, 2 remaining
      expect(res.body.meta.page).toBe(3);
      expect(res.body.meta.hasMore).toBe(false);
    });

    it('offset mode: page beyond range returns empty', async () => {
      const res = await supertest(app)
        .get('/api/tasks?mode=offset&page=100&limit=25')
        .set(authHeader());
      expect(res.status).toBe(200);
      expect(res.body.data).toHaveLength(0);
      expect(res.body.meta.hasMore).toBe(false);
      expect(res.body.meta.total).toBe(10);
    });

    it('offset mode: limit=100 works (max)', async () => {
      const res = await supertest(app)
        .get('/api/tasks?mode=offset&limit=100')
        .set(authHeader());
      expect(res.status).toBe(200);
      expect(res.body.data.length).toBe(10);
      expect(res.body.meta.hasMore).toBe(false);
    });
  });

  // ── Priority Filtering — Cursor Mode ─────────────────────

  describe('Priority Filtering — Cursor Mode', () => {
    beforeAll(async () => {
      await pool.query('DELETE FROM tasks');
      // 5 high, 3 low — 8 total
      const priorities = ['high', 'high', 'low', 'high', 'low', 'high', 'low', 'high'];
      for (let i = 0; i < priorities.length; i++) {
        await supertest(app)
          .post('/api/tasks')
          .set(authHeader())
          .send({ title: `Priority-C${i}`, priority: priorities[i] });
      }
    });

    it('filters by priority=high — returns only high-priority tasks', async () => {
      const res = await supertest(app)
        .get('/api/tasks?priority=high')
        .set(authHeader());
      expect(res.status).toBe(200);
      expect(res.body.data.length).toBeGreaterThan(0);
      res.body.data.forEach((t: any) => {
        expect(t.priority).toBe('high');
      });
    });

    it('meta.total reflects filtered count (high=5), not unfiltered (8)', async () => {
      const res = await supertest(app)
        .get('/api/tasks?priority=high')
        .set(authHeader());
      expect(res.status).toBe(200);
      expect(res.body.meta.total).toBe(5);
      expect(res.body.data).toHaveLength(5);
      expect(res.body.meta.hasMore).toBe(false);
    });

    it('meta.total reflects filtered count (low=3)', async () => {
      const res = await supertest(app)
        .get('/api/tasks?priority=low')
        .set(authHeader());
      expect(res.status).toBe(200);
      expect(res.body.meta.total).toBe(3);
      expect(res.body.data).toHaveLength(3);
      res.body.data.forEach((t: any) => {
        expect(t.priority).toBe('low');
      });
    });

    it('cursor pagination through filtered set: all pages sum to filtered total, no overlap', async () => {
      // 5 high-priority tasks, 2 per page → 3 pages
      const page1 = await supertest(app)
        .get('/api/tasks?priority=high&limit=2')
        .set(authHeader());
      expect(page1.status).toBe(200);
      expect(page1.body.data).toHaveLength(2);
      expect(page1.body.meta.total).toBe(5);
      expect(page1.body.meta.hasMore).toBe(true);
      expect(page1.body.meta.cursor).toBeDefined();

      const page2 = await supertest(app)
        .get(`/api/tasks?priority=high&limit=2&cursor=${encodeURIComponent(page1.body.meta.cursor)}`)
        .set(authHeader());
      expect(page2.status).toBe(200);
      expect(page2.body.data).toHaveLength(2);
      expect(page2.body.meta.total).toBe(5);
      expect(page2.body.meta.hasMore).toBe(true);

      const page3 = await supertest(app)
        .get(`/api/tasks?priority=high&limit=2&cursor=${encodeURIComponent(page2.body.meta.cursor)}`)
        .set(authHeader());
      expect(page3.status).toBe(200);
      expect(page3.body.data).toHaveLength(1);
      expect(page3.body.meta.total).toBe(5);
      expect(page3.body.meta.hasMore).toBe(false);

      // All pages have correct total and no overlap
      const page1Ids = page1.body.data.map((t: any) => t.id);
      const page2Ids = page2.body.data.map((t: any) => t.id);
      const page3Ids = page3.body.data.map((t: any) => t.id);
      expect(page1Ids.filter((id: string) => page2Ids.includes(id))).toHaveLength(0);
      expect(page1Ids.filter((id: string) => page3Ids.includes(id))).toHaveLength(0);
      expect(page2Ids.filter((id: string) => page3Ids.includes(id))).toHaveLength(0);
      expect(new Set([...page1Ids, ...page2Ids, ...page3Ids]).size).toBe(5);
    });

    it('empty result for priority with no matches', async () => {
      const res = await supertest(app)
        .get('/api/tasks?priority=medium')
        .set(authHeader());
      expect(res.status).toBe(200);
      expect(res.body.data).toHaveLength(0);
      expect(res.body.meta.total).toBe(0);
      expect(res.body.meta.hasMore).toBe(false);
    });
  });

  // ── Priority Filtering — Offset Mode ─────────────────────

  describe('Priority Filtering — Offset Mode', () => {
    beforeAll(async () => {
      await pool.query('DELETE FROM tasks');
      // 6 low, 3 medium, 1 high — 10 total
      const priorities = ['low', 'low', 'medium', 'low', 'high', 'low', 'medium', 'low', 'medium', 'low'];
      for (let i = 0; i < priorities.length; i++) {
        await supertest(app)
          .post('/api/tasks')
          .set(authHeader())
          .send({ title: `Offset-Prio-${i}`, priority: priorities[i] });
      }
    });

    it('filters by priority=low in offset mode', async () => {
      const res = await supertest(app)
        .get('/api/tasks?mode=offset&priority=low')
        .set(authHeader());
      expect(res.status).toBe(200);
      res.body.data.forEach((t: any) => {
        expect(t.priority).toBe('low');
      });
    });

    it('meta.total reflects filtered count in offset mode (low=6)', async () => {
      const res = await supertest(app)
        .get('/api/tasks?mode=offset&priority=low')
        .set(authHeader());
      expect(res.status).toBe(200);
      expect(res.body.meta.total).toBe(6);
      expect(res.body.data).toHaveLength(6);
    });

    it('meta.total reflects filtered count in offset mode (medium=3)', async () => {
      const res = await supertest(app)
        .get('/api/tasks?mode=offset&priority=medium')
        .set(authHeader());
      expect(res.status).toBe(200);
      expect(res.body.meta.total).toBe(3);
    });

    it('offset pagination through filtered set: page 2 of low-priority', async () => {
      // 6 low-priority, 3 per page → 2 pages
      const page1 = await supertest(app)
        .get('/api/tasks?mode=offset&priority=low&page=1&limit=3')
        .set(authHeader());
      expect(page1.status).toBe(200);
      expect(page1.body.data).toHaveLength(3);
      expect(page1.body.meta.total).toBe(6);
      expect(page1.body.meta.hasMore).toBe(true);
      expect(page1.body.meta.cursor).toBeUndefined(); // offset mode: no cursor

      const page2 = await supertest(app)
        .get('/api/tasks?mode=offset&priority=low&page=2&limit=3')
        .set(authHeader());
      expect(page2.status).toBe(200);
      expect(page2.body.data).toHaveLength(3);
      expect(page2.body.meta.total).toBe(6);
      expect(page2.body.meta.hasMore).toBe(false);

      // No overlap
      const page1Ids = page1.body.data.map((t: any) => t.id);
      const page2Ids = page2.body.data.map((t: any) => t.id);
      const overlap = page1Ids.filter((id: string) => page2Ids.includes(id));
      expect(overlap).toHaveLength(0);
    });

    it('offset pagination: page beyond filtered range returns empty with correct total', async () => {
      const res = await supertest(app)
        .get('/api/tasks?mode=offset&priority=medium&page=10&limit=25')
        .set(authHeader());
      expect(res.status).toBe(200);
      expect(res.body.data).toHaveLength(0);
      expect(res.body.meta.total).toBe(3); // filtered total, even when page is empty
      expect(res.body.meta.hasMore).toBe(false);
    });
  });

  // ── Priority Filtering — Validation ──────────────────────

  describe('Priority Filtering — Validation', () => {
    it('rejects invalid priority value', async () => {
      const res = await supertest(app)
        .get('/api/tasks?priority=critical')
        .set(authHeader());
      expect(res.status).toBe(400);
    });

    it('rejects empty priority string', async () => {
      const res = await supertest(app)
        .get('/api/tasks?priority=')
        .set(authHeader());
      expect(res.status).toBe(400);
    });
  });

  // ── Pagination: Legacy (no mode param, defaults to cursor) ──

  describe('Pagination — Legacy (no mode param)', () => {
    it('rejects limit > 100', async () => {
      const res = await supertest(app).get('/api/tasks?limit=101').set(authHeader());
      expect(res.status).toBe(400);
    });
  });
});
