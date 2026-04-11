/**
 * Message Detail Component
 * 
 * Shows full message details with reply functionality
 */

import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import EmptyState from '@/components/common/EmptyState'
import { 
  MessageSquare,
  Send,
  Image,
  Video,
  File,
  ExternalLink,
  Copy,
  Check,
} from 'lucide-react'
import { PLATFORM_NAMES, PLATFORM_COLORS } from '@/utils/constants'
import type { Message } from '@/types/message.types'
import { formatDate } from '@/lib/utils'
import toast from 'react-hot-toast'

interface MessageDetailProps {
  message?: Message | null
  onReply?: (content: string) => void
  replying?: boolean
  showReply?: boolean
}

export default function MessageDetail({ message, onReply, replying, showReply = true }: MessageDetailProps) {
  const [replyText, setReplyText] = useState('')
  const [copied, setCopied] = useState(false)

  const handleReply = () => {
    if (!replyText.trim()) {
      toast.error('Please enter a message')
      return
    }

    onReply?.(replyText)
    setReplyText('')
  }

  const handleCopy = () => {
    if (message) {
      navigator.clipboard.writeText(message.content)
      setCopied(true)
      toast.success('Copied to clipboard')
      setTimeout(() => setCopied(false), 2000)
    }
  }

  if (!message) {
    return (
      <Card className="h-full flex items-center justify-center">
        <EmptyState
          icon={<MessageSquare className="w-8 h-8 text-gray-400 dark:text-gray-600" />}
          title="No message selected"
          description="Select a message from the list to view details"
        />
      </Card>
    )
  }

  const getMediaIcon = (type: string) => {
    switch (type) {
      case 'image':
        return Image
      case 'video':
        return Video
      default:
        return File
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <Card className="mb-4">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              {/* Platform Badge */}
              <div
                className="w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold shadow-sm"
                style={{ backgroundColor: PLATFORM_COLORS[message.platform] }}
              >
                {PLATFORM_NAMES[message.platform]?.[0] || '?'}
              </div>

              {/* Sender Info */}
              <div>
                <CardTitle className="text-lg">
                  {message.sender.displayName || message.sender.username}
                </CardTitle>
                <div className="flex items-center gap-2 mt-1">
                  <Badge variant="gray">
                    {PLATFORM_NAMES[message.platform]}
                  </Badge>
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {formatDate(new Date(message.timestamp))}
                  </span>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCopy}
                className="gap-2"
              >
                {copied ? <Check size={16} /> : <Copy size={16} />}
                {copied ? 'Copied' : 'Copy'}
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Message Content */}
      <Card className="flex-1 mb-4">
        <CardContent className="p-6">
          <div className="prose dark:prose-invert max-w-none">
            <p className="text-gray-900 dark:text-white whitespace-pre-wrap">
              {message.content}
            </p>
          </div>

          {/* Media Attachments */}
          {message.media && message.media.length > 0 && (
            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                Attachments ({message.media.length})
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {message.media.map((media, index) => {
                  const MediaIcon = getMediaIcon(media.type)
                  return (
                    <a
                      key={index}
                      href={media.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-3 p-3 border-2 border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-500 dark:hover:border-blue-500 transition-colors group"
                    >
                      <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                        <MediaIcon className="text-gray-600 dark:text-gray-400" size={20} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {media.type}.{media.url.split('.').pop()}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {media.type}
                        </p>
                      </div>
                      <ExternalLink className="text-gray-400 group-hover:text-blue-500" size={16} />
                    </a>
                  )
                })}
              </div>
            </div>
          )}

          {/* Metadata */}
          {message.metadata && Object.keys(message.metadata).length > 0 && (
            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                Additional Info
              </h4>
              <dl className="grid grid-cols-2 gap-3 text-sm">
                {Object.entries(message.metadata).map(([key, value]) => (
                  <div key={key}>
                    <dt className="text-gray-500 dark:text-gray-400 capitalize">
                      {key.replace(/_/g, ' ')}
                    </dt>
                    <dd className="text-gray-900 dark:text-white font-medium mt-1">
                      {String(value)}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Reply Section - Only show if not in trash */}
      {showReply && (
        <Card>
          <CardContent className="p-4">
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <Send size={16} />
                <span>Reply to {message.sender.displayName || message.sender.username}</span>
              </div>
              <textarea
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                placeholder="Type your reply..."
                rows={4}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white resize-none"
                disabled={replying}
              />
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {replyText.length} characters
                </span>
                <Button
                  onClick={handleReply}
                  disabled={!replyText.trim() || replying}
                  loading={replying}
                  className="gap-2"
                >
                  <Send size={16} />
                  Send Reply
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
