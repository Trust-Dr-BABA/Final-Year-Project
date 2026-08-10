/**
 * api.ts — Backend API client for Next.js dashboard.
 * Communicates with FastAPI backend.
 */

import { HistoryResponse, Scan, Stats } from "./types";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

// Fetch aggregate scan statistics; returns all-zero defaults if the backend is unreachable.
export async function getStats(): Promise<Stats> {
  try {
    const res = await fetch(`${BACKEND_URL}/stats`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("[API] Failed to fetch stats:", err);
    return {
      total_scans: 0,
      phishing_count: 0,
      suspicious_count: 0,
      legitimate_count: 0,
      avg_confidence_pct: 0,
    };
  }
}

// Fetch paginated scan history; returns an empty page if the backend is unreachable.
export async function getHistory(
  limit: number = 50,
  offset: number = 0
): Promise<HistoryResponse> {
  try {
    const res = await fetch(
      `${BACKEND_URL}/history?limit=${limit}&offset=${offset}`,
      { cache: "no-store" }
    );
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("[API] Failed to fetch scan history:", err);
    return { scans: [], total: 0, limit, offset };
  }
}

// Fetch a single scan's full detail by id; returns null if not found or unreachable.
export async function getScan(scanId: string): Promise<Scan | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/scan/${scanId}`, {
      cache: "no-store",
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error(`[API] Failed to fetch scan ${scanId}:`, err);
    return null;
  }
}
