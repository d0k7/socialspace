/**
 * Message List Component
 * 
 * Displays list of messages with filtering
 */

import { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import EmptyState from '@/components/common/EmptyState'
import Loading from '@/components/common/Loading'
import { 
  MessageSquare, 
  Search, 
  Filter,
  CheckCircle2,
  Circle,
  MoreVertical,
  Trash2,
  Archive,
} from 'lucide-react'
import { PLATFORM_NAMES, PLATFORM_COLORS, type Platform } from '@/utils/constants'
import type { Message } from '@/types/message.types'
import { getRelativeTime } from '@/lib/utils'
import { cn } from '@/lib/utils'

interface MessageListProps {
  messages?: Message[]
  loading?: boolean
  selectedMessage?: Message | null
  onSelectMessage?: (message: Message) => void
  onMarkAsRead?: (messageId: string) => void
  onArchive?: (messageId: string) => void
  onUnarchive?: (messageId: string) => void
  onDelete?: (messageId: string) => void
  onRestore?: (messageId: string) => void
  onPermanentDelete?: (messageId: string) => void
  showArchived?: boolean
  showTrashed?: boolean
}

export default function MessageList({
  messages = [],
  loading,
  selectedMessage,
  onSelectMessage,
  onMarkAsRead,
  onArchive,
  onUnarchive,
  onDelete,
  onRestore,
  onPermanentDelete,
}: MessageListProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterPlatform, setFilterPlatform] = useState<Platform | 'all'>('all')
  const [filterStatus, setFilterStatus] = useState<'all' | 'read' | 'unread'>('all')
  const [showFilters, setShowFilters] = useState(false)

  // Filter messages
  const filteredMessages = messages.filter((message) => {
    // Search filter
    if (searchQuery && !message.content.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false
    }

    // Platform filter
    if (filterPlatform !== 'all' && message.platform !== filterPlatform) {
      return false
    }

    // Status filter
    if (filterStatus === 'read' && !message.isRead) return false
    if (filterStatus === 'unread' && message.isRead) return false

    return true
  })

  // Get unique platforms from messages
  const platforms = Array.from(new Set(messages.map(m => m.platform)))

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loading size="lg" text="Loading messages..." />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Search & Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="search"
            placeholder="Search messages..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
          />
        </div>

        {/* Filter Button */}
        <Button
          variant="outline"
          onClick={() => setShowFilters(!showFilters)}
          className="gap-2"
        >
          <Filter size={16} />
          Filters
          {(filterPlatform !== 'all' || filterStatus !== 'all') && (
            <Badge variant="default" className="ml-1">
              {(filterPlatform !== 'all' ? 1 : 0) + (filterStatus !== 'all' ? 1 : 0)}
            </Badge>
          )}
        </Button>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <Card className="p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Platform Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Platform
              </label>
              <select
                value={filterPlatform}
                onChange={(e) => setFilterPlatform(e.target.value as Platform | 'all')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="all">All Platforms</option>
                {platforms.map((platform) => (
                  <option key={platform} value={platform}>
                    {PLATFORM_NAMES[platform]}
                  </option>
                ))}
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Status
              </label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value as 'all' | 'read' | 'unread')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="all">All Messages</option>
                <option value="unread">Unread Only</option>
                <option value="read">Read Only</option>
              </select>
            </div>
          </div>

          {/* Clear Filters */}
          {(filterPlatform !== 'all' || filterStatus !== 'all') && (
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setFilterPlatform('all')
                  setFilterStatus('all')
                }}
              >
                Clear All Filters
              </Button>
            </div>
          )}
        </Card>
      )}

      {/* Results Count */}
      <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
        <span>
          {filteredMessages.length} {filteredMessages.length === 1 ? 'message' : 'messages'}
        </span>
        <span>
          {messages.filter(m => !m.isRead).length} unread
        </span>
      </div>

      {/* Message List */}
      {filteredMessages.length === 0 ? (
        <EmptyState
          icon={MessageSquare}
          title={searchQuery ? 'No messages found' : 'No messages yet'}
          description={
            searchQuery
              ? 'Try adjusting your search or filters'
              : 'Messages from your connected platforms will appear here'
          }
        />
      ) : (
        <div className="space-y-2">
          {filteredMessages.map((message) => (
            <MessageListItem
              key={message.id}
              message={message}
              isSelected={selectedMessage?.id === message.id}
              onSelect={() => onSelectMessage?.(message)}
              onMarkAsRead={() => onMarkAsRead?.(message.id)}
              onArchive={onArchive ? () => onArchive(message.id) : undefined}
              onUnarchive={onUnarchive ? () => onUnarchive(message.id) : undefined}
              onDelete={onDelete ? () => onDelete(message.id) : undefined}
              onRestore={onRestore ? () => onRestore(message.id) : undefined}
              onPermanentDelete={onPermanentDelete ? () => onPermanentDelete(message.id) : undefined}
            />
          ))}
        </div>
      )}
    </div>
  )
}

