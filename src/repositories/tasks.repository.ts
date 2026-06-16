import { query, getClient } from '../lib/db/pool';
import { Task, CreateTaskDto, UpdateTaskDto } from '../types/task';
import { PaginatedQuery } from '../types/api';

export interface FindAllResult {
  tasks: Task[];
  total: number;
  /** PostgreSQL-native cursor for keyset pagination — preserves microsecond precision.
   *  Pass this as `cursor` in PaginatedQuery for the next page. Null when no more pages. */
  nextCursor: string | null;
}

export class TasksRepository {
  async findAll(
    userId: string,
    pq: PaginatedQuery,
  ): Promise<FindAllResult> {
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

    const whereClause = conditions.join(' AND ');
    const whereParamCount = paramIdx - 1;

    const orderDir = pq.order === 'desc' ? 'DESC' : 'ASC';

    if (pq.mode === 'cursor') {
      // ── Keyset cursor pagination ──────────────────────────
      const cursorWhere = pq.cursor
        ? (() => {
            // Split on LAST '_' — safe because neither timestamptz::text nor UUID contain '_'
            const lastUnderscore = pq.cursor!.lastIndexOf('_');
            const cursorCreatedAt = pq.cursor!.substring(0, lastUnderscore);
            const cursorId = pq.cursor!.substring(lastUnderscore + 1);
            const direction = pq.order === 'desc' ? '<' : '>';
            const clause = `AND (t.created_at, t.id) ${direction} ($${paramIdx}::timestamptz, $${paramIdx + 1}::uuid)`;
            params.push(cursorCreatedAt, cursorId);
            paramIdx += 2;
            return clause;
          })()
        : '';

      // PostgreSQL constructs the cursor natively to preserve microsecond precision
      const selectSql = `
        SELECT t.*, t.created_at::text || '_' || t.id::text as _cursor
        FROM tasks t
        WHERE ${whereClause} ${cursorWhere}
        ORDER BY t.created_at ${orderDir}, t.id ${orderDir}
        LIMIT $${paramIdx++}
      `;
      params.push(pq.limit);

      const countSql = `SELECT COUNT(*) as total FROM tasks t WHERE ${whereClause}`;

      const [result, countResult] = await Promise.all([
        query(selectSql, params),
        query(countSql, params.slice(0, whereParamCount)),
      ]);

      // Strip internal _cursor column from returned rows
      const tasks = result.rows.map((row: any) => {
        const { _cursor, ...task } = row;
        return task;
      });

      const total = parseInt(countResult.rows[0].total, 10);
      const nextCursor = result.rows.length > 0 && result.rows.length >= pq.limit
        ? result.rows[result.rows.length - 1]._cursor
        : null;

      return { tasks, total, nextCursor };
    } else {
      // ── Offset pagination ─────────────────────────────────
      const offset = (pq.page - 1) * pq.limit;

      const selectSql = `
        SELECT t.*
        FROM tasks t
        WHERE ${whereClause}
        ORDER BY t.${pq.sort_by} ${orderDir}, t.id ${orderDir}
        LIMIT $${paramIdx++} OFFSET $${paramIdx++}
      `;
      params.push(pq.limit, offset);

      const countSql = `SELECT COUNT(*) as total FROM tasks t WHERE ${whereClause}`;

      const [result, countResult] = await Promise.all([
        query(selectSql, params),
        query(countSql, params.slice(0, whereParamCount)),
      ]);

      const total = parseInt(countResult.rows[0].total, 10);
      const nextCursor = null; // OFFSET mode does not use cursors

      return { tasks: result.rows, total, nextCursor };
    }
  }

  async findById(id: string, userId: string): Promise<Task | null> {
    const sql = `
      SELECT * FROM tasks
      WHERE id = $1 AND user_id = $2 AND deleted_at IS NULL
    `;
    const result = await query(sql, [id, userId]);
    return result.rows[0] || null;
  }

  async create(dto: CreateTaskDto, userId: string): Promise<Task> {
    const sql = `
      INSERT INTO tasks (user_id, title, description, status, priority, due_date)
      VALUES ($1, $2, $3, $4, $5, $6)
      RETURNING *
    `;
    const result = await query(sql, [
      userId,
      dto.title,
      dto.description || null,
      dto.status || 'todo',
      dto.priority || 'medium',
      dto.due_date || null,
    ]);
    return result.rows[0];
  }

  async update(id: string, userId: string, dto: UpdateTaskDto): Promise<Task | null> {
    const setClauses: string[] = [];
    const params: unknown[] = [];
    let paramIdx = 1;

    if (dto.title !== undefined) {
      setClauses.push(`title = $${paramIdx++}`);
      params.push(dto.title);
    }
    if (dto.description !== undefined) {
      setClauses.push(`description = $${paramIdx++}`);
      params.push(dto.description);
    }
    if (dto.status !== undefined) {
      setClauses.push(`status = $${paramIdx++}`);
      params.push(dto.status);
    }
    if (dto.priority !== undefined) {
      setClauses.push(`priority = $${paramIdx++}`);
      params.push(dto.priority);
    }
    if (dto.due_date !== undefined) {
      setClauses.push(`due_date = $${paramIdx++}`);
      params.push(dto.due_date);
    }

    if (setClauses.length === 0) return null;

    const sql = `
      UPDATE tasks
      SET ${setClauses.join(', ')}
      WHERE id = $${paramIdx++} AND user_id = $${paramIdx++} AND deleted_at IS NULL
      RETURNING *
    `;
    params.push(id, userId);

    const result = await query(sql, params);
    return result.rows[0] || null;
  }

  async remove(id: string, userId: string): Promise<Task | null> {
    const sql = `
      UPDATE tasks
      SET deleted_at = NOW()
      WHERE id = $1 AND user_id = $2 AND deleted_at IS NULL
      RETURNING *
    `;
    const result = await query(sql, [id, userId]);
    return result.rows[0] || null;
  }

  async bulkCreate(dtos: CreateTaskDto[], userId: string): Promise<Task[]> {
    if (dtos.length > 500) {
      throw new Error('Batch size exceeds maximum of 500');
    }
    if (dtos.length === 0) return [];

    const values: string[] = [];
    const params: unknown[] = [];
    let paramIdx = 1;

    for (const dto of dtos) {
      values.push(
        `($${paramIdx++}, $${paramIdx++}, $${paramIdx++}, $${paramIdx++}, $${paramIdx++}, $${paramIdx++})`,
      );
      params.push(
        userId,
        dto.title,
        dto.description || null,
        dto.status || 'todo',
        dto.priority || 'medium',
        dto.due_date || null,
      );
    }

    const sql = `
      INSERT INTO tasks (user_id, title, description, status, priority, due_date)
      VALUES ${values.join(', ')}
      RETURNING *
    `;

    const result = await query(sql, params);
    return result.rows;
  }

  async transaction<T>(fn: (client: Awaited<ReturnType<typeof getClient>>) => Promise<T>): Promise<T> {
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
}

export const tasksRepository = new TasksRepository();
