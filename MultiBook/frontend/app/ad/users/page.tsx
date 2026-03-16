'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import { useEffect, useState } from 'react'
import { useAuthContext } from '@/components/auth/AuthProvider'

interface User {
  id: number
  email: string
  username?: string | null
  role: 'admin' | 'manager' | 'staff' | 'customer'
  first_name?: string | null
  last_name?: string | null
  is_active: boolean
  is_verified: boolean
  date_joined: string
}

interface UserListResponse {
  success: boolean
  data: User[]
  meta: {
    count: number
  }
}

type RoleFilter = 'all' | 'admin' | 'manager' | 'staff' | 'customer'

/**
 * Admin Users Management Page
 * Route: /ad/users (Security: /ad/)
 */
export default function AdminUsersPage() {
  const { user: currentUser } = useAuthContext()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [roleFilter, setRoleFilter] = useState<RoleFilter>('all')
  const [activeFilter, setActiveFilter] = useState<boolean | null>(null)
  const [verifiedFilter, setVerifiedFilter] = useState<boolean | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [editingUser, setEditingUser] = useState<User | null>(null)

  useEffect(() => {
    fetchUsers()
  }, [roleFilter, activeFilter, verifiedFilter, searchQuery])

  const fetchUsers = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const params = new URLSearchParams()
      if (roleFilter !== 'all') {
        params.append('role', roleFilter)
      }
      if (activeFilter !== null) {
        params.append('is_active', activeFilter.toString())
      }
      if (verifiedFilter !== null) {
        params.append('is_verified', verifiedFilter.toString())
      }
      if (searchQuery.trim()) {
        params.append('search', searchQuery.trim())
      }
      
      const url = `${ADMIN_ENDPOINTS.USERS.LIST}${params.toString() ? '?' + params.toString() : ''}`
      const response = await apiClient.get<UserListResponse>(url)
      
      if (response.data.success && response.data.data) {
        setUsers(response.data.data)
      } else {
        setError('Failed to load users')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load users')
      console.error('Error fetching users:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateUser = async (userId: number, updates: Partial<User>) => {
    try {
      await apiClient.patch(ADMIN_ENDPOINTS.USERS.UPDATE(userId), updates)
      fetchUsers() // Refresh list
      setEditingUser(null)
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to update user')
      console.error('Error updating user:', err)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
      return
    }

    try {
      await apiClient.delete(ADMIN_ENDPOINTS.USERS.DELETE(id))
      fetchUsers() // Refresh list
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to delete user')
      console.error('Error deleting user:', err)
    }
  }

  const _toggleActive = async (user: User) => {
    await handleUpdateUser(user.id, { is_active: !user.is_active })
  }

  const _toggleVerified = async (user: User) => {
    await handleUpdateUser(user.id, { is_verified: !user.is_verified })
  }

  const _changeRole = async (user: User, newRole: User['role']) => {
    if (!confirm(`Change ${user.email}'s role from ${user.role} to ${newRole}?`)) {
      return
    }
    await handleUpdateUser(user.id, { role: newRole })
  }

  const getRoleColor = (role: User['role']) => {
    const colors = {
      admin: 'bg-purple-100 text-purple-800',
      manager: 'bg-blue-100 text-blue-800',
      staff: 'bg-green-100 text-green-800',
      customer: 'bg-gray-100 text-gray-800',
    }
    return colors[role]
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold mb-2">User Management</h1>
              <p className="text-muted-foreground">
                Manage all users across all roles (customers, staff, managers, admins)
              </p>
            </div>
          </div>

          {/* Search */}
          <div className="mb-6">
            <input
              type="text"
              placeholder="Search by email, username, or name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full max-w-md px-4 py-2 border rounded-md"
            />
          </div>

          {/* Filters */}
          <div className="mb-6 flex flex-wrap gap-4">
            <div className="flex gap-2">
              <span className="text-sm font-medium py-2">Role:</span>
              <Button
                variant={roleFilter === 'all' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setRoleFilter('all')}
              >
                All
              </Button>
              <Button
                variant={roleFilter === 'customer' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setRoleFilter('customer')}
              >
                Customers
              </Button>
              <Button
                variant={roleFilter === 'staff' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setRoleFilter('staff')}
              >
                Staff
              </Button>
              <Button
                variant={roleFilter === 'manager' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setRoleFilter('manager')}
              >
                Managers
              </Button>
              <Button
                variant={roleFilter === 'admin' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setRoleFilter('admin')}
              >
                Admins
              </Button>
            </div>

            <div className="flex gap-2">
              <span className="text-sm font-medium py-2">Status:</span>
              <Button
                variant={activeFilter === null ? 'default' : 'outline'}
                size="sm"
                onClick={() => setActiveFilter(null)}
              >
                All
              </Button>
              <Button
                variant={activeFilter === true ? 'default' : 'outline'}
                size="sm"
                onClick={() => setActiveFilter(true)}
              >
                Active
              </Button>
              <Button
                variant={activeFilter === false ? 'default' : 'outline'}
                size="sm"
                onClick={() => setActiveFilter(false)}
              >
                Inactive
              </Button>
            </div>

            <div className="flex gap-2">
              <span className="text-sm font-medium py-2">Verified:</span>
              <Button
                variant={verifiedFilter === null ? 'default' : 'outline'}
                size="sm"
                onClick={() => setVerifiedFilter(null)}
              >
                All
              </Button>
              <Button
                variant={verifiedFilter === true ? 'default' : 'outline'}
                size="sm"
                onClick={() => setVerifiedFilter(true)}
              >
                Verified
              </Button>
              <Button
                variant={verifiedFilter === false ? 'default' : 'outline'}
                size="sm"
                onClick={() => setVerifiedFilter(false)}
              >
                Unverified
              </Button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-4 bg-destructive/10 text-destructive rounded-md">
              {error}
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
              <p className="mt-4 text-muted-foreground">Loading users...</p>
            </div>
          )}

          {/* Users Table */}
          {!loading && !error && (
            <div className="rounded-lg border overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="text-left p-3">User</th>
                    <th className="text-left p-3">Role</th>
                    <th className="text-left p-3">Status</th>
                    <th className="text-left p-3">Verified</th>
                    <th className="text-left p-3">Joined</th>
                    <th className="text-left p-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center py-12 text-muted-foreground">
                        No users found
                      </td>
                    </tr>
                  ) : (
                    users.map((user) => {
                      const displayName = user.first_name && user.last_name
                        ? `${user.first_name} ${user.last_name}`
                        : user.email
                      const isCurrentUser = currentUser?.id === user.id
                      
                      return (
                        <tr key={user.id} className="border-b hover:bg-muted/30">
                          <td className="p-3">
                            <div>
                              <div className="font-medium">{displayName}</div>
                              <div className="text-xs text-muted-foreground">{user.email}</div>
                              {user.username && (
                                <div className="text-xs text-muted-foreground">@{user.username}</div>
                              )}
                            </div>
                          </td>
                          <td className="p-3">
                            {editingUser?.id === user.id ? (
                              <select
                                value={editingUser.role}
                                onChange={(e) => setEditingUser({ ...editingUser, role: e.target.value as User['role'] })}
                                className="px-2 py-1 border rounded text-xs"
                                disabled={isCurrentUser}
                              >
                                <option value="customer">Customer</option>
                                <option value="staff">Staff</option>
                                <option value="manager">Manager</option>
                                <option value="admin">Admin</option>
                              </select>
                            ) : (
                              <span className={`px-2 py-1 text-xs rounded ${getRoleColor(user.role)}`}>
                                {user.role.toUpperCase()}
                              </span>
                            )}
                          </td>
                          <td className="p-3">
                            {editingUser?.id === user.id ? (
                              <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={editingUser.is_active}
                                  onChange={(e) => setEditingUser({ ...editingUser, is_active: e.target.checked })}
                                  disabled={isCurrentUser}
                                  className="cursor-pointer"
                                />
                                <span className="text-xs">Active</span>
                              </label>
                            ) : (
                              <span
                                className={`px-2 py-1 text-xs rounded ${
                                  user.is_active
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}
                              >
                                {user.is_active ? 'Active' : 'Inactive'}
                              </span>
                            )}
                          </td>
                          <td className="p-3">
                            {editingUser?.id === user.id ? (
                              <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={editingUser.is_verified}
                                  onChange={(e) => setEditingUser({ ...editingUser, is_verified: e.target.checked })}
                                  className="cursor-pointer"
                                />
                                <span className="text-xs">Verified</span>
                              </label>
                            ) : (
                              <span
                                className={`px-2 py-1 text-xs rounded ${
                                  user.is_verified
                                    ? 'bg-blue-100 text-blue-800'
                                    : 'bg-yellow-100 text-yellow-800'
                                }`}
                              >
                                {user.is_verified ? 'Verified' : 'Unverified'}
                              </span>
                            )}
                          </td>
                          <td className="p-3 text-xs text-muted-foreground">
                            {formatDate(user.date_joined)}
                          </td>
                          <td className="p-3">
                            {editingUser?.id === user.id ? (
                              <div className="flex gap-2">
                                <Button
                                  size="sm"
                                  variant="default"
                                  onClick={() => {
                                    handleUpdateUser(editingUser.id, {
                                      role: editingUser.role,
                                      is_active: editingUser.is_active,
                                      is_verified: editingUser.is_verified,
                                    })
                                  }}
                                >
                                  Save
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => setEditingUser(null)}
                                >
                                  Cancel
                                </Button>
                              </div>
                            ) : (
                              <div className="flex gap-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => setEditingUser(user)}
                                >
                                  Edit
                                </Button>
                                {!isCurrentUser && (
                                  <Button
                                    size="sm"
                                    variant="destructive"
                                    onClick={() => handleDelete(user.id)}
                                  >
                                    Delete
                                  </Button>
                                )}
                              </div>
                            )}
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* Summary */}
          {!loading && users.length > 0 && (
            <div className="mt-6 text-sm text-muted-foreground">
              Showing {users.length} user{users.length !== 1 ? 's' : ''}
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
