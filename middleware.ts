import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { auth } from "@/lib/auth";

const protectedRoutes = ["/dashboard", "/new", "/projects", "/billing", "/settings", "/admin"];

export async function middleware(req: NextRequest) {
  if (!protectedRoutes.some((route) => req.nextUrl.pathname.startsWith(route))) {
    return NextResponse.next();
  }

  const session = await auth(req);
  if (!session?.user) {
    const loginUrl = new URL("/login", req.url);
    loginUrl.searchParams.set("callbackUrl", req.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (req.nextUrl.pathname.startsWith("/admin") && session.user.role !== "ADMIN") {
    return NextResponse.redirect(new URL("/dashboard", req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/new/:path*", "/projects/:path*", "/billing/:path*", "/settings/:path*", "/admin/:path*"]
};
