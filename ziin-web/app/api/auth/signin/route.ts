import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const hasError = request.nextUrl.searchParams.has("error");
  if (hasError) {
    return NextResponse.redirect(new URL("/", request.url));
  }

  return NextResponse.redirect(new URL("/", request.url));
}
