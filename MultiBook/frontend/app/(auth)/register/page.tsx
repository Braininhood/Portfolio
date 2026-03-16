'use client'

import { Suspense, useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuthContext } from '@/components/auth/AuthProvider'
import { apiClient } from '@/lib/api/client'

function RegisterPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { register, isLoading } = useAuthContext()

  const [googleLoading, setGoogleLoading] = useState(false)
  const showGoogleAuth = true
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    password_confirm: '',
  })
  const [error, setError] = useState<string | null>(null)

  // Pre-fill email from query parameter (when redirected from login)
  useEffect(() => {
    const emailParam = searchParams.get('email')
    if (emailParam) {
      setFormData(prev => ({ ...prev, email: emailParam }))
    }
  }, [searchParams])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // Validation
    if (!formData.name || !formData.email || !formData.password) {
      setError('Please fill in all required fields')
      return
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long')
      return
    }

    if (formData.password !== formData.password_confirm) {
      setError('Passwords do not match')
      return
    }

    try {
      const response = await register({
        email: formData.email,
        password: formData.password,
        name: formData.name,
        phone: formData.phone,
        role: 'customer',
      })
      
      // SECURITY: Check if backend returned redirect_to_login flag (email already exists)
      // This prevents user enumeration - backend returns 200 OK for both cases
      if (response.redirect_to_login || response.data?.redirect_to_login) {
        router.push(`/login?email=${encodeURIComponent(formData.email)}&message=${encodeURIComponent('This email is already registered. Please login instead.')}`)
        return
      }
      
      // Check if user is customer (this page is only for customers)
      if (response.user && response.user.role !== 'customer') {
        setError('Registration failed. Please use the correct registration page for your role.')
        return
      }
      
      // Redirect to customer dashboard
      router.push('/cus/dashboard')
    } catch (err: any) {
      // Handle other validation errors (password mismatch, invalid role, etc.)
      // Note: Email duplicates are now handled by redirect_to_login flag (returns 200 OK)
      const _errorCode = err?.error?.code || err?.code
      const errorMessage = err?.error?.message || err?.message || 'Registration failed. Please try again.'
      
      // Extract field-specific errors from DRF validation errors
      const responseData = err?.response?.data || err
      let displayMessage = errorMessage
      
      // Check for field-specific validation errors (password, role, etc.)
      if (responseData) {
        const fieldErrors: string[] = []
        Object.keys(responseData).forEach(key => {
          if (Array.isArray(responseData[key])) {
            fieldErrors.push(`${key}: ${responseData[key][0]}`)
          } else if (typeof responseData[key] === 'string') {
            fieldErrors.push(responseData[key])
          }
        })
        if (fieldErrors.length > 0) {
          displayMessage = fieldErrors.join(', ')
        }
      }
      
      setError(displayMessage)
    }
  }

  const emailFromLogin = searchParams.get('email')

  return (
    <div className="min-h-screen flex items-center justify-center p-4 sm:p-6 md:p-8">
      <div className="w-full max-w-md space-y-8">
        <div>
          <h2 className="text-3xl font-bold text-center">Create Account</h2>
          <p className="mt-2 text-center text-muted-foreground">
            Register for MultiBook
          </p>
          {emailFromLogin && (
            <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                This email is not registered. Please create an account to continue.
              </p>
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="p-4 bg-destructive/10 text-destructive rounded-lg">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="name" className="block text-sm font-medium mb-2">
              Full Name
            </label>
            <input
              id="name"
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              className="w-full px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-2">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
              className="w-full px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring"
            />
          </div>

          <div>
            <label htmlFor="phone" className="block text-sm font-medium mb-2">
              Phone (Optional)
            </label>
            <input
              id="phone"
              type="tel"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
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
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
              className="w-full px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring"
            />
          </div>

          <div>
            <label htmlFor="password_confirm" className="block text-sm font-medium mb-2">
              Confirm Password
            </label>
            <input
              id="password_confirm"
              type="password"
              value={formData.password_confirm}
              onChange={(e) => setFormData({ ...formData, password_confirm: e.target.value })}
              required
              className="w-full px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {isLoading ? 'Creating account...' : 'Register'}
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
                {googleLoading ? 'Redirecting...' : 'Sign up with Google'}
              </button>
            </>
          )}
        </form>

        <div className="text-center text-sm text-muted-foreground">
          <p>
            Already have an account?{' '}
            <Link href="/login" className="text-primary hover:underline">
              Login
            </Link>
          </p>
          <p className="mt-2">
            <Link href="/forgot-password" className="text-primary hover:underline">
              Forgot password?
            </Link>
          </p>
          <p className="mt-4">
            <Link href="/booking" className="text-primary hover:underline">
              Continue as guest (No registration required)
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default function RegisterPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center p-4"><p className="text-muted-foreground">Loading...</p></div>}>
      <RegisterPageContent />
    </Suspense>
  )
}
