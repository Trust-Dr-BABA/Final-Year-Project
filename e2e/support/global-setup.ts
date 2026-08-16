/**
 * global-setup.ts — Fails the whole run fast, with one clear message, if the backend isn't
 * reachable, instead of letting every single test in the suite time out confusingly against a
 * dead API. The backend + Postgres are an external dependency this suite does not start itself
 * (see playwright.config.ts) — the developer or CI job is responsible for having them up first.
 */

const BACKEND_URL = process.env.E2E_BACKEND_URL || "http://localhost:8000";

export default async function globalSetup() {
  let response: Response;
  try {
    response = await fetch(`${BACKEND_URL}/health`);
  } catch (err) {
    throw new Error(
      `E2E setup: backend at ${BACKEND_URL} is unreachable (${(err as Error).message}).\n` +
        `Start it first — e.g. "docker compose -f docker/docker-compose.yml up -d" or the ` +
        `host-run uvicorn command in README.md — then re-run the suite. ` +
        `Override the URL with E2E_BACKEND_URL if it isn't on localhost:8000.`
    );
  }

  if (!response.ok) {
    throw new Error(`E2E setup: backend at ${BACKEND_URL}/health returned ${response.status}.`);
  }

  const health = (await response.json()) as { db_reachable: boolean; model_loaded: boolean };
  if (!health.db_reachable) {
    throw new Error(
      `E2E setup: backend is up but reports db_reachable: false. Check Postgres is running ` +
        `and DATABASE_URL is correct before running the suite.`
    );
  }
  if (!health.model_loaded) {
    // Not fatal — ADR-016's fallback path (ESA_ALLOW_FALLBACK=1) still produces a deterministic
    // verdict shape, which is all the structural assertions in this suite depend on. Logged so a
    // failure that happens to correlate with "wrong" verdicts isn't mysterious.
    console.warn(
      "[e2e] Warning: backend reports model_loaded: false — /analyze is using the heuristic " +
        "fallback (ADR-016), not the trained model. Tests that assert on structure will still " +
        "pass; anything that assumed the real model's verdict on a specific URL would not."
    );
  }
}
