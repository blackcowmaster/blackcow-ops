import path from 'path';
import { Pool } from 'pg';
import { startPostgresContainer, stopPostgresContainer, runMigration } from '../test-helpers';

// Dynamic import after env vars set
let repo: any;
let pool: Pool;

const TEST_USER_ID = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
const OTHER_USER_ID = 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22';

describe('TasksRepository', () => {
  beforeAll(async () => {
    const result = await startPostgresContainer('bkow-test-pg-repo');
    pool = result.pool;

    // Set env before imports
    process.env.DATABASE_URL = result.dbUrl;

    // Run migration
    const migrationPath = path.join(
      __dirname, '..', '..', 'src', 'lib', 'db', 'migrations', '001_create_tasks.sql',
    );
    await runMigration(pool, migrationPath);

    // Dynamic import
    const mod = await import('../../src/repositories/tasks.repository');
    repo = new mod.TasksRepository();
  }, 60000);

  afterAll(async () => {
    await stopPostgresContainer(pool);
  });

  describe('create', () => {
    it('should create a task with all fields', async () => {
      const task = await repo.create(
        { title: 'Test task', description: 'A test description', priority: 'high' },
        TEST_USER_ID,
      );
      expect(task.id).toBeDefined();
      expect(task.title).toBe('Test task');
      expect(task.description).toBe('A test description');
      expect(task.status).toBe('todo');
      expect(task.priority).toBe('high');
      expect(task.user_id).toBe(TEST_USER_ID);
      expect(task.created_at).toBeDefined();
      expect(task.deleted_at).toBeNull();
    });

    it('should use defaults', async () => {
      const task = await repo.create({ title: 'Minimal' }, TEST_USER_ID);
      expect(task.status).toBe('todo');
      expect(task.priority).toBe('medium');
    });
  });

  describe('findById', () => {
    it('should find task by id', async () => {
      const created = await repo.create({ title: 'Find me' }, TEST_USER_ID);
      const found = await repo.findById(created.id, TEST_USER_ID);
      expect(found).not.toBeNull();
      expect(found.id).toBe(created.id);
    });

    it('should return null for non-existent', async () => {
      const found = await repo.findById('00000000-0000-0000-0000-000000000000', TEST_USER_ID);
      expect(found).toBeNull();
    });

    it('should return null for wrong user', async () => {
      const created = await repo.create({ title: 'Not yours' }, TEST_USER_ID);
      const found = await repo.findById(created.id, OTHER_USER_ID);
      expect(found).toBeNull();
    });
  });

  describe('findAll — cursor mode', () => {
    beforeEach(async () => {
      await pool.query('DELETE FROM tasks');
      await repo.create({ title: 'Task 1', priority: 'low' }, TEST_USER_ID);
      await repo.create({ title: 'Task 2', priority: 'medium' }, TEST_USER_ID);
      await repo.create({ title: 'Task 3', priority: 'high' }, TEST_USER_ID);
      await repo.create({ title: 'Other user task' }, OTHER_USER_ID);
    });

    it('should return only user tasks', async () => {
      const { tasks, total } = await repo.findAll(TEST_USER_ID, {
        page: 1, limit: 25, sort_by: 'created_at', order: 'desc', mode: 'cursor',
      });
      expect(tasks).toHaveLength(3);
      expect(total).toBe(3);
      tasks.forEach((t: any) => expect(t.user_id).toBe(TEST_USER_ID));
    });

    it('should filter by priority', async () => {
      const { tasks } = await repo.findAll(TEST_USER_ID, {
        page: 1, limit: 25, sort_by: 'created_at', order: 'desc', mode: 'cursor', priority: 'high',
      });
      expect(tasks).toHaveLength(1);
      expect(tasks[0].priority).toBe('high');
    });

    it('should paginate with limit', async () => {
      const { tasks, total, nextCursor } = await repo.findAll(TEST_USER_ID, {
        page: 1, limit: 2, sort_by: 'created_at', order: 'desc', mode: 'cursor',
      });
      expect(tasks).toHaveLength(2);
      expect(total).toBe(3);
      expect(nextCursor).toBeDefined();
      expect(nextCursor).not.toBeNull();
    });

    it('should support keyset cursor pagination', async () => {
      const page1 = await repo.findAll(TEST_USER_ID, {
        page: 1, limit: 2, sort_by: 'created_at', order: 'desc', mode: 'cursor',
      });
      expect(page1.tasks).toHaveLength(2);
      expect(page1.nextCursor).toBeDefined();
      expect(page1.nextCursor).not.toBeNull();

      const page2 = await repo.findAll(TEST_USER_ID, {
        page: 1, limit: 2, sort_by: 'created_at', order: 'desc', mode: 'cursor', cursor: page1.nextCursor!,
      });
      expect(page2.tasks).toHaveLength(1);
    });

    it('should handle identical timestamps in keyset pagination', async () => {
      await pool.query('DELETE FROM tasks');
      const FIXED_TS = '2026-06-27T12:00:00.123456Z';
      const ids: string[] = [];
      for (let i = 1; i <= 3; i++) {
        const result = await pool.query(
          `INSERT INTO tasks (user_id, title, created_at)
           VALUES ($1, $2, $3::timestamptz)
           RETURNING id`,
          [TEST_USER_ID, `Identical ${i}`, FIXED_TS],
        );
        ids.push(result.rows[0].id);
      }

      const page1 = await repo.findAll(TEST_USER_ID, {
        page: 1, limit: 2, sort_by: 'created_at', order: 'desc', mode: 'cursor',
      });
      expect(page1.tasks).toHaveLength(2);
      expect(page1.nextCursor).toBeDefined();
      expect(page1.nextCursor).not.toBeNull();
      expect(page1.nextCursor).toContain('123456');

      const page2 = await repo.findAll(TEST_USER_ID, {
        page: 1, limit: 2, sort_by: 'created_at', order: 'desc', mode: 'cursor', cursor: page1.nextCursor!,
      });
      expect(page2.tasks).toHaveLength(1);
      expect(page2.total).toBe(3);

      const allIds = [...page1.tasks.map((t: any) => t.id), ...page2.tasks.map((t: any) => t.id)];
      expect(new Set(allIds).size).toBe(3);
      ids.forEach((id) => expect(allIds).toContain(id));
    });
  });

  describe('findAll — offset mode', () => {
    beforeEach(async () => {
      await pool.query('DELETE FROM tasks');
      for (let i = 0; i < 10; i++) {
        await repo.create({ title: `Offset ${i}`, priority: i % 2 === 0 ? 'low' : 'high' }, TEST_USER_ID);
      }
    });

    it('should return first page', async () => {
      const { tasks, total, nextCursor } = await repo.findAll(TEST_USER_ID, {
        page: 1, limit: 4, sort_by: 'created_at', order: 'desc', mode: 'offset',
      });
      expect(tasks).toHaveLength(4);
      expect(total).toBe(10);
      // Offset mode: no cursor
      expect(nextCursor).toBeNull();
    });

    it('should return second page with correct offset', async () => {
      const page1 = await repo.findAll(TEST_USER_ID, {
        page: 1, limit: 4, sort_by: 'created_at', order: 'desc', mode: 'offset',
      });
      const page2 = await repo.findAll(TEST_USER_ID, {
        page: 2, limit: 4, sort_by: 'created_at', order: 'desc', mode: 'offset',
      });
      expect(page2.tasks).toHaveLength(4);
      // No overlap
      const page1Ids = page1.tasks.map((t: any) => t.id);
      const page2Ids = page2.tasks.map((t: any) => t.id);
      const overlap = page1Ids.filter((id: string) => page2Ids.includes(id));
      expect(overlap).toHaveLength(0);
    });

    it('should return last partial page', async () => {
      const { tasks, total } = await repo.findAll(TEST_USER_ID, {
        page: 3, limit: 4, sort_by: 'created_at', order: 'desc', mode: 'offset',
      });
      expect(tasks).toHaveLength(2); // 10 total, 8 dispensed
      expect(total).toBe(10);
    });

    it('should return empty for page beyond range', async () => {
      const { tasks, total } = await repo.findAll(TEST_USER_ID, {
        page: 100, limit: 25, sort_by: 'created_at', order: 'desc', mode: 'offset',
      });
      expect(tasks).toHaveLength(0);
      expect(total).toBe(10);
    });

    it('should filter by priority in offset mode', async () => {
      const { tasks, total } = await repo.findAll(TEST_USER_ID, {
        page: 1, limit: 25, sort_by: 'created_at', order: 'desc', mode: 'offset', priority: 'high',
      });
      expect(tasks).toHaveLength(5);
      expect(total).toBe(5);
      tasks.forEach((t: any) => expect(t.priority).toBe('high'));
    });

    it('should respect sort_by and order', async () => {
      const { tasks } = await repo.findAll(TEST_USER_ID, {
        page: 1, limit: 3, sort_by: 'title', order: 'asc', mode: 'offset',
      });
      expect(tasks).toHaveLength(3);
      // Ascending title order
      expect(tasks[0].title.localeCompare(tasks[1].title)).toBeLessThanOrEqual(0);
      expect(tasks[1].title.localeCompare(tasks[2].title)).toBeLessThanOrEqual(0);
    });
  });

  describe('update', () => {
    it('should update fields', async () => {
      const created = await repo.create({ title: 'Old' }, TEST_USER_ID);
      const updated = await repo.update(created.id, TEST_USER_ID, {
        title: 'New', status: 'in_progress',
      });
      expect(updated).not.toBeNull();
      expect(updated.title).toBe('New');
      expect(updated.status).toBe('in_progress');
    });

    it('should not update other user task', async () => {
      const created = await repo.create({ title: 'Mine' }, TEST_USER_ID);
      const result = await repo.update(created.id, OTHER_USER_ID, { title: 'Stolen' });
      expect(result).toBeNull();
    });
  });

  describe('remove (soft-delete)', () => {
    it('should soft-delete', async () => {
      const created = await repo.create({ title: 'Delete me' }, TEST_USER_ID);
      const removed = await repo.remove(created.id, TEST_USER_ID);
      expect(removed).not.toBeNull();
      expect(removed.deleted_at).not.toBeNull();
      const found = await repo.findById(created.id, TEST_USER_ID);
      expect(found).toBeNull();
    });

    it('should not delete other user task', async () => {
      const created = await repo.create({ title: 'Safe' }, TEST_USER_ID);
      await repo.remove(created.id, OTHER_USER_ID);
      const found = await repo.findById(created.id, TEST_USER_ID);
      expect(found).not.toBeNull();
    });
  });

  describe('bulkCreate', () => {
    it('should create multiple tasks', async () => {
      const tasks = await repo.bulkCreate(
        [{ title: 'B1' }, { title: 'B2' }, { title: 'B3' }],
        TEST_USER_ID,
      );
      expect(tasks).toHaveLength(3);
    });

    it('should reject > 500', async () => {
      const dtos = Array.from({ length: 501 }, (_, i) => ({ title: `T${i}` }));
      await expect(repo.bulkCreate(dtos, TEST_USER_ID)).rejects.toThrow('Batch size exceeds maximum');
    });
  });

  describe('SQL injection prevention', () => {
    it('should escape malicious input', async () => {
      const task = await repo.create(
        { title: "'; DROP TABLE tasks; --" },
        TEST_USER_ID,
      );
      expect(task.title).toBe("'; DROP TABLE tasks; --");
      const { total } = await repo.findAll(TEST_USER_ID, {
        page: 1, limit: 25, sort_by: 'created_at', order: 'desc', mode: 'cursor',
      });
      expect(total).toBeGreaterThan(0);
    });
  });
});
