/**
 * config.js — Extension configuration constants
 * Update BACKEND_URL and DASHBOARD_URL after deploying to production.
 */

const ESA_CONFIG = {
  /** The deployed FastAPI backend URL. Change this after deploying to Render/Railway. */
  BACKEND_URL: "http://localhost:8000",

  /** The deployed Next.js dashboard URL. Change this after deploying to Vercel. */
  DASHBOARD_URL: "http://localhost:3000",

  /** How long to wait for the backend before showing an error (ms) */
  REQUEST_TIMEOUT_MS: 15000,
};

export default ESA_CONFIG;
