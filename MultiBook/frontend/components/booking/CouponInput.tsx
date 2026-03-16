'use client'

import { useState } from 'react'
import { apiClient } from '@/lib/api/client'
import { PUBLIC_ENDPOINTS } from '@/lib/api/endpoints'
import { Button } from '@/components/ui/button'

interface CouponInputProps {
  orderAmount: number
  serviceIds?: number[]
  customerId?: number
  onCouponApplied: (coupon: {
    code: string
    discountAmount: string
    finalAmount: string
  }) => void
  onCouponRemoved: () => void
  appliedCoupon?: {
    code: string
    discountAmount: string
    finalAmount: string
  } | null
}

/**
 * Coupon Input Component
 * Allows users to enter and validate coupon codes
 */
export function CouponInput({
  orderAmount,
  serviceIds = [],
  customerId,
  onCouponApplied,
  onCouponRemoved,
  appliedCoupon,
}: CouponInputProps) {
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [_validating, setValidating] = useState(false)

  const handleValidate = async () => {
    if (!code.trim()) {
      setError('Please enter a coupon code')
      return
    }

    setLoading(true)
    setError(null)
    setValidating(true)

    try {
      const response = await apiClient.post(PUBLIC_ENDPOINTS.COUPONS.VALIDATE, {
        code: code.trim().toUpperCase(),
        order_amount: orderAmount,
        service_ids: serviceIds,
        customer_id: customerId,
      })

      if (response.data.success) {
        const couponData = response.data.data
        onCouponApplied({
          code: couponData.coupon.code,
          discountAmount: couponData.discount_amount,
          finalAmount: couponData.final_amount,
        })
        setCode('')
        setError(null)
      } else {
        setError(response.data.error?.message || 'Invalid coupon code')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to validate coupon')
    } finally {
      setLoading(false)
      setValidating(false)
    }
  }

  const handleRemove = () => {
    setCode('')
    setError(null)
    onCouponRemoved()
  }

  return (
    <div className="space-y-2">
      {appliedCoupon ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex justify-between items-center">
            <div>
              <div className="font-medium text-green-800">Coupon Applied: {appliedCoupon.code}</div>
              <div className="text-sm text-green-600">
                Discount: £{parseFloat(appliedCoupon.discountAmount).toFixed(2)}
              </div>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleRemove}
              className="min-h-[44px]"
            >
              Remove
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              placeholder="Enter coupon code"
              className="flex-1 px-4 py-3 border rounded-md min-h-[44px] text-base"
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  handleValidate()
                }
              }}
            />
            <Button
              type="button"
              onClick={handleValidate}
              disabled={loading || !code.trim()}
              className="min-h-[44px]"
            >
              {loading ? 'Validating...' : 'Apply'}
            </Button>
          </div>
          {error && (
            <div className="text-sm text-destructive">{error}</div>
          )}
        </div>
      )}
    </div>
  )
}
