/**
 * Navigation Bar Component
 * 
 * Role-based navigation with logout functionality.
 * Mobile-responsive with hamburger menu.
 */
'use client'

import Link from 'next/link'
import { useState } from 'react'
import { useAuthContext } from '@/components/auth/AuthProvider'
import type { UserRole } from '@/types/auth'

export function Navbar() {
  const { user, isAuthenticated, logout } = useAuthContext()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  if (!isAuthenticated || !user) {
    return (
      <nav className="border-b bg-background sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <Link href="/" className="text-xl font-bold">
            MultiBook
          </Link>
          {/* Desktop Navigation */}
          <div className="hidden md:flex gap-4">
            <Link href="/login" className="text-sm hover:underline py-2 px-3 rounded-md hover:bg-muted transition-colors">
              Login
            </Link>
            <Link href="/register" className="text-sm hover:underline py-2 px-3 rounded-md hover:bg-muted transition-colors">
              Register
            </Link>
            <Link href="/booking" className="text-sm hover:underline py-2 px-3 rounded-md hover:bg-muted transition-colors">
              Book Now
            </Link>
          </div>
          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-md hover:bg-muted transition-colors"
            aria-label="Toggle menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {mobileMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>
        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t bg-background">
            <div className="container mx-auto px-4 py-4 flex flex-col gap-2">
              <Link 
                href="/login" 
                className="text-sm py-3 px-4 rounded-md hover:bg-muted transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                Login
              </Link>
              <Link 
                href="/register" 
                className="text-sm py-3 px-4 rounded-md hover:bg-muted transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                Register
              </Link>
              <Link 
                href="/booking" 
                className="text-sm py-3 px-4 rounded-md hover:bg-muted transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                Book Now
              </Link>
            </div>
          </div>
        )}
      </nav>
    )
  }

  const rolePrefix = getRolePrefix(user.role)
  const userDisplayName = user.first_name && user.last_name 
    ? `${user.first_name} ${user.last_name}`
    : user.email

  // Get navigation links based on role
  const getNavLinks = () => {
    if (user.role === 'customer') {
      return [
        { href: '/cus/dashboard', label: 'Dashboard' },
        { href: '/cus/bookings', label: 'Bookings' },
        { href: '/cus/calendar', label: 'Calendar' },
        { href: '/cus/subscriptions', label: 'Subscriptions' },
        { href: '/cus/orders', label: 'Orders' },
        { href: '/cus/payments', label: 'Payments' },
        { href: '/cus/profile', label: 'Profile' },
      ]
    } else if (user.role === 'staff') {
      return [
        { href: '/st/dashboard', label: 'Dashboard' },
        { href: '/st/jobs', label: 'Jobs' },
        { href: '/st/schedule', label: 'Schedule' },
        { href: '/st/calendar', label: 'Calendar' },
        { href: '/st/services', label: 'Services' },
        { href: '/st/areas', label: 'Areas' },
      ]
    } else if (user.role === 'manager') {
      return [
        { href: '/man/dashboard', label: 'Dashboard' },
        { href: '/man/appointments', label: 'Appointments' },
        { href: '/man/staff', label: 'Staff' },
        { href: '/man/customers', label: 'Customers' },
        { href: '/settings/calendar', label: 'Calendar' },
      ]
    } else if (user.role === 'admin') {
      return [
        { href: '/ad/dashboard', label: 'Dashboard' },
        { href: '/ad/users', label: 'Users' },
        { href: '/ad/orders', label: 'Orders' },
        { href: '/ad/appointments', label: 'Appointments' },
        { href: '/ad/staff', label: 'Staff' },
        { href: '/ad/customers', label: 'Customers' },
        { href: '/ad/managers', label: 'Managers' },
        { href: '/ad/services', label: 'Services' },
        { href: '/ad/coupons', label: 'Coupons' },
        { href: '/ad/reports/revenue', label: 'Reports' },
        { href: '/ad/calendar', label: 'Calendar' },
      ]
    }
    return []
  }

  const navLinks = getNavLinks()

  return (
    <nav className="border-b bg-background sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <Link href={`/${rolePrefix}/dashboard`} className="text-xl font-bold">
          MultiBook
        </Link>
        
        {/* Desktop Navigation */}
        <div className="hidden lg:flex gap-2 items-center">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm py-2 px-3 rounded-md hover:bg-muted transition-colors min-h-[44px] flex items-center"
            >
              {link.label}
            </Link>
          ))}
          
          {/* User info and logout */}
          <div className="flex items-center gap-4 border-l pl-4 ml-2">
            <span className="text-sm text-muted-foreground hidden xl:inline">
              {userDisplayName}
            </span>
            <span className="text-xs px-2 py-1 bg-primary/10 text-primary rounded min-h-[44px] flex items-center">
              {user.role.toUpperCase()}
            </span>
            <button
              onClick={() => logout()}
              className="text-sm text-destructive hover:underline py-2 px-3 rounded-md hover:bg-muted transition-colors min-h-[44px] flex items-center"
            >
              Logout
            </button>
          </div>
        </div>

        {/* Mobile Menu Button */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="lg:hidden p-2 rounded-md hover:bg-muted transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
          aria-label="Toggle menu"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {mobileMenuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t bg-background">
          <div className="container mx-auto px-4 py-4 flex flex-col gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-sm py-3 px-4 rounded-md hover:bg-muted transition-colors min-h-[44px] flex items-center"
                onClick={() => setMobileMenuOpen(false)}
              >
                {link.label}
              </Link>
            ))}
            <div className="border-t pt-3 mt-2">
              <div className="text-sm text-muted-foreground px-4 py-2">
                {userDisplayName}
              </div>
              <div className="px-4 py-2">
                <span className="text-xs px-2 py-1 bg-primary/10 text-primary rounded">
                  {user.role.toUpperCase()}
                </span>
              </div>
              <button
                onClick={() => {
                  logout()
                  setMobileMenuOpen(false)
                }}
                className="text-sm text-destructive hover:underline py-3 px-4 rounded-md hover:bg-muted transition-colors min-h-[44px] w-full text-left"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      )}
    </nav>
  )
}

function getRolePrefix(role: UserRole): string {
  const roleMap: Record<UserRole, string> = {
    customer: 'cus',
    staff: 'st',
    manager: 'man',
    admin: 'ad',
  }
  return roleMap[role] || 'cus'
}
