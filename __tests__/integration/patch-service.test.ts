import path from 'path';
import { Pool } from 'pg';
import jwt from 'jsonwebtoken';
import supertest from 'supertest';
import type { Application } from 'express';
import { startPostgresContainer, stopPostgresContainer, runMigration } from '../test-helpers';
import { tasksService } from '../../src/services/tasks.service';
import { tasksRepository } from '../../src/repositories/tasks.repository';
import { Task } from '../../src/types/task';

const TEST_JWT_SECRET = 'test-secret-that-is-at-least-32-characters-long!!';
const TEST_USER_ID = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
const OTHER_USER_ID = 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22';

function generateToken(sub = TEST_USER_ID): string {
  return jwt.sign({ sub, role: 'user' }, TEST_JWT_SECRET, {
    algorithm: 'HS256',
    expiresIn: '15m',
  } as jwt.SignOptions);
}

function authHeader(token?: string) {
  return { Authorization: `Bearer ${token || generateToken()}` };
}

const MOCK_NOW = '2026-06-27T12:00:00.000Z';

function makeMockTask(overrides: Partial<Task> = {}): Task {
  return {
    id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a01',
    user_id: TEST_USER_ID,
    title: 'Original Title',
    description: 'Original description',
    status: 'todo',
    priority: 'medium',
    due_date: null,
    created_at: MOCK_NOW,
    updated_at: MOCK_NOW,
    deleted_at: null,
    ...overrides,
  };
}

// =================================================================
// SECTION 1: Service-level tests — tasksService.update with
//            mocked repository (partial DTO, ownership, edge cases)
// =================================================================

