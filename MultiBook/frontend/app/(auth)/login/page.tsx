'use client'

import { Suspense, useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuthContext } from '@/components/auth/AuthProvider'
import { apiClient } from '@/lib/api/client'

const ROLE_PREFIX: Record<string, string> = {
  admin: 'ad',
  customer: 'cus',
  staff: 'st',
  manager: 'man',
}

function LoginPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { login, isLoading, isAuthenticated, user } = useAuthContext()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [googleLoading, setGoogleLoading] = useState(false)
  const showGoogleAuth = true

  // If already authenticated, redirect to role dashboard (e.g. after Google callback or refresh on /login)
  useEffect(() => {
    if (!isLoading && isAuthenticated && user?.role) {
      const prefix = ROLE_PREFIX[user.role] ?? 'cus'
      router.replace(`/${prefix}/dashboard`)
    }
  }, [isLoading, isAuthenticated, user, router])

  // Read URL params once on mount (safely handle search params)
  useEffect(() => {
    try {
      if (searchParams) {
        const emailParam = searchParams.get('email')
        const messageParam = searchParams.get('message')
        const errorParam = searchParams.get('error')
        
        if (emailParam) {
          setEmail(emailParam)
        }
        if (messageParam) {
          setMessage(messageParam)
        }
        // Show user-friendly message for OAuth errors
        if (errorParam === 'oauth_failed') {
          setError('Google sign-in failed. Please try again or use email and password.')
        } else if (errorParam === 'invalid_state') {
          setError('Session expired. Please try signing in with Google again.')
        } else if (errorParam === 'no_code') {
          setError('Google sign-in was cancelled or failed to complete.')
        } else if (errorParam === 'access_denied') {
          setError('Google sign-in was denied. Please try again.')
        } else if (errorParam && !messageParam && !emailParam) {
          setError('Sign-in failed. Please try again.')
        }
      }
    } catch (err) {
      // Silently handle any errors reading search params
      console.debug('Error reading search params:', err)
    }
    // Only run once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!email || !password) {
      setError('Please enter both email and password')
      return
    }

    try {
      await login({ email, password })
      // useAuth hook redirects to role dashboard: admin -> /ad/dashboard, customer -> /cus/dashboard, etc.
      return
    } catch (err: any) {
      // SECURITY: Backend always returns "Invalid email or password" for both cases
      // (email not found OR wrong password) to prevent user enumeration
      // Frontend shows the generic error message without revealing which case it is
      const _errorCode = err?.error?.code || err?.code
      const errorMessage = err?.error?.message || err?.message || 'Invalid email or password'
      
      // Show generic error message (prevents user enumeration)
      // Always shows "Invalid email or password" regardless of actual issue
      setError(errorMessage)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 sm:p-6 md:p-8">
      <div className="w-full max-w-md space-y-8">
        <div>
          <h2 className="text-3xl font-bold text-center">Login</h2>
          <p className="mt-2 text-center text-muted-foreground">
            Access your MultiBook account
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {message && (
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <p className="text-sm text-blue-800 dark:text-blue-200">{message}</p>
            </div>
          )}
          {error && (
            <div className="p-4 bg-destructive/10 text-destructive rounded-lg">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-2">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium mb-2">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring"
            />
          </div>

          <div className="flex items-center justify-between">
            <Link
              href="/forgot-password"
              className="text-sm text-primary hover:underline"
            >
              Forgot password?
            </Link>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>

          {showGoogleAuth && (
            <>
              <div className="relative my-4">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-border" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background px-2 text-muted-foreground">Or</span>
                </div>
              </div>
              <button
                type="button"
                disabled={googleLoading}
                onClick={async () => {
                  setGoogleLoading(true)
                  setError(null)
                  try {
                    // Get Google OAuth authorization URL from backend
                    const authorizationUrl = await apiClient.googleOAuthStart()
                    // Redirect to Google OAuth
                    if (typeof window !== 'undefined' && authorizationUrl) {
                      window.location.href = authorizationUrl
                    }
                  } catch (err: any) {
                    setError(err?.message || 'Failed to start Google sign-in')
                    setGoogleLoading(false)
                  }
                }}
                className="w-full py-3 border border-border rounded-lg hover:bg-muted transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                {googleLoading ? 'Redirecting...' : 'Sign in with Google'}
              </button>
            </>
          )}
        </form>

        <div className="text-center text-sm text-muted-foreground">
          <p>
            Don&apos;t have an account?{' '}
            <Link href="/register" className="text-primary hover:underline">
              Register
            </Link>
          </p>
          <p className="mt-4">
            <Link href="/booking" className="text-primary hover:underline">
              Continue as guest (No login required)
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center p-4"><p className="text-muted-foreground">Loading...</p></div>}>
      <LoginPageContent />
    </Suspense>
  )
}
