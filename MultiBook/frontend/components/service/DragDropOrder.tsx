'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'

interface DragDropOrderProps {
  items: Array<{ id: number; name: string; position: number }>
  onReorder: (reorderedItems: Array<{ id: number; position: number }>) => Promise<void>
  itemType: 'service' | 'category'
}

export function DragDropOrder({ items, onReorder, itemType }: DragDropOrderProps) {
  const [draggedItem, setDraggedItem] = useState<number | null>(null)
  const [reorderedItems, setReorderedItems] = useState(items)
  const [saving, setSaving] = useState(false)

  const handleDragStart = (e: React.DragEvent, itemId: number) => {
    setDraggedItem(itemId)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleDrop = (e: React.DragEvent, targetId: number) => {
    e.preventDefault()
    
    if (!draggedItem || draggedItem === targetId) {
      setDraggedItem(null)
      return
    }

    const draggedIndex = reorderedItems.findIndex(item => item.id === draggedItem)
    const targetIndex = reorderedItems.findIndex(item => item.id === targetId)

    if (draggedIndex === -1 || targetIndex === -1) {
      setDraggedItem(null)
      return
    }

    const newItems = [...reorderedItems]
    const [removed] = newItems.splice(draggedIndex, 1)
    newItems.splice(targetIndex, 0, removed)

    // Update positions
    const updatedItems = newItems.map((item, index) => ({
      ...item,
      position: index,
    }))

    setReorderedItems(updatedItems)
    setDraggedItem(null)
  }

  const handleSaveOrder = async () => {
    try {
      setSaving(true)
      
      const reorderData = reorderedItems.map((item, index) => ({
        id: item.id,
        position: index,
      }))

      await onReorder(reorderData)
      
      // Update items with new positions
      const updatedItems = reorderedItems.map((item, index) => ({
        ...item,
        position: index,
      }))
      setReorderedItems(updatedItems)
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to save order')
      console.error('Error saving order:', err)
    } finally {
      setSaving(false)
    }
  }

  const handleReset = () => {
    setReorderedItems(items)
  }

  const hasChanges = JSON.stringify(reorderedItems.map(i => i.id)) !== JSON.stringify(items.map(i => i.id))

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Drag and Drop to Reorder</h3>
        <div className="flex gap-2">
          {hasChanges && (
            <>
              <Button variant="outline" onClick={handleReset} disabled={saving}>
                Reset
              </Button>
              <Button onClick={handleSaveOrder} disabled={saving}>
                {saving ? 'Saving...' : 'Save Order'}
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="bg-card border rounded-lg overflow-x-auto">
        <div className="divide-y divide-border">
          {reorderedItems.map((item, index) => (
            <div
              key={item.id}
              draggable
              onDragStart={(e) => handleDragStart(e, item.id)}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, item.id)}
              className={`px-6 py-4 flex items-center gap-4 cursor-move hover:bg-muted/50 ${
                draggedItem === item.id ? 'opacity-50' : ''
              }`}
            >
              <div className="text-muted-foreground text-sm">#{index}</div>
              <div className="flex-1 font-medium">{item.name}</div>
              <div className="text-sm text-muted-foreground">
                Position: {item.position}
              </div>
              <div className="text-muted-foreground">⋮⋮</div>
            </div>
          ))}
        </div>
      </div>

      {reorderedItems.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          No {itemType}s to reorder
        </div>
      )}
    </div>
  )
}
