import { jsonLdOrganization, jsonLdWebSite } from '@/lib/seo'
import { HomeCTA } from '@/components/home/HomeCTA'

// Escape </script> in JSON so it does not close the script tag and cause "literal not terminated"
function safeJsonLdHtml(obj: object): string {
  const raw = JSON.stringify(obj)
  return raw.replace(/<\/script/gi, '<\\/script')
}

export default function Home() {
  const orgJsonLd = jsonLdOrganization()
  const webJsonLd = jsonLdWebSite()

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-4 sm:p-6 md:p-8">
      {/* Structured data (Phase 5: SEO) */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: safeJsonLdHtml(orgJsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: safeJsonLdHtml(webJsonLd) }}
      />
      <div className="text-center space-y-8">
        <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold">MultiBook - Multi-Service Booking</h1>
        <p className="text-base sm:text-lg md:text-xl text-muted-foreground">
          Professional booking system for cleaning services
        </p>

        <HomeCTA />
      </div>
    </main>
  )
}
