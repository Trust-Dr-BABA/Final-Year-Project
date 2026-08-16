/**
 * global-teardown.ts — Deletes every scan row seeded by this suite (client_id LIKE 'e2e-%').
 *
 * Not required for test correctness — every test seeds a unique client_id (see fixtures/client.ts),
 * so runs never interfere with each other even if this never ran. It exists purely so a dev
 * database doesn't accumulate thousands of throwaway rows across repeated local runs. Best-effort:
 * a cleanup failure must never fail the run that already passed.
 */

import { Client } from "pg";

export default async function globalTeardown() {
  const databaseUrl = process.env.DATABASE_URL;
  if (!databaseUrl) {
    console.warn("[e2e] Skipping teardown cleanup: DATABASE_URL not set.");
    return;
  }

  // node-postgres doesn't understand SQLAlchemy's "+asyncpg" driver suffix in the URL.
  const client = new Client({ connectionString: databaseUrl.replace("+asyncpg", "") });

  try {
    await client.connect();
    const result = await client.query("DELETE FROM scans WHERE client_id LIKE 'e2e-%'");
    console.log(`[e2e] Teardown: removed ${result.rowCount} seeded scan row(s).`);
  } catch (err) {
    console.warn(`[e2e] Teardown cleanup failed (non-fatal): ${(err as Error).message}`);
  } finally {
    await client.end().catch(() => {});
  }
}
