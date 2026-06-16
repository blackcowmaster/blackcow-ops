import { Pool, PoolConfig } from 'pg';

let _pool: Pool | null = null;

function getPoolConfig(): PoolConfig {
  return {
    connectionString: process.env.DATABASE_URL,
    max: 10,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 5000,
    statement_timeout: 30000,
  };
}

export function getPool(): Pool {
  if (!_pool) {
    _pool = new Pool(getPoolConfig());
    _pool.on('error', (err: Error) => {
      console.error('[pg pool] Unexpected error on idle client:', err.message);
    });
  }
  return _pool;
}

export function resetPool(): void {
  if (_pool) {
    _pool.end().catch((err) => {
      console.error('Failed to terminate database pool:', err);
    });
    _pool = null;
  }
}

export async function query(text: string, params?: unknown[]) {
  const pool = getPool();
  const start = Date.now();
  const result = await pool.query(text, params);
  const duration = Date.now() - start;
  if (duration > 1000) {
    console.warn(`[pg] Slow query (${duration}ms): ${text.substring(0, 200)}`);
  }
  return result;
}

export async function getClient() {
  const pool = getPool();
  return pool.connect();
}

export async function endPool() {
  if (_pool) {
    await _pool.end();
    _pool = null;
  }
}
