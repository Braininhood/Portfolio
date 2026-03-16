'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/use-auth'

/**
 * Manager Login Page
 * Route: /man/login
 * Only allows manager/admin role login, redirects to /man/dashboard
 */
export default function ManagerLoginPage() {
  const router = useRouter()
  const { login, isLoading } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!email || !password) {
      setError('Please enter both email and password')
      return
    }

    try {
      const response = await login({ email, password })
      // Check if user is manager or admin
      if (response.user.role !== 'manager' && response.user.role !== 'admin') {
        setError('This login is only for managers and admins. Please use the correct login page for your role.')
        return
      }
      // Redirect handled by useAuth hook (will go to /man/dashboard for manager or /ad/dashboard for admin)
    } catch (err: any) {
      const errorCode = err?.error?.code || err?.code
      const errorMessage = err?.error?.message || err?.message || 'Login failed. Please check your credentials.'
      
      if (errorCode === 'EMAIL_NOT_FOUND') {
        router.push(`/man/register?email=${encodeURIComponent(email)}`)
        return
      }
      
      setError(errorMessage)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-8">
      <div className="w-full max-w-md space-y-8">
        <div>
          <h2 className="text-3xl font-bold text-center">Manager Login</h2>
          <p className="mt-2 text-center text-muted-foreground">
            Access your MultiBook manager/admin account
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
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

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="text-center text-sm text-muted-foreground">
          <p>
            Don&apos;t have a manager account?{' '}
            <Link href="/man/register" className="text-primary hover:underline">
              Register
            </Link>
          </p>
          <p className="mt-2">
            <Link href="/login" className="text-primary hover:underline">
              Customer Login
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
