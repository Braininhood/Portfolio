/**
 * Dashboard Layout Component
 * 
 * Common layout for all dashboard pages with navigation.
 */
'use client'

import { Navbar } from '@/components/navigation/Navbar'

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main>{children}</main>
    </div>
  )
}
