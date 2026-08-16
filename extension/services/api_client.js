/**
 * api_client.js — Backend API communication
 * Handles all calls to the FastAPI backend /analyze endpoint.
 */

import ESA_CONFIG from "../config.js";

const CLIENT_ID_KEY = "esa_client_id";

// Return this browser install's client_id, generating and persisting one on first use.
export async function getClientId() {
  const stored = await chrome.storage.local.get([CLIENT_ID_KEY]);
  if (stored[CLIENT_ID_KEY]) return stored[CLIENT_ID_KEY];

  const clientId = crypto.randomUUID();
  await chrome.storage.local.set({ [CLIENT_ID_KEY]: clientId });
  return clientId;
}

// Send the URL plus collected network/permission signals to the backend and return its verdict.
// client_id scopes /history and /stats to this browser install (not authentication).
export async function analyzePage(url, networkSignals, permissionSignals) {
  const controller = new AbortController();
  const timeoutId = setTimeout(
    () => controller.abort(),
    ESA_CONFIG.REQUEST_TIMEOUT_MS
  );

  try {
    const clientId = await getClientId();
    const response = await fetch(`${ESA_CONFIG.BACKEND_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url,
        network_signals: networkSignals,
        permission_signals: permissionSignals,
        client_id: clientId,
      }),
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
