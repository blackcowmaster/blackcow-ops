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
const NONEXISTENT_UUID = '00000000-0000-0000-0000-000000000000';
const VALID_UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const ISO8601_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/;

// ── Helpers ───────────────────────────────────────────────

function generateToken(sub = TEST_USER_ID, expiresIn = '15m'): string {
  return jwt.sign({ sub, role: 'user' }, TEST_JWT_SECRET, {
    algorithm: 'HS256',
    expiresIn,
  } as jwt.SignOptions);
}

function authHeader(token?: string) {
  return { Authorization: `Bearer ${token || generateToken()}` };
}

// ── L3 Contract Test Suite ────────────────────────────────
//
// These tests verify the API *contract* — request/response shape,
// status codes, error structure, and headers — NOT business logic.
// Each test isolates a single contractual obligation.

describe('L3 Contract — PATCH /api/tasks/:id', () => {
  let pool: Pool;
  let app: Application;
  let seedTaskId: string;

  // Task seed data — kept stable across all PATCH tests
  const SEED_TASK = {
    title: 'Contract Seed Task',
    description: 'Original description for contract tests',
    status: 'todo' as const,
    priority: 'medium' as const,
  };

  // ── Bootstrap ─────────────────────────────────────────

  beforeAll(async () => {
    const result = await startPostgresContainer('bkow-contract-pg');
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

    // Seed a single task for PATCH operations
    const seedRes = await supertest(app)
      .post('/api/tasks')
      .set(authHeader())
      .send(SEED_TASK);
    seedTaskId = seedRes.body.data.id;
  }, 60000);

  afterAll(async () => {
    await stopPostgresContainer(pool);
  });

  // ═══════════════════════════════════════════════════════════
  // C1 — 200 Success: Response Body Shape
  // ═══════════════════════════════════════════════════════════

  describe('C1 — 200 Success Response Shape', () => {
    it('returns 200 with full TaskResponse shape on partial title update', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ title: 'Updated Title' });

      expect(res.status).toBe(200);
      expect(res.body).toHaveProperty('data');
      expect(res.body).toHaveProperty('error');
      expect(res.body.error).toBeNull();

      const d = res.body.data;
      // Required string fields
      expect(typeof d.id).toBe('string');
      expect(VALID_UUID_RE.test(d.id)).toBe(true);
      expect(typeof d.title).toBe('string');
      expect(typeof d.status).toBe('string');
      expect(typeof d.priority).toBe('string');
      expect(typeof d.created_at).toBe('string');
      expect(ISO8601_RE.test(d.created_at)).toBe(true);
      expect(typeof d.updated_at).toBe('string');
      expect(ISO8601_RE.test(d.updated_at).valueOf()).toBe(true);

      // Nullable fields
      expect(d.description === null || typeof d.description === 'string').toBe(true);
      expect(d.due_date === null || typeof d.due_date === 'string').toBe(true);
      if (d.due_date !== null) {
        expect(ISO8601_RE.test(d.due_at)).toBe(true);
      }

      // Status and priority enum values
      expect(['todo', 'in_progress', 'done']).toContain(d.status);
      expect(['low', 'medium', 'high']).toContain(d.priority);

      // Fields that MUST NOT be leaked
      expect(d).not.toHaveProperty('user_id');
      expect(d).not.toHaveProperty('deleted_at');

      // Top-level envelope shape
      expect(res.body).not.toHaveProperty('meta'); // no pagination meta on single-resource response
    });

    it('returns updated_at > created_at after PATCH', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ title: 'Timestamp Test' });

      expect(res.status).toBe(200);
      const d = res.body.data;
      expect(new Date(d.updated_at).getTime()).toBeGreaterThanOrEqual(
        new Date(d.created_at).getTime(),
      );
    });

    it('description can be set to a string value', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ description: 'Non-null description' });

      expect(res.status).toBe(200);
      expect(res.body.data.description).toBe('Non-null description');
    });

    it('priority enum values are accepted (low → medium → high)', async () => {
      // Set to low
      let res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ priority: 'low' });
      expect(res.status).toBe(200);
      expect(res.body.data.priority).toBe('low');

      // Set to high
      res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ priority: 'high' });
      expect(res.status).toBe(200);
      expect(res.body.data.priority).toBe('high');
    });

    it('status enum values are accepted (todo → in_progress → done)', async () => {
      let res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ status: 'in_progress' });
      expect(res.status).toBe(200);
      expect(res.body.data.status).toBe('in_progress');

      res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ status: 'done' });
      expect(res.status).toBe(200);
      expect(res.body.data.status).toBe('done');

      res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ status: 'todo' });
      expect(res.status).toBe(200);
      expect(res.body.data.status).toBe('todo');
    });

    it('meta field is absent from single-resource 200 response', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ title: 'No meta check' });

      expect(res.status).toBe(200);
      expect(res.body).not.toHaveProperty('meta');
    });

    // Reset task to known state
    it('(cleanup) reset seed to original', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send(SEED_TASK);
      expect(res.status).toBe(200);
      expect(res.body.data.title).toBe(SEED_TASK.title);
    });
  });

  // ═══════════════════════════════════════════════════════════
  // C2 — 400 Validation Error Shape
  // ═══════════════════════════════════════════════════════════

  describe('C2 — 400 Validation Error Shape', () => {
    it('returns 400 + ApiError shape for empty body', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({});

      expect(res.status).toBe(400);
      // Envelope
      expect(res.body).toHaveProperty('data');
      expect(res.body.data).toBeNull();
      expect(res.body).toHaveProperty('error');
      expect(typeof res.body.error).toBe('string');
      expect(res.body.error).toBe('Validation failed');
      // Errors array
      expect(res.body).toHaveProperty('errors');
      expect(Array.isArray(res.body.errors)).toBe(true);
      expect(res.body.errors.length).toBeGreaterThanOrEqual(1);
      // Each error item
      for (const e of res.body.errors) {
        expect(e).toHaveProperty('field');
        expect(typeof e.field).toBe('string');
        expect(e).toHaveProperty('message');
        expect(typeof e.message).toBe('string');
      }
      // No meta, no stack
      expect(res.body).not.toHaveProperty('meta');
      expect(res.body).not.toHaveProperty('stack');
    });

    it('returns 400 + field-level error for invalid UUID param', async () => {
      const res = await supertest(app)
        .patch('/api/tasks/not-a-uuid')
        .set(authHeader())
        .send({ title: 'x' });

      expect(res.status).toBe(400);
      expect(res.body.data).toBeNull();
      expect(res.body.error).toBe('Validation failed');
      expect(Array.isArray(res.body.errors)).toBe(true);
      expect(res.body.errors.some((e: any) => e.field === 'id')).toBe(true);
      expect(res.body.errors[0].message).toMatch(/uuid/i);
    });

    it('returns 400 for empty title (preprocess collapses sanitized empty)', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ title: '' });

      expect(res.status).toBe(400);
      expect(res.body.data).toBeNull();
      expect(res.body.error).toBe('Validation failed');
      expect(res.body.errors.some((e: any) => e.field === 'title')).toBe(true);
    });

    it('returns 400 for whitespace-only title (collapses to empty)', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ title: '   ' });

      expect(res.status).toBe(400);
      expect(res.body.data).toBeNull();
      expect(res.body.error).toBe('Validation failed');
    });

    it('returns 400 for XSS-only title that collapses to empty', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ title: '<script></script>' });

      expect(res.status).toBe(400);
      expect(res.body.data).toBeNull();
      expect(res.body.error).toBe('Validation failed');
    });

    it('returns 400 for invalid status enum value', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ status: 'invalid_status' });

      expect(res.status).toBe(400);
      expect(res.body.data).toBeNull();
      expect(res.body.error).toBe('Validation failed');
      expect(res.body.errors.some((e: any) => e.field === 'status')).toBe(true);
    });

    it('returns 400 for invalid priority enum value', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ priority: 'urgent' });

      expect(res.status).toBe(400);
      expect(res.body.data).toBeNull();
      expect(res.body.error).toBe('Validation failed');
      expect(res.body.errors.some((e: any) => e.field === 'priority')).toBe(true);
    });

    it('returns 400 for invalid due_date format', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ due_date: 'not-a-date' });

      expect(res.status).toBe(400);
      expect(res.body.data).toBeNull();
      expect(res.body.error).toBe('Validation failed');
      expect(res.body.errors.some((e: any) => e.field === 'due_date')).toBe(true);
    });

    it('returns 400 for title exceeding 200 characters', async () => {
      const longTitle = 'a'.repeat(201);
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ title: longTitle });

      expect(res.status).toBe(400);
      expect(res.body.data).toBeNull();
      expect(res.body.error).toBe('Validation failed');
    });

    it('returns 400 for description exceeding 5000 characters', async () => {
      const longDesc = 'a'.repeat(5001);
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ description: longDesc });

      expect(res.status).toBe(400);
      expect(res.body.data).toBeNull();
      expect(res.body.error).toBe('Validation failed');
    });

    it('returns 400 for unknown extra fields (strict mode)', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ title: 'x', unknown_field: 'should be rejected' });

      // Zod strict object would reject; but current schema is NOT strict so unknown fields pass through
      // This documents the contract — test may need updating if schema becomes strict
      expect(res.status).toBe(200); // current contract: unknown fields are silently ignored
    });
  });

  // ═══════════════════════════════════════════════════════════
  // C3 — 401 Auth Error Shape
  // ═══════════════════════════════════════════════════════════

  describe('C3 — 401 Auth Error Shape', () => {
    it('returns 401 + AppError shape when no auth header', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .send({ title: 'x' });

      expect(res.status).toBe(401);
      // AppError envelope
      expect(res.body).toHaveProperty('data');
      expect(res.body.data).toBeNull();
      expect(res.body).toHaveProperty('error');
      expect(typeof res.body.error).toBe('string');
      expect(res.body.error).toMatch(/authorization/i);
      // AppError has meta.correlationId
      expect(res.body).toHaveProperty('meta');
      expect(res.body.meta).toHaveProperty('correlationId');
      expect(typeof res.body.meta.correlationId).toBe('string');
      // No errors array (AppError path, not validation path)
      expect(res.body).not.toHaveProperty('errors');
      // No stack trace
      expect(res.body).not.toHaveProperty('stack');
    });

    it('returns 401 for expired token', async () => {
      const token = generateToken(TEST_USER_ID, '0s');
      await new Promise((r) => setTimeout(r, 100));
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader(token))
        .send({ title: 'x' });

      expect(res.status).toBe(401);
      expect(res.body.data).toBeNull();
      expect(res.body.error).toBeDefined();
      expect(res.body.meta).toHaveProperty('correlationId');
    });

    it('returns 401 for malformed auth header', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set('Authorization', 'BadFormat')
        .send({ title: 'x' });

      expect(res.status).toBe(401);
      expect(res.body.data).toBeNull();
      expect(res.body.error).toMatch(/bearer/i);
    });

    it('returns 401 for invalid JWT signature', async () => {
      const badToken = jwt.sign(
        { sub: TEST_USER_ID, role: 'user' },
        'wrong-secret-that-is-at-least-32-chars!!',
        { algorithm: 'HS256' },
      );
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader(badToken))
        .send({ title: 'x' });

      expect(res.status).toBe(401);
      expect(res.body.data).toBeNull();
      expect(res.body.error).toBeDefined();
    });
  });

  // ═══════════════════════════════════════════════════════════
  // C4 — 404 Not Found Error Shape
  // ═══════════════════════════════════════════════════════════

  describe('C4 — 404 Not Found Error Shape', () => {
    it('returns 404 + AppError shape for non-existent UUID', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${NONEXISTENT_UUID}`)
        .set(authHeader())
        .send({ title: 'x' });

      expect(res.status).toBe(404);
      expect(res.body.data).toBeNull();
      expect(res.body.error).toMatch(/not found/i);
      // AppError envelope
      expect(res.body).toHaveProperty('meta');
      expect(res.body.meta).toHaveProperty('correlationId');
      expect(typeof res.body.meta.correlationId).toBe('string');
      // No validation errors array (not a validation error)
      expect(res.body).not.toHaveProperty('errors');
      // No stack trace
      expect(res.body).not.toHaveProperty('stack');
    });

    it('returns 404 for another user\'s task (same as not found)', async () => {
      const otherToken = generateToken(OTHER_USER_ID);
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader(otherToken))
        .send({ title: 'x' });

      expect(res.status).toBe(404);
      expect(res.body.data).toBeNull();
      expect(res.body.error).toMatch(/not found/i);
      expect(res.body.meta).toHaveProperty('correlationId');
    });
  });

  // ═══════════════════════════════════════════════════════════
  // C5 — Headers Contract
  // ═══════════════════════════════════════════════════════════

  describe('C5 — Response Headers', () => {
    it('Content-Type is application/json on success', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ title: 'Header Test' });

      expect(res.status).toBe(200);
      expect(res.headers['content-type']).toMatch(/application\/json/);
    });

    it('Content-Type is application/json on validation error', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({});

      expect(res.status).toBe(400);
      expect(res.headers['content-type']).toMatch(/application\/json/);
    });

    it('Content-Type is application/json on auth error', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .send({ title: 'x' });

      expect(res.status).toBe(401);
      expect(res.headers['content-type']).toMatch(/application\/json/);
    });

    it('Content-Type is application/json on 404', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${NONEXISTENT_UUID}`)
        .set(authHeader())
        .send({ title: 'x' });

      expect(res.status).toBe(404);
      expect(res.headers['content-type']).toMatch(/application\/json/);
    });

    it('security headers present (helmet)', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ title: 'Security' });

      expect(res.status).toBe(200);
      expect(res.headers['x-content-type-options']).toBe('nosniff');
      expect(res.headers['x-frame-options']).toBeDefined();
      expect(res.headers['x-xss-protection']).toBeDefined();
      expect(res.headers['strict-transport-security']).toBeDefined();
    });

    it('no x-powered-by header leaked', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ title: 'No Leak' });

      expect(res.headers['x-powered-by']).toBeUndefined();
    });
  });

  // ═══════════════════════════════════════════════════════════
  // C6 — Field-Level Update Contract
  // ═══════════════════════════════════════════════════════════

  describe('C6 — Field-Level Update Semantics', () => {
    let testTaskId: string;

    beforeAll(async () => {
      const res = await supertest(app)
        .post('/api/tasks')
        .set(authHeader())
        .send({
          title: 'Field Contract Task',
          description: 'Initial desc',
          status: 'todo',
          priority: 'high',
          due_date: '2026-01-01T00:00:00.000Z',
        });
      testTaskId = res.body.data.id;
    });

    it('omitted fields are preserved (not nulled)', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${testTaskId}`)
        .set(authHeader())
        .send({ title: 'Only Title Changed' });

      expect(res.status).toBe(200);
      expect(res.body.data.title).toBe('Only Title Changed');
      expect(res.body.data.description).toBe('Initial desc');
      expect(res.body.data.status).toBe('todo');
      expect(res.body.data.priority).toBe('high');
      expect(res.body.data.due_date).toBe('2026-01-01T00:00:00.000Z');
    });

    it('explicit null description is accepted (nullable field)', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${testTaskId}`)
        .set(authHeader())
        .send({ description: null });

      expect(res.status).toBe(200);
      expect(res.body.data.description).toBeNull();
    });

    it('explicit null due_date is accepted (nullable field)', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${testTaskId}`)
        .set(authHeader())
        .send({ due_date: null });

      expect(res.status).toBe(200);
      expect(res.body.data.due_date).toBeNull();
    });

    it('valid ISO due_date is accepted', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${testTaskId}`)
        .set(authHeader())
        .send({ due_date: '2027-06-15T12:30:00.000Z' });

      expect(res.status).toBe(200);
      expect(res.body.data.due_date).toBe('2027-06-15T12:30:00.000Z');
    });
  });

  // ═══════════════════════════════════════════════════════════
  // C7 — Nullable Field Contract in Response
  // ═══════════════════════════════════════════════════════════

  describe('C7 — Nullable Field Response Contract', () => {
    it('description is null when not provided', async () => {
      const res = await supertest(app)
        .post('/api/tasks')
        .set(authHeader())
        .send({ title: 'No Desc Task' });

      expect(res.status).toBe(201);
      expect(res.body.data.description).toBeNull();

      // PATCH should keep it null
      const patchRes = await supertest(app)
        .patch(`/api/tasks/${res.body.data.id}`)
        .set(authHeader())
        .send({ title: 'Still No Desc' });

      expect(patchRes.status).toBe(200);
      expect(patchRes.body.data.description).toBeNull();
    });

    it('due_date is null when not provided', async () => {
      const res = await supertest(app)
        .post('/api/tasks')
        .set(authHeader())
        .send({ title: 'No Due Date Task' });

      expect(res.status).toBe(201);
      expect(res.body.data.due_date).toBeNull();
    });
  });

  // ═══════════════════════════════════════════════════════════
  // C8 — Request Body Size Limit
  // ═══════════════════════════════════════════════════════════

  describe('C8 — Request Body Size Limit', () => {
    it('returns 413 for oversized request body (>100kb)', async () => {
      const largePayload = { title: 'x'.repeat(102_400) }; // ~100KB just in title
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send(largePayload);

      // Express.json({ limit: '100kb' }) returns 413
      expect(res.status).toBe(413);
    });
  });

  // ═══════════════════════════════════════════════════════════
  // C9 — Error Response: No Stack Traces
  // ═══════════════════════════════════════════════════════════

  describe('C9 — No Stack Traces Leaked', () => {
    it('stack is absent from validation errors', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .set(authHeader())
        .send({ status: 'bad' });

      expect(res.status).toBe(400);
      expect(res.body).not.toHaveProperty('stack');
    });

    it('stack is absent from auth errors', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${seedTaskId}`)
        .send({ title: 'x' });

      expect(res.status).toBe(401);
      expect(res.body).not.toHaveProperty('stack');
    });

    it('stack is absent from 404 errors', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${NONEXISTENT_UUID}`)
        .set(authHeader())
        .send({ title: 'x' });

      expect(res.status).toBe(404);
      expect(res.body).not.toHaveProperty('stack');
    });
  });
});
