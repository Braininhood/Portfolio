'use client'

/**
 * Admin: Bulk calendar sync.
 * Route: /ad/settings/calendar
 *
 * Purpose: Trigger a one-time sync of appointments to the connected calendar
 * (Google/Outlook) for selected staff. Each staff member must have a linked
 * login account and have connected a calendar in their own settings; this page
 * only runs "sync now" for them in bulk (e.g. after a data fix or to refresh calendars).
 */
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS, CALENDAR_ENDPOINTS } from '@/lib/api/endpoints'
import Link from 'next/link'

interface StaffItem {
  id: number
  user?: number | null
  name: string
  email?: string
}
interface BulkResult {
  user_id: number
  synced_count: number
  error?: string
}

export default function AdminCalendarBulkSyncPage() {
  const _router = useRouter()
  const [staffList, setStaffList] = useState<StaffItem[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [results, setResults] = useState<BulkResult[] | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    fetchStaff()
  }, [])

  const fetchStaff = async () => {
    try {
      setLoading(true)
      const res = await apiClient.get(ADMIN_ENDPOINTS.STAFF.LIST)
      const data = res.data?.results ?? res.data?.data ?? res.data
      const raw = Array.isArray(data) ? data : (data?.staff ?? data?.list ?? [])
      const list = raw.map((s: any) => ({
        id: s.id,
        user: s.user != null ? (typeof s.user === 'object' ? s.user?.id : s.user) : (s.user_id ?? null),
        name: s.name ?? s.user_email ?? '',
        email: s.email ?? s.user_email ?? '',
      }))
      setStaffList(list)
    } catch (_e) {
      setMessage({ type: 'error', text: 'Failed to load staff list' })
    } finally {
      setLoading(false)
    }
  }

  const userIds = staffList.filter((s) => s.user).map((s) => s.user as number)

  const toggleAll = () => {
    if (selectedIds.size === userIds.length) setSelectedIds(new Set())
    else setSelectedIds(new Set(userIds))
  }

  const toggleOne = (uid: number) => {
    const next = new Set(selectedIds)
    if (next.has(uid)) next.delete(uid)
    else next.add(uid)
    setSelectedIds(next)
  }

  const handleBulkSync = async () => {
    const ids = Array.from(selectedIds)
    if (ids.length === 0) {
      setMessage({ type: 'error', text: 'Select at least one user.' })
      return
    }
    try {
      setSyncing(true)
      setMessage(null)
      setResults(null)
      const res = await apiClient.post(CALENDAR_ENDPOINTS.SYNC_BULK, { user_ids: ids })
      if (res.data?.success && res.data?.data?.results) {
        setResults(res.data.data.results)
        const total = res.data.data.results.reduce((s: number, r: BulkResult) => s + r.synced_count, 0)
        setMessage({ type: 'success', text: `Bulk sync finished. Total events synced: ${total}.` })
      } else {
        setMessage({ type: 'error', text: res.data?.error?.message || 'Bulk sync failed' })
      }
    } catch (e: any) {
      setMessage({ type: 'error', text: e.response?.data?.error?.message || 'Bulk sync failed' })
    } finally {
      setSyncing(false)
    }
  }

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8 space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">Bulk calendar sync</h1>
            <Link href="/settings/calendar">
              <Button variant="outline">My calendar settings</Button>
            </Link>
          </div>

          {message && (
            <div
              className={`rounded-lg border p-4 ${
                message.type === 'success' ? 'border-green-200 bg-green-50' : 'border-destructive/50 bg-destructive/10 text-destructive'
              }`}
            >
              {message.text}
            </div>
          )}

          <p className="text-muted-foreground">
            Run a one-time sync of appointments into the connected calendar (Google/Outlook) for selected staff. Only staff with a linked login account can be synced; they must connect a calendar in Settings → Calendar first. Select rows below and click &quot;Sync selected&quot; to run sync for them.
          </p>

          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </div>
          ) : (
            <>
              <div className="flex items-center gap-4">
                <Button onClick={toggleAll} variant="outline" size="sm">
                  {selectedIds.size === userIds.length ? 'Deselect all' : 'Select all'}
                </Button>
                <Button onClick={handleBulkSync} disabled={syncing || selectedIds.size === 0}>
                  {syncing ? 'Syncing…' : `Sync selected (${selectedIds.size})`}
                </Button>
              </div>

              <div className="rounded-lg border overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3 w-10">
                        <input
                          type="checkbox"
                          checked={userIds.length > 0 && selectedIds.size === userIds.length}
                          onChange={toggleAll}
                        />
                      </th>
                      <th className="text-left p-3">Staff</th>
                      <th className="text-left p-3">Account (ID)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {staffList.map((s) => (
                      <tr key={s.id} className="border-b">
                        <td className="p-3">
                          {s.user != null && (
                            <input
                              type="checkbox"
                              checked={selectedIds.has(s.user)}
                              onChange={() => toggleOne(s.user!)}
                            />
                          )}
                        </td>
                        <td className="p-3">{s.name ?? s.email ?? `Staff #${s.id}`}</td>
                        <td className="p-3">{s.user != null ? String(s.user) : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {staffList.length === 0 && <p className="text-muted-foreground">No staff found.</p>}
              {staffList.length > 0 && userIds.length === 0 && (
                <p className="text-muted-foreground text-sm">
                  No staff have a linked login account (Account column shows —). Link staff to users in Staff management to enable bulk sync.
                </p>
              )}

              {results && (
                <div className="rounded-lg border p-4">
                  <h3 className="font-semibold mb-2">Last run results</h3>
                  <ul className="space-y-1 text-sm">
                    {results.map((r) => (
                      <li key={r.user_id}>
                        User {r.user_id}: {r.synced_count} synced{r.error ? ` — ${r.error}` : ''}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