/**
 * Individual Message List Item
 */
interface MessageListItemProps {
  message: Message
  isSelected: boolean
  onSelect: () => void
  onMarkAsRead?: () => void
  onArchive?: () => void
  onUnarchive?: () => void
  onDelete?: () => void
  onRestore?: () => void
  onPermanentDelete?: () => void
}

function MessageListItem({
  message,
  isSelected,
  onSelect,
  onMarkAsRead,
  onArchive,
  onUnarchive,
  onDelete,
  onRestore,
  onPermanentDelete,
}: MessageListItemProps) {
  const [showActions, setShowActions] = useState(false)
  const hasActions =
    (!message.isRead && Boolean(onMarkAsRead)) ||
    Boolean(onArchive) ||
    Boolean(onUnarchive) ||
    Boolean(onRestore) ||
    Boolean(onDelete) ||
    Boolean(onPermanentDelete)

  return (
    <div
      className={cn(
        'relative group p-4 rounded-lg border-2 transition-all cursor-pointer hover:shadow-md',
        isSelected
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600',
        !message.isRead && 'bg-blue-50/50 dark:bg-blue-900/10'
      )}
      onClick={onSelect}
    >
      <div className="flex items-start gap-4">
        {/* Platform Badge */}
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-sm flex-shrink-0 shadow-sm"
          style={{ backgroundColor: PLATFORM_COLORS[message.platform] }}
        >
          {PLATFORM_NAMES[message.platform]?.[0] || '?'}
        </div>

        {/* Message Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-start justify-between gap-2 mb-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-gray-900 dark:text-white">
                {message.sender.displayName || message.sender.username}
              </span>
              <Badge variant="gray" className="text-xs">
                {PLATFORM_NAMES[message.platform]}
              </Badge>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              {!message.isRead && (
                <Circle className="w-2 h-2 fill-blue-600 text-blue-600" />
              )}
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {getRelativeTime(message.timestamp)}
              </span>
            </div>
          </div>

          {/* Message Preview */}
          <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
            {message.content}
          </p>

          {/* Media Indicators */}
          {message.media && message.media.length > 0 && (
            <div className="flex items-center gap-2 mt-2">
              {message.media.map((media, index) => (
                <Badge key={index} variant="gray" className="text-xs">
                  {media.type}
                </Badge>
              ))}
            </div>
          )}
        </div>

      {/* Actions Menu */}
        <div className="relative flex-shrink-0">
          {hasActions && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                setShowActions(!showActions)
              }}
              className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <MoreVertical size={16} className="text-gray-400" />
            </button>
          )}

          {showActions && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={(e) => {
                  e.stopPropagation()
                  setShowActions(false)
                }}
              />
              <div className="absolute right-0 mt-1 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-20">
                {!message.isRead && onMarkAsRead && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onMarkAsRead()
                      setShowActions(false)
                    }}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    <CheckCircle2 size={16} />
                    Mark as Read
                  </button>
                )}
                
                {onArchive && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onArchive()
                      setShowActions(false)
                    }}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    <Archive size={16} />
                    Archive
                  </button>
                )}
                
                {onUnarchive && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onUnarchive()
                      setShowActions(false)
                    }}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    <Archive size={16} />
                    Restore to Inbox
                  </button>
                )}
                
                {onRestore && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onRestore()
                      setShowActions(false)
                    }}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-green-600 dark:text-green-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    <CheckCircle2 size={16} />
                    Restore
                  </button>
                )}
                
                {onDelete && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onDelete()
                      setShowActions(false)
                    }}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    <Trash2 size={16} />
                    {onPermanentDelete ? 'Move to Trash' : 'Delete'}
                  </button>
                )}
                
                {onPermanentDelete && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      if (window.confirm('Permanently delete this message?')) {
                        onPermanentDelete()
                      }
                      setShowActions(false)
                    }}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    <Trash2 size={16} />
                    Delete Permanently
                  </button>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
