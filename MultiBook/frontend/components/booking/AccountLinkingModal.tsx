'use client'

/**
 * Account Linking Modal Component
 * 
 * Shows login or registration form based on whether email exists.
 * Used for linking guest orders to customer accounts.
 */
import { useEffect, useState } from 'react'
import { apiClient } from '@/lib/api/client'
import { PUBLIC_ENDPOINTS } from '@/lib/api/endpoints'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

interface AccountLinkingModalProps {
  orderNumber: string
  guestEmail: string
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  emailExists: boolean
}

export function AccountLinkingModal({
  orderNumber,
  guestEmail,
  isOpen,
  onClose,
  onSuccess,
  emailExists,
}: AccountLinkingModalProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState(guestEmail)
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      setEmail(guestEmail)
      setPassword('')
      setPasswordConfirm('')
      setError(null)
      // Set mode based on emailExists
      setMode(emailExists ? 'login' : 'register')
    }
  }, [isOpen, guestEmail, emailExists])

  const handleLogin = async () => {
    if (!email || !password) {
      setError('Email and password are required')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await apiClient.post(
        PUBLIC_ENDPOINTS.BOOKINGS.GUEST_ORDER_LINK_LOGIN(orderNumber),
        {
          email: email.trim(),
          password,
        }
      )

      if (response.data.success) {
        onSuccess()
        onClose()
      } else {
        setError(response.data.error?.message || 'Login failed')
      }
    } catch (err: any) {
      setError(
        err.response?.data?.error?.message || 
        'Unable to link order. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async () => {
    if (!email || !password || !passwordConfirm) {
      setError('All fields are required')
      return
    }

    if (password !== passwordConfirm) {
      setError('Passwords do not match')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await apiClient.post(
        PUBLIC_ENDPOINTS.BOOKINGS.GUEST_ORDER_LINK_REGISTER(orderNumber),
        {
          email: email.trim(),
          password,
          password_confirm: passwordConfirm,
        }
      )

      if (response.data.success) {
        onSuccess()
        onClose()
      } else {
        setError(response.data.error?.message || 'Registration failed')
      }
    } catch (err: any) {
      setError(
        err.response?.data?.error?.message || 
        'Unable to create account. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {mode === 'login' ? 'Link Order to Account' : 'Create Account & Link Order'}
          </DialogTitle>
          <DialogDescription>
            {mode === 'login' 
              ? 'Login to link this order to your existing account.'
              : 'Create an account to link this order and manage all your bookings in one place.'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {error && (
            <div className="p-3 bg-destructive/10 text-destructive rounded-lg text-sm">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={true}
              className="w-full px-3 py-2 border border-border rounded-lg bg-muted text-muted-foreground"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Email is pre-filled from your order
            </p>
          </div>

          {mode === 'login' ? (
            <>
              <div>
                <label htmlFor="password" className="block text-sm font-medium mb-1">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full px-3 py-2 border border-border rounded-lg"
                  disabled={loading}
                />
              </div>

              <Button
                onClick={handleLogin}
                disabled={loading || !email || !password}
                className="w-full"
              >
                {loading ? 'Linking...' : 'Login & Link Order'}
              </Button>

              <p className="text-xs text-center text-muted-foreground">
                Don&apos;t have an account?{' '}
                <button
                  type="button"
                  onClick={() => setMode('register')}
                  className="text-primary hover:underline"
                >
                  Create one instead
                </button>
              </p>
            </>
          ) : (
            <>
              <div>
                <label htmlFor="password" className="block text-sm font-medium mb-1">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Create a password (min. 8 characters)"
                  className="w-full px-3 py-2 border border-border rounded-lg"
                  disabled={loading}
                />
              </div>

              <div>
                <label htmlFor="passwordConfirm" className="block text-sm font-medium mb-1">
                  Confirm Password
                </label>
                <input
                  id="passwordConfirm"
                  type="password"
                  value={passwordConfirm}
                  onChange={(e) => setPasswordConfirm(e.target.value)}
                  placeholder="Confirm your password"
                  className="w-full px-3 py-2 border border-border rounded-lg"
                  disabled={loading}
                />
              </div>

              <Button
                onClick={handleRegister}
                disabled={loading || !email || !password || !passwordConfirm}
                className="w-full"
              >
                {loading ? 'Creating Account...' : 'Create Account & Link Order'}
              </Button>

              <p className="text-xs text-center text-muted-foreground">
                Already have an account?{' '}
                <button
                  type="button"
                  onClick={() => setMode('login')}
                  className="text-primary hover:underline"
                >
                  Login instead
                </button>
              </p>
            </>
          )}

          <div className="pt-4 border-t border-border">
            <button
              type="button"
              onClick={onClose}
              className="w-full text-sm text-muted-foreground hover:text-foreground"
            >
              Skip - Continue as Guest
            </button>
            <p className="text-xs text-center text-muted-foreground mt-2">
              Your order will continue to work without an account
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
