/**
 * Next.js Proxy (formerly middleware)
 * Handles favicon requests to prevent 404 errors
 */
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function proxy(request: NextRequest) {
  // Handle favicon requests
  if (request.nextUrl.pathname === '/favicon.ico') {
    return new NextResponse(null, {
      status: 204,
      headers: {
        'Content-Type': 'image/x-icon',
      },
    })
  }

  return NextResponse.next()
}

export const config = {
  matcher: '/favicon.ico',
}
