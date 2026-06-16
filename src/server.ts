import dotenv from 'dotenv';
import { cleanEnv, str, num, makeValidator } from 'envalid';
import { app } from './app';
import { endPool } from './lib/db/pool';

dotenv.config();

const minLen32 = makeValidator<string>((input: string) => {
  if (input.length < 32) {
    throw new Error('JWT_SECRET must be at least 32 characters');
  }
  return input;
});

const env = cleanEnv(process.env, {
  DATABASE_URL: str({ desc: 'PostgreSQL connection string' }),
  JWT_SECRET: minLen32({ desc: 'JWT signing secret (min 32 chars)' }),
  PORT: num({ default: 3000, desc: 'HTTP port' }),
  JWT_EXPIRY: str({ default: '15m', desc: 'JWT token expiry' }),
  ALLOWED_ORIGINS: str({ default: 'http://localhost:3000', desc: 'CORS allowed origins' }),
});

const server = app.listen(env.PORT, () => {
  console.log(`[server] Listening on port ${env.PORT}`);
});

process.on('SIGTERM', async () => {
  console.log('[server] SIGTERM received');
  server.close(async () => {
    await endPool();
    process.exit(0);
  });
});

process.on('SIGINT', async () => {
  console.log('[server] SIGINT received');
  server.close(async () => {
    await endPool();
    process.exit(0);
  });
});

export default server;
