'use client'

/**
 * Google Cloud OAuth callback (replaces Supabase OAuth callback).
 * Handles Google OAuth callback, extracts tokens from URL, stores them, then redirects to role dashboard.
 */
import { Suspense, useEffect, useState, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { apiClient } from '@/lib/api/client'
import { useAuthContext } from '@/components/auth/AuthProvider'

const ROLE_PREFIX: Record<string, string> = {
  admin: 'ad',
  customer: 'cus',
  staff: 'st',
  manager: 'man',
}

function GoogleCallbackContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { checkAuth } = useAuthContext()
  const [status, setStatus] = useState<'loading' | 'ok' | 'error'>('loading')
  const done = useRef(false)

  useEffect(() => {
    if (done.current) return
    done.current = true

    const token = searchParams?.get('token')
    const refresh = searchParams?.get('refresh')
    const error = searchParams?.get('error')

    if (error) {
      setStatus('error')
      router.replace(`/login?error=${encodeURIComponent(error)}`)
      return
    }

    if (!token || !refresh) {
      setStatus('error')
      router.replace('/login?error=missing_tokens')
      return
    }

    try {
      // Store tokens
      if (typeof window !== 'undefined') {
        localStorage.setItem('access_token', token)
        localStorage.setItem('refresh_token', refresh)
      }

      // Refresh auth context to get user info
      checkAuth().then(() => {
        // Get user role and redirect
        const userStr = localStorage.getItem('user')
        if (userStr) {
          try {
            const user = JSON.parse(userStr)
            const role = user?.role || 'customer'
            const rolePrefix = ROLE_PREFIX[role] || 'cus'
            setStatus('ok')
            const path = `/${rolePrefix}/dashboard`
            if (typeof window !== 'undefined') {
              window.location.href = path
            } else {
              router.replace(path)
            }
          } catch {
            // Fallback to customer dashboard
            setStatus('ok')
            router.replace('/cus/dashboard')
          }
        } else {
          // Fallback: fetch user info
          apiClient.get('/aut/me/').then((res) => {
            if (res.data.success && res.data.data) {
              const user = res.data.data
              const role = user?.role || 'customer'
              const rolePrefix = ROLE_PREFIX[role] || 'cus'
              setStatus('ok')
              router.replace(`/${rolePrefix}/dashboard`)
            } else {
              setStatus('ok')
              router.replace('/cus/dashboard')
            }
          }).catch(() => {
            setStatus('ok')
            router.replace('/cus/dashboard')
          })
        }
      }).catch(() => {
        setStatus('ok')
        router.replace('/cus/dashboard')
      })
    } catch (err) {
      done.current = false
      setStatus('error')
      const msg = err instanceof Error ? err.message : 'Could not complete sign-in.'
      router.replace('/login?error=' + encodeURIComponent(msg))
    }
  }, [router, searchParams, checkAuth])

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

export default function GoogleCallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center p-8">
        <div className="text-center">
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    }>
      <GoogleCallbackContent />
    </Suspense>
  )
}
