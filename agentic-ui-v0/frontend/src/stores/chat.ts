import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Message, Session } from '../types'

export const useChatStore = defineStore('chat', () => {
  const currentSession = ref<Session | null>(null)
  const isLoading = ref(false)

  const createSession = () => {
    currentSession.value = {
      id: crypto.randomUUID(),
      messages: []
    }
    return currentSession.value
  }

  const addMessage = (content: string, role: 'user' | 'assistant'): Message => {
    if (!currentSession.value) {
      createSession()
    }

    const message: Message = {
      id: crypto.randomUUID(),
      content,
      role,
      timestamp: new Date()
    }

    currentSession.value!.messages.push(message)
    return message
  }

  const clearSession = () => {
    if (currentSession.value) {
      currentSession.value.messages = []
    }
  }

  return {
    currentSession,
    isLoading,
    createSession,
    addMessage,
    clearSession
  }
})