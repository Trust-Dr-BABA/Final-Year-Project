import type { NextConfig } from "next";

// Non-nonce CSP, matching node_modules/next/dist/docs/01-app/02-guides/content-security-policy.md's
// own "Without Nonces" recommendation — the nonce-based approach forces every page into dynamic
// rendering app-wide, which is a bigger architectural trade-off than this fix warrants. 'unsafe-inline'
// for scripts/styles is what Next.js itself ships as the baseline non-nonce policy (App Router
// hydration relies on some inline scripts); connect-src is scoped to the backend origin this
// dashboard actually talks to (dashboard/lib/api.ts), not left at the wildcard default.
const isDev = process.env.NODE_ENV === "development";
const backendOrigin = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
const cspHeader = `
  default-src 'self';
  script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""};
  style-src 'self' 'unsafe-inline';
  img-src 'self' blob: data:;
  font-src 'self';
  connect-src 'self' ${backendOrigin};
  object-src 'none';
  base-uri 'self';
  form-action 'self';
  frame-ancestors 'none';
`.replace(/\s{2,}/g, " ").trim();

const nextConfig: NextConfig = {
  // Baseline hardening headers — the dashboard renders one browser's real scan/browsing history,
  // so clickjacking (embedding it in an invisible iframe for UI-redress) and an unrestricted CSP
  // are worth closing even though there's no other known live exploit path today.
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Content-Security-Policy", value: cspHeader },
        ],
      },
    ];
  },
};

export default nextConfig;
