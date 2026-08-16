/**
 * api.ts — Backend API client for Next.js dashboard.
 * Communicates with FastAPI backend.
 */

import { HistoryResponse, Scan, Stats } from "./types";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

// Shared fetch/parse/fallback shape used by every function below — on any failure (network error,
// non-2xx status, unreachable backend), logs and returns the caller's fallback rather than
// throwing, since every call site here is a server component rendering a page that must still
// render something sensible if the backend is down.
async function fetchJson<T>(url: string, fallback: T, label: string): Promise<T> {
  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error(`[API] Failed to fetch ${label}:`, err);
    return fallback;
  }
}

// Fetch aggregate scan statistics for one browser's own scans; all-zero if unreachable or if
// clientId is absent (a dashboard visit that never came from the extension has no history to show).
export async function getStats(clientId?: string): Promise<Stats> {
  const empty: Stats = {
    total_scans: 0,
    phishing_count: 0,
    suspicious_count: 0,
    legitimate_count: 0,
    avg_confidence_pct: 0,
  };
  if (!clientId) return empty;

  return fetchJson(
    `${BACKEND_URL}/stats?client_id=${encodeURIComponent(clientId)}`,
    empty,
    "stats"
  );
}

// Fetch paginated scan history for one browser's own scans; empty if unreachable or clientId absent.
export async function getHistory(
  limit: number = 50,
  offset: number = 0,
  clientId?: string
): Promise<HistoryResponse> {
  const empty: HistoryResponse = { scans: [], total: 0, limit, offset };
  if (!clientId) return empty;

  return fetchJson(
    `${BACKEND_URL}/history?limit=${limit}&offset=${offset}&client_id=${encodeURIComponent(clientId)}`,
    empty,
    "scan history"
  );
}

// Fetch a single scan's full detail by id, scoped to the caller's own clientId; returns null if
// not found, not owned by this clientId, unreachable, or clientId is absent (never fetch someone
// else's scan just because we know its id — see backend/routers/history.py).
export async function getScan(scanId: string, clientId?: string): Promise<Scan | null> {
  if (!clientId) return null;

  return fetchJson<Scan | null>(
    `${BACKEND_URL}/scan/${scanId}?client_id=${encodeURIComponent(clientId)}`,
    null,
    `scan ${scanId}`
  );
}
