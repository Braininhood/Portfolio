/**
 * robots.txt (Phase 5: SEO).
 * Next.js serves this at /robots.txt
 */
import { MetadataRoute } from 'next'
import { getAbsoluteUrl } from '@/lib/seo'

export default function robots(): MetadataRoute.Robots {
  const base = getAbsoluteUrl('')
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: ['/api/', '/auth/', '/cus/', '/ad/', '/st/', '/man/', '/dashboard', '/settings/'],
      },
    ],
    sitemap: `${base}/sitemap.xml`,
  }
}
