'use client'

import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import type { CustomerPaymentsResponse } from '@/types/customer'
import { useEffect, useState } from 'react'

interface CustomerPaymentsHistoryProps {
  customerId: number
}

export function CustomerPaymentsHistory({ customerId }: CustomerPaymentsHistoryProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [payments, setPayments] = useState<CustomerPaymentsResponse['data']>([])
  const [meta, setMeta] = useState<CustomerPaymentsResponse['meta'] | null>(null)

  useEffect(() => {
    fetchPayments()
  }, [customerId])

  const fetchPayments = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.get<CustomerPaymentsResponse>(
        ADMIN_ENDPOINTS.CUSTOMERS.PAYMENTS(customerId)
      )
      
      if (response.data.success) {
        setPayments(response.data.data)
        setMeta(response.data.meta)
      } else {
        setError('Failed to load payment history')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load payment history')
      console.error('Error fetching payments:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP',
    }).format(amount)
  }

  if (loading) {
    return <div className="text-center py-8 text-muted-foreground">Loading payment history...</div>
  }

  if (error) {
    return <div className="bg-destructive/10 text-destructive p-4 rounded-lg">{error}</div>
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      {meta && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-card border rounded-lg p-4">
            <div className="text-sm text-muted-foreground">Total Paid</div>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(meta.total_paid)}
            </div>
          </div>
          <div className="bg-card border rounded-lg p-4">
            <div className="text-sm text-muted-foreground">Total Pending</div>
            <div className="text-2xl font-bold text-yellow-600">
              {formatCurrency(meta.total_pending)}
            </div>
          </div>
          <div className="bg-card border rounded-lg p-4">
            <div className="text-sm text-muted-foreground">Transactions</div>
            <div className="text-2xl font-bold">{meta.count}</div>
          </div>
        </div>
      )}

      {/* Payments Table */}
      {payments.length > 0 ? (
        <div className="bg-card border rounded-lg overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase">Date</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase">Order #</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase">Amount</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase">Payment Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase">Order Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {payments.map((payment) => (
                <tr key={payment.id}>
                  <td className="px-4 py-3">{formatDate(payment.date)}</td>
                  <td className="px-4 py-3 font-mono">{payment.order_number}</td>
                  <td className="px-4 py-3 font-semibold">{formatCurrency(payment.amount)}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs ${
                      payment.status === 'paid' ? 'bg-green-100 text-green-800' :
                      payment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      payment.status === 'refunded' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {payment.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs ${
                      payment.order_status === 'completed' ? 'bg-green-100 text-green-800' :
                      payment.order_status === 'cancelled' ? 'bg-red-100 text-red-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {payment.order_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-12 text-muted-foreground">
          No payment history found
        </div>
      )}
    </div>
  )
}
