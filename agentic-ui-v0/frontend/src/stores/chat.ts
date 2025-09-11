import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import type { Message, Session } from '../types'

export const useChatStore = defineStore('chat', () => {
  const currentSession = ref<Session | null>(null)
  const sessions = ref<Session[]>([])
  const isLoading = ref(false)

  // Load session history from backend
  const loadSessionHistory = async (sessionId: string): Promise<Session | null> => {
    try {
      const response = await axios.get(`/api/sessions/${sessionId}/messages`)
      const sessionData: Session = {
        id: sessionId,
        messages: response.data.messages.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        })),
        createdAt: response.data.messages[0] ? new Date(response.data.messages[0].timestamp) : new Date()
      }
      
      // Add to sessions if not already present
      const existingIndex = sessions.value.findIndex(s => s.id === sessionId)
      if (existingIndex === -1) {
        sessions.value.unshift(sessionData)
      } else {
        sessions.value[existingIndex] = sessionData
      }
      
      return sessionData
    } catch (error) {
      console.error('Error loading session history:', error)
      return null
    }
  }

  // Switch to different session
  const switchToSession = async (sessionId: string) => {
    const existingSession = sessions.value.find(s => s.id === sessionId)
    if (existingSession) {
      currentSession.value = existingSession
    } else {
      const loadedSession = await loadSessionHistory(sessionId)
      if (loadedSession) {
        currentSession.value = loadedSession
      }
    }
  }

  // Create new session
  const createSession = () => {
    const newSession: Session = {
      id: crypto.randomUUID(),
      messages: [],
      createdAt: new Date()
    }
    
    sessions.value.unshift(newSession)
    currentSession.value = newSession
    return newSession
  }

  // Delete session
  const deleteSession = (sessionId: string) => {
    sessions.value = sessions.value.filter(s => s.id !== sessionId)
    if (currentSession.value?.id === sessionId) {
      currentSession.value = sessions.value[0] || null
      if (!currentSession.value) {
        createSession()
      }
    }
  }

  // Add message to current session
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
    
    // Update the session in sessions array
    const sessionIndex = sessions.value.findIndex(s => s.id === currentSession.value!.id)
    if (sessionIndex !== -1) {
      sessions.value[sessionIndex] = { ...currentSession.value! }
    }
    
    return message
  }

  // Clear current session
  const clearSession = () => {
    if (currentSession.value) {
      currentSession.value.messages = []
    }
  }

  // Get session title from first user message or default
  const getSessionTitle = (session: Session): string => {
    if (session.title) return session.title
    
    const firstUserMessage = session.messages.find(m => m.role === 'user')
    if (firstUserMessage) {
      return firstUserMessage.content.slice(0, 30) + (firstUserMessage.content.length > 30 ? '...' : '')
    }
    
    return 'New Conversation'
  }

  return {
    currentSession,
    sessions,
    isLoading,
    createSession,
    switchToSession,
    deleteSession,
    addMessage,
    clearSession,
    loadSessionHistory,
    getSessionTitle
  }
})