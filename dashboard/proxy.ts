import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { CLIENT_ID_COOKIE } from "./lib/clientId";

const ONE_YEAR_SECONDS = 60 * 60 * 24 * 365;

// Bind ?client_id=... (set by the extension's "Open Dashboard" link) to a long-lived cookie, then
// strip it from the URL. Every later page load reads the cookie via next/headers instead — this
// is per-browser scoping, not authentication, matching the single-user-per-install trust model
// documented in LIMITATIONS.md.
export function proxy(request: NextRequest) {
  const clientId = request.nextUrl.searchParams.get("client_id");
  if (!clientId) return NextResponse.next();

  const cleanUrl = new URL(request.nextUrl);
  cleanUrl.searchParams.delete("client_id");
  const response = NextResponse.redirect(cleanUrl);
  response.cookies.set(CLIENT_ID_COOKIE, clientId, {
    maxAge: ONE_YEAR_SECONDS,
    sameSite: "lax",
    path: "/",
    httpOnly: true, // only ever read server-side via next/headers cookies() — no page JS needs it
    secure: process.env.NODE_ENV === "production",
  });
  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
