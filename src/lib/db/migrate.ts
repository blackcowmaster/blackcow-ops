import fs from 'fs';
import path from 'path';
import { getPool } from './pool';

async function migrate() {
  const migrationPath = path.join(__dirname, 'migrations', '001_create_tasks.sql');
  const sql = fs.readFileSync(migrationPath, 'utf-8');

  console.log('[migrate] Running migration 001_create_tasks...');
  const pool = getPool();
  await pool.query(sql);
  console.log('[migrate] Migration complete.');

  await pool.end();
}

migrate().catch((err) => {
  console.error('[migrate] Failed:', err.message);
  process.exit(1);
});
