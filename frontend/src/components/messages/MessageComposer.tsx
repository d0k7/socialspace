/**
 * Message Composer Component
 * 
 * Compose and send new messages
 */

import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { 
  Send, 
  Image, 
  Paperclip,
  X,
  Smile,
} from 'lucide-react'
import { PLATFORMS, PLATFORM_NAMES, PLATFORM_COLORS, type Platform } from '@/utils/constants'
import toast from 'react-hot-toast'

interface MessageComposerProps {
  onSend?: (platform: Platform, content: string) => void
  sending?: boolean
}

export default function MessageComposer({ onSend, sending }: MessageComposerProps) {
  const [selectedPlatforms, setSelectedPlatforms] = useState<Platform[]>([])
  const [content, setContent] = useState('')
  const [attachments, setAttachments] = useState<File[]>([])

  const handleTogglePlatform = (platform: Platform) => {
    setSelectedPlatforms(prev => 
      prev.includes(platform)
        ? prev.filter(p => p !== platform)
        : [...prev, platform]
    )
  }

  const handleSend = () => {
    if (!content.trim()) {
      toast.error('Please enter a message')
      return
    }

    if (selectedPlatforms.length === 0) {
      toast.error('Please select at least one platform')
      return
    }

    // Send to each platform
    selectedPlatforms.forEach(platform => {
      onSend?.(platform, content)
    })

    // Reset form
    setContent('')
    setAttachments([])
    setSelectedPlatforms([])
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    setAttachments(prev => [...prev, ...files])
  }

  const handleRemoveAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index))
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Send size={20} />
          Compose Message
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Platform Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Select Platforms
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
            {Object.values(PLATFORMS).map((platform) => {
              const isSelected = selectedPlatforms.includes(platform)
              return (
                <button
                  key={platform}
                  onClick={() => handleTogglePlatform(platform)}
                  className={`flex items-center gap-2 p-3 rounded-lg border-2 transition-all ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold"
                    style={{ backgroundColor: PLATFORM_COLORS[platform] }}
                  >
                    {PLATFORM_NAMES[platform]?.[0] || '?'}
                  </div>
                  <span className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {PLATFORM_NAMES[platform]}
                  </span>
                </button>
              )
            })}
          </div>
          {selectedPlatforms.length > 0 && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              Selected: {selectedPlatforms.length} platform{selectedPlatforms.length > 1 ? 's' : ''}
            </p>
          )}
        </div>

        {/* Message Content */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Message
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Type your message..."
            rows={6}
            className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white resize-none"
            disabled={sending}
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            {content.length} characters
          </p>
        </div>

        {/* Attachments */}
        {attachments.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Attachments
            </label>
            <div className="space-y-2">
              {attachments.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <Paperclip size={16} className="text-gray-400" />
                    <span className="text-sm text-gray-900 dark:text-white">
                      {file.name}
                    </span>
                    <Badge variant="gray" className="text-xs">
                      {(file.size / 1024).toFixed(1)} KB
                    </Badge>
                  </div>
                  <button
                    onClick={() => handleRemoveAttachment(index)}
                    className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                  >
                    <X size={16} className="text-gray-400" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <label className="cursor-pointer">
              <input
                type="file"
                multiple
                onChange={handleFileSelect}
                className="hidden"
                disabled={sending}
              />
              <div className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                <Image size={20} className="text-gray-600 dark:text-gray-400" />
              </div>
            </label>
            <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
              <Smile size={20} className="text-gray-600 dark:text-gray-400" />
            </button>
          </div>

          <Button
            onClick={handleSend}
            disabled={!content.trim() || selectedPlatforms.length === 0 || sending}
            loading={sending}
            className="gap-2"
          >
            <Send size={16} />
            Send to {selectedPlatforms.length} Platform{selectedPlatforms.length !== 1 ? 's' : ''}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}