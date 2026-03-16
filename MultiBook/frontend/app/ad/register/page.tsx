'use client'

import { Suspense, useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/hooks/use-auth'
import { apiClient } from '@/lib/api/client'

/**
 * Admin Registration Page
 * Route: /ad/register
 * Requires invitation token for admin registration
 */
function AdminRegisterPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { register, isLoading } = useAuth()
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    password_confirm: '',
    invitation_token: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [invitationError, setInvitationError] = useState<string | null>(null)
  const [validatingInvitation, setValidatingInvitation] = useState(true)
  const [invitationData, setInvitationData] = useState<{ email: string; role: string } | null>(null)

  useEffect(() => {
    const token = searchParams.get('token')
    const emailParam = searchParams.get('email')
    
    if (token) {
      setFormData(prev => ({ ...prev, invitation_token: token }))
      // Validate invitation token
      apiClient.validateInvitation(token)
        .then((data) => {
          setInvitationData(data)
          if (data.email) {
            setFormData(prev => ({ ...prev, email: data.email }))
          }
          setValidatingInvitation(false)
        })
        .catch((err: any) => {
          const errorMessage = err?.response?.data?.error?.message || err?.message || 'Invalid or expired invitation token'
          setInvitationError(errorMessage)
          setValidatingInvitation(false)
        })
    } else {
      // No token provided - show error
      setInvitationError('Invitation token is required for admin registration. Please use the invitation link sent to you.')
      setValidatingInvitation(false)
    }
    
    if (emailParam && !token) {
      setFormData(prev => ({ ...prev, email: emailParam }))
    }
  }, [searchParams])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

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

    // Validate invitation token is present
    if (!formData.invitation_token) {
      setError('Invitation token is required for admin registration.')
      return
    }

    try {
      const response = await register({
        email: formData.email,
        password: formData.password,
        name: formData.name,
        phone: formData.phone,
        role: 'admin',
        invitation_token: formData.invitation_token,
      })
      
      // Check if user is admin
      if (response.user && response.user.role !== 'admin') {
        setError('Registration failed. Please contact system administrator to create an admin account.')
        return
      }
      
      // Redirect to admin dashboard
      router.push('/ad/dashboard')
    } catch (err: any) {
      const errorMessage = err?.error?.message || err?.response?.data?.error?.message || err?.message || 'Registration failed. Please try again.'
      setError(errorMessage)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-8">
      <div className="w-full max-w-md space-y-8">
        <div>
          <h2 className="text-3xl font-bold text-center">Admin Registration</h2>
          <p className="mt-2 text-center text-muted-foreground">
            Register for MultiBook admin account
          </p>
          {validatingInvitation && (
            <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                Validating invitation token...
              </p>
            </div>
          )}
          {invitationError && (
            <div className="mt-4 p-3 bg-destructive/10 text-destructive border border-destructive/20 rounded-lg">
              <p className="text-sm">{invitationError}</p>
            </div>
          )}
          {invitationData && !invitationError && (
            <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
              <p className="text-sm text-green-800 dark:text-green-200">
                Invitation validated for {invitationData.email}. Please complete your registration below.
              </p>
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-6" style={{ display: invitationError || validatingInvitation ? 'none' : 'block' }}>
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
              disabled={!!invitationData?.email}
              className="w-full px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring disabled:opacity-50 disabled:cursor-not-allowed"
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
        </form>

        <div className="text-center text-sm text-muted-foreground">
          <p>
            Already have an admin account?{' '}
            <Link href="/ad/login" className="text-primary hover:underline">
              Login
            </Link>
          </p>
          <p className="mt-2">
            <Link href="/register" className="text-primary hover:underline">
              Customer Registration
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default function AdminRegisterPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><p className="text-muted-foreground">Loading...</p></div>}>
      <AdminRegisterPageContent />
    </Suspense>
  )
}
