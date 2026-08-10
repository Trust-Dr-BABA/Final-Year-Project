/**
 * api_client.js — Backend API communication
 * Handles all calls to the FastAPI backend /analyze endpoint.
 */

import ESA_CONFIG from "../config.js";

// Send the URL plus collected network/permission signals to the backend and return its verdict.
export async function analyzePage(url, networkSignals, permissionSignals) {
  const controller = new AbortController();
  const timeoutId = setTimeout(
    () => controller.abort(),
    ESA_CONFIG.REQUEST_TIMEOUT_MS
  );

  try {
    const response = await fetch(`${ESA_CONFIG.BACKEND_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, network_signals: networkSignals, permission_signals: permissionSignals }),
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  } finally {
    clearTimeout(timeoutId);
  }
}
