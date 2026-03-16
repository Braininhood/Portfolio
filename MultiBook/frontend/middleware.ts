import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

/**
 * Redirect traffic from raw EC2 IP to canonical hostname so OAuth and cookies
 * use a single origin (avoids invalid_state / session issues).
 * Set CANONICAL_ORIGIN in .env to the canonical URL (use hyphens in hostname, not dots):
 * e.g. https://ec2-13-135-109-229.eu-west-2.compute.amazonaws.com
 */
const RAW_IP_HOSTS = ['13.135.109.229']

export function middleware(request: NextRequest) {
  const host = request.headers.get('host')?.split(':')[0] ?? ''
  const canonicalOrigin = process.env.CANONICAL_ORIGIN || process.env.NEXT_PUBLIC_APP_URL

  if (!canonicalOrigin || !canonicalOrigin.startsWith('http')) {
    return NextResponse.next()
  }

  const canonicalUrl = new URL(canonicalOrigin)
  if (RAW_IP_HOSTS.includes(host) && host !== canonicalUrl.host) {
    const path = request.nextUrl.pathname + request.nextUrl.search
    const target = new URL(path, canonicalOrigin)
    return NextResponse.redirect(target.toString(), 301)
  }

  return NextResponse.next()
}

export const config = {
  matcher: '/:path*',
}