describe('Patch — Service Layer (mocked repository)', () => {
  let findByIdSpy: jest.SpyInstance;
  let updateSpy: jest.SpyInstance;

  beforeEach(() => {
    findByIdSpy = jest.spyOn(tasksRepository, 'findById');
    updateSpy = jest.spyOn(tasksRepository, 'update');
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  // ── Partial DTO shapes ────────────────────────────────

  it('updates title only — partial DTO', async () => {
    const existing = makeMockTask();
    findByIdSpy.mockResolvedValue(existing);
    updateSpy.mockResolvedValue({ ...existing, title: 'New Title' });

    const result = await tasksService.update(existing.id, TEST_USER_ID, { title: 'New Title' });

    expect(result.title).toBe('New Title');
    expect(result.description).toBe('Original description'); // unchanged
    expect(updateSpy).toHaveBeenCalledWith(existing.id, TEST_USER_ID, { title: 'New Title' });
  });

  it('updates description only — partial DTO', async () => {
    const existing = makeMockTask();
    findByIdSpy.mockResolvedValue(existing);
    updateSpy.mockResolvedValue({ ...existing, description: 'New desc' });

    const result = await tasksService.update(existing.id, TEST_USER_ID, { description: 'New desc' });

    expect(result.description).toBe('New desc');
    expect(result.title).toBe('Original Title'); // unchanged
    expect(updateSpy).toHaveBeenCalledWith(existing.id, TEST_USER_ID, { description: 'New desc' });
  });

  it('updates status only — partial DTO', async () => {
    const existing = makeMockTask();
    findByIdSpy.mockResolvedValue(existing);
    updateSpy.mockResolvedValue({ ...existing, status: 'done' });

    const result = await tasksService.update(existing.id, TEST_USER_ID, { status: 'done' });

    expect(result.status).toBe('done');
    expect(result.title).toBe('Original Title'); // unchanged
    expect(updateSpy).toHaveBeenCalledWith(existing.id, TEST_USER_ID, { status: 'done' });
  });

  it('updates priority only — partial DTO', async () => {
    const existing = makeMockTask();
    findByIdSpy.mockResolvedValue(existing);
    updateSpy.mockResolvedValue({ ...existing, priority: 'high' });

    const result = await tasksService.update(existing.id, TEST_USER_ID, { priority: 'high' });

    expect(result.priority).toBe('high');
    expect(updateSpy).toHaveBeenCalledWith(existing.id, TEST_USER_ID, { priority: 'high' });
  });

  it('updates due_date only — partial DTO', async () => {
    const existing = makeMockTask();
    const futureDate = '2026-12-31T23:59:59.000Z';
    findByIdSpy.mockResolvedValue(existing);
    updateSpy.mockResolvedValue({ ...existing, due_date: futureDate });

    const result = await tasksService.update(existing.id, TEST_USER_ID, { due_date: futureDate });

    expect(result.due_date).toBe(futureDate);
    expect(updateSpy).toHaveBeenCalledWith(existing.id, TEST_USER_ID, { due_date: futureDate });
  });

  it('updates multiple fields simultaneously — partial DTO', async () => {
    const existing = makeMockTask();
    findByIdSpy.mockResolvedValue(existing);
    updateSpy.mockResolvedValue({
      ...existing,
      title: 'Multi',
      status: 'in_progress',
      priority: 'high',
    });

    const result = await tasksService.update(existing.id, TEST_USER_ID, {
      title: 'Multi',
      status: 'in_progress',
      priority: 'high',
    });

    expect(result.title).toBe('Multi');
    expect(result.status).toBe('in_progress');
    expect(result.priority).toBe('high');
    expect(result.description).toBe('Original description'); // unchanged
    expect(updateSpy).toHaveBeenCalledWith(existing.id, TEST_USER_ID, {
      title: 'Multi',
      status: 'in_progress',
      priority: 'high',
    });
  });

  // ── Error paths ───────────────────────────────────────

  it('throws 404 when findById returns null (task not found)', async () => {
    findByIdSpy.mockResolvedValue(null);

    await expect(
      tasksService.update('00000000-0000-0000-0000-000000000000', TEST_USER_ID, { title: 'x' }),
    ).rejects.toMatchObject({ statusCode: 404, code: 'NOT_FOUND' });

    expect(updateSpy).not.toHaveBeenCalled();
  });

  it('throws 403 when task.user_id !== userId (ownership violation)', async () => {
    const existing = makeMockTask({ user_id: OTHER_USER_ID });
    findByIdSpy.mockResolvedValue(existing);

    await expect(
      tasksService.update(existing.id, TEST_USER_ID, { title: 'Stolen' }),
    ).rejects.toMatchObject({ statusCode: 403, code: 'FORBIDDEN' });

    expect(updateSpy).not.toHaveBeenCalled();
  });

  it('throws 404 when findById succeeds but update returns null (race / concurrent delete)', async () => {
    const existing = makeMockTask();
    findByIdSpy.mockResolvedValue(existing);
    updateSpy.mockResolvedValue(null); // concurrent deletion

    await expect(
      tasksService.update(existing.id, TEST_USER_ID, { title: 'x' }),
    ).rejects.toMatchObject({ statusCode: 404, code: 'NOT_FOUND' });
  });

  it('passes the exact DTO through to repository.update (no extra fields)', async () => {
    const existing = makeMockTask();
    findByIdSpy.mockResolvedValue(existing);
    updateSpy.mockResolvedValue(existing);

    await tasksService.update(existing.id, TEST_USER_ID, { description: 'Just desc' });

    expect(updateSpy).toHaveBeenCalledWith(existing.id, TEST_USER_ID, { description: 'Just desc' });
    const callDto = updateSpy.mock.calls[0][2];
    expect(Object.keys(callDto)).toEqual(['description']);
  });
});

// =================================================================
// Sections 2 & 3 share one PostgreSQL container for real-DB tests.
// Section 2: Repository-level dynamic SET clause behavior.
// Section 3: Cross-verb PATCH→GET persistence via supertest.
// =================================================================

describe('Patch — Real Database', () => {
  let pool: Pool;
  let app: Application;
  let repo: any;

  beforeAll(async () => {
    const result = await startPostgresContainer('bkow-test-pg-patch');
    pool = result.pool;

    process.env.DATABASE_URL = result.dbUrl;
    process.env.JWT_SECRET = TEST_JWT_SECRET;
    process.env.JWT_EXPIRY = '15m';
    process.env.ALLOWED_ORIGINS = '*';

    const migrationPath = path.join(
      __dirname, '..', '..', 'src', 'lib', 'db', 'migrations', '001_create_tasks.sql',
    );
    await runMigration(pool, migrationPath);

    // Import app for supertest (cross-verb tests)
    const appMod = await import('../../src/app');
    app = appMod.app;

    // Import repository class directly for repo-level tests
    const repoMod = await import('../../src/repositories/tasks.repository');
    repo = new repoMod.TasksRepository();
  }, 60000);

  afterAll(async () => {
    await stopPostgresContainer(pool);
  });

  // ===============================================================
  // SECTION 2: Repository-level — dynamic SET clause behavior
  //            with various DTO shapes
  // ===============================================================

  describe('Repository Layer (dynamic SET clause)', () => {
    let baseTaskId: string;

    beforeEach(async () => {
      await pool.query('DELETE FROM tasks');
      const task = await repo.create(
        { title: 'Base', description: 'Base desc', status: 'todo', priority: 'medium' },
        TEST_USER_ID,
      );
      baseTaskId = task.id;
    });

    // ── Single-field updates ──────────────────────────────

    it('title only — only title column changes', async () => {
      const updated = await repo.update(baseTaskId, TEST_USER_ID, { title: 'New Title' });
      expect(updated.title).toBe('New Title');
      expect(updated.description).toBe('Base desc');
      expect(updated.status).toBe('todo');
      expect(updated.priority).toBe('medium');
      expect(updated.due_date).toBeNull();
    });

    it('description only — only description column changes', async () => {
      const updated = await repo.update(baseTaskId, TEST_USER_ID, { description: 'New desc' });
      expect(updated.description).toBe('New desc');
      expect(updated.title).toBe('Base');
      expect(updated.status).toBe('todo');
      expect(updated.priority).toBe('medium');
    });

    it('status only — only status column changes', async () => {
      const updated = await repo.update(baseTaskId, TEST_USER_ID, { status: 'done' });
      expect(updated.status).toBe('done');
      expect(updated.title).toBe('Base');
      expect(updated.description).toBe('Base desc');
      expect(updated.priority).toBe('medium');
    });

    it('priority only — only priority column changes', async () => {
      const updated = await repo.update(baseTaskId, TEST_USER_ID, { priority: 'high' });
      expect(updated.priority).toBe('high');
      expect(updated.title).toBe('Base');
      expect(updated.status).toBe('todo');
    });

    it('due_date only — only due_date column changes', async () => {
      const futureDate = '2026-12-31T23:59:59.000Z';
      const updated = await repo.update(baseTaskId, TEST_USER_ID, { due_date: futureDate });
      // PostgreSQL returns timestamptz as Date; normalize for comparison
      expect(new Date(updated.due_date).toISOString()).toBe(futureDate);
      expect(updated.title).toBe('Base');
      expect(updated.status).toBe('todo');
    });

    // ── All-fields update ─────────────────────────────────

    it('all fields simultaneously — every column updates', async () => {
      const futureDate = '2027-01-15T08:00:00.000Z';
      const updated = await repo.update(baseTaskId, TEST_USER_ID, {
        title: 'Full Update',
        description: 'Full desc replacement',
        status: 'done',
        priority: 'low',
        due_date: futureDate,
      });

      expect(updated.title).toBe('Full Update');
      expect(updated.description).toBe('Full desc replacement');
      expect(updated.status).toBe('done');
      expect(updated.priority).toBe('low');
      expect(new Date(updated.due_date).toISOString()).toBe(futureDate);
    });

    // ── Empty DTO → null ──────────────────────────────────

    it('empty DTO (no fields) returns null — no SQL executed', async () => {
      const result = await repo.update(baseTaskId, TEST_USER_ID, {});
      expect(result).toBeNull();
    });

    // ── updated_at advances ───────────────────────────────

    it('updated_at timestamp advances after update', async () => {
      await new Promise((r) => setTimeout(r, 50)); // ensure time advances
      const updated = await repo.update(baseTaskId, TEST_USER_ID, { title: 'Time test' });
      expect(new Date(updated.updated_at).getTime()).toBeGreaterThan(
        new Date(updated.created_at).getTime(),
      );
    });

    // ── Ownership isolation ───────────────────────────────

    it('update returns null for other user task', async () => {
      const result = await repo.update(baseTaskId, OTHER_USER_ID, { title: 'Stolen' });
      expect(result).toBeNull();

      // Verify the original is untouched
      const unchanged = await repo.findById(baseTaskId, TEST_USER_ID);
      expect(unchanged.title).toBe('Base');
    });
  });

  // ===============================================================
  // SECTION 3: Cross-verb consistency — PATCH then GET to verify
  //            persistence through the full HTTP stack
  // ===============================================================

  describe('Cross-verb Persistence (PATCH then GET)', () => {
    let taskId: string;

    beforeEach(async () => {
      await pool.query('DELETE FROM tasks');
      const res = await supertest(app)
        .post('/api/tasks')
        .set(authHeader())
        .send({ title: 'Persist Me', description: 'Initial desc', status: 'todo', priority: 'low' });
      taskId = res.body.data.id;
    });

    // ── Single-field persistence ──────────────────────────

    it('PATCH title → GET confirms title updated, rest unchanged', async () => {
      const patchRes = await supertest(app)
        .patch(`/api/tasks/${taskId}`)
        .set(authHeader())
        .send({ title: 'Persisted Title' });
      expect(patchRes.status).toBe(200);
      expect(patchRes.body.data.title).toBe('Persisted Title');

      // Cross-verb verification: GET immediately after
      const getRes = await supertest(app).get(`/api/tasks/${taskId}`).set(authHeader());
      expect(getRes.status).toBe(200);
      expect(getRes.body.data.title).toBe('Persisted Title');
      expect(getRes.body.data.description).toBe('Initial desc');
      expect(getRes.body.data.status).toBe('todo');
      expect(getRes.body.data.priority).toBe('low');
    });

    it('PATCH description → GET confirms description updated, rest unchanged', async () => {
      const patchRes = await supertest(app)
        .patch(`/api/tasks/${taskId}`)
        .set(authHeader())
        .send({ description: 'Persisted desc' });
      expect(patchRes.status).toBe(200);

      const getRes = await supertest(app).get(`/api/tasks/${taskId}`).set(authHeader());
      expect(getRes.body.data.description).toBe('Persisted desc');
      expect(getRes.body.data.title).toBe('Persist Me');
      expect(getRes.body.data.status).toBe('todo');
      expect(getRes.body.data.priority).toBe('low');
    });

    // ── Multi-field persistence ───────────────────────────

    it('PATCH title + status + priority → GET confirms all three', async () => {
      const patchRes = await supertest(app)
        .patch(`/api/tasks/${taskId}`)
        .set(authHeader())
        .send({ title: 'Triple', status: 'done', priority: 'high' });
      expect(patchRes.status).toBe(200);

      const getRes = await supertest(app).get(`/api/tasks/${taskId}`).set(authHeader());
      expect(getRes.body.data.title).toBe('Triple');
      expect(getRes.body.data.status).toBe('done');
      expect(getRes.body.data.priority).toBe('high');
      expect(getRes.body.data.description).toBe('Initial desc'); // untouched
    });

    // ── updated_at advances (verified via GET) ────────────

    it('PATCH → updated_at advances, created_at preserved', async () => {
      // Capture pre-update timestamps from GET
      const preGet = await supertest(app).get(`/api/tasks/${taskId}`).set(authHeader());
      const origCreatedAt = preGet.body.data.created_at;
      const origUpdatedAt = preGet.body.data.updated_at;

      await new Promise((r) => setTimeout(r, 50)); // let time tick

      await supertest(app)
        .patch(`/api/tasks/${taskId}`)
        .set(authHeader())
        .send({ title: 'Time marches on' });

      const postGet = await supertest(app).get(`/api/tasks/${taskId}`).set(authHeader());

      // created_at must never change
      expect(postGet.body.data.created_at).toBe(origCreatedAt);
      // updated_at must advance
      expect(new Date(postGet.body.data.updated_at).getTime()).toBeGreaterThan(
        new Date(origUpdatedAt).getTime(),
      );
    });

    // ── due_date persistence ──────────────────────────────

    it('PATCH due_date → GET confirms date set', async () => {
      const dueDate = '2027-03-15T10:30:00.000Z';
      await supertest(app)
        .patch(`/api/tasks/${taskId}`)
        .set(authHeader())
        .send({ due_date: dueDate });

      const getRes = await supertest(app).get(`/api/tasks/${taskId}`).set(authHeader());
      expect(getRes.body.data.due_date).toBe(dueDate);
    });

    // ── Response does not leak internal fields ────────────

    it('PATCH response does not leak user_id or deleted_at', async () => {
      const res = await supertest(app)
        .patch(`/api/tasks/${taskId}`)
        .set(authHeader())
        .send({ title: 'Clean response' });

      expect(res.body.data.user_id).toBeUndefined();
      expect(res.body.data.deleted_at).toBeUndefined();
    });

    // ── Sequential PATCH operations ───────────────────────

    it('consecutive PATCH calls each persist correctly', async () => {
      // First PATCH: change description only
      await supertest(app)
        .patch(`/api/tasks/${taskId}`)
        .set(authHeader())
        .send({ description: 'Step 1' });

      let getRes = await supertest(app).get(`/api/tasks/${taskId}`).set(authHeader());
      expect(getRes.body.data.description).toBe('Step 1');
      expect(getRes.body.data.title).toBe('Persist Me');

      // Second PATCH: change title only
      await supertest(app)
        .patch(`/api/tasks/${taskId}`)
        .set(authHeader())
        .send({ title: 'Step 2' });

      getRes = await supertest(app).get(`/api/tasks/${taskId}`).set(authHeader());
      expect(getRes.body.data.title).toBe('Step 2');
      expect(getRes.body.data.description).toBe('Step 1'); // preserved from first PATCH
    });
  });
});
