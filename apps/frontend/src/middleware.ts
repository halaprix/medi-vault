import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Paths that don't require authentication
const PUBLIC_PATHS = ["/login", "/setup", "/_next", "/favicon.ico", "/api"];
const ASSET_PREFIXES = ["/_next/", "/static/", "/images/", "/fonts/"];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public paths and assets
  if (
    PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith(p)) ||
    ASSET_PREFIXES.some((p) => pathname.startsWith(p))
  ) {
    // If on /login or /setup and already authenticated, redirect to /dashboard
    const token = request.cookies.get("access_token")?.value;
    if ((pathname === "/login" || pathname === "/setup") && token) {
      try {
        // Verify JWT is not expired by checking the backend
        const res = await fetch(
          `${request.nextUrl.origin}/api/v1/auth/verify`,
          { headers: { Authorization: `Bearer ${token}` } },
        );
        if (res.ok) {
          return NextResponse.redirect(new URL("/dashboard", request.url));
        }
      } catch {
        // If backend is not available, allow the page to load
      }
    }
    return NextResponse.next();
  }

  // All other paths require authentication
  const token = request.cookies.get("access_token")?.value;

  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
