'use client'

/**
 * OAuth callback (e.g. Google sign-in via Supabase).
 * Exchanges Supabase session for Django user/JWT, stores tokens, then full-page redirect to role dashboard.
 * Full-page redirect ensures the dashboard loads with tokens in localStorage and AuthProvider hydrates from /api/aut/me/.
 */
import { useEffect, useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { supabase } from '@/lib/supabase/client'
import { apiClient } from '@/lib/api/client'

const ROLE_PREFIX: Record<string, string> = {
  admin: 'ad',
  customer: 'cus',
  staff: 'st',
  manager: 'man',
}

export default function AuthCallbackPage() {
  const router = useRouter()
  const [status, setStatus] = useState<'loading' | 'ok' | 'error'>('loading')
  const done = useRef(false)

  useEffect(() => {
    if (!supabase) {
      setStatus('error')
      router.replace('/login')
      return
    }
    if (done.current) return
    done.current = true

    supabase.auth.getSession().then(async ({ data: { session }, error }) => {
      if (error) {
        setStatus('error')
        router.replace('/login?message=' + encodeURIComponent('Sign-in failed. Please try again.'))
        return
      }
      if (!session?.access_token) {
        setStatus('error')
        router.replace('/login')
        return
      }
      try {
        const email = session.user?.email ?? undefined
        const name = session.user?.user_metadata?.full_name ?? session.user?.user_metadata?.name ?? session.user?.email ?? undefined
        const { user } = await apiClient.googleLogin(session.access_token, email, name)
        // Map backend role to URL prefix (same as email/password login: customer -> /cus/dashboard, etc.)
        const role = (user as { role?: string })?.role
        const rolePrefix = role && ROLE_PREFIX[role] ? ROLE_PREFIX[role] : 'cus'
        setStatus('ok')
        // Full-page redirect to role dashboard (same URL as email login: /cus/dashboard, /ad/dashboard, etc.)
        const path = `/${rolePrefix}/dashboard`
        const fullUrl = typeof window !== 'undefined' ? `${window.location.origin}${path}` : path
        if (typeof window !== 'undefined') {
          window.location.href = fullUrl
        } else {
          router.replace(path)
        }
      } catch (err) {
        done.current = false
        setStatus('error')
        const msg = err instanceof Error ? err.message : 'Could not sign in with Google.'
        router.replace('/login?message=' + encodeURIComponent(msg))
      }
    })
  }, [router])

  return (
    <div className="min-h-screen flex items-center justify-center p-8">
      <div className="text-center">
        {status === 'loading' && <p className="text-muted-foreground">Completing sign-in...</p>}
        {status === 'ok' && <p className="text-muted-foreground">Redirecting...</p>}
        {status === 'error' && <p className="text-muted-foreground">Redirecting to login...</p>}
      </div>
    </div>
  )
}
