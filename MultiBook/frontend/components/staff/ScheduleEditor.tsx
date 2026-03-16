'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import type { StaffSchedule, StaffScheduleCreateRequest } from '@/types/staff'

interface ScheduleEditorProps {
  staffId: number
  schedules: StaffSchedule[]
  onUpdate: () => void
}

const DAYS = [
  { value: 0, label: 'Monday' },
  { value: 1, label: 'Tuesday' },
  { value: 2, label: 'Wednesday' },
  { value: 3, label: 'Thursday' },
  { value: 4, label: 'Friday' },
  { value: 5, label: 'Saturday' },
  { value: 6, label: 'Sunday' },
]

export function ScheduleEditor({ staffId, schedules, onUpdate }: ScheduleEditorProps) {
  const [localSchedules, setLocalSchedules] = useState<StaffSchedule[]>(schedules)
  const [editingSchedule, setEditingSchedule] = useState<StaffSchedule | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    day_of_week: 0,
    start_time: '09:00',
    end_time: '17:00',
    breaks: [] as Array<{ start: string; end: string }>,
    is_active: true,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLocalSchedules(schedules)
  }, [schedules])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (formData.start_time >= formData.end_time) {
      setError('End time must be after start time')
      return
    }

    // Validate breaks
    for (const breakItem of formData.breaks) {
      if (breakItem.start >= breakItem.end) {
        setError('Break end time must be after start time')
        return
      }
      if (breakItem.start < formData.start_time || breakItem.end > formData.end_time) {
        setError('Break times must be within working hours')
        return
      }
    }

    try {
      setLoading(true)
      
      if (editingSchedule?.id) {
        // Update existing schedule
        await apiClient.patch(
          ADMIN_ENDPOINTS.STAFF.SCHEDULES.UPDATE(editingSchedule.id),
          {
            staff: staffId,
            day_of_week: formData.day_of_week,
            start_time: formData.start_time,
            end_time: formData.end_time,
            breaks: formData.breaks,
            is_active: formData.is_active,
          }
        )
      } else {
        // Check if schedule for this day already exists
        const existing = localSchedules.find(s => s.day_of_week === formData.day_of_week)
        if (existing && existing.id) {
          // Update existing
          await apiClient.patch(
            ADMIN_ENDPOINTS.STAFF.SCHEDULES.UPDATE(existing.id),
            {
              staff: staffId,
              day_of_week: formData.day_of_week,
              start_time: formData.start_time,
              end_time: formData.end_time,
              breaks: formData.breaks,
              is_active: formData.is_active,
            }
          )
        } else {
          // Create new schedule
          const request: StaffScheduleCreateRequest = {
            staff: staffId,
            day_of_week: formData.day_of_week,
            start_time: formData.start_time,
            end_time: formData.end_time,
            breaks: formData.breaks,
            is_active: formData.is_active,
          }
          await apiClient.post(ADMIN_ENDPOINTS.STAFF.SCHEDULES.CREATE, request)
        }
      }

      setFormData({ day_of_week: 0, start_time: '09:00', end_time: '17:00', breaks: [], is_active: true })
      setShowForm(false)
      setEditingSchedule(null)
      onUpdate()
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to save schedule')
      console.error('Error saving schedule:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (schedule: StaffSchedule) => {
    setEditingSchedule(schedule)
    setFormData({
      day_of_week: schedule.day_of_week,
      start_time: schedule.start_time,
      end_time: schedule.end_time,
      breaks: schedule.breaks || [],
      is_active: schedule.is_active,
    })
    setShowForm(true)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this schedule?')) {
      return
    }

    try {
      await apiClient.delete(ADMIN_ENDPOINTS.STAFF.SCHEDULES.DELETE(id))
      onUpdate()
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to delete schedule')
      console.error('Error deleting schedule:', err)
    }
  }

  const handleAddBreak = () => {
    setFormData(prev => ({
      ...prev,
      breaks: [...prev.breaks, { start: '12:00', end: '13:00' }],
    }))
  }

  const handleRemoveBreak = (index: number) => {
    setFormData(prev => ({
      ...prev,
      breaks: prev.breaks.filter((_, i) => i !== index),
    }))
  }

  const handleBreakChange = (index: number, field: 'start' | 'end', value: string) => {
    setFormData(prev => ({
      ...prev,
      breaks: prev.breaks.map((b, i) => (i === index ? { ...b, [field]: value } : b)),
    }))
  }

  const handleCancel = () => {
    setShowForm(false)
    setEditingSchedule(null)
    setFormData({ day_of_week: 0, start_time: '09:00', end_time: '17:00', breaks: [], is_active: true })
    setError(null)
  }

  const getScheduleForDay = (day: number) => {
    return localSchedules.find(s => s.day_of_week === day)
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold">Weekly Schedule</h3>
          <p className="text-sm text-muted-foreground">
            Define working hours for each day of the week
          </p>
        </div>
        {!showForm && (
          <Button onClick={() => setShowForm(true)} size="sm">
            Add Schedule
          </Button>
        )}
      </div>

      {/* Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="border rounded-lg p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Day of Week</label>
            <select
              value={formData.day_of_week}
              onChange={(e) => setFormData(prev => ({ ...prev, day_of_week: parseInt(e.target.value) }))}
              className="w-full px-3 py-2 border rounded-md"
              disabled={!!editingSchedule}
              required
            >
              {DAYS.map(day => (
                <option key={day.value} value={day.value}>
                  {day.label}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Start Time</label>
              <input
                type="time"
                value={formData.start_time}
                onChange={(e) => setFormData(prev => ({ ...prev, start_time: e.target.value }))}
                className="w-full px-3 py-2 border rounded-md"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">End Time</label>
              <input
                type="time"
                value={formData.end_time}
                onChange={(e) => setFormData(prev => ({ ...prev, end_time: e.target.value }))}
                className="w-full px-3 py-2 border rounded-md"
                required
              />
            </div>
          </div>

          {/* Breaks */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="block text-sm font-medium">Breaks</label>
              <Button type="button" variant="outline" size="sm" onClick={handleAddBreak}>
                Add Break
              </Button>
            </div>
            {formData.breaks.map((breakItem, index) => (
              <div key={index} className="flex gap-2 items-center mb-2">
                <input
                  type="time"
                  value={breakItem.start}
                  onChange={(e) => handleBreakChange(index, 'start', e.target.value)}
                  className="flex-1 px-3 py-2 border rounded-md"
                />
                <span className="text-muted-foreground">to</span>
                <input
                  type="time"
                  value={breakItem.end}
                  onChange={(e) => handleBreakChange(index, 'end', e.target.value)}
                  className="flex-1 px-3 py-2 border rounded-md"
                />
                <Button
                  type="button"
                  variant="destructive"
                  size="sm"
                  onClick={() => handleRemoveBreak(index)}
                >
                  Remove
                </Button>
              </div>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active_schedule"
              checked={formData.is_active}
              onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
              className="rounded"
            />
            <label htmlFor="is_active_schedule" className="text-sm">
              Active
            </label>
          </div>

          {error && (
            <div className="p-2 bg-destructive/10 text-destructive text-sm rounded">
              {error}
            </div>
          )}

          <div className="flex gap-2">
            <Button type="submit" disabled={loading} size="sm">
              {editingSchedule ? 'Update' : 'Save'} Schedule
            </Button>
            <Button type="button" variant="outline" onClick={handleCancel} size="sm">
              Cancel
            </Button>
          </div>
        </form>
      )}

      {/* Schedule List */}
      <div className="space-y-2">
        {DAYS.map(day => {
          const schedule = getScheduleForDay(day.value)
          return (
            <div
              key={day.value}
              className="flex items-center justify-between border rounded-lg p-3"
            >
              <div className="flex-1">
                <div className="font-medium">{day.label}</div>
                {schedule ? (
                  <div className="text-sm text-muted-foreground">
                    {schedule.start_time} - {schedule.end_time}
                    {schedule.breaks && schedule.breaks.length > 0 && (
                      <span className="ml-2">
                        ({schedule.breaks.length} break{schedule.breaks.length !== 1 ? 's' : ''})
                      </span>
                    )}
                    {!schedule.is_active && (
                      <span className="ml-2 text-destructive">(Inactive)</span>
                    )}
                  </div>
                ) : (
                  <div className="text-sm text-muted-foreground">Not scheduled</div>
                )}
              </div>
              {schedule && schedule.id && (
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEdit(schedule)}
                  >
                    Edit
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleDelete(schedule.id!)}
                  >
                    Delete
                  </Button>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
