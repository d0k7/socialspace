/**
 * Message Store (Zustand)
 */

import { create } from 'zustand'
import type { Message, MessageFilter } from '@/types/message.types'

interface MessageState {
  messages: Message[]
  unreadCount: number
  filters: MessageFilter
  isLoading: boolean
}

interface MessageActions {
  setMessages: (messages: Message[]) => void
  addMessage: (message: Message) => void
  updateMessage: (messageId: string, updates: Partial<Message>) => void
  markAsRead: (messageId: string) => void
  setFilters: (filters: MessageFilter) => void
  setLoading: (loading: boolean) => void
  getUnreadMessages: () => Message[]
}

type MessageStore = MessageState & MessageActions

/**
 * Message Store
 */
export const useMessageStore = create<MessageStore>((set, get) => ({
  // Initial State
  messages: [],
  unreadCount: 0,
  filters: {},
  isLoading: false,

  // Actions
  setMessages: (messages) =>
    set({
      messages,
      unreadCount: messages.filter((m) => !m.isRead).length,
    }),
  
  addMessage: (message) =>
    set((state) => ({
      messages: [message, ...state.messages],
      unreadCount: message.isRead ? state.unreadCount : state.unreadCount + 1,
    })),
  
  updateMessage: (messageId, updates) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === messageId ? { ...m, ...updates } : m
      ),
    })),
  
  markAsRead: (messageId) =>
    set((state) => {
      const message = state.messages.find((m) => m.id === messageId)
      const wasUnread = message && !message.isRead
      
      return {
        messages: state.messages.map((m) =>
          m.id === messageId ? { ...m, isRead: true } : m
        ),
        unreadCount: wasUnread ? state.unreadCount - 1 : state.unreadCount,
      }
    }),
  
  setFilters: (filters) => set({ filters }),
  
  setLoading: (loading) => set({ isLoading: loading }),
  
  getUnreadMessages: () => {
    const { messages } = get()
    return messages.filter((m) => !m.isRead)
  },
}))
