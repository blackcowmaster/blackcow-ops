import { execSync } from 'child_process';
import { Pool } from 'pg';

let containerName: string | null = null;
let hostPort: number | null = null;

export async function startPostgresContainer(name = 'bkow-test-pg'): Promise<{ dbUrl: string; pool: Pool }> {
  containerName = name;
  // Kill any existing container with this name
  try {
    execSync(`docker rm -f ${containerName}`, { stdio: 'ignore' });
  } catch {
    // ignore
  }

  // Start postgres with dynamic port
  execSync(
    `docker run -d --name ${containerName} \
      -e POSTGRES_DB=testdb \
      -e POSTGRES_USER=testuser \
      -e POSTGRES_PASSWORD=testpass \
      -P \
      postgres:16-alpine`,
    { encoding: 'utf-8' },
  ).trim();

  // Find the mapped port
  const portOutput = execSync(`docker port ${containerName} 5432`, { encoding: 'utf-8' }).trim();
  // Output format: "0.0.0.0:32768" or "[::]:32768"
  const portMatch = portOutput.match(/:(\d+)/);
  hostPort = portMatch ? parseInt(portMatch[1], 10) : 54320;

  // Wait for postgres to be ready
  const dbUrl = `postgresql://testuser:testpass@localhost:${hostPort}/testdb`;
  const pool = new Pool({ connectionString: dbUrl });

  for (let i = 0; i < 30; i++) {
    try {
      await pool.query('SELECT 1');
      break;
    } catch {
      await new Promise((r) => setTimeout(r, 1000));
    }
  }

  return { dbUrl, pool };
}

export async function stopPostgresContainer(pool: Pool) {
  await pool.end();
  if (containerName) {
    try {
      execSync(`docker rm -f ${containerName}`, { stdio: 'ignore' });
    } catch {
      // ignore
    }
  }
}

export function runMigration(pool: Pool, migrationPath: string) {
  const fs = require('fs');
  const sql = fs.readFileSync(migrationPath, 'utf-8');
  return pool.query(sql);
}
