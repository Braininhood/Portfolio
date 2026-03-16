/**
 * SEO config and helpers (Phase 5).
 * Used for metadata, Open Graph, JSON-LD.
 * All values are safe strings (no empty or unterminated literals in serialized output).
 */
const siteName = 'MultiBook'
const siteTagline = 'Professional booking system for cleaning services'
const defaultTitle = siteName + ' Booking System'
const defaultDescription = siteTagline + '. Book cleaning services online.'

function getBaseUrl(): string {
  if (typeof process === 'undefined') return 'http://localhost:3000'
  const envUrl = process.env.NEXT_PUBLIC_APP_URL
  if (envUrl && typeof envUrl === 'string' && envUrl.trim()) {
    const u = envUrl.replace(/\/+$/, '').trim()
    if (/^https?:\/\/[^\s"']+$/i.test(u)) return u
  }
  const vercel = process.env.VERCEL_URL
  if (vercel && typeof vercel === 'string' && /^[a-z0-9.-]+$/i.test(vercel)) return 'https://' + vercel
  return 'http://localhost:3000'
}

export const siteConfig = {
  name: siteName,
  tagline: siteTagline,
  title: defaultTitle,
  description: defaultDescription,
  url: getBaseUrl(),
  locale: 'en_GB',
  twitterHandle: 'MultiBook',
}

export function getAbsoluteUrl(path: string): string {
  const base = siteConfig.url
  const p = path.startsWith('/') ? path : `/${path}`
  return base.replace(/\/$/, '') + p
}

/** JSON-LD Organization for home/booking pages. */
export function jsonLdOrganization() {
  return {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: siteConfig.name,
    description: siteConfig.description,
    url: siteConfig.url,
  }
}

/** JSON-LD WebSite with search action (for sitelinks search box). */
export function jsonLdWebSite() {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: siteConfig.name,
    description: siteConfig.description,
    url: siteConfig.url,
    potentialAction: {
      '@type': 'SearchAction',
      target: { '@type': 'EntryPoint', urlTemplate: siteConfig.url + '/booking?q={search_term_string}' },
      'query-input': 'required name=search_term_string',
    },
  }
}

/** JSON-LD LocalBusiness (optional – use if you have a physical location). */
export function jsonLdLocalBusiness(overrides?: Record<string, unknown>) {
  return {
    '@context': 'https://schema.org',
    '@type': 'LocalBusiness',
    name: siteConfig.name,
    description: siteConfig.description,
    url: siteConfig.url,
    ...overrides,
  }
}
