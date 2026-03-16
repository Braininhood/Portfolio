/**
 * Dynamic sitemap (Phase 5: SEO).
 * Next.js serves this at /sitemap.xml
 */
import { MetadataRoute } from 'next'
import { getAbsoluteUrl } from '@/lib/seo'

export default function sitemap(): MetadataRoute.Sitemap {
  const base = getAbsoluteUrl('')
  const now = new Date().toISOString()

  const staticRoutes: MetadataRoute.Sitemap = [
    { url: base, lastModified: now, changeFrequency: 'weekly', priority: 1 },
    { url: getAbsoluteUrl('/booking'), lastModified: now, changeFrequency: 'weekly', priority: 0.9 },
    { url: getAbsoluteUrl('/login'), lastModified: now, changeFrequency: 'monthly', priority: 0.5 },
    { url: getAbsoluteUrl('/register'), lastModified: now, changeFrequency: 'monthly', priority: 0.5 },
  ]

  return staticRoutes
}
